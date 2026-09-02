"""Turn a local Parquet corpus into one tidy timeline of everything countable.

The output is deliberately **long, not wide**: one row per
``(source, month, dimension, value)`` carrying a record count and a distinct-domain
count. A wide table would need its schema fixed in advance, and every new
algorithm number or TLSA usage would need a migration; a long table absorbs values
nobody has seen yet, which over a seventeen-year corpus is the normal case.

Both counts are kept because they answer different questions and have been
confused before. A record count is weighted by how often a name is measured and by
how many keys it publishes; a distinct-domain count is one vote per name. The
RFC 4509 "10x disagreement" was entirely this: DS records are 8% of forward DNSSEC
records and 100% of reverse ones, so the same mechanism read 5% and 79%.

Every dimension carries its own denominator as a ``*_total`` row, so a share can be
computed without ever guessing which population it belongs to. That is the whole
point -- ``P(value | population)`` is only meaningful when the population came from
the same query as the numerator.

Nothing here touches the network. The corpus is already on disk; the scan is a
local read, so it cannot be throttled and does not need pacing.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Sequence

import duckdb
import pandas as pd

from .cache_index import CachedDay
from .models import OpenINTELDictionary
from .parquet_reader import describe_parquet, resolve_column_candidates
from .utils import ensure_dir, get_logger, warn

__all__ = [
    "DIMENSIONS",
    "Dimension",
    "extract_days",
    "extract_one",
    "merge_timeline",
]

LOGGER = get_logger(__name__)


@dataclass(frozen=True)
class Dimension:
    """One countable axis.

    ``expression`` is SQL over the normalized column names; ``where`` narrows the
    rows it applies to (an algorithm on a DS record and on a DNSKEY record are
    different facts and must not be pooled). ``needs`` lists the normalized fields
    the dimension requires -- a corpus missing any of them skips this dimension
    rather than emitting nulls that look like observations.
    """

    name: str
    expression: str
    needs: tuple[str, ...]
    where: str | None = None
    note: str = ""


#: What to count. Extend this list rather than writing bespoke queries: every
#: entry automatically gets its own denominator row and flows through to both the
#: bottom-up and top-down analyses.
DIMENSIONS: tuple[Dimension, ...] = (
    Dimension("rr_type", "rr_type", ("rr_type",),
              note="Record-type composition. The denominator every cross-corpus "
                   "comparison has to be conditioned on."),

    # Algorithm, split by the record that carries it. Pooling these is the
    # single most common way to produce a number that is true of nothing.
    Dimension("algorithm_ds", "CAST(algorithm AS VARCHAR)", ("algorithm", "rr_type"),
              where="rr_type = 'DS'"),
    Dimension("algorithm_dnskey", "CAST(algorithm AS VARCHAR)", ("algorithm", "rr_type"),
              where="rr_type = 'DNSKEY'"),
    Dimension("algorithm_rrsig", "CAST(algorithm AS VARCHAR)", ("algorithm", "rr_type"),
              where="rr_type = 'RRSIG'"),
    Dimension("algorithm_cds", "CAST(algorithm AS VARCHAR)", ("algorithm", "rr_type"),
              where="rr_type IN ('CDS', 'CDNSKEY')",
              note="Algorithm 0 here is the RFC 8078 delete signal, not an algorithm."),

    Dimension("digest_type_ds", "CAST(digest_type AS VARCHAR)", ("digest_type", "rr_type"),
              where="rr_type = 'DS'"),
    Dimension("digest_type_cds", "CAST(digest_type AS VARCHAR)", ("digest_type", "rr_type"),
              where="rr_type = 'CDS'"),

    # NSEC3 parameters -- RFC 9276 is a statement about exactly these.
    Dimension("nsec3_iterations", "CAST(nsec3_iterations AS VARCHAR)",
              ("nsec3_iterations",), where="nsec3_iterations IS NOT NULL"),
    Dimension("nsec3_salt_empty",
              "CASE WHEN nsec3_salt IS NULL OR nsec3_salt IN ('', '-') "
              "THEN 'empty' ELSE 'present' END",
              ("nsec3_salt",), where="rr_type IN ('NSEC3', 'NSEC3PARAM')"),
    Dimension("nsec3_optout", "CAST(nsec3_flags % 2 AS VARCHAR)", ("nsec3_flags",),
              where="nsec3_flags IS NOT NULL",
              note="Bit 0 of the NSEC3 flags is Opt-Out (RFC 5155 s6)."),

    # DNSKEY shape. 257 = SEP/KSK, 256 = ZSK, 385 = REVOKE set (RFC 5011).
    Dimension("dnskey_flags", "CAST(flags AS VARCHAR)", ("flags", "rr_type"),
              where="rr_type IN ('DNSKEY', 'CDNSKEY')"),
    Dimension("dnskey_protocol", "CAST(dnskey_protocol AS VARCHAR)",
              ("dnskey_protocol",), where="dnskey_protocol IS NOT NULL"),
    Dimension("rsa_key_bitsize", "CAST(rsa_key_bitsize AS VARCHAR)",
              ("rsa_key_bitsize",), where="rsa_key_bitsize IS NOT NULL"),

    Dimension("rrsig_type_covered", "rrsig_type_covered", ("rrsig_type_covered",),
              where="rrsig_type_covered IS NOT NULL"),

    # DANE.
    Dimension("tlsa_usage", "CAST(tlsa_usage AS VARCHAR)", ("tlsa_usage",),
              where="tlsa_usage IS NOT NULL"),
    Dimension("tlsa_selector", "CAST(tlsa_selector AS VARCHAR)", ("tlsa_selector",),
              where="tlsa_selector IS NOT NULL"),
    Dimension("tlsa_matchtype", "CAST(tlsa_matchtype AS VARCHAR)", ("tlsa_matchtype",),
              where="tlsa_matchtype IS NOT NULL"),
)

#: Fields worth selecting whenever the corpus has them.
_ALL_FIELDS: tuple[str, ...] = (
    "timestamp", "domain", "rr_type", "algorithm", "digest_type", "key_tag",
    "flags", "nsec3_iterations", "nsec3_salt", "nsec3_flags", "dnskey_protocol",
    "rsa_key_bitsize", "rrsig_type_covered", "tlsa_usage", "tlsa_selector",
    "tlsa_matchtype",
)


def _binding(field: str, candidates: Sequence[str]) -> str:
    """SQL binding a normalized field to whichever native columns exist.

    COALESCE rather than "first match": OpenINTEL splits one logical field across
    per-record-type columns (``ds_algorithm``, ``dnskey_algorithm``, ...) and
    populates only the one matching each row. Binding to the first would read
    NULL for every row of every other record type.
    """
    if not candidates:
        return f"NULL AS {field}"
    if len(candidates) == 1:
        return f'"{candidates[0]}" AS {field}'
    joined = ", ".join(f'"{c}"' for c in candidates)
    return f"COALESCE({joined}) AS {field}"


def _timestamp_expression(candidates: Sequence[str]) -> str:
    """Month key, tolerating epoch-millis integers and native timestamps alike."""
    if not candidates:
        return "NULL AS month"
    column = f'"{candidates[0]}"'
    return (
        "strftime("
        f"CASE WHEN typeof({column}) IN ('BIGINT','INTEGER','HUGEINT','UBIGINT') "
        f"THEN to_timestamp(CAST({column} AS BIGINT) / 1000) "
        f"ELSE CAST({column} AS TIMESTAMP) END, '%Y-%m') AS month"
    )


def extract_one(
    con: duckdb.DuckDBPyConnection,
    day: CachedDay,
    dictionary: OpenINTELDictionary,
    *,
    warnings: list[str] | None = None,
) -> pd.DataFrame:
    """Tidy counts for one source-day. Returns an empty frame if nothing applies."""
    collected = warnings if warnings is not None else []
    if not day.paths:
        return pd.DataFrame()

    try:
        columns = [str(c["name"]) for c in describe_parquet(Path(day.paths[0]))["columns"]]
    except Exception as exc:
        warn(collected, f"{day.key}: cannot read schema ({exc}); skipped.", LOGGER)
        return pd.DataFrame()

    resolved = resolve_column_candidates(dictionary, _ALL_FIELDS, columns)
    available = {f for f, c in resolved.items() if c}
    if "rr_type" not in available or "domain" not in available:
        warn(
            collected,
            f"{day.key}: no rr_type/domain column; the file carries "
            f"{len(columns)} columns but none maps to the dictionary. Skipped.",
            LOGGER,
        )
        return pd.DataFrame()

    selects = [_timestamp_expression(resolved.get("timestamp", []))]
    selects += [
        _binding(f, resolved.get(f, []))
        for f in _ALL_FIELDS if f != "timestamp"
    ]
    files = ", ".join(f"'{p}'" for p in day.paths)
    base = f"SELECT {', '.join(selects)} FROM read_parquet([{files}], union_by_name=true)"

    blocks: list[str] = [
        # The denominator every other row is read against.
        f"SELECT month, 'all' AS dimension, 'all' AS value, "
        f"count(*) AS records, count(DISTINCT domain) AS domains FROM src GROUP BY 1"
    ]
    skipped: list[str] = []
    for dim in DIMENSIONS:
        if not set(dim.needs) <= available:
            skipped.append(dim.name)
            continue
        clause = f"WHERE {dim.where}" if dim.where else ""
        blocks.append(
            f"SELECT month, '{dim.name}' AS dimension, "
            f"CAST({dim.expression} AS VARCHAR) AS value, "
            f"count(*) AS records, count(DISTINCT domain) AS domains "
            f"FROM src {clause} GROUP BY 1, 3"
        )
        # Per-dimension denominator: the rows the dimension could apply to.
        blocks.append(
            f"SELECT month, '{dim.name}' AS dimension, '_total' AS value, "
            f"count(*) AS records, count(DISTINCT domain) AS domains "
            f"FROM src {clause} GROUP BY 1"
        )

    sql = f"WITH src AS ({base}) " + " UNION ALL ".join(blocks)
    try:
        frame = con.execute(sql).df()
    except Exception as exc:
        warn(collected, f"{day.key}: query failed ({exc}); skipped.", LOGGER)
        return pd.DataFrame()

    if frame.empty:
        return frame
    frame.insert(0, "source", day.source)
    frame.insert(1, "basis", day.basis)
    frame.insert(2, "day", day.day.isoformat())
    frame["files"] = len(day.paths)
    if skipped:
        LOGGER.debug("%s: dimensions unavailable: %s", day.key, ", ".join(skipped))
    return frame


def extract_days(
    days: Sequence[CachedDay],
    dictionary: OpenINTELDictionary,
    checkpoint_dir: Path | str,
    *,
    threads: int | None = None,
    memory_limit: str | None = None,
    resume: bool = True,
    warnings: list[str] | None = None,
) -> tuple[int, int]:
    """Extract every source-day, checkpointing each one. Returns (done, skipped).

    One Parquet checkpoint per source-day, so an interrupted 14 TB run resumes at
    the day it stopped rather than at the beginning. This is the property that
    makes the run survivable on a machine that may be rebooted.
    """
    collected = warnings if warnings is not None else []
    out_dir = ensure_dir(checkpoint_dir)

    con = duckdb.connect()
    if threads:
        con.execute(f"SET threads={int(threads)}")
    if memory_limit:
        con.execute(f"SET memory_limit='{memory_limit}'")

    done = skipped = 0
    for index, day in enumerate(days, start=1):
        target = out_dir / f"{day.basis}__{day.source}__{day.day.isoformat()}.parquet"
        if resume and target.exists():
            skipped += 1
            continue
        frame = extract_one(con, day, dictionary, warnings=collected)
        if frame.empty:
            # Record the attempt so a resumed run does not retry a file that
            # cannot be read; an empty checkpoint is a fact, not a gap.
            pd.DataFrame(
                columns=["source", "basis", "day", "month", "dimension",
                         "value", "records", "domains", "files"]
            ).to_parquet(target, index=False)
            skipped += 1
            continue
        tmp = target.with_suffix(".parquet.part")
        frame.to_parquet(tmp, index=False)
        tmp.replace(target)
        done += 1
        if index % 25 == 0 or index == len(days):
            LOGGER.info("extracted %d/%d source-days", index, len(days))
    con.close()
    return done, skipped


def merge_timeline(checkpoint_dir: Path | str) -> pd.DataFrame:
    """Fold every checkpoint into one monthly timeline.

    Days are summed into months. Record counts add; **distinct-domain counts do
    not** -- the same name measured on two days is one domain, and adding them
    would overcount. Summing is the honest option available from per-day
    checkpoints, so the column is named ``domain_days`` to say what it is rather
    than being passed off as a distinct count.
    """
    files = sorted(Path(checkpoint_dir).glob("*.parquet"))
    if not files:
        return pd.DataFrame()
    frames = []
    for path in files:
        try:
            frame = pd.read_parquet(path)
        except Exception as exc:  # a half-written checkpoint from a hard kill
            LOGGER.warning("unreadable checkpoint %s: %s", path.name, exc)
            continue
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame()

    merged = pd.concat(frames, ignore_index=True)
    merged = merged.rename(columns={"domains": "domain_days"})
    grouped = (
        merged.groupby(["source", "basis", "month", "dimension", "value"], dropna=False)
        .agg(records=("records", "sum"),
             domain_days=("domain_days", "sum"),
             # The largest single day in the month. Distinct domains cannot be
             # summed across days without counting the same name repeatedly, and
             # the per-day checkpoints do not carry the identities needed to union
             # them. The busiest day is a true lower bound on the month's distinct
             # count, which is the direction a threshold guard needs to be wrong
             # in: it can only ever understate reach, never inflate it.
             domains_peak=("domain_days", "max"),
             measured_days=("day", "nunique"))
        .reset_index()
        .sort_values(["source", "month", "dimension", "value"])
    )
    return grouped
