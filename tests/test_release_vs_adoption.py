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
    assert len(avail) >= 4
    assert all(e["change_pp"] == 0.0 for e in avail), avail


def test_default_change_is_closer_to_takeoff_than_the_rfc(a):
    """Suggestive, and the doc says so; this pins the arithmetic behind it."""
    rows = [r for r in a["takeoff"] if r["from_default_change_to_1pct_years"] is not None]
    assert rows
    for r in rows:
        assert r["from_default_change_to_1pct_years"] < r["from_rfc_to_1pct_years"], r


def test_doc_does_not_overclaim(a):
    doc = DOC.read_text(encoding="utf-8")
    assert "Not established either way" in doc
    assert "Not supported" in doc
    # No interpretable default-change event shows an effect. If one ever does,
    # this fails and the document has to be rewritten rather than quietly drift.
    early = [e for e in a["event_studies"]
             if e["kind"].startswith("default change") and not e["late_curve"]]
    assert early
    assert all(abs(e["change_pp"]) < 0.1 for e in early), early


def test_reverse_rates_come_from_the_strict_panel(a):
    """Summing the five RIRs double-counts names and moved every crossing date.

    ECDSA read 2017-08 summed against 2018-06 on the panel. The panel is what
    adoption_measures.json uses, so anything else puts this analysis and the
    project's published adoption dates in disagreement.
    """
    assert "afrinic" in a["populations"]["reverse"].lower()
    for r in a["takeoff"]:
        if r["basis"] == "reverse":
            assert "AFRINIC+ARIN" in r["population"]
            assert r["series_start"] >= "2011-05"


def test_reverse_crossings_match_the_projects_adoption_measures(a):
    """digest 4 is the one observable mapping 1:1 to an adoption_measures row."""
    am = json.loads((ROOT / "out" / "analysis" / "adoption_measures.json")
                    .read_text(encoding="utf-8"))
    sha384 = next(d for d in am["digest_types"] if d["value"] == 4)
    row = next(r for r in a["takeoff"]
               if r["observable"] == "digest 4" and r["basis"] == "reverse")
    assert row["first_month_over_1pct"] == sha384["t_1pct_date"]
