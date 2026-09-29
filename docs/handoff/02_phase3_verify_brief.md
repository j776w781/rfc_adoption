# Phase 3 brief: adversarially verify one program's timeline

You are checking, not building. A Phase 1 agent produced
`data/software/timelines/<program>.json` and `.md` from the bare clone under
`out/software_repos/`. Assume every row is wrong until you have re-derived it
yourself from the clone. Your job is to find the rows that do not survive.

Three earlier claims in this project failed only at verification. Each was a
number that looked plausible on the page. Do not read the `.md` and nod.

## Inputs

| program | clone | tag pattern |
|---|---|---|
| bind9 | out/software_repos/bind9.git | `v9.x.y`; odd minors >= 9.13 are development, `stable: false` |
| unbound | out/software_repos/unbound.git | `release-x.y.z` |
| nsd | out/software_repos/nsd.git | `NSD_x_y_z_REL` |
| knot | out/software_repos/knot.git | `vx.y.z` |
| kresd | out/software_repos/kresd.git | `vx.y.z` |
| opendnssec | out/software_repos/opendnssec.git | `x.y.z` / `release/x.y.z` |
| pdns-auth | out/software_repos/pdns.git | `auth-x.y.z` (shared repo) |
| pdns-rec | out/software_repos/pdns.git | `rec-x.y.z` (shared repo) |

The JSON schema (top level): `program, product, role, generated, tag_pattern,
release_count, span, branch_note, releases[], default_changes[], cve_fixes[],
news_edits[], sources, gaps[]`.

`releases[]`: `version, tag, released, released_full, stable, commit,
changelog_path, total_entries, changelog_entries[], stability_note, entries_note`.
`default_changes[]`: `version, released, title, mechanism, before, after,
applies_on_upgrade, opt_in, commits[{commit, commit_date, subject,
tag_contains_confirmed}], documentation, rfcs, cves, attribution`.
`cve_fixes[]`: `cve, in_inventory_by_product, in_inventory_fixes, nvd_published,
applicable, mechanism, dnssec_related, fix_tag, fix_released,
fix_commits[{commit, commit_date, subject, first_tag, tag_contains_confirmed}],
latency_days`.

## What to check, and how

Run every command yourself. A check you did not run is a check that failed.

### A. Release dates — random 20 releases, plus the first and last

    git -C <clone> log -1 --format=%cI <tag>^{commit}

must equal `released_full`. Also confirm `stable` against the tag pattern rule
(BIND odd minors; rc/beta/alpha/dev suffixes anywhere). FAIL on any mismatch.

Known trap: tag-object dates. Tags imported from SVN/CVS carry the migration
day (all Unbound tags before 1.6.3 show 2017-06-13; old BIND and NSD tags too).
If a `released` value equals a migration day, the builder used the tag date.

### B. Default changes — every row, no sampling

These are the load-bearing rows and there are few of them. For each:

1. `git -C <clone> show --stat <commit>` — the changed files must be product
   code or shipped configuration, **not** tests, docs, CI, or examples. A
   changed test fixture reads identically to a changed default in a log; BIND
   commit `ca391cd0` ("Change the default algorithm to RSASHA256") touched only
   `bin/tests/system/conf.sh.*` and was wrongly reported as a product default
   once already.
2. `git -C <clone> tag --contains <commit> | grep -x <tag>` — must hit.
3. Is `<tag>` the **earliest** stable tag containing it? Backports mean the
   same change lands on several branches under different SHAs. Search
   `git log --all --grep='<distinctive words>'` for sibling commits and take
   the earliest stable tag across all of them. If an earlier tag exists, FAIL
   and name it. (BIND ECDSA read 9.10.0/2014 for exactly this reason; it
   shipped in 9.8.4/2012.)
4. `before` and `after` must be readable from the diff or the cited
   documentation at that tag (`git show <tag>:<path>`), not inferred from a
   version number.
5. `applies_on_upgrade` vs `opt_in`: a default in a shipped example config
   (OpenDNSSEC `kasp.xml.in`) or behind an opt-in feature (BIND
   `dnssec-policy`) is not the same as a default that changes behaviour on
   upgrade. FAIL if the flag contradicts what the diff shows.
6. `attribution == "approximate"` is allowed only with a stated reason.

### C. CVE fixes — every row

1. The CVE must be in `data/software/cve_inventory.json` under this product
   (`by_product`) or in its `fixes`. If `in_inventory_by_product` is false and
   `applicable` is true, the row must say why.
2. `fix_tag` must contain every `fix_commits[].commit`
   (`git tag --contains`), and must be the earliest stable tag that does —
   check sibling branches as in B.3. A fix cherry-picked to a maintenance
   branch usually ships there first.
3. `latency_days` = `fix_released` − `nvd_published` in days; recompute.
   Negative is expected (coordinated disclosure) and is not an error.
4. For pdns-auth / pdns-rec: the fix tag must be the right product's prefix.
   A recursor CVE with an `auth-*` fix tag is a FAIL.

### D. Changelog entries — random 20 kept entries across at least 8 releases

1. `git -C <clone> show <tag>:<changelog_path> | grep -F '<line>'` — present.
2. `git -C <clone> show <previous stable tag>:<changelog_path> | grep -F '<line>'`
   — **absent**. An entry present at both is re-attributed from an older
   release and is a FAIL. (BIND's `CHANGES` is per-branch; an old entry sits
   under whatever marker the branch carries.)
3. `mechanism` matches the text. `cds-cdnskey` on a line that only says
   ECDSA is the known false positive (`CDS` is a substring of `ECDSA`).
4. `total_entries` for that release: recount from the diff of the changelog
   between the two tags. Off by more than 10 % is a FAIL.

### E. Coverage

1. Count stable tags in the clone with the pattern; compare to
   `release_count` and to the number of `releases[]` with `stable: true`.
2. Any stable tag absent from `releases[]` is a FAIL with the tag named.
3. Read `gaps[]`. Each gap should be a thing that could not be determined,
   not a thing that was skipped. If you can determine one in five minutes,
   the gap is a FAIL.

## Output

Write **only** `docs/handoff/verify/<program>.md`. Do not edit the timeline
files; you report, the next stage corrects.

Structure:

1. Verdict line: `PASS` / `PASS WITH CORRECTIONS` / `FAIL`, and one sentence.
2. A table with one row per check you ran: `section, row identified (tag /
   commit / cve), command, expected, observed, result`. Every row. Commands
   verbatim so anyone can paste them.
3. `## Corrections required` — for each failing row: the field, the wrong
   value, the right value, and the command that proves it. If none, say so.
4. `## Not verifiable` — anything you could not check and why.
5. Totals: checks run, passed, failed, by section.

## Standards

* Sample randomly and say how (`shuf --random-source=<(yes)` or a stated seed).
* Never accept `tag_contains_confirmed: true` from the JSON; run it.
* A row you could not reproduce is a FAIL, not a "probably fine".
* If the `.md` and the `.json` disagree with each other, that is its own FAIL.
* Do not commit.
