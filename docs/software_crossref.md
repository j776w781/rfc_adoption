# Software releases against observed deployment

Every date in this project so far has been an RFC date or a zone-file date. This
adds a third clock — when the code that can publish or validate a thing was
actually released — and it changes the reading of the first two.

The pipeline could already say ECDSA took 3.6 years to appear. It could not say
whether those years were spent waiting for somebody to write ECDSA, or waiting
for somebody to switch it on. Splitting them turns out to matter more than the
total.

Sources: git history of Unbound, NSD, BIND 9, Knot DNS, Knot Resolver,
OpenDNSSEC, PowerDNS Authoritative and PowerDNS Recursor — 1,083 dated stable
releases. BIND's odd-numbered minors from 9.13 on (9.15, 9.17, 9.19, 9.21) are
development branches and are excluded; counting them dates dnssec-policy's CDS
publication to 9.15.6 in 2019 instead of 9.16.0 in 2020. Data: `data/software/software_support.json`, analysis
`scripts/software_crossref.py`, output `out/analysis/software_crossref.json`.

## Method, and one trap in it

Release dates come from git tags, dereferenced to the commit the tag points at.
The tag object's own date is useless: every tag imported from CVS or SVN carries
the migration day, which dates BIND 9.0.1 to 2012 and all of Unbound before 1.6.3
to a single afternoon in June 2017.

A feature's release is found by locating the introducing commit and taking the
earliest-dated stable tag containing it. Parsing changelog sections does not work
on projects with long-lived parallel branches: BIND keeps one `CHANGES` file per
branch, so the 2012 ECDSA entry sits under a 9.11.0 marker on the branch we
happened to read, four years late.

**The trap.** BIND commit `ca391cd0` (2018-12-05) reads *"Change the default
algorithm to RSASHA256 and the alternative algorithm to RSASHA1"*. Read as a
product default it is a headline: the most widely deployed authoritative server
defaulting to SHA-1 until 2019. Its file list is
`bin/tests/system/conf.sh.in` and `conf.sh.win32` — the system-test fixture.
Every default claim below was checked against the commit's file list for this
reason, and this one was dropped.

## Unbound first, since it is the cleanest record

Unbound is a validating resolver, so it never publishes anything and appears in
none of our zone data. That is precisely what makes it useful: it dates the
*validation* side independently of everything we measure, and its changelog is
the most consistently dated of the eight.

| Observable | Committed | First stable release | RFC | Against the RFC |
| --- | --- | --- | --- | --- |
| NSEC3 | 2007-09-12 | 0.7.1 (2007-11-19) | RFC 5155 (2008-03) | 4 months early |
| RSASHA256/512 | 2008-11-03 | 1.1.0 (2008-11-14) | RFC 5702 (2009-10) | 11 months early |
| GOST | 2009-08-06 | 1.4.0 (2009-11-23) | RFC 5933 (2010-07) | 8 months early |
| RFC 5011 rollover | 2009-09-22 | 1.4.0 (2009-11-23) | RFC 5011 (2007-09) | 2.2 years late |
| ECDSA | 2012-04-13 | 1.4.17 (2012-05-18) | RFC 6605 (2012-04) | same quarter |
| Ed25519 | 2017-05-30 | 1.6.4 (2017-06-22) | RFC 8080 (2017-02) | 4 months late |
| Ed448 | 2018-04-05 | 1.7.1 (2018-04-26) | RFC 8080 (2017-02) | 1.2 years late |
| NSEC3 iteration cap 150 | 2021-05-25 | 1.13.2 (2021-08-05) | RFC 9276 (2022-08) | 1 year early |

Four of eight shipped before the RFC that standardises them, from drafts. Unbound
1.4.17 had ECDSA validation working the month after RFC 6605 was published,
having implemented `draft-ietf-dnsext-ecdsa-04` in February. The first ECDSA
signal anywhere in our corpus is **2015-11**, three and a half years later — and
that is a DS algorithm in the reverse corpus, not a DNSKEY, because the forward
corpus does not start until 2016-06.

Validators were ready before signers for **three of the four signing algorithms**
(RSA/SHA-2, GOST, EdDSA). ECDSA is the exception, and only just: PowerDNS shipped
an ECDSA signer in 3.0.1 (2012-01) on provisional codepoints, four months before
Unbound's ECDSA release. The ordering that never reverses is the other one —
**both sides of the protocol were ready years before any operator used it**, in
all four cases.

## Onset splits into code and deployment, and it is not close

    observable   rfc       published  signer ships   code   first zone  deploy  onset
    alg 8/10     RFC 5702  2009-10    2010-02         0.3    2010-03      0.1    0.4
    alg 12       RFC 5933  2010-07    2010-02        -0.4    2012-12      2.8    2.4
    alg 13/14    RFC 6605  2012-04    2012-01        -0.2    2015-11      3.8    3.6
    alg 15/16    RFC 8080  2017-02    2017-09         0.6    2019-01      1.3    1.9
    CDS/CDNSKEY  RFC 7344  2014-09    2016-07         1.8    2017-10      1.2    3.1

Code lag runs **−0.4 to +1.8 years, median 0.3**. Deployment lag runs **0.1 to
3.8 years**. For the two slowest mechanisms the entire onset is deployment: ECDSA
was publishable by PowerDNS 3.0.1 three months *before* RFC 6605 existed, and the
first zone still took another 3.8 years.

Three of the five were implemented before their RFC was published, from drafts:

| Implementation | Shipped from draft | RFC | Lead |
| --- | --- | --- | --- |
| Unbound 1.1.0 (2008-11) | RSASHA256/512 | RFC 5702 (2009-10) | 11 months |
| Unbound 1.4.0 (2009-11) | `draft-dolmatov-dnsext-dnssec-gost-01` | RFC 5933 (2010-07) | 8 months |
| PowerDNS 3.0.1 (2012-01) | `draft-ietf-dnsext-ecdsa`, provisional codepoints | RFC 6605 (2012-04) | 3 months |
| Knot 2.4.0 (2017-01) | EdDSA constants, *explicitly not signing yet* | RFC 8080 (2017-02) | 1 month |

PowerDNS also had a working Ed25519 signer in **2012-03**, five years early, on
private codepoint 250. It is excluded from the arithmetic — nothing published
under codepoint 250 is an RFC 8080 observation — but it settles the question of
whether the cryptography was the obstacle.

**This refutes the reading the onset bands were given.** `bottom_up.md` groups
observables by "how many parties must implement something new" and finds a clean
ascending order, with new cryptographic primitives slowest because a signer *and*
a validator must both change. The ordering survives. The explanation does not:
implementers were not the slow party in any of the five cases. What the groups
were really ranking is how much work an **operator** has to do, and how likely
that work is to happen without anyone deciding to do it.

## The refinement: how a change reaches a zone

The existing groups (A, B, C, D, G) describe the change. This adds a second axis
describing its **propagation mechanism** — and that is what predicts the
deployment lag.

| Mechanism | What happens | Observed lag | Example |
| --- | --- | --- | --- |
| **Validator-forced** | resolvers stop accepting the old value; the zone changes or goes dark | **2 months** | NSEC3 iterations, 2021 |
| **Registry-automated** | the registry acts on a signal the child publishes | ~2 months | CDS bootstrapping in `.ch`/`.li`, 2021 |
| **Default-on-upgrade** | the new value is what the software does if nobody says otherwise | 3 months – 3 years | ECDSA defaults, 2016 |
| **Opt-in config** | somebody must decide and edit something | 1.3 – 3.8 years | everything else |

The four are ordered by how little human decision each requires, and that
ordering matches the measured lags better than implementation difficulty does.

**Two of these lags are measured and two are inferred.** Validator-forced and
registry-automated are read directly off the series — the zones move, and the
month they move is visible. Default-on-upgrade and opt-in config are the residual
categories: their ranges come from the deployment-lag column above, attributed to
a mechanism we cannot observe, because no zone tells us whether its operator
changed a setting or simply upgraded. Those two rows are the hypothesis this
analysis leaves open, not a result.

### Default changes are dated, and they are the mechanism

| Software | Default change | Release | Date | Verified against |
| --- | --- | --- | --- | --- |
| BIND | NSEC3 iterations 100 → 10 | 9.7.0 | 2010-02-16 | product code |
| OpenDNSSEC | signing algorithm → RSASHA256 | 1.2.0 | 2011-03-18 | product code |
| Knot | signing algorithm → RSASHA256 | 2.0.0 | 2015-06-26 | product code |
| **Knot** | **signing algorithm → ECDSAP256SHA256** | **2.1.0** | **2016-01-14** | `src/dnssec/lib/kasp/policy.c` |
| **PowerDNS** | **ZSK default → ECDSA P-256** | **4.0.0** | **2016-07-08** | `common_startup.cc`, `pdns.conf-dist`, `pdnsutil.cc` |
| PowerDNS | KSK default → ECDSA P-256 | 4.0.0 | 2016-07-08 | `pdnsutil.cc` |
| BIND | `dnssec-policy default` signs with one ECDSAP256SHA256 CSK | 9.16.0 | 2020-02-12 | ISC documentation |

BIND's is the odd one out and is not comparable to the rest: `dnssec-policy` is
**opt-in**. An operator has to write `dnssec-policy default;` to get that CSK, so
it does not propagate silently on upgrade the way the Knot and PowerDNS defaults
do. The dataset records this as `opt_in`, and
[releases_vs_adoption.md](releases_vs_adoption.md) keeps it out of the
default-change comparison for that reason.

Knot and PowerDNS moved their default signing algorithm to ECDSA P-256 within
seven months of each other, in 2016. `.se` shows its first ECDSA jump in **2016-10** —
three months after PowerDNS 4.0.0, with `.nu` moving the same month. That is an alignment, not an
attribution: we cannot see what software any zone runs, and the same operator was
also making its own decisions. It is offered as consistent, not as proof.

## The one place the causal direction is legible

Zone operators cannot be compelled to change an algorithm. They can be compelled
to change an NSEC3 iteration count, because a count above what resolvers accept
stops the zone validating. So this is the one mechanism where the arrow is
readable from outside.

    distinct NSEC3 owner names published with >= 100 iterations, forward corpus

    2021-06   18,077
    2021-07   18,071     <- PowerDNS Auth 4.5.0 caps configurable iterations at 100
    2021-08   17,941     <- Unbound 1.13.2 released 2021-08-05
    2021-09   17,491
    2021-10    3,027     <- -83% in one month
    2021-11      528     <- -97% against August
    2021-12      528     <- Knot 3.1.5 adds a config check
    2022-01      534
                         <- RFC 9276 published 2022-08

An owner name, not a zone: NSEC3 owner names are hashed, so one zone contributes
one name per hashed owner. The zone-level measure is NSEC3PARAM, which sits only
at the apex, and it puts NSEC3 on 98.4% of signed forward zones in 2016-06 and
61.9% by 2023-12. The collapse below is a within-series comparison, so the
percentages hold whichever unit is used.

The Unbound commit that lowered the cap (2021-05-25) says what it is doing:

> *"Move the NSEC3 max iterations count in line with the 150 value used by BIND,
> Knot and ..."*

A cross-vendor agreement, stated in a commit message, **15 months before RFC 9276
was published**. PowerDNS Authoritative had already capped the configurable
maximum at 100 in 4.5.0 (2021-07-12) — the authoritative side of the same
squeeze, limiting what an operator can ask for — and Knot added a config check in
3.1.5 (2021-12-20).

**The zones moved two months after the resolver release and ten months before the
RFC.** RFC 9276 documented a change that had already happened. This is the
explanation for the `predates_rfc` flag and the −6.2 y "negative onset" that
`full_run_findings.md` recorded and could not account for: the question was not
mis-posed, the RFC simply was not the cause.

`.gov` is the control. It sat at 40 such names before the collapse
and 42 after — it never moved, because it was never above the cap.

## Every jump is one operator, and the pairs show it

`full_run_findings.md` established that the big month-on-month jumps are
portfolio moves rather than diffusion, and that the data could not name who. It
can name them, because the corpus contains **two pairs of TLDs sharing a registry
operator**: `.se` and `.nu` are both run by the Swedish Internet Foundation, and
`.ch` and `.li` are both run by SWITCH.

    observable   month    jumped        delta   partner    before     after   partner
    alg 13/14    2016-10  .se         +10,788   .nu            43       900    +1993%
    alg 13/14    2019-01  .se        +119,500   .nu         2,844    21,091     +642%
    alg 13/14    2021-08  .ch        +174,356   .li         2,564     4,446      +73%
    alg 15/16    2020-04  .se          +8,403   .nu             0       411       new
    alg 15/16    2023-01  .se         +10,623   .nu             3       738   +24500%
    CDS          2021-06  .ch         +38,633   .li           928     1,715      +85%
    CDS          2021-11  .ch        +155,150   .li         3,718     5,673      +53%

The right test is not whether both zones clear the jump threshold — `.nu` is
roughly eight times smaller than `.se`, so it often cannot — but whether the
partner moves in the same month. **It does in 20 of 21 jumps**, the single
exception being `.se` 2017-04, where `.nu` was flat.

Both zones of an operator move together, at proportional scale, in the same
month. Two zones moving together is one decision, and the unit of change in this
data is the operator, not the zone.

The `.ch` CDS surge is the clearest single case. SWITCH polls child zones for CDS
records and bootstraps DNSSEC automatically when one appears. In the data, CDS
publication jumps first (14,385 zones publishing CDS in 2021-04 → 100,549 in
2021-07) and signed zones follow (154,190 in 2021-05 → 573,504 in 2021-09).
`.ch` went from 140,506 to 851,003 signed zones during 2021 — a **6x increase in
twelve months**, driven by an RFC 7344 mechanism running unattended on both
sides.

That is the strongest case for automation rather than persuasion moving these
numbers. It also means `.ch`'s 2021 ECDSA jump is *mass signing*, not an
algorithm migration: the zone's whole DNSSEC population tripled. `.se` 2019-01 is
the opposite — total signed zones were *falling* (812,349 in 2018-11 → 745,073 in
2019-01) while ECDSA gained 119,500, which is a migration inside a stable
population. The two must not be pooled.

## Newer RFCs land while the older one is still arriving

Asked directly: on the month a successor RFC was published, what fraction of its
eventual peak had the predecessor reached?

    successor  published  predecessor  at pub    peak    fraction  still spreading
    RFC 5933   2010-07    RFC 5702      0.80%   87.79%      0.01   yes
    RFC 6605   2012-04    RFC 5702     14.20%   87.79%      0.16   yes
    RFC 7344   2014-09    RFC 5702     46.45%   87.79%      0.53   yes
    RFC 7344   2014-09    RFC 5933      0.15%    0.35%      0.43   yes
    RFC 8080   2017-02    RFC 5702     87.76%   87.79%      1.00   no
    RFC 8080   2017-02    RFC 5933      0.11%    0.35%      0.30   yes
    RFC 8080   2017-02    RFC 6605      0.51%   74.06%      0.01   yes

Reverse corpus, `P(algorithm | DS records)`, the only basis spanning 2009–2026.

**Six of seven pairs overlap.** RFC 8080 standardised EdDSA when ECDSA had
reached **1% of the share it would eventually hold** — five years before ECDSA
passed 50%. The standards pipeline runs two to three generations ahead of
deployment, permanently. Any snapshot of this ecosystem contains one mechanism
being retired, one arriving, and one that has been standardised and started
essentially nowhere.

This is also why *"is it adopted yet"* has no answer at the ecosystem level: at
the moment RFC 8080 was published, RSA/SHA-2 was at its peak, ECDSA was at 0.5%,
and GOST was at a third of a peak of 0.35%. Three RFCs, three completely
different states, one date.

## What this cannot show

- **Code lag is a floor.** It is the earliest release among the eight open-source
  implementations whose history can be read. Registry and registrar platforms —
  which the operator evidence says are the actors that matter — are closed, and
  their release dates are not observable.
- **No zone's software is identifiable.** Every alignment between a release date
  and a deployment move is a coincidence in time. The NSEC3 case is the strongest
  because the mechanism is coercive and the direction is forced, but even there
  the specific software each operator ran is unknown.
- **Two of the five first-seen dates rest on the reverse corpus**, whose
  delegation-only records make an algorithm visible as a DS algorithm rather than
  a DNSKEY algorithm. That is the same value by a different route, not the same
  measurement.
- **`.gov` and `fed.us` contribute almost nothing** to the jump analysis: 23,755
  and 10 zones at peak against `.ch`'s 6.2 million.
- **Capability is now partly observable, but only upward.** A release proves the
  code existed; nothing here proves any operator installed it. The
  `vocabulary.md` Layer 4 exclusion on capability is narrowed, not lifted.

## What changes elsewhere in the project

1. **`bottom_up.md` step 3** — the implementation-cost explanation for the onset
   bands should be replaced. The ordering holds; the cause is operator decision
   cost and propagation mechanism, not implementation difficulty. RFC 5218's
   "incrementally deployable" still applies, but it is about deployment, which is
   what the release data now shows directly.
2. **`stages.md`** — onset should be reported split. A single onset averages a
   near-zero code lag with a multi-year operator lag and hides which one moved.
3. **`vocabulary.md` Layer 4** — "Capability: we see what a zone publishes, never
   what its software supports" is too strong now. Software support has a date,
   from the release history; what remains unobservable is which software a given
   zone runs.
4. **`full_run_findings.md`** — the `NSEC3 zero iterations` negative onset now has
   an explanation and should carry it: implementations converged on a limit in
   2021 and RFC 9276 documented it in 2022.

## Provenance, and what was not available

Every software date here is re-derivable offline from a bare clone:

```bash
git clone --bare --filter=blob:none <repo>
git for-each-ref --format='%(*committerdate:short) %(refname:short)' refs/tags
git log --all --grep=<feature>          # commit messages need no blobs
git tag --contains <sha>                # earliest stable tag wins
```

`data/software/software_support.json` carries, for every row, the introducing
commit's SHA and a URL to it, the commit date, the release, and an `attribution`
of `exact`, `earliest-of-several` or `approximate` with an `attribution_basis`
saying in words what is uncertain. An earlier `confidence` field was removed: a
bare "medium" tells a reader nothing about what to distrust.

Every citation is checked to be contained in the release it is cited against.
That check caught three rows citing a master-branch changelog commit for a
feature that had shipped earlier on a maintenance branch — BIND's ECDSA support
read 9.10.0 (2014-04-28) instead of 9.8.4 (2012-09-26), a 19-month error.

**The vendor and platform papers referred to in the request are not in this
repository**, and nothing here is drawn from them. The literature this analysis
does build on is in [prior_work.md](prior_work.md). If those papers cover
registry or registrar platform behaviour, they would bear directly on the operator
findings above — that is exactly the layer this data cannot see — and the
propagation-mechanism table is the part most likely to need revising once they
are read.
