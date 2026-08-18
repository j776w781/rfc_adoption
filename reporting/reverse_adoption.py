"""Adoption over the RIPE reverse-delegation corpus, 2009 onward.

Two things this can say that the OpenINTEL side of the project cannot.

**A share of zones, not of records.** Every delegation appears in the zone file, so
the denominator is the number of delegations rather than the number of DNSSEC
records that happened to be measured. "0.71% of delegations are signed" is a claim
about zones; "62% of .gov records use ECDSA" never was.

**Dates before 2018.** The OpenINTEL window starts 2018-01-01, so every first-seen
date there is an upper bound. This corpus starts in 2009, which is before five of
the eight RFCs in the checklist were published, so their adoption can be watched
from publication rather than from whenever measurement happened to begin.

Reads two things, both produced by earlier steps:

``<corpus>/reverse/_summary/*.json``
    Per-day delegation and signed-delegation counts, written by ``ingest-reverse``.
    The scan's record-type prefilter drops NS rows before anything is counted, so
    the denominator lives here rather than in the aggregates.
``<checkpoints>``
    Per-partition checkpoints from ``scale --basis reverse``, holding the per-RFC
    and per-algorithm counts.
"""
from __future__ import annotations

import collections
import datetime
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, "src")
from openintel_rfc.reverse_zones import load_summaries
from openintel_rfc.scale_runner import merge_checkpoints

CORPUS = Path(sys.argv[1] if len(sys.argv) > 1 else "out/reverse/corpus")
CHECKPOINTS = Path(sys.argv[2] if len(sys.argv) > 2 else "out/reverse/analysis/checkpoints")
OUT = Path(sys.argv[3] if len(sys.argv) > 3 else "reporting/charts")
OUT.mkdir(parents=True, exist_ok=True)

# dataviz reference instance, light mode; validated all-pairs elsewhere in this repo.
SURFACE, INK, INK_2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
RAMP = ["#86b6ef", "#2a78d6", "#104281"]

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "text.color": INK,
    "axes.labelcolor": INK_2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": BASELINE, "axes.linewidth": 0.8,
    "xtick.labelsize": 12, "ytick.labelsize": 12,
})


def style(ax, axis="y"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis=axis, color=GRID, linewidth=0.8)
    ax.tick_params(length=0)


def save(fig, name):
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print(f"  wrote {OUT / name}")


# --------------------------------------------------------------------------- #
# 1. Signed share of delegations -- the metric with a real denominator
# --------------------------------------------------------------------------- #

summaries = load_summaries(CORPUS)
if not summaries:
    raise SystemExit(f"No summaries under {CORPUS}; run 'ingest-reverse' first.")
summaries.sort(key=lambda s: s["date"])
print(f"{len(summaries)} measured day(s): {summaries[0]['date']} .. {summaries[-1]['date']}")

RIRS = ("afrinic", "apnic", "arin", "lacnic", "ripe")


def count(day: dict, rir: str, key: str) -> int:
    return int(day["per_rir"].get(rir, {}).get(key, 0))


# The archive's composition changes under you. APNIC contributed zonelets from
# 2009 until 2024-12-01 and its directory is empty from 2025-01-01 onward -- about
# 530,000 delegations leaving the denominator in one step. Charting the raw total
# produces a jump at that date that looks like adoption and is not: the same
# denominator artefact that had to be retracted from the NSEC3 slide of the
# OpenINTEL deck.
#
# So the headline series is computed over the RIRs that report on *every* measured
# day. The full set is kept and plotted beside it, clearly labelled, rather than
# hidden.
STABLE = tuple(
    rir for rir in RIRS
    if all(count(day, rir, "delegations") > 0 for day in summaries)
)
# A RIR that reports on no day at all is not "dropped mid-window" -- it is simply
# outside this window, which is the normal case for a nightly run over the last
# few days. Distinguishing the two matters: one is a composition change worth
# annotating, the other is nothing to say.
DROPPED, ABSENT = [], []
for rir in RIRS:
    if rir in STABLE:
        continue
    (ABSENT if all(count(d, rir, "delegations") == 0 for d in summaries)
     else DROPPED).append(rir)
DROPPED, ABSENT = tuple(DROPPED), tuple(ABSENT)

print(f"stable panel: {', '.join(STABLE) or '(none)'}")
for rir in DROPPED:
    present = [d["date"] for d in summaries if count(d, rir, "delegations") > 0]
    print(f"  excluded from the panel: {rir} reports "
          f"{present[0]} .. {present[-1]} then stops")
for rir in ABSENT:
    print(f"  absent from this window entirely: {rir}")

dates = [datetime.date.fromisoformat(s["date"]) for s in summaries]


def series(rirs):
    signed, total = [], []
    for day in summaries:
        signed.append(sum(count(day, r, "signed_delegations") for r in rirs))
        total.append(sum(count(day, r, "delegations") for r in rirs))
    return ([s / t * 100 if t else None for s, t in zip(signed, total)], signed, total)


if not STABLE:
    raise SystemExit(
        "No RIR reports on every measured day in this window, so there is no "
        "consistent panel to chart. Widen the range, or chart a single RIR."
    )

stable_share, stable_signed, stable_total = series(STABLE)
all_share, all_signed, all_total = series(RIRS)

fig, ax = plt.subplots(figsize=(12, 5.4))
ax.plot(dates, stable_share, color=S1, linewidth=2.4, zorder=4,
        label=f"stable panel ({', '.join('.' + r for r in STABLE)})")
ax.fill_between(dates, stable_share, color=S1, alpha=0.10, zorder=2)
if DROPPED:
    ax.plot(dates, all_share, color=MUTED, linewidth=1.6, linestyle="--", zorder=3,
            label="all RIRs present that day (composition changes)")
    # Mark the break rather than letting the reader infer it from a kink.
    break_day = next(
        (d for d, day in zip(dates, summaries)
         if any(count(day, r, "delegations") == 0 for r in DROPPED)),
        None,
    )
    if break_day is not None:
        ax.axvline(break_day, color=BASELINE, linewidth=1.0, zorder=1)
        ax.annotate(f"{', '.join('.' + r for r in DROPPED)} leaves the archive",
                    (break_day, ax.get_ylim()[1]), textcoords="offset points",
                    xytext=(-8, -14), ha="right", color=MUTED, fontsize=11)

style(ax)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1f}%"))
ax.set_ylabel("share of reverse delegations that are signed", color=INK_2,
              fontsize=12, labelpad=10)
ax.legend(frameon=False, fontsize=12, labelcolor=INK_2, loc="upper left")
ax.annotate(f"{stable_share[-1]:.2f}%" + chr(10)
            + f"{stable_signed[-1]:,} of {stable_total[-1]:,}",
            (dates[-1], stable_share[-1]), textcoords="offset points",
            xytext=(-10, 10), color=INK, fontsize=13, fontweight="bold", ha="right")
save(fig, "reverse_signed_share.png")

# Kept for the JSON and the printed summary below.
share, delegations, signed = stable_share, stable_total, stable_signed

# --------------------------------------------------------------------------- #
# 2. Algorithm mix over time, from the scan
# --------------------------------------------------------------------------- #

ALGORITHM_RFC = {
    "RFC 6605": "ECDSA (13/14)",
    "RFC 8080": "EdDSA (15/16)",
    "RFC 4509": "SHA-256 DS",
    "RFC 4033": "DNSSEC present",
    "RFC 5155": "NSEC3",
}

per_year_rfc: dict[tuple[str, str], int] = collections.defaultdict(int)
scanned_year: dict[str, int] = collections.defaultdict(int)
first_seen: dict[str, str] = {}
have_scan = CHECKPOINTS.is_dir()

if have_scan:
    agg = merge_checkpoints(CHECKPOINTS, recursive=True)
    for row in agg.rows:
        year = row.year_month[:4]
        if row.rfc_id == "*" and row.decision == "scanned":
            scanned_year[year] += row.count
        elif row.rfc_id != "*" and row.indicator_id == "*" and row.decision in (
            "valid_match", "ambiguous"
        ):
            per_year_rfc[(row.rfc_id, year)] += row.count
            prior = first_seen.get(row.rfc_id)
            if prior is None or row.year_month < prior:
                first_seen[row.rfc_id] = row.year_month

    years = sorted(scanned_year)
    fig, ax = plt.subplots(figsize=(12, 5.4))
    for (rfc, label), colour in zip(
        [(r, ALGORITHM_RFC[r]) for r in ("RFC 6605", "RFC 4509", "RFC 8080")],
        (S1, S2, S3),
    ):
        ys, xs2 = [], []
        for i, year in enumerate(years):
            total = scanned_year[year]
            if not total:
                continue
            xs2.append(i)
            ys.append(per_year_rfc[(rfc, year)] / total * 100)
        if not ys:
            continue
        ax.plot(xs2, ys, color=colour, linewidth=2.4, marker="o", markersize=7,
                markerfacecolor=colour, markeredgecolor=SURFACE, markeredgewidth=2,
                label=label, zorder=3)
    style(ax)
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years, rotation=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_ylabel("share of DS records in reverse delegations", color=INK_2,
                  fontsize=12, labelpad=10)
    ax.legend(frameon=False, fontsize=13, labelcolor=INK_2)
    save(fig, "reverse_algorithm_mix.png")

# --------------------------------------------------------------------------- #
# 3. First observation versus publication -- now with pre-2018 evidence
# --------------------------------------------------------------------------- #

# Read from the checklist rather than restated here, so an RFC added to the
# checklist appears in this table without a second edit -- and so the publication
# dates can never drift between the two.
CHECKLIST = json.loads(Path(
    "data/rfc_checklists/dnssec_rfc_checklists.json").read_text(encoding="utf-8"))
ENTRIES = {
    e["rfc_id"]: {
        "published": e["publication_date"][:7],
        "signal_type": e.get("signal_type", "adoption"),
        "status": e.get("status", ""),
    }
    for e in CHECKLIST["rfcs"]
}
CORPUS_START = summaries[0]["date"][:7]

rows = []
for rfc, meta in sorted(ENTRIES.items(), key=lambda kv: int(kv[0].split()[1])):
    published = meta["published"]
    seen = first_seen.get(rfc)
    if seen is None:
        rows.append((rfc, published, "not observed", "", meta["signal_type"]))
        continue
    censored = seen <= CORPUS_START
    lag_years = (int(seen[:4]) - int(published[:4])) + (
        int(seen[5:7]) - int(published[5:7])
    ) / 12
    note = "corpus-start censored" if censored else "observable"
    if meta["signal_type"] == "non_conformance":
        note += " (deprecated mechanism STILL present)"
    rows.append((rfc, published, seen,
                 f"{'<=' if censored else ''}{lag_years:.1f}y", note))

payload = {
    "corpus": "RIPE reverse-DNS delegation zones",
    "measured_days": len(summaries),
    "window": [summaries[0]["date"], summaries[-1]["date"]],
    "denominator": "delegations (zone-level), not records",
    "stable_panel": list(STABLE),
    "excluded_from_panel": list(DROPPED),
    "panel_note": (
        "APNIC contributed zonelets until 2024-12-01 and its directory is empty "
        "from 2025-01-01. The headline share is computed over the RIRs present on "
        "every measured day, so the 2025 step is not read as adoption."
    ),
    "signed_share_stable_first": stable_share[0],
    "signed_share_stable_last": stable_share[-1],
    "signed_share_first": summaries[0]["totals"],
    "signed_share_last": summaries[-1]["totals"],
    "first_observation": rows,
    "note": (
        "A DS in the parent proves the delegation is signed, not that the child "
        "validates. Reverse DNS is a different population from forward DNS."
    ),
}
target = OUT.parent / "reverse_adoption.json"
target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
print(f"  wrote {target}")

print("\nFirst observation versus publication (reverse corpus):")
print(f"  {'RFC':10} {'published':10} {'first seen':12} {'lag':8} note")
for rfc, published, seen, lag, note in rows:
    print(f"  {rfc:10} {published:10} {seen:12} {lag:8} {note}")

print(f"\nSigned share: {summaries[0]['date']} "
      f"{summaries[0]['totals']['signed_share'] * 100:.3f}%  ->  "
      f"{summaries[-1]['date']} {summaries[-1]['totals']['signed_share'] * 100:.3f}%")
