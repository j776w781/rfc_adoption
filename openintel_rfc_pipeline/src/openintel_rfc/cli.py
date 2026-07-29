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
from datetime import date, datetime
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

    scale = sub.add_parser(
        "scale",
        help=(
            "Run a real, resumable analysis over the OpenINTEL S3 corpus across "
            "many TLDs and dates."
        ),
        description=(
            "Streams (or downloads) OpenINTEL partitions, pushes the checklist "
            "match into DuckDB, and aggregates per RFC. Every partition is "
            "checkpointed, so an interrupted run resumes instead of restarting. "
            "Always try --dry-run first."
        ),
    )
    _add_common_inputs(scale)
    scale.add_argument(
        "--sources",
        required=True,
        help="Comma-separated OpenINTEL sources, e.g. 'nu,se,nl'.",
    )
    scale.add_argument("--start", required=True, help="First measurement day, YYYY-MM-DD.")
    scale.add_argument("--end", required=True, help="Last measurement day, YYYY-MM-DD.")
    scale.add_argument(
        "--basis", choices=("zonefile", "toplist"), default="zonefile",
        help="OpenINTEL measurement basis (default: zonefile).",
    )
    scale.add_argument(
        "--mode", choices=("stream", "download"), default="stream",
        help="stream: query object.openintel.nl directly. download: fetch first.",
    )
    scale.add_argument("--cache-dir", type=Path, default=None, help="Cache for --mode download.")
    scale.add_argument(
        "--checkpoint-dir", type=Path, default=None,
        help="Per-partition checkpoints (default: <out>/checkpoints).",
    )
    scale.add_argument("--threads", type=int, default=None, help="DuckDB threads.")
    scale.add_argument(
        "--memory-limit", default=None, help="DuckDB memory limit, e.g. '64GB'."
    )
    scale.add_argument(
        "--max-partitions", type=int, default=None,
        help="Stop after this many partitions (bounded trial run).",
    )
    scale.add_argument(
        "--exemplars", type=int, default=5,
        help="Exemplar observations kept per RFC and decision, for reasoning traces.",
    )
    scale.add_argument(
        "--no-resume", action="store_true",
        help="Recompute every partition, ignoring existing checkpoints.",
    )
    scale.add_argument(
        "--dry-run", action="store_true",
        help="Discover partitions and probe the schema, then stop without scanning.",
    )
    scale.set_defaults(func=cmd_scale)

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


def cmd_scale(args: argparse.Namespace) -> int:
    """Real-corpus run: many partitions, SQL-pushdown matching, checkpointed."""
    from .checklist_loader import (
        load_checklist_db,
        load_dictionary,
        validate_checklist_db,
        validate_dictionary,
    )
    from .exporters import export_analysis
    from .openintel_source import AccessConfig, discover_partitions, probe_schema
    from .report import render_report
    from .scale_runner import ScaleRunConfig, run_scale_analysis
    from .schema_checker import check_schema

    warnings: list[str] = []
    sources = [s.strip() for s in str(args.sources).split(",") if s.strip()]
    if not sources:
        raise PipelineError("--sources must name at least one OpenINTEL source.")

    db = load_checklist_db(args.checklists)
    dictionary = load_dictionary(args.dictionary)
    for message in validate_checklist_db(db) + validate_dictionary(dictionary):
        warn(warnings, message, LOGGER)

    schema_report = check_schema(
        db,
        dictionary,
        checklist_path=str(args.checklists),
        dictionary_path=str(args.dictionary),
        warnings=warnings,
    )

    if args.mode == "download" and args.cache_dir is None:
        raise PipelineError("--mode download requires --cache-dir.")

    access = AccessConfig(
        mode=args.mode,
        cache_dir=Path(args.cache_dir) if args.cache_dir else None,
        threads=args.threads,
        memory_limit=args.memory_limit,
    )

    out_dir = ensure_dir(args.out)
    checkpoint_dir = Path(args.checkpoint_dir) if args.checkpoint_dir else out_dir / "checkpoints"

    if args.dry_run:
        # Everything that can be learned without scanning a single row: how much
        # work the range actually is, and whether the real schema can answer the
        # checklist at all. Both are cheap; discovering either three hours in is
        # not.
        partitions = discover_partitions(
            access, sources, args.start, args.end, basis=args.basis
        )
        print(f"\n{len(partitions)} partition(s) match {args.start}..{args.end} for {', '.join(sources)}")
        for partition in partitions[:15]:
            print(f"  {partition.partition_id:<44} {len(partition.keys)} object(s)")
        if len(partitions) > 15:
            print(f"  ... and {len(partitions) - 15} more")
        if partitions:
            schema = probe_schema(partitions[0], access)
            columns = [c["name"] for c in schema.get("columns", [])]
            print(f"\nReal schema of {partitions[0].partition_id}: {len(columns)} columns")
            _report_field_resolution(dictionary, schema_report, columns)
        _print_warnings(warnings)
        print("\nDry run only; nothing was scanned. Drop --dry-run to start.")
        return 0

    run_config = ScaleRunConfig(
        sources=sources,
        # ScaleRunConfig declares these as dates and formats them into the run
        # manifest; argparse hands over strings.
        start=_parse_run_date(args.start, "--start"),
        end=_parse_run_date(args.end, "--end"),
        basis=args.basis,
        out=out_dir,
        checkpoint_dir=ensure_dir(checkpoint_dir),
        access=access,
        exemplars_per_group=args.exemplars,
        max_partitions=args.max_partitions,
        resume=not args.no_resume,
        # Recorded in run_manifest.json so a result can be traced back to the
        # exact checklist and dictionary that produced it. A multi-day run whose
        # inputs cannot be identified afterwards is not reproducible.
        checklists=str(args.checklists),
        dictionary=str(args.dictionary),
    )

    result = run_scale_analysis(
        run_config, db, dictionary, schema_report, warnings=warnings
    )
    report_md = render_report(result, survey_markdown=_read_survey())
    written = export_analysis(result, out_dir, report_md=report_md)

    # Also emit the schema-check artefacts. A scale run is a long unattended job
    # on a server; requiring a separate `schema-check` invocation afterwards just
    # to populate the dashboard's Schema Check page is friction that will be
    # forgotten, and the report is already computed above at no extra cost.
    from .exporters import export_schema_check
    from .report import render_schema_check_report

    written.update(
        export_schema_check(
            schema_report, out_dir, report_md=render_schema_check_report(schema_report)
        )
    )

    _print_written(written)
    _print_analysis_summary(result, {})
    _print_warnings(result.warnings or warnings)
    return 0


def _parse_run_date(value: object, flag: str) -> date:
    """Parse a CLI date, failing with the flag name rather than a ValueError."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise PipelineError(
            f"{flag} must be a date in YYYY-MM-DD form, got {value!r}."
        ) from exc


def _report_field_resolution(dictionary, schema_report, columns: Sequence[str]) -> None:
    """Say which normalized fields the real corpus can actually supply."""
    from .parquet_reader import resolve_column_candidates
    from .schema_checker import queryable_field_names

    needed = sorted(set(queryable_field_names(schema_report)) | set(config.ALWAYS_SELECT_FIELDS))
    candidates = resolve_column_candidates(dictionary, needed, columns)
    print("\nNormalized field resolution against the real schema:")
    unresolved: list[str] = []
    for field in sorted(candidates):
        cols = candidates[field]
        if cols:
            print(f"  {field:<16} <- {', '.join(cols)}")
        else:
            unresolved.append(field)
            print(f"  {field:<16} <- (nothing; will be all-null)")
    if not unresolved:
        return

    # Separate the two cases: a missing field an indicator actually tests is a
    # reason to stop and fix the dictionary, whereas a missing metadata column
    # only costs provenance detail. Reporting both with the same alarming
    # wording trains the reader to ignore it.
    indicator_fields = set(queryable_field_names(schema_report))
    blocking = [name for name in unresolved if name in indicator_fields]
    cosmetic = [name for name in unresolved if name not in indicator_fields]

    if blocking:
        print(
            "\nWarning: "
            + ", ".join(sorted(blocking))
            + " cannot be supplied by this corpus, and indicator conditions test "
            "them. Those indicators can never match here. Fix the dictionary's "
            "openintel_native_fields before spending compute on this range."
        )
    if cosmetic:
        plural = len(cosmetic) > 1
        print(
            "\nNote: "
            + ", ".join(sorted(cosmetic))
            + (" cannot be supplied by this corpus. No indicator tests "
               + ("them" if plural else "it")
               + ", so matching is unaffected; "
               + ("those columns are" if plural else "the column is")
               + " only carried for provenance and will read as null.")
        )


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
