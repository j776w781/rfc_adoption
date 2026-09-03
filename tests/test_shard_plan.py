"""Sharding a local scan across machines that share a NAS.

The property that matters is a partition: every source-day lands in exactly one
shard. If a day were in two, its records would be counted twice; if it were in
none, the corpus would be quietly short. Neither shows up as an error -- both
just produce plausible wrong numbers -- so both are pinned here.
"""
from __future__ import annotations

from datetime import date

from openintel_rfc.cache_index import CachedDay
from openintel_rfc.mirror import plan_shards

SIZE = dict(size_of=lambda d: d.bytes_total, key_of=lambda d: d.key)


def _days(n, sizes=None):
    return [CachedDay(source=f"s{i % 4}", day=date(2020, 1, 1 + i % 28),
                      basis="zonefile",
                      paths=[f"/nas/{i}.parquet"],
                      bytes_total=(sizes[i] if sizes else (i % 9 + 1) * 1000))
            for i in range(n)]


def test_every_day_lands_in_exactly_one_shard():
    days = _days(200)
    buckets = plan_shards(days, 5, **SIZE)
    seen = [id(d) for b in buckets for d in b]
    assert len(seen) == len(days), "no day may be dropped or duplicated"
    assert len({id(d) for d in days}) == len(set(seen))


def test_shards_balance_on_bytes_not_on_day_count():
    """One huge day must not sit alongside a hundred small ones."""
    sizes = [100_000] + [100] * 99
    buckets = plan_shards(_days(100, sizes), 4, **SIZE)
    loads = sorted(sum(d.bytes_total for d in b) for b in buckets)
    counts = sorted(len(b) for b in buckets)
    assert counts[0] == 1, "the huge day gets a shard nearly to itself"
    assert loads[-1] == 100_000


def test_the_plan_is_identical_on_every_machine():
    """No coordination: each machine computes the whole plan and keeps its slice."""
    days = _days(120)
    a = plan_shards(days, 4, **SIZE)
    b = plan_shards(list(reversed(days)), 4, **SIZE)
    assert [sorted(d.key for d in s) for s in a] == [sorted(d.key for d in s) for s in b]


def test_more_shards_than_days_leaves_empty_shards_not_duplicates():
    buckets = plan_shards(_days(3), 8, **SIZE)
    assert sum(len(b) for b in buckets) == 3
    assert sum(1 for b in buckets if not b) == 5


def test_one_shard_is_the_whole_corpus():
    days = _days(40)
    assert len(plan_shards(days, 1, **SIZE)[0]) == 40


# --------------------------------------------------------------------------- #
# merge_timeline must honour the run's selection
# --------------------------------------------------------------------------- #

def test_merge_only_folds_the_days_this_run_selected(tmp_path):
    """Two runs sharing an output directory must not pool into each other.

    A second pass with a different --sources into the same --out produced a
    timeline holding every RIR while the analysis beside it was labelled a
    two-RIR panel. The checkpoints are keyed by source-day so the merge can be
    filtered; it now is.
    """
    import pandas as pd
    from openintel_rfc.timeline_extract import merge_timeline

    ck = tmp_path / "checkpoints"
    ck.mkdir()
    wanted, stray = [], []
    for source, bucket in (("arin", wanted), ("ripe", stray)):
        day = CachedDay(source=source, day=date(2020, 1, 1), basis="reverse",
                        paths=["/x.parquet"])
        bucket.append(day)
        pd.DataFrame([{
            "source": source, "basis": "reverse", "day": "2020-01-01",
            "month": "2020-01", "dimension": "algorithm_ds", "value": "13",
            "records": 10, "domains": 10, "files": 1,
        }]).to_parquet(ck / f"reverse__{source}__2020-01-01.parquet", index=False)

    everything = merge_timeline(ck)
    selected = merge_timeline(ck, wanted)

    assert set(everything.source) == {"arin", "ripe"}, "unfiltered folds in both"
    assert set(selected.source) == {"arin"}, "filtered keeps only the selection"
