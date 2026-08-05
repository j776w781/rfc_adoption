# OpenINTEL RFC-Adoption Matching Pipeline

Match large-scale DNS/DNSSEC measurement data from [OpenINTEL](https://openintel.nl)
against a database of RFC checklists, and produce **ranked RFC candidates with
explicit, inspectable reasoning** — not a single opaque label.

## Status

Working, and verified against the real corpus — not only the shipped fixture.

A run over live OpenINTEL data (`source=nu`, 2018-05-01..03, **7,861,083 rows in
3m46s**) produced these counts, every one of which was reproduced exactly by
hand-written SQL issued directly against the same S3 objects:

| Rank | RFC | Mechanism | Observations |
| --- | --- | --- | --- |
| 1 | RFC 5155 | NSEC3 | 1,226,569 |
| 2 | RFC 6605 | ECDSA | 82,773 |
| 3 | RFC 7344 | CDS/CDNSKEY | 537 |
| 4 | RFC 4509 | SHA-256 DS | 394,783 |
| 5 | RFC 4033 | base DNSSEC | 6,633,977 |

Note RFC 4033 ranking **last** on 6.6M observations while RFC 7344 ranks third on
537. That is the specificity weighting working: a CDS record says something
specific, a DNSKEY record says only "this zone is signed".

**718 tests pass.** All 10 dashboard pages load clean. Two runs of the same range
are byte-identical apart from the recorded output path.

### Two execution paths, and they are not interchangeable

| | `analyze` | `scale` |
| --- | --- | --- |
| Input | one local Parquet file | the OpenINTEL S3 corpus, many partitions |
| Built for | ~10⁴–10⁶ rows | 10⁹–10¹¹ rows |
| Matching | Python, row by row | pushed into DuckDB SQL |
| Output | one signal and one trace **per row** | **exact aggregates** + a *sampled* set of traces |
| Resumable | not needed | yes, per-partition checkpoints |

Both use the same checklist, the same scoring formula and the same decision rules;
a cross-validation test asserts the two engines produce identical per-RFC counts,
`first_seen` and scores. What differs is only what can be materialized.

**Read [`docs/running_at_scale.md`](docs/running_at_scale.md) before quoting a
number from a `scale` run.** Its counts are exact; its scores and reasoning traces
come from a bounded sample.

## Project goal

Given three inputs:

1. an **RFC checklist / signature database** (observable indicators + publication dates),
2. an **OpenINTEL dictionary / schema** (which fields the corpus actually exports),
3. **OpenINTEL-style Parquet files** of DNS measurements,

the system determines which RFCs are *consistent with* the observed signals, how
strongly, since when, and — critically — **why**.

## What the system does

- Cross-checks every RFC-derived indicator against the OpenINTEL dictionary and
  classifies it `queryable`, `partially_queryable`, `non_queryable`, or `ambiguous`.
- Reads OpenINTEL Parquet with DuckDB (projection pushdown; pandas/PyArrow fallback),
  resolving real column names (`response_type`, `cds_algorithm`, …) to normalized
  analysis fields (`rr_type`, `algorithm`, …).
- Extracts normalized **observed signals** from measurement rows.
- Compares **every** observed signal against **every** RFC checklist. It never picks
  one RFC up front, and a signal is allowed to match several RFCs at once.
- Applies **publication-date cutoff logic**: an observation that predates an RFC
  cannot evidence its adoption.
- Ranks candidate RFCs with an itemized, reproducible score.
- Emits a **structured decision trace** for every single signal × RFC evaluation —
  matches, partial matches, rejections, and timestamp-invalid cases alike.
- Routes missing fields, ambiguity, and inconsistencies to a **review queue**.
- Exports JSON, CSV and Markdown, and ships a nine-page Streamlit dashboard.
- At corpus scale: discovers S3 partitions, streams or downloads them, pushes the
  match into SQL, **checkpoints every partition** so an interrupted multi-day run
  resumes, and survives object-store throttling.

## What the system does *not* claim

> This pipeline does not prove RFC adoption by itself. It identifies ranked RFC
> candidates based on OpenINTEL-observable signals and timestamp consistency.

Concretely:

- A record matching an RFC's signature shows the *mechanism* is present. It does not
  show the operator read the RFC, nor that the deployment is conformant.
- Broad base-DNSSEC RFCs (4033/4034/4035) match almost any signed zone. Their low
  specificity multiplier reflects that; they are evidence of DNSSEC, not of a choice.
- Recommendation-oriented RFCs (e.g. 8624) are **not** directly observable. Their
  indicators are marked ambiguous and always routed to review.
- Absence of a signal is not evidence of absence: it may mean the corpus does not
  export the field, or the measurement did not cover the name.
- The shipped sample Parquet is **synthetic**, built to exercise every code path.
- In a `scale` run, observation counts are exact but **scores and reasoning traces
  are derived from a sample**. A candidate's score is a lower bound, and an RFC can
  hold millions of corpus observations yet be absent from the ranking because no
  sampled exemplar scored above the threshold. The run warns explicitly when that
  happens; it is a real limitation, not a display quirk.

## Architecture overview

```mermaid
flowchart LR
    A[RFC Corpus] --> B[LLM + Manual RFC Checklist]
    B --> C[RFC Checklist DB<br/>observable indicators + publication dates]

    D[OpenINTEL Dictionary / Schema] --> E[Cross-check Queryable Fields]
    C --> E

    E --> F[Queryable Indicators]
    E --> G[Non-queryable / Ambiguous<br/>review later]

    H[OpenINTEL Parquet Files] --> I[Read Relevant Fields<br/>DuckDB / PyArrow]
    F --> I

    I --> J[Observed Signals<br/>fields, values, timestamps]

    J --> K[Compare Against All RFC Checklists]
    C --> K

    K --> L[Timestamp Cutoff<br/>remove impossible RFC matches]

    L --> M[Score + Rank Candidate RFC Groups]
    M --> N[Reasoning + Review Queue]

    N --> O[Verified Ranked RFC Evidence]
    N --> P[Inconsistencies / Manual Review]

    O --> Q[First-seen Dates + Adoption Timeline]
    O --> R[Management Dashboard]
```

Module map (`src/openintel_rfc/`):

| Module | Responsibility |
| --- | --- |
| `models.py` | Pydantic models for every artefact; the integration contract |
| `config.py` | Constants, scoring parameters, output file names |
| `utils.py` | Deterministic IO, timestamp parsing, ID minting |
| `checklist_loader.py` | Load + validate the checklist DB and dictionary |
| `rfc_metadata.py` | RFC metadata interface (offline default; Datatracker/RFCXML seams) |
| `schema_checker.py` | Indicator × dictionary cross-check and queryability verdicts |
| `parquet_reader.py` | DuckDB/PyArrow Parquet reads with alias resolution |
| `signal_extractor.py` | Parquet rows → normalized `ObservedSignal`s |
| `openintel_source.py` | S3 partition discovery; stream (httpfs) and download modes |
| `sql_compiler.py` | Compiles the checklist into SQL evaluated during the scan |
| `scale_runner.py` | Streaming aggregation, checkpointing, exemplar sampling |
| `matcher.py` | Condition/indicator evaluation, timestamp cutoff |
| `ranking.py` | Score breakdown, confidence, candidate aggregation |
| `reasoning.py` | Structured decision traces and their prose summaries |
| `timeline.py` | First-seen dates and adoption trajectories |
| `review_queue.py` | Everything a human should look at, with severity |
| `llm_verifier.py` | Verification interface + deterministic offline backend |
| `report.py` | `report.md` and the schema-check report |
| `exporters.py` | JSON / CSV / Markdown writers |
| `dashboard_data.py` | The dashboard's only data-access layer |
| `tool_survey.py` | Generates the open-source tool survey |
| `cli.py` | `tool-survey`, `schema-check`, `analyze` |

See [`docs/architecture.md`](docs/architecture.md) for the full data flow and
extension points.

## Selected open-source tool stack

| Tool | Role | Why |
| --- | --- | --- |
| **DuckDB** | Default Parquet query engine | SQL directly over Parquet with projection and predicate pushdown; zero-setup, single-file, ideal for OpenINTEL-shaped columnar data |
| **PyArrow** | Parquet IO | The Parquet backend, and the fallback read path |
| **pandas** | DataFrame handling | Simple manipulation, CSV/JSON export, native Streamlit rendering |
| **Pydantic** | Typed models | Malformed checklists fail loudly at load time instead of producing wrong matches |
| **Streamlit** | Dashboard | Multipage management UI in pure Python |
| **Plotly** | Charts | Interactive rankings, timelines and distributions |
| **pytest** | Tests | End-to-end and unit coverage |

Full evaluation — including what was deliberately rejected and why — is in
[`docs/open_source_tool_survey.md`](docs/open_source_tool_survey.md).

## The RFC checklist / signature database

`data/rfc_checklists/dnssec_rfc_checklists.json`. Each RFC carries `rfc_id`, `title`,
`publication_date`, `protocol`, `specificity`, `description`, `references`, `notes`,
and a list of `indicators`. Each indicator has an `id`, `description`, `required`
flag, `weight`, an `ambiguous` flag, and a list of `conditions`:

```json
{
  "id": "rfc8078_cds_cdnskey_algorithm_zero",
  "description": "CDS or CDNSKEY record with algorithm field 0 (the delete signal)",
  "required": true,
  "weight": 10,
  "conditions": [
    {"field": "rr_type", "op": "in", "value": ["CDS", "CDNSKEY"]},
    {"field": "algorithm", "op": "equals", "value": 0}
  ]
}
```

Conditions within an indicator are ANDed. Supported operators: `equals`,
`not_equals`, `in`, `exists`, `contains`, `greater_or_equal`, `less_or_equal`.

Shipped RFCs: **4033** (with 4034/4035, base DNSSEC), **4509** (SHA-256 DS digest),
**5155** (NSEC3), **6605** (ECDSA), **7344** (CDS/CDNSKEY), **8078** (delete signal),
**8080** (EdDSA), **8624** (algorithm recommendations).

Two indicators are intentionally *not* satisfiable by the shipped dictionary, so the
missing-field paths are exercised by the demo rather than only by tests:
`rfc8624_validator_algorithm_support` (non-queryable) and
`rfc4033_dnssec_ok_negotiated` (partially queryable).

## OpenINTEL dictionary / schema alignment

`data/openintel_dictionary/sample_openintel_dictionary.json` describes each analysis
field with a `type`, `description`, `available_from` date, and the real OpenINTEL
column names it derives from:

```json
{
  "name": "algorithm",
  "type": "integer",
  "available_from": "2010-01-01",
  "openintel_native_fields": ["dnskey_algorithm", "ds_algorithm", "rrsig_algorithm",
                              "cds_algorithm", "cdnskey_algorithm"]
}
```

The schema checker walks every condition of every indicator and reports, in prose,
whether the corpus can answer it. `available_from` matters: the dictionary's `flags`
field only becomes available in 2016, so any indicator depending on it cannot speak
to adoption before then — and the report says so explicitly rather than returning a
confident zero.

## Timestamp cutoff

For each signal × RFC pair the pipeline compares the observation timestamp with the
RFC's publication date. If `observation_timestamp < rfc_publication_date` the match is
`timestamp_invalid`: its score is forfeited to `0.0`, it is excluded from ranking and
from `first_seen`, and it is pushed to the review queue at **high** severity. The
score that *would* have been awarded is preserved in `score_breakdown.timestamp_penalty`,
so a reviewer can see exactly what was withheld.

This is what separates "these bytes look like RFC 8078" from "this is evidence of
RFC 8078 adoption". A CDS record with algorithm 0 in 2016 is a real observation of
something — but it cannot be adoption of a document published in March 2017.

## Ranking

```
base_indicator_score      = sum(weight of matched REQUIRED indicators)
optional_match_bonus      = sum(weight of matched OPTIONAL indicators) * 0.5
required_match_bonus      = 2.0  if the RFC has >= 2 required indicators and all matched
missing_required_penalty  = 3.0 * (required indicators evaluated and not matched)
partial_match_penalty     = 2.0  if some but not all required indicators matched
ambiguity_penalty         = 2.0  if any matched indicator is flagged ambiguous

final_score = max(0, base + required_bonus + optional_bonus
                     - missing_required_penalty - partial_match_penalty
                     - ambiguity_penalty) * specificity_multiplier
```

Specificity multipliers: `very_high 1.5`, `high 1.25`, `medium 1.0`, `low 0.75`.
Confidence bands: `>=12 very_high`, `>=8 high`, `>=4 medium`, `>0 low`.

The effect is that a specific RFC outranks the broad one it builds on. A CDS record
with `algorithm=0` scores RFC 8078 at `17.25` (very_high) and RFC 7344 at `11.25`
(high) — both are true, and the ordering says which one explains the observation.

Every term is recorded in `ScoreBreakdown.steps` as readable arithmetic, so any
score can be recomputed by hand from the output.

## Reasoning traces

The pipeline emits **no hidden chain-of-thought**. It emits explicit, structured
decision records — one per signal × RFC evaluation:

```json
{
  "signal_id": "sig_0001",
  "rfc_id": "RFC 8078",
  "decision": "valid_match",
  "reasoning_summary": "Observed CDS record with algorithm=0 after RFC 8078 publication date.",
  "matched_conditions": [
    {"field": "rr_type", "op": "in", "expected": ["CDS", "CDNSKEY"], "observed": "CDS", "passed": true},
    {"field": "algorithm", "op": "equals", "expected": 0, "observed": 0, "passed": true}
  ],
  "failed_conditions": [],
  "timestamp_check": {
    "observation_timestamp": "2018-05-01",
    "rfc_publication_date": "2017-03-01",
    "valid": true,
    "explanation": "Observation occurs after RFC publication."
  },
  "score_breakdown": {
    "base_indicator_score": 10, "specificity_multiplier": 1.5,
    "required_match_bonus": 0, "missing_required_penalty": 0,
    "partial_match_penalty": 0, "timestamp_penalty": 0, "final_score": 15
  }
}
```

Each trace answers: which RFC was considered, which indicator was checked, which
OpenINTEL field was used, what passed, what failed, whether the timestamp was valid,
why the score is what it is, why one match outranks another, what evidence supports
the result, and what is missing or uncertain.

Decisions: `valid_match`, `partial_match`, `no_match`, `timestamp_invalid`,
`non_queryable`, `ambiguous`. `no_match` traces are kept — explaining why an RFC was
*rejected* is as important as explaining why one matched.

## Dashboard pages

| Page | Contents |
| --- | --- |
| 1. Overview | Corpus/checklist counters, matches per RFC, queryability split, review severity |
| 2. Schema Check | Dictionary fields, indicator queryability, missing fields, per-indicator reasoning |
| 3. RFC Checklists | Browse RFCs, publication dates, indicators, weights, conditions |
| 4. OpenINTEL Data Explorer | Sample rows, extracted signals, `rr_type`/`algorithm`/`digest_type` distributions, observations over time |
| 5. Matching Results | Ranked candidates with score, confidence, first-seen, matched fields, filters |
| 6. Reasoning Explorer | Per-trace matched/failed conditions, timestamp verdict, score breakdown — the transparency page |
| 7. Adoption Timeline | First-seen per RFC, monthly/yearly counts, domain/zone spread |
| 8. Review Queue | Severity-ranked items with evidence; mark accepted / rejected / needs follow-up |
| 9. Export Center | Download every JSON, CSV and Markdown artefact |

The dashboard reads `demo_output/` by default and lets you point at another output
directory from the sidebar.

## Platform support

| Component | Linux | Windows | macOS |
| --- | --- | --- | --- |
| Pipeline (`python -m openintel_rfc.cli …`) | yes | yes | yes |
| Test suite (`pytest`) | yes | yes | yes |
| Dashboard (`streamlit run dashboard/app.py`) | yes | yes | yes |
| `scripts/*.sh` | **yes — the target** | via Git Bash | yes |

The Python side is the portable contract and is verified on both Linux and
Windows. The shell scripts are written for the Linux server; they do run under
Git Bash, which is how they are exercised during development, but that is a
convenience rather than a promise. Nothing in the pipeline requires them — they
wrap the same CLI commands documented below.

**Artefacts are byte-identical across platforms.** That is a deliberate property,
not an accident, and three things are needed for it:

- JSON and Markdown are written with explicit `newline="\n"`. `Path.write_text`
  otherwise translates to CRLF on Windows, so the "two runs are byte-identical"
  guarantee would have held per-machine and quietly failed across machines.
- Paths recorded *inside* artefacts are normalized to forward slashes, so a run
  does not report `data\rfc_checklists\x.json` on one OS and
  `data/rfc_checklists/x.json` on another.
- CSV keeps the RFC 4180 `\r\n` that `csv.writer` emits on every platform, and
  `.gitattributes` marks `*.csv -text` so git does not rewrite it per checkout.

Verified: two runs into the same directory produce 13 of 13 identical artefacts,
including `report.md` and every CSV.

If you are on Windows and `make` is unavailable, use the raw `python -m
openintel_rfc.cli …` commands below; they are the same thing the Makefile runs.

## Documentation

| Document | Read it when |
| --- | --- |
| this README | orientation, the demo, interpreting output |
| [`docs/running_at_scale.md`](docs/running_at_scale.md) | **before any real-corpus run** — exact vs sampled, throttling, sizing |
| [`docs/architecture.md`](docs/architecture.md) | data flow, module map, extension points |
| [`docs/open_source_tool_survey.md`](docs/open_source_tool_survey.md) | why each dependency was chosen, and what was rejected |

## Installation

For the offline demo:

```bash
pip install -r requirements.txt
```

For a Linux server that will read the real corpus, use the script instead — it
also installs `boto3`, verifies that DuckDB's `httpfs` extension loads (streaming
fails without it), runs the demo and runs the tests:

```bash
./scripts/setup.sh
```

### Setup troubleshooting

**`bin/activate: No such file or directory`** — `python3 -m venv` failed and left a
skeleton behind. On Debian/Ubuntu the venv module needs a separate package:

```bash
sudo apt install python3-venv          # or python3.12-venv to match your interpreter
rm -rf .venv && ./scripts/setup.sh
```

The tell-tale sign is a `.venv/bin/` containing only `python` symlinks — no
`activate`, no `pip` — and an empty `site-packages`. `setup.sh` now detects and
recreates such a venv rather than reusing it, and says which package to install.

**Running under WSL on a `/mnt/<drive>/` path** — the code is fine there, but the
*virtualenv* should not be. pip on DrvFs is slow and virtualenv symlinks are
unreliable. Keep the checkout where it is and put the venv on the Linux
filesystem:

```bash
VENV_DIR=$HOME/.venvs/openintel ./scripts/setup.sh
VENV_DIR=$HOME/.venvs/openintel ./scripts/run_full_analysis.sh --sources nu \
    --start 2018-05-01 --end 2018-05-01 --dry-run
```

`setup.sh` warns when it notices this.

Python 3.10+. All commands below run from the repository root.
The package lives under `src/`, so either `pip install -e .` or set `PYTHONPATH=src`
(the `Makefile` and the scripts do this for you).

`boto3` is **not** in `requirements.txt`: it is only needed to reach the real S3
corpus, and the demo and test suite are fully offline without it.

## Demo commands

```bash
pip install -r requirements.txt

python data/sample_parquet/create_sample_parquet.py

python -m openintel_rfc.cli tool-survey --out docs/open_source_tool_survey.md

python -m openintel_rfc.cli schema-check \
  --checklists data/rfc_checklists/dnssec_rfc_checklists.json \
  --dictionary data/openintel_dictionary/sample_openintel_dictionary.json \
  --out demo_output

python -m openintel_rfc.cli analyze \
  --checklists data/rfc_checklists/dnssec_rfc_checklists.json \
  --dictionary data/openintel_dictionary/sample_openintel_dictionary.json \
  --parquet data/sample_parquet/sample_openintel.parquet \
  --out demo_output

streamlit run dashboard/app.py
```

Or simply `make demo && make dashboard`.

## Running against the real OpenINTEL corpus

The commands above use the synthetic fixture. For real measurements on a Linux
server there are four scripts, meant to be used in this order:

```bash
# 1. One-time setup. Idempotent, safe to re-run.
./scripts/setup.sh

# 2. Costs seconds, scans nothing. Reports the available sources, the partition
#    count, and whether the real schema can actually answer the checklist.
#    Do this for every new range.
./scripts/run_full_analysis.sh --sources nu --start 2018-05-01 --end 2018-05-01 --dry-run

# 3. One real day, end to end (~1 minute). Prove the path before scaling it.
./scripts/run_full_analysis.sh --sources nu --start 2018-05-01 --end 2018-05-01

# 4. Size the range you actually want, then fetch it.
./scripts/fetch_openintel.sh --sources nu,se --start 2015-01-01 --end 2021-12-31 --list
./scripts/fetch_openintel.sh --sources nu,se --start 2015-01-01 --end 2021-12-31 \
    --cache-dir /large/volume

# 5. The real run. Hours to days, and resumable — use tmux.
tmux new -s openintel
./scripts/run_full_analysis.sh --mode download --cache-dir /large/volume \
    --sources nu,se --start 2015-01-01 --end 2021-12-31 --pace-seconds 2
```

### Which sources exist

`fdns/basis=zonefile` publishes exactly: **`ch, ee, fed.us, fr, gov, li, nu, root,
se, sk`**. `.com` and `.nl` are **not** available. The `scale` command refuses to
start on a source OpenINTEL does not publish, because a source with no objects
produces no matches — which in the output is indistinguishable from a source with
no adoption.

### Prefer `--mode download` for anything large

OpenINTEL rate-limits on **request count**, not bytes. Streaming issues thousands
of small parallel HTTP range requests per object; downloading issues one sequential
64 MB-chunked GET. Measured on a real partition:

| Strategy | Per partition |
| --- | --- |
| Stream | **71 s** |
| Download, cold | 13.9 s fetch + 21.4 s scan = **35 s** |
| Download, cached re-scan | **21.4 s** |

Download mode is ~2× faster cold, ~3.3× faster on a re-scan, and far less likely to
be throttled. `run_full_analysis.sh` warns with concrete estimates if you are about
to stream a large range.

Thread count is not the lever it looks like: 20/8/4/2 threads measured 5.6/5.8/5.9/5.9 s
on a remote scan — the work is network-bound. Stream mode therefore caps threads at
8 by default; local scans get every core.

### Splitting across machines

Give each machine a disjoint date range (or a disjoint set of sources), then
gather the checkpoints and run the whole range against them — every partition is
already done, so it becomes a merge. **Verified byte-equivalent to a single run**,
because sharding uses the same merge path a single-machine run already takes.

Only checkpoints move: **~49 KB per 3 partitions, ~82 MB for a 6.3 TB run**. Each
one records the checklist version and a fingerprint of the compiled scan, so a
shard produced with a different checklist is rejected and recomputed rather than
silently merged. See [`docs/running_at_scale.md`](docs/running_at_scale.md)
section 4b.

### Sizing a run

| Source | Objects/day | Size/day | 2015–2021 (2,557 days) |
| --- | --- | --- | --- |
| `nu` | 1 | 0.37 GB | ~0.95 TB |
| `se` | 4 | 2.09 GB | ~5.3 TB |

`fetch_openintel.sh --list` reports the real total for your exact range and
compares it against free space, refusing a download that will not fit.

### Real-corpus behaviour worth knowing

These were all found by running against live data. Every one is a **silent**
failure — the pipeline keeps going and produces plausible, wrong output — so all
five are pinned by `tests/test_parquet_reader_real_schema.py`.

1. OpenINTEL has **no single `algorithm` column**: it has `dnskey_algorithm`,
   `ds_algorithm`, `rrsig_algorithm`, `cds_algorithm`, `cdnskey_algorithm`,
   `nsec3_hash_algorithm`, `nsec3param_hash_algorithm`, populated per record type.
   The reader COALESCEs them; binding to the first would read NULL for every CDS
   row and RFC 8078 delete signals could never match.
2. `timestamp` is **epoch milliseconds**. Read as nanoseconds it maps everything to
   1970-01-01 and destroys the publication-date cutoff. The unit is detected from
   magnitude.
3. DuckDB exposes the Hive path segments `year`/`month`/`day` as columns and types
   them from the literal text (`year` BIGINT, `month`/`day` VARCHAR). They are not
   fallbacks for `timestamp`; datetime fields are never coalesced.
4. The scan projects `<decoded> AS "timestamp"`, but OpenINTEL's own column has the
   same name and DuckDB resolves the base column first. The cutoff compares the
   decoded expression, never the bare identifier.
5. `measurement_id` does not exist in the real corpus. It reads as null; no
   indicator tests it, so matching is unaffected.

Full detail, including the throttling escalation ladder, is in
[`docs/running_at_scale.md`](docs/running_at_scale.md).

### Outputs

`schema-check` writes `queryable_indicators.json`, `non_queryable_indicators.json`,
`schema_check_report.md`, `schema_check.csv`, `schema_check.json`.

`analyze` writes `observed_signals.json`, `rfc_matches.json`, `reasoning_traces.json`,
`review_queue.json`, `adoption_timeline.json`, `ranked_candidates.json`, `report.md`,
`run_manifest.json`, and CSV equivalents for matches, review queue, timeline, signals
and traces.

`scale` writes all of the above plus the `schema-check` artefacts, so one output
directory fully describes its own run and the dashboard needs no second command.
`run_manifest.json` records `rows` (the real scanned count) and `sampled: true`.

## Testing

```bash
pytest                      # 718 tests, fully offline
pytest -m network           # opt-in; needs OPENINTEL_NETWORK_TESTS=1
```

Beyond the unit suite there is a full-system gate that checks what pytest cannot
reach on its own — the documented commands, engine equivalence, determinism across
runs, every dashboard page, the shell scripts, and one real partition from
OpenINTEL (self-skipping when offline):

```bash
make verify          # or: bash scripts/verify_all.sh
```

79 checks. It is Linux/Git-Bash only, since it drives the shell scripts.

Covers the schema checker, signal extraction, matching, all seven condition
operators including the missing-value rule, the timestamp cutoff from five angles,
ranking order and exact scores, `ScoreBreakdown.steps` arithmetic reconstruction,
reasoning-trace completeness, the review queue, timeline first-seen computation,
DuckDB/pandas engine equivalence, determinism, the real-OpenINTEL schema
regressions, the SQL compiler, the scale runner's checkpoint/resume behaviour, a
**cross-validation of the SQL and Python matchers**, all CLI commands end-to-end,
and the dashboard data loader.

## Limitations

- **The pipeline does not prove adoption.** It ranks candidates consistent with
  observable signals and timestamp constraints.
- The sample Parquet is synthetic. Numbers in the demo report describe that fixture,
  not the real DNS.
- Matching is **record-level**. Zone-level conclusions ("this zone adopted NSEC3")
  need aggregation the pipeline does not perform.
- In a `scale` run, **scores and reasoning traces come from a bounded sample** while
  counts are exact. A score is a lower bound, and an RFC with many observations can
  be missing from the ranking if no sampled exemplar cleared the threshold. Raise
  `--exemplars` if a specific RFC matters to your analysis.
- `distinct_domains` at scale is a lower bound: `approx_count_distinct` returns a
  number rather than a mergeable sketch, so per-partition results cannot be unioned
  exactly.
- The DNSSEC record-type prefilter is what makes a large run tractable, and it
  assumes every DNSSEC observation carries one of the expected `rr_type` values. An
  observation with a null or unexpected type is not counted.
- The checklist DB is hand-curated for eight DNSSEC RFCs. The LLM-assisted extraction
  path for building it at scale is designed but not wired to a backend.
- Some RFC requirements are simply not observable in passive forward-DNS measurement
  (resolver-side behaviour, DO-bit negotiation, validation outcomes). These are
  surfaced as non-queryable rather than silently ignored.
- `first_seen` is bounded by measurement coverage: it is the first date *in this
  corpus*, not the first date on the Internet. Where a field's `available_from`
  postdates an RFC, the schema report says so explicitly.
- OpenINTEL does not publish `.com` or `.nl` under `basis=zonefile`, so no
  conclusion can be drawn about them from this corpus.

## Next steps

1. Aggregate record-level matches to zone- and TLD-level adoption statistics — the
   single most valuable next step, since "6.6M records" is not "N zones".
2. Replace exemplar-derived scoring with exact per-RFC scoring in SQL, removing the
   lower-bound caveat on `scale` scores.
3. Carry a mergeable distinct-count sketch (HLL) through checkpoints so
   `distinct_domains` becomes exact.
4. Wire `rfc_metadata.py` to the IETF Datatracker API so publication dates come from
   the source of truth rather than the checklist file.
5. Wire `llm_verifier.py` to a real structured-output backend for the ambiguous and
   partial cases, keeping the deterministic verifier as the offline default.
6. Expand the checklist DB beyond DNSSEC, with LLM-assisted extraction from RFCXML
   plus human review through the existing review queue.
7. Add zone-level time-series regression to distinguish genuine adoption events from
   measurement artefacts.
