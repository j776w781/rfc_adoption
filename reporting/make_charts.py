"""Render the deck's charts from the merged checkpoints.

Palette and mark rules follow the dataviz reference instance; the three
categorical slots used here were validated all-pairs in light mode.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, "src")
from openintel_rfc.scale_runner import merge_checkpoints

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)

# --- palette (dataviz reference instance, light mode) ----------------------- #
SURFACE   = "#fcfcfb"
INK       = "#0b0b0b"
INK_2     = "#52514e"
MUTED     = "#898781"
GRID      = "#e1e0d9"
BASELINE  = "#c3c2b7"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"   # blue, orange, aqua
CRITICAL  = "#d03b3b"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "text.color": INK,
    "axes.labelcolor": INK_2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": BASELINE, "axes.linewidth": 0.8,
    "xtick.labelsize": 12, "ytick.labelsize": 12,
})


def style(ax, ygrid=True):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(BASELINE)
    ax.spines["bottom"].set_color(BASELINE)
    if ygrid:
        ax.set_axisbelow(True)
        ax.grid(axis="y", color=GRID, linewidth=0.8, linestyle="-")
    ax.tick_params(length=0)


def save(fig, name):
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print(f"  wrote {name}")


# --- data ------------------------------------------------------------------- #
agg = merge_checkpoints(Path("out/final/checkpoints"), recursive=True)
scanned_sy = collections.defaultdict(int)
scanned_s = collections.defaultdict(int)
for r in agg.rows:
    if r.rfc_id == "*" and r.decision == "scanned":
        scanned_sy[(r.source, r.year_month[:4])] += r.count
        scanned_s[r.source] += r.count

per_sy = collections.defaultdict(int)
per_s = collections.defaultdict(int)
for r in agg.rows:
    if r.rfc_id != "*" and r.indicator_id == "*" and r.decision in ("valid_match", "ambiguous"):
        per_sy[(r.source, r.year_month[:4], r.rfc_id)] += r.count
        per_s[(r.source, r.rfc_id)] += r.count

# Near-empty partitions are excluded from the day counts. OpenINTEL published an
# object for .gov on 2021-04-27..05-10 carrying ~6 rows instead of ~29,000 -- a
# measurement outage on their side, not a scan failure, so the checkpoint is
# legitimately "complete". Counting them as full days would depress every per-day
# rate for that year by ~4% while contributing no records.
_status = [json.loads(p.read_text())
           for p in Path("out/final/checkpoints").rglob("*.status.json")]
NEAR_EMPTY = {(r["source"], r["date"]) for r in _status if r["rows_scanned"] < 100}
days = collections.Counter()
for d in _status:
    if (d["source"], d["date"]) not in NEAR_EMPTY:
        days[(d["source"], d["date"][:4])] += 1

YEARS = ["2018", "2019", "2020", "2021", "2023", "2024", "2026"]


def share(src, year, rfc):
    tot = scanned_sy.get((src, year), 0)
    return per_sy.get((src, year, rfc), 0) / tot * 100 if tot else None


# --- 1. ECDSA migration: the headline --------------------------------------- #
fig, ax = plt.subplots(figsize=(11, 5.4))
for src, color, label in (("gov", S1, ".gov"), ("nu", S2, ".nu")):
    xs = [i for i, y in enumerate(YEARS) if share(src, y, "RFC 6605") is not None]
    ys = [share(src, YEARS[i], "RFC 6605") for i in xs]
    ax.plot(xs, ys, color=color, linewidth=2.4, marker="o", markersize=9,
            markerfacecolor=color, markeredgecolor=SURFACE, markeredgewidth=2,
            label=label, zorder=3)
    # Selective direct label: the endpoint only.
    ax.annotate(f"{label}  {ys[-1]:.0f}%", (xs[-1], ys[-1]), textcoords="offset points",
                xytext=(12, -4), color=INK, fontsize=14, fontweight="bold")
style(ax)
ax.set_xticks(range(len(YEARS)))
ax.set_xticklabels(YEARS)
ax.set_ylim(0, 72)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.set_ylabel("share of the zone's DNSSEC records", color=INK_2, fontsize=12, labelpad=10)
ax.set_xlim(-0.3, len(YEARS) - 0.3 + 0.9)
ax.legend(frameon=False, loc="upper left", fontsize=13, labelcolor=INK_2)
save(fig, "ecdsa_migration.png")

# --- 2. Cross-zone comparison, held at a COMMON year ------------------------ #
# 2021 is the only year all three sources were measured. Comparing each zone's
# latest year instead would put .gov 2026 beside .se 2021 and read the ECDSA
# migration -- which is steep -- as a difference between zones.
COMMON = "2021"
rfcs = [("RFC 6605", "ECDSA"), ("RFC 5155", "NSEC3"), ("RFC 4509", "SHA-256 DS"),
        ("RFC 7344", "CDS/CDNSKEY"), ("RFC 8080", "EdDSA")]
fig, ax = plt.subplots(figsize=(11, 5.4))
h = 0.26
for i, (src, color, label) in enumerate((("gov", S1, ".gov"), ("nu", S2, ".nu"), ("se", S3, ".se"))):
    vals = [share(src, COMMON, r) or 0 for r, _ in rfcs]
    pos = [j + (i - 1) * (h + 0.02) for j in range(len(rfcs))]
    bars = ax.barh(pos, vals, height=h, color=color,
                   label=f"{label}  ({days[(src, COMMON)]} days)", zorder=3)
    for b, v in zip(bars, vals):
        if v >= 0.5:
            ax.annotate(f"{v:.1f}%", (v, b.get_y() + b.get_height() / 2),
                        xytext=(6, 0), textcoords="offset points",
                        va="center", color=INK_2, fontsize=11)
style(ax, ygrid=False)
ax.set_axisbelow(True)
ax.grid(axis="x", color=GRID, linewidth=0.8)
ax.set_yticks(range(len(rfcs)))
ax.set_yticklabels([f"{lbl}" + chr(10) + f"{rfc}" for rfc, lbl in rfcs], fontsize=12, color=INK)
ax.invert_yaxis()
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.set_xlabel(f"share of that zone's DNSSEC records, {COMMON}", color=INK_2,
              fontsize=12, labelpad=10)
ax.set_xlim(0, 52)
ax.legend(frameon=False, fontsize=12, labelcolor=INK_2, loc="lower right")
save(fig, "landscape.png")

# --- 3. .gov delegation automation ------------------------------------------ #
fig, ax = plt.subplots(figsize=(11, 5.0))
gov_years = [y for y in YEARS if scanned_sy.get(("gov", y))]
xs = range(len(gov_years))
for rfc, color, label in (("RFC 7344", S1, "CDS/CDNSKEY published  (RFC 7344)"),
                          ("RFC 8078", S2, "delete signal  (RFC 8078)")):
    ys = [share("gov", y, rfc) or 0 for y in gov_years]
    ax.plot(xs, ys, color=color, linewidth=2.4, marker="o", markersize=9,
            markerfacecolor=color, markeredgecolor=SURFACE, markeredgewidth=2,
            label=label, zorder=3)
    ax.annotate(f"{ys[-1]:.2f}%", (list(xs)[-1], ys[-1]), textcoords="offset points",
                xytext=(12, -4), color=INK, fontsize=13, fontweight="bold")
style(ax)
ax.set_xticks(list(xs)); ax.set_xticklabels(gov_years)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.set_ylabel("share of .gov DNSSEC records", color=INK_2, fontsize=12, labelpad=10)
ax.set_xlim(-0.3, len(gov_years) - 1 + 1.0)
ax.legend(frameon=False, fontsize=12, labelcolor=INK_2, loc="upper left")
save(fig, "gov_automation.png")

# --- 4. Growth vs the zone's own baseline ----------------------------------- #
# Shares mislead here. NSEC3's share of .gov records falls 10.9% -> 5.8%, but its
# per-day count is flat: the share moved because the denominator grew 79%, not
# because NSEC3 retreated. Comparing each mechanism's per-day growth against the
# zone's own baseline growth removes the shared denominator entirely.
def per_day(rfc, year):
    d = days[("gov", year)]
    return per_sy.get(("gov", year, rfc), 0) / d if d else 0

first_y, last_y = "2018", "2026"
baseline = (scanned_sy[("gov", last_y)] / days[("gov", last_y)]) /            (scanned_sy[("gov", first_y)] / days[("gov", first_y)])

mechs = [("RFC 6605", "ECDSA"), ("RFC 7344", "CDS/CDNSKEY"),
         ("RFC 4509", "SHA-256 DS"), ("RFC 5155", "NSEC3")]
growth = [(lbl, per_day(r, last_y) / per_day(r, first_y)) for r, lbl in mechs
          if per_day(r, first_y)]

fig, ax = plt.subplots(figsize=(11, 4.8))
pos = range(len(growth))
bars = ax.barh(list(pos), [g for _, g in growth], height=0.5, color=S1, zorder=3)
for b, (lbl, g) in zip(bars, growth):
    ax.annotate(f"{g:.1f}x", (g, b.get_y() + b.get_height()/2), xytext=(8, 0),
                textcoords="offset points", va="center", color=INK,
                fontsize=13, fontweight="bold")
ax.axvline(baseline, color=CRITICAL, linewidth=2, zorder=4)
# Anchor the reference label in axes coordinates so it cannot fall outside the
# plot: an unexplained red rule is worse than no rule at all.
# Park the reference label in the empty band between the two short bars: on top
# of a bar it reads as that bar's label, and red-on-blue is unreadable anyway.
ax.text(baseline + 0.6, 2.55,
        "the zone's own record count" + chr(10)
        + f"grew {baseline:.1f}x over the same period",
        color=CRITICAL, fontsize=12, fontweight="bold", va="center", ha="left")
style(ax, ygrid=False)
ax.set_axisbelow(True); ax.grid(axis="x", color=GRID, linewidth=0.8)
ax.set_yticks(list(pos)); ax.set_yticklabels([l for l, _ in growth], fontsize=13, color=INK)
ax.invert_yaxis()
ax.set_xlabel("growth in records per measurement day, 2018 to 2026", color=INK_2,
              fontsize=12, labelpad=10)
ax.set_xlim(0, max(g for _, g in growth) * 1.18)
save(fig, "growth_vs_baseline.png")

# --- 5. Panel balance: why totals mislead ----------------------------------- #
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
srcs = ["gov", "nu", "se"]
d = [sum(days[(s, y)] for y in YEARS) for s in srcs]
rws = [scanned_s[s] for s in srcs]
for ax, vals, title, fmt in (
    (a1, d, "Days measured", lambda v: f"{v:,}"),
    (a2, rws, "DNSSEC records", lambda v: f"{v/1e6:,.0f}M"),
):
    tot = sum(vals)
    bars = ax.bar([f".{s}" for s in srcs], vals, color=[S1, S2, S3], width=0.55, zorder=3)
    for b, v in zip(bars, vals):
        ax.annotate(f"{fmt(v)}\n{v/tot:.0%}", (b.get_x() + b.get_width()/2, v),
                    xytext=(0, 6), textcoords="offset points", ha="center",
                    color=INK_2, fontsize=11)
    style(ax)
    ax.set_title(title, color=INK, fontsize=14, pad=14, loc="left")
    ax.set_yticks([])
    ax.set_ylim(0, max(vals) * 1.28)
    ax.tick_params(axis="x", labelsize=13, colors=INK)
save(fig, "panel_balance.png")

# --- 6. NSEC3 iteration buckets (spot measurement) -------------------------- #
# Ordered buckets of one distribution that partition the population, so: stacked,
# and an ordinal blue ramp (light 0 -> dark >=10) rather than categorical hues.
# An earlier version showed only "0" and ">=10" as grouped bars, which silently
# dropped iterations 1-9 -- for .se that was 96% of the names.
compliance_path = Path("reporting/nsec3_compliance.json")
if not compliance_path.is_file():
    print("  skipped nsec3_compliance.png -- run reporting/nsec3_compliance.py first "
          "(it is the only step that needs network)")
else:
    payload = json.loads(compliance_path.read_text(encoding="utf-8"))
    zones = payload["zones"]
    RAMP = ["#86b6ef", "#2a78d6", "#104281"]      # ordinal, validated light mode
    LABELS = ["0 iterations", "1-9 iterations", "10 or more iterations"]

    def buckets(zone):
        hist = {int(k): v["names"] for k, v in zone["iterations"].items() if k != "null"}
        total = zone["total_names"]
        zero = hist.get(0, 0)
        low = sum(v for k, v in hist.items() if 1 <= k <= 9)
        high = sum(v for k, v in hist.items() if k >= 10)
        assert zero + low + high == total, f"buckets must partition {zone['source']}"
        return [zero / total * 100, low / total * 100, high / total * 100]

    fig, ax = plt.subplots(figsize=(11, 4.4))
    ypos = list(range(len(zones)))
    for zi, zone in enumerate(zones):
        left = 0.0
        for bi, value in enumerate(buckets(zone)):
            # 2px surface gap between segments instead of a border.
            ax.barh(zi, value, left=left, height=0.46, color=RAMP[bi], zorder=3,
                    edgecolor=SURFACE, linewidth=1.6,
                    label=LABELS[bi] if zi == 0 else None)
            if value >= 7:      # only label where the text actually fits
                ax.annotate(f"{value:.1f}%", (left + value / 2, zi), ha="center",
                            va="center", color="#ffffff" if bi else INK,
                            fontsize=12, fontweight="bold", zorder=4)
            left += value
    style(ax, ygrid=False)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_yticks(ypos)
    ax.set_yticklabels([f".{z['source']}" for z in zones], fontsize=14, color=INK)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xlabel("share of that zone's NSEC3-signed names (buckets sum to 100%)",
                  color=INK_2, fontsize=12, labelpad=10)
    ax.legend(frameon=False, fontsize=12, labelcolor=INK_2, loc="upper center",
              bbox_to_anchor=(0.5, -0.22), ncol=3)
    save(fig, "nsec3_compliance.png")

print("charts done")
