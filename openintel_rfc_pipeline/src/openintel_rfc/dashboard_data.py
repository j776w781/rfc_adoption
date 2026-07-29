"""The dashboard's only data-access layer.

Streamlit pages import from here and nowhere else. They never open a file, never
parse JSON, and never touch the matching code: they receive a
:class:`DashboardBundle` of DataFrames and dictionaries and render it.

Two properties matter more than anything else in this module:

*Never raise at the user.* A ``demo_output`` directory that is missing, empty or
half-written is a normal state - someone opened the dashboard before running the
pipeline, or a run was interrupted. Every such case produces warnings on the
bundle and empty structures, never a traceback in the browser.

*Always the same columns.* Every DataFrame is returned with its full declared
column set even when the underlying file is absent, so a page can write
``df[df["decision"] == "valid_match"]`` without first checking that the column
exists. List-valued fields are joined with ``"; "`` for display and kept intact
in a parallel ``<column>_raw`` column for pages that need the list itself.

Artefacts are read as plain JSON rather than validated back into pydantic models:
a partially written file should degrade to "some rows are missing" instead of
failing validation and showing nothing at all.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import pandas as pd

from . import config
from .models import OpenINTELDictionary, RFCChecklistDB
from .utils import PipelineError, get_logger, iso, now, read_json, write_json

__all__ = [
    "DashboardBundle",
    "load_dashboard_data",
    "load_review_status",
    "save_review_status",
    "summarize",
    "available_output_dirs",
    "filter_dataframe",
    "SIGNAL_COLUMNS",
    "MATCH_COLUMNS",
    "RANKED_COLUMNS",
    "TRACE_COLUMNS",
    "REVIEW_COLUMNS",
    "TIMELINE_COLUMNS",
    "SCHEMA_COLUMNS",
]

LOGGER = get_logger("openintel_rfc.dashboard_data")


# --------------------------------------------------------------------------- #
# Artefact layout
# --------------------------------------------------------------------------- #

#: ``config.OUTPUT_FILES`` key -> envelope key holding the list payload. Mirrors
#: ``exporters.ENVELOPE_KEYS``; duplicated deliberately so the dashboard has no
#: import dependency on the exporter.
_ENVELOPE_KEYS: Final[dict[str, str]] = {
    "queryable_indicators": "indicators",
    "non_queryable_indicators": "indicators",
    "observed_signals": "signals",
    "rfc_matches": "matches",
    "ranked_candidates": "candidates",
    "reasoning_traces": "traces",
    "review_queue": "review_items",
    "adoption_timeline": "timeline",
}

#: Artefacts whose absence is worth telling the user about.
_EXPECTED_ARTEFACTS: Final[tuple[str, ...]] = (
    "observed_signals",
    "rfc_matches",
    "ranked_candidates",
    "reasoning_traces",
    "review_queue",
    "adoption_timeline",
    "schema_check_json",
    "report_md",
    "run_manifest",
)

#: Allowed values for a review item's human-set status (mirrors models.ReviewStatus).
REVIEW_STATUSES: Final[frozenset[str]] = frozenset(
    {"unresolved", "accepted", "rejected", "needs_follow_up"}
)

_SKIP_DIRECTORIES: Final[frozenset[str]] = frozenset(
    {".git", ".hg", ".svn", "__pycache__", ".venv", "venv", "node_modules", ".idea", ".mypy_cache"}
)


# --------------------------------------------------------------------------- #
# Column declarations
#
# Each frame declares its display columns plus the list-valued fields among
# them. The public ``*_COLUMNS`` tuple is the full frame layout: display columns
# followed by one ``<field>_raw`` column per list field. Declaring the ``_raw``
# columns here (rather than letting them appear only when rows exist) is what
# keeps an empty frame column-compatible with a populated one.
# --------------------------------------------------------------------------- #


def _with_raw(base: tuple[str, ...], list_fields: tuple[str, ...]) -> tuple[str, ...]:
    """Display columns plus a ``_raw`` column for every list-valued field."""
    return base + tuple(f"{name}_raw" for name in list_fields)


SIGNAL_COLUMNS: Final[tuple[str, ...]] = (
    "signal_id",
    "timestamp",
    "domain",
    "zone",
    "rr_type",
    "algorithm",
    "digest_type",
    "key_tag",
    "flags",
    "source",
    "measurement_id",
    "row_index",
    "origin_file",
)

_MATCH_LIST_FIELDS: Final[tuple[str, ...]] = (
    "matched_indicator_ids",
    "failed_indicator_ids",
    "matched_fields",
    "missing_fields",
)

_MATCH_BASE_COLUMNS: Final[tuple[str, ...]] = (
    "signal_id",
    "rfc_id",
    "rfc_title",
    "decision",
    "score",
    "confidence",
    "timestamp_valid",
    "observation_timestamp",
    "rfc_publication_date",
    "domain",
    "zone",
    "matched_indicator_ids",
    "failed_indicator_ids",
    "matched_fields",
    "missing_fields",
    "final_score",
    "timestamp_penalty",
    "trace_id",
    "reasoning_summary",
)

MATCH_COLUMNS: Final[tuple[str, ...]] = _with_raw(_MATCH_BASE_COLUMNS, _MATCH_LIST_FIELDS)

_RANKED_LIST_FIELDS: Final[tuple[str, ...]] = (
    "matched_indicator_ids",
    "matched_fields",
    "domains",
    "zones",
    "example_signal_ids",
    "example_trace_ids",
)

_RANKED_BASE_COLUMNS: Final[tuple[str, ...]] = (
    "rank",
    "rfc_id",
    "rfc_title",
    "specificity",
    "rfc_publication_date",
    "decision",
    "score",
    "aggregate_score",
    "confidence",
    "supporting_signal_count",
    "valid_match_count",
    "partial_match_count",
    "timestamp_invalid_count",
    "first_seen",
    "last_seen",
    "matched_indicator_ids",
    "matched_fields",
    "domains",
    "zones",
    "example_signal_ids",
    "example_trace_ids",
    "reasoning_summary",
)

RANKED_COLUMNS: Final[tuple[str, ...]] = _with_raw(_RANKED_BASE_COLUMNS, _RANKED_LIST_FIELDS)

_TRACE_LIST_FIELDS: Final[tuple[str, ...]] = (
    "matched_indicator_ids",
    "failed_indicator_ids",
    "skipped_indicator_ids",
    "missing_required_indicator_ids",
    "missing_fields",
    "matched_openintel_fields",
    "uncertainty_notes",
)

_TRACE_BASE_COLUMNS: Final[tuple[str, ...]] = (
    "trace_id",
    "signal_id",
    "rfc_id",
    "rfc_title",
    "observation_timestamp",
    "rfc_publication_date",
    "timestamp_valid",
    "decision",
    "confidence",
    "final_score",
    "timestamp_penalty",
    "matched_indicator_ids",
    "failed_indicator_ids",
    "skipped_indicator_ids",
    "missing_required_indicator_ids",
    "missing_fields",
    "matched_openintel_fields",
    "matched_condition_count",
    "failed_condition_count",
    "uncertainty_notes",
    "reasoning_summary",
)

TRACE_COLUMNS: Final[tuple[str, ...]] = _with_raw(_TRACE_BASE_COLUMNS, _TRACE_LIST_FIELDS)

_REVIEW_LIST_FIELDS: Final[tuple[str, ...]] = (
    "affected_rfc_ids",
    "affected_fields",
    "affected_signal_ids",
    "trace_ids",
)

_REVIEW_BASE_COLUMNS: Final[tuple[str, ...]] = (
    "item_id",
    "item_type",
    "severity",
    "status",
    "reason",
    "affected_rfc_ids",
    "affected_fields",
    "affected_signal_ids",
    "trace_ids",
    "suggested_action",
    "verification_status",
    "verification_explanation",
)

REVIEW_COLUMNS: Final[tuple[str, ...]] = _with_raw(_REVIEW_BASE_COLUMNS, _REVIEW_LIST_FIELDS)

_TIMELINE_LIST_FIELDS: Final[tuple[str, ...]] = ("domains", "zones")

_TIMELINE_BASE_COLUMNS: Final[tuple[str, ...]] = (
    "rfc_id",
    "rfc_title",
    "rfc_publication_date",
    "first_seen",
    "last_seen",
    "days_from_publication_to_first_seen",
    "observation_count",
    "distinct_domains",
    "distinct_zones",
    "domains",
    "zones",
    "notes",
)

TIMELINE_COLUMNS: Final[tuple[str, ...]] = _with_raw(
    _TIMELINE_BASE_COLUMNS, _TIMELINE_LIST_FIELDS
)

_SCHEMA_LIST_FIELDS: Final[tuple[str, ...]] = (
    "fields_used",
    "present_fields",
    "missing_fields",
    "warnings",
)

_SCHEMA_BASE_COLUMNS: Final[tuple[str, ...]] = (
    "rfc_id",
    "rfc_title",
    "rfc_publication_date",
    "indicator_id",
    "indicator_description",
    "required",
    "weight",
    "queryability",
    "fields_used",
    "present_fields",
    "missing_fields",
    "reasoning",
    "warnings",
)

SCHEMA_COLUMNS: Final[tuple[str, ...]] = _with_raw(_SCHEMA_BASE_COLUMNS, _SCHEMA_LIST_FIELDS)

#: Columns converted to ``datetime64`` so pages can sort, plot and range-filter.
_DATE_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        "timestamp",
        "observation_timestamp",
        "rfc_publication_date",
        "first_seen",
        "last_seen",
    }
)

#: Columns coerced to numeric so pages can aggregate without casting.
_NUMERIC_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        "rank",
        "score",
        "aggregate_score",
        "final_score",
        "timestamp_penalty",
        "weight",
        "algorithm",
        "digest_type",
        "key_tag",
        "row_index",
        "supporting_signal_count",
        "valid_match_count",
        "partial_match_count",
        "timestamp_invalid_count",
        "observation_count",
        "distinct_domains",
        "distinct_zones",
        "days_from_publication_to_first_seen",
        "matched_condition_count",
        "failed_condition_count",
    }
)


# --------------------------------------------------------------------------- #
# Bundle
# --------------------------------------------------------------------------- #


def _empty_frame(columns: Sequence[str]) -> pd.DataFrame:
    """An empty frame that still carries the declared columns (plus ``_raw``)."""
    return pd.DataFrame(columns=list(columns))


@dataclass
class DashboardBundle:
    """Everything the dashboard needs from one output directory.

    ``available`` is keyed by ``config.OUTPUT_FILES`` key (``"rfc_matches"``,
    not ``"rfc_matches.json"``) and says whether that artefact exists on disk.
    ``warnings`` explains every gap: a missing file, an unreadable file, or an
    envelope whose shape was not what this version expects.
    """

    output_dir: Path
    available: dict[str, bool] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    signals_df: pd.DataFrame = field(default_factory=lambda: _empty_frame(SIGNAL_COLUMNS))
    matches_df: pd.DataFrame = field(default_factory=lambda: _empty_frame(MATCH_COLUMNS))
    ranked_df: pd.DataFrame = field(default_factory=lambda: _empty_frame(RANKED_COLUMNS))
    traces_df: pd.DataFrame = field(default_factory=lambda: _empty_frame(TRACE_COLUMNS))
    review_df: pd.DataFrame = field(default_factory=lambda: _empty_frame(REVIEW_COLUMNS))
    timeline_df: pd.DataFrame = field(default_factory=lambda: _empty_frame(TIMELINE_COLUMNS))
    schema_df: pd.DataFrame = field(default_factory=lambda: _empty_frame(SCHEMA_COLUMNS))
    traces: list[dict] = field(default_factory=list)
    review_items: list[dict] = field(default_factory=list)
    timeline_entries: list[dict] = field(default_factory=list)
    schema_report: dict | None = None
    checklist_db: RFCChecklistDB | None = None
    dictionary: OpenINTELDictionary | None = None
    report_md: str | None = None
    survey_md: str | None = None
    run_manifest: dict | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def has_analysis(self) -> bool:
        """True when at least one analyze artefact was loaded."""
        return not self.matches_df.empty or not self.signals_df.empty

    def trace_by_id(self, trace_id: str) -> dict | None:
        """Look up one full reasoning trace, including its condition lists."""
        for trace in self.traces:
            if trace.get("trace_id") == trace_id:
                return trace
        return None

    def review_item_by_id(self, item_id: str) -> dict | None:
        for item in self.review_items:
            if item.get("item_id") == item_id:
                return item
        return None


# --------------------------------------------------------------------------- #
# Low-level readers (never raise)
# --------------------------------------------------------------------------- #


def _warn(warnings: list[str], message: str) -> None:
    if message not in warnings:
        warnings.append(message)
    LOGGER.warning(message)


def _read_json_file(path: Path, warnings: list[str]) -> Any | None:
    """Read one JSON artefact; ``None`` when it is missing or unreadable."""
    if not path.is_file():
        return None
    try:
        return read_json(path)
    except PipelineError as exc:
        _warn(warnings, f"{path.name} could not be read: {exc}")
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:  # pragma: no cover
        _warn(warnings, f"{path.name} could not be read: {exc}")
    return None


def _read_text_file(path: Path, warnings: list[str]) -> str | None:
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:  # pragma: no cover - defensive
        _warn(warnings, f"{path.name} could not be read: {exc}")
        return None


def _read_envelope(
    output_dir: Path, file_key: str, warnings: list[str]
) -> list[dict[str, Any]]:
    """Read a JSON list artefact and unwrap its envelope.

    Tolerates a bare JSON list as well as the envelope, so hand-written or
    older files still load.
    """
    path = output_dir / config.OUTPUT_FILES[file_key]
    payload = _read_json_file(path, warnings)
    if payload is None:
        return []
    envelope_key = _ENVELOPE_KEYS.get(file_key, "items")
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, Mapping):
        raw = payload.get(envelope_key)
        if raw is None:
            # Fall back to the only list-valued key, if there is exactly one.
            candidates = [v for k, v in payload.items() if isinstance(v, list)]
            if len(candidates) == 1:
                raw = candidates[0]
            else:
                _warn(
                    warnings,
                    f"{path.name} has no '{envelope_key}' list; the file may have "
                    "been written by a different pipeline version.",
                )
                return []
        items = raw if isinstance(raw, list) else []
    else:
        _warn(warnings, f"{path.name} is not a JSON object or list; ignoring it.")
        return []
    return [item for item in items if isinstance(item, Mapping)]


# --------------------------------------------------------------------------- #
# Row shaping
# --------------------------------------------------------------------------- #


def _join(value: Any) -> str:
    """Render a possibly list-valued field for display."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "; ".join(str(item) for item in value)
    if isinstance(value, Mapping):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _raw(value: Any) -> list[Any]:
    """The list form of a possibly list-valued field, for pages that need it."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _with_lists(row: dict[str, Any], list_fields: Iterable[str], source: Mapping[str, Any]) -> None:
    """Populate ``field`` (joined) and ``field_raw`` (list) for each list field."""
    for name in list_fields:
        value = source.get(name)
        row[name] = _join(value)
        row[f"{name}_raw"] = _raw(value)


def _frame(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> pd.DataFrame:
    """Build a DataFrame that always has ``columns``, in that order, typed."""
    frame = pd.DataFrame(list(rows)) if rows else pd.DataFrame(columns=list(columns))
    for name in columns:
        if name not in frame.columns:
            frame[name] = pd.NA
    ordered = list(columns) + [name for name in frame.columns if name not in columns]
    frame = frame[ordered]

    for name in frame.columns:
        if name in _DATE_COLUMNS:
            frame[name] = pd.to_datetime(frame[name], errors="coerce")
        elif name in _NUMERIC_COLUMNS:
            frame[name] = pd.to_numeric(frame[name], errors="coerce")
    return frame


def _signal_rows(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        fields = item.get("fields") or {}
        if not isinstance(fields, Mapping):
            fields = {}
        row: dict[str, Any] = {
            "signal_id": item.get("signal_id"),
            "timestamp": item.get("timestamp"),
            "domain": item.get("domain"),
            "zone": item.get("zone"),
            "source": item.get("source"),
            "measurement_id": item.get("measurement_id"),
            "row_index": item.get("row_index"),
            "origin_file": item.get("origin_file"),
        }
        for name in ("rr_type", "algorithm", "digest_type", "key_tag", "flags"):
            row[name] = fields.get(name)
        # Keep any further normalized fields the extractor produced.
        for name in sorted(fields):
            row.setdefault(name, fields[name])
        rows.append(row)
    return rows


def _match_rows(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        breakdown = item.get("score_breakdown") or {}
        if not isinstance(breakdown, Mapping):
            breakdown = {}
        row: dict[str, Any] = {
            "signal_id": item.get("signal_id"),
            "rfc_id": item.get("rfc_id"),
            "rfc_title": item.get("rfc_title"),
            "decision": item.get("decision"),
            "score": item.get("score"),
            "confidence": item.get("confidence"),
            "timestamp_valid": item.get("timestamp_valid"),
            "observation_timestamp": item.get("observation_timestamp"),
            "rfc_publication_date": item.get("rfc_publication_date"),
            "domain": item.get("domain"),
            "zone": item.get("zone"),
            "final_score": breakdown.get("final_score", item.get("score")),
            "timestamp_penalty": breakdown.get("timestamp_penalty", 0.0),
            "trace_id": item.get("trace_id"),
            "reasoning_summary": item.get("reasoning_summary"),
        }
        _with_lists(row, _MATCH_LIST_FIELDS, item)
        rows.append(row)
    return rows


def _ranked_rows(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        row: dict[str, Any] = {
            name: item.get(name)
            for name in (
                "rank",
                "rfc_id",
                "rfc_title",
                "specificity",
                "rfc_publication_date",
                "decision",
                "score",
                "aggregate_score",
                "confidence",
                "supporting_signal_count",
                "valid_match_count",
                "partial_match_count",
                "timestamp_invalid_count",
                "first_seen",
                "last_seen",
                "reasoning_summary",
            )
        }
        _with_lists(row, _RANKED_LIST_FIELDS, item)
        rows.append(row)
    return rows


def _trace_rows(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        breakdown = item.get("score_breakdown") or {}
        if not isinstance(breakdown, Mapping):
            breakdown = {}
        matched = item.get("matched_conditions") or []
        failed = item.get("failed_conditions") or []
        row: dict[str, Any] = {
            name: item.get(name)
            for name in (
                "trace_id",
                "signal_id",
                "rfc_id",
                "rfc_title",
                "observation_timestamp",
                "rfc_publication_date",
                "timestamp_valid",
                "decision",
                "confidence",
                "reasoning_summary",
            )
        }
        row["final_score"] = breakdown.get("final_score")
        row["timestamp_penalty"] = breakdown.get("timestamp_penalty")
        row["matched_condition_count"] = len(matched) if isinstance(matched, list) else 0
        row["failed_condition_count"] = len(failed) if isinstance(failed, list) else 0
        _with_lists(row, _TRACE_LIST_FIELDS, item)
        rows.append(row)
    return rows


def _review_rows(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        verification = item.get("verification") or {}
        if not isinstance(verification, Mapping):
            verification = {}
        row: dict[str, Any] = {
            name: item.get(name)
            for name in (
                "item_id",
                "item_type",
                "severity",
                "status",
                "reason",
                "suggested_action",
            )
        }
        row["verification_status"] = verification.get("verification_status")
        row["verification_explanation"] = verification.get("explanation")
        _with_lists(row, _REVIEW_LIST_FIELDS, item)
        rows.append(row)
    return rows


def _timeline_rows(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        row: dict[str, Any] = {
            name: item.get(name)
            for name in (
                "rfc_id",
                "rfc_title",
                "rfc_publication_date",
                "first_seen",
                "last_seen",
                "days_from_publication_to_first_seen",
                "observation_count",
                "distinct_domains",
                "distinct_zones",
                "notes",
            )
        }
        _with_lists(row, _TIMELINE_LIST_FIELDS, item)
        rows.append(row)
    return rows


def _schema_rows(indicators: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for check in indicators:
        conditions = check.get("condition_checks") or []
        fields_used: list[str] = []
        if isinstance(conditions, list):
            for condition in conditions:
                if isinstance(condition, Mapping):
                    name = condition.get("field")
                    if name is not None and name not in fields_used:
                        fields_used.append(str(name))
        row: dict[str, Any] = {
            name: check.get(name)
            for name in (
                "rfc_id",
                "rfc_title",
                "rfc_publication_date",
                "indicator_id",
                "indicator_description",
                "required",
                "weight",
                "queryability",
                "reasoning",
            )
        }
        # ``fields_used`` is derived rather than read, so it is filled in first
        # and then shares the same joined/_raw treatment as the other lists.
        enriched = dict(check)
        enriched["fields_used"] = fields_used
        _with_lists(row, _SCHEMA_LIST_FIELDS, enriched)
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- #
# Input files (checklist / dictionary / survey)
# --------------------------------------------------------------------------- #


def _resolve_optional_path(
    supplied: str | Path | None, fallback: Path, label: str, warnings: list[str]
) -> Path | None:
    """Resolve a caller-supplied path, falling back to the packaged default."""
    if supplied is not None:
        path = Path(supplied)
        if path.is_file():
            return path
        _warn(warnings, f"{label} not found at {path}; continuing without it.")
        return None
    return fallback if fallback.is_file() else None


def _load_checklist_db(path: Path | None, warnings: list[str]) -> RFCChecklistDB | None:
    """Load the checklist DB directly from JSON (no checklist_loader import)."""
    if path is None:
        return None
    payload = _read_json_file(path, warnings)
    if payload is None:
        return None
    try:
        return RFCChecklistDB.model_validate(payload)
    except Exception as exc:  # pydantic ValidationError and friends
        _warn(warnings, f"Checklist database at {path.name} is not valid: {exc}")
        return None


def _load_dictionary(path: Path | None, warnings: list[str]) -> OpenINTELDictionary | None:
    if path is None:
        return None
    payload = _read_json_file(path, warnings)
    if payload is None:
        return None
    try:
        return OpenINTELDictionary.model_validate(payload)
    except Exception as exc:
        _warn(warnings, f"OpenINTEL dictionary at {path.name} is not valid: {exc}")
        return None


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def load_dashboard_data(
    output_dir: str | Path,
    *,
    checklists: str | Path | None = None,
    dictionary: str | Path | None = None,
    survey: str | Path | None = None,
) -> DashboardBundle:
    """Load every artefact in ``output_dir`` into a :class:`DashboardBundle`.

    Missing files are not errors: they become ``available[key] = False`` plus a
    warning, and their DataFrame comes back empty with the right columns. The
    checklist, dictionary and tool survey fall back to the packaged defaults
    when the caller passes nothing and those files exist.
    """
    directory = Path(output_dir)
    warnings: list[str] = []

    available = {
        key: (directory / name).is_file() for key, name in config.OUTPUT_FILES.items()
    }
    if not directory.is_dir():
        _warn(
            warnings,
            f"Output directory {directory} does not exist. Run "
            f"'{config.PIPELINE_NAME} analyze --out {directory}' to create it.",
        )
    else:
        missing = [
            config.OUTPUT_FILES[key] for key in _EXPECTED_ARTEFACTS if not available[key]
        ]
        if missing:
            _warn(
                warnings,
                f"{len(missing)} expected artefact(s) missing from {directory}: "
                + ", ".join(missing),
            )

    signal_items = _read_envelope(directory, "observed_signals", warnings)
    match_items = _read_envelope(directory, "rfc_matches", warnings)
    ranked_items = _read_envelope(directory, "ranked_candidates", warnings)
    trace_items = _read_envelope(directory, "reasoning_traces", warnings)
    review_items = _read_envelope(directory, "review_queue", warnings)
    timeline_items = _read_envelope(directory, "adoption_timeline", warnings)

    schema_payload = _read_json_file(
        directory / config.OUTPUT_FILES["schema_check_json"], warnings
    )
    schema_report: dict | None = None
    schema_indicators: list[Mapping[str, Any]] = []
    if isinstance(schema_payload, Mapping):
        schema_report = dict(schema_payload)
        raw_indicators = schema_payload.get("indicators")
        if isinstance(raw_indicators, list):
            schema_indicators = [i for i in raw_indicators if isinstance(i, Mapping)]
    elif schema_payload is not None:
        _warn(
            warnings,
            f"{config.OUTPUT_FILES['schema_check_json']} is not a JSON object; ignoring it.",
        )

    manifest_payload = _read_json_file(
        directory / config.OUTPUT_FILES["run_manifest"], warnings
    )
    run_manifest = dict(manifest_payload) if isinstance(manifest_payload, Mapping) else None
    if run_manifest:
        for message in run_manifest.get("warnings") or []:
            # Surface the pipeline's own warnings in the UI: they explain gaps
            # in the data the dashboard is about to display.
            _warn(warnings, f"From run: {message}")

    report_md = _read_text_file(directory / config.OUTPUT_FILES["report_md"], warnings)

    checklist_path = _resolve_optional_path(
        checklists, config.DEFAULT_CHECKLIST_PATH, "Checklist database", warnings
    )
    dictionary_path = _resolve_optional_path(
        dictionary, config.DEFAULT_DICTIONARY_PATH, "OpenINTEL dictionary", warnings
    )
    survey_path = _resolve_optional_path(
        survey, config.DEFAULT_SURVEY_PATH, "Tool survey", warnings
    )

    bundle = DashboardBundle(
        output_dir=directory,
        available=available,
        signals_df=_frame(_signal_rows(signal_items), SIGNAL_COLUMNS),
        matches_df=_frame(_match_rows(match_items), MATCH_COLUMNS),
        ranked_df=_frame(_ranked_rows(ranked_items), RANKED_COLUMNS),
        traces_df=_frame(_trace_rows(trace_items), TRACE_COLUMNS),
        review_df=_frame(_review_rows(review_items), REVIEW_COLUMNS),
        timeline_df=_frame(_timeline_rows(timeline_items), TIMELINE_COLUMNS),
        schema_df=_frame(_schema_rows(schema_indicators), SCHEMA_COLUMNS),
        traces=[dict(item) for item in trace_items],
        review_items=[dict(item) for item in review_items],
        timeline_entries=[dict(item) for item in timeline_items],
        schema_report=schema_report,
        checklist_db=_load_checklist_db(checklist_path, warnings),
        dictionary=_load_dictionary(dictionary_path, warnings),
        report_md=report_md,
        survey_md=_read_text_file(survey_path, warnings) if survey_path else None,
        run_manifest=run_manifest,
        warnings=warnings,
    )
    bundle.summary = summarize(bundle)
    return bundle


def _count_where(frame: pd.DataFrame, column: str, value: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int((frame[column].astype("string") == value).sum())


def _date_bounds(bundle: DashboardBundle) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """Observation window, preferring signals and falling back to matches."""
    for frame, column in (
        (bundle.signals_df, "timestamp"),
        (bundle.matches_df, "observation_timestamp"),
    ):
        if frame.empty or column not in frame.columns:
            continue
        series = pd.to_datetime(frame[column], errors="coerce").dropna()
        if not series.empty:
            return series.min(), series.max()
    return None, None


def summarize(bundle: DashboardBundle) -> dict[str, Any]:
    """Build the Overview page counters from an already-loaded bundle.

    ``date_range`` is a display string (``"2016-01-15 to 2019-08-20"`` or
    ``"n/a"``); ``date_start`` / ``date_end`` carry the same information as ISO
    strings, or ``None`` when there are no observations.
    """
    schema_report = bundle.schema_report or {}
    manifest = bundle.run_manifest or {}
    manifest_counts = manifest.get("counts") if isinstance(manifest.get("counts"), Mapping) else {}

    # An 'analyze'-only output directory has no schema_check.json, so the run
    # manifest is the last source that still knows the queryability split.
    queryability: dict[str, int] = {}
    if not bundle.schema_df.empty and "queryability" in bundle.schema_df.columns:
        counts = bundle.schema_df["queryability"].astype("string").value_counts()
        queryability = {str(key): int(value) for key, value in counts.items()}
    elif isinstance(schema_report.get("counts_by_queryability"), Mapping):
        queryability = {
            str(k): int(v) for k, v in schema_report["counts_by_queryability"].items()
        }
    elif isinstance(manifest.get("indicators_by_queryability"), Mapping):
        queryability = {
            str(k): int(v) for k, v in manifest["indicators_by_queryability"].items()
        }

    if bundle.checklist_db is not None:
        rfc_count = len(bundle.checklist_db.rfcs)
    elif isinstance(schema_report.get("rfc_count"), int):
        rfc_count = int(schema_report["rfc_count"])
    elif isinstance(manifest_counts.get("rfcs"), int):
        rfc_count = int(manifest_counts["rfcs"])
    elif not bundle.matches_df.empty:
        rfc_count = int(bundle.matches_df["rfc_id"].nunique())
    else:
        rfc_count = 0

    if bundle.dictionary is not None:
        dictionary_field_count = len(bundle.dictionary.fields)
    elif isinstance(schema_report.get("dictionary_field_count"), int):
        dictionary_field_count = int(schema_report["dictionary_field_count"])
    elif isinstance(manifest_counts.get("dictionary_fields"), int):
        dictionary_field_count = int(manifest_counts["dictionary_fields"])
    else:
        dictionary_field_count = 0

    indicator_count = len(bundle.schema_df)
    if not indicator_count:
        if isinstance(schema_report.get("indicator_count"), int):
            indicator_count = int(schema_report["indicator_count"])
        elif isinstance(manifest_counts.get("indicators"), int):
            indicator_count = int(manifest_counts["indicators"])

    top_rfc_id: str | None = None
    top_rfc_score: float = 0.0
    if not bundle.ranked_df.empty:
        ranked = bundle.ranked_df
        ordered = ranked.sort_values(
            by=["rank", "score"], ascending=[True, False], na_position="last"
        )
        top = ordered.iloc[0]
        raw_id = top.get("rfc_id")
        top_rfc_id = None if pd.isna(raw_id) else str(raw_id)
        raw_score = top.get("score")
        top_rfc_score = 0.0 if pd.isna(raw_score) else float(raw_score)

    start, end = _date_bounds(bundle)
    date_range = (
        f"{start.date().isoformat()} to {end.date().isoformat()}"
        if start is not None and end is not None
        else "n/a"
    )

    return {
        "output_dir": str(bundle.output_dir),
        "rfc_count": rfc_count,
        "dictionary_field_count": dictionary_field_count,
        "indicator_count": int(indicator_count),
        "queryable_indicator_count": queryability.get("queryable", 0),
        "partially_queryable_indicator_count": queryability.get("partially_queryable", 0),
        "non_queryable_indicator_count": queryability.get("non_queryable", 0),
        "ambiguous_indicator_count": queryability.get("ambiguous", 0),
        "signal_count": int(len(bundle.signals_df)),
        "match_count": int(len(bundle.matches_df)),
        "valid_match_count": _count_where(bundle.matches_df, "decision", "valid_match"),
        "partial_match_count": _count_where(bundle.matches_df, "decision", "partial_match"),
        "timestamp_invalid_count": _count_where(
            bundle.matches_df, "decision", "timestamp_invalid"
        ),
        "ranked_candidate_count": int(len(bundle.ranked_df)),
        "trace_count": int(len(bundle.traces_df)),
        "review_item_count": int(len(bundle.review_df)),
        "high_severity_count": _count_where(bundle.review_df, "severity", "high"),
        "unresolved_review_count": _count_where(bundle.review_df, "status", "unresolved"),
        "timeline_entry_count": int(len(bundle.timeline_df)),
        "top_rfc_id": top_rfc_id,
        "top_rfc_score": top_rfc_score,
        "date_range": date_range,
        "date_start": start.isoformat() if start is not None else None,
        "date_end": end.isoformat() if end is not None else None,
        "warning_count": len(bundle.warnings),
        "generated_at": (bundle.run_manifest or {}).get("generated_at"),
    }


# --------------------------------------------------------------------------- #
# Review status (dashboard-owned state)
# --------------------------------------------------------------------------- #


def load_review_status(output_dir: str | Path) -> dict[str, str]:
    """Read ``review_queue_status.json`` as ``{item_id: status}``.

    Returns an empty mapping when the file is absent or unreadable: reviewer
    annotations are convenience state, and losing them must not stop the
    dashboard from rendering the run.
    """
    path = Path(output_dir) / config.OUTPUT_FILES["review_queue_status"]
    if not path.is_file():
        return {}
    discarded: list[str] = []
    payload = _read_json_file(path, discarded)
    if payload is None:
        return {}
    statuses = payload.get("statuses") if isinstance(payload, Mapping) else None
    if statuses is None and isinstance(payload, Mapping):
        # Tolerate a bare {item_id: status} mapping.
        statuses = {k: v for k, v in payload.items() if isinstance(v, str)}
    if not isinstance(statuses, Mapping):
        return {}
    return {str(key): str(value) for key, value in statuses.items()}


def save_review_status(output_dir: str | Path, statuses: Mapping[str, str]) -> Path:
    """Persist reviewer decisions and return the file path.

    An unknown status value is a caller error and raises
    :class:`PipelineError`; the pipeline's own ``review_queue.json`` is never
    modified, so this file is the only place human annotations live.
    """
    invalid = sorted(
        f"{key}={value}" for key, value in statuses.items() if value not in REVIEW_STATUSES
    )
    if invalid:
        raise PipelineError(
            "Invalid review status value(s): "
            + ", ".join(invalid)
            + ". Allowed: "
            + ", ".join(sorted(REVIEW_STATUSES))
        )
    payload = {
        "generated_at": iso(now()),
        "pipeline": config.PIPELINE_NAME,
        "version": config.PIPELINE_VERSION,
        "count": len(statuses),
        "statuses": {key: statuses[key] for key in sorted(statuses)},
    }
    return write_json(
        Path(output_dir) / config.OUTPUT_FILES["review_queue_status"], payload
    )


# --------------------------------------------------------------------------- #
# Directory discovery and filtering
# --------------------------------------------------------------------------- #


def available_output_dirs(search_root: str | Path) -> list[Path]:
    """Find directories under ``search_root`` that hold pipeline artefacts.

    Used by the dashboard's output-directory picker. The search is depth-limited
    (root, children, grandchildren) so pointing it at a large tree stays cheap.
    """
    root = Path(search_root)
    if not root.is_dir():
        return []
    markers = set(config.OUTPUT_FILES.values())

    def holds_artefacts(directory: Path) -> bool:
        return any((directory / name).is_file() for name in markers)

    def child_dirs(directory: Path) -> list[Path]:
        try:
            entries = sorted(directory.iterdir())
        except OSError:  # pragma: no cover - unreadable directory
            return []
        return [
            entry
            for entry in entries
            if entry.is_dir()
            and not entry.name.startswith(".")
            and entry.name not in _SKIP_DIRECTORIES
        ]

    found: dict[Path, None] = {}
    if holds_artefacts(root):
        found.setdefault(root, None)
    for child in child_dirs(root):
        if holds_artefacts(child):
            found.setdefault(child, None)
        for grandchild in child_dirs(child):
            if holds_artefacts(grandchild):
                found.setdefault(grandchild, None)
    return sorted(found)


def filter_dataframe(df: pd.DataFrame, **filters: Any) -> pd.DataFrame:
    """Filter ``df`` by column values, ignoring "no filter" sentinels.

    Accepted filter values:

    ``None``, ``""``, ``"All"``
        No filtering on that column (what an untouched Streamlit widget sends).
    scalar
        Equality, compared as text so ``"13"`` matches an integer 13.
    list / tuple / set
        Membership; an empty collection means no filtering.
    ``slice(start, stop)``
        Inclusive range, for date and numeric columns.
    callable
        Applied to each value in the column; must return a boolean.

    A filter naming a column the frame does not have is logged and skipped
    rather than raising, so a page cannot break the dashboard with a stale
    column name.
    """
    if df is None or df.empty or not filters:
        return df
    mask = pd.Series(True, index=df.index)
    for column, value in filters.items():
        if value is None:
            continue
        if column not in df.columns:
            LOGGER.warning("filter_dataframe: no column %r; filter ignored", column)
            continue
        series = df[column]
        if callable(value):
            mask &= series.map(value).fillna(False).astype(bool)
        elif isinstance(value, slice):
            if value.start is not None:
                mask &= series >= value.start
            if value.stop is not None:
                mask &= series <= value.stop
        elif isinstance(value, str):
            if value in {"", "All", "all", "*"}:
                continue
            mask &= series.astype("string") == value
        elif isinstance(value, (list, tuple, set, frozenset)):
            wanted = [str(item) for item in value]
            if not wanted:
                continue
            mask &= series.astype("string").isin(wanted)
        else:
            mask &= series == value
    return df[mask.fillna(False)]
