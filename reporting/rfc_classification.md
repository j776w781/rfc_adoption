# DNSSEC RFC classification

Checklist `0.2.0` against a dictionary of 19 fields: **30 RFCs, 50 indicators**.

`signal_type` is what a match means. `verdict` is whether this corpus can answer it. They are independent: an RFC can be perfectly well specified and still unmeasurable here.

## Adoption signals

A match means the mechanism is deployed.

| RFC | Published | Status | Verdict | Observable from | Title |
| --- | --- | --- | --- | --- | --- |
| RFC 3110 | 2001-05-01 | Proposed Standard | measurable | 2010-01-01 ⚠ | RSA/SHA-1 SIGs and RSA KEYs in the Domain Name System (DNS) |
| RFC 4033 | 2005-03-01 | Proposed Standard | measurable | 2010-01-01 ⚠ | DNS Security Introduction and Requirements (DNSSEC base: RFC 403 |
| RFC 4034 | 2005-03-01 | Proposed Standard | measurable | 2010-01-01 ⚠ | Resource Records for the DNS Security Extensions |
| RFC 4509 | 2006-05-01 | Proposed Standard | measurable | 2010-01-01 ⚠ | Use of SHA-256 in DNSSEC Delegation Signer (DS) Resource Records |
| RFC 5011 | 2007-09-01 | Internet Standard | measurable | 2016-01-01 ⚠ | Automated Updates of DNS Security (DNSSEC) Trust Anchors |
| RFC 5155 | 2008-03-01 | Proposed Standard | measurable | 2010-01-01 ⚠ | DNS Security (DNSSEC) Hashed Authenticated Denial of Existence |
| RFC 5702 | 2009-10-01 | Proposed Standard | measurable | 2010-01-01 ⚠ | Use of SHA-2 Algorithms with RSA in DNSKEY and RRSIG Resource Re |
| RFC 5933 | 2010-07-01 | Historic | measurable | 2010-01-01 | Use of GOST Signature Algorithms in DNSKEY and RRSIG Resource Re |
| RFC 6605 | 2012-04-01 | Proposed Standard | measurable | 2010-01-01 | Elliptic Curve Digital Signature Algorithm (DSA) for DNSSEC |
| RFC 6698 | 2012-08-01 | Proposed Standard | measurable | 2010-01-01 | The DNS-Based Authentication of Named Entities (DANE) Transport  |
| RFC 7344 | 2014-09-01 | Proposed Standard | measurable | 2010-01-01 | Automating DNSSEC Delegation Trust Maintenance |
| RFC 7671 | 2015-10-01 | Proposed Standard | measurable | 2012-08-01 | The DNS-Based Authentication of Named Entities (DANE) Protocol:  |
| RFC 7672 | 2015-10-01 | Proposed Standard | partly measurable | 2010-01-01 | SMTP Security via Opportunistic DNS-Based Authentication of Name |
| RFC 8078 | 2017-03-01 | Proposed Standard | measurable | 2010-01-01 | Managing DS Records from the Parent via CDS/CDNSKEY |
| RFC 8080 | 2017-02-01 | Proposed Standard | measurable | 2010-01-01 | Edwards-Curve Digital Security Algorithm (EdDSA) for DNSSEC |
| RFC 8624 | 2019-06-01 | Proposed Standard | ambiguous only | 2010-01-01 | Algorithm Implementation Requirements and Usage Guidance for DNS *(obs. by RFC 9904)* |
| RFC 9276 | 2022-08-01 | Best Current Practice | measurable | 2010-01-01 | Guidance for NSEC3 Parameter Settings |
| RFC 9558 | 2024-04-01 | Informational | measurable | 2010-01-01 | Use of GOST 2012 Signature Algorithms in DNSKEY and RRSIG Resour |
| RFC 9563 | 2024-12-01 | Informational | measurable | 2010-01-01 | SM2 Digital Signature Algorithm for DNSSEC |
| RFC 9615 | 2024-07-01 | Proposed Standard | not measurable here | 2010-01-01 | Automatic DNSSEC Bootstrapping Using Authenticated Signals from  |

## Non-conformance signals

A match means a **deprecated** mechanism is still published. Counting these as adoption would invert the finding.

| RFC | Published | Status | Verdict | Observable from | Title |
| --- | --- | --- | --- | --- | --- |
| RFC 9905 | 2025-11-01 | Proposed Standard | measurable | 2010-01-01 | Deprecating the Use of SHA-1 in DNSSEC Signature Algorithms |
| RFC 9906 | 2025-11-01 | Proposed Standard | measurable | 2010-01-01 | Deprecate Usage of ECC-GOST within DNSSEC |

## Process and resolver-side documents

These define a process, an operational practice, or resolver behaviour. Nothing an authoritative zone publishes can evidence them, so they are carried for completeness and are expected to be unmeasurable.

| RFC | Published | Status | Verdict | Observable from | Title |
| --- | --- | --- | --- | --- | --- |
| RFC 4035 | 2005-03-01 | Proposed Standard | not measurable here | — | Protocol Modifications for the DNS Security Extensions |
| RFC 6781 | 2012-12-01 | Informational | ambiguous only | 2016-01-01 ⚠ | DNSSEC Operational Practices, Version 2 |
| RFC 6840 | 2013-02-01 | Proposed Standard | ambiguous only | 2010-01-01 | Clarifications and Implementation Notes for DNS Security (DNSSEC |
| RFC 7583 | 2015-10-01 | Informational | not measurable here | — | DNSSEC Key Rollover Timing Considerations |
| RFC 8198 | 2017-07-01 | Proposed Standard | not measurable here | — | Aggressive Use of DNSSEC-Validated Cache |
| RFC 9077 | 2021-07-01 | Proposed Standard | partly measurable | 2010-01-01 | NSEC and NSEC3: TTLs and Aggressive Use |
| RFC 9364 | 2023-02-01 | Best Current Practice | ambiguous only | 2010-01-01 | DNS Security Extensions (DNSSEC) |
| RFC 9904 | 2025-11-01 | Proposed Standard | not measurable here | — | DNSSEC Cryptographic Algorithm Recommendation Update Process |

## ⚠ Left-censored RFCs

Published before the corpus can see the fields their indicators need. A first-seen date for these is an **upper bound on the lag**, not a measurement of it.

| RFC | Published | Observable from |
| --- | --- | --- |
| RFC 3110 | 2001-05-01 | 2010-01-01 |
| RFC 4033 | 2005-03-01 | 2010-01-01 |
| RFC 4034 | 2005-03-01 | 2010-01-01 |
| RFC 4509 | 2006-05-01 | 2010-01-01 |
| RFC 5011 | 2007-09-01 | 2016-01-01 |
| RFC 5155 | 2008-03-01 | 2010-01-01 |
| RFC 5702 | 2009-10-01 | 2010-01-01 |
| RFC 6781 | 2012-12-01 | 2016-01-01 |

## Why each verdict was reached

**RFC 3110** — measurable  
Indicator rfc3110_rsasha1_algorithm is queryable because all fields it references exist in the OpenINTEL dictionary: algorithm (integer).

**RFC 4033** — measurable  
Indicator rfc4033_base_dnssec_record_present is queryable because all fields it references exist in the OpenINTEL dictionary: rr_type (string).

**RFC 4034** — measurable  
Indicator rfc4034_core_record_present is queryable because all fields it references exist in the OpenINTEL dictionary: rr_type (string).

**RFC 4035** — not measurable here  
Indicator rfc4035_dnssec_ok_negotiated is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: dnssec_ok_flag. No part of it can ever be evaluated against the measurement corpus.

**RFC 4509** — measurable  
Indicator rfc4509_ds_sha256_digest is queryable because all fields it references exist in the OpenINTEL dictionary: rr_type (string), digest_type (integer).

**RFC 5011** — measurable  
Indicator rfc5011_revoked_key_published is queryable because all fields it references exist in the OpenINTEL dictionary: rr_type (string), flags (string).

**RFC 5155** — measurable  
Indicator rfc5155_nsec3_record_present is queryable because all fields it references exist in the OpenINTEL dictionary: rr_type (string).

**RFC 5702** — measurable  
Indicator rfc5702_rsa_sha2_algorithm is queryable because all fields it references exist in the OpenINTEL dictionary: algorithm (integer).

**RFC 5933** — measurable  
Indicator rfc5933_ecc_gost_algorithm is queryable because all fields it references exist in the OpenINTEL dictionary: algorithm (integer).

**RFC 6605** — measurable  
Indicator rfc6605_ecdsa_algorithm is queryable because all fields it references exist in the OpenINTEL dictionary: algorithm (integer).

**RFC 6698** — measurable  
Indicator rfc6698_tlsa_record_present is queryable because all fields it references exist in the OpenINTEL dictionary: rr_type (string).

**RFC 6781** — ambiguous only  
Indicator rfc6781_ksk_zsk_separation is ambiguous: every field it references exists in the OpenINTEL dictionary (rr_type (string), flags (string)), so it can be evaluated, but the checklist marks it ambiguous because the same observation is equally well explained by other RFCs, so a match is not uniquely attributable to RFC 6781.

**RFC 6840** — ambiguous only  
Indicator rfc6840_clarified_dnssec_present is ambiguous: every field it references exists in the OpenINTEL dictionary (rr_type (string)), so it can be evaluated, but the checklist marks it ambiguous because the same observation is equally well explained by other RFCs, so a match is not uniquely attributable to RFC 6840.

**RFC 7344** — measurable  
Indicator rfc7344_cds_cdnskey_present is queryable because all fields it references exist in the OpenINTEL dictionary: rr_type (string).

**RFC 7583** — not measurable here  
Indicator rfc7583_rollover_timing_observed is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: key_rollover_phase. No part of it can ever be evaluated against the measurement corpus.

**RFC 7671** — measurable  
Indicator rfc7671_dane_usage_preferred is queryable because all fields it references exist in the OpenINTEL dictionary: rr_type (string), tlsa_usage (integer).

**RFC 7672** — partly measurable  
Indicator rfc7672_smtp_dane_tlsa is partially queryable: rr_type (string) exists in the OpenINTEL dictionary but domain does not, so the conditions on domain fail with field_present=False while the remaining conditions, which carry the indicator's discriminating value, are still evaluated.

**RFC 8078** — measurable  
Indicator rfc8078_cds_cdnskey_algorithm_zero is queryable because all fields it references exist in the OpenINTEL dictionary: rr_type (string), algorithm (integer).

**RFC 8080** — measurable  
Indicator rfc8080_eddsa_algorithm is queryable because all fields it references exist in the OpenINTEL dictionary: algorithm (integer).

**RFC 8198** — not measurable here  
Indicator rfc8198_aggressive_nsec_use is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: resolver_synthesised_nxdomain. No part of it can ever be evaluated against the measurement corpus.

**RFC 8624** — ambiguous only  
Indicator rfc8624_recommended_signing_algorithm is ambiguous: every field it references exists in the OpenINTEL dictionary (algorithm (integer)), so it can be evaluated, but the checklist marks it ambiguous because the same observation is equally well explained by other RFCs, so a match is not uniquely attributable to RFC 8624.

**RFC 9077** — partly measurable  
Indicator rfc9077_nsec_ttl_bounded is partially queryable: rr_type (string) exists in the OpenINTEL dictionary but record_ttl does not, so the conditions on record_ttl fail with field_present=False while the remaining conditions, which carry the indicator's discriminating value, are still evaluated.

**RFC 9276** — measurable  
Indicator rfc9276_zero_nsec3_iterations is queryable because all fields it references exist in the OpenINTEL dictionary: rr_type (string), nsec3_iterations (integer).

**RFC 9364** — ambiguous only  
Indicator rfc9364_dnssec_deployed is ambiguous: every field it references exists in the OpenINTEL dictionary (rr_type (string)), so it can be evaluated, but the checklist marks it ambiguous because the same observation is equally well explained by other RFCs, so a match is not uniquely attributable to RFC 9364.

**RFC 9558** — measurable  
Indicator rfc9558_gost2012_algorithm is queryable because all fields it references exist in the OpenINTEL dictionary: algorithm (integer).

**RFC 9563** — measurable  
Indicator rfc9563_sm2sm3_algorithm is queryable because all fields it references exist in the OpenINTEL dictionary: algorithm (integer).

**RFC 9615** — not measurable here  
Indicator rfc9615_bootstrap_signal_label is non-queryable: the field carrying its discriminating value, domain, is absent from the OpenINTEL dictionary, and the only field that remains, rr_type (string), merely scopes which records are considered and is not used by any other RFC 9615 indicator, so nothing testable is left to attribute an observation to RFC 9615.

**RFC 9904** — not measurable here  
Indicator rfc9904_algorithm_guidance_process is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: guidance_source_registry. No part of it can ever be evaluated against the measurement corpus. The checklist additionally marks this indicator ambiguous, so even a full match is not uniquely attributable to RFC 9904.

**RFC 9905** — measurable  
Indicator rfc9905_deprecated_sha1_signature_still_published is queryable because all fields it references exist in the OpenINTEL dictionary: rr_type (string), algorithm (integer).

**RFC 9906** — measurable  
Indicator rfc9906_deprecated_ecc_gost_still_published is queryable because all fields it references exist in the OpenINTEL dictionary: algorithm (integer).

