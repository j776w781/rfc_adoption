"""Condition and indicator evaluation, timestamp cutoff, and the match loop.

This is where an observation meets a checklist. The module evaluates every
condition of every indicator of every RFC against every signal — it never picks
one RFC up front, and one signal is allowed to evidence several RFCs at once
(a CDS record with ``algorithm=0`` really is both an RFC 7344 record type and
an RFC 8078 delete signal; the ranking, not the matcher, says which explains it
better).

Two rules shape everything here:

* **Absence is not evidence.** A field the observation does not carry fails
  every operator, is recorded in ``missing_fields``, and is reported as
  untested rather than as a contradiction.
* **Untestable is not failed.** An indicator the corpus cannot answer at all is
  skipped, and a skipped indicator never penalizes its RFC. Reporting a corpus
  limitation as an operator's non-conformance would be the easiest way for this
  pipeline to lie.

Depends on ``ranking`` (scores and decisions) and ``reasoning`` (explanations);
both are leaves, so the dependency direction stays acyclic.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .models import (
    ConditionEvaluation,
    IndicatorCondition,
    IndicatorEvaluation,
    ObservedSignal,
    Queryability,
    ReasoningTrace,
    RFCChecklistDB,
    RFCChecklistEntry,
    RFCIndicator,
    RFCMatch,
    SchemaCheckReport,
    TimestampCheck,
)
from .ranking import confidence_for, score_match
from .reasoning import build_trace, explain_condition, explain_indicator, explain_timestamp
from .utils import format_value, get_logger, normalize_timestamp, trace_id, unique_sorted, warn

__all__ = [
    "evaluate_condition",
    "evaluate_indicator",
    "check_timestamp",
    "match_signal_to_rfc",
    "match_all",
]

LOGGER = get_logger("openintel_rfc.matcher")


# --------------------------------------------------------------------------- #
# Value comparison
# --------------------------------------------------------------------------- #


def _as_number(value: Any) -> float | None:
    """Coerce numbers and numeric strings to float; return None if impossible.

    Booleans are deliberately rejected: Python treats ``True == 1``, and a DNS
    algorithm number 0 must never compare equal to a boolean ``False``.
    """
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _values_equal(observed: Any, expected: Any) -> bool:
    """Equality that tolerates Parquet's string/number ambiguity.

    ``"13" == 13`` is treated as equal because the same OpenINTEL column can be
    exported as either, but ``0 == False`` is not: those are different claims.
    """
    if isinstance(observed, bool) or isinstance(expected, bool):
        return isinstance(observed, bool) and isinstance(expected, bool) and observed == expected
    if observed == expected:
        return True
    left, right = _as_number(observed), _as_number(expected)
    return left is not None and right is not None and left == right


def _apply_operator(
    op: str, field: str, observed: Any, expected: Any
) -> tuple[bool, str]:
    """Apply one operator to a present observed value.

    Returns ``(passed, explanation_override)``. The override is empty for the
    ordinary pass/fail cases — :func:`reasoning.explain_condition` renders those
    from the evaluation itself — and carries a message for the cases the raw
    values cannot express, such as a type mismatch or a malformed condition.
    """
    if op == "exists":
        return True, ""  # a None value never reaches here
    if op == "equals":
        return _values_equal(observed, expected), ""
    if op == "not_equals":
        return not _values_equal(observed, expected), ""
    if op == "in":
        if not isinstance(expected, (list, tuple, set, frozenset)):
            return False, (
                f"condition is malformed: operator 'in' needs a list of expected values "
                f"for '{field}' but the checklist supplies {format_value(expected)}, so "
                "the condition cannot be satisfied"
            )
        return any(_values_equal(observed, item) for item in expected), ""
    if op == "contains":
        if isinstance(observed, str):
            return (expected is not None and str(expected) in observed), ""
        if isinstance(observed, (list, tuple, set, frozenset)):
            return any(_values_equal(item, expected) for item in observed), ""
        return False, (
            f"{field}={format_value(observed)} has type "
            f"{type(observed).__name__}, which has no membership or substring "
            f"relation to {format_value(expected)}, so 'contains' fails on a type "
            "mismatch rather than on the value"
        )
    if op in ("greater_or_equal", "less_or_equal"):
        left, right = _as_number(observed), _as_number(expected)
        if left is None or right is None:
            symbol = ">=" if op == "greater_or_equal" else "<="
            return False, (
                f"{field}={format_value(observed)} cannot be compared numerically with "
                f"{format_value(expected)} using {symbol} (type mismatch), so the "
                "condition fails"
            )
        return (left >= right if op == "greater_or_equal" else left <= right), ""
    return False, (
        f"unsupported operator '{op}' on field '{field}'; the condition is treated as "
        "failed rather than silently ignored"
    )


# --------------------------------------------------------------------------- #
# Condition / indicator evaluation
# --------------------------------------------------------------------------- #


def evaluate_condition(
    condition: IndicatorCondition, signal: ObservedSignal
) -> ConditionEvaluation:
    """Evaluate one condition against one observation.

    A missing (or null) observed value fails every operator, including
    ``not_equals``: we cannot claim a field differs from a value when we never
    saw the field. The evaluation records ``field_present=False`` so downstream
    consumers can tell "contradicted" from "not observed".
    """
    observed = signal.value(condition.field)
    present = observed is not None

    if present:
        passed, override = _apply_operator(
            condition.op, condition.field, observed, condition.value
        )
    else:
        passed, override = False, ""

    evaluation = ConditionEvaluation(
        field=condition.field,
        op=condition.op,
        expected=condition.value,
        observed=observed,
        passed=passed,
        field_present=present,
        explanation=override,
    )
    evaluation.explanation = explain_condition(evaluation)
    return evaluation


def evaluate_indicator(
    indicator: RFCIndicator,
    signal: ObservedSignal,
    queryability: Queryability = "queryable",
) -> IndicatorEvaluation:
    """Evaluate one indicator (its conditions ANDed) against one observation.

    ``queryability`` comes from the schema cross-check:

    * ``non_queryable`` — the corpus cannot answer this indicator at all. It is
      marked ``skipped``, no condition is evaluated, and scoring ignores it in
      both directions.
    * ``partially_queryable`` — evaluated normally; its untestable conditions
      simply fail on ``field_present=False``, which is the honest result and is
      surfaced in the trace's uncertainty notes.
    * ``queryable`` / ``ambiguous`` — evaluated normally.
    """
    if queryability == "non_queryable":
        evaluation = IndicatorEvaluation(
            indicator_id=indicator.id,
            indicator_description=indicator.description,
            required=indicator.required,
            weight=indicator.weight,
            ambiguous=indicator.ambiguous,
            queryability=queryability,
            matched=False,
            skipped=True,
            conditions=[],
            missing_fields=unique_sorted(indicator.fields_used),
            explanation="",
        )
        evaluation.explanation = explain_indicator(evaluation)
        return evaluation

    conditions = [evaluate_condition(c, signal) for c in indicator.conditions]
    evaluation = IndicatorEvaluation(
        indicator_id=indicator.id,
        indicator_description=indicator.description,
        required=indicator.required,
        weight=indicator.weight,
        ambiguous=indicator.ambiguous,
        queryability=queryability,
        matched=all(c.passed for c in conditions),
        skipped=False,
        conditions=conditions,
        missing_fields=unique_sorted(c.field for c in conditions if not c.field_present),
        explanation="",
    )
    evaluation.explanation = explain_indicator(evaluation)
    return evaluation


# --------------------------------------------------------------------------- #
# Timestamp cutoff
# --------------------------------------------------------------------------- #


def check_timestamp(signal: ObservedSignal, rfc: RFCChecklistEntry) -> TimestampCheck:
    """Compare an observation date with an RFC publication date.

    This is the single check that separates "these bytes look like RFC 8078"
    from "this is evidence of RFC 8078 adoption".
    """
    observed = normalize_timestamp(signal.timestamp)
    published = normalize_timestamp(rfc.publication_date)
    days = (observed - published).days
    check = TimestampCheck(
        observation_timestamp=observed,
        rfc_publication_date=published,
        valid=observed >= published,
        days_after_publication=days,
        explanation="",
    )
    check.explanation = explain_timestamp(check)
    return check


# --------------------------------------------------------------------------- #
# Matching
# --------------------------------------------------------------------------- #


def _queryability_for(
    indicator: RFCIndicator,
    schema_report: SchemaCheckReport | None,
    warnings: list[str] | None,
) -> Queryability:
    if schema_report is None:
        return "queryable"
    status = schema_report.status_for(indicator.id)
    if status is None:
        if warnings is not None:
            warn(
                warnings,
                f"Indicator {indicator.id} is absent from the schema report; it was "
                "evaluated as queryable, which may over-state what the corpus can answer.",
                LOGGER,
            )
        return "queryable"
    return status


def match_signal_to_rfc(
    signal: ObservedSignal,
    rfc: RFCChecklistEntry,
    schema_report: SchemaCheckReport | None = None,
    *,
    warnings: list[str] | None = None,
) -> tuple[RFCMatch, ReasoningTrace]:
    """Evaluate one signal against one RFC and return the match and its trace.

    The trace is produced for every decision, ``no_match`` included: explaining
    why an RFC was rejected is as much of an output as explaining why one
    matched.
    """
    indicator_evals = [
        evaluate_indicator(
            indicator, signal, _queryability_for(indicator, schema_report, warnings)
        )
        for indicator in rfc.indicators
    ]
    timestamp_check = check_timestamp(signal, rfc)
    breakdown, decision = score_match(rfc, indicator_evals, timestamp_check)
    confidence = confidence_for(breakdown.final_score)

    trace = build_trace(
        signal=signal,
        rfc=rfc,
        decision=decision,
        confidence=confidence,
        indicator_evals=indicator_evals,
        timestamp_check=timestamp_check,
        breakdown=breakdown,
    )

    match = RFCMatch(
        signal_id=signal.signal_id,
        rfc_id=rfc.rfc_id,
        rfc_title=rfc.title,
        decision=decision,
        score=breakdown.final_score,
        confidence=confidence,
        timestamp_valid=timestamp_check.valid,
        observation_timestamp=timestamp_check.observation_timestamp,
        rfc_publication_date=timestamp_check.rfc_publication_date,
        domain=signal.domain,
        zone=signal.zone,
        matched_indicator_ids=trace.matched_indicator_ids,
        failed_indicator_ids=trace.failed_indicator_ids,
        missing_fields=trace.missing_fields,
        matched_fields=trace.matched_openintel_fields,
        indicator_evaluations=indicator_evals,
        score_breakdown=breakdown,
        trace_id=trace_id(signal.signal_id, rfc.rfc_id),
        reasoning_summary=trace.reasoning_summary,
    )
    return match, trace


def match_all(
    signals: Sequence[ObservedSignal],
    db: RFCChecklistDB,
    schema_report: SchemaCheckReport | None = None,
    *,
    warnings: list[str] | None = None,
) -> tuple[list[RFCMatch], list[ReasoningTrace]]:
    """Compare every signal against every RFC in the checklist database.

    Returns ``(matches, traces)`` with the traces in the same order as the
    matches, sorted by ``(signal_id, -score, rfc_id)`` so that each signal's
    best explanation reads first and repeated runs are byte-identical.
    """
    collected: list[str] = [] if warnings is None else warnings

    if not db.rfcs:
        warn(collected, "The checklist database contains no RFCs; nothing to match against.", LOGGER)
        return [], []
    if not signals:
        warn(collected, "No observed signals were supplied; no matches were produced.", LOGGER)
        return [], []

    pairs: list[tuple[RFCMatch, ReasoningTrace]] = []
    for signal in signals:
        for rfc in db.rfcs:
            pairs.append(match_signal_to_rfc(signal, rfc, schema_report, warnings=collected))

    pairs.sort(key=lambda pair: (pair[0].signal_id, -pair[0].score, pair[0].rfc_id))
    return [match for match, _ in pairs], [trace for _, trace in pairs]
