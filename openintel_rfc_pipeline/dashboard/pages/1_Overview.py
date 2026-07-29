"""Overview: what this run contains, at a glance.

Counters come from ``bundle.summary`` (built by ``dashboard_data.summarize``),
so the numbers here and the numbers the CLI printed are the same numbers. The
three charts answer the three questions a reader has before anything else: which
RFCs were matched at all, how much of the checklist the corpus can even answer,
and how much manual review this run generated.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Streamlit runs pages as top-level scripts; put `dashboard/` on sys.path so the
# shared bootstrap and helpers resolve, then let _bootstrap do the rest.
_DASHBOARD_DIR = str(Path(__file__).resolve().parents[1])
if _DASHBOARD_DIR not in sys.path:
    sys.path.insert(0, _DASHBOARD_DIR)

from _bootstrap import setup  # noqa: E402

setup()

import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from _shared import (  # noqa: E402
    DECISION_COLORS,
    DECISION_ORDER,
    QUERYABILITY_COLORS,
    QUERYABILITY_ORDER,
    SEVERITY_COLORS,
    SEVERITY_ORDER,
    DashboardBundle,
    empty_state,
    load_bundle,
    no_rows,
    ordered_categories,
    page_setup,
    show_df,
    show_fig,
    sidebar_controls,
    sidebar_status,
)


def _counters(summary: dict) -> None:
    st.subheader("Run counters")

    row = st.columns(4)
    row[0].metric("RFCs in checklist", summary.get("rfc_count", 0))
    row[1].metric("Dictionary fields", summary.get("dictionary_field_count", 0))
    row[2].metric("Indicators", summary.get("indicator_count", 0))
    row[3].metric("Observed signals", summary.get("signal_count", 0))

    row = st.columns(4)
    row[0].metric("Queryable indicators", summary.get("queryable_indicator_count", 0))
    row[1].metric(
        "Partially queryable", summary.get("partially_queryable_indicator_count", 0)
    )
    row[2].metric("Non-queryable", summary.get("non_queryable_indicator_count", 0))
    row[3].metric("Ambiguous", summary.get("ambiguous_indicator_count", 0))

    row = st.columns(4)
    row[0].metric("Ranked matches", summary.get("ranked_candidate_count", 0))
    row[1].metric("Valid matches", summary.get("valid_match_count", 0))
    row[2].metric("Review items", summary.get("review_item_count", 0))
    row[3].metric("High-severity items", summary.get("high_severity_count", 0))

    st.caption(
        "Indicator counts describe the checklist as evaluated against this "
        "dictionary, not the corpus. `valid_match` counts signal x RFC "
        "evaluations, so one observation can contribute to several RFCs."
    )


def _matches_per_rfc(bundle: DashboardBundle, include_no_match: bool) -> None:
    st.markdown("**Matches per RFC**")
    matches = bundle.matches_df
    if matches.empty:
        no_rows("No rfc_matches.json rows in this output directory.")
        return

    frame = matches[["rfc_id", "decision"]].copy()
    frame["decision"] = frame["decision"].astype("string").fillna("unknown")
    if not include_no_match:
        frame = frame[frame["decision"] != "no_match"]
    if frame.empty:
        no_rows(
            "Every evaluation in this run is a `no_match`. Enable "
            "'Include no_match' to see them."
        )
        return

    grouped = (
        frame.groupby(["rfc_id", "decision"], dropna=False)
        .size()
        .reset_index(name="evaluations")
    )
    totals = grouped.groupby("rfc_id")["evaluations"].sum().sort_values(ascending=False)
    figure = px.bar(
        grouped,
        x="rfc_id",
        y="evaluations",
        color="decision",
        color_discrete_map=DECISION_COLORS,
        category_orders={
            "rfc_id": list(totals.index),
            "decision": ordered_categories(grouped["decision"], DECISION_ORDER),
        },
        title="Signal x RFC evaluations by decision",
    )
    figure.update_layout(xaxis_title="", yaxis_title="evaluations", barmode="stack")
    show_fig(figure, height=380)


def _queryability_donut(summary: dict) -> None:
    st.markdown("**Indicator queryability**")
    counts = {
        "queryable": summary.get("queryable_indicator_count", 0),
        "partially_queryable": summary.get("partially_queryable_indicator_count", 0),
        "ambiguous": summary.get("ambiguous_indicator_count", 0),
        "non_queryable": summary.get("non_queryable_indicator_count", 0),
    }
    present = {name: value for name, value in counts.items() if value}
    if not present:
        no_rows("No schema check has been run against this output directory.")
        return
    frame = pd.DataFrame(
        {"queryability": list(present), "indicators": list(present.values())}
    )
    figure = px.pie(
        frame,
        names="queryability",
        values="indicators",
        hole=0.55,
        color="queryability",
        color_discrete_map=QUERYABILITY_COLORS,
        category_orders={
            "queryability": ordered_categories(frame["queryability"], QUERYABILITY_ORDER)
        },
        title="How much of the checklist this dictionary can answer",
    )
    figure.update_traces(textinfo="label+value")
    show_fig(figure, height=380)


def _review_by_severity(bundle: DashboardBundle) -> None:
    st.markdown("**Review items by severity**")
    review = bundle.review_df
    if review.empty:
        no_rows("This run produced no review items.")
        return
    counts = (
        review.assign(severity=review["severity"].astype("string").fillna("unknown"))
        .groupby("severity")
        .size()
        .reset_index(name="items")
    )
    order = ordered_categories(counts["severity"], SEVERITY_ORDER)
    figure = px.bar(
        counts,
        x="severity",
        y="items",
        color="severity",
        color_discrete_map=SEVERITY_COLORS,
        category_orders={"severity": order},
        title="Open findings by severity",
    )
    figure.update_layout(xaxis_title="", yaxis_title="items", showlegend=False)
    show_fig(figure, height=340)


def _top_matched_rfcs(bundle: DashboardBundle) -> None:
    st.subheader("Top matched RFCs")
    ranked = bundle.ranked_df
    if ranked.empty:
        no_rows(
            "No ranked candidates. Either nothing matched, or ranked_candidates.json "
            "is missing from this directory."
        )
        return
    top = ranked.sort_values("rank", na_position="last").head(8)
    show_df(
        top,
        columns=[
            "rank",
            "rfc_id",
            "rfc_title",
            "specificity",
            "score",
            "confidence",
            "supporting_signal_count",
            "valid_match_count",
            "timestamp_invalid_count",
            "first_seen",
        ],
    )
    st.caption(
        "`score` is the best single-signal score for that RFC; "
        "`timestamp_invalid_count` counts observations that matched the "
        "indicators but predate publication and were therefore not scored."
    )


def _high_severity_items(bundle: DashboardBundle) -> None:
    st.subheader("High-severity review items")
    review = bundle.review_df
    if review.empty:
        no_rows("This run produced no review items.")
        return
    high = review[review["severity"].astype("string") == "high"]
    if high.empty:
        st.success("No high-severity items in this run.")
        return
    show_df(
        high,
        columns=[
            "item_id",
            "item_type",
            "reason",
            "affected_rfc_ids",
            "affected_fields",
            "suggested_action",
            "status",
        ],
        height=320,
    )
    st.caption("Full evidence and the resolution controls are on the Review Queue page.")


def main() -> None:
    page_setup(
        "Overview",
        "📊",
        subtitle="Counters, decision mix and review load for the selected run.",
    )
    output_dir = sidebar_controls()
    bundle = load_bundle(output_dir)
    sidebar_status(bundle)

    if not bundle.has_analysis and bundle.schema_df.empty:
        empty_state(
            "No pipeline output found, so there is nothing to summarise.",
            output_dir=output_dir,
        )
        return

    summary = bundle.summary or {}
    _counters(summary)

    st.divider()
    include_no_match = st.checkbox(
        "Include `no_match` evaluations in the per-RFC chart",
        value=False,
        help=(
            "no_match traces are kept on purpose — they record why an RFC was "
            "rejected — but they dominate the counts, so they are hidden by default."
        ),
    )
    left, right = st.columns([3, 2])
    with left:
        _matches_per_rfc(bundle, include_no_match)
    with right:
        _queryability_donut(summary)

    _review_by_severity(bundle)

    st.divider()
    _top_matched_rfcs(bundle)

    st.divider()
    _high_severity_items(bundle)


main()
