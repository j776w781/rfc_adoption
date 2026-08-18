"""Streaming, checkpointed execution of the RFC matcher over real OpenINTEL data.

The MVP entry point (``openintel_rfc.cli analyze``) materializes one
:class:`~openintel_rfc.models.ObservedSignal` per row and one
:class:`~openintel_rfc.models.ReasoningTrace` per (signal x RFC). At the target
scale -- several TLDs over several years, order 10^10-10^11 rows against 8 RFCs
-- that is 10^11 traces and cannot exist. This module is the second entry point,
not a replacement: the MVP path is untouched and stays the reference
implementation.

The division of labour
----------------------
**SQL decides which rows match which indicators.** One DuckDB query per
partition applies the record-type prefilter, resolves the OpenINTEL column
aliases, evaluates every indicator, applies the publication-date cutoff and
groups the result down to
``(rfc_id, indicator_id, decision, source, year_month)``. See
:mod:`openintel_rfc.sql_compiler` for how the checklist becomes that query.

**Python still owns scoring and the decision rules.** The scoring formula is
never written in SQL. Scores come from :func:`openintel_rfc.ranking.score_match`
applied to sampled exemplar rows that are pushed through the *existing*
``signal_extractor`` -> ``matcher.match_all`` -> ``reasoning`` path, so a real
:class:`~openintel_rfc.models.ReasoningTrace` backs every claim in the output.
The decision rules are Python's too: :func:`sql_compiler.compile_checklist` asks
``score_match`` what each evidence pattern means and emits the answer as a lookup
table, so the SQL path cannot drift from the Python path without the Python path
changing first.

What the numbers mean
---------------------
Two kinds of number come out of a scale run and they must not be confused:

* **Corpus totals** -- observation counts, first/last seen, per-month counts.
  These are exact, computed over every row that was scanned.
* **Exemplar-derived detail** -- scores, reasoning traces, example signal ids,
  the domain and zone *lists*. These come from a bounded sample.

Every candidate and timeline entry says which is which in its own prose, and the
run's ``warnings`` restate it. A report that let a reader take the exemplar count
for the corpus count would be worse than no report.

Distinct-domain counts are the one genuinely approximate figure.
``approx_count_distinct`` is exact enough within a partition but its sketches are
not merged across partitions, so a merged count is reported as the largest
single-partition estimate -- a lower bound -- with the sum recorded separately as
the upper bound. Neither is presented as the truth.

Checkpointing
-------------
A run over several years takes days. Every partition writes its aggregate to
``<checkpoint_dir>/<partition_id>.parquet`` and a small status file next to it,
status last so a partial write can never look complete. On resume a checkpoint is
skipped only if it reads back cleanly, carries the expected row count, and was
produced by the same compiled checklist; anything else is recomputed with a
warning. A corrupt checkpoint is never silently trusted.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .config import (
    ALWAYS_SELECT_FIELDS,
    DEFAULT_MAX_PACE_SECONDS,
    DEFAULT_PACE_SECONDS,
    OPENINTEL_REQUESTS_PER_SECOND,
)
from .models import (
    AdoptionTimelineEntry,
    ObservedSignal,
    OpenINTELDictionary,
    PipelineResult,
    RankedRFCCandidate,
    ReasoningTrace,
    ReviewItem,
    RFCChecklistDB,
    RFCMatch,
    RunConfig,
    SchemaCheckReport,
    TimelineBucket,
)
from .parquet_reader import describe_parquet
from .ranking import ADOPTION_DECISIONS, RANKABLE_DECISIONS, rank_candidates
from .schema_checker import queryable_field_names
from .signal_extractor import PROVENANCE_FIELDS, SIGNAL_FIELDS, extract_signals
from .sql_compiler import (
    CompiledChecklist,
    MATCHED_DECISION,
    PAIR_COLUMN,
    ROLLUP_INDICATOR_ID,
    SCANNED_DECISION,
    TOTALS_RFC_ID,
    build_column_expressions,
    build_scan_sql,
    compile_checklist,
    quote_identifier,
    quote_string,
    scan_fields,
)
from .utils import (
    PipelineError,
    ensure_dir,
    get_logger,
    iso,
    now,
    round_score,
    unique_sorted,
    warn,
)

__all__ = [
    "ScaleRunConfig",
    "LocalPartition",
    "PartitionResult",
    "AggregateRow",
    "AggregateTable",
    "CHECKPOINT_SUFFIX",
    "STATUS_SUFFIX",
    "EXEMPLAR_DIRNAME",
    "run_scale_analysis",
    "process_partition",
    "merge_checkpoints",
    "aggregates_to_candidates",
    "aggregates_to_timeline",
]

LOGGER = get_logger(__name__)

CHECKPOINT_SUFFIX = ".parquet"
STATUS_SUFFIX = ".status.json"
EXEMPLAR_DIRNAME = "exemplars"

#: Columns of the per-partition aggregate checkpoint.
AGGREGATE_COLUMNS: tuple[str, ...] = (
    "rfc_id",
    "indicator_id",
    "decision",
    "source",
    "year_month",
    "count",
    "first_seen",
    "last_seen",
    "approx_domains",
    "approx_zones",
)


# --------------------------------------------------------------------------- #
# Staying under the store's request budget
# --------------------------------------------------------------------------- #


@dataclass
class ThrottleGovernor:
    """Adaptive gap between partitions: fast backoff, slow relief.

    A fixed `--pace-seconds` cannot be right for both halves of a run. Too small
    and a busy period collapses into a 503 storm; too large and thousands of
    quiet partitions each pay for a busy period that may never come. So the pace
    responds to evidence: every throttled partition doubles it, every clean one
    decays it back toward the floor.

    ``shards`` divides the budget. N processes sharing one bucket may each spend
    only 1/N of it, so the floor is multiplied by N -- the failure the overnight
    run hit was N shards each being individually polite while the aggregate was N
    times over.
    """

    floor_seconds: float = DEFAULT_PACE_SECONDS
    ceiling_seconds: float = DEFAULT_MAX_PACE_SECONDS
    shards: int = 1
    #: How much a throttled partition multiplies the gap by.
    backoff_factor: float = 2.0
    #: How much a clean partition shrinks it by. Deliberately far slower than the
    #: backoff: recovering faster than the store forgets re-triggers the limiter.
    recovery_factor: float = 0.9

    throttle_events: int = field(default=0, init=False)
    _delay: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self.shards = max(int(self.shards), 1)
        self.floor_seconds = max(float(self.floor_seconds), 0.0)
        self.ceiling_seconds = max(float(self.ceiling_seconds), self._floor)
        self._delay = self._floor

    @property
    def _floor(self) -> float:
        return self.floor_seconds * self.shards

    @property
    def delay(self) -> float:
        """Seconds to wait before starting the next partition."""
        return self._delay

    def on_throttled(self) -> None:
        self.throttle_events += 1
        # max(..., 1/rate) so the first throttle produces a real gap even when
        # the run was configured with no pacing at all.
        widened = max(self._delay * self.backoff_factor,
                      self.shards / OPENINTEL_REQUESTS_PER_SECOND)
        self._delay = min(widened, self.ceiling_seconds)

    def on_success(self) -> None:
        self._delay = max(self._floor, self._delay * self.recovery_factor)

    def wait(self) -> None:
        if self._delay > 0:
            time.sleep(self._delay)


# --------------------------------------------------------------------------- #
# Configuration and partition handles
# --------------------------------------------------------------------------- #


@dataclass(kw_only=True)
class ScaleRunConfig:
    """Inputs for one scale run.

    Keyword-only by design: the field list is long, several fields are optional,
    and a positional call site would be unreadable and easy to get wrong.

    ``access`` is an ``openintel_source.AccessConfig``; it is typed loosely so
    that this module never has to import that one at definition time (and so that
    local runs, which pass ``None``, stay possible without it).
    """

    sources: list[str] = field(default_factory=list)
    start: date | None = None
    end: date | None = None
    basis: str = "zonefile"
    out: Path = Path("scale_output")
    checkpoint_dir: Path = Path("scale_checkpoints")
    access: Any = None
    exemplars_per_group: int = 5
    max_partitions: int | None = None
    resume: bool = True

    #: Partition-level retry. DuckDB retries individual HTTP requests, but a
    #: store that is throttling hard exhausts those and fails the whole query;
    #: without this a multi-day walk dies at an arbitrary partition. The waits
    #: double from `partition_retry_wait_seconds`, so the default budget is
    #: roughly 30+60+120+240 = 7.5 minutes before giving up on a partition.
    partition_retries: int = 5
    partition_retry_wait_seconds: float = 30.0

    #: Floor for the gap between partitions. The store allows about one request
    #: per second with a burst of about five (see `ThrottleGovernor`), so this is
    #: not merely politeness -- a run with no gap at all overflows the burst queue
    #: and is rejected. The gap is adaptive: this is the smallest it ever gets.
    pace_seconds: float = DEFAULT_PACE_SECONDS
    #: Largest the adaptive gap may grow to before the run is simply stuck.
    max_pace_seconds: float = DEFAULT_MAX_PACE_SECONDS
    #: How many processes are sharing the store's budget with this one. A sharded
    #: run must declare it: N shards each pacing for the whole budget is N times
    #: over it, which is what made the overnight run collapse into 503s.
    shards: int = 1
    #: Recorded in the run manifest so an output directory names its own inputs.
    checklists: Path | str | None = None
    dictionary: Path | str | None = None
    #: Optional cap on rows read *per partition*; for smoke runs, not production.
    limit_per_partition: int | None = None
    min_score: float = 0.0

    def __post_init__(self) -> None:
        self.out = Path(self.out)
        self.checkpoint_dir = Path(self.checkpoint_dir)
        if self.exemplars_per_group < 1:
            raise PipelineError(
                f"exemplars_per_group must be >= 1, got {self.exemplars_per_group}: "
                "a run with no exemplars would produce aggregates that nothing explains."
            )
        if self.max_partitions is not None and self.max_partitions < 1:
            raise PipelineError(f"max_partitions must be >= 1, got {self.max_partitions}.")


@dataclass(frozen=True)
class LocalPartition:
    """A partition backed by Parquet files already on this filesystem.

    ``openintel_source.Partition`` is the object a real run uses; this is the
    same duck type for local files. Having it here keeps a local corpus (and the
    test suite) runnable without any object-store access at all.
    """

    partition_id: str
    source: str = "local"
    paths: tuple[str, ...] = ()
    columns: tuple[str, ...] = ()
    basis: str = "local"
    date: date | None = None

    @classmethod
    def from_paths(
        cls,
        paths: Sequence[Path | str],
        *,
        partition_id: str | None = None,
        source: str | None = None,
    ) -> LocalPartition:
        """Build a partition from local Parquet paths, probing their schema."""
        resolved = [Path(p) for p in paths]
        if not resolved:
            raise PipelineError("LocalPartition.from_paths requires at least one path.")
        columns: dict[str, None] = {}
        for path in resolved:
            for column in describe_parquet(path)["columns"]:
                columns.setdefault(str(column["name"]), None)
        identifier = partition_id or _stable_partition_id(resolved)
        return cls(
            partition_id=identifier,
            source=source or resolved[0].parent.name or "local",
            paths=tuple(p.as_posix() for p in resolved),
            columns=tuple(columns),
        )


def _stable_partition_id(paths: Sequence[Path]) -> str:
    """A filesystem-safe id that is the same for the same file set every run."""
    joined = "|".join(sorted(p.as_posix() for p in paths))
    digest = hashlib.sha1(joined.encode("utf-8")).hexdigest()[:10]
    stem = "".join(c if c.isalnum() or c in "-_" else "_" for c in paths[0].stem)[:40]
    return f"{stem}_{digest}"


@dataclass
class PartitionResult:
    """What one partition contributed, and what it cost."""

    partition_id: str
    source: str
    checkpoint_path: Path
    status_path: Path
    exemplar_path: Path
    rows_scanned: int = 0
    rows_matched: int = 0
    aggregate_rows: int = 0
    exemplar_rows: int = 0
    elapsed_seconds: float = 0.0
    reused: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def selectivity(self) -> float | None:
        """Fraction of scanned rows that reached a rankable decision."""
        if not self.rows_scanned:
            return None
        return self.rows_matched / self.rows_scanned


# --------------------------------------------------------------------------- #
# Aggregates
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class AggregateRow:
    """One merged aggregate group.

    ``indicator_id == '*'`` is the per-RFC roll-up: one contribution per scanned
    row, so ``no_match`` observations are counted rather than disappearing.
    ``rfc_id == '*'`` carries the two scan totals (``scanned`` / ``matched``).
    """

    rfc_id: str
    indicator_id: str
    decision: str
    source: str
    year_month: str
    count: int
    first_seen: datetime | None
    last_seen: datetime | None
    #: Largest single-partition ``approx_count_distinct``: a lower bound.
    approx_domains: int
    #: Sum over partitions: an upper bound, since sketches are not merged.
    approx_domains_upper: int
    approx_zones: int
    approx_zones_upper: int


@dataclass
class AggregateTable:
    """Every partition's aggregates, merged, plus the exemplars that explain them."""

    rows: list[AggregateRow] = field(default_factory=list)
    exemplars: pd.DataFrame = field(default_factory=pd.DataFrame)
    partition_ids: list[str] = field(default_factory=list)
    exemplars_per_group: int = 0
    warnings: list[str] = field(default_factory=list)
    #: Cache for the exemplar matcher run; see :meth:`evidence`.
    _evidence: tuple[list[ObservedSignal], list[RFCMatch], list[ReasoningTrace]] | None = None

    # -- totals ---------------------------------------------------------- #

    @property
    def rows_scanned(self) -> int:
        return sum(
            r.count
            for r in self.rows
            if r.rfc_id == TOTALS_RFC_ID and r.decision == SCANNED_DECISION
        )

    @property
    def rows_matched(self) -> int:
        return sum(
            r.count
            for r in self.rows
            if r.rfc_id == TOTALS_RFC_ID and r.decision == MATCHED_DECISION
        )

    def rfc_rows(self) -> list[AggregateRow]:
        """Aggregate rows about RFCs, i.e. everything except the scan totals."""
        return [r for r in self.rows if r.rfc_id != TOTALS_RFC_ID]

    def rollup_rows(self, *, decisions: Sequence[str] | None = None) -> list[AggregateRow]:
        """Per-RFC roll-up rows, optionally restricted to some decisions."""
        allowed = None if decisions is None else set(decisions)
        return [
            r
            for r in self.rfc_rows()
            if r.indicator_id == ROLLUP_INDICATOR_ID
            and (allowed is None or r.decision in allowed)
        ]

    def decision_counts(self) -> dict[tuple[str, str], int]:
        """Observation count per (rfc_id, decision), summed over the whole corpus."""
        counts: dict[tuple[str, str], int] = {}
        for row in self.rollup_rows():
            key = (row.rfc_id, row.decision)
            counts[key] = counts.get(key, 0) + row.count
        return counts

    def first_seen(self, rfc_id: str, *, decisions: Sequence[str] = ADOPTION_DECISIONS) -> datetime | None:
        stamps = [
            r.first_seen
            for r in self.rollup_rows(decisions=decisions)
            if r.rfc_id == rfc_id and r.first_seen is not None
        ]
        return min(stamps) if stamps else None

    def last_seen(self, rfc_id: str, *, decisions: Sequence[str] = ADOPTION_DECISIONS) -> datetime | None:
        stamps = [
            r.last_seen
            for r in self.rollup_rows(decisions=decisions)
            if r.rfc_id == rfc_id and r.last_seen is not None
        ]
        return max(stamps) if stamps else None

    # -- exemplar evidence ------------------------------------------------ #

    def evidence(
        self,
        db: RFCChecklistDB,
        *,
        schema_report: SchemaCheckReport | None = None,
        warnings: list[str] | None = None,
    ) -> tuple[list[ObservedSignal], list[RFCMatch], list[ReasoningTrace]]:
        """Run the sampled exemplars through the real matcher, once.

        Deliberately the *existing* extractor / matcher / reasoning path: the
        traces backing a scale run have to be the same objects the MVP produces,
        or the explanations would be a second implementation nobody tested.
        """
        if self._evidence is None:
            frame = self.exemplar_frame()
            collected = warnings if warnings is not None else []
            signals = extract_signals(
                frame, origin_file="scale_exemplars", warnings=collected
            )
            from .matcher import match_all  # local: keeps the import graph acyclic

            matches, traces = match_all(signals, db, schema_report, warnings=collected)
            self._evidence = (signals, matches, traces)
        return self._evidence

    def exemplar_frame(self) -> pd.DataFrame:
        """The sampled rows as a frame the signal extractor accepts.

        Deduplicated (one row can be the exemplar of several groups) and ordered
        by value, so signal ids are stable across runs.
        """
        if self.exemplars is None or self.exemplars.empty:
            return pd.DataFrame({name: pd.Series(dtype="object") for name in _EXEMPLAR_COLUMNS})
        columns = [c for c in self.exemplars.columns if c in _EXEMPLAR_COLUMNS]
        frame = self.exemplars[columns].copy()
        order = [c for c in _EXEMPLAR_COLUMNS if c in frame.columns]
        frame = frame[order]
        frame = frame.drop_duplicates()
        sort_keys = [c for c in order if c in frame.columns]
        frame = frame.sort_values(
            by=sort_keys, kind="mergesort", na_position="last"
        ).reset_index(drop=True)
        return frame


#: Column order of the exemplar frame handed to the signal extractor. Nothing
#: else may be in it: an extra column becomes an "observed field" in every trace.
_EXEMPLAR_COLUMNS: tuple[str, ...] = (*PROVENANCE_FIELDS, *SIGNAL_FIELDS)


# --------------------------------------------------------------------------- #
# Per-partition execution
# --------------------------------------------------------------------------- #


def _sql_fingerprint(statement: str) -> str:
    return hashlib.sha1(statement.encode("utf-8")).hexdigest()


def _checkpoint_key(partition: Any) -> str:
    """A flat, file-name-safe token identifying one partition's checkpoint.

    ``openintel_source.Partition.partition_id`` is a *path* -- ``zonefile/nu/
    2018-05-01`` -- which would scatter checkpoints across nested directories
    where the top-level glob in :func:`merge_checkpoints` could not see them.
    ``Partition`` exposes ``slug`` for exactly this; anything without one is
    sanitized here so that no partition identity can ever escape the checkpoint
    directory.
    """
    token = str(
        getattr(partition, "slug", None)
        or getattr(partition, "partition_id", "")
        or "partition"
    )
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in token) or "partition"


def _checkpoint_paths(checkpoint_dir: Path, key: str) -> tuple[Path, Path, Path]:
    directory = Path(checkpoint_dir)
    return (
        directory / f"{key}{CHECKPOINT_SUFFIX}",
        directory / f"{key}{STATUS_SUFFIX}",
        directory / EXEMPLAR_DIRNAME / f"{key}{CHECKPOINT_SUFFIX}",
    )


def _read_status(status_path: Path) -> dict[str, Any] | None:
    try:
        with status_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _checkpoint_problem(
    checkpoint_path: Path,
    status_path: Path,
    *,
    fingerprint: str,
    checklist_version: str,
) -> str | None:
    """Why an existing checkpoint may not be trusted, or ``None`` if it may.

    Every failure mode here means "recompute", never "use anyway". A silently
    accepted truncated Parquet file would under-count a whole day and nothing
    downstream could tell.
    """
    if not status_path.is_file():
        return "the status file is missing, so the partition was interrupted mid-write"
    status = _read_status(status_path)
    if status is None:
        return "the status file is not readable JSON"
    if not status.get("complete"):
        return "the status file does not mark the partition complete"
    if not checkpoint_path.is_file():
        return "the aggregate Parquet file is missing"
    if status.get("scan_sql_sha1") != fingerprint:
        return (
            "it was produced by a different compiled scan (checklist, dictionary or "
            "column resolution changed), so its aggregates answer a different question"
        )
    if status.get("checklist_version") != checklist_version:
        return "it was produced from a different checklist version"
    try:
        frame = pd.read_parquet(checkpoint_path)
    except Exception as exc:  # pyarrow raises a family of unrelated errors
        return f"the aggregate Parquet file could not be read ({exc})"
    expected = status.get("aggregate_rows")
    if isinstance(expected, int) and len(frame) != expected:
        return (
            f"the aggregate Parquet file holds {len(frame)} row(s) but the status file "
            f"claims {expected}, so the write was truncated"
        )
    missing = [c for c in AGGREGATE_COLUMNS if c not in frame.columns]
    if missing:
        return f"the aggregate Parquet file is missing column(s): {', '.join(missing)}"
    return None


def _write_atomic_parquet(frame: pd.DataFrame, path: Path) -> None:
    ensure_dir(path.parent)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_parquet(temporary, engine="pyarrow", index=False)
    os.replace(temporary, path)


def _write_atomic_json(payload: Mapping[str, Any], path: Path) -> None:
    ensure_dir(path.parent)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _exemplar_struct_sql(fields: Sequence[str]) -> str:
    """One struct per sampled row: its normalized fields plus its sort key.

    Carrying ``sample_hash`` inside the struct is what lets
    :func:`_reduce_exemplars` narrow a multi-partition run's samples down to the
    same rows a single-partition run would have kept.
    """
    entries = [f"{quote_string('sample_hash')}: sample_hash"]
    entries += [f"{quote_string(name)}: s.{quote_identifier(name)}" for name in fields]
    return "{" + ", ".join(entries) + "}"


def _sample_hash_sql(fields: Sequence[str], partition_id: str) -> str:
    """A per-row sort key that is stable for a given partition.

    Reservoir sampling with a random generator would give a different sample
    every run, which would make two runs over the same partition disagree about
    which observations they can show. Hashing the row's own values together with
    the partition id gives an unbiased but fixed order instead.
    """
    parts = [quote_string(partition_id)]
    parts += [
        f"COALESCE(CAST(s.{quote_identifier(name)} AS VARCHAR), '')" for name in fields
    ]
    return "md5(concat_ws('|', " + ", ".join(parts) + "))"


def build_aggregate_sql(
    scan_sql: str,
    *,
    fields: Sequence[str],
    partition_id: str,
    source: str,
    exemplars_per_group: int,
) -> str:
    """Wrap a row-level scan in the single aggregation query for one partition.

    One query, one pass: the prefilter, the alias resolution, the per-indicator
    evaluation, the publication-date cutoff, the grouping *and* the exemplar
    sample all happen inside it. The exemplars ride along as an ``arg_min`` over
    the row hash, which is why sampling costs no extra scan.
    """
    source_expr = (
        f"COALESCE(CAST(s.{quote_identifier('source')} AS VARCHAR), {quote_string(source)})"
        if "source" in fields
        else quote_string(source)
    )
    domain_expr = (
        f"CAST(s.{quote_identifier('domain')} AS VARCHAR)" if "domain" in fields else "NULL"
    )
    zone_expr = (
        f"CAST(s.{quote_identifier('zone')} AS VARCHAR)" if "zone" in fields else "NULL"
    )
    return (
        "WITH scan AS (\n"
        + scan_sql
        + "\n),\nexploded AS (\n"
        "  SELECT\n"
        "    u.pair.rfc_id AS rfc_id,\n"
        "    u.pair.indicator_id AS indicator_id,\n"
        "    u.pair.decision AS decision,\n"
        f"    {source_expr} AS source,\n"
        "    strftime(s.\"timestamp\", '%Y-%m') AS year_month,\n"
        "    s.\"timestamp\" AS observation_timestamp,\n"
        f"    {domain_expr} AS domain,\n"
        f"    {zone_expr} AS zone,\n"
        f"    {_sample_hash_sql(fields, partition_id)} AS sample_hash,\n"
        f"    {_exemplar_struct_sql(fields)} AS exemplar\n"
        f"  FROM scan s, UNNEST(s.{quote_identifier(PAIR_COLUMN)}) AS u(pair)\n"
        ")\n"
        "SELECT\n"
        "  rfc_id,\n"
        "  indicator_id,\n"
        "  decision,\n"
        "  source,\n"
        "  year_month,\n"
        "  CAST(count(*) AS BIGINT) AS \"count\",\n"
        "  min(observation_timestamp) AS first_seen,\n"
        "  max(observation_timestamp) AS last_seen,\n"
        "  CAST(approx_count_distinct(domain) AS BIGINT) AS approx_domains,\n"
        "  CAST(approx_count_distinct(zone) AS BIGINT) AS approx_zones,\n"
        f"  arg_min(exemplar, sample_hash, {int(exemplars_per_group)}) "
        f"FILTER (WHERE indicator_id = {quote_string(ROLLUP_INDICATOR_ID)} "
        f"AND rfc_id <> {quote_string(TOTALS_RFC_ID)}) AS exemplars\n"
        "FROM exploded\n"
        "GROUP BY 1, 2, 3, 4, 5\n"
        "ORDER BY 1, 2, 3, 4, 5"
    )


#: Substrings identifying an error worth retrying: a shared object store under
#: load, not a bug in the query. Matched case-insensitively against the message,
#: because DuckDB surfaces HTTP failures as generic exceptions.
#:
#: ``403`` is here because of what the endpoint actually does. nginx fronts the
#: object store and rejects an overflowing ``limit_req`` queue with 503, but an
#: address it has decided to block gets 403 -- with nginx's own HTML body, not
#: the store's XML. Neither says the request was malformed, so both are worth
#: waiting out. Distinguishing them from a genuine permission failure is
#: `_PERMANENT_AUTH_MARKERS`' job, and it is consulted first.
_TRANSIENT_MARKERS: tuple[str, ...] = (
    "403",
    "429",
    "500",
    "502",
    "503",
    "504",
    "forbidden",
    "service unavailable",
    "slow down",
    "slowdown",
    "too many requests",
    "timeout",
    "timed out",
    "connection reset",
    "connection closed",
    "temporarily unavailable",
    "could not establish connection",
)

#: Substrings identifying a *permission* failure rather than load. The bucket is
#: public and this client is meant to send no credentials at all; when one leaks
#: in -- ``AWS_ACCESS_KEY_ID`` in the environment, an instance profile on the
#: server, a stale ``~/.aws/credentials`` -- botocore and DuckDB sign every
#: request and the store refuses every one of them with a 403 carrying an
#: ``AccessDenied`` XML body.
#:
#: That failure is immediate, total and permanent, so it must not be retried:
#: spending the 7.5-minute budget per partition on it turns a one-line
#: misconfiguration into an overnight run that produces nothing and explains
#: nothing. Checked before `_TRANSIENT_MARKERS` because these messages carry
#: "403" too.
_PERMANENT_AUTH_MARKERS: tuple[str, ...] = (
    "accessdenied",
    "access denied",
    "signaturedoesnotmatch",
    "invalidaccesskeyid",
    "invalid access key",
    "expiredtoken",
    "tokenrefreshrequired",
)

#: What to tell an operator who hit the permanent case. It names the thing to
#: look at, because "AccessDenied" on a public bucket is otherwise baffling.
_ANONYMOUS_ACCESS_HELP = (
    "The object store refused the request as unauthorised. This bucket is public "
    "and the pipeline reads it anonymously, so this almost always means stray AWS "
    "credentials were picked up and used to sign the request. Check "
    "AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_SESSION_TOKEN in the "
    "environment, ~/.aws/credentials, and any instance profile on this host; "
    "unset them for this run. Retrying cannot help: the credential is wrong on "
    "every request, not just this one."
)


def _is_auth_failure(exc: BaseException) -> bool:
    """True when the store rejected the *identity*, not the load."""
    text = f"{type(exc).__name__}: {exc}".lower()
    return any(marker in text for marker in _PERMANENT_AUTH_MARKERS)


def _is_transient(exc: BaseException) -> bool:
    if _is_auth_failure(exc):
        return False
    text = f"{type(exc).__name__}: {exc}".lower()
    return any(marker in text for marker in _TRANSIENT_MARKERS)


def _process_with_retry(
    partition: Any,
    *,
    attempts: int,
    base_wait: float,
    warnings: list[str],
    governor: "ThrottleGovernor | None" = None,
    _process: Any = None,
    **kwargs: Any,
) -> PartitionResult:
    """Run one partition, retrying transient object-store failures.

    DuckDB retries individual HTTP requests internally, but when a store is
    throttling hard those retries are exhausted and the whole query fails. On a
    multi-day walk that would abandon the run at an arbitrary point. Retrying at
    the partition level, with a wait long enough for a rate limiter to relax,
    turns a fatal error into a pause.

    Waits are jittered. A sharded run is several processes drawing on one
    ``limit_req`` bucket; if they fail together and each sleeps exactly the same
    number of seconds, they return together and knock each other over again.
    Equal jitter -- half the backoff plus a random half -- keeps the growth while
    breaking the lockstep.

    ``governor``, when given, learns from what happened: a throttled partition
    widens the gap before the next one, a clean partition narrows it back toward
    the configured floor.

    A non-transient failure is raised immediately: retrying a malformed query or
    a genuinely missing object just wastes time and hides the real cause. A
    credential failure is raised with an explanation, because "AccessDenied" on a
    deliberately public bucket is otherwise baffling.

    ``_process`` is a test seam; production callers leave it unset.
    """
    run = _process if _process is not None else process_partition
    partition_id = getattr(partition, "partition_id", "?")
    wait = max(float(base_wait), 0.0)
    last: Exception | None = None

    for attempt in range(1, max(int(attempts), 1) + 1):
        try:
            result = run(partition, warnings=warnings, **kwargs)
        # Deliberately broad: the runner wraps DuckDB failures in PipelineError,
        # but httpfs raises its own exception hierarchy and a raw HTTPException
        # escaping here would defeat the whole point of retrying. Non-transient
        # errors are re-raised untouched on the first attempt.
        except Exception as exc:
            last = exc
            if _is_auth_failure(exc):
                raise PipelineError(
                    f"Partition {partition_id}: {_ANONYMOUS_ACCESS_HELP} "
                    f"Original error: {exc}"
                ) from exc
            if not _is_transient(exc):
                raise
            if governor is not None:
                governor.on_throttled()
            if attempt >= attempts:
                raise
            # Equal jitter: keep the doubling, lose the synchronisation.
            delay = wait / 2 + random.uniform(0.0, wait / 2) if wait > 0 else 0.0
            LOGGER.warning(
                "Partition %s failed with a transient error on attempt %d/%d "
                "(%s); retrying in %.1fs.",
                partition_id,
                attempt,
                attempts,
                str(exc).splitlines()[0][:160],
                delay,
            )
            time.sleep(delay)
            wait *= 2
        else:
            if governor is not None:
                governor.on_success()
            return result

    raise last if last is not None else PipelineError(  # pragma: no cover
        f"Partition {partition_id} failed without an recorded error."
    )


def process_partition(
    partition: Any,
    *,
    uris: Sequence[str],
    connection: Any,
    compiled: CompiledChecklist,
    column_expr: Mapping[str, str],
    checkpoint_dir: Path,
    prefilter: Sequence[str] | None = None,
    exemplars_per_group: int = 5,
    limit: int | None = None,
    resume: bool = True,
    warnings: list[str] | None = None,
) -> PartitionResult:
    """Evaluate one partition and checkpoint it.

    ``partition`` only has to carry ``partition_id`` and ``source``; both
    ``openintel_source.Partition`` and :class:`LocalPartition` do. Passing the
    URIs separately keeps this function independent of how they were discovered,
    which is what lets a local corpus run without any object-store access.

    Returns without touching the data when a usable checkpoint already exists and
    ``resume`` is set. "Usable" is checked, not assumed -- see
    :func:`_checkpoint_problem`.
    """
    collected = warnings if warnings is not None else []
    partition_id = str(getattr(partition, "partition_id", "") or "partition")
    source = str(getattr(partition, "source", "") or "unknown")
    fields = scan_fields(compiled, column_expr)
    effective_prefilter = (
        list(prefilter) if prefilter is not None else list(compiled.prefilter)
    )

    checkpoint_path, status_path, exemplar_path = _checkpoint_paths(
        checkpoint_dir, _checkpoint_key(partition)
    )
    scan_sql = build_scan_sql(
        uris, column_expr, compiled, prefilter=effective_prefilter, limit=limit
    )
    statement = build_aggregate_sql(
        scan_sql,
        fields=fields,
        partition_id=partition_id,
        source=source,
        exemplars_per_group=exemplars_per_group,
    )
    fingerprint = _sql_fingerprint(statement)

    result = PartitionResult(
        partition_id=partition_id,
        source=source,
        checkpoint_path=checkpoint_path,
        status_path=status_path,
        exemplar_path=exemplar_path,
    )

    if resume and checkpoint_path.is_file():
        problem = _checkpoint_problem(
            checkpoint_path,
            status_path,
            fingerprint=fingerprint,
            checklist_version=compiled.checklist_version,
        )
        if problem is None:
            status = _read_status(status_path) or {}
            result.reused = True
            result.rows_scanned = int(status.get("rows_scanned", 0))
            result.rows_matched = int(status.get("rows_matched", 0))
            result.aggregate_rows = int(status.get("aggregate_rows", 0))
            result.exemplar_rows = int(status.get("exemplar_rows", 0))
            result.elapsed_seconds = float(status.get("elapsed_seconds", 0.0))
            LOGGER.info(
                "Partition %s: reusing checkpoint (%d aggregate rows, %d rows scanned)",
                partition_id,
                result.aggregate_rows,
                result.rows_scanned,
            )
            return result
        message = (
            f"Checkpoint for partition {partition_id} was not reused because {problem}; "
            "it is being recomputed. A checkpoint that cannot be verified is never trusted."
        )
        warn(collected, message, LOGGER)
        result.warnings.append(message)

    started = time.monotonic()
    try:
        frame = connection.execute(statement).df()
    except Exception as exc:  # DuckDB raises its own error hierarchy
        raise PipelineError(
            f"DuckDB failed on partition {partition_id} ({len(uris)} object(s)): {exc}"
        ) from exc
    result.elapsed_seconds = time.monotonic() - started

    aggregates, exemplars = _split_partition_frame(frame, exemplars_per_group)
    result.rows_scanned = int(
        aggregates.loc[
            (aggregates["rfc_id"] == TOTALS_RFC_ID)
            & (aggregates["decision"] == SCANNED_DECISION),
            "count",
        ].sum()
    )
    result.rows_matched = int(
        aggregates.loc[
            (aggregates["rfc_id"] == TOTALS_RFC_ID)
            & (aggregates["decision"] == MATCHED_DECISION),
            "count",
        ].sum()
    )
    result.aggregate_rows = len(aggregates)
    result.exemplar_rows = len(exemplars)

    # Parquet first, status last: a status file only ever exists once the data it
    # describes is fully on disk.
    _write_atomic_parquet(aggregates, checkpoint_path)
    _write_atomic_parquet(exemplars, exemplar_path)
    _write_atomic_json(
        {
            "partition_id": partition_id,
            "source": source,
            "basis": str(getattr(partition, "basis", "") or ""),
            "date": iso(getattr(partition, "date", None))
            if isinstance(getattr(partition, "date", None), datetime)
            else str(getattr(partition, "date", "") or ""),
            "object_count": len(uris),
            "rows_scanned": result.rows_scanned,
            "rows_matched": result.rows_matched,
            "aggregate_rows": result.aggregate_rows,
            "exemplar_rows": result.exemplar_rows,
            "exemplars_per_group": int(exemplars_per_group),
            "elapsed_seconds": round(result.elapsed_seconds, 3),
            "prefilter": sorted(effective_prefilter),
            "checklist_version": compiled.checklist_version,
            "scan_sql_sha1": fingerprint,
            "complete": True,
            "completed_at": iso(now()),
        },
        status_path,
    )

    selectivity = result.selectivity
    LOGGER.info(
        "Partition %s: %d rows scanned, %d matched (%s), %d aggregate rows, "
        "%d exemplars, %.2fs",
        partition_id,
        result.rows_scanned,
        result.rows_matched,
        "n/a" if selectivity is None else f"{selectivity:.4%}",
        result.aggregate_rows,
        result.exemplar_rows,
        result.elapsed_seconds,
    )
    return result


def _split_partition_frame(
    frame: pd.DataFrame, exemplars_per_group: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split the one query result into the aggregate rows and the exemplar rows.

    The query samples per aggregate group, which is finer than the (rfc_id,
    decision) grouping the exemplar budget is defined over -- a group is also
    split by source and month. The extra samples are narrowed here, by the same
    hash order, so a partition's checkpoint really does hold at most
    ``exemplars_per_group`` rows per (rfc_id, decision).
    """
    aggregates = frame[list(AGGREGATE_COLUMNS)].copy()
    aggregates["source"] = aggregates["source"].astype(object).where(
        aggregates["source"].notna(), ""
    )
    for column in ("count", "approx_domains", "approx_zones"):
        aggregates[column] = pd.to_numeric(aggregates[column], errors="coerce").fillna(0).astype("int64")

    records: list[dict[str, Any]] = []
    for row in frame.itertuples(index=False):
        sampled = getattr(row, "exemplars", None)
        if sampled is None or not hasattr(sampled, "__len__") or len(sampled) == 0:
            continue
        for item in sampled:
            if not isinstance(item, Mapping):
                continue
            record = {str(k): v for k, v in item.items()}
            record["rfc_id"] = row.rfc_id
            record["decision"] = row.decision
            record["sample_hash"] = str(record.get("sample_hash") or "")
            records.append(record)

    columns = [*_EXEMPLAR_COLUMNS, "rfc_id", "decision", "sample_hash"]
    exemplars = pd.DataFrame(records)
    for name in columns:
        if name not in exemplars.columns:
            exemplars[name] = pd.Series([None] * len(exemplars), dtype="object")
    exemplars = exemplars[columns]
    if "timestamp" in exemplars.columns and len(exemplars):
        exemplars["timestamp"] = pd.to_datetime(exemplars["timestamp"], errors="coerce")
    return aggregates, _reduce_exemplars([exemplars], exemplars_per_group)


# --------------------------------------------------------------------------- #
# Merging
# --------------------------------------------------------------------------- #


def merge_checkpoints(checkpoint_dir: Path, *, recursive: bool = False) -> AggregateTable:
    """Merge every readable partition checkpoint into one aggregate table.

    Counts and first/last-seen merge exactly. Distinct-domain and distinct-zone
    estimates do not: ``approx_count_distinct`` returns a number, not a sketch, so
    the same domain measured on two days is counted twice by a sum. Both bounds
    are kept -- the largest single-partition estimate (a lower bound) and the sum
    (an upper bound) -- and the reports say which is which rather than presenting
    either as the answer.

    Unreadable checkpoints are skipped with a warning and recorded in
    :attr:`AggregateTable.warnings`; they are never treated as empty partitions,
    because "this day had no matches" and "this day was not counted" are different
    claims.
    """
    directory = Path(checkpoint_dir)
    if not directory.is_dir():
        raise PipelineError(f"Checkpoint directory not found: {directory}")

    warnings: list[str] = []
    frames: list[pd.DataFrame] = []
    exemplar_frames: list[pd.DataFrame] = []
    partition_ids: list[str] = []
    exemplars_per_group = 0

    # A sharded run is usually gathered as one subdirectory per machine or per
    # year, so `recursive` walks those instead of forcing the operator to flatten
    # thousands of files by hand. The same partition appearing in two shards is
    # deduplicated on its id: a partition's checkpoint is deterministic, so the
    # copies are interchangeable, but counting one twice would silently double
    # that day's observations.
    if recursive:
        # Exemplar files share the partition's name and the .parquet suffix but
        # live under `exemplars/`, and are loaded from beside their aggregate.
        # Treating them as checkpoints would double the file count and emit a
        # "no status file" warning for every partition.
        found = sorted(
            path
            for path in directory.rglob(f"*{CHECKPOINT_SUFFIX}")
            if EXEMPLAR_DIRNAME not in path.parts
        )
        seen: dict[str, Path] = {}
        duplicates: list[str] = []
        for path in found:
            key = path.name[: -len(CHECKPOINT_SUFFIX)]
            if key in seen:
                duplicates.append(key)
                continue
            seen[key] = path
        if duplicates:
            warn(
                warnings,
                f"{len(duplicates)} partition(s) appeared in more than one shard and were "
                f"counted once each (e.g. {', '.join(sorted(duplicates)[:3])}). A "
                "partition checkpoint is deterministic, so the duplicates are "
                "interchangeable; counting one twice would inflate that day's counts.",
            )
        candidate_paths = [seen[k] for k in sorted(seen)]
    else:
        candidate_paths = sorted(directory.glob(f"*{CHECKPOINT_SUFFIX}"))

    for checkpoint_path in candidate_paths:
        partition_id = checkpoint_path.name[: -len(CHECKPOINT_SUFFIX)]
        status_path = checkpoint_path.parent / f"{partition_id}{STATUS_SUFFIX}"
        status = _read_status(status_path)
        if status is None or not status.get("complete"):
            warn(
                warnings,
                f"Skipping checkpoint {checkpoint_path.name}: it has no complete status "
                "file, so the partition it represents is not counted in these totals.",
                LOGGER,
            )
            continue
        try:
            frame = pd.read_parquet(checkpoint_path)
        except Exception as exc:
            warn(
                warnings,
                f"Skipping checkpoint {checkpoint_path.name}: it could not be read ({exc}). "
                "Delete it and re-run that partition; these totals are incomplete until then.",
                LOGGER,
            )
            continue
        missing = [c for c in AGGREGATE_COLUMNS if c not in frame.columns]
        if missing:
            warn(
                warnings,
                f"Skipping checkpoint {checkpoint_path.name}: missing column(s) "
                f"{', '.join(missing)}.",
                LOGGER,
            )
            continue
        frames.append(frame[list(AGGREGATE_COLUMNS)])
        partition_ids.append(partition_id)
        exemplars_per_group = max(
            exemplars_per_group, int(status.get("exemplars_per_group", 0) or 0)
        )

        # Resolve exemplars beside their own aggregate, not beside the root. In a
        # recursive merge each shard carries its own exemplars/ directory, and
        # looking under the root silently finds none -- which costs every trace,
        # every score and the whole ranking while the aggregate counts still look
        # healthy.
        exemplar_path = (
            checkpoint_path.parent / EXEMPLAR_DIRNAME / f"{partition_id}{CHECKPOINT_SUFFIX}"
        )
        if exemplar_path.is_file():
            try:
                exemplar_frames.append(pd.read_parquet(exemplar_path))
            except Exception as exc:
                warn(
                    warnings,
                    f"Exemplars for partition {partition_id} could not be read ({exc}); "
                    "its aggregates are counted but no sampled observation explains them.",
                    LOGGER,
                )

    if not frames:
        warn(
            warnings,
            f"No usable checkpoint was found in {directory}; the merged aggregate table "
            "is empty. This is not a statement about the corpus.",
            LOGGER,
        )
        return AggregateTable(
            rows=[],
            exemplars=pd.DataFrame(),
            partition_ids=[],
            exemplars_per_group=exemplars_per_group,
            warnings=warnings,
        )

    merged = pd.concat(frames, ignore_index=True)
    merged["source"] = merged["source"].fillna("").astype(str)
    merged["year_month"] = merged["year_month"].fillna("").astype(str)
    grouped = merged.groupby(
        ["rfc_id", "indicator_id", "decision", "source", "year_month"], dropna=False
    ).agg(
        count=("count", "sum"),
        first_seen=("first_seen", "min"),
        last_seen=("last_seen", "max"),
        approx_domains=("approx_domains", "max"),
        approx_domains_upper=("approx_domains", "sum"),
        approx_zones=("approx_zones", "max"),
        approx_zones_upper=("approx_zones", "sum"),
    )
    grouped = grouped.reset_index().sort_values(
        by=["rfc_id", "indicator_id", "decision", "source", "year_month"],
        kind="mergesort",
    )

    rows = [
        AggregateRow(
            rfc_id=str(record["rfc_id"]),
            indicator_id=str(record["indicator_id"]),
            decision=str(record["decision"]),
            source=str(record["source"]),
            year_month=str(record["year_month"]),
            count=int(record["count"]),
            first_seen=_as_datetime(record["first_seen"]),
            last_seen=_as_datetime(record["last_seen"]),
            approx_domains=int(record["approx_domains"]),
            approx_domains_upper=int(record["approx_domains_upper"]),
            approx_zones=int(record["approx_zones"]),
            approx_zones_upper=int(record["approx_zones_upper"]),
        )
        for record in grouped.to_dict("records")
    ]

    exemplars = _reduce_exemplars(exemplar_frames, exemplars_per_group or 5)
    return AggregateTable(
        rows=rows,
        exemplars=exemplars,
        partition_ids=partition_ids,
        exemplars_per_group=exemplars_per_group,
        warnings=warnings,
    )


def _as_datetime(value: Any) -> datetime | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, datetime):
        return value
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()
    return None


def _reduce_exemplars(frames: Sequence[pd.DataFrame], per_group: int) -> pd.DataFrame:
    """Keep the ``per_group`` lowest-hash exemplars per (rfc_id, decision).

    Each partition already kept its own lowest ``per_group``, and the hash order
    is total, so taking the lowest again across partitions gives exactly the
    sample a single-partition run would have produced.
    """
    usable = [f for f in frames if f is not None and len(f)]
    if not usable:
        return pd.DataFrame(
            {
                name: pd.Series(dtype="object")
                for name in (*_EXEMPLAR_COLUMNS, "rfc_id", "decision", "sample_hash")
            }
        )
    combined = pd.concat(usable, ignore_index=True)
    for column in ("rfc_id", "decision", "sample_hash"):
        if column not in combined.columns:
            combined[column] = ""
    combined = combined.sort_values(
        by=["rfc_id", "decision", "sample_hash"], kind="mergesort"
    )
    reduced = combined.groupby(["rfc_id", "decision"], dropna=False, sort=True).head(
        max(int(per_group), 1)
    )
    return reduced.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Aggregates -> pipeline output
# --------------------------------------------------------------------------- #


def _exemplar_note(aggregates: AggregateTable, sampled: int, total: int) -> str:
    """The sentence that stops a reader taking the sample for the corpus.

    It also states the one thing about the score that is not exact: the score is
    the best of the sampled observations, and two observations with the same
    decision can still carry different evidence, so it is a lower bound on the
    best score the corpus contains.
    """
    return (
        f"Corpus total: {total} observation(s), counted exactly. The score, the reasoning "
        f"trace, the example signal ids and the domain and zone lists above come from "
        f"{sampled} sampled exemplar observation(s) (up to "
        f"{aggregates.exemplars_per_group or 'n'} per (RFC, decision) per partition), not "
        "from the whole corpus. Read them as evidence that the aggregate is what it claims "
        "to be, not as the aggregate itself; and read the score as the best of the sampled "
        "observations, which is a lower bound on the best score in the corpus."
    )


def aggregates_to_candidates(
    aggregates: AggregateTable,
    db: RFCChecklistDB,
    *,
    schema_report: SchemaCheckReport | None = None,
    min_score: float = 0.0,
    warnings: list[str] | None = None,
) -> list[RankedRFCCandidate]:
    """Rank RFCs from the corpus aggregates, scored from the sampled exemplars.

    The scoring formula is not reimplemented: :func:`openintel_rfc.ranking.rank_candidates`
    is called on real :class:`~openintel_rfc.models.RFCMatch` objects produced by
    the real matcher over the exemplars. What the aggregates then supply is
    everything that is a *count* -- supporting observations, per-decision counts,
    first and last seen -- because those are exact over the corpus and the
    exemplars would understate them by orders of magnitude.
    """
    collected = warnings if warnings is not None else []
    _signals, matches, _traces = aggregates.evidence(
        db, schema_report=schema_report, warnings=collected
    )
    candidates = rank_candidates(matches, db, min_score=min_score)
    counts = aggregates.decision_counts()

    matched_indicators: dict[str, set[str]] = {}
    for row in aggregates.rfc_rows():
        if row.indicator_id == ROLLUP_INDICATOR_ID or row.decision not in ADOPTION_DECISIONS:
            continue
        matched_indicators.setdefault(row.rfc_id, set()).add(row.indicator_id)

    for candidate in candidates:
        rfc_id = candidate.rfc_id
        sampled = candidate.supporting_signal_count
        supporting = sum(
            counts.get((rfc_id, decision), 0) for decision in ADOPTION_DECISIONS
        )
        candidate.supporting_signal_count = supporting
        candidate.valid_match_count = counts.get((rfc_id, "valid_match"), 0)
        candidate.partial_match_count = counts.get((rfc_id, "partial_match"), 0)
        candidate.timestamp_invalid_count = counts.get((rfc_id, "timestamp_invalid"), 0)
        candidate.first_seen = aggregates.first_seen(rfc_id) or candidate.first_seen
        candidate.last_seen = aggregates.last_seen(rfc_id) or candidate.last_seen
        if matched_indicators.get(rfc_id):
            candidate.matched_indicator_ids = unique_sorted(matched_indicators[rfc_id])
        candidate.reasoning_summary = (
            candidate.reasoning_summary + " " + _exemplar_note(aggregates, sampled, supporting)
        ).strip()

    # Re-rank: the ordering key includes the observation count, which has just
    # been replaced by the corpus figure.
    candidates.sort(key=lambda c: (-c.score, -c.supporting_signal_count, c.rfc_id))
    for index, candidate in enumerate(candidates, start=1):
        candidate.rank = index

    ranked_ids = {c.rfc_id for c in candidates}
    for (rfc_id, decision), count in sorted(counts.items()):
        if decision in RANKABLE_DECISIONS and count and rfc_id not in ranked_ids:
            warn(
                collected,
                f"{rfc_id} has {count} {decision} observation(s) in the corpus aggregates but "
                "does not appear among the ranked candidates: no sampled exemplar earned a "
                "score above the threshold. The aggregate counts are still exact; only the "
                "ranking is exemplar-derived.",
                LOGGER,
            )
    return candidates


def _month_floor(rows: Sequence[AggregateRow], attribute: str) -> int:
    """Distinct-value lower bound for one calendar month.

    ``approx_count_distinct`` is computed per partition and its sketches are not
    merged, so a merged row's estimate is the busiest single partition's. Those
    per-source figures may be added: OpenINTEL sources are different zone files
    and their name sets are disjoint. The result reads as "at least this many
    distinct names were measured on the busiest day of this month, across all
    sources" -- a bound the data actually supports, unlike a sum over days, which
    counts a domain once per day it was measured.
    """
    by_source: dict[str, int] = {}
    for row in rows:
        value = int(getattr(row, attribute))
        by_source[row.source] = max(by_source.get(row.source, 0), value)
    return sum(by_source.values())


def _period_floor(rows: Sequence[AggregateRow], attribute: str) -> int:
    """The largest monthly lower bound, i.e. peak measured breadth."""
    months: dict[str, list[AggregateRow]] = {}
    for row in rows:
        months.setdefault(row.year_month, []).append(row)
    return max((_month_floor(items, attribute) for items in months.values()), default=0)


def _bucket_rows(
    rows: Sequence[AggregateRow],
    key_fn,
    scores: Mapping[tuple[str, str], float],
    rfc_id: str,
) -> list[TimelineBucket]:
    """Group aggregate rows into timeline buckets.

    ``mean_score`` is the count-weighted mean of the exemplar-derived score for
    each decision in the bucket. It is an estimate: the score is a property of the
    evidence pattern, and every observation with the same pattern scores the same,
    but the aggregate does not record which pattern each observation had beyond
    its decision.
    """
    grouped: dict[str, list[AggregateRow]] = {}
    for row in rows:
        if not row.year_month:
            continue
        grouped.setdefault(key_fn(row.year_month), []).append(row)

    buckets: list[TimelineBucket] = []
    for period in sorted(grouped):
        members = grouped[period]
        total = sum(r.count for r in members)
        weighted = sum(scores.get((rfc_id, r.decision), 0.0) * r.count for r in members)
        buckets.append(
            TimelineBucket(
                period=period,
                count=total,
                domains=_period_floor(members, "approx_domains"),
                mean_score=round_score(weighted / total) if total else 0.0,
            )
        )
    return buckets


def _exemplar_scores(matches: Sequence[RFCMatch]) -> dict[tuple[str, str], float]:
    """Best exemplar score per (rfc_id, decision), used to weight the timeline."""
    scores: dict[tuple[str, str], float] = {}
    for match in matches:
        key = (match.rfc_id, match.decision)
        scores[key] = max(scores.get(key, 0.0), match.score)
    return scores


def aggregates_to_timeline(
    aggregates: AggregateTable,
    db: RFCChecklistDB,
    *,
    include_decisions: Sequence[str] = ADOPTION_DECISIONS,
    schema_report: SchemaCheckReport | None = None,
    warnings: list[str] | None = None,
) -> list[AdoptionTimelineEntry]:
    """Build one adoption timeline entry per RFC from the corpus aggregates.

    Counts, first-seen and last-seen are exact. Distinct-domain counts are the
    lower bound described in :func:`merge_checkpoints`, and the domain and zone
    *lists* come from the exemplars only -- listing every domain of a
    10^10-row corpus is not something an output file can do, and pretending the
    exemplar list is complete would be the same lie in a different place.

    Periods with no qualifying observation are omitted rather than zero-filled,
    matching :func:`openintel_rfc.timeline.build_timeline`: a gap means "nothing
    qualifying was measured", which is not "nothing was deployed".
    """
    collected = warnings if warnings is not None else []
    _signals, matches, _traces = aggregates.evidence(
        db, schema_report=schema_report, warnings=collected
    )
    scores = _exemplar_scores(matches)
    allowed = set(include_decisions)

    by_rfc: dict[str, list[AggregateRow]] = {}
    excluded: dict[str, dict[str, int]] = {}
    for row in aggregates.rollup_rows():
        if row.decision in allowed:
            by_rfc.setdefault(row.rfc_id, []).append(row)
        elif row.decision != "no_match":
            excluded.setdefault(row.rfc_id, {})
            excluded[row.rfc_id][row.decision] = (
                excluded[row.rfc_id].get(row.decision, 0) + row.count
            )

    exemplar_domains: dict[str, list[str]] = {}
    exemplar_zones: dict[str, list[str]] = {}
    for match in matches:
        if match.decision not in allowed:
            continue
        exemplar_domains.setdefault(match.rfc_id, []).append(match.domain or "")
        exemplar_zones.setdefault(match.rfc_id, []).append(match.zone or "")

    metadata: dict[str, tuple[str, datetime]] = {
        entry.rfc_id: (entry.title, entry.publication_date) for entry in db.rfcs
    }
    for rfc_id in sorted(set(by_rfc) | set(excluded)):
        if rfc_id not in metadata:
            LOGGER.warning(
                "RFC %s appears in the aggregates but not in the checklist database; it is "
                "reported with placeholder metadata.",
                rfc_id,
            )
            metadata[rfc_id] = (rfc_id, datetime(1970, 1, 1))

    entries: list[AdoptionTimelineEntry] = []
    for rfc_id in sorted(metadata):
        title, publication_date = metadata[rfc_id]
        rows = by_rfc.get(rfc_id, [])
        excluded_counts = excluded.get(rfc_id, {})
        domains = unique_sorted(d for d in exemplar_domains.get(rfc_id, []) if d)
        zones = unique_sorted(z for z in exemplar_zones.get(rfc_id, []) if z)

        if not rows:
            entries.append(
                AdoptionTimelineEntry(
                    rfc_id=rfc_id,
                    rfc_title=title,
                    rfc_publication_date=publication_date,
                    notes=_unseen_notes(rfc_id, include_decisions, publication_date, excluded_counts),
                )
            )
            continue

        stamps = [r.first_seen for r in rows if r.first_seen is not None]
        last_stamps = [r.last_seen for r in rows if r.last_seen is not None]
        first_seen = min(stamps) if stamps else None
        last_seen = max(last_stamps) if last_stamps else None
        observations = sum(r.count for r in rows)
        days = (first_seen - publication_date).days if first_seen else None
        months = _bucket_rows(rows, lambda period: period, scores, rfc_id)

        entries.append(
            AdoptionTimelineEntry(
                rfc_id=rfc_id,
                rfc_title=title,
                rfc_publication_date=publication_date,
                first_seen=first_seen,
                last_seen=last_seen,
                days_from_publication_to_first_seen=days,
                observation_count=observations,
                distinct_domains=_period_floor(rows, "approx_domains"),
                distinct_zones=_period_floor(rows, "approx_zones"),
                domains=domains,
                zones=zones,
                monthly_counts=months,
                yearly_counts=_bucket_rows(
                    rows, lambda period: period.split("-", 1)[0], scores, rfc_id
                ),
                confidence_over_time=[b.model_copy(deep=True) for b in months],
                notes=_seen_notes(
                    rfc_id=rfc_id,
                    decisions=include_decisions,
                    observations=observations,
                    first_seen=first_seen,
                    last_seen=last_seen,
                    publication_date=publication_date,
                    days=days,
                    rows=rows,
                    exemplar_domains=len(domains),
                    excluded=excluded_counts,
                ),
            )
        )

    entries.sort(
        key=lambda e: (
            0 if e.first_seen is not None else 1,
            e.first_seen or datetime.max,
            e.rfc_id,
        )
    )
    return entries


def _excluded_summary(excluded: Mapping[str, int]) -> str:
    if not excluded:
        return ""
    parts = [f"{count} {decision}" for decision, count in sorted(excluded.items())]
    return f"Also observed but not counted: {', '.join(parts)}. "


def _seen_notes(
    *,
    rfc_id: str,
    decisions: Sequence[str],
    observations: int,
    first_seen: datetime | None,
    last_seen: datetime | None,
    publication_date: datetime,
    days: int | None,
    rows: Sequence[AggregateRow],
    exemplar_domains: int,
    excluded: Mapping[str, int],
) -> str:
    lower = _period_floor(rows, "approx_domains")
    upper = sum(r.approx_domains_upper for r in rows)
    negative = ""
    if days is not None and days < 0:
        negative = (
            f"BUG: days_from_publication_to_first_seen is {days}, i.e. the first counted "
            "observation predates the RFC. The publication-date cutoff let through a row it "
            "should have rejected; do not use this entry until that is fixed. "
        )
    return (
        f"{observations} observation(s) counted for {rfc_id} (decisions counted: "
        f"{', '.join(decisions)}), spanning {iso(first_seen)} to {iso(last_seen)}. "
        f"{negative}"
        f"{_excluded_summary(excluded)}"
        "Observation counts, first_seen and last_seen are exact over every row scanned. "
        f"distinct_domains ({lower}) is a lower bound: the most distinct domains measured in "
        "any single month, summed across the disjoint OpenINTEL sources. Summing every "
        f"partition's own estimate instead would give {upper}, which counts a domain once per "
        "measurement day it appeared on; the true figure lies between the two, and this "
        "pipeline does not merge the underlying HyperLogLog sketches, so it cannot narrow "
        f"that. The {exemplar_domains} listed domains and the listed zones come from sampled "
        "exemplars and are not the full set. Months with no qualifying observation are "
        "omitted rather than zero-filled, and a gap in OpenINTEL coverage is "
        "indistinguishable here from non-adoption."
    )


def _unseen_notes(
    rfc_id: str,
    decisions: Sequence[str],
    publication_date: datetime,
    excluded: Mapping[str, int],
) -> str:
    return (
        f"No observation qualified for {rfc_id} (decisions counted: {', '.join(decisions)}), "
        f"so first_seen is null and every count is zero. {_excluded_summary(excluded)}"
        f"The RFC was published {iso(publication_date)}. A null first_seen is not evidence of "
        "non-adoption: the RFC's indicators may be non-queryable against this corpus, the "
        "relevant names may lie outside the measured sources, or the record-type prefilter may "
        "exclude the records that would carry the evidence. Check the review queue and the run "
        "warnings before reporting this RFC as unadopted."
    )


# --------------------------------------------------------------------------- #
# Whole-run orchestration
# --------------------------------------------------------------------------- #


def _open_connection(access: Any) -> Any:
    """Open a DuckDB connection, through ``openintel_source`` when configured."""
    if access is not None:
        try:
            from .openintel_source import open_duckdb  # local import: optional module
        except ImportError:
            open_duckdb = None  # type: ignore[assignment]
        if open_duckdb is not None:
            return open_duckdb(access)
    import duckdb

    return duckdb.connect(database=":memory:")


def _resolve_uris(partition: Any, access: Any, warnings: list[str]) -> list[str]:
    """Object URIs (or local paths) for one partition.

    In ``download`` mode the objects have to exist locally before the scan can
    read them, so :func:`openintel_source.materialize` runs first; it is
    resumable, so a partition already in the cache costs nothing.
    """
    paths = getattr(partition, "paths", None)
    if paths:
        return [str(p) for p in paths]
    from .openintel_source import materialize, partition_uris  # local import

    if str(getattr(access, "mode", "") or "").lower() == "download":
        return [Path(p).as_posix() for p in materialize(partition, access, warnings=warnings)]
    return [str(uri) for uri in partition_uris(partition, access)]


def _resolve_columns(partition: Any, access: Any, uris: Sequence[str]) -> list[str]:
    """Physical column names available in one partition."""
    columns = list(getattr(partition, "columns", ()) or [])
    if columns:
        return [str(c) for c in columns]
    try:
        from .openintel_source import probe_schema  # local import
    except ImportError:
        probe_schema = None  # type: ignore[assignment]
    if probe_schema is not None:
        probed = probe_schema(partition, access)
        if isinstance(probed, Mapping):
            # `column_names` already includes the Hive path columns
            # (source/year/month/day), which the files themselves do not carry.
            names = probed.get("column_names") or probed.get("columns")
            if names:
                return [
                    str(item["name"]) if isinstance(item, Mapping) else str(item)
                    for item in names
                ]
    # Local fallback: read the footer of the first object.
    for uri in uris:
        path = Path(uri)
        if path.is_file():
            return [str(c["name"]) for c in describe_parquet(path)["columns"]]
    raise PipelineError(
        "Could not determine the Parquet schema for partition "
        f"{getattr(partition, 'partition_id', '?')}; without it the OpenINTEL column "
        "aliases cannot be resolved."
    )


def _partition_keys(partition: Any) -> dict[str, str]:
    keys = getattr(partition, "keys", None)
    return {str(k): str(v) for k, v in keys.items()} if isinstance(keys, Mapping) else {}


def run_scale_analysis(
    config: ScaleRunConfig,
    db: RFCChecklistDB,
    dictionary: OpenINTELDictionary,
    schema_report: SchemaCheckReport,
    *,
    warnings: list[str] | None = None,
    partitions: Sequence[Any] | None = None,
    connection: Any = None,
) -> PipelineResult:
    """Run the whole scale pipeline and return an MVP-shaped :class:`PipelineResult`.

    ``partitions`` may be supplied directly, which is how a local corpus (and the
    test suite) runs without discovery; otherwise
    ``openintel_source.discover_partitions`` is asked for them.

    The returned result is deliberately shape-compatible with the MVP's so that
    ``exporters``, ``report`` and the dashboard work unchanged. Where a field
    cannot be populated at scale -- ``signals``, ``matches``, ``traces`` -- it
    holds the exemplars, and the true totals live in the candidate counts, the
    timeline, and the warnings. No field silently presents an exemplar count as a
    corpus count.
    """
    collected = warnings if warnings is not None else []
    started = time.monotonic()

    discovered = list(partitions) if partitions is not None else _discover(config, collected)
    if not discovered:
        warn(
            collected,
            "No partitions were selected for this run; there is nothing to scan.",
            LOGGER,
        )
    if config.max_partitions is not None:
        discovered = discovered[: config.max_partitions]

    owns_connection = connection is None
    active = connection if connection is not None else _open_connection(config.access)

    try:
        needed_fields = sorted(
            set(queryable_field_names(schema_report))
            | set(ALWAYS_SELECT_FIELDS)
            | set(SIGNAL_FIELDS)
        )
        checkpoint_dir = ensure_dir(config.checkpoint_dir)

        governor = ThrottleGovernor(
            floor_seconds=config.pace_seconds,
            ceiling_seconds=config.max_pace_seconds,
            shards=config.shards,
        )
        LOGGER.info(
            "Pacing: %.2fs between partitions (floor %.2fs x %d shard(s)), "
            "widening to at most %.0fs while the store pushes back.",
            governor.delay,
            config.pace_seconds,
            governor.shards,
            governor.ceiling_seconds,
        )

        column_expr: dict[str, str] = {}
        compiled: CompiledChecklist | None = None
        results: list[PartitionResult] = []
        scanned = 0
        matched = 0

        for index, partition in enumerate(discovered, start=1):
            uris = _resolve_uris(partition, config.access, collected)
            if not uris:
                warn(
                    collected,
                    f"Partition {getattr(partition, 'partition_id', '?')} resolved to no "
                    "objects and was skipped.",
                    LOGGER,
                )
                continue
            columns = _resolve_columns(partition, config.access, uris)
            columns = sorted(set(columns) | set(_partition_keys(partition)))
            expressions = build_column_expressions(dictionary, needed_fields, columns)
            if expressions != column_expr:
                # Recompile only when the physical schema actually changed;
                # OpenINTEL generations differ, and a run must not assume they do
                # not.
                column_expr = expressions
                compiled = compile_checklist(db, column_expr, schema_report)
                for message in compiled.warnings:
                    warn(collected, message, LOGGER)
                LOGGER.info(
                    "Record-type prefilter: %s", ", ".join(compiled.prefilter) or "(none)"
                )
            assert compiled is not None  # set on the first iteration

            result = _process_with_retry(
                partition,
                governor=governor,
                uris=uris,
                connection=active,
                compiled=compiled,
                column_expr=column_expr,
                checkpoint_dir=checkpoint_dir,
                exemplars_per_group=config.exemplars_per_group,
                limit=config.limit_per_partition,
                resume=config.resume,
                warnings=collected,
                attempts=config.partition_retries,
                base_wait=config.partition_retry_wait_seconds,
            )
            results.append(result)
            scanned += result.rows_scanned
            matched += result.rows_matched
            _log_progress(index, len(discovered), scanned, matched, started)

            # Adaptive gap. OpenINTEL is a shared academic object store behind a
            # ~1 req/s limiter, so this is what keeps the run inside the budget
            # instead of discovering the edge of it a thousand times.
            if index < len(discovered):
                governor.wait()

        # A throttled run is not a wrong run, but it is a slower and more fragile
        # one, and the next operator should not have to guess that it happened.
        if governor.throttle_events:
            warn(
                collected,
                f"The object store throttled this run {governor.throttle_events} "
                f"time(s); the gap between partitions widened to "
                f"{governor.delay:.1f}s in response. Partitions that exhausted "
                "their retry budget are absent from the checkpoints rather than "
                "empty, so a throttled run can under-cover a date range without "
                "any count looking wrong. Re-run with --resume to fill the gaps, "
                "and raise --pace-seconds or --shards if it recurs.",
                LOGGER,
            )

        if compiled is not None:
            selectivity = matched / scanned if scanned else None
            LOGGER.info(
                "Prefilter %s kept %d row(s); %d reached a rankable decision (%s).",
                ", ".join(compiled.prefilter) or "(none)",
                scanned,
                matched,
                "n/a" if selectivity is None else f"{selectivity:.4%}",
            )
            warn(
                collected,
                "Rows whose rr_type is not one of "
                + (", ".join(compiled.prefilter) or "(none)")
                + " were excluded before any indicator was evaluated. That is what makes the "
                "run tractable, and it assumes every DNSSEC observation carries one of those "
                "record types; an observation with a null or unexpected rr_type is not counted.",
                LOGGER,
            )

        aggregates = merge_checkpoints(checkpoint_dir)
        for message in aggregates.warnings:
            warn(collected, message, LOGGER)

        candidates = aggregates_to_candidates(
            aggregates,
            db,
            schema_report=schema_report,
            min_score=config.min_score,
            warnings=collected,
        )
        timeline = aggregates_to_timeline(
            aggregates, db, schema_report=schema_report, warnings=collected
        )
        signals, matches_out, traces = aggregates.evidence(
            db, schema_report=schema_report, warnings=collected
        )

        warn(
            collected,
            f"This is an aggregate run over {len(results)} partition(s) and "
            f"{aggregates.rows_scanned} scanned row(s). observed_signals.json, "
            f"rfc_matches.json and reasoning_traces.json hold {len(signals)} sampled "
            "exemplar observation(s), not the corpus: they exist to show that the aggregate "
            "counts in ranked_candidates.json and adoption_timeline.json mean what they say. "
            "Do not read their length as a measurement.",
            LOGGER,
        )

        review_items = _build_review_items(
            schema_report=schema_report,
            matches=matches_out,
            traces=traces,
            ranked=candidates,
            db=db,
            warnings=collected,
        )

        return PipelineResult(
            generated_at=now(),
            run_config=_run_config(config, discovered),
            schema_report=schema_report,
            signals=signals,
            matches=matches_out,
            ranked_candidates=candidates,
            traces=traces,
            review_items=review_items,
            timeline=timeline,
            warnings=collected,
            # `signals` holds exemplars, not the corpus. Without these numbers the
            # report would state the exemplar count as the observation count --
            # "this run evaluated 15 observations" for a 2.6-million-row scan.
            corpus_stats={
                "sampled": True,
                "rows_scanned": int(aggregates.rows_scanned),
                "rows_matched": int(aggregates.rows_matched),
                "partitions": len(discovered),
                "exemplar_signals": len(signals),
                "sources": list(config.sources),
            },
        )
    finally:
        if owns_connection:
            try:
                active.close()
            except Exception:  # pragma: no cover - closing must never mask a failure
                pass


def _discover(config: ScaleRunConfig, warnings: list[str]) -> list[Any]:
    from .openintel_source import discover_partitions  # local import

    if config.start is None or config.end is None:
        raise PipelineError(
            "run_scale_analysis needs both 'start' and 'end' to discover partitions; "
            "pass partitions explicitly to run over a corpus that is already on disk."
        )
    found = list(
        discover_partitions(
            config.access,
            config.sources,
            config.start,
            config.end,
            basis=config.basis,
            warnings=warnings,
        )
    )
    LOGGER.info(
        "Discovered %d partition(s) for %s between %s and %s",
        len(found),
        ", ".join(config.sources) or "(no source)",
        config.start,
        config.end,
    )
    return found


def _log_progress(
    index: int, total: int, scanned: int, matched: int, started: float
) -> None:
    elapsed = time.monotonic() - started
    remaining = total - index
    eta = (elapsed / index) * remaining if index and remaining > 0 else 0.0
    LOGGER.info(
        "Progress %d/%d partitions | %d rows scanned | %d matched | %s elapsed | ETA %s",
        index,
        total,
        scanned,
        matched,
        _duration(elapsed),
        _duration(eta) if remaining > 0 else "done",
    )


def _duration(seconds: float) -> str:
    total = int(max(0.0, seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    if minutes:
        return f"{minutes}m{secs:02d}s"
    return f"{secs}s"


def _build_review_items(
    *,
    schema_report: SchemaCheckReport,
    matches: Sequence[RFCMatch],
    traces: Sequence[ReasoningTrace],
    ranked: Sequence[RankedRFCCandidate],
    db: RFCChecklistDB,
    warnings: Sequence[str],
) -> list[ReviewItem]:
    from .review_queue import build_review_queue  # local import

    return build_review_queue(
        schema_report=schema_report,
        matches=matches,
        traces=traces,
        ranked=ranked,
        db=db,
        warnings=warnings,
    )


def _run_config(config: ScaleRunConfig, partitions: Sequence[Any]) -> RunConfig:
    """Describe the run in the MVP's :class:`RunConfig` shape.

    ``parquet`` names the partition set rather than a single file: the field is
    what the report prints as "the data this run read", and a scale run read
    thousands of objects.
    """
    span = ""
    if config.start is not None and config.end is not None:
        span = f" {config.start.isoformat()}..{config.end.isoformat()}"
    descriptor = (
        f"basis={config.basis} sources={','.join(config.sources) or '(explicit)'}"
        f"{span} partitions={len(partitions)}"
    )
    return RunConfig(
        checklists=str(config.checklists or ""),
        dictionary=str(config.dictionary or ""),
        parquet=descriptor,
        out=str(config.out),
        limit=config.limit_per_partition,
        engine="duckdb",
        min_score=float(config.min_score),
    )
