"""Sensor platform for Czech TV Program."""

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import AVAILABLE_CHANNELS, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    channels = config_entry.options.get(f"{DOMAIN}_OPTIONS") or config_entry.data.get(
        "channels", []
    )

    entities = [CzTVProgramSensor(coordinator, channel_id) for channel_id in channels]

    async_add_entities(entities)


class CzTVProgramSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Czech TV Program sensor."""

    def __init__(self, coordinator, channel_id: str):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._channel_id = channel_id
        self._channel_name = AVAILABLE_CHANNELS.get(channel_id, channel_id)
        self._attr_name = f"TV Program {self._channel_name}"
        self._attr_unique_id = f"{DOMAIN}_{channel_id}"
        self._attr_icon = "mdi:television-classic"
        # OPRAVA: Cache pro aktuální program
        self._cached_current_program = None
        self._cached_next_programs = []
        self._last_update = None

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return "Nedostupné"

        channel_data = self.coordinator.data.get(self._channel_id, [])
        if not channel_data:
            return "Nedostupné"

        # Aktualizovat cache
        self._update_program_cache()

        if self._cached_current_program:
            return self._cached_current_program.get("title", "Neznámý pořad")

        return "Nedostupné"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        channel_data = self.coordinator.data.get(self._channel_id, [])
        if not channel_data:
            return {}

        # Aktualizovat cache pokud je potřeba
        self._update_program_cache()

        attributes = {
            "channel": self._channel_name,
            "channel_id": self._channel_id,
            "total_programs": len(channel_data),
        }

        # Current program details
        if self._cached_current_program:
            attributes.update(
                {
                    "current_title": self._cached_current_program.get("title", ""),
                    "current_supertitle": self._cached_current_program.get(
                        "supertitle", ""
                    ),
                    "current_episode_title": self._cached_current_program.get(
                        "episode_title", ""
                    ),
                    "current_time": self._cached_current_program.get("time", ""),
                    "current_date": self._cached_current_program.get("date", ""),
                    "current_genre": self._cached_current_program.get("genre", ""),
                    "current_duration": self._cached_current_program.get(
                        "duration", ""
                    ),
                    "current_description": self._cached_current_program.get(
                        "description", ""
                    ),
                    "current_episode": self._cached_current_program.get("episode", ""),
                    "current_link": self._cached_current_program.get("link", ""),
                    "current_live": self._cached_current_program.get("live", False),
                    "current_premiere": self._cached_current_program.get(
                        "premiere", False
                    ),
                }
            )

        # OPRAVA: Pouze nadcházejících 10 programů místo všech
        attributes["upcoming_programs"] = [
            {
                "title": p.get("title", ""),
                "time": p.get("time", ""),
                "date": p.get("date", ""),
                "genre": p.get("genre", ""),
                "duration": p.get("duration", ""),
                "description": p.get("description", ""),
                "live": p.get("live", False),
                "premiere": p.get("premiere", False),
            }
            for p in self._cached_next_programs[:10]
        ]

        # OPRAVA: all_programs pouze pro dnešek a zítra (ne celý týden)
        # Snížení velikosti dat z ~200 programů na ~50
        today = datetime.now().date()
        tomorrow = (datetime.now() + timedelta(days=1)).date()

        attributes["all_programs"] = [
            {
                "title": p.get("title", ""),
                "supertitle": p.get("supertitle", ""),
                "episode_title": p.get("episode_title", ""),
                "time": p.get("time", ""),
                "date": p.get("date", ""),
                "genre": p.get("genre", ""),
                "duration": p.get("duration", ""),
                "description": p.get("description", ""),
                "episode": p.get("episode", ""),
                "live": p.get("live", False),
                "premiere": p.get("premiere", False),
                "link": p.get("link", ""),
            }
            for p in channel_data
            if self._parse_program_datetime(p)
            and self._parse_program_datetime(p).date() in (today, tomorrow)
        ]

        return attributes

    def _update_program_cache(self) -> None:
        """Update cached current and next programs."""
        # OPRAVA: Cache se aktualizuje max 1x za minutu
        now = datetime.now()
        if self._last_update and (now - self._last_update).seconds < 60:
            return

        self._last_update = now
        channel_data = self.coordinator.data.get(self._channel_id, [])

        if not channel_data:
            self._cached_current_program = None
            self._cached_next_programs = []
            return

        # Find current program
        current_program = None
        next_programs = []

        for program in channel_data:
            program_datetime = self._parse_program_datetime(program)
            if not program_datetime:
                continue

            if program_datetime <= now:
                current_program = program
            elif len(next_programs) < 20:  # Cache 20 nadcházejících
                next_programs.append(program)
            else:
                break

        self._cached_current_program = current_program
        self._cached_next_programs = next_programs

    def _parse_program_datetime(self, program: dict) -> datetime | None:
        """Parse program date and time."""
        try:
            date_str = program.get("date", "")
            time_str = program.get("time", "")
            if date_str and time_str:
                datetime_str = f"{date_str} {time_str}"
                return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            pass
        return None
