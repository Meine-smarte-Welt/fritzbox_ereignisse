# SHA256 (Inhalt ab Zeile 2, d.h. dieser Datei ohne diese erste Zeile): 0f98befc7cb7e63478e522be222f03dd3981c9d8f497dbb6ec998e1d429d126b
"""The fritzbox_ereignisse integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path

from fritzconnection.core.exceptions import FritzConnectionException, FritzSecurityError
from requests.exceptions import ConnectionError as RequestsConnectionError

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er

from .base import FritzBoxDevice
from .const import DOMAIN, PLATFORMS, SERIAL_NUMBER, VERSION
from .events import FritzEventsCoordinator
from .nc_catalog import NC_CATALOG, NC_ICON
from .notification_bridge import NotificationBridge
from .update_check import UpdateChecker
from .websocket_api import async_register_websocket_api

_LOGGER = logging.getLogger(__name__)

# --- Bundled Lovelace card (fritzbox-ereignisse-card.js) --------------------
#
# Die Karte liegt im "www"-Ordner dieser Integration und wird über einen
# statischen Pfad ausgeliefert. Damit das Frontend sie lädt, gibt es seit
# v1.1.0 (Issue #2, "Custom element not found") ZWEI Wege, die sich
# ergänzen:
#
# 1. bevorzugt: ein persistierter Lovelace-Ressourceneintrag
#    (_async_ensure_lovelace_resource) - sichtbar unter Einstellungen ->
#    Dashboards -> Ressourcen;
# 2. Rückfall: ``frontend.add_extra_js_url`` - greift immer dann, wenn der
#    Ressourceneintrag nicht angelegt werden konnte (Lovelace-Daten nicht
#    gefunden, YAML-Modus, Fehler beim Speichern). Früher wurde dieser Fall
#    nur im Debug-Log vermerkt und die Karte blieb stillschweigend
#    ungeladen.
#
# Beide Wege gleichzeitig sind unkritisch: die Karte registriert ihre
# Elemente nur, wenn sie noch nicht definiert sind (siehe
# www/fritzbox-ereignisse-card.js).
_CARD_URL_BASE = "/fritzbox_ereignisse_files"
_CARD_FILENAME = "fritzbox-ereignisse-card.js"
_CARD_DIR = Path(__file__).parent / "www"
_CARD_STATIC_URL = f"{_CARD_URL_BASE}/{_CARD_FILENAME}"
_FRONTEND_REGISTERED_KEY = f"{DOMAIN}_frontend_registered"


async def _async_register_frontend_card(hass: HomeAssistant) -> None:
    """Serve and register the bundled fritzbox-ereignisse-card Lovelace card.

    Idempotent / runs at most once per Home Assistant instance, even if
    multiple FRITZ!Box accounts (config entries) are set up.
    """
    if hass.data.get(_FRONTEND_REGISTERED_KEY):
        return

    if not _CARD_DIR.joinpath(_CARD_FILENAME).is_file():
        _LOGGER.warning(
            "Die Dashboard-Karte fehlt im Integrationsordner (%s). Bitte die"
            " Integration über HACS erneut herunterladen.",
            _CARD_DIR / _CARD_FILENAME,
        )
        return

    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(_CARD_URL_BASE, str(_CARD_DIR), False)]
        )
    except RuntimeError:
        # Already registered (e.g. integration reloaded without a full HA
        # restart) - safe to ignore, the static path is still serving.
        _LOGGER.debug("Static path for %s already registered", _CARD_URL_BASE)
    except Exception as ex:  # noqa: BLE001 - must not silently wedge setup
        _LOGGER.warning(
            "Konnte den statischen Pfad für die Dashboard-Karte (%s) nicht"
            " registrieren (%s) - die Karte ist ggf. nicht erreichbar. Wird"
            " beim nächsten Setup erneut versucht.",
            _CARD_URL_BASE,
            ex,
        )
        return  # don't mark as registered - retry on the next config entry/restart

    target_url = f"{_CARD_STATIC_URL}?v={VERSION}"
    if not await _async_ensure_lovelace_resource(hass, target_url):
        _async_add_extra_js_fallback(hass, target_url)
    hass.data[_FRONTEND_REGISTERED_KEY] = True


def _async_add_extra_js_fallback(hass: HomeAssistant, target_url: str) -> None:
    """Load the card via ``frontend.add_extra_js_url`` (Rückfall, siehe oben)."""
    try:
        from homeassistant.components.frontend import add_extra_js_url  # noqa: PLC0415

        add_extra_js_url(hass, target_url)
    except Exception as ex:  # noqa: BLE001 - best-effort
        _LOGGER.warning(
            "Die Dashboard-Karte konnte weder als Lovelace-Ressource noch über das"
            " Frontend geladen werden (%s). Bitte unter Einstellungen -> Dashboards ->"
            " Ressourcen manuell %s als JavaScript-Modul hinzufügen.",
            ex,
            _CARD_STATIC_URL,
        )
        return
    _LOGGER.info(
        "Dashboard-Karte %s wird über das Frontend geladen (kein Lovelace-Ressourceneintrag"
        " möglich, z. B. YAML-Modus).",
        target_url,
    )


async def _async_ensure_lovelace_resource(hass: HomeAssistant, target_url: str) -> bool:
    """Register (or update) the card as the persisted Lovelace resource entry.

    Returns ``True`` if a matching resource entry exists afterwards (created,
    updated or already current), ``False`` if the caller has to fall back to
    :func:`_async_add_extra_js_fallback`. Never raises; a failure here must
    not break the rest of the integration. Seit v1.1.0 werden die Gründe
    für ein ``False`` als Warnung/Info protokolliert statt nur als Debug.
    """
    try:
        from homeassistant.components.lovelace.const import LOVELACE_DATA  # noqa: PLC0415
    except ImportError as ex:
        _LOGGER.warning(
            "Lovelace-Konstante nicht gefunden (%s) - die Karte wird über das Frontend"
            " geladen statt über einen Ressourceneintrag.",
            ex,
        )
        return False

    lovelace_data = hass.data.get(LOVELACE_DATA)
    if lovelace_data is None:
        _LOGGER.warning(
            "Lovelace-Daten nicht gefunden - die Karte wird über das Frontend geladen"
            " statt über einen Ressourceneintrag."
        )
        return False

    resources = lovelace_data.resources
    if not hasattr(resources, "async_create_item"):
        # YAML-mode dashboards (ResourceYAMLCollection) manage resources
        # exclusively via configuration.yaml - nothing to create here.
        _LOGGER.debug("Lovelace läuft im YAML-Modus - Ressourceneintrag nicht möglich.")
        return False

    try:
        if not getattr(resources, "loaded", True):
            await resources.async_load()

        existing = next(
            (
                item
                for item in resources.async_items()
                if item.get("url", "").split("?", 1)[0] == _CARD_STATIC_URL
            ),
            None,
        )

        if existing is None:
            await resources.async_create_item({"res_type": "module", "url": target_url})
            _LOGGER.info("Lovelace-Ressource für %s automatisch angelegt.", target_url)
        elif existing.get("url") != target_url:
            await resources.async_update_item(
                existing["id"], {"res_type": "module", "url": target_url}
            )
            _LOGGER.info(
                "Lovelace-Ressource für %s auf %s aktualisiert.", _CARD_STATIC_URL, target_url
            )
        else:
            _LOGGER.debug("Lovelace-Ressource für %s bereits aktuell.", target_url)
    except Exception as ex:  # noqa: BLE001 - best-effort, must not break setup
        _LOGGER.warning(
            "Konnte %s nicht als Lovelace-Ressource eintragen (%s) - die Karte wird über"
            " das Frontend geladen.",
            _CARD_STATIC_URL,
            ex,
        )
        return False
    return True


def _async_reserve_entity_id(hass: HomeAssistant, config_entry: ConfigEntry, unique_id: str) -> None:
    """Reserve a fixed, language-neutral entity_id for the Ereignisse sensor.

    Home Assistant derives an entity_id from its (translated, therefore
    language-dependent) display name and offers no supported hook on the
    entity itself to override that - same situation and same fix as
    fritzbox_anrufe's ``_async_reserve_entity_ids``: pre-create the registry
    entry with an explicit ``suggested_object_id`` before the platform sets
    up its entity, so ``sensor.fritzbox_ereignisse_ereignisse`` stays stable
    across languages instead of e.g. ``sensor.fritz_box_7590_ereignisse``.
    """
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{unique_id}-ereignisse",
        suggested_object_id=f"{DOMAIN}_ereignisse",
        config_entry=config_entry,
    )


@dataclass
class FritzBoxEreignisseRuntimeData:
    """Runtime data shared between this integration's platforms."""

    device: FritzBoxDevice
    coordinator: FritzEventsCoordinator
    nc: NotificationBridge
    update_checker: UpdateChecker


type FritzBoxEreignisseConfigEntry = ConfigEntry[FritzBoxEreignisseRuntimeData]


async def async_setup_entry(hass: HomeAssistant, config_entry: FritzBoxEreignisseConfigEntry) -> bool:
    """Set up the fritzbox_ereignisse platforms."""
    await _async_register_frontend_card(hass)

    device = FritzBoxDevice(
        host=config_entry.data[CONF_HOST],
        port=config_entry.data[CONF_PORT],
        username=config_entry.data[CONF_USERNAME],
        password=config_entry.data[CONF_PASSWORD],
    )

    try:
        await hass.async_add_executor_job(device.connect)
    except FritzSecurityError as ex:
        _LOGGER.error(
            "Dem FRITZ!Box-Konto fehlt die Berechtigung 'FRITZ!Box-Einstellungen'"
            " für den TR-064-Zugriff: %s",
            ex,
        )
        return False
    except FritzConnectionException as ex:
        raise ConfigEntryAuthFailed from ex
    except RequestsConnectionError as ex:
        _LOGGER.error("Unable to connect to FRITZ!Box: %s", ex)
        raise ConfigEntryNotReady from ex

    _async_reserve_entity_id(hass, config_entry, config_entry.data[SERIAL_NUMBER])

    coordinator = FritzEventsCoordinator(hass, config_entry, device)

    # Notification Center (optional, Schnittstelle Schema 1): ohne installiertes
    # Notification Center passiert nichts - die Events verhallen ohne Fehler.
    nc = NotificationBridge(
        hass,
        config_entry,
        source=DOMAIN,
        name="FRITZ!Box Ereignisse",
        version=VERSION,
        icon=NC_ICON,
        catalog=NC_CATALOG,
    )
    nc.set_state_provider(coordinator.nc_active_state)
    coordinator.nc = nc

    await coordinator.async_config_entry_first_refresh()

    update_checker = UpdateChecker(hass, VERSION, on_change=coordinator.async_update_listeners)

    config_entry.runtime_data = FritzBoxEreignisseRuntimeData(
        device=device, coordinator=coordinator, nc=nc, update_checker=update_checker
    )

    async_register_websocket_api(hass)
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # Erst nach dem ersten erfolgreichen Abruf: Katalog anmelden, Ausgangszustand
    # melden (ohne Push), Update-Prüfung starten.
    nc.async_start()
    update_checker.async_start(config_entry)
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: FritzBoxEreignisseConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
