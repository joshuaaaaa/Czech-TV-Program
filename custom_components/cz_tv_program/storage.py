"""Storage manager for Czech TV Program integration."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

from .const import STORAGE_KEY, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)


class TVProgramStorage:
    """Manage TV program data storage in JSON files."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the storage manager."""
        self.hass = hass
        self.storage_dir = Path(hass.config.path("tv_program_data"))
        self.storage_dir.mkdir(exist_ok=True)

    def _get_channel_file(self, channel_id: str) -> Path:
        """Get the file path for a channel."""
        return self.storage_dir / f"{channel_id}.json"

    async def async_save_channel_data(
        self, channel_id: str, data: list[dict[str, Any]]
    ) -> None:
        """Save channel data to JSON file."""
        try:
            file_path = self._get_channel_file(channel_id)

            storage_data = {
                "version": STORAGE_VERSION,
                "channel_id": channel_id,
                "last_update": datetime.now().isoformat(),
                "programs": data,
            }

            def _write_file():
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(storage_data, f, ensure_ascii=False, indent=2)

            await self.hass.async_add_executor_job(_write_file)
            _LOGGER.debug("Saved %d programs for %s", len(data), channel_id)

        except Exception as err:
            _LOGGER.error("Error saving data for %s: %s", channel_id, err)

    async def async_load_channel_data(self, channel_id: str) -> list[dict[str, Any]]:
        """Load channel data from JSON file."""
        try:
            file_path = self._get_channel_file(channel_id)

            if not file_path.exists():
                return []

            def _read_file():
                with open(file_path, encoding="utf-8") as f:
                    return json.load(f)

            storage_data = await self.hass.async_add_executor_job(_read_file)

            # Validate version
            if storage_data.get("version") != STORAGE_VERSION:
                _LOGGER.warning(
                    "Storage version mismatch for %s, ignoring cache", channel_id
                )
                return []

            programs = storage_data.get("programs", [])
            _LOGGER.debug("Loaded %d programs for %s", len(programs), channel_id)
            return programs

        except Exception as err:
            _LOGGER.error("Error loading data for %s: %s", channel_id, err)
            return []

    async def async_get_last_update(self, channel_id: str) -> datetime | None:
        """Get the last update time for a channel."""
        try:
            file_path = self._get_channel_file(channel_id)

            if not file_path.exists():
                return None

            def _read_file():
                with open(file_path, encoding="utf-8") as f:
                    return json.load(f)

            storage_data = await self.hass.async_add_executor_job(_read_file)
            last_update_str = storage_data.get("last_update")

            if last_update_str:
                return datetime.fromisoformat(last_update_str)

        except Exception as err:
            _LOGGER.debug("Error getting last update for %s: %s", channel_id, err)

        return None

    async def async_clear_channel_data(self, channel_id: str) -> None:
        """Clear cached data for a channel."""
        try:
            file_path = self._get_channel_file(channel_id)

            if file_path.exists():
                await self.hass.async_add_executor_job(os.remove, file_path)
                _LOGGER.debug("Cleared cache for %s", channel_id)

        except Exception as err:
            _LOGGER.error("Error clearing cache for %s: %s", channel_id, err)

    async def async_clear_all(self) -> None:
        """Clear all cached data."""
        try:
            def _clear_all():
                for file_path in self.storage_dir.glob("*.json"):
                    file_path.unlink()

            await self.hass.async_add_executor_job(_clear_all)
            _LOGGER.info("Cleared all cached TV program data")

        except Exception as err:
            _LOGGER.error("Error clearing all cache: %s", err)

    async def async_get_cache_size(self) -> int:
        """Get total size of cached data in bytes."""
        try:
            def _get_size():
                total_size = 0
                for file_path in self.storage_dir.glob("*.json"):
                    total_size += file_path.stat().st_size
                return total_size

            return await self.hass.async_add_executor_job(_get_size)

        except Exception as err:
            _LOGGER.error("Error getting cache size: %s", err)
            return 0
