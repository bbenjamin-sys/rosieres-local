"""Control buttons for Rosières Local."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .api import RosieresApiError
from .const import DOMAIN
from .entity import RosieresEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up dishwasher control buttons."""

    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            RosieresStartButton(runtime, entry),
            RosieresStopButton(runtime, entry),
        ]
    )


class RosieresStartButton(RosieresEntity, ButtonEntity):
    """Start the selected dishwasher program."""

    _attr_name = "Démarrer"
    _attr_icon = "mdi:play"

    def __init__(self, runtime, entry):
        super().__init__(runtime, entry, "start")

    async def async_press(self) -> None:
        status = self.status

        if str(status.get("OpenDoor", "0")) != "0":
            raise HomeAssistantError(
                "Démarrage refusé : la porte du lave-vaisselle est ouverte."
            )

        if str(status.get("StatoWiFi", "0")) != "1":
            raise HomeAssistantError(
                "Démarrage refusé : le contrôle à distance n'est pas disponible."
            )

        try:
            await self.runtime.api.async_start_program(
                self.runtime.selected_program,
                extra_dry=self.runtime.selected_extra_dry,
                open_door=self.runtime.selected_open_door,
                half_load=self.runtime.selected_half_load,
                three_in_one=self.runtime.selected_three_in_one,
                eco=self.runtime.selected_eco,
                delay_start=self.runtime.selected_delay_start,
            )
        except RosieresApiError as err:
            raise HomeAssistantError(
                f"Le lave-vaisselle a refusé le démarrage : {err}"
            ) from err

        await self.coordinator.async_request_refresh()


class RosieresStopButton(RosieresEntity, ButtonEntity):
    """Reset/stop the current dishwasher program."""

    _attr_name = "Arrêter"
    _attr_icon = "mdi:stop"

    def __init__(self, runtime, entry):
        super().__init__(runtime, entry, "stop")

    async def async_press(self) -> None:
        try:
            await self.runtime.api.async_stop()
        except RosieresApiError as err:
            raise HomeAssistantError(
                f"Le lave-vaisselle a refusé l'arrêt : {err}"
            ) from err

        await self.coordinator.async_request_refresh()
