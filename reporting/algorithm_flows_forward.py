"""The OpenINTEL (forward) side of the algorithm-flow story.

What the forward data in this repository can and cannot do, stated once:

  out/server_run/timeline_monthly.parquet   monthly counts per (source, dimension,
      value) for seven TLDs, 2016-06 to 2023-12. This is what the figures below
      use.
  out/final/checkpoints                     3,127 partitions for .gov, .nu, .se,
      aggregated per (rfc_id, indicator_id, decision) -- RFC matches, not zones.
  .../exemplars                             per-domain rows, but ~75 sampled per
      partition. A sample for explainability, not a census.

None of the three follows an individual forward zone month to month, so the
rollover-path figure has no forward counterpart: "which zone went from RSASHA256
to ECDSA" needs a per-zone census the forward side does not carry here. Shares
and net flows do not, and those are drawn.

    python reporting/algorithm_flows_forward.py
"""
from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter, MaxNLocator

from algorithm_flows import (BARE, BASELINE, FAM_COLOR, FAMILY, GRID, INK, INK_2,
                             MUTED, ORDER, SURFACE, style)  # noqa: F401 (shared look)

TLDS = ["se", "nu", "ch", "gov", "ee", "li"]


def family_of(value: str) -> str:
    return FAMILY.get(str(value), "other")


def load(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    z = df[(df.basis == "zonefile") & (df.dimension == "algorithm_dnskey")].copy()
    z["family"] = z.value.map(family_of)
    return z[z.family.isin(ORDER)]


def to_year(m: str) -> float:
    return int(m[:4]) + (int(m[5:7]) - 1) / 12


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", type=Path,
                    default=Path("out/server_run/timeline_monthly.parquet"))
    ap.add_argument("--out", type=Path, default=Path("reporting/charts/flows"))
    ap.add_argument("--bare", action="store_true")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    z = load(args.timeline)
    tlds = [t for t in TLDS if t in set(z.source)]

    # ---- f6: family share of signed zones, per TLD ------------------------- #
    fig, axes = plt.subplots(2, 3, figsize=(12, 5.6), sharey=True)
    for ax, tld in zip(axes.ravel(), tlds):
        part = z[z.source == tld]
        wide = (part.pivot_table(index="month", columns="family", values="domains_peak",
                                 aggfunc="sum").fillna(0).sort_index())
        for fam in ORDER:
            if fam not in wide:
                wide[fam] = 0
        wide = wide[ORDER]
        total = wide.sum(axis=1).replace(0, pd.NA)
        share = wide.div(total, axis=0) * 100
        xs = [to_year(m) for m in share.index]
        # Lines on a shared zero, not a stack: in a stacked area only the bottom
        # band has a fixed baseline, and comparing .se's ECDSA with .ch's means
        # reading two bands off two different floors.
        for fam in ORDER:
            ser = share[fam].fillna(0)
            if ser.max() < 1:
                continue
            ax.plot(xs, ser, color=FAM_COLOR[fam], linewidth=2.2, zorder=3)
        ax.axhline(50, color=BASELINE, linewidth=0.9, linestyle=(0, (4, 3)), zorder=2)
        style(ax)
        ax.set_ylim(0, 100)
        ax.set_xlim(min(xs), max(xs))
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4, integer=True))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v)}"))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}%"))
        last = share.iloc[-1]
        lead = max(ORDER, key=lambda f: 0 if pd.isna(last[f]) else last[f])
        ax.set_title(f".{tld}   {int(total.iloc[-1]):,} signed zones   "
                     f"{lead} {last[lead]:.0f}%",
                     loc="left", fontsize=10.5, color=INK, fontweight="bold")
        ax.tick_params(labelsize=9)
    for ax in axes.ravel()[len(tlds):]:
        ax.set_visible(False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=FAM_COLOR[f]) for f in ORDER]
    if not args.bare:
        # Title above, legend under it: at the same height they overprint.
        fig.suptitle("OpenINTEL: what the signed zones of each TLD actually run",
                     x=0.005, y=1.075, ha="left", fontsize=13, fontweight="bold",
                     color=INK)
        fig.legend(handles, ORDER, frameon=False, ncol=4, loc="lower left",
                   bbox_to_anchor=(0.005, 0.985), fontsize=10, labelcolor=INK_2)
        fig.text(0.005, -0.04, textwrap.fill(
            "Share of each TLD's signed zones by algorithm family, from the monthly "
            "counts. The forward corpus runs 2016-06 to 2023-12 and the TLDs enter at "
            "different dates, so each panel starts where its data does.", 130),
            color=MUTED, fontsize=9.5, linespacing=1.5)
    fig.tight_layout(rect=[0, 0, 1, 0.93 if not args.bare else 1.0])
    p = args.out / "f6_forward_family_share.png"
    fig.savefig(p, bbox_inches="tight", pad_inches=0.3, facecolor=SURFACE)
    plt.close(fig)
    print(f"  wrote {p}")

    # ---- f7: how many zones publish each family, and how many publish two --- #
    #
    # NOT a stack. A zone mid-rollover publishes the old algorithm and the new one
    # at once, so it is counted under both families: .se's per-algorithm counts
    # sum to 974,799 against a total of 764,651 signed zones. Stacking them
    # therefore invents a population. Drawn as lines against the true total, the
    # overlap becomes the interesting quantity -- it is the rollovers in flight.
    pooled = (z.pivot_table(index="month", columns="family", values="domains_peak",
                            aggfunc="sum").fillna(0).sort_index())
    for fam in ORDER:
        if fam not in pooled:
            pooled[fam] = 0
    pooled = pooled[ORDER]
    total = (pd.read_parquet(args.timeline)
             .query("basis == 'zonefile' and dimension == 'algorithm_dnskey' "
                    "and value == '_total'")
             .groupby("month").domains_peak.sum().reindex(pooled.index).fillna(0))
    dual = (pooled.sum(axis=1) - total).clip(lower=0)
    xs = [to_year(m) for m in pooled.index]

    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.fill_between(xs, dual, color=MUTED, alpha=0.22, zorder=1,
                    label="zones publishing two families at once (rollover in flight)")
    ax.plot(xs, total, color=INK_2, linewidth=1.6, linestyle=(0, (5, 3)), zorder=3,
            label="signed zones in total")
    for fam in ORDER:
        if pooled[fam].max() < 500:
            continue
        ax.plot(xs, pooled[fam], color=FAM_COLOR[fam], linewidth=2.4, zorder=4,
                label=fam)
    peak = dual.idxmax()
    ax.annotate(f"{int(dual.max()):,} zones dual-signed, {peak}",
                (to_year(peak), dual.max()), xytext=(-186, 78),
                textcoords="offset points", fontsize=10, color=INK, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=INK_2, linewidth=1.2))
    style(ax)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=8, integer=True))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v)}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax.set_ylabel("zones", color=INK_2)
    ax.set_xlabel("year", color=INK_2)
    if not args.bare:
        ax.legend(frameon=False, fontsize=9.5, labelcolor=INK_2, ncol=3,
                  loc="lower left", bbox_to_anchor=(0, 1.02))
        ax.set_title("OpenINTEL: the ECDSA migration, and the rollovers still in flight",
                     loc="left", color=INK, fontweight="bold", pad=52)
        ax.text(0, -0.30, textwrap.fill(
            "Zones publishing a DNSKEY of each family, pooled across the seven forward "
            "TLDs, against the true count of signed zones. The lines sum to more than the "
            "total because a zone rolling over publishes both algorithms; that gap, "
            "shaded, is the population mid-rollover. ECDSA overtakes RSA/SHA-2 in 2019 "
            "and the old keys are dropped in December of that year.", 104),
            transform=ax.transAxes, color=MUTED, fontsize=9.5, va="top", linespacing=1.5)
    p_out = args.out / "f7_forward_net_growth.png"
    fig.savefig(p_out, bbox_inches="tight", pad_inches=0.3, facecolor=SURFACE)
    plt.close(fig)
    print(f"  wrote {p_out}")

    last = pooled.iloc[-1]
    summary = {
        "corpus": {"months": [str(pooled.index.min()), str(pooled.index.max())],
                   "sources": sorted(z.source.unique()),
                   "entry_month": {s_: str(z[z.source == s_].month.min())
                                   for s_ in sorted(z.source.unique())}},
        "signed_zones_last_month": {f: int(last[f]) for f in ORDER},
        "share_of_signed_zones_last_month_pct": {
            f: round(float(last[f] / float(total.iloc[-1]) * 100), 1) for f in ORDER},
        "dual_signing_peak": {"month": str(dual.idxmax()), "zones": int(dual.max())},
        "overlap_warning": ("per-algorithm zone counts overlap: a zone mid-rollover "
                            "publishes two families and is counted under both, so they "
                            "must never be stacked"),
        "per_tld_last_month_pct": {},
        "not_available_forward": ("per-zone rollover paths: neither the monthly "
                                  "aggregates, the RFC checkpoints nor the sampled "
                                  "exemplars follow one zone across months"),
    }
    # Per TLD, at that TLD's own last month: the pooled share is a different
    # number and labelling one with the other is how the deck got .ee wrong.
    for tld in tlds:
        part = z[z.source == tld]
        last_m = part.month.max()
        w = (part[part.month == last_m].groupby("family").domains_peak.sum())
        tot_t = (pd.read_parquet(args.timeline)
                 .query("basis == 'zonefile' and dimension == 'algorithm_dnskey' "
                        f"and value == '_total' and source == '{tld}' "
                        f"and month == '{last_m}'").domains_peak.max())
        summary["per_tld_last_month_pct"][tld] = {
            "month": str(last_m), "signed_zones": int(tot_t),
            **{f: round(float(w.get(f, 0)) / float(tot_t) * 100, 1) for f in ORDER}}

    out_json = Path("out/analysis/algorithm_flows_forward.json")
    out_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"  wrote {out_json}")
    print(f"\n  forward signed zones at {pooled.index.max()}: " +
          ", ".join(f"{f} {int(last[f]):,}" for f in ORDER))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
