"""Entry page of the OpenINTEL RFC-adoption dashboard.

Run it from the project root::

    PYTHONPATH=src python -m streamlit run dashboard/app.py

This page frames what the pipeline does and does not claim, shows the manifest
of the run currently being displayed, and indexes the nine analysis pages. All
shared plumbing (output-directory selection, cached loading, colours, chart
styling) lives in ``_shared``; the import bootstrap lives in ``_bootstrap``.
"""

from __future__ import annotations

# Streamlit executes this file as a top-level script, so `dashboard/` is not on
# sys.path yet; locate it, then hand over to the shared bootstrap.
import sys
from pathlib import Path

_DASHBOARD_DIR = str(Path(__file__).resolve().parent)
if _DASHBOARD_DIR not in sys.path:
    sys.path.insert(0, _DASHBOARD_DIR)

from _bootstrap import setup  # noqa: E402

setup()

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from _shared import (  # noqa: E402
    APP_TITLE,
    empty_state,
    load_bundle,
    page_setup,
    show_df,
    sidebar_controls,
    sidebar_status,
)

# --------------------------------------------------------------------------- #
# Page index
# --------------------------------------------------------------------------- #

#: (page file, icon, title, one-line purpose). Kept in one place so the entry
#: page and the reader's mental model of the app stay in sync.
PAGES: tuple[tuple[str, str, str, str], ...] = (
    (
        "pages/1_Overview.py",
        "📊",
        "Overview",
        "Run-level counters, matches per RFC, queryability split, review load.",
    ),
    (
        "pages/2_Schema_Check.py",
        "🧾",
        "Schema Check",
        "Which checklist indicators the OpenINTEL dictionary can actually answer, and why.",
    ),
    (
        "pages/3_RFC_Checklists.py",
        "📚",
        "RFC Checklists",
        "The RFC signature database: indicators, weights, and their conditions.",
    ),
    (
        "pages/4_OpenINTEL_Data_Explorer.py",
        "🛰️",
        "OpenINTEL Data Explorer",
        "The observed signals themselves: field distributions and coverage over time.",
    ),
    (
        "pages/5_Matching_Results.py",
        "🎯",
        "Matching Results",
        "Ranked RFC candidates, their scores, and the per-signal matches behind them.",
    ),
    (
        "pages/6_Reasoning_Explorer.py",
        "🔍",
        "Reasoning Explorer",
        "Every decision opened up: conditions, timestamp check, score arithmetic.",
    ),
    (
        "pages/7_Adoption_Timeline.py",
        "📈",
        "Adoption Timeline",
        "First-seen dates and observation volume per RFC, with coverage caveats.",
    ),
    (
        "pages/8_Review_Queue.py",
        "📋",
        "Review Queue",
        "Findings that need a human, with a persisted resolution status.",
    ),
    (
        "pages/9_Export_Center.py",
        "📦",
        "Export Center",
        "Download every artefact this run produced; preview the Markdown reports.",
    ),
)

FRAMING = """
This dashboard displays the output of a deterministic matching pipeline. The
pipeline takes a database of RFC *indicators* — observable signatures such as
"a CDS record whose algorithm field is 0" — and evaluates them against
normalized OpenINTEL DNS measurements. For every observation it produces a
ranked list of **RFC candidates** together with a full reasoning trace: which
conditions passed, which failed, which fields were missing, and how the score
was arrived at.

**What this does not claim.** A ranked candidate is a statement that an
observation is *consistent with* the signature of an RFC, not that the operator
adopted that RFC, read it, or intended to implement it. Several RFCs share
observable behaviour, some indicators are explicitly flagged ambiguous, and one
field referenced by the checklist is absent from the dictionary entirely, so its
indicator can never be tested. First-seen dates are bounded by measurement
coverage: they are a lower bound on when a mechanism became *visible*, not on
when it was deployed. Anything the pipeline could not settle on its own is
routed to the review queue rather than quietly resolved.
"""


def _manifest_section(manifest: dict | None) -> None:
    """Show provenance for the run being displayed."""
    st.subheader("Run manifest")
    if not manifest:
        st.info(
            "No run_manifest.json in this output directory, so the inputs and "
            "engine behind these artefacts are unknown."
        )
        return

    top = st.columns(4)
    top[0].metric("Pipeline", str(manifest.get("pipeline", "unknown")))
    top[1].metric("Version", str(manifest.get("version", "unknown")))
    top[2].metric("Engine", str(manifest.get("engine", "unknown")))
    top[3].metric("Generated at", str(manifest.get("generated_at", "unknown")))

    left, right = st.columns(2)

    with left:
        st.markdown("**Inputs**")
        inputs = manifest.get("inputs")
        if isinstance(inputs, dict) and inputs:
            show_df(
                pd.DataFrame(
                    {"input": list(inputs), "value": [str(v) for v in inputs.values()]}
                )
            )
        else:
            st.caption("The manifest records no inputs.")

    with right:
        st.markdown("**Counts**")
        counts = manifest.get("counts")
        if isinstance(counts, dict) and counts:
            show_df(
                pd.DataFrame(
                    {"quantity": list(counts), "count": [counts[k] for k in counts]}
                )
            )
        else:
            st.caption("The manifest records no counts.")

    by_decision = manifest.get("matches_by_decision")
    by_queryability = manifest.get("indicators_by_queryability")
    if isinstance(by_decision, dict) and by_decision:
        st.markdown("**Matches by decision**")
        st.caption(
            "`no_match` traces are produced deliberately: they record why an RFC "
            "was rejected for an observation. They are excluded from ranking."
        )
        show_df(
            pd.DataFrame(
                {
                    "decision": list(by_decision),
                    "matches": [by_decision[k] for k in by_decision],
                }
            )
        )
    if isinstance(by_queryability, dict) and by_queryability:
        st.markdown("**Indicators by queryability**")
        show_df(
            pd.DataFrame(
                {
                    "queryability": list(by_queryability),
                    "indicators": [by_queryability[k] for k in by_queryability],
                }
            )
        )


def _page_index() -> None:
    st.subheader("Pages")
    st.caption(
        "Use the sidebar to navigate, or the links below. Every page reads the "
        "output directory selected in the sidebar."
    )
    left, right = st.columns(2)
    for position, (path, icon, title, purpose) in enumerate(PAGES):
        column = left if position % 2 == 0 else right
        with column:
            with st.container(border=True):
                try:
                    st.page_link(path, label=f"{title}", icon=icon)
                except Exception:  # pragma: no cover - page_link needs a real run
                    st.markdown(f"{icon} **{title}**")
                st.caption(purpose)


def main() -> None:
    page_setup(
        APP_TITLE,
        "🧭",
        subtitle=(
            "Ranked RFC candidates from OpenINTEL DNS measurements, with an "
            "auditable reason for every decision."
        ),
    )
    output_dir = sidebar_controls()
    bundle = load_bundle(output_dir)
    sidebar_status(bundle)

    st.markdown(FRAMING)
    st.divider()

    if not bundle.has_analysis:
        empty_state(
            "No analysis artefacts were found, so there is nothing to display yet.",
            output_dir=output_dir,
        )
        _page_index()
        return

    summary = bundle.summary or {}
    headline = st.columns(4)
    headline[0].metric("Observed signals", summary.get("signal_count", 0))
    headline[1].metric("Signal x RFC evaluations", summary.get("match_count", 0))
    headline[2].metric("Ranked RFC candidates", summary.get("ranked_candidate_count", 0))
    headline[3].metric("Review items", summary.get("review_item_count", 0))
    st.caption(
        f"Observation window {summary.get('date_range', 'n/a')}. "
        f"Top candidate: {summary.get('top_rfc_id') or 'n/a'} "
        f"(score {summary.get('top_rfc_score', 0.0):g})."
    )

    st.divider()
    _manifest_section(bundle.run_manifest)

    st.divider()
    _page_index()

    if bundle.warnings:
        st.divider()
        st.subheader("Load warnings")
        st.caption(
            "These come from the data layer and from the pipeline run itself. "
            "They describe gaps in what follows rather than failures of it."
        )
        for message in bundle.warnings:
            st.warning(message)


main()
