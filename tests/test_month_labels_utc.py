"""Month labels must be UTC whatever the host time zone.

A server run on a UTC-negative host labelled every 00:00-UTC snapshot of day 1
with the previous month (reverse corpus shifted by one month against the panel
run). These tests pin the fix.
"""
import duckdb

from openintel_rfc.timeline_extract import _timestamp_expression

MIDNIGHT_UTC_2009_04_01_MS = 1238544000 * 1000


def _month(tz: str) -> str:
    con = duckdb.connect()
    con.execute(f"SET TimeZone='{tz}'")
    con.execute(f"CREATE TABLE t AS SELECT CAST({MIDNIGHT_UTC_2009_04_01_MS} AS BIGINT) AS ts")
    return con.execute(f"SELECT {_timestamp_expression(['ts'])} FROM t").fetchone()[0]


def test_month_label_is_utc_on_a_negative_offset_host():
    assert _month("America/New_York") == "2009-04"


def test_month_label_is_utc_on_a_positive_offset_host():
    assert _month("Asia/Tokyo") == "2009-04"


def test_extraction_connection_pins_utc():
    import inspect

    from openintel_rfc import scale_runner, timeline_extract

    assert "SET TimeZone='UTC'" in inspect.getsource(timeline_extract)
    assert "SET TimeZone='UTC'" in inspect.getsource(scale_runner._open_connection)
