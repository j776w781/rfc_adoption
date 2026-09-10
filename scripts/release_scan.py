"""Every release of every project, against the delegation change ledger.

Asks the direct question -- for each version, did adoption move after it? -- and
reports the answer at the only resolution the data supports.

**The identification problem, first.** 1,083 releases land in 193 corpus months.
97% of months contain a release from some project and 100% sit within three
months of one, so there is no "no release happened" control at the ecosystem
level and no per-release effect is identifiable. Per project a control does
exist: OpenDNSSEC releases in 26% of months, PowerDNS Authoritative in 33%. Those
are the comparisons this script runs.

**Two confounds had to be removed before any of this means anything.**

Delegation changes rise roughly twenty-five-fold from 2009 to 2019 and stay high,
and projects differ in when they released: PowerDNS Recursor's median release
year is 2022, OpenDNSSEC's is 2014. Comparing raw counts therefore ranks projects
by how recently they shipped, not by any effect. So the series is **detrended**
against a centred two-year rolling median, and the contrast is computed on the
residual -- each release is judged against its own era.

And the null must preserve each project's release schedule. Shuffling release
months uniformly destroys their clustering, so a late-clustered schedule beats a
uniform null automatically. The null here is a **circular shift**: the whole
schedule slides by a random offset, keeping every gap between releases intact and
changing only where it lands.

Reads out/analysis/delegation_changes.parquet and data/software/release_dates.json.
Writes out/analysis/release_scan.json plus a per-release CSV.
"""
from __future__ import annotations

import argparse
import json
import random
from datetime import date
from pathlib import Path

import pandas as pd

WINDOW = 3          # months counted as "after" a release, inclusive of its own
PERMUTATIONS = 2000
SEED = 20260910


def month_range(months: list[str], start: str, k: int) -> list[str]:
    if start not in months:
        return []
    i = months.index(start)
    return months[i:i + k]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", type=Path,
                    default=Path("out/analysis/delegation_changes.parquet"))
    ap.add_argument("--releases", type=Path,
                    default=Path("data/software/release_dates.json"))
    ap.add_argument("--out", type=Path, default=Path("out/analysis/release_scan.json"))
    ap.add_argument("--csv", type=Path,
                    default=Path("out/analysis/dns_release_scan_per_release.csv"))
    args = ap.parse_args()

    led = pd.read_parquet(args.ledger)
    rel = json.loads(args.releases.read_text(encoding="utf-8"))

    months = sorted(led.month.unique())
    span = set(months)
    # Adoption events only: an unsign is not adoption, and pooling the two hides
    # the sign of any effect.
    adopt = led[led.kind.isin(["sign", "rollover"])]
    per_month = adopt.groupby("month").delegation.nunique().reindex(months, fill_value=0)

    # Detrend: judge each month against its own era, not against 2009.
    trend = per_month.rolling(25, center=True, min_periods=5).median()
    resid = (per_month - trend).fillna(0.0)

    rng = random.Random(SEED)
    density, projects, per_release = {}, {}, []

    for proj, meta in sorted(rel.items()):
        dates = sorted({d[:7] for d in meta["releases"].values() if d[:7] in span})
        density[proj] = {"releases_total": len(meta["releases"]),
                         "releases_in_span": len(dates),
                         "months_with_a_release": len(dates),
                         "share_of_months": round(len(dates) / len(months), 3)}
        if not dates or len(dates) >= len(months) - WINDOW:
            projects[proj] = {"testable": False,
                              "why": "releases cover the whole span; no control months"}
            continue

        idx = {m: i for i, m in enumerate(months)}

        def contrast(release_months, series):
            after = set()
            for m in release_months:
                after.update(month_range(months, m, WINDOW))
            other = [m for m in months if m not in after]
            after = [m for m in months if m in after]
            if not other or not after:
                return None
            return (series[after].mean(), series[other].mean(),
                    series[after].mean() - series[other].mean())

        obs = contrast(dates, resid)
        raw = contrast(dates, per_month)
        if obs is None:
            projects[proj] = {"testable": False, "why": "window covers every month"}
            continue
        # Circular shift: keeps every gap in the schedule, moves only its phase.
        offsets = [i for i in range(1, len(months))]
        null = []
        for _ in range(PERMUTATIONS):
            k = rng.choice(offsets)
            shifted = [months[(idx[m] + k) % len(months)] for m in dates]
            c = contrast(shifted, resid)
            if c:
                null.append(c[2])
        beat = sum(1 for v in null if v >= obs[2])
        projects[proj] = {
            "testable": True, "role": meta["role"],
            "n_release_months": len(dates),
            "median_release_year": sorted(int(d[:4]) for d in meta["releases"].values())
                                   [len(meta["releases"]) // 2],
            "raw_mean_after": round(raw[0], 2),
            "raw_mean_other": round(raw[1], 2),
            "raw_difference": round(raw[2], 2),
            "detrended_after": round(obs[0], 2),
            "detrended_other": round(obs[1], 2),
            "detrended_difference": round(obs[2], 2),
            "circular_shift_p": round((beat + 1) / (len(null) + 1), 4),
            "n_permutations": len(null),
        }

        for ver, d in sorted(meta["releases"].items(), key=lambda kv: kv[1]):
            m = d[:7]
            win = month_range(months, m, WINDOW)
            per_release.append({
                "project": proj, "version": ver, "released": d, "month": m,
                "in_corpus_span": m in span,
                "changes_in_window": int(per_month[win].sum()) if win else "",
                "window_months": WINDOW,
                "corpus_median_window": int(per_month.rolling(WINDOW).sum().median()),
            })

    payload = {
        "generated": date.today().isoformat(),
        "corpus": {"months": [months[0], months[-1]], "n_months": len(months),
                   "basis": "reverse (RIR delegations); the forward per-day records "
                            "are not in this repository"},
        "window_months": WINDOW,
        "identification": {
            "months_with_any_release": round(
                len({m for p in rel.values() for d in p["releases"].values()
                     if (m := d[:7]) in span}) / len(months), 3),
            "note": "No ecosystem-level control exists. Only per-project tests are run.",
        },
        "release_density": density,
        "per_project": projects,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(per_release).to_csv(args.csv, index=False, lineterminator="\n")

    print(f"corpus {months[0]} .. {months[-1]} ({len(months)} months), "
          f"window {WINDOW} months")
    print(f"months containing any release: "
          f"{payload['identification']['months_with_any_release'] * 100:.0f}%  "
          f"-> no ecosystem-level control\n")
    print(f"{'project':12} {'med yr':>6} {'raw diff':>9} {'detrended':>10} "
          f"{'shift p':>8}")
    for proj, r in projects.items():
        if not r.get("testable"):
            print(f"{proj:12} {'-':>6} {r['why']}")
            continue
        star = "  *" if r["circular_shift_p"] < 0.05 else ""
        print(f"{proj:12} {r['median_release_year']:>6} {r['raw_difference']:>9} "
              f"{r['detrended_difference']:>10} {r['circular_shift_p']:>8}{star}")
    print("\nraw diff ranks projects by how recently they shipped; the detrended "
          "column is the one to read.")
    print(f"\nwrote {args.out} and {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
