"""One chart: steps in what newly signed zones choose, against OS releases.

Per algorithm family, the share of newly signed reverse delegations that chose
it, per quarter. Steps are marked. Every sourced OS release is a tick along
the top. The point is visual: releases are constant, steps are sporadic, and
each step has a different release behind it.

Reads out/analysis/os_release_attribution.json.
Writes reporting/charts/os_release_attribution.png.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

SURFACE, INK, INK_2, MUTED, BASELINE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#c3c2b7", "#e1e0d9"
S1, CRITICAL = "#2a78d6", "#d03b3b"
plt.rcParams.update({"font.family": ["DejaVu Sans", "sans-serif"], "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
                     "savefig.facecolor": SURFACE, "text.color": INK, "axes.labelcolor": INK_2, "xtick.color": INK_2,
                     "ytick.color": INK_2, "axes.edgecolor": BASELINE, "figure.dpi": 120, "font.size": 10.5})

doc = json.loads(Path("out/analysis/os_release_attribution.json").read_text("utf-8"))


def qx(q):
    return int(q[:4]) + (int(q[5]) - 1) / 4.0


def dx(d):
    return int(d[:4]) + (int(d[5:7]) - 1) / 12.0


fams = ["ECDSA", "RSA/SHA-256"]
fig, axes = plt.subplots(2, 1, figsize=(13.5, 8.4), sharex=True, gridspec_kw={"hspace": 0.3})
for ax, fam in zip(axes, fams):
    f = doc["families"][fam]
    q = f["quarterly"]
    x = [qx(r["q"]) for r in q]
    y = [r["share_pct"] for r in q]
    ax.plot(x, y, color=S1, linewidth=2, zorder=3)
    ax.scatter(x, y, s=[min(90, 10 + r["n"] / 8) for r in q], color=S1, zorder=4, edgecolor=SURFACE, linewidth=0.7)
    for si, st in enumerate(f["steps"]):
        sx = qx(st["quarter"])
        ax.annotate("", xy=(sx, st["to_pct"]), xytext=(sx, st["from_pct"]),
                    arrowprops=dict(arrowstyle="-|>", color=CRITICAL, linewidth=2.2, shrinkA=0, shrinkB=0), zorder=5)
        names = [r["name"] for r in st["os_releases_within_12m_before"]]
        lab = ", ".join(names) if names else "no OS release\nin the year before"
        ax.annotate(f'{st["quarter"]}\n{lab}', (sx, st["to_pct"]), (0, 10 + 26 * (si % 2)),
                    textcoords="offset points", ha="center", va="bottom", fontsize=8, color=CRITICAL, zorder=6)
    for r in doc["os_releases"]:
        ax.plot(dx(r["date"]), 112, marker="|", ms=10, mew=1.5, color=MUTED, ls="none", clip_on=False)
    ax.set_ylim(-4, 108)
    ax.set_ylabel("% of that quarter's\nnew signings", fontsize=10)
    ax.set_title(f'{fam}: {len(f["steps"])} steps', loc="left", fontsize=12, fontweight="bold", pad=18)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID); ax.set_axisbelow(True); ax.tick_params(length=0)
axes[0].annotate("each tick is an OS release (Debian, Ubuntu LTS, RHEL)", (dx("2014-06-09"), 112), (4, 6),
                 textcoords="offset points", fontsize=9, color=MUTED, annotation_clip=False)
axes[-1].xaxis.set_major_locator(MaxNLocator(integer=True, nbins=12))
axes[-1].xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v)}"))
c = doc["chance_a_month_follows_an_os_release"]
fig.suptitle("Operators switch algorithm in sudden batches; OS releases are constant, so the timing cannot pick one out",
             x=0.01, ha="left", fontsize=13, fontweight="bold", y=0.985)
fig.text(0.01, 0.932, f'Each ECDSA step has a different OS release behind it; two RSA/SHA-256 steps have none at all.',
         fontsize=9.5, color=INK_2)
fig.text(0.01, 0.906, f'{c["within_3m"]*100:.0f}% of all months already follow some OS release within 3 months '
                      f'({c["within_6m"]*100:.0f}% within 6), so "a release came just before" is not evidence.',
         fontsize=9.5, color=INK_2)
fig.subplots_adjust(left=0.085, right=0.985, top=0.845, bottom=0.07)
fig.savefig("reporting/charts/os_release_attribution.png", dpi=150)
print("ok")
