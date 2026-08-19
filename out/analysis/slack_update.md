> **SUPERSEDED — see `slack_analysis.md`.**
> The claim below that the signed share of reverse delegations "crossed 1% this
> year" is **wrong**. A second composition break in the RIPE archive (RIPE
> changes publication format in Oct 2015, its delegation count falls 97.4%) was
> not being excluded from the panel. The corrected figure is **0.88–1.01%
> depending on the panel**, and whether it has crossed 1% is inside that
> uncertainty. Everything else in this message still stands.

Hi, just wanted to give a bit of an update from my side of things so we can maybe do a run on the pipeline before the meeting on Thursday.

*What I changed*

• *Screening went from 8 to 30 DNSSEC RFCs.* All dates and statuses are pulled from the RFC Editor index and the IANA registries at build time, so nothing is hand-typed. That caught three RFCs I didn't know existed: 9904, 9905 and 9906, all published Nov 2025.

• *Every RFC now says what a match actually means.* Three categories: `adoption` (the mechanism is deployed), `non_conformance` (a *deprecated* mechanism is still being published — bad news, not good), and `meta` (process/resolver docs that no zone file can ever evidence). Without this the report would have counted "still using SHA-1 after it was deprecated" as an adoption win.

• *Every RFC also says whether our data can answer it at all* — measurable / partly / ambiguous only / not measurable here — each with the sentence explaining why. 8 of the 30 are flagged left-censored, meaning they were published before our corpus can see the fields they need, so their "first seen" date is an upper bound and not a real measurement.

• *Fixed two real bugs* that were live before this. One made a pre-publication observation count as adoption — RFC 6840 was showing a first-seen of 2010 for a document published in 2013. The other made the SQL and Python paths silently disagree. Both were caught by the cross-engine equivalence tests, which is exactly what they're there for.

• *Fixed the throttling.* I measured the OpenINTEL endpoint properly: nginx allows about 1 request/second with a burst of 5, and going over it is what was killing the overnight runs. Added adaptive pacing and a `mirror` command so we fetch once and then scan locally forever. Worth knowing: mirroring the whole 2 TB costs only ~7,300 requests (about 2 hours of the limit) — bandwidth is the real constraint, not the rate limit.

• *Added a nightly script* so the server can keep itself up to date without anyone watching it.

Tests: 790 passing. Everything is pushed to the `overnight-data` branch.

*The RFCs added to the screening*

Detected from the algorithm number in the record:
• *RFC 3110* — RSA/SHA-1 (alg 5). Measurable.
• *RFC 5702* — RSA/SHA-256 and SHA-512 (alg 8, 10). Measurable.
• *RFC 5933* — GOST (alg 12 + DS digest 3). Measurable, and now HISTORIC — any match means someone is still running a retired algorithm.
• *RFC 9558* — GOST 2012 (alg 23 + digest 5). Measurable.
• *RFC 9563* — SM2/SM3 (alg 17 + digest 6). Measurable.

Detected from record format or parameters:
• *RFC 4034* — the DNSSEC record formats. Split out from 4033 and matched on the DNSKEY protocol octet and the RRSIG type-covered field, so it says something 4033's "any DNSSEC record" indicator doesn't.
• *RFC 9276* — NSEC3 parameters: zero iterations, empty salt. Measurable, and the one BCP here we can actually test a zone against.
• *RFC 5011* — trust anchor rollover, via the REVOKE bit in the DNSKEY flags. Measurable, but only the revocation half — the resolver-side timer isn't visible to us.

DANE:
• *RFC 6698* — TLSA records. Measurable.
• *RFC 7671* — DANE operational guidance, via TLSA usage 2/3. Measurable.
• *RFC 7672* — SMTP DANE. Only *partly* measurable: its signature is a `_25._tcp` owner-name prefix, and names are provenance in our model, not evidence.

Still-using-something-deprecated (a match here is a finding, not an achievement):
• *RFC 9905* — deprecates SHA-1 signing (alg 5/7). Measurable.
• *RFC 9906* — retires ECC-GOST (alg 12). Measurable.

Carried for completeness but *not* measurable from what we have — this is the honest answer, not a gap:
• *RFC 4035* — protocol modifications (the DO bit, AD bit). That's a query/response property; we measure what zones publish.
• *RFC 8198* — aggressive NSEC caching. Purely resolver-side.
• *RFC 7583* — key rollover timing. Needs intent inferred across time, not a per-record test.
• *RFC 9904* — the algorithm-guidance process doc. Nothing on the wire.
• *RFC 9615* — automatic bootstrapping. Its signature is a `_signal` owner-name label, same limitation as 7672.
• *RFC 6840, 6781, 9364* — clarifications, operational practice, and the BCP roadmap. All match only things that are indistinguishable from plain DNSSEC, so they're marked ambiguous and can never outrank the RFC actually being evidenced.
• *RFC 9077* — NSEC/NSEC3 TTLs. Partly measurable; we'd need the record TTL, which isn't in the schema.

*The RIPE reverse-DNS data you pointed me at*

This is the part I'd really like your read on, since it's much more your side — I mostly just streamlined the pipeline so it can take this source as well.

I ingested the RIPE historical reverse-delegation archive: 199 monthly snapshots from 2009-04 to 2026-08, all five RIRs, IPv4 and IPv6, 1.88M DS records. Two things it gives us that OpenINTEL structurally can't:

1. *A real denominator.* The zone files list every delegation, so we can say "share of *zones* signed" instead of "share of records", which is the caveat that's been on half the slides. It goes 0.022% (2009) → 1.012% (2026) — it crossed 1% this year.

2. *Uncensored adoption lags*, because it starts nine years before OpenINTEL:
   • RSA/SHA-2 (5702) — 0.5 years
   • GOST (5933) — 2.5 years
   • ECDSA (6605) — 3.7 years
   • EdDSA (8080) — 5.6 years
   Each new signing algorithm took longer to show up than the one before it. That looks like a real result to me but I'd rather you sanity-check it before we put it in front of anyone.

Two things I had to handle, and I'd like to know if you'd have done them differently:

• The archive publishes *zero-byte files with HTTP 200* on some days. I'm treating those as gaps in the series — the day is absent from the corpus, not empty. 199 of 209 target days exist: 8 unpublished, 2 zero-byte.
• *APNIC leaves the archive in Jan 2025*, which pulls ~530,000 delegations out of the denominator in one step and puts a jump in the curve that reads like adoption but isn't. I'm computing the headline number over only the RIRs present on every measured day, and plotting the all-RIRs line next to it with the break marked. If you'd rather see it another way, easy to change.

On the other sources you mentioned: DNS-OARC DITL and their root zone archive are both members-only, so I can't get at them — if you have OARC access that's a conversation worth having, since DITL is the one thing that would let us say anything about the resolver side. stats.dnssec-tools.org has no public API, so that'd need asking Viktor/Wes directly. Tony Finch's `saveroot` is public and would give us TLD-level history, but it's a 4.7 GB clone and stops in 2021 — happy to add it if you think it's worth it.

*What I'd like from you*

Does the classification look right to you? Anything you'd move between categories, or any RFC you think we should be screening that I've missed? And do the reverse-DNS numbers match your intuition?

If it all looks OK, we could get a run going before Thursday. On each machine:

```
git checkout overnight-data && git pull
./scripts/setup.sh
```

Then, using a different shard number per machine (0, 1, 2 … and `--shards` = however many machines we use):

```
# 1. mirror our share of OpenINTEL. one request per object, paid once
openintel-rfc mirror --sources gov,nu,se \
    --start 2018-01-01 --end 2026-08-01 \
    --cache-dir /large/volume/openintel \
    --shards 3 --shard 0

# 2. the reverse-DNS corpus (this one is small, ~1.1 GB, only needs one machine)
openintel-rfc ingest-reverse --monthly \
    --start 2009-03-24 --end 2026-08-01 \
    --cache-dir /large/volume/reverse

# 3. scan. reads local disk only, so it can't be throttled
openintel-rfc scale --sources gov,nu,se \
    --start 2018-01-01 --end 2026-08-01 \
    --mode download --local-corpus \
    --cache-dir /large/volume/openintel --out out/run
```

Add `--plan-only` to step 1 first if you want to see how the work splits before committing to the download — it balances on bytes, not days, because `.se` is 1.49 TB of the 2 TB and a per-year split would hand one machine 750 GB and another 2 GB.

One thing to flag: adding the RFCs bumped the checklist version, which *invalidates the existing checkpoints* by design, so this is a full re-scan rather than a top-up. That's deliberate — a result should never mix two checklist versions — but it's the reason to mirror first rather than stream.

And once we're happy, the nightly keeps it current by itself:

```
15 3 * * *  /path/to/rfc_adoption/scripts/nightly.sh >> /var/log/rfc-nightly.log 2>&1
```

Let me know what you think.
