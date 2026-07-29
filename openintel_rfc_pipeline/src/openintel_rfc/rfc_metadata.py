"""RFC metadata resolution, with an offline default and opt-in network backends.

Everything the matcher needs about an RFC — its title, and above all its
**publication date**, which drives the timestamp cutoff rule — is already
carried by the checklist database. So the default provider,
:class:`ChecklistMetadataProvider`, reads exactly that and performs no IO.

The two network providers exist because the checklist is hand-maintained and
will eventually need to be reconciled against an authoritative source. They are
written as real integration seams (documented endpoints, documented response
shapes, working parsers) rather than as ``pass`` placeholders, but they are
inert unless constructed with ``enable_network=True``, and nothing in the
pipeline constructs them at all. With network access disabled they raise
:class:`~openintel_rfc.utils.PipelineError` explaining how to opt in and which
provider to use instead — they never return a silently empty result, because a
missing publication date would quietly turn every timestamp check into a pass.

Provider hierarchy
------------------
``RFCMetadataProvider``            abstract; ``fetch`` for one RFC, ``fetch_many``
                                   for a batch (default: loop over ``fetch``).
``ChecklistMetadataProvider``      offline default, sourced from the checklist DB.
``DatatrackerMetadataProvider``    IETF Datatracker REST API (opt-in).
``RFCEditorXMLMetadataProvider``   RFC Editor RFCXML v3 documents (opt-in).
"""

from __future__ import annotations

import abc
import re
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from .models import RFCChecklistDB, RFCMetadata
from .utils import PipelineError, get_logger, normalize_timestamp, parse_timestamp

__all__ = [
    "RFCMetadataProvider",
    "ChecklistMetadataProvider",
    "DatatrackerMetadataProvider",
    "RFCEditorXMLMetadataProvider",
    "normalize_rfc_id",
    "rfc_number",
    "rfc_editor_url",
    "build_metadata_index",
    "get_publication_date",
]

LOGGER = get_logger(__name__)

#: ``rfc8078``, ``RFC-8078``, ``RFC 8078`` and ``8078`` all denote RFC 8078.
_RFC_ID_PATTERN = re.compile(r"^\s*(?:rfc[\s._\-]*)?(\d+)\s*$", re.IGNORECASE)

_RFC_EDITOR_INFO_BASE = "https://www.rfc-editor.org/info/"

#: Month names as they appear in the ``<front><date>`` element of RFCXML v3.
_XML_MONTHS: dict[str, int] = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


# --------------------------------------------------------------------------- #
# RFC identifier helpers
# --------------------------------------------------------------------------- #


def normalize_rfc_id(rfc_id: str) -> str:
    """Normalize any spelling of an RFC identifier to the canonical ``RFC N``.

    ``"rfc8078"``, ``"RFC-8078"``, ``"rfc_8078"`` and ``"8078"`` all normalize to
    ``"RFC 8078"``. Anything that does not look like an RFC reference is
    returned with surrounding whitespace collapsed but otherwise untouched, so
    the function is total and never loses information.
    """
    match = _RFC_ID_PATTERN.match(rfc_id or "")
    if match:
        return f"RFC {int(match.group(1))}"
    return " ".join((rfc_id or "").split())


def rfc_number(rfc_id: str) -> int | None:
    """Return the numeric part of an RFC identifier, or ``None`` if there is none."""
    match = _RFC_ID_PATTERN.match(rfc_id or "")
    return int(match.group(1)) if match else None


def rfc_editor_url(rfc_id: str) -> str:
    """Return the canonical RFC Editor info page URL for an RFC identifier.

    ``"RFC 8078"`` -> ``"https://www.rfc-editor.org/info/rfc8078"``. For an
    identifier with no number the slugified identifier is used, which keeps the
    function total; the resulting URL may of course 404.
    """
    number = rfc_number(rfc_id)
    if number is not None:
        return f"{_RFC_EDITOR_INFO_BASE}rfc{number}"
    slug = re.sub(r"[^a-z0-9]", "", (rfc_id or "").lower()) or "unknown"
    return f"{_RFC_EDITOR_INFO_BASE}{slug}"


# --------------------------------------------------------------------------- #
# Provider interface
# --------------------------------------------------------------------------- #


class RFCMetadataProvider(abc.ABC):
    """Resolve :class:`~openintel_rfc.models.RFCMetadata` for an RFC identifier.

    Implementations must be safe to construct at import time: no IO, no network,
    no filesystem access in ``__init__``.
    """

    #: Value written into ``RFCMetadata.source``; also used in log lines.
    name: str = "abstract"

    @abc.abstractmethod
    def fetch(self, rfc_id: str) -> RFCMetadata | None:
        """Return metadata for one RFC, or ``None`` if this backend has none.

        ``None`` means "this backend legitimately does not know about this RFC".
        It must never be used to paper over a backend that is unavailable or
        misconfigured — that case raises
        :class:`~openintel_rfc.utils.PipelineError`.
        """

    def fetch_many(self, rfc_ids: Sequence[str]) -> dict[str, RFCMetadata]:
        """Resolve several RFCs, skipping the ones this backend does not know.

        The default implementation loops over :meth:`fetch`. Backends with a
        bulk endpoint should override it. Keys are returned in sorted order so
        callers that iterate the mapping stay deterministic.
        """
        resolved: dict[str, RFCMetadata] = {}
        for rfc_id in rfc_ids:
            metadata = self.fetch(rfc_id)
            if metadata is not None:
                resolved[rfc_id] = metadata
        return {key: resolved[key] for key in sorted(resolved)}


class ChecklistMetadataProvider(RFCMetadataProvider):
    """The default, offline provider: metadata comes from the checklist DB.

    The checklist already carries the title, the publication date (normalized to
    the first day of the RFC Editor publication month) and the related-RFC
    links, so for the MVP this backend is authoritative *by construction*: the
    dates the matcher enforces are exactly the dates the checklist declares.

    That is also its limitation, and the reason the network backends exist: a
    wrong date in the checklist cannot be detected from inside the checklist.
    """

    name = "checklist"

    def __init__(self, db: RFCChecklistDB) -> None:
        self._db = db
        # Index on the normalized form so "rfc8078" resolves an entry stored as
        # "RFC 8078" and vice versa.
        self._by_normalized: dict[str, str] = {}
        for rfc_id in db.rfc_ids:
            self._by_normalized.setdefault(normalize_rfc_id(rfc_id), rfc_id)

    def fetch(self, rfc_id: str) -> RFCMetadata | None:
        entry = self._db.get(rfc_id)
        if entry is None:
            original = self._by_normalized.get(normalize_rfc_id(rfc_id))
            entry = self._db.get(original) if original is not None else None
        if entry is None:
            return None
        return RFCMetadata(
            rfc_id=entry.rfc_id,
            title=entry.title,
            publication_date=normalize_timestamp(entry.publication_date),
            source=self.name,
            url=entry.references[0] if entry.references else rfc_editor_url(entry.rfc_id),
            related_rfc_ids=list(entry.related_rfc_ids),
            notes=entry.notes,
        )


# --------------------------------------------------------------------------- #
# Opt-in network backends
# --------------------------------------------------------------------------- #


class _NetworkMetadataProvider(RFCMetadataProvider):
    """Shared opt-in guard and HTTP helper for the network-backed providers.

    Network access is opt-in for two reasons: the pipeline must be reproducible
    offline, and a build contract rule forbids network IO on any default code
    path. Constructing one of these without ``enable_network=True`` therefore
    produces an object that raises on use rather than one that quietly returns
    nothing.
    """

    #: Human-readable description of the upstream service, used in errors.
    service: str = "the upstream service"

    def __init__(
        self,
        *,
        enable_network: bool = False,
        timeout: float = 10.0,
        user_agent: str = "openintel-rfc-adoption-matcher/0.1 (research)",
    ) -> None:
        self.enable_network = bool(enable_network)
        self.timeout = float(timeout)
        self.user_agent = user_agent

    def _require_network(self, rfc_id: str) -> None:
        if not self.enable_network:
            raise PipelineError(
                f"{type(self).__name__} cannot resolve {normalize_rfc_id(rfc_id)}: network "
                f"access to {self.service} is opt-in and is disabled for this provider. "
                f"Construct it explicitly as {type(self).__name__}(enable_network=True) if "
                f"you intend to make live requests. The pipeline's default provider is "
                f"ChecklistMetadataProvider, which resolves publication dates offline from "
                f"the checklist database and is what build_metadata_index() uses."
            )

    def _get(self, url: str) -> bytes:
        """Perform one GET. Only ever reached when ``enable_network`` is true.

        ``urllib`` from the standard library is used deliberately: adding a
        third-party HTTP dependency for a backend that is off by default would
        be a poor trade.
        """
        import urllib.error
        import urllib.request

        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:  # pragma: no cover - network path
            raise PipelineError(f"{self.service} returned HTTP {exc.code} for {url}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network path
            raise PipelineError(f"{self.service} is unreachable at {url}: {exc.reason}") from exc


class DatatrackerMetadataProvider(_NetworkMetadataProvider):
    """IETF Datatracker backend (https://datatracker.ietf.org/api/).

    Endpoints
    ---------
    The Datatracker exposes a Tastypie REST API rooted at
    ``https://datatracker.ietf.org/api/v1/``. Two calls are needed, because the
    document resource's own ``time`` field is the *last modification* time, not
    the publication date:

    1. Document record (title, stream, status)::

           GET https://datatracker.ietf.org/api/v1/doc/document/rfc8078/?format=json

       Relevant response keys: ``name`` (``"rfc8078"``), ``title``, ``time``,
       ``std_level``, ``abstract``.

    2. Publication date, which is the ``time`` of the document's
       ``published_rfc`` event::

           GET https://datatracker.ietf.org/api/v1/doc/docevent/?doc=rfc8078&type=published_rfc&format=json

       Relevant response shape: ``{"objects": [{"type": "published_rfc",
       "time": "2017-03-02T00:00:00", ...}]}``. The first object carries the
       publication timestamp.

    Caveats a real integration must handle: Datatracker renamed RFC documents
    from their draft names to ``rfcNNNN`` names, so very old scripts keyed on
    the draft name will 404; the API is rate limited and unversioned beyond
    ``v1``; and ``published_rfc`` events are absent for a handful of early RFCs,
    in which case the RFC Editor index is the better source.
    """

    name = "datatracker"
    service = "the IETF Datatracker API"

    DOCUMENT_ENDPOINT = "https://datatracker.ietf.org/api/v1/doc/document/{name}/?format=json"
    PUBLICATION_EVENT_ENDPOINT = (
        "https://datatracker.ietf.org/api/v1/doc/docevent/"
        "?doc={name}&type=published_rfc&format=json"
    )

    def fetch(self, rfc_id: str) -> RFCMetadata | None:
        self._require_network(rfc_id)
        number = rfc_number(rfc_id)
        if number is None:
            return None
        document_name = f"rfc{number}"

        import json

        document: dict[str, Any] = json.loads(
            self._get(self.DOCUMENT_ENDPOINT.format(name=document_name)).decode("utf-8")
        )
        events: dict[str, Any] = json.loads(
            self._get(self.PUBLICATION_EVENT_ENDPOINT.format(name=document_name)).decode("utf-8")
        )
        objects = events.get("objects") or []
        if not objects:
            raise PipelineError(
                f"{self.service} has no 'published_rfc' document event for {document_name}, so "
                f"its publication date cannot be established from this backend. Use "
                f"RFCEditorXMLMetadataProvider or keep the date in the checklist database."
            )
        published_at = parse_timestamp(objects[0].get("time"))
        return RFCMetadata(
            rfc_id=normalize_rfc_id(rfc_id),
            title=str(document.get("title") or normalize_rfc_id(rfc_id)),
            publication_date=published_at,
            source=self.name,
            url=f"https://datatracker.ietf.org/doc/{document_name}/",
            related_rfc_ids=[],
            notes="Publication date taken from the Datatracker 'published_rfc' document event.",
        )


class RFCEditorXMLMetadataProvider(_NetworkMetadataProvider):
    """RFC Editor backend reading RFCXML v3 (the xml2rfc v3 vocabulary).

    Endpoint
    --------
    ::

        GET https://www.rfc-editor.org/rfc/rfc8078.xml

    Element carrying the publication date
    -------------------------------------
    In the xml2rfc v3 vocabulary the date lives on ``/rfc/front/date`` as
    attributes, not as text::

        <rfc number="8078" ...>
          <front>
            <title>Managing DS Records from the Parent via CDS/CDNSKEY</title>
            <date month="March" year="2017"/>
          </front>
          ...
        </rfc>

    ``month`` is the English month name (occasionally a number in older
    conversions), ``year`` is four digits, and ``day`` is usually absent — which
    is precisely why the checklist normalizes publication dates to the first day
    of the publication month. The title comes from ``/rfc/front/title``.

    Caveats a real integration must handle: only RFCs published from roughly
    2016 onwards, plus the retro-converted back catalogue, have an ``.xml``
    file at all; anything else is text-only and must fall back to
    ``https://www.rfc-editor.org/rfc-index.xml``, whose ``<rfc-entry><date>``
    element carries ``<month>`` and ``<year>`` as child elements instead of
    attributes.
    """

    name = "rfc_editor_xml"
    service = "the RFC Editor XML archive"

    XML_ENDPOINT = "https://www.rfc-editor.org/rfc/rfc{number}.xml"
    #: XPath of the element that carries the publication date in RFCXML v3.
    PUBLICATION_DATE_XPATH = "front/date"

    def fetch(self, rfc_id: str) -> RFCMetadata | None:
        self._require_network(rfc_id)
        number = rfc_number(rfc_id)
        if number is None:
            return None

        from xml.etree import ElementTree

        payload = self._get(self.XML_ENDPOINT.format(number=number))
        try:
            root = ElementTree.fromstring(payload)
        except ElementTree.ParseError as exc:  # pragma: no cover - network path
            raise PipelineError(
                f"{self.service} returned XML for RFC {number} that could not be parsed: {exc}"
            ) from exc

        date_element = root.find(self.PUBLICATION_DATE_XPATH)
        if date_element is None:
            raise PipelineError(
                f"The RFCXML document for RFC {number} has no <{self.PUBLICATION_DATE_XPATH}> "
                f"element, so its publication date cannot be established from this backend."
            )
        published_at = _publication_date_from_xml_date(date_element.attrib, number)

        title_element = root.find("front/title")
        title = (title_element.text or "").strip() if title_element is not None else ""
        return RFCMetadata(
            rfc_id=normalize_rfc_id(rfc_id),
            title=title or normalize_rfc_id(rfc_id),
            publication_date=published_at,
            source=self.name,
            url=rfc_editor_url(rfc_id),
            related_rfc_ids=[],
            notes="Publication date taken from the RFCXML v3 <front><date> element.",
        )


def _publication_date_from_xml_date(attributes: dict[str, str], number: int) -> datetime:
    """Turn RFCXML ``<date month=... year=... [day=...]>`` attributes into a datetime."""
    year_text = attributes.get("year", "").strip()
    if not year_text.isdigit():
        raise PipelineError(
            f"The RFCXML <date> element for RFC {number} has no usable 'year' attribute "
            f"(got {attributes.get('year')!r})."
        )
    month_text = attributes.get("month", "").strip().lower()
    if month_text.isdigit():
        month = int(month_text)
    else:
        month = _XML_MONTHS.get(month_text, 1)
    day_text = attributes.get("day", "").strip()
    day = int(day_text) if day_text.isdigit() else 1
    return datetime(int(year_text), max(1, min(12, month)), max(1, min(28, day)))


# --------------------------------------------------------------------------- #
# Index building and lookup
# --------------------------------------------------------------------------- #


def build_metadata_index(
    db: RFCChecklistDB, provider: RFCMetadataProvider | None = None
) -> dict[str, RFCMetadata]:
    """Resolve metadata for every RFC in the checklist DB.

    This is the function the rest of the pipeline calls. It defaults to
    :class:`ChecklistMetadataProvider`, so the default path is offline and
    deterministic; pass another provider only when you have deliberately opted
    into network access.

    Keys are the ``rfc_id`` strings exactly as they appear in the checklist, so
    a lookup with a checklist-derived id always hits. The returned mapping is
    sorted by key.
    """
    active = provider if provider is not None else ChecklistMetadataProvider(db)
    index = active.fetch_many(db.rfc_ids)
    missing = [rfc_id for rfc_id in db.rfc_ids if rfc_id not in index]
    if missing:
        LOGGER.warning(
            "Metadata provider '%s' resolved no record for: %s",
            active.name,
            ", ".join(sorted(missing)),
        )
    return index


def get_publication_date(rfc_id: str, index: dict[str, RFCMetadata]) -> datetime | None:
    """Look up an RFC's publication date, tolerating identifier spelling.

    Tries the literal key first, then the canonical ``RFC N`` form, then scans
    the index comparing normalized identifiers. Returns ``None`` when the RFC is
    not in the index — callers must treat that as "cutoff cannot be enforced"
    rather than as "cutoff passed".
    """
    metadata = index.get(rfc_id)
    if metadata is None:
        metadata = index.get(normalize_rfc_id(rfc_id))
    if metadata is None:
        wanted = normalize_rfc_id(rfc_id)
        for key in sorted(index):
            if normalize_rfc_id(key) == wanted:
                metadata = index[key]
                break
    if metadata is None:
        return None
    return normalize_timestamp(metadata.publication_date)
