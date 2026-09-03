# Full-run timeline

## Corpus

- roots: /mnt/nas_share/Josh, out/reverse/corpus
- sources: afrinic, apnic, arin, ch, ee, fed.us, gov, lacnic, li, nu, ripe, se
- source-days: 15,179  |  files: 25,151  |  7.5 TB
- days split across roots (merged): 0
- files matching no layout (EXCLUDED): 0
- duplicate files across roots (counted once): 0

| Source | Days | Files | Span | Split |
|---|---|---|---|---|
| afrinic | 200 | 200 | 2009-04-01 .. 2026-09-01 | 0 |
| apnic | 179 | 179 | 2009-04-01 .. 2024-12-01 | 0 |
| arin | 200 | 200 | 2009-04-01 .. 2026-09-01 | 0 |
| ch | 1,321 | 2,755 | 2020-05-19 .. 2023-12-31 | 0 |
| ee | 1,615 | 1,646 | 2019-07-29 .. 2023-12-31 | 0 |
| fed.us | 1,989 | 1,989 | 2017-05-01 .. 2022-10-28 | 0 |
| gov | 2,432 | 2,432 | 2017-05-01 .. 2023-12-31 | 0 |
| lacnic | 200 | 200 | 2009-04-01 .. 2026-09-01 | 0 |
| li | 1,321 | 1,358 | 2020-05-19 .. 2023-12-31 | 0 |
| nu | 2,761 | 2,853 | 2016-06-07 .. 2023-12-31 | 0 |
| ripe | 200 | 200 | 2009-04-01 .. 2026-09-01 | 0 |
| se | 2,761 | 11,139 | 2016-06-07 .. 2023-12-31 | 0 |

## Bottom-up: observable changes

Stage thresholds: partial >= 1.0%, common >= 10.0%, both requiring >= 10 distinct names.

30 changes configured, **24 observed**, 18 reached partial usage, 12 reached common usage.

| Change | RFC | Published | First seen | Partial | Common | Onset | Now | State |
|---|---|---|---|---|---|---|---|---|
| DSA/SHA-1 | RFC 2536 | 1999-03 | 2009-03 | — | — | <= 10.0y | 0.00% | seen_only |
| RSASHA1 | RFC 3110 | 2001-05 | 2009-03 | 2009-03 | 2009-03 | <= 7.8y | 1.27% | common |
| SHA-1 DS digest | RFC 3658 | 2003-12 | 2009-03 | 2009-03 | 2009-03 | <= 5.2y | 18.26% | common |
| DNSKEY SEP/KSK | RFC 4034 | 2005-03 | 2016-06 | 2016-06 | 2016-06 | <= 11.2y | 99.94% | common |
| DNSKEY protocol = 3 | RFC 4034 | 2005-03 | 2016-06 | 2016-06 | 2016-06 | <= 11.2y | 100.00% | common |
| SHA-256 DS digest | RFC 4509 | 2006-05 | 2009-03 | 2009-03 | 2009-07 | <= 2.8y | 98.19% | common |
| DNSKEY REVOKE bit | RFC 5011 | 2007-09 | 2016-06 | — | — | <= 8.8y | 0.00% | seen_only |
| NSEC3 opt-out in use | RFC 5155 | 2008-03 | 2016-06 | 2016-06 | 2016-06 | <= 8.2y | 14.34% | common |
| RSASHA1-NSEC3 | RFC 5155 | 2008-03 | 2009-07 | 2009-07 | 2009-07 | 1.3y | 6.02% | common |
| RSASHA256 | RFC 5702 | 2009-10 | 2010-03 | 2011-04 | 2011-10 | 0.4y | 20.37% | common |
| RSASHA512 | RFC 5702 | 2009-10 | 2010-07 | 2012-12 | — | 0.8y | 0.30% | partial |
| ECC-GOST | RFC 5933 | 2010-07 | 2012-12 | — | — | 2.4y | 0.00% | seen_only |
| GOST DS digest | RFC 5933 | 2010-07 | 2011-04 | 2013-06 | — | 0.8y | 0.10% | partial |
| ECDSAP256SHA256 | RFC 6605 | 2012-04 | 2015-11 | 2016-10 | 2019-02 | 3.6y | 71.07% | common |
| ECDSAP384SHA384 | RFC 6605 | 2012-04 | 2016-03 | 2024-01 | — | 3.9y | 2.44% | partial |
| SHA-384 DS digest | RFC 6605 | 2012-04 | 2013-07 | 2013-07 | 2021-08 | 1.2y | 8.03% | common |
| DANE-EE (TLSA usage 3) | RFC 7671 | 2015-10 | — | — | — | — | — | no_corpus_coverage |
| DANE-TA (TLSA usage 2) | RFC 7671 | 2015-10 | — | — | — | — | — | no_corpus_coverage |
| Ed25519 | RFC 8080 | 2017-02 | 2019-01 | 2020-04 | — | 1.9y | 0.37% | partial |
| Ed448 | RFC 8080 | 2017-02 | 2020-05 | — | — | 3.2y | 0.03% | seen_only |
| CDS delete sentinel | RFC 8078 | 2017-03 | 2018-08 | 2018-09 | — | 1.4y | 0.50% | partial |
| NSEC3 empty salt | RFC 9276 | 2022-08 | — | — | — | — | 0.00% | scanned_no_match |
| NSEC3 zero iterations | RFC 9276 | 2022-08 | 2016-06 | 2022-02 | — | <= -6.2y | 9.61% | partial |
| ECC-GOST12 | RFC 9558 | 2024-04 | — | — | — | — | 0.00% | scanned_no_match |
| GOST-2012 digest | RFC 9558 | 2024-04 | 2023-11 | — | — | -0.4y | 0.00% | seen_only |
| SM2SM3 | RFC 9563 | 2024-12 | — | — | — | — | 0.00% | scanned_no_match |
| SM3 DS digest | RFC 9563 | 2024-12 | — | — | — | — | 0.00% | scanned_no_match |
| ECC-GOST still published | RFC 9906 | 2025-11 | 2012-12 | — | — | — | 0.00% | residue |
| SHA-1 DS digest still published | RFC 9905 | 2025-11 | 2009-03 | 2009-03 | 2009-03 | — | 18.26% | residue |
| SHA-1 signing still published | RFC 9905 | 2025-11 | 2009-03 | 2009-03 | 2009-03 | — | 7.30% | residue |

**Not testable in this corpus** (no denominator for the dimension, so a blank here is not a negative result -- distinct from a change that was scanned and genuinely never occurred, which shows as `scanned_no_match`): DANE-EE (TLSA usage 3), DANE-TA (TLSA usage 2)


## Top-down: conceptual categories

| Category | RFCs | Observables | Observed | Onset median | Reached common |
|---|---|---|---|---|---|
| Base protocol: the four record types | 5 | 2 | 2 | 11.25y | 2 |
| Which cryptography a zone signs with | 9 | 16 | 13 | 2.42y | 6 |
| Proving a name does not exist | 4 | 4 | 3 | 1.33y | 2 |
| Key rollover and parent-child coordination | 6 | 2 | 2 | 5.08y | 0 |
| Things built on top of DNSSEC (DANE) | 3 | 2 | 0 | — | 0 |
| Retiring cryptography that is no longer safe | 4 | 3 | 3 | — | 2 |

RFCs in a category with no observable change configured (the taxonomy reaches further than the data):

- **Base protocol: the four record types**: RFC 4033, RFC 4035, RFC 6840, RFC 9364
- **Proving a name does not exist**: RFC 8198, RFC 9077
- **Key rollover and parent-child coordination**: RFC 6781, RFC 7344, RFC 7583, RFC 9615
- **Things built on top of DNSSEC (DANE)**: RFC 6698, RFC 7672
- **Retiring cryptography that is no longer safe**: RFC 8624, RFC 9904

## Where the two directions meet

| Implementation group | Changes | Observed | Onset range |
|---|---|---|---|
| New codepoint over an existing primitive | 3 | 3 | 0.4–7.8y |
| Same cryptography, new signalling | 3 | 3 | 1.3–11.2y |
| New record type on existing infrastructure | 2 | 2 | 1.4–11.2y |
| New cryptographic primitive | 8 | 6 | 1.9–10.0y |
| Parameter choice within an existing mechanism | 5 | 2 | -6.2–8.2y |
| Deprecation | 3 | 3 | — |
| New DS digest type | 6 | 5 | -0.4–5.2y |

Onset bands come from the implementation groups, not the conceptual categories: a category mixes changes of very different implementation cost, so its onset spread is wide and says little. The groups are the predictive cut; the categories are the communicable one.


## Cross-reference: forward vs reverse

forward: ch, ee, fed.us, gov, li, nu, se  |  reverse: afrinic, apnic, arin, lacnic, ripe

| Observable | Fwd first | Rev first | Earliest | Fwd now | Rev now | Δ |
|---|---|---|---|---|---|---|
| DSA/SHA-1 | 2016-06 | 2009-03 | 2009-03 | — | 0.0% | — |
| RSASHA1 | 2016-06 | 2009-03 | 2009-03 | — | 1.3% | — |
| RSASHA1-NSEC3 | 2016-06 | 2009-07 | 2009-07 | — | 6.0% | — |
| RSASHA256 | 2016-06 | 2010-03 | 2010-03 | — | 20.4% | — |
| RSASHA512 | 2016-06 | 2010-07 | 2010-07 | — | 0.3% | — |
| ECC-GOST | 2019-05 | 2012-12 | 2012-12 | — | 0.0% | — |
| ECDSAP256SHA256 | 2016-06 | 2015-11 | 2015-11 | — | 71.1% | — |
| ECDSAP384SHA384 | 2017-01 | 2016-03 | 2016-03 | — | 2.4% | — |
| Ed25519 | 2019-01 | 2022-08 | 2019-01 | — | 0.4% | — |
| Ed448 | 2020-05 | 2022-11 | 2020-05 | — | 0.0% | — |
| SM2SM3 | — | — | — | — | 0.0% | — |
| ECC-GOST12 | — | — | — | — | 0.0% | — |
| SHA-1 DS digest | 2016-06 | 2009-03 | 2009-03 | — | 18.3% | — |
| SHA-256 DS digest | 2016-06 | 2009-03 | 2009-03 | — | 98.2% | — |
| GOST DS digest | 2016-06 | 2011-04 | 2011-04 | — | 0.1% | — |
| SHA-384 DS digest | 2016-06 | 2013-07 | 2013-07 | — | 8.0% | — |
| GOST-2012 digest | 2023-11 | — | 2023-11 | — | 0.0% | — |
| SM3 DS digest | — | — | — | — | 0.0% | — |
| SHA-1 DS digest still published | 2016-06 | 2009-03 | 2009-03 | — | 18.3% | — |
| ECC-GOST still published | 2019-05 | 2012-12 | 2012-12 | — | 0.0% | — |

- 0 of 20 comparable observables agree within 5 percentage points across two corpora that share no infrastructure, operator population or collection method.
- 3 observable(s) appear EARLIER in the forward corpus than the reverse one: Ed25519, Ed448, GOST-2012 digest. A reverse-only onset overstates these.

---

Generated by `scripts/full_timeline.py`. The tidy timeline behind every number is `timeline_monthly.csv`; each row carries its own denominator as a `_total` row of the same dimension, so any share can be recomputed against the population it actually belongs to.
