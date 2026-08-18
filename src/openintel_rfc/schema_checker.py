"""Cross-check the RFC checklist against the OpenINTEL analysis dictionary.

Before a single Parquet row is read, this module answers the question the whole
study depends on: *which of the RFC indicators can the measurement corpus
actually answer?* An indicator that references a field OpenINTEL does not
export is not evidence of anything — it is an unanswerable question, and saying
so explicitly is more useful than silently scoring it as "no match".

Classification (:data:`openintel_rfc.models.Queryability`)
----------------------------------------------------------
``queryable``
    Every field the indicator references exists in the dictionary and the
    checklist does not mark the indicator ``ambiguous``.
``ambiguous``
    Every referenced field exists — so the indicator is queryable in principle —
    but the checklist marks it ``ambiguous`` because a match is not uniquely
    attributable to this RFC.
``partially_queryable``
    Some referenced fields exist and some do not. The indicator can still be
    partially evaluated; downstream, each condition on a missing field is
    recorded with ``field_present=False`` and fails.
``non_queryable``
    Either no referenced field exists at all, or the indicator's *discriminating*
    field is missing and nothing that survives can stand in for it (see below).

The discriminating-field rule
-----------------------------
"Some fields present, some missing" is not always the same situation. Splitting
it needs one extra distinction:

* a condition is **value-pinning** when its operator fixes a concrete value on
  the observation (``equals``, ``not_equals``, ``contains``,
  ``greater_or_equal``, ``less_or_equal``);
* a condition is **scoping** when it only narrows the population being looked at
  (``in`` over an enumeration, ``exists``).

An indicator's *discriminating* fields are the fields of its value-pinning
conditions: they carry the specific value that makes the indicator evidence for
its RFC rather than for DNSSEC in general.

A mixed indicator is downgraded from ``partially_queryable`` to
``non_queryable`` when **both** hold:

1. the indicator has at least one value-pinning condition, and *every* one of
   them is on a missing field — so the specific value the indicator is defined
   by can never be tested; and
2. no surviving field can substitute, where a present field counts as a
   substitute only if some *other* indicator of the same RFC also relies on it.
   That second clause is the "no present field can substitute" test: if the RFC
   evidences a field elsewhere, partially evaluating this indicator still yields
   information the RFC cares about; if it does not, the leftover conditions are
   generic scoping that says nothing about this RFC.

Worked example. ``rfc4033_dnssec_ok_negotiated`` loses ``dnssec_ok_flag`` but
keeps ``rr_type``, and RFC 4033's own required indicator
``rfc4033_base_dnssec_record_present`` is built on ``rr_type`` — the residue is
still RFC 4033 evidence, so the verdict is ``partially_queryable``. In contrast
``rfc8624_validator_algorithm_support`` loses ``validator_algorithm_support``
and keeps only ``rr_type``, which no other RFC 8624 indicator uses — "the record
is a DNSKEY or RRSIG" says nothing about RFC 8624's validator requirements, so
the verdict is ``non_queryable``.

Type compatibility and availability
-----------------------------------
Type mismatches (``greater_or_equal`` against a ``string`` field, ``equals 2``
against a ``string`` field) are recorded as ``type_compatible=False`` warnings,
not hard failures: the field does exist, so the condition is still evaluated —
it just probably will not behave as the checklist author intended.

Availability is a genuine limitation of the corpus rather than a defect in the
inputs: a dictionary field with ``available_from`` later than an RFC's
publication date means adoption in the intervening years is simply not
observable. Those warnings are emitted for every (field, RFC) pair, including
fields no indicator currently references, because they bound what any future
indicator could show.
"""

from __future__ import annotations

import difflib
from datetime import datetime
from typing import Any

from .models import (
    ConditionSchemaCheck,
    DictionaryField,
    IndicatorCondition,
    IndicatorSchemaCheck,
    OpenINTELDictionary,
    Queryability,
    RFCChecklistDB,
    RFCChecklistEntry,
    RFCIndicator,
    SchemaCheckReport,
)
from .utils import PipelineError, format_value, get_logger, now, unique_sorted, warn

__all__ = [
    "check_condition",
    "check_indicator",
    "check_schema",
    "queryable_field_names",
]

LOGGER = get_logger(__name__)

#: Stable key order for ``SchemaCheckReport.counts_by_queryability`` so the
#: dashboard and the report always render the same columns, even when a
#: category is empty.
QUERYABILITY_ORDER: tuple[Queryability, ...] = (
    "queryable",
    "partially_queryable",
    "ambiguous",
    "non_queryable",
)

#: Operators that pin a concrete value on the observation. See the module
#: docstring: the fields these use are an indicator's discriminating fields.
VALUE_PINNING_OPS: frozenset[str] = frozenset(
    {"equals", "not_equals", "contains", "greater_or_equal", "less_or_equal"}
)

#: Operators that only narrow the population under consideration.
SCOPING_OPS: frozenset[str] = frozenset({"in", "exists"})

#: Operators that require an ordered (numeric or temporal) field.
_ORDERING_OPS: frozenset[str] = frozenset({"greater_or_equal", "less_or_equal"})

_NUMERIC_TYPES: frozenset[str] = frozenset(
    {
        "integer",
        "int",
        "int32",
        "int64",
        "long",
        "bigint",
        "short",
        "number",
        "numeric",
        "float",
        "double",
        "decimal",
    }
)
_STRING_TYPES: frozenset[str] = frozenset({"string", "str", "text", "varchar", "utf8"})
_BOOLEAN_TYPES: frozenset[str] = frozenset({"boolean", "bool"})
_DATETIME_TYPES: frozenset[str] = frozenset({"datetime", "timestamp", "date", "time"})
_SEQUENCE_TYPES: frozenset[str] = frozenset({"list", "array", "set", "sequence", "repeated"})

#: Similarity cutoff for the "did you mean" hint on an unknown field name.
_SUGGESTION_CUTOFF = 0.6


# --------------------------------------------------------------------------- #
# Small formatting / typing helpers
# --------------------------------------------------------------------------- #


def _type_family(type_name: str) -> str:
    """Map a declared dictionary type onto a coarse family used for checking."""
    normalized = (type_name or "").strip().lower()
    base = normalized.split("[", 1)[0].split("<", 1)[0].strip()
    if base in _NUMERIC_TYPES:
        return "numeric"
    if base in _STRING_TYPES:
        return "string"
    if base in _BOOLEAN_TYPES:
        return "boolean"
    if base in _DATETIME_TYPES:
        return "datetime"
    if base in _SEQUENCE_TYPES:
        return "sequence"
    return "unknown"


def _is_numeric_text(value: str) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _value_fits_family(value: Any, family: str) -> bool:
    """Is a single condition value usable against a field of this type family?

    Deliberately lenient where the matcher is lenient: the evaluator coerces
    numeric strings, so ``"13"`` against an integer field is not a warning.
    """
    if value is None or family == "unknown":
        return True
    if family == "numeric":
        if isinstance(value, bool):
            return False
        if isinstance(value, (int, float)):
            return True
        return isinstance(value, str) and _is_numeric_text(value)
    if family == "string":
        return isinstance(value, str)
    if family == "boolean":
        if isinstance(value, bool):
            return True
        return isinstance(value, str) and value.strip().lower() in {"true", "false"}
    if family == "datetime":
        return isinstance(value, (str, datetime, int, float)) and not isinstance(value, bool)
    if family == "sequence":
        # Membership/containment against a list-valued field accepts any scalar.
        return True
    return True


def _render_condition(condition: IndicatorCondition) -> str:
    """Render a condition the way it is shown to a human, e.g. ``algorithm equals 0``."""
    if condition.op == "exists":
        return f"{condition.field} exists"
    return f"{condition.field} {condition.op} {format_value(condition.value)}"


#: Dictionary fields the matcher treats as provenance rather than as evidence.
#: Mirrors ``signal_extractor.PROVENANCE_FIELDS`` minus ``timestamp``, which has
#: its own publication-date machinery and is never used as an indicator condition.
NON_EVIDENTIAL_FIELDS: frozenset[str] = frozenset(
    {"domain", "zone", "source", "measurement_id"}
)


def _describe_field(name: str, dictionary: OpenINTELDictionary) -> str:
    """Render a field as ``name (type)`` when known, else just ``name``."""
    field = dictionary.get(name)
    return f"{name} ({field.type})" if field is not None else name


def _join(items: list[str]) -> str:
    """Join names into readable prose: ``a``, ``a and b``, ``a, b and c``."""
    if not items:
        return "none"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def _suggest_field(name: str, dictionary: OpenINTELDictionary) -> str | None:
    """Closest dictionary field name to an unknown one, if any is close enough."""
    matches = difflib.get_close_matches(
        name, dictionary.field_names, n=1, cutoff=_SUGGESTION_CUTOFF
    )
    return matches[0] if matches else None


def _availability_warning(field: DictionaryField, rfc: RFCChecklistEntry) -> str | None:
    """Warn when a field post-dates an RFC, i.e. early adoption is unobservable."""
    if field.available_from is None:
        return None
    if field.available_from <= rfc.publication_date:
        return None
    available = field.available_from.date().isoformat()
    published = rfc.publication_date.date().isoformat()
    return (
        f"Field `{field.name}` is only available from {available}, which is after "
        f"{rfc.rfc_id}'s publication date {published}; adoption before {available} "
        f"cannot be observed through this field."
    )


#: Marker phrase identifying a message produced by :func:`_availability_warning`,
#: used to keep those caveats on the indicator instead of duplicating them into
#: the report-level warning list (which carries an aggregated form already).
_AVAILABILITY_MARKER = "is only available from"


def _is_availability_warning(message: str) -> bool:
    return _AVAILABILITY_MARKER in message


# --------------------------------------------------------------------------- #
# Condition-level check
# --------------------------------------------------------------------------- #


def _type_compatibility(
    condition: IndicatorCondition, field: DictionaryField
) -> tuple[bool, str | None]:
    """Compare the dictionary field's declared type with the condition's op/value.

    Returns ``(compatible, reason)``; ``reason`` is a sentence fragment naming
    the field and the mismatch, suitable for splicing into an explanation.
    """
    family = _type_family(field.type)
    if condition.op == "exists" or family == "unknown":
        # 'exists' carries no value, and an unrecognized type gives us nothing to
        # check against; the dictionary validator already warns about the latter.
        return True, None

    if condition.op in _ORDERING_OPS:
        if family not in {"numeric", "datetime"}:
            return False, (
                f"the OpenINTEL dictionary declares {field.name} as type {field.type}, which "
                f"is not an ordered numeric or temporal type, so the '{condition.op}' "
                f"comparison cannot be applied meaningfully"
            )
        if not _value_fits_family(condition.value, family):
            return False, (
                f"the OpenINTEL dictionary declares {field.name} as type {field.type} but the "
                f"condition compares it against {format_value(condition.value)}, which is not "
                f"an ordered {family} value"
            )
        return True, None

    if condition.op == "contains":
        if family not in {"string", "sequence"}:
            return False, (
                f"the OpenINTEL dictionary declares {field.name} as type {field.type}, which "
                f"has neither substring nor membership semantics, so the 'contains' operator "
                f"cannot be applied to it"
            )
        return True, None

    if condition.op == "in":
        if not isinstance(condition.value, list):
            return False, (
                f"the 'in' operator requires a list of accepted values, but the checklist "
                f"supplies {format_value(condition.value)} for {field.name}"
            )
        bad = [item for item in condition.value if not _value_fits_family(item, family)]
        if bad:
            return False, (
                f"the OpenINTEL dictionary declares {field.name} as type {field.type} but the "
                f"accepted values include {format_value(bad)}, which are not {family} values"
            )
        return True, None

    # equals / not_equals
    if not _value_fits_family(condition.value, family):
        return False, (
            f"the OpenINTEL dictionary declares {field.name} as type {field.type} but the "
            f"condition compares it against {format_value(condition.value)}, which is not a "
            f"{family} value"
        )
    return True, None


def check_condition(
    condition: IndicatorCondition,
    dictionary: OpenINTELDictionary,
    rfc: RFCChecklistEntry,
) -> ConditionSchemaCheck:
    """Check one indicator condition against the dictionary.

    Produces the machine-readable verdict *and* the sentence that is shown
    verbatim in the schema-check report and the dashboard.
    """
    rendered = _render_condition(condition)
    field = dictionary.get(condition.field)

    # A provenance field says where an observation came from, not what the zone
    # published, so the matcher never exposes it as evidence. The SQL path reads
    # it as an ordinary column and would happily answer a condition on it, which
    # is exactly how the two engines came to disagree about RFC 9615. Refusing it
    # here keeps both paths on the same answer -- and the answer is honest: an
    # owner-name pattern is not something this signal model can testify to.
    if condition.field in NON_EVIDENTIAL_FIELDS:
        explanation = (
            f"Condition `{rendered}` of {rfc.rfc_id} cannot be evaluated: "
            f"{condition.field} is provenance, not evidence. It identifies which "
            "observation this is, and the matcher deliberately does not expose it "
            "as a testable field, so an indicator resting on it can never match. "
            "An owner-name or measurement-identity signature needs a different "
            "corpus, not a different condition."
        )
        return ConditionSchemaCheck(
            field=condition.field,
            op=condition.op,
            expected=condition.value,
            field_exists=False,
            field_type=None,
            available_from=None,
            type_compatible=True,
            explanation=explanation,
        )

    if field is None:
        suggestion = _suggest_field(condition.field, dictionary)
        hint = (
            f" The closest name the dictionary does define is {suggestion}, which may be "
            f"what was intended."
            if suggestion
            else " No similarly named field exists in the dictionary either."
        )
        explanation = (
            f"Condition `{rendered}` of {rfc.rfc_id} cannot be evaluated because the "
            f"OpenINTEL dictionary defines no field named {condition.field}; at match time "
            f"the condition is recorded with field_present=False, fails, and "
            f"{condition.field} is reported in the match's missing_fields.{hint}"
        )
        return ConditionSchemaCheck(
            field=condition.field,
            op=condition.op,
            expected=condition.value,
            field_exists=False,
            field_type=None,
            available_from=None,
            type_compatible=True,  # nothing to compare a type against
            explanation=explanation,
        )

    compatible, reason = _type_compatibility(condition, field)
    if compatible:
        explanation = (
            f"Condition `{rendered}` of {rfc.rfc_id} can be evaluated because the OpenINTEL "
            f"dictionary defines the field {field.name} with type {field.type}."
        )
    else:
        explanation = (
            f"Condition `{rendered}` of {rfc.rfc_id} can be evaluated because the field "
            f"{field.name} exists in the OpenINTEL dictionary, but it is type-suspect: "
            f"{reason}; the condition may therefore never succeed even where the mechanism "
            f"is deployed."
        )

    availability = _availability_warning(field, rfc)
    if availability:
        explanation = f"{explanation} {availability}"

    return ConditionSchemaCheck(
        field=condition.field,
        op=condition.op,
        expected=condition.value,
        field_exists=True,
        field_type=field.type,
        available_from=field.available_from,
        type_compatible=compatible,
        explanation=explanation,
    )


# --------------------------------------------------------------------------- #
# Indicator-level check
# --------------------------------------------------------------------------- #


def _sibling_fields(rfc: RFCChecklistEntry, indicator: RFCIndicator) -> set[str]:
    """Fields referenced by the RFC's *other* indicators.

    Used by the substitution clause of the discriminating-field rule: a field the
    RFC relies on elsewhere can carry partial evidence on its own.
    """
    fields: set[str] = set()
    for other in rfc.indicators:
        if other.id == indicator.id:
            continue
        fields.update(other.fields_used)
    return fields


def _classify(
    rfc: RFCChecklistEntry,
    indicator: RFCIndicator,
    present: list[str],
    missing: list[str],
) -> tuple[Queryability, str]:
    """Return the queryability verdict and the fragment that justifies it.

    The fragment is spliced into the indicator's ``reasoning`` sentence; see the
    module docstring for the rule this implements.
    """
    if not present:
        return "non_queryable", "no-fields"
    if not missing:
        return ("ambiguous" if indicator.ambiguous else "queryable"), "all-fields"

    pinning_fields = unique_sorted(
        condition.field
        for condition in indicator.conditions
        if condition.op in VALUE_PINNING_OPS
    )
    missing_set = set(missing)
    all_pinning_missing = bool(pinning_fields) and all(
        name in missing_set for name in pinning_fields
    )
    if not all_pinning_missing:
        return "partially_queryable", "value-survives"

    substitutes = sorted(set(present) & _sibling_fields(rfc, indicator))
    if substitutes:
        return "partially_queryable", "substitute"
    return "non_queryable", "discriminator-lost"


def check_indicator(
    rfc: RFCChecklistEntry,
    indicator: RFCIndicator,
    dictionary: OpenINTELDictionary,
) -> IndicatorSchemaCheck:
    """Classify one indicator's queryability against the dictionary.

    The returned ``reasoning`` is a complete sentence naming the concrete fields
    involved; it is rendered verbatim in the report and the dashboard, so it has
    to stand on its own without the surrounding table.
    """
    condition_checks = [
        check_condition(condition, dictionary, rfc) for condition in indicator.conditions
    ]

    # A provenance field is defined in the dictionary but is not evidence, so it
    # counts as missing here: the matcher never exposes it, and an indicator that
    # rests on one can never match however well-formed it looks.
    def usable(name: str) -> bool:
        return dictionary.has(name) and name not in NON_EVIDENTIAL_FIELDS

    present = [name for name in indicator.fields_used if usable(name)]
    missing = [name for name in indicator.fields_used if not usable(name)]
    present_described = [_describe_field(name, dictionary) for name in present]

    queryability, rule = _classify(rfc, indicator, present, missing)

    # Availability limitations are attached per indicator as well as to the
    # report, so a reader looking at one indicator sees the caveat that applies
    # to it without cross-referencing the global warning list.
    indicator_warnings: list[str] = []
    for name in present:
        field = dictionary.get(name)
        if field is None:  # pragma: no cover - present implies get() succeeds
            continue
        message = _availability_warning(field, rfc)
        if message:
            indicator_warnings.append(message)
    incompatible = [check.field for check in condition_checks if not check.type_compatible]
    for name in unique_sorted(incompatible):
        indicator_warnings.append(
            f"Indicator {indicator.id} of {rfc.rfc_id} applies an operator to "
            f"{_describe_field(name, dictionary)} that its declared type does not support; "
            f"the condition is still evaluated but is unlikely to match."
        )

    ambiguity_clause = (
        f" The checklist additionally marks this indicator ambiguous, so even a full match "
        f"is not uniquely attributable to {rfc.rfc_id}."
        if indicator.ambiguous and queryability != "ambiguous"
        else ""
    )

    if rule == "all-fields" and queryability == "queryable":
        reasoning = (
            f"Indicator {indicator.id} is queryable because all fields it references exist "
            f"in the OpenINTEL dictionary: {', '.join(present_described)}."
        )
    elif rule == "all-fields":  # queryability == "ambiguous"
        reasoning = (
            f"Indicator {indicator.id} is ambiguous: every field it references exists in the "
            f"OpenINTEL dictionary ({', '.join(present_described)}), so it can be evaluated, "
            f"but the checklist marks it ambiguous because the same observation is equally "
            f"well explained by other RFCs, so a match is not uniquely attributable to "
            f"{rfc.rfc_id}."
        )
    elif rule == "no-fields":
        reasoning = (
            f"Indicator {indicator.id} is non-queryable because none of the fields it "
            f"references exist in the OpenINTEL dictionary: {_join(missing)}. No part of it "
            f"can ever be evaluated against the measurement corpus."
        )
    elif rule == "discriminator-lost":
        pinning_missing = unique_sorted(
            condition.field
            for condition in indicator.conditions
            if condition.op in VALUE_PINNING_OPS and condition.field in set(missing)
        )
        reasoning = (
            f"Indicator {indicator.id} is non-queryable: the field carrying its "
            f"discriminating value, {_join(pinning_missing)}, is absent from the OpenINTEL "
            f"dictionary, and the only field that remains, {_join(present_described)}, merely "
            f"scopes which records are considered and is not used by any other {rfc.rfc_id} "
            f"indicator, so nothing testable is left to attribute an observation to "
            f"{rfc.rfc_id}."
        )
    elif rule == "substitute":
        substitutes = sorted(set(present) & _sibling_fields(rfc, indicator))
        reasoning = (
            f"Indicator {indicator.id} is partially queryable: {_join(present_described)} "
            f"exists in the OpenINTEL dictionary but {_join(missing)} does not, so every "
            f"condition on {_join(missing)} fails with field_present=False. The surviving "
            f"field {_join(substitutes)} is also relied on by other {rfc.rfc_id} indicators, "
            f"so the part that can be evaluated still carries evidence for {rfc.rfc_id}."
        )
    else:  # rule == "value-survives"
        reasoning = (
            f"Indicator {indicator.id} is partially queryable: {_join(present_described)} "
            f"exists in the OpenINTEL dictionary but {_join(missing)} does not, so the "
            f"conditions on {_join(missing)} fail with field_present=False while the "
            f"remaining conditions, which carry the indicator's discriminating value, are "
            f"still evaluated."
        )

    return IndicatorSchemaCheck(
        rfc_id=rfc.rfc_id,
        rfc_title=rfc.title,
        rfc_publication_date=rfc.publication_date,
        indicator_id=indicator.id,
        indicator_description=indicator.description,
        required=indicator.required,
        weight=indicator.weight,
        queryability=queryability,
        reasoning=reasoning + ambiguity_clause,
        condition_checks=condition_checks,
        present_fields=present,
        missing_fields=missing,
        warnings=indicator_warnings,
    )


# --------------------------------------------------------------------------- #
# Report-level check
# --------------------------------------------------------------------------- #


def check_schema(
    db: RFCChecklistDB,
    dictionary: OpenINTELDictionary,
    *,
    checklist_path: str,
    dictionary_path: str,
    warnings: list[str] | None = None,
) -> SchemaCheckReport:
    """Cross-check every indicator of every RFC against the dictionary.

    Args:
        db: the loaded checklist database.
        dictionary: the loaded OpenINTEL analysis dictionary.
        checklist_path: path the checklist came from, recorded in the report.
        dictionary_path: path the dictionary came from, recorded in the report.
        warnings: optional accumulator shared with the rest of the run. When
            given, warnings raised here are appended to it *and* copied into the
            report, so the caller's earlier warnings are carried through.

    Raises:
        PipelineError: when the checklist contains no RFCs at all, which makes
            the whole run vacuous.
    """
    if not db.rfcs:
        raise PipelineError(
            f"The checklist database loaded from {checklist_path} contains no RFCs, so there "
            f"is nothing to cross-check against {dictionary_path}."
        )

    collected: list[str] = warnings if warnings is not None else []

    checks: list[IndicatorSchemaCheck] = []
    for rfc in db.rfcs:
        for indicator in rfc.indicators:
            checks.append(check_indicator(rfc, indicator, dictionary))
    checks.sort(key=lambda check: (check.rfc_id, check.indicator_id))

    counts: dict[str, int] = {label: 0 for label in QUERYABILITY_ORDER}
    for check in checks:
        counts[check.queryability] = counts.get(check.queryability, 0) + 1

    referenced: dict[str, list[str]] = {}
    for check in checks:
        for name in check.present_fields + check.missing_fields:
            referenced.setdefault(name, []).append(check.indicator_id)

    unused = sorted(name for name in dictionary.field_names if name not in referenced)

    # 1. Fields the checklist asks for that the corpus does not have.
    for name in sorted(referenced):
        if dictionary.has(name):
            continue
        users = sorted(set(referenced[name]))
        suggestion = _suggest_field(name, dictionary)
        hint = (
            f" The closest defined field name is {suggestion}."
            if suggestion
            else " No similarly named field is defined either."
        )
        warn(
            collected,
            f"Field '{name}' is referenced by {len(users)} indicator(s) "
            f"({', '.join(users)}) but is not defined in the OpenINTEL dictionary loaded from "
            f"{dictionary_path}; every condition on it is unanswerable.{hint}",
            LOGGER,
        )

    # 2. Indicators that cannot contribute evidence at all.
    for check in checks:
        if check.queryability == "non_queryable":
            warn(
                collected,
                f"Indicator {check.indicator_id} of {check.rfc_id} is non-queryable against "
                f"this dictionary and will be skipped during matching: {check.reasoning}",
                LOGGER,
            )

    # 3. Corpus availability limits, aggregated.
    #
    #    A naive sweep of every dictionary field against every RFC emits one
    #    warning per pair and buries the actionable findings under dozens of
    #    restatements of the same fact. Two aggregated forms carry the same
    #    information:
    #      (a) one warning per RFC, over the fields its own indicators rely on,
    #          which is what actually bounds this run's conclusions;
    #      (b) one forward-looking warning for late fields no indicator uses yet.
    for rfc in sorted(db.rfcs, key=lambda entry: entry.rfc_id):
        rfc_fields = {
            name
            for indicator in rfc.indicators
            for name in indicator.fields_used
            if dictionary.has(name)
        }
        late: list[tuple[str, datetime]] = []
        for name in sorted(rfc_fields):
            field = dictionary.get(name)
            if field and field.available_from and field.available_from > rfc.publication_date:
                late.append((name, field.available_from))
        if not late:
            continue
        observable_from = max(available for _, available in late)
        field_list = ", ".join(
            f"`{name}` (from {available.date().isoformat()})" for name, available in late
        )
        warn(
            collected,
            f"{rfc.rfc_id} was published {rfc.publication_date.date().isoformat()}, but the "
            f"OpenINTEL fields its indicators rely on only become available later: {field_list}. "
            f"Adoption of {rfc.rfc_id} before {observable_from.date().isoformat()} cannot be "
            f"observed through this corpus, so a first-seen date is a lower bound on when the "
            f"mechanism appeared, not on when it was adopted.",
            LOGGER,
        )

    earliest_publication = min(
        (rfc.publication_date for rfc in db.rfcs), default=None
    )
    if earliest_publication is not None:
        forward_looking = sorted(
            field.name
            for field in dictionary.fields
            if field.name in unused
            and field.available_from
            and field.available_from > earliest_publication
        )
        if forward_looking:
            warn(
                collected,
                "Dictionary fields "
                + ", ".join(
                    f"`{name}` (from {dictionary.get(name).available_from.date().isoformat()})"  # type: ignore[union-attr]
                    for name in forward_looking
                )
                + " become available after the earliest RFC in this checklist was published. "
                "No indicator references them today, but any future indicator built on them "
                "will inherit that lower bound.",
                LOGGER,
            )

    # 4. Type mismatches, promoted from the indicator level.
    #
    #    Per-indicator availability caveats stay on the indicator: step 3 already
    #    states the same limitation once per RFC, and repeating it per indicator
    #    would restore the noise that aggregation removed. Type mismatches have
    #    no aggregate form, so they are promoted.
    for check in checks:
        for message in check.warnings:
            if _is_availability_warning(message):
                continue
            warn(collected, message, LOGGER)

    report = SchemaCheckReport(
        generated_at=now(),
        checklist_path=str(checklist_path),
        dictionary_path=str(dictionary_path),
        dictionary_field_count=len(dictionary.fields),
        rfc_count=len(db.rfcs),
        indicator_count=len(checks),
        counts_by_queryability=counts,
        indicators=checks,
        dictionary_fields=sorted(dictionary.fields, key=lambda item: item.name),
        unused_dictionary_fields=unused,
        warnings=list(collected),
    )
    LOGGER.info(
        "Schema check: %d indicators across %d RFCs (%s)",
        report.indicator_count,
        report.rfc_count,
        ", ".join(f"{label}={counts[label]}" for label in QUERYABILITY_ORDER),
    )
    return report


def queryable_field_names(report: SchemaCheckReport) -> list[str]:
    """Dictionary fields the Parquet reader actually has to load.

    Only indicators that can be evaluated at least in part are considered:
    a ``non_queryable`` indicator is never evaluated, so its surviving fields do
    not need to be read on its behalf (they are still included if any evaluable
    indicator references them). Returned sorted and deduplicated.
    """
    names: set[str] = set()
    for check in report.indicators:
        if check.queryability == "non_queryable":
            continue
        names.update(check.present_fields)
    return sorted(names)
