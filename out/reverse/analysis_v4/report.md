# OpenINTEL RFC Adoption Analysis

Generated: 2026-08-20T10:23:52  
Pipeline: openintel-rfc-adoption-matcher 0.1.0  
Observation window: 2009-09-01 to 2026-08-01

This report identifies ranked RFC candidates that are consistent with the observed OpenINTEL signals. Read Section 13 before quoting any number from it.

## 1. Executive Summary

This run evaluated 1,875,584 OpenINTEL rows across 975 partitions against 30 DNSSEC RFCs (50 indicators); 1,875,584 (100.0% of them) reached a rankable decision. That row count is what survived the DNSSEC record-type prefilter, not the size of the partitions: rows of other record types are excluded before any indicator is evaluated, which is what makes a corpus this size tractable. The observation counts in section 7 are exact aggregates over those rows. The 38 observations carried through sections 6 and 8 are a deterministic *sample*, kept so that every aggregate has a worked reasoning trace behind it -- their number is not a measurement of anything. Every score below is derived from record-level observations and the RFC publication date; nothing here is an assertion that an operator deliberately implemented a specification.

The highest-ranked candidate is **RFC 5933** (Use of GOST Signature Algorithms in DNSKEY and RRSIG Resource Records for DNSSEC) with score 18.0 (very_high confidence), supported by 702 observations, first seen 2013-01-01.

- Observation window: 2009-09-01 to 2026-08-01.
- Valid matches: 123; partial: 35; ambiguous: 14; no match: 681.
- Rejected on publication date (impossible timestamps): 21.
- Ranked candidates emitted: 9.
- Review queue: 88 items, 13 of high severity.
- Warnings collected during the run: 28.

## 2. Inputs

| Input | Value |
| --- | --- |
| Checklist database | E:/Documents/University/year2/DNSSEC/rfc_adoption/data/rfc_checklists/dnssec_rfc_checklists.json |
| OpenINTEL dictionary | E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json |
| Parquet input | (none) |
| Output directory | out/reverse/analysis_final |
| Parquet engine | auto |
| Row limit | none |
| Minimum rankable score | 0 |
| Generated at | 2026-08-20T10:23:52 |
| Pipeline | openintel-rfc-adoption-matcher 0.1.0 |

The checklist database is the RFC signature source; the dictionary describes which normalized analysis fields the OpenINTEL corpus can supply and from which date each is reliably populated.

## 3. Open-Source Tool Stack

The stack was chosen for reproducibility and for keeping the reasoning auditable: every dependency either reads the input format, validates the inputs, or renders the outputs. No dependency participates in the matching decision itself.

| Tool | Category | Role in this pipeline | Decision |
| --- | --- | --- | --- |
| DuckDB | Parquet / analytics engine | parquet_reader.py - default engine; builds the SELECT over resolved nat... | use_now |
| Plotly | Dashboard and visualization | dashboard/pages/* - timeline charts from adoption_timeline.json, score... | use_now |
| PyArrow | Parquet / analytics engine | parquet_reader.py - schema introspection and the pandas-engine read pat... | use_now |
| Pydantic | Schema and validation | models.py - every model in the pipeline; checklist_loader.py and schema... | use_now |
| Streamlit | Dashboard and visualization | dashboard/app.py + dashboard/pages/* - reads the JSON artefacts named i... | use_now |
| pandas | Parquet / analytics engine | parquet_reader.py, exporters.py, dashboard/ - fallback read engine, CSV... | use_now |
| pytest | Testing | tests/ - operator semantics, scoring arithmetic, timestamp cutoff, deci... | use_now |
| Apache Superset | Dashboard and visualization | Would consume the exported artefacts or the Parquet corpus directly; no... | optional_later |
| Evidence.dev | Dashboard and visualization | Would render from the exported artefacts; an alternative to report.md,... | optional_later |
| IETF Datatracker API | RFC metadata and text | rfc_metadata.py - an additional backend behind the existing resolver, p... | optional_later |
| LangChain structured output | LLM structured extraction | llm_verifier.py - an alternative backend producing LLMVerification, sel... | optional_later |
| LlamaIndex | LLM structured extraction | llm_verifier.py - alternative to the LangChain backend; would also serv... | optional_later |
| Pandera | Schema and validation | parquet_reader.py - would validate the raw frame between read and norma... | optional_later |
| Polars | Parquet / analytics engine | parquet_reader.py - would become a third engine choice alongside 'duckd... | optional_later |
| RFC Editor RFCXML v3 | RFC metadata and text | data/rfc_checklists/ - a provenance field per indicator citing the RFC... | optional_later |
| ietfdata | RFC metadata and text | rfc_metadata.py - would implement the datatracker backend rather than c... | optional_later |
| xml2rfc | RFC metadata and text | Offline checklist-authoring tooling; would not be imported by the runti... | optional_later |
| Docling | LLM structured extraction | None. | reject_for_mvp |
| Great Expectations | Schema and validation | None. Its role would overlap schema_checker.py and any future Pandera c... | reject_for_mvp |

Survey summary: Generated by `openintel_rfc.tool_survey` for openintel-rfc-adoption-matcher v0.1.0.

The full survey, including tools that were considered and rejected, is in `open_source_tool_survey.md`.

## 4. Schema Cross-Check

50 indicators across 30 RFCs were checked against 19 dictionary fields before any measurement data was read.

| Queryability | Indicators | Share |
| --- | --- | --- |
| queryable | 36 | 72.0% |
| non_queryable | 8 | 16.0% |
| ambiguous | 3 | 6.0% |
| partially_queryable | 3 | 6.0% |

Dictionary fields that no indicator references: `key_tag`, `measurement_id`, `nsec3_flags`, `rsa_key_bitsize`, `source`, `timestamp`, `tlsa_selector`, `zone`.

Schema warnings:

- Dictionary field 'measurement_id' lists no openintel_native_fields, so the Parquet reader has no real OpenINTEL column to resolve it from; it will only be populated if a column of exactly that name exists.
- Field 'declared_standards_profile' is referenced by 1 indicator(s) (rfc9364_bcp_profile_declared) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'dnssec_ok_flag' is referenced by 2 indicator(s) (rfc4033_dnssec_ok_negotiated, rfc4035_dnssec_ok_negotiated) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. The closest defined field name is nsec3_flags.
- Field 'guidance_source_registry' is referenced by 1 indicator(s) (rfc9904_algorithm_guidance_process) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'key_rollover_phase' is referenced by 1 indicator(s) (rfc7583_rollover_timing_observed) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'name_algorithm_set_consistency' is referenced by 1 indicator(s) (rfc6840_mandatory_algorithm_rules) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'record_ttl' is referenced by 1 indicator(s) (rfc9077_nsec_ttl_bounded) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'resolver_synthesised_nxdomain' is referenced by 1 indicator(s) (rfc8198_aggressive_nsec_use) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'validator_algorithm_support' is referenced by 1 indicator(s) (rfc8624_validator_algorithm_support) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Indicator rfc4035_dnssec_ok_negotiated of RFC 4035 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc4035_dnssec_ok_negotiated is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: dnssec_ok_flag. No part of it can ever be evaluated against the measurement corpus.
- Indicator rfc6840_mandatory_algorithm_rules of RFC 6840 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc6840_mandatory_algorithm_rules is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: name_algorithm_set_consistency. No part of it can ever be evaluated against the measurement corpus.
- Indicator rfc7583_rollover_timing_observed of RFC 7583 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc7583_rollover_timing_observed is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: key_rollover_phase. No part of it can ever be evaluated against the measurement corpus.
- Indicator rfc8198_aggressive_nsec_use of RFC 8198 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc8198_aggressive_nsec_use is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: resolver_synthesised_nxdomain. No part of it can ever be evaluated against the measurement corpus.
- Indicator rfc8624_validator_algorithm_support of RFC 8624 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc8624_validator_algorithm_support is non-queryable: the field carrying its discriminating value, validator_algorithm_support, is absent from the OpenINTEL dictionary, and the only field that remains, rr_type (string), merely scopes which records are considered and is not used by any other RFC 8624 indicator, so nothing testable is left to attribute an observation to RFC 8624.
- Indicator rfc9364_bcp_profile_declared of RFC 9364 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc9364_bcp_profile_declared is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: declared_standards_profile. No part of it can ever be evaluated against the measurement corpus.
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

## 5. Queryable vs Non-Queryable Indicators

### 5.1 Queryable indicators

| RFC | Indicator | Role | Weight | Fields used |
| --- | --- | --- | --- | --- |
| RFC 3110 | rfc3110_rsasha1_algorithm | required | 9 | algorithm |
| RFC 3110 | rfc3110_rsasha1_on_key_or_signature | optional | 3 | rr_type, algorithm |
| RFC 4033 | rfc4033_base_dnssec_record_present | required | 4 | rr_type |
| RFC 4033 | rfc4033_dnssec_algorithm_present | optional | 2 | algorithm |
| RFC 4034 | rfc4034_core_record_present | required | 3 | rr_type |
| RFC 4034 | rfc4034_dnskey_protocol_is_three | optional | 7 | rr_type, dnskey_protocol |
| RFC 4034 | rfc4034_rrsig_type_covered_present | optional | 7 | rr_type, rrsig_type_covered |
| RFC 4509 | rfc4509_ds_sha256_digest | required | 9 | rr_type, digest_type |
| RFC 5011 | rfc5011_revoked_key_published | required | 8 | rr_type, flags |
| RFC 5155 | rfc5155_nsec3_hash_algorithm | optional | 3 | rr_type, algorithm |
| RFC 5155 | rfc5155_nsec3_record_present | required | 10 | rr_type |
| RFC 5702 | rfc5702_rsa_sha2_algorithm | required | 9 | algorithm |
| RFC 5702 | rfc5702_rsa_sha2_on_dnssec_record | optional | 3 | rr_type, algorithm |
| RFC 5933 | rfc5933_ecc_gost_algorithm | required | 10 | algorithm |
| RFC 5933 | rfc5933_gost_ds_digest | optional | 4 | rr_type, digest_type |
| RFC 6605 | rfc6605_ecdsa_algorithm | required | 9 | algorithm |
| RFC 6605 | rfc6605_ecdsa_on_key_or_signature | optional | 3 | rr_type, algorithm |
| RFC 6698 | rfc6698_tlsa_fields_well_formed | optional | 4 | tlsa_usage, tlsa_matchtype |
| RFC 6698 | rfc6698_tlsa_record_present | required | 10 | rr_type |
| RFC 7344 | rfc7344_cds_cdnskey_present | required | 9 | rr_type |
| RFC 7344 | rfc7344_cds_publishes_digest | optional | 3 | rr_type, digest_type |
| RFC 7671 | rfc7671_dane_usage_preferred | required | 8 | rr_type, tlsa_usage |
| RFC 8078 | rfc8078_cds_cdnskey_algorithm_zero | required | 10 | rr_type, algorithm |
| RFC 8078 | rfc8078_delete_signal_digest_zero | optional | 3 | rr_type, digest_type |
| RFC 8080 | rfc8080_eddsa_algorithm | required | 10 | algorithm |
| RFC 8080 | rfc8080_eddsa_on_key_or_signature | optional | 3 | rr_type, algorithm |
| RFC 9276 | rfc9276_empty_nsec3_salt | optional | 4 | rr_type, nsec3_salt |
| RFC 9276 | rfc9276_zero_nsec3_iterations | required | 10 | rr_type, nsec3_iterations |
| RFC 9558 | rfc9558_gost2012_algorithm | required | 10 | algorithm |
| RFC 9558 | rfc9558_gost2012_ds_digest | optional | 4 | rr_type, digest_type |
| RFC 9563 | rfc9563_sm2sm3_algorithm | required | 10 | algorithm |
| RFC 9563 | rfc9563_sm3_ds_digest | optional | 4 | rr_type, digest_type |
| RFC 9905 | rfc9905_deprecated_sha1_in_delegation | optional | 4 | rr_type, algorithm |
| RFC 9905 | rfc9905_deprecated_sha1_signature_still_published | required | 9 | rr_type, algorithm |
| RFC 9906 | rfc9906_deprecated_ecc_gost_still_published | required | 10 | algorithm |
| RFC 9906 | rfc9906_deprecated_gost_digest_still_published | optional | 4 | rr_type, digest_type |

### 5.2 Non-queryable indicators

| RFC | Indicator | Missing fields | Reason |
| --- | --- | --- | --- |
| RFC 4035 | rfc4035_dnssec_ok_negotiated | dnssec_ok_flag | Indicator rfc4035_dnssec_ok_negotiated is non-queryable because none of... |
| RFC 6840 | rfc6840_mandatory_algorithm_rules | name_algorithm_set_consistency | Indicator rfc6840_mandatory_algorithm_rules is non-queryable because no... |
| RFC 7583 | rfc7583_rollover_timing_observed | key_rollover_phase | Indicator rfc7583_rollover_timing_observed is non-queryable because non... |
| RFC 8198 | rfc8198_aggressive_nsec_use | resolver_synthesised_nxdomain | Indicator rfc8198_aggressive_nsec_use is non-queryable because none of... |
| RFC 8624 | rfc8624_validator_algorithm_support | validator_algorithm_support | Indicator rfc8624_validator_algorithm_support is non-queryable: the fie... |
| RFC 9364 | rfc9364_bcp_profile_declared | declared_standards_profile | Indicator rfc9364_bcp_profile_declared is non-queryable because none of... |
| RFC 9615 | rfc9615_bootstrap_signal_label | domain | Indicator rfc9615_bootstrap_signal_label is non-queryable: the field ca... |
| RFC 9904 | rfc9904_algorithm_guidance_process | guidance_source_registry | Indicator rfc9904_algorithm_guidance_process is non-queryable because n... |

These indicators are not scored as failures. They are excluded from evaluation and raised in the review queue, because a field the corpus does not carry is an absence of measurement, not evidence of absence.

### 5.3 Partially queryable and ambiguous indicators

| RFC | Indicator | Queryability | Missing fields | Reason |
| --- | --- | --- | --- | --- |
| RFC 4033 | rfc4033_dnssec_ok_negotiated | partially_queryable | dnssec_ok_flag | Indicator rfc4033_dnssec_ok_negotiated is partially queryable: rr_type... |
| RFC 7672 | rfc7672_smtp_dane_tlsa | partially_queryable | domain | Indicator rfc7672_smtp_dane_tlsa is partially queryable: rr_type (strin... |
| RFC 9077 | rfc9077_nsec_ttl_bounded | partially_queryable | record_ttl | Indicator rfc9077_nsec_ttl_bounded is partially queryable: rr_type (str... |
| RFC 6781 | rfc6781_ksk_zsk_separation | ambiguous | - | Indicator rfc6781_ksk_zsk_separation is ambiguous: every field it refer... |
| RFC 8624 | rfc8624_avoids_deprecated_algorithm | ambiguous | - | Indicator rfc8624_avoids_deprecated_algorithm is ambiguous: every field... |
| RFC 8624 | rfc8624_recommended_signing_algorithm | ambiguous | - | Indicator rfc8624_recommended_signing_algorithm is ambiguous: every fie... |

A partially queryable indicator can be evaluated on the fields that exist, but its verdict is weaker than the checklist intends. An ambiguous indicator is measurable yet not uniquely attributable to the RFC that lists it.

## 6. Observed OpenINTEL Signals

38 observations are shown below. These are a deterministic sample of the 1,875,584 rows scanned, not the corpus: the distributions in this section describe the sample and must not be read as corpus proportions. The exact per-RFC corpus counts are in section 7, covering 2009-09-01 to 2026-08-01.

- Distinct domains: 35.
- Distinct zones: 4.
- Observations carrying an algorithm number: 38.

Resource record types observed:

| Record type | Observations | Share |
| --- | --- | --- |
| DS | 38 | 100.0% |

DNSSEC algorithm numbers observed:

| Algorithm | Observations | Share |
| --- | --- | --- |
| 13 | 11 | 28.9% |
| 8 | 9 | 23.7% |
| 5 | 6 | 15.8% |
| 15 | 4 | 10.5% |
| 12 | 3 | 7.9% |
| 7 | 3 | 7.9% |
| 14 | 1 | 2.6% |
| 16 | 1 | 2.6% |

Each row is one record-level observation. A zone that publishes several records appears several times, so observation counts measure records seen, not zones deployed.

## 7. Ranked RFC Matches

| Rank | RFC | Title | Score | Confidence | Supporting observations | First seen |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | RFC 5933 | Use of GOST Signature Algorithms in DNSKEY and RRSIG Resource Records f... | 18 | very_high | 702 | 2013-01-01 |
| 2 | RFC 8080 | Edwards-Curve Digital Security Algorithm (EdDSA) for DNSSEC | 17.25 | very_high | 823 | 2022-09-01 |
| 3 | RFC 5702 | Use of SHA-2 Algorithms with RSA in DNSKEY and RRSIG Resource Records f... | 13.125 | very_high | 983357 | 2010-04-01 |
| 4 | RFC 6605 | Elliptic Curve Digital Signature Algorithm (DSA) for DNSSEC | 13.125 | very_high | 502557 | 2015-12-01 |
| 5 | RFC 4509 | Use of SHA-256 in DNSSEC Delegation Signer (DS) Resource Records | 11.25 | high | 1079660 | 2009-04-01 |
| 6 | RFC 3110 | RSA/SHA-1 SIGs and RSA KEYs in the Domain Name System (DNS) | 11.25 | high | 241967 | 2009-04-01 |
| 7 | RFC 4033 | DNS Security Introduction and Requirements (DNSSEC base: RFC 4033/4034/... | 3.75 | low | 1875584 | 2009-04-01 |
| 8 | RFC 8624 | Algorithm Implementation Requirements and Usage Guidance for DNSSEC | 3.375 | low | 443137 | 2019-06-01 |
| 9 | RFC 4034 | Resource Records for the DNS Security Extensions | 3 | low | 1875584 | 2009-04-01 |

Score is the best per-signal score for that RFC, after the specificity multiplier (very_high 1.5, high 1.25, medium 1.0, low 0.75) has been applied. A broad RFC with many observations can therefore rank below a narrow RFC with one unambiguous observation, which is the intended behaviour: specificity is evidence.

Per-candidate evidence breakdown:

| RFC | Best score | Aggregate score | Valid | Partial | Timestamp-invalid | Matched indicators |
| --- | --- | --- | --- | --- | --- | --- |
| RFC 5933 | 18 | 48 | 702 | 19865 | 0 | rfc5933_ecc_gost_algorithm, rfc5933_gost_ds_digest |
| RFC 8080 | 17.25 | 86.25 | 823 | 0 | 0 | rfc8080_eddsa_algorithm, rfc8080_eddsa_on_key_or_signature |
| RFC 5702 | 13.125 | 118.125 | 983357 | 0 | 0 | rfc5702_rsa_sha2_algorithm, rfc5702_rsa_sha2_on_dnssec_record |
| RFC 6605 | 13.125 | 157.5 | 502557 | 0 | 0 | rfc6605_ecdsa_algorithm, rfc6605_ecdsa_on_key_or_signature |
| RFC 4509 | 11.25 | 135 | 1079660 | 0 | 0 | rfc4509_ds_sha256_digest |
| RFC 3110 | 11.25 | 67.5 | 241967 | 0 | 0 | rfc3110_rsasha1_algorithm |
| RFC 4033 | 3.75 | 142.5 | 1875584 | 0 | 0 | rfc4033_base_dnssec_record_present, rfc4033_dnssec_algorithm_present |
| RFC 8624 | 3.375 | 47.25 | 0 | 796344 | 636103 | rfc8624_avoids_deprecated_algorithm, rfc8624_recommended_signing_algori... |
| RFC 4034 | 3 | 114 | 1875584 | 0 | 0 | rfc4034_core_record_present |

## 8. Reasoning Summary

Every one of the 1140 signal-by-RFC evaluations carries a stored reasoning trace: the conditions that passed, the conditions that failed, the fields that were missing, the timestamp verdict and the arithmetic of the score. Non-matches are traced too, because the reason an RFC was *not* selected is as much a result as the reason one was.

| Decision | Traces | Share |
| --- | --- | --- |
| no_match | 681 | 59.7% |
| non_queryable | 266 | 23.3% |
| valid_match | 123 | 10.8% |
| partial_match | 35 | 3.1% |
| timestamp_invalid | 21 | 1.8% |
| ambiguous | 14 | 1.2% |

Verbatim reasoning summaries from this run:

**trace_sig_0006_rfc5933** - RFC 5933, signal `sig_0006`, decision `valid_match`, score 18.0:

> RFC 5933 matched signal sig_0006: the required indicator rfc5933_ecc_gost_algorithm passed because algorithm=12 equals the expected value 12. Corroborating indicators also matched: rfc5933_gost_ds_digest. The observation on 2015-06-01 is 1796 days after RFC 5933's publication on 2010-07-01, so the timestamp is valid. Score 18.0 (very_high) = (10.0 required + 2.0 optional) x 1.5 very_high specificity.

**trace_sig_0006_rfc9906** - RFC 9906, signal `sig_0006`, decision `timestamp_invalid`, score 0.0:

> RFC 9906 cannot explain signal sig_0006: although algorithm=12 satisfy the required indicator rfc9906_deprecated_ecc_gost_still_published, the observation on 2015-06-01 predates RFC 9906's publication on 2025-11-01 by 3806 days. An observation cannot evidence adoption of an RFC that did not yet exist, so the score of 18.0 is forfeited and this is routed to the review queue. The withheld score derives from (10.0 required + 2.0 optional) x 1.5 very_high specificity.

**trace_sig_0032_rfc8624** - RFC 8624, signal `sig_0032`, decision `ambiguous`, score 3.375:

> RFC 8624 is an ambiguous match for signal sig_0032: the required indicator rfc8624_recommended_signing_algorithm passed because algorithm=15 is in [13, 15]. Corroborating indicators also matched: rfc8624_avoids_deprecated_algorithm. The checklist flags rfc8624_avoids_deprecated_algorithm, rfc8624_recommended_signing_algorithm ambiguous: the same observation is equally explained by other RFCs, so the match is penalized and sent to the review queue rather than reported as adoption. The observation on 2026-04-01 is 2496 days after RFC 8624's publication on 2019-06-01, so the timestamp is valid. Score 3.375 (low) = (5.0 required + 1.5 optional - 2.0 ambiguity penalty) x 0.75 low specificity.

## 9. First-Seen Dates / Adoption Timeline

First-seen is the earliest *valid* match: an observation dated at or after the RFC's publication date. It is the first date this corpus saw the mechanism, which is an upper bound on when deployment began and says nothing about deployment before the measurement window.

| RFC | Published | First seen | Last seen | Days from publication | Observations | Distinct domains |
| --- | --- | --- | --- | --- | --- | --- |
| RFC 3110 | 2001-05-01 | 2009-04-01 | 2026-08-01 | 2892 | 241967 | 1042 |
| RFC 4033 | 2005-03-01 | 2009-04-01 | 2026-08-01 | 1492 | 1875584 | 10930 |
| RFC 4034 | 2005-03-01 | 2009-04-01 | 2026-08-01 | 1492 | 1875584 | 10930 |
| RFC 4509 | 2006-05-01 | 2009-04-01 | 2026-08-01 | 1066 | 1079660 | 10535 |
| RFC 5702 | 2009-10-01 | 2010-04-01 | 2026-08-01 | 182 | 983357 | 5213 |
| RFC 5933 | 2010-07-01 | 2013-01-01 | 2015-09-01 | 915 | 702 | 5 |
| RFC 6605 | 2012-04-01 | 2015-12-01 | 2026-08-01 | 1339 | 502557 | 5093 |
| RFC 8624 | 2019-06-01 | 2019-06-01 | 2026-08-01 | 0 | 443137 | 4894 |
| RFC 8080 | 2017-02-01 | 2022-09-01 | 2026-08-01 | 2038 | 823 | 34 |
| RFC 4035 | 2005-03-01 | - | - | - | 0 | 0 |
| RFC 5011 | 2007-09-01 | - | - | - | 0 | 0 |
| RFC 5155 | 2008-03-01 | - | - | - | 0 | 0 |
| RFC 6698 | 2012-08-01 | - | - | - | 0 | 0 |
| RFC 6781 | 2012-12-01 | - | - | - | 0 | 0 |
| RFC 6840 | 2013-02-01 | - | - | - | 0 | 0 |
| RFC 7344 | 2014-09-01 | - | - | - | 0 | 0 |
| RFC 7583 | 2015-10-01 | - | - | - | 0 | 0 |
| RFC 7671 | 2015-10-01 | - | - | - | 0 | 0 |
| RFC 7672 | 2015-10-01 | - | - | - | 0 | 0 |
| RFC 8078 | 2017-03-01 | - | - | - | 0 | 0 |
| RFC 8198 | 2017-07-01 | - | - | - | 0 | 0 |
| RFC 9077 | 2021-07-01 | - | - | - | 0 | 0 |
| RFC 9276 | 2022-08-01 | - | - | - | 0 | 0 |
| RFC 9364 | 2023-02-01 | - | - | - | 0 | 0 |
| RFC 9558 | 2024-04-01 | - | - | - | 0 | 0 |
| RFC 9563 | 2024-12-01 | - | - | - | 0 | 0 |
| RFC 9615 | 2024-07-01 | - | - | - | 0 | 0 |
| RFC 9904 | 2025-11-01 | - | - | - | 0 | 0 |
| RFC 9905 | 2025-11-01 | - | - | - | 0 | 0 |
| RFC 9906 | 2025-11-01 | - | - | - | 0 | 0 |

Monthly observation buckets (valid matches only):

| RFC | Period | Observations | Domains | Mean score |
| --- | --- | --- | --- | --- |
| RFC 3110 | 2009-04 | 342 | 172 | 11.25 |
| RFC 3110 | 2009-05 | 342 | 172 | 11.25 |
| RFC 3110 | 2009-08 | 320 | 171 | 11.25 |
| RFC 3110 | 2009-09 | 320 | 171 | 11.25 |
| RFC 3110 | 2009-10 | 320 | 171 | 11.25 |
| RFC 3110 | 2009-11 | 320 | 171 | 11.25 |
| RFC 3110 | 2009-12 | 320 | 171 | 11.25 |
| RFC 3110 | 2010-01 | 320 | 171 | 11.25 |
| RFC 3110 | 2010-02 | 330 | 176 | 11.25 |
| RFC 3110 | 2010-03 | 388 | 194 | 11.25 |
| RFC 3110 | 2010-04 | 514 | 269 | 11.25 |
| RFC 3110 | 2010-05 | 530 | 280 | 11.25 |
| RFC 3110 | 2010-06 | 598 | 283 | 11.25 |
| RFC 3110 | 2010-07 | 594 | 283 | 11.25 |
| RFC 3110 | 2010-08 | 806 | 413 | 11.25 |
| RFC 3110 | 2010-09 | 806 | 413 | 11.25 |
| RFC 3110 | 2010-10 | 870 | 413 | 11.25 |
| RFC 3110 | 2010-11 | 884 | 393 | 11.25 |
| RFC 3110 | 2011-05 | 665 | 394 | 11.25 |
| RFC 3110 | 2011-06 | 1083 | 448 | 11.25 |
| RFC 3110 | 2011-07 | 1133 | 451 | 11.25 |
| RFC 3110 | 2011-08 | 948 | 451 | 11.25 |
| RFC 3110 | 2011-09 | 1440 | 455 | 11.25 |
| RFC 3110 | 2011-10 | 1718 | 456 | 11.25 |
| RFC 3110 | 2011-11 | 1700 | 444 | 11.25 |
| RFC 3110 | 2011-12 | 1712 | 447 | 11.25 |
| RFC 3110 | 2012-01 | 2087 | 540 | 11.25 |
| RFC 3110 | 2012-02 | 1879 | 551 | 11.25 |
| RFC 3110 | 2012-03 | 1879 | 547 | 11.25 |
| RFC 3110 | 2012-04 | 1901 | 552 | 11.25 |
| RFC 3110 | 2012-05 | 1917 | 552 | 11.25 |
| RFC 3110 | 2012-06 | 1932 | 552 | 11.25 |
| RFC 3110 | 2012-08 | 1986 | 558 | 11.25 |
| RFC 3110 | 2012-09 | 2000 | 558 | 11.25 |
| RFC 3110 | 2012-10 | 2004 | 562 | 11.25 |
| RFC 3110 | 2012-11 | 2001 | 560 | 11.25 |
| RFC 3110 | 2012-12 | 1940 | 552 | 11.25 |
| RFC 3110 | 2013-01 | 2109 | 575 | 11.25 |
| RFC 3110 | 2013-02 | 2132 | 575 | 11.25 |
| RFC 3110 | 2013-03 | 2160 | 583 | 11.25 |
| RFC 3110 | 2013-04 | 2176 | 583 | 11.25 |
| RFC 3110 | 2013-05 | 2188 | 583 | 11.25 |
| RFC 3110 | 2013-06 | 2190 | 583 | 11.25 |
| RFC 3110 | 2013-07 | 2206 | 598 | 11.25 |
| RFC 3110 | 2013-08 | 2250 | 615 | 11.25 |
| RFC 3110 | 2013-09 | 2250 | 615 | 11.25 |
| RFC 3110 | 2013-10 | 2261 | 651 | 11.25 |
| RFC 3110 | 2013-11 | 2271 | 651 | 11.25 |
| RFC 3110 | 2013-12 | 2989 | 757 | 11.25 |
| RFC 3110 | 2014-01 | 2989 | 757 | 11.25 |
| RFC 3110 | 2014-02 | 3002 | 757 | 11.25 |
| RFC 3110 | 2014-03 | 2994 | 757 | 11.25 |
| RFC 3110 | 2014-04 | 2962 | 746 | 11.25 |
| RFC 3110 | 2014-05 | 2986 | 765 | 11.25 |
| RFC 3110 | 2014-06 | 2972 | 765 | 11.25 |
| RFC 3110 | 2014-07 | 2998 | 765 | 11.25 |
| RFC 3110 | 2014-08 | 3044 | 770 | 11.25 |
| RFC 3110 | 2014-09 | 3137 | 791 | 11.25 |
| RFC 3110 | 2014-10 | 2650 | 820 | 11.25 |
| RFC 3110 | 2014-11 | 2672 | 835 | 11.25 |
| RFC 3110 | 2014-12 | 2688 | 862 | 11.25 |
| RFC 3110 | 2015-01 | 2750 | 867 | 11.25 |
| RFC 3110 | 2015-02 | 2748 | 867 | 11.25 |
| RFC 3110 | 2015-03 | 2758 | 874 | 11.25 |
| RFC 3110 | 2015-04 | 2878 | 882 | 11.25 |
| RFC 3110 | 2015-05 | 2807 | 854 | 11.25 |
| RFC 3110 | 2015-06 | 3121 | 976 | 11.25 |
| RFC 3110 | 2015-07 | 3591 | 995 | 11.25 |
| RFC 3110 | 2015-08 | 3681 | 1032 | 11.25 |
| RFC 3110 | 2015-09 | 3348 | 1042 | 11.25 |
| RFC 3110 | 2015-10 | 1069 | 293 | 11.25 |
| RFC 3110 | 2015-11 | 1074 | 299 | 11.25 |
| RFC 3110 | 2015-12 | 1074 | 299 | 11.25 |
| RFC 3110 | 2016-01 | 1060 | 292 | 11.25 |
| RFC 3110 | 2016-02 | 1042 | 291 | 11.25 |
| RFC 3110 | 2016-04 | 1044 | 285 | 11.25 |
| RFC 3110 | 2016-05 | 1038 | 286 | 11.25 |
| RFC 3110 | 2016-06 | 1044 | 285 | 11.25 |
| RFC 3110 | 2016-07 | 1026 | 285 | 11.25 |
| RFC 3110 | 2016-08 | 989 | 257 | 11.25 |
| RFC 3110 | 2016-09 | 1004 | 259 | 11.25 |
| RFC 3110 | 2016-10 | 1004 | 253 | 11.25 |
| RFC 3110 | 2016-11 | 1004 | 253 | 11.25 |
| RFC 3110 | 2016-12 | 997 | 252 | 11.25 |
| RFC 3110 | 2017-01 | 989 | 247 | 11.25 |
| RFC 3110 | 2017-02 | 990 | 247 | 11.25 |
| RFC 3110 | 2017-03 | 990 | 247 | 11.25 |
| RFC 3110 | 2017-04 | 1179 | 299 | 11.25 |
| RFC 3110 | 2017-05 | 1163 | 294 | 11.25 |
| RFC 3110 | 2017-06 | 993 | 251 | 11.25 |
| RFC 3110 | 2017-07 | 987 | 250 | 11.25 |
| RFC 3110 | 2017-08 | 989 | 253 | 11.25 |
| RFC 3110 | 2017-09 | 1002 | 264 | 11.25 |
| RFC 3110 | 2017-10 | 988 | 264 | 11.25 |
| RFC 3110 | 2017-11 | 986 | 264 | 11.25 |
| RFC 3110 | 2017-12 | 991 | 264 | 11.25 |
| RFC 3110 | 2018-01 | 993 | 264 | 11.25 |
| RFC 3110 | 2018-02 | 993 | 264 | 11.25 |
| RFC 3110 | 2018-03 | 991 | 255 | 11.25 |
| RFC 3110 | 2018-04 | 991 | 255 | 11.25 |
| RFC 3110 | 2018-05 | 997 | 265 | 11.25 |
| RFC 3110 | 2018-06 | 997 | 265 | 11.25 |
| RFC 3110 | 2018-07 | 988 | 258 | 11.25 |
| RFC 3110 | 2018-08 | 990 | 258 | 11.25 |
| RFC 3110 | 2018-09 | 990 | 258 | 11.25 |
| RFC 3110 | 2018-10 | 990 | 258 | 11.25 |
| RFC 3110 | 2018-11 | 1015 | 280 | 11.25 |
| RFC 3110 | 2018-12 | 1016 | 282 | 11.25 |
| RFC 3110 | 2019-01 | 1018 | 293 | 11.25 |
| RFC 3110 | 2019-02 | 1021 | 290 | 11.25 |
| RFC 3110 | 2019-03 | 1004 | 275 | 11.25 |
| RFC 3110 | 2019-04 | 1006 | 275 | 11.25 |
| RFC 3110 | 2019-05 | 929 | 275 | 11.25 |
| RFC 3110 | 2019-06 | 893 | 282 | 11.25 |
| RFC 3110 | 2019-07 | 893 | 282 | 11.25 |
| RFC 3110 | 2019-08 | 849 | 245 | 11.25 |
| RFC 3110 | 2019-09 | 849 | 245 | 11.25 |
| RFC 3110 | 2019-10 | 841 | 243 | 11.25 |
| RFC 3110 | 2019-11 | 841 | 243 | 11.25 |
| RFC 3110 | 2019-12 | 843 | 245 | 11.25 |
| RFC 3110 | 2020-01 | 839 | 242 | 11.25 |
| RFC 3110 | 2020-02 | 853 | 234 | 11.25 |
| RFC 3110 | 2020-03 | 853 | 234 | 11.25 |
| RFC 3110 | 2020-04 | 855 | 234 | 11.25 |
| RFC 3110 | 2020-05 | 858 | 234 | 11.25 |
| RFC 3110 | 2020-06 | 1880 | 516 | 11.25 |
| RFC 3110 | 2020-07 | 1288 | 317 | 11.25 |
| RFC 3110 | 2020-08 | 834 | 211 | 11.25 |
| RFC 3110 | 2020-09 | 834 | 211 | 11.25 |
| RFC 3110 | 2020-10 | 824 | 207 | 11.25 |
| RFC 3110 | 2020-11 | 816 | 204 | 11.25 |
| RFC 3110 | 2020-12 | 832 | 209 | 11.25 |
| RFC 3110 | 2021-02 | 835 | 209 | 11.25 |
| RFC 3110 | 2021-03 | 835 | 209 | 11.25 |
| RFC 3110 | 2021-04 | 835 | 209 | 11.25 |
| RFC 3110 | 2021-05 | 844 | 210 | 11.25 |
| RFC 3110 | 2021-06 | 786 | 185 | 11.25 |
| RFC 3110 | 2021-07 | 792 | 187 | 11.25 |
| RFC 3110 | 2021-08 | 792 | 187 | 11.25 |
| RFC 3110 | 2021-09 | 776 | 187 | 11.25 |
| RFC 3110 | 2021-10 | 777 | 187 | 11.25 |
| RFC 3110 | 2021-11 | 777 | 187 | 11.25 |
| RFC 3110 | 2021-12 | 792 | 197 | 11.25 |
| RFC 3110 | 2022-01 | 813 | 212 | 11.25 |
| RFC 3110 | 2022-02 | 799 | 197 | 11.25 |
| RFC 3110 | 2022-03 | 809 | 211 | 11.25 |
| RFC 3110 | 2022-04 | 796 | 197 | 11.25 |
| RFC 3110 | 2022-05 | 797 | 197 | 11.25 |
| RFC 3110 | 2022-06 | 797 | 197 | 11.25 |
| RFC 3110 | 2022-07 | 797 | 197 | 11.25 |
| RFC 3110 | 2022-08 | 797 | 197 | 11.25 |
| RFC 3110 | 2022-09 | 797 | 197 | 11.25 |
| RFC 3110 | 2022-10 | 797 | 205 | 11.25 |
| RFC 3110 | 2022-11 | 798 | 207 | 11.25 |
| RFC 3110 | 2022-12 | 793 | 208 | 11.25 |
| RFC 3110 | 2023-01 | 784 | 196 | 11.25 |
| RFC 3110 | 2023-02 | 782 | 195 | 11.25 |
| RFC 3110 | 2023-03 | 785 | 196 | 11.25 |
| RFC 3110 | 2023-04 | 782 | 194 | 11.25 |
| RFC 3110 | 2023-05 | 782 | 194 | 11.25 |
| RFC 3110 | 2023-06 | 782 | 194 | 11.25 |
| RFC 3110 | 2023-07 | 782 | 194 | 11.25 |
| RFC 3110 | 2023-08 | 782 | 194 | 11.25 |
| RFC 3110 | 2023-09 | 787 | 207 | 11.25 |
| RFC 3110 | 2023-10 | 777 | 203 | 11.25 |
| RFC 3110 | 2023-11 | 798 | 213 | 11.25 |
| RFC 3110 | 2023-12 | 798 | 213 | 11.25 |
| RFC 3110 | 2024-01 | 782 | 200 | 11.25 |
| RFC 3110 | 2024-02 | 761 | 197 | 11.25 |
| RFC 3110 | 2024-03 | 756 | 194 | 11.25 |
| RFC 3110 | 2024-04 | 750 | 198 | 11.25 |
| RFC 3110 | 2024-05 | 750 | 198 | 11.25 |
| RFC 3110 | 2024-06 | 814 | 247 | 11.25 |
| RFC 3110 | 2024-07 | 728 | 190 | 11.25 |
| RFC 3110 | 2024-08 | 726 | 190 | 11.25 |
| RFC 3110 | 2024-09 | 714 | 176 | 11.25 |
| RFC 3110 | 2024-10 | 715 | 177 | 11.25 |
| RFC 3110 | 2024-11 | 715 | 177 | 11.25 |
| RFC 3110 | 2024-12 | 713 | 169 | 11.25 |
| RFC 3110 | 2025-01 | 696 | 160 | 11.25 |
| RFC 3110 | 2025-02 | 696 | 160 | 11.25 |
| RFC 3110 | 2025-03 | 694 | 160 | 11.25 |
| RFC 3110 | 2025-04 | 673 | 151 | 11.25 |
| RFC 3110 | 2025-05 | 673 | 151 | 11.25 |
| RFC 3110 | 2025-06 | 673 | 151 | 11.25 |
| RFC 3110 | 2025-07 | 669 | 151 | 11.25 |
| RFC 3110 | 2025-08 | 669 | 151 | 11.25 |
| RFC 3110 | 2025-09 | 664 | 150 | 11.25 |
| RFC 3110 | 2025-10 | 664 | 150 | 11.25 |
| RFC 3110 | 2025-11 | 664 | 150 | 11.25 |
| RFC 3110 | 2025-12 | 663 | 149 | 11.25 |
| RFC 3110 | 2026-01 | 663 | 149 | 11.25 |
| RFC 3110 | 2026-02 | 663 | 149 | 11.25 |
| RFC 3110 | 2026-03 | 659 | 148 | 11.25 |
| RFC 3110 | 2026-04 | 629 | 132 | 11.25 |
| RFC 3110 | 2026-05 | 629 | 132 | 11.25 |
| RFC 3110 | 2026-06 | 610 | 119 | 11.25 |
| RFC 3110 | 2026-07 | 610 | 119 | 11.25 |
| RFC 3110 | 2026-08 | 603 | 118 | 11.25 |
| RFC 4033 | 2009-04 | 350 | 176 | 3.75 |
| RFC 4033 | 2009-05 | 350 | 176 | 3.75 |
| RFC 4033 | 2009-08 | 412 | 189 | 3.75 |
| RFC 4033 | 2009-09 | 412 | 189 | 3.75 |
| RFC 4033 | 2009-10 | 412 | 189 | 3.75 |
| RFC 4033 | 2009-11 | 412 | 189 | 3.75 |
| RFC 4033 | 2009-12 | 448 | 198 | 3.75 |
| RFC 4033 | 2010-01 | 448 | 198 | 3.75 |
| RFC 4033 | 2010-02 | 458 | 202 | 3.75 |
| RFC 4033 | 2010-03 | 516 | 216 | 3.75 |
| RFC 4033 | 2010-04 | 646 | 278 | 3.75 |
| RFC 4033 | 2010-05 | 662 | 290 | 3.75 |
| RFC 4033 | 2010-06 | 730 | 294 | 3.75 |
| RFC 4033 | 2010-07 | 730 | 294 | 3.75 |
| RFC 4033 | 2010-08 | 946 | 420 | 3.75 |
| RFC 4033 | 2010-09 | 948 | 420 | 3.75 |
| RFC 4033 | 2010-10 | 1016 | 420 | 3.75 |
| RFC 4033 | 2010-11 | 1030 | 399 | 3.75 |
| RFC 4033 | 2011-05 | 811 | 437 | 3.75 |
| RFC 4033 | 2011-06 | 1240 | 501 | 3.75 |
| RFC 4033 | 2011-07 | 1293 | 504 | 3.75 |
| RFC 4033 | 2011-08 | 1187 | 515 | 3.75 |
| RFC 4033 | 2011-09 | 1843 | 546 | 3.75 |
| RFC 4033 | 2011-10 | 2123 | 547 | 3.75 |
| RFC 4033 | 2011-11 | 2426 | 596 | 3.75 |
| RFC 4033 | 2011-12 | 2438 | 599 | 3.75 |
| RFC 4033 | 2012-01 | 2857 | 702 | 3.75 |
| RFC 4033 | 2012-02 | 2839 | 813 | 3.75 |
| RFC 4033 | 2012-03 | 2881 | 829 | 3.75 |
| RFC 4033 | 2012-04 | 2918 | 836 | 3.75 |
| RFC 4033 | 2012-05 | 2939 | 836 | 3.75 |
| RFC 4033 | 2012-06 | 3203 | 873 | 3.75 |
| RFC 4033 | 2012-08 | 3251 | 887 | 3.75 |
| RFC 4033 | 2012-09 | 3268 | 903 | 3.75 |
| RFC 4033 | 2012-10 | 3275 | 915 | 3.75 |
| RFC 4033 | 2012-11 | 3575 | 929 | 3.75 |
| RFC 4033 | 2012-12 | 3745 | 929 | 3.75 |
| RFC 4033 | 2013-01 | 3931 | 991 | 3.75 |
| RFC 4033 | 2013-02 | 4242 | 1038 | 3.75 |
| RFC 4033 | 2013-03 | 4024 | 1019 | 3.75 |
| RFC 4033 | 2013-04 | 4088 | 1019 | 3.75 |
| RFC 4033 | 2013-05 | 4122 | 1053 | 3.75 |
| RFC 4033 | 2013-06 | 4246 | 1074 | 3.75 |
| RFC 4033 | 2013-07 | 4379 | 1129 | 3.75 |
| RFC 4033 | 2013-08 | 4609 | 1174 | 3.75 |
| RFC 4033 | 2013-09 | 4681 | 1185 | 3.75 |
| RFC 4033 | 2013-10 | 4768 | 1256 | 3.75 |
| RFC 4033 | 2013-11 | 4784 | 1320 | 3.75 |
| RFC 4033 | 2013-12 | 5642 | 1477 | 3.75 |
| RFC 4033 | 2014-01 | 5867 | 1481 | 3.75 |
| RFC 4033 | 2014-02 | 6251 | 1533 | 3.75 |
| RFC 4033 | 2014-03 | 6313 | 1625 | 3.75 |
| RFC 4033 | 2014-04 | 6517 | 1668 | 3.75 |
| RFC 4033 | 2014-05 | 6614 | 1737 | 3.75 |
| RFC 4033 | 2014-06 | 6600 | 1753 | 3.75 |
| RFC 4033 | 2014-07 | 6684 | 1791 | 3.75 |
| RFC 4033 | 2014-08 | 6732 | 1823 | 3.75 |
| RFC 4033 | 2014-09 | 7785 | 1940 | 3.75 |
| RFC 4033 | 2014-10 | 6114 | 2106 | 3.75 |
| RFC 4033 | 2014-11 | 6455 | 2470 | 3.75 |
| RFC 4033 | 2014-12 | 6970 | 2597 | 3.75 |
| RFC 4033 | 2015-01 | 6906 | 2597 | 3.75 |
| RFC 4033 | 2015-02 | 6888 | 2597 | 3.75 |
| RFC 4033 | 2015-03 | 6890 | 2614 | 3.75 |
| RFC 4033 | 2015-04 | 7838 | 2703 | 3.75 |
| RFC 4033 | 2015-05 | 7817 | 2639 | 3.75 |
| RFC 4033 | 2015-06 | 8276 | 2875 | 3.75 |
| RFC 4033 | 2015-07 | 8466 | 2717 | 3.75 |
| RFC 4033 | 2015-08 | 8924 | 2919 | 3.75 |
| RFC 4033 | 2015-09 | 7848 | 2934 | 3.75 |
| RFC 4033 | 2015-10 | 3059 | 1072 | 3.75 |
| RFC 4033 | 2015-11 | 3075 | 1072 | 3.75 |
| RFC 4033 | 2015-12 | 4461 | 1438 | 3.75 |
| RFC 4033 | 2016-01 | 4442 | 1438 | 3.75 |
| RFC 4033 | 2016-02 | 4411 | 1438 | 3.75 |
| RFC 4033 | 2016-04 | 4490 | 1487 | 3.75 |
| RFC 4033 | 2016-05 | 4487 | 1441 | 3.75 |
| RFC 4033 | 2016-06 | 4500 | 1441 | 3.75 |
| RFC 4033 | 2016-07 | 4544 | 1452 | 3.75 |
| RFC 4033 | 2016-08 | 4559 | 1443 | 3.75 |
| RFC 4033 | 2016-09 | 4575 | 1443 | 3.75 |
| RFC 4033 | 2016-10 | 4700 | 1500 | 3.75 |
| RFC 4033 | 2016-11 | 4752 | 1552 | 3.75 |
| RFC 4033 | 2016-12 | 7637 | 2506 | 3.75 |
| RFC 4033 | 2017-01 | 8571 | 2883 | 3.75 |
| RFC 4033 | 2017-02 | 8867 | 2839 | 3.75 |
| RFC 4033 | 2017-03 | 8875 | 2834 | 3.75 |
| RFC 4033 | 2017-04 | 8781 | 2770 | 3.75 |
| RFC 4033 | 2017-05 | 8801 | 2821 | 3.75 |
| RFC 4033 | 2017-06 | 8808 | 2821 | 3.75 |
| RFC 4033 | 2017-07 | 9004 | 2869 | 3.75 |
| RFC 4033 | 2017-08 | 8996 | 2903 | 3.75 |
| RFC 4033 | 2017-09 | 10325 | 3045 | 3.75 |
| RFC 4033 | 2017-10 | 10195 | 3046 | 3.75 |
| RFC 4033 | 2017-11 | 10199 | 3046 | 3.75 |
| RFC 4033 | 2017-12 | 10257 | 3046 | 3.75 |
| RFC 4033 | 2018-01 | 10262 | 3081 | 3.75 |
| RFC 4033 | 2018-02 | 10309 | 3144 | 3.75 |
| RFC 4033 | 2018-03 | 10225 | 2963 | 3.75 |
| RFC 4033 | 2018-04 | 10239 | 2963 | 3.75 |
| RFC 4033 | 2018-05 | 10169 | 2994 | 3.75 |
| RFC 4033 | 2018-06 | 11109 | 3023 | 3.75 |
| RFC 4033 | 2018-07 | 11255 | 3075 | 3.75 |
| RFC 4033 | 2018-08 | 11265 | 3075 | 3.75 |
| RFC 4033 | 2018-09 | 11362 | 3086 | 3.75 |
| RFC 4033 | 2018-10 | 11357 | 3086 | 3.75 |
| RFC 4033 | 2018-11 | 11675 | 3181 | 3.75 |
| RFC 4033 | 2018-12 | 12898 | 3572 | 3.75 |
| RFC 4033 | 2019-01 | 13479 | 3858 | 3.75 |
| RFC 4033 | 2019-02 | 14673 | 4144 | 3.75 |
| RFC 4033 | 2019-03 | 14834 | 4245 | 3.75 |
| RFC 4033 | 2019-04 | 14879 | 4273 | 3.75 |
| RFC 4033 | 2019-05 | 9433 | 4267 | 3.75 |
| RFC 4033 | 2019-06 | 10713 | 4769 | 3.75 |
| RFC 4033 | 2019-07 | 11488 | 5263 | 3.75 |
| RFC 4033 | 2019-08 | 11514 | 5273 | 3.75 |
| RFC 4033 | 2019-09 | 11601 | 5428 | 3.75 |
| RFC 4033 | 2019-10 | 11710 | 5442 | 3.75 |
| RFC 4033 | 2019-11 | 11737 | 5444 | 3.75 |
| RFC 4033 | 2019-12 | 11811 | 5450 | 3.75 |
| RFC 4033 | 2020-01 | 12646 | 6408 | 3.75 |
| RFC 4033 | 2020-02 | 12728 | 6554 | 3.75 |
| RFC 4033 | 2020-03 | 12754 | 6578 | 3.75 |
| RFC 4033 | 2020-04 | 12763 | 6578 | 3.75 |
| RFC 4033 | 2020-05 | 12870 | 6619 | 3.75 |
| RFC 4033 | 2020-06 | 13915 | 6885 | 3.75 |
| RFC 4033 | 2020-07 | 13377 | 6701 | 3.75 |
| RFC 4033 | 2020-08 | 12837 | 6547 | 3.75 |
| RFC 4033 | 2020-09 | 12911 | 6554 | 3.75 |
| RFC 4033 | 2020-10 | 12962 | 6604 | 3.75 |
| RFC 4033 | 2020-11 | 13114 | 6700 | 3.75 |
| RFC 4033 | 2020-12 | 13360 | 6853 | 3.75 |
| RFC 4033 | 2021-02 | 13762 | 6932 | 3.75 |
| RFC 4033 | 2021-03 | 13824 | 7039 | 3.75 |
| RFC 4033 | 2021-04 | 14068 | 7208 | 3.75 |
| RFC 4033 | 2021-05 | 14135 | 7232 | 3.75 |
| RFC 4033 | 2021-06 | 14110 | 7251 | 3.75 |
| RFC 4033 | 2021-07 | 14099 | 7279 | 3.75 |
| RFC 4033 | 2021-08 | 14215 | 7281 | 3.75 |
| RFC 4033 | 2021-09 | 14392 | 7504 | 3.75 |
| RFC 4033 | 2021-10 | 14514 | 7601 | 3.75 |
| RFC 4033 | 2021-11 | 14635 | 7766 | 3.75 |
| RFC 4033 | 2021-12 | 14860 | 7795 | 3.75 |
| RFC 4033 | 2022-01 | 15027 | 7874 | 3.75 |
| RFC 4033 | 2022-02 | 15210 | 7848 | 3.75 |
| RFC 4033 | 2022-03 | 15371 | 7927 | 3.75 |
| RFC 4033 | 2022-04 | 15436 | 7978 | 3.75 |
| RFC 4033 | 2022-05 | 15682 | 8168 | 3.75 |
| RFC 4033 | 2022-06 | 15962 | 8348 | 3.75 |
| RFC 4033 | 2022-07 | 16063 | 8528 | 3.75 |
| RFC 4033 | 2022-08 | 16153 | 8646 | 3.75 |
| RFC 4033 | 2022-09 | 16255 | 8761 | 3.75 |
| RFC 4033 | 2022-10 | 16189 | 8776 | 3.75 |
| RFC 4033 | 2022-11 | 15933 | 8814 | 3.75 |
| RFC 4033 | 2022-12 | 15992 | 8912 | 3.75 |
| RFC 4033 | 2023-01 | 16025 | 9031 | 3.75 |
| RFC 4033 | 2023-02 | 16244 | 9175 | 3.75 |
| RFC 4033 | 2023-03 | 16345 | 9262 | 3.75 |
| RFC 4033 | 2023-04 | 16498 | 9468 | 3.75 |
| RFC 4033 | 2023-05 | 16532 | 9433 | 3.75 |
| RFC 4033 | 2023-06 | 16647 | 9457 | 3.75 |
| RFC 4033 | 2023-07 | 16725 | 9512 | 3.75 |
| RFC 4033 | 2023-08 | 16828 | 9801 | 3.75 |
| RFC 4033 | 2023-09 | 16987 | 9912 | 3.75 |
| RFC 4033 | 2023-10 | 17201 | 9525 | 3.75 |
| RFC 4033 | 2023-11 | 17336 | 9642 | 3.75 |
| RFC 4033 | 2023-12 | 17315 | 9674 | 3.75 |
| RFC 4033 | 2024-01 | 17408 | 9831 | 3.75 |
| RFC 4033 | 2024-02 | 17453 | 9819 | 3.75 |
| RFC 4033 | 2024-03 | 17483 | 9887 | 3.75 |
| RFC 4033 | 2024-04 | 17542 | 9532 | 3.75 |
| RFC 4033 | 2024-05 | 17540 | 9547 | 3.75 |
| RFC 4033 | 2024-06 | 17721 | 9999 | 3.75 |
| RFC 4033 | 2024-07 | 17868 | 10311 | 3.75 |
| RFC 4033 | 2024-08 | 17950 | 10480 | 3.75 |
| RFC 4033 | 2024-09 | 17900 | 10589 | 3.75 |
| RFC 4033 | 2024-10 | 18116 | 10826 | 3.75 |
| RFC 4033 | 2024-11 | 18075 | 10930 | 3.75 |
| RFC 4033 | 2024-12 | 18245 | 10819 | 3.75 |
| RFC 4033 | 2025-01 | 11118 | 6142 | 3.75 |
| RFC 4033 | 2025-02 | 11223 | 6149 | 3.75 |
| RFC 4033 | 2025-03 | 11333 | 6477 | 3.75 |
| RFC 4033 | 2025-04 | 11428 | 6773 | 3.75 |
| RFC 4033 | 2025-05 | 11515 | 6763 | 3.75 |
| RFC 4033 | 2025-06 | 11553 | 6813 | 3.75 |
| RFC 4033 | 2025-07 | 11713 | 6835 | 3.75 |
| RFC 4033 | 2025-08 | 11800 | 6767 | 3.75 |
| RFC 4033 | 2025-09 | 11837 | 6653 | 3.75 |
| RFC 4033 | 2025-10 | 12278 | 7127 | 3.75 |
| RFC 4033 | 2025-11 | 12082 | 7118 | 3.75 |
| RFC 4033 | 2025-12 | 12224 | 7085 | 3.75 |
| RFC 4033 | 2026-01 | 12273 | 7304 | 3.75 |
| RFC 4033 | 2026-02 | 12451 | 7296 | 3.75 |
| RFC 4033 | 2026-03 | 12702 | 7370 | 3.75 |
| RFC 4033 | 2026-04 | 12722 | 7397 | 3.75 |
| RFC 4033 | 2026-05 | 12867 | 7445 | 3.75 |
| RFC 4033 | 2026-06 | 13057 | 7357 | 3.75 |
| RFC 4033 | 2026-07 | 13213 | 7410 | 3.75 |
| RFC 4033 | 2026-08 | 13410 | 7387 | 3.75 |
| RFC 4034 | 2009-04 | 350 | 176 | 3 |
| RFC 4034 | 2009-05 | 350 | 176 | 3 |
| RFC 4034 | 2009-08 | 412 | 189 | 3 |
| RFC 4034 | 2009-09 | 412 | 189 | 3 |
| RFC 4034 | 2009-10 | 412 | 189 | 3 |
| RFC 4034 | 2009-11 | 412 | 189 | 3 |
| RFC 4034 | 2009-12 | 448 | 198 | 3 |
| RFC 4034 | 2010-01 | 448 | 198 | 3 |
| RFC 4034 | 2010-02 | 458 | 202 | 3 |
| RFC 4034 | 2010-03 | 516 | 216 | 3 |
| RFC 4034 | 2010-04 | 646 | 278 | 3 |
| RFC 4034 | 2010-05 | 662 | 290 | 3 |
| RFC 4034 | 2010-06 | 730 | 294 | 3 |
| RFC 4034 | 2010-07 | 730 | 294 | 3 |
| RFC 4034 | 2010-08 | 946 | 420 | 3 |
| RFC 4034 | 2010-09 | 948 | 420 | 3 |
| RFC 4034 | 2010-10 | 1016 | 420 | 3 |
| RFC 4034 | 2010-11 | 1030 | 399 | 3 |
| RFC 4034 | 2011-05 | 811 | 437 | 3 |
| RFC 4034 | 2011-06 | 1240 | 501 | 3 |
| RFC 4034 | 2011-07 | 1293 | 504 | 3 |
| RFC 4034 | 2011-08 | 1187 | 515 | 3 |
| RFC 4034 | 2011-09 | 1843 | 546 | 3 |
| RFC 4034 | 2011-10 | 2123 | 547 | 3 |
| RFC 4034 | 2011-11 | 2426 | 596 | 3 |
| RFC 4034 | 2011-12 | 2438 | 599 | 3 |
| RFC 4034 | 2012-01 | 2857 | 702 | 3 |
| RFC 4034 | 2012-02 | 2839 | 813 | 3 |
| RFC 4034 | 2012-03 | 2881 | 829 | 3 |
| RFC 4034 | 2012-04 | 2918 | 836 | 3 |
| RFC 4034 | 2012-05 | 2939 | 836 | 3 |
| RFC 4034 | 2012-06 | 3203 | 873 | 3 |
| RFC 4034 | 2012-08 | 3251 | 887 | 3 |
| RFC 4034 | 2012-09 | 3268 | 903 | 3 |
| RFC 4034 | 2012-10 | 3275 | 915 | 3 |
| RFC 4034 | 2012-11 | 3575 | 929 | 3 |
| RFC 4034 | 2012-12 | 3745 | 929 | 3 |
| RFC 4034 | 2013-01 | 3931 | 991 | 3 |
| RFC 4034 | 2013-02 | 4242 | 1038 | 3 |
| RFC 4034 | 2013-03 | 4024 | 1019 | 3 |
| RFC 4034 | 2013-04 | 4088 | 1019 | 3 |
| RFC 4034 | 2013-05 | 4122 | 1053 | 3 |
| RFC 4034 | 2013-06 | 4246 | 1074 | 3 |
| RFC 4034 | 2013-07 | 4379 | 1129 | 3 |
| RFC 4034 | 2013-08 | 4609 | 1174 | 3 |
| RFC 4034 | 2013-09 | 4681 | 1185 | 3 |
| RFC 4034 | 2013-10 | 4768 | 1256 | 3 |
| RFC 4034 | 2013-11 | 4784 | 1320 | 3 |
| RFC 4034 | 2013-12 | 5642 | 1477 | 3 |
| RFC 4034 | 2014-01 | 5867 | 1481 | 3 |
| RFC 4034 | 2014-02 | 6251 | 1533 | 3 |
| RFC 4034 | 2014-03 | 6313 | 1625 | 3 |
| RFC 4034 | 2014-04 | 6517 | 1668 | 3 |
| RFC 4034 | 2014-05 | 6614 | 1737 | 3 |
| RFC 4034 | 2014-06 | 6600 | 1753 | 3 |
| RFC 4034 | 2014-07 | 6684 | 1791 | 3 |
| RFC 4034 | 2014-08 | 6732 | 1823 | 3 |
| RFC 4034 | 2014-09 | 7785 | 1940 | 3 |
| RFC 4034 | 2014-10 | 6114 | 2106 | 3 |
| RFC 4034 | 2014-11 | 6455 | 2470 | 3 |
| RFC 4034 | 2014-12 | 6970 | 2597 | 3 |
| RFC 4034 | 2015-01 | 6906 | 2597 | 3 |
| RFC 4034 | 2015-02 | 6888 | 2597 | 3 |
| RFC 4034 | 2015-03 | 6890 | 2614 | 3 |
| RFC 4034 | 2015-04 | 7838 | 2703 | 3 |
| RFC 4034 | 2015-05 | 7817 | 2639 | 3 |
| RFC 4034 | 2015-06 | 8276 | 2875 | 3 |
| RFC 4034 | 2015-07 | 8466 | 2717 | 3 |
| RFC 4034 | 2015-08 | 8924 | 2919 | 3 |
| RFC 4034 | 2015-09 | 7848 | 2934 | 3 |
| RFC 4034 | 2015-10 | 3059 | 1072 | 3 |
| RFC 4034 | 2015-11 | 3075 | 1072 | 3 |
| RFC 4034 | 2015-12 | 4461 | 1438 | 3 |
| RFC 4034 | 2016-01 | 4442 | 1438 | 3 |
| RFC 4034 | 2016-02 | 4411 | 1438 | 3 |
| RFC 4034 | 2016-04 | 4490 | 1487 | 3 |
| RFC 4034 | 2016-05 | 4487 | 1441 | 3 |
| RFC 4034 | 2016-06 | 4500 | 1441 | 3 |
| RFC 4034 | 2016-07 | 4544 | 1452 | 3 |
| RFC 4034 | 2016-08 | 4559 | 1443 | 3 |
| RFC 4034 | 2016-09 | 4575 | 1443 | 3 |
| RFC 4034 | 2016-10 | 4700 | 1500 | 3 |
| RFC 4034 | 2016-11 | 4752 | 1552 | 3 |
| RFC 4034 | 2016-12 | 7637 | 2506 | 3 |
| RFC 4034 | 2017-01 | 8571 | 2883 | 3 |
| RFC 4034 | 2017-02 | 8867 | 2839 | 3 |
| RFC 4034 | 2017-03 | 8875 | 2834 | 3 |
| RFC 4034 | 2017-04 | 8781 | 2770 | 3 |
| RFC 4034 | 2017-05 | 8801 | 2821 | 3 |
| RFC 4034 | 2017-06 | 8808 | 2821 | 3 |
| RFC 4034 | 2017-07 | 9004 | 2869 | 3 |
| RFC 4034 | 2017-08 | 8996 | 2903 | 3 |
| RFC 4034 | 2017-09 | 10325 | 3045 | 3 |
| RFC 4034 | 2017-10 | 10195 | 3046 | 3 |
| RFC 4034 | 2017-11 | 10199 | 3046 | 3 |
| RFC 4034 | 2017-12 | 10257 | 3046 | 3 |
| RFC 4034 | 2018-01 | 10262 | 3081 | 3 |
| RFC 4034 | 2018-02 | 10309 | 3144 | 3 |
| RFC 4034 | 2018-03 | 10225 | 2963 | 3 |
| RFC 4034 | 2018-04 | 10239 | 2963 | 3 |
| RFC 4034 | 2018-05 | 10169 | 2994 | 3 |
| RFC 4034 | 2018-06 | 11109 | 3023 | 3 |
| RFC 4034 | 2018-07 | 11255 | 3075 | 3 |
| RFC 4034 | 2018-08 | 11265 | 3075 | 3 |
| RFC 4034 | 2018-09 | 11362 | 3086 | 3 |
| RFC 4034 | 2018-10 | 11357 | 3086 | 3 |
| RFC 4034 | 2018-11 | 11675 | 3181 | 3 |
| RFC 4034 | 2018-12 | 12898 | 3572 | 3 |
| RFC 4034 | 2019-01 | 13479 | 3858 | 3 |
| RFC 4034 | 2019-02 | 14673 | 4144 | 3 |
| RFC 4034 | 2019-03 | 14834 | 4245 | 3 |
| RFC 4034 | 2019-04 | 14879 | 4273 | 3 |
| RFC 4034 | 2019-05 | 9433 | 4267 | 3 |
| RFC 4034 | 2019-06 | 10713 | 4769 | 3 |
| RFC 4034 | 2019-07 | 11488 | 5263 | 3 |
| RFC 4034 | 2019-08 | 11514 | 5273 | 3 |
| RFC 4034 | 2019-09 | 11601 | 5428 | 3 |
| RFC 4034 | 2019-10 | 11710 | 5442 | 3 |
| RFC 4034 | 2019-11 | 11737 | 5444 | 3 |
| RFC 4034 | 2019-12 | 11811 | 5450 | 3 |
| RFC 4034 | 2020-01 | 12646 | 6408 | 3 |
| RFC 4034 | 2020-02 | 12728 | 6554 | 3 |
| RFC 4034 | 2020-03 | 12754 | 6578 | 3 |
| RFC 4034 | 2020-04 | 12763 | 6578 | 3 |
| RFC 4034 | 2020-05 | 12870 | 6619 | 3 |
| RFC 4034 | 2020-06 | 13915 | 6885 | 3 |
| RFC 4034 | 2020-07 | 13377 | 6701 | 3 |
| RFC 4034 | 2020-08 | 12837 | 6547 | 3 |
| RFC 4034 | 2020-09 | 12911 | 6554 | 3 |
| RFC 4034 | 2020-10 | 12962 | 6604 | 3 |
| RFC 4034 | 2020-11 | 13114 | 6700 | 3 |
| RFC 4034 | 2020-12 | 13360 | 6853 | 3 |
| RFC 4034 | 2021-02 | 13762 | 6932 | 3 |
| RFC 4034 | 2021-03 | 13824 | 7039 | 3 |
| RFC 4034 | 2021-04 | 14068 | 7208 | 3 |
| RFC 4034 | 2021-05 | 14135 | 7232 | 3 |
| RFC 4034 | 2021-06 | 14110 | 7251 | 3 |
| RFC 4034 | 2021-07 | 14099 | 7279 | 3 |
| RFC 4034 | 2021-08 | 14215 | 7281 | 3 |
| RFC 4034 | 2021-09 | 14392 | 7504 | 3 |
| RFC 4034 | 2021-10 | 14514 | 7601 | 3 |
| RFC 4034 | 2021-11 | 14635 | 7766 | 3 |
| RFC 4034 | 2021-12 | 14860 | 7795 | 3 |
| RFC 4034 | 2022-01 | 15027 | 7874 | 3 |
| RFC 4034 | 2022-02 | 15210 | 7848 | 3 |
| RFC 4034 | 2022-03 | 15371 | 7927 | 3 |
| RFC 4034 | 2022-04 | 15436 | 7978 | 3 |
| RFC 4034 | 2022-05 | 15682 | 8168 | 3 |
| RFC 4034 | 2022-06 | 15962 | 8348 | 3 |
| RFC 4034 | 2022-07 | 16063 | 8528 | 3 |
| RFC 4034 | 2022-08 | 16153 | 8646 | 3 |
| RFC 4034 | 2022-09 | 16255 | 8761 | 3 |
| RFC 4034 | 2022-10 | 16189 | 8776 | 3 |
| RFC 4034 | 2022-11 | 15933 | 8814 | 3 |
| RFC 4034 | 2022-12 | 15992 | 8912 | 3 |
| RFC 4034 | 2023-01 | 16025 | 9031 | 3 |
| RFC 4034 | 2023-02 | 16244 | 9175 | 3 |
| RFC 4034 | 2023-03 | 16345 | 9262 | 3 |
| RFC 4034 | 2023-04 | 16498 | 9468 | 3 |
| RFC 4034 | 2023-05 | 16532 | 9433 | 3 |
| RFC 4034 | 2023-06 | 16647 | 9457 | 3 |
| RFC 4034 | 2023-07 | 16725 | 9512 | 3 |
| RFC 4034 | 2023-08 | 16828 | 9801 | 3 |
| RFC 4034 | 2023-09 | 16987 | 9912 | 3 |
| RFC 4034 | 2023-10 | 17201 | 9525 | 3 |
| RFC 4034 | 2023-11 | 17336 | 9642 | 3 |
| RFC 4034 | 2023-12 | 17315 | 9674 | 3 |
| RFC 4034 | 2024-01 | 17408 | 9831 | 3 |
| RFC 4034 | 2024-02 | 17453 | 9819 | 3 |
| RFC 4034 | 2024-03 | 17483 | 9887 | 3 |
| RFC 4034 | 2024-04 | 17542 | 9532 | 3 |
| RFC 4034 | 2024-05 | 17540 | 9547 | 3 |
| RFC 4034 | 2024-06 | 17721 | 9999 | 3 |
| RFC 4034 | 2024-07 | 17868 | 10311 | 3 |
| RFC 4034 | 2024-08 | 17950 | 10480 | 3 |
| RFC 4034 | 2024-09 | 17900 | 10589 | 3 |
| RFC 4034 | 2024-10 | 18116 | 10826 | 3 |
| RFC 4034 | 2024-11 | 18075 | 10930 | 3 |
| RFC 4034 | 2024-12 | 18245 | 10819 | 3 |
| RFC 4034 | 2025-01 | 11118 | 6142 | 3 |
| RFC 4034 | 2025-02 | 11223 | 6149 | 3 |
| RFC 4034 | 2025-03 | 11333 | 6477 | 3 |
| RFC 4034 | 2025-04 | 11428 | 6773 | 3 |
| RFC 4034 | 2025-05 | 11515 | 6763 | 3 |
| RFC 4034 | 2025-06 | 11553 | 6813 | 3 |
| RFC 4034 | 2025-07 | 11713 | 6835 | 3 |
| RFC 4034 | 2025-08 | 11800 | 6767 | 3 |
| RFC 4034 | 2025-09 | 11837 | 6653 | 3 |
| RFC 4034 | 2025-10 | 12278 | 7127 | 3 |
| RFC 4034 | 2025-11 | 12082 | 7118 | 3 |
| RFC 4034 | 2025-12 | 12224 | 7085 | 3 |
| RFC 4034 | 2026-01 | 12273 | 7304 | 3 |
| RFC 4034 | 2026-02 | 12451 | 7296 | 3 |
| RFC 4034 | 2026-03 | 12702 | 7370 | 3 |
| RFC 4034 | 2026-04 | 12722 | 7397 | 3 |
| RFC 4034 | 2026-05 | 12867 | 7445 | 3 |
| RFC 4034 | 2026-06 | 13057 | 7357 | 3 |
| RFC 4034 | 2026-07 | 13213 | 7410 | 3 |
| RFC 4034 | 2026-08 | 13410 | 7387 | 3 |
| RFC 4509 | 2009-04 | 20 | 11 | 11.25 |
| RFC 4509 | 2009-05 | 20 | 11 | 11.25 |
| RFC 4509 | 2009-08 | 66 | 33 | 11.25 |
| RFC 4509 | 2009-09 | 66 | 33 | 11.25 |
| RFC 4509 | 2009-10 | 66 | 33 | 11.25 |
| RFC 4509 | 2009-11 | 66 | 33 | 11.25 |
| RFC 4509 | 2009-12 | 66 | 33 | 11.25 |
| RFC 4509 | 2010-01 | 66 | 33 | 11.25 |
| RFC 4509 | 2010-02 | 70 | 34 | 11.25 |
| RFC 4509 | 2010-03 | 98 | 47 | 11.25 |
| RFC 4509 | 2010-04 | 162 | 78 | 11.25 |
| RFC 4509 | 2010-05 | 162 | 78 | 11.25 |
| RFC 4509 | 2010-06 | 194 | 89 | 11.25 |
| RFC 4509 | 2010-07 | 194 | 89 | 11.25 |
| RFC 4509 | 2010-08 | 196 | 90 | 11.25 |
| RFC 4509 | 2010-09 | 196 | 90 | 11.25 |
| RFC 4509 | 2010-10 | 246 | 123 | 11.25 |
| RFC 4509 | 2010-11 | 274 | 134 | 11.25 |
| RFC 4509 | 2011-05 | 279 | 193 | 11.25 |
| RFC 4509 | 2011-06 | 297 | 209 | 11.25 |
| RFC 4509 | 2011-07 | 322 | 217 | 11.25 |
| RFC 4509 | 2011-08 | 393 | 232 | 11.25 |
| RFC 4509 | 2011-09 | 599 | 239 | 11.25 |
| RFC 4509 | 2011-10 | 615 | 240 | 11.25 |
| RFC 4509 | 2011-11 | 775 | 272 | 11.25 |
| RFC 4509 | 2011-12 | 781 | 274 | 11.25 |
| RFC 4509 | 2012-01 | 990 | 380 | 11.25 |
| RFC 4509 | 2012-02 | 1086 | 442 | 11.25 |
| RFC 4509 | 2012-03 | 1107 | 445 | 11.25 |
| RFC 4509 | 2012-04 | 1123 | 451 | 11.25 |
| RFC 4509 | 2012-05 | 1136 | 451 | 11.25 |
| RFC 4509 | 2012-06 | 1299 | 489 | 11.25 |
| RFC 4509 | 2012-08 | 1316 | 511 | 11.25 |
| RFC 4509 | 2012-09 | 1327 | 515 | 11.25 |
| RFC 4509 | 2012-10 | 1331 | 517 | 11.25 |
| RFC 4509 | 2012-11 | 1495 | 569 | 11.25 |
| RFC 4509 | 2012-12 | 1595 | 566 | 11.25 |
| RFC 4509 | 2013-01 | 1676 | 644 | 11.25 |
| RFC 4509 | 2013-02 | 1835 | 699 | 11.25 |
| RFC 4509 | 2013-03 | 1726 | 704 | 11.25 |
| RFC 4509 | 2013-04 | 1755 | 704 | 11.25 |
| RFC 4509 | 2013-05 | 1769 | 713 | 11.25 |
| RFC 4509 | 2013-06 | 1829 | 728 | 11.25 |
| RFC 4509 | 2013-07 | 1895 | 762 | 11.25 |
| RFC 4509 | 2013-08 | 1955 | 785 | 11.25 |
| RFC 4509 | 2013-09 | 1961 | 793 | 11.25 |
| RFC 4509 | 2013-10 | 2006 | 819 | 11.25 |
| RFC 4509 | 2013-11 | 2047 | 844 | 11.25 |
| RFC 4509 | 2013-12 | 2473 | 1081 | 11.25 |
| RFC 4509 | 2014-01 | 2587 | 1092 | 11.25 |
| RFC 4509 | 2014-02 | 2784 | 1117 | 11.25 |
| RFC 4509 | 2014-03 | 2794 | 1210 | 11.25 |
| RFC 4509 | 2014-04 | 2908 | 1281 | 11.25 |
| RFC 4509 | 2014-05 | 2963 | 1271 | 11.25 |
| RFC 4509 | 2014-06 | 2967 | 1313 | 11.25 |
| RFC 4509 | 2014-07 | 2982 | 1322 | 11.25 |
| RFC 4509 | 2014-08 | 3037 | 1351 | 11.25 |
| RFC 4509 | 2014-09 | 3568 | 1441 | 11.25 |
| RFC 4509 | 2014-10 | 2799 | 1638 | 11.25 |
| RFC 4509 | 2014-11 | 3115 | 1979 | 11.25 |
| RFC 4509 | 2014-12 | 3371 | 2080 | 11.25 |
| RFC 4509 | 2015-01 | 3340 | 2080 | 11.25 |
| RFC 4509 | 2015-02 | 3338 | 2080 | 11.25 |
| RFC 4509 | 2015-03 | 3341 | 2092 | 11.25 |
| RFC 4509 | 2015-04 | 3991 | 2200 | 11.25 |
| RFC 4509 | 2015-05 | 4012 | 2204 | 11.25 |
| RFC 4509 | 2015-06 | 4289 | 2445 | 11.25 |
| RFC 4509 | 2015-07 | 4384 | 2288 | 11.25 |
| RFC 4509 | 2015-08 | 4577 | 2463 | 11.25 |
| RFC 4509 | 2015-09 | 4060 | 2477 | 11.25 |
| RFC 4509 | 2015-10 | 1628 | 1025 | 11.25 |
| RFC 4509 | 2015-11 | 1635 | 1025 | 11.25 |
| RFC 4509 | 2015-12 | 2337 | 1383 | 11.25 |
| RFC 4509 | 2016-01 | 2327 | 1383 | 11.25 |
| RFC 4509 | 2016-02 | 2315 | 1387 | 11.25 |
| RFC 4509 | 2016-04 | 2379 | 1433 | 11.25 |
| RFC 4509 | 2016-05 | 2374 | 1397 | 11.25 |
| RFC 4509 | 2016-06 | 2381 | 1397 | 11.25 |
| RFC 4509 | 2016-07 | 2407 | 1408 | 11.25 |
| RFC 4509 | 2016-08 | 2431 | 1408 | 11.25 |
| RFC 4509 | 2016-09 | 2441 | 1409 | 11.25 |
| RFC 4509 | 2016-10 | 2504 | 1457 | 11.25 |
| RFC 4509 | 2016-11 | 2528 | 1509 | 11.25 |
| RFC 4509 | 2016-12 | 3971 | 2463 | 11.25 |
| RFC 4509 | 2017-01 | 4446 | 2843 | 11.25 |
| RFC 4509 | 2017-02 | 4669 | 2796 | 11.25 |
| RFC 4509 | 2017-03 | 4673 | 2786 | 11.25 |
| RFC 4509 | 2017-04 | 4626 | 2722 | 11.25 |
| RFC 4509 | 2017-05 | 4670 | 2765 | 11.25 |
| RFC 4509 | 2017-06 | 4673 | 2765 | 11.25 |
| RFC 4509 | 2017-07 | 4774 | 2813 | 11.25 |
| RFC 4509 | 2017-08 | 4772 | 2842 | 11.25 |
| RFC 4509 | 2017-09 | 5139 | 2984 | 11.25 |
| RFC 4509 | 2017-10 | 5094 | 2985 | 11.25 |
| RFC 4509 | 2017-11 | 5088 | 2985 | 11.25 |
| RFC 4509 | 2017-12 | 5108 | 2985 | 11.25 |
| RFC 4509 | 2018-01 | 5114 | 3015 | 11.25 |
| RFC 4509 | 2018-02 | 5108 | 3085 | 11.25 |
| RFC 4509 | 2018-03 | 5060 | 2912 | 11.25 |
| RFC 4509 | 2018-04 | 5069 | 2912 | 11.25 |
| RFC 4509 | 2018-05 | 5045 | 2922 | 11.25 |
| RFC 4509 | 2018-06 | 5387 | 2950 | 11.25 |
| RFC 4509 | 2018-07 | 5464 | 3017 | 11.25 |
| RFC 4509 | 2018-08 | 5462 | 3017 | 11.25 |
| RFC 4509 | 2018-09 | 5523 | 3038 | 11.25 |
| RFC 4509 | 2018-10 | 5516 | 3038 | 11.25 |
| RFC 4509 | 2018-11 | 5672 | 3105 | 11.25 |
| RFC 4509 | 2018-12 | 6311 | 3485 | 11.25 |
| RFC 4509 | 2019-01 | 6728 | 3778 | 11.25 |
| RFC 4509 | 2019-02 | 7322 | 4066 | 11.25 |
| RFC 4509 | 2019-03 | 7438 | 4158 | 11.25 |
| RFC 4509 | 2019-04 | 7475 | 4211 | 11.25 |
| RFC 4509 | 2019-05 | 4949 | 4206 | 11.25 |
| RFC 4509 | 2019-06 | 5671 | 4733 | 11.25 |
| RFC 4509 | 2019-07 | 6068 | 5227 | 11.25 |
| RFC 4509 | 2019-08 | 6097 | 5237 | 11.25 |
| RFC 4509 | 2019-09 | 6160 | 5386 | 11.25 |
| RFC 4509 | 2019-10 | 6217 | 5400 | 11.25 |
| RFC 4509 | 2019-11 | 6229 | 5402 | 11.25 |
| RFC 4509 | 2019-12 | 6250 | 5408 | 11.25 |
| RFC 4509 | 2020-01 | 6693 | 6363 | 11.25 |
| RFC 4509 | 2020-02 | 6755 | 6366 | 11.25 |
| RFC 4509 | 2020-03 | 6766 | 6387 | 11.25 |
| RFC 4509 | 2020-04 | 6772 | 6387 | 11.25 |
| RFC 4509 | 2020-05 | 6825 | 6427 | 11.25 |
| RFC 4509 | 2020-06 | 7351 | 6686 | 11.25 |
| RFC 4509 | 2020-07 | 7089 | 6508 | 11.25 |
| RFC 4509 | 2020-08 | 6833 | 6357 | 11.25 |
| RFC 4509 | 2020-09 | 6893 | 6360 | 11.25 |
| RFC 4509 | 2020-10 | 6925 | 6405 | 11.25 |
| RFC 4509 | 2020-11 | 7058 | 6499 | 11.25 |
| RFC 4509 | 2020-12 | 7226 | 6646 | 11.25 |
| RFC 4509 | 2021-02 | 7407 | 6723 | 11.25 |
| RFC 4509 | 2021-03 | 7481 | 6827 | 11.25 |
| RFC 4509 | 2021-04 | 7681 | 6979 | 11.25 |
| RFC 4509 | 2021-05 | 7741 | 7003 | 11.25 |
| RFC 4509 | 2021-06 | 7737 | 7024 | 11.25 |
| RFC 4509 | 2021-07 | 7743 | 7053 | 11.25 |
| RFC 4509 | 2021-08 | 7840 | 7055 | 11.25 |
| RFC 4509 | 2021-09 | 7987 | 7273 | 11.25 |
| RFC 4509 | 2021-10 | 8113 | 7368 | 11.25 |
| RFC 4509 | 2021-11 | 8231 | 7536 | 11.25 |
| RFC 4509 | 2021-12 | 8364 | 7563 | 11.25 |
| RFC 4509 | 2022-01 | 8519 | 7609 | 11.25 |
| RFC 4509 | 2022-02 | 8671 | 7584 | 11.25 |
| RFC 4509 | 2022-03 | 8808 | 7658 | 11.25 |
| RFC 4509 | 2022-04 | 8887 | 7739 | 11.25 |
| RFC 4509 | 2022-05 | 9093 | 7959 | 11.25 |
| RFC 4509 | 2022-06 | 9279 | 8100 | 11.25 |
| RFC 4509 | 2022-07 | 9367 | 8279 | 11.25 |
| RFC 4509 | 2022-08 | 9429 | 8392 | 11.25 |
| RFC 4509 | 2022-09 | 9500 | 8503 | 11.25 |
| RFC 4509 | 2022-10 | 9514 | 8518 | 11.25 |
| RFC 4509 | 2022-11 | 9555 | 8546 | 11.25 |
| RFC 4509 | 2022-12 | 9802 | 8638 | 11.25 |
| RFC 4509 | 2023-01 | 9871 | 8792 | 11.25 |
| RFC 4509 | 2023-02 | 10108 | 8934 | 11.25 |
| RFC 4509 | 2023-03 | 10184 | 9018 | 11.25 |
| RFC 4509 | 2023-04 | 10310 | 9213 | 11.25 |
| RFC 4509 | 2023-05 | 10371 | 9179 | 11.25 |
| RFC 4509 | 2023-06 | 10505 | 9207 | 11.25 |
| RFC 4509 | 2023-07 | 10573 | 9293 | 11.25 |
| RFC 4509 | 2023-08 | 10654 | 9578 | 11.25 |
| RFC 4509 | 2023-09 | 10810 | 9688 | 11.25 |
| RFC 4509 | 2023-10 | 10967 | 9307 | 11.25 |
| RFC 4509 | 2023-11 | 11076 | 9420 | 11.25 |
| RFC 4509 | 2023-12 | 11053 | 9452 | 11.25 |
| RFC 4509 | 2024-01 | 11138 | 9607 | 11.25 |
| RFC 4509 | 2024-02 | 11199 | 9578 | 11.25 |
| RFC 4509 | 2024-03 | 11194 | 9646 | 11.25 |
| RFC 4509 | 2024-04 | 11277 | 9295 | 11.25 |
| RFC 4509 | 2024-05 | 11282 | 9292 | 11.25 |
| RFC 4509 | 2024-06 | 11434 | 9683 | 11.25 |
| RFC 4509 | 2024-07 | 11615 | 9871 | 11.25 |
| RFC 4509 | 2024-08 | 11716 | 10044 | 11.25 |
| RFC 4509 | 2024-09 | 11672 | 10154 | 11.25 |
| RFC 4509 | 2024-10 | 11883 | 10423 | 11.25 |
| RFC 4509 | 2024-11 | 12015 | 10535 | 11.25 |
| RFC 4509 | 2024-12 | 12057 | 10418 | 11.25 |
| RFC 4509 | 2025-01 | 8409 | 6045 | 11.25 |
| RFC 4509 | 2025-02 | 8502 | 6052 | 11.25 |
| RFC 4509 | 2025-03 | 8624 | 6373 | 11.25 |
| RFC 4509 | 2025-04 | 8716 | 6658 | 11.25 |
| RFC 4509 | 2025-05 | 8802 | 6647 | 11.25 |
| RFC 4509 | 2025-06 | 8832 | 6666 | 11.25 |
| RFC 4509 | 2025-07 | 8944 | 6686 | 11.25 |
| RFC 4509 | 2025-08 | 9035 | 6623 | 11.25 |
| RFC 4509 | 2025-09 | 9084 | 6511 | 11.25 |
| RFC 4509 | 2025-10 | 9392 | 7019 | 11.25 |
| RFC 4509 | 2025-11 | 9340 | 7011 | 11.25 |
| RFC 4509 | 2025-12 | 9467 | 6992 | 11.25 |
| RFC 4509 | 2026-01 | 9504 | 7206 | 11.25 |
| RFC 4509 | 2026-02 | 9644 | 7178 | 11.25 |
| RFC 4509 | 2026-03 | 9900 | 7249 | 11.25 |
| RFC 4509 | 2026-04 | 9938 | 7275 | 11.25 |
| RFC 4509 | 2026-05 | 10082 | 7332 | 11.25 |
| RFC 4509 | 2026-06 | 10295 | 7319 | 11.25 |
| RFC 4509 | 2026-07 | 10563 | 7370 | 11.25 |
| RFC 4509 | 2026-08 | 10735 | 7348 | 11.25 |
| RFC 5702 | 2010-04 | 4 | 1 | 13.125 |
| RFC 5702 | 2010-05 | 4 | 1 | 13.125 |
| RFC 5702 | 2010-06 | 4 | 1 | 13.125 |
| RFC 5702 | 2010-07 | 8 | 2 | 13.125 |
| RFC 5702 | 2010-08 | 10 | 3 | 13.125 |
| RFC 5702 | 2010-09 | 10 | 3 | 13.125 |
| RFC 5702 | 2010-10 | 10 | 3 | 13.125 |
| RFC 5702 | 2010-11 | 10 | 3 | 13.125 |
| RFC 5702 | 2011-05 | 53 | 34 | 13.125 |
| RFC 5702 | 2011-06 | 64 | 35 | 13.125 |
| RFC 5702 | 2011-07 | 67 | 35 | 13.125 |
| RFC 5702 | 2011-08 | 68 | 36 | 13.125 |
| RFC 5702 | 2011-09 | 144 | 41 | 13.125 |
| RFC 5702 | 2011-10 | 144 | 41 | 13.125 |
| RFC 5702 | 2011-11 | 212 | 67 | 13.125 |
| RFC 5702 | 2011-12 | 212 | 67 | 13.125 |
| RFC 5702 | 2012-01 | 212 | 67 | 13.125 |
| RFC 5702 | 2012-02 | 358 | 104 | 13.125 |
| RFC 5702 | 2012-03 | 384 | 114 | 13.125 |
| RFC 5702 | 2012-04 | 399 | 115 | 13.125 |
| RFC 5702 | 2012-05 | 404 | 117 | 13.125 |
| RFC 5702 | 2012-06 | 649 | 157 | 13.125 |
| RFC 5702 | 2012-08 | 637 | 160 | 13.125 |
| RFC 5702 | 2012-09 | 639 | 158 | 13.125 |
| RFC 5702 | 2012-10 | 640 | 157 | 13.125 |
| RFC 5702 | 2012-11 | 852 | 204 | 13.125 |
| RFC 5702 | 2012-12 | 958 | 236 | 13.125 |
| RFC 5702 | 2013-01 | 1156 | 279 | 13.125 |
| RFC 5702 | 2013-02 | 1448 | 338 | 13.125 |
| RFC 5702 | 2013-03 | 1208 | 296 | 13.125 |
| RFC 5702 | 2013-04 | 1208 | 296 | 13.125 |
| RFC 5702 | 2013-05 | 1218 | 321 | 13.125 |
| RFC 5702 | 2013-06 | 1336 | 330 | 13.125 |
| RFC 5702 | 2013-07 | 1462 | 362 | 13.125 |
| RFC 5702 | 2013-08 | 1787 | 404 | 13.125 |
| RFC 5702 | 2013-09 | 1845 | 434 | 13.125 |
| RFC 5702 | 2013-10 | 1905 | 442 | 13.125 |
| RFC 5702 | 2013-11 | 1909 | 449 | 13.125 |
| RFC 5702 | 2013-12 | 2031 | 475 | 13.125 |
| RFC 5702 | 2014-01 | 2250 | 491 | 13.125 |
| RFC 5702 | 2014-02 | 2355 | 501 | 13.125 |
| RFC 5702 | 2014-03 | 2681 | 577 | 13.125 |
| RFC 5702 | 2014-04 | 2917 | 643 | 13.125 |
| RFC 5702 | 2014-05 | 2990 | 655 | 13.125 |
| RFC 5702 | 2014-06 | 3004 | 670 | 13.125 |
| RFC 5702 | 2014-07 | 3065 | 689 | 13.125 |
| RFC 5702 | 2014-08 | 3106 | 699 | 13.125 |
| RFC 5702 | 2014-09 | 4053 | 740 | 13.125 |
| RFC 5702 | 2014-10 | 2955 | 863 | 13.125 |
| RFC 5702 | 2014-11 | 3265 | 1177 | 13.125 |
| RFC 5702 | 2014-12 | 3598 | 1415 | 13.125 |
| RFC 5702 | 2015-01 | 3602 | 1415 | 13.125 |
| RFC 5702 | 2015-02 | 3576 | 1415 | 13.125 |
| RFC 5702 | 2015-03 | 3558 | 1419 | 13.125 |
| RFC 5702 | 2015-04 | 4325 | 1451 | 13.125 |
| RFC 5702 | 2015-05 | 4379 | 1453 | 13.125 |
| RFC 5702 | 2015-06 | 4434 | 1478 | 13.125 |
| RFC 5702 | 2015-07 | 4438 | 1485 | 13.125 |
| RFC 5702 | 2015-08 | 4801 | 1612 | 13.125 |
| RFC 5702 | 2015-09 | 4111 | 1626 | 13.125 |
| RFC 5702 | 2015-10 | 1872 | 735 | 13.125 |
| RFC 5702 | 2015-11 | 1883 | 735 | 13.125 |
| RFC 5702 | 2015-12 | 3263 | 1115 | 13.125 |
| RFC 5702 | 2016-01 | 3254 | 1174 | 13.125 |
| RFC 5702 | 2016-02 | 3241 | 1176 | 13.125 |
| RFC 5702 | 2016-04 | 3312 | 1219 | 13.125 |
| RFC 5702 | 2016-05 | 3297 | 1176 | 13.125 |
| RFC 5702 | 2016-06 | 3304 | 1177 | 13.125 |
| RFC 5702 | 2016-07 | 3366 | 1186 | 13.125 |
| RFC 5702 | 2016-08 | 3435 | 1208 | 13.125 |
| RFC 5702 | 2016-09 | 3437 | 1208 | 13.125 |
| RFC 5702 | 2016-10 | 3562 | 1243 | 13.125 |
| RFC 5702 | 2016-11 | 3602 | 1289 | 13.125 |
| RFC 5702 | 2016-12 | 6488 | 2156 | 13.125 |
| RFC 5702 | 2017-01 | 7430 | 2532 | 13.125 |
| RFC 5702 | 2017-02 | 7725 | 2510 | 13.125 |
| RFC 5702 | 2017-03 | 7725 | 2501 | 13.125 |
| RFC 5702 | 2017-04 | 7455 | 2462 | 13.125 |
| RFC 5702 | 2017-05 | 7495 | 2509 | 13.125 |
| RFC 5702 | 2017-06 | 7500 | 2509 | 13.125 |
| RFC 5702 | 2017-07 | 7536 | 2515 | 13.125 |
| RFC 5702 | 2017-08 | 7524 | 2528 | 13.125 |
| RFC 5702 | 2017-09 | 7583 | 2528 | 13.125 |
| RFC 5702 | 2017-10 | 7472 | 2529 | 13.125 |
| RFC 5702 | 2017-11 | 7461 | 2529 | 13.125 |
| RFC 5702 | 2017-12 | 7465 | 2529 | 13.125 |
| RFC 5702 | 2018-01 | 7442 | 2541 | 13.125 |
| RFC 5702 | 2018-02 | 7403 | 2573 | 13.125 |
| RFC 5702 | 2018-03 | 7218 | 2440 | 13.125 |
| RFC 5702 | 2018-04 | 7224 | 2440 | 13.125 |
| RFC 5702 | 2018-05 | 7127 | 2455 | 13.125 |
| RFC 5702 | 2018-06 | 7131 | 2455 | 13.125 |
| RFC 5702 | 2018-07 | 7194 | 2471 | 13.125 |
| RFC 5702 | 2018-08 | 7197 | 2471 | 13.125 |
| RFC 5702 | 2018-09 | 7197 | 2471 | 13.125 |
| RFC 5702 | 2018-10 | 7161 | 2465 | 13.125 |
| RFC 5702 | 2018-11 | 7183 | 2501 | 13.125 |
| RFC 5702 | 2018-12 | 8327 | 2694 | 13.125 |
| RFC 5702 | 2019-01 | 8363 | 2694 | 13.125 |
| RFC 5702 | 2019-02 | 9541 | 3111 | 13.125 |
| RFC 5702 | 2019-03 | 9581 | 3129 | 13.125 |
| RFC 5702 | 2019-04 | 9606 | 3143 | 13.125 |
| RFC 5702 | 2019-05 | 5690 | 3140 | 13.125 |
| RFC 5702 | 2019-06 | 6689 | 3513 | 13.125 |
| RFC 5702 | 2019-07 | 7342 | 3871 | 13.125 |
| RFC 5702 | 2019-08 | 7367 | 3871 | 13.125 |
| RFC 5702 | 2019-09 | 7423 | 3961 | 13.125 |
| RFC 5702 | 2019-10 | 7430 | 3961 | 13.125 |
| RFC 5702 | 2019-11 | 7426 | 3961 | 13.125 |
| RFC 5702 | 2019-12 | 7377 | 3909 | 13.125 |
| RFC 5702 | 2020-01 | 8145 | 4482 | 13.125 |
| RFC 5702 | 2020-02 | 8105 | 4482 | 13.125 |
| RFC 5702 | 2020-03 | 8108 | 4482 | 13.125 |
| RFC 5702 | 2020-04 | 8104 | 4482 | 13.125 |
| RFC 5702 | 2020-05 | 8118 | 4520 | 13.125 |
| RFC 5702 | 2020-06 | 8142 | 4533 | 13.125 |
| RFC 5702 | 2020-07 | 8159 | 4550 | 13.125 |
| RFC 5702 | 2020-08 | 8081 | 4506 | 13.125 |
| RFC 5702 | 2020-09 | 8081 | 4498 | 13.125 |
| RFC 5702 | 2020-10 | 8100 | 4508 | 13.125 |
| RFC 5702 | 2020-11 | 8145 | 4511 | 13.125 |
| RFC 5702 | 2020-12 | 8238 | 4530 | 13.125 |
| RFC 5702 | 2021-02 | 8265 | 4557 | 13.125 |
| RFC 5702 | 2021-03 | 8278 | 4562 | 13.125 |
| RFC 5702 | 2021-04 | 8371 | 4733 | 13.125 |
| RFC 5702 | 2021-05 | 8417 | 4740 | 13.125 |
| RFC 5702 | 2021-06 | 8436 | 4759 | 13.125 |
| RFC 5702 | 2021-07 | 8403 | 4756 | 13.125 |
| RFC 5702 | 2021-08 | 8409 | 4589 | 13.125 |
| RFC 5702 | 2021-09 | 8411 | 4591 | 13.125 |
| RFC 5702 | 2021-10 | 8431 | 4538 | 13.125 |
| RFC 5702 | 2021-11 | 8454 | 4578 | 13.125 |
| RFC 5702 | 2021-12 | 8963 | 4723 | 13.125 |
| RFC 5702 | 2022-01 | 9043 | 4769 | 13.125 |
| RFC 5702 | 2022-02 | 9071 | 4795 | 13.125 |
| RFC 5702 | 2022-03 | 9055 | 4818 | 13.125 |
| RFC 5702 | 2022-04 | 9034 | 4822 | 13.125 |
| RFC 5702 | 2022-05 | 9106 | 4855 | 13.125 |
| RFC 5702 | 2022-06 | 9121 | 4873 | 13.125 |
| RFC 5702 | 2022-07 | 9150 | 4857 | 13.125 |
| RFC 5702 | 2022-08 | 9197 | 4913 | 13.125 |
| RFC 5702 | 2022-09 | 9186 | 4883 | 13.125 |
| RFC 5702 | 2022-10 | 9203 | 4889 | 13.125 |
| RFC 5702 | 2022-11 | 8848 | 4874 | 13.125 |
| RFC 5702 | 2022-12 | 8707 | 4860 | 13.125 |
| RFC 5702 | 2023-01 | 8678 | 4858 | 13.125 |
| RFC 5702 | 2023-02 | 8690 | 4864 | 13.125 |
| RFC 5702 | 2023-03 | 8691 | 4866 | 13.125 |
| RFC 5702 | 2023-04 | 8705 | 4910 | 13.125 |
| RFC 5702 | 2023-05 | 8602 | 4848 | 13.125 |
| RFC 5702 | 2023-06 | 8598 | 4843 | 13.125 |
| RFC 5702 | 2023-07 | 8605 | 4833 | 13.125 |
| RFC 5702 | 2023-08 | 8607 | 4860 | 13.125 |
| RFC 5702 | 2023-09 | 8701 | 4968 | 13.125 |
| RFC 5702 | 2023-10 | 8704 | 4905 | 13.125 |
| RFC 5702 | 2023-11 | 8704 | 4948 | 13.125 |
| RFC 5702 | 2023-12 | 8559 | 4911 | 13.125 |
| RFC 5702 | 2024-01 | 8566 | 4963 | 13.125 |
| RFC 5702 | 2024-02 | 8566 | 4949 | 13.125 |
| RFC 5702 | 2024-03 | 8590 | 4963 | 13.125 |
| RFC 5702 | 2024-04 | 8604 | 4963 | 13.125 |
| RFC 5702 | 2024-05 | 8592 | 4972 | 13.125 |
| RFC 5702 | 2024-06 | 8590 | 4954 | 13.125 |
| RFC 5702 | 2024-07 | 8630 | 5019 | 13.125 |
| RFC 5702 | 2024-08 | 8612 | 5013 | 13.125 |
| RFC 5702 | 2024-09 | 8630 | 5049 | 13.125 |
| RFC 5702 | 2024-10 | 8667 | 5210 | 13.125 |
| RFC 5702 | 2024-11 | 8345 | 5213 | 13.125 |
| RFC 5702 | 2024-12 | 8280 | 5159 | 13.125 |
| RFC 5702 | 2025-01 | 2938 | 1947 | 13.125 |
| RFC 5702 | 2025-02 | 2940 | 1966 | 13.125 |
| RFC 5702 | 2025-03 | 2962 | 2008 | 13.125 |
| RFC 5702 | 2025-04 | 2983 | 2030 | 13.125 |
| RFC 5702 | 2025-05 | 2967 | 2012 | 13.125 |
| RFC 5702 | 2025-06 | 2964 | 2035 | 13.125 |
| RFC 5702 | 2025-07 | 2981 | 2031 | 13.125 |
| RFC 5702 | 2025-08 | 2939 | 2011 | 13.125 |
| RFC 5702 | 2025-09 | 2897 | 1960 | 13.125 |
| RFC 5702 | 2025-10 | 3174 | 2016 | 13.125 |
| RFC 5702 | 2025-11 | 2864 | 1971 | 13.125 |
| RFC 5702 | 2025-12 | 2893 | 1989 | 13.125 |
| RFC 5702 | 2026-01 | 2869 | 2070 | 13.125 |
| RFC 5702 | 2026-02 | 2955 | 2034 | 13.125 |
| RFC 5702 | 2026-03 | 2945 | 2041 | 13.125 |
| RFC 5702 | 2026-04 | 2985 | 2057 | 13.125 |
| RFC 5702 | 2026-05 | 2984 | 2054 | 13.125 |
| RFC 5702 | 2026-06 | 3031 | 2001 | 13.125 |
| RFC 5702 | 2026-07 | 3024 | 2056 | 13.125 |
| RFC 5702 | 2026-08 | 3003 | 2054 | 13.125 |
| RFC 5933 | 2013-01 | 18 | 3 | 18 |
| RFC 5933 | 2013-02 | 12 | 2 | 18 |
| RFC 5933 | 2013-03 | 12 | 2 | 18 |
| RFC 5933 | 2013-04 | 12 | 2 | 18 |
| RFC 5933 | 2013-05 | 12 | 2 | 18 |
| RFC 5933 | 2013-06 | 12 | 2 | 18 |
| RFC 5933 | 2013-07 | 12 | 2 | 18 |
| RFC 5933 | 2013-08 | 12 | 2 | 18 |
| RFC 5933 | 2013-09 | 12 | 2 | 18 |
| RFC 5933 | 2013-10 | 12 | 2 | 18 |
| RFC 5933 | 2013-11 | 12 | 2 | 18 |
| RFC 5933 | 2013-12 | 30 | 5 | 18 |
| RFC 5933 | 2014-01 | 30 | 5 | 18 |
| RFC 5933 | 2014-02 | 18 | 3 | 18 |
| RFC 5933 | 2014-03 | 18 | 3 | 18 |
| RFC 5933 | 2014-04 | 18 | 3 | 18 |
| RFC 5933 | 2014-05 | 18 | 3 | 18 |
| RFC 5933 | 2014-06 | 18 | 3 | 18 |
| RFC 5933 | 2014-07 | 18 | 3 | 18 |
| RFC 5933 | 2014-08 | 18 | 3 | 18 |
| RFC 5933 | 2014-09 | 18 | 3 | 18 |
| RFC 5933 | 2014-10 | 18 | 3 | 18 |
| RFC 5933 | 2014-11 | 18 | 3 | 18 |
| RFC 5933 | 2014-12 | 27 | 3 | 18 |
| RFC 5933 | 2015-01 | 27 | 3 | 18 |
| RFC 5933 | 2015-02 | 27 | 3 | 18 |
| RFC 5933 | 2015-03 | 27 | 3 | 18 |
| RFC 5933 | 2015-04 | 36 | 3 | 18 |
| RFC 5933 | 2015-05 | 36 | 3 | 18 |
| RFC 5933 | 2015-06 | 36 | 3 | 18 |
| RFC 5933 | 2015-07 | 36 | 3 | 18 |
| RFC 5933 | 2015-08 | 36 | 3 | 18 |
| RFC 5933 | 2015-09 | 36 | 3 | 18 |
| RFC 6605 | 2015-12 | 2 | 2 | 13.125 |
| RFC 6605 | 2016-01 | 2 | 2 | 13.125 |
| RFC 6605 | 2016-02 | 2 | 2 | 13.125 |
| RFC 6605 | 2016-04 | 6 | 5 | 13.125 |
| RFC 6605 | 2016-05 | 6 | 5 | 13.125 |
| RFC 6605 | 2016-06 | 6 | 5 | 13.125 |
| RFC 6605 | 2016-07 | 6 | 5 | 13.125 |
| RFC 6605 | 2016-08 | 9 | 7 | 13.125 |
| RFC 6605 | 2016-09 | 9 | 7 | 13.125 |
| RFC 6605 | 2016-10 | 9 | 7 | 13.125 |
| RFC 6605 | 2016-11 | 20 | 10 | 13.125 |
| RFC 6605 | 2016-12 | 20 | 10 | 13.125 |
| RFC 6605 | 2017-01 | 20 | 10 | 13.125 |
| RFC 6605 | 2017-02 | 20 | 10 | 13.125 |
| RFC 6605 | 2017-03 | 26 | 13 | 13.125 |
| RFC 6605 | 2017-04 | 26 | 13 | 13.125 |
| RFC 6605 | 2017-05 | 26 | 13 | 13.125 |
| RFC 6605 | 2017-06 | 26 | 13 | 13.125 |
| RFC 6605 | 2017-07 | 26 | 13 | 13.125 |
| RFC 6605 | 2017-08 | 28 | 15 | 13.125 |
| RFC 6605 | 2017-09 | 1236 | 194 | 13.125 |
| RFC 6605 | 2017-10 | 1237 | 194 | 13.125 |
| RFC 6605 | 2017-11 | 1248 | 195 | 13.125 |
| RFC 6605 | 2017-12 | 1297 | 205 | 13.125 |
| RFC 6605 | 2018-01 | 1297 | 205 | 13.125 |
| RFC 6605 | 2018-02 | 1393 | 217 | 13.125 |
| RFC 6605 | 2018-03 | 1484 | 244 | 13.125 |
| RFC 6605 | 2018-04 | 1484 | 244 | 13.125 |
| RFC 6605 | 2018-05 | 1505 | 258 | 13.125 |
| RFC 6605 | 2018-06 | 2267 | 391 | 13.125 |
| RFC 6605 | 2018-07 | 2271 | 393 | 13.125 |
| RFC 6605 | 2018-08 | 2276 | 398 | 13.125 |
| RFC 6605 | 2018-09 | 2295 | 413 | 13.125 |
| RFC 6605 | 2018-10 | 2324 | 417 | 13.125 |
| RFC 6605 | 2018-11 | 2331 | 411 | 13.125 |
| RFC 6605 | 2018-12 | 2411 | 442 | 13.125 |
| RFC 6605 | 2019-01 | 2954 | 758 | 13.125 |
| RFC 6605 | 2019-02 | 2954 | 758 | 13.125 |
| RFC 6605 | 2019-03 | 3058 | 837 | 13.125 |
| RFC 6605 | 2019-04 | 3076 | 842 | 13.125 |
| RFC 6605 | 2019-05 | 1809 | 857 | 13.125 |
| RFC 6605 | 2019-06 | 1946 | 983 | 13.125 |
| RFC 6605 | 2019-07 | 2068 | 1067 | 13.125 |
| RFC 6605 | 2019-08 | 2109 | 1163 | 13.125 |
| RFC 6605 | 2019-09 | 2167 | 1190 | 13.125 |
| RFC 6605 | 2019-10 | 2277 | 1235 | 13.125 |
| RFC 6605 | 2019-11 | 2306 | 1256 | 13.125 |
| RFC 6605 | 2019-12 | 2419 | 1281 | 13.125 |
| RFC 6605 | 2020-01 | 2487 | 1306 | 13.125 |
| RFC 6605 | 2020-02 | 2556 | 1326 | 13.125 |
| RFC 6605 | 2020-03 | 2581 | 1342 | 13.125 |
| RFC 6605 | 2020-04 | 2588 | 1342 | 13.125 |
| RFC 6605 | 2020-05 | 2671 | 1283 | 13.125 |
| RFC 6605 | 2020-06 | 2689 | 1283 | 13.125 |
| RFC 6605 | 2020-07 | 2694 | 1283 | 13.125 |
| RFC 6605 | 2020-08 | 2692 | 1293 | 13.125 |
| RFC 6605 | 2020-09 | 2752 | 1306 | 13.125 |
| RFC 6605 | 2020-10 | 2811 | 1389 | 13.125 |
| RFC 6605 | 2020-11 | 2916 | 1462 | 13.125 |
| RFC 6605 | 2020-12 | 2933 | 1463 | 13.125 |
| RFC 6605 | 2021-02 | 3147 | 1584 | 13.125 |
| RFC 6605 | 2021-03 | 3200 | 1631 | 13.125 |
| RFC 6605 | 2021-04 | 3349 | 1738 | 13.125 |
| RFC 6605 | 2021-05 | 3369 | 1766 | 13.125 |
| RFC 6605 | 2021-06 | 3409 | 1793 | 13.125 |
| RFC 6605 | 2021-07 | 3427 | 1823 | 13.125 |
| RFC 6605 | 2021-08 | 3539 | 1854 | 13.125 |
| RFC 6605 | 2021-09 | 3744 | 1985 | 13.125 |
| RFC 6605 | 2021-10 | 3843 | 2071 | 13.125 |
| RFC 6605 | 2021-11 | 3947 | 2153 | 13.125 |
| RFC 6605 | 2021-12 | 3996 | 2177 | 13.125 |
| RFC 6605 | 2022-01 | 4014 | 2235 | 13.125 |
| RFC 6605 | 2022-02 | 4220 | 2397 | 13.125 |
| RFC 6605 | 2022-03 | 4406 | 2448 | 13.125 |
| RFC 6605 | 2022-04 | 4518 | 2518 | 13.125 |
| RFC 6605 | 2022-05 | 4694 | 2633 | 13.125 |
| RFC 6605 | 2022-06 | 4894 | 2776 | 13.125 |
| RFC 6605 | 2022-07 | 4963 | 2891 | 13.125 |
| RFC 6605 | 2022-08 | 4992 | 2880 | 13.125 |
| RFC 6605 | 2022-09 | 5108 | 2986 | 13.125 |
| RFC 6605 | 2022-10 | 5178 | 3031 | 13.125 |
| RFC 6605 | 2022-11 | 5279 | 2941 | 13.125 |
| RFC 6605 | 2022-12 | 5493 | 3286 | 13.125 |
| RFC 6605 | 2023-01 | 5563 | 3495 | 13.125 |
| RFC 6605 | 2023-02 | 5771 | 3630 | 13.125 |
| RFC 6605 | 2023-03 | 5871 | 3756 | 13.125 |
| RFC 6605 | 2023-04 | 6008 | 3790 | 13.125 |
| RFC 6605 | 2023-05 | 6148 | 3847 | 13.125 |
| RFC 6605 | 2023-06 | 6264 | 3861 | 13.125 |
| RFC 6605 | 2023-07 | 6338 | 3893 | 13.125 |
| RFC 6605 | 2023-08 | 6422 | 3870 | 13.125 |
| RFC 6605 | 2023-09 | 6484 | 3868 | 13.125 |
| RFC 6605 | 2023-10 | 6704 | 3918 | 13.125 |
| RFC 6605 | 2023-11 | 6817 | 4145 | 13.125 |
| RFC 6605 | 2023-12 | 6946 | 4127 | 13.125 |
| RFC 6605 | 2024-01 | 7046 | 4127 | 13.125 |
| RFC 6605 | 2024-02 | 7111 | 4221 | 13.125 |
| RFC 6605 | 2024-03 | 7120 | 4215 | 13.125 |
| RFC 6605 | 2024-04 | 7188 | 4181 | 13.125 |
| RFC 6605 | 2024-05 | 7220 | 4289 | 13.125 |
| RFC 6605 | 2024-06 | 7345 | 4470 | 13.125 |
| RFC 6605 | 2024-07 | 7542 | 4725 | 13.125 |
| RFC 6605 | 2024-08 | 7645 | 4772 | 13.125 |
| RFC 6605 | 2024-09 | 7578 | 4750 | 13.125 |
| RFC 6605 | 2024-10 | 7734 | 4974 | 13.125 |
| RFC 6605 | 2024-11 | 8040 | 4944 | 13.125 |
| RFC 6605 | 2024-12 | 8255 | 5093 | 13.125 |
| RFC 6605 | 2025-01 | 6516 | 3917 | 13.125 |
| RFC 6605 | 2025-02 | 6627 | 3917 | 13.125 |
| RFC 6605 | 2025-03 | 6711 | 4006 | 13.125 |
| RFC 6605 | 2025-04 | 6810 | 4226 | 13.125 |
| RFC 6605 | 2025-05 | 6909 | 4241 | 13.125 |
| RFC 6605 | 2025-06 | 6946 | 4267 | 13.125 |
| RFC 6605 | 2025-07 | 7031 | 4269 | 13.125 |
| RFC 6605 | 2025-08 | 7172 | 4348 | 13.125 |
| RFC 6605 | 2025-09 | 7259 | 4365 | 13.125 |
| RFC 6605 | 2025-10 | 7423 | 4537 | 13.125 |
| RFC 6605 | 2025-11 | 7537 | 4387 | 13.125 |
| RFC 6605 | 2025-12 | 7651 | 4429 | 13.125 |
| RFC 6605 | 2026-01 | 7722 | 4457 | 13.125 |
| RFC 6605 | 2026-02 | 7812 | 4448 | 13.125 |
| RFC 6605 | 2026-03 | 8064 | 4483 | 13.125 |
| RFC 6605 | 2026-04 | 8076 | 4498 | 13.125 |
| RFC 6605 | 2026-05 | 8230 | 4610 | 13.125 |
| RFC 6605 | 2026-06 | 8403 | 4610 | 13.125 |
| RFC 6605 | 2026-07 | 8686 | 4679 | 13.125 |
| RFC 6605 | 2026-08 | 8919 | 4676 | 13.125 |
| RFC 8624 | 2019-06 | 1919 | 983 | 3.375 |
| RFC 8624 | 2019-07 | 2025 | 1048 | 3.375 |
| RFC 8624 | 2019-08 | 2066 | 1144 | 3.375 |
| RFC 8624 | 2019-09 | 2120 | 1152 | 3.375 |
| RFC 8624 | 2019-10 | 2226 | 1209 | 3.375 |
| RFC 8624 | 2019-11 | 2257 | 1229 | 3.375 |
| RFC 8624 | 2019-12 | 2370 | 1252 | 3.375 |
| RFC 8624 | 2020-01 | 2438 | 1277 | 3.375 |
| RFC 8624 | 2020-02 | 2488 | 1267 | 3.375 |
| RFC 8624 | 2020-03 | 2513 | 1282 | 3.375 |
| RFC 8624 | 2020-04 | 2522 | 1282 | 3.375 |
| RFC 8624 | 2020-05 | 2589 | 1227 | 3.375 |
| RFC 8624 | 2020-06 | 2605 | 1243 | 3.375 |
| RFC 8624 | 2020-07 | 2610 | 1243 | 3.375 |
| RFC 8624 | 2020-08 | 2606 | 1252 | 3.375 |
| RFC 8624 | 2020-09 | 2664 | 1265 | 3.375 |
| RFC 8624 | 2020-10 | 2723 | 1342 | 3.375 |
| RFC 8624 | 2020-11 | 2828 | 1426 | 3.375 |
| RFC 8624 | 2020-12 | 2839 | 1425 | 3.375 |
| RFC 8624 | 2021-02 | 3053 | 1545 | 3.375 |
| RFC 8624 | 2021-03 | 3106 | 1591 | 3.375 |
| RFC 8624 | 2021-04 | 3265 | 1696 | 3.375 |
| RFC 8624 | 2021-05 | 3282 | 1724 | 3.375 |
| RFC 8624 | 2021-06 | 3311 | 1751 | 3.375 |
| RFC 8624 | 2021-07 | 3329 | 1780 | 3.375 |
| RFC 8624 | 2021-08 | 3431 | 1809 | 3.375 |
| RFC 8624 | 2021-09 | 3638 | 1949 | 3.375 |
| RFC 8624 | 2021-10 | 3719 | 2013 | 3.375 |
| RFC 8624 | 2021-11 | 3826 | 2094 | 3.375 |
| RFC 8624 | 2021-12 | 3883 | 2117 | 3.375 |
| RFC 8624 | 2022-01 | 3901 | 2169 | 3.375 |
| RFC 8624 | 2022-02 | 4085 | 2323 | 3.375 |
| RFC 8624 | 2022-03 | 4269 | 2372 | 3.375 |
| RFC 8624 | 2022-04 | 4391 | 2442 | 3.375 |
| RFC 8624 | 2022-05 | 4567 | 2572 | 3.375 |
| RFC 8624 | 2022-06 | 4775 | 2715 | 3.375 |
| RFC 8624 | 2022-07 | 4844 | 2830 | 3.375 |
| RFC 8624 | 2022-08 | 4873 | 2819 | 3.375 |
| RFC 8624 | 2022-09 | 4990 | 2926 | 3.375 |
| RFC 8624 | 2022-10 | 5060 | 2971 | 3.375 |
| RFC 8624 | 2022-11 | 5049 | 2836 | 3.375 |
| RFC 8624 | 2022-12 | 5199 | 3059 | 3.375 |
| RFC 8624 | 2023-01 | 5271 | 3237 | 3.375 |
| RFC 8624 | 2023-02 | 5475 | 3397 | 3.375 |
| RFC 8624 | 2023-03 | 5579 | 3503 | 3.375 |
| RFC 8624 | 2023-04 | 5715 | 3651 | 3.375 |
| RFC 8624 | 2023-05 | 5872 | 3732 | 3.375 |
| RFC 8624 | 2023-06 | 5980 | 3754 | 3.375 |
| RFC 8624 | 2023-07 | 6040 | 3785 | 3.375 |
| RFC 8624 | 2023-08 | 6124 | 3761 | 3.375 |
| RFC 8624 | 2023-09 | 6184 | 3760 | 3.375 |
| RFC 8624 | 2023-10 | 6404 | 3808 | 3.375 |
| RFC 8624 | 2023-11 | 6517 | 4003 | 3.375 |
| RFC 8624 | 2023-12 | 6646 | 3985 | 3.375 |
| RFC 8624 | 2024-01 | 6745 | 3985 | 3.375 |
| RFC 8624 | 2024-02 | 6810 | 4076 | 3.375 |
| RFC 8624 | 2024-03 | 6795 | 4072 | 3.375 |
| RFC 8624 | 2024-04 | 6868 | 4040 | 3.375 |
| RFC 8624 | 2024-05 | 6895 | 4139 | 3.375 |
| RFC 8624 | 2024-06 | 7020 | 4316 | 3.375 |
| RFC 8624 | 2024-07 | 7217 | 4560 | 3.375 |
| RFC 8624 | 2024-08 | 7320 | 4604 | 3.375 |
| RFC 8624 | 2024-09 | 7249 | 4579 | 3.375 |
| RFC 8624 | 2024-10 | 7400 | 4794 | 3.375 |
| RFC 8624 | 2024-11 | 7712 | 4762 | 3.375 |
| RFC 8624 | 2024-12 | 7931 | 4894 | 3.375 |
| RFC 8624 | 2025-01 | 6238 | 3834 | 3.375 |
| RFC 8624 | 2025-02 | 6351 | 3834 | 3.375 |
| RFC 8624 | 2025-03 | 6439 | 3956 | 3.375 |
| RFC 8624 | 2025-04 | 6538 | 4170 | 3.375 |
| RFC 8624 | 2025-05 | 6645 | 4184 | 3.375 |
| RFC 8624 | 2025-06 | 6680 | 4210 | 3.375 |
| RFC 8624 | 2025-07 | 6769 | 4212 | 3.375 |
| RFC 8624 | 2025-08 | 6914 | 4306 | 3.375 |
| RFC 8624 | 2025-09 | 7002 | 4322 | 3.375 |
| RFC 8624 | 2025-10 | 7162 | 4489 | 3.375 |
| RFC 8624 | 2025-11 | 7276 | 4327 | 3.375 |
| RFC 8624 | 2025-12 | 7392 | 4368 | 3.375 |
| RFC 8624 | 2026-01 | 7465 | 4395 | 3.375 |
| RFC 8624 | 2026-02 | 7561 | 4386 | 3.375 |
| RFC 8624 | 2026-03 | 7810 | 4467 | 3.375 |
| RFC 8624 | 2026-04 | 7822 | 4482 | 3.375 |
| RFC 8624 | 2026-05 | 7975 | 4590 | 3.375 |
| RFC 8624 | 2026-06 | 8088 | 4590 | 3.375 |
| RFC 8624 | 2026-07 | 8379 | 4659 | 3.375 |
| RFC 8624 | 2026-08 | 8608 | 4656 | 3.375 |
| RFC 8080 | 2022-09 | 2 | 2 | 17.25 |
| RFC 8080 | 2022-10 | 2 | 2 | 17.25 |
| RFC 8080 | 2022-11 | 2 | 2 | 17.25 |
| RFC 8080 | 2022-12 | 3 | 3 | 17.25 |
| RFC 8080 | 2023-01 | 5 | 4 | 17.25 |
| RFC 8080 | 2023-02 | 5 | 4 | 17.25 |
| RFC 8080 | 2023-03 | 5 | 4 | 17.25 |
| RFC 8080 | 2023-04 | 5 | 4 | 17.25 |
| RFC 8080 | 2023-05 | 5 | 4 | 17.25 |
| RFC 8080 | 2023-06 | 5 | 4 | 17.25 |
| RFC 8080 | 2023-07 | 5 | 4 | 17.25 |
| RFC 8080 | 2023-08 | 5 | 4 | 17.25 |
| RFC 8080 | 2023-09 | 5 | 4 | 17.25 |
| RFC 8080 | 2023-10 | 5 | 4 | 17.25 |
| RFC 8080 | 2023-11 | 5 | 4 | 17.25 |
| RFC 8080 | 2023-12 | 5 | 4 | 17.25 |
| RFC 8080 | 2024-01 | 5 | 4 | 17.25 |
| RFC 8080 | 2024-02 | 5 | 4 | 17.25 |
| RFC 8080 | 2024-03 | 5 | 4 | 17.25 |
| RFC 8080 | 2024-04 | 10 | 8 | 17.25 |
| RFC 8080 | 2024-05 | 10 | 8 | 17.25 |
| RFC 8080 | 2024-06 | 10 | 8 | 17.25 |
| RFC 8080 | 2024-07 | 10 | 8 | 17.25 |
| RFC 8080 | 2024-08 | 10 | 8 | 17.25 |
| RFC 8080 | 2024-09 | 10 | 8 | 17.25 |
| RFC 8080 | 2024-10 | 13 | 11 | 17.25 |
| RFC 8080 | 2024-11 | 14 | 12 | 17.25 |
| RFC 8080 | 2024-12 | 16 | 15 | 17.25 |
| RFC 8080 | 2025-01 | 16 | 13 | 17.25 |
| RFC 8080 | 2025-02 | 20 | 16 | 17.25 |
| RFC 8080 | 2025-03 | 24 | 19 | 17.25 |
| RFC 8080 | 2025-04 | 24 | 19 | 17.25 |
| RFC 8080 | 2025-05 | 24 | 19 | 17.25 |
| RFC 8080 | 2025-06 | 28 | 22 | 17.25 |
| RFC 8080 | 2025-07 | 28 | 22 | 17.25 |
| RFC 8080 | 2025-08 | 30 | 25 | 17.25 |
| RFC 8080 | 2025-09 | 30 | 25 | 17.25 |
| RFC 8080 | 2025-10 | 30 | 25 | 17.25 |
| RFC 8080 | 2025-11 | 30 | 25 | 17.25 |
| RFC 8080 | 2025-12 | 32 | 27 | 17.25 |
| RFC 8080 | 2026-01 | 34 | 27 | 17.25 |
| RFC 8080 | 2026-02 | 40 | 33 | 17.25 |
| RFC 8080 | 2026-03 | 41 | 34 | 17.25 |
| RFC 8080 | 2026-04 | 41 | 34 | 17.25 |
| RFC 8080 | 2026-05 | 41 | 34 | 17.25 |
| RFC 8080 | 2026-06 | 41 | 34 | 17.25 |
| RFC 8080 | 2026-07 | 41 | 34 | 17.25 |
| RFC 8080 | 2026-08 | 41 | 34 | 17.25 |

## 10. Impossible Timestamp Matches

An observation that predates the RFC it appears to match cannot be evidence of that RFC. The indicator conditions may have passed, but the match is rejected outright, its score is forfeited to zero, and it is sent to the review queue rather than quietly dropped.

| Signal | RFC | Observed | RFC published | Forfeited score | Matched indicators |
| --- | --- | --- | --- | --- | --- |
| sig_0001 | RFC 8624 | 2009-09-01 | 2019-06-01 | 0 | rfc8624_avoids_deprecated_algorithm |
| sig_0001 | RFC 9905 | 2009-09-01 | 2025-11-01 | 0 | rfc9905_deprecated_sha1_in_delegation |
| sig_0002 | RFC 8624 | 2011-11-01 | 2019-06-01 | 0 | rfc8624_avoids_deprecated_algorithm |
| sig_0002 | RFC 9905 | 2011-11-01 | 2025-11-01 | 0 | rfc9905_deprecated_sha1_in_delegation |
| sig_0003 | RFC 8624 | 2013-02-01 | 2019-06-01 | 0 | rfc8624_avoids_deprecated_algorithm |
| sig_0003 | RFC 9905 | 2013-02-01 | 2025-11-01 | 0 | rfc9905_deprecated_sha1_in_delegation |
| sig_0004 | RFC 8624 | 2013-02-01 | 2019-06-01 | 0 | rfc8624_avoids_deprecated_algorithm |
| sig_0004 | RFC 9906 | 2013-02-01 | 2025-11-01 | 15 | rfc9906_deprecated_ecc_gost_still_published |
| sig_0005 | RFC 8624 | 2015-04-01 | 2019-06-01 | 0 | rfc8624_avoids_deprecated_algorithm |
| sig_0005 | RFC 9906 | 2015-04-01 | 2025-11-01 | 15 | rfc9906_deprecated_ecc_gost_still_published |
| sig_0006 | RFC 8624 | 2015-06-01 | 2019-06-01 | 0 | rfc8624_avoids_deprecated_algorithm |
| sig_0006 | RFC 9906 | 2015-06-01 | 2025-11-01 | 18 | rfc9906_deprecated_ecc_gost_still_published, rfc9906_deprecated_gost_di... |
| sig_0007 | RFC 8624 | 2017-03-01 | 2019-06-01 | 0 | rfc8624_avoids_deprecated_algorithm |
| sig_0008 | RFC 8624 | 2018-07-01 | 2019-06-01 | 3.375 | rfc8624_avoids_deprecated_algorithm, rfc8624_recommended_signing_algori... |
| sig_0009 | RFC 8624 | 2018-11-01 | 2019-06-01 | 0 | rfc8624_avoids_deprecated_algorithm |
| sig_0009 | RFC 9905 | 2018-11-01 | 2025-11-01 | 0 | rfc9905_deprecated_sha1_in_delegation |
| sig_0011 | RFC 9906 | 2019-12-01 | 2025-11-01 | 0 | rfc9906_deprecated_gost_digest_still_published |
| sig_0016 | RFC 9906 | 2022-05-01 | 2025-11-01 | 0 | rfc9906_deprecated_gost_digest_still_published |
| sig_0018 | RFC 9906 | 2022-11-01 | 2025-11-01 | 0 | rfc9906_deprecated_gost_digest_still_published |
| sig_0020 | RFC 9906 | 2023-06-01 | 2025-11-01 | 0 | rfc9906_deprecated_gost_digest_still_published |
| sig_0022 | RFC 9906 | 2024-03-01 | 2025-11-01 | 0 | rfc9906_deprecated_gost_digest_still_published |

The forfeited score is what the match would have scored had the observation been dated after publication. It is recorded so that a reviewer can see how strong the rejected evidence was: a large forfeited score usually means the mechanism predates its own standardization, which is common - the RFC often documents existing practice - or that the checklist attributes the indicator to the wrong document.

## 11. Partial / Ambiguous Matches

A partial match means some but not all required indicators were satisfied. An ambiguous match means the evidence fits, but the same observation is equally explained by another RFC. Neither is reported as adoption.

| Signal | RFC | Decision | Score | Missing fields | Why |
| --- | --- | --- | --- | --- | --- |
| sig_0001 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0001: every required... |
| sig_0001 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0001: every required... |
| sig_0001 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0001: every required... |
| sig_0001 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0001: every required... |
| sig_0001 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0001: every required... |
| sig_0001 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0001: every required... |
| sig_0001 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0001: every required... |
| sig_0002 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0002: every required... |
| sig_0002 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0002: every required... |
| sig_0002 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0002: every required... |
| sig_0002 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0002: every required... |
| sig_0002 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0002: every required... |
| sig_0002 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0002: every required... |
| sig_0002 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0002: every required... |
| sig_0003 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0003: every required... |
| sig_0003 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0003: every required... |
| sig_0003 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0003: every required... |
| sig_0003 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0003: every required... |
| sig_0003 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0003: every required... |
| sig_0003 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0003: every required... |
| sig_0003 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0003: every required... |
| sig_0004 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0004: every required... |
| sig_0004 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0004: every required... |
| sig_0004 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0004: every required... |
| sig_0004 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0004: every required... |
| sig_0004 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0004: every required... |
| sig_0004 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0004: every required... |
| sig_0004 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0004: every required... |
| sig_0005 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0005: every required... |
| sig_0005 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0005: every required... |
| sig_0005 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0005: every required... |
| sig_0005 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0005: every required... |
| sig_0005 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0005: every required... |
| sig_0005 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0005: every required... |
| sig_0005 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0005: every required... |
| sig_0006 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0006: every required... |
| sig_0006 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0006: every required... |
| sig_0006 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0006: every required... |
| sig_0006 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0006: every required... |
| sig_0006 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0006: every required... |
| sig_0006 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0006: every required... |
| sig_0006 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0006: every required... |
| sig_0007 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0007: every required... |
| sig_0007 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0007: every required... |
| sig_0007 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0007: every required... |
| sig_0007 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0007: every required... |
| sig_0007 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0007: every required... |
| sig_0007 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0007: every required... |
| sig_0007 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0007: every required... |
| sig_0008 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0008: every required... |
| sig_0008 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0008: every required... |
| sig_0008 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0008: every required... |
| sig_0008 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0008: every required... |
| sig_0008 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0008: every required... |
| sig_0008 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0008: every required... |
| sig_0008 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0008: every required... |
| sig_0009 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0009: every required... |
| sig_0009 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0009: every required... |
| sig_0009 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0009: every required... |
| sig_0009 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0009: every required... |
| sig_0009 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0009: every required... |
| sig_0009 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0009: every required... |
| sig_0009 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0009: every required... |
| sig_0010 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0010: every required... |
| sig_0010 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0010: every required... |
| sig_0010 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0010: every required... |
| sig_0010 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0010: every required... |
| sig_0010 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0010: the optional indicator rfc8... |
| sig_0010 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0010: every required... |
| sig_0010 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0010: every required... |
| sig_0010 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0010: every required... |
| sig_0011 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0011: the required indica... |
| sig_0011 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0011: every required... |
| sig_0011 | RFC 5933 | partial_match | 0 | - | RFC 5933 partially matches signal sig_0011: the optional indicator rfc5... |
| sig_0011 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0011: every required... |
| sig_0011 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0011: every required... |
| sig_0011 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0011: every required... |
| sig_0011 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0011: every required... |
| sig_0011 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0011: every required... |
| sig_0011 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0011: every required... |
| sig_0012 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0012: the required indica... |
| sig_0012 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0012: every required... |
| sig_0012 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0012: every required... |
| sig_0012 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0012: every required... |
| sig_0012 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0012: every required... |
| sig_0012 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0012: every required... |
| sig_0012 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0012: every required... |
| sig_0012 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0012: every required... |
| sig_0013 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0013: every required... |
| sig_0013 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0013: every required... |
| sig_0013 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0013: every required... |
| sig_0013 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0013: every required... |
| sig_0013 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0013: the optional indicator rfc8... |
| sig_0013 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0013: every required... |
| sig_0013 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0013: every required... |
| sig_0013 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0013: every required... |
| sig_0014 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0014: the required indica... |
| sig_0014 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0014: every required... |
| sig_0014 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0014: every required... |
| sig_0014 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0014: every required... |
| sig_0014 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0014: every required... |
| sig_0014 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0014: every required... |
| sig_0014 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0014: every required... |
| sig_0014 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0014: every required... |
| sig_0015 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0015: the required indica... |
| sig_0015 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0015: every required... |
| sig_0015 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0015: every required... |
| sig_0015 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0015: every required... |
| sig_0015 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0015: every required... |
| sig_0015 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0015: every required... |
| sig_0015 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0015: every required... |
| sig_0015 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0015: every required... |
| sig_0016 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0016: the required indica... |
| sig_0016 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0016: every required... |
| sig_0016 | RFC 5933 | partial_match | 0 | - | RFC 5933 partially matches signal sig_0016: the optional indicator rfc5... |
| sig_0016 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0016: every required... |
| sig_0016 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0016: every required... |
| sig_0016 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0016: every required... |
| sig_0016 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0016: every required... |
| sig_0016 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0016: every required... |
| sig_0016 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0016: every required... |
| sig_0017 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0017: every required... |
| sig_0017 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0017: every required... |
| sig_0017 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0017: every required... |
| sig_0017 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0017: every required... |
| sig_0017 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0017: the optional indicator rfc8... |
| sig_0017 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0017: every required... |
| sig_0017 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0017: every required... |
| sig_0017 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0017: every required... |
| sig_0018 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0018: the required indica... |
| sig_0018 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0018: every required... |
| sig_0018 | RFC 5933 | partial_match | 0 | - | RFC 5933 partially matches signal sig_0018: the optional indicator rfc5... |
| sig_0018 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0018: every required... |
| sig_0018 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0018: every required... |
| sig_0018 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0018: every required... |
| sig_0018 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0018: every required... |
| sig_0018 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0018: every required... |
| sig_0018 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0018: every required... |
| sig_0019 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0019: the required indica... |
| sig_0019 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0019: every required... |
| sig_0019 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0019: every required... |
| sig_0019 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0019: every required... |
| sig_0019 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0019: every required... |
| sig_0019 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0019: every required... |
| sig_0019 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0019: every required... |
| sig_0019 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0019: every required... |
| sig_0020 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0020: the required indica... |
| sig_0020 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0020: every required... |
| sig_0020 | RFC 5933 | partial_match | 0 | - | RFC 5933 partially matches signal sig_0020: the optional indicator rfc5... |
| sig_0020 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0020: every required... |
| sig_0020 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0020: every required... |
| sig_0020 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0020: every required... |
| sig_0020 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0020: every required... |
| sig_0020 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0020: every required... |
| sig_0020 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0020: every required... |
| sig_0021 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0021: the required indica... |
| sig_0021 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0021: every required... |
| sig_0021 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0021: every required... |
| sig_0021 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0021: every required... |
| sig_0021 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0021: every required... |
| sig_0021 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0021: every required... |
| sig_0021 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0021: every required... |
| sig_0021 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0021: every required... |
| sig_0022 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0022: the required indica... |
| sig_0022 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0022: every required... |
| sig_0022 | RFC 5933 | partial_match | 0 | - | RFC 5933 partially matches signal sig_0022: the optional indicator rfc5... |
| sig_0022 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0022: every required... |
| sig_0022 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0022: every required... |
| sig_0022 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0022: every required... |
| sig_0022 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0022: every required... |
| sig_0022 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0022: every required... |
| sig_0022 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0022: every required... |
| sig_0023 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0023: every required... |
| sig_0023 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0023: every required... |
| sig_0023 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0023: every required... |
| sig_0023 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0023: every required... |
| sig_0023 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0023: the optional indicator rfc8... |
| sig_0023 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0023: every required... |
| sig_0023 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0023: every required... |
| sig_0023 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0023: every required... |
| sig_0024 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0024: the required indica... |
| sig_0024 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0024: every required... |
| sig_0024 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0024: every required... |
| sig_0024 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0024: every required... |
| sig_0024 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0024: every required... |
| sig_0024 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0024: every required... |
| sig_0024 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0024: every required... |
| sig_0024 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0024: every required... |
| sig_0025 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0025: every required... |
| sig_0025 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0025: every required... |
| sig_0025 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0025: every required... |
| sig_0025 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0025: every required... |
| sig_0025 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0025: the optional indicator rfc8... |
| sig_0025 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0025: every required... |
| sig_0025 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0025: every required... |
| sig_0025 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0025: every required... |
| sig_0025 | RFC 9905 | partial_match | 0 | - | RFC 9905 partially matches signal sig_0025: the optional indicator rfc9... |
| sig_0026 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0026: every required... |
| sig_0026 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0026: every required... |
| sig_0026 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0026: every required... |
| sig_0026 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0026: every required... |
| sig_0026 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0026: the optional indicator rfc8... |
| sig_0026 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0026: every required... |
| sig_0026 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0026: every required... |
| sig_0026 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0026: every required... |
| sig_0027 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0027: the required indica... |
| sig_0027 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0027: every required... |
| sig_0027 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0027: every required... |
| sig_0027 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0027: every required... |
| sig_0027 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0027: every required... |
| sig_0027 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0027: every required... |
| sig_0027 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0027: every required... |
| sig_0027 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0027: every required... |
| sig_0028 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0028: the required indica... |
| sig_0028 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0028: every required... |
| sig_0028 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0028: every required... |
| sig_0028 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0028: every required... |
| sig_0028 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0028: every required... |
| sig_0028 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0028: every required... |
| sig_0028 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0028: every required... |
| sig_0028 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0028: every required... |
| sig_0029 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0029: every required... |
| sig_0029 | RFC 5933 | partial_match | 0 | - | RFC 5933 partially matches signal sig_0029: the optional indicator rfc5... |
| sig_0029 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0029: every required... |
| sig_0029 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0029: every required... |
| sig_0029 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0029: every required... |
| sig_0029 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0029: the optional indicator rfc8... |
| sig_0029 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0029: every required... |
| sig_0029 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0029: every required... |
| sig_0029 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0029: every required... |
| sig_0029 | RFC 9906 | partial_match | 0 | - | RFC 9906 partially matches signal sig_0029: the optional indicator rfc9... |
| sig_0030 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0030: every required... |
| sig_0030 | RFC 5933 | partial_match | 0 | - | RFC 5933 partially matches signal sig_0030: the optional indicator rfc5... |
| sig_0030 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0030: every required... |
| sig_0030 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0030: every required... |
| sig_0030 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0030: every required... |
| sig_0030 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0030: the optional indicator rfc8... |
| sig_0030 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0030: every required... |
| sig_0030 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0030: every required... |
| sig_0030 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0030: every required... |
| sig_0030 | RFC 9905 | partial_match | 0 | - | RFC 9905 partially matches signal sig_0030: the optional indicator rfc9... |
| sig_0030 | RFC 9906 | partial_match | 0 | - | RFC 9906 partially matches signal sig_0030: the optional indicator rfc9... |
| sig_0031 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0031: every required... |
| sig_0031 | RFC 5933 | partial_match | 0 | - | RFC 5933 partially matches signal sig_0031: the optional indicator rfc5... |
| sig_0031 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0031: every required... |
| sig_0031 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0031: every required... |
| sig_0031 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0031: every required... |
| sig_0031 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0031: the optional indicator rfc8... |
| sig_0031 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0031: every required... |
| sig_0031 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0031: every required... |
| sig_0031 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0031: every required... |
| sig_0031 | RFC 9906 | partial_match | 0 | - | RFC 9906 partially matches signal sig_0031: the optional indicator rfc9... |
| sig_0032 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0032: the required indica... |
| sig_0032 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0032: every required... |
| sig_0032 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0032: every required... |
| sig_0032 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0032: every required... |
| sig_0032 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0032: every required... |
| sig_0032 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0032: every required... |
| sig_0032 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0032: every required... |
| sig_0032 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0032: every required... |
| sig_0033 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0033: every required... |
| sig_0033 | RFC 5933 | partial_match | 0 | - | RFC 5933 partially matches signal sig_0033: the optional indicator rfc5... |
| sig_0033 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0033: every required... |
| sig_0033 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0033: every required... |
| sig_0033 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0033: every required... |
| sig_0033 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0033: the optional indicator rfc8... |
| sig_0033 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0033: every required... |
| sig_0033 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0033: every required... |
| sig_0033 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0033: every required... |
| sig_0033 | RFC 9906 | partial_match | 0 | - | RFC 9906 partially matches signal sig_0033: the optional indicator rfc9... |
| sig_0034 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0034: every required... |
| sig_0034 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0034: every required... |
| sig_0034 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0034: every required... |
| sig_0034 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0034: every required... |
| sig_0034 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0034: the optional indicator rfc8... |
| sig_0034 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0034: every required... |
| sig_0034 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0034: every required... |
| sig_0034 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0034: every required... |
| sig_0034 | RFC 9905 | partial_match | 0 | - | RFC 9905 partially matches signal sig_0034: the optional indicator rfc9... |
| sig_0035 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0035: every required... |
| sig_0035 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0035: every required... |
| sig_0035 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0035: every required... |
| sig_0035 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0035: every required... |
| sig_0035 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0035: the optional indicator rfc8... |
| sig_0035 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0035: every required... |
| sig_0035 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0035: every required... |
| sig_0035 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0035: every required... |
| sig_0035 | RFC 9905 | partial_match | 0 | - | RFC 9905 partially matches signal sig_0035: the optional indicator rfc9... |
| sig_0036 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0036: every required... |
| sig_0036 | RFC 5933 | partial_match | 0 | - | RFC 5933 partially matches signal sig_0036: the optional indicator rfc5... |
| sig_0036 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0036: every required... |
| sig_0036 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0036: every required... |
| sig_0036 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0036: every required... |
| sig_0036 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0036: the optional indicator rfc8... |
| sig_0036 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0036: every required... |
| sig_0036 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0036: every required... |
| sig_0036 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0036: every required... |
| sig_0036 | RFC 9906 | partial_match | 0 | - | RFC 9906 partially matches signal sig_0036: the optional indicator rfc9... |
| sig_0037 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0037: every required... |
| sig_0037 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0037: every required... |
| sig_0037 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0037: every required... |
| sig_0037 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0037: every required... |
| sig_0037 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0037: the optional indicator rfc8... |
| sig_0037 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0037: every required... |
| sig_0037 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0037: every required... |
| sig_0037 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0037: every required... |
| sig_0038 | RFC 4035 | non_queryable | 0 | dnssec_ok_flag | RFC 4035 could not be evaluated against signal sig_0038: every required... |
| sig_0038 | RFC 6840 | non_queryable | 0 | name_algorithm_set_consistency | RFC 6840 could not be evaluated against signal sig_0038: every required... |
| sig_0038 | RFC 7583 | non_queryable | 0 | key_rollover_phase | RFC 7583 could not be evaluated against signal sig_0038: every required... |
| sig_0038 | RFC 8198 | non_queryable | 0 | resolver_synthesised_nxdomain | RFC 8198 could not be evaluated against signal sig_0038: every required... |
| sig_0038 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0038: the optional indicator rfc8... |
| sig_0038 | RFC 9364 | non_queryable | 0 | declared_standards_profile | RFC 9364 could not be evaluated against signal sig_0038: every required... |
| sig_0038 | RFC 9615 | non_queryable | 0 | domain, rr_type | RFC 9615 could not be evaluated against signal sig_0038: every required... |
| sig_0038 | RFC 9904 | non_queryable | 0 | guidance_source_registry | RFC 9904 could not be evaluated against signal sig_0038: every required... |
| sig_0038 | RFC 9905 | partial_match | 0 | - | RFC 9905 partially matches signal sig_0038: the optional indicator rfc9... |

A missing field is not a failed condition: it means the corpus did not carry the value, so the condition could not be tested at all.

## 12. Review Queue

The review queue collects everything the pipeline is not entitled to decide on its own.

By severity:

| Severity | Items | Share |
| --- | --- | --- |
| high | 13 | 14.8% |
| medium | 31 | 35.2% |
| low | 44 | 50.0% |

By type:

| Item type | Items | Share |
| --- | --- | --- |
| schema_inconsistency | 44 | 50.0% |
| llm_review_recommended | 13 | 14.8% |
| non_queryable_indicator | 8 | 9.1% |
| close_ranking | 6 | 6.8% |
| missing_required_field | 4 | 4.5% |
| partial_match | 4 | 4.5% |
| ambiguous_indicator | 3 | 3.4% |
| partially_queryable_indicator | 3 | 3.4% |
| timestamp_invalid_match | 3 | 3.4% |

| Item | Type | Severity | RFCs | Reason | Suggested action |
| --- | --- | --- | --- | --- | --- |
| rev_0001 | non_queryable_indicator | high | RFC 4035 | Indicator rfc4035_dnssec_ok_negotiated (required, weight 6.0) of RFC 40... | Add `dnssec_ok_flag` to the OpenINTEL analysis dictionary with an openi... |
| rev_0002 | non_queryable_indicator | high | RFC 6840 | Indicator rfc6840_mandatory_algorithm_rules (required, weight 7.0) of R... | Add `name_algorithm_set_consistency` to the OpenINTEL analysis dictiona... |
| rev_0003 | non_queryable_indicator | high | RFC 7583 | Indicator rfc7583_rollover_timing_observed (required, weight 6.0) of RF... | Add `key_rollover_phase` to the OpenINTEL analysis dictionary with an o... |
| rev_0004 | non_queryable_indicator | high | RFC 8198 | Indicator rfc8198_aggressive_nsec_use (required, weight 6.0) of RFC 819... | Add `resolver_synthesised_nxdomain` to the OpenINTEL analysis dictionar... |
| rev_0005 | non_queryable_indicator | high | RFC 8624 | Indicator rfc8624_validator_algorithm_support (optional, weight 6.0) of... | Add `validator_algorithm_support` to the OpenINTEL analysis dictionary... |
| rev_0006 | non_queryable_indicator | high | RFC 9364 | Indicator rfc9364_bcp_profile_declared (required, weight 5.0) of RFC 93... | Add `declared_standards_profile` to the OpenINTEL analysis dictionary w... |
| rev_0007 | non_queryable_indicator | high | RFC 9615 | Indicator rfc9615_bootstrap_signal_label (required, weight 10.0) of RFC... | Add `domain` to the OpenINTEL analysis dictionary with an openintel_nat... |
| rev_0008 | non_queryable_indicator | high | RFC 9904 | Indicator rfc9904_algorithm_guidance_process (required, weight 5.0) of... | Add `guidance_source_registry` to the OpenINTEL analysis dictionary wit... |
| rev_0009 | partial_match | high | RFC 5933 | RFC 5933 matched partially on 10 observation(s): indicator(s) rfc5933_g... | Inspect indicator(s) rfc5933_ecc_gost_algorithm against signal(s) sig_0... |
| rev_0010 | partial_match | high | RFC 9906 | RFC 9906 matched partially on 5 observation(s): indicator(s) rfc9906_de... | Inspect indicator(s) rfc9906_deprecated_ecc_gost_still_published agains... |
| rev_0011 | timestamp_invalid_match | high | RFC 3110, RFC 4033, RFC 4034, RFC 4509, RFC 5702, RFC 5933, RFC 6605, R... | 9 observation(s) matched RFC 8624 indicator(s) rfc8624_avoids_deprecate... | Verify the RFC 8624 publication_date 2019-06-01T00:00:00 in the checkli... |
| rev_0012 | timestamp_invalid_match | high | RFC 3110, RFC 4033, RFC 4034, RFC 4509, RFC 9905 | 4 observation(s) matched RFC 9905 indicator(s) rfc9905_deprecated_sha1_... | Verify the RFC 9905 publication_date 2025-11-01T00:00:00 in the checkli... |
| rev_0013 | timestamp_invalid_match | high | RFC 4033, RFC 4034, RFC 5933, RFC 6605, RFC 8624, RFC 9906 | 8 observation(s) matched RFC 9906 indicator(s) rfc9906_deprecated_ecc_g... | Verify the RFC 9906 publication_date 2025-11-01T00:00:00 in the checkli... |
| rev_0014 | ambiguous_indicator | medium | RFC 6605, RFC 8080, RFC 8624 | Indicator rfc8624_avoids_deprecated_algorithm of RFC 8624 is ambiguous... | Decide attribution by hand for signal(s) sig_0010, sig_0011, sig_0012,... |
| rev_0015 | ambiguous_indicator | medium | RFC 6605, RFC 8080, RFC 8624 | Indicator rfc8624_recommended_signing_algorithm of RFC 8624 is ambiguou... | Decide attribution by hand for signal(s) sig_0011, sig_0012, sig_0014,... |
| rev_0016 | ambiguous_indicator | medium | RFC 6781 | Indicator rfc6781_ksk_zsk_separation of RFC 6781 is ambiguous (A DNSKEY... | Decide attribution by hand for signal(s) n/a: the observation is also c... |
| rev_0017 | close_ranking | medium | RFC 3110, RFC 4509 | RFC 4509 (score 11.25) and RFC 3110 (score 11.25) differ by 0.0%, insid... | Do not report RFC 4509 as the single best match. Compare the distinguis... |
| rev_0018 | close_ranking | medium | RFC 4033, RFC 8624 | RFC 4033 (score 3.75) and RFC 8624 (score 3.375) differ by 10.0%, insid... | Do not report RFC 4033 as the single best match. Compare the distinguis... |
| rev_0019 | close_ranking | medium | RFC 4034, RFC 8624 | RFC 8624 (score 3.375) and RFC 4034 (score 3.0) differ by 11.11%, insid... | Do not report RFC 8624 as the single best match. Compare the distinguis... |
| rev_0020 | close_ranking | medium | RFC 4509, RFC 6605 | RFC 6605 (score 13.125) and RFC 4509 (score 11.25) differ by 14.29%, in... | Do not report RFC 6605 as the single best match. Compare the distinguis... |
| rev_0021 | close_ranking | medium | RFC 5702, RFC 6605 | RFC 5702 (score 13.125) and RFC 6605 (score 13.125) differ by 0.0%, ins... | Do not report RFC 5702 as the single best match. Compare the distinguis... |
| rev_0022 | close_ranking | medium | RFC 5933, RFC 8080 | RFC 5933 (score 18.0) and RFC 8080 (score 17.25) differ by 4.17%, insid... | Do not report RFC 5933 as the single best match. Compare the distinguis... |
| rev_0023 | llm_review_recommended | medium | RFC 4033 | The deterministic verifier returned needs_manual_review for 38 trace(s)... | Open trace(s) trace_sig_0001_rfc4033, trace_sig_0002_rfc4033, trace_sig... |
| rev_0024 | llm_review_recommended | medium | RFC 4034 | The deterministic verifier returned needs_manual_review for 38 trace(s)... | Open trace(s) trace_sig_0001_rfc4034, trace_sig_0002_rfc4034, trace_sig... |
| rev_0025 | llm_review_recommended | medium | RFC 4035 | The deterministic verifier returned needs_manual_review for 38 trace(s)... | Open trace(s) trace_sig_0001_rfc4035, trace_sig_0002_rfc4035, trace_sig... |

63 further items are in `review_queue.json`.

## 13. Limitations

This pipeline does not prove RFC adoption by itself. It identifies ranked RFC candidates based on OpenINTEL-observable signals and timestamp consistency.

- **Synthetic sample data.** The measurements in this run come from a small generated sample corpus built to exercise the matching rules, not from a production OpenINTEL measurement. Absolute counts and first-seen dates carry no external meaning.
- **A single Parquet file.** One file is one slice of one measurement campaign. It cannot support statements about global deployment, and an RFC absent from these results may simply be absent from this file.
- **Record-level, not zone-level.** Each observation is one resource record. The pipeline never aggregates records into a zone-level verdict, so a zone that publishes many records is over-represented relative to one that publishes few, and per-zone policy claims (such as "this zone avoids deprecated algorithms") cannot be made from a single record.
- **Indicators the corpus cannot express.** 8 indicators (rfc4035_dnssec_ok_negotiated, rfc6840_mandatory_algorithm_rules, rfc7583_rollover_timing_observed, rfc8198_aggressive_nsec_use, rfc8624_validator_algorithm_support, rfc9364_bcp_profile_declared, rfc9615_bootstrap_signal_label, rfc9904_algorithm_guidance_process) reference fields that do not exist in the OpenINTEL dictionary, typically resolver-side behaviour. They are neither confirmed nor refuted here.
- **Broad base-DNSSEC RFCs match almost any signed zone.** RFC 4033 and its companions are matched by the presence of any DNSSEC record, so they will match nearly every signed zone regardless of what else the operator has deployed. Their low specificity multiplier deliberately keeps them below mechanism-specific RFCs (affected here: RFC 4033); a match on them should be read as "this zone is signed", not as adoption of a specific mechanism.
- **Ambiguity is structural, not incidental.** Recommendation documents such as RFC 8624 register nothing observable of their own. Any match against them is an inference about operator policy drawn from algorithm choice, which is why those indicators are marked ambiguous and penalized.
- **Timestamps bound possibility, not causation.** An observation dated after publication is consistent with the RFC; it does not show the operator acted because of the RFC, and many mechanisms were deployed before the document that describes them was published.

## 14. Next Steps

- Resolve the 28 warning(s) recorded in `run_manifest.json`; each one marks a place where the run degraded rather than failed.
- Run the pipeline against a real OpenINTEL Parquet partition rather than the sample corpus, and compare the ranking to the sample result to confirm nothing depends on the generated data.
- Aggregate observations to zone level before ranking, so that adoption is counted once per zone instead of once per record.
- Work through the review queue: the timestamp-invalid matches and the missing-required-field partials are the items most likely to indicate a checklist error rather than a data artefact.
- Extend the OpenINTEL dictionary, or drop the indicators that depend on fields it cannot supply, so the checklist states only what this data source can be asked.
- Add RFC obsoletes/updates relationships to the ranking so that a superseded document does not compete with the one that replaced it.
- Validate a sample of the top-ranked candidates against zone data or operator statements; that is the step this pipeline is explicitly not a substitute for.

## Appendix A. Warnings

- Dictionary field 'measurement_id' lists no openintel_native_fields, so the Parquet reader has no real OpenINTEL column to resolve it from; it will only be populated if a column of exactly that name exists.
- Field 'declared_standards_profile' is referenced by 1 indicator(s) (rfc9364_bcp_profile_declared) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'dnssec_ok_flag' is referenced by 2 indicator(s) (rfc4033_dnssec_ok_negotiated, rfc4035_dnssec_ok_negotiated) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. The closest defined field name is nsec3_flags.
- Field 'guidance_source_registry' is referenced by 1 indicator(s) (rfc9904_algorithm_guidance_process) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'key_rollover_phase' is referenced by 1 indicator(s) (rfc7583_rollover_timing_observed) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'name_algorithm_set_consistency' is referenced by 1 indicator(s) (rfc6840_mandatory_algorithm_rules) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'record_ttl' is referenced by 1 indicator(s) (rfc9077_nsec_ttl_bounded) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'resolver_synthesised_nxdomain' is referenced by 1 indicator(s) (rfc8198_aggressive_nsec_use) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'validator_algorithm_support' is referenced by 1 indicator(s) (rfc8624_validator_algorithm_support) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Indicator rfc4035_dnssec_ok_negotiated of RFC 4035 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc4035_dnssec_ok_negotiated is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: dnssec_ok_flag. No part of it can ever be evaluated against the measurement corpus.
- Indicator rfc6840_mandatory_algorithm_rules of RFC 6840 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc6840_mandatory_algorithm_rules is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: name_algorithm_set_consistency. No part of it can ever be evaluated against the measurement corpus.
- Indicator rfc7583_rollover_timing_observed of RFC 7583 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc7583_rollover_timing_observed is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: key_rollover_phase. No part of it can ever be evaluated against the measurement corpus.
- Indicator rfc8198_aggressive_nsec_use of RFC 8198 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc8198_aggressive_nsec_use is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: resolver_synthesised_nxdomain. No part of it can ever be evaluated against the measurement corpus.
- Indicator rfc8624_validator_algorithm_support of RFC 8624 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc8624_validator_algorithm_support is non-queryable: the field carrying its discriminating value, validator_algorithm_support, is absent from the OpenINTEL dictionary, and the only field that remains, rr_type (string), merely scopes which records are considered and is not used by any other RFC 8624 indicator, so nothing testable is left to attribute an observation to RFC 8624.
- Indicator rfc9364_bcp_profile_declared of RFC 9364 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc9364_bcp_profile_declared is non-queryable because none of the fields it references exist in the OpenINTEL dictionary: declared_standards_profile. No part of it can ever be evaluated against the measurement corpus.
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
- RFC 9905 has 15966 partial_match observation(s) in the corpus aggregates but does not appear among the ranked candidates: no sampled exemplar earned a score above the threshold. The aggregate counts are still exact; only the ranking is exemplar-derived.
- RFC 9906 has 90 partial_match observation(s) in the corpus aggregates but does not appear among the ranked candidates: no sampled exemplar earned a score above the threshold. The aggregate counts are still exact; only the ranking is exemplar-derived.
