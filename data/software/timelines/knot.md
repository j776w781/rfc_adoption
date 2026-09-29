# Knot DNS (knot) DNSSEC timeline

Generated 2026-09-28 from `out/software_repos/knot.git` (bare clone), `data/software/cve_inventory.json` and `out/analysis/cve_crossref.json`. Machine-readable twin: `data/software/timelines/knot.json`.

**Releases:** 216 tags (174 stable, 42 pre-release/dev/duplicate), 2011-02-02 .. 2026-09-08. Changelog: none (v0.1-v0.3, v0.8), `RELNOTES` (v0.8.1..v1.3.x), `NEWS` (v1.4.0-beta..v3.6.0). Release date = commit date of `<tag>^{commit}`.

1.6.x LTS (2014-10 .. 2016-08) ran alongside 2.0-2.3; since 2.5 two minor lines are maintained in parallel (e.g. 2.4.5 with 2.5.2, 3.4.10 with 3.5.4), so the same fix appears as different commits on each line. 1.99.0/1.99.1 are development previews of 2.0.

## How to verify a row

```
C=out/software_repos/knot.git
git -C $C log -1 --format=%cI <tag>^{commit}          # release date
git -C $C show <tag>:NEWS | grep -n -F "<changelog line>"  # entry present at the tag (RELNOTES for <= 1.3.x)
git -C $C tag --contains <commit> | grep -x <tag>     # commit is in the release
git -C $C show <commit> --stat                        # what it changed
```

## Support added / defaults changed / limits changed

| version | date | stable | kind | default change | mechanism | changelog line | commit(s) | in tag |
|---|---|---|---|---|---|---|---|---|
| 0.8 | 2011-11-03 | yes | support-added | no | other | DNSSEC | 1b8f0c523b | yes |
| 0.8 | 2011-11-03 | yes | support-added | no | nsec3 | NSEC3 | 1858df0cf5 | yes |
| 1.4.0-beta | 2013-10-28 | no | support-added | no | other | Experimental automatic DNSSEC signing | 16529a00c7, 3a3459445e, dbc8fc45d5, 3107c34bdb | yes |
| 1.4.0-rc1 | 2013-11-20 | no | support-added | no | dnskey | Support for DNSSEC key pre-publication | 3976853596 | yes |
| 1.4.0-rc2 | 2013-12-13 | no | support-added | no | alg-gost | DNSSEC: support for GOST algorithm | a8244839df | yes |
| 1.4.2 | 2014-01-27 | yes | default-changed | yes | rrsig | DNSSEC: Refresh signatures earlier (3 days before their expiration with the default signature lifetime) | 704e2bff9a | yes |
| 1.6.1 | 2014-12-12 | yes | support-added | no | dnskey | DNSSEC Single Type Signing Scheme is now supported | d645f19f41 | yes |
| 1.6.3 | 2015-04-08 | yes | support-added | no | cds-cdnskey | CDS and CDNSKEY support in zone parser | 5ff97dfb7c | yes |
| 2.0.0 | 2015-06-26 | yes | support-added | no | other | DNSSEC: separate library, switch to GnuTLS, new utilities | c907cd675e | yes |
| 2.0.0 | 2015-06-26 | yes | support-added | yes | dnskey | DNSSEC: basic KASP support (generate initial keys, ZSK rollover) | 8aaba1c994, 4a85667e72 | yes |
| 2.1.0 | 2016-01-14 | yes | support-added | no | other | DNSSEC: Support for cryptographic tokens via PKCS #11 interface | 0b60906aa2 | yes |
| 2.1.0 | 2016-01-14 | yes | support-added | no | other | DNSSEC: Experimental support for online signing | 7711ddacf1 | yes |
| 2.3.0 | 2016-08-09 | yes | support-added | no | other | DNSSEC policy can be defined in server configuration | b83e49365e | yes |
| 2.3.0 | 2016-08-09 | yes | support-added | yes | nsec3 | Automatic NSEC3 resalt according to DNSSEC policy | dfc39e540e | yes |
| 2.4.0 | 2017-01-18 | yes | default-changed | yes | dnskey | Automatic deletion of retired DNSSEC keys | a7c72081a0 | yes |
| 2.4.3 | 2017-04-10 | yes | default-changed | yes | other | The default TSIG algorithm for utilities input is HMAC-SHA256 | 3dd88d6173 | yes |
| 2.5.0 | 2017-06-05 | yes | support-added | no | cds-cdnskey | KSK rollover support using CDNSKEY and CDS in the automatic DNSSEC signing | be44184f66, 0d8dadb47c, 3fbf23dee0 | yes |
| 2.5.3 | 2017-07-14 | yes | support-added | no | dnskey | CSK rollover support for Single-Type Signing Scheme | a4cbcf9b14, f0e9d0a2e0 | yes |
| 2.5.5 | 2017-09-29 | yes | default-changed | yes | rrsig | Generated RRSIG records have inception time 90 minutes in the past | a1283c9c02 | yes |
| 2.6.0 | 2017-09-29 | yes | support-added | no | other | On-slave (inline) signing support | 90cb18eece, 928fa6a8b5 | yes |
| 2.6.0 | 2017-09-29 | yes | support-added | no | dnskey | Automatic DNSSEC key algorithm rollover | fd9c7283ed, 6cea1fb0f3 | yes |
| 2.6.0 | 2017-09-29 | yes | support-added | no | alg-eddsa | Ed25519 algorithm support in DNSSEC (requires GnuTLS 3.6.0) | 662b449b7f, dcb7ac0e6e, 5cb637cbe8, f9521dda2b | yes |
| 2.6.1 | 2017-11-02 | yes | support-added | no | nsec3 | NSEC3 Opt-Out support in the DNSSEC signing | 28e9063c45, d4fabf9905 | yes |
| 2.6.1 | 2017-11-02 | yes | support-added | no | cds-cdnskey | New CDS/CDNSKEY publish configuration option | 5a242bfc0d, f503b0d2fb | yes |
| 2.6.2 | 2017-11-23 | yes | support-added | no | dnskey | CSK algorithm rollover and (KSK, ZSK) <-> CSK rollover support | 34f7638e9e | yes |
| 2.7.0 | 2018-08-03 | yes | support-added | no | other | Online Signing support for automatic key rollover | 36bb621616 | yes |
| 2.7.4 | 2018-11-13 | yes | support-added | no | cds-cdnskey | Reintroduced 'rollover' configuration option for CDS/CDNSKEY publication | e16da2dc7 (doc-only; schema value since v2.6.1) | yes |
| 2.7.5 | 2019-01-07 | yes | default-changed | yes | dnskey | Manually generated KSK is 'ready' by default | 8e2530f02c | yes |
| 2.8.0 | 2019-03-05 | yes | support-added | no | dnskey | New offline-KSK mode of operation | 8bb97c6ad0 | yes |
| 2.8.0 | 2019-03-05 | yes | support-added | no | other | Configurable multithreaded DNSSEC signing for large zones | 59ffc11226 | yes |
| 2.8.0 | 2019-03-05 | yes | support-added | no | dnskey | New knotc trigger 'zone-key-rollover' for immediate DNSKEY rollover | c82fb9c4b8 | yes |
| 2.8.0 | 2019-03-05 | yes | support-added | no | cds-cdnskey | New 'double-ds' option for CDS/CDNSKEY publication | 5c9ef20c0b | yes |
| 2.8.0 | 2019-03-05 | yes | default-changed | yes | cds-cdnskey | Changed configuration default for 'cds-cdnskey-publish' to 'rollover' | 7f609f3dfb | yes |
| 2.8.0 | 2019-03-05 | yes | default-changed | yes | ds-digest | Keymgr no longer prints DS for algorithm SHA-1 | 6cf74f5d7a | yes |
| 2.8.4 | 2019-09-24 | yes | support-added | no | cds-cdnskey | Automatic uploading of DS records to parent zone using DDNS, see 'policy.ds-push' configuration option | 5c375a9da2 | yes |
| 2.9.0 | 2019-10-10 | yes | support-added | no | rrsig | New DNSSEC policy configuration option 'rrsig-pre-refresh' for reducing frequency of the zone signing event | 44d12f83d7 | yes |
| 2.9.3 | 2020-03-03 | yes | support-added | no | alg-eddsa | Enabled testing support for Ed448 DNSSEC algorithm (requires GnuTLS 3.6.12+ and not-yet-released Nettle 3.6+) | 3802e36bfe | yes |
| 2.9.3 | 2020-03-03 | yes | support-added | no | alg-eddsa | keymgr can import Ed25519 and Ed448 keys in the BIND format (Thanks to Conrad Hoffmann) | 3802e36bfe | yes |
| 2.9.4 | 2020-05-05 | yes | support-added | no | other | Module onlinesign allows KSK + ZSK mode | 19f44c0d85 | yes |
| 3.0.0 | 2020-09-09 | yes | support-added | no | validation | New DNSSEC validation mode | 7b97d163f3 | yes |
| 3.0.0 | 2020-09-09 | yes | support-added | no | other | New kzonesign utility — an interface for manual DNSSEC signing | b3107054c2 | yes |
| 3.0.0 | 2020-09-09 | yes | support-added | no | trust-anchor-5011 | New KSK revoked state (RFC 5011) in manual DNSSEC key management mode | 1ad6ddf0d0 | yes |
| 3.0.0 | 2020-09-09 | yes | support-added | no | alg-ecdsa | Deterministic signing with ECDSA algorithms (requires GnuTLS 3.6.10+) | 7803589738, 03029bcbfe | yes |
| 3.0.2 | 2020-11-11 | yes | default-changed | yes | other | libdnssec respects local GnuTLS policy — affects DNSSEC operations and Knot Resolver | 5994a92c04 | yes |
| 3.0.7 | 2021-06-16 | yes | support-added | no | ds-digest | knotd: new configuration policy option for CDS digest algorithm setting #738 | 9e41b3a8e4 | yes |
| 3.0.8 | 2021-07-16 | yes | support-added | no | other | knotd: new policy configuration option for disabling some DNSSEC safety features #741 | 8d200ccec5 | yes |
| 3.1.0 | 2021-08-01 | yes | support-added | no | other | knotd: support for ZONEMD validation and generation | 66bc4fc33f, 8c35bc8c55 | yes |
| 3.1.0 | 2021-08-01 | yes | default-changed | yes | nsec3 | knotd: TTL of generated NSEC(3) records is set to min(SOA TTL, SOA minimum) | f86cc39e0e | yes |
| 3.1.0 | 2021-08-01 | yes | default-changed | yes | nsec3 | knotd: TTL of generated NSEC3PARAM is equal to TTL of NSEC3 records | 99e401a5d1 | yes |
| 3.1.6 | 2022-02-08 | yes | support-added | no | cds-cdnskey | knotd: new submission configuration option for delayed KSK post-activation (see 'submission.parent-delay') | bb1bd60c4a | yes |
| 3.1.6 | 2022-02-08 | yes | support-added | no | validation | kzonesign: added multithreaded DNSSEC validation mode (see '--verify') | 2a3f1c5c8f | yes |
| 3.2.0 | 2022-08-22 | yes | support-added | no | dnskey | knotd: new incremental DNSKEY management for multi-signer deployment (see 'policy.dnskey-management') | 8a1f9fd90d | yes |
| 3.2.0 | 2022-08-22 | yes | support-added | no | nsec3 | knotd: NSEC3 salt is changed with every ZSK rollover if lifetime is set to -1 | 89662f91bf | yes |
| 3.2.0 | 2022-08-22 | yes | support-added | no | other | knotd: DNSSEC-related records can be updated via DDNS | 1f9f05d847 | yes |
| 3.2.0 | 2022-08-22 | yes | default-changed | yes | nsec3-iterations | knotd: default value for 'policy.nsec3-iterations' was lowered to 0 | 0009836974 | yes |
| 3.2.0 | 2022-08-22 | yes | default-changed | yes | rrsig | knotd: default value for 'policy.rrsig-refresh' is propagation delay + zone maximum TTL | 084c8ab842 | yes |
| 3.2.0 | 2022-08-22 | yes | limit-changed | yes | rrsig | knotd: server fails to load configuration if 'policy.rrsig-refresh' is too low | 084c8ab842, d8b1e148f7 | yes |
| 3.3.0 | 2023-08-28 | yes | support-added | no | dnskey | knotd: new multi-signer operation mode (see 'policy.dnskey-sync' and 'DNSSEC multi-signer') | 92e6be3cc2 | yes |
| 3.3.3 | 2023-12-13 | yes | default-changed | yes | rrsig | knotd: increased default for 'policy.rrsig-refresh' by (0.1 * 'rrsig-lifetime') | 3c7449eafa | yes |
| 3.3.5 | 2024-03-06 | yes | support-added | no | other | knotd: new module mod-authsignal for automatic authenticated DNSSEC bootstrapping records synthesis (Thanks to | b37888237c | yes |
| 3.4.0 | 2024-09-02 | yes | limit-changed | yes | validation | knotd: DNSSEC validation requires the remaining RRSIG validity is longer than 'rrsig-refresh' | a7a739faab | yes |
| 3.4.0 | 2024-09-02 | yes | support-added | no | validation | knotd: new event for automatic DNSSEC revalidation | a7a739faab, e8965be59b | yes |
| 3.4.0 | 2024-09-02 | yes | support-added | no | validation | knotc: new command for explicit triggering DNSSEC validation (see 'zone-validate' command) | a7a739faab | yes |
| 3.4.6 | 2025-04-10 | yes | default-changed | yes | other | knotd: default TSIG algorithm is now 'hmac-sha256' | ff9e7365a7 | yes |
| 3.4.7 | 2025-06-04 | yes | support-added | no | ds-digest | knotd: semantic checks support DS algorithms 5 and 6 | 7719d83eaa | yes |
| 3.5.0 | 2025-09-18 | yes | support-added | no | validation | knotd: external zone validation (see 'External validation') | 8ccc39d8dc | yes |
| 3.5.0 | 2025-09-18 | yes | support-added | no | other | knotd: multiple keystores can be specified per policy (see 'DNSSEC multiple keystores') | 34cb1aef7c | yes |
| 3.5.0 | 2025-09-18 | yes | default-changed | yes | nsec3 | knotd: new default value of 'policy.nsec3-salt-length' is 0 | edcb6b09f7 | yes |
| 3.5.6 | 2026-07-20 | yes | support-added | no | other | libknot: added support for EDE code 33 (Negative Trust Anchor) (Thanks to Babak Farrokhi) | 652b4b0c84 | yes |
| 3.6.0 | 2026-09-08 | yes | support-added | no | other | knotd: DELEG-aware zone signing (see 'policy.deleg-adt') | 756dcce25e | yes |
| 3.6.0 | 2026-09-08 | yes | support-added | no | other | knotd: optional jitter for DNSSEC events (see 'policy.dnssec-jitter') | a80a723bc4 | yes |
| 3.6.0 | 2026-09-08 | yes | support-added | no | validation | kdig: per zone DNSSEC answer validation (see '+validate') | 26358f91f3 | yes |
| 3.6.0 | 2026-09-08 | yes | default-changed | yes | rrsig | knotd: default value for 'policy.rrsig-pre-refresh' changed to 0.005 * 'policy.rrsig-lifetime' | 87d1c94222 | yes |
| 3.6.0 | 2026-09-08 | yes | limit-changed | yes | nsec3-iterations | knotd: the maximum allowed number of NSEC3 iterations is restricted to 256 | c9b863e42f, 9e915de7c4 | yes |

## Default changes (before / after)

| version | date | change | before | after | on upgrade | opt-in | commits | attribution |
|---|---|---|---|---|---|---|---|---|
| 1.4.2 | 2014-01-27 | RRSIG refresh 3 days before expiration | signatures regenerated when they expire (1.4.0/1.4.1: zone event scheduled at expires_at) | signatures regenerated 3 days before expiration (libknot/dnssec/policy.c; NEWS: "3 days before their expiration with the default signature lifetime") | yes | no | 704e2bff9a | exact |
| 2.0.0 | 2015-06-26 | default signing algorithm RSASHA256 (first built-in KASP policy) | no built-in policy in 1.x (keys generated externally, e.g. with BIND dnssec-keygen, into dnssec-keydir); the 1.99.1 development preview shipped the first default policy with RSASHA512 (8aaba1c99: policy->algorithm = RSA_SHA512, ksk 2048, zsk 1024) | keymgr policy default: algorithm RSASHA256 (8), KSK 2048 bits, ZSK 1024 bits (src/dnssec/lib/kasp/policy.c; doc/configuration.rst@v2.0.0:450-458) | no | no | 4a85667e72, 8aaba1c994 | exact |
| 2.1.0 | 2016-01-14 | default signing algorithm ECDSAP256SHA256; default key size 256 | RSASHA256, KSK 2048 / ZSK 1024 (2.0.x) | ECDSAP256SHA256 (13), KSK and ZSK 256 bits; per-algorithm size table: RSA* zsk 1024 / ksk 2048, ECDSAP384 384 (src/dnssec/lib/kasp/policy.c DEFAULT_KEY_SIZES) | no | no | 2e64ea6d08, 8c298aa490, 855238534b | exact |
| 2.2.0 | 2016-04-26 | default RSA key size 2048 for ZSK as well as KSK | RSA policies: ZSK 1024 / KSK 2048 (2.1.x DEFAULT_KEY_SIZES); keymgr required an explicit key size | dnssec_algorithm_key_size_default(): RSA* 2048, DSA 1024, ECDSAP256 256, ECDSAP384 384 for both KSK and ZSK; keymgr picks it when no size is given (doc/reference.rst@v2.3.0 ksk-size "1024 (dsa*), 2048 (rsa*), 256 (ecdsap256*), 384 (ecdsap384*)") | no | no | 6a7da32dd1, 8d5b25d539, 3d5626ab17 | exact |
| 2.3.0 | 2016-08-09 | automatic NSEC3 re-salting every 30 days | NSEC3 salt fixed once set (2.2.x keymgr policy) | policy.nsec3-salt-lifetime default 30 days, nsec3-salt-length default 8, nsec3-iterations default 10 in the schema (doc/reference.rst@v2.3.0:687 wrongly says 5 until 3.0.6) | yes | no | dfc39e540e, b83e49365e | exact |
| 2.4.0 | 2017-01-18 | retired DNSSEC keys deleted automatically | retired keys stayed in the KASP database | retired keys are removed after their remove timestamp | yes | no | a7c72081a0 | exact |
| 2.5.5 | 2017-09-29 | RRSIG inception 90 minutes in the past | inception = signing time | inception = signing time - 90 min, expiration = signing time + rrsig-lifetime (rrset-sign.c RRSIG_INCEPT_IN_PAST) | yes | no | a1283c9c02 | exact |
| 2.6.0 | 2017-09-29 | DSA (algorithms 3 and 6) no longer supported | DSA/DSA-NSEC3-SHA1 keys accepted by libdnssec (key.h@v2.0.0) | DSA removed from the enum; policies with algorithm 3/6 are rejected ("DSA algorithm no longer supported" in conf checks) | yes | no | da9e7ceb8f | exact |
| 2.7.0 | 2018-08-03 | minimum RSA key size raised to 1024 bits | RSA 512..4096 accepted (algorithm.c limits .min = 512) | RSA 1024..4096; default stays 2048 | yes | no | d0f52e7c40 | exact |
| 2.7.5 | 2019-01-07 | keymgr-generated KSK is ready by default | manually generated KSK waited in the published state | keymgr generate ... ksk=yes creates the key in ready state, so submission proceeds immediately | yes | no | 8e2530f02c | exact |
| 2.8.0 | 2019-03-05 | cds-cdnskey-publish default always -> rollover | CDS/CDNSKEY for the active KSK published permanently (default always since 2.5.0/2.6.1) | CDS/CDNSKEY published only during the KSK submission phase (schema.c C_CDS_CDNSKEY CDS_CDNSKEY_ROLLOVER; doc/reference.rst@v2.8.0 "Default: rollover") | yes | no | 7f609f3dfb | exact |
| 2.8.0 | 2019-03-05 | keymgr ds no longer prints the SHA-1 digest | keymgr ds printed SHA-1, SHA-256 and SHA-384 DS records | SHA-1 DS omitted | yes | no | 6cf74f5d7a | exact |
| 3.0.2 | 2020-11-11 | libdnssec honours the local GnuTLS crypto policy | algorithm support decided by libdnssec alone | dnssec_algorithm_key_support()/digest_support() return false for algorithms the system policy disables (e.g. SHA-1 on RHEL 9); signing/validation with such keys fails | yes | no | 5994a92c04 | exact |
| 3.1.0 | 2021-08-01 | NSEC/NSEC3/NSEC3PARAM TTL = min(SOA TTL, SOA minimum) | NSEC(3) TTL = SOA minimum | NSEC(3) TTL = min(SOA TTL, SOA minimum); NSEC3PARAM TTL follows NSEC3 | yes | no | f86cc39e0e, 99e401a5d1 | exact |
| 3.2.0 | 2022-08-22 | default policy.nsec3-iterations 10 -> 0 | schema default 10 (src/knot/conf/scheme.c@v2.3.0:166 .. schema.c@v3.1.9); documented as 5 until 3.0.6 | schema default 0 (schema.c C_NSEC3_ITER); doc/reference.rst "Default: 0" | yes | no | 0009836974 | exact |
| 3.2.0 | 2022-08-22 | default policy.rrsig-refresh computed; too-low value is a hard error | rrsig-refresh default 7 days; too-low values warned | default = propagation-delay + zone-max-ttl; zone signing fails with an error if rrsig-refresh is too low (NEWS overstates it as a config-load failure) | yes | no | 084c8ab842 | exact |
| 3.3.3 | 2023-12-13 | default policy.rrsig-refresh increased by 0.1 * rrsig-lifetime | propagation-delay + zone-max-ttl | propagation-delay + zone-max-ttl + 0.1 * rrsig-lifetime | yes | no | 3c7449eafa | exact |
| 3.4.0 | 2024-09-02 | validation requires remaining RRSIG validity > rrsig-refresh | any unexpired RRSIG accepted by zone.dnssec-validation | RRSIGs expiring within rrsig-refresh make validation fail (validation re-run as a scheduled event) | yes | no | a7a739faab | exact |
| 3.5.0 | 2025-09-18 | default policy.nsec3-salt-length 8 -> 0 | schema default 8 (schema.c C_NSEC3_SALT_LEN since 2.3.0) | schema default 0; empty salt (notice added in 3.4.3, 7ed353619) | yes | no | edcb6b09f7 | exact |
| 3.6.0 | 2026-09-08 | NSEC3 iterations capped at 256 | policy.nsec3-iterations 0..65535 accepted | policy.nsec3-iterations 0..256 (CONF_NSEC3_MAX_ITERS); NSEC3PARAM with more iterations refused in zone updates; NSEC3PARAM changes via DDNS refused | yes | no | c9b863e42f, 9e915de7c4, 5e2120fa67 | exact |
| 3.6.0 | 2026-09-08 | default policy.rrsig-pre-refresh 1 hour -> 0.005 * rrsig-lifetime | 1 hour (since 2.9.0) | 0.005 * rrsig-lifetime (100.8 min with the 14-day default lifetime) | yes | no | 87d1c94222 | exact |

`(!)` marks a commit not contained in the tag; none are.

## Documented policy defaults over time (doc/reference.rst, stable tags)

| option | 2.3.0 | change |
|---|---|---|
| algorithm | ecdsap256sha256 (2.1.0: was rsasha256 in 2.0.x) | unchanged through 3.6.0 |
| ksk-size / zsk-size | 1024 (dsa*), 2048 (rsa*), 256 (ecdsap256*), 384 (ecdsap384*) | 2.6.0: dsa dropped, ed25519 256 added; 2.9.3: ed448 456 added |
| nsec3-iterations | 5 documented / 10 in schema | 3.0.6: doc corrected to 10; 3.2.0: 0; 3.6.0: maximum 256 |
| nsec3-salt-length | 8 | 3.5.0: 0 |
| nsec3-salt-lifetime (nsec3-resalt until 2.3.0) | 30 days | 2.8.2: infinity allowed; 3.2.0: -1 = resalt at every ZSK rollover |
| cds-cdnskey-publish | (option since 2.6.1) always | 2.7.4: rollover value; 2.8.0: default rollover |
| cds-digest-type | (option since 3.0.7) sha256 | unchanged |
| rrsig-lifetime | 14 days | unchanged |
| rrsig-refresh | 7 days | 3.2.0: propagation-delay + zone-max-ttl; 3.3.3: + 0.1 * rrsig-lifetime |
| rrsig-pre-refresh | (option since 2.9.0) 1 hour | 3.6.0: 0.005 * rrsig-lifetime |
| propagation-delay | 1 day | 2.7.4: 1 hour |
| ksk-lifetime | (2.5.0) infinity | unchanged (0 = infinity) |
| zsk-lifetime | 30 days | unchanged |
| reproducible-signing | (3.0.0) off | unchanged |
| dnskey-management | (3.2.0) full | unchanged |

Source: `scratchpad/knot/docdefaults.py` diff of `doc/reference.rst` `*Default:*` lines at every stable tag >= v2.3.0, cross-checked against `src/knot/conf/schema.c`.

## Algorithm support (libdnssec / libknot live in this repository)

| algorithm | code | event | version (first stable) | date | commit(s) | in tag | evidence |
|---|---|---|---|---|---|---|---|
| RSASHA256 / RSASHA512 | 8 / 10 | signing support added | 1.4.0-beta (1.4.0) | 2013-10-28 | 16529a00c7, 3a3459445e | yes | src/libknot/consts.h@v1.4.0:170-172; NEWS 1.4.0-beta "Experimental automatic DNSSEC signing" |
| ECDSAP256SHA256 / ECDSAP384SHA384 | 13 / 14 | signing/verification support added | 1.4.0-beta (1.4.0) | 2013-10-28 | dbc8fc45d5, 3107c34bdb, 65c7147e0a | yes | src/libknot/dnssec/sign.c@v1.4.0:549-598; NEWS 1.4.0-rc2 "fixed detection of ECDSA support" |
| GOST R 34.10-2001 | 12 | support added | 1.4.0-rc2 (1.4.0) | 2013-12-13 | a8244839df | yes | NEWS 1.4.0-rc2 "DNSSEC: support for GOST algorithm"; src/libknot/dnssec/sign.c@v1.4.0:723-825 (OpenSSL GOST engine) |
| GOST R 34.10-2001 | 12 | support removed (GnuTLS switch) | 2.0.0 | 2015-06-26 | c907cd675e | yes | src/dnssec/lib/dnssec/key.h@v2.0.0:88-96 has no algorithm 12; NEWS 2.0.0 "separate library, switch to GnuTLS" |
| RSASHA256 / RSASHA512 | 8 / 10 | default algorithm RSASHA256 | 2.0.0 | 2015-06-26 | 4a85667e72 | yes | src/dnssec/lib/kasp/policy.c |
| ECDSAP256SHA256 | 13 | default algorithm | 2.1.0 | 2016-01-14 | 2e64ea6d08 | yes | src/dnssec/lib/kasp/policy.c; doc/configuration.rst@v2.1.0 |
| DSA / DSA-NSEC3-SHA1 | 3 / 6 | support removed | 2.6.0 | 2017-09-29 | da9e7ceb8f | yes | src/dnssec/lib/dnssec/key.h@v2.6.0:86-94 |
| Ed25519 | 15 | support added | 2.6.0 | 2017-09-29 | 662b449b7f, dcb7ac0e6e, f9521dda2b | yes | NEWS 2.6.0 "Ed25519 algorithm support in DNSSEC (requires GnuTLS 3.6.0)" |
| Ed448 | 16 | support added (testing) | 2.9.3 | 2020-03-03 | 3802e36bfe | yes | NEWS 2.9.3 "Enabled testing support for Ed448"; src/libdnssec/key/algorithm.c@v2.9.3:101-103 (HAVE_ED448) |
| ECDSA deterministic signing | 13 / 14 | support added (policy.reproducible-signing) | 3.0.0 | 2020-09-09 | 7803589738, 03029bcbfe | yes | NEWS 3.0.0 "Deterministic signing with ECDSA algorithms (requires GnuTLS 3.6.10+)" |
| RSASHA1 / RSASHA1-NSEC3-SHA1 | 5 / 7 | deprecation notice for policy.algorithm < 8 | 3.2.0 | 2022-08-22 | 41cfe3558c | yes | NEWS 3.2.0 "new configuration check on deprecated DNSSEC algorithm"; src/knot/conf/tools.c |
| DS digest GOST R 34.11-2012 / SM3 | DS 5 / 6 | semantic-check support added | 3.4.7 | 2025-06-04 | 7719d83eaa | yes | NEWS 3.4.7 "semantic checks support DS algorithms 5 and 6" |
| libdnssec | - | merged into libknot | 3.6.0 | 2026-09-08 | 5bfafd9ce0 | yes | NEWS 3.6.0 "libs: libdnssec integrated into libknot"; src/libknot/dnssec/key.h@v3.6.0 |

## CVE fixes

| CVE | NVD published | fix tag | fix date | latency (days) | DNSSEC | fix commit(s) | note |
|---|---|---|---|---|---|---|---|
| CVE-2014-0486 | 2018-03-27 | v1.5.2 | 2014-09-08 | -1296 | no | fac2b82e8b(v1.5.2), 4dca5dbbf1(v1.5.2), 5cb0ba2f88(v1.5.2), e63439b025(v1.5.2), bd2a198dae(v1.5.2) | NVD: crash via crafted DNS message, fixed before 1.5.2. NEWS 1.5.2 does not name the CVE; its only matching entry is "Some RR parsing corner cases were not handled properly". Commits are the rrset-from-wire hardening merge (fac2b82e8) and its bounds-check parents. |
| CVE-2016-6171 | 2017-02-09 | v2.3.0 | 2016-08-09 | -184 | no | dde98863d0(v2.3.0), 85f3217b05(v2.3.0) | also fixed on the 1.6 LTS line in v1.6.8 (2016-08-09, merge c204b7f43); NEWS 2.3.0/1.6.8 name the CVE |
| CVE-2017-11104 | 2017-07-08 | v2.5.2 | 2017-06-23 | -15 | no | 74862ce015(v2.5.2) | TSIG; also fixed in v2.4.5 the same day (3dfbb674b). The CVE id appears in NEWS only in the untagged "2.3.4" section (first present at v2.5.7). |
| CVE-2018-1000002 | 2018-01-22 | n/a | n/a | n/a | n/a | - | Knot Resolver (kresd) CVE listed under "knot" only because the NVD keyword search "Knot DNS" matches "Knot Resolver"; not a Knot DNS issue (verified: id absent from Knot DNS NEWS and git log) |
| CVE-2018-10920 | 2018-08-02 | n/a | n/a | n/a | n/a | - | Knot Resolver (kresd) CVE listed under "knot" only because the NVD keyword search "Knot DNS" matches "Knot Resolver"; not a Knot DNS issue (verified: id absent from Knot DNS NEWS and git log) |
| CVE-2018-1110 | 2021-03-30 | n/a | n/a | n/a | n/a | - | Knot Resolver (kresd) CVE listed under "knot" only because the NVD keyword search "Knot DNS" matches "Knot Resolver"; not a Knot DNS issue (verified: id absent from Knot DNS NEWS and git log) |
| CVE-2019-10190 | 2019-07-16 | n/a | n/a | n/a | n/a | - | Knot Resolver (kresd) CVE listed under "knot" only because the NVD keyword search "Knot DNS" matches "Knot Resolver"; not a Knot DNS issue (verified: id absent from Knot DNS NEWS and git log) |
| CVE-2019-10191 | 2019-07-16 | n/a | n/a | n/a | n/a | - | Knot Resolver (kresd) CVE listed under "knot" only because the NVD keyword search "Knot DNS" matches "Knot Resolver"; not a Knot DNS issue (verified: id absent from Knot DNS NEWS and git log) |
| CVE-2019-19331 | 2019-12-16 | n/a | n/a | n/a | n/a | - | Knot Resolver (kresd) CVE listed under "knot" only because the NVD keyword search "Knot DNS" matches "Knot Resolver"; not a Knot DNS issue (verified: id absent from Knot DNS NEWS and git log) |
| CVE-2020-12667 | 2020-05-19 | n/a | n/a | n/a | n/a | - | Knot Resolver (kresd) CVE listed under "knot" only because the NVD keyword search "Knot DNS" matches "Knot Resolver"; not a Knot DNS issue (verified: id absent from Knot DNS NEWS and git log) |
| CVE-2022-32983 | 2022-06-20 | n/a | n/a | n/a | n/a | - | Knot Resolver (kresd) CVE listed under "knot" only because the NVD keyword search "Knot DNS" matches "Knot Resolver"; not a Knot DNS issue (verified: id absent from Knot DNS NEWS and git log) |
| CVE-2023-26249 | 2023-02-21 | n/a | n/a | n/a | n/a | - | Knot Resolver (kresd) CVE listed under "knot" only because the NVD keyword search "Knot DNS" matches "Knot Resolver"; not a Knot DNS issue (verified: id absent from Knot DNS NEWS and git log) |
| CVE-2026-39155 | 2026-07-23 | v3.5.4 | 2026-04-02 | -112 | yes | 605b3d1700(v3.4.10), 15647ab26d(v3.5.4) | mod-onlinesign NSEC successor bug (aggressive-NSEC downstream DoS). Fixed in v3.4.10 and v3.5.4, both released 2026-04-02 (v3.5.4 14 minutes earlier); CVE id not in NEWS, mapped from the NVD description. Inventory also lists it under kresd by keyword overlap. |

Negative latency = fix released before NVD publication (coordinated disclosure or late CVE assignment).

## Other security fixes without a CVE id

- 3.4.11 (2026-08-18): knotd: server crash on zone with NSEC3PARAM but without NSEC3 records (Thanks to Qifan Zhang) -- cdbe5ef16e
- 3.5.7 (2026-08-18): knotd: server crash on zone with NSEC3PARAM but without NSEC3 records (Thanks to Qifan Zhang) -- 68aab66aa0
- 3.5.8 (2026-09-04): knotd: unauthenticated TSIG chosen-prefix signing that enables DDNS forgery (Thanks to Gia Bui) -- 355fde8bb0

## Post-hoc NEWS edits (section text at v3.6.0 differs from the text at the release tag; versions >= 2.0.0)

- 2.0.1 (vs v3.6.0): added 1, removed 1
  - + Fix CNAME following when querying for NSEC RR type
  - - Fix CNAME following when quering for NSEC RR type
- 2.1.1 (vs v3.6.0): added 2, removed 2
  - + Fix server crash when an incoming transfer is in progress and reload is issued
  - + Select correct source address for UDP messages received on ANY address
  - - Fix server crash when an incomming transfer is in progress and reload is issued
  - - Select correct source address for UDP messages recieved on ANY address
- 2.4.0 (vs v3.6.0): added 1, removed 1
  - + Per zone module and global module inconsistency
  - - Per zone module and global module insconsistency
- 2.4.1 (vs v3.6.0): added 1, removed 1
  - + Introduce check of minimum timeout for next refresh
  - - Introduce check of minumum timeout for next refresh
- 2.5.2 (vs v3.6.0): added 1, removed 1
  - + CVE-2017-11104: Improper TSIG validity period check can allow TSIG forgery (Thanks to Synacktiv!)
  - - Improper TSIG validity period check can allow TSIG forgery (Thanks to Synacktiv!)
- 2.5.3 (vs v3.6.0): added 1, removed 1
  - + Allowed binding to non-local addresses for TCP (Thanks to Julian Brost!)
  - - Allowed binding to non-local adresses for TCP (Thanks to Julian Brost!)
  - - CVE-2017-11104: Improper TSIG validity period check can allow TSIG forgery (Thanks to Synacktiv!)
  - - Unexpected response for DS query below delegation poing
  - - Zone events not rescheduled upon server reload (Thanks to Mark Warren)
  - - Missing trailing dot in the keymgr DS owner output
  - - Malformed output from kjournalprint
  - - Redundant SO_REUSEPORT activation on the TCP socket
- 2.6.0 (vs v3.6.0): added 1, removed 1
  - + More DNSSEC-related semantic checks
  - - More DNSSSEC-related semantic checks
- 2.6.5 (vs v3.6.0): added 1, removed 1
  - + Kdig uses '@server' as a hostname for TLS authentication if '+tls-ca' is set
  - - Kdig uses '@server' as a hostname for TLS authenticaion if '+tls-ca' is set
- 2.6.6 (vs v3.6.0): added 1, removed 1
  - + Reduced memory consumption of disabled statistics metrics
  - - Reduced memory consuption of disabled statistics metrics
- 2.6.8 (vs v3.6.0): added 1, removed 1
  - + Creeping memory consumption upon server reload #584
  - - Creeping memory consuption upon server reload #584
- 2.9.4 (vs v3.6.0): added 2, removed 2
  - + NSEC(3) chain not fixed if affected by zone update
  - + Zone check logs error instead of warning after a first error occurred
  - - NSEC(3) chain not fixed if affected by zone udpate
  - - Zone check logs error instead of warning after a first error occured
- 3.0.0 (vs v3.6.0): added 3, removed 3
  - + Kdig prints detailed algorithm identifier for PRIVATEDNS and PRIVATEOID in multiline mode #334
  - + Responding FORMERR to queries with more OPT or TSIG records
  - + Module onlinesign responds NXDOMAIN instead of NOERROR (NODATA) if DNSSEC not requested
  - - Kdig prints detailed algorithm idendifier for PRIVATEDNS and PRIVATEOID in multiline mode #334
  - - Responding FORMERR to queries with more OPT records
  - - Module onlinesign responds NXDOMAIN insted of NOERROR (NODATA) if DNSSEC not requested
- 3.1.0 (vs v3.6.0): added 1, removed 1
  - + libzscanner: omitted TTL value is correctly set to the last explicitly stated value (RFC 1035)
  - - libzsanner: omitted TTL value is correctly set to the last explicitly stated value (RFC 1035)
- 3.1.4 (vs v3.6.0): added 1, removed 1
  - + mod-dnstap: added 'responses-with-queries' configuration option (Thanks to Robert Edmonds) #764
  - - mod-dnstap: added 'responses-with-queries' configuration option (Thanks to Robert Edmonds)
- 3.2.7 (vs v3.6.0): added 1, removed 1
  - + packaging: RHEL9 requires libxdp like fedora since RHEL 9.2 #844
  - - packaging: RHEL9 requires libxdp like fedora since RHEL 9.1 #844
- 3.3.5 (vs v3.6.0): added 1, removed 0
  - + libzscanner: incorrect alpn processing #923
- 3.3.10 (vs v3.6.0): added 3, removed 3
  - + knotd: generated catalog member metadata is stored when the zone is loaded
  - + knotd: more active ZSKs cause cumulative ZSK rollovers
  - + knotd: zone purge clears active generated catalog member metadata
  - - knotd: generated catalog memeber metadata is stored when the zone is loaded
  - - knotd: more active ZSKs causes cumulative ZSK rollovers
  - - knotd: zone purge clears active generated catalog memeber metadata
- 3.4.3 (vs v3.6.0): added 2, removed 2
  - + knotd: more active ZSKs cause cumulative ZSK rollovers
  - + knotd: zone purge clears active generated catalog member metadata
  - - knotd: more active ZSKs causes cumulative ZSK rollovers
  - - knotd: zone purge clears active generated catalog memeber metadata

## Release list

| version | tag | date | stable | own entries | DNSSEC-ish rows |
|---|---|---|---|---|---|
| 0.1 | v0.1 | 2011-02-02 | yes | 0 | 0 |
| 0.2 | v0.2 | 2011-04-12 | yes | 0 | 0 |
| 0.3 | v0.3 | 2011-09-02 | yes | 0 | 0 |
| 0.8 | v0.8 | 2011-11-03 | yes | 16 | 2 |
| 0.8.1 | v0.8.1 | 2011-12-01 | yes | 2 | 0 |
| 0.9 | v0.9 | 2012-01-13 | yes | 7 | 0 |
| 0.9.1 | v0.9.1 | 2012-01-20 | yes | 6 | 0 |
| 1.0-rc1 | v1.0-rc1 | 2012-02-14 | no | 15 | 2 |
| 1.0.0 | v1.0.0 | 2012-02-29 | yes | 6 | 0 |
| 1.0.1 | v1.0.1 | 2012-03-09 | yes | 8 | 1 |
| 1.0.2 | v1.0.2 | 2012-04-13 | yes | 8 | 0 |
| 1.0.3 | v1.0.3 | 2012-04-17 | yes | 4 | 0 |
| 1.0.4 | v1.0.4 | 2012-05-16 | yes | 11 | 1 |
| 1.0.5 | v1.0.5 | 2012-05-17 | yes | 1 | 0 |
| 1.0.6 | v1.0.6 | 2012-06-13 | yes | 3 | 1 |
| 1.1.0-rc1 | v1.1.0-rc1 | 2012-08-17 | no | 25 | 4 |
| 1.1.0-rc2 | v1.1.0-rc2 | 2012-08-23 | no | 4 | 1 |
| 1.1.0 | v1.1.0 | 2012-08-31 | yes | 2 | 0 |
| 1.1.1-rc1 | v1.1.1-rc1 | 2012-10-23 | no | 8 | 1 |
| 1.1.1 | v1.1.1 | 2012-10-30 | yes | 1 | 0 |
| 1.1.2-rc1 | v1.1.2-rc1 | 2012-11-14 | no | 2 | 0 |
| 1.1.2 | v1.1.2 | 2012-11-21 | yes | 2 | 0 |
| 1.1.3-rc1 | v1.1.3-rc1 | 2012-12-06 | no | 4 | 2 |
| 1.1.3 | v1.1.3 | 2012-12-19 | yes | 2 | 0 |
| 1.2-rc1 | v1.2-rc1 | 2013-01-07 | no | 4 | 0 |
| 1.2.0-rc1 | v1.2.0-rc1 | 2013-01-07 | no | 0 | 0 |
| 1.2-rc2 | v1.2-rc2 | 2013-02-15 | no | 4 | 0 |
| 1.2.0-rc2 | v1.2.0-rc2 | 2013-02-15 | no | 0 | 0 |
| 1.2.0-rc3 | v1.2.0-rc3 | 2013-03-01 | no | 3 | 1 |
| 1.2.0-rc4 | v1.2.0-rc4 | 2013-03-22 | no | 6 | 0 |
| 1.2.0 | v1.2.0 | 2013-04-02 | yes | 1 | 0 |
| 1.3.0-rc1 | v1.3.0-rc1 | 2013-06-04 | no | 13 | 1 |
| 1.3.0-rc2 | v1.3.0-rc2 | 2013-06-14 | no | 4 | 0 |
| 1.3.0-rc3 | v1.3.0-rc3 | 2013-06-28 | no | 8 | 1 |
| 1.3.0-rc4 | v1.3.0-rc4 | 2013-07-15 | no | 7 | 1 |
| 1.3.0-rc5 | v1.3.0-rc5 | 2013-07-29 | no | 6 | 0 |
| 1.3.0 | v1.3.0 | 2013-08-05 | yes | 6 | 1 |
| 1.3.1 | v1.3.1 | 2013-08-27 | yes | 5 | 0 |
| 1.3.2 | v1.3.2 | 2013-09-30 | yes | 4 | 0 |
| 1.3.3 | v1.3.3 | 2013-10-28 | yes | 6 | 0 |
| 1.3.4 | v1.3.4 | 2013-12-12 | yes | 3 | 0 |
| 1.4.0-beta | v1.4.0-beta | 2013-10-28 | no | 2 | 1 |
| 1.4.0-rc1 | v1.4.0-rc1 | 2013-11-20 | no | 8 | 4 |
| 1.4.0-rc2 | v1.4.0-rc2 | 2013-12-13 | no | 11 | 4 |
| 1.4.0 | v1.4.0 | 2013-12-31 | yes | 7 | 1 |
| 1.4.1 | v1.4.1 | 2014-01-13 | yes | 4 | 0 |
| 1.4.2 | v1.4.2 | 2014-01-27 | yes | 6 | 2 |
| 1.4.3 | v1.4.3 | 2014-02-12 | yes | 5 | 1 |
| 1.4.4 | v1.4.4 | 2014-03-27 | yes | 10 | 1 |
| 1.4.5 | v1.4.5 | 2014-04-14 | yes | 1 | 0 |
| 1.4.6 | v1.4.6 | 2014-05-22 | yes | 2 | 1 |
| 1.4.7 | v1.4.7 | 2014-06-17 | yes | 5 | 1 |
| 1.5.0-alpha | v1.5.0-alpha | 2014-04-01 | no | 0 | 0 |
| 1.5.0-rc1 | v1.5.0-rc1 | 2014-06-03 | no | 12 | 0 |
| 1.5.0-rc2 | v1.5.0-rc2 | 2014-06-18 | no | 7 | 0 |
| 1.5.0 | v1.5.0 | 2014-07-08 | yes | 15 | 1 |
| 1.5.1 | v1.5.1 | 2014-08-19 | yes | 9 | 2 |
| 1.5.2 | v1.5.2 | 2014-09-08 | yes | 3 | 0 |
| 1.5.3 | v1.5.3 | 2014-09-15 | yes | 5 | 1 |
| 1.6.0-rc1 | v1.6.0-rc1 | 2014-10-13 | no | 4 | 1 |
| 1.6.0-rc2 | v1.6.0-rc2 | 2014-10-17 | no | 3 | 0 |
| 1.6.0 | v1.6.0 | 2014-10-23 | yes | 2 | 0 |
| 1.6.1 | v1.6.1 | 2014-12-12 | yes | 4 | 1 |
| 1.6.2 | v1.6.2 | 2015-02-19 | yes | 4 | 0 |
| 1.6.3 | v1.6.3 | 2015-04-08 | yes | 8 | 2 |
| 1.6.3-rosedb | v1.6.3-rosedb | 2015-04-10 | no | 0 | 0 |
| 1.6.4 | v1.6.4 | 2015-06-16 | yes | 11 | 0 |
| 1.6.4-rosedb | v1.6.4-rosedb | 2015-06-16 | no | 0 | 0 |
| 1.6.5 | v1.6.5 | 2015-09-01 | yes | 11 | 1 |
| 1.6.5-rosedb | v1.6.5-rosedb | 2015-09-01 | no | 0 | 0 |
| 1.6.6 | v1.6.6 | 2015-11-24 | yes | 3 | 0 |
| 1.6.7 | v1.6.7 | 2016-02-08 | yes | 4 | 0 |
| 1.6.8 | v1.6.8 | 2016-08-09 | yes | 1 | 1 |
| 1.99.0 | v1.99.0 | 2014-12-31 | no | 1 | 0 |
| 1.99.1 | v1.99.1 | 2015-02-11 | no | 1 | 0 |
| 2.0.0-beta | v2.0.0-beta | 2015-04-23 | no | 3 | 0 |
| 2.0.0-rc1 | v2.0.0-rc1 | 2015-06-15 | no | 16 | 0 |
| 2.0.0 | v2.0.0 | 2015-06-26 | yes | 19 | 2 |
| 2.0.1 | v2.0.1 | 2015-09-02 | yes | 27 | 6 |
| 2.0.2 | v2.0.2 | 2015-11-24 | yes | 1 | 0 |
| 2.1.0-rc1 | v2.1.0-rc1 | 2015-12-20 | no | 16 | 0 |
| 2.1.0 | v2.1.0 | 2016-01-14 | yes | 18 | 5 |
| 2.1.1-test | v2.1.1-test | 2016-02-04 | no | 3 | 1 |
| 2.1.1 | v2.1.1 | 2016-02-10 | yes | 7 | 2 |
| 2.2.0 | v2.2.0 | 2016-04-26 | yes | 20 | 5 |
| 2.2.1 | v2.2.1 | 2016-05-24 | yes | 14 | 1 |
| 2.3.0 | v2.3.0 | 2016-08-09 | yes | 13 | 7 |
| 2.3.1 | v2.3.1 | 2016-10-10 | yes | 12 | 0 |
| 2.3.2 | v2.3.2 | 2016-11-04 | yes | 13 | 0 |
| 2.3.3 | v2.3.3 | 2016-12-08 | yes | 7 | 2 |
| 2.4.0 | v2.4.0 | 2017-01-18 | yes | 22 | 4 |
| 2.4.1 | v2.4.1 | 2017-02-10 | yes | 14 | 0 |
| 2.4.2 | v2.4.2 | 2017-03-23 | yes | 9 | 0 |
| 2.4.3 | v2.4.3 | 2017-04-10 | yes | 8 | 2 |
| 2.4.4 | v2.4.4 | 2017-06-05 | yes | 6 | 0 |
| 2.4.5 | v2.4.5 | 2017-06-23 | yes | 2 | 0 |
| 2.5.0 | v2.5.0 | 2017-06-05 | yes | 12 | 4 |
| 2.5.1 | v2.5.1 | 2017-06-07 | yes | 5 | 3 |
| 2.5.2 | v2.5.2 | 2017-06-23 | yes | 16 | 6 |
| 2.5.3 | v2.5.3 | 2017-07-14 | yes | 9 | 7 |
| 2.5.4 | v2.5.4 | 2017-08-30 | yes | 12 | 5 |
| 2.5.5 | v2.5.5 | 2017-09-29 | yes | 8 | 3 |
| 2.5.6 | v2.5.6 | 2017-11-02 | yes | 5 | 2 |
| 2.5.7 | v2.5.7 | 2018-01-01 | yes | 11 | 5 |
| 2.6.0 | v2.6.0 | 2017-09-29 | yes | 18 | 9 |
| 2.6.1 | v2.6.1 | 2017-11-02 | yes | 14 | 6 |
| 2.6.2 | v2.6.2 | 2017-11-23 | yes | 6 | 3 |
| 2.6.3 | v2.6.3 | 2017-11-24 | yes | 1 | 1 |
| 2.6.4 | v2.6.4 | 2018-01-01 | yes | 9 | 5 |
| 2.6.5 | v2.6.5 | 2018-02-12 | yes | 12 | 0 |
| 2.6.6 | v2.6.6 | 2018-04-11 | yes | 13 | 2 |
| 2.6.7 | v2.6.7 | 2018-05-17 | yes | 7 | 0 |
| 2.6.8 | v2.6.8 | 2018-07-10 | yes | 9 | 4 |
| 2.6.9 | v2.6.9 | 2018-08-14 | yes | 5 | 2 |
| 2.7.0 | v2.7.0 | 2018-08-03 | yes | 32 | 9 |
| 2.7.1 | v2.7.1 | 2018-08-14 | yes | 6 | 2 |
| 2.7.2 | v2.7.2 | 2018-08-29 | yes | 8 | 2 |
| 2.7.3 | v2.7.3 | 2018-10-11 | yes | 12 | 4 |
| 2.7.4 | v2.7.4 | 2018-11-13 | yes | 13 | 7 |
| 2.7.5 | v2.7.5 | 2019-01-07 | yes | 17 | 8 |
| 2.7.6 | v2.7.6 | 2019-01-23 | yes | 9 | 0 |
| 2.7.7 | v2.7.7 | 2019-04-15 | yes | 11 | 5 |
| 2.7.8 | v2.7.8 | 2019-07-16 | yes | 6 | 0 |
| 2.8.0 | v2.8.0 | 2019-03-05 | yes | 22 | 10 |
| 2.8.1 | v2.8.1 | 2019-04-09 | yes | 14 | 6 |
| 2.8.2 | v2.8.2 | 2019-06-05 | yes | 15 | 3 |
| 2.8.3 | v2.8.3 | 2019-07-16 | yes | 14 | 4 |
| 2.8.4 | v2.8.4 | 2019-09-24 | yes | 12 | 2 |
| 2.8.5 | v2.8.5 | 2020-01-01 | yes | 9 | 3 |
| 2.9.dev | v2.9.dev | 2019-03-05 | no | 0 | 0 |
| 2.9.0 | v2.9.0 | 2019-10-10 | yes | 45 | 10 |
| 2.9.1 | v2.9.1 | 2019-11-11 | yes | 14 | 2 |
| 2.9.2 | v2.9.2 | 2019-12-12 | yes | 10 | 5 |
| 2.9.3 | v2.9.3 | 2020-03-03 | yes | 17 | 4 |
| 2.9.4 | v2.9.4 | 2020-05-05 | yes | 20 | 9 |
| 2.9.5 | v2.9.5 | 2020-05-25 | yes | 4 | 2 |
| 2.9.6 | v2.9.6 | 2020-08-31 | yes | 11 | 4 |
| 2.9.7 | v2.9.7 | 2020-10-09 | yes | 5 | 2 |
| 2.9.8 | v2.9.8 | 2020-12-15 | yes | 8 | 4 |
| 2.9.9 | v2.9.9 | 2021-04-01 | yes | 6 | 3 |
| 3.0.dev | v3.0.dev | 2019-10-10 | no | 0 | 0 |
| 3.0.0 | v3.0.0 | 2020-09-09 | yes | 23 | 8 |
| 3.0.1 | v3.0.1 | 2020-10-10 | yes | 18 | 9 |
| 3.0.2 | v3.0.2 | 2020-11-11 | yes | 22 | 7 |
| 3.0.3 | v3.0.3 | 2020-12-15 | yes | 14 | 2 |
| 3.0.4 | v3.0.4 | 2021-01-20 | yes | 10 | 1 |
| 3.0.5 | v3.0.5 | 2021-03-25 | yes | 15 | 3 |
| 3.0.6 | v3.0.6 | 2021-05-12 | yes | 18 | 6 |
| 3.0.7 | v3.0.7 | 2021-06-16 | yes | 16 | 6 |
| 3.0.8 | v3.0.8 | 2021-07-16 | yes | 7 | 6 |
| 3.0.9 | v3.0.9 | 2021-09-09 | yes | 7 | 3 |
| 3.0.10 | v3.0.10 | 2021-11-04 | yes | 9 | 2 |
| 3.0.11 | v3.0.11 | 2022-04-28 | yes | 10 | 3 |
| 3.1.dev | v3.1.dev | 2020-09-09 | no | 0 | 0 |
| 3.1.0 | v3.1.0 | 2021-08-01 | yes | 51 | 8 |
| 3.1.1 | v3.1.1 | 2021-08-10 | yes | 11 | 3 |
| 3.1.2 | v3.1.2 | 2021-09-08 | yes | 21 | 9 |
| 3.1.3 | v3.1.3 | 2021-10-18 | yes | 12 | 2 |
| 3.1.4 | v3.1.4 | 2021-11-04 | yes | 12 | 4 |
| 3.1.5 | v3.1.5 | 2021-12-20 | yes | 23 | 4 |
| 3.1.6 | v3.1.6 | 2022-02-08 | yes | 17 | 5 |
| 3.1.7 | v3.1.7 | 2022-03-30 | yes | 14 | 2 |
| 3.1.8 | v3.1.8 | 2022-04-28 | yes | 10 | 0 |
| 3.1.9 | v3.1.9 | 2022-08-10 | yes | 19 | 5 |
| 3.2.dev | v3.2.dev | 2021-08-01 | no | 0 | 0 |
| 3.2.0 | v3.2.0 | 2022-08-22 | yes | 69 | 24 |
| 3.2.1 | v3.2.1 | 2022-09-08 | yes | 11 | 1 |
| 3.2.2 | v3.2.2 | 2022-11-01 | yes | 13 | 1 |
| 3.2.3 | v3.2.3 | 2022-11-20 | yes | 8 | 1 |
| 3.2.4 | v3.2.4 | 2022-12-12 | yes | 11 | 2 |
| 3.2.5 | v3.2.5 | 2023-02-01 | yes | 15 | 1 |
| 3.2.6 | v3.2.6 | 2023-04-04 | yes | 15 | 0 |
| 3.2.7 | v3.2.7 | 2023-06-06 | yes | 18 | 0 |
| 3.2.8 | v3.2.8 | 2023-06-26 | yes | 7 | 0 |
| 3.2.9 | v3.2.9 | 2023-07-27 | yes | 8 | 3 |
| 3.2.10 | v3.2.10 | 2023-09-11 | yes | 10 | 0 |
| 3.2.11 | v3.2.11 | 2023-10-30 | yes | 8 | 4 |
| 3.2.12 | v3.2.12 | 2023-12-19 | yes | 10 | 2 |
| 3.2.13 | v3.2.13 | 2024-06-25 | yes | 9 | 1 |
| 3.3.dev | v3.3.dev | 2022-08-22 | no | 0 | 0 |
| 3.3.0 | v3.3.0 | 2023-08-28 | yes | 46 | 4 |
| 3.3.1 | v3.3.1 | 2023-09-11 | yes | 8 | 1 |
| 3.3.2 | v3.3.2 | 2023-10-20 | yes | 22 | 7 |
| 3.3.3 | v3.3.3 | 2023-12-13 | yes | 23 | 4 |
| 3.3.4 | v3.3.4 | 2024-01-24 | yes | 21 | 4 |
| 3.3.5 | v3.3.5 | 2024-03-06 | yes | 10 | 5 |
| 3.3.6 | v3.3.6 | 2024-06-12 | yes | 23 | 3 |
| 3.3.7 | v3.3.7 | 2024-06-25 | yes | 5 | 0 |
| 3.3.8 | v3.3.8 | 2024-07-22 | yes | 8 | 3 |
| 3.3.9 | v3.3.9 | 2024-08-26 | yes | 9 | 1 |
| 3.3.10 | v3.3.10 | 2024-12-12 | yes | 12 | 1 |
| 3.4.dev | v3.4.dev | 2023-08-26 | no | 0 | 0 |
| 3.4.0 | v3.4.0 | 2024-09-02 | yes | 51 | 10 |
| 3.4.1 | v3.4.1 | 2024-10-14 | yes | 25 | 3 |
| 3.4.2 | v3.4.2 | 2024-10-31 | yes | 10 | 2 |
| 3.4.3 | v3.4.3 | 2024-12-06 | yes | 16 | 5 |
| 3.4.4 | v3.4.4 | 2025-01-22 | yes | 18 | 2 |
| 3.4.5 | v3.4.5 | 2025-03-18 | yes | 11 | 2 |
| 3.4.6 | v3.4.6 | 2025-04-10 | yes | 16 | 5 |
| 3.4.7 | v3.4.7 | 2025-06-04 | yes | 30 | 4 |
| 3.4.8 | v3.4.8 | 2025-07-29 | yes | 14 | 3 |
| 3.4.9 | v3.4.9 | 2025-11-28 | yes | 8 | 2 |
| 3.4.10 | v3.4.10 | 2026-04-02 | yes | 14 | 3 |
| 3.4.11 | v3.4.11 | 2026-08-18 | yes | 24 | 6 |
| 3.5.dev | v3.5.dev | 2024-09-02 | no | 0 | 0 |
| 3.5.0 | v3.5.0 | 2025-09-18 | yes | 37 | 5 |
| 3.5.1 | v3.5.1 | 2025-10-16 | yes | 18 | 3 |
| 3.5.2 | v3.5.2 | 2025-11-28 | yes | 25 | 4 |
| 3.5.3 | v3.5.3 | 2026-01-16 | yes | 28 | 8 |
| 3.5.4 | v3.5.4 | 2026-04-02 | yes | 29 | 2 |
| 3.5.5 | v3.5.5 | 2026-06-12 | yes | 30 | 6 |
| 3.5.6 | v3.5.6 | 2026-07-20 | yes | 18 | 1 |
| 3.5.7 | v3.5.7 | 2026-08-18 | yes | 24 | 6 |
| 3.5.8 | v3.5.8 | 2026-09-04 | yes | 6 | 1 |
| 3.6.0 | v3.6.0 | 2026-09-08 | yes | 40 | 13 |
| 3.7.dev | v3.7.dev | 2026-09-08 | no | 0 | 0 |

## Verification

Phase 3 adversarial check: **PASS WITH CORRECTIONS** (397 checks, 9 failed, 7 corrections applied 2026-09-29). Report: `docs/handoff/verify/knot.md`.

## Gaps

- The tag "embedded_lmdb" (2020-05-11) is not a release and is excluded. v1.2-rc1/v1.2-rc2 are duplicate names for v1.2.0-rc1/rc2 (same commits) and carry no entries.
- NEWS section "2.3.4 (2017-11-20)" has no tag in the clone; its six entries (incl. the only NEWS line naming CVE-2017-11104) are attributed to v2.5.7, the first tag whose NEWS carries the section, and flagged news_section_untagged.
- The 2.1.0 default-algorithm switch to ECDSAP256SHA256 and the 2.2.0 RSA key-size default (2048 for ZSK) are not in NEWS; they are recorded in default_changes from the commits and doc/configuration.rst diffs only.
- DSA removal (2.6.0, da9e7ceb8) and the RSA minimum key size 1024 (2.7.0, d0f52e7c4) are not in NEWS; recorded in default_changes / algorithm_support from the commits.
- doc/reference.rst documented nsec3-iterations "Default: 5" from 2.3.0 to 3.0.5 while the schema default was 10 (scheme.c@v2.3.0:166); the doc was corrected to 10 in 3.0.6 (9a2a2ecf9). The documented-defaults diff therefore shows 5 -> 10 at 3.0.6, which is a documentation fix, not a behaviour change.
- CVE-2014-0486: no NEWS line names the CVE and NVD published it 3.5 years after the fix; the fixing commits are attributed approximately to the rrset-from-wire hardening merged before v1.5.2 (fac2b82e8).
- CVE-2026-39155: the CVE id is absent from NEWS; both fix commits are identified from the NVD description and the NEWS 3.4.10/3.5.4 line "mod-onlinesign: incorrect next NSEC owner name leading to a DoS".
- Nine Knot Resolver CVEs in by_product.knot are keyword-search artefacts ("Knot DNS" matches "Knot Resolver"); marked not applicable after checking that none appears in Knot DNS NEWS or git log.
- Security fixes without a CVE id: 3.4.11/3.5.7 "server crash on zone with NSEC3PARAM but without NSEC3 records", 3.5.8 "unauthenticated TSIG chosen-prefix signing", 3.5.8 XDP crash; listed as entry rows only.
- 0.8 "DNSSEC"/"NSEC3" support rows: the first public release already served signed zones; commits are the earliest RRSIG/NSEC3 commits in the clone (2010-11/12), attribution approximate.
- Pre-release tags (rc/beta/alpha/test/dev/rosedb/1.99.x) have stable=false. Knot NEWS has separate sections per rc tag, so entries that appear only in an rc section stay on the rc tag (with stable_release set); entries repeated verbatim in the final release are attributed to the final release.
- Parallel maintenance lines (1.6.x alongside 2.0-2.3; 2.x/3.x minors in pairs, e.g. 3.4.x alongside 3.5.x) mean a fix lands as two different commits; each row cites the commit contained in its own tag. Where the same NEWS line appears on both lines both rows are kept.
- Post-hoc NEWS edits are checked for versions >= 2.0.0 only (1.x sections were reformatted when RELNOTES content was merged into NEWS); see news_edits.
- Non-DNSSEC default changes seen in NEWS are entry rows only (2.4.3 utilities TSIG default HMAC-SHA256; 3.4.6 key.algorithm default hmac-sha256).
