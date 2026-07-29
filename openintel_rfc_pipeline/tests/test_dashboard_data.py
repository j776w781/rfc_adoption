"""The dashboard's data-access layer.

Two properties are non-negotiable here and are what the tests assert: the loader
never raises at the user, and every DataFrame comes back with its full declared
column set even when the underlying file is absent. A page must be able to write
``df[df["decision"] == "valid_match"]`` without first checking that the column
exists.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from openintel_rfc import config
from openintel_rfc.dashboard_data import (
    MATCH_COLUMNS,
    RANKED_COLUMNS,
    REVIEW_COLUMNS,
    SCHEMA_COLUMNS,
    SIGNAL_COLUMNS,
    TIMELINE_COLUMNS,
    TRACE_COLUMNS,
    DashboardBundle,
    available_output_dirs,
    filter_dataframe,
    load_dashboard_data,
    load_review_status,
    save_review_status,
    summarize,
)
from openintel_rfc.utils import PipelineError

ALL_FRAMES = (
    ("signals_df", SIGNAL_COLUMNS),
    ("matches_df", MATCH_COLUMNS),
    ("ranked_df", RANKED_COLUMNS),
    ("traces_df", TRACE_COLUMNS),
    ("review_df", REVIEW_COLUMNS),
    ("timeline_df", TIMELINE_COLUMNS),
    ("schema_df", SCHEMA_COLUMNS),
)


@pytest.fixture(scope="module")
def demo_bundle(demo_output_dir: Path) -> DashboardBundle:
    """The committed demo run, loaded read-only."""
    return load_dashboard_data(demo_output_dir)


# --------------------------------------------------------------------------- #
# The committed demo run
# --------------------------------------------------------------------------- #


def test_the_loader_reads_demo_output_without_crashing(demo_bundle: DashboardBundle) -> None:
    assert isinstance(demo_bundle, DashboardBundle)
    assert demo_bundle.has_analysis is True
    assert not demo_bundle.signals_df.empty
    assert not demo_bundle.matches_df.empty
    assert not demo_bundle.ranked_df.empty
    assert not demo_bundle.review_df.empty
    assert not demo_bundle.timeline_df.empty
    assert demo_bundle.report_md is not None


@pytest.mark.parametrize(("attribute", "columns"), ALL_FRAMES, ids=[a for a, _ in ALL_FRAMES])
def test_every_frame_declares_its_full_column_set(
    demo_bundle: DashboardBundle, attribute: str, columns: tuple[str, ...]
) -> None:
    frame = getattr(demo_bundle, attribute)

    assert list(frame.columns)[: len(columns)] == list(columns)


def test_dates_and_scores_are_typed_for_plotting(demo_bundle: DashboardBundle) -> None:
    assert pd.api.types.is_datetime64_any_dtype(demo_bundle.signals_df["timestamp"])
    assert pd.api.types.is_datetime64_any_dtype(
        demo_bundle.matches_df["observation_timestamp"]
    )
    assert pd.api.types.is_numeric_dtype(demo_bundle.matches_df["score"])
    assert pd.api.types.is_numeric_dtype(demo_bundle.ranked_df["rank"])


def test_list_valued_fields_keep_a_parallel_raw_column(demo_bundle: DashboardBundle) -> None:
    row = demo_bundle.matches_df.iloc[0]

    assert isinstance(row["matched_indicator_ids"], str)
    assert isinstance(row["matched_indicator_ids_raw"], list)


def test_the_bundle_resolves_traces_and_review_items_by_id(
    demo_bundle: DashboardBundle,
) -> None:
    trace_id = demo_bundle.traces[0]["trace_id"]
    item_id = demo_bundle.review_items[0]["item_id"]

    assert demo_bundle.trace_by_id(trace_id)["trace_id"] == trace_id
    assert demo_bundle.review_item_by_id(item_id)["item_id"] == item_id
    assert demo_bundle.trace_by_id("trace_does_not_exist") is None
    assert demo_bundle.review_item_by_id("rev_9999") is None


def test_the_demo_summary_reports_the_headline_counters(demo_bundle: DashboardBundle) -> None:
    summary = demo_bundle.summary

    assert summary["signal_count"] == len(demo_bundle.signals_df)
    assert summary["match_count"] == len(demo_bundle.matches_df)
    assert summary["rfc_count"] > 0
    assert summary["timestamp_invalid_count"] > 0, "the demo data exercises the cutoff"
    assert summary["top_rfc_id"] == "RFC 8078"
    assert summary["top_rfc_score"] == pytest.approx(17.25)
    assert " to " in summary["date_range"]
    assert summary == summarize(demo_bundle)


def test_loading_demo_output_does_not_write_to_it(demo_output_dir: Path) -> None:
    before = sorted(p.name for p in demo_output_dir.iterdir())

    load_dashboard_data(demo_output_dir)

    assert sorted(p.name for p in demo_output_dir.iterdir()) == before


# --------------------------------------------------------------------------- #
# A freshly produced run
# --------------------------------------------------------------------------- #


def test_the_loader_reads_a_fresh_analyze_run(analyzed_output: Path) -> None:
    bundle = load_dashboard_data(analyzed_output)

    assert bundle.has_analysis is True
    assert bundle.available["rfc_matches"] is True
    assert bundle.run_manifest is not None
    # schema-check artefacts are written by a different subcommand.
    assert bundle.available["schema_check_json"] is False
    assert any("schema_check.json" in message for message in bundle.warnings)


def test_pipeline_warnings_are_surfaced_from_the_run_manifest(analyzed_output: Path) -> None:
    bundle = load_dashboard_data(analyzed_output)

    assert any(message.startswith("From run: ") for message in bundle.warnings)


# --------------------------------------------------------------------------- #
# Degraded inputs
# --------------------------------------------------------------------------- #


def test_an_empty_directory_yields_empty_frames_and_warnings(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    bundle = load_dashboard_data(empty)

    assert bundle.warnings, "the user must be told the directory holds nothing"
    assert bundle.has_analysis is False
    for attribute, columns in ALL_FRAMES:
        frame = getattr(bundle, attribute)
        assert frame.empty
        assert list(frame.columns) == list(columns), f"{attribute} lost its columns"
    assert bundle.traces == [] and bundle.review_items == []
    assert bundle.summary["signal_count"] == 0
    assert bundle.summary["date_range"] == "n/a"
    assert bundle.summary["top_rfc_id"] is None


def test_a_missing_directory_warns_instead_of_raising(tmp_path: Path) -> None:
    bundle = load_dashboard_data(tmp_path / "never_created")

    assert any("does not exist" in message for message in bundle.warnings)
    assert bundle.has_analysis is False
    assert all(value is False for value in bundle.available.values())


def test_an_unparseable_artefact_is_reported_not_raised(tmp_path: Path) -> None:
    directory = tmp_path / "corrupt"
    directory.mkdir()
    (directory / config.OUTPUT_FILES["rfc_matches"]).write_text("{not json", encoding="utf-8")

    bundle = load_dashboard_data(directory)

    assert bundle.matches_df.empty
    assert any("rfc_matches.json could not be read" in message for message in bundle.warnings)


def test_an_envelope_from_another_version_is_reported_not_raised(tmp_path: Path) -> None:
    directory = tmp_path / "otherversion"
    directory.mkdir()
    (directory / config.OUTPUT_FILES["rfc_matches"]).write_text(
        json.dumps({"rows": [], "other": []}), encoding="utf-8"
    )

    bundle = load_dashboard_data(directory)

    assert bundle.matches_df.empty
    assert any("different pipeline version" in message for message in bundle.warnings)


def test_a_bare_json_list_is_still_accepted(tmp_path: Path) -> None:
    """Hand-written or older files load rather than being rejected."""
    directory = tmp_path / "bare"
    directory.mkdir()
    (directory / config.OUTPUT_FILES["observed_signals"]).write_text(
        json.dumps(
            [
                {
                    "signal_id": "sig_0001",
                    "timestamp": "2018-05-01T00:00:00",
                    "domain": "example.nl",
                    "fields": {"rr_type": "CDS", "algorithm": 0},
                }
            ]
        ),
        encoding="utf-8",
    )

    bundle = load_dashboard_data(directory)

    assert len(bundle.signals_df) == 1
    assert bundle.signals_df.iloc[0]["rr_type"] == "CDS"
    assert bundle.signals_df.iloc[0]["algorithm"] == 0


def test_a_missing_checklist_path_is_a_warning_not_a_failure(tmp_path: Path) -> None:
    bundle = load_dashboard_data(tmp_path, checklists=tmp_path / "absent.json")

    assert bundle.checklist_db is None
    assert any("Checklist database not found" in message for message in bundle.warnings)


# --------------------------------------------------------------------------- #
# Reviewer state (dashboard-owned, never written back into the pipeline output)
# --------------------------------------------------------------------------- #


def test_review_status_round_trips_through_its_own_file(tmp_path: Path) -> None:
    path = save_review_status(tmp_path, {"rev_0002": "accepted", "rev_0001": "rejected"})

    assert path.name == config.OUTPUT_FILES["review_queue_status"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert list(payload["statuses"]) == ["rev_0001", "rev_0002"], "sorted for a stable diff"
    assert load_review_status(tmp_path) == {"rev_0001": "rejected", "rev_0002": "accepted"}


def test_saving_an_unknown_review_status_is_refused(tmp_path: Path) -> None:
    with pytest.raises(PipelineError, match="Invalid review status"):
        save_review_status(tmp_path, {"rev_0001": "probably"})


def test_review_status_is_empty_when_nobody_has_reviewed_anything(tmp_path: Path) -> None:
    assert load_review_status(tmp_path) == {}


def test_saving_review_status_does_not_touch_the_pipeline_artefacts(
    tmp_path: Path, analyzed_output: Path
) -> None:
    """Reviewer annotations live in their own file; review_queue.json is read-only."""
    source = (analyzed_output / config.OUTPUT_FILES["review_queue"]).read_text(encoding="utf-8")
    (tmp_path / config.OUTPUT_FILES["review_queue"]).write_text(source, encoding="utf-8")

    save_review_status(tmp_path, {"rev_0001": "accepted"})

    assert (tmp_path / config.OUTPUT_FILES["review_queue"]).read_text(encoding="utf-8") == source


# --------------------------------------------------------------------------- #
# Discovery and filtering
# --------------------------------------------------------------------------- #


def test_available_output_dirs_finds_directories_holding_artefacts(
    tmp_path: Path, analyzed_output: Path
) -> None:
    nested = tmp_path / "runs" / "one"
    nested.mkdir(parents=True)
    (nested / config.OUTPUT_FILES["rfc_matches"]).write_text("{}", encoding="utf-8")
    (tmp_path / "runs" / "empty").mkdir()

    found = available_output_dirs(tmp_path)

    assert nested in found
    assert (tmp_path / "runs" / "empty") not in found
    assert available_output_dirs(tmp_path / "not_a_directory") == []


def test_filter_dataframe_ignores_the_no_filter_sentinels(
    demo_bundle: DashboardBundle,
) -> None:
    frame = demo_bundle.matches_df

    assert len(filter_dataframe(frame, decision=None)) == len(frame)
    assert len(filter_dataframe(frame, decision="All")) == len(frame)
    assert len(filter_dataframe(frame, decision="")) == len(frame)


def test_filter_dataframe_supports_equality_membership_and_ranges(
    demo_bundle: DashboardBundle,
) -> None:
    frame = demo_bundle.matches_df

    valid = filter_dataframe(frame, decision="valid_match")
    assert not valid.empty
    assert set(valid["decision"]) == {"valid_match"}

    either = filter_dataframe(frame, decision=["valid_match", "timestamp_invalid"])
    assert set(either["decision"]) == {"valid_match", "timestamp_invalid"}

    high = filter_dataframe(frame, score=slice(12.0, None))
    assert not high.empty
    assert (high["score"] >= 12.0).all()


def test_filter_dataframe_skips_a_column_the_frame_does_not_have(
    demo_bundle: DashboardBundle,
) -> None:
    frame = demo_bundle.matches_df

    assert len(filter_dataframe(frame, no_such_column="x")) == len(frame)
