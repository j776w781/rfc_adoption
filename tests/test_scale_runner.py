"""Tests for :mod:`openintel_rfc.scale_runner`.

The important test here is :func:`test_sql_and_python_agree_on_decision_counts`
and its two siblings. They run **both** engines over the same sample Parquet
file -- the SQL path that a real 10^10-row run uses, and the existing Python
``match_all`` path that the MVP uses -- and require identical per-(rfc_id,
decision) counts, identical first-seen dates, and identical scores for the rows
the SQL path sampled as exemplars. A scale run whose numbers do not reproduce the
reference implementation on 73 hand-built rows cannot be trusted on a corpus
nobody can check by hand.

The rest of the file covers the properties that make a multi-day run survivable:
the prefilter really does drop non-DNSSEC records, a completed partition is
skipped on resume, a corrupt checkpoint is recomputed rather than believed, and
the exemplar sample is the same on every run over the same partition.

Nothing here imports ``openintel_source``: the tests drive the runner with local
Parquet paths through :class:`~openintel_rfc.scale_runner.LocalPartition`.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import pytest

from openintel_rfc import sql_compiler
from openintel_rfc.matcher import match_all
from openintel_rfc.models import ObservedSignal, RFCMatch
from openintel_rfc.parquet_reader import describe_parquet, read_parquet
from openintel_rfc.ranking import ADOPTION_DECISIONS
from openintel_rfc.scale_runner import (
    AggregateTable,
    LocalPartition,
    ScaleRunConfig,
    merge_checkpoints,
    process_partition,
    run_scale_analysis,
)
from openintel_rfc.schema_checker import queryable_field_names
from openintel_rfc.signal_extractor import SIGNAL_FIELDS, extract_signals


# --------------------------------------------------------------------------- #
# Shared setup
# --------------------------------------------------------------------------- #


def _needed_fields(schema_report) -> list[str]:
    return sorted(
        set(queryable_field_names(schema_report))
        | {"timestamp", "domain", "zone", "source", "measurement_id"}
        | set(SIGNAL_FIELDS)
    )


@pytest.fixture(scope="module")
def compiled_scan(checklist_db, dictionary, schema_report, sample_parquet_path):
    """Column expressions and the compiled checklist for the sample fixture."""
    columns = [c["name"] for c in describe_parquet(sample_parquet_path)["columns"]]
    column_expr = sql_compiler.build_column_expressions(
        dictionary, _needed_fields(schema_report), columns
    )
    compiled = sql_compiler.compile_checklist(checklist_db, column_expr, schema_report)
    return column_expr, compiled


@pytest.fixture(scope="module")
def scale_result(
    tmp_path_factory, checklist_db, dictionary, schema_report, sample_parquet_path
):
    """One full scale run over the sample Parquet, shared by several tests."""
    root = tmp_path_factory.mktemp("scale_run")
    partition = LocalPartition.from_paths(
        [sample_parquet_path], partition_id="sample", source="zonefile-sample"
    )
    config = ScaleRunConfig(
        out=root / "out",
        checkpoint_dir=root / "checkpoints",
        access=None,
        exemplars_per_group=5,
        checklists="tests",
        dictionary="tests",
    )
    warnings: list[str] = []
    result = run_scale_analysis(
        config, checklist_db, dictionary, schema_report, warnings=warnings,
        partitions=[partition],
    )
    aggregates = merge_checkpoints(root / "checkpoints")
    return result, aggregates, warnings, root


@pytest.fixture(scope="module")
def python_matches(
    checklist_db, dictionary, schema_report, sample_parquet_path
) -> tuple[list[ObservedSignal], list[RFCMatch]]:
    """The MVP path over the same file: the reference the SQL path must reproduce."""
    frame = read_parquet(sample_parquet_path, dictionary, _needed_fields(schema_report))
    signals = extract_signals(frame)
    matches, _traces = match_all(signals, checklist_db, schema_report)
    return signals, matches


def _python_decision_counts(matches) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    for match in matches:
        key = (match.rfc_id, match.decision)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _signal_key(signal: ObservedSignal) -> tuple[Any, ...]:
    """Identify an observation by its content, not by its minted id.

    The two engines number their signals independently -- the SQL path only ever
    materializes the sampled rows -- so a comparison has to key on what was
    observed.
    """
    return (
        signal.timestamp,
        signal.domain,
        signal.zone,
        signal.source,
        signal.measurement_id,
        signal.fields.get("rr_type"),
        signal.fields.get("algorithm"),
        signal.fields.get("digest_type"),
        signal.fields.get("key_tag"),
        signal.fields.get("flags"),
    )


# --------------------------------------------------------------------------- #
# Cross-validation: the SQL engine against the Python engine
# --------------------------------------------------------------------------- #


def test_sql_and_python_agree_on_decision_counts(scale_result, python_matches):
    """Every (rfc_id, decision) group must have the same size in both engines."""
    _result, aggregates, _warnings, _root = scale_result
    _signals, matches = python_matches

    sql_counts = aggregates.decision_counts()
    py_counts = _python_decision_counts(matches)

    assert set(sql_counts) == set(py_counts), (
        "the two engines disagree about which (rfc_id, decision) groups exist: "
        f"SQL only {sorted(set(sql_counts) - set(py_counts))}, "
        f"Python only {sorted(set(py_counts) - set(sql_counts))}"
    )
    disagreements = {
        key: (sql_counts[key], py_counts[key])
        for key in sorted(sql_counts)
        if sql_counts[key] != py_counts[key]
    }
    assert not disagreements, f"per-(rfc_id, decision) counts differ: {disagreements}"

    # Sanity floor: the comparison must actually have compared something.
    assert sum(py_counts.values()) == 73 * 8


def test_sql_and_python_agree_on_first_seen(scale_result, python_matches):
    """``first_seen`` per RFC must be identical, decision filter included."""
    _result, aggregates, _warnings, _root = scale_result
    _signals, matches = python_matches

    python_first: dict[str, datetime] = {}
    for match in matches:
        if match.decision not in ADOPTION_DECISIONS:
            continue
        current = python_first.get(match.rfc_id)
        if current is None or match.observation_timestamp < current:
            python_first[match.rfc_id] = match.observation_timestamp

    rfc_ids = {row.rfc_id for row in aggregates.rfc_rows()}
    disagreements = {
        rfc_id: (aggregates.first_seen(rfc_id), python_first.get(rfc_id))
        for rfc_id in sorted(rfc_ids)
        if aggregates.first_seen(rfc_id) != python_first.get(rfc_id)
    }
    assert not disagreements, f"first_seen differs per RFC: {disagreements}"
    assert python_first, "the fixture must produce at least one adoption match"


def test_exemplar_scores_match_the_python_matcher(
    scale_result, python_matches, checklist_db
):
    """Each sampled exemplar must score exactly what the MVP scores that row."""
    result, _aggregates, _warnings, _root = scale_result
    signals, matches = python_matches

    reference = {(_signal_key(s), m.rfc_id): m for s in signals for m in matches if m.signal_id == s.signal_id}
    by_signal = {s.signal_id: _signal_key(s) for s in result.signals}

    compared = 0
    disagreements: list[str] = []
    for match in result.matches:
        key = (by_signal[match.signal_id], match.rfc_id)
        expected = reference.get(key)
        assert expected is not None, f"exemplar {match.signal_id} is not a row of the fixture"
        compared += 1
        if (match.score, match.decision, match.confidence) != (
            expected.score,
            expected.decision,
            expected.confidence,
        ):
            disagreements.append(
                f"{match.rfc_id} on {by_signal[match.signal_id]}: "
                f"SQL path {match.decision}/{match.score}/{match.confidence} vs "
                f"Python {expected.decision}/{expected.score}/{expected.confidence}"
            )
    assert not disagreements, "exemplar scores differ:\n" + "\n".join(disagreements)
    assert compared == len(result.signals) * len(checklist_db.rfcs)


def test_ranked_candidates_reproduce_the_reference_ranking(
    scale_result, python_matches, checklist_db
):
    """The corpus-scale ranking must be the MVP's ranking, with exact counts."""
    from openintel_rfc.ranking import rank_candidates

    result, _aggregates, _warnings, _root = scale_result
    _signals, matches = python_matches
    reference = rank_candidates(matches, checklist_db)

    assert [c.rfc_id for c in result.ranked_candidates] == [c.rfc_id for c in reference]
    for scaled, expected in zip(result.ranked_candidates, reference):
        assert scaled.score == expected.score
        assert scaled.confidence == expected.confidence
        assert scaled.decision == expected.decision
        # These come from the aggregates, not from the exemplars, and must be the
        # whole-corpus figures rather than the sample's.
        assert scaled.supporting_signal_count == expected.supporting_signal_count
        assert scaled.valid_match_count == expected.valid_match_count
        assert scaled.timestamp_invalid_count == expected.timestamp_invalid_count
        assert scaled.first_seen == expected.first_seen


def test_timeline_matches_the_reference_timeline(scale_result, python_matches, checklist_db):
    from openintel_rfc.timeline import build_timeline

    result, _aggregates, _warnings, _root = scale_result
    _signals, matches = python_matches
    reference = {e.rfc_id: e for e in build_timeline(matches, checklist_db)}

    assert {e.rfc_id for e in result.timeline} == set(reference)
    for entry in result.timeline:
        expected = reference[entry.rfc_id]
        assert entry.first_seen == expected.first_seen
        assert entry.last_seen == expected.last_seen
        assert entry.observation_count == expected.observation_count
        assert [b.period for b in entry.monthly_counts] == [
            b.period for b in expected.monthly_counts
        ]
        assert [b.count for b in entry.monthly_counts] == [
            b.count for b in expected.monthly_counts
        ]


# --------------------------------------------------------------------------- #
# Honesty of the aggregate output
# --------------------------------------------------------------------------- #


def test_result_never_presents_exemplars_as_the_corpus(scale_result):
    result, aggregates, warnings, _root = scale_result
    assert len(result.signals) < aggregates.rows_scanned
    assert any("exemplar" in message for message in result.warnings)
    for candidate in result.ranked_candidates:
        assert "Corpus total" in candidate.reasoning_summary
    for entry in result.timeline:
        if entry.observation_count:
            assert "lower bound" in entry.notes


def test_result_is_shape_compatible_with_the_mvp(scale_result, tmp_path):
    """``exporters`` and ``report`` must work on a scale result unchanged."""
    from openintel_rfc.exporters import export_analysis
    from openintel_rfc.report import render_report

    result, _aggregates, _warnings, _root = scale_result
    markdown = render_report(result)
    written = export_analysis(result, tmp_path / "out", report_md=markdown)
    assert (tmp_path / "out" / "ranked_candidates.json").is_file()
    assert (tmp_path / "out" / "adoption_timeline.json").is_file()
    assert (tmp_path / "out" / "reasoning_traces.json").is_file()
    assert written


def test_traces_are_real_reasoning_traces(scale_result):
    """Explanations come from the existing reasoning module, not a second one."""
    result, _aggregates, _warnings, _root = scale_result
    assert result.traces
    for trace in result.traces:
        assert trace.reasoning_summary
        assert trace.score_breakdown.steps
        assert trace.timestamp_check.explanation


# --------------------------------------------------------------------------- #
# The prefilter
# --------------------------------------------------------------------------- #


def _write_mixed_parquet(path: Path) -> None:
    """A file that is mostly the record types a DNSSEC checklist can never match."""
    rows = [
        ("2019-01-01", "a.example.com", "com", "A", None),
        ("2019-01-02", "b.example.com", "com", "AAAA", None),
        ("2019-01-03", "c.example.com", "com", "MX", None),
        ("2019-01-04", "d.example.com", "com", "TXT", None),
        ("2019-01-05", "e.example.com", "com", "NS", None),
        ("2019-01-06", "f.example.com", "com", "DNSKEY", 13),
    ]
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime([r[0] for r in rows]),
            "domain": [r[1] for r in rows],
            "zone": [r[2] for r in rows],
            "rr_type": [r[3] for r in rows],
            "algorithm": pd.array([r[4] for r in rows], dtype="Int64"),
            "digest_type": pd.array([None] * len(rows), dtype="Int64"),
            "key_tag": pd.array([None] * len(rows), dtype="Int64"),
            "flags": pd.array([None] * len(rows), dtype="object"),
            "source": ["zonefile-com"] * len(rows),
            "measurement_id": [f"oi-{i}" for i in range(len(rows))],
        }
    )
    frame.to_parquet(path, engine="pyarrow", index=False)


def test_prefilter_excludes_non_dnssec_record_types(
    tmp_path, checklist_db, dictionary, schema_report
):
    """A/AAAA/MX/TXT/NS rows must never reach an indicator expression."""
    parquet = tmp_path / "mixed.parquet"
    _write_mixed_parquet(parquet)

    columns = [c["name"] for c in describe_parquet(parquet)["columns"]]
    column_expr = sql_compiler.build_column_expressions(
        dictionary, _needed_fields(schema_report), columns
    )
    compiled = sql_compiler.compile_checklist(checklist_db, column_expr, schema_report)
    partition = LocalPartition.from_paths([parquet], partition_id="mixed", source="com")

    connection = duckdb.connect(database=":memory:")
    try:
        result = process_partition(
            partition,
            uris=list(partition.paths),
            connection=connection,
            compiled=compiled,
            column_expr=column_expr,
            checkpoint_dir=tmp_path / "checkpoints",
        )
    finally:
        connection.close()

    # Six rows in the file, one of them a DNSSEC record type.
    assert result.rows_scanned == 1
    aggregates = merge_checkpoints(tmp_path / "checkpoints")
    assert aggregates.rows_scanned == 1
    assert not [row for row in aggregates.rfc_rows() if row.count and row.decision == "no_match" and row.rfc_id == "RFC 6605"]
    valid = {
        (row.rfc_id, row.decision)
        for row in aggregates.rollup_rows()
        if row.decision == "valid_match"
    }
    assert ("RFC 6605", "valid_match") in valid


def test_prefilter_is_reported_in_the_run_warnings(scale_result):
    _result, _aggregates, warnings, _root = scale_result
    assert any("rr_type is not one of" in message for message in warnings)


# --------------------------------------------------------------------------- #
# Checkpointing
# --------------------------------------------------------------------------- #


@pytest.fixture
def one_partition(tmp_path, checklist_db, dictionary, schema_report, sample_parquet_path):
    """Everything :func:`process_partition` needs, over the sample file."""
    columns = [c["name"] for c in describe_parquet(sample_parquet_path)["columns"]]
    column_expr = sql_compiler.build_column_expressions(
        dictionary, _needed_fields(schema_report), columns
    )
    compiled = sql_compiler.compile_checklist(checklist_db, column_expr, schema_report)
    partition = LocalPartition.from_paths(
        [sample_parquet_path], partition_id="sample", source="zonefile-sample"
    )
    connection = duckdb.connect(database=":memory:")
    yield partition, column_expr, compiled, connection
    connection.close()


def _run(one_partition, checkpoint_dir: Path, **kwargs):
    partition, column_expr, compiled, connection = one_partition
    return process_partition(
        partition,
        uris=list(partition.paths),
        connection=connection,
        compiled=compiled,
        column_expr=column_expr,
        checkpoint_dir=checkpoint_dir,
        **kwargs,
    )


def test_resume_skips_completed_partitions(one_partition, tmp_path):
    checkpoints = tmp_path / "checkpoints"
    first = _run(one_partition, checkpoints)
    assert first.reused is False
    stamp = first.checkpoint_path.stat().st_mtime_ns

    second = _run(one_partition, checkpoints)
    assert second.reused is True
    assert second.rows_scanned == first.rows_scanned
    assert second.aggregate_rows == first.aggregate_rows
    assert second.checkpoint_path.stat().st_mtime_ns == stamp, (
        "a reused checkpoint must not be rewritten"
    )


def test_resume_false_recomputes(one_partition, tmp_path):
    checkpoints = tmp_path / "checkpoints"
    _run(one_partition, checkpoints)
    again = _run(one_partition, checkpoints, resume=False)
    assert again.reused is False


def test_corrupt_checkpoint_is_recomputed(one_partition, tmp_path):
    """A checkpoint that does not read back is never silently trusted."""
    checkpoints = tmp_path / "checkpoints"
    first = _run(one_partition, checkpoints)
    first.checkpoint_path.write_bytes(b"this is not a parquet file")

    warnings: list[str] = []
    second = _run(one_partition, checkpoints, warnings=warnings)
    assert second.reused is False
    assert second.rows_scanned == first.rows_scanned
    assert any("recomputed" in message for message in warnings)
    assert any("could not be read" in message for message in warnings)
    # And the recomputation left a checkpoint that does read back.
    assert len(pd.read_parquet(second.checkpoint_path)) == second.aggregate_rows


def test_missing_status_file_forces_recomputation(one_partition, tmp_path):
    checkpoints = tmp_path / "checkpoints"
    first = _run(one_partition, checkpoints)
    first.status_path.unlink()

    warnings: list[str] = []
    second = _run(one_partition, checkpoints, warnings=warnings)
    assert second.reused is False
    assert any("status file is missing" in message for message in warnings)


def test_truncated_checkpoint_is_detected(one_partition, tmp_path):
    """A readable but short Parquet file is a truncated write, not a small day."""
    checkpoints = tmp_path / "checkpoints"
    first = _run(one_partition, checkpoints)
    frame = pd.read_parquet(first.checkpoint_path)
    frame.head(3).to_parquet(first.checkpoint_path, engine="pyarrow", index=False)

    warnings: list[str] = []
    second = _run(one_partition, checkpoints, warnings=warnings)
    assert second.reused is False
    assert any("truncated" in message for message in warnings)


def test_stale_checkpoint_from_another_checklist_is_recomputed(
    one_partition, tmp_path, checklist_db, dictionary, schema_report, sample_parquet_path
):
    """Changing the checklist invalidates checkpoints: they answer another question."""
    checkpoints = tmp_path / "checkpoints"
    _run(one_partition, checkpoints)

    partition, column_expr, _compiled, connection = one_partition
    reduced = checklist_db.model_copy(deep=True)
    reduced.rfcs = reduced.rfcs[:2]
    other = sql_compiler.compile_checklist(reduced, column_expr, schema_report)

    warnings: list[str] = []
    result = process_partition(
        partition,
        uris=list(partition.paths),
        connection=connection,
        compiled=other,
        column_expr=column_expr,
        checkpoint_dir=checkpoints,
        warnings=warnings,
    )
    assert result.reused is False
    assert any("different compiled scan" in message for message in warnings)


class _PathLikePartition:
    """A partition whose id is a path, as ``openintel_source.Partition``'s is.

    Written by hand rather than imported so this test cannot become a test of
    that module; what matters is only the shape the runner has to survive.
    """

    partition_id = "zonefile/nu/2018-05-01"
    slug = "zonefile__nu__2018-05-01"
    source = "nu"
    basis = "zonefile"
    date = None


def test_path_shaped_partition_id_stays_one_flat_checkpoint(one_partition, tmp_path):
    """A partition id with slashes must not scatter checkpoints into subfolders.

    ``merge_checkpoints`` globs the top level of the checkpoint directory; a
    nested checkpoint would be silently uncounted, which reads as "that day had
    no matches".
    """
    _partition, column_expr, compiled, connection = one_partition
    partition, *_ = one_partition
    checkpoints = tmp_path / "checkpoints"
    result = process_partition(
        _PathLikePartition(),
        uris=list(partition.paths),
        connection=connection,
        compiled=compiled,
        column_expr=column_expr,
        checkpoint_dir=checkpoints,
    )
    assert result.checkpoint_path.parent == checkpoints
    assert "/" not in result.checkpoint_path.name
    assert merge_checkpoints(checkpoints).rows_scanned == 73


def test_merge_checkpoints_skips_unreadable_files(one_partition, tmp_path):
    checkpoints = tmp_path / "checkpoints"
    _run(one_partition, checkpoints)
    (checkpoints / "broken.parquet").write_bytes(b"nope")

    aggregates = merge_checkpoints(checkpoints)
    assert any("broken.parquet" in message for message in aggregates.warnings)
    assert aggregates.rows_scanned == 73


# --------------------------------------------------------------------------- #
# Exemplar sampling
# --------------------------------------------------------------------------- #


def test_exemplar_sampling_is_deterministic(one_partition, tmp_path):
    """The same partition must yield the same exemplars on every run."""
    first_dir = tmp_path / "run_a"
    second_dir = tmp_path / "run_b"
    first = _run(one_partition, first_dir, exemplars_per_group=3)
    second = _run(one_partition, second_dir, exemplars_per_group=3)

    left = pd.read_parquet(first.exemplar_path).sort_values(
        by=["rfc_id", "decision", "sample_hash"], kind="mergesort"
    ).reset_index(drop=True)
    right = pd.read_parquet(second.exemplar_path).sort_values(
        by=["rfc_id", "decision", "sample_hash"], kind="mergesort"
    ).reset_index(drop=True)
    pd.testing.assert_frame_equal(left, right)
    assert len(left) > 0


def test_exemplars_are_capped_per_group(one_partition, tmp_path):
    result = _run(one_partition, tmp_path / "checkpoints", exemplars_per_group=2)
    frame = pd.read_parquet(result.exemplar_path)
    sizes = frame.groupby(["rfc_id", "decision"]).size()
    assert sizes.max() <= 2
    assert (frame["rfc_id"] != sql_compiler.TOTALS_RFC_ID).all()


def test_exemplar_frame_carries_only_observation_columns(scale_result):
    """Bookkeeping columns must not leak into ``ObservedSignal.fields``."""
    result, _aggregates, _warnings, _root = scale_result
    for signal in result.signals:
        assert set(signal.fields) == set(SIGNAL_FIELDS)


def test_merged_exemplars_stay_capped(scale_result):
    _result, aggregates, _warnings, _root = scale_result
    frame = aggregates.exemplars
    sizes = frame.groupby(["rfc_id", "decision"]).size()
    assert sizes.max() <= aggregates.exemplars_per_group


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #


def test_scale_run_config_rejects_a_zero_exemplar_budget(tmp_path):
    from openintel_rfc.utils import PipelineError

    with pytest.raises(PipelineError):
        ScaleRunConfig(out=tmp_path, checkpoint_dir=tmp_path, exemplars_per_group=0)


def test_merge_checkpoints_requires_a_directory(tmp_path):
    from openintel_rfc.utils import PipelineError

    with pytest.raises(PipelineError):
        merge_checkpoints(tmp_path / "does-not-exist")


def test_empty_checkpoint_directory_is_not_a_claim_about_the_corpus(tmp_path):
    aggregates: AggregateTable = merge_checkpoints(tmp_path)
    assert aggregates.rows == []
    assert any("not a statement about the corpus" in m for m in aggregates.warnings)
