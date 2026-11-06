"""Sensors for Rosières Local."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from .const import (
    DISHWASHER_STATES,
    DOMAIN,
    KNOWN_STATUS_FIELDS,
    PROGRAM_BY_CODE,
    PROGRAMS,
    WATER_HARDNESS_FIELD,
    WATER_HARDNESS_LEVELS,
)
from .entity import RosieresEntity


def _as_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Rosières local sensors."""

    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            RosieresStateSensor(runtime, entry),
            RosieresProgramSensor(runtime, entry),
            RosieresRemainingTimeSensor(runtime, entry),
            RosieresDelayStartSensor(runtime, entry),
            RosieresErrorSensor(runtime, entry),
            RosieresRawSettingsSensor(runtime, entry),
            RosieresWaterHardnessSensor(runtime, entry),
        ]
    )


class RosieresStateSensor(RosieresEntity, SensorEntity):
    """Current dishwasher phase."""

    _attr_name = "État"
    _attr_icon = "mdi:dishwasher"

    def __init__(self, runtime, entry):
        super().__init__(runtime, entry, "state")

    @property
    def native_value(self):
        error = str(self.status.get("CodiceErrore", "E0"))
        if error not in ("0", "E0"):
            return "Erreur"

        if str(self.status.get("StartStop", "0")) == "1":
            return "En cours"

        code = _as_int(self.status.get("StatoDWash"), -1)
        return DISHWASHER_STATES.get(code, f"État {code}")

    @property
    def extra_state_attributes(self):
        return {
            "code_etat": _as_int(self.status.get("StatoDWash"), -1),
            "start_stop": self.status.get("StartStop"),
            "check_up": self.status.get("CheckUp"),
        }


class RosieresProgramSensor(RosieresEntity, SensorEntity):
    """Current dishwasher program."""

    _attr_name = "Programme actuel"
    _attr_icon = "mdi:dishwasher"

    def __init__(self, runtime, entry):
        super().__init__(runtime, entry, "current_program")

    @property
    def native_value(self):
        code = self.status.get("Program")
        return PROGRAM_BY_CODE.get(code, code or "Inconnu")

    @property
    def extra_state_attributes(self):
        code = self.status.get("Program")
        name = PROGRAM_BY_CODE.get(code)
        details = PROGRAMS.get(name, {})
        return {
            "code_api": code,
            "temperature_c": details.get("temperature"),
            "duree_theorique_min": details.get("duration"),
        }


class RosieresRemainingTimeSensor(RosieresEntity, SensorEntity):
    """Remaining program time."""

    _attr_name = "Temps restant"
    _attr_icon = "mdi:progress-clock"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, runtime, entry):
        super().__init__(runtime, entry, "remaining_time")

    @property
    def native_value(self):
        if str(self.status.get("StartStop", "0")) != "1":
            return 0
        return _as_int(self.status.get("RemTime"), 0)


class RosieresDelayStartSensor(RosieresEntity, SensorEntity):
    """Delayed start value."""

    _attr_name = "Départ différé"
    _attr_icon = "mdi:clock-start"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.HOURS

    def __init__(self, runtime, entry):
        super().__init__(runtime, entry, "delay_start")

    @property
    def native_value(self):
        return _as_int(self.status.get("DelayStart"), 0)


class RosieresErrorSensor(RosieresEntity, SensorEntity):
    """Dishwasher error code."""

    _attr_name = "Erreur"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, runtime, entry):
        super().__init__(runtime, entry, "error")

    @property
    def native_value(self):
        return self.status.get("CodiceErrore", "Inconnu")

    @property
    def icon(self):
        return (
            "mdi:check-circle-outline"
            if self.native_value in ("0", "E0")
            else "mdi:alert-circle-outline"
        )


def _field_sort_key(name: str):
    """Sort r1, r2, ..., r15 numerically, other names afterwards."""

    if name[:1] == "r" and name[1:].isdigit():
        return (0, int(name[1:]), name)
    return (1, 0, name)


class RosieresRawSettingsSensor(RosieresEntity, SensorEntity):
    """Raw fields of statusDWash that are not mapped yet (r1, r2, ...).

    Their meaning is not documented. The state is a compact summary so that
    any change made from the official app shows up in the history.
    """

    _attr_name = "Réglages bruts"
    _attr_icon = "mdi:code-braces"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, runtime, entry):
        super().__init__(runtime, entry, "raw_settings")

    def _unmapped(self) -> dict:
        fields = {
            key: value
            for key, value in self.status.items()
            if key not in KNOWN_STATUS_FIELDS
        }
        return {key: fields[key] for key in sorted(fields, key=_field_sort_key)}

    @property
    def native_value(self):
        summary = " ".join(f"{key}={value}" for key, value in self._unmapped().items())
        return summary[:255] if summary else None

    @property
    def extra_state_attributes(self):
        return self._unmapped()


class RosieresWaterHardnessSensor(RosieresEntity, SensorEntity):
    """Water softener level, read only.

    It can only be changed on the control panel: program selection and
    on/off held together for 5 s, then program selection to pick the level.
    """

    _attr_name = "Dureté de l'eau"
    _attr_icon = "mdi:water-opacity"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [level["label"] for level in WATER_HARDNESS_LEVELS.values()]

    def __init__(self, runtime, entry):
        super().__init__(runtime, entry, "water_hardness")

    def _level(self):
        return _as_int(self.status.get(WATER_HARDNESS_FIELD), -1)

    @property
    def native_value(self):
        level = WATER_HARDNESS_LEVELS.get(self._level())
        return level["label"] if level else None

    @property
    def extra_state_attributes(self):
        code = self._level()
        level = WATER_HARDNESS_LEVELS.get(code, {})
        return {
            "niveau": f"S{code}" if level else None,
            "plage_fh": level.get("fh"),
            "plage_dh": level.get("dh"),
            "sel_necessaire": level.get("salt"),
            "reglage": "au bandeau uniquement",
        }
