# How much of the DNSSEC RFC space do we actually cover?

Short answer: **29 of 105 current DNSSEC/DANE-related RFCs.** Everything the
project has said about "the DNSSEC RFCs" is a statement about that 29, and the
selection was made by hand rather than derived from the index.

Measured against `https://www.rfc-editor.org/rfc-index.xml`, matching DNSSEC and
DANE terms in title or abstract:

| | count |
| --- | --- |
| DNSSEC/DANE-related RFCs in the index | 125 |
| …not obsoleted and not historic | 105 |
| …in our checklist | **29** |
| uncovered, of which genuinely about DNS | 39 |
| uncovered **and measurable from zone data** | **13** |

The other 66 uncovered documents are either false positives of the keyword sweep
(SSH, RPKI, OAuth and IPsec all use the phrase "trust anchor") or genuinely
out of scope: resolver-side signalling, EPP mappings, IANA process, threat
analyses. Those are not gaps — nothing in a zone file could evidence them.

## The 13 real gaps

Each of these defines something a zone can publish, so each could be added to the
checklist and measured with the machinery that already exists.

| RFC | Year | What we would look for |
| --- | --- | --- |
| 4255 | 2006 | SSHFP records |
| 4470 | 2006 | NSEC records with minimally-covering ranges (on-line signing) |
| 4956 | 2007 | NSEC3 Opt-In flag — the experimental precursor to opt-out |
| 6594 | 2012 | SSHFP with SHA-256 fingerprints |
| 7673 | 2015 | TLSA under `_service._proto` names (DANE for SRV) |
| 7929 | 2016 | OPENPGPKEY records |
| 8162 | 2017 | SMIMEA records |
| 8749 | 2020 | Absence of DLV records, after DLV moved to historic |
| 8901 | 2020 | Multi-signer: several DNSKEY sets for one zone |
| 8976 | 2021 | ZONEMD records |
| 9824 | 2025 | Compact Denial of Existence — NSEC bitmap shape |
| 9975 | 2026 | CDS/CDNSKEY and CSYNC consistency |
| 10026 | 2026 | DS automation practice, visible through CDS/CDNSKEY |

Three stand out. **ZONEMD (RFC 8976)** is an entire record type we never look
for. **Compact Denial of Existence (RFC 9824)** is current work whose uptake is
exactly the kind of thing this project exists to track. **Multi-signer
(RFC 8901)** is measurable and operationally interesting, and nothing else we
have would reveal it.

The DANE family is also lopsided: we screen TLSA (RFC 6698, 7671, 7672) but not
its siblings OPENPGPKEY and SMIMEA, which share the same shape and would be
almost free to add.

## Two internal inconsistencies found at the same time

- **RFC 2536 and RFC 3658 are measured but not screened.** Both appear in
  `data/analysis_config.json` as observable changes — DSA/SHA-1 and the SHA-1 DS
  digest — but neither is in the checklist. They therefore have no indicator, no
  measurability verdict, and no publication date validated against the index.
  The dates used for them come from the config file alone.
- The checklist contains **RFC 3110**, which the keyword sweep does not return:
  its title and abstract describe RSA/SHA-1 keys without using a DNSSEC term.
  That is a limitation of the sweep, not of the checklist.

## What this means for anything already written

Every figure the project has published remains correct for what it measures. What
is not supportable is the phrasing "the DNSSEC RFCs", which implies completeness
the selection does not have. The honest form is **"the 29 DNSSEC RFCs we
screen"**, and where a claim is about the state of DNSSEC deployment generally,
the 13 gaps above are the first thing a reviewer will ask about.
