# Three stages, and the time between them

`first_seen` -> `partial usage` -> `common usage`, with an interval between each.
This replaces the single "adoption date" the project used to quote. Stage names are
plain English; each is defined by an operation on the data, so nothing is hiding in
the name. See [vocabulary.md](vocabulary.md) for why "adoption" was retired.

## The definition

| Stage | Definition | Reads as |
| --- | --- | --- |
| **1 — first seen** | value present on >=1 zone, any RIR, always quoted with `n` | somebody did it once |
| **2 — partial usage** | `P(value \| signed delegations) >= 1%` **and** on >=10 distinct zones | in real use, not the norm |
| **3 — common usage** | `P(value \| signed delegations) >= 10%` **and** on >=10 distinct zones | a normal choice |

Stage 1 is an existence proof, so it takes the whole corpus — a RIR leaving cannot
un-happen an observation made while it was there. Stages 2 and 3 are population
statements, so they take the strict panel (AFRINIC + ARIN, the two RIRs with no
step change) and condition on **signed delegations**: a zone publishing no DS was
never a candidate for algorithm 13.

The three intervals:

    onset          publication -> first seen     how long until anyone did it
    establishment  first seen  -> partial        how long from novelty to real use
    ascent         partial     -> common         how long from real use to normal

## Why not the standard diffusion thresholds

Rogers' adopter categories set boundaries at cumulative **2.5% / 16% / 50% / 84%**,
and adopting them would be better grounded than any number we choose. They were
tested and rejected: Rogers' curve is *cumulative adoption*, monotone by
construction, while ours is a **share of a fixed population** where one
mechanism's rise is another's fall. Four of six observed series decline from their
peak, which cumulative adoption cannot do, and only the one still ascending fits a
logistic at all. Applying those boundaries here would move RSA/SHA-1 backwards
through the categories as it is displaced. Full test in
[prior_work.md](prior_work.md).

## Why 1% and 10%, and why >=10 zones

Both thresholds were **swept, not chosen**. Moving the threshold from 0.5% to 60%
changes the number of qualifying algorithms exactly twice:

    0.5% - 3%    6 algorithms
    4%  - 25%    4 algorithms      <- cliffs at 4% and 30%
    30% +        3 algorithms

1% and 10% each sit in the middle of a plateau. Partial can be anywhere in 0.5-3%
and common anywhere in 4-25% without changing a single result. A threshold at 4% or
30% would sit on a cliff, and the answer would then be an artefact of the number
picked rather than a fact about the data.

The **>=10 zone guard** is there because a percentage means different things at
different dates. The panel grew **201x** over the series (32 signed delegations in
2011-05, 6,444 in 2026-08), so one zone was 3.1% of it then and is 0.016% now.
Without the guard, RSASHA256 and RSASHA1-NSEC3 both "reach 1%" in 2011-05 **on a
single zone**. The guard removes that artefact and changes no current result; a
>=25 guard over-constrains the early era, pushing RSASHA1-NSEC3 from 2.0y to 7.8y
purely because its contemporaries were few.

## Results

    change              published  first_seen  partial   common    onset  estab  ascent
    DSA/SHA-1           1999-03    2009-04     -         -         10.1y      -       -
    RSASHA1             2001-05    2009-04     2011-05   2011-05    7.9y   2.1y    0.0y
    RSASHA1-NSEC3       2008-03    2009-08     2011-08   2011-08    1.4y   2.0y    0.0y
    RSASHA256           2009-10    2010-04     2012-06   2012-06    0.5y   2.2y    0.0y
    RSASHA512           2009-10    2010-08     2017-01   -          0.8y   6.4y       -
    ECC-GOST            2010-07    2013-01     -         -          2.5y      -       -
    ECDSAP256SHA256     2012-04    2015-12     2018-06   2019-03    3.7y   2.5y    0.8y
    ECDSAP384SHA384     2012-04    2016-04     2018-09   -          4.0y   2.4y       -
    Ed25519             2017-02    2022-09     -         -          5.6y      -       -
    Ed448               2017-02    2022-12     -         -          5.8y      -       -
    SHA-1 DS digest     2003-12    2009-04     2011-05   2011-05    5.3y   2.1y    0.0y
    SHA-256 DS digest   2006-05    2009-04     2011-05   2011-05    2.9y   2.1y    0.0y
    GOST DS digest      2010-07    2011-05     -         -          0.8y      -       -
    SHA-384 DS digest   2012-04    2013-08     2018-06   2022-03    1.3y   4.8y    3.8y

**The funnel: 14 reach first seen, 9 reach partial, 7 reach common.** Five never get
past being seen (DSA, ECC-GOST, Ed25519, Ed448, GOST digest); two reach real use and
stall there (RSASHA512, ECDSAP384). Splitting the stages is what makes that visible
— under a single "adoption date" all fourteen looked adopted.

| Interval | n | range | median | spread |
| --- | --- | --- | --- | --- |
| onset | 14/14 | 0.5 – 10.1 y | 3.3 y | **9.6 y** |
| establishment | 9/14 | 2.0 – 6.4 y | 2.2 y | 4.4 y |
| ascent | 7/14 | 0.0 – 3.8 y | 0.0 y | 3.8 y |

**Almost all the variance is in onset.** Establishment sits at ~2.2y for 7 of the 9
that reach it, whatever the mechanism and whatever the decade. What differs between
a fast RFC and a slow one is how long until the *first* operator moves, not how long
the spreading then takes.

## What this measure cannot resolve

**Ascent is degenerate before ~2015** and the 0.0y entries must not be read as
"spread instantly". At the 2011-05 crossing the panel held 32 signed delegations, so
1% and 10% are 0.3 and 3.2 zones — a gap one operator closes in under a month, below
the monthly sampling interval. Ascent is only resolvable where the panel is large:

    ECDSAP256SHA256   2018-06 -> 2019-03   0.8y
    SHA-384 DS digest 2018-06 -> 2022-03   3.8y

Two data points. **Do not quote a median ascent** — say that only two crossings are
resolvable and give both. The fix is a finer cadence in the early archive, not a
different threshold; no threshold choice recovers resolution the sampling never had.

The other three limits carry over unchanged from [vocabulary.md](vocabulary.md):
these stages measure what zones publish, never what software supports, never whether
any resolver validates it, and never that an RFC *caused* anything.
