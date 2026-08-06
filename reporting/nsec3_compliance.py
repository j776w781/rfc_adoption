"""Measure RFC 9276 conformance (NSEC3 iterations) for one day per zone.

RFC 5155 lets a zone publish NSEC3 with an unbounded iteration count, and every
extra iteration is another SHA-1 pass a validating resolver must perform on a
negative answer. That is the root cause of CVE-2023-50868: an attacker floods a
resolver with queries against a high-iteration zone and exhausts its CPU. RFC 9276
(August 2022) is the fix -- 0 extra iterations and an empty salt.

The checkpoints cannot answer this: `nsec3_iterations` was never projected into
them, because no checklist indicator references it. So this queries S3 directly for
one day per zone. It is a **spot measurement**, not a corpus-wide figure, and the
JSON says so; anything built on it must say so too.

Percentages are over **distinct names**, not records. The rest of the deck is
record-weighted, which is right for "how much of the corpus looks like X" but wrong
here: one large signed zone publishing thousands of NSEC3 records would otherwise
decide the conformance rate for a whole TLD.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, "src")
from openintel_rfc.openintel_source import AccessConfig, open_duckdb

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("reporting/nsec3_compliance.json")

#: RFC 9276 was published in August 2022. A day before that cannot be read as
#: non-conformance -- the guidance did not exist yet.
RFC_9276_PUBLISHED = date(2022, 8, 1)

#: The most recent measured day available per zone in the overnight corpus.
DAYS = [("gov", date(2026, 4, 28)), ("nu", date(2024, 3, 3)), ("se", date(2021, 1, 11))]

#: Iteration counts at or above this are the materially risky ones. Patched
#: resolvers cap around here and treat higher as insecure, so a zone above it
#: risks failing validation outright.
HIGH_ITERATIONS = 10

BASE = "s3://openintel-public/fdns/basis=zonefile"

QUERY = """
SELECT COALESCE(nsec3_iterations, nsec3param_iterations) AS iterations,
       count(*)                    AS records,
       count(DISTINCT query_name)  AS names
FROM read_parquet('{uri}')
WHERE response_type IN ('NSEC3', 'NSEC3PARAM')
GROUP BY 1
ORDER BY 1
"""


def measure(connection, source: str, day: date) -> dict:
    uri = (f"{BASE}/source={source}/year={day:%Y}/month={day:%m}/day={day:%d}"
           "/*.gz.parquet")
    rows = connection.execute(QUERY.format(uri=uri)).fetchall()
    histogram = {("null" if i is None else int(i)): {"records": int(r), "names": int(n)}
                 for i, r, n in rows}
    total_names = sum(v["names"] for v in histogram.values())
    total_records = sum(v["records"] for v in histogram.values())

    def names_where(predicate) -> int:
        return sum(v["names"] for k, v in histogram.items()
                   if k != "null" and predicate(k))

    conformant = names_where(lambda i: i == 0)
    high = names_where(lambda i: i >= HIGH_ITERATIONS)
    numeric = [k for k in histogram if k != "null"]
    pct = lambda n: round(n / total_names * 100, 1) if total_names else 0.0  # noqa: E731

    return {
        "source": source,
        "date": day.isoformat(),
        "total_records": total_records,
        "total_names": total_names,
        "iterations": {str(k): v for k, v in sorted(
            histogram.items(), key=lambda kv: (kv[0] == "null", kv[0]))},
        "pct_conformant": pct(conformant),
        "pct_high": pct(high),
        "max_iterations": max(numeric) if numeric else None,
        "predates_rfc9276": day < RFC_9276_PUBLISHED,
    }


def main() -> int:
    connection = open_duckdb(AccessConfig(mode="stream"))
    try:
        zones = [measure(connection, source, day) for source, day in DAYS]
    finally:
        connection.close()

    payload = {
        "measurement": "spot",
        "note": ("One measured day per zone, not the corpus. Percentages are over "
                 "distinct names, not records."),
        "high_iterations_threshold": HIGH_ITERATIONS,
        "rfc9276_published": RFC_9276_PUBLISHED.isoformat(),
        "zones": zones,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")

    print("RFC 9276 conformance (0 NSEC3 iterations), one day per zone")
    for z in zones:
        flag = "   [day predates RFC 9276]" if z["predates_rfc9276"] else ""
        print(f"  .{z['source']:<4}{z['date']}  {z['total_names']:>9,} names  "
              f"conformant {z['pct_conformant']:>5.1f}%  "
              f">={HIGH_ITERATIONS} iters {z['pct_high']:>5.1f}%  "
              f"max {z['max_iterations']}{flag}")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
