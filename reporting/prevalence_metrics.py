"""One figure per DNSSEC prevalence metric, from out/analysis/prevalence_metrics.csv.

Run ``python scripts/prevalence_metrics.py`` first. Writes to
``reporting/charts/prevalence/``:

    ds_share.png       reverse (five RIRs thin, strict panel bold) | forward TLDs
    dnskey_share.png   forward TLDs only (not observable in the reverse corpus)
    rrsig_share.png    forward TLDs: zone-level proxy (RRSIG over DNSKEY / NS zones)
                       and the name-level share (names with RRSIG / all names)
    secspider.png      SecSpider tracked-set shares from Wayback captures (if present)

fed.us (1-2 zones) is left off the charts; it is in the CSV.
Every subtitle states the denominator. No stacked areas.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "out/analysis/prevalence_metrics.csv"
OUT = ROOT / "reporting/charts/prevalence"

BLUE, ORANGE, GREEN, YELLOW, PURPLE, ROSE = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#8a5cd6", "#c2416d"
INK, GRID, SURFACE = "#0b0b0b", "#e1e0d9", "#fcfcfb"
MUTED = "#6b6a66"

REVERSE_COLOURS = {"afrinic": BLUE, "apnic": ORANGE, "arin": GREEN, "lacnic": YELLOW, "ripe": PURPLE}
# six categorical hues in fixed order; validated (dataviz validate_palette.js, light surface)
FORWARD_COLOURS = {"se": BLUE, "nu": ORANGE, "ch": GREEN, "li": YELLOW, "ee": PURPLE, "gov": ROSE}
FORWARD_ORDER = ["se", "nu", "ch", "li", "ee", "gov"]
PANEL = "_pooled-afrinic-arin"

plt.rcParams.update({
    "font.family": ["DejaVu Sans", "sans-serif"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": GRID, "axes.linewidth": 0.8, "xtick.labelsize": 10, "ytick.labelsize": 10,
})


def style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.tick_params(length=0)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def series(df, corpus, source, metric, break_after_months=None):
    """x, y for one line. With ``break_after_months`` a gap longer than that many
    months gets a NaN so the line breaks instead of bridging months nobody measured."""
    s = df[(df.corpus == corpus) & (df.source == source) & (df.metric == metric)].sort_values("month")
    x, y = pd.to_datetime(s.month + "-01"), s.pct.astype(float)
    if break_after_months and len(x) > 1:
        gap = x.diff().dt.days > break_after_months * 31
        xs, ys = [], []
        for xi, yi, g in zip(x, y, gap):
            if g:
                xs.append(xi - pd.Timedelta(days=1)); ys.append(float("nan"))
            xs.append(xi); ys.append(yi)
        return pd.Series(xs), pd.Series(ys)
    return x, y


def line(ax, df, corpus, source, metric, colour, bold=False, label=None, ls="-"):
    x, y = series(df, corpus, source, metric)
    if len(x) == 0:
        return
    ax.plot(x, y, color=colour, linewidth=2.6 if bold else 1.4, linestyle=ls,
            label=label or source, zorder=3 if bold else 2)


def titled(fig, title, subtitle):
    fig.suptitle(title, x=0.01, ha="left", fontsize=14, fontweight="bold", y=0.995)
    fig.text(0.01, 0.955, subtitle, ha="left", va="top", fontsize=9.5, color=MUTED)


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=160, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    print(f"  wrote {OUT / name}")


def fig_ds(df):
    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 5.2))
    fig.subplots_adjust(top=0.82, wspace=0.22)
    for src, c in REVERSE_COLOURS.items():
        line(a, df, "reverse", src, "ds_share", c)
    line(a, df, "reverse_panel", PANEL, "ds_share", INK, bold=True, label="strict panel (afrinic+arin)")
    a.set_title("Reverse: in-addr.arpa delegations with a DS", loc="left", fontsize=11)
    a.set_ylabel("% of delegations")
    style(a); a.legend(frameon=False, fontsize=9)
    for src in FORWARD_ORDER:
        line(b, df, "forward", src, "ds_share", FORWARD_COLOURS[src], label=f".{src}")
    b.set_title("Forward: delegated zones with a DS", loc="left", fontsize=11)
    b.set_ylabel("% of delegated zones")
    style(b); b.legend(frameon=False, fontsize=9, ncol=2)
    titled(fig, "Share of domains with at least one DS record",
           "Reverse: delegations with a DS / all delegations in the RIR zone file (one snapshot per month). "
           "Forward: names with a DS / names with an NS RRset (delegated zones), mean daily share per month, OpenINTEL.")
    save(fig, "ds_share.png")


def fig_dnskey(df):
    fig, ax = plt.subplots(figsize=(9, 5.2))
    fig.subplots_adjust(top=0.82)
    for src in FORWARD_ORDER:
        line(ax, df, "forward", src, "dnskey_share", FORWARD_COLOURS[src], label=f".{src}")
    ax.set_ylabel("% of delegated zones")
    style(ax); ax.legend(frameon=False, fontsize=9, ncol=2)
    titled(fig, "Share of zones serving at least one DNSKEY (forward TLDs)",
           "Names answering with a DNSKEY / names with an NS RRset (delegated zones), mean daily share per month, OpenINTEL. "
           "Not observable in the reverse corpus: RIR zone files carry only the parent-side DS.")
    save(fig, "dnskey_share.png")


def fig_rrsig(df):
    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 5.2))
    fig.subplots_adjust(top=0.82, wspace=0.22)
    for src in FORWARD_ORDER:
        line(a, df, "forward", src, "rrsig_zone_share", FORWARD_COLOURS[src], label=f".{src}")
    a.set_title("Zone level: zones whose DNSKEY RRset carries an RRSIG", loc="left", fontsize=11)
    a.set_ylabel("% of delegated zones")
    style(a); a.legend(frameon=False, fontsize=9, ncol=2)
    for src in FORWARD_ORDER:
        line(b, df, "forward", src, "rrsig_names_share", FORWARD_COLOURS[src], label=f".{src}")
    b.set_title("Name level: measured names with any RRSIG", loc="left", fontsize=11)
    b.set_ylabel("% of measured names")
    style(b); b.legend(frameon=False, fontsize=9, ncol=2)
    titled(fig, "Share of domains with at least one RRSIG (forward TLDs)",
           "Left: names with an RRSIG covering DNSKEY (a signed apex) / names with an NS RRset (delegated zones). "
           "Right: names with any RRSIG / all measured names -- a name count, not a zone count. "
           "Not observable in the reverse corpus.")
    save(fig, "rrsig_share.png")


def fig_secspider(df):
    s = df[df.corpus == "secspider"]
    if s.empty:
        print("  secspider: no rows, chart skipped")
        return
    fig, ax = plt.subplots(figsize=(9, 5.2))
    fig.subplots_adjust(top=0.82)
    # the series is host-agnostic per month; pool the three hosts into one line each
    pooled = s.assign(source="secspider")
    for metric, c, lab in [("dnssec_enabled_share", BLUE, "DNSSEC enabled zones"),
                           ("dnssec_verified_share", GREEN, "DNSSEC verified zones"),
                           ("production_share", ORANGE, "production DNSSEC zones")]:
        x, y = series(pooled, "secspider", "secspider", metric, break_after_months=3)
        if len(x) == 0:
            continue
        ax.plot(x, y, color=c, linewidth=1.6, marker="o", markersize=3, label=lab)
    ax.set_ylabel("% of zones SecSpider tracks")
    ax.set_ylim(0, 100)
    style(ax); ax.legend(frameon=False, fontsize=9, loc="lower right")
    titled(fig, "SecSpider: DNSSEC-enabled share of its tracked zone set",
           "Counts from SecSpider's Monitoring Summary in Wayback Machine captures (one per month where captured; "
           "lines break at gaps over 3 months).\n"
           "Denominator = zones SecSpider tracks (crawled, submitted, NSEC-walked): a DNSSEC-seeking set, not the DNS.")
    save(fig, "secspider.png")


def main() -> int:
    df = pd.read_csv(CSV, dtype={"month": str})
    fig_ds(df)
    fig_dnskey(df)
    fig_rrsig(df)
    fig_secspider(df)
    return 0


if __name__ == "__main__":
    sys.exit(main())
