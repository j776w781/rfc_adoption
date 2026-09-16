"""Pins for the CVE-patch vs RFC-publication adoption-rate comparison."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "out/analysis/cve_vs_rfc_rates.json"
pytestmark = pytest.mark.skipif(not DOC.exists(), reason="run scripts/cve_vs_rfc_rates.py first")


@pytest.fixture(scope="module")
def doc():
    return json.loads(DOC.read_text("utf-8"))


def test_events_come_from_the_crossref_and_the_screen(doc):
    ev = doc["events"]
    assert len(ev["rfc_publications"]) == 30
    assert all(e["month"] for e in ev["cve_patches"])
    cv = json.loads((ROOT / "out/analysis/cve_crossref.json").read_text("utf-8"))
    by = {c["cve"]: c for c in cv["cves"]}
    for e in ev["cve_patches"]:
        assert by[e["event"]]["scope"] == "dnssec" and by[e["event"]]["fixes"]


def test_months_counted_once(doc):
    """Fourteen CVEs were fixed in 2026-07; that month is one draw, not fourteen."""
    for res in doc["overall"].values():
        for k in ("raw", "detrended"):
            assert res[k]["cve_patches"]["n"] < res[k]["cve_events"]
            assert res[k]["cve_patches"]["n"] <= len({e["month"] for e in doc["events"]["cve_patches"]})


def test_no_difference_survives_year_matching_or_detrending(doc):
    for res in doc["overall"].values():
        d = res["detrended"]
        assert d["p_cve_vs_rfc"] > 0.05
        assert d["p_cve_vs_all_year_matched"] > 0.05
        assert d["p_rfc_vs_all_year_matched"] > 0.05


def test_control_of_all_dns_cves_also_null_after_matching(doc):
    for res in doc["control_dns_cves"].values():
        assert res["detrended"]["p_dnscve_vs_all_year_matched"] > 0.05


def test_reverse_rates_are_tiny(doc):
    r = doc["overall"]["reverse signed share (strict panel)"]["raw"]
    assert abs(r["all_months"]["median"]) < 0.02          # pp per month, on a ~1% share
    assert r["cve_patches"]["n"] >= 15 and r["rfc_publications"]["n"] >= 10
