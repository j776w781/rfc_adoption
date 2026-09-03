Hi both — I went looking for prior work before we commit to our own framework, and it turned up a real fork in the road. I'd rather have your view than pick it myself.

━━━━━━━━━━━━━━━━━━━━━━━━━━━

*What's out there*

Four things came closest:

• *Osterweil et al., IMC 2008* — availability / verifiability / validity. The standard DNSSEC deployment metrics. All three need active resolution, so we can't compute any of them from published zone data. Useful as a citation for what we explicitly *don't* measure.
• *Hovav et al., ISJ 2004* — the Internet Standards Adoption model, which explicitly includes *"partial adoption", where old and new standards coexist*. That's our middle stage, arrived at independently.
• *RFC 5218* — "incrementally deployable" is their term for exactly the mechanism behind our onset bands.
• *Rogers / Bass diffusion* — the canonical adoption curve, with categories at cumulative 2.5% / 16% / 50% / 84%.

The first three we can just adopt. The fourth is the problem.

*The mismatch*

Rogers' curve counts *how many have ever adopted*. It's monotone by construction — you can't un-adopt. Our current measure is *share of signed delegations right now*, which is a fixed pie: one algorithm's rise is another's fall.

```
  RSA/SHA-256, share of signed delegations
  2010   0%   →   2017  74.6%   →   2026  22.3%
```

That last step is impossible in Rogers' model, and nothing went wrong — those zones didn't drop DNSSEC, they moved to ECDSA. But it means his thresholds can't be lifted across: applied to our data they'd file RSA/SHA-1 as "late majority" in 2011 and "innovator" in 2026, the same mechanism walking backwards through the categories as it gets displaced.

I checked how general this is: *four of our six tracked algorithms are declining from their peak*, and only ECDSA P-256 — the one still ascending — fits a logistic at all (R² = 0.939, ceiling ~69%).

━━━━━━━━━━━━━━━━━━━━━━━━━━━

*The actual choice*

Both of these are computable from the data we already have, and they answer different questions:

*A — share of signed delegations (what we do now)*
"What fraction of signed zones use ECDSA *today*?" → 68.0%
Compositional. Goes up and down. Directly answers "what is the internet running", but no existing framework fits it.

*B — cumulative: zones that have *ever* published it*
"What fraction of zones that ever signed have ever used ECDSA?" → 62.1%

```
              ever used alg 13    ever signed    cumulative
  2016-01                    2            854          0.2%
  2018-01                    9          1,202          0.7%
  2020-01                  518          2,387         21.7%
  2022-01                1,189          3,766         31.6%
  2024-01                2,618          5,473         47.8%
  2026-08                5,068          8,156         62.1%
```

Monotone by construction, so Rogers and Bass apply directly and we inherit their categories, their thresholds and forty years of literature instead of defending numbers we swept ourselves.

The catch: B can't see displacement at all. A zone that used ECDSA once and moved on still counts forever, so B would never show the SHA-1 retreat or the RSA/SHA-256 decline — which is arguably the most interesting thing in our data.

━━━━━━━━━━━━━━━━━━━━━━━━━━━

*What I'd like your opinion on*

1. *A, B, or both?* My instinct is both — B to place us in the existing literature and inherit its thresholds, A because it's the one that answers "what is actually deployed right now". But that's two curves per mechanism in every figure, and I don't know if that's clarity or clutter for a reader.

2. *Is the displacement thing genuinely unclaimed?* Every framework I found describes something arriving; none describes something being pushed out. In a fixed population that's half of what happens, and in our data it's the bigger half. I've searched and found nothing, but "I didn't find it" is weak evidence — do either of you know work on protocol *retreat* rather than protocol adoption? If it really is open, it looks more like the contribution than the timeline does.

3. *Thresholds.* If we go with A, we're stuck defending our own 1% / 10%. They were swept rather than picked — the qualifying count is flat across 0.5–3% and 4–25%, so any value mid-plateau gives identical results — but that's still our construction. If we go with B, we can just use Rogers' 2.5 / 16 / 50 / 84. Is inherited-but-imperfect better than derived-but-ours?

4. *Vocabulary* — any objection to aligning "partial usage" with Hovav's "partial adoption", and naming our un-measurable layer with Osterweil's availability / verifiability / validity? Costs nothing and buys citations, but it does mean our terms stop being self-describing.

No rush on 3 and 4, but 1 and 2 shape what the next round of analysis even computes, so I'd like to settle those before I build more on top of the current choice.

Full write-up with the tests in `docs/prior_work.md` on the `server-full-run` branch.
