"""Pin docs/release_scan.md to its outputs.

Two confounds in this analysis produce significant-looking results that are not
real, and both did before they were removed: delegation changes rise ~25x over
the corpus, so a raw comparison ranks projects by how recently they shipped; and
shuffling release months uniformly destroys each project's release clustering, so
a late-clustered schedule beats that null automatically. On raw counts four
projects cleared p < 0.05. After detrending and a circular-shift null, none does.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCAN = ROOT / "out" / "analysis" / "release_scan.json"
DOC = ROOT / "docs" / "release_scan.md"
LEDGER = ROOT / "out" / "analysis" / "delegation_changes.parquet"

pytestmark = pytest.mark.skipif(
    not SCAN.exists(), reason="run scripts/release_scan.py first")


@pytest.fixture(scope="module")
def scan() -> dict:
    return json.loads(SCAN.read_text(encoding="utf-8"))


def test_no_ecosystem_level_control_exists(scan):
    """97% of months contain a release; the per-release table is descriptive."""
    assert scan["identification"]["months_with_any_release"] > 0.9


def test_every_project_reports_raw_and_detrended(scan):
    for proj, r in scan["per_project"].items():
        if not r.get("testable"):
            continue
        for key in ("raw_difference", "detrended_difference", "circular_shift_p",
                    "median_release_year"):
            assert key in r, (proj, key)


def test_detrending_changes_the_answer(scan):
    """If raw and detrended agreed everywhere, the correction did nothing and
    the doc's account of it would be wrong."""
    rows = [r for r in scan["per_project"].values() if r.get("testable")]
    flipped = [r for r in rows
               if (r["raw_difference"] > 0) != (r["detrended_difference"] > 0)]
    assert flipped, "expected at least one project to change sign under detrending"


def test_no_project_survives_as_significant(scan):
    """The finding. If this ever fails, the document must be rewritten rather
    than the threshold moved."""
    sig = {p: r["circular_shift_p"] for p, r in scan["per_project"].items()
           if r.get("testable") and r["circular_shift_p"] < 0.05}
    assert not sig, sig


def test_doc_states_the_scope_limits(scan):
    doc = DOC.read_text(encoding="utf-8")
    assert "reverse-only" in doc or "reverse only" in doc.lower()
    assert "no DNS-provider level" in doc or "DNS-provider level" in doc


@pytest.mark.skipif(not LEDGER.exists(), reason="ledger not built")
def test_ledger_kinds_are_exhaustive():
    import pandas as pd
    led = pd.read_parquet(LEDGER)
    assert set(led.kind) <= {"sign", "unsign", "rollover"}
    assert len(led) > 10000
    # A rollover must have an algorithm on both sides; sign/unsign must not.
    ro = led[led.kind == "rollover"]
    assert (ro.from_alg != "").all() and (ro.to_alg != "").all()
    assert (led[led.kind == "sign"].from_alg == "").all()
    assert (led[led.kind == "unsign"].to_alg == "").all()
