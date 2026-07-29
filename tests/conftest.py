"""Shared fixtures for the openintel_rfc test suite.

Three kinds of fixture live here:

*Inputs* -- ``checklist_db``, ``dictionary``, ``schema_report`` and
``sample_parquet_path`` load the repository's real data files once per session.
The tests assert against the shipped checklist and dictionary rather than against
miniature stand-ins, because the worked expectations in the build contract are
statements about *those* files.

*Construction helpers* -- ``signal_factory`` hand-builds an
:class:`~openintel_rfc.models.ObservedSignal`. Unit tests use it instead of
depending on a particular row of the sample Parquet, so a change to the fixture
data cannot silently turn a scoring test green.

*Artefacts* -- ``analyzed_output`` runs the CLI ``analyze`` command once into a
session-scoped temporary directory. Tests that need real files on disk share
that one run; nothing in the suite writes into the repository's ``demo_output``.
"""

from __future__ import annotations

import contextlib
import io
import itertools
import os
import re
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from openintel_rfc import cli, config, utils
from openintel_rfc.checklist_loader import load_checklist_db, load_dictionary
from openintel_rfc.models import (
    ObservedSignal,
    OpenINTELDictionary,
    RFCChecklistDB,
    ScoreBreakdown,
    SchemaCheckReport,
)
from openintel_rfc.schema_checker import check_schema
from openintel_rfc.signal_extractor import SIGNAL_FIELDS

# --------------------------------------------------------------------------- #
# Repository layout
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="session")
def project_root() -> Path:
    """The repository root (``tests/`` lives directly beneath it)."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def checklist_path(project_root: Path) -> Path:
    return project_root / "data" / "rfc_checklists" / "dnssec_rfc_checklists.json"


@pytest.fixture(scope="session")
def dictionary_path(project_root: Path) -> Path:
    return project_root / "data" / "openintel_dictionary" / "sample_openintel_dictionary.json"


@pytest.fixture(scope="session")
def sample_parquet_path(project_root: Path) -> Path:
    """The deterministic sample OpenINTEL Parquet fixture."""
    path = project_root / "data" / "sample_parquet" / "sample_openintel.parquet"
    if not path.is_file():  # pragma: no cover - the fixture is committed
        pytest.skip(f"sample Parquet fixture is missing: {path}")
    return path


@pytest.fixture(scope="session")
def demo_output_dir(project_root: Path) -> Path:
    """The committed demo run. Read-only: no test may write into it."""
    path = project_root / "demo_output"
    if not path.is_dir():  # pragma: no cover - the directory is committed
        pytest.skip(f"demo_output is missing: {path}")
    return path


# --------------------------------------------------------------------------- #
# Loaded inputs
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="session")
def checklist_db(checklist_path: Path) -> RFCChecklistDB:
    return load_checklist_db(checklist_path)


@pytest.fixture(scope="session")
def dictionary(dictionary_path: Path) -> OpenINTELDictionary:
    return load_dictionary(dictionary_path)


@pytest.fixture(scope="session")
def schema_report(
    checklist_db: RFCChecklistDB,
    dictionary: OpenINTELDictionary,
    checklist_path: Path,
    dictionary_path: Path,
) -> SchemaCheckReport:
    """The queryability cross-check of the shipped checklist and dictionary."""
    return check_schema(
        checklist_db,
        dictionary,
        checklist_path=str(checklist_path),
        dictionary_path=str(dictionary_path),
    )


# --------------------------------------------------------------------------- #
# Hand-built observations
# --------------------------------------------------------------------------- #


@pytest.fixture
def signal_factory() -> Callable[..., ObservedSignal]:
    """Build an :class:`ObservedSignal` from keyword field values.

    Every canonical signal field is present as a key, defaulting to ``None`` --
    the same shape the extractor produces -- so a test that omits ``digest_type``
    is asserting "not observed" rather than "key absent". Unknown keyword names
    are accepted and land in ``fields`` too, which is how conditions over fields
    the dictionary does not define (``dnssec_ok_flag``) are exercised.

    Signal ids auto-increment (``sig_0001``, ``sig_0002``, ...) unless one is
    supplied explicitly.
    """
    counter = itertools.count(1)

    def make(
        timestamp: str | datetime = "2018-05-01",
        *,
        signal_id: str | None = None,
        domain: str | None = "example.nl",
        zone: str | None = "nl",
        source: str = "openintel_parquet",
        measurement_id: str | None = None,
        row_index: int | None = None,
        origin_file: str | None = None,
        **observed: Any,
    ) -> ObservedSignal:
        fields: dict[str, Any] = {name: None for name in SIGNAL_FIELDS}
        fields.update(observed)
        return ObservedSignal(
            signal_id=signal_id or utils.signal_id(next(counter)),
            source=source,
            timestamp=utils.parse_timestamp(timestamp),
            domain=domain,
            zone=zone,
            measurement_id=measurement_id,
            fields=fields,
            row_index=row_index,
            origin_file=origin_file,
        )

    return make


# --------------------------------------------------------------------------- #
# Score-step arithmetic
# --------------------------------------------------------------------------- #

#: ``base_indicator_score = 10.0 (...)`` -> ("base_indicator_score", 10.0)
_TERM_PATTERN = re.compile(r"^(?P<name>[a-z_]+) = (?P<value>-?\d+(?:\.\d+)?)")

#: Trailing ``= 17.25`` of a compound line such as ``raw = a + b - c = 17.25``.
_TAIL_PATTERN = re.compile(r"= (?P<value>-?\d+(?:\.\d+)?)\s*$")


def _parse_score_steps(breakdown: ScoreBreakdown) -> dict[str, float]:
    """Recover the numbers a human reader would read out of ``steps``.

    The point of the exercise is that ``steps`` has to be self-sufficient: a
    reader with nothing but those lines must be able to recompute
    ``final_score``. Later lines override earlier ones, which is what makes the
    forfeited ``final_score = 0.0`` line of a timestamp-invalid match win over
    the arithmetic that produced the withheld amount.
    """
    terms: dict[str, float] = {}
    for step in breakdown.steps:
        match = _TERM_PATTERN.match(step)
        if match:
            terms[match.group("name")] = float(match.group("value"))
        if step.startswith("raw = ") or step.startswith("final_score = max("):
            tail = _TAIL_PATTERN.search(step)
            assert tail is not None, f"no trailing total in score step: {step!r}"
            key = "raw" if step.startswith("raw = ") else "final_score"
            terms[key] = float(tail.group("value"))
    return terms


@pytest.fixture
def score_step_terms() -> Callable[[ScoreBreakdown], dict[str, float]]:
    """Return the parser that turns ``ScoreBreakdown.steps`` back into numbers."""
    return _parse_score_steps


# --------------------------------------------------------------------------- #
# Real artefacts from one CLI run
# --------------------------------------------------------------------------- #


@contextlib.contextmanager
def deterministic_environment() -> Iterator[None]:
    """Freeze :func:`openintel_rfc.utils.now` for the duration of the block."""
    key = config.DETERMINISTIC_TIMESTAMP_ENV
    previous = os.environ.get(key)
    os.environ[key] = "1"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(key, None)
        else:  # pragma: no cover - only when the caller already set it
            os.environ[key] = previous


def run_cli(argv: list[str]) -> tuple[int, str]:
    """Invoke ``cli.main`` in-process, capturing stdout. Never shells out."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = cli.main(argv)
    return code, buffer.getvalue()


@pytest.fixture(scope="session")
def analyzed_output(
    tmp_path_factory: pytest.TempPathFactory,
    checklist_path: Path,
    dictionary_path: Path,
    sample_parquet_path: Path,
) -> Path:
    """One full ``analyze`` run, shared by every test that needs real artefacts."""
    out_dir = tmp_path_factory.mktemp("analyze_run")
    with deterministic_environment():
        code, _ = run_cli(
            [
                "analyze",
                "--checklists",
                str(checklist_path),
                "--dictionary",
                str(dictionary_path),
                "--parquet",
                str(sample_parquet_path),
                "--out",
                str(out_dir),
            ]
        )
    assert code == 0, "the session-scoped analyze run must succeed"
    return out_dir


@pytest.fixture(scope="session")
def schema_checked_output(
    tmp_path_factory: pytest.TempPathFactory,
    checklist_path: Path,
    dictionary_path: Path,
) -> Path:
    """One full ``schema-check`` run, for tests needing its artefacts on disk."""
    out_dir = tmp_path_factory.mktemp("schema_check_run")
    with deterministic_environment():
        code, _ = run_cli(
            [
                "schema-check",
                "--checklists",
                str(checklist_path),
                "--dictionary",
                str(dictionary_path),
                "--out",
                str(out_dir),
            ]
        )
    assert code == 0, "the session-scoped schema-check run must succeed"
    return out_dir
