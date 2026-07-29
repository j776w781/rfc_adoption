"""Deterministic writers for every artefact the pipeline puts on disk.

This module is the single place that knows how a pipeline result becomes files.
Nothing else in the package should call ``open()`` on an output path.

Design notes
------------
* File *names* always come from :data:`openintel_rfc.config.OUTPUT_FILES`. A
  file key that is not in that mapping is a programming error and raises
  :class:`~openintel_rfc.utils.PipelineError` rather than inventing a name.
* JSON list artefacts share one envelope shape so that every consumer (the
  dashboard, tests, downstream scripts) can unwrap them the same way::

      {"generated_at": ..., "pipeline": ..., "version": ..., "count": N,
       "<envelope_key>": [...]}

  The per-file envelope key is fixed in :data:`ENVELOPE_KEYS`.
* All JSON goes through :func:`openintel_rfc.utils.write_json`, which runs the
  payload through ``to_jsonable`` (models -> dicts, datetimes -> ISO strings,
  floats rounded) so repeated runs over the same input are byte-identical.
* CSV artefacts are written even when there are no rows: the dashboard reads
  them unconditionally, and a header-only file is a valid empty table whereas a
  missing file is an error path. When rows are present the header is the union
  of all row keys in first-seen order; when there are none, the header falls
  back to the declared column list for that artefact.
"""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, Final

from . import config
from .models import (
    AdoptionTimelineEntry,
    ObservedSignal,
    PipelineResult,
    ReasoningTrace,
    ReviewItem,
    RFCMatch,
    SchemaCheckReport,
)
from .utils import (
    PipelineError,
    ensure_dir,
    flatten_for_csv,
    get_logger,
    iso,
    now,
    write_json,
    write_text,
)

__all__ = [
    "ENVELOPE_KEYS",
    "DEFAULT_CSV_COLUMNS",
    "output_path",
    "export_json_list",
    "export_csv",
    "export_markdown",
    "export_schema_check",
    "export_analysis",
    "build_run_manifest",
    "matches_to_rows",
    "signals_to_rows",
    "traces_to_rows",
    "schema_check_to_rows",
    "review_items_to_rows",
    "timeline_to_rows",
]

LOGGER = get_logger("openintel_rfc.exporters")


# --------------------------------------------------------------------------- #
# Envelope keys
# --------------------------------------------------------------------------- #

#: ``config.OUTPUT_FILES`` key -> the JSON key holding the list payload.
#:
#: ``schema_check_json`` is deliberately absent: that file carries a whole
#: :class:`~openintel_rfc.models.SchemaCheckReport`, not a list, so it is not
#: written through :func:`export_json_list`.
ENVELOPE_KEYS: Final[dict[str, str]] = {
    "queryable_indicators": "indicators",
    "non_queryable_indicators": "indicators",
    "observed_signals": "signals",
    "rfc_matches": "matches",
    "ranked_candidates": "candidates",
    "reasoning_traces": "traces",
    "review_queue": "review_items",
    "adoption_timeline": "timeline",
}

#: Envelope metadata keys; an artefact may not use one of these as its list key.
_RESERVED_ENVELOPE_KEYS: Final[frozenset[str]] = frozenset(
    {"generated_at", "pipeline", "version", "count"}
)


# --------------------------------------------------------------------------- #
# CSV column declarations
# --------------------------------------------------------------------------- #

SIGNAL_CSV_COLUMNS: Final[tuple[str, ...]] = (
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

#: Normalized analysis fields lifted out of ``ObservedSignal.fields`` into their
#: own CSV columns (the remaining five live on the model itself).
_SIGNAL_VALUE_FIELDS: Final[tuple[str, ...]] = (
    "rr_type",
    "algorithm",
    "digest_type",
    "key_tag",
    "flags",
)

MATCH_CSV_COLUMNS: Final[tuple[str, ...]] = (
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
    "base_indicator_score",
    "specificity_multiplier",
    "required_match_bonus",
    "optional_match_bonus",
    "missing_required_penalty",
    "partial_match_penalty",
    "ambiguity_penalty",
    "timestamp_penalty",
    "final_score",
    "trace_id",
    "reasoning_summary",
)

TRACE_CSV_COLUMNS: Final[tuple[str, ...]] = (
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
    "score_steps",
)

REVIEW_CSV_COLUMNS: Final[tuple[str, ...]] = (
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
    "evidence",
)

TIMELINE_CSV_COLUMNS: Final[tuple[str, ...]] = (
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
    "monthly_counts",
    "yearly_counts",
    "notes",
)

SCHEMA_CHECK_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "rfc_id",
    "rfc_title",
    "rfc_publication_date",
    "indicator_id",
    "indicator_description",
    "required",
    "weight",
    "queryability",
    "condition_count",
    "fields_used",
    "present_fields",
    "missing_fields",
    "available_from",
    "reasoning",
    "warnings",
)

#: Fallback header for each CSV artefact, used when there are no rows to write.
DEFAULT_CSV_COLUMNS: Final[dict[str, tuple[str, ...]]] = {
    "observed_signals_csv": SIGNAL_CSV_COLUMNS,
    "rfc_matches_csv": MATCH_CSV_COLUMNS,
    "reasoning_traces_csv": TRACE_CSV_COLUMNS,
    "review_queue_csv": REVIEW_CSV_COLUMNS,
    "adoption_timeline_csv": TIMELINE_CSV_COLUMNS,
    "schema_check_csv": SCHEMA_CHECK_CSV_COLUMNS,
}


# --------------------------------------------------------------------------- #
# Primitive writers
# --------------------------------------------------------------------------- #


def output_path(out_dir: str | Path, file_key: str) -> Path:
    """Resolve ``file_key`` against :data:`config.OUTPUT_FILES` and ``out_dir``.

    Raises a :class:`PipelineError` for unknown keys so that a typo surfaces at
    the call site instead of silently creating a stray file.
    """
    try:
        name = config.OUTPUT_FILES[file_key]
    except KeyError as exc:
        known = ", ".join(sorted(config.OUTPUT_FILES))
        raise PipelineError(
            f"Unknown output file key {file_key!r}. Known keys: {known}"
        ) from exc
    return Path(out_dir) / name


def export_json_list(
    out_dir: str | Path,
    file_key: str,
    envelope_key: str,
    items: Sequence[Any],
    *,
    generated_at: datetime | None = None,
) -> Path:
    """Write ``items`` as a counted JSON envelope and return the file path.

    ``generated_at`` defaults to :func:`utils.now`, which is frozen when the
    deterministic-output environment variable is set. Callers that already have
    a run timestamp (the analyze command does) should pass it so that every
    artefact from one run carries the same value.
    """
    if envelope_key in _RESERVED_ENVELOPE_KEYS:
        raise PipelineError(
            f"Envelope key {envelope_key!r} collides with envelope metadata "
            f"({', '.join(sorted(_RESERVED_ENVELOPE_KEYS))})"
        )
    payload: dict[str, Any] = {
        "generated_at": iso(generated_at or now()),
        "pipeline": config.PIPELINE_NAME,
        "version": config.PIPELINE_VERSION,
        "count": len(items),
        envelope_key: list(items),
    }
    path = write_json(output_path(out_dir, file_key), payload)
    LOGGER.debug("Wrote %d %s to %s", len(items), envelope_key, path)
    return path


def export_csv(
    out_dir: str | Path,
    file_key: str,
    rows: Sequence[Mapping[str, Any]],
    *,
    fieldnames: Sequence[str] | None = None,
) -> Path:
    """Write ``rows`` as UTF-8 CSV and return the file path.

    The header is built from ``fieldnames`` (when given) followed by any further
    keys in first-seen row order. With no rows and no explicit ``fieldnames``
    the declared column list for the artefact is used, so the file still has a
    usable header instead of being empty.
    """
    path = output_path(out_dir, file_key)
    ensure_dir(path.parent)

    header: dict[str, None] = {}
    if fieldnames is not None:
        for name in fieldnames:
            header.setdefault(name, None)
    elif not rows:
        for name in DEFAULT_CSV_COLUMNS.get(file_key, ()):
            header.setdefault(name, None)
    for row in rows:
        for name in row:
            header.setdefault(name, None)
    columns = list(header)

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: flatten_for_csv(row.get(name)) for name in columns})
    LOGGER.debug("Wrote %d rows to %s", len(rows), path)
    return path


def export_markdown(out_dir: str | Path, file_key: str, text: str) -> Path:
    """Write a Markdown artefact (trailing newline enforced) and return its path."""
    return write_text(output_path(out_dir, file_key), text)


# --------------------------------------------------------------------------- #
# Model -> flat row conversion
# --------------------------------------------------------------------------- #


def signals_to_rows(signals: Sequence[ObservedSignal]) -> list[dict[str, Any]]:
    """Flatten observed signals into one row each, fields lifted to columns."""
    rows: list[dict[str, Any]] = []
    for signal in signals:
        row: dict[str, Any] = {
            "signal_id": signal.signal_id,
            "timestamp": signal.timestamp,
            "domain": signal.domain,
            "zone": signal.zone,
        }
        for name in _SIGNAL_VALUE_FIELDS:
            row[name] = signal.fields.get(name)
        row["source"] = signal.source
        row["measurement_id"] = signal.measurement_id
        # Any further normalized fields the extractor produced are kept rather
        # than dropped; sorted so the column order stays deterministic.
        for name in sorted(signal.fields):
            row.setdefault(name, signal.fields[name])
        row["row_index"] = signal.row_index
        row["origin_file"] = signal.origin_file
        rows.append(row)
    return rows


def matches_to_rows(matches: Sequence[RFCMatch]) -> list[dict[str, Any]]:
    """Flatten RFC matches, itemizing the score breakdown into its own columns."""
    rows: list[dict[str, Any]] = []
    for match in matches:
        breakdown = match.score_breakdown
        rows.append(
            {
                "signal_id": match.signal_id,
                "rfc_id": match.rfc_id,
                "rfc_title": match.rfc_title,
                "decision": match.decision,
                "score": match.score,
                "confidence": match.confidence,
                "timestamp_valid": match.timestamp_valid,
                "observation_timestamp": match.observation_timestamp,
                "rfc_publication_date": match.rfc_publication_date,
                "domain": match.domain,
                "zone": match.zone,
                "matched_indicator_ids": match.matched_indicator_ids,
                "failed_indicator_ids": match.failed_indicator_ids,
                "matched_fields": match.matched_fields,
                "missing_fields": match.missing_fields,
                "base_indicator_score": breakdown.base_indicator_score,
                "specificity_multiplier": breakdown.specificity_multiplier,
                "required_match_bonus": breakdown.required_match_bonus,
                "optional_match_bonus": breakdown.optional_match_bonus,
                "missing_required_penalty": breakdown.missing_required_penalty,
                "partial_match_penalty": breakdown.partial_match_penalty,
                "ambiguity_penalty": breakdown.ambiguity_penalty,
                "timestamp_penalty": breakdown.timestamp_penalty,
                "final_score": breakdown.final_score,
                "trace_id": match.trace_id,
                "reasoning_summary": match.reasoning_summary,
            }
        )
    return rows


def traces_to_rows(traces: Sequence[ReasoningTrace]) -> list[dict[str, Any]]:
    """Flatten reasoning traces; condition detail is summarized to counts.

    The full condition lists stay in ``reasoning_traces.json`` - the CSV exists
    for spreadsheet triage, where one row per trace is what is wanted.
    """
    rows: list[dict[str, Any]] = []
    for trace in traces:
        rows.append(
            {
                "trace_id": trace.trace_id,
                "signal_id": trace.signal_id,
                "rfc_id": trace.rfc_id,
                "rfc_title": trace.rfc_title,
                "observation_timestamp": trace.observation_timestamp,
                "rfc_publication_date": trace.rfc_publication_date,
                "timestamp_valid": trace.timestamp_valid,
                "decision": trace.decision,
                "confidence": trace.confidence,
                "final_score": trace.score_breakdown.final_score,
                "timestamp_penalty": trace.score_breakdown.timestamp_penalty,
                "matched_indicator_ids": trace.matched_indicator_ids,
                "failed_indicator_ids": trace.failed_indicator_ids,
                "skipped_indicator_ids": trace.skipped_indicator_ids,
                "missing_required_indicator_ids": trace.missing_required_indicator_ids,
                "missing_fields": trace.missing_fields,
                "matched_openintel_fields": trace.matched_openintel_fields,
                "matched_condition_count": len(trace.matched_conditions),
                "failed_condition_count": len(trace.failed_conditions),
                "uncertainty_notes": trace.uncertainty_notes,
                "reasoning_summary": trace.reasoning_summary,
                "score_steps": trace.score_breakdown.steps,
            }
        )
    return rows


def review_items_to_rows(items: Sequence[ReviewItem]) -> list[dict[str, Any]]:
    """Flatten review-queue items, including any verification verdict."""
    rows: list[dict[str, Any]] = []
    for item in items:
        verification = item.verification
        rows.append(
            {
                "item_id": item.item_id,
                "item_type": item.item_type,
                "severity": item.severity,
                "status": item.status,
                "reason": item.reason,
                "affected_rfc_ids": item.affected_rfc_ids,
                "affected_fields": item.affected_fields,
                "affected_signal_ids": item.affected_signal_ids,
                "trace_ids": item.trace_ids,
                "suggested_action": item.suggested_action,
                "verification_status": (
                    verification.verification_status if verification else None
                ),
                "verification_explanation": (
                    verification.explanation if verification else None
                ),
                "evidence": item.evidence,
            }
        )
    return rows


def timeline_to_rows(entries: Sequence[AdoptionTimelineEntry]) -> list[dict[str, Any]]:
    """Flatten adoption-timeline entries; buckets collapse to ``period=count``."""
    rows: list[dict[str, Any]] = []
    for entry in entries:
        rows.append(
            {
                "rfc_id": entry.rfc_id,
                "rfc_title": entry.rfc_title,
                "rfc_publication_date": entry.rfc_publication_date,
                "first_seen": entry.first_seen,
                "last_seen": entry.last_seen,
                "days_from_publication_to_first_seen": (
                    entry.days_from_publication_to_first_seen
                ),
                "observation_count": entry.observation_count,
                "distinct_domains": entry.distinct_domains,
                "distinct_zones": entry.distinct_zones,
                "domains": entry.domains,
                "zones": entry.zones,
                "monthly_counts": [
                    f"{bucket.period}={bucket.count}" for bucket in entry.monthly_counts
                ],
                "yearly_counts": [
                    f"{bucket.period}={bucket.count}" for bucket in entry.yearly_counts
                ],
                "notes": entry.notes,
            }
        )
    return rows


def schema_check_to_rows(report: SchemaCheckReport) -> list[dict[str, Any]]:
    """Flatten the schema cross-check into one row per indicator."""
    rows: list[dict[str, Any]] = []
    for check in report.indicators:
        fields_used: dict[str, None] = {}
        available_from: list[str] = []
        for condition in check.condition_checks:
            fields_used.setdefault(condition.field, None)
            if condition.available_from is not None:
                available_from.append(f"{condition.field}={iso(condition.available_from)}")
        rows.append(
            {
                "rfc_id": check.rfc_id,
                "rfc_title": check.rfc_title,
                "rfc_publication_date": check.rfc_publication_date,
                "indicator_id": check.indicator_id,
                "indicator_description": check.indicator_description,
                "required": check.required,
                "weight": check.weight,
                "queryability": check.queryability,
                "condition_count": len(check.condition_checks),
                "fields_used": list(fields_used),
                "present_fields": check.present_fields,
                "missing_fields": check.missing_fields,
                "available_from": available_from,
                "reasoning": check.reasoning,
                "warnings": check.warnings,
            }
        )
    return rows


# --------------------------------------------------------------------------- #
# Artefact bundles
# --------------------------------------------------------------------------- #


def export_schema_check(
    report: SchemaCheckReport, out_dir: str | Path, *, report_md: str
) -> dict[str, Path]:
    """Write every ``schema-check`` artefact; returns ``{file_key: path}``.

    ``queryable_indicators.json`` and ``non_queryable_indicators.json`` use the
    report's own definitions of those two sets. Indicators that came out
    ``partially_queryable`` or ``ambiguous`` appear in neither list file; the
    complete verdict for every indicator is in ``schema_check.json``.
    """
    directory = ensure_dir(out_dir)
    generated_at = report.generated_at
    written: dict[str, Path] = {}

    written["queryable_indicators"] = export_json_list(
        directory,
        "queryable_indicators",
        ENVELOPE_KEYS["queryable_indicators"],
        report.queryable_indicators,
        generated_at=generated_at,
    )
    written["non_queryable_indicators"] = export_json_list(
        directory,
        "non_queryable_indicators",
        ENVELOPE_KEYS["non_queryable_indicators"],
        report.non_queryable_indicators,
        generated_at=generated_at,
    )
    # The full report is not a list, so it is written as-is rather than wrapped.
    written["schema_check_json"] = write_json(
        output_path(directory, "schema_check_json"), report
    )
    written["schema_check_csv"] = export_csv(
        directory, "schema_check_csv", schema_check_to_rows(report)
    )
    written["schema_check_report_md"] = export_markdown(
        directory, "schema_check_report_md", report_md
    )
    return written


def build_run_manifest(result: PipelineResult, written: Mapping[str, Path]) -> dict[str, Any]:
    """Assemble the provenance record for one ``analyze`` run.

    The manifest is what makes a result directory self-describing: which inputs
    produced it, how much data was involved, which engine read the Parquet, and
    every warning collected along the way (schema-check warnings included, since
    those explain gaps in the matching that follows).
    """
    run_config = result.run_config
    schema_report = result.schema_report

    warnings: dict[str, None] = {}
    for message in list(result.warnings) + list(schema_report.warnings):
        warnings.setdefault(message, None)

    decisions: dict[str, int] = {}
    for match in result.matches:
        decisions[match.decision] = decisions.get(match.decision, 0) + 1

    return {
        "pipeline": config.PIPELINE_NAME,
        "version": config.PIPELINE_VERSION,
        "generated_at": iso(result.generated_at),
        "engine": run_config.engine,
        "inputs": {
            "checklists": run_config.checklists,
            "dictionary": run_config.dictionary,
            "parquet": run_config.parquet,
            "output_dir": run_config.out,
            "row_limit": run_config.limit,
            "min_score": run_config.min_score,
        },
        "counts": {
            # For an exhaustive run one signal is extracted per usable Parquet
            # row, so the signal count is also the row count. For a sampled
            # (scale) run it is emphatically not: `signals` holds exemplars, and
            # reporting their number as "rows" would understate a multi-million
            # row scan by five orders of magnitude.
            "rows": int(
                result.corpus_stats.get("rows_scanned", len(result.signals))
            ),
            "signals": len(result.signals),
            "sampled": result.is_sampled,
            "matches": len(result.matches),
            "traces": len(result.traces),
            "ranked_candidates": len(result.ranked_candidates),
            "review_items": len(result.review_items),
            "timeline_entries": len(result.timeline),
            "rfcs": schema_report.rfc_count,
            "indicators": schema_report.indicator_count,
            "dictionary_fields": schema_report.dictionary_field_count,
        },
        "matches_by_decision": {key: decisions[key] for key in sorted(decisions)},
        "indicators_by_queryability": {
            key: schema_report.counts_by_queryability[key]
            for key in sorted(schema_report.counts_by_queryability)
        },
        "outputs": {key: written[key].name for key in sorted(written)},
        "warning_count": len(warnings),
        "warnings": list(warnings),
    }


def export_analysis(
    result: PipelineResult, out_dir: str | Path, *, report_md: str
) -> dict[str, Path]:
    """Write every ``analyze`` artefact; returns ``{file_key: path}``.

    All envelopes carry ``result.generated_at`` so that one run's files agree on
    a single timestamp. The run manifest is written last because it records the
    names of everything else.
    """
    directory = ensure_dir(out_dir)
    generated_at = result.generated_at
    written: dict[str, Path] = {}

    list_artefacts: tuple[tuple[str, Sequence[Any]], ...] = (
        ("observed_signals", result.signals),
        ("rfc_matches", result.matches),
        ("ranked_candidates", result.ranked_candidates),
        ("reasoning_traces", result.traces),
        ("review_queue", result.review_items),
        ("adoption_timeline", result.timeline),
    )
    for file_key, items in list_artefacts:
        written[file_key] = export_json_list(
            directory, file_key, ENVELOPE_KEYS[file_key], items, generated_at=generated_at
        )

    written["observed_signals_csv"] = export_csv(
        directory, "observed_signals_csv", signals_to_rows(result.signals)
    )
    written["rfc_matches_csv"] = export_csv(
        directory, "rfc_matches_csv", matches_to_rows(result.matches)
    )
    written["reasoning_traces_csv"] = export_csv(
        directory, "reasoning_traces_csv", traces_to_rows(result.traces)
    )
    written["review_queue_csv"] = export_csv(
        directory, "review_queue_csv", review_items_to_rows(result.review_items)
    )
    written["adoption_timeline_csv"] = export_csv(
        directory, "adoption_timeline_csv", timeline_to_rows(result.timeline)
    )
    written["report_md"] = export_markdown(directory, "report_md", report_md)

    manifest_path = output_path(directory, "run_manifest")
    written["run_manifest"] = manifest_path
    write_json(manifest_path, build_run_manifest(result, written))
    return written
