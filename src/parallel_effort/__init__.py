"""A month/domain/tld DS-DNSKEY-RRSIG presence table, built from a local OpenINTEL cache.

This is a separate, standalone effort from :mod:`openintel_rfc` -- it answers a
simpler question (which of DS/DNSKEY/RRSIG did we ever see for this domain in
this month?) than the RFC-checklist matcher does, so it does not reuse that
matcher. It does reuse the parts of ``openintel_rfc`` that are not specific to
RFC matching:

* :mod:`openintel_rfc.cache_index` to discover the Parquet files across
  whatever roots/layouts a local cache happens to have accumulated.
* :mod:`openintel_rfc.checklist_loader` / :mod:`openintel_rfc.models` to load
  the OpenINTEL analysis dictionary, so ``domain``/``zone``/``rr_type``/
  ``timestamp`` are resolved against real Parquet columns the same way the
  rest of the project resolves them.
* :mod:`openintel_rfc.parquet_reader` / :mod:`openintel_rfc.sql_compiler` for
  the column-alias COALESCE + cleaning expressions (trim, empty-as-absent,
  upper-cased record types, epoch-timestamp decoding) and for the small SQL
  quoting helpers.

No file under ``openintel_rfc`` is modified by this package.
"""
