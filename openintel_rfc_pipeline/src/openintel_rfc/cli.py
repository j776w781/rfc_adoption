"""Command-line entry point for the OpenINTEL RFC-adoption matching pipeline.

Three subcommands:

``tool-survey``   regenerate the open-source tool survey Markdown.
``schema-check``  cross-check RFC indicators against the OpenINTEL dictionary.
``analyze``       run the full pipeline over a Parquet file and write all artefacts.

Run with ``python -m openintel_rfc.cli <command>`` or via the ``openintel-rfc``
console script.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from . import config
from .models import PipelineResult, RunConfig
from .utils import PipelineError, ensure_dir, get_logger, iso, now, warn

LOGGER = get_logger("openintel_rfc.cli")


# --------------------------------------------------------------------------- #
# Argument parsing
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openintel-rfc",
        description=(
            "Match OpenINTEL DNS/DNSSEC measurements against RFC checklists and "
            "emit ranked candidates with explicit reasoning traces."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"{config.PIPELINE_NAME} {config.PIPELINE_VERSION}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    survey = sub.add_parser(
        "tool-survey", help="Generate or refresh the open-source tool survey."
    )
    survey.add_argument(
        "--out",
        type=Path,
        default=config.DEFAULT_SURVEY_PATH,
        help="Markdown file to write (default: docs/open_source_tool_survey.md).",
    )
    survey.add_argument(
        "--live-search",
        action="store_true",
        help=(
            "Record that a live web/GitHub search backed this survey. Only pass "
            "this if a search was actually performed; the survey states which."
        ),
    )
    survey.set_defaults(func=cmd_tool_survey)

    schema = sub.add_parser(
        "schema-check",
        help="Classify every RFC indicator as queryable / partial / non-queryable.",
    )
    _add_common_inputs(schema)
    schema.set_defaults(func=cmd_schema_check)

    analyze = sub.add_parser(
        "analyze", help="Run the full matching pipeline over an OpenINTEL Parquet file."
    )
    _add_common_inputs(analyze)
    analyze.add_argument(
        "--parquet",
        type=Path,
        default=config.DEFAULT_PARQUET_PATH,
        help="OpenINTEL-style Parquet file to analyze.",
    )
    analyze.add_argument(
        "--engine",
        choices=("auto", "duckdb", "pandas"),
        default="auto",
        help="Parquet query engine (default: auto, prefers DuckDB).",
    )
    analyze.add_argument(
        "--limit", type=int, default=None, help="Cap the number of Parquet rows read."
    )
    analyze.add_argument(
        "--min-score",
        type=float,
        default=config.MIN_RANKABLE_SCORE,
        help="Drop ranked candidates scoring at or below this value.",
    )
    analyze.add_argument(
        "--config",
        type=Path,
        default=None,
        help="JSON run config (examples/sample_run_config.json); CLI flags win.",
    )
    analyze.set_defaults(func=cmd_analyze)

    return parser


def _add_common_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--checklists",
        type=Path,
        default=config.DEFAULT_CHECKLIST_PATH,
        help="RFC checklist/signature database JSON.",
    )
    parser.add_argument(
        "--dictionary",
        type=Path,
        default=config.DEFAULT_DICTIONARY_PATH,
        help="OpenINTEL dictionary/schema JSON.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=config.DEFAULT_OUTPUT_DIR,
        help="Output directory for generated artefacts.",
    )


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #


def cmd_tool_survey(args: argparse.Namespace) -> int:
    from .tool_survey import generate_survey

    note = (
        "Live web/GitHub search was performed for this run."
        if args.live_search
        else ""
    )
    out_path = generate_survey(
        Path(args.out), live_search_performed=bool(args.live_search), search_note=note
    )
    LOGGER.info("Wrote tool survey to %s", out_path)
    print(f"tool survey -> {out_path}")
    return 0


def cmd_schema_check(args: argparse.Namespace) -> int:
    from .checklist_loader import (
        load_checklist_db,
        load_dictionary,
        validate_checklist_db,
        validate_dictionary,
    )
    from .exporters import export_schema_check
    from .report import render_schema_check_report
    from .schema_checker import check_schema

    warnings: list[str] = []
    db = load_checklist_db(args.checklists)
    dictionary = load_dictionary(args.dictionary)
    for message in validate_checklist_db(db) + validate_dictionary(dictionary):
        warn(warnings, message, LOGGER)

    report = check_schema(
        db,
        dictionary,
        checklist_path=str(args.checklists),
        dictionary_path=str(args.dictionary),
        warnings=warnings,
    )

    out_dir = ensure_dir(args.out)
    report_md = render_schema_check_report(report)
    written = export_schema_check(report, out_dir, report_md=report_md)

    _print_written(written)
    counts = report.counts_by_queryability
    print(
        f"\n{report.indicator_count} indicators across {report.rfc_count} RFCs: "
        + ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    )
    _print_warnings(warnings)
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    from .checklist_loader import (
        load_checklist_db,
        load_dictionary,
        validate_checklist_db,
        validate_dictionary,
    )
    from .exporters import export_analysis
    from .llm_verifier import get_verifier, verify_traces
    from .matcher import match_all
    from .parquet_reader import read_parquet
    from .ranking import close_ranking_pairs, rank_candidates
    from .report import render_report
    from .review_queue import build_review_queue
    from .schema_checker import check_schema, queryable_field_names
    from .signal_extractor import extract_signals
    from .timeline import build_timeline

    run_config = _resolve_run_config(args)
    warnings: list[str] = []

    # 1. Inputs -------------------------------------------------------------
    db = load_checklist_db(run_config.checklists)
    dictionary = load_dictionary(run_config.dictionary)
    for message in validate_checklist_db(db) + validate_dictionary(dictionary):
        warn(warnings, message, LOGGER)

    # 2. Which indicators can OpenINTEL actually answer? ---------------------
    schema_report = check_schema(
        db,
        dictionary,
        checklist_path=str(run_config.checklists),
        dictionary_path=str(run_config.dictionary),
        warnings=warnings,
    )
    needed_fields = sorted(
        set(queryable_field_names(schema_report)) | set(config.ALWAYS_SELECT_FIELDS)
    )
    LOGGER.info("Reading Parquet columns: %s", ", ".join(needed_fields))

    # 3. Parquet -> normalized observed signals ------------------------------
    if not run_config.parquet:
        raise PipelineError("analyze requires --parquet")
    parquet_path = Path(run_config.parquet)
    frame = read_parquet(
        parquet_path,
        dictionary,
        needed_fields,
        engine=run_config.engine,
        limit=run_config.limit,
        warnings=warnings,
    )
    signals = extract_signals(
        frame, origin_file=parquet_path.name, warnings=warnings
    )
    if not signals:
        warn(warnings, f"No usable observations were extracted from {parquet_path}", LOGGER)

    # 4. Compare every signal against every RFC ------------------------------
    matches, traces = match_all(signals, db, schema_report, warnings=warnings)
    ranked = rank_candidates(matches, db, min_score=run_config.min_score)
    close_pairs = close_ranking_pairs(ranked)

    # 5. Verification, review queue, timeline --------------------------------
    verifier = get_verifier()
    verifications = verify_traces(traces, db, verifier)
    review_items = build_review_queue(
        schema_report=schema_report,
        matches=matches,
        traces=traces,
        ranked=ranked,
        db=db,
        verifier=verifier,
        warnings=warnings,
        close_pairs=close_pairs,
    )
    timeline = build_timeline(matches, db)

    result = PipelineResult(
        generated_at=now(),
        run_config=run_config,
        schema_report=schema_report,
        signals=signals,
        matches=matches,
        ranked_candidates=ranked,
        traces=traces,
        review_items=review_items,
        timeline=timeline,
        warnings=warnings,
    )

    # 6. Export --------------------------------------------------------------
    out_dir = ensure_dir(run_config.out)
    report_md = render_report(result, survey_markdown=_read_survey())
    written = export_analysis(result, out_dir, report_md=report_md)

    _print_written(written)
    _print_analysis_summary(result, verifications)
    _print_warnings(warnings)
    return 0


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _resolve_run_config(args: argparse.Namespace) -> RunConfig:
    """Merge an optional JSON run config with CLI flags (flags win)."""
    from .utils import read_json

    payload: dict[str, object] = {}
    if getattr(args, "config", None):
        config_path = Path(args.config)
        payload = dict(read_json(config_path))
        base = config_path.resolve().parent.parent
        for key in ("checklists", "dictionary", "parquet", "out"):
            value = payload.get(key)
            if isinstance(value, str) and not Path(value).is_absolute():
                payload[key] = str((base / value).resolve())

    parser_defaults = {
        "checklists": config.DEFAULT_CHECKLIST_PATH,
        "dictionary": config.DEFAULT_DICTIONARY_PATH,
        "parquet": config.DEFAULT_PARQUET_PATH,
        "out": config.DEFAULT_OUTPUT_DIR,
        "engine": "auto",
        "limit": None,
        "min_score": config.MIN_RANKABLE_SCORE,
    }
    for key, default in parser_defaults.items():
        supplied = getattr(args, key, None)
        # A CLI flag left at its default does not override the config file.
        if supplied is not None and str(supplied) != str(default):
            payload[key] = supplied
        payload.setdefault(key, supplied if supplied is not None else default)

    return RunConfig(
        checklists=str(payload["checklists"]),
        dictionary=str(payload["dictionary"]),
        parquet=str(payload["parquet"]) if payload.get("parquet") else None,
        out=str(payload["out"]),
        limit=payload.get("limit"),  # type: ignore[arg-type]
        engine=str(payload.get("engine", "auto")),  # type: ignore[arg-type]
        min_score=float(payload.get("min_score", 0.0)),  # type: ignore[arg-type]
    )


def _read_survey() -> str | None:
    survey_path = config.DEFAULT_SURVEY_PATH
    if survey_path.is_file():
        return survey_path.read_text(encoding="utf-8")
    return None


def _print_written(written: dict[str, Path]) -> None:
    print("Wrote:")
    for key in sorted(written):
        print(f"  {written[key]}")


def _print_analysis_summary(result: PipelineResult, verifications: dict) -> None:
    valid = [m for m in result.matches if m.decision == "valid_match"]
    invalid = [m for m in result.matches if m.decision == "timestamp_invalid"]
    print(
        f"\n{len(result.signals)} signals x {result.schema_report.rfc_count} RFCs "
        f"-> {len(result.matches)} evaluations "
        f"({len(valid)} valid, {len(invalid)} timestamp-invalid), "
        f"{len(result.ranked_candidates)} ranked candidates, "
        f"{len(result.review_items)} review items."
    )
    if result.ranked_candidates:
        print("\nTop RFC candidates:")
        for candidate in result.ranked_candidates[:5]:
            first_seen = iso(candidate.first_seen) or "n/a"
            print(
                f"  {candidate.rank}. {candidate.rfc_id:<9} score={candidate.score:<8} "
                f"confidence={candidate.confidence:<10} "
                f"observations={candidate.supporting_signal_count:<4} "
                f"first_seen={first_seen}"
            )
    needs_review = sum(
        1 for v in verifications.values() if v.verification_status == "needs_manual_review"
    )
    if needs_review:
        print(f"\n{needs_review} traces flagged for manual review by the deterministic verifier.")


def _print_warnings(warnings: Sequence[str]) -> None:
    if not warnings:
        return
    print(f"\n{len(warnings)} warning(s):")
    for message in warnings:
        print(f"  - {message}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except PipelineError as exc:
        # Expected, actionable failures: report cleanly rather than dumping a
        # traceback at someone who gave us a bad path or a malformed checklist.
        LOGGER.error("%s", exc)
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
