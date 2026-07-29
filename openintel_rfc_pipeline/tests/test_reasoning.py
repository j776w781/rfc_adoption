"""Reasoning traces: the structured record of a decision already made.

A trace has to carry four things at once -- the conditions that matched, the
conditions that failed, the publication-date verdict, and the score arithmetic --
and its prose has to name concrete values so a reader can check the claim against
the observation instead of trusting it. Both properties are asserted here.
"""

from __future__ import annotations

import pytest

from openintel_rfc.matcher import evaluate_condition, match_signal_to_rfc
from openintel_rfc.models import (
    ConditionEvaluation,
    IndicatorCondition,
    IndicatorEvaluation,
    ReasoningTrace,
)
from openintel_rfc.reasoning import (
    explain_condition,
    explain_indicator,
    explain_timestamp,
    summarize_decision,
    trace_to_row,
)


@pytest.fixture
def delete_signal_trace(signal_factory, checklist_db, schema_report) -> ReasoningTrace:
    rfc = checklist_db.get("RFC 8078")
    assert rfc is not None
    signal = signal_factory(
        "2018-05-01", signal_id="sig_0001", rr_type="CDS", algorithm=0, digest_type=0
    )
    return match_signal_to_rfc(signal, rfc, schema_report)[1]


# --------------------------------------------------------------------------- #
# Trace contents
# --------------------------------------------------------------------------- #


def test_the_trace_lists_the_conditions_that_matched(delete_signal_trace) -> None:
    matched = delete_signal_trace.matched_conditions

    assert matched, "a valid match must record which predicates held"
    assert all(isinstance(c, ConditionEvaluation) and c.passed for c in matched)
    assert {c.field for c in matched} == {"rr_type", "algorithm", "digest_type"}
    assert any(c.field == "algorithm" and c.observed == 0 for c in matched)


def test_the_trace_lists_the_conditions_that_failed(
    signal_factory, checklist_db, schema_report
) -> None:
    rfc = checklist_db.get("RFC 8078")
    assert rfc is not None
    signal = signal_factory("2018-05-01", rr_type="CDS", algorithm=8, digest_type=2)

    _, trace = match_signal_to_rfc(signal, rfc, schema_report)

    assert trace.failed_conditions
    assert all(not c.passed for c in trace.failed_conditions)
    failed = {(c.field, c.observed) for c in trace.failed_conditions}
    assert ("algorithm", 8) in failed
    assert "rfc8078_cds_cdnskey_algorithm_zero" in trace.failed_indicator_ids


def test_the_trace_carries_the_timestamp_check(delete_signal_trace) -> None:
    check = delete_signal_trace.timestamp_check

    assert check.valid is True
    assert delete_signal_trace.timestamp_valid is True
    assert check.observation_timestamp == delete_signal_trace.observation_timestamp
    assert check.rfc_publication_date == delete_signal_trace.rfc_publication_date
    assert check.days_after_publication == 426
    assert check.explanation.endswith("so the timestamp is valid.")


def test_the_trace_carries_the_itemized_score_breakdown(delete_signal_trace) -> None:
    breakdown = delete_signal_trace.score_breakdown

    assert breakdown.final_score == pytest.approx(17.25)
    assert breakdown.base_indicator_score == pytest.approx(10.0)
    assert breakdown.optional_match_bonus == pytest.approx(1.5)
    assert breakdown.specificity_multiplier == pytest.approx(1.5)
    assert len(breakdown.steps) >= 9, "one line per term, including the zero ones"


def test_the_trace_records_which_openintel_fields_carried_the_match(
    delete_signal_trace,
) -> None:
    assert delete_signal_trace.matched_openintel_fields == [
        "algorithm",
        "digest_type",
        "rr_type",
    ]
    assert delete_signal_trace.missing_fields == []


def test_the_trace_snapshots_the_observation_it_judged(delete_signal_trace) -> None:
    observation = delete_signal_trace.supporting_observation

    assert observation["signal_id"] == "sig_0001"
    assert observation["fields"]["rr_type"] == "CDS"
    assert observation["fields"]["algorithm"] == 0
    assert observation["indicator_explanations"], "per-indicator prose is part of the record"


def test_the_trace_id_pairs_the_signal_with_the_rfc(delete_signal_trace) -> None:
    assert delete_signal_trace.trace_id == "trace_sig_0001_rfc8078"
    assert delete_signal_trace.signal_id == "sig_0001"
    assert delete_signal_trace.rfc_id == "RFC 8078"


# --------------------------------------------------------------------------- #
# Prose
# --------------------------------------------------------------------------- #


def test_the_summary_names_the_rfc_the_indicator_the_values_and_the_score(
    delete_signal_trace,
) -> None:
    summary = delete_signal_trace.reasoning_summary

    assert "RFC 8078" in summary
    assert "rfc8078_cds_cdnskey_algorithm_zero" in summary
    assert "rr_type=CDS" in summary
    assert "algorithm=0" in summary
    assert "17.25" in summary
    assert "very_high" in summary
    assert "2017-03-01" in summary, "the publication date it was compared against"


def test_a_no_match_summary_explains_why_not(
    signal_factory, checklist_db, schema_report
) -> None:
    rfc = checklist_db.get("RFC 5155")
    assert rfc is not None
    signal = signal_factory("2018-05-01", rr_type="DNSKEY", algorithm=8)

    _, trace = match_signal_to_rfc(signal, rfc, schema_report)

    assert trace.decision == "no_match"
    assert "does not explain" in trace.reasoning_summary
    assert "rfc5155_nsec3_record_present" in trace.reasoning_summary
    assert "nothing to score" in trace.reasoning_summary


def test_explain_condition_says_absence_is_not_evidence(signal_factory) -> None:
    signal = signal_factory("2020-01-01", rr_type="CDS")

    evaluation = evaluate_condition(
        IndicatorCondition(field="algorithm", op="equals", value=0), signal
    )

    text = explain_condition(evaluation)
    assert "field 'algorithm' is absent from this observation" in text
    assert "absence is not evidence" in text


def test_explain_condition_renders_a_passing_predicate_checkably(signal_factory) -> None:
    signal = signal_factory("2020-01-01", rr_type="CDS", algorithm=0)

    evaluation = evaluate_condition(
        IndicatorCondition(field="algorithm", op="equals", value=0), signal
    )

    assert explain_condition(evaluation) == "algorithm=0 equals the expected value 0"


def test_explain_indicator_distinguishes_skipped_from_failed() -> None:
    skipped = IndicatorEvaluation(
        indicator_id="probe",
        indicator_description="probe",
        required=True,
        weight=6.0,
        queryability="non_queryable",
        matched=False,
        skipped=True,
        missing_fields=["validator_algorithm_support"],
    )

    text = explain_indicator(skipped)

    assert "was not evaluated" in text
    assert "neither as evidence nor as a failure" in text


def test_explain_timestamp_reports_a_rejection_in_full_sentences(
    signal_factory, checklist_db, schema_report
) -> None:
    rfc = checklist_db.get("RFC 8078")
    assert rfc is not None
    signal = signal_factory("2016-01-15", rr_type="CDS", algorithm=0, digest_type=0)

    _, trace = match_signal_to_rfc(signal, rfc, schema_report)

    text = explain_timestamp(trace.timestamp_check)
    assert text.startswith("The observation on 2016-01-15 predates")
    assert "cannot evidence adoption of an RFC that did not yet exist" in text


def test_summarize_decision_states_the_same_verdict_as_the_trace(
    signal_factory, checklist_db, schema_report
) -> None:
    """The standalone summary differs from the trace's only in its subject."""
    rfc = checklist_db.get("RFC 4509")
    assert rfc is not None
    signal = signal_factory("2012-03-14", rr_type="DS", algorithm=8, digest_type=2)
    match, trace = match_signal_to_rfc(signal, rfc, schema_report)

    standalone = summarize_decision(
        rfc,
        match.decision,
        match.indicator_evaluations,
        trace.timestamp_check,
        match.score_breakdown,
    )

    assert "this observation" in standalone
    assert f"signal {trace.signal_id}" in trace.reasoning_summary
    assert standalone.replace("this observation", f"signal {trace.signal_id}") == (
        trace.reasoning_summary
    )


# --------------------------------------------------------------------------- #
# Uncertainty
# --------------------------------------------------------------------------- #


def test_uncertainty_notes_flag_a_partially_queryable_indicator(
    signal_factory, checklist_db, schema_report
) -> None:
    rfc = checklist_db.get("RFC 4033")
    assert rfc is not None
    signal = signal_factory("2011-05-24", rr_type="DNSKEY", algorithm=8)

    _, trace = match_signal_to_rfc(signal, rfc, schema_report)

    assert any(
        "rfc4033_dnssec_ok_negotiated" in note and "partially queryable" in note
        for note in trace.uncertainty_notes
    )
    assert any("dnssec_ok_flag" in note for note in trace.uncertainty_notes)


def test_uncertainty_notes_flag_an_ambiguous_match(
    signal_factory, checklist_db, schema_report
) -> None:
    rfc = checklist_db.get("RFC 8624")
    assert rfc is not None
    signal = signal_factory("2020-01-01", rr_type="DNSKEY", algorithm=13)

    _, trace = match_signal_to_rfc(signal, rfc, schema_report)

    assert trace.decision == "ambiguous"
    assert any("flagged ambiguous" in note for note in trace.uncertainty_notes)
    assert any("never tested" in note or "Corpus availability" in note for note in trace.uncertainty_notes)


def test_uncertainty_notes_flag_a_partial_match_as_not_adoption_evidence(
    signal_factory, checklist_db, schema_report
) -> None:
    rfc = checklist_db.get("RFC 8078")
    assert rfc is not None
    signal = signal_factory("2019-04-12", rr_type="CDS")

    _, trace = match_signal_to_rfc(signal, rfc, schema_report)

    assert trace.decision == "partial_match"
    assert any("candidates, not adoption evidence" in note for note in trace.uncertainty_notes)


def test_uncertainty_notes_are_deduplicated(delete_signal_trace) -> None:
    notes = delete_signal_trace.uncertainty_notes
    assert len(notes) == len(set(notes))


# --------------------------------------------------------------------------- #
# Flat rendering
# --------------------------------------------------------------------------- #


def test_trace_to_row_flattens_without_losing_information(delete_signal_trace) -> None:
    row = trace_to_row(delete_signal_trace)

    assert row["trace_id"] == "trace_sig_0001_rfc8078"
    assert row["decision"] == "valid_match"
    assert row["final_score"] == pytest.approx(17.25)
    assert row["timestamp_valid"] == "true", "booleans render as text for CSV"
    assert row["matched_condition_count"] == len(delete_signal_trace.matched_conditions)
    assert "; " in row["matched_conditions"], "condition prose is joined, not dropped"
    assert "base_indicator_score" in row["score_steps"]
    assert all(not isinstance(value, (list, dict)) for value in row.values())
