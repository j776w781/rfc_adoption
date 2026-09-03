"""Two charts for the five-slide deck: the bottom-up bands, and the crosswalk.

The pair exists to make one point visually: sorting observables by what an
implementer must do partitions onset cleanly, and sorting them by conceptual
category does not.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RUN = Path(sys.argv[1] if len(sys.argv) > 1 else "out/server_run")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "reporting/charts/short")
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

sp = json.loads((RUN / "split_analysis.json").read_text(encoding="utf-8"))
cfg = json.loads(Path("data/analysis_config.json").read_text(encoding="utf-8"))

glabel = {k: v["label"] for k, v in cfg["bottom_up"]["groups"].items()}
group_of = {c["label"]: c["group"] for c in cfg["bottom_up"]["changes"]}
rfc_of = {c["label"]: c["rfc"] for c in cfg["bottom_up"]["changes"]}
rfc_cat = {r: c["label"] for c in cfg["top_down"]["categories"] for r in c["rfcs"]}

fwd = {r["label"]: r for r in sp["sides"]["forward"]["bottom_up"]}
rev = {r["label"]: r for r in sp["sides"]["reverse"]["bottom_up"]}

# Earliest onset that is neither censored nor negative. A censored onset is a
# bound and a negative one means the value predates its own RFC; neither can sit
# in a band.
onset = {}
for label in set(fwd) | set(rev):
    cands = [s[label]["onset_years"] for s in (fwd, rev)
             if label in s and s[label].get("onset_years") is not None
             and s[label]["onset_years"] >= 0 and not s[label].get("left_censored")]
    if cands:
        onset[label] = min(cands)


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  {name}.png")


# --------------------------------------------------------------------------- #
# 1. Bottom-up: onset by what the change costs an implementer.
# --------------------------------------------------------------------------- #
groups = defaultdict(list)
for label, y in onset.items():
    groups[group_of.get(label, "?")].append((label, y))
order = sorted(groups, key=lambda k: min(y for _, y in groups[k]))

fig, ax = plt.subplots(figsize=(10, 0.86 * len(order) + 1.2))
for i, key in enumerate(order):
    vals = sorted(groups[key], key=lambda x: x[1])
    lo, hi = vals[0][1], vals[-1][1]
    colour = BRICK if key == "D_new_primitive" else TEAL
    ax.plot([lo, hi], [i, i], color=colour, lw=7, solid_capstyle="round",
            zorder=2, alpha=0.28)
    for label, y in vals:
        ax.plot(y, i, "o", ms=9, color=colour, zorder=3,
                markeredgecolor="white", markeredgewidth=1.6)
    rng = f"{lo:.1f}–{hi:.1f} y" if lo != hi else f"{lo:.1f} y"
    ax.text(hi + 0.18, i, f"{rng}   n={len(vals)}", va="center", fontsize=11,
            color=colour, fontweight="bold")
ax.set_yticks(range(len(order)))
ax.set_yticklabels([glabel[k] for k in order], fontsize=11.5)
ax.invert_yaxis()
ax.set_xlim(0, 5.6)
ax.set_xlabel("onset — years from RFC publication to first sighting in either corpus")
ax.grid(axis="x", color=RULE, lw=0.7)
ax.set_axisbelow(True)
ax.axvspan(1.4, 1.9, color=BRICK, alpha=0.06, zorder=1)
# Above the first row, not below the last: the x-axis label lives down there.
ax.set_ylim(len(order) - 0.5, -1.05)
ax.text(1.65, -0.78, "the one real gap\n1.4 → 1.9 y", ha="center", va="center",
        fontsize=10, color=BRICK, fontweight="bold")
save(fig, "bottom_up_bands")

# --------------------------------------------------------------------------- #
# 2. The crosswalk: the same observables sorted the other way.
# --------------------------------------------------------------------------- #
cats = defaultdict(list)
for label, y in onset.items():
    cats[rfc_cat.get(rfc_of.get(label, ""), "(uncategorised)")].append((label, y))
corder = sorted(cats, key=lambda k: -(max(y for _, y in cats[k])
                                      - min(y for _, y in cats[k])))

fig, ax = plt.subplots(figsize=(10, 0.86 * len(corder) + 1.2))
for i, key in enumerate(corder):
    vals = sorted(cats[key], key=lambda x: x[1])
    lo, hi = vals[0][1], vals[-1][1]
    wide = (hi - lo) > 2
    colour = BRICK if wide else MUTED
    ax.plot([lo, hi], [i, i], color=colour, lw=7, solid_capstyle="round",
            zorder=2, alpha=0.28)
    for label, y in vals:
        ax.plot(y, i, "o", ms=9, color=colour, zorder=3,
                markeredgecolor="white", markeredgewidth=1.6)
    rng = f"{lo:.1f}–{hi:.1f} y" if lo != hi else f"{lo:.1f} y"
    ax.text(hi + 0.18, i, f"{rng}   n={len(vals)}", va="center", fontsize=11,
            color=colour, fontweight="bold" if wide else "normal")
ax.set_yticks(range(len(corder)))
ax.set_yticklabels([k if len(k) < 40 else k[:38] + "…" for k in corder], fontsize=11.5)
ax.invert_yaxis()
ax.set_xlim(0, 5.6)
ax.set_xlabel("onset — the same observables, grouped by conceptual category instead")
ax.grid(axis="x", color=RULE, lw=0.7)
ax.set_axisbelow(True)
save(fig, "top_down_bands")

print(f"\ncharts in {OUT}")
