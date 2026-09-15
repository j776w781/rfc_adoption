"""Scan a local OpenINTEL cache into a month/domain/tld presence table.

Two stages, checkpointed the way ``openintel_rfc.scale_runner`` checkpoints its
own scan -- write-then-atomic-rename, status file last -- because a walk over a
multi-terabyte NAS cache takes long enough that "resume after the process was
killed" is not optional:

``scan``
    One DuckDB query per source-day, grouping every row down to (month, domain,
    tld) with a 0/1 presence flag per record type. This is the expensive part
    (it touches every row) and the one whose result is small: a source-day's
    checkpoint holds one row per *domain*, not per record.
``merge``
    Every source-day checkpoint for the requested sources/date range is read
    back and grouped again, this time across days, taking the OR (``max`` over
    0/1) of each presence flag and collapsing repeat domain sightings within a
    month into one row. This is cheap: its input is already domain-sized, not
    row-sized.

Why the OpenINTEL-native column names never appear here
---------------------------------------------------------
The cache holds a decade of measurement generations, and OpenINTEL exports
DS/DNSKEY/RRSIG under record-type-specific columns rather than one column that
means "domain" or "record type". Re-deriving that column mapping here would
silently drift from what the rest of the project already knows. Instead this
module asks the same dictionary the same question through
``openintel_rfc.parquet_reader.resolve_column_candidates`` and
``openintel_rfc.sql_compiler.column_expressions``, and gets back a normalized
``domain`` / ``zone`` / ``rr_type`` / ``timestamp`` SQL expression per field,
already COALESCEd across whichever native columns exist in that file and
cleaned (trimmed, empty-as-absent, record type upper-cased, epoch timestamp
unit detected) exactly as ``openintel_rfc.sql_compiler.build_scan_sql`` cleans
them for the RFC matcher's own scan.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

import duckdb

from openintel_rfc.cache_index import CachedDay, CacheInventory
from openintel_rfc.models import OpenINTELDictionary
from openintel_rfc.parquet_reader import describe_parquet, resolve_column_candidates
from openintel_rfc.sql_compiler import column_expressions, quote_string
from openintel_rfc.utils import PipelineError, ensure_dir, get_logger, iso, now, warn

__all__ = [
    "REQUIRED_FIELDS",
    "OPTIONAL_FIELDS",
    "PRESENCE_RR_TYPES",
    "DAY_OUTPUT_COLUMNS",
    "DayCheckpointResult",
    "ScanSummary",
    "MergeSummary",
    "resolve_day_expressions",
    "build_day_scan_sql",
    "process_day",
    "scan_cache",
    "merge_domain_month_table",
]

LOGGER = get_logger(__name__)

#: Normalized fields a day's scan cannot proceed without.
REQUIRED_FIELDS: tuple[str, ...] = ("timestamp", "domain", "rr_type")

#: Normalized fields used if present, with a fallback (the cache-inventory
#: source name) when the corpus does not carry them.
OPTIONAL_FIELDS: tuple[str, ...] = ("zone",)

#: The three record types this table reports presence for, in output-column order.
PRESENCE_RR_TYPES: tuple[str, ...] = ("DS", "DNSKEY", "RRSIG")

DAY_OUTPUT_COLUMNS: tuple[str, ...] = (
    "month",
    "domain",
    "tld",
    "ds_present",
    "dnskey_present",
    "rrsig_present",
)

_STATUS_SUFFIX = ".status.json"
_CHECKPOINT_SUFFIX = ".parquet"


# --------------------------------------------------------------------------- #
# Column resolution (thin wrapper: all the real logic lives in openintel_rfc)
# --------------------------------------------------------------------------- #


def _describe_columns(connection: duckdb.DuckDBPyConnection, paths: Sequence[str]) -> list[str]:
    """The union of column names across ``paths``, via one DESCRIBE query.

    ``union_by_name`` mirrors how the day itself will be scanned: a source-day
    whose files were written by two different measurement generations can carry
    slightly different columns, and the resolver has to see the union, not just
    the first file's schema.
    """
    literal = ", ".join(quote_string(p) for p in paths)
    described = connection.execute(
        f"DESCRIBE SELECT * FROM read_parquet([{literal}], union_by_name = true)"
    ).fetchall()
    return [str(row[0]) for row in described]


def resolve_day_expressions(
    dictionary: OpenINTELDictionary, columns: Sequence[str]
) -> dict[str, str]:
    """Normalized field -> cleaned SQL expression, for one day's column set.

    Delegates entirely to ``openintel_rfc.parquet_reader.resolve_column_candidates``
    (alias resolution) and ``openintel_rfc.sql_compiler.column_expressions``
    (COALESCE + cleaning), so this module can never disagree with the RFC
    matcher's scan about what a normalized field means.
    """
    candidates = resolve_column_candidates(
        dictionary, (*REQUIRED_FIELDS, *OPTIONAL_FIELDS), columns
    )
    return column_expressions(dictionary, candidates)


def build_day_scan_sql(
    paths: Sequence[str], column_expr: Mapping[str, str], *, tld_fallback: str
) -> str:
    """The per-day scan: one row per (month, domain, tld) with presence flags.

    ``tld_fallback`` (the cache inventory's own source name for this day) is
    used only when the corpus does not carry a resolvable ``zone`` column --
    matching the fallback ``openintel_rfc.sql_compiler.build_aggregate_sql``
    uses for the same normalized field.
    """
    missing = [name for name in REQUIRED_FIELDS if name not in column_expr]
    if missing:
        raise PipelineError(
            f"Cannot resolve required field(s) {', '.join(missing)} against this "
            "day's Parquet schema. Check the dictionary's openintel_native_fields "
            "against the file's real columns."
        )

    domain_expr = column_expr["domain"]
    timestamp_expr = column_expr["timestamp"]
    rr_type_expr = column_expr["rr_type"]
    tld_expr = column_expr.get("zone", quote_string(tld_fallback))
    literal = ", ".join(quote_string(p) for p in paths)

    def presence(rr_type: str) -> str:
        # COALESCE(..., FALSE) so a domain with rows but none of this type
        # reports 0, never NULL -- the caller asked for a 0/1 flag, not a
        # three-valued one.
        return f"CAST(COALESCE(bool_or({rr_type_expr} = {quote_string(rr_type)}), FALSE) AS TINYINT)"

    presence_columns = ",\n  ".join(
        f"{presence(rr_type)} AS {rr_type.lower()}_present" for rr_type in PRESENCE_RR_TYPES
    )

    return (
        "SELECT\n"
        f"  strftime({timestamp_expr}, '%Y-%m') AS month,\n"
        f"  {domain_expr} AS domain,\n"
        f"  {tld_expr} AS tld,\n"
        f"  {presence_columns}\n"
        f"FROM read_parquet([{literal}], union_by_name = true, hive_partitioning = true)\n"
        f"WHERE {domain_expr} IS NOT NULL AND {timestamp_expr} IS NOT NULL\n"
        "GROUP BY 1, 2, 3"
    )


# --------------------------------------------------------------------------- #
# Atomic writes (same pattern as openintel_rfc.scale_runner: data first, status
# last, so a killed process can never leave a checkpoint that looks complete)
# --------------------------------------------------------------------------- #


def _copy_query_to_parquet(
    connection: duckdb.DuckDBPyConnection, select_sql: str, destination: Path
) -> None:
    ensure_dir(destination.parent)
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    if tmp.exists():
        tmp.unlink()
    connection.execute(f"COPY ({select_sql}) TO {quote_string(str(tmp))} (FORMAT PARQUET)")
    os.replace(tmp, destination)


def _read_status(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_status(path: Path, payload: Mapping[str, Any]) -> None:
    ensure_dir(path.parent)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(dict(payload), indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)


def _checkpoint_key(day: CachedDay) -> str:
    """A flat, filesystem-safe token identifying one source-day's checkpoint."""
    token = day.key  # "<basis>/<source>/<YYYY-MM-DD>"
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in token) or "day"


def _checkpoint_paths(checkpoint_dir: Path, day: CachedDay) -> tuple[Path, Path]:
    directory = Path(checkpoint_dir) / "days"
    key = _checkpoint_key(day)
    return directory / f"{key}{_CHECKPOINT_SUFFIX}", directory / f"{key}{_STATUS_SUFFIX}"


# --------------------------------------------------------------------------- #
# Per-day processing
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DayCheckpointResult:
    """What scanning one source-day produced, or reused."""

    key: str
    source: str
    day: str  # ISO date
    checkpoint_path: Path
    status_path: Path
    reused: bool
    rows_out: int
    elapsed_seconds: float


def _checkpoint_is_usable(status_path: Path, checkpoint_path: Path, *, fingerprint: str) -> bool:
    """Mirrors ``scale_runner._checkpoint_problem``'s trust rule: verify, don't assume."""
    if not checkpoint_path.is_file():
        return False
    status = _read_status(status_path)
    if status is None or not status.get("complete"):
        return False
    return status.get("scan_sql_sha1") == fingerprint


def process_day(
    day: CachedDay,
    *,
    dictionary: OpenINTELDictionary,
    connection: duckdb.DuckDBPyConnection,
    checkpoint_dir: Path,
    resume: bool = True,
    warnings: list[str] | None = None,
) -> DayCheckpointResult:
    """Scan one source-day into its (month, domain, tld) checkpoint.

    Returns without touching Parquet when a checkpoint already exists, is
    marked complete, and was produced by the exact same compiled scan (its SQL
    fingerprint matches) -- the same "verify, don't assume" rule
    ``openintel_rfc.scale_runner`` applies to its own checkpoints, so a
    dictionary change or a corrupt write is recomputed rather than silently
    trusted.
    """
    collected = warnings if warnings is not None else []
    if not day.paths:
        raise PipelineError(f"{day.key} has no files to scan.")

    checkpoint_path, status_path = _checkpoint_paths(checkpoint_dir, day)

    columns = _describe_columns(connection, day.paths)
    column_expr = resolve_day_expressions(dictionary, columns)
    scan_sql = build_day_scan_sql(day.paths, column_expr, tld_fallback=day.source)
    fingerprint = hashlib.sha1(scan_sql.encode("utf-8")).hexdigest()

    if resume and _checkpoint_is_usable(status_path, checkpoint_path, fingerprint=fingerprint):
        status = _read_status(status_path) or {}
        LOGGER.info("Reusing checkpoint for %s", day.key)
        return DayCheckpointResult(
            key=day.key,
            source=day.source,
            day=day.day.isoformat(),
            checkpoint_path=checkpoint_path,
            status_path=status_path,
            reused=True,
            rows_out=int(status.get("rows_out", 0)),
            elapsed_seconds=0.0,
        )
    if resume and (checkpoint_path.is_file() or status_path.is_file()):
        warn(
            collected,
            f"Checkpoint for {day.key} was not reused (missing, incomplete, or from a "
            "different scan) and is being recomputed.",
            LOGGER,
        )

    started = time.monotonic()
    try:
        _copy_query_to_parquet(connection, scan_sql, checkpoint_path)
    except Exception as exc:  # DuckDB raises its own error hierarchy
        raise PipelineError(
            f"DuckDB failed scanning {day.key} ({len(day.paths)} file(s)): {exc}"
        ) from exc
    elapsed = time.monotonic() - started
    rows_out = int(describe_parquet(checkpoint_path)["row_count"])

    _write_status(
        status_path,
        {
            "key": day.key,
            "source": day.source,
            "basis": day.basis,
            "date": day.day.isoformat(),
            "object_count": len(day.paths),
            "rows_out": rows_out,
            "elapsed_seconds": round(elapsed, 3),
            "scan_sql_sha1": fingerprint,
            "complete": True,
            "completed_at": iso(now()),
        },
    )

    LOGGER.info(
        "%s: %d domain-row(s) from %d file(s) in %.2fs",
        day.key,
        rows_out,
        len(day.paths),
        elapsed,
    )
    return DayCheckpointResult(
        key=day.key,
        source=day.source,
        day=day.day.isoformat(),
        checkpoint_path=checkpoint_path,
        status_path=status_path,
        reused=False,
        rows_out=rows_out,
        elapsed_seconds=elapsed,
    )


# --------------------------------------------------------------------------- #
# Orchestration across many source-days
# --------------------------------------------------------------------------- #


@dataclass
class ScanSummary:
    days_processed: int
    days_reused: int
    days_failed: int
    warnings: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


def scan_cache(
    inventory: CacheInventory,
    *,
    dictionary: OpenINTELDictionary,
    checkpoint_dir: Path | str,
    sources: Sequence[str] | None = None,
    start: date | None = None,
    end: date | None = None,
    max_days: int | None = None,
    resume: bool = True,
    threads: int | None = None,
) -> ScanSummary:
    """Run :func:`process_day` over every selected source-day in ``inventory``.

    One DuckDB connection is reused across days (each query is independent, so
    there is nothing to isolate), which is what lets ``threads`` parallelize
    within a day's scan without spinning up a new connection per day.

    A day whose scan fails is recorded as a failure and the walk continues:
    thousands of source-days are in play, and one unreadable file should not
    abort every day after it.
    """
    days = inventory.select(sources=sources, start=start, end=end)
    if not days:
        raise PipelineError("No cached source-days match the requested sources/date range.")
    if max_days is not None:
        days = days[: max(int(max_days), 0)]

    connection = duckdb.connect(database=":memory:")
    if threads:
        connection.execute(f"SET threads={int(threads)}")
    try:
        connection.execute("SET enable_progress_bar=false")
    except Exception:  # pragma: no cover - setting exists in all builds
        pass

    warnings: list[str] = []
    failures: list[str] = []
    processed = 0
    reused = 0
    try:
        for index, day in enumerate(days, start=1):
            LOGGER.info("[%d/%d] %s (%d file(s))", index, len(days), day.key, len(day.paths))
            try:
                result = process_day(
                    day,
                    dictionary=dictionary,
                    connection=connection,
                    checkpoint_dir=Path(checkpoint_dir),
                    resume=resume,
                    warnings=warnings,
                )
            except PipelineError as exc:
                message = f"{day.key}: {exc}"
                warn(warnings, message, LOGGER)
                failures.append(message)
                continue
            processed += 1
            if result.reused:
                reused += 1
    finally:
        connection.close()

    return ScanSummary(
        days_processed=processed,
        days_reused=reused,
        days_failed=len(failures),
        warnings=warnings,
        failures=failures,
    )


# --------------------------------------------------------------------------- #
# Merge: day checkpoints -> the final month/domain/tld table
# --------------------------------------------------------------------------- #


@dataclass
class MergeSummary:
    day_checkpoints_used: int
    output_path: Path
    row_count: int
    warnings: list[str] = field(default_factory=list)


def _select_day_checkpoints(
    checkpoint_dir: Path,
    *,
    sources: Sequence[str] | None,
    start: date | None,
    end: date | None,
    warnings: list[str],
) -> list[Path]:
    directory = Path(checkpoint_dir) / "days"
    if not directory.is_dir():
        raise PipelineError(f"No day checkpoints found under {directory}.")

    wanted_sources = set(sources) if sources is not None else None
    usable: list[Path] = []
    for status_path in sorted(directory.glob(f"*{_STATUS_SUFFIX}")):
        checkpoint_path = status_path.with_name(
            status_path.name[: -len(_STATUS_SUFFIX)] + _CHECKPOINT_SUFFIX
        )
        status = _read_status(status_path)
        if status is None or not status.get("complete") or not checkpoint_path.is_file():
            warn(
                warnings,
                f"Skipping {status_path.name}: no complete, readable checkpoint beside it.",
                LOGGER,
            )
            continue
        if wanted_sources is not None and str(status.get("source")) not in wanted_sources:
            continue
        if start is not None or end is not None:
            try:
                day_value = date.fromisoformat(str(status.get("date")))
            except ValueError:
                day_value = None
            if day_value is not None:
                if start is not None and day_value < start:
                    continue
                if end is not None and day_value > end:
                    continue
        usable.append(checkpoint_path)
    return usable


def merge_domain_month_table(
    checkpoint_dir: Path | str,
    output_path: Path | str,
    *,
    sources: Sequence[str] | None = None,
    start: date | None = None,
    end: date | None = None,
    csv: bool = False,
) -> MergeSummary:
    """Merge every selected day checkpoint into the final (month, domain, tld) table.

    Each day checkpoint already holds at most one row per domain for that day
    (``process_day`` grouped it that way); this step ORs the presence flags
    (``max`` over 0/1) across every day of the month and collapses repeat
    domain sightings, so a domain seen on 30 days of the month still produces
    exactly one output row.
    """
    warnings: list[str] = []
    checkpoints = _select_day_checkpoints(
        Path(checkpoint_dir), sources=sources, start=start, end=end, warnings=warnings
    )
    if not checkpoints:
        raise PipelineError(
            f"No usable day checkpoints matched the requested filter under "
            f"{Path(checkpoint_dir) / 'days'}."
        )

    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    connection = duckdb.connect(database=":memory:")
    try:
        literal = ", ".join(quote_string(p.as_posix()) for p in checkpoints)
        merge_sql = (
            "SELECT\n"
            "  month,\n"
            "  domain,\n"
            "  tld,\n"
            "  CAST(max(ds_present) AS TINYINT) AS ds_present,\n"
            "  CAST(max(dnskey_present) AS TINYINT) AS dnskey_present,\n"
            "  CAST(max(rrsig_present) AS TINYINT) AS rrsig_present\n"
            f"FROM read_parquet([{literal}], union_by_name = true)\n"
            "GROUP BY month, domain, tld\n"
            "ORDER BY month, tld, domain"
        )
        tmp = output_path.with_suffix(output_path.suffix + ".tmp")
        if tmp.exists():
            tmp.unlink()
        try:
            connection.execute(f"COPY ({merge_sql}) TO {quote_string(str(tmp))} (FORMAT PARQUET)")
        except Exception as exc:  # DuckDB raises its own error hierarchy
            raise PipelineError(f"DuckDB failed merging day checkpoints: {exc}") from exc
        os.replace(tmp, output_path)
        row_count = int(describe_parquet(output_path)["row_count"])

        if csv:
            csv_path = output_path.with_suffix(".csv")
            csv_tmp = csv_path.with_suffix(csv_path.suffix + ".tmp")
            if csv_tmp.exists():
                csv_tmp.unlink()
            connection.execute(
                f"COPY (SELECT * FROM read_parquet({quote_string(str(output_path))}) "
                f"ORDER BY month, tld, domain) TO {quote_string(str(csv_tmp))} "
                "(FORMAT CSV, HEADER)"
            )
            os.replace(csv_tmp, csv_path)
    finally:
        connection.close()

    return MergeSummary(
        day_checkpoints_used=len(checkpoints),
        output_path=output_path,
        row_count=row_count,
        warnings=warnings,
    )
