"""Two charts that had no working producer, rebuilt on the canonical timeline.

Both were orphans. `reverse_algorithm_mix.png` was generated from the reverse
RFC-match checkpoints, but none of the 1,174 partitions in this checkout carries
a `.status.json` completion marker, so `merge_checkpoints` refuses to count them
-- correctly, since "this day had no matches" and "this day was not counted" are
different claims -- and the chart came out empty. Its label also disagreed with
its denominator: it divided matched records by every scanned record while calling
the result a share of DS records. `nsec3_vs_ecdsa.png` was dropped from
make_charts.py when growth_vs_baseline.png replaced it, and measured shares of
.gov *records* rather than of zones.

Both are rebuilt here from out/server_run/timeline_monthly.parquet and
out/panel_run/timeline_monthly.parquet, the sources every verified chart in this
project uses, with the denominators the project settled on:

    reverse share = algorithm_ds <value> / algorithm_ds "_total"   (signed delegations)
    forward share = algorithm_dnskey <value> / algorithm_dnskey "_total"  (signed zones)
    forward NSEC3 = rr_type NSEC3PARAM / algorithm_dnskey "_total"

Per-algorithm counts overlap while a zone is dual-signed, so the lines are never
stacked and never summed.

    python reporting/algorithm_mix.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter, MaxNLocator

SURFACE, INK, INK_2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
S1, S2, S3, YELLOW, PURPLE = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#8a5cd6"
PANEL = "_pooled-afrinic-arin"
plt.rcParams.update({
    "font.family": ["DejaVu Sans", "sans-serif"], "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "text.color": INK, "axes.labelcolor": INK_2, "xtick.color": INK_2,
    "ytick.color": INK_2, "axes.edgecolor": BASELINE, "figure.dpi": 120, "font.size": 11})

FAMILIES = [("RSA/SHA-1", ["5", "7"], S2), ("RSA/SHA-2", ["8", "10"], S1),
            ("ECDSA", ["13", "14"], S3), ("EdDSA", ["15", "16"], PURPLE),
            ("GOST", ["12"], YELLOW)]


def yr(m):
    return int(m[:4]) + (int(m[5:7]) - 1) / 12.0


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=10))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v)}"))


def share(df, dim, values, den_dim=None, den_value="_total"):
    """A share whose denominator is stated, not assumed."""
    den = df[(df.dimension == (den_dim or dim)) & (df.value == den_value)].groupby("month").domains_peak.sum()
    num = df[(df.dimension == dim) & (df.value.isin(values))].groupby("month").domains_peak.sum()
    return (num.reindex(den.index, fill_value=0) / den.where(den > 0) * 100).dropna().sort_index()


def label_end(ax, s, text, color):
    if len(s):
        ax.annotate(text, (yr(s.index[-1]), s.iloc[-1]), (6, 0), textcoords="offset points",
                    va="center", fontsize=9.5, color=color, fontweight="bold")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reporting/charts")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    srv = pd.read_parquet("out/server_run/timeline_monthly.parquet")
    pan = pd.read_parquet("out/panel_run/timeline_monthly.parquet")
    rev = pan[(pan.basis == "reverse") & (pan.source == PANEL)]
    fwd = srv[srv.basis == "zonefile"]

    # ---------------------------------------------------- 1. algorithm mix --
    fig, ax = plt.subplots(figsize=(12.5, 5.6))
    drawn = []
    for name, vals, colour in FAMILIES:
        s = share(rev, "algorithm_ds", vals)
        if s.empty or s.max() < 0.05:
            drawn.append(f"{name} (never present)")
            continue
        ax.plot([yr(m) for m in s.index], s.values, color=colour, linewidth=2.2, zorder=3)
        label_end(ax, s, name, colour)
    style(ax)
    ax.set_ylim(0, 100)
    ax.set_ylabel("% of signed delegations", fontsize=10.5)
    ax.set_xlim(min(yr(m) for m in rev.month.unique()) - 0.3, 2027.2)
    fig.suptitle("What signed reverse delegations are signed with", x=0.012, ha="left",
                 fontsize=13, fontweight="bold", y=0.975)
    fig.text(0.012, 0.915, "Strict AFRINIC+ARIN panel, share of delegations that carry a DS record. A dual-signed "
                           "delegation counts in two families, so the lines are not stacked and do not sum to 100%.",
             fontsize=9, color=INK_2)
    if drawn:
        fig.text(0.012, 0.878, "; ".join(drawn) + " on this panel.", fontsize=9, color=INK_2)
    fig.subplots_adjust(left=0.07, right=0.93, top=0.845, bottom=0.09)
    fig.savefig(out / "reverse_algorithm_mix.png", dpi=150)
    plt.close(fig)

    # ------------------------------------------------- 2. NSEC3 vs ECDSA ----
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4))
    f_n3 = share(fwd, "rr_type", ["NSEC3PARAM"], den_dim="algorithm_dnskey")
    f_ec = share(fwd, "algorithm_dnskey", ["13", "14"])
    r_n3 = share(rev, "algorithm_ds", ["7"])
    r_ec = share(rev, "algorithm_ds", ["13", "14"])
    for ax, (n3, ec, title, unit) in zip(axes, [
            (f_n3, f_ec, "OpenINTEL zone files (7 TLDs)", "% of signed zones"),
            (r_n3, r_ec, "Reverse DNS (AFRINIC+ARIN panel)", "% of signed delegations")]):
        ax.plot([yr(m) for m in n3.index], n3.values, color=S2, linewidth=2.4, zorder=3)
        ax.plot([yr(m) for m in ec.index], ec.values, color=S3, linewidth=2.4, zorder=3)
        label_end(ax, n3, "NSEC3", S2); label_end(ax, ec, "ECDSA", S3)
        style(ax)
        ax.set_ylim(0, 100)
        ax.set_ylabel(unit, fontsize=10.5)
        ax.set_title(title, loc="left", fontsize=12, fontweight="bold", pad=8)
        lo = min([yr(m) for m in n3.index] + [yr(m) for m in ec.index])
        hi = max([yr(m) for m in n3.index] + [yr(m) for m in ec.index])
        ax.set_xlim(lo - 0.2, hi + 1.1)
    fig.suptitle("NSEC3 and ECDSA move independently: one is a denial mechanism, the other a signing algorithm",
                 x=0.012, ha="left", fontsize=13, fontweight="bold", y=0.98)
    fig.text(0.012, 0.915, "Forward NSEC3 is zones publishing NSEC3PARAM over signed zones. Reverse NSEC3 is visible only through "
                           "algorithm 7 (RSASHA1-NSEC3-SHA1), so it undercounts NSEC3 used with algorithms 8 or 13.",
             fontsize=9, color=INK_2)
    fig.subplots_adjust(left=0.055, right=0.985, top=0.82, bottom=0.09, wspace=0.22)
    fig.savefig(out / "nsec3_vs_ecdsa.png", dpi=150)
    plt.close(fig)
    print("reverse_algorithm_mix.png, nsec3_vs_ecdsa.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
