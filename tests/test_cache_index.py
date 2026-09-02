"""Multi-root discovery: the failure mode here is silent, so it gets real tests.

Part of the server's cache was moved to a second drive. If discovery reads one
root at a time, a source-day whose files are now split reports only the half it
can see -- and a half-sized day is indistinguishable from a day when fewer names
were signed. That is a measurement error the pipeline would never flag, so the
merge behaviour is pinned here rather than assumed.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from openintel_rfc.cache_index import (
    build_inventory, load_inventory, parse_path, save_inventory,
)
from openintel_rfc.utils import PipelineError


def _touch(path: Path, size: int = 16) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)
    return path


# --------------------------------------------------------------------------- #
# Layout parsing
# --------------------------------------------------------------------------- #

def test_parses_the_mirror_layout_this_project_writes():
    got = parse_path("/data/cache/zonefile/gov/2024-05-06/part-0.parquet")
    assert got == ("gov", date(2024, 5, 6), "zonefile")


def test_parses_openintel_hive_layout_without_zero_padding():
    # OpenINTEL writes month=5, not month=05.
    got = parse_path("/mnt/d2/source=nu/year=2021/month=5/day=7/part-0.parquet")
    assert got == ("nu", date(2021, 5, 7), "zonefile")


def test_parses_the_reverse_corpus_as_just_another_root():
    got = parse_path("out/reverse/corpus/reverse/arin/2015-10-01/zone.parquet")
    assert got == ("arin", date(2015, 10, 1), "reverse")


def test_returns_none_for_a_path_with_no_recoverable_date():
    assert parse_path("/data/cache/random/file.parquet") is None


def test_rejects_an_impossible_date_rather_than_guessing():
    assert parse_path("/data/source=gov/year=2021/month=13/day=1/x.parquet") is None


# --------------------------------------------------------------------------- #
# The merge across roots -- the reason this module exists
# --------------------------------------------------------------------------- #

def test_a_day_split_across_two_drives_is_merged_not_halved(tmp_path):
    """The exact production situation: same day, files on two drives."""
    root_a, root_b = tmp_path / "drive1", tmp_path / "drive2"
    _touch(root_a / "zonefile/gov/2024-05-06/part-0.parquet", 100)
    _touch(root_a / "zonefile/gov/2024-05-06/part-1.parquet", 100)
    _touch(root_b / "zonefile/gov/2024-05-06/part-2.parquet", 100)

    inventory = build_inventory([root_a, root_b])

    assert len(inventory.days) == 1, "one day, not one per drive"
    day = inventory.days["zonefile/gov/2024-05-06"]
    assert len(day.paths) == 3, "all three parts, not just the first drive's two"
    assert day.split_across_roots is True
    assert day.bytes_total == 300
    assert inventory.summary()["days_split_across_roots"] == 1


def test_reading_one_root_alone_would_have_undercounted(tmp_path):
    """Pins the bug this guards against, so it cannot regress quietly."""
    root_a, root_b = tmp_path / "drive1", tmp_path / "drive2"
    _touch(root_a / "zonefile/gov/2024-05-06/part-0.parquet")
    _touch(root_b / "zonefile/gov/2024-05-06/part-1.parquet")

    single = build_inventory([root_a])
    both = build_inventory([root_a, root_b])

    assert len(single.days["zonefile/gov/2024-05-06"].paths) == 1
    assert len(both.days["zonefile/gov/2024-05-06"].paths) == 2


def test_the_same_file_on_two_drives_is_counted_once(tmp_path):
    """A partial move leaves copies behind; scanning both would double counts."""
    root_a, root_b = tmp_path / "drive1", tmp_path / "drive2"
    _touch(root_a / "zonefile/gov/2024-05-06/part-0.parquet", 100)
    _touch(root_b / "zonefile/gov/2024-05-06/part-0.parquet", 100)  # same name

    inventory = build_inventory([root_a, root_b])

    day = inventory.days["zonefile/gov/2024-05-06"]
    assert len(day.paths) == 1, "one object, not two"
    assert day.bytes_total == 100, "size must not be double counted either"
    assert len(inventory.duplicates) == 1
    assert any("more than one root" in w for w in inventory.warnings)


def test_different_days_stay_separate_across_roots(tmp_path):
    root_a, root_b = tmp_path / "a", tmp_path / "b"
    _touch(root_a / "zonefile/gov/2024-05-06/p.parquet")
    _touch(root_b / "zonefile/gov/2024-05-07/p.parquet")

    inventory = build_inventory([root_a, root_b])
    assert len(inventory.days) == 2
    assert all(not d.split_across_roots for d in inventory.days.values())


# --------------------------------------------------------------------------- #
# Refusing to be quietly incomplete
# --------------------------------------------------------------------------- #

def test_unmatched_files_are_reported_not_silently_dropped(tmp_path):
    root = tmp_path / "drive"
    _touch(root / "zonefile/gov/2024-05-06/good.parquet")
    _touch(root / "loose/nowhere.parquet")

    inventory = build_inventory([root])

    assert len(inventory.unmatched) == 1
    assert "nowhere.parquet" in inventory.unmatched[0]
    assert any("matched no known layout" in w for w in inventory.warnings)


def test_a_missing_root_is_an_error_not_an_empty_result(tmp_path):
    with pytest.raises(PipelineError, match="does not exist"):
        build_inventory([tmp_path / "not-here"])


def test_a_corpus_with_nothing_recognisable_raises(tmp_path):
    _touch(tmp_path / "junk" / "a.parquet")
    with pytest.raises(PipelineError, match="matched a known layout"):
        build_inventory([tmp_path])


def test_no_roots_at_all_raises(tmp_path):
    with pytest.raises(PipelineError, match="at least one root"):
        build_inventory([])


# --------------------------------------------------------------------------- #
# Selection and round-tripping
# --------------------------------------------------------------------------- #

def test_select_filters_by_source_and_date(tmp_path):
    root = tmp_path / "drive"
    for src in ("gov", "nu"):
        for day in ("2024-05-06", "2024-06-06"):
            _touch(root / f"zonefile/{src}/{day}/p.parquet")

    inventory = build_inventory([root])
    chosen = inventory.select(sources=["gov"], start=date(2024, 6, 1))

    assert [d.key for d in chosen] == ["zonefile/gov/2024-06-06"]


def test_inventory_round_trips_through_disk(tmp_path):
    """A 14 TB walk is paid for once; the reload must not lose the merge."""
    root_a, root_b = tmp_path / "a", tmp_path / "b"
    _touch(root_a / "zonefile/gov/2024-05-06/p0.parquet", 50)
    _touch(root_b / "zonefile/gov/2024-05-06/p1.parquet", 50)

    original = build_inventory([root_a, root_b])
    path = save_inventory(original, tmp_path / "inventory.json")
    reloaded = load_inventory(path)

    assert set(reloaded.days) == set(original.days)
    day = reloaded.days["zonefile/gov/2024-05-06"]
    assert len(day.paths) == 2
    assert day.split_across_roots is True
    assert day.bytes_total == 100


def test_loose_layout_does_not_mistake_a_date_part_for_the_source():
    """`YYYY/MM/DD` splits the date across components; "05" is not a source."""
    got = parse_path("/data/openintel/nu/2020/01/05/part.parquet")
    assert got == ("nu", date(2020, 1, 5), "zonefile")


def test_a_truncated_duplicate_does_not_win_on_root_order(tmp_path):
    """An interrupted move leaves a short file; root order must not prefer it.

    The spill exists because files were moved between drives. A move that died
    partway leaves a truncated copy behind, and taking it because its drive was
    named first would read a short day as a real one.
    """
    main, spill = tmp_path / "main", tmp_path / "spill"
    _touch(main / "zonefile/gov/2024-05-06/part-0.parquet", 10)      # truncated
    _touch(spill / "zonefile/gov/2024-05-06/part-0.parquet", 5000)   # complete

    inventory = build_inventory([main, spill])   # main named FIRST

    day = inventory.days["zonefile/gov/2024-05-06"]
    assert len(day.paths) == 1
    assert "spill" in day.paths[0], "the complete copy must win"
    assert day.bytes_total == 5000
    assert any("DIFFERENT sizes" in w for w in inventory.warnings)


def test_identical_duplicates_still_follow_root_order(tmp_path):
    """When the copies agree, the first root wins and nothing is flagged."""
    main, spill = tmp_path / "main", tmp_path / "spill"
    _touch(main / "zonefile/gov/2024-05-06/part-0.parquet", 100)
    _touch(spill / "zonefile/gov/2024-05-06/part-0.parquet", 100)

    inventory = build_inventory([main, spill])

    day = inventory.days["zonefile/gov/2024-05-06"]
    assert "main" in day.paths[0]
    assert day.bytes_total == 100
    assert not any("DIFFERENT sizes" in w for w in inventory.warnings)
