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

# Gruppen-/Kategorie-Kürzel, wie sie im XML-Protokoll (Weg 1 oben)
# beobachtet wurden - rein für hübschere Anzeigenamen in der Karte
# (siehe www/fritzbox-ereignisse-card.js). Ein unbekanntes/fehlendes
# Kürzel wird defensiv als "Allgemein" dargestellt, nie verworfen.
EVENT_GROUP_LABELS: Final[dict[str, str]] = {
    "sys": "System",
    "system": "System",
    "internet": "Internet",
    "dsl": "Internet",
    "wan": "Internet",
    "tel": "Telefonie",
    "fon": "Telefonie",
    "wlan": "WLAN",
    "usb": "USB / Speicher",
    "storage": "USB / Speicher",
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
