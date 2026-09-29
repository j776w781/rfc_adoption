# PowerDNS Recursor (pdns-rec) DNSSEC timeline

Generated 2026-09-29 from `out/software_repos/pdns.git` (bare clone shared with the Authoritative Server; only `rec-*` tags are used), `data/software/cve_inventory.json` and `out/analysis/cve_crossref.json`. Machine-readable twin: `data/software/timelines/pdns-rec.json`.

**Releases:** 262 `rec-*` tags (174 stable, 88 alpha/beta/rc or alias), 2006-04-20 .. 2026-09-02. Release date = commit date of `<tag>^{commit}` (`git -C out/software_repos/pdns.git log -1 --format=%cI <tag>^{commit}`).

The recursor shares the clone with the Authoritative Server; only rec-* tags are used. Since 4.x every minor series X.Y lives on a rel/rec-X.Y.x branch; point releases are tagged on the branch, so a fix that master carries under one hash reaches a stable release under a cherry-picked hash on the branch. rec-3-0/rec-3-0-1 are hyphenated aliases of rec-3.0/rec-3.0.1 (same commit); rec-5.0.0-rc2 and rec-5.0.0, and rec-5.4.0-rc1 and rec-5.4.0, share one commit each.

## How to verify a row

```
C=out/software_repos/pdns.git
git -C $C log -1 --format=%cI <tag>^{commit}                          # release date
git -C $C show <changelog_source_tag>:<changelog_path> | grep -n -F "<changelog line>"   # entry present in the section for <version>
git -C $C log <prev>..<tag> --grep="<pullreq or words>"                 # commit that carries the change
git -C $C tag --contains <commit> | grep -x <tag>                       # commit is in the release
git -C $C show <commit> -- pdns/recursordist/rec-lua-conf.hh pdns/recursordist/settings/table.py pdns/pdns_recursor.cc   # default value before/after
```

## Support added / defaults changed / limits changed / removed

| version | date | kind | default change | mechanism | changelog line | commit(s) | in tag |
|---|---|---|---|---|---|---|---|
| 3.0 | 2006-04-20 | default-changed | yes | other | **Warning**: Because of recent DNS based denial of service attacks, running an open recursor has become a s... | - | n/a |
| 3.1.2 | 2006-06-27 | support-added | no | other | Recursor would send out differing TTLs when receiving a misconfigured, standards violating, RRSET with diff... | - | n/a |
| 3.1.2 | 2006-06-27 | support-added | no | other | Some operators may want to follow RFC 2181 paragraph 5.2 and 5.4. This harms performance and does not solve... | - | n/a |
| 3.1.2 | 2006-06-27 | support-added | no | other | Misconfigured domains, with a broken nameserver in the parent zone, should now work better. Changes motivat... | - | n/a |
| 3.5 | 2013-04-15 | default-changed | yes | other | Our local-nets definition (used as a default for some settings) now includes the networks from RFC 3927 and... | - | n/a |
| 4.0.0-beta1 | 2016-05-27 | support-added | no | validation | #3905 Add a dnssec=process-no-validate option and make it default | - | n/a |
| 4.0.0-rc1 | 2016-06-08 | support-added | no | trust-anchor-5011 | #3910 Add (Negative) Trust Anchor management | - | n/a |
| 4.0.0 | 2016-07-08 | support-added | no | validation | #4077 Add DNSSEC validation statistics | - | n/a |
| 4.0.4 | 2017-01-13 | support-added | no | validation | commit 5aa64e6, commit 5f4242e and commit 0f707cd: DNSSEC: Implement keysearch based on zone-cuts | - | n/a |
| 4.0.5 | 2017-06-13 | support-added | no | alg-eddsa | This release adds ed25519 (algorithm 15) support for DNSSEC and adds the 2017 DNSSEC root key. If you do DN... | - | n/a |
| 4.0.6 | 2017-07-04 | support-added | no | alg-eddsa | This release features a fix for the ed25519 verifier. This verifier hashed the message before verifying, re... | - | n/a |
| 4.1.0-alpha1 | 2017-07-18 | support-added | no | validation | Implement "on-the-fly" DNSSEC processing. This places the DNSSEC processing alongside the regular recursion... | - | n/a |
| 4.1.0-rc1 | 2017-10-09 | support-added | no | alg-eddsa | Add DNSSEC test vectors for RSA, ECDSA, ed25519 and GOST. | - | n/a |
| 4.1.0-rc3 | 2017-11-17 | removal | no | validation | The third Release Candidate adds support for Botan 2.x (and removes support for Botan 1.10!), has a lot of ... | - | n/a |
| 4.1.0-rc3 | 2017-11-17 | support-added | no | validation | Add the DNSSEC validation state to the DNSQuestion Lua object (although the ability to update the validatio... | - | n/a |
| 4.1.0 | 2017-12-04 | support-added | no | validation | This is the first release in the 4.1 train. The full release notes can be read on the blog. This is a major... | - | n/a |
| 4.3.0-alpha3 | 2019-10-28 | support-added | no | other | Implement RFC 8020 "NXDOMAIN: There Really Is Nothing Underneath" | - | n/a |
| 4.5.0-alpha1 | 2021-01-13 | support-added | no | other | Add support for rfc8914: Extended DNS Errors. | - | n/a |
| 4.5.0-alpha3 | 2021-03-08 | default-changed | yes | validation | Change dnssec default to `process`. | - | n/a |
| 4.5.0-alpha3 | 2021-03-08 | support-added | no | validation | Implement rfc 8198 - Aggressive Use of DNSSEC-Validated Cache. | - | n/a |
| 4.5.0-alpha3 | 2021-03-08 | support-added | no | validation | Add validation state to protobuf message. | - | n/a |
| 4.5.0-beta1 | 2021-03-24 | support-added | no | other | Implement EDNS0 padding (rfc7830) for outgoing responses. | - | n/a |
| 4.9.0-rc1 | 2023-06-13 | support-added | no | validation | Add feature to switch off unsupported DNSSEC algos, either automatically or manually. | - | n/a |
| 5.1.0-alpha1 | 2024-05-14 | support-added | no | validation | Introduce command to set aggressive NSEC cache size. | - | n/a |
| 5.1.3 | 2024-10-24 | support-added | no | other | Implement rfc6303 special zones (mostly v6 reverse mappings). | - | n/a |
| 5.2.0-alpha1 | 2024-11-11 | support-added | no | other | Implement rfc6303 special zones (mostly v6 reverse mappings). | - | n/a |
| 5.0.10 | 2025-04-08 | support-added | no | trust-anchor-5011 | Add new root trust anchor. | - | n/a |
| 5.1.4 | 2025-04-08 | support-added | no | trust-anchor-5011 | Add new root trust anchor. | - | n/a |
| 5.4.0-beta1 | 2026-01-26 | support-added | no | other | dnsrecords: Add RESINFO DNS Record (RFC 9606). | - | n/a |

## Default changes (detail)

(pending)

## CVE fixes

| CVE | NVD published | fix commit(s) | first tag containing fix | fix date | first stable tag | latency (days) | note |
|---|---|---|---|---|---|---|---|
| (pending) | | | | | | | |

## Gaps

- STAGE 2 ONLY: default_changes, cve_fixes, news_edits and per-entry commit evidence are pending; release list and changelog_entries (keyword-filtered, auto-classified, unreviewed) are populated.

## Release list

| tag | version | released | stable | commit | changelog section source |
|---|---|---|---|---|---|
| rec-3-0 | 3.0 (alias of rec-3.0) | 2006-04-20 | yes | 8af92496cde4 | - |
| rec-3.0 | 3.0 | 2006-04-20 | yes | 8af92496cde4 | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3-0-1 | 3.0.1 (alias of rec-3.0.1) | 2006-04-25 | yes | 832255b42ef1 | - |
| rec-3.0.1 | 3.0.1 | 2006-04-25 | yes | 832255b42ef1 | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.1.2 | 3.1.2 | 2006-06-27 | yes | 5a5fef568e1f | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.1.4 | 3.1.4 | 2006-11-16 | yes | d766ffc90869 | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.1.7.1 | 3.1.7.1 | 2009-08-02 | yes | a6f83ed5cbee | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.1.7.2 | 3.1.7.2 | 2009-12-28 | yes | 514472d39d3a | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.2 | 3.2 | 2010-03-06 | yes | ded69cde032b | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.3 | 3.3 | 2010-09-21 | yes | 018b331fd505 | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.3.1 | 3.3.1 | 2010-12-18 | yes | 2c9cf4e0e526 | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.5-rc1 | 3.5-rc1 | 2013-01-25 | no | d6700386baa5 | - |
| rec-3.5-rc3 | 3.5-rc3 | 2013-03-28 | no | 2fde441eab26 | - |
| rec-3.5-rc4 | 3.5-rc4 | 2013-04-05 | no | 9aa0922bb31d | - |
| rec-3.5-rc5 | 3.5-rc5 | 2013-04-08 | no | 24b8c97b23bd | - |
| rec-3.5 | 3.5 | 2013-04-15 | yes | 8c848191f80d | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.5.1 | 3.5.1 | 2013-05-03 | yes | 9d539d73d052 | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.5.2 | 3.5.2 | 2013-06-03 | yes | d08e0cecf65a | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.5.3 | 3.5.3 | 2013-09-17 | yes | c73022077f24 | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.6.0-rc1 | 3.6.0-rc1 | 2014-05-30 | no | b6c4a26509ef | - |
| rec-3.6.0 | 3.6.0 | 2014-06-20 | yes | 3da09fdd6a00 | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.6.1 | 3.6.1 | 2014-09-09 | yes | 6148f0cbee06 | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.6.2 | 3.6.2 | 2014-10-30 | yes | ab14b4fed2ae | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.7.0-rc1 | 3.7.0-rc1 | 2015-01-21 | no | e10d31141b57 | - |
| rec-3.7.0-rc2 | 3.7.0-rc2 | 2015-02-04 | no | f8f243b01215 | - |
| rec-3.7.0 | 3.7.0 | 2015-02-09 | yes | 60ba1e645265 | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.7.1 | 3.7.1 | 2015-02-11 | yes | d63f0d83631c | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.7.2 | 3.7.2 | 2015-04-21 | yes | dc02ebf65ab4 | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.6.3 | 3.6.3 | 2015-04-21 | yes | 64425b951d5a | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.6.4 | 3.6.4 | 2015-06-08 | yes | 0b510b67dda0 | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-3.7.3 | 3.7.3 | 2015-06-09 | yes | b453a2097529 | master:pdns/recursordist/docs/changelog/pre-4.0.rst |
| rec-4.0.0-alpha1 | 4.0.0-alpha1 | 2015-12-24 | no | 744f43704e06 | master:pdns/recursordist/docs/changelog/4.0.rst |
| rec-4.0.0-alpha2 | 4.0.0-alpha2 | 2016-03-09 | no | b7a6009a93a9 | master:pdns/recursordist/docs/changelog/4.0.rst |
| rec-4.0.0-alpha3 | 4.0.0-alpha3 | 2016-05-10 | no | 22d2001802b0 | master:pdns/recursordist/docs/changelog/4.0.rst |
| rec-4.0.0-beta1 | 4.0.0-beta1 | 2016-05-27 | no | 0cad91850c99 | master:pdns/recursordist/docs/changelog/4.0.rst |
| rec-4.0.0-rc1 | 4.0.0-rc1 | 2016-06-08 | no | 51039eab7889 | master:pdns/recursordist/docs/changelog/4.0.rst |
| rec-4.0.0 | 4.0.0 | 2016-07-08 | yes | ba64cecd4176 | master:pdns/recursordist/docs/changelog/4.0.rst |
| rec-4.0.1 | 4.0.1 | 2016-07-29 | yes | c3a33379007e | master:pdns/recursordist/docs/changelog/4.0.rst |
| rec-4.0.2 | 4.0.2 | 2016-08-26 | yes | 9d7fd146ebfc | master:pdns/recursordist/docs/changelog/4.0.rst |
| rec-4.0.3 | 4.0.3 | 2016-09-06 | yes | 1824fd19a34c | master:pdns/recursordist/docs/changelog/4.0.rst |
| rec-3.7.4 | 3.7.4 | 2017-01-12 | yes | ed2de597f393 | - |
| rec-4.0.4 | 4.0.4 | 2017-01-13 | yes | 9388f1be79e4 | master:pdns/recursordist/docs/changelog/4.0.rst |
| rec-4.0.5-rc1 | 4.0.5-rc1 | 2017-05-18 | no | 306843845529 | - |
| rec-4.0.5-rc2 | 4.0.5-rc2 | 2017-06-01 | no | 79ed38c2911f | - |
| rec-4.0.5 | 4.0.5 | 2017-06-13 | yes | db8868071c3d | master:pdns/recursordist/docs/changelog/4.0.rst |
| rec-4.0.6 | 4.0.6 | 2017-07-04 | yes | f8023470fdd6 | master:pdns/recursordist/docs/changelog/4.0.rst |
| rec-4.1.0-alpha1 | 4.1.0-alpha1 | 2017-07-18 | no | a8bbd3057cf9 | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.1.0-rc1 | 4.1.0-rc1 | 2017-10-09 | no | de9ba7f79c74 | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.1.0-rc2 | 4.1.0-rc2 | 2017-10-30 | no | 6425370d60b7 | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.1.0-rc3 | 4.1.0-rc3 | 2017-11-17 | no | be5c4d7e7314 | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.0.7 | 4.0.7 | 2017-11-27 | yes | 1e61e68fdd6f | master:pdns/recursordist/docs/changelog/4.0.rst |
| rec-4.1.0 | 4.1.0 | 2017-12-04 | yes | 80da1b4773cb | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.0.8 | 4.0.8 | 2017-12-11 | yes | fdd1fca63fc4 | master:pdns/recursordist/docs/changelog/4.0.rst |
| rec-4.1.1 | 4.1.1 | 2018-01-22 | yes | d4ac9dc14a9a | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.1.2 | 4.1.2 | 2018-03-27 | yes | 431819add3aa | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.1.3 | 4.1.3 | 2018-05-22 | yes | 337d664beff8 | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.1.4 | 4.1.4 | 2018-08-31 | yes | 0a98a51fb1fb | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.1.5 | 4.1.5 | 2018-11-06 | yes | def520c76649 | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.0.9 | 4.0.9 | 2018-11-06 | yes | 8fca8ec92abb | master:pdns/recursordist/docs/changelog/4.0.rst |
| rec-4.1.6 | 4.1.6 | 2018-11-07 | yes | 19fe9781d0fa | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.1.7 | 4.1.7 | 2018-11-09 | yes | 8c7029b6158e | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.1.8 | 4.1.8 | 2018-11-26 | yes | e412a9494918 | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.1.9 | 4.1.9 | 2019-01-21 | yes | 924b641ce41f | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.1.10 | 4.1.10 | 2019-01-22 | yes | 4dcb0559597b | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.2.0-alpha1 | 4.2.0-alpha1 | 2019-01-25 | no | 72386ccce9ac | master:pdns/recursordist/docs/changelog/4.2.rst |
| rec-4.1.11 | 4.1.11 | 2019-01-30 | yes | 5a5d87c13cb6 | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.1.12 | 4.1.12 | 2019-04-02 | yes | 8703bd7a4256 | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.2.0-beta1 | 4.2.0-beta1 | 2019-04-30 | no | 7f0bf8eab543 | master:pdns/recursordist/docs/changelog/4.2.rst |
| rec-4.1.13 | 4.1.13 | 2019-05-14 | yes | 851572589db9 | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.2.0-rc1 | 4.2.0-rc1 | 2019-05-21 | no | 9a41797f61c6 | master:pdns/recursordist/docs/changelog/4.2.rst |
| rec-4.1.14 | 4.1.14 | 2019-06-12 | yes | b0d4221818cd | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.2.0-rc2 | 4.2.0-rc2 | 2019-06-19 | no | 9c9b31869b2a | master:pdns/recursordist/docs/changelog/4.2.rst |
| rec-4.2.0 | 4.2.0 | 2019-07-12 | yes | 2e63a37703dd | master:pdns/recursordist/docs/changelog/4.2.rst |
| rec-4.3.0-alpha1 | 4.3.0-alpha1 | 2019-09-03 | no | 0ae57d6967a8 | master:pdns/recursordist/docs/changelog/4.3.rst |
| rec-4.3.0-alpha2 | 4.3.0-alpha2 | 2019-10-28 | no | 1fd8eedff0ca | master:pdns/recursordist/docs/changelog/4.3.rst |
| rec-4.3.0-alpha3 | 4.3.0-alpha3 | 2019-10-28 | no | e1638c1174c9 | master:pdns/recursordist/docs/changelog/4.3.rst |
| rec-4.1.15 | 4.1.15 | 2019-11-27 | yes | 67663bab8f65 | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.2.1 | 4.2.1 | 2019-11-27 | yes | ce435fc3ef4b | master:pdns/recursordist/docs/changelog/4.2.rst |
| rec-4.3.0-beta1 | 4.3.0-beta1 | 2019-12-10 | no | 38361ad8362c | master:pdns/recursordist/docs/changelog/4.3.rst |
| rec-4.3.0-beta2 | 4.3.0-beta2 | 2020-01-15 | no | c14a762fb9d5 | master:pdns/recursordist/docs/changelog/4.3.rst |
| rec-4.3.0-rc1 | 4.3.0-rc1 | 2020-01-28 | no | a48db83b5fb6 | master:pdns/recursordist/docs/changelog/4.3.rst |
| rec-4.3.0-rc2 | 4.3.0-rc2 | 2020-02-17 | no | 7f76c239aa59 | master:pdns/recursordist/docs/changelog/4.3.rst |
| rec-4.3.0 | 4.3.0 | 2020-02-26 | yes | f8e019026f5a | master:pdns/recursordist/docs/changelog/4.3.rst |
| rec-4.4.0-alpha0 | 4.4.0-alpha0 | 2020-03-02 | no | 3cd3245a18ed | - |
| rec-4.4.0-alpha1 | 4.4.0-alpha1 | 2020-04-20 | no | 8b82ded0ae94 | master:pdns/recursordist/docs/changelog/4.4.rst |
| rec-4.3.1 | 4.3.1 | 2020-05-19 | yes | 474236432a3b | master:pdns/recursordist/docs/changelog/4.3.rst |
| rec-4.2.2 | 4.2.2 | 2020-05-19 | yes | 130c3986cee3 | master:pdns/recursordist/docs/changelog/4.2.rst |
| rec-4.1.16 | 4.1.16 | 2020-05-19 | yes | aeba5fdaad53 | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.1.17 | 4.1.17 | 2020-06-30 | yes | 93535261ce9f | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.2.3 | 4.2.3 | 2020-06-30 | yes | 0cc0497f0b33 | master:pdns/recursordist/docs/changelog/4.2.rst |
| rec-4.3.2 | 4.3.2 | 2020-06-30 | yes | 3fb1225d0e0f | master:pdns/recursordist/docs/changelog/4.3.rst |
| rec-4.3.3 | 4.3.3 | 2020-07-14 | yes | 1a7db21d28ee | master:pdns/recursordist/docs/changelog/4.3.rst |
| rec-4.2.4 | 4.2.4 | 2020-07-14 | yes | 31f5e27adb63 | master:pdns/recursordist/docs/changelog/4.2.rst |
| rec-4.4.0-alpha2 | 4.4.0-alpha2 | 2020-07-16 | no | c22723c57335 | master:pdns/recursordist/docs/changelog/4.4.rst |
| rec-4.4.0-beta1 | 4.4.0-beta1 | 2020-08-28 | no | 52494c26ec4d | master:pdns/recursordist/docs/changelog/4.4.rst |
| rec-4.3.4 | 4.3.4 | 2020-09-01 | yes | e003a498f0cb | master:pdns/recursordist/docs/changelog/4.3.rst |
| rec-4.4.0-rc1 | 4.4.0-rc1 | 2020-09-18 | no | 87ca8045ba69 | master:pdns/recursordist/docs/changelog/4.4.rst |
| rec-4.5.0-alpha0 | 4.5.0-alpha0 | 2020-09-18 | no | b124aa85a4c3 | - |
| rec-4.4.0-rc2 | 4.4.0-rc2 | 2020-10-02 | no | af8b15fd74c7 | master:pdns/recursordist/docs/changelog/4.4.rst |
| rec-4.1.18 | 4.1.18 | 2020-10-12 | yes | 77409aab0be4 | master:pdns/recursordist/docs/changelog/4.1.rst |
| rec-4.2.5 | 4.2.5 | 2020-10-13 | yes | 70b6d0d36de2 | master:pdns/recursordist/docs/changelog/4.2.rst |
| rec-4.3.5 | 4.3.5 | 2020-10-13 | yes | d37778a45851 | master:pdns/recursordist/docs/changelog/4.3.rst |
| rec-4.4.0 | 4.4.0 | 2020-10-13 | yes | c3fcaf52b503 | master:pdns/recursordist/docs/changelog/4.4.rst |
| rec-4.3.6 | 4.3.6 | 2020-11-16 | yes | 135c23388eea | master:pdns/recursordist/docs/changelog/4.3.rst |
| rec-4.4.1 | 4.4.1 | 2020-11-16 | yes | 5b732f82f821 | master:pdns/recursordist/docs/changelog/4.4.rst |
| rec-4.4.2 | 4.4.2 | 2020-12-09 | yes | a3ae31a05df9 | master:pdns/recursordist/docs/changelog/4.4.rst |
| rec-4.5.0-alpha1 | 4.5.0-alpha1 | 2021-01-13 | no | f0abe7ad8e66 | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.5.0-alpha2 | 4.5.0-alpha2 | 2021-03-04 | no | e95f1270a294 | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.5.0-alpha3 | 4.5.0-alpha3 | 2021-03-08 | no | 7cc0c15478f0 | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.3.7 | 4.3.7 | 2021-03-19 | yes | e72c568f2d11 | master:pdns/recursordist/docs/changelog/4.3.rst |
| rec-4.5.0-beta1 | 4.5.0-beta1 | 2021-03-24 | no | 3b04f99d1241 | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.6.0-alpha0 | 4.6.0-alpha0 | 2021-03-26 | no | 0acc352c208b | - |
| rec-4.4.3 | 4.4.3 | 2021-03-29 | yes | 8c642b6c559a | master:pdns/recursordist/docs/changelog/4.4.rst |
| rec-4.5.0-beta2 | 4.5.0-beta2 | 2021-04-09 | no | 086d46d22e3d | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.5.0-rc1 | 4.5.0-rc1 | 2021-04-26 | no | 4cb17151025e | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.5.0 | 4.5.0 | 2021-05-07 | yes | 8acf42e9ad4c | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.5.1 | 4.5.1 | 2021-05-10 | yes | b17a76a74e19 | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.4.4 | 4.4.4 | 2021-05-11 | yes | da6f1d1dc9a8 | master:pdns/recursordist/docs/changelog/4.4.rst |
| rec-4.5.2 | 4.5.2 | 2021-06-07 | yes | 9dff4a783f2a | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.5.3 | 4.5.3 | 2021-06-23 | yes | aa4d818094e7 | - |
| rec-4.5.4 | 4.5.4 | 2021-06-30 | yes | f9c4f82b7a58 | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.4.5 | 4.4.5 | 2021-07-28 | yes | 93b658eb43be | master:pdns/recursordist/docs/changelog/4.4.rst |
| rec-4.5.5 | 4.5.5 | 2021-07-28 | yes | 390b8c374701 | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.6.0-alpha1 | 4.6.0-alpha1 | 2021-09-24 | no | 57ec75fc8a21 | master:pdns/recursordist/docs/changelog/4.6.rst |
| rec-4.4.6 | 4.4.6 | 2021-10-06 | yes | 4649fa2d41d7 | master:pdns/recursordist/docs/changelog/4.4.rst |
| rec-4.5.6 | 4.5.6 | 2021-10-07 | yes | 9de0dc6acfee | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.6.0-alpha2 | 4.6.0-alpha2 | 2021-10-21 | no | fb1e4416a0de | master:pdns/recursordist/docs/changelog/4.6.rst |
| rec-4.4.7 | 4.4.7 | 2021-10-27 | yes | 403e4a06cee6 | master:pdns/recursordist/docs/changelog/4.4.rst |
| rec-4.5.7 | 4.5.7 | 2021-10-27 | yes | 18b3d6981991 | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.6.0-beta1 | 4.6.0-beta1 | 2021-11-08 | no | bed227797005 | master:pdns/recursordist/docs/changelog/4.6.rst |
| rec-4.6.0-beta2 | 4.6.0-beta2 | 2021-11-16 | no | 55e1368ad436 | master:pdns/recursordist/docs/changelog/4.6.rst |
| rec-4.7.0-alpha0 | 4.7.0-alpha0 | 2021-11-30 | no | e6f9befcb2e0 | - |
| rec-4.6.0-rc1 | 4.6.0-rc1 | 2021-12-01 | no | d20512df6f3d | master:pdns/recursordist/docs/changelog/4.6.rst |
| rec-4.6.0 | 4.6.0 | 2021-12-14 | yes | 267458e54fe9 | master:pdns/recursordist/docs/changelog/4.6.rst |
| rec-4.7.0-alpha1 | 4.7.0-alpha1 | 2022-02-24 | no | 48bb84567e39 | master:pdns/recursordist/docs/changelog/4.7.rst |
| rec-4.6.1 | 4.6.1 | 2022-03-16 | yes | ab4a4b861a01 | master:pdns/recursordist/docs/changelog/4.6.rst |
| rec-4.5.8 | 4.5.8 | 2022-03-16 | yes | 22980701dbd4 | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.4.8 | 4.4.8 | 2022-03-16 | yes | 50c085395e81 | master:pdns/recursordist/docs/changelog/4.4.rst |
| rec-4.6.2 | 4.6.2 | 2022-03-29 | yes | 5939b408a84d | master:pdns/recursordist/docs/changelog/4.6.rst |
| rec-4.5.9 | 4.5.9 | 2022-03-29 | yes | 15d6189d5f87 | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.7.0-beta1 | 4.7.0-beta1 | 2022-04-13 | no | 1ad44ca7024f | master:pdns/recursordist/docs/changelog/4.7.rst |
| rec-4.8.0-alpha0 | 4.8.0-alpha0 | 2022-04-13 | no | 0fce8eae4606 | - |
| rec-4.7.0-rc1 | 4.7.0-rc1 | 2022-04-26 | no | 74771388528e | master:pdns/recursordist/docs/changelog/4.7.rst |
| rec-4.7.0 | 4.7.0 | 2022-05-25 | yes | 677a4e8ea8f7 | master:pdns/recursordist/docs/changelog/4.7.rst |
| rec-4.7.1 | 4.7.1 | 2022-07-05 | yes | aa30ded1488b | master:pdns/recursordist/docs/changelog/4.7.rst |
| rec-4.5.10 | 4.5.10 | 2022-08-23 | yes | 87735c1c89bc | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.6.3 | 4.6.3 | 2022-08-23 | yes | 9067ba9431f2 | master:pdns/recursordist/docs/changelog/4.6.rst |
| rec-4.7.2 | 4.7.2 | 2022-08-23 | yes | 2bf98efd6d80 | master:pdns/recursordist/docs/changelog/4.7.rst |
| rec-4.5.11 | 4.5.11 | 2022-09-13 | yes | cbe1f9833ac9 | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.6.4 | 4.6.4 | 2022-09-13 | yes | 74d635bc7a51 | master:pdns/recursordist/docs/changelog/4.6.rst |
| rec-4.7.3 | 4.7.3 | 2022-09-15 | yes | f527a32f0d3d | master:pdns/recursordist/docs/changelog/4.7.rst |
| rec-4.8.0-alpha1 | 4.8.0-alpha1 | 2022-09-21 | no | 7eaadaa856d4 | master:pdns/recursordist/docs/changelog/4.8.rst |
| rec-4.9.0-alpha0 | 4.9.0-alpha0 | 2022-10-03 | no | 35f66c936af5 | - |
| rec-4.8.0-beta1 | 4.8.0-beta1 | 2022-10-03 | no | 397f88f75456 | master:pdns/recursordist/docs/changelog/4.8.rst |
| rec-4.8.0-beta2 | 4.8.0-beta2 | 2022-11-04 | no | 22406c18f011 | master:pdns/recursordist/docs/changelog/4.8.rst |
| rec-4.8.0-rc1 | 4.8.0-rc1 | 2022-11-17 | no | c494a03f6465 | master:pdns/recursordist/docs/changelog/4.8.rst |
| rec-4.7.4 | 4.7.4 | 2022-11-23 | yes | 1172e8ee2bbd | master:pdns/recursordist/docs/changelog/4.7.rst |
| rec-4.6.5 | 4.6.5 | 2022-11-23 | yes | aad376e3df92 | master:pdns/recursordist/docs/changelog/4.6.rst |
| rec-4.5.12 | 4.5.12 | 2022-11-23 | yes | 27e373528087 | master:pdns/recursordist/docs/changelog/4.5.rst |
| rec-4.8.0 | 4.8.0 | 2022-12-07 | yes | 84bc8944539b | master:pdns/recursordist/docs/changelog/4.8.rst |
| rec-4.8.1 | 4.8.1 | 2023-01-18 | yes | ff1537871d45 | master:pdns/recursordist/docs/changelog/4.8.rst |
| rec-4.8.2 | 4.8.2 | 2023-01-26 | yes | ce120186e7c0 | master:pdns/recursordist/docs/changelog/4.8.rst |
| rec-4.8.3 | 4.8.3 | 2023-03-06 | yes | be8ecbe309ce | master:pdns/recursordist/docs/changelog/4.8.rst |
| rec-4.8.4 | 4.8.4 | 2023-03-29 | yes | 566ad636d523 | master:pdns/recursordist/docs/changelog/4.8.rst |
| rec-4.7.5 | 4.7.5 | 2023-03-29 | yes | 21b255f57931 | master:pdns/recursordist/docs/changelog/4.7.rst |
| rec-4.6.6 | 4.6.6 | 2023-03-29 | yes | cbbfb4f0012e | master:pdns/recursordist/docs/changelog/4.6.rst |
| rec-4.9.0-alpha1 | 4.9.0-alpha1 | 2023-04-11 | no | 96a4510bf64f | master:pdns/recursordist/docs/changelog/4.9.rst |
| rec-4.9.0-beta1 | 4.9.0-beta1 | 2023-05-31 | no | d081c90c7812 | master:pdns/recursordist/docs/changelog/4.9.rst |
| rec-4.10.0-alpha0 | 4.10.0-alpha0 | 2023-06-12 | no | 27c01b79a750 | - |
| rec-4.9.0-rc1 | 4.9.0-rc1 | 2023-06-13 | no | 9c36bc81cb3f | master:pdns/recursordist/docs/changelog/4.9.rst |
| rec-4.9.0 | 4.9.0 | 2023-06-29 | yes | 99d7f7a403ba | master:pdns/recursordist/docs/changelog/4.9.rst |
| rec-4.7.6 | 4.7.6 | 2023-08-23 | yes | 78b227a7887d | master:pdns/recursordist/docs/changelog/4.7.rst |
| rec-4.8.5 | 4.8.5 | 2023-08-23 | yes | a06ef30be675 | master:pdns/recursordist/docs/changelog/4.8.rst |
| rec-4.9.1 | 4.9.1 | 2023-08-23 | yes | 49d27c999a91 | master:pdns/recursordist/docs/changelog/4.9.rst |
| rec-5.0.0-alpha1 | 5.0.0-alpha1 | 2023-09-13 | no | bd6745952ec4 | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-5.0.0-alpha2 | 5.0.0-alpha2 | 2023-10-17 | no | 55af970bdff8 | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-4.9.2 | 4.9.2 | 2023-11-06 | yes | 35e2c1ad21f9 | master:pdns/recursordist/docs/changelog/4.9.rst |
| rec-5.0.0-beta1 | 5.0.0-beta1 | 2023-11-10 | no | 9b46a96d4e90 | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-5.1.0-alpha0 | 5.1.0-alpha0 | 2023-12-04 | no | 1101973a3cba | - |
| rec-5.0.0-rc1 | 5.0.0-rc1 | 2023-12-05 | no | 20adaa6331bb | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-5.0.0-rc2 | 5.0.0-rc2 | 2023-12-18 | no | d1499af06af5 | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-5.0.0 | 5.0.0 | 2023-12-18 | yes | d1499af06af5 | - |
| rec-5.0.1 | 5.0.1 | 2024-01-09 | yes | 524b8cc4c448 | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-5.0.2 | 5.0.2 | 2024-02-06 | yes | 8cb2740c8468 | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-4.8.6 | 4.8.6 | 2024-02-06 | yes | a4bc1426238b | master:pdns/recursordist/docs/changelog/4.8.rst |
| rec-4.9.3 | 4.9.3 | 2024-02-06 | yes | 9a555d9e76e9 | master:pdns/recursordist/docs/changelog/4.9.rst |
| rec-4.9.4 | 4.9.4 | 2024-03-04 | yes | 1a8fd04ccabb | master:pdns/recursordist/docs/changelog/4.9.rst |
| rec-5.0.3 | 5.0.3 | 2024-03-04 | yes | de4058192bf0 | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-4.8.7 | 4.8.7 | 2024-03-04 | yes | a5f01369fea3 | master:pdns/recursordist/docs/changelog/4.8.rst |
| rec-5.0.4 | 5.0.4 | 2024-04-09 | yes | b6ee83de58b7 | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-4.9.5 | 4.9.5 | 2024-04-09 | yes | 3d16f2f49c22 | master:pdns/recursordist/docs/changelog/4.9.rst |
| rec-4.8.8 | 4.8.8 | 2024-04-09 | yes | e1247da96807 | master:pdns/recursordist/docs/changelog/4.8.rst |
| rec-5.0.5 | 5.0.5 | 2024-05-06 | yes | be3e84d15c0b | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-4.9.6 | 4.9.6 | 2024-05-06 | yes | 7394acc984b4 | master:pdns/recursordist/docs/changelog/4.9.rst |
| rec-4.8.9 | 4.8.9 | 2024-05-06 | yes | 078696cdf701 | master:pdns/recursordist/docs/changelog/4.8.rst |
| rec-5.1.0-alpha1 | 5.1.0-alpha1 | 2024-05-14 | no | 31815572b33b | master:pdns/recursordist/docs/changelog/5.1.rst |
| rec-5.0.6 | 5.0.6 | 2024-05-23 | yes | bedb98023c7c | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-5.1.0-beta1 | 5.1.0-beta1 | 2024-06-05 | no | 6012ba6e83f1 | master:pdns/recursordist/docs/changelog/5.1.rst |
| rec-5.2.0-alpha0 | 5.2.0-alpha0 | 2024-06-24 | no | a376dc3be971 | - |
| rec-5.1.0-rc1 | 5.1.0-rc1 | 2024-06-24 | no | 9a8b02619621 | master:pdns/recursordist/docs/changelog/5.1.rst |
| rec-5.0.7 | 5.0.7 | 2024-06-25 | yes | 1d5e654dfcd2 | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-4.9.7 | 4.9.7 | 2024-06-25 | yes | 70921ee8a9bd | master:pdns/recursordist/docs/changelog/4.9.rst |
| rec-5.1.0 | 5.1.0 | 2024-07-08 | yes | f6109dd21a7e | master:pdns/recursordist/docs/changelog/5.1.rst |
| rec-5.0.8 | 5.0.8 | 2024-07-18 | yes | 1fddc70f3913 | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-4.9.8 | 4.9.8 | 2024-07-18 | yes | 9e58e58718b1 | master:pdns/recursordist/docs/changelog/4.9.rst |
| rec-5.1.1 | 5.1.1 | 2024-07-22 | yes | f1b71975cc80 | master:pdns/recursordist/docs/changelog/5.1.rst |
| rec-5.0.9 | 5.0.9 | 2024-08-26 | yes | 49f201d641e7 | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-4.9.9 | 4.9.9 | 2024-08-26 | yes | 4775860c55ed | master:pdns/recursordist/docs/changelog/4.9.rst |
| rec-5.1.2 | 5.1.2 | 2024-08-27 | yes | 9872469c7561 | master:pdns/recursordist/docs/changelog/5.1.rst |
| rec-5.1.3 | 5.1.3 | 2024-10-24 | yes | a3d8f0f147b0 | master:pdns/recursordist/docs/changelog/5.1.rst |
| rec-5.2.0-alpha1 | 5.2.0-alpha1 | 2024-11-11 | no | eaf5b9c07e6c | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.2.0-beta1 | 5.2.0-beta1 | 2024-11-26 | no | 6be83e2da7e7 | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.3.0-alpha0 | 5.3.0-alpha0 | 2024-12-13 | no | c788a201f427 | - |
| rec-5.2.0-rc1 | 5.2.0-rc1 | 2024-12-13 | no | 137c80160488 | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.2.0 | 5.2.0 | 2025-01-10 | yes | 544037cd123e | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.2.1 | 5.2.1 | 2025-03-19 | yes | efd5250cef87 | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.0.10 | 5.0.10 | 2025-04-08 | yes | b15ba8622f87 | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-5.1.4 | 5.1.4 | 2025-04-08 | yes | 1a465473da81 | master:pdns/recursordist/docs/changelog/5.1.rst |
| rec-5.2.2 | 5.2.2 | 2025-04-08 | yes | 4ea1ce6e255d | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.3.0-alpha1 | 5.3.0-alpha1 | 2025-06-24 | no | 85757350ab43 | master:pdns/recursordist/docs/changelog/5.3.rst |
| rec-5.3.0-alpha2 | 5.3.0-alpha2 | 2025-07-09 | no | 7b0e17e0407a | master:pdns/recursordist/docs/changelog/5.3.rst |
| rec-5.2.4 | 5.2.4 | 2025-07-17 | yes | 02523089a579 | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.1.6 | 5.1.6 | 2025-07-17 | yes | b9e5701fd55c | master:pdns/recursordist/docs/changelog/5.1.rst |
| rec-5.0.12 | 5.0.12 | 2025-07-17 | yes | b1e7d3a1b853 | master:pdns/recursordist/docs/changelog/5.0.rst |
| rec-5.4.0-alpha0 | 5.4.0-alpha0 | 2025-07-22 | no | f33ae94a0420 | - |
| rec-5.3.0-beta1 | 5.3.0-beta1 | 2025-07-22 | no | 73aa742805e4 | master:pdns/recursordist/docs/changelog/5.3.rst |
| rec-5.1.7 | 5.1.7 | 2025-07-28 | yes | b8c1770d0cf4 | master:pdns/recursordist/docs/changelog/5.1.rst |
| rec-5.2.5 | 5.2.5 | 2025-07-28 | yes | 3955b468e9f9 | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.3.0-rc1 | 5.3.0-rc1 | 2025-08-20 | no | 0c02f2c34501 | master:pdns/recursordist/docs/changelog/5.3.rst |
| rec-5.3.0 | 5.3.0 | 2025-08-25 | yes | ff33413345dc | master:pdns/recursordist/docs/changelog/5.3.rst |
| rec-5.3.1 | 5.3.1 | 2025-10-22 | yes | 74e6f92a9010 | master:pdns/recursordist/docs/changelog/5.3.rst |
| rec-5.1.8 | 5.1.8 | 2025-10-22 | yes | 465c37fad194 | master:pdns/recursordist/docs/changelog/5.1.rst |
| rec-5.2.6 | 5.2.6 | 2025-10-22 | yes | 7d228e3ddad5 | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.3.3 | 5.3.3 | 2025-11-25 | yes | b51584b39989 | master:pdns/recursordist/docs/changelog/5.3.rst |
| rec-5.2.7 | 5.2.7 | 2025-11-25 | yes | 6f6d02b1f8fa | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.1.9 | 5.1.9 | 2025-11-25 | yes | 3a4436d7e5af | master:pdns/recursordist/docs/changelog/5.1.rst |
| rec-5.4.0-alpha1 | 5.4.0-alpha1 | 2025-12-15 | no | 844375bb485a | master:pdns/recursordist/docs/changelog/5.4.rst |
| rec-5.3.4 | 5.3.4 | 2026-01-07 | yes | 411173bcbf60 | master:pdns/recursordist/docs/changelog/5.3.rst |
| rec-5.4.0-beta1 | 5.4.0-beta1 | 2026-01-26 | no | c048c4a807f9 | master:pdns/recursordist/docs/changelog/5.4.rst |
| rec-5.3.5 | 5.3.5 | 2026-02-09 | yes | 0a44ec6431b9 | master:pdns/recursordist/docs/changelog/5.3.rst |
| rec-5.1.10 | 5.1.10 | 2026-02-09 | yes | 18309fb31837 | master:pdns/recursordist/docs/changelog/5.1.rst |
| rec-5.2.8 | 5.2.8 | 2026-02-09 | yes | 15e4956e9602 | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.5.0-alpha0 | 5.5.0-alpha0 | 2026-02-16 | no | ad0edc82d559 | - |
| rec-5.4.0-rc1 | 5.4.0-rc1 | 2026-02-16 | no | c95adbda8ce5 | master:pdns/recursordist/docs/changelog/5.4.rst |
| rec-5.4.0 | 5.4.0 | 2026-02-16 | yes | c95adbda8ce5 | master:pdns/recursordist/docs/changelog/5.4.rst |
| rec-5.2.9 | 5.2.9 | 2026-04-02 | yes | b297bb729c00 | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.3.6 | 5.3.6 | 2026-04-02 | yes | 1d377042e08a | master:pdns/recursordist/docs/changelog/5.3.rst |
| rec-5.4.1 | 5.4.1 | 2026-04-02 | yes | 9a49123aab87 | master:pdns/recursordist/docs/changelog/5.4.rst |
| rec-5.4.2 | 5.4.2 | 2026-06-01 | yes | aeeeca4edfdc | master:pdns/recursordist/docs/changelog/5.4.rst |
| rec-5.3.7 | 5.3.7 | 2026-06-01 | yes | 6624d013501d | master:pdns/recursordist/docs/changelog/5.3.rst |
| rec-5.2.10 | 5.2.10 | 2026-06-01 | yes | 5e5a078d663c | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.3.8 | 5.3.8 | 2026-06-08 | yes | b2f7567b5e2b | master:pdns/recursordist/docs/changelog/5.3.rst |
| rec-5.2.11 | 5.2.11 | 2026-06-08 | yes | 8565b266486a | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.4.3 | 5.4.3 | 2026-06-08 | yes | 9f875a6231f2 | master:pdns/recursordist/docs/changelog/5.4.rst |
| rec-5.4.4 | 5.4.4 | 2026-07-07 | yes | 64c4f00f2b3d | master:pdns/recursordist/docs/changelog/5.4.rst |
| rec-5.3.9 | 5.3.9 | 2026-07-07 | yes | 53dfd1af948d | master:pdns/recursordist/docs/changelog/5.3.rst |
| rec-5.2.12 | 5.2.12 | 2026-07-07 | yes | b74225ba558d | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.4.5 | 5.4.5 | 2026-08-03 | yes | d17205974426 | master:pdns/recursordist/docs/changelog/5.4.rst |
| rec-5.3.10 | 5.3.10 | 2026-08-03 | yes | 13a6334dc599 | master:pdns/recursordist/docs/changelog/5.3.rst |
| rec-5.2.13 | 5.2.13 | 2026-08-03 | yes | cfa38e316540 | master:pdns/recursordist/docs/changelog/5.2.rst |
| rec-5.5.0-alpha1 | 5.5.0-alpha1 | 2026-08-12 | no | 1810ae213482 | master:pdns/recursordist/docs/changelog/5.5.rst |
| rec-5.4.6 | 5.4.6 | 2026-09-02 | yes | 607df7bdbf08 | master:pdns/recursordist/docs/changelog/5.4.rst |
