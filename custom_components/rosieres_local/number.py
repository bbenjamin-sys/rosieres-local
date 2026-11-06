"""Delayed start configuration for Rosières Local."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import RosieresEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up delayed start configuration."""

    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RosieresDelayStartNumber(runtime, entry)])


class RosieresDelayStartNumber(RosieresEntity, NumberEntity):
    """Delay, in hours, included in the next Start command."""

    _attr_name = "Départ différé prochain cycle"
    _attr_icon = "mdi:clock-start"
    _attr_native_min_value = 0
    _attr_native_max_value = 23
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_mode = NumberMode.BOX

    def __init__(self, runtime, entry) -> None:
        super().__init__(runtime, entry, "next_delay_start")

    @property
    def native_value(self) -> float:
        return float(self.runtime.selected_delay_start)

    async def async_set_native_value(self, value: float) -> None:
        self.runtime.selected_delay_start = max(0, min(23, int(round(value))))
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        return {
            "applique_au": "prochain démarrage",
            "experimental": True,
        }
