# SHA256 (Inhalt ab Zeile 2, d.h. dieser Datei ohne diese erste Zeile): 0ada18c583a83e65bad330cc27d51a72c2bab700ebe90a9a5d0aee696d890b3e
"""Anonymisierter Diagnose-Download (Design-Master, Abschnitt 13)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from . import FritzBoxEreignisseConfigEntry
from .const import SERIAL_NUMBER, VERSION

# Zugangsdaten, Adresse und Seriennummer gehören nicht in einen Diagnose-Export.
TO_REDACT = {CONF_HOST, CONF_PASSWORD, CONF_USERNAME, SERIAL_NUMBER}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: FritzBoxEreignisseConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    Enthält keine Meldungstexte, Namen oder Adressen - nur Zähler, Schalterstände
    und Versionsangaben. Für das Notification Center: je Meldungsart der
    Schalterstand und die Anzahl gesendeter Meldungen seit dem Start.
    """
    runtime = entry.runtime_data
    coordinator = runtime.coordinator
    events = coordinator.data or []

    groups: dict[str, int] = {}
    for event in events:
        groups[event.group] = groups.get(event.group, 0) + 1

    snapshot = runtime.nc.snapshot()
    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": {
                key: value
                for key, value in entry.options.items()
                if key not in ("nc_enabled", "nc_types")
            },
        },
        "experimental_enabled": snapshot["experimental"],
        "version": VERSION,
        "update": runtime.update_checker.as_dict(),
        "events": {
            "count": len(events),
            "groups": groups,
            "source": coordinator.last_source,
            "last_update_success": coordinator.last_update_success,
        },
        "notification_center": {
            "available": snapshot["available"],
            "enabled": snapshot["enabled"],
            "types": {
                item["type"]: {
                    "enabled": item["enabled"],
                    "sent": coordinator.nc_sent.get(item["type"], 0),
                }
                for item in snapshot["types"]
            },
        },
    }
