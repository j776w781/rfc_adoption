"""Build data/software/cve_inventory.json: every CVE touching the eight DNS
implementations, plus the protocol-level DNS/DNSSEC set.

Three sources, because none alone is complete:

  NVD per product      the authority on what exists. Unbound's own changelog
                       never mentions CVE-2009-3602, an NSEC3 signature
                       verification bug from before the project cited IDs.
  NVD by keyword       protocol-level flaws that span implementations. A bug in
                       one program is a patch; a bug in DNSSEC is an ecosystem
                       event, and only those can move deployment.
  project git history  the authority on *when it was fixed* and in which
                       release, which NVD does not record. Also the only source
                       for dependency CVEs a project patched around.

Needs network. The output is committed so scripts/cve_crossref.py runs offline.

    python scripts/cve_fetch.py [--out data/software/cve_inventory.json]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
CVE_RE = re.compile(r"CVE-(\d{4})-(\d{4,7})", re.I)

PRODUCTS = {
    "unbound":    ("virtualMatchString", "cpe:2.3:a:nlnetlabs:unbound"),
    "nsd":        ("virtualMatchString", "cpe:2.3:a:nlnetlabs:nsd"),
    "bind9":      ("virtualMatchString", "cpe:2.3:a:isc:bind"),
    "knot":       ("keywordSearch",      "Knot DNS"),
    "kresd":      ("keywordSearch",      "Knot Resolver"),
    "opendnssec": ("keywordSearch",      "OpenDNSSEC"),
    "pdns-auth":  ("virtualMatchString", "cpe:2.3:a:powerdns:authoritative_server"),
    "pdns-rec":   ("virtualMatchString", "cpe:2.3:a:powerdns:recursor"),
}
KEYWORDS = ["DNSSEC", "NSEC3", "RRSIG", "DNSKEY", "DNS cache poisoning"]


def fetch(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return json.load(r)
        except Exception as exc:                      # NVD 503s under load
            print(f"    retry {attempt + 1}: {exc}", file=sys.stderr)
            time.sleep(12 * (attempt + 1))
    raise SystemExit(f"gave up on {url}")


def slim(v: dict) -> dict:
    c = v["cve"]
    score = severity = None
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        if c.get("metrics", {}).get(key):
            d = c["metrics"][key][0]["cvssData"]
            score = d.get("baseScore")
            severity = d.get("baseSeverity") or c["metrics"][key][0].get("baseSeverity")
            break
    return {
        "cve": c["id"], "published": c["published"][:10],
        "description": next((d["value"] for d in c["descriptions"] if d["lang"] == "en"), ""),
        "cvss": score, "severity": severity,
        "cwe": sorted({d["value"] for w in c.get("weaknesses", [])
                       for d in w["description"] if d["value"].startswith("CWE")}),
        "refs": [r["url"] for r in c.get("references", [])][:6],
    }


def page(field: str, value: str) -> list[dict]:
    rows, start = [], 0
    while True:
        data = fetch({field: value, "resultsPerPage": 2000, "startIndex": start})
        rows += [slim(v) for v in data.get("vulnerabilities", [])]
        total, got = data.get("totalResults", 0), data.get("resultsPerPage", 0)
        start += got
        if start >= total or not got:
            break
        time.sleep(7)
    time.sleep(7)
    return rows


def from_git(repos: Path) -> dict[str, list[dict]]:
    """Earliest commit naming each CVE, and the first stable release with it."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _release_map import first_release, REPO_DIR      # noqa: E402

    out: dict[str, dict] = defaultdict(dict)
    for proj in PRODUCTS:
        repo = repos / f"{REPO_DIR.get(proj, proj)}.git"
        if not repo.exists():
            print(f"  skip {proj}: no clone at {repo}", file=sys.stderr)
            continue
        log = subprocess.run(
            ["git", "-C", str(repo), "log", "--all", "--date=short",
             "--format=%x01%ad\t%H\t%s%n%b"], capture_output=True, text=True).stdout
        for rec in log.split("\x01")[1:]:
            head, _, body = rec.partition("\n")
            parts = head.split("\t", 2)
            if len(parts) < 3:
                continue
            cdate, sha, subj = parts
            for y, n in set(CVE_RE.findall(head + "\n" + body)):
                cve = f"CVE-{y}-{n}"
                prev = out[proj].get(cve)
                if prev is None or cdate < prev["commit_date"]:
                    out[proj][cve] = {"cve": cve, "commit_date": cdate, "sha": sha,
                                      "subject": subj[:150]}
        for rec in out[proj].values():
            fr = first_release(proj, rec["sha"], not_before=rec["commit_date"])
            rec["fix_release"], rec["fix_released"] = fr if fr else (None, None)
        print(f"  {proj:12} {len(out[proj]):>4} CVEs in git history")
    return {k: sorted(v.values(), key=lambda r: r["cve"]) for k, v in out.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data/software/cve_inventory.json"))
    ap.add_argument("--repos", type=Path, default=Path("out/software_repos"),
                    help="bare clones made by scripts/clone_dns_software.sh")
    ap.add_argument("--skip-git", action="store_true")
    args = ap.parse_args()

    print("NVD, per product:")
    products = {}
    for proj, (field, value) in PRODUCTS.items():
        products[proj] = page(field, value)
        print(f"  {proj:12} {len(products[proj]):>4}")

    print("NVD, protocol keywords:")
    keywords = {}
    for term in KEYWORDS:
        keywords[term] = page("keywordSearch", term)
        print(f"  {term:22} {len(keywords[term]):>4}")

    fixes = {} if args.skip_git else from_git(args.repos)

    payload = {"generated": date.today().isoformat(),
               "sources": {"nvd_api": API, "products": PRODUCTS, "keywords": KEYWORDS},
               "by_product": products, "by_keyword": keywords, "fixes": fixes}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    distinct = {r["cve"] for v in products.values() for r in v} | \
               {r["cve"] for v in keywords.values() for r in v} | \
               {r["cve"] for v in fixes.values() for r in v}
    print(f"\nwrote {args.out}: {len(distinct)} distinct CVEs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
