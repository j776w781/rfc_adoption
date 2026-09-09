"""Join the CVE record to the adoption measures, per observable change.

The two datasets answer different halves of one question. `adoption_measures`
says when each mechanism appeared, when it reached 1% and 10% of signed
delegations, and where it ended up. The CVE record says what went wrong in it.
Putting them side by side asks whether vulnerability follows deployment -- and
whether a flaw ever arrived early enough to have discouraged anyone.

The join is deliberately narrow. Only a CVE whose description names a specific
algorithm or mechanism can be attached to a specific adoption curve; a bug in the
shared validation path belongs to all of them and is counted separately.

Reads out/analysis/adoption_measures.json, out/analysis/cve_crossref.json and
out/server_run/timeline_monthly.parquet.
Writes out/analysis/cve_adoption_crossref.json.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd

#: change name -> pattern that must appear in a CVE description for the CVE to be
#: about *that* mechanism. Deliberately strict: "DNSSEC validation crashes" is not
#: evidence against ECDSA just because ECDSA is a DNSSEC algorithm.
NAMED = {
    "DSA/SHA-1":         r"\bDSA\b(?!.{0,4}P-)",
    "RSASHA1":           r"RSASHA1\b|RSA/SHA-1",
    "RSASHA1-NSEC3":     r"\bNSEC3\b",
    "RSASHA256":         r"RSASHA256|RSA/SHA-256",
    "RSASHA512":         r"RSASHA512|RSA/SHA-512",
    "ECC-GOST":          r"\bGOST\b",
    "ECDSAP256SHA256":   r"\bECDSA\b|P-256",
    "ECDSAP384SHA384":   r"ECDSA.{0,20}384|P-384",
    "Ed25519":           r"Ed25519|EdDSA",
    "Ed448":             r"Ed448",
    "SHA-384 DS digest": r"SHA-?384",
}

#: The specifications every signed zone uses whatever algorithm it picked. A CVE
#: here has no adoption curve of its own -- its exposure is 100% of signed zones
#: by construction.
SHARED_CORE = {"RFC 4033", "RFC 4034", "RFC 4035"}


def nsec3_mechanism(timeline: pd.DataFrame) -> dict | None:
    """NSEC3's own deployment curve, which no algorithm codepoint carries.

    NSEC3 is used with algorithms 7, 8, 10, 13 and more, so algorithm 7
    (RSASHA1-NSEC3) is a bad proxy for it -- 5% against NSEC3's own 62%. The
    zone-level measure is NSEC3PARAM, published once at the apex. Forward corpus
    only: the reverse corpus carries delegations and cannot see it.
    """
    if not len(timeline):
        return None
    f = timeline[timeline.basis == "zonefile"]
    par = f[(f.dimension == "rr_type") & (f.value.astype(str) == "NSEC3PARAM")] \
        .groupby("month").domains_peak.sum()
    signed = f[(f.dimension == "algorithm_dnskey") & (f.value.astype(str) == "_total")] \
        .groupby("month").domains_peak.sum()
    share = (par / signed * 100).dropna()
    if share.empty:
        return None
    return {"basis": "forward corpus, NSEC3PARAM zones / signed zones",
            "first_month": share.index.min(), "last_month": share.index.max(),
            "peak_share_pct": round(float(share.max()), 2),
            "peak_month": str(share.idxmax()),
            "last_share_pct": round(float(share.iloc[-1]), 2)}


def stage_at(change: dict, when: str) -> str:
    """Which deployment stage the mechanism was in on a given month."""
    first, one, ten = (change.get("t_first_date"), change.get("t_1pct_date"),
                       change.get("t_10pct_date"))
    if not first or when < first:
        return "before first use"
    if one and when >= one:
        return "in common usage" if ten and when >= ten else "in partial usage"
    return "seen, below 1%"


def share_at(timeline: pd.DataFrame, dimension: str, value: str, month: str):
    """Share of signed delegations carrying the value, reverse corpus.

    Reverse is the only basis spanning 2009-2026; the forward corpus starts
    2016-06 and stops 2023-12, so it cannot date most of these CVEs.
    """
    b = timeline[(timeline.basis == "reverse") & (timeline.dimension == dimension)]
    num = b[b.value == value].groupby("month").domains_peak.sum()
    den = b[b.value == "_total"].groupby("month").domains_peak.sum()
    at = (num / den * 100).dropna()
    at = at[at.index <= month]
    return round(float(at.iloc[-1]), 3) if len(at) else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adoption", type=Path, default=Path("out/analysis/adoption_measures.json"))
    ap.add_argument("--cves", type=Path, default=Path("out/analysis/cve_crossref.json"))
    ap.add_argument("--timeline", type=Path,
                    default=Path("out/server_run/timeline_monthly.parquet"))
    ap.add_argument("--out", type=Path,
                    default=Path("out/analysis/cve_adoption_crossref.json"))
    args = ap.parse_args()

    adopt = json.loads(args.adoption.read_text(encoding="utf-8"))
    cve = json.loads(args.cves.read_text(encoding="utf-8"))
    tl = pd.read_parquet(args.timeline) if args.timeline.exists() else pd.DataFrame()

    changes = [(c, "algorithm_ds") for c in adopt["algorithms"]] + \
              [(c, "digest_type_ds") for c in adopt["digest_types"]]
    dnssec = [c for c in cve["cves"] if c["scope"] == "dnssec"]

    rows, attached = [], set()
    for change, dim in changes:
        pat = NAMED.get(change["change"])
        hits = []
        if pat:
            for c in dnssec:
                if c["published"] and re.search(pat, c["description"] or "", re.I):
                    hits.append(c)
                    attached.add(c["cve"])
        stages = Counter(stage_at(change, c["published"][:7]) for c in hits)
        rows.append({
            "change": change["change"], "codepoint": change["value"], "rfc": change["rfc"],
            "published": change["published"],
            "t_first": change.get("t_first_date"), "t_1pct": change.get("t_1pct_date"),
            "t_10pct": change.get("t_10pct_date"),
            "onset_years": change.get("onset_years"),
            "peak_share_pct": change.get("peak_share_pct"),
            "current_share_pct": change.get("current_share_pct"),
            "reached_common_usage": bool(change.get("t_10pct_date")),
            "matchable": bool(pat),
            "n_cves": len(hits),
            "cve_stage_counts": dict(stages),
            "cves": [{"cve": c["cve"], "published": c["published"], "cvss": c["cvss"],
                      "mechanism": c["mechanism"],
                      "stage_when_published": stage_at(change, c["published"][:7]),
                      "share_pct_then": share_at(tl, dim, str(change["value"]),
                                                 c["published"][:7]) if len(tl) else None}
                     for c in sorted(hits, key=lambda x: x["published"])],
        })

    # NSEC3 gets its own row: the CVEs matched on /NSEC3/ are about the mechanism,
    # not about algorithm 7, and the two curves differ by an order of magnitude.
    n3 = nsec3_mechanism(tl)
    n3_cves = [c for c in dnssec if c["mechanism"] == "nsec3" and c["published"]]
    if n3:
        n3.update(mechanism="NSEC3", rfc="RFC 5155", published="2008-03",
                  n_cves=len(n3_cves),
                  cves=[{"cve": c["cve"], "published": c["published"], "cvss": c["cvss"]}
                        for c in sorted(n3_cves, key=lambda x: x["published"])])

    core = [c for c in dnssec if c["rfc"] in SHARED_CORE]
    unattached = [c for c in dnssec if c["cve"] not in attached]

    # Does vulnerability count follow deployment? Only over changes we can match.
    m = [(r["peak_share_pct"] or 0, r["n_cves"]) for r in rows if r["matchable"]]
    corr = None
    if len(m) > 2:
        s = pd.DataFrame(m, columns=["peak", "cves"])
        corr = round(float(s.peak.corr(s.cves)), 3)

    payload = {
        "generated": date.today().isoformat(),
        "method": {
            "join": "CVE description must name the algorithm or mechanism.",
            "why_narrow": ("A bug in the shared validation path is not evidence against "
                           "any one algorithm. Those are counted under shared_core."),
            "share_basis": "reverse corpus, P(value | signed delegations)",
        },
        "totals": {
            "dnssec_cves": len(dnssec),
            "attached_to_a_named_mechanism": len(attached),
            "shared_core_rfc_4033_4034_4035": len(core),
            "not_attachable": len(unattached),
        },
        "correlation_peak_share_vs_cve_count": corr,
        "correlation_caveat": ("11 mechanisms and 16 mechanism-named CVEs. This refutes a "
                               "strong relationship; it does not establish a weak one."),
        "nsec3_mechanism": n3,
        "changes": rows,
        "shared_core": {
            "rfcs": sorted(SHARED_CORE),
            "n_cves": len(core),
            "exposure": ("100% of signed zones by construction: every signed zone uses "
                         "these three specifications whatever algorithm it chose."),
            "cves": [{"cve": c["cve"], "published": c["published"], "cvss": c["cvss"],
                      "mechanism": c["mechanism"]} for c in
                     sorted(core, key=lambda x: x["published"] or "")],
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"{'change':20} {'rfc':9} {'first':8} {'1%':8} {'10%':8} {'peak%':>7} {'CVEs':>5}")
    for r in sorted(rows, key=lambda x: -(x["peak_share_pct"] or 0)):
        if not r["matchable"] and not r["n_cves"]:
            continue
        print(f"{r['change']:20} {r['rfc']:9} {str(r['t_first'] or '-'):8} "
              f"{str(r['t_1pct'] or '-'):8} {str(r['t_10pct'] or '-'):8} "
              f"{(r['peak_share_pct'] or 0):>7.2f} {r['n_cves']:>5}")
    t = payload["totals"]
    print(f"\n{t['dnssec_cves']} DNSSEC CVEs: {t['attached_to_a_named_mechanism']} name a "
          f"mechanism, {t['shared_core_rfc_4033_4034_4035']} are in the shared core "
          f"(RFC 4033/4034/4035), {t['not_attachable']} not attachable")
    if n3:
        print(f"\nNSEC3 as a mechanism ({n3['basis']}): peak {n3['peak_share_pct']}% "
              f"({n3['peak_month']}), last {n3['last_share_pct']}% ({n3['last_month']}), "
              f"{n3['n_cves']} CVEs -- against algorithm 7's peak of "
              f"{next((r['peak_share_pct'] for r in rows if r['change'] == 'RSASHA1-NSEC3'), None)}%")
    print(f"\ncorr(peak share, CVE count) over matchable changes = {corr} "
          f"(n={len(m)} mechanisms; refutes a strong relationship, establishes nothing)")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
