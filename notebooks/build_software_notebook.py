"""Build the software-releases notebook, then execute it so outputs are embedded.

Every figure derives from JSON and parquet committed in this repository, so the
notebook re-runs from a fresh clone with no network access.
"""
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
# DNS software releases, DNSSEC adoption, and the CVE record

Three clocks over the same seventeen years:

| Clock | Source | What it dates |
|---|---|---|
| **RFC** | IETF publication dates | when a mechanism became a standard |
| **Code** | git tags of 8 implementations, 1,083 stable releases | when a signer could publish it, or a validator check it |
| **Zones** | OpenINTEL forward TLDs + RIR reverse delegations | when anyone actually did |

The question underneath: almost no operator implements DNSSEC themselves, so is
adoption a story about **software updates** rather than about operators reading
RFCs? This notebook draws every figure the three datasets support and lets the
shape of them answer.

**The headline, up front.** Code lag is near zero and deployment lag is years.
Four of four releases that first made a value publishable are followed by
*exactly* zero change in its share a year later. Whatever moves adoption, it is
not the feature becoming available.

Sources: `docs/software_crossref.md`, `docs/releases_vs_adoption.md`,
`docs/cve_crossref.md`.
""")

# ============================================================== setup ========
md(r"""
## 1. Setup, palette and provenance

Colors are the validated reference palette used across this project's reporting:
categorical slots 1-3 (blue, orange, aqua), a single-hue blue ramp for ordered
magnitude, and status red reserved for emphasis. Slots are assigned in fixed
order and never cycled; where more than three categories exist the chart facets
or folds the tail into "other" rather than inventing a fourth hue.
""")

code(r"""
import collections
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter, MaxNLocator

# Walk up so the notebook runs from notebooks/, the repo root, or elsewhere.
ROOT = Path.cwd()
while not (ROOT / "data" / "rfc_checklists").is_dir():
    if ROOT == ROOT.parent:
        raise RuntimeError("run this notebook from inside the rfc_adoption repository")
    ROOT = ROOT.parent
print("repository root:", ROOT)

FIGDIR = ROOT / "reporting" / "charts" / "software"
FIGDIR.mkdir(parents=True, exist_ok=True)

# --- palette (validated reference instance, light mode) --------------------- #
SURFACE = "#fcfcfb"
INK, INK_2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"      # categorical, fixed order
RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#2a78d6", "#1c5cab", "#104281"]
CRITICAL = "#d03b3b"                               # status, never a series color

plt.rcParams.update({
    "font.family": ["DejaVu Sans", "sans-serif"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "text.color": INK,
    "axes.labelcolor": INK_2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": BASELINE, "axes.linewidth": 0.8,
    "xtick.labelsize": 11, "ytick.labelsize": 11, "axes.titlesize": 13,
    "figure.dpi": 110,
})


def style(ax, axis="y"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis=axis, color=GRID, linewidth=0.8)
    ax.tick_params(length=0)


def pct(ax, axis="y"):
    fmt = FuncFormatter(lambda v, _: f"{v:g}%")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


def title(ax, headline, sub=None):
    '''Headline plus an optional deck line, without the two overlapping.'''
    ax.set_title(headline, loc="left", color=INK, fontweight="bold",
                 pad=30 if sub else 8)
    if sub:
        ax.text(0, 1.028, sub, transform=ax.transAxes, color=INK_2, fontsize=10,
                va="bottom")


def year_axis(ax):
    '''Integer year ticks on a fractional-year axis.

    Formatting fractional years with int() alone prints 2021 twice, once for
    2021.0 and once for 2021.5, which reads as a broken axis.
    '''
    ax.xaxis.set_major_locator(MaxNLocator(nbins=8, integer=True))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, v_=None: f"{int(v)}"))


def save(fig, name):
    path = FIGDIR / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", pad_inches=0.3)
    plt.show()
    return path
""")

code(r"""
A = json.loads((ROOT / "out/analysis/software_crossref.json").read_text(encoding="utf-8"))
RA = json.loads((ROOT / "out/analysis/release_vs_adoption.json").read_text(encoding="utf-8"))
CV = json.loads((ROOT / "out/analysis/cve_crossref.json").read_text(encoding="utf-8"))
CA = json.loads((ROOT / "out/analysis/cve_adoption_crossref.json").read_text(encoding="utf-8"))
SUP = json.loads((ROOT / "data/software/software_support.json").read_text(encoding="utf-8"))
REL = json.loads((ROOT / "data/software/release_dates.json").read_text(encoding="utf-8"))
AM = json.loads((ROOT / "out/analysis/adoption_measures.json").read_text(encoding="utf-8"))

SRV = pd.read_parquet(ROOT / "out/server_run/timeline_monthly.parquet")
PAN = pd.read_parquet(ROOT / "out/panel_run/timeline_monthly.parquet")
PANEL_SOURCE = "_pooled-afrinic-arin"

NAME = {"unbound": "Unbound", "nsd": "NSD", "bind9": "BIND 9", "knot": "Knot DNS",
        "kresd": "Knot Resolver", "opendnssec": "OpenDNSSEC",
        "pdns-auth": "PowerDNS Auth", "pdns-rec": "PowerDNS Recursor"}


def share(df, basis, dim, values, source=None):
    '''P(value | signed) per month. An absent month is 0%, never missing --
    dropping those deletes the whole pre-release period an event study needs.'''
    b = df[(df.basis == basis) & (df.dimension == dim)]
    if source is not None:
        b = b[b.source == source]
    den = b[b.value == "_total"].groupby("month").domains_peak.sum().sort_index()
    num = (b[b.value.isin(values)].groupby("month").domains_peak.sum()
           .reindex(den.index, fill_value=0))
    return (num / den * 100).sort_index()


def to_year(m):
    return int(m[:4]) + (int(m[5:7]) - 1) / 12

print(f"{len(A['onset_decomposition'])} observables, "
      f"{sum(len(v['releases']) for v in REL.values())} stable releases, "
      f"{CV['totals']['distinct_cves']} CVEs")
""")

# ========================================================= three clocks ======
md(r"""
## 2. The three clocks

### 2.1 Onset splits into code lag and deployment lag

`onset` is the time from RFC publication to the first zone publishing the value.
It bundles two very different waits: for somebody to write the code, and for
somebody to switch it on. Split, they are not close in size.
""")

code(r"""
rows = [r for r in A["onset_decomposition"]
        if r.get("code_lag_years") is not None and r.get("deployment_lag_years") is not None]
rows.sort(key=lambda r: r["onset_years"])
labels = [f'{r["observable"]}\n{r["rfc"]}' for r in rows]
code_l = [r["code_lag_years"] for r in rows]
depl = [r["deployment_lag_years"] for r in rows]
y = range(len(rows))

fig, ax = plt.subplots(figsize=(10, 3.6))
# Code lag can be negative (shipped from the draft), so it is drawn from zero and
# deployment stacks from wherever code ended.
ax.barh(y, code_l, height=0.5, color=S2, label="code lag: RFC -> first signer release",
        zorder=3)
ax.barh(y, depl, left=[max(c, 0) for c in code_l], height=0.5, color=S1,
        label="deployment lag: that release -> first zone", zorder=3)
for i, r in enumerate(rows):
    ax.text(max(r["code_lag_years"], 0) + r["deployment_lag_years"] + 0.12, i,
            f'{r["onset_years"]:.1f} y total', va="center", color=INK, fontsize=10.5,
            fontweight="bold")
ax.axvline(0, color=BASELINE, linewidth=1)
ax.set_yticks(list(y)); ax.set_yticklabels(labels, fontsize=10.5, color=INK_2)
ax.set_xlabel("years", color=INK_2)
ax.set_xlim(-0.8, 5.2)
style(ax, axis="x")
ax.legend(frameon=False, loc="lower right", fontsize=10, labelcolor=INK_2)
title(ax, "Almost all of onset is operators, not implementers",
      "Negative code lag means the implementation shipped before the RFC was published")
save(fig, "01_onset_decomposition")
""")

md(r"""
### 2.2 The same thing as a timeline

One row per observable. The gap that matters is the one on the right.
""")

code(r"""
rows = [r for r in A["onset_decomposition"] if r.get("first_zone_seen")]
rows.sort(key=lambda r: r["rfc_published"], reverse=True)
fig, ax = plt.subplots(figsize=(10, 3.4))
for i, r in enumerate(rows):
    xs = [to_year(r["rfc_published"]), to_year(r["first_signer_released"]),
          to_year(r["first_zone_seen"])]
    ax.plot([xs[0], xs[2]], [i, i], color=GRID, linewidth=6, solid_capstyle="round",
            zorder=1)
    ax.scatter(xs[0], i, s=90, color=S3, zorder=3, edgecolor=SURFACE, linewidth=2)
    ax.scatter(xs[1], i, s=90, color=S2, zorder=3, edgecolor=SURFACE, linewidth=2)
    ax.scatter(xs[2], i, s=90, color=S1, zorder=3, edgecolor=SURFACE, linewidth=2)
ax.set_yticks(range(len(rows)))
ax.set_yticklabels([f'{r["observable"]}  {r["rfc"]}' for r in rows], fontsize=10.5,
                   color=INK_2)
ax.set_xlabel("year", color=INK_2)
year_axis(ax)
style(ax, axis="x")
for label, colour, xoff in (("RFC published", S3, 0), ("first signer release", S2, 1),
                            ("first zone", S1, 2)):
    ax.scatter([], [], s=90, color=colour, label=label)
ax.legend(frameon=False, loc="lower right", fontsize=10, labelcolor=INK_2, ncol=3)
title(ax, "Code arrives with the standard; zones arrive years later")
save(fig, "02_three_clocks_timeline")
""")

md(r"""
### 2.3 Three of five implementations shipped before the RFC existed

Negative bars are implementations that shipped from an Internet-Draft.
""")

code(r"""
pre = [r for r in SUP["support"] if r.get("standard_codepoint", True)]
lead = []
RFC_PUB = {"RFC 5011": "2007-09", "RFC 5155": "2008-03", "RFC 5702": "2009-10",
           "RFC 5933": "2010-07", "RFC 6605": "2012-04", "RFC 7344": "2014-09",
           "RFC 8080": "2017-02"}
for r in pre:
    pub = RFC_PUB.get(r["rfc"])
    if not pub:
        continue
    months = (int(r["released"][:4]) - int(pub[:4])) * 12 + (int(r["released"][5:7]) - int(pub[5:7]))
    lead.append((months, f'{NAME[r["implementation"]]} {r["first_release"]}',
                 f'{r["observable"]}  {r["rfc"]}'))
lead.sort()
fig, ax = plt.subplots(figsize=(10, 6.2))
ys = range(len(lead))
colors = [S2 if m < 0 else S1 for m, _, _ in lead]
ax.barh(list(ys), [m for m, _, _ in lead], height=0.62, color=colors, zorder=3)
ax.axvline(0, color=BASELINE, linewidth=1.2)
ax.set_yticks(list(ys))
ax.set_yticklabels([f"{s}   ·   {o}" for _, s, o in lead], fontsize=9.5, color=INK_2)
ax.set_xlabel("months after the RFC was published  (negative = shipped from the draft)",
              color=INK_2)
style(ax, axis="x")
ax.scatter([], [], marker="s", s=70, color=S2, label="before the RFC")
ax.scatter([], [], marker="s", s=70, color=S1, label="after the RFC")
ax.legend(frameon=False, loc="lower right", fontsize=10, labelcolor=INK_2)
title(ax, "When each implementation shipped, against its RFC")
save(fig, "03_pre_rfc_lead")
""")

md(r"""
## 3. The software itself

### 3.1 Release cadence

1,083 stable releases across eight projects. BIND's odd minors from 9.13 on are
development branches and are excluded — counting them dates `dnssec-policy`'s CDS
publication to 9.15.6 in 2019 rather than 9.16.0 in 2020.
""")

code(r"""
order = sorted(REL, key=lambda p: -len(REL[p]["releases"]))
fig, axes = plt.subplots(4, 2, figsize=(11, 8), sharex=True)
for ax, proj in zip(axes.ravel(), order):
    years = collections.Counter(int(d[:4]) for d in REL[proj]["releases"].values())
    span = range(min(years), max(years) + 1)
    ax.bar(list(span), [years.get(y, 0) for y in span], color=S1, width=0.75, zorder=3)
    style(ax)
    ax.set_title(f'{NAME[proj]}   ({len(REL[proj]["releases"])} releases, '
                 f'{REL[proj]["role"]})', loc="left", fontsize=11, color=INK)
    ax.tick_params(labelsize=9.5)
axes[-1][0].set_xlabel("year", color=INK_2)
axes[-1][1].set_xlabel("year", color=INK_2)
fig.suptitle("Stable releases per year", x=0.005, ha="left", fontsize=13,
             fontweight="bold", color=INK)
fig.tight_layout(rect=[0, 0, 1, 0.97])
save(fig, "04_release_cadence")
""")

md(r"""
### 3.2 Who supported what, and when

Cell colour is the year the capability first shipped in a stable release —
darker is later. Blank means the project has no row for that mechanism in the
dataset, not that it lacks support.
""")

code(r"""
alias = {"alg 15": "alg 15/16", "alg 16": "alg 15/16", "alg 13": "alg 13/14",
         "alg 14": "alg 13/14", "alg 8": "alg 8/10", "alg 10": "alg 8/10"}
grid = {}
for r in SUP["support"]:
    obs = alias.get(r["observable"], r["observable"])
    key = (NAME[r["implementation"]], f'{obs}\n{r["rfc"]}')
    yr = int(r["released"][:4])
    if key not in grid or yr < grid[key][0]:
        grid[key] = (yr, r["capability"])

projects = sorted({k[0] for k in grid})
mechs = sorted({k[1] for k in grid}, key=lambda m: min(v[0] for k, v in grid.items()
                                                       if k[1] == m))
lo = min(v[0] for v in grid.values()); hi = max(v[0] for v in grid.values())
SHORT_CAP = {"algorithm-aware": "alg-aware", "revoked-KSK state": "revoked-KSK"}
fig, ax = plt.subplots(figsize=(12, 4.2))
for xi, m in enumerate(mechs):
    for yi, p in enumerate(projects):
        cell = grid.get((p, m))
        if not cell:
            continue
        frac = (cell[0] - lo) / max(hi - lo, 1)
        colour = RAMP[min(int(frac * (len(RAMP) - 1) + 0.5), len(RAMP) - 1)]
        ax.add_patch(plt.Rectangle((xi - 0.44, yi - 0.42), 0.88, 0.84, color=colour,
                                   zorder=3))
        ax.text(xi, yi, f"{cell[0]}\n{SHORT_CAP.get(cell[1], cell[1])}", ha="center",
                va="center", fontsize=8.5,
                color="#ffffff" if frac > 0.55 else INK, zorder=4)
ax.set_xlim(-0.6, len(mechs) - 0.4); ax.set_ylim(-0.6, len(projects) - 0.4)
ax.set_xticks(range(len(mechs)))
ax.set_xticklabels([m.replace("\n", "  ") for m in mechs], fontsize=9,
                   color=INK_2, rotation=28, ha="right")
ax.set_yticks(range(len(projects))); ax.set_yticklabels(projects, fontsize=10, color=INK_2)
for side in ("top", "right", "left", "bottom"):
    ax.spines[side].set_visible(False)
ax.tick_params(length=0)
title(ax, "First stable release with each capability",
      "Darker = later. Cell text is the year and what the release could do.")
save(fig, "05_support_matrix")
""")

md(r"""
### 3.3 Default changes — the only mechanism that reaches an operator who decided nothing

Six of the seven propagate silently on upgrade. BIND's `dnssec-policy` is opt-in:
an operator has to write `dnssec-policy default;` to get it.
""")

code(r"""
SHORT_WHAT = {"built-in dnssec-policy 'default' signs with one ECDSAP256SHA256 CSK":
              "dnssec-policy 'default' -> one ECDSAP256SHA256 CSK"}
dc = sorted(SUP["default_changes"], key=lambda r: r["released"])
fig, ax = plt.subplots(figsize=(10, 3.0))
for i, r in enumerate(dc):
    x = to_year(r["released"])
    opt = r.get("opt_in", False)
    ax.scatter(x, i, s=130, color=S2 if opt else S1, zorder=3, edgecolor=SURFACE,
               linewidth=2)
    ax.text(x + 0.16, i,
            f'{NAME[r["implementation"]]} {r["first_release"]} — '
            f'{SHORT_WHAT.get(r["what"], r["what"])}',
            va="center", fontsize=9.5, color=INK_2)
    ax.plot([to_year("2009-01"), x], [i, i], color=GRID, linewidth=1.4, zorder=1)
ax.set_yticks([]); ax.set_xlim(2009, 2029)
ax.set_xlabel("year", color=INK_2)
year_axis(ax)
style(ax, axis="x")
ax.scatter([], [], s=110, color=S1, label="applies on upgrade")
ax.scatter([], [], s=110, color=S2, label="opt-in")
ax.legend(frameon=False, loc="lower right", fontsize=10, labelcolor=INK_2)
title(ax, "Every default change found across five projects in seventeen years")
save(fig, "06_default_changes")
""")

md(r"""
## 4. Adoption, and whether releases explain it

### 4.1 The curves

Reverse rates use the strict **AFRINIC + ARIN** panel, the same population as
`out/analysis/adoption_measures.json`; summing all five RIRs double-counts names
present in more than one and moves every crossing date. Forward rates pool the
seven forward TLDs, which are disjoint zones, so that pooling is exact.
""")

code(r"""
CURVES = [("alg 8/10", ["8", "10"], "RSA/SHA-2", S1),
          ("alg 13/14", ["13", "14"], "ECDSA", S2),
          ("alg 15/16", ["15", "16"], "EdDSA", S3)]

fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
for ax, (basis, df, dim, src, label) in zip(
        axes, [("reverse", PAN, "algorithm_ds", PANEL_SOURCE,
                "reverse: strict AFRINIC+ARIN panel"),
               ("zonefile", SRV, "algorithm_dnskey", None,
                "forward: 7 disjoint TLDs")]):
    for _, vals, name, colour in CURVES:
        s = share(df, basis, dim, vals, source=src)
        xs = [to_year(m) for m in s.index]
        ax.plot(xs, s.values, color=colour, linewidth=2, label=name, zorder=3)
        if s.max() > 3:
            ax.annotate(name, (xs[-1], s.values[-1]), xytext=(6, 0),
                        textcoords="offset points", color=INK, fontsize=10.5,
                        fontweight="bold", va="center")
    style(ax); pct(ax)
    ax.set_title(label, loc="left", fontsize=11, color=INK_2)
    ax.set_xlabel("year", color=INK_2)
    year_axis(ax)
    ax.set_xlim(right=ax.get_xlim()[1] + 1.6)
axes[0].set_ylabel("share of signed delegations", color=INK_2)
axes[0].legend(frameon=False, loc="upper left", fontsize=10, labelcolor=INK_2)
fig.suptitle("Signing-algorithm share, two corpora", x=0.005, ha="left", fontsize=13,
             fontweight="bold", color=INK)
fig.tight_layout(rect=[0, 0, 1, 0.95])
save(fig, "07_adoption_curves")
""")

md(r"""
### 4.2 Which date predicts takeoff?

Time from each candidate date to the month the value first crossed 1%. Where a
default change exists it is three to six times closer than the RFC.
""")

code(r"""
rows = [r for r in RA["takeoff"] if r["first_month_over_1pct"] and not r["censored_start"]]
rows.sort(key=lambda r: r["from_rfc_to_1pct_years"])
labels = [f'{r["observable"]}\n{r["basis"]}' for r in rows]
y = range(len(rows))
h = 0.26
fig, ax = plt.subplots(figsize=(10, 3.6))
for off, key, colour, name in ((-h, "from_rfc_to_1pct_years", S1, "from RFC"),
                               (0.0, "from_first_signer_to_1pct_years", S2,
                                "from first signer release"),
                               (h, "from_default_change_to_1pct_years", S3,
                                "from default change")):
    vals = [r[key] if r[key] is not None else 0 for r in rows]
    ax.barh([i + off for i in y], vals, height=h - 0.03, color=colour, label=name,
            zorder=3)
    for i, (r, v) in enumerate(zip(rows, vals)):
        if r[key] is not None:
            ax.text(v + 0.09, i + off, f"{v:.2f}", va="center", fontsize=9, color=INK_2)
        elif key.endswith("default_change_to_1pct_years"):
            ax.text(0.09, i + off, "no default change identified", va="center",
                    fontsize=9, color=MUTED, style="italic")
ax.set_yticks(list(y)); ax.set_yticklabels(labels, fontsize=10, color=INK_2)
ax.set_xlabel("years to the 1% crossing", color=INK_2)
style(ax, axis="x")
ax.legend(frameon=False, loc="lower right", fontsize=10, labelcolor=INK_2)
title(ax, "The default change sits closest to takeoff",
      "Two observations carry the default column; treat it as suggestive")
save(fig, "08_takeoff_lags")
""")

md(r"""
### 4.3 The event studies do not confirm it

Mean monthly change in share, twelve months either side of each release. Events
firing above 20% share are excluded from interpretation: a bounded series must
decelerate as it approaches its ceiling, so a late event inherits a negative
delta it did not cause.
""")

code(r"""
ev = [e for e in RA["event_studies"] if not e["late_curve"]]
ev.sort(key=lambda e: (e["kind"], e["observable"]))
def pretty(sw):
    key, _, ver = sw.partition(" ")
    return f"{NAME.get(key, key)} {ver}"

labels = [f'{pretty(e["software"])}\n{e["observable"]} · {e["basis"]}' for e in ev]
y = range(len(ev))
fig, ax = plt.subplots(figsize=(10, 3.4))
for i, e in enumerate(ev):
    ax.plot([e["mean_pp_before"], e["mean_pp_after"]], [i, i], color=GRID, linewidth=5,
            solid_capstyle="round", zorder=1)
    ax.scatter(e["mean_pp_before"], i, s=95, color=S1, zorder=3, edgecolor=SURFACE,
               linewidth=2)
    ax.scatter(e["mean_pp_after"], i, s=95, color=S2, zorder=3, edgecolor=SURFACE,
               linewidth=2)
    ax.text(max(e["mean_pp_before"], e["mean_pp_after"]) + 0.0035, i,
            f'{e["change_pp"]:+.3f} pp', va="center", fontsize=9.5, color=INK_2)
ax.set_yticks(list(y)); ax.set_yticklabels(labels, fontsize=9.5, color=INK_2)
ax.set_xlabel("mean monthly change in share (percentage points)", color=INK_2)
ax.axvline(0, color=BASELINE, linewidth=1)
ax.set_xlim(-0.006, 0.082)          # headroom so the right-hand labels are not clipped
style(ax, axis="x")
ax.scatter([], [], s=95, color=S1, label="12 months before")
ax.scatter([], [], s=95, color=S2, label="12 months after")
ax.legend(frameon=False, loc="upper right", fontsize=10, labelcolor=INK_2,
          bbox_to_anchor=(1.0, 1.18), ncol=2)
title(ax, "No release is followed by a change in adoption rate",
      "Availability releases sit at exactly zero on both sides")
save(fig, "09_event_studies")
""")

md(r"""
## 5. NSEC3: the one place a validator can force a zone to change

### 5.1 The iteration collapse

Resolver vendors converged on a 150-iteration cap in 2021, stated outright in
Unbound's commit message. Zones moved two months later — and ten months before
RFC 9276 documented it.
""")

code(r"""
col = A["nsec3_iteration_collapse"]
h = col["high_iteration_names_by_month"]
months = sorted(h)
xs = [to_year(m) for m in months]
fig, ax = plt.subplots(figsize=(10, 3.6))
ax.plot(xs, [h[m] for m in months], color=S1, linewidth=2.2, zorder=3)
ax.fill_between(xs, [h[m] for m in months], color=S1, alpha=0.10, zorder=2)
# Three of the four limits land within seven months of each other in 2021, so
# their labels are staggered; stacked at one height they overprint.
top = ax.get_ylim()[1]
for k, lim in enumerate(sorted(col["validator_limits"], key=lambda r: r["released"])):
    x = to_year(lim["released"][:7])
    if not (xs[0] <= x <= xs[-1]):
        continue
    ax.axvline(x, color=MUTED, linewidth=1, linestyle=(0, (4, 3)), zorder=1)
    ax.annotate(f'{NAME[lim["implementation"]]} {lim["first_release"]}',
                xy=(x, top * 0.99), xytext=(-40 + 26 * k, -18 - 26 * k),
                textcoords="offset points", fontsize=8.5, color=INK_2, ha="left",
                arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.8))
x9276 = to_year("2022-08")
ax.axvline(x9276, color=CRITICAL, linewidth=1.6, zorder=1)
ax.annotate("RFC 9276 published", xy=(x9276, top * 0.99), xytext=(10, -6),
            textcoords="offset points", fontsize=9.5, color=CRITICAL,
            fontweight="bold", ha="left")
worst = col["largest_single_month_fall"]
ax.annotate(f'{worst["month"]}: {worst["before"]:,} -> {worst["after"]:,}',
            (to_year(worst["month"]), worst["after"]), xytext=(14, 46),
            textcoords="offset points", fontsize=10, color=INK, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=INK_2, linewidth=1.2))
style(ax)
ax.set_ylabel("NSEC3 owner names at >= 100 iterations", color=INK_2)
ax.set_xlabel("year", color=INK_2)
year_axis(ax)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v):,}"))
title(ax, "Zones moved when resolvers stopped accepting them",
      "Owner names, not zones: NSEC3 owners are hashed, so a zone contributes one per owner")
save(fig, "10_nsec3_collapse")
""")

code(r"""
f = SRV[SRV.basis == "zonefile"]
par = f[(f.dimension == "rr_type") & (f.value.astype(str) == "NSEC3PARAM")] \
    .groupby("month").domains_peak.sum()
signed = f[(f.dimension == "algorithm_dnskey") & (f.value.astype(str) == "_total")] \
    .groupby("month").domains_peak.sum()
s = (par / signed * 100).dropna().sort_index()
xs = [to_year(m) for m in s.index]

fig, ax = plt.subplots(figsize=(10, 3.2))
ax.plot(xs, s.values, color=S1, linewidth=2.2, zorder=3)
ax.fill_between(xs, s.values, color=S1, alpha=0.10, zorder=2)
for m in (s.index[0], s.index[-1]):
    ax.annotate(f"{s[m]:.1f}%", (to_year(m), s[m]), xytext=(0, 10),
                textcoords="offset points", ha="center", fontsize=11, color=INK,
                fontweight="bold")
style(ax); pct(ax)
ax.set_ylim(0, 105)
ax.set_ylabel("share of signed zones", color=INK_2)
ax.set_xlabel("year", color=INK_2)
year_axis(ax)
title(ax, "NSEC3 is the most deployed optional mechanism in DNSSEC",
      "NSEC3PARAM at the zone apex, forward corpus. Algorithm 7 peaks at 29% and is a bad proxy.")
save(fig, "11_nsec3_prevalence")
""")

md(r"""
## 6. The unit of change is the operator, not the zone

`.se` and `.nu` are both run by the Swedish Internet Foundation; `.ch` and `.li`
by SWITCH. In 20 of 21 detected jumps the partner zone moves in the same month.
""")

code(r"""
PARTNER = {"se": "nu", "nu": "se", "ch": "li", "li": "ch"}
OPNAME = {"se": "Swedish Internet Foundation", "nu": "Swedish Internet Foundation",
          "ch": "SWITCH", "li": "SWITCH"}
jumps = [(obs, j) for obs, js in A["portfolio_jumps"].items() for j in js]
jumps.sort(key=lambda t: t[1]["month"])
fig, ax = plt.subplots(figsize=(10, 4.4))
for i, (obs, j) in enumerate(jumps):
    ax.barh(i, j["delta_zones"], height=0.62,
            color=S1 if OPNAME.get(j["source"]) == "SWITCH" else S2, zorder=3)
    ax.text(j["delta_zones"] * 1.04, i, f'{j["delta_zones"]:,}', va="center",
            fontsize=9, color=INK_2)
ax.set_yticks(range(len(jumps)))
ax.set_yticklabels([f'{j["month"]}  .{j["source"]}  ·  {obs}' for obs, j in jumps],
                   fontsize=9.5, color=INK_2)
ax.set_xscale("log")
ax.set_xlabel("zones gained in one month (log scale)", color=INK_2)
style(ax, axis="x")
ax.scatter([], [], marker="s", s=70, color=S2, label="Swedish Internet Foundation (.se, .nu)")
ax.scatter([], [], marker="s", s=70, color=S1, label="SWITCH (.ch, .li)")
ax.legend(frameon=False, loc="lower right", fontsize=10, labelcolor=INK_2)
title(ax, "Every jump belongs to one of two registry operators")
save(fig, "12_portfolio_jumps")
""")

md(r"""
## 7. The CVE record

441 CVEs touching the eight implementations or naming DNS/DNSSEC itself, from
NVD per-product CPE queries, NVD keyword queries and the projects' own git
history. None of the three sources subsumes the others.
""")

code(r"""
fig, axes = plt.subplots(1, 2, figsize=(11, 3.2))
scope = CV["totals"]["by_scope"]
order = ["dns", "dnssec", "dependency"]
lab = {"dns": "DNS, not DNSSEC", "dnssec": "DNSSEC", "dependency": "dependency"}
ax = axes[0]
ax.bar(range(len(order)), [scope[k] for k in order], color=[S1, S2, S3], width=0.62,
       zorder=3)
for i, k in enumerate(order):
    ax.text(i, scope[k] + 6, f"{scope[k]}", ha="center", fontsize=11, color=INK,
            fontweight="bold")
ax.set_xticks(range(len(order))); ax.set_xticklabels([lab[k] for k in order], fontsize=10,
                                                     color=INK_2)
style(ax); ax.set_ylim(0, max(scope.values()) * 1.16)
ax.set_title("By scope", loc="left", fontsize=11, color=INK_2)

ax = axes[1]
mech = CV["totals"]["by_mechanism"]
RFC_OF = {"nsec3": "RFC 5155", "nsec": "RFC 4034", "dnskey": "RFC 4034",
          "rrsig": "RFC 4035", "validation": "RFC 4035", "trust-anchor": "RFC 5011",
          "algorithm": "RFC 6605/8080", "ds-digest": "RFC 4509",
          "dnssec-other": "RFC 4033", "nxt-sig-key": "RFC 2535"}
byrfc = collections.Counter()
for k, v in mech.items():
    byrfc[RFC_OF.get(k, k)] += v
items = byrfc.most_common()
ax.barh(range(len(items)), [v for _, v in items], height=0.62, color=S1, zorder=3)
for i, (_, v) in enumerate(items):
    ax.text(v + 0.5, i, str(v), va="center", fontsize=10, color=INK_2)
ax.set_yticks(range(len(items)))
ax.set_yticklabels([k for k, _ in items], fontsize=10, color=INK_2)
ax.invert_yaxis(); style(ax, axis="x")
ax.set_title("DNSSEC CVEs by the RFC they touch", loc="left", fontsize=11, color=INK_2)
fig.suptitle("DNSSEC is 22% of the CVE surface, and validation is most of that",
             x=0.005, ha="left", fontsize=13, fontweight="bold", color=INK)
fig.tight_layout(rect=[0, 0, 1, 0.93])
save(fig, "13_cve_scope_and_rfc")
""")

md(r"""
### 7.1 The whole DNSSEC CVE surface is on the validating side

NSD serves zones somebody else signed and OpenDNSSEC signs them; neither
validates, and neither has a DNSSEC CVE. This is exactly the half of DNSSEC this
project's zone-file measurement cannot see.
""")

code(r"""
qm = CV["query_method"]
cpe = [p for p in CV["per_project"] if qm[p] == "cpe"]
cpe.sort(key=lambda p: -sum(CV["per_project"][p].values()))
dn = [CV["per_project"][p].get("dnssec", 0) for p in cpe]
other = [sum(CV["per_project"][p].values()) - d for p, d in zip(cpe, dn)]
x = range(len(cpe))
fig, ax = plt.subplots(figsize=(10, 3.3))
ax.bar(x, dn, color=S2, width=0.6, label="DNSSEC", zorder=3)
ax.bar(x, other, bottom=dn, color=S1, width=0.6, label="everything else", zorder=3)
for i, (d, o) in enumerate(zip(dn, other)):
    if d:
        ax.text(i, d / 2, str(d), ha="center", va="center", fontsize=10, color="#ffffff",
                fontweight="bold")
    ax.text(i, d + o + 4, str(d + o), ha="center", fontsize=10, color=INK_2)
ax.set_xticks(list(x))
ax.set_xticklabels([f'{NAME[p]}\n{CV["project_roles"][p]}' for p in cpe], fontsize=9.5,
                   color=INK_2)
style(ax)
ax.set_ylabel("CVEs", color=INK_2)
ax.legend(frameon=False, loc="upper right", fontsize=10, labelcolor=INK_2)
title(ax, "NSD has 14 CVEs and none is DNSSEC; OpenDNSSEC has one, a dependency",
      "CPE-attributed products only; Knot and OpenDNSSEC have no usable CPE")
save(fig, "14_cve_by_project")
""")

code(r"""
years = collections.Counter(c["published"][:4] for c in CV["cves"]
                            if c["scope"] == "dnssec" and c["published"])
span = [str(y) for y in range(min(int(y) for y in years), max(int(y) for y in years) + 1)]
vals = [years.get(y, 0) for y in span]
fig, ax = plt.subplots(figsize=(10, 3.2))
colours = [CRITICAL if y == "2026" else S1 for y in span]
ax.bar(range(len(span)), vals, color=colours, width=0.72, zorder=3)
ax.text(len(span) - 1, vals[-1] + 1, f"{vals[-1]}", ha="center", fontsize=11,
        color=CRITICAL, fontweight="bold")
ax.set_xticks(range(0, len(span), 2))
ax.set_xticklabels(span[::2], fontsize=9.5, color=INK_2)
style(ax); ax.set_ylabel("DNSSEC CVEs published", color=INK_2)
title(ax, "2026 carries 30 DNSSEC CVEs against a prior maximum of eight",
      "ISC attributes the run to systematic code auditing: a discovery-rate change, not a defect-rate one")
save(fig, "15_cve_per_year")
""")

md(r"""
### 7.2 Fixes, embargoes, and how long the ecosystem stays exposed
""")

code(r"""
lat = []
for c in CV["cves"]:
    for p, f in c["fixes"].items():
        if c["published"] and f.get("released"):
            lat.append((pd.Timestamp(f["released"]) - pd.Timestamp(c["published"])).days)
fig, axes = plt.subplots(1, 2, figsize=(11, 3.2))
ax = axes[0]
ax.hist([d for d in lat if -200 <= d <= 400], bins=40, color=S1, zorder=3)
ax.axvline(0, color=CRITICAL, linewidth=1.6, zorder=4)
ax.text(0, ax.get_ylim()[1] * 0.94, "  CVE published", color=CRITICAL, fontsize=9.5,
        fontweight="bold", va="top")
style(ax)
ax.set_xlabel("days from CVE publication to the release that fixed it", color=INK_2)
ax.set_ylabel("fixes", color=INK_2)
share_before = sum(1 for d in lat if d < 0) / len(lat) * 100
ax.set_title(f"{share_before:.0f}% shipped before publication — coordinated disclosure",
             loc="left", fontsize=11, color=INK_2)

ax = axes[1]
co = [c for c in CV["coordinated"] if c["spread_days"] is not None]
co.sort(key=lambda c: c["spread_days"])
for i, c in enumerate(co):
    a, b = to_year(c["first_release"][:7]), to_year(c["last_release"][:7])
    ax.plot([a, b], [i, i], color=GRID, linewidth=6, solid_capstyle="round", zorder=1)
    ax.scatter(a, i, s=90, color=S1, zorder=3, edgecolor=SURFACE, linewidth=2)
    ax.scatter(b, i, s=90, color=S2, zorder=3, edgecolor=SURFACE, linewidth=2)
    ax.text(b + 0.06, i, f'{c["spread_days"]} d', va="center", fontsize=9.5, color=INK_2)
ax.set_yticks(range(len(co)))
ax.set_yticklabels([f'{c["cve"]}\n{len(c["vendors"])} vendor'
                    f'{"" if len(c["vendors"]) == 1 else "s"}' for c in co],
                   fontsize=9, color=INK_2)
ax.set_xlabel("year", color=INK_2)
year_axis(ax)
style(ax, axis="x")
ax.scatter([], [], s=90, color=S1, label="first fix")
ax.scatter([], [], s=90, color=S2, label="last fix")
# Above the axes: inside it, the legend lands on the 2020 row.
ax.legend(frameon=False, fontsize=9.5, labelcolor=INK_2, ncol=2,
          loc="lower right", bbox_to_anchor=(1.0, 1.0))
ax.set_title("Multi-codebase CVEs: first fix to last", loc="left", fontsize=11,
             color=INK_2)
fig.tight_layout()
save(fig, "16_cve_latency_and_spread")
""")

md(r"""
### 7.3 Vulnerability does not follow deployment

Only 16 of 97 DNSSEC CVEs name a specific mechanism; 69 sit in RFC 4033/4034/4035,
whose exposure is 100% of signed zones by construction. Among the mechanisms that
can be matched, peak share explains nothing.
""")

code(r"""
rows = [r for r in CA["changes"] if r["matchable"] and r["peak_share_pct"] is not None]
fig, axes = plt.subplots(1, 2, figsize=(11, 3.4))
ax = axes[0]
ax.scatter([r["peak_share_pct"] for r in rows], [r["n_cves"] for r in rows], s=110,
           color=S1, zorder=3, edgecolor=SURFACE, linewidth=2)
for r in rows:
    if r["n_cves"] or r["peak_share_pct"] > 60:
        ax.annotate(r["change"], (r["peak_share_pct"], r["n_cves"]), xytext=(7, 5),
                    textcoords="offset points", fontsize=9, color=INK_2)
style(ax, axis="both"); pct(ax, axis="x")
ax.set_xlim(-6, 122)          # room for the RSASHA1 label at 100%
ax.set_xlabel("peak share of signed delegations", color=INK_2)
ax.set_ylabel("CVEs naming the mechanism", color=INK_2)
ax.set_title(f'corr = {CA["correlation_peak_share_vs_cve_count"]}  (n=11)', loc="left",
             fontsize=11, color=INK_2)

ax = axes[1]
stages = collections.Counter(c["stage_when_published"] for r in CA["changes"]
                             for c in r["cves"])
# Every stage is drawn, including the empty ones: "before first use" reading
# zero is the finding, and a category that is simply absent does not show it.
order = ["before first use", "seen, below 1%", "in partial usage", "in common usage"]
vals = [stages.get(o, 0) for o in order]
ax.barh(range(len(order)), vals, height=0.6, color=S1, zorder=3)
for i, v in enumerate(vals):
    ax.text(v + 0.2, i, str(v), va="center", fontsize=10.5,
            color=CRITICAL if v == 0 and i == 0 else INK_2, fontweight="bold")
ax.set_yticks(range(len(order)))
ax.set_yticklabels(order, fontsize=10, color=INK_2)
ax.set_xlim(0, max(vals) * 1.12)
ax.invert_yaxis(); style(ax, axis="x")
ax.set_title("Deployment stage when the CVE was published", loc="left", fontsize=11,
             color=INK_2)
fig.suptitle("No CVE has ever landed before the thing it attacks was in use",
             x=0.005, ha="left", fontsize=13, fontweight="bold", color=INK)
fig.tight_layout(rect=[0, 0, 1, 0.93])
save(fig, "17_cve_vs_adoption")
""")

# ============================================================= closing =======
md(r"""
## 8. What the figures support

**Established.** Shipping a capability does not move deployment. Onset is almost
entirely operator time (fig 1), the three clocks run RFC → code → *years* → zones
(fig 2), and four of four availability releases are followed by exactly zero
change (fig 9).

**Established.** The unit of change is the operator. Every detected jump belongs
to one of two registry operators, and the partner TLD moves in the same month in
20 of 21 cases (fig 12).

**Established.** A validator can coerce a zone, and did once: the NSEC3 iteration
tail collapsed 83% in the month after resolvers capped it, ten months before the
RFC (fig 10).

**Suggested, not established.** That default changes drive adoption. The timing
is right and vendors moved before the rise, not after (fig 8) — but no event
study detects anything (fig 9), and it rests on two observations of one
algorithm.

**Not supported.** "Software updates drive adoption rates" as a general claim.

The decisive test is blocked by coverage: both ECDSA default changes land in
2016, the forward corpus starts 2016-06 and cannot see the before-period, and the
reverse panel that spans the window lags the ecosystem by years.
""")

code(r"""
print("Figures written to", FIGDIR.resolve())
for p in sorted(FIGDIR.glob("*.png")):
    print(f"  {p.name:34} {p.stat().st_size / 1024:6.0f} KB")
""")

NB["cells"] = cells
NB["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}
out = Path("notebooks/dnssec_software_releases.ipynb")
nbf.write(NB, out)
print(f"wrote {out} ({len(cells)} cells)")
