# Unbound DNSSEC timeline

Generated 2026-09-29 from `out/software_repos/unbound.git` (bare clone), `data/software/cve_inventory.json` and `out/analysis/cve_crossref.json`. Machine-readable twin: `data/software/timelines/unbound.json`.

**Releases:** 214 tags (120 stable incl. 1.4.13p1/p2, 94 rc/stray), 2007-02-19 .. 2026-09-16. Changelog: `doc/Changelog` for every tag (one cumulative newest-first file with dated headers, no release markers). Release date = commit date of `<tag>^{commit}` (tagger dates before 1.6.3 are the June 2017 SVN import and are ignored).

Single master line (SVN trunk until 2017-06, git afterwards); point releases are cut on branch-X.Y.Z branches that never touch doc/Changelog, so their entries are recorded on master after the release and attributed here through the branch commits (git log <prev>..<tag>). SVN-era tags are copies of trunk and mostly not ancestors of master (git merge-base --is-ancestor release-1.0.0 master fails), but each tag commit descends from the trunk commits it contains, so git tag --contains works. Five SVN-import tags (release-1.4.13p1, release-1.4.13p2, release-1.6.3, release-1.6.5, release-1.6.8) point at trees identical to the previous release; their code and real dates are missing from the clone. Tagger dates on pre-1.6.3 tags are the June 2017 SVN import; all dates here are commit dates of <tag>^{commit}. release-1.26.0rc1 and several other rcN tags share the final release commit.

## How to verify a row

```
C=out/software_repos/unbound.git
git -C $C log -1 --format=%cI <tag>^{commit}                 # release date
git -C $C show <tag>:doc/Changelog | grep -n -F "<changelog line>"   # entry present at the tag
git -C $C show <prev_stable_tag>:doc/Changelog | grep -c -F "<changelog line>"   # 0 = new in this release
git -C $C log <prev>..<tag> -F -i --grep="<changelog line>"   # commit that carries the entry
git -C $C tag --contains <commit> | grep -x <tag>            # commit is in the release
git -C $C show <commit> -- util/config_file.c              # default value before/after
git -C $C diff --stat <prev> <tag>                          # empty for the five mis-imported re-tags
```

## Support added / defaults changed / limits changed / removed

| version | date | kind | default change | mechanism | changelog line | commit(s) | in tag |
|---|---|---|---|---|---|---|---|
| 0.3 | 2007-05-09 | support-added | no | rrsig | RRSIG parsing and storing and putting in messages. | add942bd40 | yes |
| 0.4 | 2007-07-31 | support-added | yes | validation | Option harden-glue, default is on. It will discard out of zone | - | n/a |
| 0.4 | 2007-07-31 | support-added | no | validation | config options harden-short-bufsize and harden-large-queries. | 890a3fe0a9 | yes |
| 0.5 | 2007-09-25 | support-added | no | nsec3 | validator calls nsec3 proof routines if no NSECs prove anything. | facde2ca10 | yes |
| 0.5 | 2007-09-25 | support-added | yes | nsec3-iterations | nsec3 work, config, max iterations, filter, and hash cache. | d85debfae4 | yes |
| 0.5 | 2007-09-25 | default-changed | yes | validation | default configuration is with validation enabled. | 134db23ea8 | yes |
| 0.5 | 2007-09-25 | support-added | no | validation | permissive mode feature, sets AD bit for secure, but bogus does | 60470b186e | yes |
| 0.5 | 2007-09-25 | support-added | yes | validation | val-clean-additional option, so you can turn it off. | 6890f55d17 | yes |
| 0.5 | 2007-09-25 | support-added | no | trust-anchor-5011 | trust anchors can be in config file or read from zone file, | d48e17e1dd | yes |
| 0.5 | 2007-09-25 | support-added | no | validation | validator module exists, and does nothing but pass through, | ce12d59957 | yes |
| 0.6 | 2007-11-14 | default-changed | yes | validation | harden-dnssec-stripped: yes is now default. It insists on dnssec | a06131872d | yes |
| 0.6 | 2007-11-14 | support-added | no | validation | DNSSEC-lameness detection, as LAME. | 633daf4bc7 | yes |
| 0.11 | 2008-04-24 | support-added | no | validation | implemented AD bit signaling. If a query sets AD bit (but not DO) | 8359474330 | yes |
| 1.1.0 | 2008-11-14 | default-changed | yes | validation | changed bogus-ttl default value from 900 to 60 seconds. | 00f301d35f | yes |
| 1.1.0 | 2008-11-14 | support-added | no | alg-rsa-sha2 | RSASHA256 and RSASHA512 support (using the draft in dnsext), | 8a32f9003b | yes |
| 1.1.0 | 2008-11-14 | support-added | no | validation | harden-referral-path option for query for NS records. | bf659c8362 | yes |
| 1.1.0 | 2008-11-14 | support-added | no | other | config option to set size of aggressive negative cache, | - | n/a |
| 1.1.0 | 2008-11-14 | support-added | no | trust-anchor-5011 | DLV works, straight to the dlv repository, so not for production. | 8e39c9c1cb | yes |
| 1.1.0 | 2008-11-14 | support-added | no | trust-anchor-5011 | DLV work, config file element, trust anchor read in. | 080d9d6540 | yes |
| 1.3.0 | 2009-06-03 | default-changed | yes | alg-rsa-sha2 | --enable-sha2 option. The draft rsasha256 changed its algorithm | 4b449309e5 | yes |
| 1.3.0 | 2009-06-03 | support-added | no | trust-anchor-5011 | domain-insecure: "example.com" statement added. Sets domain | 97a73402fc | yes |
| 1.3.0 | 2009-06-03 | support-added | no | trust-anchor-5011 | keys with rfc5011 REVOKE flag are skipped and not considered when | b182b66e0e | yes |
| 1.3.1 | 2009-07-08 | removal | no | trust-anchor-5011 | Removed RFC5011 REVOKE flag support. Partial 5011 support may cause | 6451748967 | yes |
| 1.3.3 | 2009-08-03 | support-added | no | validation | feature val-log-level: 1 prints validation failures so you can | 72aa0bad92 | yes |
| 1.4.0 | 2009-11-23 | default-changed | yes | alg-rsa-sha2 | RFC 5702: RSASHA256 and RSASHA512 support enabled by default. | 9a08ad419e | yes |
| 1.4.0 | 2009-11-23 | support-added | no | validation | Made new validator error string available from libunbound for | f42d27e1a2 | yes |
| 1.4.0 | 2009-11-23 | support-added | no | validation | first validation failure retry code.  Retries for data failures. | 455c3d130d | yes |
| 1.4.0 | 2009-11-23 | support-added | no | trust-anchor-5011 | autotrust probing. | 902323da2f | yes |
| 1.4.0 | 2009-11-23 | support-added | no | trust-anchor-5011 | autotrust options: add-holddown, del-holddown, keep-missing. | 7d90b75ce8 | yes |
| 1.4.0 | 2009-11-23 | support-added | no | alg-gost | configure --enable-gost for GOST support, experimental | 1f4222aa94 | yes |
| 1.4.2 | 2010-03-08 | support-added | no | dnskey | prefetch-key option that performs DNSKEY queries earlier in the | bcd1ac7599 | yes |
| 1.4.6 | 2010-07-22 | default-changed | yes | dnskey | Fix RFC4035 compliance with 2.2 statement that the DNSKEY at apex | 518504ff5c | yes |
| 1.4.7 | 2010-11-05 | default-changed | yes | alg-gost | GOST code enabled by default (RFC 5933). | 93ffd44608 | yes |
| 1.4.7 | 2010-11-05 | support-added | no | trust-anchor-5011 | unbound-anchor working, it creates or updates a root.key file. | 1c2a8d977c | yes |
| 1.4.8 | 2011-01-19 | default-changed | yes | validation | algorithm compromise protection using the algorithms signalled in | daab92e954 | yes |
| 1.4.8 | 2011-01-19 | support-added | no | validation | harden-below-nxdomain option, default off (because very old | 78cc3d8ae1 | yes |
| 1.4.11 | 2011-06-23 | support-added | no | validation | feature, ignore-cd-flag: yesno to provide dnssec to legacy servers. | ca38a8bd55 | yes |
| 1.4.17 | 2012-05-18 | default-changed | yes | alg-ecdsa | ECDSA support (RFC 6605) by default. Use --disable-ecdsa for older | 53a448ffae | yes |
| 1.4.17 | 2012-05-18 | support-added | no | alg-ecdsa | implement draft-ietf-dnsext-ecdsa-04; which is in IETF LC; This | 924789d877 | yes |
| 1.4.19 | 2012-12-06 | default-changed | yes | other | RFC6725 deprecates RSAMD5: this DNSKEY algorithm is disabled. | 5e5e89b9f5 | yes |
| 1.4.21 | 2013-09-10 | support-added | no | trust-anchor-5011 | add unbound-control insecure_add and insecure_remove for the | 5dca6deca9 | yes |
| 1.5.0 | 2014-11-11 | support-added | no | trust-anchor-5011 | Add ub_ctx_add_ta_autr function to add a RFC5011 automatically | 973f7a2225 | yes |
| 1.5.0 | 2014-11-11 | support-added | no | cds-cdnskey | type CDS and CDNSKEY types in sldns. | 3e510bedee | yes |
| 1.5.4 | 2015-06-29 | deprecation | no | trust-anchor-5011 | DLV is going to be decommissioned.  Advice to stop using it, and | b5f391d845 | yes |
| 1.5.4 | 2015-06-29 | support-added | no | validation | Fix #644: harden-algo-downgrade option, if turned off, fixes the | 49250ef291 | yes |
| 1.5.5 | 2015-10-01 | default-changed | yes | validation | Change default of harden-algo-downgrade to off.  This is lenient | e65fdc31aa | yes |
| 1.5.5 | 2015-10-01 | support-added | no | trust-anchor-5011 | Added permit-small-holddown config to debug fast 5011 rollover. | ee263cf6c5 | yes |
| 1.5.9 | 2016-06-02 | support-added | no | validation | disable-dnssec-lame-check config option from Charles Walker. | 7fcec8102f | yes |
| 1.5.9 | 2016-06-02 | support-added | no | other | OpenSSL 1.1.0 portability, --disable-dsa configure option. | fbae76885a | yes |
| 1.6.1 | 2017-02-14 | default-changed | yes | trust-anchor-5011 | Include root trust anchor id 20326 in unbound-anchor. | 367c3f034e | yes |
| 1.6.2 | 2017-04-13 | default-changed | yes | ds-digest | harden-algo-downgrade: no also makes unbound more lenient about | 5a0ae9a055 | yes |
| 1.6.2 | 2017-04-13 | support-added | no | trust-anchor-5011 | Add trustanchor.unbound CH TXT that gets a response with a number | 6c456aa15e | yes |
| 1.6.2 | 2017-04-13 | support-added | no | other | --disable-sha1 disables SHA1 support in RRSIG, so from DNSKEY and | 05215e8e7d | yes |
| 1.6.4 | 2017-06-22 | support-added | no | alg-eddsa | Support for the ED25519 algorithm with openssl (from openssl 1.1.1). | 8c4e7ffb14 | yes |
| 1.6.4 | 2017-06-22 | support-added | no | trust-anchor-5011 | Implemented trust anchor signaling using key tag query. | a511d5d95e | yes |
| 1.6.6 | 2017-09-13 | support-added | no | alg-eddsa | Fix #1365: Add Ed25519 support using libnettle. | e396684a54 | yes |
| 1.6.7 | 2017-10-10 | default-changed | yes | trust-anchor-5011 | Set trust-anchor-signaling default to yes | ac9b95ca0c | yes |
| 1.7.0 | 2018-03-12 | support-added | no | validation | Aggressive use of NSEC implementation. Use cached NSEC records to | 77f78152ee | yes |
| 1.7.1 | 2018-04-26 | support-added | yes | trust-anchor-5011 | Added root-key-sentinel support | 4d06c36342 | yes |
| 1.7.1 | 2018-04-26 | support-added | no | alg-eddsa | ED448 support. | 1f9caf5805 | yes |
| 1.8.0 | 2018-09-04 | default-changed | yes | validation | Set defaults to yes for a number of options to increase speed and | e0745813f4 | yes |
| 1.10.0 | 2020-02-20 | default-changed | yes | other | Fix #153: Disable validation for DSA algorithms.  RFC 8624 | 68ff1730ac | yes |
| 1.11.0 | 2020-07-20 | default-changed | yes | trust-anchor-5011 | Merge #225 from akhait: KSK-2010 has been revoked. It removes the | 6320776b25 | yes |
| 1.12.0 | 2020-10-01 | removal | no | trust-anchor-5011 | Merge PR #284 and Fix #246: Remove DLV entirely from Unbound. | f35293caba | yes |
| 1.13.2 | 2021-08-05 | limit-changed | yes | nsec3-iterations | Move the NSEC3 max iterations count in line with the 150 value | 11b3ebc386 | yes |
| 1.13.2 | 2021-08-05 | support-added | no | other | Merge PR #317: ZONEMD Zone Verification, with RFC 8976 support. | d6e55a586c | yes |
| 1.15.0 | 2022-02-03 | default-changed | yes | validation | Change aggressive-nsec default to yes. | 32c3bbd249 | yes |
| 1.16.0 | 2022-05-27 | support-added | no | other | Merge PR #604: Add basic support for EDE (RFC8914). | 0ce36e8289 | yes |
| 1.16.1 | 2022-07-04 | default-changed | yes | validation | Merge PR #660 from Petr Menšík: Sha1 runtime insecure. | 2fba248ebe | yes |
| 1.18.0 | 2023-08-25 | support-added | no | validation | Add harden-unknown-additional option. It removes | 8df1e58209 | yes |
| 1.19.0 | 2023-11-02 | support-added | no | validation | Merge #944: Disable EDNS DO. | 908e1cb11a | yes |
| 1.21.0 | 2024-08-09 | default-changed | yes | trust-anchor-5011 | Add root key 38696 from 2024 for DNSSEC validation. It is added | f094f4ea3c | yes |
| 1.22.0 | 2024-10-16 | limit-changed | yes | validation | Fix to limit NSEC and NSEC3 TTL when aggressive nsec is | 24e0f0ab7e | yes |
| 1.22.0 | 2024-10-16 | support-added | no | validation | Merge patch to fix for glue that is outside of zone, with | 1e0cf1e86b | yes |
| 1.23.0 | 2025-04-11 | default-changed | yes | validation | Make the default value of module-config "validator iterator" | 35dbbcb2f5 | yes |
| 1.25.0 | 2026-04-23 | limit-changed | yes | rrsig | Fix to shorten RRSIG count in scrubber, this protects against | db1fe8b475 | yes |
| 1.26.0 | 2026-07-24 | limit-changed | yes | validation | Fix that validator caps number of ANY RRsets it can | fb2745024a | yes |

77 rows. `(!)` marks a commit not contained in the tag; `n/a` = no commit found by message grep (entry is still at the tag).

## Default changes (before / after)

| version | date | change | before | after | on upgrade | opt-in | commits | attribution |
|---|---|---|---|---|---|---|---|---|
| 0.5 | 2007-09-25 | validation on by default (module-config "validator iterator") | module-config default "iterator": validator not loaded | module-config default "validator iterator" (util/config_file.c); validation is performed once a trust anchor is configured (none is built in) | yes | no | 134db23ea8 | exact |
| 0.5 | 2007-09-25 | NSEC3 iteration cap introduced with NSEC3 support | no NSEC3 support | val-nsec3-keysize-iterations default "1024 150 2048 500 4096 2500"; higher iteration counts make the zone insecure | yes | no | d85debfae4 | exact |
| 0.6 | 2007-11-14 | harden-dnssec-stripped on by default | no check that DNSSEC data is present for zones under a trust anchor | cfg->harden_dnssec_stripped = 1: answers under a trust anchor that lack DNSSEC data are bogus | yes | no | a06131872d | exact |
| 1.1.0 | 2008-11-14 | bogus-ttl default 900 -> 60 seconds | bogus results cached 900 s | bogus results cached 60 s | yes | no | 00f301d35f | exact |
| 1.3.0 | 2009-06-03 | RSASHA256/RSASHA512 disabled by default (--enable-sha2 needed) | RSASHA256/512 validated (draft numbers, since 1.1.0) | algorithms 8/10 compiled out unless --enable-sha2 (configure.ac) | yes | no | 4b449309e5 | exact |
| 1.4.0 | 2009-11-23 | RSASHA256/RSASHA512 (RFC 5702) enabled by default | off unless --enable-sha2 (1.3.0) | on by default; --disable-sha2 to turn off | yes | no | 9a08ad419e | exact |
| 1.4.6 | 2010-07-22 | DNSKEY RRset must be signed by every algorithm listed in the parent DS set (RFC 4035 2.2) | a DNSKEY set validated if any DS algorithm verified it | the apex DNSKEY set must be signed with all algorithms present in the DS RRset; otherwise bogus | yes | no | 518504ff5c | exact |
| 1.4.7 | 2010-11-05 | GOST (RFC 5933) enabled by default | off unless --enable-gost (1.4.0; 1.4.5 "GOST disabled-by-default") | on by default when OpenSSL provides GOST; --disable-gost to turn off | yes | no | 93ffd44608 | exact |
| 1.4.8 | 2011-01-19 | algorithm-downgrade protection from DS-signalled algorithms | one verifying algorithm sufficed for a chain of trust step (1.4.7 "if one key matches it's good enough") | data must be signed with every algorithm signalled in the DS set (also for trust anchors, DLV and 5011); no knob until harden-algo-downgrade (1.5.4) | yes | no | daab92e954 | exact |
| 1.4.17 | 2012-05-18 | ECDSA (RFC 6605) enabled by default | ECDSA P-256/P-384 (algorithms 13/14) not supported (experimental --enable-ecdsa in the same release cycle) | on by default; --disable-ecdsa for older OpenSSL | yes | no | d71a1ba0c2, 53a448ffae | exact |
| 1.4.19 | 2012-12-06 | RSAMD5 (algorithm 1) disabled | RSAMD5 signatures validated | RSAMD5 treated as unsupported (zone insecure); contrib/patch_rsamd5_enable.diff re-enables | yes | no | 5e5e89b9f5 | exact |
| 1.5.5 | 2015-10-01 | harden-algo-downgrade default yes -> no | cfg->harden_algo_downgrade = 1 (option added 1.5.4 for the behaviour introduced in 1.4.8) | cfg->harden_algo_downgrade = 0: one verifying algorithm suffices again | yes | no | e65fdc31aa | exact |
| 1.6.1 | 2017-02-14 | unbound-anchor built-in root keys gain KSK-2017 (key id 20326) | built-in root anchor: KSK-2010 (19036) only | built-in root anchors: KSK-2010 + KSK-2017 (smallapp/unbound-anchor.c) | no | no | 367c3f034e | exact |
| 1.6.2 | 2017-04-13 | DS digest algorithm downgrade tolerated when harden-algo-downgrade is no (the default) | DS digest-type downgrade always refused (1.1.0: "no longer possible to downgrade to SHA1") | with harden-algo-downgrade: no (default since 1.5.5) any supported DS digest suffices | yes | no | 4d7d32c846 | exact |
| 1.6.7 | 2017-10-10 | trust-anchor-signaling (RFC 8145) on by default | cfg->trust_anchor_signaling = 0 (option added 1.6.4) | cfg->trust_anchor_signaling = 1: _ta-<keytag> queries sent to the root | yes | no | ac9b95ca0c | exact |
| 1.7.1 | 2018-04-26 | root-key-sentinel on by default | no KSK sentinel processing | cfg->root_key_sentinel = 1 (root-key-sentinel: yes) | yes | no | 4d06c36342 | exact |
| 1.8.0 | 2018-09-04 | harden-below-nxdomain on by default | cfg->harden_below_nxdomain = 0 (option added 1.4.8) | cfg->harden_below_nxdomain = 1: names under a DNSSEC-secure cached NXDOMAIN are answered NXDOMAIN | yes | no | e0745813f4 | exact |
| 1.10.0 | 2020-02-20 | DSA (algorithms 3, 6) validation disabled by default | DSA validated when the crypto library supports it (--disable-dsa since 1.5.9) | configure defaults to DSA off (RFC 8624 section 3.1); DSA-signed zones treated as insecure unless --enable-dsa | yes | no | 68ff1730ac | exact |
| 1.11.0 | 2020-07-20 | unbound-anchor built-in root keys drop KSK-2010 (19036) | built-in root anchors: KSK-2010 + KSK-2017 | built-in root anchors: KSK-2017 only | no | no | 201c158377, 6320776b25 | exact |
| 1.13.2 | 2021-08-05 | NSEC3 iteration cap lowered to 150 for all key sizes | val-nsec3-keysize-iterations "1024 150 2048 500 4096 2500" (since 0.5) | val-nsec3-keysize-iterations "1024 150 2048 150 4096 150" (util/config_file.c, doc/unbound.conf.5.in) | yes | no | 11b3ebc386 | exact |
| 1.15.0 | 2022-02-03 | aggressive-nsec (RFC 8198) on by default | cfg->aggressive_nsec = 0 (feature added 1.7.0) | cfg->aggressive_nsec = 1: NXDOMAIN/NODATA/wildcard answers synthesised from cached NSEC/NSEC3 | yes | no | 32c3bbd249 | exact |
| 1.16.1 | 2022-07-04 | SHA-1 refused by the crypto library at runtime makes RSASHA1 zones insecure, not bogus | an RSASHA1/RSASHA1-NSEC3-SHA1 signature the library cannot verify fails validation (bogus) | when EVP refuses SHA-1 (FIPS, crypto-policies) the algorithm is treated as unsupported, so such zones validate as insecure (validator/val_secalgo.c) | yes | no | e102aea751, 2fba248ebe | exact |
| 1.19.1 | 2024-02-13 | KeyTrap (CVE-2023-50387) validation work limits | unbounded RRSIG/DNSKEY combinations tried per RRset | MAX_VALIDATE_RRSIGS 8, MAX_DS_MATCH_FAILURES 4, MAX_VALIDATE_AT_ONCE 8, MAX_VALIDATION_SUSPENDS 16 (validator/val_sigcrypt.h, validator/validator.h); exceeding them fails validation | yes | no | 882903f2fa | exact |
| 1.19.1 | 2024-02-13 | NSEC3 hash-calculation cap (CVE-2023-50868) | NSEC3 closest-encloser proofs hashed every label without a bound | MAX_NSEC3_CALCULATIONS 8 per message, MAX_NSEC3_ERRORS -1 (validator/val_nsec3.h) | yes | no | 92f2a1ca69 | exact |
| 1.21.0 | 2024-08-09 | unbound-anchor built-in root keys gain KSK-2024 (key id 38696) | built-in root anchors: KSK-2017 (20326) only | built-in root anchors: KSK-2017 + KSK-2024 (smallapp/unbound-anchor.c) | no | no | f094f4ea3c | exact |
| 1.22.0 | 2024-10-16 | NSEC/NSEC3 TTL capped for aggressive use (RFC 9077) | cached NSEC/NSEC3 used for synthesis for their full TTL | NSEC/NSEC3 TTL limited to the SOA minimum for aggressive-nsec synthesis | yes | no | 24e0f0ab7e | exact |
| 1.23.0 | 2025-04-11 | module-config default "validator iterator" regardless of build options | --enable-subnet (and similar) builds defaulted to a module-config that inserted the extra module | default module-config is always "validator iterator"; extra modules must be configured explicitly | yes | no | 35dbbcb2f5 | exact |
| 1.25.0 | 2026-04-23 | RRSIG count in the scrubber capped (iter-scrub-rrsig: 8) | any number of RRSIGs per RRset accepted from upstream | cfg->iter_scrub_rrsig = 8: extra RRSIGs dropped by the scrubber | yes | no | db1fe8b475 | exact |
| 1.26.0 | 2026-07-24 | validator caps the number of ANY RRsets it validates | every RRset in a qtype ANY answer validated | number of validated ANY RRsets capped and the validation wait timer shortened | yes | no | fb2745024a | exact |
| 1.26.1 | 2026-09-16 | Retrap (CVE-2026-85501): val-clean-additional off by default; validation and hash attempt budgets | cfg->val_clean_additional = 1 (since 0.5); no per-query budget of validation attempts | cfg->val_clean_additional = 0; cfg->val_validation_attempts = 32; cfg->val_hash_attempts = 32 (util/config_file.c at release-1.26.1) | yes | no | 13b6717f17 | exact |

30 rows. Rows with 'on upgrade = no' (unbound-anchor built-in key list) only matter when root.key is created or repaired by unbound-anchor.

## CVE fixes

| CVE | NVD published | fix tag | fix date | latency (days) | DNSSEC | fix commit(s) | note |
|---|---|---|---|---|---|---|---|
| CVE-2009-3602 | 2009-10-13 | 1.4.0rc1 | 2009-11-13 | 31 | yes | 1a02ab895b | CVE id never appears in the Changelog or log. Fix = 1a02ab89 "Fix check for signatures." (validator/val_nsec3.c, 2009-10-07) matching the 1.4.0 Changelog entry "Fixed security bug where the signatures for NSEC3 records were not checked ... 1.3.4 release with o |
| CVE-2009-4008 | 2011-06-02 | - | - | - | yes | - | no entry or commit names this CVE; NVD says fixed before 1.4.4. Candidate in the 1.4.4 entries: df9db1a0 "Fix bug#305: pkt_dname_tolower could read beyond end of buffer or get into an endless loop" (2010-04-09), but the NVD text ("does not send responses for s |
| CVE-2010-0969 | 2010-03-16 | 1.4.3 | 2010-03-11 | -5 | no | ae83a2b706 | CVE id not in the Changelog. Mapped by NVD text ("does not properly align structures on 64-bit platforms", before 1.4.3) to the 1.4.3 entry "fix for memory alignment in struct sock_list allocation." (ae83a2b7/6cf3327d, 2010-03-11). |
| CVE-2011-1922 | 2011-05-31 | 1.4.10 | 2011-05-25 | -6 | no | a79861c86c |  |
| CVE-2011-4528 | - | 1.4.14 | 2011-12-19 | - | no | 0916e1d0ea | not in by_product.unbound (only in fixes.unbound), so no NVD date in the inventory. |
| CVE-2014-8602 | 2014-12-11 | 1.5.1 | 2014-12-08 | -3 | no | f7039d8a59 |  |
| CVE-2017-15105 | 2018-01-23 | 1.7.0rc1 | 2018-03-06 | 42 | yes | eff62cecac, 2a6250e3fb | fix 2a6250e3 (2018-01-19) is first contained by release-1.7.0rc1 in the clone. The vendor point release 1.6.8 (2018-01-19) carried it, but the release-1.6.8 tag is a bare re-tag of 1.6.7 (tree identical, dated 2017-10-10), so 1.6.8 cannot be used as the fix ta |
| CVE-2019-16866 | 2019-10-03 | 1.9.4 | 2019-10-03 | 0 | no | b60c4a472c, facc6c6541 | inventory attributes the fix to facc6c65 (master merge, first in 1.9.6rc1); the 1.9.4 branch tag is a single commit b60c4a47 whose tree diff against 1.9.3 changes util/data/msgparse.c (the NOTIFY uninitialised-memory fix), so the first tag with the fix is rele |
| CVE-2019-18934 | 2019-11-19 | 1.9.5 | 2019-11-19 | 0 | no | 09845779d5, 34e52a4313 |  |
| CVE-2019-25031 | 2021-04-27 | 1.9.6rc1 | 2019-12-05 | -509 | no | f887552763 | X41 D-Sec audit finding; vendor disputes. Mapped by NVD text to the 1.9.6 audit-fix commit; first tag 1.9.6rc1. NVD says "before 1.9.5" but 1.9.5 is a 1.9.4-branch point release (only the ipsecmod fix); the audit fixes are on master in 1.9.6. |
| CVE-2019-25032 | 2021-04-27 | 1.9.6rc1 | 2019-12-05 | -509 | no | 226298bbd3 | X41 D-Sec audit finding; vendor disputes. Mapped by NVD text to the matching "reported by X41 D-Sec" commit in 1.9.6 (first tag 1.9.6rc1). |
| CVE-2019-25033 | 2021-04-27 | 1.9.6rc1 | 2019-12-05 | -509 | no | 09707fc403 | X41 D-Sec audit finding; vendor disputes. Mapped by NVD text to the matching "reported by X41 D-Sec" commit in 1.9.6 (first tag 1.9.6rc1). |
| CVE-2019-25034 | 2021-04-27 | 1.9.6rc1 | 2019-12-05 | -509 | no | a3545867fc | X41 D-Sec audit finding; vendor disputes. Mapped by NVD text to the matching "reported by X41 D-Sec" commit in 1.9.6 (first tag 1.9.6rc1). |
| CVE-2019-25035 | 2021-04-27 | 1.9.6rc1 | 2019-12-05 | -509 | no | fa23ee8f31 | X41 D-Sec audit finding; vendor disputes. Mapped by NVD text to the matching "reported by X41 D-Sec" commit in 1.9.6 (first tag 1.9.6rc1). |
| CVE-2019-25036 | 2021-04-27 | 1.9.6rc1 | 2019-12-05 | -509 | no | f5e06689d1 | X41 D-Sec audit finding; vendor disputes. Mapped by NVD text to the matching "reported by X41 D-Sec" commit in 1.9.6 (first tag 1.9.6rc1). |
| CVE-2019-25037 | 2021-04-27 | 1.9.6rc1 | 2019-12-05 | -509 | no | d2eb78e871 | X41 D-Sec audit finding; vendor disputes. Mapped by NVD text to the matching "reported by X41 D-Sec" commit in 1.9.6 (first tag 1.9.6rc1). |
| CVE-2019-25038 | 2021-04-27 | 1.9.6rc1 | 2019-12-05 | -509 | no | 02080f6b18 | X41 D-Sec audit finding; vendor disputes. Mapped by NVD text to the matching "reported by X41 D-Sec" commit in 1.9.6 (first tag 1.9.6rc1). |
| CVE-2019-25039 | 2021-04-27 | 1.9.6rc1 | 2019-12-05 | -509 | no | 02080f6b18 | X41 D-Sec audit finding; vendor disputes. Mapped by NVD text to the matching "reported by X41 D-Sec" commit in 1.9.6 (first tag 1.9.6rc1). |
| CVE-2019-25040 | 2021-04-27 | 1.9.6rc1 | 2019-12-05 | -509 | no | 2d444a5037 | X41 D-Sec audit finding; vendor disputes. Mapped by NVD text to the matching "reported by X41 D-Sec" commit in 1.9.6 (first tag 1.9.6rc1). |
| CVE-2019-25041 | 2021-04-27 | 1.9.6rc1 | 2019-12-05 | -509 | no | 2d444a5037, d2eb78e871 | X41 D-Sec audit finding; vendor disputes. Mapped by NVD text to the matching "reported by X41 D-Sec" commit in 1.9.6 (first tag 1.9.6rc1). |
| CVE-2019-25042 | 2021-04-27 | 1.9.6rc1 | 2019-12-05 | -509 | no | 6c3a0b54ed | X41 D-Sec audit finding; vendor disputes. Mapped by NVD text to the matching "reported by X41 D-Sec" commit in 1.9.6 (first tag 1.9.6rc1). |
| CVE-2020-10772 | 2020-11-27 | - | - | - | no | - | Red Hat downstream issue (incomplete RHEL 7 backport of CVE-2020-12662); no upstream commit. Not applicable. |
| CVE-2020-12662 | 2020-05-19 | 1.10.1 | 2020-05-19 | 0 | no | ba0f382eee, 50d4c893c4 |  |
| CVE-2020-12663 | 2020-05-19 | 1.10.1 | 2020-05-19 | 0 | no | ba0f382eee, 50d4c893c4 |  |
| CVE-2020-28935 | 2020-12-07 | 1.13.0rc1 | 2020-11-24 | -13 | no | 19f8f4d9f9, ad38783297 | fix 19f8f4d9 is first in release-1.13.0rc1; latency against that tag. |
| CVE-2022-30698 | 2022-08-01 | 1.16.2 | 2022-08-01 | 0 | no | f6753a0f10 |  |
| CVE-2022-30699 | 2022-08-01 | 1.16.2 | 2022-08-01 | 0 | no | f6753a0f10 |  |
| CVE-2022-3204 | 2022-09-26 | 1.16.3 | 2022-09-21 | -5 | no | 137719522a |  |
| CVE-2023-50387 | 2024-02-14 | 1.19.1 | 2024-02-13 | -1 | yes | 882903f2fa |  |
| CVE-2023-50868 | 2024-02-14 | 1.19.1 | 2024-02-13 | -1 | yes | 92f2a1ca69 | not in by_product.unbound; NVD date 2024-02-14 taken from by_product.bind9 (same CVE). |
| CVE-2024-1931 | 2024-03-07 | 1.19.2 | 2024-03-07 | 0 | no | 5b37cd6e4c | inventory fix_release 1.19.3 (master commit 326ba265); the branch fix 5b37cd6e is in release-1.19.2 (2024-03-07). |
| CVE-2024-33655 | - | 1.20.0rc1 | 2024-05-01 | - | no | c3206f4568 |  |
| CVE-2024-8508 | 2024-10-03 | 1.21.1 | 2024-10-03 | 0 | no | a1b25f0296, b7c61d7cc2 | inventory fix_release 1.22.0 (master commit a1b25f02); the branch fix b7c61d7c is in release-1.21.1 (2024-10-03). |
| CVE-2025-11411 | - | 1.24.1 | 2025-10-22 | - | no | f6269baa60, a33f0638e1 |  |
| CVE-2025-5994 | 2025-07-16 | 1.23.1 | 2025-07-16 | 0 | no | f49e6ccecd, 5bf82f2464 | not in by_product.unbound; NVD date 2025-07-16 from by_keyword "DNS cache poisoning". |
| CVE-2026-14586 | - | 1.25.2 | 2026-07-22 | - | no | f157c691bb |  |
| CVE-2026-32665 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | 01dfd2f466 |  |
| CVE-2026-32792 | 2026-05-20 | 1.25.1 | 2026-05-20 | 0 | no | a587535c5d |  |
| CVE-2026-33278 | 2026-05-20 | 1.25.1 | 2026-05-20 | 0 | yes | 6a31e470f8 |  |
| CVE-2026-40622 | 2026-05-20 | 1.25.1 | 2026-05-20 | 0 | no | 13ec8d0f26, 8d8fa42266 |  |
| CVE-2026-40691 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | f54e0791ba |  |
| CVE-2026-41292 | 2026-05-20 | 1.25.1 | 2026-05-20 | 0 | no | ef5ca84360 |  |
| CVE-2026-41637 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | 27f22b8808 |  |
| CVE-2026-42534 | 2026-05-20 | 1.25.1 | 2026-05-20 | 0 | no | a794c87578 |  |
| CVE-2026-42923 | 2026-05-20 | 1.25.1 | 2026-05-20 | 0 | yes | c343fff3a4 |  |
| CVE-2026-42944 | 2026-05-20 | 1.25.1 | 2026-05-20 | 0 | no | fe946ba4e9 |  |
| CVE-2026-42955 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | 13ec8d0f26 |  |
| CVE-2026-42959 | 2026-05-20 | 1.25.1 | 2026-05-20 | 0 | yes | 94d5babaee |  |
| CVE-2026-42960 | 2026-05-20 | 1.25.1 | 2026-05-20 | 0 | no | 8ae4b4545d |  |
| CVE-2026-44390 | 2026-05-20 | 1.25.1 | 2026-05-20 | 0 | no | 138fb48eac, dae7a37974 |  |
| CVE-2026-44608 | 2026-05-20 | 1.25.1 | 2026-05-20 | 0 | no | 75b6dba593 |  |
| CVE-2026-44621 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | f52a9e864b |  |
| CVE-2026-44687 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | yes | 1e1940383a |  |
| CVE-2026-44690 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | yes | f7637a4f18 |  |
| CVE-2026-46582 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | yes | fea0ff550b |  |
| CVE-2026-50045 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | yes | 364ac737f7 |  |
| CVE-2026-50046 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | 1ad8d4c395 |  |
| CVE-2026-50243 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | yes | 02b16de1ae |  |
| CVE-2026-50248 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | yes | cf5e6e89a5, 3530c81e29 |  |
| CVE-2026-50251 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | e180b06298 |  |
| CVE-2026-50252 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | 804cff4c15 |  |
| CVE-2026-52863 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | 8c702de175 |  |
| CVE-2026-54478 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | 8a15ffee62 |  |
| CVE-2026-55708 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | c29ff70f6a |  |
| CVE-2026-55717 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | 2ce2ca3691 |  |
| CVE-2026-55973 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | 96f8755520 |  |
| CVE-2026-55990 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | ae1b3810cc |  |
| CVE-2026-55991 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | aac261cbb3 |  |
| CVE-2026-56416 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | yes | 4b1635e194 |  |
| CVE-2026-56444 | 2026-07-22 | 1.25.2 | 2026-07-22 | 0 | no | 84d9682dd0 |  |
| CVE-2026-77860 | - | 1.26.1 | 2026-09-16 | - | no | bd71e3b8a6 |  |
| CVE-2026-77955 | - | 1.26.1 | 2026-09-16 | - | yes | 565651cd02 |  |
| CVE-2026-78227 | - | 1.26.1 | 2026-09-16 | - | no | 7914901915 |  |
| CVE-2026-80225 | - | 1.26.1 | 2026-09-16 | - | no | e619ead2db |  |
| CVE-2026-81634 | - | 1.26.1 | 2026-09-16 | - | yes | 3d65973d38 |  |
| CVE-2026-81642 | - | 1.26.1 | 2026-09-16 | - | no | 8c2e0fd6cc |  |
| CVE-2026-82717 | - | 1.26.1 | 2026-09-16 | - | no | 0d4a6a63dd |  |
| CVE-2026-82720 | - | 1.26.1 | 2026-09-16 | - | no | eba3d35ad4 |  |
| CVE-2026-85501 | - | 1.26.1 | 2026-09-16 | - | yes | 13b6717f17 | Retrap; fixed in release-1.26.1 (branch-1.26.1) after the inventory was generated; not in the inventory, NVD date unknown here. |

Negative latency = fix released before NVD publication (coordinated disclosure or late CVE assignment). fix tag = first tag (rc included) whose history contains a fix commit; `first_stable_tag` is in the JSON.

## Branch point releases without Changelog at the tag

- 1.8.3 (2018-12-04): 0 commit(s) on the branch; point release on a branch: doc/Changelog at the tag equals release-1.8.2; entries below are the branch commits (git log 
- 1.9.4 (2019-10-03): 1 commit(s) on the branch; point release on a branch: doc/Changelog at the tag equals release-1.9.3; entries below are the branch commits (git log 
- 1.9.5 (2019-11-19): 1 commit(s) on the branch; point release on a branch: doc/Changelog at the tag equals release-1.9.4; entries below are the branch commits (git log 
- 1.10.1 (2020-05-19): 1 commit(s) on the branch; point release on a branch: doc/Changelog at the tag equals release-1.10.0; entries below are the branch commits (git log
- 1.19.1 (2024-02-13): 2 commit(s) on the branch; point release on a branch: doc/Changelog at the tag equals release-1.19.0; entries below are the branch commits (git log
- 1.19.2 (2024-03-07): 1 commit(s) on the branch; point release on a branch: doc/Changelog at the tag equals release-1.19.1; entries below are the branch commits (git log
- 1.21.1 (2024-10-03): 1 commit(s) on the branch; point release on a branch: doc/Changelog at the tag equals release-1.21.0; entries below are the branch commits (git log
- 1.23.1 (2025-07-16): 1 commit(s) on the branch; point release on a branch: doc/Changelog at the tag equals release-1.23.0; entries below are the branch commits (git log
- 1.24.1 (2025-10-22): 1 commit(s) on the branch; point release on a branch: doc/Changelog at the tag equals release-1.24.0; entries below are the branch commits (git log
- 1.24.2 (2025-11-26): 1 commit(s) on the branch; point release on a branch: doc/Changelog at the tag equals release-1.24.1; entries below are the branch commits (git log
- 1.25.2 (2026-07-22): 24 commit(s) on the branch; point release on a branch: doc/Changelog at the tag equals release-1.25.1; entries below are the branch commits (git log
- 1.26.1 (2026-09-16): 10 commit(s) on the branch; point release on a branch: doc/Changelog at the tag equals release-1.26.0; entries below are the branch commits (git log

## Post-hoc Changelog edits (text at release-1.26.1 differs from text at the release tag)

- 0.3: added 0, removed 1
  - - [7 May 2007] edns extended error reponses once the edns record from the query has successfully been parsed.
- 0.4: added 0, removed 5
  - - [25 May 2007] packed rrset key has type and class as easily accessable struct members. they are still kept in network format for fast msg encode.
  - - [30 May 2007] iterator reponse typing.
  - - [17 July 2007] forward per zone in iterator. takes precendence over stubs.
- 0.5: added 0, removed 2
  - - [5 September 2007] if you configure many trust anchors, parent trust anchors can securely deny existance of child trust anchors, if validated.
  - - [24 September 2007] multiple nsec3 paramaters in message test.
- 0.7.1: added 0, removed 1
  - - [19 November 2007] version 0.71: * includes tpkg fixes to kill daemons at end of test * includes nsec/rrsig not downcasing fixup from dnssec-bis-updat
- 0.7.2: added 0, removed 3
  - - [19 November 2007] for 0.7.2: * fixup for donotq matching.
  - - [19 November 2007] version 0.7.1: * includes tpkg fixes to kill daemons at end of test * includes nsec/rrsig not downcasing fixup from dnssec-bis-upda
  - - [3 December 2007] fixup building in a subdirectory. (for 0.7.2)
- 0.9: added 0, removed 4
  - - [11 February 2008] ub_val to ub_ for library api (from trunk).
  - - [25 January 2008] fixup race problems from opensll in rand init from library, with a mutex around the rand init.
  - - [11 February 2008] nicer statistic output (from trunk).
- 1.0.2: added 0, removed 6
  - - [6 August 2008] patch for scrubber that removes ends of cnames, no more dnames from cache. remove more irrelevant rrsets from the message.
  - - [19 July 2008] #198: fixup manpage to suggest entropy chroot fix.
  - - [4 August 2008] bug #201 fixup from trunk; fixes segfault on exit cleanup
- 1.1.0: added 0, removed 1
  - - [17 October 2008] harden referral path now also validates the root after priming. it looks up the root ns authoritatively as well as the root servers 
- 1.2.0: added 0, removed 4
  - - [13 January 2009] tag updated with:
  - - [13 January 2009] fix lame marking
  - - [13 January 2009] iana portlist updated
- 1.3.0: added 0, removed 1
  - - [5 February 2009] configure option --with-ldns-builtin forces the use of the inluded ldns package with the unbound source. the -i include is put befor
- 1.3.1: added 0, removed 1
  - - [8 June 2009] removed rfc5011 revoke flag support. partial 5011 support may cause inadvertant behaviour.
- 1.4.10: added 0, removed 2
  - - [25 March 2011] fix assertion failure when unbound generates an empty error reply in response to a query, cve-2011-1922 vu#531342.
  - - [25 March 2011] release 1.4.10.
- 1.4.12: added 0, removed 1
  - - [30 June 2011] tag relase 1.4.11, trunk is 1.4.12 development.
- 1.4.14: added 0, removed 1
  - - [5 December 2011] fix malloc detection and double defintion.
- 1.4.18: added 0, removed 1
  - - [30 July 2012] tag 1.4.18rc2.
- 1.4.22: added 0, removed 1
  - - [20 February 2014] be lenient when a nsec nameerror response with rcode=nxdomain is received. this is okay according 4035, but not after revising exis
- 1.5.4: added 0, removed 2
  - - [29 May 2015] fix that unparseable error responses are ratelimited.
  - - [10 May 2015] change syntax of particular validator error to be easier for machine parse, swap rrset and ip adres info so it looks like: validation fa
- 1.5.9: added 0, removed 1
  - - [18 April 2016] fix some malformed reponses to edns queries get fallback to nonedns.
- 1.6.0: added 0, removed 4
  - - [22 Novenber 2016] qname minimisation uses qtype=a, therefore always check cache for this type in harden-below-nxdomain functionality.
  - - [22 Novenber 2016] fix nsec ent wildcard check. matching wildcard does not have to be a subdomain of the nsec owner.
  - - [22 Novenber 2016] added unit test for qname minimisation + harden below nxdomain synergy.
- 1.6.1: added 0, removed 2
  - - [14 February 2017] tag 1.6.1rc3.
  - - [5 January 2017] fix #1185: source ip rate limiting, patch from larissa feng.
- 1.6.2: added 0, removed 3
  - - [27 February 2017] fix #1227: fix that unbound control allows weak ciphersuits.
  - - [24 March 2017] fix to prevent non-referal query from being cached as referal when the no_cache_store flag was set.
  - - [7 March 2017] fix #1230: swig version 2.0.0 is required for pythonmod, with 1.3.40 it crashes when running repeatly unbound-control reload.
- 1.6.6: added 0, removed 1
  - - [13 September 2017] tag 1.6.6rc2
- 1.7.0: added 0, removed 2
  - - [12 March 2018] tag 1.7.0rc3.
  - - [1 February 2018] fix unaligned structure making a false positive in checklock unitialised memory.
- 1.7.1: added 0, removed 1
  - - [26 April 2018] tag for 1.7.1rc1 release.
- 1.7.2: added 0, removed 2
  - - [23 May 2018] use accept4 to speed up incoming tcp (and tls) connections, available on linux and freebsd.
  - - [4 June 2018] tag for 1.7.2rc1
- 1.7.3: added 0, removed 1
  - - [18 June 2018] fix that control-use-cert: no works for 127.0.0.1 to disable certs.
- 1.8.0: added 0, removed 1
  - - [4 September 2018] tag for 1.8.0rc1 release.
- 1.8.1: added 0, removed 1
  - - [1 October 2018] tag for release 1.8.1rc1.
- 1.9.0: added 0, removed 1
  - - [28 January 2019] set version to 1.9.0 for release.
- 1.9.2: added 0, removed 1
  - - [12 June 2019] 1.9.2rc3 release candidate tag.
- 1.9.3: added 0, removed 2
  - - [1 August 2019] fix to remove unused test for task_probe existance.
  - - [22 August 2019] 1.9.3rc2 release candidate tag.
- 1.9.6: added 0, removed 1
  - - [3 December 2019] fix text around serial arithmatic used for rrsig times to refer to correct rfc number.
- 1.12.0: added 0, removed 1
  - - [6 August 2020] merge pr #284 and fix #246: remove dlv entirely from unbound. the dlv has been decommisioned and in unbound 1.5.4, in 2015, there was 
- 1.13.0: added 0, removed 1
  - - [30 November 2020] tag for the 1.13.0rc4 release.
- 1.13.2: added 0, removed 2
  - - [10 February 2021] merge pr #420 from dyunwei: doh not responsing with "http2_query_read_done failure" logged.
  - - [23 March 2021] travis, analyzer disabled on test without debug, that does not run anway. turn off failing tests except one. update ios test to xcode 
- 1.14.0: added 0, removed 1
  - - [1 December 2021] configure is set to 1.14.0, and release branch.
- 1.16.0: added 0, removed 1
  - - [27 May 2022] version is set to 1.16.0 for release. release tag 1.16.0rc1.
- 1.16.1: added 0, removed 1
  - - [4 July 2022] tag for 1.16.1rc1 release.
- 1.17.1: added 0, removed 1
  - - [11 November 2022] fix #779: [doc] missing documention in ub_resolve_event() for callback parameter was_ratelimited.
- 1.18.0: added 0, removed 1
  - - [23 August 2023] tag for 1.18.0rc1 release.
- ... 4 more in the JSON

## Gaps

- Five SVN-import tags are bare re-tags with trees identical to the previous release (git diff --stat is empty): release-1.4.13p1 and release-1.4.13p2 (= release-1.4.13), release-1.6.3 (= 1.6.2), release-1.6.5 (= 1.6.4), release-1.6.8 (= 1.6.7). Their point-release code and their real release dates are not in the clone; the dates recorded for them are the predecessor's tag-commit dates and must not be used. Their changelog_entries are empty and total_entries is 0 for that reason. 1.6.5 = 1.6.4 + the two-anchor RFC 5011 fix (per the 1.6.6 Changelog entry); 1.6.8 = 1.6.7 + the CVE-2017-15105 fix.
- release-1.3.4 is also mis-imported: its tree is 1.3.3 plus test data and iana_ports, without the NSEC3 signature fix (CVE-2009-3602) that the 1.4.0 Changelog says was the only content of the 1.3.4 release. The fix commit (1a02ab89, 2009-10-07) is first contained by release-1.4.0rc1.
- CVE-2009-4008: no Changelog entry or commit names it and the NVD text does not map unambiguously to a 1.4.4 entry; fix_tag left null.
- CVE-2020-10772 is a Red Hat downstream issue with no upstream fix; marked not applicable.
- CVE-2019-25031..25042 (X41 D-Sec audit, vendor-disputed) are mapped to 1.9.6 audit-fix commits by NVD description text only (attribution approximate); NVD's 'before 1.9.5' version bound does not match the clone, where 1.9.5 is a 1.9.4-branch point release.
- Ten CVEs fixed in release-1.26.1 (2026-09-16; CVE-2026-85501 Retrap, -82717, -77860, -81642, -81634, -77955, -78227, -82720, -80225) and CVE-2026-14586 are not in data/software/cve_inventory.json (generated before that release), so their NVD publication dates and latencies are unknown here; the rows carry the branch commits only.
- Point releases cut on branch-X.Y.Z (1.9.4, 1.9.5, 1.10.1, 1.19.1, 1.19.2, 1.21.1, 1.23.1, 1.24.1, 1.24.2, 1.25.2, 1.26.1) never update doc/Changelog at the tag; their entries here are the branch commit messages, and the corresponding Changelog text (added on master afterwards) is attributed by the tag-diff method to the next master release as well. A verifier will find the text with git show <next master tag>:doc/Changelog and the code with git log <prev>..<tag>.
- release-1.26.1 is the newest tag; the Changelog text for its fixes exists only on master (not at any tag). news_edits compares against release-1.26.1's Changelog, which therefore lacks those entries.
- Commit lookup for support-added/default-changed/limit-changed entries is by fixed-string message grep of the Changelog line in <prev>..<tag> (then --all). Entries whose evidence.commits is empty have commit_note set; the change is still documented by the Changelog line at the tag. Where an SVN commit bundles several Changelog lines the found commit may carry more than the one entry.
- Kind assignment (support-added/default-changed/limit-changed/deprecation/removal) was applied by hand to 86 entries listed in the curation; all other kept entries are kind 'other' (or 'cve-fix' when a CVE id appears). Mechanism labels on uncurated entries are keyword heuristics.
- Changelog entries dated more than 60 days before the previous stable release (656 total, mostly the master entries that follow a branch point release, plus a handful of post-hoc edits such as the 2007-dated line re-attributed to 1.5.7 and the 1.24.0 re-edits of the 1.3.1/1.12.0 lines) are flagged late_entry and were not treated as new work.
- Validation is enabled by default since 0.5 only in the sense that the validator module is loaded; Unbound ships no built-in trust anchor in unbound.conf, so a stock configuration without auto-trust-anchor-file/trust-anchor-file does not validate. Whether a given deployment validated therefore depends on packaging (e.g. distribution unbound-anchor units), which this clone cannot show.
- Algorithm support dates before the SVN-to-git switch (RSASHA256/512 draft 1.1.0, GOST 1.4.0/1.4.7, ECDSA 1.4.17) rely on the Changelog line plus the configure.ac commit; the ldns tarball bundled at the time also had to support the algorithm, which is not tracked here.
- The unbound.conf.5 man page could not be grepped for a val-clean-additional default sentence at 1.26.0/1.26.1 (pattern not matched); the before/after values for the 1.26.1 row come from util/config_file.c only.
