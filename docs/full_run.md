# Running the full timeline on the server

One script, four stages, no network:

```bash
python scripts/full_timeline.py \
    --roots /mnt/bigdisk/openintel \
    --roots /mnt/spill/openintel \
    --roots out/reverse/corpus \
    --out out/full_run \
    --threads 16 --memory-limit 48GB
```

The OpenINTEL cache is already on disk, so nothing here lists or fetches from the
object store. There is no endpoint to be throttled by, which is what makes the run
repeatable and restartable.

## Why several roots matter

Part of the cache was moved to a second drive when the first filled up. Nothing
records that move, so a source-day can now have some files on one drive and the
rest on another. **Reading one root at a time would report a partial day as a
complete one** — and a half-sized day is indistinguishable from a month when fewer
names were signed. It would be read as a measurement.

So every root is walked, each file is reduced to a `(source, date, filename)`
identity, and identities are merged. Two behaviours fall out, both verified
against the real corpus (`tests/test_cache_index.py`):

| Situation | What happens |
| --- | --- |
| Same day, different files, two drives | merged into one day; flagged `split_across_roots` |
| Same file copied to both drives (a partial move) | counted **once**; listed under `duplicates` |
| File matching no known layout | **excluded and reported**, never silently dropped |

Three layouts are recognised: this project's `<basis>/<source>/<YYYY-MM-DD>/`,
OpenINTEL's Hive-style `source=/year=/month=/day=`, and a loose date fallback. The
reverse corpus needs no special handling — it is just another root.

## Stages

Run them together, or one at a time with `--stage`:

| Stage | Does | Output |
| --- | --- | --- |
| `index` | walks every root | `inventory.json` |
| `extract` | one pass per source-day | `checkpoints/*.parquet`, `timeline_monthly.csv` |
| `analyse` | bottom-up + top-down | `bottom_up.json`, `top_down.json`, `comparison.json` |
| `report` | digest for humans and for the next conversation | `summary.md`, `analysis_bundle.json` |

`extract` writes one checkpoint per source-day and skips days already done, so an
interrupted 14 TB run resumes where it stopped rather than at the beginning. Use
`--no-resume` to force a re-scan.

Re-analysing costs nothing — it reads the timeline, not the corpus:

```bash
python scripts/full_timeline.py --stage analyse --stage report --out out/full_run
```

## The timeline is long, not wide

One row per `(source, month, dimension, value)` with a record count and a
domain count. A wide table would need its schema fixed in advance and every new
algorithm number would need a migration; a long table absorbs values nobody has
seen yet, which over seventeen years is the normal case.

**Every dimension carries its own denominator** as a `_total` row. That is the fix
for the error that produced the retracted "10× disagreement": a share is only
meaningful against the population it was taken from, and here the population comes
from the same query as the numerator, so `P(value | population)` can always be
recomputed correctly.

Both counts are kept because they answer different questions. `records` is weighted
by how often a name is measured and how many keys it publishes; `domains_peak` is
the busiest single day in the month, a true lower bound on distinct names. Distinct
counts cannot be summed across days without counting the same name repeatedly, and
per-day checkpoints do not carry the identities needed to union them — so the bound
errs toward understating reach, never inflating it.

## Both directions are configuration, not code

`data/analysis_config.json` drives everything. Add a row to
`bottom_up.changes` to measure a new observable; move an RFC between
`top_down.categories` to re-cut the taxonomy. Neither requires touching Python.

```bash
python scripts/full_timeline.py --no-top-down --out out/full_run    # one direction
python scripts/full_timeline.py --config my_taxonomy.json ...       # another cut
```

Stage thresholds live in the same file (`stages`), and the defaults are the swept
ones from [stages.md](stages.md): partial ≥ 1%, common ≥ 10%, both requiring ≥ 10
distinct names.

## Reading the output

`bottom_up.json` gives every configured change a `state`, and three of them are
easy to confuse:

| State | Means |
| --- | --- |
| `common` / `partial` / `seen_only` | observed, and how far it got |
| `scanned_no_match` | **the corpus was asked and the answer is no** — a real null |
| `no_corpus_coverage` | the corpus cannot carry this record type — *not* a result |
| `residue` | a deprecation; the number is what persists, not when it appeared |

That distinction is load-bearing. Collapsing `scanned_no_match` into
`no_corpus_coverage` is how RFC 9905 once reported zero observations while 15,966
non-conforming records sat in the corpus. `left_censored` marks a first sighting
in the corpus's opening month, where onset is an upper bound rather than a
measurement.

## Cross-corpus comparison

`cross_reference` in the config names which dimensions are comparable between the
forward and reverse corpora. Only algorithm- and digest-scoped dimensions are:
the reverse corpus holds NS and DS records only, so any share taken over "all
DNSSEC records" is a statement about record-type composition rather than operator
behaviour. That is the RFC 4509 lesson in [bottom_up.md](bottom_up.md), encoded so
it does not have to be remembered.
