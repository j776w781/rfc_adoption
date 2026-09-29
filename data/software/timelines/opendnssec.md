# OpenDNSSEC (opendnssec) DNSSEC timeline

Generated 2026-09-29 from `out/software_repos/opendnssec.git` (bare clone), `data/software/cve_inventory.json` and `out/analysis/cve_crossref.json`. Machine-readable twin: `data/software/timelines/opendnssec.json`.

**Releases:** 144 tags (65 stable, 79 pre-release/dev/duplicate), 2009-07-30 .. 2024-08-22. Changelog: `NEWS` at every tag (1.0a1/1.0a2 sections read from NEWS at 1.0a3); `signer/doc/Changelog` is a stale signer-only log (last edit 2014-01-13) and was not used. Shipped example policy: `conf/kasp.xml.in` (`xml/kasp.xml.in` at 1.0a1..1.0a5). Release date = commit date of `<tag>^{commit}`.

Four maintained lines, each on its own branch: 1.3.x (2011-07 .. 2014-07), 1.4.x (2012-03 .. 2017-04; branched before 1.3.12, so 1.3.13+ fixes are re-done on 1.4), 2.0.x (2016-07 .. 2017-01; EnforcerNG rewrite of the enforcer, alphas from 2012), 2.1.x (2017-02 .. 2024-08, still maintained on 2.1/develop). 2.2 was never released: develop holds it, with six date-stamped test tags in 2018-2019.

OpenDNSSEC is a signer only: there are no validation, trust-anchor-consumption or resolver-side rows. "Default" here means what a fresh install signs with, i.e. the shipped `conf/kasp.xml.in` plus code defaults; template changes are marked `on upgrade = no` because an operator with their own kasp.xml is unaffected.

## How to verify a row

```
C=out/software_repos/opendnssec.git
git -C $C log -1 --format=%cI <tag>^{commit}          # release date
git -C $C show <tag>:NEWS | grep -n -F "<changelog line>"  # entry present at the tag
git -C $C tag --contains <commit> | grep -x <tag>     # commit is in the release
git -C $C show <commit> --stat                        # what it changed
git -C $C diff <prev>:conf/kasp.xml.in <tag>:conf/kasp.xml.in   # template default changes
```

## Support added / defaults changed / limits changed / removals

| version | date | stable | kind | default change | mechanism | changelog line (or code-only change) | commit(s) | in tag |
|---|---|---|---|---|---|---|---|---|
| 1.0.0b2 | 2009-10-09 | no | support-added | no | alg-rsa-sha2 | * Added experimental support for RSA/SHA256 and RSA/SHA512 to KASP enforcer | 924e772972, 4fdb5dd073 | yes |
| 1.0.0b2 | 2009-10-09 | no | support-added | no | alg-rsa-sha2 | * Added support for RSA/SHA256 and RSA/SHA512 to libhsm. No API changes. | b11d7bdab1, 0807501945 | yes |
| 1.0.0b2 | 2009-10-09 | no | default-changed | yes | rrsig | (code) conf/kasp.xml.in template: <Denial> validity P14D -> P7D; ZSK <Lifetime> P14D -> P30D | 3a83b287b5, 5f25bcedc3 | yes |
| 1.0.0b3 | 2009-10-16 | no | support-added | no | alg-rsa-sha2 | * The auditor (dnsruby) supports RSA/SHA256 and RSA/SHA512 | af6337dcab | yes |
| 1.0.0b3 | 2009-10-16 | no | removal | no | trust-anchor-5011 | (code) conf/kasp.xml.in template: <RFC5011/> element removed from the KSK example ("say that it is not implemented yet") | 27c37dc164 | yes |
| 1.0.0b8 | 2009-11-23 | no | default-changed | yes | other | * ods-ksmutil: KSK rollover now holds at the point where the new key is made | df60b95811, a2537c7c9d | yes |
| 1.0.0b8 | 2009-11-23 | no | default-changed | yes | rrsig | (code) conf/kasp.xml.in template: <InceptionOffset> PT300S -> PT3600S; <Zone><PropagationDelay> PT9999S -> PT43200S | f7fad72703 | yes |
| 1.0a4 | 2009-09-10 | no | support-added | no | dnskey | * add export of DNSKEY and DS records to ksmutil | 99b8c2e414, c88d6c8e02 | yes |
| 1.0a4 | 2009-09-10 | no | support-added | no | other | * Added <ManualRollover/> tag to kasp.xml; this allows automatic rollovers | f515281e8d, 94c193decb | yes |
| 1.1.0rc1 | 2010-04-22 | no | support-added | no | other | * Enable the EPP-client using --enable-eppclient | 58ebef56cd, e7dbbff19b, b2aade575b | yes |
| 1.1.0rc1 | 2010-04-22 | no | default-changed | yes | nsec3 | * Turn NSEC3 OptOut off by default | ceba527456 | yes |
| 1.1.0rc1 | 2010-04-22 | no | support-added | no | dnskey | * DNSKEY records communicated to an external script if configured | 5c22ab4a9d, d057f659fd | yes |
| 1.1.1 | 2010-07-08 | yes | default-changed | yes | dnskey | (code) conf/kasp.xml.in template: <Standby> 1 -> 0 for both KSK and ZSK ("Set the default number of standby keys to zero") | 980c9d0a33 | yes |
| 1.2.0b1 | 2010-10-18 | no | default-changed | yes | alg-rsa-sha2 | (code) conf/kasp.xml.in template: KSK and ZSK <Algorithm> 7 (RSASHA1-NSEC3-SHA1) -> 8 (RSASHA256) ("Default algorithm is now 8 (RSASHA256)") | 00ac6896dd | yes |
| 1.2.2 | 2011-08-11 | yes | limit-changed | no | nsec3-iterations | * signconf.rnc now allows NSEC3 Iterations of 0 | 57a4f9c3b9 | yes |
| 1.3.0rc2 | 2011-05-18 | no | limit-changed | no | nsec3-iterations | * signconf.rnc now allows NSEC3 Iterations of 0 | e9783741af | yes |
| 1.3.11 | 2012-11-13 | yes | default-changed | yes | nsec3 | * OPENDNSSEC-330: NSEC3PARAM TTL should be set to zero. | 1459ca16c1 | yes |
| 1.3.16 | 2013-12-04 | yes | support-added | no | nsec3 | * OPENDNSSEC-436: NSEC3PARAM TTL can now be optionally configured in kasp.xml. | 312b56315f, 70540d9966 | yes |
| 1.3.17 | 2014-05-06 | yes | default-changed | yes | nsec3 | * OPENDNSSEC-550: Signer Engine: Put NSEC3 records on empty non-terminals | 95ca9be254 | yes |
| 1.4.0a1 | 2012-03-15 | no | support-added | no | alg-gost | (code) libhsm: DSA and GOST key generation and signing, ECDSA P-256 signing case ("Support DSA and GOST in libhsm. Needs testing.") | 4b5736cbef | yes |
| 1.4.0a2 | 2012-05-24 | no | default-changed | yes | rrsig | (code) conf/kasp.xml.in template: signature <Validity> Default/Denial P7D -> P14D; ZSK <Lifetime> P30D -> P90D | 627d82798a | yes |
| 1.4.0b2 | 2012-12-17 | no | default-changed | yes | nsec3 | * OPENDNSSEC-330: Signer Engine: NSEC3PARAM TTL should be set to zero. | 6d11eb9b85 | yes |
| 1.4.0rc1 | 2013-01-10 | no | removal | no | other | * OPENDNSSEC-359: Remove eppclient | feee749967 | yes |
| 1.4.3 | 2013-12-04 | yes | support-added | no | nsec3 | * OPENDNSSEC-330: NSEC3PARAM TTL can now be optionally configured in kasp.xml. | c2ba8d69c4, 9b0fd1e00d, 95bef6f628 | yes |
| 1.4.4 | 2014-03-25 | yes | default-changed | yes | nsec3 | * OPENDNSSEC-549: Signer Engine: Put NSEC3 records on empty non-terminals | 7d014cc924 | yes |
| 1.4.8 | 2015-09-25 | yes | support-added | no | trust-anchor-5011 | * Support for RFC5011 style KSK rollovers. KSK section in the KASP now | 84b743a4cd, 7f73606202 | yes |
| 2.0.0a3 | 2012-06-18 | no | default-changed | yes | other | (code) conf/kasp.xml.in template: <MaxZoneTTL>PT1D</MaxZoneTTL> added to the default policy ("define MaxZoneTTL in example config") | 1b11a04053 | yes |
| 2.0.0a5 | 2015-10-28 | no | support-added | no | alg-ecdsa | (code) libhsm: ECDSA key generation (hsm_generate_ecdsa_key) and "ods-hsmutil generate ... ecdsa" ("OPENDNSSEC-450: Add support for ECDSA in libhsm") | 34b2602965, e5fb3dd4e1 | yes |
| 2.0.2 | 2016-09-27 | yes | default-changed | yes | other | * OPENDNSSEC-843: MaxZoneTTL defaults to 0 instead of 1 day. | 847e9e391a | yes |
| 2.1.0 | 2017-02-22 | yes | support-added | no | alg-ecdsa | * OPENDNSSEC-450: Implement support for ECDSA P-256, P-384, GOST. Notice: | 75fe5aa5c7 | yes |
| 2.1.0 | 2017-02-22 | yes | default-changed | yes | ds-digest | * OPENDNSSEC-552: On key export don't print SHA1 DS by default. (introduced | b6bfbe1c71, 64a6d9cc55 | yes |
| 2.1.3 | 2017-08-10 | yes | default-changed | yes | other | * OPENDNSSEC-908: Warn when TTL exceeds KASP's MaxZoneTTL instead of capping. | f5ed360d4c | yes |
| 2.1.7 | 2020-10-07 | yes | support-added | no | alg-eddsa | * SUPPORT-222: Support ED25519/ED448 keys.  This requires library ldns 1.7.0 | 46e0a7b947, c32451f71b, 804b90ae0c | yes |
| 2.1.10 | 2021-09-10 | yes | limit-changed | no | nsec3-iterations | * OPENDNSSEC-959: Emit warning on ods-kaspcheck for NSEC iteration count | d654d90f90 | yes |
| 2.1.13 | 2023-06-26 | yes | limit-changed | no | nsec3-iterations | * Emit warning when using ods-kaspcheck for RFC 5155 | b6716e31fb | yes |

`(!)` would mark a commit not contained in the tag; none are. Rows whose line starts with `(code)` have no NEWS entry and are evidenced by the commit / `conf/kasp.xml.in` diff alone.

## Default changes (before / after)

| version | date | change | before | after | on upgrade | opt-in | commits | attribution |
|---|---|---|---|---|---|---|---|---|
| 1.0.0b2 | 2009-10-09 | example policy: signature validity for denial RRs 14 -> 7 days, ZSK lifetime 14 -> 30 days | <Validity><Denial>P14D; ZSK <Lifetime>P14D (conf/kasp.xml.in@1.0.0b1) | <Validity><Denial>P7D; ZSK <Lifetime>P30D (conf/kasp.xml.in@1.0.0b2) | no | no | 3a83b287b5, 5f25bcedc3 | exact |
| 1.0.0b8 | 2009-11-23 | example policy: RRSIG inception offset 5 min -> 1 h | <InceptionOffset>PT300S (conf/kasp.xml.in@1.0.0b7) | <InceptionOffset>PT3600S (conf/kasp.xml.in@1.0.0b8:29) | no | no | f7fad72703 | exact |
| 1.0.0b8 | 2009-11-23 | KSK rollover waits for the operator (ds-seen) before the new key goes active | KSK rollover proceeded automatically once timers expired | KSK rollover halts with the new key in READY state until "ods-ksmutil ds-seen" (renamed ksk-roll in 1.0.0b9, back to ds-seen in 1.1.0) is issued | yes | no | df60b95811, a2537c7c9d | exact |
| 1.1.0rc1 | 2010-04-22 | example policy: NSEC3 Opt-Out off | <NSEC3><OptOut/> active (conf/kasp.xml.in@1.0.0:34) | <!-- <OptOut/> --> (conf/kasp.xml.in@1.1.0rc1); Opt-Out zones become opt-in | no | no | ceba527456 | exact |
| 1.1.1 | 2010-07-08 | example policy: no standby keys | <Standby>1 for KSK and ZSK (conf/kasp.xml.in@1.1.0) | <Standby>0 for KSK and ZSK (conf/kasp.xml.in@1.1.1); 1.2.0b1 then drops the element (63d1facd "make Standby keys optional") | no | no | 980c9d0a33 | exact |
| 1.2.0b1 | 2010-10-18 | example policy: default signing algorithm 7 (RSASHA1-NSEC3-SHA1) -> 8 (RSASHA256) | <Algorithm length="2048">7 (KSK) and <Algorithm length="1024">7 (ZSK) (conf/kasp.xml.in@1.1.3) | <Algorithm length="2048">8 (KSK) and <Algorithm length="1024">8 (ZSK) (conf/kasp.xml.in@1.2.0b1); unchanged through 2.1.14 (conf/kasp.xml.in@2.1.14:53,60) | no | no | 00ac6896dd | exact |
| 1.3.11 | 2012-11-13 | NSEC3PARAM RR published with TTL 0 | NSEC3PARAM TTL taken from the zone default/SOA minimum | NSEC3PARAM TTL 0 (OPENDNSSEC-330); 1.3.16 makes it configurable via kasp.xml <NSEC3><TTL>, default still PT0S | yes | no | 1459ca16c1 | exact |
| 1.4.0b2 | 2012-12-17 | NSEC3PARAM RR published with TTL 0 (1.4 line) | NSEC3PARAM TTL taken from the zone default/SOA minimum | NSEC3PARAM TTL 0 (OPENDNSSEC-330); 1.4.3 makes it configurable, default still PT0S | yes | no | 6d11eb9b85 | exact |
| 1.4.0a2 | 2012-05-24 | example policy: signature validity 7 -> 14 days, ZSK lifetime 30 -> 90 days | <Validity><Default>P7D <Denial>P7D; ZSK <Lifetime>P30D (conf/kasp.xml.in@1.4.0a1) | <Validity><Default>P14D <Denial>P14D; ZSK <Lifetime>P90D (conf/kasp.xml.in@1.4.0a2); unchanged through 2.1.14 (conf/kasp.xml.in@2.1.14:22-23,61) | no | no | 627d82798a | exact |
| 1.3.17 | 2014-05-06 | NSEC3 records also emitted for empty non-terminals above unsigned delegations | no NSEC3 for ENTs whose only descendants are insecure (opt-out) delegations, per RFC 5155 errata 3441 | such ENTs get NSEC3 RRs, for resolvers/servers that pre-date errata 3441 (OPENDNSSEC-550) | yes | no | 95ca9be254 | exact |
| 1.4.4 | 2014-03-25 | NSEC3 records also emitted for empty non-terminals above unsigned delegations (1.4 line) | no NSEC3 for such ENTs (errata 3441 behaviour) | NSEC3 RRs emitted for them (OPENDNSSEC-549) | yes | no | 7d014cc924 | exact |
| 2.0.0a3 | 2012-06-18 | example policy gains <MaxZoneTTL> | no MaxZoneTTL element (1.4.x template) | <Signatures><MaxZoneTTL>PT1D (default policy) / PT300S (lab policy) (conf/kasp.xml.in@2.0.0a3); P1D from 2.0.0a5 | no | no | 1b11a04053 | exact |
| 2.0.2 | 2016-09-27 | MaxZoneTTL default when the element is absent | NEWS: 1 day | NEWS: 0. NOT confirmed from code: the only MaxZoneTTL change in 2.0.1..2.0.2 is 847e9e39 (restores PR #508 "drifting_time"), whose policy_ext.c hunk replaces "set 0 when updated" with "set 86400 if != 86400", and enforcer/src/db/policy.c@2.0.2:490 still initialises signatures_max_zone_ttl = 86400 | yes | no | 847e9e391a | approximate |
| 2.1.0 | 2017-02-22 | key export prints SHA-256 DS only (SHA-1 DS no longer printed by default) | "ods-enforcer key export --ds" printed both SHA-1 (digest 1) and SHA-256 (digest 2) DS records | SHA-256 DS only; --sha1 restores the SHA-1 DS; SHA-1 declared deprecated (64a6d9cc "Depracation notice of sha1") | yes | no | b6bfbe1c71, 64a6d9cc55 | exact |
| 2.1.3 | 2017-08-10 | TTLs above MaxZoneTTL are warned about instead of capped | signer capped RR TTLs to the policy MaxZoneTTL | signer leaves TTLs as in the input zone and logs a warning (OPENDNSSEC-908 "Capping to MaxZoneTTL breaks IXFR") | yes | no | f5ed360d4c | exact |

"on upgrade = no" rows change only the shipped example policy `conf/kasp.xml.in`; existing installations keep their own kasp.xml. Advisory limits (2.1.10 >100 iterations, 2.1.13 RFC 5155 tiers) are ods-kaspcheck warnings and do not alter signing output, so they are not repeated here.

## CVE fixes

| CVE | NVD published | fix tag | fix date | latency (days) | DNSSEC | fix commit(s) | note |
|---|---|---|---|---|---|---|---|
| CVE-2012-5582 | 2019-11-25 | - | - | - | no | - | No fix commit exists in the clone: git log --all -G VERIFYHOST returns only the 2010 import (58ebef56) and the 2013 removal (feee7499). 1.3.x kept the vulnerable file through 1.3.18 (2014-07-21, end of the 1.3 line); 1.4.0rc1 (2013-01-10) removed eppclient from the tree entirely (NEWS 1.4.0rc1 "OPENDNSSEC-359: Remove eppclient"). NVD published the id on 2019-11-25, seven years after the oss-security report (2012-11-28) the inventory refs point to; days from removal to NVD publication: 2510. The crossref file scopes it "dependency" with rule DEPENDENCY and no mechanism. |

The inventory attributes exactly one CVE to OpenDNSSEC (keyword search "OpenDNSSEC"; the product has no CPE in NVD, see crossref attribution_caveat). No NEWS file or commit message in the clone names any CVE id.

## Security-relevant fixes without a CVE id

- 1.4.0rc2 (2013-01-25): * SUPPORT-44: Signer Engine: Drop privileges after binding to socket [OPENDNSSEC-364].
- 2.0.0a5 (2015-10-28): (no NEWS line) OPENDNSSEC-534: Fix information leak in hsm_get_key_ecdsa_value; OPENDNSSEC-540: Fix possible integer overflow in hsm_get_key_size_ecdsa -- c40d2aa085, cdac7346ae
- 1.3.7 (2012-03-13): * SUPPORT-21: HSM SCA 6000 in combination with OpenCryptoki can return RSA key material with leading zeroes. DNSSEC does not allow leading zeroes in key data. ... OpenDNSSEC will now sanitize ...

## Changes that never reached a release tag

- example policy ZSK 1024 -> 2048 bit RSA ("use 2048-bit RSA/SHA-256 as default") -- aa6aa1a525 (2019-11-14, branches: develop): develop branch only; contained in no tag. Every released kasp.xml.in through 2.1.14 keeps <Algorithm length="1024">8 for the ZSK (conf/kasp.xml.in@2.1.14:60,124)
- ods-kaspcheck RFC 5155 s10.3 iteration warning (OPENDNSSEC-893) -- 65065fbbce (2017-06-15, branches: none): develop/master and the 2.2.0-dev date tags only (first tag by date 20181001); reached the 2.1 line as part of b6716e31 in 2.1.13
- EdDSA on the 2.2 line (SUPPORT-222, develop copy) -- 40f41194e6 (2020-08-15, branches: develop): develop only; the 2.1-line copy 46e0a7b9 is what shipped (2.1.7)

## Post-hoc NEWS edits (text at latest tag differs from text at the release tag)

- 1.0.0b1 (vs 2.1.14): added 2, removed 1
  - + There are changes to the KASP DB:
  - + Zone fetcher added, that will do AXFR from the master. sqlite3 <PATH_TO_ENFORCER.DB> < enforcer/utils/migrate_090922_1.sqlite3 sqlite3 <PATH_TO_ENFORCER.DB> < e
  - - There are changes to the KASP DB: sqlite3 <PATH_TO_ENFORCER.DB> < enforcer/utils/migrate_090922_1.sqlite3 sqlite3 <PATH_TO_ENFORCER.DB> < enforcer/utils/migrate
- 1.0.0b2 (vs 2.1.14): added 1, removed 0
  - + Added experimental support for RSA/SHA256 and RSA/SHA512 to KASP auditor. Dnsruby version 1.38 or higher required for SHA2 support.
- 1.0a3 (vs 2.1.14): added 1, removed 1
  - + Changes to the KASP DB, please apply: sqlite3 <PATH_TO_ENFORCER.DB> < enforcer/utils/migrate_090820_1.sqlite3 Or start fresh (with loss of information. User sho
  - - Changes to the KASP DB, please apply: sqlite3 <PATH_TO_ENFORCER.DB> < enforcer/utils/migrate_090820_1.sqlite3 ksmutil setup
- 1.0a4 (vs 2.1.14): added 1, removed 1
  - + Changes to the KASP DB, please apply: sqlite3 <PATH_TO_ENFORCER.DB> < enforcer/utils/migrate_090901_1.sqlite3 Or start fresh (with loss of information. User sho
  - - Changes to the KASP DB, please apply: sqlite3 <PATH_TO_ENFORCER.DB> < enforcer/utils/migrate_090901_1.sqlite3 ksmutil setup
- 1.2.0b1 (vs 2.1.14): added 1, removed 0
  - + Signer Engine: Check if the signature exists before recycling it.
- 1.2.0rc1 (vs 2.1.14): added 0, removed 1
  - - There is a kasp schema change from the 1.1 branch (or trunk if you built 1) Run ods-ksmutil setup again. This will remove _all_ the current information from the
- 1.2.0rc2 (vs 2.1.14): added 0, removed 1
  - - There is a kasp schema change from the 1.1 branch (or trunk if you built 1) Run ods-ksmutil setup again. This will remove _all_ the current information from the
- 1.2.1 (vs 2.1.14): added 1, removed 0
  - + Signer Engine: NSEC chain could become broken if the predecessor domain of a deleted domain was a glue domain.
- 1.3.0b1 (vs 2.1.14): added 3, removed 1
  - + Bugreport #139: ods-auditor fails on root zone.
  - + Signer Engine: Temperate the number of backup files.
  - + Support for signing the root. Use the zone name "."
  - - Signer Engine: NSEC chain could become broken if the predecessor domain of a deleted domain was a glue domain.
- 1.3.0rc1 (vs 2.1.14): added 1, removed 0
  - + Include check for resign < resalt in ods-kaspcheck.
- 1.3.0rc3 (vs 2.1.14): added 1, removed 1
  - + Bugfix #242: Race condition when receiving multiple NOTIFIES for a zone.
  - - Bugfix #242: Race condition when receiving multiple NOTIFIES for a zone. (Need an end-user acceptance test before closing the ticket)
- 1.4.0a2 (vs 2.1.14): added 4, removed 0
  - + OPENDNSSEC-228: Signer Engine: Make 'ods-signer update' reload signconfs even if zonelist has not changed.
  - + OPENDNSSEC-231: Signer Engine: Allow for Classless IN-ADDR.ARPA names (RFC 2317).
  - + OPENDNSSEC-247: Signer Engine: TTL on NSEC(3) was not updated on SOA Minimum change.
- 1.4.0b1 (vs 2.1.14): added 1, removed 1
  - + OPENDNSSEC-269: Signer Engine: Crash when multiple threads access ixfr struct. 
  - - OPENDNSSEC-269: Signer Engine: Crash when multiple threads access ixfr struct.
- 1.4.0b3 (vs 2.1.14): added 10, removed 0
  - + Enforcer: Handle cases where negative cache > positive cache.
  - + Enforcer: Key material not always reused when using <SharedKeys>.
  - + Enforcer: Lacking documentation.
- 1.4.8 (vs 1.4.14): added 0, removed 1
  - - SUPPORT-147: Signer Engine: Fix a bug where zone updating via XFR got stuck because of incorrect storing SOA to disk (thanks Håvard Eidnes!).
- 1.4.11 (vs 1.4.14): added 0, removed 9
  - - OPENDNSSEC-805: Avoid full resign due to mismatch in backup file when upgrading from 1.4.8 or later.
  - - OPENDNSSEC-808: Crash on query with empty query section (thanks Håvard Eidnes).
  - - OPENDNSSEC-811,OPENDNSSEC-827,e.o.: compiler warnings and other static code analysis cleanup
- 2.0.0a3 (vs 2.1.14): added 10, removed 10
  - + OPENDNSSEC-401: 'ods-signer sign <zone> --serial <nr>' command produces seg fault when run directly on command line (i.e. not via interactive mode)
  - + OPENDNSSEC-424: Signer Engine: Respond to SOA queries from file instead of memory. Makes response non-blocking.
  - + OPENDNSSEC-425 Change "hsmutil list" output so that the table header goes to stdout not stderr
  - - Enforcer: Handle cases where negative cache > positive cache.
  - - Enforcer: Key material not always reused when using <SharedKeys>.
  - - Enforcer: Lacking documentation.
- 2.0.0a5 (vs 2.1.14): added 0, removed 4
  - - The enforcer can no longer be run on a single policy at a time anymore.  An enforce run will always process all zones.
  - - The key export method will not allow you to export keys for all zones at once (--all flag) or for a particular type of key (--keystate). It will not export ZSK 
  - - The key generate method is at this time not available, neither are the --all option at key list.
- 2.0.2 (vs 2.0.2-rel): added 4, removed 0
  - + Fixed incorrect behaviour when more than 2 ZSKs involved in roll.
  - + Migration script can handle converting a database with zones in rollover better.
  - + OPENDNSSEC-845: Memory leak on IXFR out.
- 2.1.1 (vs 2.1.14): added 1, removed 0
  - + OPENDNSSEC-882: Signerd exit code always non-zero.

## Release list

| version | tag | date | stable | own entries | DNSSEC-ish rows | note |
|---|---|---|---|---|---|---|
| 1.0.0 | 1.0.0 | 2010-02-28 | yes | 1 | 0 |  |
| 1.0.0b1 | 1.0.0b1 | 2009-10-02 | no | 13 | 4 |  |
| 1.0.0b2 | 1.0.0b2 | 2009-10-09 | no | 9 | 4 |  |
| 1.0.0b3 | 1.0.0b3 | 2009-10-16 | no | 9 | 2 |  |
| 1.0.0b4 | 1.0.0b4 | 2009-10-23 | no | 9 | 1 |  |
| 1.0.0b5 | 1.0.0b5 | 2009-10-31 | no | 13 | 2 |  |
| 1.0.0b6 | 1.0.0b6 | 2009-11-09 | no | 5 | 0 |  |
| 1.0.0b7 | 1.0.0b7 | 2009-11-16 | no | 10 | 3 |  |
| 1.0.0b8 | 1.0.0b8 | 2009-11-23 | no | 8 | 4 |  |
| 1.0.0b9 | 1.0.0b9 | 2009-11-27 | no | 8 | 2 |  |
| 1.0.0rc1 | 1.0.0rc1 | 2009-12-04 | no | 9 | 2 |  |
| 1.0.0rc2 | 1.0.0rc2 | 2009-12-16 | no | 10 | 0 |  |
| 1.0.0rc3 | 1.0.0rc3 | 2010-01-25 | no | 10 | 2 |  |
| 1.0.0rc4 | 1.0.0rc4 | 2010-02-02 | no | 5 | 1 |  |
| 1.0a1 | 1.0a1 | 2009-07-30 | no | 1 | 0 |  |
| 1.0a2 | 1.0a2 | 2009-08-14 | no | 17 | 0 |  |
| 1.0a3 | 1.0a3 | 2009-08-26 | no | 10 | 2 |  |
| 1.0a4 | 1.0a4 | 2009-09-10 | no | 8 | 4 |  |
| 1.0a5 | 1.0a5 | 2009-09-21 | no | 4 | 0 |  |
| 1.1.0 | 1.1.0 | 2010-05-26 | yes | 0 | 0 |  |
| 1.1.0rc1 | 1.1.0rc1 | 2010-04-22 | no | 35 | 8 |  |
| 1.1.0rc2 | 1.1.0rc2 | 2010-05-04 | no | 1 | 0 |  |
| 1.1.0rc3 | 1.1.0rc3 | 2010-05-14 | no | 2 | 0 |  |
| 1.1.1 | 1.1.1 | 2010-07-08 | yes | 6 | 2 |  |
| 1.1.2 | 1.1.2 | 2010-08-25 | yes | 13 | 0 |  |
| 1.1.3 | 1.1.3 | 2010-09-10 | yes | 1 | 0 |  |
| 1.2.0 | 1.2.0 | 2011-03-18 | yes | 1 | 0 |  |
| 1.2.0b1 | 1.2.0b1 | 2010-10-18 | no | 18 | 3 |  |
| 1.2.0rc1 | 1.2.0rc1 | 2010-11-17 | no | 17 | 0 |  |
| 1.2.0rc2 | 1.2.0rc2 | 2010-11-24 | no | 5 | 1 |  |
| 1.2.0rc3 | 1.2.0rc3 | 2010-12-27 | no | 13 | 7 |  |
| 1.2.1 | 1.2.1 | 2011-03-18 | yes | 17 | 0 | same commit date as 1.2.0 (both tags point at "add missing tags" commits made 2011-03-18); NEWS dates 1.2.0 as |
| 1.2.2 | 1.2.2 | 2011-08-11 | yes | 10 | 3 |  |
| 1.3.0 | 1.3.0 | 2011-07-12 | yes | 8 | 3 |  |
| 1.3.0b1 | 1.3.0b1 | 2011-03-23 | no | 10 | 4 |  |
| 1.3.0rc1 | 1.3.0rc1 | 2011-04-21 | no | 7 | 1 |  |
| 1.3.0rc2 | 1.3.0rc2 | 2011-05-18 | no | 10 | 1 |  |
| 1.3.0rc3 | 1.3.0rc3 | 2011-06-12 | no | 8 | 1 |  |
| 1.3.1 | 1.3.1 | 2011-09-07 | yes | 11 | 5 |  |
| 1.3.2 | 1.3.2 | 2011-09-13 | yes | 2 | 0 |  |
| 1.3.3 | 1.3.3 | 2011-11-17 | yes | 16 | 1 |  |
| 1.3.4 | 1.3.4 | 2011-12-09 | yes | 1 | 1 |  |
| 1.3.5 | 1.3.5 | 2012-01-23 | yes | 13 | 4 |  |
| 1.3.6 | 1.3.6 | 2012-02-16 | yes | 7 | 5 |  |
| 1.3.7 | 1.3.7 | 2012-03-13 | yes | 7 | 7 |  |
| 1.3.8 | 1.3.8 | 2012-05-09 | yes | 7 | 7 |  |
| 1.3.9 | 1.3.9 | 2012-06-15 | yes | 2 | 1 |  |
| 1.3.10 | 1.3.10 | 2012-08-10 | yes | 8 | 7 |  |
| 1.3.11 | 1.3.11 | 2012-11-13 | yes | 8 | 8 |  |
| 1.3.12 | 1.3.12 | 2013-01-23 | yes | 2 | 1 |  |
| 1.3.12rc1 | 1.3.12rc1 | 2012-11-24 | no | 0 | 0 | no own NEWS section at this tag (first header: 'OpenDNSSEC 1.3.12'); entries attributed to 1.3.12 |
| 1.3.13 | 1.3.13 | 2013-02-20 | yes | 3 | 2 |  |
| 1.3.13rc1 | 1.3.13rc1 | 2013-02-12 | no | 3 | 0 | NEWS section "OpenDNSSEC 1.3.13rc1 - 2013-02-12" (3 entries) is renamed to "1.3.13" at tag 1.3.13; entries att |
| 1.3.14 | 1.3.14 | 2013-05-16 | yes | 7 | 6 |  |
| 1.3.14rc1 | 1.3.14rc1 | 2013-05-07 | no | 7 | 0 | NEWS section "OpenDNSSEC 1.3.14rc1 - 2013-05-07" (7 entries) is renamed to "1.3.14" at tag 1.3.14; entries att |
| 1.3.15 | 1.3.15 | 2013-09-19 | yes | 7 | 7 |  |
| 1.3.15rc1 | 1.3.15rc1 | 2013-09-11 | no | 7 | 0 | NEWS section "OpenDNSSEC 1.3.15rc1 - 2013-09-11" (7 entries) is renamed to "1.3.15" at tag 1.3.15; entries att |
| 1.3.16 | 1.3.16 | 2013-12-04 | yes | 9 | 9 |  |
| 1.3.16rc1 | 1.3.16rc1 | 2013-11-27 | no | 0 | 0 | no own NEWS section at this tag (first header: 'OpenDNSSEC 1.3.16'); entries attributed to 1.3.16 |
| 1.3.16s1 | 1.3.16s1 | 2013-11-26 | no | 0 | 0 | "Snapshot 1.3.16" pre-release |
| 1.3.17 | 1.3.17 | 2014-05-06 | yes | 14 | 11 |  |
| 1.3.17rc1 | 1.3.17rc1 | 2014-04-28 | no | 14 | 0 | NEWS section "OpenDNSSEC 1.3.17rc1 - 2014-04-28" (14 entries) is renamed to "1.3.17" at tag 1.3.17; entries at |
| 1.3.18 | 1.3.18 | 2014-07-21 | yes | 7 | 4 |  |
| 1.3.18rc1 | 1.3.18rc1 | 2014-07-11 | no | 7 | 0 | NEWS section "OpenDNSSEC 1.3.18rc1 - 2014-07-11" (7 entries) is renamed to "1.3.18" at tag 1.3.18; entries att |
| 1.4.0 | 1.4.0 | 2013-04-22 | yes | 3 | 1 | 1.4 line branched before 1.3.12; 1.3.13..1.3.18 are not ancestors of any 1.4 tag |
| 1.4.0a1 | 1.4.0a1 | 2012-03-15 | no | 22 | 11 |  |
| 1.4.0a2 | 1.4.0a2 | 2012-05-24 | no | 9 | 9 |  |
| 1.4.0a3 | 1.4.0a3 | 2012-08-08 | no | 11 | 9 |  |
| 1.4.0b1 | 1.4.0b1 | 2012-09-06 | no | 11 | 11 |  |
| 1.4.0b2 | 1.4.0b2 | 2012-12-17 | no | 17 | 10 |  |
| 1.4.0b3 | 1.4.0b3 | 2013-02-20 | no | 4 | 4 |  |
| 1.4.0rc1 | 1.4.0rc1 | 2013-01-10 | no | 1 | 1 |  |
| 1.4.0rc2 | 1.4.0rc2 | 2013-01-25 | no | 5 | 4 |  |
| 1.4.0rc3 | 1.4.0rc3 | 2013-03-15 | no | 1 | 1 |  |
| 1.4.1 | 1.4.1 | 2013-06-27 | yes | 9 | 8 |  |
| 1.4.1rc1 | 1.4.1rc1 | 2013-06-19 | no | 9 | 0 | NEWS section "OpenDNSSEC 1.4.1rc1 - 2013-06-19" (9 entries) is renamed to "1.4.1" at tag 1.4.1; entries attrib |
| 1.4.2 | 1.4.2 | 2013-09-11 | yes | 11 | 9 |  |
| 1.4.2rc1 | 1.4.2rc1 | 2013-09-03 | no | 11 | 0 | NEWS section "OpenDNSSEC 1.4.2rc1 - 2013-09-03" (11 entries) is renamed to "1.4.2" at tag 1.4.2; entries attri |
| 1.4.3 | 1.4.3 | 2013-12-04 | yes | 11 | 11 |  |
| 1.4.3rc1 | 1.4.3rc1 | 2013-11-27 | no | 0 | 0 | no own NEWS section at this tag (first header: 'OpenDNSSEC 1.4.3'); entries attributed to 1.4.3 |
| 1.4.4 | 1.4.4 | 2014-03-25 | yes | 21 | 17 |  |
| 1.4.4rc1 | 1.4.4rc1 | 2014-03-17 | no | 20 | 0 | NEWS section "OpenDNSSEC 1.4.4rc1 - 2014-03-17" (20 entries) is renamed to "1.4.4" at tag 1.4.4; entries attri |
| 1.4.4rc2 | 1.4.4rc2 | 2014-03-17 | no | 1 | 0 | NEWS section "OpenDNSSEC 1.4.4rc2 - 2014-03-17" (1 entries) is renamed to "1.4.4" at tag 1.4.4; entries attrib |
| 1.4.5 | 1.4.5 | 2014-04-11 | yes | 2 | 2 |  |
| 1.4.5rc1 | 1.4.5rc1 | 2014-04-04 | no | 2 | 0 | NEWS section "OpenDNSSEC 1.4.5rc1 - 2014-04-04" (2 entries) is renamed to "1.4.5" at tag 1.4.5; entries attrib |
| 1.4.6 | 1.4.6 | 2014-07-21 | yes | 12 | 8 |  |
| 1.4.6rc1 | 1.4.6rc1 | 2014-07-11 | no | 12 | 0 | NEWS section "OpenDNSSEC 1.4.6rc1 - 2014-07-11" (12 entries) is renamed to "1.4.6" at tag 1.4.6; entries attri |
| 1.4.7 | 1.4.7 | 2014-12-04 | yes | 2 | 0 |  |
| 1.4.7-tcp_queue_fix | 1.4.7-tcp_queue_fix | 2015-12-22 | no | 0 | 0 | hotfix branch tag on 1.4.7 ("Backport tcp_waiting handling to 1.4.7"), version.m4 = 1.4.7; not a numbered rele |
| 1.4.7rc1 | 1.4.7rc1 | 2014-11-28 | no | 2 | 0 | NEWS section "OpenDNSSEC 1.4.7rc1 - 2014-11-28" (2 entries) is renamed to "1.4.7" at tag 1.4.7; entries attrib |
| 1.4.8 | 1.4.8 | 2015-09-25 | yes | 8 | 2 |  |
| 1.4.8.1 | 1.4.8.1 | 2015-10-05 | yes | 0 | 0 | 1.4.8 re-release; NEWS section still titled "1.4.8" (date changed to 2015-10-05) |
| 1.4.8.2 | 1.4.8.2 | 2015-10-05 | yes | 0 | 0 | 1.4.8 re-release; NEWS section still titled "1.4.8" (date changed to 2015-10-05) |
| 1.4.8rc1 | 1.4.8rc1 | 2015-09-25 | no | 0 | 0 | same commit as 1.4.8 |
| 1.4.9 | 1.4.9 | 2016-01-21 | yes | 6 | 2 |  |
| 1.4.9rc1 | 1.4.9rc1 | 2016-01-04 | no | 0 | 0 | no own NEWS section at this tag (first header: 'OpenDNSSEC 1.4.9 - 2016-01-04'); entries attributed to 1.4.9 |
| 1.4.10 | 1.4.10 | 2016-05-02 | yes | 9 | 5 |  |
| 1.4.11 | 1.4.11 | 2016-10-13 | yes | 9 | 6 | NEWS at 1.4.14 marks 1.4.11 "Skipped"; the tag exists and its own NEWS section (dated "2015-10-13", a typo for |
| 1.4.12 | 1.4.12 | 2016-10-17 | yes | 10 | 7 |  |
| 1.4.13 | 1.4.13 | 2017-01-20 | yes | 5 | 3 |  |
| 1.4.14 | 1.4.14 | 2017-04-28 | yes | 3 | 3 |  |
| 2.0.0 | 2.0.0 | 2016-07-06 | yes | 5 | 4 |  |
| 2.0.0-1 | 2.0.0-1 | 2016-07-15 | yes | 1 | 0 | re-issued 2.0.0 tarball ("missing dist files", version.m4 still says 2.0.0rc2); own NEWS section "OpenDNSSEC 2 |
| 2.0.0a3 | 2.0.0a3 | 2012-06-18 | no | 17 | 7 | 2012 EnforcerNG-branch alpha (predates 1.4.0); 2.0.0a4 was never tagged |
| 2.0.0a5 | 2.0.0a5 | 2015-10-28 | no | 4 | 3 | "Project transfer to NLnetLabs, performing code drop as-is for evaluation purposes only" (NEWS) |
| 2.0.0a6 | 2.0.0a6 | 2016-02-05 | no | 0 | 0 | NEWS section "OpenDNSSEC 2.0.0a6" (0 entries) is renamed to "2.0.0" at tag 2.0.0; entries attributed to 2.0.0 |
| 2.0.0b1 | 2.0.0b1 | 2016-04-14 | no | 8 | 3 |  |
| 2.0.0rc1 | 2.0.0rc1 | 2016-06-27 | no | 5 | 0 | NEWS section "None" (5 entries) is renamed to "2.0.0" at tag 2.0.0; entries attributed to 2.0.0 |
| 2.0.0rc2 | 2.0.0rc2 | 2016-06-28 | no | 5 | 0 | NEWS section "None" (5 entries) is renamed to "2.0.0" at tag 2.0.0; entries attributed to 2.0.0 |
| 2.0.1 | 2.0.1 | 2016-07-21 | yes | 3 | 0 |  |
| 2.0.2 | 2.0.2 | 2016-09-27 | yes | 3 | 3 |  |
| 2.0.2-rel | 2.0.2-rel | 2016-10-14 | no | 0 | 0 | same commit as 2.0.3 (2e0592a4); duplicate tag, listed with stable=false |
| 2.0.3 | 2.0.3 | 2016-10-14 | yes | 0 | 0 | same commit as 2.0.2-rel; NEWS at this tag still heads the section "2.0.2 - TBA", NEWS at 2.0.4 retitles it "2 |
| 2.0.4 | 2.0.4 | 2017-01-13 | yes | 2 | 0 |  |
| 2.1.0 | 2.1.0 | 2017-02-22 | yes | 23 | 13 |  |
| 2.1.0rc1 | 2.1.0rc1 | 2017-02-10 | no | 0 | 0 | no own NEWS section at this tag (first header: 'OpenDNSSEC 2.1.0 - TBD'); entries attributed to 2.1.0 |
| 2.1.1 | 2.1.1 | 2017-04-28 | yes | 4 | 4 |  |
| 2.1.2 | 2.1.2 | 2017-08-03 | yes | 7 | 7 |  |
| 2.1.3 | 2.1.3 | 2017-08-10 | yes | 8 | 8 |  |
| 2.1.4 | 2.1.4 | 2019-05-16 | yes | 8 | 3 |  |
| 2.1.4rc1 | 2.1.4rc1 | 2019-05-07 | no | 0 | 0 | no own NEWS section at this tag (first header: 'OpenDNSSEC 2.1.4 - 2019-??-?? (T.B.A)'); entries attributed to |
| 2.1.5 | 2.1.5 | 2019-11-05 | yes | 8 | 0 |  |
| 2.1.6 | 2.1.6 | 2020-02-10 | yes | 6 | 6 |  |
| 2.1.7 | 2.1.7 | 2020-10-07 | yes | 8 | 4 |  |
| 2.1.8 | 2.1.8 | 2021-02-20 | yes | 6 | 5 |  |
| 2.1.8rc1 | 2.1.8rc1 | 2020-11-18 | no | 0 | 0 | no own NEWS section at this tag (first header: 'OpenDNSSEC 2.1.8 - T.B.A.'); entries attributed to 2.1.8 |
| 2.1.8rc2 | 2.1.8rc2 | 2021-02-16 | no | 0 | 0 | no own NEWS section at this tag (first header: 'OpenDNSSEC 2.1.8rc1'); entries attributed to 2.1.8 |
| 2.1.9 | 2.1.9 | 2021-05-03 | yes | 2 | 2 |  |
| 2.1.9rc1 | 2.1.9rc1 | 2021-04-16 | no | 2 | 0 | NEWS section "OpenDNSSEC 2.1.9rc1 - 20210-04-16" (2 entries) is renamed to "2.1.9" at tag 2.1.9; entries attri |
| 2.1.10 | 2.1.10 | 2021-09-10 | yes | 5 | 3 |  |
| 2.1.10rc1 | 2.1.10rc1 | 2021-08-25 | no | 0 | 0 | no own NEWS section at this tag (first header: 'OpenDNSSEC 2.1.10 - T.B.D.'); entries attributed to 2.1.10 |
| 2.1.11 | 2.1.11 | 2022-10-17 | yes | 5 | 0 |  |
| 2.1.11-rc3 | 2.1.11-rc3 | 2022-09-22 | no | 0 | 0 | no own NEWS section at this tag (first header: 'OpenDNSSEC 2 1.11 - 2022-09-TBD'); entries attributed to 2.1.1 |
| 2.1.12 | 2.1.12 | 2022-11-08 | yes | 3 | 0 |  |
| 2.1.13 | 2.1.13 | 2023-06-26 | yes | 3 | 1 |  |
| 2.1.14 | 2.1.14 | 2024-08-22 | yes | 6 | 6 |  |
| 2.1.14rc1 | 2.1.14rc1 | 2023-09-26 | no | 0 | 0 | no own NEWS section at this tag (first header: 'OpenDNSSEC 2.1.14 RC 1 - 2023-09-10'); entries attributed to 2 |
| 20181001 | 20181001 | 2018-10-01 | no | 0 | 0 | 2.2.0-dev test drop ("code drop"/"testing release" tag message; version.m4 = 2.2.0-dev); never released as a n |
| 20181009 | 20181009 | 2018-10-09 | no | 0 | 0 | 2.2.0-dev test drop ("code drop"/"testing release" tag message; version.m4 = 2.2.0-dev); never released as a n |
| 20181106 | 20181106 | 2018-11-06 | no | 0 | 0 | 2.2.0-dev test drop ("code drop"/"testing release" tag message; version.m4 = 2.2.0-dev); never released as a n |
| 20181113 | 20181113 | 2018-11-13 | no | 0 | 0 | 2.2.0-dev test drop ("code drop"/"testing release" tag message; version.m4 = 2.2.0-dev); never released as a n |
| 20181204 | 20181204 | 2018-12-04 | no | 0 | 0 | 2.2.0-dev test drop ("code drop"/"testing release" tag message; version.m4 = 2.2.0-dev); never released as a n |
| 20190904 | 20190904 | 2019-09-04 | no | 0 | 0 | 2.2.0-dev test drop ("code drop"/"testing release" tag message; version.m4 = 2.2.0-dev); never released as a n |
| fastupdates/pre | fastupdates/pre | 2018-04-19 | no | 0 | 0 | "Temporary tag on the global repository marking the beginning of changes on behalf of fast updates" (tag messa |

## Gaps

- CVE-2012-5582 (the only inventory CVE) has no fix commit in the clone. The vulnerable eppclient (opt-in build) stayed unchanged on the 1.3 line through 1.3.18 and was deleted from the tree in 1.4.0rc1 (feee7499). fix_tag is null; the removal is recorded instead. Whether distributions patched CURLOPT_SSL_VERIFYHOST to 2 is outside the clone.
- No CVE id appears in any NEWS file (0 found) or commit message (0 found); "cve_fixes" therefore has no fix latency to report.
- The default signing algorithm switch 7 -> 8 (1.2.0b1, 00ac6896) and the 1.4.0a2 validity/lifetime change (627d8279) have no NEWS line; they are recorded from conf/kasp.xml.in diffs only.
- The 2048-bit ZSK default (aa6aa1a5, 2019-11-14) exists only on the develop branch; no released tag ships it, so 2.1.14 (2024-08-22) still installs a 1024-bit RSA ZSK example policy. Not recorded as a default change.
- NSEC3 iterations/salt in the shipped policy (Iterations 5, Salt length 8, Resalt P100D, hash alg 1) never changed between 1.0a1 and 2.1.14; the only commit that touched them ("shorter salt and less iterations" 8a21f7cb, 10/160 -> 5/8) predates the first tag. OpenDNSSEC never enforces an iteration cap; 2.1.10 and 2.1.13 only add ods-kaspcheck warnings (rows are limit-changed, advisory).
- OPENDNSSEC-843 (2.0.2 "MaxZoneTTL defaults to 0 instead of 1 day"): the code hunk in the only candidate commit (847e9e39) sets 86400, and policy.c keeps 86400 through 2.1.14; before/after taken from NEWS with attribution "approximate".
- Algorithm support arrives in layers: libhsm signing/keygen (RSA/SHA-2 1.0.0b2; DSA+GOST 1.4.0a1; ECDSA keygen 2.0.0a5; EdDSA 2.1.7) versus enforcer key generation (RSA only until 2.1.0, which adds DSA/GOST/ECDSA via hsm_key_factory.c; EdDSA 2.1.7). Rows exist for both layers; the enforcer-level date is the one a signing operator can use.
- RFC 5011: only the 1.4 line implements it (1.4.8, <RFC5011/> per KSK, opt-in). git grep -i rfc5011 on 2.1.14 finds it only in kasp.rnc/kasp2html.xsl/signconf.rnc and enforcer db fields; whether the 2.x enforcer honours the flag was not verified here.
- Pre-release tags (a/b/rc/s1, -rc3, 2.0.2-rel, 1.4.7-tcp_queue_fix, fastupdates/pre, the six 2018-2019 date tags) are stable=false. Where the rc NEWS section is renamed to the final version at the final tag, entries are attributed to the final; where the pre-release section persists (1.0.0b1..rc4, 1.1.0rc1..rc3, 1.2.0b1..rc3, 1.3.0b1..rc3, 1.4.0a1..rc3, 2.0.0a3/a5/b1) entries stay on the pre-release row.
- NEWS dates are unreliable for several tags (1.4.11/1.4.12 say 2015 for 2016 tags; 1.2.0 says 2011-01-13 for a tag committed 2011-03-18; 2.1.9rc1 says "20210-04-16"); release dates come from the tag commit only.
- Lines are not linear: 1.3.18 is not an ancestor of 1.4.0, 1.4.14 is not an ancestor of 2.0.0, 2.0.4 is not an ancestor of 2.1.0. The same fix therefore appears as different commits on each line (OPENDNSSEC-330, -549/-550, -778, -808, -890 ...); each line has its own row.
- Section "2.0.0-trunk", "EnforcerNG branch alpha1/alpha2" and "2.2 - 2017-xx-xx" in NEWS correspond to no tag; their entries are not attributed to any release.
- ods-auditor (Ruby, dnsruby) entries are kept with kind other; its algorithm coverage is a dependency property, not OpenDNSSEC code.
