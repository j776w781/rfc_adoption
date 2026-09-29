"""Three plain histograms of the adoption rate (reverse DNS strict panel):
months when a DNSSEC CVE was patched, months when a DNSSEC RFC was published,
and the two together. Same bins on every chart.
Writes reporting/charts/rate_hist_cve.png, rate_hist_rfc.png, rate_hist_both.png.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE, INK, INK_2, MUTED, BASELINE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#c3c2b7", "#e1e0d9"
S3, CRITICAL = "#1baf7a", "#d03b3b"
plt.rcParams.update({"font.family": ["DejaVu Sans", "sans-serif"], "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
                     "savefig.facecolor": SURFACE, "text.color": INK, "axes.labelcolor": INK_2, "xtick.color": INK_2,
                     "ytick.color": INK_2, "axes.edgecolor": BASELINE, "figure.dpi": 120, "font.size": 11})

rows = pd.read_csv("out/analysis/dns_cve_vs_rfc_rates.csv")
r = rows[rows.series.str.startswith("reverse") & (rows.measure == "raw")].drop_duplicates(["kind", "month"])
cve = r[r.kind == "cve_patch"].rate_window_pp_per_month.values * 1000   # thousandths of a point, for readable ticks
rfc = r[r.kind == "rfc_published"].rate_window_pp_per_month.values * 1000
bins = np.arange(-2, 22, 2)
XL = "adoption rate in the 4 months after the event\n(change in the share of signed reverse delegations, thousandths of a percentage point per month)"


def hist(vals, color, title, out, second=None, second_color=None, second_label=None, label=None):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(vals, bins=bins, color=color, edgecolor=SURFACE, linewidth=1.2, alpha=0.9 if second is None else 0.6, label=label)
    if second is not None:
        ax.hist(second, bins=bins, color=second_color, edgecolor=SURFACE, linewidth=1.2, alpha=0.6, label=second_label)
        ax.legend(frameon=False, loc="upper right")
    med = float(np.median(vals))
    ax.axvline(med, color=INK, linewidth=2)
    ax.annotate(f"median {med:.1f}", (med, ax.get_ylim()[1] * 0.95), (6, 0), textcoords="offset points", fontsize=10, va="top")
    if second is not None:
        m2 = float(np.median(second))
        ax.axvline(m2, color=INK, linewidth=2, linestyle=(0, (4, 3)))
        ax.annotate(f"median {m2:.1f}", (m2, ax.get_ylim()[1] * 0.85), (6, 0), textcoords="offset points", fontsize=10, va="top")
    ax.set_xlabel(XL, fontsize=10)
    ax.set_ylabel("number of months")
    ax.set_xticks(bins[::2])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID); ax.set_axisbelow(True); ax.tick_params(length=0)
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", pad=10)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.88, bottom=0.2)
    fig.savefig(out, dpi=150)
    plt.close(fig)


hist(cve, CRITICAL, f"Months when a DNSSEC CVE was patched  ({len(cve)} months)",
     "reporting/charts/rate_hist_cve.png")
hist(rfc, S3, f"Months when a DNSSEC RFC was published  ({len(rfc)} months)",
     "reporting/charts/rate_hist_rfc.png")
hist(cve, CRITICAL, "Both together", "reporting/charts/rate_hist_both.png",
     second=rfc, second_color=S3, second_label=f"RFC published ({len(rfc)} months)", label=f"CVE patched ({len(cve)} months)")
print("ok", np.median(cve), np.median(rfc))
