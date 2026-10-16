"""Timeline plot: DS/DNSKEY/RRSIG prevalence over time, RFC dates marked.

Reads the per-(tld, month) table ``prevalence.rollup_tld_month_prevalence``
produces for one TLD and draws a connected line per record type (the actual
monthly values -- no fitting, unlike ``segmented_regression``), then overlays
a vertical line for every RFC publication date (from the project's RFC
checklist, ``openintel_rfc.checklist_loader``) that falls within the plotted
date range. RFCs published in the same month are combined onto one line/label
rather than drawn on top of each other.

Event categories (RFCs today; software releases and CVEs are meant to join
later) each get one fixed color from EVENT_COLORS, so a reader can tell "this
is an RFC" from "this is a CVE" at a glance, however many categories
eventually overlay onto the same timeline.

Uses a real date axis, not the categorical string-month axis
``segmented_regression`` uses -- that one can get away with it only because it
requires a gap-free series first. This plot has no such requirement, so an
RFC date has to be placeable (and a gap has to be visually a gap) regardless
of whether the exact month it falls in has an observed data point.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Sequence

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from openintel_rfc import config
from openintel_rfc.checklist_loader import load_checklist_db
from openintel_rfc.utils import PipelineError

__all__ = ["DEFAULT_METRICS", "EVENT_COLORS", "load_rfc_events", "plot_tld_timeline"]

DEFAULT_METRICS: tuple[str, ...] = ("ds_prevalence", "dnskey_prevalence", "rrsig_prevalence")

#: One fixed color per event category. Keep RFCs on this exact entry so later
#: categories (software releases, CVEs) can each get their own without ever
#: touching this one.
EVENT_COLORS: dict[str, str] = {
    "rfc": "tab:red",
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


def plot_tld_timeline(
    input_path: Path | str,
    tld: str,
    *,
    metrics: Sequence[str] = DEFAULT_METRICS,
    checklist_path: Path | str | None = None,
    out_path: Path | str | None = None,
) -> Path:
    """Plot DS/DNSKEY/RRSIG prevalence over time for one TLD, RFC dates marked."""
    df = pd.read_parquet(input_path)
    tld_df = df[df["tld"] == tld].copy()
    if tld_df.empty:
        raise PipelineError(f"No rows for tld={tld!r} in {input_path}")

    tld_df["month"] = pd.PeriodIndex(tld_df["month"], freq="M").to_timestamp()
    tld_df = tld_df.sort_values("month").reset_index(drop=True)

    events = [
        (month, label)
        for month, label in load_rfc_events(checklist_path)
        if tld_df["month"].min() <= month <= tld_df["month"].max()
    ]

    metrics = list(metrics)
    fig, axes = plt.subplots(len(metrics), 1, figsize=(11, 3 * len(metrics)), sharex=True)
    if len(metrics) == 1:
        axes = [axes]

    for ax, metric in zip(axes, metrics):
        ax.plot(tld_df["month"], tld_df[metric], "o-", markersize=3, linewidth=1, color="tab:blue")
        ax.set_title(f"{tld}: {metric}")
        ax.set_ylabel("prevalence")
        bottom, top = ax.get_ylim()
        # Labels cycle through a few heights so RFCs that land close together
        # in time (close enough for their rotated text to overlap) don't get
        # stacked at the same height -- not true collision detection, just
        # enough to keep a dense stretch of RFCs legible.
        height_levels = [top, top - 0.12 * (top - bottom), top - 0.24 * (top - bottom)]
        for i, (month, label) in enumerate(events):
            ax.axvline(month, color=EVENT_COLORS["rfc"], linestyle="--", linewidth=0.8, alpha=0.7)
            ax.text(
                month, height_levels[i % len(height_levels)], label, rotation=90, fontsize=6,
                color=EVENT_COLORS["rfc"], ha="right", va="top",
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
