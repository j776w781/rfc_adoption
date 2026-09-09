# CVEs against RFCs and observed deployment

441 distinct CVEs touching the eight DNS implementations this project tracks, or
naming DNS/DNSSEC itself. This asks what the vulnerability record says about the
standards we measure, and whether any of it moved a zone.

Data `data/software/cve_inventory.json` (built by `scripts/cve_fetch.py`,
needs network), analysis `scripts/cve_crossref.py` (offline), output
`out/analysis/cve_crossref.json`.

## Coverage, and why one source is not enough

| Source | What it is the authority on | Distinct CVEs |
| --- | --- | --- |
| NVD, per-product CPE query | what exists for a product | 330 |
| NVD, protocol keyword query | flaws in DNS/DNSSEC across all vendors | 137 |
| project git history | **when** it was fixed, and in which release | 200 |
| **union** | | **441** |

None subsumes another. NVD does not record which release carried a fix, so the
git history is the only source for latency. Conversely Unbound's changelog never
mentions **CVE-2009-3602**, an NSEC3 signature-verification flaw from before the
project cited IDs, and Knot names two CVEs in its entire NEWS file. The keyword
query is what catches **dnsmasq**, which is not one of our eight but carries five
of the DNSSEC CVEs published on a single day in 2021.

**One attribution caveat that changes results.** Knot DNS, Knot Resolver and
OpenDNSSEC have no usable CPE, so their CVE lists come from keyword search — and
the string `Knot DNS` matches every `Knot Resolver` advisory. Before this was
separated out, fourteen CVEs looked like multi-vendor events and ten of them were
one product matched twice. Keyword-derived product membership is recorded but is
never used to decide who a CVE affected.

The same trap sits in PowerDNS: Authoritative and Recursor ship from **one
repository**, so counting them as two codebases turns every PowerDNS advisory
into a fake coordination event. Coordination is counted per codebase.

## The shape of the surface

    441 CVEs
      322  DNS, not DNSSEC        cache poisoning, TSIG, parsers, memory safety
       97  DNSSEC
       22  dependency             OpenSSL, h2o, webrick, SPNEGO -- patched around, not in

DNSSEC is **22%** of the CVE surface of DNS software. By the RFC each one
touches:

| RFC | Mechanism | CVEs |
| --- | --- | --- |
| RFC 4035 | validation, RRSIG processing | 37 |
| RFC 4033 | DNSSEC generally | 16 |
| RFC 4034 | DNSKEY, NSEC records | 16 |
| **RFC 5155** | **NSEC3** | **12** |
| RFC 5011 | trust-anchor rollover | 8 |
| RFC 6605 / 8080 | ECDSA, EdDSA | 4 |
| RFC 4509 | DS digests | 3 |
| RFC 2535 | NXT/SIG/KEY, pre-2005 DNSSEC | 1 |

RFC 4035 — *validating* signatures — carries more CVEs than every other DNSSEC
RFC combined. The specification for how to check a signature is where the bugs
are, not the specifications for the signatures themselves.

## The whole DNSSEC CVE surface is on the side we cannot see

CVEs per implementation, from the reliable CPE lists only:

| Implementation | Role | Total | DNSSEC | Not DNSSEC |
| --- | --- | --- | --- | --- |
| BIND 9 | resolver + authoritative | 207 | 40 | 167 |
| Unbound | resolver | 70 | 16 | 54 |
| PowerDNS Recursor | resolver | 64 | 12 | 52 |
| PowerDNS Authoritative | authoritative | 28 | 3 | 25 |
| **NSD** | **authoritative** | **14** | **0** | 14 |
| **OpenDNSSEC** | **signer** | **1** | **0** | 1 (a dependency) |

**NSD has fourteen CVEs and not one is DNSSEC. OpenDNSSEC has one, and it is a
dependency.** Neither validates: NSD serves zones somebody else signed, and
OpenDNSSEC signs them. Producing a signature is arithmetic on data you already
own; checking one means parsing whatever an attacker sends. PowerDNS
Authoritative's three DNSSEC CVEs are all shared with the Recursor, from the same
repository.

This lands exactly on this project's blind spot. `vocabulary.md` Layer 4 excludes
**verifiability** — whether cryptographic verification succeeds — because we read
published zone data. The CVE record says that is where essentially the entire
DNSSEC vulnerability surface lives. **We measure the half of DNSSEC that does not
have the security problems.** That is not an argument against the measurement; it
is the sharpest available statement of what it does not cover, and it is now
quantified rather than asserted.

## Fixes, embargoes, and how long the ecosystem stays exposed

Across 141 dated (CVE, project) fixes the median gap from publication to release
is **0 days**, and **37% of fixes shipped before the CVE was published**. That is
not vendors seeing the future — it is coordinated disclosure working: the release
goes out, then the ID becomes public. A negative latency here is a success, and
any analysis that averages it as a delay is measuring the wrong thing.

Four CVEs required fixes in two or more independent codebases:

| CVE | Published | CVSS | Mechanism | Codebases | First fix | Last fix | Spread |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CVE-2013-5661 | 2019-11-05 | 5.9 | — | bind9, nsd | — | — | — |
| CVE-2020-28935 | 2020-12-07 | 5.5 | — | nsd, unbound | 2020-11-24 | 2020-12-03 | 9 d |
| **CVE-2023-50387** (KeyTrap) | 2024-02-14 | 7.5 | DNSKEY | bind9, unbound, powerdns, kresd | 2024-02-11 | 2024-07-08 | **148 d** |
| **CVE-2023-50868** | 2024-02-14 | 7.5 | NSEC3 | bind9, unbound, powerdns, kresd | 2024-02-13 | 2024-07-08 | **146 d** |

The two 2024 entries are the ecosystem events. BIND shipped KeyTrap **three days
before** publication and Unbound one day before; PowerDNS Authoritative followed
a month later and the Recursor nearly five months later. So "patched on
disclosure day" is true of the first two implementations and false of the
ecosystem: the last fix landed **21 weeks** after the flaw was public.

### Multi-CVE disclosure days

| Day | CVEs | Max CVSS | Codebases | What it was |
| --- | --- | --- | --- | --- |
| 2018-01-23 | 4 | 7.5 | powerdns, unbound | wildcard-synthesised NSEC accepted as proof of non-existence |
| 2021-01-20 | 5 | 8.1 | (dnsmasq) | DNSpooq — heap overflows in dnsmasq's DNSSEC handling |
| 2026-05-20 | 3 | **9.8** | unbound | Unbound validator, one of them RCE |
| **2026-07-22** | **13** | 7.5 | bind9, unbound | coordinated DNSSEC resource-exhaustion release |
| 2026-07-23 | 3 | 7.5 | — | continuation of the same event |

The July 2026 day is the largest DNSSEC disclosure in the record: ISC shipped
BIND 9.20.26/9.21.24 and NLnet Labs shipped Unbound 1.25.2 on the same date,
covering NSEC3, RRSIG, DNSKEY and general validation. KeyTrap does not appear as
a cluster only because it was two CVEs, below the three-CVE threshold.

### 2026 is not like the other years

DNSSEC CVEs by publication year:

    2010  ######
    2018  #######
    2019  ########
    2021  ######
    2022  ########
    2023  ###
    2024  ###
    2025  ###
    2026  ##############################  30

Thirty in the first three quarters of 2026, against a prior maximum of eight.
ISC's own July release notes attribute the run to systematic code auditing rather
than to new attack research. **This is a change in discovery rate, not
necessarily in the number of flaws that exist**, and it means any "CVEs per year"
trend line drawn through 2026 is measuring how hard people looked.

## Did any CVE move deployment?

Almost none could. A CVE in a resolver is fixed by upgrading the resolver, which
changes nothing a zone publishes and is therefore invisible here. The exception is
the one mechanism where a validator can refuse to accept what a zone publishes —
NSEC3 iterations — and the chronology is worth setting out in full, because it
does not run the way the standards process implies:

    2021-05-25   Unbound commits the 150-iteration cap, citing agreement with
                 BIND and Knot
    2021-08-05   Unbound 1.13.2 ships it
    2021-08-25   CVE-2021-40083 (CVSS 7.5): Knot Resolver assertion failure on
                 "NSEC3 with too many iterations"
    2021-10      zones at >=100 iterations fall 17,491 -> 3,027  (-83%)
    2021-11      -> 528  (-97% against August)
    2021-12      PowerDNS lowers max-nsec3-iterations to 100; Knot adds a check
    2022-08      RFC 9276 published
    2024-02-14   CVE-2023-50868, CVSS 7.5, in every major implementation

**Deployment moved in October 2021.** That is two months after the first cap
shipped, ten months before the RFC, and **two years and four months before the
CVE that made the risk famous**. NVD's own description of CVE-2023-50868 names
both RFCs — *"in RFC 5155 when RFC 9276 guidance is skipped"* — so by the time
the CVE existed, the guidance and most of the compliance already did.

The ordering is: **vendors agree → vendors ship → zones move → IETF documents it
→ CVE confirms the risk.** The RFC and the CVE are both downstream of a decision
taken in a commit message. This is the same conclusion the release-date analysis
reached from a different direction (see
[software_crossref.md](software_crossref.md)), and the two are independent.

## What this cannot show

- **A CVE list is a discovery record, not a defect record.** BIND has 207 CVEs
  and NSD 14; BIND is also older, larger, does far more, and is examined far more
  closely. Nothing here ranks implementations by quality and nothing should be
  read that way.
- **Fix dates come from commit messages naming a CVE.** Knot names almost none,
  so it is absent from the latency and coordination figures even where it was
  affected. Those counts are lower bounds.
- **Classification is keyword-based over CVE descriptions**, with the rule that
  fired recorded on every row. `RFC 6605/8080` is a single bucket because
  descriptions rarely distinguish which curve. Rows are auditable individually in
  `out/analysis/cve_crossref.json`.
- **Severity is NVD's CVSS**, which is assigned per product and often disputed by
  the vendor. It is reported, not endorsed.
- **The deployment link rests on one mechanism.** NSEC3 iterations is the only
  observable in this corpus a resolver can coerce. Nothing here generalises to
  algorithms, which no CVE has ever forced a zone to change.
