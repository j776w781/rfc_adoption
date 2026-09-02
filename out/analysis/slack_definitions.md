Hi — big update, and it's mostly about *definitions* rather than new data. Short version: we've been using one word ("adoption") for three different things, and once I split them the numbers started disagreeing with some of what we've been saying. Everything below is on the `server-full-run` branch.

*First — I merged your `fetch-tweak` branch.* Your retry on `list_partition_keys` filled a real gap: I'd only hardened the GET/scan path, so a throttled LIST was still aborting whole runs. I kept it and moved the classification into a shared `retry.py` so both paths agree. Four changes to it, all things I'd hit earlier and hadn't written down anywhere you could see: 403 is *throttling* here not a permission failure (nginx fronts the store and blocks with 403 + its own HTML; only an `AccessDenied` XML body means the credential is wrong, and that one must fail fast); added equal jitter, because every shard backing off on the same schedule retries in lockstep and stays throttled; the loop ran `range(15)` but gave up at `attempt == 9`; and `fetch_openintel.sh` slept 20s after every *successful* fetch, which is now a knob (`OPENINTEL_PACE_SECONDS`, default 0). Shout if you disagree with any of that.

━━━━━━━━━━━━━━━━━━━━━━━━━━━

*1. The new definition: three stages, not one date*

"RFC 8080 was adopted after 5.6 years" bundles five claims and we observe one of them. The first occurrence of Ed25519 was *one zone*. Nine years on it's at 0.3% of signed delegations. Both "adopted after 5.6 years" and "never adopted" are defensible readings of that sentence, which is what makes it unusable.

So it's split into three stages, each defined by an operation on the data:

```
  1  first seen        value present on >=1 zone, any RIR        -- somebody did it once
  2  partial usage     P(value | signed delegations) >= 1%       -- in real use, not the norm
                       AND on >= 10 distinct zones
  3  common usage      P(value | signed delegations) >= 10%      -- a normal choice
                       AND on >= 10 distinct zones
```

and three intervals between them:

```
  onset          publication -> first seen    how long until anyone did it
  establishment  first seen  -> partial       novelty to real use
  ascent         partial     -> common        real use to normal
```

*The thresholds were swept, not chosen.* This is the part I'd most like you to check. Moving the threshold from 0.5% to 60% changes the number of qualifying algorithms exactly twice:

```
   0.5% - 3%    6 algorithms
   4%  - 25%    4 algorithms      <- cliffs at 4% and 30%
   30% +        3 algorithms
```

1% and 10% each sit mid-plateau, so partial can be anywhere in 0.5–3% and common anywhere in 4–25% without changing a single result. Picking 4% or 30% would put us on a cliff and the answer would be an artefact of the number.

*The >=10 zone guard* exists because a percentage means different things at different dates. The panel grew *201x* over the series (32 signed delegations in 2011-05, 6,444 in 2026-08), so one zone was 3.1% of it then and is 0.016% now. Without the guard, RSASHA256 and RSASHA1-NSEC3 both "reach 1%" in 2011-05 *on a single zone*. A >=25 guard over-corrects and pushes RSASHA1-NSEC3 from 2.0y to 7.8y purely because its contemporaries were few.

*The funnel — this is what splitting buys us:* 14 changes reach first seen, *9* reach partial, *7* reach common. Five never get past being seen (DSA, ECC-GOST, Ed25519, Ed448, GOST digest); two reach real use and stall (RSASHA512, ECDSAP384). Under a single "adoption date" all fourteen looked adopted.

```
  interval        n       range        median   spread
  onset         14/14   0.5 - 10.1y     3.3y     9.6y
  establishment  9/14   2.0 -  6.4y     2.2y     4.4y
  ascent         7/14   0.0 -  3.8y     0.0y     3.8y
```

*Almost all the variance is in onset.* Establishment sits at ~2.2y for 7 of the 9 that reach it, whatever the mechanism and whatever the decade.

*One caveat I want to flag rather than bury:* ascent is degenerate before ~2015 and those 0.0y entries do NOT mean "spread instantly". At the 2011-05 crossing the panel held 32 signed delegations, so 1% and 10% are 0.3 and 3.2 zones — a gap one operator closes in under a month, below our monthly sampling. Only two crossings are actually resolvable (ECDSA-P256 0.8y, SHA-384 3.8y). *Please don't let me quote a median ascent.*

*Vocabulary:* "adoption" is retired as a measurement term. It's fine in "we study DNSSEC RFC adoption"; it's wrong in any sentence with a number. Two rules that would have caught every retraction we've had: *no prevalence without its population* (write `P(x | population)`), and *no first occurrence without its n*. I added a third this week — see the Ed25519 item below.

━━━━━━━━━━━━━━━━━━━━━━━━━━━

*2. Bottom-up logic*

Built from the RFC text upward, and the unit is the *observable change, not the RFC*. RFC 5702 defines two algorithms that appeared ten months apart and RFC 6605 two that differ by four; an RFC-level date averages away a real, repeated pattern.

*Step 1 is testability, and it changed the picture.* Of the 19 RFCs we classify measurable, only *11 were ever scanned against a corpus that could hold their evidence*:

```
  observed                   11   3110 4033 4034 4509 5155 5702 5933 6605 7344 8078 8080
  scanned, no match           4   9558 9563 9905 9906
  NOT YET SCANNED             2   5011 9276    <- forward run predates them
  no corpus can evidence it   2   6698 7671    <- no TLSA anywhere
```

The reverse corpus carries *NS and DS records only*, and our forward run still covers just 8 RFCs under the old checklist. So the 22 RFCs we added later were tested against delegation data alone, and anything needing DNSKEY, RRSIG, NSEC3PARAM or TLSA had nothing to match. *RFC 5011 and 9276 are not negative results* — re-running the forward scan under checklist 0.2.2 settles both. A blank and a null were previously indistinguishable in our tables, which I think is the single worst thing that was wrong.

*Step 2 — grouping by the implementation change required.* Derived from what an implementer must actually do, then checked against onset. The bands don't overlap:

```
  A  New codepoint, primitive already linked in   RFC 5702        0.5y
  B  Same crypto, new signalling                  RFC 5155 alg 7  1.4y
  C  New record type, existing infrastructure     RFC 8078        1.4y
  D  New cryptographic primitive                  5933/6605/8080  2.5 - 3.9y
  E  Deprecation                                  9905/9906       inverted clock, see below
```

*What separates them is whether new cryptographic code must ship at both ends*, not algorithmic difficulty — Ed25519 isn't harder to implement than RSA/SHA-512. Group D needs a signer *and* a validator to agree before anything is publishable; A, B and C need one party to change a value it already supports. RFC 5702 §8.1 says the quiet part out loud: _"The signature scheme RSASSA-PKCS1-v1_5 is chosen to match the one used for RSA/SHA-1 signatures. This should ease implementation."_

*Step 3 — the finding I think is the headline: onset does not predict spread.*

*Pearson r = -0.14 over 14 observable changes.* The two most prevalent mechanisms were *slower* than average to appear, and half the fastest are nowhere:

```
  SHA-256 DS digest   onset 2.9y  ->  P = 98.28%
  ECDSAP256SHA256     onset 3.7y  ->  P = 67.95%
  RSASHA512           onset 0.8y  ->  P =  0.37%
  GOST DS digest      onset 0.8y  ->  P =  0.11%
  ECC-GOST            onset 2.5y  ->  P =  0.00%
```

This is the *evidence for* splitting the definition rather than an assumption behind it. "First appeared after 0.8 years" and "used by 0.37% of signed delegations" are both true of RSASHA512, and one adoption date reports only the flattering one.

*Step 4 — deprecation runs on a different clock.* The observable is what *persists*, so onset is meaningless and residue is the quantity:

```
  RFC 9906 (ECC-GOST)  0 records after publication           -- genuinely complete
  RFC 9905 (SHA-1)     P(SHA-1 | signed reverse delegations) = 23.51%
                         signature alg 5/7    7.81%  (514 zones)
                         DS digest type 1    21.77%  (1,433 zones)
                         both                          400 zones
```

RFC 9906 documented an ending rather than causing one. The two halves of 9905 need different remedies — replace the DS at the parent vs reissue the child's keys — so they must be two numbers, never one "SHA-1 exposure".

━━━━━━━━━━━━━━━━━━━━━━━━━━━

*3. Two corrections, one of them to something I told you*

*RFC 9905 was reporting zero.* It showed 0 observations against 15,966 non-conforming DS records sitting in the corpus. Cause: its DNSKEY/RRSIG indicator was marked `required`, and a delegation-only corpus contains no such records, so every match scored 0.0 and vanished from the timeline. Two fixes in checklist 0.2.2 — that indicator is now alternative evidence rather than a precondition, and I added a missing `digest_type = 1` indicator, since 9905 closes the SHA-1 *digest* as well as the *signature* and nothing covered it. *The 23.51% above is computed straight from the corpus; the timeline won't show it until we rescan.*

⚠️ *In my last message I told you "that residual is exactly what RFC 9905's non-conformance signal now measures." That was wrong — it wasn't measuring it at all.* Sorry, please re-read that paragraph with this correction.

*Ed25519 onset is 3.9 years, not 5.6.* Every figure I've given you came from the reverse corpus alone. The forward corpus has Ed25519 in `.se` from *2021-01* — 53,365 distinct domains, 6.6M observations, not a stray. Hence a third vocabulary rule: *no first occurrence without naming the corpora searched.* Existence is a minimum over all available evidence, so a date from one corpus is an upper bound until the others are checked. Quoting 5.6y while holding forward data saying 3.9y is the same class of error as quoting a share without its population.

━━━━━━━━━━━━━━━━━━━━━━━━━━━

*4. Top-down logic*

Six categories by conceptual impact, then mapped down to RFCs:

```
  protocol_foundation     4033 4034 4035 6840 9364
  crypto_agility          3110 3658 4509 5702 5933 6605 8080 9558 9563
  authenticated_denial    5155 9276 8198 9077
  key_lifecycle           5011 6781 7344 7583 8078 9615
  applications (DANE)     6698 7671 7672
  deprecation             9905 9906 8624 9904
```

*The important design decision:* a category's numbers are exactly its members' numbers — nothing is measured independently at this level. So "meeting in the middle" is a *check*, not a rhetorical device: if a category's story isn't visible in its members' rows, the output says the category has no evidence rather than letting an average paper over it. It also reports which RFCs in a category have no observable change configured at all, i.e. where the taxonomy reaches further than the data.

The crosswalk between the two directions is the interesting bit — the implementation groups cut across the conceptual categories, and the *groups* are what predict onset while the *categories* are what's communicable. `crypto_agility` mixes Group A (0.5y) and Group D (3.9y) changes, so its category-level onset spread is wide and says almost nothing. Worth deciding which cut we lead with in the writeup.

━━━━━━━━━━━━━━━━━━━━━━━━━━━

*5. The script*

`scripts/full_timeline.py` — builds the whole timeline off the local cache and runs both analyses. *Entirely offline*: OpenINTEL is already mirrored, so nothing lists or fetches from the store and there's no endpoint left to throttle us.

```bash
python scripts/full_timeline.py \
    --roots /mnt/bigdisk/openintel \
    --roots /mnt/spill/openintel \
    --roots out/reverse/corpus \
    --out out/full_run --threads 16 --memory-limit 48GB
```

*Multiple roots is the load-bearing feature*, because part of the cache moved to a second drive and nothing records that move. A source-day can now have files on both, and *reading one root at a time reports a partial day as a complete one* — which is indistinguishable from a month when fewer names were signed, so it'd be read as a measurement. Files are merged by `(source, date, filename)` identity across roots:

• same day, different files, two drives → merged, flagged `split_across_roots`
• same file on both drives (a partial move left a copy) → counted *once*
• file matching no known layout → *excluded and reported*, never silently dropped

Three layouts recognised: ours (`<basis>/<source>/<YYYY-MM-DD>/`), OpenINTEL's Hive-style (`source=/year=/month=/day=`), and a loose date fallback. The reverse corpus is just another root.

*Four stages, each resumable and skippable* (`--stage`):

```
  index     walk every root, merge          -> inventory.json
  extract   one pass per source-day         -> checkpoints/, timeline_monthly.csv
  analyse   bottom-up + top-down            -> bottom_up.json, top_down.json, comparison.json
  report    digest + compact bundle         -> summary.md, analysis_bundle.json
```

`extract` writes one checkpoint per source-day and skips what's done, so an interrupted 14 TB run resumes where it stopped rather than at the beginning. Re-analysing is free — it reads the timeline, not the corpus:

```bash
python scripts/full_timeline.py --stage analyse --stage report --out out/full_run
```

*The timeline is long, not wide* — one row per `(source, month, dimension, value)` across 16 dimensions (algorithms per record type, digests, NSEC3 params, DNSKEY flags, RSA key sizes, TLSA). A wide table would need its schema fixed in advance and every new algorithm number would need a migration. *Every dimension emits its own `_total` row*, so a share is always recomputable against the population it came from — that's the retracted-10x lesson encoded rather than remembered.

*Both directions are configuration, not code.* `data/analysis_config.json` holds the observable changes, the implementation groups, the categories and the thresholds. Add a row to measure a new observable; move an RFC between categories to re-cut the taxonomy. Neither needs Python touched.

```bash
--no-top-down / --no-bottom-up      # run one direction
--config my_taxonomy.json           # a different cut entirely
```

*Reading the output* — three states are easy to confuse and the difference matters:

```
  common / partial / seen_only   observed, and how far it got
  scanned_no_match               we asked and the answer is no  -- a real null
  no_corpus_coverage             corpus can't carry the record type -- NOT a result
  residue                        deprecation; the number is what persists
```

Plus `left_censored`, which marks a first sighting in the corpus's opening month where onset is an upper bound, not a measurement.

*Validation:* indexes your 975 source-days across all 5 RIRs; a simulated production split correctly merges a two-drive day and counts 20 duplicated files once; reproduces the known figure (alg 13 = 8,569/13,410 DS records = 63.9% on 2026-08). 814 tests pass, `verify_all.sh` 80/81 (the one failure is "working tree clean", expected with uncommitted work).

━━━━━━━━━━━━━━━━━━━━━━━━━━━

*What I'd like from you*

1. *The thresholds.* 1% and 10% are mid-plateau and robust, but they're still our choice. Does "partial / common usage" match how you'd describe those stages, or would you cut them differently?
2. *Which cut leads the writeup* — implementation groups (predictive) or conceptual categories (communicable)?
3. *The forward rescan.* RFC 5011 and 9276 are unresolved purely because the forward run predates the 30-RFC checklist. Worth queueing on the server, or are they low enough value to leave?

Docs are in `docs/stages.md` (the three stages), `docs/bottom_up.md` (the RFC-by-RFC pass), `docs/vocabulary.md` (the terms) and `docs/full_run.md` (the runbook). Happy to walk through any of it.
