"""Binary sensors for Rosières Local."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import RosieresEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Rosières local binary sensors."""

    runtime = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            RosieresBinarySensor(
                runtime,
                entry,
                "door",
                "Porte",
                "OpenDoor",
                "mdi:door",
                BinarySensorDeviceClass.DOOR,
            ),
            RosieresBinarySensor(
                runtime,
                entry,
                "remote_control",
                "Connexion Wi-Fi",
                "StatoWiFi",
                "mdi:remote",
                BinarySensorDeviceClass.CONNECTIVITY,
            ),
            RosieresBinarySensor(
                runtime,
                entry,
                "salt_empty",
                "Sel manquant",
                "MissSalt",
                "mdi:shaker-outline",
                BinarySensorDeviceClass.PROBLEM,
            ),
            RosieresBinarySensor(
                runtime,
                entry,
                "rinse_aid_empty",
                "Liquide de rinçage manquant",
                "MissRinse",
                "mdi:bottle-tonic-outline",
                BinarySensorDeviceClass.PROBLEM,
            ),
            RosieresBinarySensor(
                runtime,
                entry,
                "eco_mode",
                "Mode Eco",
                "Eco",
                "mdi:leaf",
                None,
            ),
            RosieresBinarySensor(
                runtime,
                entry,
                "open_door_option",
                "Option ouverture automatique",
                "OpenDoorOpt",
                "mdi:door-open",
                None,
            ),
            RosieresBinarySensor(
                runtime,
                entry,
                "extra_dry",
                "Extra Dry",
                "ExtraDry",
                "mdi:weather-sunny",
                None,
            ),
            RosieresBinarySensor(
                runtime,
                entry,
                "half_load",
                "Demi-charge",
                "MetaCarico",
                "mdi:dishwasher",
                None,
            ),
            RosieresBinarySensor(
                runtime,
                entry,
                "three_in_one",
                "Option 3-en-1",
                "TreinUno",
                "mdi:tablet",
                None,
            ),
        ]
    )


class RosieresBinarySensor(RosieresEntity, BinarySensorEntity):
    """Generic boolean field from statusDWash."""

    def __init__(
        self,
        runtime,
        entry,
        entity_key,
        name,
        source_field,
        icon,
        device_class,
    ):
        super().__init__(runtime, entry, entity_key)
        self._source_field = source_field
        self._attr_name = name
        self._attr_icon = icon
        self._attr_device_class = device_class

    @property
    def is_on(self):
        return str(self.status.get(self._source_field, "0")) not in (
            "0",
            "",
            "None",
            "NULL",
        )
