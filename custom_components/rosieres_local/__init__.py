"""Rosières Local integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RosieresLocalApi
from .const import (
    CONF_ENCRYPTION_KEY,
    DEFAULT_PROGRAM,
    DOMAIN,
    PROGRAM_BY_CODE,
)
from .coordinator import RosieresDataUpdateCoordinator
from .runtime import RosieresRuntimeData

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.SWITCH,
    Platform.NUMBER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Rosières Local from a config entry."""

    session = async_get_clientsession(hass)
    api = RosieresLocalApi(
        session=session,
        host=entry.data[CONF_HOST],
        encryption_key=entry.data[CONF_ENCRYPTION_KEY],
    )

    coordinator = RosieresDataUpdateCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    status = coordinator.data.get("statusDWash", {})
    selected_program = PROGRAM_BY_CODE.get(
        status.get("Program"),
        DEFAULT_PROGRAM,
    )

    def _flag(name: str) -> bool:
        return str(status.get(name, "0")) == "1"

    try:
        selected_delay_start = int(status.get("DelayStart", 0))
    except (TypeError, ValueError):
        selected_delay_start = 0

    runtime = RosieresRuntimeData(
        api=api,
        coordinator=coordinator,
        selected_program=selected_program,
        selected_extra_dry=_flag("ExtraDry"),
        selected_open_door=_flag("OpenDoorOpt"),
        selected_half_load=_flag("MetaCarico"),
        selected_three_in_one=_flag("TreinUno"),
        selected_delay_start=max(0, min(23, selected_delay_start)),
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN, None)

    return unloaded
