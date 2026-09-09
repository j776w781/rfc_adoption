"""Cross-reference DNS/DNSSEC CVEs against RFCs and observed deployment.

Three questions, in order of how much the data can actually answer:

  1. What is the CVE surface, and how much of it is DNSSEC rather than DNS?
     Countable, and the answer is smaller than the reputation suggests.
  2. How fast does a fix reach a release, and how far apart are vendors on a
     shared flaw? Countable per project, from the git history.
  3. Did any CVE move deployment? Only answerable where a fix changes what zones
     may publish -- which is almost never. Stated as such, not glossed.

Reads data/software/cve_inventory.json (offline; built by scripts/cve_fetch.py)
and out/server_run/timeline_monthly.parquet.
Writes out/analysis/cve_crossref.json.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

#: Ordered. First rule that matches wins, and the rule name is recorded on the
#: row so a disputed classification can be argued with rather than guessed at.
DEPENDENCY = re.compile(
    r"\b(openssl|libressl|gnutls|nettle|libxml|expat|zlib|lua\b|luajit|h2o\b|webrick|"
    r"spnego|nghttp2|libcurl|curl\b|sqlite|protobuf|boost|libidn|krb5|kerberos|"
    r"systemd|glibc|python|ruby on rails|rails\b|jinja|node\.js|openldap|mysql|"
    r"postgres|libmaxminddb|c-ares)\b", re.I)

MECHANISM = [
    ("nsec3",        re.compile(r"\bNSEC3\b", re.I),                       "RFC 5155"),
    ("nsec",         re.compile(r"\bNSEC\b", re.I),                        "RFC 4034"),
    ("cds",          re.compile(r"\bCDS\b|\bCDNSKEY\b", re.I),             "RFC 7344"),
    ("trust-anchor", re.compile(r"trust anchor|managed[- ]keys|RFC ?5011", re.I), "RFC 5011"),
    ("ds-digest",    re.compile(r"\bDS record|digest type|\bSHA-?(1|256|384)\b", re.I), "RFC 4509"),
    ("algorithm",    re.compile(r"\bECDSA\b|\bEdDSA\b|Ed25519|Ed448|GOST|RSASHA", re.I), "RFC 6605/8080"),
    ("dnskey",       re.compile(r"\bDNSKEY\b|\bKSK\b|\bZSK\b|zone key", re.I), "RFC 4034"),
    ("rrsig",        re.compile(r"\bRRSIG\b|signature verif|verify.{0,20}signature", re.I), "RFC 4035"),
    ("validation",   re.compile(r"\bDNSSEC\b.{0,40}validat|validat.{0,40}\bDNSSEC\b", re.I), "RFC 4035"),
    ("nxt-sig-key",  re.compile(r"\bNXT record|\bSIG record|\bKEY record", re.I), "RFC 2535"),
    ("dnssec-other", re.compile(r"\bDNSSEC\b", re.I),                      "RFC 4033"),
]

DNS_GENERIC = re.compile(
    r"cache poison|spoof|\bTSIG\b|zone transfer|\bAXFR\b|\bIXFR\b|resolver|"
    r"\bDNS\b|named\b|nameserver|\bEDNS\b|\bRRL\b|rate limit", re.I)

PROJECT_ROLE = {"unbound": "resolver", "kresd": "resolver", "pdns-rec": "resolver",
                "nsd": "authoritative", "knot": "authoritative", "pdns-auth": "authoritative",
                "opendnssec": "signer", "bind9": "both"}

#: pdns-auth and pdns-rec are built from one repository, and NSD and Unbound come
#: from one vendor. Coordination is only interesting across codebases that had to
#: be fixed independently, so both facts have to be collapsed before counting.
CODEBASE = {"pdns-auth": "powerdns", "pdns-rec": "powerdns"}

#: How each project's NVD list was obtained. CPE attribution is a curated claim
#: that the CVE affects that product. Keyword attribution is a substring match:
#: the "Knot DNS" query also returns every Knot Resolver CVE, because "Knot
#: Resolver" contains "Knot". Keyword-sourced product membership therefore
#: cannot be used to say who was affected.
QUERY_METHOD = {"unbound": "cpe", "nsd": "cpe", "bind9": "cpe",
                "pdns-auth": "cpe", "pdns-rec": "cpe",
                "knot": "keyword", "kresd": "keyword", "opendnssec": "keyword"}
VENDOR = {"unbound": "nlnetlabs", "nsd": "nlnetlabs", "bind9": "isc",
          "knot": "cznic", "kresd": "cznic", "opendnssec": "opendnssec",
          "pdns-auth": "powerdns", "pdns-rec": "powerdns"}


def classify(text: str, in_dns_product: bool = False) -> dict:
    """scope, mechanism and the RFC a CVE touches, with the rule that decided it.

    `in_dns_product` is provenance, not text: a CVE returned by an NVD CPE query
    for BIND *is* a vulnerability in DNS software, whatever its wording. Without
    it, "Buffer overflow in BIND 8.2 via NXT records" classifies as "other"
    because the description never says "DNS".
    """
    if DEPENDENCY.search(text):
        return {"scope": "dependency", "mechanism": None, "rfc": None, "rule": "DEPENDENCY"}
    for name, rx, rfc in MECHANISM:
        if rx.search(text):
            scope = "dns" if name == "ds-digest" and not re.search(r"DNSSEC|DS record", text, re.I) \
                else "dnssec"
            return {"scope": scope, "mechanism": name, "rfc": rfc, "rule": name}
    if DNS_GENERIC.search(text):
        return {"scope": "dns", "mechanism": None, "rfc": None, "rule": "DNS_GENERIC"}
    if in_dns_product:
        return {"scope": "dns", "mechanism": None, "rfc": None, "rule": "PRODUCT_CPE"}
    return {"scope": "other", "mechanism": None, "rfc": None, "rule": "none"}


def build_index(inv: dict) -> dict[str, dict]:
    """One row per CVE: metadata, which projects list it, and where each fixed it."""
    rows: dict[str, dict] = {}

    def note(rec, source, project=None, keyword=None):
        r = rows.setdefault(rec["cve"], {
            "cve": rec["cve"], "published": None, "description": "", "cvss": None,
            "severity": None, "cwe": [], "sources": set(), "products": set(),
            "keywords": set(), "fixes": {}})
        r["sources"].add(source)
        if project:
            r["products"].add(project)
        if keyword:
            r["keywords"].add(keyword)
        for k in ("published", "description", "cvss", "severity"):
            if rec.get(k) and not r.get(k):
                r[k] = rec[k]
        if rec.get("cwe") and not r["cwe"]:
            r["cwe"] = rec["cwe"]

    for proj, recs in inv["by_product"].items():
        for rec in recs:
            note(rec, "nvd-product", project=proj)
    for term, recs in inv["by_keyword"].items():
        for rec in recs:
            note(rec, "nvd-keyword", keyword=term)
    for proj, recs in inv["fixes"].items():
        for rec in recs:
            note({"cve": rec["cve"], "description": rec.get("subject", "")}, "git", project=proj)
            rows[rec["cve"]]["fixes"][proj] = {
                "commit_date": rec.get("commit_date"), "release": rec.get("fix_release"),
                "released": rec.get("fix_released"), "subject": rec.get("subject")}

    for r in rows.values():
        r.update(classify(f'{r["description"]} '
                          f'{" ".join(f["subject"] or "" for f in r["fixes"].values())}',
                          in_dns_product=bool(r["products"])))
        r["sources"] = sorted(r["sources"])
        r["products"] = sorted(r["products"])
        r["keywords"] = sorted(r["keywords"])
    return rows


def fix_latency(rows: dict) -> list[dict]:
    """CVE publication to the release that carried the fix, per project."""
    out = []
    for r in rows.values():
        for proj, f in r["fixes"].items():
            if not (r["published"] and f.get("released")):
                continue
            days = (date.fromisoformat(f["released"]) - date.fromisoformat(r["published"])).days
            out.append({"cve": r["cve"], "project": proj, "scope": r["scope"],
                        "published": r["published"], "released": f["released"],
                        "release": f["release"], "days": days})
    return sorted(out, key=lambda d: d["cve"])


def coordinated(rows: dict, min_codebases: int = 2) -> list[dict]:
    """CVEs that more than one *codebase* had to fix.

    A shared CVE is a protocol problem, not a coding mistake, and the spread
    between the first and last release is how long the ecosystem stayed exposed
    once the flaw was public. Counted per codebase, not per product: PowerDNS
    Authoritative and Recursor ship from one repository, so treating them as two
    turns every PowerDNS advisory into a fake multi-vendor event.
    """
    out = []
    for r in rows.values():
        dated = {p: f["released"] for p, f in r["fixes"].items() if f.get("released")}
        # Affected set: a git fix is proof; CPE attribution is a curated claim;
        # keyword attribution is a substring match and proves nothing.
        affected = set(dated) | {p for p in r["products"] if QUERY_METHOD[p] == "cpe"}
        if len({CODEBASE.get(p, p) for p in affected}) < min_codebases:
            continue
        if not dated:
            first = last = None
        else:
            first, last = min(dated.values()), max(dated.values())
        out.append({
            "cve": r["cve"], "published": r["published"], "scope": r["scope"],
            "codebases": sorted({CODEBASE.get(p, p) for p in affected}),
            "vendors": sorted({VENDOR[p] for p in affected}),
            "affected_evidence": {p: ("git-fix" if p in dated else "nvd-cpe")
                                  for p in sorted(affected)},
            "keyword_only_also_listed": sorted(
                p for p in r["products"] if QUERY_METHOD[p] == "keyword" and p not in affected),
            "mechanism": r["mechanism"], "rfc": r["rfc"], "cvss": r["cvss"],
            "projects": dict(sorted(dated.items(), key=lambda kv: kv[1])),
            "first_release": first, "last_release": last,
            "spread_days": (date.fromisoformat(last) - date.fromisoformat(first)).days
                           if first and last else None,
            "description": (r["description"] or "")[:220],
        })
    return sorted(out, key=lambda d: (d["published"] or "", d["cve"]))


def disclosure_clusters(rows: dict, min_cves: int = 3) -> list[dict]:
    """Days on which several DNSSEC CVEs were published at once.

    Vendors sit on a shared protocol flaw until every affected implementation has
    a release ready, so a cluster is the visible edge of an embargo. It is also
    the only CVE event large enough that an operator would plausibly notice, and
    therefore the only kind that could move deployment.
    """
    by_day = defaultdict(list)
    for r in rows.values():
        if r["scope"] == "dnssec" and r["published"]:
            by_day[r["published"]].append(r)
    out = []
    for day, group in sorted(by_day.items()):
        if len(group) < min_cves:
            continue
        codebases = sorted({CODEBASE.get(p, p) for r in group for p in r["products"]
                            if QUERY_METHOD[p] == "cpe"})
        out.append({
            "published": day, "n_cves": len(group), "codebases": codebases,
            "max_cvss": max((r["cvss"] or 0) for r in group),
            "mechanisms": sorted({r["mechanism"] for r in group if r["mechanism"]}),
            "cves": sorted(r["cve"] for r in group),
        })
    return out


def deployment_context(rows: dict, timeline: Path) -> list[dict]:
    """For each DNSSEC CVE, what the NSEC3 iteration tail was doing around it.

    This is the only observable a resolver-side flaw can plausibly move: a zone
    cannot be made to change algorithm by a CVE, but it can be made to lower an
    iteration count that resolvers stop accepting. Everything else is reported as
    context, not as effect.
    """
    if not timeline.exists():
        return []
    df = pd.read_parquet(timeline)
    z = df[(df.basis == "zonefile") & (df.dimension == "nsec3_iterations")].copy()
    z["iv"] = pd.to_numeric(z.value, errors="coerce")
    high = z[z.iv >= 100].groupby("month").domains_peak.sum()
    out = []
    for r in sorted(rows.values(), key=lambda x: x["published"] or ""):
        if r["scope"] != "dnssec" or not r["published"]:
            continue
        m = r["published"][:7]
        if m < high.index.min() or m > high.index.max():
            continue
        out.append({"cve": r["cve"], "published": r["published"], "mechanism": r["mechanism"],
                    "cvss": r["cvss"],
                    "high_iteration_names_that_month": int(high.get(m, 0)),
                    "description": (r["description"] or "")[:160]})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", type=Path, default=Path("data/software/cve_inventory.json"))
    ap.add_argument("--timeline", type=Path, default=Path("out/server_run/timeline_monthly.parquet"))
    ap.add_argument("--out", type=Path, default=Path("out/analysis/cve_crossref.json"))
    args = ap.parse_args()

    inv = json.loads(args.inventory.read_text(encoding="utf-8"))
    rows = build_index(inv)
    lat = fix_latency(rows)
    coord = coordinated(rows)

    by_scope = Counter(r["scope"] for r in rows.values())
    by_mech = Counter(r["mechanism"] for r in rows.values() if r["mechanism"])
    per_project = defaultdict(Counter)
    for r in rows.values():
        for p in r["products"]:
            per_project[p][r["scope"]] += 1

    dnssec_lat = [d["days"] for d in lat if d["scope"] == "dnssec"]
    all_lat = [d["days"] for d in lat]

    payload = {
        "generated": date.today().isoformat(),
        "totals": {"distinct_cves": len(rows), "by_scope": dict(by_scope),
                   "by_mechanism": dict(by_mech),
                   "with_a_dated_fix": len({d["cve"] for d in lat})},
        "per_project": {p: dict(c) for p, c in sorted(per_project.items())},
        "project_roles": PROJECT_ROLE,
        "query_method": QUERY_METHOD,
        "attribution_caveat": ("Knot, Knot Resolver and OpenDNSSEC have no usable CPE, so "
                               "their CVE lists come from keyword search and overlap by "
                               "substring. Their product membership is not used to decide "
                               "who a CVE affected."),
        "fix_latency_days": {
            "all": {"n": len(all_lat), "median": int(pd.Series(all_lat).median()) if all_lat else None,
                    "p90": int(pd.Series(all_lat).quantile(0.9)) if all_lat else None},
            "dnssec": {"n": len(dnssec_lat),
                       "median": int(pd.Series(dnssec_lat).median()) if dnssec_lat else None},
            "negative_are_embargo": "A fix released before the CVE was published is a "
                                    "coordinated disclosure, not a time machine.",
        },
        "coordinated": coord,
        "disclosure_clusters": disclosure_clusters(rows),
        "deployment_context": deployment_context(rows, args.timeline),
        "cves": sorted(rows.values(), key=lambda r: r["cve"]),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    print(f"distinct CVEs: {len(rows)}")
    print("  by scope:", dict(by_scope))
    print("  by DNSSEC mechanism:", dict(by_mech))
    print(f"  with a dated fix release: {payload['totals']['with_a_dated_fix']}")
    print(f"  fixed by >=2 implementations: {len(coord)}")
    clusters = payload["disclosure_clusters"]
    print(f"  multi-CVE DNSSEC disclosure days: {len(clusters)}")
    for c in clusters:
        print(f"    {c['published']}  {c['n_cves']:>2} CVEs  max CVSS {c['max_cvss']}  "
              f"{c['codebases']}  {c['mechanisms']}")
    print(f"\nfix latency (days from CVE publication to release): "
          f"median {payload['fix_latency_days']['all']['median']}, "
          f"p90 {payload['fix_latency_days']['all']['p90']}, n={len(all_lat)}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
