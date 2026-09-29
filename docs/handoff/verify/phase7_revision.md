# Phase 7 revision verification (commit 4a584dc8)

Adversarial check of the revised `docs/handoff/07_software_vs_adoption.md` and `scripts/software_vs_adoption.py`
against the corrections in `docs/handoff/verify/phase7_software_vs_adoption.md`. All numbers were recomputed with
independent code in `/tmp/claude-1000/v7b/` (`lib.py` builds shares from the parquet files and reimplements the
statistics; it does not import the Phase 7 script). Where a Monte Carlo null is compared exactly, the script's
per-test stream `default_rng([20260929, crc32(key)])` is reused; my own draws use seed 20260929. `$P` is the
scratchpad venv python. `out/analysis` was not written: md5 of every `software_vs_adoption*` output is identical
before and after the test run (`pytest tests/test_software_vs_adoption.py`: 15 passed).

## A. The step test

### A.1 Reimplementation and sampled events (`$P /tmp/claude-1000/v7b/vA1.py`)

Statistic: OLS line over the 24 months before the event index, extrapolated over 12 months, mean of actual minus
extrapolated; at least 16 and 8 valid months; forward event index = calendar month r, panel event index = label r+1.
Five step12 events sampled with `random.seed(20260929)` from the 78 tested, plus the two focus events:

| row | observable, corpus | after-labels | step12 mine | Phase 7 | percentile mine / P7 | p mine / P7 | band mine = P7 | testable months |
|---|---|---|---|---|---|---|---|---|
| knot[12]@3.0.2 | alg5_7, nu | 2020-11.. | -1.13755 | -1.13755 | 22.70 / 22.7 | 0.470 / 0.47 | -3.551..3.091 | 56 |
| pdns-auth[10]@4.5.0 | iter_gt100, ee | 2021-07.. | -0.0020506 | -0.002051 | 2.65 / 2.65 | 0.106 / 0.106 | -0.002051..0.01534 | 19 |
| l01-nsec3-max-iterations-150 | iter_gt150, gov | 2021-05.. | 0.0384215 | 0.038421 | 91.70 / 91.7 | 0.332 / 0.332 | -0.07806..0.03842 | 45 |
| kresd[9]@5.3.1 | iter_gt150, gov | 2021-03.. | 0.0384215 | 0.038421 | 90.50 / 90.5 | 0.380 / 0.38 | -0.07806..0.03842 | 45 |
| d17-nsec3param-default-in-policy | iter5, se | 2020-12.. | -25.3287 | -25.3287 | 11.45 / 11.45 | 0.250 / 0.25 | -27.41..29.59 | 56 |
| bind9 d21 | iter0, se | 2022-07..2023-06 | 2.63985 | 2.63985 | 97.55 / 97.55 | 0.066 / 0.066 | -0.001087..2.410 | 56 |
| knot[14]@3.2.0 | iter0, se | 2022-08..2023-07 | 2.88010 | 2.8801 | 99.10 / 99.1 | 0.036 / 0.036 | -0.001087..2.410 | 56 |

All seven **match exactly**. The statistic is implemented as described.

### A.2 Does it detect an injected step (`$P /tmp/claude-1000/v7b/vA2.py`)

A step of h pp is added to every month from the event on; the statistic and its whole null are recomputed on the
modified series (the null is drawn from the same series, so it sees the step too).

| series, event | +0 pp | +1 pp | +5 pp | +10 pp |
|---|---|---|---|---|
| panel alg13, 2018-06 (N=149) | 5.11, pct 90.3 | 6.11, pct 90.9 | 10.11, pct 99.7 | 15.11, pct 99.7 |
| se iter0, 2019-06 (N=56) | 0.00, pct 13.4 | 1.00, pct 75.9 | 5.00, pct 99.1 | 10.00, pct 99.1 |
| se alg13, 2019-01 (N=56) | 31.5, pct 92.0 | 32.5, pct 93.8 | 36.5, pct 95.5 | 41.5, pct 97.3 |
| se iter0, 2022-07 (d21) | 2.64, pct 97.3 | 3.64, pct 97.3 | 7.64, pct 99.1 | 12.64, pct 99.1 |
| nu digest1, 2019-03 (N=56) | 26.2, pct 88.4 | 27.2, pct 88.4 | 31.2, pct 90.2 | 36.2, pct 90.2 |
| gov alg8, 2020-01 (N=45) | -1.88, pct 45.6 | -0.88, pct 61.1 | 3.12, pct 98.9 | 8.12, pct 98.9 |

(percentile among all testable months of the modified series; the seeded-draw percentile differs by under 1.5.)

- The statistic itself moves by exactly h: the step shows up in full. **Confirmed**; this fixes the first report's D.2.
- The percentile does not. It saturates at the series' ceiling: in .se a +5 pp and a +10 pp step both give the 99.1st
  percentile, which is the maximum reachable with 56 testable months (p floor 2/56 = 0.036). A +1 pp step is not
  detected in any of the six series. In volatile series (.nu SHA-1 DS, .se ECDSA) even +10 pp stays inside or at the
  edge of the band.
- Cause: the placebo months that neighbour the event carry the same step in their own windows, so the step widens
  the null along with the statistic. With the placebo months restricted to those whose windows do not overlap the
  event (|e' - e| outside -24..+12), every +5 and +10 pp injection is at the 100th percentile, but only 24 to 112
  months remain.

### A.3 The placebo null

- Eligible months: every month of the same series at which step12 is defined (`s.testable_months(test)`), drawn 1,000
  times with replacement. **The event's own month is not excluded, nor are the 35 months whose 36-month windows
  overlap the event's.** Evidence: knot[14] in .se has percentile 99.1 but p 0.036, i.e. ~18 of the 1,000 draws tie with
  the observed value, which is the event month itself drawn ~1000/56 times.
- Including the event month is exchangeable under the null, so it does not break the size (see A.4); it caps the
  smallest p at about 2/N and, with the overlapping months, costs power against exactly the lasting step the test is
  meant to find (A.2).
- Q2 has no minimum-length guard, unlike Q1: 4 step tests (d21 and knot[14] in .ch and .li) have only 9 testable
  months, where the band is set by the single most extreme placebo and the smallest attainable p is 0.22.
  Distribution of testable months over the 78 tests: 56 (41 tests), 45 (16), 149 (11), 19 (6), 9 (4).

### A.4 Calibration (`$P /tmp/claude-1000/v7b/vA3.py`, own implementation of the described simulation)

| run | Q2 step12 rejection | Q1 coverage-window shift | Q1 whole-span shift |
|---|---|---|---|
| script's stream `crc32(b"calibration")` | **0.086** | **0.120** | **0.032** |
| another stream | 0.092 | 0.119 | 0.029 |
| dense schedule, 15 of 61 testable months (500 reps) | 0.090 | 0.120 | 0.084 |
| dense schedule, 30 of 61 | 0.078 | 0.128 | 0.112 |
| dense schedule, 45 of 61 (74%) | 0.072 | 0.124 | 0.124 |

- The claimed 0.086 and 0.12 are **reproduced exactly**, and 0.032 for the old null.
- 1,000 replications give a standard error of 0.0095, so Q1's 0.12 is about 2 SE above nominal: the coverage-window
  shift is **mildly liberal**, stably so at every density. Under it the chance expectation for 76 Q1 step tests is
  about 9.1, not 7.6; the 7 observed is at or below chance either way.
- The Q2 rate is at nominal by construction: the simulated event is drawn from the same months as the placebos. The
  calibration therefore confirms the size but says nothing about power, which is where A.2 finds the problem.

**A result: 5 checks run (reimplementation on 7 events, step detection, placebo eligibility, Q2 calibration, Q1
calibration); 4 passed; 1 failed (the step is detected by the statistic but the placebo null, which includes the
event's own and overlapping windows, caps the percentile, so a +1 pp step is never detected and +5/+10 pp only in
quiet series).**

## B. The Q1 guard (`$P /tmp/claude-1000/v7b/vB.py`)

Code (`q1`, lines ~720-735): the testable window [a, b] is the span of months at which the statistic is defined; the
release months counted are those in the window with a defined statistic; a test needs L = b - a + 1 >= 24 and
occupancy <= 0.75. **Implemented as described.** The release schedule is already collapsed to one event per calendar
month (`rel_months = sorted({m2i(d[:7]) ...})`), so collapsing BIND's parallel-branch releases to one per month is
what the script already does; it does not help.

BIND 9: 444 stable public releases in 190 months. In the .se/.nu step window 2018-06..2023-01 releases fill 52 of 56
months (93%); in .gov 45 of 45; on the panel 114 of 149 (77%, just over the guard).

Soundness:
- The guard is not needed for the size of the test. With schedules of 15, 30 and 45 release months in a 61-month
  window (25% to 74%), the coverage-window shift rejects at 0.12 to 0.128 (A.4), the same as at low density.
- It is needed for meaning. At 93% occupancy the release-month mean differs from every shifted mean by 4 of 56 months,
  so the test compares "release months" with the 4 months without a release. Excluding such cells is right; the 75%
  cut itself is arbitrary (the panel at 77% sits on the edge).
- "Every stable release is an event" is the part that fails for BIND. A schedule of meaningful events does give BIND
  a test. Feature releases (x.y.0) as the event set, occupancy 4 to 8%:

| observable, corpus | x.y.0 months tested / window | mean step12 | percentile | p |
|---|---|---|---|---|
| alg13, se | 3 / 56 | +5.41 | 70.8 | 0.584 |
| alg13, nu | 3 / 56 | +4.50 | 77.6 | 0.448 |
| alg13, gov | 2 / 45 | +3.88 | 89.8 | 0.204 |
| alg13, panel | 12 / 149 | +0.75 | 68.9 | 0.622 |
| iter0, se | 3 / 56 | +0.50 | 44.8 | 0.896 |
| digest1, panel | 12 / 149 | -2.78 | 16.1 | 0.322 |
| rsa1024, se | 3 / 56 | -13.08 | 9.2 | 0.184 |
| alg5_7, panel | 12 / 149 | +0.57 | 36.4 | 0.728 |

  None is outside the 90% band, so adding them would not change the headline, but "no program-level test for BIND 9"
  is a choice of event definition, not a property of the data. A "newest branch only" schedule does not help (51 of
  56 months). The default-change releases of BIND are already Q2.

**B result: 3 checks run (guard implemented as stated, guard needed for validity, bind9 consequence); 2 passed; 1
qualified (the exclusion is defensible, but an x.y.0 schedule gives BIND a program-level test; the doc should say
so instead of implying no test is possible).**

## C. Dating

| check | evidence | result |
|---|---|---|
| server-run reverse relabelled | afrinic, arin, ripe months now 2009-04..2026-09; `timeline_monthly.pre_utc_fix.parquet` 2009-03..2026-08; forward `se` unchanged 2016-06..2023-12 | confirmed |
| per-RIR counts equal the panel without a shift | own query, `algorithm_ds _total`: afrinic 168 of 168, arin 181 of 181 equal; the JSON `reverse_dating_check` gives 72 and 12 equal with a +1 shift | confirmed |
| no double shift in the script | `reverse_count_series` reads `data.pivot("srv", rir, dim)` and reindexes on its own months, no offset; `REV_EVENT_LAG = 1` is applied only to panel event indices; the Q4 `cal_shift` applies only to the lag and chance computation; `program_rfc_cases.spikes` (imported) has no month offset | confirmed, no double shift |
| Q1/Q2 panel windows | CSV `before_labels`/`after_labels` for all 11 panel step12 events: before ends at label r, after starts at r+1 (e.g. knot[2] 2016-01-14: 2014-02..2016-01 / 2016-02..2017-01) | confirmed |
| Q3 window labels r+1..r+4 | code `range(m + 1, m + WINDOW + 2)`; CSV windows e.g. pdns-auth[0] 2013-02..2013-05, d15 2020-03..2020-06 | confirmed |
| Q4 change month = label - 1 | `s0 = m2i(ep["start"]) - cal_shift`, `cal_shift = 1` for reverse; chance rate uses `m2i(x) - cal_shift`; spike 127 labelled 2013-02 is given as change month 2013-01, lag 0 to pdns-auth[0] | confirmed |
| Q4 composition | ledger rows selected on the spike labels, same convention as the relabelled counts | consistent |

Forward events still start the after-window at the release month r, so the days before the release in month r
count as "after"; the doc says so ("Lag 0 means the same calendar month, which can include days before the release").

**C result: 7 checks run; 7 passed.**

## D. Multiple testing (`$P /tmp/claude-1000/v7b/vD.py`)

- BH q recomputed over the 78 step12 p-values: max difference from the CSV `bh_q` 4e-7; smallest q **0.8233**, shared
  by the first 8 ranks. **Confirmed**; "no q below 0.10" and "none below 0.8" are correct.
- Ranking by two-sided p: knot[14] .se 0.036; l01 .se 0.044; knot[1] panel 0.044; d21 .se 0.066; knot[14] .ee 0.098.
  So d21 is the 4th most extreme, and the doc's "the two .se events are the most extreme default-change events in the
  data" (line 633-634) is **wrong**.
- "4 at least as extreme as d21 against 5.1 expected; 1 as extreme as knot[14] against 2.8": the counts are right
  (4 with p <= 0.066; 1 with p <= 0.036), and 5.1 = 78 x 0.066, 2.8 = 78 x 0.036. But the p-values are discrete with
  a floor near 2/N (N = 9 to 149 testable months), so many tests cannot reach p <= 0.066. Expectation under the exact
  placebo null (event month uniform over its series' testable months): **2.77** for p <= 0.066 and **1.76** for
  p <= 0.036. Poisson-binomial P(at least 4 | 2.77 expected) = **0.30**. The conclusion (not beyond chance) stands;
  the expected values in the doc are overstated by about 2x.
- Structural limit: the BH rank-1 threshold at q = 0.10 is p <= 0.10/78 = 0.0013; the smallest attainable p of any
  test is 2/149 = 0.013. **No test in this family could reach q < 0.10 whatever the data**, so "neither survives a
  multiple-testing view" and "no Benjamini-Hochberg q below 0.10" are guaranteed by the design and carry no evidence.
- The family also counts 8 duplicates: d14/d16 (3 corpora), d18/pdns-auth[11] (4), pdns-auth[7]/[8] (panel) are the
  same observable, corpus and month; 70 distinct tests.
- Outside-band count "5 of 78 against 7.8": with the discrete band on N months the expected number outside is 9.2,
  so 5 is below chance either way.

**D result: 4 checks run (BH values, "4 vs 5.1", "1 vs 2.8", ranking); 2 passed (BH values; counts 4 and 1); 2
failed (expected values 5.1 and 2.8 should be about 2.8 and 1.8; "most extreme events" is false). One structural
finding: the BH statement cannot fail.**

## E. Q3, pdns-auth[0]@3.2 (`$P /tmp/claude-1000/v7b/vE.py`)

Window labels 2013-02..2013-05; sign or rollover to algorithm 8; universe = ledger span.

| scope | window / other delegations | statistic | mine | Phase 7 | p (script stream) | era p | p, own 5,000 draws | era p, own |
|---|---|---|---|---|---|---|---|---|
| all RIRs | 73 / 7555 | one-block-or-concentrated diff | +0.5578 | +0.558 | 0.098 | 0.214 | 0.107 | 0.223 |
| all RIRs | | large-action (>= 10) diff | +0.3361 | +0.336 | 0.060 | 0.074 | 0.055 | 0.071 |
| ripe | 70 / 1025 | large-action diff | +0.4518 | +0.452 | 0.041 | 0.050 | 0.045 | 0.042 |
| ripe | | block diff | +0.4021 | +0.402 | 0.347 | 0.254 | 0.357 | 0.258 |

All values **confirmed** (0.098, 0.214, +0.34 with p 0.060).

What the window contains: label 2013-02, RIPE `216.151.in-addr.arpa`, 64 delegations signed (the only large action
and the only block-level action); 2013-03: 2 ARIN singles; 2013-04: none; 2013-05: 7 singles. So in the revised
window **64 of the 73 matching delegations, and all of the large-action and block-level signal, are that one block**.
The doc says "It was not one RIPE block" of the old result (correct for the old window), but does not say that the
revised near-0.06 result is exactly one block. Its changes happened between 2013-01-01 and 2013-02-01, so whether they
followed the release of 2013-01-17 cannot be told from monthly snapshots (the doc lists this under "What could not be
determined", but not beside this result).

Other Q3 claims: 24 tested and 36 no-test cells (CSV: 24 and 36, confirmed); 19 of 24 large-action differences
negative (confirmed from the table); "With 48 p-values in the table, 1 are below 0.05": 48 = the non-era p-values of
24 cells, 1 below 0.05 (ripe 0.041), confirmed; the table actually shows 96 p-values counting era-matched, and "1
are" is a grammar slip.

**E result: 6 checks run; 5 passed; 1 wording gap (the revised result is one block of 64 delegations in the release
month, possibly before the release).**

## F. Q5 (`$P /tmp/claude-1000/v7b/vF.py`)

Peak over months with at least 300 in the peak-day denominator; first month after the peak below half of it, same
floor.

| observable, corpus | peak, month, denominator mine | Phase 7 | below half | 2019-06 -> 12 months | Phase 7 |
|---|---|---|---|---|---|
| alg5_7, panel | 50.16, 2014-08, 313 | 50.16, 2014-08, 313 | 2017-02 (-28) | 31.21 -> 33.76 | same |
| alg5_7, se / nu / gov | 0.97 2016-12; 6.30 2016-11; 44.74 2017-05 | same | 2020-11 (17); 2021-08 (26); 2022-02 (32) | 0.71->0.52; 5.42->5.22; 35.79->31.41 | same |
| digest1, panel | 91.56, 2014-09, 379 | same | 2022-05 (35) | 61.91 -> 64.02 | same |
| digest1, se | 65.49, 2017-10, 689140 | same | 2022-04 (34) | 63.72 -> 61.99 | same |
| digest1, nu | 93.10, 2017-05, 86803 | same | 2022-04 (34) | 69.59 -> 69.58 | same |
| digest1, gov | 93.91, 2017-12, 1097 | same | 2023-05 (47) | 80.99 -> 80.03 | same |
| alg5_7 panel at RFC 9905 | 9.81 (2025-11) -> 7.98 (2026-08) | same | | | |

All numbers **confirmed**.

Reading problem, the same kind the first report raised: 2014-08 is **the first month in which the panel's signed
delegations reach 300** (2014-07: 294). The RSASHA1 share was falling throughout: 101% (100 delegations) in 2011-08,
96% in 2012-05, 74% in 2013-02, 52% in 2014-02, 50% in 2014-08, 32% in 2014-11. The "peak of 50.2% in 2014-08" is the
floor's cut-off, not a peak, and "fell below half of that in 2017-02" measures from an arbitrary point on a decline.
SHA-1 DS is less affected (about 95% from 2012 to 2014-07, then 90-92% at the floor), so its 91.6% "peak" is a fair
level. The doc should call the RSASHA1 figure "the first month with at least 300 signed delegations" and state that
the share had been falling since 2012 from near 100% of about 100-200 delegations. The same applies to the RFC 9905 row
(peak 50.16, 2014-08, -105 months).

**F result: 12 checks run (8 rows of peak/half/trajectory, 2 RFC 9905 values, SHA-1 DS set, RSASHA1 peak); 11
passed; 1 wording failure (RSASHA1 "peak" is the floor's first month).**

## G. Wording

### G.1 The first report's corrections

| first report item | revised text | applied |
|---|---|---|
| H 17-18 headline "do not line up more often than chance" | lines 19-23: step test primary, transient labelled as blind to lasting shifts | yes |
| H 19-20 / 723-725 draft in the same eight months | lines 31-32, 789-791: draft public by 2021-10 | yes |
| H 20-21 / 726 two registry operators | lines 32-33, 793-794: four TLDs, two registries, zone operators unidentified | yes in the doc; **no in the script**: `FORWARD_NOTE` (script lines 82-84), written into the JSON `forward_note` of q2, q4 and q5, still says "two registry operators ... about a dozen organisations" |
| H 21-22 / 633-636 / 840 one RIPE block, one operator | lines 683-692 | yes for the old window; see E for the new window |
| H 62 timing "uncertain by about a month" | lines 52-56, Dating paragraph | yes |
| H 158 "handful of registry operators" | line 184 "DNS operators" | yes |
| H 166 conservative null | new null, calibration paragraph | yes (by fixing the method) |
| H 176-177 new-signing rows "no different" | lines 211-213 | yes, under the step test |
| H 775-776 panel 2011 peak | lines 840-843 | replaced, but the new peak is also a floor artefact (F) |
| H 818-820 / 823-824 "no default change moves its observable", "neither shows an effect" | lines 905-911 | yes, now cites the step test |
| A.2 labels one month late for changes | lines 52-56, 730-734, 872-873 | yes |
| E.3 pdns-auth 3.2 wording | lines 683-692 | yes |
| F.4 reverse aligned 14 -> 13 | lines 746, 796-798, 893 | yes |
| G iter_gt0 owner names | line 836-837 | yes |
| C.1 conservative Q1 null | coverage-window shift | yes |

14 of 15 applied in the doc; the registry-operator wording survives in the script's JSON note.

### G.2 Sentences that still overstate or misstate

| line | sentence (abridged) | problem | replacement |
|---|---|---|---|
| 22, 30, 198, 628-629 | "none with a Benjamini-Hochberg q below 0.8"; "neither survives a multiple-testing view"; "no Benjamini-Hochberg q is below 0.10" | cannot fail: smallest attainable p is 2/N >= 0.013, rank-1 BH needs 0.0013 (D) | "with at most 149 placebo months per series no single test can reach a BH q below 0.10, so the multiple-testing view is judged by counts: 4 tests have p <= 0.066 against about 2.8 expected" |
| 27-30, 628-629 | "4 ... at least as extreme as d21 against 5.1 expected, and 1 ... as knot[14] against 2.8" | expected values assume continuous p; exact discrete expectation 2.77 and 1.76 (D) | "4 against 2.8 expected (P = 0.30), and 1 against 1.8" |
| 633-635 | "Both approaches agree that the two .se events are the most extreme default-change events in the data" | l01 .se and knot[1] panel (p 0.044) are more extreme than d21 (0.066) (D) | "knot[14] in .se is the most extreme step test; d21 in .se is fourth" |
| 26, 233, 330, 633 | d21 "97.5th" (line 26, table) vs "97.6th" (233, 633); knot[14] .ee "97.6th" (330) vs 97.5 (table) | JSON value 97.55 rounded two ways | use one rounding (97.5 or 97.6) throughout |
| 58-60 | "A lasting level shift at the event shows up in full." | true of the statistic, not of the test: the placebo null includes the event month and overlapping windows, so a +1 pp step is never detected and +5/+10 pp reach only the series' ceiling percentile (A.2) | add: "The placebo null includes the event's own and overlapping months, so the percentile saturates: in .se a 5 pp and a 10 pp step both reach the 99.1st percentile and a 1 pp step is not detected." |
| 211-213, 898, 906-907 | "No group shows a lasting departure from trend more often than chance"; "no lasting departure from trend ... beyond chance" | absence of detection with limited power (A.2) | append "; steps under about 5 pp, or in volatile series, would not be detected" |
| 35-36, 683-687 | "the block-level signing after PowerDNS 3.2 has p = 0.098"; "+0.56 ... +0.34, p = 0.060" | in the revised window 64 of 73 delegations and all block-level and large-action signal are RIPE 216.151.in-addr.arpa, changed between 2013-01-01 and 2013-02-01 (E) | add: "In the revised window this is one action, RIPE 216.151.in-addr.arpa, 64 delegations signed in January 2013, which may predate the release of the 17th." |
| 227-229, 866-867 | BIND 9 "no program-level test ... the test has no contrast"; "A program-level test for BIND 9 ... no schedule shift gives a contrast" | true for "every stable release", not for BIND: an x.y.0 schedule (2-12 events, occupancy 4-8%) is testable, and inside the band in all 8 cells tried (B) | "no program-level test on every stable release; a feature-release (x.y.0) schedule would be testable and was not run" |
| 73-77 | Q1 coverage-window shift "rejects at 0.120, against a nominal 0.10" | 2 SE above nominal: mildly liberal, so the chance expectation for 76 tests is about 9.1 (A.4) | "rejects at 0.12, slightly liberal; 7 of 76 is below the 9.1 this implies" |
| 841-843, 896 | "its peak over months with at least 300 signed delegations is 50.2%, in 2014-08 with 313, and it fell below half of that in 2017-02, 28 months before RFC 8624" | 2014-08 is the first month past the floor; the share fell from about 100% in 2011-12 (F) | "In 2014-08, the first month with at least 300 signed delegations, it was 50.2%, down from about 100% of 100-200 delegations in 2011-12; it fell below 25% in 2017-02, 28 months before RFC 8624" |
| 691-692 | "With 48 p-values in the table, 1 are below 0.05" | 48 are the non-era p-values; the table shows 96 with era-matched; grammar | "Of the 48 non-era-matched p-values, 1 is below 0.05" |
| script 82-84 (JSON `forward_note`) | "two registry operators ... about a dozen organisations" | the retracted wording (first report F.2) | use the doc's line 184-186 wording |

No sentence credits an adoption step to one release: every alignment is labelled timing, not attribution.

**G result: 15 first-report corrections checked, 14 applied, 1 not (script JSON note); 12 sentences listed that still
overstate or misstate.**

## Totals

| section | run | passed | failed |
|---|---|---|---|
| A. step test | 5 | 4 | 1 |
| B. Q1 guard | 3 | 2 | 1 |
| C. dating | 7 | 7 | 0 |
| D. multiple testing | 4 | 2 | 2 |
| E. Q3 pdns-auth 3.2 | 6 | 5 | 1 |
| F. Q5 | 12 | 11 | 1 |
| G.1 first-report corrections | 15 | 14 | 1 |
| G.2 remaining overstatements | 12 | 0 | 12 |
| **all** | **64** | **45** | **19** |

Verdict: **PASS WITH CORRECTIONS.** Every number recomputed matches the outputs exactly (step statistics,
percentiles, bands, BH q, calibration 0.086 / 0.12 / 0.032, Q3 p-values, Q5 peaks). The dating is consistent with no
double shift. What needs fixing is how the results are read: the placebo null caps the step test's power and makes the
BH statement vacuous, the chance expectations 5.1 and 2.8 are about twice the discrete-null values, d21 is not among
the two most extreme events, the revised Q3 result is one block, the Q5 RSASHA1 "peak" is the floor's first month, and
BIND 9 could be given a program-level test with feature releases.

Recommended (optional) method change: draw Q2 placebo months only from months whose 36-month window does not overlap
the event's, or report the percentile against non-overlapping months beside the current one; and give Q2 the same
minimum of 24 testable months as Q1 (drops the 4 .ch/.li tests with 9 months).

Scripts: `/tmp/claude-1000/v7b/lib.py`, `vA1.py`, `vA2.py`, `vA3.py`, `vB.py`, `vD.py`, `vE.py`, `vF.py`.
