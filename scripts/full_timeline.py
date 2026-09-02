#!/usr/bin/env python3
"""Build the full timeline from a local Parquet cache and analyse it both ways.

Everything here is offline. The OpenINTEL corpus is already mirrored on the
server, so this never lists or fetches from the object store; the RIPE reverse
zones are just another root pointed at the same walker. That is what makes the
run repeatable and un-throttleable -- there is no endpoint to be throttled by.

Five stages, each resumable and each skippable:

    ripe      fetch and ingest RIPE's reverse-delegation archive
    index     walk every root, merge into one view of the corpus
    extract   one tidy timeline row per (source, month, dimension, value)
    analyse   bottom-up over observable changes, top-down over categories
    report    a markdown digest and a compact JSON bundle

Only `ripe` touches the network, and it is plain HTTPS with no rate limiter.

The multi-root walk is the point. Part of the cache was moved to a second drive,
so a source-day can have files on both, and scanning either root alone would
report a *partial* day as a complete one -- indistinguishable from a month when
fewer names were signed. Days are merged by identity across roots and duplicates
counted once; see cache_index.

Usage
-----
    # everything: main cache, spill cache, and RIPE fetched fresh
    python scripts/full_timeline.py \\
        --roots /mnt/data1/openintel --roots /mnt/data2/openintel \\
        --ripe-cache out/reverse/corpus --out out/full_run

    # re-analyse without re-scanning 14 TB
    python scripts/full_timeline.py --stage analyse --stage report --out out/full_run

    # a subsample that still spans every source and the whole period
    python scripts/full_timeline.py --max-days 200 --out out/full_run

    # turn either direction off
    python scripts/full_timeline.py --no-top-down --out out/full_run
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402

from openintel_rfc.cache_index import (  # noqa: E402
    build_inventory, load_inventory, save_inventory,
)
from openintel_rfc.checklist_loader import load_dictionary  # noqa: E402
from openintel_rfc.reverse_zones import ingest_range, monthly_days  # noqa: E402
from openintel_rfc.timeline_analysis import (  # noqa: E402
    bottom_up, compare_directions, cross_reference, load_config, top_down,
)
from openintel_rfc.timeline_extract import (  # noqa: E402
    extract_days, merge_timeline,
)
from openintel_rfc.utils import ensure_dir, get_logger  # noqa: E402

LOGGER = get_logger("full_timeline")
STAGES = ("ripe", "index", "extract", "analyse", "report")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--roots", action="append", default=[], metavar="DIR",
                   help="Cache root. Repeat, or comma-separate, for several drives. "
                        "Point it at the reverse corpus too -- it is just another root.")
    p.add_argument("--out", type=Path, default=REPO / "out" / "full_run",
                   help="Output directory (default: out/full_run).")
    p.add_argument("--config", type=Path, default=REPO / "data" / "analysis_config.json",
                   help="Analysis config driving both directions.")
    p.add_argument("--dictionary", type=Path,
                   default=REPO / "data" / "openintel_dictionary"
                                 / "sample_openintel_dictionary.json",
                   help="Field dictionary used to bind native columns.")

    p.add_argument("--stage", choices=STAGES, action="append", default=[],
                   help="Run only these stages (repeatable). Default: all.")
    p.add_argument("--sources", default=None,
                   help="Comma-separated sources to include (default: all found).")
    p.add_argument("--start", default=None, metavar="YYYY-MM-DD")
    p.add_argument("--end", default=None, metavar="YYYY-MM-DD")
    p.add_argument("--max-days", type=int, default=None,
                   help="Cap source-days to extract. For a smoke test on real data.")

    p.add_argument("--bottom-up", dest="bottom_up", action="store_true", default=None)
    p.add_argument("--no-bottom-up", dest="bottom_up", action="store_false")
    p.add_argument("--top-down", dest="top_down", action="store_true", default=None)
    p.add_argument("--no-top-down", dest="top_down", action="store_false")

    p.add_argument("--ripe-cache", type=Path, default=None, metavar="DIR",
                   help="Where the RIPE reverse-zone corpus lives. The 'ripe' stage "
                        "fetches into it, and it is added to --roots automatically.")
    p.add_argument("--ripe-start", default="2009-03-24", metavar="YYYY-MM-DD")
    p.add_argument("--ripe-end", default=None, metavar="YYYY-MM-DD",
                   help="Default: today.")
    p.add_argument("--ripe-daily", action="store_true",
                   help="Every day instead of one per month. 17 years of dailies is "
                        "6,108 tarballs and several hundred GB; monthly is ~210 and "
                        "still resolves a curve to the month.")
    p.add_argument("--keep-archives", action="store_true",
                   help="Keep the RIPE .tar.bz2 files after parsing.")

    p.add_argument("--pool-sources", action="store_true",
                   help="Additionally extract each day with EVERY source's files "
                        "together, as source '_pooled'. Needed only where sources "
                        "can share a name: reverse-DNS zonelets overlap between "
                        "RIRs, so 1,911 of 6,581 names appear under two of them and "
                        "per-source distinct counts cannot be summed. Forward "
                        "sources are disjoint TLDs and need this off.")

    p.add_argument("--threads", type=int, default=None, help="DuckDB threads.")
    p.add_argument("--memory-limit", default=None, help="DuckDB memory limit, e.g. 32GB.")
    p.add_argument("--no-resume", dest="resume", action="store_false", default=True,
                   help="Re-extract source-days that already have a checkpoint.")
    args = p.parse_args(argv)

    roots: list[str] = []
    for entry in args.roots:
        roots.extend(part for part in str(entry).split(",") if part)
    # The RIPE corpus is discovered by exactly the same walker as the OpenINTEL
    # cache -- it is written in the same layout, so it needs no special case. It
    # is only added once it exists: on a first run the 'ripe' stage creates it,
    # and an `--stage index` before that should not die on a directory whose whole
    # purpose is to be created later.
    if args.ripe_cache is not None and Path(args.ripe_cache).exists():
        ripe_root = Path(args.ripe_cache).as_posix()
        if ripe_root not in roots:
            roots.append(ripe_root)
    args.roots = roots
    args.stages = tuple(args.stage) if args.stage else STAGES
    return args


def _fmt_bytes(n: int) -> str:
    step = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if step < 1024 or unit == "PB":
            return f"{step:.1f} {unit}"
        step /= 1024
    return f"{n} B"


def stage_ripe(args: argparse.Namespace) -> Path:
    """Fetch and ingest RIPE's reverse-delegation archive.

    This is the one stage that touches the network, and it is a different network
    from OpenINTEL's: RIPE publishes plain HTTPS tarballs with no rate limiter, so
    nothing here shares the object store's throttling problem.

    The archive is the only source in the project that yields a true *zone-level*
    denominator -- every delegation is listed, signed or not -- so "share of
    delegations signed" is directly countable rather than inferred from whichever
    names a forward measurement happened to query. It also starts 2009-03-24, nine
    years before the OpenINTEL window, which is what makes an uncensored onset
    possible at all.
    """
    if args.ripe_cache is None:
        raise SystemExit("--ripe-cache is required for the ripe stage.")
    start = date.fromisoformat(args.ripe_start)
    end = date.fromisoformat(args.ripe_end) if args.ripe_end else date.today()
    days = ([start + timedelta(days=i) for i in range((end - start).days + 1)]
            if args.ripe_daily else monthly_days(start, end))

    LOGGER.info("RIPE: %d day(s) from %s to %s (%s)",
                len(days), start, end, "daily" if args.ripe_daily else "monthly")
    warnings: list[str] = []
    reports = ingest_range(
        days,
        cache_dir=args.ripe_cache,
        download_dir=args.ripe_cache / "_archives",
        keep_archive=args.keep_archives,
        warnings=warnings,
    )
    ingested = [r for r in reports if getattr(r, "rows", 0)]
    LOGGER.info("RIPE: %d/%d days ingested; %d unavailable or empty",
                len(ingested), len(days), len(days) - len(ingested))
    for message in warnings[:10]:
        LOGGER.warning("RIPE: %s", message)
    return args.ripe_cache


def stage_index(args: argparse.Namespace) -> Path:
    if not args.roots:
        raise SystemExit("--roots is required for the index stage.")
    LOGGER.info("indexing %d root(s): %s", len(args.roots), ", ".join(args.roots))
    inventory = build_inventory(args.roots)
    target = save_inventory(inventory, args.out / "inventory.json")
    s = inventory.summary()
    LOGGER.info(
        "%d source-days, %d files, %s, sources: %s",
        s["source_days"], s["files"], _fmt_bytes(s["bytes"]), ", ".join(s["sources"]),
    )
    if s["days_split_across_roots"]:
        LOGGER.info(
            "%d source-day(s) span more than one root and were merged.",
            s["days_split_across_roots"],
        )
    if s["unmatched_files"]:
        LOGGER.warning(
            "%d file(s) matched no layout and are NOT in this run; see "
            "inventory.json 'unmatched'.", s["unmatched_files"],
        )
    return target


def _require(path: Path, what: str, produced_by: str) -> Path:
    if not path.exists():
        raise SystemExit(
            f"{what} not found at {path}. Run the '{produced_by}' stage first, or "
            f"point --out at a directory that already has it."
        )
    return path


def stage_extract(args: argparse.Namespace) -> Path:
    inventory = load_inventory(
        _require(args.out / "inventory.json", "Corpus inventory", "index"))
    sources = args.sources.split(",") if args.sources else None
    days = inventory.select(
        sources=sources,
        start=date.fromisoformat(args.start) if args.start else None,
        end=date.fromisoformat(args.end) if args.end else None,
    )
    if args.max_days and args.max_days < len(days):
        # Evenly spaced, NOT the first N. The list is sorted by (source, day), so
        # a prefix is one source's earliest days -- for the reverse corpus that is
        # AFRINIC 2009-2010 and nothing else. A subsample has to span every source
        # and the whole period or it answers a different question than the full run.
        step = len(days) / args.max_days
        days = [days[int(i * step)] for i in range(args.max_days)]
        LOGGER.info("subsampled %d of the matching source-days, evenly spaced",
                    len(days))
    if not days:
        raise SystemExit("No source-days matched the filter; nothing to extract.")

    total_bytes = sum(d.bytes_total for d in days)
    LOGGER.info("extracting %d source-days (%s)", len(days), _fmt_bytes(total_bytes))

    if args.pool_sources:
        # One synthetic day per (basis, date) carrying every source's files, so
        # count(DISTINCT domain) is taken across the whole day rather than summed
        # over sources that share names.
        from collections import defaultdict
        from openintel_rfc.cache_index import CachedDay
        grouped: dict[tuple[str, object], list] = defaultdict(list)
        for day in days:
            grouped[(day.basis, day.day)].append(day)
        # The pooled source name carries WHICH sources it pooled. Without that,
        # `--sources afrinic,arin --pool-sources` and a full pooled run write the
        # same checkpoint filename, and the second silently reuses the first --
        # a panel restricted to two RIRs would quietly report all five.
        pooled = []
        for key, members in sorted(grouped.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            names = sorted({d.source for d in members})
            tag = ("_pooled" if sources is None
                   else "_pooled-" + "-".join(names))
            pooled.append(CachedDay(
                source=tag, day=key[1], basis=key[0],
                paths=[p for d in members for p in d.paths],
                roots={r for d in members for r in d.roots},
                bytes_total=sum(d.bytes_total for d in members)))
        LOGGER.info("pooling: %d day(s) will also be extracted across all sources",
                    len(pooled))
        days = list(days) + pooled

    dictionary = load_dictionary(args.dictionary)
    warnings: list[str] = []
    done, skipped, failed = extract_days(
        days, dictionary, args.out / "checkpoints",
        threads=args.threads, memory_limit=args.memory_limit,
        resume=args.resume, warnings=warnings,
    )
    LOGGER.info("extracted %d, skipped %d (already done or empty), failed %d",
                done, skipped, failed)
    if failed:
        LOGGER.warning(
            "%d source-day(s) failed and were NOT checkpointed -- re-run to retry "
            "them; they are absent from this timeline, not empty in it.", failed)

    timeline = merge_timeline(args.out / "checkpoints")
    if timeline.empty:
        raise SystemExit("Extraction produced no rows; check the roots and dictionary.")
    ensure_dir(args.out)
    timeline.to_parquet(args.out / "timeline_monthly.parquet", index=False)
    timeline.to_csv(args.out / "timeline_monthly.csv", index=False)
    (args.out / "extract_warnings.json").write_text(
        json.dumps(warnings, indent=1), encoding="utf-8")
    LOGGER.info(
        "timeline: %d rows, %d months, %d dimensions",
        len(timeline), timeline.month.nunique(), timeline.dimension.nunique(),
    )
    return args.out / "timeline_monthly.parquet"


def stage_analyse(args: argparse.Namespace) -> dict[str, Any]:
    timeline = pd.read_parquet(
        _require(args.out / "timeline_monthly.parquet", "Timeline", "extract"))
    config = load_config(args.config)

    do_bottom = args.bottom_up if args.bottom_up is not None \
        else config["bottom_up"].get("enabled", True)
    do_top = args.top_down if args.top_down is not None \
        else config["top_down"].get("enabled", True)

    sources = args.sources.split(",") if args.sources else None
    results: dict[str, Any] = {"stages_config": config["stages"]}

    bu: list[dict[str, Any]] = []
    if do_bottom:
        bu = bottom_up(timeline, config, sources=sources)
        (args.out / "bottom_up.json").write_text(
            json.dumps(bu, indent=1), encoding="utf-8")
        pd.DataFrame(bu).to_csv(args.out / "bottom_up.csv", index=False)
        LOGGER.info(
            "bottom-up: %d changes, %d observed, %d reached common usage",
            len(bu),
            sum(1 for r in bu if r.get("t1_first_seen")),
            sum(1 for r in bu if r.get("t3_common_usage")),
        )
        results["bottom_up"] = bu
    else:
        LOGGER.info("bottom-up disabled")

    if do_top:
        td = top_down(timeline, config, bu)
        (args.out / "top_down.json").write_text(
            json.dumps(td, indent=1), encoding="utf-8")
        LOGGER.info("top-down: %d categories", len(td))
        results["top_down"] = td
        if bu:
            comparison = compare_directions(bu, td, config)
            (args.out / "comparison.json").write_text(
                json.dumps(comparison, indent=1), encoding="utf-8")
            results["comparison"] = comparison
    else:
        LOGGER.info("top-down disabled")

    # Cross-corpus check runs whenever both sides are present. It is independent
    # of either direction being enabled: it compares observables, not analyses.
    xref = cross_reference(timeline, config)
    (args.out / "cross_reference.json").write_text(
        json.dumps(xref, indent=1), encoding="utf-8")
    results["cross_reference"] = xref
    for note in xref["notes"]:
        LOGGER.info("cross-ref: %s", note)

    return results


def _bottom_up_table(rows: list[dict[str, Any]]) -> str:
    header = ("| Change | RFC | Published | First seen | Partial | Common | "
              "Onset | Now | State |\n|---|---|---|---|---|---|---|---|---|\n")
    body = []
    for r in sorted(rows, key=lambda x: (x["published"], x["label"])):
        f = lambda v, s="—": (v if v else s)
        share = ("—" if r.get("current_share_pct") is None
                 else f"{r['current_share_pct']:.2f}%")
        onset = "—" if r.get("onset_years") is None else f"{r['onset_years']:.1f}y"
        if r.get("left_censored") and onset != "—":
            onset = "<= " + onset          # first sighting is the corpus start
        body.append(
            f"| {r['label']} | {r['rfc']} | {r['published']} | "
            f"{f(r.get('t1_first_seen'))} | {f(r.get('t2_partial_usage'))} | "
            f"{f(r.get('t3_common_usage'))} | {onset} | {share} | {r['state']} |"
        )
    return header + "\n".join(body) + "\n"


def stage_report(args: argparse.Namespace, results: dict[str, Any]) -> Path:
    inv = json.loads(
        _require(args.out / "inventory.json", "Corpus inventory", "index")
        .read_text(encoding="utf-8"))["summary"]
    bu = results.get("bottom_up", [])
    td = results.get("top_down", [])
    cmp_ = results.get("comparison", {})
    stages = results.get("stages_config", {})

    lines: list[str] = [
        "# Full-run timeline",
        "",
        "## Corpus",
        "",
        f"- roots: {', '.join(inv['roots'])}",
        f"- sources: {', '.join(inv['sources'])}",
        f"- source-days: {inv['source_days']:,}  |  files: {inv['files']:,}  "
        f"|  {_fmt_bytes(inv['bytes'])}",
        f"- days split across roots (merged): {inv['days_split_across_roots']:,}",
        f"- files matching no layout (EXCLUDED): {inv['unmatched_files']:,}",
        f"- duplicate files across roots (counted once): {inv['duplicate_files']:,}",
        "",
        "| Source | Days | Files | Span | Split |",
        "|---|---|---|---|---|",
    ]
    for name, s in inv["per_source"].items():
        lines.append(
            f"| {name} | {s['days']:,} | {s['files']:,} | "
            f"{s['first_day']} .. {s['last_day']} | {s['days_split_across_roots']:,} |"
        )

    if bu:
        observed = [r for r in bu if r.get("t1_first_seen")]
        lines += [
            "", "## Bottom-up: observable changes", "",
            f"Stage thresholds: partial >= {stages.get('partial_usage_pct')}%, "
            f"common >= {stages.get('common_usage_pct')}%, "
            f"both requiring >= {stages.get('min_zones')} distinct names.",
            "",
            f"{len(bu)} changes configured, **{len(observed)} observed**, "
            f"{sum(1 for r in bu if r.get('t2_partial_usage'))} reached partial usage, "
            f"{sum(1 for r in bu if r.get('t3_common_usage'))} reached common usage.",
            "",
            _bottom_up_table(bu),
        ]
        no_cover = [r for r in bu if r["state"] == "no_corpus_coverage"]
        if no_cover:
            lines += [
                "**Not testable in this corpus** (no denominator for the dimension, so "
                "a blank here is not a negative result -- distinct from a change that "
                "was scanned and genuinely never occurred, which shows as "
                "`scanned_no_match`): "
                + ", ".join(sorted(r["label"] for r in no_cover)), "",
            ]

    if td:
        lines += ["", "## Top-down: conceptual categories", "",
                  "| Category | RFCs | Observables | Observed | Onset median | Reached common |",
                  "|---|---|---|---|---|---|"]
        for c in td:
            onset = c.get("onset_years")
            lines.append(
                f"| {c['label']} | {len(c['rfcs'])} | {c['observable_changes']} | "
                f"{c['observed_changes']} | "
                f"{(str(onset['median']) + 'y') if onset else '—'} | "
                f"{c['reached_common']} |"
            )
        gaps = [c for c in td if c["rfcs_without_observables"]]
        if gaps:
            lines += ["", "RFCs in a category with no observable change configured "
                          "(the taxonomy reaches further than the data):", ""]
            for c in gaps:
                lines.append(
                    f"- **{c['label']}**: {', '.join(c['rfcs_without_observables'])}")

    if cmp_:
        lines += ["", "## Where the two directions meet", "",
                  "| Implementation group | Changes | Observed | Onset range |",
                  "|---|---|---|---|"]
        for g in cmp_["implementation_groups"]:
            o = g.get("onset_years")
            span = f"{o['min']:.1f}–{o['max']:.1f}y" if o else "—"
            lines.append(
                f"| {g['label']} | {g['changes']} | {g['observed']} | {span} |"
            )
        lines += ["", cmp_["note"], ""]
        if cmp_["categories_without_observables"]:
            lines.append("Categories with no observable changes at all: "
                         + ", ".join(cmp_["categories_without_observables"]))

    xref = results.get("cross_reference", {})
    if xref.get("comparisons"):
        lines += ["", "## Cross-reference: forward vs reverse", "",
                  f"forward: {', '.join(xref['forward_sources'])}  |  "
                  f"reverse: {', '.join(xref['reverse_sources'])}", "",
                  "| Observable | Fwd first | Rev first | Earliest | Fwd now | Rev now | Δ |",
                  "|---|---|---|---|---|---|---|"]
        for c in xref["comparisons"]:
            g = lambda v, s="—": (v if v is not None else s)
            d = ("—" if c["difference_pct_points"] is None
                 else f"{c['difference_pct_points']:+.1f}pp")
            fs = "—" if c["forward_share_pct"] is None else f"{c['forward_share_pct']:.1f}%"
            rs = "—" if c["reverse_share_pct"] is None else f"{c['reverse_share_pct']:.1f}%"
            lines.append(
                f"| {c['label']} | {g(c['forward_first_seen'])} | "
                f"{g(c['reverse_first_seen'])} | {g(c['earliest_first_seen'])} | "
                f"{fs} | {rs} | {d} |")
        lines += [""] + [f"- {n}" for n in xref["notes"]]
    elif xref.get("notes"):
        lines += ["", "## Cross-reference", ""] + [f"- {n}" for n in xref["notes"]]

    lines += ["", "---", "",
              "Generated by `scripts/full_timeline.py`. The tidy timeline behind every "
              "number is `timeline_monthly.csv`; each row carries its own denominator "
              "as a `_total` row of the same dimension, so any share can be recomputed "
              "against the population it actually belongs to.", ""]

    target = args.out / "summary.md"
    target.write_text("\n".join(lines), encoding="utf-8")

    bundle = {
        "corpus": inv,
        "stages_config": stages,
        "bottom_up": bu,
        "top_down": td,
        "comparison": cmp_,
        "cross_reference": xref,
    }
    (args.out / "analysis_bundle.json").write_text(
        json.dumps(bundle, indent=1), encoding="utf-8")
    LOGGER.info("wrote %s and analysis_bundle.json", target.name)
    return target


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ensure_dir(args.out)

    if "ripe" in args.stages and args.ripe_cache is not None:
        stage_ripe(args)
        # Created by the stage just now, so it can join the roots for this run.
        ripe_root = Path(args.ripe_cache).as_posix()
        if ripe_root not in args.roots:
            args.roots.append(ripe_root)
    elif "ripe" in args.stages:
        LOGGER.info("ripe stage skipped: no --ripe-cache given")
    if "index" in args.stages:
        stage_index(args)
    if "extract" in args.stages:
        stage_extract(args)

    results: dict[str, Any] = {}
    if "analyse" in args.stages:
        results = stage_analyse(args)
    if "report" in args.stages:
        if not results:
            # Reporting on its own re-derives from the timeline rather than
            # requiring the analyse stage to have run in the same process.
            results = stage_analyse(args)
        stage_report(args, results)

    LOGGER.info("done -- outputs under %s", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
