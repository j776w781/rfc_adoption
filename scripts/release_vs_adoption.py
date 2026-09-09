"""Do software releases explain when adoption moved?

Three dates could explain when a mechanism started spreading: the RFC that
standardised it, the release that first let a signer publish it, and the release
that made it the *default*. This measures which one the adoption curve actually
follows.

    RFC published  ->  code exists  ->  code is the default  ->  zones move

Method, and its limit. "Adoption rate" here is the month-on-month change in the
share of signed delegations carrying a value. The earlier jump analysis showed
this population is not independent adopters -- a handful of registry operators
move six figures of names in a month -- so an event study over it is measuring
whether *those operators* moved after a release, not whether a population
diffused. That is still the question asked, but it is a question about a dozen
actors, not a market.

Reads out/server_run/timeline_monthly.parquet and data/software/software_support.json.
Writes out/analysis/release_vs_adoption.json.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

#: observable -> (reverse dimension, forward dimension, codepoints, RFC, published)
OBSERVABLES = {
    "alg 8/10":   ("algorithm_ds", "algorithm_dnskey", ["8", "10"],  "RFC 5702", "2009-10"),
    "alg 12":     ("algorithm_ds", "algorithm_dnskey", ["12"],       "RFC 5933", "2010-07"),
    "alg 13/14":  ("algorithm_ds", "algorithm_dnskey", ["13", "14"], "RFC 6605", "2012-04"),
    "alg 15/16":  ("algorithm_ds", "algorithm_dnskey", ["15", "16"], "RFC 8080", "2017-02"),
    "digest 4":   ("digest_type_ds", "digest_type_ds", ["4"],        "RFC 6605", "2012-04"),
}
PUBLISHING = {"sign", "publish"}

#: Which observable each default change is about, so a default can be lined up
#: with the curve it should have moved.
DEFAULT_TARGET = {
    "default signing algorithm -> 8 (RSASHA256)": "alg 8/10",
    "default signing algorithm -> RSASHA256": "alg 8/10",
    "default signing algorithm -> ECDSAP256SHA256": "alg 13/14",
    "default ZSK algorithm -> ECDSA P-256": "alg 13/14",
    "default KSK algorithm -> ECDSA P-256": "alg 13/14",
    "built-in dnssec-policy 'default' signs with one ECDSAP256SHA256 CSK": "alg 13/14",
}


def months_between(a: str, b: str) -> float:
    return ((int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))) / 12.0


def series(df: pd.DataFrame, basis: str, dim: str, values: list[str]) -> pd.Series:
    """Share of signed delegations carrying the value, per month.

    A month in which the value does not appear is 0%, not missing. Dropping
    those instead leaves the series starting at first sighting, which deletes
    every month before the software shipped -- exactly the period an event study
    needs.
    """
    b = df[(df.basis == basis) & (df.dimension == dim)]
    den = b[b.value == "_total"].groupby("month").domains_peak.sum().sort_index()
    num = (b[b.value.isin(values)].groupby("month").domains_peak.sum()
           .reindex(den.index, fill_value=0))
    return (num / den * 100).sort_index()


def takeoff(s: pd.Series, threshold: float = 1.0) -> dict:
    """When the curve started moving, by two independent definitions."""
    over = s[s >= threshold]
    growth = s.diff()
    return {
        "first_month_over_1pct": str(over.index[0]) if len(over) else None,
        "steepest_month": str(growth.idxmax()) if growth.notna().any() else None,
        "steepest_gain_pp": round(float(growth.max()), 2) if growth.notna().any() else None,
        "months_observed": len(s),
    }


#: Above this share a percentage-point event study is not interpretable: a
#: bounded series must decelerate as it approaches its ceiling, so any event late
#: in the curve inherits a negative delta it did not cause.
LATE_CURVE_PCT = 20.0


def event_study(s: pd.Series, event: str, window: int = 12) -> dict | None:
    """Mean monthly percentage-point change before and after a release month.

    Also records the share at the event, because the measure is only meaningful
    on the early part of a curve -- see LATE_CURVE_PCT.
    """
    g = s.diff().dropna()
    before = g[(g.index < event)][-window:]
    after = g[(g.index >= event)][:window]
    if len(before) < 3 or len(after) < 3:
        return None
    at = s[s.index <= event]
    share = float(at.iloc[-1]) if len(at) else None
    return {"event": event, "window_months": window,
            "n_before": len(before), "n_after": len(after),
            "share_at_event_pct": round(share, 2) if share is not None else None,
            "late_curve": bool(share is not None and share > LATE_CURVE_PCT),
            "mean_pp_before": round(float(before.mean()), 3),
            "mean_pp_after": round(float(after.mean()), 3),
            "change_pp": round(float(after.mean() - before.mean()), 3)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", type=Path,
                    default=Path("out/server_run/timeline_monthly.parquet"))
    ap.add_argument("--support", type=Path,
                    default=Path("data/software/software_support.json"))
    ap.add_argument("--out", type=Path, default=Path("out/analysis/release_vs_adoption.json"))
    args = ap.parse_args()

    df = pd.read_parquet(args.timeline)
    sup = json.loads(args.support.read_text(encoding="utf-8"))

    alias = {"alg 15": "alg 15/16", "alg 16": "alg 15/16", "alg 13": "alg 13/14",
             "alg 14": "alg 13/14", "alg 8": "alg 8/10", "alg 10": "alg 8/10"}
    first_signer, defaults = {}, {}
    for r in sup["support"]:
        if r["capability"] in PUBLISHING and r.get("standard_codepoint", True):
            k = alias.get(r["observable"], r["observable"])
            if k not in first_signer or r["released"] < first_signer[k]["released"]:
                first_signer[k] = r
    all_defaults = []
    for r in sup["default_changes"]:
        k = DEFAULT_TARGET.get(r["what"])
        if not k:
            continue
        all_defaults.append((k, r))
        if k not in defaults or r["released"] < defaults[k]["released"]:
            defaults[k] = r

    rows, studies = [], []
    for obs, (rdim, fdim, vals, rfc, pub) in OBSERVABLES.items():
        for basis, dim in (("reverse", rdim), ("zonefile", fdim)):
            s = series(df, basis, dim, vals)
            if s.empty:
                continue
            t = takeoff(s)
            sig = first_signer.get(obs)
            dfl = defaults.get(obs)
            mark = t["first_month_over_1pct"]
            row = {"observable": obs, "rfc": rfc, "rfc_published": pub, "basis": basis,
                   "series_start": str(s.index.min()), "series_end": str(s.index.max()),
                   **t,
                   "first_signer": f'{sig["implementation"]} {sig["first_release"]}' if sig else None,
                   "first_signer_released": sig["released"][:7] if sig else None,
                   "default_change": f'{dfl["implementation"]} {dfl["first_release"]}' if dfl else None,
                   "default_released": dfl["released"][:7] if dfl else None,
                   "censored_start": mark == str(s.index.min())}
            for label, when in (("from_rfc", pub),
                                ("from_first_signer", row["first_signer_released"]),
                                ("from_default_change", row["default_released"])):
                row[f"{label}_to_1pct_years"] = (
                    round(months_between(when, mark), 2) if when and mark else None)
            rows.append(row)

            events = [("first signer release", sig)] if sig else []
            seen_rel = set()
            for k, rec in all_defaults:
                if k != obs or rec["released"] in seen_rel:
                    continue
                seen_rel.add(rec["released"])
                events.append(("default change" + (" (opt-in)" if rec.get("opt_in") else ""),
                               rec))
            for kind, rec in events:
                es = event_study(s, rec["released"][:7])
                if es:
                    es.update(observable=obs, basis=basis, kind=kind,
                              software=f'{rec["implementation"]} {rec["first_release"]}')
                    studies.append(es)

    payload = {
        "generated": date.today().isoformat(),
        "question": "Which date does the adoption curve follow: the RFC, the first "
                    "release that could publish it, or the release that made it default?",
        "caveat": ("Month-on-month share change over a population a dozen registry "
                   "operators dominate. An event study here measures whether those "
                   "operators moved, not whether a market diffused."),
        "takeoff": rows,
        "event_studies": studies,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"{'observable':11} {'basis':9} {'1% at':8} {'RFC->1%':>8} {'signer->1%':>11} "
          f"{'default->1%':>12}")
    for r in rows:
        if r["censored_start"] or not r["first_month_over_1pct"]:
            continue
        print(f"{r['observable']:11} {r['basis']:9} {r['first_month_over_1pct']:8} "
              f"{str(r['from_rfc_to_1pct_years']):>8} "
              f"{str(r['from_first_signer_to_1pct_years']):>11} "
              f"{str(r['from_default_change_to_1pct_years']):>12}")
    print(f"\n{'observable':11} {'basis':9} {'kind':24} {'software':18} "
          f"{'at%':>6} {'before':>8} {'after':>8} {'delta':>8}")
    for e in sorted(studies, key=lambda x: (x["kind"], x["observable"])):
        flag = "  <- late curve, not interpretable" if e["late_curve"] else ""
        print(f"{e['observable']:11} {e['basis']:9} {e['kind']:24} {e['software']:18} "
              f"{e['share_at_event_pct']:>6} {e['mean_pp_before']:>8} "
              f"{e['mean_pp_after']:>8} {e['change_pp']:>8}{flag}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
