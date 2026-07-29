"""OpenINTEL Data Explorer: the observations, before any RFC reasoning.

Everything downstream is an interpretation of these rows, so it is worth looking
at them on their own terms first: what record types were seen, which algorithm
and digest values appear, how the observations are spread over time, and which
normalized fields are actually populated. A field that is null everywhere cannot
support or refute anything, and that is visible here and nowhere else.
"""

from __future__ import annotations

import sys
from pathlib import Path

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
    date_range_slice,
    empty_state,
    filter_dataframe,
    int_like,
    load_bundle,
    multiselect_filter,
    no_rows,
    page_setup,
    show_df,
    show_fig,
    sidebar_controls,
    sidebar_status,
)

#: Fields the pipeline normalizes out of OpenINTEL Parquet columns.
_VALUE_FIELDS: tuple[str, ...] = (
    "rr_type",
    "algorithm",
    "digest_type",
    "key_tag",
    "flags",
)

ALGORITHM_ZERO_NOTE = (
    "**Algorithm 0 is not a signing algorithm.** In a CDS or CDNSKEY record it "
    "is the RFC 8078 *delete* signal: the child is asking the parent to remove "
    "its DS records. Reading the bar for 0 as \"a very popular algorithm\" "
    "inverts its meaning — those rows are teardown requests, not deployments."
)


def _distribution(frame: pd.DataFrame, column: str, title: str) -> None:
    """A bar chart of one field's values, missing values counted explicitly."""
    if column not in frame.columns:
        no_rows(f"`{column}` is not present in observed_signals.json.")
        return
    series = frame[column]
    if column in {"algorithm", "digest_type", "key_tag"}:
        series = int_like(series)
    labels = series.astype("string").fillna("(missing)")
    counts = labels.value_counts().reset_index()
    counts.columns = [column, "observations"]
    if counts.empty:
        no_rows(f"No values for `{column}` in the current selection.")
        return

    # Sort numerically where the field is numeric, so 2 < 8 < 13 < 15.
    numeric = pd.to_numeric(counts[column], errors="coerce")
    if numeric.notna().any():
        counts = counts.assign(_sort=numeric).sort_values(
            ["_sort", column], na_position="last"
        ).drop(columns="_sort")
    else:
        counts = counts.sort_values("observations", ascending=False)

    figure = px.bar(
        counts,
        x=column,
        y="observations",
        title=title,
        text="observations",
    )
    figure.update_layout(xaxis_title="", yaxis_title="observations", showlegend=False)
    figure.update_xaxes(type="category")
    figure.update_traces(textposition="outside", cliponaxis=False)
    show_fig(figure, height=330)


def _over_time(frame: pd.DataFrame) -> None:
    st.markdown("**Observations over time**")
    stamps = pd.to_datetime(frame["timestamp"], errors="coerce").dropna()
    if stamps.empty:
        no_rows("No usable timestamps in the current selection.")
        return
    granularity = st.radio(
        "Bucket",
        ["Monthly", "Yearly"],
        horizontal=True,
        key="signals_granularity",
    )
    period = "M" if granularity == "Monthly" else "Y"
    counts = (
        stamps.dt.to_period(period)
        .value_counts()
        .sort_index()
        .rename_axis("period")
        .reset_index(name="observations")
    )
    counts["period"] = counts["period"].astype(str)
    figure = px.line(
        counts,
        x="period",
        y="observations",
        markers=True,
        title=f"{granularity} observation count",
    )
    figure.update_layout(xaxis_title="", yaxis_title="observations")
    show_fig(figure, height=330)
    st.caption(
        "Gaps are gaps in the measurement corpus supplied to the pipeline, not "
        "evidence that nothing was deployed in those periods."
    )


def _coverage(frame: pd.DataFrame) -> None:
    st.markdown("**Field coverage**")
    total = len(frame)
    rows = []
    for name in _VALUE_FIELDS:
        if name not in frame.columns:
            continue
        populated = int(frame[name].notna().sum())
        rows.append(
            {
                "field": name,
                "populated": populated,
                "missing": total - populated,
                "populated_pct": round(100.0 * populated / total, 1) if total else 0.0,
            }
        )
    if not rows:
        no_rows("No normalized value fields are present.")
        return
    show_df(pd.DataFrame(rows))
    st.caption(
        "A field that is missing everywhere makes every condition on it fail. "
        "The matcher records that as a missing field rather than as a "
        "negative finding, and the Schema Check page explains why."
    )


def _explorer(bundle: DashboardBundle) -> None:
    signals = bundle.signals_df

    st.subheader("Filters")
    controls = st.columns([1, 1, 2])
    rr_types = multiselect_filter(
        "Record type", signals["rr_type"], key="signals_rr_type", container=controls[0]
    )
    zones = multiselect_filter(
        "Zone", signals["zone"], key="signals_zone", container=controls[1]
    )
    window = date_range_slice(
        "Observation window", signals["timestamp"], key="signals_dates", container=controls[2]
    )

    filtered = filter_dataframe(
        signals, rr_type=rr_types, zone=zones, timestamp=window
    )

    st.metric("Observations in selection", f"{len(filtered)} of {len(signals)}")
    if filtered.empty:
        no_rows("No observation matches these filters. Widen them to see rows again.")
        return

    st.divider()
    st.subheader("Observed signals")
    display = filtered.assign(
        algorithm=int_like(filtered["algorithm"]),
        digest_type=int_like(filtered["digest_type"]),
        key_tag=int_like(filtered["key_tag"]),
    )
    show_df(
        display,
        columns=[
            "signal_id",
            "timestamp",
            "domain",
            "zone",
            "rr_type",
            "algorithm",
            "digest_type",
            "key_tag",
            "flags",
            "source",
            "measurement_id",
            "origin_file",
        ],
        height=420,
    )

    st.divider()
    st.subheader("Field distributions")
    columns = st.columns(3)
    with columns[0]:
        _distribution(filtered, "rr_type", "Record types")
    with columns[1]:
        _distribution(filtered, "algorithm", "DNSSEC algorithm numbers")
        st.info(ALGORITHM_ZERO_NOTE)
    with columns[2]:
        _distribution(filtered, "digest_type", "DS digest types")
        st.caption(
            "Digest type 0 accompanies the same RFC 8078 delete signal; digest "
            "type 2 is SHA-256, the RFC 4509 indicator."
        )

    st.divider()
    left, right = st.columns([3, 2])
    with left:
        _over_time(filtered)
    with right:
        _coverage(filtered)


def main() -> None:
    page_setup(
        "OpenINTEL Data Explorer",
        "🛰️",
        subtitle="The normalized observations the matcher was given, on their own terms.",
    )
    output_dir = sidebar_controls()
    bundle = load_bundle(output_dir)
    sidebar_status(bundle)

    if bundle.signals_df.empty:
        empty_state(
            "No observed_signals.json in this output directory, so there are no "
            "observations to explore.",
            output_dir=output_dir,
        )
        return

    _explorer(bundle)


main()
