# Additional historical corpora

The OpenINTEL forward-DNS corpus this project started from is three zones over
2018–2026. Five other historical sources were assessed for whether they could
extend that. This records what each one is, what it can answer, and — for the two
that are closed — exactly what a reader would have to do to get in.

| Source | Status | What it adds |
| --- | --- | --- |
| [RIPE NCC reverse-DNS zones](https://data-store.ripe.net/datasets/reverse-dns-zones/in-addr.arpa/) | **Integrated** | 2009→now, all 5 RIRs, IPv4 + IPv6, true zone-level denominator |
| [Tony Finch's `saveroot`](https://github.com/fanf2/saveroot) | Available, not integrated | Root-zone history → TLD-level DS adoption |
| [DNS-OARC DITL](https://www.dns-oarc.net/oarc/data/ditl) | **Closed** — members/researchers only | Resolver-side query behaviour |
| [DNS-OARC root zone archive](https://www.dns-oarc.net/oarc/data/zfr/root) | **Closed** — members only, Subversion | Root zone history |
| [stats.dnssec-tools.org](https://stats.dnssec-tools.org) | **Closed** — no public API | Validation-side DNSSEC/DANE statistics |

---

## 1. RIPE NCC reverse-DNS zones — integrated

```bash
openintel-rfc ingest-reverse --monthly \
    --start 2009-03-24 --end 2026-08-01 --cache-dir out/reverse/corpus

openintel-rfc scale --basis reverse --local-corpus \
    --sources afrinic,apnic,arin,lacnic,ripe \
    --start 2009-03-24 --end 2026-08-01 \
    --mode download --cache-dir out/reverse/corpus --out out/reverse/analysis
```

**Why it is worth the work.** Two things it has that OpenINTEL does not:

*It starts in 2009.* Every first-seen date in the OpenINTEL analysis is
left-censored at 2018-01-01, which is why that side of the project can only ever
publish upper bounds on adoption lag. This archive predates five of the eight RFCs
in the checklist, so their adoption can be watched from before publication.

*It has a real denominator.* A zone file lists every delegation, so "how many
delegations exist" and "how many carry a DS" are both directly countable. The
OpenINTEL analysis can only report a share of *records*, which is why its slides
have to keep saying "record-level, not zone-level". On 2024-01-01: **1,332,174
delegations, 9,508 signed — 0.714%.**

**Shape.** One `tar.bz2` per day, `YYYYMMDD/<rir>/<zonefile>`, ~19 MB in 2009
growing to ~102 MB in 2026, 6,108 days published. Despite the dataset name it
carries `ip6.arpa` zones too, and all five RIRs' zonelets — not just RIPE's.

**Gaps are real.** Some days are published as **zero-byte files served with HTTP
200** (2009-06-01 through 06-07, for instance), and some dates are absent
entirely. Both are treated as gaps in the series: the day is *absent from the
corpus rather than empty*, and warned about. A day whose tarball is unreadable
costs that day, not the run.

**Cost.** Monthly sampling is 209 days and about 1.2 GB of Parquet — enough to
resolve an adoption curve to the month. Daily is 6,108 tarballs and several
hundred GB; the ingest is resumable either way.

**What it cannot say.** A DS in the parent proves the delegation is *signed*, not
that the child validates. Reverse DNS is also a different population from forward
DNS — mostly network operators, allocated in blocks, far more concentrated — so
nothing here should be read as a statement about the DNS as a whole, any more than
three forward zones should be.

### How it reaches the existing checklists

The ingester writes Parquet using OpenINTEL's **native column names**
(`query_name`, `response_type`, `ds_algorithm`, `ds_digest_type`, `ds_key_tag`,
`timestamp` as epoch milliseconds). Once the rows look like OpenINTEL rows, the
existing checklist compiler, matcher, scorer and timeline work on them unmodified
and RFC 4509 / 6605 / 8080 mean exactly what they already mean elsewhere.

`--local-corpus` discovers partitions from disk rather than listing the object
store. That is required here — the store never hosted this corpus — and it is
worth using for a full OpenINTEL mirror too, where discovery otherwise spends one
LIST per partition-day confirming what is already local.

---

## 2. Tony Finch's `saveroot` — available, not integrated

`https://github.com/fanf2/saveroot` — a git archive of the DNS root zone, 4.7 GB,
last pushed 2021-02-12. The root zone's DS records are the TLD delegations, so
this would answer "when did each TLD sign, and with what algorithm" — a different
and complementary question to the reverse-delegation one.

Not integrated because it needs a 4.7 GB clone whose value is a per-commit walk of
one file, and because it stops in 2021. Worth doing if TLD-level adoption is the
question; the ingestion would mirror `reverse_zones.py` closely, since a root zone
is the same kind of BIND master file.

## 3. DNS-OARC DITL — closed

> "OARC offers access to these data to researchers and OARC members through the
> use of a number of analysis servers."

Access requires OARC membership or a researcher agreement, and the data is worked
on OARC's own analysis servers rather than downloaded. It is also resolver-side
query capture — the one thing this project's authoritative-side measurement
structurally cannot see, which is why the deck has to state that KeyTrap
(CVE-2023-50387) is invisible here. If that limitation matters enough to remove,
DITL is the source that removes it, and the route is an OARC membership
application.

## 4. DNS-OARC root zone archive — closed

> "The Root Zone Archive data is available only to DNS-OARC members, either as raw
> zone files or as a Subversion repository."

Same membership requirement. `saveroot` above is the open substitute for the same
question, at the cost of stopping in 2021.

## 5. stats.dnssec-tools.org — closed

Viktor Dukhovni and Wes Hardaker's DNSSEC/DANE deployment statistics. The site is
a JavaScript front end with no public API — `/api/`, `/data/` and the obvious JSON
paths all return 404, and `robots.txt` grants nothing. The raw data would have to
be requested from the maintainers directly, which is a human conversation rather
than something this pipeline can automate.

Its value would be *validation-side* statistics — DANE/TLSA usage and validating
resolver behaviour — which, like DITL, is the half of DNSSEC that authoritative
measurement cannot reach.
