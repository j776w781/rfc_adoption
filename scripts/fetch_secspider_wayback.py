"""Collect SecSpider's "Monitoring Summary" counts from Wayback Machine captures.

SecSpider (secspider.net, Eric Osterweil, crawling since 2005) publishes no
downloadable time series: its growth chart is a PNG, its trend charts are
gnuplot SVGs of the last four months only, and the flat files it documents are
per-zone DS/DNSKEY dumps. What it does publish is a live summary block --
"N Zones", "N DNSSEC enabled zones", "N DNSSEC verified zones", "N Production
DNSSEC-enabled zones" -- and the Internet Archive has captured that block on
three hosts:

    2006-09 .. 2015-08   http://secspider.cs.ucla.edu/          (home page)
    2012-01 .. 2018-09   http://secspider.verisignlabs.com/stats.html
    2019-09 .. today     https://secspider.net/stats.html

This script asks the CDX index for at most one capture per month on each host
(the UCLA host is asked twice: its home page carried the summary until 2012 and
its ``stats.html`` from 2013),
downloads each capture in raw (``id_``) mode, saves the HTML untouched under
``data/external/secspider/raw/<host>/<timestamp>.html`` and parses the counts
into ``data/external/secspider/secspider_wayback_snapshots.csv``. The live
page is appended as one more row so the series reaches the retrieval date.

Nothing is interpolated. A month with no capture is absent from the CSV.

Usage: python scripts/fetch_secspider_wayback.py [--out data/external/secspider]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (research; rfc_adoption DNSSEC prevalence; contact via repo)"
CDX = "https://web.archive.org/cdx/search/cdx"

# (host label, archived URL, era note)
TARGETS = [
    ("secspider.cs.ucla.edu", "http://secspider.cs.ucla.edu/", "UCLA home page"),
    ("secspider.cs.ucla.edu", "http://secspider.cs.ucla.edu/stats.html", "UCLA stats page (2013-2015)"),
    ("secspider.verisignlabs.com", "http://secspider.verisignlabs.com/stats.html", "Verisign Labs stats page"),
    ("secspider.net", "https://secspider.net/stats.html", "current stats page"),
]
LIVE = ("secspider.net", "https://secspider.net/stats.html")

# label on the page -> CSV column. Labels are matched after tag stripping and
# whitespace collapsing, case-insensitively, immediately after a number.
FIELDS = [
    ("zones_tracked", r"Zones(?! (?:have|use|are))"),
    ("zones_ns_match_parent", r"Zones have NS sets that match their parents' delegation set"),
    ("dnssec_enabled_zones", r"DNSSEC enabled zones"),
    ("zones_ksk_and_zsk", r"Zones use both KSKs and ZSKs"),
    ("zones_serving_revoked_keys", r"Zones are serving revoked keys"),
    ("dnssec_verified_zones", r"DNSSEC verified zones"),
    ("production_dnssec_zones", r"Production DNSSEC-enabled zones"),
]
ASOF = re.compile(r"as of:?\s*([A-Z][a-z]{2} [A-Z][a-z]{2}\s+\d{1,2} \d{2}:\d{2}:\d{2} \d{4}) ?(?:UTC|GMT)?")
# The 2007-08 UCLA capture printed "1849 Zones / 0 DNSSEC enabled zones" under a
# "Sorry, but we have hit a minor pot-hole" banner: an outage page, not a count.
# Such captures are kept raw and flagged so the consumer can drop them.
NOTICE = re.compile(r"Sorry, but we have (?:hit|it) a minor pot-hole", re.I)


def fetch(url: str, tries: int = 5, timeout: int = 120) -> bytes:
    delay = 5.0
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503, 502, 504) and attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError("unreachable")


def cdx_monthly(url: str) -> list[str]:
    q = urllib.parse.urlencode({
        "url": url, "output": "txt", "fl": "timestamp,statuscode",
        "filter": "statuscode:200", "collapse": "timestamp:6",
    })
    body = fetch(f"{CDX}?{q}").decode("utf-8", "replace")
    return [line.split()[0] for line in body.splitlines() if line.strip()]


def text_of(raw: bytes) -> str:
    t = raw.decode("utf-8", "replace")
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t)


def parse(raw: bytes) -> dict[str, str]:
    t = text_of(raw)
    out: dict[str, str] = {}
    for col, label in FIELDS:
        m = re.search(r"(\d[\d,]*)\s+" + label, t)
        out[col] = m.group(1).replace(",", "") if m else ""
    m = ASOF.search(t)
    out["page_as_of"] = m.group(1) if m else ""
    out["page_notice"] = "outage" if NOTICE.search(t) else ""
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/external/secspider")
    ap.add_argument("--sleep", type=float, default=1.0)
    args = ap.parse_args()
    out = Path(args.out)
    raw_dir = out / "raw"
    rows: list[dict[str, str]] = []
    today = dt.date.today().isoformat()

    for host, url, note in TARGETS:
        stamps = cdx_monthly(url)
        print(f"{host}: {len(stamps)} monthly captures ({stamps[0][:6]}..{stamps[-1][:6]})", flush=True)
        for ts in stamps:
            path = raw_dir / host / f"{ts}.html"
            if path.exists():
                raw = path.read_bytes()
            else:
                wb = f"https://web.archive.org/web/{ts}id_/{url}"
                try:
                    raw = fetch(wb)
                except Exception as exc:  # keep going; the gap is recorded by absence
                    print(f"  {ts}: FAILED {exc}", flush=True)
                    time.sleep(args.sleep)
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                time.sleep(args.sleep)
            parsed = parse(raw)
            rows.append({
                "capture_ts": ts,
                "capture_date": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}",
                "month": f"{ts[:4]}-{ts[4:6]}",
                "host": host, "kind": "wayback",
                "source_url": f"https://web.archive.org/web/{ts}/{url}",
                "raw_file": str(path.relative_to(out)),
                **parsed,
            })
            flag = "" if parsed["zones_tracked"] else "  (no counts parsed)"
            print(f"  {ts} zones={parsed['zones_tracked']} enabled={parsed['dnssec_enabled_zones']}{flag}", flush=True)

    # live page: one capture per UTC day; a re-run on the same day re-parses it
    # instead of adding a duplicate row.
    host, url = LIVE
    try:
        live_dir = raw_dir / f"{host}-live"
        todays = sorted(live_dir.glob(dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d") + "*.html"))
        if todays:
            path = todays[-1]
            stamp = path.stem
            raw = path.read_bytes()
        else:
            raw = fetch(url)
            stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S")
            path = live_dir / f"{stamp}.html"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        parsed = parse(raw)
        rows.append({
            "capture_ts": stamp, "capture_date": today, "month": today[:7],
            "host": host, "kind": "live", "source_url": url,
            "raw_file": str(path.relative_to(out)), **parsed,
        })
        print(f"live {today} zones={parsed['zones_tracked']} enabled={parsed['dnssec_enabled_zones']}")
    except Exception as exc:
        print(f"live fetch failed: {exc}")

    rows.sort(key=lambda r: r["capture_ts"])
    cols = ["capture_ts", "capture_date", "month", "host", "kind", "source_url", "raw_file",
            "page_as_of", "page_notice"] + [c for c, _ in FIELDS]
    out.mkdir(parents=True, exist_ok=True)
    with (out / "secspider_wayback_snapshots.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out / 'secspider_wayback_snapshots.csv'} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
