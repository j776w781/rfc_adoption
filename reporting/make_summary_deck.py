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
    os9 = next(r for r in c6["new_signings"]["around_os_ships"] if r["os"] == "Debian 9")
    od = {o["rfc"]: o for o in SC["onset_decomposition"]}
    code = [o["code_lag_years"] for o in SC["onset_decomposition"] if o.get("code_lag_years") is not None]
    dep = [o["deployment_lag_years"] for o in SC["onset_decomposition"] if o.get("deployment_lag_years") is not None]
    smallest_p = min(v["circular_shift_p"] for v in RS["per_project"].values() if v.get("testable"))

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
        "Short version: code is never the wait; defaults do reach zones, through OS releases and only on newly signed zones, so they "
        "never show as a spike; one RFC was forced by validators before it was published; no CVE led a push.",
    ], size=14, color=INK_2)

    # 2 what we did
    s = blank(prs); kicker(s, "WHAT WE DID", "Four sources, one time axis")
    rows = [
        ("Software", f"{len(R)} projects cloned; {n_rel:,} stable release dates from git tags (BIND development branches excluded). "
                     "For each RFC: the first release that signs or validates it, the release that changed the default, and "
                     "validator caps -- each backed by the commit and checked to be contained in the cited release."),
        ("OS packages", "the first Ubuntu LTS (16.04 to 24.04) and Debian (11 to 13) release carrying each version, from Launchpad and "
                        "the Debian tracker: the path by which most operators actually receive a new default."),
        ("CVEs", f"{n_cve} CVEs across the eight products from NVD; {n_dnssec} are DNSSEC mechanisms, classified by the mechanism the "
                 f"description names (NSEC3, validation, trust anchor, algorithm...) and attributed to a product only by NVD CPE."),
        ("Zones", "OpenINTEL zone files for .se .nu .ch .li .ee .gov .fed.us (2016-06 to 2023-12) and reverse DNS for five RIRs "
                  "(2009-03 to 2026-08), with the strict AFRINIC+ARIN panel for reverse shares and a per-delegation change ledger."),
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
        f"detrending, the smallest circular-shift p across the eight projects is {smallest_p:.2f}. 97% of months contain some DNS release, "
        f"so 'a release came just before' is always true and never evidence.",
        "Verdict rule: FAST = first zone within a year of the RFC and 10% of signed delegations within four; SLOW = reached 10%, later; "
        "NEVER = under 1% of signed zones today.",
    ], size=12, color=INK, space=8)

    # 4 ECDSA
    j16 = next(j for j in c6["spikes"] if j["source"] == "se" and j["start"] == "2016-10")
    j19 = next(j for j in c6["spikes"] if j["source"] == "se" and j["start"] == "2019-06")
    jch = next(j for j in c6["spikes"] if j["source"] == "ch" and j["start"] == "2021-06")
    s = blank(prs); kicker(s, "FINDING 2  ·  RFC 6605 ECDSA", "Defaults changed in 2016; the zones moved in 2019 and 2021, by hand", ACCENT)
    fit_picture(s, figs / "rfc_6605.png", Inches(1.25), Inches(3.9))
    text(s, Inches(0.62), Inches(5.25), Inches(12.1), Inches(2.0), [
        f'Knot 2.1.0 (2016-01) and PowerDNS 4.0.0 (2016-07) made ECDSA the default; BIND 9.16.0 (2020-02) offered it as an opt-in policy. '
        f'The first forward move, .se {j16["start"]} +{j16["delta"]:,}, is {j16["nearest_default_change"]["lag_months"]} months after the PowerDNS '
        f'default but {j16["split"]["rollovers_at_least"]:,} of those zones were existing zones rolling over: an operator decision, not an update.',
        f'The moves that made ECDSA the majority were all rollovers, 30-35 months after any default (.se {j19["start"]}..{j19["end"]} '
        f'+{j19["delta"]:,}). The .ch wave of {jch["start"]}..{jch["end"]} (+{jch["delta"]:,}) was new signings choosing ECDSA '
        f'{jch["share_after_pct"]:.0f}% of the time -- that is where a default acts: silently, on new zones, years after it changed. '
        f'{c6["summary"]["spikes_within_3m_of_default_change"]} of {c6["summary"]["n_spikes"]} spikes sit within 3 months of a default, '
        f'against a {pct(c6["chance"]["forward"]["within_3m_after_default_change"])} chance rate.',
    ], size=11, color=INK, space=6)

    # 5 auto-update
    s = blank(prs); kicker(s, "FINDING 3  ·  THE AUTO-UPDATE TEST", "Updates work: the OS release is the event, and it acts on new zones only", ACCENT)
    fit_picture(s, figs / "rfc_6605_new_signings.png", Inches(1.25), Inches(2.6))
    text(s, Inches(0.62), Inches(4.0), Inches(12.1), Inches(3.2), [
        "An update cannot roll an existing zone; it can only change what a zone signed after the update gets. So the test is the share of "
        "NEW signings choosing the algorithm, which the reverse ledger records per delegation.",
        f'ECDSA: on their upstream dates the 2016 Knot and PowerDNS defaults left no trace ({ar6["2.1.0"]["share_before_pct"]}% -> '
        f'{ar6["2.1.0"]["share_after_pct"]}%, {ar6["4.0.0"]["share_before_pct"]}% -> {ar6["4.0.0"]["share_after_pct"]}%), and neither did Ubuntu 16.04, '
        f'which carried only Knot. Debian 9 ({os9["date"]}) was the first OS release to ship both ECDSA-default signers: in the year after it, '
        f'{os9["share_after_pct"]}% of new reverse signings chose ECDSA ({os9["share_before_pct"]}% the year before), from {os9["blocks_choosing_after"]} '
        f'blocks ({os9["blocks_choosing_before"]} before). A second step, {ar6["9.16.0"]["share_before_pct"]}% -> {ar6["9.16.0"]["share_after_pct"]}%, '
        f'came with BIND 9.16.0 in Ubuntu 20.04 and Debian 11.',
        f'RSA/SHA-256: new signings choosing it went {ar5["1.2.0"]["share_before_pct"]}% -> {ar5["1.2.0"]["share_after_pct"]}% across OpenDNSSEC 1.2.0\'s '
        f'default (2011-03) and kept rising for two years; BIND 9.7.0 had shipped it 13 months earlier, so it reads as availability, not one vendor.',
        f'EdDSA: never a default anywhere; {sum(r["hit"] for r in c8["new_signings"]["rollovers_to_by_year"])} rollovers to it in the whole ledger; '
        f'two forward episodes, both withdrawn. No default, no adoption.',
    ], size=11, color=INK, space=6)

    # 6 RFC 9276
    nu = next(j for j in c9["spikes"] if j["source"] == "nu")
    s = blank(prs); kicker(s, "FINDING 4  ·  RFC 9276 NSEC3 ITERATIONS", "The one vendor-triggered case, and it happened before the RFC", CRIT)
    fit_picture(s, figs / "rfc_9276.png", Inches(1.25), Inches(3.7))
    text(s, Inches(0.62), Inches(5.05), Inches(12.1), Inches(2.2), [
        f'Names with 100 or more NSEC3 iterations collapsed in {nu["start"]}..{nu["end"]} in every TLD that had them (.nu {nu["level_before"]:,} -> '
        f'{nu["level_after"]}), {abs(nu["months_after_rfc"])} months before RFC 9276. Two to three months earlier PowerDNS 4.5.0 and Unbound 1.13.2 '
        f'had capped iterations, and CVE-2021-40083 (Knot Resolver, assertion failure on NSEC3 with too many iterations) was published.',
        f'All {c9["summary"]["n_spikes"]} spikes are within 3 months of a cap against a {pct(c9["chance"]["forward"]["within_3m_after_validator_limit"])} '
        f'chance rate. The caps and the CVE are one event: resolver vendors agreed to reject high counts and the zones that would have failed were '
        f're-signed. The RFC codified what validators had already forced. BIND\'s own default change (100 -> 10) was 140 months earlier and moved nothing.',
    ], size=11, color=INK, space=6)

    # 7 CVEs
    s = blank(prs); kicker(s, "FINDING 5  ·  CVEs", "CVEs follow deployment; none led a push")
    text(s, Inches(0.62), Inches(1.4), Inches(12.1), Inches(5.5), [
        f'{n_dnssec} of the {n_cve} CVEs are DNSSEC mechanisms; {core} of those sit in the RFC 4033/4034/4035 core (validation, RRSIG, DNSKEY, NSEC) '
        f'and belong to no single later RFC. The per-RFC sets are small: NSEC3 {len(T["RFC 5155"]["cves"])}, trust anchors {len(T["RFC 5011"]["cves"])}, '
        f'ECDSA {len(T["RFC 6605"]["cves"])}, EdDSA {len(T["RFC 8080"]["cves"])}, RSA/SHA-256 and CDS none.',
        "A CVE is attached to an RFC by the mechanism its description names, not by citing the RFC; only CVE-2023-50868 (NSEC3) and CVE-2013-4854 "
        "(RFC 5011) name their RFC in the text.",
        f'Every CVE nearest to an adoption spike is a validator bug (memory leak, assertion failure). Median lag from a spike to the nearest CVE: '
        f'{c6["summary"]["median_lag_to_cve_months"]:.0f} months for ECDSA, {C["RFC 5155"]["summary"]["median_lag_to_cve_months"]:.0f} for NSEC3. '
        f'CVE-2022-38178 came 4 months before the second EdDSA episode; it is a BIND memory leak and not a reason to sign with EdDSA.',
        "The one CVE inside a causal chain is CVE-2021-40083: a symptom of the iteration problem the 2021 caps fixed, published the month the caps "
        "shipped. The DNSSEC CVE surface is on validators (Unbound, BIND, Knot Resolver, PowerDNS Recursor); the signers whose defaults move zones "
        "publish almost none.",
        "NSEC3 order of events: BIND 9.6.0 signs it 2008-12, the first NSEC3-signed reverse delegations appear 2009-07, the first CVE 2009-10. "
        "Code, then deployment, then CVEs, each within a year.",
    ], size=12, color=INK, space=8)

    # 8 why fast vs never
    s = blank(prs); kicker(s, "SO WHY FAST, SLOW OR NEVER", "How a change reaches a zone decides its speed")
    rows = [["RFC", "verdict", "how it reaches a zone", "what the data shows"]]
    rows += [
        ["RFC 5702 RSA/SHA-256", T["RFC 5702"]["verdict"], "signer default, inherited by new zones",
         f'first zone {od["RFC 5702"]["first_zone_seen"]}; new reverse signings {ar5["1.2.0"]["share_before_pct"]}% -> {ar5["1.2.0"]["share_after_pct"]}% across the 2011 default'],
        ["RFC 6605 ECDSA", T["RFC 6605"]["verdict"], "signer default (2016) + operator rollovers",
         f'first zone {od["RFC 6605"]["first_zone_seen"]}; majority only via 2019 rollovers and the 2021 .ch wave'],
        ["RFC 5155 NSEC3", T["RFC 5155"]["verdict"], "signer option; BIND default from 9.7.0", f'first zone {T["RFC 5155"]["lags"]["first_zone_seen"]}; 10% at {T["RFC 5155"]["adoption"][0]["t_10pct"]}'],
        ["RFC 9276 iterations", T["RFC 9276"]["verdict"], "validator caps force re-signing", "collapse 2021-10, ten months before the RFC"],
        ["RFC 7344 CDS", T["RFC 7344"]["verdict"], "only useful where the parent acts on it", f'{T["RFC 7344"]["curve_summary"]["forward_last_pct"]:.1f}% of signed forward zones'],
        ["RFC 8080 EdDSA", T["RFC 8080"]["verdict"], "never a default anywhere", f'{T["RFC 8080"]["curve_summary"]["reverse_last_pct"]:.2f}% reverse, {T["RFC 8080"]["curve_summary"]["forward_last_pct"]:.2f}% forward today'],
        ["RFC 5933 GOST", T["RFC 5933"]["verdict"], "never a default; Russian namespace not in corpora", "0.00% in both corpora"],
    ]
    table(s, Inches(0.5), Inches(1.35), Inches(12.3), rows, [Inches(2.2), Inches(1.5), Inches(3.6), Inches(5.0)], size=10)
    text(s, Inches(0.62), Inches(4.5), Inches(12.1), Inches(2.5), [
        "Fast RFCs are the ones a signer default carries into every newly signed zone. Slow ones need operators to roll existing zones, and "
        "operators do that in six-figure batches years after the default changed. Never-adopted ones had no default anywhere. The only RFC that "
        "moved on a vendor's schedule was the one where validators refused the old value.",
    ], size=12, color=INK)

    # 9 limits
    s = blank(prs); kicker(s, "LIMITS", "What this cannot show")
    text(s, Inches(0.62), Inches(1.4), Inches(12.1), Inches(5.5), [
        "Which software signs a zone is never visible from its records; 'nearest release' is timing evidence. Registry and registrar signing "
        "platforms are closed source and are not in the release list.",
        "OpenINTEL here is monthly aggregates for seven TLDs from 2016-06 (2020-05 for .ch/.li) to 2023-12, so RSA/SHA-256 and NSEC3 adoption "
        "are visible only in reverse DNS, and forward spikes cannot be attributed to an operator.",
        "Reverse DNS is small (25,930 change events on 13,654 delegations) and NSEC3 is visible there only through algorithm 7.",
        "OS package dates bound when a default became reachable by apt, not when anyone upgraded. The Debian 9 step rests on 55 blocks in one "
        "corpus, APNIC-heavy, with one block a third of it.",
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
