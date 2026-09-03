"""Charts for the framework deck. Every number comes from out/panel_run.

Rendered as PNG rather than drawn in the deck, because Google Slides re-flows
native chart objects unpredictably on import and a picture survives the round
trip intact.

Palette is the one validated for colour-vision deficiency in this project:
teal / amber / blue / brick, worst adjacent pair dE 12.0 under protanopia.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RUN = Path(sys.argv[1] if len(sys.argv) > 1 else "out/panel_run")
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


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print(f"  {name}.png")


curves = json.load(open(RUN / "curves.json"))
BUNDLE = Path(sys.argv[3]) if len(sys.argv) > 3 else None
if BUNDLE and BUNDLE.exists():
    bottom_up = json.load(open(BUNDLE))["bottom_up"]
    SCOPE = "full corpus"
else:
    bottom_up = json.load(open(RUN / "bottom_up.json"))
    SCOPE = "reverse corpus"
print(f"  onsets from: {SCOPE}")


def months_axis(ax, months):
    ticks = [i for i, m in enumerate(months) if m.endswith("-01") and int(m[:4]) % 3 == 0]
    ax.set_xticks(ticks)
    ax.set_xticklabels([months[i][:4] for i in ticks])


# --------------------------------------------------------------------------- #
# 1. The measure we use: share of signed delegations. Rises AND falls.
# --------------------------------------------------------------------------- #
SERIES = [("ECDSA P-256", TEAL), ("RSA/SHA-256", AMBER),
          ("RSASHA1-NSEC3", BLUE), ("RSASHA1", BRICK)]
months = sorted({m for n, _ in SERIES for m in curves[n]})

fig, ax = plt.subplots(figsize=(10, 4.6))
for name, colour in SERIES:
    y = [curves[name].get(m) for m in months]
    ax.plot(range(len(months)), y, color=colour, lw=2.2, label=name)
    last = max(i for i, v in enumerate(y) if v is not None)
    ax.annotate(f"{y[last]:.1f}%", (last, y[last]), xytext=(8, -3),
                textcoords="offset points", color=colour, fontsize=10.5,
                fontweight="bold")
ax.set_ylim(0, 105)
ax.set_ylabel("share of signed delegations")
months_axis(ax, months)
ax.grid(axis="y", color=RULE, lw=0.7)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper center", ncol=4, fontsize=10,
          bbox_to_anchor=(0.5, 1.14))
save(fig, "share_measure")

# --------------------------------------------------------------------------- #
# 2. Why the diffusion literature does not fit: one series, both readings.
# --------------------------------------------------------------------------- #
cumulative = json.load(open(RUN / "cumulative.json")) if (RUN / "cumulative.json").exists() else None
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))

y = np.array([curves["RSA/SHA-256"].get(m, np.nan) for m in months], dtype=float)
a1.plot(range(len(months)), y, color=AMBER, lw=2.4)
peak = int(np.nanargmax(y))
last = int(np.max(np.flatnonzero(~np.isnan(y))))
# Anchored to the points themselves, and offset away from the curve on each
# side, so neither label can land on the line or on the caption.
a1.annotate(f"peak {y[peak]:.1f}%", (peak, y[peak]), xytext=(6, 12),
            textcoords="offset points", color=AMBER, fontweight="bold",
            fontsize=11)
a1.annotate(f"{y[last]:.1f}% today", (last, y[last]), xytext=(-8, -22),
            textcoords="offset points", color=AMBER, fontweight="bold",
            fontsize=11, ha="right")
a1.set_title("What we measure: share today", fontsize=12, color=INK, pad=12)
a1.set_ylabel("RSA/SHA-256, % of signed delegations")
a1.set_ylim(0, 92)
months_axis(a1, months)
a1.grid(axis="y", color=RULE, lw=0.7); a1.set_axisbelow(True)
a1.text(0.30, 0.94, "rises AND falls", transform=a1.transAxes,
        color=BRICK, fontsize=11.5, fontweight="bold")

t = np.linspace(0, 10, 200)
a2.plot(t, 100 / (1 + np.exp(-(t - 5))), color=MUTED, lw=2.4)
a2.set_title("What Rogers / Bass model: cumulative adopters", fontsize=12,
             color=INK, pad=12)
a2.set_ylabel("% who have EVER adopted")
a2.set_ylim(0, 105)
a2.set_xticks([])
a2.grid(axis="y", color=RULE, lw=0.7); a2.set_axisbelow(True)
for frac, lbl in [(2.5, "innovators 2.5%"), (16, "early adopters 16%"),
                  (50, "early majority 50%"), (84, "late majority 84%")]:
    a2.axhline(frac, color=RULE, lw=1, ls=":")
    a2.text(10.2, frac, lbl, fontsize=8.5, color=MUTED, va="center")
a2.text(0.02, 0.92, "can only go up", transform=a2.transAxes,
        color=MUTED, fontsize=11, fontweight="bold")
save(fig, "why_not_rogers")

# --------------------------------------------------------------------------- #
# 3. Onset does not predict spread.
# --------------------------------------------------------------------------- #
# Peak share, not today's share: "today" is 2023-12 for forward-only dimensions
# and 2026-08 for DS ones, because the forward sources stop in 2023. Comparing
# those in one scatter would put two different dates on one axis.
pts = [r for r in bottom_up
       if r.get("onset_years") is not None and r["onset_years"] >= 0
       and not r["is_residue"] and not r["left_censored"]
       and r.get("peak_share_pct") is not None]
for r in pts:
    r["_y"] = r["peak_share_pct"]
fig, ax = plt.subplots(figsize=(9.6, 4.8))
for r in pts:
    c = TEAL if r["_y"] >= 5 else AMBER
    ax.scatter(r["onset_years"], np.sqrt(r["_y"]), s=95,
               color=c, zorder=3, edgecolor="white", lw=1.6)
    ax.annotate(r["label"], (r["onset_years"], np.sqrt(r["_y"])),
                xytext=(9, -3), textcoords="offset points", fontsize=9.5,
                color=MUTED)
for v in (0, 1, 5, 25, 100):
    ax.axhline(np.sqrt(v), color=RULE, lw=0.7, zorder=1)
ax.set_yticks([np.sqrt(v) for v in (0, 1, 5, 25, 100)])
ax.set_yticklabels(["0%", "1%", "5%", "25%", "100%"])
ax.set_xlabel("onset — years from RFC publication to first sighting")
ax.set_ylabel("peak share of signed names reached")
ax.set_xlim(0, max(r["onset_years"] for r in pts) + 1.4)
ax.set_axisbelow(True)
import statistics as _st
_xs = [r["onset_years"] for r in pts]; _ys = [r["_y"] for r in pts]
_mx, _my = _st.mean(_xs), _st.mean(_ys)
_num = sum((a - _mx) * (b - _my) for a, b in zip(_xs, _ys))
_den = (sum((a - _mx) ** 2 for a in _xs) * sum((b - _my) ** 2 for b in _ys)) ** 0.5
_r = _num / _den if _den else 0.0
ax.text(0.60, 0.12, f"r = {_r:+.2f}   n = {len(pts)}", transform=ax.transAxes,
        fontsize=15, fontweight="bold", color=INK)
ax.text(0.60, 0.03, "not distinguishable from no relationship",
        transform=ax.transAxes, fontsize=10, color=MUTED)
save(fig, "onset_vs_spread")

# --------------------------------------------------------------------------- #
# 4. Displacement: how far each mechanism has fallen from its own peak.
# --------------------------------------------------------------------------- #
rows = []
for name in curves:
    v = [curves[name][m] for m in sorted(curves[name])]
    pk = max(v)
    if pk < 0.3:
        continue
    rows.append((name, pk, v[-1], (pk - v[-1]) / pk * 100))
rows.sort(key=lambda r: -r[3])

fig, ax = plt.subplots(figsize=(9.6, 4.2))
names = [r[0] for r in rows]
ypos = np.arange(len(rows))
ax.barh(ypos, [r[1] for r in rows], color=RULE, height=0.55, label="peak share")
ax.barh(ypos, [r[2] for r in rows], color=TEAL, height=0.55, label="share today")
for i, r in enumerate(rows):
    if r[3] > 5:
        ax.text(r[1] + 1.5, i, f"−{r[3]:.0f}%", va="center", fontsize=10,
                color=BRICK, fontweight="bold")
ax.set_yticks(ypos); ax.set_yticklabels(names)
ax.invert_yaxis()
ax.set_xlabel("% of signed delegations")
ax.legend(frameon=False, loc="lower right", fontsize=10)
ax.grid(axis="x", color=RULE, lw=0.7); ax.set_axisbelow(True)
save(fig, "displacement")

print(f"\ncharts in {OUT}")
