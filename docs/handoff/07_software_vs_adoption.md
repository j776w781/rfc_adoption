# Phase 7: each program's update timeline against the adoption data

For an agent with no other context. This redoes `docs/releases_vs_adoption.md`, `docs/release_scan.md` and the case
studies in `scripts/program_rfc_cases.py` on the verified timelines of Phase 2 and 3 and on the Phase 4 normalised
default rows, as corrected after Phase 5. The specification is `docs/handoff/07_phase7_brief.md`. This is the revised
version, after the Phase 7 verification in `docs/handoff/verify/phase7_software_vs_adoption.md`; the section "What the
revision changed" lists every change with its old and new value.

Everything here comes from `scripts/software_vs_adoption.py`. It reads only the inputs the brief lists, uses seed
20260929 with 1,000 draws for every null, and writes `out/analysis/software_vs_adoption.json` with one key per question
plus `observable_mapping`, `excluded` and `notes`, and one long-form CSV per question,
`out/analysis/software_vs_adoption_<question>.csv`. Two full runs give a byte-identical JSON, and a run of a single
question with `--only` reproduces the same file. Tests: `python -m pytest tests/test_software_vs_adoption.py -q`.

Rebuild everything: `python scripts/software_vs_adoption.py`. It takes about half a minute.

## Short answer

The primary test now asks whether a share departs from its own pre-event trend after a release or a default change,
which a lasting level shift would do. By that test, release months and default changes are followed by departures
outside the 90% chance band about as often as chance predicts: 7 of 76 program-level tests against 7.6 expected, and
5 of 78 default-change events against 7.8, none with a Benjamini-Hochberg q below 0.8. The secondary test, which
detects only short-lived deviations and not lasting level shifts, also finds nothing beyond chance.

The strongest single results are the zero-iteration NSEC3 defaults of 2022 in .se: after bind9 d21 the 0-iteration
share departs from its pre-trend at the 97.5th percentile, and after knot[14] at the
99.1th. Among the 78 step tests, 4 are at
least as extreme as d21 against 5.1 expected, and
1 is at least as extreme as knot[14] against
2.8, so neither survives a multiple-testing view. The spike alignment
of question 4 points the same way and does beat its chance rate, but those defaults and RFC 9276 fall within the same
eight months, the IETF draft behind them was public by 2021-10 at the latest, and the four TLDs involved are run by
two registries; the operators of the changed zones cannot be identified. This is timing, not attribution.

The ledger test of question 3 no longer passes: with the window aligned to the calendar months after the release,
the block-level signing after PowerDNS 3.2 has p = 0.098, era-matched 0.21.

## How it was done

**Series.** A share is a percentage. Forward shares use the OpenINTEL TLD zone files per TLD. Reverse shares use only
the strict panel `_pooled-afrinic-arin`; per-RIR series are used only as counts, in question 4. Denominators are signed
zones, `algorithm_dnskey _total`, or DS-carrying delegations, `algorithm_ds _total` and `digest_type_ds _total`. NSEC3
iteration shares are over NSEC3 owner names, `nsec3_iterations _total`, and count names, not zones. A month with fewer
than 30 in the peak-day denominator is left out.

Shares are built from `domain_days`, which gives the month's mean daily share. `domains_peak` is not additive across
values: in .se in 2019-06, while zones moved from 1 to 5 NSEC3 iterations, the per-value peaks sum to 115% of the
`_total` peak. For the reverse corpus one snapshot is taken per month, so the two columns agree. Algorithm, digest and
key-size values are multi-valued per name, so a zone carrying two of them is counted in both, which is why a few summed
shares reach 100 to 127%.

**Dating.** Every reverse source, the server run, the panel run and the ledger, now shares one convention: label M is
the state at 00:00 UTC on the 1st of M. A reverse state difference or ledger change labelled M therefore happened during
calendar month M-1. For a release in calendar month r, reverse states up to label r are before it, after-states start
at label r+1, and ledger changes after it are labels r+1 on. Forward labels are the calendar month of measurement, and
a forward event's after-months start at r. No series is shifted; the event index is.

**Primary statistic, step12.** A line is fitted by least squares to the 24 months before the event and extrapolated
over the 12 months after; the statistic is the mean of actual minus extrapolated over those 12 months. A lasting level
shift at the event shows up in full. At least 16 of the 24 and 8 of the 12 months must be valid.

**Secondary statistic, transient.** The old statistic, kept and labelled as a transient-deviation test: the share
detrended by a centred 25-month rolling median, then the mean of the after-months minus the before-months, 3 and 3 in
question 1 and 12 and 12 in question 2. The rolling median follows a lasting step, so this test sees only deviations
that revert within about a year. The verifier showed that a synthetic step of 1, 5 or 10 pp leaves it unchanged.

**Nulls.** Question 2 draws 1,000 placebo event months from every eligible month of the same series. Question 1 takes
the program's release months that fall inside the series' own testable window and shifts them circularly by one
uniform offset within that window, 1,000 times. It needs a window of at least 24 months with release months filling at
most 75% of it; otherwise every shift covers nearly the same months. The 90% band means about one test in ten falls
outside it by chance.

**Calibration.** On 1000 synthetic series with no effect, a trend plus a random walk plus noise, the question 2
test rejects at 0.086 and the question 1 coverage-window shift at
0.120, against a nominal 0.10. The old whole-span shift rejects at
0.032 on the same data, which confirms the verifier's finding that it was
conservative. On the real schedules the mean p of the question 1 step tests is 0.46
and of the transient tests 0.53, against 0.63 for the old null.

## What the data says about the brief's coverage facts

Checked from the parquet files, recorded under `notes.coverage` in the JSON:

- The forward TLDs start as the brief says: se and nu 2016-06, gov and fed.us 2017-05, ee 2019-07, ch and li 2020-05.
  All end 2023-12 except fed.us, which ends 2022-10.
- fed.us never has a signed zone, so it has no share series at all. Every fed.us cell is "no test" for that reason,
  and the per-program text does not repeat it.
- The strict panel is `_pooled-afrinic-arin` in `out/panel_run`, with rows from 2009-04 and a signed-delegation series
  from label 2011-05, when it held 32 signed delegations.
- The server run's reverse rows were relabelled after the first version of this report, and now agree with the panel
  without any shift: all 168 afrinic and 181 arin compared months are equal, against 72 and 12 with a one-month shift.
  The script no longer shifts the per-RIR counts.
- `nsec3_salt_empty` holds only the value `present`, equal to `_total` in all 404 forward source-months, so salt length
  is not observable.

Recompute: `python scripts/software_vs_adoption.py --only q4 && python -c "import json;d=json.load(open('out/analysis/software_vs_adoption.json'));print(json.dumps(d['notes']['coverage'],indent=1));print(d['q4_spikes']['reverse_dating_check']);print(d['notes']['calibration'])"`

## Observable mapping

46 of the 154 normalised rows map to an observable; the other 108 are listed with a reason under
`excluded.rows_not_observable`. The mapping is by mechanism and before and after text, row by row, in `ROW_MAP` in the
script, and the test file pins it. The mapping did not change in this revision.

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

Unmapped rows by reason: 69 are validator-side behaviour, meaning validation, trust anchors, validator algorithm
support, DS-digest handling, caching and limits other than the NSEC3 caps; 16 are signature timing or serving options;
8 are NSEC3 serving details, salt or TTLs; 5 are key-management state; 4 are OpenDNSSEC enforcer settings with no
zone-data trace; 5 are not default changes; and 1 is an NSD compile default.

Recompute: `python scripts/software_vs_adoption.py --only q1 && python -c "import pandas as pd;print(pd.read_csv('out/analysis/software_vs_adoption_mapping.csv')[['program','row_id','observable','expected_direction','relation']].to_string());print(pd.read_csv('out/analysis/software_vs_adoption_excluded.csv').reason.value_counts())"`

## Per program: questions 1 and 2

Every forward result below measures a handful of DNS operators. Earlier work found every forward adoption jump
belonged to one of two registries' TLD pairs, and the counts cannot say which DNS operators ran the zones that changed,
so a forward event study measures whether a small number of organisations moved, not whether a market responded.

Question 1 totals. Step test: 76 tested of 289;
7 means fall outside the 90% null band against
7.6 expected, and 4 tests
have an excess of release months outside the single-release band. Transient test: 126 tested;
8 outside against 12.6
expected, and 3 excess-outside tests. Most untested cells lack
a testable window of 24 months or have release months in more than 75% of it.

Question 2 totals. Step test: 78 tested events, 5 outside the
band against 7.8 expected, 4 of
them in the expected direction; no Benjamini-Hochberg q is below 0.10. Transient test: 103
tested, 2 outside against 10.3.
The step test needs 24 months before the event, so it covers fewer events than the transient test.

Split of the step test by upgrade path:

| applies on upgrade, opt-in | tested | outside the 90% band | outside and in the expected direction | expected by chance |
|---|---|---|---|---|
| True, False | 56 | 4 | 4 | 5.6 |
| False, True | 14 | 0 | 0 | 1.4 |
| True, True | 4 | 0 | 0 | 0.4 |
| False, False | 4 | 1 | 0 | 0.4 |

Rows that apply on upgrade and are not opt-in, the ones an automatic update could carry, have 4 of 56 events outside
the band, all in the expected direction, against 5.6 expected by chance. The other groups have 1 of 22. No group
shows a lasting departure from trend more often than chance.

In each program's first table, question 1: "null percentile of the mean" is where the mean statistic over the
program's release months sits among 1,000 circular shifts within the series' testable window. The second table is
question 2, step and transient side by side for each default row and corpus.

Recompute question 1: `python scripts/software_vs_adoption.py --only q1 && python -c "import pandas as pd;d=pd.read_csv('out/analysis/software_vs_adoption_q1.csv');print(d[d.status=='tested'][['test','program','observable','source','null_window','release_months_tested','observed_mean','percentile','p_two_sided','share_release_months_outside_band','null_mean_share_outside','p_share_outside_ge_observed']].to_string())"`

Recompute question 2: `python scripts/software_vs_adoption.py --only q2 && python -c "import pandas as pd;d=pd.read_csv('out/analysis/software_vs_adoption_q2.csv');print(d[['test','program','row_id','observable','source','status','before_labels','after_labels','observed','band_lo','band_hi','percentile','bh_q','outside_90_band','reason']].to_string())"`

### bind9

BIND 9 has 444 stable releases in 190 release months, and twelve observables.

**Question 1:** no program-level test. BIND ships in nearly every month, so its release months fill more than 75% of
every testable window. A circular shift of such a schedule covers almost the same months as the real one, and the test
has no contrast. The old whole-span test reported 0 of 58 outside; it was conservative, and it is withdrawn.

**Question 2, step test:** 38 tests in 12 rows. Two fall outside the 90% band, both in the expected direction. d21, the
signzone default of 0 NSEC3 iterations in 2022-07, is followed in .se by a departure of +2.64 pp from the pre-trend of
the 0-iteration share, at the 97.6th percentile. In the other TLDs the same row sits at the 10th to 92nd percentile,
and in .nu it goes the other way. l01, the validator cap of 150, is followed by a fall in .se of NSEC3 names above 150,
at the 1st percentile, on a share near 0.0002%. d15, the opt-in ECDSA policy of 2020-02, departs from trend at the 17th,
21st, 52nd and 8th percentiles in .se, .nu, .gov and the panel: no lasting shift toward algorithm 13 beyond the trend.
d20, SHA-2-only CDS handling in 2022-01, is followed by SHA-1 DS shares 32 pp below trend in .se and 28 pp in .nu,
which includes the single-month SHA-1 DS drop in both TLDs in 2022-04, at the 7th and 6th percentiles: large, in the expected
direction, and still inside the band of those volatile series. The transient test puts one bind9 event outside its
band, d08 in .se, against the expected direction on a share of 0.00007%.

**Not testable:** d02 and d03 shipped in 2010-02, before any corpus. d09's algorithm 12 never appears. l02 has no
after-period. d08 and d10 are tested only in .se and .nu, the corpora where RSAMD5 and DSA
appear at all.

Question 1 counts. step12: 0 tested, 0 means outside the null band, 0 excess-outside tests; not tested besides fed.us: 31 because release months fill more than 75% of the testable window, 27 because the testable window is shorter than 24 months, 17 because the value never appears, 3 because the value is present in fewer than 12 months. transient3: 0 tested, 0 means outside the null band, 0 excess-outside tests; not tested besides fed.us: 58 because release months fill more than 75% of the testable window, 17 because the value never appears, 3 because the value is present in fewer than 12 months.

Question 2:

| row | timing | observable | corpus | upgrade, opt-in | step12, pp | percentile | outside | transient12, pp | percentile | outside |
|---|---|---|---|---|---|---|---|---|---|---|
| d06-keygen-no-default-alg | 2018-01-17 | alg5 | se | yes, no | no test | |  | -0.01809 | 11.6 | no |
| d06-keygen-no-default-alg | 2018-01-17 | alg5 | nu | yes, no | no test | |  | -0.006195 | 24.8 | no |
| d06-keygen-no-default-alg | 2018-01-17 | alg5 | panel | yes, no | 3.436 | 85.3 | no | -1.293 | 11.1 | no |
| d08-rsamd5-removed | 2019-03-20 | alg1 | se | yes, no | -2.3e-05 | 17.7 | no | 1.2e-05 | 97.9 | yes |
| d08-rsamd5-removed | 2019-03-20 | alg1 | nu | yes, no | 0.000252 | 87.4 | no | no test | |  |
| d10-dsa-removed | 2019-03-20 | alg3_6 | se | yes, no | 4.6e-05 | 59.2 | no | 2e-06 | 84.8 | no |
| d13-ds-cds-sha1-dropped | 2020-02-12 | digest1 | se | yes, no | -6.835 | 26.1 | no | -1.056 | 20.5 | no |
| d13-ds-cds-sha1-dropped | 2020-02-12 | digest1 | nu | yes, no | -9.841 | 29.6 | no | -0.2549 | 29.6 | no |
| d13-ds-cds-sha1-dropped | 2020-02-12 | digest1 | gov | yes, no | 2.424 | 79.2 | no | 0.206 | 79.8 | no |
| d13-ds-cds-sha1-dropped | 2020-02-12 | digest1 | panel | yes, no | 2.602 | 73.7 | no | 0.3907 | 77.5 | no |
| d14-keygen-rsa-zsk-2048 | 2020-02-12 | rsa1024 | se | yes, no | -7.348 | 29.6 | no | -0.1488 | 36.9 | no |
| d14-keygen-rsa-zsk-2048 | 2020-02-12 | rsa1024 | nu | yes, no | -0.1058 | 40.2 | no | -0.4124 | 28.1 | no |
| d14-keygen-rsa-zsk-2048 | 2020-02-12 | rsa1024 | gov | yes, no | 0.01582 | 64.7 | no | 0.4448 | 82.8 | no |
| d15-dnssec-policy-default-ecdsap256 | 2020-02-12 | alg13 | se | no, yes | -19.75 | 17.1 | no | -1.293 | 12.5 | no |
| d15-dnssec-policy-default-ecdsap256 | 2020-02-12 | alg13 | nu | no, yes | -8.069 | 21.4 | no | -0.1606 | 17.5 | no |
| d15-dnssec-policy-default-ecdsap256 | 2020-02-12 | alg13 | gov | no, yes | 2.398 | 52.4 | no | 0.1485 | 55.9 | no |
| d15-dnssec-policy-default-ecdsap256 | 2020-02-12 | alg13 | panel | no, yes | -4.215 | 7.5 | no | -0.01451 | 17.8 | no |
| d16-dnssec-policy-default-key-size-2048 | 2020-02-12 | rsa1024 | se | no, yes | -7.348 | 28.2 | no | -0.1488 | 38.7 | no |
| d16-dnssec-policy-default-key-size-2048 | 2020-02-12 | rsa1024 | nu | no, yes | -0.1058 | 37.5 | no | -0.4124 | 28.1 | no |
| d16-dnssec-policy-default-key-size-2048 | 2020-02-12 | rsa1024 | gov | no, yes | 0.01582 | 62.0 | no | 0.4448 | 82.7 | no |
| d17-nsec3param-default-in-policy | 2020-12-07 | iter5 | se | no, yes | -25.33 | 11.4 | no | -0.8238 | 8.2 | no |
| d17-nsec3param-default-in-policy | 2020-12-07 | iter5 | nu | no, yes | -4.189 | 11.7 | no | 0 | 36.9 | no |
| d17-nsec3param-default-in-policy | 2020-12-07 | iter5 | gov | no, yes | -0.1774 | 36.5 | no | -0.000803 | 43.5 | no |
| d17-nsec3param-default-in-policy | 2020-12-07 | iter5 | ee | no, yes | no test | |  | -0.4991 | 6.8 | no |
| d18-nsec3param-default-0-0 | 2022-01-24 | iter0 | se | yes, yes | 1.495 | 83.5 | no | 0.02612 | 86.3 | no |
| d18-nsec3param-default-0-0 | 2022-01-24 | iter0 | nu | yes, yes | 2.793 | 82.0 | no | 3.1e-05 | 36.4 | no |
| d18-nsec3param-default-0-0 | 2022-01-24 | iter0 | gov | yes, yes | 0.06069 | 70.6 | no | -0.03619 | 8.1 | no |
| d18-nsec3param-default-0-0 | 2022-01-24 | iter0 | ee | yes, yes | 0.05147 | 47.4 | no | -3.8e-05 | 4.0 | no |
| d18-nsec3param-default-0-0 | 2022-01-24 | iter0 | ch | yes, yes | no test | |  | 0.01274 | 11.9 | no |
| d18-nsec3param-default-0-0 | 2022-01-24 | iter0 | li | yes, yes | no test | |  | 0.001285 | 17.4 | no |
| d20-dnssec-cds-sha2-only | 2022-01-24 | digest1 | se | yes, no | -32.41 | 6.8 | no | 0 | 71.2 | no |
| d20-dnssec-cds-sha2-only | 2022-01-24 | digest1 | nu | yes, no | -28.42 | 6.2 | no | 0.1378 | 73.8 | no |
| d20-dnssec-cds-sha2-only | 2022-01-24 | digest1 | gov | yes, no | -1.949 | 61.0 | no | -0.06854 | 74.3 | no |
| d20-dnssec-cds-sha2-only | 2022-01-24 | digest1 | ch | yes, no | no test | |  | 0.3049 | 87.0 | no |
| d20-dnssec-cds-sha2-only | 2022-01-24 | digest1 | li | yes, no | no test | |  | 1.405 | 86.1 | no |
| d20-dnssec-cds-sha2-only | 2022-01-24 | digest1 | panel | yes, no | -5.571 | 11.6 | no | -0.7376 | 12.2 | no |
| d21-signzone-nsec3-iterations-0 | 2022-07-07 | iter0 | se | yes, no | 2.64 | 97.5 | yes | 0.03992 | 90.1 | no |
| d21-signzone-nsec3-iterations-0 | 2022-07-07 | iter0 | nu | yes, no | -1.099 | 9.7 | no | 0.1068 | 89.5 | no |
| d21-signzone-nsec3-iterations-0 | 2022-07-07 | iter0 | gov | yes, no | 0.3403 | 87.1 | no | 0.08094 | 89.1 | no |
| d21-signzone-nsec3-iterations-0 | 2022-07-07 | iter0 | ee | yes, no | 0.099 | 91.8 | no | 0.00717 | 86.0 | no |
| d21-signzone-nsec3-iterations-0 | 2022-07-07 | iter0 | ch | yes, no | 8.282 | 25.4 | no | 1.014 | 71.0 | no |
| d21-signzone-nsec3-iterations-0 | 2022-07-07 | iter0 | li | yes, no | 8.095 | 72.2 | no | 1.014 | 70.2 | no |
| l01-nsec3-max-iterations-150 | 2021-05-12 | iter_gt150 | se | yes, no | -0.000138 | 1.1 | yes | 0 | 63.4 | no |
| l01-nsec3-max-iterations-150 | 2021-05-12 | iter_gt150 | nu | yes, no | -0.000434 | 36.0 | no | -1e-06 | 49.4 | no |
| l01-nsec3-max-iterations-150 | 2021-05-12 | iter_gt150 | gov | yes, no | 0.03842 | 91.7 | no | 0.03842 | 93.5 | no |
| l01-nsec3-max-iterations-150 | 2021-05-12 | iter_gt150 | ee | yes, no | no test | |  | -4.7e-05 | 34.1 | no |
| l01-nsec3-max-iterations-150 | 2021-05-12 | iter_gt150 | ch | yes, no | no test | |  | -0.00282 | 2.9 | no |
| l01-nsec3-max-iterations-150 | 2021-05-12 | iter_gt150 | li | yes, no | no test | |  | -0.007297 | 2.9 | no |

Where the step test could not run, besides fed.us:

| row | timing | observable | why not tested |
|---|---|---|---|
| d02-keygen-default-alg-rsasha1 | 2010-02-16 | alg5 | no step test in any corpus: no before-period in se, nu, gov, ee, ch, li, panel |
| d03-signzone-nsec3-iterations-100-to-10 | 2010-02-16 | iter10 | no step test in any corpus: no before-period in se, nu, gov, ee, ch, li |
| d06-keygen-no-default-alg | 2018-01-17 | alg5 | no step test: no before-period in se, nu, gov, ee, ch, li |
| d08-rsamd5-removed | 2019-03-20 | alg1 | no step test: the value never appears in this series in gov, ch, li; no before-period in ee; the value is absent in every month of the window 2017-04..2020-03 in panel |
| d09-gost-removed | 2019-03-20 | alg12 | no step test in any corpus: the value is absent in every month of the window 2017-03..2020-02 in se, nu; the value never appears in this series in gov, ee, ch, li; the value is absent in every month of the window 2017-04..2020-03 in panel |
| d10-dsa-removed | 2019-03-20 | alg3_6 | no step test: the value is absent in every month of the window 2017-03..2020-02 in nu; the value never appears in this series in gov, ee, li; no before-period in ch; the value is absent in every month of the window 2017-04..2020-03 in panel |
| d13-ds-cds-sha1-dropped | 2020-02-12 | digest1 | no step test: the value never appears in this series in ee; no before-period in ch, li |
| d14-keygen-rsa-zsk-2048 | 2020-02-12 | rsa1024 | no step test: no before-period in ee, ch, li |
| d15-dnssec-policy-default-ecdsap256 | 2020-02-12 | alg13 | no step test: no before-period in ee, ch, li |
| d16-dnssec-policy-default-key-size-2048 | 2020-02-12 | rsa1024 | no step test: no before-period in ee, ch, li |
| d17-nsec3param-default-in-policy | 2020-12-07 | iter5 | no step test: no before-period in ee, ch, li |
| d18-nsec3param-default-0-0 | 2022-01-24 | iter0 | no step test: no before-period in ch, li |
| d20-dnssec-cds-sha2-only | 2022-01-24 | digest1 | no step test: the value is absent in every month of the window 2020-01..2022-12 in ee; no before-period in ch, li |
| l01-nsec3-max-iterations-150 | 2021-05-12 | iter_gt150 | no step test: no before-period in ee, ch, li |
| l02-nsec3-max-iterations-50 | 2024-07-08 | iter_gt50 | no step test in any corpus: no after-period in se, nu, gov, ee, ch, li |

### knot

Knot DNS has 174 stable releases in 126 release months, and ten observables.

**Question 1, step test:** 30 tests. Two means fall outside the null band, the RSASHA1 family in .nu at p = 0.042 and
SHA-1 DS on the panel at p = 0.066; one test has an excess of release months outside the band, RSA under 1024 bits in
.gov. Three of 30 is what chance gives.

**Question 2, step test:** knot[14]@3.2.0, iterations 10 to 0 in 2022-08, is followed by a departure of +2.88 pp in
.se, at the 99.1st percentile, and of +0.10 pp in .ee, at the 97.6th; .li is at 95.6, .gov at 89.9, .ch at 41 and .nu
at 10. knot[1]@2.0.0, the RSASHA256 default of 2015-06, is followed by a panel algorithm 8 share 17 pp below its
pre-trend, at the 2nd percentile, against the expected direction. knot[2]@2.1.0, the ECDSA default of 2016-01, is at
the 63rd percentile on the panel: its algorithm 13 share averaged 0.34% in the year after against 0.02% in the two
years before, but no more than its pre-trend predicts.

**Not testable:** knot[3] and knot[7] lack a 24-month before-period in any corpus that records their value, and
knot[19] shipped after both corpora end for NSEC3.

Question 1 counts. step12: 30 tested, 2 means outside the null band, 1 excess-outside tests; not tested besides fed.us: 24 because the testable window is shorter than 24 months, 10 because the value never appears, 1 because the value is present in fewer than 12 months. transient3: 36 tested, 2 means outside the null band, 0 excess-outside tests; not tested besides fed.us: 18 because release months fill more than 75% of the testable window, 10 because the value never appears, 1 because the value is present in fewer than 12 months.

| statistic | observable | corpora tested | release months tested per corpus | null percentile of the mean, lowest to highest | means outside the 90% null | tests where more release months fall outside the band than chance, p < 0.10 |
|---|---|---|---|---|---|---|
| step12 | alg13 | se, nu, gov, panel | 39, 39, 32, 102 | 27.0 to 66.1 | 0 of 4 | 0 of 4 |
| step12 | alg3_6 | se | 39 | 66.3 to 66.3 | 0 of 1 | 0 of 1 |
| step12 | alg5_7 | se, nu, gov, panel | 39, 39, 32, 102 | 2.1 to 52.0 | 1 of 4 | 0 of 4 |
| step12 | alg8 | se, nu, gov, panel | 39, 39, 32, 102 | 41.9 to 75.9 | 0 of 4 | 0 of 4 |
| step12 | cds | se, nu, gov | 39, 39, 32 | 6.1 to 89.9 | 0 of 3 | 0 of 3 |
| step12 | digest1 | se, nu, gov, panel | 39, 39, 32, 102 | 3.3 to 51.2 | 1 of 4 | 0 of 4 |
| step12 | iter0 | se, nu, gov | 39, 39, 32 | 16.2 to 93.3 | 0 of 3 | 0 of 3 |
| step12 | iter_gt256 | nu | 39 | 69.6 to 69.6 | 0 of 1 | 0 of 1 |
| step12 | rsa1024 | se, nu, gov | 39, 39, 32 | 48.8 to 67.6 | 0 of 3 | 0 of 3 |
| step12 | rsa_lt1024 | se, nu, gov | 39, 39, 32 | 43.8 to 83.8 | 0 of 3 | 1 of 3 |
| transient3 | alg13 | se, nu, gov, ee, panel | 62, 62, 53, 36, 120 | 23.6 to 97.7 | 1 of 5 | 0 of 5 |
| transient3 | alg3_6 | se | 62 | 37.6 to 37.6 | 0 of 1 | 0 of 1 |
| transient3 | alg5_7 | se, nu, gov, ee, panel | 62, 62, 53, 36, 120 | 32.5 to 53.7 | 0 of 5 | 0 of 5 |
| transient3 | alg8 | se, nu, gov, ee, panel | 62, 62, 53, 36, 120 | 2.9 to 57.2 | 1 of 5 | 0 of 5 |
| transient3 | cds | se, nu, gov, ee | 62, 62, 53, 36 | 42.2 to 73.2 | 0 of 4 | 0 of 4 |
| transient3 | digest1 | se, nu, gov, panel | 62, 62, 53, 120 | 36.6 to 85.3 | 0 of 4 | 0 of 4 |
| transient3 | iter0 | se, nu, gov, ee | 62, 62, 53, 36 | 16.8 to 75.0 | 0 of 4 | 0 of 4 |
| transient3 | iter_gt256 | nu | 62 | 22.4 to 22.4 | 0 of 1 | 0 of 1 |
| transient3 | rsa1024 | se, nu, gov, ee | 62, 62, 53, 36 | 39.0 to 70.8 | 0 of 4 | 0 of 4 |
| transient3 | rsa_lt1024 | se, nu, gov | 62, 62, 53 | 31.1 to 40.1 | 0 of 3 | 0 of 3 |

Question 2:

| row | timing | observable | corpus | upgrade, opt-in | step12, pp | percentile | outside | transient12, pp | percentile | outside |
|---|---|---|---|---|---|---|---|---|---|---|
| knot[1]@2.0.0 | 2015-06-26 | alg8 | panel | no, no | -17.23 | 1.9 | yes | -2.935 | 7.5 | no |
| knot[2]@2.1.0 | 2016-01-14 | alg13 | panel | no, no | 0.2286 | 63.5 | no | -0.0215 | 14.1 | no |
| knot[7]@2.6.0 | 2017-09-29 | alg3_6 | se | yes, no | no test | |  | -6.6e-05 | 4.8 | no |
| knot[8]@2.7.0 | 2018-08-03 | rsa_lt1024 | se | yes, no | 0.05684 | 71.7 | no | 0.005362 | 71.8 | no |
| knot[8]@2.7.0 | 2018-08-03 | rsa_lt1024 | nu | yes, no | -1.738 | 4.2 | no | -0.8093 | 12.2 | no |
| knot[8]@2.7.0 | 2018-08-03 | rsa_lt1024 | gov | yes, no | no test | |  | -0.06803 | 5.2 | no |
| knot[10]@2.8.0 | 2019-03-05 | cds | se | yes, no | 0.01539 | 50.8 | no | -0.00094 | 4.5 | yes |
| knot[10]@2.8.0 | 2019-03-05 | cds | nu | yes, no | 0.09048 | 60.2 | no | 0 | 34.6 | no |
| knot[10]@2.8.0 | 2019-03-05 | cds | gov | yes, no | no test | |  | 0.3113 | 70.8 | no |
| knot[11]@2.8.0 | 2019-03-05 | digest1 | se | yes, no | 10.73 | 90.5 | no | 3.014 | 93.5 | no |
| knot[11]@2.8.0 | 2019-03-05 | digest1 | nu | yes, no | 26.17 | 89.2 | no | 8.916 | 92.8 | no |
| knot[11]@2.8.0 | 2019-03-05 | digest1 | gov | yes, no | no test | |  | 0.5016 | 84.2 | no |
| knot[11]@2.8.0 | 2019-03-05 | digest1 | panel | yes, no | -4.438 | 23.2 | no | -0.578 | 17.0 | no |
| knot[12]@3.0.2 | 2020-11-11 | alg5_7 | se | yes, no | 0.02258 | 57.5 | no | -0.000206 | 55.1 | no |
| knot[12]@3.0.2 | 2020-11-11 | alg5_7 | nu | yes, no | -1.138 | 22.7 | no | -0.013 | 42.9 | no |
| knot[12]@3.0.2 | 2020-11-11 | alg5_7 | gov | yes, no | -0.09397 | 64.8 | no | 0.0124 | 91.2 | no |
| knot[12]@3.0.2 | 2020-11-11 | alg5_7 | ee | yes, no | no test | |  | -0.1161 | 14.8 | no |
| knot[12]@3.0.2 | 2020-11-11 | alg5_7 | panel | yes, no | 7.319 | 83.3 | no | 0.8648 | 76.3 | no |
| knot[14]@3.2.0 | 2022-08-22 | iter0 | se | yes, no | 2.88 | 99.1 | yes | 0.139 | 92.2 | no |
| knot[14]@3.2.0 | 2022-08-22 | iter0 | nu | yes, no | -1.396 | 9.9 | no | 0.1703 | 90.2 | no |
| knot[14]@3.2.0 | 2022-08-22 | iter0 | gov | yes, no | 0.4177 | 89.9 | no | 0.1338 | 91.6 | no |
| knot[14]@3.2.0 | 2022-08-22 | iter0 | ee | yes, no | 0.1026 | 97.5 | yes | 0.007178 | 90.6 | no |
| knot[14]@3.2.0 | 2022-08-22 | iter0 | ch | yes, no | 8.901 | 41.2 | no | 1.101 | 85.0 | no |
| knot[14]@3.2.0 | 2022-08-22 | iter0 | li | yes, no | 8.269 | 95.5 | no | 1.051 | 88.5 | no |

Where the step test could not run, besides fed.us:

| row | timing | observable | why not tested |
|---|---|---|---|
| knot[1]@2.0.0 | 2015-06-26 | alg8 | no step test: no before-period in se, nu, gov, ee, ch, li |
| knot[2]@2.1.0 | 2016-01-14 | alg13 | no step test: no before-period in se, nu, gov, ee, ch, li |
| knot[3]@2.2.0 | 2016-04-26 | rsa1024 | no step test in any corpus: no before-period in se, nu, gov, ee, ch, li |
| knot[7]@2.6.0 | 2017-09-29 | alg3_6 | no step test in any corpus: no before-period in se, ch; the value never appears in this series in nu, gov, ee, li; the value is absent in every month of the window 2015-10..2018-09 in panel |
| knot[8]@2.7.0 | 2018-08-03 | rsa_lt1024 | no step test: no before-period in gov, ch, li; the value never appears in this series in ee |
| knot[10]@2.8.0 | 2019-03-05 | cds | no step test: no before-period in gov, ee, ch, li |
| knot[11]@2.8.0 | 2019-03-05 | digest1 | no step test: no before-period in gov, ch, li; the value never appears in this series in ee |
| knot[12]@3.0.2 | 2020-11-11 | alg5_7 | no step test: no before-period in ee, ch, li |
| knot[19]@3.6.0 | 2026-09-08 | iter_gt256 | no step test in any corpus: no after-period in se, nu, ch; the value never appears in this series in gov, ee, li |

### kresd

Knot Resolver is a validator; only its NSEC3 iteration caps map, indirectly.

**Question 1:** 5 step tests, none outside the null band. **Question 2:** kresd[9]@5.3.1, the cap of 150 in 2021-03,
is inside its band in all three TLDs with a step test. kresd[12] and kresd[15], the cap of 50 in 2024-02, have no
after-period.

Question 1 counts. step12: 5 tested, 0 means outside the null band, 0 excess-outside tests; not tested besides fed.us: 6 because the testable window is shorter than 24 months, 1 because the value is present in fewer than 12 months. transient3: 11 tested, 0 means outside the null band, 0 excess-outside tests; not tested besides fed.us: 1 because the value is present in fewer than 12 months.

| statistic | observable | corpora tested | release months tested per corpus | null percentile of the mean, lowest to highest | means outside the 90% null | tests where more release months fall outside the band than chance, p < 0.10 |
|---|---|---|---|---|---|---|
| step12 | iter_gt150 | se, nu | 32, 32 | 5.0 to 6.1 | 0 of 2 | 0 of 2 |
| step12 | iter_gt50 | se, nu, gov | 32, 32, 26 | 9.9 to 11.4 | 0 of 3 | 0 of 3 |
| transient3 | iter_gt150 | se, nu, ee, ch, li | 50, 50, 27, 20, 20 | 16.7 to 54.1 | 0 of 5 | 0 of 5 |
| transient3 | iter_gt50 | se, nu, gov, ee, ch, li | 50, 50, 44, 27, 20, 20 | 8.1 to 81.1 | 0 of 6 | 0 of 6 |

Question 2:

| row | timing | observable | corpus | upgrade, opt-in | step12, pp | percentile | outside | transient12, pp | percentile | outside |
|---|---|---|---|---|---|---|---|---|---|---|
| kresd[9]@5.3.1 | 2021-03-31 | iter_gt150 | se | yes, no | -0.000116 | 5.9 | no | 1e-06 | 79.9 | no |
| kresd[9]@5.3.1 | 2021-03-31 | iter_gt150 | nu | yes, no | -0.00028 | 46.1 | no | 2e-06 | 58.6 | no |
| kresd[9]@5.3.1 | 2021-03-31 | iter_gt150 | gov | yes, no | 0.03842 | 90.5 | no | 0.03842 | 92.7 | no |
| kresd[9]@5.3.1 | 2021-03-31 | iter_gt150 | ee | yes, no | no test | |  | -0.000217 | 25.8 | no |

Where the step test could not run, besides fed.us:

| row | timing | observable | why not tested |
|---|---|---|---|
| kresd[9]@5.3.1 | 2021-03-31 | iter_gt150 | no step test: no before-period in ee, ch, li |
| kresd[12]@5.7.1 | 2024-02-13 | iter_gt50 | no step test in any corpus: no after-period in se, nu, gov, ee, ch, li |
| kresd[15]@6.0.6 | 2024-02-13 | iter_gt50 | no step test in any corpus: no after-period in se, nu, gov, ee, ch, li |

### nsd

NSD serves what the zone file holds and does not sign, so no row maps to a zone-data observable and nothing was
tested. This is a program with no mapped observable, not a null result.

### opendnssec

OpenDNSSEC has 65 stable releases in 52 release months, and four observables.

**Question 1, step test:** 15 tests. One mean falls outside the null band, algorithm 7 in .gov at p = 0.054, on 9
release months, and one excess-outside test, algorithm 7 in .se. Two of 15 is chance level.

**Question 2:** opendnssec[13]@2.1.0, SHA-256 only in key export, 2017-02, is the only testable row, on the panel, at the
59th percentile of the step test.

**Not testable:** opendnssec[5], the switch from algorithm 7 to 8 in 2011-03, and opendnssec[3], 2010-05, predate every
corpus.

Question 1 counts. step12: 15 tested, 1 means outside the null band, 1 excess-outside tests; not tested besides fed.us: 11 because the testable window is shorter than 24 months, 1 because the value never appears. transient3: 26 tested, 2 means outside the null band, 0 excess-outside tests; not tested besides fed.us: 1 because the value never appears.

| statistic | observable | corpora tested | release months tested per corpus | null percentile of the mean, lowest to highest | means outside the 90% null | tests where more release months fall outside the band than chance, p < 0.10 |
|---|---|---|---|---|---|---|
| step12 | alg7 | se, nu, gov, panel | 9, 9, 9, 32 | 11.2 to 97.3 | 1 of 4 | 1 of 4 |
| step12 | alg8 | se, nu, gov, panel | 9, 9, 9, 32 | 34.9 to 94.7 | 0 of 4 | 0 of 4 |
| step12 | digest1 | se, nu, gov, panel | 9, 9, 9, 32 | 29.5 to 78.5 | 0 of 4 | 0 of 4 |
| step12 | optout | se, nu, gov | 9, 9, 9 | 13.5 to 84.9 | 0 of 3 | 0 of 3 |
| transient3 | alg7 | se, nu, gov, ee, ch, li, panel | 16, 16, 11, 9, 7, 7, 46 | 7.0 to 95.3 | 1 of 7 | 0 of 7 |
| transient3 | alg8 | se, nu, gov, ee, ch, li, panel | 16, 16, 11, 9, 7, 7, 46 | 3.9 to 67.6 | 1 of 7 | 0 of 7 |
| transient3 | digest1 | se, nu, gov, ch, li, panel | 16, 16, 11, 7, 7, 46 | 16.2 to 74.9 | 0 of 6 | 0 of 6 |
| transient3 | optout | se, nu, gov, ee, ch, li | 16, 16, 11, 9, 7, 7 | 14.6 to 81.6 | 0 of 6 | 0 of 6 |

Question 2:

| row | timing | observable | corpus | upgrade, opt-in | step12, pp | percentile | outside | transient12, pp | percentile | outside |
|---|---|---|---|---|---|---|---|---|---|---|
| opendnssec[13]@2.1.0 | 2017-02-22 | digest1 | panel | yes, no | 1.007 | 59.4 | no | 0.7345 | 86.6 | no |

Where the step test could not run, besides fed.us:

| row | timing | observable | why not tested |
|---|---|---|---|
| opendnssec[3]@1.1.0rc1 | 2010-05-26 | optout | no step test in any corpus: no before-period in se, nu, gov, ee, ch, li |
| opendnssec[5]@1.2.0b1 | 2011-03-18 | alg8 | no step test in any corpus: no before-period in se, nu, gov, ee, ch, li, panel, se, nu, gov, ee, ch, li, panel |
| opendnssec[13]@2.1.0 | 2017-02-22 | digest1 | no step test: no before-period in se, nu, gov, ch, li; the value never appears in this series in ee |

### pdns-auth

PowerDNS Authoritative has 132 stable releases in 85 release months, and seven observables.

**Question 1, step test:** 19 tests. Three means fall outside the null band: algorithm 13 in .se at the 100th
percentile, algorithm 8 in .nu at the 4th, and opt-out in .se at the 0th. Two further tests have an excess of release
months outside the band. Five of 19 is more than the 1.9 chance gives, but the three means all fall in .se and .nu
over 2018 to 2023, the years in which those TLDs' zones moved from RSASHA256 to ECDSA and dropped opt-out, and every
program that released often in those years sits over the same moves. With 21 release months in a 56-month window, the
null has only 55 distinct shifts, so its resolution is about 2%.

**Question 2, step test:** 10 tests, none outside the band. pdns-auth[7] and [8], the ECDSA default of 2016-07, are
at the 57th and 59th percentiles on the panel. pdns-auth[10], the 100-iteration clamp, and pdns-auth[11], opt-in 0
iterations, are inside their bands everywhere.

**Not testable:** pdns-auth[0], RSASHA256 in 2013-01, now lacks a 24-month before-period on the panel; the transient test
and question 3 still cover it. pdns-auth[1], [3], [4] and [9] predate every corpus that records their value.

Question 1 counts. step12: 19 tested, 3 means outside the null band, 2 excess-outside tests; not tested besides fed.us: 18 because the testable window is shorter than 24 months, 4 because the value never appears, 3 because the value is present in fewer than 12 months. transient3: 37 tested, 1 means outside the null band, 2 excess-outside tests; not tested besides fed.us: 4 because the value never appears, 3 because the value is present in fewer than 12 months.

| statistic | observable | corpora tested | release months tested per corpus | null percentile of the mean, lowest to highest | means outside the 90% null | tests where more release months fall outside the band than chance, p < 0.10 |
|---|---|---|---|---|---|---|
| step12 | alg13 | se, nu, gov, panel | 21, 21, 17, 55 | 44.6 to 100.0 | 1 of 4 | 0 of 4 |
| step12 | alg8 | se, nu, gov, panel | 21, 21, 17, 55 | 3.8 to 16.5 | 1 of 4 | 1 of 4 |
| step12 | iter0 | se, nu, gov | 21, 21, 17 | 12.2 to 85.9 | 0 of 3 | 0 of 3 |
| step12 | iter_gt100 | se, nu | 21, 21 | 73.4 to 77.2 | 0 of 2 | 0 of 2 |
| step12 | optout | se, nu, gov | 21, 21, 17 | 0.0 to 50.9 | 1 of 3 | 1 of 3 |
| step12 | rsa1024 | se, nu, gov | 21, 21, 17 | 17.8 to 41.6 | 0 of 3 | 0 of 3 |
| transient3 | alg13 | se, nu, gov, ee, ch, li, panel | 32, 32, 29, 19, 17, 17, 65 | 18.9 to 92.8 | 0 of 7 | 0 of 7 |
| transient3 | alg8 | se, nu, gov, ee, ch, li, panel | 32, 32, 29, 19, 17, 17, 65 | 19.6 to 92.7 | 0 of 7 | 0 of 7 |
| transient3 | iter0 | se, nu, gov, ee, ch, li | 32, 32, 29, 19, 17, 17 | 13.0 to 87.0 | 0 of 6 | 1 of 6 |
| transient3 | iter_gt100 | se, nu, ee, ch, li | 32, 32, 19, 17, 17 | 28.1 to 100.0 | 1 of 5 | 0 of 5 |
| transient3 | optout | se, nu, gov, ee, ch, li | 32, 32, 29, 19, 17, 17 | 13.0 to 87.3 | 0 of 6 | 1 of 6 |
| transient3 | rsa1024 | se, nu, gov, ee, ch, li | 32, 32, 29, 19, 17, 17 | 6.3 to 83.4 | 0 of 6 | 0 of 6 |

Question 2:

| row | timing | observable | corpus | upgrade, opt-in | step12, pp | percentile | outside | transient12, pp | percentile | outside |
|---|---|---|---|---|---|---|---|---|---|---|
| pdns-auth[0]@3.2 | 2013-01-17 | alg8 | panel | no, no | no test | |  | -0.5919 | 25.9 | no |
| pdns-auth[7]@4.0.0 | 2016-07-08 | alg13 | panel | no, no | 0.1464 | 57.0 | no | -0.01235 | 19.2 | no |
| pdns-auth[8]@4.0.0 | 2016-07-08 | alg13 | panel | no, no | 0.1464 | 59.1 | no | -0.01235 | 19.5 | no |
| pdns-auth[10]@4.5.0 | 2021-07-12 | iter_gt100 | se | yes, no | -0.000195 | 27.9 | no | -0.000129 | 12.7 | no |
| pdns-auth[10]@4.5.0 | 2021-07-12 | iter_gt100 | nu | yes, no | 0.000561 | 69.0 | no | -0.000186 | 5.0 | no |
| pdns-auth[10]@4.5.0 | 2021-07-12 | iter_gt100 | gov | yes, no | 0.03842 | 91.4 | no | 0.03842 | 93.5 | no |
| pdns-auth[10]@4.5.0 | 2021-07-12 | iter_gt100 | ee | yes, no | -0.002051 | 2.6 | no | -0.003223 | 13.5 | no |
| pdns-auth[10]@4.5.0 | 2021-07-12 | iter_gt100 | ch | yes, no | no test | |  | -0.0392 | 15.9 | no |
| pdns-auth[10]@4.5.0 | 2021-07-12 | iter_gt100 | li | yes, no | no test | |  | -0.1052 | 22.3 | no |
| pdns-auth[11]@4.6.0 | 2022-01-24 | iter0 | se | no, yes | 1.495 | 84.5 | no | 0.02612 | 86.5 | no |
| pdns-auth[11]@4.6.0 | 2022-01-24 | iter0 | nu | no, yes | 2.793 | 80.2 | no | 3.1e-05 | 31.6 | no |
| pdns-auth[11]@4.6.0 | 2022-01-24 | iter0 | gov | no, yes | 0.06069 | 72.6 | no | -0.03619 | 7.5 | no |
| pdns-auth[11]@4.6.0 | 2022-01-24 | iter0 | ee | no, yes | 0.05147 | 42.6 | no | -3.8e-05 | 5.2 | no |
| pdns-auth[11]@4.6.0 | 2022-01-24 | iter0 | ch | no, yes | no test | |  | 0.01274 | 12.6 | no |
| pdns-auth[11]@4.6.0 | 2022-01-24 | iter0 | li | no, yes | no test | |  | 0.001285 | 16.1 | no |

Where the step test could not run, besides fed.us:

| row | timing | observable | why not tested |
|---|---|---|---|
| pdns-auth[0]@3.2 | 2013-01-17 | alg8 | no step test in any corpus: no before-period in se, nu, gov, ee, ch, li, panel |
| pdns-auth[1]@3.3 | 2013-07-05 | optout | no step test in any corpus: no before-period in se, nu, gov, ee, ch, li |
| pdns-auth[3]@3.4.0 | 2014-09-30 | iter_gt500 | no step test in any corpus: no before-period in se, ch; the value never appears in this series in nu, gov, ee, li |
| pdns-auth[4]@3.4.7 | 2015-11-03 | iter_gt500 | no step test in any corpus: no before-period in se, ch; the value never appears in this series in nu, gov, ee, li |
| pdns-auth[7]@4.0.0 | 2016-07-08 | alg13 | no step test: no before-period in se, nu, gov, ee, ch, li |
| pdns-auth[8]@4.0.0 | 2016-07-08 | alg13 | no step test: no before-period in se, nu, gov, ee, ch, li |
| pdns-auth[9]@4.0.0 | 2016-07-08 | rsa1024 | no step test in any corpus: no before-period in se, nu, gov, ee, ch, li |
| pdns-auth[10]@4.5.0 | 2021-07-12 | iter_gt100 | no step test: no before-period in ch, li |
| pdns-auth[11]@4.6.0 | 2022-01-24 | iter0 | no step test: no before-period in ch, li |

### pdns-rec

PowerDNS Recursor has 171 publicly released stable tags; rec-4.5.0, rec-4.5.3 and rec-5.0.0 were never shipped
and are excluded. Only its NSEC3 caps map, indirectly.

**Question 1:** 5 step tests, none outside. **Question 2:** nsec3-max-iterations-150, 2021-06, is inside its band in the
three TLDs with a step test, at the 5th percentile in .se. The caps of 2500 and 50 have no series or no after-period.

Question 1 counts. step12: 5 tested, 0 means outside the null band, 0 excess-outside tests; not tested besides fed.us: 6 because the testable window is shorter than 24 months, 6 because the value never appears, 1 because the value is present in fewer than 12 months. transient3: 11 tested, 1 means outside the null band, 0 excess-outside tests; not tested besides fed.us: 6 because the value never appears, 1 because the value is present in fewer than 12 months.

| statistic | observable | corpora tested | release months tested per corpus | null percentile of the mean, lowest to highest | means outside the 90% null | tests where more release months fall outside the band than chance, p < 0.10 |
|---|---|---|---|---|---|---|
| step12 | iter_gt150 | se, nu | 30, 30 | 54.6 to 67.1 | 0 of 2 | 0 of 2 |
| step12 | iter_gt50 | se, nu, gov | 30, 30, 26 | 33.1 to 91.8 | 0 of 3 | 0 of 3 |
| transient3 | iter_gt150 | se, nu, ee, ch, li | 42, 42, 26, 21, 21 | 1.9 to 82.3 | 1 of 5 | 0 of 5 |
| transient3 | iter_gt50 | se, nu, gov, ee, ch, li | 42, 42, 38, 26, 21, 21 | 10.6 to 73.9 | 0 of 6 | 0 of 6 |

Question 2:

| row | timing | observable | corpus | upgrade, opt-in | step12, pp | percentile | outside | transient12, pp | percentile | outside |
|---|---|---|---|---|---|---|---|---|---|---|
| nsec3-max-iterations-150 | 2021-06-07 | iter_gt150 | se | yes, no | -0.000118 | 5.2 | no | -0 | 48.0 | no |
| nsec3-max-iterations-150 | 2021-06-07 | iter_gt150 | nu | yes, no | -0.000512 | 29.2 | no | -3e-06 | 47.5 | no |
| nsec3-max-iterations-150 | 2021-06-07 | iter_gt150 | gov | yes, no | 0.03842 | 91.4 | no | 0.03842 | 92.8 | no |
| nsec3-max-iterations-150 | 2021-06-07 | iter_gt150 | ee | yes, no | no test | |  | -1.3e-05 | 38.2 | no |
| nsec3-max-iterations-150 | 2021-06-07 | iter_gt150 | ch | yes, no | no test | |  | -0.002389 | 7.0 | no |
| nsec3-max-iterations-150 | 2021-06-07 | iter_gt150 | li | yes, no | no test | |  | -0.007109 | 7.6 | no |

Where the step test could not run, besides fed.us:

| row | timing | observable | why not tested |
|---|---|---|---|
| nsec3-max-iterations-2500 | 2017-12-04 | iter_gt2500 | no step test in any corpus: the value never appears in this series in se, nu, gov, ee, ch, li |
| nsec3-max-iterations-150 | 2021-06-07 | iter_gt150 | no step test: no before-period in ee, ch, li |
| nsec3-max-iterations-50 | 2024-01-09 | iter_gt50 | no step test in any corpus: no after-period in se, nu, gov, ee, ch, li |

### unbound

Unbound has 120 stable releases in 102 release months. Only its NSEC3 caps map, indirectly.

**Question 1:** 2 step tests; one mean, NSEC3 names above 150 in .nu, is higher than under every shifted schedule, on a share
near 0.002%, which is the direction a cap would not produce. **Question 2:** unbound[20], the cap of 150 in 2021-08, is inside its band in all four
TLDs with a step test. unbound[1] shipped in 2007, before any corpus.

Question 1 counts. step12: 2 tested, 1 means outside the null band, 0 excess-outside tests; not tested besides fed.us: 3 because the testable window is shorter than 24 months, 1 because the value is present in fewer than 12 months. transient3: 5 tested, 2 means outside the null band, 1 excess-outside tests; not tested besides fed.us: 1 because the value is present in fewer than 12 months.

| statistic | observable | corpora tested | release months tested per corpus | null percentile of the mean, lowest to highest | means outside the 90% null | tests where more release months fall outside the band than chance, p < 0.10 |
|---|---|---|---|---|---|---|
| step12 | iter_gt150 | se, nu | 27, 27 | 88.0 to 100.0 | 1 of 2 | 0 of 2 |
| transient3 | iter_gt150 | se, nu, ee, ch, li | 37, 37, 19, 13, 13 | 2.2 to 97.6 | 2 of 5 | 1 of 5 |

Question 2:

| row | timing | observable | corpus | upgrade, opt-in | step12, pp | percentile | outside | transient12, pp | percentile | outside |
|---|---|---|---|---|---|---|---|---|---|---|
| unbound[20]@1.13.2 | 2021-08-05 | iter_gt150 | se | yes, no | -5.6e-05 | 21.1 | no | 0 | 66.5 | no |
| unbound[20]@1.13.2 | 2021-08-05 | iter_gt150 | nu | yes, no | -0.000691 | 18.1 | no | -1e-05 | 38.5 | no |
| unbound[20]@1.13.2 | 2021-08-05 | iter_gt150 | gov | yes, no | 0.009641 | 74.2 | no | 0.02269 | 82.7 | no |
| unbound[20]@1.13.2 | 2021-08-05 | iter_gt150 | ee | yes, no | 0.004295 | 56.6 | no | 0 | 70.3 | no |
| unbound[20]@1.13.2 | 2021-08-05 | iter_gt150 | ch | yes, no | no test | |  | -0.001634 | 16.2 | no |
| unbound[20]@1.13.2 | 2021-08-05 | iter_gt150 | li | yes, no | no test | |  | -0.00611 | 18.8 | no |

Where the step test could not run, besides fed.us:

| row | timing | observable | why not tested |
|---|---|---|---|
| unbound[1]@0.5 | 2007-09-25 | iter_gt150 | no step test in any corpus: no before-period in se, nu, gov, ee, ch, li |
| unbound[20]@1.13.2 | 2021-08-05 | iter_gt150 | no step test: no before-period in ch, li |

### The two .se results under a multiple-testing view

| event | step12, pp | percentile | two-sided p | step tests in the family | at least as extreme | expected by chance | Benjamini-Hochberg q |
|---|---|---|---|---|---|---|---|
| d21-signzone-nsec3-iterations-0, .se | 2.640 | 97.5 | 0.066 | 78 | 4 | 5.1 | 0.82 |
| knot[14]@3.2.0, .se | 2.880 | 99.1 | 0.036 | 78 | 1 | 2.8 | 0.82 |

The verifier's own step-sensitive version, a line fitted to 12 months and percentiles over all testable months, put
these two at the 97.8th and 99.3rd percentiles and their raw 12-month changes at the 96.3rd and 99.3rd. This revision,
with a 24-month fit and 1,000 placebo draws, gives the 97.6th and 99.1st. Both approaches agree that the two .se events
are the most extreme default-change events in the data, and that about as many events as chance predicts reach that
level. The same two rows are at the 10th percentile in .nu, in the opposite direction.

## Question 3: manual against automatic, and at which level

The reverse ledger `delegation_change_clusters.parquet` groups every change into actions: one month, one RIR, one
block and one transition. The events are the signer default changes that name a target algorithm: bind9 d02 to
algorithm 5, knot[1], opendnssec[5] and pdns-auth[0] to 8, and knot[2], pdns-auth[7] and [8] and bind9 d15 to 13. The
window for a release in calendar month r is ledger labels r+1 to r+4, which are the changes made in the release month
and the 3 months after. The matching transitions are new signings and rollovers to the target algorithm.

Two statistics are compared between window months and all other months: the share of matching delegations that moved in
actions of 10 or more, and the share at level "one block" or "concentrated" in `delegation_change_levels.parquet`. The
null draws the same number of months at random from the ledger span, 1,000 times. Because ledger activity rises about
25-fold from 2009 to 2019, an era-matched version draws only from months within 36 months of the window.

Action size is a proxy. One operator automating one delegation is indistinguishable from a manual edit, and one operator
hand-editing a whole block is indistinguishable from an upgrade.

| group | scope | window, labels | matching delegations, window / other | large-action share, difference | p | era-matched p | one-block-or-concentrated share, difference | p | era-matched p |
|---|---|---|---|---|---|---|---|---|---|
| d02-keygen-default-alg-rsasha1 | all RIRs | 2010-03..2010-06 | 73 / 1633 | +0.046 | 0.224 | 0.335 | +0.011 | 0.630 | 0.632 |
| d02-keygen-default-alg-rsasha1 | ripe | 2010-03..2010-06 | 73 / 741 | +0.039 | 0.179 | 0.311 | +0.115 | 0.509 | 0.496 |
| knot[1]@2.0.0 | all RIRs | 2015-07..2015-10 | 127 / 7501 | -0.169 | 0.362 | 0.582 | -0.133 | 0.680 | 0.777 |
| knot[1]@2.0.0 | apnic | 2015-07..2015-10 | 10 / 3139 | -0.800 | 0.924 | 0.879 | +0.871 | 0.102 | 0.074 |
| knot[1]@2.0.0 | arin | 2015-07..2015-10 | 15 / 2349 | -0.373 | 0.517 | 0.789 | -0.083 | 0.475 | 0.806 |
| knot[1]@2.0.0 | ripe | 2015-07..2015-10 | 98 / 997 | -0.002 | 0.187 | 0.318 | -0.501 | 0.589 | 0.685 |
| opendnssec[5]@1.2.0b1 | all RIRs | 2011-04..2011-07 | 31 / 7597 | -0.546 | 0.719 | 0.823 | -0.288 | 0.875 | 0.846 |
| opendnssec[5]@1.2.0b1 | ripe | 2011-04..2011-07 | 30 / 1065 | -0.505 | 0.947 | 0.867 | -0.485 | 0.611 | 0.661 |
| pdns-auth[0]@3.2 | all RIRs | 2013-02..2013-05 | 73 / 7555 | +0.336 | 0.060 | 0.074 | +0.558 | 0.098 | 0.214 |
| pdns-auth[0]@3.2 | ripe | 2013-02..2013-05 | 70 / 1025 | +0.452 | 0.041 | 0.050 | +0.402 | 0.347 | 0.254 |
| pdns-auth[7]@4.0.0 | all RIRs | 2016-08..2016-11 | 5 / 8380 | -0.211 | 0.669 | 0.667 | +0.167 | 0.178 | 0.576 |
| pdns-auth[8]@4.0.0 | all RIRs | 2016-08..2016-11 | 5 / 8380 | -0.211 | 0.658 | 0.643 | +0.167 | 0.172 | 0.560 |
| d15-dnssec-policy-default-ecdsap256 | all RIRs | 2020-03..2020-06 | 63 / 8322 | -0.213 | 0.787 | 0.837 | +0.085 | 0.237 | 0.392 |
| d15-dnssec-policy-default-ecdsap256 | apnic | 2020-03..2020-06 | 5 / 845 | -0.386 | 0.429 | 0.411 | +0.220 | 0.497 | 0.466 |
| d15-dnssec-policy-default-ecdsap256 | arin | 2020-03..2020-06 | 51 / 5031 | -0.235 | 0.785 | 0.800 | +0.066 | 0.269 | 0.331 |
| d15-dnssec-policy-default-ecdsap256 | ripe | 2020-03..2020-06 | 7 / 603 | -0.255 | 0.495 | 0.432 | +0.061 | 0.516 | 0.483 |
| all default changes to algorithm 8 | all RIRs | 2015-07..2015-10, 2011-04..2011-07, 2013-02..2013-05 | 231 / 7397 | -0.061 | 0.418 | 0.526 | +0.066 | 0.399 | 0.600 |
| all default changes to algorithm 8 | apnic | 2015-07..2015-10, 2011-04..2011-07, 2013-02..2013-05 | 11 / 3138 | -0.800 | 0.836 | 0.764 | +0.780 | 0.249 | 0.238 |
| all default changes to algorithm 8 | arin | 2015-07..2015-10, 2011-04..2011-07, 2013-02..2013-05 | 18 / 2346 | -0.373 | 0.787 | 0.729 | -0.039 | 0.448 | 0.826 |
| all default changes to algorithm 8 | ripe | 2015-07..2015-10, 2011-04..2011-07, 2013-02..2013-05 | 198 / 897 | +0.091 | 0.229 | 0.343 | -0.200 | 0.619 | 0.647 |
| all default changes to algorithm 13 | all RIRs | 2016-02..2016-05, 2016-08..2016-11, 2016-08..2016-11, 2020-03..2020-06 | 68 / 8317 | -0.213 | 0.959 | 0.949 | +0.091 | 0.190 | 0.393 |
| all default changes to algorithm 13 | apnic | 2016-02..2016-05, 2016-08..2016-11, 2016-08..2016-11, 2020-03..2020-06 | 7 / 843 | -0.387 | 0.420 | 0.540 | +0.278 | 0.286 | 0.324 |
| all default changes to algorithm 13 | arin | 2016-02..2016-05, 2016-08..2016-11, 2016-08..2016-11, 2020-03..2020-06 | 53 / 5029 | -0.235 | 0.934 | 0.883 | +0.058 | 0.231 | 0.347 |
| all default changes to algorithm 13 | ripe | 2016-02..2016-05, 2016-08..2016-11, 2016-08..2016-11, 2020-03..2020-06 | 8 / 602 | -0.256 | 0.364 | 0.436 | -0.029 | 0.512 | 0.564 |

36 group and scope cells have no test; the per-cell reasons are in the CSV. knot[2] has no matching new
signing or rollover to algorithm 13 in any RIR in its window, and pdns-auth[7] and [8] have 5 across all RIRs.

**Result.** No statistic passes after the release in the pooled data. pdns-auth[0]@3.2, released 2013-01-17, is the
closest: in labels 2013-02 to 2013-05 the one-block-or-concentrated share is +0.56
higher than in other months, p = 0.098, era-matched 0.21, and the
large-action share is +0.34 higher, p = 0.060, era-matched
0.07. In RIPE alone the large-action difference has p = 0.041. The result
the first version reported, p = 0.015, came from the window labels 2013-01 to 2013-04. It was carried by concentrated
signings in 2013-01 and 2013-02, 106 delegations, 42 of them in label 2013-01 and so made in December 2012, before the
release. It was not one RIPE block: the verifier showed that without block 216.151.in-addr.arpa the old result is
unchanged, because the other 42 delegations are concentrated too. With 48 p-values in the table,
1 are below 0.05, where chance gives about 2.4.

The share of matching delegations moved in actions of 10 or more is lower in the window than in other months in
19 of 24 tested cells: large actions are not
more common after a signer default change.

Pooled over all RIRs, the size distribution of matching delegations in the windows against other months:

| window group | 1 | 2-4 | 5-9 | 10-49 | 50-99 | 100+ |
|---|---|---|---|---|---|---|
| d02-keygen-default-alg-rsasha1, window | 10 | 11 | 5 | 47 | 0 | 0 |
| d02-keygen-default-alg-rsasha1, other months | 197 | 286 | 174 | 478 | 63 | 435 |
| knot[1]@2.0.0, window | 27 | 12 | 40 | 48 | 0 | 0 |
| knot[1]@2.0.0, other months | 805 | 1877 | 719 | 2415 | 500 | 1185 |
| opendnssec[5]@1.2.0b1, window | 13 | 10 | 8 | 0 | 0 | 0 |
| opendnssec[5]@1.2.0b1, other months | 819 | 1879 | 751 | 2463 | 500 | 1185 |
| pdns-auth[0]@3.2, window | 7 | 2 | 0 | 0 | 64 | 0 |
| pdns-auth[0]@3.2, other months | 825 | 1887 | 759 | 2463 | 436 | 1185 |
| pdns-auth[7]@4.0.0, window | 5 | 0 | 0 | 0 | 0 | 0 |
| pdns-auth[7]@4.0.0, other months | 1412 | 4465 | 734 | 1338 | 315 | 116 |
| pdns-auth[8]@4.0.0, window | 5 | 0 | 0 | 0 | 0 | 0 |
| pdns-auth[8]@4.0.0, other months | 1412 | 4465 | 734 | 1338 | 315 | 116 |
| d15-dnssec-policy-default-ecdsap256, window | 24 | 31 | 8 | 0 | 0 | 0 |
| d15-dnssec-policy-default-ecdsap256, other months | 1393 | 4434 | 726 | 1338 | 315 | 116 |
| all default changes to algorithm 8, window | 47 | 24 | 48 | 48 | 64 | 0 |
| all default changes to algorithm 8, other months | 785 | 1865 | 711 | 2415 | 436 | 1185 |
| all default changes to algorithm 13, window | 29 | 31 | 8 | 0 | 0 | 0 |
| all default changes to algorithm 13, other months | 1388 | 4434 | 726 | 1338 | 315 | 116 |

Per RIR counts are in the CSV under the same column names, and the level distributions under
`window_delegations_by_level:*` and `other_delegations_by_level:*`.

Recompute: `python scripts/software_vs_adoption.py --only q3 && python -c "import pandas as pd;d=pd.read_csv('out/analysis/software_vs_adoption_q3.csv');print(d[['group','scope','status','windows','window_matching_delegations','diff_share_in_actions_ge_10','p_large_ge_observed','p_large_era_matched','diff_share_one_block_or_concentrated','p_block_ge_observed','p_block_era_matched','reason']].to_string())"`

## Question 4: adoption spikes, attributed or not

Spikes use `spikes()` from `scripts/program_rfc_cases.py`, imported rather than re-implemented, on the numerator counts
of each mapped observable: forward per TLD with a floor of 300 names, reverse per RIR with a floor of 30 delegations.
Both directions are scanned. A reverse spike labelled M is a change between the states of the 1st of M-1 and the 1st
of M, so it happened in calendar month M-1; the CSV gives that month as `change_calendar_month_start`, and lags and
chance rates use it. A default change is relevant to a spike if it maps to the same observable with the same expected
direction; it is aligned if it falls 0 to 3 calendar months before the change. Lag 0 means the same calendar month,
which can include days before the release. The chance rate is the share of the series' months that have a relevant
default change 0 to 3 months before them. Each observable, corpus and direction is judged by the Poisson-binomial tail
of its aligned count, which assumes independent spikes; spikes in one TLD a few months apart are not independent, so
the p-values are if anything too small.

For every spike the JSON and CSV also give the nearest preceding verified release of each of the eight programs and
its lag. The brief records that 97% of corpus months contain some release, so that column is descriptive only.

The composition of a reverse spike comes from the ledger, whose labels now match the per-RIR counts: new signings,
rollovers or unsignings of the spike's algorithm in the spike labels. The ledger records only DS algorithms, so a digest
spike has no composition. A forward spike has only a bound, from the growth in signed zones.

248 spikes: 120 forward and 128 reverse. 13 have a relevant default change within 3 months before them, against 9.1 expected from the chance rates.

| observable | corpus | direction | spikes | aligned within 3 months | expected by chance | p, at least as many |
|---|---|---|---|---|---|---|
| alg13 | forward | + | 17 | 2 | 1.23 | 0.352 |
| alg13 | reverse | + | 13 | 0 | 0.74 | 1.000 |
| alg5 | forward | - | 2 | 0 | 0.09 | 1.000 |
| alg5 | reverse | - | 6 | 0 | 0.12 | 1.000 |
| alg5 | reverse | + | 10 | 1 | 0.20 | 0.186 |
| alg5_7 | forward | - | 4 | 0 | 0.23 | 1.000 |
| alg5_7 | reverse | - | 7 | 0 | 0.11 | 1.000 |
| alg7 | reverse | - | 6 | 0 | 0.09 | 1.000 |
| alg8 | reverse | + | 21 | 2 | 1.22 | 0.347 |
| digest1 | forward | - | 8 | 2 | 1.08 | 0.296 |
| digest1 | reverse | - | 7 | 0 | 0.57 | 1.000 |
| iter0 | forward | + | 13 | 6 | 2.07 | 0.009 |
| iter5 | forward | + | 6 | 0 | 0.44 | 1.000 |
| rsa1024 | forward | - | 9 | 0 | 0.80 | 1.000 |
| rsa_lt1024 | forward | - | 3 | 0 | 0.13 | 1.000 |

18 further observable, corpus and direction cells have 116 spikes between them and no
relevant default change anywhere near their series.

The aligned spikes:

| spike | observable, direction | corpus, source | labels | change made in | change | nearest relevant default | lag, months | chance rate | composition |
|---|---|---|---|---|---|---|---|---|---|
| 1 | alg13 + | forward se | 2016-10 to 2016-11 | 2016-10 | 17193 | pdns-auth pdns-auth[7]@4.0.0 2016-07-08 | 3 | 0.089 | mostly rollovers (bound); new signings at most 6445, rollovers at least 10748 |
| 6 | alg13 + | forward nu | 2016-10 to 2016-10 | 2016-10 | 857 | pdns-auth pdns-auth[7]@4.0.0 2016-07-08 | 3 | 0.089 | mostly rollovers (bound); new signings at most 0, rollovers at least 857 |
| 43 | alg5 + | reverse ripe | 2010-04 to 2010-04 | 2010-03 | 32 | bind9 d02-keygen-default-alg-rsasha1 2010-02-16 | 1 | 0.020 | mostly new signings; new signings 32, rollovers 0 |
| 127 | alg8 + | reverse ripe | 2013-02 to 2013-02 | 2013-01 | 66 | pdns-auth pdns-auth[0]@3.2 2013-01-17 | 0 | 0.055 | mostly new signings; new signings 64, rollovers 0 |
| 130 | alg8 + | reverse ripe | 2015-08 to 2015-08 | 2015-07 | 86 | knot knot[1]@2.0.0 2015-06-26 | 1 | 0.055 | mostly new signings; new signings 86, rollovers 0 |
| 145 | digest1 - | forward se | 2022-04 to 2022-04 | 2022-04 | 314317 | bind9 d20-dnssec-cds-sha2-only 2022-01-24 | 3 | 0.178 | not determinable: forward per-zone records are not in the repository |
| 147 | digest1 - | forward nu | 2022-04 to 2022-04 | 2022-04 | 48566 | bind9 d20-dnssec-cds-sha2-only 2022-01-24 | 3 | 0.178 | not determinable: forward per-zone records are not in the repository |
| 190 | iter0 + | forward se | 2022-07 to 2022-08 | 2022-07 | 41250 | bind9 d21-signzone-nsec3-iterations-0 2022-07-07 | 0 | 0.100 | not determinable: forward per-zone records are not in the repository |
| 193 | iter0 + | forward nu | 2022-08 to 2022-08 | 2022-08 | 1723 | knot knot[14]@3.2.0 2022-08-22 | 0 | 0.100 | not determinable: forward per-zone records are not in the repository |
| 196 | iter0 + | forward ch | 2022-03 to 2022-03 | 2022-03 | 20076 | bind9 d18-nsec3param-default-0-0 2022-01-24 | 2 | 0.209 | not determinable: forward per-zone records are not in the repository |
| 197 | iter0 + | forward ch | 2022-08 to 2022-08 | 2022-08 | 7920 | knot knot[14]@3.2.0 2022-08-22 | 0 | 0.209 | not determinable: forward per-zone records are not in the repository |
| 198 | iter0 + | forward ch | 2022-11 to 2023-02 | 2022-11 | 139874 | knot knot[14]@3.2.0 2022-08-22 | 3 | 0.209 | not determinable: forward per-zone records are not in the repository |
| 199 | iter0 + | forward li | 2022-03 to 2022-03 | 2022-03 | 544 | bind9 d18-nsec3param-default-0-0 2022-01-24 | 2 | 0.209 | not determinable: forward per-zone records are not in the repository |

**What beats chance:** only zero-iteration NSEC3 in the forward corpus, 6 of 13 spikes aligned against 2.07 expected,
p = 0.009. The six are .se in 2022-07, .nu in 2022-08, .ch in 2022-03, 2022-08 and 2022-11, and .li in 2022-03. The
defaults they follow, bind9 d18 and pdns-auth[11] in 2022-01, bind9 d21 in 2022-07 and knot[14] in 2022-08, and
RFC 9276, published 2022-08, fall within the same eight months. The IETF draft behind them was public by 2021-10 at the
latest: bind9 cites draft-ietf-dnsop-nsec3-guidance in a commit of 2021-10-20. Four of the seven unaligned
zero-iteration spikes fall in 2021-09 to 2021-12, before any zero-iteration signer default shipped. The six aligned
spikes are in four TLDs run by two registries; the operators of the changed zones cannot be identified, and three of the
six are one .ch series. This is an alignment, not an attribution.

**What does not:** every algorithm, digest, key-size, opt-out and CDS observable. The afrinic SHA-1 DS spike labelled
2022-01 was counted as aligned with bind9 d20 in the first version; it happened in December 2021, before d20 shipped on
2022-01-24, and is no longer aligned. The .se ECDSA spike of 2016-10, three months after PowerDNS 4.0.0, is at least 62%
rollovers of already-signed zones by the signed-zone bound, and a rollover is not what a new default produces. The
three aligned reverse spikes, algorithm 5 in RIPE and algorithm 8 in RIPE twice, are new signings of 32 to 86
delegations each, and 2 of 21 algorithm 8 spikes aligned against 1.2 expected is p = 0.35.

Recompute: `python scripts/software_vs_adoption.py --only q4 && python -c "import pandas as pd;print(pd.read_csv('out/analysis/software_vs_adoption_q4_alignment.csv').to_string());d=pd.read_csv('out/analysis/software_vs_adoption_q4.csv');print(d[d.relevant_default_within_3m][['n','observable','direction','source','start','change_calendar_month_start','delta','nearest_relevant_default','lag_months','chance_relevant_default_within_3m','composition']].to_string())"`

## Question 5: successor RFC while the predecessor is still deploying

Pairs come from the checklist: RFC 8624's `obsoleted_by`, RFC 9904, and the `related_rfc_ids` of RFC 9276, 9905 and
9906. The brief adds RFC 8624 against the RSASHA1 algorithms and SHA-1 DS it deprecates, and SHA-1 DS against RFC 4509.
The share is the predecessor's deployment in the month the successor was published; for the panel that is the state
on the 1st of that month. The trajectory compares it with up to 12 months later, fewer where the corpus ends; rising or
falling means a change of more than 10% relative. The peak is now taken only over months with at least 300 in the
denominator. The MIN_DEN floor of 30 alone admits the panel's first signed month, 2011-05, with 32 delegations and a
summed RSASHA1 share of 103%. This is descriptive and says nothing about cause.

| predecessor | successor, published | observable | corpus | share at successor, % | up to 12 months later, % | trajectory | peak, month, denominator | first month below half the peak | months from successor to that |
|---|---|---|---|---|---|---|---|---|---|
| RFC 5155 | RFC 9276, 2022-08 | iter_gt0 | se | 97.00 | 95.46, 2023-08 | flat | 100.00, 2021-02, 1341980 | not by 2023-12 |  |
| RFC 5155 | RFC 9276, 2022-08 | iter_gt0 | nu | 92.17 | 90.33, 2023-08 | flat | 100.00, 2016-12, 178049 | not by 2023-12 |  |
| RFC 5155 | RFC 9276, 2022-08 | iter_gt0 | gov | 99.94 | 99.08, 2023-08 | flat | 100.01, 2017-11, 1877 | not by 2023-12 |  |
| RFC 5155 | RFC 9276, 2022-08 | iter_gt0 | ee | 99.88 | 99.82, 2023-08 | flat | 100.02, 2019-07, 8550 | not by 2023-12 |  |
| RFC 5155 | RFC 9276, 2022-08 | iter_gt0 | ch | 95.67 | 82.42, 2023-08 | fell | 99.98, 2020-07, 50064 | not by 2023-12 |  |
| RFC 5155 | RFC 9276, 2022-08 | iter_gt0 | li | 92.59 | 81.31, 2023-08 | fell | 100.00, 2020-05, 2046 | not by 2023-12 |  |
| RFC 3110 / RFC 4034 RSASHA1 signing | RFC 8624, 2019-06 | alg5_7 | se | 0.71 | 0.52, 2020-06 | fell | 0.97, 2016-12, 716002 | 2020-11 | 17 |
| RFC 3110 / RFC 4034 RSASHA1 signing | RFC 8624, 2019-06 | alg5_7 | nu | 5.42 | 5.22, 2020-06 | flat | 6.30, 2016-11, 92190 | 2021-08 | 26 |
| RFC 3110 / RFC 4034 RSASHA1 signing | RFC 8624, 2019-06 | alg5_7 | gov | 35.79 | 31.41, 2020-06 | fell | 44.74, 2017-05, 1134 | 2022-02 | 32 |
| RFC 3110 / RFC 4034 RSASHA1 signing | RFC 8624, 2019-06 | alg5_7 | panel | 31.21 | 33.76, 2020-06 | flat | 50.16, 2014-08, 313 | 2017-02 | -28 |
| SHA-1 DS (RFC 4034 digest 1) | RFC 8624, 2019-06 | digest1 | se | 63.72 | 61.99, 2020-06 | flat | 65.49, 2017-10, 689140 | 2022-04 | 34 |
| SHA-1 DS (RFC 4034 digest 1) | RFC 8624, 2019-06 | digest1 | nu | 69.59 | 69.58, 2020-06 | flat | 93.10, 2017-05, 86803 | 2022-04 | 34 |
| SHA-1 DS (RFC 4034 digest 1) | RFC 8624, 2019-06 | digest1 | gov | 80.99 | 80.03, 2020-06 | flat | 93.91, 2017-12, 1097 | 2023-05 | 47 |
| SHA-1 DS (RFC 4034 digest 1) | RFC 8624, 2019-06 | digest1 | panel | 61.91 | 64.02, 2020-06 | flat | 91.56, 2014-09, 379 | 2022-05 | 35 |
| RFC 8624 | RFC 9904, 2025-11 | alg8_13 | panel | 87.78 | 90.25, 2026-08 | flat | 90.25, 2026-08, 6444 | not by 2026-08 |  |
| RFC 3110 (RSA/SHA-1) | RFC 9905, 2025-11 | alg5_7 | panel | 9.81 | 7.98, 2026-08 | fell | 50.16, 2014-08, 313 | 2017-02 | -105 |

Readings, without causal language:

- **RFC 5155 and RFC 9276.** When RFC 9276 was published in 2022-08, 92 to 99.9% of NSEC3 owner names in every forward
  TLD still used more than 0 iterations. Over the next 12 months the share of NSEC3 owner names stayed flat in .se, .nu,
  .gov and .ee and fell to about 82% in .ch and .li. It never fell below half its peak before the forward corpus ends in
  2023-12. The reverse corpus cannot see NSEC3.
- **RSASHA1 and RFC 8624.** In 2019-06 the RSASHA1 family, algorithms 5 and 7, was 31% of panel signed delegations, 36%
  of .gov signed zones, 5.4% in .nu and 0.7% in .se. On the panel its peak over months with at least 300 signed
  delegations is 50.2%, in 2014-08 with 313, and it fell below half of that in 2017-02, 28 months before RFC 8624; it
  was flat over the year after. In the forward TLDs it reached half its peak 17 to 32 months after RFC 8624. By 2026-08
  it is 8.0% of panel signed delegations.
- **SHA-1 DS and RFC 8624.** In 2019-06 SHA-1 DS was carried by 62% of panel DS-carrying delegations and by 64 to 81%
  in .se, .nu and .gov, flat over the next year in all four. It fell below half its peak 34 to 47 months after RFC 8624;
  on the panel the peak is 91.6% in 2014-09 with 379 delegations and the fall below half came in 2022-05, 35 months
  after.
- **SHA-1 DS and RFC 4509.** RFC 4509 was published in 2006-05, five years before the first covered month of any corpus,
  so the share at publication cannot be determined.
- **RFC 8624 and RFC 9904.** Only the panel covers 2025-11. The RFC 8624 MUST algorithms, 8 and 13, were 87.8% of panel
  signed delegations then and 90.3% nine months later.
- **RFC 3110 and RFC 9905.** RSASHA1 was 9.8% of panel signed delegations at RFC 9905's publication and 8.0% nine
  months later.
- **RFC 5933 and RFC 9906.** Algorithm 12, GOST, never appears in any corpus.

Recompute: `python scripts/software_vs_adoption.py --only q5 && python -c "import pandas as pd;d=pd.read_csv('out/analysis/software_vs_adoption_q5.csv');print(d[['predecessor','successor','source','status','share_at_successor','share_after_up_to_12m','trajectory','peak','peak_month','peak_denominator','first_below_half_peak_after_peak','months_from_successor_to_below_half','peak_over_min_den_months','reason']].to_string())"`

## What could not be determined

- Any event before 2011-05 in the reverse corpus, and before 2016-06 in the forward corpus; for the step test, any event
  without 24 months of data before it. That removes both ECDSA signing defaults of 2016 from the forward corpus, all four
  RSASHA256 signer defaults of 2011 to 2015 from the forward corpus, pdns-auth[0] from the step test, and bind9 d02,
  d03, opendnssec[3] and [5] and pdns-auth[1] from every test.
- Any event after 2023-12 in the forward corpus, which removes the NSEC3 caps of 50 and knot[19].
- A program-level test for BIND 9 and for most corpora of other frequent releasers: releases fill most months, so no
  schedule shift gives a contrast.
- Salt length, NSEC and NSEC3 TTLs, RRSIG timing and key-management state, which the monthly counts do not record.
- All validation, trust-anchor and validator-limit behaviour, apart from the NSEC3 caps tested indirectly.
- The software that signed any zone, and the DNS operator that runs it. Every alignment above is timing, not attribution.
- Whether a forward spike is new signings or rollovers beyond the bound, and the composition of any digest spike.
- Whether a reverse change made in the release month came before or after the release day; the corpus has one snapshot
  per month.

## What the revision changed

| item | first version | this revision | why |
|---|---|---|---|
| Q1 primary statistic | detrended 3-month change, centred 25-month median | step12, departure from a 24-month linear pre-trend over 12 months; the old statistic kept as transient3 | the rolling median absorbs a lasting step, as the verifier showed |
| Q1 null | circular shift over the program's whole release span | circular shift within the series' testable window, with a window of at least 24 months and release months in at most 75% of it | the whole-span shift was conservative: mean p 0.63; calibration 0.032 against 0.10 |
| Q1 tested, means outside the 90% null | 202 tested, 6 outside against 20.2 | step: 76 tested, 7 against 7.6; transient: 126 tested, 8 against 12.6 | new null; BIND 9 and other dense schedules no longer testable |
| Q1 mean p | 0.63 | step 0.46, transient 0.53 | calibrated null |
| Q2 primary statistic | detrended 12-month change | step12, the old statistic kept as transient12 | step blindness |
| Q2 events outside the 90% band | 103 tested, 2 outside against 10.3 | step: 78 tested, 5 outside against 7.8, lowest BH q 0.82; transient: 103 tested, 2 outside | new statistic and reverse dating |
| bind9 d21 and knot[14] in .se | transient percentiles 90.4 and 91.2, inside the band | step percentiles 97.5 and 99.1, outside the band; not beyond chance across 78 tests | step test |
| knot[2] on the panel | transient -0.019 pp, 15th percentile, after-labels from 2016-01 | step +0.229 pp, 63rd percentile; transient -0.022 pp; after-labels from 2016-02 | step test and reverse dating |
| pdns-auth[7] and [8] on the panel | transient -0.017 pp, 16th to 19th percentile | step +0.146 pp, 57th and 59th percentile | step test |
| Reverse event dating | release month r, after-labels from r; per-RIR counts shifted +1 | after-labels from r+1; no shift, because the server run was relabelled | UTC label convention |
| Q3 window for a release in month r | labels r to r+3 | labels r+1 to r+4 | label M holds changes made in M-1 |
| Q3 pdns-auth[0]@3.2 one-block-or-concentrated | +0.658, p 0.015, era-matched 0.026 | +0.558, p 0.098, era-matched 0.214 | 42 of the 106 old-window delegations changed before the release |
| Q3 pdns-auth[0]@3.2 large-action share | +0.061, p 0.192 | +0.336, p 0.060, era-matched 0.074 | same window change |
| Q3 attribution | one RIPE block of 64 delegations | concentrated signings in labels 2013-01 and 2013-02, 106 delegations, 42 before the release; not one block | verifier section E |
| Q4 aligned spikes | 14 against 9.0 expected | 13 against 9.1 | afrinic SHA-1 DS spike happened in 2021-12, before bind9 d20 |
| Q4 digest1 reverse | 1 of 7 aligned | 0 of 7 | same |
| Q4 zero-iteration wording | the defaults, the IETF draft and RFC 9276 land in eight months; two registry operators | the defaults and RFC 9276 fall within eight months, the draft was public by 2021-10; four TLDs run by two registries, zone operators unidentified | verifier F.2 and F.3 |
| Q5 panel RSASHA1 peak | 103.1% in 2011-05 with 32 delegations; below half in 2014-05, 61 months before RFC 8624 | 50.2% in 2014-08 with 313; below half in 2017-02, 28 months before | peak over months with at least 300 in the denominator |
| Q5 panel SHA-1 DS peak | 100% in 2011-05; below half in 2022-01, 31 months after RFC 8624 | 91.6% in 2014-09 with 379; below half in 2022-05, 35 months after | same |
| Headline | no alignment beyond chance | no lasting departure from trend and no transient deviation beyond chance; the one spike alignment is timing, not attribution | step test |

## Changed from the earlier analysis

- **Release dates.** The earlier documents used `data/software/release_dates.json`, including cvs2git artefacts such as
  BIND 9.3.0 to 9.3.4 on one day. This analysis uses only the verified `released` dates and drops never-public pdns-rec
  tags: 1,325 stable public releases.
- **Seven default changes became 46 mapped rows.** The earlier analysis tested seven defaults, two usable. Of the 154
  verified rows, 46 map to an observable, and 29 have at least one step or transient test. No default change is
  followed by a lasting departure from trend more often than chance predicts.
- **ECDSA defaults.** `docs/releases_vs_adoption.md` reported Knot 2.1.0 and PowerDNS 4.0.0 with slope changes of
  +0.034 and -0.043 on the panel and concluded that neither shows an effect. The step test, which is sensitive to the
  lasting shift a default would cause, puts knot[2] at the 63rd percentile and pdns-auth[7] and [8] at the 57th and
  59th: the algorithm 13 share rose after both, but no faster than its pre-trend predicts.
- **BIND 9.16.0.** The earlier analysis discarded BIND 9.16.0's forward result as a ceiling artefact. Here bind9 d15 is
  tested as opt-in and not applied on upgrade and is inside its band in all four corpora with a step test.
- **The withdrawn OpenDNSSEC 1.2.0 result stays withdrawn.** opendnssec[5] predates the panel's first signed month.
- **Release scan.** `docs/release_scan.md` found no project with a detrended release effect on ledger change counts.
  Its 3-month window of labels r to r+2 includes one month of changes made before the release. Question 1 here uses
  shares, the verified schedules and a step-sensitive statistic, and agrees that nothing exceeds chance.
- **Spike attribution.** `scripts/program_rfc_cases.py` scored spikes against unverified rows and counted a spike as
  release-timed on lag alone. Here alignment is tested against each series' chance rate, with reverse spikes dated to
  the calendar month of the change. The zero-iteration NSEC3 alignment is new.
- **Manual against automatic.** Question 3 restricts the size distribution to transitions that match a signer default
  and tests the calendar months after the release; large actions are not more common then.
- **Shares.** The earlier documents built forward shares from `domains_peak`; this analysis uses `domain_days`.
