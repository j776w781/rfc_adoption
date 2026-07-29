"""Reasoning Explorer: every decision, opened up.

This page exists for the reader who does not trust the pipeline. For one
signal x RFC evaluation it shows the whole chain: which conditions passed and
failed with expected against observed values, which fields were absent, whether
the observation postdates the RFC, how each term of the score was computed, the
raw observation the verdict rests on, and what the pipeline itself says it is
uncertain about.

The decision filter defaults to ``timestamp_invalid`` rather than to everything.
Dumping several hundred traces teaches nothing; the timestamp-invalid cases are
where the pipeline refuses to award a score it otherwise would have, which is
the most informative thing it does.
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
import streamlit as st  # noqa: E402

from _shared import (  # noqa: E402
    DECISION_COLORS,
    DECISION_ORDER,
    DashboardBundle,
    badge,
    confidence_color,
    decision_badge,
    empty_state,
    format_timestamp,
    format_value,
    load_bundle,
    no_rows,
    ordered_categories,
    page_setup,
    show_df,
    sidebar_controls,
    sidebar_status,
)

#: Where the explorer starts. Chosen because these traces show the pipeline
#: withholding a score it had already computed, which is its least obvious and
#: most consequential behaviour.
DEFAULT_DECISION = "timestamp_invalid"

#: Ordered as the scoring formula applies them, so the table reads top to bottom
#: like the arithmetic does.
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

_DECISION_MEANING: dict[str, str] = {
    "valid_match": (
        "Every evaluable required indicator matched, none of them flagged "
        "ambiguous, and the observation postdates publication."
    ),
    "ambiguous": (
        "Every evaluable required indicator matched, but at least one matched "
        "indicator is flagged ambiguous: the same observation is equally "
        "consistent with another RFC."
    ),
    "partial_match": (
        "Some, but not all, of the evaluable required indicators matched — or "
        "only optional indicators did."
    ),
    "timestamp_invalid": (
        "The indicators matched, but the observation predates the RFC's "
        "publication. The score is forfeited: an observation cannot evidence "
        "adoption of a document that did not exist yet."
    ),
    "non_queryable": (
        "Every required indicator of this RFC depends on a field the corpus "
        "does not export, so nothing could be tested."
    ),
    "no_match": "No required or optional indicator matched this observation.",
}


def _conditions_frame(conditions: Any) -> pd.DataFrame:
    if not isinstance(conditions, list) or not conditions:
        return pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "field": condition.get("field"),
                "op": condition.get("op"),
                "expected": format_value(condition.get("expected")),
                "observed": format_value(condition.get("observed")),
                "passed": condition.get("passed"),
                "field_present": condition.get("field_present"),
                "explanation": condition.get("explanation"),
            }
            for condition in conditions
            if isinstance(condition, dict)
        ]
    )


def _timestamp_section(trace: dict[str, Any]) -> None:
    check = trace.get("timestamp_check") or {}
    st.markdown("#### Timestamp check")
    columns = st.columns(4)
    columns[0].metric(
        "Observation", format_timestamp(check.get("observation_timestamp"), date_only=True)
    )
    columns[1].metric(
        "RFC published", format_timestamp(check.get("rfc_publication_date"), date_only=True)
    )
    delta = check.get("days_after_publication")
    columns[2].metric(
        "Days after publication", delta if delta is not None else "n/a"
    )
    valid = bool(check.get("valid"))
    columns[3].markdown(
        badge("valid" if valid else "invalid", "#2E9E5B" if valid else "#D64545"),
        unsafe_allow_html=True,
    )
    explanation = check.get("explanation")
    if explanation:
        (st.success if valid else st.error)(str(explanation))
    if delta is not None and delta < 0:
        st.caption(
            f"The observation precedes publication by {abs(int(delta))} days, so "
            "any score it earned is withheld and the case is routed to review."
        )


def _score_section(trace: dict[str, Any]) -> None:
    breakdown = trace.get("score_breakdown") or {}
    st.markdown("#### Score breakdown")
    if not breakdown:
        no_rows("This trace carries no score breakdown.")
        return
    left, right = st.columns([1, 2])
    with left:
        show_df(
            pd.DataFrame(
                [
                    {"term": term, "value": breakdown.get(term)}
                    for term in _BREAKDOWN_TERMS
                    if term in breakdown
                ]
            )
        )
    with right:
        steps = breakdown.get("steps") or []
        if not steps:
            no_rows("No arithmetic steps were recorded for this trace.")
        else:
            st.markdown("**Arithmetic, in order**")
            # An ordered list, not a blob: the point is that a reader can check
            # each term against the formula without re-deriving it.
            for index, step in enumerate(steps, start=1):
                st.markdown(f"{index}. {step}")


def _observation_section(trace: dict[str, Any]) -> None:
    observation = trace.get("supporting_observation") or {}
    st.markdown("#### Supporting observation")
    if not observation:
        no_rows("No supporting observation was attached to this trace.")
        return
    facts = {
        key: observation.get(key)
        for key in ("signal_id", "timestamp", "domain", "zone", "source", "measurement_id")
        if key in observation
    }
    if facts:
        show_df(
            pd.DataFrame({"attribute": list(facts), "value": [str(v) for v in facts.values()]})
        )
    fields = observation.get("fields")
    if isinstance(fields, dict) and fields:
        st.markdown("**Normalized fields**")
        show_df(
            pd.DataFrame(
                {
                    "field": list(fields),
                    "observed": [format_value(fields[key]) for key in fields],
                }
            )
        )
    explanations = observation.get("indicator_explanations")
    if isinstance(explanations, list) and explanations:
        st.markdown("**Per-indicator outcome**")
        for line in explanations:
            st.markdown(f"- {line}")


def render_trace(trace: dict[str, Any]) -> None:
    """Render one reasoning trace in full."""
    decision = str(trace.get("decision"))
    st.markdown(f"### {trace.get('rfc_id')} — {trace.get('rfc_title')}")
    header = st.columns([1, 1, 1, 2])
    with header[0]:
        st.markdown(decision_badge(decision), unsafe_allow_html=True)
    with header[1]:
        st.markdown(
            badge(trace.get("confidence"), confidence_color(trace.get("confidence"))),
            unsafe_allow_html=True,
        )
    header[2].metric(
        "Final score", (trace.get("score_breakdown") or {}).get("final_score", "n/a")
    )
    header[3].markdown(
        f"trace `{trace.get('trace_id')}` on signal `{trace.get('signal_id')}`"
    )
    meaning = _DECISION_MEANING.get(decision)
    if meaning:
        st.caption(meaning)

    st.markdown("#### Reasoning summary")
    # Verbatim: this is the pipeline's own account of the decision.
    st.info(str(trace.get("reasoning_summary") or "No summary was recorded."))

    st.divider()
    _timestamp_section(trace)

    st.divider()
    st.markdown("#### Conditions")
    matched = _conditions_frame(trace.get("matched_conditions"))
    failed = _conditions_frame(trace.get("failed_conditions"))
    left, right = st.columns(2)
    with left:
        st.markdown(f"**Matched conditions ({len(matched)})**")
        if matched.empty:
            no_rows("No condition passed for this evaluation.")
        else:
            show_df(matched)
    with right:
        st.markdown(f"**Failed conditions ({len(failed)})**")
        if failed.empty:
            st.success("No condition failed.")
        else:
            show_df(failed)

    missing = trace.get("missing_fields") or []
    if missing:
        st.warning(
            "Fields absent from the observation: "
            + ", ".join(f"`{name}`" for name in missing)
            + ". Absence is recorded as a failure to test, not as evidence "
            "against the RFC."
        )
    else:
        st.caption("Every field referenced by the evaluated conditions was present.")

    st.markdown("#### Indicator outcomes")
    show_df(
        pd.DataFrame(
            [
                {
                    "outcome": label,
                    "indicator_ids": "; ".join(str(i) for i in (trace.get(key) or []))
                    or "none",
                }
                for label, key in (
                    ("matched", "matched_indicator_ids"),
                    ("failed", "failed_indicator_ids"),
                    ("skipped (non-queryable)", "skipped_indicator_ids"),
                    ("required but unmatched", "missing_required_indicator_ids"),
                    ("matched OpenINTEL fields", "matched_openintel_fields"),
                )
            ]
        )
    )

    st.divider()
    _score_section(trace)

    st.divider()
    _observation_section(trace)

    notes = trace.get("uncertainty_notes") or []
    st.divider()
    st.markdown("#### Uncertainty notes")
    if not notes:
        st.caption("The pipeline recorded no caveats for this evaluation.")
    else:
        for note in notes:
            st.warning(note)


def _trace_label(row: pd.Series) -> str:
    return (
        f"{row['trace_id']} — {row['rfc_id']} / {row['signal_id']} "
        f"({row['decision']}, score {row['final_score']})"
    )


def _explorer(bundle: DashboardBundle) -> None:
    traces_df = bundle.traces_df

    st.subheader("Select a decision to inspect")
    controls = st.columns([1, 1, 1])
    decisions_available = ordered_categories(traces_df["decision"], DECISION_ORDER)
    default_decisions = (
        [DEFAULT_DECISION] if DEFAULT_DECISION in decisions_available else decisions_available[:1]
    )
    decisions = controls[0].multiselect(
        "Decision",
        decisions_available,
        default=default_decisions,
        key="reasoning_decision",
        help=(
            "Defaults to timestamp_invalid: those traces show the pipeline "
            "withholding a score. Leave empty to include every decision."
        ),
    )
    rfc_ids = controls[1].multiselect(
        "RFC",
        sorted(set(traces_df["rfc_id"].astype(str))),
        default=[],
        key="reasoning_rfc",
    )
    signal_ids = controls[2].multiselect(
        "Signal",
        sorted(set(traces_df["signal_id"].astype(str))),
        default=[],
        key="reasoning_signal",
    )

    filtered = traces_df
    if decisions:
        filtered = filtered[filtered["decision"].astype(str).isin(decisions)]
    if rfc_ids:
        filtered = filtered[filtered["rfc_id"].astype(str).isin(rfc_ids)]
    if signal_ids:
        filtered = filtered[filtered["signal_id"].astype(str).isin(signal_ids)]

    st.caption(
        f"{len(filtered)} of {len(traces_df)} traces selected. "
        "Every signal x RFC pair produces a trace, including the ones that "
        "explain a rejection."
    )
    if filtered.empty:
        no_rows("No trace matches these filters. Widen them to see traces again.")
        return

    counts = filtered["decision"].astype("string").value_counts()
    chips = st.columns(min(6, max(1, len(counts))))
    for position, (decision, count) in enumerate(counts.items()):
        chips[position % len(chips)].markdown(
            badge(f"{decision}: {count}", DECISION_COLORS.get(str(decision), "#8A8F98")),
            unsafe_allow_html=True,
        )

    st.markdown("**Traces in selection**")
    show_df(
        filtered.sort_values(["final_score", "trace_id"], ascending=[False, True]),
        columns=[
            "trace_id",
            "rfc_id",
            "signal_id",
            "decision",
            "confidence",
            "final_score",
            "timestamp_valid",
            "observation_timestamp",
            "matched_condition_count",
            "failed_condition_count",
            "missing_fields",
        ],
        height=280,
    )

    st.divider()
    ordered = filtered.sort_values(["rfc_id", "signal_id"])
    labels = {row["trace_id"]: _trace_label(row) for _, row in ordered.iterrows()}
    options = list(ordered["trace_id"])
    focus = st.session_state.get("focus_trace_id")
    index = options.index(focus) if focus in options else 0
    chosen = st.selectbox(
        "Trace",
        options,
        index=index,
        format_func=lambda trace_id: labels.get(trace_id, str(trace_id)),
        key="reasoning_trace",
    )

    trace = bundle.trace_by_id(str(chosen))
    if trace is None:
        no_rows(
            "That trace id is listed in the summary table but its full record is "
            "missing from reasoning_traces.json."
        )
        return
    with st.container(border=True):
        render_trace(trace)


def main() -> None:
    page_setup(
        "Reasoning Explorer",
        "🔍",
        subtitle="Conditions, timestamp checks and score arithmetic for one decision at a time.",
    )
    output_dir = sidebar_controls()
    bundle = load_bundle(output_dir)
    sidebar_status(bundle)

    if bundle.traces_df.empty:
        empty_state(
            "No reasoning_traces.json in this output directory, so no decision "
            "can be inspected.",
            output_dir=output_dir,
        )
        return

    _explorer(bundle)


main()
