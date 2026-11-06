"""Base entity for Rosières Local."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .runtime import RosieresRuntimeData


class RosieresEntity(CoordinatorEntity):
    """Base entity linked to the dishwasher device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        runtime: RosieresRuntimeData,
        entry: ConfigEntry,
        entity_key: str,
    ) -> None:
        super().__init__(runtime.coordinator)
        self.runtime = runtime
        self.entry = entry

        device_identifier = entry.unique_id or entry.data[CONF_HOST]

        self._attr_unique_id = f"{device_identifier}_{entity_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_identifier)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def status(self) -> dict[str, Any]:
        """Return the raw statusDWash object."""

        data = self.coordinator.data or {}
        status = data.get("statusDWash", {})
        return status if isinstance(status, dict) else {}
