"""Constants for the Czech TV Program integration."""

DOMAIN = "cz_tv_program"
PLATFORMS = ["sensor"]

# Available channels
AVAILABLE_CHANNELS = {
    "ct1": "ČT1",
    "ct2": "ČT2",
    "ct24": "ČT24",
    "ct4": "ČT sport",
    "ct5": "ČT :D",
    "ct6": "ČT art",
    "ct7": "ČT3",
}

# API Configuration
API_BASE_URL = "https://www.ceskatelevize.cz/services-old/programme/xml/schedule.php"
API_TIMEOUT = 30

# Default values
DEFAULT_USERNAME = "test"
DEFAULT_DAYS_AHEAD = 7
