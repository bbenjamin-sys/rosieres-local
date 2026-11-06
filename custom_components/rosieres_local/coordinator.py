"""Data coordinator for Rosières Local."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RosieresApiError, RosieresLocalApi
from .const import POLL_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class RosieresDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate polling of the dishwasher local API."""

    def __init__(self, hass: HomeAssistant, api: RosieresLocalApi) -> None:
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name="Rosières Local",
            update_interval=timedelta(seconds=POLL_INTERVAL_SECONDS),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.async_get_status()
        except RosieresApiError as err:
            raise UpdateFailed(str(err)) from err
