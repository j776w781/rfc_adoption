"""The publication-date cutoff, checked from every angle it can leak through.

An observation recorded before an RFC existed cannot be evidence of adopting it.
That single rule is what separates "these bytes look like RFC 8078" from "this
is evidence of RFC 8078 adoption", and it has to hold simultaneously in five
places: the score, the decision, the ranked candidates, the adoption timeline
and the review queue. Each of those is asserted separately below, because a
regression in any one of them would produce an adoption curve that starts before
the RFC was published.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openintel_rfc import config
from openintel_rfc.llm_verifier import DeterministicVerifier
from openintel_rfc.matcher import match_all, match_signal_to_rfc
from openintel_rfc.ranking import RANKABLE_DECISIONS, rank_candidates
from openintel_rfc.review_queue import build_review_queue
from openintel_rfc.timeline import build_timeline, monthly_buckets

#: RFC 8078 was published 2017-03-01; this observation is over a year early.
EARLY = "2016-01-15"
#: The same record shape, safely after publication.
LATE = "2018-05-01"

#: What a valid RFC 8078 delete signal is worth, and therefore what is forfeited.
RFC8078_SCORE = 17.25


@pytest.fixture
def early_delete_signal(signal_factory):
    """A CDS delete signal recorded before RFC 8078 existed."""
    return signal_factory(EARLY, signal_id="sig_0001", rr_type="CDS", algorithm=0, digest_type=0)


@pytest.fixture
def late_delete_signal(signal_factory):
    """The same record shape, recorded after RFC 8078 was published."""
    return signal_factory(LATE, signal_id="sig_0002", rr_type="CDS", algorithm=0, digest_type=0)


@pytest.fixture
def early_match(early_delete_signal, checklist_db, schema_report):
    rfc = checklist_db.get("RFC 8078")
    assert rfc is not None
    return match_signal_to_rfc(early_delete_signal, rfc, schema_report)


# --------------------------------------------------------------------------- #
# 1. The score itself
# --------------------------------------------------------------------------- #


def test_a_timestamp_invalid_match_scores_exactly_zero(early_match) -> None:
    match, trace = early_match

    assert match.decision == "timestamp_invalid"
    assert match.score == pytest.approx(0.0)
    assert match.score_breakdown.final_score == pytest.approx(0.0)
    assert match.confidence == "none"
    assert trace.score_breakdown.final_score == pytest.approx(0.0)


def test_the_withheld_score_is_recorded_in_timestamp_penalty(early_match) -> None:
    """The reviewer must be able to see exactly what was taken away."""
    match, _ = early_match

    assert match.score_breakdown.timestamp_penalty == pytest.approx(RFC8078_SCORE)


def test_the_withheld_score_equals_what_the_same_record_earns_after_publication(
    early_match, late_delete_signal, checklist_db, schema_report
) -> None:
    early, _ = early_match
    rfc = checklist_db.get("RFC 8078")
    assert rfc is not None
    late, _ = match_signal_to_rfc(late_delete_signal, rfc, schema_report)

    assert late.decision == "valid_match"
    assert early.score_breakdown.timestamp_penalty == pytest.approx(late.score)
    assert early.score == pytest.approx(0.0)


def test_the_score_steps_state_the_forfeit_and_end_at_zero(
    early_match, score_step_terms
) -> None:
    _, trace = early_match
    steps = trace.score_breakdown.steps

    assert any("timestamp_penalty" in step and "predates" in step for step in steps)
    assert any("the score is withheld" in step for step in steps)
    assert steps[-1].startswith("final_score = 0.0")
    assert "cannot evidence adoption of an RFC that did not yet exist" in steps[-1]

    terms = score_step_terms(trace.score_breakdown)
    assert terms["timestamp_penalty"] == pytest.approx(RFC8078_SCORE)
    assert terms["final_score"] == pytest.approx(0.0)


def test_the_matched_indicators_are_still_recorded(early_match) -> None:
    """The evidence is not erased, only disqualified -- that is what makes it reviewable."""
    match, trace = early_match

    assert "rfc8078_cds_cdnskey_algorithm_zero" in match.matched_indicator_ids
    assert trace.matched_conditions, "the conditions that passed are still listed"
    assert trace.timestamp_valid is False
    assert any("predates" in note for note in trace.uncertainty_notes)


def test_a_no_match_is_not_relabelled_timestamp_invalid(
    signal_factory, checklist_db, schema_report
) -> None:
    """An evaluation that fails on the evidence stays a no_match: the date did not decide it."""
    rfc = checklist_db.get("RFC 5155")
    assert rfc is not None
    signal = signal_factory("2001-01-01", rr_type="DNSKEY", algorithm=8)

    match, _ = match_signal_to_rfc(signal, rfc, schema_report)

    assert match.timestamp_valid is False
    assert match.decision == "no_match"
    assert match.score_breakdown.timestamp_penalty == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# 2. Ranked candidates
# --------------------------------------------------------------------------- #


def test_an_rfc_whose_only_evidence_predates_it_is_not_a_ranked_candidate(
    early_delete_signal, checklist_db, schema_report
) -> None:
    matches, _ = match_all([early_delete_signal], checklist_db, schema_report)

    ranked = rank_candidates(matches, checklist_db)

    ranked_ids = {candidate.rfc_id for candidate in ranked}
    assert "RFC 8078" not in ranked_ids
    # RFC 7344 defined the record type in 2014, so the same row is valid for it.
    assert "RFC 7344" in ranked_ids


def test_timestamp_invalid_is_not_a_rankable_decision() -> None:
    assert "timestamp_invalid" not in RANKABLE_DECISIONS
    assert "no_match" not in RANKABLE_DECISIONS


def test_a_late_observation_rescues_the_rfc_and_the_early_one_is_counted_separately(
    early_delete_signal, late_delete_signal, checklist_db, schema_report
) -> None:
    matches, _ = match_all(
        [early_delete_signal, late_delete_signal], checklist_db, schema_report
    )

    ranked = rank_candidates(matches, checklist_db)
    rfc8078 = next(candidate for candidate in ranked if candidate.rfc_id == "RFC 8078")

    assert rfc8078.score == pytest.approx(RFC8078_SCORE)
    assert rfc8078.supporting_signal_count == 1, "only the valid observation supports it"
    assert rfc8078.timestamp_invalid_count == 1
    assert rfc8078.first_seen is not None
    assert rfc8078.first_seen.date().isoformat() == LATE
    assert "withheld from the score" in rfc8078.reasoning_summary


def test_the_early_observation_never_moves_first_seen_backwards(
    early_delete_signal, late_delete_signal, checklist_db, schema_report
) -> None:
    matches, _ = match_all(
        [early_delete_signal, late_delete_signal], checklist_db, schema_report
    )

    ranked = rank_candidates(matches, checklist_db)
    rfc8078 = next(candidate for candidate in ranked if candidate.rfc_id == "RFC 8078")
    publication = rfc8078.rfc_publication_date

    assert rfc8078.first_seen is not None and rfc8078.first_seen >= publication
    assert rfc8078.last_seen is not None and rfc8078.last_seen >= publication


# --------------------------------------------------------------------------- #
# 3. The adoption timeline
# --------------------------------------------------------------------------- #


def test_a_timestamp_invalid_match_does_not_set_first_seen(
    early_delete_signal, checklist_db, schema_report
) -> None:
    matches, _ = match_all([early_delete_signal], checklist_db, schema_report)

    timeline = build_timeline(matches, checklist_db)
    rfc8078 = next(entry for entry in timeline if entry.rfc_id == "RFC 8078")

    assert rfc8078.first_seen is None
    assert rfc8078.last_seen is None
    assert rfc8078.observation_count == 0
    assert rfc8078.days_from_publication_to_first_seen is None
    assert "1 timestamp_invalid" in rfc8078.notes
    assert "not evidence of non-adoption" in rfc8078.notes


def test_the_cutoff_holds_even_if_a_caller_asks_for_timestamp_invalid_matches(
    early_delete_signal, checklist_db, schema_report
) -> None:
    """Rule 2 of ``_qualifying_matches`` is structural, not a convention."""
    matches, _ = match_all([early_delete_signal], checklist_db, schema_report)

    timeline = build_timeline(
        matches, checklist_db, include_decisions=("valid_match", "timestamp_invalid")
    )
    rfc8078 = next(entry for entry in timeline if entry.rfc_id == "RFC 8078")

    assert rfc8078.first_seen is None
    assert rfc8078.observation_count == 0


def test_monthly_buckets_ignore_observations_that_predate_the_rfc(
    early_delete_signal, late_delete_signal, checklist_db, schema_report
) -> None:
    matches, _ = match_all(
        [early_delete_signal, late_delete_signal], checklist_db, schema_report
    )
    rfc8078_matches = [m for m in matches if m.rfc_id == "RFC 8078"]

    buckets = monthly_buckets(rfc8078_matches)

    assert [bucket.period for bucket in buckets] == ["2018-05"]


def test_no_timeline_entry_ever_has_a_negative_days_to_first_seen(
    analyzed_output: Path,
) -> None:
    payload = json.loads(
        (analyzed_output / config.OUTPUT_FILES["adoption_timeline"]).read_text(encoding="utf-8")
    )

    for entry in payload["timeline"]:
        days = entry["days_from_publication_to_first_seen"]
        assert days is None or days >= 0, f"{entry['rfc_id']} first_seen predates publication"
        assert "BUG:" not in entry["notes"]


# --------------------------------------------------------------------------- #
# 4. The review queue and the verifier
# --------------------------------------------------------------------------- #


def test_the_review_queue_surfaces_the_timestamp_invalid_match(
    early_delete_signal, checklist_db, schema_report
) -> None:
    matches, traces = match_all([early_delete_signal], checklist_db, schema_report)
    ranked = rank_candidates(matches, checklist_db)

    items = build_review_queue(
        schema_report=schema_report,
        matches=matches,
        traces=traces,
        ranked=ranked,
        db=checklist_db,
    )

    invalid = [
        item
        for item in items
        if item.item_type == "timestamp_invalid_match" and "RFC 8078" in item.affected_rfc_ids
    ]
    assert len(invalid) == 1
    item = invalid[0]
    assert item.severity == "high"
    assert item.affected_signal_ids == ["sig_0001"]
    assert item.evidence["forfeited_score_total"] == pytest.approx(RFC8078_SCORE)
    assert item.evidence["max_days_before_publication"] > 0
    # The evidence really belongs to RFC 7344, and the item says so.
    assert "RFC 7344" in item.evidence["alternative_valid_rfc_ids"]


def test_the_deterministic_verifier_rejects_a_timestamp_invalid_trace(early_match) -> None:
    _, trace = early_match

    verification = DeterministicVerifier().verify(trace=trace)

    assert verification.verification_status == "rejected"
    assert "before" in verification.explanation
    assert "did not yet exist" in verification.explanation


# --------------------------------------------------------------------------- #
# 5. End to end, over the real sample data
# --------------------------------------------------------------------------- #


def test_the_analyze_run_records_timestamp_invalid_matches_with_zero_score(
    analyzed_output: Path,
) -> None:
    payload = json.loads(
        (analyzed_output / config.OUTPUT_FILES["rfc_matches"]).read_text(encoding="utf-8")
    )
    invalid = [m for m in payload["matches"] if m["decision"] == "timestamp_invalid"]

    assert invalid, "the sample data deliberately contains pre-publication observations"
    for match in invalid:
        assert match["score"] == 0.0
        assert match["timestamp_valid"] is False
        assert match["score_breakdown"]["final_score"] == 0.0
        assert match["observation_timestamp"] < match["rfc_publication_date"]


def test_every_ranked_candidate_in_the_analyze_run_is_first_seen_after_publication(
    analyzed_output: Path,
) -> None:
    payload = json.loads(
        (analyzed_output / config.OUTPUT_FILES["ranked_candidates"]).read_text(encoding="utf-8")
    )

    for candidate in payload["candidates"]:
        if candidate["first_seen"] is None:
            continue
        assert candidate["first_seen"] >= candidate["rfc_publication_date"], candidate["rfc_id"]


def test_the_pre_publication_cds_rows_are_attributed_to_rfc7344_not_rfc8078(
    analyzed_output: Path,
) -> None:
    payload = json.loads(
        (analyzed_output / config.OUTPUT_FILES["rfc_matches"]).read_text(encoding="utf-8")
    )
    rfc8078_invalid = {
        m["signal_id"] for m in payload["matches"]
        if m["rfc_id"] == "RFC 8078" and m["decision"] == "timestamp_invalid"
    }
    rfc7344_valid = {
        m["signal_id"] for m in payload["matches"]
        if m["rfc_id"] == "RFC 7344" and m["decision"] == "valid_match"
    }

    assert rfc8078_invalid, "the fixture contains CDS delete signals from before 2017-03"
    assert rfc8078_invalid <= rfc7344_valid
