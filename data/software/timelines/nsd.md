# NSD DNSSEC timeline

Generated 2026-09-28 from `out/software_repos/nsd.git` (bare clone), `data/software/cve_inventory.json` and `out/analysis/cve_crossref.json`. Machine-readable twin: `data/software/timelines/nsd.json`.

**Releases:** 134 tags (130 stable, 4 pre-release), 2002-09-26 .. 2026-09-02. Changelog: `RELNOTES` (NSD_1_0_2_REL..NSD_2_3_7_REL), `doc/ChangeLog` (NSD_3_0_0_REL..NSD_4_15_2_REL). Release date = commit date of `<tag>^{commit}`; 15 manufactured 1.x/2.x tags (1.0.3, 1.1.0b2, 1.1.0, 1.2.0, 1.2.1, 1.2.2, 1.2.3, 1.2.4, 2.0.1, 2.0.2, 2.1.3, 2.1.4, 2.1.5, 2.2.1, 2.3.0) sit on pre-release commits, so their dates are lower bounds (see Gaps).

NSD serves DNSSEC but does not sign: there are no signing/key/NSEC3-parameter defaults. The default changes below are compile-time availability of DNSSEC/NSEC3 answer composition and answer-behaviour changes that need no configuration.

Lines: 2.x (RELNOTES) to 2.3.7 (2007-04); 3.x (doc/ChangeLog) 2006-09 .. 3.2.22 (2016-06), overlapping 4.x from 4.0.0 (2013-10). Release tags in the SVN era are off-branch "Created release tag" commits, so tags are not each other's ancestors; release_x.y.z branches in the git era (4.14.1 and 4.13.0 are not descendants of 4.14.0 / 4.12.1). 1.x/2.x tags were manufactured in 2017 and 13 of them sit on pre-release commits.

## How to verify a row

```
C=out/software_repos/nsd.git
git -C $C log -1 --format=%cI <tag>^{commit}                 # release date
git -C $C show <tag>:doc/ChangeLog | grep -n -F "<changelog line>"   # entry present at the tag (RELNOTES for 1.x/2.x)
git -C $C tag --contains <commit> | grep -x <tag>            # commit is in the release
git -C $C show <commit> --stat                               # what it changed
git -C $C show <tag>:configure.ac | sed -n "<lines>p"        # compile-default evidence
```

## Support added / defaults changed / limits changed

| version | date | kind | default change | mechanism | changelog line | commit(s) | in tag |
|---|---|---|---|---|---|---|---|
| 2.0.0ws | 2004-01-09 | support-added | no | rrsig | DNSSEC implemented. | b0de617861, acb6794503 | yes |
| 2.0.0 | 2004-02-12 | support-added | yes | rrsig | Experimental DNSSEC support implemented, but disabled by | acb6794503, b2d80474e1 | yes |
| 2.3.0 | 2005-01-10* | default-changed | yes | rrsig | DNSSEC is now enabled by default. NSD should be fully | 9203aba7a5 | no |
| 3.0.0 | 2006-09-05 | default-changed | yes | rrsig | Fixed RFC 4035 says CD flag SHOULD be cleared on authoritative | 8b51cb2ee9 | yes |
| 3.0.0 | 2006-09-05 | support-added | no | nsec3 | configure option to enable NSEC3 (--enable-nsec3) support. | e9743fda73 | yes |
| 3.0.5 | 2007-06-26 | support-added | no | nsec3 | NSEC3 new wireformat and presentation format from draft-09. | a7d6d473f6 | yes |
| 3.1.0 | 2008-06-23 | default-changed | yes | nsec3 | configure default is --enable-nsec3. Disabling this will save 20% more | e77877aec0 | yes |
| 3.1.0 | 2008-06-23 | support-added | no | nsec3 | set RRTYPE numbers for NSEC3=50, NSEC3PARAM=51. | abcc999311 | yes |
| 3.2.6 | 2010-07-20 | removal | no | rrsig | Removed --disable-nsid, --disable-dnssec, --disable-tsig | bcede5dc3a | yes |
| 3.2.9 | 2011-11-02 | default-changed | yes | rrsig | First step of bug #369: RRSIG DNSKEY sets zone to be treated DNSSEC. | 057212075d | yes |
| 3.2.11 | 2012-06-18 | support-added | no | alg-ecdsa | Add ECDSA support for zonec | 1981eed615 | yes |
| 3.2.11 | 2012-06-18 | support-added | no | dnskey | Allow reading in new DNSKEY algorithm mnemonics in zonefile. | f854e3f8b2 | yes |
| 3.2.19 | 2015-05-21 | support-added | no | cds-cdnskey | RFC 7344: CDS and CDNSKEY (read in). | 381f66a256 | yes |
| 4.1.1 | 2015-02-03 | support-added | no | cds-cdnskey | RFC 7344: CDS and CDNSKEY (read in). | 749900f499 | yes |
| 4.1.13 | 2016-09-19 | default-changed | yes | other | default tsig algorithm is sha256. | ed9cb6ca52 | yes |
| 4.1.16 | 2017-04-11 | support-added | no | alg-eddsa | zone parser can parse acronyms for algorithms ED25519 and ED448. | fead39f912 | yes |

`*` = suspect tag date (manufactured tag). "in tag = no" rows carry an `attribution_reason` in the JSON.

## Default changes (before / after)

| version | date | change | before | after | on upgrade | opt-in | commits | attribution |
|---|---|---|---|---|---|---|---|---|
| 2.0.0 | 2004-02-12 | DNSSEC answer composition compiled in (configure default yes; RELNOTES says disabled) | no DNSSEC code (1.x) | configure.ac@NSD_2_0_0_REL:333-340 defines DNSSEC unless --disable-dnssec; RRSIG/NSEC added to answers when DO is set | yes | no | b2d80474e1, acb6794503 | exact |
| 2.2.0 | 2005-01-10 | DNSSEC compile default flipped to off on trunk | configure.ac@NSD_2_1_2_REL:333-340: DNSSEC defined unless --disable-dnssec | configure.ac@NSD_2_2_0_REL:331-338: DNSSEC defined only with --enable-dnssec | yes | yes | fc944b1d26 | approximate |
| 2.3.0 | 2005-01-10 | DNSSEC enabled by default (compile-time) | configure.ac@NSD_2_2_0_REL:331-338: --enable-dnssec needed | configure.ac@NSD_2_3_1_REL: --disable-dnssec to turn off; DNSSEC (RFC 4033-4035) always compiled in unless disabled | yes | no | 9203aba7a5(!) | approximate |
| 3.0.0 | 2006-09-05 | CD bit cleared in authoritative responses (RFC 4035 bug #140) | CD bit copied from query to response when DNSSEC compiled in | CD bit cleared in all authoritative responses | yes | no | 8b51cb2ee9 | exact |
| 3.1.0 | 2008-06-23 | NSEC3 compiled in by default | configure.ac@NSD_3_0_8_REL: NSEC3 defined only with --enable-nsec3 | configure.ac@NSD_3_1_0_REL:563-570: NSEC3 defined unless --disable-nsec3 (later: unless no SSL) | yes | no | e77877aec0 | exact |
| 3.2.6 | 2010-07-20 | --disable-dnssec removed: DNSSEC serving can no longer be compiled out | configure --disable-dnssec builds a server that ignores DO/RRSIG | DNSSEC answer composition unconditional | yes | no | bcede5dc3a | exact |
| 3.2.9 | 2011-11-02 | zone treated as DNSSEC-signed when RRSIG(DNSKEY) present, not RRSIG(SOA) | zone->is_secure set when an RRSIG covering SOA is loaded (difffile.c/dbaccess.c/zonec.c) | zone->is_secure set when an RRSIG covering DNSKEY is loaded | yes | no | 057212075d | exact |

`(!)` marks a commit not contained in the tag (2.3.0: manufactured tag; see attribution_reason).

## CVE fixes

| CVE | NVD published | fix tag | fix date | latency (days) | DNSSEC | fix commit(s) | note |
|---|---|---|---|---|---|---|---|
| CVE-2009-1755 | 2009-05-22 | NSD_3_2_2_REL | 2009-05-13 | -9 | no | b738d1616a | ChangeLog 3.2.2 "Off-by-one bugfix (thanks Ilja van Sprundel, IOActive)" (6 May 2009) carries no CVE id; matched via the NVD text (packet_read_query_section). NVD also names 2.3.7; no 2.3.x tag after 2.3.7 exists in the clone |
| CVE-2012-2978 | 2012-07-27 | NSD_3_2_13_REL | 2012-07-19 | -8 | no | 793547222d | ChangeLog 3.2.13 (19 July 2012) names the CVE; the code commit 79354722 "Update branche to have DOS vulnerability fixed" is the only commit in the window |
| CVE-2013-5661 | 2019-11-05 | - | - | - | no | fecd050ac3, 029d25ddfc | no NSD commit or ChangeLog line names CVE-2013-5661 (generic RRL slip cache-poisoning id, NVD-published 2019); the related change is the rrl-slip option (ChangeLog "18 Jun 2013: Add rrl-slip config option", first in NSD_3_2_16_REL 2013-07-09 and NSD_4_0_0_REL). fix_tag left null because no commit is attributable to the CVE |
| CVE-2016-6173 | 2017-02-09 | NSD_4_1_11_REL | 2016-08-01 | -192 | no | 7fc93931a8 | ChangeLog line "Fix #790: size-limit-xfr ..." (5 July 2016) has no CVE id; the commit subject does |
| CVE-2019-13207 | - | NSD_4_2_2_REL | 2019-08-13 | - | no | 91102da24d | not in by_product (inventory fixes list only); NVD date absent from the inventory, so latency is null. A second, related overflow (NSEC3 255-octet names, 58ed7127) shipped in 4.15.0 with commit body "incomplete fix of CVE-2019-13207" |
| CVE-2020-28935 | 2020-12-07 | NSD_4_3_4_REL | 2020-11-24 | -13 | no | a4caec3137 | not in by_product (inventory fixes list only); NVD date taken from cve_crossref.json (2020-12-07) |
| CVE-2026-12244 | 2026-06-25 | NSD_4_14_3_REL | 2026-06-24 | -1 | no | 289d78b366 |  |
| CVE-2026-12245 | 2026-06-25 | NSD_4_14_3_REL | 2026-06-24 | -1 | no | 188cb02ba1 |  |
| CVE-2026-12246 | 2026-06-25 | NSD_4_14_3_REL | 2026-06-24 | -1 | no | 42c30338e8 |  |
| CVE-2026-12490 | 2026-06-25 | NSD_4_14_3_REL | 2026-06-24 | -1 | no | 790530f29d |  |
| CVE-2026-18664 | 2026-08-26 | NSD_4_15_1_REL | 2026-08-26 | 0 | no | 11a14bf210 | inventory sha 19260dda is the merge of NSD_4_15_1_REL into release-4.15.2 (4.15.2); the fix is in 4.15.1 |
| CVE-2026-18916 | 2026-08-26 | NSD_4_15_1_REL | 2026-08-26 | 0 | no | 51cc81418e | inventory sha 19260dda is the 4.15.2 merge; the fix is in 4.15.1 |
| CVE-2026-19401 | 2026-08-26 | NSD_4_15_1_REL | 2026-08-26 | 0 | no | bab481d3b7 | inventory sha 19260dda is the 4.15.2 merge; the fix is in 4.15.1 |
| CVE-2026-19538 | 2026-08-26 | NSD_4_15_1_REL | 2026-08-26 | 0 | no | fe6c25b4de | inventory sha 19260dda is the 4.15.2 merge; the fix is in 4.15.1 |

Negative latency = fix released before NVD publication. None of the NSD CVEs in the inventory is a DNSSEC-mechanism bug; the closest is 58ed7127 (4.15.0, NSEC3 255-octet-name overflow, "incomplete fix of CVE-2019-13207").

## Other security fixes without a CVE id

- 4.2.2 (2019-08-13): Fix #19: Out-of-bounds read caused by improper validation of -- 5a01c83900
- 4.15.0 (2026-07-07): Fix to set zone is_secure to false when IXFR removes RRSIG DNSKEY. -- 6bd2498bdb
- 4.15.0 (2026-07-07): Fix to handle NSEC3 zones without space for hashes. Zones with a apex -- cb526641d8
- 4.15.0 (2026-07-07): Fix that out-of-zone records are skipped from zone transfers. -- 43152ede6f
- 4.15.0 (2026-07-07): Fix to not fail on NSEC3 records with a bad owner name. -- d1fe51dbb9
- 4.15.2 (2026-09-02): Fix to ignore NSEC3 records with malformed owner name. In depth fix -- fb99f47f4b, bd584331d7

## Post-hoc changelog edits (release-tag entry text missing at the line's latest tag)

- 2.0.0ws (vs NSD_2_3_7_REL): 1 line(s) missing
  - DNSSEC implemented.
- 3.0.6 (vs NSD_3_2_22_REL): 1 line(s) missing
  - Merged bind2nsd 0.5.0 in contrib from trunk.
- 3.0.7 (vs NSD_3_2_22_REL): 2 line(s) missing
  - Fixed man pages
  - fixup mark_and_exit for rollback of malformed zone transfers.
- 3.0.8 (vs NSD_3_2_22_REL): 1 line(s) missing
  - Release 3.0.7, tagged, configure.ac moved to 3.0.8.
- 3.2.3 (vs NSD_3_2_22_REL): 1 line(s) missing
  - Bug 253: No need for NS RRset in authority section, when returning final answer for QTYPE=DNSKEY.
- 3.2.6 (vs NSD_3_2_22_REL): 1 line(s) missing
  - fix big#314, NSEC next field now correctly escapes spaces.
- 3.2.8 (vs NSD_3_2_22_REL): 1 line(s) missing
  - undo #bug235: messes up dname compression.
- 3.2.11 (vs NSD_3_2_22_REL): 1 line(s) missing
  - Per zone stats, enable with --enable-zone-statistics.
- 4.0.0 (vs NSD_4_15_2_REL): 3 line(s) missing
  - Fix segfault with no logfile and chroot.
  - Fix tpkg test cutest_qroot and rr-test for prinout of algorithms
  - fix bug that relptrs have to be inited with rel_ptr_init() when
- 4.1.4 (vs NSD_4_15_2_REL): 1 line(s) missing
  - Fix #618: documented need to list ip-addresses seperately in
- 4.1.22 (vs NSD_4_15_2_REL): 1 line(s) missing
  - Use accept4 to speed up answer of TCP queries, on Linux and FreeBSD.
- 4.12.1 (vs NSD_4_15_2_REL): 1 line(s) missing
  - Do not delete nodes from non-existent (hash_)trees

## Release list

| version | tag | date | stable | date basis | changelog | own entries | DNSSEC-ish rows |
|---|---|---|---|---|---|---|---|
| 1.0.2 | NSD_1_0_2_REL | 2002-10-14 | yes | tag commit | RELNOTES | 10 | 0 |
| 1.0.3 | NSD_1_0_3_REL | 2002-09-26 | yes | suspect | RELNOTES | 6 | 0 |
| 1.1.0b2 | NSD_1_1_0B2_REL | 2003-03-20 | no | suspect | RELNOTES | 0 | 0 |
| 1.1.0 | NSD_1_1_0_REL | 2003-03-20 | yes | suspect | RELNOTES | 0 | 0 |
| 1.2.0 | NSD_1_2_0_REL | 2003-07-09 | yes | suspect | RELNOTES | 25 | 1 |
| 1.2.1 | NSD_1_2_1_REL | 2003-07-09 | yes | suspect | RELNOTES | 4 | 0 |
| 1.2.2 | NSD_1_2_2_REL | 2003-07-09 | yes | suspect | RELNOTES | 6 | 0 |
| 1.2.3 | NSD_1_2_3_REL | 2003-07-09 | yes | suspect | RELNOTES | 4 | 0 |
| 1.2.4 | NSD_1_2_4_REL | 2003-07-09 | yes | suspect | RELNOTES | 1 | 0 |
| 1.3.0alpha1 | NSD_1_3_0_ALPHA_1_REL | 2003-09-16 | no | tag commit | RELNOTES | 8 | 0 |
| 1.4.0alpha1 | NSD_1_4_0_ALPHA_1_REL | 2003-11-06 | no | tag commit | RELNOTES | 6 | 0 |
| 2.0.0ws | NSD_2_0_0_WS_REL | 2004-01-09 | no | tag commit | RELNOTES | 3 | 1 |
| 2.0.0 | NSD_2_0_0_REL | 2004-02-12 | yes | tag commit | RELNOTES | 6 | 1 |
| 2.0.1 | NSD_2_0_1_REL | 2004-02-25 | yes | suspect | RELNOTES | 4 | 1 |
| 2.0.2 | NSD_2_0_2_REL | 2004-02-25 | yes | suspect | RELNOTES | 3 | 1 |
| 2.1.0 | NSD_2_1_0_REL | 2004-05-12 | yes | tag commit | RELNOTES | 1 | 0 |
| 2.1.1 | NSD_2_1_1_REL | 2004-06-30 | yes | tag commit | RELNOTES | 4 | 0 |
| 2.1.2 | NSD_2_1_2_REL | 2004-07-29 | yes | tag commit | RELNOTES | 7 | 1 |
| 2.1.3 | NSD_2_1_3_REL | 2004-06-22 | yes | suspect | RELNOTES | 8 | 2 |
| 2.1.4 | NSD_2_1_4_REL | 2004-06-22 | yes | suspect | RELNOTES | 1 | 0 |
| 2.1.5 | NSD_2_1_5_REL | 2004-06-22 | yes | suspect | RELNOTES | 2 | 0 |
| 2.2.0 | NSD_2_2_0_REL | 2005-01-10 | yes | tag commit | RELNOTES | 8 | 1 |
| 2.2.1 | NSD_2_2_1_REL | 2005-01-10 | yes | suspect | RELNOTES | 5 | 0 |
| 2.3.0 | NSD_2_3_0_REL | 2005-01-10 | yes | suspect | RELNOTES | 6 | 2 |
| 2.3.1 | NSD_2_3_1_REL | 2005-08-30 | yes | tag commit | RELNOTES | 5 | 1 |
| 2.3.2 | NSD_2_3_2_REL | 2005-12-05 | yes | tag commit | RELNOTES | 9 | 1 |
| 2.3.3 | NSD_2_3_3_REL | 2005-12-07 | yes | tag commit | RELNOTES | 1 | 0 |
| 2.3.4 | NSD_2_3_4_REL | 2006-05-01 | yes | tag commit | RELNOTES | 8 | 0 |
| 2.3.5 | NSD_2_3_5_REL | 2006-05-23 | yes | tag commit | RELNOTES | 2 | 0 |
| 2.3.6 | NSD_2_3_6_REL | 2006-09-29 | yes | tag commit | RELNOTES | 14 | 2 |
| 2.3.7 | NSD_2_3_7_REL | 2007-04-13 | yes | tag commit | RELNOTES | 5 | 0 |
| 3.0.0 | NSD_3_0_0_REL | 2006-09-05 | yes | tag commit | doc/ChangeLog | 548 | 45 |
| 3.0.1 | NSD_3_0_1_REL | 2006-09-06 | yes | tag commit | doc/ChangeLog | 4 | 0 |
| 3.0.2 | NSD_3_0_2_REL | 2006-11-02 | yes | tag commit | doc/ChangeLog | 37 | 2 |
| 3.0.3 | NSD_3_0_3_REL | 2006-12-07 | yes | tag commit | doc/ChangeLog | 32 | 1 |
| 3.0.4 | NSD_3_0_4_REL | 2007-01-16 | yes | tag commit | doc/ChangeLog | 28 | 3 |
| 3.0.5 | NSD_3_0_5_REL | 2007-06-26 | yes | tag commit | doc/ChangeLog | 48 | 16 |
| 3.0.6 | NSD_3_0_6_REL | 2007-09-07 | yes | tag commit | doc/ChangeLog | 7 | 1 |
| 3.0.7 | NSD_3_0_7_REL | 2007-11-13 | yes | tag commit | doc/ChangeLog | 4 | 0 |
| 3.0.8 | NSD_3_0_8_REL | 2008-04-18 | yes | tag commit | doc/ChangeLog | 6 | 0 |
| 3.1.0 | NSD_3_1_0_REL | 2008-06-23 | yes | tag commit | doc/ChangeLog | 40 | 10 |
| 3.1.1 | NSD_3_1_1_REL | 2008-07-17 | yes | tag commit | doc/ChangeLog | 7 | 1 |
| 3.2.0 | NSD_3_2_0_REL | 2008-11-10 | yes | tag commit | doc/ChangeLog | 28 | 3 |
| 3.2.1 | NSD_3_2_1_REL | 2009-01-16 | yes | tag commit | doc/ChangeLog | 13 | 1 |
| 3.2.2 | NSD_3_2_2_REL | 2009-05-13 | yes | tag commit | doc/ChangeLog | 15 | 3 |
| 3.2.3 | NSD_3_2_3_REL | 2009-08-11 | yes | tag commit | doc/ChangeLog | 13 | 1 |
| 3.2.4 | NSD_3_2_4_REL | 2009-12-23 | yes | tag commit | doc/ChangeLog | 17 | 0 |
| 3.2.5 | NSD_3_2_5_REL | 2010-04-14 | yes | tag commit | doc/ChangeLog | 21 | 0 |
| 3.2.6 | NSD_3_2_6_REL | 2010-07-20 | yes | tag commit | doc/ChangeLog | 9 | 2 |
| 3.2.7 | NSD_3_2_7_REL | 2011-01-17 | yes | tag commit | doc/ChangeLog | 20 | 4 |
| 3.2.8 | NSD_3_2_8_REL | 2011-03-22 | yes | tag commit | doc/ChangeLog | 20 | 0 |
| 3.2.9 | NSD_3_2_9_REL | 2011-11-02 | yes | tag commit | doc/ChangeLog | 26 | 4 |
| 3.2.10 | NSD_3_2_10_REL | 2012-02-09 | yes | tag commit | doc/ChangeLog | 6 | 0 |
| 3.2.11 | NSD_3_2_11_REL | 2012-06-18 | yes | tag commit | doc/ChangeLog | 11 | 4 |
| 3.2.12 | NSD_3_2_12_REL | 2012-07-09 | yes | tag commit | doc/ChangeLog | 2 | 0 |
| 3.2.13 | NSD_3_2_13_REL | 2012-07-19 | yes | tag commit | doc/ChangeLog | 2 | 1 |
| 3.2.14 | NSD_3_2_14_REL | 2012-10-24 | yes | tag commit | doc/ChangeLog | 11 | 0 |
| 3.2.15 | NSD_3_2_15_REL | 2013-01-29 | yes | tag commit | doc/ChangeLog | 28 | 6 |
| 3.2.16 | NSD_3_2_16_REL | 2013-07-09 | yes | tag commit | doc/ChangeLog | 30 | 0 |
| 3.2.17 | NSD_3_2_17_REL | 2014-01-20 | yes | tag commit | doc/ChangeLog | 19 | 4 |
| 3.2.18 | NSD_3_2_18_REL | 2014-07-09 | yes | tag commit | doc/ChangeLog | 14 | 1 |
| 3.2.19 | NSD_3_2_19_REL | 2015-05-21 | yes | tag commit | doc/ChangeLog | 15 | 2 |
| 3.2.20 | NSD_3_2_20_REL | 2015-12-03 | yes | tag commit | doc/ChangeLog | 13 | 3 |
| 3.2.21 | NSD_3_2_21_REL | 2016-03-02 | yes | tag commit | doc/ChangeLog | 7 | 0 |
| 3.2.22 | NSD_3_2_22_REL | 2016-06-07 | yes | tag commit | doc/ChangeLog | 10 | 4 |
| 4.0.0 | NSD_4_0_0_REL | 2013-10-29 | yes | tag commit | doc/ChangeLog | 311 | 23 |
| 4.0.1 | NSD_4_0_1_REL | 2014-01-21 | yes | tag commit | doc/ChangeLog | 24 | 4 |
| 4.0.2 | NSD_4_0_2_REL | 2014-03-12 | yes | tag commit | doc/ChangeLog | 18 | 0 |
| 4.0.3 | NSD_4_0_3_REL | 2014-03-14 | yes | tag commit | doc/ChangeLog | 7 | 0 |
| 4.1.0 | NSD_4_1_0_REL | 2014-09-04 | yes | tag commit | doc/ChangeLog | 63 | 2 |
| 4.1.1 | NSD_4_1_1_REL | 2015-02-03 | yes | tag commit | doc/ChangeLog | 25 | 2 |
| 4.1.2 | NSD_4_1_2_REL | 2015-04-07 | yes | tag commit | doc/ChangeLog | 23 | 0 |
| 4.1.3 | NSD_4_1_3_REL | 2015-06-04 | yes | tag commit | doc/ChangeLog | 12 | 1 |
| 4.1.4 | NSD_4_1_4_REL | 2015-08-31 | yes | tag commit | doc/ChangeLog | 18 | 1 |
| 4.1.5 | NSD_4_1_5_REL | 2015-09-21 | yes | tag commit | doc/ChangeLog | 4 | 0 |
| 4.1.6 | NSD_4_1_6_REL | 2015-10-20 | yes | tag commit | doc/ChangeLog | 14 | 1 |
| 4.1.7 | NSD_4_1_7_REL | 2015-12-09 | yes | tag commit | doc/ChangeLog | 47 | 2 |
| 4.1.8 | NSD_4_1_8_REL | 2016-03-02 | yes | tag commit | doc/ChangeLog | 12 | 1 |
| 4.1.9 | NSD_4_1_9_REL | 2016-03-10 | yes | tag commit | doc/ChangeLog | 0 | 0 |
| 4.1.10 | NSD_4_1_10_REL | 2016-06-07 | yes | tag commit | doc/ChangeLog | 19 | 4 |
| 4.1.11 | NSD_4_1_11_REL | 2016-08-01 | yes | tag commit | doc/ChangeLog | 13 | 2 |
| 4.1.12 | NSD_4_1_12_REL | 2016-08-09 | yes | tag commit | doc/ChangeLog | 0 | 0 |
| 4.1.13 | NSD_4_1_13_REL | 2016-09-19 | yes | tag commit | doc/ChangeLog | 26 | 5 |
| 4.1.14 | NSD_4_1_14_REL | 2016-12-01 | yes | tag commit | doc/ChangeLog | 13 | 0 |
| 4.1.15 | NSD_4_1_15_REL | 2017-02-07 | yes | tag commit | doc/ChangeLog | 7 | 0 |
| 4.1.16 | NSD_4_1_16_REL | 2017-04-11 | yes | tag commit | doc/ChangeLog | 11 | 1 |
| 4.1.17 | NSD_4_1_17_REL | 2017-07-13 | yes | tag commit | doc/ChangeLog | 8 | 2 |
| 4.1.18 | NSD_4_1_18_REL | 2017-11-27 | yes | tag commit | doc/ChangeLog | 22 | 4 |
| 4.1.19 | NSD_4_1_19_REL | 2017-12-11 | yes | tag commit | doc/ChangeLog | 10 | 0 |
| 4.1.20 | NSD_4_1_20_REL | 2018-02-14 | yes | tag commit | doc/ChangeLog | 5 | 1 |
| 4.1.21 | NSD_4_1_21_REL | 2018-05-07 | yes | tag commit | doc/ChangeLog | 17 | 1 |
| 4.1.22 | NSD_4_1_22_REL | 2018-06-04 | yes | tag commit | doc/ChangeLog | 8 | 2 |
| 4.1.23 | NSD_4_1_23_REL | 2018-06-11 | yes | tag commit | doc/ChangeLog | 0 | 0 |
| 4.1.24 | NSD_4_1_24_REL | 2018-08-06 | yes | tag commit | doc/ChangeLog | 15 | 2 |
| 4.1.25 | NSD_4_1_25_REL | 2018-09-18 | yes | tag commit | doc/ChangeLog | 21 | 1 |
| 4.1.26 | NSD_4_1_26_REL | 2018-11-29 | yes | tag commit | doc/ChangeLog | 21 | 1 |
| 4.1.27 | NSD_4_1_27_REL | 2019-03-19 | yes | tag commit | doc/ChangeLog | 27 | 1 |
| 4.2.0 | NSD_4_2_0_REL | 2019-06-06 | yes | tag commit | doc/ChangeLog | 44 | 2 |
| 4.2.1 | NSD_4_2_1_REL | 2019-07-02 | yes | tag commit | doc/ChangeLog | 19 | 0 |
| 4.2.2 | NSD_4_2_2_REL | 2019-08-13 | yes | tag commit | doc/ChangeLog | 19 | 2 |
| 4.2.3 | NSD_4_2_3_REL | 2019-11-14 | yes | tag commit | doc/ChangeLog | 22 | 0 |
| 4.2.4 | NSD_4_2_4_REL | 2019-12-03 | yes | tag commit | doc/ChangeLog | 11 | 0 |
| 4.3.0 | NSD_4_3_0_REL | 2020-03-10 | yes | tag commit | doc/ChangeLog | 54 | 1 |
| 4.3.1 | NSD_4_3_1_REL | 2020-04-08 | yes | tag commit | doc/ChangeLog | 28 | 0 |
| 4.3.2 | NSD_4_3_2_REL | 2020-07-07 | yes | tag commit | doc/ChangeLog | 27 | 1 |
| 4.3.3 | NSD_4_3_3_REL | 2020-10-01 | yes | tag commit | doc/ChangeLog | 21 | 1 |
| 4.3.4 | NSD_4_3_4_REL | 2020-11-24 | yes | tag commit | doc/ChangeLog | 19 | 2 |
| 4.3.5 | NSD_4_3_5_REL | 2021-01-19 | yes | tag commit | doc/ChangeLog | 19 | 3 |
| 4.3.6 | NSD_4_3_6_REL | 2021-03-30 | yes | tag commit | doc/ChangeLog | 26 | 2 |
| 4.3.7 | NSD_4_3_7_REL | 2021-07-22 | yes | tag commit | doc/ChangeLog | 26 | 3 |
| 4.3.8 | NSD_4_3_8_REL | 2021-10-07 | yes | tag commit | doc/ChangeLog | 26 | 2 |
| 4.3.9 | NSD_4_3_9_REL | 2021-12-02 | yes | tag commit | doc/ChangeLog | 7 | 0 |
| 4.4.0 | NSD_4_4_0_REL | 2022-02-10 | yes | tag commit | doc/ChangeLog | 12 | 0 |
| 4.5.0 | NSD_4_5_0_REL | 2022-05-13 | yes | tag commit | doc/ChangeLog | 10 | 1 |
| 4.6.0 | NSD_4_6_0_REL | 2022-06-23 | yes | tag commit | doc/ChangeLog | 9 | 0 |
| 4.6.1 | NSD_4_6_1_REL | 2022-11-01 | yes | tag commit | doc/ChangeLog | 15 | 1 |
| 4.7.0 | NSD_4_7_0_REL | 2023-05-31 | yes | tag commit | doc/ChangeLog | 36 | 0 |
| 4.8.0 | NSD_4_8_0_REL | 2023-11-29 | yes | tag commit | doc/ChangeLog | 25 | 0 |
| 4.9.0 | NSD_4_9_0_REL | 2024-04-03 | yes | tag commit | doc/ChangeLog | 29 | 2 |
| 4.9.1 | NSD_4_9_1_REL | 2024-04-04 | yes | tag commit | doc/ChangeLog | 2 | 0 |
| 4.10.0 | NSD_4_10_0_REL | 2024-06-12 | yes | tag commit | doc/ChangeLog | 16 | 0 |
| 4.10.1 | NSD_4_10_1_REL | 2024-08-02 | yes | tag commit | doc/ChangeLog | 32 | 1 |
| 4.11.0 | NSD_4_11_0_REL | 2024-12-12 | yes | tag commit | doc/ChangeLog | 30 | 2 |
| 4.11.1 | NSD_4_11_1_REL | 2025-01-18 | yes | tag commit | doc/ChangeLog | 5 | 0 |
| 4.12.0 | NSD_4_12_0_REL | 2025-04-24 | yes | tag commit | doc/ChangeLog | 33 | 1 |
| 4.12.1 | NSD_4_12_1_REL | 2025-10-09 | yes | tag commit | doc/ChangeLog | 1 | 0 |
| 4.13.0 | NSD_4_13_0_REL | 2025-09-03 | yes | tag commit | doc/ChangeLog | 48 | 0 |
| 4.14.0 | NSD_4_14_0_REL | 2025-12-04 | yes | tag commit | doc/ChangeLog | 17 | 1 |
| 4.14.1 | NSD_4_14_1_REL | 2026-02-24 | yes | tag commit | doc/ChangeLog | 19 | 3 |
| 4.14.2 | NSD_4_14_2_REL | 2026-03-12 | yes | tag commit | doc/ChangeLog | 3 | 0 |
| 4.14.3 | NSD_4_14_3_REL | 2026-06-24 | yes | tag commit | doc/ChangeLog | 4 | 4 |
| 4.15.0 | NSD_4_15_0_REL | 2026-07-07 | yes | tag commit | doc/ChangeLog | 30 | 5 |
| 4.15.1 | NSD_4_15_1_REL | 2026-08-26 | yes | tag commit | doc/ChangeLog | 4 | 4 |
| 4.15.2 | NSD_4_15_2_REL | 2026-09-02 | yes | tag commit | doc/ChangeLog | 43 | 7 |

## Gaps

- NSD is an authoritative server that does not sign: there are no default signing algorithm, key size, NSEC3 iteration/salt or CDS-publication defaults to record. default_changes therefore holds only compile-time DNSSEC/NSEC3 availability and answer-composition behaviour (CD bit, is_secure trigger).
- Algorithm awareness is parse-and-serve only: NSD never verifies RRSIGs, so "support" for RSASHA256/512, ECDSA, Ed25519/Ed448 or GOST means the zone parser accepts the mnemonic. git log --all -i --grep for gost and rsasha returns nothing; ECDSA (3.2.11) and ED25519/ED448 (4.1.16) are the only algorithm-mnemonic commits. RSA/SHA-2 mnemonics were probably covered by "Allow reading in new DNSKEY algorithm mnemonics" (3.2.11, f854e3f8) but the commit does not list them; not asserted.
- No NSEC3 iteration cap exists in the serving code at any tag (nsec3.c@NSD_4_15_2_REL:127 only asserts iterations <= 65536); no limit-changed rows.
- 13 of the 1.x/2.x tags (1.0.3, 1.1.0, 1.1.0B2, 1.2.0-1.2.4, 2.0.1, 2.0.2, 2.1.3-2.1.5, 2.2.1, 2.3.0) were manufactured by the 2017 SVN import on commits whose RELNOTES lack the version's own section; their dates (date_reliability="suspect") are lower bounds, several tags share one commit, and 1.0.3 is dated before 1.0.2. Entries for those versions are read from NSD_2_3_7_REL:RELNOTES. The real release dates are not recoverable from the clone.
- RELNOTES 2.0.0 says DNSSEC is "disabled by default. Enable using --enable-dnssec" but configure.ac at NSD_2_0_0_REL (and 2.1.x) defines DNSSEC unless --disable-dnssec is given (b2d80474 "default: yes"). Trunk flipped the default to off in merge fc944b1d (first in NSD_2_2_0_REL) and back on in 9203aba7 for 2.3.0. Which binary default 2.0.x packagers actually shipped cannot be settled from the clone.
- NSD_2_3_0_REL (the "DNSSEC enabled by default" release) does not contain its own release commit; first tag containing 9203aba7 is NSD_2_3_1_REL (2005-08-30). Attribution marked approximate.
- doc/ChangeLog first appears at NSD_3_0_0_REL and holds the whole 3.0 development log (548 entries back to 2004), so 3.0.0 "new entries" are the 3.0 branch history, not one release cycle.
- SVN-era tags are not ancestors of one another (each tag is a "Created x.y.z release tag" commit off the branch), so commits_since_prev is null for many 3.x tags; entry attribution uses changelog diffs, and tag --contains works because the tag commit descends from the branch.
- The 3.2.x line (3.2.16-3.2.22) and 4.x line ran in parallel 2013-10 .. 2016-06; entries backported to 3.2.x appear twice with their own tags (e.g. CDS/CDNSKEY in 4.1.1 then 3.2.19). Some ChangeLog entries are re-listed in later releases (3.2.7 re-lists 3.2.3/3.2.6 lines; 4.1.7 re-lists 2006/2012 lines; 4.15.2 re-dates three 4.15.0 lines as "29 June 2026: Jannik"); these rows carry a note and are not new changes.
- CVE-2013-5661 (RRL slip cache poisoning): no commit or ChangeLog line names it; fix_tag null, related rrl-slip option noted. CVE-2019-13207: NVD publication date absent from the inventory and crossref, latency null. CVE-2009-1755 also names NSD 2.3.7; no later 2.3.x tag exists.
- The inventory attributes the four 2026-08 CVEs to 4.15.2 via merge commit 19260dda; the ChangeLog and the non-merge fix commits place them in NSD_4_15_1_REL (2026-08-26, NVD-published the same day).
- Entry rows classified "other" with note "not DNSSEC (keyword match only)" are keyword false positives (signed/unsigned, sha256 tarballs, TSIG hmac-sha256, unrelated RFC numbers); they are kept so the density count is reproducible.
- Commit attribution for kind=other rows is automatic (commit message equal to the ChangeLog line within +-10 days of the header date, inside the tag); rows without a match simply have no commit. Only support-added/default-changed/cve-fix rows were verified by hand.
