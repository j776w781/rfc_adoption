# Did a program's release cause the spikes? Five RFC case studies

`scripts/program_rfc_cases.py` -> `out/analysis/program_rfc_cases.json`,
`dns_program_rfc_spikes.csv`, `dns_program_rfc_new_signings.csv`;
`reporting/program_rfc_cases.py` -> `reporting/charts/cases/`;
`reporting/make_program_cases_deck.py` -> `out/analysis/dnssec_program_rfc_cases.pptx`.

## The question

For an RFC, line up on one axis: its publication; the release in which each
program (BIND 9, Knot DNS, PowerDNS Auth, OpenDNSSEC as signers; Unbound, Knot
Resolver, PowerDNS Recursor as validators) first implemented it; the release
that made it the default or capped the old value; the first Ubuntu and Debian
packages that carried that release; and the CVEs on the mechanism. Then find
every spike in the OpenINTEL zone files (per TLD) and in reverse DNS (per RIR)
and ask what had just happened in software.

## Method

* **Spike**: month-on-month change of at least the floor (300 zones forward,
  30 reverse), at least 10% of the previous level, and at least 4x the median
  absolute monthly change of the preceding 12 months. Consecutive months merge.
  For RFC 9276 the direction is negative (names with >= 100 iterations vanish).
* **Nearest events**: for each spike, the latest preceding signer release that
  implements or defaults the mechanism, the latest default change, the latest
  validator cap, the latest CVE on the mechanism, and the latest release of any
  of the eight projects, each with its lag in months.
* **Chance rate**: 97% of months contain some DNS release, so a short lag to
  "some release" is meaningless. The fraction of series months lying within 3
  months after a relevant event is reported alongside each count.
* **New vs rolled**: a jump in zones on algorithm X is at most the growth in
  signed zones that month (could be new signings); the remainder are existing
  zones that rolled. An automatic update changes what a newly signed zone gets;
  it never re-signs an existing zone.
* **Auto-update proxy**: from `delegation_changes.parquet`, the share of new
  reverse signings choosing the algorithm per quarter, and in the 12 months
  either side of each default change.
* **OS packages** (`data/software/distro_ships.json`): Ubuntu 16.04-24.04 from
  Launchpad, Debian 11-13 from the Debian tracker, with release dates. Debian
  9 and 10 are no longer served and are not asserted.
* Shares per RIR are hidden where the RIR has under 30 signed delegations;
  the strict AFRINIC+ARIN panel is the reverse share of record.

## Findings

**RFC 6605 (ECDSA).** PowerDNS Auth signed it three months before the RFC
(3.0.1, 2012-01); BIND 9.8.4 five months after; Knot 1.4.0 twenty months
after. Defaults: Knot 2.1.0 (2016-01), PowerDNS 4.0.0 (2016-07), BIND 9.16.0
(2020-02, opt-in dnssec-policy). The first forward move, .se 2016-10
(+17,193), is three months after the PowerDNS default -- but 10,748 of those
zones were rollovers, a deliberate migration. The moves that made ECDSA the
majority in .se (2019-01 +119,500; 2019-06/07 +217,437) were entirely
rollovers, 30-35 months after any default. The .ch wave of 2021-06..11
(+591,333) was new signings that chose ECDSA 96% of the time. Two of 31 spikes
fall within three months of a default, against a 9% forward chance rate. In
reverse DNS, new signings ignored the 2016 defaults (0.2% -> 0.3%, 0.3% ->
0.2%) and stepped around BIND 9.16.0 (22.8% -> 38.8%), which Ubuntu 20.04 and
Debian 11 carried.

**RFC 5702 (RSA/SHA-256).** Adopted before the forward corpus begins (99% of
signed .se zones in 2016-06). Forward spikes are later signing waves that used
it (.se 2017-11 +123,402 new signings). In reverse DNS the share of new
signings choosing it went from 0.9% to 20.0% across OpenDNSSEC 1.2.0's default
(2011-03) and kept rising for two years; BIND 9.7.0 had enabled it 13 months
earlier, so this reads as availability, not one vendor's default.

**RFC 8080 (EdDSA).** No default anywhere, no OS package carrying one. Two
forward episodes, both .se/.nu, both withdrawn: 2020-04..06 (+18,746, 11,718
rolled) and 2023-01..02 (+13,257, 12,748 rolled). Each sits 27 months after
the nearest signer release. CVE-2022-38178 came four months before the second
episode; it is a BIND validator memory leak and not a reason to sign with
EdDSA. Reverse DNS: no spike.

**RFC 5155 (NSEC3).** BIND 9.6.0 shipped it nine months after the RFC;
Unbound validated it before the RFC. The first NSEC3-signed reverse
delegations (RIPE, 21 of them) appear in 2009-07, seven months after BIND
9.6.0; the first CVE on the mechanism (CVE-2009-3602) came three months after
that. Code, deployment and CVEs each followed within a year. The forward corpus opens with NSEC3 at 98% of .se.
The .ch 2021-07..10 spike (+296,470 NSEC3PARAM zones) is the same signing wave
as the ECDSA one and lands in the month of the PowerDNS 4.5.0 and Unbound
1.13.2 caps; it signed with 1 iteration.

**RFC 9276 (NSEC3 iterations).** The one vendor-triggered case. Names with
>= 100 iterations collapsed in 2021-10..11 in every TLD that had them (.nu
12,145 -> 110; .ch 3,618 -> 252; .se 1,476 -> 88), ten months before the RFC,
two to three months after the Unbound 1.13.2 and PowerDNS 4.5.0 caps and two
months after CVE-2021-40083 (Knot Resolver assertion failure on NSEC3 with too
many iterations). All three spikes are within three months of a cap against a
14% chance rate. The RFC codified what validators had already forced.

## Reading

* Spikes are operator decisions (rollovers) or signing waves; neither is an
  update. Defaults act on signing waves silently, years after they changed.
* Only the 2021 iteration cap moved zones on a vendor's schedule, and it did
  so before the RFC.
* No CVE led a push; the one inside a causal chain (CVE-2021-40083) is a
  symptom of the problem the caps fixed.
* In reverse DNS the defaults that reached operators were BIND's, through
  Ubuntu 20.04 and Debian 11; Knot's and PowerDNS's defaults left no trace
  there.

## Limits

The program that signs a zone is never visible; "nearest release" is timing
only. Forward per-zone records are not in this repo, so forward spikes cannot
be attributed to an operator. Reverse DNS is small (25,930 events). Package
dates bound when a default became reachable, not when anyone upgraded. Counts
of 3-31 spikes per RFC make "beats chance" a reading, not a test.
