# Adding an RFC to the checklist

A worked example, start to finish. Every command and every output below was
actually run; the numbers are real.

The checklist lives in `data/rfc_checklists/dnssec_rfc_checklists.json`. Adding an
RFC means adding one entry to `rfcs[]`. The editing is trivial — the work is
deciding *what is observable* and *how strongly it attributes*.

---

## Step 0. Decide whether the RFC is observable at all

This is the step that matters, and the one that is easy to skip.

Ask: **what would appear in a passive forward-DNS measurement if someone deployed
this?** Three honest outcomes:

| | Example | What to do |
| --- | --- | --- |
| A record type or field value exists *only because* of this RFC | RFC 5155 defines NSEC3; RFC 8080 registers algorithms 15/16 | Ideal. `specificity: very_high` |
| The RFC's mechanism is visible but shared with others | RFC 5702 registers algorithm 8, which is also just "how most zones sign" | Fine, but `high` or `medium`, not `very_high` |
| The RFC constrains behaviour you cannot see | RFC 8624 recommends algorithms; resolver-side validation; DO-bit negotiation | Add it with `ambiguous: true`, or with a field the dictionary lacks, and let the review queue carry it |

An RFC that is not observable is still worth adding — the pipeline is explicitly
designed to report "this cannot be answered from this corpus" rather than to
quietly omit it. What is *not* acceptable is inventing an indicator that looks
decisive but is really measuring something else.

---

## Step 1. Write the entry

Worked example: **RFC 5702**, which registers DNSSEC algorithms 8 (RSASHA256) and
10 (RSASHA512).

```json
{
  "rfc_id": "RFC 5702",
  "title": "Use of SHA-2 Algorithms with RSA in DNSKEY and RRSIG Resource Records for DNSSEC",
  "publication_date": "2009-10-01",
  "protocol": "DNSSEC",
  "specificity": "high",
  "related_rfc_ids": [],
  "description": "Registers DNSSEC algorithms 8 (RSASHA256) and 10 (RSASHA512).",
  "references": ["https://www.rfc-editor.org/info/rfc5702"],
  "notes": "Algorithm 8 is the most widely deployed DNSSEC algorithm, so a match is evidence the mechanism is in use rather than a deliberate recent choice.",
  "indicators": [
    {
      "id": "rfc5702_rsasha2_algorithm",
      "description": "Record uses DNSSEC algorithm 8 or 10 (RSASHA256 / RSASHA512).",
      "required": true,
      "weight": 9,
      "ambiguous": false,
      "conditions": [
        {"field": "algorithm", "op": "in", "value": [8, 10]}
      ]
    },
    {
      "id": "rfc5702_rsasha2_on_key_or_signature",
      "description": "The RSA/SHA-2 algorithm appears on a key, delegation or signature record.",
      "required": false,
      "weight": 3,
      "ambiguous": false,
      "conditions": [
        {"field": "rr_type", "op": "in", "value": ["DNSKEY", "DS", "RRSIG", "CDS", "CDNSKEY"]},
        {"field": "algorithm", "op": "in", "value": [8, 10]}
      ]
    }
  ]
}
```

### Field reference

| Key | Notes |
| --- | --- |
| `rfc_id` | `"RFC NNNN"`, with the space. Used as a dict key everywhere |
| `publication_date` | RFC Editor month, normalized to the 1st. **This is the cutoff** — get it right or you invent or destroy adoption |
| `specificity` | `very_high` 1.5, `high` 1.25, `medium` 1.0, `low` 0.75 — the ranking multiplier |
| `indicators[].required` | All required indicators must match for `valid_match`. Optional ones corroborate at half weight |
| `indicators[].weight` | Existing entries use 9–10 for a defining signature, 3–4 for corroboration |
| `indicators[].ambiguous` | `true` when the observation fits but does not *attribute*. Costs 2.0 and routes to review |
| `conditions[]` | ANDed. Ops: `equals`, `not_equals`, `in`, `exists`, `contains`, `greater_or_equal`, `less_or_equal` |

Condition `field` names are the **normalized** analysis fields (`rr_type`,
`algorithm`, `digest_type`, `key_tag`, `flags`), never raw OpenINTEL column names.
The dictionary maps normalized names onto the real columns.

---

## Step 2. Check it is queryable

```bash
python -m openintel_rfc.cli schema-check \
  --checklists data/rfc_checklists/dnssec_rfc_checklists.json \
  --dictionary data/openintel_dictionary/sample_openintel_dictionary.json \
  --out demo_output
```

Real output for the entry above:

```
19 indicators across 9 RFCs: ambiguous=2, non_queryable=1, partially_queryable=1, queryable=15

rfc5702_rsasha2_algorithm            queryable
  Indicator rfc5702_rsasha2_algorithm is queryable because all fields it
  references exist in the OpenINTEL dictionary: algorithm (integer).
```

If it says `non_queryable`, the dictionary is missing a field — see Step 5.

---

## Step 3. Run it and read the trace

```bash
python -m openintel_rfc.cli analyze \
  --checklists data/rfc_checklists/dnssec_rfc_checklists.json \
  --dictionary data/openintel_dictionary/sample_openintel_dictionary.json \
  --parquet data/sample_parquet/sample_openintel.parquet \
  --out demo_output
```

```
73 signals x 9 RFCs -> 657 evaluations (137 valid, 14 timestamp-invalid), 9 ranked candidates
  1. RFC 8078  score=17.25    very_high  observations=12
  ...
  4. RFC 5702  score=13.125   very_high  observations=24
  5. RFC 6605  score=13.125   very_high  observations=10
```

**Do not stop at "it appeared."** Open the reasoning trace and confirm it matched
for the reason you intended:

```
RFC 5702 matched signal sig_0002: the required indicator rfc5702_rsasha2_algorithm
passed because algorithm=8 is in [8, 10]. Corroborating indicators also matched:
rfc5702_rsasha2_on_key_or_signature. The observation on 2011-02-15 is 502 days
after RFC 5702's publication on 2009-10-01, so the timestamp is valid.

base_indicator_score = 9.0 (matched required indicators: rfc5702_rsasha2_algorithm)
optional_match_bonus = 1.5 = 3.0 x 0.5 (matched optional: rfc5702_rsasha2_on_key_or_signature)
final_score = max(0, 10.5) * 1.25 = 13.125
```

Dashboard page 6 is the same thing with filters.

### Sanity questions

- **Did it outrank something more specific?** RFC 5702 landing above RFC 8078 on a
  CDS delete signal would mean the specificity is miscalibrated.
- **Is `first_seen` after `publication_date`?** It is enforced, but a surprising
  value usually means the publication date is wrong.
- **Did the review queue grow in a way you did not expect?** New close-ranking or
  ambiguity items are the pipeline telling you the entry does not attribute as
  cleanly as you assumed.

---

## Step 4. Check it against real data

The sample fixture is synthetic. Before trusting the entry, point it at one real
day:

```bash
./scripts/run_full_analysis.sh --sources nu --start 2018-05-01 --end 2018-05-01 --dry-run
./scripts/run_full_analysis.sh --sources nu --start 2018-05-01 --end 2018-05-01
```

The `--dry-run` reports whether the fields your indicator needs actually resolve
against the real 98-column schema. A field can exist in the dictionary and still
have no real column behind it.

---

## Step 5. When the field does not exist yet

Worked example: **RFC 9276**, which recommends NSEC3 with 0 extra iterations. That
needs `nsec3_iterations`, which the shipped dictionary does not define.

`schema-check` says so, precisely:

```
Field 'nsec3_iterations' is referenced by 1 indicator(s)
(rfc9276_nsec3_zero_iterations) but is not defined in the OpenINTEL dictionary;
every condition on it is unanswerable.

Indicator rfc9276_nsec3_zero_iterations is non-queryable: the field carrying its
discriminating value, nsec3_iterations, is absent from the OpenINTEL dictionary,
and the only field that remains, rr_type (string), merely scopes which records are
considered ... so nothing testable is left to attribute an observation to RFC 9276.
```

The indicator is **skipped, not failed** — it never counts against the RFC — and a
`non_queryable_indicator` review item is raised. That is a legitimate end state if
the corpus genuinely cannot answer it.

If the corpus *can* answer it, add the field to
`data/openintel_dictionary/sample_openintel_dictionary.json`:

```json
{
  "name": "nsec3_iterations",
  "type": "integer",
  "description": "Extra NSEC3 hash iterations beyond the first.",
  "available_from": "2010-01-01",
  "openintel_native_fields": ["nsec3_iterations", "nsec3param_iterations"],
  "nullable": true
}
```

`openintel_native_fields` must list **real OpenINTEL column names**. The reader
COALESCEs them in order, which is how one normalized field spans the per-record-type
columns OpenINTEL actually publishes. Confirm the names against a real partition:

```bash
./scripts/run_full_analysis.sh --sources nu --start 2018-05-01 --end 2018-05-01 --dry-run
```

Re-running `schema-check` then gives:

```
20 indicators across 10 RFCs: queryable=16, non_queryable=1, ...
rfc9276_nsec3_zero_iterations      queryable
```

Two cautions on `available_from`: it is the date the field became *reliably
populated*, and the schema checker warns when it postdates the RFC — a first-seen
date is then a lower bound on the corpus, not on the Internet. And listing a
native column that does not exist makes the field silently all-null rather than
raising.

---

## Step 6. Add a test

Existing per-RFC expectations live in `tests/test_matcher.py` and
`tests/test_ranking.py`. Pin the score, not just the fact of a match:

```python
def test_rfc5702_matches_rsasha256(checklist_db, signal_factory):
    signal = signal_factory(rr_type="DNSKEY", algorithm=8,
                            timestamp=datetime(2015, 1, 1))
    match, _ = match_signal_to_rfc(signal, checklist_db.get("RFC 5702"))
    assert match.decision == "valid_match"
    assert match.score == pytest.approx(13.125)
```

Then re-run the whole gate — a new RFC changes evaluation counts everywhere:

```bash
pytest
make verify
```

`scripts/verify_all.sh` asserts specific totals (`73 signals x 8 RFCs -> 584
evaluations`, `8 ranked candidates`). **Adding an RFC will fail those checks by
design** — update the expected numbers in the same commit, so the change is
visible in review rather than silently absorbed.

---

## Step 7. Re-run anything already computed

Checkpoints record `checklist_version` and a `scan_sql_sha1` of the compiled
scan. Changing the checklist invalidates them, and a `scale` run will **recompute
every partition** rather than merge stale aggregates.

That is the safe behaviour, but it is expensive. Bump `checklist_version` when you
change the checklist, and expect a full rescan — or keep the old output directory
alongside the new one if you want to compare.

---

## Common mistakes

| Mistake | What happens |
| --- | --- |
| Wrong `publication_date` | Real adoption is discarded as timestamp-invalid, or pre-standard deployment is counted as adoption. The most damaging single error |
| `specificity: very_high` on a shared mechanism | It outranks the RFC that actually explains the observation |
| Everything marked `required` | One missing field drops the whole RFC to `partial_match`, score 0 |
| Native column name in a `conditions[].field` | Always `non_queryable`; conditions use normalized names |
| Indicator that restates another RFC's signature | Both match every time and generate permanent `close_ranking` review items |
| Assuming "it appeared in the ranking" means it is right | Read the trace. It might be matching on the corroborating indicator only |

---

## Checklist

- [ ] Decided what is genuinely observable, and set `specificity` honestly
- [ ] `publication_date` checked against the RFC Editor record
- [ ] `schema-check` reports the expected queryability
- [ ] `analyze` runs and the reasoning trace shows the intended reason
- [ ] Ranking against neighbouring RFCs still makes sense
- [ ] Verified against one real OpenINTEL day
- [ ] Test added pinning the score
- [ ] `pytest` and `make verify` green, with expected totals updated
- [ ] `checklist_version` bumped if any `scale` output exists


## The four questions the pipeline asks (checklist 0.2.0)

Adding an RFC is answering these in order. The tooling answers the last two for
you and writes down why, which is what makes the result explainable rather than
asserted.

### 1. What does a match *mean*? (`signal_type`)

Not every RFC is an adoption story, and treating them alike inverts a third of
the corpus.

| `signal_type` | A match means | Examples |
| --- | --- | --- |
| `adoption` | the mechanism is deployed | RFC 6605 (ECDSA), RFC 9276 (NSEC3 params) |
| `non_conformance` | a **deprecated** mechanism is still published | RFC 9905 (SHA-1 sigs), RFC 9906 (ECC-GOST) |
| `meta` | the document defines a process or resolver behaviour | RFC 9904, RFC 8198, RFC 7583 |

A `non_conformance` match is bad news. Counting it as adoption would report a
zone that ignored a deprecation as a zone that adopted something.

### 2. Is the field *evidence*, or is it *provenance*?

`domain`, `zone`, `source` and `measurement_id` identify **which observation this
is**. The matcher deliberately does not expose them as testable fields, so an
indicator resting on one can never match — and `schema-check` now says exactly
that instead of calling it queryable.

This is not a technicality. It is why RFC 9615 (bootstrapping via `_signal`
labels) and RFC 7672 (SMTP DANE at `_25._tcp`) classify as unmeasurable here:
their signature is an **owner-name pattern**, and this signal model testifies to
record content, not to names. Wanting them measured means changing the signal
model, not the condition.

The SQL path would happily answer a condition on `domain` — it is just a column —
which is how the two engines came to disagree. If you add a field, decide which
side of this line it falls on, or the engines will silently diverge.

### 3. Can this corpus answer it? (`schema-check`)

```bash
openintel-rfc schema-check --out out/schema
python reporting/rfc_classification.py out/schema/schema_check.json     data/rfc_checklists/dnssec_rfc_checklists.json out/classification
```

Every indicator lands on `queryable`, `partially_queryable`, `ambiguous` or
`non_queryable`, each with the sentence that justifies it. The per-RFC roll-up in
`rfc_classification.md` adds the verdict a person reads: **measurable**, **partly
measurable**, **ambiguous only**, **not measurable here**.

An RFC classifying as "not measurable here" is a *result*, not a failure. Eight
of the thirty do, and the report says which field made each one unanswerable.

### 4. When could an answer first exist? (`observable_from`)

An RFC published before the fields its indicators need is **left-censored**: a
first-seen date is an upper bound on the lag, never a measurement of it. Eight of
the thirty are, and `rfc_classification.md` flags each with ⚠ and the date the
corpus could first have seen it.

## What adding an RFC costs

Adding an entry changes `checklist_version`, which **invalidates every existing
checkpoint** — by design, so a result can never mix two checklists. Plan on a
rescan. For a local corpus that is cheap (the reverse corpus rescans in about an
hour); for a streamed OpenINTEL range it is the full walk again, which is one
more reason to mirror rather than stream.

Two things worth re-running afterwards, because they are the ones that catch a
badly specified indicator:

```bash
pytest tests/test_scale_runner.py -k "agree"   # the two engines must still match
bash scripts/verify_all.sh                     # end-to-end gate
```

The engine-agreement tests are not ceremony. They are what surfaced both real
bugs found while extending the checklist to 30 RFCs: a provenance field being
answerable in SQL but not in Python, and a zero-scoring `ambiguous` match keeping
an adoption verdict on an observation that predated its own RFC.
