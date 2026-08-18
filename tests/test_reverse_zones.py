"""Parsing RIPE's reverse-delegation zones into rows the existing matcher reads.

The samples here are copied from the real archive (2024-01-01), including its
whitespace and its mixed-case digests, so the parser is pinned against the data
rather than against an idealised zone file.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from openintel_rfc.reverse_zones import (
    ARCHIVE_START,
    REVERSE_BASIS,
    RIR_SOURCES,
    archive_url,
    build_frame,
    load_summaries,
    monthly_days,
    parquet_path,
    parse_zone_text,
    _write_summary,
)

# Verbatim from 20240101/afrinic/102.in-addr.arpa and .../0.c.2.ip6.arpa.
REAL_ZONE = """$TTL 172800
$ORIGIN .


; Source AFRINIC
102.in-addr.arpa.         NS        ns1.afrinic.net.
102.in-addr.arpa.         NS        ns2.afrinic.net.

; Source AFRINIC
132.23.102.in-addr.arpa.         NS        nsmaster.ndc.org.sz.
132.23.102.in-addr.arpa.         NS        ns1.ndc.org.sz.
132.23.102.in-addr.arpa.         DS        34325 13 1 fceb3fc81db52aae24ac249c0e5c4edd6ad2c7c1
132.23.102.in-addr.arpa.         DS        34325 13 2 ae1b1c839dd5d82159a78432ddb713e0bda0fb4950fb386ab820c32007df513f
132.23.102.in-addr.arpa.         DS        34325 13 4 7a29cdcfed9597b14ca4020b702ff9534771daf39aaee24c05eaf128e8cdd2d3c5882d453493a8ffc05c548c7aed607b

; Source AFRINIC
0.4.c.0.f.0.c.2.ip6.arpa.         NS        pns103.cloudns.net.
0.4.c.0.f.0.c.2.ip6.arpa.         DS        55115 13 2 3FECAAB6FAFE293F6AD5F4438F73B25B35110D60656C6F7EA5BC2456D4999ECD
AFRINIC.102.in-addr.arpa.	IN	TXT	"Generated at 2024-01-01 04:26:16Z with 4 DS records from AFRINIC."
"""


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #


def test_parses_ds_records_from_a_real_zone() -> None:
    ds_rows, delegated = parse_zone_text(REAL_ZONE)
    assert len(ds_rows) == 4
    assert ("132.23.102.in-addr.arpa", 34325, 13, 1) in ds_rows
    assert ("132.23.102.in-addr.arpa", 34325, 13, 2) in ds_rows
    assert ("132.23.102.in-addr.arpa", 34325, 13, 4) in ds_rows
    assert ("0.4.c.0.f.0.c.2.ip6.arpa", 55115, 13, 2) in ds_rows


def test_ipv6_reverse_zones_are_parsed_too() -> None:
    """The dataset is named in-addr.arpa but carries ip6.arpa delegations.

    Dropping them would silently under-report exactly the delegations most likely
    to have been signed recently.
    """
    ds_rows, delegated = parse_zone_text(REAL_ZONE)
    assert any(name.endswith("ip6.arpa") for name, _, _, _ in ds_rows)
    assert "0.4.c.0.f.0.c.2.ip6.arpa" in delegated


def test_delegations_are_deduplicated_by_name() -> None:
    """A delegation with four nameservers is one delegation.

    Counting NS records instead would make the denominator a function of how many
    nameservers operators happen to run.
    """
    _, delegated = parse_zone_text(REAL_ZONE)
    assert delegated == {
        "102.in-addr.arpa",
        "132.23.102.in-addr.arpa",
        "0.4.c.0.f.0.c.2.ip6.arpa",
    }


def test_a_txt_record_mentioning_ds_is_not_a_ds_record() -> None:
    """The archive puts a "... with N DS records ..." TXT in every zone.

    A looser pattern matches that line and inflates every count in the corpus.
    """
    ds_rows, _ = parse_zone_text(REAL_ZONE)
    assert all("afrinic.102" not in name for name, _, _, _ in ds_rows)
    assert len(ds_rows) == 4


def test_comments_and_directives_are_ignored() -> None:
    ds_rows, delegated = parse_zone_text(
        "$TTL 172800\n$ORIGIN .\n; 1.2.3.in-addr.arpa. DS 1 2 3 aa\n\n"
    )
    assert ds_rows == [] and delegated == set()


def test_optional_ttl_and_class_are_tolerated() -> None:
    ds_rows, delegated = parse_zone_text(
        "a.in-addr.arpa. 3600 IN DS 1 8 2 abcd\n"
        "b.in-addr.arpa. IN DS 2 13 1 ef01\n"
        "c.in-addr.arpa. 3600 NS ns.example.\n"
    )
    assert ("a.in-addr.arpa", 1, 8, 2) in ds_rows
    assert ("b.in-addr.arpa", 2, 13, 1) in ds_rows
    assert delegated == {"c.in-addr.arpa"}


def test_names_are_normalised_for_joining() -> None:
    """Trailing dot and case must not split one delegation into three."""
    ds_rows, delegated = parse_zone_text(
        "A.IN-ADDR.ARPA. DS 1 8 2 ab\na.in-addr.arpa. NS ns.example.\n"
    )
    assert ds_rows[0][0] == "a.in-addr.arpa"
    assert delegated == {"a.in-addr.arpa"}


def test_malformed_ds_lines_are_skipped_not_guessed_at() -> None:
    ds_rows, _ = parse_zone_text(
        "x.in-addr.arpa. DS notanumber 8 2 abcd\n"
        "y.in-addr.arpa. DS 1 8\n"
        "z.in-addr.arpa. DS 1 8 2 abcd\n"
    )
    assert ds_rows == [("z.in-addr.arpa", 1, 8, 2)]


# --------------------------------------------------------------------------- #
# The emitted frame
# --------------------------------------------------------------------------- #


def test_frame_uses_openintel_native_column_names() -> None:
    """This is the whole integration contract.

    The scan resolves `algorithm` from `ds_algorithm`, `digest_type` from
    `ds_digest_type` and so on. Rename any of these and the corpus still loads,
    still scans, and matches nothing at all.
    """
    ds_rows, delegated = parse_zone_text(REAL_ZONE)
    frame = build_frame(date(2024, 1, 1), "afrinic", ds_rows, delegated)
    for column in ("timestamp", "query_name", "response_type", "ds_algorithm",
                   "ds_digest_type", "ds_key_tag", "source"):
        assert column in frame.columns


def test_timestamp_is_epoch_milliseconds() -> None:
    """OpenINTEL's timestamps are epoch ms and the reader detects the unit by
    magnitude; emitting seconds here would land every row in 1970."""
    frame = build_frame(date(2024, 1, 1), "arin", [("a", 1, 8, 2)], ["a"])
    assert frame["timestamp"].iloc[0] == 1704067200000


def test_frame_holds_one_ns_row_per_delegation_and_one_row_per_ds() -> None:
    ds_rows, delegated = parse_zone_text(REAL_ZONE)
    frame = build_frame(date(2024, 1, 1), "afrinic", ds_rows, delegated)
    assert (frame.response_type == "DS").sum() == 4
    assert (frame.response_type == "NS").sum() == 3


def test_ns_rows_carry_no_algorithm() -> None:
    """A delegation is not a DNSSEC observation; giving it an algorithm would
    make it match RFC indicators it has no evidence for."""
    frame = build_frame(date(2024, 1, 1), "arin", [("a", 1, 8, 2)], ["a", "b"])
    ns = frame[frame.response_type == "NS"]
    assert ns.ds_algorithm.isna().all()
    assert ns.ds_digest_type.isna().all()


def test_frame_is_stable_across_runs() -> None:
    """Re-ingesting a day must not produce a different file."""
    ds_rows, delegated = parse_zone_text(REAL_ZONE)
    first = build_frame(date(2024, 1, 1), "afrinic", ds_rows, delegated)
    second = build_frame(date(2024, 1, 1), "afrinic", ds_rows, set(delegated))
    assert first.equals(second)


# --------------------------------------------------------------------------- #
# Layout and summaries
# --------------------------------------------------------------------------- #


def test_parquet_path_matches_download_mode_layout() -> None:
    path = parquet_path(date(2024, 1, 1), "arin", "/c")
    assert path.parent == Path("/c") / REVERSE_BASIS / "arin" / "2024-01-01"


def test_archive_url_is_the_published_name() -> None:
    assert archive_url(date(2024, 1, 1)).endswith("in-addr.arpa-20240101.tar.bz2")


def test_monthly_sampling_covers_every_month_once() -> None:
    days = monthly_days(date(2009, 3, 24), date(2010, 2, 28))
    assert len(days) == 11
    assert {(d.year, d.month) for d in days} == {
        (2009, m) for m in range(4, 13)
    } | {(2010, 1), (2010, 2)}


def test_archive_start_is_respected() -> None:
    assert ARCHIVE_START == date(2009, 3, 24)


def test_summary_records_the_denominator(tmp_path: Path) -> None:
    """The delegation count is why this corpus is worth having.

    The scan's record-type prefilter drops NS rows before anything is counted, so
    without this sidecar the denominator would never reach any report.
    """
    per_rir = {rir: ([], set()) for rir in RIR_SOURCES}
    per_rir["arin"] = ([("a", 1, 8, 2), ("a", 1, 8, 1), ("b", 2, 13, 2)],
                       {"a", "b", "c", "d"})
    _write_summary(date(2024, 1, 1), tmp_path, per_rir)

    loaded = load_summaries(tmp_path)
    assert len(loaded) == 1
    totals = loaded[0]["totals"]
    assert totals["delegations"] == 4
    assert totals["signed_delegations"] == 2      # 'a' and 'b', not 3 DS records
    assert totals["ds_records"] == 3
    assert totals["signed_share"] == pytest.approx(0.5)


def test_load_summaries_is_empty_when_nothing_ingested(tmp_path: Path) -> None:
    assert load_summaries(tmp_path) == []


# --------------------------------------------------------------------------- #
# Discovering a corpus that the object store never hosted
# --------------------------------------------------------------------------- #


def _seed(root: Path, basis: str, source: str, day: str) -> Path:
    directory = root / basis / source / day
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "part-00000.parquet"
    path.write_bytes(b"\x00")
    return path


def test_local_discovery_finds_an_ingested_corpus(tmp_path: Path) -> None:
    from openintel_rfc.openintel_source import discover_local_partitions

    _seed(tmp_path, "reverse", "arin", "2024-01-01")
    _seed(tmp_path, "reverse", "arin", "2024-01-02")
    found = discover_local_partitions(
        tmp_path, ["arin"], "2024-01-01", "2024-01-02", basis="reverse"
    )
    assert [p.partition_id for p in found] == [
        "reverse/arin/2024-01-01", "reverse/arin/2024-01-02"
    ]


def test_local_partitions_carry_direct_paths(tmp_path: Path) -> None:
    """Without `paths` the runner asks the object store to materialise them,
    which for this corpus means asking for objects that do not exist there."""
    from openintel_rfc.openintel_source import discover_local_partitions

    seeded = _seed(tmp_path, "reverse", "ripe", "2024-01-01")
    found = discover_local_partitions(
        tmp_path, ["ripe"], "2024-01-01", "2024-01-01", basis="reverse"
    )
    assert found[0].paths == (seeded.as_posix(),)


def test_local_discovery_warns_about_days_it_could_not_find(tmp_path: Path) -> None:
    """A range that silently resolves to fewer days is the failure mode that
    only shows up after the report is written."""
    from openintel_rfc.openintel_source import discover_local_partitions

    _seed(tmp_path, "reverse", "arin", "2024-01-01")
    warnings: list[str] = []
    found = discover_local_partitions(
        tmp_path, ["arin"], "2024-01-01", "2024-01-03",
        basis="reverse", warnings=warnings,
    )
    assert len(found) == 1
    assert any("2 source-day(s)" in w for w in warnings)


def test_local_discovery_refuses_an_empty_range(tmp_path: Path) -> None:
    from openintel_rfc.openintel_source import discover_local_partitions
    from openintel_rfc.utils import PipelineError

    with pytest.raises(PipelineError, match="No local partitions"):
        discover_local_partitions(
            tmp_path, ["arin"], "2024-01-01", "2024-01-01", basis="reverse"
        )


def test_local_discovery_ignores_non_parquet_files(tmp_path: Path) -> None:
    from openintel_rfc.openintel_source import discover_local_partitions

    directory = tmp_path / "reverse" / "arin" / "2024-01-01"
    directory.mkdir(parents=True)
    (directory / "part-00000.parquet").write_bytes(b"\x00")
    (directory / "notes.txt").write_text("ignore me")
    found = discover_local_partitions(
        tmp_path, ["arin"], "2024-01-01", "2024-01-01", basis="reverse"
    )
    assert len(found[0].paths) == 1


# --------------------------------------------------------------------------- #
# Gaps in the archive
# --------------------------------------------------------------------------- #


def test_zero_byte_archive_is_a_gap_not_a_failure(tmp_path: Path, monkeypatch) -> None:
    """RIPE publishes empty placeholders for days it has no data for.

    2009-06-01 through 06-07 are all served with HTTP 200 and zero bytes. Treating
    that as a transfer failure aborted a 57-day ingest at the third day.
    """
    import openintel_rfc.reverse_zones as rz

    class _Empty:
        # The real response really does carry Content-Length: 0 with HTTP 200.
        status = 200
        headers = {"Content-Length": "0"}
        def read(self, _n=None): return b""
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(rz.urllib.request, "urlopen", lambda *a, **k: _Empty())
    warnings: list[str] = []
    result = rz.fetch_archive(date(2009, 6, 1), tmp_path, warnings=warnings)

    assert result is None
    assert any("published but empty" in w for w in warnings)
    assert list(tmp_path.glob("*.part")) == [], "no stub left behind"


def test_unreadable_archive_costs_one_day_not_the_range(tmp_path: Path) -> None:
    """One damaged tarball must not end a multi-year ingest."""
    import openintel_rfc.reverse_zones as rz

    download_dir = tmp_path / "arch"
    download_dir.mkdir()
    bogus = rz.archive_path(date(2011, 5, 1), download_dir)
    bogus.write_bytes(b"this is not a bzip2 stream")

    warnings: list[str] = []
    result = rz.ingest_day(
        date(2011, 5, 1), cache_dir=tmp_path / "c",
        download_dir=download_dir, warnings=warnings,
    )
    assert result is None
    assert any("unreadable" in w for w in warnings)
    assert not bogus.exists(), "the bad copy must be discarded so a re-run refetches"


def test_days_before_the_archive_starts_are_skipped(tmp_path: Path) -> None:
    import openintel_rfc.reverse_zones as rz

    warnings: list[str] = []
    reports = rz.ingest_range(
        [date(2000, 1, 1)], cache_dir=tmp_path, download_dir=tmp_path,
        warnings=warnings,
    )
    assert reports == []
    assert any("precedes the reverse-zone archive" in w for w in warnings)


def test_truncated_download_is_retried_then_reported(tmp_path: Path, monkeypatch) -> None:
    """A short read surfaces later as "compressed file ended before the
    end-of-stream marker", where it looks like a corrupt archive rather than a
    transfer that needs retrying. Catch it at fetch time instead."""
    import openintel_rfc.reverse_zones as rz

    attempts = {"n": 0}

    class _Short:
        status = 200
        headers = {"Content-Length": "1000"}
        def read(self, _n=None):
            if self._done: return b""
            self._done = True
            return b"x" * 10          # far short of the declared length
        _done = False
        def __enter__(self):
            attempts["n"] += 1
            self._done = False
            return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(rz.urllib.request, "urlopen", lambda *a, **k: _Short())
    warnings: list[str] = []
    result = rz.fetch_archive(date(2024, 10, 1), tmp_path, attempts=3, warnings=warnings)

    assert result is None
    assert attempts["n"] == 3, "a truncated transfer must be retried, not accepted"
    assert any("truncated" in w for w in warnings)
    assert list(tmp_path.glob("*.part")) == []
