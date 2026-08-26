# What we measure, and why one number was doing two jobs

> **Terms used here are defined in [`vocabulary.md`](vocabulary.md).** In
> particular "adoption" is retired as a measurement term: what this document calls
> `t_first` is a **first occurrence** (always reported with `n`, the number of
> zones), and every share is a **prevalence** written with its population.

Everything this project has published so far has used one date — the first
observation of a matching record — and called it *adoption*. It is not. This
document separates the measures, rebuilds the RFC classification from both
directions, and reports what the two directions disagree about.

The short version, up front:

> **Almost all the variation in DNSSEC adoption lag is in how long a mechanism
> takes to appear at all. Once it appears, the time to reach 10% of signed
> delegations is nearly constant at about two years.** First appearance ranges
> over 5.3 years; the diffusion phase that follows ranges over 1.2 years for six
> of the seven cases that got there. And **half of what appears never diffuses**
> — 7 of 14 observed changes never reached 10% of the population that could have
> adopted them.

---

## Part 1 — Three measures, not one

### 1.1 The conflation

`first_seen` in the pipeline is the earliest month any record matched an
indicator. One operator publishing one record settles it. That answers a real
question — *did anyone ever do this, and when* — but it is an **existence proof**,
and it has been carrying the word "adoption" in every artefact we have produced.

Ed25519 makes the problem concrete. It first appeared 5.6 years after RFC 8080.
Nine years after publication it is on **0.3%** of signed delegations. "Adopted
after 5.6 years" and "never adopted" are both defensible readings of the same
record, which means the measure is underspecified.

### 1.2 The measures

| Measure | Question | Unit | Denominator | Sensitive to |
| --- | --- | --- | --- | --- |
| **`t_first`** | Did anyone do this, and when? | months from publication | none — a minimum over the corpus | corpus start date (left-censoring) |
| **`t_1%`, `t_10%`, `t_50%`** | How far did it spread? | months from publication | **signed delegations** | denominator choice, composition breaks |
| **`appearance → 10%`** | How long did spreading take, once started? | months | as above | both of the above |

Three consequences follow from taking this seriously.

**Different corpora for different measures.** `t_first` is computed over **all
five RIRs**: a RIR later leaving the archive cannot un-happen an observation made
while it was present, so composition breaks are irrelevant to an existence claim.
Diffusion is computed over the **strict panel (AFRINIC + ARIN)**, the two RIRs
with no step change in their delegation counts, because a share is meaningless if
the denominator moves for reasons unrelated to behaviour.

**The denominator is the population that could have adopted.** For a signing
algorithm that is **signed delegations**, not all delegations. A zone publishing
no DS at all was never a candidate for using algorithm 13, and including it in the
denominator measures DNSSEC deployment rather than algorithm choice. This is a
different denominator from the one in the cross-reference notebook (share of DS
*records*), and it gives different numbers for the same underlying fact — RSA/SHA-1
is 4.9% of DS records but 1.5% of signed delegations, because a delegation
typically publishes several DS records.

**Censoring is a property of the corpus, not the RFC.** A value present on the
corpus's first measured day was already deployed before we could look. Its
`t_first` is an upper bound and is marked `*` throughout. Four of the eighteen
observable changes are in this state.

### 1.3 The unit of analysis is the observable change, not the RFC

RFC 5702 defines **two** algorithms, and they appeared ten months apart
(RSASHA256 at 0.5 y, RSASHA512 at 0.8 y). RFC 6605 defines two that differ by four
months; RFC 8080 two that differ by three. An RFC-level date averages away a
pattern that repeats in every pair: **the larger parameter always trails the
smaller one.** So the row in every table below is an observable change — an
algorithm number, a digest type, a record type — and RFCs are the grouping, not
the unit.

---

## Part 2 — Bottom-up: from the wire back to the document

Each row is a value that appears in published DNS data, the RFC that assigns it,
and what an operator had to do to produce it. Section references marked **(v)**
were read from the RFC text; the rest name the defining document without a section
claim.

### 2.1 Signing algorithms

| Alg | Change | RFC | Where assigned | Published | `t_first` | `t_10%` | Now |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | RSASHA256 | RFC 5702 | §2.1 (v) | 2009-10 | **0.5 y** | 2.7 y | 22.3% |
| 10 | RSASHA512 | RFC 5702 | §2.2 (v) | 2009-10 | **0.8 y** | never | 0.4% |
| 7 | RSASHA1-NSEC3 | RFC 5155 | alg 7 | 2008-03 | **1.4 y** | 3.4 y | 6.5% |
| 12 | ECC-GOST | RFC 5933 | alg 12 | 2010-07 | **2.5 y** | never | 0.0% |
| 13 | ECDSAP256SHA256 | RFC 6605 | §7 IANA (v) | 2012-04 | **3.7 y** | 6.9 y | 68.0% |
| 14 | ECDSAP384SHA384 | RFC 6605 | §7 IANA (v) | 2012-04 | **4.0 y** | never | 2.7% |
| 15 | Ed25519 | RFC 8080 | §5 (v) | 2017-02 | **5.6 y** | never | 0.3% |
| 16 | Ed448 | RFC 8080 | §5 (v) | 2017-02 | **5.8 y** | never | 0.0% |
| 5 | RSASHA1 | RFC 3110 | alg 5 | 2001-05 | ≤7.9 y \* | 10.0 y | 1.5% |
| 3 | DSA/SHA-1 | RFC 2536 | alg 3 | 1999-03 | ≤10.1 y \* | never | 0.0% |
| 17 | SM2SM3 | RFC 9563 | alg 17 | 2024-12 | **never observed** | — | 0.0% |
| 23 | ECC-GOST12 | RFC 9558 | alg 23 | 2024-04 | **never observed** | — | 0.0% |

### 2.2 DS digest types

| Type | Change | RFC | Where assigned | Published | `t_first` | `t_10%` | Now |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | GOST digest | RFC 5933 | digest 3 | 2010-07 | **0.8 y** | never | 0.1% |
| 4 | SHA-384 digest | RFC 6605 | §7 IANA, OPTIONAL (v) | 2012-04 | **1.3 y** | 9.9 y | 8.8% |
| 2 | SHA-256 digest | RFC 4509 | §5 IANA, MANDATORY (v) | 2006-05 | ≤2.9 y \* | 5.0 y | **98.3%** |
| 1 | SHA-1 digest | RFC 3658 | digest 1 | 2003-12 | ≤5.3 y \* | 7.4 y | 22.2% |
| 5 | GOST-2012 digest | RFC 9558 | digest 5 | 2024-04 | **never observed** | — | 0.0% |
| 6 | SM3 digest | RFC 9563 | digest 6 | 2024-12 | **never observed** | — | 0.0% |

\* present on the corpus's first measured day — upper bound, not a measurement.

### 2.3 Grouping by the implementation change required

Sorting the observed `t_first` values produces three bands with **no overlap**,
and the boundary is not what the RFC is *about* but what an operator's existing
toolchain already had.

**Band A — rehash of an existing primitive.** Same key material, same signature
scheme, new hash function. Existing keys stay valid; the signer needs a hash, not
a new cryptographic library.

| Change | `t_first` |
| --- | --- |
| RSASHA256 (alg 8) | 0.5 y |
| RSASHA512 (alg 10) | 0.8 y |
| GOST digest (type 3) | 0.8 y |
| SHA-384 digest (type 4) | 1.3 y |

RFC 5702 states this design intent outright, in §8.1:

> "The signature scheme RSASSA-PKCS1-v1_5 is chosen to match the one used for
> RSA/SHA-1 signatures. This should ease implementation of the new hashing
> algorithms in DNSSEC software."

That is the fastest change in the corpus, and the RFC says why.

**Band B — signalling variant, no new cryptography.** Algorithm 7 is RSASHA1 with
a different algorithm number, used to signal NSEC3 capability. The crypto is
unchanged; what changes is what the number tells a resolver.

| Change | `t_first` |
| --- | --- |
| RSASHA1-NSEC3 (alg 7) | 1.4 y |

**Band C — new cryptographic primitive.** A new curve or key type. Requires
library support, new key generation, and a parent willing to accept a DS with the
new algorithm number.

| Change | `t_first` |
| --- | --- |
| ECC-GOST (alg 12) | 2.5 y |
| ECDSAP256 (alg 13) | 3.7 y |
| ECDSAP384 (alg 14) | 4.0 y |
| Ed25519 (alg 15) | 5.6 y |
| Ed448 (alg 16) | 5.8 y |

RFC 6605's motivation is efficiency, not ease — it argues from size and speed:

> "ECDSA keys are much shorter than RSA keys; at this size, the difference is 256
> versus 3072 bits... Signing with ECDSA is significantly faster than with RSA
> (over 20 times in some implementations)."

RFC 8080 offers no transition guidance at all; its §8 discusses when to prefer
Ed448 over Ed25519, not how to get there from what you have. It is also the
slowest change in the corpus.

**Band A: 0.5–1.3 y. Band B: 1.4 y. Band C: 2.5–5.8 y.** The bands do not overlap.

### 2.4 The measures separate cleanly

| | Range | Spread | Median |
| --- | --- | --- | --- |
| **First appearance** (uncensored, n=10) | 0.5 – 5.8 y | **5.3 y** | 2.0 y |
| **Appearance → 10%** (n=7) | 2.0 – 8.6 y | 6.6 y | 2.1 y |
| **Appearance → 10%**, excluding one outlier (n=6) | 2.0 – 3.2 y | **1.2 y** | 2.1 y |

Once a mechanism exists in the wild, reaching 10% of signed delegations takes
about two years, and it takes about two years almost regardless of which mechanism
it is. The one exception is the SHA-384 DS digest at 8.6 years — consistent with
its `OPTIONAL` status in RFC 6605 §7, against SHA-256's `MANDATORY` in RFC 4509 §5.

**And appearance does not imply diffusion.** Of 14 observed changes, **7 never
reached 10%**: DSA/SHA-1, RSASHA512, ECC-GOST, ECDSAP384, Ed25519, Ed448, and the
GOST digest. Reporting `t_first` as "adoption" would count every one of those as a
success.

---

## Part 3 — Top-down: from conceptual impact to the wire

Built independently of Part 2, by asking what kind of change each document makes
to the system, then mapping down to the RFCs we screen.

**T1 — Protocol-layer additions.** New record types or new wire formats. Every
participant must learn a new object.
*RFC 4034 (DNSKEY/RRSIG/NSEC/DS formats), RFC 5155 (NSEC3, NSEC3PARAM),
RFC 7344 (CDS, CDNSKEY), RFC 6698 (TLSA).*

**T2 — Cryptographic agility.** New algorithm or digest values inside existing
record formats. No new record type; a new value in an existing field.
*RFC 3110, RFC 5702, RFC 5933, RFC 6605, RFC 8080, RFC 9558, RFC 9563, RFC 4509.*

**T3 — Operational and parameter guidance.** No new syntax; guidance on how to set
what already exists.
*RFC 9276 (NSEC3 iterations and salt), RFC 6781 (operational practices),
RFC 7583 (rollover timing).*

**T4 — Trust-maintenance automation.** Changes who does what, and when, across the
parent/child boundary.
*RFC 7344, RFC 8078, RFC 9615, RFC 5011.*

**T5 — Resolver-side behaviour.** Properties of a query/response exchange or of
cache handling.
*RFC 4035, RFC 8198, RFC 9077.*

**T6 — Retirement.** Withdraws something previously allowed.
*RFC 9905 (SHA-1 signing), RFC 9906 (ECC-GOST), RFC 8624 → RFC 9904.*

**T7 — Roadmap and clarification.** Defines no mechanism of its own.
*RFC 6840, RFC 9364.*

### What the top-down view predicts about measurability

It predicts our own classification well. T5 and T7 are unmeasurable from
authoritative data by construction — which is exactly what the schema checker
concludes independently, and why 7 of 30 RFCs land on *not measurable here*. T4 is
measurable only where it leaves a record (CDS/CDNSKEY yes, the RFC 5011 acceptance
timer no). That the two agree is a useful consistency check on both.

---

## Part 4 — Where the two views meet, and where they don't

### 4.1 The disagreement

The top-down category **T2, cryptographic agility, contains both the fastest and
the slowest changes in the entire corpus** — RSASHA256 at 0.5 years and Ed448 at
5.8 years, an eleven-fold difference inside one conceptual bucket. RFC 4509's
SHA-256 DS digest and RFC 6605's SHA-384 DS digest are both "a new digest type in
an existing field", and they reach 10% 5.0 and 9.9 years after publication
respectively.

So the conceptual category has **no predictive power over timing**. Knowing an RFC
is about cryptographic agility tells you nothing about how long it will take.

### 4.2 What does predict it

The bottom-up axis does: **does the change reuse the operator's existing
cryptographic primitive and key material, or require a new one?** That single
question separates 0.5–1.4 years from 2.5–5.8 years with no overlap, across four
RFCs and ten observable changes.

### 4.3 The synthesis

The two views are **orthogonal, and both are needed**:

- The **top-down category** predicts *whether we can measure it at all*. T5 and T7
  are unmeasurable by construction; T1, T2 and T4 leave records.
- The **bottom-up continuity axis** predicts *how long it will take* once it is
  measurable.

Neither substitutes for the other. A classification using only conceptual
categories would have told us Ed25519 and RSASHA256 are the same kind of thing.

### 4.4 A reinterpretation this forces

"Each new signing algorithm took longer than the one before" — the finding in the
current deck — survives, but the explanation changes. It is not evidence that the
ecosystem has slowed. It is that **the cheap changes were available early and were
taken early**: rehashes of RSA in 2009–2012, new curves from 2012 onward. The
trend is compositional. There were no Band-A changes left to make.

That distinction matters for anything forward-looking. A post-quantum algorithm
would be Band C, and Band C has never gone faster than 2.5 years to first
appearance or reached 10% in under 6.9 years.

---

## Part 5 — What this changes in the pipeline

1. **`first_seen` is renamed in meaning, not just in prose.** It is an existence
   proof. Any artefact using it must say so, and must not call it adoption.
2. **Diffusion needs a stated denominator.** "Share of signed delegations" for
   algorithm choice; "share of delegations" for DNSSEC deployment. These are
   different questions and give different numbers for the same fact.
3. **The observable change is the unit.** RFC-level dates hide within-RFC
   structure that turned out to carry the finding.
4. **Left-censoring is marked, not silently averaged.** Four of eighteen changes
   are bounds rather than measurements.

### Known limits of this analysis

- **It rests on the reverse corpus.** The forward corpus was scanned under
  checklist 0.1.0 and has no data for the 22 RFCs added since, so every date here
  comes from reverse delegations. Forward-DNS confirmation needs a rescan of
  2.07 TB.
- **DS records only.** The reverse corpus carries `DS` and `NS` and nothing else,
  so record-type changes (NSEC3, CDS/CDNSKEY, TLSA) have no first-appearance date
  here. Bands A–C are built on algorithm and digest changes alone.
- **Algorithms 17 and 23 are true negatives, not gaps.** Both are DS algorithm
  values, the corpus carries DS algorithms throughout, and neither ever appears.
  RFC 9563 and RFC 9558 have no deployment in reverse DNS at all.
- **Diffusion sits on two RIRs.** The strict panel is 78% of signed delegations
  but is dominated by ARIN, so "10% of signed delegations" is substantially a
  statement about North American address space.

Reproduce with `python reporting/adoption_measures.py`; figures land in
`out/analysis/adoption_measures.json`.
