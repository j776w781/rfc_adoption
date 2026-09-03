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
    cross_reference,
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


# --------------------------------------------------------------------------- #
# Cross-corpus comparison
# --------------------------------------------------------------------------- #

XREF_CONFIG = {
    **CONFIG,
    "cross_reference": {
        "comparable_dimensions": ["algorithm_ds"],
        "incomparable_dimensions": ["rr_type"],
        "incomparable_reason": "record-type composition differs",
    },
}


#: Forward/reverse is decided by `basis`, so test rows have to carry a real one.
_BASIS = {"arin": "reverse", "afrinic": "reverse", "apnic": "reverse",
          "lacnic": "reverse", "se": "zonefile", "gov": "zonefile", "nu": "zonefile"}


def _row_src(source, month, dimension, value, records, domains):
    return [source, _BASIS.get(source, "zonefile"), month, dimension, value,
            records, domains, domains, 1]


def test_cross_reference_needs_both_sides():
    timeline = _timeline([
        _row_src("arin", "2020-01", "algorithm_ds", "_total", 100, 100),
        _row_src("arin", "2020-01", "algorithm_ds", "13", 50, 50),
    ])
    out = cross_reference(timeline, XREF_CONFIG)
    assert out["comparisons"] == []
    assert "missing corpus" in out["notes"][0]


def test_cross_reference_takes_the_earlier_first_sighting():
    """The Ed25519 lesson: existence is a minimum over ALL evidence."""
    timeline = _timeline([
        # forward sees it in 2021; reverse not until 2022
        _row_src("se", "2021-01", "algorithm_ds", "_total", 100, 100),
        _row_src("se", "2021-01", "algorithm_ds", "13", 10, 10),
        _row_src("arin", "2021-01", "algorithm_ds", "_total", 100, 100),
        _row_src("arin", "2022-01", "algorithm_ds", "_total", 100, 100),
        _row_src("arin", "2022-01", "algorithm_ds", "13", 20, 20),
        _row_src("se", "2022-01", "algorithm_ds", "_total", 100, 100),
        _row_src("se", "2022-01", "algorithm_ds", "13", 20, 20),
    ])
    out = cross_reference(timeline, XREF_CONFIG)
    c = out["comparisons"][0]
    assert c["forward_first_seen"] == "2021-01"
    assert c["reverse_first_seen"] == "2022-01"
    assert c["earliest_first_seen"] == "2021-01"
    assert c["earlier_corpus"] == "forward"
    assert any("EARLIER in the forward" in n for n in out["notes"])


def test_cross_reference_skips_incomparable_dimensions():
    """A record-type share differs by composition alone; never difference it."""
    config = {**XREF_CONFIG, "bottom_up": {**CONFIG["bottom_up"], "changes": [
        {**CONFIG["bottom_up"]["changes"][0], "dimension": "rr_type", "value": "DS"}]}}
    timeline = _timeline([
        _row_src("se", "2020-01", "rr_type", "_total", 100, 100),
        _row_src("se", "2020-01", "rr_type", "DS", 8, 8),
        _row_src("arin", "2020-01", "rr_type", "_total", 100, 100),
        _row_src("arin", "2020-01", "rr_type", "DS", 100, 100),
    ])
    out = cross_reference(timeline, config)
    assert out["comparisons"] == [], "rr_type is not comparable across corpora"


def test_multi_value_domains_are_not_double_counted():
    """A zone publishing both alg 5 and alg 7 is one zone, not two.

    Summing per-value domain counts gave RFC 9905 a share of 120% of its own
    population. Records still add (they are disjoint); domains take the largest
    single value as a lower bound on the union.
    """
    timeline = _timeline([
        _row("2026-01", "algorithm_ds", "_total", 100, 100),
        _row("2026-01", "algorithm_ds", "5", 60, 60),
        _row("2026-01", "algorithm_ds", "7", 60, 60),
    ])
    series = prevalence_series(timeline, "algorithm_ds", "5|7")
    assert int(series.records.iloc[0]) == 120, "records are disjoint and add"
    assert int(series.domains_peak.iloc[0]) == 60, "domains must not be summed"
    assert series.share_pct.iloc[0] <= 100.0


def test_corpus_side_comes_from_basis_not_source_name():
    """A forward source named after an RIR must not be filed as reverse."""
    timeline = _timeline([
        _row_src("ripe", "2026-01", "algorithm_ds", "_total", 10, 10),
        _row_src("arin", "2026-01", "algorithm_ds", "_total", 10, 10),
    ])
    timeline.loc[timeline.source == "ripe", "basis"] = "zonefile"
    timeline.loc[timeline.source == "arin", "basis"] = "reverse"
    out = cross_reference(timeline, XREF_CONFIG)
    assert out["forward_sources"] == ["ripe"]
    assert out["reverse_sources"] == ["arin"]


def test_a_deprecation_has_no_onset():
    """Publication-to-first-sighting is negative for a deprecation and meaningless.

    RFC 9905 (2025-11) deprecates algorithm 5, which has been in the data since
    2009. Reporting that as an onset of -13.7 years is not a slow adoption; it is
    a category error. Residue is the quantity for these.
    """
    config = {**CONFIG, "bottom_up": {**CONFIG["bottom_up"], "changes": [
        {**CONFIG["bottom_up"]["changes"][0], "value": "5",
         "published": "2025-11", "residue": True}]}}
    timeline = _timeline([
        _row("2009-04", "algorithm_ds", "_total", 100, 100),
        _row("2009-04", "algorithm_ds", "5", 50, 50),
        _row("2026-01", "algorithm_ds", "_total", 100, 100),
        _row("2026-01", "algorithm_ds", "5", 10, 10),
    ])
    row = bottom_up(timeline, config)[0]
    assert row["onset_years"] is None, "a deprecation has no onset"
    assert row["state"] == "residue"
    assert row["residue_share_pct"] == 10.0


# --------------------------------------------------------------------------- #
# Plain-language description: where it is now vs the furthest it ever got
# --------------------------------------------------------------------------- #

def test_reached_and_retreated_is_not_the_same_as_never_reached():
    """The case that exposed the old single label.

    RSA/SHA-512 sat at 0.37% having peaked at 3.7%; Ed25519 sat at 0.34% having
    never exceeded 0.37%. One label meaning "furthest ever reached" but reading
    as present tense put nearly identical numbers in different categories with
    no way to see why.
    """
    retreated = _timeline([
        _row("2015-01", "algorithm_ds", "_total", 1000, 1000),
        _row("2015-01", "algorithm_ds", "13", 40, 40),      # 4% — in use
        _row("2026-01", "algorithm_ds", "_total", 1000, 1000),
        _row("2026-01", "algorithm_ds", "13", 4, 4),        # 0.4% — seen only
    ])
    never = _timeline([
        _row("2015-01", "algorithm_ds", "_total", 1000, 1000),
        _row("2015-01", "algorithm_ds", "13", 3, 3),
        _row("2026-01", "algorithm_ds", "_total", 1000, 1000),
        _row("2026-01", "algorithm_ds", "13", 4, 4),        # 0.4%, never higher
    ])
    a = bottom_up(retreated, CONFIG)[0]
    b = bottom_up(never, CONFIG)[0]

    assert a["now"] == "seen only" and a["peak_reached"] == "in use"
    assert b["now"] == "seen only" and b["peak_reached"] == "seen only"
    assert a["trend"] == "declining"
    assert "Was in use" in a["summary"], a["summary"]
    # Both sit at the same share today, and the summaries say different things.
    assert a["current_share_pct"] == b["current_share_pct"]
    assert a["summary"] != b["summary"]


def test_a_tiny_movement_is_steady_not_a_decline():
    """A ratio is hysterical about small numbers; 0.03pp is not a trend."""
    timeline = _timeline([
        _row("2025-01", "algorithm_ds", "_total", 10000, 10000),
        _row("2025-01", "algorithm_ds", "13", 37, 37),      # 0.37%
        _row("2026-01", "algorithm_ds", "_total", 10000, 10000),
        _row("2026-01", "algorithm_ds", "13", 34, 34),      # 0.34%
    ])
    row = bottom_up(timeline, CONFIG)[0]
    assert row["trend"] == "steady", row["summary"]


def test_a_real_decline_is_named_as_one():
    timeline = _timeline([
        _row("2017-01", "algorithm_ds", "_total", 1000, 1000),
        _row("2017-01", "algorithm_ds", "13", 750, 750),    # 75%
        _row("2026-01", "algorithm_ds", "_total", 1000, 1000),
        _row("2026-01", "algorithm_ds", "13", 220, 220),    # 22%
    ])
    row = bottom_up(timeline, CONFIG)[0]
    assert row["trend"] == "declining"
    assert row["now"] == "widely used" and row["peak_reached"] == "widely used"
    assert "down from" in row["summary"]


def test_something_at_its_own_peak_is_rising():
    timeline = _timeline([
        _row("2020-01", "algorithm_ds", "_total", 1000, 1000),
        _row("2020-01", "algorithm_ds", "13", 100, 100),
        _row("2026-01", "algorithm_ds", "_total", 1000, 1000),
        _row("2026-01", "algorithm_ds", "13", 680, 680),
    ])
    row = bottom_up(timeline, CONFIG)[0]
    assert row["trend"] == "rising"
    assert "its highest" in row["summary"]


def test_an_unfound_value_says_so_plainly():
    timeline = _timeline([
        _row("2020-01", "algorithm_ds", "_total", 100, 100),
        _row("2020-01", "algorithm_ds", "8", 100, 100),
    ])
    row = bottom_up(timeline, CONFIG)[0]
    assert row["now"] == "not seen"
    assert row["summary"] == "Looked for and not found in this corpus."
