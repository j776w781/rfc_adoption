"""Discovery of, and access to, the real OpenINTEL S3 corpus.

The MVP reads one Parquet file that happens to be on local disk. A real-scale
run reads *partitions* -- one measurement day of one zone -- straight out of
OpenINTEL's public object store. This module is the boundary between "a date
range someone typed on the command line" and "a list of concrete Parquet
objects DuckDB can scan". Nothing above it needs to know about S3, and nothing
below it needs to know about RFCs.

Why the layout matters
----------------------
OpenINTEL publishes forward-DNS measurements under a Hive-style prefix::

    fdns/basis={zonefile|toplist}/source={tld}/year=YYYY/month=MM/day=DD/

with one or more ``*.gz.parquet`` objects per day (``.se`` days are split into
four ~500 MiB parts; ``.nu`` days are a single ~350 MiB part). The partition
columns live in the *path*, not in the files. DuckDB's ``read_parquet``
recovers them automatically through Hive-partition detection, which is why
``probe_schema`` reports them separately: they are real, queryable columns in
stream mode even though ``parquet_schema`` never mentions them.

Two access modes, deliberately interchangeable
----------------------------------------------
``stream``
    DuckDB reads ``s3://`` URIs directly through ``httpfs``. Nothing touches
    local disk, so a multi-terabyte range needs no staging area. Range requests
    mean a well-pushed-down predicate reads a fraction of each object.
``download``
    Objects are staged under ``cache_dir/<basis>/<source>/<YYYY-MM-DD>/`` and
    scanned locally. Slower to start and it needs the disk, but it survives a
    flaky link, and a re-run of the same range costs nothing because a file
    that is already present with a non-zero size is never fetched again.

The mode is a property of :class:`AccessConfig` alone. Every other function in
this module -- and, more importantly, every caller -- behaves identically
either way.

Access is anonymous
-------------------
The bucket is public and there are no credentials to configure. Getting this
right is fiddly enough to be worth stating: botocore must be told
``signature_version=UNSIGNED``, *and* the ``fix_s3_host`` handler must be
unregistered from ``before-sign.s3``, or botocore rewrites the request host
into an AWS virtual-host style name and the request leaves for Amazon instead
of Utwente. On the DuckDB side the equivalent is a ``TYPE s3`` secret with
empty credentials, path-style URLs and an explicit endpoint.

boto3 is an optional dependency. It is imported inside the functions that need
it, so the MVP -- which never lists an S3 bucket -- keeps importing and running
on a machine that has never heard of it. No function here performs IO at import
time.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from .models import OpenINTELDictionary
from .parquet_reader import resolve_column_candidates
from .utils import PipelineError, ensure_dir, get_logger, parse_timestamp, warn

if TYPE_CHECKING:  # pragma: no cover - typing only, never imported at runtime
    import duckdb

__all__ = [
    "BASES",
    "DEFAULT_BUCKET",
    "DEFAULT_ENDPOINT",
    "DEFAULT_REGION",
    "FDNS_BASE",
    "MODES",
    "OBJECT_SUFFIX",
    "PARTITION_COLUMNS",
    "SECRET_NAME",
    "AccessConfig",
    "Partition",
    "build_s3_client",
    "cache_paths",
    "configure_duckdb_s3",
    "date_range",
    "discover_partitions",
    "estimate_partition_rows",
    "list_partition_keys",
    "list_sources",
    "materialize",
    "open_duckdb",
    "partition_prefix",
    "partition_uris",
    "probe_schema",
]

LOGGER = get_logger(__name__)

#: OpenINTEL's S3-compatible endpoint. Not AWS; see the module docstring.
DEFAULT_ENDPOINT: str = "https://object.openintel.nl"

#: The public, credential-free bucket.
DEFAULT_BUCKET: str = "openintel-public"

#: Region string the endpoint expects. Signing is disabled, but botocore still
#: requires *a* region to build a client.
DEFAULT_REGION: str = "nl-utwente"

#: Top-level prefix for forward-DNS measurement data.
FDNS_BASE: str = "fdns"

#: Measurement bases published under :data:`FDNS_BASE`.
BASES: tuple[str, ...] = ("zonefile", "toplist")

#: Suffix every measurement object carries.
OBJECT_SUFFIX: str = ".gz.parquet"

#: Access modes accepted by :class:`AccessConfig`.
MODES: tuple[str, ...] = ("stream", "download")

#: Columns DuckDB reconstructs from the Hive-style path rather than the file.
#: They are unavailable to a reader that opens the object by hand, which is why
#: :func:`probe_schema` reports them apart from the file's own columns.
PARTITION_COLUMNS: tuple[str, ...] = ("basis", "source", "year", "month", "day")

#: Name of the DuckDB secret this module creates. Fixed, so that repeated
#: configuration of one connection replaces rather than accumulates.
SECRET_NAME: str = "openintel_public"

#: Multipart chunk size for downloads. OpenINTEL rate-limits request *count*,
#: so a small chunk size on a 500 MiB object trips the limiter and the transfer
#: stalls; 64 MiB is the value the project's existing boto3 code uses.
_MULTIPART_CHUNKSIZE: int = 64 * 1024 * 1024

#: Characters that must never appear in a path component taken from user input
#: or from an object key. ``partition_id`` is used to name checkpoint files, so
#: a stray separator would escape the directory it is meant to sit in.
_UNSAFE_PATH_CHARS: frozenset[str] = frozenset('/\\=:*?"<>|\0')

#: How a missing boto3 is reported. One message, used everywhere, because the
#: fix is always the same and the MVP legitimately runs without the package.
_BOTO3_HINT = (
    "boto3 is required for OpenINTEL S3 access but is not installed. "
    "Install it with: pip install boto3"
)


# --------------------------------------------------------------------------- #
# Small internal helpers
# --------------------------------------------------------------------------- #


def _validate_component(value: Any, kind: str) -> str:
    """Return ``value`` as a path/prefix-safe component, or raise.

    Sources really do contain dots (``fed.us``), so dots are allowed; anything
    that could act as a separator, a drive marker or a traversal step is not.
    """
    text = str(value).strip()
    if not text:
        raise PipelineError(f"{kind} must be a non-empty string.")
    if text in {".", ".."}:
        raise PipelineError(f"{kind} must not be {text!r}.")
    bad = sorted({ch for ch in text if ch in _UNSAFE_PATH_CHARS})
    if bad:
        raise PipelineError(
            f"{kind} {text!r} contains character(s) that are unsafe in an S3 "
            f"prefix or a file name: {' '.join(repr(c) for c in bad)}."
        )
    return text


def _sql_literal(value: Any) -> str:
    """Quote a value as a SQL string literal.

    A single quote would terminate the literal early. Rather than escape it and
    hope, such values are refused: no OpenINTEL key or endpoint contains one,
    so a value that does is a bug worth surfacing.
    """
    text = str(value)
    if "'" in text:
        raise PipelineError(
            f"Refusing to build SQL for a value containing a single quote: {text!r}."
        )
    return f"'{text}'"


def _as_date(value: Any, *, label: str) -> date:
    """Coerce ``datetime`` / ``date`` / ``"YYYY-MM-DD"`` to a plain date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return parse_timestamp(value).date()
    except PipelineError as exc:
        raise PipelineError(f"{label} is not a usable date: {value!r} ({exc})") from exc


def date_range(start: Any, end: Any) -> list[date]:
    """Every calendar day from ``start`` to ``end``, inclusive.

    Inclusive because a user asking for ``2018-05-01 .. 2018-05-31`` means the
    whole month; silently dropping the last day would under-count adoption at
    exactly the boundary a timeline chart draws attention to.
    """
    first = _as_date(start, label="start")
    last = _as_date(end, label="end")
    if first > last:
        raise PipelineError(
            f"start ({first.isoformat()}) is after end ({last.isoformat()}); "
            "an empty date range is almost always a typo rather than an intent."
        )
    span = (last - first).days
    return [first + timedelta(days=offset) for offset in range(span + 1)]


def _endpoint_parts(endpoint: str) -> tuple[str, bool]:
    """Split an endpoint into ``(host[:port], use_ssl)``.

    DuckDB wants the bare host -- ``s3_endpoint='https://...'`` silently
    produces unreachable URLs -- while boto3 wants a full URL. Both are derived
    here from the single value the caller configured.
    """
    text = str(endpoint).strip()
    use_ssl = True
    if "://" in text:
        scheme, _, remainder = text.partition("://")
        use_ssl = scheme.strip().lower() != "http"
        text = remainder
    return text.strip("/"), use_ssl


def _key_basename(key: str) -> str:
    """The final path element of an S3 key, validated as a file name."""
    name = str(key).rsplit("/", 1)[-1].strip()
    if not name or name in {".", ".."} or "\\" in name:
        raise PipelineError(f"Object key does not end in a usable file name: {key!r}")
    return name


# --------------------------------------------------------------------------- #
# Configuration and partition identity
# --------------------------------------------------------------------------- #


@dataclass
class AccessConfig:
    """How to reach the OpenINTEL corpus, and how to read it.

    The defaults are the real public endpoint, so ``AccessConfig()`` is a
    working anonymous stream-mode configuration and callers only override what
    they actually want to change.

    ``threads`` and ``memory_limit`` are DuckDB runtime settings rather than
    access settings, but they belong to the same decision: a stream-mode run
    over a wide corpus is bounded by network parallelism and by how much of a
    row group DuckDB is willing to hold, and those have to be tunable per host
    without touching code.
    """

    mode: Literal["stream", "download"] = "stream"
    endpoint: str = DEFAULT_ENDPOINT
    bucket: str = DEFAULT_BUCKET
    region: str = DEFAULT_REGION
    cache_dir: Path | None = None
    threads: int | None = None
    memory_limit: str | None = None

    # HTTP resilience. DuckDB's defaults (3 retries, 100 ms base, backoff 4)
    # exhaust in roughly two seconds, which is tuned for a flaky link rather
    # than for a shared public object store that rate-limits. OpenINTEL returns
    # 503 under load, and on a multi-day run a two-second retry budget turns a
    # transient throttle into an aborted partition. These defaults retry for
    # about eight minutes before giving up; the checkpoint then makes a resume
    # cheap if it still fails.
    http_retries: int = 10
    http_retry_wait_ms: int = 500
    http_retry_backoff: float = 2.0
    http_timeout_seconds: int = 120

    def __post_init__(self) -> None:
        mode = str(self.mode).strip().lower()
        if mode not in MODES:
            raise PipelineError(
                f"Unknown access mode {self.mode!r}; expected one of {', '.join(MODES)}."
            )
        self.mode = mode  # type: ignore[assignment]

        self.endpoint = str(self.endpoint).strip()
        if not self.endpoint:
            raise PipelineError("AccessConfig.endpoint must be a non-empty URL or host.")
        self.bucket = _validate_component(self.bucket, "AccessConfig.bucket")
        self.region = str(self.region).strip()
        if not self.region:
            raise PipelineError("AccessConfig.region must be a non-empty string.")

        if self.cache_dir is not None:
            self.cache_dir = Path(self.cache_dir)
        elif mode == "download":
            raise PipelineError(
                "AccessConfig(mode='download') requires cache_dir=<path>: downloaded "
                "objects have to be staged somewhere the run can find them again."
            )

        if self.threads is not None:
            self.threads = int(self.threads)
            if self.threads < 1:
                raise PipelineError(f"AccessConfig.threads must be >= 1, got {self.threads}.")

        if self.memory_limit is not None:
            self.memory_limit = str(self.memory_limit).strip() or None

    @property
    def endpoint_host(self) -> str:
        """The endpoint without a scheme -- what DuckDB's ``s3_endpoint`` wants."""
        return _endpoint_parts(self.endpoint)[0]

    @property
    def use_ssl(self) -> bool:
        """True unless the endpoint was explicitly configured as ``http://``."""
        return _endpoint_parts(self.endpoint)[1]

    @property
    def endpoint_url(self) -> str:
        """The endpoint with a scheme -- what boto3's ``endpoint_url`` wants."""
        host, use_ssl = _endpoint_parts(self.endpoint)
        return f"{'https' if use_ssl else 'http'}://{host}"


@dataclass(frozen=True)
class Partition:
    """One measurement day of one source: the unit of work for a real run.

    Frozen because a partition is an identity as much as a value. It is used as
    a checkpoint key, so two objects describing the same day must be
    interchangeable and neither may drift after discovery.

    ``keys`` may be empty when a partition was discovered with
    ``require_objects=False``; in that case the reader falls back to a prefix
    glob rather than an explicit object list.
    """

    source: str
    basis: str
    date: date
    prefix: str
    keys: tuple[str, ...] = field(default=())

    @property
    def partition_id(self) -> str:
        """Stable identity, e.g. ``"zonefile/nu/2018-05-01"``.

        Every component is validated at construction time, so this is safe to
        use as a *relative* path. Use :attr:`slug` where a single flat file name
        is wanted instead.
        """
        return f"{self.basis}/{self.source}/{self.date.isoformat()}"

    @property
    def slug(self) -> str:
        """:attr:`partition_id` flattened into one file-name-safe token."""
        return self.partition_id.replace("/", "__")

    @property
    def object_count(self) -> int:
        return len(self.keys)

    def describe(self) -> str:
        """One line a human can read in a progress log."""
        objects = f"{self.object_count} object(s)" if self.keys else "no listed objects"
        return f"{self.partition_id} ({objects}) at {self.prefix}"


def partition_prefix(basis: str, source: str, day: Any) -> str:
    """Build the S3 key prefix for one (basis, source, day).

    The layout is fixed by OpenINTEL and is reproduced here exactly, including
    the zero padding: ``month=5`` is not a valid prefix and would list nothing
    at all, which is the quiet failure this whole module exists to prevent.
    """
    safe_basis = _validate_component(basis, "basis")
    safe_source = _validate_component(source, "source")
    when = _as_date(day, label="day")
    return (
        f"{FDNS_BASE}/basis={safe_basis}/source={safe_source}/"
        f"year={when.year:04d}/month={when.month:02d}/day={when.day:02d}/"
    )


# --------------------------------------------------------------------------- #
# Anonymous S3 access
# --------------------------------------------------------------------------- #


def build_s3_client(config: AccessConfig) -> Any:
    """Return an anonymous botocore S3 client pointed at OpenINTEL.

    Two details are load-bearing and both are copied from the project's
    existing, working access code:

    * ``signature_version=botocore.UNSIGNED`` -- the bucket is public and there
      are no credentials; signing an anonymous request gets it rejected.
    * unregistering ``fix_s3_host`` from ``before-sign.s3`` -- botocore's
      default handler rewrites ``object.openintel.nl`` into AWS
      virtual-host-style addressing, so without this the request goes to Amazon
      and fails with a confusing DNS or 403 error rather than an obvious one.

    Constructing a client performs no network IO; the first request does.
    """
    try:
        import boto3
        import botocore
        import botocore.config
        import botocore.utils
    except ImportError as exc:
        raise PipelineError(_BOTO3_HINT) from exc

    resource = boto3.resource(
        "s3",
        config.region,
        endpoint_url=config.endpoint_url,
        config=botocore.config.Config(signature_version=botocore.UNSIGNED),
    )
    client = resource.meta.client
    try:
        client.meta.events.unregister("before-sign.s3", botocore.utils.fix_s3_host)
    except ValueError:  # pragma: no cover - botocore normally ignores this itself
        # Already absent in this botocore version; the goal (no host rewriting)
        # is met either way, so this is not an error.
        LOGGER.debug("fix_s3_host was not registered on before-sign.s3; nothing to remove.")
    return client


def _transfer_config() -> Any:
    """Multipart settings for downloads (see :data:`_MULTIPART_CHUNKSIZE`)."""
    try:
        import boto3.s3.transfer
    except ImportError as exc:
        raise PipelineError(_BOTO3_HINT) from exc
    return boto3.s3.transfer.TransferConfig(multipart_chunksize=_MULTIPART_CHUNKSIZE)


def list_partition_keys(
    config: AccessConfig,
    prefix: str,
    *,
    client: Any | None = None,
    suffix: str = OBJECT_SUFFIX,
) -> list[str]:
    """List the measurement objects directly under ``prefix``.

    ``Delimiter="/"`` keeps the listing to the partition itself rather than
    walking everything beneath it, and the continuation token is followed to the
    end: a day with more than a thousand parts would otherwise be silently
    truncated. Only keys ending in ``suffix`` are returned, so ``_SUCCESS``
    markers and other bookkeeping objects never reach the reader.

    Returns keys in sorted order so that a run over the same partition twice
    reads its parts in the same sequence.
    """
    s3 = client if client is not None else build_s3_client(config)
    wanted = suffix.lower()

    keys: list[str] = []
    token: str | None = None
    while True:
        request: dict[str, Any] = {
            "Bucket": config.bucket,
            "Prefix": prefix,
            "Delimiter": "/",
        }
        if token:
            request["ContinuationToken"] = token

        '''
        try:
            response = s3.list_objects_v2(**request)
        except Exception as exc:  # botocore raises its own error hierarchy
            raise PipelineError(
                f"Listing s3://{config.bucket}/{prefix} at {config.endpoint_url} failed: {exc}"
            ) from exc
        '''
        wait = 30
        for attempt in range(10):
            try:
                response = s3.list_objects_v2(**request)
                break

            except Exception as exc:

                text = str(exc).lower()
                transient = (
                    "503" in text
                    or "service unavailable" in text
                    or "slow down" in text
                )

                if not transient or attempt == 9:
                    raise PipelineError(
                                    f"Listing s3://{config.bucket}/{prefix} at {config.endpoint_url} failed: {exc}"
                                ) from exc

                time.sleep(wait)
                wait *= 2


        for item in response.get("Contents", ()):
            key = str(item.get("Key", ""))
            if key.lower().endswith(wanted):
                keys.append(key)

        if not response.get("IsTruncated"):
            break
        token = response.get("NextContinuationToken")
        if not token:  # pragma: no cover - defensive; truncated without a token
            break

    return sorted(keys)


def list_sources(
    config: AccessConfig,
    basis: str = "zonefile",
    *,
    client: Any | None = None,
) -> list[str]:
    """List the sources (TLDs / zones) published under ``basis``.

    Used to turn ``--sources all`` into a concrete list, and to tell a user who
    mistyped a source what was actually available.
    """
    safe_basis = _validate_component(basis, "basis")
    s3 = client if client is not None else build_s3_client(config)
    prefix = f"{FDNS_BASE}/basis={safe_basis}/"

    sources: list[str] = []
    token: str | None = None
    while True:
        request: dict[str, Any] = {"Bucket": config.bucket, "Prefix": prefix, "Delimiter": "/"}
        if token:
            request["ContinuationToken"] = token
        try:
            response = s3.list_objects_v2(**request)
        except Exception as exc:
            raise PipelineError(
                f"Listing sources under s3://{config.bucket}/{prefix} failed: {exc}"
            ) from exc

        for entry in response.get("CommonPrefixes", ()):
            text = str(entry.get("Prefix", "")).rstrip("/")
            name = text.rsplit("source=", 1)[-1] if "source=" in text else ""
            if name:
                sources.append(name)

        if not response.get("IsTruncated"):
            break
        token = response.get("NextContinuationToken")
        if not token:  # pragma: no cover - defensive
            break

    return sorted(set(sources))


# --------------------------------------------------------------------------- #
# Partition discovery
# --------------------------------------------------------------------------- #

#: Signature of the pluggable lister used by :func:`discover_partitions`.
KeyLister = Callable[[str], Sequence[str]]


def _default_lister(config: AccessConfig) -> KeyLister:
    """A lister that builds one S3 client and reuses it for every prefix.

    Lazily, so that a caller who supplies their own lister -- a test, or a
    runner replaying a cached manifest -- never needs boto3 at all.
    """
    holder: dict[str, Any] = {}

    def listing(prefix: str) -> Sequence[str]:
        client = holder.get("client")
        if client is None:
            client = build_s3_client(config)
            holder["client"] = client
        return list_partition_keys(config, prefix, client=client)

    return listing


def discover_partitions(
    config: AccessConfig,
    sources: str | Sequence[str],
    start: Any,
    end: Any,
    *,
    basis: str = "zonefile",
    require_objects: bool = True,
    warnings: list[str] | None = None,
    lister: KeyLister | None = None,
) -> list[Partition]:
    """Enumerate the partitions covering ``sources`` over ``start .. end``.

    This lists object metadata only -- it never downloads a byte -- so it is
    cheap enough to run before committing to a multi-day scan, which is exactly
    what it is for.

    With ``require_objects=True`` (the default) a date whose prefix holds no
    ``*.gz.parquet`` object is dropped *and warned about by prefix*. That
    warning is the point of the flag: OpenINTEL coverage starts on different
    dates for different zones and has gaps, and a range that silently resolves
    to nothing is a failure mode that only becomes visible after a night of
    compute has produced an empty report. With ``require_objects=False`` the
    partition is kept with empty ``keys`` and the reader falls back to a prefix
    glob.

    ``lister`` overrides how keys are fetched; it exists so callers (and tests)
    can supply their own listing without an S3 client.

    The result is sorted by ``(basis, source, date)``: deterministic, and it
    groups a source's days together so a resumed run walks the corpus in the
    same order it did before.
    """
    collected = warnings if warnings is not None else []
    safe_basis = _validate_component(basis, "basis")

    if isinstance(sources, str):
        requested = [sources]
    else:
        requested = [str(name) for name in sources]
    if not requested:
        raise PipelineError("discover_partitions requires at least one source.")

    safe_sources: list[str] = []
    for name in requested:
        safe = _validate_component(name, "source")
        if safe not in safe_sources:
            safe_sources.append(safe)
    safe_sources.sort()

    days = date_range(start, end)
    list_keys = lister if lister is not None else _default_lister(config)

    partitions: list[Partition] = []
    empty = 0
    for source in safe_sources:
        for day in days:
            prefix = partition_prefix(safe_basis, source, day)
            keys = tuple(str(key) for key in list_keys(prefix))
            if not keys:
                empty += 1
                if require_objects:
                    warn(
                        collected,
                        f"No {OBJECT_SUFFIX} objects under s3://{config.bucket}/{prefix}; "
                        f"skipping {safe_basis}/{source}/{day.isoformat()}.",
                        LOGGER,
                    )
                    continue
                warn(
                    collected,
                    f"No {OBJECT_SUFFIX} objects under s3://{config.bucket}/{prefix}; "
                    "keeping the partition because require_objects=False.",
                    LOGGER,
                )
            partitions.append(
                Partition(
                    source=source,
                    basis=safe_basis,
                    date=day,
                    prefix=prefix,
                    keys=keys,
                )
            )

    partitions.sort(key=lambda item: (item.basis, item.source, item.date))

    if not partitions:
        warn(
            collected,
            f"Discovery found no usable partitions for basis={safe_basis}, "
            f"sources={', '.join(safe_sources)}, {days[0].isoformat()}..{days[-1].isoformat()}. "
            "Check the source names against list_sources() and the date coverage.",
            LOGGER,
        )
    else:
        LOGGER.info(
            "Discovered %d partition(s) across %d source(s) and %d day(s); "
            "%d day(s) held no objects.",
            len(partitions),
            len(safe_sources),
            len(days),
            empty,
        )
    return partitions


# --------------------------------------------------------------------------- #
# Locating a partition's data
# --------------------------------------------------------------------------- #


def _partition_cache_dir(partition: Partition, config: AccessConfig) -> Path:
    """``cache_dir/<basis>/<source>/<YYYY-MM-DD>`` for one partition."""
    if config.cache_dir is None:
        raise PipelineError(
            "AccessConfig.cache_dir is not set; download-mode access needs a "
            "directory to stage objects in."
        )
    return (
        Path(config.cache_dir)
        / partition.basis
        / partition.source
        / partition.date.isoformat()
    )


def cache_paths(partition: Partition, config: AccessConfig) -> list[Path]:
    """Where each of ``partition``'s objects lives (or would live) on disk.

    Pure path arithmetic: it does not check whether the files are there. The
    layout mirrors the S3 prefix so a cache directory can be read by eye, and so
    two sources measured on the same day never collide.
    """
    directory = _partition_cache_dir(partition, config)
    return [directory / _key_basename(key) for key in partition.keys]


def _glob_uri(partition: Partition, config: AccessConfig) -> str:
    """Prefix glob used when a partition has no enumerated object keys."""
    return f"s3://{config.bucket}/{partition.prefix}*{OBJECT_SUFFIX}"


def partition_uris(partition: Partition, config: AccessConfig) -> list[str]:
    """The scannable locations of ``partition``, one per object.

    In ``stream`` mode these are ``s3://`` URIs. In ``download`` mode they are
    local paths under the cache directory -- the *expected* paths, so
    :func:`materialize` must have run first. Keeping the two modes behind one
    function is what lets the runner build its SQL once.

    A partition discovered with ``require_objects=False`` has no keys; in stream
    mode it degrades to a prefix glob, which DuckDB expands server-side, rather
    than to an empty scan that would look like a legitimately empty day.
    """
    if config.mode == "download":
        return [path.as_posix() for path in cache_paths(partition, config)]
    if not partition.keys:
        return [_glob_uri(partition, config)]
    return [f"s3://{config.bucket}/{key}" for key in partition.keys]


def materialize(
    partition: Partition,
    config: AccessConfig,
    *,
    warnings: list[str] | None = None,
    client: Any | None = None,
) -> list[Path]:
    """Download ``partition``'s objects into the cache, and return their paths.

    Resumable by construction: an object whose destination already exists with a
    non-zero size is left alone. A partition is hundreds of megabytes and a
    range is thousands of partitions, so re-fetching what is already on disk is
    not a minor inefficiency -- it is the difference between resuming a run and
    restarting it.

    Each object is written to a ``.part`` sibling and only then renamed, so an
    interrupted download can never be mistaken for a complete one on the next
    pass. A zero-byte leftover is treated as absent and re-fetched.
    """
    collected = warnings if warnings is not None else []
    directory = ensure_dir(_partition_cache_dir(partition, config))

    if not partition.keys:
        warn(
            collected,
            f"Partition {partition.partition_id} has no object keys to download "
            f"({partition.prefix}); nothing was materialized.",
            LOGGER,
        )
        return []

    s3 = client if client is not None else build_s3_client(config)
    transfer = _transfer_config()

    downloaded: list[Path] = []
    for key in partition.keys:
        destination = directory / _key_basename(key)
        if destination.is_file() and destination.stat().st_size > 0:
            LOGGER.info(
                "Already cached, skipping download: %s (%.1f MiB).",
                destination.name,
                destination.stat().st_size / (1024 * 1024),
            )
            downloaded.append(destination)
            continue

        partial = destination.with_name(destination.name + ".part")
        if partial.exists():
            partial.unlink()
        try:
            s3.download_file(
                Bucket=config.bucket,
                Key=key,
                Filename=str(partial),
                Config=transfer,
            )
        except Exception as exc:
            if partial.exists():
                partial.unlink()
            raise PipelineError(
                f"Downloading s3://{config.bucket}/{key} into {directory} failed: {exc}"
            ) from exc

        os.replace(partial, destination)
        LOGGER.info(
            "Downloaded %s (%.1f MiB) for %s.",
            destination.name,
            destination.stat().st_size / (1024 * 1024),
            partition.partition_id,
        )
        downloaded.append(destination)

    return downloaded


# --------------------------------------------------------------------------- #
# DuckDB
# --------------------------------------------------------------------------- #


def _import_duckdb() -> Any:
    try:
        import duckdb as module
    except ImportError as exc:  # pragma: no cover - duckdb is a hard dependency
        raise PipelineError(
            "DuckDB is required for real-scale OpenINTEL access. "
            "Install it with: pip install duckdb"
        ) from exc
    return module


def _apply_runtime_settings(connection: Any, config: AccessConfig) -> None:
    """Push ``threads`` / ``memory_limit`` onto a connection, when configured.

    Left untouched when unset: DuckDB's own defaults are derived from the host
    and are a better guess than anything hard-coded here.
    """
    if config.threads is not None:
        connection.execute(f"SET threads={int(config.threads)}")
        LOGGER.info("DuckDB threads set to %d.", config.threads)
    if config.memory_limit:
        connection.execute(f"SET memory_limit={_sql_literal(config.memory_limit)}")
        LOGGER.info("DuckDB memory_limit set to %s.", config.memory_limit)


def configure_duckdb_s3(connection: Any, config: AccessConfig) -> None:
    """Teach a DuckDB connection to read OpenINTEL's bucket anonymously.

    Loads ``httpfs``, then registers anonymous, path-style access to the
    configured endpoint. Two mechanisms exist and which one is available depends
    on the DuckDB build, so both are attempted in order and the one that was
    used is logged -- when a stream-mode run cannot see the bucket, the first
    question is always which of these took effect.

    ``CREATE OR REPLACE SECRET`` is preferred: it is the current API, it scopes
    the settings to S3 URLs instead of the whole connection, and re-configuring
    a connection replaces the secret rather than layering onto it. The legacy
    ``SET s3_*`` pragmas are the fallback.

    The endpoint is passed as a bare host. A scheme in ``s3_endpoint`` produces
    URLs DuckDB cannot resolve, and it fails as a generic HTTP error rather than
    as anything that points back here.
    """
    try:
        connection.execute("INSTALL httpfs")
    except Exception as exc:
        # Offline hosts often have the extension already unpacked; LOAD below
        # decides whether that is the case, so this is informational only.
        LOGGER.info("INSTALL httpfs did not run (%s); trying LOAD anyway.", exc)
    try:
        connection.execute("LOAD httpfs")
    except Exception as exc:
        raise PipelineError(
            "DuckDB could not load the httpfs extension, which stream mode needs "
            f"to read s3:// URIs ({exc}). Install it once on a connected host, or "
            "use mode='download'."
        ) from exc

    host = config.endpoint_host
    use_ssl = "true" if config.use_ssl else "false"

    secret_sql = (
        f"CREATE OR REPLACE SECRET {SECRET_NAME} ("
        "TYPE s3, "
        "PROVIDER config, "
        "KEY_ID '', "
        "SECRET '', "
        f"REGION {_sql_literal(config.region)}, "
        f"ENDPOINT {_sql_literal(host)}, "
        "URL_STYLE 'path', "
        f"USE_SSL {use_ssl}"
        ")"
    )
    try:
        connection.execute(secret_sql)
    except Exception as exc:
        LOGGER.info(
            "CREATE SECRET is unavailable on this DuckDB build (%s); "
            "falling back to the legacy SET s3_* pragmas.",
            exc,
        )
        try:
            connection.execute(f"SET s3_endpoint={_sql_literal(host)}")
            connection.execute(f"SET s3_region={_sql_literal(config.region)}")
            connection.execute("SET s3_url_style='path'")
            connection.execute(f"SET s3_use_ssl={use_ssl}")
            # Empty credentials are how the legacy pragmas express "anonymous".
            connection.execute("SET s3_access_key_id=''")
            connection.execute("SET s3_secret_access_key=''")
        except Exception as fallback_exc:
            raise PipelineError(
                "DuckDB accepted neither CREATE SECRET nor the legacy SET s3_* "
                f"pragmas for anonymous access to {host}: {fallback_exc}"
            ) from fallback_exc
        LOGGER.info(
            "Configured anonymous path-style S3 access to %s via legacy SET s3_* pragmas.",
            host,
        )
    else:
        LOGGER.info(
            "Configured anonymous path-style S3 access to %s via CREATE OR REPLACE SECRET %s.",
            host,
            SECRET_NAME,
        )

    _apply_http_resilience(connection, config)
    _apply_runtime_settings(connection, config)


def _apply_http_resilience(
    connection: duckdb.DuckDBPyConnection, config: AccessConfig
) -> None:
    """Widen DuckDB's HTTP retry budget for a long run against a shared store.

    OpenINTEL is a public, shared object store and returns 503 under load. Out
    of the box DuckDB gives up after about two seconds of retrying, so a routine
    throttle aborts the partition. Each setting is applied independently and a
    build that does not recognise one is not an error -- the names have changed
    across DuckDB versions, and losing a tuning knob is not worth failing a run
    that would otherwise work.
    """
    settings = {
        "http_retries": int(config.http_retries),
        "http_retry_wait_ms": int(config.http_retry_wait_ms),
        "http_retry_backoff": float(config.http_retry_backoff),
        "http_timeout": int(config.http_timeout_seconds),
    }
    applied: list[str] = []
    for name, value in settings.items():
        try:
            connection.execute(f"SET {name}={value}")
        except Exception as exc:  # unknown on this build; keep going
            LOGGER.debug("DuckDB rejected SET %s=%s (%s)", name, value, exc)
            continue
        applied.append(f"{name}={value}")

    if applied:
        LOGGER.info("HTTP resilience: %s.", ", ".join(applied))
    else:  # pragma: no cover - only on a build with none of these settings
        LOGGER.warning(
            "This DuckDB build accepted none of the HTTP retry settings; a "
            "transient 503 from the object store will abort the partition. "
            "Completed partitions are still checkpointed, so a re-run resumes."
        )


def open_duckdb(config: AccessConfig) -> duckdb.DuckDBPyConnection:
    """Return an in-memory DuckDB connection configured for ``config``.

    Stream mode gets ``httpfs`` and the anonymous S3 credentials; download mode
    does not, because a local scan should not require an extension the host may
    not have. Both get the configured ``threads`` / ``memory_limit``.

    The progress bar is switched off. It renders ANSI carriage-return frames to
    stdout, and a run of this length is watched through a log file, where those
    frames turn a readable log into tens of thousands of unusable characters.
    A caller that wants it back can re-enable it on the returned connection.
    """
    duckdb_module = _import_duckdb()
    connection = duckdb_module.connect(database=":memory:")
    try:
        try:
            connection.execute("SET enable_progress_bar=false")
        except Exception as exc:  # pragma: no cover - setting exists in all builds
            LOGGER.debug("Could not disable the DuckDB progress bar: %s", exc)

        if config.mode == "stream":
            configure_duckdb_s3(connection, config)
        else:
            _apply_runtime_settings(connection, config)
    except Exception:
        connection.close()
        raise
    return connection


# --------------------------------------------------------------------------- #
# Metadata probes
# --------------------------------------------------------------------------- #


def _probe_target(partition: Partition, config: AccessConfig) -> str:
    """The single object a metadata probe should open."""
    uris = partition_uris(partition, config)
    if not uris:
        raise PipelineError(
            f"Partition {partition.partition_id} has no readable objects "
            f"({partition.prefix}); nothing to probe."
        )
    target = uris[0]
    if config.mode == "download" and not Path(target).is_file():
        raise PipelineError(
            f"{target} is not on disk. In download mode, call materialize() for "
            f"{partition.partition_id} before probing its schema."
        )
    return target


def probe_schema(
    partition: Partition,
    config: AccessConfig,
    *,
    dictionary: OpenINTELDictionary | None = None,
    needed_fields: Sequence[str] | None = None,
    connection: Any | None = None,
) -> dict[str, Any]:
    """Report the real columns of one object in ``partition``.

    Metadata only: the Parquet footer of a single object, never its data. That
    is what makes it affordable to run before a long job, and running it before
    a long job is the entire point -- the corpus spans a decade of measurement
    generations, and a normalized field that resolves against 2022 data may
    resolve against nothing in 2015. Finding that out from a footer costs
    seconds; finding it out from an empty report costs a night.

    Pass ``dictionary`` and ``needed_fields`` to also get the alias resolution
    the reader would perform, under ``resolved`` (normalized field -> candidate
    columns, in priority order) and ``unresolved_fields``. Resolution is
    delegated to :func:`~openintel_rfc.parquet_reader.resolve_column_candidates`
    so that a probe and an actual scan can never disagree.

    The returned dict separates ``file_columns`` from ``hive_columns``: DuckDB
    reconstructs ``basis``/``source``/``year``/``month``/``day`` from the path,
    so they are queryable in a scan even though the file itself does not carry
    them. That distinction is not cosmetic. Those five columns exist only in
    stream mode -- the download cache deliberately stores objects under
    ``<basis>/<source>/<YYYY-MM-DD>/``, which has no ``key=value`` segments and
    therefore yields no Hive columns -- and DuckDB types them by guessing from
    the literal path text, so on the real corpus ``year`` binds as BIGINT while
    ``month`` and ``day`` bind as VARCHAR (their values carry a leading zero).
    A normalized field whose candidate list mixes a file column with a Hive
    column can therefore fail to bind at all. ``hive_derived_candidates``
    reports exactly which fields are in that position, so the caller can decide
    what to do about it before, rather than during, a long run.
    """
    target = _probe_target(partition, config)
    literal = _sql_literal(target)

    owned = connection is None
    duckdb_connection = connection if connection is not None else open_duckdb(config)
    try:
        try:
            described = duckdb_connection.execute(
                f"DESCRIBE SELECT * FROM read_parquet({literal})"
            ).fetchall()
        except Exception as exc:
            raise PipelineError(f"Could not read the Parquet schema of {target}: {exc}") from exc

        # parquet_schema() reports the physical file schema; its first row is the
        # schema root (a group node with no type), which is not a column.
        try:
            physical = duckdb_connection.execute(
                f"SELECT name, type FROM parquet_schema({literal})"
            ).fetchall()
        except Exception as exc:  # pragma: no cover - DESCRIBE would have failed first
            LOGGER.info("parquet_schema(%s) failed (%s); reporting DESCRIBE only.", target, exc)
            physical = []

        row_count: int | None = None
        row_group_count: int | None = None
        try:
            meta = duckdb_connection.execute(
                f"SELECT num_rows, num_row_groups FROM parquet_file_metadata({literal})"
            ).fetchone()
            if meta is not None:
                row_count = int(meta[0])
                row_group_count = int(meta[1])
        except Exception as exc:
            LOGGER.info("parquet_file_metadata(%s) is unavailable: %s", target, exc)
    finally:
        if owned:
            duckdb_connection.close()

    columns = [{"name": str(row[0]), "type": str(row[1])} for row in described]
    column_names = [column["name"] for column in columns]
    file_columns = [str(row[0]) for row in physical if row[1] is not None]
    file_column_set = set(file_columns)
    hive_columns = (
        [name for name in column_names if name not in file_column_set] if file_columns else []
    )

    report: dict[str, Any] = {
        "partition_id": partition.partition_id,
        "basis": partition.basis,
        "source": partition.source,
        "date": partition.date.isoformat(),
        "mode": config.mode,
        "uri": target,
        "object_count": partition.object_count,
        "columns": columns,
        "column_names": column_names,
        "file_columns": file_columns,
        "hive_columns": hive_columns,
        "row_count": row_count,
        "row_group_count": row_group_count,
        "resolved": None,
        "unresolved_fields": None,
        "hive_derived_candidates": None,
    }

    if dictionary is not None and needed_fields is not None:
        resolved = resolve_column_candidates(dictionary, list(needed_fields), column_names)
        report["resolved"] = resolved
        report["unresolved_fields"] = sorted(
            field_name for field_name, candidates in resolved.items() if not candidates
        )

        hive_set = set(hive_columns)
        shadowed = {
            field_name: [column for column in candidates if column in hive_set]
            for field_name, candidates in resolved.items()
            if any(column in hive_set for column in candidates)
        }
        report["hive_derived_candidates"] = shadowed
        for field_name, columns in sorted(shadowed.items()):
            if len(resolved[field_name]) > len(columns):
                # A mixed file/path candidate list is the dangerous shape: the
                # two sets have unrelated physical types and coalescing them
                # without a cast is a bind error rather than a wrong answer.
                LOGGER.warning(
                    "Normalized field '%s' draws on both file columns and "
                    "path-derived columns (%s) in %s; coalescing them needs an "
                    "explicit cast.",
                    field_name,
                    ", ".join(columns),
                    target,
                )

    return report


def estimate_partition_rows(
    partition: Partition,
    config: AccessConfig,
    *,
    connection: Any | None = None,
) -> int | None:
    """Total rows in ``partition``, from Parquet footers alone.

    Returns ``None`` rather than raising when the footers cannot be read: a
    row estimate is used for progress reporting and for ordering work, and a
    run must not fall over because one metadata query timed out. A caller that
    needs certainty should scan.
    """
    uris = partition_uris(partition, config)
    if not uris:
        return None

    owned = connection is None
    duckdb_connection = connection if connection is not None else open_duckdb(config)
    total = 0
    try:
        for uri in uris:
            literal = _sql_literal(uri)
            try:
                row = duckdb_connection.execute(
                    f"SELECT sum(num_rows) FROM parquet_file_metadata({literal})"
                ).fetchone()
            except Exception as exc:
                LOGGER.info(
                    "Row estimate for %s failed on %s: %s", partition.partition_id, uri, exc
                )
                return None
            if row is None or row[0] is None:
                return None
            total += int(row[0])
    finally:
        if owned:
            duckdb_connection.close()
    return total
