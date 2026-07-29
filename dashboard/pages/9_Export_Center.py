"""Export Center: download what this run produced.

Everything the pipeline writes is offered here with its size and modification
time, so a reader can tell whether the CSV they are about to download came from
the same run as the JSON. Artefacts that do not exist are listed as missing,
with the command that would produce them, rather than being hidden or raising.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_DASHBOARD_DIR = str(Path(__file__).resolve().parents[1])
if _DASHBOARD_DIR not in sys.path:
    sys.path.insert(0, _DASHBOARD_DIR)

from _bootstrap import setup  # noqa: E402

setup()

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from _shared import (  # noqa: E402
    DOCS_DIR,
    human_size,
    load_bundle,
    no_rows,
    page_setup,
    show_df,
    sidebar_controls,
    sidebar_status,
)

from openintel_rfc import config  # noqa: E402

_MIME_TYPES = {
    ".json": "application/json",
    ".csv": "text/csv",
    ".md": "text/markdown",
}


@dataclass(frozen=True)
class Artefact:
    """One downloadable file and the command that produces it."""

    label: str
    path: Path
    producer: str
    note: str = ""


#: ``config.OUTPUT_FILES`` keys grouped the way a reader thinks about them.
_GROUPS: tuple[tuple[str, str, tuple[tuple[str, str], ...]], ...] = (
    (
        "Matching artefacts (JSON)",
        "openintel-rfc analyze",
        (
            ("observed_signals", "Normalized observations extracted from Parquet."),
            ("rfc_matches", "Every signal x RFC evaluation with its score breakdown."),
            ("ranked_candidates", "RFCs aggregated across signals and ranked."),
            ("reasoning_traces", "Full decision records, including failed conditions."),
            ("review_queue", "Findings routed to a human."),
            ("adoption_timeline", "First-seen dates and bucketed counts per RFC."),
            ("run_manifest", "Inputs, engine, counts and warnings for the run."),
        ),
    ),
    (
        "Schema check (JSON)",
        "openintel-rfc schema-check",
        (
            ("schema_check_json", "Queryability verdict and reasoning per indicator."),
            ("queryable_indicators", "The subset that can be evaluated."),
            ("non_queryable_indicators", "The subset that cannot, and why."),
        ),
    ),
    (
        "Tabular exports (CSV)",
        "openintel-rfc analyze / schema-check",
        (
            ("rfc_matches_csv", ""),
            ("reasoning_traces_csv", ""),
            ("review_queue_csv", ""),
            ("adoption_timeline_csv", ""),
            ("observed_signals_csv", ""),
            ("schema_check_csv", ""),
        ),
    ),
    (
        "Reports (Markdown)",
        "openintel-rfc analyze / schema-check",
        (
            ("report_md", "Narrative report for the whole run."),
            ("schema_check_report_md", "Narrative report for the schema cross-check."),
        ),
    ),
    (
        "Dashboard state",
        "written by the Review Queue page",
        (("review_queue_status", "Reviewer resolutions; not pipeline output."),),
    ),
)


@st.cache_data(show_spinner=False)
def _read_bytes(path: str, mtime_ns: int, size: int) -> bytes:
    """Read a file for download, cached on its identity so reruns are cheap."""
    del mtime_ns, size  # part of the cache key only
    return Path(path).read_bytes()


@st.cache_data(show_spinner=False)
def _read_text(path: str, mtime_ns: int, size: int) -> str:
    del mtime_ns, size
    return Path(path).read_text(encoding="utf-8", errors="replace")


def _stat(path: Path) -> tuple[int, int] | None:
    try:
        info = path.stat()
    except OSError:
        return None
    return int(info.st_mtime_ns), int(info.st_size)


def _artefacts(output_dir: Path) -> list[tuple[str, str, list[Artefact]]]:
    groups: list[tuple[str, str, list[Artefact]]] = []
    for title, producer, keys in _GROUPS:
        entries: list[Artefact] = []
        for key, note in keys:
            name = config.OUTPUT_FILES.get(key)
            if name is None:  # pragma: no cover - config drift guard
                continue
            entries.append(Artefact(name, output_dir / name, producer, note))
        groups.append((title, producer, entries))

    docs = [
        Artefact(
            "open_source_tool_survey.md",
            DOCS_DIR / "open_source_tool_survey.md",
            "openintel-rfc tool-survey",
            "Survey of the open-source tools considered for this pipeline.",
        ),
        Artefact(
            "architecture.md",
            DOCS_DIR / "architecture.md",
            "written by hand",
            "How the modules fit together.",
        ),
    ]
    groups.append(("Project documentation", "docs/", docs))
    return groups


def _inventory(groups: list[tuple[str, str, list[Artefact]]]) -> pd.DataFrame:
    rows = []
    for title, _producer, entries in groups:
        for artefact in entries:
            info = _stat(artefact.path)
            rows.append(
                {
                    "group": title,
                    "file": artefact.label,
                    "present": info is not None,
                    "size": human_size(info[1]) if info else "-",
                    "modified": (
                        datetime.fromtimestamp(info[0] / 1_000_000_000).isoformat(
                            sep=" ", timespec="seconds"
                        )
                        if info
                        else "-"
                    ),
                    "path": str(artefact.path),
                }
            )
    return pd.DataFrame(rows)


def _render_artefact(artefact: Artefact) -> None:
    info = _stat(artefact.path)
    columns = st.columns([3, 1, 2, 2])
    if info is None:
        columns[0].markdown(f":grey[{artefact.label}]")
        columns[1].markdown(":grey[missing]")
        columns[2].markdown(":grey[-]")
        columns[3].caption(f"Produced by `{artefact.producer}`.")
        return

    mtime_ns, size = info
    columns[0].markdown(f"**{artefact.label}**")
    columns[1].markdown(human_size(size))
    columns[2].caption(
        datetime.fromtimestamp(mtime_ns / 1_000_000_000).isoformat(sep=" ", timespec="seconds")
    )
    with columns[3]:
        st.download_button(
            "Download",
            data=_read_bytes(str(artefact.path), mtime_ns, size),
            file_name=artefact.label,
            mime=_MIME_TYPES.get(artefact.path.suffix, "application/octet-stream"),
            # The full path is unique per artefact, so widget keys cannot collide.
            key=f"download::{artefact.path}",
        )
    if artefact.note:
        st.caption(artefact.note)

    if artefact.path.suffix == ".md":
        with st.expander(f"Preview {artefact.label}"):
            st.markdown(_read_text(str(artefact.path), mtime_ns, size))


def main() -> None:
    page_setup(
        "Export Center",
        "📦",
        subtitle="Every artefact this run wrote, with its size, age and a download link.",
    )
    output_dir = sidebar_controls()
    bundle = load_bundle(output_dir)
    sidebar_status(bundle)

    groups = _artefacts(output_dir)
    inventory = _inventory(groups)

    present = int(inventory["present"].sum())
    header = st.columns(3)
    header[0].metric("Files present", f"{present} of {len(inventory)}")
    header[1].metric("Output directory", output_dir.name or str(output_dir))
    header[2].metric(
        "Run generated at", str((bundle.summary or {}).get("generated_at") or "unknown")
    )

    if present == 0:
        st.warning(
            f"No artefacts exist under {output_dir}. Run the pipeline first; "
            "the file list below shows which command produces what."
        )

    st.divider()
    st.subheader("Inventory")
    show_df(inventory)
    st.caption(
        "Modification times let you tell a stale CSV from the JSON of the "
        "current run. Files written by different commands can legitimately "
        "differ: `schema-check` artefacts are older than `analyze` artefacts "
        "when only the latter was re-run."
    )

    for title, producer, entries in groups:
        st.divider()
        st.subheader(title)
        st.caption(f"Produced by `{producer}`.")
        missing = [entry for entry in entries if _stat(entry.path) is None]
        for artefact in entries:
            _render_artefact(artefact)
        if missing:
            st.caption(
                "Greyed out above: "
                + ", ".join(entry.label for entry in missing)
                + f". Run `{producer}` to create them."
            )

    if not any(
        _stat(entry.path) is not None for _, _, entries in groups for entry in entries
    ):
        no_rows("Nothing to download yet.")


main()
