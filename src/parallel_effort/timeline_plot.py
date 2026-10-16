"""Timeline plot: DS/DNSKEY/RRSIG prevalence over time, RFC/software dates marked.

Reads the per-(tld, month) table ``prevalence.rollup_tld_month_prevalence``
produces for one TLD and draws a connected line per record type (the actual
monthly values -- no fitting, unlike ``segmented_regression``), then overlays
a vertical line for every event that falls within the plotted date range:

* every RFC publication date (from the project's RFC checklist,
  ``openintel_rfc.checklist_loader``) -- RFCs sharing a publication month are
  combined onto one line/label rather than drawn on top of each other;
* every ``data/software/software_support.json`` entry -- the date each DNS
  implementation first supported/signed/validated a capability tied to one of
  those RFCs. Entries sharing an exact release date are likewise combined.

Event categories each get one fixed color from EVENT_COLORS, so a reader can
tell "this is an RFC" from "this is a CVE" at a glance, however many
categories eventually overlay onto the same timeline (CVEs are meant to join
later). Labels from every category share one height-staggering pass so two
events close in time -- whichever categories they belong to -- don't overlap.

Uses a real date axis, not the categorical string-month axis
``segmented_regression`` uses -- that one can get away with it only because it
requires a gap-free series first. This plot has no such requirement, so an
event date has to be placeable (and a gap has to be visually a gap) regardless
of whether the exact month it falls in has an observed data point.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Sequence

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from openintel_rfc import config
from openintel_rfc.checklist_loader import load_checklist_db
from openintel_rfc.utils import PipelineError

__all__ = [
    "DEFAULT_METRICS",
    "DEFAULT_SOFTWARE_SUPPORT_PATH",
    "EVENT_COLORS",
    "load_rfc_events",
    "load_software_support_events",
    "plot_tld_timeline",
]

DEFAULT_METRICS: tuple[str, ...] = ("ds_prevalence", "dnskey_prevalence", "rrsig_prevalence")

#: data/software/software_support.json -- not an openintel_rfc file, so (unlike
#: DEFAULT_CHECKLIST_PATH) its default lives here rather than in that package's
#: config.
DEFAULT_SOFTWARE_SUPPORT_PATH: Path = (
    config.PROJECT_ROOT / "data" / "software" / "software_support.json"
)

#: One fixed color per event category. Keep existing entries where they are so
#: a category already in use never changes color just because another one was
#: added.
EVENT_COLORS: dict[str, str] = {
    "rfc": "tab:red",
    "software_support": "tab:purple",
}


def _rfc_sort_key(rfc_id: str) -> int:
    try:
        return int(rfc_id.rsplit(" ", 1)[-1])
    except ValueError:
        return 0


def load_rfc_events(checklist_path: Path | str | None = None) -> list[tuple[pd.Timestamp, str]]:
    """Every RFC's (publication month, label), one entry per distinct month.

    RFCs sharing a publication month (three triples do: 4033/4034/4035,
    7583/7671/7672, 9904/9905/9906) are combined into one label
    ("RFC 4033/4034/4035") instead of three overlapping lines at one date.
    """
    db = load_checklist_db(checklist_path or config.DEFAULT_CHECKLIST_PATH)
    by_month: dict[pd.Timestamp, list[str]] = defaultdict(list)
    for entry in db.rfcs:
        month = pd.Timestamp(entry.publication_date).replace(day=1)
        by_month[month].append(entry.rfc_id)
    return [
        (month, "/".join(sorted(ids, key=_rfc_sort_key)))
        for month, ids in sorted(by_month.items())
    ]


def load_software_support_events(
    path: Path | str | None = None,
) -> list[tuple[pd.Timestamp, str]]:
    """Every software_support.json entry's (release date, label).

    Entries that share an exact release date (three groups do, e.g. unbound
    0.7.1 on 2009-11-23 both gaining algorithm-12 validation and trust-anchor
    rollover on the same day) are combined onto one label rather than drawn as
    separate overlapping lines.
    """
    file_path = Path(path) if path else DEFAULT_SOFTWARE_SUPPORT_PATH
    if not file_path.is_file():
        raise PipelineError(f"Software support file not found: {file_path}")
    payload = json.loads(file_path.read_text(encoding="utf-8"))

    by_date: dict[pd.Timestamp, list[str]] = defaultdict(list)
    for entry in payload.get("support", []):
        day = pd.Timestamp(entry["released"])
        label = f"{entry['implementation']} {entry['capability']} {entry['observable']}"
        by_date[day].append(label)
    return [(day, "; ".join(labels)) for day, labels in sorted(by_date.items())]


def plot_tld_timeline(
    input_path: Path | str,
    tld: str,
    *,
    metrics: Sequence[str] = DEFAULT_METRICS,
    checklist_path: Path | str | None = None,
    software_support_path: Path | str | None = None,
    out_path: Path | str | None = None,
) -> Path:
    """Plot DS/DNSKEY/RRSIG prevalence over time for one TLD, events marked."""
    df = pd.read_parquet(input_path)
    tld_df = df[df["tld"] == tld].copy()
    if tld_df.empty:
        raise PipelineError(f"No rows for tld={tld!r} in {input_path}")

    tld_df["month"] = pd.PeriodIndex(tld_df["month"], freq="M").to_timestamp()
    tld_df = tld_df.sort_values("month").reset_index(drop=True)
    window_start, window_end = tld_df["month"].min(), tld_df["month"].max()

    # One combined, time-sorted list across every category, so the height
    # staggering below (which exists to keep close-together labels legible)
    # sees all of them together rather than restarting per category.
    categorized: list[tuple[pd.Timestamp, str, str]] = [
        (when, label, "rfc")
        for when, label in load_rfc_events(checklist_path)
        if window_start <= when <= window_end
    ] + [
        (when, label, "software_support")
        for when, label in load_software_support_events(software_support_path)
        if window_start <= when <= window_end
    ]
    categorized.sort(key=lambda item: item[0])

    metrics = list(metrics)
    fig, axes = plt.subplots(len(metrics), 1, figsize=(11, 3 * len(metrics)), sharex=True)
    if len(metrics) == 1:
        axes = [axes]

    for ax, metric in zip(axes, metrics):
        ax.plot(tld_df["month"], tld_df[metric], "o-", markersize=3, linewidth=1, color="tab:blue")
        ax.set_title(f"{tld}: {metric}")
        ax.set_ylabel("prevalence")
        bottom, top = ax.get_ylim()
        # Labels cycle through a few heights so events landing close together
        # in time (close enough for their rotated text to overlap) don't get
        # stacked at the same height -- not true collision detection, just
        # enough to keep a dense stretch legible.
        height_levels = [top, top - 0.12 * (top - bottom), top - 0.24 * (top - bottom)]
        for i, (when, label, category) in enumerate(categorized):
            color = EVENT_COLORS[category]
            ax.axvline(when, color=color, linestyle="--", linewidth=0.8, alpha=0.7)
            ax.text(
                when, height_levels[i % len(height_levels)], label, rotation=90, fontsize=6,
                color=color, ha="right", va="top",
            )

    axes[-1].set_xlabel("month")
    # Explicit month ticks instead of matplotlib's default (which collapses to
    # bare years over a long span). The interval scales with the span so a
    # multi-decade plot still gets month-labelled ticks without cramming in
    # one per calendar month.
    span_months = max(len(tld_df), 1)
    interval = max(1, round(span_months / 20))
    for ax in axes:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=interval))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    plt.tight_layout()

    out_path = Path(out_path) if out_path else Path(f"{tld}_timeline.png")
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path
