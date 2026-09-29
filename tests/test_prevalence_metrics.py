"""Pins the denominator rules of scripts/prevalence_metrics.py and a few endpoints.

The synthetic-frame tests run everywhere. The endpoint tests read the real
parquets and skip when they are absent.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("prevalence_metrics", ROOT / "scripts" / "prevalence_metrics.py")
pm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pm)

SERVER = ROOT / "out/server_run/timeline_monthly.parquet"
PANEL = ROOT / "out/panel_run/timeline_monthly.parquet"
CSV = ROOT / "out/analysis/prevalence_metrics.csv"
JSON = ROOT / "out/analysis/prevalence_metrics.json"


def _row(source, basis, month, dim, val, peak, days=1):
    return dict(source=source, basis=basis, month=month, dimension=dim, value=val,
                records=peak, domain_days=peak * days, domains_peak=peak, measured_days=days)


@pytest.fixture
def forward_frame():
    # _total (all names) is deliberately huge: using it as the denominator is the bug being pinned.
    return pd.DataFrame([
        _row("se", "zonefile", "2023-12", "rr_type", "_total", 1_000_000, 31),
        _row("se", "zonefile", "2023-12", "rr_type", "NS", 1_000, 31),
        _row("se", "zonefile", "2023-12", "rr_type", "DS", 600, 31),
        _row("se", "zonefile", "2023-12", "rr_type", "DNSKEY", 620, 31),
        _row("se", "zonefile", "2023-12", "algorithm_dnskey", "_total", 620, 31),
        _row("se", "zonefile", "2023-12", "rr_type", "RRSIG", 1_900, 31),
        _row("se", "zonefile", "2023-12", "rrsig_type_covered", "DNSKEY", 619, 31),
        _row("se", "zonefile", "2023-12", "rrsig_type_covered", "SOA", 1_200, 31),
    ])


@pytest.fixture
def reverse_frame():
    return pd.DataFrame([
        _row("arin", "reverse", "2026-08", "all", "all", 10_000),
        _row("arin", "reverse", "2026-08", "rr_type", "_total", 10_000),
        _row("arin", "reverse", "2026-08", "rr_type", "NS", 9_999),
        _row("arin", "reverse", "2026-08", "rr_type", "DS", 80),
        _row("arin", "reverse", "2026-08", "algorithm_ds", "_total", 80),
        # a month with delegations but no DS row at all: numerator is 0, not missing
        _row("arin", "reverse", "2009-03", "all", "all", 5_000),
        _row("arin", "reverse", "2009-03", "rr_type", "NS", 5_000),
    ])


def _one(res, metric, month="2023-12"):
    r = res[(res.metric == metric) & (res.month == month)]
    assert len(r) == 1, (metric, month, r)
    return r.iloc[0]


def test_forward_domain_count_is_ns_not_total(forward_frame):
    res = pm.compute_corpus(forward_frame, "forward", pm.FORWARD_METRICS)
    for metric in pm.DOMAIN_LEVEL_FORWARD:
        assert _one(res, metric).denominator == 1_000, metric
    assert pm.FORWARD_METRICS["ds_share"][1] == ("rr_type", "NS")
    for metric in pm.DOMAIN_LEVEL_FORWARD:
        assert pm.FORWARD_METRICS[metric][1] != ("rr_type", "_total")


def test_forward_numerators(forward_frame):
    res = pm.compute_corpus(forward_frame, "forward", pm.FORWARD_METRICS)
    assert _one(res, "ds_share").numerator == 600 and _one(res, "ds_share").pct == 60.0
    assert _one(res, "dnskey_share").numerator == 620
    assert pm.FORWARD_METRICS["dnskey_share"][0] == ("algorithm_dnskey", "_total")
    # zone-level RRSIG proxy is the RRSIG that covers DNSKEY, over NS zones
    assert pm.FORWARD_METRICS["rrsig_zone_share"] == (("rrsig_type_covered", "DNSKEY"), ("rr_type", "NS"))
    assert _one(res, "rrsig_zone_share").numerator == 619
    # name-level RRSIG share is names over names, and exceeds the zone count
    r = _one(res, "rrsig_names_share")
    assert r.numerator == 1_900 and r.denominator == 1_000_000
    assert r.numerator > _one(res, "ds_share").denominator


def test_reverse_rules(reverse_frame):
    res = pm.compute_corpus(reverse_frame, "reverse", pm.REVERSE_METRICS)
    assert pm.REVERSE_METRICS["ds_share"] == (("algorithm_ds", "_total"), ("all", "all"))
    r = _one(res, "ds_share", "2026-08")
    assert r.denominator == 10_000 and r.numerator == 80 and r.pct == 0.8
    # only DS is observable from a parent zone file
    assert set(res.metric) == {"ds_share"}
    assert "dnskey_share" not in pm.REVERSE_METRICS and "rrsig_share" not in pm.REVERSE_METRICS


def test_reverse_missing_ds_row_is_zero(reverse_frame):
    res = pm.compute_corpus(reverse_frame, "reverse", pm.REVERSE_METRICS)
    r = _one(res, "ds_share", "2009-03")
    assert r.numerator == 0 and r.denominator == 5_000 and r.pct == 0.0


def test_month_gaps():
    assert pm.month_gaps(["2020-01", "2020-02", "2020-05"]) == ["2020-03", "2020-04"]
    assert pm.month_gaps([]) == []


def test_secspider_monthly_shape(tmp_path):
    csv = tmp_path / "snap.csv"
    UCLA, VRSN = "secspider.cs.ucla.edu", "secspider.verisignlabs.com"
    pd.DataFrame([
        # newer host wins even though the UCLA capture is later in the month
        {"capture_ts": "20130101000000", "month": "2013-01", "host": VRSN, "zones_tracked": "200",
         "dnssec_enabled_zones": "120", "dnssec_verified_zones": "", "production_dnssec_zones": "80", "page_notice": ""},
        {"capture_ts": "20130115000000", "month": "2013-01", "host": UCLA, "zones_tracked": "100",
         "dnssec_enabled_zones": "60", "dnssec_verified_zones": "50", "production_dnssec_zones": "40", "page_notice": ""},
        # a capture without counts is dropped
        {"capture_ts": "20130201000000", "month": "2013-02", "host": UCLA, "zones_tracked": "",
         "dnssec_enabled_zones": "", "dnssec_verified_zones": "", "production_dnssec_zones": "", "page_notice": ""},
        # an outage page that printed zeros is dropped, not counted as 0 %
        {"capture_ts": "20130301000000", "month": "2013-03", "host": UCLA, "zones_tracked": "1849",
         "dnssec_enabled_zones": "0", "dnssec_verified_zones": "", "production_dnssec_zones": "", "page_notice": "outage"},
        # a frozen page (same four counts as the host's previous capture) is not a new month
        {"capture_ts": "20130401000000", "month": "2013-04", "host": VRSN, "zones_tracked": "200",
         "dnssec_enabled_zones": "120", "dnssec_verified_zones": "", "production_dnssec_zones": "80", "page_notice": ""},
        # a numerator above the denominator is an inconsistent page, dropped
        {"capture_ts": "20130501000000", "month": "2013-05", "host": VRSN, "zones_tracked": "300",
         "dnssec_enabled_zones": "250", "dnssec_verified_zones": "310", "production_dnssec_zones": "100", "page_notice": ""},
    ]).to_csv(csv, index=False)
    res = pm.secspider_monthly(csv)
    en = res[res.metric == "dnssec_enabled_share"]
    assert list(en.month) == ["2013-01"] and int(en.denominator.iloc[0]) == 200 and float(en.pct.iloc[0]) == 60.0
    assert list(en.source) == [VRSN]
    assert res[res.metric == "dnssec_verified_share"].empty
    assert set(res.month) == {"2013-01"}
    _, dropped = pm.secspider_usable(pd.read_csv(csv, dtype=str).fillna(""))
    assert dropped == {"no_counts": 1, "outage": 1, "frozen": 1, "inconsistent": 1}


# --------------------------------------------------------------------------- #
# endpoints against the real data
# --------------------------------------------------------------------------- #

needs_data = pytest.mark.skipif(not (SERVER.exists() and PANEL.exists()), reason="timeline parquets not present")


@needs_data
def test_endpoint_values():
    long, meta = pm.build(SERVER, PANEL, ROOT / "data/external/secspider")

    def get(corpus, source, month, metric):
        r = long[(long.corpus == corpus) & (long.source == source) & (long.month == month) & (long.metric == metric)]
        assert len(r) == 1
        return r.iloc[0]

    r = get("reverse_panel", "_pooled-afrinic-arin", "2026-08", "ds_share")
    assert (r.numerator, r.denominator) == (6_444, 744_825) and abs(r.pct - 0.8652) < 1e-3
    # Server-run reverse months relabelled +1 (scripts/fix_server_run_month_labels.py):
    # label M = snapshot at 00:00 UTC on the 1st of M, same as the panel run.
    r = get("reverse", "arin", "2026-09", "ds_share")
    assert (r.numerator, r.denominator) == (6_080, 710_116)
    r = get("reverse", "apnic", "2024-12", "ds_share")
    assert (r.numerator, r.denominator) == (3_711, 573_053)
    r = get("forward", "se", "2023-12", "ds_share")
    # pct is the mean daily share (domain_days), not the ratio of the two peaks
    assert (r.numerator, r.denominator) == (811_627, 1_339_712) and abs(r.pct - 60.6306) < 1e-3
    assert abs(r.pct - 100 * r.numerator_domain_days / r.denominator_domain_days) < 1e-3
    # .gov 2018-02: the peak ratio (21.4%) mixes days; the mean daily share is 31.2%
    r = get("forward", "gov", "2018-02", "ds_share")
    assert abs(r.pct - 31.1955) < 1e-3 and abs(100 * r.numerator / r.denominator - 21.39) < 0.01
    r = get("forward", "se", "2023-12", "dnskey_share")
    assert (r.numerator, r.denominator) == (840_009, 1_339_712)
    r = get("forward", "se", "2023-12", "rrsig_zone_share")
    assert (r.numerator, r.denominator) == (839_978, 1_339_712)
    r = get("forward", "se", "2023-12", "rrsig_names_share")
    assert (r.numerator, r.denominator) == (2_571_213, 3_663_131)
    r = get("forward", "gov", "2023-12", "dnskey_share")
    assert (r.numerator, r.denominator) == (1_766, 9_636)
    r = get("forward", "fed.us", "2022-10", "ds_share")
    assert (r.numerator, r.denominator) == (0, 1)
    assert meta["headline"]["reverse_panel"]["_pooled-afrinic-arin"]["ds_share"]["month"] == "2026-08"


SECSPIDER_CSV = ROOT / "data/external/secspider/secspider_wayback_snapshots.csv"


@pytest.mark.skipif(not SECSPIDER_CSV.exists(), reason="SecSpider snapshot CSV not present")
def test_secspider_endpoints():
    res = pm.secspider_monthly(SECSPIDER_CSV)

    def get(month, metric):
        r = res[(res.month == month) & (res.metric == metric)]
        assert len(r) == 1, (month, metric)
        return r.iloc[0]

    # first capture with the summary block (UCLA, 2006-09-02)
    r = get("2006-09", "dnssec_enabled_share")
    assert (r.numerator, r.denominator) == (87, 130)
    # 2012 overlap: the Verisign page was frozen at 42,084 zones from 2012-01 to
    # 2012-10, so its repeats drop and the moving UCLA page carries those months
    r = get("2012-01", "dnssec_enabled_share")
    assert r.source == "secspider.verisignlabs.com" and r.denominator == 42_084
    assert (res[res.metric == "dnssec_enabled_share"].denominator == 42_084).sum() == 1
    # the UCLA 2012-02 and 2012-06 captures repeat its 2011-12 page and drop too;
    # 2012-08 is the next real UCLA observation
    assert not {"2012-02", "2012-03", "2012-05", "2012-06", "2012-07"} & set(res.month)
    r = get("2012-08", "dnssec_enabled_share")
    assert r.source == "secspider.cs.ucla.edu" and (r.numerator, r.denominator) == (37_191, 74_223)
    r = get("2012-11", "dnssec_enabled_share")
    assert r.source == "secspider.verisignlabs.com" and (r.numerator, r.denominator) == (36_963, 52_850)
    # the 2007-08 outage page (1849 zones, 0 enabled) and the inconsistent
    # 2021-12 page (960,264 zones, 1,135,208 production) are not data points
    assert "2007-08" not in set(res.month) and "2021-12" not in set(res.month)
    assert (res.numerator <= res.denominator).all()
    # last Wayback capture before the live row
    r = get("2026-05", "dnssec_enabled_share")
    assert (r.numerator, r.denominator) == (15_733_833, 20_064_857)
    # the denominator is SecSpider's own tracked set, so shares are high by construction
    en = res[res.metric == "dnssec_enabled_share"]
    assert en.pct.median() > 50
    assert res.source.isin(pm.SECSPIDER_HOST_RANK).all()


@needs_data
def test_forward_rrsig_proxy_tracks_dnskey():
    long, _ = pm.build(SERVER, PANEL, ROOT / "data/external/secspider")
    f = long[(long.corpus == "forward") & (long.source != "fed.us")]
    dk = f[f.metric == "dnskey_share"].set_index(["source", "month"]).numerator
    rz = f[f.metric == "rrsig_zone_share"].set_index(["source", "month"]).numerator
    ratio = (rz / dk).dropna()
    assert ratio.min() > 0.99 and ratio.max() <= 1.0


@needs_data
def test_forward_share_never_exceeds_100_at_zone_level():
    long, _ = pm.build(SERVER, PANEL, ROOT / "data/external/secspider")
    f = long[(long.corpus == "forward") & (long.metric.isin(pm.DOMAIN_LEVEL_FORWARD))]
    assert f.pct.max() <= 100.0


@pytest.mark.skipif(not (CSV.exists() and JSON.exists()), reason="run scripts/prevalence_metrics.py first")
def test_written_outputs_agree():
    long = pd.read_csv(CSV, dtype={"month": str})
    meta = json.loads(JSON.read_text())
    assert list(long.columns) == ["corpus", "source", "month", "metric", "numerator", "denominator",
                                  "numerator_domain_days", "denominator_domain_days", "pct", "measured_days"]
    assert meta["rows"] == len(long)
    h = meta["headline"]["forward"]["se"]["ds_share"]
    r = long[(long.corpus == "forward") & (long.source == "se") & (long.metric == "ds_share")].sort_values("month").iloc[-1]
    assert h["month"] == r.month and h["numerator"] == r.numerator and h["denominator"] == r.denominator
    assert not ((long.corpus == "reverse") & (long.metric != "ds_share")).any()
    if SECSPIDER_CSV.exists():
        assert meta["secspider"]["status"] == "available"
        assert (long.corpus == "secspider").any()
