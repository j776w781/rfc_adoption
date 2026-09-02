# Measurement vocabulary

"Adoption" is retired as a measurement term in this project. It survives only as a
narrative word, and only where it names which measure backs it.

## Why the word fails

"RFC 8080 was adopted after 5.6 years" bundles five separate claims, of which we
observe one:

| The claim | Do we observe it? |
| --- | --- |
| A record carrying algorithm 15 existed in published data | **yes** — directly |
| Some population uses it to a meaningful degree | no — that is a different measure |
| It is spreading rather than static or declining | no — a different measure again |
| Operators did it *because of* RFC 8080 | **no** — not observable from any zone file |
| This constitutes success | not a measurement at all |

The first occurrence of Ed25519 was **one zone**. Nine years after publication it
is on 0.3% of signed delegations. Both "adopted after 5.6 years" and "never
adopted" are defensible readings of that sentence, which is what makes it unusable.

## The replacement

Each term is named after the operation that computes it. If the name describes the
arithmetic, no inference can hide inside it.

### Layer 1 — what is literally in the data

**Occurrence.** A value present in published records. Countable, dated, and the
only thing we observe directly.

**First occurrence** — `t_occ`, written **always with `n`**, the number of distinct
zones carrying it that month.

> ECDSAP256: first occurrence 2015-12, n=2 zones.

The `n` is not decoration. For four of the ten observed algorithms — RSASHA256,
RSASHA512, Ed25519, Ed448 — the first occurrence is a **single zone**. A date
resting on one operator must never be reported bare.

**Persistence.** Whether the value is still present in later measured months. All
ten observed algorithms persist, so this distinguishes nothing in the current data
— reported because it was checked, not because it separated anything.

### Layer 2 — extent

**Prevalence** — `P(value | population)`. A fraction, with the population named in
the expression. The conditioning bar is mandatory notation, not decoration:

> `P(alg 13 | signed delegations) = 68.0%`  (4,379 / 6,444)
> `P(alg 13 | DS records) = 63.9%`  (8,569 / 13,410)
> `P(alg 13 | all reverse delegations) = 0.60%`  (4,502 / 751,188)

Three different true numbers for the same fact, on the same day (2026-08-01),
from the same corpus, differing by a factor of 113. Writing "ECDSA is at 68%"
is the error that produced both the RFC 4509 "10× disagreement" and the
retracted "crossed 1%" headline. **No prevalence figure may be written without its
population.**

### Layer 3 — movement

**Onset lag** — publication → first occurrence. How long until anyone did it.

**Rise time** — first occurrence → a stated prevalence threshold. How long the
spreading took, once started. Undefined where the threshold is never reached, and
that is the common case: 7 of 14 observed changes never reach
`P(· | signed delegations) = 10%`.

**Ceiling** — maximum prevalence reached, with its population.

**Residue** — prevalence remaining after a value is deprecated or superseded.
`P(SHA-1 signing | DS records) = 4.9%` is a residue, not an adoption.

### Layer 4 — what we do not measure

These are the three metrics Osterweil et al. define for DNSSEC deployment
(IMC 2008), and naming them their way is better than inventing our own words for
the same boundary. All three require *active resolution*; we read published zone
data, so we measure none of them. See [prior_work.md](prior_work.md).

**Availability** — can a resolver actually receive the data at all (middleboxes,
MTU, truncation). **Verifiability** — does cryptographic verification succeed.
**Validity** — does the data match what the zone administrator intended.

The rest of this layer is ours:

**Attribution.** Whether an RFC *caused* a change. Nothing in a zone file carries
intent. An operator who enabled ECDSA because their DNS provider changed a default
is indistinguishable from one who read RFC 6605.

**Capability.** We see what a zone *publishes*, never what its software *supports*.
Absence of occurrence is not absence of capability.

**Validation.** We see what is published, not whether any resolver accepts it.

These are not gaps to be filled later with the same data. They are outside what
authoritative measurement can reach, and any sentence asserting one is wrong
regardless of how much data is behind it.

## Two rules

1. **No prevalence without its population.** Write `P(x | population)`.
2. **No first occurrence without its `n`.** Write `t_occ = 2022-12, n=1`.

## What the rules would have caught

Every error this project has had to retract violates one of them:

| Retracted claim | Rule broken |
| --- | --- |
| "0.022% → 1.012%, crossed 1% this year" | 1 — population changed under the series |
| "RFC 4509: ~5% forward vs ~79% reverse, a 10× gap" | 1 — two different populations |
| "EdDSA adopted after 5.6 years" | 2 — n=1, and occurrence read as prevalence |
| "Rollovers peak when adoption is steepest" | Layer 4 — attribution asserted, r = 0.43 |
| "RFC 6840 first seen 2013-02, 1.8M observations" | Layer 1 — occurrence of the wrong thing |

## Worked rewrites

**Before:** "ECDSA adoption reached 64% in 2026."
**After:** "`P(alg 13 | DS records)` = 63.9% on 2026-08-01."

**Before:** "EdDSA was adopted 5.6 years after publication."
**After:** "Ed25519 first occurrence **2021-01** in the forward corpus, onset lag
**3.9 y**. (Reverse corpus alone gives 2022-09, n=1 zone, 5.6 y — an upper bound,
not the measurement.) `P(alg 15 | signed delegations)` = 0.3% at 2026-08; the 10%
threshold is never reached, so rise time is undefined."

That parenthesis is a **third rule**, learned the hard way — see
[bottom_up.md](bottom_up.md) step 2:

3. **No first occurrence without naming the corpora searched.** Existence is a
   minimum over all available evidence, so a date from one corpus is an upper bound
   until the others are checked. Quoting 5.6 y while holding forward data that says
   3.9 y is the same error as quoting a prevalence without its population.

**Before:** "Each new algorithm took longer to be adopted."
**After:** "Onset lag increases monotonically with publication date across the four
signing-algorithm families. Rise time does not vary with it — the variation is in
onset, not in spread."

**Before:** "15.3% of DS records still use SHA-1, a compliance problem."
**After:** "`P(digest 1 | DS records)` = 15.3%, a residue. RFC 9905 closes it to
new deployment; RFC 4509 §4 previously *recommended* publishing SHA-1 and SHA-256
DS records together, so this residue is partly prior best practice, not only
inertia."

## A note on the word that remains

"Adoption" is still the right word in a sentence like *"we are studying DNSSEC RFC
adoption"* — it names the subject. It is wrong in any sentence with a number in it.
Where a number appears, name the measure.
