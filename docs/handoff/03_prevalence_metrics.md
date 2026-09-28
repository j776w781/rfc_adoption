# DNSSEC prevalence metrics: what each number is, per corpus

For an agent with no other context. Everything here is recomputable from two
parquet files plus one CSV, with the commands at the end.

The owner asked for three monthly metrics per corpus: the share of unique
domains with at least one **DS**, at least one **DNSKEY**, at least one
**RRSIG**. The honest answer differs by corpus because the corpora observe
different things. Every series below states its numerator and denominator; a
share without them is meaningless here.

## Files

| path | what |
|---|---|
| `scripts/prevalence_metrics.py` | computes everything; writes the two files below |
| `out/analysis/prevalence_metrics.csv` | long: `corpus, source, month, metric, numerator, denominator, pct, measured_days` |
| `out/analysis/prevalence_metrics.json` | definitions, selectors, coverage + gap months, headline (latest month per source), SecSpider status |
| `reporting/prevalence_metrics.py` | one figure per metric into `reporting/charts/prevalence/` (`ds_share.png`, `dnskey_share.png`, `rrsig_share.png`, `secspider.png`); every subtitle states the denominator, lines break at capture gaps |
| `tests/test_prevalence_metrics.py` | pins the denominator rules and endpoint values |
| `scripts/fetch_secspider_wayback.py` | scrapes SecSpider's Monitoring Summary counts from Wayback captures (skips files already in `raw/`) |
| `data/external/secspider/README.md` | what secspider.net publishes, what was fetched, every column, every dropped capture |
| `data/external/secspider/secspider_wayback_snapshots.csv` | one row per capture (134): counts as printed, plus `page_as_of`, `page_notice` |
| `data/external/secspider/raw/<host>/<ts>.html` | 133 Wayback captures + 1 live page, unmodified |

Inputs: `out/server_run/timeline_monthly.parquet` (basis `reverse` = five RIRs,
basis `zonefile` = seven OpenINTEL TLDs) and `out/panel_run/timeline_monthly.parquet`
(source `_pooled-afrinic-arin` = the strict reverse panel). Columns:
`source, basis, month, dimension, value, records, domain_days, domains_peak, measured_days`.

## The count column

Every count is `domains_peak`: the largest single-day distinct-domain count in
the month (`openintel_rfc.timeline_extract.merge_checkpoints`; each day's
count is an exact DuckDB `count(DISTINCT domain)`, not an estimate). Per-day
checkpoints carry no identities, so distinct names cannot be unioned across
days; the busiest day is a lower bound on the month's distinct count. For the
reverse basis `measured_days` is always 1, so `domains_peak` is simply the
month's snapshot. For the forward basis it is a peak day (28-32 measured days
in a full month), and numerator and denominator may peak on different days.

## Corpus 1: reverse (in-addr.arpa, five RIRs) and the strict panel

Sources `afrinic, apnic, arin, lacnic, ripe` (server run) and
`_pooled-afrinic-arin` + its `afrinic`/`arin` parts (panel run). One zone-file
snapshot per month, 2009-03 to 2026-08 (apnic ends 2024-11; panel starts 2009-04).

| metric | numerator | denominator |
|---|---|---|
| `ds_share` | `dimension=algorithm_ds, value=_total` -> delegations with >= 1 DS | `dimension=all` -> every delegation in the RIR's zone file |

Checked: `algorithm_ds _total` equals `rr_type DS` in all 826 source-months.
`dimension=all` differs from `rr_type NS` by at most 1 in 34 months (the zone's
own apex); the rule is `all`. Months where the snapshot has no DS row at all
(early years; lacnic until 2016-08) are 0 signed, not missing.

**DNSKEY and RRSIG are not observable in this corpus.** A parent zone file
carries only the delegation: NS, DS, glue. DNSKEY and RRSIG live in the child
zone and were never measured. No rows are emitted; the JSON lists this under
`not_observable`. Use the strict panel (`reverse_panel`, `_pooled-afrinic-arin`)
for a headline share; the per-RIR series are for shape, not for pooling.

Gap months (no snapshot, 10 per RIR): 2009-05, 2009-06, 2010-11 to 2011-03,
2012-06, 2016-02, 2020-12. The panel's gap list is the same set shifted by one
month (it is dated by the following month: 2009-06, 2009-07, 2010-12 to
2011-04, 2012-07, 2016-03, 2021-01).

Structural steps a reader will see and should not read as adoption events:
afrinic 2014-10 (20 -> 196 signed delegations, 0.07 % -> 0.71 %) and 2018-10
(258 -> 366); lacnic's climb from 2021-08 onward is real growth on a small base
(23,854 delegations).

## Corpus 2: forward (OpenINTEL TLD zone files, seven TLDs)

Sources `se, nu` (2016-06..2023-12), `gov` (2017-05..2023-12), `fed.us`
(2017-05..2022-10), `ee` (2019-07..2023-12), `ch, li` (2020-05..2023-12). No gap
months inside any span. The measurement is over NAMES (apex and subnames such
as `www.`), which is why the denominator must be chosen.

| metric | numerator | denominator |
|---|---|---|
| `ds_share` | `rr_type=DS` -> names with >= 1 DS (DS exists only at a delegation point, so these are delegated zones) | `rr_type=NS` -> names with an NS RRset = delegated zones |
| `dnskey_share` | `algorithm_dnskey=_total` -> names answering with >= 1 DNSKEY (a zone apex serving keys); equals `rr_type=DNSKEY` in all 404 source-months | `rr_type=NS` |
| `rrsig_zone_share` | `rrsig_type_covered=DNSKEY` -> names carrying an RRSIG whose type-covered is DNSKEY. Only a signed apex has one, so this is "zones with an RRSIG" at zone level | `rr_type=NS` |
| `rrsig_names_share` | `rr_type=RRSIG` -> NAMES with >= 1 RRSIG of any type | `rr_type=_total` -> every measured name. A name count, used only for this name-level metric |

**Never use `rr_type=_total` as the domain count.** It is every measured name:
se 2023-12 has 3,663,131 names but 1,339,712 delegated zones (2.7x).

**Why RRSIG needs a proxy.** `rr_type=RRSIG` counts names, and every name in a
signed zone carries RRSIGs, so it exceeds the zone count (se 2023-12:
2,571,213 names with RRSIG vs 1,339,712 zones). Dividing it by zones gives
>100 %. The zone-level proxy is the RRSIG that covers the DNSKEY RRset: it
exists only at a signed apex, and it is an RRSIG observation rather than an
inference from DNSKEY. Across every TLD-month the ratio
`rrsig_type_covered DNSKEY / rr_type DNSKEY` is between 0.995 and 1.000
(pinned by a test). `rrsig_type_covered SOA` is not usable: it is ~2x the
DNSKEY count in many months because subnames return the apex SOA's RRSIG.

DS < DNSKEY in every TLD: zones serving keys without a DS at the parent
(signed, not chained). Example se 2023-12: 811,627 DS vs 840,009 DNSKEY.

Structural facts, not adoption events:
* `.gov` 2018-02: denominator 1,234 -> 5,553 delegated zones while DS names
  went 1,091 -> 1,188, so `ds_share` falls 88.4 % -> 21.4 %. The measured
  corpus widened; signing did not collapse.
* `fed.us` has 1-2 delegated zones and never a DS or DNSKEY; it is in the CSV
  (all shares 0) and off the charts.
* `ch` 2020-05, `li` 2020-05 (14 measured days) and `ee` 2019-07 (4 days) are
  partial first months.

## Corpus 3: SecSpider (external, Wayback captures)

**Outcome: obtained, with caveats.** SecSpider publishes no downloadable time
series (checked 2026-09-28: the growth chart is a PNG, the trend charts are
4-month gnuplot SVGs, the documented flat files are per-zone DS/DNSKEY dumps,
`/downloads.html` and `/data/` are 404). What it does publish is a live
"Monitoring Summary" block (`N Zones`, `N DNSSEC enabled zones`,
`N DNSSEC verified zones`, `N Production DNSSEC-enabled zones`), and the
Internet Archive has captured it since 2006 on three successive hosts
(`secspider.cs.ucla.edu` 2006-09..2015-08, `secspider.verisignlabs.com`
2012-01..2018-09, `secspider.net` 2019-09..2026-05) plus the live page
(2026-09-28). The fetcher takes at most one capture per month per host and
parses those counts; `data/external/secspider/README.md` documents every
column and every dropped capture.

| metric | numerator | denominator |
|---|---|---|
| `dnssec_enabled_share` | "DNSSEC enabled zones" (all online nameservers pass SecSpider's checks: EDNS0, RRSIG with DO, RRSIG matches served DNSKEY, no apex CNAME, NSEC/NSEC3 denial) | "Zones": every zone SecSpider tracks |
| `dnssec_verified_share` | "DNSSEC verified zones" | "Zones" |
| `production_share` | "Production DNSSEC-enabled zones" | "Zones" |

The denominator is SecSpider's tracked set (crawled + user-submitted +
NSEC-walked), which is assembled by looking for DNSSEC. The share is a
property of that set, not a prevalence over the DNS, and the absolute counts
are the useful part. `month` is the capture month, not a measurement month.

Coverage: 134 captures, 100 usable, **96 capture-months 2006-09 .. 2026-09**
(ucla 24, verisignlabs 36, secspider.net 36 incl. live). Dropped by
`secspider_usable` with the reason recorded in the JSON under
`secspider.captures_dropped`: 19 with no summary block (UCLA home page after
2012-11 was a landing page; two truncated captures), 1 outage page (2007-08:
`1849 Zones / 0 enabled` under a "pot-hole" banner), 13 frozen pages (counts
identical to the host's previous capture -- Verisign Labs served 42,084 zones
unchanged 2012-01..2012-10 while the UCLA page's own "as of" date kept moving),
1 inconsistent page (2021-12: 960,264 zones but 1,135,208 "production" zones,
mid-rebuild). Nothing is interpolated; the longest holes are 2009-05..2010-02,
2014-02..2014-12, 2018-10..2019-08 and 2020-06..2021-11, and the chart breaks
its lines at gaps over three months. The 2012 jaggedness (55 % UCLA, 78 %
Verisign, 50 % UCLA) is two hosts tracking different sets, not a change in the
DNS. The `secspider.net` era shows the tracked set growing 3.9 M -> 21.6 M
zones while the enabled share drifts 85 % -> 72 % and the verified share 60 %
-> 37 %: the crawler is finding more unsigned or unchained zones, which says
something about SecSpider's crawl, not about deployment.

## Headline numbers (latest month per source)

SecSpider `dnssec_enabled_share` (enabled / tracked zones), latest per host:
`secspider.net` 2026-09 15,449,854 / 21,594,218 = 71.55 % (live);
`secspider.verisignlabs.com` 2018-09 79.78 %; `secspider.cs.ucla.edu` 2015-04
263,314 / 529,911 = 49.69 %. Not comparable to the two corpora above (see
Corpus 3).

Reverse `ds_share` (signed delegations / all delegations):

| source | month | numerator | denominator | pct |
|---|---|---|---|---|
| `_pooled-afrinic-arin` (strict panel) | 2026-08 | 6,444 | 744,825 | 0.865 |
| afrinic | 2026-08 | 627 | 40,227 | 1.559 |
| apnic | 2024-11 | 3,711 | 573,053 | 0.648 |
| arin | 2026-08 | 6,080 | 710,116 | 0.856 |
| lacnic | 2026-08 | 1,265 | 23,854 | 5.303 |
| ripe | 2026-08 | 659 | 65,616 | 1.004 |

Forward, 2023-12 (2022-10 for fed.us), denominator = delegated zones (`rr_type NS`):

| TLD | zones (NS) | DS | DS % | DNSKEY | DNSKEY % | RRSIG over DNSKEY | RRSIG zone % | RRSIG names / all names | RRSIG name % |
|---|---|---|---|---|---|---|---|---|---|
| se | 1,339,712 | 811,627 | 60.58 | 840,009 | 62.70 | 839,978 | 62.70 | 2,571,213 / 3,663,131 | 70.19 |
| nu | 208,718 | 118,172 | 56.62 | 126,141 | 60.44 | 126,133 | 60.43 | 402,976 / 588,578 | 68.47 |
| ch | 2,355,587 | 1,231,138 | 52.26 | 1,244,739 | 52.84 | 1,244,584 | 52.84 | 3,715,218 / 6,216,637 | 59.76 |
| li | 63,300 | 21,314 | 33.67 | 22,041 | 34.82 | 22,030 | 34.80 | 66,250 / 157,422 | 42.08 |
| ee | 156,690 | 36,055 | 23.01 | 36,865 | 23.53 | 36,865 | 23.53 | 116,840 / 367,428 | 31.80 |
| gov | 9,636 | 1,552 | 16.11 | 1,766 | 18.33 | 1,761 | 18.28 | 6,858 / 23,755 | 28.87 |
| fed.us | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 2 | 0 |

## Facts a verifier can recompute

Each is one row of `out/analysis/prevalence_metrics.csv`; the parquet selector
is in the JSON under `selectors`.

1. `reverse_panel, _pooled-afrinic-arin, 2026-08, ds_share`: 6,444 / 744,825 = 0.8652 %.
2. `reverse_panel, _pooled-afrinic-arin, 2015-01, ds_share`: 669 / 522,055 = 0.1281 %.
3. `reverse_panel, _pooled-afrinic-arin, 2020-01, ds_share`: 2,240 / 641,368 = 0.3493 %.
4. `reverse, ripe, 2010-01, ds_share`: 195 / 450,187 = 0.0433 %.
5. `reverse, apnic, 2024-11, ds_share`: 3,711 / 573,053 = 0.6476 % (apnic's last month).
6. `forward, se, 2016-06, ds_share`: 647,663 / 1,229,994 = 52.66 % (25 measured days).
7. `forward, se, 2020-01, dnskey_share`: 765,890 / 1,382,035 = 55.42 %.
8. `forward, gov, 2017-05, ds_share`: 1,128 / 1,280 = 88.13 %; `forward, gov, 2018-02, ds_share`: 1,188 / 5,553 = 21.39 %.
9. `forward, nu, 2016-06, rrsig_zone_share`: 88,107 / 259,800 = 33.91 %.
10. `forward, ch, 2020-06, ds_share`: 118,901 / 1,966,694 = 6.05 %; `forward, ee, 2019-08, dnskey_share`: 5,340 / 119,052 = 4.49 %.
11. First month with any signed delegation per RIR: ripe 2009-03, arin 2011-04, apnic 2011-05, afrinic 2012-05, lacnic 2016-09.
12. `secspider, secspider.cs.ucla.edu, 2006-09, dnssec_enabled_share`: 87 / 130 = 66.92 % (first capture with the block, page as of 2006-09-02).
13. `secspider, secspider.verisignlabs.com, 2018-09, dnssec_enabled_share`: 2,127,227 / 2,666,278 = 79.78 % (last Verisign Labs capture).
14. `secspider, secspider.net, 2026-05, dnssec_enabled_share`: 15,733,833 / 20,064,857 = 78.41 % (last Wayback capture).
15. `secspider, secspider.net, 2026-09, dnssec_enabled_share`: 15,449,854 / 21,594,218 = 71.55 %; `dnssec_verified_share`: 8,092,472 / 21,594,218 = 37.48 % (live page, 2026-09-28).
16. 2021-12 is absent from the SecSpider series: the raw row in `secspider_wayback_snapshots.csv` (`capture_ts` 20211206174941) reads 960,264 zones and 1,135,208 production zones, and `secspider_usable` drops it as inconsistent.

## Recompute

```
python scripts/prevalence_metrics.py          # -> out/analysis/prevalence_metrics.{csv,json}
python reporting/prevalence_metrics.py        # -> reporting/charts/prevalence/*.png
python -m pytest tests/test_prevalence_metrics.py -q
python scripts/fetch_secspider_wayback.py     # re-scrape SecSpider (slow: ~1 Wayback request/s)
```

A one-liner check of fact 1 straight from the parquet:

```python
import pandas as pd
p = pd.read_parquet("out/panel_run/timeline_monthly.parquet")
m = p[(p.source == "_pooled-afrinic-arin") & (p.month == "2026-08")]
num = m[(m.dimension == "algorithm_ds") & (m.value == "_total")].domains_peak.item()
den = m[m.dimension == "all"].domains_peak.item()
print(num, den, round(num / den * 100, 4))   # 6444 744825 0.8652
```
