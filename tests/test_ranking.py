"""The scoring arithmetic, the confidence bands and cross-signal aggregation.

The exact scores asserted here come from the build contract's worked
expectations. They are checked numerically rather than by ordering alone,
because an ordering test passes just as happily when every weight has drifted by
the same factor.

``ScoreBreakdown.steps`` is checked as arithmetic, not as prose: a reader who has
only those lines must be able to recompute ``final_score`` by hand, and that is
exactly what ``score_step_terms`` does.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from openintel_rfc import config
from openintel_rfc.matcher import match_all, match_signal_to_rfc
from openintel_rfc.models import (
    SPECIFICITY_MULTIPLIERS,
    RankedRFCCandidate,
    RFCMatch,
    ScoreBreakdown,
)
from openintel_rfc.ranking import (
    ADOPTION_DECISIONS,
    close_ranking_pairs,
    confidence_for,
    rank_candidates,
)

#: (rfc_id, observation kwargs, expected score, expected confidence, expected decision).
#: These are the build contract's worked expectations, verbatim.
WORKED_EXPECTATIONS = [
    (
        "RFC 8078",
        {"timestamp": "2018-05-01", "rr_type": "CDS", "algorithm": 0, "digest_type": 0},
        17.25,
        "very_high",
        "valid_match",
    ),
    (
        "RFC 7344",
        {"timestamp": "2018-05-01", "rr_type": "CDS", "algorithm": 0, "digest_type": 0},
        11.25,
        "high",
        "valid_match",
    ),
    (
        "RFC 5155",
        {"timestamp": "2010-06-15", "rr_type": "NSEC3", "algorithm": 1},
        17.25,
        "very_high",
        "valid_match",
    ),
    (
        "RFC 4509",
        {"timestamp": "2012-03-14", "rr_type": "DS", "algorithm": 8, "digest_type": 2},
        11.25,
        "high",
        "valid_match",
    ),
    (
        "RFC 6605",
        {"timestamp": "2018-09-04", "rr_type": "DNSKEY", "algorithm": 13},
        13.125,
        "very_high",
        "valid_match",
    ),
    (
        "RFC 8624",
        {"timestamp": "2020-01-01", "rr_type": "DNSKEY", "algorithm": 13},
        3.375,
        "low",
        "ambiguous",
    ),
]

WORKED_IDS = [f"{rfc}-{score}" for rfc, _, score, _, _ in WORKED_EXPECTATIONS]


def _evaluate(signal_factory, checklist_db, schema_report, rfc_id: str, observation: dict):
    kwargs = dict(observation)
    timestamp = kwargs.pop("timestamp")
    rfc = checklist_db.get(rfc_id)
    assert rfc is not None, f"{rfc_id} is missing from the checklist database"
    return match_signal_to_rfc(signal_factory(timestamp, **kwargs), rfc, schema_report)


# --------------------------------------------------------------------------- #
# Exact scores
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("rfc_id", "observation", "expected_score", "expected_confidence", "expected_decision"),
    WORKED_EXPECTATIONS,
    ids=WORKED_IDS,
)
def test_worked_expectation_scores_are_exact(
    signal_factory,
    checklist_db,
    schema_report,
    rfc_id: str,
    observation: dict,
    expected_score: float,
    expected_confidence: str,
    expected_decision: str,
) -> None:
    match, _ = _evaluate(signal_factory, checklist_db, schema_report, rfc_id, observation)

    assert match.score == pytest.approx(expected_score)
    assert match.score_breakdown.final_score == pytest.approx(expected_score)
    assert match.confidence == expected_confidence
    assert match.decision == expected_decision


@pytest.mark.parametrize(
    ("rfc_id", "observation", "expected_score", "_confidence", "_decision"),
    WORKED_EXPECTATIONS,
    ids=WORKED_IDS,
)
def test_score_steps_reconstruct_the_final_score(
    signal_factory,
    checklist_db,
    schema_report,
    score_step_terms,
    rfc_id: str,
    observation: dict,
    expected_score: float,
    _confidence: str,
    _decision: str,
) -> None:
    match, _ = _evaluate(signal_factory, checklist_db, schema_report, rfc_id, observation)
    breakdown = match.score_breakdown
    terms = score_step_terms(breakdown)

    # Every term of the formula gets its own line, including the zero ones.
    for name in (
        "base_indicator_score",
        "optional_match_bonus",
        "required_match_bonus",
        "missing_required_penalty",
        "partial_match_penalty",
        "ambiguity_penalty",
        "specificity_multiplier",
        "raw",
        "final_score",
    ):
        assert name in terms, f"score step {name!r} is missing from the breakdown"

    # The steps must agree with the structured fields...
    assert terms["base_indicator_score"] == pytest.approx(breakdown.base_indicator_score)
    assert terms["optional_match_bonus"] == pytest.approx(breakdown.optional_match_bonus)
    assert terms["required_match_bonus"] == pytest.approx(breakdown.required_match_bonus)
    assert terms["missing_required_penalty"] == pytest.approx(
        breakdown.missing_required_penalty
    )
    assert terms["partial_match_penalty"] == pytest.approx(breakdown.partial_match_penalty)
    assert terms["ambiguity_penalty"] == pytest.approx(breakdown.ambiguity_penalty)
    assert terms["specificity_multiplier"] == pytest.approx(breakdown.specificity_multiplier)

    # ...and the arithmetic in them must reproduce the answer.
    raw = (
        terms["base_indicator_score"]
        + terms["required_match_bonus"]
        + terms["optional_match_bonus"]
        - terms["missing_required_penalty"]
        - terms["partial_match_penalty"]
        - terms["ambiguity_penalty"]
    )
    assert raw == pytest.approx(terms["raw"])
    assert max(0.0, raw) * terms["specificity_multiplier"] == pytest.approx(expected_score)
    assert terms["final_score"] == pytest.approx(expected_score)


def test_the_specificity_multiplier_used_is_the_one_the_checklist_declares(
    signal_factory, checklist_db, schema_report
) -> None:
    for rfc_id, observation, _score, _confidence, _decision in WORKED_EXPECTATIONS:
        match, _ = _evaluate(signal_factory, checklist_db, schema_report, rfc_id, observation)
        rfc = checklist_db.get(rfc_id)
        assert rfc is not None
        assert match.score_breakdown.specificity_multiplier == pytest.approx(
            SPECIFICITY_MULTIPLIERS[rfc.specificity]
        )


def test_the_ambiguity_penalty_is_what_costs_rfc8624_its_score(
    signal_factory, checklist_db, schema_report
) -> None:
    match, _ = _evaluate(
        signal_factory,
        checklist_db,
        schema_report,
        "RFC 8624",
        {"timestamp": "2020-01-01", "rr_type": "DNSKEY", "algorithm": 13},
    )
    breakdown = match.score_breakdown

    assert breakdown.ambiguity_penalty == pytest.approx(config.AMBIGUITY_PENALTY)
    assert breakdown.base_indicator_score == pytest.approx(5.0)
    assert breakdown.optional_match_bonus == pytest.approx(1.5)
    assert breakdown.final_score == pytest.approx(3.375)


def test_the_all_required_bonus_needs_at_least_two_required_indicators(
    signal_factory, checklist_db, schema_report
) -> None:
    """Every shipped RFC has one required indicator, so none of them earns the bonus."""
    for rfc_id, observation, _score, _confidence, _decision in WORKED_EXPECTATIONS:
        match, _ = _evaluate(signal_factory, checklist_db, schema_report, rfc_id, observation)
        assert match.score_breakdown.required_match_bonus == pytest.approx(0.0)
        assert any(
            f"needs at least {config.MIN_REQUIRED_FOR_BONUS}" in step
            for step in match.score_breakdown.steps
        )


def test_the_raw_total_is_clamped_at_zero_before_the_multiplier(
    signal_factory, checklist_db, schema_report, score_step_terms
) -> None:
    """Algorithm 1 is what RFC 8624 tells operators to avoid, so nothing matches."""
    match, _ = _evaluate(
        signal_factory,
        checklist_db,
        schema_report,
        "RFC 8624",
        {"timestamp": "2020-01-01", "rr_type": "DNSKEY", "algorithm": 1},
    )
    terms = score_step_terms(match.score_breakdown)

    assert match.decision == "no_match"
    assert terms["missing_required_penalty"] == pytest.approx(config.MISSING_REQUIRED_PENALTY)
    assert terms["raw"] < 0.0, "the penalties really do drive the raw total negative"
    assert match.score_breakdown.final_score == pytest.approx(0.0)
    assert match.confidence == "none"


# --------------------------------------------------------------------------- #
# Relative ordering
# --------------------------------------------------------------------------- #


def test_rfc8078_outranks_rfc7344_for_cds_delete_signal(
    signal_factory, checklist_db, schema_report
) -> None:
    """Both explain the record; RFC 8078 adds the condition that pins the meaning."""
    signals = [signal_factory("2018-05-01", rr_type="CDS", algorithm=0, digest_type=0)]

    matches, _ = match_all(signals, checklist_db, schema_report)
    ranked = rank_candidates(matches, checklist_db)
    by_id = {candidate.rfc_id: candidate for candidate in ranked}

    assert by_id["RFC 8078"].score > by_id["RFC 7344"].score
    assert by_id["RFC 8078"].rank < by_id["RFC 7344"].rank
    assert ranked[0].rfc_id == "RFC 8078"


def test_rfc6605_outranks_rfc8624_for_algorithm_thirteen(
    signal_factory, checklist_db, schema_report
) -> None:
    signals = [signal_factory("2020-01-01", rr_type="DNSKEY", algorithm=13)]

    matches, _ = match_all(signals, checklist_db, schema_report)
    ranked = rank_candidates(matches, checklist_db)
    by_id = {candidate.rfc_id: candidate for candidate in ranked}

    assert by_id["RFC 6605"].score == pytest.approx(13.125)
    assert by_id["RFC 8624"].score == pytest.approx(3.375)
    assert by_id["RFC 6605"].rank < by_id["RFC 8624"].rank


def test_rfc8080_outranks_rfc8624_for_algorithm_fifteen(
    signal_factory, checklist_db, schema_report
) -> None:
    signals = [signal_factory("2020-05-18", rr_type="DNSKEY", algorithm=15)]

    matches, _ = match_all(signals, checklist_db, schema_report)
    ranked = rank_candidates(matches, checklist_db)
    by_id = {candidate.rfc_id: candidate for candidate in ranked}

    assert by_id["RFC 8080"].score == pytest.approx(17.25)
    assert by_id["RFC 8080"].rank < by_id["RFC 8624"].rank


def test_base_dnssec_records_rank_low_and_only_reach_rfc4033(
    signal_factory, checklist_db, schema_report
) -> None:
    """Contract case 7: an algorithm-8 DNSKEY is base DNSSEC, and specifically RSA/SHA-2.

    Checklist 0.2.0 named the algorithm that case 7 always carried: algorithm 8 is
    RSASHA256, which RFC 5702 defines. So the observation now evidences a specific
    algorithm RFC as well as the base, and RFC 5702 -- being the specific one --
    must outrank RFC 4033. What must NOT happen is a competing *algorithm* RFC
    appearing: an algorithm-8 record is not evidence of ECDSA or EdDSA.
    """
    signals = [signal_factory("2011-05-24", rr_type="DNSKEY", algorithm=8)]

    matches, _ = match_all(signals, checklist_db, schema_report)
    ranked = rank_candidates(matches, checklist_db)
    ids = [candidate.rfc_id for candidate in ranked]

    assert "RFC 5702" in ids, "algorithm 8 is RSASHA256, which RFC 5702 defines"
    assert "RFC 4033" in ids, "it is still base DNSSEC"
    assert ids.index("RFC 5702") < ids.index("RFC 4033"), (
        "the specific algorithm RFC must outrank the base"
    )
    for wrong in ("RFC 6605", "RFC 8080", "RFC 5933", "RFC 9558", "RFC 9563"):
        assert wrong not in ids, f"algorithm 8 is not evidence of {wrong}"

    base = next(c for c in ranked if c.rfc_id == "RFC 4033")
    assert base.confidence in {"low", "medium"}
    assert base.score == pytest.approx(3.75)


# --------------------------------------------------------------------------- #
# Confidence banding
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (17.25, "very_high"),
        (12.0, "very_high"),
        (11.9999, "high"),
        (8.0, "high"),
        (7.9999, "medium"),
        (4.0, "medium"),
        (3.375, "low"),
        (0.0001, "low"),
        (0.0, "none"),
    ],
)
def test_confidence_bands_follow_the_threshold_table(score: float, expected: str) -> None:
    assert confidence_for(score) == expected


# --------------------------------------------------------------------------- #
# Aggregation across signals
# --------------------------------------------------------------------------- #


def _candidate(rfc_id: str, score: float, **overrides) -> RankedRFCCandidate:
    payload = {
        "rank": 0,
        "rfc_id": rfc_id,
        "rfc_title": rfc_id,
        "specificity": "high",
        "rfc_publication_date": datetime(2014, 9, 1),
        "decision": "valid_match",
        "score": score,
        "confidence": confidence_for(score),
    }
    payload.update(overrides)
    return RankedRFCCandidate(**payload)


def test_rank_candidates_uses_the_best_observation_not_the_sum(
    signal_factory, checklist_db, schema_report
) -> None:
    signals = [
        signal_factory("2018-05-01", rr_type="CDS", algorithm=0, digest_type=0),
        signal_factory("2019-02-11", rr_type="CDS", algorithm=0, digest_type=0),
        signal_factory("2019-04-12", rr_type="CDS"),  # partial evidence only
    ]

    matches, _ = match_all(signals, checklist_db, schema_report)
    ranked = rank_candidates(matches, checklist_db)
    rfc8078 = next(candidate for candidate in ranked if candidate.rfc_id == "RFC 8078")

    assert rfc8078.score == pytest.approx(17.25), "score is the strongest observation"
    assert rfc8078.aggregate_score == pytest.approx(34.5), "aggregate is the volume measure"
    assert rfc8078.valid_match_count == 2
    assert rfc8078.partial_match_count == 1
    # A partial match scores 0.0, so counting it as support would inflate the
    # evidence base with observations that contributed nothing.
    assert rfc8078.supporting_signal_count == 2
    assert set(ADOPTION_DECISIONS) == {"valid_match", "ambiguous"}
    assert rfc8078.decision == "valid_match", "the strongest decision wins"


def test_rank_candidates_drops_no_match_and_zero_scoring_evaluations(
    signal_factory, checklist_db, schema_report
) -> None:
    """A zero score is not evidence, whether it came from no_match or from penalties."""
    signals = [signal_factory("2010-06-15", rr_type="NSEC3", algorithm=1)]

    matches, _ = match_all(signals, checklist_db, schema_report)
    ranked = rank_candidates(matches, checklist_db)
    by_rfc = {match.rfc_id: match for match in matches}

    assert [candidate.rfc_id for candidate in ranked] == ["RFC 5155"]
    assert by_rfc["RFC 8078"].decision == "no_match"
    # RFC 4033 is rankable in principle but its penalties leave it at zero.
    assert by_rfc["RFC 4033"].decision == "partial_match"
    assert by_rfc["RFC 4033"].score == pytest.approx(0.0)


def test_rank_candidates_honours_the_min_score_threshold(
    signal_factory, checklist_db, schema_report
) -> None:
    signals = [signal_factory("2020-01-01", rr_type="DNSKEY", algorithm=13)]

    matches, _ = match_all(signals, checklist_db, schema_report)
    everything = rank_candidates(matches, checklist_db)
    filtered = rank_candidates(matches, checklist_db, min_score=5.0)

    assert "RFC 8624" in {c.rfc_id for c in everything}
    assert "RFC 8624" not in {c.rfc_id for c in filtered}
    assert all(candidate.score > 5.0 for candidate in filtered)
    assert [candidate.rank for candidate in filtered] == list(range(1, len(filtered) + 1))


def test_rank_candidates_returns_a_dense_rank_ordered_by_score(
    signal_factory, checklist_db, schema_report
) -> None:
    signals = [
        signal_factory("2018-05-01", rr_type="CDS", algorithm=0, digest_type=0),
        signal_factory("2020-01-01", rr_type="DNSKEY", algorithm=13),
        signal_factory("2012-03-14", rr_type="DS", algorithm=8, digest_type=2),
    ]

    matches, _ = match_all(signals, checklist_db, schema_report)
    ranked = rank_candidates(matches, checklist_db)

    assert [candidate.rank for candidate in ranked] == list(range(1, len(ranked) + 1))
    scores = [candidate.score for candidate in ranked]
    assert scores == sorted(scores, reverse=True)
    for candidate in ranked:
        assert candidate.reasoning_summary.startswith(candidate.rfc_id)
        assert candidate.score_breakdown is not None


def test_rank_candidates_is_empty_without_matches(checklist_db) -> None:
    assert rank_candidates([], checklist_db) == []


def test_close_ranking_pairs_flags_neighbours_inside_the_tolerance() -> None:
    candidates = [
        _candidate("RFC 5155", 17.25, rank=1),
        _candidate("RFC 8078", 17.0, rank=2),
        _candidate("RFC 4033", 3.75, rank=3),
    ]

    pairs = close_ranking_pairs(candidates)

    assert [(a.rfc_id, b.rfc_id) for a, b in pairs] == [("RFC 5155", "RFC 8078")]


def test_close_ranking_pairs_ignores_partial_matches() -> None:
    candidates = [
        _candidate("RFC 5155", 17.25, rank=1),
        _candidate("RFC 8078", 17.0, rank=2, decision="partial_match"),
    ]

    assert close_ranking_pairs(candidates) == []


def test_close_ranking_pairs_respects_an_explicit_tolerance() -> None:
    candidates = [_candidate("RFC 5155", 10.0, rank=1), _candidate("RFC 8078", 9.0, rank=2)]

    assert close_ranking_pairs(candidates, tolerance=0.05) == []
    assert len(close_ranking_pairs(candidates, tolerance=0.2)) == 1


def test_score_breakdown_defaults_are_all_zero() -> None:
    breakdown = ScoreBreakdown()

    assert breakdown.final_score == 0.0
    assert breakdown.timestamp_penalty == 0.0
    assert breakdown.steps == []


def test_rank_candidates_tolerates_a_match_for_an_rfc_outside_the_checklist(
    signal_factory, checklist_db, schema_report
) -> None:
    """A checklist revision mismatch must not crash the ranker."""
    signals = [signal_factory("2018-05-01", rr_type="CDS", algorithm=0, digest_type=0)]
    matches, _ = match_all(signals, checklist_db, schema_report)
    stranger = matches[0].model_copy(update={"rfc_id": "RFC 9999", "rfc_title": "Unknown"})

    ranked = rank_candidates([*matches, stranger], checklist_db)

    unknown = next(candidate for candidate in ranked if candidate.rfc_id == "RFC 9999")
    assert unknown.specificity == "medium"
    assert isinstance(unknown, RankedRFCCandidate)


def test_matches_are_plain_models_with_a_trace_id(
    signal_factory, checklist_db, schema_report
) -> None:
    signals = [signal_factory("2018-05-01", signal_id="sig_0007", rr_type="CDS", algorithm=0)]

    matches, _ = match_all(signals, checklist_db, schema_report)
    rfc8078 = next(match for match in matches if match.rfc_id == "RFC 8078")

    assert isinstance(rfc8078, RFCMatch)
    assert rfc8078.trace_id == "trace_sig_0007_rfc8078"
