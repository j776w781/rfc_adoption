# Prototypes

Exploratory scripts that predate the pipeline in `src/openintel_rfc/`. Kept
because they are the working reference for how to reach OpenINTEL over S3, and
because the real pipeline's access layer was derived from them.

| File | What it is |
| --- | --- |
| `trial.py` | Minimal anonymous S3 walk over `fdns/basis=zonefile`, downloading a day's Parquet and reading two columns with pandas. |
| `openIntelPlugin.py` | The same access pattern wrapped in a `SourcePlugin`, filtering for `response_type=CDS`/`CDNSKEY` with `algorithm=0` — the RFC 8078 delete signal. |
| `source_plugin.py` | The `SourcePlugin` base class those two implement. |
| `SAMPLE_IOA.json` | Sample indicator-of-adoption input for that plugin interface. |

These are **not** imported by the pipeline and are not covered by the test suite.
They run standalone and need `boto3` plus `python-dateutil`.

Two details in them turned out to matter and are carried into
`src/openintel_rfc/openintel_source.py`:

- the `before-sign.s3` / `fix_s3_host` unregister, without which requests go to
  AWS instead of Utwente;
- `multipart_chunksize=64MB`, because OpenINTEL rate-limits on request count and
  a small chunk size on a 500 MB object trips the limiter.

The production equivalents are `openintel_source.py` (discovery and both access
modes) and `parquet_reader.py` (schema-aware reads). Prefer those; these remain
as the record of where the approach came from.
