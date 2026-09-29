# Phase 3 verification: unbound

**Verdict: PASS WITH CORRECTIONS.** All four load-bearing claims reproduce from the clone (five bare re-tags, 1.3.4 mis-import, three branch point-release fix tags, six SVN-era default commits touch `util/config_file.c` / `configure.ac`); the corrections are one CVE latency (CVE-2017-15105 should be dated to vendor release 1.6.8, 2018-01-19, not 1.7.0rc1), nine CVE rows whose `fix_commits[]` list commits their `fix_tag` does not contain, eight CVE rows with no per-row inventory reason, two default-change rows citing the wrong header file, two gaps that are determinable, and one un-noted mis-imported pair (release-1.8.2 / release-1.8.3).

Clone: `out/software_repos/unbound.git` (bare, blob-less). `C=out/software_repos/unbound.git` in every command below. Commands were run under `bash` (zsh does not word-split).

## The four hard claims

| # | claim | command | observed | result |
|---|---|---|---|---|
| 1 | release-1.4.13p1, -1.4.13p2, -1.6.3, -1.6.5, -1.6.8 are bare re-tags | `for p in "release-1.4.13 release-1.4.13p1" "release-1.4.13 release-1.4.13p2" "release-1.6.2 release-1.6.3" "release-1.6.4 release-1.6.5" "release-1.6.7 release-1.6.8"; do set -- $p; git -C $C diff --stat $1 $2; git -C $C rev-parse $1^{tree} $2^{tree}; done` | all five diffs empty; tree hashes equal pairwise (23db2af4…, 23db2af4…, b9d06dcf…, 2a0d195d…, 68ce6ea4…). Full scan of all 120 stable tags in date order (`rev-parse <tag>^{tree}` on consecutive pairs) finds exactly these five identical-tree pairs and no others. | PASS |
| 2 | release-1.3.4 lacks 1a02ab89; first tag with it is release-1.4.0rc1 | `git -C $C tag --contains 1a02ab89 \| sort -V \| head -5` → `1.11.0rc1 final-svn-state release-1.4.0 release-1.4.0rc1 release-1.4.1`; `git -C $C tag --contains 1a02ab89 \| grep -xc release-1.3.4` → 0; `git -C $C diff --stat release-1.3.3 release-1.3.4` → `doc/Changelog, testcode/unitverify.c, testdata/test_signatures.10, testdata/test_signatures.14, util/iana_ports.inc` (5 files, no validator code) | release-1.3.4 commit is 2f85c581 "1.3.3 release." (2009-08-04); 1a02ab89 adds `list_is_secure()` to `validator/val_nsec3.c` (23 insertions) and is contained by release-1.4.0rc1 and later only. Changelog at release-1.4.0 (7 October 2009): "moved version number to 1.4.0 because of 1.3.4 release with only the NSEC3 patch". | PASS |
| 3a | CVE-2024-1931 → release-1.19.2 (inventory 1.19.3) | `git -C $C tag --contains 5b37cd6e4cf1` → `release-1.19.2` only; `git -C $C log --all --grep=CVE-2024-1931` → 5b37cd6e (branch, 2024-03-07) and 326ba265 (master "Version set to 1.19.3…", 2024-03-07); `git -C $C log -1 --format=%cI release-1.19.2^{commit}` → 2024-03-07 | earliest stable tag containing the fix is release-1.19.2 (2024-03-07); release-1.19.3 is 2024-03-11. Builder is right, inventory is wrong. | PASS |
| 3b | CVE-2024-8508 → release-1.21.1 (inventory 1.22.0) | `git -C $C tag --contains b7c61d7cc256 \| sort -V` → `release-1.21.1 release-1.22.0 release-1.22.0rc1 …`; `git -C $C tag --contains a1b25f029641 \| sort -V \| head -1` → `release-1.22.0` | branch fix b7c61d7c is in release-1.21.1 (2024-10-03); master commit a1b25f02 (the one the inventory cites, "The fix for CVE-2024-8508 was part of 1.21.1…") is first in release-1.22.0 (2024-10-16). Builder is right. | PASS |
| 3c | CVE-2019-16866 → release-1.9.4 (inventory 1.9.6) | `git -C $C tag --contains b60c4a472c85 \| grep -E '^release-' \| sort -V \| head -1` → `release-1.9.4`; `git -C $C log release-1.9.3..release-1.9.4` → single commit b60c4a47; `git -C $C diff release-1.9.3 release-1.9.4 -- util/data/msgparse.c` → moves `memset(edns, 0, sizeof(*edns))` before the early returns in `parse_edns_from_pkt` (the uninitialised-EDNS fix); inventory's facc6c65 ("Merge 1.9.4 release with fix for CVE-2019-16866") is first in release-1.9.6rc1 | release-1.9.4 (2019-10-03) is the earliest stable tag with the fix code. Builder is right. | PASS |
| 4 | SVN-era default commits touch product config | `git -C $C show --stat <sha>` for 134db23e, 9a08ad41, 93ffd446, d71a1ba0, 53a448ff, e65fdc31, 11b3ebc3 | 134db23e: `util/config_file.c` (+`doc/Changelog`, `doc/unbound.conf.5`); 9a08ad41: `configure.ac`, `configure`; 93ffd446: `configure.ac`, `configure`; d71a1ba0/53a448ff: `configure.ac`, `configure`; e65fdc31: `util/config_file.c`; 11b3ebc3: `util/config_file.c` (+ man page, testdata). Before/after hunks quoted in section B. None is test-only. | PASS |

**Stray tag `release-1.6.5@4299`:** `git -C $C for-each-ref 'refs/tags/release-1.6.5*' --format='%(refname) %(objectname) %(subject)'` → it is an annotated tag ("release 1.6.4 tag", tagger 2017-08-21) whose commit is `ac98f480` = the same commit as `release-1.6.4` ("tag 1.6.4rc2", 2017-06-22). It is an SVN-import artefact (`@4299` is the SVN revision). It **is** counted in `release_count` (214 = every `release-*` ref, including 94 rc/p/stray tags) and is present in `releases[]` with `stable: false` and `stability_note: "stray SVN-import tag; same commit as release-1.6.4; not a release"`; it is **not** among the 120 stable releases. So it is excluded from the stable count, not from `release_count`. The `.md` header says the same ("214 tags (120 stable incl. 1.4.13p1/p2, 94 rc/stray)"). Consistent; no correction.

## A. Release dates (20 random + first + last)

Sample: Python `random.seed(20260929); random.sample(range(214), 20)` over `releases[]` in file order → indices [2, 17, 37, 60, 74, 79, 93, 97, 111, 118, 123, 128, 129, 132, 149, 151, 153, 170, 188, 209], plus `releases[0]` and `releases[-1]`. Command for every row: `git -C $C log -1 --format=%cI <tag>^{commit}`; stable rule: `release-X.Y[.Z]` (and `p1/p2`) stable, `rcN`/`@` not.

| tag | json released_full / stable | git %cI / pattern | result |
|---|---|---|---|
| release-0.2 | 2007-04-03T14:17:42Z / true | 2007-04-03T14:17:42Z / stable | PASS |
| release-1.1.0 | 2008-11-14T06:28:14Z / true | same / stable | PASS |
| release-1.4.6 | 2010-07-22T11:50:28Z / true | same / stable | PASS |
| release-1.4.16 | 2012-02-02T09:05:06Z / true | same / stable | PASS |
| release-1.5.0rc1 | 2014-11-11T14:18:32Z / false | same / rc | PASS |
| release-1.5.2rc1 | 2015-02-11T14:57:19Z / false | same / rc | PASS |
| release-1.5.9rc1 | 2016-06-02T12:13:30Z / false | same / rc | PASS |
| release-1.6.0rc1 | 2016-12-08T08:49:12Z / false | same / rc | PASS |
| release-1.6.6rc1 | 2017-09-01T14:55:52Z / false | same / rc | PASS |
| release-1.7.0rc2 | 2018-03-08T13:37:34Z / false | same / rc | PASS |
| release-1.7.2rc1 | 2018-06-04T10:40:47Z / false | same / rc | PASS |
| release-1.8.0rc1 | 2018-09-04T07:15:06Z / false | same / rc | PASS |
| release-1.8.0 | 2018-09-04T07:15:30Z / true | same / stable | PASS |
| release-1.8.2rc1 | 2018-11-29T08:27:47Z / false | same / rc | PASS |
| release-1.9.6 | 2019-12-06T11:31:34+01:00 / true | same / stable | PASS |
| release-1.10.0rc2 | 2020-02-17T13:38:01+01:00 / false | same / rc | PASS |
| release-1.10.1 | 2020-05-19T08:17:45+02:00 / true | same / stable | PASS |
| release-1.15.0rc1 | 2022-02-03T09:03:09+01:00 / false | same / rc | PASS |
| release-1.19.2 | 2024-03-07T09:10:46+01:00 / true | same / stable | PASS |
| release-1.25.1 | 2026-05-20T10:22:52+02:00 / true | same / stable | PASS |
| release-0.0 (first) | 2007-02-19T10:07:52Z / true | same / stable | PASS |
| release-1.26.1 (last) | 2026-09-16T09:30:25+02:00 / true | same / stable | PASS |
| all 214: `stable` vs pattern | 120 stable | `git -C $C tag -l 'release-*' \| grep -vE 'rc[0-9]\|@' \| wc -l` → 120; only release-1.4.13p1/p2 need the "p" allowance, which the brief's rule (rc/beta/alpha/dev only) permits | PASS |
| `span` | 2007-02-19 .. 2026-09-16 | min/max `released` over stable rows = 2007-02-19 (release-0.0) / 2026-09-16 (release-1.26.1) | PASS |
| migration-day trap | only release-1.6.3 has `released` = 2017-06-13 | it is the commit date of dc5d46b0 "pointrelease 1.6.3 tag" (2017-06-13T08:46:23Z), and `git -C $C show release-1.6.4:doc/Changelog \| grep -n -B5 '1.6.3 tag created'` puts that line under the header "13 June 2017: Wouter" — the date is in fact right, by coincidence with the import day | PASS (note) |

Tagger dates were also printed for every sampled tag: all pre-1.6.3 tags show 2017-06-13 and none was used as `released`.

## B. Default changes (all 30 rows)

Per row: (1) `git -C $C show --stat --format='%H %cI %s' <sha>`; (2) `git -C $C tag --contains <sha> | grep -x release-<version>`; (3) `git -C $C tag --contains <sha> | grep -E '^release-[0-9.]+$' | sort -V | head -1` plus `git -C $C log --all -i --grep='<words>'` for siblings, then the same tag-contains on every sibling; (4) `git -C $C show --format= <sha> -- <file> | grep -E '^[-+]'` and `git -C $C show <prev-tag>:<file> | grep <symbol>` vs `git -C $C show <tag>:<file> | grep <symbol>`.

All 30 rows: tag-contains HIT; earliest stable tag containing the commit (and every sibling found) equals the row's version; every commit touches product code or `configure.ac` (never test/doc only); `attribution: exact` on all 30 with a commit that shows the value. Row-specific evidence:

| row | version / commit | (1) product files touched | (4) before → after as read from the diff | sibling search | result |
|---|---|---|---|---|---|
| 0 | 0.5 / 134db23e | util/config_file.c | `-strdup("iterator")` → `+strdup("validator iterator")` (parent 134db23e^ has "iterator" at line 120) | 1 hit | PASS |
| 1 | 0.5 / d85debfa | util/config_file.c, validator/val_nsec3.c (+416), validator.c, … | `+strdup("1024 150 2048 500 4096 2500")` for `val_nsec3_key_iterations` | 3 hits ("nsec3 work"), all in release-0.5 | PASS |
| 2 | 0.6 / a0613187 | util/config_file.c, validator/validator.c (+testdata) | `+cfg->harden_dnssec_stripped = 1;` | 1 hit | PASS |
| 3 | 1.1.0 / 00f301d3 | util/config_file.c, iterator/iter_utils.c | `-cfg->bogus_ttl = 900;` → `+cfg->bogus_ttl = 60;`; at release-1.0.2 = 900, release-1.1.0 = 60 | 1 hit | PASS |
| 4 | 1.3.0 / 4b449309 | configure.ac, config.h.in, validator/val_sigcrypt.c | `+AC_ARG_ENABLE(sha2, … [--enable-sha2] …)`, `case "$enable_sha2" in yes)` defines USE_SHA2; val_sigcrypt.c wraps SHA256/512 in `#if … defined(USE_SHA2)`; release-1.2.1 has SHA256 code unguarded (15 hits) | 1 hit | PASS |
| 5 | 1.4.0 / 9a08ad41 | configure.ac | `-[--enable-sha2]` → `+[--disable-sha2]`; case flips `yes)` → `no)`; at release-1.3.4 still `--enable-sha2`/`yes)`, at release-1.4.0 `--disable-sha2`/`no)` | 1 hit | PASS |
| 6 | 1.4.6 / 518504ff | validator/val_utils.c, val_sigcrypt.c/.h | adds `algo_needs_init_ds`, `algo_needs_set_secure/bogus`, `algo_needs_missing` → "missing verification of …" reason | 1 hit | PASS |
| 7 | 1.4.7 / 93ffd446 | configure.ac | `-[--enable-gost] … experimental` → `+[--disable-gost]`; release-1.4.5/1.4.6 `case "$enable_gost" in yes)`, release-1.4.7 `no)`; 1.4.5 Changelog line 22 "GOST disabled-by-default" | 1 hit | PASS |
| 8 | 1.4.8 / daab92e9 | validator/val_utils.c/.h, autotrust.c, validator.c | `algo_needs` extended to trust anchors/5011 ("must have enough space for ALGO_NEEDS_MAX+1") | 1 hit | PASS |
| 9 | 1.4.17 / d71a1ba0 + 53a448ff | configure.ac | 53a448ff: `-[--enable-ecdsa]` → `+[--disable-ecdsa]`; release-1.4.16 configure.ac has 0 `ecdsa` lines; release-1.4.17 `case "$enable_ecdsa" in no)` | 1 hit | PASS |
| 10 | 1.4.19 / 5e5e89b9 | validator/val_secalgo.c | `case LDNS_RSAMD5:` `-return !FIPS_mode();` → `+/* RFC 6725 deprecates RSAMD5 */ return 0;` (release-1.4.18 line 154 still FIPS-conditional) | 4 hits: 87ded67c/98b6f906 (1.4.18) are FIPS-only disables, b44780b2 (1.4.19) adds the contrib patch → earliest unconditional disable is 1.4.19 | PASS |
| 11 | 1.5.5 / e65fdc31 | util/config_file.c | `-cfg->harden_algo_downgrade = 1;` → `+… = 0;`; release-1.5.4 = 1, release-1.5.5 = 0; 1.5.4 Changelog line 135 "Fix #644: harden-algo-downgrade option" | 1 hit | PASS |
| 12 | 1.6.1 / 367c3f03 | smallapp/unbound-anchor.c | adds `". IN DS 20326 8 2 E06D44B8…"`; release-1.6.0 has DS 19036 only, release-1.6.1 has 19036 + 20326 | 2 hits (7181c0fa in 1.8.0 is later) | PASS |
| 13 | 1.6.2 / 4d7d32c8 | validator/val_utils.c | `+/* accept any key algo, any digest algo */ digest_algo = -1;` under `!harden_algo_downgrade`; 1.1.0 Changelog line 164 "no longer possible to downgrade to SHA1" | 1 hit | PASS |
| 14 | 1.6.7 / ac9b95ca | util/config_file.c (196 files: iana/ldns bundle) | `-cfg->trust_anchor_signaling = 0;` → `+… = 1;`; release-1.6.6 = 0, release-1.6.7 = 1 | 1 hit | PASS |
| 15 | 1.7.1 / 4d06c363 | util/config_file.c, configparser.y, daemon/worker.c, services/mesh.c, … | `+cfg->root_key_sentinel = 1;`; symbol absent at release-1.7.0 | 1 hit | PASS |
| 16 | 1.8.0 / e0745813 | util/config_file.c (110 files) | `-cfg->harden_below_nxdomain = 0;` → `+… = 1;`; release-1.7.3 = 0, release-1.8.0 = 1 | 1 hit | PASS |
| 17 | 1.10.0 / 68ff1730 | configure.ac | `case "$enable_dsa" in` `-no) ;; *)` → `+yes) … *) # disable dsa by default, RFC 8624 section 3.1`; release-1.9.6 `no)`, release-1.10.0 `yes)` | 1 hit | PASS |
| 18 | 1.11.0 / 201c1583 + 6320776b | smallapp/unbound-anchor.c | `-". IN DS 19036 …"` removed; release-1.10.1 = 19036+20326, release-1.11.0 = 20326 | 3 hits, all in 1.11.0 | PASS |
| 19 | 1.13.2 / 11b3ebc3 | util/config_file.c | `-strdup("1024 150 2048 500 4096 2500")` → `+strdup("1024 150 2048 150 4096 150")`; release-1.13.1 vs 1.13.2 confirm | 1 hit | PASS |
| 20 | 1.15.0 / 32c3bbd2 | util/config_file.c | `-cfg->aggressive_nsec = 0;` → `+… = 1;`; release-1.14.0 = 0, release-1.15.0 = 1 | 2 hits, both 1.15.0 | PASS |
| 21 | 1.16.1 / e102aea7 (merge) + 2fba248e | validator/val_secalgo.c, val_sigcrypt.c, val_utils.c (via `git diff e102aea7^1 e102aea7`) | adds `digest_error_status()` returning `sec_status_indeterminate` on `EVP_R_INVALID_DIGEST`; callers count `numindeterminate` and treat all-indeterminate like unsupported | 3 hits; 9a2d0238 (1.19.3) is the later completion the row already cites | PASS |
| 22 | 1.19.1 / 882903f2 | validator/val_sigcrypt.c, val_utils.c, validator.c, val_nsec.c, val_nsec3.c, services/authzone.c (+tests) | `+#define MAX_VALIDATE_RRSIGS 8` (val_sigcrypt.c), `+#define MAX_DS_MATCH_FAILURES 4` (val_utils.c), `+#define MAX_VALIDATE_AT_ONCE 8`, `+#define MAX_VALIDATION_SUSPENDS 16` (validator.c). **Row text cites `validator/val_sigcrypt.h, validator/validator.h`; `git -C $C show release-1.19.1:validator/val_sigcrypt.h \| grep MAX_` is empty** | 1 hit | FAIL (file citation) |
| 23 | 1.19.1 / 92f2a1ca | validator/val_nsec3.c, validator.c, services/cache/dns.c (+tests) | `+#define MAX_NSEC3_CALCULATIONS 8`, `+#define MAX_NSEC3_ERRORS -1` in **val_nsec3.c**; row cites `validator/val_nsec3.h` (`git -C $C show release-1.19.1:validator/val_nsec3.h \| grep MAX_` empty) | 1 hit | FAIL (file citation) |
| 24 | 1.21.0 / f094f4ea | smallapp/unbound-anchor.c | `+". IN DS 38696 8 2 683D2D0A…"`; release-1.20.0 = 20326, release-1.21.0 = 20326+38696 | 1 hit | PASS |
| 25 | 1.22.0 / 24e0f0ab | iterator/iterator.c | `+limit_nsec_ttl()`: "Limit the NSEC and NSEC3 TTL values to the SOA TTL and SOA minimum TTL" | 1 hit | PASS |
| 26 | 1.23.0 / 35dbbcb2 | util/config_file.c | removes `#ifdef CLIENT_SUBNET … strdup("subnetcache validator iterator")` | 1 hit | PASS |
| 27 | 1.25.0 / db1fe8b4 | util/config_file.c, iter_scrub.c, configparser.y, remote.c | `+cfg->iter_scrub_rrsig = 8;` + `iter-scrub-rrsig:` option | 1 hit | PASS |
| 28 | 1.26.0 / fb274502 | validator/validator.c, val_utils.c | `+#define MAX_RRSETS_ANY_VALIDATED 24`, `shorten_answer_any()`; timer: `-if(vq->suspend_count > 3) slack += 3; else … slack += suspend_count` → `+if(vq->suspend_count > 0) slack += 1;` | 1 hit | PASS |
| 29 | 1.26.1 / 13b6717f | util/config_file.c, configparser.y, iter_scrub.c, mesh.c, … (31 files) | `-cfg->val_clean_additional = 1;` → `+… = 0; /* off to protect against much data. */`, `+cfg->val_validation_attempts = 32;`, `+cfg->val_hash_attempts = 32;`; release-1.26.0 = 1, release-1.26.1 = 0. Note: `git -C $C show release-1.26.1:doc/unbound.conf.5.in \| grep -A8 'val\\-clean\\-additional:'` still says **"Default: yes"** (master says "Default: no") — the man page lagged the code at the tag; see gap 13 | 2 hits (a7fc80d8 is master, untagged) | PASS (note) |

`applies_on_upgrade`/`opt_in` flags: rows 12, 18, 24 (`unbound-anchor` built-in key list) are `applies_on_upgrade: false`, which the diff supports (the list only matters when `unbound-anchor` creates/repairs `root.key`); rows 4/5/7/9/17 are build-time configure defaults that apply to anyone rebuilding the tag, marked `applies_on_upgrade: true`, `opt_in: false` — consistent with the diffs. All others are runtime `cfg->` defaults. No flag contradicts a diff.

## C. CVE fixes (all 79 rows)

Per row: inventory lookup in `data/software/cve_inventory.json` (`by_product.unbound`: 64 CVEs; `fixes.unbound`: 54); for every `fix_commits[].commit`: `git -C $C tag --contains <sha>`; earliest stable tag = `… | grep -E '^release-[0-9.]+(p[0-9])?$' | sort -V | head -1` and, across all tags containing any listed commit, the earliest by `git -C $C log -1 --format=%cI <tag>^{commit}`; `fix_released` = that date; `latency_days` recomputed as `fix_released − nvd_published`. Script: `/tmp/secC.py` (logic reproduced by the commands above).

Coverage: every one of the 64 `by_product` CVEs and 54 `fixes` CVEs appears in `cve_fixes[]`; the 9 rows not in the inventory at all are CVE-2026-77860, -77955, -78227, -80225, -81634, -81642, -82717, -82720, -85501 (all release-1.26.1), plus CVE-2026-14586 which is in `fixes` only.

Rows where every check passed (61): CVE-2009-3602 (fix_tag release-1.4.0rc1 contains 1a02ab89, earliest stable release-1.4.0, 2009-11-13 − 2009-10-13 = 31; the 1.3.4 tag is mis-imported and no dated "1.3.4 release" line exists in any Changelog, so this is the best the clone gives and the row says so), CVE-2009-4008 (null, see gaps), CVE-2010-0969, CVE-2011-1922, CVE-2011-4528, CVE-2014-8602, CVE-2019-25031..25042 (12 rows; all commits in release-1.9.6rc1, −509 d), CVE-2020-10772 (not applicable, reason given), CVE-2020-28935, CVE-2022-30698, CVE-2022-30699, CVE-2022-3204, CVE-2023-50387, CVE-2023-50868, CVE-2024-1931, CVE-2024-33655, CVE-2026-14586, CVE-2026-32665, CVE-2026-32792, CVE-2026-33278, CVE-2026-40691, CVE-2026-41292, CVE-2026-41637, CVE-2026-42534, CVE-2026-42923, CVE-2026-42944, CVE-2026-42955, CVE-2026-42959, CVE-2026-42960, CVE-2026-44390, CVE-2026-44608, CVE-2026-44621, CVE-2026-44687, CVE-2026-44690, CVE-2026-46582, CVE-2026-50045, CVE-2026-50046, CVE-2026-50243, CVE-2026-50251, CVE-2026-50252, CVE-2026-52863, CVE-2026-54478, CVE-2026-55708, CVE-2026-55717, CVE-2026-55973, CVE-2026-55990, CVE-2026-55991, CVE-2026-56416, CVE-2026-56444, CVE-2026-85501. For the 26 rows where the inventory's `fix_release` differs from the builder's `fix_tag` (1.7.0→1.7.0rc1, 1.9.6→1.9.4/1.9.5, 1.11.0→1.10.1 ×2, 1.13.0→1.13.0rc1, 1.19.3→1.19.2, 1.20.0→1.20.0rc1, 1.22.0→1.21.1, 1.24.0→1.23.1, 1.26.0→1.25.1/1.25.2 ×16), the builder's tag is in every case the earliest tag containing the branch fix commit; the inventory cites the master sibling SHA.

Rows that fail a check (18):

| row | check | command | expected | observed | result |
|---|---|---|---|---|---|
| CVE-2017-15105 | C.2/C.3 fix release date | `git -C $C show release-1.7.0:doc/Changelog \| sed -n 127,131p` → "19 January 2018: Wouter / - tag 1.6.8 for release with CVE fix. / - patch for CVE-2017-15105"; `git -C $C for-each-ref refs/tags/release-1.6.8 --format='%(taggerdate:iso-strict)'` → 2018-01-19T08:40:23+01:00; `git -C $C log -1 --format=%cI 2a6250e3` → 2018-01-19T…; `git -C $C diff --stat release-1.6.7 release-1.6.8` → empty | fix shipped in vendor release 1.6.8 on 2018-01-19; latency 2018-01-19 − 2018-01-23 = **−4** | row says fix_tag release-1.7.0rc1, fix_released 2018-03-06, latency **42**, because the clone's release-1.6.8 tag is a bare re-tag of 1.6.7. The `.md` note itself states "The vendor point release 1.6.8 (2018-01-19) carried it". The clone cannot show 1.6.8's tree, but it does show the release day twice (Changelog line and tagger date). | FAIL |
| CVE-2019-16866 | C.2 fix_tag contains every fix_commit | `git -C $C tag --contains facc6c654144 \| grep -x release-1.9.4` | hit | miss (facc6c65 is the master merge, first in release-1.9.6rc1; per-commit `first_tag` says so) | FAIL (labelling) |
| CVE-2019-18934 | C.2 | `git -C $C tag --contains 09845779d5f2 \| grep -x release-1.9.5` | hit | miss (master sibling, first in release-1.9.6rc1) | FAIL (labelling) |
| CVE-2020-12662 | C.2 | `git -C $C tag --contains ba0f382eee81 \| grep -x release-1.10.1` | hit | miss (master sibling, release-1.11.0rc1) | FAIL (labelling) |
| CVE-2020-12663 | C.2 | same commit as above | hit | miss | FAIL (labelling) |
| CVE-2024-8508 | C.2 | `git -C $C tag --contains a1b25f029641 \| grep -x release-1.21.1` | hit | miss (master note commit, release-1.22.0rc1) | FAIL (labelling) |
| CVE-2025-11411 | C.2 | `git -C $C tag --contains f6269baa605d \| grep -x release-1.24.1` | hit | miss ("Additional fix", release-1.24.2) | FAIL (labelling) |
| CVE-2025-5994 | C.2 | `git -C $C tag --contains f49e6ccecd0b \| grep -x release-1.23.1` | hit | miss (master sibling, release-1.24.0rc1) | FAIL (labelling) |
| CVE-2026-40622 | C.2 | `git -C $C tag --contains 13ec8d0f261e \| grep -x release-1.25.1` | hit | miss ("Extra fix", release-1.25.2) | FAIL (labelling) |
| CVE-2026-50248 | C.2 | `git -C $C tag --contains cf5e6e89a582 \| grep -x release-1.25.2` | hit | miss ("Fix error in log printout", release-1.26.0rc1) | FAIL (labelling) |
| CVE-2026-77860, -77955, -78227, -80225, -81634, -81642, -82717, -82720 (8 rows) | C.1 not in inventory, `applicable: true`, row must say why | `python3 -c "…print(row.get('note'))"` | a per-row reason | `note` absent; `description` empty; the reason exists only in `gaps[]` ("inventory generated before release-1.26.1") | FAIL (missing per-row reason) |

For the nine "labelling" rows the row-level `fix_tag`, `fix_released`, `first_stable_tag` and `latency_days` are all correct (verified: the tag contains the branch commit, is the earliest by version and by date, and the latency recomputes). Only the `fix_commits[]` list mixes in master siblings / follow-up fixes without a role marker, which the brief's C.2 forbids.

## D. Changelog entries (20 random kept entries)

Sample: `random.seed(20260929); random.sample(pool, 20)` over the 754 kept entries of stable releases (file order); 19 distinct releases. Commands per entry: `git -C $C show <tag>:doc/Changelog | grep -F '<line>'` (present), `git -C $C show <prev_stable_tag>:doc/Changelog | grep -F '<line>'` (absent), mechanism read against the text, and `git -C $C diff <prev_stable_tag> <tag> -- doc/Changelog | grep -cE '^\+\s*- '` for `total_entries`.

| tag (prev) | line | mech | @tag / @prev | total_entries / recount | result |
|---|---|---|---|---|---|
| release-1.5.9 (1.5.8) | Document write permission to directory of trust anchor… | trust-anchor-5011 | 1 / 0 | 68 / 68 | PASS |
| release-1.13.2 (1.13.1) | Fix unit test in the ctime_r calls for autotrust… | trust-anchor-5011 | 1 / 0 | 154 / 154 | PASS |
| release-1.26.1 (1.26.0) | Fix CVE-2026-80225, Possible degradation of service… | other | 0 / 0 — branch point release; `evidence.changelog_path` = "commit message of e619ead2db (git log release-1.26.0..release-1.26.1)"; `git -C $C log release-1.26.0..release-1.26.1 --format='%h %s' \| grep -F 'Fix CVE-2026-80225'` → e619ead2; text present in `master:doc/Changelog` | 10 / 11 commits in range (one is the version commit) | PASS (by the documented method) |
| release-1.4.9 (1.4.8) | Added explicit note on unbound-anchor usage: | trust-anchor-5011 | 1 / 0 | 19 / 19 | PASS |
| release-1.25.2 (1.25.1) | Fix CVE-2026-46582, A wildcard replay… | validation | 0 / 0 — branch release; `git -C $C log release-1.25.1..release-1.25.2 --format='%h %s' \| grep -F 'Fix CVE-2026-46582'` → fea0ff55; present in `release-1.26.0:doc/Changelog` | 24 / 26 commits (8 %) | PASS (by the documented method) |
| release-1.8.0 (1.7.3) | Update libunbound/python/examples/dnssec_test.py… | trust-anchor-5011 | 1 / 0 | 94 / 93 (1 %) | PASS |
| release-1.2.0 (1.1.1) | HINFO no longer downcased for validation… | validation | 1 / 0 | 53 / 53 | PASS |
| release-1.7.0 (1.6.8) | Fix to check define of DSA for when openssl is without depre… | other | 1 / 0 | 95 / 95 | PASS |
| release-1.4.2 (1.4.1) | Re-query pattern changed on validation failure… | dnskey | 1 / 0 | 59 / 59 | PASS |
| release-1.23.0 (1.22.0) | More descriptive text for 'harden-algo-downgrade'. | validation | 1 / 0 | 99 / 99 | PASS |
| release-1.5.5 (1.5.4) | 5011 implementation does not insist on all algorithms… | trust-anchor-5011 | 1 / 0 | 38 / 38 | PASS |
| release-1.9.5 (1.9.4) | Fix CVE-2019-18934, shell execution in ipsecmod. | other | 0 / 0 — branch release; `git -C $C log release-1.9.4..release-1.9.5 --format='%h %s' \| grep -F 'Fix CVE-2019-18934'` → 34e52a43; present in `release-1.9.6:doc/Changelog` | 1 / 2 commits (the other is the branch/version commit) | PASS (by the documented method) |
| release-0.5 (0.4) | fixed error in parser with backwards rrsig references. | rrsig | 1 / 0 | 182 / 182 | PASS |
| release-1.12.0 (1.11.0) | Merge PR #284 and Fix #246: Remove DLV entirely… | trust-anchor-5011 | 1 / 0 | 50 / 50 | PASS |
| release-0.4 (0.3) | config options harden-short-bufsize and harden-large-queries | validation | 1 / 0 | 187 / 187 | PASS |
| release-1.4.17 (1.4.16) | Fix validation of nodata for DS query in NSEC zones… | validation | 1 / 0 | 49 / 49 | PASS |
| release-1.11.0 (1.10.1) | Merge #225 from akhait: KSK-2010 has been revoked… | trust-anchor-5011 | 1 / 0 | 114 / 114 | PASS |
| release-1.22.0 (1.21.1) | Fix negative cache NSEC3 parameter compares for zero length… | nsec3 | 1 / 0 | 50 / 50 | PASS |
| release-1.23.0 (1.22.0) | Fix #986: Resolving sas.com with dnssec-validation fails… | validation | 1 / 0 | 99 / 99 | PASS |
| release-1.6.4 (1.6.3) | Fix #1259: "--disable-ecdsa" argument overwritten | alg-ecdsa | 1 / 0 | 88 / 88 | PASS |

No entry is present at both its tag and the previous stable tag. No `cds-cdnskey`-on-ECDSA false positive in the sample. Mechanism labels match the text (the two "other" labels are non-DNSSEC lines; `trust-anchor-5011` on the ctime_r/autotrust unit-test line is a keyword heuristic the JSON's gap 9 already declares).

## E. Coverage and gaps

| check | command | expected | observed | result |
|---|---|---|---|---|
| E.1 tag count | `git -C $C tag -l 'release-*' \| wc -l` | 214 = `release_count` = len(`releases[]`) | 214 / 214 / 214; stable 120 = 120 `stable: true` | PASS |
| E.2 tags missing from `releases[]` | set difference both ways | none | none either way | PASS |
| E.3 gap 1 (five re-tags: "real release dates are not in the clone … must not be used") | `git -C $C for-each-ref refs/tags/release-1.6.5 refs/tags/release-1.6.8 --format='%(refname) %(taggerdate:iso-strict)'`; `git -C $C show release-1.6.6:doc/Changelog \| sed -n 50,61p` (header "22 August 2017" over "tag 1.6.5 with pointrelease 1.6.5 (1.6.4 plus 5011 fix)"); `git -C $C show release-1.7.0:doc/Changelog \| sed -n 127,128p` ("19 January 2018 … tag 1.6.8 for release with CVE fix"); `git -C $C show release-1.6.4:doc/Changelog \| sed -n 25,38p` ("13 June 2017 … 1.6.3 tag created, with only #1280 fix") | undeterminable | Three of the five dates are determinable from the clone: 1.6.3 = 2017-06-13 (the recorded value is right), 1.6.5 = 2017-08-21 (tagger) / 22 Aug (Changelog header), 1.6.8 = 2018-01-19 (tagger and Changelog). Only 1.4.13p1/p2 have no dated line (`git -C $C show release-1.4.14:doc/Changelog \| grep -i '13p'` empty) and migration-day taggers. The trees are indeed missing. | FAIL (partly determinable) |
| E.3 gap 13 (man page "could not be grepped for a val-clean-additional default sentence") | `git -C $C show release-1.26.1:doc/unbound.conf.5.in \| grep -n -A8 'val\\-clean\\-additional:'` | undeterminable | matches at line 2608; "Default: yes" at both release-1.26.0 and release-1.26.1; `master:doc/unbound.conf.5.in` says "Default: no". Determinable in one command; the finding is that the man page lagged the code at the tag. | FAIL |
| E.3 gap 3 (CVE-2009-4008 unmapped) | `git -C $C diff release-1.4.3 release-1.4.4 -- doc/Changelog \| grep -E '^\+' \| grep -iE 'dnssec\|signed\|respon\|bug#'` | undeterminable | only bug#305 (pkt_dname_tolower), bug#301 (checkconf) and the .de EDNS-probe entry; nothing names the CVE or "no response for signed zones". Not determinable from the clone. | PASS |
| E.3 other gaps (2, 4–12, 14) | read | statements of what could not be determined | each is either a documented method limitation (branch releases, keyword heuristics, late entries, no built-in trust anchor, ldns bundling) or a fact confirmed above (1.3.4 mis-import, 1.26.1 CVEs post-date the inventory) | PASS |
| E (unlisted) sixth/seventh mis-import: release-1.8.2 / release-1.8.3 | `git -C $C log -1 --format='%h %cI %s' release-1.8.2^{commit}` → 2195bf50 2018-11-29 "tag 1.8.2rc1"; `git -C $C log -1 --format='%h %cI %s' release-1.8.3^{commit}` → d29c1f06 2018-12-04 "update windows icon, larger and with transparency."; `git -C $C diff --stat release-1.8.2 release-1.8.3` → `winrc/combined.ico` only; `git -C $C show release-1.9.0:doc/Changelog \| sed -n 148,151p` → "tag for 1.8.2rc1, which became 1.8.2 on 4 dec 2018, with icon updated … Which became 1.8.3 on 11 december with only the dns64 fix of 6 dec."; `git -C $C tag --contains 42244e1b \| sort -V \| head -1` → release-1.9.0 | every stable tag's tree and date is the release's | The clone's release-1.8.2 is the rc1 commit (real 1.8.2 = 4 Dec 2018, the icon commit that the clone tags as release-1.8.3); the clone's release-1.8.3 (2018-12-04, `total_entries: 0`) is not the 11 Dec 2018 release and lacks its only change (42244e1b, first in release-1.9.0). Not DNSSEC-related and no CVE, so no latency impact, but `releases[]` dates for 1.8.2 (should be 2018-12-04) and 1.8.3 (should be 2018-12-11, tree missing) are wrong and un-noted. | FAIL |
| `.md` vs `.json` | header figures (214/120/94, span), 30-row default table, 79-row CVE table (fix tag, fix date, NVD date, latency per row), 14 gap bullets, branch-release list | identical | identical on every compared field | PASS |

## Corrections required

1. **`cve_fixes[CVE-2017-15105].fix_released` / `latency_days`** — wrong: `2018-03-06` / `42` (from `fix_tag: release-1.7.0rc1`); right: vendor release **1.6.8, 2018-01-19, latency −4**, with `attribution: approximate` (the clone's release-1.6.8 tag is a bare re-tag, so `fix_tag` may stay release-1.7.0rc1 as the first tag whose tree contains 2a6250e3, but the date fed to the inventory must be 1.6.8's). Proof: `git -C $C show release-1.7.0:doc/Changelog | sed -n 127,131p` ("19 January 2018 … tag 1.6.8 for release with CVE fix … patch for CVE-2017-15105"); `git -C $C for-each-ref refs/tags/release-1.6.8 --format='%(taggerdate:iso-strict)'` → 2018-01-19T08:40:23+01:00; `git -C $C diff --stat release-1.6.7 release-1.6.8` → empty. The inventory's `fixes.unbound` entry (1.7.0, 2018-03-12) is wrong for the same reason.
2. **`cve_fixes[].fix_commits[]` for CVE-2019-16866 (facc6c65), CVE-2019-18934 (09845779), CVE-2020-12662 and CVE-2020-12663 (ba0f382e), CVE-2024-8508 (a1b25f02), CVE-2025-11411 (f6269baa), CVE-2025-5994 (f49e6cce), CVE-2026-40622 (13ec8d0f), CVE-2026-50248 (cf5e6e89)** — wrong: listed as fix commits although `fix_tag` does not contain them; right: move them to a `sibling_commits`/`followup_commits` field or mark `role: "master-sibling"` / `"follow-up"`, keeping `fix_tag` and `latency_days` as they are (both verified correct). Proof for each: `git -C $C tag --contains <sha> | grep -x <fix_tag>` → no output.
3. **`cve_fixes[]` rows CVE-2026-77860, -77955, -78227, -80225, -81634, -81642, -82717, -82720** — wrong: `in_inventory_by_product: false`, `applicable: true`, no `note`; right: add `note: "not in cve_inventory.json (generated before release-1.26.1); NVD date unknown"` as CVE-2026-85501's row-level treatment implies. Proof: `python3 -c "import json;d=json.load(open('data/software/timelines/unbound.json'));print([x.get('note') for x in d['cve_fixes'] if x['cve'] in ('CVE-2026-77860','CVE-2026-82720')])"` → `[None, None]`.
4. **`default_changes[22].after`** (1.19.1 KeyTrap) — wrong: "(validator/val_sigcrypt.h, validator/validator.h)"; right: `MAX_VALIDATE_RRSIGS` in `validator/val_sigcrypt.c`, `MAX_DS_MATCH_FAILURES` in `validator/val_utils.c`, `MAX_VALIDATE_AT_ONCE`/`MAX_VALIDATION_SUSPENDS` in `validator/validator.c`. Proof: `git -C $C show --format= 882903f2 | grep -E '^(\+\+\+|\+#define MAX_)'`; `git -C $C show release-1.19.1:validator/val_sigcrypt.h | grep MAX_` → empty. Values (8, 4, 8, 16) are correct.
5. **`default_changes[23].after`** (1.19.1 NSEC3 cap) — wrong: "(validator/val_nsec3.h)"; right: `validator/val_nsec3.c`. Proof: `git -C $C show --format= 92f2a1ca | grep -E '^(\+\+\+|\+#define MAX_)'`; `git -C $C show release-1.19.1:validator/val_nsec3.h | grep MAX_` → empty. Values (8, −1) are correct.
6. **`gaps[0]`** (five re-tags) — wrong: "their real release dates are not in the clone"; right: 1.6.3 = 2017-06-13 (Changelog header at release-1.6.4, so the recorded date stands), 1.6.5 = 2017-08-21 (tagger; Changelog header 22 August 2017 at release-1.6.6), 1.6.8 = 2018-01-19 (tagger; Changelog at release-1.7.0); only 1.4.13p1/p2 are undatable from the clone. Also add a `stability_note` to each of the five `releases[]` rows (currently empty) saying the `released` value is the predecessor's commit date, and the same for release-1.3.4 (`released` 2009-08-04 is the "1.3.3 release." commit; the real 1.3.4 is October 2009 and undated in the clone). Proof: commands in E.3 gap 1 above.
7. **`gaps[12]`** (man page not greppable) — wrong; right: "`doc/unbound.conf.5.in` at release-1.26.1 still documents `val-clean-additional` as `Default: yes` (line 2616); the code default is 0 at the tag and the man page was corrected on master." Also worth a sentence in `default_changes[29].documentation`. Proof: `git -C $C show release-1.26.1:doc/unbound.conf.5.in | sed -n 2608,2616p`; `git -C $C show master:doc/unbound.conf.5.in | grep -n -A9 'val\\-clean\\-additional:' | grep Default` → "Default: no".
8. **`releases[]` release-1.8.2 and release-1.8.3, and a new gap** — wrong: 1.8.2 `released` 2018-11-29 (rc1 commit), 1.8.3 `released` 2018-12-04 with `total_entries: 0`; right: 1.8.2 = 2018-12-04 (the icon commit d29c1f06 the clone tags as release-1.8.3), 1.8.3 = 2018-12-11 with its only change (42244e1b, dns64 region fix) absent from any 1.8.x tag; add both to the mis-import gap. Proof: E.3 row above (`git -C $C show release-1.9.0:doc/Changelog | sed -n 148,151p`; `git -C $C diff --stat release-1.8.2 release-1.8.3`).

Nothing in the four hard claims needs correcting: the five re-tags are bare (claim 1), release-1.3.4 lacks 1a02ab89 (claim 2), release-1.19.2 / release-1.21.1 / release-1.9.4 are the earliest stable tags containing the respective fixes and the inventory's 1.19.3 / 1.22.0 / 1.9.6 are wrong (claim 3), and all six SVN-era default commits touch `util/config_file.c` or `configure.ac` with the before/after value in the hunk (claim 4).

## Not verifiable

* Real-world release dates of release-1.4.13p1 / p2 and release-1.3.4: no dated Changelog line and migration-day tagger dates. The rows' `released` values are the predecessor's commit dates and should not be used (already the builder's position, minus the per-row note).
* Whether the 2018-01-19 / 2017-08-21 tagger dates are the vendor announcement days rather than the day the tag was pushed: the clone shows two independent same-day sources (tag object, Changelog header) but no tarball.
* CVE-2009-4008's fix commit: nothing in `release-1.4.3..release-1.4.4` names it or matches the NVD text; the builder's `null` stands.
* Latencies for the ten release-1.26.1 CVEs: no NVD dates in the inventory (generated before 2026-09-16).
* `applies_on_upgrade` for the build-time rows (4, 5, 7, 9, 17) depends on the packager rebuilding with default configure flags; the clone cannot show what distributions did.

## Totals

| section | checks run | passed | failed |
|---|---|---|---|
| Hard claims 1–4 (+ stray tag) | 8 | 8 | 0 |
| A. Release dates | 25 (20 sampled + first + last + all-214 stable flag + span + migration-day) | 25 | 0 |
| B. Default changes | 30 rows (each: stat, tag-contains, earliest/siblings, before-after, flags, attribution) | 28 | 2 (rows 22, 23: wrong file cited, values right) |
| C. CVE fixes | 79 rows | 61 | 18 (1 date/latency: CVE-2017-15105; 9 fix_commits labelling; 8 missing per-row inventory reason) |
| D. Changelog entries | 20 | 20 | 0 (3 branch-release entries pass by the documented commit-log method, not by the tag Changelog) |
| E. Coverage and gaps | 8 (tag count, missing tags, gaps 1/3/13, other gaps, 1.8.2/1.8.3 scan, .md vs .json) | 5 | 3 (gap 1 partly determinable, gap 13 determinable, 1.8.2/1.8.3 mis-import unlisted) |
| **Total** | **170** | **147** | **23** |
