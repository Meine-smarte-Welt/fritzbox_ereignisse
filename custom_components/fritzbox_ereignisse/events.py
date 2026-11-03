# SHA256 (Inhalt ab Zeile 2, d.h. dieser Datei ohne diese erste Zeile): ce0ca7811e906dc4a6cced9c79dd7df1d2c4e0a829b40ef65ba3828660f4ffb5
"""Fetch + parse the FRITZ!Box event log ("Ereignisse").

Es gibt inzwischen DREI Wege zum selben Protokoll, das die FRITZ!Box-
Oberfläche unter System > Ereignisse anzeigt:

0. ``query.lua`` (seit v0.3.0, EXPERIMENTELL, bevorzugt): dieselbe
   sitzungsbasierte ("sid") Web-UI-interne Abfrage, die die FRITZ!Box-
   Oberfläche SELBST verwendet, um die Ereignisse-Seite live zu befüllen -
   ``mq_log=logger:status/log_separate/list(time,msg,ref,type)`` gegen
   ``/query.lua``. Community-Referenz: ip-phone-forum.de, Thread "Abfrage
   von query.lua und data.lua mit OS Version 07.27". Kein TR-064-SOAP;
   Anmeldung/Session über ``FritzHttp._get_sid()``/``call_url()``
   (fritzconnection bringt diesen Baustein bereits mit - identisches
   Prinzip wie der Anrufbeantworter-Audio-Download in fritzbox_anrufe's
   ``tam.py`` bzw. dessen ``settings_data.py``). Da dies exakt die
   Abfrage ist, die auch die Live-Ansicht der Weboberfläche befüllt, ist
   dies der Weg mit der größten Chance auf tagesaktuelle Daten.
1. ``X_AVM-DE_GetDeviceLogPath`` (FRITZ!OS 7.90+, TR-064): liefert einen
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

Alle drei Wege werden defensiv nacheinander versucht (Weg 0 zuerst, dann
Weg 1, dann Weg 2); erst wenn ALLE DREI fehlschlagen, meldet der
Coordinator ``UpdateFailed`` - identisches Prinzip wie ``settings_data.py``
in fritzbox_anrufe. KEINER der drei Wege ist an echter Hardware
vollständig verifiziert (siehe README) - noch unbekannt, welcher
FRITZ!OS-Mindeststand/welche Kontoberechtigung in der Praxis tatsächlich
reicht bzw. ob AVM ``query.lua`` auf allen Modellen/Firmwareständen
unverändert bereitstellt (ein undokumentierter, interner Endpunkt, der
sich jederzeit ändern kann).

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

Fix/Feature in v0.3.0 - fehlende Kategorien + veraltete Daten
---------------------------------------------------------------------
Ein Nutzer verglich die Karte direkt mit der echten FRITZ!Box-
Weboberfläche (Screenshots) und meldete zwei Probleme: (1) die Karte zeigt
ausschließlich "Sonstiges" statt der auf der Box sichtbaren Reiter
Telefonie/Internetverbindung/USB-Geräte/WLAN/System, und (2) der neueste
Eintrag in der Karte war zum Zeitpunkt des Vergleichs mehrere Stunden
älter als der neueste Eintrag in der echten Weboberfläche. Diagnose (aus
dem Sensor-Attribut ``source``, das beim Nutzer "text" war): Weg 1
(``X_AVM-DE_GetDeviceLogPath``) schlägt auf dieser FRITZ!Box/Firmware aus
unbekanntem Grund fehl (kein FRITZ!OS 7.90+, andere Kontoberechtigung
nötig, o. ä. - der breite ``except Exception`` aus dem v0.2.0-Fix
verschluckt den genauen Grund bewusst, siehe oben), sodass ausschließlich
der Text-Rückfall (Weg 2, ``GetDeviceLog``) lief - und dessen bereits in
den "Bekannten Einschränkungen" dokumentierte Lücke (fehlende
Eintragstypen) erklärt beide Symptome zugleich: keine Kategorien (der
Text-Rückfall kennt grundsätzlich keine Kategorie) UND scheinbar
veraltete Daten (wenn ``GetDeviceLog`` bestimmte, neuere Eintragstypen
schlicht nie liefert, wirkt der zuletzt sichtbare Eintrag eines
gelieferten Typs "alt", obwohl die Box selbst längst neuere - andersartige
- Einträge kennt). Zwei Korrekturen, unabhängig voneinander wirksam:

1. **Neuer Weg 0** (``_fetch_via_query_log()``, ``query.lua``, siehe oben)
   - wird jetzt VOR Weg 1 versucht. Da dies exakt dieselbe Abfrage ist,
   die auch die Live-Ansicht der echten Weboberfläche (das Vergleichsbild
   des Nutzers) befüllt, ist dies der plausibelste Weg zu tagesaktuellen,
   vollständigen Daten - aber ein undokumentierter interner Endpunkt,
   daher weiterhin EXPERIMENTELL und mit dem gleichen breiten
   ``except Exception``-Rückfallprinzip abgesichert wie Weg 1.
2. **Text-Heuristik für Kategorien** (``_classify_message_group()``,
   ``_derive_group()``): unabhängig davon, ÜBER WELCHEN Weg ein Ereignis
   ankommt, wird - falls die Box selbst kein (oder ein leeres) Gruppen-
   Kürzel liefert (das betrifft IMMER Weg 2, und ggf. auch Weg 0/1, falls
   deren Felder anders benannt sind als erwartet) - der Meldungstext
   gegen bekannte, typische FRITZ!Box-Formulierungen (deutsch) geprüft und
   einer der Kategorien aus ``EVENT_GROUP_LABELS`` zugeordnet (z. B.
   "Anruf"/"Anrufbeantworter" -> Telefonie, "USB" -> USB-Geräte,
   "Internetverbindung"/"DSL-Synchronisierung" -> Internetverbindung).
   Das behebt "alles landet unter Sonstiges" AUCH dann, wenn Weg 0 sich
   als auf dieser Hardware nicht unterstützt herausstellt und weiterhin
   nur der Text-Rückfall läuft. Rein heuristisch (Best-Effort) - eine
   unbekannte/nicht erkannte Formulierung landet weiterhin unter
   "Sonstiges", nie falsch verworfen; ein von der Box selbst geliefertes
   Gruppen-Kürzel (Weg 1) hat immer Vorrang vor der Heuristik.

Fix in v0.4.0 - Kategorie "System" fehlte weiterhin
---------------------------------------------------------------------
Nach v0.3.0 meldete derselbe Nutzer, dass "System" als Kategorie
weiterhin nicht auftauchte, obwohl die echte FRITZ!Box-Weboberfläche
(Bild 1 aus v0.3.0) sie klar als Reiter zeigt. Ursache: die v0.3.0-
Heuristik behandelte "System" als EIN WEITERES eng gefasstes Stichwort-
Muster unter mehreren SELBST ERFUNDENEN Zusatzkategorien ("Heimnetz"/
"DECT"/"VPN"/"Smart Home") - Kategorien, die auf der echten Box, soweit
aus dem Bildvergleich des Nutzers ersichtlich, GAR NICHT als eigene
Reiter existieren (dort gibt es nur Alle/Telefonie/Internetverbindung/
USB-Geräte/WLAN/System). Ein System-Ereignis, dessen Text keines der
engen Muster ("Firmware", "Neustart", "Zeitzone", ...) traf, landete
dadurch fälschlich unter "Sonstiges" oder einer der erfundenen
Zusatzkategorien, obwohl es auf der echten Box unter "System" erscheint.

Korrektur: ``_classify_message_group()`` prüft jetzt nur noch die vier
Kategorien, die nachweislich auch als eigene Reiter existieren
(Telefonie/WLAN/USB-Geräte/Internetverbindung), und liefert für JEDEN
nicht-leeren Meldungstext, der keines dieser vier Muster trifft, jetzt
``"sys"`` (System) statt ``None`` - "System" ist also der echte
Auffang-Topf für alles Übrige, nicht eine fünfte spezifische Kategorie
neben "Sonstiges". "Sonstiges" bleibt dadurch praktisch nur noch für den
Randfall eines leeren Meldungstexts übrig. Die erfundenen Zusatz-
Kategorien-Kürzel ("dect"/"vpn"/"network"/"smarthome") bleiben in
``EVENT_GROUP_LABELS`` bestehen (falls ein zukünftiger Fetch-Weg sie
einmal nativ als Gruppen-Kürzel liefert), werden aber seit v0.4.0 von
der Text-Heuristik selbst nicht mehr vergeben.

Fix in v1.1.0 - Abruf des XML-Protokolls (Issue #1)
---------------------------------------------------
Das Protokoll wurde bisher nur per HTTP geladen und ``<Event>``-Elemente
nur in einer Schreibweise erkannt. Jetzt: zuerst HTTPS am SecurityPort der
FRITZ!Box (``GetSecurityPort``, Rückfall 49443, selbst signiertes Zertifikat
-> ``verify=False``), danach HTTP; Tags werden ohne Beachtung der Groß-/
Kleinschreibung gelesen; eine HTML-Antwort (z. B. Anmeldeseite) gilt als
Fehler statt als leeres Protokoll. Außerdem meldet der Koordinator seit
v1.1.0 neue Einträge und Verbindungsverlust ans Notification Center
(``notification_bridge.py``). Nicht an echter Hardware geprüft.

Nachtrag zu v1.1.0 (Issue #1, Kommentar zu FRITZ!OS 8.25) - drei weitere
Korrekturen:

1. Host-Aufbau: Der Host wird von Schema, Pfad und Port befreit
   (:func:`_normalize_host`), nur echte IPv6-Adressen bekommen eckige
   Klammern. Zuvor löste jede Adresse mit ``:`` den Fehler "Invalid IPv6
   URL" aus. ``urljoin`` liegt jetzt innerhalb des ``try``; ein
   ungültiger Ursprung überspringt nur sich selbst. Zusätzlicher letzter
   Ursprung: HTTP am TR-064-Port (laut Meldung liefert er dasselbe XML).
2. Eindeutiger Schlüssel: Die ``id`` aus dem XML (bzw. ``ref`` aus
   query.lua) bezeichnet offenbar die Meldungsart und wiederholt sich. Die
   Ereignis-``id`` ist jetzt ein Hash aus Zeitstempel, Kennung und Text
   (:func:`_make_ids_unique` unterscheidet zusätzlich völlig identische
   Einträge). Die Kennung der Box bleibt als ``code`` erhalten. Dadurch
   gelten neue Einträge einer bereits bekannten Art als neu.
3. query.lua auf FRITZ!OS 8.25 liefert nur ``mq_log``, teils als leere
   Liste. Der Weg fällt wie bisher auf XML zurück; das Debug-Log nennt jetzt
   die Form der Antwort (ohne Inhalte), damit sich das Format klären lässt.

Feature in v1.0.0 - Verlaufstiefe wahlweise nach Tagen statt nur Anzahl
---------------------------------------------------------------------
Bisher (bis v0.4.0) wurde die Verlaufstiefe ausschließlich über eine feste
Anzahl (``CONF_MAX_EVENTS``) begrenzt. Seit v1.0.0 lässt sich stattdessen
auch ein Alters-Fenster in Tagen wählen (``CONF_EVENT_LIMIT_TYPE`` /
``CONF_MAX_EVENT_DAYS``, siehe const.py) - analog zum Anzahl-oder-Tage-
Umschalter der drei Anruflisten-Sensoren in fritzbox_anrufe
(``CALL_LOG_LIMIT_COUNT``/``CALL_LOG_LIMIT_DAYS``). Anders als dort gibt es
hier nur EINEN Sensor und keinen fest begrenzten, gemeinsam genutzten
Abruf-Zeitraum (die FRITZ!Box liefert bei jedem Abruf ohnehin ihr
gesamtes, eigenes Ereignisprotokoll) - im Tage-Modus werden daher einfach
alle Einträge verworfen, deren Zeitstempel älter als der gewählte
Tage-Wert ist (bzw. die - wie mitunter beim Text-Rückfall Weg 2 - gar
keinen auswertbaren Zeitstempel haben, siehe :func:`_apply_event_limit`),
statt wie bisher hart auf die letzten N Einträge zu kürzen.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import ipaddress
import logging
import re
from typing import Any, Final
from urllib.parse import urljoin
import warnings
from xml.etree.ElementTree import Element, ParseError, fromstring

from fritzconnection.core.exceptions import FritzConnectionException, FritzSecurityError
from fritzconnection.core.fritzhttp import FritzHttp
from requests.exceptions import ConnectionError as RequestsConnectionError, RequestException
from urllib3.exceptions import InsecureRequestWarning

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .base import FritzBoxDevice
from .const import (
    ACTION_GET_DEVICE_LOG,
    ACTION_GET_DEVICE_LOG_PATH,
    ACTION_GET_SECURITY_PORT,
    CONF_EVENT_LIMIT_TYPE,
    CONF_MAX_EVENT_DAYS,
    CONF_MAX_EVENTS,
    DEFAULT_EVENT_LIMIT_TYPE,
    DEFAULT_MAX_EVENT_DAYS,
    DEFAULT_MAX_EVENTS,
    DEFAULT_SECURITY_PORT,
    DOMAIN,
    EVENT_GROUP_LABEL_UNKNOWN,
    EVENT_GROUP_LABELS,
    EVENT_GROUP_UNKNOWN,
    EVENT_LIMIT_DAYS,
    EVENT_NEW_EREIGNIS,
    MQ_LOG_SEPARATE_ALL,
    NC_TYPE_CONNECTION_LOST,
    NC_TYPE_DEFAULT_FOR_GROUP,
    NC_TYPE_FOR_GROUP,
    QUERY_LUA_PATH,
    SERVICE_DEVICE_INFO,
)
from .notification_bridge import NotificationBridge

_LOGGER = logging.getLogger(__name__)

EVENTS_UPDATE_INTERVAL = timedelta(minutes=5)
# Zeitlimit (Sekunden) für den Download der devicelog-XML (v1.1.0).
LOG_XML_TIMEOUT: Final = 30
# Obergrenze für den Meldungstext in einer Notification-Center-Meldung.
NC_MESSAGE_MAX_LEN: Final = 300

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

# v0.3.0/v0.4.0 - Text-Heuristik für Kategorien (siehe Moduldoku,
# "Fix/Feature in v0.3.0" + "Fix in v0.4.0"): reihenfolgeabhängige Liste
# aus (Gruppen-Kürzel, [Muster]) - das erste passende Muster gewinnt.
# NUR die vier Kategorien, die auch in der echten FRITZ!Box-Weboberfläche
# als eigene Reiter neben "System" auftauchen (siehe Bild-Vergleich des
# Nutzers: Telefonie/Internetverbindung/USB-Geräte/WLAN/System). Bewusst
# NUR auf typische, wiederkehrende FRITZ!Box-Formulierungen (deutsch)
# gestützt - keine Garantie auf Vollständigkeit, siehe README "Bekannte
# Einschränkungen". Ein Treffer hier wird NUR verwendet, wenn die Box
# selbst kein Gruppen-Kürzel geliefert hat (siehe _derive_group) - ein von
# der Box geliefertes Kürzel hat immer Vorrang.
#
# WICHTIG (v0.4.0): "System" ist bewusst KEIN Eintrag in dieser Liste,
# sondern der universelle Auffang-Wert von _classify_message_group() für
# alles, was hier NICHT passt - siehe dortige Begründung.
_MESSAGE_GROUP_PATTERNS: Final[tuple[tuple[str, re.Pattern[str]], ...]] = tuple(
    (group, re.compile(pattern, re.IGNORECASE))
    for group, pattern in (
        (
            "tel",
            r"anruf\w*|anrufbeantworter|telefonanlage|telefonie|rufumleitung|"
            r"rufnummer|faxnachricht|\bsip\b|\bvoip\b",
        ),
        ("wlan", r"\bwlan\b|wpa[2-3]?[- ]?(psk|schlüssel)?"),
        ("usb", r"\busb\b|massenspeicher"),
        (
            "internet",
            r"internetverbindung|dsl[- ]?synchronisierung|\bppp\b|"
            r"online-zähler|zwangstrennung|internetzugang|\bipv[46]\b",
        ),
    )
)


def _classify_message_group(message: str) -> str | None:
    """Best-effort-Kategorie anhand des Meldungstexts (siehe oben).

    Reines Muster-Matching, kein Aufruf an die FRITZ!Box - daher ohne
    Hardware testbar und ohne jedes Risiko für den Abrufpfad selbst.

    v0.4.0-Fix: liefert für JEDEN nicht-leeren Meldungstext, der keines
    der vier spezifischen Muster oben trifft, jetzt ``"sys"`` (System)
    statt ``None``. Grund: ein Nutzer meldete nach v0.3.0, dass die
    Kategorie "System" weiterhin fehlte, obwohl sie in der echten
    FRITZ!Box-Weboberfläche neben Telefonie/Internetverbindung/
    USB-Geräte/WLAN klar sichtbar ist (siehe Moduldoku). Ursache: bis
    v0.3.0 war "System" nur EIN WEITERES eng gefasstes Stichwort-Muster
    unter mehreren erfundenen Zusatzkategorien (u. a. "Heimnetz"/"DECT"/
    "VPN"/"Smart Home", die auf der echten Box gar nicht als eigene
    Reiter existieren) - viele eigentlich System-Meldungen trafen keines
    dieser engen Muster und landeten fälschlich unter "Sonstiges" (oder
    einer der erfundenen Zusatzkategorien). Da die echte Oberfläche
    NACHWEISLICH nur fünf Reiter kennt (Alle plus die vier oben plus
    System), ist "System" tatsächlich der Auffang-Topf für alles
    Restliche - nicht eine fünfte spezifische Kategorie neben "Sonstiges".
    ``None`` (-> "Sonstiges") bleibt nur für den Randfall eines leeren
    Meldungstexts.
    """
    if not message:
        return None
    for group, pattern in _MESSAGE_GROUP_PATTERNS:
        if pattern.search(message):
            return group
    return "sys"


def _derive_group(explicit_group: str | None, message: str) -> str:
    """Gruppen-Kürzel: von der Box geliefertes Kürzel hat Vorrang.

    Fehlt es (leer/``None`` - insb. immer bei Weg 2, ggf. auch bei Weg 0/1),
    wird die Text-Heuristik versucht; schlägt auch die fehl (nur bei
    leerem Meldungstext, siehe :func:`_classify_message_group`), bleibt es
    bei :data:`EVENT_GROUP_UNKNOWN` ("Sonstiges").
    """
    explicit = (explicit_group or "").strip().lower()
    if explicit:
        return explicit
    return _classify_message_group(message) or EVENT_GROUP_UNKNOWN


@dataclass
class FritzEvent:
    """One parsed FRITZ!Box event-log entry, from either fetch path."""

    id: str
    group: str
    timestamp: datetime | None
    raw_date: str
    message: str
    # Kennung, die die FRITZ!Box selbst mitliefert (XML ``id``, query.lua
    # ``ref``). Sie bezeichnet laut Issue #1 offenbar die MELDUNGSART, nicht den
    # einzelnen Eintrag, und ist daher NICHT eindeutig. ``id`` ist seit v1.1.0
    # ein eigener, eindeutiger Schlüssel; die Kennung der Box steht in ``code``.
    code: str | None = None

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
            "code": self.code,
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
        group = _derive_group(fields.get("group"), message)
        date_part = (fields.get("date") or "").strip()
        time_part = (fields.get("time") or "").strip()
        raw_date = f"{date_part} {time_part}".strip()
        timestamp = _parse_datetime(date_part, time_part)
        # Issue #1 (Nachtrag, v1.1.0): Die ``id`` der Box wiederholt sich
        # (z. B. dieselbe Zahl für jede "Anmeldung des Benutzers ..."). Als
        # Schlüssel taugt sie nur zusammen mit Zeitstempel und Text; sonst
        # gälten neue Einträge einer bekannten Meldungsart nie als neu.
        code = (fields.get("id") or "").strip()
        return cls(
            id=_synthetic_id(f"{raw_date}|{code}", message),
            group=group,
            timestamp=timestamp,
            raw_date=raw_date,
            message=message,
            code=code or None,
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
            # v0.3.0: kein natives Gruppen-Kürzel auf diesem Weg - siehe
            # ob die Text-Heuristik (_derive_group) trotzdem eine Kategorie
            # erkennt, statt hier hart EVENT_GROUP_UNKNOWN zu setzen.
            group=_derive_group(None, message),
            timestamp=timestamp,
            raw_date=raw_date,
            message=message,
        )

    @classmethod
    def from_query_fields(cls, fields: dict[str, object]) -> FritzEvent:
        """Build from one ``query.lua``/``log_separate``-Eintrag (Weg 0, v0.3.0).

        Erwartete Feldnamen laut Community-Referenz (siehe Moduldoku):
        ``time``/``msg``/``ref``/``type``. ``type`` wird BEWUSST NICHT als
        Gruppen-Kürzel übernommen - seine Bedeutung/Werte-Zuordnung ist
        nicht verlässlich dokumentiert, ein falsch geratenes Mapping wäre
        schlimmer als gar keine Kategorie (siehe Moduldoku). Stattdessen
        läuft auch hier die Text-Heuristik über ``_derive_group``. ``ref``
        wird - falls vorhanden - als stabile Kennung verwendet (identisches
        Prinzip wie ``id`` bei Weg 1).
        """
        message = str(fields.get("msg") or fields.get("message") or "").strip()
        raw_date = str(fields.get("time") or fields.get("date") or "").strip()
        timestamp = _parse_query_datetime(raw_date)
        ref = str(fields.get("ref") or "").strip()
        group = _derive_group(None, message)
        return cls(
            # ``ref`` allein ist nicht als eindeutig belegt (siehe ``code``).
            id=_synthetic_id(f"{raw_date or message}|{ref}", message),
            group=group,
            timestamp=timestamp,
            raw_date=raw_date,
            message=message,
            code=ref or None,
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


def _parse_query_datetime(raw: str) -> datetime | None:
    """Parse the ``query.lua``/Weg-0 ``time``-Feld (v0.3.0).

    Community-Beispiele zeigen dasselbe Format wie ``GetDeviceLog``
    (``DD.MM.YY HH:MM:SS``) - wird zuerst versucht, danach defensiv ein
    paar naheliegende Varianten. Unparsbares wird nie verworfen: der
    Eintrag bleibt über ``raw_date`` trotzdem vollständig sichtbar (siehe
    :meth:`FritzEvent.from_query_fields`), nur ohne sortierbaren
    Zeitstempel.
    """
    raw = raw.strip()
    if not raw:
        return None
    for fmt in (_DATETIME_FORMAT, "%d.%m.%Y %H:%M:%S", "%d.%m.%y"):
        try:
            return datetime.strptime(raw, fmt)
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


def _make_ids_unique(events: list[FritzEvent]) -> list[FritzEvent]:
    """Identische Einträge (gleicher Schlüssel) unterscheidbar machen.

    Zwei Meldungen mit gleichem Zeitstempel, gleicher Kennung und gleichem Text
    erzeugen denselben Hash. Würden sie zusammenfallen, ginge die zweite für
    die Erkennung neuer Einträge verloren. Das erste Vorkommen behält seine
    ``id``, jedes weitere bekommt ``-1``, ``-2`` ... angehängt. Da die
    Einträge untereinander identisch sind, ist ihre Reihenfolge belanglos: die
    Menge der IDs bleibt zwischen zwei Abrufen stabil, solange sich die Box
    nicht ändert, und ein neuer, identischer Eintrag liefert genau eine neue ID.
    """
    seen: dict[str, int] = {}
    for event in events:
        count = seen.get(event.id, 0)
        seen[event.id] = count + 1
        if count:
            event.id = f"{event.id}-{count}"
    return events


def _normalize_host(address: object) -> str:
    """Host einer FRITZ!Box-Adresse für den Einsatz in einer URL.

    Entfernt Schema, Pfad und Port. Nur echte IPv6-Adressen werden in eckige
    Klammern gesetzt (Issue #1, Nachtrag: bisher jede Adresse mit ``:``, was
    bei ``host:port`` oder ``https://host`` zu "Invalid IPv6 URL" führte).
    Liefert einen leeren String, wenn kein Host erkennbar ist.
    """
    host = re.sub(r"^[a-z][a-z0-9+.-]*://", "", str(address or "").strip(), flags=re.IGNORECASE)
    host = re.split(r"[/?#]", host, maxsplit=1)[0]
    if host.startswith("["):
        end = host.find("]")
        bare = host[1:end] if end > 0 else host.strip("[]")
    else:
        try:
            ipaddress.IPv6Address(host.split("%", 1)[0])
        except ValueError:
            bare = host.split(":", 1)[0]  # host:port -> host
        else:
            bare = host
    bare = bare.strip()
    if not bare:
        return ""
    try:
        ipaddress.IPv6Address(bare.split("%", 1)[0])
    except ValueError:
        return bare
    return "[" + bare.replace("%", "%25") + "]"


def _describe_shape(value: object, _depth: int = 0) -> str:
    """Form einer JSON-Antwort für das Debug-Log: Typen, Längen, Schlüsselnamen.

    Enthält nie Werte (also auch keine Meldungstexte).
    """
    if _depth > 3:
        return "…"
    if isinstance(value, dict):
        inner = ", ".join(
            f"{key}: {_describe_shape(item, _depth + 1)}" for key, item in list(value.items())[:8]
        )
        return "{" + inner + "}"
    if isinstance(value, list):
        first = _describe_shape(value[0], _depth + 1) if value else ""
        return f"Liste[{len(value)}]" + (f" aus {first}" if first else "")
    return type(value).__name__


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
        # "query" (Weg 0, seit v0.3.0) / "xml" (Weg 1) / "text" (Weg 2).
        self.last_source: str | None = None
        # None bis zum ersten erfolgreichen Abruf - siehe _fire_new_events
        # für den Grund, warum dann bewusst NICHTS gefeuert wird.
        self._known_ids: set[str] | None = None
        # HTTPS-Port der Box (GetSecurityPort), beim ersten Bedarf ermittelt.
        self._security_port: int | None = None
        # Notification Center (seit v1.1.0, optional - siehe
        # notification_bridge.py). Wird von __init__.py gesetzt; ohne
        # Notification Center passiert nichts.
        self.nc: NotificationBridge | None = None
        self._nc_connection_lost = False
        # Anzahl tatsächlich gesendeter Meldungen je Art (nur Zähler, für die
        # Diagnose - keine Inhalte).
        self.nc_sent: dict[str, int] = {}

    async def _async_update_data(self) -> list[FritzEvent]:
        """Fetch the current event log (executor job, TR-064 + optional HTTP)."""
        try:
            events = await self.hass.async_add_executor_job(self._fetch)
        except FritzSecurityError as ex:
            self._nc_set_connection_lost(True)
            raise UpdateFailed(
                "Dem FRITZ!Box-Konto fehlt die Berechtigung"
                f" 'FRITZ!Box-Einstellungen' für den Zugriff auf das"
                f" Ereignisprotokoll: {ex}"
            ) from ex
        except (FritzConnectionException, RequestsConnectionError, RequestException) as ex:
            self._nc_set_connection_lost(True)
            raise UpdateFailed(f"Fehler beim Abrufen der FRITZ!Box-Ereignisse: {ex}") from ex

        self._nc_set_connection_lost(False)
        limit_type, limit_value = _limit_for(self.config_entry)
        events = _apply_event_limit(_sorted_newest_first(events), limit_type, limit_value)
        self._fire_new_events(events)
        return events

    def _fetch(self) -> list[FritzEvent]:
        """Fetch the log via the first working path, with unique entry ids.

        BLOCKING - run in an executor job. Siehe :meth:`_fetch_raw` für die
        Reihenfolge der Wege; hier werden zusätzlich identische Einträge
        (gleiche Sekunde, gleicher Text) mit unterscheidbaren ``id`` versehen.
        """
        return _make_ids_unique(self._fetch_raw())

    def _fetch_raw(self) -> list[FritzEvent]:
        """Try query.lua, then the structured XML path, then plain text.

        BLOCKING - run in an executor job. Returns whichever path succeeds
        first; only raises once ALL THREE have failed, mirroring
        ``settings_data.py``'s "never fail unless everything fails"
        philosophy in fritzbox_anrufe - except here the event log IS this
        integration's only sensor, so - unlike that optional add-on sensor -
        a combined failure legitimately marks the entity unavailable.
        """
        try:
            events = self._fetch_via_query_log()
            if events is not None:
                self.last_source = "query"
                return events
        except Exception as ex:  # noqa: BLE001 - Weg 0 ist ein
            # undokumentierter, interner Endpunkt (siehe Moduldoku,
            # "Fix/Feature in v0.3.0") - JEDER Fehler hier (fehlende
            # Anmeldung, unerwartetes/nicht-JSON-Antwortformat, blockierter
            # Endpunkt auf dieser Firmware, ...) darf nur den Rückfall auf
            # Weg 1 auslösen, nie das gesamte Setup zum Absturz bringen.
            _LOGGER.debug(
                "Ereignisse: query.lua fehlgeschlagen (%s: %s), versuche"
                " X_AVM-DE_GetDeviceLogPath als Rückfall",
                type(ex).__name__,
                ex,
            )

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

    def _fetch_via_query_log(self) -> list[FritzEvent] | None:
        """Weg 0 (v0.3.0, EXPERIMENTELL): dieselbe Abfrage wie die Weboberfläche.

        ``None`` (statt eine leere Liste), wenn die Antwort keine
        erkennbare Eintragsliste enthält - signalisiert dem Aufrufer
        "dieser Weg ist auf dieser Box (so) nicht nutzbar", genau wie
        :meth:`_fetch_via_log_path` es für Weg 1 tut, statt fälschlich
        "0 Ereignisse" zu melden.
        """
        fc = self._device.fc
        assert fc is not None
        http = FritzHttp(fc)
        url = f"{http.router_url}{QUERY_LUA_PATH}"
        response = http.call_url(url, {"mq_log": MQ_LOG_SEPARATE_ALL})
        payload = response.json()
        entries = _find_log_entries(payload)
        if entries is None:
            # Nur die Form der Antwort (Typen, Längen, Schlüsselnamen), nie
            # Meldungstexte. Hilft bei Firmware-Ständen (z. B. FRITZ!OS 8.25),
            # bei denen "mq_log" leer ist oder anders aufgebaut ist.
            _LOGGER.debug(
                "Ereignisse: query.lua-Antwort ohne erkennbare Eintragsliste"
                " (Form der Antwort: %s)",
                _describe_shape(payload),
            )
            return None
        return [
            FritzEvent.from_query_fields(entry) for entry in entries if isinstance(entry, dict)
        ]

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

        # v1.1.0 (Issue #1): Der Pfad wird zuerst über HTTPS am von der Box
        # gemeldeten Sicherheits-Port (GetSecurityPort, meist 49443) geholt,
        # erst danach über das bisherige HTTP. Auf manchen Boxen/Firmwares
        # (z. B. 6690 Cable, FRITZ!OS 8.25) liefert HTTP/Port 80 für
        # /devicelog.lua nur eine HTML-Fehlerseite.
        last_error: Exception | None = None
        for origin in self._log_origins(fc):
            try:
                # Issue #1 (Nachtrag): ``urljoin`` liegt innerhalb des ``try``.
                # Eine ungültige Basis-URL (z. B. "Invalid IPv6 URL") darf nur
                # diesen einen Ursprung überspringen, nicht den ganzen XML-Weg.
                url = urljoin(origin, path)
                events = _parse_log_xml(_download_log_xml(fc.session, url))
            except Exception as ex:  # noqa: BLE001 - nächster Ursprung / Rückfall
                last_error = ex
                _LOGGER.debug(
                    "Ereignisse: devicelog.lua über %s fehlgeschlagen (%s: %s)",
                    origin.split("://", 1)[0],
                    type(ex).__name__,
                    ex,
                )
                continue
            if events is not None:
                return events
            _LOGGER.debug(
                "Ereignisse: devicelog-XML über %s enthielt keine <Event>-Einträge",
                origin.split("://", 1)[0],
            )
        if last_error is not None:
            raise last_error
        return None

    def _log_origins(self, fc: Any) -> list[str]:
        """Basis-URLs für den devicelog-Abruf.

        Reihenfolge: HTTPS am Sicherheits-Port, HTTP am Web-UI-Port (80/443
        laut ``FritzHttp``), HTTP am TR-064-Port. Der Host wird zuvor von
        Schema, Pfad und Port befreit; nur echte IPv6-Adressen bekommen eckige
        Klammern (Issue #1, Nachtrag).
        """
        origins: list[str] = []
        host = _normalize_host(getattr(fc, "address", ""))
        if host:
            origins.append(f"https://{host}:{self._get_security_port(fc)}")
        try:
            origins.append(FritzHttp(fc).router_url)
        except Exception as ex:  # noqa: BLE001 - dieser Ursprung entfällt nur
            _LOGGER.debug(
                "Ereignisse: Web-UI-Adresse nicht ermittelbar (%s: %s)", type(ex).__name__, ex
            )
        port = getattr(fc, "port", None)
        if host and isinstance(port, int) and 0 < port < 65536:
            origins.append(f"http://{host}:{port}")
        # Doppelte Ursprünge (z. B. identische Adressen) nur einmal versuchen.
        return list(dict.fromkeys(origins))

    def _get_security_port(self, fc: Any) -> int:
        """Sicherheits-Port (HTTPS) der Box per TR-064; Standard 49443 als Rückfall."""
        if self._security_port is not None:
            return self._security_port
        port = DEFAULT_SECURITY_PORT
        try:
            result = fc.call_action(SERVICE_DEVICE_INFO, ACTION_GET_SECURITY_PORT)
            candidate = int(result.get("NewSecurityPort"))
            if 0 < candidate < 65536:
                port = candidate
        except Exception as ex:  # noqa: BLE001 - Standardport genügt als Rückfall
            _LOGGER.debug(
                "Ereignisse: GetSecurityPort fehlgeschlagen (%s: %s) - verwende %s",
                type(ex).__name__,
                ex,
                DEFAULT_SECURITY_PORT,
            )
        self._security_port = port
        return port

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
                # Älteste zuerst (events ist neueste-zuerst sortiert), damit
                # Automationen und das Notification Center die Einträge in
                # zeitlicher Reihenfolge erhalten.
                for event in reversed(events):
                    if event.id not in new_ids:
                        continue
                    self.hass.bus.async_fire(
                        EVENT_NEW_EREIGNIS,
                        {
                            "entry_id": self.config_entry.entry_id,
                            **event.to_dict(),
                        },
                    )
                    self._nc_report_event(event)
        self._known_ids = current_ids

    # --- Notification Center (seit v1.1.0) --------------------------------

    def _nc_subject(self) -> dict[str, str]:
        """Objekt, auf das sich die Meldungen beziehen (keine Seriennummer)."""
        return {
            "id": self.config_entry.entry_id,
            "name": self._device.modelname or "FRITZ!Box",
            "kind": "network",
        }

    def _nc_count(self, type_: str) -> None:
        self.nc_sent[type_] = self.nc_sent.get(type_, 0) + 1

    def _nc_report_event(self, event: FritzEvent) -> None:
        """Neuen Protokolleintrag als Einzelereignis ans Notification Center melden."""
        nc = self.nc
        if nc is None:
            return
        type_ = NC_TYPE_FOR_GROUP.get(event.group, NC_TYPE_DEFAULT_FOR_GROUP)
        if not nc.type_enabled(type_):
            return
        nc.report(
            type_,
            event.id,
            "active",
            subject=self._nc_subject(),
            placeholders={"message": event.message[:NC_MESSAGE_MAX_LEN]},
            data={
                "group": event.group,
                "date": event.timestamp.isoformat() if event.timestamp else None,
            },
        )
        self._nc_count(type_)

    def _nc_set_connection_lost(self, lost: bool) -> None:
        """Verbindungsverlust melden (nur bei Zustandswechsel, keine Wiederholung)."""
        if lost == self._nc_connection_lost:
            return
        self._nc_connection_lost = lost
        nc = self.nc
        if nc is None or not nc.type_enabled(NC_TYPE_CONNECTION_LOST):
            return
        subject = self._nc_subject()
        nc.report(
            NC_TYPE_CONNECTION_LOST,
            self.config_entry.entry_id,
            "active" if lost else "resolved",
            subject=subject,
            placeholders={"name": subject["name"]},
        )
        if lost:
            self._nc_count(NC_TYPE_CONNECTION_LOST)

    def nc_active_state(self) -> dict[str, list[dict[str, Any]]]:
        """Aktive, auflösbare Zustände für Ausgangszustand und Sync (siehe Brücke)."""
        if not self._nc_connection_lost:
            return {NC_TYPE_CONNECTION_LOST: []}
        subject = self._nc_subject()
        return {
            NC_TYPE_CONNECTION_LOST: [
                {
                    "key": self.config_entry.entry_id,
                    "subject": subject,
                    "placeholders": {"name": subject["name"]},
                }
            ]
        }


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


def _find_log_entries(payload: object, _depth: int = 0) -> list[dict] | None:
    """Recursively locate the list of log entries in a query.lua response.

    Weg 0 (v0.3.0) ist ein undokumentierter Endpunkt - die genaue
    Verschachtelungstiefe der JSON-Antwort (z. B. ``{"mq_log": {"data":
    {"log_separate": {"list": [...]}}}}`` oder etwas flacheres) ist ohne
    echte Hardware nicht verifizierbar. Statt einen einzigen, geratenen
    Pfad hart zu verdrahten, wird die Antwort defensiv nach der ERSTEN
    Liste durchsucht, deren Elemente wie Log-Einträge aussehen (Dicts mit
    mindestens ``time``+``msg``, case-insensitiv) - funktioniert
    unabhängig davon, wie tief AVM diese Liste tatsächlich verschachtelt,
    und liefert ``None`` (nicht ``[]``), wenn nichts Passendes gefunden
    wurde, damit der Aufrufer das von einem "0 Ereignisse" unterscheiden
    kann. Tiefenbegrenzt (``_depth``), um bei unerwartet rekursiven/
    zyklischen Strukturen nicht endlos zu suchen.
    """
    if _depth > 6:
        return None
    if isinstance(payload, list):
        candidates = [item for item in payload if isinstance(item, dict)]
        if candidates and all(
            any(key.lower() in ("time", "date") for key in item) for item in candidates
        ) and all(any(key.lower() in ("msg", "message") for key in item) for item in candidates):
            return payload
        for item in payload:
            found = _find_log_entries(item, _depth + 1)
            if found is not None:
                return found
        return None
    if isinstance(payload, dict):
        for value in payload.values():
            found = _find_log_entries(value, _depth + 1)
            if found is not None:
                return found
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


def _local_name(tag: object) -> str:
    """Tag-Name ohne XML-Namespace (``{ns}Event`` -> ``Event``)."""
    text = tag if isinstance(tag, str) else ""
    return text.rsplit("}", 1)[-1]


def _iter_event_elements(root: Element):
    """Yield every event element, regardless of nesting depth and spelling.

    v1.1.0 (Issue #1): FRITZ!OS 8.25 liefert ``<Event>`` (großes E), ältere
    Stände ``<event>`` - der Vergleich ist daher unabhängig von der Groß-/
    Kleinschreibung (und ignoriert einen evtl. vorhandenen Namespace).
    """
    for element in root.iter():
        if _local_name(element.tag).lower() == "event":
            yield element


def _download_log_xml(session: Any, url: str) -> bytes:
    """Lädt die devicelog-XML (BLOCKING). Löst bei HTML-Antworten einen Fehler aus.

    ``verify=False``: Die FRITZ!Box nutzt am Sicherheits-Port ein selbst
    signiertes Zertifikat. Die Verbindung geht ausschließlich zur
    konfigurierten FRITZ!Box im lokalen Netz; die sid steckt bereits in der
    URL. Die Zertifikatswarnung wird nur für diesen einen Aufruf
    unterdrückt.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", InsecureRequestWarning)
        response = session.get(url, verify=False, timeout=LOG_XML_TIMEOUT)
    response.raise_for_status()
    content: bytes = response.content
    head = content[:300].lstrip().lower()
    if head.startswith((b"<!doctype html", b"<html")):
        raise ValueError("HTML-Seite statt devicelog-XML erhalten")
    return content


def _parse_log_xml(content: bytes) -> list[FritzEvent] | None:
    """Parst die devicelog-XML. ``None``, wenn kein einziger Eintrag gefunden wurde.

    Bei kaputtem XML gibt es genau einen Reparaturversuch (siehe Moduldoku,
    "Fix in v0.2.0"); schlägt auch der fehl, wird der ``ParseError`` an den
    Aufrufer durchgereicht.
    """
    try:
        root = fromstring(content)
    except ParseError as ex:
        _LOGGER.debug(
            "Ereignisse: devicelog-XML nicht wohlgeformt (%s) - versuche"
            " Reparatur (Steuerzeichen/bloße '&' escapen)",
            ex,
        )
        root = fromstring(_sanitize_xml_text(content.decode("utf-8", errors="replace")))
    elements = list(_iter_event_elements(root))
    if not elements:
        return None
    return [
        FritzEvent.from_xml_fields(
            {_local_name(child.tag).lower(): (child.text or "").strip() for child in element}
        )
        for element in elements
    ]


def _sorted_newest_first(events: list[FritzEvent]) -> list[FritzEvent]:
    """Sort by timestamp descending; entries without one keep their order at the end."""
    with_timestamp = [event for event in events if event.timestamp is not None]
    without_timestamp = [event for event in events if event.timestamp is None]
    with_timestamp.sort(key=lambda event: event.timestamp, reverse=True)
    return with_timestamp + without_timestamp


def _limit_for(config_entry: ConfigEntry) -> tuple[str, int]:
    """Return (limit_type, value) for the configured Verlaufstiefe (v1.0.0).

    Analog ``FritzCallLogCoordinator._limit_for()`` in fritzbox_anrufe -
    hier nur für den einen Ereignisse-Sensor dieser Integration, siehe
    Moduldoku ("Feature in v1.0.0").
    """
    options = config_entry.options
    limit_type = options.get(CONF_EVENT_LIMIT_TYPE, DEFAULT_EVENT_LIMIT_TYPE)
    if limit_type == EVENT_LIMIT_DAYS:
        return limit_type, options.get(CONF_MAX_EVENT_DAYS, DEFAULT_MAX_EVENT_DAYS)
    return limit_type, options.get(CONF_MAX_EVENTS, DEFAULT_MAX_EVENTS)


def _apply_event_limit(
    events: list[FritzEvent], limit_type: str, value: int
) -> list[FritzEvent]:
    """Truncate an already newest-first-sorted event list to the given limit.

    Reine, hardware-unabhängig testbare Funktion (siehe
    fritzbox_ereignisse_test/test_v100.py) - analog
    ``FritzCallLogCoordinator._apply_limit()`` in fritzbox_anrufe. Im
    Tage-Modus (:data:`EVENT_LIMIT_DAYS`) werden Einträge OHNE auswertbaren
    Zeitstempel (``timestamp is None`` - insbesondere möglich beim
    Text-Rückfall Weg 2, siehe :meth:`FritzEvent.from_text_line`) verworfen,
    da ihr Alter nicht beurteilt werden kann - identisches Prinzip wie dort
    (``isinstance(call.date, datetime)``).
    """
    if limit_type == EVENT_LIMIT_DAYS:
        cutoff = datetime.now() - timedelta(days=value)
        return [event for event in events if event.timestamp is not None and event.timestamp >= cutoff]
    return events[:value]
