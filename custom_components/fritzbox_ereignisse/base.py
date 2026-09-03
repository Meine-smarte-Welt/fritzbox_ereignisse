"""Connection helper + shared device info for fritzbox_ereignisse."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from fritzconnection import FritzConnection

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, FRITZ_ATTR_SERIAL_NUMBER, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


@dataclass
class FritzBoxDevice:
    """Thin wrapper around an authenticated FritzConnection instance.

    Mirrors the connect-once-reuse-everywhere pattern already established
    by ``FritzBoxPhonebook`` in fritzbox_anrufe's ``base.py`` - one TR-064
    session, shared by the coordinator and (later) any additional
    platforms, rather than logging in again for every call.
    """

    host: str
    port: int
    username: str
    password: str
    fc: FritzConnection | None = None
    serial_number: str | None = None
    modelname: str | None = None
    system_version: str | None = None

    def connect(self) -> None:
        """Open the TR-064 connection and read the identifying device info.

        BLOCKING - must be called from an executor job. Raises whatever
        ``fritzconnection``/``requests`` exception occurs; callers are
        expected to translate that into the appropriate Home Assistant
        config-flow/setup error (see ``config_flow.py``/``__init__.py``),
        exactly like fritzbox_anrufe's ``_try_connect``/``async_setup_entry``.
        """
        self.fc = FritzConnection(
            address=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
        )
        # Same convenience property fritzbox_anrufe's config_flow.py already
        # uses to both verify credentials and read the serial number in one
        # call - avoids a second round-trip just to confirm the connection.
        info = self.fc.updatecheck
        self.serial_number = info[FRITZ_ATTR_SERIAL_NUMBER]
        self.modelname = self.fc.modelname
        self.system_version = self.fc.system_version


def build_device_info(device: FritzBoxDevice, unique_id: str) -> DeviceInfo:
    """Build the Home Assistant device entry for one FRITZ!Box account."""
    return DeviceInfo(
        configuration_url=device.fc.address if device.fc else None,
        identifiers={(DOMAIN, unique_id)},
        manufacturer=MANUFACTURER,
        model=device.modelname,
        name=device.modelname or "FRITZ!Box",
        sw_version=device.system_version,
    )
