# SecSpider (secspider.net) -- what is here and how it was obtained

Retrieved 2026-09-28 from this machine. Nothing in this directory is edited;
every HTML file is the byte-for-byte response of the URL named in the CSV.

## What SecSpider publishes (checked 2026-09-28)

SecSpider (Eric Osterweil et al., crawling since 2005; UCLA -> Verisign Labs
-> GMU) tracks a set of DNSSEC zones assembled by user submission, crawling and
NSEC walking. Its live site offers **no downloadable time series**:

| page | what it holds | usable as a series? |
|---|---|---|
| `https://secspider.net/stats.html` | a "Detailed Monitoring Summary" block with the current counts: `N Zones`, `N DNSSEC enabled zones`, `N Zones use both KSKs and ZSKs`, `N Zones are serving revoked keys`, `N DNSSEC verified zones`, `N Production DNSSEC-enabled zones`, plus key-algorithm and DANE/TLSA tables | current values only |
| `https://secspider.net/growth.html` -> `pix/growth.png` | "CDF of DNSSEC zones", a 640x480 log-scale line chart 2004-2028 (all zones / user submissions / crawled / NSEC walked) | an image; not digitised, not used |
| `pix/avail_trend.svg`, `valid_trend.svg`, `verif_trend.svg` | gnuplot SVGs of the availability / validity / verifiability health metrics over the **last four months only** (May 26 .. Sep 26 at retrieval) | no history |
| `https://secspider.net/docs.html` "Format of DS/DNSKEY Flat Files" | per-zone DS and DNSKEY dumps linked from each zone's drill-down page, GPG-signed | per-zone current state, not counts over time |
| `/downloads.html`, `/data/`, `/stats/` | 404 | -- |

So the only historical signal is the Monitoring Summary block as the Internet
Archive captured it over the years. That is what was collected.

## What was collected

`scripts/fetch_secspider_wayback.py` asked the Wayback CDX index
(`web.archive.org/cdx/search/cdx`, `collapse=timestamp:6`, status 200) for at
most one capture per calendar month of each URL that carried the summary
block, downloaded each in raw (`id_`) mode, and parsed the counts. The live
`stats.html` was fetched once as the final row.

| host (CSV `host`) | archived URL | monthly captures | span |
|---|---|---|---|
| `secspider.cs.ucla.edu` | `http://secspider.cs.ucla.edu/` (home page carried the block until 2012) | 45 | 2006-09 .. 2015-08 |
| `secspider.cs.ucla.edu` | `http://secspider.cs.ucla.edu/stats.html` | 6 | 2013-03 .. 2015-04 |
| `secspider.verisignlabs.com` | `http://secspider.verisignlabs.com/stats.html` | 44 | 2012-01 .. 2018-09 |
| `secspider.net` | `https://secspider.net/stats.html` | 38 | 2019-09 .. 2026-05 |
| `secspider.net` (`kind=live`) | `https://secspider.net/stats.html` | 1 | 2026-09-28 |

Files:

* `raw/<host>/<YYYYMMDDhhmmss>.html` -- 133 Wayback captures, unmodified.
* `raw/secspider.net-live/20260928203518.html` -- the live page.
* `secspider_wayback_snapshots.csv` -- one row per capture (134 rows).

## `secspider_wayback_snapshots.csv` columns

| column | meaning |
|---|---|
| `capture_ts` | Wayback timestamp `YYYYMMDDhhmmss` (UTC); for the live row the fetch time |
| `capture_date`, `month` | derived from `capture_ts`; `month` is the **capture** month |
| `host` | which SecSpider host served the page (see table above) |
| `kind` | `wayback` or `live` |
| `source_url` | the Wayback URL (`web.archive.org/web/<ts>/<url>`) or the live URL |
| `raw_file` | path of the saved HTML relative to this directory |
| `page_as_of` | the page's own "Deployment status as of ..." timestamp where printed (UCLA pages only); it lags the capture by days to weeks |
| `page_notice` | `outage` when the page carried SecSpider's "Sorry, but we have hit a minor pot-hole" banner (one capture, 2007-08-10) |
| `zones_tracked` | "N Zones": every zone SecSpider tracks |
| `zones_ns_match_parent` | "Zones have NS sets that match their parents' delegation set" (UCLA-era pages only) |
| `dnssec_enabled_zones` | "DNSSEC enabled zones": all online nameservers pass SecSpider's checks (EDNS0, RRSIG returned with DO bit, RRSIG matches served DNSKEY, no CNAME at apex, NSEC/NSEC3 for nonexistent names) |
| `zones_ksk_and_zsk` | "Zones use both KSKs and ZSKs" |
| `zones_serving_revoked_keys` | "Zones are serving revoked keys" |
| `dnssec_verified_zones` | "DNSSEC verified zones": verifiable from SecSpider's trust anchors / parent DS chain (absent on pages before 2012) |
| `production_dnssec_zones` | "Production DNSSEC-enabled zones": SecSpider's stricter production criterion (absent before 2009) |

Empty cell = the label was not on the page (older layouts lack some rows;
19 captures have no summary block at all: the UCLA home page after 2012-11
became a health-metrics landing page, and 2008-03 and secspider.net 2022-11
are truncated captures).

## How it is consumed, and what is dropped

`scripts/prevalence_metrics.py::secspider_usable` keeps 100 of the 134 rows.
Dropped, with the count and the reason:

| dropped | n | why |
|---|---|---|
| no summary block | 19 | nothing to parse (see above) |
| outage page | 1 | 2007-08-10 printed `1849 Zones / 0 DNSSEC enabled zones` under an outage banner |
| frozen page | 13 | the four counts are identical to the same host's previous capture, so the page was not being regenerated. Verisign Labs served `42,084 Zones / 32,876 enabled` unchanged in every capture from 2012-01-30 to 2012-10-02; the UCLA page repeated its 2011-12-14 state in 2012-02 and 2012-06 and its 2012-06-27 state in 2012-10; single repeats on 2011-08-20, 2017-07-04 and 2023-10-01 |
| inconsistent | 1 | 2021-12-06 (secspider.net): `960,264 Zones` but `981,380 verified` and `1,135,208 production` -- a numerator above the denominator, captured mid-rebuild (4.0M zones in 2020-05, 0.96M in 2021-12, 13.3M in 2022-01) |

Within a month with two usable captures (only the 2012 UCLA/Verisign overlap,
which the frozen rule already resolves) the newer host wins
(`secspider.net` > `secspider.verisignlabs.com` > `secspider.cs.ucla.edu`).
Result: 96 capture-months, 2006-09 .. 2026-09. Months without a usable capture
are absent, never interpolated; the longest holes are 2009-05..2010-02,
2014-02..2014-12, 2018-10..2019-08 and 2020-06..2021-11.

## Why the share is not a DNSSEC prevalence

The denominator is SecSpider's *tracked set*, which is built by looking for
DNSSEC (submissions, NSEC walks from signed zones, crawling). 71.5 % of it
being DNSSEC-enabled on 2026-09-28 (15,449,854 / 21,594,218) is a property of
that set, not of the DNS. The two hosts also tracked different sets: on
2012-01-30 Verisign Labs reported 42,084 zones while UCLA's 2011-12 page had
67,623. The absolute counts are the informative part; the shares are kept
because they were asked for, labelled `corpus = secspider` in
`out/analysis/prevalence_metrics.csv` with the metric names
`dnssec_enabled_share`, `dnssec_verified_share`, `production_share`.

## Reproduce

```
python scripts/fetch_secspider_wayback.py   # ~1 request/s; skips files already in raw/
python scripts/prevalence_metrics.py        # folds the CSV into out/analysis/
```
