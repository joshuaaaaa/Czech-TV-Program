"""API client for Slovak TV Program with multiple XMLTV sources."""
import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from defusedxml import ElementTree as ET
from xml.etree.ElementTree import Element

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import XMLTV_API_URL, LEMONCZE_API_URL, API_TIMEOUT, AVAILABLE_CHANNELS, DEFAULT_DAYS_AHEAD

_LOGGER = logging.getLogger(__name__)

class SkTVProgramAPI:
    """API client for Slovak TV Program."""

    def __init__(self, hass: HomeAssistant, channels: List[str]):
        """Initialize the API client."""
        self.hass = hass
        self.channels = channels or list(AVAILABLE_CHANNELS.keys())
        self.session = async_get_clientsession(hass)

    async def async_update_data(self) -> Dict[str, Any]:
        """Fetch data from all XMLTV feeds and return structured program info."""
        all_data: Dict[str, List[Dict[str, Any]]] = {}
        try:
            # Fetch RTVS feed
            rtvs_root = await self._fetch_xmltv(XMLTV_API_URL)
            # Fetch LemonCZE feed (komerční kanály)
            lemon_root = await self._fetch_xmltv(LEMONCZE_API_URL)

            # Combine feeds
            xmltv_roots = [r for r in [rtvs_root, lemon_root] if r is not None]
            if not xmltv_roots:
                _LOGGER.warning("No XMLTV data available")
                return all_data

            for channel_id in self.channels:
                programs: List[Dict[str, Any]] = []
                for root in xmltv_roots:
                    programs += self._filter_channel_programs(root, channel_id)
                # Sort programs by date/time
                programs.sort(key=lambda x: (x.get("date"), x.get("time")))
                all_data[channel_id] = programs

                if programs:
                    _LOGGER.debug("Found %d programs for channel %s", len(programs), channel_id)
                else:
                    _LOGGER.warning("No programs found for channel %s", channel_id)

            _LOGGER.info("Fetched TV program for %d channels", len(all_data))
            return all_data

        except Exception as err:
            _LOGGER.error("Error fetching TV program: %s", err, exc_info=True)
            return all_data

    async def _fetch_xmltv(self, url: str) -> Optional[Element]:
        """Fetch XMLTV data from a given URL."""
        try:
            async with self.session.get(url, timeout=API_TIMEOUT) as response:
                if response.status == 200:
                    content = await response.text()
                    root = ET.fromstring(content)
                    _LOGGER.debug("Successfully fetched XMLTV from %s", url)
                    return root
                _LOGGER.warning("Failed to fetch XMLTV: HTTP %s (%s)", response.status, url)
                return None
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching XMLTV data from %s", url)
            return None
        except Exception as err:
            _LOGGER.error("Error fetching XMLTV from %s: %s", url, err)
            return None

    def _filter_channel_programs(self, xmltv_root: Element, channel_id: str) -> List[Dict[str, Any]]:
        """Filter and parse programs for a specific channel from XMLTV."""
        programs: List[Dict[str, Any]] = []
        if xmltv_root is None:
            return programs

        now = datetime.now()
        end_date = now + timedelta(days=DEFAULT_DAYS_AHEAD)

        # Channel ID mapping for XMLTV
        xmltv_channel_ids = {
            "rtvs1": ["jednotka.rtvs.sk", "rtvs1", "rtvs 1"],
            "rtvs2": ["dvojka.rtvs.sk", "rtvs2", "rtvs 2"],
            "rtvs24": ["24.rtvs.sk", "rtvs24", "rtvs :24"],
            "rtvs_sport": ["sport.rtvs.sk", "rtvs sport"],
            "markiza": ["markiza.sk", "tv markiza"],
            "doma": ["doma.sk", "tv doma"],
            "dajto": ["dajto.sk", "tv dajto"],
            "joj": ["joj.sk", "tv joj"],
            "joj_plus": ["jojplus.sk", "joj plus"],
            "wau": ["wau.sk"],
            "prima": ["prima.sk", "tv prima"],
            "ta3": ["ta3.sk"],
        }

        channel_ids = [cid.lower() for cid in xmltv_channel_ids.get(channel_id, [channel_id])]

        for programme in xmltv_root.findall("programme"):
            channel_attr = programme.attrib.get("channel", "").lower()
            
            # Check if this program belongs to our channel
            if not any(cid in channel_attr for cid in channel_ids):
                continue

            start_str = programme.attrib.get("start")
            stop_str = programme.attrib.get("stop")
            if not start_str or not stop_str:
                continue

            try:
                # Parse XMLTV datetime format (YYYYMMDDHHmmss +ZONE)
                start = datetime.strptime(start_str[:14], "%Y%m%d%H%M%S")
                stop = datetime.strptime(stop_str[:14], "%Y%m%d%H%M%S")
            except Exception as e:
                _LOGGER.debug("Error parsing datetime for %s: %s", start_str, e)
                continue

            # Filter by date range
            if start < now - timedelta(hours=2) or start > end_date:
                continue

            # Extract program details
            title_el = programme.find("title")
            desc_el = programme.find("desc")
            category_el = programme.find("category")
            
            title = title_el.text if title_el is not None and title_el.text else "Bez názvu"
            description = desc_el.text if desc_el is not None and desc_el.text else ""
            genre = category_el.text if category_el is not None and category_el.text else ""

            duration_minutes = int((stop - start).total_seconds() / 60)

            programs.append({
                "title": title,
                "supertitle": "",
                "episode_title": "",
                "description": description,
                "genre": genre,
                "duration": f"{duration_minutes} min",
                "date": start.strftime("%Y-%m-%d"),
                "time": start.strftime("%H:%M"),
                "stop_time": stop.strftime("%H:%M"),
                "start_datetime": start,
                "stop_datetime": stop,
                "episode": "",
                "link": "",
                "live": False,
                "premiere": False,
            })

        return programs
