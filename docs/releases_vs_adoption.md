# Do software updates drive the adoption rates?

The question this project kept circling: BIND, Unbound, PowerDNS, Knot and
OpenDNSSEC ship constantly, and almost no operator implements DNSSEC themselves.
If adoption is really a story about software updates rather than about operators
reading RFCs, it should show up as adoption moving when releases land.

It partly does, and the part that does not is the more useful finding.

Analysis `scripts/release_vs_adoption.py`, output
`out/analysis/release_vs_adoption.json`. Three candidate explanations for when a
mechanism started spreading:

    RFC published  ->  a signer can publish it  ->  it is the default  ->  zones move

## Availability moves nothing

An event study around each release that first let a signer publish a value —
mean monthly change in share of signed delegations, twelve months either side:

| Observable | corpus | Release | share at event | before | after | change |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| alg 12 | reverse | BIND 9.6.2 (2010-02) | 0.00% | 0.000 | 0.000 | **0.000** |
| alg 13/14 | reverse | PowerDNS 3.0.1 (2012-01) | 0.00% | 0.000 | 0.000 | **0.000** |
| alg 15/16 | reverse | Knot 2.6.0 (2017-09) | 0.00% | 0.000 | 0.000 | **0.000** |
| alg 15/16 | forward | Knot 2.6.0 (2017-09) | 0.00% | 0.000 | 0.000 | **0.000** |
| digest 4 | reverse | PowerDNS 3.0.1 (2012-01) | 0.00% | 0.000 | 0.000 | **0.000** |
| alg 8/10 | reverse | BIND 9.7.0 (2010-02) | 0.00% | 0.000 | 0.575 | +0.575 |

Five of the six rows show literally nothing — **four distinct releases, and for
each of them the share is still exactly 0.00% a full year after the software
could publish the value.** The single exception is RSA/SHA-256, and even there
the reverse panel held only tens of zones at the time.

This is the same result the onset decomposition reached from the other side: code
lag is near zero, deployment lag is years. Shipping the capability is not an
event in the deployment record. It is a precondition, and nothing more.

## Defaults sit far closer to takeoff than RFCs do

Time from each candidate date to the month the value first crossed 1% of signed
delegations:

| Observable | corpus | 1% at | from RFC | from first signer | from default change |
| --- | --- | --- | ---: | ---: | ---: |
| alg 8/10 | reverse | 2011-04 | 1.50 y | 1.17 y | **0.08 y** |
| alg 13/14 | reverse | 2017-08 | 5.33 y | 5.58 y | **1.58 y** |
| alg 13/14 | forward | 2016-10 | 4.50 y | 4.75 y | **0.75 y** |

RFC dates span 1.5–5.3 years from takeoff and first-availability 1.2–5.6; the
default change spans **0.08–1.58**. Across the three cases where a default change
can be identified, it is between four and six times closer to the crossing than
either of the other two dates.

And the defaults led rather than followed. Knot switched its default to ECDSA
P-256 in 2.1.0 (2016-01) when ECDSA stood at **0.14%** of reverse signed
delegations; PowerDNS 4.0.0 followed in 2016-07 at 0.55%. Neither vendor was
ratifying something already popular.

## But the event studies do not confirm it

The same test applied to the default changes, restricted to those occurring
early enough in a curve for a percentage-point comparison to mean anything:

| Observable | Default change | share at event | before | after | change |
| --- | --- | ---: | ---: | ---: | ---: |
| alg 8/10 | OpenDNSSEC 1.2.0 (2011-03) | 0.76% | 0.064 | 1.108 | **+1.045** |
| alg 13/14 | Knot 2.1.0 (2016-01) | 0.14% | 0.012 | 0.025 | +0.013 |
| alg 13/14 | PowerDNS 4.0.0 (2016-07) | 0.55% | 0.034 | 0.007 | −0.027 |

**One of three.** OpenDNSSEC's default change is followed by a seventeen-fold
jump in monthly growth; the two ECDSA defaults are followed by nothing
measurable within a year.

Three further events had to be discarded rather than read: Knot 2.0.0 fires at
55.8% share, BIND 9.16.0 at 21.7% (reverse) and 51.5% (forward). **A bounded
share series must decelerate as it approaches its ceiling**, so an event late in
a curve inherits a negative delta it did not cause — BIND 9.16.0 shows −2.33 in
the forward corpus purely because ECDSA was already past half the population.
Reporting those as evidence that a release slowed adoption would be an artefact
of the measure.

BIND's is not a comparable event anyway: `dnssec-policy` is **opt-in**. An
operator has to write `dnssec-policy default;` to get the ECDSAP256SHA256 CSK,
so unlike the PowerDNS and Knot rows it does not propagate silently on upgrade.
That distinction is now recorded in the dataset.

## Why the decisive test cannot be run here

The two ECDSA default changes land in 2016-01 and 2016-07. The forward corpus —
the one whose operators actually modernised — **starts 2016-06**, so it cannot
see the before-period for either. The reverse corpus spans the whole window but
its operators lag the ecosystem by years, which is exactly why it shows nothing
in 2016.

So the one place where the hypothesis is most testable is the one place the data
does not reach. Everything above is the honest remainder.

## What this supports, and what it does not

**Supported.** Shipping a capability does not move deployment: five of six
first-availability releases are followed by zero change, and four leave the share
at exactly 0.00% a year later. Whatever moves adoption, it is not the feature
becoming available.

**Suggested, not established.** Default changes sit four to six times closer to
the 1% crossing than RFC publication does, and they precede rather than follow
the rise. That is three data points, and only one of the three shows an
acceleration in the surrounding year.

**Not supported.** "Software updates drive adoption rates" as a general claim.
Two of three interpretable default changes produced no measurable acceleration,
and the population is not one where a diffusion statistic means much: the jump
analysis in [software_crossref.md](software_crossref.md) showed a handful of
registry operators move six-figure blocks of names in single months, and every
jump is paired across the two TLDs of one operator. An event study over that
population measures whether a dozen organisations happened to move, not whether
a market responded.

**The consistent story across all three analyses** — onset decomposition, the
jump pairing, and this — is that the binding constraint sits with **operators and
the platforms they run**, not with implementers and not with the IETF. Software
defaults are the most plausible channel by which an operator's behaviour changes
without an operator deciding anything, and the timing is consistent with that.
Proving it needs something this corpus does not contain.

## What would settle it

- **Forward-corpus coverage before 2016-06**, which would give a real
  before-period for the two ECDSA default changes. This is the single highest-value
  gap.
- **Per-zone software identification.** Nothing in published zone data says what
  signed it. Version fingerprinting, or registry disclosure, would turn every
  alignment here into an attribution.
- **More default changes to test.** Six are identified across five projects in
  seventeen years; three are usable. That is the sample size, and no amount of
  care with the existing corpora enlarges it.
