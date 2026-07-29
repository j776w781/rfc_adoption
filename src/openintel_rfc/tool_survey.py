"""Curated open-source tool survey for the OpenINTEL RFC-adoption pipeline.

The survey is a *build artefact*, not prose: the shortlist below is data, and
``docs/open_source_tool_survey.md`` is rendered from it. Keeping the document
generated means the recommendation, the dependency list in ``requirements.txt``
and the module mapping cannot silently drift apart.

Honesty about provenance
------------------------
This module performs **no network access**. Rendering is a pure function of
:data:`CURATED_TOOLS`. The shortlist itself was researched with live web search
and direct fetches of upstream project pages on the date recorded in
:data:`RESEARCH_DATE`; the concrete facts retrieved on that day are listed
verbatim in :data:`LIVE_VERIFICATION_LOG` and rendered into the document, so a
reader can tell exactly what was checked and when rather than taking "we looked
it up" on trust.

``build_survey(live_search_performed=...)`` therefore describes *the run that
produced the file*, and defaults to ``False``: a plain ``generate_survey()``
call reads no sockets. A caller (typically the CLI) that has genuinely re-run
the searches may pass ``live_search_performed=True`` together with its own
``search_note``.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from . import config
from .models import ToolSurvey, ToolSurveyEntry
from .utils import now, write_text

__all__ = [
    "RESEARCH_DATE",
    "DEFAULT_SEARCH_NOTE",
    "LIVE_VERIFICATION_LOG",
    "CATEGORY_ORDER",
    "CURATED_TOOLS",
    "MVP_REQUIREMENTS",
    "EXECUTIVE_SUMMARY",
    "RISKS",
    "build_survey",
    "render_markdown",
    "generate_survey",
]


# --------------------------------------------------------------------------- #
# Provenance
# --------------------------------------------------------------------------- #

#: Day on which the shortlist was last checked against upstream sources.
RESEARCH_DATE: date = date(2026, 7, 29)

DEFAULT_SEARCH_NOTE: str = (
    "No live search was performed by this run. The document is rendered offline "
    "from the curated shortlist in openintel_rfc/tool_survey.py, which was "
    f"researched against upstream sources on {RESEARCH_DATE.isoformat()} using web "
    "search plus direct fetches of the PyPI project pages, the DuckDB Parquet "
    "documentation, the IETF Datatracker API notes and the Evidence repository. "
    "Every version number, release date and licence quoted below comes from that "
    "session and is reproduced verbatim in the verification log; nothing here is "
    "inferred. Versions move, so treat the log as a dated observation rather than "
    "as the current state of the ecosystem, and re-run the survey before relying "
    "on it for a dependency decision."
)

#: Facts actually retrieved on :data:`RESEARCH_DATE`, one line per observation.
#: Kept as literal strings so the document reports what was seen, not what the
#: author remembered.
LIVE_VERIFICATION_LOG: tuple[str, ...] = (
    "duckdb 1.5.5, released 2026-07-22, MIT, requires Python >=3.10 "
    "(pypi.org/project/duckdb/).",
    "DuckDB Parquet documentation confirms read_parquet with glob patterns and file "
    "lists, projection pushdown, filter pushdown using file zonemaps, "
    "hive_partitioning, union_by_name, parquet_schema/parquet_metadata inspection "
    "and HTTPS reads (duckdb.org/docs/current/data/parquet/overview.html).",
    "pyarrow 25.0.0, released 2026-07-10, Apache-2.0 (pypi.org/project/pyarrow/).",
    "pandas 3.0.5, released 2026-07-22, BSD-3-Clause (pypi.org/project/pandas/). The "
    "pipeline is developed against the pandas 2.2.x series.",
    "polars 1.43.1, released 2026-07-27, MIT (pypi.org/project/polars/).",
    "pydantic 2.13.4, released 2026-05-06, MIT (pypi.org/project/pydantic/).",
    "pandera 0.32.1, released 2026-06-29, MIT (pypi.org/project/pandera/); the 0.32.0 "
    "series introduced a Narwhals-backed engine, so the backend story is still moving.",
    "great-expectations 1.19.1, released 2026-07-24, Apache-2.0, sdist 36.3 MB / wheel "
    "4.9 MB, requires Python >=3.10,<3.14 (pypi.org/project/great-expectations/).",
    "streamlit 1.60.0, released 2026-07-21, Apache-2.0, requires Python >=3.10 "
    "(pypi.org/project/streamlit/).",
    "plotly 6.9.0, released 2026-07-09, MIT (pypi.org/project/plotly/).",
    "pytest 9.1.1, released 2026-06-19, MIT (pypi.org/project/pytest/).",
    "xml2rfc 3.34.0, released 2026-06-03, BSD-3-Clause, maintained under the "
    "ietf-tools organisation, requires Python >=3.10 (pypi.org/project/xml2rfc/). Its "
    "RFCXML v3 grammar (RFC 7991) ships as v3.rnc in ietf-tools/RFCXML.",
    "ietfdata 0.9.0, released 2026-06-24, BSD, actively maintained by Colin Perkins, "
    "but requires Python >=3.13 and caches into local SQLite with an optional ~2 GB "
    "snapshot download (pypi.org/project/ietfdata/).",
    "IETF Datatracker exposes a read-only tastypie API at /api/v1 returning JSON and "
    "XML, plus an unauthenticated per-document endpoint /doc/{docname}/doc.json; "
    "personal API keys are scoped per endpoint and only needed for write endpoints "
    "(datatracker.ietf.org/api/).",
    "langchain 1.3.14, released 2026-07-16, MIT (pypi.org/project/langchain/).",
    "llama-index 0.14.23, released 2026-06-24, MIT (pypi.org/project/llama-index/).",
    "docling 2.116.0, released 2026-07-29, MIT (pypi.org/project/docling/). Local "
    "models pull torch >=2.2.2,<3.0.0 through docling-ibm-models, which also requires "
    "transformers, torchvision, accelerate, safetensors and huggingface_hub; the "
    "docling-slim core is documented at roughly 50 MB before those extras.",
    "apache-superset 6.1.0, released 2026-05-13, Apache-2.0, Python >=3.10 with "
    "classifiers up to 3.12 (pypi.org/project/apache-superset/).",
    "Evidence (github.com/evidence-dev/evidence) is MIT licensed and builds on DuckDB, "
    "but is a Node/npm build toolchain rather than a Python library; the release "
    "version could not be confirmed from the repository landing page and is therefore "
    "not quoted here.",
    "OpenINTEL publishes its measurement archive as Parquet (having migrated from "
    "Avro) and documents the columns in a public data dictionary, noting that the "
    "schema evolved over time so not every field is present in every file "
    "(openintel.nl/data/dictionary/).",
)


# --------------------------------------------------------------------------- #
# Curated shortlist
# --------------------------------------------------------------------------- #

#: Category rendering order. Entries sort by (category position, name) so the
#: document is byte-stable across runs.
CATEGORY_ORDER: tuple[str, ...] = (
    "Parquet / analytics engine",
    "Schema and validation",
    "RFC metadata and text",
    "LLM structured extraction",
    "Dashboard and visualization",
    "Testing",
)

CURATED_TOOLS: list[ToolSurveyEntry] = [
    # ---- Parquet / analytics engine ---- #
    ToolSurveyEntry(
        name="DuckDB",
        category="Parquet / analytics engine",
        url="https://duckdb.org/",
        docs_url="https://duckdb.org/docs/stable/data/parquet/overview",
        why_it_may_help=(
            "In-process SQL engine that reads Parquet directly, with projection and "
            "filter pushdown, glob/multi-file scans, hive partitioning, union_by_name "
            "for schemas that changed between measurement generations, and "
            "parquet_schema() for introspecting a file before reading it. That last "
            "point matters here: the schema checker needs to know which OpenINTEL "
            "columns actually exist in a given file, not which ones the dictionary "
            "claims."
        ),
        decision="use_now",
        decision_rationale=(
            "Only the columns the queryable indicators reference are read, so a large "
            "OpenINTEL partition costs roughly what the selected columns cost rather "
            "than what the file costs. Single file, no server, MIT licence, and "
            "already installed in the target environment."
        ),
        pipeline_mapping=(
            "parquet_reader.py - default engine; builds the SELECT over resolved "
            "native column aliases and applies the row limit."
        ),
        pypi_package="duckdb>=0.10",
        risks=(
            "Single-node and memory-bound on very wide aggregations. The Parquet "
            "reader was rewritten in the 1.3 series, so behaviour on unusual files can "
            "differ across versions; the pandas/pyarrow fallback path exists partly to "
            "cross-check that."
        ),
    ),
    ToolSurveyEntry(
        name="PyArrow",
        category="Parquet / analytics engine",
        url="https://arrow.apache.org/",
        docs_url="https://arrow.apache.org/docs/python/parquet.html",
        why_it_may_help=(
            "Reference Parquet implementation for Python. Reads file metadata and the "
            "column schema without materializing row groups, and is the engine pandas "
            "uses under read_parquet. Also the interchange format DuckDB uses when "
            "handing results to pandas."
        ),
        decision="use_now",
        decision_rationale=(
            "Needed regardless: it backs the pandas fallback reader, and schema "
            "introspection through pyarrow.parquet.ParquetFile is how the reader "
            "discovers which native OpenINTEL columns are present before deciding "
            "which aliases to resolve. Not an optional add-on."
        ),
        pipeline_mapping=(
            "parquet_reader.py - schema introspection and the pandas-engine read path; "
            "also the sample Parquet writer under data/sample_parquet/."
        ),
        pypi_package="pyarrow>=14.0",
        risks=(
            "Large wheels (tens of MB). Major versions land frequently; pin a floor "
            "rather than an exact version."
        ),
    ),
    ToolSurveyEntry(
        name="pandas",
        category="Parquet / analytics engine",
        url="https://pandas.pydata.org/",
        docs_url="https://pandas.pydata.org/docs/reference/io.html",
        why_it_may_help=(
            "Universal in-memory table type. Everything downstream - CSV export, the "
            "dashboard tables, the timeline aggregation - is easier to express against "
            "a DataFrame than against raw dicts, and both DuckDB and PyArrow convert "
            "to one cheaply."
        ),
        decision="use_now",
        decision_rationale=(
            "It is the lingua franca between the reader, the exporters and Streamlit. "
            "Using anything else at the boundary would mean converting at every hop."
        ),
        pipeline_mapping=(
            "parquet_reader.py, exporters.py, dashboard/ - fallback read engine, CSV "
            "writing, and the tables the dashboard renders."
        ),
        pypi_package="pandas>=2.0",
        risks=(
            "Memory-hungry relative to Arrow-native engines; the row limit in "
            "RunConfig exists for that reason. pandas 3.0 is now the current release "
            "while this pipeline is developed against 2.2.x - the code deliberately "
            "sticks to long-stable APIs (read_parquet, to_csv, itertuples) that the "
            "3.0 string-dtype and copy-on-write changes do not alter."
        ),
    ),
    ToolSurveyEntry(
        name="Polars",
        category="Parquet / analytics engine",
        url="https://pola.rs/",
        docs_url=(
            "https://docs.pola.rs/api/python/stable/reference/api/polars.scan_parquet.html"
        ),
        why_it_may_help=(
            "scan_parquet gives a lazy frame with predicate and projection pushdown "
            "and a multi-threaded Rust execution engine; it is consistently the "
            "faster option once a scan runs into multiple gigabytes."
        ),
        decision="optional_later",
        decision_rationale=(
            "It would duplicate what DuckDB already does for this workload, and it is "
            "not installed in the target environment, so importing it unconditionally "
            "would break the demo. Worth revisiting only when a run spans many "
            "OpenINTEL day-partitions and the DuckDB path becomes the bottleneck - at "
            "which point it slots in behind the same reader interface."
        ),
        pipeline_mapping=(
            "parquet_reader.py - would become a third engine choice alongside "
            "'duckdb' and 'pandas' in RunConfig.engine."
        ),
        pypi_package="polars>=0.20",
        risks=(
            "Second DataFrame dialect to maintain alongside pandas; API still moves "
            "faster than pandas'. Must stay behind a guarded import."
        ),
    ),
    # ---- Schema and validation ---- #
    ToolSurveyEntry(
        name="Pydantic",
        category="Schema and validation",
        url="https://pydantic.dev/",
        docs_url="https://pydantic.dev/docs/validation/latest/get-started/",
        why_it_may_help=(
            "Declarative typed models with strict extra-key rejection, so a typo in a "
            "hand-edited RFC checklist fails at load time with a pointer to the "
            "offending key instead of producing a silently unmatched indicator. Also "
            "gives free, stable JSON serialization for every output artefact."
        ),
        decision="use_now",
        decision_rationale=(
            "The checklist and dictionary are hand-maintained JSON; that is exactly "
            "the input class where loud validation pays for itself. The same models "
            "then define the on-disk contract the dashboard reads."
        ),
        pipeline_mapping=(
            "models.py - every model in the pipeline; checklist_loader.py and "
            "schema_checker.py parse JSON straight into them."
        ),
        pypi_package="pydantic>=2.5",
        risks=(
            "extra='forbid' means a future OpenINTEL dictionary key breaks the load "
            "rather than being ignored. That is the intended trade, but it makes "
            "input-format changes a code change."
        ),
    ),
    ToolSurveyEntry(
        name="Pandera",
        category="Schema and validation",
        url="https://github.com/unionai-oss/pandera",
        docs_url="https://pandera.readthedocs.io/en/stable/",
        why_it_may_help=(
            "Validates DataFrames rather than objects: column presence, dtypes, "
            "nullability and value ranges on the frame that comes out of the Parquet "
            "reader, before it is normalized into signals."
        ),
        decision="optional_later",
        decision_rationale=(
            "Genuinely complementary to Pydantic rather than redundant - it covers the "
            "frame-shaped stage Pydantic does not see. It is deferred only because the "
            "reader already resolves aliases against the dictionary and records "
            "missing fields explicitly, so the failure mode Pandera guards against is "
            "currently caught and reported by the schema checker. It is also not "
            "installed in the target environment."
        ),
        pipeline_mapping=(
            "parquet_reader.py - would validate the raw frame between read and "
            "normalization into ObservedSignal."
        ),
        pypi_package="pandera>=0.18",
        risks=(
            "Backend churn: the 0.32 series moved onto a Narwhals-based engine, so "
            "pinning matters. Adds a second schema vocabulary next to the dictionary "
            "JSON, which then has to be kept in step with it."
        ),
    ),
    ToolSurveyEntry(
        name="Great Expectations",
        category="Schema and validation",
        url="https://greatexpectations.io/",
        docs_url="https://docs.greatexpectations.io/",
        why_it_may_help=(
            "Expectation suites, validation results as first-class artefacts, and "
            "generated data-quality documentation - the mature answer for recurring "
            "production data-quality monitoring."
        ),
        decision="reject_for_mvp",
        decision_rationale=(
            "Concretely: it is a 36.3 MB source distribution whose operating model is "
            "a persistent Data Context with configured stores, checkpoints and "
            "datasource definitions on disk. That is infrastructure for a scheduled "
            "pipeline, and this is a single-shot CLI whose entire state is the output "
            "directory. It would roughly double the install and add a second "
            "configuration surface to explain, in exchange for validation that "
            "schema_checker.py already performs against the dictionary and reports in "
            "the schema-check artefacts."
        ),
        pipeline_mapping=(
            "None. Its role would overlap schema_checker.py and any future Pandera "
            "checks in parquet_reader.py."
        ),
        pypi_package="great-expectations",
        risks=(
            "Not applicable for the MVP. If adopted later it brings a stateful "
            "context directory that must be version-controlled and migrated across "
            "major releases."
        ),
    ),
    # ---- RFC metadata and text ---- #
    ToolSurveyEntry(
        name="IETF Datatracker API",
        category="RFC metadata and text",
        url="https://datatracker.ietf.org/",
        docs_url="https://datatracker.ietf.org/api/",
        why_it_may_help=(
            "Authoritative RFC metadata: publication date, status, obsoletes/updates "
            "relations, working group. Publication date is not cosmetic here - it is "
            "the cutoff the timestamp rule tests against, so its provenance is a "
            "correctness question. The read-only /api/v1 endpoints and the "
            "per-document /doc/{docname}/doc.json need no authentication."
        ),
        decision="optional_later",
        decision_rationale=(
            "The natural second backend for rfc_metadata.py, which is written against "
            "an interface precisely so this can be added. Deferred because a network "
            "call in a default code path is forbidden by the build contract and would "
            "make runs non-reproducible; the eight checklist RFCs carry their "
            "publication dates inline and those are trivially auditable by hand."
        ),
        pipeline_mapping=(
            "rfc_metadata.py - an additional backend behind the existing resolver, "
            "populating RFCMetadata.source='datatracker'."
        ),
        pypi_package=None,
        risks=(
            "Introduces network dependence, latency and an availability failure mode "
            "into a pipeline that is currently offline and deterministic. Needs a "
            "local cache and an explicit opt-in flag before it is usable."
        ),
    ),
    ToolSurveyEntry(
        name="RFC Editor RFCXML v3",
        category="RFC metadata and text",
        url="https://www.rfc-editor.org/info/rfc7991/",
        docs_url="https://ietf-tools.github.io/xml2rfc/",
        why_it_may_help=(
            "The RFC 7991 vocabulary marks up sections, requirement keywords and "
            "references structurally. Parsing it would let checklist indicators be "
            "traced to the specific normative sentence they encode, instead of the "
            "prose description a human typed into the checklist."
        ),
        decision="optional_later",
        decision_rationale=(
            "This is the most valuable future direction for the checklist itself: it "
            "turns indicator authoring from an editorial exercise into a "
            "document-grounded one. It is out of MVP scope because it is a research "
            "task, not an integration - mapping normative text to an observable "
            "Parquet predicate is the hard part, and no parser does that step."
        ),
        pipeline_mapping=(
            "data/rfc_checklists/ - a provenance field per indicator citing the RFC "
            "section it derives from; consumed by rfc_metadata.py."
        ),
        pypi_package=None,
        risks=(
            "Older RFCs only exist as v2 XML or plain text, so coverage is uneven "
            "across the DNSSEC corpus this pipeline cares about."
        ),
    ),
    ToolSurveyEntry(
        name="xml2rfc",
        category="RFC metadata and text",
        url="https://github.com/ietf-tools/xml2rfc",
        docs_url="https://ietf-tools.github.io/xml2rfc/",
        why_it_may_help=(
            "The reference implementation of the v2/v3 vocabularies, maintained under "
            "the ietf-tools organisation. Ships the RelaxNG grammar and can convert v2 "
            "documents to v3, which is the practical way to normalize an older RFC "
            "before parsing it."
        ),
        decision="optional_later",
        decision_rationale=(
            "It is a document *renderer* first - its job is producing formatted RFCs, "
            "not exposing a query API over their structure. For extraction it is "
            "useful mainly for its v2-to-v3 conversion and its grammar; the actual "
            "traversal would be lxml against the converted tree. Only worth pulling in "
            "once the RFCXML provenance work above is actually started."
        ),
        pipeline_mapping=(
            "Offline checklist-authoring tooling; would not be imported by the runtime "
            "pipeline."
        ),
        pypi_package="xml2rfc",
        risks=(
            "Heavier than a parser needs to be, and oriented toward rendering rather "
            "than structured extraction."
        ),
    ),
    ToolSurveyEntry(
        name="ietfdata",
        category="RFC metadata and text",
        url="https://github.com/glasgow-ipl/ietfdata",
        docs_url="https://pypi.org/project/ietfdata/",
        why_it_may_help=(
            "A typed Python client over the Datatracker and the RFC index, with a "
            "local SQLite cache, which is a considerably better starting point than "
            "hand-rolling HTTP against /api/v1."
        ),
        decision="optional_later",
        decision_rationale=(
            "Blocked on a concrete incompatibility rather than a preference: the "
            "current release requires Python >=3.13, while this project targets >=3.10 "
            "and is developed on 3.12. Adopting it now would raise the floor for the "
            "whole pipeline for the sake of one optional backend. Revisit if and when "
            "the project's Python floor moves."
        ),
        pipeline_mapping=(
            "rfc_metadata.py - would implement the datatracker backend rather than "
            "calling the HTTP API directly."
        ),
        pypi_package="ietfdata",
        risks=(
            "Python >=3.13 floor; an optional bulk snapshot on the order of 2 GB; a "
            "small single-maintainer project, which is fine for research use but is a "
            "bus-factor consideration for anything load-bearing."
        ),
    ),
    # ---- LLM structured extraction ---- #
    ToolSurveyEntry(
        name="LangChain structured output",
        category="LLM structured extraction",
        url="https://github.com/langchain-ai/langchain",
        docs_url="https://docs.langchain.com/oss/python/langchain/structured-output",
        why_it_may_help=(
            "with_structured_output binds a Pydantic model to a model call and returns "
            "a validated instance. Since LLMVerification is already a Pydantic model, "
            "an LLM backend for the review queue is close to a drop-in: same schema, "
            "different producer."
        ),
        decision="optional_later",
        decision_rationale=(
            "The verifier interface was designed for this, and the MVP ships a "
            "deterministic rule-based backend behind it. It stays optional because a "
            "non-deterministic component in the default path would undermine the "
            "reproducibility the reasoning traces are supposed to provide, and because "
            "an API key requirement would break the offline demo."
        ),
        pipeline_mapping=(
            "llm_verifier.py - an alternative backend producing LLMVerification, "
            "selected explicitly rather than by default."
        ),
        pypi_package="langchain",
        risks=(
            "Large transitive dependency tree and a fast-moving API across major "
            "versions. Any LLM verdict must stay advisory and be recorded as such in "
            "the review item, never allowed to overwrite a deterministic score."
        ),
    ),
    ToolSurveyEntry(
        name="LlamaIndex",
        category="LLM structured extraction",
        url="https://github.com/run-llama/llama_index",
        docs_url=(
            "https://developers.llamaindex.ai/python/framework/module_guides/querying/"
            "structured_outputs/"
        ),
        why_it_may_help=(
            "Pydantic programs map a prompt to a typed object, and the indexing side "
            "would matter if RFC full text were ever retrieved to justify a match."
        ),
        decision="optional_later",
        decision_rationale=(
            "Overlaps LangChain for the one thing the pipeline would need it for - "
            "producing a validated LLMVerification. Its differentiator is retrieval "
            "over a document corpus, which only becomes relevant alongside the RFCXML "
            "work. Adopting both would be redundant; pick one at that point."
        ),
        pipeline_mapping=(
            "llm_verifier.py - alternative to the LangChain backend; would also serve "
            "RFC-text retrieval if that is ever built."
        ),
        pypi_package="llama-index",
        risks=(
            "Broad dependency surface and frequent releases in the 0.x line, meaning "
            "no stability guarantee across minor versions."
        ),
    ),
    ToolSurveyEntry(
        name="Docling",
        category="LLM structured extraction",
        url="https://github.com/docling-project/docling",
        docs_url="https://docling-project.github.io/docling/",
        why_it_may_help=(
            "Converts PDF and other documents into structured, machine-readable form "
            "with layout understanding - the right tool if RFC PDFs had to be mined."
        ),
        decision="reject_for_mvp",
        decision_rationale=(
            "Two independent reasons. First, the input does not exist: RFCs are "
            "available as XML, HTML and plain text, so document layout analysis solves "
            "a problem this pipeline does not have. Second, the cost is concrete - "
            "local models pull torch >=2.2.2,<3.0.0 via docling-ibm-models, together "
            "with transformers, torchvision, accelerate and huggingface_hub, which is "
            "a multi-gigabyte install and a model-download step attached to a project "
            "whose entire runtime footprint is otherwise a few DataFrame libraries."
        ),
        pipeline_mapping="None.",
        risks=(
            "Not applicable for the MVP. If document ingestion is ever needed, prefer "
            "the docling-slim core without OCR or VLM extras, and treat it as an "
            "offline authoring tool rather than a runtime dependency."
        ),
    ),
    # ---- Dashboard and visualization ---- #
    ToolSurveyEntry(
        name="Streamlit",
        category="Dashboard and visualization",
        url="https://streamlit.io/",
        docs_url="https://docs.streamlit.io/develop/concepts/multipage-apps",
        why_it_may_help=(
            "Multipage apps map cleanly onto the artefacts this pipeline emits - one "
            "page per concern (overview, ranked candidates, reasoning traces, review "
            "queue, timeline, schema check) - and it is plain Python, so a page can "
            "load the same Pydantic models the pipeline wrote."
        ),
        decision="use_now",
        decision_rationale=(
            "The dashboard is a management surface, not a report: the review queue "
            "needs mutable per-item state written back to disk. That is application "
            "logic, which rules out declarative BI tools and is trivial in Streamlit."
        ),
        pipeline_mapping=(
            "dashboard/app.py + dashboard/pages/* - reads the JSON artefacts named in "
            "config.OUTPUT_FILES and writes review_queue_status.json."
        ),
        pypi_package="streamlit>=1.30",
        risks=(
            "Re-runs the whole script on every interaction, so artefact loading must "
            "be cached. Single-user by design - concurrent reviewers would clobber "
            "each other's review-queue state."
        ),
    ),
    ToolSurveyEntry(
        name="Plotly",
        category="Dashboard and visualization",
        url="https://plotly.com/python/",
        docs_url="https://plotly.com/python/",
        why_it_may_help=(
            "Interactive charts that render natively in Streamlit via "
            "st.plotly_chart, with hover text - which is what makes an adoption "
            "timeline readable, since the interesting quantity is usually the gap "
            "between RFC publication and first observation."
        ),
        decision="use_now",
        decision_rationale=(
            "Highest-quality interactive output for the least code, no build step, and "
            "already installed. Matplotlib would be static; a JS charting library "
            "would need a bundler."
        ),
        pipeline_mapping=(
            "dashboard/pages/* - timeline charts from adoption_timeline.json, score "
            "distributions from rfc_matches.json, ranking bars from "
            "ranked_candidates.json."
        ),
        pypi_package="plotly>=5.18",
        risks=(
            "Bundles a large JavaScript payload into each page. Figures with tens of "
            "thousands of points get sluggish in the browser, so aggregate before "
            "plotting."
        ),
    ),
    ToolSurveyEntry(
        name="Apache Superset",
        category="Dashboard and visualization",
        url="https://superset.apache.org/",
        docs_url="https://superset.apache.org/docs/intro",
        why_it_may_help=(
            "A full BI platform with saved charts, dashboards, role-based access and "
            "SQL Lab, and it can sit on DuckDB, so it could point straight at the same "
            "Parquet corpus."
        ),
        decision="optional_later",
        decision_rationale=(
            "It solves multi-user exploration, which is a real need once results are "
            "shared beyond one researcher. It is not the MVP answer because it is a "
            "deployed service: a metadata database, a web server, a worker and an "
            "async cache, versus 'python -m streamlit run'. It also cannot host the "
            "review-queue workflow, since that needs custom write-back logic."
        ),
        pipeline_mapping=(
            "Would consume the exported artefacts or the Parquet corpus directly; no "
            "module in src/openintel_rfc/ would depend on it."
        ),
        pypi_package="apache-superset",
        risks=(
            "Substantial operational burden for a single-researcher project, and a "
            "narrower supported Python range than the rest of this stack."
        ),
    ),
    ToolSurveyEntry(
        name="Evidence.dev",
        category="Dashboard and visualization",
        url="https://evidence.dev/",
        docs_url="https://docs.evidence.dev/",
        why_it_may_help=(
            "SQL-and-Markdown reports built on DuckDB, compiled to a static site. A "
            "good fit for publishing a fixed, citable adoption report alongside a "
            "paper."
        ),
        decision="optional_later",
        decision_rationale=(
            "Complements rather than replaces the Streamlit dashboard: static "
            "publication versus interactive triage. Deferred because it introduces a "
            "Node and npm toolchain into an otherwise pure-Python project, and because "
            "report.md already covers the 'fixed narrative artefact' need for now."
        ),
        pipeline_mapping=(
            "Would render from the exported artefacts; an alternative to report.md, "
            "not a library dependency."
        ),
        pypi_package=None,
        risks=(
            "Second language toolchain to install and keep current. Static output "
            "cannot support the review-queue write-back workflow."
        ),
    ),
    # ---- Testing ---- #
    ToolSurveyEntry(
        name="pytest",
        category="Testing",
        url="https://github.com/pytest-dev/pytest",
        docs_url="https://docs.pytest.org/",
        why_it_may_help=(
            "Plain-function tests, fixtures for the sample Parquet and checklist "
            "inputs, and parametrization - which is how the seven condition operators "
            "and the worked scoring cases from the build contract are best expressed."
        ),
        decision="use_now",
        decision_rationale=(
            "The scoring formula and the decision-state machine are the parts of this "
            "pipeline where a silent regression would be least visible and most "
            "damaging, since a wrong score still looks like a plausible score. They "
            "need executable expectations."
        ),
        pipeline_mapping=(
            "tests/ - operator semantics, scoring arithmetic, timestamp cutoff, "
            "decision rules, exporter round-trips and the worked demo cases."
        ),
        pypi_package="pytest>=7.4",
        risks=(
            "None material. Test data must stay small enough to commit, which is why "
            "the sample Parquet is generated rather than vendored."
        ),
    ),
]


# --------------------------------------------------------------------------- #
# Narrative blocks
# --------------------------------------------------------------------------- #

EXECUTIVE_SUMMARY: str = (
    "This pipeline reads OpenINTEL Parquet measurements, normalizes them into DNS/"
    "DNSSEC signals, evaluates those signals against an RFC indicator checklist, and "
    "emits ranked RFC candidates with an explicit reasoning trace behind every "
    "decision. The tooling question is therefore narrower than it first appears: the "
    "hard parts - indicator semantics, the publication-date cutoff, the scoring "
    "arithmetic, the decision-state machine - are domain logic that no library "
    "supplies. What the stack has to do is read columnar files efficiently, validate "
    "hand-maintained JSON loudly, and render the results so a human can audit them.\n\n"
    "The recommendation is a deliberately small stack: DuckDB and PyArrow for Parquet, "
    "pandas as the interchange table type, Pydantic for typed inputs and outputs, "
    "Streamlit and Plotly for the dashboard, and pytest for the test suite. All seven "
    "are already present in the target environment, all are permissively licensed "
    "(MIT, Apache-2.0 or BSD-3-Clause), and together they add no service, no daemon "
    "and no network dependency.\n\n"
    "Everything else is deferred rather than dismissed, and the deferrals are "
    "architectural rather than arbitrary: rfc_metadata.py is written against an "
    "interface so a Datatracker or ietfdata backend can be added, and llm_verifier.py "
    "ships a deterministic backend behind the interface an LLM backend would "
    "implement. Two tools are rejected outright for the MVP - Great Expectations and "
    "Docling - in both cases because their cost is concrete and their benefit is "
    "already covered or not yet applicable. The governing constraint throughout is "
    "reproducibility: this is research code whose output has to be defensible, so no "
    "dependency may introduce a network call or a non-deterministic result into a "
    "default code path."
)

RISKS: tuple[str, ...] = (
    "Reproducibility over convenience. Every tool that would put a network call or a "
    "sampled model output into a default code path is deferred, including the "
    "Datatracker backend and both LLM frameworks. The cost is that RFC publication "
    "dates are transcribed by hand into the checklist and must be audited there; the "
    "benefit is that two runs over the same inputs produce identical bytes.",
    "Single-node ceiling. DuckDB plus pandas is comfortable for a day-partition of "
    "OpenINTEL data and will not stay comfortable across a multi-year corpus. The "
    "mitigation is structural rather than speculative: RunConfig.engine already selects "
    "between backends, so Polars becomes an added branch rather than a rewrite.",
    "Version drift in the recorded facts. Every version and licence in this document "
    "was read from upstream on a single day. DuckDB rewrote its Parquet reader within "
    "the 1.x line, pandas has since moved to 3.0, and Pandera changed its backend in a "
    "0.0.x step - none of which are hypothetical. Re-run the survey before treating "
    "these numbers as current.",
    "pandas major-version boundary. The floor is pandas>=2.0 while the current release "
    "is 3.0.x and development happens on 2.2.x. Only long-stable APIs are used, so the "
    "copy-on-write and string-dtype changes should not bite, but this is the single "
    "most likely source of an environment-dependent failure and is worth an explicit "
    "CI job on both series.",
    "Guarded imports are a rule, not a style preference. Polars and Pandera are absent "
    "from the target environment. Any code that touches them must import inside the "
    "function that needs them and degrade with an explicit message, or the demo stops "
    "running end-to-end on a clean install.",
    "Dashboard concurrency. Streamlit's review-queue write-back assumes one reviewer. "
    "Two people triaging simultaneously will overwrite each other's decisions in "
    "review_queue_status.json; multi-user review needs a real store, not a JSON file.",
    "Deferral is not free. rfc_metadata.py and llm_verifier.py each carry an interface "
    "whose only implementation is the trivial one. That indirection is justified by the "
    "specific backends named here, and should be collapsed rather than kept for its own "
    "sake if those backends are never built.",
)

MVP_REQUIREMENTS: tuple[tuple[str, str], ...] = (
    ("pandas>=2.0", "DataFrame handling, CSV/JSON export, dashboard tables"),
    ("pyarrow>=14.0", "Parquet IO and Arrow interop (also pandas' parquet engine)"),
    ("duckdb>=0.10", "Default query engine: SQL with projection pushdown over Parquet"),
    ("pydantic>=2.5", "Typed models for checklists, signals, matches, reasoning traces"),
    ("streamlit>=1.30", "Multipage management + visualization dashboard"),
    ("plotly>=5.18", "Interactive charts inside the dashboard"),
    ("pytest>=7.4", "Test suite"),
)

OPTIONAL_REQUIREMENTS: tuple[tuple[str, str], ...] = (
    ("polars>=0.20", "Lazy Parquet scans if the corpus outgrows DuckDB single-node"),
    ("pandera>=0.18", "DataFrame-level schema validation of extracted signals"),
    ("rich>=13.0", "Prettier CLI output"),
    ("networkx>=3.0", "RFC dependency/obsoletion graph analysis"),
)


# --------------------------------------------------------------------------- #
# Survey construction
# --------------------------------------------------------------------------- #


def _sort_key(entry: ToolSurveyEntry) -> tuple[int, str]:
    """Order entries by curated category position, then by name.

    Unknown categories sort last rather than raising, so adding a category to
    :data:`CURATED_TOOLS` without updating :data:`CATEGORY_ORDER` degrades to a
    still-deterministic order instead of breaking the build.
    """
    try:
        category_index = CATEGORY_ORDER.index(entry.category)
    except ValueError:
        category_index = len(CATEGORY_ORDER)
    return (category_index, entry.name.lower())


def build_survey(
    *,
    live_search_performed: bool = False,
    search_note: str = "",
) -> ToolSurvey:
    """Assemble the :class:`~openintel_rfc.models.ToolSurvey` from curated data.

    Parameters
    ----------
    live_search_performed:
        Whether *this run* re-ran the upstream searches. Defaults to ``False``
        because this module never touches the network; only a caller that has
        actually performed the searches may set it.
    search_note:
        Replaces :data:`DEFAULT_SEARCH_NOTE` when non-empty. A caller setting
        ``live_search_performed=True`` is expected to supply one describing what
        it searched.

    Notes
    -----
    Entries are deep-copied so that a caller mutating the returned survey cannot
    corrupt the module-level shortlist for later calls in the same process.
    """
    entries = sorted((e.model_copy(deep=True) for e in CURATED_TOOLS), key=_sort_key)

    note = search_note.strip() or DEFAULT_SEARCH_NOTE

    return ToolSurvey(
        generated_at=now(),
        live_search_performed=live_search_performed,
        search_note=note,
        executive_summary=EXECUTIVE_SUMMARY,
        entries=entries,
        mvp_stack=[e.name for e in entries if e.decision == "use_now"],
        optional_stack=[e.name for e in entries if e.decision == "optional_later"],
        rejected=[e.name for e in entries if e.decision == "reject_for_mvp"],
        risks=list(RISKS),
        requirements_txt=[f"{spec:<22}# {reason}" for spec, reason in MVP_REQUIREMENTS],
    )


# --------------------------------------------------------------------------- #
# Markdown rendering
# --------------------------------------------------------------------------- #

_DECISION_LABELS: dict[str, str] = {
    "use_now": "use now",
    "optional_later": "optional / later",
    "reject_for_mvp": "reject for MVP",
}


def _cell(text: str) -> str:
    """Make a string safe for a Markdown table cell (single line, no bare pipes)."""
    return " ".join(text.split()).replace("|", "\\|")


def _entries_by_decision(survey: ToolSurvey, decision: str) -> list[ToolSurveyEntry]:
    return [e for e in survey.entries if e.decision == decision]


def _render_entry_detail(entry: ToolSurveyEntry) -> list[str]:
    """Render one tool as a detail block used by sections 4, 5 and 6."""
    lines = [f"### {entry.name}", ""]
    lines.append(f"- Category: {entry.category}")
    if entry.pypi_package:
        lines.append(f"- Package: `{entry.pypi_package}`")
    if entry.docs_url:
        lines.append(f"- Docs: {entry.docs_url}")
    elif entry.url:
        lines.append(f"- Home: {entry.url}")
    lines.append(f"- Why it may help: {entry.why_it_may_help}")
    lines.append(f"- Decision rationale: {entry.decision_rationale}")
    lines.append(f"- Pipeline mapping: {entry.pipeline_mapping}")
    if entry.risks:
        lines.append(f"- Risks: {entry.risks}")
    lines.append("")
    return lines


def render_markdown(survey: ToolSurvey) -> str:
    """Render a :class:`ToolSurvey` as the Markdown document shipped in ``docs/``.

    Pure function of the survey: same input, same bytes. The section order is
    fixed because the document is referenced by section number from the build
    contract and from ``requirements.txt``.
    """
    lines: list[str] = [
        "# Open-source tool survey",
        "",
        f"Generated by `openintel_rfc.tool_survey` for {config.PIPELINE_NAME} "
        f"v{config.PIPELINE_VERSION}.",
        "",
        f"- Generated at: {survey.generated_at.isoformat()}",
        f"- Shortlist researched: {RESEARCH_DATE.isoformat()}",
        f"- Tools evaluated: {len(survey.entries)}",
        "",
        "This file is generated. Edit `src/openintel_rfc/tool_survey.py` and re-run",
        "`make survey` rather than editing the Markdown, or the two will drift.",
        "",
    ]

    # ---- 1. Executive summary ---- #
    lines += ["## 1. Executive summary", ""]
    lines += [survey.executive_summary, ""]

    # ---- 2. Live search status ---- #
    status = (
        "Yes - this run performed live search."
        if survey.live_search_performed
        else "No - this run performed no network access."
    )
    lines += [
        "## 2. Was live search performed?",
        "",
        f"**{status}**",
        "",
        survey.search_note,
        "",
        f"The following was retrieved from upstream sources on "
        f"{RESEARCH_DATE.isoformat()} and is reproduced as observed:",
        "",
    ]
    lines += [f"- {item}" for item in LIVE_VERIFICATION_LOG]
    lines += [
        "",
        "Facts not listed above were not verified live and are not asserted as "
        "current. Where a lookup failed - the Evidence release version, for "
        "instance - that is stated rather than filled in from memory.",
        "",
    ]

    # ---- 3. Comparison table ---- #
    lines += [
        "## 3. Tool comparison",
        "",
        "| Tool | Category | Decision | Why | Pipeline mapping |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in survey.entries:
        lines.append(
            "| {name} | {category} | {decision} | {why} | {mapping} |".format(
                name=_cell(entry.name),
                category=_cell(entry.category),
                decision=_DECISION_LABELS.get(entry.decision, entry.decision),
                why=_cell(entry.decision_rationale),
                mapping=_cell(entry.pipeline_mapping),
            )
        )
    lines.append("")

    # ---- 4. Recommended MVP stack ---- #
    use_now = _entries_by_decision(survey, "use_now")
    lines += [
        "## 4. Recommended MVP stack",
        "",
        "Adopted now. Every one of these is already installed in the target "
        "environment, is permissively licensed, and adds no service or network "
        "dependency.",
        "",
    ]
    lines += [f"- **{e.name}** ({e.category})" for e in use_now]
    lines.append("")
    for entry in use_now:
        lines += _render_entry_detail(entry)

    # ---- 5. Optional / future stack ---- #
    optional = _entries_by_decision(survey, "optional_later")
    lines += [
        "## 5. Optional / future stack",
        "",
        "Not adopted for the MVP, but each has a named extension point and a stated "
        "trigger condition. These are deferrals, not dismissals.",
        "",
    ]
    lines += [f"- **{e.name}** ({e.category})" for e in optional]
    lines.append("")
    for entry in optional:
        lines += _render_entry_detail(entry)

    # ---- 6. Rejected ---- #
    rejected = _entries_by_decision(survey, "reject_for_mvp")
    lines += [
        "## 6. Rejected for the MVP",
        "",
        "Rejected because the cost is concrete and the benefit is either already "
        "covered elsewhere in the pipeline or not applicable to the inputs this "
        "pipeline actually has. Neither rejection is a judgement on the project.",
        "",
    ]
    lines += [f"- **{e.name}** ({e.category})" for e in rejected]
    lines.append("")
    for entry in rejected:
        lines += _render_entry_detail(entry)

    # ---- 7. Risks and tradeoffs ---- #
    lines += ["## 7. Risks and tradeoffs", ""]
    for risk in survey.risks:
        lines.append(f"- {risk}")
    lines.append("")

    # ---- 8. Dependencies ---- #
    lines += [
        "## 8. Exact dependencies for `requirements.txt`",
        "",
        "```text",
        "# OpenINTEL RFC-adoption matching pipeline -- MVP dependencies.",
        "# Selected in docs/open_source_tool_survey.md; each line notes its "
        "pipeline role.",
        "",
    ]
    lines += list(survey.requirements_txt)
    lines += [
        "",
        "# --- Optional extras (not required for the demo; see section 5) ---",
    ]
    lines += [f"# {spec:<20}# {reason}" for spec, reason in OPTIONAL_REQUIREMENTS]
    lines += [
        "```",
        "",
        "Floors, not pins: the pipeline uses long-stable APIs from each of these, and "
        "a research project that cannot be installed alongside a current scientific "
        "Python environment is not useful. Pin exactly in a lockfile if a run has to "
        "be reproduced byte-for-byte years later.",
        "",
    ]

    # ---- 9. Pipeline mapping ---- #
    lines += [
        "## 9. How each selected tool maps to the pipeline",
        "",
        "| Tool | Module or artefact | Role |",
        "| --- | --- | --- |",
    ]
    for entry in use_now:
        module, _, role = entry.pipeline_mapping.partition(" - ")
        lines.append(
            "| {name} | {module} | {role} |".format(
                name=_cell(entry.name),
                module=f"`{_cell(module)}`",
                role=_cell(role or entry.why_it_may_help),
            )
        )
    lines += [
        "",
        "Read end to end: `parquet_reader.py` uses **DuckDB** to project only the "
        "native OpenINTEL columns that the queryable indicators reference, falling "
        "back to **PyArrow** plus **pandas** when DuckDB is unavailable or the caller "
        "asks for it. Those rows are normalized into `ObservedSignal` objects, which "
        "are **Pydantic** models - as is every artefact from there on, which is what "
        "makes the JSON layout a checked contract rather than a convention. The "
        "exporters write **pandas** frames to CSV beside that JSON. The dashboard "
        "loads the artefacts by the names in `config.OUTPUT_FILES`, lays them out as "
        "**Streamlit** pages, and draws the timeline and ranking views with "
        "**Plotly**. **pytest** pins the parts that would fail quietly: operator "
        "semantics, the scoring arithmetic and the timestamp cutoff.",
        "",
    ]

    # ---- Closing recommended-stack block ---- #
    lines += [
        "## Recommended stack",
        "",
        "```text",
        "USE NOW:        " + ", ".join(survey.mvp_stack),
        "OPTIONAL/LATER: " + ", ".join(survey.optional_stack),
        "REJECT FOR MVP: " + ", ".join(survey.rejected),
        "```",
    ]

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def generate_survey(
    out_path: Path,
    *,
    live_search_performed: bool = False,
    search_note: str = "",
) -> Path:
    """Build the survey and write it to ``out_path`` as Markdown.

    Returns the written path. Parent directories are created as needed. The
    caller supplies the path; this module holds no absolute paths of its own.
    """
    survey = build_survey(
        live_search_performed=live_search_performed,
        search_note=search_note,
    )
    return write_text(out_path, render_markdown(survey))
