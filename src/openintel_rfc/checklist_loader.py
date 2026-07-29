"""Loading and sanity-checking of the two JSON inputs the pipeline runs on.

Two files drive everything downstream:

* the **RFC checklist database** (``data/rfc_checklists/*.json``), which lists
  each RFC together with the observable indicators that evidence its
  deployment, and
* the **OpenINTEL analysis dictionary** (``data/openintel_dictionary/*.json``),
  which describes the normalized fields an observation can actually carry.

This module is the only place that turns those files into
:class:`~openintel_rfc.models.RFCChecklistDB` /
:class:`~openintel_rfc.models.OpenINTELDictionary` instances.

Two distinct failure modes are handled differently on purpose:

* **Unusable input** — the JSON does not fit the model at all (a missing
  ``rfc_id``, an unknown operator, a malformed date). That raises
  :class:`~openintel_rfc.utils.PipelineError`. A raw pydantic traceback is not
  acceptable operator feedback, so the error text names the offending RFC,
  indicator and field before quoting pydantic's own message.
* **Suspicious but usable input** — duplicate identifiers, an RFC with no
  required indicators, a dangling ``related_rfc_ids`` reference. Those are
  returned as warning strings so the caller can route them into the run's
  warning list, the report and the dashboard instead of aborting the run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .models import (
    IndicatorCondition,
    OpenINTELDictionary,
    RFCChecklistDB,
    RFCChecklistEntry,
    RFCIndicator,
)
from .utils import PipelineError, get_logger, now, read_json

__all__ = [
    "load_checklist_db",
    "load_dictionary",
    "validate_checklist_db",
    "validate_dictionary",
    "indicator_index",
]

LOGGER = get_logger(__name__)

#: Operators that compare against ``condition.value``; only ``exists`` does not.
_OPS_REQUIRING_VALUE: frozenset[str] = frozenset(
    {"equals", "not_equals", "in", "contains", "greater_or_equal", "less_or_equal"}
)

#: Field types the rest of the pipeline knows how to reason about. Anything else
#: still loads, but is flagged so a typo in the dictionary does not silently
#: disable type checking in the schema checker.
_KNOWN_FIELD_TYPES: frozenset[str] = frozenset(
    {
        "string",
        "integer",
        "float",
        "number",
        "boolean",
        "datetime",
        "date",
        "list",
        "array",
    }
)

#: Keys used to name a JSON object when describing a validation error location.
_IDENTITY_KEYS: tuple[str, ...] = ("rfc_id", "id", "name", "field")

#: Cap on how many pydantic errors are quoted, so one broken file does not
#: produce a wall of text.
_MAX_REPORTED_ERRORS = 20


# --------------------------------------------------------------------------- #
# Turning pydantic failures into operator-readable errors
# --------------------------------------------------------------------------- #


def _identify(node: Any) -> str | None:
    """Return a short human label for a JSON object, e.g. its ``rfc_id``."""
    if not isinstance(node, dict):
        return None
    for key in _IDENTITY_KEYS:
        value = node.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _describe_location(payload: Any, loc: tuple[Any, ...]) -> str:
    """Render a pydantic ``loc`` tuple as a path through the *raw* JSON.

    The models never got built, so the identifying names have to come from the
    JSON payload itself. Walking it alongside ``loc`` lets the message say
    ``rfcs[7] (RFC 8624).indicators[2] (rfc8624_validator_algorithm_support)``
    instead of the opaque ``('rfcs', 7, 'indicators', 2)``.
    """
    node: Any = payload
    tokens: list[str] = []
    for element in loc:
        if isinstance(element, int):
            node = node[element] if isinstance(node, list) and 0 <= element < len(node) else None
            label = _identify(node)
            tokens.append(f"[{element}]" + (f" ({label})" if label else ""))
        else:
            node = node.get(element) if isinstance(node, dict) else None
            tokens.append(f".{element}" if tokens else str(element))
    return "".join(tokens) or "<document root>"


def _validation_error_message(
    *, path: Path, what: str, payload: Any, error: ValidationError
) -> str:
    """Compose the full PipelineError text for a failed model validation."""
    errors = error.errors()
    lines = [
        f"{path} is not a usable {what}: {len(errors)} validation problem(s) found."
    ]
    for entry in errors[:_MAX_REPORTED_ERRORS]:
        location = _describe_location(payload, tuple(entry.get("loc", ())))
        message = entry.get("msg", "invalid value")
        supplied = entry.get("input", None)
        # ``input`` can be an entire nested object; truncate so the error stays
        # readable in a terminal.
        rendered = repr(supplied)
        if len(rendered) > 160:
            rendered = rendered[:157] + "..."
        lines.append(f"  - {location}: {message} (received {rendered})")
    if len(errors) > _MAX_REPORTED_ERRORS:
        lines.append(f"  - ... and {len(errors) - _MAX_REPORTED_ERRORS} further problem(s).")
    lines.append(
        "Fix the offending entries in the source JSON; the pipeline refuses to "
        "run on a partially understood checklist because that would silently "
        "change which RFCs can be matched."
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #


def _require_mapping(payload: Any, path: Path, what: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise PipelineError(
            f"{path} must contain a JSON object at the top level to be a {what}, "
            f"but it contains a {type(payload).__name__}."
        )
    return payload


def load_checklist_db(path: str | Path) -> RFCChecklistDB:
    """Load and validate the RFC checklist / signature database.

    Raises:
        PipelineError: if the file is missing, is not JSON, or does not satisfy
            :class:`~openintel_rfc.models.RFCChecklistDB`. The message names the
            RFC, indicator and field that failed.
    """
    file_path = Path(path)
    payload = _require_mapping(read_json(file_path), file_path, "RFC checklist database")
    try:
        db = RFCChecklistDB.model_validate(payload)
    except ValidationError as exc:
        raise PipelineError(
            _validation_error_message(
                path=file_path,
                what="RFC checklist database",
                payload=payload,
                error=exc,
            )
        ) from exc
    LOGGER.info(
        "Loaded checklist %s from %s: %d RFCs, %d indicators",
        db.checklist_version,
        file_path,
        len(db.rfcs),
        sum(len(entry.indicators) for entry in db.rfcs),
    )
    return db


def load_dictionary(path: str | Path) -> OpenINTELDictionary:
    """Load and validate the OpenINTEL analysis dictionary.

    Raises:
        PipelineError: if the file is missing, is not JSON, or does not satisfy
            :class:`~openintel_rfc.models.OpenINTELDictionary`.
    """
    file_path = Path(path)
    payload = _require_mapping(read_json(file_path), file_path, "OpenINTEL dictionary")
    try:
        dictionary = OpenINTELDictionary.model_validate(payload)
    except ValidationError as exc:
        raise PipelineError(
            _validation_error_message(
                path=file_path,
                what="OpenINTEL dictionary",
                payload=payload,
                error=exc,
            )
        ) from exc
    LOGGER.info(
        "Loaded dictionary %s from %s: %d fields",
        dictionary.dictionary_version,
        file_path,
        len(dictionary.fields),
    )
    return dictionary


# --------------------------------------------------------------------------- #
# Non-fatal consistency checks
# --------------------------------------------------------------------------- #


def _condition_label(rfc: RFCChecklistEntry, indicator: RFCIndicator, index: int) -> str:
    return f"{rfc.rfc_id} indicator {indicator.id} condition {index + 1}"


def _check_condition(
    rfc: RFCChecklistEntry,
    indicator: RFCIndicator,
    index: int,
    condition: IndicatorCondition,
    warnings: list[str],
) -> None:
    """Collect warnings for one condition (never raises)."""
    label = _condition_label(rfc, indicator, index)
    if condition.op in _OPS_REQUIRING_VALUE and condition.value is None:
        warnings.append(
            f"{label} uses operator '{condition.op}' on field '{condition.field}' "
            f"but supplies no value; only the 'exists' operator works without one, "
            f"so this condition can never be satisfied."
        )
    if condition.op == "in" and condition.value is not None:
        if not isinstance(condition.value, list):
            warnings.append(
                f"{label} uses the 'in' operator on field '{condition.field}' with a "
                f"{type(condition.value).__name__} value ({condition.value!r}); "
                f"'in' expects a JSON list of accepted values."
            )
        elif not condition.value:
            warnings.append(
                f"{label} uses the 'in' operator on field '{condition.field}' with an "
                f"empty list, so no observation can ever match it."
            )


def validate_checklist_db(db: RFCChecklistDB) -> list[str]:
    """Return human-readable warnings about a structurally valid checklist DB.

    None of these abort the run: each describes something that will make the
    results harder to trust rather than impossible to compute. They are surfaced
    in the report and dashboard so the operator can decide.

    Checks performed:

    * duplicate ``rfc_id`` (the second entry is unreachable via ``db.get``),
    * duplicate indicator ``id`` anywhere in the DB (indicator IDs key the
      review queue and the per-indicator evaluations, so collisions merge
      unrelated evidence),
    * an RFC with no indicators at all (it can never match),
    * an RFC with no *required* indicators (it can never reach ``valid_match``,
      because the decision rules need a non-empty required set),
    * a ``publication_date`` in the future (every observation would then be
      ``timestamp_invalid``),
    * a condition whose operator needs a value but has ``value=None``,
    * an ``in`` condition whose value is not a list (or is an empty list),
    * a ``related_rfc_ids`` entry that is not itself in the DB.
    """
    warnings: list[str] = []
    current_time = now()

    seen_rfc_ids: dict[str, int] = {}
    seen_indicator_ids: dict[str, str] = {}

    for position, rfc in enumerate(db.rfcs):
        if rfc.rfc_id in seen_rfc_ids:
            warnings.append(
                f"Duplicate rfc_id '{rfc.rfc_id}' at rfcs[{position}]; it also appears at "
                f"rfcs[{seen_rfc_ids[rfc.rfc_id]}]. Lookups resolve to the first entry, "
                f"so the later definition is ignored."
            )
        else:
            seen_rfc_ids[rfc.rfc_id] = position

        if not rfc.indicators:
            warnings.append(
                f"{rfc.rfc_id} defines no indicators, so no observation can ever match it."
            )
        elif not rfc.required_indicators:
            warnings.append(
                f"{rfc.rfc_id} defines {len(rfc.indicators)} indicator(s) but none of them "
                f"is required=true, so it can never be decided a valid_match; the best "
                f"attainable decision is partial_match."
            )

        if rfc.publication_date > current_time:
            warnings.append(
                f"{rfc.rfc_id} has publication_date {rfc.publication_date.date().isoformat()}, "
                f"which is in the future relative to {current_time.date().isoformat()}; every "
                f"observation will fail the publication-date cutoff and be recorded as "
                f"timestamp_invalid."
            )

        for related in rfc.related_rfc_ids:
            if related not in db.rfc_ids:
                warnings.append(
                    f"{rfc.rfc_id} lists related RFC '{related}', which is not defined in this "
                    f"checklist database; the relationship cannot be resolved or ranked against."
                )

        for indicator in rfc.indicators:
            owner = seen_indicator_ids.get(indicator.id)
            if owner is not None:
                warnings.append(
                    f"Duplicate indicator id '{indicator.id}' on {rfc.rfc_id}; it is already "
                    f"used by {owner}. Indicator IDs key the schema report and the review "
                    f"queue, so evidence from the two indicators cannot be told apart."
                )
            else:
                seen_indicator_ids[indicator.id] = rfc.rfc_id

            for index, condition in enumerate(indicator.conditions):
                _check_condition(rfc, indicator, index, condition, warnings)

    return warnings


def validate_dictionary(dictionary: OpenINTELDictionary) -> list[str]:
    """Return human-readable warnings about a structurally valid dictionary.

    Checks performed:

    * an empty dictionary (every indicator would be non-queryable),
    * duplicate field ``name`` (``dictionary.get`` resolves to the first),
    * a field ``type`` the schema checker does not know how to type-check,
    * a field with no ``openintel_native_fields``, which means the Parquet
      reader has no column alias to resolve it from,
    * a field with a blank ``name`` or ``type``.
    """
    warnings: list[str] = []

    if not dictionary.fields:
        warnings.append(
            "The OpenINTEL dictionary declares no fields, so every checklist indicator "
            "will be classified non_queryable."
        )

    seen: dict[str, int] = {}
    for position, field in enumerate(dictionary.fields):
        if field.name in seen:
            warnings.append(
                f"Duplicate dictionary field name '{field.name}' at fields[{position}]; it "
                f"also appears at fields[{seen[field.name]}]. Lookups resolve to the first "
                f"definition, so the later one is ignored."
            )
        else:
            seen[field.name] = position

        if not field.name.strip():
            warnings.append(
                f"Dictionary fields[{position}] has a blank name, so no indicator condition "
                f"can ever reference it."
            )

        normalized_type = field.type.strip().lower()
        if not normalized_type:
            warnings.append(
                f"Dictionary field '{field.name}' declares an empty type, so operator/value "
                f"type compatibility for conditions on this field cannot be verified."
            )
        elif normalized_type not in _KNOWN_FIELD_TYPES:
            warnings.append(
                f"Dictionary field '{field.name}' declares type '{field.type}', which the "
                f"schema checker does not recognize; operator/value type compatibility for "
                f"conditions on this field cannot be verified."
            )

        if not field.openintel_native_fields:
            warnings.append(
                f"Dictionary field '{field.name}' lists no openintel_native_fields, so the "
                f"Parquet reader has no real OpenINTEL column to resolve it from; it will "
                f"only be populated if a column of exactly that name exists."
            )

    return warnings


# --------------------------------------------------------------------------- #
# Indexing
# --------------------------------------------------------------------------- #


def indicator_index(
    db: RFCChecklistDB,
) -> dict[str, tuple[RFCChecklistEntry, RFCIndicator]]:
    """Map every indicator id to its ``(rfc, indicator)`` pair.

    The review queue, the matcher and the dashboard all resolve indicators by id
    alone, so this index is what makes an id sufficient to recover its RFC.

    Duplicate ids keep the *first* definition, mirroring
    :meth:`RFCChecklistDB.get`; :func:`validate_checklist_db` reports the
    collision separately. Keys are returned in sorted order so any consumer that
    iterates the mapping produces deterministic output.
    """
    collected: dict[str, tuple[RFCChecklistEntry, RFCIndicator]] = {}
    for rfc in db.rfcs:
        for indicator in rfc.indicators:
            collected.setdefault(indicator.id, (rfc, indicator))
    return {key: collected[key] for key in sorted(collected)}
