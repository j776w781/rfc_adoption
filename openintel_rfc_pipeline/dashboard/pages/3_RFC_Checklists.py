"""RFC Checklists: the signature database the whole pipeline rests on.

Every match this pipeline reports is only as good as the indicator that produced
it, so the checklist itself has to be readable by a reviewer who did not write
it. This page renders the database as-is: each RFC, its specificity multiplier,
and each indicator's conditions written out the way the checklist means them
(``rr_type in [CDS, CDNSKEY]``, ``algorithm equals 0``).

The page is read-only. :func:`render_rfc_detail` is the seam an editing feature
would plug into: it takes one checklist entry and owns everything rendered for
it, so a future editable variant can replace that one function without touching
the listing, the filters, or the rest of the dashboard.
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
    QUERYABILITY_COLORS,
    DashboardBundle,
    badge,
    empty_state,
    format_condition,
    format_timestamp,
    load_bundle,
    no_rows,
    page_setup,
    show_df,
    sidebar_controls,
    sidebar_status,
)

from openintel_rfc.models import (  # noqa: E402
    SPECIFICITY_MULTIPLIERS,
    RFCChecklistEntry,
)


def _checklist_frame(entries: list[RFCChecklistEntry]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "rfc_id": entry.rfc_id,
                "title": entry.title,
                "publication_date": format_timestamp(entry.publication_date, date_only=True),
                "protocol": entry.protocol,
                "specificity": entry.specificity,
                "specificity_multiplier": SPECIFICITY_MULTIPLIERS.get(entry.specificity, 1.0),
                "indicators": len(entry.indicators),
                "required_indicators": len(entry.required_indicators),
                "ambiguous_indicators": sum(1 for i in entry.indicators if i.ambiguous),
                "related_rfc_ids": "; ".join(entry.related_rfc_ids),
            }
            for entry in entries
        ]
    )


def _queryability_lookup(bundle: DashboardBundle) -> dict[str, str]:
    """indicator_id -> queryability verdict, when a schema check is available."""
    schema_df = bundle.schema_df
    if schema_df.empty:
        return {}
    return {
        str(row.indicator_id): str(row.queryability)
        for row in schema_df.itertuples(index=False)
    }


def _render_indicator(
    indicator: Any, queryability: str | None, position: int, total: int
) -> None:
    """One indicator: role, weight, ambiguity flag, and its conditions."""
    role = "required" if indicator.required else "optional"
    header = st.columns([2, 1, 1, 2])
    header[0].markdown(f"**{indicator.id}**")
    header[1].markdown(f"`{role}`")
    header[2].markdown(f"weight `{indicator.weight:g}`")
    with header[3]:
        if indicator.ambiguous:
            st.markdown(badge("ambiguous", "#8E5BD0"), unsafe_allow_html=True)
        if queryability:
            st.markdown(
                badge(queryability, QUERYABILITY_COLORS.get(queryability, "#8A8F98")),
                unsafe_allow_html=True,
            )

    st.markdown(indicator.description or "*no description*")

    st.markdown("Conditions (all must hold):")
    for condition in indicator.conditions:
        payload = condition.model_dump()
        line = format_condition(payload)
        st.code(line, language="text")
        if payload.get("notes"):
            st.caption(payload["notes"])

    if indicator.notes:
        st.caption(f"Note: {indicator.notes}")
    if indicator.ambiguous:
        st.caption(
            "Flagged ambiguous: a matching observation is equally consistent with "
            "other RFCs, so the score is penalised and the result is routed to review."
        )
    if position < total - 1:
        st.divider()


def render_rfc_detail(rfc: RFCChecklistEntry, *, queryability: dict[str, str]) -> None:
    """Render everything about one checklist entry.

    This function is the extension point for a future checklist editor: it is
    the only place that knows how an RFC entry is presented, so an editable
    version would replace this body (and add a save path through the checklist
    loader) without any other page changing. It is intentionally read-only here
    — the pipeline's determinism depends on the checklist being a versioned
    input file, not dashboard state.
    """
    st.markdown(f"### {rfc.rfc_id} — {rfc.title}")
    facts = st.columns(4)
    facts[0].metric("Published", format_timestamp(rfc.publication_date, date_only=True))
    facts[1].metric("Protocol", rfc.protocol)
    facts[2].metric("Specificity", rfc.specificity)
    facts[3].metric(
        "Score multiplier", f"{SPECIFICITY_MULTIPLIERS.get(rfc.specificity, 1.0):g}x"
    )

    if rfc.description:
        st.markdown(rfc.description)
    if rfc.related_rfc_ids:
        st.caption("Related RFCs: " + ", ".join(rfc.related_rfc_ids))
    if rfc.references:
        st.markdown("**References**")
        for reference in rfc.references:
            st.markdown(f"- {reference}")
    if rfc.notes:
        st.markdown("**Notes**")
        st.info(rfc.notes)

    st.markdown(
        f"**Indicators ({len(rfc.indicators)}: "
        f"{len(rfc.required_indicators)} required, "
        f"{len(rfc.optional_indicators)} optional)**"
    )
    if not rfc.indicators:
        no_rows("This RFC entry defines no indicators, so nothing can match it.")
        return
    with st.container(border=True):
        for position, indicator in enumerate(rfc.indicators):
            _render_indicator(
                indicator, queryability.get(indicator.id), position, len(rfc.indicators)
            )


def main() -> None:
    page_setup(
        "RFC Checklists",
        "📚",
        subtitle="The RFC indicator database, exactly as the matcher reads it.",
    )
    output_dir = sidebar_controls()
    bundle = load_bundle(output_dir)
    sidebar_status(bundle)

    if bundle.checklist_db is None or not bundle.checklist_db.rfcs:
        empty_state(
            "No RFC checklist database could be loaded, so there is nothing to show. "
            "The dashboard falls back to data/rfc_checklists/dnssec_rfc_checklists.json.",
            output_dir=output_dir,
        )
        return

    database = bundle.checklist_db
    st.caption(
        f"Checklist version {database.checklist_version}. {database.description}"
        if database.description
        else f"Checklist version {database.checklist_version}."
    )
    for note in database.notes:
        st.caption(f"- {note}")

    entries = list(database.rfcs)
    frame = _checklist_frame(entries)

    st.divider()
    st.subheader("All RFCs")
    filters = st.columns([2, 1, 1])
    search = filters[0].text_input(
        "Search by RFC number or title",
        key="checklist_search",
        placeholder="8078",
    )
    protocol = filters[1].selectbox(
        "Protocol", ["All", *sorted(frame["protocol"].unique())], key="checklist_protocol"
    )
    specificity = filters[2].selectbox(
        "Specificity",
        ["All", *[s for s in ("very_high", "high", "medium", "low") if s in set(frame["specificity"])]],
        key="checklist_specificity",
    )

    filtered = frame
    if search.strip():
        needle = search.strip().lower()
        filtered = filtered[
            filtered["rfc_id"].str.lower().str.contains(needle, regex=False)
            | filtered["title"].str.lower().str.contains(needle, regex=False)
        ]
    if protocol != "All":
        filtered = filtered[filtered["protocol"] == protocol]
    if specificity != "All":
        filtered = filtered[filtered["specificity"] == specificity]

    if filtered.empty:
        no_rows("No RFC matches these filters.")
        return

    show_df(filtered)
    st.caption(
        "`specificity_multiplier` scales the raw indicator score: a very_high "
        "RFC such as RFC 8078 is worth 1.5x a medium one, because its signature "
        "is far harder to produce by accident."
    )

    st.divider()
    st.subheader("RFC detail")
    options = list(filtered["rfc_id"])
    labels = dict(zip(filtered["rfc_id"], filtered["title"]))
    selected = st.selectbox(
        "RFC",
        options,
        format_func=lambda rfc_id: f"{rfc_id} — {labels.get(rfc_id, '')}",
        key="checklist_detail",
    )
    entry = database.get(selected)
    if entry is None:  # pragma: no cover - options come from the same database
        no_rows("That RFC is no longer present in the checklist database.")
        return
    render_rfc_detail(entry, queryability=_queryability_lookup(bundle))


main()
