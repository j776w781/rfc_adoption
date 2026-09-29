# Knot Resolver (kresd) DNSSEC timeline

Generated 2026-09-28 from `out/software_repos/kresd.git` (bare clone), `data/software/cve_inventory.json` and `out/analysis/cve_crossref.json`. Machine-readable twin: `data/software/timelines/kresd.json`.

**Releases:** 98 tags (89 stable, 9 pre-release/early-access), 2015-10-08 .. 2026-08-05. Changelog: `ChangeLog` (v1.0.0-beta1..v1.1.0), `NEWS` (v1.1.1..v6.4.2, 1.3.0-rc1). Release date = commit date of `<tag>^{commit}`.

5.7.x (2023-08 .. 2026-08) and 6.0.x+ (2023-05 ..) are parallel lines. v5.7.1 is an ancestor of v6.0.6 (KeyTrap/NSEC3 commits shared); v5.7.4+ are not ancestors of any 6.x tag, so 6.x entries after 6.0.6 carry their own commits. 6.x NEWS files also embed the 5.x sections; entries are attributed by section header, not by file.

## How to verify a row

```
C=out/software_repos/kresd.git
git -C $C log -1 --format=%cI <tag>^{commit}          # release date
git -C $C show <tag>:NEWS | grep -n -F "<changelog line>"  # entry present at the tag
git -C $C tag --contains <commit> | grep -x <tag>     # commit is in the release
git -C $C show <commit> --stat                        # what it changed
```

## Support added / defaults changed / limits changed

| version | date | kind | default change | mechanism | changelog line | commit(s) | in tag |
|---|---|---|---|---|---|---|---|
| 1.2.5 | 2017-04-05 | support-added | no | validation | - dnssec/nsec: missed wildcard no-data answers validation has been | da69221c61 | yes |
| 1.2.5 | 2017-04-05 | support-added | no | trust-anchor-5011 | - trust anchors: support non-root TAs, one domain per file | 26d3c47eaf | yes |
| 1.3.0 | 2017-06-13 | support-added | yes | validation | - major feature: support for forwarding with validation (#112). | 651c5aadeb, 8ae906e08b | yes |
| 1.3.2 | 2017-07-28 | support-added | no | dnskey | - dnssec: handle unknown DNSKEY/DS algorithms (#210) | cd8cd0a4ba | yes |
| 1.5.0 | 2017-11-02 | default-changed | yes | trust-anchor-5011 | - new module ta_signal_query supporting Signaling Trust Anchor Knowledge | ac23d8d0f1, 35a8a64cd5 | yes |
| 1.5.1 | 2017-12-12 | default-changed | yes | other | - add priming module to implement RFC 8109, enabled by default (#220) | 52c39a01aa, 9e90f9fb20 | yes |
| 1.99.1-alpha | 2017-10-26 | support-added | no | other | - negative answers from validated NSEC (NXDOMAIN, NODATA) | 0c3f6a269e | yes |
| 2.0.0 | 2018-01-31 | default-changed | yes | other | - policy module is now loaded by default to enforce RFC 6761; | 85ef152406 | yes |
| 2.0.0 | 2018-01-31 | support-added | yes | other | - aggressive caching of validated records (RFC 8198) for NSEC zones; | 997242e079, 762ab96653 | yes |
| 2.0.0 | 2018-01-31 | support-added | no | trust-anchor-5011 | - trust anchors: you may specify a read-only file via -K or --keyfile-ro | 6c2db2b56b | yes |
| 2.0.0 | 2018-01-31 | support-added | no | trust-anchor-5011 | - trust anchors: at build-time you may set KEYFILE_DEFAULT (read-only) | 6c2db2b56b | yes |
| 2.0.0 | 2018-01-31 | support-added | yes | trust-anchor-5011 | - ta_sentinel module implements draft ietf-dnsop-kskroll-sentinel-00, | 777a680a9c | yes |
| 2.4.0 | 2018-07-03 | support-added | yes | nsec3 | - aggressive caching for NSEC3 zones (!600) | e2d5bd39ad, 17dae8a15f | yes |
| 2.4.0 | 2018-07-03 | support-added | no | validation | - module bogus_log to log DNSSEC bogus queries without verbose logging (!613) | d7a905d771 | yes |
| 4.0.0 | 2019-04-18 | default-changed | yes | validation | - DNSSEC is enabled by default | 8abc490f6f, 4b3ac5d78f, 92fced622c | yes |
| 4.0.0 | 2019-04-18 | default-changed | yes | validation | - always send DO+CD flags upstream, even in insecure zones (#153) | bfc8511bda | yes |
| 4.1.0 | 2019-07-10 | default-changed | yes | other | - aggressive caching is disabled on minimal NSEC* ranges (!826) | f1be61dd21 | yes |
| 5.3.1 | 2021-03-31 | limit-changed | yes | nsec3-iterations | - validator: downgrade NSEC3 records with too many iterations (>150; !1160) | 7107faebc7, 5922eecd46, 21e50fca15 | yes |
| 5.5.0 | 2022-03-15 | default-changed | yes | ds-digest | - validator: conditionally ignore SHA1 DS, as SHOULD by RFC4509 (!1251) | d4e95821ae | yes |
| 5.6.0 | 2023-01-26 | default-changed | yes | other | - policy.STUB: avoid applying aggressive DNSSEC denial proofs (!1364) | 24e912e0b0 | yes |
| 5.6.0 | 2023-01-26 | default-changed | yes | validation | - policy.STUB: avoid copying +dnssec flag from client to upstream (!1364) | fab10d1ea0 | yes |
| 5.7.1 | 2024-02-13 | cve-fix | yes | nsec3-iterations | - CVE-2023-50868: NSEC3 closest encloser proof can exhaust CPU | e966b7fdb1, eccb8e278c, b5051ac26f, 24699e9f20, a05cf1d379 | yes |
| 5.7.1 | 2024-02-13 | cve-fix | yes | validation | - CVE-2023-50387 "KeyTrap": DNSSEC verification complexity | cc5051b444, feb65eb97b | yes |
| 5.7.4 | 2024-07-23 | default-changed | yes | trust-anchor-5011 | - add the fresh DNSSEC root key "KSK-2024" already, Key ID 38696 (!1556) | 62b3b1e931 | yes |
| 6.0.6 | 2024-02-13 | cve-fix | yes | nsec3-iterations | - CVE-2023-50868: NSEC3 closest encloser proof can exhaust CPU | e966b7fdb1, eccb8e278c, b5051ac26f, 24699e9f20, a05cf1d379 | yes |
| 6.0.6 | 2024-02-13 | cve-fix | yes | validation | - CVE-2023-50387 "KeyTrap": DNSSEC verification complexity | cc5051b444, feb65eb97b | yes |
| 6.0.8 | 2024-07-23 | default-changed | yes | trust-anchor-5011 | - add the fresh DNSSEC root key "KSK-2024" already, Key ID 38696 (!1556) | 62b3b1e931 | yes |

## Default changes (before / after)

| version | date | change | before | after | on upgrade | opt-in | commits | attribution |
|---|---|---|---|---|---|---|---|---|
| 1.3.0 | 2017-06-13 | policy.FORWARD validates (forwarding with validation) | policy.FORWARD forwarded without DNSSEC validation (NEWS 1.2.0: "policy.FORWARD() doesn't do DNSSEC validation yet") | policy.FORWARD validates answers; the old non-validating mode is policy.STUB | yes | no | 651c5aadeb, 8ae906e08b | exact |
| 1.5.0 | 2017-11-02 | ta_signal_query module enabled by default | no RFC 8145 key-tag signalling | module ta_signal_query loaded by default; resolver sends _ta-<keytag> queries | yes | no | ac23d8d0f1, 35a8a64cd5 | exact |
| 2.0.0 | 2018-01-31 | aggressive use of DNSSEC-validated cache (RFC 8198) for NSEC | negative answers always sent upstream | NXDOMAIN/NODATA synthesised from cached validated NSEC; no configuration knob | yes | no | 997242e079, 762ab96653 | exact |
| 2.0.0 | 2018-01-31 | ta_sentinel module enabled by default | no KSK-rollover sentinel | ta_sentinel (draft-ietf-dnsop-kskroll-sentinel-00, later RFC 8509) enabled by default | yes | no | 777a680a9c | exact |
| 2.0.0 | 2018-01-31 | managed trust-anchor file must be writeable; read-only -K and build-time KEYFILE_DEFAULT added | -k <file>: TA file; no read-only mode; no build-time default file | -k requires a writeable directory (RFC 5011 managed); -K/--keyfile-ro for unmanaged; KEYFILE_DEFAULT build option (empty by default, config.mk) | yes | no | 6c2db2b56b | exact |
| 2.4.0 | 2018-07-03 | aggressive caching for NSEC3 zones | RFC 8198 synthesis only from NSEC | RFC 8198 synthesis also from NSEC3 (non-opt-out); on by default | yes | no | e2d5bd39ad, 17dae8a15f | exact |
| 4.0.0 | 2019-04-18 | DNSSEC validation enabled by default | KEYFILE_DEFAULT empty by default (v3.2.1 config.mk:26 "KEYFILE_DEFAULT ?="); validation only if built with a keyfile or started with -k/-K | meson option keyfile_default=root.keys (v4.0.0 meson_options.txt), always loaded by trust_anchors.lua; -k/-K removed; disable with trust_anchors.remove(".") | yes | no | 8abc490f6f, 4b3ac5d78f, 92fced622c, 1405517deb | exact |
| 4.0.0 | 2019-04-18 | DO (and CD) bit always sent upstream | DO bit sent only when the zone was known secure | DO+CD sent on every upstream query, iterating or forwarding, even in insecure zones | yes | no | bfc8511bda | exact |
| 4.1.0 | 2019-07-10 | no aggressive caching on minimal NSEC/NSEC3 ranges | RFC 8198 synthesis from any validated NSEC/NSEC3 | ranges covering only the owner name (black lies) are not used for synthesis | yes | no | f1be61dd21 | exact |
| 5.3.1 | 2021-03-31 | NSEC3 iteration cap: zones above 150 iterations treated as insecure | no cap; any iteration count validated | KR_NSEC3_MAX_ITERATIONS 150 (lib/dnssec/nsec3.h@v5.3.1:19); NSEC3 above the cap not cached, zone downgraded to insecure | yes | no | 7107faebc7, 5922eecd46, 21e50fca15 | exact |
| 5.5.0 | 2022-03-15 | SHA-1 DS digests ignored when a stronger digest is present | every DS digest in the set tried | SHA-1 DS skipped if the DS RRset also has a supported non-SHA-1 digest (lib/dnssec/signature.c) | yes | no | d4e95821ae | exact |
| 5.6.0 | 2023-01-26 | policy.STUB: no aggressive denial proofs, no +dnssec copied upstream | STUB answers could be synthesised from cached NSEC/NSEC3 and forwarded the client DO flag | STUB skips RFC 8198 synthesis and does not copy +dnssec from client | yes | no | 24e912e0b0, fab10d1ea0 | exact |
| 5.7.1 | 2024-02-13 | NSEC3 limits tightened (CVE-2023-50868): iterations 150 -> 50, salt priced in, >8 NSEC3 RRs refused | KR_NSEC3_MAX_ITERATIONS 150; no salt-length limit; unlimited NSEC3 RRs per answer | kr_nsec3_limited() MAX_ITERATIONS 50 vs kr_nsec3_price (macro removed at v5.7.1) with kr_nsec3_price(iterations, salt_len) (lib/dnssec/nsec3.h@v5.7.1); answers with >8 NSEC3 in AUTHORITY are bogus; SHA-1 work in cache/proofs bounded | yes | no | e966b7fdb1, eccb8e278c, b5051ac26f, 24699e9f20, a05cf1d379 | exact |
| 5.7.1 | 2024-02-13 | per-request crypto-validation budget (CVE-2023-50387 KeyTrap) | unbounded signature/key checks per answer | vld_limit_crypto_remains budget per request; exceeding it fails validation (E2BIG) without retry | yes | no | cc5051b444, feb65eb97b | exact |
| 5.7.4 | 2024-07-23 | built-in root trust anchors gain KSK-2024 (key id 38696) | etc/root.keys: KSK-2017 (20326) only | etc/root.keys: KSK-2017 + KSK-2024 (38696) | no | no | 62b3b1e931 | exact |
| 6.0.6 | 2024-02-13 | NSEC3 limits tightened (CVE-2023-50868): iterations 150 -> 50, salt priced in, >8 NSEC3 RRs refused | KR_NSEC3_MAX_ITERATIONS 150; no salt-length limit; unlimited NSEC3 RRs per answer | kr_nsec3_limited() MAX_ITERATIONS 50 vs kr_nsec3_price (macro removed at v5.7.1) with kr_nsec3_price(iterations, salt_len) (lib/dnssec/nsec3.h@v5.7.1); answers with >8 NSEC3 in AUTHORITY are bogus; SHA-1 work in cache/proofs bounded | yes | no | e966b7fdb1, eccb8e278c, b5051ac26f, 24699e9f20, a05cf1d379 | exact |
| 6.0.6 | 2024-02-13 | per-request crypto-validation budget (CVE-2023-50387 KeyTrap) | unbounded signature/key checks per answer | vld_limit_crypto_remains budget per request; exceeding it fails validation (E2BIG) without retry | yes | no | cc5051b444, feb65eb97b | exact |
| 6.0.8 | 2024-07-23 | built-in root trust anchors gain KSK-2024 (key id 38696) | etc/root.keys: KSK-2017 (20326) only | etc/root.keys: KSK-2017 + KSK-2024 (38696) | no | no | 62b3b1e931 | exact |

`(!)` would mark a commit not contained in the tag; none are.

## CVE fixes

| CVE | NVD published | fix tag | fix date | latency (days) | DNSSEC | fix commit(s) | note |
|---|---|---|---|---|---|---|---|
| CVE-2018-1000002 | 2018-01-22 | v1.5.2 | 2018-01-22 | 0 | yes | d296e36eb5, f90d27de49 |  |
| CVE-2018-10920 | 2018-08-02 | v2.4.1 | 2018-08-02 | 0 | yes | d2dd680d54, 0d20fe3cc4 |  |
| CVE-2018-1110 | 2021-03-30 | v2.3.0 | 2018-04-23 | -1072 | no | c77bce8a0d, 8ea37cc36d, 96a12caf33, 120351eda3, fbbec0a15b | NEWS cites security!2/!4 in a private repo; c77bce8a is the merge "changes from security repo" and the listed commits are its non-merge parents |
| CVE-2019-10190 | 2019-07-16 | v4.1.0 | 2019-07-10 | -6 | yes | c5654da745, 625f4882d3 | NEWS cites !827 (merge 625f4882); the behavioural change is in c5654da7 "failing states in answer finalization" |
| CVE-2019-10191 | 2019-07-16 | v4.1.0 | 2019-07-10 | -6 | yes | bef03dcfb1 |  |
| CVE-2019-19331 | 2019-12-16 | v4.3.0 | 2019-12-04 | -12 | no | edb8ffef7f, 204960369b, 4fbd5baf3c |  |
| CVE-2020-12667 | 2020-05-19 | v5.1.1 | 2020-05-19 | 0 | no | ba7b89db78, 54f05e4d7b |  |
| CVE-2021-40083 | 2021-08-25 | v5.3.2 | 2021-05-05 | -112 | yes | 97ec93e178 | inventory says fix_release 5.4.2 because the NEWS commit c360ef30 that added the CVE id landed in v5.4.2; the code fix 97ec93e1 is in v5.3.2 (NEWS 5.3.2: "validator: fix 5.3.1 regression on over-limit NSEC3 edge case (!1169)") |
| CVE-2022-32983 | 2022-06-20 | - | - | - | no | 097339c188 | no code fix in the clone; the only related commit is the docs warning 097339c1 "policy docs: warn about filters and forwarding" (2022-01-11, first in v5.5.0), which predates NVD publication. NVD refs a GitHub hash ccb9d9794db5 present in clone, untagged, patch-identical to 097339c1. |
| CVE-2022-40188 | 2022-09-23 | v5.5.3 | 2022-09-21 | -2 | no | f6577a20e4 | inventory sha 817586f8 is a later duplicate of f6577a20 not contained in any tag |
| CVE-2023-26249 | 2023-02-21 | v5.6.0 | 2023-01-26 | -26 | no | 3e28a8a644, a9528e334b | CVE id never appears in NEWS; mapped via NVD description ("hundred TCP connection attempts") to NEWS 5.6.0 Security entry (!1380) |
| CVE-2023-46317 | 2023-10-22 | v5.7.0 | 2023-08-22 | -61 | no | 49876a99ba |  |
| CVE-2023-50387 | 2024-02-14 | v5.7.1 | 2024-02-13 | -1 | yes | cc5051b444, feb65eb97b | v6.0.6 (same day) contains the same commits; inventory sha 151c2645 is a rebased duplicate not in any tag |
| CVE-2023-50868 | 2024-02-14 | v5.7.1 | 2024-02-13 | -1 | yes | e966b7fdb1, eccb8e278c, b5051ac26f, 24699e9f20, a05cf1d379 | v6.0.6 (same day) contains the same commits; inventory sha 96525e9a is a rebased duplicate not in any tag |
| CVE-2026-39155 | 2026-07-23 | n/a | n/a | n/a | n/a | - | Knot DNS mod-onlinesign (authoritative signer) issue; listed under kresd only by keyword overlap ("Knot"). No kresd fix exists or is needed. |
| CVE-2026-66374 | 2026-07-25 | v6.4.1 | 2026-07-22 | -3 | no | beab42290f, 7eb2e11810, 2e18114ade | DoQ server code exists only in 6.2.0+ (NEWS 6.2.0: "DNS-over-QUIC (DoQ) is available for serving"); 5.7.x unaffected. NEWS 6.4.1 names no CVE id. |

Negative latency = fix released before NVD publication (coordinated disclosure or late CVE assignment).

## Other security fixes without a CVE id

- 1.3.0 (2017-06-13): - Refactor handling of AD flag and security status of resource records. -- dfdafb9a4f, 527577dd22, d8cd33f81f
- 1.3.2 (2017-07-28): - fix possible opportunities to use insecure data from cache as keys -- 8dac5cd7ff
- 1.3.3 (2017-08-09): - Fix a critical DNSSEC flaw.  Signatures might be accepted as valid -- d7d7cae5a3
- 2.4.0 (2018-07-03): - fix a rare case of zones incorrectly dowgraded to insecure status (!576) -- f37d6c2540, 3cc35e0e07
- 5.7.7 (2026-07-22): - DNSSEC correctness issues, acting mainly through the aggressive cache: -- a7ee59ebee, 1c00e8da3b
- 6.4.1 (2026-07-22): - DNSSEC correctness issues, acting mainly through the aggressive cache: -- 29b55ceb42, ccbf48088f

## Post-hoc NEWS edits (text at latest tag differs from text at the release tag)

- 1.2.0 (vs v1.5.3): added 1, removed 1
  - + - New policy.QTRACE policy to print packet contents
  - - - New policy.TRACE() policy to print packet contents
- 2.0.0 (vs v2.4.1): added 1, removed 1
  - + - systemd: change unit files to allow running multiple instances, deployments with single instance now must use `kresd@1.service` instead of `kresd.service`; se
  - - - systemd: change unit files to allow running multiple instances, deployments with single instance now must use `kresd@1.service` instead of `kresd.service`; se
- 2.3.0 (vs v2.4.1): added 1, removed 0
  - + - new policy.REFUSE to reply REFUSED to clients
- 5.2.0 (vs v5.7.8): added 1, removed 1
  - + - lower default EDNS buffer size to 1232 bytes (#538, #300, !920); see https://www.dnsflagday.net/2020/
  - - - lower default EDNS buffer size to 1232 bytes (#538, #300, !920); see https://dnsflagday.net/2020/
- 5.3.2 (vs v5.7.8): added 1, removed 1
  - + - validator: fix 5.3.1 regression on over-limit NSEC3 edge case (!1169) Assertion might be triggered by query/answer, potentially DoS. CVE-2021-40083 was later 
  - - - validator: fix 5.3.1 regression on over-limit NSEC3 edge case (!1169) Assertion might be triggered by query/answer, potentially DoS.
- 5.7.0 (vs v5.7.8): added 1, removed 1
  - + - avoid excessive TCP reconnections in a few more cases (!1448) Like before, the remote server had to behave nonsensically in order to inflict this upon itself,
  - - - avoid excessive TCP reconnections in a few more cases (!NNNN) Like before, the remote server had to behave nonsensically in order to inflict this upon itself,
- 6.0.9 (vs v6.4.2): added 1, removed 0
  - + - rate-limiting: add these options, mechanism, docs (!1624)
- 6.1.0 (vs v6.4.2): added 1, removed 0
  - + - fix handling of protolayer_data_sess_init_cb failure (!1797)

## Release list

| version | tag | date | stable | own entries | DNSSEC-ish rows |
|---|---|---|---|---|---|
| 1.0.0-beta1 | v1.0.0-beta1 | 2015-10-08 | no | 0 | 0 |
| 1.0.0-beta2 | v1.0.0-beta2 | 2015-11-20 | no | 0 | 0 |
| 1.0.0-beta3 | v1.0.0-beta3 | 2016-01-30 | no | 0 | 0 |
| 1.0.0 | v1.0.0 | 2016-05-30 | yes | 1 | 0 |
| 1.1.0 | v1.1.0 | 2016-08-11 | yes | 8 | 2 |
| 1.1.1 | v1.1.1 | 2016-08-24 | yes | 8 | 0 |
| 1.2.0-rc1 | v1.2.0-rc1 | 2017-01-17 | no | 16 | 0 |
| 1.2.0-rc2 | v1.2.0-rc2 | 2017-01-20 | no | 16 | 0 |
| 1.2.0-rc3 | v1.2.0-rc3 | 2017-01-24 | no | 17 | 0 |
| 1.2.0 | v1.2.0 | 2017-01-25 | yes | 17 | 4 |
| 1.2.1 | v1.2.1 | 2017-02-01 | yes | 3 | 1 |
| 1.2.2 | v1.2.2 | 2017-02-10 | yes | 5 | 1 |
| 1.2.3 | v1.2.3 | 2017-02-23 | yes | 4 | 0 |
| 1.2.4 | v1.2.4 | 2017-03-09 | yes | 15 | 4 |
| 1.2.5 | v1.2.5 | 2017-04-05 | yes | 15 | 7 |
| 1.2.6 | v1.2.6 | 2017-04-24 | yes | 6 | 3 |
| 1.3.0-rc1 | 1.3.0-rc1 | 2017-06-01 | no | 8 | 0 |
| 1.3.0 | v1.3.0 | 2017-06-13 | yes | 8 | 3 |
| 1.3.1 | v1.3.1 | 2017-06-23 | yes | 2 | 0 |
| 1.3.2 | v1.3.2 | 2017-07-28 | yes | 8 | 2 |
| 1.3.3 | v1.3.3 | 2017-08-09 | yes | 5 | 3 |
| 1.4.0 | v1.4.0 | 2017-09-21 | yes | 7 | 0 |
| 1.5.0 | v1.5.0 | 2017-11-02 | yes | 3 | 2 |
| 1.5.1 | v1.5.1 | 2017-12-12 | yes | 9 | 1 |
| 1.5.2 | v1.5.2 | 2018-01-22 | yes | 2 | 1 |
| 1.5.3 | v1.5.3 | 2018-01-23 | yes | 1 | 0 |
| 1.99.1-alpha | v1.99.1-alpha | 2017-10-26 | no | 7 | 2 |
| 2.0.0 | v2.0.0 | 2018-01-31 | yes | 15 | 6 |
| 2.1.0 | v2.1.0 | 2018-02-16 | yes | 11 | 3 |
| 2.1.1 | v2.1.1 | 2018-02-23 | yes | 3 | 1 |
| 2.2.0 | v2.2.0 | 2018-03-28 | yes | 4 | 0 |
| 2.3.0 | v2.3.0 | 2018-04-23 | yes | 10 | 5 |
| 2.4.0 | v2.4.0 | 2018-07-03 | yes | 16 | 6 |
| 2.4.1 | v2.4.1 | 2018-08-02 | yes | 6 | 2 |
| 3.0.0 | v3.0.0 | 2018-08-17 | yes | 13 | 3 |
| 3.1.0 | v3.1.0 | 2018-11-02 | yes | 7 | 0 |
| 3.2.0 | v3.2.0 | 2018-12-17 | yes | 23 | 3 |
| 3.2.1 | v3.2.1 | 2019-01-10 | yes | 10 | 6 |
| 4.0.0 | v4.0.0 | 2019-04-18 | yes | 39 | 8 |
| 4.1.0 | v4.1.0 | 2019-07-10 | yes | 20 | 4 |
| 4.2.0 | v4.2.0 | 2019-08-05 | yes | 5 | 0 |
| 4.2.1 | v4.2.1 | 2019-09-26 | yes | 7 | 2 |
| 4.2.2 | v4.2.2 | 2019-10-07 | yes | 1 | 0 |
| 4.3.0 | v4.3.0 | 2019-12-04 | yes | 14 | 2 |
| 5.0.0 | v5.0.0 | 2020-01-27 | yes | 19 | 0 |
| 5.0.1 | v5.0.1 | 2020-02-05 | yes | 2 | 0 |
| 5.1.0 | v5.1.0 | 2020-04-29 | yes | 21 | 2 |
| 5.1.1 | v5.1.1 | 2020-05-19 | yes | 2 | 1 |
| 5.1.2 | v5.1.2 | 2020-07-01 | yes | 7 | 0 |
| 5.1.3 | v5.1.3 | 2020-09-08 | yes | 11 | 3 |
| 5.2.0 | v5.2.0 | 2020-11-11 | yes | 20 | 1 |
| 5.2.1 | v5.2.1 | 2020-12-09 | yes | 4 | 0 |
| 5.3.0 | v5.3.0 | 2021-02-25 | yes | 14 | 0 |
| 5.3.1 | v5.3.1 | 2021-03-31 | yes | 6 | 1 |
| 5.3.2 | v5.3.2 | 2021-05-05 | yes | 8 | 2 |
| 5.4.0 | v5.4.0 | 2021-07-29 | yes | 11 | 1 |
| 5.4.1 | v5.4.1 | 2021-08-19 | yes | 4 | 0 |
| 5.4.2 | v5.4.2 | 2021-10-13 | yes | 6 | 0 |
| 5.4.3 | v5.4.3 | 2021-12-01 | yes | 6 | 0 |
| 5.4.4 | v5.4.4 | 2022-01-05 | yes | 1 | 0 |
| 5.5.0 | v5.5.0 | 2022-03-15 | yes | 13 | 2 |
| 5.5.1 | v5.5.1 | 2022-06-14 | yes | 9 | 1 |
| 5.5.2 | v5.5.2 | 2022-08-16 | yes | 7 | 0 |
| 5.5.3 | v5.5.3 | 2022-09-21 | yes | 2 | 1 |
| 5.6.0 | v5.6.0 | 2023-01-26 | yes | 8 | 3 |
| 5.7.0 | v5.7.0 | 2023-08-22 | yes | 6 | 2 |
| 5.7.1 | v5.7.1 | 2024-02-13 | yes | 4 | 2 |
| 5.7.2 | v5.7.2 | 2024-03-27 | yes | 1 | 0 |
| 5.7.3 | v5.7.3 | 2024-05-30 | yes | 2 | 1 |
| 5.7.4 | v5.7.4 | 2024-07-23 | yes | 3 | 1 |
| 5.7.5 | v5.7.5 | 2025-04-24 | yes | 5 | 1 |
| 5.7.6 | v5.7.6 | 2025-07-17 | yes | 2 | 0 |
| 5.7.7 | v5.7.7 | 2026-07-22 | yes | 12 | 4 |
| 5.7.8 | v5.7.8 | 2026-08-05 | yes | 3 | 0 |
| 6.0.0a1 | v6.0.0a1 | 2023-05-22 | no | 2 | 0 |
| 6.0.1 | v6.0.1 | 2023-06-23 | no | 0 | 0 |
| 6.0.2 | v6.0.2 | 2023-08-30 | no | 0 | 0 |
| 6.0.3 | v6.0.3 | 2023-09-25 | no | 0 | 0 |
| 6.0.4 | v6.0.4 | 2023-10-05 | no | 0 | 0 |
| 6.0.5 | v6.0.5 | 2024-01-09 | no | 0 | 0 |
| 6.0.6 | v6.0.6 | 2024-02-13 | yes | 6 | 3 |
| 6.0.7 | v6.0.7 | 2024-03-27 | yes | 15 | 0 |
| 6.0.8 | v6.0.8 | 2024-07-23 | yes | 18 | 3 |
| 6.0.9 | v6.0.9 | 2024-11-11 | yes | 14 | 2 |
| 6.0.10 | v6.0.10 | 2025-01-20 | yes | 7 | 0 |
| 6.0.11 | v6.0.11 | 2025-02-26 | yes | 7 | 1 |
| 6.0.12 | v6.0.12 | 2025-04-24 | yes | 6 | 0 |
| 6.0.13 | v6.0.13 | 2025-05-29 | yes | 7 | 1 |
| 6.0.14 | v6.0.14 | 2025-06-03 | yes | 1 | 0 |
| 6.0.15 | v6.0.15 | 2025-07-17 | yes | 11 | 2 |
| 6.0.16 | v6.0.16 | 2025-10-30 | yes | 9 | 1 |
| 6.0.17 | v6.0.17 | 2025-12-02 | yes | 6 | 2 |
| 6.1.0 | v6.1.0 | 2026-01-08 | yes | 9 | 2 |
| 6.2.0 | v6.2.0 | 2026-02-03 | yes | 3 | 0 |
| 6.3.0 | v6.3.0 | 2026-04-27 | yes | 8 | 0 |
| 6.4.0 | v6.4.0 | 2026-06-17 | yes | 4 | 0 |
| 6.4.1 | v6.4.1 | 2026-07-22 | yes | 6 | 3 |
| 6.4.2 | v6.4.2 | 2026-08-05 | yes | 4 | 0 |

## Verification

Phase 3 adversarial check: **PASS WITH CORRECTIONS** (220 checks, 8 failed, 5 corrections applied 2026-09-29). Report: `docs/handoff/verify/kresd.md`.

## Gaps

- Algorithm support: kresd delegates DNSKEY/DS algorithm and digest support to libdnssec/libknot (lib/dnssec.c calls dnssec_algorithm_key_support / dnssec_algorithm_digest_support). The clone has no commit adding RSASHA256/512, ECDSA, Ed25519/Ed448 or GOST (git log --all -i --grep for each returns nothing). Dates for algorithm support therefore belong to the Knot DNS timeline, not this one; only the unknown-algorithm handling (1.3.2, 4.0.0) and the SHA-1 DS rule (5.5.0) are kresd-side.
- CVE-2022-32983: no code fix found in the clone; the vendor treated it as a configuration/documentation issue (097339c1 in v5.5.0). fix_tag left null.
- CVE-2026-39155 is a Knot DNS (authoritative) CVE that the keyword search attached to kresd; marked not applicable.
- CVE-2018-1110 and CVE-2019-10190: exact fixing commits are approximate (private security repo merge; !827 merge). See attribution_reason.
- NEWS sections for v6.0.1 .. v6.0.5 contain no per-release entries (only the alpha/early-access notice); their DNSSEC behaviour is that of the 5.x commits they contain (merge-base of v6.0.0a1 with 5.x is v5.5.3).
- Pre-release tags (v1.0.0-beta*, v1.2.0-rc*, 1.3.0-rc1, v6.0.0a1) are listed with stable=false and no entry rows; entries are attributed to the final release.
- v1.0.0 and v1.1.0 ChangeLog entries are one-liners; no DNSSEC entry exists for 1.0.0 ("First release") although validation code was present (lib/dnssec.c exists at v1.0.0). The initial validation-capable release is therefore 1.0.0 by code presence, not by changelog claim.
- The 6.x declarative config keeps validation on by default (manager/.../config_schema.py@v6.0.6:123 "dnssec: Union[bool, DnssecSchema] = True"); no 6.x default change recorded because it continues the 4.0.0 default.
- Non-DNSSEC default changes seen in NEWS but not tabulated as default_changes: 5.6.0 cache.max_ttl default 6 days -> 1 day; 1.5.1 priming on by default; 2.0.0 policy module on by default (they appear as entry rows only).
- Post-hoc NEWS edits (CVE ids added after the release) are listed in news_edits; the entry rows use the text as it was at the release tag.
