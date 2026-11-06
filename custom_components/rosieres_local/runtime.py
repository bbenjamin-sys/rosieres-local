"""Runtime data for Rosières Local."""

from dataclasses import dataclass

from .api import RosieresLocalApi
from .coordinator import RosieresDataUpdateCoordinator


@dataclass
class RosieresRuntimeData:
    """Per-config-entry runtime data."""

    api: RosieresLocalApi
    coordinator: RosieresDataUpdateCoordinator
    selected_program: str
    selected_extra_dry: bool = False
    selected_open_door: bool = False
    selected_half_load: bool = False
    selected_three_in_one: bool = False
    selected_eco: bool = False
    selected_delay_start: int = 0
