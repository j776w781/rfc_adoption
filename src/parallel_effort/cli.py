"""Command-line entry point for the DS/DNSKEY/RRSIG presence-by-month table.

Examples
--------
Walk a NAS cache once, saving the file listing so a re-run does not have to
walk it again, then scan every discovered source-day into checkpoints::

    python -m parallel_effort.cli scan \\
        --cache-root D:\\nas\\openintel \\
        --checkpoint-dir out\\checkpoints \\
        --inventory-cache out\\inventory.json

Merge whatever checkpoints exist into the final table (safe to re-run; only
complete checkpoints are used)::

    python -m parallel_effort.cli merge \\
        --checkpoint-dir out\\checkpoints \\
        --out out\\domain_month_table.parquet --csv

Or do both in one step::

    python -m parallel_effort.cli run \\
        --cache-root D:\\nas\\openintel \\
        --checkpoint-dir out\\checkpoints \\
        --out out\\domain_month_table.parquet --csv

A scan can be scoped and safely re-run: ``--source``, ``--start``/``--end`` and
``--max-days`` narrow what is scanned, and anything already checkpointed is
reused unless ``--no-resume`` is given.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

from openintel_rfc import config
from openintel_rfc.cache_index import build_inventory, load_inventory, save_inventory
from openintel_rfc.checklist_loader import load_dictionary, validate_dictionary
from openintel_rfc.utils import PipelineError, get_logger, warn

from . import presence_table as pt
from . import prevalence as pv
from . import segmented_regression as sr

LOGGER = get_logger(__name__)


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _load_dictionary(path: str | None):
    dictionary = load_dictionary(path or config.DEFAULT_DICTIONARY_PATH)
    warnings: list[str] = []
    for message in validate_dictionary(dictionary):
        warn(warnings, message, LOGGER)
    return dictionary, warnings


def _build_inventory(args: argparse.Namespace):
    inventory_cache = Path(args.inventory_cache) if args.inventory_cache else None
    if inventory_cache is not None and not args.refresh_inventory and inventory_cache.is_file():
        LOGGER.info("Loading cached inventory from %s", inventory_cache)
        return load_inventory(inventory_cache)
    inventory = build_inventory(args.cache_root)
    if inventory_cache is not None:
        save_inventory(inventory, inventory_cache)
        LOGGER.info("Saved cache inventory to %s", inventory_cache)
    return inventory


def _add_duckdb_tuning_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--threads", type=int, default=None, help="DuckDB thread count.")
    parser.add_argument(
        "--memory-limit",
        default=None,
        help="DuckDB memory_limit (e.g. '32GB'). Default: DuckDB's own heuristic "
        "based on available RAM.",
    )
    parser.add_argument(
        "--temp-directory",
        default=None,
        help="Where DuckDB spills intermediate data once memory_limit is exceeded. "
        "Default: the OS temp folder, which may not be the drive with the most "
        "free space -- set this explicitly for a large merge.",
    )


def _add_common_scan_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--cache-root",
        action="append",
        required=True,
        help="Root directory holding OpenINTEL Parquet files. Repeatable for a "
        "cache split across drives.",
    )
    parser.add_argument(
        "--dictionary",
        default=None,
        help="Path to an OpenINTEL analysis dictionary JSON "
        "(default: the project's bundled dictionary).",
    )
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        default=None,
        help="Restrict to this OpenINTEL source/TLD; repeatable. Default: every "
        "source the cache root(s) contain.",
    )
    parser.add_argument("--start", default=None, help="Earliest measurement day, YYYY-MM-DD.")
    parser.add_argument("--end", default=None, help="Latest measurement day, YYYY-MM-DD.")
    parser.add_argument(
        "--max-days",
        type=int,
        default=None,
        help="Cap on the number of source-days scanned, for a smoke run.",
    )
    parser.add_argument(
        "--checkpoint-dir", required=True, help="Directory for per-day checkpoints (resumable)."
    )
    parser.add_argument(
        "--inventory-cache",
        default=None,
        help="Where to save/load the cache file listing, so a large NAS is walked once.",
    )
    parser.add_argument(
        "--refresh-inventory",
        action="store_true",
        help="Re-walk the cache root(s) even if --inventory-cache already exists.",
    )
    parser.add_argument(
        "--no-resume",
        dest="resume",
        action="store_false",
        help="Recompute every day's checkpoint even if a valid one already exists.",
    )
    _add_duckdb_tuning_args(parser)
    parser.set_defaults(resume=True)


def _add_merge_only_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--checkpoint-dir", required=True)
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        default=None,
        help="Restrict the merge to this source/TLD; repeatable.",
    )
    parser.add_argument("--start", default=None)
    parser.add_argument("--end", default=None)
    _add_duckdb_tuning_args(parser)


def cmd_scan(args: argparse.Namespace) -> int:
    dictionary, dict_warnings = _load_dictionary(args.dictionary)
    for message in dict_warnings:
        print(f"warning: {message}", file=sys.stderr)

    inventory = _build_inventory(args)
    for message in inventory.warnings:
        print(f"warning: {message}", file=sys.stderr)

    summary = pt.scan_cache(
        inventory,
        dictionary=dictionary,
        checkpoint_dir=args.checkpoint_dir,
        sources=args.sources,
        start=_parse_date(args.start),
        end=_parse_date(args.end),
        max_days=args.max_days,
        resume=args.resume,
        threads=args.threads,
        memory_limit=args.memory_limit,
        temp_directory=args.temp_directory,
    )
    for message in summary.warnings:
        print(f"warning: {message}", file=sys.stderr)
    print(
        f"Scanned {summary.days_processed} day(s) "
        f"({summary.days_reused} reused checkpoint(s)), {summary.days_failed} failure(s)."
    )
    if summary.failures:
        print("Failed days:", file=sys.stderr)
        for failure in summary.failures:
            print(f"  {failure}", file=sys.stderr)
    return 1 if summary.days_failed and not summary.days_processed else 0


def cmd_merge(args: argparse.Namespace) -> int:
    result = pt.merge_domain_month_table(
        args.checkpoint_dir,
        args.out,
        sources=args.sources,
        start=_parse_date(args.start),
        end=_parse_date(args.end),
        csv=args.csv,
        threads=args.threads,
        memory_limit=args.memory_limit,
        temp_directory=args.temp_directory,
    )
    for message in result.warnings:
        print(f"warning: {message}", file=sys.stderr)
    print(
        f"Wrote {result.row_count} row(s) to {result.output_path} "
        f"from {result.day_checkpoints_used} day checkpoint(s)."
    )
    return 0


def cmd_rollup(args: argparse.Namespace) -> int:
    result = pv.rollup_tld_month_prevalence(args.input, args.out, csv=args.csv)
    print(
        f"Wrote {result.row_count} (tld, month) row(s) to {result.output_path} "
        f"across {len(result.tlds)} TLD(s): {', '.join(result.tlds)}"
    )
    return 0


def cmd_regress(args: argparse.Namespace) -> int:
    out_path = sr.run_segmented_regression(
        args.input,
        args.tld,
        args.cutoff,
        metrics=args.metrics if args.metrics else sr.DEFAULT_METRICS,
        out_path=args.out,
    )
    print(f"\nSaved plot to {out_path}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    scan_rc = cmd_scan(args)
    if scan_rc != 0:
        return scan_rc
    return cmd_merge(args)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="parallel_effort",
        description="Build a month/domain/tld DS-DNSKEY-RRSIG presence table "
        "from a local OpenINTEL Parquet cache.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan the cache into per-day checkpoints.")
    _add_common_scan_args(scan_parser)
    scan_parser.set_defaults(func=cmd_scan)

    merge_parser = subparsers.add_parser(
        "merge", help="Merge existing day checkpoints into the final table."
    )
    _add_merge_only_args(merge_parser)
    merge_parser.add_argument(
        "--out", required=True, help="Output Parquet path for the merged table."
    )
    merge_parser.add_argument(
        "--csv", action="store_true", help="Also write a CSV copy next to the Parquet output."
    )
    merge_parser.set_defaults(func=cmd_merge)

    run_parser = subparsers.add_parser("run", help="Scan then merge in one step.")
    _add_common_scan_args(run_parser)
    run_parser.add_argument(
        "--out", required=True, help="Output Parquet path for the merged table."
    )
    run_parser.add_argument(
        "--csv", action="store_true", help="Also write a CSV copy next to the Parquet output."
    )
    run_parser.set_defaults(func=cmd_run)

    rollup_parser = subparsers.add_parser(
        "rollup",
        help="Aggregate a merged domain-month table into per-TLD monthly prevalence.",
    )
    rollup_parser.add_argument(
        "--input", required=True, help="Path to domain_month_table.parquet (from `merge`)."
    )
    rollup_parser.add_argument(
        "--out", required=True, help="Output Parquet path for the per-(tld, month) table."
    )
    rollup_parser.add_argument(
        "--csv", action="store_true", help="Also write a CSV copy next to the Parquet output."
    )
    rollup_parser.set_defaults(func=cmd_rollup)

    regress_parser = subparsers.add_parser(
        "regress",
        help="Fit a segmented regression (level/slope break at a cutoff month) for one TLD.",
    )
    regress_parser.add_argument(
        "--input", required=True, help="Path to the per-(tld, month) table (from `rollup`)."
    )
    regress_parser.add_argument("--tld", required=True, help="Which TLD to fit.")
    regress_parser.add_argument(
        "--cutoff",
        required=True,
        help="Cutoff month, YYYY-MM (e.g. the RFC's publication month).",
    )
    regress_parser.add_argument(
        "--metrics",
        nargs="+",
        default=None,
        help="Which prevalence columns to fit (default: ds_prevalence dnskey_prevalence "
        "rrsig_prevalence).",
    )
    regress_parser.add_argument(
        "--out", default=None, help="Output PNG path (default: <tld>_segmented_regression.png)."
    )
    regress_parser.set_defaults(func=cmd_regress)

    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PipelineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
