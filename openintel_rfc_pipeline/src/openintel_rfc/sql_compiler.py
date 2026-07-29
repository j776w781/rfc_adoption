"""Compiling the RFC checklist into SQL that DuckDB evaluates during the scan.

The MVP builds one :class:`~openintel_rfc.models.ObservedSignal` per Parquet row
and asks :mod:`openintel_rfc.matcher` about it. That is the right shape for a
single day of one TLD and the wrong shape for 10^10 rows: the Python objects
alone would not fit on the machine. This module translates the same checklist
into a SQL expression per indicator so that the matching happens inside the
scan, and only aggregates come back.

What is and is not moved into SQL
---------------------------------
SQL answers exactly one question: **which rows satisfy which indicators**, and
-- as a direct consequence of that -- which :class:`~openintel_rfc.models.Decision`
each (row, RFC) pair lands on. Nothing else moves.

The decision *rules* are not reimplemented here either. :func:`compile_checklist`
enumerates every evidence pattern an RFC can produce (each indicator is matched,
contradicted, or partly-untestable; the timestamp is valid or not), asks the real
:func:`openintel_rfc.ranking.score_match` what that pattern means, and emits the
resulting lookup as a ``CASE`` over a small integer. The Python implementation
stays the single source of truth; SQL only carries a precomputed table derived
from it. The scoring *formula* never appears in SQL at all -- scores are produced
in Python from sampled exemplars (see :mod:`openintel_rfc.scale_runner`).

Operator semantics
------------------
Every operator mirrors :func:`openintel_rfc.matcher.evaluate_condition` exactly,
because a run whose SQL and Python paths disagree is worse than no run at all:

* a NULL observed value fails **every** operator, ``not_equals`` included --
  we cannot claim a field differs from a value we never saw;
* ``exists`` is ``IS NOT NULL``;
* ``contains`` is substring containment for text and fails on any other type,
  matching the matcher's type-mismatch branch;
* numeric comparison coerces numeric strings, via
  ``TRY_CAST(CAST(x AS VARCHAR) AS DOUBLE)``. Routing through VARCHAR reproduces
  :func:`openintel_rfc.matcher._as_number` for free: booleans render as
  ``'true'``/``'false'`` and timestamps as text, so both coerce to NULL exactly
  as the Python helper returns ``None`` for them;
* a type mismatch yields FALSE, never an error. ``TRY_CAST`` and ``typeof``
  guards keep every comparison total.

Every emitted predicate is strictly two-valued once the ``IS NOT NULL`` guard has
passed, so ``NOT (...)`` is safe and SQL's three-valued logic never leaks a NULL
into a decision.

Injection
---------
A checklist is user-supplied input. Every literal that reaches SQL goes through
:func:`sql_literal` / :func:`quote_identifier`, which quote and escape rather than
interpolate, and reject NUL bytes and non-finite floats outright. No checklist
value is ever concatenated into SQL unquoted.

Column binding
--------------
``column_expr`` maps a normalized analysis field onto the SQL expression that
produces it -- in practice the COALESCE built by
:func:`openintel_rfc.parquet_reader._duckdb_expression`, wrapped by
:func:`column_expressions` in the same cleaning
:mod:`openintel_rfc.signal_extractor` applies (trim, empty-as-absent, upper-cased
record types, epoch-millisecond timestamps). A bare column name is never inlined:
OpenINTEL carries ``dnskey_algorithm``, ``ds_algorithm``, ``cds_algorithm`` and
four more as separate columns, and binding ``algorithm`` to any one of them would
read NULL for every other record type.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from .models import (
    ConditionEvaluation,
    Decision,
    IndicatorCondition,
    IndicatorEvaluation,
    OpenINTELDictionary,
    Queryability,
    RFCChecklistDB,
    RFCChecklistEntry,
    RFCIndicator,
    SchemaCheckReport,
    TimestampCheck,
)
from .parquet_reader import _EPOCH_UNIT_BOUNDS, _duckdb_expression, resolve_column_candidates
from .ranking import RANKABLE_DECISIONS, score_match
from .signal_extractor import NUMERIC_FIELDS, PROVENANCE_FIELDS, SIGNAL_FIELDS
from .utils import PipelineError, get_logger, normalize_timestamp

__all__ = [
    "SQL_TRUE",
    "SQL_FALSE",
    "RR_TYPE_FIELD",
    "TIMESTAMP_FIELD",
    "ROLLUP_INDICATOR_ID",
    "TOTALS_RFC_ID",
    "SCANNED_DECISION",
    "MATCHED_DECISION",
    "PAIR_COLUMN",
    "MATCHED_COLUMN",
    "CompiledIndicator",
    "CompiledRFC",
    "CompiledChecklist",
    "quote_identifier",
    "quote_string",
    "sql_literal",
    "column_expressions",
    "build_column_expressions",
    "rr_type_prefilter",
    "compile_condition",
    "compile_indicator",
    "compile_partial_evidence",
    "compile_checklist",
    "scan_fields",
    "build_scan_sql",
]

LOGGER = get_logger(__name__)

SQL_TRUE = "TRUE"
SQL_FALSE = "FALSE"

#: Normalized field carrying the DNS record type. OpenINTEL calls it
#: ``response_type``; the dictionary maps the two.
RR_TYPE_FIELD = "rr_type"

#: Normalized field carrying the observation time.
TIMESTAMP_FIELD = "timestamp"

#: ``indicator_id`` of the per-RFC roll-up row emitted for every scanned row.
#: Counting only matched indicators would make a ``no_match`` decision invisible
#: in the aggregates, and ``no_match`` is exactly the row that explains *why not*.
ROLLUP_INDICATOR_ID = "*"

#: ``rfc_id`` of the two scan-total rows (``scanned`` / ``matched``). They give
#: exact row counts and prefilter selectivity without a second pass over the data.
TOTALS_RFC_ID = "*"
SCANNED_DECISION = "scanned"
MATCHED_DECISION = "matched"

#: Name of the LIST column the scan emits, one struct per aggregate contribution.
PAIR_COLUMN = "_pairs"

#: Name of the boolean column that is true when any RFC reached a rankable decision.
MATCHED_COLUMN = "_matched"

#: Epoch-unit bounds, taken from the Parquet reader so the two paths cannot drift
#: apart on unit detection. OpenINTEL exports milliseconds, but a file that has
#: been re-exported in seconds must not silently land in 1970.
_EPOCH_BOUNDS: dict[str, int] = {unit: int(bound) for bound, unit in _EPOCH_UNIT_BOUNDS}

#: Dictionary ``type`` values whose column is read as a timestamp.
_DATETIME_TYPES = frozenset({"datetime", "timestamp", "date"})

#: Dictionary ``type`` values that :func:`_duckdb_expression` already TRY_CASTs to
#: a numeric or boolean SQL type; those need no further text cleaning.
_NON_TEXT_TYPES = frozenset(
    {
        "integer",
        "int",
        "long",
        "bigint",
        "float",
        "double",
        "number",
        "boolean",
        "bool",
    }
)


# --------------------------------------------------------------------------- #
# Literals and identifiers: the only place checklist data becomes SQL text
# --------------------------------------------------------------------------- #


def quote_identifier(name: str) -> str:
    """Quote a SQL identifier, doubling any embedded double quote."""
    text = str(name)
    _reject_nul(text, "identifier")
    return '"' + text.replace('"', '""') + '"'


def quote_string(value: str) -> str:
    """Quote a value as a SQL string literal.

    DuckDB uses SQL-standard single-quoted literals with no backslash escapes, so
    doubling the quote character is a complete escape. A NUL byte is rejected
    rather than escaped: it cannot survive a VARCHAR round trip and silently
    truncating a checklist value would be worse than refusing it.
    """
    text = str(value)
    _reject_nul(text, "string literal")
    return "'" + text.replace("'", "''") + "'"


def sql_literal(value: Any) -> str:
    """Render a scalar checklist value as a SQL literal.

    Lists are not accepted here: the ``in`` operator expands them itself so that
    each element goes through the same escaping.
    """
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return SQL_TRUE if value else SQL_FALSE
    if isinstance(value, int):
        return str(int(value))
    if isinstance(value, float):
        return _double_literal(value)
    if isinstance(value, datetime):
        return "TIMESTAMP " + quote_string(normalize_timestamp(value).isoformat(sep=" "))
    if isinstance(value, str):
        return quote_string(value)
    raise PipelineError(
        f"Cannot compile a checklist value of type {type(value).__name__} into SQL: {value!r}. "
        "Conditions must compare against a scalar (string, number, boolean) or a list of them."
    )


def _double_literal(value: float) -> str:
    number = float(value)
    if math.isnan(number) or math.isinf(number):
        raise PipelineError(
            f"Refusing to compile the non-finite condition value {value!r} into SQL; "
            "no observation can compare equal to it, so the checklist is malformed."
        )
    return f"CAST({number!r} AS DOUBLE)"


def _reject_nul(text: str, what: str) -> None:
    if "\x00" in text:
        raise PipelineError(
            f"Refusing to build SQL for a {what} containing a NUL byte: {text!r}."
        )


# --------------------------------------------------------------------------- #
# Column expressions
# --------------------------------------------------------------------------- #


def _numeric(expr: str) -> str:
    """Coerce any observed value to DOUBLE the way ``matcher._as_number`` does.

    Routing through VARCHAR is deliberate. A direct ``TRY_CAST(x AS DOUBLE)``
    turns ``TRUE`` into ``1.0`` and fails to bind for a TIMESTAMP; going via text
    yields NULL for both, which is exactly what the Python helper returns.
    """
    return f"TRY_CAST(CAST({expr} AS VARCHAR) AS DOUBLE)"


def _timestamp_expression(base: str) -> str:
    """Read a timestamp column that may hold epoch integers or real timestamps.

    OpenINTEL exports epoch **milliseconds**; the local fixtures and some
    re-exports hold a native TIMESTAMP. Interpreting one as the other is the
    single most damaging silent failure this pipeline has -- every publication
    date comparison depends on it -- so the unit is derived from the magnitude of
    the value, using the same bounds :mod:`openintel_rfc.parquet_reader` uses.
    """
    number = f"TRY_CAST(CAST({base} AS VARCHAR) AS BIGINT)"
    seconds = _EPOCH_BOUNDS["s"]
    millis = _EPOCH_BOUNDS["ms"]
    micros = _EPOCH_BOUNDS["us"]
    return (
        "CASE"
        f" WHEN {number} IS NULL THEN TRY_CAST({base} AS TIMESTAMP)"
        f" WHEN abs({number}) < {seconds} THEN epoch_ms({number} * 1000)"
        f" WHEN abs({number}) < {millis} THEN epoch_ms({number})"
        f" WHEN abs({number}) < {micros} THEN make_timestamp({number})"
        f" ELSE make_timestamp({number} // 1000)"
        " END"
    )


def column_expressions(
    dictionary: OpenINTELDictionary, candidates: Mapping[str, Sequence[str]]
) -> dict[str, str]:
    """Build one SQL expression per normalized field from its candidate columns.

    ``candidates`` is what :func:`openintel_rfc.parquet_reader.resolve_column_candidates`
    returns. The COALESCE itself comes from the Parquet reader; this function only
    adds the cleaning :func:`openintel_rfc.signal_extractor.extract_signals`
    performs on the Python path, so that a value compares the same way whichever
    engine looked at it:

    * text is trimmed and an empty string is treated as absent, because the
      matcher's ``None`` means "not observed" and ``''`` is not an observation;
    * ``rr_type`` is upper-cased -- DNS record types are case-insensitive and the
      checklists spell them in upper case;
    * timestamps are decoded from epoch integers where necessary.

    Fields with no candidate column are omitted; :func:`compile_condition` treats
    an absent field as unobservable and fails every condition over it.
    """
    expressions: dict[str, str] = {}
    for name in sorted(candidates):
        columns = [str(c) for c in candidates[name]]
        if not columns:
            continue
        base = _duckdb_expression(name, columns, dictionary)
        expressions[name] = _clean_expression(name, base, dictionary)
    return expressions


def _clean_expression(
    name: str, base: str, dictionary: OpenINTELDictionary
) -> str:
    entry = dictionary.get(name)
    declared = (entry.type if entry is not None else "").strip().lower()

    if name == TIMESTAMP_FIELD or declared in _DATETIME_TYPES:
        return _timestamp_expression(base)
    if declared in _NON_TEXT_TYPES or name in NUMERIC_FIELDS:
        # `_duckdb_expression` already TRY_CASTs these to BIGINT/DOUBLE/BOOLEAN.
        return base
    cleaned = f"NULLIF(TRIM(CAST({base} AS VARCHAR)), '')"
    if name == RR_TYPE_FIELD:
        return f"UPPER({cleaned})"
    return cleaned


def build_column_expressions(
    dictionary: OpenINTELDictionary,
    needed_fields: Sequence[str],
    parquet_columns: Sequence[str],
) -> dict[str, str]:
    """Convenience wrapper: resolve candidates then build the expressions."""
    candidates = resolve_column_candidates(dictionary, needed_fields, parquet_columns)
    return column_expressions(dictionary, candidates)


# --------------------------------------------------------------------------- #
# The record-type prefilter
# --------------------------------------------------------------------------- #


def rr_type_prefilter(db: RFCChecklistDB) -> list[str]:
    """Every record type the checklist can possibly be evidenced by.

    The overwhelming majority of fDNS rows are A/AAAA/MX/NS/TXT records that no
    DNSSEC checklist can ever match. Pushing this set into the scan as
    ``WHERE rr_type IN (...)`` before any indicator is evaluated is what makes a
    multi-year run finish at all.

    Only ``in`` and ``equals`` conditions contribute: those are the operators that
    enumerate concrete record types. An ``exists`` or ``not_equals`` condition on
    ``rr_type`` would not bound the set, and no checklist in this project uses
    one; :func:`compile_checklist` warns when it finds one, because the prefilter
    would then be unsound.
    """
    values: dict[str, None] = {}
    for entry in db.rfcs:
        for indicator in entry.indicators:
            for condition in indicator.conditions:
                if condition.field != RR_TYPE_FIELD:
                    continue
                if condition.op == "in" and isinstance(
                    condition.value, (list, tuple, set, frozenset)
                ):
                    for item in condition.value:
                        if item is not None:
                            values.setdefault(str(item).strip(), None)
                elif condition.op == "equals" and condition.value is not None:
                    values.setdefault(str(condition.value).strip(), None)
    return sorted(v for v in values if v)


def _unbounded_rr_type_ops(db: RFCChecklistDB) -> list[str]:
    """Indicators whose ``rr_type`` condition the prefilter cannot bound."""
    offenders: list[str] = []
    for entry in db.rfcs:
        for indicator in entry.indicators:
            for condition in indicator.conditions:
                if condition.field != RR_TYPE_FIELD:
                    continue
                if condition.op in ("in", "equals"):
                    continue
                offenders.append(f"{entry.rfc_id}/{indicator.id} ({condition.op})")
    return sorted(set(offenders))


# --------------------------------------------------------------------------- #
# Condition compilation
# --------------------------------------------------------------------------- #


def _as_number(value: Any) -> float | None:
    """Mirror of :func:`openintel_rfc.matcher._as_number` for checklist values."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _equals_expression(observed: str, expected: Any) -> str:
    """SQL for ``matcher._values_equal(observed, expected)``.

    Always two-valued given a non-NULL ``observed``, so callers may negate it.
    """
    if expected is None:
        # `observed == None` is False for any observed value we ever reach here,
        # and neither side coerces to a number, so the comparison cannot hold.
        return SQL_FALSE
    if isinstance(expected, bool):
        # Python compares booleans only with booleans: `0 == False` must not hold,
        # and neither must `'true' == True`. `typeof` pins the observed side down.
        rendered = quote_string("true" if expected else "false")
        return (
            f"(typeof({observed}) = 'BOOLEAN' AND CAST({observed} AS VARCHAR) = {rendered})"
        )
    if isinstance(expected, (int, float)):
        # A numeric expectation is only ever satisfied numerically; the VARCHAR
        # detour inside `_numeric` already excludes booleans and timestamps.
        return f"COALESCE({_numeric(observed)} = {_double_literal(float(expected))}, FALSE)"
    if isinstance(expected, str):
        parts = [
            f"(typeof({observed}) <> 'BOOLEAN' AND CAST({observed} AS VARCHAR) "
            f"= {quote_string(expected)})"
        ]
        number = _as_number(expected)
        if number is not None:
            # "13" against an integer column: Python falls back to numeric
            # coercion of both sides, so the same fallback belongs here.
            parts.append(f"COALESCE({_numeric(observed)} = {_double_literal(number)}, FALSE)")
        return "(" + " OR ".join(parts) + ")"
    # Lists, dicts and anything else can never equal a scalar observation.
    return SQL_FALSE


def compile_condition(
    condition: IndicatorCondition, column_expr: Mapping[str, str]
) -> str:
    """Compile one condition into a two-valued SQL predicate.

    A field with no expression in ``column_expr`` cannot be observed at all, so
    every operator over it fails -- the same verdict
    :func:`openintel_rfc.matcher.evaluate_condition` reaches through
    ``field_present=False``. Absence is not evidence, in SQL as in Python.
    """
    observed = column_expr.get(condition.field)
    if observed is None:
        return SQL_FALSE

    op = condition.op
    present = f"{observed} IS NOT NULL"

    if op == "exists":
        return f"({present})"
    if op == "equals":
        return f"({present} AND {_equals_expression(observed, condition.value)})"
    if op == "not_equals":
        # A NULL observation fails this too: we never saw the field, so we cannot
        # claim it differs from anything.
        return f"({present} AND NOT {_equals_expression(observed, condition.value)})"
    if op == "in":
        if not isinstance(condition.value, (list, tuple, set, frozenset)):
            # Malformed condition; the matcher reports it and fails the condition
            # rather than raising, so the compiled form has to fail too.
            return SQL_FALSE
        items = list(condition.value)
        if not items:
            return SQL_FALSE
        alternatives = " OR ".join(_equals_expression(observed, item) for item in items)
        return f"({present} AND ({alternatives}))"
    if op == "contains":
        if condition.value is None:
            return SQL_FALSE
        needle = quote_string(str(condition.value))
        # Substring for text; anything else is the matcher's type-mismatch branch
        # and fails on the type rather than on the value. List-valued observations
        # do not occur through the Parquet reader, which projects scalars only.
        return (
            f"({present} AND typeof({observed}) = 'VARCHAR' "
            f"AND contains(CAST({observed} AS VARCHAR), {needle}))"
        )
    if op in ("greater_or_equal", "less_or_equal"):
        number = _as_number(condition.value)
        if number is None:
            return SQL_FALSE
        symbol = ">=" if op == "greater_or_equal" else "<="
        return (
            f"({present} AND COALESCE({_numeric(observed)} {symbol} "
            f"{_double_literal(number)}, FALSE))"
        )

    # Unreachable while `ConditionOp` is a closed Literal, but the matcher treats
    # an unknown operator as failed rather than ignored, and so does this.
    return SQL_FALSE


def compile_indicator(
    indicator: RFCIndicator,
    column_expr: Mapping[str, str],
    queryability: Queryability = "queryable",
) -> str:
    """Compile one indicator's conditions, ANDed, into a SQL predicate.

    A ``non_queryable`` indicator compiles to FALSE and is separately marked
    skipped: it was never tested, so it must neither earn weight nor incur a
    penalty. :func:`compile_checklist` carries that distinction into the decision
    table.
    """
    if queryability == "non_queryable":
        return SQL_FALSE
    if not indicator.conditions:
        return SQL_TRUE  # mirrors `all([])`; the model forbids it in practice
    parts = [compile_condition(c, column_expr) for c in indicator.conditions]
    return "(" + " AND ".join(parts) + ")"


def compile_partial_evidence(
    indicator: RFCIndicator,
    column_expr: Mapping[str, str],
    queryability: Queryability = "queryable",
) -> str:
    """Compile "partly satisfied, partly untestable" for one indicator.

    :func:`openintel_rfc.ranking._has_untestable_partial_evidence` distinguishes a
    required indicator that was *contradicted* from one that agreed with the
    observation as far as the observation goes and ran out of fields. The second
    is weaker than a contradiction -- nothing rules the RFC out -- and lands on
    ``partial_match`` instead of ``no_match``. Reproducing that here is what keeps
    the CDS-with-null-algorithm case (contract example 8) out of ``no_match``.

    An indicator with a single condition can never be partly anything, so it
    compiles to FALSE.
    """
    if queryability == "non_queryable" or len(indicator.conditions) < 2:
        return SQL_FALSE
    passed = " OR ".join(compile_condition(c, column_expr) for c in indicator.conditions)
    absent = " OR ".join(
        SQL_TRUE if column_expr.get(c.field) is None else f"({column_expr[c.field]} IS NULL)"
        for c in indicator.conditions
    )
    return f"(({passed}) AND ({absent}))"


# --------------------------------------------------------------------------- #
# Compiled checklist
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CompiledIndicator:
    """One indicator, with the SQL that decides whether a row satisfies it."""

    rfc_id: str
    indicator_id: str
    description: str
    required: bool
    weight: float
    ambiguous: bool
    queryability: Queryability
    skipped: bool
    condition_count: int
    fields_used: tuple[str, ...]
    match_sql: str
    partial_sql: str
    match_alias: str
    partial_alias: str


@dataclass(frozen=True)
class CompiledRFC:
    """One RFC: its indicators, its cutoff, and its evidence-to-decision table."""

    rfc_id: str
    title: str
    publication_date: datetime
    specificity: str
    indicators: tuple[CompiledIndicator, ...]
    decision_alias: str
    timestamp_valid_sql: str
    pattern_sql: str
    decision_sql: str
    #: pattern integer -> decision, computed by `ranking.score_match` itself.
    decision_table: Mapping[int, Decision]


@dataclass(frozen=True)
class CompiledChecklist:
    """Everything :func:`build_scan_sql` needs to emit one partition's scan."""

    checklist_version: str
    rfcs: tuple[CompiledRFC, ...]
    fields: tuple[str, ...]
    prefilter: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    @property
    def indicators(self) -> tuple[CompiledIndicator, ...]:
        return tuple(
            indicator for rfc in self.rfcs for indicator in rfc.indicators
        )

    def rfc(self, rfc_id: str) -> CompiledRFC | None:
        for entry in self.rfcs:
            if entry.rfc_id == rfc_id:
                return entry
        return None


def _queryability_for(
    indicator: RFCIndicator, schema_report: SchemaCheckReport | None
) -> Queryability:
    """Same rule as :func:`openintel_rfc.matcher._queryability_for`."""
    if schema_report is None:
        return "queryable"
    status = schema_report.status_for(indicator.id)
    return status if status is not None else "queryable"


def _synthetic_evaluation(
    indicator: CompiledIndicator, code: int
) -> IndicatorEvaluation:
    """The evaluation shape a given evidence code stands for.

    Only the attributes :func:`openintel_rfc.ranking.score_match` reads are
    populated: weights, flags, ``matched``/``skipped``, and -- for code 2 -- one
    passing and one untestable condition, which is the minimum shape
    ``_has_untestable_partial_evidence`` recognises.
    """
    conditions: list[ConditionEvaluation] = []
    if code == 2:
        conditions = [
            ConditionEvaluation(field="", op="exists", passed=True, field_present=True),
            ConditionEvaluation(field="", op="exists", passed=False, field_present=False),
        ]
    return IndicatorEvaluation(
        indicator_id=indicator.indicator_id,
        indicator_description=indicator.description,
        required=indicator.required,
        weight=indicator.weight,
        ambiguous=indicator.ambiguous,
        queryability=indicator.queryability,
        matched=code == 1,
        skipped=indicator.skipped,
        conditions=conditions,
        missing_fields=[],
        explanation="",
    )


def _evidence_codes(indicator: CompiledIndicator) -> tuple[int, ...]:
    """Which evidence codes this indicator can actually produce."""
    if indicator.skipped:
        return (0,)
    if indicator.condition_count >= 2:
        return (0, 1, 2)
    return (0, 1)


def _decision_table(
    rfc: RFCChecklistEntry, indicators: Sequence[CompiledIndicator]
) -> dict[int, Decision]:
    """Ask the real scorer what every reachable evidence pattern means.

    This is the whole reason no decision logic is written in SQL: the table is
    produced by :func:`openintel_rfc.ranking.score_match`, so the SQL path cannot
    drift from the Python path without the Python path changing first.
    """
    published = normalize_timestamp(rfc.publication_date)
    table: dict[int, Decision] = {}
    base = 3 ** len(indicators)
    for combination in itertools.product(*(_evidence_codes(i) for i in indicators)):
        pattern = sum(code * (3**index) for index, code in enumerate(combination))
        for valid in (False, True):
            observed = published + timedelta(days=1 if valid else -1)
            check = TimestampCheck(
                observation_timestamp=observed,
                rfc_publication_date=published,
                valid=valid,
                days_after_publication=1 if valid else -1,
                explanation="",
            )
            evaluations = [
                _synthetic_evaluation(indicator, code)
                for indicator, code in zip(indicators, combination)
            ]
            _breakdown, decision = score_match(rfc, evaluations, check)
            table[pattern + (base if valid else 0)] = decision
    return table


def _pattern_sql(indicators: Sequence[CompiledIndicator], timestamp_valid: str) -> str:
    """The evidence pattern as a base-3 integer, timestamp validity on top."""
    terms: list[str] = []
    for index, indicator in enumerate(indicators):
        if indicator.skipped:
            continue  # its code is always 0, so the term contributes nothing
        weight = 3**index
        code = (
            f"CASE WHEN {quote_identifier(indicator.match_alias)} THEN 1"
            f" WHEN {quote_identifier(indicator.partial_alias)} THEN 2 ELSE 0 END"
        )
        terms.append(code if weight == 1 else f"{weight} * ({code})")
    terms.append(
        f"{3 ** len(indicators)} * (CASE WHEN {timestamp_valid} THEN 1 ELSE 0 END)"
    )
    return "(" + " + ".join(terms) + ")"


def _decision_sql(pattern: str, table: Mapping[int, Decision]) -> str:
    """Render the precomputed pattern -> decision table as a compact CASE."""
    grouped: dict[str, list[int]] = {}
    for value, decision in sorted(table.items()):
        grouped.setdefault(decision, []).append(value)
    # The largest bucket becomes ELSE, which keeps the emitted SQL small without
    # changing the mapping.
    fallback = max(sorted(grouped), key=lambda name: (len(grouped[name]), name))
    branches = [
        f"WHEN {pattern} IN ({', '.join(str(v) for v in grouped[name])}) "
        f"THEN {quote_string(name)}"
        for name in sorted(grouped)
        if name != fallback
    ]
    if not branches:
        return quote_string(fallback)
    return "CASE " + " ".join(branches) + f" ELSE {quote_string(fallback)} END"


def compile_checklist(
    db: RFCChecklistDB,
    column_expr: Mapping[str, str],
    schema_report: SchemaCheckReport | None = None,
) -> CompiledChecklist:
    """Compile every RFC in ``db`` into scan-time SQL.

    ``schema_report`` supplies each indicator's queryability, exactly as
    :func:`openintel_rfc.matcher.match_all` uses it: a ``non_queryable`` indicator
    is marked skipped and never earns or costs anything. Passing ``None`` treats
    every indicator as queryable, which over-states what the corpus can answer and
    is only appropriate in tests.

    Warnings are collected rather than raised: a field the corpus does not carry
    is a fact about the corpus, and the run should say so and continue.
    """
    if not db.rfcs:
        raise PipelineError(
            "The checklist database contains no RFCs, so there is nothing to compile."
        )

    warnings: list[str] = []
    compiled_rfcs: list[CompiledRFC] = []
    used_fields: dict[str, None] = {}
    missing_fields: dict[str, list[str]] = {}
    counter = itertools.count()

    timestamp_expr = column_expr.get(TIMESTAMP_FIELD)
    if timestamp_expr is None:
        raise PipelineError(
            "No column supplies the normalized 'timestamp' field, so the RFC "
            "publication-date cutoff cannot be evaluated. Refusing to compile a scan "
            "that would report adoption without checking when it was observed."
        )

    for entry in sorted(db.rfcs, key=lambda item: item.rfc_id):
        indicators: list[CompiledIndicator] = []
        for indicator in entry.indicators:
            queryability = _queryability_for(indicator, schema_report)
            index = next(counter)
            for name in indicator.fields_used:
                used_fields.setdefault(name, None)
                if queryability != "non_queryable" and name not in column_expr:
                    missing_fields.setdefault(name, []).append(
                        f"{entry.rfc_id}/{indicator.id}"
                    )
            indicators.append(
                CompiledIndicator(
                    rfc_id=entry.rfc_id,
                    indicator_id=indicator.id,
                    description=indicator.description,
                    required=indicator.required,
                    weight=float(indicator.weight),
                    ambiguous=bool(indicator.ambiguous),
                    queryability=queryability,
                    skipped=queryability == "non_queryable",
                    condition_count=len(indicator.conditions),
                    fields_used=tuple(indicator.fields_used),
                    match_sql=compile_indicator(indicator, column_expr, queryability),
                    partial_sql=compile_partial_evidence(
                        indicator, column_expr, queryability
                    ),
                    match_alias=f"_ind_{index:04d}",
                    partial_alias=f"_par_{index:04d}",
                )
            )

        published = normalize_timestamp(entry.publication_date)
        timestamp_valid = (
            f"({quote_identifier(TIMESTAMP_FIELD)} >= "
            f"TIMESTAMP {quote_string(published.isoformat(sep=' '))})"
        )
        table = _decision_table(entry, indicators)
        pattern = _pattern_sql(indicators, timestamp_valid)
        compiled_rfcs.append(
            CompiledRFC(
                rfc_id=entry.rfc_id,
                title=entry.title,
                publication_date=published,
                specificity=entry.specificity,
                indicators=tuple(indicators),
                decision_alias=f"_dec_{len(compiled_rfcs):04d}",
                timestamp_valid_sql=timestamp_valid,
                pattern_sql=pattern,
                decision_sql=_decision_sql(pattern, table),
                decision_table=dict(table),
            )
        )

    for name in sorted(missing_fields):
        users = sorted(set(missing_fields[name]))
        warnings.append(
            f"Field '{name}' has no column in this corpus but is referenced by "
            f"{len(users)} evaluable indicator(s) ({', '.join(users)}); every condition "
            "over it compiles to FALSE, so those indicators can never match here."
        )

    unbounded = _unbounded_rr_type_ops(db)
    if unbounded:
        warnings.append(
            "The record-type prefilter is derived from 'in'/'equals' conditions only, but "
            f"{', '.join(unbounded)} constrain rr_type with another operator; rows those "
            "indicators could match may be filtered out before evaluation."
        )

    prefilter = rr_type_prefilter(db)
    if not prefilter:
        warnings.append(
            "No rr_type literal appears in any checklist condition, so no record-type "
            "prefilter could be derived and every row of the corpus will be evaluated."
        )

    return CompiledChecklist(
        checklist_version=db.checklist_version,
        rfcs=tuple(compiled_rfcs),
        fields=tuple(sorted(used_fields)),
        prefilter=tuple(prefilter),
        warnings=tuple(warnings),
    )


# --------------------------------------------------------------------------- #
# The scan
# --------------------------------------------------------------------------- #


def scan_fields(
    compiled: CompiledChecklist, column_expr: Mapping[str, str]
) -> list[str]:
    """Normalized fields the scan projects, in a fixed order.

    Provenance always comes first and always in full: a run needs the timestamp,
    the domain, the zone and the source whether or not an indicator mentions them.
    """
    wanted: dict[str, None] = {}
    for name in (*PROVENANCE_FIELDS, *SIGNAL_FIELDS):
        wanted.setdefault(name, None)
    for name in compiled.fields:
        wanted.setdefault(name, None)
    return [name for name in wanted if name in column_expr]


def _read_parquet_clause(uris: Sequence[str]) -> str:
    if not uris:
        raise PipelineError("build_scan_sql requires at least one Parquet URI.")
    listed = ", ".join(quote_string(str(uri)) for uri in uris)
    # `union_by_name` because OpenINTEL measurement generations do not all carry
    # the same columns; `hive_partitioning` because source/year/month/day live in
    # the object path rather than inside the files.
    return f"read_parquet([{listed}], union_by_name = true, hive_partitioning = true)"


def _pair_struct(rfc_id: str, indicator_id: str, decision: str, keep: str) -> str:
    return (
        "{"
        f"'rfc_id': {quote_string(rfc_id)}, "
        f"'indicator_id': {quote_string(indicator_id)}, "
        f"'decision': {decision}, "
        f"'keep': {keep}"
        "}"
    )


def build_scan_sql(
    uris: Sequence[str],
    column_expr: Mapping[str, str],
    compiled: CompiledChecklist,
    *,
    prefilter: Sequence[str],
    limit: int | None = None,
) -> str:
    """Build the row-level scan for one partition.

    The emitted query does, in one pass:

    1. the record-type prefilter, in the ``WHERE`` clause so DuckDB applies it
       inside ``read_parquet`` and no indicator expression is ever evaluated for
       an A/AAAA/MX/NS/TXT row;
    2. COALESCE alias resolution into normalized fields;
    3. one boolean per indicator, plus the "partly untestable" flag the decision
       rules need;
    4. the publication-date cutoff per RFC, as ``timestamp >= publication``;
    5. one ``decision`` per RFC, read out of the table
       :func:`openintel_rfc.ranking.score_match` produced at compile time.

    The result carries one row per input row, with a ``_pairs`` LIST of
    ``{rfc_id, indicator_id, decision}`` structs that the caller unnests and
    groups. Each RFC contributes a roll-up entry (``indicator_id = '*'``) for
    every row, so decisions that match no indicator -- ``no_match`` above all --
    are counted rather than vanishing, plus one entry per indicator that matched.
    Two further entries under ``rfc_id = '*'`` carry the scan totals, which is
    where the prefilter's selectivity comes from without a second pass.

    Rows whose timestamp cannot be decoded are dropped, exactly as
    :func:`openintel_rfc.signal_extractor.extract_signals` drops them, so the two
    engines see the same population.
    """
    fields = scan_fields(compiled, column_expr)
    if TIMESTAMP_FIELD not in fields:
        raise PipelineError(
            "The scan cannot be built without a 'timestamp' expression: the "
            "publication-date cutoff has nothing to compare against."
        )

    projection: list[str] = [
        f"{column_expr[name]} AS {quote_identifier(name)}" for name in fields
    ]

    # Lateral aliases keep each condition expression in the query exactly twice
    # (once for the match, once for the partial-evidence flag) instead of once per
    # place a decision is referenced.
    for rfc in compiled.rfcs:
        for indicator in rfc.indicators:
            projection.append(
                f"{indicator.match_sql} AS {quote_identifier(indicator.match_alias)}"
            )
            projection.append(
                f"{indicator.partial_sql} AS {quote_identifier(indicator.partial_alias)}"
            )
    for rfc in compiled.rfcs:
        projection.append(
            f"{rfc.decision_sql} AS {quote_identifier(rfc.decision_alias)}"
        )

    rankable = ", ".join(quote_string(name) for name in RANKABLE_DECISIONS)
    matched_expr = " OR ".join(
        f"{quote_identifier(rfc.decision_alias)} IN ({rankable})" for rfc in compiled.rfcs
    )
    projection.append(
        f"COALESCE({matched_expr}, FALSE) AS {quote_identifier(MATCHED_COLUMN)}"
    )

    structs: list[str] = []
    for rfc in compiled.rfcs:
        decision = quote_identifier(rfc.decision_alias)
        structs.append(_pair_struct(rfc.rfc_id, ROLLUP_INDICATOR_ID, decision, SQL_TRUE))
        for indicator in rfc.indicators:
            structs.append(
                _pair_struct(
                    rfc.rfc_id,
                    indicator.indicator_id,
                    decision,
                    quote_identifier(indicator.match_alias),
                )
            )
    structs.append(
        _pair_struct(
            TOTALS_RFC_ID, ROLLUP_INDICATOR_ID, quote_string(SCANNED_DECISION), SQL_TRUE
        )
    )
    structs.append(
        _pair_struct(
            TOTALS_RFC_ID,
            ROLLUP_INDICATOR_ID,
            quote_string(MATCHED_DECISION),
            quote_identifier(MATCHED_COLUMN),
        )
    )
    projection.append(
        "list_filter([\n    "
        + ",\n    ".join(structs)
        + f"\n  ], pair -> pair.keep) AS {quote_identifier(PAIR_COLUMN)}"
    )

    timestamp_expr = column_expr[TIMESTAMP_FIELD]
    conditions: list[str] = []
    values = [str(v).strip() for v in prefilter if str(v).strip()]
    rr_type_expr = column_expr.get(RR_TYPE_FIELD)
    if values and rr_type_expr is not None:
        listed = ", ".join(quote_string(value) for value in sorted(set(values)))
        conditions.append(f"{rr_type_expr} IN ({listed})")
    conditions.append(f"({timestamp_expr}) IS NOT NULL")

    statement = (
        "SELECT\n  "
        + ",\n  ".join(projection)
        + "\nFROM "
        + _read_parquet_clause(uris)
        + "\nWHERE "
        + "\n  AND ".join(conditions)
    )
    if limit is not None:
        if int(limit) < 0:
            raise PipelineError(f"limit must be >= 0, got {limit}.")
        statement += f"\nLIMIT {int(limit)}"
    return statement
