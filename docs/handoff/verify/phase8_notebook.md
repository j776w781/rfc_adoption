# Phase 8 notebook verification (`notebooks/dnssec_software_vs_adoption.ipynb`, HEAD c44883cc)

Adversarial check of the final notebook against `docs/handoff/08_phase8_brief.md`, the Phase 4 and Phase 7 outputs
and the owner's complaints. No repository file other than this report was written. `$P` is the scratchpad venv
python.

## A. Execution

Method: the notebook's setup cell deletes and rewrites every PNG in `reporting/charts/software_vs_adoption/`, so
running it inside the repository would modify committed files. It was therefore executed in an isolated copy:
`/tmp/claude-1000/v8/repo/` holds copies of `data/`, `scripts/`, `out/analysis/` and read-only symlinks to the
other `out/*` directories (server_run, panel_run, ...). Command:
`jupyter nbconvert --execute --ExecutePreprocessor.kernel_name=rfcadopt` on a copy of the committed notebook, output
`/tmp/claude-1000/v8/nb_exec.ipynb`. `git status` in the repository was clean afterwards.

| check | result |
|---|---|
| fresh kernel `rfcadopt`, top to bottom | ran, 117 cells (64 code) |
| errors | **0** |
| assertion cell (appendix) | **passes**: "21 numbers quoted in the text match a fresh read of the source JSON" |
| figures written | 52, same file names as committed |
| markdown and text outputs of the fresh run vs committed notebook | **identical** (diff of all markdown + stream/markdown outputs empty) |

Observation: executing the notebook from a clone deletes and regenerates the committed chart directory as a side
effect (`for old in FIGDIR.glob("*.png"): old.unlink()`). That is by design of the build, but a reader who opens the
notebook and presses "Run all" silently rewrites tracked files. Not a correction, a note.

The first execution attempt from `/tmp` (outside the repository) failed with `RuntimeError: run this notebook from
inside the rfc_adoption repository`, which is the intended guard.

**A result: 4 checks run; 4 passed.**

## B. Every chart

All 52 PNGs in `reporting/charts/software_vs_adoption/` were opened and read. Columns: **T** title states a
finding; **S** subtitle states metric, numerator/denominator and corpus; **E** every line, band and marker explained
in the text under it (or in the subtitle); **O** no overlap, clipping, legend on data or duplicate year ticks; **C**
at most 3 categorical colours, no dual axis; **P** palette respected (S1/S2/S3 in order, red only for emphasis).
"ok" = passes; anything else is a finding. No chart has a dual axis or a duplicated year tick; every legend sits
below the axes.

| # | chart | T | S | E | O | C | P | finding |
|---|---|---|---|---|---|---|---|---|
| 01 | detection_power | **fail** | partial | **fail** | **fail** | ok | ok | Blue line (.se ECDSA) is hidden completely under the green (.nu SHA-1 DS); a reader sees two lines, not three. Text says "These lines stay low", but the orange (panel) line reaches 73% at 10 pp. Title's ".se: not even 10 pp" is unqualified and contradicts Phase 7's ".se ECDSA at 5 pp" (see D). Points exist only at 0, 1, 2, 5, 10 pp but are joined by straight lines, so the panel line appears to cross 50% at about 8 pp, a value never measured. |
| 02 | forward_ds_dnskey_rrsig | ok | ok | ok | ok | ok | ok | Green dotted RRSIG on orange explained; .gov jump explained and verified (denominator 1,234 in 2018-01 -> 5,553 in 2018-02). |
| 03 | reverse_panel_ds_share | ok | ok | ok | ok | ok | ok | x axis starts 2009 while text says panel from 2011-05; harmless. |
| 04 | algorithm_shares | **fail** | ok | partial | ok | ok | ok | Title "in .se and .nu from 2019" is wrong for .nu: ECDSA overtakes RSASHA256 in .nu only in 2022-02 (48.5 vs 51.5), in .se in 2019-07, on the panel in 2022-09. Text attributes the steps to "whole registrars or DNS operators re-signing their customers' zones" (unsupported, see E). The panel RSASHA1 line exceeds 100% (103% in 2011-05, 101% in 2011-08: numerator > denominator) and nothing says why. |
| 05 | bind9_cadence | ok (count) | ok | ok | partial | ok | ok | "d13, d14 +2 more", "d08, d09 +2 more", "d18, d20 +2 more" hide row ids the brief says must be labelled. |
| 06 | bind9_default_changes | ok | partial | ok | partial | ok | ok | l01 .se dot at percentile 0 is half cut by the axis spine. y labels say "d13 (expect down)" but not what is measured; the observable is only in the HTML table above. d14/d16 are the same test (same observable, corpus, month) counted twice in "2 of 34". |
| 07 | bind9_release_months | **fail** | ok | ok | ok | ok | ok | Title "its release schedule cannot be tested" contradicts the x.y.0 test two charts later; should say "its every-release schedule". |
| 08 | bind9_release_dots | **fail** | ok | partial | ok | ok | ok | Title counts dots ("2 of 12 ... (17%)"), which the text itself says is not the test ("that is why the test shifts the whole schedule instead of counting dots"). Orange ring ("month of a tested default change") is not explained in the text. Top panel: series is "outside the band" at percentile 98.7 while every dot is inside, and its gaps are 0.0001 pp, i.e. nothing; the text says neither. |
| 09 | bind9_release_tests | ok | ok | ok | ok | ok | ok | |
| 10 | bind9_cve_latency | ok | partial | ok | ok | ok | ok | Legend "CVE (not classified as DNSSEC or not)" is confusing; subtitle does not name the source (Phase 4 CVE record). |
| 11 | unbound_cadence | ok (count) | ok | ok | ok | ok | ok | |
| 12 | unbound_default_changes | ok | partial | ok | ok | ok | ok | Observable not on the chart (only in the table). |
| 13 | unbound_release_dots | **fail** | ok | partial | ok | ok | ok | Title counts dots (4 of 27); the actual test is at percentile 100 (p < 0.001). Gaps are all under 0.001 pp; the "outside" result is on a series that barely moves, and nobody says so. Orange ring unexplained in text. |
| 14 | unbound_release_tests | ok | ok | ok | partial | ok | ok | .nu dot at 100 half-clipped at the right edge. |
| 15 | unbound_cve_latency | ok | partial | partial | partial | ok | ok | 43 of 52 CVEs sit exactly at 0 days, all hidden under the median and zero lines; the reader sees ~20 dots for n = 52. Text "middle half between +0 and +0 days" without saying why. |
| 16 | knot_cadence | ok (count) | ok | ok | ok | ok | ok | |
| 17 | knot_default_changes | ok | partial | ok | partial | ok | ok | [14] .se dot at 100 half-clipped. |
| 18 | knot_release_dots | **fail** | ok | partial | ok | ok | ok | Title counts dots (26 of 243). Orange ring unexplained in text. |
| 19 | knot_release_tests | ok | ok | ok | ok | ok | ok | |
| 20 | knot_cve_latency | ok | partial | ok | ok | ok | ok | n = 4 caveat is in the text. |
| 21 | kresd_cadence | ok (count) | ok | ok | partial | ok | ok | Reverse-panel bar is cut at the left axis edge (axis starts 2015.7); "[12] 5.7.1, [15] 6.0.6 +2 more" hides ids. |
| 22 | kresd_default_changes | ok | partial | **fail** | ok | ok | ok | kresd[9] .se at percentile 5.0 is drawn red ("outside") exactly on the band edge, while the how-to-read box says "below 5 or above 95 is outside"; 5.0 is not below 5. The chart and the definition disagree (Phase 7 decides "outside" by the interpolated 5th percentile, not by the mid-rank percentile plotted). The gap is -0.00012 pp; not said to be negligible. |
| 23 | kresd_release_dots | **fail** | ok | partial | ok | ok | ok | Title counts dots. Top panel: mean percentile 5.0 labelled "(inside the 90% band)", the same 5.0 that chart 22 draws as outside. |
| 24 | kresd_release_tests | ok | ok | ok | ok | ok | ok | .se dot at 5.0 blue here, red in 22: same issue. |
| 25 | kresd_cve_latency | ok | partial | ok | ok | ok | ok | |
| 26 | nsd_cadence | ok (count) | ok | ok | ok | ok | ok | |
| 27 | nsd_cve_latency | ok | partial | ok | partial | ok | ok | 13 CVEs, about 7 visible (overplotting at 0). |
| 28 | opendnssec_cadence | ok (count) | ok | ok | ok | ok | ok | Labels "1.2.0b1", "2.0.0a3" read as pre-releases under a subtitle saying "at their first stable release"; they are row ids, the diamond sits at the stable date. |
| 29 | opendnssec_default_changes | ok | partial | ok | ok | ok | ok | |
| 30 | opendnssec_release_dots | **fail** | ok | partial | ok | ok | ok | Title counts dots. |
| 31 | opendnssec_release_tests | ok | ok | ok | ok | ok | ok | |
| 32 | pdns-auth_cadence | ok (count) | ok | ok | ok | ok | ok | |
| 33 | pdns-auth_default_changes | ok | partial | ok | ok | ok | ok | Title wraps ("0.8 / by chance"), acceptable. |
| 34 | pdns-auth_release_dots | **fail** | ok | partial | ok | ok | ok | Title counts dots (6 of 63) while two of the three series are outside at percentile 100 and 0; the title undersells what the text reports. |
| 35 | pdns-auth_release_tests | ok | ok | ok | partial | ok | ok | Dots at 0 and 100 half-clipped. |
| 36 | pdns-auth_cve_latency | ok | partial | ok | partial | ok | ok | Title breaks "n / = 10)" across lines. |
| 37 | pdns-rec_cadence | ok (count) | ok | partial | **fail** | ok | ok | Row ids truncated: the three observable diamonds all read "nsec3-max-itera..."; "dnssec-default-...", "root-ds-2017-ad...", "keytrap-aggress..., keytrap-max-dns... +5 more". The reader cannot tell which cap is which. |
| 38 | pdns-rec_default_changes | ok | partial | ok | ok | ok | ok | |
| 39 | pdns-rec_release_dots | **fail** | ok | partial | ok | ok | ok | Title counts dots. |
| 40 | pdns-rec_release_tests | ok | ok | ok | ok | ok | ok | |
| 41 | pdns-rec_cve_latency | ok | partial | ok | ok | ok | ok | |
| 42 | mechanism_matrix | ok | ok | ok | ok | ok (ramp) | ok | |
| 43 | rfc_code_lag | ok | ok | ok | partial | ok | ok | Labels crowd at RFC 9276 (PDNS-A/Unbound, PDNS-R/kresd) and RFC 4509 (ODS/Unbound), still legible. |
| 44 | leader_follower | ok | ok | ok | ok | ok | ok | |
| 45 | keytrap | ok | ok | ok | ok | ok | ok | Red NVD line = highlighted event, allowed. |
| 46 | spike_alignment | **fail** | ok | partial | ok | ok | ok | Title "Only NSEC3 names, 0 iterations spikes follow default changes more often than chance" is a single-test claim: 1 of 15 cells has p < 0.10 against 1.5 expected, and p = 0.009 does not survive a Bonferroni 0.10/15 = 0.0067. Text omits Phase 7's caveats (three of the six aligned spikes are one .ch series; four of the seven unaligned zero-iteration spikes predate every zero-iteration default) and omits pdns-auth[11] from the defaults listed. |
| 47 | action_size | ok | ok | ok | ok | ok (ramp) | ok | Pooled only; per-RIR cells appear only as unlabelled dots in 49. |
| 48 | change_level | ok | ok | ok | ok | ok (ramp) | ok | |
| 49 | manual_automatic_pvalues | ok | ok | partial | ok | ok | ok | No legend entry for the red dot; dots are unlabelled so no cell can be identified. |
| 50 | rfc9276_iterations | ok | ok | ok | ok | ok | ok | |
| 51 | rfc8624_sha1 | ok | ok | partial | ok | ok | ok | Panel RSASHA1 line starts above 100% without explanation. |
| 52 | rfc9904_9905_panel | ok | ok | ok | ok | ok | ok | |

Palette: every chart uses S1/S2/S3 in order, the blue ramp for ordered bins (42, 47, 48, the bands) and red only for
"outside the band" dots, the NVD line, RFC publication lines and the one "beyond chance" bar. Text is never in a
series colour. Nothing fails **C** or **P**.

Charts failing at least one item (T, E or O marked **fail**): **01, 04, 07, 08, 13, 18, 22, 23, 30, 34, 37, 39, 46**
(13). Charts with minor (partial) findings only: 05, 06, 10, 12, 14, 15, 17, 20, 21, 25, 27, 28, 29, 33, 35, 36,
38, 41, 43, 47, 49, 51 (22). Clean: 17 charts.

Against the owner's complaints: the notebook largely answers them. There is one section per program. Every chart
has a subtitle stating the metric, and a "How to read it" paragraph under each chart explains the lines ("what are
the lines above?"). Section 5 defines a delegation change in plain words ("what are delegation changing"). What
still fails the "make the graphs meaningful" test:
1. The seven per-release dot plots are titled with a dot count that the notebook itself says is not the test.
2. Several "outside the band" results are on series that move by 0.0001 to 0.001 pp (Unbound .nu NSEC3 > 150; BIND
   x.y.0 .se NSEC3 > 150; kresd/pdns-rec/l01 NSEC3 > 150 .se). None of them is flagged as practically zero.
3. The detection-power chart hides one of its three lines.

**B result: 52 charts checked; 17 clean, 22 with minor findings, 13 failing at least one item.**

## C. Numbers

Population: every numeric token in the markdown cells and text outputs of the executed notebook (appendix excluded),
plus the numbers in 35 chart titles transcribed from the PNGs (`/tmp/claude-1000/v8/c/titles.txt`); years, month
labels, RFC numbers, algorithm numbers, version strings and section numbers removed: 676 tokens.
`random.seed(20260929); random.sample(items, 24)`. Draws 13 (a list index "1."), 19 (a repeat of draw 7) and 20
("about 1 in 10", a definition) were replaced by draws 21-23 of the same stream.

| # | where | quoted | source | value in source | match |
|---|---|---|---|---|---|
| 1 | 3.7 cadence text | PowerDNS Auth. 132 releases on **112** different days | `sva.load_releases()` (Phase 7 release list) | 132 releases, 112 distinct dates | yes |
| 2 | section 5 intro | window = ledger labels r+1 to **r+4** | J7 `q3_manual_vs_automatic.ledger_dating`; Q3 CSV `windows` (pdns-auth[8] 2016-07-08 -> 2016-08..2016-11) | r+1..r+4 | yes |
| 3 | 3.4 dot text | kresd[9] .se **-0.00012** pp | Q2 CSV step12 | -0.000116 | yes (rounded) |
| 4 | 3.8 release text | pdns-rec **0.5** expected (0 of 5) | Q1 CSV step12: 5 tested, 0 `beats_chance_mean` | 0.1 x 5 = 0.5 | yes |
| 5 | BIND verdict | d17 .se **-25.3** pp | Q2 CSV | -25.3287 | yes |
| 6 | pdns-auth verdict | pdns-auth[8] block-level p = **0.172** | Q3 CSV all RIRs `p_block_ge_observed` | 0.171579 | yes |
| 7 | release-dot text | consecutive months share **11** of 12 after-months | definition (12-month window) | 11 | yes |
| 8 | chart 16 title | Knot **21** default changes | `data/software/timelines/knot.json` `default_changes` | 21 | yes |
| 9 | 3.6 not-tested line | **11** because window < 24 months | Q1 CSV opendnssec step12 not-tested reasons | 8 (9-month window) + 3 (19-month) = 11; plus 1 never appears; 4 .fed.us excluded | yes |
| 10 | pdns-rec verdict | nsec3-max-iterations-150 .se percentile **4** | Q2 CSV | 4.0 | yes |
| 11 | section 2 text | reverse DS share **0.865%** in 2026-08 (6,444 of 744,825) | `prevalence_metrics.csv` | pct 0.8652, 6444 / 744825 | yes |
| 12 | spike intro | aligned = default change **0** to 3 months before | J7 `q4_spikes.method` ("0..3 months before the spike start") | 0..3 | yes |
| 13 | section 4 KeyTrap text | **0.23** pairs on average under shift | J4 `q8.../distinct_release_pairs.null_mean` | 0.235 | yes, but 0.235 printed as 0.23 (float rounding); "0.24" or "0.235" would be exact |
| 14 | kresd CVE text | **1** CVE beyond the axis | `cross_program_q6_cve_latency.csv` included, latency < -200 or > 100 | 1 | yes |
| 15 | KeyTrap text | p = **0.001** | J4 `distinct_release_pairs.p_value_ge` | 0.001 | yes |
| 16 | chart 06 title | BIND **34** default-change tests | Q2 CSV bind9 step12 tested | 34 (2 outside) | yes |
| 17 | chart 10 title | BIND n = **135** | CVE latency CSV bind9 included, non-null | 135, median -13, IQR -21..-9, 18 beyond axis | yes |
| 18 | pdns-auth verdict | NSEC3 opt-out .se p < **0.001** | Q1 CSV `p_two_sided` | 0.0 | yes |
| 22 | kresd / pdns-rec dot text | 1 of **3** outside | Q2 CSV | kresd 3 tested, 1 outside; pdns-rec 3, 1 | yes |
| 23 | BIND verdict | x.y.0: **2** of 31 | J7 `q1.../aggregate/bind9_feature_releases/step12` | tested 31, mean_outside 2 | yes |

Provenance of Phase 7 numbers: the notebook reads `out/analysis/software_vs_adoption.json` and its CSVs, last
changed in 998c35db ("second-verification corrections"), the final Phase 7 output; they are clean in the working
tree. The detection-power chart reads `q2_default_change_events.detection_power` from the JSON. Its 15 rows equal
`software_vs_adoption_power.csv` on share, percentile and `above_band` (all 15 equal). The appendix's 21 asserted
values match a fresh read.

Numbers outside the sample that I checked while reading, and that are wrong:
- Chart 04 title "in .se and .nu from 2019": .nu crosses in 2022-02 (see B).
- Chart 22 vs the box: "below 5 or above 95 is outside" vs a red dot at 5.0 (see B).

**C result: 20 numbers traced; 20 match (1 with a rounding nit: 0.235 shown as 0.23).**

## D. Detection-power consistency

**What the sources say.** `q2_default_change_events.detection_power` carries two readings of the same 15 rows:
- **At one chosen month** (`above_band` at `event_month`). .se ECDSA 2019-01: 0/1/2 pp not detected, 5 pp detected
  (percentile 96.3), 10 pp detected (98.5). Panel ECDSA 2018-06: 5 pp detected (100.0). .nu SHA-1 DS 2019-03: not
  even 10 pp (90.4).
- **Across all event months** (`share_of_event_months_above_band`, and `smallest_detectable_step_pp` = the smallest
  h above the band at half or more of them). Panel 10 pp (0.73 of 149 months). .se ECDSA none up to 10 pp (0.09 of
  56). .nu SHA-1 DS none (0.09 of 56).

Phase 7 (`07_software_vs_adoption.md` lines 29-32, 133-135, 970-971, 1031) reports both. Its headline and the
"cannot show" list lead with the first: "a lasting step of 5 pp is detected at a chosen month in .se and on the
panel"; "any lasting step smaller than about 5 pp at a single named event, or about 10 pp across a series' event
months".

**What the notebook says.** Chart 01 title: "Smallest step it detects: ECDSA share .se: not even 10 pp; ECDSA share
reverse panel: 10 pp; SHA-1 DS share .nu: not even 10 pp". The rule is named only in the subtitle ("Dashed line:
the detection rule, half of the event months") and in the legend. The how-to-read box says only "It only detects steps
above a certain size ... the detection-power table below gives the sizes for this run". The short answer points to
"the box below". Section 7 says the sizes are "printed in the 'how to read' box". No table is printed: the sizes are
only in the chart title. The 5 pp at-a-chosen-month figure does not appear anywhere in the notebook.

**Judgement.**
- *Correct?* Yes. Every value in the title equals `smallest_detectable_step_pp`, and the chart plots
  `share_of_event_months_above_band`. The across-months reading is also the fairer one: at .se 2019-01 the unstepped
  series already sits at percentile 91.9, so "5 pp detected" there means crossing from 91.9 to 96.3 at one month out
  of 56.
- *Clearly defined?* No. "Detects" in the title means "above the band at half or more of the event months", but that
  definition is only in 8-point subtitle text and a legend label. The "How to read it" paragraph never states it, and
  one of its sentences is false ("These lines stay low", while the panel reaches 73%).
- *Contradiction for a reader?* Yes. Someone who reads Phase 7's summary ("a 5 pp step is detected in .se") and then
  this title (".se: not even 10 pp") is told 5 pp and "more than 10 pp" for the same series. Nothing reconciles them.
  The notebook's own later sentences ("rules out only very large lasting shifts") do not give a number either.

**Proposed wording.**

Chart 01 title:
> The step test only catches large, lasting steps: a 10 pp step shows at half the possible event months on the
> reverse panel, and no step up to 10 pp does in .se ECDSA or .nu SHA-1 DS

Chart 01 subtitle (replace the last two sentences):
> Height: share of all possible event months at which the stepped series lands above the 90% band. We call a step
> "detected" when that share reaches half (dashed line). Points are measured at 0, 1, 2, 5 and 10 pp only. Source:
> Phase 7 detection-power table.

"How to read it" under chart 01 (replace):
> **How to read it.** Each line is one real series; the blue .se line lies under the green .nu line almost exactly.
> With no step added, about 5% of event months land above the band, as they should. A test with good power would
> climb to 100% after a step of 1 or 2 pp. Here the panel line reaches 73% only at 10 pp, and the two forward lines
> stay under 10% even at 10 pp: the placebo months next to the event carry the same step and widen the band with it.
> There are two ways to state this power. **At one chosen month**, Phase 7 finds a 5 pp step lands above the band in
> .se ECDSA (2019-01) and on the panel (2018-06), and not even 10 pp does in .nu SHA-1 DS (2019-03). **Across every
> possible month**, which is what this chart shows and what this notebook calls "detected", only the panel reaches
> half, at 10 pp. So "inside the band" anywhere below means "no lasting step of more than about 5 to 10 pp", and in
> volatile series not even that.

Section 7 bullet: replace "The detection-power table printed in the 'how to read' box gives those sizes for this
run." with:
> "Chart 1 gives the sizes: about 5 pp at a single chosen month, 10 pp across a series' months on the panel, and more
> than 10 pp in .se ECDSA and .nu SHA-1 DS."

Short answer item 2: replace "(see the box below)" with "(chart 1: about 5 to 10 pp on the panel, more in volatile
forward series)".

**D result: 3 checks run (value correct, definition clear, no contradiction with Phase 7); 1 passed (values), 2
failed (definition only in subtitle/legend; unreconciled with Phase 7's 5 pp).**

## E. Claims

Every markdown cell and text output was read in full (`/tmp/claude-1000/v8/exec.txt`) and searched for effect,
cause, drove, pushed, peak, registr*, Benjamini, q-value, follow*.

| category | sentences found | where | verdict |
|---|---|---|---|
| attributes an adoption step to a single release | none | | pass. Cell 104 names three defaults but says "This is timing, not attribution". |
| effect / mechanism claimed without a chance test | 1 | Cell 11 (chart 04 text, builder line 514): "In .se, .nu and .ch the switch from blue to orange happens in a few large steps: whole registrars or DNS operators re-signing their customers' zones at once." | **fail**. The corpus records neither signer nor operator (section 7 says so), and Phase 7 says the operators "cannot be identified". |
| single-test "beyond chance" without multiplicity | 1 | Chart 46 title, "Only NSEC3 names, 0 iterations spikes follow default changes more often than chance", and its text | **fail (wording)**. 1 of 15 cells at p < 0.10 against 1.5 expected. p = 0.009 > 0.10/15. Phase 7's caveats (3 of 6 aligned spikes are one .ch series; 4 of 7 unaligned zero-iteration spikes predate every default) are missing. |
| cites BH q as evidence | none | Cells 5 and 113 say no test can reach q < 0.10 by design | pass |
| calls RSASHA1 2014-08 a peak | none | Cell 111: "2014-08 is simply the first month with at least 300" | pass. The "high point" in the same cell refers to SHA-1 DS, which the second verification accepted as a fair level. |
| PowerDNS 3.2 as anything other than one RIPE block possibly before the release | 3 | (a) 3.7 intro (builder line 1098): "its RSASHA256 default of 3.2 (2013-01) is the one closest to a signal in section 5." (b) pdns-auth verdict: "pdns-auth[0]@3.2: large-action p = 0.060, block-level p = 0.098" with no caveat. (c) Chart 49 text: "Below 0.05: pdns-auth[0]@3.2 in ripe (large-action share, p = 0.041)", no caveat. | **fail (a, b)**, borderline (c). Cells 5 and 106 carry the right caveat; these three do not. |
| "two registry operators" where operators cannot be identified | none | Cell 104: ".se/.nu and .ch/.li are each run by one registry, and the operators of the zones that changed cannot be identified" | pass. The registries (IIS, SWITCH) are identifiable, and zone operators are said not to be. The JSON `forward_note` still says "run by two registries", which is not quoted. |

Other claims needing a caveat (not in the six categories):
- Short answer item 2 names "l01-nsec3-max-iterations-150 in .se, at percentile 0.0" as one of the two most extreme
  results. Its gap is -0.00014 pp. Likewise kresd[9] .se (-0.00012 pp), nsec3-max-iterations-150 .se (-0.00012 pp),
  Unbound's release result in .nu (gaps under 0.001 pp) and BIND x.y.0 .se NSEC3 > 150 (0.0001 pp). None of these
  results says that the share barely moved. "Outside the band" on a series whose total movement is a
  ten-thousandth of a point is a rank artefact, not an adoption change.
- Section 7, BIND bullet: stale (see F).

**Reverse dating convention.** The how-to-read box states it once ("a change between labels M-1 and M happened during
calendar month M-1. Every chart that marks a release against reverse data follows this rule"). Section 5 uses labels
r+1..r+4. Cell 106 dates the RIPE block "between labels 2013-01 and 2013-02, i.e. during January 2013". The seven
release-dot charts say "reverse panel: plotted at the first label after the release" but not what that means. That
implements the rule without stating it on the chart, as the brief asks ("say so on any chart that marks a release
against reverse data"). Charts 51-52 mark RFC publication on the panel's label axis without the note; they mark
RFCs, not releases, so that is a nit.

**E result: 6 categories checked; 4 passed, 2 failed (1 unsupported mechanism sentence; 3 PowerDNS 3.2 mentions
without the one-block caveat, 2 of them clear failures). Plus 1 multiplicity wording failure (chart 46) and a partial
on the reverse-dating note in 7 chart subtitles.**

## F. Structure

| program | section | cadence strip | default changes + observables + event study | per-release dots vs null | CVE latency | verdict | missing-figure reason given |
|---|---|---|---|---|---|---|---|
| BIND 9 | 3.1 | 05 | table + 06 | 07 (occupancy) + 08 (x.y.0 dots) + 09 | 10 | yes | every-release test impossible: yes (07 + text), but see Section 7 contradiction below |
| Unbound | 3.2 | 11 | table + 12 | 13 + 14 | 15 | yes | n/a |
| Knot DNS | 3.3 | 16 | table + 17 | 18 + 19 | 20 | yes | n/a |
| Knot Resolver | 3.4 | 21 | table + 22 | 23 + 24 | 25 | yes | n/a |
| NSD | 3.5 | 26 | "not observable" text | "no mapped observable" text | 27 | yes | **yes, but contradicted**: cell 61 prints "No default change of NSD maps to anything the zone data records ... This is not a null result" and then "**No default-change chart for NSD:** none of its mapped default changes has 24 months of data before it and 12 after in any corpus". The second reason is false: NSD has no mapped default changes. |
| OpenDNSSEC | 3.6 | 28 | table + 29 | 30 + 31 | none | yes | yes: "no included CVE with a fix release ... CVE-2012-5582 has no fix commit". The verdict has no "Security fixes" line and does not repeat this. |
| PowerDNS Auth. | 3.7 | 32 | table + 33 | 34 + 35 | 36 | yes | n/a |
| PowerDNS Rec. | 3.8 | 37 | table + 38 | 39 + 40 | 41 | yes | n/a |

Eight sections, one per program, in the same order with the same five sub-headings. The brief's other sections are
present: 1 (short answer + box), 2 (series), 4 (matrix, lags, leader/follower with chance ticks, KeyTrap), 5
(definitions in plain words, action size, level, p-values), 6 (successor RFCs), 7 (limits).

Structural defects:
1. **Section 7 contradicts sections 1 and 3.1.** Builder line 1621-1624 / notebook cell 113: "A program-level test for
   BIND 9 on every stable release. ... The second verification notes that a schedule of feature releases (x.y.0)
   would be testable; it tried eight cells and all were inside the band, but this is not part of Phase 7's output."
   Phase 7 now exports `bind9_feature_releases` (31 tests, 2 outside), and the notebook reports them in the short
   answer, chart 08, chart 09 and the BIND verdict.
2. **NSD double message** (above).
3. **Verdicts are not "three to five sentences".** They are stat lists (Releases / Default changes / Key default
   changes / Reverse ledger / Security fixes). None ends with a plain conclusion such as "Adoption does not bend after
   BIND 9 releases or default changes more often than chance; the two outside results are an NSEC3 series that barely
   moves and a .gov key-size share against the expected direction." For a reader who asked "I need to understand the
   metrics", that sentence is the missing piece.
4. Per-RIR action-size results (section 5) exist only as unlabelled dots in chart 49. The brief asks for them "per
   RIR where Phase 7 reports it". The text gives the count (19 of 24) but no reader can see which RIR is which.

**F result: 8 of 8 sections present with the specified layout; 3 missing-figure reasons checked (NSD, OpenDNSSEC,
BIND per-release): 2 correct, 1 contradicted (NSD); 1 stale section-7 bullet.**

## Totals

| section | checks | passed | failed / partial |
|---|---|---|---|
| A. execution | 4 | 4 | 0 |
| B. charts | 52 | 17 clean | 13 fail, 22 minor |
| C. numbers | 20 | 20 | 0 (1 rounding nit) |
| D. detection power | 3 | 1 | 2 |
| E. claims | 6 categories + dating | 4 | 2 fail + chart 46 wording + dating partial |
| F. structure | 8 sections + 3 reasons | 8 + 2 | 1 reason contradicted, 1 stale bullet |

## Verdict: PASS WITH CORRECTIONS

The notebook runs from a fresh kernel with zero errors, its assertion cell passes, and every number traced (20 of 20,
plus the 21 asserted) matches the final Phase 7 and Phase 4 outputs. The one-section-per-program structure is what
the owner asked for, and every chart has a subtitle and a "How to read it" paragraph. What needs fixing:
- a stale section-7 bullet and an NSD double message that contradict the rest of the notebook;
- an unreconciled detection-power statement;
- one wrong chart title (04);
- seven dot-plot titles that report a statistic the notebook disowns;
- a few sentences that overreach (registrars, PowerDNS 3.2 without its caveat, the spike title);
- several "outside the band" results that are practically zero and are not flagged as such.

## Required corrections

1. **Cell 113 (Section 7), builder lines ~1621-1624.** Stale BIND bullet contradicts cells 5, 23, 27. Replace with:
   "* **A program-level test for BIND 9 on every stable release.** Its releases fill most months, so a shifted
   schedule cannot differ from the real one. Its x.y.0 feature releases are tested instead (section 3.1: 2 of 31
   outside the band, against 3.1 by chance)."
2. **Cell 61 (NSD), `q2_dotplot`, builder line ~698.** Second message gives a false reason. In `q2_dotplot`, return
   silently when `MAP[MAP.program == prog]` is empty (so only `q2_table`'s "not observable" sentence prints).
3. **Chart 01 + cell 7 text (detection power).** Apply the D wording: new title, new subtitle end, new "How to read
   it" (states the half-of-months rule, the 5 pp at-one-month figure, the hidden blue line and the panel's 73%).
   Also draw the .se line with a marker offset or `zorder` above .nu (for example a dashed S1 line on top) so all
   three are visible. Use `ls="none"` between measured points or mark "measured at 0, 1, 2, 5, 10 pp".
4. **Cell 114 and cell 5 pointers.** Replace "The detection-power table printed in the 'how to read' box gives those
   sizes" with "Chart 1 gives the sizes: about 5 pp at a single chosen month, 10 pp across a series' months on the
   panel, and more than 10 pp in .se ECDSA and .nu SHA-1 DS". Replace "(see the box below)" in item 2 with "(chart 1)".
5. **Chart 04 title.** Replace with "ECDSA replaced RSASHA256 as the main algorithm: in .se in 2019, on the reverse
   panel in 2022, in .nu only in 2022 and in .gov in 2023".
6. **Cell 11 text (builder line 514).** Replace "whole registrars or DNS operators re-signing their customers' zones
   at once" with "moves consistent with a few large operators re-signing many zones at once; the zone files do not
   record who signed, so this cannot be confirmed". Add: "The panel's RSASHA1 line starts slightly above 100% in
   2011 because a delegation carrying both algorithm 5 and algorithm 7 DS records counts once in each; the panel then
   held under 110 signed delegations." The same sentence also goes under chart 51.
7. **Charts 08, 13, 18, 23, 30, 34, 39 (release-dot titles).** Title with the test result, not the dot count. Template:
   `f"{NAME}: after its releases, {k} of {n} series shown depart from trend beyond the chance band"`, or for single
   series `f"{NAME}: {series} bends after its releases more than under shifted schedules (percentile {p})"`. Keep
   the dot share in the text only.
8. **Same seven charts, "How to read it".** Add: "An orange ring marks a release month that is also a tested default
   change." Add to the subtitle: "Reverse panel: a dot at label M covers changes made during calendar month M-1 and
   after."
9. **Chart 07 title.** "BIND 9 ships in almost every month, so its every-release schedule cannot be tested; its x.y.0
   feature releases can (next charts)".
10. **Box in cell 7, "Percentile" paragraph.** "below 5 or above 95 is outside the band" is contradicted by kresd[9] .se
    drawn red at 5.0 (chart 22) and a 5.0 drawn blue in charts 23-24. Replace with "about 5 or less, or about 95 or
    more, is outside the band; the exact edge is the placebo values' 5th and 95th percentile, so a value printed as
    5.0 can fall on either side".
11. **Magnitude caveat on near-zero results.** In `verdict()` and the Q2 dot text, when `abs(observed) < 0.01` pp
    append ", a change of under 0.01 percentage points, i.e. the share barely moved". Apply the same to the Q1
    series text when the series' step statistics are all under 0.01 pp in absolute value (Unbound .nu > 150, BIND
    x.y.0 .se > 150, kresd/pdns-rec .se > 150). In the short answer item 2 add after l01: "(a change of -0.00014 pp:
    ranked extreme, but the share hardly moved)".
12. **Chart 46 title and text (builder ~1325-1349).** Title: "Only zero-iteration NSEC3 spikes line up with default
    changes more often than their chance rate (1 of 15 series; p = 0.009)". Append to the text: "With 15 series
    tested, about 1.5 would reach p < 0.10 by chance, and 0.009 is above a Bonferroni 0.10/15 = 0.0067. Three of the
    six aligned spikes are one .ch series, and four of the seven unaligned zero-iteration spikes fall in 2021-09 to
    2021-12, before any zero-iteration signer default shipped." Add pdns-auth[11]@4.6.0 (2022-01-24) to the list of
    defaults.
13. **3.7 intro (builder line 1098), pdns-auth verdict (`verdict()`, builder ~1046), chart 49 text.** After each
    mention of pdns-auth[0]@3.2's p-value add: "; this is one RIPE block (216.151.in-addr.arpa, 64 of the window's 73
    delegations) signed during January 2013, possibly before the release on the 17th". In the 3.7 intro replace "is
    the one closest to a signal in section 5" with "gives the smallest p in section 5, which rests on one RIPE block
    that may have changed before the release".
14. **Chart 37 (pdns-rec cadence).** Row ids are truncated to "nsec3-max-itera..." and cannot be told apart. Use
    short ids (for example "cap-2500", "cap-150", "cap-50", "keytrap x7") or widen the label budget. Charts 05 and 21:
    list all ids instead of "+2 more" (or put the full list in the text under the chart).
15. **Verdict cells (27, 37, 47, 57, 67, 77, 87, 97).** Open each with one plain sentence answering "does adoption
    follow this program?" For example, BIND 9: "Adoption does not bend after BIND 9's feature releases or default
    changes more often than chance; the few results outside the band are on series that barely move or go against
    the expected direction." OpenDNSSEC's verdict should add "**Security fixes.** No datable CVE fix (CVE-2012-5582
    has no fix commit)."

Recommended (not required):
- Clip-free edge dots in the dot plots (06, 14, 17, 35): set `xlim(-2, 102)`.
- CVE charts 15 and 27: add "43 of 52 Unbound CVEs were fixed on the day NVD published them, so they sit on the zero
  line" to the text, and jitter or add a count label at 0.
- Chart 10 legend: "CVE (DNSSEC classification not recorded)".
- Chart 49: label the red dot "pdns-auth[0]@3.2, RIPE, large actions" and add a legend entry "p < 0.05".
- Section 3.6 intro: "1.2.0 (2011-03)" instead of "1.2.0b1 (2011-03)"; the date is the stable release's.
- KeyTrap text: print the null mean as 0.235 (J4 value), not 0.23.
- Cell 5 "at most about 150 placebo months" vs cell 113 "at most 149": use 149 in both.
- The setup cell deletes and rewrites `reporting/charts/software_vs_adoption/*.png` on every run. Say so in the
  Setup markdown, so that "Run all" does not silently modify tracked files.

Working files: `/tmp/claude-1000/v8/nb_exec.ipynb` (fresh execution), `/tmp/claude-1000/v8/exec.txt` (all text),
`/tmp/claude-1000/v8/repo/` (isolated copy with regenerated PNGs), `/tmp/claude-1000/v8/c/titles.txt`.
