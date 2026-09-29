"""Pins for Phase 7: program timelines against the adoption data.

Pins the observable mapping, the strict-panel rule, the seed, the reverse dating
convention, the "no test" rule, the calibration of the new null, and three event
results recomputed by hand from the parquet files, for both the primary step
test and the secondary transient test. The recomputation is repeated here
without importing the script.
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


def q2_event(doc, row_id, observable, source, test="step12"):
    return next(e for e in doc["q2_default_change_events"]["events"]
                if e["row_id"] == row_id and e["observable"] == observable and e["source"] == source
                and e["test"] == test)


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


def test_reverse_dating_convention(mod, doc):
    """Server run, panel run and ledger share one label convention: no shift between them."""
    chk = doc["q4_spikes"]["reverse_dating_check"]
    for rir in ("afrinic", "arin"):
        assert chk[rir]["equal_without_shift"] == chk[rir]["months_compared"] > 150
        assert chk[rir]["equal_with_plus_one_shift"] < chk[rir]["months_compared_with_plus_one_shift"]
    # a release in calendar month r is before reverse label r+1; forward uses r itself
    assert mod.REV_EVENT_LAG == 1
    e = q2_event(doc, "knot[2]@2.1.0", "alg13", PANEL)
    assert (e["before_labels"], e["after_labels"]) == ("2014-02..2016-01", "2016-02..2017-01")
    e = q2_event(doc, "d21-signzone-nsec3-iterations-0", "iter0", "se")
    assert (e["before_labels"], e["after_labels"]) == ("2020-07..2022-06", "2022-07..2023-06")
    # q3: ledger window labels r+1..r+4
    ev = {x["row_id"]: x["window"] for x in doc["q3_manual_vs_automatic"]["events"]}
    assert ev["pdns-auth[0]@3.2"] == ["2013-02", "2013-05"]
    # q4: the afrinic SHA-1 DS spike labelled 2022-01 happened in 2021-12, before bind9 d20
    sp = next(x for x in doc["q4_spikes"]["spikes"]
              if x["source"] == "afrinic" and x["observable"] == "digest1" and x["start"] == "2022-01")
    assert sp["change_calendar_month_start"] == "2021-12"
    assert not sp["relevant_default_within_3m"]
    assert sum(x["relevant_default_within_3m"] for x in doc["q4_spikes"]["spikes"]) == 13


# ------------------------------------------------------------- no test --

def test_untestable_events_carry_no_number(doc):
    for e in doc["q2_default_change_events"]["events"]:
        if e["status"] != "tested":
            assert "observed" not in e and e["reason"]
    for p in doc["q1_per_program_releases"]["per_program"].values():
        for t in p["tests"]:
            if t["status"] != "tested":
                assert "observed_mean" not in t and t["reason"]


def test_coverage_facts(doc):
    cov = doc["notes"]["coverage"]
    for t in ("se", "nu", "gov", "ee", "ch", "li"):
        assert cov[t]["months"].endswith("2023-12")
    assert cov["fed.us"]["months"] == "2017-05..2022-10"
    assert cov["fed.us"]["signed_zone_share_valid"] == "never"
    assert cov["se"]["months"].startswith("2016-06") and cov["ch"]["months"].startswith("2020-05")
    assert cov[PANEL]["signed_delegation_share_valid"].startswith("2011-05")


# ------------------------------------------------ three hand-checked events --

def _panel_share(value: str) -> pd.Series:
    p = pd.read_parquet(ROOT / "out/panel_run/timeline_monthly.parquet")
    pp = p[(p.source == PANEL) & (p.dimension == "algorithm_ds")]
    num = pp[pp.value == value].set_index("month").domain_days
    den = pp[pp.value == "_total"].set_index("month").domain_days
    months = pd.period_range("2011-05", "2026-08", freq="M").strftime("%Y-%m")
    return (100 * num.reindex(den.index, fill_value=0) / den).reindex(months)


def _se_iter0_share() -> pd.Series:
    s = pd.read_parquet(ROOT / "out/server_run/timeline_monthly.parquet")
    z = s[(s.source == "se") & (s.dimension == "nsec3_iterations")]
    num = z[z.value == "0"].set_index("month").domain_days
    den = z[z.value == "_total"].set_index("month").domain_days
    return 100 * num.reindex(den.index, fill_value=0) / den


def _hand_transient(share: pd.Series, first_after: str, w: int = 12) -> float:
    det = share - share.rolling(25, center=True, min_periods=13).median()
    m = pd.Period(first_after, "M")
    return float(det.loc[str(m):str(m + w - 1)].mean() - det.loc[str(m - w):str(m - 1)].mean())


def _hand_step(share: pd.Series, first_after: str) -> float:
    """Line fitted to the 24 months before, extrapolated over the 12 after; mean of actual minus line."""
    m = pd.Period(first_after, "M")
    pre = share.loc[str(m - 24):str(m - 1)].to_numpy(dtype=float)
    post = share.loc[str(m):str(m + 11)].to_numpy(dtype=float)
    tb, ta = np.arange(-24, 0), np.arange(0, 12)
    ok, oka = ~np.isnan(pre), ~np.isnan(post)
    slope, icpt = np.polyfit(tb[ok], pre[ok], 1)
    return float(np.mean(post[oka] - (icpt + slope * ta[oka])))


def test_hand_knot_ecdsa_default_on_panel(doc):
    """knot[2]@2.1.0, released 2016-01-14: panel labels up to 2016-01 are before it, so the
    after-period starts at label 2016-02."""
    share = _panel_share("13")
    step, trans = _hand_step(share, "2016-02"), _hand_transient(share, "2016-02")
    e = q2_event(doc, "knot[2]@2.1.0", "alg13", PANEL)
    assert e["status"] == "tested"
    assert e["observed"] == pytest.approx(step, abs=1e-5)
    assert step == pytest.approx(0.228598, abs=1e-5)
    assert not e["outside_90_band"]
    t = q2_event(doc, "knot[2]@2.1.0", "alg13", PANEL, "transient12")
    assert t["observed"] == pytest.approx(trans, abs=1e-5)
    assert trans == pytest.approx(-0.021503, abs=1e-5)


def test_hand_bind9_signzone_iterations_zero_on_se(doc):
    """bind9 d21, 2022-07, NSEC3 owner names at 0 iterations in .se: the step test reaches the
    97.5th percentile, the transient test does not leave its band."""
    share = _se_iter0_share()
    step, trans = _hand_step(share, "2022-07"), _hand_transient(share, "2022-07")
    e = q2_event(doc, "d21-signzone-nsec3-iterations-0", "iter0", "se")
    assert e["observed"] == pytest.approx(step, abs=1e-5)
    assert step == pytest.approx(2.639849, abs=1e-5)
    assert e["outside_90_band"] and e["percentile"] > 95
    t = q2_event(doc, "d21-signzone-nsec3-iterations-0", "iter0", "se", "transient12")
    assert t["observed"] == pytest.approx(trans, abs=1e-5)
    assert trans == pytest.approx(0.039922, abs=1e-5)
    assert not t["outside_90_band"]


def test_hand_opendnssec_rsasha256_has_no_test_on_panel(doc):
    """opendnssec[5]@1.2.0b1 (2011-03) predates the panel's first signed month, 2011-05."""
    for test in ("step12", "transient12"):
        e = q2_event(doc, "opendnssec[5]@1.2.0b1", "alg8", PANEL, test)
        assert e["status"] == "no test"
        assert e["reason"].startswith("no before-period")
        assert "observed" not in e
        assert "opendnssec[5]@1.2.0b1" in \
            doc["q2_default_change_events"]["summary"][test]["rows_with_no_test_in_any_corpus"]


def test_step_statistic_sees_a_step_the_transient_does_not(mod):
    """A lasting +5 pp step on a trending series: the step statistic recovers it, the detrended
    transient statistic does not."""
    x = 10 + 0.1 * np.arange(80)
    x[40:] += 5.0
    assert mod.step_stat(x)[40] == pytest.approx(5.0, abs=1e-9)
    det = (pd.Series(x) - pd.Series(x).rolling(25, center=True, min_periods=13).median()).to_numpy()
    assert abs(mod.window_stat(det, 12)[40]) < 1.0


# ---------------------------------------------------------- calibration --

def test_null_calibration_on_synthetic_data(mod, doc):
    """No effect: rejection at the 90% band is about 10%. The old whole-span shift was conservative."""
    cal = doc["notes"]["calibration"]
    assert cal["reps"] == 1000
    assert 0.07 <= cal["q2_step12_rejection_rate"] <= 0.13
    assert 0.07 <= cal["q1_coverage_window_shift_rejection_rate"] <= 0.14
    assert cal["q1_whole_span_shift_rejection_rate"] < cal["q1_coverage_window_shift_rejection_rate"]
    small = mod.calibration(200)
    assert 0.04 <= small["q2_step12_rejection_rate"] <= 0.16
    assert 0.04 <= small["q1_coverage_window_shift_rejection_rate"] <= 0.18


def test_q1_null_is_calibrated_on_the_real_schedules(doc):
    """With the coverage-window shift, mean p over the program tests is near 0.5, not 0.63."""
    for test, agg in doc["q1_per_program_releases"]["aggregate"].items():
        assert 0.44 <= agg["mean_p_two_sided"] <= 0.58, test


def test_q4_spike_rule_is_the_program_rfc_cases_rule(mod):
    import program_rfc_cases
    assert mod._spikes is program_rfc_cases.spikes
    assert (mod.FORWARD_FLOOR, mod.REVERSE_FLOOR) == (300, 30)
