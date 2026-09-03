"""Charts from the separated analysis. Forward and reverse are never pooled.

The pooled series cannot carry a share: the forward sources are 99.6% of the
DS-bearing population while present and stop at 2023-12, so a pooled figure is a
forward number until then and a reverse number afterwards.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RUN = Path(sys.argv[1] if len(sys.argv) > 1 else "out/server_run")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "reporting/charts/framework")
OUT.mkdir(parents=True, exist_ok=True)

TEAL, AMBER, BLUE, BRICK = "#00907f", "#c96a06", "#3f6ad8", "#b32b22"
INK, MUTED, RULE = "#171a14", "#66705c", "#d3d8cc"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.edgecolor": RULE, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
})

split = json.loads((RUN / "split_analysis.json").read_text(encoding="utf-8"))
timeline = pd.read_parquet(RUN / "timeline_monthly.parquet")
REVERSE = split["sides"]["reverse"]["sources"]
FORWARD = split["sides"]["forward"]["sources"]


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  {name}.png")


# --------------------------------------------------------------------------- #
# 1. Forward vs reverse at the one month both cover.
# --------------------------------------------------------------------------- #
x = split["cross_reference"]
month = x["comparison_month"]
# Only observables materially present on at least one side. The ten that read
# 0.00% on both would otherwise fill half the chart with bars of nothing, each
# labelled "agree" -- which is how the headline came to say 14 of 20 agreed.
pairs = [c for c in x["comparisons"]
         if c["difference_pct_points"] is not None
         and c["verdict"] != "absent from both"
         and "still publish" not in c["label"]]
pairs.sort(key=lambda c: -max(c["forward_share_pct"], c["reverse_share_pct"]))
absent = sum(1 for c in x["comparisons"]
             if c.get("verdict") == "absent from both"
             and "still publish" not in c["label"])

fig, ax = plt.subplots(figsize=(10, 0.52 * len(pairs) + 1.4))
y = np.arange(len(pairs))
ax.barh(y - 0.19, [c["forward_share_pct"] for c in pairs], height=0.36,
        color=TEAL, label=f"forward TLDs ({len(FORWARD)} sources)")
ax.barh(y + 0.19, [c["reverse_share_pct"] for c in pairs], height=0.36,
        color=AMBER, label=f"reverse delegations ({len(REVERSE)} RIRs)")
LABEL = {"agree": ("agrees to {gap:.2f} pts", TEAL),
         "disagree": ("{gap:+.0f} pts apart", BRICK),
         "present on one side only": ("one side only, {ratio}", MUTED)}
for i, c in enumerate(pairs):
    hi = max(c["forward_share_pct"], c["reverse_share_pct"])
    gap = c["difference_pct_points"]
    ratio = (f"{c['ratio']:.0f}x apart" if c.get("ratio") else "absent forward")
    tmpl, colour = LABEL[c["verdict"]]
    ax.text(hi + 1.5, i, tmpl.format(gap=abs(gap) if c["verdict"] == "agree" else gap,
                                     ratio=ratio),
            va="center", fontsize=9.5, color=colour,
            fontweight="bold" if c["verdict"] != "present on one side only" else "normal")
ax.set_yticks(y)
ax.set_yticklabels([c["label"] for c in pairs], fontsize=10)
ax.invert_yaxis()
ax.set_xlim(0, 128)
ax.set_xticks([0, 20, 40, 60, 80, 100])
ax.set_xticklabels([f"{v}%" for v in (0, 20, 40, 60, 80, 100)])
ax.set_xlabel(f"share of signed names at {month}   (labels are percentage POINTS, "
              f"not percent)")
ax.set_title(f"{absent} further observables read under 0.5% on both sides and are "
             f"omitted — absent, not agreeing",
             fontsize=10.5, color=MUTED, loc="left", pad=10)
ax.legend(frameon=False, loc="lower right", fontsize=10)
ax.grid(axis="x", color=RULE, lw=0.7)
ax.set_axisbelow(True)
save(fig, "forward_vs_reverse")

# --------------------------------------------------------------------------- #
# 2. The composition break: why the two are never pooled.
# --------------------------------------------------------------------------- #
tot = timeline[(timeline.dimension == "algorithm_ds") & (timeline.value == "_total")]
tot = tot.assign(side=np.where(tot.source.isin(REVERSE), "reverse", "forward"))
piv = tot.pivot_table(index="month", columns="side", values="domains_peak",
                      aggfunc="sum").fillna(0).sort_index()
months = list(piv.index)
fig, ax = plt.subplots(figsize=(10, 4.0))
ax.stackplot(range(len(months)), piv.get("forward", 0), piv.get("reverse", 0),
             colors=[TEAL, AMBER], labels=["forward TLDs", "reverse delegations"])
ax.set_yscale("symlog", linthresh=1000)
ticks = [i for i, m in enumerate(months) if m.endswith("-01") and int(m[:4]) % 3 == 0]
ax.set_xticks(ticks)
ax.set_xticklabels([months[i][:4] for i in ticks])
ax.set_ylabel("DS-bearing names (log)")
brk = months.index("2024-01")
ax.axvline(brk, color=BRICK, lw=1.4, ls="--")
ax.annotate("2024-01: forward sources stop\npooled population falls 99.6%",
            (brk, 6e5), xytext=(-215, -30), textcoords="offset points",
            fontsize=10.5, color=BRICK, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=BRICK, lw=1.2))
ax.legend(frameon=False, loc="upper left", fontsize=10)
ax.grid(axis="y", color=RULE, lw=0.7)
ax.set_axisbelow(True)
save(fig, "composition_break")

print(f"\ncharts in {OUT}")
