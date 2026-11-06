"""Config flow for Rosières Local."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    RosieresApiError,
    RosieresInvalidResponse,
    RosieresLocalApi,
)
from .const import (
    CONF_ENCRYPTION_KEY,
    DEFAULT_NAME,
    DOMAIN,
)


class RosieresLocalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Rosières Local."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""

        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            encryption_key = user_input[CONF_ENCRYPTION_KEY].strip()
            name = user_input.get(CONF_NAME, DEFAULT_NAME).strip() or DEFAULT_NAME

            if len(encryption_key.encode("utf-8")) != 16:
                errors["base"] = "invalid_key"
            else:
                await self.async_set_unique_id(host.lower())
                self._abort_if_unique_id_configured()

                try:
                    api = RosieresLocalApi(
                        session=async_get_clientsession(self.hass),
                        host=host,
                        encryption_key=encryption_key,
                    )
                    data = await api.async_get_status()
                    if not isinstance(data.get("statusDWash"), dict):
                        raise RosieresInvalidResponse(
                            "statusDWash is missing"
                        )
                except RosieresInvalidResponse:
                    errors["base"] = "invalid_response"
                except RosieresApiError:
                    errors["base"] = "cannot_connect"
                except Exception:  # defensive: keep config flow usable
                    errors["base"] = "unknown"
                else:
                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_HOST: host,
                            CONF_ENCRYPTION_KEY: encryption_key,
                            CONF_NAME: name,
                        },
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_ENCRYPTION_KEY): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
