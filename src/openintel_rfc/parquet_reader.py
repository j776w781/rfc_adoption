"""Reading OpenINTEL-style Parquet files into normalized analysis frames.

OpenINTEL exports one column per record-type-specific attribute
(``cds_algorithm``, ``dnskey_algorithm``, ``ds_digest_type``, ...) while the
matcher reasons over a small set of *normalized* analysis fields (``rr_type``,
``algorithm``, ``digest_type``, ...). This module is the only place where that
translation happens: everything downstream sees normalized column names and
never has to know which OpenINTEL measurement generation produced a file.

Two engines are supported:

``duckdb``
    Preferred. The projection is pushed into the scan --
    ``SELECT "cds_algorithm" AS "algorithm" FROM read_parquet('...')`` -- so
    only the requested columns are read off disk, and ``limit`` becomes a SQL
    ``LIMIT``. ``SELECT *`` is never issued: OpenINTEL files are wide and a
    full scan is the difference between seconds and minutes.
``pandas``
    Fallback through pyarrow, used when DuckDB is not installed. Column
    projection is still pushed into pyarrow and ``limit`` is honoured by
    reading only as many record batches as are actually needed.

Whichever engine runs, the resulting frame is normalized to the same dtypes
(``datetime64[ns]`` for timestamps, nullable ``Int64`` for integer fields,
``object`` holding ``None`` for everything else). A run must be reproducible
regardless of which engine happened to be available on the machine, so the two
readers are required to produce identical frames.

Fields that cannot be resolved are still emitted, as all-``None`` columns, and
each one produces a warning. Downstream code therefore never has to guard
against a missing key, and the fact that the data could not answer the question
stays visible in the output instead of being silently dropped.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from . import config
from .models import OpenINTELDictionary
from .utils import PipelineError, get_logger, warn

__all__ = [
    "ENGINES",
    "describe_parquet",
    "resolve_columns",
    "resolve_column_candidates",
    "read_parquet",
    "read_many",
]

LOGGER = get_logger(__name__)

#: Accepted values for the ``engine`` argument.
ENGINES: tuple[str, ...] = ("auto", "duckdb", "pandas")

#: Rows per record batch when the pyarrow fallback has to honour a ``limit``.
_READ_BATCH_ROWS = 65_536

#: Dictionary ``type`` values that are coerced to nullable integers.
_INTEGER_TYPES = frozenset({"integer", "int", "int32", "int64", "long"})

#: Dictionary ``type`` values that are coerced to naive-UTC datetimes.
_DATETIME_TYPES = frozenset({"datetime", "timestamp", "date"})


# --------------------------------------------------------------------------- #
# Small internal helpers
# --------------------------------------------------------------------------- #


def _require_file(path: str | Path) -> Path:
    """Return ``path`` as a :class:`Path`, raising if it is not a readable file."""
    file_path = Path(path)
    if not file_path.is_file():
        raise PipelineError(f"Parquet file not found: {file_path}")
    return file_path


def _quote_identifier(name: str) -> str:
    """Quote a SQL identifier, doubling any embedded double quote."""
    return '"' + str(name).replace('"', '""') + '"'


def _quote_path_literal(path: Path) -> str:
    """Quote a filesystem path as a SQL string literal.

    A single quote in the path would let the path terminate the literal early,
    so such paths are rejected outright rather than escaped: they are
    vanishingly rare in measurement corpora and silently mangling one would be
    worse than refusing it.
    """
    text = path.as_posix()
    if "'" in text:
        raise PipelineError(
            f"Refusing to build SQL for a path containing a single quote: {text}. "
            "Move or rename the file, or use engine='pandas'."
        )
    return f"'{text}'"


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


def _selection_fields(
    dictionary: OpenINTELDictionary, needed_fields: Sequence[str]
) -> list[str]:
    """Union the requested fields with ``config.ALWAYS_SELECT_FIELDS``.

    The result is ordered by the dictionary's own field order (so frames read
    with the same dictionary always have the same column order) followed by any
    remaining names sorted alphabetically.
    """
    wanted = {
        str(name)
        for name in (*needed_fields, *config.ALWAYS_SELECT_FIELDS)
        if name is not None and str(name) != ""
    }
    in_dictionary = [name for name in dictionary.field_names if name in wanted]
    extras = sorted(wanted.difference(in_dictionary))
    return in_dictionary + extras


# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #


def describe_parquet(path: Path) -> dict[str, Any]:
    """Describe a Parquet file from its footer alone.

    No column data is read: the row count and schema come from the file
    metadata, which is what makes this cheap enough to call before deciding
    which columns to project.

    Returns a dict with ``path``, ``row_count``, ``columns`` (a list of
    ``{"name", "type"}`` in file order) and ``engine`` (the library that
    produced the description).
    """
    file_path = _require_file(path)
    try:
        import pyarrow.parquet as pq
    except ImportError:  # pragma: no cover - pyarrow is a hard requirement
        return _describe_with_duckdb(file_path)

    try:
        parquet_file = pq.ParquetFile(file_path)
        schema = parquet_file.schema_arrow
        row_count = int(parquet_file.metadata.num_rows)
    except Exception as exc:  # pyarrow raises a family of ArrowInvalid subclasses
        raise PipelineError(f"Cannot read Parquet metadata from {file_path}: {exc}") from exc

    return {
        "path": file_path.as_posix(),
        "row_count": row_count,
        "columns": [{"name": field.name, "type": str(field.type)} for field in schema],
        "engine": "pyarrow",
    }


def _describe_with_duckdb(file_path: Path) -> dict[str, Any]:
    """Metadata fallback for environments without pyarrow."""
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - one of the two must exist
        raise PipelineError(
            "Neither pyarrow nor duckdb is installed; cannot inspect Parquet files."
        ) from exc

    literal = _quote_path_literal(file_path)
    connection = duckdb.connect(database=":memory:")
    try:
        described = connection.execute(
            f"DESCRIBE SELECT * FROM read_parquet({literal})"
        ).fetchall()
        row_count = connection.execute(
            f"SELECT count(*) FROM read_parquet({literal})"
        ).fetchone()
    except Exception as exc:
        raise PipelineError(f"Cannot read Parquet metadata from {file_path}: {exc}") from exc
    finally:
        connection.close()

    return {
        "path": file_path.as_posix(),
        "row_count": int(row_count[0]) if row_count else 0,
        "columns": [{"name": str(row[0]), "type": str(row[1])} for row in described],
        "engine": "duckdb",
    }


# --------------------------------------------------------------------------- #
# Column resolution
# --------------------------------------------------------------------------- #


def resolve_columns(
    dictionary: OpenINTELDictionary,
    needed_fields: Sequence[str],
    parquet_columns: Sequence[str],
) -> dict[str, str | None]:
    """Map normalized analysis field names onto real Parquet column names.

    Resolution is attempted in this fixed order, so the answer never depends on
    dict iteration order or on which alias happens to be listed first in a
    different dictionary version:

    1. an exact match on the normalized field name;
    2. each entry of the dictionary field's ``openintel_native_fields``, in the
       order the dictionary lists them;
    3. a case-insensitive match on the normalized field name.

    Fields that resolve to nothing map to ``None``. Two normalized fields may
    legitimately resolve to the same Parquet column (the dictionary derives both
    ``zone`` and ``source`` from OpenINTEL's ``source``), so the mapping is not
    required to be injective.
    """
    actual_columns = [str(name) for name in parquet_columns]
    exact = set(actual_columns)

    # First occurrence wins, which keeps the answer stable when a file contains
    # both "Timestamp" and "TIMESTAMP".
    case_insensitive: dict[str, str] = {}
    for name in actual_columns:
        case_insensitive.setdefault(name.lower(), name)

    resolved: dict[str, str | None] = {}
    for field in needed_fields:
        name = str(field)
        if name in resolved:  # stable de-duplication
            continue
        resolved[name] = _resolve_one(dictionary, name, exact, case_insensitive)
    return resolved


def _resolve_one(
    dictionary: OpenINTELDictionary,
    field: str,
    exact: set[str],
    case_insensitive: dict[str, str],
) -> str | None:
    candidates = _resolve_all(dictionary, field, exact, case_insensitive)
    return candidates[0] if candidates else None


def _resolve_all(
    dictionary: OpenINTELDictionary,
    field: str,
    exact: set[str],
    case_insensitive: dict[str, str],
) -> list[str]:
    """Every column that could supply ``field``, in priority order."""
    found: list[str] = []

    def add(name: str) -> None:
        if name not in found:
            found.append(name)

    if field in exact:
        add(field)

    entry = dictionary.get(field)
    if entry is not None:
        for native in entry.openintel_native_fields:
            if native in exact:
                add(native)

    fallback = case_insensitive.get(field.lower())
    if fallback is not None:
        add(fallback)

    return found


def resolve_column_candidates(
    dictionary: OpenINTELDictionary,
    needed_fields: Sequence[str],
    parquet_columns: Sequence[str],
) -> dict[str, list[str]]:
    """Map each normalized field onto *every* column that could supply it.

    This is what real OpenINTEL data requires and what
    :func:`resolve_columns` cannot express. OpenINTEL does not carry one
    ``algorithm`` column: it carries ``dnskey_algorithm``, ``ds_algorithm``,
    ``rrsig_algorithm``, ``cds_algorithm``, ``cdnskey_algorithm`` and
    ``nsec3param_hash_algorithm`` as separate columns, and populates only the
    one matching each row's ``response_type``. Binding ``algorithm`` to the
    first of those that exists would read NULL for every row of every other
    record type -- so a CDS delete signal, the strongest RFC 8078 evidence
    there is, would silently never match.

    The reader therefore COALESCEs the candidates in priority order. The
    columns are mutually exclusive per row in practice, so coalescing is
    well-defined rather than a guess between competing values.
    """
    actual_columns = [str(name) for name in parquet_columns]
    exact = set(actual_columns)

    case_insensitive: dict[str, str] = {}
    for name in actual_columns:
        case_insensitive.setdefault(name.lower(), name)

    resolved: dict[str, list[str]] = {}
    for field in needed_fields:
        name = str(field)
        if name in resolved:
            continue
        resolved[name] = _resolve_all(dictionary, name, exact, case_insensitive)
    return resolved


# --------------------------------------------------------------------------- #
# Reading
# --------------------------------------------------------------------------- #


def read_parquet(
    path: Path,
    dictionary: OpenINTELDictionary,
    needed_fields: Sequence[str],
    *,
    engine: str = "auto",
    limit: int | None = None,
    warnings: list[str] | None = None,
) -> pd.DataFrame:
    """Read a Parquet file into a frame whose columns are normalized names.

    ``needed_fields`` is the set of fields the caller actually intends to reason
    about -- in practice the fields used by queryable indicators. It is always
    unioned with :data:`config.ALWAYS_SELECT_FIELDS`, because provenance columns
    (timestamp, domain, zone, source, measurement id) are needed for every run
    whether or not an indicator mentions them.

    Every requested field appears as a column. Fields that could not be resolved
    against the file's schema are emitted as all-``None`` columns and warned
    about, so downstream code can treat "the file does not carry this" and "the
    record did not set this" uniformly, without ``KeyError`` guards.

    ``timestamp`` is coerced to ``datetime64[ns]`` holding naive UTC values;
    integer dictionary fields become nullable ``Int64``; everything else becomes
    ``object`` with ``None`` for nulls.
    """
    collected = warnings if warnings is not None else []
    file_path = _require_file(path)

    if engine not in ENGINES:
        raise PipelineError(
            f"Unknown engine {engine!r}; expected one of {', '.join(ENGINES)}."
        )
    if limit is not None and limit < 0:
        raise PipelineError(f"limit must be >= 0, got {limit}.")

    fields = _selection_fields(dictionary, needed_fields)
    description = describe_parquet(file_path)
    candidates = resolve_column_candidates(
        dictionary, fields, [column["name"] for column in description["columns"]]
    )
    # First-candidate view, kept for the normalizer and for warning messages.
    mapping = {field: (cols[0] if cols else None) for field, cols in candidates.items()}

    for field, cols in candidates.items():
        if not cols:
            warn(
                collected,
                f"Field '{field}' has no matching column in {file_path.name}; "
                "it will be read as all-null.",
                LOGGER,
            )
        elif len(cols) > 1:
            # Not a problem -- it is the normal shape of OpenINTEL data -- but
            # worth stating, because it tells the reader which record types can
            # contribute to this field.
            LOGGER.info(
                "Field '%s' coalesces %d columns in %s: %s",
                field,
                len(cols),
                file_path.name,
                ", ".join(cols),
            )

    if all(not cols for cols in candidates.values()):
        raise PipelineError(
            f"None of the requested fields could be resolved against {file_path}. "
            f"Requested: {', '.join(fields)}. "
            f"File columns: {', '.join(c['name'] for c in description['columns'])}."
        )

    frame: pd.DataFrame | None = None
    if engine in ("auto", "duckdb"):
        try:
            frame = _read_with_duckdb(file_path, candidates, dictionary, limit)
        except PipelineError as exc:
            if engine == "duckdb":
                raise
            warn(
                collected,
                f"Could not read {file_path.name} with DuckDB ({exc}); "
                "falling back to the pandas/pyarrow reader.",
                LOGGER,
            )

    if frame is None:
        frame = _read_with_pandas(file_path, candidates, limit)

    return _normalize_frame(frame, dictionary, mapping, collected)


#: DuckDB type each dictionary type is coerced to before coalescing. Candidate
#: columns for one normalized field can legitimately differ in physical type
#: across OpenINTEL measurement generations, and a bare COALESCE over mixed
#: types is a hard error. TRY_CAST yields NULL instead of failing the scan.
_DUCKDB_CAST_TYPES: dict[str, str] = {
    "integer": "BIGINT",
    "int": "BIGINT",
    "long": "BIGINT",
    "bigint": "BIGINT",
    "float": "DOUBLE",
    "double": "DOUBLE",
    "number": "DOUBLE",
    "string": "VARCHAR",
    "str": "VARCHAR",
    "text": "VARCHAR",
    "boolean": "BOOLEAN",
    "bool": "BOOLEAN",
    # Datetime fields are deliberately absent. OpenINTEL stores `timestamp` as
    # epoch milliseconds, and TRY_CAST(1525000000000 AS TIMESTAMP) is NULL, which
    # would drop every row. The raw value is passed through and the unit is
    # detected in `_coerce_epoch_integers`, so both engines agree.
}


def _duckdb_expression(
    field: str, columns: Sequence[str], dictionary: OpenINTELDictionary
) -> str:
    """SQL expression selecting ``field`` from one or more candidate columns."""
    entry = dictionary.get(field)
    declared = (entry.type if entry else "").strip().lower()
    cast_type = _DUCKDB_CAST_TYPES.get(declared)

    def term(column: str) -> str:
        quoted = _quote_identifier(column)
        return f"TRY_CAST({quoted} AS {cast_type})" if cast_type else quoted

    # Datetime fields are never coalesced. They carry no TRY_CAST (OpenINTEL
    # stores epoch milliseconds, which TRY_CAST to TIMESTAMP would null out), so
    # a multi-candidate COALESCE would mix raw physical types and fail to bind.
    # It is also meaningless: nothing is a legitimate "fallback" for a
    # measurement time. Reading real S3 partitions is where this bites -- DuckDB
    # exposes the Hive path columns year/month/day, typing year BIGINT and
    # month/day VARCHAR, and COALESCE over those is a hard Binder Error.
    if declared in _DATETIME_TYPES or field == "timestamp":
        if len(columns) > 1:
            LOGGER.warning(
                "Field '%s' is a datetime with %d candidate columns (%s); using "
                "'%s' only. Datetime fields are never coalesced -- fix the "
                "dictionary's openintel_native_fields if this is not the right "
                "column.",
                field,
                len(columns),
                ", ".join(columns),
                columns[0],
            )
        return term(columns[0])

    if len(columns) == 1:
        return term(columns[0])
    # Candidates are mutually exclusive per row in OpenINTEL (a row is one
    # record type), so the first non-null is the value for that row.
    return "COALESCE(" + ", ".join(term(c) for c in columns) + ")"


def _read_with_duckdb(
    file_path: Path,
    candidates: dict[str, list[str]],
    dictionary: OpenINTELDictionary,
    limit: int | None,
) -> pd.DataFrame:
    """Project the needed columns out of the file with DuckDB.

    DuckDB is imported lazily so that the package still imports on machines
    where only pyarrow is installed.
    """
    try:
        import duckdb
    except ImportError as exc:
        raise PipelineError("DuckDB is not installed.") from exc

    projection = ", ".join(
        f"{_duckdb_expression(field, cols, dictionary)} AS {_quote_identifier(field)}"
        for field, cols in candidates.items()
        if cols
    )
    statement = (
        f"SELECT {projection} FROM read_parquet({_quote_path_literal(file_path)})"
    )
    if limit is not None:
        statement += f" LIMIT {int(limit)}"

    connection = duckdb.connect(database=":memory:")
    try:
        return connection.execute(statement).df()
    except Exception as exc:  # duckdb raises its own error hierarchy
        raise PipelineError(f"DuckDB failed on {file_path}: {exc}") from exc
    finally:
        connection.close()


def _read_with_pandas(
    file_path: Path, candidates: dict[str, list[str]], limit: int | None
) -> pd.DataFrame:
    """Project the needed columns out of the file with pyarrow, then to pandas."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover - pyarrow is a hard requirement
        raise PipelineError("pyarrow is not installed.") from exc

    # De-duplicated because two normalized fields may share one source column,
    # and one field may draw on several.
    wanted: list[str] = []
    for cols in candidates.values():
        for actual in cols:
            if actual not in wanted:
                wanted.append(actual)

    try:
        if limit is None:
            table = pq.read_table(file_path, columns=wanted)
        else:
            table = _read_limited_table(pa, pq, file_path, wanted, int(limit))
        frame = table.to_pandas()
    except Exception as exc:
        raise PipelineError(f"pyarrow failed on {file_path}: {exc}") from exc

    # Build the aliased frame explicitly instead of renaming, so that two fields
    # sharing one source column do not collide into a duplicate column name.
    # Several candidates are combined first-non-null, mirroring the DuckDB
    # COALESCE so both engines return the same values.
    data: dict[str, pd.Series] = {}
    for field, cols in candidates.items():
        if not cols:
            continue
        series = frame[cols[0]].reset_index(drop=True)
        for extra in cols[1:]:
            series = series.combine_first(frame[extra].reset_index(drop=True))
        data[field] = series
    return pd.DataFrame(data)


def _read_limited_table(pa: Any, pq: Any, file_path: Path, columns: list[str], limit: int):
    """Read at most ``limit`` rows, touching only as many batches as needed."""
    parquet_file = pq.ParquetFile(file_path)
    if limit == 0:
        schema = pa.schema([parquet_file.schema_arrow.field(name) for name in columns])
        return schema.empty_table()

    batches: list[Any] = []
    remaining = limit
    for batch in parquet_file.iter_batches(
        batch_size=min(limit, _READ_BATCH_ROWS), columns=columns
    ):
        if batch.num_rows > remaining:
            batch = batch.slice(0, remaining)
        batches.append(batch)
        remaining -= batch.num_rows
        if remaining <= 0:
            break

    if not batches:
        schema = pa.schema([parquet_file.schema_arrow.field(name) for name in columns])
        return schema.empty_table()
    return pa.Table.from_batches(batches).select(columns)


def read_many(
    paths: Sequence[Path],
    dictionary: OpenINTELDictionary,
    needed_fields: Sequence[str],
    *,
    engine: str = "auto",
    limit: int | None = None,
    warnings: list[str] | None = None,
    origin_column: str | None = "origin_file",
) -> pd.DataFrame:
    """Read several Parquet files into one normalized frame.

    OpenINTEL publishes one file per measurement day, so a real analysis run
    spans many files. This is the multi-file entry point; the MVP CLI reads a
    single file, but the shape it produces is identical, one frame with
    normalized columns.

    ``limit`` is a cap on the *total* number of rows returned, not a per-file
    cap: reading stops as soon as the budget is exhausted, so early files are
    not truncated to make room for later ones.

    When ``origin_column`` is set, that column carries the POSIX path of the
    file each row came from, which :func:`signal_extractor.extract_signals`
    picks up as per-row provenance. Pass ``None`` for a frame whose columns
    match :func:`read_parquet` exactly.
    """
    collected = warnings if warnings is not None else []
    file_paths = [Path(p) for p in paths]
    if not file_paths:
        raise PipelineError("read_many requires at least one Parquet path.")

    frames: list[pd.DataFrame] = []
    remaining = None if limit is None else int(limit)
    for file_path in file_paths:
        if remaining is not None and remaining <= 0:
            warn(
                collected,
                f"Row limit reached; {file_path.name} and any later files were not read.",
                LOGGER,
            )
            break
        frame = read_parquet(
            file_path,
            dictionary,
            needed_fields,
            engine=engine,
            limit=remaining,
            warnings=collected,
        )
        if origin_column:
            frame[origin_column] = file_path.as_posix()
        frames.append(frame)
        if remaining is not None:
            remaining -= len(frame)

    if len(frames) == 1:
        return frames[0].reset_index(drop=True)
    return pd.concat(frames, ignore_index=True, sort=False)


# --------------------------------------------------------------------------- #
# Dtype normalization (shared by both engines)
# --------------------------------------------------------------------------- #


def _normalize_frame(
    frame: pd.DataFrame,
    dictionary: OpenINTELDictionary,
    mapping: dict[str, str | None],
    warnings: list[str],
) -> pd.DataFrame:
    """Give every requested field a column, with an engine-independent dtype."""
    row_count = len(frame)
    normalized = pd.DataFrame(index=pd.RangeIndex(row_count))

    for field, actual in mapping.items():
        if actual is None or field not in frame.columns:
            series = pd.Series([None] * row_count, dtype=object)
        else:
            series = frame[field].reset_index(drop=True)

        entry = dictionary.get(field)
        declared = (entry.type if entry is not None else "").strip().lower()

        if field == "timestamp" or declared in _DATETIME_TYPES:
            normalized[field] = _coerce_datetime(field, series, warnings)
        elif declared in _INTEGER_TYPES:
            normalized[field] = _coerce_integer(field, series, warnings)
        else:
            normalized[field] = _coerce_object(series)

    return normalized


#: Upper bounds (exclusive) that identify the unit of an integer epoch column.
#: A value below ~3e9 is plausible as seconds (year 2065); below ~3e12 as
#: milliseconds; below ~3e15 as microseconds; anything larger is nanoseconds.
_EPOCH_UNIT_BOUNDS: tuple[tuple[float, str], ...] = (
    (3e9, "s"),
    (3e12, "ms"),
    (3e15, "us"),
)


def _coerce_epoch_integers(series: pd.Series) -> pd.Series | None:
    """Convert an integer epoch column to datetimes, or return ``None``.

    OpenINTEL exports ``timestamp`` as epoch **milliseconds**. pandas' default
    integer interpretation is nanoseconds, which silently maps every real
    measurement to 1970-01-01 -- and since the whole pipeline turns on comparing
    observation dates against RFC publication dates, that failure mode is
    catastrophic and completely silent. The unit is therefore detected from the
    magnitude of the data rather than assumed.
    """
    if not pd.api.types.is_integer_dtype(series) and not pd.api.types.is_float_dtype(series):
        return None
    numeric = pd.to_numeric(series, errors="coerce")
    finite = numeric.dropna()
    if finite.empty:
        return None
    largest = float(finite.abs().max())
    unit = "ns"
    for bound, candidate in _EPOCH_UNIT_BOUNDS:
        if largest < bound:
            unit = candidate
            break
    return pd.to_datetime(numeric, unit=unit, errors="coerce")


def _coerce_datetime(field: str, series: pd.Series, warnings: list[str]) -> pd.Series:
    """Coerce to naive-UTC ``datetime64[ns]``, warning if values are lost."""
    epoch = _coerce_epoch_integers(series)
    if epoch is not None:
        return epoch.astype("datetime64[ns]")

    try:
        converted = pd.to_datetime(series, errors="raise")
    except (ValueError, TypeError, OverflowError) as exc:
        converted = pd.to_datetime(series, errors="coerce")
        lost = int((converted.isna() & series.notna()).sum())
        warn(
            warnings,
            f"Column '{field}': {lost} value(s) could not be parsed as a timestamp "
            f"and were set to null ({exc}).",
            LOGGER,
        )

    if isinstance(converted.dtype, pd.DatetimeTZDtype):
        # Comparisons against RFC publication dates are naive; normalize to UTC
        # first so the cutoff logic is never tz-dependent.
        converted = converted.dt.tz_convert("UTC").dt.tz_localize(None)
    if not pd.api.types.is_datetime64_any_dtype(converted):
        converted = pd.to_datetime(converted, errors="coerce")
    return converted.astype("datetime64[ns]")


def _coerce_integer(field: str, series: pd.Series, warnings: list[str]) -> pd.Series:
    """Coerce to nullable ``Int64``.

    DuckDB hands back ``float64`` with ``NaN`` for a nullable BIGINT while
    pyarrow may hand back ``Int64``; both are funnelled through here so that the
    two engines produce identical frames and ``algorithm=None`` never resurfaces
    as ``13.0``.
    """
    numeric = pd.to_numeric(series, errors="coerce")
    lost = int((numeric.isna() & series.notna()).sum())
    if lost:
        warn(
            warnings,
            f"Column '{field}': {lost} non-numeric value(s) were set to null.",
            LOGGER,
        )

    present = numeric.dropna()
    if len(present) and not bool((present % 1 == 0).all()):
        warn(
            warnings,
            f"Column '{field}' is declared integer but carries non-integral "
            "values; keeping it as a nullable float.",
            LOGGER,
        )
        return numeric.astype("Float64")
    return numeric.astype("Int64")


def _coerce_object(series: pd.Series) -> pd.Series:
    """Return an ``object`` column whose nulls are all plain ``None``.

    pandas represents missing strings as ``NaN``, ``pd.NA`` or ``None``
    depending on the reader; collapsing them to ``None`` is what lets the two
    engines compare equal and what lets ``value is None`` mean "absent"
    everywhere downstream.
    """
    missing = series.isna()
    converted = series.astype(object)
    if bool(missing.any()):
        converted[missing] = None
    return converted
