"""Adoption rate around DNSSEC CVE patches vs around DNSSEC RFC publications.

Two sets of event months:

    CVE patches      -- DNSSEC-mechanism CVEs (scope "dnssec" in cve_crossref)
                        with a dated fix: the month of the first fixing release
                        (or fixing commit when no release is dated)
    RFC publications -- the 30 DNSSEC RFCs the project screens
                        (reporting/rfc_classification.json)

and one adoption-rate series per corpus:

    reverse  -- strict AFRINIC+ARIN panel: signed delegations (DS present) as
                a share of all delegations, month on month, in pp/month
    forward  -- the seven OpenINTEL TLDs: zones with a DNSKEY as a share of
                delegated zones (NS owners), month-on-month pp change per TLD,
                averaged over the TLDs present in both months weighted by
                zone count (so a TLD entering the corpus is not a jump)

For every event the statistic is the mean rate over the event month and the
three months after it. The same statistic at every month of the series is the
baseline. Distributions are compared by medians, with permutation p-values:
CVE vs RFC by shuffling labels; each vs baseline by drawing same-size random
month sets, stratified by year (the events cluster in time -- most CVE fixes
are 2022-2026 -- so an unstratified draw would compare eras, not events).

Every comparison is also run on the detrended rate: the rate minus its
25-month centred rolling median, which removes the slow drift of the series
and leaves what a month did relative to its neighbours.

A second pass does the same on the mechanism's own curve, where a mechanism
maps to an RFC: NSEC3 (RFC 5155, 9276; nsec3 CVEs), ECDSA/EdDSA (RFC 6605,
8080; algorithm CVEs), RSA/SHA-256 (RFC 5702).

Writes out/analysis/cve_vs_rfc_rates.json and out/analysis/dns_cve_vs_rfc_rates.csv.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PANEL = "_pooled-afrinic-arin"
AFTER = 3            # months after the event included in the window
N_PERM = 5000
RNG = np.random.default_rng(20260916)


def months_between(a: str, b: str) -> int:
    return (int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))


def shift(m: str, k: int) -> str:
    return (pd.Period(m, freq="M") + k).strftime("%Y-%m")


# ----------------------------------------------------------------- series --

def reverse_signed_share(pan: pd.DataFrame) -> pd.Series:
    p = pan[pan.source == PANEL]
    den = p[p.dimension == "all"].groupby("month").domains_peak.sum()
    num = p[(p.dimension == "algorithm_ds") & (p.value == "_total")].groupby("month").domains_peak.sum()
    s = (num.reindex(den.index, fill_value=0) / den * 100)
    return s[s.index >= "2011-05"].sort_index()


def forward_rate(srv: pd.DataFrame) -> pd.Series:
    """Zone-weighted mean of per-TLD pp changes over TLDs present in both months."""
    f = srv[srv.basis == "zonefile"]
    zones = f[(f.dimension == "rr_type") & (f.value == "NS")].groupby(["source", "month"]).domains_peak.sum()
    signed = f[(f.dimension == "algorithm_dnskey") & (f.value == "_total")].groupby(["source", "month"]).domains_peak.sum()
    share = (signed / zones * 100).dropna()
    rows = {}
    for src, s in share.groupby(level=0):
        s = s.droplevel(0).sort_index()
        d = s.diff()
        for m in s.index[1:]:
            if months_between(s.index[s.index.get_loc(m) - 1], m) == 1:
                rows.setdefault(m, []).append((d[m], zones[(src, m)]))
    out = {m: float(np.average([v for v, _ in vals], weights=[w for _, w in vals])) for m, vals in rows.items()}
    return pd.Series(out).sort_index()


def rate_of(share: pd.Series) -> pd.Series:
    s = share.sort_index()
    d = s.diff()
    keep = [m for i, m in enumerate(s.index) if i and months_between(s.index[i - 1], m) == 1]
    return d[keep]


def windowed(rate: pd.Series, m: str) -> float | None:
    vals = [rate[x] for x in (shift(m, k) for k in range(0, AFTER + 1)) if x in rate.index]
    return float(np.mean(vals)) if len(vals) >= 2 else None


# ----------------------------------------------------------------- events --

def cve_events(cves: dict, scope="dnssec"):
    out = []
    for c in cves["cves"]:
        if c["scope"] != scope or not c["fixes"]:
            continue
        dates = [v.get("released") or v.get("commit_date") for v in c["fixes"].values()]
        dates = [d for d in dates if d]
        if not dates:
            continue
        out.append({"event": c["cve"], "kind": "cve_patch", "month": min(dates)[:7],
                    "rfc": c["rfc"], "mechanism": c["mechanism"], "products": c["products"]})
    return out


def rfc_events(rc: dict):
    rows = rc[[k for k in rc if isinstance(rc[k], list)][0]]
    return [{"event": r["rfc_id"], "kind": "rfc_published", "month": r["published"][:7],
             "title": r["title"], "verdict": r["verdict"]} for r in rows]


# ------------------------------------------------------------ comparison --

def perm_labels(a, b, n=N_PERM):
    a, b = np.asarray(a), np.asarray(b)
    obs = abs(np.median(a) - np.median(b))
    pool = np.concatenate([a, b]); k = len(a); hits = 0
    for _ in range(n):
        RNG.shuffle(pool)
        if abs(np.median(pool[:k]) - np.median(pool[k:])) >= obs:
            hits += 1
    return (hits + 1) / (n + 1)


def perm_baseline(a, base, n=N_PERM, a_months=None, base_months=None):
    """Same-size random month sets; stratified by year when months are given."""
    a, base = np.asarray(a), np.asarray(base)
    obs = abs(np.median(a) - np.median(base)); k = len(a); hits = 0
    if a_months is not None:
        by_year = {}
        for m, v in zip(base_months, base):
            by_year.setdefault(m[:4], []).append(v)
        need = {}
        for m in a_months:
            need[m[:4]] = need.get(m[:4], 0) + 1
        for _ in range(n):
            s = np.concatenate([RNG.choice(by_year[y], size=min(c, len(by_year[y])), replace=False)
                                for y, c in need.items() if y in by_year])
            if abs(np.median(s) - np.median(base)) >= obs:
                hits += 1
        return (hits + 1) / (n + 1)
    for _ in range(n):
        s = RNG.choice(base, size=k, replace=False)
        if abs(np.median(s) - np.median(base)) >= obs:
            hits += 1
    return (hits + 1) / (n + 1)


def perm_ranksum(a, b, n=N_PERM):
    """Permutation test on the difference in mean rank (Mann-Whitney in
    permutation form). Unlike the median it uses every observation, so it does
    not hinge on which value happens to sit in the middle -- with 16 RFC months
    the median falls in a 1.2-unit gap between the 8th and 9th values."""
    a, b = np.asarray(a), np.asarray(b)
    pool = np.concatenate([a, b]); k = len(a)
    ranks = pd.Series(pool).rank().values
    obs = abs(ranks[:k].mean() - ranks[k:].mean())
    hits = 0
    for _ in range(n):
        q = RNG.permutation(pool)
        rk = pd.Series(q).rank().values
        if abs(rk[:k].mean() - rk[k:].mean()) >= obs:
            hits += 1
    return (hits + 1) / (n + 1)


def detrend(rate: pd.Series) -> pd.Series:
    return rate - rate.rolling(25, center=True, min_periods=7).median()


def describe(vals):
    v = np.asarray(vals, dtype=float)
    return {"n": int(len(v)), "median": round(float(np.median(v)), 4), "mean": round(float(v.mean()), 4),
            "q25": round(float(np.percentile(v, 25)), 4), "q75": round(float(np.percentile(v, 75)), 4),
            "min": round(float(v.min()), 4), "max": round(float(v.max()), 4)} if len(v) else {"n": 0}


def _block(rate, events_cve, events_rfc, label, key):
    base = {m: windowed(rate, m) for m in rate.index}
    base = {m: v for m, v in base.items() if v is not None}
    rows = []
    for e in events_cve + events_rfc:
        if e["month"] in base:
            rows.append({**e, "series": label, "measure": key,
                         "rate_at_month_pp": round(float(rate[e["month"]]), 4),
                         "rate_window_pp_per_month": round(base[e["month"]], 4)})
    # Several CVEs are fixed in the same release month; a month is one draw
    # from the series, so the distributions are over unique event months.
    def uniq(kind):
        seen = {}
        for r in rows:
            if r["kind"] == kind:
                seen[r["month"]] = r["rate_window_pp_per_month"]
        return list(seen.values()), list(seen.keys())
    cv, cm = uniq("cve_patch")
    rf, rm = uniq("rfc_published")
    bl, bm = list(base.values()), list(base.keys())
    other = [v for m, v in base.items() if m not in set(cm) | set(rm)]
    out = {"cve_patches": describe(cv), "rfc_publications": describe(rf), "all_months": describe(bl),
           "other_months": describe(other),
           "cve_events": sum(1 for r in rows if r["kind"] == "cve_patch"),
           "rfc_events": sum(1 for r in rows if r["kind"] == "rfc_published"),
           "p_rank_cve_vs_rfc": round(perm_ranksum(cv, rf), 4) if len(cv) > 1 and len(rf) > 1 else None,
           "p_rank_cve_vs_other": round(perm_ranksum(cv, other), 4) if len(cv) > 1 and other else None,
           "p_rank_rfc_vs_other": round(perm_ranksum(rf, other), 4) if len(rf) > 1 and other else None,
           "p_cve_vs_rfc": round(perm_labels(cv, rf), 4) if len(cv) > 1 and len(rf) > 1 else None,
           "p_cve_vs_all": round(perm_baseline(cv, bl), 4) if len(cv) > 1 else None,
           "p_cve_vs_all_year_matched": round(perm_baseline(cv, bl, a_months=cm, base_months=bm), 4) if len(cv) > 1 else None,
           "p_rfc_vs_all": round(perm_baseline(rf, bl), 4) if len(rf) > 1 else None,
           "p_rfc_vs_all_year_matched": round(perm_baseline(rf, bl, a_months=rm, base_months=bm), 4) if len(rf) > 1 else None,
           "baseline_values": [round(v, 4) for v in bl], "baseline_months": bm}
    return out, rows


def compare(rate: pd.Series, events_cve, events_rfc, label):
    raw, rows = _block(rate, events_cve, events_rfc, label, "raw")
    det, rows2 = _block(detrend(rate).dropna(), events_cve, events_rfc, label, "detrended")
    out = {"series": label, "span": [rate.index.min(), rate.index.max()], "window_months": AFTER + 1,
           "raw": raw, "detrended": det}
    return out, rows + rows2


# ------------------------------------------------------- mechanism curves --

MECH = {
    "NSEC3": dict(rfcs=["RFC 5155", "RFC 9276"], cve_rfcs=["RFC 5155"], case="RFC 5155"),
    "ECDSA/EdDSA": dict(rfcs=["RFC 6605", "RFC 8080"], cve_rfcs=["RFC 6605/8080"], case="RFC 6605"),
    "RSA/SHA-256": dict(rfcs=["RFC 5702"], cve_rfcs=[], case="RFC 5702"),
}


def mechanism_series(cases, case):
    c = cases[case]
    fwd = {}
    for src, s in c["series"]["forward"].items():
        sh = pd.Series(s["share_pct"], index=s["months"], dtype=float).dropna()
        cnt = pd.Series(s["count"], index=s["months"], dtype=float)
        fwd[src] = (sh, cnt)
    rows = {}
    for src, (sh, cnt) in fwd.items():
        d = sh.diff()
        for i, m in enumerate(sh.index[1:], 1):
            if months_between(sh.index[i - 1], m) == 1:
                rows.setdefault(m, []).append((d[m], max(cnt[m], 1)))
    f_rate = pd.Series({m: float(np.average([v for v, _ in vs], weights=[w for _, w in vs])) for m, vs in rows.items()}).sort_index()
    rp = c["series"].get("reverse_panel")
    r_rate = rate_of(pd.Series(rp["share_pct"], index=rp["months"], dtype=float).dropna()) if rp else pd.Series(dtype=float)
    return f_rate, r_rate


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default="out/analysis/cve_vs_rfc_rates.json")
    a = ap.parse_args()
    srv = pd.read_parquet("out/server_run/timeline_monthly.parquet")
    pan = pd.read_parquet("out/panel_run/timeline_monthly.parquet")
    cves = json.loads(Path("out/analysis/cve_crossref.json").read_text("utf-8"))
    rc = json.loads(Path("reporting/rfc_classification.json").read_text("utf-8"))
    cases = json.loads(Path("out/analysis/program_rfc_cases.json").read_text("utf-8"))["cases"]

    ev_cve, ev_rfc = cve_events(cves), rfc_events(rc)
    ev_dns = cve_events(cves, scope="dns")
    doc = {"generated": pd.Timestamp.today().strftime("%Y-%m-%d"), "method": __doc__.strip(),
           "events": {"cve_patches": ev_cve, "rfc_publications": ev_rfc, "dns_cve_patches_control": len(ev_dns)},
           "overall": {}, "control_dns_cves": {}, "mechanism": {}}
    rows = []
    rev = rate_of(reverse_signed_share(pan)); fwd = forward_rate(srv)
    for label, rate in (("reverse signed share (strict panel)", rev), ("forward signed share (7 TLDs, zone-weighted)", fwd)):
        res, r = compare(rate, ev_cve, ev_rfc, label); doc["overall"][label] = res; rows += r
        resc, _ = compare(rate, ev_dns, ev_rfc, label)
        doc["control_dns_cves"][label] = {k: {"dns_cve_patches": resc[k]["cve_patches"], "p_dnscve_vs_all": resc[k]["p_cve_vs_all"],
                                             "p_dnscve_vs_all_year_matched": resc[k]["p_cve_vs_all_year_matched"]} for k in ("raw", "detrended")}
    for mech, spec in MECH.items():
        f_rate, r_rate = mechanism_series(cases, spec["case"])
        ec = [e for e in ev_cve if e["rfc"] in spec["cve_rfcs"]]
        er = [e for e in ev_rfc if e["event"] in spec["rfcs"]]
        doc["mechanism"][mech] = {}
        for label, rate in (("forward", f_rate), ("reverse panel", r_rate)):
            if rate.empty:
                continue
            res, r = compare(rate, ec, er, f"{mech} {label}")
            for k in ("raw", "detrended"):
                res[k].pop("baseline_values"); res[k].pop("baseline_months")
            doc["mechanism"][mech][label] = res; rows += r
    Path(a.out).write_text(json.dumps(doc, indent=1, default=str), "utf-8")
    pd.DataFrame(rows).to_csv("out/analysis/dns_cve_vs_rfc_rates.csv", index=False)
    for label, res in doc["overall"].items():
        for k in ("raw", "detrended"):
            b = res[k]
            print(label, k, "| cve", b["cve_patches"], "| rfc", b["rfc_publications"], "| all", b["all_months"],
                  "| p cve~rfc", b["p_cve_vs_rfc"], "cve~all", b["p_cve_vs_all"], "(yr)", b["p_cve_vs_all_year_matched"],
                  "rfc~all", b["p_rfc_vs_all"], "(yr)", b["p_rfc_vs_all_year_matched"])
    for label, d in doc["control_dns_cves"].items():
        print("control", label, d)
    for mech, d in doc["mechanism"].items():
        for label, res in d.items():
            b = res["detrended"]
            print(mech, label, "detrended | cve", b["cve_patches"], "| rfc", b["rfc_publications"], "| all median", b["all_months"].get("median"),
                  "| p", b["p_cve_vs_rfc"], b["p_cve_vs_all_year_matched"], b["p_rfc_vs_all_year_matched"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
