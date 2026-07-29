"""Adoption Timeline: when each RFC's signature first became visible.

Built from valid matches only, so timestamp-invalid observations never
contribute a first-seen date. The single most important caveat is stated on the
page itself rather than buried here: **first_seen is bounded by measurement
coverage.** It is the earliest date on which the corpus could show the
mechanism, which is a lower bound on visibility and says nothing about when an
operator actually deployed it. Where a dictionary field only exists from a date
later than the RFC's publication, the bound is tighter still.
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
    DashboardBundle,
    empty_state,
    load_bundle,
    no_rows,
    page_setup,
    show_df,
    show_fig,
    sidebar_controls,
    sidebar_status,
)

COVERAGE_CAVEAT = (
    "**first_seen is bounded by measurement coverage.** It is the earliest "
    "observation in this corpus that is consistent with the RFC's indicators — "
    "a lower bound on when the mechanism became *visible to this measurement*, "
    "not on when it was deployed. Several dictionary fields only become "
    "available from 2010-01-01 (and `flags` from 2016-01-01), so for RFCs "
    "published before those dates the bound is set by the instrument, not by "
    "the Internet."
)


def _bucket_frame(
    entries: list[dict[str, Any]], rfc_ids: list[str], key: str
) -> pd.DataFrame:
    """Flatten one bucket list (monthly / yearly / confidence) into a frame."""
    rows: list[dict[str, Any]] = []
    for entry in entries:
        rfc_id = str(entry.get("rfc_id"))
        if rfc_ids and rfc_id not in rfc_ids:
            continue
        for bucket in entry.get(key) or []:
            if not isinstance(bucket, dict):
                continue
            rows.append(
                {
                    "rfc_id": rfc_id,
                    "period": str(bucket.get("period")),
                    "count": bucket.get("count"),
                    "domains": bucket.get("domains"),
                    "mean_score": bucket.get("mean_score"),
                }
            )
    frame = pd.DataFrame(rows)
    return frame.sort_values(["period", "rfc_id"]) if not frame.empty else frame


def _first_seen_charts(timeline: pd.DataFrame) -> None:
    st.subheader("First seen per RFC")
    frame = timeline.dropna(subset=["first_seen"]).copy()
    if frame.empty:
        no_rows("No RFC in this run has a first-seen date.")
        return

    left, right = st.columns(2)

    with left:
        span = frame.dropna(subset=["rfc_publication_date"])
        span = span[span["first_seen"] >= span["rfc_publication_date"]]
        if span.empty:
            no_rows("No RFC has both a publication date and a later first-seen date.")
        else:
            figure = px.timeline(
                span.sort_values("rfc_publication_date"),
                x_start="rfc_publication_date",
                x_end="first_seen",
                y="rfc_id",
                color="observation_count",
                hover_data=["first_seen", "last_seen", "observation_count"],
                title="Publication date to first observation",
            )
            figure.update_yaxes(autorange="reversed", title="")
            figure.update_xaxes(title="")
            show_fig(figure, height=max(300, 44 * len(span) + 140))

    with right:
        lag = frame.dropna(subset=["days_from_publication_to_first_seen"]).sort_values(
            "days_from_publication_to_first_seen"
        )
        if lag.empty:
            no_rows("No publication-to-first-seen lag was recorded.")
        else:
            figure = px.bar(
                lag,
                x="days_from_publication_to_first_seen",
                y="rfc_id",
                orientation="h",
                text="days_from_publication_to_first_seen",
                hover_data=["first_seen", "rfc_publication_date"],
                title="Days from publication to first observation",
            )
            figure.update_layout(xaxis_title="days", yaxis_title="")
            figure.update_traces(textposition="outside", cliponaxis=False)
            show_fig(figure, height=max(300, 44 * len(lag) + 140))

    st.info(COVERAGE_CAVEAT)


def _volume_chart(entries: list[dict[str, Any]], rfc_ids: list[str]) -> None:
    st.subheader("Observation volume over time")
    granularity = st.radio(
        "Bucket", ["Monthly", "Yearly"], horizontal=True, key="timeline_granularity"
    )
    key = "monthly_counts" if granularity == "Monthly" else "yearly_counts"
    frame = _bucket_frame(entries, rfc_ids, key)
    if frame.empty:
        no_rows("No bucketed counts are available for the selected RFCs.")
        return
    figure = px.line(
        frame,
        x="period",
        y="count",
        color="rfc_id",
        markers=True,
        hover_data=["domains"],
        title=f"{granularity} supporting observations per RFC",
    )
    figure.update_layout(xaxis_title="", yaxis_title="observations")
    show_fig(figure, height=380)
    st.caption(
        "Counts come from valid matches only. A flat line at one observation per "
        "period reflects the size of the sample corpus, not adoption dynamics."
    )


def _confidence_chart(entries: list[dict[str, Any]], rfc_ids: list[str]) -> None:
    st.subheader("Score over time")
    frame = _bucket_frame(entries, rfc_ids, "confidence_over_time")
    if frame.empty:
        no_rows("No confidence buckets are available for the selected RFCs.")
        return
    figure = px.line(
        frame,
        x="period",
        y="mean_score",
        color="rfc_id",
        markers=True,
        hover_data=["count"],
        title="Mean match score per period",
    )
    figure.update_layout(xaxis_title="", yaxis_title="mean score")
    show_fig(figure, height=360)
    st.caption(
        "Mean score is the arithmetic mean of the per-signal scores in that "
        "period. It is stable when the same indicator keeps matching, so a flat "
        "line means consistent evidence, not growing certainty."
    )


def _distribution(timeline: pd.DataFrame) -> None:
    st.subheader("Where the evidence comes from")
    left, right = st.columns(2)

    with left:
        counts = timeline[["rfc_id", "distinct_domains", "distinct_zones"]].melt(
            id_vars="rfc_id", var_name="measure", value_name="count"
        )
        if counts["count"].fillna(0).sum() == 0:
            no_rows("No domain or zone counts recorded.")
        else:
            figure = px.bar(
                counts,
                x="rfc_id",
                y="count",
                color="measure",
                barmode="group",
                title="Distinct domains and zones per RFC",
            )
            figure.update_layout(xaxis_title="", yaxis_title="distinct")
            show_fig(figure, height=340)

    with right:
        zone_counts: dict[str, int] = {}
        for value in timeline.get("zones_raw", pd.Series(dtype=object)):
            if isinstance(value, list):
                for zone in value:
                    zone_counts[str(zone)] = zone_counts.get(str(zone), 0) + 1
        if not zone_counts:
            no_rows("No zones recorded on the timeline entries.")
        else:
            frame = pd.DataFrame(
                {"zone": list(zone_counts), "rfcs_seen_in_zone": list(zone_counts.values())}
            ).sort_values("rfcs_seen_in_zone", ascending=False)
            figure = px.bar(
                frame,
                x="zone",
                y="rfcs_seen_in_zone",
                title="RFCs with at least one observation per zone",
                text="rfcs_seen_in_zone",
            )
            figure.update_layout(xaxis_title="", yaxis_title="RFCs", showlegend=False)
            figure.update_traces(textposition="outside", cliponaxis=False)
            show_fig(figure, height=340)


def _timeline_page(bundle: DashboardBundle) -> None:
    timeline = bundle.timeline_df
    entries = bundle.timeline_entries

    all_rfcs = sorted(set(timeline["rfc_id"].astype(str)))
    rfc_ids = st.multiselect(
        "RFCs",
        all_rfcs,
        default=[],
        key="timeline_rfc",
        help="Leave empty to include every RFC with a timeline entry.",
    )
    selected = timeline if not rfc_ids else timeline[timeline["rfc_id"].astype(str).isin(rfc_ids)]
    if selected.empty:
        no_rows("No timeline entry matches this selection.")
        return

    st.divider()
    _first_seen_charts(selected)

    st.divider()
    _volume_chart(entries, rfc_ids)

    st.divider()
    _confidence_chart(entries, rfc_ids)

    st.divider()
    _distribution(selected)

    st.divider()
    st.subheader("Adoption table")
    show_df(
        selected.sort_values("first_seen", na_position="last"),
        columns=[
            "rfc_id",
            "rfc_title",
            "rfc_publication_date",
            "first_seen",
            "last_seen",
            "days_from_publication_to_first_seen",
            "observation_count",
            "distinct_domains",
            "distinct_zones",
            "domains",
            "zones",
            "notes",
        ],
    )
    notes = [str(note) for note in selected["notes"].dropna() if str(note).strip()]
    if notes:
        with st.expander("Per-RFC timeline notes"):
            for note in notes:
                st.markdown(f"- {note}")


def main() -> None:
    page_setup(
        "Adoption Timeline",
        "📈",
        subtitle="When each RFC's signature first appears in the corpus, and how often after that.",
    )
    output_dir = sidebar_controls()
    bundle = load_bundle(output_dir)
    sidebar_status(bundle)

    if bundle.timeline_df.empty:
        empty_state(
            "No adoption_timeline.json in this output directory, so no "
            "trajectory can be drawn.",
            output_dir=output_dir,
        )
        return

    _timeline_page(bundle)


main()
