"""Figure: adoption rate around CVE patches vs around RFC publications.

Two rows (reverse strict panel; forward seven TLDs), three columns:
  1. the rate series over time with the event months marked
  2. the distribution of the windowed rate (event month + 3) at CVE-patch
     months, at RFC-publication months, and at all months -- as ECDFs
  3. the same on the detrended rate

Reads out/analysis/cve_vs_rfc_rates.json. Writes reporting/charts/cve_vs_rfc_rates.png.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter, MaxNLocator

SURFACE, INK, INK_2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
S1, S2, S3, CRITICAL = "#2a78d6", "#eb6834", "#1baf7a", "#d03b3b"
plt.rcParams.update({
    "font.family": ["DejaVu Sans", "sans-serif"], "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "text.color": INK, "axes.labelcolor": INK_2, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.edgecolor": BASELINE, "axes.linewidth": 0.8, "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5, "figure.dpi": 120})
COL = {"cve_patch": CRITICAL, "rfc_published": S3, "all": MUTED}
NAME = {"cve_patch": "CVE patched", "rfc_published": "RFC published", "all": "all months"}


def yr(m):
    return int(m[:4]) + (int(m[5:7]) - 1) / 12.0


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def ecdf(ax, vals, color, label, lw=2.0, z=3):
    v = np.sort(np.asarray(vals, dtype=float))
    if not len(v):
        return
    y = np.arange(1, len(v) + 1) / len(v)
    ax.step(v, y, where="post", color=color, linewidth=lw, label=f"{label} (n={len(v)})", zorder=z)
    med = float(np.median(v))
    ax.plot(med, 0.5, marker="o", ms=7, color=color, mec=SURFACE, mew=1.2, zorder=z + 1, ls="none")


def panel_dists(ax, block, rows, key, title):
    bl = block["baseline_values"]
    ecdf(ax, bl, COL["all"], NAME["all"], lw=1.6, z=2)
    for kind in ("rfc_published", "cve_patch"):
        vals = list({r["month"]: r["rate_window_pp_per_month"] for r in rows if r["kind"] == kind and r["measure"] == key}.values())
        ecdf(ax, vals, COL[kind], NAME[kind] + " months")
    ax.axvline(0, color=BASELINE, linewidth=0.8)
    ax.set_ylim(0, 1.02)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.2f}"))
    style(ax)
    ax.set_title(title, loc="left", fontsize=10.5, color=INK_2, pad=6)
    p = block["p_cve_vs_rfc"]; pc = block["p_cve_vs_all_year_matched"]; pr = block["p_rfc_vs_all_year_matched"]
    fmt = lambda v: "-" if v is None else f"{v:.2f}"
    ax.text(0.02, 0.97, f'medians  CVE {block["cve_patches"]["median"]:+.3f}   RFC {block["rfc_publications"]["median"]:+.3f}   '
                        f'all {block["all_months"]["median"]:+.3f}\n'
                        f'p  CVE~RFC {fmt(p)}   CVE~all {fmt(pc)}   RFC~all {fmt(pr)}  (year-matched)',
            transform=ax.transAxes, fontsize=7.8, color=INK_2, va="top", family="DejaVu Sans Mono")
    ax.legend(loc="lower right", fontsize=8, frameon=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reporting/charts/cve_vs_rfc_rates.png")
    ap.add_argument("--bare", action="store_true")
    a = ap.parse_args()
    doc = json.loads(Path("out/analysis/cve_vs_rfc_rates.json").read_text("utf-8"))
    import pandas as pd
    rows = pd.read_csv("out/analysis/dns_cve_vs_rfc_rates.csv").to_dict("records")
    fig, axes = plt.subplots(2, 3, figsize=(17, 8.6), gridspec_kw={"width_ratios": [1.5, 1, 1], "hspace": 0.45, "wspace": 0.22})
    for i, (label, res) in enumerate(doc["overall"].items()):
        rrows = [r for r in rows if r["series"] == label]
        raw = res["raw"]
        ax = axes[i][0]
        x = [yr(m) for m in raw["baseline_months"]]
        ax.plot(x, raw["baseline_values"], color=INK, linewidth=1.3)
        ax.axhline(0, color=BASELINE, linewidth=0.8)
        ymax = max(abs(v) for v in raw["baseline_values"]) * 1.15
        for kind, dy in (("rfc_published", 0.93), ("cve_patch", 0.86)):
            ms = sorted({r["month"] for r in rrows if r["kind"] == kind})
            ax.plot([yr(m) for m in ms], [ymax * dy] * len(ms), marker="|", ms=11, mew=1.6, ls="none", color=COL[kind],
                    label=f"{NAME[kind]} (n={len(ms)})")
        ax.set_ylim(-ymax, ymax * 1.02)
        ax.set_xlim(x[0] - 0.3, x[-1] + 0.3)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=9))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v)}"))
        style(ax)
        ax.set_ylabel("pp per month (4-month mean)", fontsize=9.5)
        ax.set_title(label + "  --  rate over time, events marked", loc="left", fontsize=10.5, color=INK_2, pad=6)
        ax.legend(loc="lower left", fontsize=8, frameon=False, ncol=2)
        panel_dists(axes[i][1], raw, rrows, "raw", "distribution of the rate at event months (ECDF)")
        panel_dists(axes[i][2], res["detrended"], rrows, "detrended", "same, detrended (minus 25-month rolling median)")
        axes[i][1].set_xlabel("pp per month", fontsize=9.5); axes[i][2].set_xlabel("pp per month, residual", fontsize=9.5)
    if not a.bare:
        fig.suptitle("Adoption rate when a DNSSEC CVE was patched vs when a DNSSEC RFC was published",
                     x=0.01, ha="left", fontsize=14, fontweight="bold", y=0.995)
        fig.text(0.01, 0.962, f'Rate = month-on-month change of the signed share, averaged over the event month and the 3 months after. '
                              f'{len(doc["events"]["cve_patches"])} DNSSEC CVEs with a dated fix, counted once per fix month; '
                              f'{len(doc["events"]["rfc_publications"])} DNSSEC RFCs, those inside each series\' span.',
                 fontsize=9, color=INK_2)
        fig.text(0.01, 0.94, 'Dots on the ECDFs are medians. p-values: permutation over medians, 5,000 draws; "year-matched" draws '
                             'random months from the same years as the events, because the CVE fixes cluster in 2022-2026.',
                 fontsize=9, color=INK_2)
    fig.subplots_adjust(left=0.05, right=0.985, top=0.88 if not a.bare else 0.95, bottom=0.08)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=150)
    print(a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
