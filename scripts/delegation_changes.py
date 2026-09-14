"""Per-delegation DNSSEC change ledger, and what level of operator made each change.

The monthly timeline says how many delegations carried a value; it cannot say
*which*, so it cannot tell one operator re-signing ten thousand zones from ten
thousand operators each re-signing one. The raw reverse corpus can: it carries a
row per delegation per measurement day, so following `query_name` month to month
gives every individual change with a date.

Three operator levels, coarsest first:

    RIR          the registry the delegation sits under (5)
    block        the parent zone one label up -- `96.192.in-addr.arpa` for
                 `26.96.192.in-addr.arpa`. In reverse DNS this is an allocation,
                 so it approximates "one network operator".
    delegation   the zone itself

A change is attributed to the coarsest level at which it is coherent: if every
delegation that changed in a month sits under one block, the block made the
change; if the change spans many blocks in one RIR, it happened above them.

Works on either corpus. The reverse (RIR) per-day records are in this repository;
the forward (OpenINTEL) ones are not, but the moment they exist this runs over
them unchanged -- the column names differ between the two and are resolved by
candidate rather than hardcoded.

    # reverse, the default
    python scripts/delegation_changes.py

    # forward, once out/full_run has written a zonefile corpus
    python scripts/delegation_changes.py --corpus <root>/zonefile --basis zonefile \
        --out out/analysis/forward
"""
from __future__ import annotations

import argparse
import glob
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

MONTH = re.compile(r"/(\d{4}-\d{2})-\d{2}/")

#: Column names differ between the ingested RIPE corpus and OpenINTEL's own
#: parquet, and between OpenINTEL vintages. Resolve by candidate so a schema
#: change is a miss to report rather than a silent empty result.
NAME_COLS = ("query_name", "domain", "name")
TYPE_COLS = ("response_type", "rr_type", "type")
ALG_COLS = {"DS": ("ds_algorithm", "algorithm"),
            "DNSKEY": ("dnskey_algorithm", "algorithm")}


def pick(columns, candidates, what, path):
    for c in candidates:
        if c in columns:
            return c
    raise SystemExit(
        f"{path}: no column for {what}. Tried {list(candidates)}; file has "
        f"{sorted(columns)[:12]}...")

#: A cluster this size or larger, all making the same transition in one month
#: under one block, is a bulk action. The cut is reported alongside the full
#: size distribution so it can be moved: it is a labelling convenience, not a
#: finding.
BULK_MIN = 5


def block_of(name: str) -> str:
    """Parent zone one label up; the delegation itself if it has no parent."""
    head, _, rest = name.partition(".")
    return rest if rest.count(".") >= 2 else name


def ledger(corpus: Path, record: str = "DS") -> pd.DataFrame:
    rows = []
    for src_dir in sorted(p for p in corpus.iterdir() if p.is_dir()):
        source = src_dir.name
        if source.startswith("_"):          # _summary is derived, not a corpus
            continue
        prev = None
        for f in sorted(glob.glob(str(src_dir / "*" / "*.parquet"))):
            month = MONTH.search(f).group(1)
            available = pq.ParquetFile(f).schema_arrow.names
            name_c = pick(available, NAME_COLS, "the zone name", f)
            type_c = pick(available, TYPE_COLS, "the record type", f)
            alg_c = pick(available, ALG_COLS[record], f"the {record} algorithm", f)
            df = pd.read_parquet(f, columns=[name_c, type_c, alg_c])
            ds = df[(df[type_c] == record) & df[alg_c].notna()]
            cur = (ds.groupby(name_c)[alg_c]
                   .apply(lambda s: frozenset(int(x) for x in s)).to_dict())
            if prev is not None:
                for name in set(prev) | set(cur):
                    before, after = prev.get(name, frozenset()), cur.get(name, frozenset())
                    if before == after:
                        continue
                    if not before:
                        kind = "sign"
                    elif not after:
                        kind = "unsign"
                    else:
                        kind = "rollover"
                    rows.append({
                        "month": month, "source": source, "delegation": name,
                        "block": block_of(name), "kind": kind,
                        "from_alg": ",".join(map(str, sorted(before))),
                        "to_alg": ",".join(map(str, sorted(after))),
                    })
            prev = cur
        print(f"  {source:8} {len([r for r in rows if r['source'] == source]):>7} changes")
    return pd.DataFrame(rows)


def clusters(led: pd.DataFrame) -> pd.DataFrame:
    """Group changes into actions: one month, one transition, one block."""
    g = (led.groupby(["month", "source", "block", "kind", "from_alg", "to_alg"])
         .agg(n_delegations=("delegation", "nunique")).reset_index())
    g["scale"] = g.n_delegations.map(lambda n: "bulk" if n >= BULK_MIN else
                                     ("small group" if n > 1 else "single delegation"))
    return g


def attribute(led: pd.DataFrame) -> pd.DataFrame:
    """Where each month's transition sits, and how concentrated it is.

    "Spans many blocks" alone does not mean coordinated: signing with algorithm 8
    was a commonplace thing to do, and many unrelated operators doing a common
    thing in one month looks identical to one actor doing it everywhere. So
    concentration is measured rather than inferred -- the share of the change
    sitting in its largest block, and a Herfindahl index over blocks.
    """
    out = []
    for (month, source, kind, frm, to), part in led.groupby(
            ["month", "source", "kind", "from_alg", "to_alg"]):
        per_block = part.groupby("block").delegation.nunique()
        dels = int(per_block.sum())
        blocks = int(len(per_block))
        top = float(per_block.max()) / dels
        hhi = float(((per_block / dels) ** 2).sum())
        if dels == 1:
            level = "single delegation"
        elif blocks == 1:
            level = "one block"
        elif top >= 0.5:
            level = "concentrated (one block is most of it)"
        else:
            level = "diffuse (many blocks)"
        out.append({"month": month, "source": source, "kind": kind, "from_alg": frm,
                    "to_alg": to, "n_delegations": dels, "n_blocks": blocks,
                    "largest_block_share": round(top, 3), "hhi": round(hhi, 4),
                    "level": level})
    return pd.DataFrame(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, default=Path("out/reverse/corpus/reverse"))
    ap.add_argument("--basis", default="reverse", choices=["reverse", "zonefile"])
    ap.add_argument("--record", default=None, choices=["DS", "DNSKEY"],
                    help="Default: DS for both, which is what makes the two corpora "
                         "comparable -- it is the delegation either way.")
    ap.add_argument("--out", type=Path, default=Path("out/analysis"))
    args = ap.parse_args()
    record = args.record or "DS"

    if not args.corpus.exists():
        raise SystemExit(
            f"no corpus at {args.corpus}.\n"
            "For the forward side, run scripts/full_timeline.py --stage index "
            "--roots <openintel mirror> first; out/full_run is its output, not its "
            "input.")

    print(f"building the per-delegation change ledger "
          f"({args.basis} corpus, {record} records)")
    led = ledger(args.corpus, record=record)
    args.out.mkdir(parents=True, exist_ok=True)
    led.to_parquet(args.out / "delegation_changes.parquet", index=False)

    cl = clusters(led)
    at = attribute(led)
    cl.to_parquet(args.out / "delegation_change_clusters.parquet", index=False)
    at.to_parquet(args.out / "delegation_change_levels.parquet", index=False)

    print(f"\n{len(led):,} change events, {led.delegation.nunique():,} distinct "
          f"delegations, {led.month.min()} .. {led.month.max()}")
    print("\nby kind:")
    for k, n in led.kind.value_counts().items():
        print(f"  {k:10} {n:>7,}")
    print(f"\nactions (month x transition x block), bulk = >= {BULK_MIN} delegations:")
    for s, n in cl.scale.value_counts().items():
        share = cl[cl.scale == s].n_delegations.sum() / cl.n_delegations.sum() * 100
        print(f"  {s:18} {n:>6,} actions  covering {share:5.1f}% of changed delegations")
    print("\nconcentration of each (month, transition):")
    for lv, n in at.level.value_counts().items():
        share = at[at.level == lv].n_delegations.sum() / at.n_delegations.sum() * 100
        print(f"  {lv:40} {n:>6,}  {share:5.1f}% of delegations")
    print(f"\nwrote {args.out}/delegation_changes.parquet and two summaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
