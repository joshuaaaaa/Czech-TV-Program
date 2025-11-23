DOMAIN = "previo_v4"

# Status mapping podle oficiální Previo API dokumentace
# Commission status ID (cosId)
STATUS_MAPPING = {
    "1": "Option",           # Možnost/Opce
    "2": "Confirmed",        # Potvrzeno
    "3": "Checked in",       # Ubytován
    "6": "Waiting list",     # Čekací listina
    "7": "Cancelled",        # Zrušeno
    "8": "No-show",          # Nedostavil se
    "9": "Checked out",      # Odhlášen
    "10": "Other",           # Jiné
}

# České překlady pro lepší čitelnost (volitelné)
STATUS_MAPPING_CZ = {
    "1": "Opce",
    "2": "Potvrzeno",
    "3": "Ubytován",
    "6": "Čekací listina",
    "7": "Zrušeno",
    "8": "Nedostavil se",
    "9": "Odhlášen",
    "10": "Jiné",
}

# Výchozí hodnoty
DEFAULT_UPDATE_INTERVAL = 15  # minut
DEFAULT_DAYS_AHEAD = 30       # dní