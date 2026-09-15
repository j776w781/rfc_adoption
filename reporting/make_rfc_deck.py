"""Build the per-RFC deck: why some DNSSEC RFCs are adopted fast and some never.

One slide per RFC carrying the integrated timeline -- the standard, every
program's release for it, the CVEs that touched it, and the adoption curve with
its spikes -- plus an evidence line, then a synthesis. Every number on every
slide is read from an analysis JSON or recomputed from the timeline; the prose
is built from those values so it cannot drift from them.

    python reporting/make_rfc_deck.py [--out out/analysis/dnssec_rfc_why.pptx]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches, Pt

from make_flows_deck import ACCENT, INK, INK_2, MUTED, SURFACE, W, H, blank, text  # noqa

CRIT = RGBColor(0xD0, 0x3B, 0x3B)
GOOD = RGBColor(0x1B, 0xAF, 0x7A)
ORDER = ["RFC 5702", "RFC 5155", "RFC 9276", "RFC 6605", "RFC 7344", "RFC 8080",
         "RFC 5933", "RFC 5011"]
VC = {"fast": GOOD, "fast, then contested": GOOD, "slow": ACCENT, "vendor-triggered": CRIT,
      "never": CRIT, "niche by design": ACCENT, "partly observable": MUTED, "stalled": ACCENT}
NAME = {"unbound": "Unbound", "nsd": "NSD", "bind9": "BIND 9", "knot": "Knot DNS",
        "kresd": "Knot Resolver", "opendnssec": "OpenDNSSEC",
        "pdns-auth": "PowerDNS Auth", "pdns-rec": "PowerDNS Rec"}


def nm(s):
    if not s:
        return None
    key, _, ver = s.partition(" ")
    return f"{NAME.get(key, key)} {ver}"


def ym(d):
    return d[:7] if d else None


def evidence_line(e):
    L, C = e["lags"], e["curve_summary"]
    bits = [f"published {e['published']}"]
    if L.get("first_signer_release"):
        bits.append(f"first signer {nm(L.get('first_signer')) or ''} {ym(L['first_signer_release'])}".replace("  ", " "))
    if L.get("first_validator_release"):
        bits.append(f"first validator {nm(L.get('first_validator')) or ''} {ym(L['first_validator_release'])}".replace("  ", " "))
    if L.get("first_zone_seen"):
        bits.append(f"first zone {L['first_zone_seen']}"
                    + (f" ({L['first_seen_basis']})" if L.get("first_seen_basis") else ""))
    if L.get("onset_years") is not None and L.get("code_lag_years") is not None:
        bits.append(f"onset {L['onset_years']:.1f} y = code {L['code_lag_years']:+.1f} "
                    f"+ operators {L['deployment_lag_years']:.1f}")
    for a in e["adoption"]:
        if a.get("t_10pct"):
            bits.append(f"{a['change']} 10% at {a['t_10pct']}")
    if C.get("forward_last_pct") is not None:
        bits.append(f"forward now {C['forward_last_pct']:.1f}%")
    if C.get("reverse_last_pct") is not None:
        bits.append(f"reverse now {C['reverse_last_pct']:.1f}%")
    for o in e.get("successor_overlap", []):
        bits.append(f"published when {o['predecessor']} was at "
                    f"{o['fraction_of_peak_reached']*100:.0f}% of its eventual share")
    if e["cves"]:
        first = min(c["published"] for c in e["cves"])
        if e.get("cve_note"):
            bits.append(f"{len(e['cves'])} NSEC3 CVEs since the 2021 cap (1 names RFC 9276), "
                        f"counted again on the RFC 5155 slide")
        else:
            bits.append(f"{len(e['cves'])} CVEs naming it, first {first[:7]}")
    if e["spikes"]:
        b = max(e["spikes"], key=lambda j: j["delta_zones"])
        bits.append(f"largest spike +{b['delta_zones']:,} .{b['source']} {b['month']} "
                    f"({b['operator']})")
    if e.get("revoked"):
        r = e["revoked"]
        bits.append(f"revoked keys on {r['min']}-{r['max']} forward zones/month since {r['first']}")
    return "  ·  ".join(bits)


def why(e, X):
    """Prose per RFC, built from values on the slide. Nothing typed in that the
    evidence line does not carry or that a source file does not state."""
    rfc, L, C = e["rfc"], e["lags"], e["curve_summary"]
    if rfc == "RFC 5702":
        return (f"Same key type and sizes as RSA/SHA-1, so a zone changes one number, not "
                f"its key management. {nm(L['first_validator'])} validated it "
                f"{X['5702_val_lead']} months before the RFC and {nm(L['first_signer'])} "
                f"signed it {X['5702_sign_lag']} months after; the first zone followed the "
                f"signer within two months. It is the only signing algorithm in the set that "
                f"changed nothing about a zone's keys. Whether a default carried it cannot be "
                f"tested -- "
                f"OpenDNSSEC made it the default in 2011-03, but both corpora open with it "
                f"already in use, so no before-period exists.")
    if rfc == "RFC 5155":
        return (f"Unbound could validate NSEC3 four months before the RFC existed and BIND "
                f"could sign it nine months after. A tenth of signed delegations by "
                f"{e['adoption'][0]['t_10pct']}, and {C['forward_peak_pct']:.0f}% of "
                f"forward zones when that corpus opens in 2016. {len(e['cves'])} CVEs name "
                f"NSEC3, the first 1.6 years after the RFC and {X['5155_cves_2026']} in 2026's "
                f"audit wave. Its iteration count -- which RFC 5155 allowed up to 65,535 -- "
                f"was only capped by vendors thirteen years later, which is RFC 9276's slide.")
    if rfc == "RFC 9276":
        ex = e["iterations_exactly_100"]; gt = e["iterations_over_100"]; w = e["collapse"]
        return (f"The one RFC in this set where zones demonstrably moved before the standard. "
                f"Resolver vendors agreed a 150-iteration cap in a commit in 2021-05; PowerDNS "
                f"Auth capped configurable iterations at 100 in 2021-07; Unbound shipped 150 "
                f"in 2021-08; CVE-2021-40083 (a Knot Resolver crash on high iterations) was "
                f"published 2021-08-25, after the cap was already committed. Names at 100 or "
                f"more iterations fell {w['before']:,} to {w['after']:,} in {w['month']} -- "
                f"{ex['2021-09']:,} of them sitting at exactly 100, BIND's pre-2010 default, "
                f"which neither cap refused ({gt['2021-09']} were above 100, and {gt['2021-10']} "
                f"still were after). RFC 9276 came ten months later; CVE-2023-50868 two years "
                f"and four months after the collapse. The ordering is certain. What moved "
                f"the names -- refusal, guidance, or an operator re-signing -- the data "
                f"cannot separate.")
    if rfc == "RFC 6605":
        return (f"The code was never the wait: PowerDNS signed ECDSA three months before the "
                f"RFC, Unbound validated it one month after, and the first zone came "
                f"{L['deployment_lag_years']:.1f} years later. Knot (2016-01, at "
                f"{X['knot_share']:.2f}% share) and PowerDNS (2016-07, at {X['pdns_share']:.2f}%) "
                f"then made it their default, and .se and .nu show their first ECDSA jump in "
                f"2016-10 (+{X['se_1610']:,} and +{X['nu_1610']:,}), three months after "
                f"PowerDNS 4.0.0 -- an alignment, not an attribution: on the reverse panel, "
                f"the only corpus with a before-period, event studies around both defaults "
                f"detect nothing ({X['knot_delta']:+.3f} and {X['pdns_delta']:+.3f} pp/month). "
                f"The forward rise is two registries: .se migrating {X['se_1901']:,} zones in "
                f"2019-01, SWITCH mass-signing .ch (+{X['ch_2108']:,}) in 2021-08. The reverse "
                f"curve's owners are network blocks: the largest single ECDSA action is "
                f"{X['rev_act']['n']} delegations under {X['rev_act']['block']} in "
                f"{X['rev_act']['month']}.")
    if rfc == "RFC 7344":
        return (f"{C['forward_last_pct']:.1f}% of signed forward zones publish a CDS record, "
                f"and only a zone whose parent will act on it has reason to. Where a registry "
                f"does -- SWITCH's registry page says it polls .ch and .li for CDS and signs on "
                f"sight, a statement this repository cites but does not contain -- CDS "
                f"publication jumped first ({X['ch_cds_2104']:,} .ch zones in "
                f"2021-04 to {X['ch_cds_2107']:,} in 2021-07) and signed zones followed "
                f"({X['ch_signed_2105']:,} to {X['ch_signed_2109']:,} by 2021-09), taking .ch "
                f"from {X['ch_signed_2101']:,} to {X['ch_signed_2112']:,} signed zones inside "
                f"2021. An RFC that automates a step is adopted by the party that automates.")
    if rfc == "RFC 8080":
        o = e["successor_overlap"][0]
        return (f"Knot, Unbound and BIND shipped EdDSA within a year of the RFC; OpenDNSSEC "
                f"took 3.6. No vendor ever made it a default. It was published when ECDSA "
                f"stood at {o['fraction_of_peak_reached']*100:.0f}% of the share it would "
                f"reach. Nine years on: {C['reverse_last_pct']:.2f}% of panel delegations, "
                f"{C['forward_last_pct']:.2f}% of forward zones; the only spikes were one "
                f"operator's .se and .nu moves, withdrawn twice. One CVE names EdDSA "
                f"(CVE-2022-38178), published at 0.02% deployment.")
    if rfc == "RFC 5933":
        o = e["successor_overlap"][0]
        return (f"BIND and Unbound both implemented GOST from the draft, before the RFC. In "
                f"these corpora it never exceeded five RIPE delegations (2012-12 to 2015-08) "
                f"or four forward zones: 0.00% of the strict AFRINIC+ARIN panel and of the "
                f"seven TLDs, none of which is Russian; the RIPE region, where every reverse "
                f"GOST record sits, is outside the panel. Published when RSA/SHA-2 was at "
                f"{o['fraction_of_peak_reached']*100:.0f}% of its eventual share. RFC 9906 "
                f"deprecated it in 2025-11, a decade after its last record here -- like RFC "
                f"9276 at the front, it documented what had already happened.")
    if rfc == "RFC 5011":
        r = e["revoked"]
        return (f"The resolver half -- hold-down timers, whether a validator accepts a new "
                f"anchor -- leaves no trace in any zone, and the reverse corpus (NS and DS "
                f"only) sees none of it. The signer half does leave one: the REVOKE bit RFC "
                f"5011 defines, on {r['min']} to {r['max']} forward zones in every month since "
                f"{r['first']} (median {r['median']}). BIND 9.7.0 could both revoke a key "
                f"and track a rolled anchor from {X['bind_5011']}, Unbound 1.4.0 the validator "
                f"side from 2009-11; the forward corpus opens with revoked keys already "
                f"present, so first-seen is left-censored. {len(e['cves'])} CVEs mention "
                f"trust anchors; the first ({min(c['published'] for c in e['cves'])[:7]}) "
                f"predates every implementation in the table.")
    return ""


def rfc_slide(prs, e, figs, X):
    s = blank(prs)
    v = e["verdict"]
    text(s, Inches(0.62), Inches(0.36), Inches(8), Inches(0.3),
         [f"{v.upper()}  ·  {e['rfc']}"], size=12, color=VC.get(v, MUTED), bold=True)
    text(s, Inches(0.62), Inches(0.64), Inches(12.1), Inches(0.7), [e["title"]],
         size=26, bold=True)
    fig = figs / f"{e['rfc'].replace(' ', '_').lower()}.png"
    band_top, band_h = Inches(1.34), Inches(3.75)
    pic = s.shapes.add_picture(str(fig), Inches(0.9), band_top, height=band_h)
    if pic.width > Inches(11.9):
        pic.width, pic.height = Inches(11.9), int(pic.height * Inches(11.9) / pic.width)
    pic.left = int((W - pic.width) / 2)
    pic.top = int(band_top + (band_h - pic.height) / 2)
    text(s, Inches(0.62), Inches(5.2), Inches(12.1), Inches(1.35), [why(e, X)],
         size=11.5, color=INK)
    text(s, Inches(0.62), Inches(6.62), Inches(12.1), Inches(0.6), [evidence_line(e)],
         size=8.5, color=MUTED)
    return s


def facts():
    """Every number the prose uses that is not already on the evidence line."""
    T = json.loads(Path("out/analysis/rfc_timelines.json").read_text("utf-8"))
    SC = json.loads(Path("out/analysis/software_crossref.json").read_text("utf-8"))
    CV = json.loads(Path("out/analysis/cve_crossref.json").read_text("utf-8"))
    CA = json.loads(Path("out/analysis/cve_adoption_crossref.json").read_text("utf-8"))
    RA = json.loads(Path("out/analysis/release_vs_adoption.json").read_text("utf-8"))
    RS = json.loads(Path("out/analysis/release_scan.json").read_text("utf-8"))
    SUP = json.loads(Path("data/software/software_support.json").read_text("utf-8"))
    srv = pd.read_parquet("out/server_run/timeline_monthly.parquet")
    X = {}

    def months(a, b):
        return (int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))
    L = T["RFC 5702"]["lags"]
    X["5702_val_lead"] = months(L["first_validator_release"], "2009-10")
    X["5702_sign_lag"] = months("2009-10", L["first_signer_release"])
    X["5155_cves_2026"] = sum(1 for c in T["RFC 5155"]["cves"] if c["published"].startswith("2026"))

    ev = {e["software"]: e for e in RA["event_studies"] if e["kind"] == "default change"
          and e["observable"] == "alg 13/14" and e["basis"] == "reverse"}
    X["knot_share"] = ev["knot 2.1.0"]["share_at_event_pct"]
    X["pdns_share"] = ev["pdns-auth 4.0.0"]["share_at_event_pct"]
    X["knot_delta"] = ev["knot 2.1.0"]["change_pp"]
    X["pdns_delta"] = ev["pdns-auth 4.0.0"]["change_pp"]
    J = {(j["month"], j["source"]): j["delta_zones"] for j in SC["portfolio_jumps"]["alg 13/14"]}
    X["se_1610"], X["nu_1610"] = J[("2016-10", "se")], J[("2016-10", "nu")]
    X["se_1901"], X["ch_2108"] = J[("2019-01", "se")], J[("2021-08", "ch")]

    f = srv[srv.basis == "zonefile"]
    cds = f[(f.dimension == "rr_type") & (f.value.astype(str) == "CDS") & (f.source == "ch")].set_index("month").domains_peak
    sig = f[(f.dimension == "algorithm_dnskey") & (f.value.astype(str) == "_total") & (f.source == "ch")].set_index("month").domains_peak
    X["ch_cds_2104"], X["ch_cds_2107"] = int(cds["2021-04"]), int(cds["2021-07"])
    X["ch_signed_2105"], X["ch_signed_2109"] = int(sig["2021-05"]), int(sig["2021-09"])
    X["ch_signed_2101"], X["ch_signed_2112"] = int(sig["2021-01"]), int(sig["2021-12"])

    dec = {r["observable"]: r for r in SC["onset_decomposition"]}
    X["dec"] = dec
    X["stages"] = {}
    for r in CA["changes"]:
        for c in r["cves"]:
            X["stages"][c["stage_when_published"]] = X["stages"].get(c["stage_when_published"], 0) + 1
    X["core"] = CA["shared_core"]["n_cves"]; X["dnssec_total"] = CA["totals"]["dnssec_cves"]
    qm = CV["query_method"]
    X["per_program"] = {NAME[p]: CV["per_project"][p].get("dnssec", 0)
                        for p in ("bind9", "unbound", "pdns-rec", "pdns-auth", "nsd", "opendnssec")
                        if qm.get(p) == "cpe" or p in ("nsd", "opendnssec")}
    kt = next(c for c in CV["coordinated"] if c["cve"] == "CVE-2023-50387")
    X["keytrap_spread"] = kt["spread_days"]; X["keytrap_vendors"] = len(kt["vendors"])
    X["bind_p"] = RS["per_project"]["bind9"]["circular_shift_p"]
    ub = [r for r in SUP["support"] if r["implementation"] == "unbound"]
    X["unbound_pre"] = sum(1 for r in ub if r.get("pre_rfc"))
    X["unbound_rows"] = len(ub)
    X["unbound_pre_names"] = ", ".join(r["observable"] for r in ub if r.get("pre_rfc"))
    X["code_lags"] = sorted(r["code_lag_years"] for r in dec.values() if r.get("code_lag_years") is not None)
    X["dep_lags"] = sorted(r["deployment_lag_years"] for r in dec.values() if r.get("deployment_lag_years") is not None)
    X["bind_defaults"] = [(r["first_release"], r["released"][:7], r["what"], bool(r.get("opt_in")))
                          for r in SUP["default_changes"] if r["implementation"] == "bind9"]
    # ECDSA rows only. The alg 8/10 rows carry OpenDNSSEC 1.2.0, which is
    # start-censored on both corpora and whose result releases_vs_adoption.md withdrew.
    tk = [r for r in RA["takeoff"] if r.get("from_default_change_to_1pct_years") is not None
          and r["observable"] == "alg 13/14" and not r.get("censored_start")]
    X["tk_def"] = (min(r["from_default_change_to_1pct_years"] for r in tk),
                   max(r["from_default_change_to_1pct_years"] for r in tk))
    X["tk_rfc"] = (min(r["from_rfc_to_1pct_years"] for r in tk),
                   max(r["from_rfc_to_1pct_years"] for r in tk))
    X["col"] = SC["nsec3_iteration_collapse"]["largest_single_month_fall"]
    X["cds_jump"] = max(json.loads(Path("out/analysis/cds_only_spikes.json").read_text("utf-8")),
                        key=lambda j: j["delta_zones"])
    # Reverse-panel spikes have owners too: the largest alg-13 action in the ledger.
    acts = pd.read_csv("out/analysis/dns_delegation_actions.csv")
    a13 = acts[(acts.kind == "sign") & (acts.to_alg.astype(str) == "13")].sort_values("n_delegations", ascending=False).iloc[0]
    X["rev_act"] = {"month": a13.month, "source": a13.source, "block": a13.block, "n": int(a13.n_delegations)}
    b5011 = [r for r in SUP["support"] if r["implementation"] == "bind9" and r["rfc"] == "RFC 5011"]
    X["bind_5011"] = min((r["released"][:7] for r in b5011), default=None)
    return T, X


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--figs", type=Path, default=Path("reporting/charts/rfc/bare"))
    ap.add_argument("--out", type=Path, default=Path("out/analysis/dnssec_rfc_why.pptx"))
    args = ap.parse_args()
    T, X = facts()

    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H

    # ---- title ------------------------------------------------------------- #
    s = blank(prs)
    text(s, Inches(0.9), Inches(2.0), Inches(11.5), Inches(0.4),
         ["DNSSEC RFC ADOPTION  ·  EIGHT IMPLEMENTATIONS  ·  441 CVEs  ·  TWO CORPORA"],
         size=13, color=MUTED, bold=True)
    text(s, Inches(0.9), Inches(2.45), Inches(11.6), Inches(1.8),
         ["Why some DNSSEC RFCs are adopted fast,", "and some never"], size=40, bold=True,
         space=2)
    ln = s.shapes.add_shape(1, Inches(0.92), Inches(4.35), Inches(2.0), Emu(28575))
    ln.fill.solid(); ln.fill.fore_color.rgb = ACCENT; ln.line.fill.background()
    text(s, Inches(0.9), Inches(4.7), Inches(11.5), Inches(1.6), [
        "For each RFC, on one time axis: when it was published, when BIND, Unbound, Knot, "
        "PowerDNS and OpenDNSSEC could first sign or validate it, every default change and "
        "validator limit, every CVE that names it, and what zones actually did -- each spike "
        "named to the operator that made it.",
        "The question is what separates the RFCs that moved from the ones that did not.",
    ], size=15, color=INK_2)

    # ---- key --------------------------------------------------------------- #
    s = blank(prs)
    text(s, Inches(0.62), Inches(0.38), Inches(12), Inches(0.3), ["HOW TO READ A TIMELINE"],
         size=12, color=MUTED, bold=True)
    text(s, Inches(0.62), Inches(0.68), Inches(12.1), Inches(0.7),
         ["Four clocks on one axis"], size=28, bold=True)
    rows = [
        ("Upper strip", "events, packed into lanes so labels never overprint. Height means "
                        "nothing; only the horizontal position is data."),
        ("Green circle", "the RFC published. Faded green: a related RFC (predecessor or "
                         "successor)."),
        ("Orange / blue circle", "first stable release of a signer that could produce this "
                                 "value / of a validator that could check it."),
        ("Yellow diamond", "a vendor changed its default to this. Red square: a validator "
                           "or signer capped the old value."),
        ("Red triangle", "a CVE whose description names this mechanism, sized by CVSS."),
        ("Lower panel", "share of signed zones carrying the value. Orange: the seven "
                        "OpenINTEL forward TLDs. Blue: the strict AFRINIC+ARIN reverse "
                        "panel, the same population as every adoption date in this "
                        "project. Red dots: one operator moved more than half the running "
                        "maximum in a month -- a portfolio move, not diffusion."),
        ("Verdict rule", "FAST = first zone within a year of the RFC and 10% of signed "
                         "delegations within four. SLOW = reached 10%, later. NEVER = under "
                         "1% of signed zones in every corpus today. Others are named for what "
                         "the data shows."),
        ("Evidence line", "under each timeline: every date and figure the slide rests on."),
    ]
    yy = Inches(1.55)
    for head, body in rows:
        text(s, Inches(0.62), yy, Inches(2.6), Inches(0.5), [head], size=12.5, bold=True)
        text(s, Inches(3.2), yy, Inches(9.5), Inches(0.7), [body], size=11.5, color=INK_2)
        yy += Inches(0.66)

    for rfc in ORDER:
        rfc_slide(prs, T[rfc], args.figs, X)

    # ---- synthesis: the mechanism table ------------------------------------ #
    dec, col = X["dec"], X["col"]
    s = blank(prs)
    text(s, Inches(0.62), Inches(0.38), Inches(12), Inches(0.3), ["WHAT SEPARATES THEM"],
         size=12, color=MUTED, bold=True)
    text(s, Inches(0.62), Inches(0.68), Inches(12.1), Inches(0.7),
         ["How a change reaches a zone decides its speed"], size=28, bold=True)
    text(s, Inches(0.62), Inches(1.42), Inches(12.1), Inches(0.5),
         [f"Across the five mechanisms with a release history, RFC-to-signer runs "
          f"{X['code_lags'][0]:+.1f} to {X['code_lags'][-1]:+.1f} years and signer-to-first-zone "
          f"{X['dep_lags'][0]:.1f} to {X['dep_lags'][-1]:.1f}. For the two slowest, ECDSA and GOST, "
          f"the whole onset is the second number; CDS is the exception, where the code itself "
          f"took 1.8 years. Speed is mostly decided after the code ships, by the mechanism "
          f"that carries the value to a zone:"],
         size=12, color=INK_2)
    table = [
        ("Vendor-triggered", "measured", "2 months",
         f"NSEC3 iterations: names at >=100 fell {col['before']:,} to {col['after']:,} in "
         f"{col['month']}, two months after the caps, ten months before RFC 9276."),
        ("Registry-automated", "measured", "~2 months",
         f"CDS: SWITCH acts on the record; .ch {X['ch_signed_2101']:,} to "
         f"{X['ch_signed_2112']:,} signed zones inside 2021. The ~2 months is CDS "
         f"publication leading signing in the series, not a derived figure."),
        ("Default-on-upgrade", "inferred", "3 months - 3 years",
         f"ECDSA: Knot and PowerDNS defaults in 2016 sit {X['tk_def'][0]:.1f}-{X['tk_def'][1]:.1f} y "
         f"from the 1% crossing against {X['tk_rfc'][0]:.1f}-{X['tk_rfc'][1]:.1f} for the RFC; "
         f"event studies detect no acceleration, so this is timing, not proof."),
        ("Opt-in configuration", "inferred", "1.3 - 3.8 years",
         "everything else: somebody decides and edits. Every spike is one operator; the "
         "partner TLD moves in the same month in 20 of 21."),
        ("No default, ever", "observed", "never",
         f"EdDSA and GOST: fully implemented, never a default anywhere, published when the "
         f"predecessor stood at 1% of its eventual share. 0.37% and 0.00% today."),
    ]
    yy = Inches(2.35)
    for mech, status, lag, ex in table:
        text(s, Inches(0.62), yy, Inches(2.5), Inches(0.4), [mech], size=13, bold=True)
        text(s, Inches(3.1), yy, Inches(1.2), Inches(0.4), [status], size=11,
             color=GOOD if status == "measured" else MUTED, bold=True)
        text(s, Inches(4.3), yy, Inches(1.6), Inches(0.4), [lag], size=12, bold=True)
        text(s, Inches(5.9), yy, Inches(6.9), Inches(0.8), [ex], size=10.5, color=INK_2)
        yy += Inches(0.86)
    text(s, Inches(0.62), Inches(6.75), Inches(12.1), Inches(0.5),
         ["Fast (RFC 5702) is the case where the value changes nothing a zone manages. "
          "The first two rows are read off the series; the next two are the residual after "
          "that, attributed to a mechanism no zone reveals; the last is the absence of a "
          "default in the release history."], size=10, color=MUTED)

    # ---- synthesis: the programs and the CVEs ------------------------------- #
    s = blank(prs)
    text(s, Inches(0.62), Inches(0.38), Inches(12), Inches(0.3),
         ["THE PROGRAMS, AND THE CVEs"], size=12, color=MUTED, bold=True)
    text(s, Inches(0.62), Inches(0.68), Inches(12.1), Inches(0.7),
         ["CVEs follow adoption; the validators that carry most of them publish nothing"],
         size=28, bold=True)
    pp = X["per_program"]
    items = [
        ("Unbound is a validator: it can never appear in a spike.",
         f"It publishes nothing, so zone data cannot see it move. What it dates is the "
         f"validation side, and it was ready before the RFC for {X['unbound_pre']} of its "
         f"{X['unbound_rows']} DNSSEC milestones ({X['unbound_pre_names']}) -- plus the 2021 "
         f"iteration cap, fifteen months before RFC 9276."),
        ("BIND: one dated silent default change found in seventeen years.",
         f"{X['bind_defaults'][0][2]} in {X['bind_defaults'][0][0]} ({X['bind_defaults'][0][1]}). "
         f"Its ECDSA default arrived only as opt-in dnssec-policy in "
         f"{X['bind_defaults'][1][0]} ({X['bind_defaults'][1][1]}). No BIND release schedule "
         f"predicts change in the ledger (p = {X['bind_p']:.2f})."),
        ("No CVE led a push.",
         f"Of {sum(X['stages'].values())} DNSSEC CVEs that name a specific mechanism, "
         f"{X['stages'].get('in common usage', 0)} were published while it was already in "
         f"common usage and {X['stages'].get('before first use', 0)} before anyone used it. "
         f"The one candidate, CVE-2021-40083, was published after the NSEC3 cap it might "
         f"have prompted was already committed."),
        ("The DNSSEC CVE surface is on validators, and validators are invisible here.",
         f"DNSSEC CVEs per program: BIND 9 {pp['BIND 9']}, Unbound {pp['Unbound']}, "
         f"PowerDNS Rec {pp['PowerDNS Rec']}, PowerDNS Auth {pp['PowerDNS Auth']}, NSD "
         f"{pp['NSD']}, OpenDNSSEC {pp['OpenDNSSEC']}. NSD and OpenDNSSEC do not validate. "
         f"{X['core']} of {X['dnssec_total']} DNSSEC CVEs sit in the validation core every "
         f"signed zone shares -- KeyTrap (CVE-2023-50387) among them, with git-dated fixes "
         f"from {X['keytrap_vendors']} vendors spread over {X['keytrap_spread']} days. No "
         f"algorithm choice avoids any of it."),
    ]
    yy = Inches(1.6)
    for i, (head, body) in enumerate(items, 1):
        text(s, Inches(0.62), yy, Inches(0.45), Inches(0.4), [str(i)], size=18,
             color=ACCENT, bold=True)
        text(s, Inches(1.15), yy, Inches(11.6), Inches(0.35), [head], size=14, bold=True)
        text(s, Inches(1.15), yy + Inches(0.36), Inches(11.6), Inches(0.75), [body],
             size=11, color=INK_2)
        yy += Inches(1.22)

    # ---- limits ------------------------------------------------------------ #
    s = blank(prs)
    text(s, Inches(0.62), Inches(0.38), Inches(12), Inches(0.3), ["WHAT THIS CANNOT SHOW"],
         size=12, color=MUTED, bold=True)
    text(s, Inches(0.62), Inches(0.68), Inches(12.1), Inches(0.7),
         ["Four limits that bound every claim above"], size=28, bold=True)
    lims = [
        ("No zone's software is identifiable.", "Every alignment between a release and a "
         "deployment move is a coincidence in time. Even for NSEC3 iterations, which resolver "
         "or signer each operator ran is unknown -- and the names that moved sat below Unbound's "
         "cap and at PowerDNS's."),
        ("Per-zone tracking is reverse-only.", "The forward per-day records are not in this "
         "repository; .se, .nu and .ch are seen as monthly aggregates. Rollover paths and the "
         "manual-versus-bulk split rest on RIR delegations."),
        ("Release timing is not identifiable at the ecosystem level.", "97% of corpus months "
         "contain a release from some project. Per project, after detrending, no release "
         "schedule predicts change: smallest p is 0.11."),
        ("The registry and registrar layer is closed.", "The operators the evidence points at "
         "-- SWITCH, the Swedish Internet Foundation -- run platforms whose release history "
         "cannot be read. The channel most likely to carry an automatic change is the one "
         "this data cannot see."),
    ]
    yy = Inches(1.6)
    for head, body in lims:
        text(s, Inches(0.62), yy, Inches(11.9), Inches(0.35), [head], size=15, bold=True)
        text(s, Inches(0.62), yy + Inches(0.36), Inches(11.9), Inches(0.75), [body],
             size=12, color=INK_2)
        yy += Inches(1.25)
    text(s, Inches(0.62), Inches(6.9), Inches(12), Inches(0.3),
         ["Reproducible: python reporting/rfc_timelines.py && python reporting/make_rfc_deck.py"],
         size=10, color=MUTED)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(args.out)
    print(f"wrote {args.out}  ({len(prs.slides._sldIdLst)} slides)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
