"""Find the Parquet corpus when it is spread across several drives.

The server's OpenINTEL cache outgrew one disk, so part of it was moved. Nothing
about that move is recorded anywhere: the same source-day can now have some of
its files on one drive and the rest on another, and a naive scan of either root
sees a *partial* day and reports it as a complete one. That is the failure this
module exists to prevent -- a silently short day looks exactly like a day when
fewer domains were signed, and it would be read as a measurement.

So discovery here is deliberately root-agnostic. Every root is walked, each file
is reduced to a ``(source, date, filename)`` identity, and identities are merged
across roots. A source-day is the union of its files wherever they live; a file
present on two roots is counted once and reported as a duplicate rather than
scanned twice.

Layouts
-------
Three are recognised, tried in order, because the cache holds files written by
different things over time:

1. ``<root>/<basis>/<source>/<YYYY-MM-DD>/*.parquet`` -- what ``cache_paths``
   writes, so a mirror and an ingested reverse corpus are both found.
2. ``.../source=<name>/year=YYYY/month=M/day=D/*.parquet`` -- OpenINTEL's own
   Hive-style partitioning, which is what a bulk copy of the public bucket has.
3. Anything else with a date and a recognisable source in the path, matched by
   regex as a last resort.

A file no pattern matches is *reported*, never silently skipped: an unreadable
corner of a 14 TB cache is a fact the operator needs, and a run that quietly
covers 80% of the data is worse than one that says so.
"""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

from .utils import PipelineError, ensure_dir, get_logger, warn

__all__ = [
    "CachedDay",
    "CacheInventory",
    "build_inventory",
    "discover_files",
    "load_inventory",
    "parse_path",
    "save_inventory",
]

LOGGER = get_logger(__name__)

#: ``<basis>/<source>/<YYYY-MM-DD>/file.parquet`` -- the layout this project writes.
_MIRROR_RE = re.compile(
    r"/(?P<basis>[A-Za-z0-9_.-]+)/(?P<source>[A-Za-z0-9_.-]+)/"
    r"(?P<date>\d{4}-\d{2}-\d{2})/[^/]+$"
)

#: OpenINTEL's Hive-style layout. Month and day are not zero-padded in the wild.
_HIVE_RE = re.compile(
    r"/source=(?P<source>[^/]+)/year=(?P<year>\d{4})/month=(?P<month>\d{1,2})/"
    r"day=(?P<day>\d{1,2})/[^/]+$"
)

#: Last resort: any ``YYYY/MM/DD`` or ``YYYY-MM-DD`` anywhere in the path.
_LOOSE_DATE_RE = re.compile(r"(?P<year>20\d{2})[-/_](?P<month>\d{1,2})[-/_](?P<day>\d{1,2})")


@dataclass
class CachedDay:
    """One source-day, with every file that belongs to it from every root."""

    source: str
    day: date
    basis: str = "zonefile"
    paths: list[str] = field(default_factory=list)
    roots: set[str] = field(default_factory=set)
    bytes_total: int = 0

    @property
    def key(self) -> str:
        return f"{self.basis}/{self.source}/{self.day.isoformat()}"

    @property
    def split_across_roots(self) -> bool:
        """True when this day's files do not all live on one drive."""
        return len(self.roots) > 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "source": self.source,
            "basis": self.basis,
            "day": self.day.isoformat(),
            "paths": sorted(self.paths),
            "roots": sorted(self.roots),
            "files": len(self.paths),
            "bytes": self.bytes_total,
            "split_across_roots": self.split_across_roots,
        }


@dataclass
class CacheInventory:
    """Everything discoverable under a set of roots, keyed by source-day."""

    roots: list[str]
    days: dict[str, CachedDay] = field(default_factory=dict)
    unmatched: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # -- summaries the operator actually wants to see ----------------------- #

    @property
    def sources(self) -> list[str]:
        return sorted({d.source for d in self.days.values()})

    @property
    def total_files(self) -> int:
        return sum(len(d.paths) for d in self.days.values())

    @property
    def total_bytes(self) -> int:
        return sum(d.bytes_total for d in self.days.values())

    def span(self, source: str | None = None) -> tuple[date, date] | None:
        days = [d.day for d in self.days.values() if source in (None, d.source)]
        return (min(days), max(days)) if days else None

    def select(
        self,
        sources: Sequence[str] | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> list[CachedDay]:
        """Source-days matching a filter, in a stable order."""
        chosen = [
            day for day in self.days.values()
            if (sources is None or day.source in set(sources))
            and (start is None or day.day >= start)
            and (end is None or day.day <= end)
        ]
        return sorted(chosen, key=lambda d: (d.source, d.day))

    def summary(self) -> dict[str, Any]:
        per_source: dict[str, dict[str, Any]] = {}
        for source in self.sources:
            days = [d for d in self.days.values() if d.source == source]
            span = (min(d.day for d in days), max(d.day for d in days))
            per_source[source] = {
                "days": len(days),
                "files": sum(len(d.paths) for d in days),
                "bytes": sum(d.bytes_total for d in days),
                "first_day": span[0].isoformat(),
                "last_day": span[1].isoformat(),
                "days_split_across_roots": sum(1 for d in days if d.split_across_roots),
            }
        return {
            "roots": self.roots,
            "sources": self.sources,
            "source_days": len(self.days),
            "files": self.total_files,
            "bytes": self.total_bytes,
            "unmatched_files": len(self.unmatched),
            "duplicate_files": len(self.duplicates),
            "days_split_across_roots": sum(
                1 for d in self.days.values() if d.split_across_roots
            ),
            "per_source": per_source,
        }


def parse_path(path: str) -> tuple[str, date, str] | None:
    """``(source, day, basis)`` inferred from a file's path, or None.

    Patterns are tried most-specific first. The loose pattern is last because it
    would happily match a date inside a filename that means something else.
    """
    posix = Path(path).as_posix()

    hive = _HIVE_RE.search(posix)
    if hive:
        try:
            day = date(int(hive["year"]), int(hive["month"]), int(hive["day"]))
        except ValueError:
            return None
        return hive["source"], day, "zonefile"

    mirror = _MIRROR_RE.search(posix)
    if mirror:
        try:
            day = date.fromisoformat(mirror["date"])
        except ValueError:
            return None
        return mirror["source"], day, mirror["basis"]

    loose = _LOOSE_DATE_RE.search(posix)
    if loose:
        try:
            day = date(int(loose["year"]), int(loose["month"]), int(loose["day"]))
        except ValueError:
            return None
        # The source is the nearest ancestor directory that is not itself part of
        # the date. A `YYYY/MM/DD` path splits the date across three components,
        # so filtering only on the full pattern leaves "05" looking like a source
        # name -- each component has to be rejected on its own.
        parts = Path(posix).parts[:-1]  # drop the filename
        source = next(
            (p for p in reversed(parts)
             if not p.isdigit() and not _LOOSE_DATE_RE.fullmatch(p)),
            "unknown",
        )
        return source, day, "zonefile"

    return None


def discover_files(
    roots: Iterable[Path | str], *, suffix: str = ".parquet"
) -> Iterator[tuple[str, str, int]]:
    """Yield ``(root, path, size)`` for every candidate file under every root.

    ``os.scandir`` rather than ``Path.rglob``: on a 14 TB cache the difference is
    minutes, because scandir gets the size from the directory entry that the walk
    already read instead of a second stat per file.
    """
    for raw_root in roots:
        root = Path(raw_root)
        if not root.exists():
            raise PipelineError(f"Cache root does not exist: {root}")
        root_key = root.as_posix()
        stack = [root]
        while stack:
            current = stack.pop()
            try:
                entries = list(os.scandir(current))
            except (PermissionError, OSError) as exc:  # unreadable corner
                LOGGER.warning("cannot read %s: %s", current, exc)
                continue
            for entry in entries:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(Path(entry.path))
                    elif entry.name.endswith(suffix):
                        yield root_key, Path(entry.path).as_posix(), entry.stat().st_size
                except OSError:  # a file that vanished mid-walk
                    continue


def build_inventory(
    roots: Sequence[Path | str],
    *,
    suffix: str = ".parquet",
    progress_every: int = 50_000,
) -> CacheInventory:
    """Walk every root and merge what is found into one view of the corpus."""
    if not roots:
        raise PipelineError("build_inventory requires at least one root.")
    inventory = CacheInventory(roots=[Path(r).as_posix() for r in roots])
    seen_names: dict[str, set[str]] = defaultdict(set)
    count = 0

    for root_key, path, size in discover_files(roots, suffix=suffix):
        count += 1
        if progress_every and count % progress_every == 0:
            LOGGER.info("indexed %d files...", count)

        parsed = parse_path(path)
        if parsed is None:
            inventory.unmatched.append(path)
            continue
        source, day, basis = parsed
        key = f"{basis}/{source}/{day.isoformat()}"
        entry = inventory.days.get(key)
        if entry is None:
            entry = CachedDay(source=source, day=day, basis=basis)
            inventory.days[key] = entry

        # Identity is the filename within the source-day. The same object copied
        # to a second drive is one object, not two, and scanning it twice would
        # double every count it contributes.
        name = Path(path).name
        if name in seen_names[key]:
            inventory.duplicates.append(path)
            continue
        seen_names[key].add(name)
        entry.paths.append(path)
        entry.roots.add(root_key)
        entry.bytes_total += size

    if inventory.unmatched:
        warn(
            inventory.warnings,
            f"{len(inventory.unmatched)} file(s) matched no known layout and are "
            "absent from this run. They are listed in the inventory under "
            "'unmatched'; if they hold measurements, add a layout pattern rather "
            "than letting the run quietly cover less than the cache holds.",
            LOGGER,
        )
    if inventory.duplicates:
        warn(
            inventory.warnings,
            f"{len(inventory.duplicates)} file(s) exist on more than one root and "
            "were counted once. This is expected after a partial move between "
            "drives; the copies are listed under 'duplicates'.",
            LOGGER,
        )
    split = sum(1 for d in inventory.days.values() if d.split_across_roots)
    if split:
        LOGGER.info(
            "%d source-day(s) have files on more than one root; each is scanned as "
            "the union of its files.", split,
        )
    if not inventory.days:
        raise PipelineError(
            f"No {suffix} files under {', '.join(inventory.roots)} matched a known "
            "layout. Check the roots, or add a pattern to cache_index."
        )
    return inventory


def save_inventory(inventory: CacheInventory, path: Path | str) -> Path:
    """Persist the inventory so a 14 TB walk is paid for once."""
    target = Path(path)
    ensure_dir(target.parent)
    payload = {
        "summary": inventory.summary(),
        "warnings": inventory.warnings,
        "days": [day.to_dict() for day in sorted(
            inventory.days.values(), key=lambda d: (d.source, d.day)
        )],
        "unmatched": sorted(inventory.unmatched)[:5000],
        "duplicates": sorted(inventory.duplicates)[:5000],
    }
    target.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return target


def load_inventory(path: Path | str) -> CacheInventory:
    """Read back what :func:`save_inventory` wrote."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    inventory = CacheInventory(roots=list(payload["summary"]["roots"]))
    inventory.warnings = list(payload.get("warnings", ()))
    inventory.unmatched = list(payload.get("unmatched", ()))
    inventory.duplicates = list(payload.get("duplicates", ()))
    for row in payload["days"]:
        inventory.days[row["key"]] = CachedDay(
            source=row["source"],
            day=date.fromisoformat(row["day"]),
            basis=row.get("basis", "zonefile"),
            paths=list(row["paths"]),
            roots=set(row.get("roots", ())),
            bytes_total=int(row.get("bytes", 0)),
        )
    return inventory
