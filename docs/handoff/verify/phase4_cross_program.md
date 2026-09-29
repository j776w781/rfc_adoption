# Phase 5 verification: Phase 4 cross-program comparison

Verifier: Phase 5 adversarial pass, 2026-09-29. Subject: commit 02650d6b, `scripts/cross_program.py`,
`docs/handoff/04_cross_program.md`, `out/analysis/cross_program*.{json,csv}`.
Method: every number below was recomputed from `data/software/timelines/<program>.json`, the RFC checklist and the
clones with verifier code in `/tmp/claude-1000/v5/` (not by importing `cross_program.py`). Samples use
`random.seed(20260929)`. No existing file was edited.

`PY` below means `/tmp/claude-1000/-mnt-shared-Documents-University-year2-DNSSEC-rfc-adoption/009fe9c8-8f6c-489b-9085-0e0b381788e0/scratchpad/venv/bin/python`.

## A. Normalisation

Checks run: 8 program recounts x 3 counts, 4 field-mapping checks, 1 full diff of 153 normalised default rows.

| program | default rows | CVE included | disputed | stable:true rows | stable after alias drop | pinned | result |
|---|---|---|---|---|---|---|---|
| bind9 | 28 | 149 | 0 | 444 | 444 | 28/149/444 | match |
| knot | 21 | 4 | 0 | 174 | 174 | 21/4/174 | match |
| kresd | 18 | 14 | 0 | 89 | 89 | 18/14/89 | match |
| nsd | 7 | 13 | 0 | 130 | 130 | 7/13/130 | match |
| opendnssec | 15 | 0 | 0 | 65 | 65 | 15/0/65 | match |
| pdns-auth | 12 | 15 | 0 | 132 | 132 | 12/15/132 | match |
| pdns-rec | 22 | 52 | 0 | **176** | 174 | 22/52/174 | explained |
| unbound | 30 | 65 | 12 | 120 | 120 | 30/65/120+12 | match |

Every count difference explained:

- pdns-rec 176 vs 174: `releases[]` has 176 rows with `stable: true`; two (`rec-3-0`, `rec-3-0-1`) carry `alias_of`
  and are dropped by `stable_releases()`. The brief says "only stable: true rows count", so the alias drop goes beyond
  the brief; it is disclosed in the doc and is the right call (same commit, not a separate release).
- Excluded CVEs: bind9 58 = 32 `not-applicable-or-not-bind9-release` + 26 `not-found` (the doc's label
  "not-applicable 32" abbreviates the status string). kresd 2 = CVE-2022-32983 (`applicable: true`, no `fix_tag`) +
  1 not applicable. nsd 1 = CVE-2013-5661 (applicable, no tag). opendnssec 1 = CVE-2012-5582 (applicable, no tag).
  unbound 2 = CVE-2009-4008 (applicable, no tag) + 1 not applicable. The brief's filter for "others" is only
  `applicable is True`; excluding applicable rows with a null tag is necessary (there is no date) and is disclosed.
- Every included bind9 row has `status` null; no bind9 row with a non-null `first_stable_tag` carries a
  not-found/not-applicable status.

Field mapping (all confirmed by my own normaliser, diffed against `cross_program_defaults_normalised.csv`, 153/153 rows
agree on stable tag, stable date, timing date and UTC instant):

- pdns-auth: all 12 rows use `releases[stable_tag].released`, not row `released`. Example: pdns-auth[11] row
  `released` 2021-12-07 (auth-4.6.0-beta1) -> stable auth-4.6.0 2022-01-24. Correct.
- nsd 2.3.0: date 2005-05-02, instant 2005-05-02T11:49:23Z from `released_note`. Correct.
- pdns-rec `first_public_tag`: three rows (dnssec-default-process and aggressive-nsec-cache: rec-4.5.0 2021-05-07
  -> public rec-4.5.1 2021-05-10; nsec3-max-iterations-50: rec-5.0.0 2023-12-18 -> public rec-5.0.1 2024-01-09).
  Both dates reported, public used for timing. Correct.
- bind9: no default row has a null tag; d22 and d23 (`value_changed: false`) are kept in Q1 only. CVE rows with a null
  tag are excluded and counted by status. Correct.

**Finding A1 (minor, doc wording).** Seven opendnssec rows have no `first_stable_tag` field at all:
opendnssec[4]@1.1.1, [6]@1.3.11, [9]@1.3.17, [10]@1.4.4, [12]@2.0.2, [13]@2.1.0, [14]@2.1.3. The brief's mapping, read
literally, fails them. The script substitutes the row `version` (`tag = r.get("first_stable_tag") or r["version"]`);
in all seven the version is itself a `stable: true` tag with the same date, so the substitution is correct in effect.
But the doc says "The field mapping is the one in 04_phase4_brief.md" and "no row failed the assert" without naming
this fallback; the JSON `normalisation.opendnssec` does name it. Proof:
`python3 -c "import json;d=json.load(open('data/software/timelines/opendnssec.json'));print([ (i,r['version']) for i,r in enumerate(d['default_changes']) if not r.get('first_stable_tag')])"`

Section A result: 29 checks run, 28 passed, 1 minor wording finding (A1), 0 inconclusive.

## B. Question 2: code lag vs RFC

Recomputed with `/tmp/claude-1000/v5/b.py` (own normaliser, checklist `publication_date`, months = days / 30.436875,
earliest row per program by timing date). All 16 per-RFC rows of the doc's table, every program order, every lag and
every spread reproduce exactly. The seven rows citing RFCs outside the checklist (kresd[1], kresd[3], unbound[10],
unbound[14], unbound[15], unbound[16], trust-anchor-ta-nta-management) reproduce.

Five sampled RFC x program pairs (`random.seed(20260929); random.sample(sorted(pairs), 5)`):

| RFC | published | program | row | timing date | lag days | lag months | doc | result |
|---|---|---|---|---|---|---|---|---|
| RFC 5702 | 2009-10-01 | knot | knot[1]@2.0.0 | 2015-06-26 | 2094 | 68.8 | 68.8 | pass |
| RFC 6840 | 2013-02-01 | unbound | unbound[22]@1.19.1 | 2024-02-13 | 4029 | 132.4 | 132.4 | pass |
| RFC 9276 | 2022-08-01 | pdns-auth | pdns-auth[10]@4.5.0 | 2021-07-12 | -385 | -12.6 | -12.6 | pass |
| RFC 5155 | 2008-03-01 | kresd | kresd[9]@5.3.1 | 2021-03-31 | 4778 | 157.0 | 157.0 | pass |
| RFC 8624 | 2019-06-01 | unbound | unbound[17]@1.10.0 | 2020-02-20 | 264 | 8.7 | 8.7 | pass |

Findings:

- **B1 (wording).** The doc says each program is represented by "the first default change that cites the RFC". Q2 in
  fact uses every row, including rows with `is_default_change: false`: pdns-rec's RFC 4034/4035 entry is
  `dnssec-setting-introduced`, its RFC 5011 entry is `revoked-dnskey-rejected`, its RFC 8080 entry is
  `ed25519-validation`, all `is_default_change: false`. The numbers are right for "first row citing the RFC"; the
  sentence is wrong. Proof: `python3 -c "import csv;[print(r['rfc'],r['row_id'],r['is_default_change']) for r in csv.DictReader(open('out/analysis/cross_program_q2_code_lag.csv')) if r['is_default_change']=='False']"`
- **B2 (wording).** "There are eleven negative lags" counts rows; four of the eleven are pdns-auth[5..8], all the same
  release auth-4.0.0 for RFC 8624, and two of those are the suspect intermediate rows. At the per-RFC, per-program
  level of the table there are six negative lags (unbound 5155, unbound 5702, pdns-auth 8624, knot 8624, pdns-auth
  9276, unbound 9276).
- **B3 (suspect row feeds the table).** The pdns-auth entry for RFC 6605 and RFC 8624 is pdns-auth[5]@4.0.0, a row
  Phase 4 itself rejects as an intermediate pre-release state (see H). No numeric effect because pdns-auth[7] and [8]
  have the same stable date 2016-07-08, but the row id cited should be pdns-auth[7]@4.0.0.
- **B4 (wording).** "No program comes first more often than chance": unbound comes first 4 times against 3.34
  expected, which is more often than the expectation, just not significantly (p = 0.44). Say "significantly more".

### Omission of bind9

bind9 rows have no `rfcs` field, but four rows name an RFC in their own text (`grep` over the JSON row):
d04-root-trust-anchor-builtin and d07-validation-auto-default name RFC 5011; d18-nsec3param-default-0-0 and
l02-nsec3-max-iterations-50 name RFC 9276. For the other programs the `rfcs` field follows the mechanism almost
mechanically: all six `alg-ecdsa` rows cite RFC 6605, and 21 of 27 `nsec3`/`nsec3-iterations` rows cite RFC 5155.
So there are two defensible inclusions, and both should be labelled as derived, not recorded:

1. Text-cited only (strictest): use a bind9 row only when its own text names the RFC.
2. Mechanism analogue: map `alg-ecdsa` -> RFC 6605 and `nsec3`/`nsec3-iterations` -> RFC 5155, as every other
   program's curated rows do.

| RFC | bind9 row | rule | date | lag months | position among programs | effect |
|---|---|---|---|---|---|---|
| RFC 5155 | d03-signzone-nsec3-iterations-100-to-10 | mechanism analogue | 2010-02-16 | 23.6 | 3rd of 8, after unbound and nsd | spread unchanged, 162.2 |
| RFC 6605 | d15-dnssec-policy-default-ecdsap256 | mechanism analogue | 2020-02-12 | 94.4 | last of 4 | spread becomes 92.9, was 49.7 |
| RFC 5011 | d04-root-trust-anchor-builtin | text-cited | 2011-02-21 | 41.7 | 1st of 4, ahead of unbound 113.5 | spread becomes 115.7; unbound loses its RFC 5011 lead |
| RFC 9276 | d18-nsec3param-default-0-0 | text-cited | 2022-01-24 | -6.2 | 3rd of 6, after pdns-auth and unbound | spread unchanged, 31.1 |
| RFC 9276 | l01-nsec3-max-iterations-150 | mechanism analogue, like unbound[19] and pdns-auth[10] | 2021-05-12 | -14.7 | 1st of 6 | would lead RFC 9276 |

Lag arithmetic: `python3 -c "from datetime import date as d;M=365.2425/12;[print(a,round((d.fromisoformat(c)-d.fromisoformat(b)).days/M,1)) for a,b,c in [('5155','2008-03-01','2010-02-16'),('6605','2012-04-01','2020-02-12'),('5011','2007-09-01','2011-02-21'),('9276 d18','2022-08-01','2022-01-24'),('9276 l01','2022-08-01','2021-05-12')]]"`

Caveats. Like every other program's entry these are first default changes, not first support: BIND shipped NSEC3 in
9.6.0 (2008-12-21, `NSEC3RSASHA1` is in `lib/dns/include/dns/keyvalues.h` at v9.6.0) and RFC 5011 managed-keys in
9.7.0 (2010-02-16, `bin/named/bind.keys.h` exists at v9.7.0), neither of which has a row. RFC 9276 is ambiguous for
bind9 because the pdns-rec 150 cap (nsec3-max-iterations-150) cites only RFC 5155 while unbound's and pdns-auth's
150 caps cite RFC 9276; the curated `rfcs` fields are themselves inconsistent here.

Judgement: omitting bind9 is defensible as "not recorded", but calling it only "a schema gap" undersells that the
data to include it for RFC 5011 and RFC 9276 is in the rows' own text. With the text-cited rule the RFC 5011 leader
changes from unbound to bind9. This does not change the Q2 chance-baseline conclusion (unbound drops from 4 to 3
leads). Recommended: add a derived bind9 row set, text-cited rule, labelled as such, or state in the doc that bind9
would lead RFC 5011 by its d04 text.

Section B result: 5 sampled lags + 16 per-RFC rows + 1 negative-lag count + 1 baseline sentence = 23 checks run,
19 passed, 4 wording or citation findings (B1-B4), 0 inconclusive. bind9 inclusion: judged, reported, not edited.

## C. Question 3: topic membership

I read all 153 normalised rows (mechanism, title/description, before, after; dump in `/tmp/claude-1000/v5/rows.txt`
plus the bind9 rows) and assigned the six topics without looking at `TOPICS`, then compared. For 44 of the 49
milestone assignments and all context assignments I agree. The six-topic table in the doc reproduces from the
script's `TOPICS` exactly (the regex/mechanism asserts are real and pass). Rows I would assign differently, or where
the table misleads because a comparable event exists in the rows' own text but is not a row:

| # | row / event | Phase 4 | verifier | reason and proof |
|---|---|---|---|---|
| C1 | bind9 d23-bindkeys-revoked-key-removed, v9.14.1, 2019-04-06 | rejected, `value_changed` false | same event as the KSK-2010 19036 removed sub-milestone | The key removed is KSK-2010: `git -C out/software_repos/bind9.git show v9.14.0:bind.keys \| grep -c AwEAAagAIKlVZrpC6Ia7gEz` gives 1, at v9.14.1 gives 0 (that base64 prefix is key tag 19036). unbound[18] and pdns-rec root-ds-19036-removed record the identical change, removing the revoked 19036 anchor, as default changes, and it has no validation effect there either. Excluding bind9 follows the brief's `value_changed` rule, but the like-for-like sub-milestone then drops the earliest program: bind9 2019-04-06 would lead pdns-rec 2019-07-12 and unbound 2020-07-20. At minimum the doc must say so. |
| C2 | unbound built-in root anchor, unbound-anchor at release-1.4.7, 2010-11-05 | table shows bind9 d04 2011-02-21 and kresd[6] only; Q4 calls bind9 leader by 2978 days | unbound had a built-in root anchor first; no row exists | unbound[12]'s own before text says "built-in root anchor: KSK-2010 (19036) only". `git -C out/software_repos/unbound.git show release-1.4.7:smallapp/unbound-anchor.c \| grep 'IN DS 19036'` matches; the file is absent at release-1.4.6. pdns-rec also had a built-in root DS from rec-4.0.0, 2016-07-08 (`git -C out/software_repos/pdns.git grep -n 19036 rec-4.0.0 -- pdns/rec-lua-conf.cc`), per trust-anchor-ta-nta-management's before text. The k = 2 contest and its 2978-day gap are an artefact of missing rows; Phase 4 must not report a leader for it. |
| C3 | knot[10]@2.8.0, CDS/CDNSKEY | "CDS/CDNSKEY publication default 2019-03-05" | knot[10] narrows publication, it does not start it | knot[10] before text: "CDS/CDNSKEY for the active KSK published permanently (default always since 2.5.0/2.6.1)"; after: "only during the KSK submission phase". The row belongs in the topic, but the table label should read "publication narrowed to rollover", and the first-publication date is not in the rows. No leader effect (k = 1). |
| C4 | knot[7], unbound[17], bind9 d10 (DSA removal) | rejected: "the DSA removals are not SHA-1" | agree with rejection, reason wrong | DSA algorithm 3 is DSA/SHA-1 and 6 is DSA-NSEC3-SHA1, so they are SHA-1 algorithms. The defensible reason is that the topic is RSASHA1 and SHA-1 DS, and DSA removal was driven by DSA itself. Reword. |
| C5 | pdns-auth[10]@4.5.0 in "iteration cap 150 or lower" | milestone | keep, but not like-for-like | It is an authoritative-side clamp on the zone's own NSEC3PARAM (500 -> 100), not a validator cap; the other four are validator caps. It does not lead, so no effect on Q4. The Q4 caveat mentions it; the Q3 table does not. |
| C6 | pdns-rec dnssec-default-process in "validates out of the box" | milestone | keep with caveat already given | Validates only when the client sets AD or DO. The doc states this. Agree. |

Timeline gaps found while checking (not Phase 4 errors; the rows do not exist, so Phase 4 could not use them, but
they change who is first):

- bind9 `trust-anchor-telemetry yes` (RFC 8145) is the built-in default at v9.11.0, 2016-09-29, and v9.10.5,
  2017-04-14: `git -C out/software_repos/bind9.git grep -n 'trust-anchor-telemetry yes' v9.11.0 -- bin/named/config.c`.
  bind9 would lead the RFC 8145 sub-milestone by a year over unbound[14] (2017-10-10).
- bind9 `root-key-sentinel yes` (RFC 8509) is the default at v9.12.2, 2018-07-03 (absent at v9.12.1):
  `git -C out/software_repos/bind9.git grep -n 'root-key-sentinel yes' v9.12.2 -- bin/named/config.c`. bind9 would
  be third, after kresd and unbound.

Clone checks of five topic dates and values (sample `random.seed(20260929); random.sample(sorted(milestone rows), 5)`;
value read at the tag, date is the tag commit's `%cI` in UTC):

| row | tag | clone commit instant, UTC | timeline instant | value at the tag | result |
|---|---|---|---|---|---|
| kresd[3]@2.0.0 | v2.0.0 | 2018-01-31T13:25:52Z | 2018-01-31T13:25:52Z | `daemon/lua/sandbox.lua:242: modules.load('ta_sentinel')`; absent at v1.5.3 | pass |
| pdns-auth[8]@4.0.0 | auth-4.0.0 | 2016-07-08T09:59:41Z | 2016-07-08T09:59:41Z | `pdns/common_startup.cc:179 default-ksk-algorithms="ecdsa256"`, `:181 default-zsk-algorithms=""` | pass |
| unbound[21]@1.16.1 | release-1.16.1 | 2022-07-04T11:48:56Z | 2022-07-04T11:48:56Z | `validator/val_secalgo.c` diff 1.16.0..1.16.1 adds `EVP_R_INVALID_DIGEST` / FIPS handling | pass |
| knot[2]@2.1.0 | v2.1.0 | 2016-01-14T09:15:02Z | 2016-01-14T09:15:02Z | `src/dnssec/lib/kasp/policy.c:109 policy->algorithm = DNSSEC_KEY_ALGORITHM_ECDSA_P256_SHA256` (v2.0.0: RSA_SHA256) | pass |
| unbound[12]@1.6.1 | release-1.6.1 | 2017-02-14T13:44:42Z | 2017-02-14T13:44:42Z | `smallapp/unbound-anchor.c:247 ". IN DS 20326 8 2 E06D..."`; release-1.6.0 has 19036 only | pass |

Note: the timeline uses commit instants, not tagger dates. For auth-4.0.0 the tagger date is 2016-07-11 and for
release-1.16.1 it is 2022-07-11; this was settled in Phase 1 and does not affect Phase 4.

Section C result: 49 milestone assignments + 5 clone checks = 54 checks run, 49 passed, 5 failed (C1-C3 material to
the table or to Q4, C4-C5 wording; C6 is an agreed caveat and counts as a pass), 0 inconclusive.

## D. Question 4: chance baseline

Recomputed with `/tmp/claude-1000/v5/d.py`: my own ordering of the Q3 memberships by UTC instant, my own
Poisson-binomial tail. All 16 sub-milestone leaders, k values and median gaps reproduce exactly, and so does every
row of the baseline table (bind9 10/2/3.45/0.91, knot 3/2/1.00/0.26, kresd 7/3/2.62/0.53, opendnssec 2/2/0.67/0.11,
pdns-auth 3/0/0.87/1.00, pdns-rec 7/2/2.28/0.73, unbound 8/3/3.12/0.67). The Q2 first-to-ship baseline also
reproduces: unbound 11 contests, 4 firsts, 3.34 expected, p = 0.44, with RFC 4033/4034/4035 merged on nsd[2].

Ties. Two contests tie on the calendar day (bind9 d18 and pdns-auth[11], 2022-01-24 at 20:04Z and 11:00Z). Dropping
them is defensible because a 9-hour gap between two unrelated release processes is not a lead. Alternative: split the
lead 1/2 each. Then bind9 has 12 contests, 3 leads, 4.12 expected, p = 0.84, and pdns-auth has 5 contests, 1 lead,
1.53 expected, p = 0.84. The conclusion does not change. The median gaps of the tied contests (105 and 666.5) are
computed from pdns-auth as order[0], with bind9 at gap 0 included; that is consistent with "median gap to the rest".

Sensitivity to section C. With C1 (bind9 d23 leads KSK-2010 removal) and C2 (unbound 2010-11-05 and pdns-rec
2016-07-08 join the built-in root anchor contest): unbound 9 contests, 4 leads, 3.20 expected, p = 0.40; bind9 11/2/3.53/0.92.
Also adding the bind9 RFC 8145 and RFC 8509 defaults found in the clone: bind9 13/3/4.20/0.85, unbound 9/3/2.87/0.59.
No variant makes any program a leader. The conclusion "no program is a leader" is robust.

**Finding D1 (method).** The topic-level contests (the doc's "at the level of the six whole topics") include context
rows, which the doc says are "not milestones". The NSEC3/RFC 9276 topic is therefore led by unbound[1]@0.5 (a 2007
key-size-dependent cap, context), not by kresd[9] (2021-03-31, the first milestone). The doc's sentence "no program
leads more than two of them" is true under both readings (with context: knot 1, unbound 2, bind9 1, opendnssec 1, and
k = 1 for CDS; milestones only: knot, kresd, unbound, bind9, opendnssec 1 each), so only the method needs a note.
Proof: `python3 -c "import json;[print(t['topic'],t.get('leader'),t.get('leader_row')) for t in json.load(open('out/analysis/cross_program.json'))['q4_leader_follower']['topics']]"`

**Finding D2 (depends on C2).** The row "built-in root anchor | 2 | bind9 | 2978" must not stand: unbound-anchor had a
built-in root DS at release-1.4.7, 2010-11-05, three months before bind9 d04. Either drop this sub-milestone from Q4
or mark it "leader not determinable from rows".

Section D result: 16 leaders + 7 baseline rows + Q2 baseline + tie handling + topic-level = 26 checks run, 24 passed,
2 findings (D1, D2), 0 inconclusive.

## E. Question 6: CVE fix latency

Recomputed with pandas (`/tmp/claude-1000/v5/e.py`; `Series.quantile` linear interpolation, which equals
`statistics.quantiles(method="inclusive")`).

| program | included | with latency | median | IQR | public median, n | DNSSEC rows with latency: n, median, IQR | doc |
|---|---|---|---|---|---|---|---|
| bind9 | 149 | 135 | -13 | -21 to -9 | none | not classified | match |
| knot | 4 | 4 | -148 | -462 to -87.75 | none | 1, -112 | match; doc rounds Q3 to -88 |
| kresd | 14 | 14 | -4.5 | -22.5 to -1 | none | 7, -1, -6 to -0.5 | match |
| nsd | 13 | 13 | -1 | -8 to 0 | none | 0 | match |
| opendnssec | 0 | 0 | none | none | none | 0 | match |
| pdns-auth | 15 | 10 | -8.5 | -34.75 to -0.75 | -2, n=3 | 0 | match |
| pdns-rec | 52 | 46 | -20 | -37.5 to -3.25 | -2, n=4 | **13**, -8, -20 to -3 | doc says n = 14 |
| unbound | 65 | 52 | 0 | 0 to 0 | none | **14**, 0, 0 to 0 | doc says n = 17 |

Pooled: n = 274, median -10, IQR -20 to -0.25. Matches. Disputed unbound: 12 rows, all -509. Matches.

knot's -148, row by row (fix tag dates checked against the clone's commit dates, all four agree):

| CVE | fix tag | fix date | NVD published | latency |
|---|---|---|---|---|
| CVE-2014-0486 | v1.5.2 | 2014-09-08 | 2018-03-27 | -1296 |
| CVE-2016-6171 | v2.3.0 | 2016-08-09 | 2017-02-09 | -184 |
| CVE-2026-39155 | v3.5.4 | 2026-04-02 | 2026-07-23 | -112 |
| CVE-2017-11104 | v2.5.2 | 2017-06-23 | 2017-07-08 | -15 |

The median of four is the mean of the middle two, (-184 + -112) / 2 = -148. It measures NVD's delay in publishing
old knot CVEs, not knot's fix speed: three of the four rows are 3 to 43 months ahead of NVD. With n = 4 the median is
not comparable to bind9's n = 135. The doc gives n but no warning; the JSON caveat mentions CVE-2014-0486.

**Finding E1 (count error).** The doc says "Five unbound fixes and all twelve disputed unbound rows name a release
candidate as `fix_tag`". The number is four: CVE-2009-3602 (release-1.4.0rc1), CVE-2017-15105 (release-1.7.0rc1),
CVE-2020-28935 (release-1.13.0rc1), CVE-2024-33655 (release-1.20.0rc1). The script's own
`n_pre_release_fix_tags` for unbound is 4. Proof:
`python3 -c "import json;[print(r['program'],r['n_pre_release_fix_tags'],r['pre_release_fix_tag_rows']) for r in json.load(open('out/analysis/cross_program.json'))['q6_cve_latency']['per_program'] if r['program']=='unbound']"`

Release-candidate handling for those four rows is correct: `latency_days_stable` is 41 for CVE-2009-3602
(release-1.4.0, 2009-11-23 minus 2009-10-13), -4 for CVE-2020-28935 (release-1.13.0, 2020-12-03 minus 2020-12-07),
null for CVE-2024-33655 (no NVD date), and CVE-2017-15105 keeps the vendor 1.6.8 date as the brief requires.
The unbound median is 0 either way.

**Finding E2 (wording).** The DNSSEC-subset n in the doc is the number of rows classified `dnssec_related: true`
(pdns-rec 14, unbound 17), but the median and IQR are over the rows that have a latency (13 and 14). Report both, as
the main columns already do ("included", "with latency").

Section E result: 8 program rows + pooled + disputed + 4 knot rows + 4 RC rows = 18 checks run, 16 passed,
2 findings (E1, E2), 0 inconclusive.

## F. Question 7: release cadence

Recomputed with `/tmp/claude-1000/v5/f.py` (stable true, aliases dropped, ordered by `released_full` as UTC instants,
intervals in days, decade of the later release). All eight rows of the doc's table reproduce exactly: n, overall
median, the three decade medians and the "same-day pairs" count.

Note on the label: "same-day pairs" is the number of consecutive intervals shorter than 24 hours, not pairs on the
same calendar day. For bind9 that is 208 intervals; bind9 has 444 releases on 242 distinct UTC days.

Should same-day parallel-branch releases be collapsed? Yes, for any cross-program comparison. A bind9 security event
ships 9.16.x, 9.18.x and 9.20.x at once; pdns-rec ships three or four maintained branches together. Counting each tag
as a release measures the number of maintained branches, not how often the project releases. The uncollapsed medians
make bind9 (3.39 days) and pdns-rec (16.03) look five to ten times faster than everyone else; collapsed, the eight
programs sit within a factor of 2.3 of each other. Collapsed medians, one event per UTC calendar day:

| program | stable releases | distinct release days | median days between, raw | collapsed | 2000s | 2010s | 2020s |
|---|---|---|---|---|---|---|---|
| bind9 | 444 | 242 | 3.39 | 30 | 49 | 30 | 28 |
| knot | 174 | 157 | 30.04 | 34 | none | 34 | 34 |
| kresd | 89 | 82 | 35.05 | 37 | none | 27 | 46.5 |
| nsd | 130 | 119 | 64.09 | 68.5 | 73 | 64 | 70 |
| opendnssec | 65 | 60 | 51.95 | 61 | none | 46.5 | 136 |
| pdns-auth | 132 | 112 | 35.10 | 50 | 41 | 69 | 39 |
| pdns-rec | 174 | 117 | 16.03 | 34.5 | 142 | 49.5 | 30 |
| unbound | 120 | 118 | 55.15 | 56 | 24 | 58.5 | 63 |

The collapsed ordering is bind9 30, knot 34, pdns-rec 34.5, kresd 37, pdns-auth 50, unbound 56, opendnssec 61,
nsd 68.5. Collapsing on the `released` calendar field instead of the UTC day gives 245 bind9 days, not 242, because
three bind9 releases cross midnight UTC. The medians are unchanged to the day.

**Finding F1 (missing comparison).** The doc says parallel branches "pull bind9's and pdns-rec's medians down" but
publishes only the raw medians. Add the collapsed column, and relabel "same-day pairs" as "intervals under 24 hours".

Section F result: 8 program rows reproduced, collapse judged = 9 checks run, 8 passed, 1 finding (F1), 0 inconclusive.

## G. Question 8: circular-shift null

Implementation read (`circular_null`, `codebase_spans`, `coordinated_pairs`, `summarise_null` in
`scripts/cross_program.py`):

- One offset per codebase per draw, `rng.uniform(0, span_seconds)`, applied to every event of that codebase, so all
  internal spacings are preserved (modulo the wrap). Confirmed.
- The wrap is `((t - lo) + offset) % L` with `lo, hi` = the codebase's first and last stable release instant, so
  events wrap within the program's own span. Confirmed.
- `N_DRAWS = 1000`, `random.Random(SEED)` with `SEED = 20260929`, codebases iterated in sorted order, so draws are
  deterministic. Confirmed.
- pdns: `CODEBASE["pdns-auth"] = CODEBASE["pdns-rec"] = "pdns"`; the span is the union of the two programs' spans,
  pairs with `ca == cb` are skipped, and both programs' events move with one offset. Confirmed; pdns-auth and pdns-rec
  count as one codebase.
- p = (draws >= observed + 1) / 1001, percentile = mid-rank. Reasonable.

Independent recomputation (`/tmp/claude-1000/v5/g.py`: my own event builder from the timeline JSONs, own pair finder,
own shift; topic events taken from the Q3 membership CSV). 370 events; labels shared by two or more codebases:
CVE-2023-50387, CVE-2023-50868 (bind9, kresd, pdns, unbound), CVE-2020-28935 (nsd, unbound) and five topics.

| statistic | observed | null mean | null p95 | percentile | p | doc |
|---|---|---|---|---|---|---|
| distinct release pairs | 4 | 0.202 | 1 | 100.0 | 0.001 | match |
| CVE label pairs | 6 | 0.012 | 0 | 100.0 | 0.001 | match |
| topic label pairs | 1 | 0.196 | 1 | 90.25 | 0.186 | match (doc 90.2, 0.19) |

With a different seed (1) the figures are 0.198, 0.009, 0.194, percentile 90.4, p 0.173: the result does not
depend on the seed.

The four coordinated release pairs:

1. bind9 v9.18.0 2022-01-24T20:04:14Z and pdns auth-4.6.0 2022-01-24T10:59:59Z, topic nsec3-iterations-rfc9276
   (d18 and pdns-auth[11]), gap 0.38 days.
2. bind9 v9.18.24 2024-02-11T10:39:40Z and kresd v5.7.1 2024-02-13T12:03:08Z, CVE-2023-50387 and CVE-2023-50868, 2.06 days.
3. bind9 v9.18.24 and unbound release-1.19.1 2024-02-13T12:04:07Z, the same two CVEs, 2.06 days.
4. kresd v5.7.1 and unbound release-1.19.1, the same two CVEs, 0.00 days (59 seconds apart).

The public-date variant (pdns-rec KeyTrap at 2024-02-13 from the changelog) adds pdns to bind9, kresd and unbound:
1.56, 0.50 and 0.50 days, so 3 more pairs = 7. That matches the doc's 7 by arithmetic; I did not rerun its null.

Comments:

- The CVE test is significant by construction: two codebases fixing the same CVE within 3 days is an embargo, and
  independent circular shifts almost never realign them (null mean 0.012). The doc says this ("the shift destroys by
  design") and correctly calls it one event. Fine.
- Topic labels are matched at the whole-topic level, and context rows are events. So a signer default in one
  program and a validator cap in another would count as "the same topic". The single observed topic pair is a true
  like-for-like pair (both signer iterations 0), and it is correctly called not a finding.

Section G result: 5 implementation checks + 3 statistics + 4 pairs + seed robustness + pdns-codebase check = 14
checks run, 13 passed, 0 failed, 1 inconclusive (the public-date variant's null was not rerun).

## H. Suspect rows raised by Phase 4

### bind9 d10-dsa-removed, field `mechanism`

Confirmed. The row's description and changelog line say "Remove support for DNSSEC algorithms 3 (DSA) and 6
(DSA-NSEC3-SHA1)"; its commit d6c50674bb removes DSA; the clone agrees
(`git -C out/software_repos/bind9.git ls-tree -r --name-only v9.12.0 lib/dns | grep -c openssldsa_link` gives 1, at
v9.14.0 gives 0). Nothing about it is RSA or SHA-2, yet `mechanism` is `alg-rsa-sha2`. The other two DSA-removal rows,
knot[7]@2.6.0 and unbound[17]@1.10.0, use `other`.

Correct value: `mechanism: "other"`, for consistency with knot[7] and unbound[17]. The Phase 3 bind9 verification
(`docs/handoff/verify/bind9.md` line 71) checked the tag and the removal but not the mechanism label.
Effect on Phase 4: the Q1 cell alg-rsa-sha2 / bind9 / removal (v9.14.0, d10) should move to other / bind9 / removal.
No other question uses d10.

Proof: `python3 -c "import json;d=json.load(open('data/software/timelines/bind9.json'));r=[x for x in d['default_changes'] if x['id']=='d10-dsa-removed'][0];print(r['mechanism'],'|',r['description'])"`

### pdns-auth default_changes[5] and [6], field `stable_tag`

Confirmed. Values of the two settings in `pdns/common_startup.cc`, read at each tag:

| tag | commit date | default-ksk-algorithms | default-zsk-algorithms |
|---|---|---|---|
| auth-3.4.11 | 2017-01-13 | rsasha256 | rsasha256 |
| auth-4.0.0-alpha1 | 2015-12-24 | "" | ecdsa256 |
| auth-4.0.0-alpha2 | 2016-02-25 | "" | ecdsa256 |
| auth-4.0.0-alpha3 | 2016-05-11 | ecdsa256 | "" |
| auth-4.0.0-beta1, rc1, 4.0.0, 4.0.1 | 2016-05-27 to 2016-07-29 | ecdsa256 | "" |

Command: `bash -c 'for t in auth-3.4.11 auth-4.0.0-alpha1 auth-4.0.0-alpha2 auth-4.0.0-alpha3 auth-4.0.0; do echo $t $(git -C out/software_repos/pdns.git grep -h "default-[kz]sk-algorithms" $t -- pdns/common_startup.cc | sed "s/.*=//"); done'`

pdns-auth[5]'s after-state (KSK list empty) and pdns-auth[6]'s after-state (ZSK default ecdsa256) exist only in
auth-4.0.0-alpha1 and alpha2. pdns-auth[8] reversed both at alpha3, and no stable release on any branch carries either
state. `stable_tag: "auth-4.0.0"` is therefore wrong for both rows.

Correct value: `stable_tag: null` for pdns-auth[5] and [6], with a note "pre-release only, superseded by
default_changes[8] at auth-4.0.0-alpha3". pdns-auth[5]'s after text also misdescribes alpha1, which shipped both
changes together: KSK "" and ZSK ecdsa256, not KSK "" and ZSK rsasha256. Also acceptable: keep the rows and set
`is_default_change: false`.

Effect on Phase 4: none numerically, because pdns-auth[7] and [8] have the same stable date. But pdns-auth[5] is the
cited row id for pdns-auth in Q2 for RFC 6605 and RFC 8624 (finding B3) and in the Q1 alg-ecdsa cell. Once
`stable_tag` is null the normaliser's assert would list both rows as failures, which is the brief's intended handling.

Section H result: 2 suspect items checked, 2 confirmed with commands, correct values given.

## I. Sentences in 04_cross_program.md that overstate or misstate

| # | section | sentence (current) | problem | replacement |
|---|---|---|---|---|
| I1 | Normalisation | "The field mapping is the one in 04_phase4_brief.md" and "so no row failed the assert" | Seven opendnssec rows have no `first_stable_tag`; the script falls back to `version` (A1) | "... except that seven opendnssec rows without `first_stable_tag` use their `version`, which is itself a stable release with the same date" |
| I2 | Q1 | Table header "earliest program", rows cds-cdnskey = knot v2.8.0 and trust-anchor-5011 = bind9 v9.8.0 | Reads as "first to do it". knot[10]'s own before text says CDS was published by default since 2.5.0, and unbound[12]'s before text implies a built-in root anchor before 1.6.1 (release-1.4.7, 2010-11-05) | Header "earliest row"; add "blank or later rows do not mean later adoption" |
| I3 | Q2 | "That row is the first default change that cites the RFC" | Non-default rows are used (B1) | "the first row, default change or not, that cites the RFC" |
| I4 | Q2 | "There are eleven negative lags." | Eleven rows but six program-level lags; four rows are the same auth-4.0.0 release (B2) | "Eleven rows, six programs x RFCs, have negative lags" |
| I5 | Q2 | "No program comes first more often than chance." | unbound comes first 4 times against 3.34 expected (B4) | "No program comes first significantly more often than chance (unbound 4 vs 3.34, p = 0.44)" |
| I6 | Q2 and "could not be determined" | "bind9 is absent here. That is a schema gap, not a finding." / "bind9's RFC lags, because bind9 rows carry no rfcs field." | d04, d07, d18, l02 name RFC 5011 or RFC 9276 in their own text; bind9 would lead RFC 5011 (41.7 months vs unbound 113.5) | Add the text-cited bind9 lags or state them as a derived sensitivity (section B) |
| I7 | Q3 | "The DSA removals are not SHA-1." | Algorithms 3 and 6 are DSA/SHA-1 (C4) | "DSA removals are driven by DSA itself, not by the SHA-1 / RSASHA1 deprecation" |
| I8 | Q3 | Row "CDS/CDNSKEY publication default: knot 2019-03-05 knot[10]" | knot[10] narrows publication to rollover-only (C3) | "CDS/CDNSKEY publication narrowed to rollover" |
| I9 | Q3 and Q4 | KSK-2010 19036 removed: pdns-rec leads, k = 2; rejected list: "bind9 d22 and d23 are not default changes" | bind9 d23 removed the same key on 2019-04-06, earlier than both (C1) | State that bind9 removed 19036 first and is excluded only by `value_changed: false` |
| I10 | Q4 | "built-in root anchor, k = 2, leader bind9, 2978 days" | unbound had a built-in root DS in release-1.4.7, 2010-11-05, and pdns-rec from rec-4.0.0; no rows exist (C2, D2) | Drop the leader, or write "not determinable from the rows" |
| I11 | Q4 | "kresd and unbound reach three leads, but each is at its chance expectation." | kresd 3 vs 2.62 is above its expectation, not at it | "each is close to its chance expectation (p = 0.53 and 0.67)" |
| I12 | Q4 | "At the level of the six whole topics, no program leads more than two of them." | True, but topic-level contests include context rows; unbound leads NSEC3 via context row unbound[1] (D1) | Add "context rows included", or recompute on milestones only |
| I13 | Normalisation point 3 | "Five unbound fixes and all twelve disputed unbound rows name a release candidate" | Four (E1) | "Four unbound fixes ..." |
| I14 | Q6 | DNSSEC subset "pdns-rec 14, -8", "unbound 17, 0" | n counts classified rows; the medians are over 13 and 14 rows with latency (E2) | Give both n |
| I15 | Q6 | knot median -148 with no qualifier | n = 4; three of the four are driven by late NVD publication (-1296, -184, -112) | Add "n = 4; reflects NVD lag, not comparable" |
| I16 | Q7 | Column "same-day pairs"; raw medians only | These are intervals under 24 h; raw medians mostly count branches (F1) | Rename, add collapsed medians (bind9 30, pdns-rec 34.5 ...) |

Not overstated, checked: Q5's "all four programs still ship RFC 8624-motivated defaults" (the heuristic is stated,
and the hand-read rows are named); Q8's "The CVE coordination is real, and it is one event" (the doc also says the
shift destroys embargo alignment by design); the Arc A cross-check (2 disagreements recomputed from the JSON; the
unbound 0.5 `validator/val_nsec3.c` claim is confirmed by `git ls-tree`).

Not run: `python3 -m pytest tests/test_cross_program.py -q` ("24 passed"). The test fixtures call the script, which
rewrites `out/analysis/`, and this pass must not modify existing files. Recorded as inconclusive.

## Totals

| section | run | passed | failed | inconclusive |
|---|---|---|---|---|
| A normalisation | 29 | 28 | 1 | 0 |
| B Q2 lags + bind9 | 23 | 19 | 4 | 0 |
| C Q3 topics + clone | 54 | 49 | 5 | 0 |
| D Q4 baseline | 26 | 24 | 2 | 0 |
| E Q6 latency | 18 | 16 | 2 | 0 |
| F Q7 cadence | 9 | 8 | 1 | 0 |
| G Q8 null | 14 | 13 | 0 | 1 |
| H suspect rows | 2 | 2 (both suspicions confirmed) | 0 | 0 |
| I sentences | 19 | 3 | 16 | 0 |
| tests, Arc A | 3 | 2 | 0 | 1 |
| **total** | **197** | **164** | **31** | **2** |

"Failed" counts findings, most of which are wording. No recomputed number differs from Phase 4's, except the count
"five" in I13. No conclusion changes: no program is a leader under any variant, and the only coordination is KeyTrap.

## Verdict: PASS WITH CORRECTIONS

Required corrections are listed in the hand-off report, and repeated here:

1. `docs/handoff/04_cross_program.md`, Normalisation point 3: "Five unbound fixes" should read "Four unbound fixes".
   Proof: `python3 -c "import json;[print(r['n_pre_release_fix_tags']) for r in json.load(open('out/analysis/cross_program.json'))['q6_cve_latency']['per_program'] if r['program']=='unbound']"` prints 4.
2. `data/software/timelines/bind9.json` default_changes id d10-dsa-removed, `mechanism`: currently `alg-rsa-sha2`,
   should be `other`, matching knot[7] and unbound[17]; move the Q1 cell. Proof: section H command.
3. `data/software/timelines/pdns-auth.json` default_changes[5] and [6], `stable_tag`: currently `auth-4.0.0`, should be
   null, with a note "pre-release only (alpha1, alpha2); superseded by [8] at alpha3". Fix [5]'s `after` text to match
   alpha1 (ZSK ecdsa256 via [6]). Proof: the section H `bash -c` loop.
4. `04_cross_program.md` Q2 and `cross_program.json` q2 `per_rfc` for RFC 6605 and RFC 8624: pdns-auth `row_id`
   is currently pdns-auth[5]@4.0.0, should be pdns-auth[7]@4.0.0 (same date). Follows from 3.
5. `04_cross_program.md` Q4 row "built-in root anchor | 2 | bind9 | 2978": replace the leader with "not determinable
   from rows; unbound-anchor had a built-in root DS at release-1.4.7, 2010-11-05". Proof:
   `git -C out/software_repos/unbound.git show release-1.4.7:smallapp/unbound-anchor.c | grep 'IN DS 19036'`.
6. `04_cross_program.md` Q3/Q4 KSK-2010 removal: add that bind9 d23 (v9.14.1, 2019-04-06) removed the same key first
   and is excluded only by `value_changed: false`. Proof: `git -C out/software_repos/bind9.git show v9.14.1:bind.keys | grep -c AwEAAagAIKlVZrpC6Ia7gEz` prints 0; at v9.14.0 it prints 1.
7. `04_cross_program.md` Q2: add the bind9 text-cited lags (RFC 5011 d04 41.7 months, first; RFC 9276 d18 -6.2, third)
   as a labelled derived sensitivity, and change "schema gap, not a finding" accordingly. Proof: section B lag command.
8. `04_cross_program.md` wording fixes I1, I3, I4, I5, I7, I8, I11, I12, I14, I15, I16 as tabled in section I.
9. Phase 1 follow-up, not a Phase 4 error: bind9 lacks rows for `trust-anchor-telemetry yes` (RFC 8145, v9.11.0,
   2016-09-29) and `root-key-sentinel yes` (RFC 8509, v9.12.2, 2018-07-03), and unbound lacks a row for the built-in
   root anchor (release-1.4.7). Proof: `git -C out/software_repos/bind9.git grep -n 'trust-anchor-telemetry yes' v9.11.0 -- bin/named/config.c`.
