"""Condition operators, indicator evaluation and the signal x RFC match loop.

Two rules are asserted repeatedly here because everything else rests on them:

* absence is not evidence -- a field the observation does not carry fails every
  operator and is recorded as untested, never as a contradiction;
* untestable is not failed -- a non-queryable indicator is skipped, and a
  skipped indicator neither earns weight nor incurs a penalty.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from openintel_rfc.matcher import (
    check_timestamp,
    evaluate_condition,
    evaluate_indicator,
    match_all,
    match_signal_to_rfc,
)
from openintel_rfc.models import (
    IndicatorCondition,
    ObservedSignal,
    RFCChecklistDB,
    RFCIndicator,
    SchemaCheckReport,
)

ALL_OPS = (
    "equals",
    "not_equals",
    "in",
    "exists",
    "contains",
    "greater_or_equal",
    "less_or_equal",
)


def _match(signal, db: RFCChecklistDB, rfc_id: str, report: SchemaCheckReport):
    rfc = db.get(rfc_id)
    assert rfc is not None, f"{rfc_id} is missing from the checklist database"
    return match_signal_to_rfc(signal, rfc, report)


# --------------------------------------------------------------------------- #
# Worked expectations from the build contract
# --------------------------------------------------------------------------- #


def test_rfc8078_matches_cds_algorithm_zero_after_publication(
    signal_factory, checklist_db, schema_report
) -> None:
    signal = signal_factory("2018-05-01", rr_type="CDS", algorithm=0, digest_type=0)

    match, trace = _match(signal, checklist_db, "RFC 8078", schema_report)

    assert match.decision == "valid_match"
    assert match.timestamp_valid is True
    assert match.confidence == "very_high"
    assert "rfc8078_cds_cdnskey_algorithm_zero" in match.matched_indicator_ids
    assert set(match.matched_fields) == {"rr_type", "algorithm", "digest_type"}
    assert trace.decision == "valid_match"


def test_rfc8078_is_timestamp_invalid_when_the_observation_predates_publication(
    signal_factory, checklist_db, schema_report
) -> None:
    signal = signal_factory("2016-01-15", rr_type="CDS", algorithm=0, digest_type=0)

    match, trace = _match(signal, checklist_db, "RFC 8078", schema_report)

    assert match.decision == "timestamp_invalid"
    assert match.timestamp_valid is False
    assert match.score == 0.0
    # The indicators still matched; only the date disqualifies the evidence.
    assert "rfc8078_cds_cdnskey_algorithm_zero" in match.matched_indicator_ids
    assert trace.timestamp_check.valid is False
    assert trace.timestamp_check.days_after_publication < 0


def test_rfc7344_still_matches_a_cds_record_that_predates_rfc8078(
    signal_factory, checklist_db, schema_report
) -> None:
    """RFC 7344 defined the record type in 2014, so the same row is valid for it."""
    signal = signal_factory("2016-01-15", rr_type="CDS", algorithm=0, digest_type=0)

    match, _ = _match(signal, checklist_db, "RFC 7344", schema_report)

    assert match.decision == "valid_match"
    assert match.timestamp_valid is True
    assert match.score == pytest.approx(11.25)


def test_rfc5155_matches_an_nsec3_record(signal_factory, checklist_db, schema_report) -> None:
    signal = signal_factory("2010-06-15", rr_type="NSEC3", algorithm=1)

    match, _ = _match(signal, checklist_db, "RFC 5155", schema_report)

    assert match.decision == "valid_match"
    assert match.confidence == "very_high"
    assert "rfc5155_nsec3_record_present" in match.matched_indicator_ids


def test_rfc5155_also_matches_nsec3param(signal_factory, checklist_db, schema_report) -> None:
    signal = signal_factory("2011-03-09", rr_type="NSEC3PARAM", algorithm=1)

    match, _ = _match(signal, checklist_db, "RFC 5155", schema_report)

    assert match.decision == "valid_match"


def test_rfc4509_matches_a_ds_record_with_digest_type_two(
    signal_factory, checklist_db, schema_report
) -> None:
    signal = signal_factory("2012-03-14", rr_type="DS", algorithm=8, digest_type=2)

    match, _ = _match(signal, checklist_db, "RFC 4509", schema_report)

    assert match.decision == "valid_match"
    assert match.confidence == "high"
    assert "rfc4509_ds_sha256_digest" in match.matched_indicator_ids


def test_rfc4509_does_not_match_a_sha1_digest(
    signal_factory, checklist_db, schema_report
) -> None:
    """Digest type 1 predates RFC 4509; it must fail rather than match weakly."""
    signal = signal_factory("2011-02-15", rr_type="DS", algorithm=8, digest_type=1)

    match, _ = _match(signal, checklist_db, "RFC 4509", schema_report)

    assert match.decision == "no_match"
    assert match.score == 0.0
    assert "rfc4509_ds_sha256_digest" in match.failed_indicator_ids


def test_a_cds_row_with_no_algorithm_is_a_partial_match_for_rfc8078(
    signal_factory, checklist_db, schema_report
) -> None:
    """Nothing observed contradicts RFC 8078; the deciding field is simply absent."""
    signal = signal_factory("2019-04-12", rr_type="CDS")

    match, trace = _match(signal, checklist_db, "RFC 8078", schema_report)

    assert match.decision == "partial_match"
    assert "algorithm" in match.missing_fields
    assert "rfc8078_cds_cdnskey_algorithm_zero" in trace.missing_required_indicator_ids


# --------------------------------------------------------------------------- #
# Operators
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("field", "op", "expected"),
    [
        ("rr_type", "equals", "CDS"),
        ("rr_type", "not_equals", "DNSKEY"),
        ("rr_type", "in", ["CDS", "CDNSKEY"]),
        ("rr_type", "exists", None),
        ("rr_type", "contains", "CD"),
        ("algorithm", "greater_or_equal", 0),
        ("algorithm", "less_or_equal", 13),
    ],
    ids=ALL_OPS,
)
def test_every_operator_passes_on_a_satisfying_observation(
    signal_factory, field: str, op: str, expected
) -> None:
    signal = signal_factory("2020-01-01", rr_type="CDS", algorithm=0)

    evaluation = evaluate_condition(
        IndicatorCondition(field=field, op=op, value=expected), signal
    )

    assert evaluation.passed is True
    assert evaluation.field_present is True
    assert evaluation.explanation


@pytest.mark.parametrize(
    ("field", "op", "expected"),
    [
        ("rr_type", "equals", "DNSKEY"),
        ("rr_type", "not_equals", "CDS"),
        ("rr_type", "in", ["DS", "DNSKEY"]),
        ("algorithm", "greater_or_equal", 5),
        ("algorithm", "less_or_equal", -1),
        ("rr_type", "contains", "NSEC"),
    ],
)
def test_operators_fail_on_a_contradicting_observation(
    signal_factory, field: str, op: str, expected
) -> None:
    signal = signal_factory("2020-01-01", rr_type="CDS", algorithm=0)

    evaluation = evaluate_condition(
        IndicatorCondition(field=field, op=op, value=expected), signal
    )

    assert evaluation.passed is False
    assert evaluation.field_present is True


@pytest.mark.parametrize("op", ALL_OPS)
def test_a_missing_observed_value_fails_every_operator(signal_factory, op: str) -> None:
    """Absence is not evidence: it cannot satisfy any predicate, not even not_equals."""
    signal = signal_factory("2020-01-01", rr_type="CDS")
    expected = ["X"] if op == "in" else ("X" if op in {"equals", "not_equals", "contains"} else 1)

    evaluation = evaluate_condition(
        IndicatorCondition(field="digest_type", op=op, value=expected), signal
    )

    assert evaluation.passed is False
    assert evaluation.field_present is False
    assert evaluation.observed is None
    assert "absent from this observation" in evaluation.explanation
    assert "absence is not evidence" in evaluation.explanation


def test_missing_fields_are_recorded_on_the_indicator_evaluation(signal_factory) -> None:
    signal = signal_factory("2020-01-01", rr_type="CDS")
    indicator = RFCIndicator(
        id="probe",
        description="probe",
        required=True,
        conditions=[
            IndicatorCondition(field="rr_type", op="equals", value="CDS"),
            IndicatorCondition(field="digest_type", op="equals", value=0),
        ],
    )

    evaluation = evaluate_indicator(indicator, signal)

    assert evaluation.matched is False
    assert evaluation.missing_fields == ["digest_type"]
    assert [c.passed for c in evaluation.conditions] == [True, False]


def test_contains_works_on_both_strings_and_lists(signal_factory) -> None:
    signal = signal_factory("2020-01-01", rr_type="CDNSKEY", tags=["ecdsa", "p256"])

    on_string = evaluate_condition(
        IndicatorCondition(field="rr_type", op="contains", value="KEY"), signal
    )
    on_list = evaluate_condition(
        IndicatorCondition(field="tags", op="contains", value="p256"), signal
    )
    absent_member = evaluate_condition(
        IndicatorCondition(field="tags", op="contains", value="ed25519"), signal
    )

    assert on_string.passed is True
    assert on_list.passed is True
    assert absent_member.passed is False


def test_numeric_strings_compare_equal_to_numbers(signal_factory) -> None:
    """The same OpenINTEL column can be exported as text or as an integer."""
    signal = signal_factory("2020-01-01", algorithm="13")

    equals = evaluate_condition(
        IndicatorCondition(field="algorithm", op="equals", value=13), signal
    )
    member = evaluate_condition(
        IndicatorCondition(field="algorithm", op="in", value=[13, 14]), signal
    )

    assert equals.passed is True
    assert member.passed is True


def test_algorithm_zero_never_compares_equal_to_false(signal_factory) -> None:
    """``0`` (the RFC 8078 delete signal) and ``False`` are different claims."""
    signal = signal_factory("2020-01-01", algorithm=0)

    evaluation = evaluate_condition(
        IndicatorCondition(field="algorithm", op="equals", value=False), signal
    )

    assert evaluation.passed is False


def test_a_type_mismatch_fails_with_an_explanation_instead_of_raising(
    signal_factory,
) -> None:
    signal = signal_factory("2020-01-01", rr_type="CDS")

    evaluation = evaluate_condition(
        IndicatorCondition(field="rr_type", op="greater_or_equal", value=1), signal
    )

    assert evaluation.passed is False
    assert evaluation.field_present is True
    assert "type mismatch" in evaluation.explanation


def test_a_malformed_in_condition_is_reported_rather_than_silently_ignored(
    signal_factory,
) -> None:
    signal = signal_factory("2020-01-01", rr_type="CDS")

    evaluation = evaluate_condition(
        IndicatorCondition(field="rr_type", op="in", value="CDS"), signal
    )

    assert evaluation.passed is False
    assert "malformed" in evaluation.explanation


# --------------------------------------------------------------------------- #
# Queryability handling
# --------------------------------------------------------------------------- #


def test_a_non_queryable_indicator_is_skipped_not_failed(signal_factory) -> None:
    signal = signal_factory("2020-01-01", rr_type="DNSKEY")
    indicator = RFCIndicator(
        id="probe",
        description="probe",
        required=True,
        weight=6.0,
        conditions=[IndicatorCondition(field="validator_algorithm_support", op="exists")],
    )

    evaluation = evaluate_indicator(indicator, signal, "non_queryable")

    assert evaluation.skipped is True
    assert evaluation.matched is False
    assert evaluation.conditions == []
    assert evaluation.missing_fields == ["validator_algorithm_support"]
    assert "never tested" in evaluation.explanation


def test_a_partially_queryable_indicator_is_evaluated_and_fails_on_the_absent_field(
    signal_factory, checklist_db, schema_report
) -> None:
    signal = signal_factory("2011-05-24", rr_type="DNSKEY", algorithm=8)

    match, trace = _match(signal, checklist_db, "RFC 4033", schema_report)

    partial = next(
        e for e in match.indicator_evaluations if e.indicator_id == "rfc4033_dnssec_ok_negotiated"
    )
    assert partial.queryability == "partially_queryable"
    assert partial.skipped is False
    assert partial.matched is False
    assert partial.missing_fields == ["dnssec_ok_flag"]
    assert any("partially queryable" in note for note in trace.uncertainty_notes)


def test_rfc8624_skips_its_non_queryable_indicator_but_still_reaches_a_verdict(
    signal_factory, checklist_db, schema_report
) -> None:
    signal = signal_factory("2020-01-01", rr_type="DNSKEY", algorithm=13)

    match, trace = _match(signal, checklist_db, "RFC 8624", schema_report)

    assert trace.skipped_indicator_ids == ["rfc8624_validator_algorithm_support"]
    assert match.decision == "ambiguous"
    assert any(
        "could not be tested against the OpenINTEL corpus" in step
        for step in match.score_breakdown.steps
    ), "a skipped indicator must be reported in the arithmetic, not hidden"


def test_an_indicator_missing_from_the_schema_report_is_warned_about(
    signal_factory, checklist_db
) -> None:
    empty_report = SchemaCheckReport(
        generated_at=datetime(2020, 1, 1),
        checklist_path="checklist.json",
        dictionary_path="dictionary.json",
        dictionary_field_count=0,
        rfc_count=0,
        indicator_count=0,
    )
    rfc = checklist_db.get("RFC 8078")
    assert rfc is not None
    warnings: list[str] = []

    match_signal_to_rfc(
        signal_factory("2018-05-01", rr_type="CDS", algorithm=0),
        rfc,
        empty_report,
        warnings=warnings,
    )

    assert any("absent from the schema report" in message for message in warnings)


# --------------------------------------------------------------------------- #
# Timestamp check
# --------------------------------------------------------------------------- #


def test_check_timestamp_counts_days_after_publication(signal_factory, checklist_db) -> None:
    rfc = checklist_db.get("RFC 8078")
    assert rfc is not None

    check = check_timestamp(signal_factory("2017-03-11", rr_type="CDS"), rfc)

    assert check.valid is True
    assert check.days_after_publication == 10
    assert "10 days after" in check.explanation


def test_an_observation_on_the_publication_date_itself_is_valid(
    signal_factory, checklist_db
) -> None:
    rfc = checklist_db.get("RFC 8078")
    assert rfc is not None

    check = check_timestamp(signal_factory("2017-03-01", rr_type="CDS"), rfc)

    assert check.valid is True
    assert check.days_after_publication == 0


def test_an_observation_one_day_early_is_invalid(signal_factory, checklist_db) -> None:
    rfc = checklist_db.get("RFC 8078")
    assert rfc is not None

    check = check_timestamp(signal_factory("2017-02-28", rr_type="CDS"), rfc)

    assert check.valid is False
    assert check.days_after_publication == -1
    assert "predates" in check.explanation


# --------------------------------------------------------------------------- #
# The whole loop
# --------------------------------------------------------------------------- #


def test_match_all_evaluates_every_signal_against_every_rfc(
    signal_factory, checklist_db, schema_report
) -> None:
    signals = [
        signal_factory("2018-05-01", rr_type="CDS", algorithm=0, digest_type=0),
        signal_factory("2010-06-15", rr_type="NSEC3", algorithm=1),
    ]

    matches, traces = match_all(signals, checklist_db, schema_report)

    assert len(matches) == len(signals) * len(checklist_db.rfcs)
    assert len(traces) == len(matches)
    assert [m.trace_id for m in matches] == [t.trace_id for t in traces]


def test_match_all_sorts_each_signals_best_explanation_first(
    signal_factory, checklist_db, schema_report
) -> None:
    signals = [signal_factory("2018-05-01", rr_type="CDS", algorithm=0, digest_type=0)]

    matches, _ = match_all(signals, checklist_db, schema_report)

    keys = [(m.signal_id, -m.score, m.rfc_id) for m in matches]
    assert keys == sorted(keys)
    assert matches[0].rfc_id == "RFC 8078"


def test_match_all_warns_and_returns_nothing_without_signals(checklist_db) -> None:
    warnings: list[str] = []

    matches, traces = match_all([], checklist_db, None, warnings=warnings)

    assert matches == [] and traces == []
    assert any("No observed signals" in message for message in warnings)


def test_match_all_warns_and_returns_nothing_without_rfcs(signal_factory) -> None:
    warnings: list[str] = []

    matches, traces = match_all(
        [signal_factory("2020-01-01", rr_type="CDS")], RFCChecklistDB(), None, warnings=warnings
    )

    assert matches == [] and traces == []
    assert any("no RFCs" in message for message in warnings)


def test_one_observation_may_evidence_several_rfcs(
    signal_factory, checklist_db, schema_report
) -> None:
    """A CDS with algorithm 0 really is both an RFC 7344 record and an RFC 8078 signal."""
    signals = [signal_factory("2018-05-01", rr_type="CDS", algorithm=0, digest_type=0)]

    matches, _ = match_all(signals, checklist_db, schema_report)

    valid = {m.rfc_id for m in matches if m.decision == "valid_match"}
    assert {"RFC 7344", "RFC 8078"} <= valid
