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
from homeassistant.loader import async_get_integration

from .base import FritzBoxDevice
from .const import DOMAIN, PLATFORMS, SERIAL_NUMBER
from .events import FritzEventsCoordinator

_LOGGER = logging.getLogger(__name__)

# --- Bundled Lovelace card (fritzbox-ereignisse-card.js) --------------------
#
# Served directly from this integration's "www" folder and registered with
# the frontend through exactly ONE path: a persisted Lovelace resource entry
# (see _async_ensure_lovelace_resource) - identical mechanism to
# fritzbox_anrufe's __init__.py (see its module comment for the history of
# why a second, document-embedded load path was deliberately removed).
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

    await _async_ensure_lovelace_resource(hass)
    hass.data[_FRONTEND_REGISTERED_KEY] = True


async def _async_ensure_lovelace_resource(hass: HomeAssistant) -> None:
    """Register (or update) the card as the persisted Lovelace resource entry.

    Same cache-busting/idempotency approach as fritzbox_anrufe's
    __init__.py - see there for the detailed rationale. Never raises; a
    failure here must not break the rest of the integration.

    ``LOVELACE_DATA`` is imported lazily (rather than at module level, as
    fritzbox_anrufe does) and tolerantly - unlike that already-shipped,
    hardware-confirmed sibling integration, this is v0.1.0 and hasn't run
    against every Home-Assistant version yet. Should this constant ever
    move/rename, the whole integration must still load - only the
    automatic Lovelace-resource registration degrades to "add it manually".
    """
    try:
        from homeassistant.components.lovelace.const import LOVELACE_DATA  # noqa: PLC0415
    except ImportError as ex:
        _LOGGER.debug(
            "homeassistant.components.lovelace.const.LOVELACE_DATA nicht"
            " gefunden (%s) - automatischer Ressourcen-Eintrag für %s"
            " übersprungen. Bitte bei Bedarf manuell unter Einstellungen ->"
            " Dashboards -> Ressourcen eintragen.",
            ex,
            _CARD_STATIC_URL,
        )
        return

    lovelace_data = hass.data.get(LOVELACE_DATA)
    if lovelace_data is None:
        _LOGGER.debug(
            "Lovelace-Daten nicht gefunden - automatischer Ressourcen-"
            "Eintrag für %s übersprungen. Bitte bei Bedarf manuell unter"
            " Einstellungen -> Dashboards -> Ressourcen eintragen.",
            _CARD_STATIC_URL,
        )
        return

    resources = lovelace_data.resources
    if not hasattr(resources, "async_create_item"):
        # YAML-mode dashboards (ResourceYAMLCollection) manage resources
        # exclusively via configuration.yaml - nothing to create here.
        _LOGGER.debug(
            "Lovelace läuft im YAML-Modus - bitte %s bei Bedarf manuell als"
            " Ressource (Typ 'module') eintragen, siehe README.",
            _CARD_STATIC_URL,
        )
        return

    try:
        if not getattr(resources, "loaded", True):
            await resources.async_load()

        integration = await async_get_integration(hass, DOMAIN)
        target_url = f"{_CARD_STATIC_URL}?v={integration.version}"

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
            _LOGGER.debug("Lovelace-Ressource für %s automatisch angelegt.", target_url)
        elif existing.get("url") != target_url:
            await resources.async_update_item(
                existing["id"], {"res_type": "module", "url": target_url}
            )
            _LOGGER.debug(
                "Lovelace-Ressource für %s auf %s aktualisiert.", _CARD_STATIC_URL, target_url
            )
        else:
            _LOGGER.debug("Lovelace-Ressource für %s bereits aktuell.", target_url)
    except Exception as ex:  # noqa: BLE001 - best-effort, must not break setup
        _LOGGER.warning(
            "Konnte %s nicht automatisch als Lovelace-Ressource eintragen"
            " (%s) - bitte bei Bedarf manuell unter Einstellungen ->"
            " Dashboards -> Ressourcen hinzufügen (Typ 'module').",
            _CARD_STATIC_URL,
            ex,
        )


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
    await coordinator.async_config_entry_first_refresh()

    config_entry.runtime_data = FritzBoxEreignisseRuntimeData(
        device=device, coordinator=coordinator
    )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: FritzBoxEreignisseConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
