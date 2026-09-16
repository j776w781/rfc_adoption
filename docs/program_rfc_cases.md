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
  Launchpad, Debian 9-13 from sources.debian.org, with release dates. The
  auto-update test is run around each OS release that carried a
  default-changing version, as well as around the upstream release.
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
reverse DNS, new signings ignored the 2016 defaults on their upstream dates
(0.2% -> 0.3%, 0.3% -> 0.2%) and then stepped four times: 2017Q3, 2019Q1,
2019Q4 and 2020Q3. See "Can a step be attributed to an OS release?" below;
the short answer is no.

**RFC 5702 (RSA/SHA-256).** Adopted before the forward corpus begins (99% of
signed .se zones in 2016-06). Forward spikes are later signing waves that used
it (.se 2017-11 +123,402 new signings). In reverse DNS new signings
choosing it go from 0% in 2010Q4 to 20% in 2011Q2 and 81% in 2012Q2; the step
detector puts the step at 2012Q2, 15 months after OpenDNSSEC 1.2.0 made
RSASHA256 its default and 27 after BIND 9.7.0 shipped it. The 2011 rise is 88
signings across three RIRs with one parent block a third of them. Same
batching as ECDSA, same absence of an identifiable trigger.

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
* New signings switch in sudden batches, months to years after the upstream
  default, and no delivery path can be identified from published records.

## Limits

The program that signs a zone is never visible; "nearest release" is timing
only. Forward per-zone records are not in this repo, so forward spikes cannot
be attributed to an operator. Reverse DNS is small (25,930 events). Package
dates bound when a default became reachable, not when anyone upgraded. Counts
of 3-31 spikes per RFC make "beats chance" a reading, not a test.


## Can a step be attributed to an OS release?

`scripts/os_release_attribution.py` -> `out/analysis/os_release_attribution.json`;
`reporting/os_release_attribution.py` -> `reporting/charts/os_release_attribution.png`.

An earlier version of this document attributed the ECDSA step in new reverse
signings to Debian 9 (2017-06-17), the first OS release carrying both
ECDSA-default signers. That attribution does not hold and has been withdrawn.

* **There is not one step, there are four.** ECDSA steps at 2017Q3, 2019Q1,
  2019Q4 and 2020Q3. Each has an OS release in the preceding year and a
  different one each time: Debian 9, Ubuntu 18.04, RHEL 8 with Debian 10, and
  Ubuntu 20.04. Picking the first and naming Debian 9 was selection.
* **Steps happen without OS releases.** Of the five RSA/SHA-256 steps, those
  at 2012Q2 and 2014Q1 have no sourced OS release in the twelve months before
  them.
* **OS releases are dense.** 31% of months in the ledger follow some sourced
  OS release within three months, 51% within six, 79% within twelve. That is a
  floor: it counts only Debian, Ubuntu LTS and RHEL, so adding Fedora, Alpine,
  Ubuntu interim and the rolling distributions raises it.
* **Each step is a few operators.** 2017Q3 is 157 signings, 155 of them in
  September 2017, all but two in APNIC, with one parent block 40% of the step
  and an HHI of 0.19 over blocks. That is a handful of operators deciding, not
  a population receiving an update.
* **Most operators could not have received it that way.** Anchored directory
  listings (2026-09-16) show CentOS 7.9, Rocky 8.5 and Rocky 9 base
  repositories carry BIND and neither Knot nor PowerDNS; both come from EPEL.
  BIND gained an ECDSA-default policy in 9.16, which reached that family with
  RHEL 9 on 2022-05-17, five years after the step. FreeBSD ports, Alpine,
  containers, appliances and source builds are not represented in the table at
  all.

What survives: an update changes only what a zone signed after it gets, never
an existing zone, so new signings are where a default would act; and the steps
show operators moving in batches once the defaults existed upstream. Which
path carried a default to any operator is not identifiable from published DNS
records.
