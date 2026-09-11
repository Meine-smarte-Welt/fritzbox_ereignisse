"""Config flow for fritzbox_ereignisse."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
import logging
from typing import Any, override

from fritzconnection.core.exceptions import FritzConnectionException, FritzSecurityError
from requests.exceptions import ConnectionError as RequestsConnectionError
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .base import FritzBoxDevice
from .const import (
    CONF_EVENT_LIMIT_TYPE,
    CONF_MAX_EVENT_DAYS,
    CONF_MAX_EVENTS,
    DEFAULT_EVENT_LIMIT_TYPE,
    DEFAULT_HOST,
    DEFAULT_MAX_EVENT_DAYS,
    DEFAULT_MAX_EVENTS,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    DOMAIN,
    EVENT_COUNT_PRESETS,
    EVENT_LIMIT_COUNT,
    EVENT_LIMIT_DAYS,
    MAX_EVENT_DAYS,
    MIN_EVENT_DAYS,
    SERIAL_NUMBER,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA_USER = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
        vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ConnectResult(StrEnum):
    """FritzBoxDevice connection result."""

    INVALID_AUTH = "invalid_auth"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"
    NO_DEVICES_FOUND = "no_devices_found"
    UNKNOWN = "unknown"
    SUCCESS = "success"


def _event_limit_schema_dict(current_options: Mapping[str, Any]) -> dict[Any, Any]:
    """Shared (config- und options-flow) Schema für die Verlaufstiefe.

    Seit v1.0.0, analog ``_history_schema_dict()`` in fritzbox_anrufe: ein
    Modus-Auswahlfeld (Anzahl/Tage) plus je ein Feld für den jeweiligen
    Grenzwert - anders als dort aber nur EIN Satz Felder (kein Loop über
    mehrere Anruftypen), da diese Integration nur einen einzigen
    Ereignisse-Sensor kennt.
    """
    return {
        vol.Optional(
            CONF_EVENT_LIMIT_TYPE,
            default=current_options.get(CONF_EVENT_LIMIT_TYPE, DEFAULT_EVENT_LIMIT_TYPE),
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[EVENT_LIMIT_COUNT, EVENT_LIMIT_DAYS],
                translation_key="event_limit_type",
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Optional(
            CONF_MAX_EVENTS,
            default=str(current_options.get(CONF_MAX_EVENTS, DEFAULT_MAX_EVENTS)),
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[str(preset) for preset in EVENT_COUNT_PRESETS],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Optional(
            CONF_MAX_EVENT_DAYS,
            default=current_options.get(CONF_MAX_EVENT_DAYS, DEFAULT_MAX_EVENT_DAYS),
        ): vol.All(vol.Coerce(int), vol.Range(min=MIN_EVENT_DAYS, max=MAX_EVENT_DAYS)),
    }


def _parse_event_limit_input(user_input: Mapping[str, Any]) -> dict[str, Any]:
    """Extract/coerce the Verlaufstiefe-Felder aus dem Options-Formular."""
    return {
        CONF_EVENT_LIMIT_TYPE: user_input[CONF_EVENT_LIMIT_TYPE],
        CONF_MAX_EVENTS: int(user_input[CONF_MAX_EVENTS]),
        CONF_MAX_EVENT_DAYS: int(user_input[CONF_MAX_EVENT_DAYS]),
    }


class FritzBoxEreignisseConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a fritzbox_ereignisse config flow."""

    VERSION = 1

    _entry: ConfigEntry
    _host: str
    _port: int
    _username: str
    _password: str
    _device: FritzBoxDevice
    _serial_number: str

    def _try_connect(self) -> ConnectResult:
        """Try to connect and check auth. BLOCKING - run in executor."""
        self._device = FritzBoxDevice(
            host=self._host, port=self._port, username=self._username, password=self._password
        )
        try:
            self._device.connect()
        except FritzSecurityError:
            return ConnectResult.INSUFFICIENT_PERMISSIONS
        except FritzConnectionException:
            return ConnectResult.INVALID_AUTH
        except RequestsConnectionError:
            # e.g. host unreachable / connection refused (TR-064 port closed).
            return ConnectResult.NO_DEVICES_FOUND
        except Exception:  # noqa: BLE001 - deliberately broad: never let an
            # unexpected exception (timeout, HTTP error, malformed XML
            # response, ...) surface to the user as an unhelpful "Unknown
            # error occurred" without at least a traceback in the log - same
            # reasoning as fritzbox_anrufe's config_flow.py.
            _LOGGER.exception(
                "Unerwarteter Fehler beim Verbindungsaufbau zur FRITZ!Box unter %s",
                self._host,
            )
            return ConnectResult.UNKNOWN

        self._serial_number = self._device.serial_number or ""
        return ConnectResult.SUCCESS

    @staticmethod
    @callback
    @override
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> FritzBoxEreignisseOptionsFlowHandler:
        """Get the options flow for this handler."""
        return FritzBoxEreignisseOptionsFlowHandler()

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA_USER, errors={})

        self._host = user_input[CONF_HOST]
        self._port = user_input[CONF_PORT]
        self._username = user_input[CONF_USERNAME]
        self._password = user_input[CONF_PASSWORD]

        result = await self.hass.async_add_executor_job(self._try_connect)

        if result in (
            ConnectResult.INVALID_AUTH,
            ConnectResult.INSUFFICIENT_PERMISSIONS,
            ConnectResult.NO_DEVICES_FOUND,
            ConnectResult.UNKNOWN,
        ):
            # Recoverable: re-show the form instead of aborting the whole
            # flow, so the user can just correct the input and retry.
            return self.async_show_form(
                step_id="user", data_schema=DATA_SCHEMA_USER, errors={"base": result}
            )

        await self.async_set_unique_id(self._serial_number)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=self._device.modelname or "FRITZ!Box",
            data={
                CONF_HOST: self._host,
                CONF_PORT: self._port,
                CONF_USERNAME: self._username,
                CONF_PASSWORD: self._password,
                SERIAL_NUMBER: self._serial_number,
            },
            options={
                CONF_EVENT_LIMIT_TYPE: DEFAULT_EVENT_LIMIT_TYPE,
                CONF_MAX_EVENTS: DEFAULT_MAX_EVENTS,
                CONF_MAX_EVENT_DAYS: DEFAULT_MAX_EVENT_DAYS,
            },
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Handle flow upon an API authentication error."""
        self._entry = self._get_reauth_entry()
        self._host = entry_data[CONF_HOST]
        self._port = entry_data[CONF_PORT]
        self._username = entry_data[CONF_USERNAME]
        self._password = entry_data[CONF_PASSWORD]
        return await self.async_step_reauth_confirm()

    def _show_setup_form_reauth_confirm(
        self, user_input: dict[str, Any], errors: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Show the reauth form to the user."""
        default_username = user_input.get(CONF_USERNAME)
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=default_username): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            description_placeholders={"host": self._host},
            errors=errors or {},
        )

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            return self._show_setup_form_reauth_confirm(
                user_input={CONF_USERNAME: self._username}
            )

        self._username = user_input[CONF_USERNAME]
        self._password = user_input[CONF_PASSWORD]

        if (
            error := await self.hass.async_add_executor_job(self._try_connect)
        ) is not ConnectResult.SUCCESS:
            return self._show_setup_form_reauth_confirm(
                user_input=user_input, errors={"base": error}
            )

        self.hass.config_entries.async_update_entry(
            self._entry,
            data={
                CONF_HOST: self._host,
                CONF_PORT: self._port,
                CONF_USERNAME: self._username,
                CONF_PASSWORD: self._password,
                SERIAL_NUMBER: self._serial_number,
            },
        )
        await self.hass.config_entries.async_reload(self._entry.entry_id)
        return self.async_abort(reason="reauth_successful")


class FritzBoxEreignisseOptionsFlowHandler(OptionsFlowWithReload):
    """Handle a fritzbox_ereignisse options flow (Verlaufstiefe)."""

    @override
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the single options-flow step."""
        if user_input is not None:
            return self.async_create_entry(data=_parse_event_limit_input(user_input))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(_event_limit_schema_dict(self.config_entry.options)),
        )
