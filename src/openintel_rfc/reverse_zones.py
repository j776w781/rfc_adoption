"""Ingest RIPE NCC's historical reverse-delegation zones as a second corpus.

What this adds that OpenINTEL cannot
------------------------------------
The RIPE NCC republishes the reverse DNS zones (``in-addr.arpa`` and, despite the
dataset's name, ``ip6.arpa``) daily, and the archive carries the *other* RIRs'
zonelets too -- AFRINIC, APNIC, ARIN, LACNIC and RIPE. Two things make it worth a
separate ingestion path:

**It starts in 2009.** The archive runs from 2009-03-24 to the present, so it
reaches nine years further back than the OpenINTEL window this project otherwise
measures. Every first-seen date in the existing analysis is left-censored at
2018-01-01; here the same RFCs can be watched from before several of them were
published.

**It has a real denominator.** A zone file lists every delegation, so "how many
delegations exist" and "how many carry a DS" are both directly countable. The
OpenINTEL side of this project can only report a share of *records*, which is why
the deck has to keep saying "record-level, not zone-level". Measured on
2024-01-01: 1,218,333 delegations, 7,775 of them signed -- 0.638%.

What it cannot say
------------------
A DS in the parent proves the delegation is *signed*, not that the child validates,
and reverse DNS is a different population from forward DNS -- run mostly by network
operators, allocated in blocks, and far more concentrated. Nothing here should be
read as a statement about the DNS as a whole, any more than three forward zones
should be.

Shape of the archive
--------------------
One ``tar.bz2`` per day, roughly 19 MB in 2009 growing to 102 MB in 2026, laid out
as ``YYYYMMDD/<rir>/<zonefile>`` with ``.gz``/``.md5``/``.asc``/``.sha1`` siblings
that are skipped. The zone files are ordinary BIND master files whose records are
unusually regular: every owner name is a fully-qualified name with a trailing dot,
the class is omitted, and no record wraps across lines. The parser still refuses a
line it does not fully understand rather than guessing at it.

Output
------
Parquet written into the same cache layout ``--mode download --cache-dir`` reads,
using OpenINTEL's *native* column names. That is the whole trick: once the rows
look like OpenINTEL rows, the existing checklist compiler, matcher, scorer and
timeline work on them unmodified, and RFC 4509 / 6605 / 8080 mean exactly what they
already mean elsewhere in the project.
"""
from __future__ import annotations

import json
import re
import tarfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Sequence

import pandas as pd

from .utils import PipelineError, ensure_dir, get_logger, warn

LOGGER = get_logger(__name__)

#: The published archive. Named for in-addr.arpa; also carries ip6.arpa zones.
ARCHIVE_BASE = (
    "https://data-store.ripe.net/datasets/reverse-dns-zones/in-addr.arpa/"
)

#: First day the archive offers. Requests before this are a mistake worth naming.
ARCHIVE_START = date(2009, 3, 24)

#: The five RIRs whose zonelets appear inside each daily tarball.
RIR_SOURCES: tuple[str, ...] = ("afrinic", "apnic", "arin", "lacnic", "ripe")

#: Basis label for this corpus, kept distinct from OpenINTEL's zonefile/toplist so
#: the two can share a cache directory without colliding.
REVERSE_BASIS = "reverse"

#: Sidecar suffixes inside the tarball that are not zone data.
_SKIP_SUFFIXES = (".gz", ".md5", ".asc", ".sha1", ".txt")

# Owner names are fully qualified; class is optional; TTL is optional.
_DS = re.compile(
    r"^(?P<name>\S+)\s+(?:\d+\s+)?(?:IN\s+)?DS\s+"
    r"(?P<key_tag>\d+)\s+(?P<algorithm>\d+)\s+(?P<digest_type>\d+)\s+(?P<digest>\S+)",
    re.IGNORECASE,
)
_NS = re.compile(r"^(?P<name>\S+)\s+(?:\d+\s+)?(?:IN\s+)?NS\s+\S+", re.IGNORECASE)


@dataclass
class IngestReport:
    """What one day's ingestion produced."""

    day: date
    delegations: int = 0
    ds_records: int = 0
    signed_delegations: int = 0
    rows: int = 0
    per_rir: dict[str, int] = field(default_factory=dict)
    paths: list[Path] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    warnings: list[str] = field(default_factory=list)

    @property
    def signed_share(self) -> float:
        return self.signed_delegations / self.delegations if self.delegations else 0.0

    def describe(self) -> str:
        return (
            f"{self.day.isoformat()}: {self.delegations:,} delegations, "
            f"{self.signed_delegations:,} signed ({self.signed_share * 100:.3f}%), "
            f"{self.ds_records:,} DS records, {self.rows:,} rows, "
            f"{self.elapsed_seconds:.0f}s"
        )


def archive_url(day: date) -> str:
    """URL of the daily tarball."""
    return f"{ARCHIVE_BASE}in-addr.arpa-{day:%Y%m%d}.tar.bz2"


def archive_path(day: date, download_dir: Path | str) -> Path:
    return Path(download_dir) / f"in-addr.arpa-{day:%Y%m%d}.tar.bz2"


def parquet_path(day: date, rir: str, cache_dir: Path | str) -> Path:
    """Where a day's rows for one RIR live, in download-mode cache layout."""
    return (
        Path(cache_dir)
        / REVERSE_BASIS
        / rir
        / day.isoformat()
        / f"part-00000-{rir}-{day:%Y%m%d}.parquet"
    )


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #


def fetch_archive(
    day: date,
    download_dir: Path | str,
    *,
    timeout: int = 600,
    attempts: int = 3,
    warnings: list[str] | None = None,
) -> Path | None:
    """Download one day's tarball, skipping a copy already on disk.

    Returns ``None`` when the archive has no file for that day -- the series has
    real gaps (2009 holds 280 days, 2011 holds 273), and a missing day is a fact
    about the archive rather than an error to abort on.
    """
    collected = warnings if warnings is not None else []
    destination = archive_path(day, download_dir)
    if destination.is_file() and destination.stat().st_size > 0:
        return destination

    ensure_dir(destination.parent)
    partial = destination.with_suffix(destination.suffix + ".part")
    url = archive_url(day)
    request = urllib.request.Request(url, headers={"User-Agent": "openintel-rfc/1.0"})

    # A truncated transfer is the common failure here, and it only shows up later
    # as "compressed file ended before the end-of-stream marker" -- by which point
    # the cause looks like a corrupt archive rather than a short read. Compare
    # against Content-Length at fetch time and retry, so a transient short read
    # costs a retry rather than the day.
    last_error = ""
    for attempt in range(1, max(int(attempts), 1) + 1):
        declared = None
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                header = response.headers.get("Content-Length")
                declared = int(header) if header is not None else None
                with open(partial, "wb") as handle:
                    while chunk := response.read(1 << 20):
                        handle.write(chunk)
        except urllib.error.HTTPError as exc:
            partial.unlink(missing_ok=True)
            if exc.code == 404:
                warn(collected, f"No reverse-zone archive published for {day}.", LOGGER)
                return None
            raise PipelineError(f"Fetching {url} failed: HTTP {exc.code}") from exc
        except Exception as exc:
            partial.unlink(missing_ok=True)
            last_error = str(exc)
            if attempt >= attempts:
                raise PipelineError(
                    f"Fetching {url} failed after {attempts} attempt(s): {exc}"
                ) from exc
            LOGGER.warning("Fetching %s failed (%s); retrying.", url, str(exc)[:120])
            continue

        got = partial.stat().st_size
        if declared is not None and got != declared:
            partial.unlink(missing_ok=True)
            last_error = f"got {got} bytes, expected {declared}"
            if attempt >= attempts:
                warn(
                    collected,
                    f"The reverse-zone archive for {day} kept arriving truncated "
                    f"({last_error}) after {attempts} attempt(s); the day is absent "
                    "from this corpus rather than empty.",
                    LOGGER,
                )
                return None
            LOGGER.warning("Truncated download of %s (%s); retrying.", url, last_error)
            continue
        break

    # The archive publishes zero-byte placeholders for days it has no data for --
    # 2009-06-01 through 06-07 are all 0 bytes and served with HTTP 200. That is a
    # gap in the series, not a failed transfer, so it must skip rather than abort a
    # range that is otherwise fine.
    if partial.stat().st_size == 0:
        partial.unlink(missing_ok=True)
        warn(
            collected,
            f"The reverse-zone archive for {day} is published but empty "
            "(zero bytes); treated as a gap in the series.",
            LOGGER,
        )
        return None

    partial.replace(destination)
    return destination


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #


def parse_zone_text(text: str) -> tuple[list[tuple[str, int, int, int]], set[str]]:
    """Pull DS records and delegated names out of one zone file.

    Returns ``(ds_rows, delegated_names)`` where each DS row is
    ``(name, key_tag, algorithm, digest_type)``. The digest itself is discarded:
    no indicator tests it, and keeping a hex string per record would multiply the
    corpus size for nothing.

    Comments, ``$``-directives and blank lines are skipped. A record type this
    corpus does not carry a signal for is ignored rather than parsed, which keeps
    the parser honest about how little it claims to understand.
    """
    ds_rows: list[tuple[str, int, int, int]] = []
    delegated: set[str] = set()

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(";") or line.startswith("$"):
            continue

        match = _DS.match(line)
        if match is not None:
            ds_rows.append(
                (
                    match["name"].lower().rstrip("."),
                    int(match["key_tag"]),
                    int(match["algorithm"]),
                    int(match["digest_type"]),
                )
            )
            continue

        match = _NS.match(line)
        if match is not None:
            delegated.add(match["name"].lower().rstrip("."))

    return ds_rows, delegated


def _members(archive: tarfile.TarFile) -> Iterator[tarfile.TarInfo]:
    for member in archive:
        if not member.isfile():
            continue
        if member.name.endswith(_SKIP_SUFFIXES):
            continue
        yield member


def _rir_of(member_name: str) -> str | None:
    """``20240101/arin/041-ARIN`` -> ``arin``."""
    parts = member_name.split("/")
    if len(parts) < 3:
        return None
    rir = parts[1].strip().lower()
    return rir if rir in RIR_SOURCES else None


def read_archive(
    tarball: Path | str,
) -> dict[str, tuple[list[tuple[str, int, int, int]], set[str]]]:
    """Parse a whole daily tarball into per-RIR ``(ds_rows, delegated_names)``."""
    per_rir: dict[str, tuple[list, set]] = {
        rir: ([], set()) for rir in RIR_SOURCES
    }
    with tarfile.open(tarball, "r:bz2") as archive:
        for member in _members(archive):
            rir = _rir_of(member.name)
            if rir is None:
                continue
            handle = archive.extractfile(member)
            if handle is None:
                continue
            text = handle.read().decode("utf-8", "replace")
            ds_rows, delegated = parse_zone_text(text)
            per_rir[rir][0].extend(ds_rows)
            per_rir[rir][1].update(delegated)
    return per_rir


# --------------------------------------------------------------------------- #
# Emitting OpenINTEL-shaped rows
# --------------------------------------------------------------------------- #


def build_frame(
    day: date,
    rir: str,
    ds_rows: Sequence[tuple[str, int, int, int]],
    delegated: Iterable[str],
) -> pd.DataFrame:
    """Rows in OpenINTEL's native column names, so the existing scan reads them.

    Two record types are emitted:

    ``DS``
        One row per DS record. This is the DNSSEC signal, and it carries the
        algorithm and digest type that RFC 4509, 6605 and 8080 are matched on.
    ``NS``
        One row per *distinct* delegated name -- not per NS record. A delegation
        with four nameservers is one delegation, and counting it four times would
        make the denominator a function of how many nameservers operators happen
        to run.

    The timestamp is midnight UTC on the snapshot day, in epoch milliseconds,
    which is the unit OpenINTEL uses and the reader already decodes.
    """
    stamp = int(
        datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp() * 1000
    )
    # Sorted so a re-ingestion of the same day produces a byte-identical file.
    delegated_list = sorted(delegated)
    names = [name for name, _, _, _ in ds_rows] + delegated_list
    types = ["DS"] * len(ds_rows) + ["NS"] * len(delegated_list)

    key_tags = [tag for _, tag, _, _ in ds_rows] + [None] * len(delegated_list)
    algorithms = [alg for _, _, alg, _ in ds_rows] + [None] * len(delegated_list)
    digests = [dig for _, _, _, dig in ds_rows] + [None] * len(delegated_list)

    return pd.DataFrame(
        {
            "timestamp": pd.Series([stamp] * len(names), dtype="int64"),
            "query_name": pd.Series(names, dtype="object"),
            "response_name": pd.Series(names, dtype="object"),
            "response_type": pd.Series(types, dtype="object"),
            "ds_key_tag": pd.Series(key_tags, dtype="Int32"),
            "ds_algorithm": pd.Series(algorithms, dtype="Int32"),
            "ds_digest_type": pd.Series(digests, dtype="Int32"),
            "source": pd.Series([rir] * len(names), dtype="object"),
        }
    )


def ingest_day(
    day: date,
    *,
    cache_dir: Path | str,
    download_dir: Path | str,
    keep_archive: bool = False,
    warnings: list[str] | None = None,
) -> IngestReport | None:
    """Fetch, parse and write one day. Returns ``None`` if the day is not published.

    Idempotent: a day whose Parquet files all exist is not re-parsed, so a
    long ingestion can be interrupted and resumed like any other part of this
    pipeline.
    """
    collected = warnings if warnings is not None else []
    report = IngestReport(day=day, warnings=collected)
    started = time.time()

    expected = [parquet_path(day, rir, cache_dir) for rir in RIR_SOURCES]
    if all(path.is_file() and path.stat().st_size > 0 for path in expected):
        LOGGER.info("Already ingested, skipping: %s", day.isoformat())
        report.paths = expected
        return report

    tarball = fetch_archive(day, download_dir, warnings=collected)
    if tarball is None:
        return None

    try:
        per_rir = read_archive(tarball)
    except (tarfile.TarError, EOFError, OSError, ValueError) as exc:
        # Discard the local copy so a re-run re-fetches it, but do not abort: one
        # damaged day in a 57-day range should cost that day, not the range. The
        # day is absent from the corpus rather than empty, and the warning says so.
        tarball.unlink(missing_ok=True)
        warn(
            collected,
            f"Reverse-zone archive for {day} is unreadable ({exc}); the local copy "
            "was discarded and the day is absent from this corpus, not empty. "
            "Re-run to fetch it again.",
            LOGGER,
        )
        return None

    for rir, (ds_rows, delegated) in per_rir.items():
        delegated_list = sorted(delegated)
        if not ds_rows and not delegated_list:
            continue
        frame = build_frame(day, rir, ds_rows, delegated_list)
        destination = parquet_path(day, rir, cache_dir)
        ensure_dir(destination.parent)
        frame.to_parquet(destination, index=False, compression="zstd")

        report.paths.append(destination)
        report.rows += len(frame)
        report.ds_records += len(ds_rows)
        report.delegations += len(delegated_list)
        report.signed_delegations += len({name for name, _, _, _ in ds_rows})
        report.per_rir[rir] = len(frame)

    if not keep_archive:
        tarball.unlink(missing_ok=True)

    _write_summary(day, cache_dir, per_rir)
    report.elapsed_seconds = time.time() - started
    LOGGER.info("Ingested %s", report.describe())
    return report



#: Per-day counts live beside the Parquet, not inside it.
#:
#: The scan's record-type prefilter drops NS rows before anything is counted --
#: correctly, because no indicator matches on a bare delegation -- so the
#: delegation total never reaches the aggregates. That total is the one thing this
#: corpus has that OpenINTEL does not: a real denominator. Writing it here keeps it
#: without weakening the prefilter that makes the scan tractable.
SUMMARY_DIRNAME = "_summary"


def summary_path(day: date, cache_dir: Path | str) -> Path:
    return Path(cache_dir) / REVERSE_BASIS / SUMMARY_DIRNAME / f"{day.isoformat()}.json"


def _write_summary(day: date, cache_dir: Path | str, per_rir: dict) -> Path:
    payload = {
        "date": day.isoformat(),
        "basis": REVERSE_BASIS,
        "per_rir": {
            rir: {
                "delegations": len(delegated),
                "signed_delegations": len({n for n, _, _, _ in ds_rows}),
                "ds_records": len(ds_rows),
            }
            for rir, (ds_rows, delegated) in per_rir.items()
        },
    }
    totals = {
        key: sum(v[key] for v in payload["per_rir"].values())
        for key in ("delegations", "signed_delegations", "ds_records")
    }
    totals["signed_share"] = (
        totals["signed_delegations"] / totals["delegations"] if totals["delegations"] else 0.0
    )
    payload["totals"] = totals

    destination = summary_path(day, cache_dir)
    ensure_dir(destination.parent)
    destination.write_text(
        json.dumps(payload, indent=2) + chr(10), encoding="utf-8", newline=chr(10)
    )
    return destination


def load_summaries(cache_dir: Path | str) -> list[dict]:
    """Every per-day summary written by :func:`ingest_day`, oldest first."""
    directory = Path(cache_dir) / REVERSE_BASIS / SUMMARY_DIRNAME
    if not directory.is_dir():
        return []
    out = []
    for path in sorted(directory.glob("*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return out


def ingest_range(
    days: Sequence[date],
    *,
    cache_dir: Path | str,
    download_dir: Path | str,
    keep_archive: bool = False,
    warnings: list[str] | None = None,
) -> list[IngestReport]:
    """Ingest each day in turn, skipping days the archive does not publish."""
    collected = warnings if warnings is not None else []
    reports: list[IngestReport] = []
    for index, day in enumerate(days, start=1):
        if day < ARCHIVE_START:
            warn(
                collected,
                f"{day} precedes the reverse-zone archive, which starts "
                f"{ARCHIVE_START}; skipped.",
                LOGGER,
            )
            continue
        report = ingest_day(
            day,
            cache_dir=cache_dir,
            download_dir=download_dir,
            keep_archive=keep_archive,
            warnings=collected,
        )
        if report is not None:
            reports.append(report)
        LOGGER.info("Reverse-zone ingest %d/%d days", index, len(days))
    return reports


def monthly_days(start: date, end: date, *, day_of_month: int = 1) -> list[date]:
    """One day per month across a range.

    A 17-year daily ingestion is 6,108 tarballs and several hundred gigabytes;
    monthly sampling costs about 210 and still resolves an adoption curve to the
    month, which is finer than any of the conclusions drawn from it.
    """
    out: list[date] = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        try:
            candidate = date(year, month, day_of_month)
        except ValueError:  # pragma: no cover - day 29-31 in a short month
            candidate = date(year, month, 28)
        if start <= candidate <= end:
            out.append(candidate)
        month += 1
        if month > 12:
            year, month = year + 1, 1
    return out
