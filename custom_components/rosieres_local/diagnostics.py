"""Diagnostics for Rosières Local."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import CONF_ENCRYPTION_KEY, DOMAIN

TO_REDACT = {CONF_ENCRYPTION_KEY, CONF_HOST}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return the raw dishwasher status, without the key or the address."""

    runtime = hass.data[DOMAIN][entry.entry_id]
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "last_update_success": runtime.coordinator.last_update_success,
        "status": runtime.coordinator.data,
    }
