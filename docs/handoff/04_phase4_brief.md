# Phase 4 brief: cross-program comparison

For a fresh agent with no other context. Read this file in full before starting.

## Goal

Compare the eight DNS programs **with each other and with RFC publication**, using only
the verified Phase 1 timelines. No adoption data in this phase (that is Phase 7). Every
number you publish must trace to named rows in the timeline files, so a Phase 5 verifier
can recompute it.

Repo root: `/mnt/shared/Documents/University/year2/DNSSEC/rfc_adoption`, branch
`software-timelines-v2`. Do not commit; the session commits your output.

## Inputs (read-only)

| path | what |
|---|---|
| `data/software/timelines/<program>.json` | eight programs: bind9, knot, kresd, nsd, opendnssec, pdns-auth, pdns-rec, unbound. Each passed a Phase 3 verification; `verification.phase3` or `docs/handoff/verify/<program>.md` lists what was corrected |
| `data/software/timelines/<program>.md` | human-readable form of the same; the JSON wins where they differ |
| `docs/handoff/00_phase1_brief.md` | the schema the timelines were built to |
| `data/rfc_checklists/dnssec_rfc_checklists.json` | `rfcs[]` with `rfc_id` ("RFC 5155"), `publication_date`, `obsoleted_by`, `related_rfc_ids`, `status` -- the only RFC date source |
| `data/software/software_support.json` | Arc A support rows (first release implementing an RFC); use only to cross-check, and report disagreements with the timelines |
| `out/software_repos/*.git` | clones, for spot checks only |

Roles (from each file's `role`): signers / authoritative -- bind9, knot, nsd, opendnssec,
pdns-auth; validating resolvers -- bind9, unbound, kresd, pdns-rec. bind9 is both. Compare
within a role unless the question is role-independent (CVE latency, release cadence).
pdns-auth and pdns-rec share one repository (`pdns.git`); count a shared fix once per
**codebase** when asking about coordination.

## Normalisation (the schemas differ -- use exactly this mapping)

Stable release dates always come from the program's own `releases[]` row
(`released`, calendar date; `released_full` for ordering within a day -- compare as UTC
instants, never as strings with offsets). Only `stable: true` rows count as releases.
BIND odd minors >= 9.13 are development (`stable: false` already).

### default_changes[] -> (program, row id, mechanism, kind, first stable tag, date, opt_in, applies_on_upgrade)

| program | row id | first stable tag field | date to use |
|---|---|---|---|
| bind9 | `id` | `first_stable_tag` | releases[tag].released (= `first_stable_date`) |
| knot | index + `version` | releases row with that `version` | releases[...].released (= row `released`) |
| kresd | index + `version` | releases row with that `version` | releases[...].released (= row `released`) |
| nsd | index + `version` | `tag` | row `released` for 2.3.0 only (the tag NSD_2_3_0_REL is manufactured on a pre-release commit; see the row's `released_note`); releases[tag].released otherwise |
| opendnssec | index + `version` | `first_stable_tag` | `first_stable_released` |
| pdns-auth | index + `version` | `stable_tag` | releases[stable_tag].released. **Not** row `released`: that is the first pre-release date |
| unbound | index + `version` | `tag` | releases[tag].released (= row `released`) |
| pdns-rec | inspect when you start; it was the last built. Write its mapping into your output before using it | | |

Assert for every row that the tag exists in `releases[]` with `stable: true`; list any
row that fails instead of guessing.

`mechanism` vocabulary in use: `alg-ecdsa, alg-rsa-sha2, alg-gost, ds-digest, dnskey,
rrsig, nsec3, nsec3-iterations, validation, trust-anchor-5011, cds-cdnskey, other`.
`kind` differs by program (`default-changed, limit-changed, support-added, removed`, ...);
bind9 also has `value_changed` and `default_related` -- rows with `value_changed: false`
are not default changes. Keep `opt_in` exactly as recorded, and note that pdns-auth's
NSEC3 `set-nsec3` rows use `opt_in: true` in a different sense from algorithm rows (see its
gaps).

### cve_fixes[] -> (program, cve, fix tag, fix date, nvd_published, latency, dnssec_related)

| program | tag field | date field | include only if |
|---|---|---|---|
| bind9 | `first_stable_tag` | `fix_release_date` | tag not null (rows with `status` not-found / not-applicable are excluded; count them) |
| pdns-auth | `fix_tag` | `fix_released` | always (no `applicable` key by design) |
| others | `fix_tag` | `fix_released` | `applicable is True`; report `"disputed"` (unbound CVE-2019-25031..25042) separately |

Use the row's date and `latency_days` as recorded: they were verified and some carry
vendor or public dates on purpose (unbound CVE-2017-15105 = vendor 1.6.8 on 2018-01-19;
CVE-2020-28935 and CVE-2009-3602 differ from their tag row with an explanatory note).
Where a row also has `public_release_date` / `latency_days_public`, report both
latencies. `dnssec_related` is missing for bind9 and knot: do not infer it from keywords;
report those programs' DNSSEC subset as "not classified".

## Questions to answer

1. **Mechanism matrix.** For each mechanism x program: the first stable release that
   added support, changed a default, or changed a limit (separate columns by `kind`), with
   date and row id. Blank means no row, not "never supported" -- say which.
2. **Code lag vs RFC.** For each row whose `rfcs` names an RFC in the checklist: first
   stable release date minus `publication_date`, in months. Per RFC, list programs in order
   and the spread between first and last. Negative lags (shipped from a draft) are real;
   keep them.
3. **Default-flip topics.** Group default changes into these topics and give a side-by-side
   date table, one row per program, with row ids:
   ECDSA P-256 as default signing algorithm; NSEC3 iterations capped / default 0 (RFC 9276);
   validation on by default; built-in root trust anchor and RFC 5011 rollover; SHA-1 /
   RSASHA1 deprecation; CDS/CDNSKEY publication. A row belongs to a topic only by its
   `mechanism` and its before/after text -- list your assignment so it can be checked.
4. **Leader / follower.** Within each topic, which program shipped first, the median gap to
   the rest, and whether the same program leads across topics. Add a chance baseline: with
   k programs per topic, a given program leads by chance with probability 1/k; report the
   observed lead count against that expectation, and do not call a program a leader on
   fewer than three topics.
5. **Obsolescence overlap.** Using `obsoleted_by` in the checklist: for each obsoleted
   RFC that has software rows, when each program shipped the successor relative to its own
   support for the predecessor, and whether any program still ships the predecessor as a
   default after the successor RFC's publication. (Deployment of either is Phase 7.)
6. **CVE fix latency.** Per program: n included, n excluded by reason, median and IQR of
   `latency_days` (tag date), and of `latency_days_public` where present. The DNSSEC
   subset separately where classified. Negative latency means the fix shipped before NVD
   publication (embargo), which is normal.
7. **Release cadence.** Stable releases per calendar year per program; median days between
   stable releases per program and per decade. Do not compare `total_entries` across
   programs: its meaning differs (bind9 de-duplicates across branches, pdns-auth counts
   prose paragraphs).
8. **Coordinated releases.** Dates on which two or more **codebases** shipped a stable
   release within 3 days of each other that fixes the same CVE, or that ship the same
   default-flip topic. Compare the count against a circular-shift null: shift each
   program's release dates by a random offset within its own span (preserving its internal
   spacing), 1,000 draws, fixed seed 20260929, and report the observed count's percentile.
   A coincidence you cannot distinguish from the null is not a finding.

## Standing rules

- Every claim cites row ids; every aggregate lists the rows it used.
- Never attribute anything to a single release by keyword; use the rows as given.
- Test every timing coincidence against a chance rate before reporting it.
- If a timeline row looks wrong, do not fix it: list it under "suspect rows" with a
  one-line reason and a command that shows the problem.
- Write output incrementally: save after each question, so a cutoff loses at most one.

## Output

1. `scripts/cross_program.py` -- reads only the inputs above; deterministic (seed
   20260929); writes everything below. Run it with the scratch venv python or plain
   `python3` (stdlib + pandas if available).
2. `out/analysis/cross_program.json` -- one key per question, plus `normalisation`
   (the mapping actually used, including pdns-rec), `excluded_rows`, `suspect_rows`.
3. `out/analysis/cross_program_<question>.csv` -- one long-form CSV per question.
4. `tests/test_cross_program.py` -- pins at least: the per-program row counts after
   normalisation, three topic dates you checked against a clone, and the null's seed.
   Run with `python3 -m pytest tests/test_cross_program.py -q`.
5. `docs/handoff/04_cross_program.md` -- for the Phase 5 verifier: each question's answer
   in a short table, the row ids behind it, and one command per table that recomputes it.
   Plain sentences, no parentheticals; state what you could not determine and why.

End with a short report: files written, the answer to each question in one or two
sentences, suspect rows, and anything you skipped.
