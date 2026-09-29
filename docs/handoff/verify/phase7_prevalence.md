# Verification: Phase 7 prevalence extension (DS / DNSKEY / RRSIG)

Verifier: fresh adversarial pass, 2026-09-30. Repo HEAD 5034325c, branch software-timelines-v2. No existing file edited;
recomputation code in /tmp/claude-1000/vP/. Seed 20260929 where randomness is used.

## A. Series — PASS

Own rebuild (`/tmp/claude-1000/vP/a_series.py`): forward ds/dnskey/rrsig_zone as summed `domain_days` of Phase 6's
selectors (rr_type DS, algorithm_dnskey _total, rrsig_type_covered DNSKEY) over rr_type NS; reverse panel
algorithm_ds _total over all/all. No duplicate (source, month, dimension, value) keys in either parquet, so Phase 6's
`groupby().max()` and Phase 7's `pivot_table(aggfunc="sum")` agree.

- 1,609 of my (corpus, source, month, metric) cells match `prevalence_metrics.csv` rows; after 4-decimal rounding the
  largest difference is 0.0, unrounded 4.996e-05 (doc: "5e-05") — matches.
- Of these, 1,411 have peak denominator >= MIN_DEN 30 (ds 603, dnskey 404, rrsig 404; se 273, nu 273, gov 240,
  ee 162, ch 132, li 132, panel 199); fed.us contributes 0. Doc's "1411 months compared" — matches.
- Panel `_pooled-afrinic-arin` carries only dimensions algorithm_ds, all, digest_type_ds, rr_type (DS, NS, _total),
  sha1_signing_ds: no DNSKEY or RRSIG dimension exists, and prevalence_metrics.csv has only `ds_share` for the panel.
  Reverse panel emits DS only — confirmed.

## B. Q2 mapping — PASS WITH CORRECTIONS

Source of rows: `out/analysis/cross_program_defaults_normalised.csv` (154 rows; the timelines' 156 `default_changes`
less pdns-auth [5] and [6], two pre-release intermediate states, dropped in Phase 4). Row text read in
`data/software/timelines/<program>.json`; dump of every non-validator row in `/tmp/claude-1000/vP/rows_nonvalidator.txt`.
Arithmetic of the exclusion file: 144 excluded = 79 validator-only + 45 "parameter of signed zones" + 16 named + 4
"not a default change" (pdns-rec rows with is_default_change False). 10 included rows -> 20 mapping rows.

Corpus coverage matters for whether a mapping choice changes any number: forward series start 2016-06 (se, nu),
2017-05 (gov), 2019-07 (ee), 2020-05 (ch, li); the step test needs 24 months before. So any row dated before
~2018-06 is untestable in the forward corpus and only its ds_prev can be tested on the panel.

### Included rows

| row | verdict | comment |
|---|---|---|
| d06-keygen-no-default-alg (2018-01, -) | keep, but inconsistent with d02 | Plausible (scripts relying on the implicit default stop producing keys), but it is the exact mirror of d02, which is excluded. Either both or neither. Untestable either way (only transient tests), so no number changes. |
| d15-dnssec-policy-default-ecdsap256 (2020-02, +) | keep | Opt-in per zone, applies_on_upgrade False; the most plausible "signing becomes a one-liner" row. DS via ds_prev is a second-order effect (the parent still acts; BIND's check-DS/parental-agents only arrives in 9.16.19). |
| knot[1]@2.0.0 (2015-06, +) | keep | Knot 1.4 already signed automatically with external keys; 2.0 adds internal key generation. Weak +. Only a panel ds_prev test exists. |
| knot[9]@2.7.5 (2019-01, + ds) | keep as weak | Affects only KSKs created by hand with `keymgr generate`; KASP-generated keys are unaffected. The DS still needs the operator or a CDS-scanning parent. Effect on whether a domain has a DS is at most a matter of days for a small subset. |
| knot[10]@2.8.0 (2019-03, - ds) | **exclude** | The before/after text (cds-cdnskey-publish always -> rollover) changes CDS/CDNSKEY publication only *outside* the KSK submission phase. A newly signed zone's first KSK goes through submission, during which CDS/CDNSKEY are still published under `rollover`. So a parent that bootstraps a DS from CDS sees the same records; what disappears is the permanent CDS of zones that already have a DS. The row cannot plausibly lower the share of domains with a DS. The stated reason ("fewer chances for a parent that scans CDS to add a DS") does not follow from the row. Excluding it removes 2 of the 6 step tests outside the band (se 98.3, panel 98.3), both "against expected direction". |
| knot[12]@3.0.2 (2020-11, -) | keep, flag timing | The effect bites only on systems whose crypto policy disables SHA-1, i.e. RHEL 9 (GA 2022-05), and only for RSASHA1/NSEC3RSASHA1 zones. The event month 2020-11 is the release, not the month the effect could occur; a null result at 2020-11 says little. |
| nsd[0], nsd[1], nsd[2], nsd[5] (2004-2010) | keep, minor | Plausible for rrsig_prev. For dnskey_prev less so: DNSKEY is an ordinary RRset NSD serves for a DNSKEY query even without DNSSEC compiled in; only the RRSIGs added under DO depend on it. Also nsd[1] is flagged "on trunk" / opt_in True. All untestable (pre-corpus), so no number changes. |

### Named exclusions (16 in `PREV_EXCLUDED_ROW`)

| row | verdict |
|---|---|
| d02-keygen-default-alg-rsasha1 | inconsistent with including d06 (see above); include with + or drop d06. Untestable (2010-02), no number changes. |
| d08, d09, d10, knot[7] (algorithm removals) | agree. Checked: algorithm_dnskey value 1 peaks at 4 zones (nu), 3 at 3, 6 at 2, 12 absent in every forward TLD. |
| d17-nsec3param-default-in-policy | agree. |
| d22-cdns-cdnskey-options | agree (not a default change). **Missing from the doc's exclusion table**, which lists 15 of the 16. |
| knot[17]@3.4.0 | agree (zone.dnssec-validation is itself opt-in). |
| nsd[3], nsd[4], nsd[6] | agree. |
| opendnssec[2], opendnssec[5] | agree. |
| pdns-auth[0], [7], [8] | agree: the operator still has to secure the zone. |

### Rows in the 45 "parameter" bucket that are in the same failure class as d06 / knot[12]

The inclusion rule for d06 and knot[12] is "a default that makes signing *fail* for some configurations". By that
rule the following excluded rows belong to the same class and are treated inconsistently (direction -):
knot[8]@2.7.0 (RSA keys < 1024 bits rejected), knot[15]@3.2.0 (too-low rrsig-refresh makes zone signing fail),
pdns-auth[9]@4.0.0 (addKey without bits throws for RSA), bind9 l02 (2024-07, dnssec-policy refuses non-zero NSEC3
iterations). I would keep all of them excluded (each is a configuration error the operator fixes, not a lasting change
in signed share) and therefore also exclude d06 and knot[12]; at minimum the doc should state the rule and apply it to
all six. Only knot[12] (2020-11) and l02/knot[15] fall inside testable windows, so this changes Q2 counts slightly.

### Rows the mapping missed

Searched all eight timelines' default_changes and every stable release's changelog entries for auto-dnssec,
inline-signing, dnssec-policy, KASP, CDS/CDNSKEY, "enabled by default", sign-on-load/live-signing, check-DS/ds-push
(`/tmp/claude-1000/vP/grep_entries.txt`, 180 hits). None is a default change the normalised table lacks except one
arguable case:

- **knot 2.5.0 (2017-06-05): CDS/CDNSKEY published by default ("always") under automatic signing.** knot[10]'s own
  `before` text says "default always since 2.5.0/2.6.1". The timeline records it as `support-added`
  (is_default_change False), so it never reaches the normalised table. If knot[10] stays in (as a - for ds_prev), its
  mirror (+ for ds_prev, 2017-06) should be added, or the asymmetry stated. With knot[10] excluded as above, the
  cleaner choice is to exclude both.
- bind9 9.16.3 (2020-05, "inline-signing implied only for non-dynamic zones"), bind9 9.11.0 (automated CDS
  generation, driven by key timing metadata, off unless set), knot 2.8.4/3.2.3 ds-push, knot 3.3.5 mod-authsignal,
  pdns-auth 4.0.5 (publish inactive KSK as CDS): all opt-in or not whether-signed changes; correctly absent.
- kresd 4.0.0 "DNSSEC is enabled by default" is validation, correctly validator-only.

## C. Q1 — numbers PASS; unit of the chance comparison needs CORRECTION

Independent step12 (own least-squares, own window rules) and shift null (`/tmp/claude-1000/vP/c_q1.py`). With the
script's RNG key the five sampled tests reproduce to the printed digit; with an unrelated generator (seed 20260929)
they move by at most 2 percentile points:

| program | series | corpus | window | release months | mean step12 | pct (script key) | pct (own seed) | doc |
|---|---|---|---|---|---|---|---|---|
| nsd | dnskey_prev | gov | 2019-05..2023-01 | 19 | +8.9548 | 98.6 | 97.9 | 98.6 |
| opendnssec | ds_prev | nu | 2018-06..2023-01 | 9 | -1.4537 | 3.4 | 3.8 | 3.4 |
| pdns-rec | ds_prev | se | 2018-06..2023-01 | 30 | +0.1466 | 0.0 | 0.0 | 0.0 |
| unbound | ds_prev | nu | 2018-06..2023-01 | 27 | +0.8446 | 96.1 | 96.2 | 96.1 |
| knot | ds_prev | panel | 2011-03..2025-08 | 116 | +0.0078 | 82.2 | 80.3 | 82.2 (not outside) |

**Aggregate.** 70 tested = 7 programs (BIND 9's every-release cells untestable) x 10 series-cells (ds, dnskey, rrsig in
se, nu, gov; ds on the panel); ee/ch/li never reach 24+12 months. 12 outside; calibrated rate 0.108 -> 7.56 expected;
P(X >= 12 | Bin(70, 0.108)) = 0.071. Matches "7.6" and "about 0.07".

**The 12 come from 5 program-corpus pairs** — confirmed: nsd/gov (3), opendnssec/se (dnskey, rrsig), opendnssec/nu
(3), pdns-rec/se (3), unbound/nu (ds only). Directions: opendnssec and pdns-rec at the 0-4th percentile, nsd and
unbound at the 96-99th. Note pdns-rec's *mean* step is positive (+0.15 to +0.20) but below every shifted schedule;
the doc's "below nearly every shifted schedule" is correct, a reader of the "+0.2" column may misread it.

**Does counting ds/dnskey/rrsig separately inflate the count? Yes.** In se/nu/gov the three series are the same
signed-zone count over the same NS denominator (DNSKEY and RRSIG(DNSKEY) within 0.5%, DS a few points lower), so one
release schedule tested on all three is one test counted three times; every flagged pair except unbound/nu is flagged
in 2 or 3 of its series. A binomial on 70 treats them as independent and overstates the evidence. The right unit is
**program x corpus** (7 x 4 = 28), one series per unit:

| unit | units | outside | expected (0.108) | P(X >= k) |
|---|---|---|---|---|
| program x series-cell (doc) | 70 | 12 | 7.56 | 0.071 |
| program x corpus, ds_prev only (only series defined in all four corpora) | 28 | 4 | 3.02 | 0.36 |
| program x corpus, dnskey (forward) + ds (panel) | 28 | 4 | 3.02 | 0.36 |
| program x corpus, flagged if any of its series is outside | 28 | 5 | >= 3.02 (the any-of-three null rate is above 0.108) | >= 0.18 (0.18 at rate 0.108; larger at the true, higher rate) |

At the correct unit Q1 is at chance (4 of 28 against 3.0, P = 0.36). Even this is optimistic about independence: se
and nu are run by one registry and share the 2018-12..2019-02 break described under D, and the programs' schedules
are tested against the same four series.

## D. Q2 — numbers PASS; interpretation needs CORRECTION

Recomputed with `/tmp/claude-1000/vP/d_q2.py` (own step12, own placebo draw; script RNG key reproduces exactly, an
unrelated generator agrees within 1.4 pct points and on every outside flag):

| row | series | corpus | step12 | pct | outside | before mean | after mean | pre-trend slope pp/mo | extrapolated after-mean |
|---|---|---|---|---|---|---|---|---|---|
| d15 | ds_prev | nu | -4.381 | 0.0 | yes | 36.91 | 47.43 | +0.83 | 51.82 |
| d15 | dnskey_prev | nu | -9.931 | 1.3 | yes | 43.28 | 55.32 | +1.22 | 65.25 |
| d15 | rrsig_prev | nu | -9.892 | 2.0 | yes | 43.25 | 55.32 | +1.22 | 65.21 |
| knot[9] | ds_prev | se | +3.976 | 87.8 | no | | | | |
| knot[9] | ds_prev | nu | +8.898 | 94.2 | no (hi 9.076) | | | | |
| knot[9] | ds_prev | panel | +0.0722 | 98.3 | yes | | | | |
| knot[10] | ds_prev | se | +4.877 | 98.3 | yes | | | | |
| knot[10] | ds_prev | nu | +6.173 | 82.8 | no | | | | |
| knot[10] | ds_prev | panel | +0.0787 | 98.3 | yes | | | | |

Aggregate (`/tmp/claude-1000/vP/d_q2agg.py`): 23 tests, 6 outside, discrete expectation 3.13, Poisson-binomial
P(X >= 6) = 0.082; 1 in the expected direction (knot[9] panel). All match the doc.

**d15 in .nu: "the extrapolation overshoots" — correct, but the cause is not stated and it is not a separate
movement.** .nu DS prevalence was 44.9% in 2020-01 and rose ~0.5 pp/month afterwards: no drop. The pre-window
2018-02..2020-01 contains a jump in 2018-12..2019-02 (33 -> 39%), which inflates the fitted slope to 0.83 pp/month.
That jump is not new signing: over 2018-10..2019-02 the .nu NS denominator falls from 363,900 to 232,995 (-36%) and
the DS count from 127,794 to 92,722 (-27%); prevalence rises because unsigned names leave the measured set. .se shows
the same break: NS 1,571,232 -> 1,338,823, and DS share dips to 44.98% (2018-12) and 43.68% (2019-01) before
returning to 50.74% (2019-02). In both TLDs the extreme step12 months cluster at exactly the windows that straddle this
break (.nu: 2018-09..11 high, 2020-01..03 low; .se: 2019-02..03 high). d15 (2020-02 in .nu) and knot[10] (2019-03 in
.se) sit on those months. So four of the six outside tests (d15 nu x3, knot[10] se) are produced by one 2018-12..2019-02
denominator break in the IIS-run TLDs, and the other two (knot[9], knot[10] on the panel) by one panel rise in label
2019-06 (0.249 -> 0.313%). The doc's "the six are three movements" should be "two movements, one of them a
denominator artifact"; "knot[9] in .nu at 94.2" is also driven by the break.

**knot[9] and knot[10] share one window — confirmed.** Event months 2019-01 and 2019-03: step12 pre-windows
2017-01..2018-12 and 2017-03..2019-02 share 22 of 24 months, after-windows 2019-01..12 and 2019-03..2020-02 share 10 of
12 (panel labels shifted by one, same overlap). Both panel tests land at 98.3 on the same rise. The doc's "the same rise
cannot support both readings" is correct. Separately, knot[10] should not be mapped at all (section B); without it Q2
is 4 of 20 outside against 2.73, P = 0.29.

## E. Q4 — PASS

Independent spike rule and chance rate (`/tmp/claude-1000/vP/e_q4.py`): 59 spikes (identical set to the script's),
3 aligned, 3.18 expected. The three: .se DS 2019-02 after knot[9] (lag 1), APNIC DS calendar 2019-01 after knot[9]
(lag 0), ARIN DS calendar 2020-05 after d15 (lag 3). Per-cell table matches the doc. Other checks of the prose: .ch
2021-06..12 +669,731 to +696,817, .li, .se/.nu 2017-11 and RIPE 2015-09 (label 2015-10) have no relevant default within
12 months (lags 16, 29, none); 33 reverse spikes, 31 "mostly new signings", 2 "mostly unsignings" — all confirmed.

Caveat the doc omits: the aligned .se DS spike of 2019-02 (+129,644) is the recovery from the -135,404 dip of 2019-01
(the break above), not a rise; a spike rule on counts sees a one-month measurement dip as two spikes. Alignment is at
chance anyway, so the conclusion stands, but it should not be listed as an aligned rise.

### Addendum to C: the .gov cells measure a denominator break, not releases

`/tmp/claude-1000/vP` check: .gov's NS denominator jumps from 1,234 (2018-01) to 5,553 (2018-02) and DS prevalence
from 88.7% to 31.2% then 21.4%. Every step12 whose 24-month pre-window contains that break (event months 2019-05 to
2020-02) is large and positive, decaying from +45.8 to +1.5 pp; from 2020-03 on it is between -1.0 and 0. The .gov
step12 90% band is -0.9 to +42.9 pp. A program's .gov mean therefore depends only on what share of its release months
fall in 2019-05..2020-01: NSD has 5 of 19 (26%) against 20% for the window; that is its whole 98.6th-percentile
result. So 3 of the 12 Q1 "outside" tests (NSD .gov) are produced by the 2018-02 .gov break, and the doc's "a series
that jumps by tens of points" understates it. The .gov cells should be dropped from Q1/Q2, or the .gov series started
at 2018-03. With .gov dropped, the Q1 unit count is 7 x 3 = 21 program x corpus units, ds_prev: 3 outside
(opendnssec/nu, pdns-rec/se, unbound/nu) against 2.27, P(X >= 3 | Bin(21, 0.108)) = 0.40.

## F. Wording — CORRECTIONS

Sentences in the short answer and the new section that claim more or less than the numbers show:

1. Short answer, "12 of 70 step tests against 7.6 expected, from only 5 program and corpus pairs with mixed
   directions" and section Q1 "Treated as independent, 12 or more has a chance of about 0.07". Numbers correct, but the
   comparison is at the wrong unit and the doc never gives the right one. At program x corpus it is 4 of 28 against
   3.0 (P = 0.36); dropping the .gov break, 3 of 21 against 2.3 (P = 0.40). Leaving only "P about 0.07" makes Q1 read
   as borderline evidence, which it is not.
2. Short answer, "So neither releases nor defaults are shown to move how many domains are signed." The conclusion is
   right, and "not shown to move" is the right summary. But the support the doc gives for it (12/70 at P 0.07, 6/23 at
   P 0.08) makes it look close to a positive finding. It should rest on the unit-corrected counts and on the artifacts
   in items 5 and 6. Also "how many domains are signed" should be "the share of domains that are signed". The
   prevalence moves in question are share moves from shrinking denominators (.nu -36% NS in 2018-10..2019-02, .gov
   x4.5 in 2018-02), with no domain signed.
3. Short answer, "Both are absences of detection within the power limits stated below." The power limits
   (`software_vs_adoption_power.csv`) cover only alg13 .se, alg13 panel and digest1 .nu. No prevalence series was
   power-tested (0 prevalence rows in that CSV). The prevalence step12 90% bands are -2.9..+4.4 pp (.se DS),
   -4.2..+8.9 pp (.nu DS), -0.9..+42.9 pp (.gov) and -0.05..+0.06 pp (panel, on a 0.2-0.3% level). A lasting shift
   smaller than about 5 pp in .se or 9 pp in .nu is inside chance, and .gov has no usable power.
4. Section intro, "Forward DNSKEY and RRSIG prevalence move almost together ... counts below are of tests". True, but
   DS moves with them too (the same zones, with or without a DS at the parent), and the doc then compares counts of
   tests to a per-test expectation anyway. The chance comparison should be per program x corpus (C).
5. Q1, "NSD's .gov result rests on 19 release months in a 45-month window of a series that jumps by tens of points."
   This understates the problem. The .gov step series is the 2018-02 denominator break (C addendum), and the NSD result
   is 5 of 19 release months falling in the 9 break-affected months.
6. Q2, "But the six are three movements". They are two: four (d15 .nu x3, knot[10] .se) come from the 2018-12..2019-02
   denominator break in .se/.nu, and two (knot[9], knot[10] panel) from the panel rise at label 2019-06. The d15 bullet
   ("the steep rise before predicted more, so the extrapolation overshoots") is correct as mechanics, but the "steep
   rise" is that break (.nu NS 363,900 -> 232,995, DS count 127,794 -> 92,722), not signing growth.
7. Q2 knot[10] reason, "fewer chances for a parent that scans CDS to add a DS". This does not follow from the row: under
   `rollover` CDS/CDNSKEY is still published during the KSK submission phase, which is when a parent could add the
   first DS. The row should be excluded (B). Without it Q2 is 4 of 20 against 2.73, P = 0.29, 1 in the expected
   direction.
8. Q2 exclusion table, "Candidate rows considered and excluded". It lists 15 rows. `PREV_EXCLUDED_ROW` and the CSV
   have 16 (d22-cdns-cdnskey-options is missing). "The other excluded rows are 79 validator-only rows and 45 rows ..."
   omits the 4 pdns-rec rows excluded as "not a default change" (79 + 45 + 16 + 4 = 144).
9. Q4, "The aligned three are .se DS in 2019-02 after knot[9] ...". The .se DS "spike" of 2019-02 (+129,644) is the
   recovery from the 2019-01 dip (-135,404), not a rise. The count 3 against 3.2 is unchanged, but it should not be
   presented as an aligned rise.
10. Mapping consistency: d06 is included and d02 excluded, though they are mirror images. d06 and knot[12] are included
    as "signing fails" defaults, while knot[8], knot[15], pdns-auth[9] and bind9 l02 of the same class are excluded.
    knot[12]'s effect can only occur from RHEL 9 (2022-05), not at its 2020-11 release. No step count changes except
    through knot[12] (0 of 6 outside), so this is wording and consistency.

Correct as written: the 1,411-month Phase 6 identity; "transient 9 of 128 against 12.8"; "BIND 9 x.y.0 0 of 10";
"6 of 23 against 3.1, 1 in the expected direction"; "P about 0.08"; the knot[9]/[10] shared-window caveat;
"59 spikes, 3 aligned against 3.2"; the Q4 lags and ledger compositions; "Not tested ... 72 ... 10" (176 = 70 + 24
fed.us + 72 ee/ch/li + 10 BIND 9); feature CSVs are byte-identical prefixes of the HEAD~1 files (q1, q1_releases, q2,
q4 checked with `cmp`).

## Verdict: PASS WITH CORRECTIONS

Every number the extension prints reproduces independently: the series, the 5 sampled Q1 tests, the Q2 d15/knot
tests, the aggregates and Q4. The conclusion "prevalence is not shown to move" holds, and holds more firmly than the
doc says. What needs correcting: the chance comparison is made at an inflated unit, one mapped row (knot[10]) does not
fit its own reason, three denominator breaks (.gov 2018-02, .se/.nu 2018-12..2019-02) produce most of the "outside"
results without being named, and the power statement does not cover prevalence.

| item | doc | recomputed | status |
|---|---|---|---|
| prevalence months compared | 1411, max diff 5e-05 | 1411, 4.996e-05 | match |
| Q1 step12 outside / tested | 12 / 70, 7.6 exp, P~0.07 | 12 / 70, 7.56, P=0.071 | match (wrong unit) |
| Q1 at program x corpus (ds_prev) | not given | 4 / 28, 3.02, P=0.36 | correction |
| Q1 program x corpus, .gov dropped | not given | 3 / 21, 2.27, P=0.40 | correction |
| Q1 transient3 | 9 / 128 vs 12.8 | not recomputed (aggregate read) | - |
| Q2 step12 outside / tested | 6 / 23, 3.1, P~0.08, 1 expected-dir | 6 / 23, 3.13, P=0.082, 1 | match |
| Q2 without knot[10] | - | 4 / 20, 2.73, P=0.29 | correction |
| Q2 d15 .nu ds/dnskey/rrsig | -4.38/0.0, -9.93/1.3, -9.89/2.0 | same | match |
| Q2 knot[9]/[10] panel | 98.3 / 98.3 | same; windows share 22/24 pre, 10/12 post | match |
| Q4 spikes / aligned / expected | 59 / 3 / 3.2 | 59 / 3 / 3.18 | match |

## Required corrections

Proof scripts are in `/tmp/claude-1000/vP/`. Run them with the scratchpad venv python.

1. `docs/handoff/07_software_vs_adoption.md`, short answer and Q1 paragraph. Current: "12 of 70 ... 7.6 expected",
   "about 0.07". Correct: keep those numbers and add the program x corpus comparison, 4 of 28 against 3.0, P = 0.36
   (3 of 21 against 2.3, P = 0.40 without .gov). Proof: `python /tmp/claude-1000/vP/c_q1.py` (last two lines), and
   for 21 units `from binom import sf; sf(3,21,0.108)`.
2. Same file, Q1 NSD sentence. Current: ".gov ... a series that jumps by tens of points". Correct: the .gov NS
   denominator goes from 1,234 to 5,553 in 2018-02 and DS share from 88.7% to 31.2%. step12 is +45.8 to +1.5 pp for
   event months 2019-05..2020-02 and about 0 afterwards, so NSD's 98.6 reflects 5 of its 19 release months falling in
   those 9 months. Drop the .gov cells or start .gov at 2018-03. Proof: the .gov snippet in the C addendum
   (`series('ds_prev','gov')`, `step()` from `/tmp/claude-1000/vP/common.py`).
3. `scripts/software_vs_adoption.py` `PREV_ROW_MAP["knot[10]@2.8.0"]` and the Q2 table. Current: included, "-" for
   ds_prev. Correct: exclude, because under `rollover` CDS/CDNSKEY is still published during KSK submission. Then Q2
   step12 is 4 of 20 against 2.73, P = 0.29, and the Q4 "-" chance rates change slightly. Proof:
   `python /tmp/claude-1000/vP/d_q2agg.py` (line "without knot[10]").
4. Doc, Q2 "the six are three movements". Correct: two movements. Four tests (d15 .nu x3, knot[10] .se) come from
   the .se/.nu denominator break of 2018-12..2019-02 (.nu NS 363,900 to 232,995, DS count 127,794 to 92,722; .se DS
   share 44.98/43.68 in 2018-12/2019-01, back to 50.74). Two (knot[9], knot[10] panel) come from the panel rise at
   label 2019-06. Name the break in the d15 bullet. Proof: the se/nu table snippet in section D, and
   `python /tmp/claude-1000/vP/d_q2.py`.
5. Doc, short answer, "within the power limits stated below". Correct: no prevalence series was power-tested. State
   the step12 90% bands instead: .se DS -2.9..+4.4, .nu DS -4.2..+8.9, .gov -0.9..+42.9 pp. Proof:
   `grep -c prev out/analysis/software_vs_adoption_power.csv` gives 0; bands from the F snippet.
6. Doc, short answer, "how many domains are signed". Correct: "the share of domains that are signed", with a note
   that the largest share moves in the tested windows come from shrinking denominators. Proof: as 2 and 4.
7. Doc, Q2 exclusion table. Current: 15 rows, and "79 validator-only rows and 45 rows". Correct: add
   d22-cdns-cdnskey-options (16 rows) and the 4 pdns-rec "not a default change" rows (79 + 45 + 16 + 4 = 144). Proof:
   `python -c "import pandas as pd;e=pd.read_csv('out/analysis/software_vs_adoption_prevalence_excluded.csv');print(len(e),e.reason.str[:30].value_counts())"`.
8. Doc, Q4, "The aligned three are .se DS in 2019-02 after knot[9]". Correct: the 2019-02 +129,644 spike is the
   recovery from the 2019-01 dip of -135,404; say so. The count of 3 against 3.2 stands. Proof:
   `python /tmp/claude-1000/vP/e_q4.py` and the spike table (n=10 and n=9 in the JSON).
9. `PREV_ROW_MAP` / `PREV_EXCLUDED_ROW` consistency. Current: d06 is in and d02 out; d06 and knot[12] are in while
   knot[8], knot[15], pdns-auth[9] and l02 are out. Correct: one rule for all of them (preferably exclude the
   "configuration now fails" class). If knot[12] stays, note that its effect can only begin with RHEL 9 (2022-05).
   Optionally add knot 2.5.0's default-always CDS publication as knot[10]'s mirror, or state the asymmetry. Proof:
   `/tmp/claude-1000/vP/rows_nonvalidator.txt` and `/tmp/claude-1000/vP/grep_entries.txt`.
