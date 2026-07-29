"""Regressions for reading *real* OpenINTEL Parquet, not the synthetic fixture.

Every failure guarded here is silent: the pipeline keeps running and produces
plausible-looking output that is wrong. They were all found by building a file
with the real fDNS schema rather than by reading the sample, which is why these
tests construct their own inputs instead of using ``sample_openintel.parquet``.

Real-corpus facts these encode (confirmed against
``fdns/basis=zonefile/source=nu/year=2018/month=05/day=01/``):

* one column per record-type attribute, populated only for matching rows;
* ``timestamp`` is INT64 epoch **milliseconds**;
* NSEC3 carries ``nsec3_hash_algorithm`` / ``nsec3param_hash_algorithm``;
* there is no ``measurement_id`` column;
* DuckDB exposes Hive path segments as columns, typed by guessing from the text.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from openintel_rfc.parquet_reader import read_parquet, resolve_column_candidates
from openintel_rfc.signal_extractor import extract_signals

#: A row per DNSSEC record type, laid out the way OpenINTEL lays them out.
_REAL_ROWS = [
    ("CDS", {"cds_algorithm": 0, "cds_digest_type": 0, "cds_key_tag": 0}),
    ("CDNSKEY", {"cdnskey_algorithm": 0}),
    ("DNSKEY", {"dnskey_algorithm": 13}),
    ("DS", {"ds_algorithm": 8, "ds_digest_type": 2, "ds_key_tag": 12345}),
    ("RRSIG", {"rrsig_algorithm": 8, "rrsig_key_tag": 54321}),
    ("NSEC3", {"nsec3_hash_algorithm": 1}),
    ("NSEC3PARAM", {"nsec3param_hash_algorithm": 1}),
]

_REAL_COLUMNS = [
    "timestamp", "query_name", "response_name", "response_type",
    "dnskey_algorithm", "dnskey_flags",
    "ds_algorithm", "ds_digest_type", "ds_key_tag",
    "rrsig_algorithm", "rrsig_key_tag",
    "cds_algorithm", "cds_digest_type", "cds_key_tag",
    "cdnskey_algorithm", "cdnskey_flags",
    "nsec3_hash_algorithm", "nsec3_flags",
    "nsec3param_hash_algorithm", "nsec3param_flags",
]

#: 2018-05-01T00:00:00Z in epoch milliseconds, as OpenINTEL stores it.
_EPOCH_MS_BASE = 1_525_132_800_000

_NEEDED = ["rr_type", "algorithm", "digest_type", "key_tag", "flags"]


def _write_real_schema_parquet(target: Path) -> Path:
    records = []
    for index, (rr_type, populated) in enumerate(_REAL_ROWS):
        record: dict[str, object] = {column: None for column in _REAL_COLUMNS}
        record["timestamp"] = _EPOCH_MS_BASE + index * 86_400_000
        record["query_name"] = f"example{index}.nu."
        record["response_name"] = f"example{index}.nu."
        record["response_type"] = rr_type
        record.update(populated)
        records.append(record)

    frame = pd.DataFrame(records, columns=_REAL_COLUMNS)
    for column in _REAL_COLUMNS:
        if any(token in column for token in ("algorithm", "digest_type", "key_tag")):
            frame[column] = frame[column].astype("Int64")
    frame["timestamp"] = frame["timestamp"].astype("int64")

    target.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(target, index=False)
    return target


@pytest.fixture()
def real_schema_parquet(tmp_path: Path) -> Path:
    return _write_real_schema_parquet(tmp_path / "real_fdns.parquet")


def test_algorithm_resolves_every_record_type_specific_column(dictionary):
    """`algorithm` must draw on all of the per-record-type columns, not one."""
    candidates = resolve_column_candidates(dictionary, ["algorithm"], _REAL_COLUMNS)
    assert candidates["algorithm"][0] == "dnskey_algorithm"
    for expected in (
        "ds_algorithm", "rrsig_algorithm", "cds_algorithm",
        "cdnskey_algorithm", "nsec3_hash_algorithm", "nsec3param_hash_algorithm",
    ):
        assert expected in candidates["algorithm"], expected


@pytest.mark.parametrize("engine", ["duckdb", "pandas"])
def test_algorithm_is_coalesced_across_record_types(real_schema_parquet, dictionary, engine):
    """The regression that would hide every RFC 8078 delete signal.

    Binding `algorithm` to the first candidate (`dnskey_algorithm`) reads NULL
    for CDS rows, so the strongest evidence the pipeline can find disappears
    without any error.
    """
    frame = read_parquet(real_schema_parquet, dictionary, _NEEDED, engine=engine)
    observed = {
        signal.fields["rr_type"]: signal.fields.get("algorithm")
        for signal in extract_signals(frame)
    }
    assert observed == {
        "CDS": 0, "CDNSKEY": 0, "DNSKEY": 13, "DS": 8,
        "RRSIG": 8, "NSEC3": 1, "NSEC3PARAM": 1,
    }


@pytest.mark.parametrize("engine", ["duckdb", "pandas"])
def test_epoch_millisecond_timestamps_are_not_read_as_1970(
    real_schema_parquet, dictionary, engine
):
    """pandas reads bare integers as nanoseconds, mapping everything to 1970.

    That would silently destroy the publication-date cutoff, which is the one
    thing separating "looks like RFC 8078" from "is evidence of RFC 8078".
    """
    frame = read_parquet(real_schema_parquet, dictionary, _NEEDED, engine=engine)
    signals = extract_signals(frame)
    assert len(signals) == len(_REAL_ROWS), "rows were dropped as unparseable"
    assert signals[0].timestamp == datetime(2018, 5, 1)
    assert all(signal.timestamp.year == 2018 for signal in signals)


@pytest.mark.parametrize("engine", ["duckdb", "pandas"])
def test_digest_type_and_key_tag_coalesce_across_ds_and_cds(
    real_schema_parquet, dictionary, engine
):
    frame = read_parquet(real_schema_parquet, dictionary, _NEEDED, engine=engine)
    by_type = {s.fields["rr_type"]: s.fields for s in extract_signals(frame)}
    assert by_type["DS"]["digest_type"] == 2
    assert by_type["DS"]["key_tag"] == 12345
    assert by_type["CDS"]["digest_type"] == 0
    assert by_type["RRSIG"]["key_tag"] == 54321


def test_both_engines_agree_on_the_real_schema(real_schema_parquet, dictionary):
    """A run must not depend on which engine happened to be installed."""
    duck = read_parquet(real_schema_parquet, dictionary, _NEEDED, engine="duckdb")
    pandas_frame = read_parquet(real_schema_parquet, dictionary, _NEEDED, engine="pandas")
    pd.testing.assert_frame_equal(duck, pandas_frame)


def test_missing_measurement_id_reads_as_null_not_an_error(
    real_schema_parquet, dictionary
):
    """The real corpus has no `measurement_id`; that must degrade, not fail."""
    warnings: list[str] = []
    frame = read_parquet(
        real_schema_parquet, dictionary, _NEEDED, engine="duckdb", warnings=warnings
    )
    assert "measurement_id" in frame.columns
    assert frame["measurement_id"].isna().all()
    assert any("measurement_id" in message for message in warnings)


# --------------------------------------------------------------------------- #
# Hive-partitioned layout (how the real corpus is actually addressed)
# --------------------------------------------------------------------------- #


def test_timestamp_is_not_coalesced_with_hive_partition_columns(dictionary):
    """`year`/`month`/`day` must never be fallbacks for `timestamp`.

    DuckDB types Hive path segments by guessing from the literal text: `year`
    binds BIGINT while `month`/`day` bind VARCHAR (leading zeros). Coalescing
    them is a hard Binder Error on real S3 reads -- and semantically wrong, since
    a partition component is not a measurement time.
    """
    entry = dictionary.get("timestamp")
    assert entry is not None
    for partition_column in ("year", "month", "day"):
        assert partition_column not in entry.openintel_native_fields


@pytest.mark.parametrize("engine", ["duckdb", "pandas"])
def test_reading_a_file_inside_a_hive_partition_tree(tmp_path, dictionary, engine):
    """The real layout is fdns/basis=.../source=.../year=.../month=.../day=..."""
    target = (
        tmp_path / "basis=zonefile" / "source=nu" / "year=2018" / "month=05" / "day=01"
        / "part-00000.gz.parquet"
    )
    _write_real_schema_parquet(target)

    frame = read_parquet(target, dictionary, _NEEDED, engine=engine)
    signals = extract_signals(frame)
    assert len(signals) == len(_REAL_ROWS)
    assert signals[0].timestamp == datetime(2018, 5, 1)
