# OpenINTEL Schema Cross-Check

Generated: 2026-08-18T16:10:31  
Pipeline: openintel-rfc-adoption-matcher 0.1.0

Every indicator in the RFC checklist is checked field by field against the OpenINTEL analysis dictionary *before* any measurement data is read. An indicator whose fields the corpus does not carry cannot be answered by this data source at any confidence level, and saying so explicitly is more useful than silently scoring it as a non-match.

## 1. Inputs

| Input | Value |
| --- | --- |
| Checklist | E:/Documents/University/year2/DNSSEC/rfc_adoption/data/rfc_checklists/dnssec_rfc_checklists.json |
| Dictionary | E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json |
| RFCs | 30 |
| Indicators | 50 |
| Dictionary fields | 19 |

## 2. Queryability summary

| Queryability | Indicators | Share |
| --- | --- | --- |
| queryable | 36 | 72.0% |
| non_queryable | 6 | 12.0% |
| ambiguous | 5 | 10.0% |
| partially_queryable | 3 | 6.0% |

Definitions: *queryable* - every field the indicator references exists in the dictionary; *partially_queryable* - some fields exist and at least one does not, so the indicator can only ever be partly evaluated; *non_queryable* - none of the discriminating fields exist; *ambiguous* - the fields exist but the observation is not uniquely attributable to the RFC.

## 3. Indicator verdicts

| RFC | Indicator | Role | Weight | Queryability | Fields used | Missing fields |
| --- | --- | --- | --- | --- | --- | --- |
| RFC 3110 | rfc3110_rsasha1_algorithm | required | 9 | queryable | algorithm | - |
| RFC 3110 | rfc3110_rsasha1_on_key_or_signature | optional | 3 | queryable | rr_type, algorithm | - |
| RFC 4033 | rfc4033_base_dnssec_record_present | required | 4 | queryable | rr_type | - |
| RFC 4033 | rfc4033_dnssec_algorithm_present | optional | 2 | queryable | algorithm | - |
| RFC 4033 | rfc4033_dnssec_ok_negotiated | optional | 3 | partially_queryable | rr_type, dnssec_ok_flag | dnssec_ok_flag |
| RFC 4034 | rfc4034_core_record_present | required | 3 | queryable | rr_type | - |
| RFC 4034 | rfc4034_dnskey_protocol_is_three | optional | 7 | queryable | rr_type, dnskey_protocol | - |
| RFC 4034 | rfc4034_rrsig_type_covered_present | optional | 7 | queryable | rr_type, rrsig_type_covered | - |
| RFC 4035 | rfc4035_dnssec_ok_negotiated | required | 6 | non_queryable | dnssec_ok_flag | dnssec_ok_flag |
| RFC 4509 | rfc4509_ds_sha256_digest | required | 9 | queryable | rr_type, digest_type | - |
| RFC 5011 | rfc5011_revoked_key_published | required | 8 | queryable | rr_type, flags | - |
| RFC 5155 | rfc5155_nsec3_hash_algorithm | optional | 3 | queryable | rr_type, algorithm | - |
| RFC 5155 | rfc5155_nsec3_record_present | required | 10 | queryable | rr_type | - |
| RFC 5702 | rfc5702_rsa_sha2_algorithm | required | 9 | queryable | algorithm | - |
| RFC 5702 | rfc5702_rsa_sha2_on_dnssec_record | optional | 3 | queryable | rr_type, algorithm | - |
| RFC 5933 | rfc5933_ecc_gost_algorithm | required | 10 | queryable | algorithm | - |
| RFC 5933 | rfc5933_gost_ds_digest | optional | 4 | queryable | rr_type, digest_type | - |
| RFC 6605 | rfc6605_ecdsa_algorithm | required | 9 | queryable | algorithm | - |
| RFC 6605 | rfc6605_ecdsa_on_key_or_signature | optional | 3 | queryable | rr_type, algorithm | - |
| RFC 6698 | rfc6698_tlsa_fields_well_formed | optional | 4 | queryable | tlsa_usage, tlsa_matchtype | - |
| RFC 6698 | rfc6698_tlsa_record_present | required | 10 | queryable | rr_type | - |
| RFC 6781 | rfc6781_ksk_zsk_separation | required | 3 | ambiguous | rr_type, flags | - |
| RFC 6840 | rfc6840_clarified_dnssec_present | required | 2 | ambiguous | rr_type | - |
| RFC 7344 | rfc7344_cds_cdnskey_present | required | 9 | queryable | rr_type | - |
| RFC 7344 | rfc7344_cds_publishes_digest | optional | 3 | queryable | rr_type, digest_type | - |
| RFC 7583 | rfc7583_rollover_timing_observed | required | 6 | non_queryable | key_rollover_phase | key_rollover_phase |
| RFC 7671 | rfc7671_dane_usage_preferred | required | 8 | queryable | rr_type, tlsa_usage | - |
| RFC 7672 | rfc7672_smtp_dane_tlsa | required | 10 | partially_queryable | rr_type, domain | domain |
| RFC 8078 | rfc8078_cds_cdnskey_algorithm_zero | required | 10 | queryable | rr_type, algorithm | - |
| RFC 8078 | rfc8078_delete_signal_digest_zero | optional | 3 | queryable | rr_type, digest_type | - |
| RFC 8080 | rfc8080_eddsa_algorithm | required | 10 | queryable | algorithm | - |
| RFC 8080 | rfc8080_eddsa_on_key_or_signature | optional | 3 | queryable | rr_type, algorithm | - |
| RFC 8198 | rfc8198_aggressive_nsec_use | required | 6 | non_queryable | resolver_synthesised_nxdomain | resolver_synthesised_nxdomain |
| RFC 8624 | rfc8624_avoids_deprecated_algorithm | optional | 3 | ambiguous | algorithm | - |
| RFC 8624 | rfc8624_recommended_signing_algorithm | required | 5 | ambiguous | algorithm | - |
| RFC 8624 | rfc8624_validator_algorithm_support | optional | 6 | non_queryable | validator_algorithm_support, rr_type | validator_algorithm_support |
| RFC 9077 | rfc9077_nsec_ttl_bounded | required | 6 | partially_queryable | rr_type, record_ttl | record_ttl |
| RFC 9276 | rfc9276_empty_nsec3_salt | optional | 4 | queryable | rr_type, nsec3_salt | - |
| RFC 9276 | rfc9276_zero_nsec3_iterations | required | 10 | queryable | rr_type, nsec3_iterations | - |
| RFC 9364 | rfc9364_dnssec_deployed | required | 2 | ambiguous | rr_type | - |
| RFC 9558 | rfc9558_gost2012_algorithm | required | 10 | queryable | algorithm | - |
| RFC 9558 | rfc9558_gost2012_ds_digest | optional | 4 | queryable | rr_type, digest_type | - |
| RFC 9563 | rfc9563_sm2sm3_algorithm | required | 10 | queryable | algorithm | - |
| RFC 9563 | rfc9563_sm3_ds_digest | optional | 4 | queryable | rr_type, digest_type | - |
| RFC 9615 | rfc9615_bootstrap_signal_label | required | 10 | non_queryable | domain, rr_type | domain |
| RFC 9904 | rfc9904_algorithm_guidance_process | required | 5 | non_queryable | guidance_source_registry | guidance_source_registry |
| RFC 9905 | rfc9905_deprecated_sha1_in_delegation | optional | 4 | queryable | rr_type, algorithm | - |
| RFC 9905 | rfc9905_deprecated_sha1_signature_still_published | required | 9 | queryable | rr_type, algorithm | - |
| RFC 9906 | rfc9906_deprecated_ecc_gost_still_published | required | 10 | queryable | algorithm | - |
| RFC 9906 | rfc9906_deprecated_gost_digest_still_published | optional | 4 | queryable | rr_type, digest_type | - |

## 4. Reasoning per non-queryable indicator

### RFC 4033 / rfc4033_dnssec_ok_negotiated (partially_queryable)

The resolver negotiated DNSSEC by setting the DO bit in the query (RFC 4035 section 3.2.1).

> Indicator rfc4033_dnssec_ok_negotiated is partially queryable: rr_type (string) exists in the OpenINTEL dictionary but dnssec_ok_flag does not, so every condition on dnssec_ok_flag fails with field_present=False. The surviving field rr_type is also relied on by other RFC 4033 indicators, so the part that can be evaluated still carries evidence for RFC 4033.

Missing dictionary fields: `dnssec_ok_flag`

Warning: Field `rr_type` is only available from 2010-01-01, which is after RFC 4033's publication date 2005-03-01; adoption before 2010-01-01 cannot be observed through this field.

### RFC 4035 / rfc4035_dnssec_ok_negotiated (non_queryable)

The exchange negotiated DNSSEC via the DO bit.

> Indicator rfc4035_dnssec_ok_negotiated is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: dnssec_ok_flag. No part of it can ever be evaluated against the measurement corpus.

Missing dictionary fields: `dnssec_ok_flag`

### RFC 7583 / rfc7583_rollover_timing_observed (non_queryable)

A key rollover was observed to follow RFC 7583 timing.

> Indicator rfc7583_rollover_timing_observed is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: key_rollover_phase. No part of it can ever be evaluated against the measurement corpus.

Missing dictionary fields: `key_rollover_phase`

### RFC 7672 / rfc7672_smtp_dane_tlsa (partially_queryable)

A TLSA record published under the _25._tcp SMTP prefix.

> Indicator rfc7672_smtp_dane_tlsa is partially queryable: rr_type (string) exists in the OpenINTEL dictionary but domain does not, so the conditions on domain fail with field_present=False while the remaining conditions, which carry the indicator's discriminating value, are still evaluated.

Missing dictionary fields: `domain`

### RFC 8198 / rfc8198_aggressive_nsec_use (non_queryable)

A resolver synthesised a negative answer from a cached NSEC/NSEC3.

> Indicator rfc8198_aggressive_nsec_use is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: resolver_synthesised_nxdomain. No part of it can ever be evaluated against the measurement corpus.

Missing dictionary fields: `resolver_synthesised_nxdomain`

### RFC 8624 / rfc8624_validator_algorithm_support (non_queryable)

Validating resolver implements the RFC 8624 mandatory-to-implement validation algorithm set.

> Indicator rfc8624_validator_algorithm_support is non-queryable: the field carrying its discriminating value, validator_algorithm_support, is absent from the OpenINTEL dictionary, and the only field that remains, rr_type (string), merely scopes which records are considered and is not used by any other RFC 8624 indicator, so nothing testable is left to attribute an observation to RFC 8624.

Missing dictionary fields: `validator_algorithm_support`

### RFC 9077 / rfc9077_nsec_ttl_bounded (partially_queryable)

NSEC/NSEC3 TTL is capped at the SOA minimum, per RFC 9077.

> Indicator rfc9077_nsec_ttl_bounded is partially queryable: rr_type (string) exists in the OpenINTEL dictionary but record_ttl does not, so the conditions on record_ttl fail with field_present=False while the remaining conditions, which carry the indicator's discriminating value, are still evaluated.

Missing dictionary fields: `record_ttl`

### RFC 9615 / rfc9615_bootstrap_signal_label (non_queryable)

A CDS/CDNSKEY published under an RFC 9615 _signal bootstrapping label.

> Indicator rfc9615_bootstrap_signal_label is non-queryable: the field carrying its discriminating value, domain, is absent from the OpenINTEL dictionary, and the only field that remains, rr_type (string), merely scopes which records are considered and is not used by any other RFC 9615 indicator, so nothing testable is left to attribute an observation to RFC 9615.

Missing dictionary fields: `domain`

### RFC 9904 / rfc9904_algorithm_guidance_process (non_queryable)

Algorithm guidance is sourced from the IANA registry rather than an RFC.

> Indicator rfc9904_algorithm_guidance_process is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: guidance_source_registry. No part of it can ever be evaluated against the measurement corpus. The checklist additionally marks this indicator ambiguous, so even a full match is not uniquely attributable to RFC 9904.

Missing dictionary fields: `guidance_source_registry`

## 5. Dictionary coverage

| Field | Type | Available from | Nullable | OpenINTEL columns |
| --- | --- | --- | --- | --- |
| algorithm | integer | 2010-01-01 | yes | dnskey_algorithm, ds_algorithm, rrsig_algorithm, cds_algorithm, cdnskey... |
| digest_type | integer | 2010-01-01 | yes | ds_digest_type, cds_digest_type |
| dnskey_protocol | integer | 2010-01-01 | yes | dnskey_protocol, cdnskey_protocol |
| domain | string | 2010-01-01 | no | query_name, response_name |
| flags | string | 2016-01-01 | yes | dnskey_flags, cdnskey_flags, nsec3_flags, nsec3param_flags |
| key_tag | integer | 2010-01-01 | yes | ds_key_tag, rrsig_key_tag, cds_key_tag |
| measurement_id | string | 2010-01-01 | yes | - |
| nsec3_flags | integer | 2010-01-01 | yes | nsec3_flags, nsec3param_flags |
| nsec3_iterations | integer | 2010-01-01 | yes | nsec3_iterations, nsec3param_iterations |
| nsec3_salt | string | 2010-01-01 | yes | nsec3_salt, nsec3param_salt |
| rr_type | string | 2010-01-01 | no | response_type |
| rrsig_type_covered | string | 2010-01-01 | yes | rrsig_type_covered |
| rsa_key_bitsize | integer | 2010-01-01 | yes | dnskey_pk_rsa_bitsize, cdnskey_pk_rsa_bitsize |
| source | string | 2010-01-01 | yes | source |
| timestamp | datetime | 2010-01-01 | no | timestamp |
| tlsa_matchtype | integer | 2012-08-01 | yes | tlsa_matchtype |
| tlsa_selector | integer | 2012-08-01 | yes | tlsa_selector |
| tlsa_usage | integer | 2012-08-01 | yes | tlsa_usage |
| zone | string | 2010-01-01 | no | source |

Dictionary fields no indicator references: `key_tag`, `measurement_id`, `nsec3_flags`, `rsa_key_bitsize`, `source`, `timestamp`, `tlsa_selector`, `zone`

## 6. Warnings

- Dictionary field 'measurement_id' lists no openintel_native_fields, so the Parquet reader has no real OpenINTEL column to resolve it from; it will only be populated if a column of exactly that name exists.
- Field 'dnssec_ok_flag' is referenced by 2 indicator(s) (rfc4033_dnssec_ok_negotiated, rfc4035_dnssec_ok_negotiated) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. The closest defined field name is nsec3_flags.
- Field 'guidance_source_registry' is referenced by 1 indicator(s) (rfc9904_algorithm_guidance_process) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'key_rollover_phase' is referenced by 1 indicator(s) (rfc7583_rollover_timing_observed) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'record_ttl' is referenced by 1 indicator(s) (rfc9077_nsec_ttl_bounded) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'resolver_synthesised_nxdomain' is referenced by 1 indicator(s) (rfc8198_aggressive_nsec_use) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'validator_algorithm_support' is referenced by 1 indicator(s) (rfc8624_validator_algorithm_support) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Indicator rfc4035_dnssec_ok_negotiated of RFC 4035 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc4035_dnssec_ok_negotiated is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: dnssec_ok_flag. No part of it can ever be evaluated against the measurement corpus.
- Indicator rfc7583_rollover_timing_observed of RFC 7583 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc7583_rollover_timing_observed is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: key_rollover_phase. No part of it can ever be evaluated against the measurement corpus.
- Indicator rfc8198_aggressive_nsec_use of RFC 8198 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc8198_aggressive_nsec_use is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: resolver_synthesised_nxdomain. No part of it can ever be evaluated against the measurement corpus.
- Indicator rfc8624_validator_algorithm_support of RFC 8624 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc8624_validator_algorithm_support is non-queryable: the field carrying its discriminating value, validator_algorithm_support, is absent from the OpenINTEL dictionary, and the only field that remains, rr_type (string), merely scopes which records are considered and is not used by any other RFC 8624 indicator, so nothing testable is left to attribute an observation to RFC 8624.
- Indicator rfc9615_bootstrap_signal_label of RFC 9615 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc9615_bootstrap_signal_label is non-queryable: the field carrying its discriminating value, domain, is absent from the OpenINTEL dictionary, and the only field that remains, rr_type (string), merely scopes which records are considered and is not used by any other RFC 9615 indicator, so nothing testable is left to attribute an observation to RFC 9615.
- Indicator rfc9904_algorithm_guidance_process of RFC 9904 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc9904_algorithm_guidance_process is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: guidance_source_registry. No part of it can ever be evaluated against the measurement corpus. The checklist additionally marks this indicator ambiguous, so even a full match is not uniquely attributable to RFC 9904.
- RFC 3110 was published 2001-05-01, but the OpenINTEL fields its indicators rely on only become available later: `algorithm` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 3110 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- RFC 4033 was published 2005-03-01, but the OpenINTEL fields its indicators rely on only become available later: `algorithm` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 4033 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- RFC 4034 was published 2005-03-01, but the OpenINTEL fields its indicators rely on only become available later: `dnskey_protocol` (from 2010-01-01), `rr_type` (from 2010-01-01), `rrsig_type_covered` (from 2010-01-01). Adoption of RFC 4034 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- RFC 4509 was published 2006-05-01, but the OpenINTEL fields its indicators rely on only become available later: `digest_type` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 4509 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- RFC 5011 was published 2007-09-01, but the OpenINTEL fields its indicators rely on only become available later: `flags` (from 2016-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 5011 before 2016-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- RFC 5155 was published 2008-03-01, but the OpenINTEL fields its indicators rely on only become available later: `algorithm` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 5155 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- RFC 5702 was published 2009-10-01, but the OpenINTEL fields its indicators rely on only become available later: `algorithm` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 5702 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- RFC 6781 was published 2012-12-01, but the OpenINTEL fields its indicators rely on only become available later: `flags` (from 2016-01-01). Adoption of RFC 6781 before 2016-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- Dictionary fields `key_tag` (from 2010-01-01), `measurement_id` (from 2010-01-01), `nsec3_flags` (from 2010-01-01), `rsa_key_bitsize` (from 2010-01-01), `source` (from 2010-01-01), `timestamp` (from 2010-01-01), `tlsa_selector` (from 2012-08-01), `zone` (from 2010-01-01) become available after the earliest RFC in this checklist was published. No indicator references them today, but any future indicator built on them will inherit that lower bound.

## 7. How to read this document

A *queryable* verdict means the corpus can express the indicator, not that the indicator was observed. Matching against measurement data happens in `report.md`. A *non_queryable* verdict is a statement about this data source only: the mechanism may well be deployed, but OpenINTEL record-level observations cannot see it.
