# Phase 3 verification: kresd (Knot Resolver)

**Verdict: PASS WITH CORRECTIONS.** Every release date, every default-change commit, every CVE fix commit and every sampled changelog entry reproduces from the clone; the failures are five `stable` flags that contradict the brief's tag-pattern rule (with a documented, clone-backed reason), one documentation-only commit cited as product evidence, a stale macro name in two `after` texts, one factually wrong note about a commit being "absent from this clone", and one inconsistent `mechanism` on a duplicated NEWS line.

Inputs: `data/software/timelines/kresd.json`, `data/software/timelines/kresd.md`, clone `out/software_repos/kresd.git` (bare, blob-less). All commands below were run from the repo root with `C=out/software_repos/kresd.git`. Verified 2026-09-29.

Sampling: Python `random.seed(20260929)`; `random.sample(range(98), 20)` over `releases[]` in file order for section A (indices `[1, 8, 18, 30, 37, 39, 46, 48, 54, 55, 58, 59, 61, 64, 66, 74, 75, 76, 85, 94]`), and `random.sample(range(136), 20)` over the flattened list of kept `changelog_entries` for section D (indices `[2, 14, 17, 33, 37, 60, 74, 79, 93, 97, 108, 111, 113, 114, 117, 118, 123, 128, 129, 132]`, covering 17 releases). Sections B, C and E were checked in full, no sampling.

Conventions: `stable by pattern` means no `rc|beta|alpha|dev|a<digit>` in the tag. "Earliest stable tag" is computed as the earliest-dated tag (by `<tag>^{commit}` committer date) among `git tag --contains <sha>` after dropping pre-release tags; both the 5.7.x and 6.0.x lines are in that set.

## Check table

### A. Release dates (20 sampled + first + last, then a full sweep)

Command per row: `git -C $C log -1 --format=%cI <tag>^{commit}`. Expected = `released_full` in the JSON; `stable` expected = tag has no pre-release suffix.

| section | row | command | expected | observed | result |
|---|---|---|---|---|---|
| A | v1.0.0-beta2 | `git -C $C log -1 --format=%cI v1.0.0-beta2^{commit}` | 2015-11-20T11:19:32+01:00, stable=false | 2015-11-20T11:19:32+01:00, pre-release suffix | PASS |
| A | v1.2.0-rc3 | `git -C $C log -1 --format=%cI v1.2.0-rc3^{commit}` | 2017-01-24T10:21:24+01:00, stable=false | identical; rc suffix | PASS |
| A | v1.3.1 | `git -C $C log -1 --format=%cI v1.3.1^{commit}` | 2017-06-23T14:10:44+02:00, stable=true | identical | PASS |
| A | v2.2.0 | `git -C $C log -1 --format=%cI v2.2.0^{commit}` | 2018-03-28T13:33:39+02:00, stable=true | identical | PASS |
| A | v3.2.1 | `git -C $C log -1 --format=%cI v3.2.1^{commit}` | 2019-01-10T11:40:47Z, stable=true | identical | PASS |
| A | v4.1.0 | `git -C $C log -1 --format=%cI v4.1.0^{commit}` | 2019-07-10T14:06:44Z, stable=true | identical | PASS |
| A | v5.1.0 | `git -C $C log -1 --format=%cI v5.1.0^{commit}` | 2020-04-29T13:04:26+02:00, stable=true | identical | PASS |
| A | v5.1.2 | `git -C $C log -1 --format=%cI v5.1.2^{commit}` | 2020-07-01T14:26:03+02:00, stable=true | identical | PASS |
| A | v5.3.2 | `git -C $C log -1 --format=%cI v5.3.2^{commit}` | 2021-05-05T09:23:24Z, stable=true | identical | PASS |
| A | v5.4.0 | `git -C $C log -1 --format=%cI v5.4.0^{commit}` | 2021-07-29T14:25:42Z, stable=true | identical | PASS |
| A | v5.4.3 | `git -C $C log -1 --format=%cI v5.4.3^{commit}` | 2021-12-01T12:52:38+01:00, stable=true | identical | PASS |
| A | v5.4.4 | `git -C $C log -1 --format=%cI v5.4.4^{commit}` | 2022-01-05T14:04:10+01:00, stable=true | identical | PASS |
| A | v5.5.1 | `git -C $C log -1 --format=%cI v5.5.1^{commit}` | 2022-06-14T09:13:12+02:00, stable=true | identical | PASS |
| A | v5.6.0 | `git -C $C log -1 --format=%cI v5.6.0^{commit}` | 2023-01-26T18:01:18+01:00, stable=true | identical | PASS |
| A | v5.7.1 | `git -C $C log -1 --format=%cI v5.7.1^{commit}` | 2024-02-13T13:03:08+01:00, stable=true | identical | PASS |
| A | v6.0.0a1 | `git -C $C log -1 --format=%cI v6.0.0a1^{commit}` | 2023-05-22T14:35:37+02:00, stable=false | identical; `a1` suffix | PASS |
| A | v6.0.1 | `git -C $C log -1 --format=%cI v6.0.1^{commit}` | 2023-06-23T12:11:55+02:00; stable by pattern = **true** | date identical; JSON `stable: false` (`stability_note`: "NEWS header at this tag marks 6.0.x as alpha/early access"; `git -C $C show v6.0.1:NEWS \| head -8` does say "6.0.x versions are dedicated to alpha cycle") | FAIL (rule) |
| A | v6.0.2 | `git -C $C log -1 --format=%cI v6.0.2^{commit}` | 2023-08-30T17:02:38+02:00; stable by pattern = **true** | date identical; JSON `stable: false`, same note | FAIL (rule) |
| A | v6.0.11 | `git -C $C log -1 --format=%cI v6.0.11^{commit}` | 2025-02-26T12:54:55+01:00, stable=true | identical | PASS |
| A | v6.3.0 | `git -C $C log -1 --format=%cI v6.3.0^{commit}` | 2026-04-27T14:00:42+02:00, stable=true | identical | PASS |
| A | v1.0.0-beta1 (first) | `git -C $C log -1 --format=%cI v1.0.0-beta1^{commit}` | 2015-10-08T15:00:22+02:00, stable=false | identical | PASS |
| A | v6.4.2 (last) | `git -C $C log -1 --format=%cI v6.4.2^{commit}` | 2026-08-05T11:40:54+02:00, stable=true | identical | PASS |
| A | all 98 tags (sweep) | `for t in $(git -C $C tag); do git -C $C log -1 --format="$t %cI %H" $t^{commit}; done` vs `released_full`/`commit` | 0 mismatches | 0 date mismatches, 0 commit-sha mismatches | PASS |
| A | tag-object date trap | `git -C $C for-each-ref --format='%(refname:short) %(objecttype) %(taggerdate:short)' refs/tags` | no migration-day cluster | largest tagger-date cluster is 2 tags; no cluster | PASS |

### B. Default changes (all 18 rows, all 38 commit instances)

B.1/B.2 per commit: `git -C $C show --stat <sha>` and `git -C $C tag --contains <sha> | grep -x <tag>`. B.3 per row: `git -C $C log --all -i --grep='<words>' --format='%h %cs %s'` then earliest stable tag across all hits. B.4 per row: the diff or `git -C $C show <tag>:<path>`.

| section | row | command | expected | observed | result |
|---|---|---|---|---|---|
| B.1/2 | 1.3.0 / 651c5aad | `git -C $C show --stat 651c5aad; git -C $C tag --contains 651c5aad \| grep -x v1.3.0` | product code; v1.3.0 hit | lib/layer/{iterate,validate}.c, lib/nsrep.*, lib/resolve.c, lib/rplan.h, modules/policy/policy.lua, daemon/lua/kres-gen.lua; hit | PASS |
| B.1/2 | 1.3.0 / 8ae906e0 | same, sha 8ae906e0 | product code; hit | merge !303, 22 files incl. lib/dnssec*.c, lib/layer/*.c; hit | PASS |
| B.3 | 1.3.0 forwarding w/ validation | `git -C $C log --all -i --grep='forwarding with validation'`, `--grep='full forwarding'` | v1.3.0 earliest | only 8ae906e0 and 651c5aad; earliest stable v1.3.0 | PASS |
| B.4 | 1.3.0 before/after | `git -C $C show v1.2.0:NEWS \| grep "doesn't do DNSSEC validation yet"`; `git -C $C show 651c5aad -- modules/policy/policy.lua` | before text in NEWS 1.2.0; STUB introduced as non-validating mode | NEWS 1.2.0:7 matches; diff adds `STUB = stub` and re-labels old FORWARD asserts as STUB | PASS |
| B.5/6 | 1.3.0 flags | — | on-upgrade yes / opt-in no / exact | policy.FORWARD semantics change for existing configs; attribution exact | PASS |
| B.1/2 | 1.5.0 / ac23d8d0 | `git -C $C show --stat ac23d8d0; git -C $C tag --contains ac23d8d0 \| grep -x v1.5.0` | product code; hit | daemon/lua/sandbox.lua (+`modules.load('ta_signal_query')`), module README, tests/deckard; hit | PASS |
| B.1/2 | 1.5.0 / 35a8a64c | same, sha 35a8a64c | product code; hit | modules/ta_signal_query/*.lua, modules.mk, kres.lua.in, NEWS, doc; hit | PASS |
| B.3 | 1.5.0 ta_signal_query | `git -C $C log --all -i --grep='ta_signal_query'`, `--grep='Signaling Trust Anchor'` | v1.5.0 earliest | all other hits are later (v2.4.0, v4.0.0, v4.3.0); earliest v1.5.0 | PASS |
| B.4 | 1.5.0 before/after | `git -C $C show ac23d8d0 -- daemon/lua/sandbox.lua`; `git -C $C show v1.5.0:NEWS \| grep -A1 ta_signal_query` | module loaded by default; NEWS "enabled by default" | diff adds default load; NEWS 1.5.0:10-11 "it is enabled by default" | PASS |
| B.5/6 | 1.5.0 flags | — | yes / no / exact | consistent with diff | PASS |
| B.1/2 | 2.0.0 aggr / 997242e0 | `git -C $C show --stat 997242e0; git -C $C tag --contains 997242e0 \| grep -x v2.0.0` | product code; hit | merge !422, 50 files, lib/cache/* rewrite; hit | PASS |
| B.1/2 | 2.0.0 aggr / 762ab966 | same, sha 762ab966 | product code; hit | lib/cache/{api,entry_list,entry_pkt,nsec1}.c, impl.h; hit | PASS |
| B.3 | 2.0.0 aggressive NSEC | `git -C $C log --all -i --grep='aggressive'` (24 hits) | v2.0.0 earliest for NSEC synthesis | all hits with an earlier tag are unrelated (none before 2018-01); earliest v2.0.0 | PASS |
| B.4 | 2.0.0 aggr before/after | `git -C $C log -1 --format=%B 997242e0`; `git -C $C grep -n -i aggressive v2.4.0 -- '*.rst'` | on by default, no knob | merge message "It's not for NSEC3"; v2.4.0 modules/rfc7706.rst: "enabled automatically together with DNSSEC validation"; no knob found in v2.0.0 docs/lua | PASS |
| B.5/6 | 2.0.0 aggr flags | — | yes / no / exact | consistent | PASS |
| B.1/2 | 2.0.0 sentinel / 777a680a | `git -C $C show --stat 777a680a; git -C $C tag --contains 777a680a \| grep -x v2.0.0` | product code; hit | daemon/lua/sandbox.lua (+`modules.load('ta_sentinel')`), modules/ta_sentinel/*; hit | PASS |
| B.3 | 2.0.0 ta_sentinel | `git -C $C log --all -i --grep='ta_sentinel'`, `--grep='kskroll-sentinel'` | v2.0.0 earliest | earliest hit 777a680a / merge 1b36d2d4 -> v2.0.0; rest v2.1.0+ | PASS |
| B.4 | 2.0.0 sentinel before/after | `git -C $C show v2.0.0:NEWS \| grep -A1 'ta_sentinel module implements'` | NEWS says enabled by default | NEWS 2.0.0:28-29 "...kskroll-sentinel-00, / enabled by default" (line-wrapped; JSON `documentation` joins the two lines) | PASS |
| B.5/6 | 2.0.0 sentinel flags | — | yes / no / exact | consistent | PASS |
| B.1/2 | 2.0.0 keyfile / 6c2db2b5 | `git -C $C show --stat 6c2db2b5; git -C $C tag --contains 6c2db2b5 \| grep -x v2.0.0` | product code; hit | config.mk, daemon/main.c, daemon/engine.[ch], daemon/lua/trust_anchors.lua.in, config.lua, docs; hit | PASS |
| B.3 | 2.0.0 keyfile | `git -C $C log --all -i --grep='keyfile-ro'`, `--grep='KEYFILE_DEFAULT'` | v2.0.0 earliest | earliest is 6c2db2b5 -> v2.0.0; other hits v2.2.0+ | PASS |
| B.4 | 2.0.0 keyfile before/after | `git -C $C show 6c2db2b5 \| grep -E '^\+.*(writ\|keyfile-ro\|unmanaged)'`; `git -C $C show v2.0.0:config.mk \| grep KEYFILE_DEFAULT` | -K added; write access required for managed; KEYFILE_DEFAULT empty | `-K, --keyfile-ro` added; `error("[ ta ] ERROR: write access needed to keyfile dir ...")`; config.mk:26 `KEYFILE_DEFAULT ?=` | PASS |
| B.5/6 | 2.0.0 keyfile flags | — | yes / no / exact | -k behaviour changes on upgrade | PASS |
| B.1/2 | 2.4.0 / e2d5bd39 | `git -C $C show --stat e2d5bd39; git -C $C tag --contains e2d5bd39 \| grep -x v2.4.0` | product code; hit | merge !600, lib/cache/nsec3.c (new), api.c, peek.c, contrib/base32hex.*; hit | PASS |
| B.1/2 | 2.4.0 / 17dae8a1 | `git -C $C show --stat 17dae8a1` | product code | **NEWS only** (1 file). Not product evidence. Row survives on e2d5bd39. | FAIL |
| B.3 | 2.4.0 NSEC3 aggressive | `git -C $C log --all -i --grep='NSEC3 aggressive'`, `--grep='aggressive NSEC3'` | v2.4.0 earliest | e2d5bd39/17dae8a1 -> v2.4.0; 2ffa6c10 fixes -> v2.4.1; earliest v2.4.0 | PASS |
| B.4 | 2.4.0 before/after | `git -C $C grep -n -i 'opt.?out' v2.4.0 -- lib/cache`; `git -C $C show v2.4.0:NEWS \| grep -n aggressive` | NSEC3 synthesis, opt-out excluded, on by default | lib/cache/api.c:212 `ok = ok && (eh->is_packet \|\| !eh->has_optout)`; NEWS 2.4.0:17; rfc7706.rst "enabled automatically" | PASS |
| B.5/6 | 2.4.0 flags | — | yes / no / exact | consistent | PASS |
| B.1/2 | 4.0.0 default / 8abc490f | `git -C $C show --stat 8abc490f; git -C $C tag --contains 8abc490f \| grep -x v4.0.0` | product code; hit | daemon/lua/trust_anchors.lua.in, config.lua, sandbox.lua.in, etc/config/*.in, docs, tests; hit | PASS |
| B.1/2 | 4.0.0 default / 4b3ac5d7 | same, sha 4b3ac5d7 | product code; hit | meson.build, meson_options.txt, daemon/lua/trust_anchors.lua.in, docs, tests; hit | PASS |
| B.1/2 | 4.0.0 default / 92fced62 | same, sha 92fced62 | product code; hit | daemon/lua/trust_anchors.lua.in; hit | PASS |
| B.1/2 | 4.0.0 default / 1405517d | same, sha 1405517d | product code; hit | daemon/main.c (+tests, doc); hit | PASS |
| B.3 | 4.0.0 validation default | `git -C $C log --all -i --grep='keyfile_default'`, `--grep='remove -k'` | v4.0.0 earliest | 9f603486 (2018-12, v3.2.0) is a doc mention only; all code hits -> v4.0.0 | PASS |
| B.4 | 4.0.0 default before/after | `git -C $C show v3.2.1:config.mk \| grep -n KEYFILE_DEFAULT`; `git -C $C show v4.0.0:meson_options.txt \| grep -A3 keyfile_default`; `git -C $C show v4.0.0:daemon/README.rst \| grep -n 'enabled by default'`; `git -C $C show v4.0.0:daemon/main.c \| grep keyfile` | before: empty default; after: root.keys, -k/-K gone, doc line 388 | config.mk:26 `KEYFILE_DEFAULT ?=`; meson_options.txt:3-5 `keyfile_default ... value: 'root.keys'`; README.rst:388 exact; no `keyfile` in v4.0.0 main.c | PASS |
| B.5/6 | 4.0.0 default flags | — | yes / no / exact | consistent | PASS |
| B.1/2 | 4.0.0 DO / bfc8511b | `git -C $C show --stat bfc8511b; git -C $C tag --contains bfc8511b \| grep -x v4.0.0` | product code; hit | lib/resolve.c, NEWS; hit | PASS |
| B.3 | 4.0.0 DO bit | `git -C $C log --all -i --grep='always send DO'`, `--grep='DO bit'` | v4.0.0 earliest | bfc8511b / merge 37510f73 -> v4.0.0; d1b84a1e (2015) is a test fix | PASS |
| B.4 | 4.0.0 DO before/after | `git -C $C show bfc8511b -- lib/resolve.c` | DO previously conditional on DNSSEC_WANT; now unconditional | diff removes `else if (qry->flags.DNSSEC_WANT)` branch; DO+CD set in the unconditional `else` | PASS |
| B.5/6 | 4.0.0 DO flags | — | yes / no / exact | consistent | PASS |
| B.1/2 | 4.1.0 / f1be61dd | `git -C $C show --stat f1be61dd; git -C $C tag --contains f1be61dd \| grep -x v4.1.0` | product code; hit | lib/cache/{api,entry_pkt,peek}.c, impl.h, NEWS; hit | PASS |
| B.3 | 4.1.0 minimal ranges | `git -C $C log --all -i --grep='minimal NSEC'` | v4.1.0 earliest | f1be61dd, merge e4b7f259, test f402b3d3, all -> v4.1.0 | PASS |
| B.4 | 4.1.0 before/after | `git -C $C show f1be61dd -- lib/cache/entry_pkt.c lib/cache/peek.c` | minimal ranges excluded from synthesis | diff adds `needs_pkt`/`want_negative` gating in entry_pkt.c and peek.c | PASS |
| B.5/6 | 4.1.0 flags | — | yes / no / exact | consistent | PASS |
| B.1/2 | 5.3.1 / 7107faeb | `git -C $C show --stat 7107faeb; git -C $C tag --contains 7107faeb \| grep -x v5.3.1` | product code; hit | lib/dnssec/nsec3.h, lib/layer/validate.c, NEWS; hit | PASS |
| B.1/2 | 5.3.1 / 5922eecd | same, sha 5922eecd | product code; hit | lib/cache/api.c; hit | PASS |
| B.1/2 | 5.3.1 / 21e50fca | same, sha 21e50fca | product code; hit | lib/cache/nsec3.c, lib/dnssec/nsec3.c; hit | PASS |
| B.3 | 5.3.1 NSEC3 iterations | `git -C $C log --all -i --grep='NSEC3 iterations'`, `--grep='high NSEC3'`, `--grep='NSEC3 limit'` | v5.3.1 earliest | 7107faeb, 21e50fca -> v5.3.1; other hits 2024+ | PASS |
| B.4 | 5.3.1 before/after | `git -C $C show v5.3.0:lib/dnssec/nsec3.h \| grep KR_NSEC3_MAX_ITERATIONS`; `git -C $C show v5.3.1:lib/dnssec/nsec3.h \| grep -n KR_NSEC3_MAX_ITERATIONS` | absent at v5.3.0; `150` at v5.3.1:19 | absent; `19:#define KR_NSEC3_MAX_ITERATIONS 150` | PASS |
| B.5/6 | 5.3.1 flags | — | yes / no / exact | consistent | PASS |
| B.1/2 | 5.5.0 / d4e95821 | `git -C $C show --stat d4e95821; git -C $C tag --contains d4e95821 \| grep -x v5.5.0` | product code; hit | lib/dnssec/signature.c, NEWS; hit | PASS |
| B.3 | 5.5.0 SHA-1 DS | `git -C $C log --all -i --grep='SHA1 DS'`, `--grep='ignore SHA1'` | v5.5.0 earliest | d4e95821 + merge 741502f4 (!1251) -> v5.5.0 | PASS |
| B.4 | 5.5.0 before/after | `git -C $C show d4e95821 -- lib/dnssec/signature.c` | skip SHA-1 if a supported stronger digest is present | diff adds `skip_sha1` loop: `algo != DNSSEC_KEY_DIGEST_SHA1 && dnssec_algorithm_digest_support(algo)` | PASS |
| B.5/6 | 5.5.0 flags | — | yes / no / exact | consistent | PASS |
| B.1/2 | 5.6.0 / 24e912e0 | `git -C $C show --stat 24e912e0; git -C $C tag --contains 24e912e0 \| grep -x v5.6.0` | product code; hit | lib/cache/peek.c, modules/policy/README.rst, NEWS; hit | PASS |
| B.1/2 | 5.6.0 / fab10d1e | same, sha fab10d1e | product code; hit | lib/resolve.c, NEWS; hit | PASS |
| B.3 | 5.6.0 policy.STUB | `git -C $C log --all -i --grep='policy.STUB'` | v5.6.0 earliest for these changes | earlier hits (v1.3.2, v5.3.1, v5.3.2) are unrelated STUB docs/TCP; these two -> v5.6.0 (v6.0.1 also contains them, non-stable) | PASS |
| B.4 | 5.6.0 before/after | `git -C $C show 24e912e0 -- lib/cache/peek.c; git -C $C show fab10d1e -- lib/resolve.c` | STUB skips synthesis; DO no longer copied | `if (qry->flags.STUB) return ctx->state;` added; `knot_edns_set_do` under `knot_pkt_has_dnssec(request->qsource.packet)` removed | PASS |
| B.5/6 | 5.6.0 flags | — | yes / no / exact | consistent | PASS |
| B.1/2 | 5.7.1 NSEC3 / e966b7fd | `git -C $C show --stat e966b7fd; git -C $C tag --contains e966b7fd \| grep -x v5.7.1` | product code; hit | lib/dnssec/nsec3.h; hit | PASS |
| B.1/2 | 5.7.1 NSEC3 / eccb8e27 | same, sha eccb8e27 | product code; hit | lib/cache/{api,nsec3}.c, lib/dnssec/nsec3.[ch], lib/layer/validate.c; hit | PASS |
| B.1/2 | 5.7.1 NSEC3 / b5051ac2 | same, sha b5051ac2 | product code; hit | lib/cache/nsec3.c, lib/dnssec/nsec3.h; hit | PASS |
| B.1/2 | 5.7.1 NSEC3 / 24699e9f | same, sha 24699e9f | product code; hit | lib/dnssec/nsec3.c; hit | PASS |
| B.1/2 | 5.7.1 NSEC3 / a05cf1d3 | same, sha a05cf1d3 | product code; hit | lib/layer/validate.c; hit | PASS |
| B.3 | 5.7.1 NSEC3 limits | `git -C $C log --all -i --grep='iteration limit'`, `--grep='NSEC3 salt'`, `--grep='8 NSEC3'` | v5.7.1 earliest across 5.7.x/6.0.x | siblings 5a840a06/5efa4053 (2024-02-10), e260bb65/5f31b64a/2775442e/96525e9a/4146cd01 (2024-02-22) are in **no** tag; v5.7.1 (13:03+01) precedes v6.0.6 (14:17+01) same day; v5.7.1 is an ancestor of v6.0.6 (`git -C $C merge-base --is-ancestor v5.7.1 v6.0.6` -> yes) | PASS |
| B.4 | 5.7.1 NSEC3 before/after | `git -C $C show v5.7.0:lib/dnssec/nsec3.h \| grep KR_NSEC3_MAX_ITERATIONS`; `git -C $C show v5.7.1:lib/dnssec/nsec3.h \| grep -n -i -E 'ITERATIONS\|price'`; `git -C $C show a05cf1d3 -- lib/layer/validate.c \| grep 'count > 8'` | before 150; after "KR_NSEC3_MAX_ITERATIONS 50 with kr_nsec3_price" | before OK (v5.7.0:19 = 150). After: **`KR_NSEC3_MAX_ITERATIONS` does not exist at v5.7.1**; it is `kr_nsec3_limited()` with local `const int MAX_ITERATIONS = 50` compared to `kr_nsec3_price(iterations, salt_len)` (nsec3.h:12-30), plus a `128 / kr_nsec3_price(...)` budget (line 50). `count > 8` -> bogus confirmed. Substance right, symbol name wrong. | FAIL |
| B.5/6 | 5.7.1 NSEC3 flags | — | yes / no / exact | consistent | PASS |
| B.1/2 | 5.7.1 KeyTrap / cc5051b4 | `git -C $C show --stat cc5051b4; git -C $C tag --contains cc5051b4 \| grep -x v5.7.1` | product code; hit | lib/dnssec.c, lib/layer/validate.c, lib/resolve.c; hit | PASS |
| B.1/2 | 5.7.1 KeyTrap / feb65eb9 | same, sha feb65eb9 | product code; hit | daemon/engine.c, lib/defines.h, lib/dnssec.[ch], lib/layer/validate.c, lib/resolve.h, lib/rplan.h, kres-gen-*.lua; hit | PASS |
| B.3 | 5.7.1 KeyTrap | `git -C $C log --all -i --grep='KeyTrap'` (15 hits) | v5.7.1 earliest | merge 867b5f28 + these two -> v5.7.1; 2024-02-22/23 siblings untagged or v5.7.2 | PASS |
| B.4 | 5.7.1 KeyTrap before/after | `git -C $C show cc5051b4 \| grep -E '^\+.*(vld_limit_crypto\|E2BIG)'` | budget field, E2BIG failure | `qry->vld_limit_crypto_remains <= 0`, `vctx->result = kr_error(E2BIG)` present | PASS |
| B.5/6 | 5.7.1 KeyTrap flags | — | yes / no / exact | consistent | PASS |
| B.1/2 | 5.7.4 / 62b3b1e9 | `git -C $C show --stat 62b3b1e9; git -C $C tag --contains 62b3b1e9 \| grep -x v5.7.4` | shipped config; hit | etc/root.keys, NEWS; hit | PASS |
| B.3 | 5.7.4 KSK-2024 | `git -C $C log --all -i --grep='KSK-2024'` | v5.7.4 earliest | 62b3b1e9 + merge 33ec018e -> v5.7.4 (19:39:18+02) precedes v6.0.8 (19:39:45+02); v5.7.4 is not an ancestor of v6.0.8, so 6.0.8 carries the same sha by cherry-pick/merge | PASS |
| B.4 | 5.7.4 before/after | `git -C $C show v5.7.3:etc/root.keys; git -C $C show v5.7.4:etc/root.keys` | 20326 only -> 20326 + 38696 | exactly that | PASS |
| B.5/6 | 5.7.4 flags | — | on-upgrade **no**, with reason | `attribution_reason` explains RFC 5011-managed file; consistent with `trust_anchors` behaviour | PASS |
| B.1/2 | 6.0.6 NSEC3 / e966b7fd, eccb8e27, b5051ac2, 24699e9f, a05cf1d3 | `git -C $C tag --contains <sha> \| grep -x v6.0.6` (x5) | hits | all five hit; same files as the 5.7.1 rows | PASS |
| B.3 | 6.0.6 NSEC3 limits | as 5.7.1 | earliest stable tag containing | earliest is **v5.7.1**, not v6.0.6; row is explicitly a parallel-line duplicate (`note: same commits as 5.7.1; 6.x line`) and the 5.7.1 row carries the first appearance | PASS (documented duplicate) |
| B.4 | 6.0.6 NSEC3 before/after | as 5.7.1 | — | same stale `KR_NSEC3_MAX_ITERATIONS 50` text (references nsec3.h@v5.7.1) | FAIL |
| B.5/6 | 6.0.6 NSEC3 flags | — | yes / no / exact | consistent | PASS |
| B.1/2 | 6.0.6 KeyTrap / cc5051b4, feb65eb9 | `git -C $C tag --contains <sha> \| grep -x v6.0.6` (x2) | hits | both hit | PASS |
| B.3 | 6.0.6 KeyTrap | as 5.7.1 | earliest | earliest is v5.7.1; documented duplicate | PASS (documented duplicate) |
| B.4 | 6.0.6 KeyTrap before/after | as 5.7.1 | — | same diff | PASS |
| B.5/6 | 6.0.6 KeyTrap flags | — | yes / no / exact | consistent | PASS |
| B.1/2 | 6.0.8 / 62b3b1e9 | `git -C $C tag --contains 62b3b1e9 \| grep -x v6.0.8` | hit | hit | PASS |
| B.3 | 6.0.8 KSK-2024 | as 5.7.4 | earliest | earliest is v5.7.4 (27 s earlier); documented duplicate | PASS (documented duplicate) |
| B.4 | 6.0.8 before/after | `git -C $C show v6.0.7:etc/root.keys` | 20326 only before | (same file lineage) | PASS |
| B.5/6 | 6.0.8 flags | — | no / no / exact + reason | consistent | PASS |
| B | all 38 commit dates + subjects | `git -C $C log -1 --format='%cI %s' <sha>` | equal JSON `commit_date`/`subject` | 38/38 equal | PASS |

### C. CVE fixes (all 16 rows)

C.1: `python3 -c` lookup in `data/software/cve_inventory.json` (`by_product.kresd`, `fixes.kresd`). C.2: `git -C $C tag --contains <sha> | grep -x <fix_tag>` and earliest stable tag across both lines. C.3: `fix_released − nvd_published`.

| section | row | command | expected | observed | result |
|---|---|---|---|---|---|
| C.1 | CVE-2018-1000002 | inventory lookup | by_product=true, fixes=true | true / true (fixes: fix_release 1.5.2) | PASS |
| C.2 | CVE-2018-1000002 / d296e36e, f90d27de | `git -C $C tag --contains d296e36e \| grep -x v1.5.2` (x2) | v1.5.2, earliest | both hit; earliest stable v1.5.2 | PASS |
| C.3 | CVE-2018-1000002 | 2018-01-22 − 2018-01-22 | 0 | 0 | PASS |
| C.1 | CVE-2018-10920 | inventory lookup | true / true | true / true | PASS |
| C.2 | CVE-2018-10920 / d2dd680d, 0d20fe3c | `git -C $C tag --contains <sha> \| grep -x v2.4.1` (x2) | v2.4.1 earliest | both hit; earliest v2.4.1 | PASS |
| C.3 | CVE-2018-10920 | 2018-08-02 − 2018-08-02 | 0 | 0 | PASS |
| C.1 | CVE-2018-1110 | inventory lookup | by_product=false, fixes=true; NVD date from by_product.knot | false / true; by_product.knot published 2021-03-30 = row | PASS |
| C.2 | CVE-2018-1110 / c77bce8a, 8ea37cc3, 96a12caf, 120351ed, fbbec0a1 | `git -C $C tag --contains <sha> \| grep -x v2.3.0` (x5) | v2.3.0 earliest | all hit; earliest v2.3.0; attribution "approximate" with stated reason (private security repo merge !565) | PASS |
| C.3 | CVE-2018-1110 | 2018-04-23 − 2021-03-30 | −1072 | −1072 | PASS |
| C.1 | CVE-2019-10190 | inventory lookup | true / true | true / true | PASS |
| C.2 | CVE-2019-10190 / c5654da7, 625f4882 | `git -C $C tag --contains <sha> \| grep -x v4.1.0` (x2) | v4.1.0 earliest | both hit; earliest v4.1.0; "approximate" with reason (!827) | PASS |
| C.3 | CVE-2019-10190 | 2019-07-10 − 2019-07-16 | −6 | −6 | PASS |
| C.1 | CVE-2019-10191 | inventory lookup | true / true | true / true (inventory sha bef03dcf matches) | PASS |
| C.2 | CVE-2019-10191 / bef03dcf | `git -C $C tag --contains bef03dcf \| grep -x v4.1.0` | v4.1.0 earliest | hit; earliest v4.1.0 | PASS |
| C.3 | CVE-2019-10191 | 2019-07-10 − 2019-07-16 | −6 | −6 | PASS |
| C.1 | CVE-2019-19331 | inventory lookup | false / true; NVD date from by_product.knot | false / true; knot published 2019-12-16 = row | PASS |
| C.2 | CVE-2019-19331 / edb8ffef, 20496036, 4fbd5baf | `git -C $C tag --contains <sha> \| grep -x v4.3.0` (x3) | v4.3.0 earliest | all hit; earliest v4.3.0 | PASS |
| C.3 | CVE-2019-19331 | 2019-12-04 − 2019-12-16 | −12 | −12 | PASS |
| C.1 | CVE-2020-12667 | inventory lookup | true / true | true / true | PASS |
| C.2 | CVE-2020-12667 / ba7b89db, 54f05e4d | `git -C $C tag --contains <sha> \| grep -x v5.1.1` (x2) | v5.1.1 earliest | both hit; earliest v5.1.1 | PASS |
| C.3 | CVE-2020-12667 | 2020-05-19 − 2020-05-19 | 0 | 0 | PASS |
| C.1 | CVE-2021-40083 | inventory lookup | true / true; inventory says fix_release 5.4.2 via NEWS commit c360ef30 | true / true; inventory fixes entry is indeed the NEWS commit c360ef30 "NEWS 5.3.2: add CVE-2021-40083 reference", fix_release 5.4.2 | PASS |
| C.2 | CVE-2021-40083 / 97ec93e1 | `git -C $C tag --contains 97ec93e1 \| grep -x v5.3.2`; `git -C $C log --all -i --grep='!1169'`; `git -C $C merge-base --is-ancestor 97ec93e1 fa42b4ae` | v5.3.2 is the first tag with the code fix | hit; earliest stable **v5.3.2** (then v5.4.0). 97ec93e1 touches lib/dnssec/nsec3.[ch], lib/layer/validate.c, NEWS; NEWS at v5.3.2:6 "validator: fix 5.3.1 regression on over-limit NSEC3 edge case (!1169)" matches NVD ref MR !1169. The CVE id first appears in NEWS at v5.4.2 (`git -C $C show v5.4.2:NEWS \| grep -c 40083` = 1; v5.3.2 and v5.4.1 = 0), via c360ef30 whose first tag is v5.4.2. **The timeline's v5.3.2 is correct; the inventory's 5.4.2 is the NEWS-edit date.** | PASS |
| C.3 | CVE-2021-40083 | 2021-05-05 − 2021-08-25 | −112 | −112 | PASS |
| C.1 | CVE-2022-32983 | inventory lookup | true / false | true / false | PASS |
| C.2 | CVE-2022-32983 / 097339c1 (docs), fix_tag null | `git -C $C show --stat 097339c1`; `git -C $C log --all -i --grep=32983`; `git -C $C cat-file -t ccb9d9794db5eb757c33becf65cb1cf48ecfd968`; `git -C $C tag --contains ccb9d979`; `git -C $C show ccb9d979 \| git -C $C patch-id --stable` | note says GitHub hash ccb9d979 is "absent from this clone" | 097339c1 is modules/policy/README.rst only (docs) -> fix_tag null is defensible. But **ccb9d979 IS in the clone**: a commit object dated 2021-12-22, "policy docs: warn about filters and forwarding", contained in no tag, with patch-id identical to 097339c1 (0f2edce0c35e). The note is factually wrong. No CVE-id commit exists (`--grep=32983` -> 0). | FAIL |
| C.3 | CVE-2022-32983 | null | null | null | PASS |
| C.1 | CVE-2022-40188 | inventory lookup | true / true | true / true (inventory sha 817586f8) | PASS |
| C.2 | CVE-2022-40188 / f6577a20 | `git -C $C tag --contains f6577a20 \| grep -x v5.5.3`; `git -C $C tag --contains 817586f8` | v5.5.3 earliest | hit; earliest v5.5.3; 817586f8 in no tag (note correct) | PASS |
| C.3 | CVE-2022-40188 | 2022-09-21 − 2022-09-23 | −2 | −2 | PASS |
| C.1 | CVE-2023-26249 | inventory lookup | true / false | true / false; mapping via NVD text "hundred TCP connection attempts" to NEWS 5.6.0 !1380 stated | PASS |
| C.2 | CVE-2023-26249 / 3e28a8a6, a9528e33 | `git -C $C tag --contains <sha> \| grep -x v5.6.0` (x2) | v5.6.0 earliest | both hit; earliest v5.6.0 | PASS |
| C.3 | CVE-2023-26249 | 2023-01-26 − 2023-02-21 | −26 | −26 | PASS |
| C.1 | CVE-2023-46317 | inventory lookup | true / true | true / true | PASS |
| C.2 | CVE-2023-46317 / 49876a99 | `git -C $C tag --contains 49876a99 \| grep -x v5.7.0` | v5.7.0 earliest | hit; earliest v5.7.0 (then v6.0.2, non-stable) | PASS |
| C.3 | CVE-2023-46317 | 2023-08-22 − 2023-10-22 | −61 | −61 | PASS |
| C.1 | CVE-2023-50387 | inventory lookup | false / true; NVD date from by_product.bind9 | false / true (inventory sha 151c2645); bind9 published 2024-02-14 = row | PASS |
| C.2 | CVE-2023-50387 / cc5051b4, feb65eb9 | `git -C $C tag --contains <sha> \| grep -x v5.7.1` (x2); `git -C $C tag --contains 151c2645` | v5.7.1 earliest across 5.7.x and 6.0.x | both hit; earliest v5.7.1 (13:03+01) before v6.0.6 (14:17+01); 151c2645 in no tag (note correct) | PASS |
| C.3 | CVE-2023-50387 | 2024-02-13 − 2024-02-14 | −1 | −1 | PASS |
| C.1 | CVE-2023-50868 | inventory lookup | false / true; NVD from bind9 | false / true (inventory sha 96525e9a); bind9 2024-02-14 = row | PASS |
| C.2 | CVE-2023-50868 / e966b7fd, eccb8e27, b5051ac2, 24699e9f, a05cf1d3 | `git -C $C tag --contains <sha> \| grep -x v5.7.1` (x5); `git -C $C tag --contains 96525e9a` | v5.7.1 earliest | all hit; earliest v5.7.1; 96525e9a in no tag | PASS |
| C.3 | CVE-2023-50868 | 2024-02-13 − 2024-02-14 | −1 | −1 | PASS |
| C.1 | CVE-2026-39155 | inventory lookup | true / false; applicable=false with reason | true / false; inventory description is "Knot DNS ... mod-onlinesign", not Knot Resolver; reason stated | PASS |
| C.2 | CVE-2026-39155 | n/a | no fix expected | no fix_commits | PASS |
| C.1 | CVE-2026-66374 | inventory lookup | true / false | true / false; NVD 2026-07-25 | PASS |
| C.2 | CVE-2026-66374 / beab4229, 7eb2e118, 2e18114a | `git -C $C tag --contains <sha> \| grep -x v6.4.1` (x3); `git -C $C ls-tree v5.7.7 daemon/ \| grep -i quic` | v6.4.1 earliest; 5.7.x unaffected | all hit; earliest v6.4.1; no quic/doq files at v5.7.7, eight at v6.4.1; NEWS 6.4.1 Security "DNS-over-QUIC (DoQ) had severe issues, allowing even RCE" with no CVE id (note correct) | PASS |
| C.3 | CVE-2026-66374 | 2026-07-22 − 2026-07-25 | −3 | −3 | PASS |
| C.4 | pdns prefix rule | n/a for kresd | — | — | not applicable |

### D. Changelog entries (20 sampled, 17 releases)

Per row: D.1 `git -C $C show <tag>:<path> | grep -F '<first line of text>'`; D.2 same at the previous stable tag **on the same line** (5.x or 6.x); D.3 mechanism vs text; D.4 top-level `- ` bullets in the "Knot Resolver <ver>" section at the tag, and `+- ` lines in `git -C $C diff <prev>:<path> <tag>:<path>`.

| section | row | command | expected | observed | result |
|---|---|---|---|---|---|
| D | v1.2.0 "In a policy.FORWARD() mode, the AD flag..." | `git -C $C show v1.2.0:NEWS \| grep -F '- In a policy.FORWARD() mode'`; same at v1.1.1 | present / absent / validation / 17 | present; absent at v1.1.1; validation fits; section 17, diff +17 | PASS |
| D | v1.2.5 "dnssec/nsec: missed wildcard no-data..." | at v1.2.5 / v1.2.4 | present / absent / validation / 15 | present; absent; fits; 15 / +15 | PASS |
| D | v1.2.5 "policy.DENY: set AA flag and clear AD flag" | at v1.2.5 / v1.2.4 | present / absent / validation / 15 | present; absent; AD-flag handling, fits; 15 / +15 | PASS |
| D | v1.5.2 "fix CVE-2018-1000002..." | at v1.5.2 / v1.5.1 | present / absent / validation / 2 | present; absent; fits; 2 / +2 | PASS |
| D | v2.0.0 "policy module is now loaded by default..." | at v2.0.0 / v1.5.3 | present / absent / other / 15 | present; absent; "other" with note "not DNSSEC" fits; section 15, diff +22 (diff also picks up the 1.99.1-alpha section merged into the file; section count is the right measure) | PASS |
| D | v3.0.0 "fix multi-process race condition in trust anchor maintenance" | at v3.0.0 / v2.4.1 | present / absent / trust-anchor-5011 / 13 | present; absent; fits; 13 / +14 | PASS |
| D | v4.0.0 "DNSSEC is enabled by default" | at v4.0.0 / v3.2.1 | present / absent / validation / 39 | present; absent; fits; 39 / +39 | PASS |
| D | v4.1.0 "fix CVE-2019-10190..." | at v4.1.0 / v4.0.0 | present / absent / validation / 20 | present; absent; fits; 20 / +20 | PASS |
| D | v5.2.0 "ta_update: warn if there are differences..." | at v5.2.0 / v5.1.3 | present / absent / trust-anchor-5011 / 20 | present; absent; fits; 20 / +20 | PASS |
| D | v5.4.0 "trust_anchors.set_insecure: improve precision" | at v5.4.0 / v5.3.2 | present / absent / trust-anchor-5011 / 11 | present; absent; NTA handling, fits; 11 / +11 | PASS |
| D | v5.7.1 "CVE-2023-50387 KeyTrap..." | at v5.7.1 / v5.7.0 | present / absent / validation / 4 | present; absent; fits; 4 / +5 | PASS |
| D | v5.7.5 "validator: accept a confusing NODATA proof..." | at v5.7.5 / v5.7.4 | present / absent / validation / 5 | present; absent; fits; 5 / +5 | PASS |
| D | v5.7.7 "avoid AD=1 in reply if ANSWER+AUTHORITY are empty (#914)" | at v5.7.7 / v5.7.6 | present / absent / validation / 12 | present; absent; validation fits; 12 / +12 | PASS |
| D | v5.7.7 "support libdnssec merged into libknot..." | at v5.7.7 / v5.7.6 | present / absent / other / 12 | present; absent; build-level, "other" fits; 12 / +12 | PASS |
| D | v6.0.6 "CVE-2023-50387 KeyTrap..." | at v6.0.6 / v6.0.5 | present / absent / validation / 6 | present; absent at v6.0.5; fits; 6 / +8 (diff includes the embedded 5.7.1 section) | PASS |
| D | v6.0.6 "fix validation of RRsets around 64 KiB size" | at v6.0.6 / v6.0.5 | present / absent / validation / 6 | present; absent; fits; 6 / +8 | PASS |
| D | v6.0.9 "forward: fix wrong pin-sha256 length" | at v6.0.9 / v6.0.8 | present / absent / other (false positive noted) / 14 | present; absent; "other" + note "TLS SPKI pin" correct; 14 / +14 | PASS |
| D | v6.0.16 "reduce validation strictness for domain names" | at v6.0.16 / v6.0.15 | present / absent / other (false positive noted) / 9 | present; absent; correct; 9 / +9 | PASS |
| D | v6.0.17 "Removed options from declarative configuration model" | at v6.0.17 / v6.0.16 | present / absent / other, kind removal / 6 | present; absent; sub-bullets folded into one entry, top-level count 6 / +6 | PASS |
| D | v6.1.0 "avoid AD=1 in reply if ANSWER+AUTHORITY are empty (#914, !1780)" | at v6.1.0 / v6.0.17 | present / absent / mechanism consistent with the 5.7.7 twin / 9 | present; absent; **mechanism "other" while the same text under 5.7.7 is "validation"**; 9 / +9 | FAIL (D.3) |

### E. Coverage and gaps

| section | row | command | expected | observed | result |
|---|---|---|---|---|---|
| E.1 | stable tag count | `git -C $C tag \| grep -v -E 'rc\|beta\|alpha\|dev\|a[0-9]' \| wc -l` vs `release_count` / `stable:true` count | pattern count == stable:true count | 98 tags; **89** stable by pattern; JSON `release_count` 98 (all tags), `stable:true` = **84**; `.md` header "84 stable, 14 pre-release/early-access". The 5 extra are v6.0.1..v6.0.5, flagged `stable:false` on NEWS evidence (see A). | FAIL (rule) |
| E.2 | stable tags absent from releases[] | set difference | none | none; also no JSON tag absent from the clone | PASS |
| E.3 | gap 1 (algorithm support delegated to libdnssec) | `for p in ed25519 ed448 ecdsa gost rsasha256 rsasha512 'sha-?384'; do git -C $C log --all -i -E --grep=$p --format='%h %s'; done` | no algorithm-adding commits | 0 hits for all but "gost" (1 hit, cfd3e895 "gostats", a false substring) | PASS |
| E.3 | gap 2 (CVE-2022-32983 no code fix) | see C.2 above | not determinable in the clone | confirmed: only docs commits exist (097339c1 and its untagged twin ccb9d979); the gap statement itself is correct, the `cve_fixes` note is not (counted under C) | PASS |
| E.3 | gap 3 (CVE-2026-39155 not kresd) | inventory description | Knot DNS mod-onlinesign | confirmed | PASS |
| E.3 | gap 4 (approximate attribution for 2018-1110 / 2019-10190) | reasons stated | reasons present | `attribution_reason` present on both rows | PASS |
| E.3 | gap 5 (v6.0.1..v6.0.5 NEWS have no per-release entries) | `git -C $C show v6.0.1:NEWS \| head -8; git -C $C show v6.0.5:NEWS \| head -8` | only alpha/early-access notice | confirmed at v6.0.1 ("v6 alpha starts") and v6.0.5 ("early access ... not generally recommended"); v6.0.6 has a real section | PASS |
| E.3 | gap 6 (pre-release tags without entries) | tag list | rc/beta/alpha/a1 tags | 9 pattern pre-releases; consistent | PASS |
| E.3 | gap 7 (validation code at v1.0.0) | `git -C $C ls-tree v1.0.0 lib/dnssec.c` | file exists | `100644 blob a061c60c ... lib/dnssec.c` | PASS |
| E.3 | gap 8 (6.x YAML validation default) | `git -C $C show v6.0.6:manager/knot_resolver_manager/datamodel/config_schema.py \| grep -n dnssec` | line 123 `dnssec: Union[bool, DnssecSchema] = True` | line 123 exact | PASS |
| E.3 | gap 9 (non-DNSSEC defaults not tabulated) | entry rows | present as entries | 2.0.0 policy-module entry seen in D sample with `is_default_change: true`, mechanism other | PASS |
| E.3 | gap 10 (news_edits) | `git -C $C show v5.7.0:NEWS \| grep -c '!NNNN'`; `git -C $C show v5.7.8:NEWS \| grep -c '!1448'`; `git -C $C show v2.3.0:NEWS \| grep -c policy.REFUSE`; `... v2.4.1 ...`; 40083 counts above | edits reproduce | 1/1, 0/1, 40083 0 at v5.3.2 and 1 at v5.4.2: all four spot-checked edits reproduce | PASS |

### X. `.md` vs `.json` consistency and evidence sweep

| section | row | command | expected | observed | result |
|---|---|---|---|---|---|
| X | Release list table (98 rows) | parse `.md` "Release list" vs `releases[]` (date, stable, own entries, DNSSEC-ish rows) | equal | 0 mismatches | PASS |
| X | CVE table (16 rows) | parse vs `cve_fixes[]` (NVD date, fix tag, fix date, latency, commits) | equal | 0 mismatches | PASS |
| X | Default changes table (18 rows) | parse vs `default_changes[]` (version, date, title, flags, commits, attribution) | equal | 0 mismatches | PASS |
| X | Header line | "98 tags (84 stable, 14 pre-release/early-access)" | equals JSON counts | equals (subject to the E.1 rule question) | PASS |
| X | all 122 `changelog_entries[].evidence.commits[]` | `git -C $C tag --contains <sha> \| grep -x <tag>` for each | all hit | 122/122 hit | PASS |
| X | all 46 commits in the `.md` "Support added / defaults changed" table | same | all hit | 46/46 hit | PASS |

## Corrections required

1. **`releases[].stable` for v6.0.1, v6.0.2, v6.0.3, v6.0.4, v6.0.5** (and the derived counts: `stable:true` 84 -> 89; `.md` header "84 stable, 14 pre-release/early-access" -> "89 stable, 9 pre-release"). Wrong value by the brief's rule: `false`. Right value by the rule: `true`. Proof: `git -C $C tag | grep -E '^v6\.0\.[1-5]$'` — none carries an rc/beta/alpha/dev/aN suffix. Caveat for the corrector: the builder's deviation is not invented; `git -C $C show v6.0.1:NEWS | head -8` reads "6.0.x versions are dedicated to alpha cycle" and `git -C $C show v6.0.5:NEWS | head -6` reads "6.0.x are \"early access\" versions, not generally recommended for production use", and the notice disappears at v6.0.6. Either flip the five flags to `true`, or keep them and record the exception explicitly in `tag_pattern`/`branch_note` and in the brief's table for kresd. As delivered, the JSON contradicts the stated rule without the rule being amended.

2. **`default_changes[5]` (2.4.0 aggressive NSEC3) `commits[1]` = 17dae8a15f8546a4244626b576524f5c39b91130.** Wrong: cited as a product-change commit. Right: it is documentation only; drop it or move it to `documentation`. Proof: `git -C $C show --stat 17dae8a1` -> ` NEWS | 1 file changed`. The row stands on e2d5bd39 (merge !600, lib/cache/nsec3.c etc.).

3. **`default_changes[12]` (5.7.1 NSEC3 limits) and `default_changes[15]` (6.0.6 twin), field `after`.** Wrong: "KR_NSEC3_MAX_ITERATIONS 50 with kr_nsec3_price(iterations, salt_len) (lib/dnssec/nsec3.h@v5.7.1)". Right: the macro was removed; at v5.7.1 the limit is `kr_nsec3_limited(iterations, salt_len)` returning `kr_nsec3_price(iterations, salt_len) > MAX_ITERATIONS + 1` with a function-local `const int MAX_ITERATIONS = 50`, plus a `128 / kr_nsec3_price(...)` closest-encloser budget (nsec3.h lines 12-50). Same correction in the `.md` "Default changes" table (two rows). Proof: `git -C $C show v5.7.1:lib/dnssec/nsec3.h | grep -n -i -E 'ITERATIONS|price'` (no `KR_NSEC3_MAX_ITERATIONS`; line 29 `const int MAX_ITERATIONS = 50;`), versus `git -C $C show v5.7.0:lib/dnssec/nsec3.h | grep -n KR_NSEC3_MAX_ITERATIONS` (line 19, 150).

4. **`cve_fixes[8]` (CVE-2022-32983) `note`, and the same sentence in the `.md` CVE table.** Wrong: "NVD refs a GitHub hash (ccb9d9794db5) absent from this clone." Right: the commit is in the clone, dated 2021-12-22, "policy docs: warn about filters and forwarding", contained in no tag, and byte-identical as a patch to 097339c1 (which is in v5.5.0). Proof: `git -C $C cat-file -t ccb9d9794db5eb757c33becf65cb1cf48ecfd968` -> `commit`; `git -C $C tag --contains ccb9d9794db5eb757c33becf65cb1cf48ecfd968` -> empty; `git -C $C show ccb9d979 | git -C $C patch-id --stable` and `git -C $C show 097339c1 | git -C $C patch-id --stable` -> both `0f2edce0c35e...`. The conclusion (no code fix; fix_tag null) is unaffected.

5. **`releases[]` v6.1.0 entry "avoid AD=1 in reply if ANSWER+AUTHORITY are empty (#914, !1780)", field `mechanism`.** Wrong: `other`. Right: `validation`, matching the identical 5.7.7 entry "(#914)" which the same file classifies as `validation`. Proof: `git -C $C show v5.7.7:NEWS | grep -n 'avoid AD=1'` and `git -C $C show v6.1.0:NEWS | grep -n 'avoid AD=1'` show the same line; the JSON gives it two mechanisms.

Not a correction, but worth a line in `branch_note`: the three 6.0.x `default_changes` rows (6.0.6 x2, 6.0.8) are not the earliest stable tag containing their commits (v5.7.1 precedes v6.0.6 by 75 minutes and is its ancestor; v5.7.4 precedes v6.0.8 by 27 seconds and is not its ancestor). They are labelled as duplicates and the 5.7.x rows carry the first appearance, so no date is misattributed; a consumer that takes "earliest row per commit" gets the right answer.

## Not verifiable

- CVE-2022-32983 is described by NVD as fixed only by documentation; whether the vendor ever shipped a code change cannot be decided from this clone (`git -C $C log --all -i --grep=32983` -> 0; the GitHub-referenced hash is a docs commit). The row's `fix_tag: null` is the honest value.
- The `nvd_published` dates were checked against `data/software/cve_inventory.json` only (including the borrowed `by_product.knot` / `by_product.bind9` dates for CVE-2018-1110, CVE-2019-19331, CVE-2023-50387, CVE-2023-50868, all equal), not against NVD itself.
- For 6.0.x rows the "previous stable tag" used in D.2 was the previous 6.0.x tag regardless of the `stable` question in correction 1; if v6.0.1..v6.0.5 are re-flagged, the D.2 result for the two v6.0.6 entries is unchanged (checked against v6.0.5 already).

## Totals

| section | checks run | passed | failed |
|---|---|---|---|
| A. Release dates | 24 | 22 | 2 |
| B. Default changes | 92 | 89 | 3 |
| C. CVE fixes | 66 | 65 | 1 |
| D. Changelog entries | 20 | 19 | 1 |
| E. Coverage and gaps | 12 | 11 | 1 |
| X. md/json consistency and sweeps | 6 | 6 | 0 |
| **Total** | **220** | **212** | **8** |

The 8 failures collapse to the five corrections above (the five `stable` flags count once in A for the two sampled tags and once in E.1; the stale macro text counts once per duplicated row).
