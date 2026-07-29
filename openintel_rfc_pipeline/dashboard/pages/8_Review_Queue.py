"""Review Queue: everything the pipeline refused to decide on its own.

The queue is the honest half of the pipeline's output. It collects
non-queryable indicators, timestamp-invalid matches, partial matches with
missing fields, ambiguous indicators and rankings too close to call, each with
the evidence that produced it and a suggested action.

Reviewer decisions are written to ``review_queue_status.json`` through
``dashboard_data.save_review_status``. That file is dashboard-owned state: the
pipeline's own ``review_queue.json`` is never modified, so a re-run of the
analysis cannot be confused with a human having signed anything off.
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
    REVIEW_STATUS_COLORS,
    REVIEW_STATUS_ORDER,
    REVIEW_STATUSES,
    SEVERITY_COLORS,
    SEVERITY_ORDER,
    DashboardBundle,
    badge,
    empty_state,
    load_bundle,
    load_review_status,
    no_rows,
    ordered_categories,
    page_setup,
    save_review_status,
    severity_badge,
    show_df,
    show_fig,
    sidebar_controls,
    sidebar_status,
)

from openintel_rfc.utils import PipelineError  # noqa: E402

_STATUS_MAP_KEY = "review_status_map"
_STATUS_DIR_KEY = "review_status_dir"
_SAVE_ERROR_KEY = "review_status_error"

#: Statuses in the order a reviewer walks through them.
_STATUS_OPTIONS: tuple[str, ...] = tuple(
    name for name in REVIEW_STATUS_ORDER if name in REVIEW_STATUSES
)


def _widget_key(output_dir: Path, item_id: str) -> str:
    """Namespace status widgets by output directory.

    Without this, switching to another run would leave the previous run's widget
    values in session state and show the wrong status against the new items.
    """
    return f"review_status::{output_dir}::{item_id}"


def _initial_status_map(output_dir: Path, items: list[dict[str, Any]]) -> dict[str, str]:
    """Pipeline-declared status, overridden by anything a reviewer saved."""
    statuses = {
        str(item.get("item_id")): str(item.get("status") or "unresolved") for item in items
    }
    for item_id, status in load_review_status(output_dir).items():
        if item_id in statuses and status in REVIEW_STATUSES:
            statuses[item_id] = status
    return statuses


def _ensure_status_map(output_dir: Path, items: list[dict[str, Any]]) -> dict[str, str]:
    if st.session_state.get(_STATUS_DIR_KEY) != str(output_dir):
        st.session_state[_STATUS_DIR_KEY] = str(output_dir)
        st.session_state[_STATUS_MAP_KEY] = _initial_status_map(output_dir, items)
    statuses: dict[str, str] = st.session_state.setdefault(_STATUS_MAP_KEY, {})
    for item in items:
        statuses.setdefault(str(item.get("item_id")), str(item.get("status") or "unresolved"))
    return statuses


def _persist(output_dir: Path, statuses: dict[str, str]) -> None:
    """Write the whole map; surface a failure instead of losing it quietly."""
    try:
        save_review_status(output_dir, statuses)
        st.session_state[_SAVE_ERROR_KEY] = ""
    except PipelineError as exc:
        st.session_state[_SAVE_ERROR_KEY] = str(exc)
    except OSError as exc:
        st.session_state[_SAVE_ERROR_KEY] = f"Could not write review status: {exc}"


def _on_status_change(item_id: str, output_dir: Path) -> None:
    value = st.session_state.get(_widget_key(output_dir, item_id))
    if value not in REVIEW_STATUSES:
        return
    statuses = st.session_state.setdefault(_STATUS_MAP_KEY, {})
    statuses[item_id] = value
    # Written on every change so a browser reload never loses a decision.
    _persist(output_dir, statuses)


def _severity_chart(frame: pd.DataFrame, statuses: dict[str, str]) -> None:
    counts = (
        frame.assign(
            severity=frame["severity"].astype("string").fillna("unknown"),
            status=frame["item_id"].map(lambda i: statuses.get(str(i), "unresolved")),
        )
        .groupby(["severity", "status"])
        .size()
        .reset_index(name="items")
    )
    figure = px.bar(
        counts,
        x="severity",
        y="items",
        color="status",
        color_discrete_map=REVIEW_STATUS_COLORS,
        category_orders={
            "severity": ordered_categories(counts["severity"], SEVERITY_ORDER),
            "status": ordered_categories(counts["status"], REVIEW_STATUS_ORDER),
        },
        title="Review items by severity and resolution status",
    )
    figure.update_layout(xaxis_title="", yaxis_title="items", barmode="stack")
    show_fig(figure, height=320)


def _render_item(
    item: dict[str, Any], statuses: dict[str, str], output_dir: Path
) -> None:
    item_id = str(item.get("item_id"))
    severity = str(item.get("severity") or "unknown")
    status = statuses.get(item_id, "unresolved")

    heading = st.columns([1, 1, 2])
    with heading[0]:
        st.markdown(severity_badge(severity), unsafe_allow_html=True)
    with heading[1]:
        st.markdown(
            badge(status, REVIEW_STATUS_COLORS.get(status, "#8A8F98")),
            unsafe_allow_html=True,
        )
    heading[2].markdown(f"`{item.get('item_type')}`")

    st.markdown("**Reason**")
    st.write(str(item.get("reason") or ""))

    facts = st.columns(3)
    facts[0].markdown(
        "**Affected RFCs**\n\n"
        + (", ".join(str(v) for v in item.get("affected_rfc_ids") or []) or "none")
    )
    facts[1].markdown(
        "**Affected fields**\n\n"
        + (", ".join(f"`{v}`" for v in item.get("affected_fields") or []) or "none")
    )
    signal_ids = [str(v) for v in item.get("affected_signal_ids") or []]
    facts[2].markdown(
        "**Affected signals**\n\n"
        + (", ".join(signal_ids[:8]) + (" ..." if len(signal_ids) > 8 else "") or "none")
    )

    if item.get("suggested_action"):
        st.markdown("**Suggested action**")
        st.info(str(item["suggested_action"]))

    verification = item.get("verification")
    if isinstance(verification, dict) and verification:
        st.markdown("**Automated verification**")
        columns = st.columns([1, 3])
        columns[0].markdown(
            badge(
                verification.get("verification_status", "unknown"),
                {
                    "accepted": "#2E9E5B",
                    "rejected": "#D64545",
                    "needs_manual_review": "#E1A11A",
                }.get(str(verification.get("verification_status")), "#8A8F98"),
            ),
            unsafe_allow_html=True,
        )
        columns[1].caption(
            f"backend `{verification.get('backend', 'unknown')}`, "
            f"confidence `{verification.get('confidence', 'none')}`"
        )
        st.write(str(verification.get("explanation") or ""))
    else:
        st.caption("No automated verification was attached to this item.")

    trace_ids = [str(v) for v in item.get("trace_ids") or []]
    if trace_ids:
        st.caption(
            "Traces: " + ", ".join(f"`{t}`" for t in trace_ids[:6])
            + (" ..." if len(trace_ids) > 6 else "")
            + " — open them on the Reasoning Explorer page."
        )

    evidence = item.get("evidence")
    if isinstance(evidence, dict) and evidence:
        with st.expander("Evidence"):
            st.json(evidence, expanded=False)

    key = _widget_key(output_dir, item_id)
    st.selectbox(
        "Resolution",
        _STATUS_OPTIONS,
        index=_STATUS_OPTIONS.index(status) if status in _STATUS_OPTIONS else 0,
        key=key,
        on_change=_on_status_change,
        args=(item_id, output_dir),
        help="Saved to review_queue_status.json immediately; survives a reload.",
    )


def _queue(bundle: DashboardBundle, output_dir: Path) -> None:
    review = bundle.review_df
    items = bundle.review_items
    statuses = _ensure_status_map(output_dir, items)

    if st.session_state.get(_SAVE_ERROR_KEY):
        st.error(st.session_state[_SAVE_ERROR_KEY])

    resolved = sum(
        1 for item_id in review["item_id"].astype(str) if statuses.get(item_id, "unresolved") != "unresolved"
    )
    total = len(review)
    progress = st.columns([1, 1, 1, 2])
    progress[0].metric("Items", total)
    progress[1].metric("Resolved", f"{resolved} of {total}")
    progress[2].metric(
        "High severity", int((review["severity"].astype("string") == "high").sum())
    )
    with progress[3]:
        st.progress(resolved / total if total else 0.0, text="Review progress")
        st.caption(
            f"Stored in {output_dir / 'review_queue_status.json'}. The pipeline's "
            "review_queue.json is never modified."
        )

    st.divider()
    st.subheader("Filters")
    controls = st.columns(5)
    severities = controls[0].multiselect(
        "Severity",
        ordered_categories(review["severity"], SEVERITY_ORDER),
        default=[],
        key="review_severity",
    )
    types = controls[1].multiselect(
        "Item type", sorted(set(review["item_type"].astype(str))), default=[], key="review_type"
    )
    rfc_options = sorted(
        {
            str(rfc)
            for value in review["affected_rfc_ids_raw"]
            if isinstance(value, list)
            for rfc in value
        }
    )
    rfc_choice = controls[2].multiselect("RFC", rfc_options, default=[], key="review_rfc")
    field_options = sorted(
        {
            str(field)
            for value in review["affected_fields_raw"]
            if isinstance(value, list)
            for field in value
        }
    )
    field_choice = controls[3].multiselect(
        "Field", field_options, default=[], key="review_field"
    )
    status_choice = controls[4].multiselect(
        "Status", list(_STATUS_OPTIONS), default=[], key="review_status_filter"
    )

    filtered = review.assign(
        status=review["item_id"].astype(str).map(lambda i: statuses.get(i, "unresolved"))
    )
    if severities:
        filtered = filtered[filtered["severity"].astype(str).isin(severities)]
    if types:
        filtered = filtered[filtered["item_type"].astype(str).isin(types)]
    if rfc_choice:
        filtered = filtered[
            filtered["affected_rfc_ids_raw"].map(
                lambda values: isinstance(values, list)
                and any(str(v) in rfc_choice for v in values)
            )
        ]
    if field_choice:
        filtered = filtered[
            filtered["affected_fields_raw"].map(
                lambda values: isinstance(values, list)
                and any(str(v) in field_choice for v in values)
            )
        ]
    if status_choice:
        filtered = filtered[filtered["status"].isin(status_choice)]

    _severity_chart(review, statuses)

    if filtered.empty:
        no_rows("No review item matches these filters.")
        return

    st.divider()
    st.subheader(f"Items ({len(filtered)} of {total})")
    show_df(
        filtered,
        columns=[
            "item_id",
            "severity",
            "status",
            "item_type",
            "affected_rfc_ids",
            "affected_fields",
            "verification_status",
            "reason",
        ],
        height=300,
    )

    by_id = {str(item.get("item_id")): item for item in items}
    severity_rank = {name: index for index, name in enumerate(SEVERITY_ORDER)}
    ordered = filtered.assign(
        _rank=filtered["severity"].astype(str).map(lambda s: severity_rank.get(s, 99))
    ).sort_values(["_rank", "item_id"])

    for _, row in ordered.iterrows():
        item_id = str(row["item_id"])
        item = by_id.get(item_id)
        if item is None:  # pragma: no cover - frame and list come from one file
            continue
        label = f"{row['severity'].upper()} — {item_id} — {row['item_type']}"
        with st.expander(label, expanded=False):
            _render_item(item, statuses, output_dir)

    st.divider()
    if st.button("Re-save all decisions", help="Rewrite review_queue_status.json from the current state."):
        _persist(output_dir, statuses)
        if st.session_state.get(_SAVE_ERROR_KEY):
            st.error(st.session_state[_SAVE_ERROR_KEY])
        else:
            st.success(f"Saved {len(statuses)} decisions to {output_dir}.")


def main() -> None:
    page_setup(
        "Review Queue",
        "📋",
        subtitle="Findings the pipeline routed to a human, with a persisted resolution.",
    )
    output_dir = sidebar_controls()
    bundle = load_bundle(output_dir)
    sidebar_status(bundle)

    if bundle.review_df.empty:
        empty_state(
            "No review_queue.json in this output directory, so there is nothing "
            "to review.",
            output_dir=output_dir,
        )
        return

    _queue(bundle, output_dir)


main()
