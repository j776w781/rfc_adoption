# Why some DNSSEC RFCs are adopted fast and some never

The question the project has been circling: what relates the DNS programs
(BIND, Unbound, Knot, PowerDNS, OpenDNSSEC) to the spikes in RFC adoption, did
any CVE lead a push, and what separates the RFCs that moved from the ones that
did not. The deck `out/analysis/dnssec_rfc_why.pptx` answers it one RFC per
slide; this page is the same argument with its sources.

Builder `reporting/rfc_timelines.py` (figures and `out/analysis/rfc_timelines.json`)
and `reporting/make_rfc_deck.py` (every number on a slide is read from that JSON
or recomputed from `out/server_run/timeline_monthly.parquet`; none is typed in).
Pinned by `tests/test_rfc_deck.py`.

## One time axis per RFC

Each timeline carries four clocks: the RFC's publication; the first stable
release of each program that could sign, validate or publish the value; every
default change and validator limit; every CVE whose description names the
mechanism; and beneath them the share of signed zones carrying the value on both
corpora, with each portfolio spike marked and named to its operator. Marker
height is lane packing so labels never overprint — only horizontal position is
data.

The verdict rule is stated on the deck and applied by code, not by hand:
**fast** = first zone within a year of the RFC and 10% of signed delegations
within four; **slow** = reached 10%, later; **never** = under 1% of signed zones
in every corpus today. Two RFCs get names for what the data shows instead.

## The eight, with what decided each

| RFC | Verdict | What decided it |
| --- | --- | --- |
| 5702 RSA/SHA-2 | fast (onset 0.4 y) | The only algorithm in the set that changed nothing about a zone's keys. Unbound validated it 11 months before the RFC, BIND signed it 4 months after, the first zone followed the signer within two months. Whether a default carried it cannot be tested: OpenDNSSEC's 2011-03 default lands after both corpora open with it in use. |
| 5155 NSEC3 | slow (onset 1.4 y, 10% at 2011-08) | Unbound validated NSEC3 four months before the RFC. On 98% of forward zones when that corpus opens. Its trouble is thirteen years later, in an iteration count RFC 5155 allowed up to 65,535. |
| 9276 NSEC3 params | vendor-triggered | Vendors agreed a 150 cap in a commit (2021-05); PowerDNS capped at 100 (2021-07); Unbound shipped (2021-08); names at ≥100 fell 17,491 → 3,027 in 2021-10; RFC ten months later; CVE-2023-50868 two years and four months after the collapse. **The moved names sat at exactly 100** — below Unbound's cap, at PowerDNS's — so neither cap refused them. The ordering is certain; the mechanism is not. |
| 6605 ECDSA | slow (onset 3.6 y = code −0.2 + operators 3.8) | Code never the wait. Knot (2016-01, at 0.25% share) and PowerDNS (2016-07, 0.72%) defaulted to it; .se/.nu jump three months later — an alignment. On the reverse panel, the only corpus with a before-period, event studies detect nothing. The rise is two registries: .se 2019-01 (+119,500), SWITCH .ch 2021-08 (+174,356). |
| 7344 CDS | niche by design | 18.5% of signed forward zones publish CDS; only a zone whose parent acts on it has reason to. Where SWITCH does, CDS publication led signing by a month or two and .ch went 140,506 → 851,003 signed zones inside 2021. Largest CDS-only spike +78,041 (2021-11). |
| 8080 EdDSA | never (0.37% panel, 0.01% forward) | Knot, Unbound, BIND shipped within a year; OpenDNSSEC took 3.6. No vendor ever made it a default. Published when ECDSA stood at 1% of its eventual share. The only spikes were one operator's .se and .nu moves, withdrawn twice. |
| 5933 GOST | never (0.00%) | Both BIND and Unbound implemented it from the draft. Never more than five RIPE delegations or four forward zones; the strict panel and the seven TLDs exclude the region it was written for. RFC 9906 deprecated it a decade after its last record — like 9276 at the front, it documented what had happened. |
| 5011 trust anchors | partly observable | The resolver half leaves no trace anywhere. The signer half does: the REVOKE bit, on 3–159 forward zones every month since 2016-06 (peak 150 in .se, 2019-01). BIND 9.7.0 could revoke and track from 2010-02, so first-seen is left-censored. 8 CVEs mention trust anchors; the first predates every implementation. |

## What separates them

Across the five mechanisms with a release history, RFC-to-signer runs −0.4 to
+1.8 years and signer-to-first-zone 0.1 to 3.8. For the two slowest, ECDSA and
GOST, the whole onset is the second number. CDS is the exception, where the code
itself took 1.8 years. Speed is mostly decided after the code ships, by the
mechanism that carries a value to a zone:

| Mechanism | Status | Lag | Case |
| --- | --- | --- | --- |
| Vendor-triggered | measured | 2 months | NSEC3 iterations, 2021 |
| Registry-automated | measured | ~2 months (CDS publication leading signing in the series) | SWITCH, .ch/.li, 2021 |
| Default-on-upgrade | inferred | 0.8–1.6 y from the ECDSA defaults to the 1% crossing, against 4.5–5.3 from the RFC; event studies detect no acceleration | ECDSA, 2016 |
| Opt-in configuration | inferred | 1.3–3.8 y | everything else; every spike is one operator, partner TLD moving the same month in 20 of 21 |
| No default, ever | observed | never | EdDSA, GOST |

## The programs, and the CVEs

- **Unbound** is a validator and publishes nothing, so it can never appear in a
  spike. It dates the validation side, and was ready before the RFC for 4 of its
  8 milestones — plus the 2021 cap, fifteen months before RFC 9276.
- **BIND**: one dated silent default change found in seventeen years (NSEC3
  iterations 100 → 10, 9.7.0, 2010-02). Its ECDSA default arrived only as opt-in
  `dnssec-policy` (9.16.0, 2020-02). No BIND release schedule predicts change in
  the ledger (p = 0.93).
- **No CVE led a push.** Of 16 DNSSEC CVEs naming a mechanism, 12 were published
  while it was already in common usage and 0 before anyone used it. The one
  candidate, CVE-2021-40083, was published after the NSEC3 cap it might have
  prompted was already committed.
- **The DNSSEC CVE surface is on validators**: BIND 40, Unbound 16, PowerDNS
  Recursor 12, PowerDNS Auth 3, NSD 0, OpenDNSSEC 0. 69 of 97 sit in the
  validation core every signed zone shares; KeyTrap among them, fixed across
  three vendors over 148 days. No algorithm choice avoids any of it.

## What two verification rounds changed

The deck was checked by re-deriving every dated or numeric claim from the source
files (221 claims, two rounds) and by auditing it against the literal ask.
Corrections it forced, all now pinned by tests:

- EdDSA first-seen was the retracted reverse-only 2022-09; the both-corpora
  figure is 2019-01.
- CDS share was over every forward name (6.5%); over signed zones it is 18.5%.
  CDS spikes summed CDS+CDNSKEY names, counting every zone publishing both twice
  (+155,150 became +78,041).
- "Validator-forced" was asserted for names that sat at exactly 100 iterations,
  below Unbound's cap. Relabelled vendor-triggered; the docs corrected.
- RFC 5011 was labelled unobservable while its REVOKE bit is in the forward
  corpus, and its only signer row was Knot 3.0.0 (2020-09); BIND 9.7.0 (2010-02)
  added.
- The same four "RFC 6605/8080" CVEs were counted on two slides; split by which
  curve the description names.
- RFC 5155's "fast, then contested" was a hard-coded override of the stated rule.
- Slide 11's default-to-1% bounds pooled the withdrawn OpenDNSSEC rows (0.2–5.2 y);
  ECDSA-only is 0.8–1.6.
- "Earliest default change in the set" (OpenDNSSEC 2011) was false by 13 months.

## What this cannot show

No zone's software is identifiable, so every release-to-move alignment is a
coincidence in time. Per-zone tracking is reverse-only. Release timing is not
identifiable at the ecosystem level (97% of months carry a release). The registry
and registrar layer — the operators every spike points at — is closed.
