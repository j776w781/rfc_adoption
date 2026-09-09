"""Cross-reference DNS software release dates against observed first use.

Onset -- RFC publication to the first zone carrying the value -- is one number
covering two very different waits: for somebody to write the code, and for
somebody to switch it on. This splits them.

    onset = code lag (RFC -> first release able to publish it)
          + deployment lag (that release -> first zone observed)

Publishing needs a signer, so the code lag for a signing algorithm is set by the
earliest *signer* release, not by the earliest release of anything. Validation is
tracked separately because a zone can publish a value no resolver understands,
and RFC 5218's "incrementally deployable" argument turns on exactly that gap.

Reads out/server_run/timeline_monthly.parquet and data/software/software_support.json.
Writes out/analysis/software_crossref.json.

    python scripts/software_crossref.py [--timeline PATH] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

#: Publication dates of the RFCs that introduce each observable.
RFC_PUBLISHED = {
    "RFC 5155": "2008-03", "RFC 5702": "2009-10", "RFC 5933": "2010-07",
    "RFC 6605": "2012-04", "RFC 7344": "2014-09", "RFC 8078": "2017-03",
    "RFC 8080": "2017-02", "RFC 5011": "2007-09", "RFC 9276": "2022-08",
}

#: Observable -> (timeline dimension, codepoints). Signing algorithms only: these
#: are the ones where "who had to implement something" is a real question.
#: Forward carries DNSKEY; reverse carries delegations only, so the same
#: algorithm is visible there as the DS algorithm. Existence is a minimum over
#: all available evidence, so first-seen takes both dimensions.
#:
#: Counting must not. A signed forward zone appears under BOTH algorithm_dnskey
#: and algorithm_ds -- .se 2016-10 has 11,046 zones by DNSKEY and 10,904 of the
#: same zones by DS -- so any sum over dimensions doubles the population. JUMP_DIM
#: names the single dimension the zone counts come from.
OBSERVABLES = {
    "alg 8/10":    (["algorithm_dnskey", "algorithm_ds"], ["8", "10"],       "RFC 5702"),
    "alg 12":      (["algorithm_dnskey", "algorithm_ds"], ["12"],            "RFC 5933"),
    "alg 13/14":   (["algorithm_dnskey", "algorithm_ds"], ["13", "14"],      "RFC 6605"),
    "alg 15/16":   (["algorithm_dnskey", "algorithm_ds"], ["15", "16"],      "RFC 8080"),
    "CDS/CDNSKEY": (["rr_type"],                          ["CDS", "CDNSKEY"], "RFC 7344"),
}
JUMP_DIM = {"alg 8/10": "algorithm_dnskey", "alg 12": "algorithm_dnskey",
            "alg 13/14": "algorithm_dnskey", "alg 15/16": "algorithm_dnskey",
            "CDS/CDNSKEY": "rr_type"}

#: Capabilities that let a zone *publish* the value. "rrtype" and
#: "algorithm-aware" deliberately do not count -- Knot 2.4.0 shipped EdDSA
#: constants a month before RFC 8080 and said in the same commit that it could
#: not yet sign with them.
PUBLISHING = {"sign", "publish"}
VALIDATING = {"validate"}

#: Implementations ship one curve at a time, so a support row may name "alg 15"
#: where the observable groups 15 and 16. Fold the parts into the group.
OBSERVABLE_ALIASES = {"alg 15": "alg 15/16", "alg 16": "alg 15/16",
                      "alg 13": "alg 13/14", "alg 14": "alg 13/14",
                      "alg 8": "alg 8/10",   "alg 10": "alg 8/10"}


def obs_key(name: str) -> str:
    return OBSERVABLE_ALIASES.get(name, name)

#: TLDs sharing a registry operator. Two zones moving in the same month under one
#: operator is one decision, not two, and the pairing is what makes that legible.
OPERATORS = {
    "se": "Swedish Internet Foundation", "nu": "Swedish Internet Foundation",
    "ch": "SWITCH", "li": "SWITCH",
    "gov": "US GSA", "fed.us": "US GSA", "ee": "Estonian Internet Foundation",
}


def months_between(a: str, b: str) -> float:
    """Whole months from YYYY-MM a to YYYY-MM b, in years."""
    ya, ma = int(a[:4]), int(a[5:7])
    yb, mb = int(b[:4]), int(b[5:7])
    return ((yb - ya) * 12 + (mb - ma)) / 12.0


def _ym(d: str) -> str:
    return d[:7]


def load_timeline(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def first_seen(df: pd.DataFrame, dims: list[str], values: list[str]) -> tuple:
    """First month the value appears in any corpus, with zone count and corpus.

    Returns (month, zones, basis, censored). `censored` marks a first sighting in
    that corpus's opening month, which is an upper bound and not a measurement.
    """
    sel = df[(df.dimension.isin(dims)) & (df.value.isin(values)) & (df.domains_peak > 0)]
    if sel.empty:
        return None, 0, None, None
    m = sel.month.min()
    hit = sel[sel.month == m]
    basis = sorted(hit.basis.unique())
    opening = df[df.basis.isin(basis)].month.min()
    # Largest single dimension, never a sum: the same zone is counted by both its
    # DNSKEY and its DS.
    zones = int(hit.groupby("dimension").domains_peak.sum().max())
    return m, zones, "+".join(basis), m == opening


def source_entry(fwd: pd.DataFrame) -> dict[str, str]:
    """First month each source appears, so corpus entry is not read as a jump."""
    return fwd.groupby("source").month.min().to_dict()


def spikes(fwd: pd.DataFrame, dim: str, values: list[str], entry: dict[str, str],
           min_zones: int = 500) -> list[dict]:
    """Month-on-month jumps larger than half the running maximum.

    A zone count that more than half again itself in one month is not a
    population of operators independently deciding; it is one actor moving a
    portfolio. The corpus-entry month of each source is excluded, because a
    source appearing looks identical to every value in it appearing at once.
    """
    sel = (fwd[(fwd.dimension == dim) & (fwd.value.isin(values))]
           .groupby(["source", "month"]).domains_peak.sum().unstack(0).fillna(0).sort_index())
    out = []
    for src in sel.columns:
        series, delta = sel[src], sel[src].diff()
        prev_max = series.cummax().shift()
        for month in series.index:
            d = delta.get(month, 0)
            if month == entry.get(src) or d < min_zones:
                continue
            if pd.notna(prev_max.get(month)) and d > max(prev_max[month] * 0.5, 0):
                out.append({"month": month, "source": src, "operator": OPERATORS.get(src, "?"),
                            "delta_zones": int(d), "zones_after": int(series[month])})
    return sorted(out, key=lambda r: (r["month"], r["source"]))


def decompose(support: list[dict], fwd: pd.DataFrame) -> list[dict]:
    rows = []
    for obs, (dims, values, rfc) in OBSERVABLES.items():
        pub = RFC_PUBLISHED[rfc]
        seen, n, basis, censored = first_seen(fwd, dims, values)
        # A private codepoint proves the crypto was ready, not that the RFC was
        # implemented; nothing published under it is an observation of this RFC.
        cands = [s for s in support
                 if obs_key(s["observable"]) == obs and s.get("standard_codepoint", True)]
        pubcap = [s for s in cands if s["capability"] in PUBLISHING]
        valcap = [s for s in cands if s["capability"] in VALIDATING]
        earliest_pub = min(pubcap, key=lambda s: s["released"], default=None)
        earliest_val = min(valcap, key=lambda s: s["released"], default=None)

        row = {"observable": obs, "rfc": rfc, "rfc_published": pub,
               "first_zone_seen": seen, "zones_at_first_sight": n,
               "first_seen_basis": basis, "corpus_left_censored": censored}
        if earliest_pub:
            rel = _ym(earliest_pub["released"])
            row["first_signer"] = f'{earliest_pub["implementation"]} {earliest_pub["first_release"]}'
            row["first_signer_released"] = rel
            row["code_lag_years"] = round(months_between(pub, rel), 1)
            if seen:
                row["deployment_lag_years"] = round(months_between(rel, seen), 1)
        if earliest_val:
            rel = _ym(earliest_val["released"])
            row["first_validator"] = f'{earliest_val["implementation"]} {earliest_val["first_release"]}'
            row["first_validator_released"] = rel
        if seen:
            row["onset_years"] = round(months_between(pub, seen), 1)
        rows.append(row)
    return rows


def share_series(df: pd.DataFrame, dims: list[str], values: list[str]) -> pd.Series:
    """Share of signed zones carrying the value, on whichever corpus spans longest.

    Reverse runs 2009-2026 but carries delegations only; forward carries DNSKEY
    but starts 2016-06. Mixing them would put a 99.6% composition break in the
    middle of the series, so one basis is chosen and named.
    """
    best = None
    for basis in df.basis.unique():
        b = df[df.basis == basis]
        for dim in dims:
            sel = b[(b.dimension == dim) & (b.value.isin(values))]
            tot = b[(b.dimension == dim) & (b.value == "_total")]
            if not sel.empty and not tot.empty:
                break
        if sel.empty or tot.empty:
            continue
        num = sel.groupby("month").domains_peak.sum()
        den = tot.groupby("month").domains_peak.sum()
        ser = (num / den * 100).dropna()
        if best is None or len(ser) > len(best[1]):
            best = (basis, ser)
    return pd.Series(dtype=float) if best is None else best[1].rename(best[0])


def overlap(df: pd.DataFrame) -> list[dict]:
    """Was the predecessor still spreading when its successor was published?

    "Still deploying" is made concrete: what fraction of its eventual peak had
    the predecessor reached on the month the successor's RFC came out. Under 90%
    means the older mechanism was still on its way up when the newer one was
    standardised.
    """
    series = {obs: share_series(df, dims, vals)
              for obs, (dims, vals, _) in OBSERVABLES.items()}
    out = []
    items = [(obs, meta) for obs, meta in OBSERVABLES.items()]
    items.sort(key=lambda kv: RFC_PUBLISHED[kv[1][2]])
    for i, (later_obs, later_meta) in enumerate(items):
        pub = RFC_PUBLISHED[later_meta[2]]
        for earlier_obs, earlier_meta in items[:i]:
            ser = series.get(earlier_obs)
            if ser is None or ser.empty or pub < ser.index.min():
                continue
            at = ser[ser.index <= pub]
            if at.empty:
                continue
            now, peak = float(at.iloc[-1]), float(ser.max())
            out.append({
                "successor": later_meta[2], "successor_published": pub,
                "predecessor": earlier_meta[2], "predecessor_observable": earlier_obs,
                "predecessor_basis": ser.name,
                "predecessor_share_at_publication": round(now, 2),
                "predecessor_peak_share": round(peak, 2),
                "predecessor_peak_month": str(ser.idxmax()),
                "fraction_of_peak_reached": round(now / peak, 2) if peak else None,
                "still_spreading": bool(peak and now / peak < 0.9),
            })
    return out


def iteration_collapse(fwd: pd.DataFrame, limits: list[dict]) -> dict:
    """NSEC3 iteration counts against the dates validators started refusing them.

    This is the one mechanism where the causal direction is legible from the
    outside. Zone operators cannot be made to change an algorithm, but a zone
    whose iteration count exceeds what resolvers accept stops validating, so the
    operator either lowers it or goes dark. The question is whether the counts
    moved when the resolvers moved.
    """
    it = fwd[fwd.dimension == "nsec3_iterations"].copy()
    it["iv"] = pd.to_numeric(it.value, errors="coerce")
    it = it.dropna(subset=["iv"])
    high = it[it.iv >= 100].groupby(["month", "source"]).domains_peak.sum().unstack().fillna(0)
    zero = it[it.iv == 0].groupby(["month", "source"]).domains_peak.sum().unstack().fillna(0)
    tot = high.sum(axis=1)

    # The collapse month: the largest single-month fall in the high-iteration tail.
    drop = tot.diff()
    worst = drop.idxmin() if not drop.dropna().empty else None
    return {
        "definition": ("distinct NSEC3 owner names published with >= 100 iterations, "
                       "forward corpus. NSEC3 owner names are hashed, so this counts "
                       "names and not zones; a zone contributes one name per hashed "
                       "owner. The zone-level measure is NSEC3PARAM, which sits only "
                       "at the apex."),
        "high_iteration_names_by_month": {m: int(v) for m, v in tot.items()},
        "largest_single_month_fall": {
            "month": str(worst),
            "names_lost": int(-drop[worst]) if worst else None,
            "before": int(tot.shift()[worst]) if worst else None,
            "after": int(tot[worst]) if worst else None,
        },
        "by_source_around_collapse_names": {
            src: {m: int(high[src][m]) for m in high.index if "2021-06" <= m <= "2022-02"}
            for src in high.columns},
        "zero_iteration_names": {
            src: {m: int(zero[src][m]) for m in zero.index if m in ("2021-08", "2021-11", "2022-08", "2023-12")}
            for src in zero.columns},
        "validator_limits": limits,
        "rfc_9276_published": RFC_PUBLISHED["RFC 9276"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", type=Path, default=Path("out/server_run/timeline_monthly.parquet"))
    ap.add_argument("--support", type=Path, default=Path("data/software/software_support.json"))
    ap.add_argument("--out", type=Path, default=Path("out/analysis/software_crossref.json"))
    args = ap.parse_args()

    doc = json.loads(args.support.read_text(encoding="utf-8"))
    df = load_timeline(args.timeline)
    fwd = df[df.basis == "zonefile"].copy()   # jumps are a forward-corpus question
    entry = source_entry(fwd)

    rows = decompose(doc["support"], df)
    jumps = {obs: spikes(fwd, JUMP_DIM[obs], vals, entry)
             for obs, (_, vals, _) in OBSERVABLES.items()}

    payload = {
        "generated": date.today().isoformat(),
        "corpus": {"first_seen_over": sorted(df.basis.unique()),
                   "jumps_over": "zonefile (forward)",
                   "months": [df.month.min(), df.month.max()],
                   "forward_months": [fwd.month.min(), fwd.month.max()],
                   "sources": sorted(df.source.unique()),
                   "source_entry_month": entry},
        "onset_decomposition": rows,
        "rfc_overlap": overlap(df),
        "portfolio_jumps": jumps,
        "nsec3_iteration_collapse": iteration_collapse(fwd, doc["validator_limits"]),
        "caveat": ("Code lag is a floor: it is the earliest release of software we can read the "
                   "history of. Registry and registrar platforms are closed, and a zone's own "
                   "software is never observable from its published records."),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"{'observable':12} {'rfc':9} {'pub':8} {'signer ships':13} {'code':>6} "
          f"{'first zone':11} {'deploy':>7} {'onset':>6}  corpus")
    for r in rows:
        mark = "<=" if r.get("corpus_left_censored") else "  "
        print(f"{r['observable']:12} {r['rfc']:9} {r['rfc_published']:8} "
              f"{r.get('first_signer_released','-'):13} "
              f"{r.get('code_lag_years','-'):>6} {mark}{str(r.get('first_zone_seen','-')):9} "
              f"{r.get('deployment_lag_years','-'):>7} {r.get('onset_years','-'):>6}  "
              f"{r.get('first_seen_basis') or '-'}")
    print("\n<= marks a first sighting in the corpus's opening month: an upper bound.")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
