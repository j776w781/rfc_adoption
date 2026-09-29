# Phase 8 brief: the final notebook

For a fresh agent with no other context. Read this file in full first.

## Goal

One notebook, `notebooks/dnssec_software_vs_adoption.ipynb`, that answers the owner's
question from the verified outputs of Phases 1-7:

> For each program (bind9, unbound, knot, kresd, nsd, opendnssec, pdns-auth, pdns-rec), for
> each version release, does adoption in OpenINTEL and the RIR reverse data follow it? What
> is the split between operator manual changes and automatic changes due to version
> updates, and at which operator level does a change happen? Is a newer RFC published while
> its predecessor is still being deployed?

The owner has said, of earlier notebooks: "all the graphs suck, make the graphs actually
meaningful, I need to understand the metrics", "instead of comparing all of them I want a
graph for each program separately", and asked "what are the lines above?" and "what are
delegation changing?". So: **one clearly titled section per program**, every chart with a
subtitle that states the metric, its numerator and denominator, and the corpus; every line
or band explained in text directly under the chart; no chart whose reading needs the code.

Repo root `/mnt/shared/Documents/University/year2/DNSSEC/rfc_adoption`, branch
`software-timelines-v2`. Do not commit.

## Inputs (read-only; every figure must derive from these)

| path | what |
|---|---|
| `data/software/timelines/<program>.json` | verified releases, default changes, CVE fixes |
| `out/analysis/cross_program.json` + CSVs, `docs/handoff/04_cross_program.md` | Phase 4 (verified): mechanism matrix, RFC lags, topics, leaders, CVE latency, cadence, coordination |
| `out/analysis/software_vs_adoption.json` + CSVs, `docs/handoff/07_software_vs_adoption.md` | Phase 7: per-program release tests, default-change event studies, manual-vs-automatic and level, spikes, successor RFCs. Use its verified version (see `docs/handoff/verify/phase7*.md` if present) |
| `out/analysis/prevalence_metrics.csv`, `docs/handoff/03_prevalence_metrics.md` | DS / DNSKEY / RRSIG shares per corpus |
| `out/analysis/cve_crossref.json` | CVE record (434 CVEs), per-program DNSSEC counts |
| `out/server_run/timeline_monthly.parquet`, `out/panel_run/timeline_monthly.parquet`, `out/analysis/delegation_changes.parquet` | only if a figure needs a series Phase 7 did not export; same rules as Phase 7 (strict panel for reverse shares, signed denominators) |

Do not recompute any statistic Phase 4 or 7 already produced; plot and quote it. If a
number you need is missing, compute it in a clearly marked cell and say it is new.

## Data conventions fixed on 2026-09-29 (use them; do not reintroduce the old ones)

- **Reverse month labels:** label M = the zone state at 00:00 UTC on the 1st of M, in the server
  run, the panel run and the delegation ledger alike (the server run was relabelled; see
  `out/server_run/month_labels_utc.json`). A change between labels M-1 and M happened in calendar
  month M-1; say so on any chart that marks a release against reverse data.
- **Forward shares** are mean daily shares: summed daily numerator counts over summed daily
  denominator counts (`domain_days`), never a ratio of two peak days. `prevalence_metrics.csv`
  carries `numerator_domain_days` / `denominator_domain_days`; its `pct` is already correct.
- **Reverse shares** come from the strict panel `_pooled-afrinic-arin` only.
- **Phase 7's primary test** is the step test (departure from the 24-month pre-event trend over
  the 12 months after); its "transient deviation" test is secondary. Plot the step test's
  percentile per event against its null; say which programs have no Q1 test and why (bind9:
  releases fill most months, so a shifted schedule cannot differ from the real one).
- Phase 7 has a second verification running (`docs/handoff/verify/phase7_revision.md`); if it
  exists when you finish, check whether any number you quote changed, and say so.

## Build method (learned the hard way)

- Write `notebooks/build_software_vs_adoption_notebook.py` that assembles the notebook
  with `nbformat` (`md()` / `code()` helpers as in `notebooks/build_software_notebook.py`),
  then execute it with `nbclient` so outputs are embedded, then save. Charts also saved to
  `reporting/charts/software_vs_adoption/<nn>_<name>.png`.
- Inside `code(r"""...""")` cells never use `"""` docstrings; use `'''` or comments.
- In regex replacement strings use `\g<1>` before digits, never `\1` followed by a digit.
- Python: `/tmp/claude-1000/-mnt-shared-Documents-University-year2-DNSSEC-rfc-adoption/009fe9c8-8f6c-489b-9085-0e0b381788e0/scratchpad/venv/bin/python`
  (pandas, pyarrow, matplotlib, nbformat, nbclient, ipykernel; kernel name `rfcadopt`).

## Chart rules (the project's validated palette and the owner's complaints)

- Palette: categorical S1 `#2a78d6`, S2 `#eb6834`, S3 `#1baf7a` in that fixed order, at most
  three categorical series per chart; more categories -> small multiples or fold into
  "other". Sequential ramp `#cde2fb #9ec5f4 #6da7ec #2a78d6 #1c5cab #104281`. Emphasis red
  `#d03b3b` only for a highlighted event. Ink `#0b0b0b` (primary), `#52514e` (secondary),
  `#898781` (muted); grid `#e1e0d9`; surface `#fcfcfb`. Text never in series colour.
- One y-axis per chart; never a dual axis. Year axes via a helper using
  `MaxNLocator(integer=True)` so a year never prints twice.
- Title = the finding in words; subtitle = metric, numerator / denominator, corpus, window.
  Title and subtitle must not overlap; legends never sit on data.
- Every null or chance band is drawn and named in the legend ("90% of circular shifts"),
  and the text under the chart says how many points fall outside it against how many would
  by chance.
- Release markers: stable releases only, public release where the row has one. Default
  changes marked distinctly from ordinary releases and labelled with the row id.
- Replace line-heavy "superposed epoch" plots with something a reader can parse: e.g. a
  per-release dot plot of the detrended 3-month change with the null band as a shaded
  interval, sorted by date, default-change releases highlighted.
- After rendering, open each PNG and look at it for overlaps and overflow before accepting.

## Structure

1. **What this notebook answers, and the short answer.** Five sentences, each tied to a
   later section. Then a "how to read every chart" box: corpora (forward TLDs and their
   coverage window; reverse strict panel), denominators, what "detrended", "null band" and
   "action size" mean.
2. **The adoption series themselves.** DS / DNSKEY / RRSIG shares and the main algorithm
   shares per corpus, so every later chart has a reference.
3. **One section per program** (eight), same layout each: release cadence strip (stable
   releases, default changes marked); its default changes with observables and event-study
   result (or "not observable" / "no test", with the reason); the per-release dot plot
   against the null; its CVE fix latency; a three-to-five sentence verdict.
4. **Across programs.** Mechanism x program first-release matrix as a heatmap-style table;
   RFC-to-code lag per RFC; the leader/follower result with its chance baseline; the KeyTrap
   coordination (four codebases within seven days, all before publication).
5. **Manual against automatic, and operator level.** Action-size distributions after
   default changes against other months, per RIR where Phase 7 reports it; level (single
   delegation / block / concentrated / diffuse). Explain in plain words what a "delegation
   change" is (a reverse-DNS zone that gained, lost or changed its DS algorithm between two
   monthly snapshots) and that action size is only a proxy.
6. **Successor RFCs published while the predecessor still deploys.**
7. **What this cannot show**, from Phases 4 and 7, in plain sentences.

## Verification before you finish

- Execute the notebook top to bottom from a fresh kernel; zero errors.
- For ten numbers quoted in markdown cells, assert in a final hidden-by-default cell that
  they equal the values in the source JSON (so a later rerun that changes data fails loudly).
- `python -m pytest -q` passes.

End with a short report: files written, number of figures, the ten asserted numbers, and any
figure you could not make and why.
