"""One integrated timeline per RFC: the standard, the software, the CVEs, and
what zones actually did -- on a single time axis.

This is the figure the whole project has been circling. Every earlier chart
showed one of these clocks at a time. Here, per RFC:

    upper strip   RFC published; each implementation's first release that could
                  sign / validate / publish it; default changes; validator
                  limits; CVEs touching the mechanism
    lower panel   share of signed zones carrying the value, both corpora, with
                  first sighting, the 1% crossing, and every portfolio jump
                  marked with its operator

Then a verdict per RFC computed from the data (fast / slow / never / forced /
unobservable), which the deck turns into the "why" -- and which the verification
pass is meant to argue with.

Reads data/software/software_support.json, out/analysis/cve_crossref.json,
out/analysis/adoption_measures.json, out/analysis/software_crossref.json,
out/server_run/timeline_monthly.parquet, out/panel_run/timeline_monthly.parquet.
Writes out/analysis/rfc_timelines.json and reporting/charts/rfc/*.png.

    python reporting/rfc_timelines.py [--bare --out reporting/charts/rfc/bare]
"""
from __future__ import annotations

import argparse
import json
import re
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter, MaxNLocator

SURFACE, INK, INK_2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"          # validator / signer / RFC
CRITICAL, WARNING = "#d03b3b", "#eda100"               # CVE / default change

plt.rcParams.update({
    "font.family": ["DejaVu Sans", "sans-serif"], "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "text.color": INK,
    "axes.labelcolor": INK_2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": BASELINE, "axes.linewidth": 0.8, "xtick.labelsize": 10.5,
    "ytick.labelsize": 10.5, "figure.dpi": 120,
})

NAME = {"unbound": "Unbound", "nsd": "NSD", "bind9": "BIND 9", "knot": "Knot DNS",
        "kresd": "Knot Resolver", "opendnssec": "OpenDNSSEC",
        "pdns-auth": "PowerDNS Auth", "pdns-rec": "PowerDNS Rec"}
PANEL = "_pooled-afrinic-arin"

#: What each RFC introduces, where it is visible, and what it relates to.
#: `curve` is (reverse dim, forward dim, values); `jumps` the software_crossref
#: observable key; `cve_labels` the rfc strings cve_crossref assigns.
RFCS = {
    "RFC 5155": dict(title="NSEC3 authenticated denial", published="2008-03",
                     curve=("algorithm_ds", "algorithm_dnskey", ["7"]),
                     curve_note="algorithm 7 (RSASHA1-NSEC3) is a proxy; NSEC3 itself is "
                                "used with 8, 10 and 13 too",
                     forward_alt=("rr_type", ["NSEC3PARAM"]),
                     jumps=None, cve_labels=["RFC 5155"], sw_obs=["nsec3"],
                     related=["RFC 9276"]),
    "RFC 5702": dict(title="RSA/SHA-256 and RSA/SHA-512", published="2009-10",
                     curve=("algorithm_ds", "algorithm_dnskey", ["8", "10"]),
                     jumps="alg 8/10", cve_labels=[], sw_obs=["alg 8/10"],
                     related=["RFC 6605"]),
    "RFC 5933": dict(title="GOST signing and digest", published="2010-07",
                     curve=("algorithm_ds", "algorithm_dnskey", ["12"]),
                     jumps="alg 12", cve_labels=[], sw_obs=["alg 12"],
                     related=["RFC 5702", "RFC 9906"]),
    # cve_crossref buckets ECDSA and EdDSA together as "RFC 6605/8080"; split by
    # what the description names, so the same four CVEs are not counted twice.
    "RFC 6605": dict(title="ECDSA P-256 / P-384", published="2012-04",
                     curve=("algorithm_ds", "algorithm_dnskey", ["13", "14"]),
                     jumps="alg 13/14", cve_labels=["RFC 6605/8080"],
                     cve_filter=r"ECDSA|P-256|P-384|prime256",
                     sw_obs=["alg 13/14", "digest 4"], related=["RFC 5702", "RFC 8080"]),
    # CDS alone, over signed zones. Summing CDS+CDNSKEY double-counts zones that
    # publish both, and rr_type's own _total is every name with any record.
    "RFC 7344": dict(title="CDS / CDNSKEY child signalling", published="2014-09",
                     curve=None, forward_alt=("rr_type", ["CDS"]),
                     jumps="CDS/CDNSKEY", cve_labels=[], sw_obs=["CDS/CDNSKEY"],
                     related=["RFC 8078"]),
    "RFC 8080": dict(title="EdDSA (Ed25519 / Ed448)", published="2017-02",
                     curve=("algorithm_ds", "algorithm_dnskey", ["15", "16"]),
                     jumps="alg 15/16", cve_labels=["RFC 6605/8080"],
                     cve_filter=r"Ed25519|Ed448|EdDSA",
                     sw_obs=["alg 15/16", "alg 15", "alg 16"], related=["RFC 6605"]),
    # Only CVEs from the cap era onward belong to a 2022 guidance RFC; the twelve
    # NSEC3 CVEs from 2009 stay on RFC 5155's slide.
    "RFC 9276": dict(title="NSEC3 parameter guidance (0 iterations)", published="2022-08",
                     curve=None, jumps=None, cve_labels=["RFC 5155"], cve_min="2021-05",
                     cve_note="NSEC3 CVEs since the 2021 cap; counted again on RFC 5155's "
                              "slide. Only CVE-2023-50868 names RFC 9276 itself.",
                     sw_obs=[], related=["RFC 5155"], collapse=True),
    # The resolver half of 5011 leaves no trace; the signer half does -- the
    # REVOKE bit on a DNSKEY (flags 384/385), which the forward corpus carries.
    "RFC 5011": dict(title="Automated trust-anchor rollover", published="2007-09",
                     curve=None, jumps=None, cve_labels=["RFC 5011"],
                     sw_obs=["trust-anchor rollover", "revoked-KSK state"],
                     related=[], revoked=True),
}
RFC_PUB = {"RFC 4509": "2006-05", "RFC 5011": "2007-09", "RFC 5155": "2008-03",
           "RFC 5702": "2009-10", "RFC 5933": "2010-07", "RFC 6605": "2012-04",
           "RFC 7344": "2014-09", "RFC 8078": "2017-03", "RFC 8080": "2017-02",
           "RFC 9276": "2022-08", "RFC 9906": "2025-11"}
OPERATOR = {"se": "Swedish Internet Foundation", "nu": "Swedish Internet Foundation",
            "ch": "SWITCH", "li": "SWITCH"}
BARE = False


def to_year(m: str) -> float:
    return int(m[:4]) + (int(m[5:7]) - 1) / 12


def months_between(a: str, b: str) -> float:
    return ((int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))) / 12.0


def share(df, basis, dim, values, source=None):
    b = df[(df.basis == basis) & (df.dimension == dim)]
    if source is not None:
        b = b[b.source == source]
    den = b[b.value == "_total"].groupby("month").domains_peak.sum().sort_index()
    num = (b[b.value.isin(values)].groupby("month").domains_peak.sum()
           .reindex(den.index, fill_value=0))
    return (num / den * 100).sort_index()


def style(ax, axis="y"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis=axis, color=GRID, linewidth=0.8)
    ax.tick_params(length=0)


def year_axis(ax):
    ax.xaxis.set_major_locator(MaxNLocator(nbins=9, integer=True))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v)}"))


def pack_lanes(marks, span, chars_per_span=96.0):
    """Greedy lane packing so labels close in time never overprint."""
    ypc = (span[1] - span[0]) / chars_per_span
    lane_end, placed = [], []
    for m in sorted(marks, key=lambda x: x["x"]):
        width = len(m["label"]) * ypc + 0.3
        right = m["x"] > span[0] + (span[1] - span[0]) * 0.62
        x0, x1 = (m["x"] - width, m["x"]) if right else (m["x"], m["x"] + width)
        for lane, end in enumerate(lane_end):
            if x0 > end:
                lane_end[lane] = x1
                break
        else:
            lane = len(lane_end)
            lane_end.append(x1)
        placed.append({**m, "lane": lane, "right": right})
    return placed


def assemble(rfc, spec, sup, cves, am, sc, srv, pan):
    ev = {"rfc": rfc, "title": spec["title"], "published": spec["published"],
          "software": [], "defaults": [], "limits": [], "cves": [], "spikes": [],
          "related_rfcs": [{"rfc": r, "published": RFC_PUB[r]} for r in spec["related"]]}

    for r in sup["support"]:
        if r["observable"] in spec["sw_obs"] and r.get("standard_codepoint", True):
            ev["software"].append({
                "implementation": NAME[r["implementation"]], "key": r["implementation"],
                "capability": r["capability"], "version": r["first_release"],
                "released": r["released"], "pre_rfc": bool(r.get("pre_rfc")),
                "evidence_url": r.get("evidence_url", "")})
    fam = {"RFC 5702": "RSASHA256", "RFC 6605": "ECDSA", "RFC 5155": "NSEC3"}.get(rfc)
    for r in sup["default_changes"]:
        if fam and fam in r["what"]:
            ev["defaults"].append({"implementation": NAME[r["implementation"]],
                                   "version": r["first_release"], "released": r["released"],
                                   "what": r["what"], "opt_in": bool(r.get("opt_in"))})
    if rfc in ("RFC 5155", "RFC 9276"):
        for r in sup["validator_limits"]:
            if "NSEC3" in r["what"]:
                ev["limits"].append({"implementation": NAME[r["implementation"]],
                                     "version": r["first_release"],
                                     "released": r["released"], "what": r["what"]})
    flt = re.compile(spec["cve_filter"], re.I) if spec.get("cve_filter") else None
    for c in cves["cves"]:
        if c["scope"] != "dnssec" or c["rfc"] not in spec["cve_labels"] or not c["published"]:
            continue
        if flt and not flt.search(c["description"] or ""):
            continue
        if spec.get("cve_min") and c["published"][:7] < spec["cve_min"]:
            continue
        if True:
            ev["cves"].append({"cve": c["cve"], "published": c["published"],
                               "cvss": c["cvss"], "mechanism": c["mechanism"],
                               "description": (c["description"] or "")[:140]})
    if spec.get("jumps") == "CDS/CDNSKEY":
        # software_crossref sums CDS+CDNSKEY names, which counts a zone publishing
        # both twice (the normal case). Use the CDS-only spikes instead.
        for j in json.loads(Path("out/analysis/cds_only_spikes.json").read_text("utf-8")):
            ev["spikes"].append({**j, "operator": OPERATOR.get(j["source"], j["source"])})
    elif spec.get("jumps"):
        for j in sc["portfolio_jumps"].get(spec["jumps"], []):
            ev["spikes"].append({**j, "operator": OPERATOR.get(j["source"], j["source"])})

    # Adoption measures: the codepoints this RFC introduces.
    vals = spec["curve"][2] if spec.get("curve") else []
    rows = [a for a in am["algorithms"] + am["digest_types"]
            if a["rfc"] == rfc and str(a["value"]) in vals]
    ev["adoption"] = [{"change": a["change"], "first_seen": a["t_first_date"],
                       "t_1pct": a["t_1pct_date"], "t_10pct": a["t_10pct_date"],
                       "peak_share_pct": a.get("peak_share_pct"),
                       "current_share_pct": a.get("current_share_pct"),
                       "onset_years": a.get("onset_years")} for a in rows]

    # Curves for the figure.
    ev["_curves"] = {}
    if spec.get("curve"):
        rdim, fdim, values = spec["curve"]
        if rdim:
            ev["_curves"]["reverse"] = share(pan, "reverse", rdim, values, source=PANEL)
        if fdim:
            ev["_curves"]["forward"] = share(srv, "zonefile", fdim, values)
    if spec.get("forward_alt"):
        # NSEC3PARAM sits once at the apex, so it counts zones -- but its own
        # rr_type "_total" is every name with any record. The denominator has to
        # be signed zones (DNSKEY _total) or the share reads 19% instead of ~98%.
        dim, values = spec["forward_alt"]
        f = srv[srv.basis == "zonefile"]
        num = (f[(f.dimension == dim) & (f.value.isin(values))]
               .groupby("month").domains_peak.sum())
        den = (f[(f.dimension == "algorithm_dnskey") & (f.value == "_total")]
               .groupby("month").domains_peak.sum().sort_index())
        ev["_curves"]["forward"] = (num.reindex(den.index, fill_value=0) / den * 100)
        ev["curve_note"] = "forward: NSEC3PARAM at the apex over signed zones"
    if spec.get("collapse"):
        col = sc["nsec3_iteration_collapse"]
        ev["_collapse"] = pd.Series(col["high_iteration_names_by_month"]).sort_index()
        ev["collapse"] = col["largest_single_month_fall"]
        # The moved population sat at exactly 100 -- BIND's pre-9.7.0 default --
        # which is below Unbound's 150 cap and at PowerDNS's 100. Neither cap
        # refused it, so refusal cannot be what the numbers show.
        f = srv[(srv.basis == "zonefile") & (srv.dimension == "nsec3_iterations")].copy()
        f["iv"] = pd.to_numeric(f.value, errors="coerce")
        ex = f[f.iv == 100].groupby("month").domains_peak.sum()
        gt = f[f.iv > 100].groupby("month").domains_peak.sum()
        m0, m1 = "2021-09", "2021-10"
        ev["iterations_exactly_100"] = {m0: int(ex.get(m0, 0)), m1: int(ex.get(m1, 0))}
        ev["iterations_over_100"] = {m0: int(gt.get(m0, 0)), m1: int(gt.get(m1, 0))}
    if spec.get("revoked"):
        f = srv[(srv.basis == "zonefile") & (srv.dimension == "dnskey_flags")]
        rv = f[f.value.astype(str).isin(["384", "385"])].groupby("month").domains_peak.sum()
        ev["_revoked"] = rv.sort_index()
        ev["revoked"] = {"months": int(len(rv)), "first": str(rv.index.min()),
                         "min": int(rv.min()), "median": int(rv.median()),
                         "max": int(rv.max()), "last": int(rv.iloc[-1])}
    if spec.get("cve_note"):
        ev["cve_note"] = spec["cve_note"]
    # Was the predecessor still spreading when this RFC came out?
    # Only the stated predecessor: rfc_overlap pairs every earlier RFC with
    # every later one, and RFC 8080's row against RFC 5702 (at 100%) says nothing.
    for o in sc.get("rfc_overlap", []):
        if o["successor"] == rfc and o["predecessor"] in spec["related"]:
            ev.setdefault("successor_overlap", []).append(
                {"predecessor": o["predecessor"],
                 "predecessor_share_at_publication": o["predecessor_share_at_publication"],
                 "predecessor_peak_share": o["predecessor_peak_share"],
                 "fraction_of_peak_reached": o["fraction_of_peak_reached"]})

    # Lags the verdict rests on. software_crossref.json already computed these
    # as a minimum over BOTH corpora, which is what makes RFC 8080 read 2019-01
    # (.se, forward) rather than the retracted reverse-only 2022-09. Use it.
    dec = {r["observable"]: r for r in sc["onset_decomposition"]}
    obs_key = spec.get("jumps")
    if obs_key in dec:
        r = dec[obs_key]
        ev["lags"] = {
            "first_signer_release": r.get("first_signer_released"),
            "first_signer": r.get("first_signer"),
            "first_validator_release": r.get("first_validator_released"),
            "first_validator": r.get("first_validator"),
            "first_zone_seen": r.get("first_zone_seen"),
            "first_seen_basis": r.get("first_seen_basis"),
            "code_lag_years": r.get("code_lag_years"),
            "deployment_lag_years": r.get("deployment_lag_years"),
            "onset_years": r.get("onset_years"),
            "source": "out/analysis/software_crossref.json onset_decomposition",
        }
        for a in ev["adoption"]:
            a["first_seen_reverse_panel"] = a["first_seen"]
            a["first_seen"] = r.get("first_zone_seen")
        return ev
    signers = [s for s in ev["software"] if s["capability"] in ("sign", "publish")]
    validators = [s for s in ev["software"] if s["capability"] == "validate"]
    fs = min(signers, key=lambda x: x["released"], default=None)
    fv = min(validators, key=lambda x: x["released"], default=None)
    first_sign = fs["released"] if fs else None
    first_val = fv["released"] if fv else None
    seen = min((a["first_seen"] for a in ev["adoption"] if a["first_seen"]), default=None)
    ev["lags"] = {
        "first_signer_release": first_sign,
        "first_signer": f'{fs["key"]} {fs["version"]}' if fs else None,
        "first_validator_release": first_val,
        "first_validator": f'{fv["key"]} {fv["version"]}' if fv else None,
        "first_zone_seen": seen,
        "code_lag_years": round(months_between(spec["published"], first_sign[:7]), 2)
        if first_sign else None,
        "deployment_lag_years": round(months_between(first_sign[:7], seen), 2)
        if first_sign and seen else None,
        "onset_years": round(months_between(spec["published"], seen), 2) if seen else None,
    }
    return ev


def verdict(ev):
    """One label per RFC, from a stated rule.

        fast      first zone within a year of the RFC and 10% of signed
                  delegations within four
        slow      reached 10%, but later than that
        never     under 1% of signed zones in every corpus today
        stalled   in use, never past 10%
        vendor-triggered   zones moved after vendor caps and before the RFC
        partly observable  only one half of the RFC leaves a trace in zone data

    The deck turns these into prose; the verification pass argues with both.
    """
    if ev.get("collapse"):
        return "vendor-triggered", (
            "names at >= 100 iterations fell 83% in 2021-10, two months after the "
            "resolver caps shipped and ten months before the RFC. The moved names sat at "
            "exactly 100, below both caps, so what moved them -- refusal, guidance or an "
            "operator re-sign -- the data cannot say; the ordering it can")
    if ev.get("revoked"):
        r = ev["revoked"]
        return "partly observable", (
            f"the resolver half leaves no trace in any zone; the REVOKE bit RFC 5011 "
            f"defines is on {r['min']}-{r['max']} forward zones every month since "
            f"{r['first']} (median {r['median']})")
    if not ev["adoption"] and not ev.get("_curves"):
        return "unobservable", "nothing a zone publishes changes"
    onset = ev["lags"]["onset_years"]
    fwd = ev["_curves"].get("forward")
    rev = ev["_curves"].get("reverse")
    now = max((float(c.iloc[-1]) for c in (fwd, rev) if c is not None and len(c)),
              default=0.0)
    peak = max((float(c.max()) for c in (fwd, rev) if c is not None and len(c)),
               default=0.0)
    if ev["rfc"] == "RFC 7344":
        return "niche by design", (
            f"{now:.1f}% of signed forward zones publish a CDS record; only a zone whose "
            "parent will act on it has reason to, and where a registry does the effect is "
            "six figures")
    if now < 1.0:
        extra = ""
        if peak >= 1.0:
            extra = f"; a {peak:.1f}% spike was one operator and was withdrawn"
        if ev["rfc"] == "RFC 5933":
            extra += ("; neither corpus covers the Russian namespace it was written for, "
                      "so 0.00% is partly sample construction")
        return "never", (f"{now:.2f}% of signed zones today, years after every major "
                         f"implementation shipped it{extra}")
    t10 = min((a["t_10pct"] for a in ev["adoption"] if a.get("t_10pct")), default=None)
    years_to_10 = months_between(ev["published"], t10) if t10 else None
    if onset is not None and onset <= 1.0 and years_to_10 is not None and years_to_10 <= 4:
        return "fast", (f"first zone {onset:.1f} y after the RFC and 10% of signed "
                        f"delegations {years_to_10:.1f} y after it")
    if years_to_10 is not None or peak >= 10:
        return "slow", (f"first zone {onset:.1f} y after the RFC and 10% of signed "
                        f"delegations {years_to_10:.1f} y after it" if years_to_10 else
                        "reached common usage years after the code existed")
    return "stalled", f"in use at {now:.1f}%, never past 10%"


def draw(rfc, ev, out: Path):
    spec = RFCS[rfc]
    curves = ev["_curves"]
    has_lower = bool(curves) or "_collapse" in ev or "_revoked" in ev
    fig, axes = plt.subplots(2 if has_lower else 1, 1,
                             figsize=(12.5, 5.0 if has_lower else 3.2), sharex=True,
                             gridspec_kw={"height_ratios": [0.95, 1], "hspace": 0.05}
                             if has_lower else None)
    top, ax = (axes if has_lower else (axes, None))

    # ---- time span: from a year before the earliest event to the last data --- #
    xs = [to_year(ev["published"])]
    xs += [to_year(s["released"][:7]) for s in ev["software"]]
    xs += [to_year(c["published"][:7]) for c in ev["cves"]]
    xs += [to_year(r["published"]) for r in ev["related_rfcs"]]
    for c in curves.values():
        xs += [to_year(m) for m in c.index[[0, -1]]]
    if "_collapse" in ev:
        xs += [to_year(m) for m in ev["_collapse"].index[[0, -1]]]
    if "_revoked" in ev:
        xs += [to_year(m) for m in ev["_revoked"].index[[0, -1]]]
    span = (min(xs) - 0.8, max(xs) + 0.6)

    # ---- upper strip ---------------------------------------------------------- #
    marks = [{"x": to_year(ev["published"]), "label": f"{rfc} published",
              "color": S3, "marker": "o", "size": 90}]
    for r in ev["related_rfcs"]:
        marks.append({"x": to_year(r["published"]), "label": f'{r["rfc"]}',
                      "color": S3, "marker": "o", "size": 40, "muted": True})
    for s in ev["software"]:
        colour = S1 if s["capability"] == "validate" else S2
        cap = {"validate": "validates", "sign": "signs", "publish": "publishes",
               "rrtype": "record type"}.get(s["capability"], s["capability"])
        marks.append({"x": to_year(s["released"][:7]),
                      "label": f'{s["implementation"]} {s["version"]} {cap}',
                      "color": colour, "marker": "o", "size": 55})
    for d in ev["defaults"]:
        marks.append({"x": to_year(d["released"][:7]),
                      "label": f'{d["implementation"]} {d["version"]} default'
                               + (" (opt-in)" if d["opt_in"] else ""),
                      "color": WARNING, "marker": "D", "size": 60})
    for l in ev["limits"]:
        marks.append({"x": to_year(l["released"][:7]),
                      "label": f'{l["implementation"]} {l["version"]} limit',
                      "color": CRITICAL, "marker": "s", "size": 55})
    for c in ev["cves"]:
        sev = c["cvss"] or 0
        marks.append({"x": to_year(c["published"][:7]),
                      "label": f'{c["cve"]}' + (f' ({sev:.1f})' if sev else ""),
                      "color": CRITICAL, "marker": "^", "size": 35 + sev * 6})
    placed = pack_lanes(marks, span, chars_per_span=108.0)
    n_lanes = max((m["lane"] for m in placed), default=0) + 1
    for m in placed:
        y = 0.10 + 0.105 * m["lane"]
        top.plot([m["x"], m["x"]], [0, y], color=GRID, linewidth=1, zorder=1)
        if ax is not None:
            ax.axvline(m["x"], color=GRID, linewidth=0.8, zorder=0)
        top.scatter(m["x"], y, s=m["size"], color=m["color"], marker=m["marker"],
                    zorder=4, edgecolor=SURFACE, linewidth=1.3,
                    alpha=0.45 if m.get("muted") else 1.0)
        top.text(m["x"] + (-0.18 if m["right"] else 0.18), y, m["label"],
                 fontsize=8.6, color=MUTED if m.get("muted") else INK_2, va="center",
                 ha="right" if m["right"] else "left")
    top.set_ylim(0, 0.10 + 0.105 * max(n_lanes, 3))
    top.set_yticks([])
    for side in ("top", "right", "left", "bottom"):
        top.spines[side].set_visible(False)
    top.tick_params(length=0)
    top.set_xlim(*span)

    # ---- lower panel ---------------------------------------------------------- #
    if ax is not None:
        if "_revoked" in ev:
            r = ev["_revoked"]
            xr = [to_year(m) for m in r.index]
            ax.fill_between(xr, r.values, color=S2, alpha=0.12, zorder=1)
            ax.plot(xr, r.values, color=S2, linewidth=2.0, zorder=3,
                    label="forward zones publishing a REVOKED key (flags 384/385)")
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v):,}"))
            ax.set_ylabel("zones", color=INK_2)
        elif "_collapse" in ev:
            s = ev["_collapse"]
            xc = [to_year(m) for m in s.index]
            ax.fill_between(xc, s.values, color=S1, alpha=0.12, zorder=1)
            ax.plot(xc, s.values, color=S1, linewidth=2.2, zorder=3,
                    label="NSEC3 owner names at >= 100 iterations")
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v):,}"))
            ax.set_ylabel("names", color=INK_2)
            w = ev["collapse"]
            ax.annotate(f'{w["month"]}: {w["before"]:,} -> {w["after"]:,}',
                        (to_year(w["month"]), w["after"]), xytext=(-150, 70),
                        textcoords="offset points", fontsize=10, color=INK,
                        fontweight="bold",
                        arrowprops=dict(arrowstyle="->", color=INK_2, linewidth=1.1))
        else:
            for key, colour, lbl in (("forward", S2, "forward TLDs (OpenINTEL)"),
                                     ("reverse", S1, "reverse, strict RIR panel")):
                c = curves.get(key)
                if c is None or not len(c):
                    continue
                xc = [to_year(m) for m in c.index]
                ax.plot(xc, c.values, color=colour, linewidth=2.2, zorder=3, label=lbl)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}%"))
            ax.set_ylabel("share of signed zones", color=INK_2)
            # Dashed markers only; the dates themselves go in the slide's evidence
            # line. Rotated labels here landed on the legend.
            seen_marks = set()
            for a in ev["adoption"]:
                for key in ("first_seen", "t_1pct", "t_10pct"):
                    if a.get(key) and a[key] not in seen_marks:
                        seen_marks.add(a[key])
                        ax.axvline(to_year(a[key]), color=MUTED, linewidth=1,
                                   linestyle=(0, (3, 3)), zorder=2)
            if not BARE:
                stages = [(a[k], lbl) for a in ev["adoption"]
                          for k, lbl in (("first_seen", "first seen"), ("t_1pct", "1%"),
                                         ("t_10pct", "10%")) if a.get(k)]
                stages = sorted(set(stages))
                if stages:
                    ax.text(0.995, 0.04, "   ".join(f"{l} {d}" for d, l in stages),
                            transform=ax.transAxes, fontsize=8.5, color=MUTED,
                            ha="right", va="bottom")
            for j in ev["spikes"]:
                x = to_year(j["month"])
                fwd = curves.get("forward")
                if fwd is None or j["month"] not in fwd.index:
                    continue
                ax.scatter(x, fwd[j["month"]], s=80, color=CRITICAL, zorder=5,
                           edgecolor=SURFACE, linewidth=1.5)
            if ev["spikes"]:
                biggest = max(ev["spikes"], key=lambda j: j["delta_zones"])
                fwd = curves.get("forward")
                if fwd is not None and biggest["month"] in fwd.index:
                    ax.annotate(f'+{biggest["delta_zones"]:,} zones in one month, '
                                f'.{biggest["source"]} ({biggest["operator"]})',
                                (to_year(biggest["month"]), fwd[biggest["month"]]),
                                xytext=(-190, 30), textcoords="offset points",
                                fontsize=9.5, color=INK, fontweight="bold",
                                arrowprops=dict(arrowstyle="->", color=INK_2,
                                                linewidth=1.1))
        style(ax)
        ax.set_ylim(bottom=0)
        ax.set_xlabel("year", color=INK_2)
        year_axis(ax)
        if not BARE:
            ax.legend(frameon=False, fontsize=9.5, labelcolor=INK_2, loc="upper left")
    else:
        top.set_xlabel("year", color=INK_2)
        year_axis(top)
        top.spines["bottom"].set_visible(True)

    v, why = verdict(ev)
    if not BARE:
        top.set_title(f"{rfc}  —  {ev['title']}", loc="left", color=INK,
                      fontweight="bold", pad=62)
        top.text(0, 1.115, textwrap.fill(f"{v.upper()}: {why}", 120),
                 transform=top.transAxes, color=INK_2, fontsize=10, va="bottom")
        for colour, mk, lbl in ((S3, "o", "RFC"), (S2, "o", "signer release"),
                                (S1, "o", "validator release"), (WARNING, "D", "default"),
                                (CRITICAL, "s", "validator limit"), (CRITICAL, "^", "CVE")):
            top.scatter([], [], s=55, color=colour, marker=mk, label=lbl)
        top.legend(frameon=False, fontsize=9, labelcolor=INK_2, ncol=6, loc="lower left",
                   bbox_to_anchor=(0, 1.0))
    p = out / f"{rfc.replace(' ', '_').lower()}.png"
    fig.savefig(p, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("reporting/charts/rfc"))
    ap.add_argument("--bare", action="store_true")
    args = ap.parse_args()
    global BARE
    BARE = args.bare
    args.out.mkdir(parents=True, exist_ok=True)

    sup = json.loads(Path("data/software/software_support.json").read_text("utf-8"))
    cves = json.loads(Path("out/analysis/cve_crossref.json").read_text("utf-8"))
    am = json.loads(Path("out/analysis/adoption_measures.json").read_text("utf-8"))
    sc = json.loads(Path("out/analysis/software_crossref.json").read_text("utf-8"))
    srv = pd.read_parquet("out/server_run/timeline_monthly.parquet")
    pan = pd.read_parquet("out/panel_run/timeline_monthly.parquet")

    results = {}
    for rfc, spec in RFCS.items():
        ev = assemble(rfc, spec, sup, cves, am, sc, srv, pan)
        p = draw(rfc, ev, args.out)
        v, why = verdict(ev)
        ev["verdict"], ev["verdict_basis"] = v, why
        fwd = ev["_curves"].get("forward")
        rev = ev["_curves"].get("reverse")
        ev["curve_summary"] = {
            "forward_peak_pct": round(float(fwd.max()), 2) if fwd is not None and len(fwd) else None,
            "forward_last_pct": round(float(fwd.iloc[-1]), 2) if fwd is not None and len(fwd) else None,
            "reverse_peak_pct": round(float(rev.max()), 2) if rev is not None and len(rev) else None,
            "reverse_last_pct": round(float(rev.iloc[-1]), 2) if rev is not None and len(rev) else None,
        }
        ev.pop("_curves", None); ev.pop("_collapse", None)
        results[rfc] = ev
        print(f"  {rfc}: {v:12} {len(ev['software'])} sw, {len(ev['cves'])} CVEs, "
              f"{len(ev['spikes'])} spikes  -> {p.name}")
    if not BARE:
        Path("out/analysis/rfc_timelines.json").write_text(
            json.dumps(results, indent=2, default=str) + "\n", encoding="utf-8")
        print("  wrote out/analysis/rfc_timelines.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
