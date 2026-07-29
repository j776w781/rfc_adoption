"""The review queue and the deterministic verifier that feeds it.

The queue exists for everything the pipeline is not entitled to decide alone:
observations that predate their RFC, indicators the corpus cannot answer,
matches that are not uniquely attributable, and rankings too close to separate.
Each item has to name concrete evidence and a concrete action, so the tests
check the content of the rows, not only their presence.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openintel_rfc import config
from openintel_rfc.llm_verifier import (
    DEFAULT_VERIFIER_NAME,
    DeterministicVerifier,
    LLMVerifier,
    StubLLMVerifier,
    available_verifiers,
    build_prompt,
    get_verifier,
    verify_traces,
)
from openintel_rfc.matcher import match_all, match_signal_to_rfc
from openintel_rfc.ranking import close_ranking_pairs, rank_candidates
from openintel_rfc.review_queue import (
    ITEM_TYPES,
    apply_review_status,
    build_review_queue,
    default_status_path,
    load_review_status,
    review_queue_to_rows,
    save_review_status,
    severity_counts,
)
from openintel_rfc.utils import PipelineError


@pytest.fixture
def mixed_run(signal_factory, checklist_db, schema_report):
    """A handful of observations covering every review-worthy situation."""
    signals = [
        # Valid RFC 8078 delete signal.
        signal_factory("2018-05-01", signal_id="sig_0001", rr_type="CDS", algorithm=0, digest_type=0),
        # The same shape, before RFC 8078 existed.
        signal_factory("2016-01-15", signal_id="sig_0002", rr_type="CDS", algorithm=0, digest_type=0),
        # CDS with no algorithm at all: partial, missing required field.
        signal_factory("2019-04-12", signal_id="sig_0003", rr_type="CDS"),
        # Algorithm 13: RFC 6605 and the ambiguous RFC 8624 indicators.
        signal_factory("2020-01-01", signal_id="sig_0004", rr_type="DNSKEY", algorithm=13),
    ]
    matches, traces = match_all(signals, checklist_db, schema_report)
    ranked = rank_candidates(matches, checklist_db)
    items = build_review_queue(
        schema_report=schema_report,
        matches=matches,
        traces=traces,
        ranked=ranked,
        db=checklist_db,
        close_pairs=close_ranking_pairs(ranked),
    )
    return {"matches": matches, "traces": traces, "ranked": ranked, "items": items}


def _of_type(items, item_type: str):
    return [item for item in items if item.item_type == item_type]


# --------------------------------------------------------------------------- #
# Required coverage
# --------------------------------------------------------------------------- #


def test_the_queue_includes_timestamp_invalid_matches(mixed_run) -> None:
    invalid = _of_type(mixed_run["items"], "timestamp_invalid_match")

    assert invalid, "pre-publication observations must reach a human"
    rfc8078 = next(item for item in invalid if "RFC 8078" in item.affected_rfc_ids)
    assert rfc8078.severity == "high"
    assert "sig_0002" in rfc8078.affected_signal_ids
    assert "was published on 2017-03-01" in rfc8078.reason
    assert "forfeited" in rfc8078.reason
    assert rfc8078.suggested_action, "an item without an action is not actionable"
    assert "RFC 7344" in rfc8078.evidence["alternative_valid_rfc_ids"]


def test_the_queue_includes_non_queryable_indicators(mixed_run) -> None:
    non_queryable = _of_type(mixed_run["items"], "non_queryable_indicator")

    assert len(non_queryable) == 1
    item = non_queryable[0]
    assert item.severity == "high"
    assert item.affected_rfc_ids == ["RFC 8624"]
    assert item.affected_fields == ["validator_algorithm_support"]
    assert "cannot be evaluated at all" in item.reason
    assert "openintel_native_fields" in item.suggested_action
    assert item.evidence["queryability"] == "non_queryable"


def test_the_queue_includes_partially_queryable_indicators(mixed_run) -> None:
    partial = _of_type(mixed_run["items"], "partially_queryable_indicator")

    assert len(partial) == 1
    item = partial[0]
    assert item.severity == "medium"
    assert item.affected_rfc_ids == ["RFC 4033"]
    assert item.affected_fields == ["dnssec_ok_flag"]
    assert "only partially queryable" in item.reason


def test_the_queue_includes_ambiguous_indicators(mixed_run) -> None:
    ambiguous = _of_type(mixed_run["items"], "ambiguous_indicator")

    rfc8624 = [item for item in ambiguous if "RFC 8624" in item.affected_rfc_ids]
    assert rfc8624, "RFC 8624's indicators are ambiguous by construction"
    assert all(item.severity == "medium" for item in rfc8624)
    assert any("equally well explained by another RFC" in item.reason for item in rfc8624)
    assert any("Decide attribution by hand" in item.suggested_action for item in rfc8624)


def test_the_queue_includes_partial_matches_and_missing_required_fields(mixed_run) -> None:
    partial = _of_type(mixed_run["items"], "partial_match")
    missing = _of_type(mixed_run["items"], "missing_required_field")

    rfc8078_partial = next(item for item in partial if item.affected_rfc_ids == ["RFC 8078"])
    assert rfc8078_partial.severity == "high", "very_high specificity raises the priority"
    assert "sig_0003" in rfc8078_partial.affected_signal_ids
    assert "algorithm" in rfc8078_partial.affected_fields

    rfc8078_missing = next(item for item in missing if item.affected_fields == ["algorithm"] and item.affected_rfc_ids == ["RFC 8078"])
    assert "cds_algorithm" in rfc8078_missing.suggested_action, "names the real Parquet column"


def test_every_item_type_emitted_is_declared(mixed_run) -> None:
    assert {item.item_type for item in mixed_run["items"]} <= set(ITEM_TYPES)


def test_every_item_carries_a_reason_and_an_action(mixed_run) -> None:
    for item in mixed_run["items"]:
        assert item.reason.strip(), f"{item.item_id} has no reason"
        assert item.suggested_action.strip(), f"{item.item_id} has no suggested action"
        assert item.status == "unresolved"


def test_item_ids_are_dense_and_ordered_by_severity(mixed_run) -> None:
    items = mixed_run["items"]

    assert [item.item_id for item in items] == [
        f"rev_{index:04d}" for index in range(1, len(items) + 1)
    ]
    ranks = {"high": 0, "medium": 1, "low": 2}
    assert [ranks[item.severity] for item in items] == sorted(
        ranks[item.severity] for item in items
    )


def test_the_queue_is_reproducible_for_the_same_inputs(
    signal_factory, checklist_db, schema_report
) -> None:
    def build() -> list[tuple[str, str, str]]:
        signals = [
            signal_factory("2016-01-15", signal_id="sig_0001", rr_type="CDS", algorithm=0),
            signal_factory("2018-05-01", signal_id="sig_0002", rr_type="CDS", algorithm=0),
        ]
        matches, traces = match_all(signals, checklist_db, schema_report)
        ranked = rank_candidates(matches, checklist_db)
        items = build_review_queue(
            schema_report=schema_report,
            matches=matches,
            traces=traces,
            ranked=ranked,
            db=checklist_db,
        )
        return [(item.item_id, item.item_type, item.reason) for item in items]

    assert build() == build()


def test_severity_counts_always_reports_all_three_levels(mixed_run) -> None:
    counts = severity_counts(mixed_run["items"])

    assert set(counts) == {"high", "medium", "low"}
    assert sum(counts.values()) == len(mixed_run["items"])
    assert counts["high"] >= 1


def test_review_queue_to_rows_keeps_the_evidence_block(mixed_run) -> None:
    rows = review_queue_to_rows(mixed_run["items"])

    assert len(rows) == len(mixed_run["items"])
    row = next(r for r in rows if r["item_type"] == "timestamp_invalid_match")
    evidence = json.loads(row["evidence"])
    assert evidence["rfc_id"].startswith("RFC ")
    assert "forfeited_score_total" in evidence
    assert row["affected_rfc_ids"], "the affected RFCs are joined into one cell"
    assert row["verification_status"] in {"accepted", "rejected", "needs_manual_review", ""}


def test_close_ranking_items_are_raised_when_two_candidates_are_inseparable(
    mixed_run,
) -> None:
    close = _of_type(mixed_run["items"], "close_ranking")

    for item in close:
        assert len(item.affected_rfc_ids) == 2
        assert "not separable on score alone" in item.reason
        assert "Do not report" in item.suggested_action


# --------------------------------------------------------------------------- #
# Reviewer status persistence
# --------------------------------------------------------------------------- #


def test_review_status_round_trips_through_disk(tmp_path: Path, mixed_run) -> None:
    path = default_status_path(tmp_path)
    statuses = {mixed_run["items"][0].item_id: "accepted", "rev_0002": "rejected"}

    save_review_status(path, statuses)

    assert path.name == config.OUTPUT_FILES["review_queue_status"]
    assert load_review_status(path) == statuses


def test_loading_a_missing_status_file_yields_an_empty_mapping(tmp_path: Path) -> None:
    assert load_review_status(tmp_path / "nothing.json") == {}


def test_an_unknown_status_value_is_refused_rather_than_stored(tmp_path: Path) -> None:
    with pytest.raises(PipelineError, match="unknown status"):
        save_review_status(tmp_path / "status.json", {"rev_0001": "maybe"})


def test_apply_review_status_returns_copies_with_the_status_applied(mixed_run) -> None:
    items = mixed_run["items"]
    updated = apply_review_status(items, {items[0].item_id: "accepted"})

    assert updated[0].status == "accepted"
    assert items[0].status == "unresolved", "the originals are not mutated"
    assert [item.item_id for item in updated] == [item.item_id for item in items]


def test_apply_review_status_tolerates_ids_from_an_older_queue(mixed_run) -> None:
    updated = apply_review_status(mixed_run["items"], {"rev_9999": "accepted"})

    assert all(item.status == "unresolved" for item in updated)


# --------------------------------------------------------------------------- #
# The deterministic verifier
# --------------------------------------------------------------------------- #


def _trace_for(signal_factory, checklist_db, schema_report, rfc_id: str, timestamp: str, **fields):
    rfc = checklist_db.get(rfc_id)
    assert rfc is not None
    return match_signal_to_rfc(signal_factory(timestamp, **fields), rfc, schema_report)[1]


def test_the_default_verifier_is_the_offline_deterministic_backend() -> None:
    verifier = get_verifier()

    assert isinstance(verifier, DeterministicVerifier)
    assert verifier.name == DEFAULT_VERIFIER_NAME
    assert DEFAULT_VERIFIER_NAME in available_verifiers()


def test_the_verifier_accepts_a_high_confidence_valid_match(
    signal_factory, checklist_db, schema_report
) -> None:
    trace = _trace_for(
        signal_factory, checklist_db, schema_report, "RFC 8078", "2018-05-01",
        rr_type="CDS", algorithm=0, digest_type=0,
    )

    verification = DeterministicVerifier().verify(trace=trace)

    assert trace.confidence in config.LLM_AUTO_ACCEPT_CONFIDENCES
    assert verification.verification_status == "accepted"
    assert verification.backend == "deterministic"
    assert verification.rfc_id == "RFC 8078"
    assert verification.explanation.startswith("Accepted:")
    assert "rfc8078_cds_cdnskey_algorithm_zero" in verification.explanation


def test_the_verifier_rejects_a_timestamp_invalid_match(
    signal_factory, checklist_db, schema_report
) -> None:
    trace = _trace_for(
        signal_factory, checklist_db, schema_report, "RFC 8078", "2016-01-15",
        rr_type="CDS", algorithm=0, digest_type=0,
    )

    verification = DeterministicVerifier().verify(trace=trace)

    assert verification.verification_status == "rejected"
    assert verification.explanation.startswith("Rejected:")
    assert "17.25" in verification.explanation, "it names the score that was forfeited"


def test_the_verifier_flags_an_ambiguous_match_for_manual_review(
    signal_factory, checklist_db, schema_report
) -> None:
    rfc = checklist_db.get("RFC 8624")
    assert rfc is not None
    trace = _trace_for(
        signal_factory, checklist_db, schema_report, "RFC 8624", "2020-01-01",
        rr_type="DNSKEY", algorithm=13,
    )

    verification = DeterministicVerifier().verify(trace=trace, rfc=rfc)

    assert trace.decision == "ambiguous"
    assert verification.verification_status == "needs_manual_review"
    assert "flagged ambiguous" in verification.explanation
    assert "rfc8624_recommended_signing_algorithm" in verification.explanation


def test_the_verifier_flags_a_partial_match_for_manual_review(
    signal_factory, checklist_db, schema_report
) -> None:
    trace = _trace_for(
        signal_factory, checklist_db, schema_report, "RFC 8078", "2019-04-12", rr_type="CDS"
    )

    verification = DeterministicVerifier().verify(trace=trace)

    assert verification.verification_status == "needs_manual_review"
    assert "cannot distinguish non-adoption from missing data" in verification.explanation


def test_the_verifier_rejects_a_no_match(
    signal_factory, checklist_db, schema_report
) -> None:
    trace = _trace_for(
        signal_factory, checklist_db, schema_report, "RFC 5155", "2018-05-01",
        rr_type="DNSKEY", algorithm=8,
    )

    verification = DeterministicVerifier().verify(trace=trace)

    assert verification.verification_status == "rejected"
    assert "no indicator of RFC 5155 matched" in verification.explanation


def test_verify_traces_returns_one_verdict_per_trace_sorted_by_trace_id(
    mixed_run, checklist_db
) -> None:
    verifications = verify_traces(mixed_run["traces"], checklist_db)

    assert set(verifications) == {trace.trace_id for trace in mixed_run["traces"]}
    assert list(verifications) == sorted(verifications)


def test_verify_traces_refuses_duplicate_trace_ids(mixed_run, checklist_db) -> None:
    trace = mixed_run["traces"][0]

    with pytest.raises(PipelineError, match="Duplicate trace_id"):
        verify_traces([trace, trace], checklist_db)


def test_build_prompt_inlines_everything_a_model_would_need(
    signal_factory, checklist_db, schema_report
) -> None:
    rfc = checklist_db.get("RFC 8078")
    assert rfc is not None
    trace = _trace_for(
        signal_factory, checklist_db, schema_report, "RFC 8078", "2018-05-01",
        rr_type="CDS", algorithm=0, digest_type=0,
    )

    prompt = build_prompt(trace, rfc)

    assert "rfc_publication_date: 2017-03-01T00:00:00" in prompt
    assert "observation_timestamp: 2018-05-01T00:00:00" in prompt
    assert "## Publication-date cutoff" in prompt
    assert "PASS rr_type in" in prompt
    assert "## Score derivation" in prompt
    assert "verification_status" in prompt


def test_the_stub_backend_refuses_rather_than_inventing_a_verdict(
    signal_factory, checklist_db, schema_report
) -> None:
    trace = _trace_for(
        signal_factory, checklist_db, schema_report, "RFC 8078", "2018-05-01",
        rr_type="CDS", algorithm=0, digest_type=0,
    )
    verifier = StubLLMVerifier()

    with pytest.raises(PipelineError, match="No LLM backend is configured"):
        verifier.verify(trace=trace)

    assert isinstance(verifier, LLMVerifier)
    assert verifier.last_prompt is not None, "the prompt is still available for inspection"


def test_an_unknown_verifier_name_is_refused() -> None:
    with pytest.raises(PipelineError, match="Unknown verifier"):
        get_verifier("not_a_backend")


# --------------------------------------------------------------------------- #
# The real run
# --------------------------------------------------------------------------- #


def test_the_analyze_run_writes_a_populated_review_queue(analyzed_output: Path) -> None:
    payload = json.loads(
        (analyzed_output / config.OUTPUT_FILES["review_queue"]).read_text(encoding="utf-8")
    )

    assert payload["count"] == len(payload["review_items"])
    types = {item["item_type"] for item in payload["review_items"]}
    assert "timestamp_invalid_match" in types
    assert "non_queryable_indicator" in types
    assert "partially_queryable_indicator" in types
