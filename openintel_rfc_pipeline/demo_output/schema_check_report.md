# OpenINTEL Schema Cross-Check

Generated: 2026-07-29T16:02:43  
Pipeline: openintel-rfc-adoption-matcher 0.1.0

Every indicator in the RFC checklist is checked field by field against the OpenINTEL analysis dictionary *before* any measurement data is read. An indicator whose fields the corpus does not carry cannot be answered by this data source at any confidence level, and saying so explicitly is more useful than silently scoring it as a non-match.

## 1. Inputs

| Input | Value |
| --- | --- |
| Checklist | data\rfc_checklists\dnssec_rfc_checklists.json |
| Dictionary | data\openintel_dictionary\sample_openintel_dictionary.json |
| RFCs | 8 |
| Indicators | 17 |
| Dictionary fields | 10 |

## 2. Queryability summary

| Queryability | Indicators | Share |
| --- | --- | --- |
| queryable | 13 | 76.5% |
| ambiguous | 2 | 11.8% |
| non_queryable | 1 | 5.9% |
| partially_queryable | 1 | 5.9% |

Definitions: *queryable* — every field the indicator references exists in the dictionary; *partially_queryable* — some fields exist and at least one does not, so the indicator can only ever be partly evaluated; *non_queryable* — none of the discriminating fields exist; *ambiguous* — the fields exist but the observation is not uniquely attributable to the RFC.

## 3. Indicator verdicts

| RFC | Indicator | Role | Weight | Queryability | Fields used | Missing fields |
| --- | --- | --- | --- | --- | --- | --- |
| RFC 4033 | rfc4033_base_dnssec_record_present | required | 4 | queryable | rr_type | - |
| RFC 4033 | rfc4033_dnssec_algorithm_present | optional | 2 | queryable | algorithm | - |
| RFC 4033 | rfc4033_dnssec_ok_negotiated | optional | 3 | partially_queryable | rr_type, dnssec_ok_flag | dnssec_ok_flag |
| RFC 4509 | rfc4509_ds_sha256_digest | required | 9 | queryable | rr_type, digest_type | - |
| RFC 5155 | rfc5155_nsec3_hash_algorithm | optional | 3 | queryable | rr_type, algorithm | - |
| RFC 5155 | rfc5155_nsec3_record_present | required | 10 | queryable | rr_type | - |
| RFC 6605 | rfc6605_ecdsa_algorithm | required | 9 | queryable | algorithm | - |
| RFC 6605 | rfc6605_ecdsa_on_key_or_signature | optional | 3 | queryable | rr_type, algorithm | - |
| RFC 7344 | rfc7344_cds_cdnskey_present | required | 9 | queryable | rr_type | - |
| RFC 7344 | rfc7344_cds_publishes_digest | optional | 3 | queryable | rr_type, digest_type | - |
| RFC 8078 | rfc8078_cds_cdnskey_algorithm_zero | required | 10 | queryable | rr_type, algorithm | - |
| RFC 8078 | rfc8078_delete_signal_digest_zero | optional | 3 | queryable | rr_type, digest_type | - |
| RFC 8080 | rfc8080_eddsa_algorithm | required | 10 | queryable | algorithm | - |
| RFC 8080 | rfc8080_eddsa_on_key_or_signature | optional | 3 | queryable | rr_type, algorithm | - |
| RFC 8624 | rfc8624_avoids_deprecated_algorithm | optional | 3 | ambiguous | algorithm | - |
| RFC 8624 | rfc8624_recommended_signing_algorithm | required | 5 | ambiguous | algorithm | - |
| RFC 8624 | rfc8624_validator_algorithm_support | optional | 6 | non_queryable | validator_algorithm_support, rr_type | validator_algorithm_support |

## 4. Reasoning per non-queryable indicator

### RFC 4033 / rfc4033_dnssec_ok_negotiated (partially_queryable)

The resolver negotiated DNSSEC by setting the DO bit in the query (RFC 4035 section 3.2.1).

> Indicator rfc4033_dnssec_ok_negotiated is partially queryable: rr_type (string) exists in the OpenINTEL dictionary but dnssec_ok_flag does not, so every condition on dnssec_ok_flag fails with field_present=False. The surviving field rr_type is also relied on by other RFC 4033 indicators, so the part that can be evaluated still carries evidence for RFC 4033.

Missing dictionary fields: `dnssec_ok_flag`

Warning: Field `rr_type` is only available from 2010-01-01, which is after RFC 4033's publication date 2005-03-01; adoption before 2010-01-01 cannot be observed through this field.

### RFC 8624 / rfc8624_validator_algorithm_support (non_queryable)

Validating resolver implements the RFC 8624 mandatory-to-implement validation algorithm set.

> Indicator rfc8624_validator_algorithm_support is non-queryable: the field carrying its discriminating value, validator_algorithm_support, is absent from the OpenINTEL dictionary, and the only field that remains, rr_type (string), merely scopes which records are considered and is not used by any other RFC 8624 indicator, so nothing testable is left to attribute an observation to RFC 8624.

Missing dictionary fields: `validator_algorithm_support`

## 5. Dictionary coverage

| Field | Type | Available from | Nullable | OpenINTEL columns |
| --- | --- | --- | --- | --- |
| algorithm | integer | 2010-01-01 | yes | dnskey_algorithm, ds_algorithm, rrsig_algorithm, cds_algorithm, cdnskey… |
| digest_type | integer | 2010-01-01 | yes | ds_digest_type, cds_digest_type |
| domain | string | 2010-01-01 | no | query_name, response_name |
| flags | string | 2016-01-01 | yes | dnskey_flags, nsec3param_flags, cdnskey_flags |
| key_tag | integer | 2010-01-01 | yes | ds_key_tag, rrsig_key_tag, cds_key_tag |
| measurement_id | string | 2010-01-01 | yes | - |
| rr_type | string | 2010-01-01 | no | response_type |
| source | string | 2010-01-01 | yes | source |
| timestamp | datetime | 2010-01-01 | no | timestamp, year, month, day |
| zone | string | 2010-01-01 | no | source |

Dictionary fields no indicator references: `domain`, `flags`, `key_tag`, `measurement_id`, `source`, `timestamp`, `zone`

## 6. Warnings

- RFC 4033 lists related RFC 'RFC 4034', which is not defined in this checklist database; the relationship cannot be resolved or ranked against.
- RFC 4033 lists related RFC 'RFC 4035', which is not defined in this checklist database; the relationship cannot be resolved or ranked against.
- Dictionary field 'measurement_id' lists no openintel_native_fields, so the Parquet reader has no real OpenINTEL column to resolve it from; it will only be populated if a column of exactly that name exists.
- Field 'dnssec_ok_flag' is referenced by 1 indicator(s) (rfc4033_dnssec_ok_negotiated) but is not defined in the OpenINTEL dictionary loaded from data\openintel_dictionary\sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'validator_algorithm_support' is referenced by 1 indicator(s) (rfc8624_validator_algorithm_support) but is not defined in the OpenINTEL dictionary loaded from data\openintel_dictionary\sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Indicator rfc8624_validator_algorithm_support of RFC 8624 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc8624_validator_algorithm_support is non-queryable: the field carrying its discriminating value, validator_algorithm_support, is absent from the OpenINTEL dictionary, and the only field that remains, rr_type (string), merely scopes which records are considered and is not used by any other RFC 8624 indicator, so nothing testable is left to attribute an observation to RFC 8624.
- RFC 4033 was published 2005-03-01, but the OpenINTEL fields its indicators rely on only become available later: `algorithm` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 4033 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- RFC 4509 was published 2006-05-01, but the OpenINTEL fields its indicators rely on only become available later: `digest_type` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 4509 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- RFC 5155 was published 2008-03-01, but the OpenINTEL fields its indicators rely on only become available later: `algorithm` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 5155 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- Dictionary fields `domain` (from 2010-01-01), `flags` (from 2016-01-01), `key_tag` (from 2010-01-01), `measurement_id` (from 2010-01-01), `source` (from 2010-01-01), `timestamp` (from 2010-01-01), `zone` (from 2010-01-01) become available after the earliest RFC in this checklist was published. No indicator references them today, but any future indicator built on them will inherit that lower bound.

## 7. How to read this document

A *queryable* verdict means the corpus can express the indicator, not that the indicator was observed. Matching against measurement data happens in `report.md`. A *non_queryable* verdict is a statement about this data source only: the mechanism may well be deployed, but OpenINTEL record-level observations cannot see it.
