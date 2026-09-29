"""Pins for Phase 7: program timelines against the adoption data.

Pins the observable mapping, the strict-panel rule, the seed, the "no test"
rule, and three event results that were recomputed by hand from the parquet
files (the recomputation is repeated here without importing the script).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "out/analysis/software_vs_adoption.json"
PANEL = "_pooled-afrinic-arin"

pytestmark = pytest.mark.skipif(not DOC.exists(), reason="run scripts/software_vs_adoption.py first")


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("software_vs_adoption",
                                                  ROOT / "scripts/software_vs_adoption.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def doc():
    return json.loads(DOC.read_text("utf-8"))


def q2_event(doc, row_id, observable, source):
    return next(e for e in doc["q2_default_change_events"]["events"]
                if e["row_id"] == row_id and e["observable"] == observable and e["source"] == source)


# ---------------------------------------------------------------- seed --

def test_seed_and_draws(mod, doc):
    assert mod.SEED == 20260929
    assert mod.N_DRAWS == 1000
    assert doc["notes"]["seed"] == 20260929 and doc["notes"]["draws"] == 1000
    a = mod.rng_for("q2|x").integers(0, 10 ** 9, size=5)
    b = mod.rng_for("q2|x").integers(0, 10 ** 9, size=5)
    assert (a == b).all()


# ------------------------------------------------------------- mapping --

PINNED_MAP = {
    "knot[2]@2.1.0": [("alg13", 1)], "pdns-auth[7]@4.0.0": [("alg13", 1)],
    "pdns-auth[8]@4.0.0": [("alg13", 1)], "d15-dnssec-policy-default-ecdsap256": [("alg13", 1)],
    "knot[1]@2.0.0": [("alg8", 1)], "pdns-auth[0]@3.2": [("alg8", 1)],
    "opendnssec[5]@1.2.0b1": [("alg8", 1), ("alg7", -1)],
    "d13-ds-cds-sha1-dropped": [("digest1", -1)], "knot[11]@2.8.0": [("digest1", -1)],
    "opendnssec[13]@2.1.0": [("digest1", -1)], "d20-dnssec-cds-sha2-only": [("digest1", -1)],
    "d18-nsec3param-default-0-0": [("iter0", 1)], "d21-signzone-nsec3-iterations-0": [("iter0", 1)],
    "knot[14]@3.2.0": [("iter0", 1)], "pdns-auth[11]@4.6.0": [("iter0", 1)],
    "knot[10]@2.8.0": [("cds", -1)],
    "l01-nsec3-max-iterations-150": [("iter_gt150", -1)], "unbound[20]@1.13.2": [("iter_gt150", -1)],
    "kresd[9]@5.3.1": [("iter_gt150", -1)], "nsec3-max-iterations-150": [("iter_gt150", -1)],
}


def test_observable_mapping_pinned(mod):
    for rid, pairs in PINNED_MAP.items():
        assert [(o, d) for o, d, _ in mod.ROW_MAP[rid]] == pairs, rid
    assert len(mod.ROW_MAP) == 46
    o = mod.OBSERVABLES
    assert o["alg13"]["fwd"] == (("algorithm_dnskey", ["13"]), ("algorithm_dnskey", "_total"))
    assert o["alg13"]["rev"] == (("algorithm_ds", ["13"]), ("algorithm_ds", "_total"))
    assert o["alg8"]["rev"] == (("algorithm_ds", ["8"]), ("algorithm_ds", "_total"))
    assert o["digest2"]["fwd"][0] == ("digest_type_ds", ["2"])
    assert o["digest4"]["fwd"][0] == ("digest_type_ds", ["4"])
    assert o["nsec3param"]["fwd"] == (("rr_type", ["NSEC3PARAM"]), ("algorithm_dnskey", "_total"))
    assert o["cds"]["fwd"][0] == ("rr_type", ["CDS"])
    for k in ("nsec3param", "cds", "iter0", "iter_gt150", "optout", "rsa1024"):
        assert o[k]["rev"] is None, k


def test_validator_caps_are_labelled_indirect(mod):
    for rid in ("l01-nsec3-max-iterations-150", "l02-nsec3-max-iterations-50", "kresd[9]@5.3.1",
                "kresd[12]@5.7.1", "nsec3-max-iterations-150", "unbound[20]@1.13.2"):
        assert all(rel == "indirect-validator-cap" for *_, rel in mod.ROW_MAP[rid]), rid


def test_every_row_mapped_or_explained(mod, doc):
    rows = pd.read_csv(ROOT / "out/analysis/cross_program_defaults_normalised.csv", dtype=str)
    mapped = {r["row_id"] for r in doc["observable_mapping"]["rows"]}
    unmapped = {r["row_id"] for r in doc["excluded"]["rows_not_observable"]}
    assert mapped | unmapped == set(rows.row_id)
    assert not mapped & unmapped
    # the brief's "not observable" mechanisms never get an observable
    mech = dict(zip(rows.row_id, rows.mechanism))
    for r in doc["observable_mapping"]["rows"]:
        assert mech[r["row_id"]] not in ("validation", "trust-anchor", "trust-anchor-5011"), r["row_id"]


# ---------------------------------------------------------- strict panel --

def test_reverse_shares_use_only_the_strict_panel(mod, doc):
    with pytest.raises(AssertionError):
        mod.share_series(mod.Data(), "alg13", "reverse_panel", "arin")
    for r in doc["q1_per_program_releases"]["per_program"].values():
        for t in r["tests"]:
            if t["corpus"] != "forward":
                assert t["corpus"] == "reverse_panel" and t["source"] == PANEL
    for e in doc["q2_default_change_events"]["events"]:
        if e["corpus"] != "forward":
            assert e["corpus"] == "reverse_panel" and e["source"] == PANEL
    for e in doc["q5_successor_rfc"]["pairs"]:
        if e["corpus"] != "forward":
            assert e["source"] == PANEL
    # per-RIR series appear only as counts (q4 spikes), never as a share
    for s in doc["q4_spikes"]["spikes"]:
        if s["corpus"] == "reverse":
            assert s["source"] in mod.RIRS
            assert not any("share" in k for k in s)
    assert "summed" not in json.dumps(doc["q2_default_change_events"]["method"])


def test_reverse_dating_check(doc):
    chk = doc["q4_spikes"]["reverse_dating_check"]
    for rir in ("afrinic", "arin"):
        assert chk[rir]["equal_after_plus_one_month"] == chk[rir]["months_compared"]


# ------------------------------------------------------------- no test --

def test_untestable_events_carry_no_number(doc):
    for e in doc["q2_default_change_events"]["events"]:
        if e["status"] != "tested":
            assert "observed_d12" not in e and e["reason"]
    for p in doc["q1_per_program_releases"]["per_program"].values():
        for t in p["tests"]:
            if t["status"] != "tested":
                assert "observed_mean_d3" not in t and t["reason"]


def test_coverage_facts(doc):
    cov = doc["notes"]["coverage"]
    for t in ("se", "nu", "gov", "ee", "ch", "li"):
        assert cov[t]["months"].endswith("2023-12")
    assert cov["fed.us"]["months"] == "2017-05..2022-10"
    assert cov["fed.us"]["signed_zone_share_valid"] == "never"
    assert cov["se"]["months"].startswith("2016-06") and cov["ch"]["months"].startswith("2020-05")
    assert cov[PANEL]["signed_delegation_share_valid"].startswith("2011-05")


# ------------------------------------------------ three hand-checked events --

def _hand_d12(share: pd.Series, month: str) -> float:
    det = share - share.rolling(25, center=True, min_periods=13).median()
    m = pd.Period(month, "M")
    before = det.loc[str(m - 12):str(m - 1)]
    after = det.loc[str(m):str(m + 11)]
    return float(after.mean() - before.mean())


def test_hand_knot_ecdsa_default_on_panel(doc):
    """knot[2]@2.1.0 (2016-01), algorithm 13 share of panel signed delegations."""
    p = pd.read_parquet(ROOT / "out/panel_run/timeline_monthly.parquet")
    pp = p[(p.source == PANEL) & (p.dimension == "algorithm_ds")]
    num = pp[pp.value == "13"].set_index("month").domain_days
    den = pp[pp.value == "_total"].set_index("month").domain_days
    months = pd.period_range("2011-05", "2026-08", freq="M").strftime("%Y-%m")
    share = (100 * num.reindex(den.index, fill_value=0) / den).reindex(months)
    hand = _hand_d12(share, "2016-01")
    e = q2_event(doc, "knot[2]@2.1.0", "alg13", PANEL)
    assert e["status"] == "tested"
    assert e["observed_d12"] == pytest.approx(hand, abs=1e-5)
    assert hand == pytest.approx(-0.019119, abs=1e-5)
    assert not e["outside_90_band"]
    assert e["share_month_before"] == pytest.approx(0.253485, abs=1e-5)


def test_hand_bind9_signzone_iterations_zero_on_se(doc):
    """bind9 d21 (2022-07), NSEC3 owner names at 0 iterations in .se."""
    s = pd.read_parquet(ROOT / "out/server_run/timeline_monthly.parquet")
    z = s[(s.source == "se") & (s.dimension == "nsec3_iterations")]
    num = z[z.value == "0"].set_index("month").domain_days
    den = z[z.value == "_total"].set_index("month").domain_days
    share = 100 * num.reindex(den.index, fill_value=0) / den
    hand = _hand_d12(share, "2022-07")
    e = q2_event(doc, "d21-signzone-nsec3-iterations-0", "iter0", "se")
    assert e["observed_d12"] == pytest.approx(hand, abs=1e-5)
    assert hand == pytest.approx(0.039922, abs=1e-5)
    assert not e["outside_90_band"]


def test_hand_opendnssec_rsasha256_has_no_test_on_panel(doc):
    """opendnssec[5]@1.2.0b1 (2011-03) predates the panel's first signed month, 2011-05."""
    e = q2_event(doc, "opendnssec[5]@1.2.0b1", "alg8", PANEL)
    assert e["status"] == "no test"
    assert e["reason"].startswith("no before-period")
    assert "observed_d12" not in e
    # and in no corpus at all
    assert "opendnssec[5]@1.2.0b1" in doc["q2_default_change_events"]["rows_with_no_test_in_any_corpus"]


def test_q4_spike_rule_is_the_program_rfc_cases_rule(mod):
    import program_rfc_cases
    assert mod._spikes is program_rfc_cases.spikes
    assert (mod.FORWARD_FLOOR, mod.REVERSE_FLOOR) == (300, 30)
