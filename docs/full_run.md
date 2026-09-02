# Running the full timeline on the server

One script, five stages:

```bash
python scripts/full_timeline.py \
    --roots /mnt/bigdisk/openintel \
    --roots /mnt/spill/openintel \
    --ripe-cache out/reverse/corpus \
    --out out/full_run \
    --threads 16 --memory-limit 48GB
```

**The OpenINTEL side never touches the network.** The cache is already on disk, so
nothing lists or fetches from the object store, and there is no endpoint left to
throttle the run. The one stage that does fetch is `ripe`, and it pulls plain
HTTPS tarballs from a server with no rate limiter — a different network with none
of the object store's problems. Drop `--ripe-cache` and the run is fully offline.

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
| The two copies differ in size | the **larger** wins and the disagreement is reported — a short copy is an interrupted move, not a short day |
| File matching no known layout | **excluded and reported**, never silently dropped |

Three layouts are recognised: this project's `<basis>/<source>/<YYYY-MM-DD>/`,
OpenINTEL's Hive-style `source=/year=/month=/day=`, and a loose date fallback. The
reverse corpus needs no special handling — it is just another root.

**There is no "fall back to the spill".** Every root is walked in full, once, at
index time; nothing is probed at read time. A fallback would have to decide when
the main path is missing something, and it cannot — a source-day sitting there with
three of its five files looks complete. Order matters only for identical
duplicates, where the first root named wins, so pass the faster disk first.

## Stages

Run them together, or one at a time with `--stage`:

| Stage | Does | Output |
| --- | --- | --- |
| `ripe` | fetches RIPE's reverse-delegation archive | the reverse corpus |
| `index` | walks every root | `inventory.json` |
| `extract` | one pass per source-day | `checkpoints/*.parquet`, `timeline_monthly.csv` |
| `analyse` | bottom-up + top-down | `bottom_up.json`, `top_down.json`, `comparison.json` |
| `report` | digest for humans and for the next conversation | `summary.md`, `analysis_bundle.json` |

`extract` writes one checkpoint per source-day and skips days already done, so an
interrupted 14 TB run resumes where it stopped rather than at the beginning. Use
`--no-resume` to force a re-scan.

A day that **fails to read** is not checkpointed. It gets a `*.failed.json` marker
and is retried on the next run, because treating a transient read error like an
empty day would drop it from the corpus permanently and silently.

`--max-days` samples **evenly across the sorted source-days**, not the first N. The
list is ordered by `(source, day)`, so a prefix would be one source's earliest days
— for the reverse corpus, AFRINIC 2009–2010 and nothing else. A subsample has to
span every source and the whole period or it answers a different question than the
full run.

Re-analysing costs nothing — it reads the timeline, not the corpus:

```bash
python scripts/full_timeline.py --stage analyse --stage report --out out/full_run
```

## Several machines against one NAS

The cache is on a NAS, so every machine sees the same files. Split the scan by
giving each one the same command with a different `--shard`:

```bash
# machine A                              # machine B                # machine C
--shards 3 --shard 0                     --shards 3 --shard 1       --shards 3 --shard 2
```

**No coordinator, no lock, no queue.** The shard plan is deterministic, so each
machine computes the whole plan and keeps its own slice. Work is balanced on
**bytes, not day count** — a day's files vary by three orders of magnitude, so an
even split of days is a wildly uneven split of work. On the reverse corpus three
shards come out at 0.0% spread.

Each day belongs to exactly one shard and a checkpoint is named after its day, so
two machines never write the same file. Writes are `.part` then rename, which is
what makes them safe on a network filesystem.

Order of operations, which matters:

1. **Index once.** Walking a NAS from every machine multiplies the metadata
   traffic for an identical answer. Run `--stage index` on one machine, let it
   write `inventory.json` to the shared `--out`, then give the others
   `--stage extract` only.
2. **Extract in parallel**, one `--shard` each.
3. **Analyse once**, on any machine, after all shards finish.

Sharding is applied *after* `--max-days` and `--pool-sources`, so a subsample
stays a subsample and each pooled day is assigned to exactly one machine.

A three-shard run and a single-machine run over the same corpus produce
**identical results** — verified across 30 observable changes and 7 fields each.

### Knowing when it is safe to analyse

Each shard writes `shards/shard-<i>-of-<n>.json` when it finishes, carrying its
day count, bytes, failures and hostname. The `analyse` stage reads those and
warns if the set is incomplete:

```
Only 2 of 3 shards have reported. Missing: 1. This timeline covers part of the
corpus, and every share in it is taken against that part.
```

It warns rather than refuses, because analysing a deliberate partial run is
legitimate and the operator is the one who knows. What is never acceptable is
doing it silently — a partial corpus produces entirely plausible numbers. It also
flags shard reports that disagree about `n`, which means the checkpoint directory
holds output from runs split different ways: some days missing, others duplicated.

### How many machines

The limit is the NAS, not the CPUs. Extraction is one sequential read per
source-day with column pruning, so it is I/O-bound; past the point where the
shares saturate the link, more machines just divide the same bandwidth. Start
with three or four and watch whether wall-clock actually falls.

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
