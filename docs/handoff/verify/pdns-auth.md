# Phase 3 verification: pdns-auth (PowerDNS Authoritative Server)

## Verdict

**PASS WITH CORRECTIONS** - every date, stable flag, tag membership and first-stable-tag in `default_changes[]` and `cve_fixes[]` reproduces from the clone and all five headline claims survive, but there is one wrong statement in a default-change row (the `add-superfluous-nsec3` option removal), one missing default change (`fae95f259`, add-zone-key ECDSA), a systematically inflated `total_entries`, one junk changelog entry, and a fix-date/embargo skew on CVE-2022-27227.

Inputs: `data/software/timelines/pdns-auth.{json,md}` at HEAD (`30d4582f`), clone `out/software_repos/pdns.git` (bare, blob-less; tags are lightweight, so `%cI` of `<tag>^{commit}` is the tag date). Shorthand: `G=out/software_repos/pdns.git`. Sampling seed: Python `random.seed(20260929)`.

## Answers to the five scrutinised claims

1. **4.0.0 ECDSA default: HOLDS.**
   - All four commits touch product code. Checked with `git -C $G show --stat=200 --format='%H %cI %s' <c>`:
     - `5209ee174`: `pdns/common_startup.cc`, `pdns/pdns.conf-dist`, `pdns/pdnsutil.cc`
     - `d113baca3`: `pdns/common_startup.cc`, `pdns/pdns.conf-dist`, `pdns/pdnsutil.cc`
     - `b6bd795ce`: `pdns/dbdnsseckeeper.cc`, `pdns/pdnsutil.cc`, `pdns/dnsseckeeper.hh` and others
     - `1fe96a070`: `pdns/common_startup.cc`, `pdns/pdns.conf-dist`, `pdns/pdnsutil.cc`
   - The diffs read as claimed: `5209ee174` sets ksk `rsasha256` to `""`; `d113baca3` sets zsk `rsasha256` to `ecdsa256`; `1fe96a070` sets ksk `""` to `ecdsa256` and zsk `ecdsa256` to `""`; `b6bd795ce` makes addKey throw when bits==0 and algorithm<=10.
   - `git -C $G show auth-3.4.11:pdns/common_startup.cc | grep -n default-.sk-algorithms` gives `rsasha256` for both (lines 165, 167).
   - `git -C $G show auth-4.0.0:pdns/common_startup.cc | grep -n default-.sk-algorithms` gives ksk `ecdsa256` and zsk `""` (lines 179, 181).
   - No stable 3.x tag ever defaulted to ecdsa256. I scanned all 20 stable `auth-3.*` tags (`pdns/common_startup.cc`, `pdns/pdnssec.cc`, `pdns/pdnsutil.cc`, `pdns/pdns.conf-dist`) for `default-[kz]sk-algorithms.*ecdsa256`: 0 hits. I also scanned their `pdnssec.cc` for `int algorithm=13`: 0 hits.
   - CAVEAT: `fae95f259` (2016-04-05) changed the add-zone-key and generate-zone-key default from 8 to 13 and is not in `default_changes[]`. See Correction 2.
2. **max-nsec3-iterations 500 to 100 "applies on upgrade" vs nsec3param `1 0 1 ab` to `1 0 0 -` "opt-in only": BOTH FLAGS RIGHT.**
   - 4.5.0: `5a5d565f0` changes the `common_startup.cc` default to "100" and adds `&& !isPresigned(...)` to the clamp in `DNSSECKeeper::getNSEC3PARAM`.
   - `git -C $G show auth-4.5.0:pdns/dbdnsseckeeper.cc | sed -n 347,353p` shows the clamp runs on every read of stored NSEC3PARAM. So every existing zone with more than 100 iterations changes behaviour on upgrade, with no operator action. `applies_on_upgrade=true`, `opt_in=false` are correct.
   - `pdnsutil.cc:106` at auth-4.5.0 still says "500" (confirmed).
   - 4.6.0: `6830fcce2` edits only `pdns/pdnsutil.cc` line 3022, the fallback when `set-nsec3 ZONE` is run without a parameter string.
   - `git -C $G grep -n -e '1 0 1 ab' -e '1 0 0 -' auth-4.5.3 -- pdns modules` gives 1 hit (`pdnsutil.cc:2988`). The same grep on auth-4.6.0 gives 1 hit (`pdnsutil.cc:3065`). There is no other consumer, so existing NSEC3PARAM is untouched. `applies_on_upgrade=false`, `opt_in=true` are correct.
   - NOTE: the flag semantics are not uniform. Rows 3.2 (add-zone-key) and 4.0.0 (secure-zone) are also explicit operator commands but carry `opt_in=false`, while 3.3 and 4.6.0 (set-nsec3) carry `opt_in=true`. Defensible, but define it in the schema.
3. **Five CVE fix tags that disagree with the inventory: the TIMELINE is right in all five.** Details are in section C, rows "disputed". The inventory `fixes` block names the next MASTER release (3.3.1 and 4.2.0 respectively), or has no fix release at all, and its NVD text agrees with the timeline.
   - CVE-2012-0206: `auth-3.0.1`. Inventory says 3.3.1.
   - CVE-2019-3871: `auth-4.0.7`.
   - CVE-2019-10203: `auth-4.1.11`.
   - CVE-2022-27227: `auth-4.6.1`.
   - CVE-2018-1046: `auth-4.1.2`. Inventory says 4.2.0.
   - CVE-2019-3871, CVE-2019-10203 and CVE-2022-27227 have no inventory fix release; the inventory holds only the NVD text (4.0.7/4.1.7; 4.0.9/4.1.11; 4.4.3/4.5.4/4.6.1). The timeline agrees with the NVD text.
   - CVE-2019-3871, CVE-2019-10203 and CVE-2022-27227 each have sibling stable tags released the same calendar day. The chosen tag is earliest by tag-commit time; see the release-date advisory under Correction 5.
4. **Tag prefixes: HOLDS.** All 15 `fix_tag`s are `auth-*`. No `rec-` or `dnsdist-` tag, and no `pdns-` fix tag. CVE-2008-3337 uses `auth-2.9.22` by content; see its row.
5. **Eight fixes-only rows are in authoritative code paths: HOLDS.**
   - No fix commit touches `pdns/recursordist/` (`git -C $G show --name-only --format= <c> | grep -c recursordist` gives 0 for all eight).
   - The `auth-4.9.14` commits sit on `rel/auth-4.9.x` (`git -C $G branch -a --contains <c>`). The 5.0.4 siblings sit on `rel/auth-5.0.x`.
   - The touched code is auth-specific or shared-and-built-into-auth: `modules/bindbackend`, `modules/ldapbackend`, `pdns/rfc2136handler.cc`, `pdns/dnswriter.cc`, `pdns/dnsparser.cc`, and `ext/yahttp` (referenced 6 times in `auth-4.9.14:pdns/Makefile.am`; the auth web server).
   - `pdns/dnsreplay.cc` (CVE-2018-1046) is an auth tool (`Makefile.am` lines 87, 118, 901).
   - CVE-2026-33257 and CVE-2026-33260 have NVD product = pdns-rec because `ext/yahttp` is shared. The auth fix is nevertheless real on the auth branches.

## Check table

Legend: `PASS` or `FAIL`. A `merge-base` check means `git -C $G merge-base --is-ancestor <c> '<tag>^{commit}'`. `tc` means the real `git -C $G tag --contains <c>`. I ran `tc` for all 12 default-change commits and all 32 CVE fix commits (44 runs, roughly 1 minute each), each filtered to `^(auth|pdns)-`. For six commits (`1fe96a070 5a5d565f0 6830fcce2 0ba8e0f16 d33ba8ebf b3dec9c7e`) I also ran `merge-base` against all 196 tags. The two sets were identical (141/141, 80/80, 68/68, 168/168, 5/5, 2/2 tags, diff 0). "First stable" is the earliest non-alpha/beta/rc tag by tag-commit date.

### A. Release dates and stable flags (23 run, 23 pass, 0 fail)

Command for each row: `git -C $G log -1 --format=%cI <tag>^{commit}`. Expected equals JSON `released_full`. Sample: first release, last release, plus `random.seed(20260929); random.sample(releases, 20)`. All 22 tags gave observed == expected, and none has a migration-day date. `pdns-2.9*` dates are real svn commit dates, not a single import day.

| # | tag | expected = observed | stable | result |
|---|---|---|---|---|
| 1 | pdns-2.9 (first) | 2002-11-28T14:38:00Z | true | PASS |
| 2 | auth-5.2.0-alpha0 (last by list) | 2026-06-02T08:48:50+02:00 | false | PASS |
| 3 | auth-4.3.0-alpha1 | 2019-12-09T16:26:22+01:00 | false | PASS |
| 4 | auth-4.6.2 | 2022-03-28T20:16:13+02:00 | true | PASS |
| 5 | auth-5.1.0-alpha1 | 2026-03-13T16:40:37+01:00 | false | PASS |
| 6 | auth-4.1.1 | 2018-02-16T09:45:25+01:00 | true | PASS |
| 7 | auth-4.9.12 | 2025-12-08T14:47:18+01:00 | true | PASS |
| 8 | auth-4.5.0-rc1 | 2021-06-24T17:07:00+02:00 | false | PASS |
| 9 | auth-3.3.2 | 2015-05-01T09:05:37+02:00 | true | PASS |
| 10 | auth-4.4.0 | 2020-12-17T09:12:40+01:00 | true | PASS |
| 11 | auth-4.0.1 | 2016-07-29T16:28:18+02:00 | true | PASS |
| 12 | auth-4.8.4 | 2023-12-18T12:33:02+01:00 | true | PASS |
| 13 | auth-4.2.0 | 2019-08-27T15:34:17+02:00 | true | PASS |
| 14 | auth-4.5.3 | 2022-01-18T22:41:37+01:00 | true | PASS |
| 15 | pdns-2.9.18 | 2005-07-16T12:07:58Z | true | PASS |
| 16 | auth-4.6.0-rc1 | 2022-01-13T13:50:59+01:00 | false | PASS |
| 17 | pdns-2.9.2 | 2002-12-13T15:22:33Z | true | PASS |
| 18 | auth-4.1.6 | 2019-01-04T09:42:54+01:00 | true | PASS |
| 19 | auth-4.6.0-beta1 | 2021-12-07T13:12:02+01:00 | false | PASS |
| 20 | auth-4.8.0 | 2023-05-31T23:57:54+02:00 | true | PASS |
| 21 | auth-4.8.2 | 2023-09-04T12:12:49+02:00 | true | PASS |
| 22 | auth-4.4.0-alpha3 | 2020-11-03T15:28:11+01:00 | false | PASS |
| 23 | all 196 releases: `stable == !re.search('alpha\|beta\|rc\|dev', tag)` | 0 mismatches | | PASS |

Note: `released` is the commit date of the tagged commit, not the public release date. The changelogs and advisories give later dates for several security releases (see Correction 5).

### B. Default changes (81 run, 78 pass, 3 fail)

B1 = `git -C $G show --stat=200 --format='%H %cI %s' <commit>`: product code, not tests or docs. B2 = `git -C $G tag --contains <commit> | grep -x <first_tag>`. B3 = earliest stable tag across sibling commits (`git -C $G log --all --format='%h %cI %s' -i --grep=<distinctive words>`, then earliest stable `tag --contains` across siblings). B4 = before/after readable from `git -C $G show <commit>` or `git -C $G show <tag>:<path>`. B5 = the `applies_on_upgrade` and `opt_in` flags. B6 = attribution is stated or exact.

| # | row (commit) | B1 | B2 (first tag / first stable) | B3 | B4 | B5 | B6 |
|---|---|---|---|---|---|---|---|
| 1 | 3.2 add-zone-key RSASHA1 to RSASHA256 (`0ba8e0f16`) | PASS: `pdns/pdnssec.cc` only (`int algorithm=5` to `8`) | PASS: `auth-3.2-rc1` / `auth-3.2` (168 tags) | PASS: `--grep 'add-zone-key default'` finds only this commit | PASS | PASS (existing keys untouched) | PASS |
| 2 | 3.3 set-nsec3 `1 1 1 ab` to `1 0 1 ab` (`b8adb30df`) | PASS: `pdns/pdnssec.cc` plus other `pdns/` files (91 files, mostly regression) | PASS: `auth-3.3-rc1` / `auth-3.3` | PASS: `--grep 'non opt-out'` finds only master siblings (`528c12181` is `validate.cc`) | PASS: `git show auth-3.2:pdns/pdnssec.cc` line 1011 `"1 1 1 ab"`; `auth-3.3` line 1212 `"1 0 1 ab"`; the "insist on opt-out" error is removed | PASS (opt-in) | PASS |
| 3 | 3.3.2 add-superfluous yes to no (`b3dec9c7e`) | PASS: `pdns/common_startup.cc`, `pdns/pdns.conf-dist` | PASS: `auth-3.3.2` / `auth-3.3.2` (2 tags) | PASS: option-only backport | **FAIL**: text says "option dropped in auth-3.4.0-rc2" and "master (3.4.0-rc1) still shipped =yes". Both wrong. See Correction 1 | PASS | PASS |
| 4 | 3.4.0 max-nsec3-iterations introduced 500 (`28b66a947`, `017a78b85`) | PASS: `common_startup.cc`, `dbdnsseckeeper.cc`, `pdns.conf-dist`, `pdnssec.cc` | PASS: `auth-3.4.0-rc1` / `auth-3.4.0`; backport `017a78b85` is `auth-3.3.2` (later) | PASS: 3.4.0 (2014-09-30) precedes 3.3.2 (2015-05-01) | PASS: `getNSEC3PARAM` clamps on read, `setNSEC3PARAM` throws | PASS | PASS |
| 5 | 3.4.7 iterations enforced in bindbackend (`d33ba8ebf`) | PASS: `modules/bindbackend/binddnssec.cc`, `bindbackend2.hh` | PASS: `auth-3.4.7` / `auth-3.4.7` (5 tags) | PASS: master sibling `e44d76b69` (2015-07-28) first ships in `auth-4.0.0-alpha1` (later) | PASS | PASS | PASS |
| 6 | 4.0.0 default-ksk rsasha256 to `""` (`5209ee174`) | PASS: `common_startup.cc`, `pdns.conf-dist`, `pdnsutil.cc` | PASS: `auth-4.0.0-alpha1` / `auth-4.0.0` (143 tags) | PASS | PASS (diff read) | PASS | PASS |
| 7 | 4.0.0 default-zsk rsasha256 to ecdsa256 (`d113baca3`) | PASS: `common_startup.cc`, `pdns.conf-dist`, `pdnsutil.cc` (148 files, mostly regression) | PASS: `auth-4.0.0-alpha1` / `auth-4.0.0` | PASS: `--grep ecdsa256` finds `744f43704` merge and `fae95f259` (see row 12) | PASS | PASS | PASS |
| 8 | 4.0.0 net effect: ksk ecdsa256, zsk `""` (`1fe96a070`) | PASS: `common_startup.cc`, `pdns.conf-dist`, `pdnsutil.cc` | PASS: `auth-4.0.0-alpha3` / `auth-4.0.0` (141 tags; ancestry 141/141) | PASS | **FAIL**: `scope` says "keys created by secure-zone / add-zone-key". This commit does not touch add-zone-key's literal default, which was changed by `fae95f259`. See Correction 2 | PASS | PASS |
| 9 | 4.0.0 addKey no RSA size guess (`b6bd795ce`) | PASS: `pdns/dbdnsseckeeper.cc`, `pdnsutil.cc`, `dnsseckeeper.hh`, `dnssecsigner.cc`, `ws-auth.cc` | PASS: `auth-4.0.0-alpha2` / `auth-4.0.0` | PASS | PASS: `git show auth-3.4.11:pdns/dbdnsseckeeper.cc` line 78 `bits = keyOrZone ? 2048 : 1024`; `auth-4.0.0` line 81 throws | PASS | PASS |
| 10 | 4.5.0 max-nsec3-iterations 500 to 100 (`5a5d565f0`) | PASS: `pdns/common_startup.cc`, `pdns/dbdnsseckeeper.cc` (plus docs, test) | PASS: `auth-4.5.0-alpha1` / `auth-4.5.0` (80 tags; ancestry 80/80) | PASS: `--grep 'lower max-nsec3'` finds only the master merge (`1fa649bb0`) | PASS: `common_startup.cc` `"500"` to `"100"`; presigned zones skipped | PASS (applies on upgrade) | PASS |
| 11 | 4.6.0 set-nsec3 `1 0 1 ab` to `1 0 0 -` (`6830fcce2`) | PASS: `pdns/pdnsutil.cc` (plus docs) | PASS: `auth-4.6.0-beta1` / `auth-4.6.0` (68 tags; ancestry 68/68) | PASS: `--grep 'new default nsec3param'` finds only the master merge (`c8f22c6c9`) | PASS: `pdnsutil.cc` 2988 to 3065 as above | PASS (opt-in) | PASS |

That is 66 sub-checks, 64 pass and 2 fail (rows 3 and 8, both in B4).

| # | extra B check | command | expected | observed | result |
|---|---|---|---|---|---|
| 12 | Completeness: other pre-release default changes | `git -C $G log --all -i --grep=ecdsa256 --format='%h %cI %s'` | every 4.0.0 default change is a row | `fae95f259` (2016-04-05) "make ecdsa256 the default algorithm for add-zone-key and generate-zone-key" (`pdnsutil.cc`: `int algorithm=8` to `13`, two sites) is missing | **FAIL** |
| 13 | Claim 1: no stable 3.x ecdsa256 default | scan of 20 stable `auth-3.*` tags (see Claim 1) | 0 hits | 0 hits | PASS |
| 14 | `tc` vs `merge-base` agree, `1fe96a070` | `git -C $G tag --contains 1fe96a070`, then the merge-base loop over 196 tags | same set | 141 = 141 | PASS |
| 15 | same, `5a5d565f0` | same | same set | 80 = 80 | PASS |
| 16 | same, `6830fcce2` | same | same set | 68 = 68 | PASS |
| 17 | same, `0ba8e0f16` | same | same set | 168 = 168 | PASS |
| 18 | same, `d33ba8ebf` | same | same set | 5 = 5 | PASS |
| 19 | same, `b3dec9c7e` | same | same set | 2 = 2 | PASS |
| 20 | Claim 2: 4.5.0 upgrade clamp | `git -C $G show auth-4.5.0:pdns/dbdnsseckeeper.cc \| sed -n 347,353p` | clamp on read | clamp on read, presigned skipped | PASS |
| 21 | Claim 2: 4.6.0 only pdnsutil consumer | `git -C $G grep -n -e '1 0 1 ab' -e '1 0 0 -' auth-4.6.0 -- pdns modules` | one site | `pdnsutil.cc:3065` only | PASS |
| 22 | pdnsutil.cc default 500 at 4.5.0 | `git -C $G show auth-4.5.0:pdns/pdnsutil.cc \| grep -n max-nsec3-iterations` | line 106 = "500" | line 106 = "500" | PASS |
| 23 | quote: 3.2 changelog | `git -C $G show auth-3.2-rc1:pdns/docs/pdns.xml \| grep -n 'add-zone-key now defaults'` | present | line 146 | PASS |
| 24 | quote: 4.0.0 changelog | `git -C $G show auth-4.0.9:docs/markdown/changelog.raw.md \| grep -n 'single 256 bit ECDSA'` | present | line 281 | PASS |
| 25 | quote: 4.5.0 upgrading.rst | `git -C $G show 5a5d565f0 -- docs/upgrading.rst` | 500 to 100 sentence | present | PASS |
| 26 | quote: 3.4.9 "coming in version 4.0.0" | `git -C $G grep -n 'coming in version 4.0.0' auth-4.0.9` | present | `changelog.raw.md:428` (in the 4.0.9 tree, section 3.4.9) | PASS |

Extras: 15 run, 14 pass, 1 fail. Section B totals: 81 run, 78 pass, 3 fail.

### C. CVE fixes (74 run, 73 pass, 1 fail)

C1 = present in `data/software/cve_inventory.json` under `by_product['pdns-auth']` or `fixes['pdns-auth']`. Inventory has 7 by_product rows and 22 fixes rows for pdns-auth. The 15 timeline rows are exactly the 7 by_product rows plus 8 fixes-only rows; `inventory_fixes_not_applicable` is 9 (14 CVEs). C2 = `tc` for every fix commit; `fix_tag` is the earliest stable tag across all sibling commits, by tag-commit time. C3 = latency recomputed as `date(fix_released) - date(nvd_published)`. C4 = `auth-` prefix.

| # | CVE | C1 | C2 (real `tc`; earliest stable across siblings) | C3 latency | C4 |
|---|---|---|---|---|---|
| 1 | CVE-2008-3337 | PASS by_product | PASS with caveat: `tc 8b1ed874b` first stable is `auth-3.0`, not `auth-2.9.22`. `auth-2.9.22` is a flat-layout SVN import, so ancestry fails; by content `git show auth-2.9.22:packethandler.cc` has the SERVFAIL reply (line 587) and `git show pdns-2.9.21:pdns/packethandler.cc` has "dropping" (line 579). Documented in the row. The real fix release, 2.9.21.1, has no tag; see the advisory under Correction 5 | 170 = 170 PASS | PASS (`auth-`, pre-split reason stated) |
| 2 | CVE-2012-0206 | PASS both | PASS: `a57d1591c` `auth-3.0.1` (2012-01-10 15:24Z), `6a90bacff` first stable `auth-3.1` | -38 = -38 | PASS |
| 3 | CVE-2016-6172 | PASS by_product | PASS: `db8f91521` `auth-4.0.1` (2016-07-29) is earlier than `a014f4c22` `auth-3.4.10` (2016-09-01) | -59 = -59 | PASS |
| 4 | CVE-2019-3871 | PASS by_product | PASS: `3c2f3a3b5` `auth-4.0.7` 09:21:09, `4f3c2b328` `auth-4.1.7` 09:21:15 | -3 = -3 | PASS |
| 5 | CVE-2019-10203 | PASS by_product | PASS: `6b48327a0` `auth-4.1.11` 16:42, `b2f3d1b69` `auth-4.0.9` 18:53 (same day 2019-07-30), `fbe76e78a` `auth-4.2.0` | -115 = -115 | PASS |
| 6 | CVE-2021-36754 | PASS by_product | PASS: `96cae2fd2` `auth-4.5.1`; nothing earlier | -8 = -8 | PASS |
| 7 | CVE-2022-27227 | PASS by_product | PASS: `89a28d75e` `auth-4.6.1` 11:38, `fae4de96c` `auth-4.5.4` 15:53, `57312d230` `auth-4.4.3` 16:23 (all 2022-03-16) | -9 = -9 | PASS |
| 8 | CVE-2015-1868 | PASS fixes-only (NVD product is pdns-rec) | PASS: 3 commits in `auth-3.4.4` (2015-04-23), backport `9df4944d8` `auth-3.3.2` (later) | -25 = -25 | PASS |
| 9 | CVE-2018-1046 | PASS fixes-only | PASS: `f9c57c98d` `auth-4.1.2` | n/a (NVD date null) | PASS |
| 10 | CVE-2026-33257 | PASS fixes-only | PASS: `6908f4581` `auth-4.9.14` 12:56:01, `9d5d9a3d4` `auth-5.0.4` 12:56:15 | 0 = 0 | PASS |
| 11 | CVE-2026-33260 | PASS fixes-only | PASS: `038e38a24` `auth-4.9.14`, `9e074364d` `auth-5.0.4` | 0 = 0 | PASS |
| 12 | CVE-2026-33608 | PASS fixes-only | PASS: `dc856d42b` `auth-4.9.14`, `9244f6aea` `auth-5.1.0` | n/a | PASS |
| 13 | CVE-2026-33609 | PASS fixes-only | PASS: `acab2df92` `auth-4.9.14`, `2a2d1b620` `auth-5.1.0` | n/a | PASS |
| 14 | CVE-2026-33610 | PASS fixes-only | PASS: `5d30353ea` `auth-4.9.14`, `6d3dd870e` `auth-5.1.0` | n/a | PASS |
| 15 | CVE-2026-33611 | PASS fixes-only | PASS: `1df83d797` `auth-4.9.14`, `e34973ea6` `auth-5.1.0` | n/a | PASS |

That is 60 sub-checks, all pass. Commands: `git -C $G tag --contains <c>` filtered to `^(auth|pdns)-` and sorted by `git -C $G log -1 --format=%cI <tag>^{commit}`; latency by Python `date.fromisoformat` subtraction. Row 1 (CVE-2008-3337) passes C2 only on the content check, which is a reproducible caveat rather than a clean membership result.

Disputed-tag proofs, each PASS (timeline right):

| # | CVE | command | observed | result |
|---|---|---|---|---|
| 16 | CVE-2012-0206 to `auth-3.0.1` | `git -C $G show auth-3.0:pdns/common_startup.cc \| grep -n 'P->d.qr'`, then the same with `auth-3.0.1` | absent in `auth-3.0`, line 258 in `auth-3.0.1`. Fix `a57d1591c` is in `auth-3.0.1` (2012-01-10). Inventory 3.3.1 is the next master release, and even master's `6a90bacff` first ships in `auth-3.1`, which precedes 3.3.1 | PASS |
| 17 | CVE-2019-3871 to `auth-4.0.7` | `git -C $G tag --contains 3c2f3a3b5`; `git -C $G show 3c2f3a3b5` (`modules/remotebackend/httpconnector.cc`: parse the URL at init); advisory `docs/security-advisories/powerdns-advisory-2019-03.rst` "Not affected: 4.1.7, 4.0.7", "Date: March 18th 2019" | first stable `auth-4.0.7` (09:21:09), `auth-4.1.7` six seconds later | PASS |
| 18 | CVE-2019-10203 to `auth-4.1.11` | `git -C $G tag --contains 6b48327a0`; `git -C $G show auth-4.1.11:modules/gpgsqlbackend/schema.pgsql.sql \| grep notified_serial` | `auth-4.1.11` has `BIGINT`; `auth-4.1.10` has `INT`. Same-day sibling `auth-4.0.9` (18:53). Advisory 2019-06 "Not affected: 4.2.0, 4.1.11, 4.0.9", dated 2019-07-30 | PASS |
| 19 | CVE-2022-27227 to `auth-4.6.1` | `git -C $G tag --contains 89a28d75e`; `git -C $G show auth-4.6.0:pdns/ixfr.cc` vs `auth-4.6.1` (`transferStyle`, `primarySOACount` present only from `auth-4.6.1`) | `auth-4.6.1` first by tag-commit time. `auth-4.5.4` and `auth-4.4.3` are the same day. All three carry the changelog date 25 March 2022 | PASS (see Correction 5) |
| 20 | CVE-2018-1046 to `auth-4.1.2` | `git -C $G show auth-4.1.1:pdns/dnsreplay.cc \| grep -c 'packetSize > \*len &&'`, then `auth-4.1.2` | 0 in `auth-4.1.1`, 1 in `auth-4.1.2`. Inventory 4.2.0 is the docs merge `caaa00dea` | PASS |

Claim 5, code path per fixes-only row (8 checks, all pass):

- `git -C $G show --name-only --format= <c> | grep -c recursordist` gives 0 for `2dea55e9c` (`pdns/dnsparser.cc`), `f9c57c98d` (`pdns/dnsreplay.cc`), `6908f4581` and `038e38a24` (`ext/yahttp`), `dc856d42b` (`modules/bindbackend`), `acab2df92` (`modules/ldapbackend`), `5d30353ea` (`pdns/rfc2136handler.cc`) and `1df83d797` (`pdns/dnswriter.cc`, `pdns/rcpgenerator.cc`).
- `git -C $G branch -a --contains <c>` shows `rel/auth-4.9.x` for the six 2026 commits.

Schema check:

| # | check | command | expected | observed | result |
|---|---|---|---|---|---|
| 21 | `cve_fixes[]` schema has `applicable` (per brief) | `python3 -c "..."` over `d['cve_fixes']` | key present | key absent in all 15 rows (`inventory_scope` and `note` carry the reason) | **FAIL** (minor) |

Section C totals: 74 run, 73 pass, 1 fail.

### D. Changelog entries (70 run, 61 pass, 9 fail)

Sample: `random.seed(20260929); random.sample(all (release, entry) pairs, 20)`. This gives 20 entries across 18 releases (script `/tmp/v_auth/D2.py`). Each entry has 3 checks: (a) present in `git -C $G show <changelog_source_tag>:<path>` after whitespace/markup normalisation; (b) not re-attributed, meaning absent from the previous stable tag's own changelog file, or, when the file is absent at the older tag (docs/changelog/*.rst are created retroactively), it occurs once in the file and sits under this release's section; (c) `mechanism` matches the text (no CDS-in-ECDSA false positive; all 10 `cds-cdnskey` entries contain CDNSKEY or CDS as a word).

| # | release | entry | a present | b not re-attributed | c mechanism | result |
|---|---|---|---|---|---|---|
| 1 | auth-2.9.22 | "DNSSEC records were part of 2.9.21..." | yes | yes (occ=1, `pdns-2.9.21` lacks it) | other | PASS |
| 2 | auth-3.1-rc1 | "Spotted & fixed by Jimmy Bergman... CNAMEs and RRSIGs" | yes | yes (absent at `auth-3.0.1`) | rrsig | PASS |
| 3 | auth-3.2-rc1 | #16 "DNSSEC changes in 3.2: Non-DNSSEC improvements/changes in 3.2: Assorted bugfixes:" | **NO** | n/a | other | **FAIL**: three section headings concatenated. `grep -n -F` finds them at `pdns.xml` lines 112, 219, 335 as separate headings, not an entry |
| 4 | auth-3.3.2 | "[commit bbc0bc5]..." | yes (`auth-4.0.9` md) | yes (occ=1, in section) | other | PASS |
| 5 | auth-3.4.0-rc1 | "Direct RRSIG queries now return NOTIMP." | yes | yes (absent at `auth-3.3.1`) | rrsig | PASS |
| 6 | auth-3.4.4 | "Released 23rd of April, 2015 **Warning**..." | yes | yes | other | PASS (prose preamble, not an item) |
| 7 | auth-4.0.0 | "[#3733]... ALI..." | yes | yes | other | PASS |
| 8 | auth-4.0.1 | "Released July 29th 2016 This release fixes two small issues..." | yes | yes (absent at `auth-4.0.0`) | other | PASS (prose preamble) |
| 9 | auth-4.0.5 | "#5722 Publish inactive KSK/CSK as CDNSKEY/CDS" | yes (`auth-5.1.4:docs/changelog/4.0.rst` line 77, under "Authoritative Server 4.0.5") | yes | cds-cdnskey (text says CDNSKEY/CDS) | PASS |
| 10 | auth-4.0.6 | "This release fixes PowerDNS Security Advisory 2018-03..." | yes | yes (absent at `auth-4.1.4`) | other | PASS |
| 11 | auth-4.1.0-rc2 | "Remove printing of DS records from pdnsutil export-zone-dnskey" | yes | yes (occ=1, in section) | ds-digest | PASS |
| 12 | auth-4.1.10 | "- PowerDNS Security Advisory 2019-05..." | yes | yes | other | PASS |
| 13 | auth-4.2.0-rc1 | "Improve RRset validation." | yes | yes | validation | PASS |
| 14 | auth-4.2.0-rc1 | "Error on DNSSEC default misconfiguration." | yes | yes | other | PASS |
| 15 | auth-4.2.0-rc1 | "Increase serial after DNSSEC related updates." | yes | yes | other | PASS |
| 16 | auth-4.2.0-rc2 | "disable dnssec pre-processing for non dnssec zones..." | yes | yes | other | PASS |
| 17 | auth-4.3.0-alpha1 | "API: optionally, do not return dnssec info in domain list" | yes | yes | other | PASS |
| 18 | auth-4.4.3 | "Fix validation of incremental zone transfers (IXFRs)." | yes | yes (absent at `auth-4.5.4`) | validation | PASS |
| 19 | auth-4.7.4 | "Pick the right signer name when a NSEC name is also a d..." | yes | yes | other | PASS |
| 20 | auth-4.8.4 | "ixfrdist: Fix the validation of 'max-soa-refresh'" | yes | yes (absent at `auth-4.8.3`) | validation | PASS |

That is 60 sub-checks, 59 pass and 1 fail.

`total_entries` recount, 10 releases sampled with the same seed (`random.sample` of releases that have entries). The recount is the number of `.. change::` blocks (rst) or bullet lines (md) in the release's section:

| # | release | JSON total_entries | recount | diff | result |
|---|---|---|---|---|---|
| 21 | auth-4.2.0-rc2 | 33 | 33 | 0% | PASS |
| 22 | auth-4.5.4 | 3 | 1 | +200% | FAIL |
| 23 | auth-4.1.0-rc2 | 23 | 20 | +15% | FAIL |
| 24 | auth-5.1.0 | 21 | 18 | +17% | FAIL |
| 25 | auth-4.4.0 | 16 | 5 | +220% | FAIL |
| 26 | auth-3.4.2 | 42 | 37 | +13.5% | FAIL |
| 27 | auth-4.3.0 | 7 | 4 | +75% | FAIL |
| 28 | auth-4.0.1 | 14 | 13 | +7.7% | PASS |
| 29 | auth-4.8.4 | 5 | 3 | +67% | FAIL |
| 30 | auth-4.1.14 | 2 | 1 | +100% | FAIL |

Cause: `total_entries` counts prose preamble paragraphs and bullets as well as change items. For 4.4.0, 5 changes + 3 intro paragraphs + 5 feature bullets + 3 closing paragraphs = 16. The systematic recount over all rst releases (`/tmp/v_auth/tot.py`) shows the same excess everywhere: `auth-4.5.0` 1 vs 16, `auth-4.7.0` 3 vs 17, `auth-4.6.0` 3 vs 11. Only sections without prose match (`auth-4.2.0-rc1/rc2`, `auth-4.1.4`, `auth-4.1.8`, `auth-4.2.2`).

Other D observations (not counted as fails):
- Nine releases (`auth-4.9.16/17`, `auth-5.0.6/7`, `auth-5.1.0..5.1.4`) use `changelog_source_tag: master`, a moving ref. The 5.1.0 entry "lmdb: yet another NSEC bug" exists at `git -C $G show master:docs/changelog/5.1.rst` line 170 (`master` = `080cdbd6a`, 2026-09-28) but not at `auth-5.1.4`. Pin it to the commit.
- Two of the sampled "entries" (`auth-3.4.4` #0 and `auth-4.0.1` #0) are release-intro paragraphs (dated preambles), not changelog items.

Section D totals: 70 run, 61 pass, 9 fail.

### E. Coverage and gaps (13 run, 11 pass, 2 fail)

| # | check | command | expected | observed | result |
|---|---|---|---|---|---|
| 1 | stable tag count | `git -C $G tag -l 'auth-*' 'pdns-*'`, filter `alpha\|beta\|rc\|dev` | `release_count` 196, stable 132 | clone 196 tags (175 `auth-`, 21 `pdns-`), 132 stable; JSON 196 / 132 | PASS |
| 2 | stable tag missing from `releases[]` | set difference of tags vs `releases[].tag` | empty | empty both ways | PASS |
| 3 | releases[] unchanged from previous commit | `git show HEAD~1:data/software/timelines/pdns-auth.json` vs HEAD, compare `releases` | identical | identical (196 releases with `changelog_entries`); only `gaps`, `cve_fixes`, `branch_note`, `sources`, `default_changes` differ | PASS |

Gap checks (each of the 10 `gaps[]` items):

| # | gap | finding | result |
|---|---|---|---|
| 4 | auth-3.4.10/11 no changelog section | `git -C $G grep -n -e 'Authoritative Server 3.4.10' auth-4.0.9 -- docs` finds nothing; later trees only mention them in advisories and secpoll | PASS (genuine) |
| 5 | news_edits not determined | "attempted... exceeded its time budget". That is a skip, not an undeterminable | **FAIL** |
| 6 | CVE-2008-3337, 2.9.21.1 untagged | genuinely untagged (`git -C $G tag -l '*2.9.21*'`). But the date is determinable and stated as -1 d, while the `pdns.sgml` text in `ef29748a9` says "Released on the 6th of August 2008" (-2 d). See Correction 5 | PASS (gap real) |
| 7 | CVE-2012-0206, 2.9.22.5 untagged | genuinely untagged; prep commits `19487457e`, `a2dda9a10` exist, no tag | PASS |
| 8 | CVE-2019-10203 schema-only | verified (row 18 above) | PASS |
| 9 | fixes-only CVEs and NVD dates missing | verified; NVD dates are not in the inventory (cannot be fetched offline) | PASS |
| 10 | unsurveyed defaults: RRSIG validity, signing-threads, default-soa-edit, dnssec-key-cache-ttl, direct-dnskey, API defaults | a skipped item. My spot survey of 13 tags (`auth-3.4.11`, 4.0.0, 4.1.0, 4.2.0, 4.3.0, 4.4.0, 4.5.0, 4.6.0, 4.7.0, 4.8.0, 4.9.0, 5.0.0, 5.1.0) found `signing-threads` "3", `default-soa-edit` "", `direct-dnskey` "no" and `dnssec-key-cache-ttl` "30" (new in 4.0.0) unchanged. `default-api-rectify` first appears in 4.2.0 as "yes" (introduction, not a change). No hidden default flip at those points | **FAIL** (skipped, low impact) |
| 11 | four 4.0.0 commits, no stable 3.x ecdsa256 | verified (Claim 1) | PASS |
| 12 | duplicate of item 4 | verified | PASS |
| 13 | changelog `is_default_change` entries left untouched | nothing found contradicting | PASS |

Section E totals: 13 run, 11 pass, 2 fail.

## Corrections required

1. **`default_changes[]`, row "3.3.2 add-superfluous-nsec3-for-old-bind" (`b3dec9c7e`), fields `after` and `scope`, and `.md` lines 30 and 47 plus the gaps text.**
   - Wrong: "the option itself was dropped in auth-3.4.0-rc2 (changelog gb50efd6)" and "master (3.4.0-rc1) still shipped =yes until the option was removed".
   - Right: master removed the option in `b50efd613` (2014-07-10, "don't add superfluous nsec3 for old bind", `pdns/common_startup.cc`, `pdns.conf-dist`, `packethandler.cc`). It is contained in `auth-3.4.0-rc1`, and `auth-3.4.0-rc1` has no such option in its code. The `gb50efd6` line is in the 3.4.0 changelog section, not an rc2 event. The default flip therefore shipped only on the 3.3.x branch (`auth-3.3.2`, `auth-3.3.3`, which still contain the option), and every 3.4.x and later release has no option at all.
   - Proof: `git -C $G merge-base --is-ancestor b50efd613 'auth-3.4.0-rc1^{commit}' && echo yes`; `git -C $G grep -c add-superfluous-nsec3-for-old-bind auth-3.3.3 -- pdns/common_startup.cc` gives 2; `git -C $G grep -n add-superfluous auth-3.4.0-rc1 -- pdns` shows only `pdns.xml` changelog hits and no code.
2. **`default_changes[]`, missing row (`fae95f259`), and row 4.0.0 net-effect (`1fe96a070`) `scope`.**
   - Add a row: pdnsutil add-zone-key and generate-zone-key default algorithm RSASHA256 (8) to ECDSAP256SHA256 (13) (`pdns/pdnsutil.cc`, two sites). Commit `fae95f259`, 2016-04-05T12:44:50+02:00, first tag `auth-4.0.0-alpha3`, first stable `auth-4.0.0`. `applies_on_upgrade=false`, `opt_in=false`, as for the sibling algorithm rows.
   - Fix `1fe96a070`'s `scope`, which says "secure-zone / add-zone-key". That commit changes only the `default-ksk-algorithms` and `default-zsk-algorithms` settings (secure-zone), not add-zone-key's literal default.
   - Proof: `git -C $G show --stat --format='%h %cI %s' fae95f259`; `git -C $G show auth-3.4.11:pdns/pdnssec.cc | grep -n 'int algorithm='` gives 8; `git -C $G show auth-4.0.0:pdns/pdnsutil.cc | grep -n 'int algorithm='` gives 13 at lines 2227 and 2692; `git -C $G tag --contains fae95f259` first stable is `auth-4.0.0`.
3. **`releases[].total_entries` (all releases with a changelog section).**
   - Wrong: it counts prose preamble paragraphs and bullets together with change items (auth-4.4.0: 16, auth-4.5.4: 3, auth-4.3.0: 7, auth-4.8.4: 5, auth-4.1.14: 2, auth-5.1.0: 21, auth-4.1.0-rc2: 23, auth-3.4.2: 42).
   - Right: the number of change items (5, 1, 4, 3, 1, 18, 20, 37), or rename the field and define it.
   - Proof: `python3 /tmp/v_auth/tot.py`, which recounts `.. change::` blocks per `:version:` section from `git -C $G show <changelog_source_tag>:<path>`. Example: `git -C $G show auth-5.1.4:docs/changelog/4.4.rst` section 4.4.0 has 5 `.. change::` blocks.
4. **`releases[auth-3.2-rc1].changelog_entries[16]`.** Delete it. Its text "DNSSEC changes in 3.2: Non-DNSSEC improvements/changes in 3.2: Assorted bugfixes:" is three section headings joined, not a changelog entry (`git -C $G show auth-3.2-rc1:pdns/docs/pdns.xml | grep -n -F -e 'DNSSEC changes in 3.2' -e 'Non-DNSSEC improvements/changes in 3.2' -e 'Assorted bugfixes:'` gives lines 112, 219, 335). Entry 15 ("This is a stability and confirmity update to 3.1...") and the `auth-3.4.4` / `auth-4.0.1` entry #0 are also intro paragraphs; consider dropping them.
5. **Fix-release dates for embargoed security releases (`cve_fixes[]`, advisory).**
   - `fix_released` is the tag-commit date. For coordinated-disclosure releases the public date is later, so `latency_days` is too negative:
     - CVE-2022-27227: `auth-4.6.1` tag commit 2022-03-16, public release and advisory 2022-03-25 (`git -C $G show auth-5.1.4:docs/security-advisories/powerdns-advisory-2022-01.rst`: "Date: 25th of March 2022", "Not affected: 4.4.3, 4.5.4, 4.6.1"). Latency is 0, not -9.
     - CVE-2021-36754: `auth-4.5.1` changelog and advisory 2021-01 give 2021-07-26, so latency is -4, not -8.
     - CVE-2008-3337: the actual fix release is the untagged 2.9.21.1 ("Released on the 6th of August 2008", `git -C $G show ef29748a9 -- pdns/docs/pdns.sgml`), so latency is -2, not +170. The gap text says -1; it should say -2.
   - Either annotate these rows or use the advisory date. The tag choice itself is unaffected: for the three same-day tags of CVE-2022-27227, all carry 2022-03-25 in the changelog.
6. **`cve_fixes[]` schema.** The `applicable` key required by the brief is absent from all 15 rows. Add it (true for all 15; the nine excluded inventory rows are recorded separately in `inventory_fixes_not_applicable`).
7. **Gaps that are skips.**
   - `news_edits` ("exceeded its time budget") should be computed or stated as not determinable with a reason.
   - "RRSIG validity period... defaults were NOT surveyed" is a skip. My 13-tag spot survey found no change in `signing-threads`, `default-soa-edit`, `direct-dnskey` or `dnssec-key-cache-ttl`; `default-api-rectify` (=yes) was introduced in 4.2.0. RRSIG validity (`signature-validity`) and NSEC/NSEC3 API defaults were not checked by me either.
8. **Reproducibility (advisory).** Nine releases use `changelog_source_tag: master`. Pin to a commit (`080cdbd6a` at time of check) or to `auth-5.1.4` once the section exists there.

Not corrections but recorded: `opt_in` semantics are inconsistent across rows (Claim 2 note); the `.md` and `.json` agree with each other on every row checked, so there is no md/json FAIL, but both carry the wrong "rc2" statement (Correction 1).

## Not verifiable

- NVD publication dates for CVE-2018-1046 and CVE-2026-33608..33611 are not in `cve_inventory.json`, so `latency_days` (null) could not be recomputed.
- The exact public release times of same-day tag pairs (CVE-2019-3871 `auth-4.0.7` vs `auth-4.1.7`, CVE-2019-10203 `auth-4.1.11` vs `auth-4.0.9`, CVE-2022-27227). Only tag-commit order is in the clone, so "earliest" is by commit time, and ties by calendar day are real.
- The 2026 advisory (2026-05) contents beyond the commits and the in-tree advisory file; no network access was used.
- Whether the changelog `:released:` dates are authoritative (for example 4.1.11 is "August 1st 2019" in the changelog but 2019-07-30 in the advisory and tag).

## Totals

| section | run | passed | failed |
|---|---|---|---|
| A. release dates / stable flags | 23 | 23 | 0 |
| B. default changes | 81 | 78 | 3 |
| C. CVE fixes | 74 | 73 | 1 |
| D. changelog entries | 70 | 61 | 9 |
| E. coverage and gaps | 13 | 11 | 2 |
| **total** | **261** | **246** | **15** |

Failures: B (3): row 3.3.2 B4, row `1fe96a070` B4, missing `fae95f259` row. C (1): `applicable` key absent. D (9): 3.2-rc1 junk entry, plus `total_entries` for 8 of 10 sampled releases. E (2): `news_edits` skip, unsurveyed-defaults skip.
