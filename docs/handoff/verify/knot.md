# Phase 3 verification: knot (Knot DNS)

Verified 2026-09-29 against `out/software_repos/knot.git` (bare, blob-less), `data/software/timelines/knot.json` / `knot.md` (generated 2026-09-28) and `data/software/cve_inventory.json`. Every command below was run from the repository root with `C=out/software_repos/knot.git`.

**Verdict: PASS WITH CORRECTIONS.** Release dates, stable flags, coverage, changelog attribution and the md/json twin all reproduce exactly; seven rows need correction, the load-bearing one being CVE-2026-39155, whose `fix_tag` (`v3.4.10`) does not contain one of its two fix commits and is not the earliest stable tag containing a fix (`v3.5.4` was tagged 14 minutes earlier).

Sampling: `random.seed(20260929)` in Python 3, `random.sample(sorted(tags), 20)` for A and `random.sample(pool, 20)` over the 527 kept `changelog_entries[]` for D (19 distinct releases, RELNOTES and NEWS eras both hit).

## Checks run

### A. Release dates (20 random + first + last; plus a full sweep)

Command for every row: `git -C $C log -1 --format=%cI <tag>^{commit}`; expected = `released_full`. Stable rule: `stable=false` iff tag matches `-(rc|beta|alpha|test|rosedb)` or `.dev$` or is `v1.99.*`.

| section | row | command | expected | observed | result |
|---|---|---|---|---|---|
| A | v0.1 (first) | `git -C $C log -1 --format=%cI v0.1^{commit}` | 2011-02-02T16:08:59+01:00, stable | 2011-02-02T16:08:59+01:00 | PASS |
| A | v3.7.dev (last tag) | `git -C $C log -1 --format=%cI v3.7.dev^{commit}` | 2026-09-08T09:44:44+02:00, stable=false | 2026-09-08T09:44:44+02:00 | PASS |
| A | v3.6.0 (last stable) | `git -C $C log -1 --format=%cI v3.6.0^{commit}` | 2026-09-08T09:41:57+02:00, stable | 2026-09-08T09:41:57+02:00 | PASS |
| A | v2.5.1 | `git -C $C log -1 --format=%cI v2.5.1^{commit}` | 2017-06-07T15:27:41+02:00 | same | PASS |
| A | v2.9.3 | `git -C $C log -1 --format=%cI v2.9.3^{commit}` | 2020-03-03T07:47:22+01:00 | same | PASS |
| A | v3.3.8 | `git -C $C log -1 --format=%cI v3.3.8^{commit}` | 2024-07-22T08:21:15+02:00 | same | PASS |
| A | v1.99.1 | `git -C $C log -1 --format=%cI v1.99.1^{commit}` | 2015-02-11T17:14:11+01:00, stable=false | same, false | PASS |
| A | v3.2.2 | `git -C $C log -1 --format=%cI v3.2.2^{commit}` | 2022-11-01T06:33:51+01:00 | same | PASS |
| A | v2.7.4 | `git -C $C log -1 --format=%cI v2.7.4^{commit}` | 2018-11-13T10:38:14+01:00 | same | PASS |
| A | v1.3.1 | `git -C $C log -1 --format=%cI v1.3.1^{commit}` | 2013-08-27T13:29:57+02:00 | same | PASS |
| A | v2.6.7 | `git -C $C log -1 --format=%cI v2.6.7^{commit}` | 2018-05-17T11:07:49+02:00 | same | PASS |
| A | v1.6.0-rc1 | `git -C $C log -1 --format=%cI v1.6.0-rc1^{commit}` | 2014-10-13T21:16:12+02:00, stable=false | same, false | PASS |
| A | v3.1.0 | `git -C $C log -1 --format=%cI v3.1.0^{commit}` | 2021-08-01T20:22:20+02:00 | same | PASS |
| A | v2.4.3 | `git -C $C log -1 --format=%cI v2.4.3^{commit}` | 2017-04-10T19:29:51+02:00 | same | PASS |
| A | v2.8.0 | `git -C $C log -1 --format=%cI v2.8.0^{commit}` | 2019-03-05T14:40:16+01:00 | same | PASS |
| A | v3.5.5 | `git -C $C log -1 --format=%cI v3.5.5^{commit}` | 2026-06-12T07:50:03+02:00 | same | PASS |
| A | v1.1.0-rc2 | `git -C $C log -1 --format=%cI v1.1.0-rc2^{commit}` | 2012-08-23T15:48:57+02:00, stable=false | same, false | PASS |
| A | v2.9.0 | `git -C $C log -1 --format=%cI v2.9.0^{commit}` | 2019-10-10T12:12:32+02:00 | same | PASS |
| A | v0.3 | `git -C $C log -1 --format=%cI v0.3^{commit}` | 2011-09-02T20:11:07+02:00 | same (lightweight tag) | PASS |
| A | v2.0.2 | `git -C $C log -1 --format=%cI v2.0.2^{commit}` | 2015-11-24T17:16:59+01:00 | same | PASS |
| A | v2.8.5 | `git -C $C log -1 --format=%cI v2.8.5^{commit}` | 2020-01-01T08:54:47+01:00 | same | PASS |
| A | v3.0.7 | `git -C $C log -1 --format=%cI v3.0.7^{commit}` | 2021-06-16T06:59:50+02:00 | same | PASS |
| A | v3.0.9 | `git -C $C log -1 --format=%cI v3.0.9^{commit}` | 2021-09-09T18:27:11+02:00 | same | PASS |
| A | all 216 releases (bonus sweep) | `git -C $C tag \| while read t; do echo "$t $(git -C $C log -1 --format=%cI $t^{commit})"; done` diffed against `released_full` | 0 mismatches | 0 mismatches; no migration-day clustering (dates are spread, tags are annotated with real commit dates) | PASS |
| A | stable flag rule, all 216 | regex above vs `stable` | 0 contradictions | 0 contradictions; 174 stable / 42 not | PASS |

### B. Default changes (every row, every commit)

Per commit: (1) `git -C $C show --stat <sha>`, (2) `git -C $C tag --contains <sha> | grep -x <tag>`, (3) earliest stable tag among `git -C $C tag --contains <sha>` (dated with `log -1 --format=%cI`) and among siblings from `git -C $C log --all -i --format='%h %cI %s' --grep='<words>'`. Per row: (4) before/after read from `git -C $C show <sha> -- <path>` or `git -C $C show <tag>:<path>`, (5) flags, (6) attribution.

| section | row | command | expected | observed | result |
|---|---|---|---|---|---|
| B1-3 | 1.4.2 / 704e2bff9a | `git -C $C show --stat 704e2bff9a; git -C $C tag --contains 704e2bff9a \| grep -x v1.4.2; git -C $C log --all -i --format='%h %cI %s' --grep='refresh signatures earlier'` | product code; in v1.4.2; earliest v1.4.2 | 12 files, all `src/` (policy.c new, zones.c, zone-events.c); hit; only sibling is itself; earliest v1.4.2 | PASS |
| B4-6 | 1.4.2 before/after | `git -C $C show 704e2bff9a -- src/libknot/dnssec/policy.c; git -C $C grep -n KNOT_DNSSEC_DEFAULT_LIFETIME v1.4.2 -- src/libknot/dnssec/policy.h` | refresh 3 days before expiry | `signature_safety = sign_lifetime / 10`; `KNOT_DNSSEC_DEFAULT_LIFETIME 2592000` (30 d) so 3 d with the default; applies_on_upgrade=true consistent; attribution exact | PASS (remark: mechanism is lifetime/10, "3 days" holds only for the default lifetime, as NEWS says) |
| B1-3 | 2.0.0 / 4a85667e72 | `git -C $C show --stat 4a85667e72; git -C $C tag --contains 4a85667e72 \| grep -x v2.0.0` | product code; in v2.0.0; earliest v2.0.0 | 1 file `src/dnssec/lib/kasp/policy.c`; hit; earliest stable v2.0.0 (also in v2.0.0-beta) | PASS |
| B1-3 | 2.0.0 / 8aaba1c994 | `git -C $C show --stat 8aaba1c994; git -C $C tag --contains 8aaba1c994 \| grep -x v2.0.0; git -C $C tag --contains 8aaba1c994 \| grep 1.99` | product code; in v2.0.0; first_tag v1.99.1 | `dnssec/lib/kasp/policy.c`, `kasp.h`; hit; v1.99.1 (dev preview) contains it; earliest stable v2.0.0 | PASS |
| B4-6 | 2.0.0 before/after | `git -C $C show 4a85667e72; git -C $C show 8aaba1c994; git -C $C show v2.0.0:doc/configuration.rst \| sed -n 440,465p` | RSASHA512 -> RSASHA256, ksk 2048 / zsk 1024 | diff `RSA_SHA512` -> `RSA_SHA256`; 8aaba1c99 sets ksk 2048, zsk 1024; doc "default value is RSA-SHA-256", 2048, 1024; applies_on_upgrade=false with stated reason | PASS |
| B1-3 | 2.1.0 / 2e64ea6d08 | `git -C $C show --stat 2e64ea6d08; git -C $C tag --contains 2e64ea6d08 \| grep -x v2.1.0; git -C $C log --all -i --format='%h %cI %s' --grep='default algorithm'` | product code; in v2.1.0; earliest v2.1.0 | `src/dnssec/lib/kasp/policy.c`; hit; siblings 4a85667e7 (v2.0.0, RSA) and bff0cab1f (TSIG, unrelated); earliest v2.1.0 | PASS |
| B1-3 | 2.1.0 / 8c298aa490 | `git -C $C show --stat 8c298aa490; git -C $C tag --contains 8c298aa490 \| grep -x v2.1.0` | product code; in v2.1.0 | `src/dnssec/lib/kasp/policy.c` (+59/-9); hit; earliest v2.1.0 | PASS |
| B1-3 | 2.1.0 / 855238534b | `git -C $C show --stat 855238534b; git -C $C tag --contains 855238534b \| grep -x v2.1.0` | in v2.1.0 | `doc/configuration.rst` only (documentation commit, cited as such); hit; earliest v2.1.0 | PASS (doc-only commit, acceptable as the `documentation` evidence, not as the change itself) |
| B4-6 | 2.1.0 before/after | `git -C $C show 2e64ea6d08; git -C $C show 8c298aa490; git -C $C show 855238534b` | RSASHA256 -> ECDSAP256SHA256; DEFAULT_KEY_SIZES table | diff `RSA_SHA256` -> `ECDSA_P256_SHA256`; table RSA* zsk 1024/ksk 2048, ECDSAP256 256/256, ECDSAP384 384/384; doc "default value is ECDSA-P256-SHA256", 256 bits | PASS |
| B1-3 | 2.2.0 / 6a7da32dd1 | `git -C $C show --stat 6a7da32dd1; git -C $C tag --contains 6a7da32dd1 \| grep -x v2.2.0; git -C $C log --all -i --format='%h %cI %s' --grep='key_size_default'` | product code; in v2.2.0; earliest v2.2.0 | `key.h`, `key/algorithm.c` (+ unit test); hit; no sibling; earliest v2.2.0 | PASS |
| B1-3 | 2.2.0 / 8d5b25d539 | `git -C $C show --stat 8d5b25d539; git -C $C tag --contains 8d5b25d539 \| grep -x v2.2.0` | product code; in v2.2.0 | `kasp/policy.c`, `key/algorithm.c`; hit; earliest v2.2.0 | PASS |
| B1-3 | 2.2.0 / 3d5626ab17 | `git -C $C show --stat 3d5626ab17; git -C $C tag --contains 3d5626ab17 \| grep -x v2.2.0` | product code; in v2.2.0 | `src/dnssec/utils/keymgr.c`; hit; earliest v2.2.0 | PASS |
| B4 | 2.2.0 before/after | `git -C $C show 6a7da32dd1 -- src/dnssec/lib/key/algorithm.c; git -C $C show 3d5626ab17; git -C $C show v2.2.0:src/dnssec/lib/kasp/policy.c \| grep -n size; git -C $C show v2.3.0:doc/reference.rst \| grep -n -A5 '^ksk-size'` | RSA* 2048, DSA 1024, EC 256/384; keymgr picks default | `dnssec_algorithm_key_size_default()` returns exactly those; keymgr.c drops "Key size has to be specified"; policy.c@v2.2.0:74-75 uses the default for zsk and ksk; reference.rst@v2.3.0:624 "1024 (dsa*), 2048 (rsa*), 256 (ecdsap256*), 384 (ecdsap384*)" | PASS |
| B4 | 2.2.0 documentation pointer | `git -C $C show v2.2.0:doc/man_keymgr.rst \| sed -n 238,246p` | line 243 documents zone-key default size | line 243 is inside `**tsig** **generate**` ("Generate new TSIG key ... default key size is determined optimally"); the `zone key generate` paragraph (line 98-99) says nothing about size | FAIL (wrong citation; see corrections) |
| B5-6 | 2.2.0 flags | as above | applies_on_upgrade=false / opt_in=false with reason | note present ("affects only newly generated RSA keys"); attribution exact | PASS |
| B1-3 | 2.3.0 / dfc39e540e | `git -C $C show --stat dfc39e540e; git -C $C tag --contains dfc39e540e \| grep -x v2.3.0; git -C $C log --all -i --format='%h %cI %s' --grep='NSEC3 resalt'` | product code; in v2.3.0; earliest v2.3.0 | `src/dnssec/lib/event/action/nsec3_resalt.c` (new) + event wiring; hit; all resalt siblings are later fixes (v2.4.0+); earliest v2.3.0 | PASS |
| B1-3 | 2.3.0 / b83e49365e | `git -C $C show --stat b83e49365e; git -C $C tag --contains b83e49365e \| grep -x v2.3.0` | in v2.3.0 | merge, 57 files incl. `src/knot/conf/scheme.c`, `doc/reference.rst`, tests-extra; hit; earliest v2.3.0 | PASS |
| B4-6 | 2.3.0 before/after | `git -C $C show v2.3.0:src/knot/conf/scheme.c \| sed -n 160,170p; git -C $C show v2.3.0:doc/reference.rst \| grep -n -A5 '^nsec3-iterations'; git -C $C grep -c -i resalt v2.2.1 -- src/` | salt-lifetime 30 d, salt-len 8, iter 10 in schema; doc says 5; no resalt in 2.2.x | scheme.c:166-168 `C_NSEC3_ITER ... 10`, `C_NSEC3_SALT_LEN ... 8`, `C_NSEC3_SALT_LIFETIME ... DAYS(30)`; reference.rst:687 "*Default:* 5"; no `resalt` in v2.2.1 src | PASS |
| B1-3 | 2.4.0 / a7c72081a0 | `git -C $C show --stat a7c72081a0; git -C $C tag --contains a7c72081a0 \| grep -x v2.4.0; git -C $C log --all -i --format='%h %cI %s' --grep='retired'` | product code; in v2.4.0; earliest v2.4.0 | `keyusage.c/.h`, `initial_key.c`, `zsk_rollover.c` (+ unit test); hit; merge 7fa8ad0bc also v2.4.0; earliest v2.4.0 | PASS |
| B4-6 | 2.4.0 before/after | `git -C $C show a7c72081a0 -- src/dnssec/lib/event/action/zsk_rollover.c` | retired key removed | `exec_remove_old_key` now calls `dnssec_keystore_remove_key(ctx->keystore, retired->id)` | PASS |
| B1-3 | 2.5.5 / a1283c9c02 | `git -C $C show --stat a1283c9c02; git -C $C tag --contains a1283c9c02 \| grep -x v2.5.5; git -C $C log --all -i --format='%h %cI %s' --grep='inception'` | product code; in v2.5.5; earliest v2.5.5 | `src/knot/dnssec/rrset-sign.c`; hit; sibling 752b9ea96 in v2.6.0 (2017-09-29T13:58, later than v2.5.5 10:14) | PASS |
| B4-6 | 2.5.5 before/after | `git -C $C show a1283c9c02` | incept = now - 90 min | `#define RRSIG_INCEPT_IN_PAST (90 * 60)`; `sig_incept = now - RRSIG_INCEPT_IN_PAST`; `sig_expire = now + rrsig_lifetime` | PASS |
| B1-3 | 2.6.0 / da9e7ceb8f | `git -C $C show --stat da9e7ceb8f; git -C $C tag --contains da9e7ceb8f \| grep -x v2.6.0; git -C $C log --all -i --format='%h %cI %s' --grep='remove DSA'` | product code; in v2.6.0; earliest v2.6.0 | `key.h`, `algorithm.c`, `convert.c`, `der.c`, `sign.c` (+tests); hit; siblings 6f6faba23/b86ae37d7/7b5545b85 all v2.6.0; 55b474aa2 in v2.5.5 removes tests only | PASS |
| B4-6 | 2.6.0 before/after | `git -C $C show da9e7ceb8f -- src/dnssec/lib/dnssec/key.h; git -C $C grep -n 'DSA algorithm' v2.6.0 -- src/; git -C $C show v2.5.7:src/dnssec/lib/dnssec/key.h \| grep DSA` | enum drops 3 and 6; conf check; 2.5.x still has DSA | `-DSA_SHA1 = 3`, `-DSA_SHA1_NSEC3 = 6`; `tools.c:334 "DSA algorithm no longer supported"`; v2.5.7 key.h still lists 3 and 6 | PASS |
| B1-3 | 2.7.0 / d0f52e7c40 | `git -C $C show --stat d0f52e7c40; git -C $C tag --contains d0f52e7c40 \| grep -x v2.7.0; git -C $C log --all -i --format='%h %cI %s' --grep='minimum allowed RSA'` | product code; in v2.7.0; earliest v2.7.0 | `src/dnssec/lib/key/algorithm.c` (+tests); hit; no sibling; not in any 2.6.x tag | PASS |
| B4 | 2.7.0 before/after | `git -C $C show d0f52e7c40 -- src/dnssec/lib/key/algorithm.c` | RSA .min 512 -> 1024 | `.min = 512` removed, RSA_SHA512 limits (min 1024) reused for all RSA | PASS (remark: RSASHA512 already had min 1024; the change affects alg 5/7/8) |
| B4 | 2.7.0 documentation | `git -C $C show v2.7.0:NEWS \| sed -n 1,60p \| grep -n 1024` | "not in NEWS" (as the row claims) | NEWS 2.7.0 line 27: " - Minimum allowed RSA key length was increased to 1024" | FAIL (documentation and gaps[3] wrong) |
| B5-6 | 2.7.0 flags | as above | applies_on_upgrade=true | limit change, note given; attribution exact | PASS |
| B1-3 | 2.7.5 / 8e2530f02c | `git -C $C show --stat 8e2530f02c; git -C $C tag --contains 8e2530f02c \| grep -x v2.7.5; git -C $C log --all -i --format='%h %cI %s' --grep='ksk is ready'` | product code; in v2.7.5; earliest v2.7.5 | `src/utils/keymgr/functions.c`; hit; sibling 2cbd07e73 in v2.8.0 (later) | PASS |
| B4-6 | 2.7.5 before/after | `git -C $C show 8e2530f02c` | KSK generated in ready state | `if ((flags & DNSKEY_GENERATE_KSK) && gen_timing.ready == infty) gen_timing.ready = gen_timing.active;` | PASS |
| B1-3 | 2.8.0 / 7f609f3dfb | `git -C $C show --stat 7f609f3dfb; git -C $C tag --contains 7f609f3dfb \| grep -x v2.8.0; git -C $C log --all -i --format='%h %cI %s' --grep='cds-cdnskey-publish'` | product code; in v2.8.0; earliest v2.8.0 | `src/knot/conf/schema.c` + docs; hit; no earlier sibling (others are doc commits 2021) | PASS |
| B4-6 | 2.8.0 cds before/after | `git -C $C show 7f609f3dfb; for t in v2.6.1 v2.7.5; do git -C $C show "${t}:src/knot/conf/schema.c" \| grep -n 'C_CHILD_RECORDS,'; done` | ALWAYS -> ROLLOVER; default ALWAYS since option introduced (2.6.1) | `CDS_CDNSKEY_ALWAYS` -> `CDS_CDNSKEY_ROLLOVER`; v2.6.1 and v2.7.5 schema `C_CHILD_RECORDS ... CHILD_RECORDS_ALWAYS`; reference.rst "*Default:* always" -> "rollover" | PASS |
| B1-3 | 2.8.0 / 6cf74f5d7a | `git -C $C show --stat 6cf74f5d7a; git -C $C tag --contains 6cf74f5d7a \| grep -x v2.8.0; git -C $C log --all -i --format='%h %cI %s' --grep="don't print DS"` | product code; in v2.8.0; earliest v2.8.0 | `src/utils/keymgr/functions.c` (1 deletion); hit; no sibling | PASS |
| B4-6 | 2.8.0 ds before/after | `git -C $C show 6cf74f5d7a` | SHA-1 removed from printed digests | `-DNSSEC_KEY_DIGEST_SHA1,` in `keymgr_generate_ds` digests[] | PASS |
| B1-3 | 3.0.2 / 5994a92c04 | `git -C $C show --stat 5994a92c04; git -C $C tag --contains 5994a92c04 \| grep -x v3.0.2; git -C $C log --all -i --format='%h %cI %s' --grep='GnuTLS policy'` | product code; in v3.0.2; earliest v3.0.2 | `libdnssec/key.h`, `key/algorithm.c`, `key/ds.c`, `sign/sign.c`; hit; sibling b0c6f0709 in v3.1.0 (later) | PASS |
| B4-6 | 3.0.2 before/after | `git -C $C show 5994a92c04 -- src/libdnssec/sign/sign.c` | support decided by GnuTLS policy | `dnssec_algorithm_key_support()` now `a != GNUTLS_SIGN_UNKNOWN && gnutls_sign_is_secure(a)` | PASS |
| B1-3 | 3.1.0 / f86cc39e0e | `git -C $C show --stat f86cc39e0e; git -C $C tag --contains f86cc39e0e \| grep -x v3.1.0; git -C $C log --all -i --format='%h %cI %s' --grep='min(SOA TTL'` | product code; in v3.1.0; earliest v3.1.0 | `src/knot/dnssec/zone-nsec.c` (+ test data); hit; merge 43dd77a85 also v3.1.0; not in 3.0.x | PASS |
| B1-3 | 3.1.0 / 99e401a5d1 | `git -C $C show --stat 99e401a5d1; git -C $C tag --contains 99e401a5d1 \| grep -x v3.1.0` | product code; in v3.1.0 | `nsec3-chain.c`, `zone-nsec.c/.h`; hit; earliest v3.1.0 | PASS |
| B4-6 | 3.1.0 before/after | `git -C $C show f86cc39e0e -- src/knot/dnssec/zone-nsec.c; git -C $C show 99e401a5d1` | min(SOA TTL, SOA minimum); NSEC3PARAM follows | `zone_nsec_ttl()` returns `MIN(knot_soa_minimum(...), soa.ttl)` replacing `knot_soa_minimum` alone; `add_nsec3param(..., ttl)` | PASS |
| B1-3 | 3.2.0 / 0009836974 | `git -C $C show --stat 0009836974; git -C $C tag --contains 0009836974 \| grep -x v3.2.0; git -C $C log --all -i --format='%h %cI %s' --grep='NSEC3 iterations to 0'` | product code; in v3.2.0; earliest v3.2.0 | `src/knot/conf/schema.c` + docs (+tests); hit; no sibling | PASS |
| B4-6 | 3.2.0 iter before/after | `git -C $C show 0009836974 -- src/knot/conf/schema.c doc/reference.rst; git -C $C grep -n C_NSEC3_ITER v3.1.9 -- src/knot/conf/schema.c` | 10 -> 0 | `{ 0, UINT16_MAX, 10 }` -> `{ 0, UINT16_MAX, 0 }`; doc 10 -> 0; v3.1.9 still 10 | PASS |
| B1-3 | 3.2.0 / 084c8ab842 | `git -C $C show --stat 084c8ab842; git -C $C tag --contains 084c8ab842 \| grep -x v3.2.0; git -C $C log --all -i --format='%h %cI %s' --grep='rrsig refresh if not configured'` | product code; in v3.2.0; earliest v3.2.0 | `schema.c`, `dnssec/context.c`, `dnssec/policy.c` + docs; hit; no earlier sibling | PASS |
| B4 | 3.2.0 rrsig-refresh `after` | `git -C $C show 084c8ab842 -- src/knot/conf/schema.c src/knot/dnssec/context.c src/knot/dnssec/policy.c; git -C $C log --format='%h %cI %s' v3.1.9..v3.2.0 -i --grep=rrsig; git -C $C show d8b1e148f -- src/knot/dnssec/zone-events.c` | both halves of `after` readable from the cited commit | default = propagation_delay + zone_maximal_ttl: yes (context.c/policy.c). "configuration fails to load if rrsig-refresh is too low": **not in 084c8ab84**; it is `d8b1e148f` "dnssec: enforce safe rrsig-refresh" (2021-12-15, in v3.2.0): `log_zone_error(... "rrsig-refresh too low ...")`, `result = KNOT_EINVAL; goto done;` in `knot_dnssec_zone_sign` (warning-only version bbcb937ad, also v3.2.0) | FAIL (missing commit; also the hard error is a signing failure, not a config-load failure) |
| B5-6 | 3.2.0 rrsig-refresh flags | as above | applies_on_upgrade=true | yes; attribution exact | PASS |
| B1-3 | 3.3.3 / 3c7449eafa | `git -C $C show --stat 3c7449eafa; git -C $C tag --contains 3c7449eafa \| grep -x v3.3.3; git -C $C log --all -i --format='%h %cI %s' --grep="increase default for 'policy.rrsig-refresh'"` | product code; in v3.3.3; earliest v3.3.3 | `src/knot/dnssec/policy.c` + docs; hit; sibling dd73dc1fd on master first in v3.4.0 (later) | PASS |
| B4-6 | 3.3.3 before/after | `git -C $C show 3c7449eafa -- src/knot/dnssec/policy.c` | + 0.1 * rrsig-lifetime | `reserve = 0.1 * rrsig_lifetime; rrsig_refresh_before = MIN(lifetime - prerefresh - 1, min + reserve)` | PASS (remark: capped at lifetime - prerefresh - 1) |
| B1-3 | 3.4.0 / a7a739faab | `git -C $C show --stat a7a739faab; git -C $C tag --contains a7a739faab \| grep -x v3.4.0; git -C $C log --all -i --format='%h %cI %s' --grep='validation as event'` | product code; in v3.4.0; earliest v3.4.0 | 17 files incl. `events/handlers/validate.c` (new); hit; merge e8965be59 v3.4.0 | PASS |
| B4 | 3.4.0 `after` | `git -C $C show a7a739faab \| grep -n -i refresh; git -C $C show ce1e335c9 -- src/knot/dnssec/zone-sign.c; git -C $C tag --contains ce1e335c9 \| head -1` | "RRSIGs expiring within rrsig-refresh make validation fail" readable from cited commit | a7a739faab contains no rrsig-refresh logic (only adds the re-validation event and `stats->expire`). The rule is in **ce1e335c9** "dnssec/validation: consider end of RRSIG validitiy... for dnssec-validate that it is longer than rrsig-refresh" (2023-12-21, in v3.4.0): `else if (knot_time_lt(until, now + policy->rrsig_refresh_before)) { hint->warning = KNOT_ESOON_EXPIRE; }` | FAIL (wrong/missing commit) |
| B5-6 | 3.4.0 flags | as above | applies_on_upgrade=true with note | note "only zones with dnssec-validation enabled"; attribution exact | PASS (see remark on opt-in convention below) |
| B1-3 | 3.5.0 / edcb6b09f7 | `git -C $C show --stat edcb6b09f7; git -C $C tag --contains edcb6b09f7 \| grep -x v3.5.0; git -C $C log --all -i --format='%h %cI %s' --grep='default salt length'` | product code; in v3.5.0; earliest v3.5.0 | `src/knot/conf/schema.c` + doc (+tests); hit; sibling 6b35210e4 in no stable tag | PASS |
| B4-6 | 3.5.0 before/after | `git -C $C show edcb6b09f7 -- src/knot/conf/schema.c doc/reference.rst` | 8 -> 0 | `C_NSEC3_SALT_LEN { 0, UINT8_MAX, 8 }` -> `{ 0, UINT8_MAX, 0 }`; doc 8 -> 0 | PASS |
| B1-3 | 3.6.0 / c9b863e42f | `git -C $C show --stat c9b863e42f; git -C $C tag --contains c9b863e42f \| grep -x v3.6.0` | product code; in v3.6.0; earliest v3.6.0 | `schema.c/.h`, `zone/contents.c/.h`; hit; only tag v3.6.0 | PASS |
| B1-3 | 3.6.0 / 9e915de7c4 | `git -C $C show --stat 9e915de7c4; git -C $C tag --contains 9e915de7c4 \| grep -x v3.6.0` | product code; in v3.6.0 | `src/knot/zone/contents.c/.h` (+tests); hit | PASS |
| B1-3 | 3.6.0 / 5e2120fa67 | `git -C $C show --stat 5e2120fa67; git -C $C tag --contains 5e2120fa67 \| grep -x v3.6.0` | product code; in v3.6.0 | `src/knot/updates/ddns.c` (+test); hit | PASS |
| B4-6 | 3.6.0 iter-cap before/after | `git -C $C show c9b863e42f; git -C $C show 9e915de7c4 -- src/knot/zone/contents.c; git -C $C show 5e2120fa67 -- src/knot/updates/ddns.c` | max 65535 -> 256; NSEC3PARAM refused | `{ 0, UINT16_MAX, 0 }` -> `{ 0, CONF_NSEC3_MAX_ITERS, 0 }`, `#define CONF_NSEC3_MAX_ITERS 256`; `iterations > ... -> KNOT_ENSEC3PAR`; DDNS `"refusing to modify NSEC3PARAM"` REFUSED | PASS |
| B1-3 | 3.6.0 / 87d1c94222 | `git -C $C show --stat 87d1c94222; git -C $C tag --contains 87d1c94222 \| grep -x v3.6.0; git -C $C log --all -i --format='%h %cI %s' --grep='rrsig-pre-refresh'` | product code; in v3.6.0 | `schema.c`, `dnssec/context.c` + doc; hit; sibling 28e2987d1 (0.1 variant) in no tag | PASS |
| B4-6 | 3.6.0 pre-refresh before/after | `git -C $C show 87d1c94222` | 1 h -> 0.005 * lifetime | `HOURS(1)` -> `YP_NIL`; `rrsig_prerefresh = (num != YP_NIL) ? num : 0.005 * policy->rrsig_lifetime`; doc "1h" -> "0.005 * policy_rrsig-lifetime" | PASS |

Remark on B.5 (not counted as a failure): every Knot default change sits behind `dnssec-signing: on` (and 3.4.0 behind `dnssec-validation: on`). The builder used `applies_on_upgrade=true` to mean "users already on the feature see the change on upgrade" and recorded the gating feature in `note`. That is consistent across all 21 rows; the corrector may want to make the convention explicit in `branch_note`.

### C. CVE fixes (every row)

Inventory: `python3 -c "import json;i=json.load(open('data/software/cve_inventory.json'));print([e['cve'] for e in i['by_product']['knot']]);print([e['cve'] for e in i['fixes']['knot']])"`. Latency: `python3 -c "from datetime import date;print((date.fromisoformat('<fix>')-date.fromisoformat('<nvd>')).days)"`.

| section | row | command | expected | observed | result |
|---|---|---|---|---|---|
| C1 | CVE-2014-0486 inventory | inventory command | in by_product.knot | yes (fixes: no) | PASS |
| C2 | CVE-2014-0486 tag | `for h in fac2b82e8b 4dca5dbbf1 5cb0ba2f88 e63439b025 bd2a198dae; do git -C $C tag --contains $h \| grep -x v1.5.2; done; git -C $C show v1.5.2:NEWS \| sed -n 1,8p` | all in v1.5.2; earliest stable v1.5.2 | all 5 hit; earliest containing is v1.5.2 (next v1.5.3); NEWS 1.5.2 "Some RR parsing corner cases were not handled properly"; all touch `src/libknot/packet/rrset-wire.c` | PASS (attribution "approximate" with stated reason; issue #294 not reachable from the clone) |
| C3 | CVE-2014-0486 latency | latency 2014-09-08 - 2018-03-27 | -1296 | -1296 | PASS |
| C1 | CVE-2016-6171 inventory | inventory command | by_product + fixes | yes / yes | PASS |
| C2 | CVE-2016-6171 tag | `git -C $C tag --contains dde98863d0 \| grep -x v2.3.0; git -C $C tag --contains 85f3217b05 \| grep -x v2.3.0; git -C $C tag --contains c204b7f43; git -C $C log -1 --format=%cI v1.6.8^{commit}` | both in v2.3.0; v2.3.0 earlier than the 1.6 LTS backport | both hit; LTS merge c204b7f43 only in v1.6.8 (2016-08-09T18:41:46) vs v2.3.0 2016-08-09T16:29:55 -> v2.3.0 is earliest | PASS |
| C3 | CVE-2016-6171 latency | 2016-08-09 - 2017-02-09 | -184 | -184 | PASS |
| C1 | CVE-2017-11104 inventory | inventory command | by_product + fixes | yes / yes | PASS |
| C2 | CVE-2017-11104 tag | `git -C $C tag --contains 74862ce015 \| grep -x v2.5.2; git -C $C log --all --format='%h %cI %s' --grep='validity period check'; git -C $C tag --contains 3dfbb674b; git -C $C log -1 --format=%cI v2.4.5^{commit}` | in v2.5.2; v2.5.2 earlier than 2.4-line sibling | hit; sibling 3dfbb674b only in v2.4.5 (2017-06-23T11:36:16) vs v2.5.2 2017-06-23T10:32:22 -> v2.5.2 earliest; 1.6-line siblings 909d2b8a4/576d31256 in no tag | PASS |
| C3 | CVE-2017-11104 latency | 2017-06-23 - 2017-07-08 | -15 | -15 | PASS |
| C1-2 | CVE-2018-1000002 | `git -C $C show v3.6.0:NEWS \| grep -c CVE-2018-1000002; git -C $C log --all --oneline --grep=CVE-2018-1000002 \| wc -l`; inventory description | in by_product.knot; applicable=false justified | in by_product.knot (and kresd); description "Knot Resolver (prior version 1.5.2)"; 0 NEWS hits, 0 commits | PASS |
| C1-2 | CVE-2018-10920 | same pattern | applicable=false justified | "Knot Resolver before 2.4.1"; 0 / 0 | PASS |
| C1-2 | CVE-2018-1110 | same pattern | applicable=false justified | "knot-resolver before version 2.3.0"; 0 / 0 | PASS |
| C1-2 | CVE-2019-10190 | same pattern | applicable=false justified | "knot resolver ... before 4.1.0"; 0 / 0 | PASS |
| C1-2 | CVE-2019-10191 | same pattern | applicable=false justified | "knot resolver before version 4.1.0"; 0 / 0 | PASS |
| C1-2 | CVE-2019-19331 | same pattern | applicable=false justified | "knot-resolver before version 4.3.0"; 0 / 0 | PASS |
| C1-2 | CVE-2020-12667 | same pattern | applicable=false justified | "Knot Resolver before 5.1.1"; 0 / 0 | PASS |
| C1-2 | CVE-2022-32983 | same pattern | applicable=false justified | "Knot Resolver through 5.5.1"; 0 / 0 | PASS |
| C1-2 | CVE-2023-26249 | same pattern | applicable=false justified | "Knot Resolver before 5.6.0"; 0 / 0 | PASS |
| C1 | CVE-2026-39155 inventory | inventory command | in by_product.knot | yes (also kresd; description "Knot DNS before 3.4.10 and 3.5.x before 3.5.4 ... mod-onlinesign") | PASS |
| C2 | CVE-2026-39155 fix_tag contains every commit | `git -C $C tag --contains 605b3d1700 \| grep -x v3.4.10; git -C $C tag --contains 15647ab26d \| grep -x v3.4.10` | both hit | 605b3d1700: hit. **15647ab26d: no hit** (it is only in v3.5.4+); the JSON itself records `tag_contains_confirmed: false` for it | FAIL |
| C2 | CVE-2026-39155 earliest stable tag | `git -C $C log --all --format='%h %cI %s' --grep='immediately successive name'; git -C $C log -1 --format=%cI v3.5.4^{commit}; git -C $C log -1 --format=%cI v3.4.10^{commit}` | fix_tag is the earliest stable tag containing a fix | siblings: 15647ab26 -> v3.5.4 (2026-04-02T07:07:28+02:00), 605b3d170 -> v3.4.10 (2026-04-02T07:21:06+02:00), 3699716a7 -> v3.6.0. **v3.5.4 is earlier than v3.4.10** | FAIL |
| C3 | CVE-2026-39155 latency | 2026-04-02 - 2026-07-23 | -112 | -112 (unchanged by the tag correction, same day) | PASS |

### D. Changelog entries (20 random kept entries, seed 20260929, 19 distinct releases)

Per entry: (1) `git -C $C show <tag>:<changelog_path> | grep -F '<line>'` present and under the section header for that version; (2) `git -C $C show <prev>:<changelog_path> | grep -F '<line>'` absent, where `<prev>` is the previous stable tag on the same minor line (previous stable by date when the line has none, e.g. v1.1.0-rc1 -> v1.0.6, v2.1.0 -> v1.6.6); (3) mechanism vs text; (4) bullets in that version's section recounted (`^ - ` for NEWS, `^\s+\* ` for RELNOTES) vs `total_entries`. Each row below is four checks.

| section | row | command | expected | observed | result |
|---|---|---|---|---|---|
| D | v3.2.11 "keymgr: improved error message if a key file is not accessible" | `git -C $C show v3.2.11:NEWS \| grep -F '<line>'; git -C $C show v3.2.10:NEWS \| grep -F '<line>'` | present / absent / dnskey / 8 | present under 3.2.11 / absent / dnskey (keymgr key file) / 8 | PASS |
| D | v3.0.7 "keymgr: new command for primary SOA serial manipulation in on-secondary signing mode" | same with v3.0.7 / v3.0.6 | present / absent / other / 16 | present / absent / other / 16 | PASS |
| D | v3.4.11 "knotd: missing '0.1 * policy.rrsig_lifetime' part in 'rrsig-refresh' default if 'policy.zone-max-ttl' is set #978" | v3.4.11 / v3.4.10 | present / absent / rrsig / 24 | present / absent / rrsig / 24 | PASS |
| D | v2.7.0 "Online Signing support for automatic key rollover" | v2.7.0 / v2.6.8 | present / absent / other / 32 | present / absent / other / 32 | PASS |
| D | v3.4.3 "knotd: new configuration check for using default NSEC3 salt length, which will change" | v3.4.3 / v3.4.2 | present / absent / nsec3 / 16 | present / absent / nsec3 / 16 | PASS |
| D | v2.9.4 "Changed NSEC3PARAM not correctly detected during zone update" | v2.9.4 / v2.9.3 | present / absent / nsec3 / 20 | present / absent / nsec3 / 20 | PASS |
| D | v3.2.0 "knotd: default value for 'policy.nsec3-iterations' was lowered to 0" | v3.2.0 / v3.1.9 | present / absent / nsec3-iterations / 69 | present / absent / nsec3-iterations / 69 | PASS |
| D | v3.5.3 "knotd: increased defaults for 'database.timer-db-max-size' and 'database.kasp-db-max-size'" | v3.5.3 / v3.5.2 | present / absent / other / 28 | present / absent / other / 28 | PASS |
| D | v2.3.0 "Avoid multiple loads of the same PKCS #11 module" | v2.3.0 / v2.2.1 | present / absent / other / 13 | present / absent / other / 13 | PASS |
| D | v3.6.0 "keymgr: optional digest algorithm option for 'ds' command" | v3.6.0 / v3.5.8 | present / absent / ds-digest / 40 | present / absent / ds-digest / 40 | PASS |
| D | v1.1.0-rc1 "Fixed answering when transitioning from NSEC3 to NSEC." | `git -C $C show v1.1.0-rc1:RELNOTES \| grep -F ...; git -C $C show v1.0.6:RELNOTES \| grep -F ...` | present / absent / nsec3 / 25 | present under "v1.1.0-rc1 - Aug 17, 2012" / absent / nsec3 / 25 | PASS |
| D | v3.1.0 "knotd: TTL of generated NSEC(3) records is set to min(SOA TTL, SOA minimum)" | v3.1.0 / v3.0.8 | present / absent / nsec3 / 51 | present / absent / nsec3 / 51 | PASS |
| D | v3.5.8 "knotd: unauthenticated TSIG chosen-prefix signing that enables DDNS forgery (Thanks to Gia Bui)" | v3.5.8 / v3.5.7 | present / absent / other / 6 | present / absent / other / 6 | PASS |
| D | v3.4.0 "knotd: DNSSEC validation requires the remaining RRSIG validity is longer than 'rrsig-refresh'" | v3.4.0 / v3.3.9 | present / absent / validation / 51 | present / absent / validation / 51 | PASS |
| D | v3.4.10 "mod-onlinesign: incorrect next NSEC owner name leading to a DoS (Thanks to Shang Kunjie)" | v3.4.10 / v3.4.9 | present / absent / other / 14 | present / absent / other / 14 | PASS |
| D | v3.4.6 "knotd: default TSIG algorithm is now 'hmac-sha256'" | v3.4.6 / v3.4.5 | present / absent / other / 16 | present / absent / other / 16 | PASS |
| D | v3.5.7 "mod-onlinesign: server responds with SERVFAIL instead of NOERROR if reply is truncated" | v3.5.7 / v3.5.6 | present / absent / other / 24 | present / absent / other / 24 | PASS |
| D | v3.4.6 "kdig: new '+[no]doflag' alias for '+[no]dnssec' #952" | v3.4.6 / v3.4.5 | present / absent / other / 16 | present / absent / other / 16 | PASS |
| D | v2.6.2 "Unexpected reply for DS query with an owner below a delegation point" | v2.6.2 / v2.6.1 | present / absent / other / 6 | present / absent / other / 6 | PASS |
| D | v2.1.0 "kdig: Warning instead of error on TSIG validation failure" | v2.1.0 / v1.6.6 | present / absent / other / 18 | present / absent / other / 18 (also in v2.1.0-rc1, recorded as `news_also_in_prerelease`) | PASS |

No sampled `cds-cdnskey` entry sits on an ECDSA-only line.

### E. Coverage and gaps

| section | row | command | expected | observed | result |
|---|---|---|---|---|---|
| E1 | stable tag count | `git -C $C tag \| grep -E '^v[0-9]+\.[0-9]+(\.[0-9]+)?$' \| grep -v '^v1\.99' \| wc -l` | = stable releases = 174 | 174 tags; JSON 174 `stable: true`; `release_count` 216 = 217 tags - `embedded_lmdb` | PASS |
| E2 | tags absent from releases[] | `git -C $C tag` diffed against `releases[].tag` | none except documented | only `embedded_lmdb` (not a version tag, listed in gaps[0]); no releases[] tag missing from the clone | PASS |
| E3 | gaps[0] embedded_lmdb / duplicate rc tags | `git -C $C rev-parse v1.2-rc1^{commit} v1.2.0-rc1^{commit} v1.2-rc2^{commit} v1.2.0-rc2^{commit}` | same commits | e847c49165 = e847c49165; 1a7f9c519b = 1a7f9c519b | PASS |
| E3 | gaps[1] NEWS 2.3.4 untagged | `git -C $C tag \| grep 2.3.4; git -C $C show v2.5.6:NEWS \| grep -c 'Knot DNS 2.3.4'; git -C $C show v2.5.7:NEWS \| grep -n 'Knot DNS 2.3.4'` | no tag; first at v2.5.7 | no tag; 0 at v2.5.6; line 255 at v2.5.7 | PASS |
| E3 | gaps[2] 2.1.0 / 2.2.0 not in NEWS | section extraction of NEWS@v2.1.0 (2.1.0) and NEWS@v2.2.0 (2.2.0), grep `ecdsa\|algorithm` and `key size\|2048` | absent | absent (only "synth-record ... default configuration options") | PASS |
| E3 | gaps[3] DSA removal / RSA 1024 not in NEWS | section extraction of NEWS@v2.6.0 (2.6.0) grep `dsa`; NEWS@v2.7.0 (2.7.0) grep `1024` | both absent | DSA: absent. RSA 1024: **present** — NEWS 2.7.0 " - Minimum allowed RSA key length was increased to 1024" | FAIL |
| E3 | gaps[4] nsec3-iterations doc 5 vs 10 | `git -C $C show --stat 9a2a2ecf9; git -C $C tag --contains 9a2a2ecf9 \| head -1; git -C $C show v3.0.5:doc/reference.rst \| grep -A4 '^nsec3-iterations' \| grep Default; same for v3.0.6` | doc fix in 3.0.6 | 9a2a2ecf9 "doc: fix default value of policy.nsec3-iterations" (docs only), first tag v3.0.6 by version order (`tag --contains` lists v3.0.10 first alphabetically); v3.0.5 "Default: 5", v3.0.6 "Default: 10" | PASS |
| E3 | gaps[5] CVE-2014-0486 | see C | reason stated | reason stated; commits verified | PASS |
| E3 | gaps[6] CVE-2026-39155 | see C | id absent from NEWS | 0 NEWS hits, 0 commits mention the id | PASS |
| E3 | gaps[7] nine kresd CVEs | see C | absent from NEWS/log | all 0 / 0 | PASS |
| E3 | gaps[8] security fixes without CVE | `git -C $C show v3.5.8:NEWS \| sed -n 1,12p` | entry rows only | 3.5.8 TSIG line present (sampled in D) | PASS |
| E3 | gaps[9]-[13] conventions (0.8 approximate, pre-release sections, parallel lines, news_edits >= 2.0.0, non-DNSSEC defaults) | read | statements of method, not skipped work | consistent with what the data shows | PASS |
| E3 | md support-table row 2.7.4 "Reintroduced 'rollover' ... (approximate: no commit identified between the two tags)" | `git -C $C log --format='%h %cI %s' v2.7.3..v2.7.4 -S'rollover' -- doc/reference.rst; for t in v2.6.1 v2.7.3 v2.7.4; do git -C $C show "${t}:src/knot/conf/schema.c" \| grep -n ROLLOVER; done; git -C $C show v2.7.3:doc/reference.rst \| grep -A12 '^cds-cdnskey-publish'` | not determinable | determinable in one search: `e16da2dc7` "doc: missing option" (2018-11-03, in v2.7.4) adds the `rollover` line to `doc/reference.rst`; the schema value `CHILD_RECORDS_ROLLOVER "rollover"` exists unchanged at v2.6.1, v2.7.3 and v2.7.4 (introduced by 5a242bfc0 in 2.6.1), so the 2.7.4 "reintroduction" was documentation only | FAIL (row should cite e16da2dc7 and say the change is doc-only) |

### Other: md/json agreement, cited commits in the .md tables, news_edits

| section | row | command | expected | observed | result |
|---|---|---|---|---|---|
| md/json | Release list table (216 rows) | script comparing version, tag, date, stable, own entries to `releases[]` | 0 mismatches | 0 mismatches | PASS |
| md/json | Default changes table (21 rows) | script comparing version, date, title, before, after, on-upgrade, opt-in, commits, attribution to `default_changes[]` | 0 mismatches | 0 mismatches | PASS |
| md/json | CVE table (13 rows) | script comparing CVE, NVD date, fix tag, fix date, latency, DNSSEC flag, commits to `cve_fixes[]` | 0 mismatches | 0 mismatches | PASS |
| md | every commit cited in the "Support added" and "Algorithm support" tables (110 commits, incl. all multi-commit rows) | `git -C $C tag --contains <sha> \| grep -x v<version>` for each | all hit | 110/110 hit | PASS |
| news_edits | 2.5.2 (CVE id added later) | `git -C $C show v2.5.2:NEWS \| grep -n 'TSIG validity'; git -C $C show v3.6.0:NEWS \| grep -n 'TSIG validity'` | line lacks CVE id at v2.5.2, has it at v3.6.0 | v2.5.2:6 without id; v3.6.0:2980 with id | PASS |
| news_edits | 2.0.1 "quering" -> "querying" | `git -C $C show v2.0.1:NEWS \| grep -n quering; git -C $C show v3.6.0:NEWS \| grep -n 'CNAME following when'` | typo fixed later | v2.0.1:12 "quering"; v3.6.0:3372 "querying" | PASS |
| news_edits | 3.3.5 alpn line added later | `git -C $C show v3.3.5:NEWS \| grep -c alpn; git -C $C show v3.6.0:NEWS \| grep -n 'incorrect alpn'` | absent at v3.3.5, present at v3.6.0 | 0; present (lines 881 and 1081) | PASS |
| news_edits | 2.5.7 "removed 6" | section extraction of "Knot DNS 2.5.7" and "Knot DNS 2.3.4" from NEWS@v2.5.7 and NEWS@v3.6.0 | the 2.5.7 section lost six lines by v3.6.0 | 2.5.7 section: 5 entries at both tags, identical; 2.3.4 section: 6 entries at both tags, identical. The "removed" lines are the untagged 2.3.4 section that the builder folded into 2.5.7 and then diffed against the real 2.5.7 section | FAIL (builder artefact) |

## Corrections required

1. **`cve_fixes[CVE-2026-39155].fix_tag`** (and the md CVE table "fix tag" column): wrong `v3.4.10`, right `v3.5.4`. Proof: `git -C $C tag --contains 15647ab26d | grep -x v3.4.10` (no output) and `git -C $C log -1 --format=%cI v3.5.4^{commit}` = `2026-04-02T07:07:28+02:00` vs `git -C $C log -1 --format=%cI v3.4.10^{commit}` = `2026-04-02T07:21:06+02:00`. Restructure so that `fix_commits[]` under `fix_tag` contains only `15647ab26d` (first_tag v3.5.4) and `605b3d1700` is recorded as the 3.4-line sibling (v3.4.10, +14 min), matching how CVE-2016-6171 and CVE-2017-11104 already handle their LTS siblings in `note`. `fix_released` (2026-04-02) and `latency_days` (-112) stay.
2. **`default_changes[3.2.0 rrsig-refresh].commits`**: missing `d8b1e148f785392e7119654e24c381602dce263d` ("dnssec: enforce safe rrsig-refresh", 2021-12-15T13:02:36+01:00, first_tag v3.2.0). The `after` clause "configuration fails to load if rrsig-refresh is too low" is not in 084c8ab842. Proof: `git -C $C show d8b1e148f -- src/knot/dnssec/zone-events.c` (`log_zone_error(...); result = KNOT_EINVAL; goto done;`) and `git -C $C tag --contains d8b1e148f | grep -x v3.2.0`. Also fix the wording: the check runs in `knot_dnssec_zone_sign`, so the effect is "zone signing fails with an error", not "configuration fails to load" (NEWS overstates it). The md support-table row "server fails to load configuration if 'policy.rrsig-refresh' is too low | 084c8ab842" needs the same commit.
3. **`default_changes[3.4.0 validation].commits`**: add `ce1e335c954bcc5c2b7cf52cedffe09869c68dba` ("dnssec/validation: consider end of RRSIG validitiy...", 2023-12-21T11:59:30+01:00, first_tag v3.4.0); it, not a7a739faab, implements the `after` value. Proof: `git -C $C show ce1e335c9 -- src/knot/dnssec/zone-sign.c | grep -n rrsig_refresh_before` vs `git -C $C show a7a739faab | grep -c rrsig_refresh` (0). Keep a7a739faab for the re-validation event.
4. **`default_changes[2.7.0 RSA min].documentation`** and **`gaps[3]`**: wrong "not in NEWS"; right: NEWS 2.7.0 " - Minimum allowed RSA key length was increased to 1024". Proof: `git -C $C show v2.7.0:NEWS | sed -n 1,50p | grep -n 1024`. The DSA half of gaps[3] stands. The 2.7.0 line is also a kept-entry candidate (`alg-rsa-sha2`, limit-changed) that the entry extraction missed.
5. **`default_changes[2.2.0 key size].documentation`**: wrong `doc/man_keymgr.rst@v2.2.0:243 "The default key size is determined optimally based on the algorithm"` (that sentence belongs to `tsig generate`); right: cite the code (`3d5626ab17` removes `"Key size has to be specified."` in `src/dnssec/utils/keymgr.c`; `git -C $C show v2.2.0:src/dnssec/lib/kasp/policy.c | grep -n key_size_default` lines 74-75) and note that `man_keymgr.rst@v2.2.0` does not document the zone-key default size. Proof: `git -C $C show v2.2.0:doc/man_keymgr.rst | sed -n 241,244p`.
6. **`news_edits[version=2.5.7]`** (and the md "Post-hoc NEWS edits" bullet "2.5.7 ... removed 6"): wrong "removed: [6 lines]"; right: no edit — the 2.5.7 section is byte-identical at v2.5.7 and v3.6.0 and so is the 2.3.4 section. Proof: `diff <(git -C $C show v2.5.7:NEWS | sed -n '/^Knot DNS 2.5.7 /,/^Knot DNS 2.3.4 /p') <(git -C $C show v3.6.0:NEWS | sed -n '/^Knot DNS 2.5.7 /,/^Knot DNS 2.3.4 /p')` (empty). Drop the entry, or diff the 2.3.4 pseudo-section separately.
7. **md support table row 2.7.4 "Reintroduced 'rollover' configuration option for CDS/CDNSKEY publication"** (and its JSON entry under v2.9.x-era `releases[v2.7.4].changelog_entries`): wrong "(approximate: no commit identified between the two tags)"; right: commit `e16da2dc7` ("doc: missing option", 2018-11-03T10:04:34+01:00, in v2.7.4), documentation-only — the `rollover` value has been in `src/knot/conf/schema.c` since 5a242bfc0 (v2.6.1). Proof: `git -C $C log --format='%h %cI %s' v2.7.3..v2.7.4 -S'rollover' -- doc/reference.rst` and `git -C $C show v2.7.3:src/knot/conf/schema.c | grep -n ROLLOVER`.

## Not verifiable

- NVD publication dates were taken from `cve_inventory.json` as given; no network re-fetch was done, so `nvd_published` is verified only against the inventory, not against NVD.
- CVE-2014-0486: the NVD reference `gitlab.labs.nic.cz/knot/knot-dns/issues/294` is not in the clone; the commit attribution remains "approximate" as the row says. The five commits are the only `rrset-wire` bounds-check work between v1.5.1 and v1.5.2, which is consistent with the NEWS line.
- The 0.8 "DNSSEC"/"NSEC3" support rows (commits from 2010, before the first tag) were not re-derived; they are entry rows with `attribution approximate` and outside sections B-C.
- `algorithm_support` rows and the "Documented policy defaults over time" table were only checked for commit-in-tag (110/110) and for the specific values that overlap with `default_changes`; their remaining cells were not independently re-derived.

## Totals

| section | checks run | passed | failed |
|---|---|---|---|
| A. Release dates | 25 (23 tag dates incl. first/last, 1 full sweep, 1 stable-flag rule) | 25 | 0 |
| B. Default changes | 126 (21 rows x stat / contains / earliest / before-after / flags / attribution, commit-level where multi-commit) | 122 | 4 (2.2.0 doc pointer, 2.7.0 "not in NEWS", 3.2.0 missing commit, 3.4.0 wrong commit) |
| C. CVE fixes | 34 (4 applicable rows x inventory / contains / earliest / latency = 16; 9 non-applicable rows x inventory / justification = 18) | 32 | 2 (CVE-2026-39155 contains, earliest) |
| D. Changelog entries | 80 (20 entries x present / absent-at-prev / mechanism / count) | 80 | 0 |
| E. Coverage and gaps | 15 (2 counts, 12 gap probes, 1 "no commit identified" row) | 13 | 2 (gaps[3] RSA-1024, 2.7.4 row) |
| Other (md/json twin, md-cited commits, news_edits) | 117 (3 table compares, 110 commit containments, 4 news_edits) | 116 | 1 (news_edits 2.5.7) |
| **Total** | **397** | **388** | **9** |
