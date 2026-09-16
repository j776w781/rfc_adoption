"""One simple chart: adoption rate in months when a CVE was patched, when an
RFC was published, and in all other months. Dots are months, bar is the
median. Reads out/analysis/cve_vs_rfc_rates.json and the CSV.
Writes reporting/charts/cve_vs_rfc_rates_simple.png.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SURFACE, INK, INK_2, MUTED, BASELINE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#c3c2b7", "#e1e0d9"
S3, CRITICAL = "#1baf7a", "#d03b3b"
plt.rcParams.update({"font.family": ["DejaVu Sans", "sans-serif"], "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
                     "savefig.facecolor": SURFACE, "text.color": INK, "axes.labelcolor": INK_2, "xtick.color": INK_2,
                     "ytick.color": MUTED, "axes.edgecolor": BASELINE, "figure.dpi": 120})
rng = np.random.default_rng(3)

doc = json.loads(Path("out/analysis/cve_vs_rfc_rates.json").read_text("utf-8"))
rows = pd.read_csv("out/analysis/dns_cve_vs_rfc_rates.csv")
TITLE = {"reverse signed share (strict panel)": "Reverse DNS (AFRINIC+ARIN panel), 2011-2026",
         "forward signed share (7 TLDs, zone-weighted)": "OpenINTEL zone files (7 TLDs), 2016-2023"}

fig, axes = plt.subplots(1, 2, figsize=(13, 5.6))
for ax, (label, res) in zip(axes, doc["overall"].items()):
    r = rows[(rows.series == label) & (rows.measure == "raw")].drop_duplicates(["kind", "month"])
    cve = r[r.kind == "cve_patch"].rate_window_pp_per_month.values
    rfc = r[r.kind == "rfc_published"].rate_window_pp_per_month.values
    ev_months = set(r.month)
    allm = np.array([v for m, v in zip(res["raw"]["baseline_months"], res["raw"]["baseline_values"]) if m not in ev_months])
    groups = [("CVE patched", cve, CRITICAL), ("RFC published", rfc, S3), ("all other months", allm, MUTED)]
    for i, (name, vals, col) in enumerate(groups):
        x = i + rng.uniform(-0.18, 0.18, len(vals))
        ax.scatter(x, vals, s=34, color=col, alpha=0.75, edgecolor=SURFACE, linewidth=0.6, zorder=3)
        med = float(np.median(vals))
        ax.plot([i - 0.3, i + 0.3], [med, med], color=INK, linewidth=2.6, zorder=4)
        ax.annotate(f"median {med:+.3f}" if abs(med) < 0.05 else f"median {med:+.2f}", (i, med), (0, 7),
                    textcoords="offset points", fontsize=9, color=INK, ha="center", va="bottom", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.15", fc=SURFACE, ec="none", alpha=0.85), zorder=5)
    ax.set_xticks(range(3))
    ax.set_xticklabels([f"{n}\n({len(v)} months)" for n, v, _ in groups], fontsize=10.5)
    ax.axhline(0, color=BASELINE, linewidth=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.8); ax.set_axisbelow(True); ax.tick_params(length=0)
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylabel("adoption rate (pp of signed share per month)", fontsize=10)
    ax.set_title(TITLE[label], loc="left", fontsize=12, fontweight="bold", pad=8)
fig.suptitle("DNSSEC adoption moves at the same speed whether a CVE was just patched, an RFC was just published, or neither",
             x=0.01, ha="left", fontsize=12.5, fontweight="bold", y=0.985)
fig.text(0.01, 0.915, "Each dot is one month. Rate = change of the signed share over that month and the three after it. "
                      "Black bar = median of the group.", fontsize=9.5, color=INK_2)
fig.subplots_adjust(left=0.07, right=0.985, top=0.82, bottom=0.14, wspace=0.28)
Path("reporting/charts").mkdir(exist_ok=True)
fig.savefig("reporting/charts/cve_vs_rfc_rates_simple.png", dpi=150)
print("ok")
