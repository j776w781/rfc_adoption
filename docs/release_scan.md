# Every release, every delegation: does adoption follow software updates?

The monthly timeline counts how many delegations carried a value. It cannot say
*which*, so it cannot tell one operator re-signing ten thousand zones from ten
thousand operators each re-signing one. The raw reverse corpus can: a row per
delegation per measurement day, so following `query_name` month to month yields
every individual change with a date.

Data `out/analysis/delegation_changes.parquet` (built by
`scripts/delegation_changes.py`), scan `scripts/release_scan.py`, output
`out/analysis/release_scan.json`.

## What this covers, and what it cannot

**Per-delegation analysis is reverse-only.** The RIR corpus is in this repository
— 975 monthly files, five RIRs, 2009-08 to 2026-08. The OpenINTEL forward per-day
records are **not**; only their monthly aggregates are. So `.se`, `.nu`, `.ch`
and the rest stay at TLD level and cannot be resolved to individual zones here.

**There is no DNS-provider level.** The corpus carries `query_name` but not the
NS targets, so zones cannot be grouped by who hosts them. The three levels below
are what the data supports, and "registrar" and "DNS operator" are not among
them.

| Level | What it is | Observable |
| --- | --- | --- |
| **RIR** | the registry the delegation sits under | yes, 5 |
| **block** | parent zone one label up — `96.192.in-addr.arpa` for `26.96.192.in-addr.arpa`; in reverse DNS an allocation, so roughly "one network operator" | yes |
| **delegation** | the zone itself | yes |
| registrar / DNS host | who actually runs the nameservers | **no** |

## The ledger

**25,930 change events across 13,654 distinct delegations**, 2009-08 to 2026-08.

    sign      18,205    previously unsigned, now has a DS
    unsign     6,174    had a DS, now none
    rollover   1,551    signed before and after, different algorithm

Rollovers are the interesting minority — an operator who already had DNSSEC
working choosing to change it. The dominant transition is **algorithm 8 → 13**
(399 events): RSA/SHA-256 to ECDSA P-256, the migration the share charts show
from the other side.

## Manual against automatic

An "action" is one month, one transition, one block: the smallest unit that could
plausibly be a single decision.

| Delegations in the action | Actions | Delegations | Share |
| --- | ---: | ---: | ---: |
| 1 | 3,878 | 3,878 | **15.0%** |
| 2–4 | 2,820 | 9,550 | 36.8% |
| 5–9 | 354 | 2,582 | 10.0% |
| 10–49 | 302 | 6,245 | 24.1% |
| 50–99 | 22 | 1,407 | 5.4% |
| 100+ | **14** | 2,268 | **8.7%** |

**Fourteen actions account for 8.7% of every delegation change in seventeen
years.** The largest are unambiguous machine work:

    2020-06  .arin   96.64.in-addr.arpa     sign      -> alg 5    256 delegations
    2019-06  .apnic  159.134.in-addr.arpa   sign      -> alg 8    251
    2016-12  .apnic  57.210.in-addr.arpa    sign      -> alg 8    208
    2013-12  .ripe   68.193.in-addr.arpa    sign      -> alg 5    179
    2015-10  .ripe   68.193.in-addr.arpa    unsign    alg 5 ->    179
    2026-03  .arin   45.130.in-addr.arpa    sign      -> alg 13   116

Note the third and fourth rows: `68.193.in-addr.arpa` signs 179 delegations in
one month in 2013 and unsigns the same 179 in 2015. That is one operator
switching a feature on and off, twice visible in the aggregate as a bump nobody
could otherwise attribute.

Only **15% of changed delegations moved alone**, which is the closest thing here
to a manual, per-zone decision — and even that is an upper bound, since a small
operator with one delegation automating its signing is indistinguishable from one
editing a zone file by hand.

The split differs sharply by registry, which is itself a finding:

| RIR | Delegations moving in an action of 5+ |
| --- | ---: |
| APNIC | 76.7% |
| RIPE | 66.6% |
| AFRINIC | 64.2% |
| ARIN | 40.3% |
| **LACNIC** | **4.6%** |

LACNIC's changes are almost entirely small and scattered; APNIC's are
overwhelmingly bulk. Whatever drives DNSSEC change in reverse DNS, it is not the
same process in both.

## At what level the change happens

Taking each (month, transition) and asking how concentrated it is across blocks:

| | Cases | Share of delegations |
| --- | ---: | ---: |
| single delegation | 607 | 2.3% |
| one block | 366 | 10.0% |
| concentrated — one block is most of it | 571 | 25.1% |
| diffuse — spread across many blocks | 521 | 62.6% |

"Diffuse" is deliberately not called coordinated. Signing with algorithm 8 was a
commonplace thing to do, and many unrelated operators doing a common thing in one
month looks identical from outside to one actor doing it everywhere. What the
data supports is that **35% of changed delegations move in ways tied to a single
block**, and the rest cannot be attributed either way at this resolution.

## Does adoption follow releases?

### The identification problem comes first

1,083 releases land in 193 corpus months. **97% of months contain a release from
some project, and 100% sit within three months of one.** There is no "no release
happened" control at the ecosystem level, so no individual release effect is
identifiable — the per-release table in
`out/analysis/dns_release_scan_per_release.csv` is a descriptive ledger, not a
set of tests.

Per project a control does exist, because no single project releases every month:
OpenDNSSEC in 26% of months, PowerDNS Authoritative in 33%, Knot in 62%.

### Two confounds that had to be removed

Delegation changes rise roughly **twenty-five-fold** from 2009 to 2019 and stay
high. Projects differ in when they released: PowerDNS Recursor's median release
year is 2022, OpenDNSSEC's is 2014. So a raw comparison ranks projects by
recency, not by effect — and it duly did:

| Project | median release year | raw difference | detrended | shift *p* |
| --- | ---: | ---: | ---: | ---: |
| PowerDNS Auth | 2021 | **+47.4** | +11.8 | 0.32 |
| PowerDNS Recursor | 2022 | **+43.3** | −1.8 | 0.50 |
| Knot DNS | 2019 | **+62.3** | +22.5 | 0.11 |
| Knot Resolver | 2021 | +33.0 | −9.9 | 0.64 |
| NSD | 2015 | +20.6 | +20.7 | 0.16 |
| Unbound | 2017 | +16.8 | +20.7 | 0.15 |
| OpenDNSSEC | 2014 | −35.5 | −1.9 | 0.55 |
| BIND 9 | 2020 | −7.8 | −40.3 | 0.93 |

On raw counts four projects looked significant at *p* < 0.05. Every one of those
was the trend.

Two corrections: the series is **detrended** against a centred two-year rolling
median, so each release is judged against its own era; and the null is a
**circular shift** of the project's whole release schedule rather than a uniform
reshuffle, which keeps every gap between its releases intact and changes only
where the schedule lands. Shuffling uniformly destroys the clustering, and a
late-clustered schedule then beats the null automatically.

### The answer

**No project shows an effect.** After detrending, the smallest *p* is 0.11 (Knot
DNS) and nothing clears 0.05. Months following a project's release do not carry
more DNSSEC change than months that do not, once you stop comparing 2022 with
2011.

This agrees with [releases_vs_adoption.md](releases_vs_adoption.md), which
reached the same conclusion from the share series and a handful of hand-picked
feature releases. The two tests share a corpus but not a method, an outcome
variable, or a unit of analysis, and they agree.

## What this does not rule out

- **A specific release moving a specific operator.** The test is a population
  average over 193 months; one registry upgrading and re-signing would be a
  single action in the ledger and would not move it.
- **Effects at lags longer than three months.** The window is three months; an
  upgrade cycle measured in years would be invisible to it and is not tested
  here.
- **Anything about the forward corpus.** `.se`, `.nu` and `.ch` are where the
  large operator-driven jumps live, and the per-delegation records for them are
  not in this repository. The single highest-value addition would be those files.
- **The provider level.** Nothing here can group delegations by who runs their
  nameservers, which is the level at which an "automatic update" would actually
  propagate. NS-target data, or registry disclosure, would turn the block proxy
  into a real operator identity.
