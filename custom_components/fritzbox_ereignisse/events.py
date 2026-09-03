"""Fetch + parse the FRITZ!Box event log ("Ereignisse") via TR-064.

Es gibt zwei dokumentierte TR-064-Wege zum selben Protokoll, das die
FRITZ!Box-Oberfläche unter System > Ereignisse anzeigt - beide im ohnehin
schon von fritzbox_anrufe genutzten Basisdienst ``DeviceInfo:1``, keine
zusätzliche Kontoberechtigung nötig:

1. ``X_AVM-DE_GetDeviceLogPath`` (FRITZ!OS 7.90+, bevorzugt): liefert einen
   Web-UI-Pfad (inkl. sid) zu einer XML-Datei mit STRUKTURIERTEN Einträgen
   (``id``/``group``/``date``/``time``/``msg``) - das vollständige
   Protokoll inkl. Kategorie, exakt wie in der FRITZ!Box-Oberfläche.
   Community-Referenz: github.com/kbr/fritzconnection Discussion #234.
   Der zurückgegebene Pfad ist gegen die normale Web-UI-Adresse (Port
   80/443) aufzulösen, NICHT gegen den TR-064-Port - identisches Prinzip
   wie beim Anrufbeantworter-Audio-Download in fritzbox_anrufe (siehe
   dortiges ``tam.py``), daher hier dieselbe ``FritzHttp.router_url``-
   Ermittlung.
2. ``GetDeviceLog`` (älterer, aber weiterhin vorhandener TR-064-Standard-
   Rückfall): liefert nur eine flache, neuzeilengetrennte Textliste ohne
   Kategorie ("Gruppe") - laut mehreren Community-Berichten (u. a.
   forum.iobroker.net/topic/44730) fehlen hier sogar einzelne
   Eintragstypen (z. B. fehlgeschlagene Anmeldeversuche). Reines
   TR-064-SOAP, kein zweiter HTTP-Request nötig.

Beide Wege werden defensiv nacheinander versucht (Weg 1 zuerst, da
vollständiger); erst wenn BEIDE fehlschlagen, meldet der Coordinator
``UpdateFailed`` - identisches Prinzip wie ``settings_data.py`` in
fritzbox_anrufe. NICHT an echter Hardware verifiziert (siehe README) - noch
unbekannt, welcher FRITZ!OS-Mindeststand/welche Kontoberechtigung in der
Praxis tatsächlich reicht.

Fix in v0.2.0 - Einrichtungsfehler "not well-formed (invalid token)"
---------------------------------------------------------------------
Ein Nutzer meldete einen dauerhaften Einrichtungsfehler mit genau dieser
Meldung. Ursache: ``get_xml_root()`` (Weg 1) nutzt
``xml.etree.ElementTree.fromstring`` - dessen ``ParseError`` ist WEDER von
``FritzConnectionException`` NOCH von ``RequestException`` abgeleitet und
wurde daher bislang von keinem der `except`-Blöcke aufgefangen, sondern
propagierte ungefangen bis zum Coordinator durch und ließ das komplette
Setup wiederholt fehlschlagen - selbst dann, wenn Weg 2 (der reine
Text-Rückfall, ganz ohne XML) einwandfrei funktioniert hätte. Ursache des
kaputten XML selbst vermutlich ein von AVMs eigenem Lua-Skript nicht
escapter, bloßer ``&`` in einem Meldungstext (oder ein laut XML 1.0
ungültiges Steuerzeichen) - ein seit Langem bekanntes Muster bei
FRITZ!Box-generiertem "XML" (siehe auch der charset-Bug in
fritzbox_anrufe's ``http.py``: fremde, von der FRITZ!Box gelieferte Werte
sind grundsätzlich defensiv zu behandeln, nie als garantiert wohlgeformt
anzunehmen). Zwei Korrekturen:

1. ``_fetch_via_log_path()`` unternimmt bei einem ``ParseError`` jetzt
   GENAU EINEN Reparaturversuch (``_sanitize_xml_text``): ungültige
   Steuerzeichen entfernen, einen bloßen ``&`` (der keinen gültigen
   Entity-Verweis einleitet) zu ``&amp;`` escapen, danach erneut parsen.
   Das erhält für die meisten Fälle die vollständige, kategorisierte
   Ansicht, statt sofort auf den Text-Rückfall auszuweichen.
2. Der Aufruf von ``_fetch_via_log_path()`` in ``_fetch()`` fängt jetzt
   BREIT (``except Exception``, nicht mehr nur die beiden bekannten
   Exception-Familien) ab - Weg 1 ist und bleibt experimentell/unbestätigt
   (siehe oben), daher darf JEDER Fehlschlag dort (auch ein zweiter,
   nicht reparierbarer ``ParseError``, ein `KeyError`, o. ä.) nur den
   Rückfall auf Weg 2 auslösen, niemals das gesamte Setup zum Absturz
   bringen - identisches Prinzip wie die durchgehend breiten
   `except Exception`-Blöcke in fritzbox_anrufe's ``settings_data.py`` für
   dessen ebenfalls unbestätigte data.lua-Wege.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import logging
import re
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, ParseError, fromstring

from fritzconnection.core.exceptions import FritzConnectionException, FritzSecurityError
from fritzconnection.core.fritzhttp import FritzHttp
from fritzconnection.core.utils import get_content_from, get_xml_root
from requests.exceptions import ConnectionError as RequestsConnectionError, RequestException

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .base import FritzBoxDevice
from .const import (
    ACTION_GET_DEVICE_LOG,
    ACTION_GET_DEVICE_LOG_PATH,
    CONF_MAX_EVENTS,
    DEFAULT_MAX_EVENTS,
    DOMAIN,
    EVENT_GROUP_LABEL_UNKNOWN,
    EVENT_GROUP_LABELS,
    EVENT_GROUP_UNKNOWN,
    EVENT_NEW_EREIGNIS,
    SERVICE_DEVICE_INFO,
)

_LOGGER = logging.getLogger(__name__)

EVENTS_UPDATE_INTERVAL = timedelta(minutes=5)

# Candidate output-argument names for X_AVM-DE_GetDeviceLogPath - AVMs
# eigene TR-064-Namenskonvention wäre "NewX_AVM-DE_DeviceLogPath", eine
# Community-Referenz (siehe Moduldoku) nennt schlicht "NewDeviceLogPath".
# Beide werden geprüft, bevor generisch nach jedem pfadartigen Wert im
# Ergebnis gesucht wird (siehe _extract_log_path) - dasselbe defensive
# "mehrere Namens-Kandidaten prüfen"-Muster wie tam.py:_URL_RESULT_KEYS.
_LOG_PATH_RESULT_KEYS = ("NewX_AVM-DE_DeviceLogPath", "NewDeviceLogPath")

_DATETIME_FORMAT = "%d.%m.%y %H:%M:%S"
# GetDeviceLog-Zeilen beginnen mit "DD.MM.YY HH:MM:SS <Meldungstext>".
_TEXT_LINE_PREFIX_LEN = len("01.02.23 05:45:54")

# v0.2.0-Reparaturversuch für kaputtes devicelog-XML (siehe Moduldoku oben):
# XML 1.0 erlaubt keine dieser Steuerzeichen (auch nicht escapt) - werden
# ersatzlos entfernt, statt zu versuchen sie sinnvoll darzustellen.
_INVALID_XML_CHARS_RE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f]")
# Ein "&", dem kein gültiger Entity-/Zeichenverweis folgt (&amp; &lt; &gt;
# &quot; &apos; &#123; &#x1F;) ist in XML nicht erlaubt - wird escapt.
_BARE_AMPERSAND_RE = re.compile(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9A-Fa-f]+;)")


@dataclass
class FritzEvent:
    """One parsed FRITZ!Box event-log entry, from either fetch path."""

    id: str
    group: str
    timestamp: datetime | None
    raw_date: str
    message: str

    @property
    def group_label(self) -> str:
        """Human-readable (German) label for :attr:`group`."""
        if self.group == EVENT_GROUP_UNKNOWN:
            return EVENT_GROUP_LABEL_UNKNOWN
        return EVENT_GROUP_LABELS.get(self.group, self.group.capitalize())

    def to_dict(self) -> dict[str, str | None]:
        """Flat, dashboard/automation-friendly representation."""
        return {
            "id": self.id,
            "group": self.group,
            "group_label": self.group_label,
            "date": self.timestamp.isoformat() if self.timestamp else None,
            "date_display": self.raw_date,
            "message": self.message,
        }

    @classmethod
    def from_xml_fields(cls, fields: dict[str, str]) -> FritzEvent:
        """Build from one <event> element's child tag/text pairs.

        Defensively tolerant of the exact tag set - only ``msg``/``group``/
        ``date``/``time``/``id`` are expected (see module docstring), but an
        unfamiliar or missing tag never breaks parsing, only leaves that one
        field blank/derived.
        """
        message = fields.get("msg") or fields.get("message") or ""
        group = (fields.get("group") or EVENT_GROUP_UNKNOWN).strip().lower() or EVENT_GROUP_UNKNOWN
        date_part = (fields.get("date") or "").strip()
        time_part = (fields.get("time") or "").strip()
        raw_date = f"{date_part} {time_part}".strip()
        timestamp = _parse_datetime(date_part, time_part)
        event_id = (fields.get("id") or "").strip() or _synthetic_id(raw_date, message)
        return cls(
            id=event_id,
            group=group,
            timestamp=timestamp,
            raw_date=raw_date,
            message=message,
        )

    @classmethod
    def from_text_line(cls, line: str) -> FritzEvent:
        """Build from one plain-text ``GetDeviceLog`` line (no group info)."""
        raw_date = ""
        message = line
        timestamp = None
        prefix = line[:_TEXT_LINE_PREFIX_LEN]
        try:
            timestamp = datetime.strptime(prefix, _DATETIME_FORMAT)
        except ValueError:
            pass
        else:
            raw_date = prefix
            message = line[_TEXT_LINE_PREFIX_LEN:].strip()
        return cls(
            id=_synthetic_id(raw_date or line, message),
            group=EVENT_GROUP_UNKNOWN,
            timestamp=timestamp,
            raw_date=raw_date,
            message=message,
        )


def _parse_datetime(date_part: str, time_part: str) -> datetime | None:
    """Parse the XML path's separate date ("DD.MM.YY")/time ("HH:MM:SS")."""
    if not date_part:
        return None
    combined = f"{date_part} {time_part}".strip()
    for fmt in (_DATETIME_FORMAT, "%d.%m.%y"):
        try:
            return datetime.strptime(combined, fmt)
        except ValueError:
            continue
    return None


def _synthetic_id(raw_date: str, message: str) -> str:
    """Stable id for entries with no native ``id`` field (or the text path).

    Used both as a dashboard-facing key and to detect genuinely new entries
    between two fetches (see :meth:`FritzEventsCoordinator._fire_new_events`)
    - a plain list index would change meaning every time an older entry
    scrolls out of the FRITZ!Box's own retained log.
    """
    digest = hashlib.sha1(f"{raw_date}|{message}".encode("utf-8")).hexdigest()
    return digest[:12]


class FritzEventsCoordinator(DataUpdateCoordinator[list[FritzEvent]]):
    """Coordinator that periodically fetches the FRITZ!Box event log."""

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, device: FritzBoxDevice
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="fritzbox_ereignisse",
            update_interval=EVENTS_UPDATE_INTERVAL,
        )
        self.config_entry = config_entry
        self._device = device
        # Welcher Weg beim letzten erfolgreichen Abruf funktioniert hat -
        # von sensor.py als Diagnose-Attribut mit ausgegeben (siehe dort).
        self.last_source: str | None = None
        # None bis zum ersten erfolgreichen Abruf - siehe _fire_new_events
        # für den Grund, warum dann bewusst NICHTS gefeuert wird.
        self._known_ids: set[str] | None = None

    async def _async_update_data(self) -> list[FritzEvent]:
        """Fetch the current event log (executor job, TR-064 + optional HTTP)."""
        try:
            events = await self.hass.async_add_executor_job(self._fetch)
        except FritzSecurityError as ex:
            raise UpdateFailed(
                "Dem FRITZ!Box-Konto fehlt die Berechtigung"
                f" 'FRITZ!Box-Einstellungen' für den Zugriff auf das"
                f" Ereignisprotokoll: {ex}"
            ) from ex
        except (FritzConnectionException, RequestsConnectionError, RequestException) as ex:
            raise UpdateFailed(f"Fehler beim Abrufen der FRITZ!Box-Ereignisse: {ex}") from ex

        max_events = self.config_entry.options.get(CONF_MAX_EVENTS, DEFAULT_MAX_EVENTS)
        events = _sorted_newest_first(events)[:max_events]
        self._fire_new_events(events)
        return events

    def _fetch(self) -> list[FritzEvent]:
        """Try the structured XML path first, then the plain-text fallback.

        BLOCKING - run in an executor job. Returns whichever path succeeds
        first; only raises once BOTH have failed, mirroring
        ``settings_data.py``'s "never fail unless everything fails"
        philosophy in fritzbox_anrufe - except here the event log IS this
        integration's only sensor, so - unlike that optional add-on sensor -
        a combined failure legitimately marks the entity unavailable.
        """
        try:
            events = self._fetch_via_log_path()
            if events is not None:
                self.last_source = "xml"
                return events
        except Exception as ex:  # noqa: BLE001 - Weg 1 ist experimentell/
            # unbestätigt (siehe Moduldoku) - JEDER Fehler hier darf nur den
            # Rückfall auf Weg 2 auslösen, nie das gesamte Setup zum
            # Absturz bringen. Behebt den in v0.2.0 gemeldeten
            # Einrichtungsfehler ("not well-formed (invalid token)"): ein
            # xml.etree.ElementTree.ParseError propagierte zuvor ungefangen
            # durch, weil er weder FritzConnectionException noch
            # RequestException ist - siehe Moduldoku für Details.
            _LOGGER.debug(
                "Ereignisse: X_AVM-DE_GetDeviceLogPath fehlgeschlagen (%s: %s),"
                " versuche GetDeviceLog als Rückfall",
                type(ex).__name__,
                ex,
            )

        events = self._fetch_via_plain_log()
        self.last_source = "text"
        return events

    def _fetch_via_log_path(self) -> list[FritzEvent] | None:
        """Structured XML path (FRITZ!OS 7.90+). ``None`` if unsupported."""
        fc = self._device.fc
        assert fc is not None
        result = fc.call_action(SERVICE_DEVICE_INFO, ACTION_GET_DEVICE_LOG_PATH)
        path = _extract_log_path(result)
        if not path:
            _LOGGER.debug(
                "Ereignisse: X_AVM-DE_GetDeviceLogPath lieferte keinen"
                " erkennbaren Pfad zurück (Antwort: %s)",
                sorted(result.keys()) if isinstance(result, dict) else result,
            )
            return None

        origin = FritzHttp(fc).router_url
        url = urljoin(origin, path)
        try:
            root = get_xml_root(url, session=fc.session)
        except ParseError as ex:
            # v0.2.0: einmaliger Reparaturversuch statt sofort aufzugeben -
            # siehe Moduldoku ("Fix in v0.2.0") für die Ursache. Schlägt
            # auch DAS fehl, wird die (dann zweite) ParseError vom
            # aufrufenden _fetch() breit abgefangen und löst dort den
            # Rückfall auf Weg 2 aus - hier wird bewusst nichts geschluckt.
            _LOGGER.debug(
                "Ereignisse: devicelog-XML nicht wohlgeformt (%s) - versuche"
                " Reparatur (Steuerzeichen/bloße '&' escapen)",
                ex,
            )
            raw = get_content_from(url, session=fc.session)
            root = fromstring(_sanitize_xml_text(raw))
        events = [
            FritzEvent.from_xml_fields(
                {child.tag.lower(): (child.text or "").strip() for child in event_el}
            )
            for event_el in _iter_event_elements(root)
        ]
        return events

    def _fetch_via_plain_log(self) -> list[FritzEvent]:
        """Plain-text fallback (``GetDeviceLog`` -> ``NewDeviceLog``)."""
        fc = self._device.fc
        assert fc is not None
        result = fc.call_action(SERVICE_DEVICE_INFO, ACTION_GET_DEVICE_LOG)
        raw = str(result.get("NewDeviceLog") or "")
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        return [FritzEvent.from_text_line(line) for line in lines]

    def _fire_new_events(self, events: list[FritzEvent]) -> None:
        """Fire :data:`EVENT_NEW_EREIGNIS` for entries new since the last fetch.

        Bewusst NICHT beim allerersten Abruf nach einem (Neu-)Start gefeuert
        (``_known_ids is None``) - identisches Prinzip wie
        ``EVENT_NEW_VOICEMAIL_MESSAGE`` in fritzbox_anrufe, sonst gäbe es bei
        jedem Home-Assistant-Neustart Events für längst bekannte Einträge.
        """
        current_ids = {event.id for event in events}
        if self._known_ids is not None:
            new_ids = current_ids - self._known_ids
            if new_ids:
                by_id = {event.id: event for event in events}
                for event_id in new_ids:
                    event = by_id[event_id]
                    self.hass.bus.async_fire(
                        EVENT_NEW_EREIGNIS,
                        {
                            "entry_id": self.config_entry.entry_id,
                            **event.to_dict(),
                        },
                    )
        self._known_ids = current_ids


def _extract_log_path(result: dict[str, object]) -> str | None:
    """Pull the device-log path out of a GetDeviceLogPath response.

    Checks the known candidate argument names first, then falls back to
    scanning every value for something path-shaped - see
    ``_LOG_PATH_RESULT_KEYS`` above for why more than one name is checked.
    """
    if not isinstance(result, dict):
        return None
    for key in _LOG_PATH_RESULT_KEYS:
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for value in result.values():
        if isinstance(value, str) and value.strip().startswith("/"):
            return value.strip()
    return None


def _sanitize_xml_text(text: str) -> str:
    """Best-effort repair for malformed devicelog XML (v0.2.0 fix).

    Removes characters XML 1.0 never permits (not even escaped) and escapes
    a bare ``&`` that isn't already part of a recognized entity/character
    reference - the specific issue behind the reported "not well-formed
    (invalid token)" setup error, see the module docstring. Deliberately
    minimal: this repairs the two concrete problems observed, not a general
    XML recovery tool - if the result is still malformed,
    ``xml.etree.ElementTree.fromstring`` simply raises again and the caller
    falls back to the plain-text path instead.
    """
    text = _INVALID_XML_CHARS_RE.sub("", text)
    return _BARE_AMPERSAND_RE.sub("&amp;", text)


def _iter_event_elements(root: Element):
    """Yield every ``<event>`` element, regardless of exact nesting depth."""
    yield from root.iter("event")


def _sorted_newest_first(events: list[FritzEvent]) -> list[FritzEvent]:
    """Sort by timestamp descending; entries without one keep their order at the end."""
    with_timestamp = [event for event in events if event.timestamp is not None]
    without_timestamp = [event for event in events if event.timestamp is None]
    with_timestamp.sort(key=lambda event: event.timestamp, reverse=True)
    return with_timestamp + without_timestamp
