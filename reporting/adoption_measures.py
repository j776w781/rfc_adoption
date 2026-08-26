"""Separate "when did this first appear" from "how far did it spread".

The project has been conflating two questions under the word *adoption*, and they
need different data, different denominators and different caveats.

**First appearance** (`t_first`) is an existence proof. One operator publishing one
record settles it, so the measure is a minimum over the whole corpus and
composition changes in the archive are irrelevant -- a RIR leaving cannot un-happen
an observation made while it was present. It is computed over **all five RIRs**.

**Diffusion** (`t_1`, `t_10`, `t_50`) is a population statement, so it needs a
stable denominator and a population that could plausibly have adopted. For a
signing algorithm that population is **signed delegations**, not all delegations:
a zone that publishes no DS at all was never a candidate for using algorithm 13.
Diffusion is therefore computed on the strict panel (AFRINIC + ARIN), the two RIRs
whose delegation counts carry no step change.

The two measures disagree often enough to matter. Ed25519 appeared 5.6 years after
RFC 8080 and has still not reached 1% of signed delegations nine years on; reading
its first appearance as "adoption" would invert what the data says.

The unit of analysis is the **observable change**, not the RFC. RFC 5702 defines
two algorithms that appeared ten months apart, and RFC 6605 two that differ by four
months, so an RFC-level date would average away a real and repeated pattern: the
larger parameter of a pair always trails the smaller one.
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb

CORPUS = "out/reverse/corpus/reverse/*/*/*.parquet"
PANEL = ("afrinic", "arin")
OUT = Path("out/analysis")

#: Every algorithm-bearing observable change, with the RFC that introduced it and
#: the section that defines it. Publication dates come from rfc-index.xml via the
#: checklist; the section references are cited so a reader can check the claim.
CHANGES = {
    # section references marked (v) were read from the RFC text; the rest are
    # recorded as the defining document only, without a section claim.
    3:  ("DSA/SHA-1",        "RFC 2536", "1999-03", "defines algorithm 3"),
    5:  ("RSASHA1",          "RFC 3110", "2001-05", "defines algorithm 5"),
    7:  ("RSASHA1-NSEC3",    "RFC 5155", "2008-03", "defines algorithm 7"),
    8:  ("RSASHA256",        "RFC 5702", "2009-10", "s2.1 (v)"),
    10: ("RSASHA512",        "RFC 5702", "2009-10", "s2.2 (v)"),
    12: ("ECC-GOST",         "RFC 5933", "2010-07", "defines algorithm 12"),
    13: ("ECDSAP256SHA256",  "RFC 6605", "2012-04", "s7 IANA (v)"),
    14: ("ECDSAP384SHA384",  "RFC 6605", "2012-04", "s7 IANA (v)"),
    15: ("Ed25519",          "RFC 8080", "2017-02", "s5 (v)"),
    16: ("Ed448",            "RFC 8080", "2017-02", "s5 (v)"),
    17: ("SM2SM3",           "RFC 9563", "2024-12", "defines algorithm 17"),
    23: ("ECC-GOST12",       "RFC 9558", "2024-04", "defines algorithm 23"),
}

DIGESTS = {
    1: ("SHA-1 DS digest",   "RFC 3658", "2003-12", "defines digest type 1"),
    2: ("SHA-256 DS digest", "RFC 4509", "2006-05", "s5 IANA, MANDATORY (v)"),
    3: ("GOST DS digest",    "RFC 5933", "2010-07", "defines digest type 3"),
    4: ("SHA-384 DS digest", "RFC 6605", "2012-04", "s7 IANA, OPTIONAL (v)"),
    5: ("GOST-2012 digest",  "RFC 9558", "2024-04", "defines digest type 5"),
    6: ("SM3 DS digest",     "RFC 9563", "2024-12", "defines digest type 6"),
}


def months(a: str, b: str) -> int:
    return (int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))


def years(a: str | None, b: str | None) -> float | None:
    return round(months(a, b) / 12, 2) if (a and b) else None


def measure(con, column: str, catalogue: dict) -> list[dict]:
    """First appearance over the whole corpus; diffusion over the strict panel."""
    panel = ", ".join(f"'{p}'" for p in PANEL)

    # (a) Existence: earliest month anyone published this value, all RIRs.
    first = dict(con.execute(f"""
        SELECT {column} AS v, min(strftime(to_timestamp(timestamp/1000),'%Y-%m')) AS f
        FROM read_parquet('{CORPUS}') WHERE response_type='DS' AND {column} IS NOT NULL
        GROUP BY 1
    """).fetchall())

    # (b) Diffusion: share of signed delegations on the strict panel.
    df = con.execute(f"""
        WITH ds AS (
          SELECT strftime(to_timestamp(timestamp/1000),'%Y-%m-%d') AS day,
                 query_name, {column} AS v
          FROM read_parquet('{CORPUS}')
          WHERE response_type='DS' AND source IN ({panel})),
        tot AS (SELECT day, count(DISTINCT query_name) AS signed FROM ds GROUP BY 1),
        per AS (SELECT day, v, count(DISTINCT query_name) AS users FROM ds
                WHERE v IS NOT NULL GROUP BY 1,2)
        SELECT per.day, per.v, per.users, tot.signed
        FROM per JOIN tot USING (day) ORDER BY 1,2
    """).df()
    df["share"] = df.users / df.signed * 100
    panel_start = df.day.min()[:7] if len(df) else None

    rows = []
    for value, (name, rfc, published, section) in sorted(catalogue.items()):
        seen = first.get(value)
        sub = df[df.v == value].sort_values("day")

        def milestone(threshold):
            hit = sub[sub.share >= threshold]
            return hit.day.iloc[0][:7] if len(hit) else None

        m1, m10, m50 = (milestone(t) for t in (1, 10, 50))
        rows.append({
            "value": int(value),
            "change": name,
            "rfc": rfc,
            "section": section,
            "published": published,
            # existence
            "t_first_date": seen,
            "t_first_years": years(published, seen),
            "first_censored": bool(seen) and seen <= "2009-04",
            # diffusion
            "t_1pct_date": m1, "t_1pct_years": years(published, m1),
            "t_10pct_date": m10, "t_10pct_years": years(published, m10),
            "t_50pct_date": m50, "t_50pct_years": years(published, m50),
            "current_share_pct": round(float(sub.share.iloc[-1]), 3) if len(sub) else 0.0,
            "peak_share_pct": round(float(sub.share.max()), 3) if len(sub) else 0.0,
            # the quantity that separates the two measures
            "appearance_to_10pct_years": (
                years(seen, m10) if (seen and m10) else None),
            "diffusion_panel_starts": panel_start,
        })
    return rows


def main() -> None:
    con = duckdb.connect()
    con.execute("SET threads=8")
    OUT.mkdir(parents=True, exist_ok=True)

    algorithms = measure(con, "ds_algorithm", CHANGES)
    digests = measure(con, "ds_digest_type", DIGESTS)

    payload = {
        "definitions": {
            "t_first": ("Earliest month any DS record in the corpus carries this "
                        "value. An existence proof, computed over all five RIRs; "
                        "one operator settles it."),
            "t_N_pct": ("Earliest month the value reaches N% of SIGNED delegations "
                        "on the strict panel (AFRINIC + ARIN). A population "
                        "statement; the denominator is the set of zones that could "
                        "have adopted it, i.e. those already publishing a DS."),
            "appearance_to_10pct": ("Years between existence and the population "
                                    "reaching 10%. The quantity that separates "
                                    "'someone did this' from 'this was adopted'."),
        },
        "algorithms": algorithms,
        "digest_types": digests,
    }
    (OUT / "adoption_measures.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")

    for label, rows in (("SIGNING ALGORITHMS", algorithms), ("DS DIGEST TYPES", digests)):
        print(f"\n=== {label} ===")
        print(f"{'':4} {'change':18} {'RFC':9} {'pub':8} {'first':8} "
              f"{'t_first':>8} {'t_10%':>8} {'gap':>7} {'now':>7}")
        for r in rows:
            first = r["t_first_years"]
            ten = r["t_10pct_years"]
            gap = r["appearance_to_10pct_years"]
            s_first = f"{first:.1f}y" if first is not None else "-"
            s_ten = f"{ten:.1f}y" if ten is not None else "never"
            s_gap = f"{gap:.1f}y" if gap is not None else "-"
            # A value present on the corpus's first day was already deployed when
            # measurement began, so its lag is an upper bound.
            star = "*" if r["first_censored"] else " "
            print(f"{r['value']:>4} {r['change']:18} {r['rfc']:9} {r['published']:8} "
                  f"{str(r['t_first_date'] or '-'):7}{star} {s_first:>8} "
                  f"{s_ten:>8} {s_gap:>7} {r['current_share_pct']:6.1f}%")
        print("     * present on the corpus's first day: lag is an upper bound")
    print(f"\nwrote {OUT / 'adoption_measures.json'}")


if __name__ == "__main__":
    main()
