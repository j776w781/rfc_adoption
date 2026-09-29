# Phase 2 handoff: the eight program timelines

Generated 2026-09-29 from `data/software/timelines/*.json`. For an agent with no other
context: what exists for each program, how far it got, and whether it survived
adversarial verification. Schema and standards: `00_phase1_brief.md`; verification
method: `02_phase3_verify_brief.md`.

## State

| program | key | role | releases | span | kept changelog entries | default changes | CVE rows | stage | verification |
|---|---|---|---|---|---|---|---|---|---|
| BIND 9 | `bind9` | authoritative + recursive resolver + signer (named, dnssec-* tools) | 852 (444 stable) | 1999-09-08 .. 2026-09-11 | 1383 | 0 | 0 | release list only | NOT verified |
| Unbound | `unbound` | validating resolver | 214 (120 stable) | 2007-02-19 .. 2026-09-16 | 754 | 30 | 79 | complete | verified + corrected (170 checks, 8 corrections) |
| NSD | `nsd` | authoritative server (serves DNSSEC, does not sign) | 134 (130 stable) | 2002-09-26 .. 2026-09-02 | 252 | 7 | 14 | complete | verified + corrected (201 checks, 8 corrections) |
| Knot DNS | `knot` | authoritative server and signer (validation of received zones since 3.0.0) | 216 (174 stable) | 2011-02-02 .. 2026-09-08 | 527 | 21 | 13 | complete | verified + corrected (397 checks, 7 corrections) |
| Knot Resolver | `kresd` | validating resolver | 98 (89 stable) | 2015-10-08 .. 2026-08-05 | 136 | 18 | 16 | complete | verified + corrected (220 checks, 5 corrections) |
| OpenDNSSEC | `opendnssec` | signer (KASP enforcer + signer engine; no validation) | 144 (65 stable) | 2009-07-30 .. 2024-08-22 | 379 | 15 | 1 | complete | verified + corrected (219 checks, 6 corrections) |
| PowerDNS Authoritative | `pdns-auth` | authoritative (signer; no validation) | 196 (132 stable) | 2002-11-28 .. 2026-08-03 | 330 | 0 | 0 | release list only | NOT verified |
| PowerDNS Recursor | `pdns-rec` | validating resolver | 262 (176 stable) | 2006-04-20 .. 2026-09-02 | 255 | 0 | 0 | release list only | NOT verified |

Five timelines are complete and verified (every default-change and CVE row re-derived
from the bare clone by a fresh agent; corrections applied by the session in a pass that
asserts each pre-change value and writes nothing on failure). Three -- bind9, pdns-auth,
pdns-rec -- are **release lists only**: dated stable tags, no changelog entries, default
changes or CVE fixes. Their builders were cut off by usage limits three to four times each;
the release list survived because the brief now requires writing it first.

## What the verified five established that downstream must respect

- **Release date = commit date of `<tag>^{commit}`.** Tag-object dates from CVS/SVN imports
  are migration days (Unbound before 1.6.3, old NSD and BIND tags).
- **Some tags are lies.** Unbound has five bare re-tags (trees identical to the predecessor:
  1.4.13p1/p2, 1.6.3, 1.6.5, 1.6.8), a mis-imported 1.3.4 (lacks the CVE fix it was cut for)
  and mis-imported 1.8.2/1.8.3. NSD has fifteen manufactured 1.x/2.x tags (real dates in
  `release_commit_dates`), and NSD_2_3_0_REL does not contain its own default-change
  commit. Each such row carries a `stability_note`; use it.
- **Branch point releases ship fixes under different commits than master**, and never
  touch the changelog. The NVD-derived inventory named the next master release in six
  cases; all six are corrected in `cve_inventory.json` (9cd7b41d) with a `correction`
  field. Any latency computed from the inventory before that commit is wrong for those.
- **A default change must touch product code.** A changed test fixture or example reads
  identically in a log; every default row in the verified five names the file.
- **Pre-release-pinned defaults carry `first_stable_tag`** (OpenDNSSEC, eight rows).
  Release-event analysis must use the stable pair.

## Per program

### BIND 9 (`bind9`)

Files: `data/software/timelines/bind9.json`, `.md`
Branch note: Multiple long-lived maintenance branches (v9_0 .. v9_20 in the clone as refs/heads/v9_<minor>); every stable line gets its own point releases (v9.x.y), security patch rebuilds (v9.x.y-Pn), and, 2020-2021, Windows-only rebuilds (v9.x.y-Wn). Extended-support lines are tagged v9.4-ESV[-Rn][-Pn], v9.6-ESV-Rn[-Pn] and v9.9-ESV-R10-P2 (no z component). From 9.13 on, odd minors (9.13, 9.15, 9.17, 9.19, 9

Gaps:
  - STAGE 1 ONLY: default_changes, cve_fixes, news_edits, changelog entries pending

### Unbound (`unbound`)

Files: `data/software/timelines/unbound.json`, `.md`; verify report `docs/handoff/verify/unbound.md`
Branch note: Single master line (SVN trunk until 2017-06, git afterwards); point releases are cut on branch-X.Y.Z branches that never touch doc/Changelog, so their entries are recorded on master after the release and attributed here through the branch commits (git log <prev>..<tag>). SVN-era tags are copies of trunk and mostly not ancestors of master (git merge-base --is-ancestor release-1.0.0 master fails), b

Gaps:
  - Five SVN-import tags are bare re-tags with trees identical to the previous release (git diff --stat is empty): release-1.4.13p1 and release-1.4.13p2 (= release-1.4.13), release-1.6.3 (= 1.6.2), release-1.6.5 (= 1.6.4), release-1.6...
  - release-1.3.4 is also mis-imported: its tree is 1.3.3 plus test data and iana_ports, without the NSEC3 signature fix (CVE-2009-3602) that the 1.4.0 Changelog says was the only content of the 1.3.4 release. The fix commit (1a02ab89...
  - CVE-2009-4008: no Changelog entry or commit names it and the NVD text does not map unambiguously to a 1.4.4 entry; fix_tag left null.
  - CVE-2020-10772 is a Red Hat downstream issue with no upstream fix; marked not applicable.
  - CVE-2019-25031..25042 (X41 D-Sec audit, vendor-disputed) are mapped to 1.9.6 audit-fix commits by NVD description text only (attribution approximate); NVD's 'before 1.9.5' version bound does not match the clone, where 1.9.5 is a 1...
  - Ten CVEs fixed in release-1.26.1 (2026-09-16; CVE-2026-85501 Retrap, -82717, -77860, -81642, -81634, -77955, -78227, -82720, -80225) and CVE-2026-14586 are not in data/software/cve_inventory.json (generated before that release), s...
  - ... 9 more in the JSON

### NSD (`nsd`)

Files: `data/software/timelines/nsd.json`, `.md`; verify report `docs/handoff/verify/nsd.md`
Branch note: Lines: 2.x (RELNOTES) to 2.3.7 (2007-04); 3.x (doc/ChangeLog) 2006-09 .. 3.2.22 (2016-06), overlapping 4.x from 4.0.0 (2013-10). Release tags in the SVN era are off-branch "Created release tag" commits, so tags are not each other's ancestors; release_x.y.z branches in the git era (4.14.1 and 4.13.0 are not descendants of 4.14.0 / 4.12.1). 1.x/2.x tags were manufactured in 2017 and 15 of them sit o

Gaps:
  - NSD is an authoritative server that does not sign: there are no default signing algorithm, key size, NSEC3 iteration/salt or CDS-publication defaults to record. default_changes therefore holds only compile-time DNSSEC/NSEC3 availa...
  - Algorithm awareness is parse-and-serve only: NSD never verifies RRSIGs, so "support" for RSASHA256/512, ECDSA, Ed25519/Ed448 or GOST means the zone parser accepts the mnemonic. git log --all -i --grep for gost and rsasha returns n...
  - No NSEC3 iteration cap exists in the serving code at any tag (nsec3.c@NSD_4_15_2_REL:127 only asserts iterations <= 65536); no limit-changed rows.
  - 15 of the 1.x/2.x tags (1.0.3, 1.1.0, 1.1.0B2, 1.2.0-1.2.4, 2.0.1, 2.0.2, 2.1.3-2.1.5, 2.2.1, 2.3.0) were manufactured by the 2017 SVN import on commits whose RELNOTES lack the version's own section; their dates (date_reliability=...
  - RELNOTES 2.0.0 says DNSSEC is "disabled by default. Enable using --enable-dnssec" but configure.ac at NSD_2_0_0_REL (and 2.1.x) defines DNSSEC unless --disable-dnssec is given (b2d80474 "default: yes"). Trunk flipped the default t...
  - NSD_2_3_0_REL (the "DNSSEC enabled by default" release) does not contain its own release commit; first tag containing 9203aba7 is NSD_2_3_1_REL (2005-08-30). Attribution marked approximate.
  - ... 7 more in the JSON

### Knot DNS (`knot`)

Files: `data/software/timelines/knot.json`, `.md`; verify report `docs/handoff/verify/knot.md`
Branch note: 1.6.x LTS (2014-10 .. 2016-08) ran alongside 2.0-2.3; since 2.5 two minor lines are maintained in parallel (e.g. 2.4.5 with 2.5.2, 3.4.10 with 3.5.4), so the same fix appears as different commits on each line. 1.99.0/1.99.1 are development previews of 2.0.

Gaps:
  - The tag "embedded_lmdb" (2020-05-11) is not a release and is excluded. v1.2-rc1/v1.2-rc2 are duplicate names for v1.2.0-rc1/rc2 (same commits) and carry no entries.
  - NEWS section "2.3.4 (2017-11-20)" has no tag in the clone; its six entries (incl. the only NEWS line naming CVE-2017-11104) are attributed to v2.5.7, the first tag whose NEWS carries the section, and flagged news_section_untagged.
  - The 2.1.0 default-algorithm switch to ECDSAP256SHA256 and the 2.2.0 RSA key-size default (2048 for ZSK) are not in NEWS; they are recorded in default_changes from the commits and doc/configuration.rst diffs only.
  - DSA removal (2.6.0, da9e7ceb8) is not in NEWS; recorded in default_changes / algorithm_support from the commits. The RSA minimum key size 1024 (2.7.0, d0f52e7c4) IS in NEWS 2.7.0 (' - Minimum allowed RSA key length was increased t...
  - doc/reference.rst documented nsec3-iterations "Default: 5" from 2.3.0 to 3.0.5 while the schema default was 10 (scheme.c@v2.3.0:166); the doc was corrected to 10 in 3.0.6 (9a2a2ecf9). The documented-defaults diff therefore shows 5...
  - CVE-2014-0486: no NEWS line names the CVE and NVD published it 3.5 years after the fix; the fixing commits are attributed approximately to the rrset-from-wire hardening merged before v1.5.2 (fac2b82e8).
  - ... 8 more in the JSON

### Knot Resolver (`kresd`)

Files: `data/software/timelines/kresd.json`, `.md`; verify report `docs/handoff/verify/kresd.md`
Branch note: 5.7.x (2023-08 .. 2026-08) and 6.0.x+ (2023-05 ..) are parallel lines. v5.7.1 is an ancestor of v6.0.6 (KeyTrap/NSEC3 commits shared); v5.7.4+ are not ancestors of any 6.x tag, so 6.x entries after 6.0.6 carry their own commits. 6.x NEWS files also embed the 5.x sections; entries are attributed by section header, not by file. v6.0.1-v6.0.5 carry no pre-release suffix and are counted stable by rule

Gaps:
  - Algorithm support: kresd delegates DNSKEY/DS algorithm and digest support to libdnssec/libknot (lib/dnssec.c calls dnssec_algorithm_key_support / dnssec_algorithm_digest_support). The clone has no commit adding RSASHA256/512, ECDS...
  - CVE-2022-32983: no code fix found in the clone; the vendor treated it as a configuration/documentation issue (097339c1 in v5.5.0). fix_tag left null.
  - CVE-2026-39155 is a Knot DNS (authoritative) CVE that the keyword search attached to kresd; marked not applicable.
  - CVE-2018-1110 and CVE-2019-10190: exact fixing commits are approximate (private security repo merge; !827 merge). See attribution_reason.
  - NEWS sections for v6.0.1 .. v6.0.5 contain no per-release entries (only the alpha/early-access notice); their DNSSEC behaviour is that of the 5.x commits they contain (merge-base of v6.0.0a1 with 5.x is v5.5.3).
  - Pre-release tags (v1.0.0-beta*, v1.2.0-rc*, 1.3.0-rc1, v6.0.0a1) are listed with stable=false and no entry rows; entries are attributed to the final release.
  - ... 4 more in the JSON

### OpenDNSSEC (`opendnssec`)

Files: `data/software/timelines/opendnssec.json`, `.md`; verify report `docs/handoff/verify/opendnssec.md`
Branch note: Four maintained lines, each on its own branch: 1.3.x (2011-07 .. 2014-07), 1.4.x (2012-03 .. 2017-04; branched before 1.3.12, so 1.3.13+ fixes are re-done on 1.4), 2.0.x (2016-07 .. 2017-01; EnforcerNG rewrite of the enforcer, alphas from 2012), 2.1.x (2017-02 .. 2024-08, still maintained on 2.1/develop). 2.2 was never released: develop holds it, with six date-stamped test tags in 2018-2019.

Gaps:
  - CVE-2012-5582 (the only inventory CVE) has no fix commit in the clone. The vulnerable eppclient (opt-in build) stayed unchanged on the 1.3 line through 1.3.18 and was deleted from the tree in 1.4.0rc1 (feee7499). fix_tag is null; ...
  - No CVE id appears in any NEWS file (0 found) or commit message (0 found); "cve_fixes" therefore has no fix latency to report.
  - The default signing algorithm switch 7 -> 8 (1.2.0b1, 00ac6896) and the 1.4.0a2 validity/lifetime change (627d8279) have no NEWS line; they are recorded from conf/kasp.xml.in diffs only.
  - The 2048-bit ZSK default (aa6aa1a5, 2019-11-14) exists only on the develop branch; no released tag ships it, so 2.1.14 (2024-08-22) still installs a 1024-bit RSA ZSK example policy. Not recorded as a default change.
  - NSEC3 iterations/salt in the shipped policy (Iterations 5, Salt length 8, Resalt P100D, hash alg 1) never changed between 1.0a1 and 2.1.14; the only commit that touched them ("shorter salt and less iterations" 8a21f7cb, 10/160 -> ...
  - OPENDNSSEC-843 (2.0.2 MaxZoneTTL): RESOLVED on verification -- not a gap. The NEWS line is the bug title; the code shows the absent-element default going 0 (2.0.0/2.0.1) -> 86400 s (2.0.2, 847e9e391a), and default_changes[12] now ...
  - ... 7 more in the JSON

### PowerDNS Authoritative (`pdns-auth`)

Files: `data/software/timelines/pdns-auth.json`, `.md`
Branch note: 

Gaps:
  - STAGE 2 ONLY: default_changes, cve_fixes, news_edits and per-entry commit evidence not yet populated.
  - auth-3.4.10 and auth-3.4.11: no changelog section for these versions exists anywhere in the clone (not in pdns/docs/pdns.xml on rel/auth-3.4.x, not in docs/markdown/changelog.raw.md at auth-4.0.9, not in docs/changelog/pre-4.0.rst...

### PowerDNS Recursor (`pdns-rec`)

Files: `data/software/timelines/pdns-rec.json`, `.md`
Branch note: The recursor shares the clone with the Authoritative Server; only rec-* tags are used. Since 4.x every minor series X.Y lives on a rel/rec-X.Y.x branch; point releases are tagged on the branch, so a fix that master carries under one hash reaches a stable release under a cherry-picked hash on the branch. rec-3-0/rec-3-0-1 are hyphenated aliases of rec-3.0/rec-3.0.1 (same commit); rec-5.0.0-rc2 and 

Gaps:
  - STAGE 2 ONLY: default_changes, cve_fixes, news_edits and per-entry commit evidence are pending; release list and changelog_entries (keyword-filtered, auto-classified, unreviewed) are populated.

## Not yet done

- Stages 2-4 for bind9, pdns-auth, pdns-rec; then Phase 3 verification of each.
- `out/analysis/cve_crossref.json` and the CSVs are stale relative to the corrected
  inventory; regenerate once, after the last three are verified.
