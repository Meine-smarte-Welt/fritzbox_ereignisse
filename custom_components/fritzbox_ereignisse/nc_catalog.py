# SHA256 (Inhalt ab Zeile 2, d.h. dieser Datei ohne diese erste Zeile): d01ee031e8f1557b962b7b46e42b72dba04116e65a230ad2289accaa80e3e183
"""Katalog der Meldungsarten für das Notification Center (Schema 1).

Nur Arten, die diese Integration tatsächlich erzeugen kann:

* ``connection_lost`` - der Abruf des Ereignisprotokolls schlägt fehl
  (auflösbar: sobald der Abruf wieder klappt).
* ``event_<kategorie>`` - ein neuer Eintrag im Ereignisprotokoll der
  FRITZ!Box, je Kategorie (System/Internetverbindung/Telefonie/WLAN/USB).
  Einzelereignisse (nicht auflösbar).

Die Dringlichkeit der Protokolleinträge ist bewusst ``info``: Aus dem
Meldungstext allein lässt sich nicht zuverlässig ableiten, ob ein Eintrag
(z. B. "Internetverbindung getrennt" oder "... wiederhergestellt") ein
Problem oder eine Entwarnung ist. Telefonie und WLAN sind standardmäßig
AUS, weil dort je nach Haushalt sehr viele Einträge entstehen.
"""

from __future__ import annotations

from typing import Any, Final

from .const import (
    NC_TYPE_CONNECTION_LOST,
    NC_TYPE_EVENT_INTERNET,
    NC_TYPE_EVENT_SYS,
    NC_TYPE_EVENT_TEL,
    NC_TYPE_EVENT_USB,
    NC_TYPE_EVENT_WLAN,
)

NC_ICON: Final = "mdi:router-network"

NC_CATALOG: Final[list[dict[str, Any]]] = [
    {
        "type": NC_TYPE_CONNECTION_LOST,
        "severity": "warning",
        "resolvable": True,
        "enabled_default": True,
        "icon": "mdi:lan-disconnect",
        "texts": {
            "de": {
                "label": "Verbindung zur FRITZ!Box verloren",
                "title": "Verbindung zur FRITZ!Box verloren",
                "message": "Das Ereignisprotokoll von {name} kann nicht abgerufen werden.",
            },
            "en": {
                "label": "Connection to FRITZ!Box lost",
                "title": "Connection to FRITZ!Box lost",
                "message": "The event log of {name} cannot be retrieved.",
            },
            "nl": {
                "label": "Verbinding met FRITZ!Box verbroken",
                "title": "Verbinding met FRITZ!Box verbroken",
                "message": "Het gebeurtenislogboek van {name} kan niet worden opgehaald.",
            },
            "fr": {
                "label": "Connexion à la FRITZ!Box perdue",
                "title": "Connexion à la FRITZ!Box perdue",
                "message": "Le journal des événements de {name} est inaccessible.",
            },
            "es": {
                "label": "Conexión con la FRITZ!Box perdida",
                "title": "Conexión con la FRITZ!Box perdida",
                "message": "No se puede obtener el registro de eventos de {name}.",
            },
        },
    },
    {
        "type": NC_TYPE_EVENT_SYS,
        "severity": "info",
        "resolvable": False,
        "enabled_default": True,
        "icon": "mdi:cog-outline",
        "texts": {
            "de": {
                "label": "Ereignisse: System",
                "title": "FRITZ!Box · System",
                "message": "{message}",
            },
            "en": {
                "label": "Events: System",
                "title": "FRITZ!Box · System",
                "message": "{message}",
            },
            "nl": {
                "label": "Gebeurtenissen: Systeem",
                "title": "FRITZ!Box · Systeem",
                "message": "{message}",
            },
            "fr": {
                "label": "Événements : Système",
                "title": "FRITZ!Box · Système",
                "message": "{message}",
            },
            "es": {
                "label": "Eventos: Sistema",
                "title": "FRITZ!Box · Sistema",
                "message": "{message}",
            },
        },
    },
    {
        "type": NC_TYPE_EVENT_INTERNET,
        "severity": "info",
        "resolvable": False,
        "enabled_default": True,
        "icon": "mdi:web",
        "texts": {
            "de": {
                "label": "Ereignisse: Internetverbindung",
                "title": "FRITZ!Box · Internetverbindung",
                "message": "{message}",
            },
            "en": {
                "label": "Events: Internet connection",
                "title": "FRITZ!Box · Internet connection",
                "message": "{message}",
            },
            "nl": {
                "label": "Gebeurtenissen: Internetverbinding",
                "title": "FRITZ!Box · Internetverbinding",
                "message": "{message}",
            },
            "fr": {
                "label": "Événements : Connexion Internet",
                "title": "FRITZ!Box · Connexion Internet",
                "message": "{message}",
            },
            "es": {
                "label": "Eventos: Conexión a Internet",
                "title": "FRITZ!Box · Conexión a Internet",
                "message": "{message}",
            },
        },
    },
    {
        "type": NC_TYPE_EVENT_USB,
        "severity": "info",
        "resolvable": False,
        "enabled_default": True,
        "icon": "mdi:usb",
        "texts": {
            "de": {
                "label": "Ereignisse: USB-Geräte",
                "title": "FRITZ!Box · USB-Geräte",
                "message": "{message}",
            },
            "en": {
                "label": "Events: USB devices",
                "title": "FRITZ!Box · USB devices",
                "message": "{message}",
            },
            "nl": {
                "label": "Gebeurtenissen: USB-apparaten",
                "title": "FRITZ!Box · USB-apparaten",
                "message": "{message}",
            },
            "fr": {
                "label": "Événements : Appareils USB",
                "title": "FRITZ!Box · Appareils USB",
                "message": "{message}",
            },
            "es": {
                "label": "Eventos: Dispositivos USB",
                "title": "FRITZ!Box · Dispositivos USB",
                "message": "{message}",
            },
        },
    },
    {
        "type": NC_TYPE_EVENT_TEL,
        "severity": "info",
        "resolvable": False,
        "enabled_default": False,
        "icon": "mdi:phone-outline",
        "texts": {
            "de": {
                "label": "Ereignisse: Telefonie",
                "title": "FRITZ!Box · Telefonie",
                "message": "{message}",
            },
            "en": {
                "label": "Events: Telephony",
                "title": "FRITZ!Box · Telephony",
                "message": "{message}",
            },
            "nl": {
                "label": "Gebeurtenissen: Telefonie",
                "title": "FRITZ!Box · Telefonie",
                "message": "{message}",
            },
            "fr": {
                "label": "Événements : Téléphonie",
                "title": "FRITZ!Box · Téléphonie",
                "message": "{message}",
            },
            "es": {
                "label": "Eventos: Telefonía",
                "title": "FRITZ!Box · Telefonía",
                "message": "{message}",
            },
        },
    },
    {
        "type": NC_TYPE_EVENT_WLAN,
        "severity": "info",
        "resolvable": False,
        "enabled_default": False,
        "icon": "mdi:wifi",
        "texts": {
            "de": {
                "label": "Ereignisse: WLAN",
                "title": "FRITZ!Box · WLAN",
                "message": "{message}",
            },
            "en": {
                "label": "Events: Wi-Fi",
                "title": "FRITZ!Box · Wi-Fi",
                "message": "{message}",
            },
            "nl": {
                "label": "Gebeurtenissen: WLAN",
                "title": "FRITZ!Box · WLAN",
                "message": "{message}",
            },
            "fr": {
                "label": "Événements : Wi-Fi",
                "title": "FRITZ!Box · Wi-Fi",
                "message": "{message}",
            },
            "es": {
                "label": "Eventos: Wi-Fi",
                "title": "FRITZ!Box · Wi-Fi",
                "message": "{message}",
            },
        },
    },
]
