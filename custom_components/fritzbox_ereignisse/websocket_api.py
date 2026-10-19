# SHA256 (Inhalt ab Zeile 2, d.h. dieser Datei ohne diese erste Zeile): 4df5ae598c6d8200c07c4059c98706f175bcf6d283d63c8d0b5f4b2c46ae409b
"""WebSocket-API der Karte (seit v1.1.0): Schalter fürs Notification Center.

Nur ``fritzbox_ereignisse/action`` - schreibend, daher ausschließlich für
Administratoren. Gelesen wird über die Sensor-Attribute (``app`` und
``notification_center``), nicht über eine eigene Abfrage.

Hinweis (Design-Master, Abschnitt 14): In den Nachrichten kommt weder ein
Feld ``id`` noch ``timeout`` vor - beides kollidiert mit Feldern von
Home Assistant.
"""

from __future__ import annotations

from typing import Any, Final

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .nc_catalog import NC_CATALOG
from .notification_bridge import OPT_ENABLED, OPT_TYPES

WS_TYPE: Final = f"{DOMAIN}/action"
ACTION_NC_SET_MASTER: Final = "nc_set_master"
ACTION_NC_SET_TYPE: Final = "nc_set_type"
ACTION_CHECK_UPDATE: Final = "check_update"
ACTIONS: Final = (ACTION_NC_SET_MASTER, ACTION_NC_SET_TYPE, ACTION_CHECK_UPDATE)
NC_TYPES: Final = tuple(item["type"] for item in NC_CATALOG)

_REGISTERED_KEY: Final = f"{DOMAIN}_websocket_registered"


@callback
def async_register_websocket_api(hass: HomeAssistant) -> None:
    """WebSocket-Befehl einmal je Home-Assistant-Instanz registrieren."""
    if hass.data.get(_REGISTERED_KEY):
        return
    websocket_api.async_register_command(hass, ws_action)
    hass.data[_REGISTERED_KEY] = True


def _find_entry(hass: HomeAssistant, entry_id: str | None) -> Any | None:
    """Geladenen Config-Eintrag finden (ohne ``entry_id``: der erste)."""
    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    if entry_id:
        return next((entry for entry in entries if entry.entry_id == entry_id), None)
    return entries[0] if entries else None


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE,
        vol.Required("action"): vol.In(ACTIONS),
        vol.Optional("entry_id"): str,
        vol.Optional("enabled"): bool,
        vol.Optional("nc_type"): vol.In(NC_TYPES),
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_action(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Notification-Center-Schalter setzen oder die Update-Prüfung auslösen."""
    entry = _find_entry(hass, msg.get("entry_id"))
    if entry is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Eintrag nicht gefunden")
        return
    runtime = entry.runtime_data
    action = msg["action"]

    if action == ACTION_CHECK_UPDATE:
        await runtime.update_checker.async_check()
        connection.send_result(msg["id"], {"ok": True})
        return

    if "enabled" not in msg:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, "'enabled' fehlt")
        return

    options = dict(entry.options)
    if action == ACTION_NC_SET_MASTER:
        options[OPT_ENABLED] = msg["enabled"]
    else:  # ACTION_NC_SET_TYPE
        if "nc_type" not in msg:
            connection.send_error(
                msg["id"], websocket_api.ERR_INVALID_FORMAT, "'nc_type' fehlt"
            )
            return
        chosen = dict(options.get(OPT_TYPES, {}))
        chosen[msg["nc_type"]] = msg["enabled"]
        options[OPT_TYPES] = chosen

    hass.config_entries.async_update_entry(entry, options=options)
    # Kein Neuladen nötig: die Brücke liest die Optionen bei jedem Aufruf.
    runtime.nc.async_options_changed()
    runtime.coordinator.async_update_listeners()
    connection.send_result(msg["id"], {"ok": True})
