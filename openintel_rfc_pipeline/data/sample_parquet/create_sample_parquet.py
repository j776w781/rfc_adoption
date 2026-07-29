#!/usr/bin/env python
"""Generate the sample OpenINTEL-style Parquet file used by the demo.

Run it directly::

    python data/sample_parquet/create_sample_parquet.py [--out PATH]

The output lands next to this script (``sample_openintel.parquet``) unless
``--out`` says otherwise. The script is deliberately standalone: it imports
nothing from ``openintel_rfc`` so that regenerating the fixture never depends on
the package it is a fixture for.

What the data is for
--------------------
The rows are hand-built rather than sampled, because the demo has to exercise
every branch of the matcher. Each row belongs to one of the cases below, which
map one-to-one onto the worked expectations in the build contract:

1. CDS delete signal (algorithm 0, digest type 0) after RFC 8078's publication.
2. The same delete signal *before* RFC 8078 was published, which must be
   rejected by the publication-date cutoff even though the record matches.
3. NSEC3 / NSEC3PARAM, uniquely attributable to RFC 5155.
4. DS with digest type 2 (RFC 4509), plus SHA-1 (digest type 1) rows that must
   *not* match it.
5. ECDSA algorithms 13 / 14 (RFC 6605).
6. EdDSA algorithms 15 / 16 (RFC 8080).
7. Plain RSASHA256 (algorithm 8) records: base DNSSEC only (RFC 4033/4034/4035).
8. CDS with no algorithm and no digest type: the partial, ambiguous case.
9. (No data.) Resolver-side validator support is not observable in this corpus
   at all; it is exercised by the checklist and dictionary, not by rows.

The ``flags`` column is populated only from 2016 onward, matching the
dictionary's ``available_from`` for that field, so the availability warning the
schema checker raises is grounded in the data rather than asserted.

Determinism
-----------
Row content is fixed, key tags and measurement times come from a seeded RNG, and
the rows are sorted before writing. There is no call to ``datetime.now()``.
Regenerating the file on any machine produces the same rows in the same order.

Nullability
-----------
``algorithm``, ``digest_type`` and ``key_tag`` use pandas' nullable ``Int64``
dtype rather than ``float64``. That distinction is load-bearing: with
``float64`` a missing algorithm round-trips as ``NaN`` and a present one as
``13.0``, and "algorithm 0" (the RFC 8078 delete signal) becomes impossible to
tell apart from "no algorithm recorded".
"""

from __future__ import annotations

import argparse
import random
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

#: Seed for key tags and measurement times. Any fixed value would do; this one
#: is the date of the RFC 8078 example observation in the contract.
SEED = 20180501

DEFAULT_FILENAME = "sample_openintel.parquet"

#: Column order of the generated file (the normalized analysis view).
COLUMNS: tuple[str, ...] = (
    "timestamp",
    "domain",
    "zone",
    "rr_type",
    "algorithm",
    "digest_type",
    "key_tag",
    "flags",
    "source",
    "measurement_id",
)

INTEGER_COLUMNS: tuple[str, ...] = ("algorithm", "digest_type", "key_tag")
STRING_COLUMNS: tuple[str, ...] = (
    "domain",
    "zone",
    "rr_type",
    "flags",
    "source",
    "measurement_id",
)

CASE_LABELS: dict[str, str] = {
    "1": "CDS delete signal, 2018-2021 (RFC 8078 valid)",
    "2": "CDS delete signal, 2015-2016 (pre-RFC 8078 cutoff)",
    "3": "NSEC3 / NSEC3PARAM, algorithm 1 (RFC 5155)",
    "4a": "DS digest type 2 / SHA-256 (RFC 4509)",
    "4b": "DS digest type 1 / SHA-1 (must not match RFC 4509)",
    "5": "DNSKEY / RRSIG algorithm 13, 14 (RFC 6605)",
    "6": "DNSKEY algorithm 15, 16 (RFC 8080)",
    "7": "DNSKEY / RRSIG / DS / NSEC algorithm 8 (base DNSSEC)",
    "8": "CDS with no algorithm and no digest type (partial)",
}

#: Sentinel: draw a plausible key tag from the seeded RNG.
DRAW = "<draw>"


# --------------------------------------------------------------------------- #
# Row construction
# --------------------------------------------------------------------------- #


def build_rows() -> list[dict[str, Any]]:
    """Build every sample row, in a fixed and reproducible order."""
    rng = random.Random(SEED)
    rows: list[dict[str, Any]] = []

    def add(
        case: str,
        day: str,
        domain: str,
        rr_type: str,
        *,
        algorithm: int | None,
        digest_type: int | None,
        key_tag: int | str | None,
        flags: str | None = None,
    ) -> None:
        # OpenINTEL runs its daily measurement in the early UTC hours; the exact
        # minute is irrelevant to the analysis but keeps timestamps realistic.
        moment = datetime.strptime(day, "%Y-%m-%d").replace(
            hour=rng.randrange(0, 6),
            minute=rng.randrange(0, 60),
            second=rng.randrange(0, 60),
        )
        tag = rng.randrange(1024, 65535) if key_tag is DRAW else key_tag
        zone = domain.rsplit(".", 1)[-1]
        sequence = len(rows) + 1
        rows.append(
            {
                "case": case,
                "sequence": sequence,
                "timestamp": moment,
                "domain": domain,
                "zone": zone,
                "rr_type": rr_type,
                "algorithm": algorithm,
                "digest_type": digest_type,
                "key_tag": tag,
                "flags": flags,
                "source": f"zonefile-{zone}",
                "measurement_id": f"oi-{day}-{sequence:04d}",
            }
        )

    # -- Case 1: RFC 8078 delete signal, published 2017-03-01 --------------- #
    # Algorithm 0 is reserved and never valid in a real CDS, which is precisely
    # why RFC 8078 could repurpose it as "remove all my DS records".
    for day, domain in (
        ("2018-05-01", "delete-signal.nl"),
        ("2018-06-14", "example.com"),
        ("2018-09-03", "dnssec-demo.org"),
        ("2018-11-20", "keyroll.nu"),
        ("2019-02-11", "example.nl"),
        ("2019-05-07", "rollover-test.net"),
        ("2019-08-19", "delete-signal.nl"),
        ("2020-01-13", "example.com"),
        ("2020-04-06", "dnssec-demo.org"),
        ("2020-10-05", "keyroll.nu"),
        ("2021-03-15", "example.nl"),
        ("2021-07-26", "rollover-test.net"),
    ):
        add("1", day, domain, "CDS", algorithm=0, digest_type=0, key_tag=0)

    # -- Case 2: the same record shape, before RFC 8078 existed ------------- #
    # These are real CDS records (so RFC 7344 still matches) but they cannot be
    # evidence of RFC 8078 adoption, because RFC 8078 was not published yet.
    for day, domain in (
        ("2015-04-08", "example.com"),
        ("2015-09-22", "delete-signal.nl"),
        ("2016-01-15", "dnssec-demo.org"),
        ("2016-05-30", "example.nl"),
        ("2016-11-02", "keyroll.nu"),
    ):
        add("2", day, domain, "CDS", algorithm=0, digest_type=0, key_tag=0)

    # -- Case 3: RFC 5155 hashed authenticated denial of existence ---------- #
    # Hash algorithm 1 (SHA-1) is the only value RFC 5155 defines. Pre-2016 rows
    # carry no flags, matching the dictionary's available_from for that field.
    for day, domain, rr_type, flags in (
        ("2010-06-15", "hashed-denial.nu", "NSEC3", None),
        ("2011-03-09", "example.com", "NSEC3PARAM", None),
        ("2012-07-24", "example.nl", "NSEC3", None),
        ("2013-02-18", "dnssec-demo.org", "NSEC3PARAM", None),
        ("2014-09-30", "signed-example.se", "NSEC3", None),
        ("2015-05-12", "hashed-denial.nu", "NSEC3PARAM", None),
        ("2016-08-04", "example.com", "NSEC3", "0"),
        ("2017-11-21", "example.nl", "NSEC3PARAM", "0"),
        ("2018-03-08", "dnssec-demo.org", "NSEC3", "1"),
        ("2019-09-17", "signed-example.se", "NSEC3PARAM", "0"),
    ):
        add("3", day, domain, rr_type, algorithm=1, digest_type=None, key_tag=None, flags=flags)

    # -- Case 4a: RFC 4509, SHA-256 DS digests ------------------------------ #
    for day, domain in (
        ("2012-03-14", "example.com"),
        ("2013-06-27", "example.net"),
        ("2014-01-09", "dnssec-demo.nl"),
        ("2015-04-22", "signed-example.se"),
        ("2016-07-13", "example.org"),
        ("2017-10-26", "keyroll.nu"),
        ("2018-02-06", "example.com"),
        ("2019-06-18", "dnssec-demo.nl"),
        ("2020-09-29", "example.net"),
        ("2021-05-11", "example.org"),
    ):
        add("4a", day, domain, "DS", algorithm=8, digest_type=2, key_tag=DRAW)

    # -- Case 4b: SHA-1 DS digests, the RFC 4509 negative control ----------- #
    # Digest type 1 predates RFC 4509; these rows must fail its condition rather
    # than match it weakly.
    for day, domain in (
        ("2011-02-15", "legacy-sha1.com"),
        ("2012-08-21", "legacy-sha1.com"),
        ("2013-11-05", "example.net"),
        ("2014-04-17", "example.org"),
    ):
        add("4b", day, domain, "DS", algorithm=8, digest_type=1, key_tag=DRAW)

    # -- Case 5: RFC 6605 ECDSA (algorithms 13 and 14) ---------------------- #
    for day, domain, rr_type, algorithm, flags in (
        ("2013-07-02", "ecdsa-demo.com", "DNSKEY", 13, None),
        ("2014-05-19", "ecdsa-demo.com", "RRSIG", 13, None),
        ("2015-08-27", "example.nl", "DNSKEY", 13, None),
        ("2016-03-10", "ecdsa-demo.com", "DNSKEY", 13, "257"),
        ("2017-06-23", "example.org", "RRSIG", 13, None),
        ("2018-09-04", "signed-example.se", "DNSKEY", 13, "256"),
        ("2019-12-16", "ecdsa-demo.com", "RRSIG", 13, None),
        ("2016-11-28", "example.net", "DNSKEY", 14, "257"),
        ("2018-04-09", "example.net", "RRSIG", 14, None),
        ("2020-07-21", "dnssec-demo.nl", "DNSKEY", 14, "257"),
    ):
        add(
            "5", day, domain, rr_type,
            algorithm=algorithm, digest_type=None, key_tag=DRAW, flags=flags,
        )

    # -- Case 6: RFC 8080 EdDSA (algorithms 15 and 16) ---------------------- #
    for day, domain, algorithm, flags in (
        ("2018-01-08", "eddsa-demo.se", 15, "257"),
        ("2018-08-14", "keyroll.nu", 15, None),
        ("2019-03-25", "eddsa-demo.se", 15, "256"),
        ("2019-11-06", "dnssec-demo.org", 15, None),
        ("2020-05-18", "eddsa-demo.se", 15, "257"),
        ("2021-02-01", "example.com", 15, None),
        ("2019-07-30", "eddsa-demo.se", 16, None),
        ("2021-09-13", "dnssec-demo.nl", 16, "257"),
    ):
        add(
            "6", day, domain, "DNSKEY",
            algorithm=algorithm, digest_type=None, key_tag=DRAW, flags=flags,
        )

    # -- Case 7: base DNSSEC, RSASHA256 ------------------------------------- #
    # Nothing here is attributable to any post-2005 mechanism. The DS rows use
    # digest type 1 on purpose so they stay outside RFC 4509.
    for day, domain, rr_type, digest_type, flags in (
        ("2011-05-24", "example.com", "DNSKEY", None, None),
        ("2012-02-07", "example.com", "RRSIG", None, None),
        ("2012-12-11", "example.org", "NSEC", None, None),
        ("2013-09-03", "example.nl", "DNSKEY", None, None),
        ("2014-06-16", "signed-example.se", "RRSIG", None, None),
        ("2015-11-24", "example.net", "NSEC", None, None),
        ("2016-04-05", "dnssec-demo.org", "DNSKEY", None, "256"),
        ("2017-08-15", "example.nl", "RRSIG", None, None),
        ("2018-12-04", "keyroll.nu", "DS", 1, None),
        ("2019-10-22", "example.com", "RRSIG", None, None),
    ):
        add(
            "7", day, domain, rr_type,
            algorithm=8, digest_type=digest_type, key_tag=DRAW, flags=flags,
        )

    # -- Case 8: CDS with neither algorithm nor digest type ----------------- #
    # RFC 7344 still matches (the record type is the evidence) but RFC 8078
    # cannot be decided: its required condition is over a field the row does not
    # carry, which is a missing_fields review item, not a match and not a
    # rejection.
    for day, domain, key_tag in (
        ("2019-04-12", "example.nl", DRAW),
        ("2019-08-26", "dnssec-demo.org", None),
        ("2020-02-14", "example.com", DRAW),
        ("2020-11-30", "keyroll.nu", None),
    ):
        add("8", day, domain, "CDS", algorithm=None, digest_type=None, key_tag=key_tag)

    # Chronological order with a total tie-break, so the file is byte-stable.
    rows.sort(key=lambda row: (row["timestamp"], row["domain"], row["rr_type"], row["sequence"]))
    return rows


def build_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Assemble the rows into a frame with Parquet-safe nullable dtypes."""
    frame = pd.DataFrame(rows)[list(COLUMNS)]
    frame["timestamp"] = pd.to_datetime(frame["timestamp"]).astype("datetime64[ns]")
    for column in INTEGER_COLUMNS:
        frame[column] = frame[column].astype("Int64")
    for column in STRING_COLUMNS:
        frame[column] = frame[column].astype("string")
    return frame.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Round-trip verification
# --------------------------------------------------------------------------- #


def verify_round_trip(path: Path) -> list[str]:
    """Re-read the file and confirm nullable integers survived the round trip.

    The failure this guards against is silent: pandas will happily widen an
    integer column with nulls to ``float64``, at which point every algorithm
    number comes back as ``13.0`` and every missing one as ``NaN``.
    """
    reread = pd.read_parquet(path)
    lines: list[str] = []

    algorithm = reread["algorithm"]
    null_count = int(algorithm.isna().sum())
    present = algorithm.dropna()
    if null_count == 0:
        raise AssertionError("expected at least one null algorithm in the sample data")
    if not len(present):
        raise AssertionError("expected at least one populated algorithm")

    sample_present = present.iloc[0]
    if isinstance(sample_present, float):
        raise AssertionError(
            f"algorithm read back as float ({sample_present!r}); use a nullable Int64 dtype"
        )
    if int(sample_present) != sample_present:
        raise AssertionError(f"algorithm read back non-integral: {sample_present!r}")

    lines.append(
        f"algorithm dtype {reread['algorithm'].dtype}: "
        f"{null_count} null -> <NA>, {len(present)} present -> int "
        f"(first value {int(sample_present)})"
    )
    lines.append(
        f"digest_type dtype {reread['digest_type'].dtype}, "
        f"key_tag dtype {reread['key_tag'].dtype}, "
        f"timestamp dtype {reread['timestamp'].dtype}"
    )

    pre_2016_flags = reread.loc[reread["timestamp"] < "2016-01-01", "flags"]
    post_2016_flags = reread.loc[reread["timestamp"] >= "2016-01-01", "flags"]
    if pre_2016_flags.notna().any():
        raise AssertionError("flags must be null before its available_from date")
    if not post_2016_flags.notna().any():
        raise AssertionError("expected populated flags values after 2016-01-01")
    lines.append(
        f"flags: {int(pre_2016_flags.isna().sum())} null pre-2016, "
        f"{int(post_2016_flags.notna().sum())} populated post-2016"
    )
    return lines


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the deterministic sample OpenINTEL Parquet fixture."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output path (default: sample_openintel.parquet next to this script).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    here = Path(__file__).resolve().parent
    out_path = Path(args.out).resolve() if args.out else here / DEFAULT_FILENAME
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = build_rows()
    frame = build_frame(rows)
    frame.to_parquet(out_path, engine="pyarrow", index=False)

    case_counts: dict[str, int] = {}
    for row in rows:
        case_counts[row["case"]] = case_counts.get(row["case"], 0) + 1

    print(f"Wrote {out_path}")
    print(f"  rows            : {len(frame)}")
    print(f"  columns         : {', '.join(COLUMNS)}")
    print(
        "  date range      : "
        f"{frame['timestamp'].min():%Y-%m-%d} .. {frame['timestamp'].max():%Y-%m-%d}"
    )
    print(f"  distinct domains: {frame['domain'].nunique()}")
    print(f"  distinct zones  : {', '.join(sorted(frame['zone'].dropna().unique()))}")
    print("  rows per case:")
    for case in sorted(case_counts):
        print(f"    case {case:<3} {CASE_LABELS[case]:<52} {case_counts[case]:>3}")
    print("  round-trip checks:")
    for line in verify_round_trip(out_path):
        print(f"    {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
