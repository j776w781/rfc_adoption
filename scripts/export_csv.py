"""Export the software and CVE cross-references as CSV.

Every row carries the commit it rests on and a URL to that commit, plus an
`attribution` and a plain-English `attribution_basis`. There is deliberately no
`confidence` column: a three-level label with no definition tells a reader
nothing about what to distrust.

    python scripts/export_csv.py [--out out/analysis]
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

NAME = {"unbound": "Unbound", "nsd": "NSD", "bind9": "BIND 9", "knot": "Knot DNS",
        "kresd": "Knot Resolver", "opendnssec": "OpenDNSSEC",
        "pdns-auth": "PowerDNS Authoritative", "pdns-rec": "PowerDNS Recursor"}
RFC_PUB = {"RFC 5011": "2007-09", "RFC 5155": "2008-03", "RFC 5702": "2009-10",
           "RFC 5933": "2010-07", "RFC 6605": "2012-04", "RFC 7344": "2014-09",
           "RFC 8078": "2017-03", "RFC 8080": "2017-02", "RFC 9276": "2022-08"}
CAPABILITY = {
    "rrtype": "can parse and serve the record type",
    "publish": "can generate the record itself",
    "sign": "can produce RRSIGs with this algorithm",
    "validate": "can verify this algorithm",
    "algorithm-aware": "knows the codepoint but cannot sign with it",
}


def w(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        c = csv.writer(f, lineterminator="\n")
        c.writerow(header)
        c.writerows(rows)
    print(f"  {path}  ({len(rows)} rows)")


def software(sup: dict, rel: dict, out: Path) -> None:
    w(out / "dns_software_releases.csv",
      ["project", "role", "stable_releases", "first_release_date", "last_release_date"],
      [[NAME[p], v["role"], len(v["releases"]),
        min(v["releases"].values()), max(v["releases"].values())]
       for p, v in sorted(rel.items(), key=lambda kv: -len(kv[1]["releases"]))])

    w(out / "dns_software_feature_support.csv",
      ["rfc", "rfc_published", "observable", "project", "role", "capability",
       "capability_meaning", "version", "release_date", "commit_date",
       "shipped_before_rfc", "standard_codepoint", "attribution",
       "attribution_basis", "evidence_kind", "evidence_text", "evidence_commit",
       "evidence_url", "note"],
      [[r["rfc"], RFC_PUB.get(r["rfc"], ""), r["observable"], NAME[r["implementation"]],
        rel[r["implementation"]]["role"], r["capability"],
        CAPABILITY.get(r["capability"], ""), r["first_release"], r["released"],
        r.get("commit_date", ""), r.get("pre_rfc", False),
        r.get("standard_codepoint", True), r.get("attribution", ""),
        r.get("attribution_basis", ""), r.get("evidence_kind", ""),
        r.get("evidence", ""), r.get("evidence_commit", "") or "",
        r.get("evidence_url", ""), r.get("note", "")]
       for r in sorted(sup["support"], key=lambda x: (x["rfc"], x["released"]))])

    for key, fname in (("default_changes", "dns_software_default_changes.csv"),
                       ("validator_limits", "dns_software_validator_limits.csv")):
        w(out / fname,
          ["release_date", "project", "version", "change", "commit_date",
           "changed_files", "attribution", "attribution_basis", "evidence_text",
           "evidence_commit", "evidence_url", "note"],
          [[r["released"], NAME[r["implementation"]], r["first_release"], r["what"],
            r.get("commit_date", ""), r.get("files", ""), r.get("attribution", ""),
            r.get("attribution_basis", ""), r.get("evidence", ""),
            r.get("evidence_commit", "") or "", r.get("evidence_url", ""),
            r.get("note", "")]
           for r in sorted(sup[key], key=lambda x: x["released"])])


def cves(a: dict, out: Path) -> None:
    qm = a["query_method"]
    w(out / "dns_cve_list.csv",
      ["cve", "published", "cvss", "severity", "cwe", "scope", "mechanism", "rfc",
       "classified_by_rule", "listed_for_products", "product_attribution",
       "fixed_in_projects", "first_fix_release_date", "sources", "description",
       "reference"],
      [[c["cve"], c["published"] or "", c["cvss"] if c["cvss"] is not None else "",
        c["severity"] or "", "; ".join(c["cwe"]), c["scope"], c["mechanism"] or "",
        c["rfc"] or "", c["rule"], "; ".join(NAME[p] for p in c["products"]),
        "; ".join(f"{NAME[p]}={qm[p]}" for p in c["products"]),
        "; ".join(f"{NAME[p]} {f['release']}" for p, f in sorted(c["fixes"].items())
                  if f.get("release")),
        min((f["released"] for f in c["fixes"].values() if f.get("released")), default=""),
        "; ".join(c["sources"]), (c["description"] or "").replace("\n", " "),
        f"https://nvd.nist.gov/vuln/detail/{c['cve']}"]
       for c in a["cves"]])

    w(out / "dns_cve_fixes.csv",
      ["cve", "published", "scope", "mechanism", "rfc", "project", "role",
       "fix_version", "fix_release_date", "commit_date",
       "days_from_publication_to_release", "released_before_publication",
       "commit_subject"],
      [[c["cve"], c["published"] or "", c["scope"], c["mechanism"] or "", c["rfc"] or "",
        NAME[p], a["project_roles"][p], f.get("release") or "", f.get("released") or "",
        f.get("commit_date") or "",
        (__import__("datetime").date.fromisoformat(f["released"])
         - __import__("datetime").date.fromisoformat(c["published"])).days
        if c["published"] and f.get("released") else "",
        (f["released"] < c["published"]) if c["published"] and f.get("released") else "",
        (f.get("subject") or "").replace("\n", " ")]
       for c in a["cves"] for p, f in sorted(c["fixes"].items())])

    w(out / "dns_cve_coordinated.csv",
      ["cve", "published", "cvss", "scope", "mechanism", "rfc", "codebases", "vendors",
       "affected_evidence", "first_fix", "last_fix", "spread_days", "description"],
      [[c["cve"], c["published"] or "", c["cvss"] if c["cvss"] is not None else "",
        c["scope"], c["mechanism"] or "", c["rfc"] or "", "; ".join(c["codebases"]),
        "; ".join(c["vendors"]),
        "; ".join(f"{k}={v}" for k, v in c["affected_evidence"].items()),
        c["first_release"] or "", c["last_release"] or "",
        c["spread_days"] if c["spread_days"] is not None else "",
        (c["description"] or "").replace("\n", " ")]
       for c in a["coordinated"]])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("out/analysis"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    software(json.loads(Path("data/software/software_support.json").read_text("utf-8")),
             json.loads(Path("data/software/release_dates.json").read_text("utf-8")), args.out)
    cve_path = Path("out/analysis/cve_crossref.json")
    if cve_path.exists():
        cves(json.loads(cve_path.read_text("utf-8")), args.out)
    else:
        print("  (skipping CVE exports: run scripts/cve_crossref.py first)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
