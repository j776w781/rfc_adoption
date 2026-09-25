"""Roll up the domain-level presence table into per-TLD monthly prevalence.

``domain_month_table.parquet`` (produced by
``presence_table.merge_domain_month_table``) holds one row per (domain, month),
already deduplicated and OR'd across every day of the month. The segmented
regression this feeds needs one step further: not "did this domain have the
record," but "what fraction of this TLD's domains had it that month."

TLDs are kept separate rather than pooled. The cache here spans TLDs
(fed.us, ch, ee, gov, li, nu, se) with very different sizes and very different
DNSSEC histories; averaging them into one global number would let a real shift
in one TLD get diluted or masked by others that never moved. Every output row
is one (tld, month), never a cross-TLD blend.

Prevalence is a fraction, not a raw count. A raw count of domains with a DS
record would climb simply because a zone grew (more domains registered), even
with zero change in what fraction of domains actually sign -- the same
corpus-growth confound the rest of this project is careful to avoid. Since
each presence flag is already 0/1, ``avg(flag)`` gives the fraction directly.
The raw counts are kept alongside it so a TLD-month with very few domains
observed (and therefore a noisy percentage) stays visible rather than hidden
behind a clean-looking number.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import duckdb

from openintel_rfc.parquet_reader import describe_parquet
from openintel_rfc.sql_compiler import quote_string
from openintel_rfc.utils import PipelineError, ensure_dir, get_logger

__all__ = ["RollupSummary", "rollup_tld_month_prevalence"]

LOGGER = get_logger(__name__)


@dataclass
class RollupSummary:
    output_path: Path
    row_count: int
    tlds: list[str] = field(default_factory=list)


def rollup_tld_month_prevalence(
    domain_month_table: Path | str,
    output_path: Path | str,
    *,
    csv: bool = False,
) -> RollupSummary:
    """Aggregate ``domain_month_table`` into one row per (tld, month).

    Each output row carries, per record type: the raw count of domains with
    that record present that month (``*_count``), the total domains observed
    that month (``n_domains``), and the fraction (``*_prevalence``) --
    ``*_prevalence`` is what the segmented regression models; the counts ride
    along for sanity-checking small-sample months.
    """
    domain_month_table = Path(domain_month_table)
    if not domain_month_table.is_file():
        raise PipelineError(f"Domain-month table not found: {domain_month_table}")

    output_path = Path(output_path)
    ensure_dir(output_path.parent)

    connection = duckdb.connect(database=":memory:")
    try:
        rollup_sql = (
            "SELECT\n"
            "  tld,\n"
            "  month,\n"
            "  CAST(count(*) AS BIGINT) AS n_domains,\n"
            "  CAST(sum(ds_present) AS BIGINT) AS ds_count,\n"
            "  avg(ds_present) AS ds_prevalence,\n"
            "  CAST(sum(dnskey_present) AS BIGINT) AS dnskey_count,\n"
            "  avg(dnskey_present) AS dnskey_prevalence,\n"
            "  CAST(sum(rrsig_present) AS BIGINT) AS rrsig_count,\n"
            "  avg(rrsig_present) AS rrsig_prevalence\n"
            f"FROM read_parquet({quote_string(str(domain_month_table))})\n"
            "GROUP BY tld, month\n"
            "ORDER BY tld, month"
        )
        # This aggregates the already-merged, domain-sized table down to one row
        # per (tld, month) -- a few thousand rows at most -- so, unlike the big
        # day-checkpoint merge, sorting the output here costs nothing.
        tmp = output_path.with_suffix(output_path.suffix + ".tmp")
        if tmp.exists():
            tmp.unlink()
        try:
            connection.execute(
                f"COPY ({rollup_sql}) TO {quote_string(str(tmp))} (FORMAT PARQUET)"
            )
        except Exception as exc:  # DuckDB raises its own error hierarchy
            raise PipelineError(
                f"DuckDB failed rolling up {domain_month_table}: {exc}"
            ) from exc
        os.replace(tmp, output_path)

        row_count = int(describe_parquet(output_path)["row_count"])
        tlds = [
            str(row[0])
            for row in connection.execute(
                "SELECT DISTINCT tld FROM read_parquet("
                f"{quote_string(str(output_path))}) ORDER BY tld"
            ).fetchall()
        ]

        if csv:
            csv_path = output_path.with_suffix(".csv")
            csv_tmp = csv_path.with_suffix(csv_path.suffix + ".tmp")
            if csv_tmp.exists():
                csv_tmp.unlink()
            connection.execute(
                f"COPY (SELECT * FROM read_parquet({quote_string(str(output_path))})) "
                f"TO {quote_string(str(csv_tmp))} (FORMAT CSV, HEADER)"
            )
            os.replace(csv_tmp, csv_path)
    finally:
        connection.close()

    return RollupSummary(output_path=output_path, row_count=row_count, tlds=tlds)
