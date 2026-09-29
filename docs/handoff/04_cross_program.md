# Phase 4 output: cross-program comparison

This is the corrected version, written after the Phase 5 verification in `docs/handoff/verify/phase4_cross_program.md`,
which passed with corrections. It is rebuilt on the timeline data as corrected in commit 54400276.

For the Phase 5 verifier. Everything below is produced by `scripts/cross_program.py` from the eight verified
timelines, the RFC checklist and, for a cross-check only, `data/software/software_support.json`. The script is
deterministic. The only randomness is the question 8 null, drawn from `random.Random(20260929)` with 1,000 draws.

Rebuild everything: `python3 scripts/cross_program.py`. It needs only the standard library.
Tests: `python3 -m pytest tests/test_cross_program.py -q` gives 28 passed.

Outputs:

- `out/analysis/cross_program.json` holds one key per question plus `normalisation`, `normalisation_counts`,
  `row_counts`, `excluded_rows`, `suspect_rows`, `resolved_suspect_rows` and `xcheck_software_support`.
- `out/analysis/cross_program_<question>.csv` holds one long-form CSV per question. Two more CSVs,
  `cross_program_defaults_normalised.csv` and `cross_program_cves_normalised.csv`, hold every normalised row.

Row ids: bind9 uses `id`, pdns-rec uses `key`, every other program uses `<program>[<index>]@<version>`, where the
index is the position in that file's `default_changes[]`. Index-based ids shift when a row is inserted. Commit
54400276 inserted unbound[12]@1.4.7, so every unbound row from 1.6.1 on has an index one higher than in the first
version of this report. The version part of an id is stable.

## Normalisation

The field mapping follows `04_phase4_brief.md`, with one exception: seven opendnssec rows have no `first_stable_tag`
field. Those rows use their `version`, which is itself a stable release with the same date. The seven rows are
opendnssec[4], [6], [9], [10], [12], [13] and [14], and they are listed under
`normalisation_counts.opendnssec_rows_using_version_fallback`.

Rows whose stable tag is null are excluded rather than treated as failures. They are listed under
`excluded_rows.default_changes_null_stable_tag`. There are two such rows, pdns-auth[5] and [6]: pre-release states from
auth-4.0.0-alpha1 and alpha2 that no stable release shipped. Every other default row's stable tag exists in
`releases[]` with `stable: true`, and its date agrees with the release row.

Four further points go beyond the brief.

1. Only bind9, pdns-auth and pdns-rec record `kind`. The other five programs appear under kind `not-recorded`. They
   were not classified by keyword.
2. knot rows do carry `dnssec_related`, although the brief says they do not. The recorded values are used.
3. Some CVE rows name a release candidate as `fix_tag`: four included unbound fixes and all twelve disputed unbound
   rows. The counts are generated in `normalisation_counts`. The recorded `latency_days` is kept as the headline, as the
   brief requires, and `latency_days_stable`, measured to the first stable release, is reported beside it. Question 8
   always uses the stable release. CVE-2017-15105 is the exception: it keeps the vendor 1.6.8 date because the clone's
   1.6.8 tag is a bare re-tag.
4. NSD_2_3_0_REL uses the row's own release-commit instant, 2005-05-02T11:49:23Z.

| program | default rows | of which default changes | CVE included | CVE excluded | CVE disputed | stable releases |
|---|---|---|---|---|---|---|
| bind9 | 30 | 29 | 149 | 58 | 0 | 444 |
| knot | 21 | 21 | 4 | 9 | 0 | 174 |
| kresd | 18 | 18 | 14 | 2 | 0 | 89 |
| nsd | 7 | 7 | 13 | 1 | 0 | 130 |
| opendnssec | 15 | 15 | 0 | 1 | 0 | 65 |
| pdns-auth | 10 | 10 | 15 | 0 | 0 | 132 |
| pdns-rec | 22 | 18 | 52 | 0 | 0 | 174 |
| unbound | 31 | 31 | 65 | 2 | 12 | 120 |

Recompute: `python3 scripts/cross_program.py && python3 -c "import json;d=json.load(open('out/analysis/cross_program.json'));print(json.dumps(d['row_counts'],indent=1));print(d['normalisation_counts'])"`

The pdns-rec release count drops the aliases rec-3-0 and rec-3-0-1. Five rows are kept for question 1 but are not
default changes, so they stay out of questions 3, 4 and 8. They are bind9 d22, whose `value_changed` is false, and
pdns-rec dnssec-setting-introduced, trust-anchor-ta-nta-management, ed25519-validation and revoked-dnskey-rejected,
whose `is_default_change` is false.

## Question 1: mechanism matrix

The matrix has 63 filled cells, one per mechanism, program and kind. Each cell gives the earliest stable release,
its date, the row id, and every row id in the cell. It is in `cross_program_q1_mechanism_matrix.csv`. A blank cell
means that no row exists. It does not mean the program never supported the mechanism: the timelines record support
only where it came with a default change. For example, kresd delegates algorithm support to libknot, and NSD does
not sign. A blank or a later row does not mean later adoption.

This table shows the earliest row by mechanism. It is not necessarily the first time any program did it:

| mechanism | program with the earliest row | release | date | row |
|---|---|---|---|---|
| validation | unbound | release-0.5 | 2007-09-25 | unbound[0]@0.5 |
| nsec3-iterations | unbound | release-0.5 | 2007-09-25 | unbound[1]@0.5 |
| alg-ecdsa | unbound | release-1.4.17 | 2012-05-18 | unbound[9]@1.4.17 |
| alg-ecdsa, signing default | knot | v2.1.0 | 2016-01-14 | knot[2]@2.1.0 |
| ds-digest | unbound | release-1.6.2 | 2017-04-13 | unbound[14]@1.6.2 |
| cds-cdnskey | knot | v2.8.0 | 2019-03-05 | knot[10]@2.8.0 |
| trust-anchor-5011 | unbound | release-1.4.7 | 2010-11-05 | unbound[12]@1.4.7 |

The cds-cdnskey row is not the start of CDS publication. knot[10] narrows publication to rollovers, and its before
text says publication was the default from 2.5.0.

bind9 d10-dsa-removed is now under mechanism `other`. bind9 d23 now counts as a default change.

Recompute: `python3 scripts/cross_program.py --only q1_mechanism_matrix && python3 -c "import csv;[print(r['mechanism'],r['program'],r['kind'],r['first_stable_tag'],r['first_stable_date'],r['row_id']) for r in csv.DictReader(open('out/analysis/cross_program_q1_mechanism_matrix.csv'))]"`

## Question 2: code lag behind RFC publication

Q2 uses every row whose recorded `rfcs` field names a checklist RFC. That includes support-added and limit-changed
rows, not only default changes. The lag is the release date minus the checklist `publication_date`, in months of 30.44
days. For pdns-rec rows whose tag never shipped publicly, the public release is used. Each program is represented by
the first row, of any kind, that cites the RFC. That is not necessarily first support.

bind9 rows have no `rfcs` field, so bind9 is absent from the main table. Four bind9 rows name RFC 5011 or RFC 9276 in
their own text, and the derived sensitivity below includes them.

Nine rows cite RFCs that are not in the checklist: RFC 8145, RFC 8509, RFC 7646, RFC 6725 and RFC 8020. They include
the new bind9 rows d29 and d30, and they are listed under `rows_citing_rfcs_not_in_checklist`.

| RFC | published | order: program, date, lag in months | spread first to last, months |
|---|---|---|---|
| RFC 4033 | 2005-03 | nsd 2005-05-02 2.0; unbound 2007-09-25 30.8; pdns-rec 2016-07-08 136.2 | 134.2 |
| RFC 4034 | 2005-03 | nsd 2.0; unbound 30.8; pdns-rec 136.2; opendnssec 2017-02-22 143.8 | 141.7 |
| RFC 4035 | 2005-03 | nsd 2.0; unbound 30.8; pdns-rec 136.2 | 134.2 |
| RFC 4509 | 2006-05 | opendnssec 129.8; unbound 131.4; knot 154.1; kresd 190.5 | 60.7 |
| RFC 5011 | 2007-09 | unbound 2010-11-05 38.1, unbound[12]; kresd 125.0; pdns-rec 157.4 | 119.3 |
| RFC 5155 | 2008-03 | unbound -5.2; nsd 3.7; opendnssec 26.8; pdns-auth 64.1; knot 101.3; pdns-rec 117.1; kresd 157.0 | 162.2 |
| RFC 5702 | 2009-10 | unbound -3.9; opendnssec 17.5; pdns-auth 39.6; knot 68.8 | 72.7 |
| RFC 5933 | 2010-07 | unbound 4.2 | none |
| RFC 6605 | 2012-04 | unbound 1.5; knot 45.4; pdns-auth 51.2, pdns-auth[7] | 49.7 |
| RFC 6840 | 2013-02 | pdns-rec 132.1; unbound 132.4 | 0.2 |
| RFC 7344 | 2014-09 | knot 54.1 | none |
| RFC 8080 | 2017-02 | pdns-rec 4.3 | none |
| RFC 8198 | 2017-07 | kresd 7.0; pdns-rec 46.3; unbound 55.1 | 48.1 |
| RFC 8624 | 2019-06 | pdns-auth -34.8, pdns-auth[7]; knot -20.0; unbound 8.7; pdns-rec 48.9 | 83.7 |
| RFC 9077 | 2021-07 | knot 1.0; unbound 39.5 | 38.5 |
| RFC 9276 | 2022-08 | pdns-auth -12.6; unbound -11.9; knot 0.7; pdns-rec 17.3; kresd 18.4 | 31.1 |

Nine rows have negative lags, and they come down to six program and RFC pairs:

- unbound shipped NSEC3 and RSASHA256 from drafts, which accounts for RFC 5155 and RFC 5702.
- The unbound and pdns-auth entries for RFC 9276 are the 2021 cross-vendor iteration caps, which the RFC codified
  after the fact.
- pdns-auth and knot have RFC 8624 entries. These are defaults that the RFC later endorsed, cited retroactively by the
  timeline.

Chance baseline for being first: in each RFC contest with k programs, a program comes first by chance with
probability 1/k. RFC 4033, 4034 and 4035 are decided by the same row, nsd[2], so they count as one contest. In the
merged variant, unbound comes first 4 times against 3.34 expected, with p = 0.44. No program comes first
significantly more often than chance.

### bind9 derived sensitivity

This is derived, not recorded data. It is in `bind9_derived_sensitivity` and `cross_program_q2_bind9_derived_sensitivity.csv`.

| RFC | bind9 row | rule | date | lag, months | position in the sensitivity order |
|---|---|---|---|---|---|
| RFC 5011 | d04-root-trust-anchor-builtin | text-cited | 2011-02-21 | 41.7 | 2nd of 4, after unbound at 38.1 |
| RFC 9276 | d18-nsec3param-default-0-0 | text-cited | 2022-01-24 | -6.2 | not bind9's earliest, see l01 |
| RFC 9276 | l01-nsec3-max-iterations-150 | mechanism analogue, the fixed 150 cap, like unbound[20] and pdns-auth[10] | 2021-05-12 | -14.7 | 1st of 6 |
| RFC 5155 | d03-signzone-nsec3-iterations-100-to-10 | mechanism analogue | 2010-02-16 | 23.6 | 3rd of 8 |
| RFC 6605 | d15-dnssec-policy-default-ecdsap256 | mechanism analogue | 2020-02-12 | 94.4 | 4th of 4; the spread becomes 92.8 |

The new unbound row, unbound[12]@1.4.7, puts unbound ahead of bind9 d04 for RFC 5011. The Phase 5 remark that bind9
would lead RFC 5011 therefore no longer holds.

With the sensitivity included, bind9 leads only RFC 9276, and only through the mechanism analogue. The chance result
does not change:

- With all derived rows, bind9 comes first 1 time in 4 contests against 0.79 expected, and unbound 4 times in 11
  against 3.13, with p = 0.38.
- With text-cited rows only, bind9 comes first 0 times.
- No program is called a leader in any variant.

Recompute: `python3 scripts/cross_program.py --only q2_code_lag_vs_rfc && python3 -c "import json;d=json.load(open('out/analysis/cross_program.json'))['q2_code_lag_vs_rfc'];[print(r['rfc'],r['spread_months_first_to_last'],[(o['program'],o['date'],o['lag_months'],o['row_id']) for o in r['order']]) for r in d['per_rfc']];print(d['first_to_ship_chance_baseline']['per_program_same_row_merged']);s=d['bind9_derived_sensitivity'];print(s['orders_that_change'],s['called_leader'])"`

## Question 3: default-flip topics

A row enters a topic only if two things hold: its mechanism is in the topic's set, and an evidence regex matches its
title, before and after text. The script asserts both for every assignment. The table `TOPICS` in the script lists
every assignment, every considered but rejected row with its reason, and every program with no row. Each topic is
split into sub-milestones, which are like-for-like events. A context sub holds rows that belong to the topic but are
not comparable. The full membership list, with the matched evidence text, is in `cross_program_q3_topics.csv`.

| topic and sub-milestone | bind9 | knot | kresd | opendnssec | pdns-auth | pdns-rec | unbound |
|---|---|---|---|---|---|---|---|
| ECDSA P-256 signing default | 2020-02-12 d15 | 2016-01-14 knot[2] | | no row | 2016-07-08 pdns-auth[7],[8] | | |
| NSEC3 signer iterations 0 | 2022-01-24 d18; 2022-07-07 d21 | 2022-08-22 knot[14] | | no row | 2022-01-24 pdns-auth[11] | | |
| NSEC3 signer salt empty | 2022-01-24 d18 | 2025-09-18 knot[18] | | | 2022-01-24 pdns-auth[11] | | |
| NSEC3 iteration cap 150 or lower | 2021-05-12 l01 | | 2021-03-31 kresd[9] | | 2021-07-12 pdns-auth[10] | 2021-06-07 nsec3-max-iterations-150 | 2021-08-05 unbound[20] |
| NSEC3 iteration cap 50 or lower | 2024-07-08 l02 | | 2024-02-13 kresd[12],[15] | | | 2024-01-09 public rec-5.0.1, tag rec-5.0.0 2023-12-18 | |
| validator on, anchor must be configured | 2008-05-28 d01 | | | | | | 2007-09-25 unbound[0] |
| validates out of the box | 2019-03-20 d07 | | 2019-04-18 kresd[6] | | | 2021-05-10 public rec-4.5.1, dnssec-default-process | no row |
| built-in root anchor available | 2011-02-21 d04 | | 2019-04-18 kresd[6] | | | built in from rec-4.0.0, no row | 2010-11-05 unbound[12] |
| KSK-2017 20326 added | 2017-03-29 d05 | | no row | | | 2017-06-13 root-ds-2017-added | 2017-02-14 unbound[13] |
| KSK-2010 19036 removed | 2019-04-06 d23 | | no row | | | 2019-07-12 root-ds-19036-removed | 2020-07-20 unbound[19] |
| KSK-2024 38696 added | 2024-12-03 d24 | | 2024-07-23 kresd[14],[17] | | | 2025-01-10 root-ds-38696 | 2024-08-09 unbound[25] |
| RFC 8145 signalling on | 2016-09-29 d29 | | 2017-11-02 kresd[1] | | | | 2017-10-10 unbound[15] |
| RFC 8509 sentinel on | 2018-07-03 d30 | | 2018-01-31 kresd[3] | | | | 2018-04-26 unbound[16] |
| signer default algorithm moves off RSASHA1 | 2018-01-17 d06 | | | 2011-03-18 opendnssec[5] | 2013-01-17 pdns-auth[0] | | |
| SHA-1 DS no longer generated | 2020-02-12 d13; 2022-01-24 d20 | 2019-03-05 knot[11] | | 2017-02-22 opendnssec[13] | | | |
| SHA-1 refused by crypto policy handled | | 2020-11-11 knot[12] | | | | 2023-06-29 dnssec-disabled-algorithms-auto | 2022-07-04 unbound[22] |
| CDS/CDNSKEY publication narrowed to rollover | no row | 2019-03-05 knot[10] | | no row | no row | | |

NSD has no row in any topic. It does not sign, and it has no iteration cap.

The KSK-2010 row for bind9 d23 is matched on its text, "revoked key removed". The row does not name key 19036. The
Phase 5 report showed from the clone that the revoked key removed at v9.14.1 is KSK-2010.

pdns-auth[10] in the "cap 150 or lower" row is an authoritative-side clamp on the zone's own NSEC3PARAM. The other
four entries in that row are validator caps.

Context rows are kept in the topic but are not milestones:

- bind9 d03 and d17, knot[19], pdns-auth[3] and [4], pdns-rec nsec3-max-iterations-2500 and unbound[1] belong to the
  NSEC3 topic.
- bind9 d07 and kresd[4] belong to the root anchor topic.
- kresd[10] belongs to the SHA-1 topic.

Rejected rows, with reasons in the JSON:

- unbound[9] is validation support.
- unbound[24] caps hash computations, not iterations.
- pdns-auth[1] changes the opt-out flag.
- knot[4] changes re-salting.
- dnssec-default-process-no-validate never validates.
- unbound[14] goes the opposite direction.
- The DSA removals are rejected from the SHA-1 topic. These are bind9 d10, knot[7] and unbound[18]. DSA algorithms 3
  and 6 are SHA-1 based, but the removals were driven by DSA itself, not by the RSASHA1 and SHA-1 DS deprecation that
  this topic tracks.
- bind9 d22 is not a default change.

pdns-auth[5] and [6] are no longer normalised rows, because their stable tag is null.

Two caveats apply. The bind9 d01 date, 2008-05-28, is an embargoed-tag commit date; the public release was
2008-07-08, according to the bind9 verify report. pdns-rec's "process" setting validates only when the client sets
AD or DO.

Recompute: `python3 scripts/cross_program.py --only q3_default_flip_topics && python3 -c "import csv;[print(r['topic'],r['sub'],r['program'],r['row_id'],r['timing_date'],repr(r['evidence'])) for r in csv.DictReader(open('out/analysis/cross_program_q3_topics.csv'))]"`

## Question 4: leader and follower

The leader of a sub-milestone is the program whose first row has the earliest UTC timing instant. The median gap is
the median of the other programs' dates minus the leader's date.

| sub-milestone | k | leader | median gap to the rest, days |
|---|---|---|---|
| ECDSA P-256 signing default | 3 | knot | 833 |
| NSEC3 signer iterations 0 | 3 | tie: pdns-auth and bind9, both 2022-01-24 | 105 |
| NSEC3 signer salt empty | 3 | tie: pdns-auth and bind9, both 2022-01-24 | 666.5 |
| NSEC3 cap 150 or lower | 5 | kresd | 85.5 |
| NSEC3 cap 50 or lower | 3 | pdns-rec | 108 |
| validator on, anchor needed | 2 | unbound | 246 |
| validates out of the box | 3 | bind9 | 405.5 |
| built-in root anchor | 3 | unbound, 2010-11-05 | 1597 |
| KSK-2017 added | 3 | unbound | 81 |
| KSK-2010 removed | 3 | bind9, d23 | 284 |
| KSK-2024 added | 4 | kresd | 133 |
| RFC 8145 signalling on | 3 | bind9, d29 | 387.5 |
| RFC 8509 sentinel on | 3 | kresd | 119 |
| default algorithm off RSASHA1 | 3 | opendnssec | 1584 |
| SHA-1 DS dropped | 3 | opendnssec | 913 |
| SHA-1 crypto-policy handling | 3 | knot | 780 |
| CDS/CDNSKEY publication narrowed | 1 | none, only one program | none |

In the built-in root anchor row, pdns-rec had a built-in root DS from rec-4.0.0, on 2016-07-08, but no default row
records it. It would not change the leader. The two tied contests are left out of the chance baseline.

| program | contests | leads | expected by chance | P of at least that many |
|---|---|---|---|---|
| bind9 | 13 | 3 | 4.28 | 0.86 |
| knot | 3 | 2 | 1.00 | 0.26 |
| kresd | 7 | 3 | 2.12 | 0.36 |
| opendnssec | 2 | 2 | 0.67 | 0.11 |
| pdns-auth | 3 | 0 | 0.87 | 1.00 |
| pdns-rec | 7 | 1 | 2.12 | 0.92 |
| unbound | 9 | 3 | 2.95 | 0.61 |

No program is a leader at the sub-milestone level. bind9, kresd and unbound reach three leads, but none is
significant. kresd's 3 leads are above its expectation of 2.12, with p = 0.36. The smallest p-value in the table is opendnssec's 0.11, from only 2 leads.

The whole-topic level is a coarser view. Its contests include context rows, so a context row can win a topic: unbound[1]@0.5,
the 2007 key-size-dependent cap, wins the NSEC3 topic.

- **Context rows included:** unbound leads 3 of the 4 topics it enters, against 0.81 expected, with p = 0.027. That
  meets the leader rule formally, but it rests on the context row unbound[1] and on the built-in anchor row
  unbound[12]. It is recorded in `programs_called_leader_by_level.topics_with_context_rows`.
- **Milestones only:** the NSEC3 topic passes to kresd, unbound leads 2 topics, and no program is a leader.

The sub-milestone level is the like-for-like comparison, so the conclusion stands: no program is a leader. The
sub-milestones are not independent, so these p-values are, if anything, too small.

Recompute: `python3 scripts/cross_program.py --only q4_leader_follower && python3 -c "import json;d=json.load(open('out/analysis/cross_program.json'))['q4_leader_follower'];[print(r['topic'],r['sub'],r['k'],r.get('leader'),r.get('median_gap_days')) for r in d['sub_milestones']];[print(b) for b in d['baseline_sub_milestones']];print(d['programs_called_leader_by_level'])"`

## Question 5: obsolescence overlap

The checklist has one `obsoleted_by` pair: RFC 8624, published 2019-06, is obsoleted by RFC 9904, published
2025-11-01. No timeline row cites RFC 9904, so when each program shipped the successor cannot be determined.

| program | rows citing RFC 8624 | still the current default | shipped in stable releases after 2025-11-01 |
|---|---|---|---|
| knot | knot[7] 2017-09-29, knot[11] 2019-03-05, knot[12] 2020-11-11 | all three | yes, through v3.6.0 on 2026-09-08 |
| pdns-auth | pdns-auth[7], [8] 2016-07-08 | yes | yes, through auth-5.1.4 on 2026-08-03 |
| pdns-rec | dnssec-disabled-algorithms-auto 2023-06-29 | yes | yes, through rec-5.4.6 on 2026-09-02 |
| unbound | unbound[18] 2020-02-20, unbound[22] 2022-07-04 | both | yes, through release-1.26.1 on 2026-09-16 |

"Still current" means that no later row of the same program changes the same mechanism. The mechanisms `other` and
`validation` are too broad for that test, so those rows were read by hand, and none names the same setting. All
four programs therefore still ship RFC 8624-motivated defaults after RFC 9904's publication. That is not a conflict:
RFC 9904 moves the requirements to IANA registries without reversing them. Deployment of either RFC is Phase 7.

Recompute: `python3 scripts/cross_program.py --only q5_obsolescence && python3 -c "import csv;[print(r['program'],r['row_id'],r['still_current_default'],r['shipped_after_successor_publication'],r['latest_stable_release']) for r in csv.DictReader(open('out/analysis/cross_program_q5_obsolescence.csv'))]"`

## Question 6: CVE fix latency

Latency is the fix release date minus NVD publication. A negative value means the fix shipped before NVD
publication. IQR uses inclusive quartiles. The DNSSEC subset gives the classified rows first, then the rows with a
latency, then the median and IQR over the rows with a latency.

| program | included | with latency | excluded by reason | median | IQR | public-date median, n | DNSSEC subset: rows, with latency, median, IQR |
|---|---|---|---|---|---|---|---|
| bind9 | 149 | 135 | not-applicable-or-not-bind9-release 32, not-found 26 | -13 | -21 to -9 | none | not classified |
| knot | 4 | 4 | not-applicable 9 | -148, see below | -462 to -87.75 | none | 1, 1, -112 |
| kresd | 14 | 14 | no fix tag 1, not-applicable 1 | -4.5 | -22.5 to -1 | none | 7, 7, -1, -6 to -0.5 |
| nsd | 13 | 13 | no fix tag 1 | -1 | -8 to 0 | none | 0 |
| opendnssec | 0 | 0 | no fix tag 1 | none | none | none | 0 |
| pdns-auth | 15 | 10 | none | -8.5 | -34.75 to -0.75 | -2, n=3 | 0 |
| pdns-rec | 52 | 46 | none | -20 | -37.5 to -3.25 | -2, n=4 | 14, 13, -8, -20 to -3 |
| unbound | 65 | 52 | no fix tag 1, not-applicable 1 | 0 | 0 to 0 | none | 17, 14, 0, 0 to 0 |

knot's median of -148 rests on n = 4, with latencies of -1296, -184, -112 and -15 days. It mostly measures NVD's
delay in publishing old knot CVEs, not knot's fix speed, and it is not comparable to bind9's n = 135.

Pooled over all rows with a latency, n = 274, the median is -10 days, with an IQR of -20 to -0.25.

The twelve disputed unbound rows form a separate group. Their median is -509 days, because NVD published the X41
audit CVEs in 2021.

latency_days_stable differs from the recorded latency only for three unbound rows:

- CVE-2009-3602: 31 recorded, 41 stable.
- CVE-2020-28935: -13 recorded, -4 stable.
- CVE-2024-33655 has no NVD date.

The medians do not change. Included rows without latency are listed per program in the JSON. Most lack an NVD date;
the four pdns-rec rows before 2010 were deliberately left null because of tag artefacts. The pdns-rec changelog
public text is reported beside the tag date in `cross_program_q6_cve_latency.csv`.

Recompute: `python3 scripts/cross_program.py --only q6_cve_latency && python3 -c "import json;[print(r['program'],r['n_included'],r['n_excluded_by_reason'],r['latency_days_median'],r['latency_days_iqr'],r['latency_days_public_median'],r['dnssec_subset']) for r in json.load(open('out/analysis/cross_program.json'))['q6_cve_latency']['per_program']]"`

## Question 7: release cadence

Counts are stable releases per calendar year; the per-year counts are in `cross_program_q7_release_cadence.csv`.
The raw median is taken over intervals between consecutive stable releases in UTC order. The collapsed median first
reduces the releases to one event per UTC calendar day, so parallel branches shipped together count once. Each decade
is the decade of the later release.

| program | stable releases | release days, UTC | raw median, days | collapsed median, days | collapsed 2000s | collapsed 2010s | collapsed 2020s | intervals under 24 h |
|---|---|---|---|---|---|---|---|---|
| bind9 | 444 | 242 | 3.39 | 30 | 49 | 30 | 28 | 208 |
| knot | 174 | 157 | 30.04 | 34 | none | 34 | 34 | 18 |
| kresd | 89 | 82 | 35.05 | 37 | none | 27 | 46.5 | 7 |
| nsd | 130 | 119 | 64.09 | 68.5 | 73 | 64 | 70 | 14 |
| opendnssec | 65 | 60 | 51.95 | 61 | none | 46.5 | 136 | 5 |
| pdns-auth | 132 | 112 | 35.10 | 50 | 41 | 69 | 39 | 21 |
| pdns-rec | 174 | 117 | 16.03 | 34.5 | 142 | 49.5 | 30 | 63 |
| unbound | 120 | 118 | 55.15 | 56 | 24 | 58.5 | 63 | 2 |

Raw decade medians are in the JSON under `per_decade_median_days`. Use the collapsed medians for any cross-program
comparison. Raw medians count maintained branches, which makes bind9 and pdns-rec look five to ten times faster. When
collapsed, the order runs:

- bind9 30
- knot 34
- pdns-rec 34.5
- kresd 37
- pdns-auth 50
- unbound 56
- opendnssec 61
- nsd 68.5

pdns-rec's counts include three tags that were never released publicly: rec-4.5.0, rec-4.5.3 and rec-5.0.0.
`total_entries` is not compared.

Recompute: `python3 scripts/cross_program.py --only q7_release_cadence && python3 -c "import json;d=json.load(open('out/analysis/cross_program.json'))['q7_release_cadence'];[print(r['program'],r['n_stable'],r['n_release_days_utc'],r['median_days_between'],r['median_days_between_collapsed'],r['per_decade_median_days_collapsed'],r['n_intervals_under_24h']) for r in d['per_program']]"`

## Question 8: coordinated releases

A coordinated pair is two different codebases shipping a stable release with the same label within 3 days, measured
as UTC instants. A label is either a CVE fixed by both or a question 3 topic shipped by both. pdns-auth and pdns-rec
count as one codebase. The headline statistic counts distinct release pairs, so KeyTrap's two CVEs in the same
releases count once. For the null, each codebase's events are circularly shifted by one uniform offset within its
own stable-release span. There are 1,000 draws with seed 20260929. The corrected data gives 374 events, up from 370.

Observed pairs, using tag dates:

| label | codebase A | date | codebase B | date | gap in days |
|---|---|---|---|---|---|
| topic nsec3-iterations-rfc9276: bind9 d18 and pdns-auth[11] | bind9 v9.18.0 | 2022-01-24T20:04Z | pdns auth-4.6.0 | 2022-01-24T11:00Z | 0.38 |
| CVE-2023-50387 and CVE-2023-50868 | bind9 v9.18.24 | 2024-02-11 | kresd v5.7.1 | 2024-02-13 | 2.06 |
| CVE-2023-50387 and CVE-2023-50868 | bind9 v9.18.24 | 2024-02-11 | unbound release-1.19.1 | 2024-02-13 | 2.06 |
| CVE-2023-50387 and CVE-2023-50868 | kresd v5.7.1 | 2024-02-13 | unbound release-1.19.1 | 2024-02-13 | 0.00 |

| statistic | observed | null mean | null 95th percentile | percentile | p, share of draws at or above |
|---|---|---|---|---|---|
| distinct release pairs, the headline | 4 | 0.24 | 1 | 100.0 | 0.001 |
| CVE label pairs | 6 | 0.01 | 0 | 100.0 | 0.001 |
| topic label pairs | 1 | 0.23 | 1 | 88.6 | 0.21 |

The CVE coordination is real, and it is one event: the KeyTrap embargo of February 2024. pdns-rec's rec-5.0.2 tag,
dated 2024-02-06, falls outside the window. Its changelog gives 13 February 2024 as the public date, and with that
date pdns joins the cluster. That variant has 7 release pairs, also with p = 0.001.

The single topic coincidence is not a finding: bind9 9.18.0 and pdns-auth 4.6.0 both moved NSEC3 defaults to 0
iterations on the same day, 2022-01-24, but that cannot be told apart from the null.

CVE-2020-28935 is a near miss. NSD 4.3.4 and unbound 1.13.0rc1 both shipped it on 2020-11-24, but the first stable
unbound release is 1.13.0, on 2020-12-03, so it does not count.

Recompute: `python3 scripts/cross_program.py --only q8_coordinated_releases && python3 -c "import json;d=json.load(open('out/analysis/cross_program.json'))['q8_coordinated_releases'];[print(n,k,t) for n,v in d['variants'].items() for k,t in v['tests'].items()]"`

## Cross-check against software_support.json, Arc A

The check is in `xcheck_software_support` and `cross_program_xcheck_software_support.csv`. There are 2
disagreements, reported and not resolved.

1. Arc A gives unbound's first NSEC3 validation as 0.7.1, on 2007-11-19. The timeline row unbound[1]@0.5 has NSEC3
   and its iteration cap at release-0.5, on 2007-09-25. The clone supports the timeline:
   `git -C out/software_repos/unbound.git ls-tree -r --name-only release-0.5 | grep val_nsec3` lists
   validator/val_nsec3.c. Arc A marks its own row approximate.
2. Arc A's knot 3.1.5 "config check on the default NSEC3 iteration count" has no timeline default row at v3.1.5. It
   is a configuration check, not a default change.

Every other Arc A row agrees on release date. This includes pdns-auth 4.5.0 on 2021-07-12, a stable date that the
timeline row reaches only through `stable_tag`.

## Suspect rows

There are no open suspect rows. The three rows raised in the first version were confirmed by Phase 5 and corrected in
the timeline data in commit 54400276. They are listed under `resolved_suspect_rows`:

- bind9 d10-dsa-removed: its mechanism changed from `alg-rsa-sha2` to `other`.
- pdns-auth[5] and [6]: their `stable_tag` changed from auth-4.0.0 to null.

## What could not be determined

- bind9's RFC lags from recorded data, because bind9 rows carry no `rfcs` field. Only a derived sensitivity is
  given.
- bind9's DNSSEC CVE subset, because it is not classified.
- When any program shipped RFC 9904, because no row cites it.
- The CDS/CDNSKEY topic has one program, knot, so it has no leader and no gap.
- The first date on which any program published CDS by default is not in the rows. knot's before text says 2.5.0,
  and bind9's publication start is a gap in its timeline.
- OpenDNSSEC's CVE latency, because its one CVE has no fix tag.
- Public dates exist for only 3 pdns-auth and 4 pdns-rec CVE rows, so public-date medians rest on very few rows.
