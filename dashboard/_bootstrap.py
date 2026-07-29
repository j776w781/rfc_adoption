"""Import-path bootstrap for the Streamlit dashboard.

Streamlit executes ``app.py`` and every file under ``pages/`` as a *top-level
script*, not as a module of a package. That means ``dashboard/`` is not
importable as a package and relative imports are impossible: each entry point
has to put the directories it needs on ``sys.path`` itself.

Doing that inline in ten page files would be ten chances to get it subtly wrong,
so it lives here instead. Every page starts with::

    from _bootstrap import setup

    setup()

``setup()`` is idempotent and adds two directories:

``<project>/src``
    so ``openintel_rfc.dashboard_data`` — the dashboard's only data-access layer
    — can be imported without the caller having to set ``PYTHONPATH``.

``<project>/dashboard``
    so ``_shared`` resolves from a page inside ``pages/``. Streamlit's own page
    runner already adds the *main* script's directory, but
    ``streamlit.testing.v1.AppTest.from_file("dashboard/pages/1_Overview.py")``
    runs the page as the main script, in which case only ``pages/`` is on the
    path. Adding both keeps the app and the headless smoke tests identical.

No Streamlit import happens here on purpose: this module must be usable from a
plain ``python -c`` check as well as from inside a Streamlit run.
"""

from __future__ import annotations

import sys
from pathlib import Path

__all__ = ["DASHBOARD_DIR", "PROJECT_ROOT", "SRC_DIR", "setup"]

#: ``<project>/dashboard`` — the directory holding ``app.py`` and ``_shared.py``.
DASHBOARD_DIR: Path = Path(__file__).resolve().parent

#: ``<project>`` — the repository root that owns ``src/``, ``data/``, ``docs/``.
PROJECT_ROOT: Path = DASHBOARD_DIR.parent

#: ``<project>/src`` — the importable location of the ``openintel_rfc`` package.
SRC_DIR: Path = PROJECT_ROOT / "src"


def setup() -> Path:
    """Put ``src/`` and ``dashboard/`` on ``sys.path``; return the project root.

    Prepending rather than appending matters: a checkout being developed on
    should win over any ``openintel_rfc`` installed site-wide, otherwise the
    dashboard would silently render a different version of the pipeline's data
    layer than the one in the working tree.
    """
    for directory in (SRC_DIR, DASHBOARD_DIR):
        entry = str(directory)
        if directory.is_dir() and entry not in sys.path:
            sys.path.insert(0, entry)
    return PROJECT_ROOT
