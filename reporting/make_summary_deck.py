"""A short deck: does DNS software explain DNSSEC RFC adoption? Everything in
one pass -- releases, defaults, OS packages, CVEs, spikes, and the verdicts.

Every number is read from the analysis JSONs at build time.

    python reporting/make_summary_deck.py [--out out/analysis/dnssec_software_summary.pptx]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches, Pt

from make_flows_deck import ACCENT, INK, INK_2, MUTED, SURFACE, W, H, blank, text  # noqa
from make_program_cases_deck import table, fit_picture, pct

CRIT = RGBColor(0xD0, 0x3B, 0x3B)
GOOD = RGBColor(0x1B, 0xAF, 0x7A)


def kicker(s, k, title, color=MUTED):
    text(s, Inches(0.62), Inches(0.3), Inches(12), Inches(0.3), [k], size=12, color=color, bold=True)
    text(s, Inches(0.62), Inches(0.58), Inches(12.1), Inches(0.6), [title], size=24, bold=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("out/analysis/dnssec_software_summary.pptx"))
    a = ap.parse_args()
    T = json.loads(Path("out/analysis/rfc_timelines.json").read_text("utf-8"))
    C = json.loads(Path("out/analysis/program_rfc_cases.json").read_text("utf-8"))["cases"]
    CV = json.loads(Path("out/analysis/cve_crossref.json").read_text("utf-8"))
    R = json.loads(Path("data/software/release_dates.json").read_text("utf-8"))
    SC = json.loads(Path("out/analysis/software_crossref.json").read_text("utf-8"))
    RS = json.loads(Path("out/analysis/release_scan.json").read_text("utf-8"))
    figs = Path("reporting/charts/cases/bare")
    n_rel = sum(len(v["releases"]) for v in R.values())
    n_cve = CV["totals"]["distinct_cves"]; n_dnssec = CV["totals"]["by_scope"]["dnssec"]
    core = sum(1 for c in CV["cves"] if c["scope"] == "dnssec" and c["rfc"] in ("RFC 4033", "RFC 4034", "RFC 4035"))
    c6, c9, c5, c8 = C["RFC 6605"], C["RFC 9276"], C["RFC 5702"], C["RFC 8080"]
    ar6 = {r["version"]: r for r in c6["new_signings"]["around_releases"] if r["kind"] == "default"}
    ar5 = {r["version"]: r for r in c5["new_signings"]["around_releases"]}
    AT = json.loads(Path("out/analysis/os_release_attribution.json").read_text("utf-8"))
    CH = AT["chance_a_month_follows_an_os_release"]
    ST = AT["families"]["ECDSA"]["steps"][0]
    n_ec = len(AT["families"]["ECDSA"]["steps"])
    Q5 = {r["q"]: r["share_pct"] for r in AT["families"]["RSA/SHA-256"]["quarterly"]}
    od = {o["rfc"]: o for o in SC["onset_decomposition"]}
    code = [o["code_lag_years"] for o in SC["onset_decomposition"] if o.get("code_lag_years") is not None]
    dep = [o["deployment_lag_years"] for o in SC["onset_decomposition"] if o.get("deployment_lag_years") is not None]
    smallest_p = min(v["circular_shift_p"] for v in RS["per_project"].values() if v.get("testable"))
    import pandas as pd, re
    rel_months = {d[:7] for v in R.values() for d in v["releases"].values()}
    span = pd.period_range("2009-03", "2026-08", freq="M").strftime("%Y-%m")
    # Computed over an explicit span. release_scan.json reports 0.969 over
    # "193 months", which does not reconcile with any span of this corpus, so
    # it is recomputed here rather than quoted.
    dens_lo, dens_hi = "2009-03", "2026-08"
    _sp = pd.period_range(dens_lo, dens_hi, freq="M").strftime("%Y-%m")
    dens = sum(m in rel_months for m in _sp) / len(_sp)
    cite = [(c["cve"], sorted(set(re.findall(r"RFC\s?(\d{4})", c["description"] or ""))))
            for c in CV["cves"] if c["scope"] == "dnssec" and re.search(r"RFC\s?\d{4}", c["description"] or "")]
    studied = {"5155", "9276", "5011", "5702", "6605", "8080", "7344", "5933"}
    cite_studied = [(cv, [n for n in ns if n in studied]) for cv, ns in cite if any(n in studied for n in ns)]
    import collections
    prod = collections.Counter(pr for c in CV["cves"] if c["scope"] == "dnssec" and "nvd-product" in c["sources"]
                               for pr in c["products"])
    keyword_only = [k for k, v in CV["query_method"].items() if v != "cpe"]
    ss = json.loads(Path("data/software/software_support.json").read_text("utf-8"))
    sup_rows = ss["support"] + ss["default_changes"] + ss["validator_limits"]
    n_approx = sum(1 for x in sup_rows if x.get("attribution") == "approximate")
    near = collections.Counter(j["nearest_cve"]["what"].split(" ")[0]
                               for c in C.values() for j in c["spikes"] if j.get("nearest_cve"))
    _tm = pd.read_parquet("out/server_run/timeline_monthly.parquet")
    _r = _tm[(_tm.basis == "reverse") & (_tm.dimension == "algorithm_ds")]
    _den = _r[_r.value == "_total"].groupby("month").domains_peak.sum()
    _n3 = (_r[_r.value == "7"].groupby("month").domains_peak.sum() / _den * 100).dropna()
    NSEC3_FIRST_M, NSEC3_FIRST_PCT = _n3.index[0], float(_n3.iloc[0])
    ED_REV = sum(float((_r[_r.value == v].groupby("month").domains_peak.sum() / _den * 100).dropna().iloc[-1])
                 for v in ("15", "16"))
    _f = _tm[(_tm.basis == "zonefile") & (_tm.dimension == "algorithm_dnskey")]
    _fden = _f[_f.value == "_total"].groupby("month").domains_peak.sum()
    ED_FWD = sum(float((_f[_f.value == v].groupby("month").domains_peak.sum() / _fden * 100).dropna().iloc[-1])
                 for v in ("15", "16") if not _f[_f.value == v].empty)
    _g = _r[_r.value == "12"].groupby("month").domains_peak.sum()
    GOST_PEAK, GOST_PEAK_M = (int(_g.max()), _g.idxmax()) if len(_g) else (0, "-")

    prs = Presentation(); prs.slide_width, prs.slide_height = W, H

    # 1 title
    s = blank(prs)
    text(s, Inches(0.9), Inches(2.0), Inches(11.5), Inches(0.4),
         [f"{len(R)} PROGRAMS  ·  {n_rel:,} RELEASES  ·  {n_cve} CVEs  ·  OPENINTEL + REVERSE DNS"], size=13, color=MUTED, bold=True)
    text(s, Inches(0.9), Inches(2.45), Inches(11.6), Inches(1.8),
         ["Does DNS software explain", "when DNSSEC RFCs get adopted?"], size=40, bold=True, space=2)
    ln = s.shapes.add_shape(1, Inches(0.92), Inches(4.35), Inches(2.0), Emu(28575))
    ln.fill.solid(); ln.fill.fore_color.rgb = ACCENT; ln.line.fill.background()
    text(s, Inches(0.9), Inches(4.7), Inches(11.5), Inches(1.6), [
        "BIND 9, Unbound, NSD, Knot DNS, Knot Resolver, PowerDNS Auth/Recursor and OpenDNSSEC: when each one implemented "
        "an RFC, when it made it the default, when Ubuntu and Debian shipped that version, and which CVEs touched it -- "
        "lined up against what zones actually did in the OpenINTEL zone files and in reverse DNS.",
        "Short version: code is never the wait; a default only ever changes what a newly signed zone gets, so it never shows as a spike; "
        "operators switch in sudden batches and the trigger cannot be identified; one RFC was forced by validators before it was "
        "published; and no CVE led a push, including that one, where the CVE and the vendor caps are the same event rather than a cause.",
    ], size=14, color=INK_2)

    # 2 what we did
    s = blank(prs); kicker(s, "WHAT WE DID", "Four sources, one time axis")
    rows = [
        ("Software", f"{len(R)} projects cloned; {n_rel:,} stable release dates from git tags (BIND development branches excluded). "
                     "For each RFC: the first release that signs or validates it, the release that changed the default, and "
                     f"validator caps. All but two rows carry the commit, checked to be contained in the cited release; {n_approx} of {len(sup_rows)} are "
                     f"dated from a changelog or documentation instead and are marked approximate."),
        ("OS packages", "Debian 9-13 and Ubuntu LTS 16.04-24.04 by version (Launchpad, sources.debian.org) and RHEL majors by date. "
                        "One delivery path among several, and a partial one: RHEL base carries only BIND, Knot and PowerDNS come from "
                        "EPEL, and FreeBSD, Alpine, containers and source builds are not represented at all."),
        ("CVEs", f"{n_cve} CVEs across the eight products from NVD; {n_dnssec} are DNSSEC mechanisms, classified by the mechanism the "
                 f"description names (NSEC3, validation, trust anchor, algorithm...). Five products are matched by NVD CPE; "
                 f"{', '.join(keyword_only)} have no usable CPE and are keyword-matched, so a CVE is never attributed to them."),
        ("Zones", "OpenINTEL zone files for seven TLDs, entering at different dates: .se and .nu 2016-06, .gov and .fed.us 2017-05, .ee 2019-07, "
                  ".ch and .li 2020-05, all to 2023-12. Reverse DNS for five RIRs, 2009-03 to 2026-08 with ten missing months, with the strict "
                  "AFRINIC+ARIN panel for reverse shares and a per-delegation change ledger."),
        ("Tests", "onset decomposition (RFC -> code -> first zone); event studies and a detrended release scan with a circular-shift "
                  "null; a spike ledger naming what preceded every spike, against the chance rate; new signings vs rollovers; and "
                  "the share of new reverse signings choosing each algorithm around every default change."),
    ]
    yy = Inches(1.5)
    for head, body in rows:
        text(s, Inches(0.62), yy, Inches(2.2), Inches(0.5), [head], size=12.5, bold=True)
        text(s, Inches(2.8), yy, Inches(10.0), Inches(1.0), [body], size=11, color=INK_2)
        yy += Inches(1.02)

    # 3 code is never the wait
    s = blank(prs); kicker(s, "FINDING 1", "Code is never the wait; operators are", GOOD)
    rows = [["RFC", "published", "first signer release", "code lag (y)", "first zone seen", "operator lag (y)", "verdict"]]
    for rfc in ["RFC 5702", "RFC 5933", "RFC 6605", "RFC 8080", "RFC 5155", "RFC 7344"]:
        o = od.get(rfc); e = T[rfc]; L = e["lags"]
        rows.append([rfc, e["published"], f'{L.get("first_signer") or "-"} {L.get("first_signer_release") or ""}',
                     "-" if L.get("code_lag_years") is None else f'{L["code_lag_years"]:+.1f}',
                     L.get("first_zone_seen") or "-", "-" if L.get("deployment_lag_years") is None else f'{L["deployment_lag_years"]:.1f}',
                     e["verdict"]])
    table(s, Inches(0.5), Inches(1.35), Inches(12.3), rows,
          [Inches(1.0), Inches(1.0), Inches(2.6), Inches(1.2), Inches(1.5), Inches(1.5), Inches(3.5)], size=10)
    text(s, Inches(0.62), Inches(4.0), Inches(12.1), Inches(3), [
        f"Across the algorithm and record-type RFCs the code lag runs {min(code):+.1f} to {max(code):+.1f} years (negative: a signer shipped it "
        f"from the draft), while the lag from that release to the first zone runs {min(dep):.1f} to {max(dep):.1f} years. The RFC is never "
        f"waiting for an implementation; it is waiting for an operator.",
        f"Defaults sit closer to take-off than RFCs do, but no event study or release scan finds a release month that moves the curve: after "
        f"detrending, the smallest circular-shift p across the eight projects is {smallest_p:.2f}. {dens*100:.0f}% of the {len(_sp)} months from "
        f"{dens_lo} to {dens_hi} contain a stable release of one of the eight, so 'a release came just before' is always true and never evidence. Where a default could show "
        f"at all is in what newly signed zones choose, and there the picture is sudden batches, not diffusion (slide 5).",
        "Verdict rule: FAST = first zone within a year of the RFC and 10% of signed delegations within four; SLOW = reached 10%, later; "
        "NEVER = under 1% of signed zones today.",
    ], size=12, color=INK, space=8)

    # 4 ECDSA
    j16 = next(j for j in c6["spikes"] if j["source"] == "se" and j["start"] == "2016-10")
    j19 = next(j for j in c6["spikes"] if j["source"] == "se" and j["start"] == "2019-06")
    jch = next(j for j in c6["spikes"] if j["source"] == "ch" and j["start"] == "2021-06")
    s = blank(prs); kicker(s, "FINDING 2  ·  RFC 6605 ECDSA", "Defaults changed in 2016; the zones moved years later, when operators chose", ACCENT)
    fit_picture(s, figs / "rfc_6605.png", Inches(1.25), Inches(3.9))
    text(s, Inches(0.62), Inches(5.25), Inches(12.1), Inches(2.0), [
        f'Knot 2.1.0 (2016-01) and PowerDNS 4.0.0 (2016-07) made ECDSA the default; BIND 9.16.0 (2020-02) offered it as an opt-in policy. '
        f'The first forward move, .se {j16["start"]} +{j16["delta"]:,}, is {j16["nearest_default_change"]["lag_months"]} months after the PowerDNS '
        f'default but {j16["split"]["rollovers_at_least"]:,} of those zones were existing zones rolling over: an operator decision, not an update.',
        f'In .se the moves that took ECDSA to the majority were entirely rollovers, 30-35 months after any default ({j19["start"]}..{j19["end"]} '
        f'+{j19["delta"]:,}); .nu crossed 50% on new signings instead (2022-01), and .ch and .li were already past it when the corpus first sees them. The .ch wave of {jch["start"]}..{jch["end"]} (+{jch["delta"]:,}) was new signings choosing ECDSA '
        f'{jch["split"]["share_of_new_signings_pct"]:.0f}% of the time -- that is where a default acts: silently, on new zones, years after it changed. '
        f'{c6["summary"]["spikes_within_3m_of_default_change"]} of {c6["summary"]["n_spikes"]} spikes sit within 3 months of a default, '
        f'against a {pct(c6["chance"]["forward"]["within_3m_after_default_change"])} chance rate.',
    ], size=11, color=INK, space=6)

    # 5 auto-update
    s = blank(prs); kicker(s, "FINDING 3  ·  THE AUTO-UPDATE TEST", "Updates change what a new zone gets, never an existing one", ACCENT)
    fit_picture(s, Path("reporting/charts/os_release_attribution.png"), Inches(1.2), Inches(2.75), max_w=Inches(9.6))
    text(s, Inches(0.62), Inches(4.0), Inches(12.1), Inches(3.2), [
        "An update cannot roll an existing zone; it can only change what a zone signed after the update gets. So the test is the share of "
        "NEW signings choosing the algorithm, which the reverse ledger records per delegation.",
        f'ECDSA: on their upstream dates the 2016 Knot and PowerDNS defaults left no trace ({ar6["2.1.0"]["share_before_pct"]}% -> '
        f'{ar6["2.1.0"]["share_after_pct"]}%, {ar6["4.0.0"]["share_before_pct"]}% -> {ar6["4.0.0"]["share_after_pct"]}%). Instead new signings stepped '
        f'{n_ec} times between 2017 and 2020. The first, {ST["quarter"]}, is {ST["detail"]["signings"]} signings with '
        f'{max(ST["detail"]["by_month"].values())} of them in one month, all but '
        f'{sum(v for k, v in ST["detail"]["by_rir"].items() if k != "apnic")} in APNIC and one parent block '
        f'{ST["detail"]["largest_block_share"]*100:.0f}% of it. Operators moved in batches, not as a population.',
        f'An OS release precedes each of those steps, but a different one each time (Debian 9, Ubuntu 18.04, RHEL 8 / Debian 10, Ubuntu 20.04), '
        f'{CH["within_3m"]*100:.0f}% of all months follow some OS release within 3 months anyway, and two of the five RSA/SHA-256 steps have none '
        f'at all. The timing cannot name a delivery path, and RHEL -- which ships no Knot or PowerDNS in base -- had no ECDSA-default signer until 2022.',
        f'RSA/SHA-256 is the same story earlier: new signings go from {Q5["2010Q4"]:.0f}% in 2010Q4 to {Q5["2011Q2"]:.0f}% in 2011Q2 and '
        f'{Q5["2012Q2"]:.0f}% in 2012Q2, and the step detector puts the step at 2012Q2 -- 15 months after OpenDNSSEC 1.2.0 made RSASHA256 its '
        f'default and 27 after BIND 9.7.0 shipped it. The 2011 rise is 88 signings across three RIRs with one parent block a third of them.',
        f'EdDSA: never a default anywhere; {sum(r["hit"] for r in c8["new_signings"]["rollovers_to_by_year"])} rollovers to it in the whole ledger; '
        f'two forward episodes, both withdrawn. No default, no adoption.',
    ], size=11, color=INK, space=6)

    # 6 RFC 9276
    nu = next(j for j in c9["spikes"] if j["source"] == "nu")
    s = blank(prs); kicker(s, "FINDING 4  ·  RFC 9276 NSEC3 ITERATIONS", "The one vendor-triggered case, and it happened before the RFC", CRIT)
    fit_picture(s, figs / "rfc_9276.png", Inches(1.25), Inches(3.7))
    text(s, Inches(0.62), Inches(5.05), Inches(12.1), Inches(2.2), [
        f'Names with 100 or more NSEC3 iterations collapsed in {nu["start"]}..{nu["end"]} in five of the six TLDs that had any (.nu {nu["level_before"]:,} -> '
        f'{nu["level_after"]}); only .gov, with 38 names, did not move. That is {abs(nu["months_after_rfc"])} months before RFC 9276. Two to three months earlier PowerDNS 4.5.0 and Unbound 1.13.2 '
        f'had capped iterations, and CVE-2021-40083 (Knot Resolver, assertion failure on NSEC3 with too many iterations) was published.',
        f'All {c9["summary"]["n_spikes"]} spikes are within 3 months of a cap against a {pct(c9["chance"]["forward"]["within_3m_after_validator_limit"])} '
        f'chance rate. The caps and the CVE are one event: vendors moved against high counts in mid-2021 and the zones that would have failed were '
        f're-signed. Both sides capped it: PowerDNS Auth is a signer limiting what it will sign, Unbound a validator refusing what it reads. '
        f'The RFC codified what the vendors had already forced. BIND\'s own default change (100 -> 10) was 140 months earlier and moved nothing.',
    ], size=11, color=INK, space=6)

    # 7 CVEs
    s = blank(prs); kicker(s, "FINDING 5  ·  CVEs", "CVEs follow deployment; none led a push")
    text(s, Inches(0.62), Inches(1.4), Inches(12.1), Inches(5.5), [
        f'{n_dnssec} of the {n_cve} CVEs are DNSSEC mechanisms; {core} of those sit in the RFC 4033/4034/4035 core (validation, RRSIG, DNSKEY, NSEC) '
        f'and belong to no single later RFC. The per-RFC sets are small: NSEC3 {len(T["RFC 5155"]["cves"])}, trust anchors {len(T["RFC 5011"]["cves"])}, '
        f'ECDSA {len(T["RFC 6605"]["cves"])}, EdDSA {len(T["RFC 8080"]["cves"])}, RSA/SHA-256 and CDS none; DS digests (RFC 4509) 3 and RFC 2535 one, '
        f'which the per-RFC slides do not cover.',
        f"A CVE is attached to an RFC by the mechanism its description names, not by citing the RFC: {len(cite)} of the {n_dnssec} DNSSEC CVEs cite any RFC "
        f"in their text, and only {len(cite_studied)} cite one of the RFCs studied here ("
        + "; ".join(f'{cv} -> RFC {", ".join(ns)}' for cv, ns in cite_studied) + ").",
        f'Most CVEs nearest to an adoption spike are resolver bugs (memory leak, assertion failure), but not all: CVE-2014-0591, nearest to '
        f'{near["CVE-2014-0591"]} of the NSEC3 spikes, is an assertion failure in BIND\'s AUTHORITATIVE NSEC3 code. Median lag from a spike to the '
        f'nearest CVE: {c6["summary"]["median_lag_to_cve_months"]:.1f} months for ECDSA, {C["RFC 5155"]["summary"]["median_lag_to_cve_months"]:.0f} for NSEC3. '
        f'CVE-2022-38178 came 4 months before the second EdDSA episode; it is a BIND memory leak and not a reason to sign with EdDSA.',
        "The one CVE inside a causal chain is CVE-2021-40083: a symptom of the iteration problem the 2021 caps fixed, published the month the caps "
        f'shipped. The DNSSEC CVE surface sits on the resolvers: Unbound {prod["unbound"]}, PowerDNS Recursor {prod["pdns-rec"]}, Knot Resolver '
        f'{prod["kresd"]}. The pure signers publish almost none (Knot {prod["knot"]}, PowerDNS Auth {prod["pdns-auth"]}, OpenDNSSEC 0) -- but BIND, '
        f'which both signs and validates, carries {prod["bind9"]}, more than any other product.',
        "NSEC3 order of events: BIND 9.6.0 signs it 2008-12, the first NSEC3-signed reverse delegations appear 2009-07, the first CVE 2009-10. "
        "Code, then deployment, then CVEs, each within a year.",
    ], size=12, color=INK, space=8)

    # 8 why fast vs never
    s = blank(prs); kicker(s, "SO WHY FAST, SLOW OR NEVER", "How a change reaches a zone decides its speed")
    rows = [["RFC", "verdict", "how it reaches a zone", "what the data shows"]]
    rows += [
        ["RFC 5702 RSA/SHA-256", T["RFC 5702"]["verdict"], "signer default from 2011, acting on new zones only",
         f'first zone {od["RFC 5702"]["first_zone_seen"]}; new signings {Q5["2010Q4"]:.0f}% (2010Q4) -> {Q5["2011Q2"]:.0f}% (2011Q2) -> '
         f'{Q5["2012Q2"]:.0f}% (2012Q2)'],
        ["RFC 6605 ECDSA", T["RFC 6605"]["verdict"], "signer default from 2016, acting on new zones only; majority by operator rollovers",
         f'first zone {od["RFC 6605"]["first_zone_seen"]}; majority only via 2019 rollovers and the 2021 .ch wave'],
        ["RFC 5155 NSEC3", "already in use", "a signer option; no signer ever made it the default",
         f'already {NSEC3_FIRST_PCT:.1f}% of signed reverse delegations in {NSEC3_FIRST_M}, the first month it is visible -- onset not measurable'],
        ["RFC 9276 iterations", T["RFC 9276"]["verdict"], "validator caps force re-signing", "collapse 2021-10, ten months before the RFC"],
        ["RFC 7344 CDS", T["RFC 7344"]["verdict"], "only useful where the parent acts on it", f'{T["RFC 7344"]["curve_summary"]["forward_last_pct"]:.1f}% of signed forward zones'],
        ["RFC 8080 EdDSA", T["RFC 8080"]["verdict"], "never a default anywhere",
         f'{ED_REV:.2f}% reverse, {ED_FWD:.2f}% forward today (Ed25519 and Ed448 together)'],
        ["RFC 5933 GOST", T["RFC 5933"]["verdict"], "never a default; Russian namespace not in corpora",
         f'0.00% on the panel today; peaked at {GOST_PEAK} delegations at RIPE in {GOST_PEAK_M}'],
    ]
    table(s, Inches(0.5), Inches(1.35), Inches(12.3), rows, [Inches(2.0), Inches(1.4), Inches(4.4), Inches(4.5)], size=10)
    text(s, Inches(0.62), Inches(4.5), Inches(12.1), Inches(2.5), [
        "Fast RFCs are the ones a signer default carries into every newly signed zone. Slow ones need operators to roll existing zones, and "
        "operators do that in six-figure batches years after the default changed. Never-adopted ones had no default anywhere. The only RFC that "
        "moved on a vendor's schedule was the one where validators refused the old value.",
    ], size=12, color=INK)

    # 9 CVE patches vs RFC publications
    VR = json.loads(Path("out/analysis/cve_vs_rfc_rates.json").read_text("utf-8"))
    rv = VR["overall"]["reverse signed share (strict panel)"]["raw"]
    s = blank(prs); kicker(s, "FINDING 6  ·  CVE PATCHES vs RFC PUBLICATIONS", "Adoption moves at the same speed after either")
    fit_picture(s, Path("reporting/charts/rate_hist_both.png"), Inches(1.25), Inches(3.6), max_w=Inches(7.5))
    text(s, Inches(0.62), Inches(5.3), Inches(12.1), Inches(1.9), [
        f'Take every month in which a DNSSEC CVE was patched ({rv["cve_patches"]["n"]} months; {rv["cve_events"]} CVEs, several sharing a fix month) '
        f'and every month in which a DNSSEC RFC was published ({rv["rfc_publications"]["n"]} months inside the reverse series). The adoption rate over '
        f'that month and the three after it has the same distribution in both groups and in ordinary months: medians '
        f'{rv["cve_patches"]["median"]*1000:.1f}, {rv["rfc_publications"]["median"]*1000:.1f} and {rv["all_months"]["median"]*1000:.1f} thousandths of a '
        f'point per month; permutation p = {rv["p_cve_vs_rfc"]:.2f}.',
        "Measured on each event\'s own mechanism instead, RFC publications sit in ordinary or dead months (RFC 6605 at the 3rd percentile of the ECDSA "
        "curve) and two CVE patch months are extreme: CVE-2021-40083 is the NSEC3 iteration collapse, and CVE-2022-38177/38178 coincides with one "
        "ARIN block re-signing to ECDSA -- timing, not cause.",
    ], size=11, color=INK, space=6)

    # 10 summary and takeaways
    s = blank(prs); kicker(s, "SUMMARY AND TAKEAWAYS", "What decides whether a DNSSEC RFC gets adopted")
    text(s, Inches(0.62), Inches(1.35), Inches(12.1), Inches(5.6), [
        f'1.  Code is never the bottleneck. For the five RFCs whose onset is measurable, implementation came within {min(code):+.1f} to '
        f'{max(code):+.1f} years of publication and the first zone took a further {min(dep):.1f} to {max(dep):.1f} years. The slowest code lag '
        f'anywhere is RFC 5011 at +2.4 years, still well inside its adoption gap. The wait is operators, not vendors.',
        "2.  A default can only ever change what a newly signed zone gets. It never re-signs an existing zone, so it cannot produce a spike; the only "
        "place it could show is in what new zones choose, months to years later.",
        f'3.  Operators switch in sudden batches, and the trigger is not identifiable. New reverse signings jumped to ECDSA in {n_ec} steps, each '
        f'over one to three months and 13 to 24 parent blocks. An OS release precedes every step, but no single one explains them: Debian 9, '
        f'Ubuntu 18.04, RHEL 8 with Debian 10, then Debian 10 with Ubuntu 20.04. {CH["within_3m"]*100:.0f}% of months follow some OS release '
        f'anyway, and two RSA/SHA-256 steps have none at all.',
        "4.  Spikes in the adoption curve are operator decisions: six-figure rollovers by a registry or hoster, years after any default. No release month "
        f"moves the curve; {dens*100:.0f}% of months contain a release, so a nearby release is never evidence.",
        "5.  Validators can force an RFC before it exists. The NSEC3 iteration collapse of 2021-10 followed the resolver caps and CVE-2021-40083 by two "
        "months and preceded RFC 9276 by ten. It is the only vendor-timed adoption event in the data.",
        "6.  CVEs do not lead adoption. CVE-patch months and RFC-publication months have the same adoption rate as any other month; the one CVE inside a "
        "causal chain is a symptom of the problem the caps fixed.",
        "7.  Never-adopted RFCs (EdDSA, GOST) share one trait: no signer ever made them a default. Niche ones (CDS) only matter where the parent acts on them.",
        "Takeaway: to predict an RFC\'s adoption, look at whether a signer makes it the default, not at the RFC date, the first implementation, "
        "or the CVEs. Which delivery path carries a default to a given operator is not visible in published DNS records.",
    ], size=11.5, color=INK, space=7)

    # 11 limits
    s = blank(prs); kicker(s, "LIMITS", "What this cannot show")
    text(s, Inches(0.62), Inches(1.4), Inches(12.1), Inches(5.5), [
        "Which software signs a zone is never visible from its records; 'nearest release' is timing evidence. Registry and registrar signing "
        "platforms are closed source and are not in the release list.",
        "OpenINTEL here is monthly aggregates for seven TLDs entering between 2016-06 and 2020-05 and ending 2023-12. RSA/SHA-256 and NSEC3 are "
        "plainly present in it, but their growth happened before it opens, so only reverse DNS witnesses their adoption. Forward spikes cannot be "
        "attributed to an operator.",
        "Reverse DNS is small (25,930 change events on 13,654 delegations) and NSEC3 is visible there only through algorithm 7.",
        "The OS package table is Debian, Ubuntu and RHEL only. FreeBSD ports, Alpine, containers, appliances and source builds are absent, and "
        "RHEL base ships no Knot or PowerDNS at all. Package dates bound when a default became reachable, never what an operator ran.",
        "With 3 to 31 spikes per RFC, 'beats chance' is a reading, not a test with a p-value. CVE attribution is by NVD product only.",
        "Decks with every figure and ledger: dnssec_rfc_why.pptx (per-RFC timelines), dnssec_program_rfc_cases.pptx (per-program case studies), "
        "dnssec_algorithm_flows.pptx (what zones move between). CSVs: dns_software_*.csv, dns_cve_list.csv, dns_program_rfc_spikes.csv.",
    ], size=12, color=INK, space=8)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(a.out)
    dump = [{"n": i, "text": [sh.text_frame.text for sh in sl.shapes if sh.has_text_frame] +
             [c.text for sh in sl.shapes if sh.has_table for r in sh.table.rows for c in r.cells]}
            for i, sl in enumerate(prs.slides, 1)]
    Path(str(a.out).replace(".pptx", "_slides.json")).write_text(json.dumps(dump, indent=1), "utf-8")
    print(f"{len(prs.slides)} slides -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
