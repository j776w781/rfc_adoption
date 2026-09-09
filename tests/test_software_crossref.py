"""Pin the numbers in docs/software_crossref.md to the analysis output.

Written because this analysis already produced two wrong figures that read as
plausible: zone counts summed over algorithm_dnskey and algorithm_ds, which
counts every signed forward zone twice, and a pairing claim ("no jump happens in
one half of a pair") that was true of the doubled numbers and false of the real
ones. Both were caught by re-deriving; neither would have been caught by reading.

Runs offline against out/analysis/software_crossref.json. Skips if that has not
been generated.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "software_crossref.md"
OUT = ROOT / "out" / "analysis" / "software_crossref.json"
SUPPORT = ROOT / "data" / "software" / "software_support.json"

pytestmark = pytest.mark.skipif(
    not OUT.exists(), reason="run scripts/software_crossref.py first")


@pytest.fixture(scope="module")
def analysis() -> dict:
    return json.loads(OUT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_onset_decomposes_additively(analysis):
    """code lag + deployment lag must reconstruct onset, or the join is wrong."""
    for row in analysis["onset_decomposition"]:
        if {"code_lag_years", "deployment_lag_years", "onset_years"} <= row.keys():
            total = row["code_lag_years"] + row["deployment_lag_years"]
            assert abs(total - row["onset_years"]) <= 0.15, row["observable"]


def test_no_negative_deployment_lag(analysis):
    """A zone cannot publish a value before any signer could produce it.

    A negative value here means the support row and the observable did not match
    -- which is exactly what "alg 15" against "alg 15/16" produced.
    """
    for row in analysis["onset_decomposition"]:
        if "deployment_lag_years" in row:
            assert row["deployment_lag_years"] >= 0, row["observable"]


def test_zone_counts_are_not_summed_across_dimensions(analysis):
    """.se had 11,046 zones by DNSKEY and 10,904 of the same zones by DS.

    Any figure near their sum means the double count is back.
    """
    jumps = analysis["portfolio_jumps"]["alg 13/14"]
    se_2016 = [j for j in jumps if j["source"] == "se" and j["month"] == "2016-10"]
    assert se_2016, "the .se 2016-10 ECDSA jump should be detected"
    assert se_2016[0]["zones_after"] == 11046


def test_doc_jump_figures_match_analysis(doc, analysis):
    """Every "+N" in the doc's jump table is a delta the analysis produced."""
    quoted = {int(m.replace(",", ""))
              for m in re.findall(r"\+([\d,]{5,})\s+\.", doc)}
    produced = {j["delta_zones"]
                for rows in analysis["portfolio_jumps"].values() for j in rows}
    assert quoted <= produced, sorted(quoted - produced)


def test_doc_release_dates_match_the_dataset(doc):
    """Release dates in the doc's default-change table come from the dataset."""
    support = json.loads(SUPPORT.read_text(encoding="utf-8"))
    known = {(r["implementation"], r["first_release"], r["released"])
             for r in support["default_changes"] + support["validator_limits"]}
    for impl, ver, released in known:
        if ver in doc:
            assert released in doc, f"{impl} {ver} quoted without its date {released}"


def test_default_claims_were_checked_against_product_code(analysis):
    """A changed test fixture reads like a changed default in a git log."""
    support = json.loads(SUPPORT.read_text(encoding="utf-8"))
    for row in support["default_changes"]:
        assert row.get("product_code") is True, row["what"]


def test_private_codepoints_excluded_from_code_lag(analysis):
    """PowerDNS's 2012 Ed25519 used codepoint 250, not RFC 8080's 15/16.

    Counting it would report EdDSA as implemented five years before its RFC.
    """
    row = next(r for r in analysis["onset_decomposition"] if r["observable"] == "alg 15/16")
    assert row["code_lag_years"] > 0, "code lag fell back onto the private codepoint"
    assert row["first_signer"].startswith("knot")


def test_nsec3_collapse_precedes_rfc_9276(analysis):
    """The whole point: deployment moved before the RFC, not after."""
    c = analysis["nsec3_iteration_collapse"]
    assert c["largest_single_month_fall"]["month"] < c["rfc_9276_published"]
    assert c["largest_single_month_fall"]["zones_lost"] > 10000


def test_most_rfcs_land_on_a_predecessor_still_spreading(analysis):
    rows = analysis["rfc_overlap"]
    assert sum(r["still_spreading"] for r in rows) == 6
    assert len(rows) == 7


def test_no_bare_confidence_labels_remain():
    """`confidence: medium` said nothing about what to distrust; it was replaced
    by an attribution class plus a written basis."""
    support = json.loads(SUPPORT.read_text(encoding="utf-8"))
    for section in ("support", "default_changes", "validator_limits"):
        for row in support[section]:
            assert "confidence" not in row, row
            assert row["attribution"] in {"exact", "earliest-of-several", "approximate"}
            assert len(row["attribution_basis"]) > 40, row["attribution"]


def test_every_row_cites_a_reachable_commit():
    support = json.loads(SUPPORT.read_text(encoding="utf-8"))
    for section in ("support", "default_changes", "validator_limits"):
        for row in support[section]:
            assert row.get("evidence_url"), row
            if row.get("evidence_commit"):
                assert row["evidence_commit"] in row["evidence_url"]


def test_bind_development_branches_are_not_counted_as_releases():
    """BIND 9.13+ odd minors are development branches. Counting 9.15.6 as stable
    dates dnssec-policy CDS publication to 2019 instead of 9.16.0 in 2020."""
    rel = json.loads((ROOT / "data" / "software" / "release_dates.json")
                     .read_text(encoding="utf-8"))
    for ver in rel["bind9"]["releases"]:
        major, minor = ver.split(".")[:2]
        assert not (major == "9" and int(minor) >= 13 and int(minor) % 2 == 1), ver
