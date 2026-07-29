"""Adoption timelines: when the corpus first recorded qualifying evidence.

``first_seen`` is the headline number of the whole study, so the tests below
pin down exactly which observations are allowed to set it: a valid (or
ambiguous) match whose timestamp postdates the RFC, and nothing else.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from openintel_rfc.matcher import match_all
from openintel_rfc.models import RFCChecklistDB
from openintel_rfc.timeline import (
    DEFAULT_ADOPTION_DECISIONS,
    build_timeline,
    monthly_buckets,
    timeline_to_rows,
    yearly_buckets,
)
from openintel_rfc.utils import PipelineError


def _entry(entries, rfc_id: str):
    for entry in entries:
        if entry.rfc_id == rfc_id:
            return entry
    raise AssertionError(f"{rfc_id} has no timeline entry")


@pytest.fixture
def nsec3_matches(signal_factory, checklist_db, schema_report):
    """Three NSEC3 observations spread over two years, plus one CDS row."""
    signals = [
        signal_factory("2010-06-15", signal_id="sig_0001", rr_type="NSEC3", algorithm=1),
        signal_factory("2010-09-20", signal_id="sig_0002", rr_type="NSEC3", algorithm=1),
        signal_factory(
            "2011-03-09",
            signal_id="sig_0003",
            rr_type="NSEC3PARAM",
            algorithm=1,
            domain="example.com",
            zone="com",
        ),
    ]
    matches, _ = match_all(signals, checklist_db, schema_report)
    return matches


# --------------------------------------------------------------------------- #
# first_seen
# --------------------------------------------------------------------------- #


def test_first_seen_is_the_earliest_qualifying_observation(
    nsec3_matches, checklist_db: RFCChecklistDB
) -> None:
    timeline = build_timeline(nsec3_matches, checklist_db)

    rfc5155 = _entry(timeline, "RFC 5155")
    assert rfc5155.first_seen == datetime(2010, 6, 15)
    assert rfc5155.last_seen == datetime(2011, 3, 9)
    assert rfc5155.observation_count == 3


def test_days_from_publication_to_first_seen_is_the_gap_in_days(
    nsec3_matches, checklist_db: RFCChecklistDB
) -> None:
    """RFC 5155 was published 2008-03-01; the first observation is 2010-06-15."""
    timeline = build_timeline(nsec3_matches, checklist_db)

    rfc5155 = _entry(timeline, "RFC 5155")
    expected = (datetime(2010, 6, 15) - datetime(2008, 3, 1)).days
    assert expected == 836
    assert rfc5155.days_from_publication_to_first_seen == expected


def test_distinct_domains_and_zones_are_counted_not_summed(
    nsec3_matches, checklist_db: RFCChecklistDB
) -> None:
    rfc5155 = _entry(build_timeline(nsec3_matches, checklist_db), "RFC 5155")

    assert rfc5155.domains == ["example.com", "example.nl"]
    assert rfc5155.distinct_domains == 2
    assert rfc5155.zones == ["com", "nl"]
    assert rfc5155.distinct_zones == 2


def test_a_partial_match_never_sets_first_seen(
    signal_factory, checklist_db, schema_report
) -> None:
    """A partial match means the mechanism was not confirmed; counting it inflates adoption."""
    signals = [signal_factory("2019-04-12", rr_type="CDS")]
    matches, _ = match_all(signals, checklist_db, schema_report)
    assert any(m.rfc_id == "RFC 8078" and m.decision == "partial_match" for m in matches)

    timeline = build_timeline(matches, checklist_db)

    rfc8078 = _entry(timeline, "RFC 8078")
    assert rfc8078.first_seen is None
    assert rfc8078.observation_count == 0
    assert "1 partial_match" in rfc8078.notes


def test_ambiguous_matches_do_count_by_default(
    signal_factory, checklist_db, schema_report
) -> None:
    """The indicators did all match; what is in doubt is attribution, not observation."""
    signals = [signal_factory("2019-11-06", rr_type="DNSKEY", algorithm=15)]
    matches, _ = match_all(signals, checklist_db, schema_report)

    timeline = build_timeline(matches, checklist_db)

    assert "ambiguous" in DEFAULT_ADOPTION_DECISIONS
    rfc8624 = _entry(timeline, "RFC 8624")
    assert rfc8624.first_seen == datetime(2019, 11, 6)


def test_excluding_ambiguous_leaves_rfc8624_unseen(
    signal_factory, checklist_db, schema_report
) -> None:
    signals = [signal_factory("2019-11-06", rr_type="DNSKEY", algorithm=15)]
    matches, _ = match_all(signals, checklist_db, schema_report)

    timeline = build_timeline(matches, checklist_db, include_decisions=("valid_match",))

    rfc8624 = _entry(timeline, "RFC 8624")
    assert rfc8624.first_seen is None
    assert "1 ambiguous" in rfc8624.notes


# --------------------------------------------------------------------------- #
# Coverage of the whole checklist
# --------------------------------------------------------------------------- #


def test_every_rfc_in_the_checklist_gets_an_entry(
    nsec3_matches, checklist_db: RFCChecklistDB
) -> None:
    timeline = build_timeline(nsec3_matches, checklist_db)

    assert {entry.rfc_id for entry in timeline} == set(checklist_db.rfc_ids)


def test_never_observed_rfcs_sort_last_and_say_why(
    nsec3_matches, checklist_db: RFCChecklistDB
) -> None:
    timeline = build_timeline(nsec3_matches, checklist_db)

    seen = [entry for entry in timeline if entry.first_seen is not None]
    unseen = [entry for entry in timeline if entry.first_seen is None]
    assert timeline == seen + unseen, "never-seen RFCs sort after the observed ones"
    assert [entry.first_seen for entry in seen] == sorted(e.first_seen for e in seen)

    rfc8078 = _entry(timeline, "RFC 8078")
    assert rfc8078.observation_count == 0
    assert "A null first_seen is not evidence of non-adoption" in rfc8078.notes
    assert "Check the review queue" in rfc8078.notes


def test_an_rfc_only_present_in_the_matches_still_gets_an_entry(
    nsec3_matches, checklist_db: RFCChecklistDB
) -> None:
    stranger = nsec3_matches[0].model_copy(
        update={"rfc_id": "RFC 9999", "rfc_title": "Not in the checklist"}
    )

    timeline = build_timeline([*nsec3_matches, stranger], checklist_db)

    assert _entry(timeline, "RFC 9999").rfc_title == "Not in the checklist"


# --------------------------------------------------------------------------- #
# Buckets
# --------------------------------------------------------------------------- #


def test_monthly_buckets_omit_periods_with_no_observation(nsec3_matches) -> None:
    rfc5155 = [m for m in nsec3_matches if m.rfc_id == "RFC 5155"]

    buckets = monthly_buckets(rfc5155)

    assert [bucket.period for bucket in buckets] == ["2010-06", "2010-09", "2011-03"]
    assert [bucket.count for bucket in buckets] == [1, 1, 1]
    assert all(bucket.mean_score == pytest.approx(17.25) for bucket in buckets)


def test_yearly_buckets_aggregate_the_same_observations(nsec3_matches) -> None:
    rfc5155 = [m for m in nsec3_matches if m.rfc_id == "RFC 5155"]

    buckets = yearly_buckets(rfc5155)

    assert [(bucket.period, bucket.count) for bucket in buckets] == [("2010", 2), ("2011", 1)]


def test_confidence_over_time_mirrors_the_monthly_grouping(
    nsec3_matches, checklist_db: RFCChecklistDB
) -> None:
    rfc5155 = _entry(build_timeline(nsec3_matches, checklist_db), "RFC 5155")

    assert [b.period for b in rfc5155.confidence_over_time] == [
        b.period for b in rfc5155.monthly_counts
    ]
    assert rfc5155.confidence_over_time is not rfc5155.monthly_counts


def test_bucketing_can_be_told_the_matches_are_already_filtered(nsec3_matches) -> None:
    rfc5155 = [m for m in nsec3_matches if m.rfc_id == "RFC 5155"]

    assert monthly_buckets(rfc5155, include_decisions=None) == monthly_buckets(rfc5155)


# --------------------------------------------------------------------------- #
# Validation and flat rendering
# --------------------------------------------------------------------------- #


def test_build_timeline_rejects_an_unknown_decision_name(
    nsec3_matches, checklist_db: RFCChecklistDB
) -> None:
    with pytest.raises(PipelineError, match="Unknown decision value"):
        build_timeline(nsec3_matches, checklist_db, include_decisions=("valid",))


def test_build_timeline_rejects_an_empty_decision_filter(
    nsec3_matches, checklist_db: RFCChecklistDB
) -> None:
    with pytest.raises(PipelineError, match="would count nothing"):
        build_timeline(nsec3_matches, checklist_db, include_decisions=())


def test_timeline_to_rows_renders_buckets_into_single_cells(
    nsec3_matches, checklist_db: RFCChecklistDB
) -> None:
    timeline = build_timeline(nsec3_matches, checklist_db)

    rows = timeline_to_rows(timeline)

    assert len(rows) == len(timeline)
    rfc5155 = next(row for row in rows if row["rfc_id"] == "RFC 5155")
    assert rfc5155["monthly_counts"] == "2010-06=1; 2010-09=1; 2011-03=1"
    assert rfc5155["yearly_counts"] == "2010=2; 2011=1"
    assert rfc5155["first_seen"] == "2010-06-15T00:00:00"
    assert rfc5155["domains"] == "example.com; example.nl"

    rfc8078 = next(row for row in rows if row["rfc_id"] == "RFC 8078")
    assert rfc8078["first_seen"] == ""
    assert rfc8078["days_from_publication_to_first_seen"] == ""


# --------------------------------------------------------------------------- #
# The real run
# --------------------------------------------------------------------------- #


def test_the_analyze_run_reports_first_seen_for_rfc8078_after_publication(
    analyzed_output: Path,
) -> None:
    import json

    from openintel_rfc import config

    payload = json.loads(
        (analyzed_output / config.OUTPUT_FILES["adoption_timeline"]).read_text(encoding="utf-8")
    )
    entries = {entry["rfc_id"]: entry for entry in payload["timeline"]}

    rfc8078 = entries["RFC 8078"]
    assert rfc8078["first_seen"].startswith("2018-05-01")
    assert rfc8078["days_from_publication_to_first_seen"] == 426
    # The five pre-publication CDS rows are reported, but only as excluded.
    assert "5 timestamp_invalid" in rfc8078["notes"]
