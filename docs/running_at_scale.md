# Running against the real OpenINTEL corpus

The MVP path (`analyze`) reads one Parquet file, builds one `ObservedSignal` per
row and one reasoning trace per (signal × RFC). That is exactly what you want for
tens of thousands of rows and completely impossible for tens of billions.

The `scale` path is architecturally different, and this document explains how, so
that you can read its output correctly.

---

## 1. Server setup

```bash
git clone <repo> && cd rfc_adoption
./scripts/setup.sh
```

Idempotent. Installs system build dependencies (apt / dnf / yum / zypper / pacman
/ apk), creates `.venv`, installs the pipeline plus `boto3`, verifies imports,
probes `INSTALL httpfs` (streaming needs it), runs the offline demo and the test
suite, and prints DuckDB tuning derived from the machine.

```bash
./scripts/setup.sh --no-sudo     # no system packages
./scripts/setup.sh --minimal     # dependencies only
./scripts/setup.sh --python /usr/bin/python3.12
```

Memory limit defaults to **70% of RAM**. A scan that trips the OOM killer loses
the partition it was working on; leaving headroom is cheaper than re-running.

---

## 2. Always dry-run first

```bash
./scripts/run_full_analysis.sh --sources nu,se --start 2018-05-01 --end 2018-05-03 --dry-run
```

Costs seconds, scans nothing, and answers the two questions that otherwise cost
you a night:

```
6 partition(s) match 2018-05-01..2018-05-03 for nu, se
  zonefile/nu/2018-05-01     1 object(s)
  zonefile/se/2018-05-01     4 object(s)
  ...
Real schema of zonefile/nu/2018-05-01: 98 columns

Normalized field resolution against the real schema:
  algorithm      <- dnskey_algorithm, ds_algorithm, rrsig_algorithm,
                    cds_algorithm, cdnskey_algorithm, nsec3_hash_algorithm,
                    nsec3param_hash_algorithm
  digest_type    <- ds_digest_type, cds_digest_type
  rr_type        <- response_type
  measurement_id <- (nothing; will be all-null)
```

If a field an indicator tests resolves to nothing, that indicator can never match
and the run will quietly report zero adoption for it. Fix the dictionary's
`openintel_native_fields` before spending compute.

### Available sources

`fdns/basis=zonefile` publishes: **ch, ee, fed.us, fr, gov, li, nu, root, se, sk**.
`.com` is not among them. Verify with `--dry-run` rather than assuming.

---

## 3. Running

```bash
# One real day, end to end. Do this before anything larger.
./scripts/run_full_analysis.sh --sources nu --start 2018-05-01 --end 2018-05-01

# The real thing. Use tmux: this runs for hours to days.
tmux new -s openintel
./scripts/run_full_analysis.sh --sources nu,se,nl --start 2015-01-01 --end 2021-12-31
```

**It is resumable.** Every partition writes a checkpoint. Re-running the same
command skips completed partitions. An interrupted run — network drop, OOM, power
— costs you one partition, not the whole range.

`--mode stream` (default) queries `object.openintel.nl` directly and needs no
local storage. `--mode download --cache-dir /big/volume` fetches first, which is
worth it when you will re-scan the same range while iterating on the checklist.
`./scripts/fetch_openintel.sh --list` reports object count and size first.

---

## 4. How the scale path differs — read this before quoting a number

### Matching runs in SQL; scoring stays in Python

One DuckDB query per partition applies the record-type prefilter, COALESCEs the
per-record-type columns into normalized fields, evaluates every indicator, and
applies the publication-date cutoff, then groups by
`(rfc_id, indicator_id, decision, source, year_month)`.

The scoring *formula* never appears in SQL. `sql_compiler` enumerates each RFC's
reachable evidence patterns, calls the real `ranking.score_match` for each, and
compiles the answers into a lookup. The SQL path therefore cannot drift from the
Python path without Python changing first, and a cross-validation test asserts
identical per-RFC counts, `first_seen` and scores across both engines.

### The record-type prefilter is what makes it tractable

Most fDNS rows are A / AAAA / MX / NS / TXT and can never match a DNSSEC
checklist. The DNSSEC record types are derived from the checklist and pushed into
the scan first. For `.nu` on 2018-05-01 this takes 6,172,265 rows down to
2,621,052 before a single indicator is evaluated.

The tradeoff is stated in the run's warnings: an observation with a null or
unexpected `rr_type` is not counted.

### Counts are exact; scores and traces are sampled

| Artefact | At scale |
| --- | --- |
| `ranked_candidates.json` observation counts | **exact corpus aggregates** |
| `adoption_timeline.json` counts, `first_seen` | **exact** |
| `observed_signals.json`, `rfc_matches.json`, `reasoning_traces.json` | **a deterministic sample** |
| candidate `score` / `confidence` | derived from the sample — a **lower bound** |
| `distinct_domains` | a **lower bound** (`approx_count_distinct` cannot be merged exactly) |

The exemplars exist so that every aggregate has a worked reasoning trace behind
it. **Their count is not a measurement.** The report says so in section 1, and
`corpus_stats` in `run_manifest.json` carries the true `rows_scanned`.

Because scores come from sampled exemplars, an RFC can hold a large number of
corpus observations and still be absent from the ranking if no sampled exemplar
scored above the threshold. The runner emits an explicit warning when that
happens rather than letting the RFC disappear silently.

---

## 4a. Throttling — use download mode for long runs

OpenINTEL is a shared academic object store and returns **HTTP 503** under load.
Your own `openIntelPlugin.py` already carries the clue in a comment: *"a small
chunksize may trigger the request rate limiter"*. It limits on **request count**,
not bytes — which decides the whole strategy.

Stream mode is the worst case for that. DuckDB issues many small parallel HTTP
range requests per Parquet row group, so a wide scan generates thousands of
requests per object. Download mode issues one sequential GET per object in 64 MB
chunks: a few hundred times fewer requests for the same bytes.

Measured on this corpus (`.nu`, 2018-05-01, 2.6M rows after the prefilter):

| Strategy | Per partition | Requests |
| --- | --- | --- |
| Stream | **71 s** | thousands of small ranges |
| Download, cold | 13.9 s fetch + 21.4 s scan = **35 s** | one sequential GET |
| Download, cached re-scan | **21.4 s** | none |

Download mode is **2× faster cold, 3.3× faster on a re-scan, and far gentler**.
For a multi-TLD multi-year run it is the right default, not the fallback:

```bash
./scripts/fetch_openintel.sh --sources nu,se --start 2015-01-01 --end 2021-12-31 --list
./scripts/run_full_analysis.sh --mode download --cache-dir /big/volume \
    --sources nu,se --start 2015-01-01 --end 2021-12-31 --pace-seconds 2
```

Thread count is **not** the lever people expect. Measured across a stream scan:

| threads | 20 | 8 | 4 | 2 |
| --- | --- | --- | --- | --- |
| seconds | 5.6 | 5.8 | 5.9 | 5.9 |

A 1.07× spread — the scan is network-bound, so `--threads 4` cuts request
concurrency roughly fivefold at almost no cost in time. Worth doing if you must
stream.

### What the pipeline now does about it

- **HTTP retries**: DuckDB's default budget is ~2 seconds. Raised to ~8.5 minutes
  (`http_retries=10`, `wait=500ms`, `backoff=2`, `timeout=120s`).
- **Partition-level retry**: when throttling exhausts even that and the query
  fails, the partition is retried with a doubling wait
  (`--partition-retries`, `--retry-wait`, default 5 attempts over ~7.5 minutes).
  Transient failures (503/500/502/504, timeout, connection reset, "too many
  requests") retry; a genuine error such as a binder failure raises immediately
  rather than wasting the budget.
- **`--pace-seconds`**: an optional gap between partitions. Correctness never
  needs it; a multi-day unattended walk over infrastructure nobody is billing us
  for is a good reason to use it anyway.
- **Checkpointing**: if a partition ultimately fails, everything already done is
  on disk and re-running resumes.

### Sizing a range before you start

Measured object sizes, `basis=zonefile`:

| Source | Objects/day | Size/day |
| --- | --- | --- |
| `nu` | 1 | 0.37 GB |
| `se` | 4 | 2.09 GB |

Extrapolated to 2015-01-01..2021-12-31 (2,557 days):

| Range | Partitions | Download size | Est. wall time (download) |
| --- | --- | --- | --- |
| `nu` | 2,557 | ~0.95 TB | ~25 h |
| `nu,se` | 5,114 | ~6.3 TB | ~50 h |

`./scripts/fetch_openintel.sh --list` reports the real total for your exact range
and compares it against free space on the cache volume, refusing to start a
download that will not fit. Do that before committing days of compute.

`run_full_analysis.sh` also refuses to start on a source OpenINTEL does not
publish. A source with no objects produces no matches, which in the output is
indistinguishable from a source with no adoption -- so `--sources nu,se,nl` fails
immediately rather than after three days of finding nothing for `nl`.

### If you are still being throttled

1. Switch to `--mode download` — the single biggest change.
2. Add `--pace-seconds 5`.
3. Drop `--threads` to 4.
4. Raise `--retry-wait` to 120 so retries span a longer limiter window.
5. Run overnight in Utwente's local time; the store is quieter.

## 4b. Splitting a run across several machines

Supported, and **verified byte-equivalent to a single run**. Nothing special is
needed: the unit of work is one partition (one source-day), each partition writes
its own self-contained checkpoint, and the merge is the same code path a
single-machine run already takes. Sharding does not take a different route
through the pipeline, which is why the results are identical rather than merely
close.

Split by **date range**, by **source**, or both — the ranges only have to be
disjoint:

```bash
# machine 1
./scripts/run_full_analysis.sh --sources nu,se --start 2015-01-01 --end 2017-12-31 \
    --mode download --cache-dir /large/volume --out /out/shard1

# machine 2
./scripts/run_full_analysis.sh --sources nu,se --start 2018-01-01 --end 2019-12-31 \
    --mode download --cache-dir /large/volume --out /out/shard2

# machine 3
./scripts/run_full_analysis.sh --sources nu,se --start 2020-01-01 --end 2021-12-31 \
    --mode download --cache-dir /large/volume --out /out/shard3
```

Then gather the checkpoints on one machine and run the **whole** range against
them. Every partition is already checkpointed, so nothing is rescanned and the
run is a merge:

```bash
mkdir -p /out/final/checkpoints
rsync -a machine1:/out/shard1/checkpoints/ /out/final/checkpoints/
rsync -a machine2:/out/shard2/checkpoints/ /out/final/checkpoints/
rsync -a machine3:/out/shard3/checkpoints/ /out/final/checkpoints/

./scripts/run_full_analysis.sh --sources nu,se --start 2015-01-01 --end 2021-12-31 \
    --checkpoint-dir /out/final/checkpoints --out /out/final
```

The log will show `reusing checkpoint` for every partition.

### Only checkpoints move, not data

A checkpoint is the partition's aggregate, not its rows:

| | 3 `.nu` partitions | extrapolated to `nu,se` 2015-2021 |
| --- | --- | --- |
| source data scanned | 1.1 GB | ~6.3 TB |
| checkpoints to ship | **49 KB** | **~82 MB** |

Roughly 23,000:1. Ship the checkpoints; leave the Parquet cache where it was
downloaded.

### Rules that actually matter

1. **Every machine must use the same checklist and dictionary.** This is enforced,
   not assumed: each checkpoint records `checklist_version` and a `scan_sql_sha1`
   of the compiled scan, and the merge rejects any checkpoint whose fingerprint
   differs, with the reason *"it was produced by a different compiled scan …, so
   its aggregates answer a different question"*. Rejected partitions are
   **recomputed**, so a mismatched shard turns a merge into a full rescan rather
   than into a wrong answer. Sync `data/` across machines before starting.
2. **Copy the whole `checkpoints/` directory**, including its `exemplars/`
   subdirectory. The exemplars are what give the merged run its reasoning traces.
3. **Keep ranges disjoint.** Overlap is harmless — a partition's checkpoint is
   deterministic, so a duplicate is identical — but it is wasted compute.
4. **The merge still lists partitions from S3**, so the merging machine needs
   network access even though it reads no measurement data.
5. `distinct_domains` remains a lower bound, exactly as in a single-machine run.
   Sharding does not make it worse: a single run merges per-partition checkpoints
   too.

### Verified

Two shards (`2018-05-01` and `2018-05-02..03`) merged against a single run of
`2018-05-01..03` produce identical `ranked_candidates` (rank, score, confidence,
supporting counts, first/last seen), identical `adoption_timeline`, and identical
manifest row totals.

## 5. A verified real result

`--sources nu --start 2018-05-01 --end 2018-05-01`, 2,621,052 rows scanned in
~72 s streaming from S3:

| Rank | RFC | Mechanism | Observations |
| --- | --- | --- | --- |
| 1 | RFC 5155 | NSEC3 | 408,997 |
| 2 | RFC 6605 | ECDSA | 27,631 |
| 3 | RFC 7344 | CDS/CDNSKEY | 179 |
| 4 | RFC 4509 | SHA-256 DS | 131,626 |
| 5 | RFC 4033 | base DNSSEC | 2,211,876 |

Cross-checked against direct queries on the same objects: NSEC3 285,590 +
NSEC3PARAM 123,407 = 408,997; CDS 92 + CDNSKEY 87 = 179; DNSKEY + DS + RRSIG +
NSEC = 2,211,876. All exact.

Note RFC 4033 ranking last on 2.2M observations while RFC 7344 ranks third on
179. That is the specificity weighting behaving correctly: a CDS record says
something specific, a DNSKEY record says only "this zone is signed".

---

## 6. Real-corpus gotchas already handled

These were all found by running against real data, and every one is a *silent*
failure — the pipeline keeps running and produces plausible, wrong output. They
are pinned by `tests/test_parquet_reader_real_schema.py`.

1. **Per-record-type columns.** OpenINTEL has no single `algorithm` column. The
   reader COALESCEs `dnskey_algorithm`, `ds_algorithm`, `rrsig_algorithm`,
   `cds_algorithm`, `cdnskey_algorithm`, `nsec3_hash_algorithm`,
   `nsec3param_hash_algorithm`. Binding to the first would read NULL for every
   CDS row, so RFC 8078 delete signals could never match.
2. **Epoch milliseconds.** `timestamp` is INT64 epoch ms. Read as nanoseconds it
   maps everything to 1970-01-01 and destroys the publication-date cutoff. The
   unit is detected from magnitude.
3. **Hive partition columns.** DuckDB exposes `year`/`month`/`day` from the path
   and types them from the literal text — `year` BIGINT, `month`/`day` VARCHAR.
   They are not fallbacks for `timestamp`; datetime fields are never coalesced.
4. **Lateral alias shadowing.** The scan projects `<decoded> AS "timestamp"`,
   but OpenINTEL's own column is also `timestamp`, and DuckDB resolves the base
   column first. The cutoff compares the decoded expression, never the bare
   identifier.
5. **`measurement_id` does not exist** in the real corpus. It reads as null. No
   indicator tests it, so matching is unaffected.

---

## 7. Operational notes

- Logs land in `logs/`. Run logs record per-partition rows scanned, matched,
  elapsed and ETA.
- DuckDB's progress bar is disabled: it emits ANSI carriage-return frames that
  make a multi-day log unreadable.
- Checkpoints are named from a sanitized partition slug, not the partition path,
  so they stay in one flat directory where the merge step can see them.
- To inspect results: `streamlit run dashboard/app.py --server.address 0.0.0.0`
  and point the sidebar at the output directory.
