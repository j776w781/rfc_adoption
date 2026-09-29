# Phase 7 brief: each program's update timeline against the adoption data

For a fresh agent with no other context. Read this file in full, then
`docs/handoff/01_program_timelines.md` and `docs/handoff/04_cross_program.md`, before
starting.

## Goal

The owner's question, verbatim in substance: *for each program (bind9, unbound, ...), for
each version release, does adoption in OpenINTEL and RIPE follow it; what is the split
between operator manual changes and automatic changes due to version updates; and if the
change happens at a different operator level, say so.* Also: *is a newer RFC published
while its predecessor is still being deployed?*

This was attempted once before (`docs/releases_vs_adoption.md`, `docs/release_scan.md`,
`scripts/release_scan.py`, `scripts/program_rfc_cases.py`), using an unverified release
table (`data/software/release_dates.json`, which carries cvs2git artefacts such as BIND
9.3.0-9.3.4 all on 2007-03-06) and only seven default changes. Redo it on the **verified
timelines**, which have ~150 default/limit/support rows and verified stable release dates.
Where your result differs from the earlier documents, say which and why.

Repo root: `/mnt/shared/Documents/University/year2/DNSSEC/rfc_adoption`, branch
`software-timelines-v2`. Do not commit. Python with pandas/pyarrow:
`/tmp/claude-1000/-mnt-shared-Documents-University-year2-DNSSEC-rfc-adoption/009fe9c8-8f6c-489b-9085-0e0b381788e0/scratchpad/venv/bin/python`.

## Inputs (read-only)

| path | what |
|---|---|
| `data/software/timelines/<program>.json` | verified releases (`stable`, `released`, `released_full`, `stability_note`) and `default_changes` |
| `out/analysis/cross_program_defaults_normalised.csv`, `cross_program_q3_topics.csv` | Phase 4's normalised default rows (one stable tag and date per row, per-program field mapping already applied) and topic assignment. Use these rather than re-normalising; if Phase 5 corrected them, use the corrected files |
| `out/server_run/timeline_monthly.parquet` | monthly counts, columns `source, basis, month, dimension, value, records, domain_days, domains_peak, measured_days`; `basis=zonefile` = OpenINTEL forward TLDs (se, nu, ch, li, ee, gov, fed.us), `basis=reverse` = five RIRs |
| `out/panel_run/timeline_monthly.parquet` | the strict reverse panel, source `_pooled-afrinic-arin`; rows from 2009-04, signed-delegation series usable from 2011-05 per `docs/releases_vs_adoption.md` (check it yourself) |
| `out/analysis/prevalence_metrics.csv` + `docs/handoff/03_prevalence_metrics.md` | DS / DNSKEY / RRSIG shares per corpus with numerator and denominator |
| `out/analysis/delegation_changes.parquet` | per-delegation ledger, reverse corpus: `month, source, delegation, block, kind (sign/unsign/rollover), from_alg, to_alg` |
| `out/analysis/delegation_change_clusters.parquet`, `delegation_change_levels.parquet` | actions (month x transition x block) and level classification from `scripts/delegation_changes.py` |
| `data/rfc_checklists/dnssec_rfc_checklists.json` | RFC `publication_date`, `obsoleted_by`, `related_rfc_ids` |

## Rules that verification established (do not relearn them)

- **Reverse shares use the strict panel** (`_pooled-afrinic-arin`), never the five RIRs
  summed: their name sets overlap and summing double-counts. Per-RIR series are fine for
  counts, not for shares across RIRs.
- **Shares use signed delegations / signed zones as denominator**, never all names.
- `dimension=nsec3_iterations` counts NSEC3 **owner names** (hashed), not zones. Zone-level
  NSEC3 is `rr_type NSEC3PARAM` over `algorithm_dnskey _total`.
- **Forward coverage is short and uneven:** se and nu 2016-06, gov and fed.us 2017-05, ee
  2019-07, ch and li 2020-05, and every forward TLD **ends 2023-12** (fed.us 2022-10). The
  reverse corpus runs to 2026-08. An event without 12 months of before-period and 12 of
  after-period in a corpus has no event study in that corpus: say so, per TLD.
- **Release date = the stable release row's `released`**; if a default row carries
  `first_public_tag`, the public release is the event. Never use `release_dates.json`.
- 97% of corpus months contain some release. **No single release can be credited with an
  adoption step**; every alignment is tested against a chance rate that preserves each
  program's own release clustering (circular shift within the program's span, seed
  20260929, 1,000 draws) and, for trends, against a detrended series (centred 25-month
  rolling median). A 90% band means about 2.5 of 25 offsets fall outside by chance; report
  observed against that.
- Every forward adoption jump in earlier work belonged to one of two registry operators and
  was paired across that operator's TLDs. An event study over that population measures
  whether a dozen organisations moved. State this wherever a forward result is reported.
- An automatic update changes what a newly signed zone gets; it does not re-sign an existing
  zone. A spike made of rollovers of already-signed delegations is not a default-change
  effect, whatever the lag.

## Observable mapping

Only signer-side defaults can show up in published zone data. Map each default row to an
observable by `mechanism` and before/after text, and list the mapping as a table in your
output. Starting point (extend, do not guess):

| mechanism / topic | forward observable | reverse observable |
|---|---|---|
| alg-ecdsa (ECDSA P-256 default) | `algorithm_dnskey` 13 share of signed zones | `algorithm_ds` 13 share of signed delegations (panel) |
| alg-rsa-sha2 (RSASHA256 default) | `algorithm_dnskey` 8 | `algorithm_ds` 8 |
| ds-digest (SHA-256 / SHA-384 DS) | `digest_type_ds` 2 / 4 | `digest_type_ds` 2 / 4 |
| nsec3, nsec3-iterations (signer NSEC3 defaults) | `rr_type NSEC3PARAM` share; `nsec3_iterations` owner-name counts by value | not observable |
| cds-cdnskey | `rr_type CDS` / `algorithm_cds` | not observable |
| validation, trust-anchor, trust-anchor-5011, validator limits | **not observable** in zone data; say so per row | not observable |

Validator limits (e.g. NSEC3 iteration caps) act on zones only indirectly, by making
non-compliant zones fail; test them as events on the NSEC3 iteration series, clearly labelled
as indirect.

## Questions

1. **Per program, per stable release.** For each program, every stable release is an event.
   For each mapped observable the program's rows touch, compute the detrended change in the
   3 months after against the 3 before, in each corpus with coverage, and the program-level
   superposed-epoch mean with the circular-shift null. One table per program: releases
   tested, observed statistic, null percentile, and whether any single release sits outside
   the 90% band more often than 10% of releases would by chance.
2. **Default-change events.** For each default row with an observable: the event study
   (12 months either side, detrended) in each corpus with coverage, split by
   `applies_on_upgrade` and `opt_in`. Report each row with its chance band. A row with no
   before-period gets "no test", not a number.
3. **Manual against automatic, and at which level.** Using the reverse ledger: for the
   months within 3 months after each signer default change of a mapped algorithm, the
   distribution of action sizes (1, 2-4, 5-9, 10-49, 50-99, 100+ delegations per
   month x transition x block) and the level (single delegation / one block / concentrated /
   diffuse) of the matching transitions (e.g. rollovers and new signings to algorithm 13
   after an ECDSA default), against the same distributions in all other months. A shift
   toward large single-block actions after a default change is what an automatic update
   would look like; test the difference with a permutation over months. Report per RIR where
   counts allow, and state plainly that "action size" is a proxy: one operator automating
   one delegation is indistinguishable from a manual edit.
4. **Adoption spikes, attributed or not.** Using the spike definition in
   `scripts/program_rfc_cases.py` (`spikes()`, floors 300 forward / 30 reverse), list each
   spike in each mapped observable with: the nearest preceding verified release per program,
   the nearest preceding default change of that mechanism, the lag, whether the spike is new
   signings or rollovers (ledger), and the chance of a random month having a relevant default
   change within 3 months before it. Say for each spike whether the software alignment beats
   chance; most will not.
5. **Successor RFC while the predecessor is still deploying.** For each checklist RFC with an
   `obsoleted_by` or a clear successor in `related_rfc_ids` that has an observable (e.g.
   RFC 5155 NSEC3 iterations and RFC 9276; RFC 8624 algorithm guidance and the algorithms it
   deprecates; SHA-1 DS and SHA-256), the predecessor's deployment share in each corpus in
   the month the successor was published, and its trajectory after (did deployment of the
   predecessor keep rising, flatten, or fall; how many months until it fell below half its
   peak). No causal language.

## Output

1. `scripts/software_vs_adoption.py` -- deterministic (seed 20260929), reads only the inputs
   above; saves after each question.
2. `out/analysis/software_vs_adoption.json` (one key per question, plus `observable_mapping`,
   `excluded`, `notes`) and `out/analysis/software_vs_adoption_<question>.csv`, long form.
3. `tests/test_software_vs_adoption.py` -- pins the observable mapping, the strict-panel rule
   (assert no reverse share uses summed RIRs), the seed, and three event results you checked
   by hand.
4. `docs/handoff/07_software_vs_adoption.md` -- per program: what was tested, what beat
   chance, what did not, and what could not be tested and why; then questions 3-5. Plain
   sentences, no parentheticals; each table with the command that recomputes it. End with
   a section "Changed from the earlier analysis".

Do not leave background polling loops running; never use `pgrep -f <pattern>` as a loop exit
condition. End with a short report: files, the answer to each question in two sentences,
and what you could not determine.
