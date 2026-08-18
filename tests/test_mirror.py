"""Splitting a 2 TB mirror across machines without duplicating or losing work."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from openintel_rfc.mirror import (
    MirrorReport,
    RemoteObject,
    _already_present,
    describe_plan,
    mirror_objects,
    plan_shards,
)


def obj(key: str, size: int, source: str = "se", day: str = "2021-01-11") -> RemoteObject:
    return RemoteObject(
        key=f"fdns/basis=zonefile/source={source}/{key}",
        size=size,
        source=source,
        basis="zonefile",
        day=date.fromisoformat(day),
    )


# --------------------------------------------------------------------------- #
# The split
# --------------------------------------------------------------------------- #


def test_every_object_is_assigned_exactly_once() -> None:
    """Losing an object silently shortens the corpus; duplicating one wastes a
    scarce request budget and a lot of bandwidth."""
    objects = [obj(f"o{i}", size=i * 1000 + 1) for i in range(97)]
    buckets = plan_shards(objects, 7)

    flat = [o for bucket in buckets for o in bucket]
    assert len(flat) == len(objects)
    assert {o.key for o in flat} == {o.key for o in objects}


def test_split_balances_on_bytes_not_object_count() -> None:
    """The corpus is 1.49 TB of .se and 15.8 GB of .gov.

    A split by day or by year hands one machine 750 GB and another 2 GB, which is
    why the overnight run's per-year shards were so lopsided. Balance has to be
    measured in bytes.
    """
    # One enormous object and many tiny ones: count-balancing gets this very wrong.
    objects = [obj("huge", size=500_000_000_000)] + [
        obj(f"small{i}", size=1_000_000) for i in range(400)
    ]
    buckets = plan_shards(objects, 2)
    loads = sorted(sum(o.size for o in b) for b in buckets)

    # Perfect balance is impossible -- one object is bigger than half the corpus --
    # so the requirement is that the small objects all pile onto the other shard.
    assert len(buckets[0]) != len(buckets[1]), "a count-balanced split would tie here"
    assert loads[0] == 400 * 1_000_000
    assert loads[1] == 500_000_000_000


def test_split_of_similar_objects_is_nearly_even() -> None:
    objects = [obj(f"o{i}", size=1_000_000_000) for i in range(100)]
    buckets = plan_shards(objects, 4)
    loads = [sum(o.size for o in b) for b in buckets]
    assert max(loads) == min(loads), "equal objects must split exactly"


def test_split_is_deterministic_across_machines() -> None:
    """Each machine plans independently; they must agree without talking.

    There is no coordinator and no shared filesystem in the general case, so
    agreement has to fall out of the algorithm rather than out of a lock.
    """
    objects = [obj(f"o{i}", size=(i * 7919) % 1000 + 1) for i in range(300)]
    first = plan_shards(objects, 5)
    # A different listing order, as two machines may well see.
    second = plan_shards(list(reversed(objects)), 5)
    assert [[o.key for o in b] for b in first] == [[o.key for o in b] for b in second]


def test_equal_sized_objects_still_split_deterministically() -> None:
    """Ties must break on something stable, or two machines fetch the same file."""
    objects = [obj(f"o{i}", size=1000) for i in range(20)]
    assert [[o.key for o in b] for b in plan_shards(objects, 3)] == [
        [o.key for o in b] for b in plan_shards(sorted(objects, key=lambda o: o.key, reverse=True), 3)
    ]


def test_single_shard_takes_everything() -> None:
    objects = [obj(f"o{i}", size=i + 1) for i in range(10)]
    buckets = plan_shards(objects, 1)
    assert len(buckets) == 1 and len(buckets[0]) == 10


def test_shard_count_below_one_is_treated_as_one() -> None:
    objects = [obj("o", size=1)]
    assert len(plan_shards(objects, 0)) == 1


def test_more_shards_than_objects_leaves_empty_shards() -> None:
    """A machine with nothing to do must be told so, not handed a phantom object."""
    buckets = plan_shards([obj("only", size=5)], 4)
    assert len(buckets) == 4
    assert sum(len(b) for b in buckets) == 1


def test_describe_plan_reports_the_spread() -> None:
    objects = [obj(f"o{i}", size=1_000_000_000) for i in range(8)]
    text = describe_plan(plan_shards(objects, 4))
    assert "spread" in text
    assert "0.0%" in text


# --------------------------------------------------------------------------- #
# What counts as already mirrored
# --------------------------------------------------------------------------- #


def test_short_file_is_not_accepted_as_present(tmp_path: Path) -> None:
    """The failure this guards against is silent.

    A truncated object scans without error and simply returns fewer rows, so an
    interrupted mirror would quietly become an under-counted analysis.
    """
    path = tmp_path / "part-00000.gz.parquet"
    path.write_bytes(b"x" * 100)
    assert _already_present(path, 500) is False
    assert _already_present(path, 100) is True


def test_missing_and_empty_files_are_not_present(tmp_path: Path) -> None:
    missing = tmp_path / "nope.parquet"
    assert _already_present(missing, 10) is False
    empty = tmp_path / "empty.parquet"
    empty.write_bytes(b"")
    assert _already_present(empty, 10) is False


def test_cache_path_matches_download_mode_layout() -> None:
    """A mirror nobody can read is not a mirror.

    ``--mode download --cache-dir`` computes this path independently, so the two
    must agree exactly or the scan re-fetches everything from the store.
    """
    o = obj("year=2021/month=01/day=11/part-00000.gz.parquet", size=1, day="2021-01-11")
    assert o.cache_path("/cache") == Path(
        "/cache/zonefile/se/2021-01-11/part-00000.gz.parquet"
    )


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #


class _FakeS3:
    def __init__(self, payloads: dict[str, bytes]):
        self.payloads = payloads
        self.calls: list[str] = []

    def download_file(self, *, Bucket: str, Key: str, Filename: str) -> None:  # noqa: N803
        self.calls.append(Key)
        Path(Filename).write_bytes(self.payloads[Key])


def _config(tmp_path: Path):
    from openintel_rfc.openintel_source import AccessConfig

    return AccessConfig(mode="download", cache_dir=tmp_path)


def test_mirror_writes_then_skips_on_a_second_pass(tmp_path: Path) -> None:
    o = obj("year=2021/month=01/day=11/part-00000.gz.parquet", size=4, day="2021-01-11")
    fake = _FakeS3({o.key: b"abcd"})
    config = _config(tmp_path)

    first = mirror_objects([o], config=config, cache_dir=tmp_path, client=fake)
    assert first.fetched == 1 and first.failed == 0
    assert o.cache_path(tmp_path).read_bytes() == b"abcd"

    second = mirror_objects([o], config=config, cache_dir=tmp_path, client=fake)
    assert second.skipped == 1 and second.fetched == 0
    assert fake.calls == [o.key], "an already-mirrored object must not be re-fetched"


def test_mirror_discards_a_short_download(tmp_path: Path) -> None:
    """Better to fail loudly than to leave a file a later scan will trust."""
    o = obj("year=2021/month=01/day=11/part-00000.gz.parquet", size=99, day="2021-01-11")
    fake = _FakeS3({o.key: b"too short"})
    report = mirror_objects([o], config=_config(tmp_path), cache_dir=tmp_path, client=fake)

    assert report.failed == 1 and report.fetched == 0
    assert not o.cache_path(tmp_path).exists()
    assert not o.cache_path(tmp_path).with_suffix(".parquet.part").exists()
    assert any("short copy was discarded" in w for w in report.warnings)


def test_mirror_leaves_no_part_file_when_a_download_raises(tmp_path: Path) -> None:
    o = obj("year=2021/month=01/day=11/part-00000.gz.parquet", size=4, day="2021-01-11")

    class _Boom(_FakeS3):
        def download_file(self, *, Bucket, Key, Filename):  # noqa: N803
            Path(Filename).write_bytes(b"ab")
            raise RuntimeError("connection reset")

    report = mirror_objects([o], config=_config(tmp_path), cache_dir=tmp_path,
                            client=_Boom({}))
    assert report.failed == 1
    assert list(tmp_path.rglob("*.part")) == []


def test_dry_run_touches_nothing(tmp_path: Path) -> None:
    o = obj("year=2021/month=01/day=11/part-00000.gz.parquet", size=4, day="2021-01-11")
    fake = _FakeS3({o.key: b"abcd"})
    report = mirror_objects([o], config=_config(tmp_path), cache_dir=tmp_path,
                            client=fake, dry_run=True)
    assert report.fetched == 1 and fake.calls == []
    assert not o.cache_path(tmp_path).exists()


def test_report_describes_itself() -> None:
    report = MirrorReport(fetched=2, skipped=1, bytes_fetched=2_000_000_000,
                          elapsed_seconds=100.0)
    text = report.describe()
    assert "2 fetched" in text and "MB/s" in text
    assert report.complete is True
