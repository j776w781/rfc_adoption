# Phase 7: each program's update timeline against the adoption data

For an agent with no other context. This redoes `docs/releases_vs_adoption.md`, `docs/release_scan.md` and the case
studies in `scripts/program_rfc_cases.py` on the verified timelines of Phase 2 and 3 and on the Phase 4 normalised
default rows, as corrected after Phase 5. The specification is `docs/handoff/07_phase7_brief.md`.

Everything here comes from `scripts/software_vs_adoption.py`. It reads only the inputs the brief lists, uses seed
20260929 with 1,000 draws for every null, and writes `out/analysis/software_vs_adoption.json` with one key per question
plus `observable_mapping`, `excluded` and `notes`, and one long-form CSV per question,
`out/analysis/software_vs_adoption_<question>.csv`. Two full runs give a byte-identical JSON, and a run of a single
question with `--only` reproduces the same file. Tests: `python -m pytest tests/test_software_vs_adoption.py -q`.

Rebuild everything: `python scripts/software_vs_adoption.py`. It takes about ten seconds.

## Short answer

Across 202 program-level release tests, 103 default-change event tests, 23 ledger tests and 248 adoption spikes, the
software timelines do not line up with adoption more often than chance. One spike alignment beats its chance rate: spikes
in the share of zero-iteration NSEC3 names in 2022 follow the zero-iteration signer defaults, but those defaults, the
IETF draft and RFC 9276 all land in the same eight months, and the forward TLDs involved belong to two registry
operators, so the alignment cannot be credited to software. One ledger event passes: the months after PowerDNS 3.2 made
RSASHA256 its default show more block-level signing to algorithm 8, and that rests on one RIPE block of 64 delegations.

## How it was done

**Series.** A share is a percentage. Forward shares use the OpenINTEL TLD zone files per TLD. Reverse shares use only
the strict panel `_pooled-afrinic-arin`; per-RIR series are used only as counts, in question 4. Denominators are signed
zones, `algorithm_dnskey _total`, or DS-carrying delegations, `algorithm_ds _total` and `digest_type_ds _total`. NSEC3
iteration shares are over NSEC3 owner names, `nsec3_iterations _total`, and count names, not zones. A month with fewer
than 30 in the peak-day denominator is left out.

Shares are built from `domain_days`, which gives the month's mean daily share. `domains_peak` is not additive across
values: in .se in 2019-06, while zones moved from 1 to 5 NSEC3 iterations, the per-value peaks sum to 115% of the
`_total` peak. For the reverse corpus one snapshot is taken per month, so the two columns agree. Sums over several
algorithm values still count a zone that carries two of them twice, which is why a few summed shares reach 100 to 127%.

**Detrending.** Every share is detrended by a centred 25-month rolling median, with at least 13 months in the window
at the series ends.

**Release events.** A release is a stable, publicly shipped tag from `data/software/timelines/<program>.json`, dated by
its `released` field and taken per calendar month. pdns-rec aliases and the three never-public pdns-rec tags are left
out. Default rows use the Phase 4 `timing_*` columns, which already apply `first_public_tag`.

**Tests.** Question 1 compares the 3 months from the release month on with the 3 months before. Question 2 compares 12
with 12. An event without the full before-period and after-period in a corpus gets "no test" and no number. The 90%
band means about one test in ten falls outside it by chance.

## What the data says about the brief's coverage facts

Checked from the parquet files, recorded under `notes.coverage` in the JSON:

- The forward TLDs start as the brief says: se and nu 2016-06, gov and fed.us 2017-05, ee 2019-07, ch and li 2020-05.
  All end 2023-12 except fed.us, which ends 2022-10.
- fed.us never has a signed zone, so it has no share series at all. Every fed.us cell below is "no test" for that
  reason, and the per-program text does not repeat it.
- The strict panel is `_pooled-afrinic-arin` in `out/panel_run`, with rows from 2009-04 and a signed-delegation series
  from 2011-05, when it held 32 signed delegations.
- **One disagreement with the brief's framing:** the panel and the delegation ledger are dated one month later than
  the server run's reverse series. For afrinic and arin, all 168 and 181 overlapping months agree exactly after a
  one-month shift, and only 72 and 12 agree without it. `docs/handoff/03_prevalence_metrics.md` notes this for the gap
  months. Every reverse date in this report uses the panel and ledger dating, and question 4 re-dates the per-RIR counts
  by one month to match. Event timing in the reverse corpus is therefore uncertain by about a month.
- `nsec3_salt_empty` holds only the value `present`, equal to `_total` in all 404 forward source-months, so salt length
  is not observable, and the salt rows are unmapped.

Recompute: `python scripts/software_vs_adoption.py --only q4 && python -c "import json;d=json.load(open('out/analysis/software_vs_adoption.json'));print(json.dumps(d['notes']['coverage'],indent=1));print(d['q4_spikes']['reverse_dating_check'])"`

## Observable mapping

46 of the 154 normalised rows map to an observable; the other 108 are listed with a reason under
`excluded.rows_not_observable`. The mapping is by mechanism and before and after text, row by row, in `ROW_MAP` in the
script, and the test file pins it.

| mechanism or topic | forward observable | reverse observable |
|---|---|---|
| alg-ecdsa (ECDSA P-256 default) | algorithm_dnskey 13 share of signed zones | algorithm_ds 13 share of signed delegations (panel) |
| alg-rsa-sha2 (RSASHA256 default) | algorithm_dnskey 8 | algorithm_ds 8 |
| dnskey: RSASHA1 keygen default added or removed (extension) | algorithm_dnskey 5 | algorithm_ds 5 |
| algorithm removal in a signer: RSAMD5, GOST, DSA (extension) | algorithm_dnskey 1 / 12 / 3+6 | algorithm_ds 1 / 12 / 3+6 |
| crypto-policy SHA-1 refusal in a signer library (extension) | algorithm_dnskey 5+7 | algorithm_ds 5+7 |
| ds-digest (SHA-1 DS no longer generated) | digest_type_ds 1 share | digest_type_ds 1 share |
| ds-digest (SHA-256 / SHA-384 DS) | digest_type_ds 2 / 4 | digest_type_ds 2 / 4 |
| RSA key-size defaults (extension) | rsa_key_bitsize 1024 (or under 1024) over rsa_key_bitsize _total | not observable (a DS carries no key size) |
| nsec3 opt-out default (extension) | nsec3_optout 1 over nsec3_optout _total (owner names) | not observable |
| nsec3, nsec3-iterations (signer NSEC3 defaults) | nsec3_iterations owner names at the new value over nsec3_iterations _total; rr_type NSEC3PARAM over algorithm_dnskey _total for NSEC3 use | not observable |
| NSEC3 salt, NSEC/NSEC3 TTLs | not observable (nsec3_salt_empty only holds 'present' = _total; no TTLs) | not observable |
| validator or authoritative NSEC3 iteration caps (indirect / clamp) | nsec3_iterations owner names above the cap over _total, labelled indirect | not observable |
| cds-cdnskey | rr_type CDS over algorithm_dnskey _total | not observable |
| validation, trust-anchor, trust-anchor-5011, validator limits and algorithm support | not observable in zone data | not observable |
| rrsig timing, key-management state | not observable | not observable |

Rows mapped, with the relation used. "indirect-validator-cap" marks a validator limit, tested on the NSEC3 iteration
series only as an indirect effect. "direct-auth-clamp" marks pdns-auth rewriting what it serves.

| program | row | timing | observable | expected direction | relation | upgrade | opt-in |
|---|---|---|---|---|---|---|---|
| bind9 | d02-keygen-default-alg-rsasha1 | 2010-02-16 | alg5 | + | direct | yes | no |
| bind9 | d03-signzone-nsec3-iterations-100-to-10 | 2010-02-16 | iter10 | + | direct | yes | no |
| bind9 | d06-keygen-no-default-alg | 2018-01-17 | alg5 | - | direct | yes | no |
| bind9 | d08-rsamd5-removed | 2019-03-20 | alg1 | - | direct | yes | no |
| bind9 | d09-gost-removed | 2019-03-20 | alg12 | - | direct | yes | no |
| bind9 | d10-dsa-removed | 2019-03-20 | alg3_6 | - | direct | yes | no |
| bind9 | d13-ds-cds-sha1-dropped | 2020-02-12 | digest1 | - | direct | yes | no |
| bind9 | d14-keygen-rsa-zsk-2048 | 2020-02-12 | rsa1024 | - | direct | yes | no |
| bind9 | d15-dnssec-policy-default-ecdsap256 | 2020-02-12 | alg13 | + | direct | no | yes |
| bind9 | d16-dnssec-policy-default-key-size-2048 | 2020-02-12 | rsa1024 | - | direct | no | yes |
| bind9 | d17-nsec3param-default-in-policy | 2020-12-07 | iter5 | + | direct | no | yes |
| bind9 | d18-nsec3param-default-0-0 | 2022-01-24 | iter0 | + | direct | yes | yes |
| bind9 | d20-dnssec-cds-sha2-only | 2022-01-24 | digest1 | - | direct | yes | no |
| bind9 | d21-signzone-nsec3-iterations-0 | 2022-07-07 | iter0 | + | direct | yes | no |
| bind9 | l01-nsec3-max-iterations-150 | 2021-05-12 | iter_gt150 | - | indirect-validator-cap | yes | no |
| bind9 | l02-nsec3-max-iterations-50 | 2024-07-08 | iter_gt50 | - | indirect-validator-cap | yes | no |
| knot | knot[1]@2.0.0 | 2015-06-26 | alg8 | + | direct | no | no |
| knot | knot[2]@2.1.0 | 2016-01-14 | alg13 | + | direct | no | no |
| knot | knot[3]@2.2.0 | 2016-04-26 | rsa1024 | - | direct | no | no |
| knot | knot[7]@2.6.0 | 2017-09-29 | alg3_6 | - | direct | yes | no |
| knot | knot[8]@2.7.0 | 2018-08-03 | rsa_lt1024 | - | direct | yes | no |
| knot | knot[10]@2.8.0 | 2019-03-05 | cds | - | direct | yes | no |
| knot | knot[11]@2.8.0 | 2019-03-05 | digest1 | - | direct | yes | no |
| knot | knot[12]@3.0.2 | 2020-11-11 | alg5_7 | - | direct | yes | no |
| knot | knot[14]@3.2.0 | 2022-08-22 | iter0 | + | direct | yes | no |
| knot | knot[19]@3.6.0 | 2026-09-08 | iter_gt256 | - | direct | yes | no |
| kresd | kresd[9]@5.3.1 | 2021-03-31 | iter_gt150 | - | indirect-validator-cap | yes | no |
| kresd | kresd[12]@5.7.1 | 2024-02-13 | iter_gt50 | - | indirect-validator-cap | yes | no |
| kresd | kresd[15]@6.0.6 | 2024-02-13 | iter_gt50 | - | indirect-validator-cap | yes | no |
| opendnssec | opendnssec[3]@1.1.0rc1 | 2010-05-26 | optout | - | direct | no | no |
| opendnssec | opendnssec[5]@1.2.0b1 | 2011-03-18 | alg8 | + | direct | no | no |
| opendnssec | opendnssec[5]@1.2.0b1 | 2011-03-18 | alg7 | - | direct | no | no |
| opendnssec | opendnssec[13]@2.1.0 | 2017-02-22 | digest1 | - | direct | yes | no |
| pdns-auth | pdns-auth[0]@3.2 | 2013-01-17 | alg8 | + | direct | no | no |
| pdns-auth | pdns-auth[1]@3.3 | 2013-07-05 | optout | - | direct | no | yes |
| pdns-auth | pdns-auth[3]@3.4.0 | 2014-09-30 | iter_gt500 | - | direct-auth-clamp | yes | no |
| pdns-auth | pdns-auth[4]@3.4.7 | 2015-11-03 | iter_gt500 | - | direct-auth-clamp | yes | no |
| pdns-auth | pdns-auth[7]@4.0.0 | 2016-07-08 | alg13 | + | direct | no | no |
| pdns-auth | pdns-auth[8]@4.0.0 | 2016-07-08 | alg13 | + | direct | no | no |
| pdns-auth | pdns-auth[9]@4.0.0 | 2016-07-08 | rsa1024 | - | direct | no | no |
| pdns-auth | pdns-auth[10]@4.5.0 | 2021-07-12 | iter_gt100 | - | direct-auth-clamp | yes | no |
| pdns-auth | pdns-auth[11]@4.6.0 | 2022-01-24 | iter0 | + | direct | no | yes |
| pdns-rec | nsec3-max-iterations-2500 | 2017-12-04 | iter_gt2500 | - | indirect-validator-cap | yes | no |
| pdns-rec | nsec3-max-iterations-150 | 2021-06-07 | iter_gt150 | - | indirect-validator-cap | yes | no |
| pdns-rec | nsec3-max-iterations-50 | 2024-01-09 | iter_gt50 | - | indirect-validator-cap | yes | no |
| unbound | unbound[1]@0.5 | 2007-09-25 | iter_gt150 | - | indirect-validator-cap | yes | no |
| unbound | unbound[20]@1.13.2 | 2021-08-05 | iter_gt150 | - | indirect-validator-cap | yes | no |

Unmapped rows by reason: 69 are validator-side behaviour, meaning validation, trust anchors, validator algorithm support, DS-digest handling, caching and limits other than the NSEC3 caps; 16 are signature timing or serving options; 8 are NSEC3 serving details, salt or TTLs; 5 are key-management state; 4 are OpenDNSSEC enforcer settings with no zone-data trace; 5 are not default changes; and 1 is an NSD compile default.

Recompute: `python scripts/software_vs_adoption.py --only q1 && python -c "import pandas as pd;print(pd.read_csv('out/analysis/software_vs_adoption_mapping.csv')[['program','row_id','observable','expected_direction','relation']].to_string());print(pd.read_csv('out/analysis/software_vs_adoption_excluded.csv').reason.value_counts())"`

## Per program: questions 1 and 2

In each program's first table, question 1: a test is one observable in one corpus. "Null percentile of the mean" is
where the superposed-epoch mean of the 3-month change sits among 1,000 circular shifts of the program's own release
months within its span. The last column asks whether more release months fall outside the single-release 90% band than
under the shifted schedules. The second table is question 2, one row per default row and corpus with coverage. d12 is
the detrended mean of the 12 months from the release month on minus the 12 months before, in percentage points; the band
is the 5th to 95th percentile of the same statistic at 1,000 random months of the same series.

Every forward result below measures a handful of registry operators. Earlier work found every forward adoption jump
belonged to one of two registry operators, paired across that operator's TLDs, so a forward event study measures
whether about a dozen organisations moved, not whether a market responded.

Recompute question 1: `python scripts/software_vs_adoption.py --only q1 && python -c "import pandas as pd;d=pd.read_csv('out/analysis/software_vs_adoption_q1.csv');print(d[d.status=='tested'][['program','observable','source','release_months_tested','observed_mean_d3','percentile','p_two_sided','share_release_months_outside_band','null_mean_share_outside','p_share_outside_ge_observed']].to_string())"`

Recompute question 2: `python scripts/software_vs_adoption.py --only q2 && python -c "import pandas as pd;d=pd.read_csv('out/analysis/software_vs_adoption_q2.csv');print(d[['program','row_id','observable','source','status','share_month_before','observed_d12','band_lo','band_hi','percentile','outside_90_band','reason']].to_string())"`

Totals: question 1 has 202 tested of 289. 6 means fall outside the 90% null band against 20.2 expected, and 5 tests have an excess of release months outside the band at p < 0.10.
Question 2 has 103 tested events, of which 2 fall outside the band against 10.3 expected, and 245 program, row and corpus cells have no test. Split by upgrade path:

| applies on upgrade, opt-in | tested | outside the 90% band | outside and in the expected direction | expected by chance |
|---|---|---|---|---|
| True, False | 75 | 2 | 1 | 7.5 |
| False, True | 17 | 0 | 0 | 1.7 |
| True, True | 6 | 0 | 0 | 0.6 |
| False, False | 5 | 0 | 0 | 0.5 |

The split does not separate the groups: no group has more events outside the band than chance gives it. The rows that
reach existing zones only through a new signing, opt-in or not applied on upgrade, are no different from the rest.

### bind9

BIND 9 has 444 stable releases in 190 release months. Its mapped rows touch twelve observables, from the RSASHA1
keygen default to the NSEC3 iteration caps. Of 90 program-level tests, 58 had coverage.

**What beat chance:** nothing at the program level. No test put the superposed-epoch mean outside the 90% band of the
circular-shift null, where about 6 of 58 would by chance, and no test had more release months outside the single-release
band than the shifted schedules did.

**Default-change events:** 12 rows were tested in at least one corpus. Two of 47 tests fall outside their 90% band,
against about 5 expected by chance. d08, the RSAMD5 removal, moved against its expected direction in .se, on a share of
0.00007%. l01, the fixed validator cap of 150 iterations, is followed by a fall in the share of NSEC3 names above 150 in
.li, at the 2nd percentile. That is one TLD of one registry operator, and the cap acts on zones only indirectly. d21, the
signzone default of 0 iterations, is followed by a rise in the 0-iteration share in all six forward TLDs, at percentiles
68 to 93, and none of the six leaves its band. It shares its window with knot[14] and with RFC 9276, see Knot DNS. d15, the
ECDSA default policy, is opt-in and does not apply on upgrade; it is tested in .se, .nu, .gov and the panel and is
inside its band in all four.

**Not testable:** d02 and d03 shipped in 2010-02, before any corpus has a signed-zone series. d09, the GOST removal, has
no series: algorithm 12 never appears in any corpus. l02, the cap of 50 from 2024-07, has no after-period, because the
forward corpus ends 2023-12 and the reverse corpus cannot see NSEC3.

Question 1:

| observable | corpora tested | release months tested per corpus | null percentile of the mean, lowest to highest | tests outside the 90% null | tests where more release months fall outside the band than chance, p < 0.10 |
|---|---|---|---|---|---|
| alg1 | se | 72 | 41.2 to 41.2 | 0 of 1 | 0 of 1 |
| alg13 | se, nu, gov, ee, ch, li, panel | 72, 72, 63, 48, 38, 38, 135 | 47.0 to 68.8 | 0 of 7 | 0 of 7 |
| alg3_6 | se, ch | 72, 38 | 45.2 to 49.4 | 0 of 2 | 0 of 2 |
| alg5 | se, nu, gov, ee, ch, li, panel | 72, 72, 63, 48, 38, 38, 135 | 21.6 to 64.3 | 0 of 7 | 0 of 7 |
| digest1 | se, nu, gov, ch, li, panel | 72, 72, 63, 38, 38, 135 | 20.7 to 89.6 | 0 of 6 | 0 of 6 |
| iter0 | se, nu, gov, ee, ch, li | 72, 72, 63, 48, 38, 38 | 26.8 to 72.8 | 0 of 6 | 0 of 6 |
| iter10 | se, nu, gov, ee, ch, li | 72, 72, 63, 48, 38, 38 | 18.1 to 60.4 | 0 of 6 | 0 of 6 |
| iter5 | se, nu, gov, ee, ch, li | 72, 72, 63, 48, 38, 38 | 18.9 to 82.1 | 0 of 6 | 0 of 6 |
| iter_gt150 | se, nu, ee, ch, li | 72, 72, 48, 38, 38 | 45.4 to 82.6 | 0 of 5 | 0 of 5 |
| iter_gt50 | se, nu, gov, ee, ch, li | 72, 72, 63, 48, 38, 38 | 44.8 to 80.1 | 0 of 6 | 0 of 6 |
| rsa1024 | se, nu, gov, ee, ch, li | 72, 72, 63, 48, 38, 38 | 28.4 to 55.7 | 0 of 6 | 0 of 6 |

Not tested, besides fed.us: alg1 in nu, gov, ee, ch, li, panel: the value is present in only 2 months of this series; the value is present in only 3 months of this series; the value never appears in this series. alg12 in se, nu, gov, ee, ch, li, panel: the value never appears in this series. alg3_6 in nu, gov, ee, li, panel: the value never appears in this series. digest1 in ee: the value never appears in this series. iter_gt150 in gov: the value is present in only 5 months of this series.

Question 2:

| row | timing | observable, relation | corpus | upgrade | opt-in | share before, % | d12, pp | 90% band | percentile | outside |
|---|---|---|---|---|---|---|---|---|---|---|
| d06-keygen-no-default-alg | 2018-01-17 | alg5, direct | se | yes | no | 0.3003 | -0.01809 | -0.02482 to 0.0124 | 13.7 | no |
| d06-keygen-no-default-alg | 2018-01-17 | alg5, direct | nu | yes | no | 0.09384 | -0.006195 | -0.01714 to 0.01218 | 25.6 | no |
| d06-keygen-no-default-alg | 2018-01-17 | alg5, direct | panel | yes | no | 17.07 | -1.211 | -1.632 to 2.229 | 11.1 | no |
| d08-rsamd5-removed | 2019-03-20 | alg1, direct | se | yes | no | 7.1e-05 | 1.2e-05 | -2e-05 to 7e-06 | 97.7 | yes |
| d10-dsa-removed | 2019-03-20 | alg3_6, direct | se | yes | no | 0.000133 | 2e-06 | -8.2e-05 to 1e-05 | 82.7 | no |
| d13-ds-cds-sha1-dropped | 2020-02-12 | digest1, direct | se | yes | no | 62.38 | -1.056 | -3.294 to 3.255 | 16.2 | no |
| d13-ds-cds-sha1-dropped | 2020-02-12 | digest1, direct | nu | yes | no | 69.36 | -0.2549 | -11.78 to 10.12 | 31.1 | no |
| d13-ds-cds-sha1-dropped | 2020-02-12 | digest1, direct | gov | yes | no | 83.14 | 0.206 | -7.852 to 1.675 | 79.7 | no |
| d13-ds-cds-sha1-dropped | 2020-02-12 | digest1, direct | panel | yes | no | 60.85 | -0.04545 | -1.214 to 1.098 | 42.9 | no |
| d14-keygen-rsa-zsk-2048 | 2020-02-12 | rsa1024, direct | se | yes | no | 8.756 | -0.1488 | -1.624 to 1.734 | 37.0 | no |
| d14-keygen-rsa-zsk-2048 | 2020-02-12 | rsa1024, direct | nu | yes | no | 29.2 | -0.4124 | -1.784 to 2.256 | 28.8 | no |
| d14-keygen-rsa-zsk-2048 | 2020-02-12 | rsa1024, direct | gov | yes | no | 82.62 | 0.4448 | -0.4846 to 0.5283 | 83.5 | no |
| d15-dnssec-policy-default-ecdsap256 | 2020-02-12 | alg13, direct | se | no | yes | 52.82 | -1.293 | -1.936 to 1.137 | 12.4 | no |
| d15-dnssec-policy-default-ecdsap256 | 2020-02-12 | alg13, direct | nu | no | yes | 37.99 | -0.1606 | -0.3149 to 0.2817 | 16.4 | no |
| d15-dnssec-policy-default-ecdsap256 | 2020-02-12 | alg13, direct | gov | no | yes | 12.59 | 0.1485 | -0.2969 to 3.155 | 53.6 | no |
| d15-dnssec-policy-default-ecdsap256 | 2020-02-12 | alg13, direct | panel | no | yes | 22.86 | 0.264 | -0.2508 to 0.3634 | 88.0 | no |
| d16-dnssec-policy-default-key-size-2048 | 2020-02-12 | rsa1024, direct | se | no | yes | 8.756 | -0.1488 | -1.503 to 1.734 | 35.5 | no |
| d16-dnssec-policy-default-key-size-2048 | 2020-02-12 | rsa1024, direct | nu | no | yes | 29.2 | -0.4124 | -1.784 to 2.256 | 27.0 | no |
| d16-dnssec-policy-default-key-size-2048 | 2020-02-12 | rsa1024, direct | gov | no | yes | 82.62 | 0.4448 | -0.4549 to 0.5283 | 84.1 | no |
| d17-nsec3param-default-in-policy | 2020-12-07 | iter5, direct | se | no | yes | 38.7 | -0.8238 | -0.945 to 0.6609 | 10.2 | no |
| d17-nsec3param-default-in-policy | 2020-12-07 | iter5, direct | nu | no | yes | 12.48 | 0 | -0.01198 to 0.09227 | 40.4 | no |
| d17-nsec3param-default-in-policy | 2020-12-07 | iter5, direct | gov | no | yes | 1.265 | -0.000803 | -0.02508 to 0.02626 | 42.2 | no |
| d17-nsec3param-default-in-policy | 2020-12-07 | iter5, direct | ee | no | yes | 96.4 | -0.4991 | -0.5304 to 0.2687 | 8.4 | no |
| d18-nsec3param-default-0-0 | 2022-01-24 | iter0, direct | se | yes | yes | 0.1939 | 0.02612 | -0.00044 to 0.3958 | 85.2 | no |
| d18-nsec3param-default-0-0 | 2022-01-24 | iter0, direct | nu | yes | yes | 6.383 | 3.1e-05 | -0.003218 to 0.3765 | 33.5 | no |
| d18-nsec3param-default-0-0 | 2022-01-24 | iter0, direct | gov | yes | yes | 0.1175 | -0.03619 | -0.05432 to 0.2266 | 8.4 | no |
| d18-nsec3param-default-0-0 | 2022-01-24 | iter0, direct | ee | yes | yes | 0.02446 | -3.8e-05 | -3.8e-05 to 0.01127 | 5.1 | no |
| d18-nsec3param-default-0-0 | 2022-01-24 | iter0, direct | ch | yes | yes | 0.6334 | 0.01274 | 0.01112 to 1.127 | 12.2 | no |
| d18-nsec3param-default-0-0 | 2022-01-24 | iter0, direct | li | yes | yes | 1.564 | 0.001285 | -0.001447 to 1.055 | 16.9 | no |
| d20-dnssec-cds-sha2-only | 2022-01-24 | digest1, direct | se | yes | no | 56.19 | 0 | -3.294 to 3.255 | 71.2 | no |
| d20-dnssec-cds-sha2-only | 2022-01-24 | digest1, direct | nu | yes | no | 61.16 | 0.1378 | -11.46 to 10.12 | 72.4 | no |
| d20-dnssec-cds-sha2-only | 2022-01-24 | digest1, direct | gov | yes | no | 68.67 | -0.06854 | -7.852 to 1.727 | 74.8 | no |
| d20-dnssec-cds-sha2-only | 2022-01-24 | digest1, direct | ch | yes | no | 18.88 | 0.3049 | -2.163 to 0.4537 | 86.3 | no |
| d20-dnssec-cds-sha2-only | 2022-01-24 | digest1, direct | li | yes | no | 11.88 | 1.405 | -3.197 to 1.856 | 88.0 | no |
| d20-dnssec-cds-sha2-only | 2022-01-24 | digest1, direct | panel | yes | no | 51.99 | -0.7547 | -1.157 to 1.084 | 12.8 | no |
| d21-signzone-nsec3-iterations-0 | 2022-07-07 | iter0, direct | se | yes | no | 0.362 | 0.03992 | -0.000439 to 0.3115 | 90.4 | no |
| d21-signzone-nsec3-iterations-0 | 2022-07-07 | iter0, direct | nu | yes | no | 6.578 | 0.1068 | -0.003244 to 0.2356 | 92.5 | no |
| d21-signzone-nsec3-iterations-0 | 2022-07-07 | iter0, direct | gov | yes | no | 0 | 0.08094 | -0.03731 to 0.2266 | 88.1 | no |
| d21-signzone-nsec3-iterations-0 | 2022-07-07 | iter0, direct | ee | yes | no | 0.03585 | 0.00717 | -3.8e-05 to 0.01127 | 84.4 | no |
| d21-signzone-nsec3-iterations-0 | 2022-07-07 | iter0, direct | ch | yes | no | 3.87 | 1.014 | 0.01199 to 1.119 | 67.7 | no |
| d21-signzone-nsec3-iterations-0 | 2022-07-07 | iter0, direct | li | yes | no | 6.302 | 1.014 | -0.008238 to 1.055 | 70.0 | no |
| l01-nsec3-max-iterations-150 | 2021-05-12 | iter_gt150, indirect-validator-cap | se | yes | no | 0.000149 | 0 | -7.6e-05 to 7e-06 | 64.3 | no |
| l01-nsec3-max-iterations-150 | 2021-05-12 | iter_gt150, indirect-validator-cap | nu | yes | no | 0.00193 | -1e-06 | -9.5e-05 to 0.000148 | 52.9 | no |
| l01-nsec3-max-iterations-150 | 2021-05-12 | iter_gt150, indirect-validator-cap | gov | yes | no | 0 | 0.03842 | -0.03842 to 0.03842 | 93.5 | no |
| l01-nsec3-max-iterations-150 | 2021-05-12 | iter_gt150, indirect-validator-cap | ee | yes | no | 0.004866 | -4.7e-05 | -0.003322 to 0 | 34.1 | no |
| l01-nsec3-max-iterations-150 | 2021-05-12 | iter_gt150, indirect-validator-cap | ch | yes | no | 0.04707 | -0.00282 | -0.00282 to 2.1e-05 | 2.8 | no |
| l01-nsec3-max-iterations-150 | 2021-05-12 | iter_gt150, indirect-validator-cap | li | yes | no | 0.08158 | -0.007297 | -0.007109 to 0 | 2.3 | yes |

| row | timing | observable | why not tested |
|---|---|---|---|
| d02-keygen-default-alg-rsasha1 | 2010-02-16 | alg5 | no test in any corpus: no before-period in se, nu, gov, ee, ch, li, panel |
| d03-signzone-nsec3-iterations-100-to-10 | 2010-02-16 | iter10 | no test in any corpus: no before-period in se, nu, gov, ee, ch, li |
| d06-keygen-no-default-alg | 2018-01-17 | alg5 | no test: no before-period in gov, ee, ch, li |
| d08-rsamd5-removed | 2019-03-20 | alg1 | no test: the value is absent in every month of the window 2018-03..2020-02 in nu, gov, panel; no before-period in ee; the value never appears in this series in ch, li |
| d09-gost-removed | 2019-03-20 | alg12 | no test in any corpus: the value is absent in every month of the window 2018-03..2020-02 in se, nu, gov, panel; the value never appears in this series in ee, ch, li |
| d10-dsa-removed | 2019-03-20 | alg3_6 | no test: the value is absent in every month of the window 2018-03..2020-02 in nu, gov, panel; the value never appears in this series in ee, li; no before-period in ch |
| d13-ds-cds-sha1-dropped | 2020-02-12 | digest1 | no test: the value never appears in this series in ee; no before-period in ch, li |
| d14-keygen-rsa-zsk-2048 | 2020-02-12 | rsa1024 | no test: no before-period in ee, ch, li |
| d15-dnssec-policy-default-ecdsap256 | 2020-02-12 | alg13 | no test: no before-period in ee, ch, li |
| d16-dnssec-policy-default-key-size-2048 | 2020-02-12 | rsa1024 | no test: no before-period in ee, ch, li |
| d17-nsec3param-default-in-policy | 2020-12-07 | iter5 | no test: no before-period in ch, li |
| d20-dnssec-cds-sha2-only | 2022-01-24 | digest1 | no test: the value is absent in every month of the window 2021-01..2022-12 in ee |
| l02-nsec3-max-iterations-50 | 2024-07-08 | iter_gt50 | no test in any corpus: no after-period in se, nu, gov, ee, ch, li |

### knot

Knot DNS has 174 stable releases in 126 release months, and ten observables.

**What beat chance:** no program-level mean is outside the null band. In .ee, three observables, algorithms 8 and 13 and
1024-bit RSA, have more release months outside the band than the shifted schedules, at p between 0.057 and 0.067. .ee
has 36 testable Knot release months, and three of 54 tests at p < 0.10 is fewer than the 5 expected by chance.

**Default-change events:** knot[2]@2.1.0, the ECDSA signing default of 2016-01, is testable only on the panel. The
algorithm 13 share of panel signed delegations was 0.25% before it and moved by -0.019 pp in the 12 months after,
relative to the 12 before, at the 15th percentile of random months. knot[1]@2.0.0, the RSASHA256 default of 2015-06,
is followed by a fall of 2.8 pp in the algorithm 8 panel share, at the 7th percentile, opposite to its direction.
knot[14]@3.2.0, iterations 10 to 0, is followed by a rise in the 0-iteration share in all six forward TLDs, at
percentiles 83 to 92, but no single TLD leaves its band. The six TLDs belong to four registry operators, bind9 d21
shipped a month earlier, and RFC 9276 was published in the same month as knot 3.2.0. This is one coincident pattern
with at most four independent observations, and it is not attributable to either program.

**Not testable:** knot[1], knot[2] and knot[3] predate the forward corpus. knot[3], the RSA 2048 default of 2016-04,
has no before-period in any corpus that records key size. knot[19]@3.6.0, the cap of 256 iterations, shipped 2026-09,
after both corpora end for NSEC3.

Question 1:

| observable | corpora tested | release months tested per corpus | null percentile of the mean, lowest to highest | tests outside the 90% null | tests where more release months fall outside the band than chance, p < 0.10 |
|---|---|---|---|---|---|
| alg13 | se, nu, gov, ee, ch, li, panel | 62, 62, 53, 36, 30, 30, 121 | 50.3 to 95.0 | 0 of 7 | 1 of 7 |
| alg3_6 | se, ch | 62, 30 | 43.4 to 51.4 | 0 of 2 | 0 of 2 |
| alg5_7 | se, nu, gov, ee, ch, li, panel | 62, 62, 53, 36, 30, 30, 121 | 17.2 to 54.6 | 0 of 7 | 0 of 7 |
| alg8 | se, nu, gov, ee, ch, li, panel | 62, 62, 53, 36, 30, 30, 121 | 11.2 to 79.3 | 0 of 7 | 1 of 7 |
| cds | se, nu, gov, ee, ch, li | 62, 62, 53, 36, 30, 30 | 22.6 to 65.6 | 0 of 6 | 0 of 6 |
| digest1 | se, nu, gov, ch, li, panel | 62, 62, 53, 30, 30, 121 | 40.1 to 92.7 | 0 of 6 | 0 of 6 |
| iter0 | se, nu, gov, ee, ch, li | 62, 62, 53, 36, 30, 30 | 20.7 to 73.1 | 0 of 6 | 0 of 6 |
| iter_gt256 | nu, ch | 62, 30 | 7.8 to 29.0 | 0 of 2 | 0 of 2 |
| rsa1024 | se, nu, gov, ee, ch, li | 62, 62, 53, 36, 30, 30 | 30.2 to 61.3 | 0 of 6 | 1 of 6 |
| rsa_lt1024 | se, nu, gov, ch, li | 62, 62, 53, 30, 30 | 38.4 to 56.3 | 0 of 5 | 0 of 5 |

Not tested, besides fed.us: alg3_6 in nu, gov, ee, li, panel: the value never appears in this series. digest1 in ee: the value never appears in this series. iter_gt256 in se, gov, ee, li: the value is present in only 10 months of this series; the value never appears in this series. rsa_lt1024 in ee: the value never appears in this series.

Question 2:

| row | timing | observable, relation | corpus | upgrade | opt-in | share before, % | d12, pp | 90% band | percentile | outside |
|---|---|---|---|---|---|---|---|---|---|---|
| knot[1]@2.0.0 | 2015-06-26 | alg8, direct | panel | no | no | 65.15 | -2.833 | -3.094 to 3.454 | 6.8 | no |
| knot[2]@2.1.0 | 2016-01-14 | alg13, direct | panel | no | no | 0.2535 | -0.01912 | -0.2382 to 0.3565 | 15.1 | no |
| knot[7]@2.6.0 | 2017-09-29 | alg3_6, direct | se | yes | no | 0.000135 | -6.6e-05 | -8.2e-05 to 9e-06 | 7.0 | no |
| knot[8]@2.7.0 | 2018-08-03 | rsa_lt1024, direct | se | yes | no | 0.1775 | 0.005362 | -0.02377 to 0.02307 | 70.8 | no |
| knot[8]@2.7.0 | 2018-08-03 | rsa_lt1024, direct | nu | yes | no | 1.225 | -0.8093 | -1.246 to 0.1887 | 12.1 | no |
| knot[8]@2.7.0 | 2018-08-03 | rsa_lt1024, direct | gov | yes | no | 0.5653 | -0.06803 | -0.08497 to 0.1144 | 7.0 | no |
| knot[10]@2.8.0 | 2019-03-05 | cds, direct | se | yes | no | 0.137 | -0.00094 | -0.00094 to 0.1474 | 5.2 | no |
| knot[10]@2.8.0 | 2019-03-05 | cds, direct | nu | yes | no | 0.1949 | 0 | -0.001431 to 0.1344 | 35.7 | no |
| knot[10]@2.8.0 | 2019-03-05 | cds, direct | gov | yes | no | 6.644 | 0.3113 | 0 to 3.003 | 69.3 | no |
| knot[11]@2.8.0 | 2019-03-05 | digest1, direct | se | yes | no | 62.24 | 3.014 | -3.343 to 3.255 | 93.5 | no |
| knot[11]@2.8.0 | 2019-03-05 | digest1, direct | nu | yes | no | 70.34 | 8.916 | -10.66 to 11.36 | 91.5 | no |
| knot[11]@2.8.0 | 2019-03-05 | digest1, direct | gov | yes | no | 80.15 | 0.5016 | -7.852 to 1.727 | 81.1 | no |
| knot[11]@2.8.0 | 2019-03-05 | digest1, direct | panel | yes | no | 64.77 | -0.5124 | -1.157 to 1.098 | 19.4 | no |
| knot[12]@3.0.2 | 2020-11-11 | alg5_7, direct | se | yes | no | 0.4947 | -0.000206 | -0.07403 to 0.07899 | 54.6 | no |
| knot[12]@3.0.2 | 2020-11-11 | alg5_7, direct | nu | yes | no | 5.041 | -0.013 | -0.5534 to 0.5981 | 40.5 | no |
| knot[12]@3.0.2 | 2020-11-11 | alg5_7, direct | gov | yes | no | 29.1 | 0.0124 | -1.162 to 0.02791 | 90.1 | no |
| knot[12]@3.0.2 | 2020-11-11 | alg5_7, direct | ee | yes | no | 0.7956 | -0.1161 | -0.2529 to 0 | 15.8 | no |
| knot[12]@3.0.2 | 2020-11-11 | alg5_7, direct | panel | yes | no | 25.34 | 0.4654 | -3.717 to 4.53 | 70.1 | no |
| knot[14]@3.2.0 | 2022-08-22 | iter0, direct | se | yes | no | 0.5864 | 0.139 | -0.000439 to 0.3115 | 91.2 | no |
| knot[14]@3.2.0 | 2022-08-22 | iter0, direct | nu | yes | no | 6.734 | 0.1703 | -0.003244 to 0.3025 | 92.2 | no |
| knot[14]@3.2.0 | 2022-08-22 | iter0, direct | gov | yes | no | 0 | 0.1338 | -0.05432 to 0.2266 | 91.1 | no |
| knot[14]@3.2.0 | 2022-08-22 | iter0, direct | ee | yes | no | 0.05082 | 0.007178 | -3.8e-05 to 0.01127 | 89.0 | no |
| knot[14]@3.2.0 | 2022-08-22 | iter0, direct | ch | yes | no | 3.713 | 1.101 | 0.01199 to 1.119 | 83.5 | no |
| knot[14]@3.2.0 | 2022-08-22 | iter0, direct | li | yes | no | 6.212 | 1.051 | -0.001787 to 1.055 | 88.2 | no |

| row | timing | observable | why not tested |
|---|---|---|---|
| knot[1]@2.0.0 | 2015-06-26 | alg8 | no test: no before-period in se, nu, gov, ee, ch, li |
| knot[2]@2.1.0 | 2016-01-14 | alg13 | no test: no before-period in se, nu, gov, ee, ch, li |
| knot[3]@2.2.0 | 2016-04-26 | rsa1024 | no test in any corpus: no before-period in se, nu, gov, ee, ch, li |
| knot[7]@2.6.0 | 2017-09-29 | alg3_6 | no test: the value is absent in every month of the window 2016-09..2018-08 in nu, panel; the value never appears in this series in gov, ee, li; no before-period in ch |
| knot[8]@2.7.0 | 2018-08-03 | rsa_lt1024 | no test: the value never appears in this series in ee; no before-period in ch, li |
| knot[10]@2.8.0 | 2019-03-05 | cds | no test: no before-period in ee, ch, li |
| knot[11]@2.8.0 | 2019-03-05 | digest1 | no test: the value never appears in this series in ee; no before-period in ch, li |
| knot[12]@3.0.2 | 2020-11-11 | alg5_7 | no test: no before-period in ch, li |
| knot[19]@3.6.0 | 2026-09-08 | iter_gt256 | no test in any corpus: no after-period in se, nu, ch; the value never appears in this series in gov, ee, li |

### kresd

Knot Resolver is a validator. Only its NSEC3 iteration caps map to an observable, and only indirectly: a
cap acts on zones by making those above it fail validation. Of 14 tests, 11 had coverage, over up to 59 releases.

**What beat chance:** nothing. No mean falls outside the null band and no test has an excess of release months outside
the single-release band.

**Default-change events:** kresd[9]@5.3.1, the cap of 150 in 2021-03, is tested in four TLDs and none is outside its band.
kresd[12] and kresd[15], the cap of 50 in 2024-02, have no after-period.

**Not testable:** every other kresd row is validation or trust-anchor behaviour, which zone data cannot show.

Question 1:

| observable | corpora tested | release months tested per corpus | null percentile of the mean, lowest to highest | tests outside the 90% null | tests where more release months fall outside the band than chance, p < 0.10 |
|---|---|---|---|---|---|
| iter_gt150 | se, nu, ee, ch, li | 50, 50, 27, 20, 20 | 16.1 to 50.0 | 0 of 5 | 0 of 5 |
| iter_gt50 | se, nu, gov, ee, ch, li | 50, 50, 44, 27, 20, 20 | 9.5 to 76.9 | 0 of 6 | 0 of 6 |

Not tested, besides fed.us: iter_gt150 in gov: the value is present in only 5 months of this series.

Question 2:

| row | timing | observable, relation | corpus | upgrade | opt-in | share before, % | d12, pp | 90% band | percentile | outside |
|---|---|---|---|---|---|---|---|---|---|---|
| kresd[9]@5.3.1 | 2021-03-31 | iter_gt150, indirect-validator-cap | se | yes | no | 0.000149 | 1e-06 | -7.4e-05 to 7e-06 | 78.8 | no |
| kresd[9]@5.3.1 | 2021-03-31 | iter_gt150, indirect-validator-cap | nu | yes | no | 0.001922 | 2e-06 | -9.5e-05 to 0.000151 | 58.5 | no |
| kresd[9]@5.3.1 | 2021-03-31 | iter_gt150, indirect-validator-cap | gov | yes | no | 0 | 0.03842 | -0.03842 to 0.03842 | 93.8 | no |
| kresd[9]@5.3.1 | 2021-03-31 | iter_gt150, indirect-validator-cap | ee | yes | no | 0.005272 | -0.000217 | -0.003322 to 0 | 28.4 | no |

| row | timing | observable | why not tested |
|---|---|---|---|
| kresd[9]@5.3.1 | 2021-03-31 | iter_gt150 | no test: no before-period in ch, li |
| kresd[12]@5.7.1 | 2024-02-13 | iter_gt50 | no test in any corpus: no after-period in se, nu, gov, ee, ch, li |
| kresd[15]@6.0.6 | 2024-02-13 | iter_gt50 | no test in any corpus: no after-period in se, nu, gov, ee, ch, li |

### nsd

NSD has 130 stable releases and seven default rows, all about how it serves or compiles DNSSEC. NSD serves what the
zone file holds and does not sign, so no row maps to a zone-data observable and nothing was tested. This is recorded in
the JSON as a program with no mapped observable, not as a null result.

### opendnssec

OpenDNSSEC has 65 stable releases in 52 release months, and four observables. Its releases thin out after
2016, so the forward corpus sees only 7 to 16 release months per TLD.

**What beat chance:** three of 26 means fall outside the 90% null band: algorithm 8 in .nu at the 2nd percentile, and in
.ch at the 4th, and algorithm 7 in .se at the 96th. About 2.6 would by chance. In .ch the test rests on 7 release months.
None of the share-outside tests is below 0.10.

**Default-change events:** opendnssec[13]@2.1.0, SHA-256 only in key export, 2017-02, is testable only on the panel. The
SHA-1 DS share was 68% and rose by 0.95 pp relative to trend, at the 91st percentile, against its expected direction.

**Not testable:** opendnssec[5]@1.2.0b1, the switch from algorithm 7 to 8 in 2011-03, predates the panel's first signed
month, 2011-05, and the forward corpus. opendnssec[3], the opt-out change of 2010-05, has no before-period anywhere.

Question 1:

| observable | corpora tested | release months tested per corpus | null percentile of the mean, lowest to highest | tests outside the 90% null | tests where more release months fall outside the band than chance, p < 0.10 |
|---|---|---|---|---|---|
| alg7 | se, nu, gov, ee, ch, li, panel | 16, 16, 11, 9, 7, 7, 45 | 10.1 to 95.5 | 1 of 7 | 0 of 7 |
| alg8 | se, nu, gov, ee, ch, li, panel | 16, 16, 11, 9, 7, 7, 45 | 2.0 to 87.3 | 2 of 7 | 0 of 7 |
| digest1 | se, nu, gov, ch, li, panel | 16, 16, 11, 7, 7, 45 | 5.4 to 73.4 | 0 of 6 | 0 of 6 |
| optout | se, nu, gov, ee, ch, li | 16, 16, 11, 9, 7, 7 | 12.7 to 90.8 | 0 of 6 | 0 of 6 |

Not tested, besides fed.us: digest1 in ee: the value never appears in this series.

Question 2:

| row | timing | observable, relation | corpus | upgrade | opt-in | share before, % | d12, pp | 90% band | percentile | outside |
|---|---|---|---|---|---|---|---|---|---|---|
| opendnssec[13]@2.1.0 | 2017-02-22 | digest1, direct | panel | yes | no | 68.2 | 0.9491 | -1.25 to 1.099 | 90.6 | no |

| row | timing | observable | why not tested |
|---|---|---|---|
| opendnssec[3]@1.1.0rc1 | 2010-05-26 | optout | no test in any corpus: no before-period in se, nu, gov, ee, ch, li |
| opendnssec[5]@1.2.0b1 | 2011-03-18 | alg8 | no test in any corpus: no before-period in se, nu, gov, ee, ch, li, panel, se, nu, gov, ee, ch, li, panel |
| opendnssec[13]@2.1.0 | 2017-02-22 | digest1 | no test: no before-period in se, nu, gov, ch, li; the value never appears in this series in ee |

### pdns-auth

PowerDNS Authoritative has 132 stable releases in 85 release months, and seven observables. pdns-auth[5] and
[6] are excluded upstream because their stable tag is null.

**What beat chance:** one mean of 37 is outside the null band: the share of NSEC3 names above 100 iterations in .nu, at
the 95th percentile, on shares near 0.002%. One share-outside test, opt-out in .gov, is at p = 0.082. Both are fewer than
the roughly 4 expected by chance.

**Default-change events:** pdns-auth[7] and [8]@4.0.0, the ECDSA default of 2016-07, have only one forward month
before them. On the panel the algorithm 13 share was 0.24% and moved by -0.017 pp, at the 16th to 19th percentile.
pdns-auth[0]@3.2, RSASHA256 in 2013-01, moves the panel algorithm 8 share by -0.44 pp, at the 31st percentile.
pdns-auth[10]@4.5.0, the authoritative clamp from 500 to 100 iterations, is in the expected direction in five TLDs and
outside its band in none. pdns-auth[11]@4.6.0, opt-in 0 iterations, is inside its band everywhere.

**Not testable:** pdns-auth[1], [3], [4] and [9] predate every corpus that records their observable. No forward TLD
ever had an NSEC3 name above 500 iterations with the denominator floor met, so the 500 clamp has no series.

Question 1:

| observable | corpora tested | release months tested per corpus | null percentile of the mean, lowest to highest | tests outside the 90% null | tests where more release months fall outside the band than chance, p < 0.10 |
|---|---|---|---|---|---|
| alg13 | se, nu, gov, ee, ch, li, panel | 32, 32, 29, 19, 17, 17, 65 | 17.0 to 84.1 | 0 of 7 | 0 of 7 |
| alg8 | se, nu, gov, ee, ch, li, panel | 32, 32, 29, 19, 17, 17, 65 | 25.3 to 85.2 | 0 of 7 | 0 of 7 |
| iter0 | se, nu, gov, ee, ch, li | 32, 32, 29, 19, 17, 17 | 14.8 to 72.6 | 0 of 6 | 0 of 6 |
| iter_gt100 | se, nu, ee, ch, li | 32, 32, 19, 17, 17 | 32.8 to 95.3 | 1 of 5 | 0 of 5 |
| optout | se, nu, gov, ee, ch, li | 32, 32, 29, 19, 17, 17 | 23.8 to 71.6 | 0 of 6 | 1 of 6 |
| rsa1024 | se, nu, gov, ee, ch, li | 32, 32, 29, 19, 17, 17 | 22.9 to 73.8 | 0 of 6 | 0 of 6 |

Not tested, besides fed.us: iter_gt100 in gov: the value is present in only 5 months of this series. iter_gt500 in se, nu, gov, ee, ch, li: the value is present in only 2 months of this series; the value is present in only 3 months of this series; the value never appears in this series.

Question 2:

| row | timing | observable, relation | corpus | upgrade | opt-in | share before, % | d12, pp | 90% band | percentile | outside |
|---|---|---|---|---|---|---|---|---|---|---|
| pdns-auth[0]@3.2 | 2013-01-17 | alg8, direct | panel | no | no | 27.48 | -0.4427 | -3.532 to 4.106 | 30.6 | no |
| pdns-auth[7]@4.0.0 | 2016-07-08 | alg13, direct | panel | no | no | 0.2418 | -0.01741 | -0.2508 to 0.3565 | 16.4 | no |
| pdns-auth[8]@4.0.0 | 2016-07-08 | alg13, direct | panel | no | no | 0.2418 | -0.01741 | -0.2541 to 0.3566 | 18.5 | no |
| pdns-auth[10]@4.5.0 | 2021-07-12 | iter_gt100, direct-auth-clamp | se | yes | no | 0.000744 | -0.000129 | -0.00017 to 0.000157 | 13.6 | no |
| pdns-auth[10]@4.5.0 | 2021-07-12 | iter_gt100, direct-auth-clamp | nu | yes | no | 0.001935 | -0.000186 | -0.000186 to 0.000181 | 5.6 | no |
| pdns-auth[10]@4.5.0 | 2021-07-12 | iter_gt100, direct-auth-clamp | gov | yes | no | 0 | 0.03842 | -0.03842 to 0.03842 | 92.2 | no |
| pdns-auth[10]@4.5.0 | 2021-07-12 | iter_gt100, direct-auth-clamp | ee | yes | no | 0 | -0.003223 | -0.004084 to 0.003436 | 13.2 | no |
| pdns-auth[10]@4.5.0 | 2021-07-12 | iter_gt100, direct-auth-clamp | ch | yes | no | 0.03599 | -0.0392 | -0.04037 to -1.6e-05 | 16.3 | no |
| pdns-auth[10]@4.5.0 | 2021-07-12 | iter_gt100, direct-auth-clamp | li | yes | no | 0 | -0.1052 | -0.1124 to 0 | 22.0 | no |
| pdns-auth[11]@4.6.0 | 2022-01-24 | iter0, direct | se | no | yes | 0.1939 | 0.02612 | -0.000439 to 0.3115 | 89.0 | no |
| pdns-auth[11]@4.6.0 | 2022-01-24 | iter0, direct | nu | no | yes | 6.383 | 3.1e-05 | -0.003244 to 0.3025 | 36.3 | no |
| pdns-auth[11]@4.6.0 | 2022-01-24 | iter0, direct | gov | no | yes | 0.1175 | -0.03619 | -0.05432 to 0.2266 | 7.4 | no |
| pdns-auth[11]@4.6.0 | 2022-01-24 | iter0, direct | ee | no | yes | 0.02446 | -3.8e-05 | -4e-05 to 0.01127 | 6.2 | no |
| pdns-auth[11]@4.6.0 | 2022-01-24 | iter0, direct | ch | no | yes | 0.6334 | 0.01274 | 0.01199 to 1.119 | 11.4 | no |
| pdns-auth[11]@4.6.0 | 2022-01-24 | iter0, direct | li | no | yes | 1.564 | 0.001285 | -0.008238 to 1.055 | 18.1 | no |

| row | timing | observable | why not tested |
|---|---|---|---|
| pdns-auth[0]@3.2 | 2013-01-17 | alg8 | no test: no before-period in se, nu, gov, ee, ch, li |
| pdns-auth[1]@3.3 | 2013-07-05 | optout | no test in any corpus: no before-period in se, nu, gov, ee, ch, li |
| pdns-auth[3]@3.4.0 | 2014-09-30 | iter_gt500 | no test in any corpus: no before-period in se, ch; the value never appears in this series in nu, gov, ee, li |
| pdns-auth[4]@3.4.7 | 2015-11-03 | iter_gt500 | no test in any corpus: no before-period in se, ch; the value never appears in this series in nu, gov, ee, li |
| pdns-auth[7]@4.0.0 | 2016-07-08 | alg13 | no test: no before-period in se, nu, gov, ee, ch, li |
| pdns-auth[8]@4.0.0 | 2016-07-08 | alg13 | no test: no before-period in se, nu, gov, ee, ch, li |
| pdns-auth[9]@4.0.0 | 2016-07-08 | rsa1024 | no test in any corpus: no before-period in se, nu, gov, ee, ch, li |

### pdns-rec

PowerDNS Recursor has 171 publicly released stable tags in 86 release months; rec-4.5.0, rec-4.5.3 and
rec-5.0.0 were tagged but never shipped and are excluded. Only its NSEC3 iteration caps map, indirectly.

**What beat chance:** nothing. None of 11 tests falls outside the null band.

**Default-change events:** nsec3-max-iterations-150, 2021-06, is inside its band in all six TLDs. It is at the 7th
percentile in .ch and the 6th in .li, the same .ch and .li movement that sits under bind9 l01 a month earlier.
nsec3-max-iterations-2500 has no series, because no forward name ever exceeds 2500 iterations. The cap of 50, public
2024-01, has no after-period.

**Not testable:** all validation, KeyTrap and trust-anchor rows.

Question 1:

| observable | corpora tested | release months tested per corpus | null percentile of the mean, lowest to highest | tests outside the 90% null | tests where more release months fall outside the band than chance, p < 0.10 |
|---|---|---|---|---|---|
| iter_gt150 | se, nu, ee, ch, li | 42, 42, 26, 21, 21 | 11.1 to 62.2 | 0 of 5 | 0 of 5 |
| iter_gt50 | se, nu, gov, ee, ch, li | 42, 42, 38, 26, 21, 21 | 25.2 to 70.9 | 0 of 6 | 0 of 6 |

Not tested, besides fed.us: iter_gt150 in gov: the value is present in only 5 months of this series. iter_gt2500 in se, nu, gov, ee, ch, li: the value never appears in this series.

Question 2:

| row | timing | observable, relation | corpus | upgrade | opt-in | share before, % | d12, pp | 90% band | percentile | outside |
|---|---|---|---|---|---|---|---|---|---|---|
| nsec3-max-iterations-150 | 2021-06-07 | iter_gt150, indirect-validator-cap | se | yes | no | 5e-05 | -0 | -7.4e-05 to 7e-06 | 47.5 | no |
| nsec3-max-iterations-150 | 2021-06-07 | iter_gt150, indirect-validator-cap | nu | yes | no | 0.001934 | -3e-06 | -9.5e-05 to 0.000148 | 48.5 | no |
| nsec3-max-iterations-150 | 2021-06-07 | iter_gt150, indirect-validator-cap | gov | yes | no | 0 | 0.03842 | -0.03842 to 0.03842 | 93.8 | no |
| nsec3-max-iterations-150 | 2021-06-07 | iter_gt150, indirect-validator-cap | ee | yes | no | 0.00158 | -1.3e-05 | -0.003322 to 0 | 38.0 | no |
| nsec3-max-iterations-150 | 2021-06-07 | iter_gt150, indirect-validator-cap | ch | yes | no | 0.03652 | -0.002389 | -0.002411 to 2.1e-05 | 7.4 | no |
| nsec3-max-iterations-150 | 2021-06-07 | iter_gt150, indirect-validator-cap | li | yes | no | 0.02303 | -0.007109 | -0.007109 to 0 | 6.4 | no |

| row | timing | observable | why not tested |
|---|---|---|---|
| nsec3-max-iterations-2500 | 2017-12-04 | iter_gt2500 | no test in any corpus: the value is absent in every month of the window 2016-12..2018-11 in se, nu; the value never appears in this series in gov, ee, ch, li |
| nsec3-max-iterations-50 | 2024-01-09 | iter_gt50 | no test in any corpus: no after-period in se, nu, gov, ee, ch, li |

### unbound

Unbound has 120 stable releases in 102 release months. As a validator, only its NSEC3 iteration caps map,
indirectly. Five tests had coverage.

**What beat chance:** two of five means fall outside the null band, in opposite directions: .ee at the 2nd percentile
and .ch at the 99th. The shares involved are below 0.01% of NSEC3 names, and two opposite-signed results in five are what
chance produces at this rate. The .ee share-outside test is at p = 0.013 on 19 release months.

**Default-change events:** unbound[20]@1.13.2, the cap of 150 in 2021-08, is inside its band in all six TLDs.
unbound[1]@0.5 shipped in 2007, before any corpus.

**Not testable:** the other 29 unbound rows, which are validation, trust-anchor and validator algorithm behaviour.

Question 1:

| observable | corpora tested | release months tested per corpus | null percentile of the mean, lowest to highest | tests outside the 90% null | tests where more release months fall outside the band than chance, p < 0.10 |
|---|---|---|---|---|---|
| iter_gt150 | se, nu, ee, ch, li | 37, 37, 19, 13, 13 | 2.1 to 99.3 | 2 of 5 | 1 of 5 |

Not tested, besides fed.us: iter_gt150 in gov: the value is present in only 5 months of this series.

Question 2:

| row | timing | observable, relation | corpus | upgrade | opt-in | share before, % | d12, pp | 90% band | percentile | outside |
|---|---|---|---|---|---|---|---|---|---|---|
| unbound[20]@1.13.2 | 2021-08-05 | iter_gt150, indirect-validator-cap | se | yes | no | 0 | 0 | -7.6e-05 to 8e-06 | 63.1 | no |
| unbound[20]@1.13.2 | 2021-08-05 | iter_gt150, indirect-validator-cap | nu | yes | no | 0.00194 | -1e-05 | -9.5e-05 to 0.000148 | 39.1 | no |
| unbound[20]@1.13.2 | 2021-08-05 | iter_gt150, indirect-validator-cap | gov | yes | no | 0.09436 | 0.02269 | -0.03842 to 0.03842 | 82.7 | no |
| unbound[20]@1.13.2 | 2021-08-05 | iter_gt150, indirect-validator-cap | ee | yes | no | 0 | 0 | -0.003322 to 0 | 68.4 | no |
| unbound[20]@1.13.2 | 2021-08-05 | iter_gt150, indirect-validator-cap | ch | yes | no | 0.002901 | -0.001634 | -0.002389 to 2.1e-05 | 14.8 | no |
| unbound[20]@1.13.2 | 2021-08-05 | iter_gt150, indirect-validator-cap | li | yes | no | 0 | -0.00611 | -0.007109 to 0 | 17.2 | no |

| row | timing | observable | why not tested |
|---|---|---|---|
| unbound[1]@0.5 | 2007-09-25 | iter_gt150 | no test in any corpus: no before-period in se, nu, gov, ee, ch, li |

## Question 3: manual against automatic, and at which level

The reverse ledger `delegation_change_clusters.parquet` groups every change into actions: one month, one RIR, one
block and one transition. The events are the signer default changes that name a target algorithm: bind9 d02 to
algorithm 5, knot[1], opendnssec[5] and pdns-auth[0] to 8, and knot[2], pdns-auth[7] and [8] and bind9 d15 to 13. The
window is the release month and the 3 months after. The matching transitions are new signings and rollovers to the
target algorithm.

Two statistics are compared between window months and all other months: the share of matching delegations that moved in
actions of 10 or more, and the share at level "one block" or "concentrated" in `delegation_change_levels.parquet`. The
null draws the same number of months at random from the ledger span, 1,000 times. Because ledger activity rises about
25-fold from 2009 to 2019, an era-matched version draws only from months within 36 months of the window.

Action size is a proxy. One operator automating one delegation is indistinguishable from a manual edit, and one operator
hand-editing a whole block is indistinguishable from an upgrade.

| group | scope | window | matching delegations, window / other | large-action share, difference | p | era-matched p | one-block-or-concentrated share, difference | p | era-matched p |
|---|---|---|---|---|---|---|---|---|---|
| d02-keygen-default-alg-rsasha1 | all RIRs | 2010-02..2010-05 | 60 / 1646 | -0.086 | 0.271 | 0.426 | -0.146 | 0.720 | 0.723 |
| d02-keygen-default-alg-rsasha1 | ripe | 2010-02..2010-05 | 60 / 754 | -0.099 | 0.211 | 0.345 | -0.050 | 0.540 | 0.541 |
| knot[1]@2.0.0 | all RIRs | 2015-06..2015-09 | 127 / 7501 | -0.169 | 0.362 | 0.575 | -0.109 | 0.646 | 0.744 |
| knot[1]@2.0.0 | apnic | 2015-06..2015-09 | 10 / 3139 | -0.800 | 0.924 | 0.870 | +0.871 | 0.102 | 0.105 |
| knot[1]@2.0.0 | arin | 2015-06..2015-09 | 17 / 2347 | -0.373 | 0.539 | 0.825 | +0.166 | 0.306 | 0.643 |
| knot[1]@2.0.0 | ripe | 2015-06..2015-09 | 98 / 997 | -0.002 | 0.187 | 0.325 | -0.501 | 0.589 | 0.681 |
| opendnssec[5]@1.2.0b1 | all RIRs | 2011-03..2011-06 | 30 / 7598 | -0.546 | 0.712 | 0.861 | -0.286 | 0.874 | 0.857 |
| opendnssec[5]@1.2.0b1 | ripe | 2011-03..2011-06 | 29 / 1066 | -0.505 | 0.941 | 0.862 | -0.482 | 0.611 | 0.607 |
| pdns-auth[0]@3.2 | all RIRs | 2013-01..2013-04 | 106 / 7522 | +0.061 | 0.192 | 0.261 | +0.658 | 0.015 | 0.026 |
| pdns-auth[0]@3.2 | arin | 2013-01..2013-04 | 17 / 2347 | -0.373 | 0.539 | 0.859 | +0.521 | 0.048 | 0.070 |
| pdns-auth[0]@3.2 | ripe | 2013-01..2013-04 | 89 / 1006 | +0.248 | 0.135 | 0.151 | +0.503 | 0.038 | 0.042 |
| d15-dnssec-policy-default-ecdsap256 | all RIRs | 2020-02..2020-05 | 99 / 8286 | -0.081 | 0.486 | 0.606 | -0.021 | 0.367 | 0.595 |
| d15-dnssec-policy-default-ecdsap256 | apnic | 2020-02..2020-05 | 7 / 843 | -0.387 | 0.508 | 0.476 | +0.278 | 0.460 | 0.413 |
| d15-dnssec-policy-default-ecdsap256 | arin | 2020-02..2020-05 | 83 / 4999 | -0.077 | 0.523 | 0.536 | -0.042 | 0.364 | 0.507 |
| d15-dnssec-policy-default-ecdsap256 | ripe | 2020-02..2020-05 | 9 / 601 | -0.256 | 0.605 | 0.565 | +0.013 | 0.531 | 0.579 |
| all default changes to algorithm 8 | all RIRs | 2015-06..2015-09, 2011-03..2011-06, 2013-01..2013-04 | 263 / 7365 | -0.122 | 0.510 | 0.645 | +0.183 | 0.254 | 0.461 |
| all default changes to algorithm 8 | apnic | 2015-06..2015-09, 2011-03..2011-06, 2013-01..2013-04 | 10 / 3139 | -0.800 | 0.826 | 0.794 | +0.871 | 0.117 | 0.091 |
| all default changes to algorithm 8 | arin | 2015-06..2015-09, 2011-03..2011-06, 2013-01..2013-04 | 35 / 2329 | -0.376 | 0.736 | 0.903 | +0.322 | 0.114 | 0.468 |
| all default changes to algorithm 8 | ripe | 2015-06..2015-09, 2011-03..2011-06, 2013-01..2013-04 | 216 / 879 | +0.034 | 0.264 | 0.377 | -0.099 | 0.565 | 0.539 |
| all default changes to algorithm 13 | all RIRs | 2016-01..2016-04, 2016-07..2016-10, 2016-07..2016-10, 2020-02..2020-05 | 101 / 8284 | -0.083 | 0.637 | 0.688 | -0.025 | 0.400 | 0.617 |
| all default changes to algorithm 13 | apnic | 2016-01..2016-04, 2016-07..2016-10, 2016-07..2016-10, 2020-02..2020-05 | 7 / 843 | -0.387 | 0.420 | 0.523 | +0.278 | 0.286 | 0.311 |
| all default changes to algorithm 13 | arin | 2016-01..2016-04, 2016-07..2016-10, 2016-07..2016-10, 2020-02..2020-05 | 84 / 4998 | -0.079 | 0.650 | 0.594 | -0.044 | 0.498 | 0.569 |
| all default changes to algorithm 13 | ripe | 2016-01..2016-04, 2016-07..2016-10, 2016-07..2016-10, 2020-02..2020-05 | 10 / 600 | -0.257 | 0.397 | 0.468 | -0.055 | 0.535 | 0.566 |

37 group and scope cells have no test. knot[2], pdns-auth[7] and pdns-auth[8] have no test at all: in the
months after the 2016 ECDSA defaults, no RIR shows 5 new signings or rollovers to algorithm 13. lacnic's ledger starts
2016-10 and afrinic's 2012-06, so the earlier windows are not covered there. The per-cell reasons are in the CSV.

**Result.** No large-action statistic passes, in any group or RIR. The share of matching delegations moved in actions
of 10 or more is lower in the window than in other months in 20 of 23 tested cells. One level statistic passes:
after pdns-auth[0]@3.2, released 2013-01-17, the share at one-block or concentrated level is 0.66 higher than in other
months, p = 0.015, era-matched p = 0.026, and the RIPE and ARIN cells agree. It is one action: RIPE block
216.151.in-addr.arpa signed 64 delegations with algorithm 8 in 2013-02. With 46 level and size p-values in the table,
two or three below 0.05 are expected by chance. The pdns-auth[0] result is best read as one operator acting in the
month after a release, which the data cannot tie to that release.

Pooled over all RIRs, the size distribution of matching delegations in the windows against other months:

| window group | 1 | 2-4 | 5-9 | 10-49 | 50-99 | 100+ |
|---|---|---|---|---|---|---|
| d02-keygen-default-alg-rsasha1, window | 11 | 13 | 5 | 31 | 0 | 0 |
| d02-keygen-default-alg-rsasha1, other months | 196 | 284 | 174 | 494 | 63 | 435 |
| knot[1]@2.0.0, window | 20 | 12 | 47 | 48 | 0 | 0 |
| knot[1]@2.0.0, other months | 812 | 1877 | 712 | 2415 | 500 | 1185 |
| opendnssec[5]@1.2.0b1, window | 12 | 10 | 8 | 0 | 0 | 0 |
| opendnssec[5]@1.2.0b1, other months | 820 | 1879 | 751 | 2463 | 500 | 1185 |
| pdns-auth[0]@3.2, window | 7 | 4 | 31 | 0 | 64 | 0 |
| pdns-auth[0]@3.2, other months | 825 | 1885 | 728 | 2463 | 436 | 1185 |
| d15-dnssec-policy-default-ecdsap256, window | 36 | 42 | 8 | 13 | 0 | 0 |
| d15-dnssec-policy-default-ecdsap256, other months | 1381 | 4423 | 726 | 1325 | 315 | 116 |
| all default changes to algorithm 8, window | 39 | 26 | 86 | 48 | 64 | 0 |
| all default changes to algorithm 8, other months | 793 | 1863 | 673 | 2415 | 436 | 1185 |
| all default changes to algorithm 13, window | 38 | 42 | 8 | 13 | 0 | 0 |
| all default changes to algorithm 13, other months | 1379 | 4423 | 726 | 1325 | 315 | 116 |

Per RIR counts are in the CSV under the same column names, and the level distributions under
`window_delegations_by_level:*` and `other_delegations_by_level:*`.

Recompute: `python scripts/software_vs_adoption.py --only q3 && python -c "import pandas as pd;d=pd.read_csv('out/analysis/software_vs_adoption_q3.csv');print(d[['group','scope','status','window_matching_delegations','diff_share_in_actions_ge_10','p_large_ge_observed','p_large_era_matched','diff_share_one_block_or_concentrated','p_block_ge_observed','p_block_era_matched','reason']].to_string())"`

## Question 4: adoption spikes, attributed or not

Spikes use `spikes()` from `scripts/program_rfc_cases.py`, imported rather than re-implemented, on the numerator counts
of each mapped observable: forward per TLD with a floor of 300 names, reverse per RIR with a floor of 30 delegations.
Both directions are scanned. A default change is relevant to a spike if it maps to the same observable with the same
expected direction; it is aligned if it falls 0 to 3 months before the spike starts. Lag 0 means the same calendar
month, which can include days before the release. The chance rate is the share of the series' months that have a
relevant default change 0 to 3 months before them. Each observable, corpus and direction is judged by the
Poisson-binomial tail of its aligned count, which assumes independent spikes; spikes in one TLD a few months apart are
not independent, so the p-values are if anything too small.

For every spike the JSON and CSV also give the nearest preceding verified release of each of the eight programs and
its lag. The brief records that 97% of corpus months contain some release, so that column is descriptive only.

The composition of a reverse spike comes from the ledger: new signings, rollovers or unsignings of the spike's
algorithm in the spike months. The ledger records only DS algorithms, so a digest spike has no composition. A forward
spike has only a bound, from the growth in signed zones, because the forward per-zone records are not in the repository.

248 spikes: 120 forward and 128 reverse. 14 have a relevant default change within 3 months before them, against 9.0 expected from the chance rates.

| observable | corpus | direction | spikes | aligned within 3 months | expected by chance | p, at least as many |
|---|---|---|---|---|---|---|
| alg13 | forward | + | 17 | 2 | 1.23 | 0.352 |
| alg13 | reverse | + | 13 | 0 | 0.74 | 1.000 |
| alg5 | forward | - | 2 | 0 | 0.09 | 1.000 |
| alg5 | reverse | - | 6 | 0 | 0.12 | 1.000 |
| alg5 | reverse | + | 10 | 1 | 0.20 | 0.186 |
| alg5_7 | forward | - | 4 | 0 | 0.23 | 1.000 |
| alg5_7 | reverse | - | 7 | 0 | 0.11 | 1.000 |
| alg7 | reverse | - | 6 | 0 | 0.06 | 1.000 |
| alg8 | reverse | + | 21 | 2 | 1.11 | 0.305 |
| digest1 | forward | - | 8 | 2 | 1.08 | 0.296 |
| digest1 | reverse | - | 7 | 1 | 0.57 | 0.450 |
| iter0 | forward | + | 13 | 6 | 2.07 | 0.009 |
| iter5 | forward | + | 6 | 0 | 0.44 | 1.000 |
| rsa1024 | forward | - | 9 | 0 | 0.80 | 1.000 |
| rsa_lt1024 | forward | - | 3 | 0 | 0.13 | 1.000 |

18 further observable, corpus and direction cells have 116 spikes between them and no
relevant default change anywhere near their series, so their chance and their alignment are both zero.

The aligned spikes:

| spike | observable, direction | corpus, source | months | change | nearest relevant default | lag, months | chance rate | composition |
|---|---|---|---|---|---|---|---|---|
| 1 | alg13 + | forward se | 2016-10 to 2016-11 | 17193 | pdns-auth pdns-auth[7]@4.0.0 2016-07-08 | 3 | 0.089 | mostly rollovers (bound); new signings at most 6445, rollovers at least 10748 |
| 6 | alg13 + | forward nu | 2016-10 to 2016-10 | 857 | pdns-auth pdns-auth[7]@4.0.0 2016-07-08 | 3 | 0.089 | mostly rollovers (bound); new signings at most 0, rollovers at least 857 |
| 43 | alg5 + | reverse ripe | 2010-04 to 2010-04 | 32 | bind9 d02-keygen-default-alg-rsasha1 2010-02-16 | 2 | 0.020 | mostly new signings; new signings 32, rollovers 0 |
| 127 | alg8 + | reverse ripe | 2013-02 to 2013-02 | 66 | pdns-auth pdns-auth[0]@3.2 2013-01-17 | 1 | 0.050 | mostly new signings; new signings 64, rollovers 0 |
| 130 | alg8 + | reverse ripe | 2015-08 to 2015-08 | 86 | knot knot[1]@2.0.0 2015-06-26 | 2 | 0.050 | mostly new signings; new signings 86, rollovers 0 |
| 145 | digest1 - | forward se | 2022-04 to 2022-04 | 314317 | bind9 d20-dnssec-cds-sha2-only 2022-01-24 | 3 | 0.178 | not determinable: forward per-zone records are not in the repository |
| 147 | digest1 - | forward nu | 2022-04 to 2022-04 | 48566 | bind9 d20-dnssec-cds-sha2-only 2022-01-24 | 3 | 0.178 | not determinable: forward per-zone records are not in the repository |
| 159 | digest1 - | reverse afrinic | 2022-01 to 2022-01 | 53 | bind9 d20-dnssec-cds-sha2-only 2022-01-24 | 0 | 0.080 | not determinable: the ledger records DS algorithms only |
| 190 | iter0 + | forward se | 2022-07 to 2022-08 | 41250 | bind9 d21-signzone-nsec3-iterations-0 2022-07-07 | 0 | 0.100 | not determinable: forward per-zone records are not in the repository |
| 193 | iter0 + | forward nu | 2022-08 to 2022-08 | 1723 | knot knot[14]@3.2.0 2022-08-22 | 0 | 0.100 | not determinable: forward per-zone records are not in the repository |
| 196 | iter0 + | forward ch | 2022-03 to 2022-03 | 20076 | bind9 d18-nsec3param-default-0-0 2022-01-24 | 2 | 0.209 | not determinable: forward per-zone records are not in the repository |
| 197 | iter0 + | forward ch | 2022-08 to 2022-08 | 7920 | knot knot[14]@3.2.0 2022-08-22 | 0 | 0.209 | not determinable: forward per-zone records are not in the repository |
| 198 | iter0 + | forward ch | 2022-11 to 2023-02 | 139874 | knot knot[14]@3.2.0 2022-08-22 | 3 | 0.209 | not determinable: forward per-zone records are not in the repository |
| 199 | iter0 + | forward li | 2022-03 to 2022-03 | 544 | bind9 d18-nsec3param-default-0-0 2022-01-24 | 2 | 0.209 | not determinable: forward per-zone records are not in the repository |

**What beats chance:** only zero-iteration NSEC3 in the forward corpus, 6 of 13 spikes aligned against 2.07 expected,
p = 0.009. The six are .se in 2022-07, .nu in 2022-08, .ch in 2022-03, 2022-08 and 2022-11, and .li in 2022-03. The
defaults they follow, bind9 d18 and pdns-auth[11] in 2022-01, bind9 d21 in 2022-07 and knot[14] in 2022-08, fall in the
eight months in which the IETF draft on NSEC3 parameters became RFC 9276, published 2022-08. The six spikes come from
two registry operators: .se and .nu share one, .ch and .li the other. The data cannot separate a signer default from the
guidance it implemented, and three of the six spikes are one .ch series. This is an alignment, not an attribution.

**What does not:** every algorithm, digest, key-size, opt-out and CDS observable. The .se ECDSA spike of 2016-10, three
months after PowerDNS 4.0.0, is at least 62% rollovers of already-signed zones by the signed-zone bound, and a rollover
is not what a new default produces. The three aligned reverse spikes, algorithm 5 in RIPE 2010-04 and algorithm 8 in RIPE
2013-02 and 2015-08, are new signings of 32 to 86 delegations each, with chance rates of 0.02 to 0.05 each; 2 of 21
algorithm 8 spikes aligned against 1.1 expected is p = 0.31. The largest spikes of all, .ch ECDSA in 2021-06 to 11 at
591,306 names and .se in 2019, have no relevant default change within a year.

Across the reverse spikes with a ledger composition, 66 are mostly new signings, 14 mostly unsignings, 8 mostly
rollovers away from the algorithm and 3 mostly rollovers to it.

Recompute: `python scripts/software_vs_adoption.py --only q4 && python -c "import pandas as pd;print(pd.read_csv('out/analysis/software_vs_adoption_q4_alignment.csv').to_string());d=pd.read_csv('out/analysis/software_vs_adoption_q4.csv');print(d[d.relevant_default_within_3m][['n','observable','direction','source','start','delta','nearest_relevant_default','lag_months','chance_relevant_default_within_3m','composition']].to_string())"`

## Question 5: successor RFC while the predecessor is still deploying

Pairs come from the checklist: RFC 8624's `obsoleted_by`, RFC 9904, and the `related_rfc_ids` of RFC 9276, 9905 and
9906. The brief adds RFC 8624 against the RSASHA1 algorithms and SHA-1 DS it deprecates, and SHA-1 DS against RFC 4509.
The share is the predecessor's deployment in the month the successor was published; the trajectory compares it with up
to 12 months later, fewer where the corpus ends. Rising or falling means a change of more than 10% relative. Peak is the
highest share in the covered series. This is descriptive and says nothing about cause.

| predecessor | successor, published | observable | corpus | share at successor, % | up to 12 months later, % | trajectory | peak, month | first month below half the peak | months from successor to that |
|---|---|---|---|---|---|---|---|---|---|
| RFC 5155 | RFC 9276, 2022-08 | iter_gt0 | se | 97.00 | 95.46, 2023-08 | flat | 100.00, 2021-02 | not by 2023-12 |  |
| RFC 5155 | RFC 9276, 2022-08 | iter_gt0 | nu | 92.17 | 90.33, 2023-08 | flat | 100.00, 2016-12 | not by 2023-12 |  |
| RFC 5155 | RFC 9276, 2022-08 | iter_gt0 | gov | 99.94 | 99.08, 2023-08 | flat | 100.01, 2017-11 | not by 2023-12 |  |
| RFC 5155 | RFC 9276, 2022-08 | iter_gt0 | ee | 99.88 | 99.82, 2023-08 | flat | 100.02, 2019-07 | not by 2023-12 |  |
| RFC 5155 | RFC 9276, 2022-08 | iter_gt0 | ch | 95.67 | 82.42, 2023-08 | fell | 99.98, 2020-07 | not by 2023-12 |  |
| RFC 5155 | RFC 9276, 2022-08 | iter_gt0 | li | 92.59 | 81.31, 2023-08 | fell | 100.00, 2020-05 | not by 2023-12 |  |
| RFC 3110 / RFC 4034 RSASHA1 signing | RFC 8624, 2019-06 | alg5_7 | se | 0.71 | 0.52, 2020-06 | fell | 0.97, 2016-12 | 2020-11 | 17 |
| RFC 3110 / RFC 4034 RSASHA1 signing | RFC 8624, 2019-06 | alg5_7 | nu | 5.42 | 5.22, 2020-06 | flat | 6.30, 2016-11 | 2021-08 | 26 |
| RFC 3110 / RFC 4034 RSASHA1 signing | RFC 8624, 2019-06 | alg5_7 | gov | 35.79 | 31.41, 2020-06 | fell | 44.74, 2017-05 | 2022-02 | 32 |
| RFC 3110 / RFC 4034 RSASHA1 signing | RFC 8624, 2019-06 | alg5_7 | panel | 31.21 | 33.76, 2020-06 | flat | 103.12, 2011-05 | 2014-05 | -61 |
| SHA-1 DS (RFC 4034 digest 1) | RFC 8624, 2019-06 | digest1 | se | 63.72 | 61.99, 2020-06 | flat | 65.49, 2017-10 | 2022-04 | 34 |
| SHA-1 DS (RFC 4034 digest 1) | RFC 8624, 2019-06 | digest1 | nu | 69.59 | 69.58, 2020-06 | flat | 93.10, 2017-05 | 2022-04 | 34 |
| SHA-1 DS (RFC 4034 digest 1) | RFC 8624, 2019-06 | digest1 | gov | 80.99 | 80.03, 2020-06 | flat | 93.91, 2017-12 | 2023-05 | 47 |
| SHA-1 DS (RFC 4034 digest 1) | RFC 8624, 2019-06 | digest1 | panel | 61.91 | 64.02, 2020-06 | flat | 100.00, 2011-05 | 2022-01 | 31 |
| RFC 8624 | RFC 9904, 2025-11 | alg8_13 | panel | 87.78 | 90.25, 2026-08 | flat | 90.25, 2026-08 | not by 2026-08 |  |
| RFC 3110 (RSA/SHA-1) | RFC 9905, 2025-11 | alg5_7 | panel | 9.81 | 7.98, 2026-08 | fell | 103.12, 2011-05 | 2014-05 | -138 |

Readings, without causal language:

- **RFC 5155 and RFC 9276.** When RFC 9276 was published in 2022-08, 92 to 99.9% of NSEC3 owner names in every forward
  TLD still used more than 0 iterations. Over the next 12 months the share stayed flat in .se, .nu, .gov and .ee and fell
  to about 82% in .ch and .li. It never fell below half its peak before the forward corpus ends in 2023-12. The reverse
  corpus cannot see NSEC3.
- **RSASHA1 and RFC 8624.** In 2019-06 the RSASHA1 family, algorithms 5 and 7, was 31% of panel signed delegations, 36%
  of .gov signed zones, 5.4% in .nu and 0.7% in .se. On the panel it had already fallen below half its 2011 peak in
  2014-05, 61 months earlier, and it was flat over the following year. In the forward TLDs it reached half its peak 17
  to 32 months after RFC 8624. By 2026-08 it is 8.0% of panel signed delegations.
- **SHA-1 DS and RFC 8624.** In 2019-06 SHA-1 DS was carried by 62% of panel DS-carrying delegations and by 64 to 81% in
  .se, .nu and .gov, flat over the next year in all four. It fell below half its peak 31 to 47 months after RFC 8624.
- **SHA-1 DS and RFC 4509.** RFC 4509 was published in 2006-05, five years before the first covered month of any corpus,
  so the share at publication cannot be determined. When coverage begins, SHA-1 DS is on 100% of panel DS-carrying
  delegations in 2011-05 and on 65 to 94% of forward DS-carrying delegations at their 2017 peaks.
- **RFC 8624 and RFC 9904.** Only the panel covers 2025-11. The RFC 8624 MUST algorithms, 8 and 13, were 87.8% of panel
  signed delegations then and 90.3% nine months later.
- **RFC 3110 and RFC 9905.** RSASHA1 was 9.8% of panel signed delegations at RFC 9905's publication and 8.0% nine
  months later.
- **RFC 5933 and RFC 9906.** Algorithm 12, GOST, never appears in any corpus, so there is nothing to deploy or retire.

Where the forward corpus starts after the successor, the row is "not covered at successor publication" in the CSV, with
the first covered month and the later peak.

Recompute: `python scripts/software_vs_adoption.py --only q5 && python -c "import pandas as pd;d=pd.read_csv('out/analysis/software_vs_adoption_q5.csv');print(d[['predecessor','successor','source','status','share_at_successor','share_after_up_to_12m','trajectory','peak','peak_month','first_below_half_peak_after_peak','months_from_successor_to_below_half','reason']].to_string())"`

## What could not be determined

- Any event before 2011-05 in the reverse corpus, and before 2016-06 in the forward corpus. That removes both ECDSA
  signing defaults of 2016 from the forward corpus, all four RSASHA256 signer defaults of 2011 to 2015 from the forward
  corpus, and bind9 d02, d03, opendnssec[3] and [5] and pdns-auth[1] from every corpus.
- Any event after 2023-12 in the forward corpus. That removes the NSEC3 caps of 50 in bind9, kresd and pdns-rec, and
  knot[19]; the reverse corpus cannot see NSEC3.
- Salt length, NSEC and NSEC3 TTLs, RRSIG timing and key-management state, because the monthly counts do not record them.
- All validation, trust-anchor and validator-limit behaviour, apart from the NSEC3 caps tested indirectly.
- The software that signed any zone. No zone record identifies its signer, so every alignment above is timing, not
  attribution.
- Whether a forward spike is new signings or rollovers beyond the bound, because the forward per-zone records are not in
  the repository, and the composition of any digest spike, because the ledger records algorithms only.
- The operator level above the reverse block. The ledger has no NS targets, so the DNS-provider level at which an
  automatic update would propagate cannot be seen.
- Reverse event timing to better than about a month, because of the one-month dating offset between the panel and the
  server run.

## Changed from the earlier analysis

- **Release dates.** The earlier documents used `data/software/release_dates.json`, including cvs2git artefacts such as
  BIND 9.3.0 to 9.3.4 on one day. This analysis uses only the verified `released` dates and drops never-public pdns-rec
  tags. The earlier per-project release scan counted 1,083 releases; the verified timelines have 1,325 stable public
  releases, and question 1 tests each program against its own schedule.
- **Seven default changes became 46 mapped rows.** The earlier analysis tested seven defaults, two usable. Of the 154
  verified rows, 46 map to an observable and 29 have at least one tested event. The conclusion is unchanged: no default
  change moves its observable outside the chance band more often than chance.
- **ECDSA defaults.** `docs/releases_vs_adoption.md` reported Knot 2.1.0 and PowerDNS 4.0.0 with slope changes of
  +0.034 and -0.043 on the panel. On the verified rows, with the detrended 12-month level change, knot[2] gives -0.019 pp
  and pdns-auth[7] and [8] give -0.017 pp, at the 15th and 16th to 19th percentiles. The earlier "neither shows an
  effect" stands.
- **BIND 9.16.0.** The earlier analysis discarded BIND 9.16.0's forward result as a ceiling artefact. Here bind9 d15 is
  tested as opt-in and not applied on upgrade, as the verified row records, and is inside its band in all four corpora.
- **The withdrawn OpenDNSSEC 1.2.0 result stays withdrawn.** opendnssec[5] is dated 2011-03-18, two months before the
  panel's first signed month, so it still has no test.
- **Release scan.** `docs/release_scan.md` found no project with a detrended release effect on ledger change counts, the
  smallest p being 0.11 for Knot. Question 1 here uses shares, not counts, and the verified schedules; it agrees. The
  earlier scan's claim that 97% of months contain a release is not re-derived here; question 4 reports the nearest
  release per program for description only.
- **Spike attribution.** `scripts/program_rfc_cases.py` scored spikes against unverified support and default rows from
  `data/software/software_support.json` and counted a spike as release-timed on lag alone. Here the relevant defaults
  are the verified rows mapped to the same observable and direction, and alignment is tested against each series'
  chance rate. The zero-iteration NSEC3 alignment is new, because the earlier cases tracked RFC 9276 through the
  disappearance of high iteration counts and had no signer-default rows for zero iterations.
- **Manual against automatic.** The earlier release scan gave the size distribution over all months and all
  transitions. Question 3 restricts it to transitions that match a signer default and tests the post-release months
  against the rest. Large actions are not more common after a default change; the one level result traces to one block.
- **Shares.** The earlier documents built forward shares from `domains_peak`. This analysis uses `domain_days`, because
  per-value peaks overshoot the total when zones change value within a month.
- **Reverse dating.** The earlier documents did not state that the panel and ledger are dated a month after the server
  run. This analysis states it and aligns the per-RIR counts to the ledger.
