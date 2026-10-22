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
* every ``data/software/distro_ships.json`` "ships" entry -- when a major OS
  release (Ubuntu/Debian/RHEL) shipped which DNS software version. A distinct
  signal from software_support: "upstream could do it" vs. "an operator's
  `apt upgrade` actually delivered it," which this project's own data shows
  can be years apart.
* every CVE in ``data/software/cve_inventory.json`` at or above
  ``cve_min_severity`` (default "CRITICAL" -- the inventory has 344 entries
  total, most of them not overlay-sized).
* every entry in ``data/sentiments/positive_sentiments.json`` and
  ``negative_sentiments.json`` -- publication dates of articles/events judged
  to have moved DNSSEC's public legitimacy up or down.

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
    "DEFAULT_DISTRO_SHIPS_PATH",
    "DEFAULT_CVE_INVENTORY_PATH",
    "DEFAULT_POSITIVE_SENTIMENTS_PATH",
    "DEFAULT_NEGATIVE_SENTIMENTS_PATH",
    "CVE_SEVERITY_ORDER",
    "EVENT_COLORS",
    "load_rfc_events",
    "load_software_support_events",
    "load_distro_ship_events",
    "load_cve_events",
    "load_positive_sentiment_events",
    "load_negative_sentiment_events",
    "plot_tld_timeline",
]

DEFAULT_METRICS: tuple[str, ...] = ("ds_prevalence", "dnskey_prevalence", "rrsig_prevalence")

#: Point size of an event label and the DPI it's rendered/saved at -- shared by
#: the lane-assignment math below (which needs to know how many pixels a
#: label actually occupies) and the final plt.savefig call, so the two never
#: silently disagree about scale.
LABEL_FONTSIZE: int = 6
SAVE_DPI: int = 150

#: Per-attempt downward nudge when resolving a label collision, as a fraction
#: of the axis's y-range, and how many times to try before giving up and
#: accepting the overlap (a pathological cluster, not a crash).
LABEL_NUDGE_FRACTION: float = 0.015
MAX_LABEL_NUDGES: int = 150

#: These three live under data/software/, not openintel_rfc, so (unlike
#: DEFAULT_CHECKLIST_PATH) their defaults live here rather than in that
#: package's config.
DEFAULT_SOFTWARE_SUPPORT_PATH: Path = (
    config.PROJECT_ROOT / "data" / "software" / "software_support.json"
)
DEFAULT_DISTRO_SHIPS_PATH: Path = config.PROJECT_ROOT / "data" / "software" / "distro_ships.json"
DEFAULT_CVE_INVENTORY_PATH: Path = (
    config.PROJECT_ROOT / "data" / "software" / "cve_inventory.json"
)
DEFAULT_POSITIVE_SENTIMENTS_PATH: Path = (
    config.PROJECT_ROOT / "data" / "sentiments" / "positive_sentiments.json"
)
DEFAULT_NEGATIVE_SENTIMENTS_PATH: Path = (
    config.PROJECT_ROOT / "data" / "sentiments" / "negative_sentiments.json"
)

#: Low-to-high, matching the strings cve_inventory.json uses.
CVE_SEVERITY_ORDER: tuple[str, ...] = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

#: One fixed color per event category. Keep existing entries where they are so
#: a category already in use never changes color just because another one was
#: added. "sentiment_positive" is deliberately not tab:blue -- that's already
#: the prevalence line's own color, and reusing it would make an event marker
#: hard to tell apart from the data at a glance. "sentiment_negative" is
#: deliberately not a plain yellow -- yellow text on a white plot background
#: is a legibility problem, not just an aesthetic one.
EVENT_COLORS: dict[str, str] = {
    "rfc": "tab:red",
    "software_support": "tab:purple",
    "distro_ship": "tab:green",
    "cve": "tab:orange",
    "sentiment_positive": "tab:cyan",
    "sentiment_negative": "tab:olive",
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


def load_distro_ship_events(path: Path | str | None = None) -> list[tuple[pd.Timestamp, str]]:
    """Every distro_ships.json "ships" entry's (release date, label).

    Only ``ships`` (the dated OS releases that also record which DNS software
    version they carried) is used -- ``major_releases`` in the same file is a
    broader, undated-DNS-version list kept for that file's own chance-rate
    statistics, not an event worth marking here.
    """
    file_path = Path(path) if path else DEFAULT_DISTRO_SHIPS_PATH
    if not file_path.is_file():
        raise PipelineError(f"Distro ships file not found: {file_path}")
    payload = json.loads(file_path.read_text(encoding="utf-8"))

    by_date: dict[pd.Timestamp, list[str]] = defaultdict(list)
    for entry in payload.get("ships", []):
        day = pd.Timestamp(entry["released"])
        by_date[day].append(str(entry.get("name", entry.get("distribution", "?"))))
    return [(day, "; ".join(labels)) for day, labels in sorted(by_date.items())]


def load_cve_events(
    path: Path | str | None = None,
    *,
    min_severity: str = "CRITICAL",
) -> list[tuple[pd.Timestamp, str]]:
    """Every CVE in cve_inventory.json at or above ``min_severity``.

    An entry with no recorded severity is always excluded -- there is nothing
    to compare against a threshold. 344 CVEs total across the 8 programs; at
    the default "CRITICAL" that is 12, which is what makes this usable as a
    timeline overlay at all.
    """
    if min_severity not in CVE_SEVERITY_ORDER:
        raise PipelineError(
            f"min_severity must be one of {CVE_SEVERITY_ORDER}, got {min_severity!r}."
        )
    threshold = CVE_SEVERITY_ORDER.index(min_severity)

    file_path = Path(path) if path else DEFAULT_CVE_INVENTORY_PATH
    if not file_path.is_file():
        raise PipelineError(f"CVE inventory file not found: {file_path}")
    payload = json.loads(file_path.read_text(encoding="utf-8"))

    by_date: dict[pd.Timestamp, list[str]] = defaultdict(list)
    for product, cves in payload.get("by_product", {}).items():
        for entry in cves:
            severity = entry.get("severity")
            if severity not in CVE_SEVERITY_ORDER or CVE_SEVERITY_ORDER.index(severity) < threshold:
                continue
            day = pd.Timestamp(entry["published"])
            by_date[day].append(f"{product} {entry['cve']}")

    events: list[tuple[pd.Timestamp, str]] = []
    for day, labels in sorted(by_date.items()):
        if len(labels) <= 3:
            events.append((day, "; ".join(labels)))
            continue
        # A handful of CVEs sharing a date reads fine as a joined list; a batch
        # disclosure does not -- 7 CRITICAL unbound CVEs all carry a published
        # date of 2021-04-27 (NVD backdating a late batch review), and joining
        # all 7 into one label is long enough to break the plot's layout.
        # Past 3, summarize instead of listing every one.
        products = sorted({label.split(" ", 1)[0] for label in labels})
        summary = (
            f"{products[0]}: {len(labels)} CVEs"
            if len(products) == 1
            else f"{len(labels)} CVEs ({', '.join(products)})"
        )
        events.append((day, summary))
    return events


def _load_sentiment_entries(path: Path) -> list[tuple[pd.Timestamp, str]]:
    """Shared loader for positive_sentiments.json / negative_sentiments.json.

    Both files share one schema, but the hand-maintained date field's name
    isn't even consistent *within* one file: negative_sentiments.json spells
    it "Publicatiion Date" (double i) for its first entry and "Publiction
    Date" (the same typo positive_sentiments.json uses throughout) for the
    rest. Every plausible spelling is tried per entry rather than assuming
    one -- a KeyError here would silently drop the whole file's events.
    """
    if not path.is_file():
        raise PipelineError(f"Sentiments file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))

    date_keys = ("Publiction Date", "Publicatiion Date", "Publication Date")
    by_date: dict[pd.Timestamp, list[str]] = defaultdict(list)
    for entry in payload.get("sentiments", []):
        raw_date = next((entry[key] for key in date_keys if key in entry), None)
        if raw_date is None:
            raise PipelineError(
                f"Sentiment entry {entry.get('sentimentID', '?')!r} in {path} has none of "
                f"the expected date fields {date_keys}."
            )
        day = pd.Timestamp(raw_date)
        label = str(entry.get("sentimentID") or entry.get("Title") or "?")
        by_date[day].append(label)
    return [(day, "; ".join(labels)) for day, labels in sorted(by_date.items())]


def load_positive_sentiment_events(
    path: Path | str | None = None,
) -> list[tuple[pd.Timestamp, str]]:
    """Every positive_sentiments.json entry's (publication date, label)."""
    return _load_sentiment_entries(Path(path) if path else DEFAULT_POSITIVE_SENTIMENTS_PATH)


def load_negative_sentiment_events(
    path: Path | str | None = None,
) -> list[tuple[pd.Timestamp, str]]:
    """Every negative_sentiments.json entry's (publication date, label)."""
    return _load_sentiment_entries(Path(path) if path else DEFAULT_NEGATIVE_SENTIMENTS_PATH)


def _overlaps(a, b) -> bool:
    """Whether two matplotlib display-space bounding boxes intersect."""
    return a.x0 < b.x1 and b.x0 < a.x1 and a.y0 < b.y1 and b.y0 < a.y1


def plot_tld_timeline(
    input_path: Path | str,
    tld: str,
    *,
    metrics: Sequence[str] = DEFAULT_METRICS,
    checklist_path: Path | str | None = None,
    software_support_path: Path | str | None = None,
    distro_ships_path: Path | str | None = None,
    cve_path: Path | str | None = None,
    cve_min_severity: str = "CRITICAL",
    positive_sentiments_path: Path | str | None = None,
    negative_sentiments_path: Path | str | None = None,
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
    span_months = max(len(tld_df), 1)

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
    ] + [
        (when, label, "distro_ship")
        for when, label in load_distro_ship_events(distro_ships_path)
        if window_start <= when <= window_end
    ] + [
        (when, label, "cve")
        for when, label in load_cve_events(cve_path, min_severity=cve_min_severity)
        if window_start <= when <= window_end
    ] + [
        (when, label, "sentiment_positive")
        for when, label in load_positive_sentiment_events(positive_sentiments_path)
        if window_start <= when <= window_end
    ] + [
        (when, label, "sentiment_negative")
        for when, label in load_negative_sentiment_events(negative_sentiments_path)
        if window_start <= when <= window_end
    ]
    categorized.sort(key=lambda item: item[0])

    metrics = list(metrics)
    # Width scales with the data's actual time span (not a fixed 11in) so a
    # multi-year timeline with a dense stretch of events gets proportionally
    # more horizontal room for labels to spread out, instead of staying as
    # cramped as a 2-year plot would be.
    fig_width = max(11.0, span_months * 0.18)
    fig, axes = plt.subplots(len(metrics), 1, figsize=(fig_width, 4.5 * len(metrics)), sharex=True)
    if len(metrics) == 1:
        axes = [axes]

    for ax, metric in zip(axes, metrics):
        ax.plot(tld_df["month"], tld_df[metric], "o-", markersize=3, linewidth=1, color="tab:blue")
        ax.set_title(f"{tld}: {metric}")
        ax.set_ylabel("prevalence")

    axes[-1].set_xlabel("month")
    # Explicit month ticks instead of matplotlib's default (which collapses to
    # bare years over a long span). The interval scales with the span so a
    # multi-decade plot still gets month-labelled ticks without cramming in
    # one per calendar month.
    interval = max(1, round(span_months / 20))
    for ax in axes:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=interval))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    # Finalize the layout (axis positions, margins) before placing event
    # labels below -- ax.text() annotations don't participate in tight_layout
    # at all, so doing this first means the collision detection measures
    # against the exact geometry the figure will actually be saved with,
    # rather than an approximation that layout could still shift afterward.
    plt.tight_layout()

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    for ax in axes:
        bottom, top = ax.get_ylim()
        step = LABEL_NUDGE_FRACTION * (top - bottom)
        placed_boxes: list = []
        for when, label, category in categorized:
            color = EVENT_COLORS[category]
            ax.axvline(when, color=color, linestyle="--", linewidth=0.8, alpha=0.7)
            y = top
            text_obj = ax.text(
                when, y, label, rotation=90, fontsize=LABEL_FONTSIZE,
                color=color, ha="right", va="top",
            )
            # Real collision avoidance: nudge the label down, by an amount
            # measured against its *actual rendered size* (not an estimate of
            # how many pixels a label "should" take), until it clears every
            # label already placed on this axis or we run out of room/patience
            # -- at which point the overlap is accepted as the least-bad
            # option for however dense that stretch genuinely is.
            bbox = text_obj.get_window_extent(renderer=renderer)
            attempts = 0
            while (
                any(_overlaps(bbox, other) for other in placed_boxes)
                and y - step > bottom
                and attempts < MAX_LABEL_NUDGES
            ):
                y -= step
                text_obj.set_position((when, y))
                bbox = text_obj.get_window_extent(renderer=renderer)
                attempts += 1
            placed_boxes.append(bbox)

    out_path = Path(out_path) if out_path else Path(f"{tld}_timeline.png")
    plt.savefig(out_path, dpi=SAVE_DPI)
    plt.close(fig)
    return out_path
