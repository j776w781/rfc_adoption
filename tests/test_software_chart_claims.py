"""Pins for the software-comparison chart titles.

Five of these charts asserted things the data contradicts. Each test states the
claim that was wrong and checks the data that refutes it, so the title cannot
come back.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks/build_software_notebook.py"


@pytest.fixture(scope="module")
def src():
    return NB.read_text("utf-8")


@pytest.fixture(scope="module")
def sup():
    return json.loads((ROOT / "data/software/software_support.json").read_text("utf-8"))


def test_support_matrix_excludes_non_standard_codepoints(src, sup):
    """PowerDNS Auth 3.3.1 signed EdDSA on private codepoint 250 in 2013, five
    years before RFC 8080 assigned 15/16. It must not put a cell in that column."""
    bad = [r for r in sup["support"] if not r.get("standard_codepoint", True)]
    assert bad and bad[0]["implementation"] == "pdns-auth" and bad[0]["first_release"] == "3.3.1"
    block = src[src.index('grid = {}'):src.index('save(fig, "05_support_matrix")')]
    assert 'if not r.get("standard_codepoint", True):' in block
    assert "First stable release with each capability" not in src


def test_support_matrix_says_blank_is_not_absence(src):
    """An empty cell means no dated evidence, not that the program cannot do it:
    Knot and PowerDNS both do NSEC3 and RSA/SHA-256."""
    assert "NOT that the program lacks the capability" in src


def test_default_changes_counts_are_right(src, sup):
    dc = sup["default_changes"]
    assert len(dc) == 7
    assert len({r["implementation"] for r in dc}) == 4
    assert min(r["released"] for r in dc)[:4] == "2010"
    assert max(r["released"] for r in dc)[:4] == "2020"
    assert "across five projects" not in src
    assert "four of the eight projects" in src


def test_nsec3_is_not_called_the_most_deployed_mechanism(src):
    """ECDSA is on 76.1% of signed forward zones against NSEC3's 61.9%."""
    T = json.loads((ROOT / "out/analysis/rfc_timelines.json").read_text("utf-8"))
    assert T["RFC 6605"]["curve_summary"]["forward_last_pct"] > T["RFC 5155"]["curve_summary"]["forward_last_pct"]
    assert "most deployed optional mechanism" not in src


def test_nsec3_collapse_is_not_attributed_to_resolvers_alone(src, sup):
    """PowerDNS Auth 4.5.0, annotated on that chart, is a signer capping what it
    signs, not a resolver refusing what it reads."""
    caps = [r for r in sup["validator_limits"] if r["implementation"] == "pdns-auth"]
    assert caps and caps[0]["first_release"] == "4.5.0"
    assert "resolvers stopped accepting them" not in src
    assert "signers and validators both capped" in src


def test_no_cve_count_is_claimed_for_keyword_matched_products(src):
    cv = json.loads((ROOT / "out/analysis/cve_crossref.json").read_text("utf-8"))
    assert cv["query_method"]["opendnssec"] != "cpe"
    assert "OpenDNSSEC has one, a dependency" not in src
