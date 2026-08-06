# Reporting

Regenerates the analysis deck from a merged `scale` run. Both scripts read the
checkpoints directly, so every figure in the deck traces back to measured data
rather than to a number typed into a slide.

```bash
export PYTHONPATH=src
python -m openintel_rfc.cli merge --checkpoint-dir out/final/checkpoints --out out/analysis
python reporting/make_charts.py reporting/charts
python reporting/make_deck.py  reporting/charts out/analysis/dnssec_rfc_adoption.pptx
```

## Conventions the charts follow

Colours, mark weights and chrome come from a validated categorical palette
(blue `#2a78d6`, orange `#eb6834`, aqua `#1baf7a`), checked for colour-vision
separation across all pairs before use. Two rules did real work here:

- **Never compare zones measured in different years.** ECDSA adoption moves
  steeply, so putting `.gov` 2026 beside `.se` 2021 reads a time difference as a
  zone difference — and inverts the conclusion. The cross-zone chart is pinned to
  2021, the only year all three zones were measured.
- **One axis, always.** NSEC3 and ECDSA are both shares of the same denominator,
  so they belong on one scale; a second y-axis would invent a relationship.

Counts are exact aggregates. Rankings and scores derive from a sampled set of
worked examples — see `docs/running_at_scale.md`.
