"""Analysis semantics that have already been got wrong once.

The distinction pinned hardest here is between "the corpus cannot answer this"
and "the corpus was asked and the answer is no". Collapsing them is how RFC 9905
reported zero observations while 15,966 non-conforming records sat in the corpus,
and how a blank cell in a results table came to mean two opposite things.
"""
from __future__ import annotations

import pandas as pd
import pytest

from openintel_rfc.timeline_analysis import (
    bottom_up, compare_directions, prevalence_series, top_down,
)


def _timeline(rows):
    return pd.DataFrame(
        rows,
        columns=["source", "basis", "month", "dimension", "value",
                 "records", "domain_days", "domains_peak", "measured_days"],
    )


def _row(month, dimension, value, records, domains):
    return ["rev", "reverse", month, dimension, value, records, domains, domains, 1]


CONFIG = {
    "stages": {"partial_usage_pct": 1.0, "common_usage_pct": 10.0, "min_zones": 10},
    "bottom_up": {
        "enabled": True,
        "groups": {"G": {"label": "Group", "what_must_change": "x", "evidence": "y"}},
        "changes": [{
            "key": "alg_13", "label": "ECDSAP256", "dimension": "algorithm_ds",
            "value": "13", "rfc": "RFC 6605", "published": "2012-04",
            "group": "G", "observable": "algorithm = 13",
        }],
    },
    "top_down": {
        "enabled": True,
        "categories": [{
            "key": "crypto", "label": "Crypto", "description": "d",
            "rfcs": ["RFC 6605", "RFC 9999"],
        }],
    },
}


# --------------------------------------------------------------------------- #
# The distinction that matters
# --------------------------------------------------------------------------- #

def test_absent_dimension_is_no_corpus_coverage():
    """No denominator: the corpus cannot carry this record type at all."""
    timeline = _timeline([_row("2020-01", "rr_type", "NS", 100, 100)])
    rows = bottom_up(timeline, CONFIG)
    assert rows[0]["state"] == "no_corpus_coverage"
    assert rows[0]["measurable_here"] is False


def test_present_dimension_with_no_matching_value_is_a_real_null():
    """A denominator exists and the value never appears: a genuine negative."""
    timeline = _timeline([
        _row("2020-01", "algorithm_ds", "_total", 100, 100),
        _row("2020-01", "algorithm_ds", "8", 100, 100),
    ])
    rows = bottom_up(timeline, CONFIG)
    assert rows[0]["state"] == "scanned_no_match"
    assert rows[0]["measurable_here"] is True, "we could see it; it was not there"
    assert rows[0]["t1_first_seen"] is None


# --------------------------------------------------------------------------- #
# Stages
# --------------------------------------------------------------------------- #

def test_stages_and_the_intervals_between_them():
    timeline = _timeline([
        _row("2015-01", "algorithm_ds", "_total", 1000, 1000),
        _row("2015-01", "algorithm_ds", "13", 12, 12),      # 1.2%, >=10 zones
        _row("2016-01", "algorithm_ds", "_total", 1000, 1000),
        _row("2016-01", "algorithm_ds", "13", 200, 200),    # 20%
    ])
    row = bottom_up(timeline, CONFIG)[0]
    assert row["t1_first_seen"] == "2015-01"
    assert row["t2_partial_usage"] == "2015-01"
    assert row["t3_common_usage"] == "2016-01"
    assert row["ascent_years"] == pytest.approx(1.0)
    assert row["state"] == "common"


def test_min_zones_guard_blocks_a_threshold_met_by_a_handful_of_names():
    """1% of a tiny population is one name; the guard is what stops that."""
    timeline = _timeline([
        _row("2011-05", "algorithm_ds", "_total", 32, 32),
        _row("2011-05", "algorithm_ds", "13", 1, 1),   # 3.1% but a single zone
        _row("2019-01", "algorithm_ds", "_total", 1000, 1000),
        _row("2019-01", "algorithm_ds", "13", 50, 50),  # 5%, 50 zones
    ])
    row = bottom_up(timeline, CONFIG)[0]
    assert row["t1_first_seen"] == "2011-05", "existence still records the one zone"
    assert row["zones_at_first_seen"] == 1
    assert row["t2_partial_usage"] == "2019-01", "not credited to the single zone"


def test_first_sighting_at_corpus_start_is_flagged_left_censored():
    timeline = _timeline([
        _row("2018-01", "algorithm_ds", "_total", 100, 100),
        _row("2018-01", "algorithm_ds", "13", 50, 50),
    ])
    row = bottom_up(timeline, CONFIG)[0]
    assert row["left_censored"] is True
    assert row["corpus_starts"] == "2018-01"


def test_a_later_first_sighting_is_not_censored():
    timeline = _timeline([
        _row("2018-01", "algorithm_ds", "_total", 100, 100),
        _row("2019-01", "algorithm_ds", "_total", 100, 100),
        _row("2019-01", "algorithm_ds", "13", 50, 50),
    ])
    row = bottom_up(timeline, CONFIG)[0]
    assert row["left_censored"] is False
    assert row["onset_years"] == pytest.approx(6.75, abs=0.01)


def test_multi_value_change_unions_its_codepoints():
    """RFC 9905 covers algorithms 5 and 7 as one deprecation."""
    config = {**CONFIG, "bottom_up": {**CONFIG["bottom_up"], "changes": [
        {**CONFIG["bottom_up"]["changes"][0], "value": "5|7"}]}}
    timeline = _timeline([
        _row("2020-01", "algorithm_ds", "_total", 100, 100),
        _row("2020-01", "algorithm_ds", "5", 30, 30),
        _row("2020-01", "algorithm_ds", "7", 20, 20),
    ])
    series = prevalence_series(timeline, "algorithm_ds", "5|7")
    assert int(series.records.iloc[0]) == 50


# --------------------------------------------------------------------------- #
# Top-down, and the two directions meeting
# --------------------------------------------------------------------------- #

def test_top_down_reports_rfcs_it_has_no_evidence_for():
    """A taxonomy that outruns the data must say so rather than average over it."""
    timeline = _timeline([
        _row("2020-01", "algorithm_ds", "_total", 100, 100),
        _row("2020-01", "algorithm_ds", "13", 50, 50),
    ])
    rows = bottom_up(timeline, CONFIG)
    categories = top_down(timeline, CONFIG, rows)
    assert categories[0]["rfcs_without_observables"] == ["RFC 9999"]
    assert categories[0]["observable_changes"] == 1


def test_comparison_crosswalks_groups_to_categories():
    timeline = _timeline([
        _row("2020-01", "algorithm_ds", "_total", 100, 100),
        _row("2020-01", "algorithm_ds", "13", 50, 50),
    ])
    rows = bottom_up(timeline, CONFIG)
    categories = top_down(timeline, CONFIG, rows)
    comparison = compare_directions(rows, categories, CONFIG)
    assert comparison["group_to_category"][0]["categories"] == {"crypto": 1}
    assert comparison["categories_without_observables"] == []
