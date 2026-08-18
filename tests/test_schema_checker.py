"""Queryability cross-check: what the OpenINTEL corpus can and cannot answer.

The schema checker runs before any measurement data is read, so these tests are
about the *checklist and dictionary*, not about observations. The distinctions
that matter are: a field that exists (queryable), a field that does not exist
(non-queryable), a mixture where the discriminating value survives (partially
queryable), and an indicator the checklist itself declares not uniquely
attributable (ambiguous).
"""

from __future__ import annotations

import pytest

from openintel_rfc.models import (
    IndicatorCondition,
    OpenINTELDictionary,
    RFCChecklistDB,
    SchemaCheckReport,
)
from openintel_rfc.schema_checker import (
    QUERYABILITY_ORDER,
    check_condition,
    check_indicator,
    check_schema,
    queryable_field_names,
)
from openintel_rfc.utils import PipelineError


def _check(report: SchemaCheckReport, indicator_id: str):
    for check in report.indicators:
        if check.indicator_id == indicator_id:
            return check
    raise AssertionError(f"indicator {indicator_id} is absent from the schema report")


# --------------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------------- #


def test_rfc8078_delete_signal_indicator_is_queryable_when_rr_type_and_algorithm_exist(
    schema_report: SchemaCheckReport,
) -> None:
    check = _check(schema_report, "rfc8078_cds_cdnskey_algorithm_zero")

    assert check.queryability == "queryable"
    assert check.rfc_id == "RFC 8078"
    assert set(check.present_fields) == {"rr_type", "algorithm"}
    assert check.missing_fields == []
    assert "queryable" in check.reasoning
    assert "rr_type" in check.reasoning and "algorithm" in check.reasoning


def test_indicator_is_non_queryable_when_a_required_field_is_absent_from_the_dictionary(
    schema_report: SchemaCheckReport,
) -> None:
    check = _check(schema_report, "rfc8624_validator_algorithm_support")

    assert check.queryability == "non_queryable"
    assert check.missing_fields == ["validator_algorithm_support"]
    assert "non-queryable" in check.reasoning
    assert "validator_algorithm_support" in check.reasoning
    assert check in schema_report.non_queryable_indicators


def test_rfc4033_dnssec_ok_negotiated_is_partially_queryable(
    schema_report: SchemaCheckReport,
) -> None:
    """One field survives and another RFC 4033 indicator relies on it."""
    check = _check(schema_report, "rfc4033_dnssec_ok_negotiated")

    assert check.queryability == "partially_queryable"
    assert check.present_fields == ["rr_type"]
    assert check.missing_fields == ["dnssec_ok_flag"]
    assert "partially queryable" in check.reasoning
    # Neither list file claims it: it is neither fully answerable nor hopeless.
    assert check not in schema_report.queryable_indicators
    assert check not in schema_report.non_queryable_indicators


def test_rfc8624_recommended_signing_algorithm_is_ambiguous(
    schema_report: SchemaCheckReport,
) -> None:
    check = _check(schema_report, "rfc8624_recommended_signing_algorithm")

    assert check.queryability == "ambiguous"
    assert check.missing_fields == []
    assert "ambiguous" in check.reasoning


def test_every_indicator_is_classified_and_counted(
    schema_report: SchemaCheckReport, checklist_db: RFCChecklistDB
) -> None:
    expected_indicators = sum(len(rfc.indicators) for rfc in checklist_db.rfcs)

    assert schema_report.indicator_count == expected_indicators
    assert len(schema_report.indicators) == expected_indicators
    assert schema_report.rfc_count == len(checklist_db.rfcs)
    assert set(schema_report.counts_by_queryability) == set(QUERYABILITY_ORDER)
    assert sum(schema_report.counts_by_queryability.values()) == expected_indicators


def test_indicators_are_sorted_by_rfc_then_indicator_id(
    schema_report: SchemaCheckReport,
) -> None:
    keys = [(c.rfc_id, c.indicator_id) for c in schema_report.indicators]
    assert keys == sorted(keys)


def test_status_for_returns_none_for_an_unknown_indicator(
    schema_report: SchemaCheckReport,
) -> None:
    assert schema_report.status_for("rfc9999_not_a_real_indicator") is None


# --------------------------------------------------------------------------- #
# Condition-level checks
# --------------------------------------------------------------------------- #


def test_check_condition_records_the_field_type_for_a_known_field(
    dictionary: OpenINTELDictionary, checklist_db: RFCChecklistDB
) -> None:
    rfc = checklist_db.get("RFC 8078")
    assert rfc is not None
    condition = IndicatorCondition(field="algorithm", op="equals", value=0)

    result = check_condition(condition, dictionary, rfc)

    assert result.field_exists is True
    assert result.field_type == "integer"
    assert result.type_compatible is True
    assert "algorithm" in result.explanation


def test_check_condition_reports_an_unknown_field_without_raising(
    dictionary: OpenINTELDictionary, checklist_db: RFCChecklistDB
) -> None:
    rfc = checklist_db.get("RFC 4033")
    assert rfc is not None
    condition = IndicatorCondition(field="dnssec_ok_flag", op="equals", value=True)

    result = check_condition(condition, dictionary, rfc)

    assert result.field_exists is False
    assert result.field_type is None
    assert "dnssec_ok_flag" in result.explanation
    assert "field_present=False" in result.explanation


def test_check_condition_flags_an_ordering_operator_on_a_string_field(
    dictionary: OpenINTELDictionary, checklist_db: RFCChecklistDB
) -> None:
    """``rr_type`` is a string, so ``>=`` cannot apply meaningfully to it."""
    rfc = checklist_db.get("RFC 7344")
    assert rfc is not None
    condition = IndicatorCondition(field="rr_type", op="greater_or_equal", value=1)

    result = check_condition(condition, dictionary, rfc)

    assert result.field_exists is True
    assert result.type_compatible is False
    assert "type-suspect" in result.explanation


def test_check_indicator_attaches_an_availability_warning_when_a_field_postdates_the_rfc(
    dictionary: OpenINTELDictionary, checklist_db: RFCChecklistDB
) -> None:
    """``flags`` is only available from 2016, long after RFC 4033 was published."""
    rfc = checklist_db.get("RFC 4033")
    assert rfc is not None
    indicator = rfc.indicators[0].model_copy(deep=True)
    indicator.conditions = [IndicatorCondition(field="flags", op="exists")]

    check = check_indicator(rfc, indicator, dictionary)

    assert check.queryability == "queryable"
    assert any("only available from 2016-01-01" in w for w in check.warnings)


# --------------------------------------------------------------------------- #
# Report-level warnings
# --------------------------------------------------------------------------- #


def test_report_warns_about_fields_the_dictionary_does_not_define(
    schema_report: SchemaCheckReport,
) -> None:
    joined = "\n".join(schema_report.warnings)

    assert "'dnssec_ok_flag'" in joined
    assert "'validator_algorithm_support'" in joined
    assert "unanswerable" in joined


def test_report_warns_that_non_queryable_indicators_will_be_skipped(
    schema_report: SchemaCheckReport,
) -> None:
    assert any(
        "rfc8624_validator_algorithm_support" in w and "skipped during matching" in w
        for w in schema_report.warnings
    )


def test_report_warns_that_late_dictionary_fields_bound_early_adoption(
    schema_report: SchemaCheckReport,
) -> None:
    """RFC 4033 predates every OpenINTEL field its indicators rely on."""
    assert any(
        "RFC 4033 was published 2005-03-01" in w and "2010-01-01" in w
        for w in schema_report.warnings
    )
    # `flags` is used by no indicator yet, so it appears in the forward-looking form.
    assert any("`flags` (from 2016-01-01)" in w for w in schema_report.warnings)


def test_unused_dictionary_fields_are_reported(schema_report: SchemaCheckReport) -> None:
    """A dictionary field no indicator uses is reported, so the two can be kept in step.

    `flags` stopped being unused at checklist 0.2.0, which added the RFC 5011
    REVOKE-bit and RFC 6781 SEP-bit indicators. `key_tag` is the field that is
    still defined and still unreferenced.
    """
    assert "key_tag" in schema_report.unused_dictionary_fields
    assert "rr_type" not in schema_report.unused_dictionary_fields
    assert "flags" not in schema_report.unused_dictionary_fields


def test_check_schema_appends_to_a_caller_supplied_warning_list(
    checklist_db: RFCChecklistDB, dictionary: OpenINTELDictionary
) -> None:
    collected = ["an earlier warning from the caller"]

    report = check_schema(
        checklist_db,
        dictionary,
        checklist_path="checklist.json",
        dictionary_path="dictionary.json",
        warnings=collected,
    )

    assert collected[0] == "an earlier warning from the caller"
    assert len(collected) > 1
    assert report.warnings == collected


def test_check_schema_raises_when_the_checklist_has_no_rfcs(
    dictionary: OpenINTELDictionary,
) -> None:
    with pytest.raises(PipelineError, match="contains no RFCs"):
        check_schema(
            RFCChecklistDB(),
            dictionary,
            checklist_path="empty.json",
            dictionary_path="dictionary.json",
        )


# --------------------------------------------------------------------------- #
# What the Parquet reader is asked to load
# --------------------------------------------------------------------------- #


def test_queryable_field_names_lists_only_evaluable_fields(
    schema_report: SchemaCheckReport,
) -> None:
    names = queryable_field_names(schema_report)

    assert names == sorted(names), "the field list must be deterministic"
    # Every field an evaluable indicator rests on, and nothing else. Asserted as a
    # superset plus explicit exclusions rather than an exact list, so adding an RFC
    # that uses a new field is not a failure.
    assert {"algorithm", "digest_type", "rr_type"} <= set(names)
    assert "domain" not in names, "provenance is not evidence"
    # The non-queryable indicator's surviving `rr_type` is only there because
    # other, evaluable indicators use it -- not on its own behalf.
    assert "validator_algorithm_support" not in names
    assert "dnssec_ok_flag" not in names
