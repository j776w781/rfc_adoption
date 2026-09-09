"""Pin docs/releases_vs_adoption.md to the analysis output.

Two measurement traps live in this analysis and both produce confident-looking
numbers. A month in which a value is absent is 0%, not missing -- dropping those
leaves the series starting at first sighting and deletes the entire before-period
an event study needs. And a bounded share series must decelerate near its
ceiling, so an event late in a curve inherits a negative delta it did not cause.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "analysis" / "release_vs_adoption.json"
DOC = ROOT / "docs" / "releases_vs_adoption.md"

pytestmark = pytest.mark.skipif(
    not OUT.exists(), reason="run scripts/release_vs_adoption.py first")


@pytest.fixture(scope="module")
def a() -> dict:
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_event_studies_have_a_real_before_period(a):
    """If absent months were dropped, n_before collapses to zero everywhere."""
    assert a["event_studies"], "expected at least one event study"
    for e in a["event_studies"]:
        assert e["n_before"] >= 3, e


def test_late_curve_events_are_flagged(a):
    for e in a["event_studies"]:
        assert e["late_curve"] == (e["share_at_event_pct"] > 20.0), e


def test_availability_releases_move_nothing(a):
    """The one firm result: shipping the capability is not an event."""
    avail = [e for e in a["event_studies"] if e["kind"] == "first signer release"]
    assert len(avail) >= 5
    assert sum(1 for e in avail if e["change_pp"] == 0.0) >= len(avail) - 1


def test_default_change_is_closer_to_takeoff_than_the_rfc(a):
    """Suggestive, and the doc says so; this pins the arithmetic behind it."""
    rows = [r for r in a["takeoff"] if r["from_default_change_to_1pct_years"] is not None]
    assert rows
    for r in rows:
        assert r["from_default_change_to_1pct_years"] < r["from_rfc_to_1pct_years"], r


def test_doc_does_not_overclaim(a):
    doc = DOC.read_text(encoding="utf-8")
    assert "Suggested, not established" in doc
    assert "Not supported" in doc
    # The interpretable default-change events are 3, and only 1 shows an effect.
    early = [e for e in a["event_studies"]
             if e["kind"].startswith("default change") and not e["late_curve"]]
    assert len(early) == 3
    assert sum(1 for e in early if e["change_pp"] > 0.1) == 1
