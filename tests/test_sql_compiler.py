"""Tests for :mod:`openintel_rfc.sql_compiler`.

The centre of this file is :func:`test_operator_matches_python_matcher`, a
differential test: every operator is compiled to SQL, executed by DuckDB against
a typed one-row relation, and compared with what
:func:`openintel_rfc.matcher.evaluate_condition` says about the *same* value.
The two implementations have to agree on every cell of that grid, including the
awkward ones -- NULLs, booleans against numbers, numeric strings, and type
mismatches that must fail rather than raise.

The other half of the file is about the two things a compiler of user-supplied
input must never get wrong: it must not let a checklist value escape its quotes,
and it must not silently bind a normalized field to one raw column when OpenINTEL
spreads that field over seven of them.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import duckdb
import pytest

from openintel_rfc import sql_compiler
from openintel_rfc.matcher import evaluate_condition
from openintel_rfc.models import IndicatorCondition, ObservedSignal, RFCChecklistDB
from openintel_rfc.parquet_reader import describe_parquet
from openintel_rfc.schema_checker import queryable_field_names
from openintel_rfc.signal_extractor import SIGNAL_FIELDS
from openintel_rfc.utils import PipelineError

FIELD = "probe"
COLUMN_EXPR = {FIELD: '"v"'}


# --------------------------------------------------------------------------- #
# Differential operator test
# --------------------------------------------------------------------------- #

#: (SQL literal, equivalent Python value). The SQL side is explicitly cast so
#: that ``typeof`` sees the type an OpenINTEL column would really have.
OBSERVED_VALUES: tuple[tuple[str, Any], ...] = (
    ("CAST(NULL AS BIGINT)", None),
    ("CAST(NULL AS VARCHAR)", None),
    ("CAST('CDS' AS VARCHAR)", "CDS"),
    ("CAST('CDNSKEY' AS VARCHAR)", "CDNSKEY"),
    ("CAST('13' AS VARCHAR)", "13"),
    ("CAST('ECDSAP256SHA256' AS VARCHAR)", "ECDSAP256SHA256"),
    ("CAST(0 AS BIGINT)", 0),
    ("CAST(1 AS BIGINT)", 1),
    ("CAST(2 AS BIGINT)", 2),
    ("CAST(13 AS BIGINT)", 13),
    ("CAST(13.5 AS DOUBLE)", 13.5),
    ("TRUE", True),
    ("FALSE", False),
    ("TIMESTAMP '2018-05-01 00:00:00'", datetime(2018, 5, 1)),
)

#: Every operator, with values chosen to hit both the ordinary and the awkward
#: branch of each one.
CONDITIONS: tuple[tuple[str, Any], ...] = (
    ("exists", None),
    ("equals", "CDS"),
    ("equals", 0),
    ("equals", 13),
    ("equals", "13"),
    ("equals", True),
    ("equals", None),
    ("not_equals", 1),
    ("not_equals", "CDS"),
    ("not_equals", None),
    ("not_equals", True),
    ("in", ["CDS", "CDNSKEY"]),
    ("in", [13, 14]),
    ("in", [0]),
    ("in", "not-a-list"),
    ("in", []),
    ("contains", "CD"),
    ("contains", "ECDSAP256SHA256"),
    ("contains", 3),
    ("contains", None),
    ("greater_or_equal", 1),
    ("greater_or_equal", "abc"),
    ("less_or_equal", 2),
    ("less_or_equal", 13.5),
)


@pytest.fixture(scope="module")
def connection():
    conn = duckdb.connect(database=":memory:")
    yield conn
    conn.close()


def _sql_result(conn, condition: IndicatorCondition, literal: str) -> bool:
    expression = sql_compiler.compile_condition(condition, COLUMN_EXPR)
    statement = f"SELECT ({expression}) AS passed FROM (SELECT {literal} AS v)"
    value = conn.execute(statement).fetchone()[0]
    # A compiled condition must never evaluate to NULL: three-valued logic
    # leaking into a decision is exactly the bug this assertion exists to catch.
    assert value is not None, f"{condition.op} returned NULL for {literal}: {statement}"
    return bool(value)


@pytest.mark.parametrize("op,expected", CONDITIONS, ids=lambda v: str(v)[:24])
@pytest.mark.parametrize("literal,observed", OBSERVED_VALUES, ids=lambda v: str(v)[:24])
def test_operator_matches_python_matcher(connection, op, expected, literal, observed):
    """SQL and the Python matcher must reach the same verdict on the same value."""
    condition = IndicatorCondition(field=FIELD, op=op, value=expected)
    signal = ObservedSignal(
        signal_id="sig_0001", timestamp=datetime(2020, 1, 1), fields={FIELD: observed}
    )
    assert _sql_result(connection, condition, literal) is evaluate_condition(
        condition, signal
    ).passed


def test_null_fails_every_operator(connection):
    """Absence is not evidence -- including for ``not_equals``."""
    for op, expected in CONDITIONS:
        condition = IndicatorCondition(field=FIELD, op=op, value=expected)
        assert _sql_result(connection, condition, "CAST(NULL AS VARCHAR)") is False
        assert _sql_result(connection, condition, "CAST(NULL AS BIGINT)") is False


def test_missing_field_compiles_to_false():
    """A field the corpus does not carry fails every operator, never errors."""
    for op in ("exists", "equals", "not_equals", "in", "contains", "greater_or_equal"):
        condition = IndicatorCondition(field="absent", op=op, value=1)
        assert sql_compiler.compile_condition(condition, COLUMN_EXPR) == sql_compiler.SQL_FALSE


def test_numeric_strings_are_coerced(connection):
    condition = IndicatorCondition(field=FIELD, op="greater_or_equal", value=2)
    assert _sql_result(connection, condition, "CAST(' 13 ' AS VARCHAR)") is True


def test_type_mismatch_fails_without_raising(connection):
    """A comparison that cannot be made fails; it does not abort the scan."""
    condition = IndicatorCondition(field=FIELD, op="greater_or_equal", value=2)
    assert _sql_result(connection, condition, "CAST('not-a-number' AS VARCHAR)") is False
    contains = IndicatorCondition(field=FIELD, op="contains", value="1")
    assert _sql_result(connection, contains, "CAST(13 AS BIGINT)") is False


def test_boolean_is_not_a_number(connection):
    """``0 == False`` must not hold: they are different claims about a record."""
    condition = IndicatorCondition(field=FIELD, op="equals", value=0)
    assert _sql_result(connection, condition, "FALSE") is False
    condition = IndicatorCondition(field=FIELD, op="equals", value=True)
    assert _sql_result(connection, condition, "CAST(1 AS BIGINT)") is False
    assert _sql_result(connection, condition, "TRUE") is True


# --------------------------------------------------------------------------- #
# Injection
# --------------------------------------------------------------------------- #

INJECTIONS: tuple[str, ...] = (
    "CDS'); DROP TABLE victim; --",
    "'; DROP TABLE victim; --",
    "' OR 1=1 --",
    'CDS" ; DROP TABLE victim; --',
    "\\'; DROP TABLE victim; --",
    "'||(SELECT 1)||'",
)


@pytest.mark.parametrize("payload", INJECTIONS)
def test_malicious_checklist_value_cannot_break_out(payload):
    """A checklist is user-supplied input; no value may become SQL syntax.

    Each payload is compiled through every operator that carries a value and
    executed. The table it tries to drop has to survive, the statement has to
    parse, and the condition has to be a plain FALSE -- a payload that made the
    query fail to parse would also be a defect, because a malformed checklist
    must be reported, not turned into a syntax error.
    """
    conn = duckdb.connect(database=":memory:")
    try:
        conn.execute("CREATE TABLE victim AS SELECT 1 AS keep")
        for op in ("equals", "not_equals", "contains"):
            condition = IndicatorCondition(field=FIELD, op=op, value=payload)
            expression = sql_compiler.compile_condition(condition, COLUMN_EXPR)
            conn.execute(f"SELECT ({expression}) FROM (SELECT 'CDS' AS v)").fetchall()
        listed = IndicatorCondition(field=FIELD, op="in", value=["CDS", payload])
        expression = sql_compiler.compile_condition(listed, COLUMN_EXPR)
        conn.execute(f"SELECT ({expression}) FROM (SELECT 'CDS' AS v)").fetchall()
        assert conn.execute("SELECT count(*) FROM victim").fetchone()[0] == 1
    finally:
        conn.close()


def test_quote_string_doubles_quotes():
    assert sql_compiler.quote_string("O'Brien") == "'O''Brien'"
    assert sql_compiler.quote_identifier('we"ird') == '"we""ird"'


def test_nul_byte_is_refused():
    with pytest.raises(PipelineError):
        sql_compiler.quote_string("bad\x00value")


def test_non_finite_number_is_refused():
    with pytest.raises(PipelineError):
        sql_compiler.sql_literal(float("nan"))
    with pytest.raises(PipelineError):
        sql_compiler.sql_literal(float("inf"))


def test_unsupported_literal_type_is_refused():
    with pytest.raises(PipelineError):
        sql_compiler.sql_literal({"not": "scalar"})


# --------------------------------------------------------------------------- #
# Prefilter
# --------------------------------------------------------------------------- #


def test_rr_type_prefilter_is_sorted_deduped_and_dnssec_only(checklist_db: RFCChecklistDB):
    prefilter = sql_compiler.rr_type_prefilter(checklist_db)
    assert prefilter == [
        "CDNSKEY",
        "CDS",
        "DNSKEY",
        "DS",
        "NSEC",
        "NSEC3",
        "NSEC3PARAM",
        "RRSIG",
    ]
    assert prefilter == sorted(set(prefilter))
    for excluded in ("A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME"):
        assert excluded not in prefilter


def test_prefilter_covers_equals_conditions(checklist_db: RFCChecklistDB):
    """RFC 7344's ``rr_type equals CDS`` must contribute, not only ``in`` lists."""
    equals_fields = [
        condition.value
        for rfc in checklist_db.rfcs
        for indicator in rfc.indicators
        for condition in indicator.conditions
        if condition.field == "rr_type" and condition.op == "equals"
    ]
    assert equals_fields, "the fixture checklist should exercise the 'equals' branch"
    prefilter = sql_compiler.rr_type_prefilter(checklist_db)
    for value in equals_fields:
        assert value in prefilter


# --------------------------------------------------------------------------- #
# Column expressions
# --------------------------------------------------------------------------- #


def test_column_expression_coalesces_every_candidate(dictionary):
    """``algorithm`` must never bind to one OpenINTEL column.

    OpenINTEL populates only the column matching a row's record type, so binding
    ``algorithm`` to ``dnskey_algorithm`` would read NULL for every CDS row -- and
    a CDS delete signal is the strongest RFC 8078 evidence there is.
    """
    columns = [
        "dnskey_algorithm",
        "ds_algorithm",
        "rrsig_algorithm",
        "cds_algorithm",
        "cdnskey_algorithm",
        "response_type",
        "timestamp",
    ]
    expressions = sql_compiler.build_column_expressions(
        dictionary, ["algorithm", "rr_type", "timestamp"], columns
    )
    algorithm = expressions["algorithm"]
    assert algorithm.startswith("COALESCE(")
    for name in ("dnskey_algorithm", "ds_algorithm", "cds_algorithm", "cdnskey_algorithm"):
        assert f'"{name}"' in algorithm
    assert expressions["rr_type"] != '"response_type"'
    assert "response_type" in expressions["rr_type"]


def test_epoch_millisecond_timestamps_are_decoded(dictionary):
    """OpenINTEL timestamps are epoch milliseconds, not nanoseconds or seconds."""
    expressions = sql_compiler.build_column_expressions(
        dictionary, ["timestamp"], ["timestamp"]
    )
    conn = duckdb.connect(database=":memory:")
    try:
        statement = (
            f"SELECT {expressions['timestamp']} FROM "
            "(SELECT CAST(1525132800000 AS BIGINT) AS timestamp)"
        )
        assert conn.execute(statement).fetchone()[0] == datetime(2018, 5, 1)
        statement = (
            f"SELECT {expressions['timestamp']} FROM "
            "(SELECT TIMESTAMP '2018-05-01 03:00:00' AS timestamp)"
        )
        assert conn.execute(statement).fetchone()[0] == datetime(2018, 5, 1, 3)
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Compiled checklist and scan
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def compiled_pair(request):
    """The shipped checklist compiled against the sample Parquet schema."""
    checklist_db = request.getfixturevalue("checklist_db")
    dictionary = request.getfixturevalue("dictionary")
    schema_report = request.getfixturevalue("schema_report")
    parquet_path = request.getfixturevalue("sample_parquet_path")

    columns = [c["name"] for c in describe_parquet(parquet_path)["columns"]]
    needed = sorted(
        set(queryable_field_names(schema_report))
        | {"timestamp", "domain", "zone", "source", "measurement_id"}
        | set(SIGNAL_FIELDS)
    )
    column_expr = sql_compiler.build_column_expressions(dictionary, needed, columns)
    compiled = sql_compiler.compile_checklist(checklist_db, column_expr, schema_report)
    return column_expr, compiled


def test_non_queryable_indicator_compiles_to_false(compiled_pair):
    _column_expr, compiled = compiled_pair
    skipped = [i for i in compiled.indicators if i.skipped]
    assert [i.indicator_id for i in skipped] == ["rfc8624_validator_algorithm_support"]
    assert skipped[0].match_sql == sql_compiler.SQL_FALSE


def test_decision_tables_only_contain_real_decisions(compiled_pair):
    _column_expr, compiled = compiled_pair
    legal = {
        "valid_match",
        "partial_match",
        "no_match",
        "timestamp_invalid",
        "non_queryable",
        "ambiguous",
    }
    for rfc in compiled.rfcs:
        assert rfc.decision_table
        assert set(rfc.decision_table.values()) <= legal


def test_compile_checklist_requires_a_timestamp(checklist_db):
    with pytest.raises(PipelineError, match="publication-date cutoff"):
        sql_compiler.compile_checklist(checklist_db, {"rr_type": '"rr_type"'})


def test_build_scan_sql_pushes_the_prefilter(compiled_pair, sample_parquet_path):
    column_expr, compiled = compiled_pair
    statement = sql_compiler.build_scan_sql(
        [sample_parquet_path.as_posix()],
        column_expr,
        compiled,
        prefilter=compiled.prefilter,
    )
    assert "WHERE" in statement
    where = statement.split("WHERE", 1)[1]
    for value in compiled.prefilter:
        assert f"'{value}'" in where
    assert "IS NOT NULL" in where  # the timestamp guard


def test_build_scan_sql_rejects_no_uris(compiled_pair):
    column_expr, compiled = compiled_pair
    with pytest.raises(PipelineError):
        sql_compiler.build_scan_sql([], column_expr, compiled, prefilter=[])


def test_build_scan_sql_honours_limit(compiled_pair, sample_parquet_path):
    column_expr, compiled = compiled_pair
    statement = sql_compiler.build_scan_sql(
        [sample_parquet_path.as_posix()],
        column_expr,
        compiled,
        prefilter=compiled.prefilter,
        limit=7,
    )
    conn = duckdb.connect(database=":memory:")
    try:
        assert conn.execute(f"SELECT count(*) FROM ({statement})").fetchone()[0] == 7
    finally:
        conn.close()


def test_scan_emits_scan_totals(compiled_pair, sample_parquet_path):
    """The two ``rfc_id = '*'`` rows are what report the prefilter's selectivity."""
    column_expr, compiled = compiled_pair
    statement = sql_compiler.build_scan_sql(
        [sample_parquet_path.as_posix()],
        column_expr,
        compiled,
        prefilter=compiled.prefilter,
    )
    conn = duckdb.connect(database=":memory:")
    try:
        rows = conn.execute(
            f"""
            SELECT u.pair.decision AS decision, count(*) AS n
            FROM ({statement}) s, UNNEST(s._pairs) AS u(pair)
            WHERE u.pair.rfc_id = '{sql_compiler.TOTALS_RFC_ID}'
            GROUP BY 1 ORDER BY 1
            """
        ).fetchall()
    finally:
        conn.close()
    totals = dict(rows)
    assert totals[sql_compiler.SCANNED_DECISION] == 73
    assert totals[sql_compiler.MATCHED_DECISION] <= totals[sql_compiler.SCANNED_DECISION]
