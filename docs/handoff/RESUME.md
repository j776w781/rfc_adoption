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

## To resume

1. `git checkout software-timelines-v2`; list `data/software/timelines/` and `docs/handoff/`.
2. Re-spawn Phase 1 for any program without a `.md`, using `00_phase1_brief.md` verbatim.
3. When all eight exist: write `01_program_timelines.md` (Phase 2), then spawn verifiers (Phase 3) that re-derive samples from the clones -- dates, tag containment, default-change commits.
4. Continue down the task list. Do not skip a verification stage; three earlier claims in this project failed only at verification.

Standing rules carried over: test every release-timing claim against the chance rate before reporting it; shares use signed delegations / signed zones as denominator, never all names; never attribute an adoption step to a single release.
