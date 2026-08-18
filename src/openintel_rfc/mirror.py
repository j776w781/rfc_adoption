"""Mirror the OpenINTEL objects a run needs, once, across one or more machines.

Why this exists
---------------
The store's request limiter is not the bottleneck people assume it is. Measured
against ``object.openintel.nl``, nginx allows about one request per second with a
burst of about five. The corpus this project scans is 7,261 objects totalling
2.07 TB, so *mirroring it costs about 7,261 requests -- two hours of request
budget*. Moving the 2.07 TB is what takes real time.

That inverts the tuning problem:

* **Streaming** re-reads the store on every run. A scan costs a handful of
  requests per object (6 for a 485 MB ``.se`` object with the prefilter pushed
  down, 2-3 for a small ``.gov`` day), so the whole corpus is roughly 43,000
  requests -- twelve hours of budget -- and you pay it again every time the
  checklist changes.
* **Mirroring** costs one request per object, once. Every scan afterwards is
  local, unlimited, and does not touch Utwente at all.

So the fix for "the rate limit is a bottleneck" is not a cleverer retry. It is to
stop making the store part of the inner loop.

Splitting the work across machines
----------------------------------
Two things make naive sharding useless here.

The first is that the corpus is wildly unbalanced. ``.se`` is 1.49 TB of the
2.07 TB and ``.gov`` is 15.8 GB, so "one machine per year" hands one machine 750 GB
and another 2 GB. :func:`plan_shards` therefore balances on **bytes**, not on days
or partitions.

The second is that the limiter is keyed per client address, so extra machines only
help when they have their own network path. Two VMs behind one NAT share one
budget and one uplink and will not go faster than one; two machines on different
links roughly double. Nothing here can detect that -- it is a property of your
network -- so `--shards` is a declaration, not a discovery.

The assignment is deterministic: the same object set and the same shard count
always produce the same split, so a machine that dies mid-mirror resumes on
exactly its own share, and no two machines fetch the same object.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Sequence

from .openintel_source import (
    AccessConfig,
    build_s3_client,
    date_range,
    partition_prefix,
)
from .scale_runner import ThrottleGovernor
from .utils import PipelineError, ensure_dir, get_logger, warn

LOGGER = get_logger(__name__)

#: Suffix of a staged, not-yet-complete download. A partial file must never be
#: mistaken for a finished one by the next pass.
PART_SUFFIX = ".part"


@dataclass(frozen=True)
class RemoteObject:
    """One object in the store, with the size the mirror plan needs."""

    key: str
    size: int
    source: str
    basis: str
    day: date

    @property
    def basename(self) -> str:
        name = self.key.rsplit("/", 1)[-1].strip()
        if not name or name in {".", ".."} or "\\" in name:
            raise PipelineError(f"Object key does not end in a usable file name: {self.key!r}")
        return name

    def cache_path(self, cache_dir: Path | str) -> Path:
        """Where this object belongs on disk.

        Deliberately identical to ``openintel_source.cache_paths``: a mirror is
        only useful if ``--mode download --cache-dir`` finds it without being
        told anything else.
        """
        return (
            Path(cache_dir)
            / self.basis
            / self.source
            / self.day.isoformat()
            / self.basename
        )


@dataclass
class MirrorReport:
    """What a mirror pass actually did."""

    fetched: int = 0
    skipped: int = 0
    failed: int = 0
    bytes_fetched: int = 0
    bytes_present: int = 0
    elapsed_seconds: float = 0.0
    warnings: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return self.failed == 0

    def describe(self) -> str:
        rate = self.bytes_fetched / self.elapsed_seconds if self.elapsed_seconds else 0.0
        return (
            f"{self.fetched} fetched ({self.bytes_fetched / 1e9:.1f} GB), "
            f"{self.skipped} already present ({self.bytes_present / 1e9:.1f} GB), "
            f"{self.failed} failed, {self.elapsed_seconds / 60:.1f} min, "
            f"{rate / 1e6:.1f} MB/s"
        )


# --------------------------------------------------------------------------- #
# Listing
# --------------------------------------------------------------------------- #


def list_objects(
    config: AccessConfig,
    *,
    sources: Sequence[str],
    start: Any,
    end: Any,
    basis: str = "zonefile",
    client: Any | None = None,
) -> list[RemoteObject]:
    """Every object for ``sources`` over the date range, with its size.

    Listing is paginated at 1,000 keys per request, so enumerating the whole
    corpus costs single-digit requests per source-year -- cheap enough to do
    before every mirror pass rather than caching a manifest that can go stale.
    """
    s3 = client if client is not None else build_s3_client(config)
    paginator = s3.get_paginator("list_objects_v2")
    days = date_range(start, end)
    found: list[RemoteObject] = []

    for source in sources:
        for day in days:
            prefix = partition_prefix(basis, source, day)
            try:
                pages = paginator.paginate(Bucket=config.bucket, Prefix=prefix)
                for page in pages:
                    for item in page.get("Contents", ()):
                        key = item["Key"]
                        if not key.endswith(".parquet"):
                            continue
                        found.append(
                            RemoteObject(
                                key=key,
                                size=int(item["Size"]),
                                source=source,
                                basis=basis,
                                day=day,
                            )
                        )
            except Exception as exc:
                raise PipelineError(
                    f"Listing s3://{config.bucket}/{prefix} failed: {exc}"
                ) from exc

    return found


# --------------------------------------------------------------------------- #
# Splitting the work
# --------------------------------------------------------------------------- #


def plan_shards(objects: Iterable[RemoteObject], shards: int) -> list[list[RemoteObject]]:
    """Split ``objects`` into ``shards`` lists of roughly equal **bytes**.

    Greedy longest-processing-time-first: take the largest object still unplaced
    and give it to whichever shard currently holds the fewest bytes. For a set
    like this one -- a few thousand objects, sizes spread over three orders of
    magnitude -- that lands within a couple of percent of a perfect split, which
    is far closer than any split by day or by year can get.

    Deterministic by construction. Ties break on the key, so the same input
    always yields the same assignment and a machine that restarts resumes on its
    own share rather than racing its neighbours for objects they already hold.
    """
    count = max(int(shards), 1)
    buckets: list[list[RemoteObject]] = [[] for _ in range(count)]
    loads = [0] * count

    # Largest first, key as the tie-break so the order never depends on the
    # listing order the store happened to return.
    for obj in sorted(objects, key=lambda o: (-o.size, o.key)):
        target = min(range(count), key=lambda i: (loads[i], i))
        buckets[target].append(obj)
        loads[target] += obj.size

    return buckets


def describe_plan(buckets: Sequence[Sequence[RemoteObject]]) -> str:
    """A human-readable balance report; printed before a mirror starts."""
    lines = [f"{'shard':>6} {'objects':>9} {'size':>12}"]
    for index, bucket in enumerate(buckets):
        total = sum(o.size for o in bucket)
        lines.append(f"{index:>6} {len(bucket):>9,} {total / 1e9:>9.1f} GB")
    sizes = [sum(o.size for o in b) for b in buckets]
    if sizes and max(sizes) > 0:
        spread = (max(sizes) - min(sizes)) / max(sizes) * 100
        lines.append(f"  spread between heaviest and lightest shard: {spread:.1f}%")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #


def _already_present(destination: Path, expected_size: int) -> bool:
    """True when the local copy is byte-complete.

    Checked against the size the store reports, not merely "exists and is
    non-empty". A mirror is the input to every later run, so a silently short
    file would turn into a silently short *analysis* -- a partition that scans
    without error and returns too few rows.
    """
    if not destination.is_file():
        return False
    if expected_size <= 0:  # nothing to compare against; trust presence
        return destination.stat().st_size > 0
    return destination.stat().st_size == expected_size


def mirror_objects(
    objects: Sequence[RemoteObject],
    *,
    config: AccessConfig,
    cache_dir: Path | str,
    governor: ThrottleGovernor | None = None,
    client: Any | None = None,
    warnings: list[str] | None = None,
    dry_run: bool = False,
) -> MirrorReport:
    """Download ``objects`` into ``cache_dir``, skipping what is already correct.

    One GET per object, which is the whole point: it is the cheapest possible way
    to spend the request budget, and it is paid once rather than on every run.

    Each object lands on a ``.part`` sibling and is renamed only when the
    transfer finishes, so an interrupted mirror leaves no file that the next pass
    would accept as complete.
    """
    collected = warnings if warnings is not None else []
    report = MirrorReport(warnings=collected)
    pacer = governor or ThrottleGovernor()
    s3 = client if client is not None else build_s3_client(config)

    total_bytes = sum(o.size for o in objects)
    LOGGER.info(
        "Mirroring %d object(s), %.1f GB, into %s",
        len(objects),
        total_bytes / 1e9,
        cache_dir,
    )
    started = time.time()

    for index, obj in enumerate(objects, start=1):
        destination = obj.cache_path(cache_dir)
        if _already_present(destination, obj.size):
            report.skipped += 1
            report.bytes_present += destination.stat().st_size
            continue
        if dry_run:
            report.fetched += 1
            report.bytes_fetched += obj.size
            continue

        ensure_dir(destination.parent)
        partial = destination.with_name(destination.name + PART_SUFFIX)
        if partial.exists():
            partial.unlink()

        try:
            s3.download_file(Bucket=config.bucket, Key=obj.key, Filename=str(partial))
        except Exception as exc:
            if partial.exists():
                partial.unlink()
            report.failed += 1
            warn(
                collected,
                f"Mirroring s3://{config.bucket}/{obj.key} failed: {exc}",
                LOGGER,
            )
            pacer.on_throttled()
            pacer.wait()
            continue

        actual = partial.stat().st_size
        if obj.size > 0 and actual != obj.size:
            partial.unlink()
            report.failed += 1
            warn(
                collected,
                f"Mirroring {obj.key} produced {actual} bytes but the store "
                f"reports {obj.size}; the short copy was discarded rather than "
                "left for a later run to scan.",
                LOGGER,
            )
            continue

        partial.replace(destination)
        report.fetched += 1
        report.bytes_fetched += actual
        pacer.on_success()

        done = report.fetched + report.skipped
        if done % 25 == 0 or index == len(objects):
            elapsed = time.time() - started
            rate = report.bytes_fetched / elapsed if elapsed else 0.0
            remaining = total_bytes - report.bytes_fetched - report.bytes_present
            eta = remaining / rate if rate > 0 else 0.0
            LOGGER.info(
                "Mirror %d/%d | %.1f GB fetched | %.1f MB/s | ETA %.1f h",
                index,
                len(objects),
                report.bytes_fetched / 1e9,
                rate / 1e6,
                eta / 3600,
            )
        pacer.wait()

    report.elapsed_seconds = time.time() - started
    LOGGER.info("Mirror finished: %s", report.describe())
    return report
