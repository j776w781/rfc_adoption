"""The review queue: everything the pipeline is not entitled to decide alone.

A measurement pipeline can tell you that an indicator matched. It cannot tell
you that a field was missing because the mechanism is absent rather than because
the corpus never exported that column, nor that two RFCs separated by 3% of
score really are separable. Those judgements belong to a human, and this module
is where they are collected, explained and made actionable.

Every :class:`~openintel_rfc.models.ReviewItem` carries three things a reviewer
needs: a ``reason`` that names the concrete evidence, ``evidence`` rich enough
to act on without re-running the pipeline, and a ``suggested_action`` that says
what to change and where. Generic advice ("investigate further") is treated as a
defect here.

Volume control
--------------
A run over a real corpus produces millions of matches, and a review queue with
one row per match is a review queue nobody reads. Two rules keep it usable:

* Schema-level issues are emitted once per ``(item_type, rfc_id, indicator or
  field)`` - they are properties of the checklist and dictionary, not of any
  single observation.
* Match-level issues are grouped per ``(item_type, rfc_id)``, listing the
  affected signals together. At most :data:`MAX_LISTED_IDS` signal ids are
  listed; the true total is always recorded in ``evidence`` so a grouped row
  never hides how much it represents.

Item ids come from :func:`openintel_rfc.utils.review_id` after a total sort, so
``rev_0003`` means the same thing across two runs over the same inputs and the
dashboard's saved statuses stay attached to the right rows.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, get_args

from . import config
from .llm_verifier import LLMVerifier, get_verifier, verify_traces
from .models import (
    LLMVerification,
    RankedRFCCandidate,
    ReasoningTrace,
    ReviewItem,
    ReviewStatus,
    RFCChecklistDB,
    RFCMatch,
    SchemaCheckReport,
    Severity,
)
from .utils import (
    PipelineError,
    get_logger,
    iso,
    read_json,
    review_id,
    round_score,
    to_jsonable,
    unique_sorted,
    write_json,
)

__all__ = [
    "MAX_LISTED_IDS",
    "ITEM_TYPES",
    "build_review_queue",
    "review_queue_to_rows",
    "load_review_status",
    "save_review_status",
    "apply_review_status",
    "severity_counts",
    "default_status_path",
]

LOGGER = get_logger(__name__)

#: Cap on how many signal / trace ids a single grouped item lists inline.
MAX_LISTED_IDS = 20

#: Every item type this module emits, in the order the contract defines them.
ITEM_TYPES: tuple[str, ...] = (
    "non_queryable_indicator",
    "partially_queryable_indicator",
    "ambiguous_indicator",
    "timestamp_invalid_match",
    "partial_match",
    "missing_required_field",
    "schema_inconsistency",
    "close_ranking",
    "llm_review_recommended",
)

_SEVERITY_RANK: dict[str, int] = {"high": 0, "medium": 1, "low": 2}

_VALID_STATUSES: frozenset[str] = frozenset(get_args(ReviewStatus))

#: Matches "RFC 1234" / "RFC1234" inside free-form warning text.
_RFC_PATTERN = re.compile(r"RFC\s?(\d{3,5})")

#: Identifier-shaped tokens, used to spot field names inside warning text.
_TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

#: Placeholder item_id; replaced with a stable id once the queue is sorted.
_UNASSIGNED = "unassigned"

#: A draft item plus the key it deduplicates on.
_Draft = tuple[tuple[str, ...], ReviewItem]


# --------------------------------------------------------------------------- #
# Small shared helpers
# --------------------------------------------------------------------------- #


def _cap(values: Sequence[str]) -> tuple[list[str], int, bool]:
    """Return ``(listed, true_total, truncated)`` for an id list."""
    unique = [str(v) for v in unique_sorted(values)]
    return unique[:MAX_LISTED_IDS], len(unique), len(unique) > MAX_LISTED_IDS


def _joined(values: Sequence[str], empty: str = "none") -> str:
    return ", ".join(values) if values else empty


def _ticked(values: Sequence[str]) -> str:
    return ", ".join(f"`{v}`" for v in values) if values else "none"


def _dictionary_field_names(report: SchemaCheckReport) -> list[str]:
    """Analysis field names the corpus actually exports, in stable order."""
    if report.dictionary_fields:
        return sorted(f.name for f in report.dictionary_fields)
    # Fall back to whatever the indicators proved present; better than nothing
    # when a caller hands us a report without the dictionary attached.
    return report.required_fields()


def _exported_fields_phrase(report: SchemaCheckReport, limit: int = 12) -> str:
    names = _dictionary_field_names(report)
    shown = names[:limit]
    suffix = ", ..." if len(names) > len(shown) else ""
    return (", ".join(shown) + suffix) if shown else "(the dictionary lists no fields)"


def _native_columns(report: SchemaCheckReport, field_name: str) -> list[str]:
    for field in report.dictionary_fields:
        if field.name == field_name:
            return list(field.openintel_native_fields)
    return []


def _available_from(report: SchemaCheckReport, field_name: str) -> datetime | None:
    for field in report.dictionary_fields:
        if field.name == field_name:
            return field.available_from
    return None


def _native_columns_phrase(report: SchemaCheckReport, field_name: str) -> str:
    natives = _native_columns(report, field_name)
    if not natives:
        return (
            f"`{field_name}` lists no openintel_native_fields in the dictionary, so the "
            "Parquet reader has no column to resolve it from"
        )
    return f"`{field_name}` is derived from the OpenINTEL column(s) {_joined(natives)}"


def _grouped_signal_evidence(matches: Sequence[RFCMatch]) -> dict[str, Any]:
    """Shared evidence block for match-level items: counts, span, sample rows."""
    ordered = sorted(matches, key=lambda m: (m.observation_timestamp, m.signal_id))
    listed, total, truncated = _cap([m.signal_id for m in ordered])
    return {
        "observation_count": len(ordered),
        "affected_signal_id_count": total,
        "affected_signal_ids_truncated": truncated,
        "listed_signal_ids": listed,
        "earliest_observation": iso(ordered[0].observation_timestamp) if ordered else "",
        "latest_observation": iso(ordered[-1].observation_timestamp) if ordered else "",
        "domains": unique_sorted(m.domain for m in ordered)[:MAX_LISTED_IDS],
        "zones": unique_sorted(m.zone for m in ordered)[:MAX_LISTED_IDS],
    }


def _make_item(
    *,
    key: tuple[str, ...],
    item_type: str,
    severity: Severity,
    reason: str,
    suggested_action: str,
    affected_rfc_ids: Sequence[str] = (),
    affected_fields: Sequence[str] = (),
    affected_signal_ids: Sequence[str] = (),
    trace_ids: Sequence[str] = (),
    evidence: Mapping[str, Any] | None = None,
    verification: LLMVerification | None = None,
) -> _Draft:
    """Build one draft item with a JSON-safe evidence block and a dedup key."""
    if item_type not in ITEM_TYPES:
        raise PipelineError(
            f"Unknown review item_type {item_type!r}; expected one of "
            f"{', '.join(ITEM_TYPES)}."
        )
    item = ReviewItem(
        item_id=_UNASSIGNED,
        item_type=item_type,
        severity=severity,
        reason=reason,
        affected_rfc_ids=list(affected_rfc_ids),
        affected_fields=list(affected_fields),
        affected_signal_ids=list(affected_signal_ids),
        suggested_action=suggested_action,
        evidence=to_jsonable(dict(evidence or {})),
        trace_ids=list(trace_ids),
        verification=verification,
    )
    return key, item


# --------------------------------------------------------------------------- #
# Schema-level items
# --------------------------------------------------------------------------- #


def _condition_evidence(report: SchemaCheckReport, indicator_id: str) -> list[dict[str, Any]]:
    for check in report.indicators:
        if check.indicator_id != indicator_id:
            continue
        return [
            {
                "field": c.field,
                "op": c.op,
                "expected": c.expected,
                "field_exists": c.field_exists,
                "field_type": c.field_type,
                "type_compatible": c.type_compatible,
                "available_from": iso(c.available_from),
                "explanation": c.explanation,
            }
            for c in check.condition_checks
        ]
    return []


def _queryability_items(report: SchemaCheckReport) -> list[_Draft]:
    """One item per indicator the dictionary cannot fully support."""
    drafts: list[_Draft] = []
    exported = _exported_fields_phrase(report)

    for check in report.indicators:
        if check.queryability == "non_queryable":
            item_type, severity = "non_queryable_indicator", "high"
        elif check.queryability == "partially_queryable":
            item_type, severity = "partially_queryable_indicator", "medium"
        else:
            continue

        role = "required" if check.required else "optional"
        if item_type == "non_queryable_indicator":
            reason = (
                f"Indicator {check.indicator_id} ({role}, weight {check.weight}) of "
                f"{check.rfc_id} cannot be evaluated at all: field(s) "
                f"{_ticked(check.missing_fields)} are absent from the OpenINTEL analysis "
                f"dictionary, so no observation can ever match it. {check.reasoning}"
            )
            consequence = (
                f"Until then {check.rfc_id} cannot be measured from this corpus on this "
                "indicator and must not be reported as unadopted - the evidence was never "
                "collectable."
                if check.required
                else f"Until then {check.rfc_id} scores are systematically "
                f"{round_score(check.weight)} lower than the checklist intends."
            )
        else:
            reason = (
                f"Indicator {check.indicator_id} ({role}, weight {check.weight}) of "
                f"{check.rfc_id} is only partially queryable: it uses present field(s) "
                f"{_ticked(check.present_fields)} but also missing field(s) "
                f"{_ticked(check.missing_fields)}, and because an indicator's conditions "
                f"are ANDed it can never match. {check.reasoning}"
            )
            consequence = (
                f"Until then the indicator's weight of {round_score(check.weight)} is "
                f"unreachable and every {check.rfc_id} score is low by that amount."
            )

        suggested_action = (
            f"Add {_ticked(check.missing_fields)} to the OpenINTEL analysis dictionary with "
            f"an openintel_native_fields mapping to the real Parquet column(s) that carry "
            f"it, or rewrite indicator {check.indicator_id} to rely only on fields the "
            f"corpus exports ({exported}). {consequence}"
        )

        drafts.append(
            _make_item(
                key=(item_type, check.rfc_id, check.indicator_id),
                item_type=item_type,
                severity=severity,
                reason=reason,
                suggested_action=suggested_action,
                affected_rfc_ids=[check.rfc_id],
                affected_fields=unique_sorted(check.missing_fields),
                evidence={
                    "rfc_id": check.rfc_id,
                    "rfc_title": check.rfc_title,
                    "rfc_publication_date": iso(check.rfc_publication_date),
                    "indicator_id": check.indicator_id,
                    "indicator_description": check.indicator_description,
                    "required": check.required,
                    "weight": check.weight,
                    "queryability": check.queryability,
                    "missing_fields": unique_sorted(check.missing_fields),
                    "present_fields": unique_sorted(check.present_fields),
                    "schema_reasoning": check.reasoning,
                    "schema_warnings": list(check.warnings),
                    "condition_checks": _condition_evidence(report, check.indicator_id),
                    "dictionary_fields_available": _dictionary_field_names(report),
                },
            )
        )
    return drafts


def _ambiguous_indicator_items(
    report: SchemaCheckReport, matches: Sequence[RFCMatch], db: RFCChecklistDB
) -> list[_Draft]:
    """Indicators whose match does not pin attribution to one RFC.

    Two sources feed this: the schema checker's ``ambiguous`` queryability
    verdict, and the checklist's own ``ambiguous=True`` flag on an indicator
    that actually matched something. Both are the same reviewer question - "is
    this really *this* RFC?" - so they are merged into one item per indicator.
    """
    schema_reasoning: dict[tuple[str, str], str] = {}
    for check in report.indicators:
        if check.queryability == "ambiguous":
            schema_reasoning[(check.rfc_id, check.indicator_id)] = check.reasoning

    # Which ambiguous indicators actually drove a match, and for which signals.
    matched_signals: dict[tuple[str, str], list[RFCMatch]] = defaultdict(list)
    for match in matches:
        if match.decision not in {"valid_match", "ambiguous", "partial_match"}:
            continue
        entry = db.get(match.rfc_id)
        if entry is None:
            continue
        ambiguous_ids = {i.id for i in entry.indicators if i.ambiguous}
        for indicator_id in match.matched_indicator_ids:
            if indicator_id in ambiguous_ids:
                matched_signals[(match.rfc_id, indicator_id)].append(match)

    drafts: list[_Draft] = []
    for pair in sorted(set(schema_reasoning) | set(matched_signals)):
        rfc_id, indicator_id = pair
        entry = db.get(rfc_id)
        indicator = next(
            (i for i in entry.indicators if i.id == indicator_id), None
        ) if entry else None
        hits = matched_signals.get(pair, [])
        listed, total, truncated = _cap([m.signal_id for m in hits])
        related = list(entry.related_rfc_ids) if entry else []

        occurrence = (
            f"It drove {total} match(es) in this run"
            if total
            else "It did not match anything in this run, but it will as soon as the "
            "corpus contains the relevant records"
        )
        description = (
            indicator.description.rstrip(". ") if indicator else "see the checklist entry"
        )
        reason = (
            f"Indicator {indicator_id} of {rfc_id} is ambiguous ({description}): the same "
            f"observation is equally well explained by another RFC, so a match here is an "
            f"inference about the operator, not proof of adoption. {occurrence}. "
            + schema_reasoning.get(pair, "")
        ).strip()

        alternatives = (
            f"the competing explanation(s) {_joined(related)}"
            if related
            else "any other RFC that registers the same field values"
        )
        suggested_action = (
            f"Decide attribution by hand for signal(s) {_joined(listed, 'n/a')}"
            + (f" (+{total - len(listed)} more)" if truncated else "")
            + f": the observation is also consistent with {alternatives}. Either add a "
            f"condition to {indicator_id} that only {rfc_id} can explain, or keep "
            f"'ambiguous' out of build_timeline's include_decisions so these observations "
            f"are excluded from {rfc_id}'s adoption counts instead of inflating them."
        )

        drafts.append(
            _make_item(
                key=("ambiguous_indicator", rfc_id, indicator_id),
                item_type="ambiguous_indicator",
                severity="medium",
                reason=reason,
                suggested_action=suggested_action,
                affected_rfc_ids=unique_sorted([rfc_id, *related]),
                affected_fields=(
                    unique_sorted(indicator.fields_used) if indicator else []
                ),
                affected_signal_ids=listed,
                trace_ids=_cap([m.trace_id for m in hits])[0],
                evidence={
                    "rfc_id": rfc_id,
                    "indicator_id": indicator_id,
                    "indicator_description": indicator.description if indicator else "",
                    "indicator_required": indicator.required if indicator else None,
                    "indicator_weight": indicator.weight if indicator else None,
                    "checklist_notes": (indicator.notes if indicator else None),
                    "related_rfc_ids": related,
                    "schema_queryability_reasoning": schema_reasoning.get(pair, ""),
                    "match_count": total,
                    "affected_signal_ids_truncated": truncated,
                    "example_scores": [
                        round_score(m.score)
                        for m in sorted(hits, key=lambda m: m.signal_id)[:MAX_LISTED_IDS]
                    ],
                },
            )
        )
    return drafts


# --------------------------------------------------------------------------- #
# Match-level items
# --------------------------------------------------------------------------- #


def _timestamp_invalid_items(
    matches: Sequence[RFCMatch],
    traces_by_pair: Mapping[tuple[str, str], ReasoningTrace],
    verifications: Mapping[str, LLMVerification],
) -> list[_Draft]:
    """Observations that would have matched but predate the RFC.

    These are high severity for a specific reason: the same records are usually
    real evidence of *something*, just not of this RFC. Getting the attribution
    wrong here is what produces an adoption curve that starts before the RFC
    exists.
    """
    # Only genuine `timestamp_invalid` decisions belong here. Selecting on
    # `not match.timestamp_valid` alone would sweep in every observation that
    # merely predates an RFC it never matched anyway: those forfeit a score of
    # 0.0 and list no matched indicators, so they read as "6 observations
    # matched RFC 6605 indicator(s) none", which is noise dressed as a finding.
    # The matcher already reserves `timestamp_invalid` for evaluations that had
    # real evidence and lost it to the cutoff, which is exactly this item's
    # scope. The second arm is a safety net for a matcher that forgets to set
    # the decision; it still demands real matched evidence before raising.
    grouped: dict[str, list[RFCMatch]] = defaultdict(list)
    for match in matches:
        if match.decision == "timestamp_invalid" or (
            not match.timestamp_valid and match.matched_indicator_ids
        ):
            grouped[match.rfc_id].append(match)

    # Which other RFCs did these same signals validly match? That is what the
    # reviewer needs in order to re-attribute the observation.
    valid_by_signal: dict[str, list[str]] = defaultdict(list)
    for match in matches:
        if match.decision in {"valid_match", "ambiguous"} and match.timestamp_valid:
            valid_by_signal[match.signal_id].append(match.rfc_id)

    drafts: list[_Draft] = []
    for rfc_id in sorted(grouped):
        rows = sorted(grouped[rfc_id], key=lambda m: (m.observation_timestamp, m.signal_id))
        publication = rows[0].rfc_publication_date
        listed, total, truncated = _cap([m.signal_id for m in rows])
        forfeited = [m.score_breakdown.timestamp_penalty for m in rows]
        forfeited_total = round_score(sum(forfeited))
        max_forfeited = round_score(max(forfeited)) if forfeited else 0.0
        indicator_ids = unique_sorted(
            i for m in rows for i in m.matched_indicator_ids
        )
        earliest = rows[0]
        days_early = (publication - earliest.observation_timestamp).days
        alternatives = unique_sorted(
            rfc for m in rows for rfc in valid_by_signal.get(m.signal_id, [])
        )

        observations = [
            {
                "signal_id": m.signal_id,
                "observation_timestamp": iso(m.observation_timestamp),
                "days_before_publication": (
                    publication - m.observation_timestamp
                ).days,
                "forfeited_score": round_score(m.score_breakdown.timestamp_penalty),
                "matched_indicator_ids": list(m.matched_indicator_ids),
                "matched_fields": list(m.matched_fields),
                "domain": m.domain,
                "zone": m.zone,
                "trace_id": m.trace_id,
            }
            for m in rows[:MAX_LISTED_IDS]
        ]

        reason = (
            f"{total} observation(s) matched {rfc_id} indicator(s) {_joined(indicator_ids)} "
            f"but were recorded before {rfc_id} was published on {iso(publication)}; the "
            f"earliest, {earliest.signal_id} at {iso(earliest.observation_timestamp)}, is "
            f"{days_early} day(s) early. A combined score of {forfeited_total} was "
            f"forfeited, so these observations currently count as evidence for nothing."
        )
        if alternatives:
            re_attribution = (
                f"The same signal(s) already produced a valid match for "
                f"{_joined(alternatives)}, which is where this evidence belongs."
            )
        else:
            re_attribution = (
                "No other checklist RFC claimed these signals, so the evidence is currently "
                "discarded entirely; check whether the checklist is missing the earlier RFC "
                "that defined the record type or field value seen here."
            )
        suggested_action = (
            f"Verify the {rfc_id} publication_date {iso(publication)} in the checklist "
            f"against the RFC Editor record, then verify that the observation timestamps "
            f"(earliest {iso(earliest.observation_timestamp)}) are real measurement times "
            f"rather than partition dates or epoch-unit errors. If both are correct, these "
            f"records genuinely predate {rfc_id}. {re_attribution}"
        )

        representative = max(
            rows, key=lambda m: (m.score_breakdown.timestamp_penalty, m.signal_id)
        )
        rep_trace = traces_by_pair.get((representative.signal_id, representative.rfc_id))

        drafts.append(
            _make_item(
                key=("timestamp_invalid_match", rfc_id),
                item_type="timestamp_invalid_match",
                severity="high",
                reason=reason,
                suggested_action=suggested_action,
                affected_rfc_ids=unique_sorted([rfc_id, *alternatives]),
                affected_fields=unique_sorted(f for m in rows for f in m.matched_fields),
                affected_signal_ids=listed,
                trace_ids=_cap([m.trace_id for m in rows])[0],
                evidence={
                    "rfc_id": rfc_id,
                    "rfc_title": rows[0].rfc_title,
                    "rfc_publication_date": iso(publication),
                    "earliest_observation": iso(earliest.observation_timestamp),
                    "latest_observation": iso(rows[-1].observation_timestamp),
                    "max_days_before_publication": days_early,
                    "forfeited_score_total": forfeited_total,
                    "max_forfeited_score": max_forfeited,
                    "matched_indicator_ids": indicator_ids,
                    "affected_signal_id_count": total,
                    "affected_signal_ids_truncated": truncated,
                    "alternative_valid_rfc_ids": alternatives,
                    "observations": observations,
                },
                verification=(
                    verifications.get(rep_trace.trace_id) if rep_trace else None
                ),
            )
        )
    return drafts


def _partial_match_items(
    matches: Sequence[RFCMatch],
    db: RFCChecklistDB,
    report: SchemaCheckReport,
    traces_by_pair: Mapping[tuple[str, str], ReasoningTrace],
    verifications: Mapping[str, LLMVerification],
) -> list[_Draft]:
    """Some but not all required indicators matched.

    Severity rises to high when the RFC's specificity is ``very_high``: those
    are the RFCs whose indicators are uniquely attributable, so a near miss is
    most likely a strong result the pipeline failed to confirm.
    """
    grouped: dict[str, list[RFCMatch]] = defaultdict(list)
    for match in matches:
        if match.decision == "partial_match":
            grouped[match.rfc_id].append(match)

    drafts: list[_Draft] = []
    for rfc_id in sorted(grouped):
        rows = sorted(grouped[rfc_id], key=lambda m: (m.observation_timestamp, m.signal_id))
        entry = db.get(rfc_id)
        specificity = entry.specificity if entry else "medium"
        severity: Severity = "high" if specificity == "very_high" else "medium"

        matched_ids = unique_sorted(i for m in rows for i in m.matched_indicator_ids)
        failed_ids = unique_sorted(i for m in rows for i in m.failed_indicator_ids)
        required_ids = {i.id for i in entry.required_indicators} if entry else set()
        unmatched_required = unique_sorted(i for i in failed_ids if i in required_ids)
        missing_fields = unique_sorted(f for m in rows for f in m.missing_fields)
        listed, total, truncated = _cap([m.signal_id for m in rows])
        best_score = round_score(max((m.score for m in rows), default=0.0))

        if missing_fields:
            gap_clause = (
                f" Field(s) {_ticked(missing_fields)} were absent from the observation(s), "
                "so the pipeline cannot distinguish non-adoption from missing data."
            )
            mapping = "; ".join(
                _native_columns_phrase(report, field) for field in missing_fields
            )
            action = (
                f"Confirm the Parquet reader resolves the missing field(s) for these rows "
                f"({mapping}). If the column really is empty for this measurement "
                f"generation, record {rfc_id} as unevaluable for signal(s) "
                f"{_joined(listed, 'n/a')} rather than unmatched - a partial match here is "
                f"a measurement gap, not a negative result. If the data is there, the "
                f"reader's alias resolution is dropping it."
            )
        else:
            gap_clause = (
                " Every referenced field was present, so the unmatched required "
                "indicator(s) genuinely did not hold for these observations."
            )
            action = (
                f"Inspect indicator(s) {_joined(unmatched_required or failed_ids)} against "
                f"signal(s) {_joined(listed, 'n/a')}: decide whether the condition is too "
                f"strict for real deployments (in which case relax it or set required=false "
                f"in the checklist) or whether {rfc_id} genuinely is not deployed here (in "
                f"which case the partial match is correct and can be resolved as rejected)."
            )
        if severity == "high":
            action += (
                f" Treat this as high priority: {rfc_id} has very_high specificity, so its "
                "indicators are uniquely attributable and a near miss is likely a strong "
                "result being lost."
            )

        # When nothing matched at all, "indicator(s) none matched but ..." reads
        # as a typo. Say plainly that only corroborating evidence was found, or
        # none, so the sentence stays true in both shapes.
        if matched_ids:
            matched_clause = f"indicator(s) {_joined(matched_ids)} matched"
        else:
            matched_clause = "no indicator matched outright"
        reason = (
            f"{rfc_id} matched partially on {total} observation(s): {matched_clause} "
            f"and required indicator(s) "
            f"{_joined(unmatched_required or failed_ids)} did not, capping the score at "
            f"{best_score}.{gap_clause}"
        )

        representative = max(rows, key=lambda m: (m.score, m.signal_id))
        rep_trace = traces_by_pair.get((representative.signal_id, representative.rfc_id))

        evidence = {
            "rfc_id": rfc_id,
            "rfc_title": rows[0].rfc_title,
            "rfc_specificity": specificity,
            "matched_indicator_ids": matched_ids,
            "unmatched_required_indicator_ids": unmatched_required,
            "failed_indicator_ids": failed_ids,
            "missing_fields": missing_fields,
            "missing_field_native_columns": {
                field: _native_columns(report, field) for field in missing_fields
            },
            "best_score": best_score,
            "representative_signal_id": representative.signal_id,
            "representative_trace_id": representative.trace_id,
            **_grouped_signal_evidence(rows),
        }

        drafts.append(
            _make_item(
                key=("partial_match", rfc_id),
                item_type="partial_match",
                severity=severity,
                reason=reason,
                suggested_action=action,
                affected_rfc_ids=[rfc_id],
                affected_fields=missing_fields,
                affected_signal_ids=listed,
                trace_ids=_cap([m.trace_id for m in rows])[0],
                evidence=evidence,
                verification=(
                    verifications.get(rep_trace.trace_id) if rep_trace else None
                ),
            )
        )
    return drafts


def _missing_required_field_items(
    matches: Sequence[RFCMatch], db: RFCChecklistDB, report: SchemaCheckReport
) -> list[_Draft]:
    """A required indicator needed a field the observation did not carry.

    Only fields the dictionary *does* define are reported here. A field missing
    from the dictionary entirely is a schema problem, already covered by
    :func:`_queryability_items`; reporting it twice would double the queue
    without adding information.
    """
    known_fields = set(_dictionary_field_names(report))
    non_evaluable = {
        check.indicator_id
        for check in report.indicators
        if check.queryability in {"non_queryable", "partially_queryable"}
    }

    grouped: dict[tuple[str, str], list[tuple[RFCMatch, str]]] = defaultdict(list)
    for match in matches:
        entry = db.get(match.rfc_id)
        if match.indicator_evaluations:
            for evaluation in match.indicator_evaluations:
                if not evaluation.required or evaluation.indicator_id in non_evaluable:
                    continue
                for field in evaluation.missing_fields:
                    if field in known_fields:
                        grouped[(match.rfc_id, field)].append(
                            (match, evaluation.indicator_id)
                        )
        elif entry is not None:
            # The matcher did not attach per-indicator detail; fall back to the
            # match's own missing_fields intersected with required indicators.
            for indicator in entry.required_indicators:
                if indicator.id in non_evaluable:
                    continue
                for field in indicator.fields_used:
                    if field in known_fields and field in set(match.missing_fields):
                        grouped[(match.rfc_id, field)].append((match, indicator.id))

    drafts: list[_Draft] = []
    for rfc_id, field in sorted(grouped):
        rows = [m for m, _ in grouped[(rfc_id, field)]]
        indicator_ids = unique_sorted(i for _, i in grouped[(rfc_id, field)])
        ordered = sorted(rows, key=lambda m: (m.observation_timestamp, m.signal_id))
        listed, total, truncated = _cap([m.signal_id for m in ordered])
        available_from = _available_from(report, field)

        availability_clause = ""
        if available_from is not None and ordered:
            earliest = ordered[0].observation_timestamp
            if earliest < available_from:
                availability_clause = (
                    f" The dictionary marks `{field}` reliably populated only from "
                    f"{iso(available_from)}, which is after the earliest affected "
                    f"observation {iso(earliest)}, so at least some of these gaps are "
                    "expected corpus coverage rather than deployment facts."
                )

        reason = (
            f"Field `{field}`, needed by required indicator(s) {_joined(indicator_ids)} of "
            f"{rfc_id}, was absent from {total} observation(s) between "
            f"{iso(ordered[0].observation_timestamp)} and "
            f"{iso(ordered[-1].observation_timestamp)}, so those observations could not be "
            f"evaluated for {rfc_id} at all.{availability_clause}"
        )
        suggested_action = (
            f"Confirm the Parquet reader resolves `{field}` for these rows "
            f"({_native_columns_phrase(report, field)}); a missing alias in the reader looks "
            f"exactly like a missing value here. If the column is genuinely empty for this "
            f"measurement generation, report {rfc_id} as unevaluable for signal(s) "
            f"{_joined(listed, 'n/a')} instead of unmatched, and exclude them from the "
            f"denominator when quoting {rfc_id} adoption rates."
        )

        drafts.append(
            _make_item(
                key=("missing_required_field", rfc_id, field),
                item_type="missing_required_field",
                severity="medium",
                reason=reason,
                suggested_action=suggested_action,
                affected_rfc_ids=[rfc_id],
                affected_fields=[field],
                affected_signal_ids=listed,
                trace_ids=_cap([m.trace_id for m in ordered])[0],
                evidence={
                    "rfc_id": rfc_id,
                    "field": field,
                    "required_indicator_ids": indicator_ids,
                    "openintel_native_fields": _native_columns(report, field),
                    "field_available_from": iso(available_from),
                    **_grouped_signal_evidence(ordered),
                },
            )
        )
    return drafts


# --------------------------------------------------------------------------- #
# Schema inconsistencies and free-form warnings
# --------------------------------------------------------------------------- #


def _mentioned_fields(text: str, known_fields: Sequence[str]) -> list[str]:
    tokens = set(_TOKEN_PATTERN.findall(text))
    return [name for name in known_fields if name in tokens]


def _mentioned_rfcs(text: str) -> list[str]:
    return unique_sorted(f"RFC {number}" for number in _RFC_PATTERN.findall(text))


def _warning_action(report: SchemaCheckReport, text: str, fields: Sequence[str]) -> str:
    """Turn a warning string into something the reviewer can actually do.

    The availability branch is gated on the warning text actually being about
    availability. Almost every dictionary field carries an ``available_from``,
    so keying off its mere presence would attach a coverage-window suggestion to
    warnings about types, which is worse than saying less.
    """
    dated: list[tuple[str, datetime]] = []
    if "available" in text.lower():
        dated = [
            (f, d) for f, d in ((f, _available_from(report, f)) for f in fields)
            if d is not None
        ]
    if dated:
        clauses = "; ".join(f"`{f}` from {iso(d)}" for f, d in sorted(dated))
        return (
            f"The dictionary marks {clauses}. Either restrict the analysis window to on or "
            f"after that date, or annotate results before it as unknown rather than "
            f"negative - an RFC published earlier than its indicator fields became "
            f"available cannot be measured over the whole period."
        )
    if fields:
        return (
            f"Re-check the dictionary entry for {_ticked(fields)} (type, nullability and "
            f"openintel_native_fields) against the real OpenINTEL schema, then re-run "
            f"schema-check. This does not stop matching, but it silently reduces recall for "
            f"every indicator that uses the field."
        )
    return (
        "Resolve this warning before quoting counts from this run: it did not stop the "
        "pipeline, but warnings recorded here mark places where a result may be an artefact "
        "of the schema or the reader rather than of the measurement."
    )


def _schema_inconsistency_items(
    report: SchemaCheckReport, warnings: Sequence[str]
) -> list[_Draft]:
    """Type-compatibility and availability problems, plus collected run warnings."""
    known_fields = _dictionary_field_names(report)
    drafts: list[_Draft] = []

    # (a) Type incompatibilities found while checking individual conditions.
    for check in report.indicators:
        for condition in check.condition_checks:
            if condition.type_compatible:
                continue
            reason = (
                f"Indicator {check.indicator_id} of {check.rfc_id} compares field "
                f"`{condition.field}` (dictionary type {condition.field_type}) with "
                f"{condition.expected!r} using `{condition.op}`, which the schema checker "
                f"flagged as type-incompatible: {condition.explanation}"
            )
            suggested_action = (
                f"Either correct the declared type of `{condition.field}` in the OpenINTEL "
                f"analysis dictionary, or change the expected value in {check.indicator_id} "
                f"to a {condition.field_type}. As written the condition can fail for reasons "
                f"unrelated to deployment, which reads as non-adoption in the results."
            )
            drafts.append(
                _make_item(
                    key=(
                        "schema_inconsistency",
                        check.rfc_id,
                        check.indicator_id,
                        condition.field,
                        condition.op,
                    ),
                    item_type="schema_inconsistency",
                    severity="low",
                    reason=reason,
                    suggested_action=suggested_action,
                    affected_rfc_ids=[check.rfc_id],
                    affected_fields=[condition.field],
                    evidence={
                        "rfc_id": check.rfc_id,
                        "indicator_id": check.indicator_id,
                        "field": condition.field,
                        "op": condition.op,
                        "expected": condition.expected,
                        "field_type": condition.field_type,
                        "field_exists": condition.field_exists,
                        "available_from": iso(condition.available_from),
                        "explanation": condition.explanation,
                        "source": "condition_type_check",
                    },
                )
            )

    # (b) Per-indicator warnings, and (c)/(d) report-level and run-level warnings.
    #
    # These three lists overlap by construction: `check_schema` appends into the
    # caller's warning list and then copies it onto the report, so a schema
    # warning arrives here up to three times. Deduplicate on the warning text --
    # the first source to carry it wins, since an indicator-scoped occurrence is
    # more informative than the same sentence at run level. Keying on
    # (source, scope, text) instead would make every duplicate look distinct.
    sources: list[tuple[str, str, str]] = []  # (source, scope, text)
    seen_texts: set[str] = set()
    for check in report.indicators:
        for text in check.warnings:
            if text not in seen_texts:
                seen_texts.add(text)
                sources.append(("indicator_warning", check.indicator_id, text))
    for text in report.warnings:
        if text not in seen_texts:
            seen_texts.add(text)
            sources.append(("schema_report_warning", "", text))
    for text in warnings:
        if text not in seen_texts:
            seen_texts.add(text)
            sources.append(("pipeline_warning", "", text))

    for source, scope, text in sources:
        fields = _mentioned_fields(text, known_fields)
        rfc_ids = _mentioned_rfcs(text)
        drafts.append(
            _make_item(
                key=("schema_inconsistency", source, scope, text),
                item_type="schema_inconsistency",
                severity="low",
                reason=(f"{scope}: " if scope else "") + text,
                suggested_action=_warning_action(report, text, fields),
                affected_rfc_ids=rfc_ids,
                affected_fields=fields,
                evidence={
                    "source": source,
                    "scope": scope,
                    "warning": text,
                    "fields_mentioned": fields,
                    "field_availability": {
                        f: iso(_available_from(report, f)) for f in fields
                    },
                    "rfc_ids_mentioned": rfc_ids,
                },
            )
        )
    return drafts


# --------------------------------------------------------------------------- #
# Close rankings
# --------------------------------------------------------------------------- #


def _pair_rfc_id(value: Any) -> str:
    if isinstance(value, RankedRFCCandidate):
        return value.rfc_id
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping) and "rfc_id" in value:
        return str(value["rfc_id"])
    raise PipelineError(
        "close_pairs entries must contain RankedRFCCandidate objects, rfc_id strings, or "
        f"mappings with an 'rfc_id' key; got {type(value).__name__}."
    )


def _normalize_close_pairs(
    close_pairs: Sequence[tuple],
) -> list[tuple[str, str, float | None]]:
    """Accept the shapes ranking.py might emit, and reject anything else loudly."""
    normalized: list[tuple[str, str, float | None]] = []
    for pair in close_pairs:
        if not isinstance(pair, Sequence) or isinstance(pair, (str, bytes)):
            raise PipelineError(
                f"close_pairs entries must be 2- or 3-tuples; got {type(pair).__name__}."
            )
        items = list(pair)
        if len(items) not in (2, 3):
            raise PipelineError(
                f"close_pairs entries must have 2 or 3 elements (a, b[, delta]); got "
                f"{len(items)}."
            )
        delta = float(items[2]) if len(items) == 3 and items[2] is not None else None
        normalized.append((_pair_rfc_id(items[0]), _pair_rfc_id(items[1]), delta))
    return normalized


def _derive_close_pairs(
    ranked: Sequence[RankedRFCCandidate],
) -> list[tuple[str, str, float | None]]:
    """Fallback when the caller supplies no pairs: adjacent top candidates.

    Uses :data:`openintel_rfc.config.CLOSE_RANKING_RELATIVE_TOLERANCE`, the same
    constant the ranker uses, so an explicit empty ``close_pairs`` from a ranker
    that checked for itself will simply agree with this.
    """
    ordered = sorted(
        [c for c in ranked if c.score > 0], key=lambda c: (c.rank, -c.score, c.rfc_id)
    )[:5]
    pairs: list[tuple[str, str, float | None]] = []
    for first, second in zip(ordered, ordered[1:]):
        best = max(first.score, second.score)
        if best <= 0:
            continue
        relative = abs(first.score - second.score) / best
        if relative <= config.CLOSE_RANKING_RELATIVE_TOLERANCE:
            pairs.append((first.rfc_id, second.rfc_id, relative))
    return pairs


def _close_ranking_items(
    close_pairs: Sequence[tuple], ranked: Sequence[RankedRFCCandidate]
) -> list[_Draft]:
    pairs = _normalize_close_pairs(close_pairs) or _derive_close_pairs(ranked)
    by_id = {c.rfc_id: c for c in ranked}
    tolerance_pct = round(config.CLOSE_RANKING_RELATIVE_TOLERANCE * 100, 2)

    drafts: list[_Draft] = []
    for rfc_a, rfc_b, delta in pairs:
        first, second = by_id.get(rfc_a), by_id.get(rfc_b)
        score_a = first.score if first else 0.0
        score_b = second.score if second else 0.0
        best = max(score_a, score_b)
        relative = delta if delta is not None else (
            abs(score_a - score_b) / best if best > 0 else 0.0
        )
        indicators_a = set(first.matched_indicator_ids) if first else set()
        indicators_b = set(second.matched_indicator_ids) if second else set()
        only_a = unique_sorted(indicators_a - indicators_b)
        only_b = unique_sorted(indicators_b - indicators_a)
        shared = unique_sorted(indicators_a & indicators_b)
        signals = unique_sorted(
            (first.example_signal_ids if first else [])
            + (second.example_signal_ids if second else [])
        )[:MAX_LISTED_IDS]

        overlap = (
            f"They share indicator(s) {_joined(shared)}."
            if shared
            else "They share no matched indicators at all, so the near-tie comes from the "
            "weights and specificity multipliers rather than from common evidence."
        )
        reason = (
            f"{rfc_a} (score {round_score(score_a)}) and {rfc_b} (score "
            f"{round_score(score_b)}) differ by {round(relative * 100, 2)}%, inside the "
            f"{tolerance_pct}% tolerance for declaring a winner, so the top-ranked RFC for "
            f"these observations is not separable on score alone. {overlap}"
        )
        if only_a or only_b:
            distinguishing = (
                f"Compare the distinguishing indicators (only {rfc_a}: {_joined(only_a)}; "
                f"only {rfc_b}: {_joined(only_b)}) against signal(s) "
                f"{_joined(signals, 'the supporting signals')}, and confirm the fields those "
                f"indicators read were actually populated - an unpopulated field is what "
                f"usually collapses the gap between two RFCs."
            )
        else:
            distinguishing = (
                f"{rfc_a} and {rfc_b} matched on exactly the same indicators, so score is "
                f"not evidence of a difference at all; the checklist needs a condition that "
                f"only one of them can satisfy."
            )
        suggested_action = (
            f"Do not report {rfc_a} as the single best match. {distinguishing} Then either "
            f"add a discriminating condition to the checklist, or report both candidates "
            f"with their scores and let the reader see the ambiguity."
        )

        drafts.append(
            _make_item(
                key=("close_ranking", *sorted((rfc_a, rfc_b))),
                item_type="close_ranking",
                severity="medium",
                reason=reason,
                suggested_action=suggested_action,
                affected_rfc_ids=sorted((rfc_a, rfc_b)),
                affected_fields=unique_sorted(
                    (first.matched_fields if first else [])
                    + (second.matched_fields if second else [])
                ),
                affected_signal_ids=signals,
                trace_ids=unique_sorted(
                    (first.example_trace_ids if first else [])
                    + (second.example_trace_ids if second else [])
                )[:MAX_LISTED_IDS],
                evidence={
                    "rfc_a": rfc_a,
                    "rfc_b": rfc_b,
                    "score_a": round_score(score_a),
                    "score_b": round_score(score_b),
                    "relative_difference": round_score(relative),
                    "tolerance": config.CLOSE_RANKING_RELATIVE_TOLERANCE,
                    "specificity_a": first.specificity if first else None,
                    "specificity_b": second.specificity if second else None,
                    "indicators_only_in_a": only_a,
                    "indicators_only_in_b": only_b,
                    "shared_indicators": shared,
                    "supporting_signal_count_a": (
                        first.supporting_signal_count if first else 0
                    ),
                    "supporting_signal_count_b": (
                        second.supporting_signal_count if second else 0
                    ),
                    "derived_locally": not close_pairs,
                },
            )
        )
    return drafts


# --------------------------------------------------------------------------- #
# Verifier-driven items
# --------------------------------------------------------------------------- #


def _llm_review_items(
    traces: Sequence[ReasoningTrace], verifications: Mapping[str, LLMVerification]
) -> list[_Draft]:
    grouped: dict[str, list[ReasoningTrace]] = defaultdict(list)
    for trace in traces:
        verification = verifications.get(trace.trace_id)
        if verification and verification.verification_status == "needs_manual_review":
            grouped[trace.rfc_id].append(trace)

    drafts: list[_Draft] = []
    for rfc_id in sorted(grouped):
        rows = sorted(grouped[rfc_id], key=lambda t: t.trace_id)
        representative = rows[0]
        verification = verifications[representative.trace_id]
        listed_traces, trace_total, trace_truncated = _cap([t.trace_id for t in rows])
        listed_signals, signal_total, _ = _cap([t.signal_id for t in rows])
        decisions = sorted({t.decision for t in rows})

        reason = (
            f"The {verification.backend} verifier returned needs_manual_review for "
            f"{trace_total} trace(s) on {rfc_id} (decisions: {_joined(decisions)}). "
            f"Representative verdict: {verification.explanation}"
        )
        suggested_action = (
            f"Open trace(s) {_joined(listed_traces)} in reasoning_traces.json and settle "
            f"them by hand: for each, decide whether the recorded field values really "
            f"identify {rfc_id} or merely something consistent with it, then mark the item "
            f"accepted or rejected. Recording the outcome here is what stops the same "
            f"observations being re-litigated next run. If this volume is unmanageable, "
            f"wire a real LLM backend (see openintel_rfc.llm_verifier.register_verifier) "
            f"rather than relaxing the checklist."
        )

        drafts.append(
            _make_item(
                key=("llm_review_recommended", rfc_id),
                item_type="llm_review_recommended",
                severity="medium",
                reason=reason,
                suggested_action=suggested_action,
                affected_rfc_ids=[rfc_id],
                affected_fields=unique_sorted(f for t in rows for f in t.missing_fields),
                affected_signal_ids=listed_signals,
                trace_ids=listed_traces,
                evidence={
                    "rfc_id": rfc_id,
                    "backend": verification.backend,
                    "trace_count": trace_total,
                    "trace_ids_truncated": trace_truncated,
                    "affected_signal_id_count": signal_total,
                    "decisions": decisions,
                    "representative_trace_id": representative.trace_id,
                    "representative_explanation": verification.explanation,
                    "explanations": [
                        verifications[t.trace_id].explanation
                        for t in rows[:MAX_LISTED_IDS]
                    ],
                },
                verification=verification,
            )
        )
    return drafts


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #


def _finalize(drafts: Sequence[_Draft]) -> list[ReviewItem]:
    """Deduplicate, sort into a stable order, and mint item ids."""
    deduped: dict[tuple[str, ...], ReviewItem] = {}
    for key, item in drafts:
        if key in deduped:
            # Dedup keys are built to be content-unique, so a collision means two
            # genuinely different findings collapsed into one and a reviewer will
            # never see the second. That is a bug worth surfacing, not a debug
            # detail -- hence warning level rather than debug.
            LOGGER.warning(
                "Two distinct review items collided on dedup key %s; only the first is "
                "kept, so a finding may be missing from the queue.",
                key,
            )
            continue
        deduped[key] = item

    items = sorted(
        deduped.values(),
        key=lambda i: (
            _SEVERITY_RANK.get(i.severity, len(_SEVERITY_RANK)),
            i.item_type,
            "|".join(i.affected_rfc_ids),
            "|".join(i.affected_fields),
            # Final tiebreaker so two items that agree on every sort field still
            # get a reproducible order (and therefore reproducible item ids).
            i.reason,
        ),
    )
    for index, item in enumerate(items, start=1):
        item.item_id = review_id(index)
    return items


def build_review_queue(
    *,
    schema_report: SchemaCheckReport,
    matches: Sequence[RFCMatch],
    traces: Sequence[ReasoningTrace],
    ranked: Sequence[RankedRFCCandidate],
    db: RFCChecklistDB,
    verifier: LLMVerifier | None = None,
    warnings: Sequence[str] = (),
    close_pairs: Sequence[tuple] = (),
) -> list[ReviewItem]:
    """Assemble the full review queue for one pipeline run.

    ``verifier`` defaults to the deterministic offline backend, so building the
    queue never requires credentials or a network call. Traces whose decision is
    ``no_match`` are not verified: the verdict would always be ``rejected`` and
    would produce no item, so verifying them is pure cost.

    ``close_pairs`` comes from the ranker. When it is empty the module derives
    adjacent close pairs from ``ranked`` itself using the same configured
    tolerance, so a caller that does not compute them still gets the check.
    """
    active_verifier = verifier or get_verifier()
    verifiable = [t for t in traces if t.decision != "no_match"]
    verifications = verify_traces(verifiable, db, active_verifier)
    traces_by_pair = {(t.signal_id, t.rfc_id): t for t in traces}

    drafts: list[_Draft] = []
    drafts += _queryability_items(schema_report)
    drafts += _ambiguous_indicator_items(schema_report, matches, db)
    drafts += _timestamp_invalid_items(matches, traces_by_pair, verifications)
    drafts += _partial_match_items(matches, db, schema_report, traces_by_pair, verifications)
    drafts += _missing_required_field_items(matches, db, schema_report)
    drafts += _schema_inconsistency_items(schema_report, warnings)
    drafts += _close_ranking_items(close_pairs, ranked)
    drafts += _llm_review_items(traces, verifications)
    return _finalize(drafts)


# --------------------------------------------------------------------------- #
# Flat rendering
# --------------------------------------------------------------------------- #


def review_queue_to_rows(items: Sequence[ReviewItem]) -> list[dict[str, Any]]:
    """Flatten review items into CSV-ready rows.

    ``evidence`` is kept as a JSON string rather than dropped: it is the part a
    reviewer needs in order to act without re-running the pipeline, and a CSV
    that omits it is a worklist, not a record.
    """
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
                "affected_rfc_ids": "; ".join(item.affected_rfc_ids),
                "affected_fields": "; ".join(item.affected_fields),
                "affected_signal_ids": "; ".join(item.affected_signal_ids),
                "trace_ids": "; ".join(item.trace_ids),
                "suggested_action": item.suggested_action,
                "verification_status": (
                    verification.verification_status if verification else ""
                ),
                "verification_backend": verification.backend if verification else "",
                "verification_explanation": (
                    verification.explanation if verification else ""
                ),
                "evidence": json.dumps(
                    to_jsonable(item.evidence), ensure_ascii=False, sort_keys=True
                ),
            }
        )
    return rows


def severity_counts(items: Sequence[ReviewItem]) -> dict[str, int]:
    """Count items per severity, always reporting all three levels."""
    counts = {level: 0 for level in ("high", "medium", "low")}
    for item in items:
        if item.severity not in counts:  # pragma: no cover - model constrains this
            raise PipelineError(
                f"Review item {item.item_id} has unknown severity {item.severity!r}."
            )
        counts[item.severity] += 1
    return counts


# --------------------------------------------------------------------------- #
# Reviewer status persistence (the dashboard mutates this file)
# --------------------------------------------------------------------------- #


def default_status_path(output_dir: str | Path) -> Path:
    """Location of the review-status file inside a run's output directory."""
    return Path(output_dir) / config.OUTPUT_FILES["review_queue_status"]


def _validate_statuses(statuses: Mapping[str, Any], source: str) -> dict[str, str]:
    if not isinstance(statuses, Mapping):
        raise PipelineError(
            f"{source} must contain a JSON object mapping item_id to status, got "
            f"{type(statuses).__name__}."
        )
    validated: dict[str, str] = {}
    for item_id, status in statuses.items():
        if not isinstance(item_id, str) or not isinstance(status, str):
            raise PipelineError(
                f"{source} contains a non-string entry ({item_id!r}: {status!r}); every "
                "key and value must be a string."
            )
        if status not in _VALID_STATUSES:
            raise PipelineError(
                f"{source} gives item {item_id} the unknown status {status!r}. Valid "
                f"statuses: {', '.join(sorted(_VALID_STATUSES))}."
            )
        validated[item_id] = status
    return validated


def load_review_status(path: str | Path) -> dict[str, str]:
    """Load ``{item_id: status}`` from disk.

    A missing file means "nobody has reviewed anything yet" and yields ``{}``. A
    file that exists but is unreadable, malformed or carries an unknown status
    raises: silently discarding a reviewer's decisions would be worse than
    stopping.
    """
    file_path = Path(path)
    if not file_path.is_file():
        return {}
    payload = read_json(file_path)
    return _validate_statuses(payload, str(file_path))


def save_review_status(path: str | Path, statuses: dict[str, str]) -> Path:
    """Persist ``{item_id: status}``, sorted by item id for a stable diff."""
    validated = _validate_statuses(statuses, "statuses")
    ordered = {item_id: validated[item_id] for item_id in sorted(validated)}
    return write_json(path, ordered)


def apply_review_status(
    items: Sequence[ReviewItem], statuses: Mapping[str, str]
) -> list[ReviewItem]:
    """Return copies of ``items`` with persisted reviewer statuses applied.

    Status ids that match no current item are logged rather than dropped
    quietly: they usually mean the queue changed shape between runs, which is
    exactly when a reviewer's earlier decisions are at risk of being lost.
    """
    validated = _validate_statuses(statuses, "statuses")
    known = {item.item_id for item in items}
    unknown = sorted(set(validated) - known)
    if unknown:
        LOGGER.warning(
            "%d saved review status(es) refer to item ids not in this queue (%s%s); the "
            "queue's shape changed between runs and those decisions are not being applied.",
            len(unknown),
            ", ".join(unknown[:MAX_LISTED_IDS]),
            ", ..." if len(unknown) > MAX_LISTED_IDS else "",
        )
    return [
        item.model_copy(update={"status": validated[item.item_id]})
        if item.item_id in validated
        else item.model_copy()
        for item in items
    ]
