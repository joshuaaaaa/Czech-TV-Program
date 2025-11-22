"""Constants for the Czech TV Program integration."""

DOMAIN = "cz_tv_program"
PLATFORMS = ["sensor"]

# Data source types
SOURCE_CT = "ct"  # Česká televize
SOURCE_XMLTV = "xmltv"  # XMLTV format

DEFAULT_SOURCE = SOURCE_CT

# Available channels - Česká televize
CT_CHANNELS = {
    "ct1": "ČT1",
    "ct2": "ČT2",
    "ct24": "ČT24",
    "ct4": "ČT sport",
    "ct5": "ČT :D",
    "ct6": "ČT art",
    "ct7": "ČT3",
}

# XMLTV channels - Prima, Nova and others
XMLTV_CHANNELS = {
    "prima": "Prima",
    "prima-cool": "Prima COOL",
    "prima-zoom": "Prima ZOOM",
    "prima-max": "Prima MAX",
    "prima-love": "Prima LOVE",
    "prima-krimi": "Prima KRIMI",
    "prima-star": "Prima STAR",
    "prima-show": "Prima SHOW",
    "cnn-prima": "CNN Prima NEWS",
    "nova": "TV Nova",
    "nova-cinema": "Nova Cinema",
    "nova-action": "Nova Action",
    "nova-gold": "Nova Gold",
    "nova-sport1": "Nova Sport 1",
    "nova-sport2": "Nova Sport 2",
}

# Backward compatibility
AVAILABLE_CHANNELS = CT_CHANNELS

# API Configuration - Česká televize
CT_API_BASE_URL = "https://www.ceskatelevize.cz/services-old/programme/xml/schedule.php"
API_BASE_URL = CT_API_BASE_URL  # Backward compatibility
API_TIMEOUT = 30

# XMLTV Configuration
DEFAULT_XMLTV_URL = "http://xmltv.tvpc.cz/xmltv.xml"
XMLTV_CACHE_TIME = 3600  # 1 hour

# Default values
DEFAULT_USERNAME = "test"
DEFAULT_DAYS_AHEAD = 7

# Sensor types
SENSOR_TYPE_CURRENT = "current"
SENSOR_TYPE_UPCOMING = "upcoming"
SENSOR_TYPE_DAILY = "daily"
SENSOR_TYPE_ALL = "all"  # Legacy compatibility

DEFAULT_SENSOR_TYPES = [SENSOR_TYPE_CURRENT, SENSOR_TYPE_UPCOMING, SENSOR_TYPE_DAILY]

# Storage
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_storage"
