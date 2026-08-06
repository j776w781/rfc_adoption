"""Merging checkpoints that were produced by several machines.

A sharded run is normally gathered as one subdirectory per machine or per year,
so the merge has to walk those rather than assume a single flat directory. The
failure mode this guards is silent: the aggregate counts merge correctly and look
entirely healthy while the exemplars are missed, which costs every reasoning
trace, every score and the whole ranking. A real 3,127-partition merge produced
2.76 billion rows of correct aggregates and zero ranked candidates before this was
fixed.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import duckdb
import pytest

from openintel_rfc import sql_compiler
from openintel_rfc.parquet_reader import describe_parquet
from openintel_rfc.scale_runner import (
    CHECKPOINT_SUFFIX,
    EXEMPLAR_DIRNAME,
    STATUS_SUFFIX,
    LocalPartition,
    merge_checkpoints,
    process_partition,
)
from openintel_rfc.schema_checker import queryable_field_names
from openintel_rfc.config import ALWAYS_SELECT_FIELDS


def _needed(schema_report):
    return sorted(set(queryable_field_names(schema_report)) | set(ALWAYS_SELECT_FIELDS))


@pytest.fixture()
def flat_checkpoints(tmp_path, checklist_db, dictionary, schema_report, sample_parquet_path):
    """One real checkpoint, written the way a single-machine run writes it."""
    columns = [c["name"] for c in describe_parquet(sample_parquet_path)["columns"]]
    column_expr = sql_compiler.build_column_expressions(
        dictionary, _needed(schema_report), columns
    )
    compiled = sql_compiler.compile_checklist(checklist_db, column_expr, schema_report)
    partition = LocalPartition.from_paths(
        [sample_parquet_path], partition_id="shard-a", source="zonefile-sample"
    )
    checkpoints = tmp_path / "flat"
    connection = duckdb.connect(database=":memory:")
    try:
        process_partition(
            partition,
            uris=list(partition.paths),
            connection=connection,
            compiled=compiled,
            column_expr=column_expr,
            checkpoint_dir=checkpoints,
            exemplars_per_group=5,
        )
    finally:
        connection.close()
    return checkpoints


def _shard(flat: Path, target: Path, name: str) -> Path:
    """Copy a flat checkpoint directory into ``target/<name>/``, as rsync would."""
    destination = target / name
    shutil.copytree(flat, destination)
    return destination


def test_recursive_merge_finds_checkpoints_in_shard_subdirectories(flat_checkpoints, tmp_path):
    gathered = tmp_path / "gathered"
    _shard(flat_checkpoints, gathered, "from-machine-1")

    assert merge_checkpoints(gathered, recursive=False).rows_scanned == 0, (
        "a non-recursive merge should not see into shard subdirectories"
    )
    assert merge_checkpoints(gathered, recursive=True).rows_scanned == 73


def test_recursive_merge_loads_exemplars_from_each_shard(flat_checkpoints, tmp_path):
    """The regression: aggregates merge, exemplars silently do not.

    Exemplars live in a shard-local ``exemplars/`` directory. Resolving them
    against the gathered root instead of beside their own aggregate finds none,
    and the run reports healthy corpus counts with no traces and no ranking.
    """
    gathered = tmp_path / "gathered"
    _shard(flat_checkpoints, gathered, "from-machine-1")

    flat = merge_checkpoints(flat_checkpoints)
    sharded = merge_checkpoints(gathered, recursive=True)

    assert not flat.exemplars.empty, "fixture produced no exemplars to begin with"
    assert len(sharded.exemplars) == len(flat.exemplars)
    assert sharded.exemplars_per_group == flat.exemplars_per_group


def test_exemplar_files_are_not_mistaken_for_checkpoints(flat_checkpoints, tmp_path):
    """Exemplars share the partition name and the .parquet suffix.

    Counting them as checkpoints would double the partition count and emit a
    "no status file" warning for every partition in the run.
    """
    gathered = tmp_path / "gathered"
    _shard(flat_checkpoints, gathered, "from-machine-1")

    exemplars = list((gathered / "from-machine-1" / EXEMPLAR_DIRNAME).glob(f"*{CHECKPOINT_SUFFIX}"))
    assert exemplars, "fixture wrote no exemplar files"

    merged = merge_checkpoints(gathered, recursive=True)
    assert len(merged.partition_ids) == 1
    assert not any("status" in w for w in merged.warnings)


def test_a_partition_present_in_two_shards_is_counted_once(flat_checkpoints, tmp_path):
    """Overlapping ranges are wasteful but must not double-count.

    A partition's checkpoint is deterministic, so two shards that both covered a
    day hold interchangeable copies. Summing both would inflate that day.
    """
    gathered = tmp_path / "gathered"
    _shard(flat_checkpoints, gathered, "from-machine-1")
    _shard(flat_checkpoints, gathered, "from-machine-2")

    merged = merge_checkpoints(gathered, recursive=True)
    assert len(merged.partition_ids) == 1
    assert merged.rows_scanned == 73
    assert any("more than one shard" in w for w in merged.warnings)


def test_sharded_merge_equals_the_flat_merge(flat_checkpoints, tmp_path):
    """Sharding must not change the answer, only where the work happened."""
    gathered = tmp_path / "gathered"
    _shard(flat_checkpoints, gathered, "shard-1")

    flat = merge_checkpoints(flat_checkpoints)
    sharded = merge_checkpoints(gathered, recursive=True)

    assert sharded.rows_scanned == flat.rows_scanned
    assert sharded.rows_matched == flat.rows_matched
    assert sorted(sharded.partition_ids) == sorted(flat.partition_ids)

    def key(rows):
        return sorted(
            (r.rfc_id, r.indicator_id, r.decision, r.source, r.year_month, r.count)
            for r in rows
        )

    assert key(sharded.rows) == key(flat.rows)


def test_status_file_is_read_from_beside_its_own_checkpoint(flat_checkpoints, tmp_path):
    """A shard-local status file must not be looked for at the gathered root."""
    gathered = tmp_path / "gathered"
    shard = _shard(flat_checkpoints, gathered, "shard-1")

    statuses = list(shard.glob(f"*{STATUS_SUFFIX}"))
    assert statuses, "fixture wrote no status file"
    assert not list(gathered.glob(f"*{STATUS_SUFFIX}")), "status must stay in the shard"

    merged = merge_checkpoints(gathered, recursive=True)
    assert merged.rows_scanned == 73
    assert json.loads(statuses[0].read_text(encoding="utf-8"))["complete"] is True
