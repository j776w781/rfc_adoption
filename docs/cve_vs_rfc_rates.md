# Adoption rate at CVE patches vs at RFC publications

`scripts/cve_vs_rfc_rates.py` -> `out/analysis/cve_vs_rfc_rates.json`,
`out/analysis/dns_cve_vs_rfc_rates.csv`;
`reporting/cve_vs_rfc_rates.py` -> `reporting/charts/cve_vs_rfc_rates.png`.

## Question

Take every month in which a DNSSEC CVE was patched, and every month in which
a DNSSEC RFC was published. What did the adoption rate look like in those
months, and do the two distributions differ from each other or from an
ordinary month?

## Method

* **Events.** CVE patches: the 40 DNSSEC-mechanism CVEs (scope `dnssec` in
  `cve_crossref.json`) with a dated fix, at the month of the first fixing
  release (or commit when no release is dated). Fourteen of them were fixed in
  2026-07 and several share other months; a month is one observation of the
  series, so distributions are over unique event months (22 for CVEs, and the
  30 screened DNSSEC RFCs, those inside each series' span).
* **Rate.** Reverse: the strict AFRINIC+ARIN panel's signed share (DS present
  over all delegations), month-on-month change in percentage points. Forward:
  per TLD, zones with a DNSKEY over delegated zones (NS owners), month-on-month
  change, averaged over the TLDs present in both months weighted by zone count
  so that a TLD entering the corpus is not a jump.
* **Statistic.** Mean rate over the event month and the three months after it.
  The same statistic at every month is the baseline.
* **Comparison.** Medians, with permutation p-values: CVE vs RFC by shuffling
  labels; each against the baseline by drawing same-size random month sets
  stratified by year, because the CVE fixes cluster in 2022-2026 and an
  unstratified draw compares eras, not events. Everything is repeated on the
  detrended rate (minus a 25-month centred rolling median).
* **Control.** The same test with all 200 fixed DNS CVEs (not DNSSEC-specific).

## Result

| series | measure | CVE months (n) | RFC months (n) | all months | p CVE~RFC | p CVE~all, year-matched | p RFC~all, year-matched |
|---|---|---|---|---|---|---|---|
| reverse signed share | raw, pp/mo | +0.004 (21) | +0.004 (16) | +0.004 | 0.93 | 0.94 | 0.78 |
| reverse signed share | detrended | +0.001 (21) | +0.000 (16) | +0.001 | 0.75 | 0.50 | 0.29 |
| forward signed share | raw, pp/mo | +0.07 (9) | +0.09 (7) | +0.15 | 1.00 | 0.32 | 0.38 |
| forward signed share | detrended | +0.11 (9) | -0.04 (7) | +0.04 | 0.34 | 0.47 | 0.49 |

The three distributions lie on top of each other in both corpora. Months in
which a DNSSEC CVE was patched, months in which a DNSSEC RFC was published,
and ordinary months show the same adoption rate.

Two things looked like a signal on the way and were not. Counting each CVE
as its own observation gave the CVE set a higher median in reverse DNS
(p 0.0004 against the baseline); that was fourteen CVEs sharing one month in
2026-07, and it disappears when a month is counted once. Before year
matching, the CVE months also looked faster because they sit in the years
when the reverse signed share was growing fastest; the control set of all
DNS CVEs, which have nothing to do with DNSSEC, showed the same, and both go
away with year-matched draws.

Per mechanism (NSEC3 with RFC 5155/9276 and the nsec3 CVEs; ECDSA/EdDSA with
RFC 6605/8080 and the algorithm CVEs) the event counts are one to four per
cell and no comparison is possible; the values are in the JSON.

## Limits

The forward series covers 2016-06 to 2023-12, so it sees 9 CVE fix months and
7 RFC publications. Reverse rates are tiny in absolute terms (the signed share
is about 1%), so the comparison is of ranks, not magnitudes. The 4-month
window is a choice; the conclusion did not change at the event month alone.

## On each event's own mechanism

`reporting/cve_vs_rfc_mechanism.py` -> `reporting/charts/cve_vs_rfc_mechanism.png`,
`out/analysis/dns_cve_vs_rfc_mechanism_events.csv`.

The overall signed share is the wrong ruler for a single RFC or CVE, since
neither touches it directly. Measured on the mechanism each event concerns
(ECDSA/EdDSA share for RFC 6605/8080 and the algorithm CVEs; NSEC3 share for
RFC 9276 and the nsec3 CVEs), as the percentile of the four-month window
among all months of that curve:

* RFC publications sit in ordinary or dead months: RFC 6605 at the 3rd
  percentile of the reverse ECDSA curve (nothing moved for 3.6 years), RFC
  8080 at the 32nd (reverse) and 79th (forward), RFC 9276 at the 10th to
  19th (the NSEC3 share was already falling after the 2021 collapse).
* Two CVE patch months are extreme. CVE-2021-40083 (2021-10) is the NSEC3
  iteration collapse, 6th and 11th percentile: caps, CVE and re-signing were
  one event. CVE-2022-38177/38178 (2022-09) sits at the 97th percentile of the
  reverse ECDSA curve, which is the ARIN block re-signing of 2022-11 in the
  spike ledger; the CVE is a BIND validator memory leak, so this is timing,
  not cause.
* The remaining NSEC3 CVEs (2024-02, 2026) sit in the middle half.

Only three RFCs and a handful of CVEs fall inside the curves' coverage, so
this is a table of cases, not a distribution.
