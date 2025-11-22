"""Sensor platform for Czech TV Program."""

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CT_CHANNELS,
    DOMAIN,
    SENSOR_TYPE_CURRENT,
    SENSOR_TYPE_DAILY,
    SENSOR_TYPE_UPCOMING,
    SOURCE_CT,
    XMLTV_CHANNELS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    source = config_entry.data.get("source", SOURCE_CT)
    channels = config_entry.options.get(f"{DOMAIN}_OPTIONS") or config_entry.data.get(
        "channels", []
    )

    # Get channel names based on source
    if source == SOURCE_CT:
        channel_names = CT_CHANNELS
    else:
        channel_names = XMLTV_CHANNELS

    entities = []
    for channel_id in channels:
        # Create three sensors per channel: current, upcoming, daily
        entities.extend(
            [
                CzTVProgramCurrentSensor(coordinator, channel_id, channel_names),
                CzTVProgramUpcomingSensor(coordinator, channel_id, channel_names),
                CzTVProgramDailySensor(coordinator, channel_id, channel_names),
            ]
        )

    async_add_entities(entities)


class BaseTVProgramSensor(CoordinatorEntity, SensorEntity):
    """Base class for TV Program sensors."""

    def __init__(self, coordinator, channel_id: str, channel_names: dict):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._channel_id = channel_id
        self._channel_name = channel_names.get(channel_id, channel_id)
        self._attr_icon = "mdi:television-classic"
        self._cached_current_program = None
        self._cached_next_programs = []
        self._last_update = None

    def _get_channel_data(self) -> list[dict[str, Any]]:
        """Get channel data from coordinator."""
        if not self.coordinator.data:
            return []
        return self.coordinator.data.get(self._channel_id, [])

    def _update_program_cache(self) -> None:
        """Update cached current and next programs."""
        now = datetime.now()
        if self._last_update and (now - self._last_update).seconds < 60:
            return

        self._last_update = now
        channel_data = self._get_channel_data()

        if not channel_data:
            self._cached_current_program = None
            self._cached_next_programs = []
            return

        current_program = None
        next_programs = []

        for program in channel_data:
            program_datetime = self._parse_program_datetime(program)
            if not program_datetime:
                continue

            if program_datetime <= now:
                current_program = program
            elif len(next_programs) < 20:
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


class CzTVProgramCurrentSensor(BaseTVProgramSensor):
    """Sensor for current TV program."""

    def __init__(self, coordinator, channel_id: str, channel_names: dict):
        """Initialize the current program sensor."""
        super().__init__(coordinator, channel_id, channel_names)
        self._attr_name = f"{self._channel_name} - Aktuální program"
        self._attr_unique_id = f"{DOMAIN}_{channel_id}_current"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        self._update_program_cache()

        if self._cached_current_program:
            return self._cached_current_program.get("title", "Neznámý pořad")

        return "Nedostupné"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        self._update_program_cache()

        attributes = {
            "channel": self._channel_name,
            "channel_id": self._channel_id,
        }

        if self._cached_current_program:
            attributes.update(
                {
                    "title": self._cached_current_program.get("title", ""),
                    "supertitle": self._cached_current_program.get("supertitle", ""),
                    "episode_title": self._cached_current_program.get(
                        "episode_title", ""
                    ),
                    "time": self._cached_current_program.get("time", ""),
                    "date": self._cached_current_program.get("date", ""),
                    "genre": self._cached_current_program.get("genre", ""),
                    "duration": self._cached_current_program.get("duration", ""),
                    "description": self._cached_current_program.get("description", ""),
                    "episode": self._cached_current_program.get("episode", ""),
                    "link": self._cached_current_program.get("link", ""),
                    "live": self._cached_current_program.get("live", False),
                    "premiere": self._cached_current_program.get("premiere", False),
                }
            )

        return attributes


class CzTVProgramUpcomingSensor(BaseTVProgramSensor):
    """Sensor for upcoming TV programs."""

    def __init__(self, coordinator, channel_id: str, channel_names: dict):
        """Initialize the upcoming programs sensor."""
        super().__init__(coordinator, channel_id, channel_names)
        self._attr_name = f"{self._channel_name} - Nadcházející"
        self._attr_unique_id = f"{DOMAIN}_{channel_id}_upcoming"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        self._update_program_cache()

        if self._cached_next_programs:
            return f"{len(self._cached_next_programs)} programů"

        return "Nedostupné"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        self._update_program_cache()

        attributes = {
            "channel": self._channel_name,
            "channel_id": self._channel_id,
            "programs": [
                {
                    "title": p.get("title", ""),
                    "supertitle": p.get("supertitle", ""),
                    "episode_title": p.get("episode_title", ""),
                    "time": p.get("time", ""),
                    "date": p.get("date", ""),
                    "genre": p.get("genre", ""),
                    "duration": p.get("duration", ""),
                    "description": p.get("description", ""),
                    "live": p.get("live", False),
                    "premiere": p.get("premiere", False),
                }
                for p in self._cached_next_programs[:10]
            ],
        }

        return attributes


class CzTVProgramDailySensor(BaseTVProgramSensor):
    """Sensor for daily TV program schedule."""

    def __init__(self, coordinator, channel_id: str, channel_names: dict):
        """Initialize the daily schedule sensor."""
        super().__init__(coordinator, channel_id, channel_names)
        self._attr_name = f"{self._channel_name} - Denní program"
        self._attr_unique_id = f"{DOMAIN}_{channel_id}_daily"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        channel_data = self._get_channel_data()
        today = datetime.now().date()

        today_programs = [
            p
            for p in channel_data
            if self._parse_program_datetime(p)
            and self._parse_program_datetime(p).date() == today
        ]

        return f"{len(today_programs)} programů dnes"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        channel_data = self._get_channel_data()
        today = datetime.now().date()
        tomorrow = (datetime.now() + timedelta(days=1)).date()

        attributes = {
            "channel": self._channel_name,
            "channel_id": self._channel_id,
        }

        # Today's programs
        attributes["today"] = [
            {
                "title": p.get("title", ""),
                "supertitle": p.get("supertitle", ""),
                "episode_title": p.get("episode_title", ""),
                "time": p.get("time", ""),
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
            and self._parse_program_datetime(p).date() == today
        ]

        # Tomorrow's programs
        attributes["tomorrow"] = [
            {
                "title": p.get("title", ""),
                "supertitle": p.get("supertitle", ""),
                "episode_title": p.get("episode_title", ""),
                "time": p.get("time", ""),
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
            and self._parse_program_datetime(p).date() == tomorrow
        ]

        return attributes
