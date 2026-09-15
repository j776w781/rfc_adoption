"""Pin the per-RFC deck to its sources.

Every one of these encodes a mistake the first verification round caught in
the deck as first built: the retracted reverse-only first-seen date for EdDSA,
a CDS share taken over every name instead of signed zones, "validator-forced"
asserted for a population that sat below both caps, RFC 5011 labelled
unobservable while its REVOKE bit is in the forward corpus, and the same four
CVEs counted against two RFCs.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "out" / "analysis" / "rfc_timelines.json"
SLIDES = ROOT / "out" / "analysis" / "dnssec_rfc_why_slides.json"

pytestmark = pytest.mark.skipif(not T.exists(), reason="run reporting/rfc_timelines.py first")


@pytest.fixture(scope="module")
def t() -> dict:
    return json.loads(T.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sc() -> dict:
    return json.loads((ROOT / "out/analysis/software_crossref.json").read_text(encoding="utf-8"))


def test_first_seen_is_the_both_corpora_minimum(t, sc):
    """RFC 8080 read 2022-09 (reverse only); the corrected figure is 2019-01 in .se."""
    dec = {r["observable"]: r for r in sc["onset_decomposition"]}
    assert t["RFC 8080"]["lags"]["first_zone_seen"] == dec["alg 15/16"]["first_zone_seen"]
    assert t["RFC 8080"]["lags"]["first_zone_seen"] < "2020-01"
    assert t["RFC 6605"]["lags"]["onset_years"] == dec["alg 13/14"]["onset_years"]


def test_cds_share_is_over_signed_zones(t):
    """Over rr_type '_total' (every name) it read 6.5%; over DNSKEY zones it is ~18%."""
    last = t["RFC 7344"]["curve_summary"]["forward_last_pct"]
    assert 15.0 <= last <= 25.0, last


def test_nsec3_collapse_population_sat_at_exactly_100(t):
    """Neither the 150 nor the 100 cap refused these names, so the slide must not
    say validators refused them."""
    e = t["RFC 9276"]
    ex, gt = e["iterations_exactly_100"], e["iterations_over_100"]
    assert ex["2021-09"] > 0.95 * e["collapse"]["before"]
    assert gt["2021-09"] < 100 and gt["2021-10"] < 100
    assert e["verdict"] != "forced"


def test_rfc_5011_is_partly_observable_via_the_revoke_bit(t):
    r = t["RFC 5011"]["revoked"]
    assert r["months"] >= 80 and r["min"] >= 1 and r["max"] > r["median"]
    assert t["RFC 5011"]["verdict"] == "partly observable"
    # BIND 9.7.0 could revoke a key from 2010-02; the Knot 3.0.0 (2020-09) row
    # alone made the signer side look ten years late.
    assert t["RFC 5011"]["lags"]["first_signer_release"] < "2011"


def test_cds_spikes_are_cds_only(t):
    """Summing CDS+CDNSKEY names counts every zone publishing both twice, which
    reported a +155,150 jump into 342,662 'zones' the month before .ch had
    234,592 zones publishing CDS at all."""
    spikes = t["RFC 7344"]["spikes"]
    assert spikes and max(j["delta_zones"] for j in spikes) < 100_000
    assert max(j["zones_after"] for j in spikes) <= 250_000


def test_verdicts_come_from_the_rule_not_overrides(t):
    """RFC 5155's onset is 1.42 y, which fails the stated FAST rule; it was
    once hard-coded to 'fast, then contested'."""
    assert t["RFC 5155"]["verdict"] == "slow"
    assert t["RFC 5702"]["verdict"] == "fast"


def test_slide_11_default_bounds_are_ecdsa_only():
    """The alg 8/10 takeoff rows are start-censored and their result withdrawn;
    pooling them printed 0.2-5.2 y for the ECDSA defaults instead of 0.8-1.6."""
    slides = json.loads(SLIDES.read_text(encoding="utf-8"))
    s11 = " ".join(next(s for s in slides if s["slide"] == 11)["text"])
    assert "0.8-1.6" in s11 and "0.2-5.2" not in s11


def test_cves_are_not_double_counted_between_ecdsa_and_eddsa(t):
    ecdsa = {c["cve"] for c in t["RFC 6605"]["cves"]}
    eddsa = {c["cve"] for c in t["RFC 8080"]["cves"]}
    assert not (ecdsa & eddsa), ecdsa & eddsa
    assert "CVE-2026-22866" not in ecdsa | eddsa       # ENS RSA padding, neither curve


def test_rfc_9276_lists_only_cap_era_cves(t):
    assert all(c["published"] >= "2021-05" for c in t["RFC 9276"]["cves"])
    assert len(t["RFC 5155"]["cves"]) > len(t["RFC 9276"]["cves"])


def test_evidence_lines_name_the_implementation(t):
    for rfc, e in t.items():
        L = e["lags"]
        if L.get("first_signer_release"):
            assert L.get("first_signer"), rfc
        if L.get("first_validator_release"):
            assert L.get("first_validator"), rfc


def test_verdict_words_are_from_the_stated_rule(t):
    allowed = {"fast", "slow", "never", "stalled",
               "vendor-triggered", "niche by design", "partly observable", "unobservable"}
    for rfc, e in t.items():
        assert e["verdict"] in allowed, (rfc, e["verdict"])


def test_docs_no_longer_claim_validators_refused_the_moved_names():
    for doc in ("software_crossref.md", "cve_crossref.md"):
        text = (ROOT / "docs" / doc).read_text(encoding="utf-8")
        assert "Validator-forced" not in text, doc
        assert "exactly 100" in text, doc


@pytest.mark.skipif(not SLIDES.exists(), reason="deck not built")
def test_slide_numbers_trace_to_the_timeline_json(t):
    """Every 'first zone', 'onset' and 'largest jump' figure printed on an RFC
    slide's evidence line must exist in rfc_timelines.json for that RFC."""
    slides = json.loads(SLIDES.read_text(encoding="utf-8"))
    for s in slides:
        head = s["text"][0]
        m = re.search(r"(RFC \d{4})", head)
        if not m or m.group(1) not in t:
            continue
        e = t[m.group(1)]
        ev = s["text"][-1]
        if e["lags"].get("first_zone_seen"):
            assert e["lags"]["first_zone_seen"] in ev, (m.group(1), ev)
        if e["spikes"]:
            b = max(e["spikes"], key=lambda j: j["delta_zones"])
            assert f"{b['delta_zones']:,}" in ev, (m.group(1), ev)
