Hi — update on the definitions work, plus a script I'd like to run on the server if we can get it in tonight.

Short version: we've been using one word ("adoption") for three different things, and once I split them properly some of our numbers stopped agreeing with what we've been saying.

━━━━━━━━━━━━━━━━━━━━━━━━━━━

*1. The new definition: three stages instead of one date*

"RFC 8080 was adopted after 5.6 years" bundles several claims and we observe exactly one of them. The first occurrence of Ed25519 was *one zone*. Nine years later it's on 0.3% of signed delegations. Both "adopted after 5.6 years" and "never adopted" are defensible readings of that same sentence — which is what makes it unusable as a measure.

So it's three stages now, each defined by an operation on the data rather than by a judgement:

```
  1  first seen       value present on >=1 zone, any RIR       somebody did it once
  2  partial usage    P(value | signed delegations) >= 1%      in real use, not the norm
                      AND on >= 10 distinct zones
  3  common usage     P(value | signed delegations) >= 10%     a normal choice
                      AND on >= 10 distinct zones
```

and three intervals between them:

```
  onset          publication -> first seen     how long until anyone did it
  establishment  first seen  -> partial        novelty to real use
  ascent         partial     -> common         real use to normal
```

*2. Why those numbers, and not round ones*

This is the part I'd most like you to poke at.

*The thresholds were swept, not picked.* Moving the threshold from 0.5% to 60% changes the number of qualifying algorithms exactly twice:

```
   0.5% - 3%    6 algorithms
   4%  - 25%    4 algorithms      <- cliffs at 4% and 30%
   30% +        3 algorithms
```

1% and 10% each sit in the middle of a plateau, so partial can be anywhere in 0.5–3% and common anywhere in 4–25% without changing a single result. If we'd picked 4% or 30% we'd be sitting on a cliff and the answer would be an artefact of the number we chose rather than a fact about the data.

*The ">= 10 zones" guard* is there because a percentage means different things at different dates. The panel grew *201x* over the series — 32 signed delegations in 2011-05, 6,444 in 2026-08 — so one zone was 3.1% of it then and is 0.016% now. Without the guard, RSASHA256 and RSASHA1-NSEC3 both "reach 1%" in 2011-05 *on a single zone*. A >=25 guard over-corrects and pushes RSASHA1-NSEC3 from 2.0y to 7.8y purely because it had few contemporaries.

*What splitting them actually buys us — the funnel:* 14 changes reach first seen, *9* reach partial, *7* reach common. Five never get past being seen (DSA, ECC-GOST, Ed25519, Ed448, GOST digest); two reach real use and stall there (RSASHA512, ECDSAP384). Under a single "adoption date" all fourteen looked adopted.

```
  interval        n       range        median   spread
  onset         14/14   0.5 - 10.1y     3.3y     9.6y
  establishment  9/14   2.0 -  6.4y     2.2y     4.4y
  ascent         7/14   0.0 -  3.8y     0.0y     3.8y
```

*Almost all the variance is in onset.* Establishment sits at ~2.2y for 7 of the 9 that get there, whatever the mechanism and whatever the decade. What differs between a "fast" RFC and a "slow" one is how long until the first operator moves, not how long the spreading then takes.

*And the finding that justifies the whole split:* onset does not predict spread. *Pearson r = -0.14 over 14 observable changes.* The two most prevalent mechanisms were slower than average to appear, and half the fastest are nowhere:

```
  SHA-256 DS digest   onset 2.9y  ->  P = 98.28%
  ECDSAP256SHA256     onset 3.7y  ->  P = 67.95%
  RSASHA512           onset 0.8y  ->  P =  0.37%
  GOST DS digest      onset 0.8y  ->  P =  0.11%
  ECC-GOST            onset 2.5y  ->  P =  0.00%
```

"First appeared after 0.8 years" and "used by 0.37% of signed delegations" are both true of RSASHA512. One date would report only the flattering one.

*One caveat I want to flag rather than bury:* ascent is degenerate before ~2015 and those 0.0y entries do NOT mean "spread instantly". At the 2011-05 crossing the panel held 32 signed delegations, so 1% and 10% are 0.3 and 3.2 zones — a gap one operator closes in under a month, below our monthly sampling. Only two crossings are genuinely resolvable (ECDSA-P256 0.8y, SHA-384 3.8y). *Please don't let me quote a median ascent.*

*On vocabulary:* "adoption" is fine in "we study DNSSEC RFC adoption"; it's wrong in any sentence with a number in it. Two rules that would have caught every retraction we've had: *no prevalence without its population* (write `P(x | population)`), and *no first occurrence without its n*.

━━━━━━━━━━━━━━━━━━━━━━━━━━━

*3. The interesting part — a script that extracts all of this*

I built `scripts/full_timeline.py` to pull the insights out end to end, in both directions. *I wasn't sure what you'd actually want to see, so both are configurable* — everything lives in `data/analysis_config.json` and nothing is hard-coded. Add a row to measure a new observable, move an RFC between categories to re-cut the taxonomy, change the thresholds. No Python involved.

*Bottom-up* — from the RFC text upward. The unit is the *observable change, not the RFC*: RFC 5702 defines two algorithms that appeared ten months apart, so an RFC-level date would average away a real pattern. For each one: the exact observable (`algorithm = 8`, `DS digest type = 2`, `NSEC3 iterations = 0`, ...), when it first appeared, the three stages, and which implementation-change group it belongs to. The groups came out non-overlapping:

```
  A  New codepoint, primitive already linked in   RFC 5702        0.5y
  B  Same crypto, new signalling                  RFC 5155 alg 7  1.4y
  C  New record type, existing infrastructure     RFC 8078        1.4y
  D  New cryptographic primitive                  5933/6605/8080  2.5 - 3.9y
  E  Deprecation                                  9905/9906       inverted clock
```

What separates them is whether new cryptographic code has to ship *at both ends*, not how hard the maths is — Ed25519 isn't harder to implement than RSA/SHA-512. Group D needs a signer and a validator to agree before anything is publishable. RFC 5702 §8.1 says it outright: _"chosen to match the one used for RSA/SHA-1 signatures. This should ease implementation."_

*Top-down* — six categories by conceptual impact, then mapped down to RFCs: protocol foundation, crypto agility, authenticated denial, key lifecycle, applications (DANE), deprecation. The design decision I'd like your view on: *a category's numbers are exactly its members' numbers*, nothing is measured independently at that level. So "meeting in the middle" is a real check — if a category's story isn't visible in its members' rows, the output says the category has no evidence instead of letting an average paper over it. It also lists which RFCs in a category have no observable at all, i.e. where the taxonomy reaches further than the data.

The crosswalk between the two is the bit I find most useful: the implementation groups cut *across* the conceptual categories. `crypto_agility` mixes Group A (0.5y) and Group D (3.9y), so its category-level onset spread is wide and says almost nothing. The groups predict; the categories communicate. Worth deciding which one we lead with.

*What the script actually does:*

• Reads the OpenINTEL cache off local disk — *no fetching, no listing, nothing that can be throttled*. It takes *multiple roots*, so it reads the main path and the spill path as one corpus. This matters more than it sounds: a source-day can now have files on both, and reading one path at a time would report a *partial* day as a complete one — which is indistinguishable from a month when fewer names were signed, so we'd read it as a measurement. Files are merged by identity across paths, a copy left behind by a partial move is counted once, and anything matching no known layout is *excluded and reported* rather than silently skipped.
• *Fetches the RIPE reverse-DNS archive itself* and ingests it into the same corpus (monthly by default, ~210 tarballs; `--ripe-daily` if we ever want it). Plain HTTPS, no rate limiter, so it shares none of the object store's problems. It's also the only source giving a true *zone-level* denominator, and it starts 2009 — nine years before the OpenINTEL window, which is what makes an uncensored onset possible at all.
• *Cross-references the two* where that's legitimate. Only algorithm- and digest-scoped observables are comparable: the reverse corpus is DS/NS only and the forward corpus is mostly RRSIG/DNSKEY, so differencing a record-type share measures composition, not behaviour. That's exactly how the RFC 4509 "10x gap" turned out to be about 9x denominator. Incomparable dimensions are reported as incomparable instead of being quietly differenced.
• Runs both analyses over all the RFCs we've discussed and writes `summary.md` plus a compact JSON bundle.

*How to run it:*

```bash
python scripts/full_timeline.py \
    --roots /path/to/main/openintel \
    --roots /path/to/spill \
    --ripe-cache /path/to/ripe \
    --out out/full_run --threads 16 --memory-limit 48GB
```

Five stages, each resumable and each skippable with `--stage`: `ripe` (fetch), `index` (walk the paths), `extract` (one pass per source-day), `analyse`, `report`. *Extract checkpoints per source-day and skips what's already done*, so if it dies at hour six it resumes at hour six rather than at the start. Re-analysing is free — it reads the timeline, not the corpus:

```bash
python scripts/full_timeline.py --stage analyse --stage report --out out/full_run
```

`--no-top-down` / `--no-bottom-up` to run one direction, `--config other.json` for a different cut entirely.

*Reading the output* — three states are easy to confuse and the difference matters a lot:

```
  common / partial / seen_only   observed, and how far it got
  scanned_no_match               we looked and it isn't there  -- a real null
  no_corpus_coverage             corpus can't carry that record type -- NOT a result
  residue                        deprecation; the number is what persists
```

Plus `left_censored`, which flags a first sighting in the corpus's opening month, where onset is an upper bound rather than a measurement.

━━━━━━━━━━━━━━━━━━━━━━━━━━━

*4. The ask*

*Can we run this on the server tonight so results are ready for tomorrow?* That's the main thing I need from you.

I genuinely don't know how long a full pass over the whole cache takes — it's one read per source-day with column pruning, so it should be I/O-bound rather than CPU-bound, but I have no measurement at that scale. *If you think a full run won't finish in time, let's run it on a subsample instead* — the script takes `--max-days`, `--start/--end` and `--sources`, and a monthly sample gives the same curves at a fraction of the cost. I'd rather have a defensible subsample by tomorrow than a full run that's still going.

Either way it's resumable, so a subsample tonight and the rest afterwards costs nothing extra — the second run picks up exactly where the first stopped.

What I'd send back: `summary.md` and `analysis_bundle.json`, which have the corpus stats, both directions and the crosswalk.

*Two other things I'd like your opinion on:*

1. *The threshold names.* Does "partial usage / common usage" match how you'd describe those stages? The numbers behind them are robust but the naming is ours.
2. *Which cut leads the writeup* — implementation groups (they predict onset) or conceptual categories (they're easier to explain)?

Docs are in `docs/stages.md`, `docs/bottom_up.md`, `docs/vocabulary.md` and `docs/full_run.md` if you want the long form.
