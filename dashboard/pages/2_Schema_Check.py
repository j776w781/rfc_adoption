"""Schema Check: which checklist indicators this dictionary can answer.

Before any matching is meaningful, the checklist has to be reconciled with the
schema of the corpus. An indicator that references a field the dictionary does
not define can never match — not because the mechanism is absent from the
Internet, but because the measurement cannot see it. Conflating the two is the
single easiest way to produce a wrong adoption finding.

The ``reasoning`` string the schema checker writes for each indicator is the
substance of this page, so it is shown in full and never truncated.
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
    QUERYABILITY_COLORS,
    QUERYABILITY_ORDER,
    SEVERITY_ORDER,
    DashboardBundle,
    badge,
    empty_state,
    format_timestamp,
    load_bundle,
    no_rows,
    ordered_categories,
    page_setup,
    severity_badge,
    show_df,
    show_fig,
    sidebar_controls,
    sidebar_status,
)

#: Evidence keys that name indicators a review item is actually about. Used to
#: attach a severity to an indicator row; deliberately narrow, because a review
#: item that merely *mentions* an indicator is not a finding against it.
_INDICATOR_EVIDENCE_KEYS: tuple[str, ...] = (
    "indicator_ids",
    "required_indicator_ids",
    "unmatched_required_indicator_ids",
    "failed_indicator_ids",
)

_SEVERITY_RANK = {name: index for index, name in enumerate(SEVERITY_ORDER)}


def _indicator_severity(bundle: DashboardBundle) -> dict[str, str]:
    """Highest review-queue severity raised against each indicator."""
    worst: dict[str, str] = {}
    for item in bundle.review_items:
        severity = str(item.get("severity") or "")
        evidence = item.get("evidence")
        if not isinstance(evidence, dict):
            continue
        names: list[str] = []
        single = evidence.get("indicator_id")
        if isinstance(single, str):
            names.append(single)
        for key in _INDICATOR_EVIDENCE_KEYS:
            value = evidence.get(key)
            if isinstance(value, list):
                names.extend(str(entry) for entry in value)
        for name in names:
            current = worst.get(name)
            if current is None or _SEVERITY_RANK.get(severity, 99) < _SEVERITY_RANK.get(
                current, 99
            ):
                worst[name] = severity
    return worst


def _dictionary_frame(bundle: DashboardBundle) -> pd.DataFrame:
    """The dictionary as a table, however it is available."""
    rows: list[dict[str, Any]] = []
    if bundle.dictionary is not None:
        for field in bundle.dictionary.fields:
            rows.append(
                {
                    "name": field.name,
                    "type": field.type,
                    "available_from": format_timestamp(field.available_from, date_only=True),
                    "nullable": field.nullable,
                    "openintel_native_fields": "; ".join(field.openintel_native_fields),
                    "description": field.description,
                }
            )
    elif isinstance(bundle.schema_report, dict):
        for field in bundle.schema_report.get("dictionary_fields") or []:
            if not isinstance(field, dict):
                continue
            rows.append(
                {
                    "name": field.get("name"),
                    "type": field.get("type"),
                    "available_from": format_timestamp(
                        field.get("available_from"), date_only=True
                    ),
                    "nullable": field.get("nullable"),
                    "openintel_native_fields": "; ".join(
                        str(name) for name in field.get("openintel_native_fields") or []
                    ),
                    "description": field.get("description", ""),
                }
            )
    return pd.DataFrame(rows)


def _referenced_fields(schema_df: pd.DataFrame) -> list[str]:
    names: set[str] = set()
    if "fields_used_raw" in schema_df.columns:
        for value in schema_df["fields_used_raw"]:
            if isinstance(value, list):
                names.update(str(entry) for entry in value)
    if "missing_fields_raw" in schema_df.columns:
        for value in schema_df["missing_fields_raw"]:
            if isinstance(value, list):
                names.update(str(entry) for entry in value)
    return sorted(names)


def _dictionary_section(bundle: DashboardBundle) -> None:
    st.subheader("Dictionary fields")
    frame = _dictionary_frame(bundle)
    if frame.empty:
        no_rows("No OpenINTEL dictionary could be loaded, so no fields can be listed.")
        return

    referenced = set(_referenced_fields(bundle.schema_df))
    unused = set()
    if isinstance(bundle.schema_report, dict):
        unused = {
            str(name) for name in bundle.schema_report.get("unused_dictionary_fields") or []
        }
    frame = frame.assign(
        referenced_by_an_indicator=frame["name"].map(lambda n: str(n) in referenced),
        unused=frame["name"].map(lambda n: str(n) in unused),
    )
    show_df(frame)
    st.caption(
        "`available_from` bounds what the corpus can show: a field that only "
        "exists from 2016 cannot evidence adoption of a 2005 RFC before then. "
        "`openintel_native_fields` are the real Parquet columns the analysis "
        "field is resolved from."
    )

    missing_from_dictionary = sorted(referenced - set(frame["name"].astype(str)))
    if missing_from_dictionary:
        st.error(
            "Fields referenced by the checklist but absent from the dictionary: "
            + ", ".join(f"`{name}`" for name in missing_from_dictionary)
            + ". Every condition on them is unanswerable."
        )


def _queryability_chart(schema_df: pd.DataFrame) -> None:
    counts = (
        schema_df.assign(
            queryability=schema_df["queryability"].astype("string").fillna("unknown")
        )
        .groupby("queryability")
        .size()
        .reset_index(name="indicators")
    )
    figure = px.bar(
        counts,
        x="indicators",
        y="queryability",
        orientation="h",
        color="queryability",
        color_discrete_map=QUERYABILITY_COLORS,
        category_orders={
            "queryability": list(
                reversed(ordered_categories(counts["queryability"], QUERYABILITY_ORDER))
            )
        },
        title="Indicators by queryability verdict",
    )
    figure.update_layout(xaxis_title="indicators", yaxis_title="", showlegend=False)
    show_fig(figure, height=280)


def _indicator_detail(check: dict[str, Any], severity: str | None) -> None:
    """One indicator opened up: verdict, full reasoning, condition checks."""
    header = st.columns([1, 1, 1, 1])
    header[0].markdown(
        badge(check.get("queryability", "unknown"), QUERYABILITY_COLORS.get(
            str(check.get("queryability")), "#8A8F98"
        )),
        unsafe_allow_html=True,
    )
    header[1].markdown(f"required: `{bool(check.get('required'))}`")
    header[2].markdown(f"weight: `{check.get('weight')}`")
    if severity:
        header[3].markdown(severity_badge(severity), unsafe_allow_html=True)

    st.markdown(f"*{check.get('indicator_description', '')}*")

    st.markdown("**Reasoning**")
    # Shown verbatim: this text is the schema checker's argument, and abridging
    # it would defeat the purpose of the page.
    st.info(str(check.get("reasoning") or "No reasoning was recorded."))

    present = check.get("present_fields") or []
    missing = check.get("missing_fields") or []
    columns = st.columns(2)
    columns[0].markdown(
        "**Present fields**\n\n" + (", ".join(f"`{f}`" for f in present) or "none")
    )
    columns[1].markdown(
        "**Missing fields**\n\n" + (", ".join(f"`{f}`" for f in missing) or "none")
    )

    conditions = check.get("condition_checks") or []
    if conditions:
        st.markdown("**Condition checks**")
        show_df(
            pd.DataFrame(
                [
                    {
                        "field": condition.get("field"),
                        "op": condition.get("op"),
                        "expected": str(condition.get("expected")),
                        "field_exists": condition.get("field_exists"),
                        "field_type": condition.get("field_type"),
                        "available_from": format_timestamp(
                            condition.get("available_from"), date_only=True
                        ),
                        "type_compatible": condition.get("type_compatible"),
                        "explanation": condition.get("explanation"),
                    }
                    for condition in conditions
                    if isinstance(condition, dict)
                ]
            )
        )

    warnings = check.get("warnings") or []
    if warnings:
        st.markdown("**Availability warnings**")
        for warning in warnings:
            st.warning(warning)


def _indicator_section(bundle: DashboardBundle) -> None:
    st.subheader("Indicators")
    schema_df = bundle.schema_df
    if schema_df.empty:
        no_rows(
            "No schema_check.json in this output directory. Run "
            "`openintel-rfc schema-check` to produce it."
        )
        return

    severities = _indicator_severity(bundle)
    table = schema_df.assign(
        review_severity=schema_df["indicator_id"].map(
            lambda name: severities.get(str(name), "")
        )
    )

    filters = st.columns(4)
    rfc_choice = filters[0].selectbox(
        "RFC", ["All", *sorted(set(table["rfc_id"].astype(str)))], key="schema_rfc"
    )
    query_choice = filters[1].selectbox(
        "Queryability",
        ["All", *ordered_categories(table["queryability"], QUERYABILITY_ORDER)],
        key="schema_queryability",
    )
    field_choice = filters[2].selectbox(
        "References field",
        ["All", *_referenced_fields(schema_df)],
        key="schema_field",
        help="Show only indicators whose conditions read this analysis field.",
    )
    severity_choice = filters[3].selectbox(
        "Review severity",
        ["All", *ordered_categories(table["review_severity"], SEVERITY_ORDER), "none"],
        key="schema_severity",
        help=(
            "Highest severity of any review-queue item raised about the "
            "indicator. 'none' means the indicator produced no findings."
        ),
    )

    filtered = table
    if rfc_choice != "All":
        filtered = filtered[filtered["rfc_id"].astype(str) == rfc_choice]
    if query_choice != "All":
        filtered = filtered[filtered["queryability"].astype(str) == query_choice]
    if field_choice != "All":
        filtered = filtered[
            filtered["fields_used_raw"].map(
                lambda names: isinstance(names, list) and field_choice in names
            )
            | filtered["missing_fields_raw"].map(
                lambda names: isinstance(names, list) and field_choice in names
            )
        ]
    if severity_choice == "none":
        filtered = filtered[filtered["review_severity"] == ""]
    elif severity_choice != "All":
        filtered = filtered[filtered["review_severity"] == severity_choice]

    _queryability_chart(table)

    if filtered.empty:
        no_rows("No indicator matches these filters. Widen them to see rows again.")
        return

    st.markdown(f"**{len(filtered)} of {len(table)} indicators**")
    show_df(
        filtered,
        columns=[
            "rfc_id",
            "indicator_id",
            "required",
            "weight",
            "queryability",
            "fields_used",
            "present_fields",
            "missing_fields",
            "review_severity",
            "warnings",
        ],
        height=min(420, 60 + 36 * len(filtered)),
    )

    st.markdown("### Per-indicator reasoning")
    st.caption(
        "The schema checker's verdict for each indicator, in full. This text is "
        "what justifies excluding an indicator from matching."
    )
    by_id = {
        str(check.get("indicator_id")): check
        for check in (bundle.schema_report or {}).get("indicators", [])
        if isinstance(check, dict)
    }
    for _, row in filtered.iterrows():
        indicator_id = str(row["indicator_id"])
        check = by_id.get(indicator_id)
        label = f"{row['rfc_id']} — {indicator_id} ({row['queryability']})"
        with st.expander(label, expanded=str(row["queryability"]) != "queryable"):
            if check is None:
                # Fall back to the flattened frame when the full report is absent.
                st.info(str(row.get("reasoning") or "No reasoning was recorded."))
            else:
                _indicator_detail(check, str(row["review_severity"]) or None)


def _report_warnings(bundle: DashboardBundle) -> None:
    report = bundle.schema_report or {}
    warnings = report.get("warnings") or []
    if not warnings:
        return
    st.divider()
    st.subheader(f"Schema-check warnings ({len(warnings)})")
    for warning in warnings:
        st.warning(warning)


def main() -> None:
    page_setup(
        "Schema Check",
        "🧾",
        subtitle=(
            "Reconciling the RFC checklist with the OpenINTEL dictionary: what "
            "can be tested, what cannot, and why."
        ),
    )
    output_dir = sidebar_controls()
    bundle = load_bundle(output_dir)
    sidebar_status(bundle)

    if bundle.schema_df.empty and bundle.dictionary is None:
        empty_state(
            "No schema check output and no dictionary could be loaded.",
            output_dir=output_dir,
        )
        return

    report = bundle.schema_report or {}
    if report:
        meta = st.columns(4)
        meta[0].metric("RFCs", report.get("rfc_count", 0))
        meta[1].metric("Indicators", report.get("indicator_count", 0))
        meta[2].metric("Dictionary fields", report.get("dictionary_field_count", 0))
        meta[3].metric(
            "Non-queryable",
            (report.get("counts_by_queryability") or {}).get("non_queryable", 0),
        )
        st.caption(
            f"Checked {report.get('checklist_path', 'unknown checklist')} against "
            f"{report.get('dictionary_path', 'unknown dictionary')} at "
            f"{report.get('generated_at', 'unknown time')}."
        )

    st.divider()
    _dictionary_section(bundle)

    st.divider()
    _indicator_section(bundle)

    _report_warnings(bundle)


main()
