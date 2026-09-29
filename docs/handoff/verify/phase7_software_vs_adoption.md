# Phase 7 verification: software updates against adoption

Adversarial check of `docs/handoff/07_software_vs_adoption.md` and `scripts/software_vs_adoption.py`
(commit a2e2bf1c), against `docs/handoff/07_phase7_brief.md`. Every number here was recomputed with
independent code (pandas/numpy, no import of the Phase 7 script). Samples use `random.seed(20260929)`.
`$P` below is the scratchpad venv python.

## A. The one-month reverse dating offset

### A.1 Where `month` is assigned

| pipeline | code | month for the snapshot of day 1 of month M |
|---|---|---|
| RIR corpus ingest | `src/openintel_rfc/reverse_zones.py` `build_frame`: timestamp = midnight **UTC** of the snapshot day; files at `out/reverse/corpus/reverse/<rir>/YYYY-MM-DD/`; `monthly_days(day_of_month=1)` | (the snapshot day itself, 00:00 UTC on the 1st) |
| timeline extraction (server run and panel run) | `src/openintel_rfc/timeline_extract.py` `_timestamp_expression`: `strftime(to_timestamp(ms/1000), '%Y-%m')` in DuckDB. `to_timestamp` returns TIMESTAMPTZ and `strftime` renders it in the **session time zone** | depends on the host time zone |
| panel run | checkpoints `out/panel_run/checkpoints/reverse__arin__2009-04-01.parquet` have `day=2009-04-01, month=2009-04` | **M** |
| server run | `out/server_run/inventory.json`: afrinic/arin days `2009-04-01 .. 2026-09-01` (200 days); timeline months `2009-03 .. 2026-08` (200 months) | **M-1** |
| delegation ledger | `scripts/delegation_changes.py` `MONTH = re.compile(r"/(\d{4}-\d{2})-\d{2}/")` on the corpus directory name; a change is labelled with the **later** of the two snapshots | **M** |

Mechanism, reproduced: DuckDB `strftime(to_timestamp(1238544000), '%Y-%m')` (2009-04-01 00:00 UTC) gives
`2009-04` with `TimeZone='UTC'`, `'Europe/Amsterdam'` or `'Asia/Jerusalem'`, and `2009-03` with
`TimeZone='America/New_York'`. The server run was therefore extracted on a host with a UTC-negative time
zone. Independent confirmation from the forward corpus of the same server run: in 343 of 470 forward
source-months `measured_days` equals the month's length **plus one** (se 61 of 91, ch 41 of 44, ee 50 of
54, ...), i.e. the first UTC hours of day 1 of month M+1 were labelled month M. No code in the repository
shifts months on purpose (grep for previous-month, relativedelta, TimeZone: nothing).

Recomputed agreement (dimension `algorithm_ds _total`, `domains_peak`), server run against panel run:

| RIR | months compared, no shift | equal | months compared, server +1 month | equal |
|---|---|---|---|---|
| afrinic | 165 | 72 | 168 | 168 |
| arin | 178 | 12 | 181 | 181 |
| afrinic, dimension `all` | 194 | 1 | 199 | 199 |
| arin, dimension `all` | 194 | 0 | 199 | 199 |

Phase 7's numbers (168, 181 after the shift; 72, 12 without) are **confirmed**.

### A.2 Which dating is right

- **As a date label for a state**, M is what the pipeline intends: the snapshot is stamped 00:00 UTC on the
  1st of M, the corpus directory says M, and the ledger and panel say M. The server run's M-1 is an
  unintended host-time-zone artefact, not a convention. On that reading the panel and ledger are right and
  the server run's reverse series (and, by a few hours per month, its forward series) are mislabelled.
- **But a snapshot at 00:00 on day 1 of M is the state at the end of M-1**, and a ledger change labelled M is
  the difference between the snapshots of day 1 of M-1 and day 1 of M, so it **happened during calendar month
  M-1**. For event timing against a release date, the panel/ledger label is one month late; the server
  run's accidental label is the calendar month in which the change occurred.
- Verdict: Phase 7 is internally consistent (it uses panel/ledger dating throughout and re-dates per-RIR
  counts +1), and its statement that the server run is offset is correct. What Phase 7 does **not** say is
  that under its chosen dating a reverse change labelled M occurred in M-1. Consequences inside Phase 7:
  - Q3 window "release month and the 3 months after" = ledger labels r..r+3 = changes in calendar
    r-1..r+2. Label r is **entirely before the release** (all its changes happened in the month before r),
    and the third month after the release (label r+4) is left out.
  - Q4 reverse lags are one month too long. The afrinic digest-1 spike labelled 2022-01, counted as aligned
    with bind9 d20 (released 2022-01-24) at lag 0, happened between 2021-12-01 and 2022-01-01, i.e.
    **before** d20. It should not count as aligned (see F).
  - pdns-auth[0]@3.2 (2013-01-17) and the RIPE block `216.151.in-addr.arpa` signing labelled 2013-02: the
    signing happened between 2013-01-01 and 2013-02-01, so it may predate the release. With only monthly
    snapshots in the corpus (no daily archives on disk) this is **undeterminable** (see E).
  - Q2 on the panel: the "after" window (labels e..e+11) starts with the state at 00:00 on day 1 of the
    release month, before the release. With 12-month windows this dilutes by 1/12; with Q1's 3-month
    windows by 1/3.
  - Phase 7's own caveat "event timing in the reverse corpus is therefore uncertain by about a month"
    is too weak: the direction is known (labels are late by one month for changes), not just the size.

### A.3 Existing analyses that mix the two datings or compare reverse labels to calendar dates

Type 1, mixes server-run reverse with panel or ledger in one output, no shift:

| file | what it mixes | effect |
|---|---|---|
| `scripts/program_rfc_cases.py` (and `reporting/make_program_cases_deck.py`, `out/analysis/dns_program_rfc_spikes.csv`, `dns_program_rfc_new_signings.csv`) | reverse spikes on server-run per-RIR counts (label M-1), reverse panel share curve from panel run (label M), ledger new-signing windows (label M), all in one case | the panel curve and the ledger windows sit one month after the per-RIR spikes for the same event; the same spike is one month earlier here than in Phase 7 Q4 |
| `scripts/prevalence_metrics.py` + `reporting/prevalence_metrics.py` | `reverse` rows (server run, per RIR) and `reverse_panel` rows (panel) in one CSV and one chart (`ds_share.png`, lines 98-99) | the panel line and the afrinic/arin lines are offset by a month; 03 doc notes the gap-month shift but not that every month is shifted |
| `notebooks/build_software_notebook.py` / `dnssec_software_releases.ipynb` | reverse shares from `PAN`, forward from `SRV`, ledger `LED`/`CLU`; no server-run reverse | consistent with each other; Type 2 below |

Type 2, one reverse dating compared with calendar release, CVE or RFC dates (the label convention decides
whether a change is "after" an event):

| file | reverse source | effect |
|---|---|---|
| `scripts/release_scan.py` (`docs/release_scan.md`) | ledger | window "release month + 2 after" (WINDOW=3, inclusive) = ledger labels r..r+2 = changes in r-1..r+1: one of three "after" months is entirely before the release |
| `scripts/release_vs_adoption.py` (`docs/releases_vs_adoption.md`) | panel, month-on-month share change | the change at label m happened in m-1; before/after split one month late |
| `scripts/cve_vs_rfc_rates.py` | panel, month-on-month rate | same; event month + 3 after includes one pre-event month |
| `scripts/os_release_attribution.py` | ledger quarters | quarter boundaries one month late; lags to OS releases one month too long |
| `scripts/program_rfc_cases.py` `new_signings` around releases | ledger | "12 months after" includes label m (changes before the release) |
| `scripts/cve_adoption_crossref.py`, `reporting/make_summary_deck.py`, `scripts/software_crossref.py` | server run reverse | labels are calendar-correct for changes, but state "at month M" is really the state on day 1 of M+1. Both also **sum the five RIRs for a share** (`cve_adoption_crossref.share_at`, `make_summary_deck` lines 84-89), which the brief forbids |
| `reporting/rfc_timelines.py`, `reporting/algorithm_mix.py`, `reporting/make_framework_charts.py` | panel | charts only; RFC markers one month early relative to the curves |

Impact size: at most one month on any date. Nothing that is a multi-year trend changes. What changes are
statements of the form "N months after release X" and 3-month windows, where one of three months is
misassigned: release_scan, cve_vs_rfc_rates, Phase 7 Q1 (panel), Q3 and Q4 reverse lags.

Proof commands:
```
$P -c "import duckdb;[print(tz,duckdb.connect().execute(f\"SET TimeZone='{tz}'\").execute(\"select strftime(to_timestamp(1238544000),'%Y-%m')\").fetchone()) for tz in ['UTC','America/New_York']]"
$P -c "import pandas as pd;print(pd.read_parquet('out/panel_run/checkpoints/reverse__arin__2009-04-01.parquet')[['day','month']].drop_duplicates())"
grep -n first_day out/server_run/inventory.json | head -3
$P -c "import pandas as pd;s=pd.read_parquet('out/server_run/timeline_monthly.parquet');f=s[(s.basis=='zonefile')&(s.dimension=='all')];print((f.measured_days>pd.PeriodIndex(f.month,freq='M').days_in_month).sum(),len(f))"
```

**A result: 4 checks run; 3 passed (offset exists, counts 168/181/72/12, Phase 7 aligns its own sources),
1 failed (Phase 7 does not state that ledger/panel labels are one month late for changes, which moves the Q3
window and Q4 reverse lags).**

## B. `domains_peak` against `domain_days`

### B.1 The non-additivity claim

Own query, forward `se` 2019-06, `nsec3_iterations`: per-value `domains_peak` sum 1,423,125 over `_total`
peak 1,236,469 = **115.1%** (value 1: 1,144,196; value 5: 228,524; value 20: 38,597; ...). The same with
`domain_days`: **100.001%**. **Confirmed.**

Across all 404 forward source-months, per-value sum over `_total`:

| dimension | by peak: max (where), median | by domain_days: max, median |
|---|---|---|
| nsec3_iterations | 1.151 (se 2019-06), 1.0012 | 1.000, 1.000 |
| algorithm_dnskey | 1.284 (se 2019-07), 1.0032 | 1.282, 1.0021 |
| nsec3_optout | 1.080 (se 2017-11), 1.0001 | 1.000, 1.000 |
| digest_type_ds | 1.878, 1.62 | 1.872, 1.62 |
| rsa_key_bitsize | 2.009, 1.89 | 1.998, 1.88 |

Only the single-valued dimensions (NSEC3 iterations, opt-out) are exactly additive by `domain_days`.
`algorithm_dnskey`, `digest_type_ds` and `rsa_key_bitsize` are multi-valued per name (two algorithms in a
rollover; SHA-1 and SHA-256 DS side by side; KSK and ZSK of different sizes), so their per-value sums
exceed 100% under either column. That is what Phase 7 says ("sums over several algorithm values still
count a zone that carries two of them twice"). Note the median 1.6-1.9 for digest and key size: a
`digest1` share of 62% does not mean 38% of DS-carrying names lack SHA-1 DS in the exclusive sense; Phase 7
reads these shares correctly as "names carrying the value".

Reverse: `domains_peak == domain_days` in 100% of server-run reverse rows and 100% of panel rows
(`measured_days` is always 1). Confirmed.

### B.2 Is Phase 7's use of `domain_days` correct

Yes. sum over days of numerator / sum over days of denominator is the denominator-weighted mean of daily
shares; the numerator and denominator come from the same days, so it cannot exceed 100% for a
single-valued dimension and does not jump when a value changes mid-month. Two small caveats, neither
changes a result: (1) because of the time-zone artefact in A, most forward months include a partial
first day of the next month (343 of 470), so the "month" is a few hours longer at its end and shorter at
its start; (2) the `MIN_DEN` floor is applied to the peak denominator, which is a lower-bound count, the
safe direction.

### B.3 Existing outputs that build shares from `domains_peak` (forward, numerator and denominator can peak on different days)

| file | shares from peaks |
|---|---|
| `scripts/prevalence_metrics.py` -> `out/analysis/prevalence_metrics.csv`, `docs/handoff/03_prevalence_metrics.md`, `reporting/prevalence_metrics.py` | every forward metric: DS / NS, DNSKEY / NS, RRSIG-over-DNSKEY / NS, RRSIG names / all names |
| `scripts/program_rfc_cases.py` -> `docs/program_rfc_cases*`, `dns_program_rfc_spikes.csv` | forward share per case; for NSEC3 the denominator is the **sum of per-value peaks** (line 202), which is inflated by up to 15% in transition months |
| `scripts/release_vs_adoption.py` | forward shares (per-value peak sums / `_total` peak) |
| `scripts/cve_vs_rfc_rates.py` | forward signed / delegated zones rate |
| `scripts/software_crossref.py`, `scripts/cve_adoption_crossref.py`, `scripts/cve_crossref.py` | shares and first-seen counts |
| `reporting/make_summary_deck.py`, `reporting/make_rfc_deck.py`, `reporting/rfc_timelines.py`, `reporting/algorithm_mix.py`, `reporting/algorithm_flows_forward.py`, `reporting/make_split_charts.py`, `notebooks/build_software_notebook.py` | chart shares |

Reverse shares in all of these are unaffected (one snapshot per month).

### B.4 How far off (forward), three seeded sample months plus the known transition months

`random.sample` of forward source-months (fed.us excluded) with seed 20260929, then two fixed months:

| source-month | metric | peak-based, % | day-based, % | peak minus day, pp |
|---|---|---|---|---|
| li 2021-10 | DS / NS (prevalence_metrics) | 15.477 | 14.954 | +0.523 |
| li 2021-10 | alg 13 / signed zones | 87.385 | 87.055 | +0.330 |
| li 2021-10 | NSEC3 >= 100 iterations / sum of values (program_rfc_cases) | 0.450 | 0.319 | +0.131 |
| nu 2020-01 | DS / NS | 44.906 | 44.895 | +0.012 |
| nu 2020-01 | alg 13 | 38.080 | 37.986 | +0.094 |
| se 2021-09 | DS / NS | 54.987 | 54.973 | +0.015 |
| se 2021-09 | NSEC3 0 iterations / sum of values | 0.079 | 0.033 | +0.046 (2.4x relative) |
| se 2019-06 | alg 13 | 36.076 | 25.060 | **+11.016** |
| gov 2018-02 | DS / NS (03 doc fact 8: 21.39%) | 21.39 | **31.20** | -9.81 |

Over all 404 forward source-months, |peak minus day| for alg 13: median 0.08 pp, 90th percentile 0.71,
99th 4.59, max 12.55 (nu 2019-01); DS / NS: median 0.08, 90th 0.86, max 9.80 (gov 2018-02); NSEC3
0-iteration share: median 0.0003, max 2.97 (li 2022-03). So peak-based shares are fine for level
statements in ordinary months and wrong by up to 12 pp in exactly the months that matter for event
studies: the months in which a registry operator rolled algorithms or the measured population changed.
The 03 doc's ".gov 2018-02 ... ds_share falls 88.4% -> 21.4%" is, by mean daily share, 88.7% -> 31.2% ->
21.4%: the drop is spread over two months, not one.

Proof: `$P /tmp/claude-1000/vB.py` (the script is reproduced at the end of this file).

**B result: 3 checks run (115% claim, domain_days choice, inventory and impact of peak-based shares); 3
passed. Impact on earlier analyses recorded; Phase 7 itself is correct here.**

## C. Question 1, per-release tests

Independent implementation in `/tmp/claude-1000/v7lib.py` (share from `domain_days` with the peak
denominator floor of 30, centred 25-month rolling median with 13 minimum, 3-month window statistic with
at least 2 valid months per side) and `/tmp/claude-1000/vC.py`. The null draws reuse the brief's seed with
the script's per-test stream `default_rng([20260929, crc32(key)])` so percentiles can be compared exactly;
an exact enumeration over every offset 1..L-1 is given beside it, which needs no random numbers.

Five tests sampled with `random.seed(20260929)` from the 202 tested rows:

| program | observable | corpus | release months | mean d3, mine | Phase 7 | percentile, mine | Phase 7 | exact-enumeration percentile | share outside band, mine / Phase 7 | p outside, mine / Phase 7 |
|---|---|---|---|---|---|---|---|---|---|---|
| knot | iter0 | ch | 30 | -0.0432487 | -0.043249 | 30.5 | 30.5 | 30.5 | 0.0667 / 0.0667 | 0.919 / 0.919 |
| opendnssec | alg8 | gov | 11 | -0.455452 | -0.455452 | 8.7 | 8.7 | 9.2 | 0.0909 / 0.0909 | 0.640 / 0.64 |
| pdns-rec | iter_gt150 | ee | 26 | -0.000348 | -0.000348 | 62.2 | 62.2 | 64.5 | 0.0385 / 0.0385 | 0.535 / 0.535 |
| knot | alg8 | se | 62 | -0.0959904 | -0.09599 | 39.9 | 39.9 | 37.4 | 0.1290 / 0.1290 | 0.291 / 0.291 |
| pdns-auth | iter_gt100 | nu | 32 | 4.566e-05 | 4.6e-05 | 95.3 | 95.3 | 94.7 | 0.1562 / 0.1562 | 0.266 / 0.266 |

All five match to the printed precision.

Counts: 289 rows, 202 tested, 87 no test. `p_two_sided < 0.10` in **6** of 202 (opendnssec alg7 se,
alg8 nu, alg8 ch; pdns-auth iter_gt100 nu; unbound iter_gt150 ee and ch); `beats_chance_outside` in 5.
Chance expectation = 0.10 x 202 = 20.2, which is how the brief defines it (a 90% band, 10% outside).
**Numbers confirmed.**

### C.1 But the null is conservative for the real schedules, so "6 against 20.2" is not evidence of anything

The p-values of the 202 tests are not uniform: mean 0.631 (0.50 expected), and the counts per decile rise
steadily from 6 in [0, 0.1) to 35 in [0.9, 1.0). A placebo run, in which a randomly shifted schedule is
treated as the observed one (5 per test, 1,010 in all, same nulls), rejects at 10.8% with mean p 0.502: the
null is calibrated for a random phase but not for the actual phase. The reason is that the brief's shift is
circular **within the program's whole release span** (bind9 from 2000), while a series covers at most
2016-2023 (forward) or 2011-2026 (panel). Real schedules put more release months inside the coverage window
than their shifts do, because release frequency rose over time: the real schedule has more tested months
than the null median in 165 of 202 tests (median ratio 1.15; bind9 1.39, pdns-rec 1.53). A null mean over
fewer months is more dispersed, so the observed mean looks central. When the ratio is above 1.1, 1 of 124
tests rejects; at or below 1.1, 5 of 78. The expected rejection count under this null for these schedules
is therefore well below 20.2, and the document's "6 means fall outside the 90% null band against 20.2
expected" should not be read as quieter-than-chance. Fix: shift within the series' coverage window (or
condition the null on the number of tested months). Phase 7 followed the brief literally, so this is a
wording correction plus a recommended rerun, not a code defect.

Proof: `$P /tmp/claude-1000/vC.py; $P /tmp/claude-1000/vC2.py; $P /tmp/claude-1000/vC3.py`.

**C result: 7 checks run (5 sampled tests, the 6/202/20.2 counts, the chance-expectation definition); 7
passed; 1 methodological finding (conservative null) that changes how the headline should be worded.**

## D. Question 2, default-change events

### D.1 Hand recomputation (`/tmp/claude-1000/vD.py`)

d12 = mean of the detrended share over months e..e+11 minus mean over e-12..e-1; band = 5th-95th percentile
of d12 at 1,000 months drawn with replacement from all testable months (same seeded stream as the script
for comparability; the percentile against **all** testable months, which needs no random numbers, is given
too).

| row | corpus | share month before, % | d12 mine | Phase 7 | band mine | Phase 7 | percentile mine / P7 / all-months | raw mean before -> after, % |
|---|---|---|---|---|---|---|---|---|
| knot[2]@2.1.0 | panel | 0.25349 | -0.019119 | -0.019119 | -0.23818..0.35653 | -0.23818..0.356532 | 15.1 / 15.1 / 15.2 | 0.021 -> 0.319 |
| bind9 d21 | se | 0.36196 | 0.039922 | 0.039922 | -0.000439..0.3115 | -0.000439..0.311503 | 90.4 / 90.4 / 90.4 | 0.217 -> 3.083 |
| pdns-auth[7]@4.0.0 | panel | 0.24184 | -0.017410 | -0.01741 | -0.25076..0.35653 | -0.250764..0.356532 | 16.4 / 16.4 / 16.5 | 0.135 -> 0.443 |
| pdns-auth[8]@4.0.0 | panel | 0.24184 | -0.017410 | -0.01741 | -0.25406..0.35658 | -0.254061..0.356578 | 18.5 / 18.5 / 16.5 | 0.135 -> 0.443 |

All four **match** Phase 7 exactly. (pdns-auth[7] and [8] are the same observable and month, so their d12
is identical; only the random band differs.)

### D.2 The detrended event study cannot see a step (major methodological finding)

The raw means in the last column rise 15-fold (knot[2], panel) and 14-fold (d21, .se), yet d12 is near
zero. A centred 25-month rolling median follows a level shift: at the step month the median jumps with the
data, so the detrended series has no step left. Demonstration (`/tmp/claude-1000/vD2.py`): add a synthetic
step of +1, +5 or +10 pp to the real series at a chosen month and recompute d12 at that month.

| series, step month | raw d12 with +1 / +5 / +10 pp step | detrended d12 with +1 / +5 / +10 pp step | 90% band |
|---|---|---|---|
| panel alg13, 2018-06 | 6.44 / 10.44 / 15.44 | 0.0086 / 0.0086 / 0.0086 | -0.25..0.36 |
| se iter0, 2019-06 | 1.00 / 5.00 / 10.00 | 0.0004 / 0.0004 / 0.0004 | -0.00..0.29 |
| se alg13, 2018-01 | 1.36 / 5.36 / 10.36 | 0.290 / 0.290 / 0.290 | -2.01..1.14 |

The detrended statistic is **identical whatever the size of the step**. The same holds for Q1 (3-month
windows on the same detrended series). A default change is expected to produce a sustained level or slope
change in newly signed zones, which is precisely what this detrending removes; Q1 and Q2 can only detect
transient bumps that revert within about a year. The brief prescribed the centred rolling median, so Phase
7 complied, but every sentence that reads a Q1 or Q2 null as "no default change moves its observable" is
unsupported: the test had no power against that alternative.

Step-sensitive alternatives (`/tmp/claude-1000/vD3.py`, `vD4.py`), percentile among all testable months of
the same series:

| event | corpus | raw d12, pp (percentile) | d12 against a linear pre-trend, pp (percentile) |
|---|---|---|---|
| knot[2] | panel | +0.298 (33.9) | +0.178 (65.2) |
| pdns-auth[7]/[8] | panel | +0.309 (38.2) | -0.049 (29.4) |
| bind9 d21 | se | +2.866 (**96.3**) | +2.383 (**97.8**) |
| knot[14] | se | +3.147 (**99.3**) | +2.609 (**99.3**) |
| bind9 d15 | se | +11.27 (72.8) | -33.13 (5.1) |

Raw d12 for the zero-iteration rows in the six TLDs: outside the 90% band in 3 of 18 cells (d21 .se;
knot[14] .se and .ee), against 1.8 expected. So the ECDSA conclusions survive a step-sensitive test, but
the zero-iteration NSEC3 events of 2022 move outside the band in .se, consistent with Q4. That still does
not attribute anything to software (RFC 9276 and two operators, see F).

### D.3 The 17 rows with no test in any corpus (`/tmp/claude-1000/vD5.py`)

| rows | reason verified per corpus |
|---|---|
| d02, d03, knot[3], opendnssec[3], opendnssec[5] (alg8 and alg7), pdns-auth[1], pdns-auth[9], unbound[1] | no 12-month before-period in any corpus (se, nu, gov, ee, ch, li, and the panel where observable) |
| pdns-auth[3], pdns-auth[4] (iter_gt500) | no before-period everywhere; the value also never appears in nu, gov, ee, li |
| knot[19], kresd[12], kresd[15], l02, pdns-rec nsec3-max-iterations-50 | no 12-month after-period in any corpus |
| d09 (alg12, GOST) | **covered** in se, nu, gov and the panel; not tested because algorithm 12 never appears |
| pdns-rec nsec3-max-iterations-2500 | **covered** in se and nu; not tested because no name ever exceeds 2500 iterations |

15 of 17 lack a before- or after-period in every corpus; 2 are "no test" because the value is absent,
which Phase 7's tables state correctly. Confirmed. fed.us has no signed zone and is correctly "no test"
everywhere.

**D result: 6 checks run (4 hand events, the no-test list, the per-row reasons); 6 passed. 1 major
methodological finding (D.2) that invalidates the reading of Q1 and Q2 nulls as "no effect".**

## E. Question 3, manual against automatic

Independent recomputation in `/tmp/claude-1000/vE.py`: matching transitions = sign or rollover to
algorithm 8; window = ledger labels 2013-01..2013-04 (release month and 3 after, as Phase 7); statistic =
share of matching delegations at level "one block" or "concentrated" in the window minus the share in all
other months; null = 4 months without replacement from the 2009-08..2026-08 ledger span, 1,000 draws with
Python `random.seed(20260929)` (so p differs from Phase 7 by Monte Carlo error only); era-matched = months
within +-36 of the window.

| variant | matching delegations in window | block-or-concentrated share in window | difference | p | era-matched p |
|---|---|---|---|---|---|
| Phase 7 value, all RIRs | 106 | | 0.658 | 0.015 | 0.026 |
| mine, all RIRs | 106 | 1.000 | **0.658** | 0.013 | 0.022 |
| mine, ripe | 89 | 1.000 | 0.503 | 0.040 (P7 0.038) | 0.041 (P7 0.042) |
| mine, arin | 17 | 1.000 | 0.521 | 0.060 (P7 0.048) | 0.082 (P7 0.070) |
| mine, all RIRs, **without block 216.151.in-addr.arpa** | 42 | 1.000 | **0.658** | **0.023** | **0.036** |
| mine, calendar-correct window, labels 2013-02..2013-05 | 73 | 0.904 | 0.558 | **0.090** | **0.216** |
| mine, calendar-correct window, without 216.151 | 9 | 0.222 | -0.124 | 0.674 | 0.780 |

The statistic and p-values are **confirmed**. The block is confirmed: `216.151.in-addr.arpa`, RIPE, 64
delegations signed with algorithm 8, ledger label 2013-02 (the only matching action in 2013-02).

The interpretation is **not** confirmed:

1. "It is one action: RIPE block 216.151.in-addr.arpa signed 64 delegations" and "that rests on one RIPE
   block of 64 delegations" (Short answer) are wrong. Removing that block leaves the difference at 0.658,
   p 0.023, because the other 42 window delegations are all concentrated too. They are all in label
   2013-01: RIPE 188.93 (8 signed), 98.79 (8 rolled 7 -> 8), 6.5.0.1.0.a.2.ip6.arpa (7 signed, 1 rolled);
   ARIN 91.199 (8), 180.198 (4) and three singles.
2. Label 2013-01 is the diff between the snapshots of 2012-12-01 and 2013-01-01 (section A), so those 42
   changes were made in December 2012, **before** PowerDNS 3.2 was released on 2013-01-17. With the window
   moved to the calendar months after the release (labels 2013-02..2013-05) the result is p 0.090,
   era-matched 0.216: it no longer passes at 0.05. The 216.151 signing itself (label 2013-02) happened
   between 2013-01-01 and 2013-02-01, possibly before the release; monthly snapshots cannot tell.
3. Correct wording: "One level statistic reaches p = 0.015 (era-matched 0.026) for pdns-auth[0]@3.2. It is
   carried by concentrated signings in two ledger months, 106 delegations in 12 blocks, 100 of them in six, of which 42 were
   made in December 2012, before the release; with the window aligned to the calendar months after the
   release, p = 0.09 (era-matched 0.22). With 46 p-values, three below 0.05 are what chance gives."

"The share of matching delegations moved in actions of 10 or more is lower in the window than in other
months in 20 of 23 tested cells": **confirmed** (23 tested, 20 negative, 3 positive: pdns-auth[0] all RIRs
+0.061, pdns-auth[0] ripe +0.248, all-to-algorithm-8 ripe +0.034; no missing). 37 no-test cells confirmed.
46 p-values in the table, 3 below 0.05, as the document says. Note the window is the release month plus
3 after (4 months), slightly wider than the brief's "within 3 months after".

**E result: 5 checks run (statistic, p, era p, the block, 20 of 23); 4 passed, 1 failed (the "one block"
attribution and the pre-release dating of 40% of the window).**

## F. Question 4, spikes

### F.1 Zero-iteration NSEC3 alignment (`/tmp/claude-1000/vF.py`, own spike rule, not imported)

Spike rule re-implemented from its documented definition (month-on-month change >= floor 300, >= 10% of the
previous level, >= 4x the median absolute change of the preceding 12 months; consecutive months merge), on
forward per-TLD `domains_peak` counts of NSEC3 names with 0 iterations. Relevant defaults (0 iterations,
direction +): bind9 d18 and pdns-auth[11] (2022-01-24), bind9 d21 (2022-07-07), knot[14] (2022-08-22).

| spike | months | names added | aligned default (lag, months) | chance rate |
|---|---|---|---|---|
| se | 2022-07..08 | 41,250 | bind9 d21 (0) | 0.100 |
| nu | 2022-08 | 1,723 | knot[14] (0), bind9 d21 (1) | 0.100 |
| ch | 2022-03 | 20,076 | bind9 d18, pdns-auth[11] (2) | 0.209 |
| ch | 2022-08 | 7,920 | knot[14] (0), bind9 d21 (1) | 0.209 |
| ch | 2022-11..2023-02 | 139,874 | knot[14] (3) | 0.209 |
| li | 2022-03 | 544 | bind9 d18, pdns-auth[11] (2) | 0.209 |
| not aligned | se 2021-09, 2021-12, 2023-06; nu 2021-09; ch 2021-09, 2021-12; li 2022-12..2023-02 | | | |

13 spikes, 6 aligned, expected 2.065, Poisson-binomial p = 0.0091. **Confirmed** (Phase 7: 6 of 13, 2.07,
0.009). Two of the six are aligned only by a lag of 0 with a release late in the month (knot 3.2.0 on
2022-08-22), but each of those also has bind9 d21 at lag 1, so the count stands. Note that 4 of the 7
unaligned spikes fall in 2021-09..2021-12, before any zero-iteration signer default shipped, which is the
cleanest evidence in the data that the zero-iteration move was not waiting for software defaults.

### F.2 Who is behind the spikes

Phase 7: "The six spikes come from two registry operators: .se and .nu share one, .ch and .li the other."
The TLD registries are the Swedish Internet Foundation (.se, .nu) and SWITCH (.ch, .li). But the
`nsec3_iterations` dimension counts hashed owner names returned by the **second-level zones** OpenINTEL
queries (se 2019-06: 1.24 M NSEC3 names against about 0.8 M signed zones), so the NSEC3 parameters are set
by whoever signs those child zones, i.e. DNS hosting operators, not the registry. The monthly counts carry
no NS or operator field, so the actor cannot be named from the data. The pairing is also partial: .ch and
.li move together only in 2022-03; .se (2022-07) and .nu (2022-08) are a month apart; .ch 2022-11 and .li
2022-12 differ. **Inconclusive**; the sentence should say "the six spikes are in four TLDs run by two
registries; the monthly counts cannot identify the DNS operators whose zones changed".

### F.3 "within eight months of the IETF draft that became RFC 9276"

The checklist carries only RFC 9276's publication date (2022-08-01), no draft history. The software repos
bound it: `bind9.git` commit 8f324b4717 (2021-10-20), "Change nsec3param default to iter 0 salt-length 0
... as recommended by draft-ietf-dnsop-nsec3-guidance"; commit 2ee3f4e6c8 (2022-06-09) "Update NSEC3 guidance
to match draft-ietf-dnsop-nsec3-guidance-10", i.e. the working-group draft had reached revision -10 by
June 2022. So the draft existed by 2021-10 at the latest, three months before the first zero-iteration
default shipped and ten months before the RFC. The Short-answer wording "those defaults, the IETF draft and
RFC 9276 all land in the same eight months" is **wrong** for the draft; the defaults (2022-01 to 2022-08)
and the RFC (2022-08) do fall in eight months. The -00 date of the draft could not be established from the
repository: **inconclusive** beyond the 2021-10 bound.

Proof: `git -C out/software_repos/bind9.git show -s --date=short 8f324b4717 2ee3f4e6c8`.

### F.4 Reverse spikes under calendar dating (section A)

Re-dating each reverse spike to the calendar month of the change (label minus 1): aligned reverse spikes
fall from 4 to 3. The afrinic SHA-1 DS spike labelled 2022-01, reported as lag 0 after bind9 d20
(2022-01-24), happened between 2021-12-01 and 2022-01-01, before d20; the nearest earlier relevant default is
22 months away. RIPE 2013-02 (pdns-auth[0]) becomes lag 0, possibly before the release. Totals become 13 of
248 aligned, not 14; no cell's verdict changes (digest1 reverse goes from 1 of 7 to 0 of 7).

**F result: 5 checks run (count/expected/p, spike names and rows, operators, draft timing, reverse dating);
2 passed (count/expected/p; spike names and rows), 2 failed (draft timing wording; reverse aligned count
14 -> 13), 1 inconclusive (operator identity).**

## G. Question 5, successor RFCs (`/tmp/claude-1000/vG.py`)

| successor, month | observable | corpus | share at successor, mine / P7 | 12 months later, mine / P7 | peak, month | first below half peak |
|---|---|---|---|---|---|---|
| RFC 9276, 2022-08 | iter_gt0 | se | 97.00 / 97.00 | 95.46 / 95.46 | 100.00, 2021-02 | none / none |
| RFC 9276, 2022-08 | iter_gt0 | ch | 95.67 / 95.67 | 82.42 / 82.42 | 99.98, 2020-07 | none / none |
| RFC 9276, 2022-08 | iter_gt0 | li | 92.59 / 92.59 | 81.31 / 81.31 | 100.00, 2020-05 | none / none |
| RFC 8624, 2019-06 | alg5_7 | se | 0.71 / 0.71 | 0.52 / 0.52 | 0.97, 2016-12 | 2020-11 / 2020-11 |
| RFC 8624, 2019-06 | alg5_7 | gov | 35.79 / 35.79 | 31.41 / 31.41 | 44.74, 2017-05 | 2022-02 / 2022-02 |
| RFC 8624, 2019-06 | alg5_7 | panel | 31.21 / 31.21 | 33.76 / 33.76 | 103.12, 2011-05 | 2014-05 / 2014-05 |
| RFC 8624, 2019-06 | digest1 | se | 63.72 / 63.72 | 61.99 / 61.99 | 65.49, 2017-10 | 2022-04 / 2022-04 |
| RFC 8624, 2019-06 | digest1 | gov | 80.99 / 80.99 | 80.03 / 80.03 | 93.91, 2017-12 | 2023-05 / 2023-05 |
| RFC 8624, 2019-06 | digest1 | panel | 61.91 / 61.91 | 64.02 / 64.02 | 100.00, 2011-05 | 2022-01 / 2022-01 |

All values **confirmed**. Two reading problems, not numeric errors:

- The panel peaks are the panel's first signed month, 2011-05, with 32 signed delegations, and 103.12% is
  the multi-valued double count Phase 7 mentions elsewhere. "On the panel it had already fallen below half
  its 2011 peak in 2014-05, 61 months earlier" measures the fall from a 32-delegation starting point, not
  from a deployment peak. It should say so, or use a peak over months with a denominator of at least a few
  hundred.
- iter_gt0 is a share of NSEC3 owner names, not zones; the text says so once and should keep it in the
  RFC 9276 reading ("92 to 99.9% of NSEC3 owner names").

**G result: 9 checks run, 9 passed; 1 wording caveat.**

## H. Wording in `07_software_vs_adoption.md`

Sentences that overstate the numbers or credit an adoption step to one release:

| line | sentence (abridged) | problem | replacement |
|---|---|---|---|
| 17-18 | "the software timelines do not line up with adoption more often than chance" | Q1 and Q2 use a centred-median detrend that is blind to a sustained step (D.2), and Q1's null is conservative for the real schedules (C.1); a null result here cannot mean "no alignment" | "the tests used here, which detect short-lived deviations and not sustained level shifts, find no alignment beyond chance" |
| 19-20 | "those defaults, the IETF draft and RFC 9276 all land in the same eight months" | the draft was cited in bind9 code in 2021-10 and was at revision -10 by 2022-06 (F.3) | "those defaults and RFC 9276 fall in the same eight months, and the IETF draft behind them was public from 2021-10 at the latest" |
| 20-21 | "the forward TLDs involved belong to two registry operators" | NSEC3 parameters are set by child-zone DNS operators, which the counts cannot identify (F.2) | "the four TLDs involved are run by two registries; the operators of the changed zones cannot be identified" |
| 21-22 | "that rests on one RIPE block of 64 delegations" | removing the block leaves the result unchanged; 42 of 106 window delegations changed in December 2012, before the release (E) | see E.3 |
| 62 | "Event timing in the reverse corpus is therefore uncertain by about a month" | the direction is known: a change at panel/ledger label M happened in M-1 (A.2) | "a reverse change labelled M happened during calendar month M-1; reverse lags here are one month too long" |
| 158 | "Every forward result below measures a handful of registry operators" | same as line 20: child-zone DNS operators, not registries | "measures a handful of DNS operators" |
| 166 | "6 means fall outside the 90% null band against 20.2 expected" | numerically right, but the null is conservative (mean p 0.63; 1 of 124 rejections where the real schedule has more in-window months than its shifts) | add: "the circular shift over the whole release span makes this test conservative, so fewer than 20 are expected" |
| 176-177 | "The rows that reach existing zones only through a new signing ... are no different from the rest" | test cannot see the sustained change such rows would cause (D.2) | "... show no transient difference; a sustained difference was not tested" |
| 633-634 | "It is one action: RIPE block 216.151.in-addr.arpa signed 64 delegations with algorithm 8 in 2013-02" | wrong (E.1) | see E.3 |
| 635-636 | "best read as one operator acting in the month after a release" | 42 of the 106 changes were made in the month before the release | "best read as concentrated signing in the months around a release, 40% of it before the release" |
| 726 | "The six spikes come from two registry operators: .se and .nu share one, .ch and .li the other" | as line 20; the pairing holds only for .ch/.li in 2022-03 | as line 20 |
| 723-725 | "fall in the eight months in which the IETF draft on NSEC3 parameters became RFC 9276" | as line 19 | as line 19 |
| 775-776 | "On the panel it had already fallen below half its 2011 peak in 2014-05, 61 months earlier" | the "peak" is 103% of 32 delegations in the panel's first signed month (G) | give the denominator, or measure the peak over months with at least a few hundred signed delegations |
| 818-820 | "The conclusion is unchanged: no default change moves its observable outside the chance band more often than chance" | test blind to steps (D.2) | "no default change is followed by a transient deviation outside the chance band more often than chance" |
| 823-824 | "The earlier 'neither shows an effect' stands" | the detrended d12 ignores the 15-fold raw rise; the step-sensitive tests in D.2 also find no effect for the ECDSA events, so the conclusion survives, but not on this test | cite a step-sensitive test |
| 840 | "the one level result traces to one block" | wrong (E) | "the one level result is carried by concentrated signings in 2013-01 and 2013-02, the first of which predate the release" |

No sentence found that credits an adoption step to one release outright: wherever a spike follows a
release, the text says it is timing, not attribution. The problem is the reverse: the pdns-auth 3.2
passage points to one block and one month when the data do not.

Not checked: "Two full runs give a byte-identical JSON" (running the script would overwrite `out/analysis`,
which this verification must not modify).

**H result: 16 sentences listed.**

## Totals

| section | run | passed | failed | inconclusive |
|---|---|---|---|---|
| A. reverse dating | 4 | 3 | 1 | 0 |
| B. domains_peak vs domain_days | 3 | 3 | 0 | 0 |
| C. Q1 per-release tests | 7 | 7 | 0 | 0 |
| C. Q1 null calibration (methodological) | 1 | 0 | 1 | 0 |
| D. Q2 events and no-test rows | 6 | 6 | 0 | 0 |
| D. Q2 detrending power (methodological) | 1 | 0 | 1 | 0 |
| E. Q3 pdns-auth 3.2 | 5 | 4 | 1 | 0 |
| F. Q4 spikes | 5 | 2 | 2 | 1 |
| G. Q5 successor RFCs | 9 | 9 | 0 | 0 |
| H. wording | 16 | 0 | 16 | 0 |
| **all** | **57** | **37** | **22** | **1** |

Verdict: **PASS WITH CORRECTIONS**. Every number recomputed matches (to Monte Carlo error for my own
permutation draws). The corrections are to interpretation: the Q1/Q2 detrending cannot detect a step, the
Q1 null is conservative, the reverse ledger/panel labels are one month late for changes, and the pdns-auth
3.2 and RFC 9276 draft passages are wrong on facts.

## Appendix: `/tmp/claude-1000/vB.py`

```python
import pandas as pd, random
random.seed(20260929)
s=pd.read_parquet('out/server_run/timeline_monthly.parquet')
f=s[s.basis=='zonefile']
def get(src,m,dim,vals,col):
    d=f[(f.source==src)&(f.month==m)&(f.dimension==dim)]
    if vals=='>=100':
        d=d[d.value!='_total']; d=d[pd.to_numeric(d.value,errors='coerce').fillna(-1)>=100]
    elif vals=='any':
        d=d[d.value!='_total']
    else: d=d[d.value.isin(vals)]
    return d[col].sum()
def metrics(src,m):
    r={}
    for col in ['domains_peak','domain_days']:
        ds=get(src,m,'rr_type',['DS'],col); ns=get(src,m,'rr_type',['NS'],col)
        a13=get(src,m,'algorithm_dnskey',['13'],col); at=get(src,m,'algorithm_dnskey',['_total'],col)
        i0=get(src,m,'nsec3_iterations',['0'],col); iany=get(src,m,'nsec3_iterations','any',col); it=get(src,m,'nsec3_iterations',['_total'],col)
        i100=get(src,m,'nsec3_iterations','>=100',col)
        r[col]=dict(ds_share=100*ds/ns if ns else None, alg13=100*a13/at if at else None,
                    iter0_over_sumvalues=100*i0/iany if iany else None,
                    iter0_over_total=100*i0/it if it else None,
                    ge100_over_sumvalues=100*i100/iany if iany else None)
    return r
keys=sorted(f[f.source!='fed.us'][['source','month']].drop_duplicates().itertuples(index=False,name=None))
sample=random.sample(keys,3)+[('se','2019-06'),('se','2019-07')]
for k in sample:
    r=metrics(*k)
    print(k)
    for mname in r['domains_peak']:
        a,b=r['domains_peak'][mname],r['domain_days'][mname]
        if a is None or b is None: print('  ',mname,a,b); continue
        print(f'   {mname:24s} peak={a:9.4f}  days={b:9.4f}  diff_pp={a-b:+.4f}')
# worst ds_share and alg13 difference over all forward source-months
rows=[]
for src,m in keys:
    r=metrics(src,m)
    for mname in ['ds_share','alg13','iter0_over_sumvalues']:
        a,b=r['domains_peak'][mname],r['domain_days'][mname]
        if a is not None and b is not None: rows.append((mname,src,m,a-b))
d=pd.DataFrame(rows,columns=['metric','src','month','diff'])
d['ad']=d['diff'].abs()
print(d.groupby('metric').ad.describe(percentiles=[.5,.9,.99]).to_string())
print(d.sort_values('ad',ascending=False).groupby('metric').head(2).to_string())
```

The other verification scripts are `/tmp/claude-1000/v7lib.py`, `vC.py`, `vC2.py`, `vC3.py`, `vD.py` to `vD5.py`, `vE.py`, `vF.py`, `vG.py`.
