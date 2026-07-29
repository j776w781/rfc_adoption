"""Shared helpers: deterministic IO, timestamp normalization, ID minting.

Everything here is intentionally dependency-light so it can be imported from any
module without creating cycles.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from . import config

__all__ = [
    "PipelineError",
    "get_logger",
    "warn",
    "ensure_dir",
    "read_json",
    "write_json",
    "write_text",
    "to_jsonable",
    "parse_timestamp",
    "normalize_timestamp",
    "iso",
    "signal_id",
    "trace_id",
    "review_id",
    "stable_hash",
    "now",
    "month_key",
    "year_key",
    "round_score",
    "unique_sorted",
    "format_value",
    "flatten_for_csv",
]

_LOG_FORMAT = "%(levelname)s %(name)s: %(message)s"


class PipelineError(RuntimeError):
    """Raised when the pipeline cannot continue with the given inputs.

    Used instead of silently degrading, so that bad inputs surface immediately.
    """


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers and not logging.getLogger().handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def warn(warnings: list[str], message: str, logger: logging.Logger | None = None) -> None:
    """Record a warning both in the collected list and on the logger.

    Warnings are part of the output contract: they end up in the report and the
    dashboard rather than vanishing into stderr.
    """
    if message not in warnings:
        warnings.append(message)
    if logger is not None:
        logger.warning(message)


# --------------------------------------------------------------------------- #
# Filesystem / JSON
# --------------------------------------------------------------------------- #


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def read_json(path: str | Path) -> Any:
    file_path = Path(path)
    if not file_path.is_file():
        raise PipelineError(f"Input file not found: {file_path}")
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:  # pragma: no cover - exercised via CLI
        raise PipelineError(f"{file_path} is not valid JSON: {exc}") from exc


def to_jsonable(value: Any) -> Any:
    """Recursively convert models / datetimes / paths into JSON-safe values."""
    if isinstance(value, BaseModel):
        return to_jsonable(value.model_dump(mode="python"))
    if isinstance(value, Mapping):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        items = list(value)
        if isinstance(value, (set, frozenset)):
            items = sorted(items, key=repr)
        return [to_jsonable(v) for v in items]
    if isinstance(value, datetime):
        return value.replace(tzinfo=None).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, float):
        # Collapse -0.0 and long float tails so output is byte-stable.
        rounded = round(value, config.SCORE_PRECISION)
        return 0.0 if rounded == 0 else rounded
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if hasattr(value, "item"):  # numpy scalars
        try:
            return to_jsonable(value.item())
        except Exception:  # pragma: no cover - defensive
            pass
    return str(value)


def write_json(path: str | Path, payload: Any, *, indent: int = 2) -> Path:
    file_path = Path(path)
    ensure_dir(file_path.parent)
    text = json.dumps(to_jsonable(payload), indent=indent, ensure_ascii=False)
    file_path.write_text(text + "\n", encoding="utf-8")
    return file_path


def write_text(path: str | Path, text: str) -> Path:
    file_path = Path(path)
    ensure_dir(file_path.parent)
    if not text.endswith("\n"):
        text += "\n"
    file_path.write_text(text, encoding="utf-8")
    return file_path


# --------------------------------------------------------------------------- #
# Timestamps
# --------------------------------------------------------------------------- #

_TIMESTAMP_FORMATS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y-%m",
    "%Y",
)


def parse_timestamp(value: Any) -> datetime:
    """Parse a timestamp from JSON, Parquet or epoch milliseconds.

    Always returns a naive UTC datetime so comparisons never raise on mixed
    tz-awareness.
    """
    if value is None:
        raise PipelineError("Cannot parse a timestamp from None")
    if isinstance(value, datetime):
        return normalize_timestamp(value)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        seconds = float(value)
        # OpenINTEL exports epoch milliseconds; anything past year 5138 in
        # seconds is really milliseconds.
        if seconds > 1e11:
            seconds /= 1000.0
        return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(tzinfo=None)
    if hasattr(value, "to_pydatetime"):  # pandas.Timestamp
        return normalize_timestamp(value.to_pydatetime())
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1]
    for fmt in _TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return normalize_timestamp(datetime.fromisoformat(text))
    except ValueError as exc:
        raise PipelineError(f"Unrecognized timestamp value: {value!r}") from exc


def normalize_timestamp(value: datetime) -> datetime:
    """Drop tzinfo (converting to UTC first) so all comparisons are naive-UTC."""
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def iso(value: datetime | date | None) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return normalize_timestamp(value).isoformat()
    return value.isoformat()


def now() -> datetime:
    """Current time, or a frozen timestamp when deterministic mode is on."""
    if os.environ.get(config.DETERMINISTIC_TIMESTAMP_ENV) == "1":
        return datetime(2020, 1, 1, 0, 0, 0)
    return datetime.now().replace(microsecond=0)


def month_key(value: datetime) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def year_key(value: datetime) -> str:
    return f"{value.year:04d}"


# --------------------------------------------------------------------------- #
# IDs and small formatting helpers
# --------------------------------------------------------------------------- #


def signal_id(index: int) -> str:
    return f"{config.SIGNAL_ID_PREFIX}{index:0{config.SIGNAL_ID_WIDTH}d}"


def trace_id(signal_id_value: str, rfc_id: str) -> str:
    slug = rfc_id.lower().replace(" ", "").replace("/", "-")
    return f"{config.TRACE_ID_PREFIX}{signal_id_value}_{slug}"


def review_id(index: int) -> str:
    return f"{config.REVIEW_ID_PREFIX}{index:04d}"


def stable_hash(*parts: Any) -> str:
    """Short deterministic hash; used for IDs that have no natural ordering."""
    import hashlib

    joined = "|".join(str(p) for p in parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:10]


def round_score(value: float) -> float:
    rounded = round(float(value), config.SCORE_PRECISION)
    return 0.0 if rounded == 0 else rounded


def unique_sorted(values: Iterable[Any]) -> list[Any]:
    """Deduplicate while producing a deterministic order (None values dropped)."""
    seen = {v for v in values if v is not None}
    try:
        return sorted(seen)
    except TypeError:  # mixed types
        return sorted(seen, key=repr)


def format_value(value: Any) -> str:
    """Render a value for human-readable explanation strings."""
    if value is None:
        return "<missing>"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(format_value(v) for v in value) + "]"
    if isinstance(value, datetime):
        return iso(value)
    return str(value)


def flatten_for_csv(value: Any) -> Any:
    """Flatten lists/dicts into a single CSV cell without losing information."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return "; ".join(str(flatten_for_csv(v)) for v in value)
    if isinstance(value, Mapping):
        return json.dumps(to_jsonable(value), ensure_ascii=False, sort_keys=True)
    if isinstance(value, datetime):
        return iso(value)
    return value


def require_sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise PipelineError(f"{name} must be a list, got {type(value).__name__}")
    return value
