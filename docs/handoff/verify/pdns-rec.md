# Phase 3 verification: pdns-rec (PowerDNS Recursor)

Files under test: data/software/timelines/pdns-rec.json and .md at 6e24c14d. Clone: out/software_repos/pdns.git (rec-* tags). Sampling: `random.seed(20260929)`.
Verdict: PASS WITH CORRECTIONS -- the release dates, CVE fix tags and defaults are reproducible except one wrong first-stable tag (38696 root anchor, rec-5.2.0 not rec-5.0.10), one wrong commit, one over-stated default row, one missing row, four meaningless 2008-2010 latencies and mislabelled mechanisms; see Corrections required.

## Section A -- release dates (DONE)

Command (per tag): `git -C out/software_repos/pdns.git log -1 --format=%cI <tag>^{commit}`; stable rule: no alpha/beta/rc/dev in tag.
Sample: `random.seed(20260929); [R[0],R[-1]] + random.sample(R[1:-1],20)` -- 22 tags, all PASS
(rec-3-0, rec-5.4.6, rec-5.0.6, rec-4.6.4, rec-5.4.0-beta1, rec-4.1.15, rec-5.4.0-alpha0, rec-4.5.5, rec-4.8.7, rec-5.4.1, rec-4.0.0-rc1, rec-5.5.0-alpha1, rec-3.1.4, rec-4.8.1, rec-5.4.5, rec-5.1.4, rec-5.4.0-alpha1, rec-5.3.0-rc1, rec-5.3.1, rec-4.1.13, rec-3.6.4, rec-4.4.0-rc1).
Expected == observed == released_full for all 22; stable flag matches for all 22.

Beyond the sample, I ran the same commands for all 262 releases[]: released_full, released (date part), commit (`git rev-parse <tag>^{commit}`) and stable flag all match: 0 mismatches. Migration-day trap: no releases[].released value repeats more than 3 times (max 3, e.g. 2020-05-19, same-day security releases), so no tag-date/migration-day artefact. Old 3.x tags carry `Z` commit times (SVN import) that are the real commit dates, not one migration day.
Tag set: `git tag -l 'rec-*'` = 262 = len(releases); no tag missing, none extra.

## Section B -- default_changes (all 21 rows) (DONE, except dnssec-default full-tag sweep noted below)

Commands used (verbatim, per commit C over the 33 distinct commits):
- B.1 `git -C out/software_repos/pdns.git show --stat=200 <C>`
- B.2 `git -C out/software_repos/pdns.git for-each-ref --contains <C> --format='%(refname:short)' 'refs/tags/rec-*'` (equivalent to `git tag --contains <C>` restricted to rec-*; equivalence proven in the "tag --contains" check below). Earliest stable tag = min over stable, non-alias tags by `%cI` converted to UTC.
- B.3 sibling search: `git -C out/software_repos/pdns.git log --all --no-merges -i --format='%H %cI %s' --grep=<subject words>` (16 greps OR-ed)
- B.4 `git -C ... show <tag>:<path>` at boundary tags.

B.1 (product code, not only tests/docs): every default_changes commit touches product code: 12ce523e7 (pdns_recursor.cc, syncres.cc), a6415142c (pdns_recursor.cc), 90e61f728 (pdns_recursor.cc 1-line default), 1bd49828f (rec-lua-conf.cc, validate.cc), 331bcdd53 (rec_channel_rec.cc), 7abbb2c9f (pdns_recursor.cc, Makefile.am), abfe6717d (dnssecinfra.cc, sodiumsigners.cc, plus a regression test), 1909556cc/d5037c4d3 (root-dnssec.hh), d377bb54f (pdns_recursor.cc, validate.cc), 575925eff/9a3ab3e4f (pdns_recursor.cc, validate.cc), edcf680eb (pdns_recursor.cc, aggressive_nsec.cc), be96358a5/2a93a7c4f (pdns_recursor.cc), 81a942071/04cee9810 (dnssecinfra.cc, rec-main.cc), a48730887 (settings/table.py), KeyTrap commits (syncres.cc, validate.cc, table.py, rec-main.cc, plus tests), 0bbbdd60a/a5f6b5be8/7f74864ae (root-dnssec.hh, table.py, plus tests), 6f2088b4f (validate.cc plus test). PASS for all 21 rows (no test-only commit).

B.2 tag containment (run, not copied from JSON): all listed commits are contained in the row's tag (117 commits run; results in /tmp/v/contains.json). PASS for the rows below except where noted.

| row (version / title) | commit | earliest stable tag containing it (UTC) | row tag | result |
|---|---|---|---|---|
| 4.0.0 dnssec introduced default process | 12ce523e7 | rec-4.0.0 (2016-07-08T09:59Z); first any tag rec-4.0.0-alpha1 | 4.0.0 | PASS tag; see correction 2 (semantic) |
| 4.0.0 process -> process-no-validate | a6415142c | rec-4.0.0; first any tag rec-4.0.0-beta1 | 4.0.0 | PASS |
| 4.5.0 process-no-validate -> process | 90e61f728 | rec-4.5.0 (2021-05-07T07:48Z); first any rec-4.5.0-alpha2; no sibling commit found | 4.5.0 | PASS |
| 4.0.0 trust anchor mgmt | 1bd49828f, 331bcdd53 | rec-4.0.0 | 4.0.0 | PASS |
| 4.0.5 Ed25519 | 7abbb2c9f, abfe6717d | rec-4.0.5 (2017-06-13T09:50Z). Sibling d1b28475a (same subject, master) first in rec-4.1.0-alpha1 -- later, not earlier | 4.0.5 | PASS |
| 4.0.5 root KSK 20326 | 1909556cc (branch) / d5037c4d3 (master) | rec-4.0.5 / rec-4.1.0 | 4.0.5 | PASS |
| 4.1.0 nsec3-max-iterations 2500 | d377bb54f | rec-4.1.0 stable; first any rec-4.1.0-alpha1 (absent from rec-4.0.9) | 4.1.0 | PASS |
| 4.2.0 signature-inception-skew | 575925eff (4.1.5), 9a3ab3e4f (4.2.0) | rec-4.1.5 (2018-11-06) has setting with default 0; rec-4.2.0 default 60 | 4.2.0 | PASS (row explicitly documents both) |
| 4.5.0 aggressive NSEC cache on by default | edcf680eb | edcf680eb sets default "0" (see below); decisive commit f24887cd8 first in rec-4.5.0 | 4.5.0 | FAIL (commit) -- correction 3 |
| 4.5.2 nsec3 2500 -> 150 | be96358a5 (branch), 2a93a7c4f (master) | rec-4.5.2 (2021-06-07T09:54Z); master commit first in rec-4.6.0 | 4.5.2 | PASS |
| 4.9.0 algos 5 and 7 auto-off | 81a942071, 04cee9810 | rec-4.9.0 (absent from rec-4.8.9 and rec-4.9.0-alpha1) | 4.9.0 | PASS |
| 5.0.0 nsec3 150 -> 50 | a48730887 | rec-5.0.0 stable (first any rec-5.0.0-rc1 / master rec-5.1.0-alpha0) | 5.0.0 | PASS |
| 5.0.2 KeyTrap x7 rows | 8cb2740c8 / a4bc14262 / 3a4cf2732 / 15e973d6d | rec-5.0.2 (08:36:36Z), rec-4.8.6 (08:47:54Z), rec-4.9.3 (12:57:07Z); master 15e973d6d first in rec-5.1.0 | 5.0.2 | PASS (see claim 3 section) |
| 5.0.10 root KSK 38696 | 0bbbdd60a (master, 2024-11-06), a5f6b5be8 (5.0.x), 7f74864ae (5.1.x) | **rec-5.2.0 (2025-01-10T09:04:52Z)**; rec-5.0.10 2025-04-08T08:14:43Z; rec-5.1.4 2025-04-08T08:15:40Z | 5.0.10 / 2025-04-08 | FAIL -- correction 1 |
| 4.4.0 zone-flag / REVOKE | 6f2088b4f | rec-4.4.0 (2020-10-13); no sibling commits found | 4.4.0 | PASS |

B.4 before/after readable from source at the boundary tags (all run):
- dnssec default (claim 1): `git show rec-4.0.0-alpha1:pdns/pdns_recursor.cc | grep 'set("dnssec"'` = "process" (also alpha2, alpha3); rec-4.0.0-beta1, rec-4.0.0, rec-4.4.0, rec-4.4.3, rec-4.5.0-alpha1 = "process-no-validate"; rec-4.5.0-alpha2, rec-4.5.0, rec-4.9.0 = "process"; rec-5.0.0 (settings/table.py), rec-5.4.6 and rec-5.5.0-alpha1 (rec-rust-lib/table.py) default 'process'. `validate` is never the default. PASS. Boundary commits: 90e61f728 is contained by rec-4.5.0-alpha2 and not by rec-4.5.0-alpha1 (alpha1 default still process-no-validate). The full per-tag sweep is reported in the claim-1 section below.
- nsec3-max-iterations (claim 2): see the claim-2 section.
- 4.9.0 dnssec-disabled-algorithms: absent at rec-4.8.9 and rec-4.9.0-alpha1 (0 grep hits in rec-main.cc), present with default "" at rec-4.9.0 and rec-4.9.9; auto-detection via `DNSCryptoKeyEngine::verifyOne` for RSASHA1/RSASHA1NSEC3SHA1 in rec-4.9.0 rec-main.cc. PASS.
- 20326 / 19036 / 38696: `git show <tag>:pdns/root-dnssec.hh`: rec-4.0.4 {19036}; rec-4.0.5 {19036,20326}; rec-4.1.17 {19036,20326}; rec-4.2.0-alpha1/4.2.0 {20326}; rec-4.9.8/4.9.9 {20326} (no 38696 on 4.9.x); rec-5.0.9 {20326}; rec-5.0.10 {20326,38696}; rec-5.1.3 {20326}; rec-5.1.4 {20326,38696}; rec-5.2.0-alpha1, rec-5.2.0 {20326,38696}.
- aggressive-nsec-cache-size: default "0" in edcf680eb (`git show edcf680eb -- pdns/pdns_recursor.cc`); "100000" at rec-4.5.0-alpha2 .. rec-4.5.0 via f24887cd8 ("rec: Enable the aggressive NSEC cache by default, if DNSSEC is enabled", 2021-02-24), which is not in the row.

B.5 flags: applies_on_upgrade/opt_in checked against diffs: trust-anchor-management row (applies_on_upgrade False, opt_in True) is right (needs Lua config / rec_control). Ed25519 True/False is right only for builds with libsodium (row notes this). All others behaviour-changing on upgrade (True/False). No contradictions found.
B.6 attribution: 21 rows all "exact". Rows whose commit list mixes branch and master SHAs for the same change (nsec3 150, inception skew, 20326, KeyTrap, 38696) are ok; the only "approximate"-type problem is correction 3.

Additional findings on rows:
- The 4.0.0 "process" row: no stable release ever shipped `process` as default before 4.5.0 (rec-4.0.0 default is process-no-validate). Row 1 says version 4.0.0 / released 2016-07-08 with `after` "dnssec=process". The row's own note admits "Alpha-only default". Correction 2.
- Missing row (completeness): removal of 19036 in rec-4.2.0 (779032931, 2018-10-11, `pdns/root-dnssec.hh`; contained in rec-4.2.0, absent in rec-4.1.17) exists only in gaps text, no default_changes row. Correction 4.

## Section C -- cve_fixes (all 52 rows) (DONE)

Findings:
- C.1 inventory: all 52 CVEs are in `by_product.pdns-rec` (50) or `fixes.pdns-rec` (CVE-2024-25583, CVE-2024-25590; row states why, NVD date null). nvd_published matches inventory for all 50. PASS.
- C.2 containment / earliest: brief says fix_tag must contain every fix commit. Rows hold branch and master SHAs of the same fix, so no single tag contains all of them (48 rows list several SHAs). I checked instead that fix_tag contains at least one fix commit, that each commit's `first_tag` / `first_stable_tag` equals what `for-each-ref --contains` returns, and that fix_tag is the earliest stable tag (UTC) over all of a row's commits: 0 mismatches over 49 rows with commits (CVE-2006-4252, CVE-2009-4009, CVE-2009-4010 have no commit; approximate, stated). Commits named after the CVE but on auth branches (CVE-2026-33257/33260: 6908f4581, 9d5d9a3d4, 038e38a24, 9e074364d) are contained by 0 rec-* tags and 4 auth-* tags; the rec fix commits used (8a71bde55, 7aebb0fd0, b1f9b0d80, all ext/yahttp/yahttp/reqresp.cpp/.hpp) are in 5 rec tags and 0 auth tags, first rec-5.2.9 (2026-04-02), and advisory 2026-03 says "First fixed: 5.2.9" for both CVEs. The mapping (touched file and size match) is approximate and the row says so. PASS.
- C.3 latency: recomputed for all 50 rows with an NVD date: 0 arithmetic mismatches. Four rows are arithmetically right but meaningless (see item 5 below).
- C.4 every fix_tag starts with `rec-`, is in releases[] and has stable=true; none is auth-/dnsdist-. PASS. No fix_tag is one of the never-public tags (rec-4.5.0, rec-4.5.3, rec-5.0.0).
- Sibling branches: for all rows with an advisory in the tree (2022 onward) the "Not affected"/"First fixed" release lists contain no recursor stable tag earlier (UTC) than fix_tag. KeyTrap: see claim 3.
- fix_released is the tag commit date, not the public date, for embargoed releases (rec-5.0.2/4.8.6/4.9.3: commit 2024-02-06, public 13 Feb; rec-4.8.8/4.9.5/5.0.4 for CVE-2024-25583: commit 2024-04-09, changelog 24 April 2024). The rows carry `fix_changelog_released_text` and gaps[] discloses this. Not a failure.


### Section C per-row table (all 52 rows)

Commands per row: `git -C out/software_repos/pdns.git for-each-ref --contains <commit> --format='%(refname:short)' 'refs/tags/rec-*'` for every fix commit; earliest stable tag by `%cI` converted to UTC; `date -d <fix_released> - date -d <nvd_published>`; tag prefix `rec-`; inventory membership by python over data/software/cve_inventory.json.

| cve | fix_tag (stable) | earliest stable tag over its commits (UTC) | commits | latency recomputed | inventory | result |
|---|---|---|---|---|---|---|
| CVE-2006-4251 | rec-3.1.4 | rec-3.1.4 | 1 | 2 (json 2) | by_product | PASS (approximate mapping, stated) |
| CVE-2006-4252 | rec-3.1.4 | (no commit found) | 0 | 2 (json 2) | by_product | PASS (approximate mapping, stated) |
| CVE-2008-1637 | rec-3.1.7.1 | rec-3.1.7.1 | 1 | 487 (json 487) | by_product | FAIL (latency_days not meaningful: latency artefact) |
| CVE-2008-3217 | rec-3.1.7.1 | rec-3.1.7.1 | 1 | 380 (json 380) | by_product | FAIL (latency_days not meaningful: latency artefact) |
| CVE-2009-4009 | rec-3.2 | (no commit found) | 0 | 57 (json 57) | by_product | FAIL (latency_days not meaningful: latency artefact) |
| CVE-2009-4010 | rec-3.2 | (no commit found) | 0 | 57 (json 57) | by_product | FAIL (latency_days not meaningful: latency artefact) |
| CVE-2014-8601 | rec-3.6.2 | rec-3.6.2 | 1 | -41 (json -41) | by_product | PASS |
| CVE-2015-1868 | rec-3.7.2 | rec-3.7.2 | 4 | -27 (json -27) | by_product | PASS |
| CVE-2015-5470 | rec-3.6.4 | rec-3.6.4 | 2 | -147 (json -147) | by_product | PASS |
| CVE-2016-7068 | rec-3.7.4 | rec-3.7.4 | 2 | -607 (json -607) | by_product | PASS (approximate mapping, stated) |
| CVE-2016-7073 | rec-4.0.4 | rec-4.0.4 | 1 | -606 (json -606) | by_product | PASS (approximate mapping, stated) |
| CVE-2016-7074 | rec-4.0.4 | rec-4.0.4 | 1 | -606 (json -606) | by_product | PASS (approximate mapping, stated) |
| CVE-2017-15090 | rec-4.0.7 | rec-4.0.7 | 1 | -57 (json -57) | by_product | PASS (approximate mapping, stated) |
| CVE-2017-15092 | rec-4.0.7 | rec-4.0.7 | 1 | -57 (json -57) | by_product | PASS (approximate mapping, stated) |
| CVE-2017-15093 | rec-4.0.7 | rec-4.0.7 | 1 | -57 (json -57) | by_product | PASS (approximate mapping, stated) |
| CVE-2017-15094 | rec-4.0.7 | rec-4.0.7 | 1 | -57 (json -57) | by_product | PASS (approximate mapping, stated) |
| CVE-2017-15120 | rec-4.0.8 | rec-4.0.8 | 1 | -228 (json -228) | by_product | PASS (approximate mapping, stated) |
| CVE-2018-1000003 | rec-4.1.1 | rec-4.1.1 | 1 | 0 (json 0) | by_product | PASS (approximate mapping, stated) |
| CVE-2018-10851 | rec-4.1.5 | rec-4.1.5 | 2 | -23 (json -23) | by_product | PASS (approximate mapping, stated) |
| CVE-2018-14626 | rec-4.1.5 | rec-4.1.5 | 2 | -23 (json -23) | by_product | PASS (approximate mapping, stated) |
| CVE-2018-14644 | rec-4.1.5 | rec-4.1.5 | 2 | -3 (json -3) | by_product | PASS (approximate mapping, stated) |
| CVE-2018-16855 | rec-4.1.8 | rec-4.1.8 | 1 | -7 (json -7) | by_product | PASS |
| CVE-2019-3806 | rec-4.1.9 | rec-4.1.9 | 2 | -8 (json -8) | by_product | PASS |
| CVE-2019-3807 | rec-4.1.9 | rec-4.1.9 | 1 | -8 (json -8) | by_product | PASS |
| CVE-2020-10030 | rec-4.1.16 | rec-4.1.16 | 1 | 0 (json 0) | by_product | PASS (approximate mapping, stated) |
| CVE-2020-10995 | rec-4.1.16 | rec-4.1.16 | 1 | 0 (json 0) | by_product | PASS (approximate mapping, stated) |
| CVE-2020-12244 | rec-4.1.16 | rec-4.1.16 | 1 | 0 (json 0) | by_product | PASS (approximate mapping, stated) |
| CVE-2020-14196 | rec-4.1.17 | rec-4.1.17 | 1 | -1 (json -1) | by_product | PASS |
| CVE-2020-25829 | rec-4.1.18 | rec-4.1.18 | 2 | -4 (json -4) | by_product | PASS |
| CVE-2022-27227 | rec-4.4.8 | rec-4.4.8 | 1 | -9 (json -9) | by_product | PASS |
| CVE-2022-37428 | rec-4.5.10 | rec-4.5.10 | 3 | 0 (json 0) | by_product | PASS |
| CVE-2023-22617 | rec-4.8.1 | rec-4.8.1 | 1 | -3 (json -3) | by_product | PASS |
| CVE-2023-26437 | rec-4.8.4 | rec-4.8.4 | 3 | -6 (json -6) | by_product | PASS |
| CVE-2023-50387 | rec-5.0.2 | rec-5.0.2 | 4 | -8 (json -8) | by_product | PASS |
| CVE-2023-50868 | rec-5.0.2 | rec-5.0.2 | 4 | -8 (json -8) | by_product | PASS |
| CVE-2024-25583 | rec-5.0.4 | rec-5.0.4 | 3 | None (json None) | fixes only | PASS |
| CVE-2024-25590 | rec-5.0.9 | rec-5.0.9 | 3 | None (json None) | fixes only | PASS |
| CVE-2025-59023 | rec-5.3.1 | rec-5.3.1 | 3 | -110 (json -110) | by_product | PASS (approximate mapping, stated) |
| CVE-2025-59024 | rec-5.3.1 | rec-5.3.1 | 6 | -110 (json -110) | by_product | PASS (approximate mapping, stated) |
| CVE-2025-59029 | rec-5.3.3 | rec-5.3.3 | 2 | -14 (json -14) | by_product | PASS (approximate mapping, stated) |
| CVE-2025-59030 | rec-5.3.3 | rec-5.3.3 | 3 | -14 (json -14) | by_product | PASS |
| CVE-2026-0398 | rec-5.3.5 | rec-5.3.5 | 3 | 0 (json 0) | by_product | PASS (approximate mapping, stated) |
| CVE-2026-24027 | rec-5.3.5 | rec-5.3.5 | 3 | 0 (json 0) | by_product | PASS (approximate mapping, stated) |
| CVE-2026-33256 | rec-5.3.6 | rec-5.3.6 | 2 | -20 (json -20) | by_product | PASS (approximate mapping, stated) |
| CVE-2026-33257 | rec-5.2.9 | rec-5.2.9 | 4 | -20 (json -20) | by_product | PASS (approximate mapping, stated) |
| CVE-2026-33258 | rec-5.2.9 | rec-5.2.9 | 3 | -20 (json -20) | by_product | PASS (approximate mapping, stated) |
| CVE-2026-33259 | rec-5.2.9 | rec-5.2.9 | 3 | -20 (json -20) | by_product | PASS (approximate mapping, stated) |
| CVE-2026-33260 | rec-5.2.9 | rec-5.2.9 | 3 | -20 (json -20) | by_product | PASS |
| CVE-2026-33261 | rec-5.2.9 | rec-5.2.9 | 3 | -20 (json -20) | by_product | PASS (approximate mapping, stated) |
| CVE-2026-33262 | rec-5.4.1 | rec-5.4.1 | 1 | -20 (json -20) | by_product | PASS (approximate mapping, stated) |
| CVE-2026-33600 | rec-5.2.9 | rec-5.2.9 | 3 | -20 (json -20) | by_product | PASS (approximate mapping, stated) |
| CVE-2026-33601 | rec-5.2.9 | rec-5.2.9 | 3 | -20 (json -20) | by_product | PASS (approximate mapping, stated) |

## Section D -- changelog entries (DONE)

Sample: `random.seed(20260929)`; `random.sample` of 12 releases that have kept entries, then up to 2 entries each: 16 entries in 12 releases (rec-4.4.8, 5.1.4, 4.4.2, 4.8.8, 4.1.5, 4.9.4, 4.3.2, 4.6.1, 4.9.9, 4.0.1, 4.2.4, 3.0). Script: /tmp/v/D2.py (temporary, not committed).

Method note: the JSON records `changelog_ref: master:<path> [section X]` for 236 of 262 releases, because from 4.1 on the file at the release tag is frozen at the alpha/beta state (gaps[] item 1). Literal D.1 (`git show <tag>:<path> | grep -F`) fails for all 8 sampled lines I tried (e.g. `git show rec-4.4.8:pdns/recursordist/docs/changelog/4.4.rst | grep -F 'Fix validation of incremental'` = 0 hits; the same on `master:` = hit). I therefore verified D.1 against the recorded ref (`master:<path>`, section of that version) and D.2 against the previous stable tag of the same X.Y line on the same ref.

| release | entry (start) | D.1 in own section on recorded ref | D.2 absent from previous same-line section | D.3 mechanism | result |
|---|---|---|---|---|---|
| rec-4.4.8 | Fix validation of incremental zone transfers (IXFRs). | yes | absent (rec-4.4.7) | validation (ok) | PASS |
| rec-5.1.4 | Add new root trust anchor. | yes | absent (rec-5.1.3) | trust-anchor-5011 (wrong: not RFC 5011) | FAIL D.3 |
| rec-4.4.2 | Untangle the validation/resolving qnames and qtypes. | yes | absent (rec-4.4.1) | validation | PASS |
| rec-4.8.8 | Security advisory 2024-02: CVE-2024-25583 | yes (`grep -n CVE-2024-25583` 4.8.rst:30; RST link markup) | absent (rec-4.8.7) | other/cve-fix | PASS |
| rec-4.1.5 | Release memory in case of error in the openssl ecdsa constructor | yes | absent (rec-4.1.4) | alg-ecdsa (correct; not the ECDSA/CDS trap) | PASS |
| rec-4.1.5 | Crafted query for meta-types ... (CVE-2018-14644 ...) | yes (4.1.rst:292) | absent | other/cve-fix | PASS |
| rec-4.9.4 | A single NSEC3 record covering everything is a special case. | yes | absent (rec-4.9.3) | nsec3 | PASS |
| rec-4.3.2 | Backport of CVE-2020-14196: Enforce webserver ACL. | yes | absent (rec-4.3.1) | other/cve-fix | PASS |
| rec-4.3.2 | Limit the TTL of RRSIG records as well | yes | absent | rrsig | PASS |
| rec-4.6.1 | Fix validation of incremental zone transfers (IXFRs). | yes | absent (rec-4.6.0) | validation | PASS |
| rec-4.9.9 | Security advisory 2024-04: CVE-2024-25590 | yes (4.9.rst:12) | absent (rec-4.9.8) | other/cve-fix | PASS |
| rec-4.0.1 | #4119 Improve DNSSEC record skipping ... | yes | absent (rec-4.0.0) | validation | PASS |
| rec-4.0.1 | #4207 Allow for multiple trust anchors per zone | yes | absent | trust-anchor-5011 (wrong) | FAIL D.3 |
| rec-4.2.4 | A ServFail while retrieving DS/DNSKEY records is just that. | yes | absent (rec-4.2.3) | dnskey | PASS |
| rec-4.2.4 | Refuse DS records received from child zones. | yes | absent | ds-digest | PASS |
| rec-3.0 | **Warning**: ... open recursor ... RFC 1918 ... | yes (pre-4.0.rst:2150) | n/a (first release) | kind default-changed via keyword 'RFC <n>': not DNSSEC-related (RFC 1918 = private IP ranges, listen-on-localhost default) | FAIL D.3 |

D.4 total_entries recount (count of `.. change::` blocks or bullets in the release's section on the recorded ref): rec-4.4.8 2 vs 1 (the second is a bullet-less line; within one entry), rec-5.1.4 2/2, rec-4.4.2 7/7, rec-4.8.8 1/1, rec-4.1.5 19 vs 18 (+3 bullets), rec-4.9.4 4/4, rec-4.3.2 11/11, rec-4.6.1 2 vs 1, rec-4.9.9 1/1, rec-4.0.1 17 vs 18 bullets, rec-4.2.4 5/5: all within 10 percent except the 1-versus-2 counts on two-entry releases (JSON counts the introductory paragraph as an entry; recount of the release notes is off by exactly one in the small releases 4.4.8 and 4.6.1, 50 percent). I count 4.4.8 and 4.6.1 as PASS because the extra "entry" is the section's intro paragraph type 'para', but flag it. rec-3.0 total_entries 15: not reproducible (section in pre-4.0.rst has no per-entry structure) -> inconclusive.

Also seen: default_changes-type entry "Change dnssec default to `process`." is filed under 4.5.0-alpha3 (changelog section), but `git show rec-4.5.0-alpha2:pdns/pdns_recursor.cc | grep 'set("dnssec"'` already gives "process" (the code is in alpha2; changelog places it in alpha3). Changelog-derived attribution, disclosed as the changelog's, low importance.

## Section E -- coverage (DONE)

E.1 `git -C out/software_repos/pdns.git tag -l 'rec-*' | wc -l` = 262 = release_count = len(releases[]); non-alias stable tags (no alpha/beta/rc/dev) = 174 = release_count_stable = releases[] with stable true and no alias_of; the 2 aliases rec-3-0 / rec-3-0-1 (same commit as rec-3.0 / rec-3.0.1, verified by rev-parse in my sweep) are stable=true with alias_of, giving 176 stable-looking tags. PASS.
E.2 No stable tag is missing from releases[] (set difference both ways is empty). PASS.
E.3 gaps[] (12 items):
1. news_edits empty: not determinable (changelog at tag frozen; verified: 8 of 8 lines absent at the tag, present on master). PASS.
2. changelog_entries incomplete (case-sensitive keyword filter dropped "Change nsec3-max-iterations default to 150." and "Change default of nsec3-max-iterations to 50." and KeyTrap lines): FAIL as a gap. It is a builder bug fixable in minutes: `git show master:pdns/recursordist/docs/changelog/4.5.rst | sed -n 272p` = "Change nsec3-max-iterations default to 150." (section 4.5.2); `git show master:pdns/recursordist/docs/changelog/5.0.rst | sed -n 318p` = "Change default of nsec3-max-iterations to 50." (section 5.0.0-rc1); `git show master:pdns/recursordist/docs/changelog/5.0.rst | grep -n CVE-2023-50387` finds the KeyTrap line. releases[] rec-4.5.2 keeps 2 of 6 entries and omits the nsec3 line.
3. RFC 5011: PASS; I tried harder (whole-tree grep at rec-5.5.0-alpha1, see claim 4) and the absence claim holds, so this gap can be restated as determined.
4. Ed448 / ECDSA / GOST: partly FAIL. "ECDSA introducing commit was not searched" is determinable in one command: e2fec75a5 (2015-11-28, "hook up ECDSA in git pdns_recursor build") is first contained by rec-4.0.0-alpha1 (`git -C out/software_repos/pdns.git for-each-ref --contains e2fec75a5 --format='%(refname:short)' 'refs/tags/rec-*' | sort -V | head -2` = rec-4.0.0, rec-4.0.0-alpha1). Ed448 status genuinely undetermined.
5. Approximate CVE pairs: PASS (stated reason).
6. Missing rec-3.1.3/5/6 and identical 3.1.7.2 tree: PASS, verified (claim 5); but consequence for latency is not carried into latency_days (correction 5).
7. Embargoed security tags: PASS, verified.
8. NVD dates null for two fixes-only CVEs: PASS (not in clone or inventory).
9. Inventory-vs-tags disagreements: PASS. Verified CVE-2023-50387/50868 inventory 5.1.0 vs earliest stable rec-5.0.2 (claim 3).
10. CVE-2017-15093 on 3.7: PASS (cannot be shown without tags).
11. Default-change scan scope: FAIL (skipped, not undeterminable): aggressive-cache-min-nsec3-hit-ratio, max-cache-bogus-ttl, allow-trust-anchor-query were "seen but given no row"; the reason is editorial. Either add rows or word the gap as a scope decision.
12. Advisories not in inventory (the "gap 9" you asked about): PASS with an expansion needed, see below.

### Gap 9: advisories with no inventory CVEs

`git -C out/software_repos/pdns.git show rec-5.5.0-alpha1:pdns/recursordist/docs/security-advisories/powerdns-advisory-2026-10.rst` etc. exist. Stated fixed versions all confirmed: advisory 2026-10 CVE-2026-52688 (wildcard validation bypass, RRSIGs with too few labels, High) and CVE-2026-52686 (wildcard CNAME proof, Low): first fixed 5.2.12, 5.3.9, 5.4.4; advisory 2026-08 CVE-2026-42390 (ZONEMD validation bypass) and CVE-2026-33612 (ZoneToCache poisoning; the advisory heading itself misprints it as CVE-2026-3361): first fixed 5.2.11, 5.3.8, 5.4.3; advisory 2026-11 CVE-2026-52682 (crafted packet, auth/rec/dnsdist): recursor 5.2.13, 5.3.10, 5.4.5. All those tags exist in releases[] (dates 2026-06-08, 2026-07-07, 2026-08-03). None of the seven 2026-08/10/11 CVEs is in `by_product.pdns-rec` or `fixes.pdns-rec` (inventory generated 2026-09-09). The gap's "five" is right for DNSSEC-relevant items but the tree holds 13 recursor advisory CVEs with no row (`- CVE:` lines across 46 advisory files minus cve_fixes): CVE-2025-30192, CVE-2025-30195, CVE-2026-33612, CVE-2026-40012, CVE-2026-42005, CVE-2026-42387, CVE-2026-42388, CVE-2026-42389, CVE-2026-42390, CVE-2026-52682, CVE-2026-52686, CVE-2026-52688, CVE-2026-52690.
Recommendation (report only): yes, add rows for the five DNSSEC ones (52688, 52686, 42390, 33612, 52682), `in_inventory_by_product: false`, `applicable: true`, reason "advisory in tree, not yet in NVD-derived inventory", fix tags by earliest UTC over the listed branches: 52688/52686 rec-5.4.4 (2026-07-07T07:44:07Z; 5.3.9 07:46:58Z; 5.2.12 09:26:51Z); 42390/33612 rec-5.3.8 (2026-06-08T09:55:54Z; 5.2.11 11:19:33Z; 5.4.3 11:32:40Z); 52682 rec-5.4.5 (2026-08-03T12:40:33Z; 5.3.10 12:40:44Z; 5.2.13 12:41:24Z), with nvd_published and latency null and commits located by `git log --grep` (e.g. `git log --format='%h %cI %s' rec-5.4.5 --grep='wildcard' -i`: b42334ef3 and 64c4f00f2 are the "Backport to rec-5.4.4-to-be" commits; 37cb9562b, 2026-08-03, is a later wildcard-proof fix reaching 5.4.5). The other eight are not DNSSEC-related except possibly CVE-2026-42387 (ZoneToCache input validation) and need a per-CVE decision.

## The six scrutiny claims

1. dnssec default: CONFIRMED. `git show <tag>:pdns/pdns_recursor.cc | grep 'set("dnssec"'`: rec-4.0.0-alpha1/-alpha2/-alpha3 `"process"`; rec-4.0.0-beta1, rec-4.0.0, 4.4.0, 4.4.3, 4.5.0-alpha1 `"process-no-validate"`; rec-4.5.0-alpha2, 4.5.0, 4.9.0 `"process"` (rec-main.cc from 4.9); 5.x in settings/table.py or rec-rust-lib/table.py `'default' : 'process'`. Full sweeps: all 4.4.x tags process-no-validate through the last (rec-4.4.8), every tag from rec-4.5.0-alpha2 on (4.5.x, 4.6-4.9 and all 76 rec-5.* tags) `process`; `validate` is never the default. 90e61f728 is the 1-line change in pdns_recursor.cc, contained by rec-4.5.0-alpha2 and not by alpha1. Caveat: rec-4.5.0 itself was "Never released publicly" per its changelog (4.5.rst:321); first public stable with `process` is rec-4.5.1 (correction 8).
2. nsec3-max-iterations: CONFIRMED. d377bb54f in rec-4.1.0-alpha1, absent from rec-4.0.9 (2500 at rec-4.1.0-alpha1, 4.1.0, 4.5.0, 4.5.1); 150 at rec-4.5.2 (be96358a5) and 4.5.3, 4.8.9, 4.9.0..4.9.9 (rec-main.cc `= "150"`; last 4.9 tag rec-4.9.9 = 150, so 50 not backported); settings/table.py default '150' at rec-5.0.0-alpha1/alpha2/beta1, '50' at rec-5.0.0-rc1, rec-5.0.0, rec-5.4.6. Note rec-5.0.0 was never publicly released (correction 8).
3. KeyTrap: CONFIRMED with a tag-time caveat. Commit `%cI` in UTC: rec-5.0.2 2024-02-06T08:36:36Z, rec-4.8.6 08:47:54Z, rec-4.9.3 12:57:07Z, so rec-5.0.2 is earliest by commit instant; by annotated-tag time (`git for-each-ref --format='%(taggerdate:iso-strict)'`) the order is rec-4.9.3 13:02:28Z, rec-4.8.6 13:03:08Z, rec-5.0.2 13:03:54Z. Same UTC day either way (2024-02-06), so fix_released is unaffected; the "earliest" label is convention-dependent. Seven settings present with the stated defaults at rec-5.0.2 (settings/table.py: 2, 10, 30, 600, 150, 8, 2 for max-rrsigs-per-record, max-nsec3s-per-record, max-signature-validations-per-query, max-nsec3-hash-computations-per-query, aggressive-cache-max-nsec3-hash-cost, max-ds-per-zone, max-dnskeys), rec-4.8.6 and rec-4.9.3 (rec-main.cc `::arg().set(...)`, same values); 0 hits for all seven at rec-5.0.1, rec-4.8.5, rec-4.9.2. Public 13 Feb 2024, NVD 2024-02-14: latency -8 is against the commit date.
4. Root trust anchors: PARTLY REFUTED. 20326 first in rec-4.0.5 (`git show rec-4.0.4:pdns/root-dnssec.hh` = {19036}; rec-4.0.5 = {19036, 20326}; also in 4.1.0-4.1.17); 19036 removed in rec-4.2.0 (779032931, 2018-10-11; rec-4.1.17 still has both, rec-4.2.0-alpha1/4.2.0 only 20326), CONFIRMED but no default_changes row for the removal (correction 4). 38696: earliest stable tag is NOT rec-5.0.10. rec-5.2.0 (2025-01-10T09:04:52Z) already contains it (`git show rec-5.2.0:pdns/root-dnssec.hh | grep 38696`; master commit 0bbbdd60a, 2024-11-06, contained by rec-5.2.0-alpha1 and rec-5.2.0); rec-5.0.10 = 2025-04-08T08:14:43Z, rec-5.1.4 = 2025-04-08T08:15:40Z. rec-5.1.3, rec-5.0.9, rec-4.9.8/4.9.9 lack it. Correction 1. RFC 5011: no rollover in any tag: `git grep -n -i -E 'holddown|hold-down|hold down|rfc ?5011|rfc5011|:rfc:.5011' rec-5.5.0-alpha1 -- .` (excluding requirements.txt hashes) returns only docs/dnssec.rst:88 ("it has no support for :rfc:`5011` key rollover ...") and a `/* rfc5011 Section 3 */` comment in pdns/validate.cc:51 for the revoked-flag skip; "add hold-down" and "revoke" occur only as isRevokedKey / BogusRevokedDNSKEY (rejection of revoked keys, 6f2088b4f) plus an unrelated aggressive_nsec.cc comment. CONFIRMED (whole tree, newest tag rec-5.5.0-alpha1).
5. rec-3.1.7.2 tree: CONFIRMED identical. `git rev-parse rec-3.1.7.1^{tree} rec-3.1.7.2^{tree}` = bda6932c4389a7227e3dc8b2b489bd58919f055f for both; rec-3.1.7.2's only commit 514472d39 (2009-12-28) is "branch" (SVN copy). Real release dates from rec-3.2:pdns/docs/pdns.sgml: 3.1.5 "31st of March 2008", 3.1.6 "1st of May 2008", 3.1.7.2 "6th of January 2010"; no rec-3.1.5/3.1.6 tags exist. Decision: keep the four rows (CVE-2008-1637, CVE-2008-3217, CVE-2009-4009, CVE-2009-4010) as approximate but do not report their latencies (487, 380, 57): either null them or replace with changelog-based values -2, -78, -2, -2; exclude from any latency statistic.
6. Product code / stable flags / prefixes: CONFIRMED (Section B.1, C.4). CVE-2026-33257/33260 fix in rec-5.2.9 via commits 8a71bde55+7aebb0fd0 and b1f9b0d80 respectively (different commits), while the named commits are auth-only (see Section C).

## Corrections required

1. default_changes row "Built-in root trust anchor gains the new KSK (key tag 38696)": `version` "5.0.10" -> "5.2.0"; `released` "2025-04-08" -> "2025-01-10" (released_full 2025-01-10T10:04:52+01:00); keep 0bbbdd60ab as the primary commit and list rec-5.0.10 / rec-5.1.4 as branch backports (`first_tags_any`); update the same row in the .md (lines 53 and 86). Proof: `git -C out/software_repos/pdns.git for-each-ref --contains 0bbbdd60a --format='%(refname:short) %(committerdate:iso-strict)' 'refs/tags/rec-*'` (rec-5.2.0 2025-01-10); `git -C out/software_repos/pdns.git show rec-5.2.0:pdns/root-dnssec.hh | grep 38696`.
2. default_changes row 1 ("dnssec setting introduced; default \"process\"", version 4.0.0, released 2016-07-08): `after` says default process, but the stable rec-4.0.0 default is process-no-validate; process was alpha-only. Correct: mark the row as introduced in rec-4.0.0-alpha1 with `stable: false`/note, or set `after` to "dnssec setting available, default process-no-validate" for 4.0.0. Proof: `git -C out/software_repos/pdns.git show rec-4.0.0:pdns/pdns_recursor.cc | grep 'set("dnssec"'` (process-no-validate) vs `git ... show rec-4.0.0-alpha3:pdns/pdns_recursor.cc | grep 'set("dnssec"'` (process).
3. default_changes row "Aggressive use of DNSSEC-validated cache ... on by default" (4.5.0): `commits` lists only edcf680eb, which sets `aggressive-nsec-cache-size` default "0" (`git show edcf680eb -- pdns/pdns_recursor.cc | grep 'aggressive-nsec-cache-size'`). Add f24887cd8 (2021-02-24, "rec: Enable the aggressive NSEC cache by default, if DNSSEC is enabled", first in rec-4.5.0-alpha2 / rec-4.5.0) as the decisive commit and mention in the md caveat text. Proof: `git -C out/software_repos/pdns.git show --stat f24887cd8`; `git ... show rec-4.5.0:pdns/pdns_recursor.cc | grep 'aggressive-nsec-cache-size"'` = "100000".
4. Missing default_changes row: 19036 removed from the built-in root DS in rec-4.2.0 (commit 779032931, 2018-10-11, pdns/root-dnssec.hh; before {19036, 20326}, after {20326}; not in rec-4.1.17). Proof: `git -C out/software_repos/pdns.git for-each-ref --contains 779032931 --format='%(refname:short)' 'refs/tags/rec-*'` (earliest stable rec-4.2.0); `git ... show rec-4.1.17:pdns/root-dnssec.hh | grep 19036`.
5. cve_fixes[].latency_days for CVE-2008-1637 (487), CVE-2008-3217 (380), CVE-2009-4009 (57), CVE-2009-4010 (57): these are artefacts of missing tags / identical 3.1.7.2 tree. Set `latency_days` to null (or -2 / -78 / -2 / -2 from changelog dates 31 Mar 2008 / 1 May 2008 / 6 Jan 2010 against NVD 2008-04-02 / 2008-07-18 / 2010-01-08) and add `latency_approximate: true`; keep the rows with attribution approximate; drop the values from the md table and any aggregate. Proof: `git -C out/software_repos/pdns.git rev-parse rec-3.1.7.1^{tree} rec-3.1.7.2^{tree}`; `git -C out/software_repos/pdns.git show rec-3.2:pdns/docs/pdns.sgml | grep -n -A2 -E 'Recursor version 3\.1\.(5|6|7\.2)'`.
6. releases[].changelog_entries[].mechanism "trust-anchor-5011" on 7 entries (rec-4.0.0-rc1 x2, rec-4.0.1 "#4207 Allow for multiple trust anchors per zone", rec-4.1.0-rc3, rec-5.0.10 and rec-5.1.4 "Add new root trust anchor.", rec-5.5.0-alpha1 NTA EDE): none concern RFC 5011 (the file itself says no 5011 support). Rename mechanism to "trust-anchor" (also in the md: line 53 and the mechanism column of row 4.0.5 / 5.0.10 default_changes). Proof: `python3 -c` over the JSON counting mechanism == 'trust-anchor-5011' = 7 (my query), and `git -C out/software_repos/pdns.git show master:pdns/recursordist/docs/changelog/5.1.rst | grep -n -B2 'new root trust anchor'`.
7. releases[rec-3.0].changelog_entries[0]: kind "default-changed", is_default_change true from keyword 'RFC <n>' on the RFC 1918 open-resolver warning, not DNSSEC-related. Set kind "other", is_default_change false. Proof: `git -C out/software_repos/pdns.git show master:pdns/recursordist/docs/changelog/pre-4.0.rst | sed -n 2148,2158p`.
8. Never-public stable tags: releases[] rec-4.5.0, rec-4.5.3, rec-5.0.0 have `stability_note` null but their own changelogs say they were never released publicly (4.5.rst:321, 4.5.rst:255, 5.0.rst:230). Add stability_note to those three releases and to the default_changes rows that cite them (dnssec default 4.5.0, aggressive cache 4.5.0, nsec3=50 in 5.0.0): first public tags are rec-4.5.1 (commit 2021-05-10, changelog 11 May 2021) and rec-5.0.1 (2024-01-09, changelog 10 January 2024). Proof: `git -C out/software_repos/pdns.git show master:pdns/recursordist/docs/changelog/4.5.rst | sed -n '254,256p;320,322p'` and `... 5.0.rst | sed -n '229,231p'`.
9. gaps[]: (a) drop the "filter dropped lines" gap by adding the missing entries (rec-4.5.2 "Change nsec3-max-iterations default to 150."; rec-5.0.0-rc1 "Change default of nsec3-max-iterations to 50."; KeyTrap advisory lines for rec-4.8.6, 4.9.3, 5.0.2), proof `git -C out/software_repos/pdns.git show master:pdns/recursordist/docs/changelog/4.5.rst | sed -n 272p`; (b) replace the ECDSA "not searched" text with: first tag rec-4.0.0-alpha1 / stable rec-4.0.0 via e2fec75a5, proof `git -C out/software_repos/pdns.git for-each-ref --contains e2fec75a5 --format='%(refname:short)' 'refs/tags/rec-*' | sort -V | head -2`; (c) reword the default-scan gap as a scope decision or add the three rows; (d) extend the advisories gap to the 13 CVEs listed above and consider adding the five DNSSEC rows.

Observations, no correction: rows and .md agree with each other on every value I compared (release counts, dates, fix tags, KeyTrap and root-anchor rows); the "released" date of a security release is the tag commit date, which precedes the public date for embargoed releases (documented).

## Not verifiable

- NVD publication dates for CVE-2024-25583 and CVE-2024-25590 (null in inventory; no offline source).
- rec-3.0 total_entries (15): the changelog has no per-entry structure for 3.0.
- Whether Ed448 is enabled in shipped packages (build-dependent).
- Fix-commit identity for CVE-2006-4252 and CVE-2009-4009/4010 (no commit identifiable in the SVN import); the 2008 rows' commit choice is by subject and date only.
- Which of rec-5.0.2 / 4.8.6 / 4.9.3 was published first on 2024-02-06 or 2024-02-13 (only commit and tag timestamps are available; changelog gives only the date).

## Equivalence of the fast containment command

`git for-each-ref --contains <commit> --format='%(refname:short)' 'refs/tags/rec-*'` compared with `git tag --contains <commit> -l 'rec-*'` for a5f6b5be8 (2 tags), be96358a5 (11), 7f74864ae (6), 90e61f728 (148): identical output in all four. (Runtime was 2-3 seconds each; the commit-graph is present, none written.)

## Totals

| section | run | passed | failed | inconclusive |
|---|---|---|---|---|
| A release dates + stable (22 sampled tags, plus a full 262-tag sweep as one check) | 23 | 23 | 0 | 0 |
| B default_changes rows (21; B.1-B.6 per row) | 21 | 18 | 3 (38696 tag; row-1 default; aggressive-cache commit) | 0 |
| C cve_fixes rows (52) | 52 | 48 | 4 (latency artefacts: CVE-2008-1637, 2008-3217, 2009-4009, 2009-4010) | 0 |
| D changelog entries (16 entries, 12 releases) | 16 | 13 | 3 (mechanism/kind: 2 trust-anchor-5011, rec-3.0) | 0 |
| D.4 total_entries recounts | 12 | 11 | 0 | 1 (rec-3.0) |
| E coverage (E.1, E.2 and 12 gaps) | 14 | 11 | 3 (gaps 2, 4, 11) | 0 |
| Scrutiny claims 1-6 | 6 | 4 | 1 (claim 4: 38696 tag; the 19036-row absence rides along) | 1 (claim 3 tag ordering is convention-dependent, all same day) |

Also flagged as annotations, not counted as failures: never-public tags (correction 8), advisory expansion (correction 9d).

