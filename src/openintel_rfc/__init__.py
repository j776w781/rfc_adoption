"""OpenINTEL RFC-adoption matching pipeline.

Reads OpenINTEL-style Parquet measurement data, extracts normalized DNS/DNSSEC
signals, matches them against an RFC checklist/signature database with
publication-date cutoff logic, and emits ranked RFC candidates together with
explicit, structured reasoning traces.

The pipeline identifies *ranked RFC candidates* consistent with observable
signals. It does not, by itself, prove RFC adoption.
"""

from __future__ import annotations

from .config import PIPELINE_NAME, PIPELINE_VERSION

__all__ = ["PIPELINE_NAME", "PIPELINE_VERSION", "__version__"]

__version__ = PIPELINE_VERSION
