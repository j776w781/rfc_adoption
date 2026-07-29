"""Shared plumbing for every page of the RFC-adoption dashboard.

This module owns the things that must look and behave identically on all ten
pages: the output-directory selector, the cached bundle loader, the empty state,
the Plotly styling, and the colour vocabulary for decisions, severities,
confidences and queryability verdicts.

Nothing here reads an artefact file directly. Data comes exclusively from
:mod:`openintel_rfc.dashboard_data`, which is the dashboard's only data-access
layer; pages in turn take their data exclusively from this module or from that
one. Keeping the funnel narrow is what makes "add a file to the pipeline" a
one-place change rather than a ten-place change.

Colour choices are semantic and deliberately fixed:

``valid_match`` green, ``partial_match`` amber, ``timestamp_invalid`` red,
``no_match`` grey, ``ambiguous`` purple; severities high/medium/low map to
red/amber/blue. The same hue means the same thing on every chart and every
badge, so a reader never has to re-learn the legend.
"""

from __future__ import annotations

import html
import sys
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, Final

# ---- Import bootstrap ----------------------------------------------------- #
# _shared is imported by pages that have already run the bootstrap, but it is
# also imported by tooling that has not, so make it self-sufficient.
_DASHBOARD_DIR = str(Path(__file__).resolve().parent)
if _DASHBOARD_DIR not in sys.path:  # pragma: no cover - trivial path plumbing
    sys.path.insert(0, _DASHBOARD_DIR)

from _bootstrap import DASHBOARD_DIR, PROJECT_ROOT, setup  # noqa: E402

setup()

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from openintel_rfc import config  # noqa: E402
from openintel_rfc.dashboard_data import (  # noqa: E402
    REVIEW_STATUSES,
    DashboardBundle,
    available_output_dirs,
    filter_dataframe,
    load_dashboard_data,
    load_review_status,
    save_review_status,
)

__all__ = [
    "APP_TITLE",
    "CLI_HINT",
    "CONFIDENCE_COLORS",
    "CONFIDENCE_ORDER",
    "DASHBOARD_DIR",
    "DECISION_COLORS",
    "DECISION_ORDER",
    "DEFAULT_OUTPUT_DIR",
    "DOCS_DIR",
    "PROJECT_ROOT",
    "QUERYABILITY_COLORS",
    "QUERYABILITY_ORDER",
    "REVIEW_STATUSES",
    "REVIEW_STATUS_COLORS",
    "REVIEW_STATUS_ORDER",
    "SEVERITY_COLORS",
    "SEVERITY_ORDER",
    "DashboardBundle",
    "badge",
    "confidence_color",
    "date_range_slice",
    "decision_badge",
    "decision_color",
    "drop_raw_columns",
    "empty_state",
    "filter_dataframe",
    "format_condition",
    "format_timestamp",
    "format_value",
    "human_size",
    "int_like",
    "load_bundle",
    "load_review_status",
    "multiselect_filter",
    "no_rows",
    "ordered_categories",
    "page_context",
    "page_setup",
    "save_review_status",
    "severity_badge",
    "severity_color",
    "show_df",
    "show_fig",
    "sidebar_controls",
    "sidebar_status",
    "style_fig",
    "unique_values",
]


# --------------------------------------------------------------------------- #
# Identity and locations
# --------------------------------------------------------------------------- #

APP_TITLE: Final[str] = "OpenINTEL RFC-adoption matcher"

DEFAULT_OUTPUT_DIR: Final[Path] = PROJECT_ROOT / "demo_output"
DOCS_DIR: Final[Path] = PROJECT_ROOT / "docs"

#: Shown wherever the dashboard has nothing to display.
CLI_HINT: Final[str] = (
    "PYTHONPATH=src python -m openintel_rfc.cli analyze \\\n"
    "    --checklists data/rfc_checklists/dnssec_rfc_checklists.json \\\n"
    "    --dictionary data/openintel_dictionary/sample_openintel_dictionary.json \\\n"
    "    --parquet data/sample_parquet/sample_openintel.parquet \\\n"
    "    --out demo_output"
)


# --------------------------------------------------------------------------- #
# Colour vocabulary
# --------------------------------------------------------------------------- #

#: Decision -> hue. Mid-tone colours so they stay legible on the light and the
#: dark Streamlit theme alike; nothing here is near-white or near-black.
DECISION_COLORS: Final[dict[str, str]] = {
    "valid_match": "#2E9E5B",
    "partial_match": "#E1A11A",
    "timestamp_invalid": "#D64545",
    "no_match": "#8A8F98",
    "ambiguous": "#8E5BD0",
    "non_queryable": "#6B7A8F",
}

#: Order used for stacked bars and legends: strongest evidence first.
DECISION_ORDER: Final[tuple[str, ...]] = (
    "valid_match",
    "ambiguous",
    "partial_match",
    "timestamp_invalid",
    "non_queryable",
    "no_match",
)

SEVERITY_COLORS: Final[dict[str, str]] = {
    "high": "#D64545",
    "medium": "#E1A11A",
    "low": "#4C8FD8",
}
SEVERITY_ORDER: Final[tuple[str, ...]] = ("high", "medium", "low")

CONFIDENCE_COLORS: Final[dict[str, str]] = {
    "very_high": "#1F7A4D",
    "high": "#2E9E5B",
    "medium": "#E1A11A",
    "low": "#4C8FD8",
    "none": "#8A8F98",
}
CONFIDENCE_ORDER: Final[tuple[str, ...]] = ("very_high", "high", "medium", "low", "none")

QUERYABILITY_COLORS: Final[dict[str, str]] = {
    "queryable": "#2E9E5B",
    "partially_queryable": "#E1A11A",
    "ambiguous": "#8E5BD0",
    "non_queryable": "#D64545",
}
QUERYABILITY_ORDER: Final[tuple[str, ...]] = (
    "queryable",
    "partially_queryable",
    "ambiguous",
    "non_queryable",
)

REVIEW_STATUS_COLORS: Final[dict[str, str]] = {
    "unresolved": "#8A8F98",
    "accepted": "#2E9E5B",
    "rejected": "#D64545",
    "needs_follow_up": "#E1A11A",
}
REVIEW_STATUS_ORDER: Final[tuple[str, ...]] = (
    "unresolved",
    "accepted",
    "rejected",
    "needs_follow_up",
)

#: Fallback palette for non-semantic categories (RFC ids, zones, rr_types).
CATEGORICAL_COLORS: Final[tuple[str, ...]] = (
    "#4C78A8",
    "#F58518",
    "#54A24B",
    "#B279A2",
    "#E45756",
    "#72B7B2",
    "#EECA3B",
    "#9D755D",
    "#FF9DA6",
    "#79706E",
)

_NEUTRAL: Final[str] = "#8A8F98"


def decision_color(decision: Any) -> str:
    """Hue for one decision value; neutral grey for anything unrecognised."""
    return DECISION_COLORS.get(str(decision), _NEUTRAL)


def severity_color(severity: Any) -> str:
    return SEVERITY_COLORS.get(str(severity), _NEUTRAL)


def confidence_color(confidence: Any) -> str:
    return CONFIDENCE_COLORS.get(str(confidence), _NEUTRAL)


def badge(label: Any, color: str) -> str:
    """An inline coloured chip, as an HTML fragment for ``st.markdown``.

    White text on a mid-tone fill reads on both Streamlit themes, which a
    coloured *foreground* would not.
    """
    return (
        f"<span style='background-color:{color};color:#FFFFFF;padding:2px 9px;"
        "border-radius:10px;font-size:0.85em;font-weight:600;"
        f"white-space:nowrap;'>{html.escape(str(label))}</span>"
    )


def decision_badge(decision: Any) -> str:
    return badge(decision, decision_color(decision))


def severity_badge(severity: Any) -> str:
    return badge(severity, severity_color(severity))


# --------------------------------------------------------------------------- #
# Page scaffolding
# --------------------------------------------------------------------------- #


def page_setup(title: str, icon: str, *, subtitle: str | None = None) -> None:
    """``st.set_page_config`` plus the page heading.

    Must be the first Streamlit call in a page: ``set_page_config`` raises if
    anything has already written to the app.
    """
    st.set_page_config(page_title=f"{title} — {APP_TITLE}", page_icon=icon, layout="wide")
    st.title(title)
    if subtitle:
        st.caption(subtitle)


# --------------------------------------------------------------------------- #
# Output-directory selection
# --------------------------------------------------------------------------- #

_OUTPUT_DIR_KEY: Final[str] = "output_dir"
_PICKER_KEY: Final[str] = "_output_dir_picker"
_TEXT_KEY: Final[str] = "_output_dir_text"


def _default_output_dir() -> str:
    """``demo_output`` when it exists, otherwise the first discovered run."""
    if DEFAULT_OUTPUT_DIR.is_dir():
        return str(DEFAULT_OUTPUT_DIR)
    discovered = available_output_dirs(PROJECT_ROOT)
    return str(discovered[0]) if discovered else str(DEFAULT_OUTPUT_DIR)


def _apply_picker() -> None:
    chosen = st.session_state.get(_PICKER_KEY) or _default_output_dir()
    st.session_state[_OUTPUT_DIR_KEY] = chosen
    st.session_state[_TEXT_KEY] = chosen


def _apply_text() -> None:
    typed = str(st.session_state.get(_TEXT_KEY, "")).strip()
    st.session_state[_OUTPUT_DIR_KEY] = typed or _default_output_dir()


def sidebar_controls() -> Path:
    """Render the data-source sidebar and return the selected output directory.

    The choice lives in ``st.session_state`` so it survives navigation between
    pages: switching page must not silently switch back to ``demo_output``.
    """
    st.session_state.setdefault(_OUTPUT_DIR_KEY, _default_output_dir())
    current = str(st.session_state[_OUTPUT_DIR_KEY])
    st.session_state.setdefault(_TEXT_KEY, current)

    with st.sidebar:
        st.subheader("Pipeline output")
        discovered = [str(path) for path in available_output_dirs(PROJECT_ROOT)]
        if discovered:
            options = discovered if current in discovered else [current, *discovered]
            st.selectbox(
                "Discovered runs",
                options=options,
                index=options.index(current),
                key=_PICKER_KEY,
                on_change=_apply_picker,
                help="Directories under the project root that contain pipeline artefacts.",
            )
        else:
            st.caption("No run directories discovered under the project root.")

        st.text_input(
            "Output directory",
            key=_TEXT_KEY,
            on_change=_apply_text,
            help="Any path holding artefacts written by `openintel-rfc analyze`.",
        )

        selected = Path(str(st.session_state[_OUTPUT_DIR_KEY]))
        if selected.is_dir():
            st.caption(f"Reading {selected}")
        else:
            st.warning(f"{selected} does not exist yet.")

        if st.button("Reload from disk", width="stretch"):
            st.cache_data.clear()
            st.rerun()

    return selected


# --------------------------------------------------------------------------- #
# Cached bundle loading
# --------------------------------------------------------------------------- #

#: Reviewer annotations are dashboard-owned state, not pipeline output. Leaving
#: them out of the cache key means saving a review decision does not force a
#: full re-read of the multi-megabyte trace and match artefacts.
_SIGNATURE_EXCLUDED: Final[frozenset[str]] = frozenset(
    {config.OUTPUT_FILES["review_queue_status"]}
)


def _stat_entry(path: Path) -> tuple[str, int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return (path.name, int(stat.st_mtime_ns), int(stat.st_size))


def _directory_signature(output_dir: Path) -> tuple[tuple[str, int, int], ...]:
    """Fingerprint of every artefact plus the checklist / dictionary inputs.

    Re-running the pipeline rewrites files, which changes mtimes and sizes,
    which changes this tuple, which invalidates ``st.cache_data``. The user
    never has to remember to press a refresh button.
    """
    entries: list[tuple[str, int, int]] = []
    for name in sorted(set(config.OUTPUT_FILES.values())):
        if name in _SIGNATURE_EXCLUDED:
            continue
        entry = _stat_entry(output_dir / name)
        if entry is not None:
            entries.append(entry)
    for path in (
        config.DEFAULT_CHECKLIST_PATH,
        config.DEFAULT_DICTIONARY_PATH,
        config.DEFAULT_SURVEY_PATH,
    ):
        entry = _stat_entry(path)
        if entry is not None:
            entries.append(entry)
    return tuple(entries)


@st.cache_data(show_spinner="Loading pipeline output...")
def _load_bundle_cached(
    output_dir: str, signature: tuple[tuple[str, int, int], ...]
) -> DashboardBundle:
    """Cache shim. ``signature`` is unused inside but is part of the cache key."""
    del signature  # only present so a changed artefact invalidates the cache
    return load_dashboard_data(output_dir)


def load_bundle(output_dir: str | Path) -> DashboardBundle:
    """Load (or reuse) the bundle for ``output_dir``."""
    directory = Path(output_dir)
    return _load_bundle_cached(str(directory), _directory_signature(directory))


def sidebar_status(bundle: DashboardBundle) -> None:
    """Run provenance and load warnings, shown identically on every page."""
    summary = bundle.summary or {}
    with st.sidebar:
        st.divider()
        st.subheader("Run")
        generated = summary.get("generated_at")
        st.caption(f"Generated: {generated}" if generated else "Generated: unknown")
        st.caption(f"Observation window: {summary.get('date_range', 'n/a')}")
        left, right = st.columns(2)
        left.metric("Signals", summary.get("signal_count", 0))
        right.metric("Matches", summary.get("match_count", 0))
        left.metric("Ranked RFCs", summary.get("ranked_candidate_count", 0))
        right.metric("Review items", summary.get("review_item_count", 0))
        if bundle.warnings:
            with st.expander(f"Load warnings ({len(bundle.warnings)})"):
                for message in bundle.warnings:
                    st.caption(f"- {message}")


def page_context(
    title: str, icon: str, *, subtitle: str | None = None
) -> tuple[Path, DashboardBundle]:
    """The three lines every page needs: config, sidebar, data.

    Returns the selected output directory and the loaded bundle.
    """
    page_setup(title, icon, subtitle=subtitle)
    output_dir = sidebar_controls()
    bundle = load_bundle(output_dir)
    sidebar_status(bundle)
    return output_dir, bundle


# --------------------------------------------------------------------------- #
# Empty states
# --------------------------------------------------------------------------- #


def empty_state(message: str, *, output_dir: Path | None = None) -> None:
    """The "no data yet" panel: what is missing and the command that fixes it."""
    st.warning(message)
    if output_dir is not None:
        st.caption(f"Looked in: {output_dir}")
    st.markdown("Run the pipeline from the project root, then reload this page:")
    st.code(CLI_HINT, language="bash")


def no_rows(message: str) -> None:
    """Explain an empty *filtered* view, which is not the same as no data."""
    st.info(message)


# --------------------------------------------------------------------------- #
# Formatting helpers
# --------------------------------------------------------------------------- #


def format_timestamp(value: Any, *, date_only: bool = False) -> str:
    """ISO rendering that tolerates ``NaT``, ``None`` and plain strings."""
    if value is None:
        return "n/a"
    try:
        stamp = pd.to_datetime(value, errors="coerce")
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return str(value)
    if stamp is None or pd.isna(stamp):
        return "n/a"
    if isinstance(stamp, datetime):
        return stamp.date().isoformat() if date_only else stamp.isoformat(sep=" ")
    return str(stamp)  # pragma: no cover - defensive


def format_value(value: Any) -> str:
    """Render a condition value the way the checklist reads it.

    ``[CDS, CDNSKEY]`` rather than ``['CDS', 'CDNSKEY']``; ``0`` rather than
    ``0.0``. The checklist is written by humans and should read back that way.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(format_value(item) for item in value) + "]"
    return str(value)


def format_condition(condition: Mapping[str, Any]) -> str:
    """One condition as prose-ish code: ``rr_type in [CDS, CDNSKEY]``."""
    field = condition.get("field", "?")
    op = condition.get("op", "?")
    if op == "exists":
        return f"{field} exists"
    value = condition.get("value", condition.get("expected"))
    return f"{field} {op} {format_value(value)}"


def human_size(num_bytes: int | float | None) -> str:
    """Byte count as a short human string."""
    if num_bytes is None:
        return "n/a"
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"  # pragma: no cover - unreachable


def int_like(series: pd.Series) -> pd.Series:
    """Show ``algorithm`` as 8, not 8.0, while keeping missing values missing."""
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.astype("Int64")


def drop_raw_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Hide the ``<column>_raw`` list mirrors that ``dashboard_data`` attaches."""
    if df is None:
        return df
    keep = [name for name in df.columns if not str(name).endswith("_raw")]
    return df[keep]


def unique_values(series: pd.Series | None) -> list[str]:
    """Sorted distinct values of a column, as display strings.

    Numeric columns sort numerically (2, 8, 13) rather than lexically
    (13, 2, 8), which matters for DNSSEC algorithm numbers.
    """
    if series is None or len(series) == 0:
        return []
    cleaned = series.dropna()
    if cleaned.empty:
        return []
    numeric = pd.to_numeric(cleaned, errors="coerce")
    if not numeric.isna().any():
        return [format_value(value) for value in sorted(set(numeric.tolist()))]
    return sorted({str(value) for value in cleaned.tolist()})


# --------------------------------------------------------------------------- #
# Filter widgets
# --------------------------------------------------------------------------- #


def multiselect_filter(
    label: str,
    series: pd.Series | None,
    *,
    key: str,
    default: Sequence[str] | None = None,
    help: str | None = None,
    container: Any = None,
) -> list[str]:
    """A multiselect whose empty state means "no filter".

    Matches :func:`openintel_rfc.dashboard_data.filter_dataframe`, which treats
    an empty collection as "do not filter on this column".
    """
    target = container if container is not None else st
    options = unique_values(series)
    if not options:
        target.caption(f"{label}: no values available")
        return []
    chosen = [value for value in (default or []) if value in options]
    return list(
        target.multiselect(
            label,
            options=options,
            default=chosen,
            key=key,
            help=help or "Leave empty to include everything.",
        )
    )


def date_range_slice(
    label: str,
    series: pd.Series | None,
    *,
    key: str,
    container: Any = None,
) -> slice | None:
    """A date-range picker returning an inclusive ``slice`` for filtering.

    ``None`` means "no usable range", which callers pass straight through to
    ``filter_dataframe`` as "do not filter".
    """
    target = container if container is not None else st
    if series is None or len(series) == 0:
        return None
    stamps = pd.to_datetime(series, errors="coerce").dropna()
    if stamps.empty:
        return None
    low, high = stamps.min().date(), stamps.max().date()
    if low == high:
        target.caption(f"{label}: single day ({low.isoformat()})")
        return None
    picked = target.date_input(
        label, value=(low, high), min_value=low, max_value=high, key=key
    )
    if isinstance(picked, (tuple, list)):
        if len(picked) != 2:
            # Mid-selection: the user has clicked one end of the range only.
            return None
        start, end = picked
    else:  # pragma: no cover - Streamlit returns a bare date only for single mode
        start = end = picked
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    return slice(start_ts, end_ts)


# --------------------------------------------------------------------------- #
# Tables and charts
# --------------------------------------------------------------------------- #


def show_df(
    df: pd.DataFrame,
    *,
    columns: Sequence[str] | None = None,
    height: int | None = None,
    column_config: Mapping[str, Any] | None = None,
    hide_index: bool = True,
    key: str | None = None,
    empty_message: str | None = None,
) -> None:
    """Render a DataFrame consistently: no ``_raw`` columns, full width."""
    if df is None:
        no_rows(empty_message or "Nothing to show.")
        return
    frame = drop_raw_columns(df)
    if columns:
        wanted = [name for name in columns if name in frame.columns]
        if wanted:
            frame = frame[wanted]
    if frame.empty and empty_message:
        no_rows(empty_message)
        return
    kwargs: dict[str, Any] = {"use_container_width": True, "hide_index": hide_index}
    if height is not None:
        kwargs["height"] = height
    if column_config is not None:
        kwargs["column_config"] = dict(column_config)
    if key is not None:
        kwargs["key"] = key
    st.dataframe(frame, **kwargs)


def style_fig(fig: go.Figure, *, height: int | None = None, showlegend: bool | None = None) -> go.Figure:
    """Apply the shared chart styling.

    Backgrounds are transparent and no font colour is set, so Streamlit's own
    Plotly theme supplies text and grid colours that match the active light or
    dark theme. Hardcoding a white paper background here is what makes charts
    unreadable for dark-theme users, so it is deliberately not done.
    """
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=48, b=8),
        colorway=list(CATEGORICAL_COLORS),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=""),
        hoverlabel=dict(font_size=12),
    )
    if height is not None:
        fig.update_layout(height=height)
    if showlegend is not None:
        fig.update_layout(showlegend=showlegend)
    return fig


def show_fig(fig: go.Figure, *, height: int | None = None, key: str | None = None) -> None:
    """Style and render a Plotly figure at full container width."""
    styled = style_fig(fig, height=height)
    kwargs: dict[str, Any] = {"use_container_width": True}
    if key is not None:
        kwargs["key"] = key
    st.plotly_chart(styled, **kwargs)


def ordered_categories(values: Iterable[Any], order: Sequence[str]) -> list[str]:
    """Categories present in ``values``, in the canonical ``order`` first."""
    present = {str(value) for value in values if value is not None and not pd.isna(value)}
    ranked = [name for name in order if name in present]
    ranked.extend(sorted(present - set(ranked)))
    return ranked
