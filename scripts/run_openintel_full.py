#!/usr/bin/env python3
"""Run the whole analysis against the full OpenINTEL corpus on the server.

The corpus is split across two drives: a MAIN drive and a SPILL drive holding the years
that did not fit. A source-day can even have files on both. This driver points the
multi-root walker (scripts/full_timeline.py -> openintel_rfc.cache_index) at both, so every
day is the union of its files wherever they live, then re-runs the analyses the notebook
reads. Every step is resumable: re-running skips source-days that already have checkpoints.

Steps (all by default; pick with --step):

    server    index + extract MAIN + SPILL (+ the reverse corpus) -> <run-dir>/server
    panel     index + extract the reverse corpus, AFRINIC + ARIN pooled -> <run-dir>/panel
    coverage  what each drive contributed, per source -> <run-dir>/coverage.json
    analyses  prevalence metrics, Phase 7 (software vs adoption) and the prevalence charts,
              reading <run-dir>/server and <run-dir>/panel -> out/analysis, reporting/charts

Then build the notebook against the new outputs:

    python notebooks/build_software_vs_adoption_notebook.py

Usage on the server:

    python scripts/run_openintel_full.py \\
        --main /mnt/nas_share/Josh --spill /mnt/spill/openintel \\
        --reverse-corpus out/reverse/corpus --run-dir out/openintel_full \\
        --threads 32 --memory-limit 64GB

    # a quick end-to-end check first: 300 evenly spaced source-days
    python scripts/run_openintel_full.py --main ... --spill ... --max-days 300 --run-dir out/openintel_smoke

    # print the commands without running anything
    python scripts/run_openintel_full.py --main ... --spill ... --dry-run

The analyses step OVERWRITES out/analysis/prevalence_metrics.* and software_vs_adoption*,
which are committed for the local run; `git diff out/analysis` then shows exactly what the
full corpus changes. Month labels of a run made now are UTC (d5121351); do not apply
scripts/fix_server_run_month_labels.py to it.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
STEPS = ("server", "panel", "coverage", "analyses")
PANEL_SOURCES = "afrinic,arin"


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--main", required=True, help="Main OpenINTEL drive (cache root).")
    p.add_argument("--spill", action="append", default=[],
                   help="Spill drive with the remaining years. Repeat for more than one.")
    p.add_argument("--reverse-corpus", default=str(ROOT / "out" / "reverse" / "corpus"),
                   help="RIR reverse-zone corpus root (ingested by full_timeline.py --stage ripe). "
                        "Pass '' to leave the reverse corpus out of the server run.")
    p.add_argument("--run-dir", default=str(ROOT / "out" / "openintel_full"),
                   help="Where the two runs, checkpoints and the coverage report go.")
    p.add_argument("--step", action="append", choices=STEPS, default=[],
                   help="Run only these steps (repeatable). Default: all, in order.")
    p.add_argument("--reuse-panel", default=None, metavar="DIR",
                   help="Use an existing panel run (e.g. out/panel_run) instead of building one.")
    p.add_argument("--threads", type=int, default=None)
    p.add_argument("--memory-limit", default=None)
    p.add_argument("--max-days", type=int, default=None,
                   help="Evenly spaced subsample of source-days, for a smoke test.")
    p.add_argument("--start", default=None, metavar="YYYY-MM-DD")
    p.add_argument("--end", default=None, metavar="YYYY-MM-DD")
    p.add_argument("--dry-run", action="store_true", help="Print the commands and stop.")
    a = p.parse_args(argv)
    a.steps = [s for s in STEPS if not a.step or s in a.step]
    return a


def _abs(path: str) -> Path:
    q = Path(path).expanduser()
    return q if q.is_absolute() else (ROOT / q)


def plan(a: argparse.Namespace) -> list[tuple[str, list[str], dict]]:
    """The commands, in order: (step, argv, extra env)."""
    run = _abs(a.run_dir)
    server, panel = run / "server", (_abs(a.reuse_panel) if a.reuse_panel else run / "panel")
    common = []
    if a.threads:
        common += ["--threads", str(a.threads)]
    if a.memory_limit:
        common += ["--memory-limit", a.memory_limit]
    if a.max_days:
        common += ["--max-days", str(a.max_days)]
    if a.start:
        common += ["--start", a.start]
    if a.end:
        common += ["--end", a.end]
    roots = [str(_abs(a.main))] + [str(_abs(s)) for s in a.spill]
    if a.reverse_corpus:
        roots.append(str(_abs(a.reverse_corpus)))
    cmds: list[tuple[str, list[str], dict]] = []
    if "server" in a.steps:
        argv = [PY, str(ROOT / "scripts" / "full_timeline.py")]
        for r in roots:
            argv += ["--roots", r]
        argv += ["--out", str(server), "--stage", "index", "--stage", "extract"] + common
        cmds.append(("server", argv, {}))
    if "panel" in a.steps and not a.reuse_panel:
        if not a.reverse_corpus:
            raise SystemExit("--reverse-corpus is needed to build the panel run (or pass --reuse-panel).")
        argv = [PY, str(ROOT / "scripts" / "full_timeline.py"), "--roots", str(_abs(a.reverse_corpus)),
                "--sources", PANEL_SOURCES, "--pool-sources", "--out", str(panel),
                "--stage", "index", "--stage", "extract"]
        # The panel is the whole reverse corpus (one small file per RIR-month); only the
        # resource limits carry over, never the subsample or date filter of a smoke test.
        if a.threads:
            argv += ["--threads", str(a.threads)]
        if a.memory_limit:
            argv += ["--memory-limit", a.memory_limit]
        cmds.append(("panel", argv, {}))
    if "coverage" in a.steps:
        cmds.append(("coverage", ["<internal>"], {}))
    if "analyses" in a.steps:
        env = {"DNSSEC_SERVER_RUN": str(server), "DNSSEC_PANEL_RUN": str(panel)}
        for script in ("scripts/prevalence_metrics.py", "scripts/software_vs_adoption.py",
                       "reporting/prevalence_metrics.py"):
            cmds.append(("analyses", [PY, str(ROOT / script)], env))
    return cmds


def coverage(a: argparse.Namespace) -> dict:
    """Per source: days, span, and how many days came from each drive (and from both)."""
    run = _abs(a.run_dir)
    inv_path = run / "server" / "inventory.json"
    if not inv_path.exists():
        raise SystemExit(f"{inv_path} not found; run the 'server' step first.")
    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    labels = {str(_abs(a.main).as_posix()): "main"}
    for i, s in enumerate(a.spill):
        labels[str(_abs(s).as_posix())] = "spill" if len(a.spill) == 1 else f"spill{i + 1}"
    if a.reverse_corpus:
        labels[str(_abs(a.reverse_corpus).as_posix())] = "reverse corpus"
    per = defaultdict(lambda: {"days": 0, "first_day": None, "last_day": None,
                               "by_drive": defaultdict(int), "split_days": 0})
    days = inv.get("days", {})
    for d in (days.values() if isinstance(days, dict) else days):
        src, day = d["source"], d["day"]
        roots = sorted(labels.get(r, r) for r in d.get("roots", []))
        e = per[f'{d.get("basis", "?")}/{src}']
        e["days"] += 1
        e["first_day"] = min(filter(None, [e["first_day"], day]))
        e["last_day"] = max(filter(None, [e["last_day"], day]))
        e["by_drive"][" + ".join(roots)] += 1
        e["split_days"] += len(roots) > 1
    summ = inv.get("summary", {})
    out = {"run_dir": str(run), "roots": labels, "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "unmatched_files": summ.get("unmatched_files", len(inv.get("unmatched", []))),
           "duplicate_files": summ.get("duplicate_files", len(inv.get("duplicates", []))),
           "days_split_across_roots": summ.get("days_split_across_roots"),
           "per_source": {k: {**v, "by_drive": dict(v["by_drive"])} for k, v in sorted(per.items())}}
    spill_days = sum(n for v in out["per_source"].values() for k, n in v["by_drive"].items() if "spill" in k)
    out["spill_contributed_days"] = spill_days
    (run / "coverage.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"coverage -> {run / 'coverage.json'}")
    for k, v in out["per_source"].items():
        print(f"  {k:24s} {v['days']:6d} days  {v['first_day']} .. {v['last_day']}  {dict(v['by_drive'])}")
    if a.spill and spill_days == 0:
        print("WARNING: the spill drive contributed no source-days. Check the path and its layout "
              "(<basis>/<source>/<YYYY-MM-DD>/ or fdns/basis=/source=/year=/month=/day=).")
    if out["unmatched_files"]:
        print(f"WARNING: {out['unmatched_files']} file(s) matched no layout and are NOT in the run "
              "(see server/inventory.json 'unmatched').")
    return out


def main(argv=None) -> int:
    a = parse_args(argv)
    for label, path in [("main", a.main)] + [("spill", s) for s in a.spill]:
        if not a.dry_run and not _abs(path).exists():
            raise SystemExit(f"{label} drive not found: {_abs(path)}")
    cmds = plan(a)
    run = _abs(a.run_dir)
    if a.dry_run:
        for step, argv, env in cmds:
            pre = " ".join(f"{k}={shlex.quote(v)}" for k, v in env.items())
            print(f"[{step}] {pre + ' ' if pre else ''}{' '.join(shlex.quote(x) for x in argv)}")
        return 0
    run.mkdir(parents=True, exist_ok=True)
    (run / "run_config.json").write_text(json.dumps({
        "main": str(_abs(a.main)), "spill": [str(_abs(s)) for s in a.spill],
        "reverse_corpus": str(_abs(a.reverse_corpus)) if a.reverse_corpus else None,
        "reuse_panel": a.reuse_panel, "steps": a.steps, "max_days": a.max_days,
        "start": a.start, "end": a.end,
        "git": subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True).stdout.strip(),
        "started": datetime.now(timezone.utc).isoformat(timespec="seconds")}, indent=1) + "\n", encoding="utf-8")
    for step, argv, env in cmds:
        if argv == ["<internal>"]:
            coverage(a)
            continue
        print(f"\n[{step}] {' '.join(shlex.quote(x) for x in argv)}", flush=True)
        r = subprocess.run(argv, cwd=ROOT, env={**os.environ, **env})
        if r.returncode:
            print(f"[{step}] failed with exit code {r.returncode}; fix it and re-run -- finished "
                  "source-days are kept as checkpoints and skipped.")
            return r.returncode
    print(f"\ndone. Now build the notebook:\n  {PY} notebooks/build_software_vs_adoption_notebook.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
