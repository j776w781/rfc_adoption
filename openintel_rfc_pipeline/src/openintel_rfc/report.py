"""Markdown rendering for the schema cross-check and the analysis report.

Two documents are produced here:

``schema_check_report.md``
    What the OpenINTEL corpus can and cannot answer about the RFC checklist,
    before any measurement data is read.

``report.md``
    The result of one ``analyze`` run: inputs, signals, ranked RFC candidates,
    the reasoning behind them, the matches that were rejected on publication
    dates, and what a reader should not conclude from any of it.

The report is written for a reader who will not open the JSON. Every claim it
makes is therefore accompanied by the evidence that supports it: scores are
shown with their supporting observation counts, rejected matches are shown with
both dates, and Section 8 quotes reasoning summaries verbatim.

Only :mod:`models`, :mod:`config` and :mod:`utils` are imported at module level.
:mod:`tool_survey` is imported lazily inside :func:`_tool_stack_section` and is
optional: the report degrades to a static description of the stack if it is not
available.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Any, Final

from . import config
from .models import (
    IndicatorSchemaCheck,
    PipelineResult,
    ReasoningTrace,
    RFCMatch,
    SchemaCheckReport,
)
from .utils import get_logger, iso

__all__ = ["md_table", "render_schema_check_report", "render_report"]

LOGGER = get_logger("openintel_rfc.report")

#: Cells longer than this are truncated in tables. Prose, blockquoted reasoning
#: summaries and the limitations text are never truncated.
MAX_CELL_WIDTH: Final[int] = 72

#: How many ranked candidates the headline table shows before it is cut off.
TOP_CANDIDATE_ROWS: Final[int] = 15

#: How many individual review items are listed inline.
REVIEW_ITEM_ROWS: Final[int] = 25

#: The sentence Section 13 must state, unhedged, in exactly this form.
LIMITATION_SENTENCE: Final[str] = (
    "This pipeline does not prove RFC adoption by itself. It identifies ranked "
    "RFC candidates based on OpenINTEL-observable signals and timestamp "
    "consistency."
)

#: Fallback description of the stack, used when the tool survey module or its
#: generated Markdown is unavailable. Kept in sync with pyproject dependencies.
_FALLBACK_TOOL_STACK: Final[tuple[tuple[str, str, str, str], ...]] = (
    (
        "pandas",
        "dataframes",
        "Normalized analysis frame between Parquet and the signal extractor.",
        "use_now",
    ),
    (
        "pyarrow",
        "columnar IO",
        "Reads OpenINTEL Parquet with column projection.",
        "use_now",
    ),
    (
        "duckdb",
        "analytical SQL",
        "Optional Parquet engine; pushes column selection and row limits down.",
        "use_now",
    ),
    (
        "pydantic",
        "validation",
        "Typed models for checklists, dictionary and every artefact; malformed "
        "input fails loudly at load time.",
        "use_now",
    ),
    (
        "pytest",
        "testing",
        "Regression tests for the scoring formula and the timestamp cutoff rule.",
        "use_now",
    ),
    (
        "streamlit",
        "dashboard",
        "Reads the exported artefacts; no pipeline logic lives in the UI.",
        "use_now",
    ),
    (
        "plotly",
        "charts",
        "Adoption timeline and score distribution plots in the dashboard.",
        "use_now",
    ),
    (
        "rich",
        "terminal output",
        "Would improve CLI readability; argparse plus plain print is sufficient "
        "for the MVP.",
        "optional_later",
    ),
    (
        "networkx",
        "graphs",
        "Could model RFC obsoletes/updates relationships for ranking.",
        "optional_later",
    ),
    (
        "polars",
        "dataframes",
        "Faster than pandas at scale, but not installed in this environment and "
        "pandas is adequate for the sample corpus.",
        "reject_for_mvp",
    ),
    (
        "pandera",
        "dataframe schema validation",
        "Overlaps with the pydantic models and the dictionary cross-check that "
        "already gate the inputs.",
        "reject_for_mvp",
    ),
)


# --------------------------------------------------------------------------- #
# Markdown primitives
# --------------------------------------------------------------------------- #


def _cell(value: Any, max_width: int | None) -> str:
    """Render one table cell: single line, pipes escaped, optionally truncated."""
    if value is None:
        return "-"
    if isinstance(value, datetime):
        text = iso(value)
    elif isinstance(value, bool):
        text = "yes" if value else "no"
    elif isinstance(value, float):
        text = f"{value:g}"
    elif isinstance(value, (list, tuple)):
        text = ", ".join(_cell(item, None) for item in value)
    else:
        text = str(value)
    text = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()
    # A raw pipe would terminate the cell; escape it rather than dropping it.
    text = text.replace("|", "\\|")
    if max_width is not None and len(text) > max_width:
        text = text[: max_width - 1].rstrip() + "..."
    return text or "-"


def md_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[Any]],
    *,
    max_cell_width: int | None = MAX_CELL_WIDTH,
) -> str:
    """Render a GitHub-flavoured Markdown table.

    Cells are coerced to a single line with pipes escaped. ``max_cell_width``
    truncates long values with an ellipsis; pass ``None`` where the full text
    matters more than the column width.
    """
    if not headers:
        raise ValueError("md_table requires at least one header")
    lines = [
        "| " + " | ".join(_cell(h, max_cell_width) for h in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        cells = [_cell(value, max_cell_width) for value in row]
        # Pad or trim so a malformed row cannot corrupt the whole table.
        cells = (cells + ["-"] * len(headers))[: len(headers)]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _date(value: datetime | None) -> str:
    """Render a datetime as a plain date; ``-`` when absent."""
    return value.strftime("%Y-%m-%d") if value is not None else "-"


def _bullets(items: Iterable[str]) -> list[str]:
    return [f"- {item}" for item in items]


def _quote(text: str) -> list[str]:
    """Blockquote a string without truncating it (evidence must stay intact)."""
    flattened = " ".join(str(text).split())
    return [f"> {flattened}"] if flattened else ["> (empty)"]


def _plural(count: int, singular: str, plural: str | None = None) -> str:
    return singular if count == 1 else (plural or singular + "s")


def _counter_rows(counter: Counter[str], total: int) -> list[list[Any]]:
    """Descending count rows with a percentage column; ties broken by name."""
    rows: list[list[Any]] = []
    for key, count in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])):
        share = f"{100.0 * count / total:.1f}%" if total else "-"
        rows.append([key, count, share])
    return rows


# --------------------------------------------------------------------------- #
# Schema cross-check report
# --------------------------------------------------------------------------- #


def _indicator_fields(check: IndicatorSchemaCheck) -> list[str]:
    seen: dict[str, None] = {}
    for condition in check.condition_checks:
        seen.setdefault(condition.field, None)
    return list(seen)


def render_schema_check_report(report: SchemaCheckReport) -> str:
    """Render ``schema_check_report.md`` from a completed schema cross-check.

    The document answers one question: for each RFC indicator, can the OpenINTEL
    corpus express it at all? Indicators that cannot be expressed are listed
    with the missing field names, because that is the actionable part - it says
    which measurements would have to change for the indicator to become testable.
    """
    counts = report.counts_by_queryability
    lines: list[str] = [
        "# OpenINTEL Schema Cross-Check",
        "",
        f"Generated: {iso(report.generated_at)}  ",
        f"Pipeline: {config.PIPELINE_NAME} {config.PIPELINE_VERSION}",
        "",
        "Every indicator in the RFC checklist is checked field by field against "
        "the OpenINTEL analysis dictionary *before* any measurement data is "
        "read. An indicator whose fields the corpus does not carry cannot be "
        "answered by this data source at any confidence level, and saying so "
        "explicitly is more useful than silently scoring it as a non-match.",
        "",
        "## 1. Inputs",
        "",
        md_table(
            ["Input", "Value"],
            [
                ["Checklist", report.checklist_path],
                ["Dictionary", report.dictionary_path],
                ["RFCs", report.rfc_count],
                ["Indicators", report.indicator_count],
                ["Dictionary fields", report.dictionary_field_count],
            ],
            max_cell_width=None,
        ),
        "",
        "## 2. Queryability summary",
        "",
        md_table(
            ["Queryability", "Indicators", "Share"],
            _counter_rows(Counter(counts), report.indicator_count),
        ),
        "",
        "Definitions: *queryable* - every field the indicator references exists "
        "in the dictionary; *partially_queryable* - some fields exist and at "
        "least one does not, so the indicator can only ever be partly evaluated; "
        "*non_queryable* - none of the discriminating fields exist; *ambiguous* - "
        "the fields exist but the observation is not uniquely attributable to "
        "the RFC.",
        "",
    ]

    lines += ["## 3. Indicator verdicts", ""]
    verdict_rows = [
        [
            check.rfc_id,
            check.indicator_id,
            "required" if check.required else "optional",
            check.weight,
            check.queryability,
            ", ".join(_indicator_fields(check)),
            ", ".join(check.missing_fields) or "-",
        ]
        for check in report.indicators
    ]
    if verdict_rows:
        lines += [
            md_table(
                [
                    "RFC",
                    "Indicator",
                    "Role",
                    "Weight",
                    "Queryability",
                    "Fields used",
                    "Missing fields",
                ],
                verdict_rows,
            ),
            "",
        ]
    else:
        lines += ["No indicators were checked.", ""]

    lines += ["## 4. Reasoning per non-queryable indicator", ""]
    blocked = [
        check
        for check in report.indicators
        if check.queryability in {"non_queryable", "partially_queryable"}
    ]
    if blocked:
        for check in blocked:
            lines += [
                f"### {check.rfc_id} / {check.indicator_id} "
                f"({check.queryability})",
                "",
                check.indicator_description,
                "",
            ]
            lines += _quote(check.reasoning)
            lines += [""]
            if check.missing_fields:
                lines += [
                    "Missing dictionary fields: "
                    + ", ".join(f"`{name}`" for name in check.missing_fields),
                    "",
                ]
            for warning in check.warnings:
                lines += [f"Warning: {warning}", ""]
    else:
        lines += [
            "Every indicator's fields are present in the dictionary.",
            "",
        ]

    lines += ["## 5. Dictionary coverage", ""]
    field_rows = [
        [
            field.name,
            field.type,
            _date(field.available_from),
            "yes" if field.nullable else "no",
            ", ".join(field.openintel_native_fields) or "-",
        ]
        for field in report.dictionary_fields
    ]
    if field_rows:
        lines += [
            md_table(
                ["Field", "Type", "Available from", "Nullable", "OpenINTEL columns"],
                field_rows,
            ),
            "",
        ]
    if report.unused_dictionary_fields:
        lines += [
            "Dictionary fields no indicator references: "
            + ", ".join(f"`{name}`" for name in report.unused_dictionary_fields),
            "",
        ]

    lines += ["## 6. Warnings", ""]
    if report.warnings:
        lines += _bullets(report.warnings) + [""]
    else:
        lines += ["None.", ""]

    lines += [
        "## 7. How to read this document",
        "",
        "A *queryable* verdict means the corpus can express the indicator, not "
        "that the indicator was observed. Matching against measurement data "
        "happens in `report.md`. A *non_queryable* verdict is a statement about "
        "this data source only: the mechanism may well be deployed, but "
        "OpenINTEL record-level observations cannot see it.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


# --------------------------------------------------------------------------- #
# Analysis report - section helpers
# --------------------------------------------------------------------------- #


def _signal_date_range(result: PipelineResult) -> tuple[datetime | None, datetime | None]:
    stamps = [signal.timestamp for signal in result.signals]
    if not stamps:
        stamps = [match.observation_timestamp for match in result.matches]
    if not stamps:
        return None, None
    return min(stamps), max(stamps)


def _decision_counter(result: PipelineResult) -> Counter[str]:
    return Counter(match.decision for match in result.matches)


def _timestamp_invalid_matches(result: PipelineResult) -> list[RFCMatch]:
    """Matches rejected purely because the observation predates the RFC.

    Selecting on ``decision`` alone is deliberate. Many more matches carry
    ``timestamp_valid=False`` -- every observation that predates an RFC it never
    matched on the evidence either -- but the date was not what rejected those,
    and counting them here would overstate how much the cutoff actually did.
    """
    return [match for match in result.matches if match.decision == "timestamp_invalid"]


def _executive_summary(result: PipelineResult) -> list[str]:
    decisions = _decision_counter(result)
    first, last = _signal_date_range(result)
    top = result.ranked_candidates[0] if result.ranked_candidates else None
    invalid = _timestamp_invalid_matches(result)
    high_severity = [item for item in result.review_items if item.severity == "high"]

    lines = [
        "## 1. Executive Summary",
        "",
        f"This run evaluated {len(result.signals)} normalized OpenINTEL "
        f"{_plural(len(result.signals), 'observation')} against "
        f"{result.schema_report.rfc_count} DNSSEC "
        f"{_plural(result.schema_report.rfc_count, 'RFC')} "
        f"({result.schema_report.indicator_count} indicators), producing "
        f"{len(result.matches)} signal-by-RFC "
        f"{_plural(len(result.matches), 'evaluation')} and "
        f"{len(result.traces)} reasoning "
        f"{_plural(len(result.traces), 'trace')}. Every score below is derived "
        "from record-level observations and the RFC publication date; nothing "
        "here is an assertion that an operator deliberately implemented a "
        "specification.",
        "",
    ]
    if top is not None:
        lines += [
            f"The highest-ranked candidate is **{top.rfc_id}** "
            f"({top.rfc_title}) with score {top.score} "
            f"({top.confidence} confidence), supported by "
            f"{top.supporting_signal_count} "
            f"{_plural(top.supporting_signal_count, 'observation')}"
            + (f", first seen {_date(top.first_seen)}." if top.first_seen else "."),
            "",
        ]
    else:
        lines += [
            "No RFC candidate scored above the ranking threshold, so this run "
            "makes no positive adoption claim at all.",
            "",
        ]

    lines += _bullets(
        [
            f"Observation window: {_date(first)} to {_date(last)}."
            if first
            else "Observation window: no observations were extracted.",
            f"Valid matches: {decisions.get('valid_match', 0)}; "
            f"partial: {decisions.get('partial_match', 0)}; "
            f"ambiguous: {decisions.get('ambiguous', 0)}; "
            f"no match: {decisions.get('no_match', 0)}.",
            f"Rejected on publication date (impossible timestamps): "
            f"{len(invalid)}.",
            f"Ranked candidates emitted: {len(result.ranked_candidates)}.",
            f"Review queue: {len(result.review_items)} "
            f"{_plural(len(result.review_items), 'item')}, "
            f"{len(high_severity)} of high severity.",
            f"Warnings collected during the run: {len(result.warnings)}.",
        ]
    )
    lines += [""]
    return lines


def _inputs_section(result: PipelineResult) -> list[str]:
    run_config = result.run_config
    rows: list[list[Any]] = [
        ["Checklist database", run_config.checklists],
        ["OpenINTEL dictionary", run_config.dictionary],
        ["Parquet input", run_config.parquet or "(none)"],
        ["Output directory", run_config.out],
        ["Parquet engine", run_config.engine],
        ["Row limit", run_config.limit if run_config.limit is not None else "none"],
        ["Minimum rankable score", run_config.min_score],
        ["Generated at", iso(result.generated_at)],
        ["Pipeline", f"{config.PIPELINE_NAME} {config.PIPELINE_VERSION}"],
    ]
    return [
        "## 2. Inputs",
        "",
        md_table(["Input", "Value"], rows, max_cell_width=None),
        "",
        "The checklist database is the RFC signature source; the dictionary "
        "describes which normalized analysis fields the OpenINTEL corpus can "
        "supply and from which date each is reliably populated.",
        "",
    ]


def _load_tool_survey() -> tuple[Any | None, str | None]:
    """Best-effort lazy load of a generated :class:`ToolSurvey`.

    ``tool_survey`` is owned by another module and may legitimately be absent,
    so an :class:`ImportError` is expected and downgraded to "use the static
    stack description". Any other failure is reported in the section text rather
    than swallowed.
    """
    try:
        from . import tool_survey as tool_survey_module  # noqa: PLC0415
    except ImportError:
        return None, None

    for attribute in ("build_survey", "build_default_survey", "default_survey", "make_survey"):
        factory = getattr(tool_survey_module, attribute, None)
        if not callable(factory):
            continue
        try:
            survey = factory()
        except TypeError:
            # Wrong arity for a zero-argument call; try the next candidate.
            continue
        except Exception as exc:  # pragma: no cover - defensive, reported below
            return None, f"tool_survey.{attribute}() failed: {exc}"
        if getattr(survey, "entries", None):
            return survey, None
    return None, None


def _first_paragraph(markdown: str) -> str:
    """First prose paragraph of a Markdown document (headings/tables skipped)."""
    paragraph: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            if paragraph:
                break
            continue
        if line.startswith(("#", "|", ">", "-", "*", "`", "=")):
            if paragraph:
                break
            continue
        paragraph.append(line)
    return " ".join(paragraph)


def _tool_stack_section(survey_markdown: str | None) -> list[str]:
    lines = [
        "## 3. Open-Source Tool Stack",
        "",
        "The stack was chosen for reproducibility and for keeping the reasoning "
        "auditable: every dependency either reads the input format, validates "
        "the inputs, or renders the outputs. No dependency participates in the "
        "matching decision itself.",
        "",
    ]
    survey, failure = _load_tool_survey()
    if failure:
        lines += [f"Note: {failure} The static stack description is used instead.", ""]

    rows: list[list[Any]] = []
    if survey is not None:
        for entry in survey.entries:
            rows.append(
                [
                    entry.name,
                    entry.category,
                    entry.pipeline_mapping or entry.why_it_may_help,
                    entry.decision,
                ]
            )
        # Order by how much the tool actually matters to this pipeline, not
        # alphabetically by decision -- which would otherwise print the rejected
        # tools above the ones the stack is built on.
        decision_order = {"use_now": 0, "optional_later": 1, "reject_for_mvp": 2}
        rows.sort(key=lambda row: (decision_order.get(str(row[3]), 3), str(row[0])))
    else:
        rows = [list(entry) for entry in _FALLBACK_TOOL_STACK]

    lines += [
        md_table(["Tool", "Category", "Role in this pipeline", "Decision"], rows),
        "",
    ]
    if survey_markdown:
        summary = _first_paragraph(survey_markdown)
        if summary:
            lines += [f"Survey summary: {summary}", ""]
        lines += [
            "The full survey, including tools that were considered and rejected, "
            f"is in `{config.DEFAULT_SURVEY_PATH.name}`.",
            "",
        ]
    return lines


def _schema_cross_check_section(result: PipelineResult) -> list[str]:
    report = result.schema_report
    counts = Counter(report.counts_by_queryability)
    lines = [
        "## 4. Schema Cross-Check",
        "",
        f"{report.indicator_count} indicators across {report.rfc_count} RFCs "
        f"were checked against {report.dictionary_field_count} dictionary "
        "fields before any measurement data was read.",
        "",
        md_table(
            ["Queryability", "Indicators", "Share"],
            _counter_rows(counts, report.indicator_count),
        ),
        "",
    ]
    if report.unused_dictionary_fields:
        lines += [
            "Dictionary fields that no indicator references: "
            + ", ".join(f"`{name}`" for name in report.unused_dictionary_fields)
            + ".",
            "",
        ]
    if report.warnings:
        lines += ["Schema warnings:", ""] + _bullets(report.warnings) + [""]
    return lines


def _indicator_sections(result: PipelineResult) -> list[str]:
    report = result.schema_report
    queryable = report.queryable_indicators
    non_queryable = report.non_queryable_indicators
    partial = [
        check for check in report.indicators if check.queryability == "partially_queryable"
    ]
    ambiguous = [check for check in report.indicators if check.queryability == "ambiguous"]

    lines = [
        "## 5. Queryable vs Non-Queryable Indicators",
        "",
        "### 5.1 Queryable indicators",
        "",
    ]
    if queryable:
        lines += [
            md_table(
                ["RFC", "Indicator", "Role", "Weight", "Fields used"],
                [
                    [
                        check.rfc_id,
                        check.indicator_id,
                        "required" if check.required else "optional",
                        check.weight,
                        ", ".join(_indicator_fields(check)),
                    ]
                    for check in queryable
                ],
            ),
            "",
        ]
    else:
        lines += ["No indicator is fully queryable against this dictionary.", ""]

    lines += ["### 5.2 Non-queryable indicators", ""]
    if non_queryable:
        lines += [
            md_table(
                ["RFC", "Indicator", "Missing fields", "Reason"],
                [
                    [
                        check.rfc_id,
                        check.indicator_id,
                        ", ".join(check.missing_fields) or "-",
                        check.reasoning,
                    ]
                    for check in non_queryable
                ],
            ),
            "",
            "These indicators are not scored as failures. They are excluded "
            "from evaluation and raised in the review queue, because a field "
            "the corpus does not carry is an absence of measurement, not "
            "evidence of absence.",
            "",
        ]
    else:
        lines += ["Every indicator's fields exist in the dictionary.", ""]

    if partial or ambiguous:
        lines += ["### 5.3 Partially queryable and ambiguous indicators", ""]
        lines += [
            md_table(
                ["RFC", "Indicator", "Queryability", "Missing fields", "Reason"],
                [
                    [
                        check.rfc_id,
                        check.indicator_id,
                        check.queryability,
                        ", ".join(check.missing_fields) or "-",
                        check.reasoning,
                    ]
                    for check in partial + ambiguous
                ],
            ),
            "",
            "A partially queryable indicator can be evaluated on the fields "
            "that exist, but its verdict is weaker than the checklist intends. "
            "An ambiguous indicator is measurable yet not uniquely attributable "
            "to the RFC that lists it.",
            "",
        ]
    return lines


def _signals_section(result: PipelineResult) -> list[str]:
    first, last = _signal_date_range(result)
    signals = result.signals
    lines = [
        "## 6. Observed OpenINTEL Signals",
        "",
        f"{len(signals)} {_plural(len(signals), 'observation')} were normalized "
        f"from the Parquet input"
        + (f", covering {_date(first)} to {_date(last)}." if first else "."),
        "",
    ]
    if not signals:
        lines += [
            "No observations were extracted, so no positive statement about any "
            "RFC can be made from this run.",
            "",
        ]
        return lines

    domains = {signal.domain for signal in signals if signal.domain}
    zones = {signal.zone for signal in signals if signal.zone}
    rr_types = Counter(
        str(signal.fields.get("rr_type")) for signal in signals if signal.fields.get("rr_type")
    )
    algorithms = Counter(
        str(signal.fields.get("algorithm"))
        for signal in signals
        if signal.fields.get("algorithm") is not None
    )
    lines += _bullets(
        [
            f"Distinct domains: {len(domains)}.",
            f"Distinct zones: {len(zones)}.",
            f"Observations carrying an algorithm number: {sum(algorithms.values())}.",
        ]
    )
    lines += ["", "Resource record types observed:", ""]
    lines += [
        md_table(["Record type", "Observations", "Share"], _counter_rows(rr_types, len(signals))),
        "",
    ]
    if algorithms:
        lines += ["DNSSEC algorithm numbers observed:", ""]
        lines += [
            md_table(
                ["Algorithm", "Observations", "Share"],
                _counter_rows(algorithms, sum(algorithms.values())),
            ),
            "",
        ]
    lines += [
        "Each row is one record-level observation. A zone that publishes "
        "several records appears several times, so observation counts measure "
        "records seen, not zones deployed.",
        "",
    ]
    return lines


def _ranked_section(result: PipelineResult) -> list[str]:
    lines = ["## 7. Ranked RFC Matches", ""]
    candidates = result.ranked_candidates
    if not candidates:
        lines += [
            "No candidate scored above "
            f"{result.run_config.min_score}, so no ranking is reported.",
            "",
        ]
        return lines

    shown = candidates[:TOP_CANDIDATE_ROWS]
    lines += [
        md_table(
            [
                "Rank",
                "RFC",
                "Title",
                "Score",
                "Confidence",
                "Supporting observations",
                "First seen",
            ],
            [
                [
                    candidate.rank,
                    candidate.rfc_id,
                    candidate.rfc_title,
                    candidate.score,
                    candidate.confidence,
                    candidate.supporting_signal_count,
                    _date(candidate.first_seen),
                ]
                for candidate in shown
            ],
        ),
        "",
    ]
    if len(candidates) > len(shown):
        lines += [
            f"{len(candidates) - len(shown)} further candidates are in "
            f"`{config.OUTPUT_FILES['ranked_candidates']}`.",
            "",
        ]
    lines += [
        "Score is the best per-signal score for that RFC, after the "
        "specificity multiplier (very_high 1.5, high 1.25, medium 1.0, "
        "low 0.75) has been applied. A broad RFC with many observations can "
        "therefore rank below a narrow RFC with one unambiguous observation, "
        "which is the intended behaviour: specificity is evidence.",
        "",
    ]
    aggregate_rows = [
        [
            candidate.rfc_id,
            candidate.score,
            candidate.aggregate_score,
            candidate.valid_match_count,
            candidate.partial_match_count,
            candidate.timestamp_invalid_count,
            ", ".join(candidate.matched_indicator_ids) or "-",
        ]
        for candidate in shown
    ]
    lines += [
        "Per-candidate evidence breakdown:",
        "",
        md_table(
            [
                "RFC",
                "Best score",
                "Aggregate score",
                "Valid",
                "Partial",
                "Timestamp-invalid",
                "Matched indicators",
            ],
            aggregate_rows,
        ),
        "",
    ]
    return lines


def _select_evidence_traces(traces: Sequence[ReasoningTrace]) -> list[ReasoningTrace]:
    """Pick two or three traces that together show the reasoning machinery.

    Preference order: the strongest accepted match, a timestamp-invalid
    rejection (required by the report contract), then a partial/ambiguous or
    non-queryable case. Duplicates are dropped and the list is capped at three.
    """
    chosen: list[ReasoningTrace] = []

    def add(trace: ReasoningTrace | None) -> None:
        if trace is not None and all(t.trace_id != trace.trace_id for t in chosen):
            chosen.append(trace)

    valid = [t for t in traces if t.decision == "valid_match"]
    if valid:
        add(max(valid, key=lambda t: (t.score_breakdown.final_score, t.trace_id)))

    invalid = [t for t in traces if t.decision == "timestamp_invalid"]
    if invalid:
        add(max(invalid, key=lambda t: (t.score_breakdown.timestamp_penalty, t.trace_id)))

    other = [
        t for t in traces if t.decision in {"partial_match", "ambiguous", "non_queryable"}
    ]
    if other:
        add(max(other, key=lambda t: (t.score_breakdown.final_score, t.trace_id)))

    if len(chosen) < 2:
        for trace in traces:
            add(trace)
            if len(chosen) >= 2:
                break
    return chosen[:3]


def _reasoning_section(result: PipelineResult) -> list[str]:
    traces = result.traces
    lines = [
        "## 8. Reasoning Summary",
        "",
        f"Every one of the {len(traces)} signal-by-RFC "
        f"{_plural(len(traces), 'evaluation')} carries a stored reasoning "
        "trace: the conditions that passed, the conditions that failed, the "
        "fields that were missing, the timestamp verdict and the arithmetic of "
        "the score. Non-matches are traced too, because the reason an RFC was "
        "*not* selected is as much a result as the reason one was.",
        "",
    ]
    if not traces:
        lines += ["No traces were produced.", ""]
        return lines

    decision_counts = Counter(trace.decision for trace in traces)
    lines += [
        md_table(
            ["Decision", "Traces", "Share"], _counter_rows(decision_counts, len(traces))
        ),
        "",
        "Verbatim reasoning summaries from this run:",
        "",
    ]
    for trace in _select_evidence_traces(traces):
        lines += [
            f"**{trace.trace_id}** - {trace.rfc_id}, signal `{trace.signal_id}`, "
            f"decision `{trace.decision}`, score "
            f"{trace.score_breakdown.final_score}:",
            "",
        ]
        # Never truncated: this is the evidence, not a summary of it.
        lines += _quote(trace.reasoning_summary)
        lines += [""]

    if "timestamp_invalid" not in decision_counts:
        lines += [
            "No observation in this run predates the RFC it would otherwise "
            "have matched, so no timestamp-invalid trace could be quoted here.",
            "",
        ]
    return lines


def _timeline_section(result: PipelineResult) -> list[str]:
    lines = [
        "## 9. First-Seen Dates / Adoption Timeline",
        "",
        "First-seen is the earliest *valid* match: an observation dated at or "
        "after the RFC's publication date. It is the first date this corpus saw "
        "the mechanism, which is an upper bound on when deployment began and "
        "says nothing about deployment before the measurement window.",
        "",
    ]
    entries = result.timeline
    if entries:
        lines += [
            md_table(
                [
                    "RFC",
                    "Published",
                    "First seen",
                    "Last seen",
                    "Days from publication",
                    "Observations",
                    "Distinct domains",
                ],
                [
                    [
                        entry.rfc_id,
                        _date(entry.rfc_publication_date),
                        _date(entry.first_seen),
                        _date(entry.last_seen),
                        entry.days_from_publication_to_first_seen
                        if entry.days_from_publication_to_first_seen is not None
                        else "-",
                        entry.observation_count,
                        entry.distinct_domains,
                    ]
                    for entry in entries
                ],
            ),
            "",
        ]
        buckets = [
            [entry.rfc_id, bucket.period, bucket.count, bucket.domains, bucket.mean_score]
            for entry in entries
            for bucket in entry.monthly_counts
        ]
        if buckets:
            lines += [
                "Monthly observation buckets (valid matches only):",
                "",
                md_table(
                    ["RFC", "Period", "Observations", "Domains", "Mean score"], buckets
                ),
                "",
            ]
    elif result.ranked_candidates:
        lines += [
            "No timeline entries were built; first-seen dates from the ranked "
            "candidates are shown instead.",
            "",
            md_table(
                ["RFC", "Published", "First seen", "Last seen", "Observations"],
                [
                    [
                        candidate.rfc_id,
                        _date(candidate.rfc_publication_date),
                        _date(candidate.first_seen),
                        _date(candidate.last_seen),
                        candidate.supporting_signal_count,
                    ]
                    for candidate in result.ranked_candidates
                ],
            ),
            "",
        ]
    else:
        lines += ["No valid matches, so no adoption timeline could be built.", ""]
    return lines


def _timestamp_section(result: PipelineResult) -> list[str]:
    invalid = _timestamp_invalid_matches(result)
    lines = [
        "## 10. Impossible Timestamp Matches",
        "",
        "An observation that predates the RFC it appears to match cannot be "
        "evidence of that RFC. The indicator conditions may have passed, but "
        "the match is rejected outright, its score is forfeited to zero, and it "
        "is sent to the review queue rather than quietly dropped.",
        "",
    ]
    if not invalid:
        lines += [
            "No match in this run was rejected on publication date.",
            "",
        ]
        return lines

    lines += [
        md_table(
            [
                "Signal",
                "RFC",
                "Observed",
                "RFC published",
                "Forfeited score",
                "Matched indicators",
            ],
            [
                [
                    match.signal_id,
                    match.rfc_id,
                    _date(match.observation_timestamp),
                    _date(match.rfc_publication_date),
                    match.score_breakdown.timestamp_penalty,
                    ", ".join(match.matched_indicator_ids) or "-",
                ]
                for match in invalid
            ],
        ),
        "",
        "The forfeited score is what the match would have scored had the "
        "observation been dated after publication. It is recorded so that a "
        "reviewer can see how strong the rejected evidence was: a large "
        "forfeited score usually means the mechanism predates its own "
        "standardization, which is common - the RFC often documents existing "
        "practice - or that the checklist attributes the indicator to the wrong "
        "document.",
        "",
    ]
    return lines


def _partial_section(result: PipelineResult) -> list[str]:
    partial = [
        match
        for match in result.matches
        if match.decision in {"partial_match", "ambiguous", "non_queryable"}
    ]
    lines = [
        "## 11. Partial / Ambiguous Matches",
        "",
        "A partial match means some but not all required indicators were "
        "satisfied. An ambiguous match means the evidence fits, but the same "
        "observation is equally explained by another RFC. Neither is reported "
        "as adoption.",
        "",
    ]
    if not partial:
        lines += ["No partial, ambiguous or non-queryable matches were produced.", ""]
        return lines
    lines += [
        md_table(
            ["Signal", "RFC", "Decision", "Score", "Missing fields", "Why"],
            [
                [
                    match.signal_id,
                    match.rfc_id,
                    match.decision,
                    match.score,
                    ", ".join(match.missing_fields) or "-",
                    match.reasoning_summary,
                ]
                for match in partial
            ],
        ),
        "",
        "A missing field is not a failed condition: it means the corpus did not "
        "carry the value, so the condition could not be tested at all.",
        "",
    ]
    return lines


def _review_section(result: PipelineResult) -> list[str]:
    items = result.review_items
    lines = [
        "## 12. Review Queue",
        "",
        "The review queue collects everything the pipeline is not entitled to "
        "decide on its own.",
        "",
    ]
    if not items:
        lines += ["The review queue is empty.", ""]
        return lines

    severity_counts = Counter(item.severity for item in items)
    type_counts = Counter(item.item_type for item in items)
    severity_order = {"high": 0, "medium": 1, "low": 2}
    severity_rows = [
        [severity, severity_counts[severity], f"{100.0 * severity_counts[severity] / len(items):.1f}%"]
        for severity in sorted(severity_counts, key=lambda s: severity_order.get(s, 99))
    ]
    lines += [
        "By severity:",
        "",
        md_table(["Severity", "Items", "Share"], severity_rows),
        "",
        "By type:",
        "",
        md_table(["Item type", "Items", "Share"], _counter_rows(type_counts, len(items))),
        "",
    ]
    shown = items[:REVIEW_ITEM_ROWS]
    lines += [
        md_table(
            ["Item", "Type", "Severity", "RFCs", "Reason", "Suggested action"],
            [
                [
                    item.item_id,
                    item.item_type,
                    item.severity,
                    ", ".join(item.affected_rfc_ids) or "-",
                    item.reason,
                    item.suggested_action,
                ]
                for item in shown
            ],
        ),
        "",
    ]
    if len(items) > len(shown):
        lines += [
            f"{len(items) - len(shown)} further items are in "
            f"`{config.OUTPUT_FILES['review_queue']}`.",
            "",
        ]
    return lines


def _limitations_section(result: PipelineResult) -> list[str]:
    report = result.schema_report
    non_queryable = report.non_queryable_indicators
    broad = [
        candidate.rfc_id
        for candidate in result.ranked_candidates
        if candidate.specificity == "low"
    ]
    lines = [
        "## 13. Limitations",
        "",
        LIMITATION_SENTENCE,
        "",
    ]
    limitations = [
        "**Synthetic sample data.** The measurements in this run come from a "
        "small generated sample corpus built to exercise the matching rules, "
        "not from a production OpenINTEL measurement. Absolute counts and "
        "first-seen dates carry no external meaning.",
        "**A single Parquet file.** One file is one slice of one measurement "
        "campaign. It cannot support statements about global deployment, and "
        "an RFC absent from these results may simply be absent from this file.",
        "**Record-level, not zone-level.** Each observation is one resource "
        "record. The pipeline never aggregates records into a zone-level "
        "verdict, so a zone that publishes many records is over-represented "
        "relative to one that publishes few, and per-zone policy claims (such "
        "as \"this zone avoids deprecated algorithms\") cannot be made from a "
        "single record.",
        "**Indicators the corpus cannot express.** "
        + (
            f"{len(non_queryable)} "
            f"{_plural(len(non_queryable), 'indicator')} "
            f"({', '.join(check.indicator_id for check in non_queryable)}) "
            + ("references" if len(non_queryable) == 1 else "reference")
            + " fields that do not exist in the OpenINTEL dictionary, "
            "typically resolver-side behaviour. They are neither confirmed nor "
            "refuted here."
            if non_queryable
            else "Every indicator in this checklist is expressible in the "
            "dictionary, which is a property of this checklist rather than a "
            "general guarantee."
        ),
        "**Broad base-DNSSEC RFCs match almost any signed zone.** RFC 4033 and "
        "its companions are matched by the presence of any DNSSEC record, so "
        "they will match nearly every signed zone regardless of what else the "
        "operator has deployed. Their low specificity multiplier deliberately "
        "keeps them below mechanism-specific RFCs"
        + (f" (affected here: {', '.join(sorted(set(broad)))})" if broad else "")
        + "; a match on them should be read as \"this zone is signed\", not as "
        "adoption of a specific mechanism.",
        "**Ambiguity is structural, not incidental.** Recommendation documents "
        "such as RFC 8624 register nothing observable of their own. Any match "
        "against them is an inference about operator policy drawn from "
        "algorithm choice, which is why those indicators are marked ambiguous "
        "and penalized.",
        "**Timestamps bound possibility, not causation.** An observation dated "
        "after publication is consistent with the RFC; it does not show the "
        "operator acted because of the RFC, and many mechanisms were deployed "
        "before the document that describes them was published.",
    ]
    lines += _bullets(limitations)
    lines += [""]
    return lines


def _next_steps_section(result: PipelineResult) -> list[str]:
    report = result.schema_report
    steps = [
        "Run the pipeline against a real OpenINTEL Parquet partition rather "
        "than the sample corpus, and compare the ranking to the sample result "
        "to confirm nothing depends on the generated data.",
        "Aggregate observations to zone level before ranking, so that adoption "
        "is counted once per zone instead of once per record.",
        "Work through the review queue: the timestamp-invalid matches and the "
        "missing-required-field partials are the items most likely to indicate "
        "a checklist error rather than a data artefact.",
        "Extend the OpenINTEL dictionary, or drop the indicators that depend on "
        "fields it cannot supply, so the checklist states only what this data "
        "source can be asked.",
        "Add RFC obsoletes/updates relationships to the ranking so that a "
        "superseded document does not compete with the one that replaced it.",
        "Validate a sample of the top-ranked candidates against zone data or "
        "operator statements; that is the step this pipeline is explicitly not "
        "a substitute for.",
    ]
    if report.warnings or result.warnings:
        steps.insert(
            0,
            f"Resolve the {len(set(list(result.warnings) + list(report.warnings)))} "
            "warning(s) recorded in `run_manifest.json`; each one marks a place "
            "where the run degraded rather than failed.",
        )
    return ["## 14. Next Steps", ""] + _bullets(steps) + [""]


def _warnings_appendix(result: PipelineResult) -> list[str]:
    merged: dict[str, None] = {}
    for message in list(result.warnings) + list(result.schema_report.warnings):
        merged.setdefault(message, None)
    if not merged:
        return []
    return ["## Appendix A. Warnings", ""] + _bullets(merged) + [""]


# --------------------------------------------------------------------------- #
# Analysis report
# --------------------------------------------------------------------------- #


def render_report(result: PipelineResult, *, survey_markdown: str | None = None) -> str:
    """Render ``report.md`` for one completed ``analyze`` run.

    ``survey_markdown`` is the generated open-source tool survey, if one exists
    on disk; it is summarized in Section 3 rather than inlined, so that the
    report's own section numbering stays intact.
    """
    first, last = _signal_date_range(result)
    header = [
        "# OpenINTEL RFC Adoption Analysis",
        "",
        f"Generated: {iso(result.generated_at)}  ",
        f"Pipeline: {config.PIPELINE_NAME} {config.PIPELINE_VERSION}  ",
        f"Observation window: {_date(first)} to {_date(last)}"
        if first
        else "Observation window: none",
        "",
        "This report identifies ranked RFC candidates that are consistent with "
        "the observed OpenINTEL signals. Read Section 13 before quoting any "
        "number from it.",
        "",
    ]

    sections: list[list[str]] = [
        _executive_summary(result),
        _inputs_section(result),
        _tool_stack_section(survey_markdown),
        _schema_cross_check_section(result),
        _indicator_sections(result),
        _signals_section(result),
        _ranked_section(result),
        _reasoning_section(result),
        _timeline_section(result),
        _timestamp_section(result),
        _partial_section(result),
        _review_section(result),
        _limitations_section(result),
        _next_steps_section(result),
        _warnings_appendix(result),
    ]

    lines = list(header)
    for section in sections:
        lines.extend(section)
    return "\n".join(lines).rstrip() + "\n"
