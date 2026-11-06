"""Constants for Rosières Local."""

DOMAIN = "rosieres_local"

CONF_ENCRYPTION_KEY = "encryption_key"

DEFAULT_NAME = "Lave-vaisselle Rosières"
MODEL = "RI 6E4L0FB-47"
MANUFACTURER = "Rosières"

POLL_INTERVAL_SECONDS = 15
MIN_REQUEST_INTERVAL_SECONDS = 3.0
REQUEST_TIMEOUT_SECONDS = 8

PROGRAMS = {
    "Intensif 75 °C": {
        "code": "P2",
        "w1": "1",
        "temperature": 75,
        "duration": 130,
    },
    "Universel 60 °C": {
        "code": "P5",
        "w1": "2",
        "temperature": 60,
        "duration": 120,
    },
    "Eco 45 °C": {
        "code": "P8",
        "w1": "3",
        "temperature": 45,
        "duration": 232,
    },
    "Prélavage": {
        "code": "P12",
        "w1": "4",
        "temperature": None,
        "duration": 5,
    },
    "Total Care 50 °C": {
        "code": "P13",
        "w1": "5",
        "temperature": 50,
        "duration": 100,
    },
}

PROGRAM_BY_CODE = {
    details["code"]: name for name, details in PROGRAMS.items()
}

DEFAULT_PROGRAM = "Eco 45 °C"

DISHWASHER_STATES = {
    1: "Inactif",
    2: "Prêt",
    3: "En cours",
}

# Water softener level, field r7 of statusDWash (S0 to S5).
# Confirmed on the RI 6E4L0FB-47: set to S2 on the control panel,
# r7 went from 4 to 2. The appliance ignores remote writes of this field.
WATER_HARDNESS_FIELD = "r7"
WATER_HARDNESS_LEVELS = {
    0: {"label": "Très douce", "fh": "0-5", "dh": "0-3", "salt": False},
    1: {"label": "Douce", "fh": "6-15", "dh": "4-9", "salt": True},
    2: {"label": "Moyennement dure", "fh": "16-30", "dh": "10-16", "salt": True},
    3: {"label": "Plutôt dure", "fh": "31-45", "dh": "17-25", "salt": True},
    4: {"label": "Dure", "fh": "46-60", "dh": "26-33", "salt": True},
    5: {"label": "Très dure", "fh": "61-90", "dh": "34-50", "salt": True},
}

# Fields of statusDWash already mapped to dedicated entities.
KNOWN_STATUS_FIELDS = {
    "StatoWiFi",
    "CodiceErrore",
    "StatoDWash",
    "MetaCarico",
    "StartStop",
    "TreinUno",
    "Eco",
    "Program",
    "ExtraDry",
    "OpenDoorOpt",
    "DelayStart",
    "RemTime",
    "MissSalt",
    "MissRinse",
    "OpenDoor",
    "Reset",
    "CheckUp",
}

PLATFORMS = ["sensor", "binary_sensor", "select", "button", "switch", "number"]
