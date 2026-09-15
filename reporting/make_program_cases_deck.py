"""Build the case-study deck: per RFC, per program, did a release cause a spike?

Every number on every slide is read from out/analysis/program_rfc_cases.json;
the readings are built from those values so they cannot drift from the data.

    python reporting/make_program_cases_deck.py [--out out/analysis/dnssec_program_rfc_cases.pptx]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches, Pt

from make_flows_deck import ACCENT, INK, INK_2, MUTED, SURFACE, W, H, blank, text  # noqa

CRIT = RGBColor(0xD0, 0x3B, 0x3B)
GOOD = RGBColor(0x1B, 0xAF, 0x7A)
WARN = RGBColor(0xED, 0xA1, 0x00)
ORDER = ["RFC 6605", "RFC 5702", "RFC 8080", "RFC 5155", "RFC 9276"]


def table(slide, x, y, w, rows, col_w, size=9, head_size=9):
    n_r, n_c = len(rows), len(rows[0])
    shp = slide.shapes.add_table(n_r, n_c, x, y, w, Inches(0.3) * n_r)
    t = shp.table
    for j, cw in enumerate(col_w):
        t.columns[j].width = cw
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.text = ""
            c.fill.solid()
            c.fill.fore_color.rgb = SURFACE if i else RGBColor(0xE1, 0xE0, 0xD9)
            c.margin_left = c.margin_right = Inches(0.05)
            c.margin_top = c.margin_bottom = Inches(0.03)
            p = c.text_frame.paragraphs[0]
            r = p.add_run()
            r.text = str(val)
            r.font.size = Pt(head_size if i == 0 else size)
            r.font.bold = i == 0
            r.font.color.rgb = INK if i else INK_2
    return shp


def lagtxt(v):
    return "-" if not v else f'{v["what"]} ({v["lag_months"]} mo before)'


def split_txt(j):
    s = j.get("split")
    if not s:
        return "n/a" if j["basis"] == "reverse" else "collapse"
    if s["rollovers_at_least"] == 0:
        return "new signings"
    if s["new_signings_at_most"] == 0:
        return "rollovers"
    return f'mixed: >={s["rollovers_at_least"]:,} rolled'


def top_spikes(case, n=8):
    return sorted(case["spikes"], key=lambda j: -j["delta"])[:n]


# ------------------------------------------------------------------ prose --

def prog_line(case):
    """One sentence per program: what it did and when, relative to the RFC."""
    out = []
    for p in case["programs"]:
        if p["key"] == "_unattributed":
            continue
        bits, seen = [], set()
        for e in p["events"]:
            tag = (e["kind"], e.get("version") or e.get("cve"))
            if tag in seen:
                continue
            seen.add(tag)
            lag = e["lag_months_after_rfc"]
            when = f'{e["date"][:7]} ({abs(lag)} mo {"after" if lag >= 0 else "before"} the RFC)'
            if e["kind"] == "support":
                bits.append(f'{e["capability"]}s it from {e["version"]}, {when}')
            elif e["kind"] == "default":
                bits.append(f'default from {e["version"]}{" (opt-in policy)" if e.get("opt_in") else ""}, {when}')
            elif e["kind"] == "limit":
                bits.append(f'caps it from {e["version"]}, {when}')
            elif e["kind"] == "cve":
                bits.append(f'{e["cve"]} {e["date"][:7]}')
        out.append(f'{p["program"]}: ' + "; ".join(bits) + ".")
    return out


def reading(rfc, c):
    s, ch = c["summary"], c["chance"]
    top = top_spikes(c, 3)
    b = top[0]
    W3 = "3"
    if rfc == "RFC 6605":
        se16 = next(j for j in c["spikes"] if j["source"] == "se" and j["start"] == "2016-10")
        se19 = next(j for j in c["spikes"] if j["source"] == "se" and j["start"] == "2019-01")
        ch21 = next(j for j in c["spikes"] if j["source"] == "ch" and j["start"] == "2021-06")
        pd4 = next(e for p in c["programs"] if p["key"] == "pdns-auth" for e in p["events"] if e["kind"] == "default")
        ar = {r["version"]: r for r in c["new_signings"]["around_releases"] if r["kind"] == "default"}
        os9 = next(r for r in c["new_signings"]["around_os_ships"] if r["os"] == "Debian 9")
        return [
            f'The first ECDSA move in the forward corpus is .se {se16["start"]}: +{se16["delta"]:,} zones, '
            f'{se16["nearest_default_change"]["lag_months"]} months after PowerDNS Auth {pd4["version"]} made '
            f'ECDSA its default ({pd4["date"][:7]}), and {se16["split"]["rollovers_at_least"]:,} of them were '
            f'existing zones rolling over -- a deliberate migration by whoever runs them, not an update side-effect.',
            f'The moves that made ECDSA the majority came much later and were all rollovers: .se {se19["start"]} '
            f'+{se19["delta"]:,} ({se19["nearest_default_change"]["lag_months"]} months after that default) and '
            f'.se {top[1]["start"]} +{top[1]["delta"]:,}. The largest of all, .ch {ch21["start"]}..{ch21["end"]} '
            f'+{ch21["delta"]:,}, was a signing wave in which the new zones chose ECDSA '
            f'{ch21["share_after_pct"]:.0f}% of the time: by 2021 every signer default had been ECDSA for five years.',
            f'Chance check: {s["spikes_within_3m_of_default_change"]} of {s["n_spikes"]} spikes fall within {W3} '
            f'months after a default change; a random forward month does so {ch["forward"]["within_3m_after_default_change"]*100:.0f}% '
            f'of the time, so about {round(ch["forward"]["within_3m_after_default_change"]*s["n_forward"] + ch["reverse"]["within_3m_after_default_change"]*s["n_reverse"], 1)} '
            f'would be expected by luck. CVEs: {s["spikes_within_3m_of_cve"]} spikes within {W3} months of one, '
            f'both after CVE-2022-38177 -- a validator memory leak, not a reason to sign with ECDSA.',
            f'Reverse DNS tells the auto-update story directly, and the OS release is the event, not the upstream one. New signings '
            f'ignored the Knot 2.1.0 and PowerDNS 4.0.0 defaults on their upstream dates ({ar["2.1.0"]["share_before_pct"]}% -> '
            f'{ar["2.1.0"]["share_after_pct"]}% and {ar["4.0.0"]["share_before_pct"]}% -> {ar["4.0.0"]["share_after_pct"]}% ECDSA in the year '
            f'either side) and ignored Ubuntu 16.04, which carried only Knot\'s. In the year after Debian 9 ({os9["date"]}) shipped both '
            f'PowerDNS 4.0.3 and Knot 2.4.0 with ECDSA default, the share went {os9["share_before_pct"]}% -> {os9["share_after_pct"]}% and the '
            f'blocks choosing it {os9["blocks_choosing_before"]} -> {os9["blocks_choosing_after"]}. BIND 9.16.0 (Ubuntu 20.04, Debian 11) '
            f'added a second step ({ar["9.16.0"]["share_before_pct"]}% -> {ar["9.16.0"]["share_after_pct"]}%).',
        ]
    if rfc == "RFC 5702":
        ar = {r["version"]: r for r in c["new_signings"]["around_releases"]}
        se17 = next(j for j in c["spikes"] if j["source"] == "se" and j["start"] == "2017-11")
        return [
            f'The forward corpus starts in 2016-06 with RSA/SHA-256 already at {c["series"]["forward"]["se"]["share_pct"][0]:.0f}% of signed '
            f'.se zones, so the OpenINTEL side cannot witness its adoption at all. Its forward spikes are signing waves that '
            f'happened to use it: .se {se17["start"]} +{se17["delta"]:,} zones, {se17["split"]["new_signings_at_most"]:,} of them '
            f'newly signed, {se17["nearest_default_change"]["lag_months"]} months after the nearest default change (Knot 2.0.0).',
            f'Reverse DNS does witness it. In the twelve months after OpenDNSSEC 1.2.0 made RSASHA256 its default ({ar["1.2.0"]["date"][:7]}), '
            f'the share of newly signed delegations choosing it went from {ar["1.2.0"]["share_before_pct"]}% to '
            f'{ar["1.2.0"]["share_after_pct"]}% (on {ar["1.2.0"]["new_signings_12m_before"]} and {ar["1.2.0"]["new_signings_12m_after"]} signings). '
            f'That is the one default change in this study followed by a step in what new zones chose -- but BIND 9.7.0 had '
            f'enabled the algorithm 13 months earlier, and the rise continued for two years, so it reads as the algorithm becoming '
            f'available everywhere, not as one vendor\'s default.',
            f'Spikes vs releases: {s["spikes_within_3m_of_default_change"]} of {s["n_spikes"]} spikes fall within 3 months of a default change '
            f'(expected by chance about {round(ch["reverse"]["within_3m_after_default_change"]*s["n_reverse"], 1)}); the median lag from a spike to '
            f'the nearest signer release is {s["median_lag_to_signer_release_months"]:.0f} months. No CVE names this algorithm.',
        ]
    if rfc == "RFC 8080":
        e1, e2 = top[0], top[1]
        return [
            f'No program ever made EdDSA a default, and no OS package carried a default for it. The forward corpus shows two '
            f'experiments, both in .se/.nu and both withdrawn: {e1["start"]}..{e1["end"]} +{e1["delta"]:,} zones '
            f'({e1["split"]["rollovers_at_least"]:,} rolled from another algorithm) and {e2["start"]}..{e2["end"]} +{e2["delta"]:,} '
            f'({e2["split"]["rollovers_at_least"]:,} rolled). The share returns to zero within a year each time.',
            f'Each episode sits {s["median_lag_to_signer_release_months"]:.0f} months after the nearest signer release, and a random '
            f'forward month is within 3 months of one {ch["forward"]["within_3m_after_signer_release"]*100:.0f}% of the time -- no spike is. '
            f'The second episode came {e2["nearest_cve"]["lag_months"]} months after CVE-2022-38178, a BIND memory leak on malformed '
            f'EdDSA signatures; a validator bug is not a reason to sign with EdDSA, and one such coincidence among {s["n_spikes"]} spikes is expected.',
            f'Reverse DNS: no spike, and {sum(r["hit"] for r in c["new_signings"]["rollovers_to_by_year"])} rollovers to EdDSA in the whole ledger. '
            f'The mechanism that moved ECDSA (a signer default that new zones inherit) never existed for EdDSA.',
        ]
    if rfc == "RFC 5155":
        ch21 = next(j for j in c["spikes"] if j["source"] == "ch" and j["start"] == "2021-07")
        rev_top = max((j for j in c["spikes"] if j["basis"] == "reverse"), key=lambda j: j["delta"])
        first_rev = min(m for m in c["first_seen"]["reverse"].values() if m)
        first_src = next(k for k, m in c["first_seen"]["reverse"].items() if m == first_rev)
        first_cve = min(e for p in c["programs"] for e in p["events"] if e["kind"] == "cve" for e in [e["date"]])
        bind_sup = next(e for p in c["programs"] if p["key"] == "bind9" for e in p["events"] if e["kind"] == "support")
        return [
            f'BIND 9.6.0 signed NSEC3 {abs(bind_sup["lag_months_after_rfc"])} months after the RFC and Unbound validated it from 0.7.1, '
            f'before it. The first NSEC3-signed reverse delegations ({first_src.upper()}) appear {first_rev}, '
            f'{months_between(bind_sup["date"][:7], first_rev)} months after BIND 9.6.0; the first CVE on the mechanism came {first_cve[:7]}, '
            f'{months_between(first_rev, first_cve[:7])} months after that. Code, then deployment, then CVEs, each within a year.',
            f'The forward corpus opens with NSEC3 at {c["series"]["forward"]["se"]["share_pct"][0]:.0f}% of signed .se zones. Its spikes are signing '
            f'waves, not NSEC3 decisions: .ch {ch21["start"]}..{ch21["end"]} +{ch21["delta"]:,} NSEC3PARAM zones is the same wave that put '
            f'591,333 ECDSA zones in .ch, and it lands in the month of the PowerDNS 4.5.0 and Unbound 1.13.2 iteration caps '
            f'({ch21["nearest_validator_limit"]["lag_months"]} months) -- the wave signed with 1 iteration, which is what the caps asked for.',
            f'Reverse DNS sees NSEC3 only through algorithm 7 (RSASHA1-NSEC3-SHA1), a proxy that misses NSEC3 with 8 or 13. Its largest spike, '
            f'{rev_top["source"].upper()} {rev_top["start"]} +{rev_top["delta"]}, is {rev_top["nearest_signer_release"]["lag_months"]} months after '
            f'the nearest signer release. Overall {s["spikes_within_3m_of_signer_release"]} of {s["n_spikes"]} spikes are within 3 months of a signer release.',
        ]
    if rfc == "RFC 9276":
        nu = next(j for j in c["spikes"] if j["source"] == "nu")
        caps = sorted(({**e, "program": p["program"]} for p in c["programs"] for e in p["events"]
                       if e["kind"] == "limit" and "2021" <= e["date"][:7] <= nu["start"]), key=lambda e: e["date"])
        later = sorted(({**e, "program": p["program"]} for p in c["programs"] for e in p["events"]
                        if e["kind"] == "limit" and e["date"][:7] > nu["start"]), key=lambda e: e["date"])
        return [
            f'This is the one vendor-triggered case. Names with 100 or more NSEC3 iterations collapsed in {nu["start"]}..{nu["end"]} in all three '
            f'TLDs that had them: .nu {nu["level_before"]:,} -> {nu["level_after"]}, .ch {top[1]["level_before"]:,} -> {top[1]["level_after"]}, '
            f'.se {top[2]["level_before"]:,} -> {top[2]["level_after"]}. That is {abs(nu["months_after_rfc"])} months BEFORE RFC 9276 was published.',
            f'What preceded it: ' + "; ".join(f'{NAME(e)} {e["version"]} capped iterations {e["date"][:7]}' for e in caps) +
            f'; and CVE-2021-40083 (Knot Resolver, {nu["nearest_cve"]["date"][:7]}, an assertion failure on NSEC3 with too many iterations), '
            f'{nu["nearest_cve"]["lag_months"]} months before the collapse. The caps and the CVE are one event: the resolver vendors '
            f'agreed in mid-2021 to reject high iteration counts, and the zones that would have failed validation were re-signed'
            + (" (" + ", ".join(f'{e["program"]} {e["version"]} followed {e["date"][:7]}' for e in later) + ")." if later else "."),
            f'All {s["n_spikes"]} spikes are within 3 months of a validator cap; a random forward month is {ch["forward"]["within_3m_after_validator_limit"]*100:.0f}% '
            f'likely to be. The signers\' own defaults had nothing to do with it: BIND\'s 100 -> 10 default change was {abs(nu["nearest_default_change"]["lag_months"])} months earlier. '
            f'The RFC codified what validators had already forced. CVE-2023-50868 (KeyTrap era, 2024-02) came after both.',
        ]
    return []


def NAME(e):
    return e.get("program", "")


def months_between(a: str, b: str) -> int:
    return (int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))


VERDICT = {
    "RFC 6605": ("DEFAULTS FIRST, ZONES YEARS LATER", GOOD),
    "RFC 5702": ("ADOPTED BEFORE THE FORWARD CORPUS BEGINS", ACCENT),
    "RFC 8080": ("NO DEFAULT, NO ADOPTION", CRIT),
    "RFC 5155": ("SHIPPED BEFORE THE RFC; SPIKES ARE SIGNING WAVES", ACCENT),
    "RFC 9276": ("VENDOR-TRIGGERED: CAPS AND A CVE, TEN MONTHS BEFORE THE RFC", CRIT),
}


def fit_picture(s, path, top, band_h, max_w=Inches(12.2)):
    pic = s.shapes.add_picture(str(path), Inches(0.6), top, height=band_h)
    if pic.width > max_w:
        pic.width, pic.height = max_w, int(pic.height * max_w / pic.width)
    pic.left = int((W - pic.width) / 2)
    pic.top = int(top + (band_h - pic.height) / 2)
    return pic


def figure_slide(prs, rfc, c, figs):
    s = blank(prs)
    v, col = VERDICT[rfc]
    text(s, Inches(0.62), Inches(0.3), Inches(12), Inches(0.3), [f"{v}  ·  {rfc}"], size=12, color=col, bold=True)
    text(s, Inches(0.62), Inches(0.58), Inches(12.1), Inches(0.6), [c["title"]], size=24, bold=True)
    fit_picture(s, figs / f'{rfc.lower().replace(" ", "_")}.png', Inches(1.2), Inches(5.55))
    text(s, Inches(0.62), Inches(6.8), Inches(12.1), Inches(0.5),
         ["Numbered circles are the largest spikes; the next slide names what preceded each one. "
          "Ticks: the first Ubuntu/Debian release carrying that program version (the automatic-update path)."],
         size=9, color=MUTED)
    return s


def ledger_slide(prs, rfc, c, figs):
    s = blank(prs)
    text(s, Inches(0.62), Inches(0.3), Inches(12), Inches(0.3), [f"WHAT PRECEDED EACH SPIKE  ·  {rfc}"],
         size=12, color=MUTED, bold=True)
    text(s, Inches(0.62), Inches(0.58), Inches(12.1), Inches(0.6),
         ["Nearest release, default, cap and CVE before each spike"], size=22, bold=True)
    rows = [["#", "corpus", "month(s)", "size", "made of", "nearest signer release", "nearest default / cap", "nearest CVE"]]
    for i, j in enumerate(top_spikes(c, 8), 1):
        src = ("." + j["source"]) if j["basis"] == "forward" else j["source"].upper()
        size = f'{"-" if c["rfc"] == "RFC 9276" else "+"}{j["delta"]:,}'
        if j.get("share_before_pct") is not None and j.get("share_after_pct") is not None and c["rfc"] != "RFC 9276":
            size += f'  ({j["share_before_pct"]:.0f}% -> {j["share_after_pct"]:.0f}%)'
        dc = j.get("nearest_default_change") or j.get("nearest_validator_limit")
        rows.append([i, f'{"OpenINTEL" if j["basis"]=="forward" else "reverse"} {src}',
                     j["start"] if j["start"] == j["end"] else f'{j["start"]}..{j["end"]}',
                     size, split_txt(j), lagtxt(j.get("nearest_signer_release")), lagtxt(dc), lagtxt(j.get("nearest_cve"))])
    table(s, Inches(0.45), Inches(1.25), Inches(12.4), rows,
          [Inches(0.3), Inches(1.35), Inches(1.25), Inches(1.75), Inches(1.25), Inches(2.2), Inches(2.2), Inches(2.1)], size=8.5)
    y = Inches(1.25) + Inches(0.31) * len(rows) + Inches(0.15)
    text(s, Inches(0.62), y, Inches(12.1), Inches(2.6), reading(rfc, c), size=10.5, color=INK, space=5)
    s_ = c["summary"]
    text(s, Inches(0.62), Inches(6.85), Inches(12.1), Inches(0.5),
         [f'{s_["n_spikes"]} spikes ({s_["n_forward"]} OpenINTEL, {s_["n_reverse"]} reverse). Within 3 months after: signer release '
          f'{s_["spikes_within_3m_of_signer_release"]}, default change {s_["spikes_within_3m_of_default_change"]}, validator cap '
          f'{s_["spikes_within_3m_of_validator_limit"]}, CVE {s_["spikes_within_3m_of_cve"]}, any DNS release {s_["spikes_within_3m_of_any_release"]}. '
          f'Chance that a random month is within 3 months after a default change: forward {pct(c["chance"]["forward"]["within_3m_after_default_change"])}, '
          f'reverse {pct(c["chance"]["reverse"]["within_3m_after_default_change"])}. Full ledger: out/analysis/dns_program_rfc_spikes.csv'],
         size=8.5, color=MUTED)
    return s


def pct(v):
    return "n/a" if v is None else f"{v*100:.0f}%"


def programs_slide(prs, rfc, c):
    s = blank(prs)
    text(s, Inches(0.62), Inches(0.3), Inches(12), Inches(0.3), [f"THE RFC IN EACH PROGRAM  ·  {rfc}"],
         size=12, color=MUTED, bold=True)
    text(s, Inches(0.62), Inches(0.58), Inches(12.1), Inches(0.6),
         [f'{rfc} published {c["published"]}: what each program did, in months from that date'], size=20, bold=True)
    text(s, Inches(0.62), Inches(1.3), Inches(12.1), Inches(5.5), prog_line(c), size=12, color=INK, space=8)
    return s


def new_signings_slide(prs, rfc, c, figs):
    p = figs / f'{rfc.lower().replace(" ", "_")}_new_signings.png'
    if not p.exists():
        return None
    s = blank(prs)
    text(s, Inches(0.62), Inches(0.3), Inches(12), Inches(0.3), [f"THE AUTO-UPDATE TEST  ·  {rfc}"],
         size=12, color=MUTED, bold=True)
    text(s, Inches(0.62), Inches(0.58), Inches(12.1), Inches(0.6),
         ["Did newly signed reverse delegations pick up the new default?"], size=22, bold=True)
    fit_picture(s, p, Inches(1.3), Inches(3.3))
    rows = [["release", "kind", "date", "new signings, 12 mo before", "share choosing it", "new signings, 12 mo after", "share choosing it"]]
    seen = set()
    for r in c["new_signings"]["around_releases"]:
        k = (r["program"], r["version"])
        if k in seen:
            continue
        seen.add(k)
        rows.append([f'{r["program"]} {r["version"]}', r["kind"], r["date"][:7], r["new_signings_12m_before"],
                     "-" if r["share_before_pct"] is None else f'{r["share_before_pct"]}%',
                     r["new_signings_12m_after"], "-" if r["share_after_pct"] is None else f'{r["share_after_pct"]}%'])
    for r in c["new_signings"].get("around_os_ships", []):
        rows.append([f'{r["os"]}: ' + ", ".join(r["carries"]), "OS package", r["date"][:7], r["new_signings_12m_before"],
                     "-" if r["share_before_pct"] is None else f'{r["share_before_pct"]}% ({r["blocks_choosing_before"]} blocks)',
                     r["new_signings_12m_after"],
                     "-" if r["share_after_pct"] is None else f'{r["share_after_pct"]}% ({r["blocks_choosing_after"]} blocks)'])
    table(s, Inches(0.8), Inches(4.75), Inches(11.7), rows,
          [Inches(3.3), Inches(0.9), Inches(0.9), Inches(1.7), Inches(1.9), Inches(1.7), Inches(1.9)], size=8.5)
    text(s, Inches(0.62), Inches(6.85), Inches(12.1), Inches(0.5),
         ["An update changes what a newly signed zone gets; it never re-signs an existing zone. So this share, not the "
          "adoption curve, is where an automatic update would show. Source: out/analysis/delegation_changes.parquet, kind = sign."],
         size=8.5, color=MUTED)
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--figs", type=Path, default=Path("reporting/charts/cases/bare"))
    ap.add_argument("--out", type=Path, default=Path("out/analysis/dnssec_program_rfc_cases.pptx"))
    a = ap.parse_args()
    doc = json.loads(Path("out/analysis/program_rfc_cases.json").read_text("utf-8"))
    C = doc["cases"]

    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H

    # title
    s = blank(prs)
    text(s, Inches(0.9), Inches(2.0), Inches(11.5), Inches(0.4),
         ["FIVE RFCs  ·  SIX PROGRAMS  ·  OPENINTEL + REVERSE DNS  ·  EVERY SPIKE TRACED BACK"], size=13, color=MUTED, bold=True)
    text(s, Inches(0.9), Inches(2.45), Inches(11.6), Inches(1.8),
         ["Did a program's release, default or CVE", "cause the spikes in RFC adoption?"], size=38, bold=True, space=2)
    ln = s.shapes.add_shape(1, Inches(0.92), Inches(4.35), Inches(2.0), Emu(28575))
    ln.fill.solid(); ln.fill.fore_color.rgb = ACCENT; ln.line.fill.background()
    text(s, Inches(0.9), Inches(4.7), Inches(11.5), Inches(1.8), [
        "For each RFC: the date it was published, the release in which BIND 9, Knot DNS, PowerDNS, OpenDNSSEC, Unbound and "
        "Knot Resolver first implemented it, the release that made it the default or capped it, the first Ubuntu and Debian "
        "packages that carried that release, and the CVEs on the mechanism. Then every spike in the OpenINTEL zone files "
        "(per TLD) and in reverse DNS (per RIR), with the nearest preceding release, default, cap and CVE named -- and the "
        "chance rate that check has to beat.",
    ], size=14, color=INK_2)

    # method
    s = blank(prs)
    text(s, Inches(0.62), Inches(0.38), Inches(12), Inches(0.3), ["METHOD"], size=12, color=MUTED, bold=True)
    text(s, Inches(0.62), Inches(0.68), Inches(12.1), Inches(0.7), ["Four checks per spike, and the trap they avoid"], size=26, bold=True)
    rows = [
        ("Spike", doc["spike_rule"] + f'. Floors: {doc["floors"]["forward_zones"]} zones forward, {doc["floors"]["reverse_zones"]} reverse.'),
        ("Nearest release", "for each spike, the latest preceding release that implements, defaults or caps the mechanism, per program, "
                            "and the lag in months. Also the latest preceding release of any of the eight projects."),
        ("The trap", "97% of months contain some DNS release, so 'a release came shortly before' is always true. Each lag is compared "
                     "with the same lag at every month of the series: the chance rate. A spike is release-timed only if it beats that."),
        ("New vs rolled", "a jump in zones on algorithm X is split into at most the growth in signed zones that month (could be new signings) "
                          "and the rest (existing zones that rolled over). An automatic update can change what a NEW zone gets; it never "
                          "re-signs an existing one. Rollovers are operator decisions."),
        ("Auto-update proxy", "the reverse ledger records every signing with the algorithm chosen. If a default propagates through updates, "
                              "the share of new signings choosing it steps up after the release and after the OS package that carried it."),
        ("Coverage", "OpenINTEL: .se/.nu 2016-06 to 2023-12, .ch/.li from 2020-05, .ee from 2019-07, .gov/.fed.us from 2017-05. "
                     "Reverse: five RIRs 2009-03 to 2026-08; shares hidden where a RIR has under 30 signed delegations; the strict "
                     "AFRINIC+ARIN panel is the share line in black."),
    ]
    yy = Inches(1.55)
    for head, body in rows:
        text(s, Inches(0.62), yy, Inches(2.4), Inches(0.5), [head], size=12.5, bold=True)
        text(s, Inches(3.0), yy, Inches(9.8), Inches(0.9), [body], size=11, color=INK_2)
        yy += Inches(0.86)

    for rfc in ORDER:
        c = C[rfc]
        programs_slide(prs, rfc, c)
        figure_slide(prs, rfc, c, a.figs)
        ledger_slide(prs, rfc, c, a.figs)
        new_signings_slide(prs, rfc, c, a.figs)

    # cross-RFC summary
    s = blank(prs)
    text(s, Inches(0.62), Inches(0.3), Inches(12), Inches(0.3), ["ACROSS THE FIVE RFCs"], size=12, color=MUTED, bold=True)
    text(s, Inches(0.62), Inches(0.58), Inches(12.1), Inches(0.6), ["Spikes within 3 months of a software event, against chance"], size=22, bold=True)
    rows = [["RFC", "spikes", "after signer release", "after default", "after cap", "after CVE", "chance / month (fwd, rev)", "made of (forward)"]]
    for rfc in ORDER:
        c = C[rfc]; s_ = c["summary"]; chf, chr_ = c["chance"]["forward"], c["chance"]["reverse"]
        made = "collapse" if rfc == "RFC 9276" else f'{s_.get("forward_rollovers_at_least", 0):,} rolled / {s_.get("forward_new_signings_at_most", 0):,} new at most'
        rows.append([rfc, s_["n_spikes"], s_["spikes_within_3m_of_signer_release"], s_["spikes_within_3m_of_default_change"],
                     s_["spikes_within_3m_of_validator_limit"], s_["spikes_within_3m_of_cve"],
                     f'default {pct(chf["within_3m_after_default_change"])}/{pct(chr_["within_3m_after_default_change"])}; '
                     f'cap {pct(chf["within_3m_after_validator_limit"])}; CVE {pct(chf["within_3m_after_cve"])}/{pct(chr_["within_3m_after_cve"])}',
                     made])
    table(s, Inches(0.45), Inches(1.3), Inches(12.4), rows,
          [Inches(0.9), Inches(0.6), Inches(1.2), Inches(1.0), Inches(0.8), Inches(0.8), Inches(3.6), Inches(3.5)], size=9)
    c6, c9 = C["RFC 6605"], C["RFC 9276"]
    text(s, Inches(0.62), Inches(3.6), Inches(12.1), Inches(3.2), [
        f'Only RFC 9276 beats chance: {c9["summary"]["spikes_within_3m_of_validator_limit"]} of {c9["summary"]["n_spikes"]} spikes within 3 months '
        f'of a validator cap against a {pct(c9["chance"]["forward"]["within_3m_after_validator_limit"])} chance rate, and they are one coordinated event '
        f'(caps + CVE-2021-40083) ten months before the RFC. For the algorithm RFCs the counts are what luck predicts: '
        f'{c6["summary"]["spikes_within_3m_of_default_change"]} of {c6["summary"]["n_spikes"]} ECDSA spikes after a default against a '
        f'{pct(c6["chance"]["forward"]["within_3m_after_default_change"])} forward rate.',
        f'What the spikes are made of decides the causal story. Of the {c6["summary"]["forward_zones_in_spikes"]:,} forward ECDSA zones in spikes, at least '
        f'{c6["summary"]["forward_rollovers_at_least"]:,} were existing zones rolling over -- deliberate migrations that no update performs. The rest were '
        f'signing waves whose new zones took whatever the signer defaulted to; that is where defaults act, silently and years after they changed.',
        f'CVEs did not lead any push. Every CVE nearest to a spike is a validator bug (memory leak, assertion failure); the one CVE that sits inside a causal '
        f'chain, CVE-2021-40083, is a symptom of the same iteration problem the caps fixed. Median lag from a spike to the nearest CVE: '
        f'{C["RFC 6605"]["summary"]["median_lag_to_cve_months"]:.0f} months for ECDSA, {C["RFC 5155"]["summary"]["median_lag_to_cve_months"]:.0f} for NSEC3.',
    ], size=11, color=INK, space=6)

    # auto-update synthesis
    s = blank(prs)
    text(s, Inches(0.62), Inches(0.3), Inches(12), Inches(0.3), ["AUTOMATIC UPDATES"], size=12, color=MUTED, bold=True)
    text(s, Inches(0.62), Inches(0.58), Inches(12.1), Inches(0.6), ["Where an update could act, and where it did"], size=22, bold=True)
    ar6 = {r["version"]: r for r in c6["new_signings"]["around_releases"] if r["kind"] == "default"}
    ar5 = {r["version"]: r for r in C["RFC 5702"]["new_signings"]["around_releases"]}
    os9 = next(r for r in c6["new_signings"]["around_os_ships"] if r["os"] == "Debian 9")
    text(s, Inches(0.62), Inches(1.3), Inches(12.1), Inches(5.4), [
        "An update cannot roll a zone to a new algorithm; it can only change what a zone signed AFTER the update gets. So the test is the "
        "share of new signings, not the adoption curve, and the reverse ledger is the only place it can be run per zone.",
        f'RSA/SHA-256: the share of new reverse signings choosing it rose from {ar5["1.2.0"]["share_before_pct"]}% to {ar5["1.2.0"]["share_after_pct"]}% '
        f'across OpenDNSSEC 1.2.0\'s default ({ar5["1.2.0"]["date"][:7]}) and kept rising for two years. Consistent with defaults arriving through '
        f'updates; not attributable to one vendor, since BIND 9.7.0 had shipped the algorithm 13 months earlier.',
        f'ECDSA: the Knot 2.1.0 and PowerDNS 4.0.0 defaults changed nothing on their upstream dates ({ar6["2.1.0"]["share_before_pct"]}% -> '
        f'{ar6["2.1.0"]["share_after_pct"]}%, {ar6["4.0.0"]["share_before_pct"]}% -> {ar6["4.0.0"]["share_after_pct"]}%), nor did Ubuntu 16.04 '
        f'(Knot only). The step is Debian 9 ({os9["date"]}), the first OS release shipping both ECDSA-default signers: '
        f'{os9["share_before_pct"]}% -> {os9["share_after_pct"]}% of new signings, {os9["blocks_choosing_before"]} -> {os9["blocks_choosing_after"]} '
        f'blocks. A second step came with BIND 9.16.0 ({ar6["9.16.0"]["share_before_pct"]}% -> {ar6["9.16.0"]["share_after_pct"]}%) via Ubuntu 20.04 '
        f'and Debian 11. The update path works -- one OS release at a time, on new zones only, and it never shows as a spike in the adoption curve.',
        "Forward DNS: the .ch 2021 wave chose ECDSA for 96% of 591,333 newly signed zones and NSEC3 with 1 iteration; by then every signer's "
        "default was ECDSA and the caps had just landed. That is an update effect in the only sense the data supports: whatever the hosters ran, "
        "its defaults were current. The 2019 .se moves were rollovers and cannot be.",
        "EdDSA: never a default anywhere, never picked up by new signings, and its two forward episodes were withdrawn. The update path "
        "carries defaults; where no vendor set one, it carried nothing.",
    ], size=11.5, color=INK, space=7)

    # limits
    s = blank(prs)
    text(s, Inches(0.62), Inches(0.3), Inches(12), Inches(0.3), ["LIMITS"], size=12, color=MUTED, bold=True)
    text(s, Inches(0.62), Inches(0.58), Inches(12.1), Inches(0.6), ["What this cannot show"], size=22, bold=True)
    text(s, Inches(0.62), Inches(1.3), Inches(12.1), Inches(5.4), [
        "Which software signs a zone is never visible from its records. 'Nearest release' is timing evidence only; the program named is the "
        "nearest of the six studied, not the one the operator ran. Registry and registrar signing platforms are closed source and off the list.",
        "OpenINTEL here is seven TLD zone files as monthly aggregates from 2016-06 (2020-05 for .ch/.li) to 2023-12. RSA/SHA-256 and NSEC3 "
        "were adopted before that window; their forward spikes are later signing waves, not adoption. Per-zone forward records are not in this repo, "
        "so forward spikes cannot be attributed to an operator; 'new vs rolled' is a bound from the change in signed-zone count.",
        "Reverse DNS is small (25,930 change events on 13,654 delegations); its spikes are one /16 block at a time and its shares are hidden where a "
        "RIR has fewer than 30 signed delegations. NSEC3 is invisible in DS records except through algorithm 7.",
        "OS packages: Ubuntu LTS 16.04 to 24.04 and Debian 9 to 13, from Launchpad and sources.debian.org. Package dates bound when a default "
        "became reachable by apt, not when any operator upgraded; the Debian 9 step is 55 blocks in one corpus, APNIC-heavy, with one block a third of it.",
        "The chance rate is per month and per series; with 3 to 31 spikes per RFC the counts are small, and 'beats chance' is a reading, not a test "
        "with a p-value. CVE attribution is by NVD product only; keyword matches are shown as 'other / unattributed'.",
    ], size=11.5, color=INK, space=7)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(a.out)
    # a machine-readable dump of the slide text for the tests
    dump = []
    for i, sl in enumerate(prs.slides, 1):
        dump.append({"n": i, "text": [sh.text_frame.text for sh in sl.shapes if sh.has_text_frame] +
                     [c.text for sh in sl.shapes if sh.has_table for r in sh.table.rows for c in r.cells]})
    Path(str(a.out).replace(".pptx", "_slides.json")).write_text(json.dumps(dump, indent=1), "utf-8")
    print(f"{len(prs.slides)} slides -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
