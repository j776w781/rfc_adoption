# Do software updates drive the adoption rates?

The question this project kept circling: BIND, Unbound, PowerDNS, Knot and
OpenDNSSEC ship constantly, and almost no operator implements DNSSEC themselves.
If adoption is really a story about software updates rather than about operators
reading RFCs, it should show up as adoption moving when releases land.

The short answer is that **availability demonstrably does not move it, and the
data cannot show whether defaults do.** The reasons are worth setting out,
because two of them are properties of the corpus rather than of the world.

Analysis `scripts/release_vs_adoption.py`, output
`out/analysis/release_vs_adoption.json`. Three candidate explanations for when a
mechanism started spreading:

    RFC published  ->  a signer can publish it  ->  it is the default  ->  zones move

## Which population these rates come from

This matters more than it sounds, and an earlier version of this document got it
wrong.

- **Reverse**: the strict **AFRINIC + ARIN** panel, `P(value | signed
  delegations)`, from `out/panel_run`. Summing the five RIRs instead
  double-counts names present in more than one, which
  [full_run_findings.md](full_run_findings.md) flagged. That error moved every
  crossing date — ECDSA read 2017-08 summed against **2018-06** on the panel, and
  RSA/SHA-1 read 2009-03 against **2011-05**. The panel is the population
  `out/analysis/adoption_measures.json` uses, so the crossings here now match the
  project's published adoption dates exactly.
- **Forward**: the seven forward TLDs of the full run, `out/server_run`. These
  are disjoint zones, so pooling them is exact.

The strict panel **starts 2011-05** and held 32 signed delegations then. That
single fact removes several tests below.

## Availability moves nothing

Event study around each release that first let a signer publish a value — mean
monthly change in share, twelve months either side:

| Observable | corpus | Release | share at event | before | after | change |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| alg 13/14 | reverse | PowerDNS 3.0.1 (2012-01) | 0.00% | 0.000 | 0.000 | **0.000** |
| alg 15/16 | reverse | Knot 2.6.0 (2017-09) | 0.00% | 0.000 | 0.000 | **0.000** |
| alg 15/16 | forward | Knot 2.6.0 (2017-09) | 0.00% | 0.000 | 0.000 | **0.000** |
| digest 4 | reverse | PowerDNS 3.0.1 (2012-01) | 0.00% | 0.000 | 0.000 | **0.000** |

**Every one is exactly zero, before and after.** For each of these, the share is
still 0.00% a full year after the software could publish the value. This is the
one result here that is not fragile: it holds on both corpora, on the strict
panel, and it agrees with the onset decomposition in
[software_crossref.md](software_crossref.md), which found code lag near zero and
deployment lag in years.

Shipping the capability is not an event in the deployment record. It is a
precondition and nothing more.

## Defaults are closer in time, on two cases

Time from each candidate date to the month the value first crossed 1%:

| Observable | corpus | 1% at | from RFC | from first signer | from default change |
| --- | --- | --- | ---: | ---: | ---: |
| alg 13/14 | reverse | 2018-06 | 5.33 y | 5.58 y | **1.58 y** |
| alg 13/14 | forward | 2016-10 | 4.50 y | 4.75 y | **0.75 y** |
| alg 15/16 | forward | 2020-05 | 3.25 y | 2.67 y | — |
| digest 4 | reverse | 2018-06 | 6.17 y | 6.42 y | — |
| digest 4 | forward | 2019-09 | 7.42 y | 7.67 y | — |

Where a default change exists it is three to six times closer to the crossing
than the RFC. It also **led** rather than followed: Knot switched its default to
ECDSA P-256 in 2.1.0 (2016-01) when ECDSA stood at 0.25% of panel signed
delegations, and PowerDNS 4.0.0 followed in 2016-07 at 0.72%. Neither vendor was
ratifying something already popular.

That is two observations, both of the same algorithm.

## And no event study confirms it

| Observable | Default change | share at event | before | after | change |
| --- | --- | ---: | ---: | ---: | ---: |
| alg 13/14 | Knot 2.1.0 (2016-01) | 0.25% | 0.021 | 0.055 | +0.034 |
| alg 13/14 | PowerDNS 4.0.0 (2016-07) | 0.72% | 0.060 | 0.017 | −0.043 |

**Neither shows an effect.** Both changes are followed by monthly growth within a
few hundredths of a percentage point of what preceded them.

Three further events had to be discarded rather than read, because **a bounded
share series must decelerate as it approaches its ceiling**: Knot 2.0.0 fires at
65.8% share, BIND 9.16.0 at 25.1% (reverse) and 51.5% (forward). BIND 9.16.0
shows −2.33 pp/month in the forward corpus for reasons that have nothing to do
with the release. Reporting those as a release slowing adoption would be an
artefact of the measure.

BIND's is not a comparable event anyway: `dnssec-policy` is **opt-in**. An
operator must write `dnssec-policy default;` to get the ECDSAP256SHA256 CSK, so
unlike the Knot and PowerDNS rows it does not propagate silently on upgrade.

### A withdrawn result

An earlier version of this analysis reported OpenDNSSEC 1.2.0 (2011-03) as
followed by a **seventeen-fold jump** in monthly growth of RSA/SHA-256, and
presented it as the one confirmed case of a default change moving adoption.

It was an artefact of the summed-RIR population. On the strict panel the series
begins **2011-05**, two months *after* that release, so there is no before-period
and no event study to run. RSA/SHA-256 is already at 3.1% in the panel's first
month, which makes it left-censored for this purpose entirely. The claim is
withdrawn; nothing replaces it.

## Why the decisive test cannot be run here

The two ECDSA default changes land in 2016-01 and 2016-07.

- The **forward corpus starts 2016-06**, so it has no before-period for either.
- The **reverse panel** covers the window but its operators lag the ecosystem by
  years — which is why ECDSA is still at 0.25% there in 2016 and does not cross
  1% until 2018-06.

So the corpus that would show the effect cannot see the event, and the corpus
that can see the event is not where the effect would appear. That is the whole
difficulty, and no amount of care with the existing data removes it.

## What this supports, and what it does not

**Supported.** Shipping a capability does not move deployment. Four of four
first-availability releases are followed by exactly zero change, with the share
still at 0.00% a year later.

**Not established either way.** Whether default changes drive adoption. The
timing is suggestive on two cases and the direction is right — vendors moved
before the rise, not after — but neither event study detects anything, and the
one case that appeared to was a population error.

**Not supported.** "Software updates drive adoption rates" as a general claim.
Nothing in this record demonstrates it. It remains the most plausible mechanism
by which an operator's behaviour changes without an operator deciding anything,
which is a statement about plausibility, not evidence.

A further reason to be careful with any statistic here: the jump analysis in
[software_crossref.md](software_crossref.md) showed a handful of registry
operators moving six-figure blocks of names in single months, every jump paired
across the two TLDs of one operator. An event study over that population measures
whether a dozen organisations happened to move, not whether a market responded.

**The consistent story across all three analyses** — onset decomposition, the
jump pairing, and this one — is that the binding constraint sits with **operators
and the platforms they run**, not with implementers and not with the IETF. This
analysis narrows where the evidence for that is: it is in the onset decomposition
and the operator pairing, not in release-event timing.

## What would settle it

- **Forward-corpus coverage before 2016-06.** The single highest-value gap: it
  would give a real before-period for both ECDSA default changes, in the corpus
  where the operators actually modernised.
- **Per-zone software identification.** Nothing in published zone data says what
  signed it. Version fingerprinting or registry disclosure would turn every
  alignment here into an attribution.
- **More default changes to test.** Seven are identified across five projects in
  seventeen years; two are usable. That is the sample size, and no amount of care
  with the existing corpora enlarges it.
