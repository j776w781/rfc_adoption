# OpenINTEL RFC Adoption Analysis

Generated: 2026-07-30T01:03:33  
Pipeline: openintel-rfc-adoption-matcher 0.1.0  
Observation window: 2018-05-01 to 2018-05-01

This report identifies ranked RFC candidates that are consistent with the observed OpenINTEL signals. Read Section 13 before quoting any number from it.

## 1. Executive Summary

This run evaluated 2,621,052 OpenINTEL rows across 1 partition against 8 DNSSEC RFCs (17 indicators); 2,621,052 (100.0% of them) reached a rankable decision. That row count is what survived the DNSSEC record-type prefilter, not the size of the partitions: rows of other record types are excluded before any indicator is evaluated, which is what makes a corpus this size tractable. The observation counts in section 7 are exact aggregates over those rows. The 15 observations carried through sections 6 and 8 are a deterministic *sample*, kept so that every aggregate has a worked reasoning trace behind it -- their number is not a measurement of anything. Every score below is derived from record-level observations and the RFC publication date; nothing here is an assertion that an operator deliberately implemented a specification.

The highest-ranked candidate is **RFC 5155** (DNS Security (DNSSEC) Hashed Authenticated Denial of Existence) with score 17.25 (very_high confidence), supported by 408997 observations, first seen 2018-05-01.

- Observation window: 2018-05-01 to 2018-05-01.
- Valid matches: 29; partial: 13; ambiguous: 0; no match: 71.
- Rejected on publication date (impossible timestamps): 7.
- Ranked candidates emitted: 5.
- Review queue: 31 items, 2 of high severity.
- Warnings collected during the run: 14.

## 2. Inputs

| Input | Value |
| --- | --- |
| Checklist database | /mnt/e/Documents/University/year2/DNSSEC/rfc_adoption/data/rfc_checklists/dnssec_rfc_checklists.json |
| OpenINTEL dictionary | /mnt/e/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json |
| Parquet input | basis=zonefile sources=nu 2018-05-01..2018-05-01 partitions=1 |
| Output directory | /mnt/e/Documents/University/year2/DNSSEC/rfc_adoption/output_real |
| Parquet engine | duckdb |
| Row limit | none |
| Minimum rankable score | 0 |
| Generated at | 2026-07-30T01:03:33 |
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
- Field 'dnssec_ok_flag' is referenced by 1 indicator(s) (rfc4033_dnssec_ok_negotiated) but is not defined in the OpenINTEL dictionary loaded from /mnt/e/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'validator_algorithm_support' is referenced by 1 indicator(s) (rfc8624_validator_algorithm_support) but is not defined in the OpenINTEL dictionary loaded from /mnt/e/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
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

15 observations are shown below. These are a deterministic sample of the 2,621,052 rows scanned, not the corpus: the distributions in this section describe the sample and must not be read as corpus proportions. The exact per-RFC corpus counts are in section 7, covering 2018-05-01 to 2018-05-01.

- Distinct domains: 15.
- Distinct zones: 1.
- Observations carrying an algorithm number: 15.

Resource record types observed:

| Record type | Observations | Share |
| --- | --- | --- |
| DS | 5 | 33.3% |
| CDNSKEY | 3 | 20.0% |
| RRSIG | 3 | 20.0% |
| CDS | 2 | 13.3% |
| NSEC3 | 2 | 13.3% |

DNSSEC algorithm numbers observed:

| Algorithm | Observations | Share |
| --- | --- | --- |
| 13 | 7 | 46.7% |
| 8 | 6 | 40.0% |
| 1 | 2 | 13.3% |

Each row is one record-level observation. A zone that publishes several records appears several times, so observation counts measure records seen, not zones deployed.

## 7. Ranked RFC Matches

| Rank | RFC | Title | Score | Confidence | Supporting observations | First seen |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | RFC 5155 | DNS Security (DNSSEC) Hashed Authenticated Denial of Existence | 17.25 | very_high | 408997 | 2018-05-01 |
| 2 | RFC 6605 | Elliptic Curve Digital Signature Algorithm (DSA) for DNSSEC | 13.125 | very_high | 27631 | 2018-05-01 |
| 3 | RFC 7344 | Automating DNSSEC Delegation Trust Maintenance | 13.125 | very_high | 179 | 2018-05-01 |
| 4 | RFC 4509 | Use of SHA-256 in DNSSEC Delegation Signer (DS) Resource Records | 11.25 | high | 131626 | 2018-05-01 |
| 5 | RFC 4033 | DNS Security Introduction and Requirements (DNSSEC base: RFC 4033/4034/... | 3.75 | low | 2211876 | 2018-05-01 |

Score is the best per-signal score for that RFC, after the specificity multiplier (very_high 1.5, high 1.25, medium 1.0, low 0.75) has been applied. A broad RFC with many observations can therefore rank below a narrow RFC with one unambiguous observation, which is the intended behaviour: specificity is evidence.

Per-candidate evidence breakdown:

| RFC | Best score | Aggregate score | Valid | Partial | Timestamp-invalid | Matched indicators |
| --- | --- | --- | --- | --- | --- | --- |
| RFC 5155 | 17.25 | 34.5 | 408997 | 0 | 0 | rfc5155_nsec3_hash_algorithm, rfc5155_nsec3_record_present |
| RFC 6605 | 13.125 | 91.875 | 27631 | 0 | 0 | rfc6605_ecdsa_algorithm, rfc6605_ecdsa_on_key_or_signature |
| RFC 7344 | 13.125 | 60 | 179 | 0 | 0 | rfc7344_cds_cdnskey_present, rfc7344_cds_publishes_digest |
| RFC 4509 | 11.25 | 78.75 | 131626 | 0 | 0 | rfc4509_ds_sha256_digest |
| RFC 4033 | 3.75 | 30 | 2211876 | 409176 | 0 | rfc4033_base_dnssec_record_present, rfc4033_dnssec_algorithm_present |

## 8. Reasoning Summary

Every one of the 120 signal-by-RFC evaluations carries a stored reasoning trace: the conditions that passed, the conditions that failed, the fields that were missing, the timestamp verdict and the arithmetic of the score. Non-matches are traced too, because the reason an RFC was *not* selected is as much a result as the reason one was.

| Decision | Traces | Share |
| --- | --- | --- |
| no_match | 71 | 59.2% |
| valid_match | 29 | 24.2% |
| partial_match | 13 | 10.8% |
| timestamp_invalid | 7 | 5.8% |

Verbatim reasoning summaries from this run:

**trace_sig_0006_rfc5155** - RFC 5155, signal `sig_0006`, decision `valid_match`, score 17.25:

> RFC 5155 matched signal sig_0006: the required indicator rfc5155_nsec3_record_present passed because rr_type=NSEC3 is in [NSEC3, NSEC3PARAM]. Corroborating indicators also matched: rfc5155_nsec3_hash_algorithm. The observation on 2018-05-01T02:12:41 is 3713 days after RFC 5155's publication on 2008-03-01, so the timestamp is valid. Score 17.25 (very_high) = (10.0 required + 1.5 optional) x 1.5 very_high specificity.

**trace_sig_0012_rfc8624** - RFC 8624, signal `sig_0012`, decision `timestamp_invalid`, score 0.0:

> RFC 8624 cannot explain signal sig_0012: although algorithm=13 satisfy the required indicator rfc8624_recommended_signing_algorithm, the observation on 2018-05-01T04:41:02 predates RFC 8624's publication on 2019-06-01 by 396 days. An observation cannot evidence adoption of an RFC that did not yet exist, so the score of 3.375 is forfeited and this is routed to the review queue. The withheld score derives from (5.0 required + 1.5 optional - 2.0 ambiguity penalty) x 0.75 low specificity.

**trace_sig_0015_rfc8624** - RFC 8624, signal `sig_0015`, decision `partial_match`, score 0.0:

> RFC 8624 partially matches signal sig_0015: the optional indicator rfc8624_avoids_deprecated_algorithm passed because algorithm is present (observed 8) and algorithm=8 differs from 1 as required. The required indicator rfc8624_recommended_signing_algorithm was not satisfied: algorithm=8 is not in [13, 15]. The observation on 2018-05-01T05:21:19 predates RFC 8624's publication on 2019-06-01 by 396 days. An observation cannot evidence adoption of an RFC that did not yet exist, so the score is forfeited. Score 0.0 (none): the penalties leave a raw total of -3.5, which is clamped to 0 before the 0.75 low specificity multiplier.

## 9. First-Seen Dates / Adoption Timeline

First-seen is the earliest *valid* match: an observation dated at or after the RFC's publication date. It is the first date this corpus saw the mechanism, which is an upper bound on when deployment began and says nothing about deployment before the measurement window.

| RFC | Published | First seen | Last seen | Days from publication | Observations | Distinct domains |
| --- | --- | --- | --- | --- | --- | --- |
| RFC 4033 | 2005-03-01 | 2018-05-01 | 2018-05-01 | 4809 | 2211876 | 517471 |
| RFC 4509 | 2006-05-01 | 2018-05-01 | 2018-05-01 | 4383 | 131626 | 115019 |
| RFC 5155 | 2008-03-01 | 2018-05-01 | 2018-05-01 | 3713 | 408997 | 281985 |
| RFC 6605 | 2012-04-01 | 2018-05-01 | 2018-05-01 | 2221 | 27631 | 5532 |
| RFC 7344 | 2014-09-01 | 2018-05-01 | 2018-05-01 | 1338 | 179 | 100 |
| RFC 8078 | 2017-03-01 | - | - | - | 0 | 0 |
| RFC 8080 | 2017-02-01 | - | - | - | 0 | 0 |
| RFC 8624 | 2019-06-01 | - | - | - | 0 | 0 |

Monthly observation buckets (valid matches only):

| RFC | Period | Observations | Domains | Mean score |
| --- | --- | --- | --- | --- |
| RFC 4033 | 2018-05 | 2211876 | 517471 | 3.75 |
| RFC 4509 | 2018-05 | 131626 | 115019 | 11.25 |
| RFC 5155 | 2018-05 | 408997 | 281985 | 17.25 |
| RFC 6605 | 2018-05 | 27631 | 5532 | 13.125 |
| RFC 7344 | 2018-05 | 179 | 100 | 13.125 |

## 10. Impossible Timestamp Matches

An observation that predates the RFC it appears to match cannot be evidence of that RFC. The indicator conditions may have passed, but the match is rejected outright, its score is forfeited to zero, and it is sent to the review queue rather than quietly dropped.

| Signal | RFC | Observed | RFC published | Forfeited score | Matched indicators |
| --- | --- | --- | --- | --- | --- |
| sig_0001 | RFC 8624 | 2018-05-01 | 2019-06-01 | 3.375 | rfc8624_avoids_deprecated_algorithm, rfc8624_recommended_signing_algori... |
| sig_0004 | RFC 8624 | 2018-05-01 | 2019-06-01 | 3.375 | rfc8624_avoids_deprecated_algorithm, rfc8624_recommended_signing_algori... |
| sig_0007 | RFC 8624 | 2018-05-01 | 2019-06-01 | 3.375 | rfc8624_avoids_deprecated_algorithm, rfc8624_recommended_signing_algori... |
| sig_0008 | RFC 8624 | 2018-05-01 | 2019-06-01 | 3.375 | rfc8624_avoids_deprecated_algorithm, rfc8624_recommended_signing_algori... |
| sig_0009 | RFC 8624 | 2018-05-01 | 2019-06-01 | 3.375 | rfc8624_avoids_deprecated_algorithm, rfc8624_recommended_signing_algori... |
| sig_0010 | RFC 8624 | 2018-05-01 | 2019-06-01 | 3.375 | rfc8624_avoids_deprecated_algorithm, rfc8624_recommended_signing_algori... |
| sig_0012 | RFC 8624 | 2018-05-01 | 2019-06-01 | 3.375 | rfc8624_avoids_deprecated_algorithm, rfc8624_recommended_signing_algori... |

The forfeited score is what the match would have scored had the observation been dated after publication. It is recorded so that a reviewer can see how strong the rejected evidence was: a large forfeited score usually means the mechanism predates its own standardization, which is common - the RFC often documents existing practice - or that the checklist attributes the indicator to the wrong document.

## 11. Partial / Ambiguous Matches

A partial match means some but not all required indicators were satisfied. An ambiguous match means the evidence fits, but the same observation is equally explained by another RFC. Neither is reported as adoption.

| Signal | RFC | Decision | Score | Missing fields | Why |
| --- | --- | --- | --- | --- | --- |
| sig_0001 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0001: the optional indicator rfc4... |
| sig_0002 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0002: the optional indicator rfc8... |
| sig_0003 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0003: the optional indicator rfc8... |
| sig_0004 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0004: the optional indicator rfc4... |
| sig_0005 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0005: the optional indicator rfc4... |
| sig_0006 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0006: the optional indicator rfc4... |
| sig_0007 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0007: the optional indicator rfc4... |
| sig_0010 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0010: the optional indicator rfc4... |
| sig_0011 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0011: the optional indicator rfc8... |
| sig_0012 | RFC 4033 | partial_match | 0 | dnssec_ok_flag | RFC 4033 partially matches signal sig_0012: the optional indicator rfc4... |
| sig_0013 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0013: the optional indicator rfc8... |
| sig_0014 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0014: the optional indicator rfc8... |
| sig_0015 | RFC 8624 | partial_match | 0 | rr_type, validator_algorithm_support | RFC 8624 partially matches signal sig_0015: the optional indicator rfc8... |

A missing field is not a failed condition: it means the corpus did not carry the value, so the condition could not be tested at all.

## 12. Review Queue

The review queue collects everything the pipeline is not entitled to decide on its own.

By severity:

| Severity | Items | Share |
| --- | --- | --- |
| high | 2 | 6.5% |
| medium | 9 | 29.0% |
| low | 20 | 64.5% |

By type:

| Item type | Items | Share |
| --- | --- | --- |
| schema_inconsistency | 20 | 64.5% |
| ambiguous_indicator | 2 | 6.5% |
| close_ranking | 2 | 6.5% |
| partial_match | 2 | 6.5% |
| llm_review_recommended | 1 | 3.2% |
| missing_required_field | 1 | 3.2% |
| non_queryable_indicator | 1 | 3.2% |
| partially_queryable_indicator | 1 | 3.2% |
| timestamp_invalid_match | 1 | 3.2% |

| Item | Type | Severity | RFCs | Reason | Suggested action |
| --- | --- | --- | --- | --- | --- |
| rev_0001 | non_queryable_indicator | high | RFC 8624 | Indicator rfc8624_validator_algorithm_support (optional, weight 6.0) of... | Add `validator_algorithm_support` to the OpenINTEL analysis dictionary... |
| rev_0002 | timestamp_invalid_match | high | RFC 4033, RFC 4509, RFC 6605, RFC 7344, RFC 8624 | 13 observation(s) matched RFC 8624 indicator(s) rfc8624_avoids_deprecat... | Verify the RFC 8624 publication_date 2019-06-01T00:00:00 in the checkli... |
| rev_0003 | ambiguous_indicator | medium | RFC 6605, RFC 8080, RFC 8624 | Indicator rfc8624_avoids_deprecated_algorithm of RFC 8624 is ambiguous... | Decide attribution by hand for signal(s) sig_0002, sig_0003, sig_0011,... |
| rev_0004 | ambiguous_indicator | medium | RFC 6605, RFC 8080, RFC 8624 | Indicator rfc8624_recommended_signing_algorithm of RFC 8624 is ambiguou... | Decide attribution by hand for signal(s) n/a: the observation is also c... |
| rev_0005 | close_ranking | medium | RFC 4509, RFC 7344 | RFC 7344 (score 13.125) and RFC 4509 (score 11.25) differ by 14.29%, in... | Do not report RFC 7344 as the single best match. Compare the distinguis... |
| rev_0006 | close_ranking | medium | RFC 6605, RFC 7344 | RFC 6605 (score 13.125) and RFC 7344 (score 13.125) differ by 0.0%, ins... | Do not report RFC 6605 as the single best match. Compare the distinguis... |
| rev_0007 | llm_review_recommended | medium | RFC 4033 | The deterministic verifier returned needs_manual_review for 15 trace(s)... | Open trace(s) trace_sig_0001_rfc4033, trace_sig_0002_rfc4033, trace_sig... |
| rev_0008 | missing_required_field | medium | RFC 4509 | Field `digest_type`, needed by required indicator(s) rfc4509_ds_sha256_... | Confirm the Parquet reader resolves `digest_type` for these rows (`dige... |
| rev_0009 | partial_match | medium | RFC 4033 | RFC 4033 matched partially on 7 observation(s): indicator(s) rfc4033_dn... | Confirm the Parquet reader resolves the missing field(s) for these rows... |
| rev_0010 | partial_match | medium | RFC 8624 | RFC 8624 matched partially on 6 observation(s): indicator(s) rfc8624_av... | Confirm the Parquet reader resolves the missing field(s) for these rows... |
| rev_0011 | partially_queryable_indicator | medium | RFC 4033 | Indicator rfc4033_dnssec_ok_negotiated (optional, weight 3.0) of RFC 40... | Add `dnssec_ok_flag` to the OpenINTEL analysis dictionary with an openi... |
| rev_0012 | schema_inconsistency | low | - | Field 'dnssec_ok_flag' is referenced by 1 indicator(s) (rfc4033_dnssec_... | Resolve this warning before quoting counts from this run: it did not st... |
| rev_0013 | schema_inconsistency | low | - | Field 'validator_algorithm_support' is referenced by 1 indicator(s) (rf... | Resolve this warning before quoting counts from this run: it did not st... |
| rev_0014 | schema_inconsistency | low | - | This is an aggregate run over 1 partition(s) and 2621052 scanned row(s)... | Resolve this warning before quoting counts from this run: it did not st... |
| rev_0015 | schema_inconsistency | low | - | Dictionary fields `domain` (from 2010-01-01), `flags` (from 2016-01-01)... | The dictionary marks `domain` from 2010-01-01T00:00:00; `flags` from 20... |
| rev_0016 | schema_inconsistency | low | - | Dictionary field 'measurement_id' lists no openintel_native_fields, so... | Re-check the dictionary entry for `measurement_id` (type, nullability a... |
| rev_0017 | schema_inconsistency | low | - | Rows whose rr_type is not one of CDNSKEY, CDS, DNSKEY, DS, NSEC, NSEC3,... | Re-check the dictionary entry for `rr_type` (type, nullability and open... |
| rev_0018 | schema_inconsistency | low | RFC 4033 | Field 'dnssec_ok_flag' has no column in this corpus but is referenced b... | Resolve this warning before quoting counts from this run: it did not st... |
| rev_0019 | schema_inconsistency | low | RFC 4033 | rfc4033_dnssec_algorithm_present: Field `algorithm` is only available f... | The dictionary marks `algorithm` from 2010-01-01T00:00:00. Either restr... |
| rev_0020 | schema_inconsistency | low | RFC 4033 | RFC 4033 was published 2005-03-01, but the OpenINTEL fields its indicat... | The dictionary marks `algorithm` from 2010-01-01T00:00:00; `rr_type` fr... |
| rev_0021 | schema_inconsistency | low | RFC 4033 | rfc4033_base_dnssec_record_present: Field `rr_type` is only available f... | The dictionary marks `rr_type` from 2010-01-01T00:00:00. Either restric... |
| rev_0022 | schema_inconsistency | low | RFC 4033, RFC 4034 | RFC 4033 lists related RFC 'RFC 4034', which is not defined in this che... | Resolve this warning before quoting counts from this run: it did not st... |
| rev_0023 | schema_inconsistency | low | RFC 4033, RFC 4035 | RFC 4033 lists related RFC 'RFC 4035', which is not defined in this che... | Resolve this warning before quoting counts from this run: it did not st... |
| rev_0024 | schema_inconsistency | low | RFC 4509 | rfc4509_ds_sha256_digest: Field `digest_type` is only available from 20... | The dictionary marks `digest_type` from 2010-01-01T00:00:00. Either res... |
| rev_0025 | schema_inconsistency | low | RFC 4509 | RFC 4509 was published 2006-05-01, but the OpenINTEL fields its indicat... | The dictionary marks `digest_type` from 2010-01-01T00:00:00; `rr_type`... |

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

- Resolve the 14 warning(s) recorded in `run_manifest.json`; each one marks a place where the run degraded rather than failed.
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
- Field 'dnssec_ok_flag' is referenced by 1 indicator(s) (rfc4033_dnssec_ok_negotiated) but is not defined in the OpenINTEL dictionary loaded from /mnt/e/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Field 'validator_algorithm_support' is referenced by 1 indicator(s) (rfc8624_validator_algorithm_support) but is not defined in the OpenINTEL dictionary loaded from /mnt/e/Documents/University/year2/DNSSEC/rfc_adoption/data/openintel_dictionary/sample_openintel_dictionary.json; every condition on it is unanswerable. No similarly named field is defined either.
- Indicator rfc8624_validator_algorithm_support of RFC 8624 is non-queryable against this dictionary and will be skipped during matching: Indicator rfc8624_validator_algorithm_support is non-queryable: the field carrying its discriminating value, validator_algorithm_support, is absent from the OpenINTEL dictionary, and the only field that remains, rr_type (string), merely scopes which records are considered and is not used by any other RFC 8624 indicator, so nothing testable is left to attribute an observation to RFC 8624.
- RFC 4033 was published 2005-03-01, but the OpenINTEL fields its indicators rely on only become available later: `algorithm` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 4033 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- RFC 4509 was published 2006-05-01, but the OpenINTEL fields its indicators rely on only become available later: `digest_type` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 4509 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- RFC 5155 was published 2008-03-01, but the OpenINTEL fields its indicators rely on only become available later: `algorithm` (from 2010-01-01), `rr_type` (from 2010-01-01). Adoption of RFC 5155 before 2010-01-01 cannot be observed through this corpus, so a first-seen date is a lower bound on when the mechanism appeared, not on when it was adopted.
- Dictionary fields `domain` (from 2010-01-01), `flags` (from 2016-01-01), `key_tag` (from 2010-01-01), `measurement_id` (from 2010-01-01), `source` (from 2010-01-01), `timestamp` (from 2010-01-01), `zone` (from 2010-01-01) become available after the earliest RFC in this checklist was published. No indicator references them today, but any future indicator built on them will inherit that lower bound.
- Field 'dnssec_ok_flag' has no column in this corpus but is referenced by 1 evaluable indicator(s) (RFC 4033/rfc4033_dnssec_ok_negotiated); every condition over it compiles to FALSE, so those indicators can never match here.
- Rows whose rr_type is not one of CDNSKEY, CDS, DNSKEY, DS, NSEC, NSEC3, NSEC3PARAM, RRSIG were excluded before any indicator was evaluated. That is what makes the run tractable, and it assumes every DNSSEC observation carries one of those record types; an observation with a null or unexpected rr_type is not counted.
- RFC 8624 has 2152427 partial_match observation(s) in the corpus aggregates but does not appear among the ranked candidates: no sampled exemplar earned a score above the threshold. The aggregate counts are still exact; only the ranking is exemplar-derived.
- This is an aggregate run over 1 partition(s) and 2621052 scanned row(s). observed_signals.json, rfc_matches.json and reasoning_traces.json hold 15 sampled exemplar observation(s), not the corpus: they exist to show that the aggregate counts in ranked_candidates.json and adoption_timeline.json mean what they say. Do not read their length as a measurement.
