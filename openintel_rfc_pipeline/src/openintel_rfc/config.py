"""Pipeline-wide constants, scoring parameters and output file names.

No absolute paths are baked into this module. Callers pass paths in; the only
path logic here resolves locations *relative to the installed package*, which is
used for defaults and for tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

# --------------------------------------------------------------------------- #
# Repository layout helpers
# --------------------------------------------------------------------------- #

#: ``.../src/openintel_rfc``
PACKAGE_ROOT: Final[Path] = Path(__file__).resolve().parent

#: ``.../openintel_rfc_pipeline`` (src/openintel_rfc -> src -> project root)
PROJECT_ROOT: Final[Path] = PACKAGE_ROOT.parent.parent

DEFAULT_CHECKLIST_PATH: Final[Path] = (
    PROJECT_ROOT / "data" / "rfc_checklists" / "dnssec_rfc_checklists.json"
)
DEFAULT_DICTIONARY_PATH: Final[Path] = (
    PROJECT_ROOT / "data" / "openintel_dictionary" / "sample_openintel_dictionary.json"
)
DEFAULT_PARQUET_PATH: Final[Path] = (
    PROJECT_ROOT / "data" / "sample_parquet" / "sample_openintel.parquet"
)
DEFAULT_OUTPUT_DIR: Final[Path] = PROJECT_ROOT / "demo_output"
DEFAULT_SURVEY_PATH: Final[Path] = PROJECT_ROOT / "docs" / "open_source_tool_survey.md"


# --------------------------------------------------------------------------- #
# Output artefact names (the dashboard reads these by name)
# --------------------------------------------------------------------------- #

OUTPUT_FILES: Final[dict[str, str]] = {
    # schema-check
    "queryable_indicators": "queryable_indicators.json",
    "non_queryable_indicators": "non_queryable_indicators.json",
    "schema_check_report_md": "schema_check_report.md",
    "schema_check_csv": "schema_check.csv",
    "schema_check_json": "schema_check.json",
    # analyze
    "observed_signals": "observed_signals.json",
    "rfc_matches": "rfc_matches.json",
    "reasoning_traces": "reasoning_traces.json",
    "review_queue": "review_queue.json",
    "adoption_timeline": "adoption_timeline.json",
    "ranked_candidates": "ranked_candidates.json",
    "report_md": "report.md",
    "rfc_matches_csv": "rfc_matches.csv",
    "review_queue_csv": "review_queue.csv",
    "adoption_timeline_csv": "adoption_timeline.csv",
    "observed_signals_csv": "observed_signals.csv",
    "reasoning_traces_csv": "reasoning_traces.csv",
    "run_manifest": "run_manifest.json",
    # dashboard-owned state
    "review_queue_status": "review_queue_status.json",
}

#: Fields always pulled from Parquet regardless of which indicators are queryable.
ALWAYS_SELECT_FIELDS: Final[tuple[str, ...]] = (
    "timestamp",
    "domain",
    "zone",
    "source",
    "measurement_id",
)


# --------------------------------------------------------------------------- #
# Scoring parameters
# --------------------------------------------------------------------------- #

#: Bonus when an RFC has >= 2 required indicators and *all* of them matched.
#: Single-required-indicator RFCs get no bonus: their weight already carries it.
REQUIRED_MATCH_BONUS: Final[float] = 2.0
MIN_REQUIRED_FOR_BONUS: Final[int] = 2

#: Matched optional indicators corroborate; they count at half weight.
OPTIONAL_WEIGHT_FACTOR: Final[float] = 0.5

#: Penalty per required indicator that was evaluated and did not match.
MISSING_REQUIRED_PENALTY: Final[float] = 3.0

#: Flat penalty when some, but not all, required indicators matched.
PARTIAL_MATCH_PENALTY: Final[float] = 2.0

#: Flat penalty when any matched indicator is marked ambiguous in the checklist.
AMBIGUITY_PENALTY: Final[float] = 2.0

#: Scores are rounded to this many decimals so output is byte-stable.
SCORE_PRECISION: Final[int] = 4

#: Two top candidates whose scores differ by <= this fraction are "too close to
#: call" and generate a review item.
CLOSE_RANKING_RELATIVE_TOLERANCE: Final[float] = 0.15

#: Candidates scoring at or below this are not emitted as ranked matches.
MIN_RANKABLE_SCORE: Final[float] = 0.0


# --------------------------------------------------------------------------- #
# Misc
# --------------------------------------------------------------------------- #

SIGNAL_ID_PREFIX: Final[str] = "sig_"
SIGNAL_ID_WIDTH: Final[int] = 4
TRACE_ID_PREFIX: Final[str] = "trace_"
REVIEW_ID_PREFIX: Final[str] = "rev_"

#: Confidence at or above this is auto-accepted by the deterministic verifier.
LLM_AUTO_ACCEPT_CONFIDENCES: Final[frozenset[str]] = frozenset({"very_high", "high"})

PIPELINE_NAME: Final[str] = "openintel-rfc-adoption-matcher"
PIPELINE_VERSION: Final[str] = "0.1.0"

#: Fixed timestamp used for deterministic output when OPENINTEL_RFC_DETERMINISTIC=1.
DETERMINISTIC_TIMESTAMP_ENV: Final[str] = "OPENINTEL_RFC_DETERMINISTIC"
