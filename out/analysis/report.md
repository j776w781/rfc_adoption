# OpenINTEL RFC Adoption Analysis

Generated: 2026-08-06T20:39:57  
Pipeline: openintel-rfc-adoption-matcher 0.1.0  
Observation window: 2018-01-04 to 2026-04-13

This report identifies ranked RFC candidates that are consistent with the observed OpenINTEL signals. Read Section 13 before quoting any number from it.

## 1. Executive Summary

This run evaluated 2,755,488,262 OpenINTEL rows across 3127 partitions against 8 DNSSEC RFCs (17 indicators); 2,755,488,262 (100.0% of them) reached a rankable decision. That row count is what survived the DNSSEC record-type prefilter, not the size of the partitions: rows of other record types are excluded before any indicator is evaluated, which is what makes a corpus this size tractable. The observation counts in section 7 are exact aggregates over those rows. The 29 observations carried through sections 6 and 8 are a deterministic *sample*, kept so that every aggregate has a worked reasoning trace behind it -- their number is not a measurement of anything. Every score below is derived from record-level observations and the RFC publication date; nothing here is an assertion that an operator deliberately implemented a specification.

The highest-ranked candidate is **RFC 5155** (DNS Security (DNSSEC) Hashed Authenticated Denial of Existence) with score 17.25 (very_high confidence), supported by 429544241 observations, first seen 2018-01-01.

- Observation window: 2018-01-04 to 2026-04-13.
- Valid matches: 55; partial: 24; ambiguous: 11; no match: 139.
- Rejected on publication date (impossible timestamps): 3.
- Ranked candidates emitted: 8.
- Review queue: 31 items, 2 of high severity.
- Warnings collected during the run: 10.

## 2. Inputs

| Input | Value |
| --- | --- |
| Checklist database | E:/Documents/University/year2/DNSSEC/rfc_adoption/data/rfc_checklists/dnssec_rfc_checklists.json |
| OpenINTEL dictionary | E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json |
| Parquet input | (none) |
| Output directory | out/analysis |
| Parquet engine | auto |
| Row limit | none |
| Minimum rankable score | 0 |
| Generated at | 2026-08-06T20:39:57 |
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

17 indicators across 8 RFCs were checked against 10 dictionary fields before any measurement data was read.

| Queryability | Indicators | Share |
| --- | --- | --- |
| queryable | 13 | 76.5% |
| ambiguous | 2 | 11.8% |
| non_queryable | 1 | 5.9% |
| partially_queryable | 1 | 5.9% |

Dictionary fields that no indicator references: `domain`, `flags`, `key_tag`, `measurement_id`, `source`, `timestamp`, `zone`.

Schema warnings:

- RFC 4033 lists related RFC 'RFC 4034', which is not defined in this checklist database; the relationship cannot be resolved or ranked against.
- RFC 4033 lists related RFC 'RFC 4035', which is not defined in this checklist database; the relationship cannot be resolved or ranked against.
- Dictionary field 'measurement_id' lists no openintel_native_fields, so the Parquet reader has no real OpenINTEL column to resolve it from; it will only be populated if a column of exactly that name exists.
- Field 'dnssec_ok_flag' is referenced by 1 indicator(s) (rfc4033_dnssec_ok_negotiated) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'validator_algorithm_support' is referenced by 1 indicator(s) (rfc8624_validator_algorithm_support) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Indicator rfc8624_validator_algorithm_support of RFC 8624 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc8624_validator_algorithm_support is non-queryable: the field carrying its discriminating value, validator_algorithm_support, is absent from the OpenINTEL dictionary, and the only field that remains, rr_type (string), merely scopes which records are considered and is not used by any other RFC 8624 indicator, so nothing testable is left to attribute an observation to RFC 8624.
- RFC 4033 was published 2005-03-01, but the OpenINTEL fields its indicators rely on only become available later: `algorithm` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 4033 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- RFC 4509 was published 2006-05-01, but the OpenINTEL fields its indicators rely on only become available later: `digest_type` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 4509 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- RFC 5155 was published 2008-03-01, but the OpenINTEL fields its indicators rely on only become available later: `algorithm` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 5155 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- Dictionary fields `domain` (from 2010-01-01), `flags` (from 2016-01-01), `key_tag` (from 2010-01-01), `measurement_id` (from 2010-01-01), `source` (from 2010-01-01), `timestamp` (from 2010-01-01), `zone` (from 2010-01-01) become available after the earliest RFC in this checklist was published. No indicator references them today, but any future indicator built on them will inherit that lower bound.

## 5. Queryable vs Non-Queryable Indicators

### 5.1 Queryable indicators

| RFC | Indicator | Role | Weight | Fields used |
| --- | --- | --- | --- | --- |
| RFC 4033 | rfc4033_base_dnssec_record_present | required | 4 | rr_type |
| RFC 4033 | rfc4033_dnssec_algorithm_present | optional | 2 | algorithm |
| RFC 4509 | rfc4509_ds_sha256_digest | required | 9 | rr_type, digest_type |
| RFC 5155 | rfc5155_nsec3_hash_algorithm | optional | 3 | rr_type, algorithm |
| RFC 5155 | rfc5155_nsec3_record_present | required | 10 | rr_type |
| RFC 6605 | rfc6605_ecdsa_algorithm | required | 9 | algorithm |
| RFC 6605 | rfc6605_ecdsa_on_key_or_signature | optional | 3 | rr_type, algorithm |
| RFC 7344 | rfc7344_cds_cdnskey_present | required | 9 | rr_type |
| RFC 7344 | rfc7344_cds_publishes_digest | optional | 3 | rr_type, digest_type |
| RFC 8078 | rfc8078_cds_cdnskey_algorithm_zero | required | 10 | rr_type, algorithm |
| RFC 8078 | rfc8078_delete_signal_digest_zero | optional | 3 | rr_type, digest_type |
| RFC 8080 | rfc8080_eddsa_algorithm | required | 10 | algorithm |
| RFC 8080 | rfc8080_eddsa_on_key_or_signature | optional | 3 | rr_type, algorithm |

### 5.2 Non-queryable indicators

| RFC | Indicator | Missing fields | Reason |
| --- | --- | --- | --- |
| RFC 8624 | rfc8624_validator_algorithm_support | validator_algorithm_support | Indicator rfc8624_validator_algorithm_support is non-queryable: the fie... |

These indicators are not scored as failures. They are excluded from evaluation and raised in the review queue, because a field the corpus does not carry is an absence of measurement, not evidence of absence.

### 5.3 Partially queryable and ambiguous indicators

| RFC | Indicator | Queryability | Missing fields | Reason |
| --- | --- | --- | --- | --- |
| RFC 4033 | rfc4033_dnssec_ok_negotiated | partially_queryable | dnssec_ok_flag | Indicator rfc4033_dnssec_ok_negotiated is partially queryable: rr_type... |
| RFC 8624 | rfc8624_avoids_deprecated_algorithm | ambiguous | - | Indicator rfc8624_avoids_deprecated_algorithm is ambiguous: every field... |
| RFC 8624 | rfc8624_recommended_signing_algorithm | ambiguous | - | Indicator rfc8624_recommended_signing_algorithm is ambiguous: every fie... |

A partially queryable indicator can be evaluated on the fields that exist, but its verdict is weaker than the checklist intends. An ambiguous indicator is measurable yet not uniquely attributable to the RFC that lists it.

## 6. Observed OpenINTEL Signals

29 observations are shown below. These are a deterministic sample of the 2,755,488,262 rows scanned, not the corpus: the distributions in this section describe the sample and must not be read as corpus proportions. The exact per-RFC corpus counts are in section 7, covering 2018-01-04 to 2026-04-13.

- Distinct domains: 29.
- Distinct zones: 0.
- Observations carrying an algorithm number: 29.

Resource record types observed:

| Record type | Observations | Share |
| --- | --- | --- |
| DS | 8 | 27.6% |
| RRSIG | 8 | 27.6% |
| CDNSKEY | 5 | 17.2% |
| CDS | 4 | 13.8% |
| NSEC3PARAM | 2 | 6.9% |
| DNSKEY | 1 | 3.4% |
| NSEC3 | 1 | 3.4% |

DNSSEC algorithm numbers observed:

| Algorithm | Observations | Share |
| --- | --- | --- |
| 13 | 12 | 41.4% |
| 8 | 6 | 20.7% |
| 0 | 5 | 17.2% |
| 1 | 3 | 10.3% |
| 15 | 2 | 6.9% |
| 7 | 1 | 3.4% |

Each row is one record-level observation. A zone that publishes several records appears several times, so observation counts measure records seen, not zones deployed.

## 7. Ranked RFC Matches

| Rank | RFC | Title | Score | Confidence | Supporting observations | First seen |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | RFC 5155 | DNS Security (DNSSEC) Hashed Authenticated Denial of Existence | 17.25 | very_high | 429544241 | 2018-01-01 |
| 2 | RFC 8080 | Edwards-Curve Digital Security Algorithm (EdDSA) for DNSSEC | 17.25 | very_high | 6642303 | 2021-01-01 |
| 3 | RFC 8078 | Managing DS Records from the Parent via CDS/CDNSKEY | 17.25 | very_high | 165951 | 2018-08-29 |
| 4 | RFC 6605 | Elliptic Curve Digital Signature Algorithm (DSA) for DNSSEC | 13.125 | very_high | 549969844 | 2018-01-01 |
| 5 | RFC 7344 | Automating DNSSEC Delegation Trust Maintenance | 13.125 | very_high | 2290509 | 2018-01-01 |
| 6 | RFC 4509 | Use of SHA-256 in DNSSEC Delegation Signer (DS) Resource Records | 11.25 | high | 135810997 | 2018-01-01 |
| 7 | RFC 4033 | DNS Security Introduction and Requirements (DNSSEC base: RFC 4033/4034/... | 3.75 | low | 2323653512 | 2018-01-01 |
| 8 | RFC 8624 | Algorithm Implementation Requirements and Usage Guidance for DNSSEC | 3.375 | low | 495136786 | 2019-06-01 |

Score is the best per-signal score for that RFC, after the specificity multiplier (very_high 1.5, high 1.25, medium 1.0, low 0.75) has been applied. A broad RFC with many observations can therefore rank below a narrow RFC with one unambiguous observation, which is the intended behaviour: specificity is evidence.

Per-candidate evidence breakdown:

| RFC | Best score | Aggregate score | Valid | Partial | Timestamp-invalid | Matched indicators |
| --- | --- | --- | --- | --- | --- | --- |
| RFC 5155 | 17.25 | 51.75 | 429544241 | 0 | 0 | rfc5155_nsec3_hash_algorithm, rfc5155_nsec3_record_present |
| RFC 8080 | 17.25 | 34.5 | 6642303 | 0 | 0 | rfc8080_eddsa_algorithm, rfc8080_eddsa_on_key_or_signature |
| RFC 8078 | 17.25 | 79.5 | 165951 | 0 | 0 | rfc8078_cds_cdnskey_algorithm_zero, rfc8078_delete_signal_digest_zero |
| RFC 6605 | 13.125 | 157.5 | 549969844 | 0 | 0 | rfc6605_ecdsa_algorithm, rfc6605_ecdsa_on_key_or_signature |
| RFC 7344 | 13.125 | 105 | 2290509 | 0 | 0 | rfc7344_cds_cdnskey_present, rfc7344_cds_publishes_digest |
| RFC 4509 | 11.25 | 78.75 | 135810997 | 0 | 0 | rfc4509_ds_sha256_digest |
| RFC 4033 | 3.75 | 63.75 | 2323653512 | 431834750 | 0 | rfc4033_base_dnssec_record_present, rfc4033_dnssec_algorithm_present |
| RFC 8624 | 3.375 | 37.125 | 0 | 1736968879 | 61401575 | rfc8624_avoids_deprecated_algorithm, rfc8624_recommended_signing_algori... |

## 8. Reasoning Summary

Every one of the 232 signal-by-RFC evaluations carries a stored reasoning trace: the conditions that passed, the conditions that failed, the fields that were missing, the timestamp verdict and the arithmetic of the score. Non-matches are traced too, because the reason an RFC was *not* selected is as much a result as the reason one was.

| Decision | Traces | Share |
| --- | --- | --- |
| no_match | 139 | 59.9% |
| valid_match | 55 | 23.7% |
| partial_match | 24 | 10.3% |
| ambiguous | 11 | 4.7% |
| timestamp_invalid | 3 | 1.3% |

Verbatim reasoning summaries from this run:

**trace_sig_0023_rfc8078** - RFC 8078, signal `sig_0023`, decision `valid_match`, score 17.25:

> RFC 8078 matched signal sig_0023: the required indicator rfc8078_cds_cdnskey_algorithm_zero passed because rr_type=CDS is in [CDS, CDNSKEY] and algorithm=0 equals the expected value 0. Corroborating indicators also matched: rfc8078_delete_signal_digest_zero. The observation on 2021-12-25T08:22:57 is 1760 days after RFC 8078's publication on 2017-03-01, so the timestamp is valid. Score 17.25 (very_high) = (10.0 required + 1.5 optional) x 1.5 very_high specificity.

**trace_sig_0013_rfc8624** - RFC 8624, signal `sig_0013`, decision `timestamp_invalid`, score 0.0:

> RFC 8624 cannot explain signal sig_0013: although algorithm=13 satisfy the required indicator rfc8624_recommended_signing_algorithm, the observation on 2019-04-21T02:25:06 predates RFC 8624's publication on 2019-06-01 by 41 days. An observation cannot evidence adoption of an RFC that did not yet exist, so the score of 3.375 is forfeited and this is routed to the review queue. The withheld score derives from (5.0 required + 1.5 optional - 2.0 ambiguity penalty) x 0.75 low specificity.

**trace_sig_0028_rfc8624** - RFC 8624, signal `sig_0028`, decision `ambiguous`, score 3.375:

> RFC 8624 is an ambiguous match for signal sig_0028: the required indicator rfc8624_recommended_signing_algorithm passed because algorithm=13 is in [13, 15]. Corroborating indicators also matched: rfc8624_avoids_deprecated_algorithm. The checklist flags rfc8624_avoids_deprecated_algorithm, rfc8624_recommended_signing_algorithm ambiguous: the same observation is equally explained by other RFCs, so the match is penalized and sent to the review queue rather than reported as adoption. The observation on 2024-11-06T00:59:29 is 1985 days after RFC 8624's publication on 2019-06-01, so the timestamp is valid. Score 3.375 (low) = (5.0 required + 1.5 optional - 2.0 ambiguity penalty) x 0.75 low specificity.

## 9. First-Seen Dates / Adoption Timeline

First-seen is the earliest *valid* match: an observation dated at or after the RFC's publication date. It is the first date this corpus saw the mechanism, which is an upper bound on when deployment began and says nothing about deployment before the measurement window.

| RFC | Published | First seen | Last seen | Days from publication | Observations | Distinct domains |
| --- | --- | --- | --- | --- | --- | --- |
| RFC 4033 | 2005-03-01 | 2018-01-01 | 2026-04-29 | 4689 | 2323653512 | 2939647 |
| RFC 4509 | 2006-05-01 | 2018-01-01 | 2026-04-29 | 4263 | 135810997 | 954024 |
| RFC 5155 | 2008-03-01 | 2018-01-01 | 2026-04-29 | 3593 | 429544241 | 1551219 |
| RFC 6605 | 2012-04-01 | 2018-01-01 | 2026-04-29 | 2101 | 549969844 | 1189221 |
| RFC 7344 | 2014-09-01 | 2018-01-01 | 2026-04-29 | 1218 | 2290509 | 2663 |
| RFC 8078 | 2017-03-01 | 2018-08-29 | 2026-04-29 | 546 | 165951 | 325 |
| RFC 8624 | 2019-06-01 | 2019-06-01 | 2026-04-29 | 0 | 495136786 | 1217448 |
| RFC 8080 | 2017-02-01 | 2021-01-01 | 2024-11-07 | 1430 | 6642303 | 53365 |

Monthly observation buckets (valid matches only):

| RFC | Period | Observations | Domains | Mean score |
| --- | --- | --- | --- | --- |
| RFC 4033 | 2018-01 | 411512014 | 2864058 | 3.75 |
| RFC 4033 | 2018-02 | 58403375 | 478516 | 3.75 |
| RFC 4033 | 2018-03 | 64097630 | 479538 | 3.75 |
| RFC 4033 | 2018-04 | 64217822 | 520890 | 3.75 |
| RFC 4033 | 2018-05 | 67012440 | 520918 | 3.75 |
| RFC 4033 | 2018-06 | 60481862 | 481328 | 3.75 |
| RFC 4033 | 2018-07 | 62986185 | 481328 | 3.75 |
| RFC 4033 | 2018-08 | 62980844 | 481328 | 3.75 |
| RFC 4033 | 2018-09 | 61030415 | 481328 | 3.75 |
| RFC 4033 | 2018-10 | 63691687 | 488493 | 3.75 |
| RFC 4033 | 2018-11 | 59421730 | 506123 | 3.75 |
| RFC 4033 | 2018-12 | 52064678 | 436436 | 3.75 |
| RFC 4033 | 2019-01 | 46793011 | 420578 | 3.75 |
| RFC 4033 | 2019-02 | 47259046 | 438583 | 3.75 |
| RFC 4033 | 2019-03 | 53474040 | 450498 | 3.75 |
| RFC 4033 | 2019-04 | 17822997 | 436505 | 3.75 |
| RFC 4033 | 2019-05 | 755170 | 3562 | 3.75 |
| RFC 4033 | 2019-06 | 731389 | 3529 | 3.75 |
| RFC 4033 | 2019-07 | 753668 | 3529 | 3.75 |
| RFC 4033 | 2019-08 | 748711 | 3529 | 3.75 |
| RFC 4033 | 2019-09 | 724319 | 3562 | 3.75 |
| RFC 4033 | 2019-10 | 754461 | 3562 | 3.75 |
| RFC 4033 | 2019-11 | 754153 | 3596 | 3.75 |
| RFC 4033 | 2019-12 | 784836 | 3596 | 3.75 |
| RFC 4033 | 2020-01 | 784381 | 3596 | 3.75 |
| RFC 4033 | 2020-02 | 744945 | 3596 | 3.75 |
| RFC 4033 | 2020-03 | 788252 | 3596 | 3.75 |
| RFC 4033 | 2020-04 | 747560 | 3631 | 3.75 |
| RFC 4033 | 2020-05 | 773820 | 3631 | 3.75 |
| RFC 4033 | 2020-06 | 744218 | 3720 | 3.75 |
| RFC 4033 | 2020-07 | 775890 | 3720 | 3.75 |
| RFC 4033 | 2020-08 | 784896 | 3720 | 3.75 |
| RFC 4033 | 2020-09 | 101558 | 3720 | 3.75 |
| RFC 4033 | 2021-01 | 196192370 | 2939647 | 3.75 |
| RFC 4033 | 2021-02 | 57422169 | 514470 | 3.75 |
| RFC 4033 | 2021-03 | 63292628 | 509318 | 3.75 |
| RFC 4033 | 2021-04 | 60649772 | 509318 | 3.75 |
| RFC 4033 | 2021-05 | 60389937 | 504098 | 3.75 |
| RFC 4033 | 2021-06 | 60433501 | 504098 | 3.75 |
| RFC 4033 | 2021-07 | 62414495 | 508933 | 3.75 |
| RFC 4033 | 2021-08 | 62747031 | 508975 | 3.75 |
| RFC 4033 | 2021-09 | 60124627 | 509003 | 3.75 |
| RFC 4033 | 2021-10 | 62129987 | 505047 | 3.75 |
| RFC 4033 | 2021-11 | 60816661 | 524734 | 3.75 |
| RFC 4033 | 2021-12 | 62394398 | 524734 | 3.75 |
| RFC 4033 | 2023-01 | 32400898 | 574234 | 3.75 |
| RFC 4033 | 2023-02 | 902295 | 6779 | 3.75 |
| RFC 4033 | 2023-03 | 1000398 | 6810 | 3.75 |
| RFC 4033 | 2023-04 | 978851 | 6810 | 3.75 |
| RFC 4033 | 2023-05 | 996676 | 6989 | 3.75 |
| RFC 4033 | 2023-06 | 987540 | 7113 | 3.75 |
| RFC 4033 | 2023-07 | 1030127 | 7113 | 3.75 |
| RFC 4033 | 2023-08 | 995412 | 7113 | 3.75 |
| RFC 4033 | 2023-09 | 995666 | 7388 | 3.75 |
| RFC 4033 | 2023-10 | 1025123 | 7972 | 3.75 |
| RFC 4033 | 2023-11 | 985599 | 7738 | 3.75 |
| RFC 4033 | 2023-12 | 1038585 | 7900 | 3.75 |
| RFC 4033 | 2024-01 | 63369035 | 440378 | 3.75 |
| RFC 4033 | 2024-02 | 59023883 | 440099 | 3.75 |
| RFC 4033 | 2024-03 | 7081825 | 434860 | 3.75 |
| RFC 4033 | 2024-04 | 1063973 | 8101 | 3.75 |
| RFC 4033 | 2024-05 | 1123876 | 8346 | 3.75 |
| RFC 4033 | 2024-06 | 1087370 | 8346 | 3.75 |
| RFC 4033 | 2024-07 | 1091065 | 8938 | 3.75 |
| RFC 4033 | 2024-08 | 1143576 | 8938 | 3.75 |
| RFC 4033 | 2024-09 | 1312286 | 8938 | 3.75 |
| RFC 4033 | 2024-10 | 2350303 | 9154 | 3.75 |
| RFC 4033 | 2024-11 | 879910 | 9154 | 3.75 |
| RFC 4033 | 2024-12 | 1117310 | 9499 | 3.75 |
| RFC 4033 | 2026-01 | 1328734 | 9593 | 3.75 |
| RFC 4033 | 2026-02 | 1209364 | 9589 | 3.75 |
| RFC 4033 | 2026-03 | 1352350 | 9589 | 3.75 |
| RFC 4033 | 2026-04 | 1271903 | 9589 | 3.75 |
| RFC 4509 | 2018-01 | 26799778 | 946089 | 11.25 |
| RFC 4509 | 2018-02 | 3286657 | 111779 | 11.25 |
| RFC 4509 | 2018-03 | 3676778 | 116913 | 11.25 |
| RFC 4509 | 2018-04 | 3752792 | 116157 | 11.25 |
| RFC 4509 | 2018-05 | 3964639 | 120115 | 11.25 |
| RFC 4509 | 2018-06 | 3631789 | 116157 | 11.25 |
| RFC 4509 | 2018-07 | 3750843 | 115074 | 11.25 |
| RFC 4509 | 2018-08 | 3744899 | 110900 | 11.25 |
| RFC 4509 | 2018-09 | 3621606 | 107978 | 11.25 |
| RFC 4509 | 2018-10 | 3659943 | 109988 | 11.25 |
| RFC 4509 | 2018-11 | 3263739 | 114709 | 11.25 |
| RFC 4509 | 2018-12 | 2709766 | 97726 | 11.25 |
| RFC 4509 | 2019-01 | 2602601 | 86344 | 11.25 |
| RFC 4509 | 2019-02 | 2384246 | 86644 | 11.25 |
| RFC 4509 | 2019-03 | 2704328 | 87254 | 11.25 |
| RFC 4509 | 2019-04 | 908754 | 87254 | 11.25 |
| RFC 4509 | 2019-05 | 47993 | 1199 | 11.25 |
| RFC 4509 | 2019-06 | 46431 | 1184 | 11.25 |
| RFC 4509 | 2019-07 | 47780 | 1184 | 11.25 |
| RFC 4509 | 2019-08 | 47254 | 1184 | 11.25 |
| RFC 4509 | 2019-09 | 45749 | 1192 | 11.25 |
| RFC 4509 | 2019-10 | 48207 | 1192 | 11.25 |
| RFC 4509 | 2019-11 | 48512 | 1192 | 11.25 |
| RFC 4509 | 2019-12 | 51768 | 1192 | 11.25 |
| RFC 4509 | 2020-01 | 52223 | 1192 | 11.25 |
| RFC 4509 | 2020-02 | 49606 | 1148 | 11.25 |
| RFC 4509 | 2020-03 | 52822 | 1148 | 11.25 |
| RFC 4509 | 2020-04 | 50383 | 1148 | 11.25 |
| RFC 4509 | 2020-05 | 52096 | 1108 | 11.25 |
| RFC 4509 | 2020-06 | 49464 | 1108 | 11.25 |
| RFC 4509 | 2020-07 | 51202 | 1102 | 11.25 |
| RFC 4509 | 2020-08 | 51804 | 1203 | 11.25 |
| RFC 4509 | 2020-09 | 6685 | 1211 | 11.25 |
| RFC 4509 | 2021-01 | 11897373 | 954024 | 11.25 |
| RFC 4509 | 2021-02 | 3164121 | 120628 | 11.25 |
| RFC 4509 | 2021-03 | 3494632 | 120628 | 11.25 |
| RFC 4509 | 2021-04 | 3362528 | 118317 | 11.25 |
| RFC 4509 | 2021-05 | 3349689 | 118349 | 11.25 |
| RFC 4509 | 2021-06 | 3354705 | 118349 | 11.25 |
| RFC 4509 | 2021-07 | 3465573 | 112945 | 11.25 |
| RFC 4509 | 2021-08 | 3465588 | 112982 | 11.25 |
| RFC 4509 | 2021-09 | 3348523 | 112982 | 11.25 |
| RFC 4509 | 2021-10 | 3469349 | 112982 | 11.25 |
| RFC 4509 | 2021-11 | 3352419 | 107136 | 11.25 |
| RFC 4509 | 2021-12 | 3445541 | 107145 | 11.25 |
| RFC 4509 | 2023-01 | 1828613 | 123612 | 11.25 |
| RFC 4509 | 2023-02 | 59556 | 1483 | 11.25 |
| RFC 4509 | 2023-03 | 65484 | 1596 | 11.25 |
| RFC 4509 | 2023-04 | 63057 | 1666 | 11.25 |
| RFC 4509 | 2023-05 | 65854 | 1715 | 11.25 |
| RFC 4509 | 2023-06 | 65594 | 1715 | 11.25 |
| RFC 4509 | 2023-07 | 69571 | 1747 | 11.25 |
| RFC 4509 | 2023-08 | 67382 | 1763 | 11.25 |
| RFC 4509 | 2023-09 | 65358 | 1634 | 11.25 |
| RFC 4509 | 2023-10 | 67678 | 1706 | 11.25 |
| RFC 4509 | 2023-11 | 66590 | 1676 | 11.25 |
| RFC 4509 | 2023-12 | 69925 | 1676 | 11.25 |
| RFC 4509 | 2024-01 | 3674633 | 128942 | 11.25 |
| RFC 4509 | 2024-02 | 3447425 | 128886 | 11.25 |
| RFC 4509 | 2024-03 | 428450 | 119603 | 11.25 |
| RFC 4509 | 2024-04 | 76960 | 1648 | 11.25 |
| RFC 4509 | 2024-05 | 82764 | 1648 | 11.25 |
| RFC 4509 | 2024-06 | 81498 | 1648 | 11.25 |
| RFC 4509 | 2024-07 | 83571 | 1648 | 11.25 |
| RFC 4509 | 2024-08 | 88143 | 1648 | 11.25 |
| RFC 4509 | 2024-09 | 101070 | 1606 | 11.25 |
| RFC 4509 | 2024-10 | 181044 | 1606 | 11.25 |
| RFC 4509 | 2024-11 | 67916 | 1606 | 11.25 |
| RFC 4509 | 2024-12 | 85236 | 1609 | 11.25 |
| RFC 4509 | 2026-01 | 109022 | 2447 | 11.25 |
| RFC 4509 | 2026-02 | 99275 | 2447 | 11.25 |
| RFC 4509 | 2026-03 | 111142 | 2479 | 11.25 |
| RFC 4509 | 2026-04 | 105008 | 2423 | 11.25 |
| RFC 5155 | 2018-01 | 76976543 | 1551219 | 17.25 |
| RFC 5155 | 2018-02 | 10928903 | 246860 | 17.25 |
| RFC 5155 | 2018-03 | 11933285 | 248066 | 17.25 |
| RFC 5155 | 2018-04 | 11885924 | 283859 | 17.25 |
| RFC 5155 | 2018-05 | 12773700 | 287115 | 17.25 |
| RFC 5155 | 2018-06 | 12310466 | 287115 | 17.25 |
| RFC 5155 | 2018-07 | 12718774 | 280544 | 17.25 |
| RFC 5155 | 2018-08 | 12696104 | 280544 | 17.25 |
| RFC 5155 | 2018-09 | 12268102 | 274260 | 17.25 |
| RFC 5155 | 2018-10 | 12650641 | 299512 | 17.25 |
| RFC 5155 | 2018-11 | 11996238 | 306055 | 17.25 |
| RFC 5155 | 2018-12 | 10975327 | 290600 | 17.25 |
| RFC 5155 | 2019-01 | 9512690 | 201018 | 17.25 |
| RFC 5155 | 2019-02 | 8691071 | 203983 | 17.25 |
| RFC 5155 | 2019-03 | 9773199 | 203951 | 17.25 |
| RFC 5155 | 2019-04 | 3223502 | 189773 | 17.25 |
| RFC 5155 | 2019-05 | 91313 | 1710 | 17.25 |
| RFC 5155 | 2019-06 | 87955 | 1657 | 17.25 |
| RFC 5155 | 2019-07 | 91786 | 1657 | 17.25 |
| RFC 5155 | 2019-08 | 87566 | 1657 | 17.25 |
| RFC 5155 | 2019-09 | 83359 | 1608 | 17.25 |
| RFC 5155 | 2019-10 | 85722 | 1581 | 17.25 |
| RFC 5155 | 2019-11 | 86819 | 1639 | 17.25 |
| RFC 5155 | 2019-12 | 91604 | 1745 | 17.25 |
| RFC 5155 | 2020-01 | 92003 | 1745 | 17.25 |
| RFC 5155 | 2020-02 | 85926 | 1714 | 17.25 |
| RFC 5155 | 2020-03 | 89115 | 1714 | 17.25 |
| RFC 5155 | 2020-04 | 80770 | 1571 | 17.25 |
| RFC 5155 | 2020-05 | 83307 | 1632 | 17.25 |
| RFC 5155 | 2020-06 | 82106 | 1575 | 17.25 |
| RFC 5155 | 2020-07 | 86125 | 1575 | 17.25 |
| RFC 5155 | 2020-08 | 86200 | 1568 | 17.25 |
| RFC 5155 | 2020-09 | 11122 | 1568 | 17.25 |
| RFC 5155 | 2021-01 | 35355425 | 1428369 | 17.25 |
| RFC 5155 | 2021-02 | 10457695 | 200002 | 17.25 |
| RFC 5155 | 2021-03 | 11554236 | 200054 | 17.25 |
| RFC 5155 | 2021-04 | 11135980 | 197695 | 17.25 |
| RFC 5155 | 2021-05 | 11126957 | 197695 | 17.25 |
| RFC 5155 | 2021-06 | 11125137 | 197725 | 17.25 |
| RFC 5155 | 2021-07 | 11477324 | 197725 | 17.25 |
| RFC 5155 | 2021-08 | 11470834 | 197674 | 17.25 |
| RFC 5155 | 2021-09 | 11048345 | 197674 | 17.25 |
| RFC 5155 | 2021-10 | 11395680 | 201906 | 17.25 |
| RFC 5155 | 2021-11 | 11006703 | 205276 | 17.25 |
| RFC 5155 | 2021-12 | 11321553 | 205333 | 17.25 |
| RFC 5155 | 2023-01 | 5117398 | 219612 | 17.25 |
| RFC 5155 | 2023-02 | 84940 | 1608 | 17.25 |
| RFC 5155 | 2023-03 | 94286 | 1677 | 17.25 |
| RFC 5155 | 2023-04 | 88526 | 1692 | 17.25 |
| RFC 5155 | 2023-05 | 83774 | 1538 | 17.25 |
| RFC 5155 | 2023-06 | 82708 | 1482 | 17.25 |
| RFC 5155 | 2023-07 | 86039 | 1512 | 17.25 |
| RFC 5155 | 2023-08 | 83645 | 1536 | 17.25 |
| RFC 5155 | 2023-09 | 84391 | 1512 | 17.25 |
| RFC 5155 | 2023-10 | 86667 | 1503 | 17.25 |
| RFC 5155 | 2023-11 | 84040 | 1527 | 17.25 |
| RFC 5155 | 2023-12 | 89396 | 1503 | 17.25 |
| RFC 5155 | 2024-01 | 10328076 | 219987 | 17.25 |
| RFC 5155 | 2024-02 | 9686315 | 220023 | 17.25 |
| RFC 5155 | 2024-03 | 1084525 | 212372 | 17.25 |
| RFC 5155 | 2024-04 | 86703 | 1527 | 17.25 |
| RFC 5155 | 2024-05 | 86854 | 1509 | 17.25 |
| RFC 5155 | 2024-06 | 82667 | 1509 | 17.25 |
| RFC 5155 | 2024-07 | 82594 | 1485 | 17.25 |
| RFC 5155 | 2024-08 | 86311 | 1485 | 17.25 |
| RFC 5155 | 2024-09 | 98667 | 1482 | 17.25 |
| RFC 5155 | 2024-10 | 175592 | 1506 | 17.25 |
| RFC 5155 | 2024-11 | 65961 | 1506 | 17.25 |
| RFC 5155 | 2024-12 | 84354 | 1530 | 17.25 |
| RFC 5155 | 2026-01 | 88964 | 1424 | 17.25 |
| RFC 5155 | 2026-02 | 80083 | 1382 | 17.25 |
| RFC 5155 | 2026-03 | 86938 | 1382 | 17.25 |
| RFC 5155 | 2026-04 | 80691 | 1362 | 17.25 |
| RFC 6605 | 2018-01 | 15425166 | 132228 | 13.125 |
| RFC 6605 | 2018-02 | 778890 | 5414 | 13.125 |
| RFC 6605 | 2018-03 | 901219 | 5599 | 13.125 |
| RFC 6605 | 2018-04 | 837304 | 5832 | 13.125 |
| RFC 6605 | 2018-05 | 926667 | 5840 | 13.125 |
| RFC 6605 | 2018-06 | 987730 | 6521 | 13.125 |
| RFC 6605 | 2018-07 | 1024133 | 7424 | 13.125 |
| RFC 6605 | 2018-08 | 1118681 | 7977 | 13.125 |
| RFC 6605 | 2018-09 | 1268654 | 8714 | 13.125 |
| RFC 6605 | 2018-10 | 2076384 | 124018 | 13.125 |
| RFC 6605 | 2018-11 | 4696458 | 131593 | 13.125 |
| RFC 6605 | 2018-12 | 4312694 | 108947 | 13.125 |
| RFC 6605 | 2019-01 | 4800014 | 152427 | 13.125 |
| RFC 6605 | 2019-02 | 8603976 | 156095 | 13.125 |
| RFC 6605 | 2019-03 | 10182874 | 167360 | 13.125 |
| RFC 6605 | 2019-04 | 3424888 | 167374 | 13.125 |
| RFC 6605 | 2019-05 | 49585 | 377 | 13.125 |
| RFC 6605 | 2019-06 | 51118 | 395 | 13.125 |
| RFC 6605 | 2019-07 | 54234 | 385 | 13.125 |
| RFC 6605 | 2019-08 | 56472 | 422 | 13.125 |
| RFC 6605 | 2019-09 | 58880 | 477 | 13.125 |
| RFC 6605 | 2019-10 | 66755 | 534 | 13.125 |
| RFC 6605 | 2019-11 | 71892 | 537 | 13.125 |
| RFC 6605 | 2019-12 | 76110 | 537 | 13.125 |
| RFC 6605 | 2020-01 | 78582 | 563 | 13.125 |
| RFC 6605 | 2020-02 | 76067 | 563 | 13.125 |
| RFC 6605 | 2020-03 | 83961 | 605 | 13.125 |
| RFC 6605 | 2020-04 | 93435 | 605 | 13.125 |
| RFC 6605 | 2020-05 | 98719 | 605 | 13.125 |
| RFC 6605 | 2020-06 | 99629 | 749 | 13.125 |
| RFC 6605 | 2020-07 | 111797 | 800 | 13.125 |
| RFC 6605 | 2020-08 | 115226 | 854 | 13.125 |
| RFC 6605 | 2020-09 | 15112 | 854 | 13.125 |
| RFC 6605 | 2021-01 | 81848969 | 1189221 | 13.125 |
| RFC 6605 | 2021-02 | 23593711 | 243805 | 13.125 |
| RFC 6605 | 2021-03 | 26303921 | 256700 | 13.125 |
| RFC 6605 | 2021-04 | 25653637 | 260779 | 13.125 |
| RFC 6605 | 2021-05 | 25728599 | 260666 | 13.125 |
| RFC 6605 | 2021-06 | 25782019 | 266416 | 13.125 |
| RFC 6605 | 2021-07 | 26712228 | 260640 | 13.125 |
| RFC 6605 | 2021-08 | 29539856 | 266170 | 13.125 |
| RFC 6605 | 2021-09 | 28761433 | 268047 | 13.125 |
| RFC 6605 | 2021-10 | 29812849 | 268054 | 13.125 |
| RFC 6605 | 2021-11 | 29403537 | 273611 | 13.125 |
| RFC 6605 | 2021-12 | 30191106 | 273680 | 13.125 |
| RFC 6605 | 2023-01 | 17302794 | 344500 | 13.125 |
| RFC 6605 | 2023-02 | 300782 | 2718 | 13.125 |
| RFC 6605 | 2023-03 | 339723 | 2825 | 13.125 |
| RFC 6605 | 2023-04 | 339859 | 2912 | 13.125 |
| RFC 6605 | 2023-05 | 371009 | 2949 | 13.125 |
| RFC 6605 | 2023-06 | 399754 | 3180 | 13.125 |
| RFC 6605 | 2023-07 | 435167 | 3394 | 13.125 |
| RFC 6605 | 2023-08 | 427648 | 3570 | 13.125 |
| RFC 6605 | 2023-09 | 437648 | 3962 | 13.125 |
| RFC 6605 | 2023-10 | 463823 | 4538 | 13.125 |
| RFC 6605 | 2023-11 | 463555 | 4636 | 13.125 |
| RFC 6605 | 2023-12 | 488862 | 4797 | 13.125 |
| RFC 6605 | 2024-01 | 35227994 | 310675 | 13.125 |
| RFC 6605 | 2024-02 | 32919192 | 310622 | 13.125 |
| RFC 6605 | 2024-03 | 3891317 | 307932 | 13.125 |
| RFC 6605 | 2024-04 | 548975 | 4974 | 13.125 |
| RFC 6605 | 2024-05 | 612150 | 6072 | 13.125 |
| RFC 6605 | 2024-06 | 637738 | 6072 | 13.125 |
| RFC 6605 | 2024-07 | 645739 | 6602 | 13.125 |
| RFC 6605 | 2024-08 | 683323 | 6780 | 13.125 |
| RFC 6605 | 2024-09 | 792189 | 6780 | 13.125 |
| RFC 6605 | 2024-10 | 1434852 | 6967 | 13.125 |
| RFC 6605 | 2024-11 | 547879 | 6967 | 13.125 |
| RFC 6605 | 2024-12 | 698900 | 7165 | 13.125 |
| RFC 6605 | 2026-01 | 908359 | 8196 | 13.125 |
| RFC 6605 | 2026-02 | 837697 | 8468 | 13.125 |
| RFC 6605 | 2026-03 | 951464 | 8468 | 13.125 |
| RFC 6605 | 2026-04 | 906281 | 8839 | 13.125 |
| RFC 7344 | 2018-01 | 27610 | 483 | 13.125 |
| RFC 7344 | 2018-02 | 4373 | 86 | 13.125 |
| RFC 7344 | 2018-03 | 6220 | 127 | 13.125 |
| RFC 7344 | 2018-04 | 8333 | 173 | 13.125 |
| RFC 7344 | 2018-05 | 10273 | 181 | 13.125 |
| RFC 7344 | 2018-06 | 10464 | 184 | 13.125 |
| RFC 7344 | 2018-07 | 11208 | 193 | 13.125 |
| RFC 7344 | 2018-08 | 11448 | 195 | 13.125 |
| RFC 7344 | 2018-09 | 11230 | 205 | 13.125 |
| RFC 7344 | 2018-10 | 12052 | 224 | 13.125 |
| RFC 7344 | 2018-11 | 12778 | 237 | 13.125 |
| RFC 7344 | 2018-12 | 13585 | 240 | 13.125 |
| RFC 7344 | 2019-01 | 14284 | 249 | 13.125 |
| RFC 7344 | 2019-02 | 16530 | 346 | 13.125 |
| RFC 7344 | 2019-03 | 22317 | 391 | 13.125 |
| RFC 7344 | 2019-04 | 10792 | 391 | 13.125 |
| RFC 7344 | 2019-05 | 5295 | 89 | 13.125 |
| RFC 7344 | 2019-06 | 5206 | 92 | 13.125 |
| RFC 7344 | 2019-07 | 5497 | 92 | 13.125 |
| RFC 7344 | 2019-08 | 5682 | 92 | 13.125 |
| RFC 7344 | 2019-09 | 5459 | 97 | 13.125 |
| RFC 7344 | 2019-10 | 5706 | 98 | 13.125 |
| RFC 7344 | 2019-11 | 5678 | 104 | 13.125 |
| RFC 7344 | 2019-12 | 5993 | 108 | 13.125 |
| RFC 7344 | 2020-01 | 6114 | 110 | 13.125 |
| RFC 7344 | 2020-02 | 5858 | 110 | 13.125 |
| RFC 7344 | 2020-03 | 6597 | 138 | 13.125 |
| RFC 7344 | 2020-04 | 7986 | 138 | 13.125 |
| RFC 7344 | 2020-05 | 8333 | 140 | 13.125 |
| RFC 7344 | 2020-06 | 8350 | 140 | 13.125 |
| RFC 7344 | 2020-07 | 8788 | 141 | 13.125 |
| RFC 7344 | 2020-08 | 9134 | 150 | 13.125 |
| RFC 7344 | 2020-09 | 1206 | 159 | 13.125 |
| RFC 7344 | 2021-01 | 90618 | 2663 | 13.125 |
| RFC 7344 | 2021-02 | 35548 | 638 | 13.125 |
| RFC 7344 | 2021-03 | 39840 | 657 | 13.125 |
| RFC 7344 | 2021-04 | 37694 | 630 | 13.125 |
| RFC 7344 | 2021-05 | 36270 | 647 | 13.125 |
| RFC 7344 | 2021-06 | 41048 | 658 | 13.125 |
| RFC 7344 | 2021-07 | 43357 | 664 | 13.125 |
| RFC 7344 | 2021-08 | 44354 | 703 | 13.125 |
| RFC 7344 | 2021-09 | 43544 | 713 | 13.125 |
| RFC 7344 | 2021-10 | 50474 | 810 | 13.125 |
| RFC 7344 | 2021-11 | 51613 | 813 | 13.125 |
| RFC 7344 | 2021-12 | 51762 | 811 | 13.125 |
| RFC 7344 | 2023-01 | 51894 | 1544 | 13.125 |
| RFC 7344 | 2023-02 | 19145 | 337 | 13.125 |
| RFC 7344 | 2023-03 | 21624 | 373 | 13.125 |
| RFC 7344 | 2023-04 | 20585 | 389 | 13.125 |
| RFC 7344 | 2023-05 | 22288 | 433 | 13.125 |
| RFC 7344 | 2023-06 | 25632 | 475 | 13.125 |
| RFC 7344 | 2023-07 | 28614 | 485 | 13.125 |
| RFC 7344 | 2023-08 | 28472 | 485 | 13.125 |
| RFC 7344 | 2023-09 | 29413 | 475 | 13.125 |
| RFC 7344 | 2023-10 | 31430 | 498 | 13.125 |
| RFC 7344 | 2023-11 | 31765 | 579 | 13.125 |
| RFC 7344 | 2023-12 | 33547 | 599 | 13.125 |
| RFC 7344 | 2024-01 | 145588 | 2135 | 13.125 |
| RFC 7344 | 2024-02 | 137883 | 2182 | 13.125 |
| RFC 7344 | 2024-03 | 47883 | 2186 | 13.125 |
| RFC 7344 | 2024-04 | 39146 | 681 | 13.125 |
| RFC 7344 | 2024-05 | 44770 | 721 | 13.125 |
| RFC 7344 | 2024-06 | 45010 | 728 | 13.125 |
| RFC 7344 | 2024-07 | 45986 | 733 | 13.125 |
| RFC 7344 | 2024-08 | 49089 | 775 | 13.125 |
| RFC 7344 | 2024-09 | 57133 | 775 | 13.125 |
| RFC 7344 | 2024-10 | 103778 | 775 | 13.125 |
| RFC 7344 | 2024-11 | 38982 | 775 | 13.125 |
| RFC 7344 | 2024-12 | 49937 | 788 | 13.125 |
| RFC 7344 | 2026-01 | 66635 | 1051 | 13.125 |
| RFC 7344 | 2026-02 | 61362 | 1087 | 13.125 |
| RFC 7344 | 2026-03 | 69864 | 1167 | 13.125 |
| RFC 7344 | 2026-04 | 66553 | 1167 | 13.125 |
| RFC 8078 | 2018-08 | 6 | 1 | 17.25 |
| RFC 8078 | 2018-09 | 60 | 1 | 17.25 |
| RFC 8078 | 2018-10 | 62 | 1 | 17.25 |
| RFC 8078 | 2018-11 | 100 | 2 | 17.25 |
| RFC 8078 | 2018-12 | 202 | 4 | 17.25 |
| RFC 8078 | 2019-01 | 422 | 10 | 17.25 |
| RFC 8078 | 2019-02 | 540 | 15 | 17.25 |
| RFC 8078 | 2019-03 | 602 | 14 | 17.25 |
| RFC 8078 | 2019-04 | 202 | 12 | 17.25 |
| RFC 8078 | 2019-08 | 58 | 1 | 17.25 |
| RFC 8078 | 2019-09 | 60 | 1 | 17.25 |
| RFC 8078 | 2019-10 | 66 | 2 | 17.25 |
| RFC 8078 | 2019-11 | 120 | 2 | 17.25 |
| RFC 8078 | 2019-12 | 124 | 2 | 17.25 |
| RFC 8078 | 2020-01 | 124 | 2 | 17.25 |
| RFC 8078 | 2020-02 | 124 | 3 | 17.25 |
| RFC 8078 | 2020-03 | 246 | 4 | 17.25 |
| RFC 8078 | 2020-04 | 240 | 4 | 17.25 |
| RFC 8078 | 2020-05 | 248 | 4 | 17.25 |
| RFC 8078 | 2020-06 | 292 | 5 | 17.25 |
| RFC 8078 | 2020-07 | 310 | 5 | 17.25 |
| RFC 8078 | 2020-08 | 408 | 9 | 17.25 |
| RFC 8078 | 2020-09 | 74 | 10 | 17.25 |
| RFC 8078 | 2021-01 | 9270 | 325 | 17.25 |
| RFC 8078 | 2021-02 | 4148 | 78 | 17.25 |
| RFC 8078 | 2021-03 | 4762 | 82 | 17.25 |
| RFC 8078 | 2021-04 | 4406 | 80 | 17.25 |
| RFC 8078 | 2021-05 | 4306 | 84 | 17.25 |
| RFC 8078 | 2021-06 | 4574 | 84 | 17.25 |
| RFC 8078 | 2021-07 | 4918 | 85 | 17.25 |
| RFC 8078 | 2021-08 | 5134 | 88 | 17.25 |
| RFC 8078 | 2021-09 | 5136 | 86 | 17.25 |
| RFC 8078 | 2021-10 | 5342 | 89 | 17.25 |
| RFC 8078 | 2021-11 | 5382 | 95 | 17.25 |
| RFC 8078 | 2021-12 | 5864 | 97 | 17.25 |
| RFC 8078 | 2023-01 | 3722 | 101 | 17.25 |
| RFC 8078 | 2023-02 | 1262 | 23 | 17.25 |
| RFC 8078 | 2023-03 | 1396 | 23 | 17.25 |
| RFC 8078 | 2023-04 | 1326 | 23 | 17.25 |
| RFC 8078 | 2023-05 | 1561 | 27 | 17.25 |
| RFC 8078 | 2023-06 | 1748 | 29 | 17.25 |
| RFC 8078 | 2023-07 | 1972 | 27 | 17.25 |
| RFC 8078 | 2023-08 | 2032 | 30 | 17.25 |
| RFC 8078 | 2023-09 | 2220 | 34 | 17.25 |
| RFC 8078 | 2023-10 | 2438 | 37 | 17.25 |
| RFC 8078 | 2023-11 | 2438 | 39 | 17.25 |
| RFC 8078 | 2023-12 | 2662 | 45 | 17.25 |
| RFC 8078 | 2024-01 | 8580 | 143 | 17.25 |
| RFC 8078 | 2024-02 | 8414 | 149 | 17.25 |
| RFC 8078 | 2024-03 | 3648 | 153 | 17.25 |
| RFC 8078 | 2024-04 | 3046 | 52 | 17.25 |
| RFC 8078 | 2024-05 | 3244 | 54 | 17.25 |
| RFC 8078 | 2024-06 | 3192 | 56 | 17.25 |
| RFC 8078 | 2024-07 | 3310 | 56 | 17.25 |
| RFC 8078 | 2024-08 | 3466 | 58 | 17.25 |
| RFC 8078 | 2024-09 | 4088 | 60 | 17.25 |
| RFC 8078 | 2024-10 | 7390 | 58 | 17.25 |
| RFC 8078 | 2024-11 | 2738 | 58 | 17.25 |
| RFC 8078 | 2024-12 | 3604 | 61 | 17.25 |
| RFC 8078 | 2026-01 | 4554 | 75 | 17.25 |
| RFC 8078 | 2026-02 | 4220 | 78 | 17.25 |
| RFC 8078 | 2026-03 | 4964 | 81 | 17.25 |
| RFC 8078 | 2026-04 | 4784 | 81 | 17.25 |
| RFC 8624 | 2019-06 | 51118 | 395 | 3.375 |
| RFC 8624 | 2019-07 | 54234 | 385 | 3.375 |
| RFC 8624 | 2019-08 | 56472 | 422 | 3.375 |
| RFC 8624 | 2019-09 | 58880 | 477 | 3.375 |
| RFC 8624 | 2019-10 | 66755 | 534 | 3.375 |
| RFC 8624 | 2019-11 | 71892 | 537 | 3.375 |
| RFC 8624 | 2019-12 | 76110 | 537 | 3.375 |
| RFC 8624 | 2020-01 | 78582 | 563 | 3.375 |
| RFC 8624 | 2020-02 | 76067 | 563 | 3.375 |
| RFC 8624 | 2020-03 | 83961 | 605 | 3.375 |
| RFC 8624 | 2020-04 | 93423 | 605 | 3.375 |
| RFC 8624 | 2020-05 | 98679 | 605 | 3.375 |
| RFC 8624 | 2020-06 | 99569 | 749 | 3.375 |
| RFC 8624 | 2020-07 | 111735 | 800 | 3.375 |
| RFC 8624 | 2020-08 | 115164 | 854 | 3.375 |
| RFC 8624 | 2020-09 | 15104 | 854 | 3.375 |
| RFC 8624 | 2021-01 | 87316023 | 1217448 | 3.375 |
| RFC 8624 | 2021-02 | 24071338 | 257978 | 3.375 |
| RFC 8624 | 2021-03 | 26764670 | 256700 | 3.375 |
| RFC 8624 | 2021-04 | 25816169 | 260779 | 3.375 |
| RFC 8624 | 2021-05 | 25727735 | 260666 | 3.375 |
| RFC 8624 | 2021-06 | 25779150 | 266416 | 3.375 |
| RFC 8624 | 2021-07 | 26709161 | 260640 | 3.375 |
| RFC 8624 | 2021-08 | 29536619 | 266170 | 3.375 |
| RFC 8624 | 2021-09 | 28758361 | 268047 | 3.375 |
| RFC 8624 | 2021-10 | 29810232 | 268054 | 3.375 |
| RFC 8624 | 2021-11 | 29401020 | 273611 | 3.375 |
| RFC 8624 | 2021-12 | 30188808 | 273680 | 3.375 |
| RFC 8624 | 2023-01 | 17348227 | 344500 | 3.375 |
| RFC 8624 | 2023-02 | 300642 | 2718 | 3.375 |
| RFC 8624 | 2023-03 | 339568 | 2825 | 3.375 |
| RFC 8624 | 2023-04 | 339709 | 2912 | 3.375 |
| RFC 8624 | 2023-05 | 370856 | 2949 | 3.375 |
| RFC 8624 | 2023-06 | 399604 | 3180 | 3.375 |
| RFC 8624 | 2023-07 | 435013 | 3394 | 3.375 |
| RFC 8624 | 2023-08 | 427498 | 3570 | 3.375 |
| RFC 8624 | 2023-09 | 437498 | 3962 | 3.375 |
| RFC 8624 | 2023-10 | 463668 | 4538 | 3.375 |
| RFC 8624 | 2023-11 | 463405 | 4636 | 3.375 |
| RFC 8624 | 2023-12 | 488710 | 4797 | 3.375 |
| RFC 8624 | 2024-01 | 35225583 | 310675 | 3.375 |
| RFC 8624 | 2024-02 | 32917147 | 310622 | 3.375 |
| RFC 8624 | 2024-03 | 3890964 | 307932 | 3.375 |
| RFC 8624 | 2024-04 | 548825 | 4974 | 3.375 |
| RFC 8624 | 2024-05 | 611995 | 6072 | 3.375 |
| RFC 8624 | 2024-06 | 637588 | 6072 | 3.375 |
| RFC 8624 | 2024-07 | 645590 | 6602 | 3.375 |
| RFC 8624 | 2024-08 | 683169 | 6780 | 3.375 |
| RFC 8624 | 2024-09 | 792014 | 6780 | 3.375 |
| RFC 8624 | 2024-10 | 1434542 | 6967 | 3.375 |
| RFC 8624 | 2024-11 | 547764 | 6967 | 3.375 |
| RFC 8624 | 2024-12 | 698755 | 7165 | 3.375 |
| RFC 8624 | 2026-01 | 907739 | 8196 | 3.375 |
| RFC 8624 | 2026-02 | 837137 | 8468 | 3.375 |
| RFC 8624 | 2026-03 | 950844 | 8468 | 3.375 |
| RFC 8624 | 2026-04 | 905701 | 8839 | 3.375 |
| RFC 8080 | 2021-01 | 5473847 | 53365 | 17.25 |
| RFC 8080 | 2021-02 | 480612 | 3692 | 17.25 |
| RFC 8080 | 2021-03 | 464182 | 3692 | 17.25 |
| RFC 8080 | 2021-04 | 165876 | 2808 | 17.25 |
| RFC 8080 | 2021-05 | 2646 | 51 | 17.25 |
| RFC 8080 | 2021-06 | 659 | 6 | 17.25 |
| RFC 8080 | 2021-07 | 465 | 4 | 17.25 |
| RFC 8080 | 2021-08 | 465 | 4 | 17.25 |
| RFC 8080 | 2021-09 | 450 | 4 | 17.25 |
| RFC 8080 | 2021-10 | 496 | 4 | 17.25 |
| RFC 8080 | 2021-11 | 480 | 4 | 17.25 |
| RFC 8080 | 2021-12 | 496 | 4 | 17.25 |
| RFC 8080 | 2023-01 | 48237 | 1323 | 17.25 |
| RFC 8080 | 2024-01 | 1655 | 7 | 17.25 |
| RFC 8080 | 2024-02 | 1537 | 7 | 17.25 |
| RFC 8080 | 2024-03 | 159 | 7 | 17.25 |
| RFC 8080 | 2024-10 | 34 | 1 | 17.25 |
| RFC 8080 | 2024-11 | 7 | 1 | 17.25 |

## 10. Impossible Timestamp Matches

An observation that predates the RFC it appears to match cannot be evidence of that RFC. The indicator conditions may have passed, but the match is rejected outright, its score is forfeited to zero, and it is sent to the review queue rather than quietly dropped.

| Signal | RFC | Observed | RFC published | Forfeited score | Matched indicators |
| --- | --- | --- | --- | --- | --- |
| sig_0001 | RFC 8624 | 2018-01-04 | 2019-06-01 | 3.375 | rfc8624_avoids_deprecated_algorithm, rfc8624_recommended_signing_algori... |
| sig_0006 | RFC 8624 | 2018-01-18 | 2019-06-01 | 3.375 | rfc8624_avoids_deprecated_algorithm, rfc8624_recommended_signing_algori... |
| sig_0013 | RFC 8624 | 2019-04-21 | 2019-06-01 | 3.375 | rfc8624_avoids_deprecated_algorithm, rfc8624_recommended_signing_algori... |

The forfeited score is what the match would have scored had the observation been dated after publication. It is recorded so that a reviewer can see how strong the rejected evidence was: a large forfeited score usually means the mechanism predates its own standardization, which is common - the RFC often documents existing practice - or that the checklist attributes the indicator to the wrong document.

## 11. Partial / Ambiguous Matches

A partial match means some but not all required indicators were satisfied. An ambiguous match means the evidence fits, but the same observation is equally explained by another RFC. Neither is reported as adoption.

| Signal | RFC | Decision | Score | Missing fields | Why |
| --- | --- | --- | --- | --- | --- |
| sig_0002 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0002: the optional indicator rfc4... |
| sig_0003 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0003: the optional indicator rfc4... |
| sig_0004 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0004: the optional indicator rfc8... |
| sig_0005 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0005: the optional indicator rfc8... |
| sig_0007 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0007: the optional indicator rfc8... |
| sig_0008 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0008: the optional indicator rfc8... |
| sig_0009 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0009: the optional indicator rfc8... |
| sig_0010 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0010: the optional indicator rfc8... |
| sig_0011 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0011: the optional indicator rfc4... |
| sig_0012 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0012: the optional indicator rfc4... |
| sig_0012 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0012: the optional indicator rfc8... |
| sig_0013 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0013: the optional indicator rfc4... |
| sig_0014 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0014: the required indica... |
| sig_0015 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0015: the required indica... |
| sig_0016 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0016: the required indica... |
| sig_0017 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0017: the required indica... |
| sig_0018 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0018: the required indica... |
| sig_0019 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0019: the required indica... |
| sig_0020 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0020: the optional indicator rfc4... |
| sig_0020 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0020: the optional indicator rfc8... |
| sig_0021 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0021: the optional indicator rfc4... |
| sig_0021 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0021: the optional indicator rfc8... |
| sig_0022 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0022: the optional indicator rfc8... |
| sig_0023 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0023: the optional indicator rfc4... |
| sig_0023 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0023: the optional indicator rfc8... |
| sig_0024 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0024: the required indica... |
| sig_0025 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0025: the required indica... |
| sig_0026 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0026: the required indica... |
| sig_0026 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0026: the optional indicator rfc4... |
| sig_0027 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0027: the required indica... |
| sig_0027 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0027: the optional indicator rfc4... |
| sig_0028 | RFC 8624 | ambiguous | 3.375 | rr_type, validator_algorithm_support | RFC 8624 is an ambiguous match for signal sig_0028: the required indica... |
| sig_0028 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0028: the optional indicator rfc4... |
| sig_0029 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0029: the optional indicator rfc4... |
| sig_0029 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0029: the optional indicator rfc8... |

A missing field is not a failed condition: it means the corpus did not carry the value, so the condition could not be tested at all.

## 12. Review Queue

The review queue collects everything the pipeline is not entitled to decide on its own.

By severity:

| Severity | Items | Share |
| --- | --- | --- |
| high | 2 | 6.5% |
| medium | 13 | 41.9% |
| low | 16 | 51.6% |

By type:

| Item type | Items | Share |
| --- | --- | --- |
| schema_inconsistency | 16 | 51.6% |
| close_ranking | 5 | 16.1% |
| ambiguous_indicator | 2 | 6.5% |
| llm_review_recommended | 2 | 6.5% |
| partial_match | 2 | 6.5% |
| missing_required_field | 1 | 3.2% |
| non_queryable_indicator | 1 | 3.2% |
| partially_queryable_indicator | 1 | 3.2% |
| timestamp_invalid_match | 1 | 3.2% |

| Item | Type | Severity | RFCs | Reason | Suggested action |
| --- | --- | --- | --- | --- | --- |
| rev_0001 | non_queryable_indicator | high | RFC 8624 | Indicator rfc8624_validator_algorithm_support (optional, weight 6.0) of... | Add `validator_algorithm_support` to the OpenINTEL analysis dictionary... |
| rev_0002 | timestamp_invalid_match | high | RFC 4033, RFC 4509, RFC 6605, RFC 7344, RFC 8078, RFC 8624 | 10 observation(s) matched RFC 8624 indicator(s) rfc8624_avoids_deprecat... | Verify the RFC 8624 publication_date 2019-06-01T00:00:00 in the checkli... |
| rev_0003 | ambiguous_indicator | medium | RFC 6605, RFC 8080, RFC 8624 | Indicator rfc8624_avoids_deprecated_algorithm of RFC 8624 is ambiguous... | Decide attribution by hand for signal(s) sig_0004, sig_0005, sig_0007,... |
| rev_0004 | ambiguous_indicator | medium | RFC 6605, RFC 8080, RFC 8624 | Indicator rfc8624_recommended_signing_algorithm of RFC 8624 is ambiguou... | Decide attribution by hand for signal(s) sig_0014, sig_0015, sig_0016,... |
| rev_0005 | close_ranking | medium | RFC 4033, RFC 8624 | RFC 4033 (score 3.75) and RFC 8624 (score 3.375) differ by 10.0%, insid... | Do not report RFC 4033 as the single best match. Compare the distinguis... |
| rev_0006 | close_ranking | medium | RFC 4509, RFC 7344 | RFC 7344 (score 13.125) and RFC 4509 (score 11.25) differ by 14.29%, in... | Do not report RFC 7344 as the single best match. Compare the distinguis... |
| rev_0007 | close_ranking | medium | RFC 5155, RFC 8080 | RFC 5155 (score 17.25) and RFC 8080 (score 17.25) differ by 0.0%, insid... | Do not report RFC 5155 as the single best match. Compare the distinguis... |
| rev_0008 | close_ranking | medium | RFC 6605, RFC 7344 | RFC 6605 (score 13.125) and RFC 7344 (score 13.125) differ by 0.0%, ins... | Do not report RFC 6605 as the single best match. Compare the distinguis... |
| rev_0009 | close_ranking | medium | RFC 8078, RFC 8080 | RFC 8080 (score 17.25) and RFC 8078 (score 17.25) differ by 0.0%, insid... | Do not report RFC 8080 as the single best match. Compare the distinguis... |
| rev_0010 | llm_review_recommended | medium | RFC 4033 | The deterministic verifier returned needs_manual_review for 29 trace(s)... | Open trace(s) trace_sig_0001_rfc4033, trace_sig_0002_rfc4033, trace_sig... |
| rev_0011 | llm_review_recommended | medium | RFC 8624 | The deterministic verifier returned needs_manual_review for 16 trace(s)... | Open trace(s) trace_sig_0014_rfc8624, trace_sig_0015_rfc8624, trace_sig... |
| rev_0012 | missing_required_field | medium | RFC 4509 | Field `digest_type`, needed by required indicator(s) rfc4509_ds_sha256_... | Confirm the Parquet reader resolves `digest_type` for these rows (`dige... |
| rev_0013 | partial_match | medium | RFC 4033 | RFC 4033 matched partially on 12 observation(s): indicator(s) rfc4033_d... | Confirm the Parquet reader resolves the missing field(s) for these rows... |
| rev_0014 | partial_match | medium | RFC 8624 | RFC 8624 matched partially on 12 observation(s): indicator(s) rfc8624_a... | Confirm the Parquet reader resolves the missing field(s) for these rows... |
| rev_0015 | partially_queryable_indicator | medium | RFC 4033 | Indicator rfc4033_dnssec_ok_negotiated (optional, weight 3.0) of RFC 40... | Add `dnssec_ok_flag` to the OpenINTEL analysis dictionary with an openi... |
| rev_0016 | schema_inconsistency | low | - | Field 'dnssec_ok_flag' is referenced by 1 indicator(s) (rfc4033_dnssec_... | Resolve this warning before quoting counts from this run: it did not st... |
| rev_0017 | schema_inconsistency | low | - | Field 'validator_algorithm_support' is referenced by 1 indicator(s) (rf... | Resolve this warning before quoting counts from this run: it did not st... |
| rev_0018 | schema_inconsistency | low | - | Dictionary fields `domain` (from 2010-01-01), `flags` (from 2016-01-01)... | The dictionary marks `domain` from 2010-01-01T00:00:00; `flags` from 20... |
| rev_0019 | schema_inconsistency | low | - | Dictionary field 'measurement_id' lists no openintel_native_fields, so... | Re-check the dictionary entry for `measurement_id` (type, nullability a... |
| rev_0020 | schema_inconsistency | low | RFC 4033 | rfc4033_dnssec_algorithm_present: Field `algorithm` is only available f... | The dictionary marks `algorithm` from 2010-01-01T00:00:00. Either restr... |
| rev_0021 | schema_inconsistency | low | RFC 4033 | RFC 4033 was published 2005-03-01, but the OpenINTEL fields its indicat... | The dictionary marks `algorithm` from 2010-01-01T00:00:00; `rr_type` fr... |
| rev_0022 | schema_inconsistency | low | RFC 4033 | rfc4033_base_dnssec_record_present: Field `rr_type` is only available f... | The dictionary marks `rr_type` from 2010-01-01T00:00:00. Either restric... |
| rev_0023 | schema_inconsistency | low | RFC 4033, RFC 4034 | RFC 4033 lists related RFC 'RFC 4034', which is not defined in this che... | Resolve this warning before quoting counts from this run: it did not st... |
| rev_0024 | schema_inconsistency | low | RFC 4033, RFC 4035 | RFC 4033 lists related RFC 'RFC 4035', which is not defined in this che... | Resolve this warning before quoting counts from this run: it did not st... |
| rev_0025 | schema_inconsistency | low | RFC 4509 | rfc4509_ds_sha256_digest: Field `digest_type` is only available from 20... | The dictionary marks `digest_type` from 2010-01-01T00:00:00. Either res... |

6 further items are in `review_queue.json`.

## 13. Limitations

This pipeline does not prove RFC adoption by itself. It identifies ranked RFC candidates based on OpenINTEL-observable signals and timestamp consistency.

- **Synthetic sample data.** The measurements in this run come from a small generated sample corpus built to exercise the matching rules, not from a production OpenINTEL measurement. Absolute counts and first-seen dates carry no external meaning.
- **A single Parquet file.** One file is one slice of one measurement campaign. It cannot support statements about global deployment, and an RFC absent from these results may simply be absent from this file.
- **Record-level, not zone-level.** Each observation is one resource record. The pipeline never aggregates records into a zone-level verdict, so a zone that publishes many records is over-represented relative to one that publishes few, and per-zone policy claims (such as "this zone avoids deprecated algorithms") cannot be made from a single record.
- **Indicators the corpus cannot express.** 1 indicator (rfc8624_validator_algorithm_support) references fields that do not exist in the OpenINTEL dictionary, typically resolver-side behaviour. They are neither confirmed nor refuted here.
- **Broad base-DNSSEC RFCs match almost any signed zone.** RFC 4033 and its companions are matched by the presence of any DNSSEC record, so they will match nearly every signed zone regardless of what else the operator has deployed. Their low specificity multiplier deliberately keeps them below mechanism-specific RFCs (affected here: RFC 4033); a match on them should be read as "this zone is signed", not as adoption of a specific mechanism.
- **Ambiguity is structural, not incidental.** Recommendation documents such as RFC 8624 register nothing observable of their own. Any match against them is an inference about operator policy drawn from algorithm choice, which is why those indicators are marked ambiguous and penalized.
- **Timestamps bound possibility, not causation.** An observation dated after publication is consistent with the RFC; it does not show the operator acted because of the RFC, and many mechanisms were deployed before the document that describes them was published.

## 14. Next Steps

- Resolve the 10 warning(s) recorded in `run_manifest.json`; each one marks a place where the run degraded rather than failed.
- Run the pipeline against a real OpenINTEL Parquet partition rather than the sample corpus, and compare the ranking to the sample result to confirm nothing depends on the generated data.
- Aggregate observations to zone level before ranking, so that adoption is counted once per zone instead of once per record.
- Work through the review queue: the timestamp-invalid matches and the missing-required-field partials are the items most likely to indicate a checklist error rather than a data artefact.
- Extend the OpenINTEL dictionary, or drop the indicators that depend on fields it cannot supply, so the checklist states only what this data source can be asked.
- Add RFC obsoletes/updates relationships to the ranking so that a superseded document does not compete with the one that replaced it.
- Validate a sample of the top-ranked candidates against zone data or operator statements; that is the step this pipeline is explicitly not a substitute for.

## Appendix A. Warnings

- RFC 4033 lists related RFC 'RFC 4034', which is not defined in this checklist database; the relationship cannot be resolved or ranked against.
- RFC 4033 lists related RFC 'RFC 4035', which is not defined in this checklist database; the relationship cannot be resolved or ranked against.
- Dictionary field 'measurement_id' lists no openintel_native_fields, so the Parquet reader has no real OpenINTEL column to resolve it from; it will only be populated if a column of exactly that name exists.
- Field 'dnssec_ok_flag' is referenced by 1 indicator(s) (rfc4033_dnssec_ok_negotiated) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'validator_algorithm_support' is referenced by 1 indicator(s) (rfc8624_validator_algorithm_support) but is not defined in the OpenINTEL dictionary loaded from E:/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Indicator rfc8624_validator_algorithm_support of RFC 8624 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc8624_validator_algorithm_support is non-queryable: the field carrying its discriminating value, validator_algorithm_support, is absent from the OpenINTEL dictionary, and the only field that remains, rr_type (string), merely scopes which records are considered and is not used by any other RFC 8624 indicator, so nothing testable is left to attribute an observation to RFC 8624.
- RFC 4033 was published 2005-03-01, but the OpenINTEL fields its indicators rely on only become available later: `algorithm` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 4033 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- RFC 4509 was published 2006-05-01, but the OpenINTEL fields its indicators rely on only become available later: `digest_type` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 4509 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- RFC 5155 was published 2008-03-01, but the OpenINTEL fields its indicators rely on only become available later: `algorithm` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 5155 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- Dictionary fields `domain` (from 2010-01-01), `flags` (from 2016-01-01), `key_tag` (from 2010-01-01), `measurement_id` (from 2010-01-01), `source` (from 2010-01-01), `timestamp` (from 2010-01-01), `zone` (from 2010-01-01) become available after the earliest RFC in this checklist was published. No indicator references them today, but any future indicator built on them will inherit that lower bound.
