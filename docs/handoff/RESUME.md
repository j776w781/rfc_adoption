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
- opendnssec Phase 1 output exists (144 tags, 65 stable); its Phase 3 verifier is running.
- bind9 and unbound Phase 1 running (third attempt). pdns-auth, pdns-rec still to run;
  keep concurrency at three -- six-plus agents exhausted the session limit twice.
- Inventory edits still pending (blocked while Phase 1 agents read the file):
  `fixes.kresd` CVE-2021-40083 -> 5.3.2; `by_product.nsd` CVE-2019-13207 published 2019-07-03.

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

## To resume

1. `git checkout software-timelines-v2`; list `data/software/timelines/` and `docs/handoff/`.
2. Re-spawn Phase 1 for any program without a `.md`, using `00_phase1_brief.md` verbatim.
3. When all eight exist: write `01_program_timelines.md` (Phase 2), then spawn verifiers (Phase 3) that re-derive samples from the clones -- dates, tag containment, default-change commits.
4. Continue down the task list. Do not skip a verification stage; three earlier claims in this project failed only at verification.

Standing rules carried over: test every release-timing claim against the chance rate before reporting it; shares use signed delegations / signed zones as denominator, never all names; never attribute an adoption step to a single release.
