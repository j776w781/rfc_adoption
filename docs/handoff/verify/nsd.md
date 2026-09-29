# Phase 3 verification: nsd

**PASS WITH CORRECTIONS** — all 134 release dates, the tag inventory, 12 of 14 CVE rows and 5 of 7 default-change rows reproduce from the clone; the two SVN-era default-change rows (2.2.0, 2.3.0) carry a false attribution reason and a tag that does not contain its commit, one changelog entry is re-attributed from 3.2.x to 4.0.0, one `total_entries` is off by 33 %, and two gaps are determinable.

Inputs: `data/software/timelines/nsd.json` (generated 2026-09-28), `data/software/timelines/nsd.md`, clone `out/software_repos/nsd.git` (bare, blob-less). All commands below were run from the repo root with `C=out/software_repos/nsd.git`. Verified 2026-09-29.

Sampling: section A used `cut -f2 releases.tsv | shuf -n 20 --random-source=<(yes 20260929)`; section D used Python `random.seed(20260929); random.sample(pool, 20)` over the 252 kept `changelog_entries` (15 releases drawn).

## Checks

| section | row | command | expected | observed | result |
|---|---|---|---|---|---|
| A | all 134 tags | `for t in $(cut -f2 /tmp/nsd_rel.tsv); do git -C $C log -1 --format=%cI $t^{commit}; done` vs `released_full` and `git rev-parse $t^{commit}` vs `commit` | 134 equal dates and SHAs | 134/134 equal | PASS |
| A | migration-day trap | `git -C $C for-each-ref --format='%(refname:short) %(taggerdate:short)' refs/tags/NSD_*_REL` vs `released` | no `released` equal to a tagger day that is a migration day | 86 tags have tagger 2017-06-13 (SVN import); no `released` value is 2017-06-13; the 17 tags whose tagger day equals `released` are git-era tags cut minutes after the commit (4.1.19 .. 4.15.2) | PASS |
| A | stable flag rule | `awk -F'\t' '{pre=($2 ~ /ALPHA\|BETA\|RC\|B2\|_WS_/)?"False":"True"; if(pre!=$5)print}' /tmp/nsd_rel.tsv` | no mismatch | none; 130 `stable: true` match the 130 tags of form `NSD_x_y_z_REL`; 4 pre-releases (1_1_0B2, 1_3_0_ALPHA_1, 1_4_0_ALPHA_1, 2_0_0_WS) are `stable: false` | PASS |
| A | NSD_1_0_2_REL (first) | `git -C $C log -1 --format=%cI NSD_1_0_2_REL^{commit}` | 2002-10-14T13:12:16Z | 2002-10-14T13:12:16Z | PASS |
| A | NSD_4_15_2_REL (last) | `git -C $C log -1 --format=%cI NSD_4_15_2_REL^{commit}` | 2026-09-02T15:19:37+02:00 | 2026-09-02T15:19:37+02:00 | PASS |
| A | NSD_1_1_0_REL | `git -C $C log -1 --format=%cI NSD_1_1_0_REL^{commit}` | 2003-03-20T10:52:11Z | 2003-03-20T10:52:11Z (`date_reliability: suspect`, shares commit 49631c4d with NSD_1_1_0B2_REL) | PASS |
| A | NSD_1_2_0_REL | `git -C $C log -1 --format=%cI NSD_1_2_0_REL^{commit}` | 2003-07-09T10:44:07Z | 2003-07-09T10:44:07Z (suspect; shares 64ac9f41 with 1.2.1-1.2.4) | PASS |
| A | NSD_1_2_2_REL | `git -C $C log -1 --format=%cI NSD_1_2_2_REL^{commit}` | 2003-07-09T10:44:07Z | 2003-07-09T10:44:07Z (suspect) | PASS |
| A | NSD_1_2_3_REL | `git -C $C log -1 --format=%cI NSD_1_2_3_REL^{commit}` | 2003-07-09T10:44:07Z | 2003-07-09T10:44:07Z (suspect) | PASS |
| A | NSD_2_0_1_REL | `git -C $C log -1 --format=%cI NSD_2_0_1_REL^{commit}` | 2004-02-25T15:29:50Z | 2004-02-25T15:29:50Z (suspect) | PASS |
| A | NSD_2_1_1_REL | `git -C $C log -1 --format=%cI NSD_2_1_1_REL^{commit}` | 2004-06-30T10:51:20Z | 2004-06-30T10:51:20Z | PASS |
| A | NSD_2_3_1_REL | `git -C $C log -1 --format=%cI NSD_2_3_1_REL^{commit}` | 2005-08-30T09:23:08Z | 2005-08-30T09:23:08Z | PASS |
| A | NSD_2_3_7_REL | `git -C $C log -1 --format=%cI NSD_2_3_7_REL^{commit}` | 2007-04-13T12:27:12Z | 2007-04-13T12:27:12Z | PASS |
| A | NSD_3_0_1_REL | `git -C $C log -1 --format=%cI NSD_3_0_1_REL^{commit}` | 2006-09-06T09:03:19Z | 2006-09-06T09:03:19Z | PASS |
| A | NSD_3_0_3_REL | `git -C $C log -1 --format=%cI NSD_3_0_3_REL^{commit}` | 2006-12-07T13:01:33Z | 2006-12-07T13:01:33Z | PASS |
| A | NSD_3_0_5_REL | `git -C $C log -1 --format=%cI NSD_3_0_5_REL^{commit}` | 2007-06-26T09:19:30Z | 2007-06-26T09:19:30Z | PASS |
| A | NSD_3_0_7_REL | `git -C $C log -1 --format=%cI NSD_3_0_7_REL^{commit}` | 2007-11-13T14:27:18Z | 2007-11-13T14:27:18Z | PASS |
| A | NSD_3_0_8_REL | `git -C $C log -1 --format=%cI NSD_3_0_8_REL^{commit}` | 2008-04-18T08:39:45Z | 2008-04-18T08:39:45Z | PASS |
| A | NSD_3_1_0_REL | `git -C $C log -1 --format=%cI NSD_3_1_0_REL^{commit}` | 2008-06-23T09:28:11Z | 2008-06-23T09:28:11Z | PASS |
| A | NSD_3_2_2_REL | `git -C $C log -1 --format=%cI NSD_3_2_2_REL^{commit}` | 2009-05-13T14:33:36Z | 2009-05-13T14:33:36Z | PASS |
| A | NSD_3_2_10_REL | `git -C $C log -1 --format=%cI NSD_3_2_10_REL^{commit}` | 2012-02-09T09:48:43Z | 2012-02-09T09:48:43Z | PASS |
| A | NSD_3_2_12_REL | `git -C $C log -1 --format=%cI NSD_3_2_12_REL^{commit}` | 2012-07-09T08:23:34Z | 2012-07-09T08:23:34Z | PASS |
| A | NSD_3_2_14_REL | `git -C $C log -1 --format=%cI NSD_3_2_14_REL^{commit}` | 2012-10-24T07:44:26Z | 2012-10-24T07:44:26Z | PASS |
| A | NSD_4_12_0_REL | `git -C $C log -1 --format=%cI NSD_4_12_0_REL^{commit}` | 2025-04-24T10:20:47+02:00 | 2025-04-24T10:20:47+02:00 | PASS |
| A | NSD_4_15_1_REL | `git -C $C log -1 --format=%cI NSD_4_15_1_REL^{commit}` | 2026-08-26T10:56:21+02:00 | 2026-08-26T10:56:21+02:00 | PASS |
| B.1 | 2.0.0 / b2d80474 | `git -C $C show --stat b2d80474e18afe5af5e47ec159fc5d3c8f2977de` | product code / shipped config | `configure.ac` (+8/-9), `namedb.c` (+4) | PASS |
| B.1 | 2.0.0 / acb67945 | `git -C $C show --stat acb679450367a0e3df9d4c752d4f1e3b4dcd574c` | product code | answer.c, axfr.c, dbaccess.c, heap.h, namedb.c/.h, query.c, rbtree.c/.h | PASS |
| B.2 | 2.0.0 / NSD_2_0_0_REL | `git -C $C tag --contains b2d80474 \| grep -x NSD_2_0_0_REL; git -C $C tag --contains acb67945 \| grep -x NSD_2_0_0_REL` | both hit | both hit; acb67945 also in NSD_2_0_0_WS_REL (pre-release) | PASS |
| B.3 | 2.0.0 earliest tag | `git -C $C tag --contains b2d80474 \| grep -E '^NSD_[0-9]+_[0-9]+_[0-9]+_REL$' \| while read t; do echo "$(git -C $C log -1 --format=%cI $t^{commit}) $t"; done \| sort \| head -1` | NSD_2_0_0_REL | 2004-02-12 NSD_2_0_0_REL (acb67945: same) | PASS |
| B.4 | 2.0.0 before/after | `git -C $C show NSD_2_0_0_REL:configure.ac \| sed -n '333,340p'`; `git -C $C show NSD_2_0_0_REL:RELNOTES \| grep -n -A1 'disabled by'` | `case "$enable_dnssec" in no) ;; yes\|*) AC_DEFINE(DNSSEC)`; RELNOTES says disabled | exactly that at lines 333-340; RELNOTES l.6-7 "disabled by default. Enable using the --enable-dnssec"; conflict is recorded in the row and in gaps | PASS |
| B.5 | 2.0.0 flags | diff above | applies_on_upgrade true / opt_in false (configure default yes) | consistent with configure.ac; RELNOTES disagreement disclosed | PASS |
| B.6 | 2.0.0 attribution | JSON | `exact` | exact, commit reproduces | PASS |
| B.1 | 2.2.0 / fc944b1d | `git -C $C show --stat fc944b1d267453ca0ced7e01663e9e5d56c9d96f` | product config | RELNOTES (+4), configure.ac (+3/-3), query.c (+4); configure.ac hunk flips `no)`/`yes\|*)` to `yes)`/`no\|*)` | PASS |
| B.2 | 2.2.0 / NSD_2_2_0_REL | `git -C $C tag --contains fc944b1d \| grep -x NSD_2_2_0_REL` | hit | hit | PASS |
| B.3 | 2.2.0 earliest / siblings | `git -C $C log --all --format='%h %cI %s' --since=2004-05-01 --until=2005-02-01 -- configure.ac`; `git -C $C show 466770f2 -- configure.ac`; `git -C $C merge-base --is-ancestor 466770f2 dddc2ab8 && echo yes`; `git -C $C tag --contains 466770f2` | no earlier release carries the flip | non-merge commit **466770f2 2004-10-26 "Disable DNSSEC by default."** on `svn/nsd/branches/NSD_2_1@1312` makes the identical configure.ac change; it is an ancestor of the 2.1.4 release commit dddc2ab8 (2004-11-03, `AC_INIT(NSD,2.1.4)`) and of 2.1.5 (800998b0, 2004-11-24); no REL tag contains 466770f2 because NSD_2_1_4_REL/NSD_2_1_5_REL are manufactured on 4f99c245 (2004-06-22). Earliest *tag* is NSD_2_2_0_REL; earliest *release* is 2.1.4 | FAIL |
| B.4 | 2.2.0 before/after | `git -C $C show NSD_2_1_2_REL:configure.ac \| sed -n '333,340p'`; `git -C $C show NSD_2_2_0_REL:configure.ac \| sed -n '331,338p'` | 2.1.2: define unless `no`; 2.2.0: define only on `yes` | as stated, at the cited lines | PASS |
| B.5 | 2.2.0 flags | diff | applies_on_upgrade true, opt_in true | consistent (DNSSEC becomes --enable-dnssec opt-in) | PASS |
| B.6 | 2.2.0 attribution reason | JSON `attribution_reason`: "the flip is attributable only to the merge commit fc944b1d; no non-merge commit in NSD_2_1_0_REL..NSD_2_2_0_REL touches the dnssec block"; `documentation`: "the NSD_2_1 branch itself never changed the block" | reason must be true | false: 466770f2 is a non-merge commit on the NSD_2_1 branch that changed exactly this block two days before the merge (see B.3) | FAIL |
| B.1 | 2.3.0 / 9203aba7 | `git -C $C show --stat 9203aba7a5a411a08623795f5ee3320d7141713d`; `git -C $C show 9203aba7 -- configure.ac` | product config | README, RELNOTES, configure.ac (`--enable-dnssec` -> `--disable-dnssec`, define unless `no`), dns.h, query.c | PASS |
| B.2 | 2.3.0 / NSD_2_3_0_REL | `git -C $C tag --contains 9203aba7 \| grep -x NSD_2_3_0_REL` | hit | **no hit** (rc=1); `git -C $C show NSD_2_3_0_REL:configure.ac \| grep -n -A7 'AC_ARG_ENABLE(dnssec'` still shows the 2.2.0 opt-in block at l.331-338, and `NSD_2_3_0_REL:RELNOTES` has no 2.3.0 section | FAIL |
| B.3 | 2.3.0 earliest tag | earliest-tag loop over `git -C $C tag --contains 9203aba7`; `git -C $C log --all --format='%h %cI %s' -i --grep='2\.3\.0'` | tag = earliest stable tag containing | NSD_2_3_1_REL (2005-08-30) is the earliest tag; the 2.3.0 release commit is dc1c5047 "Updated for 2.3.0." 2005-05-02 (`svn/nsd/branches/NSD_2_2@1559`, contained in NSD_2_3_1_REL). Row `released: 2005-01-10` predates its own commit (2005-04-21) | FAIL |
| B.4 | 2.3.0 before/after | `git -C $C show NSD_2_2_0_REL:configure.ac \| sed -n '331,338p'`; `git -C $C show NSD_2_3_1_REL:configure.ac \| grep -n -A7 'AC_ARG_ENABLE(dnssec'`; `git -C $C show NSD_2_3_1_REL:RELNOTES \| grep -n -B2 -A1 'enabled by default'` | as row | 2.2.0 l.331-338 opt-in; 2.3.1 l.369-376 `--disable-dnssec` / define unless `no`; RELNOTES 2.3.0 l.18 "DNSSEC is now enabled by default. NSD should be fully compliant with RFC4033, RFC4034, and RFC4035." | PASS |
| B.5 | 2.3.0 flags | diff | applies_on_upgrade true, opt_in false | consistent | PASS |
| B.6 | 2.3.0 attribution | JSON | approximate with reason | reason stated and true (manufactured tag); but see B.2/B.3 | PASS |
| B.1 | 3.0.0 / 8b51cb2e | `git -C $C show --stat 8b51cb2ee94e8cb06071faa6bb56fc25d5305f12`; `git -C $C show 8b51cb2e -- query.c` | product code | doc/ChangeLog (+2), query.c: removes `#ifdef DNSSEC flags &= 0x0110U; /* Preserve the RD and CD flags */`, adds "CD flag must be cleared for auth answers" | PASS |
| B.2 | 3.0.0 / NSD_3_0_0_REL | `git -C $C tag --contains 8b51cb2e \| grep -x NSD_3_0_0_REL` | hit | hit | PASS |
| B.3 | 3.0.0 earliest / sibling | earliest-tag loop; `git -C $C show --stat e99b81ad; git -C $C tag --contains e99b81ad \| grep -E '_REL$'` | NSD_3_0_0_REL earliest | NSD_3_0_0_REL 2006-09-05; sibling e99b81ad (2.3 branch) first in NSD_2_3_6_REL 2006-09-29, later | PASS |
| B.4 | 3.0.0 before/after | diff above; `git -C $C show NSD_3_0_0_REL:doc/ChangeLog \| grep -n -A2 'CD flag SHOULD'` | readable | l.59-61 "Fixed RFC 4035 says CD flag SHOULD be cleared on authoritative reponses, now NSD clears the CD flag. This is bug #140." | PASS |
| B.5 | 3.0.0 flags | diff | applies_on_upgrade true, opt_in false | unconditional behaviour change | PASS |
| B.6 | 3.0.0 attribution | JSON | exact | exact | PASS |
| B.1 | 3.1.0 / e77877ae | `git -C $C show --stat e77877aec028dddb58ffc529744bf05d5cc84d82`; `git -C $C show e77877ae -- configure.ac` | product config | configure.ac (`--enable-nsec3` -> `--disable-nsec3`, define unless `no`), doc/ChangeLog, doc/README, tpkg moves | PASS |
| B.2 | 3.1.0 / NSD_3_1_0_REL | `git -C $C tag --contains e77877ae \| grep -x NSD_3_1_0_REL` | hit | hit; NSD_3_0_8_REL does not contain it (rc=1) | PASS |
| B.3 | 3.1.0 earliest / sibling | earliest-tag loop; `git -C $C log --all --format='%h %cI %s' -i --grep='nsec3 by default' --grep='enable-nsec3'` | NSD_3_1_0_REL | NSD_3_1_0_REL 2008-06-23; only e77877ae flips the default (e9743fda/4f15256b/0e440162 add the opt-in) | PASS |
| B.4 | 3.1.0 before/after | `git -C $C show NSD_3_0_8_REL:configure.ac \| grep -n -A8 'AC_ARG_ENABLE(nsec3'`; `git -C $C show NSD_3_1_0_REL:configure.ac \| sed -n '563,570p'`; `git -C $C show NSD_3_1_0_REL:doc/ChangeLog \| grep -n 'configure default is --enable-nsec3'` | as row | 3.0.8 l.558-565 define only on `yes`; 3.1.0 l.563-570 define unless `no`; ChangeLog l.42 | PASS |
| B.5 | 3.1.0 flags | diff | applies_on_upgrade true, opt_in false | consistent | PASS |
| B.6 | 3.1.0 attribution | JSON | exact | exact | PASS |
| B.1 | 3.2.6 / bcede5dc | `git -C $C show --stat bcede5dc3a9a4ee596f0362b12269bd61a8dcf87`; `git -C $C show bcede5dc -- configure.ac dbaccess.c` | product code | configure.ac (-9: whole dnssec block), dbaccess.c, difffile.c, zonec.c (`#ifdef DNSSEC` removed), doc/ChangeLog, doc/README | PASS |
| B.2 | 3.2.6 / NSD_3_2_6_REL | `git -C $C tag --contains bcede5dc \| grep -x NSD_3_2_6_REL` | hit | hit | PASS |
| B.3 | 3.2.6 earliest / sibling | earliest-tag loop; `git -C $C log --all --format='%h %cI %s' -i --grep='disable-dnssec'` | NSD_3_2_6_REL | NSD_3_2_6_REL 2010-07-20; single commit | PASS |
| B.4 | 3.2.6 before/after | `git -C $C show NSD_3_2_5_REL:configure.ac \| grep -n dnssec`; `git -C $C show NSD_3_2_6_REL:configure.ac \| grep -n -i dnssec`; `git -C $C show NSD_3_2_6_REL:doc/ChangeLog \| grep -n 'Removed --disable-nsid'` | option present at 3.2.5, absent at 3.2.6 | 3.2.5 l.567-568 has the option; 3.2.6 grep rc=1; ChangeLog l.19 | PASS |
| B.5 | 3.2.6 flags | diff | applies_on_upgrade true, opt_in false | consistent | PASS |
| B.6 | 3.2.6 attribution | JSON | exact | exact | PASS |
| B.1 | 3.2.9 / 05721207 | `git -C $C show --stat 057212075df7a580989ee9a81a1ec91685b6051b`; `git -C $C show 05721207 -- dbaccess.c difffile.c zonec.c` | product code | dbaccess.c, difffile.c (x2), zonec.c: `TYPE_SOA` -> `TYPE_DNSKEY` in `rr_rrsig_type_covered` tests; doc/ChangeLog, doc/RELNOTES | PASS |
| B.2 | 3.2.9 / NSD_3_2_9_REL | `git -C $C tag --contains 05721207 \| grep -x NSD_3_2_9_REL` | hit | hit; NSD_3_2_8_REL (2011-03-22) does not contain it | PASS |
| B.3 | 3.2.9 earliest / sibling | `git -C $C log --all --format='%h %cI %s' --grep='First step of bug #369'` + earliest-tag loop for each | NSD_3_2_9_REL | 05721207 -> NSD_3_2_9_REL 2011-11-02; sibling 2c9bddec (trunk, "svn:NO TEST") -> NSD_4_0_0_REL 2013-10-29 | PASS |
| B.4 | 3.2.9 before/after | diff above; `git -C $C show NSD_3_2_9_REL:doc/ChangeLog \| grep -n 'First step of bug #369'` | readable | diff shows SOA -> DNSKEY; ChangeLog l.67 | PASS |
| B.5 | 3.2.9 flags | diff | applies_on_upgrade true, opt_in false | consistent | PASS |
| B.6 | 3.2.9 attribution | JSON | exact | exact | PASS |
| C.1 | CVE-2009-1755 inventory | `python3 -c "..."` over `data/software/cve_inventory.json` `by_product.nsd` | present | present, published 2009-05-22 | PASS |
| C.2 | CVE-2009-1755 / b738d161 | `git -C $C tag --contains b738d1616aa9eb0c34a237248ed772b7601f9e7b \| grep -x NSD_3_2_2_REL` + earliest-tag loop; `git -C $C log --all -i --fixed-strings --grep='off-by-one' --format='%h %cI %s'` | in NSD_3_2_2_REL, earliest | hit; earliest NSD_3_2_2_REL 2009-05-13; siblings 903f5c5b/1275d19b are test additions 2009-05-11 | PASS |
| C.3 | CVE-2009-1755 latency | 2009-05-13 − 2009-05-22 | -9 | -9 | PASS |
| C.1 | CVE-2012-2978 inventory | as above | present | present, 2012-07-27 | PASS |
| C.2 | CVE-2012-2978 / 79354722 | `git -C $C tag --contains 793547222d9e5df4719b5f351655f3278719c850 \| grep -x NSD_3_2_13_REL`; `for t in NSD_3_2_12_REL NSD_3_2_13_REL; do git -C $C show $t:doc/ChangeLog \| grep -n CVE-2012-2978; done` | in NSD_3_2_13_REL, earliest | hit (commit is the tag commit); 3.2.12 ChangeLog has no CVE line, 3.2.13 l.2 "Fix for VU#624931 CVE-2012-2978"; earliest NSD_3_2_13_REL 2012-07-19 | PASS |
| C.3 | CVE-2012-2978 latency | 2012-07-19 − 2012-07-27 | -8 | -8 | PASS |
| C.1 | CVE-2013-5661 inventory | as above | present | present, 2019-11-05 | PASS |
| C.2 | CVE-2013-5661 / fecd050a, 029d25dd | `git -C $C tag --contains fecd050ac334287fb60d2d9ac2a7ffa7c5aa9f15` / `029d25ddfc5f5f3e3ac28285b5f10a5bf761fb43` + earliest-tag loop; `git -C $C log --all -i --fixed-strings --grep='CVE-2013-5661'` | `first_tag` values right; fix_tag null justified | fecd050a earliest NSD_3_2_16_REL 2013-07-09; 029d25dd earliest NSD_4_0_0_REL 2013-10-29 (matches `first_tag`); no commit names the CVE; null fix_tag with stated reason | PASS |
| C.3 | CVE-2013-5661 latency | null | null | null (no fix_tag) | PASS |
| C.1 | CVE-2016-6173 inventory | as above | present | by_product and fixes (7fc93931, 4.1.11) | PASS |
| C.2 | CVE-2016-6173 / 7fc93931 | `git -C $C tag --contains 7fc93931a845950eeeba18c5f3e036a13a091df2 \| grep -x NSD_4_1_11_REL`; `git -C $C log --all -i --fixed-strings --grep='#790'`; earliest-tag loop for a2828a75 | in NSD_4_1_11_REL, earliest | hit; sibling a2828a75 (2016-07-05, the size-limit-xfr code change) also earliest NSD_4_1_11_REL 2016-08-01; NSD_3_2_22_REL (2016-06-07) predates both | PASS |
| C.3 | CVE-2016-6173 latency | 2016-08-01 − 2017-02-09 | -192 | -192 | PASS |
| C.1 | CVE-2019-13207 inventory | as above | in `fixes.nsd` with reason for not in by_product | in fixes (91102da2, 4.2.2), not in by_product; row says so | PASS |
| C.2 | CVE-2019-13207 / 91102da2 | `git -C $C tag --contains 91102da24d5949ccfec8fdab5bae2d01c4cabab5 \| grep -x NSD_4_2_2_REL`; `git -C $C log --all -i --fixed-strings --grep='CVE-2019-13207'` | in NSD_4_2_2_REL, earliest | hit; earliest NSD_4_2_2_REL 2019-08-13; only other hit is 58ed7127 (2026, "incomplete fix" follow-up, in 4.15.0) as the row notes | PASS |
| C.3 | CVE-2019-13207 latency | NVD API `https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2019-13207` -> published 2019-07-03T20:15:11; 2019-08-13 − 2019-07-03 | 41 | JSON null (inventory has no date) — the date is public and took one request | FAIL |
| C.1 | CVE-2020-28935 inventory | as above; crossref `published` | in fixes; date from crossref 2020-12-07 | in fixes (a4caec31, 4.3.4); crossref published 2020-12-07 | PASS |
| C.2 | CVE-2020-28935 / a4caec31 | `git -C $C tag --contains a4caec3137a1bc9eca05d38d66e2bce572ca9bd3 \| grep -x NSD_4_3_4_REL`; grep siblings | in NSD_4_3_4_REL, earliest | hit; earliest NSD_4_3_4_REL 2020-11-24; single commit | PASS |
| C.3 | CVE-2020-28935 latency | 2020-11-24 − 2020-12-07 | -13 | -13 | PASS |
| C.1 | CVE-2026-12244 inventory | as above | present | present, 2026-06-25 | PASS |
| C.2 | CVE-2026-12244 / 289d78b3 | `git -C $C tag --contains 289d78b36628cfdeed42debd718bbe33e3ef575a \| grep -x NSD_4_14_3_REL`; `git -C $C log --all -i --fixed-strings --grep='svcb_rdata'` | in NSD_4_14_3_REL, earliest | hit; earliest NSD_4_14_3_REL 2026-06-24; sibling a98226c8 is the test case | PASS |
| C.3 | CVE-2026-12244 latency | 2026-06-24 − 2026-06-25 | -1 | -1 | PASS |
| C.1 | CVE-2026-12245 inventory | as above | present | present, 2026-06-25 | PASS |
| C.2 | CVE-2026-12245 / 188cb02b | `git -C $C tag --contains 188cb02ba17cef96c7799ab07c34fb8c23ae1b54 \| grep -x NSD_4_14_3_REL`; grep 'early close' | in NSD_4_14_3_REL, earliest | hit; earliest NSD_4_14_3_REL; single commit | PASS |
| C.3 | CVE-2026-12245 latency | −1 | -1 | -1 | PASS |
| C.1 | CVE-2026-12246 inventory | as above | present | present | PASS |
| C.2 | CVE-2026-12246 / 42c30338 | `git -C $C tag --contains 42c30338e8d835b07ab20e374f8583547a03687f \| grep -x NSD_4_14_3_REL`; grep 'malformed APL' | in NSD_4_14_3_REL, earliest | hit; earliest NSD_4_14_3_REL; d8c0074b is the test | PASS |
| C.3 | CVE-2026-12246 latency | −1 | -1 | -1 | PASS |
| C.1 | CVE-2026-12490 inventory | as above | present | present | PASS |
| C.2 | CVE-2026-12490 / 790530f2 | `git -C $C tag --contains 790530f29d301ffedc5314604135e5211ae4eff4 \| grep -x NSD_4_14_3_REL`; grep 'client cert' | in NSD_4_14_3_REL, earliest | hit; earliest NSD_4_14_3_REL; 88d35e0c/867191a9 (2026-08-28) are later follow-ups | PASS |
| C.3 | CVE-2026-12490 latency | −1 | -1 | -1 | PASS |
| C.1 | CVE-2026-18664 inventory | as above | present; inventory fix sha 19260dda | by_product + fixes; `git -C $C log -1 --format='%H %cI %P %s' 19260dda` = merge of NSD_4_15_1_REL into release-4.15.2, only in NSD_4_15_2_REL — row's note is right | PASS |
| C.2 | CVE-2026-18664 / 11a14bf2 | `git -C $C tag --contains 11a14bf210cbae23e1472440de4b5306b36ad83a \| grep -x NSD_4_15_1_REL`; grep 'endiannes' | in NSD_4_15_1_REL, earliest | hit; earliest NSD_4_15_1_REL 2026-08-26 (4.15.2 is 2026-09-02) | PASS |
| C.3 | CVE-2026-18664 latency | 2026-08-26 − 2026-08-26 | 0 | 0 | PASS |
| C.1 | CVE-2026-18916 inventory | as above | present | as 18664 | PASS |
| C.2 | CVE-2026-18916 / 51cc8141 | `git -C $C tag --contains 51cc81418edab6b3307adff4e3903c75c14a14af \| grep -x NSD_4_15_1_REL`; grep 'short writev' | in NSD_4_15_1_REL, earliest | hit; earliest NSD_4_15_1_REL | PASS |
| C.3 | CVE-2026-18916 latency | 0 | 0 | 0 | PASS |
| C.1 | CVE-2026-19401 inventory | as above | present | as 18664 | PASS |
| C.2 | CVE-2026-19401 / bab481d3 | `git -C $C tag --contains bab481d3b771205361b2cfa535d2cb20085c2c41 \| grep -x NSD_4_15_1_REL`; grep 'multiple EDNS cookie' | in NSD_4_15_1_REL, earliest | hit; earliest NSD_4_15_1_REL | PASS |
| C.3 | CVE-2026-19401 latency | 0 | 0 | 0 | PASS |
| C.1 | CVE-2026-19538 inventory | as above | present | as 18664 | PASS |
| C.2 | CVE-2026-19538 / fe6c25b4 | `git -C $C tag --contains fe6c25b4dea44c3cd9c57ebeb63b4a8e664ca4f1 \| grep -x NSD_4_15_1_REL`; grep 'proxy status' | in NSD_4_15_1_REL, earliest | hit; earliest NSD_4_15_1_REL | PASS |
| C.3 | CVE-2026-19538 latency | 0 | 0 | 0 | PASS |
| D.1-3 | NSD_2_0_0_REL #0 "Experimental DNSSEC support implemented, but disabled by" | `git -C $C show NSD_2_0_0_REL:RELNOTES \| grep -F 'Experimental DNSSEC support implemented, but disabled by'`; same at NSD_2_0_0_WS_REL and NSD_1_2_4_REL | present / absent / rrsig | present l.6; absent at both; mechanism rrsig fits | PASS |
| D.4 | NSD_2_0_0_REL total | Python parse of the `2.0.0` section of `NSD_2_0_0_REL:RELNOTES` (`^\s+- ` bullets) | 6 | 6 | PASS |
| D.1-3 | NSD_3_0_0_REL #2 "NSEC3 made it so it can handle the case where the NSEC3 RRSET" | `git -C $C show NSD_3_0_0_REL:doc/ChangeLog \| grep -F '<line>'`; NSD_2_3_5_REL has no doc/ChangeLog | present / n.a. / nsec3 | present; no previous ChangeLog; nsec3 | PASS |
| D.1-3 | NSD_3_0_0_REL #22 "tsig signing works for all queries. SOA queries, ..." | as above | present / other (TSIG) | present; other, note "TSIG, not DNSSEC" | PASS |
| D.4 | NSD_3_0_0_REL total | `git -C $C show NSD_3_0_0_REL:doc/ChangeLog \| grep -c $'^\t- '` | 548 | 548 | PASS |
| D.1-3 | NSD_3_0_2_REL #0 "no queries for NSEC3, RRSIG, ANY succeed for nsec3 only domains." | grep -F at NSD_3_0_2_REL / NSD_3_0_1_REL | present / absent / nsec3 | present / absent / nsec3 | PASS |
| D.4 | NSD_3_0_2_REL total | entries in NSD_3_0_2_REL:doc/ChangeLog not in NSD_3_0_1_REL | 37 | 37 | PASS |
| D.1-3 | NSD_3_0_5_REL #8 "added tpkg in manual to test parent side DS answers." | grep -F at NSD_3_0_5_REL / NSD_3_0_4_REL | present / absent / other | present / absent / other (test-only line) | PASS |
| D.1-3 | NSD_3_0_5_REL #13 "Added jumpstart for nsec3 search, will greatly speed up optout" | as above | present / absent / nsec3 | present / absent / nsec3 | PASS |
| D.4 | NSD_3_0_5_REL total | `git -C $C diff NSD_3_0_4_REL NSD_3_0_5_REL -- doc/ChangeLog \| grep -c $'^+\t- '`; also `grep -c $'^\t- '` on each file (681 − 649) | 48 | **32** (33 % off; no sub-bullets added: `grep -cE $'^\\+\t +- '` = 0) | FAIL |
| D.1-3 | NSD_3_1_1_REL #0 "Fixed NSEC3 memory leak in the case NSEC3 is not needed." | grep -F at NSD_3_1_1_REL / NSD_3_1_0_REL | present / absent / nsec3 | present / absent / nsec3 | PASS |
| D.4 | NSD_3_1_1_REL total | set difference vs NSD_3_1_0_REL | 7 | 7 | PASS |
| D.1-3 | NSD_3_2_1_REL #0 "Replace SHA256_DIGEST_LENGTH with nicer HAVE_EVP_SHA256" | grep -F at NSD_3_2_1_REL / NSD_3_2_0_REL | present / absent / other | present / absent / other (keyword false positive, noted) | PASS |
| D.4 | NSD_3_2_1_REL total | set difference vs NSD_3_2_0_REL | 13 | 13 | PASS |
| D.1-3 | NSD_3_2_9_REL #3 "First step of bug #369: RRSIG DNSKEY sets zone to be treated DNSSEC." | grep -F at NSD_3_2_9_REL / NSD_3_2_8_REL | present / absent / rrsig | present / absent / rrsig | PASS |
| D.4 | NSD_3_2_9_REL total | set difference vs NSD_3_2_8_REL | 26 | 26 | PASS |
| D.1-3 | NSD_3_2_15_REL #1 "Fix for --disable-full-prehash, where NSEC3s can be illegaly" | grep -F at NSD_3_2_15_REL / NSD_3_2_14_REL | present / absent / nsec3 | present / absent / nsec3 | PASS |
| D.4 | NSD_3_2_15_REL total | set difference vs NSD_3_2_14_REL | 28 | 28 | PASS |
| D.1-3 | NSD_3_2_17_REL #0 "Bugfix #542: Match RRSIG TTL with SOA TTL in negative response." | grep -F at NSD_3_2_17_REL / NSD_3_2_16_REL / NSD_4_0_0_REL | present / absent / rrsig | present; absent at 3.2.16 and at 4.0.0 (previous by date); rrsig | PASS |
| D.4 | NSD_3_2_17_REL total | set difference vs NSD_3_2_16_REL | 19 | 19 | PASS |
| D.1-3 | NSD_3_2_19_REL #0 "hmac sha224, sha384 and sha512 support, patch from David Gwynne." | grep -F at NSD_3_2_19_REL / NSD_3_2_18_REL / NSD_4_1_2_REL | present / absent / other | present; absent at both; other (TSIG) | PASS |
| D.1-3 | NSD_3_2_19_REL #1 "RFC 7344: CDS and CDNSKEY (read in)." | grep -F at NSD_3_2_19_REL / NSD_3_2_18_REL / NSD_4_1_2_REL | present / absent on branch / cds-cdnskey | present; absent at 3.2.18 (branch predecessor); **present at NSD_4_1_2_REL** (previous stable by date) — a 3.2 backport, disclosed in the row note ("first shipped in 4.1.1") and listed twice in the md; genuine CDS/CDNSKEY text, not the ECDSA substring | PASS (note) |
| D.4 | NSD_3_2_19_REL total | set difference vs NSD_3_2_18_REL | 15 | 15 | PASS |
| D.1-3 | NSD_3_2_20_REL #2 "RFC7553 RR Type URI support." | grep -F at NSD_3_2_20_REL / NSD_3_2_19_REL / NSD_4_1_6_REL | present / absent on branch / other | present; absent at 3.2.19; present at 4.1.6 (backport; keyword false positive, noted as not DNSSEC) | PASS (note) |
| D.4 | NSD_3_2_20_REL total | set difference vs NSD_3_2_19_REL | 13 | 13 | PASS |
| D.1-3 | NSD_4_0_0_REL #12 "Don't return SERVFAIL on a domain that looks like a NSEC3" | `git -C $C show NSD_3_2_15_REL:doc/ChangeLog \| grep -n -B2 -A1 "Don't return SERVFAIL on a domain that looks like a NSEC3"` | absent at previous tag | **present at NSD_3_2_15_REL l.202** (and at NSD_3_2_16_REL) under "26 September 2011: Matthijs"; 4.0.0 re-wraps it under "26 September 2011: (Matthijs, from NSD3_2 branch)" so the exact-string diff missed it. Commit e634cfff 2011-09-26 shipped in NSD_3_2_9_REL (2011-11-02) | FAIL |
| D.1-3 | NSD_4_0_0_REL #14 "Unit test nsec3 salt change and fix for sanity check of nsec3 chain." | grep -F at NSD_4_0_0_REL / NSD_3_2_15_REL / NSD_3_2_16_REL | present / absent / nsec3 | present; absent at both; nsec3 | PASS |
| D.1-3 | NSD_4_0_0_REL #16 "unit test for salt change, rehash in udb fix, remove last NSEC3" | as above | present / absent / nsec3 | present; absent at both; nsec3 | PASS |
| D.4 | NSD_4_0_0_REL total | set difference vs NSD_3_2_15_REL (vs NSD_3_2_16_REL) | 311 | 304 (291 vs 3.2.16), 2 % (6 %) | PASS |
| D.1-3 | NSD_4_1_6_REL #0 "makedist.sh print on pgp signature creation." | grep -F at NSD_4_1_6_REL / NSD_4_1_5_REL | present / absent / other | present / absent / other (false positive, noted) | PASS |
| D.4 | NSD_4_1_6_REL total | set difference vs NSD_4_1_5_REL | 14 | 14 | PASS |
| D.1-3 | NSD_4_1_18_REL #0 "Fix crash for DS query when parent and child zones both configured" | grep -F at NSD_4_1_18_REL / NSD_4_1_17_REL | present / absent / other | present / absent / other | PASS |
| D.4 | NSD_4_1_18_REL total | set difference vs NSD_4_1_17_REL | 22 | 22 | PASS |
| D.1-3 | NSD_4_3_4_REL #1 "Fix to add missing closest encloser NSEC3 for wildcard nodata type" | grep -F at NSD_4_3_4_REL / NSD_4_3_3_REL | present / absent / nsec3 | present / absent / nsec3 | PASS |
| D.4 | NSD_4_3_4_REL total | set difference vs NSD_4_3_3_REL | 19 | 19 | PASS |
| E.1 | stable tag count | `git -C $C tag \| grep -cE '^NSD_[0-9]+_[0-9]+_[0-9]+_REL$'`; `git -C $C tag \| grep -cE '^NSD_.*_REL$'` | 130 stable, 134 total = `release_count` | 130 stable; 134 NSD `_REL` tags (a 135th, `CREDNS_0_2_10_REL`, is not NSD); JSON 130 stable / 134 releases | PASS |
| E.2 | tags absent from releases[] | `diff <(git -C $C tag \| grep -E '^NSD_.*_REL$' \| sort) <(cut -f2 /tmp/nsd_rel.tsv \| sort)` | empty | empty | PASS |
| E.3 | gap 1 (no signing defaults) | read | undeterminable by nature | true statement of scope | PASS |
| E.3 | gap 2 (algorithm mnemonics) | `git -C $C log --all -i --grep=gost --grep=rsasha --format=%h` | no hits, as claimed | no hits | PASS |
| E.3 | gap 3 (no NSEC3 iteration cap) | `git -C $C grep -n -i iterations NSD_4_15_2_REL -- nsec3.c` | only an assert | l.127 `assert(iterations <= 65536)` style check only | PASS |
| E.3 | gap 4 (manufactured 1.x/2.x tags; "real release dates are not recoverable from the clone") | `git -C $C log --all --format='%h %cI %s' --since=2002-09-01 --until=2005-06-01 -i --grep='updated for' --grep='release'`; `git -C $C show <sha> -- configure.ac \| grep '^+AC_INIT'` | not determinable | **determinable**: the SVN branches carry the release commits — 1.1.0 c38bfa54 2003-06-16; 1.2.0 81ac7ce1 2003-07-07; 1.2.1 607f0a1b 2003-07-16; 1.2.2 73240a4a 2003-07-28; 1.2.3 d0f062f8 2003-11-14 (`AC_INIT(NSD,1.2.3)`); 1.2.4 6393ba53 2004-01-07 (`AC_INIT 1.2.4`); 2.0.1 3dd6bb09 2004-03-15 (`AC_INIT 2.0.1`); 2.0.2 2547f749 2004-03-25 (`AC_INIT 2.0.2`); 2.1.3 96b9b424 2004-10-20 (`AC_INIT 2.1.3`); 2.1.4 dddc2ab8 2004-11-03 (`AC_INIT 2.1.4`); 2.1.5 800998b0 2004-11-24 (`AC_INIT 2.1.5`); 2.2.1 3ce6699a 2005-02-21; 2.3.0 dc1c5047 2005-05-02; 1.0.3 e3cdb3ee 2003-06-02 ("Updated version number to 1.0.3.", `git -C $C log --all -i --grep='1\.0\.3' --format='%h %cI %s'`) — eight months after its tag date 2002-09-26. Only 1.1.0b2 has none. These differ from the tag dates by up to six months (1.2.4: 2004-01-07 vs 2003-07-09; 2.1.5: 2004-11-24 vs 2004-06-22; 2.3.0: 2005-05-02 vs 2005-01-10) | FAIL |
| E.3 | gap 4 count ("13 of the 1.x/2.x tags") vs data | `python3 -c` count of `date_reliability == "suspect"` | 13 | **15** (the list in the same sentence enumerates 15); `branch_note` also says 13; nsd.md header says 15 and its Gaps section says 13 | FAIL (md/json consistency) |
| E.3 | gap 5 (2.0.x RELNOTES vs configure.ac) | B.4 rows above | undeterminable which binary packagers shipped | true; but "Trunk flipped the default to off in merge fc944b1d" omits 466770f2 (B.3) | PASS |
| E.3 | gap 6 (2.3.0 tag lacks its commit) | B.2 row | true | true | PASS |
| E.3 | gap 7 (3.0.0 ChangeLog holds whole 3.0 history) | D.4 NSD_3_0_0_REL | 548 entries, none attributable to one cycle | 548 confirmed | PASS |
| E.3 | gap 8 (SVN tags not ancestors) | `git -C $C merge-base --is-ancestor NSD_3_2_8_REL NSD_3_2_9_REL; echo $?` | 1 | 1 | PASS |
| E.3 | gap 9 (3.2.x/4.x parallel, re-listed entries) | D rows 3.2.19 / 3.2.20 / 4.0.0 | true | true, but the 4.0.0 #12 entry shows the re-listing detection missed re-wrapped lines (D FAIL above) | PASS |
| E.3 | gap 10 (CVE-2013-5661 no commit; CVE-2019-13207 NVD date absent; CVE-2009-1755 names 2.3.7) | C rows; NVD API | undeterminable | CVE-2013-5661 and 2.3.7 parts true; **CVE-2019-13207 NVD date is 2019-07-03** (one API call) | FAIL |
| E.3 | gap 11 (inventory attributes 2026-08 CVEs to 4.15.2 merge) | C.1 CVE-2026-18664 | true | true; 19260dda is only in NSD_4_15_2_REL, fixes are in NSD_4_15_1_REL | PASS |
| E.3 | gap 12 (keyword false positives kept) | D rows 3.2.1 #0, 3.2.20 #2, 4.1.6 #0 | noted rows | all three carry the "not DNSSEC (keyword match only)" note | PASS |
| E.3 | gap 13 (auto commit attribution for kind=other) | D row 4.0.0 #12 `evidence.commits[0].lookup` | disclosed | disclosed ("auto (message = changelog line, +-10 days of header date)") | PASS |
| md/json | default_changes, cve_fixes, release list | manual comparison of the three md tables against the JSON arrays | equal | equal for all 7 default rows, 14 CVE rows, 134 release rows; only the 13/15 count differs (row above) | PASS |

## Corrections required

1. **`default_changes[1]` (2.2.0) — `commits`, `attribution`, `attribution_reason`, `documentation`.**
   Wrong: commits = [fc944b1d] only; attribution "approximate"; reason "no non-merge commit in NSD_2_1_0_REL..NSD_2_2_0_REL touches the dnssec block"; documentation "the NSD_2_1 branch itself never changed the block".
   Right: the flip is non-merge commit `466770f2a98d7f7513e22e8b86d6aa2458689eea` (2004-10-26, "Disable DNSSEC by default.", `svn/nsd/branches/NSD_2_1@1312`), carried to trunk by fc944b1d two days later; attribution "exact" for the commit, with a note that no REL tag contains 466770f2 and that the first release to ship it was 2.1.4 (release commit dddc2ab8, 2004-11-03) whose clone tag NSD_2_1_4_REL is manufactured on an older commit. Keep `tag: NSD_2_2_0_REL` only if the row states it is the earliest *tag*, not the earliest release.
   Proof: `git -C $C show 466770f2 -- configure.ac` (identical hunk to fc944b1d); `git -C $C merge-base --is-ancestor 466770f2 dddc2ab8 && echo yes`; `git -C $C show dddc2ab8 -- configure.ac | grep '^+AC_INIT'` -> `AC_INIT(NSD,2.1.4,...)`; `git -C $C tag --contains 466770f2 | grep -c _REL` -> 0.

2. **`default_changes[2]` (2.3.0) — `tag`, `released`, `commits[0].tag_contains_confirmed`.**
   Wrong: tag NSD_2_3_0_REL, released 2005-01-10 (a manufactured-tag date three months before the commit 9203aba7 of 2005-04-21).
   Right: either tag NSD_2_3_1_REL / released 2005-08-30 (earliest tag containing 9203aba7, as `first_tag` already says), or keep version 2.3.0 with `released` set from the 2.3.0 release commit dc1c5047 = 2005-05-02 and `date_reliability: release-commit`. The md "Default changes" table must follow.
   Proof: `git -C $C tag --contains 9203aba7 | grep -x NSD_2_3_0_REL; echo $?` -> 1; `git -C $C log -1 --format='%cI %s' dc1c5047` -> `2005-05-02T11:49:23Z Updated for 2.3.0.`; `git -C $C tag --contains dc1c5047 | grep -E '^NSD_' | head -1` -> NSD_2_3_1_REL.

3. **`cve_fixes[4]` (CVE-2019-13207) — `nvd_published`, `latency_days`.**
   Wrong: null / null. Right: 2019-07-03 / 41 (2019-08-13 − 2019-07-03). The inventory row should be updated in the same pass since the timeline sources it from there.
   Proof: `curl -s 'https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2019-13207' | python3 -c "import json,sys;print(json.load(sys.stdin)['vulnerabilities'][0]['cve']['published'])"` -> `2019-07-03T20:15:11.823`.

4. **`releases[NSD_4_0_0_REL].changelog_entries[12]`** ("Don't return SERVFAIL on a domain that looks like a NSEC3 domain but is actually a empty non-terminal.") — remove from 4.0.0 or mark as a 3.2.x re-listing. It is present in NSD_3_2_15_REL:doc/ChangeLog l.202 (line-wrapped differently) and its commit e634cfff shipped in NSD_3_2_9_REL (2011-11-02). The builder's exact-string diff should compare whitespace-normalised entry text; the 4.0.0 recount (304 vs 311) suggests a handful of other re-wrapped 3.2.x lines are counted as new in 4.0.0.
   Proof: `git -C $C show NSD_3_2_15_REL:doc/ChangeLog | grep -n "Don't return SERVFAIL on a domain that looks like a NSEC3"` -> 202; `git -C $C tag --contains e634cfff | grep -E '^NSD_3_2_[0-9]+_REL$' | head -1` -> NSD_3_2_9_REL.

5. **`releases[NSD_3_0_5_REL].total_entries`** — wrong 48, right 32.
   Proof: `git -C $C diff NSD_3_0_4_REL NSD_3_0_5_REL -- doc/ChangeLog | grep -c $'^+\t- '` -> 32 (681 − 649 bullet lines).

6. **`gaps[3]` and `branch_note` ("13 of the 1.x/2.x tags")** — wrong 13, right 15 (the sentence itself lists 15 versions; `date_reliability == "suspect"` count is 15). nsd.md says 15 in its header and 13 in its Gaps section; make both 15.
   Proof: `python3 -c "import json;print(sum(r['date_reliability']=='suspect' for r in json.load(open('data/software/timelines/nsd.json'))['releases']))"` -> 15.

7. **`gaps[3]` ("The real release dates are not recoverable from the clone")** — replace with the release-commit dates listed in the E.3 gap-4 row (14 of 15 manufactured versions have an "Updated for release x.y.z" / `AC_INIT` / version-bump commit on the SVN branch). Recommend a `released_estimate` + `date_reliability: release-commit` on those `releases[]` rows; the tag-commit `released` values may stay as what the tag says.
   Proof: `git -C $C log --all --format='%h %cI %s' --since=2002-09-01 --until=2005-06-01 -i --grep='updated for' | grep -E '[0-9]\.[0-9]\.[0-9]'`.

8. **`gaps[9]`** — drop the "CVE-2019-13207: NVD publication date absent" clause once item 3 is applied.

## Not verifiable

- True release date of 1.1.0b2: no release commit on any ref names it; its manufactured-tag date (2003-03-20, shared with NSD_1_1_0_REL) remains a lower bound, and the 1.1.0 release commit c38bfa54 (2003-06-16) is the only upper bound.
- Which binary default 2.0.x/2.1.x packagers shipped (gap 5): configure.ac says DNSSEC on, RELNOTES says off; nothing in the clone resolves it.
- CVE-2013-5661 fix attribution: no commit or ChangeLog line names it; the rrl-slip rows are the only candidates, as the row says.
- Section D.2 for 3.2.x backports (3.2.19 CDS/CDNSKEY, 3.2.20 URI): "previous stable tag" is ambiguous for two parallel lines; I accepted the branch predecessor (3.2.18 / 3.2.19) and recorded the by-date predecessor result.

## Totals

| section | run | passed | failed |
|---|---|---|---|
| A | 25 (22 date rows + full-sweep, migration-day, stable-rule) | 25 | 0 |
| B | 42 (7 rows × 6 checks) | 38 | 4 (2.2.0 B.3, B.6; 2.3.0 B.2, B.3) |
| C | 42 (14 rows × 3 checks; C.4 n/a) | 41 | 1 (CVE-2019-13207 latency) |
| D | 75 (20 entries × 3 + 15 release totals) | 73 | 2 (4.0.0 #12 re-attributed; 3.0.5 total) |
| E | 17 (E.1, E.2, 13 gaps, gap-4 count, md/json tables) | 14 | 3 (gap 4, gap 4 count/md-json, gap 10) |
| **all** | **201** | **191** | **10** |
