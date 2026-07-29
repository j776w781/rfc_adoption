"""Partition discovery and access against the real OpenINTEL corpus layout.

These tests never touch the network. Everything that would need it is either
driven by a fake lister/client, or exercised against a local copy of the
committed sample Parquet file staged into a cache directory -- which is a real
test of the download-mode code path, because in that mode the reader genuinely
is looking at a local file.

The one test that does reach OpenINTEL is marked ``network`` *and* gated behind
an environment variable, so a default ``pytest`` run stays offline. The marker
is registered below rather than in ``pyproject.toml`` because this file owns it.

What is worth testing here is narrow but unforgiving:

* the S3 prefix must be byte-exact, zero padding included -- ``month=5`` lists
  nothing at all, and a range that silently resolves to nothing is the failure
  mode this module exists to prevent;
* ``require_objects`` must warn *by prefix* when it drops a day, for the same
  reason;
* the download cache must skip what it already has, or a resumed multi-day run
  is a restarted one;
* and none of it may require boto3 to import, because the MVP does not use S3.
"""

from __future__ import annotations

import importlib
import sys
import warnings
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

import openintel_rfc
from openintel_rfc import openintel_source
from openintel_rfc.models import OpenINTELDictionary
from openintel_rfc.openintel_source import (
    DEFAULT_BUCKET,
    DEFAULT_ENDPOINT,
    OBJECT_SUFFIX,
    SECRET_NAME,
    AccessConfig,
    Partition,
    build_s3_client,
    cache_paths,
    configure_duckdb_s3,
    date_range,
    discover_partitions,
    estimate_partition_rows,
    list_partition_keys,
    list_sources,
    materialize,
    open_duckdb,
    partition_prefix,
    partition_uris,
    probe_schema,
)
from openintel_rfc.parquet_reader import describe_parquet
from openintel_rfc.utils import PipelineError

# ``pytest.mark.network`` is declared by this module alone, so it is registered
# here. There is no hook a test module can use to add a marker to the session
# config, so the unknown-marker warning is suppressed directly; the marker still
# works for ``-m network`` selection.
warnings.filterwarnings("ignore", category=pytest.PytestUnknownMarkWarning)

#: Real objects verified to exist in the public bucket, used by the gated probe.
KNOWN_SOURCE = "nu"
KNOWN_DATE = date(2018, 5, 1)
KNOWN_PREFIX = "fdns/basis=zonefile/source=nu/year=2018/month=05/day=01/"
KNOWN_KEY = KNOWN_PREFIX + "part-00000-fde3742b-5e81-4652-9ac2-5bfd9d813637-c000.gz.parquet"

#: Opt-in switch for the single read-only live probe.
NETWORK_ENV = "OPENINTEL_NETWORK_TESTS"

requires_network = pytest.mark.skipif(
    "1" != __import__("os").environ.get(NETWORK_ENV, ""),
    reason=f"set {NETWORK_ENV}=1 to run the read-only OpenINTEL probe",
)


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #


class FakeS3:
    """The slice of the botocore S3 client this module actually uses.

    Records every call so tests can assert *how* the bucket was queried, not
    merely what came back: ``Delimiter='/'`` and continuation-token following
    are both correctness requirements rather than implementation details.
    """

    def __init__(
        self,
        contents: dict[str, list[str]] | None = None,
        common_prefixes: dict[str, list[str]] | None = None,
        pages: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.contents = contents or {}
        self.common_prefixes = common_prefixes or {}
        self.pages = pages or {}
        self.list_calls: list[dict[str, Any]] = []
        self.downloads: list[str] = []

    def list_objects_v2(self, **kwargs: Any) -> dict[str, Any]:
        self.list_calls.append(dict(kwargs))
        prefix = kwargs.get("Prefix", "")

        scripted = self.pages.get(prefix)
        if scripted is not None:
            token = kwargs.get("ContinuationToken")
            index = 0 if token is None else next(
                i for i, page in enumerate(scripted) if page.get("_token") == token
            )
            page = dict(scripted[index])
            page.pop("_token", None)
            return page

        response: dict[str, Any] = {"IsTruncated": False}
        keys = self.contents.get(prefix)
        if keys:
            response["Contents"] = [{"Key": key, "Size": 1} for key in keys]
        prefixes = self.common_prefixes.get(prefix)
        if prefixes:
            response["CommonPrefixes"] = [{"Prefix": value} for value in prefixes]
        return response

    def download_file(self, **kwargs: Any) -> None:
        key = kwargs["Key"]
        filename = Path(kwargs["Filename"])
        self.downloads.append(key)
        filename.write_bytes(b"parquet-bytes-for-" + key.encode("utf-8"))


def lister_from(mapping: dict[str, list[str]]):
    """A ``discover_partitions`` lister backed by a plain dict of prefix -> keys."""
    seen: list[str] = []

    def listing(prefix: str) -> list[str]:
        seen.append(prefix)
        return list(mapping.get(prefix, ()))

    listing.seen = seen  # type: ignore[attr-defined]
    return listing


@pytest.fixture
def stream_config() -> AccessConfig:
    return AccessConfig()


@pytest.fixture
def download_config(tmp_path: Path) -> AccessConfig:
    return AccessConfig(mode="download", cache_dir=tmp_path / "cache")


def make_partition(
    *,
    source: str = "nu",
    basis: str = "zonefile",
    day: date = KNOWN_DATE,
    keys: tuple[str, ...] = (KNOWN_KEY,),
) -> Partition:
    return Partition(
        source=source,
        basis=basis,
        date=day,
        prefix=partition_prefix(basis, source, day),
        keys=keys,
    )


# --------------------------------------------------------------------------- #
# Prefix construction
# --------------------------------------------------------------------------- #


def test_partition_prefix_matches_the_published_layout_exactly() -> None:
    assert partition_prefix("zonefile", "nu", date(2018, 5, 1)) == KNOWN_PREFIX
    assert (
        partition_prefix("toplist", "alexa", date(2022, 12, 31))
        == "fdns/basis=toplist/source=alexa/year=2022/month=12/day=31/"
    )


def test_partition_prefix_zero_pads_month_and_day() -> None:
    # ``month=5`` is not a prefix that exists; an unpadded component lists
    # nothing and the run looks like an empty measurement day.
    prefix = partition_prefix("zonefile", "se", date(2021, 1, 2))
    assert "/year=2021/month=01/day=02/" in prefix
    assert "month=1" not in prefix and "day=2/" not in prefix


def test_partition_prefix_accepts_dates_datetimes_and_strings() -> None:
    expected = partition_prefix("zonefile", "nu", date(2018, 5, 1))
    assert partition_prefix("zonefile", "nu", datetime(2018, 5, 1, 13, 45)) == expected
    assert partition_prefix("zonefile", "nu", "2018-05-01") == expected


def test_partition_prefix_allows_dotted_sources() -> None:
    # ``fed.us`` is a real published source; dots must not be rejected.
    assert "source=fed.us/" in partition_prefix("zonefile", "fed.us", date(2020, 6, 1))


@pytest.mark.parametrize("bad", ["", "   ", "..", "nu/se", "nu=se", "a\\b", "n*"])
def test_partition_prefix_rejects_separator_like_sources(bad: str) -> None:
    with pytest.raises(PipelineError):
        partition_prefix("zonefile", bad, date(2018, 5, 1))


# --------------------------------------------------------------------------- #
# Partition identity
# --------------------------------------------------------------------------- #


def test_partition_id_is_stable_and_human_readable() -> None:
    partition = make_partition()
    assert partition.partition_id == "zonefile/nu/2018-05-01"
    # Identity must not depend on which objects happened to be listed.
    without_keys = make_partition(keys=())
    assert without_keys.partition_id == partition.partition_id


def test_partition_id_is_filesystem_safe(tmp_path: Path) -> None:
    partition = make_partition(source="fed.us", basis="toplist")
    identifier = partition.partition_id
    assert identifier == "toplist/fed.us/2018-05-01"

    # Safe as a relative path: it stays inside the directory it is joined to.
    target = (tmp_path / identifier).resolve()
    assert target.is_relative_to(tmp_path.resolve())

    # And safe as a single flat file name.
    assert "/" not in partition.slug and "\\" not in partition.slug
    checkpoint = tmp_path / f"{partition.slug}.json"
    checkpoint.write_text("{}", encoding="utf-8")
    assert checkpoint.is_file()


def test_partition_is_frozen_and_hashable() -> None:
    partition = make_partition()
    assert hash(partition) == hash(make_partition())
    with pytest.raises(Exception):
        partition.source = "se"  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# Dates
# --------------------------------------------------------------------------- #


def test_date_range_is_inclusive_of_both_ends() -> None:
    days = date_range("2018-05-01", "2018-05-03")
    assert days == [date(2018, 5, 1), date(2018, 5, 2), date(2018, 5, 3)]
    assert date_range(date(2020, 2, 28), datetime(2020, 3, 1)) == [
        date(2020, 2, 28),
        date(2020, 2, 29),
        date(2020, 3, 1),
    ]


def test_date_range_rejects_start_after_end() -> None:
    with pytest.raises(PipelineError) as excinfo:
        date_range("2018-05-02", "2018-05-01")
    message = str(excinfo.value)
    assert "2018-05-02" in message and "2018-05-01" in message


def test_discover_partitions_rejects_start_after_end(stream_config: AccessConfig) -> None:
    with pytest.raises(PipelineError):
        discover_partitions(
            stream_config, ["nu"], "2019-01-02", "2019-01-01", lister=lister_from({})
        )


def test_date_range_rejects_unparseable_input() -> None:
    with pytest.raises(PipelineError) as excinfo:
        date_range("not-a-date", "2018-05-01")
    assert "start" in str(excinfo.value)


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #


def test_discover_partitions_lists_every_day_without_downloading(
    stream_config: AccessConfig,
) -> None:
    prefixes = {
        partition_prefix("zonefile", "nu", day): [
            partition_prefix("zonefile", "nu", day) + "part-00000-c000.gz.parquet"
        ]
        for day in date_range("2018-05-01", "2018-05-03")
    }
    lister = lister_from(prefixes)

    partitions = discover_partitions(
        stream_config, ["nu"], "2018-05-01", "2018-05-03", lister=lister
    )

    assert [p.partition_id for p in partitions] == [
        "zonefile/nu/2018-05-01",
        "zonefile/nu/2018-05-02",
        "zonefile/nu/2018-05-03",
    ]
    assert lister.seen == sorted(prefixes)  # type: ignore[attr-defined]
    assert all(p.keys for p in partitions)


def test_discover_partitions_is_sorted_by_basis_source_then_date(
    stream_config: AccessConfig,
) -> None:
    mapping: dict[str, list[str]] = {}
    for source in ("se", "nu"):
        for day in date_range("2019-01-01", "2019-01-02"):
            prefix = partition_prefix("zonefile", source, day)
            mapping[prefix] = [prefix + "part-00000-c000.gz.parquet"]

    partitions = discover_partitions(
        stream_config, ["se", "nu", "nu"], "2019-01-01", "2019-01-02", lister=lister_from(mapping)
    )

    assert [p.partition_id for p in partitions] == [
        "zonefile/nu/2019-01-01",
        "zonefile/nu/2019-01-02",
        "zonefile/se/2019-01-01",
        "zonefile/se/2019-01-02",
    ]


def test_require_objects_skips_empty_days_and_names_the_prefix(
    stream_config: AccessConfig,
) -> None:
    present = partition_prefix("zonefile", "nu", date(2018, 5, 1))
    missing = partition_prefix("zonefile", "nu", date(2018, 5, 2))
    lister = lister_from({present: [present + "part-00000-c000.gz.parquet"]})

    collected: list[str] = []
    partitions = discover_partitions(
        stream_config,
        ["nu"],
        "2018-05-01",
        "2018-05-02",
        require_objects=True,
        warnings=collected,
        lister=lister,
    )

    assert [p.partition_id for p in partitions] == ["zonefile/nu/2018-05-01"]
    # The warning has to name the prefix: "nothing matched" is only actionable
    # if the reader can see which prefix was searched.
    assert any(missing in message for message in collected)
    assert not any(present in message for message in collected)


def test_require_objects_false_keeps_empty_partitions_but_still_warns(
    stream_config: AccessConfig,
) -> None:
    collected: list[str] = []
    partitions = discover_partitions(
        stream_config,
        ["nu"],
        "2018-05-01",
        "2018-05-01",
        require_objects=False,
        warnings=collected,
        lister=lister_from({}),
    )

    assert len(partitions) == 1
    assert partitions[0].keys == ()
    assert collected and "require_objects=False" in collected[-1]


def test_discovery_over_an_entirely_empty_range_warns_loudly(
    stream_config: AccessConfig,
) -> None:
    collected: list[str] = []
    partitions = discover_partitions(
        stream_config,
        ["nu", "se"],
        "2005-01-01",
        "2005-01-02",
        warnings=collected,
        lister=lister_from({}),
    )

    assert partitions == []
    assert any("no usable partitions" in message for message in collected)


def test_discover_partitions_requires_at_least_one_source(
    stream_config: AccessConfig,
) -> None:
    with pytest.raises(PipelineError):
        discover_partitions(stream_config, [], "2018-05-01", "2018-05-01", lister=lister_from({}))


def test_discover_partitions_accepts_a_bare_source_string(
    stream_config: AccessConfig,
) -> None:
    prefix = partition_prefix("zonefile", "nu", date(2018, 5, 1))
    partitions = discover_partitions(
        stream_config,
        "nu",
        "2018-05-01",
        "2018-05-01",
        lister=lister_from({prefix: [prefix + "part-00000-c000.gz.parquet"]}),
    )
    assert [p.source for p in partitions] == ["nu"]


# --------------------------------------------------------------------------- #
# Listing (fake client)
# --------------------------------------------------------------------------- #


def test_list_partition_keys_uses_a_delimiter_and_filters_by_suffix(
    stream_config: AccessConfig,
) -> None:
    client = FakeS3(
        contents={
            KNOWN_PREFIX: [
                KNOWN_PREFIX + "part-00001-c000.gz.parquet",
                KNOWN_PREFIX + "_SUCCESS",
                KNOWN_PREFIX + "part-00000-c000.gz.parquet",
            ]
        }
    )

    keys = list_partition_keys(stream_config, KNOWN_PREFIX, client=client)

    assert keys == [
        KNOWN_PREFIX + "part-00000-c000.gz.parquet",
        KNOWN_PREFIX + "part-00001-c000.gz.parquet",
    ]
    assert client.list_calls[0]["Delimiter"] == "/"
    assert client.list_calls[0]["Bucket"] == DEFAULT_BUCKET
    assert client.list_calls[0]["Prefix"] == KNOWN_PREFIX


def test_list_partition_keys_follows_continuation_tokens(
    stream_config: AccessConfig,
) -> None:
    client = FakeS3(
        pages={
            KNOWN_PREFIX: [
                {
                    "Contents": [{"Key": KNOWN_PREFIX + "part-00000-c000.gz.parquet"}],
                    "IsTruncated": True,
                    "NextContinuationToken": "page-2",
                },
                {
                    "_token": "page-2",
                    "Contents": [{"Key": KNOWN_PREFIX + "part-00001-c000.gz.parquet"}],
                    "IsTruncated": False,
                },
            ]
        }
    )

    keys = list_partition_keys(stream_config, KNOWN_PREFIX, client=client)

    assert len(keys) == 2, "a truncated listing must not silently drop later parts"
    assert client.list_calls[1]["ContinuationToken"] == "page-2"


def test_list_partition_keys_wraps_client_errors(stream_config: AccessConfig) -> None:
    class Broken:
        def list_objects_v2(self, **_: Any) -> dict[str, Any]:
            raise RuntimeError("connection reset")

    with pytest.raises(PipelineError) as excinfo:
        list_partition_keys(stream_config, KNOWN_PREFIX, client=Broken())
    assert KNOWN_PREFIX in str(excinfo.value)


def test_list_sources_parses_source_out_of_common_prefixes(
    stream_config: AccessConfig,
) -> None:
    client = FakeS3(
        common_prefixes={
            "fdns/basis=zonefile/": [
                "fdns/basis=zonefile/source=se/",
                "fdns/basis=zonefile/source=nu/",
                "fdns/basis=zonefile/source=fed.us/",
            ]
        }
    )

    assert list_sources(stream_config, "zonefile", client=client) == ["fed.us", "nu", "se"]


# --------------------------------------------------------------------------- #
# URIs and cache layout
# --------------------------------------------------------------------------- #


def test_stream_mode_yields_one_s3_uri_per_object(stream_config: AccessConfig) -> None:
    partition = make_partition(keys=(KNOWN_PREFIX + "a.gz.parquet", KNOWN_PREFIX + "b.gz.parquet"))
    assert partition_uris(partition, stream_config) == [
        f"s3://{DEFAULT_BUCKET}/{KNOWN_PREFIX}a.gz.parquet",
        f"s3://{DEFAULT_BUCKET}/{KNOWN_PREFIX}b.gz.parquet",
    ]


def test_stream_mode_falls_back_to_a_prefix_glob_without_keys(
    stream_config: AccessConfig,
) -> None:
    uris = partition_uris(make_partition(keys=()), stream_config)
    assert uris == [f"s3://{DEFAULT_BUCKET}/{KNOWN_PREFIX}*{OBJECT_SUFFIX}"]


def test_download_mode_cache_layout_is_basis_source_date(
    download_config: AccessConfig,
) -> None:
    partition = make_partition(keys=(KNOWN_KEY,))
    paths = cache_paths(partition, download_config)

    assert len(paths) == 1
    assert paths[0] == (
        download_config.cache_dir
        / "zonefile"
        / "nu"
        / "2018-05-01"
        / "part-00000-fde3742b-5e81-4652-9ac2-5bfd9d813637-c000.gz.parquet"
    )
    # partition_uris must agree with cache_paths, or materialize() and the scan
    # would look at different files.
    assert partition_uris(partition, download_config) == [paths[0].as_posix()]


def test_two_sources_on_one_day_do_not_collide_in_the_cache(
    download_config: AccessConfig,
) -> None:
    shared_name = "part-00000-c000.gz.parquet"
    nu = make_partition(
        source="nu", keys=(partition_prefix("zonefile", "nu", KNOWN_DATE) + shared_name,)
    )
    se = make_partition(
        source="se", keys=(partition_prefix("zonefile", "se", KNOWN_DATE) + shared_name,)
    )
    assert cache_paths(nu, download_config) != cache_paths(se, download_config)


def test_cache_paths_require_a_cache_dir(stream_config: AccessConfig) -> None:
    with pytest.raises(PipelineError) as excinfo:
        cache_paths(make_partition(), stream_config)
    assert "cache_dir" in str(excinfo.value)


# --------------------------------------------------------------------------- #
# Download mode
# --------------------------------------------------------------------------- #


@pytest.fixture
def no_transfer_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub out the boto3 TransferConfig so download tests never need boto3."""
    monkeypatch.setattr(openintel_source, "_transfer_config", lambda: None)


def test_materialize_downloads_into_the_partition_cache_directory(
    download_config: AccessConfig, no_transfer_config: None
) -> None:
    partition = make_partition(keys=(KNOWN_KEY,))
    client = FakeS3()

    paths = materialize(partition, download_config, client=client)

    assert paths == cache_paths(partition, download_config)
    assert paths[0].is_file() and paths[0].stat().st_size > 0
    assert client.downloads == [KNOWN_KEY]
    # Nothing partial is left behind.
    assert not list(paths[0].parent.glob("*.part"))


def test_materialize_skips_a_file_that_is_already_present(
    download_config: AccessConfig, no_transfer_config: None
) -> None:
    partition = make_partition(keys=(KNOWN_KEY,))
    destination = cache_paths(partition, download_config)[0]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(b"already-downloaded")

    client = FakeS3()
    paths = materialize(partition, download_config, client=client)

    assert paths == [destination]
    assert client.downloads == [], "a resumed run must not refetch a cached object"
    assert destination.read_bytes() == b"already-downloaded"


def test_materialize_refetches_a_zero_byte_leftover(
    download_config: AccessConfig, no_transfer_config: None
) -> None:
    partition = make_partition(keys=(KNOWN_KEY,))
    destination = cache_paths(partition, download_config)[0]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.touch()

    client = FakeS3()
    materialize(partition, download_config, client=client)

    assert client.downloads == [KNOWN_KEY]
    assert destination.stat().st_size > 0


def test_materialize_warns_and_returns_nothing_for_an_empty_partition(
    download_config: AccessConfig, no_transfer_config: None
) -> None:
    collected: list[str] = []
    paths = materialize(
        make_partition(keys=()), download_config, warnings=collected, client=FakeS3()
    )
    assert paths == []
    assert any("no object keys" in message for message in collected)


def test_materialize_cleans_up_after_a_failed_download(
    download_config: AccessConfig, no_transfer_config: None
) -> None:
    class Failing:
        def download_file(self, **kwargs: Any) -> None:
            Path(kwargs["Filename"]).write_bytes(b"half")
            raise RuntimeError("timed out")

    partition = make_partition(keys=(KNOWN_KEY,))
    with pytest.raises(PipelineError):
        materialize(partition, download_config, client=Failing())

    destination = cache_paths(partition, download_config)[0]
    assert not destination.exists(), "a failed download must not look complete"
    assert not list(destination.parent.glob("*.part"))


# --------------------------------------------------------------------------- #
# AccessConfig
# --------------------------------------------------------------------------- #


def test_download_mode_requires_a_cache_dir() -> None:
    with pytest.raises(PipelineError) as excinfo:
        AccessConfig(mode="download")
    assert "cache_dir" in str(excinfo.value)


def test_unknown_mode_is_rejected() -> None:
    with pytest.raises(PipelineError):
        AccessConfig(mode="ftp")  # type: ignore[arg-type]


def test_endpoint_is_split_into_a_host_for_duckdb_and_a_url_for_boto3() -> None:
    config = AccessConfig()
    assert config.endpoint == DEFAULT_ENDPOINT
    # DuckDB's s3_endpoint takes a bare host; a scheme there produces
    # unresolvable URLs and a misleading HTTP error.
    assert config.endpoint_host == "object.openintel.nl"
    assert config.use_ssl is True
    assert config.endpoint_url == DEFAULT_ENDPOINT

    plain = AccessConfig(endpoint="http://localhost:9000")
    assert plain.endpoint_host == "localhost:9000"
    assert plain.use_ssl is False
    assert plain.endpoint_url == "http://localhost:9000"


def test_cache_dir_is_coerced_to_a_path(tmp_path: Path) -> None:
    config = AccessConfig(mode="download", cache_dir=str(tmp_path))
    assert isinstance(config.cache_dir, Path)


def test_thread_count_must_be_positive() -> None:
    with pytest.raises(PipelineError):
        AccessConfig(threads=0)


# --------------------------------------------------------------------------- #
# DuckDB configuration (real in-memory connection)
# --------------------------------------------------------------------------- #


def _duckdb_or_skip():
    return pytest.importorskip("duckdb", reason="DuckDB is required for the S3 setup test")


def test_configure_duckdb_s3_registers_anonymous_path_style_access() -> None:
    duckdb = _duckdb_or_skip()
    connection = duckdb.connect(database=":memory:")
    try:
        config = AccessConfig(threads=2, memory_limit="1GB")
        try:
            configure_duckdb_s3(connection, config)
        except PipelineError as exc:
            # httpfs cannot be installed on an offline machine that has never
            # cached it. That is an environment limitation, not a failure.
            pytest.skip(f"DuckDB httpfs extension unavailable: {exc}")

        secrets = connection.execute("SELECT name, type FROM duckdb_secrets()").fetchall()
        secret_names = {str(row[0]) for row in secrets}
        endpoint_setting = connection.execute(
            "SELECT current_setting('s3_endpoint')"
        ).fetchone()[0]

        if SECRET_NAME in secret_names:
            types = {str(row[0]): str(row[1]) for row in secrets}
            assert types[SECRET_NAME] == "s3"
        else:  # legacy pragma fallback
            assert endpoint_setting == config.endpoint_host

        threads, memory = connection.execute(
            "SELECT current_setting('threads'), current_setting('memory_limit')"
        ).fetchone()
        assert int(threads) == 2
        assert str(memory) != "", "memory_limit must have been applied"
    finally:
        connection.close()


def test_configure_duckdb_s3_is_idempotent() -> None:
    duckdb = _duckdb_or_skip()
    connection = duckdb.connect(database=":memory:")
    try:
        config = AccessConfig()
        try:
            configure_duckdb_s3(connection, config)
            configure_duckdb_s3(connection, config)
        except PipelineError as exc:
            pytest.skip(f"DuckDB httpfs extension unavailable: {exc}")

        names = [
            str(row[0])
            for row in connection.execute("SELECT name FROM duckdb_secrets()").fetchall()
        ]
        assert names.count(SECRET_NAME) <= 1
    finally:
        connection.close()


def test_open_duckdb_in_download_mode_needs_no_httpfs(
    download_config: AccessConfig,
) -> None:
    _duckdb_or_skip()
    connection = open_duckdb(download_config)
    try:
        assert connection.execute("SELECT 1").fetchone()[0] == 1
        names = [
            str(row[0])
            for row in connection.execute("SELECT name FROM duckdb_secrets()").fetchall()
        ]
        assert SECRET_NAME not in names
    finally:
        connection.close()


# --------------------------------------------------------------------------- #
# Metadata probes against a locally staged object
# --------------------------------------------------------------------------- #


@pytest.fixture
def staged_partition(
    tmp_path: Path, sample_parquet_path: Path
) -> tuple[Partition, AccessConfig]:
    """The committed sample Parquet, staged as if it had been downloaded.

    Download mode really does read a local file, so this exercises the probe
    path end to end without a network round trip.
    """
    config = AccessConfig(mode="download", cache_dir=tmp_path / "cache")
    key = KNOWN_PREFIX + "part-00000-c000.gz.parquet"
    partition = make_partition(keys=(key,))
    destination = cache_paths(partition, config)[0]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(sample_parquet_path.read_bytes())
    return partition, config


def test_probe_schema_reports_real_column_names_and_row_count(
    staged_partition: tuple[Partition, AccessConfig], sample_parquet_path: Path
) -> None:
    _duckdb_or_skip()
    partition, config = staged_partition

    report = probe_schema(partition, config)

    expected = describe_parquet(sample_parquet_path)
    assert report["partition_id"] == "zonefile/nu/2018-05-01"
    assert report["mode"] == "download"
    assert report["row_count"] == expected["row_count"]
    assert report["column_names"] == [column["name"] for column in expected["columns"]]
    assert report["file_columns"] == report["column_names"]
    # No key=value segments in a cache path, so nothing is Hive-derived here.
    assert report["hive_columns"] == []


def test_probe_schema_reports_which_normalized_fields_resolve(
    staged_partition: tuple[Partition, AccessConfig], dictionary: OpenINTELDictionary
) -> None:
    _duckdb_or_skip()
    partition, config = staged_partition

    report = probe_schema(
        partition,
        config,
        dictionary=dictionary,
        needed_fields=["rr_type", "algorithm", "timestamp", "no_such_field"],
    )

    resolved = report["resolved"]
    assert resolved["rr_type"], "rr_type must resolve against the sample corpus"
    assert resolved["timestamp"]
    assert report["unresolved_fields"] == ["no_such_field"]
    # The cache layout has no ``key=value`` segments, so download mode is
    # immune to the path-derived column collision that stream mode has.
    assert report["hive_derived_candidates"] == {}


def test_probe_schema_tells_you_to_materialize_first(
    download_config: AccessConfig,
) -> None:
    _duckdb_or_skip()
    with pytest.raises(PipelineError) as excinfo:
        probe_schema(make_partition(keys=(KNOWN_KEY,)), download_config)
    assert "materialize" in str(excinfo.value)


def test_estimate_partition_rows_sums_footer_metadata(
    staged_partition: tuple[Partition, AccessConfig], sample_parquet_path: Path
) -> None:
    _duckdb_or_skip()
    partition, config = staged_partition
    expected = describe_parquet(sample_parquet_path)["row_count"]
    assert estimate_partition_rows(partition, config) == expected


def test_estimate_partition_rows_returns_none_when_metadata_is_unreadable(
    download_config: AccessConfig,
) -> None:
    _duckdb_or_skip()
    # Nothing was materialized, so the footers cannot be read; a progress
    # estimate must degrade rather than abort the run.
    assert estimate_partition_rows(make_partition(keys=(KNOWN_KEY,)), download_config) is None


# --------------------------------------------------------------------------- #
# boto3 is optional
# --------------------------------------------------------------------------- #


def _block_boto3(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``import boto3`` fail exactly as it does where it is not installed."""
    monkeypatch.setitem(sys.modules, "boto3", None)
    monkeypatch.setitem(sys.modules, "boto3.s3", None)
    monkeypatch.setitem(sys.modules, "boto3.s3.transfer", None)


def test_build_s3_client_without_boto3_names_the_install_command(
    monkeypatch: pytest.MonkeyPatch, stream_config: AccessConfig
) -> None:
    _block_boto3(monkeypatch)
    with pytest.raises(PipelineError) as excinfo:
        build_s3_client(stream_config)
    assert "pip install boto3" in str(excinfo.value)


def test_listing_without_boto3_names_the_install_command(
    monkeypatch: pytest.MonkeyPatch, stream_config: AccessConfig
) -> None:
    _block_boto3(monkeypatch)
    with pytest.raises(PipelineError) as excinfo:
        list_partition_keys(stream_config, KNOWN_PREFIX)
    assert "pip install boto3" in str(excinfo.value)


def test_materialize_without_boto3_names_the_install_command(
    monkeypatch: pytest.MonkeyPatch, download_config: AccessConfig
) -> None:
    _block_boto3(monkeypatch)
    with pytest.raises(PipelineError) as excinfo:
        materialize(make_partition(keys=(KNOWN_KEY,)), download_config, client=FakeS3())
    assert "pip install boto3" in str(excinfo.value)


def test_the_module_imports_and_plans_work_without_boto3(
    monkeypatch: pytest.MonkeyPatch, stream_config: AccessConfig
) -> None:
    # The MVP path never lists an S3 bucket, so importing this module -- and
    # everything that does not actually reach the network -- must keep working
    # on a machine that has never installed boto3.
    monkeypatch.setattr(
        openintel_rfc, "openintel_source", openintel_rfc.openintel_source, raising=False
    )
    monkeypatch.delitem(sys.modules, "openintel_rfc.openintel_source", raising=False)
    _block_boto3(monkeypatch)
    monkeypatch.setitem(sys.modules, "botocore", None)

    reimported = importlib.import_module("openintel_rfc.openintel_source")

    assert reimported.DEFAULT_BUCKET == DEFAULT_BUCKET
    prefix = reimported.partition_prefix("zonefile", "nu", date(2018, 5, 1))
    assert prefix == KNOWN_PREFIX
    partitions = reimported.discover_partitions(
        reimported.AccessConfig(),
        ["nu"],
        "2018-05-01",
        "2018-05-01",
        lister=lister_from({prefix: [prefix + "part-00000-c000.gz.parquet"]}),
    )
    assert [p.partition_id for p in partitions] == ["zonefile/nu/2018-05-01"]


# --------------------------------------------------------------------------- #
# Live probe (opt-in, read-only)
# --------------------------------------------------------------------------- #


@pytest.mark.network
@requires_network
def test_live_read_only_probe_of_a_known_partition(dictionary: OpenINTELDictionary) -> None:
    """List one known day of ``.nu`` and read that object's Parquet footer."""
    config = AccessConfig()
    partitions = discover_partitions(config, ["nu"], KNOWN_DATE, KNOWN_DATE)
    assert len(partitions) == 1

    partition = partitions[0]
    assert partition.partition_id == "zonefile/nu/2018-05-01"
    assert all(key.startswith(KNOWN_PREFIX) for key in partition.keys)
    assert all(key.endswith(OBJECT_SUFFIX) for key in partition.keys)

    report = probe_schema(
        partition,
        config,
        dictionary=dictionary,
        needed_fields=["timestamp", "domain", "zone", "rr_type", "algorithm"],
    )
    names = set(report["column_names"])
    # The columns the whole matcher depends on.
    assert {"response_type", "response_name", "timestamp"}.issubset(names)
    assert {"cds_algorithm", "dnskey_algorithm", "ds_algorithm", "rrsig_algorithm"}.issubset(names)
    # DuckDB reconstructs the partition columns from the Hive-style path.
    assert set(report["hive_columns"]) == {"basis", "source", "year", "month", "day"}
    assert report["row_count"] and report["row_count"] > 0

    # ``timestamp`` lists year/month/day as native fields, and those exist only
    # as path-derived columns here -- with VARCHAR types that cannot be
    # coalesced with the BIGINT ``timestamp``. The probe must say so.
    assert "timestamp" in report["hive_derived_candidates"]
    assert set(report["hive_derived_candidates"]["timestamp"]) == {"year", "month", "day"}
