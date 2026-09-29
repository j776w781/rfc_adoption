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
git -C $C show <commit> --stat                                        # product files touched (pdns/... not tests/docs)
git -C $C rev-parse rec-3.1.7.1^{tree} rec-3.1.7.2^{tree}             # identical: rec-3.1.7.2 lacks the 3.1.7.2 fixes
git -C $C show master:pdns/recursordist/docs/security-advisories/powerdns-advisory-2024-01.rst   # affected / fixed versions
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


Rows above this line are stage-2 changelog classifications (keyword-filtered, unreviewed; commit column empty). The evidence-backed rows are in the next two tables and in the JSON `default_changes[]` / `cve_fixes[]`.

## Default / limit / support changes with commit evidence

21 rows (5 default-changed, 11 limit-changed, 5 support-added). Every commit touches product code under `pdns/` (checked per commit in the JSON `product_files`); each `first_stable_tag` was confirmed with `git tag --contains`. "tag" is the first STABLE tag containing the change; pre-release tags are in `first_tags_any`.

| tag | released | kind | mechanism | change | before | after | on upgrade | opt-in | commit(s) | first tag (any) |
|---|---|---|---|---|---|---|---|---|---|---|
| 4.0.0 | 2016-07-08 | default-changed | validation | dnssec default changed process -> process-no-validate (introduced with the new mode) | dnssec=process (rec-4.0.0-alpha1..alpha3) | dnssec=process-no-validate: security-aware but non-validating, RRSIG/NSEC passed through, never validates | yes | no | a6415142cf | rec-4.0.0-beta1 |
| 4.0.0 | 2016-07-08 | support-added | validation | dnssec setting introduced; default "process" | rec-3.x: no DNSSEC handling in the Recursor | dnssec=process: send DO, return DNSSEC records when the client asks, validate only when the client sets AD or DO | yes | no | 12ce523e77 | rec-4.0.0-alpha1 |
| 4.0.0 | 2016-07-08 | support-added | trust-anchor-5011 | Positive and negative trust anchor management (configured TAs, runtime add-ta/add-nta) | only the built-in root DS was usable | trust anchors and negative trust anchors configurable via Lua config and rec_control (runtime, volatile); not RFC 5011 | no | yes | 1bd49828f7, 331bcdd531 | rec-4.0.0-rc1 |
| 4.0.5 | 2017-06-13 | support-added | alg-eddsa | Ed25519 (algorithm 15) signature validation hooked into the Recursor | algorithm 15 unsupported (Insecure) | algorithm 15 validated when built with libsodium (sodiumsigners.cc); algorithm 16 (Ed448) only via optional libdecaf build, not default | yes | no | 7abbb2c9f0, abfe6717db | rec-4.0.5-rc1 |
| 4.0.5 | 2017-06-13 | default-changed | trust-anchor-5011 | Built-in root trust anchor gains the 2017 KSK (key tag 20326) | rootDSs = {19036} | rootDSs = {19036, 20326} | yes | no | 1909556cce, d5037c4d34 | rec-4.0.5-rc1, rec-4.1.0-alpha1 |
| 4.1.0 | 2017-12-04 | limit-changed | nsec3-iterations | nsec3-max-iterations introduced, default 2500 | no NSEC3 iteration cap | nsec3-max-iterations=2500: NSEC3 records above the cap are treated as Insecure | yes | no | d377bb54f4 | rec-4.1.0-alpha1 |
| 4.2.0 | 2019-07-12 | limit-changed | rrsig | signature-inception-skew setting: 0 in 4.1.5 backport, 60 seconds default in 4.2.0 | RRSIG inception in the future rejected without tolerance | inception tolerated up to 60 s (4.2.0+); 4.1.5+ default 0 s (no tolerance) | yes | no | 575925eff1, 9a3ab3e4f5 | rec-4.1.5, rec-4.2.0-alpha1 |
| 4.4.0 | 2020-10-13 | support-added | dnskey | DNSKEYs without the Zone flag, and DNSKEYs with the REVOKE bit set, are no longer used to validate | any DNSKEY with protocol 3 and matching tag/algorithm was a candidate validation key | getByTag() skips keys where (flags & 256)==0 (RFC 4034 s2.1.1) and, in the same commit, keys with the revoked flag (flags & 128, RFC 5011 s3) | yes | no | 6f2088b4fe | rec-4.4.0-alpha2 |
| 4.5.0 | 2021-05-07 | support-added | validation | Aggressive use of DNSSEC-validated cache (RFC 8198) on by default: aggressive-nsec-cache-size=100000 | no aggressive NSEC/NSEC3 synthesis | aggressive-nsec-cache-size=100000 (0 disables); used when dnssec is process/log-fail/validate | yes | no | edcf680eb1 | rec-4.5.0-alpha2 |
| 4.5.0 | 2021-05-07 | default-changed | validation | dnssec default changed process-no-validate -> process (first release whose default validates on client request) | dnssec=process-no-validate (never validates) | dnssec=process: validate when the client sets AD or DO (dig sets AD); SERVFAIL on bogus; NOT validate for all queries | yes | no | 90e61f7284 | rec-4.5.0-alpha2 |
| 4.5.2 | 2021-06-07 | limit-changed | nsec3-iterations | nsec3-max-iterations default lowered 2500 -> 150 | nsec3-max-iterations=2500 | nsec3-max-iterations=150 | yes | no | be96358a56, 2a93a7c4fe | rec-4.5.2, rec-4.6.0-alpha1 |
| 4.9.0 | 2023-06-29 | default-changed | alg-rsa-sha2 | Algorithms 5 (RSASHA1) and 7 (RSASHA1-NSEC3-SHA1) switched off automatically when the crypto library refuses SHA-1 signatures; dnssec-disabled-algorithms setting added | all implemented algorithms attempted; SHA-1 failures on strict crypto policies (e.g. RHEL9) became Bogus/failed | dnssec-disabled-algorithms="" means auto-detect: algorithms 5 and 7 tested with DNSCryptoKeyEngine::verifyOne at startup and switched off when the test fails (treated as unsupported => Insecure); can be set explicitly | yes | no | 81a9420715, 04cee9810c | rec-4.10.0-alpha0 |
| 5.0.0 | 2023-12-18 | limit-changed | nsec3-iterations | nsec3-max-iterations default lowered 150 -> 50 | nsec3-max-iterations=150 | nsec3-max-iterations=50 | yes | no | a487308875 | rec-5.1.0-alpha0 |
| 5.0.2 | 2024-02-06 | limit-changed | validation | KeyTrap (CVE-2023-50387/50868) validation limit aggressive-cache-max-nsec3-hash-cost introduced, default 150 | no limit on this quantity | aggressive-cache-max-nsec3-hash-cost=150 | yes | no | 8cb2740c84, a4bc142623, 3a4cf27324, 15e973d6d8 | rec-5.0.2, rec-4.8.6, rec-4.9.3 |
| 5.0.2 | 2024-02-06 | limit-changed | validation | KeyTrap (CVE-2023-50387/50868) validation limit max-dnskeys introduced, default 2 | no limit on this quantity | max-dnskeys=2 | yes | no | 8cb2740c84, a4bc142623, 3a4cf27324, 15e973d6d8 | rec-5.0.2, rec-4.8.6, rec-4.9.3 |
| 5.0.2 | 2024-02-06 | limit-changed | validation | KeyTrap (CVE-2023-50387/50868) validation limit max-ds-per-zone introduced, default 8 | no limit on this quantity | max-ds-per-zone=8 | yes | no | 8cb2740c84, a4bc142623, 3a4cf27324, 15e973d6d8 | rec-5.0.2, rec-4.8.6, rec-4.9.3 |
| 5.0.2 | 2024-02-06 | limit-changed | validation | KeyTrap (CVE-2023-50387/50868) validation limit max-nsec3-hash-computations-per-query introduced, default 600 | no limit on this quantity | max-nsec3-hash-computations-per-query=600 | yes | no | 8cb2740c84, a4bc142623, 3a4cf27324, 15e973d6d8 | rec-5.0.2, rec-4.8.6, rec-4.9.3 |
| 5.0.2 | 2024-02-06 | limit-changed | validation | KeyTrap (CVE-2023-50387/50868) validation limit max-nsec3s-per-record introduced, default 10 | no limit on this quantity | max-nsec3s-per-record=10 | yes | no | 8cb2740c84, a4bc142623, 3a4cf27324, 15e973d6d8 | rec-5.0.2, rec-4.8.6, rec-4.9.3 |
| 5.0.2 | 2024-02-06 | limit-changed | validation | KeyTrap (CVE-2023-50387/50868) validation limit max-rrsigs-per-record introduced, default 2 | no limit on this quantity | max-rrsigs-per-record=2 | yes | no | 8cb2740c84, a4bc142623, 3a4cf27324, 15e973d6d8 | rec-5.0.2, rec-4.8.6, rec-4.9.3 |
| 5.0.2 | 2024-02-06 | limit-changed | validation | KeyTrap (CVE-2023-50387/50868) validation limit max-signature-validations-per-query introduced, default 30 | no limit on this quantity | max-signature-validations-per-query=30 | yes | no | 8cb2740c84, a4bc142623, 3a4cf27324, 15e973d6d8 | rec-5.0.2, rec-4.8.6, rec-4.9.3 |
| 5.0.10 | 2025-04-08 | default-changed | trust-anchor-5011 | Built-in root trust anchor gains the new KSK (key tag 38696) | rootDSs = {20326} | rootDSs = {20326, 38696} | yes | no | 0bbbdd60ab, a5f6b5be8c, 7f74864ae7 | rec-5.2.0-alpha1, rec-5.0.10, rec-5.1.4 |

### Evidence and caveats per row

- **dnssec-default-process-no-validate** (rec-4.0.0, attribution exact): commit message: "Add process-no-validate option. Make it also the default. This turns the recursor into a Security-Aware Recursive Name Server (RFC 4033 s2), meaning it will pass on RRSIGs and NSEC(3)s but will not validate." Changelog 4.0.0-beta1: "#3905 Add a dnssec=process-no-validate option and make it default". String at rec-4.0.0: "off/process-no-validate (default)/process/log-fail/validate"="process-no-validate". NOTE: Default for every stable release 4.0.0 .. 4.4.x. The Recursor did NOT ship validation on by default in 4.0-4.4.
- **dnssec-setting-introduced** (rec-4.0.0, attribution exact): commit message: "implement four dnssec modes: off (3.x behaviour), process (ask for DNSSEC, give it when asked for, validate when asked to), validate (always validate), log-fail". git grep at rec-4.0.0-alpha1: ::arg().set("dnssec", "DNSSEC mode: off/process (default)/log-fail/validate")="process". NOTE: Alpha-only default: replaced by process-no-validate in rec-4.0.0-beta1 (next row), so no stable release ever shipped "process" as default until 4.5.0.
- **trust-anchor-ta-nta-management** (rec-4.0.0, attribution exact): Changelog 4.0.0-rc1 "#3910 Add (Negative) Trust Anchor management". docs/dnssec.rst at rec-5.4.0: "it has no support for RFC 5011 key rollover and does not persist a changed root trust anchor to disk." NOTE: RFC 7646 is inferred from the "Negative Trust Anchor" terminology; the commits do not cite it. No RFC 5011 implementation was found at any tag (see gaps).
- **ed25519-validation** (rec-4.0.5, attribution exact): Changelog 4.0.5: "This release adds ed25519 (algorithm 15) support for DNSSEC and adds the 2017 DNSSEC root key. If you do DNSSEC validation, this upgrade is mandatory ..."; commit "hook up ed25519 signer in the recursor". NOTE: Support is build-dependent (LIBSODIUM); distribution packages usually enable it. RFC 8080 is the Ed25519/Ed448 DNSSEC RFC (algorithm numbers), inferred from the algorithm number not cited in the commit.
- **root-ds-2017-added** (rec-4.0.5, attribution exact): commit "Add the 2017 root key" (pdns/root-dnssec.hh). Changelog 4.0.5 (mandatory-upgrade note above). The 4.0.x-branch commit 1909556cc first appears in rec-4.0.5-rc1; the master commit d5037c4d3 in rec-4.1.0-alpha1. NOTE: This is a hard-coded update, not RFC 5011 tracking: a Recursor older than 4.0.5 (only 19036) would stop validating after the October 2018 root KSK roll.
- **nsec3-max-iterations-2500** (rec-4.1.0, attribution exact): commit "rec: Add a `nsec3-max-iterations` setting, default to 2500" (pdns/pdns_recursor.cc, validate.cc). Changelog 4.1.0-rc3: "Fix going Insecure on NSEC3 hashes with too many iterations". NOTE: Not backported to the 4.0.x branch (rec-4.0.9 lacks the setting per git show rec-4.0.9:pdns/pdns_recursor.cc).
- **signature-inception-skew** (rec-4.2.0, attribution exact): commit "rec: allow the signture inception to be off by a number of seconds." master default "60" (9a3ab3e4f), rec-4.1.x backport default "0" (575925eff). NOTE: Row tag is rec-4.2.0 where the default is 60; rec-4.1.5 added the setting with default 0.
- **revoked-dnskey-rejected** (rec-4.4.0, attribution exact): commit "rec: Check that DNSKEYs have the 'zone' flag set, 'revoked' one cleared" (pdns/validate.cc); isRevokedKey() comment "rfc5011 Section 3". NOTE: This is the ONLY RFC 5011 behaviour found: rejecting revoked keys. No automated trust-anchor rollover (add/hold-down) exists: docs/dnssec.rst at rec-5.4.0 says "it has no support for RFC 5011 key rollover".
- **aggressive-nsec-cache** (rec-4.5.0, attribution exact): commit "rec: Cache cleaning, make the aggressive nsec cache size configurable" replaced setSwitch("aggressive-nsec") default "no" (never in a release) with aggressive-nsec-cache-size default "100000". Changelog 4.5.0-alpha3 "Implement rfc 8198 - Aggressive Use of DNSSEC-Validated Cache" (commit is in alpha2). NOTE: Only effective when validation runs, which since 4.5.0 is on client request (dnssec=process).
- **dnssec-default-process** (rec-4.5.0, attribution exact): commit message "rec: Change dnssec default to `process`"; settings.rst gained ".. versionchanged:: 4.5.0 The default changed from process-no-validate to process"; upgrade.rst: "The dnssec default has changed from process-no-validate to process." Current docs/dnssec.rst: "process: The default mode since PowerDNS Recursor 4.5.0". Changelog entry filed under 4.5.0-alpha3 ("Change dnssec default to `process`.") but the commit is first contained by rec-4.5.0-alpha2. NOTE: The default has NEVER been "validate" (validate-all): mode "validate" is still opt-in at rec-5.5.0-alpha1 (rec-rust-lib/table.py default "process"). applies_on_upgrade true for anyone on 4.4.x and earlier without an explicit dnssec= setting.
- **nsec3-max-iterations-150** (rec-4.5.2, attribution exact): commit "Change nsec3-max-iterations default to 150"; changelog 4.5.2 (PR 10477) "Change nsec3-max-iterations default to 150."; upgrade.rst: "The nsec3-max-iterations default value has been changed from 2500 to 150." Branch commit be96358a5 (rel/rec-4.5.x) ships in rec-4.5.2; master commit 2a93a7c4f in rec-4.6.0-alpha1. Table default doc: versionchanged 4.5.2. NOTE: Shipped in a patch release (4.5.2, 2021-06-07): applies on upgrade within 4.5.x.
- **dnssec-disabled-algorithms-auto** (rec-4.9.0, attribution exact): Changelog 4.9.0-rc1 (PR 12893): "Add feature to switch off unsupported DNSSEC algos, either automatically or manually." Setting docs: "If this setting is empty (the default), Recursor will determine which algorithms to disable automatically. This is important on systems that have a default strict crypto policy, like RHEL9 derived systems." NOTE: Automatic step lives in 81a942071 "Impelement verification of algos 5 and 7"; 04cee9810 adds the setting (its auto branch was an empty placeholder). No algorithm is disabled by default on a system whose crypto library accepts SHA-1. RFC 8624 inferred (algorithm requirement levels), not cited by the commits.
- **nsec3-max-iterations-50** (rec-5.0.0, attribution exact): commit "rec: change default of nsec3-max-iterations to 50" (settings/table.py); changelog 5.0.0 (PR 13478) "Change default of nsec3-max-iterations to 50."; upgrade.rst: "The nsec3-max-iterations now defaults to 50." table.py versionchanged ("5.0.0", "Default is now 50, was 150 before."). NOTE: Not backported: rec-4.9.x and 4.8.x keep 150. The commit is first contained by rec-5.0.0-rc1 and rec-5.1.0-alpha0 (tag names in first_tags_any); rec-5.0.0 is the first stable tag. RFC 9276 inferred from the value (RFC 9276 recommends 0 and a low validator cap); commit cites neither.
- **keytrap-aggressive-cache-max-nsec3-hash-cost** (rec-5.0.2, attribution exact): Advisory 2024-01 (Recursor 4.8.6, 4.9.3, 5.0.2 fixed); master commit "rec: CVE-2023-50387 and CVE-2023-50868" adds the setting in settings/table.py with default 150; rec-4.8.6/4.9.3/5.0.2 tag scans of rec-main.cc/table.py show the same default. Changelog for each release: "Security advisory 2024-01: CVE-2023-50387 and CVE-2023-50868". NOTE: Branch tags rec-5.0.2 (8cb2740c8), rec-4.8.6 (a4bc14262), rec-4.9.3 (3a4cf2732) all carry commit date 2024-02-06 while the changelog gives 13 Feb 2024 as public release (embargo). Master gets it in rec-5.1.0-alpha1 (15e973d6d, 2024-02-09).
- **keytrap-max-dnskeys** (rec-5.0.2, attribution exact): Advisory 2024-01 (Recursor 4.8.6, 4.9.3, 5.0.2 fixed); master commit "rec: CVE-2023-50387 and CVE-2023-50868" adds the setting in settings/table.py with default 2; rec-4.8.6/4.9.3/5.0.2 tag scans of rec-main.cc/table.py show the same default. Changelog for each release: "Security advisory 2024-01: CVE-2023-50387 and CVE-2023-50868". NOTE: Branch tags rec-5.0.2 (8cb2740c8), rec-4.8.6 (a4bc14262), rec-4.9.3 (3a4cf2732) all carry commit date 2024-02-06 while the changelog gives 13 Feb 2024 as public release (embargo). Master gets it in rec-5.1.0-alpha1 (15e973d6d, 2024-02-09).
- **keytrap-max-ds-per-zone** (rec-5.0.2, attribution exact): Advisory 2024-01 (Recursor 4.8.6, 4.9.3, 5.0.2 fixed); master commit "rec: CVE-2023-50387 and CVE-2023-50868" adds the setting in settings/table.py with default 8; rec-4.8.6/4.9.3/5.0.2 tag scans of rec-main.cc/table.py show the same default. Changelog for each release: "Security advisory 2024-01: CVE-2023-50387 and CVE-2023-50868". NOTE: Branch tags rec-5.0.2 (8cb2740c8), rec-4.8.6 (a4bc14262), rec-4.9.3 (3a4cf2732) all carry commit date 2024-02-06 while the changelog gives 13 Feb 2024 as public release (embargo). Master gets it in rec-5.1.0-alpha1 (15e973d6d, 2024-02-09).
- **keytrap-max-nsec3-hash-computations-per-query** (rec-5.0.2, attribution exact): Advisory 2024-01 (Recursor 4.8.6, 4.9.3, 5.0.2 fixed); master commit "rec: CVE-2023-50387 and CVE-2023-50868" adds the setting in settings/table.py with default 600; rec-4.8.6/4.9.3/5.0.2 tag scans of rec-main.cc/table.py show the same default. Changelog for each release: "Security advisory 2024-01: CVE-2023-50387 and CVE-2023-50868". NOTE: Branch tags rec-5.0.2 (8cb2740c8), rec-4.8.6 (a4bc14262), rec-4.9.3 (3a4cf2732) all carry commit date 2024-02-06 while the changelog gives 13 Feb 2024 as public release (embargo). Master gets it in rec-5.1.0-alpha1 (15e973d6d, 2024-02-09).
- **keytrap-max-nsec3s-per-record** (rec-5.0.2, attribution exact): Advisory 2024-01 (Recursor 4.8.6, 4.9.3, 5.0.2 fixed); master commit "rec: CVE-2023-50387 and CVE-2023-50868" adds the setting in settings/table.py with default 10; rec-4.8.6/4.9.3/5.0.2 tag scans of rec-main.cc/table.py show the same default. Changelog for each release: "Security advisory 2024-01: CVE-2023-50387 and CVE-2023-50868". NOTE: Branch tags rec-5.0.2 (8cb2740c8), rec-4.8.6 (a4bc14262), rec-4.9.3 (3a4cf2732) all carry commit date 2024-02-06 while the changelog gives 13 Feb 2024 as public release (embargo). Master gets it in rec-5.1.0-alpha1 (15e973d6d, 2024-02-09).
- **keytrap-max-rrsigs-per-record** (rec-5.0.2, attribution exact): Advisory 2024-01 (Recursor 4.8.6, 4.9.3, 5.0.2 fixed); master commit "rec: CVE-2023-50387 and CVE-2023-50868" adds the setting in settings/table.py with default 2; rec-4.8.6/4.9.3/5.0.2 tag scans of rec-main.cc/table.py show the same default. Changelog for each release: "Security advisory 2024-01: CVE-2023-50387 and CVE-2023-50868". NOTE: Branch tags rec-5.0.2 (8cb2740c8), rec-4.8.6 (a4bc14262), rec-4.9.3 (3a4cf2732) all carry commit date 2024-02-06 while the changelog gives 13 Feb 2024 as public release (embargo). Master gets it in rec-5.1.0-alpha1 (15e973d6d, 2024-02-09).
- **keytrap-max-signature-validations-per-query** (rec-5.0.2, attribution exact): Advisory 2024-01 (Recursor 4.8.6, 4.9.3, 5.0.2 fixed); master commit "rec: CVE-2023-50387 and CVE-2023-50868" adds the setting in settings/table.py with default 30; rec-4.8.6/4.9.3/5.0.2 tag scans of rec-main.cc/table.py show the same default. Changelog for each release: "Security advisory 2024-01: CVE-2023-50387 and CVE-2023-50868". NOTE: Branch tags rec-5.0.2 (8cb2740c8), rec-4.8.6 (a4bc14262), rec-4.9.3 (3a4cf2732) all carry commit date 2024-02-06 while the changelog gives 13 Feb 2024 as public release (embargo). Master gets it in rec-5.1.0-alpha1 (15e973d6d, 2024-02-09).
- **root-ds-38696** (rec-5.0.10, attribution exact): commit "recursor: add 38696 root anchor" (pdns/root-dnssec.hh); backports rec-5.0.10 (a5f6b5be8, PR 15214) and rec-5.1.4 (7f74864ae, PR 15215) both "Add new root trust anchor." in the changelog. NOTE: Static addition, no RFC 5011: with docs/dnssec.rst "no support for RFC 5011 key rollover". Master carries it from rec-5.2.0-alpha1. Older releases (4.x, and 5.0.0-5.0.9 / 5.1.0-5.1.3) lack it.

## CVE fixes

52 CVEs: the 50 in `cve_inventory.json` by_product.pdns-rec plus CVE-2024-25583 and CVE-2024-25590 (only in fixes.pdns-rec). `fix tag` = EARLIEST stable `rec-*` tag (by tag-commit timestamp) containing any fix commit; `shipping tags` lists the first stable tag per branch (branch point releases carry the fix under a different commit than master). Latency = fix tag commit date minus NVD published date (negative = fixed before publication). DNSSEC column = the flaw is in DNSSEC validation, parsing or caching of DNSSEC data.

| CVE | NVD published | fix tag | fix date | latency (days) | DNSSEC | shipping tags | fix commit(s) | attribution | inventory fix_release | note |
|---|---|---|---|---|---|---|---|---|---|---|
| CVE-2006-4251 | 2006-11-14 | rec-3.1.4 | 2006-11-16 | 2 | no | rec-3.1.4 | a0aa4f64f2 | approximate | - | TCP query-length overflow. rec-3.1.4 changelog: "Large TCP questions followed by garbage could cause the recursor to crash ... CVE-2006-4251, fixed in commit 915". SVN r915 has no git-svn-id in the clone; a0aa4f64f "fix possible TCP related crash on malformed packet" (pdns/pdns_recursor.cc) is the matching commit by subject and date (2006-11-07), first contained by rec-3.1.4. |
| CVE-2006-4252 | 2006-11-14 | rec-3.1.4 | 2006-11-16 | 2 | no | - | - | approximate | - | CNAME zero-TTL loop. rec-3.1.4 changelog names the fix ("CNAME loops with zero second TTLs could cause crashes") but no commit in rec-3.1.2..rec-3.1.4 is identifiable by subject; fix commit not found. Tag taken from the changelog and NVD ("3.1.3 and earlier"): rec-3.1.4 is the first rec- tag after 3.1.2. |
| CVE-2008-1637 | 2008-04-02 | rec-3.1.7.1 | 2009-08-02 | 487 | no | rec-3.1.7.1 | 4b3fbfd32b | approximate | - | Fixed in Recursor 3.1.5 (31 March 2008, pre-4.0 changelog) but the clone has NO rec-3.1.5 or rec-3.1.6 tag; the first rec- tag after them is rec-3.1.7.1. 4b3fbfd32 (AES/dns_random import, 2008-03-16) is the candidate commit by subject and date; per-commit attribution is approximate. |
| CVE-2008-3217 | 2008-07-18 | rec-3.1.7.1 | 2009-08-02 | 380 | no | rec-3.1.7.1 | 8e652125ee | approximate | - | Fixed in 3.1.6 (1 May 2008; NVD ref changeset 1179). No rec-3.1.6 tag exists; first rec- tag containing 13f1ecb52 "further randomisation improvements" (2008-04-25) is rec-3.1.7.1. Commit chosen by subject/date; approximate. |
| CVE-2009-4009 | 2010-01-08 | rec-3.2 | 2010-03-06 | 57 | no | - | - | approximate | - | Fixed in 3.1.7.2 per advisory 2010-01. rec-3.1.7.2 has a tree IDENTICAL to rec-3.1.7.1 (git rev-parse rec-3.1.7.1^{tree} rec-3.1.7.2^{tree} equal; its single commit 514472d39 is an SVN "branch" copy), so that tag cannot be the first tag containing fix code. rec-3.2 changelog says "All security fixes from 3.1.7.2 are included": rec-3.2 is the first tag that demonstrably contains the fix. Fix commit itself not found. |
| CVE-2009-4010 | 2010-01-08 | rec-3.2 | 2010-03-06 | 57 | yes | - | - | approximate | - | Advisory 2010-02 (spoofing via crafted zones), same release as CVE-2009-4009 and the same mis-imported rec-3.1.7.2 tag (tree identical to rec-3.1.7.1); first demonstrable tag rec-3.2. Fix commit not found. |
| CVE-2014-8601 | 2014-12-10 | rec-3.6.2 | 2014-10-30 | -41 | no | rec-3.6.2 | ab14b4fed2 | exact | - | rec-3.6.2 changelog: "commit ab14b4f: expedite servfail generation for ezdns-like failures (fully abort query resolving if we hit more than 50 outqueries)". This is the tag commit of rec-3.6.2. |
| CVE-2015-1868 | 2015-05-18 | rec-3.7.2 | 2015-04-21 | -27 | no | rec-3.7.2, rec-3.6.3 | dc02ebf65a, 64425b951d, adb10be102, 3ec3e0fc71 | exact | - | Label decompression forward references. rec-3.7.2 changelog lists commit adb10be, 3ec3e0f, dc02ebf; rec-3.6.3 carries the equivalent 64425b951/4247f765c. Both tags dated 2015-04-21. The inventory fixes[] row (9df4944d8 "import CVE-2015-1868 patch") has no rec- tag containing it and is an Authoritative-side import. |
| CVE-2015-5470 | 2015-11-02 | rec-3.6.4 | 2015-06-08 | -147 | no | rec-3.6.4, rec-3.7.3 | bccd068817, 92f7b2bb3f | exact | - | Insufficient fix of CVE-2015-1868 ("Limit the maximum length of a qname"): rec-3.6.4 (bccd06881) and rec-3.7.3 (92f7b2bb3). |
| CVE-2016-7068 | 2018-09-11 | rec-3.7.4 | 2017-01-12 | -607 | no | rec-3.7.4, rec-4.0.4 | 8c82b5d10e, 28e152dd6f | approximate | - | Advisory 2016-02: not affected Recursor 3.7.4, 4.0.4. "Don't parse spurious RRs in queries when we don't need them" is in rec-3.7.4 (8c82b5d10) and rec-4.0.4 (28e152dd6); mapping to the CVE is by advisory version plus subject, no commit names the CVE. |
| CVE-2016-7073 | 2018-09-11 | rec-4.0.4 | 2017-01-13 | -606 | no | rec-4.0.4 | 109d4633dc | approximate | - | Advisory 2016-04 (TSIG on IXFR, CVE-2016-7073/7074), not affected Recursor 4.0.4. 109d4633d "Check TSIG signature on IXFR" first in rec-4.0.4. (The rec-4.0.4 changelog cites "commit 658d9e4" for this, but 658d9e407 is the unrelated max-recursion-depth commit.) |
| CVE-2016-7074 | 2018-09-11 | rec-4.0.4 | 2017-01-13 | -606 | no | rec-4.0.4 | 109d4633dc | approximate | - | Same advisory and commit as CVE-2016-7073 (Advisory 2016-04). |
| CVE-2017-15090 | 2018-01-23 | rec-4.0.7 | 2017-11-27 | -57 | yes | rec-4.0.7 | 9aed598c9a | approximate | - | Advisory 2017-03 (DNSSEC validation accepted out-of-bailiwick signatures), not affected 4.0.7. 9aed598c9 "rec: Guard against out-of-bailiwick signatures" is in the 4.0.6..4.0.7 range. |
| CVE-2017-15092 | 2018-01-23 | rec-4.0.7 | 2017-11-27 | -57 | no | rec-4.0.7 | fd30387c26 | approximate | - | Advisory 2017-05 (XSS in web interface); fd30387c2 "rec: Fix XSS in the web interface" in 4.0.7. |
| CVE-2017-15093 | 2018-01-23 | rec-4.0.7 | 2017-11-27 | -57 | no | rec-4.0.7 | badf9e8900 | approximate | - | Advisory 2017-06 (api-config-dir); badf9e890 "Sanitize values received from the API" in 4.0.7. 3.7.x (affected up to 3.7.4) never received a fix tag in the clone. |
| CVE-2017-15094 | 2018-01-23 | rec-4.0.7 | 2017-11-27 | -57 | yes | rec-4.0.7 | e87fe3987a | approximate | - | Advisory 2017-07 (memory leak parsing crafted ECDSA DNSKEYs); e87fe3987 "Don't leak when the loading a public ECDSA key fails" in 4.0.7. |
| CVE-2017-15120 | 2018-07-27 | rec-4.0.8 | 2017-12-11 | -228 | no | rec-4.0.8 | 10d9d4d5e6 | approximate | - | Advisory 2017-08 (CNAME of class != IN); 10d9d4d5e "rec: Don't process records for another class than IN" in 4.0.8; 4.1.0 already not affected. |
| CVE-2018-1000003 | 2018-01-22 | rec-4.1.1 | 2018-01-22 | 0 | yes | rec-4.1.1 | 91c294836c | approximate | - | Advisory 2018-01: ancestor-delegation NSEC/NSEC3 used to prove non-existence below the owner name. 91c294836 "rec: Correctly handle ancestor delegation NSEC{,3} for children" (rec-4.1.1 changelog: "Fixes the DNSSEC validation issue found in Knot Resolver"). The changelog line does not name the CVE; mapping via the advisory text. |
| CVE-2018-10851 | 2018-11-29 | rec-4.1.5 | 2018-11-06 | -23 | no | rec-4.1.5, rec-4.0.9 | 43a8869ef4, 6fb72eaa9d | approximate | - | Advisory 2018-04 (memory leak / crash on crafted answer). 4.0.9 backport 43a8869ef and 4.1.5 backport 6fb72eaa9 "Allocate DNSRecord objects as smart pointers right away"; mapping by advisory batch (10851/14626/14644), individual commit mapping approximate. |
| CVE-2018-14626 | 2018-11-29 | rec-4.1.5 | 2018-11-06 | -23 | no | rec-4.1.5, rec-4.0.9 | a876cf9f60, 25f4137dde | approximate | - | Advisory 2018-06 packet-cache pollution: "Do full packet comparison in the packet caches in addition to the hash" (4.0.9: a876cf9f6, 4.1.5: 25f4137dd). |
| CVE-2018-14644 | 2018-11-09 | rec-4.1.5 | 2018-11-06 | -3 | yes | rec-4.1.5, rec-4.0.9 | 237e98b9ea, ebb4504339 | approximate | - | Advisory 2018-07: meta-type (OPT) query caused a zone to be cached as failing DNSSEC validation. "Refuse queries for rfc6895 section 3.1 meta types" (4.0.9: 237e98b9e, 4.1.5: ebb450433). |
| CVE-2018-16855 | 2018-12-03 | rec-4.1.8 | 2018-11-26 | -7 | no | rec-4.1.8 | 7ae359c798 | exact | - | rec-4.1.8 changelog names CVE-2018-16855; 7ae359c79 "rec: Fix an out-of-bounds read in the packet cache" is the only commit in 4.1.7..4.1.8. |
| CVE-2019-3806 | 2019-01-29 | rec-4.1.9 | 2019-01-21 | -8 | no | rec-4.1.9 | 66f0bf7f08, 6c4d0ab4cd | exact | - | rec-4.1.9 changelog: "Properly apply Lua hooks to TCP queries, even with pdns-distributes-queries set (CVE-2019-3806)". Commits 66f0bf7f0 and 6c4d0ab4c. |
| CVE-2019-3807 | 2019-01-29 | rec-4.1.9 | 2019-01-21 | -8 | yes | rec-4.1.9 | 3996e9fddd | exact | - | rec-4.1.9 changelog names CVE-2019-3807 (records in answer section of AA=0 responses not validated). 3996e9fdd "Always check signature for records in ANSWER, even with AA=0". |
| CVE-2020-10030 | 2020-05-19 | rec-4.1.16 | 2020-05-19 | 0 | no | rec-4.1.16 | ea4d4ef8c9 | approximate | - | 4.1.16 changelog groups CVE-2020-10995/12244/10030. ea4d4ef8c "Don't read potentially uninitalized memory if gethostname() failed" matches CVE-2020-10030 (hostname stack overflow). |
| CVE-2020-10995 | 2020-05-19 | rec-4.1.16 | 2020-05-19 | 0 | no | rec-4.1.16 | e792445afe | approximate | - | e792445af "backport to 4.1.x: Limit the number of queries sent out to get NS addresses per query" matches the amplification CVE (NXNSAttack-style). |
| CVE-2020-12244 | 2020-05-19 | rec-4.1.16 | 2020-05-19 | 0 | yes | rec-4.1.16 | 3c5a78c1c7 | approximate | - | 3c5a78c1c "rec: Fix DNSSEC validation of completely empty NXDomain answers" matches the SOA-less NXDOMAIN validation bypass. |
| CVE-2020-14196 | 2020-07-01 | rec-4.1.17 | 2020-06-30 | -1 | no | rec-4.1.17 | e812711892 | exact | - | rec-4.1.17 changelog "Backport of CVE-2020-14196: Enforce webserver ACL"; e81271189 "Backport of acl check to 4.1.x". |
| CVE-2020-25829 | 2020-10-16 | rec-4.1.18 | 2020-10-12 | -4 | yes | rec-4.1.18, rec-4.2.5 | 77409aab0b, e0386c2225 | exact | 4.2.5 | Cache pollution: names cached as Bogus by an ANY/any-cache-update path. 77409aab0 is the rec-4.1.18 tag commit (2020-10-12); 4.2.5/4.3.5/4.4.0 followed on 2020-10-13. The inventory fixes[] row lists 4.2.5 (the 4.2.x backport) - 4.1.18 is earlier. |
| CVE-2022-27227 | 2022-03-25 | rec-4.4.8 | 2022-03-16 | -9 | no | rec-4.4.8 | ff27c8c8e1 | exact | - | Advisory 2022-01 (IXFR incomplete read, RPZ only in Recursor): ff27c8c8e "auth, rec IXFR-in: Fix a case where an incomplete read ... truncated zone" in rec-4.4.8. Advisory lists 4.4.8, 4.5.8, 4.6.1 as fixed. |
| CVE-2022-37428 | 2022-08-23 | rec-4.5.10 | 2022-08-23 | 0 | no | rec-4.5.10, rec-4.6.3, rec-4.7.2 | 21f3d92144, 0cc78db116, cb16a5eddd | exact | 4.5.10 | Protobuf logging cleanup: 4.5.10 (21f3d9214), 4.6.3 (0cc78db11), 4.7.2 (cb16a5edd), all released 2022-08-23. |
| CVE-2023-22617 | 2023-01-21 | rec-4.8.1 | 2023-01-18 | -3 | yes | rec-4.8.1 | ff1537871d | exact | - | DS-retrieval infinite recursion under QNAME minimisation fallback: "Backport to 4.8.x: Do *not* use QName Minimization for DS retrievals in QM fallback mode" (ff1537871, rec-4.8.1). Advisory 2023-01. |
| CVE-2023-26437 | 2023-04-04 | rec-4.8.4 | 2023-03-29 | -6 | no | rec-4.8.4, rec-4.7.5, rec-4.6.6 | cd279418d3, 5174c955a5, 94fccab634 | exact | 4.6.6 | Advisory 2023-02; commit titles name the CVE: 4.8.4 cd279418d, 4.7.5 5174c955a, 4.6.6 94fccab63 (all 2023-03-29). |
| CVE-2023-50387 | 2024-02-14 | rec-5.0.2 | 2024-02-06 | -8 | yes | rec-5.0.2, rec-4.8.6, rec-4.9.3, rec-5.1.0 | 8cb2740c84, a4bc142623, 3a4cf27324, 15e973d6d8 | exact | 5.1.0 | KeyTrap. Advisory 2024-01: fixed in 4.8.6, 4.9.3, 5.0.2. Tag commits on the release branches: rec-5.0.2 8cb2740c8 "Backport of Keytrap to rec-5.0.x" (2024-02-06T09:36), rec-4.8.6 a4bc14262 (09:47), rec-4.9.3 3a4cf2732 (13:57). Master commit 15e973d6d (2024-02-09) "rec: CVE-2023-50387 and CVE-2023-50868" first appears in rec-5.1.0-alpha1. The branch tags were committed 2024-02-06 but the changelog says "Released 13th of February 2024" (embargo), NVD published 2024-02-14; the inventory fixes[] row says 5.1.0, which is the master line only. |
| CVE-2023-50868 | 2024-02-14 | rec-5.0.2 | 2024-02-06 | -8 | yes | rec-5.0.2, rec-4.8.6, rec-4.9.3, rec-5.1.0 | 8cb2740c84, a4bc142623, 3a4cf27324, 15e973d6d8 | exact | 5.1.0 | Closest-encloser proof / NSEC3 hash cost. Same commits and tags as CVE-2023-50387; adds max-nsec3-hash-computations-per-query=600 and aggressive-cache-max-nsec3-hash-cost=150. |
| CVE-2024-25583 | - | rec-5.0.4 | 2024-04-09 | - | no | rec-5.0.4, rec-4.9.5, rec-4.8.8 | 3365253d06, 3d16f2f49c, e1247da968 | exact | 4.8.8 | Not in by_product.pdns-rec but in fixes.pdns-rec (rec- commits). Advisory 2024-02: recursive-forwarding crash; fixed rec-4.8.8/4.9.5/5.0.4 (all 2024-04-09). NVD publication date for this CVE is not in the inventory. |
| CVE-2024-25590 | - | rec-5.0.9 | 2024-08-26 | - | no | rec-5.0.9, rec-4.9.9, rec-5.1.2 | 4775860c55, a2615edf7f, 884173b27f | exact | - | Not in by_product.pdns-rec but in fixes.pdns-rec. Advisory 2024-04: cache inefficiency from huge RRsets; fixed rec-4.9.9 (4775860c5), 5.0.9 (a2615edf7), 5.1.2 (884173b27). The inventory fixes[] sha 6083aa603 is a merge on a different branch and yields no fix tag. NVD publication date not in the inventory. |
| CVE-2025-59023 | 2026-02-09 | rec-5.3.1 | 2025-10-22 | -110 | no | rec-5.3.1, rec-5.1.8, rec-5.2.6 | 3fe2c79d24, e4f6ad5b92, 122665f2b6 | approximate | - | Advisory 2025-06: strict validation of received delegations. "rec: be more strict accepting delegations" (5.1.8 3fe2c79d2, 5.2.6 e4f6ad5b9, 5.3.1 122665f2b, all 2025-10-16 tags). Advisory does not split commits between 59023 and 59024. |
| CVE-2025-59024 | 2026-02-09 | rec-5.3.1 | 2025-10-22 | -110 | no | rec-5.3.1, rec-5.1.8, rec-5.2.6 | 3fe2c79d24, e4f6ad5b92, 122665f2b6, 26d0455614 | approximate | - | Advisory 2025-06, same batch as CVE-2025-59023 plus "Check to see if authoritative NS and/or address records are usable"; per-CVE mapping approximate. |
| CVE-2025-59029 | 2025-12-09 | rec-5.3.3 | 2025-11-25 | -14 | no | rec-5.3.3 | 6f13e9ecb9, 485732f128 | approximate | - | Advisory 2025-07: assertion on ANY after caching; fixed 5.3.3 (5.3.2 never released, no tag): 485732f12/6f13e9ecb "If we iterator the loop multiple times for ANY requests, authRecords might not be empty". |
| CVE-2025-59030 | 2025-12-09 | rec-5.3.3 | 2025-11-25 | -14 | no | rec-5.3.3, rec-5.2.7, rec-5.1.9 | 3a4436d7e5, 6f6d02b1f8, b51584b399 | exact | - | Advisory 2025-08: "Backport to 5.x: do proper validation of TCP notifies" in 5.1.9 (3a4436d7e), 5.2.7 (6f6d02b1f), 5.3.3 (b51584b39). |
| CVE-2026-0398 | 2026-02-09 | rec-5.3.5 | 2026-02-09 | 0 | no | rec-5.3.5, rec-5.1.10, rec-5.2.8 | 49fd19aeb0, c7a97a0ca0, b5ff23a0d4 | approximate | - | Advisory 2026-01 (CNAME chain cache poisoning): "rec: allowed names should not include names from CNAMEs that cannot be reached" in 5.1.10 (49fd19aeb), 5.2.8 (c7a97a0ca), 5.3.5 (b5ff23a0d). Advisory lists no commits; mapping by subject. |
| CVE-2026-24027 | 2026-02-09 | rec-5.3.5 | 2026-02-09 | 0 | no | rec-5.3.5, rec-5.1.10, rec-5.2.8 | 75b6da3445, 5bd9b30d69, 9eade498df | approximate | - | Advisory 2026-01 (increased incoming traffic): "Set a max on the number of visted IPs for a single qname/type" and companion commits (5.1.10 75b6da344, 5.2.8 5bd9b30d6, 5.3.5 9eade498d). Mapping by subject. |
| CVE-2026-33256 | 2026-04-22 | rec-5.3.6 | 2026-04-02 | -20 | no | rec-5.3.6, rec-5.4.1 | 0a31f06421, ddc593ca07 | approximate | - | Advisory 2026-03: "rec: limit size of incoming web request" 5.3.6 (0a31f0642), 5.4.1 (ddc593ca0). |
| CVE-2026-33257 | 2026-04-22 | rec-5.2.9 | 2026-04-02 | -20 | no | rec-5.2.9 | 8a71bde554, 7aebb0fd07, 6908f45814, 9d5d9a3d4d | approximate | - | The commits that NAME the CVE (6908f4581, 9d5d9a3d4: "Fixes for CVE-2026-33257; part of PowerDNS Security Advisory 2026-05", ext/yahttp only) are on auth branches (rel/auth-4.9.x) and are contained by NO rec- tag, so the inventory fixes[] row gives no rec- tag. The vendored-yahttp changes that reach the Recursor are 8a71bde55 (reqresp.cpp) and 7aebb0fd0 in rec-5.2.9 (2026-04-02), matched to the named commits by touched file and advisory (5.2.9 first fixed); per-commit mapping approximate. |
| CVE-2026-33258 | 2026-04-22 | rec-5.2.9 | 2026-04-02 | -20 | yes | rec-5.2.9, rec-5.3.6, rec-5.4.1 | d0d0afb01c, 2df249e3a9, 3ce2e8ae0a | approximate | - | Advisory 2026-03 (large entries in negative/aggressive NSEC(3) caches): "estimate size and refuse to cache big negcache and aggrcache entries" 5.2.9 (d0d0afb01), 5.3.6 (2df249e3a), 5.4.1 (3ce2e8ae0). |
| CVE-2026-33259 | 2026-04-22 | rec-5.2.9 | 2026-04-02 | -20 | no | rec-5.2.9, rec-5.3.6, rec-5.4.1 | 7029d225b4, a933caaf01, e7e105c143 | approximate | - | Advisory 2026-03 (concurrent RPZ transfers): "rec: work on a copy of PolicyZoneData while building the new RPZ zone" 5.2.9/5.3.6/5.4.1. |
| CVE-2026-33260 | 2026-04-22 | rec-5.2.9 | 2026-04-02 | -20 | no | rec-5.2.9 | b1f9b0d802, 038e38a248, 9e074364db | exact | - | Commits naming the CVE (038e38a24, 9e074364d, ext/yahttp only) are on auth branches and in no rec- tag. b1f9b0d80 "Fix two cases of lacking/wrong max size compares" (reqresp.cpp/.hpp, same size as 038e38a24) is in rec-5.2.9; advisory 2026-03 lists 5.2.9 as first fixed. Mapping approximate. |
| CVE-2026-33261 | 2026-04-22 | rec-5.2.9 | 2026-04-02 | -20 | yes | rec-5.2.9, rec-5.3.6, rec-5.4.1 | d6351bcb34, 177e4dc645, 5f3a386eac | approximate | - | Advisory 2026-03 (NSEC to NSEC3 transition, null pointer in aggressive cache): "rec: Prevent null-pointer dereference in aggressive NSEC cache" 5.2.9 d6351bcb3, 5.3.6 177e4dc64, 5.4.1 5f3a386ea. |
| CVE-2026-33262 | 2026-04-22 | rec-5.4.1 | 2026-04-02 | -20 | no | rec-5.4.1 | 2dd0b98935 | approximate | - | Advisory 2026-03 (cookie reply, only 5.4.0 affected): "rec: only check cookie if we sent one out" 5.4.1. |
| CVE-2026-33600 | 2026-04-22 | rec-5.2.9 | 2026-04-02 | -20 | no | rec-5.2.9, rec-5.3.6, rec-5.4.1 | b297bb729c, 1d377042e0, 9a49123aab | approximate | - | Advisory 2026-03 (RPZ null pointer): "rec: throw if no valid SOA found (YWH-PGM6095-168)" 5.2.9 b297bb729, 5.3.6 1d377042e, 5.4.1 9a49123aa; mapping by subject, advisory lists no commits. |
| CVE-2026-33601 | 2026-04-22 | rec-5.2.9 | 2026-04-02 | -20 | yes | rec-5.2.9, rec-5.3.6, rec-5.4.1 | 1f879592f7, a609000641, 93f61a82e0 | approximate | - | Advisory 2026-03 (zonemd null pointer, zoneToCache): "rec: zonemd null pointer dereference on non-standard schemes" 5.2.9 1f879592f, 5.3.6 a60900064, 5.4.1 93f61a82e. |

## Gaps

- news_edits[] left empty: not determinable. Since rec-4.1.0 the changelog file at a release tag is frozen at the alpha/beta state and point-release sections are written on master only (and for 4.0.3..4.0.9 / 3.6.3 / 3.6.4 / 3.7.2 / 3.7.3 the section does not exist at its own tag), so there is no contemporaneous text to diff against the current text.
- Stage-2 changelog_entries are kept unchanged but are incomplete for default/limit changes: the keyword filter is case-sensitive, so 4.5.2 'Change nsec3-max-iterations default to 150.' (PR 10477) and rec-5.0.0-rc1 'Change default of nsec3-max-iterations to 50.' (PR 13478) were dropped (rec-4.5.2 total_entries 6, kept 2), and the KeyTrap lines 'Security advisory 2024-01: CVE-2023-50387 and CVE-2023-50868' for 4.8.6, 4.9.3 and 5.0.2 were not parsed (total_entries 1, kept 0; the .rst lines are indented one space short). The evidence for these rows is therefore in default_changes[].documentation, not in releases[].changelog_entries.
- RFC 5011: no automated trust-anchor rollover was found at any tag. docs/dnssec.rst at rec-5.4.0 states 'it has no support for RFC 5011 key rollover and does not persist a changed root trust anchor to disk'. Only the REVOKE-bit rejection (6f2088b4f, rec-4.4.0-alpha2) and static root-DS additions (2017 KSK 20326, 2018 removal of 19036, 2025 KSK 38696) were found. An absence claim is bounded by the greps done (docs/dnssec.rst, pdns/validate.cc, root-dnssec.hh); the whole tree was not audited at every tag.
- Ed448 (algorithm 16) validation: optional libdecaf build (decafsigners.cc under 'if LIBDECAF' in recursordist/Makefile.am at rec-4.0.6) and absent from the Meson build seen at rec-5.4.0; the first tag supporting it and its status in shipped packages were not determined, so no Ed448 row. ECDSA (algorithm 13/14) is present from rec-4.0.0-alpha1 (OpenSSL) but its introducing commit was not searched. GOST (algorithm 12) was not investigated beyond the 4.1.0-rc1 crash-fix changelog line. No algorithm other than 5/7 (auto-switch-off, rec-4.9.0) was found disabled by default.
- The initial appearance of algorithms/validation code before 12ce523e7 (Dec 2015) and the exact per-commit split between CVE pairs marked attribution 'approximate' (e.g. CVE-2018-10851/14626/14644, CVE-2020-10030/10995/12244, CVE-2025-59023/59024, CVE-2026-0398/24027, CVE-2026-33258/59/61/33600/33601) rest on advisory version lists plus commit subjects; the advisories do not name commits. The fix TAG is exact for these, the fix COMMIT is a best match.
- No rec-3.1.3, rec-3.1.5 or rec-3.1.6 tags exist in the clone, and rec-3.1.7.2 has a tree identical to rec-3.1.7.1 (git rev-parse rec-3.1.7.1^{tree} rec-3.1.7.2^{tree}). CVE-2008-1637 / CVE-2008-3217 (real fix releases 3.1.5 and 3.1.6, March/May 2008) therefore show rec-3.1.7.1 (2009-08-02) as the first tag containing the code, and CVE-2009-4009/4010 show rec-3.2; their latencies (487, 380, 57 days) are artefacts of the missing tags. CVE-2006-4252 and CVE-2009-4009/4010 have no identifiable fix commit.
- Security-release tag commits precede public release: rec-5.0.2 / 4.8.6 / 4.9.3 tags are dated 2024-02-06 but the changelog says 'Released 13th of February 2024' (embargo; NVD 2024-02-14), so latency_days -8 is against the commit date; against the changelog date it is -1. Every cve_fixes row carries fix_changelog_released_text so the same check can be made for other security releases (e.g. rec-5.3.1 tag dated 2025-10-22).
- CVE-2024-25583 and CVE-2024-25590 are attributed to the Recursor only via inventory fixes.pdns-rec (not in by_product.pdns-rec), so their NVD publication dates and latency are absent (null). CVE-2025-30195 (rec-5.2.1, advisory 2025-01) and CVE-2016-6172 (rec-4.0.1 changelog; NVD attributes it to the Authoritative Server) appear in changelogs but not in by_product.pdns-rec; not added.
- Recursor DNSSEC validation CVEs present in the tree's security advisories but NOT yet in cve_inventory.json (NVD lag): CVE-2026-52688 'RRSIGs with too few labels can lead to bypass of DNSSEC wildcard validation' and CVE-2026-52686 'Wildcard CNAME proof validation bypass' (advisory 2026-10, fixed 5.2.12 / 5.3.9 / 5.4.4), CVE-2026-42390 ZONEMD validation bypass and CVE-2026-33612 ZoneToCache poisoning (advisory 2026-08, fixed 5.2.11 / 5.3.8 / 5.4.3), CVE-2026-52682 (advisory 2026-11, fixed 5.2.13 / 5.3.10 / 5.4.5). Not emitted as cve_fixes rows because the inventory does not attribute them; fix tags come from the advisories only and were not commit-verified.
- inventory fixes.pdns-rec disagrees with the tags found for: CVE-2023-50387/50868 (inventory 5.1.0; earliest stable tag rec-5.0.2, also 4.8.6 and 4.9.3), CVE-2020-25829 (inventory 4.2.5; rec-4.1.18 is earlier), CVE-2024-25590 and CVE-2026-33257/33260 (inventory shas are merges/auth-branch commits contained by no rec- tag), CVE-2015-1868 (inventory sha not in any rec- tag). The inventory also lists dnsdist/auth-only CVEs under fixes.pdns-rec (CVE-2009-4492, CVE-2012-0206, CVE-2018-1046, CVE-2019-9512/9514/9515, CVE-2023-6193, CVE-2026-33608..33611, CVE-2026-49975); they are not Recursor fixes and are not emitted.
- CVE-2017-15093 (api-config-dir, 3.x also affected up to 3.7.4) and CVE-2016-7068 on the 3.7 line: no rec-3.7.x tag after 3.7.4 carries a fix for 15093; only the 4.0.7 fix is recorded.
- Default-change rows cover settings found by scanning rec-main.cc / pdns_recursor.cc / table.py defaults at every non-alias release tag for: dnssec, nsec3-max-iterations, dnssec-disabled-algorithms, aggressive-nsec-cache-size, aggressive-cache-min-nsec3-hit-ratio, signature-inception-skew, max-cache-bogus-ttl, allow-trust-anchor-query, trustanchorfile(-interval), dnssec-log-bogus and the seven KeyTrap limits. aggressive-cache-min-nsec3-hit-ratio (2000, 4.9.0-alpha1), max-cache-bogus-ttl (3600, 4.2.0-beta1) and allow-trust-anchor-query (no) were seen but given no row because they are cache tuning / diagnostics rather than validation-outcome defaults. Other DNSSEC-relevant defaults (root-nx-trust, ECS/DNSSEC interplay, x-dnssec-names) were not analysed.

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
