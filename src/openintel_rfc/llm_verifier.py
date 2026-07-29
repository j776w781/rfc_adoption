"""Verification of reasoning traces: interface, prompt builder, and MVP backend.

The pipeline's matcher decides *mechanically* whether an observation matches an
RFC's indicators. This module asks a second question: given the trace the
matcher produced, should a human trust that verdict, reject it, or look at it
by hand? The answer lands in the review queue, so the explanation text here is
user-facing product copy, not debug output.

Three things matter about the design:

* **Nothing here needs an API key and nothing here touches the network on any
  default path.** The shipped backend, :class:`DeterministicVerifier`, is a pure
  function of the trace. A pipeline run is therefore reproducible and offline.
* :func:`build_prompt` is the real integration seam. It renders a trace into a
  structured extraction prompt and works with no backend configured at all, so
  a prompt can be inspected, diffed and unit-tested before any model exists.
* :class:`StubLLMVerifier` is the documented shape of a real backend. It builds
  the prompt and then raises :class:`~openintel_rfc.utils.PipelineError`. It
  never invents a verdict, because a fabricated "accepted" is worse than a
  crash: it would silently launder an unverified match into the results.

Wiring a real backend
---------------------
Subclass :class:`LLMVerifier`, call :func:`build_prompt` to render the trace,
send that prompt to your model, parse its JSON reply into
:class:`~openintel_rfc.models.LLMVerification`, then register the class::

    register_verifier("my_backend", MyVerifier)
    verifier = get_verifier("my_backend")

Nothing else in the pipeline needs to change.
"""

from __future__ import annotations

import abc
from collections.abc import Sequence

from . import config
from .models import (
    ConditionEvaluation,
    LLMVerification,
    RFCChecklistDB,
    RFCChecklistEntry,
    ReasoningTrace,
)
from .utils import PipelineError, format_value, get_logger, iso

__all__ = [
    "DEFAULT_VERIFIER_NAME",
    "LLMVerifier",
    "DeterministicVerifier",
    "StubLLMVerifier",
    "build_prompt",
    "get_verifier",
    "register_verifier",
    "verify_traces",
    "available_verifiers",
]

LOGGER = get_logger(__name__)

#: Backend used when the caller does not name one. Deterministic and offline.
DEFAULT_VERIFIER_NAME = "deterministic"


# --------------------------------------------------------------------------- #
# Interface
# --------------------------------------------------------------------------- #


class LLMVerifier(abc.ABC):
    """Second-opinion verifier for one reasoning trace.

    Implementations must be side-effect free with respect to the trace and must
    return an :class:`LLMVerification` whose ``explanation`` is a complete
    sentence citing concrete evidence: it is rendered verbatim in the review
    queue, where the reader has the trace but not the verifier's internals.
    """

    #: Short backend identifier, copied into ``LLMVerification.backend``.
    name: str = "abstract"

    @abc.abstractmethod
    def verify(
        self,
        *,
        trace: ReasoningTrace,
        rfc: RFCChecklistEntry | None = None,
        checklist_text: str | None = None,
    ) -> LLMVerification:
        """Return a verdict for ``trace``.

        ``rfc`` and ``checklist_text`` are optional context. When supplied they
        let a backend quote the checklist's own wording; when omitted the
        verdict must still be derivable from the trace alone.
        """

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"{type(self).__name__}(name={self.name!r})"


# --------------------------------------------------------------------------- #
# Prompt construction (works with no backend configured)
# --------------------------------------------------------------------------- #


_PROMPT_INSTRUCTIONS = """\
You are auditing one automated RFC-adoption match produced by a DNS measurement
pipeline that reads OpenINTEL data. Decide whether the observation below is
sound evidence that the named RFC's mechanism is deployed for the observed name.

Apply these rules in order, and stop at the first that applies:
1. If the observation timestamp is earlier than the RFC publication date, answer
   "rejected": an observation cannot evidence a mechanism that did not yet exist.
2. If no indicator matched, answer "rejected".
3. If every required indicator matched, no matched indicator is flagged
   ambiguous, and the pipeline confidence is high or very_high, answer
   "accepted".
4. Otherwise answer "needs_manual_review".

Judge only the evidence shown. Absence of a field is not evidence of absence of
the mechanism: if a required field was missing from the observation, say so
rather than concluding non-adoption."""

_PROMPT_ANSWER_SPEC = """\
Return exactly one JSON object and nothing else:

{
  "verification_status": "accepted" | "rejected" | "needs_manual_review",
  "explanation": "one or two complete sentences citing the concrete field
                  values, indicator ids and dates shown above",
  "confidence": "very_high" | "high" | "medium" | "low" | "none"
}"""


def _render_condition(evaluation: ConditionEvaluation) -> str:
    verdict = "PASS" if evaluation.passed else "FAIL"
    expected = (
        "" if evaluation.op == "exists" else f" {format_value(evaluation.expected)}"
    )
    absent = "" if evaluation.field_present else " [field absent from the observation]"
    return (
        f"  - {verdict} {evaluation.field} {evaluation.op}{expected} "
        f"(observed: {format_value(evaluation.observed)}){absent}"
    )


def _render_list(label: str, values: Sequence[str]) -> str:
    return f"{label}: {', '.join(values) if values else '(none)'}"


def build_prompt(
    trace: ReasoningTrace,
    rfc: RFCChecklistEntry | None = None,
    checklist_text: str | None = None,
) -> str:
    """Render one trace into a structured extraction prompt.

    This is the integration seam for a real LLM backend. It performs no IO and
    requires no configuration, so the exact text a backend would send can be
    reviewed, diffed and asserted on in tests before any model is wired up.

    The prompt is deliberately closed-book: everything needed to reach a verdict
    (dates, indicator ids, per-condition field values, the score arithmetic) is
    inlined, so the model is never asked to recall an RFC from memory.
    """
    breakdown = trace.score_breakdown
    lines: list[str] = [
        _PROMPT_INSTRUCTIONS,
        "",
        "## Match under review",
        f"trace_id: {trace.trace_id}",
        f"signal_id: {trace.signal_id}",
        f"rfc_id: {trace.rfc_id}",
        f"rfc_title: {trace.rfc_title}",
        f"rfc_publication_date: {iso(trace.rfc_publication_date)}",
        f"observation_timestamp: {iso(trace.observation_timestamp)}",
        f"pipeline_decision: {trace.decision}",
        f"pipeline_confidence: {trace.confidence}",
        f"pipeline_score: {breakdown.final_score}",
        f"pipeline_summary: {trace.reasoning_summary}",
        "",
        "## Publication-date cutoff",
        f"valid: {'yes' if trace.timestamp_valid else 'no'}",
        f"days_after_publication: {trace.timestamp_check.days_after_publication}",
        f"cutoff_explanation: {trace.timestamp_check.explanation}",
        "",
        "## Indicators",
        _render_list("matched", trace.matched_indicator_ids),
        _render_list("failed", trace.failed_indicator_ids),
        _render_list("skipped (non-queryable)", trace.skipped_indicator_ids),
        _render_list("required but unmatched", trace.missing_required_indicator_ids),
        _render_list("fields missing from the observation", trace.missing_fields),
        _render_list("fields that carried the match", trace.matched_openintel_fields),
        "",
        "## Conditions evaluated",
    ]

    conditions = list(trace.matched_conditions) + list(trace.failed_conditions)
    if conditions:
        lines.extend(_render_condition(c) for c in conditions)
    else:
        lines.append("  (no condition was evaluated)")

    lines.extend(["", "## Score derivation"])
    if breakdown.steps:
        lines.extend(f"  {step}" for step in breakdown.steps)
    else:
        lines.append(f"  final_score = {breakdown.final_score}")
    if breakdown.timestamp_penalty:
        lines.append(
            f"  score forfeited to the publication-date cutoff: "
            f"{breakdown.timestamp_penalty}"
        )

    lines.extend(["", "## Observation"])
    if trace.supporting_observation:
        for key in sorted(trace.supporting_observation):
            lines.append(f"  {key} = {format_value(trace.supporting_observation[key])}")
    else:
        lines.append("  (the trace carried no observation snapshot)")

    if trace.uncertainty_notes:
        lines.extend(["", "## Uncertainty noted by the pipeline"])
        lines.extend(f"  - {note}" for note in trace.uncertainty_notes)

    if rfc is not None:
        lines.extend(
            [
                "",
                "## RFC checklist entry",
                f"specificity: {rfc.specificity} "
                f"(ranking multiplier {rfc.specificity_multiplier})",
                f"description: {rfc.description}",
            ]
        )
        if rfc.notes:
            lines.append(f"checklist_notes: {rfc.notes}")
        for indicator in rfc.indicators:
            flags = "required" if indicator.required else "optional"
            if indicator.ambiguous:
                flags += ", ambiguous"
            lines.append(
                f"  - {indicator.id} ({flags}, weight {indicator.weight}): "
                f"{indicator.description}"
            )

    if checklist_text:
        lines.extend(["", "## Checklist text supplied by the caller", checklist_text])

    lines.extend(["", "## Required answer", _PROMPT_ANSWER_SPEC])
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Deterministic backend (the MVP default)
# --------------------------------------------------------------------------- #


def _joined(values: Sequence[str], empty: str = "none") -> str:
    return ", ".join(values) if values else empty


class DeterministicVerifier(LLMVerifier):
    """Rule-based verifier: a pure function of the trace, offline and stable.

    The rules mirror the decision table in the build contract:

    ==========================================  ======================
    trace                                       verdict
    ==========================================  ======================
    ``valid_match`` at very_high/high            ``accepted``
    ``valid_match`` at medium/low/none           ``needs_manual_review``
    ``timestamp_invalid``                        ``rejected``
    ``no_match``                                 ``rejected``
    ``partial_match`` / ``ambiguous`` /
    ``non_queryable``                            ``needs_manual_review``
    ==========================================  ======================

    The auto-accept confidence set comes from
    :data:`openintel_rfc.config.LLM_AUTO_ACCEPT_CONFIDENCES`, so raising the bar
    is a one-line configuration change rather than a code change.
    """

    name = "deterministic"

    def verify(
        self,
        *,
        trace: ReasoningTrace,
        rfc: RFCChecklistEntry | None = None,
        checklist_text: str | None = None,
    ) -> LLMVerification:
        """Apply the rule table above and explain the verdict in full sentences."""
        status, explanation = self._decide(trace, rfc)
        return LLMVerification(
            verification_status=status,
            explanation=explanation,
            backend=self.name,
            rfc_id=trace.rfc_id,
            signal_id=trace.signal_id,
            trace_id=trace.trace_id,
            confidence=trace.confidence,
        )

    # -- individual rules ---------------------------------------------------- #

    def _decide(
        self, trace: ReasoningTrace, rfc: RFCChecklistEntry | None
    ) -> tuple[str, str]:
        if trace.decision == "timestamp_invalid" or not trace.timestamp_valid:
            return "rejected", self._explain_timestamp_invalid(trace)
        if trace.decision == "no_match":
            return "rejected", self._explain_no_match(trace)
        if trace.decision == "valid_match":
            if trace.confidence in config.LLM_AUTO_ACCEPT_CONFIDENCES:
                return "accepted", self._explain_accepted(trace)
            return "needs_manual_review", self._explain_low_confidence(trace)
        if trace.decision == "ambiguous":
            return "needs_manual_review", self._explain_ambiguous(trace, rfc)
        if trace.decision == "non_queryable":
            return "needs_manual_review", self._explain_non_queryable(trace)
        if trace.decision == "partial_match":
            return "needs_manual_review", self._explain_partial(trace)
        # Unknown decision: refuse to guess rather than default to accepted.
        raise PipelineError(
            f"Trace {trace.trace_id} carries decision {trace.decision!r}, which the "
            "deterministic verifier has no rule for. Add a rule to "
            "DeterministicVerifier._decide before running verification."
        )

    def _explain_timestamp_invalid(self, trace: ReasoningTrace) -> str:
        days_before = abs(trace.timestamp_check.days_after_publication)
        forfeited = trace.score_breakdown.timestamp_penalty
        forfeited_clause = (
            f", forfeiting the score of {forfeited} the indicators would otherwise have "
            "earned"
            if forfeited
            else ""
        )
        return (
            f"Rejected: signal {trace.signal_id} was observed on "
            f"{iso(trace.observation_timestamp)}, which is {days_before} day(s) before "
            f"{trace.rfc_id} was published on {iso(trace.rfc_publication_date)}, so the "
            f"observation cannot be evidence of a mechanism that did not yet exist"
            f"{forfeited_clause}; the matched indicator(s) "
            f"{_joined(trace.matched_indicator_ids)} should be attributed to an earlier "
            "RFC instead."
        )

    def _explain_no_match(self, trace: ReasoningTrace) -> str:
        return (
            f"Rejected: no indicator of {trace.rfc_id} matched signal {trace.signal_id} "
            f"observed on {iso(trace.observation_timestamp)} - indicator(s) "
            f"{_joined(trace.failed_indicator_ids)} were evaluated and failed"
            + (
                f" and field(s) {_joined(trace.missing_fields)} were absent from the "
                "observation, so this is an absence of evidence rather than evidence of "
                "absence"
                if trace.missing_fields
                else ", so there is no evidence linking this observation to the RFC"
            )
            + "."
        )

    def _explain_accepted(self, trace: ReasoningTrace) -> str:
        return (
            f"Accepted: every required indicator of {trace.rfc_id} matched signal "
            f"{trace.signal_id} - {_joined(trace.matched_indicator_ids)} - on the fields "
            f"{_joined(trace.matched_openintel_fields)}, scoring "
            f"{trace.score_breakdown.final_score} at {trace.confidence} confidence, and "
            f"the observation of {iso(trace.observation_timestamp)} postdates the "
            f"{iso(trace.rfc_publication_date)} publication date by "
            f"{trace.timestamp_check.days_after_publication} day(s), so the match is "
            "sound on the evidence recorded."
        )

    def _explain_low_confidence(self, trace: ReasoningTrace) -> str:
        accept_at = ", ".join(sorted(config.LLM_AUTO_ACCEPT_CONFIDENCES))
        return (
            f"Manual review required: every required indicator of {trace.rfc_id} matched "
            f"signal {trace.signal_id} ({_joined(trace.matched_indicator_ids)}), but the "
            f"score of {trace.score_breakdown.final_score} yields only {trace.confidence} "
            f"confidence, below the auto-accept levels ({accept_at}); confirm by hand that "
            f"the observed field values {_joined(trace.matched_openintel_fields)} really "
            "identify this RFC rather than a broader DNSSEC deployment."
        )

    def _explain_ambiguous(
        self, trace: ReasoningTrace, rfc: RFCChecklistEntry | None
    ) -> str:
        ambiguous_ids = [
            indicator.id
            for indicator in (rfc.indicators if rfc is not None else [])
            if indicator.ambiguous and indicator.id in set(trace.matched_indicator_ids)
        ]
        flagged = _joined(ambiguous_ids) if ambiguous_ids else _joined(
            trace.matched_indicator_ids
        )
        return (
            f"Manual review required: every required indicator of {trace.rfc_id} matched "
            f"signal {trace.signal_id} observed on {iso(trace.observation_timestamp)}, but "
            f"indicator(s) {flagged} are flagged ambiguous in the checklist, meaning the "
            f"same field values ({_joined(trace.matched_openintel_fields)}) are equally "
            "well explained by another RFC; attribution has to be settled by a human, not "
            "by the score."
        )

    def _explain_non_queryable(self, trace: ReasoningTrace) -> str:
        return (
            f"Manual review required: {trace.rfc_id} could not be evaluated against signal "
            f"{trace.signal_id} because its required indicator(s) "
            f"{_joined(trace.skipped_indicator_ids)} depend on field(s) "
            f"{_joined(trace.missing_fields)} that the OpenINTEL corpus does not export; "
            "no evidence was gathered either for or against adoption, so this must not be "
            "reported as a negative result."
        )

    def _explain_partial(self, trace: ReasoningTrace) -> str:
        missing_clause = (
            f" Field(s) {_joined(trace.missing_fields)} were absent from the observation, "
            "so the pipeline cannot distinguish non-adoption from missing data."
            if trace.missing_fields
            else " All referenced fields were present, so the unmatched indicator(s) "
            "genuinely did not hold for this observation."
        )
        return (
            f"Manual review required: signal {trace.signal_id} matched "
            f"{len(trace.matched_indicator_ids)} indicator(s) of {trace.rfc_id} "
            f"({_joined(trace.matched_indicator_ids)}) but required indicator(s) "
            f"{_joined(trace.missing_required_indicator_ids)} did not match, scoring "
            f"{trace.score_breakdown.final_score}.{missing_clause}"
        )


# --------------------------------------------------------------------------- #
# Stub backend (the documented seam for a real LLM)
# --------------------------------------------------------------------------- #


class StubLLMVerifier(LLMVerifier):
    """Placeholder for a real LLM backend: builds the prompt, then refuses.

    It exists so the integration point is executable and testable without a
    model. :meth:`verify` renders the prompt (available afterwards as
    :attr:`last_prompt` for inspection) and raises
    :class:`~openintel_rfc.utils.PipelineError`. It never returns a verdict,
    because a fabricated verdict would be indistinguishable in the output from a
    real one.
    """

    name = "stub_llm"

    def __init__(self) -> None:
        #: The most recent prompt this verifier rendered, for inspection/tests.
        self.last_prompt: str | None = None

    def verify(
        self,
        *,
        trace: ReasoningTrace,
        rfc: RFCChecklistEntry | None = None,
        checklist_text: str | None = None,
    ) -> LLMVerification:
        """Render the prompt for ``trace`` and raise; never returns."""
        self.last_prompt = build_prompt(trace, rfc, checklist_text)
        raise PipelineError(
            f"No LLM backend is configured, so trace {trace.trace_id} "
            f"({trace.signal_id} x {trace.rfc_id}) cannot be verified by an LLM. "
            f"A {len(self.last_prompt)}-character prompt was prepared and is available "
            "as StubLLMVerifier.last_prompt (or from build_prompt(trace)). To wire a real "
            "backend: subclass LLMVerifier, send build_prompt(trace, rfc) to your model, "
            "parse the JSON reply into an LLMVerification, then call "
            "register_verifier('<name>', YourClass) and select it with "
            "get_verifier('<name>'). To keep the pipeline offline and reproducible, use "
            f"get_verifier('{DEFAULT_VERIFIER_NAME}') instead."
        )


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #

_VERIFIERS: dict[str, type[LLMVerifier]] = {
    DeterministicVerifier.name: DeterministicVerifier,
    StubLLMVerifier.name: StubLLMVerifier,
}


def register_verifier(name: str, verifier_cls: type[LLMVerifier]) -> None:
    """Register a backend under ``name`` so :func:`get_verifier` can build it.

    Re-registering an existing name is allowed but logged, since silently
    swapping the backend behind a familiar name would make two runs with
    identical configuration produce different verdicts.
    """
    if not issubclass(verifier_cls, LLMVerifier):
        raise PipelineError(
            f"{verifier_cls!r} cannot be registered as a verifier: it does not subclass "
            "LLMVerifier."
        )
    if name in _VERIFIERS and _VERIFIERS[name] is not verifier_cls:
        LOGGER.warning(
            "Verifier %r was already registered as %s and is being replaced by %s.",
            name,
            _VERIFIERS[name].__name__,
            verifier_cls.__name__,
        )
    _VERIFIERS[name] = verifier_cls


def available_verifiers() -> list[str]:
    """Names accepted by :func:`get_verifier`, in stable order."""
    return sorted(_VERIFIERS)


def get_verifier(name: str | None = None) -> LLMVerifier:
    """Instantiate a verifier by name.

    ``None`` selects :data:`DEFAULT_VERIFIER_NAME`, the deterministic offline
    backend, so the default path never needs credentials or a network call.
    """
    key = name or DEFAULT_VERIFIER_NAME
    verifier_cls = _VERIFIERS.get(key)
    if verifier_cls is None:
        raise PipelineError(
            f"Unknown verifier {key!r}. Available: {', '.join(available_verifiers())}. "
            "Register a new one with register_verifier(name, cls)."
        )
    return verifier_cls()


# --------------------------------------------------------------------------- #
# Batch entry point
# --------------------------------------------------------------------------- #


def verify_traces(
    traces: Sequence[ReasoningTrace],
    db: RFCChecklistDB | None = None,
    verifier: LLMVerifier | None = None,
) -> dict[str, LLMVerification]:
    """Verify every trace, returning ``{trace_id: LLMVerification}``.

    ``db`` supplies the checklist entry for each trace when available, which
    lets a backend quote indicator wording and ambiguity flags. ``verifier``
    defaults to the deterministic offline backend.

    Duplicate ``trace_id`` values are a caller bug - one trace id must identify
    one signal/RFC evaluation - so they raise instead of overwriting. The result
    is ordered by ``trace_id`` for byte-stable output.
    """
    active = verifier or get_verifier()
    results: dict[str, LLMVerification] = {}
    for trace in traces:
        if trace.trace_id in results:
            raise PipelineError(
                f"Duplicate trace_id {trace.trace_id!r} passed to verify_traces; trace ids "
                "must be unique per signal/RFC pair."
            )
        rfc = db.get(trace.rfc_id) if db is not None else None
        results[trace.trace_id] = active.verify(trace=trace, rfc=rfc)
    return {trace_id: results[trace_id] for trace_id in sorted(results)}
