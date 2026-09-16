"""Case studies: for a few RFCs, does a program's release explain a spike?

For each chosen RFC this lines up, per program (BIND 9, Knot, PowerDNS,
OpenDNSSEC, Unbound, Knot Resolver):

    RFC published -> the program's first release that implements it
                  -> the release that made it the default (or capped it)
                  -> the program's CVEs on that mechanism, before and after

and then asks the OpenINTEL zone files (per TLD) and the reverse-DNS corpus
(per RIR, and the strict AFRINIC+ARIN panel for shares) the only question that
matters: when the adoption curve jumped, what had just happened in software?

Three things are measured for every spike:

  1. the nearest preceding *relevant* release -- one that implements, defaults
     or caps the mechanism -- and the lag to it, per program;
  2. the nearest preceding CVE on the mechanism, and the lag;
  3. whether the spike was new signings or existing zones rolling over. An
     automatic update changes what a *newly signed* zone gets; it never
     re-signs an existing zone. So a spike made of rollovers cannot be an
     update effect, whatever the lag says.

The lag alone proves nothing: 97% of months contain some DNS release. So the
lag to the nearest relevant release is compared with the same lag measured
at every month of the series -- the chance rate. A spike is "release-timed"
only if its lag is short by that standard.

The auto-update proxy. The reverse ledger records every sign event with the
algorithm chosen. If a default change propagates through updates, the share
of *new* signings choosing the new algorithm should step up after the
release. That is measured directly, per default change, over the twelve
months either side.

Reads out/server_run/timeline_monthly.parquet, out/panel_run/timeline_monthly.parquet,
out/analysis/delegation_changes.parquet, data/software/*.json,
out/analysis/cve_crossref.json. Writes out/analysis/program_rfc_cases.json and
out/analysis/dns_program_rfc_spikes.csv, dns_program_rfc_new_signings.csv.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

PANEL = "_pooled-afrinic-arin"
NAME = {"unbound": "Unbound", "nsd": "NSD", "bind9": "BIND 9", "knot": "Knot DNS",
        "kresd": "Knot Resolver", "opendnssec": "OpenDNSSEC",
        "pdns-auth": "PowerDNS Auth", "pdns-rec": "PowerDNS Rec"}
SIGNERS = {"bind9", "knot", "pdns-auth", "opendnssec"}
VALIDATORS = {"unbound", "kresd", "pdns-rec", "bind9"}
FORWARD_FLOOR, REVERSE_FLOOR = 300, 30   # zones: below this a jump is not a spike
WINDOW = 3                                # months: "just after a release"
MIN_DEN = 30                              # signed delegations needed to show a share

#: Each case: which codepoints, which support-row observables, which
#: default-change strings, which CVE labels/regex, and how a "spike" reads.
CASES = {
    "RFC 5702": dict(title="RSA/SHA-256 (algorithms 8, 10)", published="2009-10",
                     forward=("algorithm_dnskey", ["8", "10"]),
                     reverse=("algorithm_ds", ["8", "10"]), ledger_algs={"8", "10"},
                     sw_obs=["alg 8/10"], default_pat=r"RSASHA256",
                     cve_labels=[], cve_filter=None, direction=+1),
    "RFC 6605": dict(title="ECDSA P-256 / P-384 (algorithms 13, 14)", published="2012-04",
                     forward=("algorithm_dnskey", ["13", "14"]),
                     reverse=("algorithm_ds", ["13", "14"]), ledger_algs={"13", "14"},
                     sw_obs=["alg 13/14", "digest 4"], default_pat=r"ECDSA",
                     cve_labels=["RFC 6605/8080"], cve_filter=r"ECDSA|P-256|P-384|prime256",
                     direction=+1),
    "RFC 8080": dict(title="EdDSA (algorithms 15, 16)", published="2017-02",
                     forward=("algorithm_dnskey", ["15", "16"]),
                     reverse=("algorithm_ds", ["15", "16"]), ledger_algs={"15", "16"},
                     sw_obs=["alg 15/16", "alg 15", "alg 16"], default_pat=r"EdDSA|Ed25519",
                     cve_labels=["RFC 6605/8080"], cve_filter=r"Ed25519|Ed448|EdDSA",
                     direction=+1),
    "RFC 5155": dict(title="NSEC3 authenticated denial", published="2008-03",
                     forward=("rr_type", ["NSEC3PARAM"]),
                     reverse=("algorithm_ds", ["7"]), ledger_algs={"7"},
                     reverse_note="algorithm 7 (RSASHA1-NSEC3-SHA1) is the only NSEC3 "
                                  "signal a DS record carries; NSEC3 with 8/13 is invisible "
                                  "in the reverse corpus",
                     sw_obs=["nsec3"], default_pat=r"NSEC3", limits=True,
                     cve_labels=["RFC 5155"], cve_filter=None, cve_max="2021-04",
                     direction=+1),
    # The thing that moves for RFC 9276 is the *disappearance* of high
    # iteration counts, so the spike direction is negative.
    "RFC 9276": dict(title="NSEC3 parameters: iterations to 0", published="2022-08",
                     forward=("nsec3_iterations", ">=100"),
                     reverse=("nsec3_iterations", ">=100"), ledger_algs=set(),
                     sw_obs=[], default_pat=r"NSEC3 iterations", limits=True,
                     cve_labels=["RFC 5155"], cve_filter=None, cve_min="2021-05",
                     direction=-1,
                     unit="names with NSEC3 iterations >= 100"),
}
RFC_PUB = {"RFC 5155": "2008-03", "RFC 5702": "2009-10", "RFC 5933": "2010-07",
           "RFC 6605": "2012-04", "RFC 7344": "2014-09", "RFC 8080": "2017-02",
           "RFC 9276": "2022-08", "RFC 5011": "2007-09"}


def months_between(a: str, b: str) -> int:
    return (int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))


def month_of(d: str) -> str:
    return d[:7]


# ----------------------------------------------------------------- inputs --

def load():
    srv = pd.read_parquet("out/server_run/timeline_monthly.parquet")
    pan = pd.read_parquet("out/panel_run/timeline_monthly.parquet")
    ledger = pd.read_parquet("out/analysis/delegation_changes.parquet")
    sup = json.loads(Path("data/software/software_support.json").read_text("utf-8"))
    rel = json.loads(Path("data/software/release_dates.json").read_text("utf-8"))
    cves = json.loads(Path("out/analysis/cve_crossref.json").read_text("utf-8"))
    return srv, pan, ledger, sup, rel, cves


def program_events(rfc, spec, sup, cves):
    """Every dated software fact about this RFC, keyed by program."""
    ev = {}

    def add(key, kind, **row):
        ev.setdefault(key, {"program": NAME[key], "key": key,
                            "role": "signer" if key in SIGNERS else "validator",
                            "events": []})
        ev[key]["events"].append({"kind": kind, **row})

    for r in sup["support"]:
        if r["observable"] in spec["sw_obs"] and r.get("standard_codepoint", True):
            add(r["implementation"], "support", version=r["first_release"],
                date=r["released"], capability=r["capability"],
                lag_months_after_rfc=months_between(spec["published"], r["released"][:7]),
                url=r.get("evidence_url", ""))
    pat = re.compile(spec["default_pat"], re.I)
    for r in sup["default_changes"]:
        if pat.search(r["what"]):
            add(r["implementation"], "default", version=r["first_release"],
                date=r["released"], what=r["what"], opt_in=bool(r.get("opt_in")),
                lag_months_after_rfc=months_between(spec["published"], r["released"][:7]))
    if spec.get("limits"):
        for r in sup["validator_limits"]:
            if "nsec3" in r["what"].lower():
                add(r["implementation"], "limit", version=r["first_release"],
                    date=r["released"], what=r["what"],
                    lag_months_after_rfc=months_between(spec["published"], r["released"][:7]))
    flt = re.compile(spec["cve_filter"], re.I) if spec.get("cve_filter") else None
    for c in cves["cves"]:
        if c["scope"] != "dnssec" or c["rfc"] not in spec["cve_labels"] or not c["published"]:
            continue
        if flt and not flt.search(c["description"] or ""):
            continue
        if spec.get("cve_min") and c["published"][:7] < spec["cve_min"]:
            continue
        if spec.get("cve_max") and c["published"][:7] > spec["cve_max"]:
            continue
        # Attribution only by NVD CPE (nvd-product); keyword hits are not a product.
        prods = [p for p in c["products"] if p in NAME] if "nvd-product" in c["sources"] else []
        cites = bool(re.search(r"RFC\s?" + rfc.split()[1], c["description"] or ""))
        for p in prods or ["_unattributed"]:
            if p == "_unattributed":
                ev.setdefault(p, {"program": "other / unattributed", "key": p,
                                  "role": "other", "events": []})
                ev[p]["events"].append({"kind": "cve", "cve": c["cve"], "date": c["published"],
                                        "cvss": c["cvss"], "cites_rfc": cites,
                                        "lag_months_after_rfc": months_between(
                                            spec["published"], c["published"][:7]),
                                        "description": (c["description"] or "")[:160]})
            else:
                add(p, "cve", cve=c["cve"], date=c["published"], cvss=c["cvss"],
                    cites_rfc=cites,
                    lag_months_after_rfc=months_between(spec["published"], c["published"][:7]),
                    description=(c["description"] or "")[:160])
    for p in ev.values():
        p["events"].sort(key=lambda e: e["date"])
    order = ["bind9", "knot", "pdns-auth", "opendnssec", "unbound", "kresd", "pdns-rec",
             "nsd", "_unattributed"]
    return [ev[k] for k in order if k in ev]


# ----------------------------------------------------------------- series --

def count_series(df, basis, dim, values, source):
    d = df[(df.basis == basis) & (df.source == source) & (df.dimension == dim)]
    if values == ">=100":
        d = d[d.value != "_total"]
        d = d[pd.to_numeric(d.value, errors="coerce").fillna(-1) >= 100]
    else:
        d = d[d.value.isin(values)]
    return d.groupby("month").domains_peak.sum().sort_index()


def denominator(df, basis, dim, source):
    d = df[(df.basis == basis) & (df.source == source)]
    if dim == "nsec3_iterations":
        # names with any NSEC3 iteration value: the population that could collapse
        d = d[(d.dimension == dim) & (d.value != "_total")]
    elif basis == "zonefile":
        d = d[(d.dimension == "algorithm_dnskey") & (d.value == "_total")]
    else:
        d = d[(d.dimension == "algorithm_ds") & (d.value == "_total")]
    return d.groupby("month").domains_peak.sum().sort_index()


def spikes(y: pd.Series, floor: int, direction: int):
    """Episodes where the month-on-month change is large by the series' own
    recent standard. Consecutive spike months merge into one episode."""
    y = y.sort_index()
    d = (y.diff() * direction).fillna(0)
    scale = d.abs().rolling(12, min_periods=3).median().shift(1)
    prev = y.shift(1).fillna(0)
    hit = (d >= floor) & (d >= 0.10 * prev) & (d >= 4 * scale.fillna(0))
    out, cur = [], None
    for m in y.index:
        if hit[m]:
            if cur and months_between(cur["end"], m) == 1:
                cur["end"] = m
                cur["delta"] += int(d[m])
            else:
                cur = {"start": m, "end": m, "delta": int(d[m]),
                       "level_before": int(prev[m])}
                out.append(cur)
        elif cur and months_between(cur["end"], m) > 1:
            cur = None
    for e in out:
        e["level_after"] = int(y[e["end"]])
    return out


def nearest_before(items, month, date_key="date"):
    """(item, lag in months) for the latest item dated on or before `month`."""
    best = None
    for it in items:
        if it[date_key][:7] <= month:
            lag = months_between(it[date_key][:7], month)
            if best is None or lag < best[1]:
                best = (it, lag)
    return best


def chance_rate(months, dates, window):
    """Fraction of series months lying within `window` months after any date."""
    if not dates or not months:
        return None
    inside = 0
    for m in months:
        lag = min((months_between(d[:7], m) for d in dates if d[:7] <= m), default=None)
        if lag is not None and lag <= window:
            inside += 1
    return round(inside / len(months), 3)


def all_release_dates(rel):
    out = []
    for proj, r in rel.items():
        for v, d in r["releases"].items():
            out.append({"program": proj, "version": v, "date": d})
    return sorted(out, key=lambda x: x["date"])


# ------------------------------------------------------------- the ledger --

def rollover_split(delta_alg, delta_signed):
    """How much of a jump in algorithm-X zones could be newly signed zones.
    New signings are bounded by the growth in signed zones that month; the rest
    are existing zones that rolled. If signed zones shrank, none are new.

    `share_of_new_signings_pct` is the FLOW share: of the zones that became
    signed over the episode, how many took this algorithm. It is not the stock
    share of the algorithm among all signed zones, which is a different number
    and must not be quoted as if it were this one."""
    new_max = max(0, min(delta_alg, delta_signed))
    return {"new_signings_at_most": int(new_max),
            "rollovers_at_least": int(max(0, delta_alg - new_max)),
            "signed_zones_delta": int(delta_signed),
            "share_of_new_signings_pct": (round(delta_alg / delta_signed * 100, 1)
                                          if delta_signed > 0 else None)}


def build_case(rfc, spec, srv, pan, ledger, sup, rel, cves):
    progs = program_events(rfc, spec, sup, cves)
    relevant = []          # releases that implement/default/cap the mechanism
    cve_list = []
    for p in progs:
        for e in p["events"]:
            row = {**e, "program": p["program"], "key": p["key"]}
            (cve_list if e["kind"] == "cve" else relevant).append(row)
    relevant.sort(key=lambda e: e["date"])
    signer_rel = [e for e in relevant if e["key"] in SIGNERS and e["kind"] in ("support", "default")]
    default_rel = [e for e in relevant if e["kind"] == "default"]
    limit_rel = [e for e in relevant if e["kind"] == "limit"]
    every = all_release_dates(rel)

    case = {"rfc": rfc, "title": spec["title"], "published": spec["published"],
            "unit": spec.get("unit", "zones"), "programs": progs,
            "series": {"forward": {}, "reverse": {}}, "spikes": [], "chance": {}}
    n = 0
    for basis, key, floor in (("zonefile", "forward", FORWARD_FLOOR),
                              ("reverse", "reverse", REVERSE_FLOOR)):
        dim, values = spec[key]
        df = srv
        sources = sorted(df[(df.basis == basis)].source.unique())
        for src in sources:
            y = count_series(df, basis, dim, values, src)
            den = denominator(df, basis, dim, src)
            if y.empty or y.max() < floor:
                continue
            first = y[y > 0].index.min() if (y > 0).any() else None
            case.setdefault("first_seen", {}).setdefault(key, {})[src] = first
            y = y.reindex(den.index, fill_value=0)
            # A share over a handful of delegations swings 0 -> 100 on one
            # operator; below MIN_DEN the share is not shown, the count still is.
            share = (y / den.where(den >= MIN_DEN) * 100).round(3)
            case["series"][key][src] = {"months": list(y.index), "count": [int(v) for v in y],
                                        "share_pct": [None if pd.isna(v) else float(v) for v in share]}
            for ep in spikes(y, floor, spec["direction"]):
                n += 1
                m = ep["start"]
                j = {"n": n, "rfc": rfc, "basis": key, "source": src, **ep,
                     "share_before_pct": None if pd.isna(share.get(m)) else float(
                         share.shift(1).get(m, np.nan)) if not pd.isna(share.shift(1).get(m, np.nan)) else None,
                     "share_after_pct": None if pd.isna(share.get(ep["end"])) else float(share[ep["end"]]),
                     "months_after_rfc": months_between(spec["published"], m)}
                if key == "forward" and spec["direction"] > 0:
                    j["split"] = rollover_split(ep["delta"], int(den.get(ep["end"], 0) - den.get(
                        (pd.Period(m) - 1).strftime("%Y-%m"), 0)))
                for label, items in (("signer_release", signer_rel), ("default_change", default_rel),
                                     ("validator_limit", limit_rel), ("cve", cve_list)):
                    hit = nearest_before(items, m)
                    if hit:
                        it, lag = hit
                        j["nearest_" + label] = {
                            "what": (f'{it["program"]} {it["version"]}' if "version" in it
                                     else f'{it["cve"]} ({it["program"]})'),
                            "date": it["date"], "lag_months": lag,
                            **({"detail": it["what"]} if "what" in it else {})}
                    else:
                        j["nearest_" + label] = None
                anyr = nearest_before(every, m)
                j["nearest_any_release"] = ({"what": f'{NAME.get(anyr[0]["program"], anyr[0]["program"])} '
                                                     f'{anyr[0]["version"]}', "date": anyr[0]["date"],
                                             "lag_months": anyr[1]} if anyr else None)
                case["spikes"].append(j)
        months = sorted({m for s in case["series"][key].values() for m in s["months"]})
        case["chance"][key] = {
            "months": len(months),
            f"within_{WINDOW}m_after_signer_release": chance_rate(months, [e["date"] for e in signer_rel], WINDOW),
            f"within_{WINDOW}m_after_default_change": chance_rate(months, [e["date"] for e in default_rel], WINDOW),
            f"within_{WINDOW}m_after_validator_limit": chance_rate(months, [e["date"] for e in limit_rel], WINDOW),
            f"within_{WINDOW}m_after_cve": chance_rate(months, [e["date"] for e in cve_list], WINDOW),
            f"within_{WINDOW}m_after_any_release": chance_rate(months, [e["date"] for e in every], WINDOW),
        }

    # Panel share (strict AFRINIC+ARIN) for the reverse curve on the figure.
    dim, values = spec["reverse"]
    y = count_series(pan, "reverse", dim, values, PANEL)
    den = denominator(pan, "reverse", dim, PANEL)
    if not y.empty:
        y = y.reindex(den.index, fill_value=0)
        sh = (y / den.replace(0, np.nan) * 100).round(3)
        case["series"]["reverse_panel"] = {"months": list(y.index), "count": [int(v) for v in y],
                                           "share_pct": [None if pd.isna(v) else float(v) for v in sh]}

    # Auto-update proxy: new signings by algorithm in the reverse ledger.
    if spec["ledger_algs"]:
        case["new_signings"] = new_signings(ledger, spec["ledger_algs"], default_rel, signer_rel)
    case["summary"] = summarise(case, spec)
    return case


def vcmp(a: str) -> tuple:
    """Debian-style version to a comparable tuple; '~' marks a pre-release,
    which sorts below the release it precedes (4.0.0~alpha2 < 4.0.0)."""
    pre = "~" in a
    a = a.split(":")[-1].split("~")[0].split("+")[0].split("-")[0]
    out = []
    for p in a.split("."):
        num = "".join(ch for ch in p if ch.isdigit())
        out.append(int(num) if num else 0)
    return tuple(out + [0] * (4 - len(out)) + [-1 if pre else 0])


def os_ships(default_rel):
    """The first OS release, per distribution, carrying each default-changing
    version -- and, per OS release, which defaults it delivered at once."""
    distro = json.loads(Path("data/software/distro_ships.json").read_text("utf-8"))
    key = {"pdns-auth": "pdns"}
    out = {}
    for e in default_rel:
        pk = key.get(e["key"], e["key"])
        hit = {}
        for d in sorted(distro["ships"], key=lambda x: x["released"]):
            v = d["versions"].get(pk)
            if v and vcmp(v) >= vcmp(e["version"]) and d["distribution"] not in hit:
                hit[d["distribution"]] = d
        for d in hit.values():
            out.setdefault(d["name"], {"os": d["name"], "date": d["released"], "carries": []})
            tag = f'{e["program"]} {e["version"]}'
            if tag not in out[d["name"]]["carries"]:
                out[d["name"]]["carries"].append(tag)
    return sorted(out.values(), key=lambda x: x["date"])


def new_signings(ledger, algs, default_rel, signer_rel):
    s = ledger[ledger.kind == "sign"].copy()
    s["hit"] = s.to_alg.astype(str).isin(algs)
    s["q"] = pd.PeriodIndex(s.month, freq="M").asfreq("Q").astype(str)
    q = s.groupby("q").agg(n=("hit", "size"), hit=("hit", "sum")).reset_index()
    q["share_pct"] = (q.hit / q.n * 100).round(1)
    r = ledger[ledger.kind == "rollover"].copy()
    r["hit"] = r.to_alg.astype(str).isin(algs)
    rq = r.groupby(r.month.str[:4]).agg(n=("hit", "size"), hit=("hit", "sum")).reset_index()
    hitq = q[q.hit > 0]
    out = {"quarterly": q.to_dict("records"),
           "first_quarter_with_any": None if hitq.empty else hitq.iloc[0]["q"],
           "rollovers_to_by_year": rq.rename(columns={"month": "year"}).to_dict("records"),
           "around_releases": [], "around_os_ships": []}
    for d in os_ships([e for e in default_rel if not e.get("opt_in")]):
        m = d["date"][:7]
        lo = (pd.Period(m) - 12).strftime("%Y-%m"); hi = (pd.Period(m) + 12).strftime("%Y-%m")
        before = s[(s.month >= lo) & (s.month < m)]
        after = s[(s.month >= m) & (s.month <= hi)]
        out["around_os_ships"].append({
            **d, "new_signings_12m_before": int(len(before)),
            "share_before_pct": round(before.hit.mean() * 100, 1) if len(before) else None,
            "blocks_choosing_before": int(before[before.hit].block.nunique()),
            "new_signings_12m_after": int(len(after)),
            "share_after_pct": round(after.hit.mean() * 100, 1) if len(after) else None,
            "blocks_choosing_after": int(after[after.hit].block.nunique())})
    for e in default_rel + [x for x in signer_rel if x["kind"] == "support"]:
        m = e["date"][:7]
        lo = (pd.Period(m) - 12).strftime("%Y-%m"); hi = (pd.Period(m) + 12).strftime("%Y-%m")
        before = s[(s.month >= lo) & (s.month < m)]
        after = s[(s.month >= m) & (s.month <= hi)]
        out["around_releases"].append({
            "program": e["program"], "version": e["version"], "kind": e["kind"], "date": e["date"],
            "what": e.get("what", e.get("capability")),
            "new_signings_12m_before": int(len(before)),
            "share_before_pct": round(before.hit.mean() * 100, 1) if len(before) else None,
            "new_signings_12m_after": int(len(after)),
            "share_after_pct": round(after.hit.mean() * 100, 1) if len(after) else None})
    return out


def summarise(case, spec):
    sp = case["spikes"]
    fwd = [j for j in sp if j["basis"] == "forward"]
    rev = [j for j in sp if j["basis"] == "reverse"]

    def timed(js, key):
        return sum(1 for j in js if j.get(key) and j[key]["lag_months"] <= WINDOW)

    s = {"n_spikes": len(sp), "n_forward": len(fwd), "n_reverse": len(rev),
         "forward_zones_in_spikes": int(sum(j["delta"] for j in fwd)),
         "reverse_zones_in_spikes": int(sum(j["delta"] for j in rev)),
         f"spikes_within_{WINDOW}m_of_signer_release": timed(sp, "nearest_signer_release"),
         f"spikes_within_{WINDOW}m_of_default_change": timed(sp, "nearest_default_change"),
         f"spikes_within_{WINDOW}m_of_validator_limit": timed(sp, "nearest_validator_limit"),
         f"spikes_within_{WINDOW}m_of_cve": timed(sp, "nearest_cve"),
         f"spikes_within_{WINDOW}m_of_any_release": timed(sp, "nearest_any_release")}
    if fwd and spec["direction"] > 0:
        s["forward_rollovers_at_least"] = int(sum(j["split"]["rollovers_at_least"] for j in fwd if "split" in j))
        s["forward_new_signings_at_most"] = int(sum(j["split"]["new_signings_at_most"] for j in fwd if "split" in j))
    lags = [j["nearest_signer_release"]["lag_months"] for j in sp if j.get("nearest_signer_release")]
    s["median_lag_to_signer_release_months"] = float(np.median(lags)) if lags else None
    lags = [j["nearest_cve"]["lag_months"] for j in sp if j.get("nearest_cve")]
    s["median_lag_to_cve_months"] = float(np.median(lags)) if lags else None
    return s


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default="out/analysis/program_rfc_cases.json")
    a = ap.parse_args()
    srv, pan, ledger, sup, rel, cves = load()
    cases = {rfc: build_case(rfc, spec, srv, pan, ledger, sup, rel, cves)
             for rfc, spec in CASES.items()}
    doc = {"generated": pd.Timestamp.today().strftime("%Y-%m-%d"),
           "method": __doc__.strip(), "window_months": WINDOW,
           "floors": {"forward_zones": FORWARD_FLOOR, "reverse_zones": REVERSE_FLOOR},
           "spike_rule": "month-on-month change >= floor, >= 10% of the previous level, and "
                         ">= 4x the median absolute monthly change of the preceding 12 months; "
                         "consecutive spike months merge into one episode",
           "cases": cases}
    Path(a.out).write_text(json.dumps(doc, indent=1, default=str), "utf-8")

    rows = []
    for rfc, c in cases.items():
        for j in c["spikes"]:
            r = {k: v for k, v in j.items() if not isinstance(v, dict)}
            for k, v in j.items():
                if isinstance(v, dict):
                    for kk, vv in v.items():
                        r[f"{k}_{kk}"] = vv
            rows.append(r)
    pd.DataFrame(rows).to_csv("out/analysis/dns_program_rfc_spikes.csv", index=False)
    rows = []
    for rfc, c in cases.items():
        for r in c.get("new_signings", {}).get("around_releases", []):
            rows.append({"rfc": rfc, **r})
    pd.DataFrame(rows).to_csv("out/analysis/dns_program_rfc_new_signings.csv", index=False)

    for rfc, c in cases.items():
        s = c["summary"]
        print(f"{rfc}: {s['n_spikes']} spikes ({s['n_forward']} forward, {s['n_reverse']} reverse); "
              f"within {WINDOW}m of signer release {s[f'spikes_within_{WINDOW}m_of_signer_release']}, "
              f"of default {s[f'spikes_within_{WINDOW}m_of_default_change']}, of CVE "
              f"{s[f'spikes_within_{WINDOW}m_of_cve']}, of any release "
              f"{s[f'spikes_within_{WINDOW}m_of_any_release']}; chance {c['chance']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
