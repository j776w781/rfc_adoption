"""Bottom-up and top-down analysis over the tidy timeline.

Both directions read the same timeline and the same config file, so they cannot
drift apart: the bottom-up rows are the evidence the top-down categories are
rolled up from, which is what makes "meeting in the middle" a check rather than a
rhetorical device. If a category's story is not visible in its members' rows, the
comparison says so.

Nothing here decides what to measure. :func:`bottom_up` walks
``config['bottom_up']['changes']`` and :func:`top_down` walks
``config['top_down']['categories']``; both are data, and either can be switched
off without touching the other.
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from .utils import PipelineError, get_logger

__all__ = [
    "MATERIAL_PCT",
    "POOLED_SOURCE",
    "STAGE_NAMES",
    "cross_reference",
    "detect_breaks",
    "bottom_up",
    "compare_directions",
    "load_config",
    "prevalence_series",
    "top_down",
]

LOGGER = get_logger(__name__)

#: Source name for rows extracted across every source of a day at once. Their
#: distinct-domain counts are exact where per-source counts cannot be summed.
POOLED_SOURCE = "_pooled"

#: A pair of shares only counts as agreement when at least one side is materially
#: present, the absolute gap is small, AND the two are within a factor of each
#: other. Two values of 0.00% are not corroboration, and 0.01% against 2.10% is
#: 2.1 points apart while being 300x apart.
MATERIAL_PCT = 0.5
POINT_TOLERANCE = 5.0
RATIO_TOLERANCE = 3.0


def load_config(path: Path | str) -> dict[str, Any]:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    for section in ("stages", "bottom_up", "top_down"):
        if section not in config:
            raise PipelineError(f"analysis config is missing '{section}': {path}")
    return config


def _months_between(a: str, b: str) -> int:
    return (int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))


def _years(a: str | None, b: str | None) -> float | None:
    return round(_months_between(a, b) / 12, 2) if (a and b) else None


def prevalence_series(
    timeline: pd.DataFrame,
    dimension: str,
    value: str,
    *,
    sources: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Monthly numerator, denominator and share for one observable value.

    ``value`` may name several codepoints separated by ``|`` (RFC 9905 covers
    algorithms 5 and 7 as one deprecation), in which case the numerator is their
    union across the month.
    """
    frame = timeline[timeline.dimension == dimension]
    if sources is not None:
        frame = frame[frame.source.isin(list(sources))]
    elif any(str(x).startswith(POOLED_SOURCE) for x in frame.source.unique()):
        # `_pooled` rows were extracted with every source's files in one query, so
        # their distinct-domain counts are exact across sources. Where they exist
        # they are the only correct basis for a pooled share: summing per-source
        # counts double-counts any name two sources share, and reverse-DNS zonelets
        # share 1,911 of 6,581 names between RIRs. Mixing the two would count
        # everything twice over.
        pooled_names = sorted(x for x in frame.source.unique()
                              if str(x).startswith(POOLED_SOURCE))
        frame = frame[frame.source == pooled_names[0]]
    else:
        frame = frame[~frame.source.astype(str).str.startswith(POOLED_SOURCE)]
    if frame.empty:
        return pd.DataFrame()

    wanted = set(value.split("|"))
    selected = frame[frame.value.isin(wanted)]
    # Records are disjoint per value, so they add. **Domains are not.** A zone
    # publishing both algorithm 5 and algorithm 7 appears under each, and summing
    # counted it twice -- RFC 9905 read 120% of its own population. The union of
    # distinct names is not recoverable from per-value counts, so this takes the
    # largest single value as a lower bound on it, matching how `domains_peak`
    # already errs: it can understate reach, never inflate it.
    per_value_domains = (
        selected.groupby(["month", "value"], as_index=False)
        .agg(d=("domains_peak", "sum"), dd=("domain_days", "sum"))
    )
    domains = (
        per_value_domains.groupby("month", as_index=False)
        .agg(domains_peak=("d", "max"), domain_days=("dd", "max"))
    )
    numerator = (
        selected.groupby("month", as_index=False)
        .agg(records=("records", "sum"))
        .merge(domains, on="month", how="left")
    )
    denominator = (
        frame[frame.value == "_total"]
        .groupby("month", as_index=False)
        .agg(total_records=("records", "sum"),
             total_domains=("domains_peak", "sum"))
    )
    # Only a missing DENOMINATOR means the corpus cannot answer this question. An
    # empty numerator against a real denominator is a genuine null -- we looked at
    # rows that could have carried the value and none did. Collapsing the two was
    # how RFC 9905 reported "no data" while 15,966 non-conforming records sat in
    # the corpus, so they stay distinct here: this returns an all-zero series
    # rather than nothing at all.
    if denominator.empty:
        return pd.DataFrame()

    merged = denominator.merge(numerator, on="month", how="left").fillna(
        {"records": 0, "domains_peak": 0, "domain_days": 0}
    )
    merged["share_pct"] = merged.apply(
        lambda r: (r.domains_peak / r.total_domains * 100) if r.total_domains else 0.0,
        axis=1,
    )
    return merged.sort_values("month").reset_index(drop=True)


#: Plain-language names for the stages, in order. These are what appears in
#: output read by people; the `t1/t2/t3` keys stay for anything computing on it.
STAGE_NAMES = ("not seen", "seen only", "in use", "widely used")


def _stage_of(share: float, zones: float, stages: dict[str, Any]) -> str:
    """Which stage a single month sits in."""
    if share <= 0:
        return "not seen"
    if zones < float(stages.get("min_zones", 0)):
        return "seen only"
    if share >= float(stages["common_usage_pct"]):
        return "widely used"
    if share >= float(stages["partial_usage_pct"]):
        return "in use"
    return "seen only"


def _describe(series: pd.DataFrame, dates: dict[str, Any],
              stages: dict[str, Any], *, residue: bool) -> dict[str, Any]:
    """Where it is now, the furthest it ever got, and which way it is moving.

    Splitting these is the whole point. A single label that means "furthest ever
    reached" but reads as present tense put RSA/SHA-512 (0.37% today, peaked at
    3.7%) and Ed25519 (0.34% today, never above 0.37%) in visibly different
    categories on nearly identical numbers, with no way for a reader to see why.
    """
    if dates["t1_first_seen"] is None:
        return {"state": "scanned_no_match", "now": "not seen",
                "peak_reached": "not seen", "trend": "absent",
                "summary": "Looked for and not found in this corpus."}

    now_share = float(series.share_pct.iloc[-1])
    now_zones = float(series.domains_peak.iloc[-1])
    peak_share = float(series.share_pct.max())
    peak_month = str(series.loc[series.share_pct.idxmax(), "month"])

    now = _stage_of(now_share, now_zones, stages)
    # The furthest it ever got is the best stage any single month achieved, which
    # is exactly what the old single label reported.
    peak_reached = max(
        (_stage_of(r.share_pct, r.domains_peak, stages) for r in series.itertuples()),
        key=STAGE_NAMES.index,
    )

    # Direction, from where it sits relative to its own peak. A mechanism at its
    # peak is still climbing or holding; one well below it has been displaced.
    #
    # The absolute test comes first because a ratio is hysterical about small
    # numbers: Ed25519 fell 0.37% -> 0.34%, a ratio of 0.92 that would read as
    # "easing" when the line is visibly flat. Three tenths of a percentage point
    # is not a movement worth naming.
    drop = peak_share - now_share
    if peak_share <= 0:
        trend = "absent"
    elif drop < 0.5:
        trend = "rising" if now_share >= peak_share * 0.99 else "steady"
    elif now_share >= peak_share * 0.7:
        trend = "easing"
    else:
        trend = "declining"

    if residue:
        summary = (f"Deprecated, still published on {now_share:.2f}% of signed "
                   f"delegations and {trend}.")
    elif now == peak_reached:
        summary = (f"{now.capitalize()} and {trend} — {now_share:.2f}% today"
                   + (f", its highest." if trend in ("rising", "steady")
                      else f", down from {peak_share:.2f}% in {peak_month}."))
    else:
        summary = (f"Was {peak_reached} ({peak_share:.2f}% in {peak_month}), "
                   f"now {now} at {now_share:.2f}% and {trend}.")

    return {
        # Kept so nothing downstream breaks, but it is the PEAK, not the present.
        "state": {"widely used": "common", "in use": "partial",
                  "seen only": "seen_only", "not seen": "scanned_no_match"}[
                      "seen only" if residue else peak_reached],
        "now": now,
        "peak_reached": peak_reached,
        "trend": trend,
        "summary": summary,
    }


def _stage_dates(series: pd.DataFrame, stages: dict[str, Any]) -> dict[str, Any]:
    """First occurrence, partial usage and common usage for one series."""
    if series.empty:
        return {"t1_first_seen": None, "t2_partial_usage": None, "t3_common_usage": None,
                "zones_at_first_seen": None}

    present = series[series.records > 0]
    if present.empty:
        return {"t1_first_seen": None, "t2_partial_usage": None, "t3_common_usage": None,
                "zones_at_first_seen": None}
    first = str(present.month.iloc[0])
    first_zones = int(present.domains_peak.iloc[0])

    min_zones = float(stages.get("min_zones", 0))

    def cross(pct: float) -> str | None:
        hit = series[(series.share_pct >= pct) & (series.domains_peak >= min_zones)]
        return str(hit.month.iloc[0]) if len(hit) else None

    return {
        "t1_first_seen": first,
        "zones_at_first_seen": first_zones,
        "t2_partial_usage": cross(float(stages["partial_usage_pct"])),
        "t3_common_usage": cross(float(stages["common_usage_pct"])),
    }


def bottom_up(
    timeline: pd.DataFrame,
    config: dict[str, Any],
    *,
    sources: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """One row per observable change: what it is, when it appeared, how far it got."""
    stages = config["stages"]
    rows: list[dict[str, Any]] = []

    for change in config["bottom_up"]["changes"]:
        series = prevalence_series(
            timeline, change["dimension"], change["value"], sources=sources
        )
        record = {
            "key": change["key"],
            "label": change["label"],
            "rfc": change["rfc"],
            "published": change["published"],
            "group": change["group"],
            "observable": change["observable"],
            "dimension": change["dimension"],
            "value": change["value"],
            "is_residue": bool(change.get("residue")),
            "measurable_here": not series.empty,
        }
        if series.empty:
            # No denominator for this dimension means the corpus cannot carry the
            # record type at all. That is not a negative observation and must not
            # be reported as one.
            record.update({
                "t1_first_seen": None, "t2_partial_usage": None,
                "t3_common_usage": None, "zones_at_first_seen": None,
                "onset_years": None, "establishment_years": None,
                "ascent_years": None, "current_share_pct": None,
                "peak_share_pct": None, "state": "no_corpus_coverage",
            })
            rows.append(record)
            continue

        dates = _stage_dates(series, stages)
        record.update(dates)

        # A first sighting in the corpus's opening month is an upper bound, not a
        # measurement: the value may well have been published before we could see
        # it. Reporting that onset as if it were measured is the left-censoring
        # error, and it is invisible unless the flag travels with the number.
        corpus_start = str(series.month.iloc[0])
        record["corpus_starts"] = corpus_start
        record["left_censored"] = bool(
            dates["t1_first_seen"] and dates["t1_first_seen"] == corpus_start
        )
        # A deprecation has no onset. Its observable is a mechanism that existed
        # long before the document retiring it, so publication-to-first-sighting is
        # negative and meaningless -- RFC 9905 (2025-11) against algorithm 5 first
        # seen in 2009 reads as -13.7 years. What matters for these is the residue,
        # computed below.
        onset = (None if change.get("residue")
                 else _years(change["published"], dates["t1_first_seen"]))
        # A negative onset is not a fast adoption, it is the wrong question. The
        # value was already in the data before the document existed, so there is
        # no "time until someone did it" to measure. Two ways this happens:
        # RFC 9276 recommends NSEC3 iterations = 0, which was always legal and
        # already common (first seen 2016-06 against a 2022-08 RFC, reading
        # -6.2y); and an implementation shipping from a draft, as the GOST-2012
        # digest did five months before RFC 9558 published.
        record["onset_years"] = None if (onset is not None and onset < 0) else onset
        record["predates_rfc"] = bool(onset is not None and onset < 0)
        if record["predates_rfc"]:
            record["predates_rfc_by_years"] = abs(onset)
        record["establishment_years"] = _years(
            dates["t1_first_seen"], dates["t2_partial_usage"])
        record["ascent_years"] = _years(
            dates["t2_partial_usage"], dates["t3_common_usage"])
        record["total_to_common_years"] = _years(
            change["published"], dates["t3_common_usage"])
        record["current_share_pct"] = round(float(series.share_pct.iloc[-1]), 4)
        record["peak_share_pct"] = round(float(series.share_pct.max()), 4)
        record["peak_month"] = str(series.loc[series.share_pct.idxmax(), "month"])
        record["last_month"] = str(series.month.iloc[-1])
        record["months_observed"] = int((series.records > 0).sum())

        # One `state` was doing two jobs and reading as though it did one. It
        # named the HIGHEST stage ever reached, but present tense: RSA/SHA-512
        # showed "partial" while sitting at 0.37%, having peaked at 3.7% seven
        # years earlier. Meanwhile Ed25519 showed "seen only" at 0.34% -- a
        # nearly identical number with a completely different history. Both
        # labels were defensible, which is the same ambiguity that made the word
        # "adoption" unusable in the first place.
        #
        # So the two questions are now answered separately: where is it NOW, and
        # what is the furthest it ever got. `trend` says which way it is moving,
        # and `summary` states all three in a sentence a reader does not have to
        # decode.
        record.update(_describe(series, dates, stages,
                                residue=bool(change.get("residue"))))

        # For a deprecation the interesting quantity is what remains after the
        # document, not when it first appeared -- which is usually decades before.
        if change.get("residue"):
            record["state"] = "residue"
            after = series[series.month >= change["published"]]
            record["residue_share_pct"] = (
                round(float(after.share_pct.iloc[-1]), 4) if len(after) else None
            )
            record["residue_records_after_publication"] = (
                int(after.records.sum()) if len(after) else 0
            )
        rows.append(record)
    return rows


def _group_stats(rows: Sequence[dict[str, Any]], key: str) -> dict[str, Any] | None:
    values = [r[key] for r in rows if r.get(key) is not None]
    if not values:
        return None
    return {
        "n": len(values),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "median": round(statistics.median(values), 2),
        "spread": round(max(values) - min(values), 2),
    }


def top_down(
    timeline: pd.DataFrame,
    config: dict[str, Any],
    bottom_up_rows: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Roll the bottom-up evidence up into the conceptual categories.

    A category's numbers are exactly its members' numbers -- nothing is measured
    independently at this level. That is deliberate: a top-down claim that cannot
    be traced to specific observable changes is an opinion, and this makes the
    absence of evidence visible instead of letting the category average paper
    over it.
    """
    by_rfc: dict[str, list[dict[str, Any]]] = {}
    for row in bottom_up_rows:
        by_rfc.setdefault(row["rfc"], []).append(row)

    out: list[dict[str, Any]] = []
    for category in config["top_down"]["categories"]:
        members = [r for rfc in category["rfcs"] for r in by_rfc.get(rfc, [])]
        measured = [r for r in members if r.get("t1_first_seen")]
        covered_rfcs = sorted({r["rfc"] for r in members})
        out.append({
            "key": category["key"],
            "label": category["label"],
            "description": category["description"],
            # Carried through so the example travels with the numbers. A category
            # that cannot be given a concrete example is not describing something
            # observable, and that should be visible in the output, not only in
            # the config.
            "example": category.get("example", ""),
            "rfcs": category["rfcs"],
            "rfcs_with_observables": covered_rfcs,
            "rfcs_without_observables": sorted(
                set(category["rfcs"]) - set(covered_rfcs)),
            "observable_changes": len(members),
            "observed_changes": len(measured),
            "onset_years": _group_stats(measured, "onset_years"),
            "establishment_years": _group_stats(measured, "establishment_years"),
            "ascent_years": _group_stats(measured, "ascent_years"),
            "reached_partial": sum(1 for r in measured if r.get("t2_partial_usage")),
            "reached_common": sum(1 for r in measured if r.get("t3_common_usage")),
            "max_current_share_pct": max(
                (r["current_share_pct"] for r in measured
                 if r.get("current_share_pct") is not None), default=None),
            "members": [
                {"key": r["key"], "label": r["label"], "rfc": r["rfc"],
                 "group": r["group"], "state": r["state"],
                 "onset_years": r.get("onset_years"),
                 "current_share_pct": r.get("current_share_pct")}
                for r in members
            ],
        })
    return out


def compare_directions(
    bottom_up_rows: Sequence[dict[str, Any]],
    top_down_rows: Sequence[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Where the two directions agree, and where the taxonomy has no evidence.

    Two failure modes are worth naming explicitly. A category with no observable
    changes is a taxonomy that outruns the data. A bottom-up group that scatters
    across many categories means the implementation-cost grouping and the
    conceptual grouping are cutting the same material differently -- which is
    interesting, not wrong, but it should be stated rather than hidden.
    """
    groups = config["bottom_up"]["groups"]
    by_group: dict[str, list[dict[str, Any]]] = {}
    for row in bottom_up_rows:
        by_group.setdefault(row["group"], []).append(row)

    group_summary = []
    for key, meta in groups.items():
        members = by_group.get(key, [])
        measured = [r for r in members if r.get("t1_first_seen")]
        group_summary.append({
            "key": key,
            "label": meta["label"],
            "what_must_change": meta["what_must_change"],
            "evidence": meta.get("evidence", ""),
            "changes": len(members),
            "observed": len(measured),
            "onset_years": _group_stats(measured, "onset_years"),
        })

    # Which conceptual categories does each implementation group land in?
    category_of_rfc: dict[str, list[str]] = {}
    for category in top_down_rows:
        for rfc in category["rfcs"]:
            category_of_rfc.setdefault(rfc, []).append(category["key"])

    crosswalk = []
    for key, members in by_group.items():
        categories: dict[str, int] = {}
        for row in members:
            for cat in category_of_rfc.get(row["rfc"], ["(uncategorised)"]):
                categories[cat] = categories.get(cat, 0) + 1
        crosswalk.append({
            "group": key,
            "categories": dict(sorted(categories.items(), key=lambda kv: -kv[1])),
            "spans_categories": len(categories),
        })

    empty = [c["key"] for c in top_down_rows if c["observable_changes"] == 0]
    unmeasured = [c["key"] for c in top_down_rows
                  if c["observable_changes"] and c["observed_changes"] == 0]

    return {
        "implementation_groups": sorted(group_summary, key=lambda g: g["key"]),
        "group_to_category": sorted(crosswalk, key=lambda c: c["group"]),
        "categories_without_observables": empty,
        "categories_with_observables_but_no_observations": unmeasured,
        "note": (
            "Onset bands come from the implementation groups, not the conceptual "
            "categories: a category mixes changes of very different implementation "
            "cost, so its onset spread is wide and says little. The groups are the "
            "predictive cut; the categories are the communicable one."
        ),
    }


def cross_reference(
    timeline: pd.DataFrame,
    config: dict[str, Any],
    *,
    forward_sources: Sequence[str] | None = None,
    reverse_sources: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Compare the same observable across the forward and reverse corpora.

    The two corpora share no infrastructure, no operator population and no
    collection method, so agreement between them is real evidence and disagreement
    usually says something about the measurement rather than about operators.
    Telling those apart is the whole job.

    **Only algorithm- and digest-scoped dimensions are comparable.** The reverse
    corpus holds NS and DS records only; the forward corpus is mostly RRSIG and
    DNSKEY. Any share taken over "all DNSSEC records" therefore differs between
    them by record-type composition alone -- which is exactly how a 10x gap in
    RFC 4509 turned out to be roughly 9x denominator. Dimensions the config marks
    incomparable are reported as such instead of being quietly differenced.
    """
    spec = config.get("cross_reference", {})
    comparable = list(spec.get("comparable_dimensions", []))
    incomparable = list(spec.get("incomparable_dimensions", []))

    # Which side a source belongs to comes from its `basis`, which the walker
    # already recorded from the corpus layout. Guessing from source names would
    # break the moment a forward source were named after an RIR, and would give a
    # wrong answer silently rather than an obvious one.
    sources = {x for x in timeline.source.unique()
               if not str(x).startswith(POOLED_SOURCE)}
    if "basis" in timeline.columns:
        by_basis = timeline.groupby("source").basis.first()
        reverse = set(reverse_sources or []) or {
            s for s in sources if str(by_basis.get(s, "")).lower() == "reverse"
        }
    else:  # pragma: no cover - older timelines without the column
        reverse = set(reverse_sources or [])
    forward = set(forward_sources or []) or (sources - reverse)

    result: dict[str, Any] = {
        "forward_sources": sorted(forward),
        "reverse_sources": sorted(reverse),
        "comparable_dimensions": comparable,
        "incomparable_dimensions": incomparable,
        "incomparable_reason": spec.get("incomparable_reason", ""),
        "comparisons": [],
        "notes": [],
    }
    if not forward or not reverse:
        result["notes"].append(
            "Only one side is present in this run "
            f"(forward={sorted(forward)}, reverse={sorted(reverse)}), so nothing is "
            "cross-referenced. This is not a disagreement; it is a missing corpus."
        )
        return result

    # Compare at the last month BOTH sides actually have, not the last month in
    # the timeline. The corpora do not end together -- forward stops when the
    # mirror stops, reverse keeps going -- so taking the global maximum asks the
    # forward corpus about a date it has no data for, gets None, and then reports
    # that absence as a failure to agree.
    fwd_months = set(timeline[timeline.source.isin(sorted(forward))].month.unique())
    rev_months = set(timeline[timeline.source.isin(sorted(reverse))].month.unique())
    shared = sorted(fwd_months & rev_months)
    if not shared:
        result["notes"].append(
            "The two corpora share no measured month, so nothing can be compared "
            f"at a common date: forward runs to {max(fwd_months, default='—')}, "
            f"reverse to {max(rev_months, default='—')}."
        )
        return result
    last = shared[-1]
    result["comparison_month"] = last
    result["forward_last_month"] = max(fwd_months)
    result["reverse_last_month"] = max(rev_months)
    if result["forward_last_month"] != result["reverse_last_month"]:
        result["notes"].append(
            f"Compared at {last}, the last month both corpora cover. Forward data "
            f"ends {result['forward_last_month']}, reverse continues to "
            f"{result['reverse_last_month']}, so a figure quoted from one side's "
            "own latest month is not comparable with the other's."
        )
    for change in config["bottom_up"]["changes"]:
        if change["dimension"] not in comparable:
            continue
        fwd = prevalence_series(timeline, change["dimension"], change["value"],
                                sources=sorted(forward))
        rev = prevalence_series(timeline, change["dimension"], change["value"],
                                sources=sorted(reverse))
        if fwd.empty or rev.empty:
            continue

        def at(series: pd.DataFrame, month: str) -> float | None:
            row = series[series.month == month]
            return round(float(row.share_pct.iloc[0]), 3) if len(row) else None

        # Existence is a minimum over all evidence, so the earlier of the two
        # first sightings is the one that counts -- see the Ed25519 correction.
        def first(series: pd.DataFrame) -> str | None:
            hit = series[series.records > 0]
            return str(hit.month.iloc[0]) if len(hit) else None

        f_first, r_first = first(fwd), first(rev)
        both = [m for m in (f_first, r_first) if m]
        f_now, r_now = at(fwd, last), at(rev, last)
        result["comparisons"].append({
            "key": change["key"],
            "label": change["label"],
            "rfc": change["rfc"],
            "published": change["published"],
            "dimension": change["dimension"],
            "forward_first_seen": f_first,
            "reverse_first_seen": r_first,
            "earliest_first_seen": min(both) if both else None,
            "earlier_corpus": (
                None if not both else
                ("forward" if f_first == min(both) and f_first != r_first
                 else "reverse" if r_first == min(both) and f_first != r_first
                 else "both")
            ),
            "onset_years_cross_corpus": (
                _years(change["published"], min(both)) if both else None),
            "forward_share_pct": f_now,
            "reverse_share_pct": r_now,
            "difference_pct_points": (
                round(f_now - r_now, 3) if (f_now is not None and r_now is not None)
                else None),
            "month": str(last),
        })

    # Only rows where BOTH sides produced a number can agree or disagree. Counting
    # a missing value as a disagreement previously turned "the forward corpus has
    # no data for this month" into "0 of 20 observables agree", which reads as the
    # two corpora contradicting each other.
    comparable = [c for c in result["comparisons"]
                  if c["difference_pct_points"] is not None]

    # An absolute threshold alone is not agreement. Most of these values sit near
    # zero, where "both absent" passes a 5-point test and reads as corroboration:
    # RSASHA1 at 0.01% against 2.10% is 2.1 points apart and 300x apart, and
    # nine pairs were 0.00% on both sides. So a pair only counts as agreeing when
    # at least one side is materially present AND the two are within a factor of
    # each other as well as within the point threshold.
    for c in comparable:
        f, r = c["forward_share_pct"], c["reverse_share_pct"]
        hi, lo = max(f, r), min(f, r)
        c["ratio"] = (hi / lo) if lo > 0 else None
        if hi < MATERIAL_PCT:
            c["verdict"] = "absent from both"
        elif abs(c["difference_pct_points"]) > POINT_TOLERANCE:
            c["verdict"] = "disagree"
        elif c["ratio"] is None or c["ratio"] >= RATIO_TOLERANCE:
            c["verdict"] = "present on one side only"
        else:
            c["verdict"] = "agree"

    counts: dict[str, int] = {}
    for c in comparable:
        counts[c["verdict"]] = counts.get(c["verdict"], 0) + 1
    result["verdict_counts"] = counts
    agreeing = [c for c in comparable if c["verdict"] == "agree"]
    if comparable:
        result["notes"].append(
            f"Of {len(comparable)} observables both corpora can answer at {last}: "
            f"{counts.get('agree', 0)} agree, "
            f"{counts.get('disagree', 0)} disagree by more than "
            f"{POINT_TOLERANCE:g} points, "
            f"{counts.get('present on one side only', 0)} are present on one side "
            f"only, and {counts.get('absent from both', 0)} are below "
            f"{MATERIAL_PCT:g}% on both sides — absent, not corroborating."
        )
        for c in agreeing:
            result["notes"].append(
                f"Agreement: {c['label']} reads {c['forward_share_pct']:.2f}% "
                f"forward and {c['reverse_share_pct']:.2f}% reverse, "
                f"{abs(c['difference_pct_points']):.2f} points apart, across "
                "corpora sharing no infrastructure, operators or method."
            )
    skipped = len(result["comparisons"]) - len(comparable)
    if skipped:
        result["notes"].append(
            f"{skipped} further observable(s) could not be compared because one "
            "side has no value for them — absent from a corpus, not disagreeing."
        )
    earlier_forward = [c for c in result["comparisons"]
                       if c["earlier_corpus"] == "forward"]
    if earlier_forward:
        result["notes"].append(
            f"{len(earlier_forward)} observable(s) appear EARLIER in the forward "
            "corpus than the reverse one: "
            + ", ".join(c["label"] for c in earlier_forward)
            + ". A reverse-only onset overstates these."
        )
    return result


def detect_breaks(timeline: pd.DataFrame, *, step_pct: float = 25.0) -> list[str]:
    """Find places where the POPULATION changed, not the behaviour.

    Two kinds, both of which make a pooled share mean different things before and
    after, and neither of which looks like an error in the output:

    * A source stops reporting mid-series. In the full run every forward source
      ends 2023-12 while the RIRs continue to 2026-08, so a pooled figure for
      2026 is reverse-only however it is labelled, and the series crosses a cliff
      at 2024-01 that has nothing to do with operators.
    * A dimension's denominator steps sharply from one month to the next, which
      is what a source joining or leaving looks like from inside the numbers.
    """
    notes: list[str] = []
    if timeline.empty:
        return notes

    real = timeline[~timeline.source.astype(str).str.startswith(POOLED_SOURCE)]
    if real.empty:
        return notes
    last_overall = real.month.max()

    ends = real.groupby("source").month.max()
    stopped = sorted(s for s, m in ends.items() if m < last_overall)
    if stopped:
        detail = ", ".join(f"{s} ends {ends[s]}" for s in stopped)
        notes.append(
            f"{len(stopped)} of {real.source.nunique()} sources stop before the "
            f"end of the series ({detail}; the rest run to {last_overall}). Any "
            "pooled share after the earliest of those dates is computed on the "
            "survivors only. Report the two groups separately, or cut the series "
            "at the last month they all cover."
        )

    for dim, grp in real[real.value == "_total"].groupby("dimension"):
        s = (grp.groupby("month").domains_peak.sum().sort_index())
        if len(s) < 3:
            continue
        step = s.pct_change() * 100
        big = step[step.abs() >= step_pct]
        for month, pct in big.items():
            notes.append(
                f"'{dim}' denominator steps {pct:+.0f}% at {month} "
                f"({int(s.shift(1)[month]):,} -> {int(s[month]):,} names). A share "
                "spanning that month compares two different populations."
            )
    return notes
