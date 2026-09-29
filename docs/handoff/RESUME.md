# Resume point -- software-timelines-v2 (written 2026-09-28, session hit its usage limit)

## What this branch is doing

Staged pipeline, one fresh agent per stage, handoff files between stages:

1. Phase 1 -- per-program release + changelog timelines (8 agents, brief in `00_phase1_brief.md`)
2. Phase 2 -- handoff file for Phase 1 outputs
3. Phase 3 -- fresh adversarial verification of Phase 1
4. Phase 4 -- cross-program comparison, then Phase 5 verification
5. Phase 6 -- prevalence metrics (% of unique domains per month with >=1 DS / DNSKEY / RRSIG), per corpus, plus SecSpider if obtainable
6. Phase 7 -- each program's update timeline vs adoption spikes in the reverse (RIR) and OpenINTEL corpora, with chance-rate controls
7. Phase 8 -- final notebook `notebooks/dnssec_software_vs_adoption.ipynb`, verified by a fresh agent

## State when the session stopped

Clones: `out/software_repos/*.git` (bare, blob-less; re-clone with `bash scripts/clone_dns_software.sh out/software_repos` if missing).
Python: rebuild with `python3 -m venv <scratch>/venv && pip install -r requirements.txt python-pptx pytest matplotlib pillow nbformat nbclient ipykernel`.

Phase 1 outputs present at stop time -- check `ls data/software/timelines/`:
- kresd.json / kresd.md -- DONE (98 tags, 136 keyword rows, 18 default-change rows, 16 CVE rows). Notable: CVE-2021-40083 code fix is in v5.3.2 not 5.4.2; validation on by default from 4.0.0; NSEC3 iteration cap 150 in 5.3.1, 50 in 5.7.1/6.0.6.
- The other seven agents (bind9, unbound, nsd, knot, opendnssec, pdns-auth, pdns-rec) were still running. They write only to `data/software/timelines/<program>.{json,md}` and do not commit. Whatever files exist when you resume are their output; a missing file means that agent did not finish -- re-run that program with the brief.
- Phase 6 agent was still running; expected outputs: `scripts/prevalence_metrics.py`, `out/analysis/prevalence_metrics.{json,csv}`, `reporting/charts/prevalence/`, `docs/handoff/03_prevalence_metrics.md`, `tests/test_prevalence_metrics.py`, `data/external/secspider/README.md`.

## Update 2026-09-29 (second resume)

- knot and nsd outputs found complete; committed as wip alongside kresd (d07f9e97).
- bind9, unbound, opendnssec, pdns-auth, pdns-rec re-spawned with the Phase 1 brief.
- `02_phase3_verify_brief.md` written; Phase 3 verifiers launched for kresd, knot, nsd
  while the five run. Verifier output goes to `docs/handoff/verify/<program>.md`.
- Scratch venv rebuilt; full suite green on the branch.

## Update 2026-09-29, second cutoff (usage limit hit again mid-run)

Done and committed this session:
- d07f9e97 knot + nsd Phase 1 outputs (wip, unverified)
- 2a7c4d42 `02_phase3_verify_brief.md`
- 86035c04 kresd: Phase 3 PASS WITH CORRECTIONS, all 5 corrections applied -> kresd is the
  first fully verified timeline. Its report also proved the CVE INVENTORY is wrong for
  CVE-2021-40083 (fix is first in v5.3.2, inventory says 5.4.2) -- `data/software/
  cve_inventory.json` `fixes.kresd` still needs that correction; deferred while Phase 1
  agents were reading the file.
- this commit: nsd Phase 3 report `docs/handoff/verify/nsd.md` (PASS WITH CORRECTIONS,
  201 checks / 10 failed / 8 corrections). **Corrections NOT yet applied.**

Agents that were still running at cutoff (they write files, never commit; whatever exists
when you resume is theirs -- a missing file means re-run with the brief):
- Phase 1: bind9, unbound, opendnssec, pdns-auth, pdns-rec -> `data/software/timelines/<p>.{json,md}`
- Phase 3: knot -> `docs/handoff/verify/knot.md`

## Update 2026-09-29, third resume

- knot and nsd corrections applied and committed (this commit); with kresd that is three of
  eight timelines fully verified. Each pass asserted every current value before changing it
  and wrote nothing on any failure -- two early runs were stopped that way (a guessed .md
  anchor; a `\1084c...` group-reference trap) before touching a file.
- opendnssec verified and corrected (136cce6d) -- FOUR of eight timelines done: kresd, knot, nsd, opendnssec.
- bind9, unbound (writing incrementally) and pdns-auth Phase 1 running. pdns-rec still to run;
  keep concurrency at three -- six-plus agents exhausted the session limit twice.
- Inventory edits still pending (blocked while Phase 1 agents read the file):
  `fixes.kresd` CVE-2021-40083 -> 5.3.2; `by_product.nsd` CVE-2019-13207 published 2019-07-03.

## Update 2026-09-29, fourth cutoff (usage limit hit again)

VERIFIED + CORRECTED, 5 of 8: kresd (86035c04), knot + nsd (be757115), opendnssec
(136cce6d), unbound (83ac2787). Each verify report is in docs/handoff/verify/.

Builders still running at cutoff (they write files, never commit; partial output is
usable -- each writes the release list first): bind9, pdns-auth (pdns-auth.json already
appearing), pdns-rec. Check `ls data/software/timelines/`; a missing .md means re-run
with the Phase 1 brief. Keep concurrency at three.

Inventory corrections APPLIED (9cd7b41d): all six, each row carrying a `correction` field
naming its verify report. Do not re-apply; the pass asserts pre-change values and would refuse.
out/analysis/cve_crossref.json and its CSVs are deliberately NOT regenerated until the last
three timelines are verified, so the latency figures move once.
Pattern behind five of the six: the NVD scrape names the next MASTER release because
branch point releases never touch doc/Changelog; the branch tag shipped the fix earlier.

## Update 2026-09-29, fifth resume

- pdns-auth stage 1 (196 releases with dates) committed as 3b0f2e37; its builder resumed for
  stages 2-4 on top of it. bind9 (4th attempt) and pdns-rec (3rd) builders re-spawned with the
  instruction to write the release list FIRST and save after every stage.
- Three builders running; nothing else can proceed until they report.

## Update 2026-09-29, sixth resume -- Fable monthly spend limit

- Fable's MONTHLY spend cap now rejects new subagents on that model (not a session window;
  it will not reset in hours). Owner chose to run the remaining builders on Sonnet.
- All eight programs now have dated release lists AND changelog entries on disk (a67d7b72):
  bind9 852 releases / 1,383 entries, pdns-auth 196 / 330, pdns-rec 262 / 255. Only
  default_changes[] and cve_fixes[] are missing for those three.
- Phase 2 index written: `01_program_timelines.md` (51466e9d). Task #2 done.
- Three Sonnet builders spawned for bind9 / pdns-auth / pdns-rec stages 3-4, each told to
  keep the existing rows untouched and save after every stage. Their verifiers (Phase 3)
  should also run on Sonnet if Fable is still capped.

## Next steps, in order

1. `git status`; commit any timeline / verify files the agents left, as wip.
2. Apply nsd's 8 corrections from `docs/handoff/verify/nsd.md` to `nsd.{json,md}` -- same
   method as kresd (86035c04): assert each current value before changing it, re-run one
   proving command per correction, commit. The two SVN-era default-change rows (2.2.0,
   2.3.0) are the substantive ones: wrong commit attribution and a tag that does not
   contain its commit.
3. Apply knot's corrections when `verify/knot.md` exists; same method.
4. Fix `cve_inventory.json` `fixes.kresd` CVE-2021-40083 -> 5.3.2 (only once no Phase 1
   agent is running).
5. Spawn Phase 3 verifiers for the five new timelines with `02_phase3_verify_brief.md`;
   apply their corrections.
6. Phase 2 `01_program_timelines.md` index, then Phase 4 onward per the task list.

## State at e0cb29de (2026-09-29)

- Verified and corrected (7/8): kresd, knot, nsd, opendnssec, unbound, bind9 (`verify/bind9.md`).
- pdns-auth verified and corrected (26dbf70b); verifier confirmed all five inventory disagreements.
- pdns-rec: stages 3-4 committed 6e24c14d (21 default rows, 52 CVE rows); Phase 3 verifier (Sonnet) was running.
- Inventory: 82 bind9/pdns-auth corrections applied (52290c82). pdns-rec's disagreements (its gap 10) after its verifier.
- Phase 4 brief ready: `04_phase4_brief.md` (3b263234); add pdns-rec's field mapping once verified.
- Then regenerate `01_program_timelines.md` (stale for bind9/pdns-auth/pdns-rec) and
  `cve_crossref` once; Phase 4 onward.

### State at a931e8d6 (2026-09-29)

- Phases 1-3 done: eight timelines verified and corrected; bind9 gained 23 fixes-only CVE rows
  (207). Phase 2 index regenerated by `scripts/build_timeline_index.py`.
- `cve_inventory.json` now agrees with every verified timeline row (batches in
  `corrections_log`); PowerDNS/BIND rows that are not the credited program's fix carry
  `not_applicable`, which `cve_crossref.py` skips.
- CVE results rebuilt (d63a7ca8): 434 CVEs, 178 dated fixes, median -8 d; KeyTrap four
  codebases within 7 days (was 148); PowerDNS Auth 0 DNSSEC CVEs (was 3). `docs/cve_crossref.md`,
  `docs/rfc_why.md` and both affected decks regenerated. Suite: 943 passed.
- Phase 4 committed unverified (02650d6b): `scripts/cross_program.py`, `out/analysis/cross_program*`,
  `docs/handoff/04_cross_program.md`. Phase 5 verifier was running -> `verify/phase4_cross_program.md`.
- Phase 5 done (report `verify/phase4_cross_program.md`); data fixes 54400276; Phase 4 rerun 263b2d90.
- Phase 7 committed unverified (a2e2bf1c). Verifier was running ->
  `verify/phase7_software_vs_adoption.md`. It also judges two data issues Phase 7 raised that may
  affect earlier outputs: (1) panel_run + delegation ledger dated one month after server_run reverse;
  (2) domains_peak non-additive across values (Phase 7 uses domain_days). Apply its corrections
  and any "impact on earlier analyses" fixes, then Phase 8 with `08_phase8_brief.md` (4d337c09).

## To resume

1. `git checkout software-timelines-v2`; list `data/software/timelines/` and `docs/handoff/`.
2. Re-spawn Phase 1 for any program without a `.md`, using `00_phase1_brief.md` verbatim.
3. When all eight exist: write `01_program_timelines.md` (Phase 2), then spawn verifiers (Phase 3) that re-derive samples from the clones -- dates, tag containment, default-change commits.
4. Continue down the task list. Do not skip a verification stage; three earlier claims in this project failed only at verification.

Standing rules carried over: test every release-timing claim against the chance rate before reporting it; shares use signed delegations / signed zones as denominator, never all names; never attribute an adoption step to a single release.
