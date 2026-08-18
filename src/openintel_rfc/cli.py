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
from .config import DEFAULT_MAX_PACE_SECONDS, DEFAULT_PACE_SECONDS
from .models import PipelineResult, RunConfig
from .utils import PipelineError, ensure_dir, get_logger, iso, now, posix_path, warn

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
        "--basis", choices=("zonefile", "toplist", "reverse"), default="zonefile",
        help=(
            "Measurement basis (default: zonefile). 'reverse' selects a corpus "
            "built by 'ingest-reverse' and requires --local-corpus."
        ),
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
        "--partition-retries", type=int, default=5,
        help=(
            "Retries per partition on a transient object-store failure (503, "
            "timeout). Waits double from --retry-wait. Default: 5."
        ),
    )
    scale.add_argument(
        "--retry-wait", type=float, default=30.0,
        help="Seconds before the first partition retry; doubles thereafter.",
    )
    scale.add_argument(
        "--pace-seconds", type=float, default=DEFAULT_PACE_SECONDS,
        help=(
            "Smallest gap between partitions. OpenINTEL sits behind a limiter "
            "measured at about one request per second with a burst of five, so "
            "this is what keeps a run inside the budget rather than discovering "
            "the edge of it. The gap is adaptive -- it widens when the store "
            f"pushes back and relaxes when it stops. Default: {DEFAULT_PACE_SECONDS}."
        ),
    )
    scale.add_argument(
        "--max-pace-seconds", type=float, default=DEFAULT_MAX_PACE_SECONDS,
        help=(
            "Ceiling for the adaptive gap. Past this the run is stuck rather than "
            f"slow, and that should be visible. Default: {DEFAULT_MAX_PACE_SECONDS}."
        ),
    )
    scale.add_argument(
        "--shards", type=int, default=1,
        help=(
            "How many processes are sharing the store's budget with this one, "
            "including this one. A sharded run MUST set it: the limiter is per "
            "endpoint, not per process, so N shards each pacing for the whole "
            "budget is N times over it. Default: 1."
        ),
    )
    scale.add_argument(
        "--local-corpus", action="store_true",
        help=(
            "Discover partitions from --cache-dir instead of listing the object "
            "store. Required for a corpus the store does not host (see "
            "'ingest-reverse'), and worth it for a full mirror too: discovery "
            "otherwise costs one LIST per partition-day even when every byte is "
            "already local."
        ),
    )
    scale.add_argument(
        "--dry-run", action="store_true",
        help="Discover partitions and probe the schema, then stop without scanning.",
    )
    scale.set_defaults(func=cmd_scale)

    mirror = sub.add_parser(
        "mirror",
        help="Download the objects a run needs, once, so later scans are local.",
        description=(
            "Copies OpenINTEL objects to local disk in the layout "
            "'--mode download --cache-dir' expects. One request per object, paid "
            "once: mirroring the 2.07 TB this project scans costs about 7,261 "
            "requests (two hours of the store's ~1 req/s budget), after which "
            "every scan is local and costs the store nothing. Split across "
            "machines with --shard/--shards; the split balances bytes, not days, "
            "because .se is 1.49 TB of the corpus and .gov is 15.8 GB."
        ),
    )
    mirror.add_argument("--sources", required=True,
                        help="Comma-separated sources, e.g. gov,nu,se.")
    mirror.add_argument("--start", required=True, help="First day, YYYY-MM-DD.")
    mirror.add_argument("--end", required=True, help="Last day, YYYY-MM-DD.")
    mirror.add_argument("--basis", default="zonefile", choices=["zonefile", "toplist"])
    mirror.add_argument("--cache-dir", type=Path, required=True,
                        help="Destination. Pass the same path to 'scale --cache-dir'.")
    mirror.add_argument(
        "--shards", type=int, default=1,
        help=(
            "Total machines sharing this mirror. Extra machines only help when "
            "they have their own network path: two hosts behind one NAT share "
            "one request budget and one uplink. Default: 1."
        ),
    )
    mirror.add_argument(
        "--shard", type=int, default=0,
        help="Which shard THIS machine fetches, 0-based. Default: 0.",
    )
    mirror.add_argument(
        "--pace-seconds", type=float, default=DEFAULT_PACE_SECONDS,
        help="Smallest gap between objects; widens if the store pushes back.",
    )
    mirror.add_argument(
        "--plan-only", action="store_true",
        help="Print the shard balance and the byte totals, then stop.",
    )
    mirror.add_argument(
        "--dry-run", action="store_true",
        help="Report what would be fetched without writing anything.",
    )
    mirror.set_defaults(func=cmd_mirror)

    ingest = sub.add_parser(
        "ingest-reverse",
        help="Build a local corpus from RIPE's historical reverse-DNS zones.",
        description=(
            "Downloads RIPE NCC's daily reverse-delegation archive (in-addr.arpa "
            "and ip6.arpa, carrying all five RIRs' zonelets), parses the DS and "
            "delegation records out of it, and writes Parquet in OpenINTEL's "
            "native column names so the existing checklists match it unchanged. "
            "The archive starts 2009-03-24, nine years before the OpenINTEL "
            "window, and unlike OpenINTEL it yields a true zone-level denominator: "
            "every delegation is listed, so 'share of delegations signed' is "
            "directly countable."
        ),
    )
    ingest.add_argument("--start", required=True, help="First day, YYYY-MM-DD.")
    ingest.add_argument("--end", required=True, help="Last day, YYYY-MM-DD.")
    ingest.add_argument("--cache-dir", type=Path, required=True,
                        help="Where the Parquet corpus is written.")
    ingest.add_argument("--download-dir", type=Path, default=None,
                        help="Scratch for tarballs (default: <cache-dir>/_archives).")
    ingest.add_argument(
        "--monthly", action="store_true",
        help=(
            "One day per month instead of every day. 17 years of dailies is 6,108 "
            "tarballs and several hundred GB; monthly is ~210 and still resolves an "
            "adoption curve to the month."
        ),
    )
    ingest.add_argument("--keep-archives", action="store_true",
                        help="Keep the .tar.bz2 files after parsing.")
    ingest.set_defaults(func=cmd_ingest_reverse)

    merge = sub.add_parser(
        "merge",
        help="Build the final report from existing checkpoints, without scanning.",
        description=(
            "Merges partition checkpoints that were already computed -- by an "
            "earlier run, or by several machines working on different date "
            "ranges -- into one set of artefacts. Reads no measurement data and "
            "makes no network calls, so it also works where 'scale' would try to "
            "rediscover and rescan partitions that are absent from the range."
        ),
    )
    _add_common_inputs(merge)
    merge.add_argument(
        "--checkpoint-dir", type=Path, required=True,
        help="Directory of checkpoints. Searched recursively unless --flat.",
    )
    merge.add_argument(
        "--flat", action="store_true",
        help="Only look in the top level, not in per-shard subdirectories.",
    )
    merge.add_argument(
        "--min-score", type=float, default=config.MIN_RANKABLE_SCORE,
        help="Drop ranked candidates scoring at or below this value.",
    )
    merge.set_defaults(func=cmd_merge)

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
        checklist_path=posix_path(args.checklists),
        dictionary_path=posix_path(args.dictionary),
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
        checklist_path=posix_path(run_config.checklists),
        dictionary_path=posix_path(run_config.dictionary),
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
        checklist_path=posix_path(args.checklists),
        dictionary_path=posix_path(args.dictionary),
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

    # Validate the source names before anything expensive. OpenINTEL publishes a
    # specific set under each basis, and a typo or an unavailable source
    # (".com" and ".nl" are not published) otherwise costs a full walk that
    # silently finds nothing for that source -- which reads as "no adoption"
    # rather than "no data".
    _validate_sources(access, sources, args.basis, warnings)

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
        checklists=posix_path(args.checklists),
        dictionary=posix_path(args.dictionary),
        partition_retries=args.partition_retries,
        partition_retry_wait_seconds=args.retry_wait,
        pace_seconds=args.pace_seconds,
        max_pace_seconds=args.max_pace_seconds,
        shards=args.shards,
    )

    # A local corpus is discovered from disk. That is required for a basis the
    # object store never hosted (see 'ingest-reverse'), and it also spares a
    # fully mirrored run one LIST per partition-day just to confirm what is
    # already there.
    partitions = None
    if args.local_corpus:
        from .openintel_source import discover_local_partitions

        if args.cache_dir is None:
            raise PipelineError("--local-corpus requires --cache-dir.")
        partitions = discover_local_partitions(
            args.cache_dir, sources,
            _parse_run_date(args.start, "--start"),
            _parse_run_date(args.end, "--end"),
            basis=args.basis, warnings=warnings,
        )
        LOGGER.info("Local corpus: %d partition(s) under %s",
                    len(partitions), args.cache_dir)

    result = run_scale_analysis(
        run_config, db, dictionary, schema_report,
        warnings=warnings, partitions=partitions,
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


def cmd_mirror(args: argparse.Namespace) -> int:
    """Mirror this machine's share of the corpus.

    Deliberately does no analysis. Fetching and scanning have completely
    different failure modes and completely different reruns -- a mirror is
    interrupted and resumed, an analysis is re-run whenever the checklist changes
    -- and coupling them is what made the store part of the inner loop.
    """
    from .mirror import describe_plan, list_objects, mirror_objects, plan_shards
    from .openintel_source import AccessConfig, build_s3_client
    from .scale_runner import ThrottleGovernor

    sources = [s.strip() for s in str(args.sources).split(",") if s.strip()]
    if not sources:
        raise PipelineError("--mirror --sources must name at least one source.")
    if not 0 <= args.shard < max(args.shards, 1):
        raise PipelineError(
            f"--shard {args.shard} is outside --shards {args.shards}; shards are "
            f"0-based, so the valid range is 0..{max(args.shards, 1) - 1}."
        )

    access = AccessConfig(mode="download", cache_dir=args.cache_dir)
    client = build_s3_client(access)

    LOGGER.info("Listing objects for %s between %s and %s",
                ", ".join(sources), args.start, args.end)
    objects = list_objects(access, sources=sources, start=args.start, end=args.end,
                           basis=args.basis, client=client)
    if not objects:
        LOGGER.warning("No objects matched; nothing to mirror.")
        return 0

    total = sum(o.size for o in objects)
    LOGGER.info("Corpus: %d object(s), %.1f GB", len(objects), total / 1e9)

    buckets = plan_shards(objects, args.shards)
    if args.shards > 1 or args.plan_only:
        LOGGER.info("Shard plan:%s%s", chr(10), describe_plan(buckets))

    mine = buckets[args.shard]
    share = sum(o.size for o in mine)
    LOGGER.info("This machine (shard %d of %d): %d object(s), %.1f GB",
                args.shard, args.shards, len(mine), share / 1e9)

    if args.plan_only:
        return 0

    report = mirror_objects(
        mine,
        config=access,
        cache_dir=args.cache_dir,
        governor=ThrottleGovernor(floor_seconds=args.pace_seconds),
        client=client,
        dry_run=args.dry_run,
    )
    print(report.describe())
    if not report.complete:
        # Not a hard failure: a mirror is resumable, and the useful next action is
        # to run it again rather than to start over.
        print(
            f"{report.failed} object(s) did not transfer. Re-run the same command; "
            "objects already present are skipped."
        )
        return 1
    return 0


def cmd_ingest_reverse(args: argparse.Namespace) -> int:
    """Build the RIPE reverse-delegation corpus on local disk."""
    from .openintel_source import date_range
    from .reverse_zones import ingest_range, monthly_days

    start, end = _parse_run_date(args.start, "--start"), _parse_run_date(args.end, "--end")
    days = monthly_days(start, end) if args.monthly else date_range(start, end)
    download_dir = args.download_dir or (args.cache_dir / "_archives")

    LOGGER.info("Ingesting %d day(s) of reverse-DNS zones into %s",
                len(days), args.cache_dir)
    warnings: list[str] = []
    reports = ingest_range(
        days,
        cache_dir=args.cache_dir,
        download_dir=download_dir,
        keep_archive=args.keep_archives,
        warnings=warnings,
    )

    delegations = sum(r.delegations for r in reports)
    signed = sum(r.signed_delegations for r in reports)
    print(
        f"ingested {len(reports)}/{len(days)} day(s): "
        f"{sum(r.rows for r in reports):,} rows, "
        f"{sum(r.ds_records for r in reports):,} DS records, "
        f"{delegations:,} delegation-days, "
        f"{signed / delegations * 100 if delegations else 0:.3f}% signed"
    )
    for message in warnings[:10]:
        print(f"  warning: {message}")
    return 0 if reports else 1


def cmd_merge(args: argparse.Namespace) -> int:
    """Assemble final artefacts from checkpoints alone -- no scanning, no network."""
    from .checklist_loader import (
        load_checklist_db,
        load_dictionary,
        validate_checklist_db,
        validate_dictionary,
    )
    from .exporters import export_analysis, export_schema_check
    from .models import PipelineResult, RunConfig
    from .report import render_report, render_schema_check_report
    from .scale_runner import (
        aggregates_to_candidates,
        aggregates_to_timeline,
        merge_checkpoints,
    )
    from .schema_checker import check_schema

    warnings: list[str] = []
    db = load_checklist_db(args.checklists)
    dictionary = load_dictionary(args.dictionary)
    for message in validate_checklist_db(db) + validate_dictionary(dictionary):
        warn(warnings, message, LOGGER)

    schema_report = check_schema(
        db,
        dictionary,
        checklist_path=posix_path(args.checklists),
        dictionary_path=posix_path(args.dictionary),
        warnings=warnings,
    )

    checkpoint_dir = Path(args.checkpoint_dir)
    aggregates = merge_checkpoints(checkpoint_dir, recursive=not args.flat)
    for message in aggregates.warnings:
        warn(warnings, message, LOGGER)
    if not aggregates.partition_ids:
        raise PipelineError(
            f"No usable checkpoints under {checkpoint_dir}. Expected files named "
            "<partition>.parquet with a matching <partition>.status.json marked "
            "complete."
        )
    LOGGER.info(
        "Merged %d partition(s), %s row(s) scanned.",
        len(aggregates.partition_ids),
        f"{aggregates.rows_scanned:,}",
    )

    candidates = aggregates_to_candidates(
        aggregates, db, schema_report=schema_report,
        min_score=args.min_score, warnings=warnings,
    )
    timeline = aggregates_to_timeline(
        aggregates, db, schema_report=schema_report, warnings=warnings
    )
    signals, matches, traces = aggregates.evidence(
        db, schema_report=schema_report, warnings=warnings
    )

    out_dir = ensure_dir(args.out)
    result = PipelineResult(
        generated_at=now(),
        run_config=RunConfig(
            checklists=posix_path(args.checklists),
            dictionary=posix_path(args.dictionary),
            parquet=None,
            out=posix_path(out_dir),
            min_score=args.min_score,
        ),
        schema_report=schema_report,
        signals=signals,
        matches=matches,
        ranked_candidates=candidates,
        traces=traces,
        review_items=[],
        timeline=timeline,
        warnings=warnings,
        corpus_stats={
            "sampled": True,
            "rows_scanned": int(aggregates.rows_scanned),
            "rows_matched": int(aggregates.rows_matched),
            "partitions": len(aggregates.partition_ids),
            "exemplar_signals": len(signals),
            "sources": sorted({p.split("/")[1] for p in aggregates.partition_ids if "/" in p}),
        },
    )

    from .llm_verifier import get_verifier
    from .ranking import close_ranking_pairs
    from .review_queue import build_review_queue

    result.review_items = build_review_queue(
        schema_report=schema_report,
        matches=matches,
        traces=traces,
        ranked=candidates,
        db=db,
        verifier=get_verifier(),
        warnings=warnings,
        close_pairs=close_ranking_pairs(candidates),
    )

    report_md = render_report(result, survey_markdown=_read_survey())
    written = export_analysis(result, out_dir, report_md=report_md)
    written.update(
        export_schema_check(
            schema_report, out_dir, report_md=render_schema_check_report(schema_report)
        )
    )

    _print_written(written)
    _print_analysis_summary(result, {})
    _print_warnings(result.warnings)
    return 0


def _validate_sources(
    access: object, sources: Sequence[str], basis: str, warnings: list[str]
) -> None:
    """Fail early on a source OpenINTEL does not publish under this basis."""
    from .openintel_source import list_sources

    try:
        available = list_sources(access, basis=basis)  # type: ignore[arg-type]
    except PipelineError as exc:
        # Listing is a convenience, not a precondition: an offline or restricted
        # host should still be able to run against a cache.
        warn(warnings, f"Could not list available OpenINTEL sources ({exc}).", LOGGER)
        return

    if not available:
        return
    unknown = [s for s in sources if s not in available]
    if not unknown:
        LOGGER.info("Sources %s are all published under basis=%s.", ", ".join(sources), basis)
        return

    raise PipelineError(
        f"OpenINTEL does not publish {', '.join(unknown)} under basis={basis}. "
        f"Available: {', '.join(available)}. "
        "Refusing to start: a source with no objects produces no matches, which "
        "is indistinguishable in the output from a source with no adoption."
    )


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
        # Relative paths in a run config are project-relative, which is how
        # examples/sample_run_config.json is written ("data/rfc_checklists/...").
        #
        # Resolving them against the config file's own grandparent -- as this did
        # -- only works when the file sits exactly one level under the root. A
        # config at the root resolved outside the repository entirely, and one two
        # levels down resolved into a sibling directory. PROJECT_ROOT is derived
        # from the package location, so it is correct wherever the config lives.
        base = config.PROJECT_ROOT
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
        checklists=posix_path(payload["checklists"]),
        dictionary=posix_path(payload["dictionary"]),
        parquet=posix_path(payload["parquet"]) if payload.get("parquet") else None,
        out=posix_path(payload["out"]),
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
