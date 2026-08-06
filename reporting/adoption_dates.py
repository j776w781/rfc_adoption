"""Per-RFC adoption dates: first, median, mean and last observation vs publication.

Two weightings are reported because they answer different questions and can
disagree:

* **observation-weighted** — each matching record counts once. This is what the
  corpus literally contains, but it is biased by how often each zone was measured
  and by how large it is.
* **rate-weighted** — each month is weighted by its records *per measurement day*,
  so a month with 30 measured days does not outweigh one with 3.

Neither is "adoption over time" in the population sense; both are summaries of
when the evidence sits inside this corpus.
"""
from __future__ import annotations

import collections
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, "src")
from openintel_rfc.scale_runner import merge_checkpoints

CKPT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("out/final/checkpoints")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("out/analysis")
CHECKLIST = Path("data/rfc_checklists/dnssec_rfc_checklists.json")

status = [json.loads(p.read_text()) for p in CKPT.rglob("*.status.json")]
near_empty = {(r["source"], r["date"]) for r in status if r["rows_scanned"] < 100}
days_per_month = collections.Counter()
for r in status:
    if (r["source"], r["date"]) not in near_empty:
        days_per_month[r["date"][:7]] += 1

corpus_first = min(r["date"] for r in status)
corpus_last = max(r["date"] for r in status)

# Every day on which *some* source was measured. A first sighting that lands on a
# day whose predecessor was not measured is censored by a coverage gap, not just
# by the start of the corpus -- the mechanism may have appeared during the hole.
measured = {r["date"] for r in status if (r["source"], r["date"]) not in near_empty}


def censored_reason(first: date) -> str:
    if first.isoformat() <= corpus_first:
        return "corpus start"
    previous = date.fromordinal(first.toordinal() - 1).isoformat()
    return "after a coverage gap" if previous not in measured else ""

agg = merge_checkpoints(CKPT, recursive=True)
monthly: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
for r in agg.rows:
    if r.rfc_id != "*" and r.indicator_id == "*" and r.decision in ("valid_match", "ambiguous"):
        monthly[r.rfc_id][r.year_month] += r.count

pub = {e["rfc_id"]: datetime.fromisoformat(e["publication_date"]).date()
       for e in json.loads(CHECKLIST.read_text(encoding="utf-8"))["rfcs"]}
title = {e["rfc_id"]: e["title"] for e in json.loads(CHECKLIST.read_text(encoding="utf-8"))["rfcs"]}

timeline = {e["rfc_id"]: e for e in
            json.loads((OUT / "adoption_timeline.json").read_text())["timeline"]}


def mid(ym: str) -> date:
    y, m = int(ym[:4]), int(ym[5:7])
    return date(y, m, 15)


def weighted_stats(weights: dict[str, float]) -> tuple[date | None, date | None]:
    """Return (median month, mean month) of a month -> weight distribution."""
    items = sorted((m, w) for m, w in weights.items() if w > 0)
    if not items:
        return None, None
    total = sum(w for _, w in items)
    run = 0.0
    median = None
    for m, w in items:
        run += w
        if median is None and run >= total / 2:
            median = mid(m)
    ordinal = sum(mid(m).toordinal() * w for m, w in items) / total
    return median, date.fromordinal(round(ordinal))


rows = []
for rfc in sorted(monthly, key=lambda r: pub[r]):
    counts = monthly[rfc]
    tl = timeline.get(rfc, {})
    first = (datetime.fromisoformat(tl["first_seen"]).date()
             if tl.get("first_seen") else mid(min(counts)))
    last = (datetime.fromisoformat(tl["last_seen"]).date()
            if tl.get("last_seen") else mid(max(counts)))
    obs_median, obs_mean = weighted_stats(dict(counts))
    rate = {m: c / days_per_month[m] for m, c in counts.items() if days_per_month[m]}
    rate_median, rate_mean = weighted_stats(rate)
    p = pub[rfc]
    lag = lambda d: (d - p).days if d else None  # noqa: E731
    rows.append({
        "rfc_id": rfc,
        "title": title[rfc],
        "published": p.isoformat(),
        "first_seen": first.isoformat(),
        "first_seen_lag_days": lag(first),
        "median_obs": obs_median.isoformat(),
        "median_obs_lag_days": lag(obs_median),
        "mean_obs": obs_mean.isoformat(),
        "mean_obs_lag_days": lag(obs_mean),
        "median_rate": rate_median.isoformat(),
        "median_rate_lag_days": lag(rate_median),
        "mean_rate": rate_mean.isoformat(),
        "mean_rate_lag_days": lag(rate_mean),
        "last_seen": last.isoformat(),
        "observations": sum(counts.values()),
        "months_seen": len(counts),
        "first_seen_censored": censored_reason(first) or "no",
    })

OUT.mkdir(parents=True, exist_ok=True)
csv_path = OUT / "rfc_adoption_dates.csv"
with csv_path.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)

def yrs(d: int | None) -> str:
    return "" if d is None else f"{d/365.25:+.1f}y"

md = [
    "# RFC adoption dates versus publication",
    "",
    f"Corpus window: **{corpus_first} to {corpus_last}** "
    f"({len(status) - len(near_empty):,} measurement days across .gov, .nu, .se).",
    "",
    "`first` is the earliest observation; `median`/`mean` summarise *when the "
    "evidence sits* in the window, not when deployment happened. Two weightings "
    "are given: **obs** counts every record, **rate** weights each month by its "
    "records per measurement day so unevenly-sampled months do not dominate.",
    "",
    "| RFC | Published | First seen | Lag | Median (obs) | Median (rate) | Mean (rate) | Last seen | Observations |",
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
]
for r in rows:
    star = " \\*" if r["first_seen_censored"] != "no" else ""
    md.append(
        f"| {r['rfc_id']} | {r['published']} | {r['first_seen']}{star} | "
        f"{yrs(r['first_seen_lag_days'])} | {r['median_obs']} | {r['median_rate']} | "
        f"{r['mean_rate']} | {r['last_seen']} | {r['observations']:,} |"
    )
censored = [f'{r["rfc_id"]} ({r["first_seen_censored"]})' for r in rows
            if r["first_seen_censored"] != "no"]
md += [
    "",
    f"\\* **First seen is censored** for {', '.join(censored)}.",
    "",
    f"*corpus start* — the earliest observation is the first measured day "
    f"({corpus_first}), so the mechanism was already deployed before measurement "
    "began. The lag is a lower bound on how long it had been in use, not a "
    "time-to-adoption.",
    "",
    "*after a coverage gap* — the first sighting falls on the day measurement "
    "resumed, so the mechanism may have appeared at any point during the hole. "
    "The lag is an upper bound.",
    "",
    "Rows without a \* are the only ones whose lag is a genuine "
    "time-from-publication: the mechanism was absent on the previous measured "
    "day and present on this one.",
    "",
    "`last seen` reflects the end of measurement, not the end of use.",
]
md_path = OUT / "rfc_adoption_dates.md"
md_path.write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")

print("\n".join(md))
print(f"\nwrote {csv_path}\nwrote {md_path}")
