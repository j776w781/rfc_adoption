"""Pins for the per-RFC, per-program case studies.

Each test states a claim the deck makes and checks it against the JSON the
deck was built from, or recomputes it from the corpus.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "out/analysis/program_rfc_cases.json"
SLIDES = ROOT / "out/analysis/dnssec_program_rfc_cases_slides.json"

pytestmark = pytest.mark.skipif(not DOC.exists(), reason="run scripts/program_rfc_cases.py first")


@pytest.fixture(scope="module")
def cases():
    return json.loads(DOC.read_text("utf-8"))["cases"]


def spike(c, source, start):
    return next(j for j in c["spikes"] if j["source"] == source and j["start"] == start)


def test_five_cases_present(cases):
    assert set(cases) == {"RFC 5702", "RFC 6605", "RFC 8080", "RFC 5155", "RFC 9276"}


def test_forward_coverage_is_stated_correctly(cases):
    se = cases["RFC 6605"]["series"]["forward"]["se"]["months"]
    ch = cases["RFC 6605"]["series"]["forward"]["ch"]["months"]
    assert se[0] == "2016-06" and se[-1] == "2023-12"
    assert ch[0] == "2020-05"


def test_ecdsa_first_forward_move_is_three_months_after_powerdns_default(cases):
    c = cases["RFC 6605"]
    j = spike(c, "se", "2016-10")
    assert j["nearest_default_change"]["what"].startswith("PowerDNS Auth 4.0.0")
    assert j["nearest_default_change"]["lag_months"] == 3
    assert j["split"]["rollovers_at_least"] > 10_000     # a migration, not new signings
    assert min(x["start"] for x in c["spikes"] if x["basis"] == "forward") == "2016-10"


def test_ecdsa_big_se_moves_are_rollovers(cases):
    c = cases["RFC 6605"]
    for start in ("2019-01", "2019-06"):
        j = spike(c, "se", start)
        assert j["split"]["new_signings_at_most"] == 0
        assert j["nearest_default_change"]["lag_months"] >= 30


def test_ch_2021_wave_is_new_signings_choosing_ecdsa(cases):
    j = spike(cases["RFC 6605"], "ch", "2021-06")
    assert j["delta"] > 500_000 and j["split"]["rollovers_at_least"] == 0
    assert j["share_after_pct"] > 95


def test_reverse_new_signings_ignored_2016_defaults_and_moved_with_bind(cases):
    ar = {r["version"]: r for r in cases["RFC 6605"]["new_signings"]["around_releases"] if r["kind"] == "default"}
    assert ar["2.1.0"]["share_after_pct"] < 1 and ar["4.0.0"]["share_after_pct"] < 1
    assert ar["9.16.0"]["share_after_pct"] - ar["9.16.0"]["share_before_pct"] > 10


def test_rsasha256_new_signings_stepped_after_opendnssec_default(cases):
    ar = {r["version"]: r for r in cases["RFC 5702"]["new_signings"]["around_releases"]}
    assert ar["1.2.0"]["share_before_pct"] < 2 and ar["1.2.0"]["share_after_pct"] >= 15


def test_eddsa_never_default_and_episodes_withdrawn(cases):
    c = cases["RFC 8080"]
    assert not [e for p in c["programs"] for e in p["events"] if e["kind"] == "default"]
    assert c["summary"]["n_reverse"] == 0
    for src in ("se", "nu"):
        s = c["series"]["forward"][src]
        assert s["share_pct"][-1] < 0.1            # back to ~zero by the end of coverage
    assert c["summary"]["spikes_within_3m_of_signer_release"] == 0


def test_nsec3_collapse_precedes_rfc_9276_and_follows_caps(cases):
    c = cases["RFC 9276"]
    assert c["summary"]["n_spikes"] == 3
    for j in c["spikes"]:
        assert j["start"] == "2021-10"
        assert j["months_after_rfc"] < 0
        assert j["nearest_validator_limit"]["lag_months"] <= 3
        assert j["nearest_cve"]["what"].startswith("CVE-2021-40083")
    assert c["summary"]["spikes_within_3m_of_validator_limit"] == 3
    assert c["chance"]["forward"]["within_3m_after_validator_limit"] < 0.2


def test_powerdns_auth_cap_is_included(cases):
    caps = [e for p in cases["RFC 9276"]["programs"] if p["key"] == "pdns-auth" for e in p["events"] if e["kind"] == "limit"]
    assert caps and caps[0]["version"] == "4.5.0"


def test_nsec3_code_and_cves_preceded_deployment(cases):
    c = cases["RFC 5155"]
    bind = next(p for p in c["programs"] if p["key"] == "bind9")
    sup = next(e for e in bind["events"] if e["kind"] == "support")
    assert sup["version"] == "9.6.0" and sup["lag_months_after_rfc"] == 9
    cves = sorted(e["date"] for p in c["programs"] for e in p["events"] if e["kind"] == "cve")
    first_rev = min(m for m in c["first_seen"]["reverse"].values() if m)
    assert first_rev == "2009-07"                 # RIPE, before the first NSEC3 CVE
    assert sup["date"] < first_rev < cves[0] < "2010-01"


def test_no_algorithm_spike_beats_chance_on_defaults(cases):
    for rfc in ("RFC 5702", "RFC 6605", "RFC 8080"):
        c = cases[rfc]; s = c["summary"]; ch = c["chance"]
        expected = (ch["forward"]["within_3m_after_default_change"] or 0) * s["n_forward"] + \
                   (ch["reverse"]["within_3m_after_default_change"] or 0) * s["n_reverse"]
        assert s["spikes_within_3m_of_default_change"] <= expected + 2


def test_every_spike_has_a_recent_any_release(cases):
    """The trap the method avoids: some release always precedes a spike."""
    for c in cases.values():
        for j in c["spikes"]:
            assert j["nearest_any_release"]["lag_months"] <= 3


def test_shares_hidden_for_tiny_populations(cases):
    lac = cases["RFC 5702"]["series"]["reverse"]["lacnic"]
    early = [v for m, v in zip(lac["months"], lac["share_pct"]) if m < "2017-01"]
    assert all(v is None for v in early)


def test_cve_attribution_is_by_product_only(cases):
    doc = json.loads((ROOT / "out/analysis/cve_crossref.json").read_text("utf-8"))
    by = {c["cve"]: c for c in doc["cves"]}
    for c in cases.values():
        for p in c["programs"]:
            for e in p["events"]:
                if e["kind"] == "cve" and p["key"] != "_unattributed":
                    assert "nvd-product" in by[e["cve"]]["sources"]
                    assert p["key"] in by[e["cve"]]["products"]


def test_distro_ships_have_sources_and_dates():
    d = json.loads((ROOT / "data/software/distro_ships.json").read_text("utf-8"))
    assert {s["name"] for s in d["ships"]} >= {"Ubuntu 20.04", "Debian 11"}
    for s in d["ships"]:
        assert len(s["released"]) == 10 and set(s["versions"]) == {"bind9", "pdns", "knot"}
    assert "launchpad" in d["sources"]["ubuntu_versions"]


@pytest.mark.skipif(not SLIDES.exists(), reason="deck not built")
def test_deck_numbers_trace_to_json(cases):
    slides = json.loads(SLIDES.read_text("utf-8"))
    txt = "\n".join(t for s in slides for t in s["text"])
    c = cases["RFC 6605"]
    j = spike(c, "ch", "2021-06")
    assert f'{j["delta"]:,}' in txt
    j = spike(cases["RFC 9276"], "nu", "2021-10")
    assert f'{j["level_before"]:,}' in txt
    ar = {r["version"]: r for r in c["new_signings"]["around_releases"] if r["kind"] == "default"}
    assert f'{ar["9.16.0"]["share_after_pct"]}%' in txt
    assert "vendor-triggered" in txt.lower()
    assert len(slides) >= 20
