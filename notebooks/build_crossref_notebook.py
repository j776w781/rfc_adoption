"""Build the cross-reference notebook, then execute it so outputs are embedded."""
import json
from pathlib import Path

import nbformat as nbf

NB = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip("\n")))


def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip("\n")))


# ============================================================== title ========
md(r"""
# DNSSEC RFC adoption: OpenINTEL forward DNS vs RIPE reverse delegations

Two independent measurement corpora, cross-referenced.

| | **OpenINTEL** (forward DNS) | **RIPE** (reverse delegations) |
|---|---|---|
| What it measures | what zones *publish* for `.gov`, `.nu`, `.se` | every delegation in `in-addr.arpa` + `ip6.arpa`, all five RIRs |
| Window | 2018-01 → 2026-04 | 2009-04 → 2026-08 |
| Volume | 2,755,488,262 records | 1,875,584 DS records over 1.33M delegations/day |
| Population | registrants (people who bought a domain) | network operators (people allocated an IP block) |
| Denominator | share of **records** | share of **delegations** (zones) |

They share no infrastructure, no operator population and no collection method. So
where they *agree*, the agreement is evidence. Where they *disagree*, the
disagreement is usually telling us something about the measurement rather than
about DNSSEC — and this notebook is mostly about telling those two cases apart.

**Read this first if you read nothing else:** section 3 is a real agreement worth
reporting, section 4 is a 10x apparent disagreement that turns out to be an
artefact of what each side counts, and section 5 is the thing the reverse corpus
can do that the forward one structurally cannot.
""")

# ============================================================== setup ========
md(r"""
## 1. Setup and provenance

Everything below is derived from checkpoints committed in this repository, so the
notebook re-runs from a fresh clone. No network access, no hidden state.
""")

code(r"""
import collections
import datetime
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

# Palette: the validated light-mode instance used throughout this project.
SURFACE, INK, INK_2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, CRITICAL = "#e1e0d9", "#c3c2b7", "#d03b3b"
FWD, REV, THIRD = "#2a78d6", "#eb6834", "#1baf7a"      # forward, reverse, third series
RAMP = ["#86b6ef", "#2a78d6", "#104281"]

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "text.color": INK,
    "axes.labelcolor": INK_2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": BASELINE, "axes.linewidth": 0.8,
    "figure.dpi": 110, "savefig.dpi": 200,
    "xtick.labelsize": 11, "ytick.labelsize": 11, "axes.titlesize": 13,
})

# Resolve the repository root by walking up, so the notebook works whether it is
# opened from notebooks/, from the repo root, or from a Jupyter server rooted
# somewhere else entirely.
ROOT = Path.cwd()
while not (ROOT / "data" / "rfc_checklists").is_dir():
    if ROOT == ROOT.parent:
        raise RuntimeError("run this notebook from inside the rfc_adoption repository")
    ROOT = ROOT.parent
print("repository root:", ROOT)

FIGDIR = ROOT / "reporting" / "charts" / "crossref"
FIGDIR.mkdir(parents=True, exist_ok=True)


def style(ax, axis="y"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis=axis, color=GRID, linewidth=0.8)
    ax.tick_params(length=0)


def pct(ax):
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}%"))


def years(ax, values, step=2):
    '''Integer year ticks; a numeric axis otherwise renders 2012.5, which is not a year.'''
    lo, hi = min(values), max(values)
    ax.set_xticks([y for y in range(lo, hi + 1) if (y - lo) % step == 0 or y == hi])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v)}"))


def save(fig, name):
    fig.savefig(FIGDIR / f"{name}.png", bbox_inches="tight", pad_inches=0.28)
    return FIGDIR / f"{name}.png"
""")

code(r"""
DATA = json.loads((ROOT / "out/analysis/crossref_data.json").read_text(encoding="utf-8"))
SUMMARY_DIR = ROOT / "out/reverse/corpus/reverse/_summary"

def frame(side):
    '''Per (source, year, rfc) match counts and the scanned denominator.'''
    scanned = collections.defaultdict(int)
    for key, value in DATA[side]["scanned"].items():
        source, year = key.split("|")
        scanned[(source, year)] += value
    rows = []
    for key, value in DATA[side]["per"].items():
        source, year, rfc = key.split("|")
        rows.append({"source": source, "year": year, "rfc": rfc, "matches": value,
                     "scanned": scanned[(source, year)]})
    df = pd.DataFrame(rows)
    df["share"] = df.matches / df.scanned * 100
    return df, pd.Series(scanned).rename_axis(["source", "year"]).rename("scanned")

fwd, fwd_scan = frame("openintel")
rev, rev_scan = frame("reverse")

def by_year(df, rfc):
    '''Corpus-wide share for one RFC, pooled across sources.'''
    years = sorted(df.year.unique())
    tot = df.groupby("year").apply(
        lambda g: g.drop_duplicates("source").scanned.sum(), include_groups=False)
    hit = df[df.rfc == rfc].groupby("year").matches.sum()
    # Reindex over every scanned year: a year with no match is a measured zero,
    # not a missing point, and dropping it makes a series look like it starts
    # when adoption starts.
    return (hit.reindex(years, fill_value=0) / tot.reindex(years) * 100).sort_index()

print(f"forward : {fwd_scan.sum():>15,} records, "
      f"{fwd.source.nunique()} zones, {fwd.year.min()}-{fwd.year.max()}")
print(f"reverse : {rev_scan.sum():>15,} DS records, "
      f"{rev.source.nunique()} RIRs,  {rev.year.min()}-{rev.year.max()}")
""")

# =========================================================== validity ========
md(r"""
## 2. Are these two things even comparable?

Three checks before any chart, because the answer to each one bounds what the
comparison is allowed to claim.

**(a) Same indicator definitions?** The forward corpus was scanned under checklist
`0.1.0` and the reverse one under `0.2.0`. That difference is only additive — the
eight RFCs present in both are byte-identical in their indicators, specificity and
publication date, verified below. So per-RFC counts *are* comparable; only the 22
RFCs added in `0.2.0` exist on one side alone.

**(b) Same denominator?** No, and this is the important one. Both sides report
"share of scanned rows", but a scanned row means something different:

- **forward**: any DNSSEC record — `DNSKEY`, `RRSIG`, `DS`, `NSEC`, `NSEC3`, `CDS`, `CDNSKEY`
- **reverse**: a `DS` record, and nothing else — a delegation zone contains no keys or signatures

An indicator scoped to DS records therefore has a *structurally* larger share on
the reverse side. Section 4 is what that looks like when you forget it.

**(c) Same population?** No. Forward DNS is registrants; reverse DNS is network
operators, allocated in blocks, far more concentrated. Neither speaks for "the
DNS", and agreement between them is meaningful precisely because they are
different.
""")

code(r"""
import subprocess

new = json.loads((ROOT / "data/rfc_checklists/dnssec_rfc_checklists.json").read_text(encoding="utf-8"))
old = json.loads(subprocess.run(
    ["git", "show", "9ca61aa:data/rfc_checklists/dnssec_rfc_checklists.json"],
    capture_output=True, text=True, cwd=ROOT).stdout)

o = {r["rfc_id"]: r for r in old["rfcs"]}
n = {r["rfc_id"]: r for r in new["rfcs"]}
identical = [k for k in o if (o[k]["indicators"], o[k]["specificity"], o[k]["publication_date"])
             == (n[k]["indicators"], n[k]["specificity"], n[k]["publication_date"])]

print(f"checklist {old['checklist_version']} -> {new['checklist_version']}")
print(f"RFCs in both: {len(o)}   definitions unchanged: {len(identical)}/{len(o)}")
print(f"added in 0.2.0: {len(n) - len(o)}")
assert len(identical) == len(o), "an RFC changed definition; counts are NOT comparable"
print("\nOK - the shared RFCs are directly comparable across the two corpora.")
SHARED = sorted(identical, key=lambda r: int(r.split()[1]))
print("shared:", ", ".join(SHARED))
""")

# ============================================================ agreement ======
md(r"""
## 3. Where they agree: ECDSA

RFC 6605 (ECDSA P-256/P-384, algorithms 13 and 14) is matched on the algorithm
number alone, independent of record type. A signed zone publishes its `DNSKEY`,
its `RRSIG`s and its parent `DS` all under the same algorithm, so the *algorithm
mix* is comparable across the two corpora even though the record populations are
not.

The two curves start 15 points apart, cross, and land within 1.7 points of each
other in 2026 — measured on different infrastructure, over different operators,
by different methods.
""")

code(r"""
e_fwd, e_rev = by_year(fwd, "RFC 6605"), by_year(rev, "RFC 6605")
overlap = sorted(set(e_fwd.index) & set(e_rev.index))

fig, ax = plt.subplots(figsize=(11, 5.2))
full = sorted(e_rev.index)
ax.plot([int(y) for y in full], e_rev[full].values, color=REV, lw=2.4, marker="o",
        ms=7, mfc=REV, mec=SURFACE, mew=2, label="RIPE reverse delegations", zorder=3)
ax.plot([int(y) for y in sorted(e_fwd.index)], e_fwd[sorted(e_fwd.index)].values,
        color=FWD, lw=2.4, marker="o", ms=7, mfc=FWD, mec=SURFACE, mew=2,
        label="OpenINTEL forward DNS", zorder=4)

ax.axvspan(int(overlap[0]), int(overlap[-1]), color=FWD, alpha=0.05, zorder=0)
ax.annotate("overlap window", (int(overlap[0]) + 0.2, 71), color=MUTED, fontsize=10)

gap_end = abs(e_fwd[overlap[-1]] - e_rev[overlap[-1]])
for value, colour in ((e_fwd[overlap[-1]], FWD), (e_rev[overlap[-1]], REV)):
    ax.annotate(f"{value:.1f}%", (int(overlap[-1]), value), xytext=(10, -4),
                textcoords="offset points", color=colour, fontweight="bold",
                va="center")

style(ax); pct(ax); years(ax, [int(y) for y in full])
ax.set_ylim(0, 78)
ax.set_ylabel("share of that corpus's scanned records", color=INK_2, labelpad=10)
ax.set_title("ECDSA (RFC 6605) converges to the same level in both corpora",
             color=INK, fontweight="bold", loc="left", pad=14)
ax.legend(frameon=False, fontsize=11, labelcolor=INK_2, loc="lower right")
save(fig, "01_ecdsa_convergence"); plt.show()

print(f"2026 gap between the two corpora: {gap_end:.2f} percentage points")
print(f"reverse leads early ({overlap[0]}: {e_rev[overlap[0]]:.1f}% vs {e_fwd[overlap[0]]:.1f}%),")
print(f"forward catches up and both land near {e_fwd[overlap[-1]]:.0f}%.")
""")

md(r"""
The early lead on the reverse side is what you would expect: reverse zones are run
by network operators with automated provisioning, not by registrants clicking
through a registrar. The convergence is the finding — **whatever drove ECDSA
adoption reached both populations, and by 2026 it had reached them equally.**
""")

# =========================================================== divergence ======
md(r"""
## 4. Where they appear to disagree — and why they don't

RFC 4509 (SHA-256 in DS records) looks like a flat contradiction: ~7% in forward
DNS, ~79% in reverse in 2026 - a 10x gap.

It is an artefact, and a completely predictable one. RFC 4509's indicator is

```
rr_type in [DS, CDS]  AND  digest_type = 2
```

so it can only ever match a `DS` record. On the reverse side **every scanned row
is a DS record**, so the denominator is exactly the population the indicator can
match. On the forward side the denominator also contains `DNSKEY`, `RRSIG`,
`NSEC`, `NSEC3` — records the indicator can never match — which dilutes the share
by the ratio of DS records to all DNSSEC records.

Contrast that with ECDSA in section 3, whose indicator is scoped to an algorithm
rather than to a record type, and which therefore compares cleanly.

The right-hand panel is *schematic*: these aggregates carry no record-type
breakdown, so it shows the mechanism rather than the measured proportions.

**The rule this gives us:** an indicator scoped by `rr_type` is only comparable
across corpora whose scanned populations have the same record-type composition.
Ours do not.
""")

code(r"""
d_fwd, d_rev = by_year(fwd, "RFC 4509"), by_year(rev, "RFC 4509")
common = sorted(set(d_fwd.index) & set(d_rev.index))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.8),
                               gridspec_kw={"width_ratios": [1.25, 1]})

x = [int(y) for y in common]
ax1.plot(x, d_rev[common].values, color=REV, lw=2.4, marker="o", ms=7,
         mfc=REV, mec=SURFACE, mew=2, label="RIPE reverse (denominator = DS only)")
ax1.plot(x, d_fwd[common].values, color=FWD, lw=2.4, marker="o", ms=7,
         mfc=FWD, mec=SURFACE, mew=2, label="OpenINTEL forward (denominator = all DNSSEC records)")
style(ax1); pct(ax1); years(ax1, x)
ax1.set_ylim(0, 88)
ax1.set_title("RFC 4509 as reported: a 10x gap", color=INK, fontweight="bold",
              loc="left", pad=12)
ax1.set_ylabel("share of scanned records", color=INK_2, labelpad=10)
ax1.legend(frameon=False, fontsize=9.5, labelcolor=INK_2, loc="center left")

# The mechanism, drawn. SCHEMATIC: the aggregates carry no rr_type breakdown, so
# the forward bar's split is illustrative of the shape, not a measured proportion.
ax2.barh([1], [100], color=REV, height=0.42, zorder=3)
ax2.barh([0], [100], color=GRID, height=0.42, zorder=2)
ax2.barh([0], [7], color=FWD, height=0.42, zorder=3)
ax2.set_yticks([0, 1])
ax2.set_yticklabels(["OpenINTEL\nforward", "RIPE\nreverse"], fontsize=10)
ax2.annotate("DS records: 100% of the denominator", (50, 1), ha="center", va="center",
             color="white", fontsize=10, fontweight="bold", zorder=4)
ax2.annotate("DS", (3.5, 0), ha="center", va="center", color="white",
             fontsize=9, fontweight="bold", zorder=4)
ax2.annotate("DNSKEY / RRSIG / NSEC / NSEC3 - unreachable by this indicator",
             (54, 0), ha="center", va="center", color=INK_2, fontsize=9.5, zorder=4)
style(ax2, axis="x")
ax2.set_xlim(0, 100); ax2.set_xticks([])
for side in ("left", "bottom"):
    ax2.spines[side].set_visible(False)
ax2.set_title("Why (schematic): what each denominator contains", color=INK,
              fontweight="bold", loc="left", pad=12)
ax2.annotate("schematic - the forward split is illustrative, not measured",
             (0, -0.42), xycoords="axes fraction", color=MUTED, fontsize=9)
fig.tight_layout()
save(fig, "02_denominator_artefact"); plt.show()

print(f"apparent gap in {common[-1]}: {d_rev[common[-1]] / d_fwd[common[-1]]:.1f}x")
print("This is not a disagreement about DNSSEC. It is the same number over two")
print("different denominators, and only one of them contains records the")
print("indicator is able to match.")
""")

# ============================================================ zone level =====
md(r"""
## 5. What only the reverse corpus can give

### 5a. A denominator made of zones, not records

Every delegation appears in a reverse zone file, whether it is signed or not. That
makes "what fraction of **zones** are signed" directly countable — the question
the forward corpus cannot answer, and the reason its slides have to keep saying
*record-level, not zone-level*.

One caveat is load-bearing: **APNIC stops contributing to the archive in January
2025**, taking ~530,000 delegations out of the denominator in a single step. Left
alone that produces a jump that reads exactly like an adoption surge. The headline
series below is therefore computed over only the RIRs that report on *every*
measured day, with the all-RIRs series drawn beside it and the break marked.
""")

code(r"""
summaries = sorted((json.loads(p.read_text(encoding="utf-8"))
                    for p in SUMMARY_DIR.glob("*.json")), key=lambda s: s["date"])
RIRS = ("afrinic", "apnic", "arin", "lacnic", "ripe")

def n(day, rir, key):
    return int(day["per_rir"].get(rir, {}).get(key, 0))

STABLE = tuple(r for r in RIRS if all(n(d, r, "delegations") > 0 for d in summaries))
DROPPED = tuple(r for r in RIRS if r not in STABLE)
dates = [datetime.date.fromisoformat(s["date"]) for s in summaries]

def series(rirs):
    sig = [sum(n(d, r, "signed_delegations") for r in rirs) for d in summaries]
    tot = [sum(n(d, r, "delegations") for r in rirs) for d in summaries]
    return [s / t * 100 if t else None for s, t in zip(sig, tot)], sig, tot

share_stable, sig_stable, tot_stable = series(STABLE)
share_all, _, _ = series(RIRS)

fig, ax = plt.subplots(figsize=(11.5, 5.2))
ax.plot(dates, share_stable, color=FWD, lw=2.4, zorder=4,
        label=f"stable panel ({', '.join('.' + r for r in STABLE)})")
ax.fill_between(dates, share_stable, color=FWD, alpha=0.10, zorder=2)
ax.plot(dates, share_all, color=MUTED, lw=1.5, ls="--", zorder=3,
        label="all RIRs reporting that day (composition changes)")

brk = next(d for d, s in zip(dates, summaries)
           if any(n(s, r, "delegations") == 0 for r in DROPPED))
ax.axvline(brk, color=CRITICAL, lw=1.2, alpha=0.65, zorder=1)
ax.annotate(f"{', '.join('.' + r for r in DROPPED)} leaves the archive",
            (brk, 0.12), xytext=(-10, 0), textcoords="offset points",
            ha="right", color=CRITICAL, fontsize=10)

style(ax); pct(ax)
ax.set_ylabel("share of reverse delegations that are signed", color=INK_2, labelpad=10)
ax.set_title("Zone-level DNSSEC deployment, 2009-2026", color=INK,
             fontweight="bold", loc="left", pad=14)
ax.annotate(f"{share_stable[-1]:.2f}%\n{sig_stable[-1]:,} of {tot_stable[-1]:,}",
            (dates[-1], share_stable[-1]), xytext=(-8, 12),
            textcoords="offset points", ha="right", color=INK, fontweight="bold")
ax.legend(frameon=False, fontsize=10.5, labelcolor=INK_2, loc="upper left")
save(fig, "03_zone_level_share"); plt.show()

print(f"{summaries[0]['date']}: {share_stable[0]:.3f}%  ->  "
      f"{summaries[-1]['date']}: {share_stable[-1]:.3f}%")
print(f"crossed 1% in {next(d for d, s in zip(dates, share_stable) if s >= 1.0)}")
print(f"excluded from the panel: {', '.join(DROPPED) or 'none'}")
""")

md(r"""
Under 1.1% of reverse delegations are signed after seventeen years. Set against
the forward corpus — where a majority of *records* in a signed zone use modern
algorithms — this is the gap between "DNSSEC is modernising where it is deployed"
and "DNSSEC is deployed".
""")

# ============================================================ lags ===========
md(r"""
### 5b. Adoption lag that is measured rather than bounded

The forward corpus begins in 2018-01. Any RFC published before that is
**left-censored**: the mechanism is already present on the first day we can see,
so all we can say is *"the lag was at most N years"*. Five of the eight shared
RFCs are in that state.

The reverse corpus begins in 2009-04, which is before four of the algorithm RFCs
were published. For those, the lag is a measurement.
""")

code(r"""
CHECKLIST = {r["rfc_id"]: r for r in new["rfcs"]}
CORPUS_START = {"openintel": "2018-01", "reverse": summaries[0]["date"][:7]}

def months(a, b):
    return (int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))

rows = []
for rfc in sorted(set(DATA["openintel"]["first_seen"]) | set(DATA["reverse"]["first_seen"]),
                  key=lambda r: int(r.split()[1])):
    published = CHECKLIST[rfc]["publication_date"][:7]
    entry = {"rfc": rfc, "published": published}
    for side in ("openintel", "reverse"):
        seen = DATA[side]["first_seen"].get(rfc)
        if seen is None:
            entry[side] = None; entry[side + "_censored"] = None
            continue
        entry[side] = months(published, seen) / 12
        entry[side + "_censored"] = seen <= CORPUS_START[side]
    rows.append(entry)

lags = pd.DataFrame(rows)
measured = lags[(lags.reverse_censored == False) & lags.reverse.notna()].copy()

fig, ax = plt.subplots(figsize=(11.5, 5.0))
y = range(len(lags))
for i, r in lags.iterrows():
    if pd.notna(r.openintel):
        censored = r.openintel_censored
        ax.barh(i + 0.19, r.openintel, height=0.34, color=FWD,
                alpha=0.35 if censored else 1.0, zorder=3,
                hatch="///" if censored else None, edgecolor=FWD)
    if pd.notna(r["reverse"]):
        censored = r.reverse_censored
        ax.barh(i - 0.19, r["reverse"], height=0.34, color=REV,
                alpha=0.35 if censored else 1.0, zorder=3,
                hatch="///" if censored else None, edgecolor=REV)
        # Label only genuine adoption lags. A `meta`/ambiguous RFC matches records
        # that already existed, so its "0.0y" is immediate by construction and
        # labelling it invites reading it as instant adoption.
        genuine = (not censored
                   and CHECKLIST[r.rfc].get("signal_type") == "adoption"
                   and r["reverse"] > 0)
        if genuine:
            ax.annotate(f"{r['reverse']:.1f}y", (r["reverse"], i - 0.19),
                        xytext=(6, -4), textcoords="offset points",
                        color=INK, fontsize=10, fontweight="bold")

style(ax, axis="x")
ax.set_yticks(list(y)); ax.set_yticklabels(lags.rfc, fontsize=10.5)
ax.invert_yaxis()
ax.set_xlabel("years between RFC publication and first observation", color=INK_2, labelpad=10)
ax.set_title("Adoption lag: solid = measured, hatched = censored (an upper bound only)",
             color=INK, fontweight="bold", loc="left", pad=14)

from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=FWD, label="OpenINTEL forward"),
                   Patch(color=REV, label="RIPE reverse"),
                   Patch(facecolor="white", edgecolor=MUTED, hatch="///",
                         label="censored: corpus starts after publication")],
          frameon=False, fontsize=10, labelcolor=INK_2,
          loc="upper left", bbox_to_anchor=(0.62, 0.34))
ax.annotate("bars without a value label are process or clarification RFCs, whose "
            "first post-publication observation is immediate by construction "
            "and is not an adoption lag",
            (0, -0.19), xycoords="axes fraction", color=MUTED, fontsize=9)
save(fig, "04_adoption_lag"); plt.show()

ALGOS = {"RFC 5702": "RSA/SHA-2", "RFC 5933": "GOST",
         "RFC 6605": "ECDSA", "RFC 8080": "EdDSA"}

print("Uncensored first observations in the reverse corpus:\n")
for _, r in measured.sort_values("published").iterrows():
    tag = ALGOS.get(r.rfc, "")
    if tag:
        print(f"  {r.rfc:9} {tag:10} published {r.published}   lag {r['reverse']:.1f} years")
    else:
        print(f"  {r.rfc:9} {'(process)':10} published {r.published}   "
              f"lag {r['reverse']:.1f} years  <- immediate by construction, "
              f"not an adoption lag")

print("\nThe four genuine algorithm-adoption lags, in publication order:")
for rfc, name in ALGOS.items():
    row = measured[measured.rfc == rfc]
    if not row.empty:
        print(f"  {rfc:9} {name:10} {row.iloc[0]['reverse']:.1f} years")
""")

md(r"""
Ordered by publication date, the measured lags are monotonically increasing:

| RFC | Algorithm | Published | Lag |
|---|---|---|---|
| RFC 5702 | RSA/SHA-2 | 2009-10 | **0.5 y** |
| RFC 5933 | GOST | 2010-07 | **2.5 y** |
| RFC 6605 | ECDSA | 2012-04 | **3.7 y** |
| RFC 8080 | EdDSA | 2017-02 | **5.6 y** |

Each new signing algorithm took longer to appear than the one before it. Two
readings are available and this data does not choose between them: either the
ecosystem has slowed, or RSA/SHA-2 was unusually fast because it was a
drop-in change to an algorithm operators already ran, where ECDSA and EdDSA each
required new tooling and new parent support. The second is more plausible, but it
is an interpretation, not a measurement.
""")

# ========================================================== algorithm mix ====
md(r"""
### 5c. Seventeen years of algorithm mix

Only the reverse corpus reaches back far enough to show the whole SHA-1 →
SHA-2 → elliptic-curve transition.
""")

code(r"""
fig, ax = plt.subplots(figsize=(11.5, 5.2))
# Palette validated all-pairs in light mode: worst adjacent CVD dE 9.2 (deutan).
# The aqua sits below 3:1 contrast on this surface, so every series carries a
# direct end label as the required relief rather than relying on the legend.
SERIES = (("RFC 4509", "SHA-256 DS digest", "#eb6834"),
          ("RFC 6605", "ECDSA",             "#2a78d6"),
          ("RFC 3110", "RSA/SHA-1",         "#d03b3b"),
          ("RFC 8080", "EdDSA",             "#1baf7a"))

for rfc, label, colour in SERIES:
    s = by_year(rev, rfc)
    if s.empty:
        continue
    xs = [int(y) for y in s.index]
    ax.plot(xs, s.values, lw=2.3, color=colour, marker="o", ms=5.5,
            mfc=colour, mec=SURFACE, mew=1.6, label=f"{label} ({rfc})", zorder=3)
    ax.annotate(f"{label}  {s.iloc[-1]:.1f}%", (xs[-1], s.iloc[-1]),
                xytext=(8, 0), textcoords="offset points", va="center",
                color=colour, fontsize=10, fontweight="bold")

style(ax); pct(ax); years(ax, [int(y) for y in by_year(rev, "RFC 4509").index])
ax.set_ylabel("share of DS records in reverse delegations", color=INK_2, labelpad=10)
ax.set_title("Algorithm transition in reverse delegations, 2009-2026",
             color=INK, fontweight="bold", loc="left", pad=14)
ax.set_xlim(2008.5, 2029.5)          # room for the direct labels
ax.set_ylim(-3, 100)                 # headroom so the legend clears every series
ax.legend(frameon=False, fontsize=10, labelcolor=INK_2, loc="upper left",
          ncol=2, columnspacing=1.6)
save(fig, "05_algorithm_mix"); plt.show()

sha1 = by_year(rev, "RFC 3110")
print(f"RSA/SHA-1 (deprecated by RFC 9905 in Nov 2025): "
      f"{sha1.iloc[0]:.1f}% in {sha1.index[0]} -> {sha1.iloc[-1]:.1f}% in {sha1.index[-1]}")
print("Still non-zero, which is what RFC 9905 non-conformance will measure.")
""")

# =========================================================== conclusion ======
md(r"""
## 6. What this cross-reference establishes

**Corroborated across both corpora** — different infrastructure, different
operators, different collection:

1. **ECDSA is the dominant modern algorithm and both populations reached the same
   level.** ~63% of forward DNSSEC records and ~64% of reverse DS records in 2026,
   from starting points 15 points apart in 2018.
2. **EdDSA stayed marginal.** Under 1% in both, nine years after RFC 8080. The
   forward corpus alone could be dismissed as three unrepresentative zones; two
   independent corpora agreeing makes it a finding.

**Only the reverse corpus can say:**

3. **Zone-level deployment is ~1.0%** and only crossed 1% this year — against
   seventeen years of availability.
4. **Measured, uncensored adoption lags**: 0.5 y (RSA/SHA-2) → 5.6 y (EdDSA),
   monotonically increasing.
5. **The SHA-1 retirement is nearly complete but not finished.** RSA/SHA-1 fell
   from 81.7% of reverse DS records in 2009 to 4.9% in 2026. RFC 9905 deprecated
   it in November 2025, so that residual 4.9% is precisely what the pipeline's
   `non_conformance` signal now measures — and the reverse corpus is the only
   place we can watch it go to zero.

**A methodological result worth carrying forward:**

6. Indicators scoped by `rr_type` are **not** comparable across corpora with
   different record-type composition — RFC 4509 shows a 10x gap that is entirely
   denominator, not behaviour. Indicators scoped by *algorithm* compare cleanly.
   Any future cross-corpus claim should state which kind it is.

### Open questions

- The reverse corpus contains only `DS` and `NS` records, so RFC 5155 (NSEC3),
  7344 (CDS/CDNSKEY), 8078 and 9276 cannot be evidenced there at all. Those remain
  forward-only, and nothing here corroborates them.
- The forward side is three zones. Its agreement with the reverse corpus on ECDSA
  raises confidence, but does not make `.gov`/`.nu`/`.se` representative.
- APNIC's departure from the archive in 2025 is handled by the stable-panel
  construction above, but if it returns, the panel should be recomputed rather
  than extended.
""")

code(r"""
print("Figures written to", FIGDIR.resolve())
for p in sorted(FIGDIR.glob("*.png")):
    print(f"  {p.name:32} {p.stat().st_size / 1024:6.0f} KB")
""")

NB["cells"] = cells
NB["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}
out = Path("notebooks/dnssec_crossref_openintel_ripe.ipynb")
out.parent.mkdir(parents=True, exist_ok=True)
nbf.write(NB, out)
print(f"wrote {out} ({len(cells)} cells)")
