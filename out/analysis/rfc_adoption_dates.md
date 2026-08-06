# RFC adoption dates versus publication

Corpus window: **2018-01-01 to 2026-04-29** (3,113 measurement days across .gov, .nu, .se).

`first` is the earliest observation; `median`/`mean` summarise *when the evidence sits* in the window, not when deployment happened. Two weightings are given: **obs** counts every record, **rate** weights each month by its records per measurement day so unevenly-sampled months do not dominate.

| RFC | Published | First seen | Lag | Median (obs) | Median (rate) | Mean (rate) | Last seen | Observations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RFC 4033 | 2005-03-01 | 2018-01-01 \* | +12.8y | 2019-02-15 | 2019-04-15 | 2020-03-18 | 2026-04-29 | 2,323,653,512 |
| RFC 4509 | 2006-05-01 | 2018-01-01 \* | +11.7y | 2019-01-15 | 2019-04-15 | 2020-03-15 | 2026-04-29 | 135,810,997 |
| RFC 5155 | 2008-03-01 | 2018-01-01 \* | +9.8y | 2019-01-15 | 2019-03-15 | 2020-01-27 | 2026-04-29 | 429,544,241 |
| RFC 6605 | 2012-04-01 | 2018-01-01 \* | +5.8y | 2021-07-15 | 2021-07-15 | 2021-10-07 | 2026-04-29 | 549,969,844 |
| RFC 7344 | 2014-09-01 | 2018-01-01 \* | +3.3y | 2023-10-15 | 2024-01-15 | 2023-06-28 | 2026-04-29 | 2,290,509 |
| RFC 8080 | 2017-02-01 | 2021-01-01 \* | +3.9y | 2021-01-15 | 2021-01-15 | 2021-02-03 | 2024-11-07 | 6,642,303 |
| RFC 8078 | 2017-03-01 | 2018-08-29 | +1.5y | 2023-09-15 | 2024-01-15 | 2023-09-03 | 2026-04-29 | 165,951 |
| RFC 8624 | 2019-06-01 | 2019-06-01 | +0.0y | 2021-08-15 | 2021-08-15 | 2022-02-04 | 2026-04-29 | 495,136,786 |

\* **First seen is censored** for RFC 4033 (corpus start), RFC 4509 (corpus start), RFC 5155 (corpus start), RFC 6605 (corpus start), RFC 7344 (corpus start), RFC 8080 (after a coverage gap).

*corpus start* — the earliest observation is the first measured day (2018-01-01), so the mechanism was already deployed before measurement began. The lag is a lower bound on how long it had been in use, not a time-to-adoption.

*after a coverage gap* — the first sighting falls on the day measurement resumed, so the mechanism may have appeared at any point during the hole. The lag is an upper bound.

Rows without a \* are the only ones whose lag is a genuine time-from-publication: the mechanism was absent on the previous measured day and present on this one.

`last seen` reflects the end of measurement, not the end of use.
