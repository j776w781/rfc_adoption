"""Parquet rows to normalized observed signals.

These are the tests where reading the real sample file is the point: everything
downstream reasons over plain Python values, and the two properties that make
that safe are (a) a missing value stays ``None`` rather than becoming ``0``, and
(b) the DuckDB and pyarrow readers agree exactly.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from openintel_rfc.models import OpenINTELDictionary
from openintel_rfc.parquet_reader import read_parquet, resolve_columns
from openintel_rfc.signal_extractor import (
    MISSING_LABEL,
    NUMERIC_FIELDS,
    SIGNAL_FIELDS,
    extract_signals,
    field_distribution,
    signal_summary,
    signals_to_dataframe,
)
from openintel_rfc.utils import PipelineError

NEEDED_FIELDS = ("rr_type", "algorithm", "digest_type", "key_tag", "flags")


@pytest.fixture(scope="module")
def sample_frame(sample_parquet_path: Path, dictionary: OpenINTELDictionary) -> pd.DataFrame:
    return read_parquet(sample_parquet_path, dictionary, NEEDED_FIELDS, engine="auto")


@pytest.fixture(scope="module")
def sample_signals(sample_frame: pd.DataFrame):
    return extract_signals(sample_frame, origin_file="sample_openintel.parquet")


# --------------------------------------------------------------------------- #
# Extraction from the real fixture
# --------------------------------------------------------------------------- #


def test_sample_parquet_rows_become_normalized_observed_signals(sample_signals) -> None:
    assert len(sample_signals) > 0

    first = sample_signals[0]
    assert first.signal_id == "sig_0001"
    assert isinstance(first.timestamp, datetime)
    assert first.origin_file == "sample_openintel.parquet"
    # Every canonical field is a key, so no consumer needs a KeyError guard.
    assert set(SIGNAL_FIELDS).issubset(first.fields)


def test_signal_ids_run_without_gaps_in_frame_order(sample_signals) -> None:
    ids = [signal.signal_id for signal in sample_signals]
    assert ids == [f"sig_{index:04d}" for index in range(1, len(sample_signals) + 1)]

    timestamps = [signal.timestamp for signal in sample_signals]
    assert timestamps == sorted(timestamps), "the fixture is written chronologically"


def test_record_types_are_upper_cased_and_numeric_fields_are_integers(sample_signals) -> None:
    for signal in sample_signals:
        rr_type = signal.value("rr_type")
        assert rr_type is not None and rr_type == rr_type.upper()
        for field in NUMERIC_FIELDS:
            value = signal.value(field)
            assert value is None or isinstance(value, int)
            assert not isinstance(value, bool)


def test_algorithm_zero_is_distinguishable_from_a_missing_algorithm(sample_signals) -> None:
    """The RFC 8078 delete signal is algorithm 0; absence must not look the same."""
    delete_signals = [
        s for s in sample_signals if s.value("rr_type") == "CDS" and s.value("algorithm") == 0
    ]
    unset = [
        s for s in sample_signals if s.value("rr_type") == "CDS" and s.value("algorithm") is None
    ]

    assert delete_signals, "the fixture must contain CDS delete signals"
    assert unset, "the fixture must contain a CDS row with no algorithm"
    for signal in delete_signals:
        assert signal.has_value("algorithm") is True
    for signal in unset:
        assert signal.has_value("algorithm") is False


def test_flags_are_absent_before_the_dictionary_availability_date(sample_signals) -> None:
    for signal in sample_signals:
        if signal.timestamp < datetime(2016, 1, 1):
            assert signal.value("flags") is None


def test_duckdb_and_pandas_engines_produce_identical_signals(
    sample_parquet_path: Path, dictionary: OpenINTELDictionary
) -> None:
    duckdb_frame = read_parquet(sample_parquet_path, dictionary, NEEDED_FIELDS, engine="duckdb")
    pandas_frame = read_parquet(sample_parquet_path, dictionary, NEEDED_FIELDS, engine="pandas")

    assert list(duckdb_frame.columns) == list(pandas_frame.columns)
    assert duckdb_frame.dtypes.astype(str).to_dict() == pandas_frame.dtypes.astype(str).to_dict()

    from_duckdb = extract_signals(duckdb_frame, origin_file="sample_openintel.parquet")
    from_pandas = extract_signals(pandas_frame, origin_file="sample_openintel.parquet")

    assert [s.model_dump() for s in from_duckdb] == [s.model_dump() for s in from_pandas]


def test_row_limit_is_honoured_by_both_engines(
    sample_parquet_path: Path, dictionary: OpenINTELDictionary
) -> None:
    for engine in ("duckdb", "pandas"):
        frame = read_parquet(
            sample_parquet_path, dictionary, NEEDED_FIELDS, engine=engine, limit=5
        )
        assert len(frame) == 5


def test_resolve_columns_maps_normalized_names_onto_native_openintel_columns(
    dictionary: OpenINTELDictionary,
) -> None:
    mapping = resolve_columns(
        dictionary,
        ["rr_type", "algorithm", "digest_type", "nonexistent_field"],
        ["response_type", "cds_algorithm", "ds_digest_type"],
    )

    assert mapping["rr_type"] == "response_type"
    assert mapping["algorithm"] == "cds_algorithm"
    assert mapping["digest_type"] == "ds_digest_type"
    assert mapping["nonexistent_field"] is None


def test_unresolvable_field_becomes_an_all_null_column_with_a_warning(
    sample_parquet_path: Path, dictionary: OpenINTELDictionary
) -> None:
    warnings: list[str] = []

    frame = read_parquet(
        sample_parquet_path,
        dictionary,
        ["rr_type", "dnssec_ok_flag"],
        engine="auto",
        warnings=warnings,
    )

    assert "dnssec_ok_flag" in frame.columns
    assert frame["dnssec_ok_flag"].isna().all()
    assert any("dnssec_ok_flag" in message for message in warnings)


# --------------------------------------------------------------------------- #
# Value normalization on hand-built frames
# --------------------------------------------------------------------------- #


def test_extract_signals_requires_a_timestamp_column() -> None:
    frame = pd.DataFrame({"rr_type": ["CDS"]})

    with pytest.raises(PipelineError, match="requires a 'timestamp' column"):
        extract_signals(frame)


def test_extract_signals_rejects_a_non_dataframe() -> None:
    with pytest.raises(PipelineError, match="expects a pandas DataFrame"):
        extract_signals([{"timestamp": "2018-05-01"}])  # type: ignore[arg-type]


def test_rows_with_an_unusable_timestamp_are_skipped_with_a_warning() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": ["2018-05-01", None, "2019-01-01"],
            "rr_type": ["CDS", "CDS", "CDS"],
        }
    )
    warnings: list[str] = []

    signals = extract_signals(frame, warnings=warnings)

    assert [s.signal_id for s in signals] == ["sig_0001", "sig_0002"]
    assert [s.row_index for s in signals] == [0, 2], "original row positions survive"
    assert any("unusable timestamp" in message for message in warnings)


def test_extra_columns_are_carried_into_fields() -> None:
    frame = pd.DataFrame({"timestamp": ["2020-01-01"], "dnssec_ok_flag": ["true"]})

    signals = extract_signals(frame)

    assert signals[0].value("dnssec_ok_flag") == "true"
    assert signals[0].value("algorithm") is None


def test_empty_text_and_nan_both_normalize_to_none() -> None:
    frame = pd.DataFrame(
        {"timestamp": ["2020-01-01"], "rr_type": ["   "], "algorithm": [float("nan")]}
    )

    signals = extract_signals(frame)

    assert signals[0].value("rr_type") is None
    assert signals[0].value("algorithm") is None


def test_integral_floats_are_narrowed_back_to_int() -> None:
    frame = pd.DataFrame({"timestamp": ["2020-01-01"], "algorithm": [13.0]})

    signals = extract_signals(frame)

    assert signals[0].value("algorithm") == 13
    assert isinstance(signals[0].value("algorithm"), int)


def test_a_non_numeric_algorithm_is_kept_verbatim_with_a_warning() -> None:
    frame = pd.DataFrame({"timestamp": ["2020-01-01"], "algorithm": ["ECDSA"]})
    warnings: list[str] = []

    signals = extract_signals(frame, warnings=warnings)

    assert signals[0].value("algorithm") == "ECDSA"
    assert any("non-numeric value" in message for message in warnings)


# --------------------------------------------------------------------------- #
# Tabular and summary views
# --------------------------------------------------------------------------- #


def test_signals_to_dataframe_keeps_nullable_integer_columns(sample_signals) -> None:
    frame = signals_to_dataframe(sample_signals)

    assert len(frame) == len(sample_signals)
    assert list(frame.columns)[:6] == [
        "signal_id",
        "timestamp",
        "domain",
        "zone",
        "source",
        "measurement_id",
    ]
    for column in NUMERIC_FIELDS:
        assert str(frame[column].dtype) == "Int64"
    assert str(frame["timestamp"].dtype) == "datetime64[ns]"


def test_signals_to_dataframe_handles_no_signals() -> None:
    frame = signals_to_dataframe([])

    assert frame.empty
    assert "signal_id" in frame.columns and "rr_type" in frame.columns


def test_field_distribution_reports_missing_values_under_an_explicit_label(
    sample_signals,
) -> None:
    distribution = field_distribution(sample_signals, "digest_type")

    assert MISSING_LABEL in distribution
    assert sum(distribution.values()) == len(sample_signals)
    numeric_labels = [label for label in distribution if label != MISSING_LABEL]
    assert numeric_labels == sorted(numeric_labels, key=float), "numeric order, not text order"


def test_signal_summary_reports_coverage(sample_signals) -> None:
    summary = signal_summary(sample_signals)

    assert summary["signal_count"] == len(sample_signals)
    assert summary["distinct_domains"] > 1
    assert summary["first_timestamp"] <= summary["last_timestamp"]
    for field in SIGNAL_FIELDS:
        present = summary["present_value_counts"][field]
        missing = summary["missing_value_counts"][field]
        assert present + missing == len(sample_signals)
