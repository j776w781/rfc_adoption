"""Pins for the two charts that had no working producer.

Both were orphans: reverse_algorithm_mix.png came from reverse RFC-match
checkpoints whose completion markers are absent in this checkout (so the merge
declined to count them and the chart rendered empty), and nsec3_vs_ecdsa.png was
dropped from make_charts.py when growth_vs_baseline.png replaced it. Both are
now built in reporting/algorithm_mix.py from the canonical timeline parquet.

These tests check the endpoints against figures verified elsewhere in the
project, so a denominator change cannot pass silently.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")

ROOT = Path(__file__).resolve().parents[1]
PANEL = "_pooled-afrinic-arin"


@pytest.fixture(scope="module")
def series():
    import importlib.util
    spec = importlib.util.spec_from_file_location("amix", ROOT / "reporting/algorithm_mix.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    srv = pd.read_parquet(ROOT / "out/server_run/timeline_monthly.parquet")
    pan = pd.read_parquet(ROOT / "out/panel_run/timeline_monthly.parquet")
    rev = pan[(pan.basis == "reverse") & (pan.source == PANEL)]
    fwd = srv[srv.basis == "zonefile"]
    return m, rev, fwd


def test_charts_exist():
    for n in ("reverse_algorithm_mix.png", "nsec3_vs_ecdsa.png"):
        p = ROOT / "reporting/charts" / n
        assert p.exists() and p.stat().st_size > 20_000, n


def test_reverse_endpoints_match_the_verified_curve_summaries(series):
    m, rev, _ = series
    T = json.loads((ROOT / "out/analysis/rfc_timelines.json").read_text("utf-8"))
    ecdsa = m.share(rev, "algorithm_ds", ["13", "14"]).iloc[-1]
    assert ecdsa == pytest.approx(T["RFC 6605"]["curve_summary"]["reverse_last_pct"], abs=0.05)
    nsec3 = m.share(rev, "algorithm_ds", ["7"]).iloc[-1]
    assert nsec3 == pytest.approx(T["RFC 5155"]["curve_summary"]["reverse_last_pct"], abs=0.05)
    eddsa = m.share(rev, "algorithm_ds", ["15", "16"]).iloc[-1]
    assert eddsa == pytest.approx(0.41, abs=0.05)          # Ed25519 + Ed448


def test_forward_endpoints_match_the_verified_curve_summaries(series):
    m, _, fwd = series
    T = json.loads((ROOT / "out/analysis/rfc_timelines.json").read_text("utf-8"))
    assert m.share(fwd, "algorithm_dnskey", ["13", "14"]).iloc[-1] == pytest.approx(
        T["RFC 6605"]["curve_summary"]["forward_last_pct"], abs=0.05)
    assert m.share(fwd, "rr_type", ["NSEC3PARAM"], den_dim="algorithm_dnskey").iloc[-1] == pytest.approx(
        T["RFC 5155"]["curve_summary"]["forward_last_pct"], abs=0.05)


def test_denominator_is_signed_not_all(series):
    """The bug in the retired chart: dividing by every scanned record while
    calling the result a share of signed delegations."""
    m, rev, _ = series
    signed_den = m.share(rev, "algorithm_ds", ["13", "14"]).iloc[-1]
    all_den = m.share(rev, "algorithm_ds", ["13", "14"], den_dim="all", den_value="all").iloc[-1]
    assert signed_den > 50 and all_den < 5      # ~70% of signed, but <1% of all delegations


def test_reverse_adoption_no_longer_writes_the_mix_chart():
    src = (ROOT / "reporting/reverse_adoption.py").read_text("utf-8")
    assert 'save(fig, "reverse_algorithm_mix.png")' not in src
    assert "reporting/algorithm_mix.py" in src          # points at the replacement
