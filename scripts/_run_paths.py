"""Where the monthly timelines live, so a full server run can replace the local one.

Every analysis script reads two parquet files:

    <server run>/timeline_monthly.parquet   forward TLDs (basis=zonefile) + five RIRs (basis=reverse)
    <panel run>/timeline_monthly.parquet    the strict reverse panel, source _pooled-afrinic-arin

By default they are the runs committed with this repository (out/server_run, out/panel_run).
To analyse a different run -- e.g. the full OpenINTEL corpus on the server, built by
scripts/run_openintel_full.py from a main drive plus a spill drive -- set

    DNSSEC_SERVER_RUN=/path/to/run/server
    DNSSEC_PANEL_RUN=/path/to/run/panel

(directories or the parquet files themselves). Relative paths resolve against the repository.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER_ENV = "DNSSEC_SERVER_RUN"
PANEL_ENV = "DNSSEC_PANEL_RUN"
DEFAULT_SERVER = ROOT / "out" / "server_run"
DEFAULT_PANEL = ROOT / "out" / "panel_run"

#: Forward TLDs this project has charted so far, in their established order and colours.
#: Any other zonefile source a run contains is appended after these, never dropped.
KNOWN_FORWARD = ["se", "nu", "ch", "li", "ee", "gov", "fed.us"]


def _resolve(env: str, default: Path) -> Path:
    raw = os.environ.get(env, "").strip()
    p = Path(raw) if raw else default
    if not p.is_absolute():
        p = ROOT / p
    return p / "timeline_monthly.parquet" if p.suffix != ".parquet" else p


def server_timeline() -> Path:
    """The server run's timeline parquet (forward + per-RIR reverse)."""
    return _resolve(SERVER_ENV, DEFAULT_SERVER)


def panel_timeline() -> Path:
    """The strict reverse panel's timeline parquet."""
    return _resolve(PANEL_ENV, DEFAULT_PANEL)


def forward_sources(timeline) -> list[str]:
    """Every forward (zonefile) source in a timeline frame: known TLDs first, then the rest sorted."""
    present = set(timeline.loc[timeline.basis == "zonefile", "source"].unique())
    return [s for s in KNOWN_FORWARD if s in present] + sorted(present - set(KNOWN_FORWARD))


def describe() -> str:
    """One line for logs: which runs are being read."""
    return f"server run {server_timeline()} | panel run {panel_timeline()}"


def inputs_record() -> dict:
    """Which timeline files an analysis read: repo-relative when inside the repository, so the
    record is stable across machines, absolute otherwise (e.g. a full server run)."""
    out = {}
    for key, p in (("server_run", server_timeline()), ("panel_run", panel_timeline())):
        try:
            out[key] = p.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            out[key] = p.resolve().as_posix()
    return out
