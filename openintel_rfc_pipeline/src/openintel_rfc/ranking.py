"""Scoring, confidence banding and cross-signal candidate aggregation.

This module owns the arithmetic. It answers three questions and nothing else:

1. How much evidence does one signal x RFC evaluation carry (:func:`score_match`)?
2. What confidence band does a score fall in (:func:`confidence_for`)?
3. Rolled up over every signal, which RFCs are the best candidates
   (:func:`rank_candidates`) and which of them are too close to separate
   (:func:`close_ranking_pairs`)?

Every score is itemized into :class:`~openintel_rfc.models.ScoreBreakdown.steps`
as readable arithmetic. A reader who only has ``steps`` must be able to
recompute ``final_score`` by hand; that requirement is why each term gets its
own line including the terms that evaluated to zero.

This module is a leaf: it imports only ``models``, ``config`` and ``utils`` so
that ``matcher`` can depend on it without creating an import cycle.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from . import config
from .models import (
    CONFIDENCE_THRESHOLDS,
    Confidence,
    Decision,
    IndicatorEvaluation,
    RankedRFCCandidate,
    RFCChecklistDB,
    RFCChecklistEntry,
    RFCMatch,
    ScoreBreakdown,
    Specificity,
    TimestampCheck,
)
from .utils import format_value, round_score, unique_sorted

__all__ = [
    "score_match",
    "confidence_for",
    "rank_candidates",
    "close_ranking_pairs",
    "RANKABLE_DECISIONS",
]

#: Decisions that represent *some* positive evidence and may therefore be
#: aggregated into a ranked candidate. ``no_match`` carries none, and
#: ``timestamp_invalid`` / ``non_queryable`` carry evidence we are not allowed
#: to count (respectively: forfeited, and never tested).
RANKABLE_DECISIONS: tuple[Decision, ...] = ("valid_match", "ambiguous", "partial_match")

#: Strength ordering used when several signals disagree about one RFC.
_DECISION_STRENGTH: dict[str, int] = {"valid_match": 3, "ambiguous": 2, "partial_match": 1}

_ORDINALS: dict[int, str] = {
    1: "first",
    2: "second",
    3: "third",
    4: "fourth",
    5: "fifth",
    6: "sixth",
    7: "seventh",
    8: "eighth",
    9: "ninth",
    10: "tenth",
}


# --------------------------------------------------------------------------- #
# Small formatting helpers
# --------------------------------------------------------------------------- #


def _num(value: float) -> str:
    """Render a score term compactly but without losing precision.

    ``10.0`` -> ``"10.0"``, ``17.25`` -> ``"17.25"``. Deliberately not ``repr``:
    the arithmetic in ``steps`` has to read like arithmetic.
    """
    text = f"{round_score(float(value)):.4f}".rstrip("0")
    return text + "0" if text.endswith(".") else text


def _id_list(evaluations: Sequence[IndicatorEvaluation]) -> str:
    if not evaluations:
        return "none"
    return ", ".join(unique_sorted(e.indicator_id for e in evaluations))


def _ordinal(rank: int) -> str:
    return _ORDINALS.get(rank, f"#{rank}")


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


# --------------------------------------------------------------------------- #
# Per-evaluation scoring and decision
# --------------------------------------------------------------------------- #


def _partition(
    indicator_evals: Sequence[IndicatorEvaluation],
) -> tuple[
    list[IndicatorEvaluation],
    list[IndicatorEvaluation],
    list[IndicatorEvaluation],
    list[IndicatorEvaluation],
    list[IndicatorEvaluation],
]:
    """Split evaluations into the groups the formula and decision rules need.

    Returns ``(evaluable_required, matched_required, unmatched_required,
    matched_optional, skipped)``. Skipped (non-queryable) indicators are held
    out of every other group on purpose: we never got to test them, so they may
    neither earn weight nor incur a penalty.
    """
    skipped = [e for e in indicator_evals if e.skipped]
    evaluable_required = [e for e in indicator_evals if e.required and not e.skipped]
    matched_required = [e for e in evaluable_required if e.matched]
    unmatched_required = [e for e in evaluable_required if not e.matched]
    matched_optional = [
        e for e in indicator_evals if not e.required and not e.skipped and e.matched
    ]
    return evaluable_required, matched_required, unmatched_required, matched_optional, skipped


def _has_untestable_partial_evidence(
    unmatched_required: Sequence[IndicatorEvaluation],
) -> bool:
    """True when a required indicator was *partly* satisfied and partly untestable.

    A required indicator whose observed fields agree with it as far as they go,
    but whose remaining conditions could not be tested because the observation
    does not carry the field, is weaker than a contradiction: nothing about the
    observation rules the RFC out. The contract's worked example 8 (a CDS record
    with a null ``algorithm``) is exactly this case and must land on
    ``partial_match`` rather than ``no_match``, so the review queue picks it up.

    An indicator where *nothing* was testable is not partial evidence, it is no
    evidence, and stays a ``no_match``.
    """
    for evaluation in unmatched_required:
        passed = [c for c in evaluation.conditions if c.passed]
        untestable = [c for c in evaluation.conditions if not c.field_present]
        if passed and untestable:
            return True
    return False


def _decide_on_evidence(
    rfc: RFCChecklistEntry, indicator_evals: Sequence[IndicatorEvaluation]
) -> Decision:
    """Apply the decision rules to the evidence, ignoring the timestamp."""
    (
        evaluable_required,
        matched_required,
        unmatched_required,
        matched_optional,
        _skipped,
    ) = _partition(indicator_evals)

    if rfc.required_indicators and not evaluable_required:
        # Every required indicator depends on a field the corpus does not
        # export: no verdict is possible, and pretending otherwise would report
        # a corpus limitation as an operator's behaviour.
        return "non_queryable"

    matched_any = matched_required + matched_optional

    if evaluable_required and not unmatched_required:
        if any(e.ambiguous for e in matched_any):
            return "ambiguous"
        return "valid_match"

    if matched_required:  # 0 < len(M_req) < len(R)
        return "partial_match"

    if matched_optional:  # nothing required matched, but corroboration exists
        return "partial_match"

    if _has_untestable_partial_evidence(unmatched_required):
        return "partial_match"

    return "no_match"


def score_match(
    rfc: RFCChecklistEntry,
    indicator_evals: Sequence[IndicatorEvaluation],
    timestamp_check: TimestampCheck,
) -> tuple[ScoreBreakdown, Decision]:
    """Score one signal x RFC evaluation and decide what it means.

    The score and the decision are returned together because they are two
    readings of the same evidence set; computing them apart would let them drift.

    The formula is the one in the build contract::

        raw   = base + required_match_bonus + optional_match_bonus
                - missing_required_penalty - partial_match_penalty
                - ambiguity_penalty
        final = round(max(0, raw) * specificity_multiplier)

    When the observation predates the RFC, the whole score is forfeited: an
    observation cannot evidence adoption of a document that did not exist yet.
    The forfeited amount is preserved in ``timestamp_penalty`` so a reviewer can
    see exactly what was withheld, and the decision becomes ``timestamp_invalid``.
    The forfeit is applied only where there was something to forfeit: an
    evaluation that fails on the evidence alone stays a ``no_match``, because
    calling it ``timestamp_invalid`` would imply the date was the deciding
    factor when it was not.
    """
    (
        evaluable_required,
        matched_required,
        unmatched_required,
        matched_optional,
        skipped,
    ) = _partition(indicator_evals)
    matched_any = matched_required + matched_optional

    base = float(sum(e.weight for e in matched_required))
    optional_weight = float(sum(e.weight for e in matched_optional))
    optional_bonus = optional_weight * config.OPTIONAL_WEIGHT_FACTOR

    all_required_matched = bool(evaluable_required) and not unmatched_required
    required_bonus = (
        config.REQUIRED_MATCH_BONUS
        if all_required_matched and len(evaluable_required) >= config.MIN_REQUIRED_FOR_BONUS
        else 0.0
    )
    missing_required_penalty = config.MISSING_REQUIRED_PENALTY * len(unmatched_required)
    partial_match_penalty = (
        config.PARTIAL_MATCH_PENALTY if matched_required and unmatched_required else 0.0
    )
    ambiguity_penalty = (
        config.AMBIGUITY_PENALTY if any(e.ambiguous for e in matched_any) else 0.0
    )

    raw = (
        base
        + required_bonus
        + optional_bonus
        - missing_required_penalty
        - partial_match_penalty
        - ambiguity_penalty
    )
    multiplier = rfc.specificity_multiplier
    final_score = round_score(max(0.0, raw) * multiplier)

    decision = _decide_on_evidence(rfc, indicator_evals)

    steps: list[str] = [
        f"base_indicator_score = {_num(base)} "
        f"(matched required indicators: {_id_list(matched_required)})",
        f"optional_match_bonus = {_num(optional_bonus)} = {_num(optional_weight)} x "
        f"{_num(config.OPTIONAL_WEIGHT_FACTOR)} "
        f"(matched optional indicators: {_id_list(matched_optional)})",
        f"required_match_bonus = {_num(required_bonus)} "
        f"({_required_bonus_reason(evaluable_required, all_required_matched)})",
        f"missing_required_penalty = {_num(missing_required_penalty)} = "
        f"{_num(config.MISSING_REQUIRED_PENALTY)} x {len(unmatched_required)} "
        f"(required indicators evaluated but not matched: {_id_list(unmatched_required)})",
        f"partial_match_penalty = {_num(partial_match_penalty)} "
        f"({_partial_penalty_reason(matched_required, unmatched_required)})",
        f"ambiguity_penalty = {_num(ambiguity_penalty)} "
        f"({_ambiguity_reason(matched_any)})",
        f"raw = {_num(base)} + {_num(required_bonus)} + {_num(optional_bonus)} - "
        f"{_num(missing_required_penalty)} - {_num(partial_match_penalty)} - "
        f"{_num(ambiguity_penalty)} = {_num(raw)}",
        f"specificity_multiplier = {_num(multiplier)} "
        f"({rfc.rfc_id} specificity={rfc.specificity})",
        f"final_score = max(0, {_num(raw)}) * {_num(multiplier)} = {_num(final_score)}",
    ]

    timestamp_penalty = 0.0
    if not timestamp_check.valid and decision in RANKABLE_DECISIONS:
        timestamp_penalty = final_score
        final_score = 0.0
        decision = "timestamp_invalid"
        steps.append(
            f"timestamp_penalty = {_num(timestamp_penalty)} "
            f"(the observation predates {rfc.rfc_id}'s publication date by "
            f"{abs(timestamp_check.days_after_publication)} days, so the score is withheld)"
        )
        steps.append(
            "final_score = 0.0 (timestamp_invalid: an observation cannot evidence "
            "adoption of an RFC that did not yet exist)"
        )

    if skipped:
        verb = "was" if len(skipped) == 1 else "were"
        steps.append(
            "note: "
            + _plural(len(skipped), "indicator")
            + f" ({_id_list(skipped)}) could not be tested against the OpenINTEL "
            f"corpus and {verb} excluded from every term above, neither earning "
            "weight nor incurring a penalty"
        )

    breakdown = ScoreBreakdown(
        base_indicator_score=round_score(base),
        specificity_multiplier=multiplier,
        required_match_bonus=round_score(required_bonus),
        optional_match_bonus=round_score(optional_bonus),
        missing_required_penalty=round_score(missing_required_penalty),
        partial_match_penalty=round_score(partial_match_penalty),
        ambiguity_penalty=round_score(ambiguity_penalty),
        timestamp_penalty=round_score(timestamp_penalty),
        final_score=round_score(final_score),
        steps=steps,
    )
    return breakdown, decision


def _required_bonus_reason(
    evaluable_required: Sequence[IndicatorEvaluation], all_matched: bool
) -> str:
    count = len(evaluable_required)
    if count < config.MIN_REQUIRED_FOR_BONUS:
        return (
            f"not awarded: {count} evaluable required indicator(s), the bonus needs "
            f"at least {config.MIN_REQUIRED_FOR_BONUS}"
        )
    if not all_matched:
        return f"not awarded: only some of the {count} required indicators matched"
    return f"awarded: all {count} required indicators matched"


def _partial_penalty_reason(
    matched_required: Sequence[IndicatorEvaluation],
    unmatched_required: Sequence[IndicatorEvaluation],
) -> str:
    if matched_required and unmatched_required:
        return (
            f"applied: {len(matched_required)} of "
            f"{len(matched_required) + len(unmatched_required)} required indicators matched"
        )
    if not matched_required:
        return "not applied: no required indicator matched, so this is not a partial match"
    return "not applied: every evaluable required indicator matched"


def _ambiguity_reason(matched_any: Sequence[IndicatorEvaluation]) -> str:
    ambiguous = [e for e in matched_any if e.ambiguous]
    if ambiguous:
        return f"applied: matched indicators flagged ambiguous: {_id_list(ambiguous)}"
    return "not applied: no matched indicator is flagged ambiguous"


def confidence_for(score: float) -> Confidence:
    """Map a final score onto its confidence band (``models.CONFIDENCE_THRESHOLDS``)."""
    for threshold, label in CONFIDENCE_THRESHOLDS:
        if score >= threshold:
            return cast(Confidence, label)
    return "none"


# --------------------------------------------------------------------------- #
# Aggregation across signals
# --------------------------------------------------------------------------- #


def _evidence_phrase(match: RFCMatch) -> str:
    """Name the strongest matched indicator of a match and what it observed."""
    matched = [e for e in match.indicator_evaluations if e.matched and not e.skipped]
    if not matched:
        return (
            "partial evidence only: no indicator matched in full "
            f"(missing fields: {', '.join(match.missing_fields) or 'none'})"
        )
    # Required indicators carry the RFC; among equals prefer the heaviest, then
    # the lowest id so the phrase is stable across runs.
    primary = sorted(matched, key=lambda e: (not e.required, -e.weight, e.indicator_id))[0]
    observed = list(
        dict.fromkeys(
            f"{c.field}={format_value(c.observed)}" for c in primary.conditions if c.passed
        )
    )
    if not observed:
        return f"indicator {primary.indicator_id}"
    return f"indicator {primary.indicator_id} matching {' and '.join(observed)}"


def _candidate_summary(candidate: RankedRFCCandidate, best: RFCMatch) -> str:
    """One sentence naming the best evidence behind a ranked candidate."""
    sentence = (
        f"{candidate.rfc_id} ranks {_ordinal(candidate.rank)} "
        f"(score {_num(candidate.score)}, {candidate.confidence}) on "
        f"{_plural(candidate.supporting_signal_count, 'supporting observation')}; "
        f"strongest evidence is {_evidence_phrase(best)}."
    )
    if candidate.decision == "ambiguous":
        sentence += (
            " The verdict is ambiguous: at least one matched indicator is not "
            "uniquely attributable to this RFC, so it is routed to the review queue."
        )
    elif candidate.decision == "partial_match":
        sentence += (
            " No observation satisfied every required indicator, so this is "
            "partial evidence only."
        )
    withheld = candidate.timestamp_invalid_count
    if withheld == 1:
        sentence += (
            " A further observation matched the indicators but was withheld from the "
            "score because it predates the RFC's publication date."
        )
    elif withheld > 1:
        sentence += (
            f" A further {withheld} observations matched the indicators but were "
            "withheld from the score because they predate the RFC's publication date."
        )
    return sentence


def _entry_for(db: RFCChecklistDB, match: RFCMatch) -> tuple[Specificity, str]:
    """Specificity and title for an RFC, tolerating a checklist/match mismatch."""
    entry = db.get(match.rfc_id)
    if entry is None:
        # Ranking must not crash because a match came from a different checklist
        # revision; 'medium' (multiplier 1.0) is the neutral assumption and the
        # per-match breakdown still records the multiplier that was applied.
        return "medium", match.rfc_title
    return entry.specificity, entry.title


def rank_candidates(
    matches: Sequence[RFCMatch],
    db: RFCChecklistDB,
    *,
    min_score: float = 0.0,
) -> list[RankedRFCCandidate]:
    """Aggregate per-signal matches into one ranked candidate per RFC.

    ``score`` is the best single observation (max), because adoption evidence is
    established by the strongest observation, not by repetition;
    ``aggregate_score`` is the sum and is a volume measure only.

    ``no_match`` evaluations are dropped entirely. ``timestamp_invalid`` ones
    are counted in ``timestamp_invalid_count`` but contribute nothing to the
    score, to ``first_seen``/``last_seen``, or to the evidence lists — so an RFC
    whose only evidence predates it never surfaces as a ranked candidate. The
    review queue is where those cases are surfaced instead.

    Candidates scoring at or below ``min_score`` (floored at
    ``config.MIN_RANKABLE_SCORE``) are not emitted: a zero score is not evidence.
    """
    threshold = max(float(min_score), config.MIN_RANKABLE_SCORE)

    grouped: dict[str, list[RFCMatch]] = {}
    for match in matches:
        grouped.setdefault(match.rfc_id, []).append(match)

    candidates: list[RankedRFCCandidate] = []
    best_matches: dict[str, RFCMatch] = {}

    for rfc_id in sorted(grouped):
        group = grouped[rfc_id]
        rankable = [m for m in group if m.decision in RANKABLE_DECISIONS]
        if not rankable:
            continue

        score = round_score(max(m.score for m in rankable))
        if score <= threshold:
            continue

        best = sorted(rankable, key=lambda m: (-m.score, m.signal_id))[0]
        best_matches[rfc_id] = best

        valid = [m for m in rankable if m.decision == "valid_match"]
        partial = [m for m in rankable if m.decision == "partial_match"]
        invalid = [m for m in group if m.decision == "timestamp_invalid"]
        by_signal = sorted(rankable, key=lambda m: m.signal_id)
        examples = by_signal[:5]

        specificity, title = _entry_for(db, best)
        decision = cast(
            Decision,
            max((m.decision for m in rankable), key=lambda d: _DECISION_STRENGTH[d]),
        )

        candidates.append(
            RankedRFCCandidate(
                rank=0,  # assigned after the whole list is sorted
                rfc_id=rfc_id,
                rfc_title=title,
                specificity=specificity,
                rfc_publication_date=best.rfc_publication_date,
                decision=decision,
                score=score,
                aggregate_score=round_score(sum(m.score for m in rankable)),
                confidence=confidence_for(score),
                supporting_signal_count=len(rankable),
                valid_match_count=len(valid),
                partial_match_count=len(partial),
                timestamp_invalid_count=len(invalid),
                first_seen=min((m.observation_timestamp for m in valid), default=None),
                last_seen=max((m.observation_timestamp for m in valid), default=None),
                matched_indicator_ids=unique_sorted(
                    i for m in rankable for i in m.matched_indicator_ids
                ),
                matched_fields=unique_sorted(f for m in rankable for f in m.matched_fields),
                domains=unique_sorted(m.domain for m in rankable),
                zones=unique_sorted(m.zone for m in rankable),
                example_signal_ids=[m.signal_id for m in examples],
                example_trace_ids=[m.trace_id for m in examples],
                reasoning_summary="",
                score_breakdown=best.score_breakdown,
            )
        )

    candidates.sort(key=lambda c: (-c.score, -c.supporting_signal_count, c.rfc_id))
    for index, candidate in enumerate(candidates, start=1):
        candidate.rank = index
        candidate.reasoning_summary = _candidate_summary(
            candidate, best_matches[candidate.rfc_id]
        )
    return candidates


def close_ranking_pairs(
    candidates: Sequence[RankedRFCCandidate],
    tolerance: float = config.CLOSE_RANKING_RELATIVE_TOLERANCE,
) -> list[tuple[RankedRFCCandidate, RankedRFCCandidate]]:
    """Adjacent ranked pairs that are too close to separate.

    Two neighbours whose scores differ by no more than ``tolerance`` of the
    higher score are reported so the review queue can say "these two are not
    distinguishable by this evidence" instead of implying the ordering is
    meaningful. Partial matches are excluded: they are already flagged as
    incomplete evidence, so a near-tie between them says nothing extra.
    """
    ordered = sorted(candidates, key=lambda c: (c.rank, c.rfc_id))
    pairs: list[tuple[RankedRFCCandidate, RankedRFCCandidate]] = []
    for higher, lower in zip(ordered, ordered[1:]):
        if higher.decision == "partial_match" or lower.decision == "partial_match":
            continue
        if higher.score <= 0.0:
            continue
        if (higher.score - lower.score) <= tolerance * higher.score:
            pairs.append((higher, lower))
    return pairs
