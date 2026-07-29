"""Structured decision traces and the prose that explains them.

The pipeline emits **no hidden chain-of-thought**. What it emits is an explicit,
structured record of a decision that was already made by deterministic code:
which RFC was considered, which indicator was checked, which OpenINTEL field it
used, what passed, what failed, whether the timestamp was valid, why the score
came out where it did, and what remains uncertain. Everything in this module is
a rendering of :class:`~openintel_rfc.models.IndicatorEvaluation` /
:class:`~openintel_rfc.models.ScoreBreakdown` data that already exists; nothing
here influences a verdict.

The prose is written to be falsifiable. It names concrete field values so a
reader can check the claim against the observation instead of trusting it.

This module is a leaf: it imports only ``models``, ``config`` and ``utils``.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any, cast

from .models import (
    CONFIDENCE_THRESHOLDS,
    ConditionEvaluation,
    Confidence,
    Decision,
    IndicatorEvaluation,
    ObservedSignal,
    ReasoningTrace,
    RFCChecklistEntry,
    ScoreBreakdown,
    TimestampCheck,
)
from .utils import flatten_for_csv, format_value, iso, round_score, trace_id, unique_sorted

__all__ = [
    "explain_condition",
    "explain_indicator",
    "explain_timestamp",
    "summarize_decision",
    "build_trace",
    "trace_to_row",
]


# --------------------------------------------------------------------------- #
# Formatting helpers
# --------------------------------------------------------------------------- #


def _num(value: float) -> str:
    """Render a score term compactly but exactly (mirrors ``ranking._num``)."""
    text = f"{round_score(float(value)):.4f}".rstrip("0")
    return text + "0" if text.endswith(".") else text


def _day(value: datetime) -> str:
    """Render a timestamp as a date when it has no time-of-day component."""
    if value.hour == value.minute == value.second == value.microsecond == 0:
        return value.date().isoformat()
    return iso(value)


def _confidence_for(score: float) -> Confidence:
    """Local confidence banding.

    ``ranking`` owns the canonical function, but this module may not import it
    (both are leaves), so the shared table in ``models`` is read directly rather
    than a second threshold set being invented here.
    """
    for threshold, label in CONFIDENCE_THRESHOLDS:
        if score >= threshold:
            return cast(Confidence, label)
    return "none"


def _join(parts: Sequence[str], conjunction: str = "and") -> str:
    items = [p for p in parts if p]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} {conjunction} {items[-1]}"


def _dedupe(values: Sequence[str]) -> list[str]:
    """Drop repeats while keeping the (already deterministic) first-seen order."""
    return list(dict.fromkeys(v for v in values if v))


# --------------------------------------------------------------------------- #
# Condition-level explanation
# --------------------------------------------------------------------------- #

_PASSED_TEMPLATES: dict[str, str] = {
    "equals": "{field}={observed} equals the expected value {expected}",
    "not_equals": "{field}={observed} differs from {expected} as required",
    "in": "{field}={observed} is in {expected}",
    "exists": "{field} is present (observed {observed})",
    "contains": "{field}={observed} contains {expected}",
    "greater_or_equal": "{field}={observed} is >= {expected}",
    "less_or_equal": "{field}={observed} is <= {expected}",
}

_FAILED_TEMPLATES: dict[str, str] = {
    "equals": "{field}={observed} does not equal the expected value {expected}",
    "not_equals": "{field}={observed} equals {expected}, which this condition excludes",
    "in": "{field}={observed} is not in {expected}",
    "exists": "{field} is not present",
    "contains": "{field}={observed} does not contain {expected}",
    "greater_or_equal": "{field}={observed} is not >= {expected}",
    "less_or_equal": "{field}={observed} is not <= {expected}",
}

_OP_PHRASES: dict[str, str] = {
    "equals": "must equal {expected}",
    "not_equals": "must differ from {expected}",
    "in": "must be in {expected}",
    "exists": "must be present",
    "contains": "must contain {expected}",
    "greater_or_equal": "must be >= {expected}",
    "less_or_equal": "must be <= {expected}",
}


def explain_condition(cond_eval: ConditionEvaluation) -> str:
    """Render one condition evaluation as a checkable clause.

    Any explanation already attached to the evaluation wins: the matcher sets
    one for cases the field values alone cannot express, such as a genuine type
    mismatch or a malformed checklist condition.
    """
    if cond_eval.explanation:
        return cond_eval.explanation

    field = cond_eval.field
    observed = format_value(cond_eval.observed)
    expected = format_value(cond_eval.expected)

    if not cond_eval.field_present:
        requirement = _OP_PHRASES.get(cond_eval.op, f"must satisfy {cond_eval.op}").format(
            expected=expected
        )
        return (
            f"field '{field}' is absent from this observation, so the condition "
            f"'{field} {requirement}' could not be satisfied (absence is not evidence)"
        )

    templates = _PASSED_TEMPLATES if cond_eval.passed else _FAILED_TEMPLATES
    template = templates.get(cond_eval.op, "{field}={observed} vs {expected}")
    return template.format(field=field, observed=observed, expected=expected)


def _condition_clauses(
    ind_eval: IndicatorEvaluation, *, passed: bool
) -> list[str]:
    return [explain_condition(c) for c in ind_eval.conditions if c.passed is passed]


def _first_failure(ind_eval: IndicatorEvaluation) -> str:
    for condition in ind_eval.conditions:
        if not condition.passed:
            return explain_condition(condition)
    return "no condition failed"


# --------------------------------------------------------------------------- #
# Indicator- and timestamp-level explanation
# --------------------------------------------------------------------------- #


def explain_indicator(ind_eval: IndicatorEvaluation) -> str:
    """Render one indicator evaluation, including why it was skipped if it was."""
    role = "Required" if ind_eval.required else "Optional"
    head = f"{role} indicator {ind_eval.indicator_id} (weight {_num(ind_eval.weight)})"

    if ind_eval.skipped:
        fields = ", ".join(ind_eval.missing_fields) or "its fields"
        verb = "is" if len(ind_eval.missing_fields) == 1 else "are"
        return (
            f"{head} was not evaluated: its queryability is {ind_eval.queryability} "
            f"because {fields} {verb} not exported by the OpenINTEL corpus. It was "
            "never tested, so it counts neither as evidence nor as a failure."
        )

    if ind_eval.matched:
        clauses = _join(_condition_clauses(ind_eval, passed=True))
        text = f"{head} matched: {clauses}."
        if ind_eval.ambiguous:
            text += (
                " The checklist flags this indicator ambiguous: the same observation "
                "is equally consistent with other RFCs, so the match is penalized and "
                "routed to review."
            )
        return text

    failed = _join(_condition_clauses(ind_eval, passed=False))
    text = f"{head} did not match: {failed}."
    passed_clauses = _condition_clauses(ind_eval, passed=True)
    if passed_clauses:
        text += f" Conditions that did hold: {_join(passed_clauses)}."
    if ind_eval.missing_fields:
        text += (
            f" The observation carries no value for "
            f"{_join(sorted(ind_eval.missing_fields))}, so that part of the "
            "signature is untested rather than contradicted."
        )
    return text


def _timestamp_clause(check: TimestampCheck, rfc_label: str) -> str:
    """Sentence fragment: how the observation sits relative to publication."""
    observation = _day(check.observation_timestamp)
    publication = _day(check.rfc_publication_date)
    days = abs(check.days_after_publication)
    if check.valid:
        return (
            f"the observation on {observation} is {days} days after {rfc_label}'s "
            f"publication on {publication}"
        )
    return (
        f"the observation on {observation} predates {rfc_label}'s publication on "
        f"{publication} by {days} days"
    )


def _timestamp_sentence(check: TimestampCheck, rfc_label: str) -> str:
    # Not str.capitalize(): it would lower-case the rest of the sentence and
    # turn "RFC 8078" into "rfc 8078".
    clause = _timestamp_clause(check, rfc_label)
    sentence = clause[0].upper() + clause[1:]
    if check.valid:
        return f"{sentence}, so the timestamp is valid."
    return (
        f"{sentence}. An observation cannot evidence adoption of an RFC that did not "
        "yet exist, so the score is forfeited."
    )


def explain_timestamp(check: TimestampCheck) -> str:
    """Render the publication-date cutoff verdict as a full sentence."""
    return _timestamp_sentence(check, "the RFC")


# --------------------------------------------------------------------------- #
# Decision summary
# --------------------------------------------------------------------------- #


def _score_expression(breakdown: ScoreBreakdown, rfc: RFCChecklistEntry) -> str:
    """The score arithmetic as one inline expression, e.g.
    ``(10.0 required + 1.5 optional) x 1.5 very_high specificity``."""
    positive = [f"{_num(breakdown.base_indicator_score)} required"]
    if breakdown.optional_match_bonus:
        positive.append(f"{_num(breakdown.optional_match_bonus)} optional")
    if breakdown.required_match_bonus:
        positive.append(f"{_num(breakdown.required_match_bonus)} all-required bonus")
    negative = []
    if breakdown.missing_required_penalty:
        negative.append(f"{_num(breakdown.missing_required_penalty)} missing-required")
    if breakdown.partial_match_penalty:
        negative.append(f"{_num(breakdown.partial_match_penalty)} partial-match")
    if breakdown.ambiguity_penalty:
        negative.append(f"{_num(breakdown.ambiguity_penalty)} ambiguity")

    expression = " + ".join(positive)
    for term in negative:
        expression += f" - {term} penalty"
    return (
        f"({expression}) x {_num(breakdown.specificity_multiplier)} "
        f"{rfc.specificity} specificity"
    )


def _raw_total(breakdown: ScoreBreakdown) -> float:
    return (
        breakdown.base_indicator_score
        + breakdown.required_match_bonus
        + breakdown.optional_match_bonus
        - breakdown.missing_required_penalty
        - breakdown.partial_match_penalty
        - breakdown.ambiguity_penalty
    )


def _score_sentence(
    rfc: RFCChecklistEntry, breakdown: ScoreBreakdown, confidence: Confidence
) -> str:
    raw = _raw_total(breakdown)
    if raw <= 0.0:
        return (
            f"Score {_num(breakdown.final_score)} ({confidence}): the penalties leave a "
            f"raw total of {_num(raw)}, which is clamped to 0 before the "
            f"{_num(breakdown.specificity_multiplier)} {rfc.specificity} "
            "specificity multiplier."
        )
    return (
        f"Score {_num(breakdown.final_score)} ({confidence}) = "
        f"{_score_expression(breakdown, rfc)}."
    )


def _primary_matched(
    indicator_evals: Sequence[IndicatorEvaluation],
) -> IndicatorEvaluation | None:
    matched = [e for e in indicator_evals if e.matched and not e.skipped]
    if not matched:
        return None
    return sorted(matched, key=lambda e: (not e.required, -e.weight, e.indicator_id))[0]


def _primary_failed_required(
    indicator_evals: Sequence[IndicatorEvaluation],
) -> IndicatorEvaluation | None:
    failed = [e for e in indicator_evals if e.required and not e.skipped and not e.matched]
    if not failed:
        return None
    return sorted(failed, key=lambda e: (-e.weight, e.indicator_id))[0]


def _matched_clause(ind_eval: IndicatorEvaluation) -> str:
    return _join(_condition_clauses(ind_eval, passed=True))


def _observed_values(ind_eval: IndicatorEvaluation) -> str:
    """The satisfied field values of an indicator, e.g. ``rr_type=CDS and algorithm=0``."""
    values = list(
        dict.fromkeys(
            f"{c.field}={format_value(c.observed)}" for c in ind_eval.conditions if c.passed
        )
    )
    return _join(values)


def _compose_summary(
    rfc: RFCChecklistEntry,
    decision: Decision,
    indicator_evals: Sequence[IndicatorEvaluation],
    timestamp_check: TimestampCheck,
    breakdown: ScoreBreakdown,
    *,
    subject: str,
    confidence: Confidence,
) -> str:
    """Build the prose summary shared by :func:`summarize_decision` and traces."""
    primary = _primary_matched(indicator_evals)
    failed_required = _primary_failed_required(indicator_evals)
    skipped = [e for e in indicator_evals if e.skipped]
    parts: list[str] = []

    if decision == "timestamp_invalid":
        evidence = (
            f"although {_observed_values(primary)} satisfy the "
            f"{'required' if primary.required else 'optional'} indicator "
            f"{primary.indicator_id}"
            if primary
            else "although the observation is otherwise consistent with this RFC"
        )
        parts.append(
            f"{rfc.rfc_id} cannot explain {subject}: {evidence}, "
            f"{_timestamp_clause(timestamp_check, rfc.rfc_id)}."
        )
        parts.append(
            "An observation cannot evidence adoption of an RFC that did not yet exist, "
            f"so the score of {_num(breakdown.timestamp_penalty)} is forfeited and this "
            "is routed to the review queue."
        )
        parts.append(
            f"The withheld score derives from {_score_expression(breakdown, rfc)}."
        )
        return " ".join(parts)

    if decision == "non_queryable":
        ids = ", ".join(unique_sorted(e.indicator_id for e in skipped)) or "its indicators"
        parts.append(
            f"{rfc.rfc_id} could not be evaluated against {subject}: every required "
            f"indicator ({ids}) depends on fields the OpenINTEL corpus does not export, "
            "so no verdict is possible in either direction."
        )
        parts.append(
            f"{_timestamp_sentence(timestamp_check, rfc.rfc_id)} "
            "This is a corpus limitation, not a statement about the observation."
        )
        return " ".join(parts)

    if decision in ("valid_match", "ambiguous") and primary is not None:
        role = "required" if primary.required else "optional"
        verb = "matched" if decision == "valid_match" else "is an ambiguous match for"
        parts.append(
            f"{rfc.rfc_id} {verb} {subject}: the {role} indicator "
            f"{primary.indicator_id} passed because {_matched_clause(primary)}."
        )
        others = [
            e
            for e in indicator_evals
            if e.matched and not e.skipped and e.indicator_id != primary.indicator_id
        ]
        if others:
            names = ", ".join(unique_sorted(e.indicator_id for e in others))
            parts.append(f"Corroborating indicators also matched: {names}.")
        unmatched = [
            e for e in indicator_evals if not e.matched and not e.skipped
        ]
        if unmatched:
            worst = sorted(unmatched, key=lambda e: (e.required is False, -e.weight))[0]
            parts.append(
                f"Indicator {worst.indicator_id} did not match: {_first_failure(worst)}."
            )
        if decision == "ambiguous":
            ambiguous_ids = ", ".join(
                unique_sorted(e.indicator_id for e in indicator_evals if e.matched and e.ambiguous)
            )
            parts.append(
                f"The checklist flags {ambiguous_ids} ambiguous: the same observation is "
                "equally explained by other RFCs, so the match is penalized and sent to "
                "the review queue rather than reported as adoption."
            )
        parts.append(_timestamp_sentence(timestamp_check, rfc.rfc_id))
        parts.append(_score_sentence(rfc, breakdown, confidence))
        return " ".join(parts)

    if decision == "partial_match":
        if primary is not None:
            role = "required" if primary.required else "optional"
            parts.append(
                f"{rfc.rfc_id} partially matches {subject}: the {role} indicator "
                f"{primary.indicator_id} passed because {_matched_clause(primary)}."
            )
        else:
            parts.append(f"{rfc.rfc_id} partially matches {subject}.")
        if failed_required is not None:
            parts.append(
                f"The required indicator {failed_required.indicator_id} was not "
                f"satisfied: {_first_failure(failed_required)}."
            )
            if failed_required.missing_fields:
                parts.append(
                    "That failure is an absence, not a contradiction: the observation "
                    f"carries no value for {_join(sorted(failed_required.missing_fields))}, "
                    "so this RFC can be neither confirmed nor ruled out here."
                )
        parts.append(_timestamp_sentence(timestamp_check, rfc.rfc_id))
        parts.append(_score_sentence(rfc, breakdown, confidence))
        return " ".join(parts)

    # no_match
    if failed_required is not None:
        parts.append(
            f"{rfc.rfc_id} does not explain {subject}: the required indicator "
            f"{failed_required.indicator_id} failed because "
            f"{_first_failure(failed_required)}."
        )
    else:
        parts.append(
            f"{rfc.rfc_id} does not explain {subject}: no indicator of this RFC matched "
            "the observation."
        )
    if skipped:
        names = ", ".join(unique_sorted(e.indicator_id for e in skipped))
        parts.append(
            f"Indicator(s) {names} were not tested at all (not exported by the corpus), "
            "so this rejection rests only on the indicators that could be evaluated."
        )
    parts.append(_timestamp_sentence(timestamp_check, rfc.rfc_id))
    parts.append(
        f"Score {_num(breakdown.final_score)} ({confidence}): no required indicator "
        "matched, so there is nothing to score."
    )
    return " ".join(parts)


def summarize_decision(
    rfc: RFCChecklistEntry,
    decision: Decision,
    indicator_evals: Sequence[IndicatorEvaluation],
    timestamp_check: TimestampCheck,
    breakdown: ScoreBreakdown,
) -> str:
    """Prose answering: which RFC, which indicator, which field, what passed,
    what failed, was the timestamp valid, and why is the score what it is."""
    return _compose_summary(
        rfc,
        decision,
        indicator_evals,
        timestamp_check,
        breakdown,
        subject="this observation",
        confidence=_confidence_for(breakdown.final_score),
    )


# --------------------------------------------------------------------------- #
# Uncertainty
# --------------------------------------------------------------------------- #


def _uncertainty_notes(
    decision: Decision,
    indicator_evals: Sequence[IndicatorEvaluation],
    timestamp_check: TimestampCheck,
) -> list[str]:
    """Everything that should stop a reader over-reading this trace.

    Four categories, per the build contract: partially-evaluated indicators,
    ambiguous indicators, fields missing from the observation, and
    corpus-availability caveats.
    """
    notes: list[str] = []

    for evaluation in indicator_evals:
        if evaluation.skipped:
            fields = ", ".join(evaluation.missing_fields) or "its fields"
            verb = "is" if len(evaluation.missing_fields) == 1 else "are"
            notes.append(
                f"Corpus availability: indicator {evaluation.indicator_id} was never "
                f"tested because {fields} {verb} absent from the OpenINTEL dictionary. "
                "Its absence from the evidence is a measurement limitation, not a "
                "finding about the observation."
            )
            continue
        if evaluation.queryability == "partially_queryable":
            notes.append(
                f"Indicator {evaluation.indicator_id} is only partially queryable: part "
                "of its signature depends on fields the corpus does not export, so it "
                "was evaluated on incomplete data."
            )
        tested = [c for c in evaluation.conditions if c.field_present]
        untestable = [c for c in evaluation.conditions if not c.field_present]
        if tested and untestable and not evaluation.matched:
            notes.append(
                f"Indicator {evaluation.indicator_id} was only partially evaluated: "
                f"{len(tested)} condition(s) were tested and {len(untestable)} could "
                "not be, because the observation carries no value for "
                f"{_join(sorted({c.field for c in untestable}))}."
            )
        if evaluation.ambiguous and evaluation.matched:
            notes.append(
                f"Indicator {evaluation.indicator_id} is flagged ambiguous: the "
                "observation it matched is equally consistent with other RFCs, so this "
                "result is an inference about policy rather than direct evidence."
            )

    missing = unique_sorted(f for e in indicator_evals for f in e.missing_fields if not e.skipped)
    if missing:
        notes.append(
            f"Fields absent from this observation: {', '.join(missing)}. Every condition "
            "over them failed by construction; absence is not evidence either way."
        )

    if not timestamp_check.valid:
        notes.append(
            "The observation predates the RFC publication date by "
            f"{abs(timestamp_check.days_after_publication)} days, so any score it would "
            "have earned is withheld and the case needs human review."
        )

    if decision == "partial_match":
        notes.append(
            "Partial matches are candidates, not adoption evidence: at least one "
            "required indicator of this RFC was not satisfied."
        )

    return _dedupe(notes)


# --------------------------------------------------------------------------- #
# Trace assembly
# --------------------------------------------------------------------------- #


def build_trace(
    *,
    signal: ObservedSignal,
    rfc: RFCChecklistEntry,
    decision: Decision,
    confidence: Confidence,
    indicator_evals: Sequence[IndicatorEvaluation],
    timestamp_check: TimestampCheck,
    breakdown: ScoreBreakdown,
) -> ReasoningTrace:
    """Assemble the full decision record for one signal x RFC evaluation.

    Condition evaluations are flattened across indicators so a reader can scan
    every predicate that was tested without walking the indicator tree, while
    the per-indicator explanations keep the grouping.
    """
    matched_conditions: list[ConditionEvaluation] = []
    failed_conditions: list[ConditionEvaluation] = []
    for evaluation in indicator_evals:
        for condition in evaluation.conditions:
            (matched_conditions if condition.passed else failed_conditions).append(condition)

    matched_ids = unique_sorted(
        e.indicator_id for e in indicator_evals if e.matched and not e.skipped
    )
    failed_ids = unique_sorted(
        e.indicator_id for e in indicator_evals if not e.matched and not e.skipped
    )
    skipped_ids = unique_sorted(e.indicator_id for e in indicator_evals if e.skipped)
    # "Missing required" means: required, actually evaluated, and not satisfied.
    # Required indicators that were skipped appear under skipped_indicator_ids
    # instead, because they were never given the chance to fail.
    missing_required_ids = unique_sorted(
        e.indicator_id for e in indicator_evals if e.required and not e.skipped and not e.matched
    )
    missing_fields = unique_sorted(f for e in indicator_evals for f in e.missing_fields)
    matched_fields = unique_sorted(c.field for c in matched_conditions)

    supporting_observation: dict[str, Any] = {
        "signal_id": signal.signal_id,
        "timestamp": iso(signal.timestamp),
        "domain": signal.domain,
        "zone": signal.zone,
        "source": signal.source,
        "measurement_id": signal.measurement_id,
        "fields": dict(signal.fields),
        "indicator_explanations": [explain_indicator(e) for e in indicator_evals],
    }

    summary = _compose_summary(
        rfc,
        decision,
        indicator_evals,
        timestamp_check,
        breakdown,
        subject=f"signal {signal.signal_id}",
        confidence=confidence,
    )

    return ReasoningTrace(
        trace_id=trace_id(signal.signal_id, rfc.rfc_id),
        signal_id=signal.signal_id,
        rfc_id=rfc.rfc_id,
        rfc_title=rfc.title,
        observation_timestamp=signal.timestamp,
        rfc_publication_date=rfc.publication_date,
        timestamp_valid=timestamp_check.valid,
        decision=decision,
        confidence=confidence,
        reasoning_summary=summary,
        matched_conditions=matched_conditions,
        failed_conditions=failed_conditions,
        matched_indicator_ids=matched_ids,
        failed_indicator_ids=failed_ids,
        skipped_indicator_ids=skipped_ids,
        missing_required_indicator_ids=missing_required_ids,
        missing_fields=missing_fields,
        matched_openintel_fields=matched_fields,
        timestamp_check=timestamp_check,
        score_breakdown=breakdown,
        supporting_observation=supporting_observation,
        uncertainty_notes=_uncertainty_notes(decision, indicator_evals, timestamp_check),
    )


def trace_to_row(trace: ReasoningTrace) -> dict[str, Any]:
    """Flatten a trace into one CSV row without dropping information.

    Lists become ``"; "``-joined cells and the condition evaluations become
    their explanation sentences, so the CSV stays readable in a spreadsheet
    while the JSON export keeps the structured form.
    """
    breakdown = trace.score_breakdown
    observation = trace.supporting_observation
    row: dict[str, Any] = {
        "trace_id": trace.trace_id,
        "signal_id": trace.signal_id,
        "rfc_id": trace.rfc_id,
        "rfc_title": trace.rfc_title,
        "domain": observation.get("domain"),
        "zone": observation.get("zone"),
        "observation_timestamp": iso(trace.observation_timestamp),
        "rfc_publication_date": iso(trace.rfc_publication_date),
        "timestamp_valid": trace.timestamp_valid,
        "days_after_publication": trace.timestamp_check.days_after_publication,
        "decision": trace.decision,
        "confidence": trace.confidence,
        "final_score": breakdown.final_score,
        "base_indicator_score": breakdown.base_indicator_score,
        "optional_match_bonus": breakdown.optional_match_bonus,
        "required_match_bonus": breakdown.required_match_bonus,
        "missing_required_penalty": breakdown.missing_required_penalty,
        "partial_match_penalty": breakdown.partial_match_penalty,
        "ambiguity_penalty": breakdown.ambiguity_penalty,
        "specificity_multiplier": breakdown.specificity_multiplier,
        "timestamp_penalty": breakdown.timestamp_penalty,
        "matched_indicator_ids": trace.matched_indicator_ids,
        "failed_indicator_ids": trace.failed_indicator_ids,
        "skipped_indicator_ids": trace.skipped_indicator_ids,
        "missing_required_indicator_ids": trace.missing_required_indicator_ids,
        "matched_openintel_fields": trace.matched_openintel_fields,
        "missing_fields": trace.missing_fields,
        "matched_condition_count": len(trace.matched_conditions),
        "failed_condition_count": len(trace.failed_conditions),
        "matched_conditions": [explain_condition(c) for c in trace.matched_conditions],
        "failed_conditions": [explain_condition(c) for c in trace.failed_conditions],
        "timestamp_explanation": trace.timestamp_check.explanation,
        "score_steps": breakdown.steps,
        "uncertainty_notes": trace.uncertainty_notes,
        "reasoning_summary": trace.reasoning_summary,
    }
    return {key: flatten_for_csv(value) for key, value in row.items()}
