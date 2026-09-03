# Full-run results, and what they changed

The run covered **8.24 TB / 15,179 source-days / 12 sources** — the five RIRs plus
seven forward TLDs (`ch`, `ee`, `fed.us`, `gov`, `li`, `nu`, `se`). Zero files
matched no layout, zero duplicates, zero days split across roots.

**Observables measured went from 14 to 24.** Ten became measurable for the first
time, because the forward corpus carries record types the reverse one cannot:
NSEC3 parameters, DNSKEY flags, CDS. That was the point of the exercise and it
worked.

## The retraction

> *"Onset lag increases monotonically with publication date across the four
> signing-algorithm families."* — [vocabulary.md](vocabulary.md), now withdrawn.

| Algorithm | Published | Reverse only | Full corpus |
| --- | --- | --- | --- |
| ECC-GOST | 2010-07 | — | 2.4 y |
| ECDSA P-256 | 2012-04 | 3.7 y | 3.6 y |
| ECDSA P-384 | 2012-04 | 4.0 y | 3.9 y |
| **Ed25519** | 2017-02 | **5.6 y** | **1.9 y** |
| Ed448 | 2017-02 | 5.8 y | 3.2 y |

Reverse only: `3.7 → 4.0 → 5.6 → 5.8`, monotonic. Full corpus:
`2.4 → 3.6 → 3.9 → 1.9 → 3.2`, **not monotonic**. The newest primitive is now the
fastest one.

The pattern was an artefact of a single corpus. Reverse-DNS operators adopt late
as a group, so every newer algorithm looked slower in reverse data — not because
the ecosystem slowed, but because `.se` had EdDSA in 2019-01 while the RIRs did
not show it until 2022-08. This is the third value this figure has taken (5.6 →
3.9 → 1.9) and each move came from searching a corpus we already had.

**14 first-seen dates moved earlier.** The largest revisions:

    SHA-384 DS digest   5.3y -> 1.2y   (-4.1y)
    Ed25519             5.6y -> 1.9y   (-3.7y)
    Ed448               5.8y -> 3.2y   (-2.6y)
    RSASHA1, SHA-1 and SHA-256 digests  -2.2y each (all left-censored anyway)

## What survived, and is now stronger

The implementation-cost ordering. Censored and negative onsets excluded:

| What the change requires | Onset | n |
| --- | --- | --- |
| New codepoint, primitive already linked in | **0.4 – 0.8 y** | 2 |
| New DS digest type — a hash, parent side only | **0.8 – 1.2 y** | 2 |
| Same cryptography, new signalling | **1.3 y** | 1 |
| New record type on existing infrastructure | **1.4 y** | 1 |
| New cryptographic primitive — signer *and* validator | **1.9 – 3.9 y** | 5 |

**Five groups, strictly ascending, on more data than before.** But be honest about
the separation: the middle gaps are 0.1 y, which with n=1 is not a real boundary.
Only the last gap is substantial — **1.4 y to 1.9 y**, before a new primitive.

Compared with the reverse-only run the new-primitive band moved *down* (2.5–5.8 →
1.9–3.9) and the gap *narrowed* (1.4→2.5 became 1.4→1.9). The claim to make is
about the **ordering**, which holds across five groups; not about sharp bands,
which the data no longer supports.

## Three defects the run exposed

**1. Two different "now" dates in one column.** Forward sources end 2023-12; the
RIRs run to 2026-08. So `NSEC3 zero iterations 9.61%` is a 2023 figure and
`ECDSA P-256 71.07%` is a 2026 one, printed in the same column as though both
were current.

**2. Every cross-corpus comparison returned nothing.** The comparison was taken
at the timeline's last month (2026-08), where the forward corpus has no data, so
all 20 forward values came back empty — and the summary reported that as
*"0 of 20 observables agree within 5 percentage points"*, which reads as the two
corpora contradicting each other. They were never compared. Fixed: the comparison
now happens at the last month **both** sides cover, and unanswerable rows are
counted separately from disagreeing ones.

**3. A composition break at 2024-01.** All seven forward sources stop then, so any
pooled share spanning that month compares two different populations — the same
error as the RIPE format change, at corpus scale. `algorithm_ds` and
`digest_type_ds` figures for 2026 are **reverse-only however they are labelled**.
`detect_breaks()` now reports sources that stop early and denominator steps over
25%.

Also fixed: a **negative onset**. `NSEC3 zero iterations` read **−6.2 y** because
zero iterations was always legal and already common when RFC 9276 recommended it
in 2022; the GOST-2012 digest read −0.4 y because an implementation shipped from
the draft. A negative onset is not a fast adoption, it is the wrong question, and
those now report no onset with a `predates_rfc` flag instead.

## Two figures not to quote

- **`DNSKEY protocol = 3` at 100%** is a tautology. RFC 4034 §2.1.2 *fixes* the
  octet at 3, so every DNSKEY has it by definition. It measures the spec, not
  behaviour.
- **`NSEC3 empty salt` at 0%** is not a finding either. NULL is recorded as
  *unknown* rather than *empty* precisely so a missing column cannot be credited
  as following RFC 9276 — so the salt half of that BCP is still unmeasured, while
  the iterations half reads 9.61%.

## What is still needed

The timeline itself (`timeline_monthly.parquet`) was not in the bundle, so the
charts still show reverse-corpus data and the forward/reverse split cannot be
computed here. With it, three things follow immediately: separate forward and
reverse series rather than pooled ones, a cross-corpus comparison at 2023-12
where both sides exist, and charts on the full corpus.

The analysis stage is cheap and needs no rescan:

```bash
python scripts/full_timeline.py --stage analyse --stage report --out out/full_run
```
