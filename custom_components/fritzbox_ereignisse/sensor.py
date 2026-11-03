# SHA256 (Inhalt ab Zeile 2, d.h. dieser Datei ohne diese erste Zeile): 9bffa274a3f3027256b09c2e2dc7479a7ea9969f0a8d69f1c16eb8fa9f742c26
"""Sensor platform for fritzbox_ereignisse."""

from __future__ import annotations

import logging
from typing import Any, override

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FritzBoxEreignisseConfigEntry, FritzBoxEreignisseRuntimeData
from .base import build_device_info
from .const import DOMAIN, SERIAL_NUMBER
from .events import FritzEvent, FritzEventsCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: FritzBoxEreignisseConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the fritzbox_ereignisse sensor."""
    runtime_data: FritzBoxEreignisseRuntimeData = config_entry.runtime_data
    serial_number: str = config_entry.data[SERIAL_NUMBER]
    device_info = build_device_info(runtime_data.device, serial_number)

    async_add_entities(
        [
            FritzBoxEreignisseSensor(
                coordinator=runtime_data.coordinator,
                runtime_data=runtime_data,
                unique_id=f"{serial_number}-ereignisse",
                device_info=device_info,
            )
        ]
    )


class FritzBoxEreignisseSensor(CoordinatorEntity[FritzEventsCoordinator], SensorEntity):
    """Sensor exposing the FRITZ!Box event log ("Ereignisse")."""

    _attr_has_entity_name = True
    _attr_translation_key = f"{DOMAIN}_ereignisse"
    _attr_native_unit_of_measurement = "Ereignisse"
    _attr_icon = "mdi:message-alert-outline"
    # Issue #2 (v1.1.0): Mit 90 Tagen Verlauf überschreitet "events" die
    # Obergrenze des Recorders (16384 Byte je Zustand) - der Recorder warnt
    # dann und speichert die Attribute gar nicht. Die Liste, die Update-Infos
    # und der Notification-Center-Stand sind reine Live-Daten für die Karte
    # und müssen nicht in die Datenbank. "groups" und "source" sind klein
    # und bleiben erhalten.
    _unrecorded_attributes = frozenset({"events", "app", "notification_center"})

    def __init__(
        self,
        coordinator: FritzEventsCoordinator,
        runtime_data: FritzBoxEreignisseRuntimeData,
        unique_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._runtime_data = runtime_data
        self._attr_unique_id = unique_id
        self._attr_device_info = device_info

    @property
    def _events(self) -> list[FritzEvent]:
        """Return the raw FritzEvent objects currently held."""
        return self.coordinator.data or []

    @property
    @override
    def native_value(self) -> int:
        """Return the number of events currently held."""
        return len(self._events)

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the events as a list of dicts, e.g. for a dashboard."""
        events = [event.to_dict() for event in self._events]
        groups = sorted({event.group for event in self._events})
        return {
            "events": events,
            "groups": groups,
            # Diagnose (siehe events.py-Moduldoku): "query" (seit v0.3.0) =
            # dieselbe interne Abfrage wie die Weboberfläche selbst
            # (query.lua), "xml" = vollständiges Protokoll via TR-064
            # (X_AVM-DE_GetDeviceLogPath), "text" = älterer TR-064-Rückfall
            # (GetDeviceLog). Seit v0.3.0 sind auch bei "text" dank
            # Text-Heuristik oft schon Kategorien vorhanden (siehe
            # events.py:_classify_message_group) - "text" heißt nicht mehr
            # zwangsläufig "keine Kategorien". None, solange noch kein
            # erfolgreicher Abruf stattgefunden hat.
            "source": self.coordinator.last_source,
            # Seit v1.1.0 (nicht aufgezeichnet, siehe oben): Versionsanzeige
            # mit Update-Hinweis und Stand des Notification Centers für die
            # Einstellungen in der Karte.
            "app": self._runtime_data.update_checker.as_dict(),
            # Experimentell (Regeln 07): ohne Hauptschalter nur das Flag, damit
            # die Karte nichts davon zeigt.
            "notification_center": self._notification_center_attribute(),
        }

    def _notification_center_attribute(self) -> dict[str, Any]:
        """Stand des Notification Centers, nur bei eingeschalteten Experimenten."""
        nc = self._runtime_data.nc
        if not nc.experimental_enabled:
            return {"experimental": False}
        return nc.snapshot()
