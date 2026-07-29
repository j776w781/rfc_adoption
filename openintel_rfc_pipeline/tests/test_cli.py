"""The command-line entry points, exercised in-process.

``cli.main`` is called directly with a ``tmp_path`` output directory: no
subprocess, no network, and nothing written into the repository's
``demo_output``. Every artefact the contract names is checked for existence and
for being parseable, because a file that exists but cannot be read is worse than
one that is missing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import run_cli
from openintel_rfc import config
from openintel_rfc.cli import build_parser
from openintel_rfc.report import LIMITATION_SENTENCE, render_report
from openintel_rfc.tool_survey import build_survey, generate_survey

#: Exactly the sentence the report must state, unhedged (build contract).
EXPECTED_LIMITATION = (
    "This pipeline does not prove RFC adoption by itself. It identifies ranked RFC "
    "candidates based on OpenINTEL-observable signals and timestamp consistency."
)

SCHEMA_CHECK_ARTEFACTS = (
    "queryable_indicators",
    "non_queryable_indicators",
    "schema_check_report_md",
    "schema_check_csv",
    "schema_check_json",
)

ANALYZE_ARTEFACTS = (
    "observed_signals",
    "rfc_matches",
    "reasoning_traces",
    "review_queue",
    "adoption_timeline",
    "ranked_candidates",
    "report_md",
    "rfc_matches_csv",
    "review_queue_csv",
    "adoption_timeline_csv",
    "observed_signals_csv",
    "reasoning_traces_csv",
    "run_manifest",
)

#: JSON artefacts whose content must not vary between two identical runs. The
#: manifest and the report are excluded on purpose: both embed the output path.
DETERMINISTIC_ARTEFACTS = (
    "observed_signals",
    "rfc_matches",
    "reasoning_traces",
    "review_queue",
    "adoption_timeline",
    "ranked_candidates",
)


def _envelope(path: Path, key: str) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["count"] == len(payload[key])
    assert payload["pipeline"] == config.PIPELINE_NAME
    assert payload["version"] == config.PIPELINE_VERSION
    return payload[key]


# --------------------------------------------------------------------------- #
# tool-survey
# --------------------------------------------------------------------------- #


def test_generate_survey_writes_a_markdown_file(tmp_path: Path) -> None:
    out_path = tmp_path / "nested" / "open_source_tool_survey.md"

    written = generate_survey(out_path)

    assert written == out_path
    assert out_path.is_file()
    text = out_path.read_text(encoding="utf-8")
    assert text.startswith("#")
    assert text.endswith("\n")
    assert "duckdb" in text and "pyarrow" in text and "pydantic" in text


def test_generate_survey_records_that_no_live_search_was_performed(tmp_path: Path) -> None:
    """The document has to say which it is, rather than implying a search happened."""
    out_path = tmp_path / "survey.md"

    generate_survey(out_path)
    survey = build_survey()

    assert survey.live_search_performed is False
    assert survey.mvp_stack, "the shortlist must recommend something"
    assert set(survey.mvp_stack).isdisjoint(survey.rejected)
    assert "No live search was performed" in out_path.read_text(encoding="utf-8")


def test_cli_tool_survey_writes_the_file_and_returns_zero(tmp_path: Path) -> None:
    out_path = tmp_path / "survey.md"

    code, stdout = run_cli(["tool-survey", "--out", str(out_path)])

    assert code == 0
    assert out_path.is_file()
    assert "tool survey ->" in stdout


# --------------------------------------------------------------------------- #
# schema-check
# --------------------------------------------------------------------------- #


def test_cli_schema_check_creates_every_expected_file(
    tmp_path: Path, checklist_path: Path, dictionary_path: Path
) -> None:
    out_dir = tmp_path / "schema"

    code, stdout = run_cli(
        [
            "schema-check",
            "--checklists",
            str(checklist_path),
            "--dictionary",
            str(dictionary_path),
            "--out",
            str(out_dir),
        ]
    )

    assert code == 0
    for key in SCHEMA_CHECK_ARTEFACTS:
        path = out_dir / config.OUTPUT_FILES[key]
        assert path.is_file(), f"{key} was not written"
        assert path.stat().st_size > 0
    assert "indicators across" in stdout


def test_cli_schema_check_artefacts_parse_and_agree(schema_checked_output: Path) -> None:
    report = json.loads(
        (schema_checked_output / config.OUTPUT_FILES["schema_check_json"]).read_text(
            encoding="utf-8"
        )
    )
    queryable = _envelope(
        schema_checked_output / config.OUTPUT_FILES["queryable_indicators"], "indicators"
    )
    non_queryable = _envelope(
        schema_checked_output / config.OUTPUT_FILES["non_queryable_indicators"], "indicators"
    )

    assert report["indicator_count"] == len(report["indicators"])
    assert all(item["queryability"] == "queryable" for item in queryable)
    assert all(item["queryability"] == "non_queryable" for item in non_queryable)
    assert report["counts_by_queryability"]["queryable"] == len(queryable)
    assert report["counts_by_queryability"]["non_queryable"] == len(non_queryable)
    assert any(
        item["indicator_id"] == "rfc8624_validator_algorithm_support" for item in non_queryable
    )


def test_cli_schema_check_markdown_names_the_unanswerable_indicator(
    schema_checked_output: Path,
) -> None:
    text = (schema_checked_output / config.OUTPUT_FILES["schema_check_report_md"]).read_text(
        encoding="utf-8"
    )

    assert text.startswith("# OpenINTEL Schema Cross-Check")
    assert "rfc8624_validator_algorithm_support" in text
    assert "validator_algorithm_support" in text


# --------------------------------------------------------------------------- #
# analyze
# --------------------------------------------------------------------------- #


def test_cli_analyze_creates_every_expected_file(analyzed_output: Path) -> None:
    for key in ANALYZE_ARTEFACTS:
        path = analyzed_output / config.OUTPUT_FILES[key]
        assert path.is_file(), f"{key} was not written"
        assert path.stat().st_size > 0


@pytest.mark.parametrize(
    ("file_key", "envelope_key"),
    [
        ("observed_signals", "signals"),
        ("rfc_matches", "matches"),
        ("reasoning_traces", "traces"),
        ("review_queue", "review_items"),
        ("adoption_timeline", "timeline"),
        ("ranked_candidates", "candidates"),
    ],
)
def test_cli_analyze_json_artefacts_use_the_counted_envelope(
    analyzed_output: Path, file_key: str, envelope_key: str
) -> None:
    items = _envelope(analyzed_output / config.OUTPUT_FILES[file_key], envelope_key)

    assert items, f"{file_key} should not be empty for the sample data"
    assert all(isinstance(item, dict) for item in items)


def test_cli_analyze_csv_artefacts_have_headers(analyzed_output: Path) -> None:
    import csv

    for key in (
        "rfc_matches_csv",
        "review_queue_csv",
        "adoption_timeline_csv",
        "observed_signals_csv",
        "reasoning_traces_csv",
    ):
        with (analyzed_output / config.OUTPUT_FILES[key]).open(
            newline="", encoding="utf-8"
        ) as handle:
            rows = list(csv.DictReader(handle))
        assert rows, f"{key} has no data rows"


def test_cli_analyze_manifest_describes_the_run(analyzed_output: Path) -> None:
    manifest = json.loads(
        (analyzed_output / config.OUTPUT_FILES["run_manifest"]).read_text(encoding="utf-8")
    )

    assert manifest["pipeline"] == config.PIPELINE_NAME
    assert manifest["counts"]["signals"] > 0
    assert manifest["counts"]["matches"] == (
        manifest["counts"]["signals"] * manifest["counts"]["rfcs"]
    )
    assert "timestamp_invalid" in manifest["matches_by_decision"]
    assert manifest["warning_count"] == len(manifest["warnings"])
    assert "report.md" in manifest["outputs"].values()


def test_cli_analyze_top_candidate_is_the_most_specific_explanation(
    analyzed_output: Path,
) -> None:
    candidates = _envelope(
        analyzed_output / config.OUTPUT_FILES["ranked_candidates"], "candidates"
    )
    by_id = {candidate["rfc_id"]: candidate for candidate in candidates}

    assert candidates[0]["rank"] == 1
    assert by_id["RFC 8078"]["score"] == pytest.approx(17.25)
    assert by_id["RFC 7344"]["score"] == pytest.approx(11.25)
    assert by_id["RFC 8078"]["rank"] < by_id["RFC 7344"]["rank"]


def test_cli_analyze_honours_the_row_limit(
    tmp_path: Path, checklist_path: Path, dictionary_path: Path, sample_parquet_path: Path
) -> None:
    out_dir = tmp_path / "limited"

    code, _ = run_cli(
        [
            "analyze",
            "--checklists",
            str(checklist_path),
            "--dictionary",
            str(dictionary_path),
            "--parquet",
            str(sample_parquet_path),
            "--out",
            str(out_dir),
            "--limit",
            "3",
        ]
    )

    assert code == 0
    signals = _envelope(out_dir / config.OUTPUT_FILES["observed_signals"], "signals")
    assert len(signals) == 3


def test_cli_analyze_engine_choice_does_not_change_the_result(
    tmp_path: Path, checklist_path: Path, dictionary_path: Path, sample_parquet_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(config.DETERMINISTIC_TIMESTAMP_ENV, "1")
    outputs = []
    for engine in ("duckdb", "pandas"):
        out_dir = tmp_path / engine
        code, _ = run_cli(
            [
                "analyze",
                "--checklists", str(checklist_path),
                "--dictionary", str(dictionary_path),
                "--parquet", str(sample_parquet_path),
                "--engine", engine,
                "--out", str(out_dir),
            ]
        )
        assert code == 0
        outputs.append(out_dir)

    for key in DETERMINISTIC_ARTEFACTS:
        name = config.OUTPUT_FILES[key]
        assert (outputs[0] / name).read_text(encoding="utf-8") == (
            outputs[1] / name
        ).read_text(encoding="utf-8"), f"{name} differs between engines"


def test_cli_analyze_is_byte_identical_across_two_runs(
    tmp_path: Path,
    checklist_path: Path,
    dictionary_path: Path,
    sample_parquet_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With utils.now() frozen, the same input must produce the same JSON."""
    monkeypatch.setenv(config.DETERMINISTIC_TIMESTAMP_ENV, "1")
    outputs = []
    for run in ("first", "second"):
        out_dir = tmp_path / run
        code, _ = run_cli(
            [
                "analyze",
                "--checklists", str(checklist_path),
                "--dictionary", str(dictionary_path),
                "--parquet", str(sample_parquet_path),
                "--out", str(out_dir),
            ]
        )
        assert code == 0
        outputs.append(out_dir)

    for key in DETERMINISTIC_ARTEFACTS:
        name = config.OUTPUT_FILES[key]
        first = (outputs[0] / name).read_text(encoding="utf-8")
        second = (outputs[1] / name).read_text(encoding="utf-8")
        assert first == second, f"{name} is not reproducible"
        assert "2020-01-01T00:00:00" in json.loads(first)["generated_at"]


# --------------------------------------------------------------------------- #
# The report's limitation statement
# --------------------------------------------------------------------------- #


def test_the_module_constant_is_the_contracted_sentence() -> None:
    assert LIMITATION_SENTENCE == EXPECTED_LIMITATION


def test_the_generated_report_states_the_limitation_verbatim(analyzed_output: Path) -> None:
    text = (analyzed_output / config.OUTPUT_FILES["report_md"]).read_text(encoding="utf-8")

    assert EXPECTED_LIMITATION in text
    assert text.startswith("# OpenINTEL RFC Adoption Analysis")


def test_render_report_states_the_limitation_for_an_empty_run(
    checklist_db, dictionary, schema_report
) -> None:
    from datetime import datetime

    from openintel_rfc.models import PipelineResult, RunConfig

    result = PipelineResult(
        generated_at=datetime(2020, 1, 1),
        run_config=RunConfig(checklists="c.json", dictionary="d.json"),
        schema_report=schema_report,
    )

    text = render_report(result)

    assert EXPECTED_LIMITATION in text, "the caveat must not depend on there being results"


# --------------------------------------------------------------------------- #
# Argument handling and failures
# --------------------------------------------------------------------------- #


def test_the_parser_exposes_the_three_documented_subcommands() -> None:
    parser = build_parser()

    for command in ("tool-survey", "schema-check", "analyze"):
        args = parser.parse_args([command])
        assert args.command == command
        assert callable(args.func)


def test_a_missing_parquet_file_fails_cleanly_with_exit_code_two(
    tmp_path: Path, checklist_path: Path, dictionary_path: Path, capsys: pytest.CaptureFixture
) -> None:
    code, _ = run_cli(
        [
            "analyze",
            "--checklists", str(checklist_path),
            "--dictionary", str(dictionary_path),
            "--parquet", str(tmp_path / "absent.parquet"),
            "--out", str(tmp_path / "out"),
        ]
    )

    assert code == 2, "a bad path is an expected failure, not a traceback"
    assert "Parquet file not found" in capsys.readouterr().err


def test_a_malformed_checklist_fails_cleanly(
    tmp_path: Path, dictionary_path: Path, capsys: pytest.CaptureFixture
) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps({"rfcs": [{"title": "no rfc_id"}]}), encoding="utf-8")

    code, _ = run_cli(
        [
            "schema-check",
            "--checklists", str(broken),
            "--dictionary", str(dictionary_path),
            "--out", str(tmp_path / "out"),
        ]
    )

    assert code == 2
    assert "not a usable RFC checklist database" in capsys.readouterr().err


def test_a_run_config_file_supplies_defaults_the_flags_can_override(
    tmp_path: Path, checklist_path: Path, dictionary_path: Path, sample_parquet_path: Path
) -> None:
    out_dir = tmp_path / "from_config"
    config_path = tmp_path / "run" / "config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "checklists": str(checklist_path),
                "dictionary": str(dictionary_path),
                "parquet": str(sample_parquet_path),
                "out": str(out_dir),
                "limit": 4,
            }
        ),
        encoding="utf-8",
    )

    # --out is passed as well so that a regression in config resolution can never
    # send output at the repository's demo_output directory.
    code, _ = run_cli(["analyze", "--config", str(config_path), "--out", str(out_dir)])

    assert code == 0
    signals = _envelope(out_dir / config.OUTPUT_FILES["observed_signals"], "signals")
    assert len(signals) == 4
