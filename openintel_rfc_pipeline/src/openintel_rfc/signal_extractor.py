"""Turning a normalized Parquet frame into :class:`ObservedSignal` records.

:mod:`openintel_rfc.parquet_reader` produces a DataFrame with normalized column
names; this module converts each row into the typed observation the matcher
consumes. The split matters because everything after this point reasons over
plain Python values only -- no ``NaN``, no numpy scalars, no pandas extension
types -- which is what makes the reasoning traces and the JSON output stable.

Two conventions are worth stating explicitly:

* Provenance (``timestamp``, ``domain``, ``zone``, ``source``,
  ``measurement_id``) lives on the signal itself. The ``fields`` mapping carries
  only the DNS/DNSSEC attributes that indicators test, so a condition over
  ``fields`` can never accidentally match a provenance column.
* ``None`` means "not observed". Missing values are never replaced by a default
  such as ``0`` or ``""``, because absence of evidence is not evidence: the
  matcher has to be able to tell "this record has algorithm 0" (the RFC 8078
  delete signal) apart from "this record has no algorithm at all".

Rows whose timestamp cannot be parsed are skipped rather than guessed at, each
with a warning naming the row. Skipping silently would understate coverage;
crashing would throw away a whole run because of one bad row.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd

from .models import ObservedSignal
from .utils import (
    PipelineError,
    format_value,
    get_logger,
    iso,
    parse_timestamp,
    signal_id,
    unique_sorted,
    warn,
)

__all__ = [
    "SIGNAL_FIELDS",
    "PROVENANCE_FIELDS",
    "NUMERIC_FIELDS",
    "MISSING_LABEL",
    "extract_signals",
    "signals_to_dataframe",
    "field_distribution",
    "signal_summary",
]

LOGGER = get_logger(__name__)

#: Normalized DNS/DNSSEC attributes carried in ``ObservedSignal.fields``.
#: Always present as keys, with ``None`` where the column was absent or null.
SIGNAL_FIELDS: tuple[str, ...] = (
    "rr_type",
    "algorithm",
    "digest_type",
    "key_tag",
    "flags",
)

#: Columns promoted to top-level attributes of :class:`ObservedSignal`.
PROVENANCE_FIELDS: tuple[str, ...] = (
    "timestamp",
    "domain",
    "zone",
    "source",
    "measurement_id",
)

#: Signal fields parsed as numbers.
NUMERIC_FIELDS: tuple[str, ...] = ("algorithm", "digest_type", "key_tag")

#: Label used for ``None`` in distribution maps (matches ``utils.format_value``).
MISSING_LABEL = "<missing>"

#: Frame columns that are provenance/bookkeeping rather than observable fields.
_RESERVED_COLUMNS = frozenset(PROVENANCE_FIELDS) | {"origin_file", "row_index"}


# --------------------------------------------------------------------------- #
# Value normalization
# --------------------------------------------------------------------------- #


def _is_missing(value: Any) -> bool:
    """True for ``None``/``NaN``/``NaT``/``pd.NA``; False for real values."""
    if value is None:
        return True
    if isinstance(value, str):
        return False
    try:
        flag = pd.isna(value)
    except (TypeError, ValueError):  # unhashable / array-like oddities
        return False
    if isinstance(flag, bool):
        return flag
    if hasattr(flag, "__len__"):  # array-like: a container is not "missing"
        return False
    return bool(flag)


def _clean_string(value: Any) -> str | None:
    """Strip a text value; empty text is treated as absent."""
    if _is_missing(value):
        return None
    text = str(value).strip()
    return text or None


def _clean_number(
    field: str, value: Any, row_label: str, warnings: list[str]
) -> int | float | str | None:
    """Normalize a numeric field to ``int`` when the value is integral.

    Parquet round-trips and DuckDB's nullable-integer handling both tend to turn
    a nullable integer column into floats, so ``algorithm`` can arrive as
    ``13.0``. Anything integral is narrowed back to ``int`` here; genuinely
    fractional values are kept as floats, and values that are not numbers at all
    are kept verbatim with a warning rather than being discarded.
    """
    if _is_missing(value):
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return int(value) if value.is_integer() else float(value)
    if hasattr(value, "item"):  # numpy / pandas scalar
        try:
            return _clean_number(field, value.item(), row_label, warnings)
        except (AttributeError, ValueError):  # pragma: no cover - defensive
            pass

    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        warn(
            warnings,
            f"{row_label}: field '{field}' has non-numeric value {text!r}; "
            "kept as text so the mismatch stays visible.",
            LOGGER,
        )
        return text
    return int(number) if number.is_integer() else number


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #


def extract_signals(
    df: pd.DataFrame,
    *,
    origin_file: str | None = None,
    warnings: list[str] | None = None,
) -> list[ObservedSignal]:
    """Convert a normalized frame into :class:`ObservedSignal` records.

    ``df`` is expected to come from :func:`parquet_reader.read_parquet`, i.e. to
    use normalized column names. Only ``timestamp`` is mandatory; every other
    column is optional and its absence simply yields ``None`` values.

    Signal ids are minted with :func:`utils.signal_id` over the *emitted*
    signals, so they run ``sig_0001``, ``sig_0002``, ... with no gaps even when
    rows are skipped. The original position in the frame is preserved separately
    in ``row_index``, which is what to use when going back to the source data.

    ``origin_file`` records which file the rows came from. A per-row
    ``origin_file`` column (as produced by :func:`parquet_reader.read_many`)
    takes precedence over the argument.
    """
    collected = warnings if warnings is not None else []

    if not isinstance(df, pd.DataFrame):
        raise PipelineError(
            f"extract_signals expects a pandas DataFrame, got {type(df).__name__}."
        )
    if "timestamp" not in df.columns:
        raise PipelineError(
            "extract_signals requires a 'timestamp' column; got columns: "
            + (", ".join(str(c) for c in df.columns) or "<none>")
        )

    columns = [str(column) for column in df.columns]
    extra_fields = sorted(
        column
        for column in columns
        if column not in _RESERVED_COLUMNS and column not in SIGNAL_FIELDS
    )
    index_labels = list(df.index)

    signals: list[ObservedSignal] = []
    for position, values in enumerate(df.itertuples(index=False, name=None)):
        row = dict(zip(columns, values))
        row_index = _row_index_for(index_labels, position)
        row_label = f"row {row_index}"

        timestamp_value = row.get("timestamp")
        try:
            if _is_missing(timestamp_value):
                raise PipelineError("timestamp is null")
            timestamp = parse_timestamp(timestamp_value)
        except (PipelineError, ValueError, TypeError, OverflowError) as exc:
            warn(
                collected,
                f"{row_label}: skipped, unusable timestamp "
                f"({format_value(timestamp_value)}): {exc}",
                LOGGER,
            )
            continue

        fields: dict[str, Any] = {}
        for field in SIGNAL_FIELDS:
            raw = row.get(field)
            if field in NUMERIC_FIELDS:
                fields[field] = _clean_number(field, raw, row_label, collected)
            else:
                cleaned = _clean_string(raw)
                # Record types are case-insensitive in DNS; the checklists spell
                # them upper-case, so normalize here rather than in every
                # condition evaluation.
                fields[field] = (
                    cleaned.upper() if cleaned is not None and field == "rr_type" else cleaned
                )
        for field in extra_fields:
            fields[field] = _clean_string(row.get(field))

        row_origin = _clean_string(row.get("origin_file")) or origin_file

        signals.append(
            ObservedSignal(
                signal_id=signal_id(len(signals) + 1),
                source=_clean_string(row.get("source")) or "openintel_parquet",
                timestamp=timestamp,
                domain=_clean_string(row.get("domain")),
                zone=_clean_string(row.get("zone")),
                measurement_id=_clean_string(row.get("measurement_id")),
                fields=fields,
                row_index=row_index,
                origin_file=row_origin,
            )
        )

    if not signals and len(df):
        warn(
            collected,
            f"No usable signals were extracted from {len(df)} row(s); "
            "every row had an unusable timestamp.",
            LOGGER,
        )
    return signals


def _row_index_for(index_labels: list[Any], position: int) -> int:
    """Prefer the frame's own integer index label, else the positional offset."""
    if position < len(index_labels):
        label = index_labels[position]
        if pd.api.types.is_integer(label):
            return int(label)
    return position


# --------------------------------------------------------------------------- #
# Tabular and summary views
# --------------------------------------------------------------------------- #


def _as_nullable_int(series: pd.Series) -> pd.Series:
    """Present an integer-valued column as nullable ``Int64``.

    Without this, a column holding ``[1, None]`` widens to ``float64`` and every
    algorithm number is exported as ``1.0``. Columns carrying anything that is
    not a whole number are returned untouched, because a non-numeric algorithm
    is a finding worth seeing rather than something to coerce away.
    """
    numeric = pd.to_numeric(series, errors="coerce")
    if bool((numeric.isna() & series.notna()).any()):
        return series
    present = numeric.dropna()
    if len(present) and not bool((present % 1 == 0).all()):
        return series
    return numeric.astype("Int64")


def signals_to_dataframe(signals: Sequence[ObservedSignal]) -> pd.DataFrame:
    """Flatten signals back into a table, for CSV export and the dashboard.

    Column order is fixed: identity, provenance, the canonical signal fields,
    then any extra observed fields in sorted order. The frame is always
    well-formed, even for an empty input, so callers can write a CSV header
    without special-casing "no signals".
    """
    extra_fields = sorted(
        {
            field
            for signal in signals
            for field in signal.fields
            if field not in SIGNAL_FIELDS
        }
    )
    columns = [
        "signal_id",
        "timestamp",
        "domain",
        "zone",
        "source",
        "measurement_id",
        *SIGNAL_FIELDS,
        *extra_fields,
        "row_index",
        "origin_file",
    ]

    records: list[dict[str, Any]] = []
    for signal in signals:
        record: dict[str, Any] = {
            "signal_id": signal.signal_id,
            "timestamp": signal.timestamp,
            "domain": signal.domain,
            "zone": signal.zone,
            "source": signal.source,
            "measurement_id": signal.measurement_id,
            "row_index": signal.row_index,
            "origin_file": signal.origin_file,
        }
        for field in (*SIGNAL_FIELDS, *extra_fields):
            record[field] = signal.fields.get(field)
        records.append(record)

    frame = pd.DataFrame(records, columns=columns)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"]).astype("datetime64[ns]")
    for column in (*NUMERIC_FIELDS, "row_index"):
        frame[column] = _as_nullable_int(frame[column])
    return frame


def _distribution_sort_key(label: str) -> tuple[int, float, str]:
    """Numeric labels first in numeric order, then text, then ``<missing>``.

    Sorting the rendered labels as plain strings would put algorithm 13 before
    algorithm 8, which reads as a bug in every report it appears in.
    """
    if label == MISSING_LABEL:
        return (2, 0.0, "")
    try:
        return (0, float(label), label)
    except ValueError:
        return (1, 0.0, label)


def _value_of(signal: ObservedSignal, field: str) -> Any:
    """Read ``field`` from the signal, whether it is provenance or observed."""
    if field in PROVENANCE_FIELDS or field in ("signal_id", "origin_file", "row_index"):
        return getattr(signal, field, None)
    return signal.fields.get(field)


def field_distribution(signals: Sequence[ObservedSignal], field: str) -> dict[str, int]:
    """Count how often each value of ``field`` occurs, in deterministic order.

    ``None`` is reported under the literal key ``"<missing>"`` rather than
    dropped: how much of the corpus cannot answer a question is itself a
    finding, and hiding it would flatter the coverage numbers.
    """
    counts: dict[str, int] = {}
    for signal in signals:
        label = format_value(_value_of(signal, field))
        counts[label] = counts.get(label, 0) + 1
    return {label: counts[label] for label in sorted(counts, key=_distribution_sort_key)}


def signal_summary(signals: Sequence[ObservedSignal]) -> dict[str, Any]:
    """Aggregate coverage statistics for a set of signals.

    Reported into the run manifest and the report, so that a reader can judge
    what the corpus could possibly have shown before reading what it did show.
    """
    timestamps = [signal.timestamp for signal in signals]
    domains = unique_sorted(signal.domain for signal in signals)
    zones = unique_sorted(signal.zone for signal in signals)

    observed_fields = unique_sorted(
        {field for signal in signals for field in signal.fields} | set(SIGNAL_FIELDS)
    )

    return {
        "signal_count": len(signals),
        "first_timestamp": iso(min(timestamps)) if timestamps else None,
        "last_timestamp": iso(max(timestamps)) if timestamps else None,
        "distinct_domains": len(domains),
        "distinct_zones": len(zones),
        "domains": domains,
        "zones": zones,
        "sources": unique_sorted(signal.source for signal in signals),
        "origin_files": unique_sorted(signal.origin_file for signal in signals),
        "field_distributions": {
            field: field_distribution(signals, field) for field in observed_fields
        },
        "present_value_counts": {
            field: sum(1 for signal in signals if signal.has_value(field))
            for field in observed_fields
        },
        "missing_value_counts": {
            field: sum(1 for signal in signals if not signal.has_value(field))
            for field in observed_fields
        },
    }
