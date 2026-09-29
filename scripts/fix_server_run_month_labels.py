"""Relabel the server run's reverse months to the UTC convention (label = snapshot month).

The server run was extracted on a UTC-negative host before d5121351, so each reverse
snapshot taken at 00:00 UTC on day 1 of month M was labelled M-1. The panel run and the
delegation ledger label it M. This script moves every `basis == "reverse"` row of
out/server_run/timeline_monthly.parquet forward by one month so all three sources share
one convention. Forward (`zonefile`) rows are left alone: their labels are off only by the
first hours of day 1 of the next month, which cannot be separated after aggregation.

Convention after the fix, for every reverse source: label M = the zone state at 00:00 UTC
on the 1st of M. A change between labels M-1 and M happened during calendar month M-1.

Idempotent: a marker file records that the shift was applied; the original is kept as
timeline_monthly.pre_utc_fix.parquet. Verification: after the shift, server-run afrinic
and arin must equal the panel run's afrinic and arin on every shared month.

    python scripts/fix_server_run_month_labels.py [--check-only]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

SRV = Path("out/server_run/timeline_monthly.parquet")
BACKUP = SRV.with_name("timeline_monthly.pre_utc_fix.parquet")
MARKER = SRV.with_name("month_labels_utc.json")
PANEL = Path("out/panel_run/timeline_monthly.parquet")


def shift(month: str, k: int = 1) -> str:
    return str(pd.Period(month, freq="M") + k)


def agreement(srv: pd.DataFrame, pan: pd.DataFrame) -> dict:
    out = {}
    for rir in ("afrinic", "arin"):
        for dim in ("all", "algorithm_ds"):
            a = srv[(srv.source == rir) & (srv.dimension == dim)].set_index(["month", "value"])["domains_peak"]
            b = pan[(pan.source == rir) & (pan.dimension == dim)].set_index(["month", "value"])["domains_peak"]
            common = a.index.intersection(b.index)
            out[f"{rir}/{dim}"] = {"compared": int(len(common)),
                                   "equal": int((a.loc[common] == b.loc[common]).sum())}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    a = ap.parse_args()
    srv = pd.read_parquet(SRV)
    pan = pd.read_parquet(PANEL)
    if MARKER.exists():
        print(f"already applied: {MARKER.read_text().strip()}")
        print(json.dumps(agreement(srv, pan), indent=1))
        return 0
    before = agreement(srv, pan)
    fixed = srv.copy()
    rev = fixed.basis == "reverse"
    fixed.loc[rev, "month"] = fixed.loc[rev, "month"].map(shift)
    after = agreement(fixed, pan)
    print("before:", json.dumps(before)); print("after: ", json.dumps(after))
    bad = [k for k, v in after.items() if v["compared"] == 0 or v["equal"] != v["compared"]]
    if bad:
        print(f"refusing to write: shifted series do not match the panel for {bad}")
        return 1
    if a.check_only:
        return 0
    shutil.copy2(SRV, BACKUP)
    fixed.to_parquet(SRV, index=False)
    MARKER.write_text(json.dumps({"applied_by": "scripts/fix_server_run_month_labels.py",
                                  "reverse_rows_shifted": int(rev.sum()), "shift_months": 1,
                                  "backup": BACKUP.name, "agreement_after": after}, indent=1) + "\n")
    print(f"shifted {int(rev.sum())} reverse rows; backup {BACKUP}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
