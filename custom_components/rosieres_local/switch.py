"""Configurable start options for Rosières Local."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import RosieresEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up next-cycle option switches."""

    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            RosieresOptionSwitch(
                runtime,
                entry,
                "next_extra_dry",
                "Extra Dry prochain cycle",
                "selected_extra_dry",
                "mdi:weather-sunny",
            ),
            RosieresOptionSwitch(
                runtime,
                entry,
                "next_open_door",
                "Ouverture automatique prochain cycle",
                "selected_open_door",
                "mdi:door-open",
            ),
            RosieresOptionSwitch(
                runtime,
                entry,
                "next_half_load",
                "Demi-charge prochain cycle",
                "selected_half_load",
                "mdi:dishwasher",
            ),
            RosieresOptionSwitch(
                runtime,
                entry,
                "next_three_in_one",
                "3-en-1 prochain cycle",
                "selected_three_in_one",
                "mdi:tablet",
            ),
            RosieresOptionSwitch(
                runtime,
                entry,
                "next_eco",
                "Eco prochain cycle",
                "selected_eco",
                "mdi:leaf",
            ),
        ]
    )


class RosieresOptionSwitch(RosieresEntity, SwitchEntity):
    """An option stored locally and included in the next Start command."""

    def __init__(
        self,
        runtime,
        entry,
        entity_key: str,
        name: str,
        runtime_attr: str,
        icon: str,
    ) -> None:
        super().__init__(runtime, entry, entity_key)
        self._attr_name = name
        self._attr_icon = icon
        self._runtime_attr = runtime_attr

    @property
    def is_on(self) -> bool:
        return bool(getattr(self.runtime, self._runtime_attr))

    async def async_turn_on(self, **kwargs) -> None:
        setattr(self.runtime, self._runtime_attr, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        setattr(self.runtime, self._runtime_attr, False)
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        return {
            "applique_au": "prochain démarrage",
            "experimental": True,
        }
