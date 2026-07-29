"""Typed data models for the OpenINTEL RFC-adoption matching pipeline.

Every module in this package exchanges data using these models. They are the
single source of truth for the on-disk JSON layout produced by the CLI and
consumed by the dashboard, so field names here are part of the public contract.

Design notes
------------
* Pydantic v2 is used so that malformed checklist / dictionary files fail loudly
  at load time instead of producing silently wrong matches.
* Every model that represents a *decision* carries human-readable explanation
  text alongside the machine-readable fields. Explainability is a first-class
  output of this pipeline, not a debug afterthought.
* All collections are emitted in deterministic order by the modules that build
  them, so repeated runs over the same input produce byte-identical output.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ConditionOp",
    "Specificity",
    "Queryability",
    "Decision",
    "Confidence",
    "Severity",
    "ReviewStatus",
    "VerificationStatus",
    "IndicatorCondition",
    "RFCIndicator",
    "RFCChecklistEntry",
    "RFCChecklistDB",
    "RFCMetadata",
    "DictionaryField",
    "OpenINTELDictionary",
    "ConditionSchemaCheck",
    "IndicatorSchemaCheck",
    "SchemaCheckReport",
    "ObservedSignal",
    "ConditionEvaluation",
    "IndicatorEvaluation",
    "TimestampCheck",
    "ScoreBreakdown",
    "ReasoningTrace",
    "RFCMatch",
    "RankedRFCCandidate",
    "ReviewItem",
    "TimelineBucket",
    "AdoptionTimelineEntry",
    "LLMVerification",
    "ToolSurveyEntry",
    "ToolSurvey",
    "RunConfig",
    "PipelineResult",
    "SPECIFICITY_MULTIPLIERS",
    "CONFIDENCE_THRESHOLDS",
]


# --------------------------------------------------------------------------- #
# Enumerations (plain Literals: they serialize as strings and stay JSON-clean)
# --------------------------------------------------------------------------- #

ConditionOp = Literal[
    "equals",
    "not_equals",
    "in",
    "exists",
    "contains",
    "greater_or_equal",
    "less_or_equal",
]

Specificity = Literal["very_high", "high", "medium", "low"]

Queryability = Literal["queryable", "partially_queryable", "non_queryable", "ambiguous"]

Decision = Literal[
    "valid_match",
    "partial_match",
    "no_match",
    "timestamp_invalid",
    "non_queryable",
    "ambiguous",
]

Confidence = Literal["very_high", "high", "medium", "low", "none"]

Severity = Literal["high", "medium", "low"]

ReviewStatus = Literal["unresolved", "accepted", "rejected", "needs_follow_up"]

VerificationStatus = Literal["accepted", "rejected", "needs_manual_review"]


#: Ranking multiplier applied to an RFC's raw indicator score.
SPECIFICITY_MULTIPLIERS: dict[str, float] = {
    "very_high": 1.5,
    "high": 1.25,
    "medium": 1.0,
    "low": 0.75,
}

#: Ordered (threshold, label) pairs; first threshold met wins.
CONFIDENCE_THRESHOLDS: tuple[tuple[float, str], ...] = (
    (12.0, "very_high"),
    (8.0, "high"),
    (4.0, "medium"),
    (0.0001, "low"),
)


class _Base(BaseModel):
    """Shared config: reject unknown keys so typos in JSON inputs are caught."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class _Lenient(_Base):
    """For models built from external data where extra keys are tolerated."""

    model_config = ConfigDict(extra="allow", validate_assignment=True)


# --------------------------------------------------------------------------- #
# RFC checklist / signature database
# --------------------------------------------------------------------------- #


class IndicatorCondition(_Base):
    """A single testable predicate over one normalized OpenINTEL field."""

    field: str = Field(description="Normalized OpenINTEL analysis field name.")
    op: ConditionOp = Field(description="Comparison operator.")
    value: Any = Field(default=None, description="Expected value; unused for 'exists'.")
    notes: str | None = None


class RFCIndicator(_Base):
    """An observable signature for one RFC mechanism.

    All conditions must pass for the indicator to be considered matched
    (conditions are ANDed).
    """

    id: str
    description: str
    required: bool = False
    weight: float = Field(default=1.0, ge=0.0)
    ambiguous: bool = Field(
        default=False,
        description="Queryable, but the observation is not uniquely attributable "
        "to this RFC. Routed to the review queue and penalized in ranking.",
    )
    conditions: list[IndicatorCondition] = Field(min_length=1)
    notes: str | None = None

    @property
    def fields_used(self) -> list[str]:
        """Distinct field names referenced by this indicator, in stable order."""
        seen: dict[str, None] = {}
        for condition in self.conditions:
            seen.setdefault(condition.field, None)
        return list(seen)


class RFCChecklistEntry(_Base):
    """One RFC and the set of indicators that evidence its deployment."""

    rfc_id: str
    title: str
    publication_date: datetime
    protocol: str = "DNSSEC"
    specificity: Specificity = "medium"
    description: str = ""
    related_rfc_ids: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    notes: str | None = None
    indicators: list[RFCIndicator] = Field(default_factory=list)

    @property
    def specificity_multiplier(self) -> float:
        return SPECIFICITY_MULTIPLIERS[self.specificity]

    @property
    def required_indicators(self) -> list[RFCIndicator]:
        return [i for i in self.indicators if i.required]

    @property
    def optional_indicators(self) -> list[RFCIndicator]:
        return [i for i in self.indicators if not i.required]


class RFCChecklistDB(_Base):
    """The full checklist database as loaded from JSON."""

    checklist_version: str = "0.0.0"
    description: str = ""
    notes: list[str] = Field(default_factory=list)
    rfcs: list[RFCChecklistEntry] = Field(default_factory=list)

    def get(self, rfc_id: str) -> RFCChecklistEntry | None:
        for entry in self.rfcs:
            if entry.rfc_id == rfc_id:
                return entry
        return None

    @property
    def rfc_ids(self) -> list[str]:
        return [entry.rfc_id for entry in self.rfcs]


class RFCMetadata(_Base):
    """RFC metadata resolved by :mod:`openintel_rfc.rfc_metadata`.

    For the MVP this is derived from the checklist DB itself; the same shape is
    what an IETF Datatracker / RFC Editor backend would populate.
    """

    rfc_id: str
    title: str
    publication_date: datetime
    source: str = Field(
        default="checklist",
        description="Where the metadata came from: 'checklist', 'datatracker', "
        "'rfc_editor_xml', or 'override'.",
    )
    url: str | None = None
    related_rfc_ids: list[str] = Field(default_factory=list)
    notes: str | None = None


# --------------------------------------------------------------------------- #
# OpenINTEL dictionary / schema
# --------------------------------------------------------------------------- #


class DictionaryField(_Base):
    """One field described by the OpenINTEL analysis dictionary."""

    name: str
    type: str
    description: str = ""
    available_from: datetime | None = None
    openintel_native_fields: list[str] = Field(
        default_factory=list,
        description="Real OpenINTEL Parquet column names this analysis field "
        "is derived from; used for alias resolution when reading Parquet.",
    )
    nullable: bool = True


class OpenINTELDictionary(_Base):
    """The dictionary / schema description as loaded from JSON."""

    dictionary_version: str = "0.0.0"
    source: str = ""
    notes: list[str] = Field(default_factory=list)
    fields: list[DictionaryField] = Field(default_factory=list)

    def get(self, name: str) -> DictionaryField | None:
        for field in self.fields:
            if field.name == name:
                return field
        return None

    def has(self, name: str) -> bool:
        return self.get(name) is not None

    @property
    def field_names(self) -> list[str]:
        return [f.name for f in self.fields]


# --------------------------------------------------------------------------- #
# Schema cross-check
# --------------------------------------------------------------------------- #


class ConditionSchemaCheck(_Base):
    """Result of checking one indicator condition against the dictionary."""

    field: str
    op: ConditionOp
    expected: Any = None
    field_exists: bool
    field_type: str | None = None
    available_from: datetime | None = None
    type_compatible: bool = True
    explanation: str


class IndicatorSchemaCheck(_Base):
    """Queryability verdict for one RFC indicator."""

    rfc_id: str
    rfc_title: str
    rfc_publication_date: datetime
    indicator_id: str
    indicator_description: str
    required: bool
    weight: float
    queryability: Queryability
    reasoning: str = Field(
        description="Human-readable justification for the queryability verdict."
    )
    condition_checks: list[ConditionSchemaCheck] = Field(default_factory=list)
    present_fields: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SchemaCheckReport(_Base):
    """Aggregate result of cross-checking every indicator in the checklist DB."""

    generated_at: datetime
    checklist_path: str
    dictionary_path: str
    dictionary_field_count: int
    rfc_count: int
    indicator_count: int
    counts_by_queryability: dict[str, int] = Field(default_factory=dict)
    indicators: list[IndicatorSchemaCheck] = Field(default_factory=list)
    dictionary_fields: list[DictionaryField] = Field(default_factory=list)
    unused_dictionary_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @property
    def queryable_indicators(self) -> list[IndicatorSchemaCheck]:
        return [i for i in self.indicators if i.queryability == "queryable"]

    @property
    def non_queryable_indicators(self) -> list[IndicatorSchemaCheck]:
        return [i for i in self.indicators if i.queryability == "non_queryable"]

    def status_for(self, indicator_id: str) -> Queryability | None:
        for check in self.indicators:
            if check.indicator_id == indicator_id:
                return check.queryability
        return None

    def required_fields(self) -> list[str]:
        """Every dictionary-present field referenced by any indicator."""
        seen: dict[str, None] = {}
        for check in self.indicators:
            for name in check.present_fields:
                seen.setdefault(name, None)
        return sorted(seen)


# --------------------------------------------------------------------------- #
# Observed signals
# --------------------------------------------------------------------------- #


class ObservedSignal(_Base):
    """One normalized DNS/DNSSEC observation extracted from Parquet."""

    signal_id: str
    source: str = "openintel_parquet"
    timestamp: datetime
    domain: str | None = None
    zone: str | None = None
    measurement_id: str | None = None
    fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Normalized field name -> observed value (None when absent).",
    )
    row_index: int | None = None
    origin_file: str | None = None

    def value(self, field_name: str) -> Any:
        return self.fields.get(field_name)

    def has_value(self, field_name: str) -> bool:
        return self.fields.get(field_name) is not None


# --------------------------------------------------------------------------- #
# Matching, reasoning and scoring
# --------------------------------------------------------------------------- #


class ConditionEvaluation(_Base):
    """One condition evaluated against one observed signal.

    Mirrors the ``matched_conditions`` / ``failed_conditions`` entries in the
    decision trace.
    """

    field: str
    op: ConditionOp
    expected: Any = None
    observed: Any = None
    passed: bool
    field_present: bool = True
    explanation: str = ""


class IndicatorEvaluation(_Base):
    """One indicator evaluated against one observed signal."""

    indicator_id: str
    indicator_description: str
    required: bool
    weight: float
    ambiguous: bool = False
    queryability: Queryability = "queryable"
    matched: bool
    skipped: bool = Field(
        default=False,
        description="True when the indicator could not be evaluated at all "
        "(non-queryable field), as opposed to evaluated-and-failed.",
    )
    conditions: list[ConditionEvaluation] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    explanation: str = ""


class TimestampCheck(_Base):
    """Publication-date cutoff verdict for one signal/RFC pair."""

    observation_timestamp: datetime
    rfc_publication_date: datetime
    valid: bool
    days_after_publication: int
    explanation: str


class ScoreBreakdown(_Base):
    """Fully itemized score derivation.

    ``final_score = max(0, base + required_bonus + optional_bonus
                        - missing_required_penalty - partial_match_penalty
                        - ambiguity_penalty) * specificity_multiplier``

    with the whole result forfeited to 0 when the timestamp check fails
    (``timestamp_penalty`` then records the score that was withheld).
    """

    base_indicator_score: float = 0.0
    specificity_multiplier: float = 1.0
    required_match_bonus: float = 0.0
    optional_match_bonus: float = 0.0
    missing_required_penalty: float = 0.0
    partial_match_penalty: float = 0.0
    ambiguity_penalty: float = 0.0
    timestamp_penalty: float = 0.0
    final_score: float = 0.0
    steps: list[str] = Field(
        default_factory=list,
        description="Ordered human-readable arithmetic, one line per term.",
    )


class ReasoningTrace(_Base):
    """The explainable decision record for one signal x RFC evaluation."""

    trace_id: str
    signal_id: str
    rfc_id: str
    rfc_title: str
    observation_timestamp: datetime
    rfc_publication_date: datetime
    timestamp_valid: bool
    decision: Decision
    confidence: Confidence = "none"
    reasoning_summary: str
    matched_conditions: list[ConditionEvaluation] = Field(default_factory=list)
    failed_conditions: list[ConditionEvaluation] = Field(default_factory=list)
    matched_indicator_ids: list[str] = Field(default_factory=list)
    failed_indicator_ids: list[str] = Field(default_factory=list)
    skipped_indicator_ids: list[str] = Field(default_factory=list)
    missing_required_indicator_ids: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    matched_openintel_fields: list[str] = Field(default_factory=list)
    timestamp_check: TimestampCheck
    score_breakdown: ScoreBreakdown
    supporting_observation: dict[str, Any] = Field(default_factory=dict)
    uncertainty_notes: list[str] = Field(default_factory=list)


class RFCMatch(_Base):
    """Result of evaluating one observed signal against one RFC."""

    signal_id: str
    rfc_id: str
    rfc_title: str
    decision: Decision
    score: float
    confidence: Confidence
    timestamp_valid: bool
    observation_timestamp: datetime
    rfc_publication_date: datetime
    domain: str | None = None
    zone: str | None = None
    matched_indicator_ids: list[str] = Field(default_factory=list)
    failed_indicator_ids: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    matched_fields: list[str] = Field(default_factory=list)
    indicator_evaluations: list[IndicatorEvaluation] = Field(default_factory=list)
    score_breakdown: ScoreBreakdown
    trace_id: str
    reasoning_summary: str = ""


class RankedRFCCandidate(_Base):
    """An RFC aggregated across every signal that matched it."""

    rank: int
    rfc_id: str
    rfc_title: str
    specificity: Specificity
    rfc_publication_date: datetime
    decision: Decision
    score: float = Field(description="Best (max) per-signal score for this RFC.")
    aggregate_score: float = Field(
        default=0.0, description="Sum of per-signal scores; a volume measure."
    )
    confidence: Confidence
    supporting_signal_count: int = 0
    valid_match_count: int = 0
    partial_match_count: int = 0
    timestamp_invalid_count: int = 0
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    matched_indicator_ids: list[str] = Field(default_factory=list)
    matched_fields: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    zones: list[str] = Field(default_factory=list)
    example_signal_ids: list[str] = Field(default_factory=list)
    example_trace_ids: list[str] = Field(default_factory=list)
    reasoning_summary: str = ""
    score_breakdown: ScoreBreakdown | None = None


# --------------------------------------------------------------------------- #
# Review queue and LLM verification
# --------------------------------------------------------------------------- #


class ReviewItem(_Base):
    """Something a human (or an LLM) should look at before trusting a result."""

    item_id: str
    item_type: str = Field(
        description="e.g. non_queryable_indicator, partially_queryable_indicator, "
        "ambiguous_indicator, timestamp_invalid_match, partial_match, "
        "missing_required_field, schema_inconsistency, close_ranking."
    )
    severity: Severity
    reason: str
    affected_rfc_ids: list[str] = Field(default_factory=list)
    affected_fields: list[str] = Field(default_factory=list)
    affected_signal_ids: list[str] = Field(default_factory=list)
    suggested_action: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)
    status: ReviewStatus = "unresolved"
    trace_ids: list[str] = Field(default_factory=list)
    verification: "LLMVerification | None" = None


class LLMVerification(_Base):
    """Verdict from :mod:`openintel_rfc.llm_verifier`.

    The MVP ships a deterministic rule-based backend; the same shape is what a
    real LLM backend must return.
    """

    verification_status: VerificationStatus
    explanation: str
    backend: str = "deterministic"
    rfc_id: str | None = None
    signal_id: str | None = None
    trace_id: str | None = None
    confidence: Confidence = "none"


# --------------------------------------------------------------------------- #
# Adoption timeline
# --------------------------------------------------------------------------- #


class TimelineBucket(_Base):
    """Observation count for one time bucket."""

    period: str = Field(description="'YYYY-MM' for monthly, 'YYYY' for yearly.")
    count: int
    domains: int = 0
    mean_score: float = 0.0


class AdoptionTimelineEntry(_Base):
    """Adoption trajectory for one RFC, built from valid matches only."""

    rfc_id: str
    rfc_title: str
    rfc_publication_date: datetime
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    days_from_publication_to_first_seen: int | None = None
    observation_count: int = 0
    distinct_domains: int = 0
    distinct_zones: int = 0
    domains: list[str] = Field(default_factory=list)
    zones: list[str] = Field(default_factory=list)
    monthly_counts: list[TimelineBucket] = Field(default_factory=list)
    yearly_counts: list[TimelineBucket] = Field(default_factory=list)
    confidence_over_time: list[TimelineBucket] = Field(default_factory=list)
    notes: str = ""


# --------------------------------------------------------------------------- #
# Tool survey
# --------------------------------------------------------------------------- #


class ToolSurveyEntry(_Base):
    """One open-source tool considered for the pipeline."""

    name: str
    category: str
    url: str = ""
    docs_url: str = ""
    why_it_may_help: str = ""
    decision: Literal["use_now", "optional_later", "reject_for_mvp"]
    decision_rationale: str = ""
    pipeline_mapping: str = ""
    pypi_package: str | None = None
    risks: str = ""


class ToolSurvey(_Base):
    """The generated open-source tool survey."""

    generated_at: datetime
    live_search_performed: bool = False
    search_note: str = ""
    executive_summary: str = ""
    entries: list[ToolSurveyEntry] = Field(default_factory=list)
    mvp_stack: list[str] = Field(default_factory=list)
    optional_stack: list[str] = Field(default_factory=list)
    rejected: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    requirements_txt: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Run configuration and top-level result
# --------------------------------------------------------------------------- #


class RunConfig(_Base):
    """Inputs for one pipeline run (mirrors examples/sample_run_config.json)."""

    checklists: str
    dictionary: str
    parquet: str | None = None
    out: str = "demo_output"
    limit: int | None = Field(
        default=None, ge=1, description="Optional cap on rows read from Parquet."
    )
    engine: Literal["duckdb", "pandas", "auto"] = "auto"
    min_score: float = Field(
        default=0.0, ge=0.0, description="Drop ranked candidates below this score."
    )


class PipelineResult(_Base):
    """Everything one ``analyze`` run produced, in memory."""

    generated_at: datetime
    run_config: RunConfig
    schema_report: SchemaCheckReport
    signals: list[ObservedSignal] = Field(default_factory=list)
    matches: list[RFCMatch] = Field(default_factory=list)
    ranked_candidates: list[RankedRFCCandidate] = Field(default_factory=list)
    traces: list[ReasoningTrace] = Field(default_factory=list)
    review_items: list[ReviewItem] = Field(default_factory=list)
    timeline: list[AdoptionTimelineEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


ReviewItem.model_rebuild()
