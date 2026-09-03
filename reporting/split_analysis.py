"""Analyse the two corpora separately, because pooling them is not defensible.

The full run's timeline pools forward and reverse sources. That cannot support a
prevalence figure: the forward sources are 99.6% of the DS-bearing population
while they are present, and they stop at 2023-12. A pooled share is therefore a
forward number until 2023-12 and a reverse number afterwards, with a -99.6% step
between the two, and any peak-to-latest comparison spans that step.

So each side is analysed on its own, and the only cross-corpus statement made is
at a month both sides cover.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openintel_rfc.timeline_analysis import (  # noqa: E402
    bottom_up, cross_reference, detect_breaks, load_config, top_down,
)

RUN = Path(sys.argv[1] if len(sys.argv) > 1 else "out/server_run")
CONFIG = Path(sys.argv[2] if len(sys.argv) > 2 else "data/analysis_config.json")

REVERSE = ["afrinic", "apnic", "arin", "lacnic", "ripe"]

timeline = pd.read_parquet(RUN / "timeline_monthly.parquet")
config = load_config(CONFIG)
forward = sorted(set(timeline.source.unique()) - set(REVERSE))
reverse = sorted(set(timeline.source.unique()) & set(REVERSE))

out = {"sides": {}}
for name, sources in (("forward", forward), ("reverse", reverse)):
    sub = timeline[timeline.source.isin(sources)]
    rows = bottom_up(sub, config, sources=sources)
    cats = top_down(sub, config, rows)
    span = (sub.month.min(), sub.month.max())
    out["sides"][name] = {
        "sources": sources,
        "months": span,
        "rows": len(sub),
        "bottom_up": rows,
        "top_down": cats,
    }
    obs = [r for r in rows if r.get("t1_first_seen")]
    print(f"{name}: {len(sources)} sources, {span[0]}..{span[1]}, "
          f"{len(obs)}/{len(rows)} observables seen")

out["cross_reference"] = cross_reference(timeline, config,
                                        forward_sources=forward,
                                        reverse_sources=reverse)
out["breaks"] = detect_breaks(timeline)

# Existence is a minimum over all evidence, so first sighting is the one figure
# that is legitimately taken across both corpora at once.
merged = []
fwd = {r["label"]: r for r in out["sides"]["forward"]["bottom_up"]}
rev = {r["label"]: r for r in out["sides"]["reverse"]["bottom_up"]}
for label in sorted(set(fwd) | set(rev)):
    f, r = fwd.get(label, {}), rev.get(label, {})
    seen = [d for d in (f.get("t1_first_seen"), r.get("t1_first_seen")) if d]
    merged.append({
        "label": label,
        "rfc": (f or r).get("rfc"),
        "published": (f or r).get("published"),
        "group": (f or r).get("group"),
        "forward_first_seen": f.get("t1_first_seen"),
        "reverse_first_seen": r.get("t1_first_seen"),
        "first_seen": min(seen) if seen else None,
        "earlier_side": (None if not seen else
                         "forward" if f.get("t1_first_seen") == min(seen)
                         and f.get("t1_first_seen") != r.get("t1_first_seen")
                         else "reverse" if r.get("t1_first_seen") == min(seen)
                         and f.get("t1_first_seen") != r.get("t1_first_seen")
                         else "both"),
        "forward_share_pct": f.get("current_share_pct"),
        "forward_last_month": f.get("last_month"),
        "reverse_share_pct": r.get("current_share_pct"),
        "reverse_last_month": r.get("last_month"),
    })
out["first_seen_across_corpora"] = merged

(RUN / "split_analysis.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(f"\nwrote {RUN / 'split_analysis.json'}")
for note in out["breaks"][:6]:
    print(f"  break: {note}")
