"""Adoption timelines built from RFC matches, with a hard publication-date cutoff.

This module answers one question per RFC: *when did the corpus first record an
observation that qualifies as evidence for this RFC, and how did that evidence
accumulate over time?*

The cutoff logic is the whole point of the module. An observation recorded
before an RFC existed cannot be evidence of adopting it, so a match whose
decision is ``timestamp_invalid`` must never set ``first_seen``. Partial
matches are excluded for a weaker but equally deliberate reason: a partial
match means the pipeline could not confirm the mechanism, and counting it would
inflate the headline "adoption started at X" result. Callers who want a
different rule pass ``include_decisions`` explicitly; the default counts only
``valid_match`` and ``ambiguous``.

Two properties of the output are worth stating because they change how the
numbers should be read:

* Months with no qualifying observation are **omitted, not zero-filled**. A gap
  in the bucket list means "no qualifying observation in the corpus", which is
  not the same as "no deployment".
* Every count is a count of *observations*, i.e. of measured records. The
  distinct domain / zone counts are the honest denominators for deployment
  breadth; the raw observation count is a measurement-volume number.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Any, get_args

from .models import (
    AdoptionTimelineEntry,
    Decision,
    RFCChecklistDB,
    RFCMatch,
    TimelineBucket,
)
from .utils import PipelineError, get_logger, iso, month_key, round_score, unique_sorted, year_key

__all__ = [
    "DEFAULT_ADOPTION_DECISIONS",
    "build_timeline",
    "monthly_buckets",
    "yearly_buckets",
    "timeline_to_rows",
]

LOGGER = get_logger(__name__)

#: Decisions that count as adoption evidence unless the caller says otherwise.
#: ``ambiguous`` is included because the indicators *did* all match; what is in
#: doubt is attribution, which the review queue handles separately.
DEFAULT_ADOPTION_DECISIONS: tuple[str, ...] = ("valid_match", "ambiguous")

#: Every legal value of :data:`openintel_rfc.models.Decision`.
_ALL_DECISIONS: frozenset[str] = frozenset(get_args(Decision))

#: Sentinel used to push never-seen RFCs to the end of the sorted timeline.
_NEVER_SEEN_SORT_KEY = datetime.max


# --------------------------------------------------------------------------- #
# Filtering: the publication-date cutoff
# --------------------------------------------------------------------------- #


def _validate_decisions(include_decisions: Sequence[str]) -> tuple[str, ...]:
    """Normalize and validate the caller's decision filter.

    Raises rather than silently ignoring an unknown decision name: a typo like
    ``"valid"`` would otherwise produce an empty, plausible-looking timeline.
    """
    decisions = tuple(include_decisions)
    if not decisions:
        raise PipelineError(
            "include_decisions is empty; the timeline would count nothing. "
            f"Pass at least one of: {', '.join(sorted(_ALL_DECISIONS))}."
        )
    unknown = [d for d in decisions if d not in _ALL_DECISIONS]
    if unknown:
        raise PipelineError(
            f"Unknown decision value(s) in include_decisions: {', '.join(unknown)}. "
            f"Valid values: {', '.join(sorted(_ALL_DECISIONS))}."
        )
    return decisions


def _qualifying_matches(
    matches: Sequence[RFCMatch], include_decisions: Sequence[str]
) -> list[RFCMatch]:
    """Return the matches that may contribute to adoption counts.

    Two filters are applied, and the second one is deliberately redundant:

    1. ``match.decision`` must appear in ``include_decisions``.
    2. ``match.timestamp_valid`` must be true.

    Rule 2 makes the cutoff invariant structural rather than conventional: even
    if a caller passes ``include_decisions=("timestamp_invalid",)``, an
    observation that predates its RFC still cannot set ``first_seen``. A match
    that passes rule 1 but fails rule 2 means the matcher produced an
    inconsistent record, so it is logged rather than dropped in silence.
    """
    allowed = set(include_decisions)
    qualifying: list[RFCMatch] = []
    for match in matches:
        if match.decision not in allowed:
            continue
        if not match.timestamp_valid:
            LOGGER.warning(
                "Excluding %s/%s from the timeline: decision is %r but timestamp_valid is "
                "False (observation %s predates publication %s). An observation older than "
                "the RFC cannot be adoption evidence.",
                match.signal_id,
                match.rfc_id,
                match.decision,
                iso(match.observation_timestamp),
                iso(match.rfc_publication_date),
            )
            continue
        qualifying.append(match)
    # Stable, explicit order so buckets and example lists are byte-reproducible.
    qualifying.sort(key=lambda m: (m.observation_timestamp, m.signal_id, m.rfc_id))
    return qualifying


# --------------------------------------------------------------------------- #
# Bucketing
# --------------------------------------------------------------------------- #


def _bucket(
    matches: Sequence[RFCMatch], key_fn: Callable[[datetime], str]
) -> list[TimelineBucket]:
    """Group matches into period buckets, omitting periods with no observations."""
    grouped: dict[str, list[RFCMatch]] = defaultdict(list)
    for match in matches:
        grouped[key_fn(match.observation_timestamp)].append(match)

    buckets: list[TimelineBucket] = []
    for period in sorted(grouped):
        members = grouped[period]
        domains = {m.domain for m in members if m.domain}
        mean_score = sum(m.score for m in members) / len(members)
        buckets.append(
            TimelineBucket(
                period=period,
                count=len(members),
                domains=len(domains),
                mean_score=round_score(mean_score),
            )
        )
    return buckets


def monthly_buckets(
    matches: Sequence[RFCMatch],
    *,
    include_decisions: Sequence[str] | None = DEFAULT_ADOPTION_DECISIONS,
) -> list[TimelineBucket]:
    """Bucket matches by calendar month (``YYYY-MM``).

    By default only qualifying matches are counted, so the safe behaviour is
    also the default one. Pass ``include_decisions=None`` to bucket every match
    given, which is what you want when the caller has already filtered.

    Periods with no observation are omitted; ``mean_score`` is the arithmetic
    mean of the per-match scores in the bucket and ``domains`` is the count of
    distinct non-empty domains.
    """
    selected = (
        list(matches)
        if include_decisions is None
        else _qualifying_matches(matches, _validate_decisions(include_decisions))
    )
    return _bucket(selected, month_key)


def yearly_buckets(
    matches: Sequence[RFCMatch],
    *,
    include_decisions: Sequence[str] | None = DEFAULT_ADOPTION_DECISIONS,
) -> list[TimelineBucket]:
    """Bucket matches by calendar year (``YYYY``). See :func:`monthly_buckets`."""
    selected = (
        list(matches)
        if include_decisions is None
        else _qualifying_matches(matches, _validate_decisions(include_decisions))
    )
    return _bucket(selected, year_key)


# --------------------------------------------------------------------------- #
# Notes: what the entry does and does not show
# --------------------------------------------------------------------------- #


def _excluded_summary(excluded_by_decision: dict[str, int]) -> str:
    """Render the observations that were seen for this RFC but did not count."""
    if not excluded_by_decision:
        return ""
    parts = [
        f"{count} {decision}" for decision, count in sorted(excluded_by_decision.items())
    ]
    return f"Also observed but not counted: {', '.join(parts)}. "


def _seen_notes(
    *,
    rfc_id: str,
    decisions: Sequence[str],
    observation_count: int,
    first_seen: datetime,
    last_seen: datetime,
    publication_date: datetime,
    days_to_first_seen: int,
    distinct_domains: int,
    distinct_zones: int,
    excluded_by_decision: dict[str, int],
) -> str:
    negative_note = ""
    if days_to_first_seen < 0:
        negative_note = (
            f"BUG: days_from_publication_to_first_seen is {days_to_first_seen}, i.e. the "
            f"first counted observation predates the RFC. The publication-date cutoff let "
            f"through a match it should have rejected; do not use this row until the "
            f"matcher's timestamp check is fixed. "
        )
    return (
        f"{observation_count} observation(s) counted for {rfc_id} "
        f"(decisions counted: {', '.join(decisions)}), spanning {iso(first_seen)} to "
        f"{iso(last_seen)} across {distinct_domains} distinct domain(s) and "
        f"{distinct_zones} distinct zone(s). First counted observation is "
        f"{days_to_first_seen} day(s) after the {iso(publication_date)} publication date. "
        f"{negative_note}"
        f"{_excluded_summary(excluded_by_decision)}"
        "Read this as when the corpus first recorded qualifying evidence, not as when the "
        "mechanism was first deployed: observations rejected by the publication-date cutoff "
        "and partial matches are excluded, months with no qualifying observation are omitted "
        "rather than zero-filled, and a gap in OpenINTEL coverage is indistinguishable here "
        "from non-adoption."
    )


def _unseen_notes(
    *,
    rfc_id: str,
    decisions: Sequence[str],
    publication_date: datetime,
    excluded_by_decision: dict[str, int],
) -> str:
    return (
        f"No observation qualified for {rfc_id} (decisions counted: "
        f"{', '.join(decisions)}), so first_seen is null and every count is zero. "
        f"{_excluded_summary(excluded_by_decision)}"
        f"The RFC was published {iso(publication_date)}. A null first_seen is not evidence "
        "of non-adoption: the RFC's indicators may be non-queryable against this corpus, the "
        "relevant records may lie outside the measured names, or every candidate observation "
        "may have been rejected by the publication-date cutoff. Check the review queue before "
        "reporting this RFC as unadopted."
    )


# --------------------------------------------------------------------------- #
# Timeline construction
# --------------------------------------------------------------------------- #


def build_timeline(
    matches: Sequence[RFCMatch],
    db: RFCChecklistDB,
    *,
    include_decisions: tuple[str, ...] = DEFAULT_ADOPTION_DECISIONS,
) -> list[AdoptionTimelineEntry]:
    """Build one :class:`AdoptionTimelineEntry` per RFC in the checklist database.

    Every RFC in ``db`` gets an entry, including RFCs that were never observed
    (their ``first_seen`` is ``None`` and they sort last). Any ``rfc_id``
    present in ``matches`` but absent from ``db`` also gets an entry, built from
    the match's own metadata, and is logged as an inconsistency.

    Only matches whose ``decision`` is in ``include_decisions`` *and* whose
    ``timestamp_valid`` is true contribute to the counts. See
    :func:`_qualifying_matches` for why the second condition is enforced
    independently of the first.

    Entries are sorted by ``(first_seen, rfc_id)`` with never-seen RFCs last.
    """
    decisions = _validate_decisions(include_decisions)
    qualifying = _qualifying_matches(matches, decisions)

    by_rfc: dict[str, list[RFCMatch]] = defaultdict(list)
    for match in qualifying:
        by_rfc[match.rfc_id].append(match)

    # Everything seen for an RFC that did *not* qualify, so the notes can say so.
    excluded: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    allowed = set(decisions)
    for match in matches:
        if match.decision in allowed and match.timestamp_valid:
            continue
        # no_match traces explain why nothing matched; they are noise in a timeline note.
        if match.decision == "no_match":
            continue
        label = match.decision if match.timestamp_valid else "timestamp_invalid"
        excluded[match.rfc_id][label] += 1

    # Metadata source of record: the checklist DB, falling back to the match rows.
    metadata: dict[str, tuple[str, datetime]] = {
        entry.rfc_id: (entry.title, entry.publication_date) for entry in db.rfcs
    }
    for match in matches:
        if match.rfc_id not in metadata:
            LOGGER.warning(
                "RFC %s appears in matches but not in the checklist database; timeline "
                "metadata for it is taken from the match rows.",
                match.rfc_id,
            )
            metadata[match.rfc_id] = (match.rfc_title, match.rfc_publication_date)

    entries: list[AdoptionTimelineEntry] = []
    for rfc_id in sorted(metadata):
        title, publication_date = metadata[rfc_id]
        rfc_matches = by_rfc.get(rfc_id, [])
        excluded_counts = dict(excluded.get(rfc_id, {}))

        if not rfc_matches:
            entries.append(
                AdoptionTimelineEntry(
                    rfc_id=rfc_id,
                    rfc_title=title,
                    rfc_publication_date=publication_date,
                    notes=_unseen_notes(
                        rfc_id=rfc_id,
                        decisions=decisions,
                        publication_date=publication_date,
                        excluded_by_decision=excluded_counts,
                    ),
                )
            )
            continue

        timestamps = [m.observation_timestamp for m in rfc_matches]
        first_seen = min(timestamps)
        last_seen = max(timestamps)
        days_to_first_seen = (first_seen - publication_date).days
        if days_to_first_seen < 0:
            # Emitted rather than clamped: a negative value is a real defect and
            # hiding it would make a corrupted headline result look clean.
            LOGGER.error(
                "RFC %s: first counted observation %s predates publication %s by %d day(s). "
                "The timestamp cutoff failed upstream.",
                rfc_id,
                iso(first_seen),
                iso(publication_date),
                -days_to_first_seen,
            )

        domains = unique_sorted(m.domain for m in rfc_matches)
        zones = unique_sorted(m.zone for m in rfc_matches)
        months = _bucket(rfc_matches, month_key)

        entries.append(
            AdoptionTimelineEntry(
                rfc_id=rfc_id,
                rfc_title=title,
                rfc_publication_date=publication_date,
                first_seen=first_seen,
                last_seen=last_seen,
                days_from_publication_to_first_seen=days_to_first_seen,
                observation_count=len(rfc_matches),
                distinct_domains=len(domains),
                distinct_zones=len(zones),
                domains=domains,
                zones=zones,
                monthly_counts=months,
                yearly_counts=_bucket(rfc_matches, year_key),
                # Same monthly grouping, exposed under the name the dashboard
                # plots: per-month mean match score is the confidence trend.
                confidence_over_time=[b.model_copy(deep=True) for b in months],
                notes=_seen_notes(
                    rfc_id=rfc_id,
                    decisions=decisions,
                    observation_count=len(rfc_matches),
                    first_seen=first_seen,
                    last_seen=last_seen,
                    publication_date=publication_date,
                    days_to_first_seen=days_to_first_seen,
                    distinct_domains=len(domains),
                    distinct_zones=len(zones),
                    excluded_by_decision=excluded_counts,
                ),
            )
        )

    entries.sort(
        key=lambda e: (
            0 if e.first_seen is not None else 1,
            e.first_seen or _NEVER_SEEN_SORT_KEY,
            e.rfc_id,
        )
    )
    return entries


# --------------------------------------------------------------------------- #
# Flat rendering
# --------------------------------------------------------------------------- #


def _render_buckets(buckets: Sequence[TimelineBucket]) -> str:
    return "; ".join(f"{b.period}={b.count}" for b in buckets)


def _render_confidence(buckets: Sequence[TimelineBucket]) -> str:
    return "; ".join(f"{b.period}={b.mean_score}" for b in buckets)


def timeline_to_rows(entries: Sequence[AdoptionTimelineEntry]) -> list[dict[str, Any]]:
    """Flatten timeline entries into one CSV-ready row each.

    Bucket lists collapse to ``period=value`` pairs joined by ``"; "`` so that a
    spreadsheet reader keeps the full series in one cell without needing JSON.
    """
    rows: list[dict[str, Any]] = []
    for entry in entries:
        rows.append(
            {
                "rfc_id": entry.rfc_id,
                "rfc_title": entry.rfc_title,
                "rfc_publication_date": iso(entry.rfc_publication_date),
                "first_seen": iso(entry.first_seen),
                "last_seen": iso(entry.last_seen),
                "days_from_publication_to_first_seen": (
                    "" if entry.days_from_publication_to_first_seen is None
                    else entry.days_from_publication_to_first_seen
                ),
                "observation_count": entry.observation_count,
                "distinct_domains": entry.distinct_domains,
                "distinct_zones": entry.distinct_zones,
                "domains": "; ".join(entry.domains),
                "zones": "; ".join(entry.zones),
                "monthly_counts": _render_buckets(entry.monthly_counts),
                "yearly_counts": _render_buckets(entry.yearly_counts),
                "confidence_over_time": _render_confidence(entry.confidence_over_time),
                "notes": entry.notes,
            }
        )
    return rows
