"""Program selector for Rosières Local."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PROGRAMS
from .entity import RosieresEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up the local program selector."""

    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RosieresProgramSelect(runtime, entry)])


class RosieresProgramSelect(RosieresEntity, SelectEntity):
    """Select which program will be sent by the Start button."""

    _attr_name = "Programme à démarrer"
    _attr_icon = "mdi:dishwasher"
    _attr_options = list(PROGRAMS.keys())

    def __init__(self, runtime, entry):
        super().__init__(runtime, entry, "program_select")

    @property
    def current_option(self):
        return self.runtime.selected_program

    async def async_select_option(self, option: str) -> None:
        if option not in PROGRAMS:
            raise ValueError(f"Unsupported program: {option}")

        self.runtime.selected_program = option
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        details = PROGRAMS[self.runtime.selected_program]
        return {
            "code_api": details["code"],
            "temperature_c": details["temperature"],
            "duree_theorique_min": details["duration"],
        }
