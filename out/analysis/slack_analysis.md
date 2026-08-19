Hi — follow-up on the DNSSEC work. Two things here: the RFCs we now screen for, and a cross-reference analysis of your RIPE reverse-DNS data against the OpenINTEL forward data. Everything is on the `overnight-data` branch, and there's an executed notebook at `notebooks/dnssec_crossref_openintel_ripe.ipynb` (plus an HTML export in `out/analysis/` if you don't want to open Jupyter).

*One correction up front*, because I gave you a wrong number in my last message: I said the signed share of reverse delegations had crossed 1%. It hasn't. More on why below — short version is I found a second composition break in the archive and the honest figure is *0.88–1.01% depending on which RIRs you include*.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*1. RFC screening: 8 → 30*

All dates and statuses are pulled from the RFC Editor index and the IANA registries at build time rather than typed by hand. That caught three I didn't know existed — *RFC 9904, 9905 and 9906, all published Nov 2025*.

Each RFC now carries two independent labels. *What a match means:*

• `adoption` (20) — the mechanism is deployed
• `non_conformance` (2) — a *deprecated* mechanism is still being published. A match is bad news.
• `meta` (8) — a process or resolver-side document that no zone file can evidence

*And whether our data can answer it at all:* measurable (19), partly measurable (2), ambiguous only (4), not measurable here (5). Plus 8 flagged left-censored — published before our corpus can see the fields they need, so their "first seen" is an upper bound, not a measurement.

The 22 added, grouped by how they're detected:

_From the algorithm number:_
• *RFC 3110* — RSA/SHA-1 (alg 5) — measurable
• *RFC 5702* — RSA/SHA-256 and SHA-512 (alg 8, 10) — measurable
• *RFC 5933* — GOST (alg 12 + DS digest 3) — measurable, now HISTORIC
• *RFC 9558* — GOST 2012 (alg 23 + digest 5) — measurable
• *RFC 9563* — SM2/SM3 (alg 17 + digest 6) — measurable

_From record format or parameters:_
• *RFC 4034* — the DNSSEC record formats. Split out from 4033 and matched on the DNSKEY protocol octet and the RRSIG type-covered field, so it says something 4033's "any DNSSEC record" indicator doesn't.
• *RFC 9276* — NSEC3 parameters (zero iterations, empty salt). Measurable, and the only BCP here we can actually test a zone against.
• *RFC 5011* — trust anchor rollover, via the REVOKE bit in DNSKEY flags. Measurable, but only the revocation half — the resolver-side timer isn't visible to us.

_DANE:_
• *RFC 6698* — TLSA records — measurable
• *RFC 7671* — DANE operational guidance, via TLSA usage 2/3 — measurable
• *RFC 7672* — SMTP DANE — only *partly* measurable; its signature is a `_25._tcp` owner-name prefix, and names are provenance in our model, not evidence

_Deprecation signals (a match is a finding, not an achievement):_
• *RFC 9905* — deprecates SHA-1 signing (alg 5/7) — measurable
• *RFC 9906* — retires ECC-GOST (alg 12) — measurable

_Carried for completeness but not measurable from what we have — this is the honest answer, not a gap:_
• *RFC 4035* — protocol modifications (DO bit, AD bit). That's a query/response property; we measure what zones publish.
• *RFC 8198* — aggressive NSEC caching. Purely resolver-side.
• *RFC 7583* — key rollover timing. Needs intent inferred across time.
• *RFC 9904* — the algorithm-guidance process doc. Nothing on the wire.
• *RFC 9615* — automatic bootstrapping. Signature is a `_signal` owner-name label, same limitation as 7672.
• *RFC 6840, 6781, 9364* — clarifications, operational practice, the BCP roadmap. All match things indistinguishable from plain DNSSEC, so they're marked ambiguous and can never outrank the RFC actually being evidenced.
• *RFC 9077* — NSEC/NSEC3 TTLs. Partly measurable; we'd need the record TTL, which isn't in the schema.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*2. Cross-referencing your RIPE data against OpenINTEL*

This is the part I'd most like your read on, since the reverse-DNS side is your territory — I mostly extended the pipeline to take it.

The two corpora share no infrastructure, no operator population and no collection method: OpenINTEL is 2.76B forward-DNS records over `.gov`/`.nu`/`.se` from 2018, RIPE is 1.88M DS records over ~1.3M delegations/day from 2009. So where they agree it's real evidence, and where they disagree it's usually telling us something about the measurement. The notebook is mostly about telling those apart.

*Where they agree — worth reporting*

• *ECDSA converges.* 62.5% of forward DNSSEC records and 64.2% of reverse DS records in 2026, from starting points 15 points apart in 2018. Two completely independent measurements landing 1.65 points apart.
• *EdDSA stayed marginal in both* — under 1%, nine years after RFC 8080. Three forward zones alone could be dismissed as unrepresentative; two independent corpora agreeing makes it a finding.

*Where they appear to disagree — and don't*

RFC 4509 (SHA-256 DS) reads ~5% forward vs ~79% reverse — a 10x gap. It's an artefact of what each side counts, and I measured it rather than hand-waving: that indicator can only match a DS record, and on the reverse side *every* scanned row is a DS record, while on the forward side DS+CDS are only *8%* of the denominator (the other 92% is RRSIG/DNSKEY/NSEC3/NSEC, which the indicator can never match).

Recomputing the forward figure over DS records only — the denominator the reverse side has by construction:

```
                     as reported    DS-only    RIPE reverse
  forward .gov 2018        5.47%     50.09%          48.99%
  forward .gov 2026        5.09%     63.49%          78.54%
```

*In 2018 the two agree to 1.1 percentage points.* The 10x was about 9x denominator. What's left in 2026 (63.5% vs 78.5%) is real — reverse-DNS operators moved to SHA-256 faster than .gov did — and that *is* a finding. The 10x wasn't.

The rule that falls out — worth keeping: *indicators scoped by record type are not comparable across corpora with different record-type composition; indicators scoped by algorithm are.* (Caveat: the forward composition is measured on .gov only, so it bounds the effect rather than characterising the whole forward corpus.)

*What only your data can give*

• *Uncensored adoption lags.* OpenINTEL starts in 2018 so everything older is left-censored. Yours starts in 2009, so these are measured, not bounded:
  RSA/SHA-2 *0.5y* → GOST *2.5y* → ECDSA *3.7y* → EdDSA *5.6y*
  Monotonically increasing by publication date. Either the ecosystem has slowed, or RSA/SHA-2 was unusually fast because it was a drop-in change to an algorithm operators already ran. I lean to the second but it's an interpretation, not a measurement — curious what you think.
• *A zone-level denominator.* 0.88–1.01% of reverse delegations are signed after seventeen years. This is the number that finally answers the "record-level, not zone-level" caveat that's been on half our slides.
• *The SHA-1 retirement, nearly done.* RSA/SHA-1 fell from 81.7% of reverse DS records in 2009 to 4.9% in 2026. That residual is exactly what RFC 9905's non-conformance signal now measures.

*Structure the pooled numbers were hiding*

• *IPv6 reverse delegations are 9.9x more likely to be signed than IPv4 ones* — 8.16% vs 0.83%. This was the sharpest split in the whole dataset and I'd never have looked if you hadn't flagged that the archive carries ip6.arpa. My reading is selection rather than causation: an operator who deployed IPv6 reverse DNS has already done discretionary modern DNS work, and those are the same people who sign. Caveat: it rests on 454 signed delegations, so quote the ratio, not the curve's shape.
• *A 6.2x spread between RIRs* — LACNIC 5.2%, AFRINIC 1.6%, RIPE 0.99%, ARIN 0.84%. But ARIN holds 85% of delegations, so *every pooled figure we quote is substantially a statement about North American address space.* Probably worth saying out loud in the deck.
• *"SHA-1" is two different mechanisms.* The DS *digest* (type 1) is at 15.3%; the *signature algorithm* (5/7) is at 4.9%. RFC 9905 closes both to new deployment — MUST NOT create new DS records with a SHA-1 digest, MUST NOT create new DNSKEY/RRSIG with 5 or 7 — while keeping validation support for each. They need different fixes (replace the DS at the parent vs reissue the child's keys), so we should report them as two numbers rather than one "SHA-1 exposure".
• *RFC 9906 retired something already dead* — GOST R 34.11-94 is at 0.07%, down from 2.9% in 2018. The deprecation documented an ending rather than causing one, which is itself interesting about how algorithm retirement works.
• *~1% of signed delegations are mid-rollover* (publishing 2+ DS algorithms at once), peaking 1.58% in 2023. It's the only *direct* evidence of operator activity in the corpus — everything else measures a state, this measures a transition — and it bounds how fast the mix can move, which fits those 3.7y/5.6y lags.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*3. The correction, and two judgement calls I'd like you to check*

*The archive has composition breaks that look exactly like adoption.* I caught APNIC leaving in Jan 2025 (~530k delegations out of the denominator in one step). I initially missed a second: *RIPE changed publication format in Oct 2015* — `legacy/` bulk zones to `1.0/` zonelets — and its delegation count fell *97.4%* without ever hitting zero, so a panel rule that only drops RIRs reporting nothing kept it. LACNIC steps 40% in 2011 for the same class of reason.

The rule is now "reports every day *and* never steps more than 25%", which leaves AFRINIC + ARIN — 89% of 2026 delegations, no discontinuity. That's what moves the headline from 1.012% to *0.880%*, and it's why "crossed 1%" was wrong: it's inside the panel-choice uncertainty. The notebook now reports all three panels instead of picking one.

Two things I'd like your opinion on:

1. *Is dropping RIPE the right call, or should we splice it?* Discarding a whole RIR to avoid one format change is heavy-handed, and it leaves us leaning almost entirely on ARIN. Splicing the series across Oct 2015 would be better — but that needs someone who knows what the `legacy/` bulk zones actually contained relative to the `1.0/` zonelets. That's you, not me.
2. *Zero-byte days.* Some days are published as 0-byte files with HTTP 200. I'm treating those as gaps — day absent from the corpus rather than empty. 199 of 209 monthly targets exist: 8 unpublished, 2 zero-byte. Reasonable?

Also worth knowing: your data can't speak to RFC 5155 (NSEC3), 7344, 8078 or 9276 at all — a delegation zone has DS and NS records and nothing else, so there are no keys, signatures or NSEC3 params to find. Those stay forward-only and nothing here corroborates them.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Happy to walk through any of it before Thursday. The notebook re-runs from a clean clone (`git checkout overnight-data && git pull`), and it verifies its own premise before charting anything — it asserts the 8 RFCs shared between the two checklist versions are byte-identical, so if that ever stops being true it stops rather than quietly producing a plausible-looking chart.
