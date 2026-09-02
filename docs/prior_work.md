# What the literature already does, and what of it we can use

Searched before inventing anything further. Four bodies of work are close to what
we are doing; two give us vocabulary and one gives us a boundary, but **the
diffusion literature's thresholds do not transfer**, and the data says why.

## 1. Osterweil, Ryan, Massey, Zhang — IMC 2008

*Quantifying the Operational Status of the DNSSEC Deployment.* The most directly
comparable work: it defines three metrics for DNSSEC deployment.

| Their metric | What it asks |
| --- | --- |
| **availability** | can a resolver actually *receive* the DNSSEC data — middleboxes, MTU, truncation |
| **verifiability** | does the cryptographic verification succeed |
| **validity** | does the data match what the zone administrator *intended* (ground truth) |

They are careful about a distinction we should borrow verbatim: *"verification
refers to the cryptographic process in which a data unit is either verified or
not. Validity, on the other hand, refers to whether the data actually corresponds
to what the zone administrator intended."*

**All three require active resolution.** We read published zone data, so we can
measure none of them. That is not a gap to close later — it is a different
instrument. This triple is the right citation for our "what we do not measure"
layer, and naming it is better than our current hand-rolled wording.

## 2. RFC 5218 — What Makes for a Successful Protocol? (IETF, 2008)

A success-factor framework, not a stage model. It classifies outcomes as
*success* / *failure* / *wild success*, and names the factors that predict them:
fills a real need, **incrementally deployable**, open specification, open code,
free of usage restrictions. It reports that technical quality was *not* a primary
factor in initial success.

"Incrementally deployable" is their term for exactly the mechanism behind our
onset bands. Our Group D — a new signing primitive needing a signer *and* a
validator before anything is publishable — is the non-incrementally-deployable
case, and it is the slow band (2.5–5.8 y). Groups A, B and G each need one party
to change a value it already supports, and they are the fast bands (0.5–1.4 y).
**We should cite RFC 5218 for that argument rather than presenting it as ours.**

## 3. Hovav et al. — Information Systems Journal 14(3), 2004

*A Model of Internet Standards Adoption (ISA): the case of IPv6.* Combines
diffusion-of-innovations with the economics of adoption, and — the part that
matters here — explicitly models **"partial adoption", where old and new
standards coexist for extended periods** rather than one replacing the other.

That is our situation exactly, and it is independent support for the middle stage
we arrived at on our own. We should align the name: their **partial adoption** is
our **partial usage**, and using their term costs nothing and buys a citation.

## 4. Rogers — Diffusion of Innovations

The canonical adopter categories, with thresholds set by standard deviations on a
normal distribution of time-to-adopt: innovators 2.5%, early adopters 13.5%,
early majority 34%, late majority 34%, laggards 16% — cumulative boundaries at
**2.5% / 16% / 50% / 84%**.

This is the obvious candidate to replace our swept 1% / 10%, and it would be
better grounded if it fitted. **It does not**, for a reason the data shows
plainly.

### The test

Rogers' curve is *cumulative adoption*: the fraction of a population that has
ever adopted. It is monotone by construction — it cannot go down — and the
categories partition **adopters by when they joined**. Bass and the logistic
S-curve inherit the same assumption.

Our measure is a **share of a fixed population**: what fraction of signed
delegations use algorithm X *today*. One algorithm's rise is another's fall.
Fitting a logistic to each series:

    series           peak%    when      now%   fallen   shape
    ECDSA P-256      67.95    2026-08   67.95      0%   monotone rise, logistic fits (R2 = 0.939, ceiling 68.6%)
    RSA/SHA-256      74.64    2017-02   22.30     70%   rise and fall - displaced
    RSASHA1-NSEC3    28.99    2018-11    6.46     78%   rise and fall - displaced
    RSASHA1         100.00    2011-05    1.52     98%   rise and fall - displaced
    RSA/SHA-512       3.72    2021-12    0.37     90%   rise and fall - displaced
    Ed25519           0.37    2026-02    0.34      8%   flat: never rose

**Four of six decline from their peak, which cumulative adoption cannot do.**
Only the one mechanism still ascending fits an S-curve at all. Applying Rogers'
2.5/16/50/84 boundaries to a compositional share would classify RSA/SHA-1 as
"late majority" in 2011 and "innovator" in 2026 — the same mechanism moving
backwards through the categories as it is displaced.

So: keep the swept thresholds, and say *why* the standard ones were rejected.
"We tested Rogers' boundaries and they do not apply to a compositional measure"
is a stronger position than either adopting them uncritically or ignoring them.

## What this changes

| Change | Why |
| --- | --- |
| Rename **partial usage** → keep, but cite Hovav's *partial adoption* | independent support for the middle stage |
| Cite **RFC 5218 §2** for the onset bands | "incrementally deployable" is their term for our mechanism |
| Replace our "what we do not measure" wording with **availability / verifiability / validity** | Osterweil's triple, already standard in this literature |
| Keep 1% / 10%, and add the Rogers rejection | the swept thresholds survive a test the canonical ones fail |
| **New: measure displacement** | the literature has no term for rise-and-fall because it assumes monotone adoption; 4 of our 6 series do it, and it is the dominant behaviour in a compositional measure |

That last row is the real gap. Every framework above describes something arriving.
Nothing describes something being pushed out, and in a fixed population that is
half of what happens — the SHA-1 residue, the RSA/SHA-256 decline, the ECC-GOST
disappearance. We already have `residue` for the deprecation case; the general
case needs the same treatment.

## Also relevant, not directly usable

- **Chung et al., USENIX Security 2017** — *A Longitudinal, End-to-End View of the
  DNSSEC Ecosystem.* 21 months of .com/.org/.net plus 59K resolvers; about
  management quality and resolver-side validation rather than timing.
- **Chung et al., IMC 2017** — *Understanding the Role of Registrars in DNSSEC
  Deployment.* Attributes deployment to registrar behaviour, which is the
  attribution layer we explicitly do not claim.
- **IMC 2025** — *Measuring the Deployment of DNSSEC Bootstrapping Using
  Authenticated Signals.* Covers RFC 9615, which our checklist carries but cannot
  evidence; worth reading before we add it.
