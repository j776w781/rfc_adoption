# Bottom-up: what each RFC actually changed, and when it first showed up

Built from the RFC text upward. For each measurable RFC: the exact observable
change it introduced, whether our corpora can see it, when it first appeared, and
what kind of implementation work it demands. Grouping comes last — it is a result,
not a starting assumption.

The unit of analysis is the **observable change, not the RFC**. RFC 5702 defines two
algorithms that appeared ten months apart and RFC 6605 two that differ by four
months; an RFC-level date would average away a real and repeated pattern.

## Step 1 — can we see it at all?

Of the 19 RFCs classified measurable, only **11 were actually tested against a
corpus that could contain their evidence**. This has to come first, because a
missing observation and an untestable one look identical in a results table and
mean opposite things.

| State | n | RFCs | What a blank means |
| --- | --- | --- | --- |
| **observed** | 11 | 3110, 4033, 4034, 4509, 5155, 5702, 5933, 6605, 7344, 8078, 8080 | a real date |
| **scanned, no match** | 4 | 9558, 9563, 9905, 9906 | a real null |
| **not yet scanned** | 2 | 5011, 9276 | nothing — forward run predates them |
| **no corpus can evidence it** | 2 | 6698, 7671 | nothing — no TLSA anywhere |

The reverse corpus carries **NS and DS records only**; the forward run covered
**8 RFCs** under the old checklist. So the 22 RFCs added later were tested against
delegation data alone, and any indicator needing DNSKEY, RRSIG, NSEC3PARAM or TLSA
had nothing to match. **RFC 5011 and 9276 are not negative results.** Re-running the
forward scan under checklist 0.2.2 would settle both; nothing else is needed.

## Step 2 — the exact observable change, and first appearance

Dates are the earliest sighting across **both** corpora, since existence is a
minimum over all available evidence. `<=` marks a first sighting in a corpus's
opening month, which is an upper bound, not a measurement.

| RFC | Exact observable change | First seen | Onset |
| --- | --- | --- | --- |
| 3110 | `algorithm = 5` (RSA/SHA-1) | <= 2009-04 | <= 7.9 y |
| 4033 | any DNSSEC RR present | <= 2009-04 | <= 4.1 y |
| 4034 | `dnskey_protocol = 3`; `rrsig_type_covered` present | <= 2009-04 | <= 4.1 y |
| 4509 | `digest_type = 2` on DS (SHA-256) | <= 2009-04 | <= 2.9 y |
| 5155 | NSEC3/NSEC3PARAM present; `algorithm = 7` | 2009-08 | 1.4 y |
| 5702 | `algorithm in (8, 10)` (RSA/SHA-2) | 2010-04 | **0.5 y** |
| 5933 | `algorithm = 12`, `digest_type = 3` (GOST) | 2013-01 | 2.5 y |
| 6605 | `algorithm in (13, 14)` (ECDSA) | 2015-12 | 3.7 y |
| 7344 | CDS / CDNSKEY present | <= 2018-01 | <= 3.3 y |
| 8078 | CDS with `algorithm = 0`, `digest_type = 0` (delete) | 2018-08 | 1.4 y |
| 8080 | `algorithm in (15, 16)` (EdDSA) | **2021-01** | **3.9 y** |
| 9558 | `algorithm = 23`, `digest_type = 5` | not observed | — |
| 9563 | `algorithm = 17`, `digest_type = 6` | not observed | — |
| 9905 | SHA-1 still published (alg 5/7, or digest 1) | see below | — |
| 9906 | `algorithm = 12` still published | none after 2025-11 | — |

**RFC 8080 correction.** Every earlier figure gave EdDSA an onset of 5.6 y from the
reverse corpus alone. The forward corpus has it in `.se` from **2021-01** — 53,365
distinct domains, 6.6M observations, not a stray. The correct onset is **3.9 y**.
This is exactly what going RFC-by-RFC across all evidence is for.

## Step 3 — grouping by the implementation change required

Groups derived from what an implementer must do, then checked against onset:

| Group | What must change | RFCs | Onset |
| --- | --- | --- | --- |
| **A. New codepoint, existing primitive** | a table entry; the crypto is already linked in | 5702 (alg 8/10) | **0.5 y** |
| **B. Same crypto, new signalling** | nothing cryptographic; a number that means "I do X" | 5155 (alg 7) | **1.4 y** |
| **C. New record type, existing infrastructure** | provisioning and RR support | 8078 (CDS delete) | **1.4 y** |
| **D. New cryptographic primitive** | new curve/hash in signer *and* validator | 5933, 6605, 8080 | **2.5 – 3.9 y** |
| **E. Deprecation** | removal, by parties who already deployed | 9905, 9906 | n/a — see below |

The bands do not overlap, and the mechanism is visible in the RFC text. RFC 5702
§8.1 states Group A's intent outright:

> "The signature scheme RSASSA-PKCS1-v1_5 is chosen to match the one used for
> RSA/SHA-1 signatures. This should ease implementation."

**What separates the groups is whether new cryptographic code must ship at both
ends.** Group D requires a signer *and* a validator to agree before anything is
publishable; A, B and C need one party to change a value it already supports. The
2.5–3.9 y floor for Group D is a two-sided coordination cost, not algorithmic
difficulty — Ed25519 is not harder to implement than RSA/SHA-512.

## Step 4 — onset does not predict spread

The obvious hypothesis, that mechanisms appearing quickly go on to be widely used,
is false in this data:

**Pearson r(onset, current prevalence) = −0.14 over 14 observable changes.**

The two most prevalent mechanisms were *slower* than average to appear:

    SHA-256 DS digest   onset 2.9y  ->  P = 98.28%
    ECDSAP256SHA256     onset 3.7y  ->  P = 67.95%

and half the fastest are nowhere:

    RSASHA512           onset 0.8y  ->  P =  0.37%
    GOST DS digest      onset 0.8y  ->  P =  0.11%
    ECC-GOST            onset 2.5y  ->  P =  0.00%

(`P` = `P(value | signed delegations on the strict panel)`, 2026-08.)

**This is the core justification for splitting the definition.** "First appeared
after 0.8 years" and "is used by 0.37% of signed delegations" are both true of
RSASHA512, and a single "adoption date" would report only the flattering one. Onset
measures whether *anyone* could and would; prevalence measures whether the
population followed. They are close to statistically independent, so neither
substitutes for the other. See [stages.md](stages.md) for the three-stage split and
[vocabulary.md](vocabulary.md) for the terms.

## Step 5 — deprecation runs on a different clock

Group E inverts the measurement: the observable is what **persists**, not what
appears, so onset is meaningless and the quantity of interest is residue.

    RFC 9906 (ECC-GOST)   0 records after publication      -- complete
    RFC 9905 (SHA-1)      P(SHA-1 exposure | signed reverse delegations) = 23.51%
                            SHA-1 signature alg (5/7)    7.81%   (514 zones)
                            SHA-1 DS digest (type 1)    21.77%  (1,433 zones)
                            both                                  400 zones

RFC 9906 documented an ending rather than causing one. RFC 9905 has a real job left,
and the two halves need different remedies — replacing the DS at the parent versus
reissuing the child's keys — so they must be reported as two numbers, never one
"SHA-1 exposure".

**A defect this analysis found.** RFC 9905 previously reported **zero** observations
despite 15,966 non-conforming DS records in the corpus. Its DNSKEY/RRSIG indicator
was marked `required`, and a delegation-only corpus contains no such records, so
every match scored 0.0 and vanished. Two fixes in checklist 0.2.2: that indicator is
now alternative evidence rather than a precondition, and a missing `digest_type = 1`
indicator was added, since RFC 9905 closes the SHA-1 *digest* as well as the SHA-1
*signature* and nothing covered it. **The 23.51% above is computed directly from the
corpus; the timeline will not show it until the scan is re-run.**

## Limits

- Six of the eleven observed dates are upper bounds, censored by corpus start.
- Group A, B and C each rest on a **single** RFC. The band separation is clean but
  it is 1 + 1 + 1 + 3 observations, not a distribution.
- r = −0.14 is 14 points; it is enough to refute "onset predicts spread", not enough
  to assert any other relationship.
- Onset measures time to *first publication by anyone*, which one motivated operator
  determines. It says nothing about intent, capability, or validation.
