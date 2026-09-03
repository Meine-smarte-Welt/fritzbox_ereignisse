"""Constants for the FRITZ!Box Ereignisse integration."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "fritzbox_ereignisse"
MANUFACTURER: Final = "FRITZ!"

PLATFORMS: Final = [Platform.SENSOR]

FRITZ_ATTR_SERIAL_NUMBER = "Serial"
SERIAL_NUMBER = "serial_number"

# Gleicher link-lokale Standardwert wie fritzbox_anrufe (gilt für jede
# FRITZ!Box, unabhängig von Modell/Netzwerkkonfiguration).
DEFAULT_HOST = "169.254.1.1"
# Anders als fritzbox_anrufe (Port 1012, Callmonitor): diese Integration
# braucht KEINEN Callmonitor, ausschließlich TR-064 - daher der reguläre
# TR-064-Standardport.
DEFAULT_PORT = 49000
DEFAULT_USERNAME = "admin"

# --- Ereignisprotokoll (DeviceInfo:1) --------------------------------------
#
# Zwei dokumentierte TR-064-Wege zum FRITZ!Box-"Ereignisse"-Protokoll (siehe
# events.py für die vollständige Herleitung/Quellen):
#   1. X_AVM-DE_GetDeviceLogPath (FRITZ!OS 7.90+): liefert einen
#      Web-UI-Pfad zu einer XML-Datei mit STRUKTURIERTEN Einträgen
#      (id/group/date/time/msg) - das vollständige Protokoll, exakt wie es
#      FRITZ!Box-Oberfläche unter System > Ereignisse anzeigt.
#   2. GetDeviceLog (ältere FRITZ!OS-Stände, auch heute noch als Rückfall
#      vorhanden): liefert nur eine flache, neuzeilengetrennte Textliste
#      ohne Kategorie ("Gruppe") - laut mehreren Community-Berichten fehlen
#      hier sogar einzelne Eintragstypen (z. B. fehlgeschlagene
#      Anmeldeversuche).
#
# Beide Aktionen liegen im selben, bereits von fritzbox_anrufe genutzten
# TR-064-Basisdienst DeviceInfo - keine weitere Kontoberechtigung nötig als
# die für "FRITZ!Box-Einstellungen" (regulärer TR-064-Zugriff).
SERVICE_DEVICE_INFO = "DeviceInfo:1"
ACTION_GET_DEVICE_LOG_PATH = "X_AVM-DE_GetDeviceLogPath"
ACTION_GET_DEVICE_LOG = "GetDeviceLog"

# --- Web-UI-interner "query.lua"-Weg (Weg 0, seit v0.3.0, EXPERIMENTELL) ---
#
# Dieselbe interne Abfrage, die die FRITZ!Box-Weboberfläche selbst für
# "System > Ereignisse" verwendet, um die dortige Liste live zu befüllen
# (siehe events.py-Moduldoku, Abschnitt "Fix/Feature in v0.3.0", für
# Herleitung/Quelle: u. a. ip-phone-forum.de, Thread "Abfrage von query.lua
# und data.lua mit OS Version 07.27"). Kein TR-064-SOAP, sondern ein
# klassischer, sitzungsbasierter (sid) Web-UI-Aufruf - identisches
# Authentifizierungsprinzip wie fritzbox_anrufe's settings_data.py bzw. der
# Anrufbeantworter-Audio-Download in dessen tam.py. fritzconnection bringt
# dafür mit ``FritzHttp._get_sid()``/``FritzHttp.call_url()`` bereits einen
# fertigen, wiederverwendbaren Baustein für die Challenge-Response-Anmeldung
# mit - keine eigene Login-Implementierung nötig.
QUERY_LUA_PATH = "/query.lua"
MQ_LOG_SEPARATE_ALL = "logger:status/log_separate/list(time,msg,ref,type)"

# Gruppen-/Kategorie-Kürzel, wie sie im XML-Protokoll (Weg 1) beobachtet
# wurden, ERGÄNZT um die Kürzel, die die integrationseigene
# Text-Heuristik (siehe events.py:_classify_message_group) vergibt - rein
# für hübschere Anzeigenamen in der Karte (siehe
# www/fritzbox-ereignisse-card.js). Namen an die tatsächliche
# FRITZ!Box-Weboberfläche angeglichen (Reiter "Telefonie" /
# "Internetverbindung" / "USB-Geräte" / "WLAN" / "System"). Seit v0.4.0
# vergibt die Text-Heuristik selbst NUR NOCH "tel"/"wlan"/"usb"/
# "internet" gezielt sowie "sys" als universellen Auffang-Wert für alles
# Übrige (siehe events.py-Moduldoku, "Fix in v0.4.0") - "vpn"/"dect"/
# "network"/"smarthome" bleiben hier als Kürzel erhalten (falls ein
# künftiger Fetch-Weg sie einmal nativ liefert), werden von der Heuristik
# aber nicht mehr vergeben. Ein unbekanntes/fehlendes Kürzel wird
# defensiv als "Allgemein" dargestellt, nie verworfen.
EVENT_GROUP_LABELS: Final[dict[str, str]] = {
    "sys": "System",
    "system": "System",
    "internet": "Internetverbindung",
    "dsl": "Internetverbindung",
    "wan": "Internetverbindung",
    "tel": "Telefonie",
    "fon": "Telefonie",
    "wlan": "WLAN",
    "usb": "USB-Geräte",
    "storage": "USB-Geräte",
    "vpn": "VPN",
    "dect": "DECT",
    "network": "Heimnetz",
    "lan": "Heimnetz",
    "smarthome": "Smart Home",
}
EVENT_GROUP_UNKNOWN = "sonstiges"
EVENT_GROUP_LABEL_UNKNOWN = "Sonstiges"

# Verlaufstiefe (Options-Flow), analog CALL_LOG_COUNT_PRESETS in
# fritzbox_anrufe - begrenzt clientseitig, wie viele der von der FRITZ!Box
# gelieferten Ereignisse je Aktualisierung im Sensor gehalten werden.
CONF_MAX_EVENTS = "max_events"
DEFAULT_MAX_EVENTS = 100
EVENT_COUNT_PRESETS: Final[tuple[int, ...]] = (20, 50, 100, 200, 500)

# Event (Home-Assistant-Bus), gefeuert vom Coordinator, sobald ein
# gegenüber dem vorherigen Abruf neuer Ereignis-Eintrag entdeckt wird -
# direkt als Automations-Auslöser nutzbar. Bewusst NICHT beim allerersten
# Abruf nach einem (Neu-)Start gefeuert (identisches Prinzip wie
# EVENT_NEW_VOICEMAIL_MESSAGE in fritzbox_anrufe), sonst gäbe es bei jedem
# Home-Assistant-Neustart Events für längst bekannte, alte Einträge.
EVENT_NEW_EREIGNIS = f"{DOMAIN}_new_event"
