"""What reverse-DNS zones are switching to, and away from, year by year.

The earlier charts counted "delegations changing", which hides the only
interesting part: what they changed *to*. This works the per-delegation ledger
into flows between algorithm families and draws the trend.

Families rather than raw codepoints, because the story is generational:

    RSA/SHA-1   algorithms 5 and 7     the original, now deprecated
    RSA/SHA-2   algorithms 8 and 10    the long-lived middle
    ECDSA       algorithms 13 and 14   the current default nearly everywhere
    EdDSA       algorithms 15 and 16   standardised 2017, still nowhere

Reverse corpus only: the forward per-day records are not in this repository.

    python reporting/algorithm_flows.py [--out reporting/charts/flows]
"""
from __future__ import annotations

import argparse
import json
import textwrap
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

SURFACE, INK, INK_2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
#: Validated reference palette, fixed order. Four families, so slots 1-4; aqua
#: sits between orange and yellow in the stack, keeping that weak pair apart.
FAM_COLOR = {"RSA/SHA-1": "#2a78d6", "RSA/SHA-2": "#eb6834",
             "ECDSA": "#1baf7a", "EdDSA": "#eda100"}
CRITICAL = "#d03b3b"

FAMILY = {"3": "other", "6": "other", "12": "other",
          "5": "RSA/SHA-1", "7": "RSA/SHA-1",
          "8": "RSA/SHA-2", "10": "RSA/SHA-2",
          "13": "ECDSA", "14": "ECDSA",
          "15": "EdDSA", "16": "EdDSA"}
ORDER = ["RSA/SHA-1", "RSA/SHA-2", "ECDSA", "EdDSA"]
ALG_NAME = {"5": "RSASHA1", "7": "RSASHA1-NSEC3", "8": "RSASHA256", "10": "RSASHA512",
            "13": "ECDSA P-256", "14": "ECDSA P-384", "15": "Ed25519", "16": "Ed448",
            "3": "DSA", "12": "ECC-GOST", "6": "DSA-NSEC3"}

plt.rcParams.update({
    "font.family": ["DejaVu Sans", "sans-serif"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "text.color": INK, "axes.labelcolor": INK_2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": BASELINE,
    "axes.linewidth": 0.8, "xtick.labelsize": 11, "ytick.labelsize": 11,
    "figure.dpi": 120,
})


def style(ax, axis="y"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis=axis, color=GRID, linewidth=0.8)
    ax.tick_params(length=0)


#: In --bare mode the figure carries no title, deck line or footnote: the deck
#: supplies those, and baking them in as well prints everything twice.
BARE = False


def headline(ax, text, sub=None, width=88):
    """Title with an optional deck line wrapped to `width`.

    The pad has to grow with the wrapped line count or a two-line deck prints
    over the title.
    """
    if BARE:
        return
    lines = textwrap.wrap(sub, width) if sub else []
    ax.set_title(text, loc="left", color=INK, fontweight="bold",
                 pad=14 + 15 * len(lines))
    if lines:
        ax.text(0, 1.03, "\n".join(lines), transform=ax.transAxes, color=INK_2,
                fontsize=10, va="bottom", linespacing=1.4)


def year_ticks(ax):
    """Integer years. A float locator prints 2012.5, which is not a year."""
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=8, integer=True))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v)}"))


def note(ax, text, width=104):
    """Footnote under the axis, hard-wrapped.

    Left unwrapped, a long caption sets the figure width under
    bbox_inches="tight" and the chart ends up three times wider than it is tall.
    """
    if BARE:
        return
    ax.text(0, -0.26, textwrap.fill(text, width), transform=ax.transAxes,
            color=MUTED, fontsize=9.5, va="top", ha="left", linespacing=1.5)


def families(alg_set: str) -> list[str]:
    return sorted({FAMILY.get(a, "other") for a in alg_set.split(",") if a})


def save(fig, out: Path, name: str):
    p = out / f"{name}.png"
    fig.savefig(p, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    print(f"  wrote {p}")
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", type=Path,
                    default=Path("out/analysis/delegation_changes.parquet"))
    ap.add_argument("--out", type=Path, default=Path("reporting/charts/flows"))
    ap.add_argument("--bare", action="store_true",
                    help="omit titles and footnotes; for embedding in slides")
    args = ap.parse_args()
    global BARE
    BARE = args.bare
    args.out.mkdir(parents=True, exist_ok=True)

    led = pd.read_parquet(args.ledger)
    led["year"] = led.month.str[:4].astype(int)
    years = list(range(led.year.min(), led.year.max() + 1))

    # ---- 1. what a zone signing for the first time chose -------------------- #
    sign = led[led.kind == "sign"].copy()
    sign["family"] = sign.to_alg.map(lambda s: families(s)[0] if families(s) else "other")
    counts = (sign.pivot_table(index="year", columns="family", values="delegation",
                               aggfunc="nunique")
              .reindex(years, fill_value=0).fillna(0))
    for fam in ORDER:
        if fam not in counts:
            counts[fam] = 0
    counts = counts[ORDER]

    fig, ax = plt.subplots(figsize=(10.5, 4.4))
    # Lines, not a stack. In a stacked area only the bottom band has a fixed
    # baseline; every band above it is read against a moving floor, which is
    # exactly the comparison these charts exist to make.
    for fam in ORDER:
        if counts[fam].max() < 5:
            continue
        ax.plot(counts.index, counts[fam], color=FAM_COLOR[fam], linewidth=2.6,
                zorder=3)
        # Right-hand labels, as in the share figure: at each line's own peak the
        # RSA/SHA-1 label lands on top of the rising ECDSA line.
        last = counts.index[-1]
        ax.annotate(f"{fam}  {int(counts[fam][last]):,}", (last, counts[fam][last]),
                    xytext=(9, 0), textcoords="offset points", va="center",
                    fontsize=10.5, color=INK, fontweight="bold")
    style(ax)
    year_ticks(ax)
    ax.set_xlim(years[0], years[-1] + 3.6)
    ax.set_ylim(bottom=0)
    ax.set_ylabel("zones signing for the first time", color=INK_2)
    ax.set_xlabel("year", color=INK_2)
    headline(ax, "What a zone turning DNSSEC on for the first time picked",
             "RSA/SHA-2 peaks in 2019 and ECDSA in 2025. RSA/SHA-1 is the odd one: "
             "still chosen by 373 zones in 2020, thirteen years after RSA/SHA-2 "
             "existed")
    note(ax, "Reverse-DNS zones that gained a DS record that year, counted by the "
             "algorithm family they chose. A zone appears once, in the year it first "
             "signed. 2026 is nine months.")
    save(fig, args.out, "f1_first_signing_choice")

    # ---- 2. the same as a share, so the handover is unmistakable ------------ #
    shares = counts.div(counts.sum(axis=1).replace(0, pd.NA), axis=0) * 100
    fig, ax = plt.subplots(figsize=(10.5, 4.2))
    for fam in ORDER:
        ser = shares[fam].fillna(0)
        if ser.max() < 1:
            continue
        ax.plot(ser.index, ser, color=FAM_COLOR[fam], linewidth=2.8, zorder=3)
        last = ser.index[-1]
        ax.annotate(f"{fam}  {ser[last]:.0f}%", (last, ser[last]), xytext=(9, 0),
                    textcoords="offset points", va="center", fontsize=10.5,
                    color=INK, fontweight="bold")
    ax.axhline(50, color=BASELINE, linewidth=1, linestyle=(0, (4, 3)), zorder=2)
    # Right-hand end: at the left it lands on the RSA/SHA-1 line.
    ax.text(years[-1] + 3.3, 51.5, "half of that year's new signers", fontsize=9.5,
            color=MUTED, ha="right")
    style(ax)
    year_ticks(ax)
    ax.set_ylim(0, 100)
    ax.set_xlim(years[0], years[-1] + 3.4)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}%"))
    ax.set_ylabel("share of that year's new signers", color=INK_2)
    ax.set_xlabel("year", color=INK_2)
    headline(ax, "Two complete handovers in seventeen years",
             "Each family crosses the halfway line on its way up, and the one before it "
             "crosses on the way down")
    note(ax, "Same data as the previous figure, as a share of each year's total. Lines "
             "sum to 100% by construction. EdDSA, standardised in 2017, never reaches 1%.")
    save(fig, args.out, "f2_first_signing_share")

    # ---- 3. where zones that already had DNSSEC went ----------------------- #
    roll = led[led.kind == "rollover"].copy()
    paths = Counter()
    for _, r in roll.iterrows():
        a, b = set(r.from_alg.split(",")), set(r.to_alg.split(","))
        added, dropped = b - a, a - b
        if added and dropped:
            label = (f"{'/'.join(ALG_NAME.get(x, x) for x in sorted(dropped))} → "
                     f"{'/'.join(ALG_NAME.get(x, x) for x in sorted(added))}")
        elif added:
            label = f"added {'/'.join(ALG_NAME.get(x, x) for x in sorted(added))}"
        else:
            label = f"dropped {'/'.join(ALG_NAME.get(x, x) for x in sorted(dropped))}"
        paths[label] += 1
    top = paths.most_common(12)[::-1]
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    colours = [FAM_COLOR["ECDSA"] if "ECDSA" in lbl.split("→")[-1] else
               (FAM_COLOR["RSA/SHA-2"] if "RSASHA" in lbl.split("→")[-1] else MUTED)
               for lbl, _ in top]
    ax.barh(range(len(top)), [n for _, n in top], color=colours, height=0.66, zorder=3)
    for i, (lbl, n) in enumerate(top):
        ax.text(n + 4, i, str(n), va="center", fontsize=10, color=INK_2)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels([lbl for lbl, _ in top], fontsize=9.5, color=INK_2)
    style(ax, axis="x")
    ax.set_xlabel("zones", color=INK_2)
    headline(ax, "Where zones that already had DNSSEC moved",
             "One path dominates: RSASHA256 to ECDSA P-256")
    note(ax, "Only zones that were signed before and after. \"added X\" is a dual-signing "
             "step -- publishing the new algorithm alongside the old one, which is how a "
             "correct rollover begins; \"dropped X\" completes it. 25% of rollovers pass "
             "through that state.")
    save(fig, args.out, "f3_rollover_paths")

    # ---- 4. arrivals against departures, per family per year --------------- #
    rows = []
    for _, r in led.iterrows():
        before, after = set(families(r.from_alg)), set(families(r.to_alg))
        for fam in after - before:
            rows.append({"year": r.year, "family": fam, "direction": "arrived"})
        for fam in before - after:
            rows.append({"year": r.year, "family": fam, "direction": "left"})
    flow = pd.DataFrame(rows)
    net = (flow.pivot_table(index="year", columns=["family", "direction"],
                            aggfunc="size").fillna(0))

    fig, axes = plt.subplots(1, 4, figsize=(11.5, 4.3), sharey=True)
    for ax, fam in zip(axes, ORDER):
        arr = net.get((fam, "arrived"), pd.Series(0, index=net.index)).reindex(years).fillna(0)
        lef = net.get((fam, "left"), pd.Series(0, index=net.index)).reindex(years).fillna(0)
        ax.bar(years, arr, color=FAM_COLOR[fam], width=0.8, zorder=3)
        ax.bar(years, -lef, color=BASELINE, width=0.8, zorder=3)
        ax.axhline(0, color=INK_2, linewidth=1)
        style(ax)
        ax.set_title(fam, loc="left", fontsize=11, color=INK, fontweight="bold")
        ax.set_xlabel("year", color=INK_2)
        ax.tick_params(labelsize=9)
    axes[0].set_ylabel("zones arriving (above)\nand leaving (below)", color=INK_2,
                       fontsize=10)
    if not BARE:
        fig.suptitle("Each family's arrivals and departures, year by year", x=0.005,
                     ha="left", fontsize=13, fontweight="bold", color=INK)
    if not BARE:
        fig.text(0.005, -0.10, textwrap.fill(
        "A zone counts as arriving in the year it first publishes an algorithm from that "
        "family, and leaving in the year it stops. Bars above the line are arrivals, below "
            "are departures.", 132), color=MUTED, fontsize=9.5, linespacing=1.5)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    save(fig, args.out, "f4_arrivals_departures")

    # ---- 5. the installed base these flows add up to ----------------------- #
    stock = {}
    for fam in ORDER:
        arr = net.get((fam, "arrived"), pd.Series(0, index=net.index)).reindex(years).fillna(0)
        lef = net.get((fam, "left"), pd.Series(0, index=net.index)).reindex(years).fillna(0)
        stock[fam] = (arr - lef).cumsum()
    fig, ax = plt.subplots(figsize=(10.5, 4.2))
    ends = sorted(((float(stock[f].iloc[-1]), f) for f in ORDER), reverse=True)
    span = max(v for v, _ in ends) - min(v for v, _ in ends)
    placed = []
    for value, fam in ends:
        y = value
        # Nudge apart: RSA/SHA-1 at 413 and EdDSA at 38 overprint otherwise.
        for taken in placed:
            if abs(y - taken) < span * 0.055:
                y = taken - span * 0.055
        placed.append(y)
        ax.plot(years, stock[fam], color=FAM_COLOR[fam], linewidth=2.6, zorder=3)
        ax.annotate(f"{fam}  {int(value):,}", (years[-1], y), xytext=(9, 0),
                    textcoords="offset points", color=INK, fontsize=10.5,
                    fontweight="bold", va="center")
    style(ax)
    ax.set_xlim(years[0], years[-1] + 3.6)
    year_ticks(ax)
    ax.set_ylabel("zones signed with that family", color=INK_2)
    ax.set_xlabel("year", color=INK_2)
    headline(ax, "The installed base those flows add up to",
             "ECDSA overtakes RSA/SHA-2 in 2024; RSA/SHA-1 peaked in 2014 and has more\n             than halved since")
    note(ax, "Running total of arrivals minus departures, from the same events. This is a "
             "net position over changes observed in the corpus, not a census of the "
             "reverse DNS.")
    save(fig, args.out, "f5_installed_base")

    summary = {
        "first_signing_by_year": {str(y): {f: int(counts[f][y]) for f in ORDER}
                                  for y in years},
        "first_signing_share_pct": {str(y): {f: (None if pd.isna(shares[f][y])
                                                 else round(float(shares[f][y]), 1))
                                             for f in ORDER} for y in years},
        "top_rollover_paths": dict(paths.most_common(20)),
        "installed_base_last": {f: int(stock[f].iloc[-1]) for f in ORDER},
    }
    out_json = Path("out/analysis/algorithm_flows.json")
    out_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"  wrote {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
