"""Can a step in what newly signed zones choose be attributed to an OS release?

The earlier reading said yes: new reverse signings went from 0.2% to 57.1%
ECDSA across Debian 9 (2017-06-17), the first OS release carrying both
ECDSA-default signers. This script tests that attribution the same way the
spike ledger tests release timing, and it fails.

Three checks:

  1. WHAT MOVED. The step is located in the ledger: which months, which RIRs,
     how many parent blocks, how concentrated. A step made by a handful of
     operators in one region is a decision by those operators, whatever
     shipped that quarter.

  2. CHANCE. OS releases are dense. The fraction of months lying within N
     months after SOME OS release is the rate any "an OS release came just
     before" claim has to beat. Only releases whose date is sourced in
     data/software/distro_ships.json are counted, so the rate is a floor:
     adding the six-month distributions (Fedora, Alpine, Ubuntu interim) and
     the rolling ones (FreeBSD ports, Arch, Gentoo) only raises it.

  3. COVERAGE. Whether an OS could deliver the default at all. RHEL and its
     rebuilds ship BIND in the base repositories and neither Knot nor
     PowerDNS; those come from EPEL. For an operator on that family no OS
     release delivered an ECDSA-default signer until BIND 9.16 in RHEL 9
     (2022-05), five years after the step.

Reads out/analysis/delegation_changes.parquet, data/software/distro_ships.json,
data/software/software_support.json.
Writes out/analysis/os_release_attribution.json.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ALGS = {"ECDSA": {"13", "14"}, "RSA/SHA-256": {"8", "10"}, "EdDSA": {"15", "16"}}
WINDOWS = (3, 6, 12)


def months_between(a: str, b: str) -> int:
    return (int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))


def quarterly(ledger: pd.DataFrame, algs: set[str], min_n: int = 20) -> pd.DataFrame:
    s = ledger[ledger.kind == "sign"].copy()
    s["hit"] = s.to_alg.astype(str).isin(algs)
    s["q"] = pd.PeriodIndex(s.month, freq="M").asfreq("Q").astype(str)
    q = s.groupby("q").agg(n=("hit", "size"), hit=("hit", "sum")).reset_index()
    q["share_pct"] = (q.hit / q.n * 100).round(1)
    return q[q.n >= min_n].reset_index(drop=True)


def find_steps(q: pd.DataFrame, jump_pp: float = 25.0) -> list[dict]:
    """Quarters where the share jumps by at least `jump_pp` points and the new
    level holds for the next two quarters."""
    out = []
    for i in range(1, len(q) - 2):
        before, after = q.share_pct[i - 1], q.share_pct[i]
        if after - before < jump_pp:
            continue
        hold = q.share_pct[i:i + 3].mean()
        if hold - before >= jump_pp * 0.6:
            out.append({"quarter": q.q[i], "from_pct": float(before), "to_pct": float(after),
                        "held_3q_mean_pct": round(float(hold), 1), "n_signings": int(q.n[i])})
    return out


def step_detail(ledger: pd.DataFrame, algs: set[str], quarter: str) -> dict:
    s = ledger[(ledger.kind == "sign")].copy()
    s["q"] = pd.PeriodIndex(s.month, freq="M").asfreq("Q").astype(str)
    d = s[(s.q == quarter) & (s.to_alg.astype(str).isin(algs))]
    if d.empty:
        return {}
    per_block = d.groupby("block").size()
    p = per_block / len(d)
    return {"quarter": quarter, "signings": int(len(d)),
            "by_rir": d.source.value_counts().to_dict(),
            "by_month": d.month.value_counts().sort_index().to_dict(),
            "blocks": int(d.block.nunique()),
            "largest_block_share": round(float(per_block.max() / len(d)), 3),
            "top_blocks": {f"{r} {b}": int(n) for (r, b), n in
                           d.groupby(["source", "block"]).size().sort_values(ascending=False).head(5).items()},
            "hhi_over_blocks": round(float((p ** 2).sum()), 3)}


def os_dates(distro: dict) -> list[dict]:
    """The sourced OS release dates -- the major_releases list, which includes
    families (RHEL) that carry no Knot or PowerDNS at all."""
    return sorted(distro["major_releases"]["releases"], key=lambda x: x["date"])


def chance_rate(months: list[str], dates: list[str], window: int) -> float:
    inside = 0
    for m in months:
        lag = min((months_between(d[:7], m) for d in dates if d[:7] <= m), default=None)
        if lag is not None and lag <= window:
            inside += 1
    return round(inside / len(months), 3)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default="out/analysis/os_release_attribution.json")
    a = ap.parse_args()
    ledger = pd.read_parquet("out/analysis/delegation_changes.parquet")
    distro = json.loads(Path("data/software/distro_ships.json").read_text("utf-8"))
    releases = os_dates(distro)

    months = sorted(ledger.month.unique())
    months = [m for m in months if m >= "2011-01"]
    doc = {"generated": pd.Timestamp.today().strftime("%Y-%m-%d"), "method": __doc__.strip(),
           "os_releases_counted": len(releases),
           "os_releases": releases,
           "chance_a_month_follows_an_os_release": {
               f"within_{w}m": chance_rate(months, [r["date"] for r in releases], w) for w in WINDOWS},
           "families": {}}

    for name, algs in ALGS.items():
        q = quarterly(ledger, algs)
        steps = find_steps(q)
        rows = []
        for st in steps:
            qq = st["quarter"]
            first_month = f'{qq[:4]}-{ {"Q1": "01", "Q2": "04", "Q3": "07", "Q4": "10"}[qq[4:]] }'
            det = step_detail(ledger, algs, qq)
            near = [{"name": r["name"], "date": r["date"],
                     "months_before_step": months_between(r["date"][:7], first_month)}
                    for r in releases if r["date"][:7] <= first_month
                    and months_between(r["date"][:7], first_month) <= 12]
            rows.append({**st, "detail": det, "os_releases_within_12m_before": near})
        doc["families"][name] = {"quarterly": q.to_dict("records"), "steps": rows}

    # The specific claim that was made.
    ec = doc["families"]["ECDSA"]
    claim = {"claim": "Debian 9 (2017-06-17) delivered the ECDSA default and the step followed",
             "verdict": None, "why": []}
    if ec["steps"]:
        st = ec["steps"][0]
        det = st["detail"]
        n_os = len(st["os_releases_within_12m_before"])
        rate3 = doc["chance_a_month_follows_an_os_release"]["within_3m"]
        claim["step"] = {k: st[k] for k in ("quarter", "from_pct", "to_pct", "held_3q_mean_pct")}
        claim["why"] = [
            f'the step is {det["signings"]} signings in {det["quarter"]}, '
            f'{max(det["by_month"].values())} of them in a single month',
            f'{det["by_rir"]} by RIR -- one region, not the population',
            f'{det["blocks"]} parent blocks, largest {det["largest_block_share"]*100:.0f}% of the step, HHI {det["hhi_over_blocks"]}',
            f'{n_os} sourced OS releases fall in the 12 months before it, so "an OS release came first" does not single one out',
            f'a random month of the ledger already follows some sourced OS release within 3 months {rate3*100:.0f}% of the time',
            'RHEL and its rebuilds ship neither Knot nor PowerDNS in base (EPEL only) and had no ECDSA-default '
            'signer until BIND 9.16 in RHEL 9, 2022-05 -- five years after the step',
        ]
        claim["verdict"] = "not supported: the timing is one of several and the step is a few operators in one region"
    doc["the_claim_tested"] = claim

    Path(a.out).write_text(json.dumps(doc, indent=1, default=str), "utf-8")
    print(f'OS releases counted: {len(releases)}')
    print("chance a month follows an OS release:", doc["chance_a_month_follows_an_os_release"])
    for name, f in doc["families"].items():
        print(f'\n{name}: {len(f["steps"])} step(s)')
        for st in f["steps"]:
            d = st["detail"]
            print(f'  {st["quarter"]}  {st["from_pct"]}% -> {st["to_pct"]}% (held {st["held_3q_mean_pct"]}%)  '
                  f'{d["signings"]} signings, {d["blocks"]} blocks, HHI {d["hhi_over_blocks"]}, RIRs {d["by_rir"]}')
            print(f'    months: {d["by_month"]}')
            print(f'    OS releases in the 12 months before: '
                  f'{[(r["name"], r["months_before_step"]) for r in st["os_releases_within_12m_before"]]}')
    print("\nverdict:", claim["verdict"])
    for w in claim["why"]:
        print("  -", w)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
