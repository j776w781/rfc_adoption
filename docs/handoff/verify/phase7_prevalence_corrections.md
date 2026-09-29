# Verification: Phase 7 prevalence corrections (commit 396ddbc9)

Verifier: fresh adversarial pass, 2026-09-30, branch software-timelines-v2, HEAD 396ddbc9. No existing file was edited
and nothing was written under out/analysis. The recomputation scripts are in `/tmp/claude-1000/vP2/`. Where a script
imports `scripts/software_vs_adoption.py`, its `save`, `write_csv` and `append_csv` are disabled. Python:
scratchpad venv.

## Scope

I checked the commit's script diff, the doc's short answer and its "Adoption as prevalence" section, and these JSON
keys: `notes.measurement_breaks`, `q1…prevalence.aggregate.unit_program_x_corpus`, `q1…prevalence.break_sensitivity`,
`q1…break_sensitivity_feature`, `q2…prevalence.{unit_row_x_corpus, break_sensitivity, detection_power, step12_bands}`,
`q2…break_sensitivity_feature` and `q4_spikes.prevalence.summary`. Feature results are unchanged: the feature rows of the
q1, q1_releases, q2, q4 and q4_alignment CSVs, and every non-prevalence JSON key, are identical to 396ddbc9~1.

## 1. Unit counts: PASS

`g_units.py` uses its own step statistic, its own window and occupancy rules, and its own circular-shift null on
`ds_prev`. `i_q2.py` uses its own placebo draw and a Poisson-binomial tail.

| unit | doc | recomputed |
|---|---|---|
| Q1 program x corpus, ds_prev | 4 / 28, 3.0, P 0.36 | 4 / 28, 3.02, P 0.358: nsd .gov 97.7, opendnssec .nu 3.4, pdns-rec .se 0.0, unbound .nu 96.1 |
| same, without .gov | 3 / 21, 2.3, P 0.40 | 3 / 21, 2.27, P 0.399 |
| Q2 row x corpus | 2 / 8, 1.05, P 0.28 | 2 / 8, 1.0496, P 0.283: d15 .nu 0.0, knot[9] panel 98.2 to 98.3 |
| Q2 breaks masked | 1 / 3, 0.34, P 0.31 | 1 / 3, 0.345, P 0.307. All three units left are on the panel. |

Stability across seeds: over 20 unrelated seeds, all four Q1 units are flagged every time. opendnssec .se (ds_prev,
p = 0.112 with the script's key) is flagged in 45% of seeds. At 5 of 28, P would be 0.18, so the conclusion does not
change.

## 2. Measurement breaks: windows correct; one comparable break missing; the sensitivity is confounded

**The three named windows are real and correctly bounded** (`b2.py`):

- .gov: NS peak 1,234 to 5,553 in 2018-02. DS share 88.70, then 31.20, then 21.35, then flat at about 21.1.
- .nu: NS peak 413,121 (2018-09), 363,900 (2018-10), 289,684 (2018-12), 232,995 (2019-02), then flat. DS share 33.1
  to 39.1, and smooth after that.
- .se: NS peak 1,621,745 (2018-09) to 1,338,823 (2019-01). DS share 44.98 and 43.68, back to 50.74 in 2019-02 and
  52.65 in 2019-03, flat after that.

Every number in the three descriptions matches the data.

**The mask is exact** (`l_mask.py`). For se, nu, gov and ee, on ds_prev and alg13, and for step12, transient3 and
transient12, the cells `apply_break_mask` sets to NaN are exactly the events whose window [k-before, k+after-1]
overlaps [first-1, last]. Nothing else changes. In .se and .nu, step12 events 2018-06..2021-02 are dropped (33); in
.gov, 2019-05..2020-03 (11). Q2 placebos are drawn from the testable months and Q1 shifted months that land on NaN
are dropped, so placebos in break windows are dropped as well.

**Scan of every source** (`b_breaks.py`) for month-on-month changes above 10% in the peak denominator: rr_type NS
for the forward sources, all/all for the panel.

- Forward:
  - gov 2018-02 (+350%).
  - nu 2017-02 (+12.6%), **2017-09 (+17.3%), 2017-11 (+17.5%)**, 2018-10 (-11.9%), 2018-12 (-20.6%), 2019-02 (-17.3%).
  - No month-on-month move in .se passes 10% (its 2018 break is -3 to -9% a month, -17% in total). ee, ch and li
    only have their partial first month.
  - The domain_days jumps of 10 to 17% every March (month length) are not population changes. Neither is .gov
    2021-04..06, a coverage gap: the peak is flat and the share is 19.4, 19.3, 19.2.
- Panel `_pooled-afrinic-arin`: no month above 10%. Afrinic alone: 2010-02, 2011-07, 2014-05, 11 to 14%, all before
  or at the panel's start. RIPE reverse 2015-10 (-97%) is not in the panel.

**Missing break: .nu 2017-06..2017-12.** The NS peak goes 281,539 (2017-05), 304,769, 356,341 (2017-09), 430,784
(2017-11), 466,775 (2017-12), which is +66%. The DS peak stays flat, 86,803 to 86,406, through 2017-10, and DS share
falls from 31.7 to 24.2 with no domain unsigned. That is -7.5 pp, the same size as the listed .nu break (+6.0 pp).
The 2017-11 DS jump (+39k) is real signing and is the Q4 spike. .se shows a smaller copy: NS +19.5% over
2017-08..12, share 48.0 to 45.3.

- This does not change any step12 number, because every step12 event whose window touches 2017 is already masked by
  the 2018 window.
- It does change the transient sensitivity. With nu 2017-06..12 and se 2017-08..12 added, Q1 prevalence transient3
  masked goes from 13 to 18 of 134 (`m_extra.py`).
- It also enters the headline pre-trends of the .nu step tests for event months 2018-06..2019-12.

**Transient masks ignore the detrend.** transient3 and transient12 are computed on a series detrended by a centred
25-month rolling median. A break up to 12 months outside the window still reaches the statistic through the trend.
This is minor, because these are the secondary tests.

**The 12-month minimum is a confound, and it is disclosed only in part.** The doc says the sensitivity uses 12 months
instead of 24 because masking leaves 23 step months in .se and .nu. It does not say that the lower minimum also admits
.ee, which has 19 step months, no break, and was excluded from every headline by the 24-month rule. Decomposition
(`f_decomp.py`, `g_units.py`):

| count | headline (min 24, no mask) | min 12, no mask | min 12, masked (committed) | min 24, masked |
|---|---|---|---|---|
| Q1 prevalence units, ds_prev | 4 / 28 (P 0.36) | 6 / 35 (P 0.17) | 4 / 35 (P 0.53) | 1 / 14 (P 0.80) |
| Q1 prevalence per-test step | 12 / 70 | 18 / 91 | 11 / 91 | 2 / 28 |
| Q1 feature per-test step | 7 / 76 | 10 / 96 | 14 / 96 | 3 / 28 |
| Q2 feature per-test step | 7 / 68 | 9 / 74 | 5 / 49 | 1 / 23 |
| Q2 prevalence units | 2 / 8 | 2 / 8 | 1 / 3 | 1 / 3 |

All the tests added by the masked run are .ee: 7 Q1 prevalence units (2 outside, knot .ee and nsd .ee), 21 Q1
prevalence tests, 20 Q1 feature tests (3 outside, Knot alg13, alg5_7 and alg8 in .ee), and 6 Q2 feature tests (2
outside, knot[14] .ee and pdns-auth[10] .ee). The JSON `*_breaks_masked` entries do not record the minimum used.

## 3. Feature-family break sensitivity: numbers PASS; wording needs correction

- Q1: 7 / 76 becomes 14 / 96. Expected 96 x 0.108 = 10.37; P(X >= 14 | Bin(96, 0.108)) = 0.151.
- Q2: 7 / 68 becomes 5 / 49. Expected (discrete) 9.17 becomes 8.04, P 0.83 and 0.92. Without .ee, 3 / 43.

Three sampled tests, recomputed with my own step, mask and shift null on the script's series (`j_feat.py`):

| test | base, script key / own seed | masked, script key / own seed | JSON |
|---|---|---|---|
| Q1 pdns-auth alg13 .se | 100.0 / 100.0 (L 56, 21 months) | 25.0 / 25.0 (2021-03..2023-01, 9 months) | 100.0 to 25.0 |
| Q1 knot iter0 .nu | 93.3 / 95.0 | 100.0 / 100.0 (17 of 23 months) | 93.3 to 100.0 |
| Q1 pdns-auth optout .se | 0.0 / 0.0 | 48.1 / 46.7 | 0.0 to 48.1 |
| Q2 bind9 d21 iter0 .se | 98.4 / 98.1 | 94.7 / 96.9 (22 placebos, 1 above) | 98.4 to 94.7 |

All four reproduce with the script's key. d21 in the masked run depends on the draw: with 22 placebos and 1 above
the statistic, another seed puts it outside.

**Wording.** "Four of the seven headline results do not survive" and the percentiles (25 to 48; ODS alg7 .gov 93.4)
are correct. "New outside results appear in their place, most of them Knot in .se and .nu" is incomplete. Of the 11
new outside results, 10 are Knot: .se 3, .nu 2, .gov 2 and .ee 3. The three .ee results come from the lower minimum,
not from masking; the eleventh is Unbound iter_gt150 .se. The masked Knot tests in .se and .nu sit on 23-month
windows at 74% release occupancy, just under the 75% cap, which leaves 22 shift offsets.

"At chance with or without them" is defensible (P 0.15), but it should give that P and the .ee confound. Compared on
the same tests, masking raises the Q1 feature count from 10 to 14 of 96. The feature result is stable in number but
not in which tests are outside.

## 4. Mapping: PASS, with minor label inconsistencies

- Mapping CSV: 7 rows, 11 row-observables. Exclusion CSV: 147 rows (79 validator, 41 parameter, 6 fails-class, 4
  not-a-default, 17 other named). No overlap between the two files, and together they cover all 154 normalised rows.
  The doc's arithmetic 79 + 41 + 27 = 147 is correct.
- The fails rule is applied to d06, knot[8], knot[12], knot[15], pdns-auth[9] and l02, and every row of that class is
  excluded. Two rows in the "parameter" bucket fit the same class by their own after-text but carry the parameter
  label: knot[19]@3.6.0 ("NSEC3PARAM with more [than 256] iterations refused") and pdns-auth[3]@3.4.0 ("set-nsec3
  above the cap throws"). No number changes.
- l02's parenthetical, "dnssec-policy and signzone refuse iterations above 50", misstates the timeline. The row title
  says dnssec-signzone's limit is lowered to 50 and that "dnssec-policy additionally refuses to load any non-zero
  iteration count".
- knot[10] exclusion: agreed. The reason matches the row text and names the Knot 2.5.0 mirror.
- NSD restricted to rrsig_prev: this is consistent with the timeline text. nsd[0] reads "RRSIG/NSEC added to answers
  when DO is set" and nsd[5] "--disable-dnssec builds a server that ignores DO/RRSIG". No row says DNSKEY serving
  depends on the build. "NSD serves an ordinary DNSKEY RRset" is domain knowledge (RFC 3597-style serving) that
  the text does not contradict. All four rows are 2004-2010 and untestable, so no number depends on it.

## 5. Power: PASS

`h_power.py` checks .se ds_prev at 2021-06:

| step h | statistic | percentile, script key / own seed | share of 56 event months above the band (JSON / own seed) |
|---|---|---|---|
| 0 | 2.770403 | 67.7 / 68.0 | 0.071 / 0.054 |
| 2 | 4.770403 | 96.7 / 97.7 | 0.286 / 0.286 |
| 5 | 7.770403 | 100.0 / 100.0 | 0.411 / 0.429 |
| 10 | 12.770403 | 100.0 / 100.0 | 0.893 / 0.929 |

The statistics are exact, and the percentiles and shares agree within the difference between seeds.

.se step12 bands:

- All 56 testable months (2018-06..2023-01): -2.874402 .. 4.428337.
- Masked, 23 months (2021-03..2023-01): -3.219018 .. 3.469842.

Both match `step12_bands` exactly.

## 6. Q4: PASS, but the doc paragraph is not rendered

- An independent dip-reversal flag on the JSON spike table finds 2 reversals, identical to the script's: .se DS
  2019-02 (+129,644 after -135,404) and ARIN DS 2013-01 (+48 after -44).
- Aligned spikes: 3 / 59 against 2.7002, and 2 / 57 against 2.5511 once the two reversals are dropped. Matches
  `summary`.
- The CSV `software_vs_adoption_q4.csv` has no `reverses_dip_within_2m` column, because `append_csv` runs before
  `mark_dip_reversals`. The JSON has the column.
- **Doc lines 1266-1272 are unrendered f-string placeholders**, for example `{PJ4['summary']['spikes']}` and
  `{PJ4['summary']['expected_aligned']:.1f}`. The published paragraph has no numbers.

## 7. Wording

In the short answer and the prevalence section, these sentences claim more or less than the numbers show:

- a. Short answer: "can miss a lasting step smaller than about 5 pp in .se or 9 pp in .nu". The 5 and 9 are the step12
  band edges, not detection thresholds, and the sentence implies larger steps are caught. The power table shows
  otherwise. In .se a 5 pp step is above the band at 41% of event months and 10 pp at 89%. In .nu a 10 pp step is
  missed at the chosen month (86.8th percentile) and caught at only 39% of months. The last sentence of the power
  paragraph has the same problem in a milder form.
- b. Q1: "The per-test step count of 12 is 4 program and corpus units counted up to three times." In fact 12 = nsd
  .gov 3 + opendnssec .nu 3 + pdns-rec .se 3 + opendnssec .se 2 (dnskey and rrsig; its ds_prev is at 5.6, inside the
  band) + unbound .nu 1. That is 5 pairs; the 4 ds_prev units carry 10 of the 12.
- c. Q1: "the units outside change entirely, to Knot in .ee and .nu, NSD in .ee and OpenDNSSEC in .gov: the earlier
  outside units depended on windows that straddle a break". Two of the four new units are .ee, admitted by the
  12-month minimum and unrelated to any break (section 2).
- d. Q2 knot[9] bullet: "the only unusual prevalence result that survives the break sensitivity". In the Q1 masked
  run, knot .nu (0.0) and opendnssec .gov (97.4) are outside too. It is the only *question 2* result that survives.
- e. "Three months-long changes in the measured population" leaves out the .nu 2017-06..12 change of the same size.
- f. Q2 d15 bullet: "from 2018-10 to 2019-02 the .nu NS denominator fell from 413,121". 413,121 is the 2018-09 value.
- g. Short answer: "Prevalence spikes line up with those defaults 3 times against 2.7 expected". This is correct, but
  one of the three is the .se dip reversal. Adding "2 of 57 against 2.6 without the dip reversals" would match the
  section.

Correct as written:

- the 4/28, 3/21, 2/8 and 1/3 statements;
- ".gov ... 21.3%";
- the .nu and .se break descriptions;
- the NSD .gov sentence (+45.8 to +1.5 pp for event months 2019-05..2020-02; 5 of 19 release months);
- the power table and "In .nu not even 10 pp is detected at half of them";
- the Q2 per-test 4 of 14 against 1.9;
- the 147-row arithmetic;
- the Q2 feature details (d21 94.7; knot[14], l01 and knot[1] stay outside; knot[8] .nu untestable).

## Verdict: PASS WITH CORRECTIONS

Every number the commit prints reproduces independently: the unit counts, the Q2 units, the power row, the bands, the
mask and the Q4 reversal counts. The conclusion, that prevalence is not shown to follow releases or defaults, holds. What
needs correcting:

- an unrendered Q4 paragraph;
- a power sentence in the short answer that states band edges as detection limits;
- a break sensitivity whose 12-month minimum also brings in .ee, which the doc reads as a break effect;
- one comparable break (.nu 2017) left out;
- a few sentences that overstate or miscount.

| item | doc / JSON | recomputed | status |
|---|---|---|---|
| Q1 units ds_prev | 4/28, 3.0, P 0.36 | 4/28, 3.02, P 0.358 | match |
| Q1 units without .gov | 3/21, 2.3, P 0.40 | 3/21, 2.27, P 0.399 | match |
| Q1 units masked | 4/35, 3.8, P 0.53 | 4/35; min-12 unmasked 6/35 (P 0.17); min-24 masked 1/14 | numbers match, reading confounded |
| Q2 units | 2/8, 1.05, P 0.28 | 2/8, 1.0496, P 0.283 | match |
| Q2 units masked | 1/3, 0.34, P 0.31 | 1/3, 0.345, P 0.307 (all panel) | match |
| Q1 feature masked | 14/96 vs ~10.4 | 14/96, 10.37, P 0.151; 20 of 96 are .ee (3 outside); unmasked at min 12: 10/96 | numbers match, reading confounded |
| Q2 feature masked | 5/49 | 5/49, expected 8.04, P 0.92; 6 .ee tests (2 outside) | match |
| Break mask | overlap [first-1, last] | exact for all three stats | match |
| Breaks listed | 3 | 3 correct, plus .nu 2017-06..12 (+66% NS, -7.5 pp) missing | correction |
| Power .se 2021-06 | 2.770/4.770/7.770/12.770; 67.7/96.7/100/100 | identical | match |
| Bands .se | -2.874..4.428; masked -3.219..3.470 | identical | match |
| Q4 | 3/59 vs 2.70; 2 reversals; 2/57 vs 2.55 | identical | match; doc paragraph unrendered |
| Mapping | 7 in, 147 out | 7 + 147 = 154, no overlap | match; 2 label inconsistencies |

## Required corrections

Proof scripts are in `/tmp/claude-1000/vP2/`; run them with the scratchpad venv python.

1. `docs/handoff/07_software_vs_adoption.md`, lines 1266-1272 (Q4 prevalence).
   - Current: `{PJ4['summary']['spikes']}` and five more placeholders.
   - Correct: "gives 59 spikes. 3 have a relevant prevalence default within 3 months before them, against 2.7
     expected ... 2 spikes only reverse ... Without them it is 2 of 57 against 2.6."
   - Proof: `grep -n PJ4 docs/handoff/07_software_vs_adoption.md` and `q4_spikes.prevalence.summary`.
2. Same file, short answer.
   - Current: "The prevalence tests can miss a lasting step smaller than about 5 pp in .se or 9 pp in .nu".
   - Correct: "In .se a lasting 2 pp step is detected at a favourable month, but only a 10 pp step at most event
     months (5 pp at 41%); in .nu not even 10 pp (39% of months, missed at the chosen month); .gov has no usable
     power; on the panel about 0.1 pp."
   - Also soften the last sentence of the power paragraph: steps above the band edges are often missed too.
   - Proof: `q2_default_change_events.prevalence.detection_power.rows`; `python h_power.py`.
3. Same file, the "Measurement breaks" paragraph, the Q1 masked row and paragraph, and "Do the breaks drive feature
   results too".
   - Current: the 12-month minimum is justified by the 23 masked months only, and the new .ee units and tests are read
     as break effects ("the earlier outside units depended on windows that straddle a break"; "most of them Knot in
     .se and .nu").
   - Correct: say that the 12-month minimum also admits .ee (19 step months, no break).
     - Q1 prevalence: 7 of 35 units and 2 of 4 outside are .ee. On the same 35 units without masking the count is
       6 (P 0.17); masked at min 24 it is 1 of 14 (opendnssec .gov).
     - Q1 feature: 20 of 96 tests (3 outside) are .ee. The same 96 unmasked give 10, P(>=14 | Bin(96, 0.108)) =
       0.15, and 10 of the 11 new outside results are Knot (.se 3, .nu 2, .gov 2, .ee 3).
     - Q2 feature: 6 of 49 tests (2 outside) are .ee. Expected 8.0, P 0.92.
   - Better still, in the script: apply `SENS_MIN` only to break-affected sources (se, nu, gov), or report
     min-12-unmasked as the comparison, and record the minimum in each `*_breaks_masked` entry.
   - Proof: `python f_decomp.py` and `python g_units.py`.
4. `scripts/software_vs_adoption.py` `MEASUREMENT_BREAKS`, and the doc sentence "Three months-long changes".
   - Current: 3 breaks.
   - Correct: add .nu 2017-06..2017-12 (NS peak 281,539 to 466,775, +66%; DS peak flat at 86.8k to 86.4k through
     2017-10; DS share 31.7 to 24.2). Optionally add .se 2017-08..2017-12 (NS +19.5%, share 48.0 to 45.3), or state
     why they are omitted.
   - Effect: step12 unchanged; Q1 prevalence transient3 masked goes from 13 to 18 of 134.
   - Proof: `python b_breaks.py`, `python b2.py`, `python m_extra.py`.
5. Doc, Q1 secondary paragraph.
   - Current: "The per-test step count of 12 is 4 program and corpus units counted up to three times."
   - Correct: "... comes from 5 program and corpus pairs (nsd .gov 3, opendnssec .nu 3, pdns-rec .se 3,
     opendnssec .se 2, unbound .nu 1); the 4 ds_prev units carry 10 of them."
   - Proof: q1 CSV grouped by program and source (the snippet in this report's section 7b; one line of pandas).
6. Doc, Q2 knot[9] bullet.
   - Current: "the only unusual prevalence result that survives the break sensitivity".
   - Correct: "the only question 2 result that survives ...". In question 1, knot .nu and opendnssec .gov are outside
     in the masked run.
   - Proof: `q1_per_program_releases.prevalence.aggregate.unit_program_x_corpus.step12_breaks_masked.units_outside`.
7. `scripts/software_vs_adoption.py` `PREV_EXCLUDED_ROW["l02-nsec3-max-iterations-50"]`, and the doc table.
   - Current: "(dnssec-policy and signzone refuse iterations above 50)".
   - Correct: "(dnssec-signzone's limit lowered to 50; dnssec-policy refuses any non-zero iteration count)".
   - Also give knot[19]@3.6.0 and pdns-auth[3]@3.4.0 the fails-class label, or say why they differ. No number
     changes.
   - Proof: the `title` of these rows in `out/analysis/cross_program_defaults_normalised.csv`.
8. Doc, Q2 d15 bullet.
   - Current: "from 2018-10 to 2019-02 the .nu NS denominator fell from 413,121".
   - Correct: "from 2018-09 (413,121) to 2019-02 (232,995)".
   - Proof: `python b2.py`.
9. Minor, script. Call `mark_dip_reversals` before `append_csv("q4", precs)`, so the q4 CSV carries
   `reverses_dip_within_2m` as the JSON does. Recommended; this is not a number change.
