"""API client for Czech TV Program."""

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .const import CT_CHANNELS, DEFAULT_DAYS_AHEAD, SOURCE_CT, SOURCE_XMLTV, XMLTV_CHANNELS
from .providers import CeskaTelevizeProvider, XMLTVProvider
from .storage import TVProgramStorage

_LOGGER = logging.getLogger(__name__)


class CzTVProgramAPI:
    """API client for Czech TV Program."""

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        channels: list[str],
        source: str = SOURCE_CT,
        xmltv_url: str | None = None,
    ):
        """Initialize the API client."""
        self.hass = hass
        self.username = username
        self.channels = channels
        self.source = source
        self.storage = TVProgramStorage(hass)

        # Initialize appropriate provider
        if source == SOURCE_XMLTV:
            self.provider = XMLTVProvider(hass, xmltv_url)
        else:
            self.provider = CeskaTelevizeProvider(hass, username)

    async def async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint with storage support."""
        tasks = []
        for channel_id in self.channels:
            tasks.append(self._fetch_channel_program_safe(channel_id))

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), timeout=120
            )
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout při načítání TV programů (>120s)")
            return {}

        all_data = {}
        for channel_id, result in zip(self.channels, results):
            if isinstance(result, Exception):
                _LOGGER.error("Chyba při načítání %s: %s", channel_id, result)
                # Try to load from storage
                cached_data = await self.storage.async_load_channel_data(channel_id)
                all_data[channel_id] = cached_data
            else:
                all_data[channel_id] = result
                # Save to storage
                await self.storage.async_save_channel_data(channel_id, result)

        return all_data

    async def _fetch_channel_program_safe(self, channel_id: str) -> list[dict[str, Any]]:
        """Fetch program for a specific channel with error handling."""
        try:
            return await self.provider.async_get_program(
                channel_id, DEFAULT_DAYS_AHEAD
            )
        except Exception as err:
            _LOGGER.error("Chyba při načítání programu pro %s: %s", channel_id, err)
            raise

    def get_available_channels(self) -> dict[str, str]:
        """Get available channels for current source."""
        return self.provider.get_available_channels()
