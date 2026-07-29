"""Matching Results: the ranked RFC candidates and the matches behind them.

A ranking is only useful if the reader can see why it came out that way, so this
page pairs the ranked table with the aggregate ``reasoning_summary`` each
candidate carries and a side-by-side comparison that shows the arithmetic
separating two RFCs — for the sample corpus, why RFC 8078 outranks RFC 7344 on
the same CDS observations.

Ranked candidates are aggregates over signals; the per-signal matches that feed
them are shown underneath, with the same filters applied.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_DASHBOARD_DIR = str(Path(__file__).resolve().parents[1])
if _DASHBOARD_DIR not in sys.path:
    sys.path.insert(0, _DASHBOARD_DIR)

from _bootstrap import setup  # noqa: E402

setup()

import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from _shared import (  # noqa: E402
    CONFIDENCE_ORDER,
    DECISION_COLORS,
    DECISION_ORDER,
    DashboardBundle,
    date_range_slice,
    decision_badge,
    empty_state,
    filter_dataframe,
    load_bundle,
    multiselect_filter,
    no_rows,
    ordered_categories,
    page_setup,
    show_df,
    show_fig,
    sidebar_controls,
    sidebar_status,
)

#: Terms of the score, in the order the formula applies them.
_BREAKDOWN_TERMS: tuple[str, ...] = (
    "base_indicator_score",
    "required_match_bonus",
    "optional_match_bonus",
    "missing_required_penalty",
    "partial_match_penalty",
    "ambiguity_penalty",
    "specificity_multiplier",
    "timestamp_penalty",
    "final_score",
)


def _enriched_matches(bundle: DashboardBundle) -> pd.DataFrame:
    """Per-signal matches joined to the observation's record type.

    ``rfc_matches.json`` carries the domain and zone but not ``rr_type``, and a
    reader filtering for "the CDS matches" needs it, so it is joined in from the
    signals frame rather than recomputed.
    """
    matches = bundle.matches_df
    signals = bundle.signals_df
    if matches.empty or signals.empty or "signal_id" not in signals.columns:
        return matches
    lookup = signals[["signal_id", "rr_type"]].drop_duplicates("signal_id")
    return matches.merge(lookup, on="signal_id", how="left")


def _ranked_chart(ranked: pd.DataFrame) -> None:
    top = ranked.sort_values("score", ascending=True, na_position="first")
    figure = px.bar(
        top,
        x="score",
        y="rfc_id",
        orientation="h",
        color="decision",
        color_discrete_map=DECISION_COLORS,
        category_orders={"decision": ordered_categories(top["decision"], DECISION_ORDER)},
        hover_data=["confidence", "specificity", "supporting_signal_count"],
        title="Ranked candidates by best per-signal score",
        text="score",
    )
    figure.update_layout(xaxis_title="score", yaxis_title="")
    figure.update_traces(textposition="outside", cliponaxis=False)
    show_fig(figure, height=max(320, 46 * len(top) + 120))


def _matches_over_time(matches: pd.DataFrame) -> None:
    st.markdown("**Matches over time**")
    frame = matches[matches["decision"].astype("string") != "no_match"]
    stamps = pd.to_datetime(frame["observation_timestamp"], errors="coerce")
    frame = frame.assign(observation_timestamp=stamps).dropna(
        subset=["observation_timestamp"]
    )
    if frame.empty:
        no_rows("No dated matches in the current selection.")
        return
    frame = frame.assign(
        period=frame["observation_timestamp"].dt.to_period("Y").astype(str),
        decision=frame["decision"].astype("string").fillna("unknown"),
    )
    counts = frame.groupby(["period", "decision"]).size().reset_index(name="matches")
    figure = px.line(
        counts.sort_values("period"),
        x="period",
        y="matches",
        color="decision",
        markers=True,
        color_discrete_map=DECISION_COLORS,
        category_orders={"decision": ordered_categories(counts["decision"], DECISION_ORDER)},
        title="Matches per year by decision (no_match excluded)",
    )
    figure.update_layout(xaxis_title="", yaxis_title="matches")
    show_fig(figure, height=340)


def _first_seen_chart(ranked: pd.DataFrame) -> None:
    st.markdown("**First seen by RFC**")
    frame = ranked.dropna(subset=["first_seen"])
    if frame.empty:
        no_rows("No candidate carries a first_seen date.")
        return
    frame = frame.sort_values("first_seen").assign(
        supporting_signal_count=frame["supporting_signal_count"].fillna(0).clip(lower=0)
    )
    # A size channel with an all-zero column makes Plotly's sizeref degenerate.
    size_column = (
        "supporting_signal_count" if frame["supporting_signal_count"].max() > 0 else None
    )
    figure = px.scatter(
        frame,
        x="first_seen",
        y="rfc_id",
        color="confidence",
        size=size_column,
        hover_data=["score", "rfc_publication_date", "last_seen"],
        title="Earliest supporting observation per RFC",
    )
    figure.update_layout(xaxis_title="", yaxis_title="")
    show_fig(figure, height=max(300, 40 * len(frame) + 140))
    st.caption(
        "First seen is bounded by measurement coverage: it is the earliest "
        "*observation* consistent with the RFC, not the earliest deployment."
    )


def _breakdown_frame(trace: dict[str, Any] | None) -> pd.DataFrame:
    if not trace:
        return pd.DataFrame()
    breakdown = trace.get("score_breakdown") or {}
    return pd.DataFrame(
        [
            {"term": term, "value": breakdown.get(term)}
            for term in _BREAKDOWN_TERMS
            if term in breakdown
        ]
    )


def _example_trace(bundle: DashboardBundle, row: pd.Series) -> dict[str, Any] | None:
    ids = row.get("example_trace_ids_raw")
    if isinstance(ids, list):
        for trace_id in ids:
            trace = bundle.trace_by_id(str(trace_id))
            if trace is not None:
                return trace
    return None


def _scored_signals(bundle: DashboardBundle, rfc_id: str) -> pd.DataFrame:
    """Non-``no_match`` evaluations of one RFC, best score first."""
    matches = bundle.matches_df
    if matches.empty:
        return matches
    subset = matches[
        (matches["rfc_id"].astype(str) == rfc_id)
        & (matches["decision"].astype("string") != "no_match")
    ]
    return subset.sort_values("score", ascending=False)


def _closest_rival(bundle: DashboardBundle, options: list[str], first: str) -> int:
    """Index of the RFC that competes with ``first`` on the most observations.

    Rank 2 is not necessarily the interesting comparison: the informative rival
    is the RFC that was evaluated against the *same* signals, because that is
    where the score difference actually decides something. For the sample corpus
    this puts RFC 7344 next to RFC 8078 — both fire on the same CDS records.
    """
    rivals = [name for name in options if name != first]
    if not rivals:
        return 0
    own = set(_scored_signals(bundle, first).get("signal_id", pd.Series(dtype=str)))
    if own:
        overlaps = {
            name: len(own & set(_scored_signals(bundle, name).get("signal_id", pd.Series(dtype=str))))
            for name in rivals
        }
        best = max(overlaps, key=lambda name: overlaps[name])
        if overlaps[best] > 0:
            return options.index(best)
    return options.index(rivals[0])


def _shared_signal(bundle: DashboardBundle, first: str, second: str) -> str | None:
    """A signal both RFCs were evaluated against, favouring the first's best."""
    left = _scored_signals(bundle, first)
    right = _scored_signals(bundle, second)
    if left.empty or right.empty:
        return None
    shared = set(left["signal_id"].astype(str)) & set(right["signal_id"].astype(str))
    if not shared:
        return None
    candidates = left[left["signal_id"].astype(str).isin(shared)]
    return str(candidates.iloc[0]["signal_id"])


def _trace_for_signal(
    bundle: DashboardBundle, rfc_id: str, signal_id: str | None
) -> dict[str, Any] | None:
    if signal_id is None:
        return None
    matches = bundle.matches_df
    row = matches[
        (matches["rfc_id"].astype(str) == rfc_id)
        & (matches["signal_id"].astype(str) == signal_id)
    ]
    if row.empty:
        return None
    return bundle.trace_by_id(str(row.iloc[0]["trace_id"]))


def _close_ranking_note(bundle: DashboardBundle, first: str, second: str) -> None:
    """Surface the review queue's own verdict on this pair, if it raised one."""
    pair = {first, second}
    for item in bundle.review_items:
        if item.get("item_type") != "close_ranking":
            continue
        evidence = item.get("evidence") or {}
        if {str(evidence.get("rfc_a")), str(evidence.get("rfc_b"))} != pair:
            continue
        st.warning(
            f"The review queue flagged this pair as too close to call "
            f"({item.get('item_id')}): {item.get('reason')}"
        )
        shared = evidence.get("shared_indicators") or []
        only_a = evidence.get("indicators_only_in_a") or []
        only_b = evidence.get("indicators_only_in_b") or []
        st.caption(
            "Shared indicators: "
            + (", ".join(str(i) for i in shared) or "none")
            + f". Only {evidence.get('rfc_a')}: "
            + (", ".join(str(i) for i in only_a) or "none")
            + f". Only {evidence.get('rfc_b')}: "
            + (", ".join(str(i) for i in only_b) or "none")
            + "."
        )
        return


def _comparison(bundle: DashboardBundle, ranked: pd.DataFrame) -> None:
    """Why one RFC outranks another, term by term."""
    st.subheader("Why one RFC outranks another")
    st.caption(
        "Ranking is driven by the best single-signal score. Where both RFCs were "
        "evaluated against the same observation, that observation is used for "
        "both panels, so the arithmetic separating them is directly comparable "
        "rather than asserted."
    )
    if len(ranked) < 2:
        no_rows("At least two ranked candidates are needed for a comparison.")
        return

    ordered = ranked.sort_values("rank", na_position="last")
    options = list(ordered["rfc_id"].astype(str))
    picker = st.columns(2)
    first = picker[0].selectbox("Higher-ranked RFC", options, index=0, key="compare_a")
    second = picker[1].selectbox(
        "Compared against",
        options,
        index=_closest_rival(bundle, options, first),
        key="compare_b",
    )
    if first == second:
        no_rows("Pick two different RFCs to compare.")
        return

    shared_signal = _shared_signal(bundle, first, second)
    if shared_signal is not None:
        st.markdown(
            f"Both RFCs were evaluated against signal `{shared_signal}`. "
            "Each panel below shows what that single observation earned for that RFC."
        )
    else:
        st.markdown(
            "These two RFCs share no observation, so each panel uses that "
            "candidate's own representative supporting trace."
        )
    _close_ranking_note(bundle, first, second)

    panels = st.columns(2)
    for column, rfc_id in zip(panels, (first, second)):
        subset = ordered[ordered["rfc_id"].astype(str) == rfc_id]
        if subset.empty:  # pragma: no cover - options come from this frame
            continue
        row = subset.iloc[0]
        with column:
            st.markdown(f"#### {rfc_id}")
            st.markdown(decision_badge(row.get("decision")), unsafe_allow_html=True)
            metrics = st.columns(2)
            metrics[0].metric("Rank", int(row["rank"]) if pd.notna(row["rank"]) else "n/a")
            metrics[1].metric(
                "Score", f"{row['score']:g}" if pd.notna(row["score"]) else "n/a"
            )
            metrics = st.columns(2)
            metrics[0].metric("Specificity", str(row.get("specificity")))
            metrics[1].metric("Confidence", str(row.get("confidence")))
            st.caption(
                f"{int(row.get('supporting_signal_count') or 0)} supporting "
                f"observations, aggregate score {row.get('aggregate_score')}."
            )
            st.markdown("**Matched indicators**")
            st.markdown(f"`{row.get('matched_indicator_ids') or 'none'}`")
            st.markdown("**Reasoning summary**")
            st.info(str(row.get("reasoning_summary") or "No summary recorded."))

            trace = _trace_for_signal(bundle, rfc_id, shared_signal) or _example_trace(
                bundle, row
            )
            breakdown = _breakdown_frame(trace)
            if breakdown.empty:
                st.caption("No example trace is available for this candidate.")
                continue
            st.markdown(
                f"**Score breakdown** (trace `{trace.get('trace_id')}`, "
                f"decision `{trace.get('decision')}`)"
            )
            show_df(breakdown)
            steps = (trace.get("score_breakdown") or {}).get("steps") or []
            if steps:
                with st.expander("Arithmetic, step by step"):
                    for index, step in enumerate(steps, start=1):
                        st.markdown(f"{index}. {step}")


def main() -> None:
    page_setup(
        "Matching Results",
        "🎯",
        subtitle="Ranked RFC candidates, the scores behind them, and the matches they aggregate.",
    )
    output_dir = sidebar_controls()
    bundle = load_bundle(output_dir)
    sidebar_status(bundle)

    if bundle.ranked_df.empty and bundle.matches_df.empty:
        empty_state(
            "No ranked candidates and no matches in this output directory.",
            output_dir=output_dir,
        )
        return

    matches = _enriched_matches(bundle)
    ranked = bundle.ranked_df

    st.subheader("Filters")
    controls = st.columns(5)
    rfc_ids = multiselect_filter(
        "RFC",
        pd.concat(
            [ranked["rfc_id"], matches["rfc_id"]] if not matches.empty else [ranked["rfc_id"]]
        ),
        key="matching_rfc",
        container=controls[0],
    )
    confidences = multiselect_filter(
        "Confidence", ranked["confidence"], key="matching_confidence", container=controls[1]
    )
    rr_types = multiselect_filter(
        "Record type",
        matches["rr_type"] if "rr_type" in matches.columns else None,
        key="matching_rr_type",
        container=controls[2],
    )
    zones = multiselect_filter(
        "Zone", matches["zone"], key="matching_zone", container=controls[3]
    )
    window = date_range_slice(
        "Observation window",
        matches["observation_timestamp"] if not matches.empty else None,
        key="matching_dates",
        container=controls[4],
    )

    ranked_view = filter_dataframe(ranked, rfc_id=rfc_ids, confidence=confidences)
    match_view = filter_dataframe(
        matches,
        rfc_id=rfc_ids,
        rr_type=rr_types,
        zone=zones,
        observation_timestamp=window,
    )

    st.divider()
    st.subheader("Ranked candidates")
    if ranked_view.empty:
        no_rows(
            "No ranked candidate matches these filters. Note that confidence and "
            "RFC filters apply to the aggregate candidate, not to single matches."
        )
    else:
        show_df(
            ranked_view.sort_values("rank", na_position="last"),
            columns=[
                "rank",
                "rfc_id",
                "rfc_title",
                "specificity",
                "decision",
                "score",
                "aggregate_score",
                "confidence",
                "supporting_signal_count",
                "valid_match_count",
                "partial_match_count",
                "timestamp_invalid_count",
                "first_seen",
                "last_seen",
                "matched_indicator_ids",
                "matched_fields",
            ],
        )
        st.caption(
            "`score` is the best single-signal score (what drives the rank); "
            "`aggregate_score` sums every supporting signal and is a volume "
            "measure, not a confidence measure."
        )
        _ranked_chart(ranked_view)

        with st.expander("Reasoning summary per candidate", expanded=False):
            for _, row in ranked_view.sort_values("rank", na_position="last").iterrows():
                st.markdown(f"**{row['rfc_id']}** (rank {row['rank']}, score {row['score']})")
                st.info(str(row.get("reasoning_summary") or "No summary recorded."))

    st.divider()
    _comparison(bundle, ranked_view if not ranked_view.empty else ranked)

    st.divider()
    st.subheader("Per-signal matches")
    if match_view.empty:
        no_rows("No per-signal match matches these filters.")
    else:
        decisions = st.multiselect(
            "Decision",
            ordered_categories(match_view["decision"], DECISION_ORDER),
            default=[
                value
                for value in ("valid_match", "ambiguous", "partial_match", "timestamp_invalid")
                if value in set(match_view["decision"].astype(str))
            ],
            key="matching_decision",
            help="Leave empty to include every decision, no_match included.",
        )
        decided = filter_dataframe(match_view, decision=decisions)
        if decided.empty:
            no_rows("No match has one of the selected decisions.")
        else:
            st.markdown(f"**{len(decided)} of {len(matches)} evaluations**")
            show_df(
                decided.sort_values(["score", "observation_timestamp"], ascending=[False, True]),
                columns=[
                    "signal_id",
                    "rfc_id",
                    "decision",
                    "score",
                    "confidence",
                    "observation_timestamp",
                    "rr_type",
                    "domain",
                    "zone",
                    "matched_indicator_ids",
                    "matched_fields",
                    "missing_fields",
                    "timestamp_valid",
                    "trace_id",
                ],
                height=430,
            )
            left, right = st.columns(2)
            with left:
                _matches_over_time(decided)
            with right:
                _first_seen_chart(ranked_view if not ranked_view.empty else ranked)

    st.caption(
        "Open any `trace_id` on the Reasoning Explorer page to see the "
        "conditions, timestamp check and score arithmetic behind a single row."
    )


main()
