"""Data providers for TV program sources."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any
from xml.etree.ElementTree import Element

from aiohttp.client import ClientError, ClientTimeout
from defusedxml import ElementTree as ET
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_TIMEOUT,
    CT_API_BASE_URL,
    CT_CHANNELS,
    DEFAULT_DAYS_AHEAD,
    DEFAULT_XMLTV_URL,
    XMLTV_CHANNELS,
)

_LOGGER = logging.getLogger(__name__)


class TVProgramProvider(ABC):
    """Abstract base class for TV program data providers."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the provider."""
        self.hass = hass
        self.session = async_get_clientsession(hass)

    @abstractmethod
    async def async_get_program(
        self, channel_id: str, days_ahead: int = DEFAULT_DAYS_AHEAD
    ) -> list[dict[str, Any]]:
        """Get program data for a channel.

        Args:
            channel_id: Channel identifier
            days_ahead: Number of days to fetch

        Returns:
            List of program dictionaries
        """

    @abstractmethod
    def get_available_channels(self) -> dict[str, str]:
        """Get available channels for this provider.

        Returns:
            Dictionary of channel_id: channel_name
        """


class CeskaTelevizeProvider(TVProgramProvider):
    """Provider for Česká televize API."""

    def __init__(self, hass: HomeAssistant, username: str = "test"):
        """Initialize the Česká televize provider."""
        super().__init__(hass)
        self.username = username

    def get_available_channels(self) -> dict[str, str]:
        """Get available ČT channels."""
        return CT_CHANNELS

    async def async_get_program(
        self, channel_id: str, days_ahead: int = DEFAULT_DAYS_AHEAD
    ) -> list[dict[str, Any]]:
        """Fetch program for a ČT channel."""
        tasks = []
        for day_offset in range(days_ahead):
            date = datetime.now() + timedelta(days=day_offset)
            tasks.append(self._fetch_day_program(channel_id, date))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_programs = []
        for result in results:
            if isinstance(result, list):
                all_programs.extend(result)
            elif isinstance(result, Exception):
                _LOGGER.debug("Chyba při načítání dne: %s", result)

        return all_programs

    async def _fetch_day_program(
        self, channel_id: str, date: datetime
    ) -> list[dict[str, Any]]:
        """Fetch program for a specific day."""
        date_str = date.strftime("%d.%m.%Y")
        url = f"{CT_API_BASE_URL}?user={self.username}&date={date_str}&channel={channel_id}"

        timeout = ClientTimeout(total=API_TIMEOUT)

        try:
            async with self.session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    content = await response.text()
                    return self._parse_ct_xml(content, date)
                else:
                    _LOGGER.warning(
                        "Nepodařilo se načíst program pro %s na %s: HTTP %s",
                        channel_id,
                        date_str,
                        response.status,
                    )
                    return []

        except asyncio.TimeoutError:
            _LOGGER.warning(
                "Timeout při načítání programu pro %s na %s", channel_id, date_str
            )
            return []

        except ClientError as err:
            _LOGGER.warning(
                "Client error při načítání programu pro %s na %s: %s",
                channel_id,
                date_str,
                err,
            )
            return []

        except Exception as err:
            _LOGGER.error(
                "Neočekávaná chyba při načítání programu pro %s na %s: %s",
                channel_id,
                date_str,
                err,
            )
            return []

    def _parse_ct_xml(self, xml_content: str, date: datetime) -> list[dict[str, Any]]:
        """Parse ČT XML response."""
        programs = []

        try:
            root: Element = ET.fromstring(xml_content)

            for porad in root.findall("porad"):
                program = {}

                # Time
                cas = porad.find("cas")
                if cas is not None:
                    program["time"] = cas.text

                # Date
                datum = porad.find("datum")
                if datum is not None:
                    program["date"] = datum.text
                else:
                    program["date"] = date.strftime("%Y-%m-%d")

                # Titles
                nazvy = porad.find("nazvy")
                if nazvy is not None:
                    nadtitul = nazvy.find("nadtitul")
                    nazev = nazvy.find("nazev")
                    nazev_casti = nazvy.find("nazev_casti")

                    program["supertitle"] = (
                        nadtitul.text if nadtitul is not None else ""
                    )
                    program["title"] = nazev.text if nazev is not None else "Bez názvu"
                    program["episode_title"] = (
                        nazev_casti.text if nazev_casti is not None else ""
                    )

                # Episode info
                dil = porad.find("dil")
                program["episode"] = dil.text if dil is not None and dil.text else ""

                # Genre
                zanr = porad.find("zanr")
                program["genre"] = zanr.text if zanr is not None else ""

                # Duration
                stopaz = porad.find("stopaz")
                program["duration"] = stopaz.text if stopaz is not None else ""

                # Description
                noticka = porad.find("noticka")
                program["description"] = noticka.text if noticka is not None else ""

                # Links
                linky = porad.find("linky")
                if linky is not None:
                    program_link = linky.find("program")
                    program["link"] = (
                        program_link.text if program_link is not None else ""
                    )
                else:
                    program["link"] = ""

                # Icons/attributes
                ikony = porad.find("ikony")
                if ikony is not None:
                    program["audio"] = (
                        ikony.find("zvuk").text
                        if ikony.find("zvuk") is not None
                        else ""
                    )
                    program["subtitles"] = (
                        ikony.find("skryte_titulky").text == "1"
                        if ikony.find("skryte_titulky") is not None
                        else False
                    )
                    program["live"] = (
                        ikony.find("live").text == "1"
                        if ikony.find("live") is not None
                        else False
                    )
                    program["premiere"] = (
                        ikony.find("premiera").text == "1"
                        if ikony.find("premiera") is not None
                        else False
                    )
                    program["aspect_ratio"] = (
                        ikony.find("pomer").text
                        if ikony.find("pomer") is not None
                        else ""
                    )

                programs.append(program)

        except ET.ParseError as err:
            _LOGGER.error("Chyba při parsování ČT XML: %s", err)

        return programs


class XMLTVProvider(TVProgramProvider):
    """Provider for XMLTV format data."""

    def __init__(self, hass: HomeAssistant, xmltv_url: str = DEFAULT_XMLTV_URL):
        """Initialize the XMLTV provider."""
        super().__init__(hass)
        self.xmltv_url = xmltv_url
        self._cached_data = None
        self._cache_time = None

    def get_available_channels(self) -> dict[str, str]:
        """Get available XMLTV channels."""
        return XMLTV_CHANNELS

    async def async_get_program(
        self, channel_id: str, days_ahead: int = DEFAULT_DAYS_AHEAD
    ) -> list[dict[str, Any]]:
        """Fetch program from XMLTV source."""
        # Load XMLTV data (cached for 1 hour)
        xmltv_data = await self._fetch_xmltv_data()

        if not xmltv_data:
            return []

        # Filter programs for the requested channel
        return self._filter_channel_programs(xmltv_data, channel_id, days_ahead)

    async def _fetch_xmltv_data(self) -> Element | None:
        """Fetch and cache XMLTV data."""
        # Check cache (1 hour)
        if self._cached_data and self._cache_time:
            if (datetime.now() - self._cache_time).seconds < 3600:
                return self._cached_data

        try:
            timeout = ClientTimeout(total=60)
            async with self.session.get(self.xmltv_url, timeout=timeout) as response:
                if response.status == 200:
                    content = await response.text()
                    root = ET.fromstring(content)
                    self._cached_data = root
                    self._cache_time = datetime.now()
                    _LOGGER.info("XMLTV data loaded successfully")
                    return root
                else:
                    _LOGGER.error(
                        "Failed to fetch XMLTV data: HTTP %s", response.status
                    )
                    return None

        except Exception as err:
            _LOGGER.error("Error fetching XMLTV data: %s", err)
            return None

    def _filter_channel_programs(
        self, root: Element, channel_id: str, days_ahead: int
    ) -> list[dict[str, Any]]:
        """Filter programs for a specific channel from XMLTV data."""
        programs = []

        # Map our channel IDs to XMLTV channel IDs
        xmltv_channel_map = {
            "prima": "prima.cz",
            "prima-cool": "cool.iprima.cz",
            "prima-zoom": "zoom.iprima.cz",
            "prima-max": "max.iprima.cz",
            "prima-love": "love.iprima.cz",
            "prima-krimi": "krimi.iprima.cz",
            "prima-star": "star.iprima.cz",
            "prima-show": "show.iprima.cz",
            "cnn-prima": "cnn.iprima.cz",
            "nova": "nova.cz",
            "nova-cinema": "cinema.nova.cz",
            "nova-action": "action.nova.cz",
            "nova-gold": "gold.nova.cz",
            "nova-sport1": "sport1.nova.cz",
            "nova-sport2": "sport2.nova.cz",
        }

        xmltv_channel_id = xmltv_channel_map.get(channel_id, channel_id)

        # Filter by date range
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=days_ahead)

        for programme in root.findall("programme"):
            channel = programme.get("channel")
            if channel != xmltv_channel_id:
                continue

            # Parse start time
            start_str = programme.get("start", "")
            if not start_str:
                continue

            try:
                # XMLTV format: YYYYMMDDHHmmss +0100
                start_time = datetime.strptime(start_str[:14], "%Y%m%d%H%M%S")
            except ValueError:
                continue

            # Filter by date range
            if not (start_date <= start_time < end_date):
                continue

            # Extract program data
            program = {
                "date": start_time.strftime("%Y-%m-%d"),
                "time": start_time.strftime("%H:%M"),
                "title": self._get_xmltv_text(programme, "title"),
                "supertitle": "",
                "episode_title": self._get_xmltv_text(programme, "sub-title"),
                "description": self._get_xmltv_text(programme, "desc"),
                "genre": self._get_xmltv_text(programme, "category"),
                "episode": "",
                "duration": "",
                "link": "",
                "live": False,
                "premiere": False,
            }

            # Calculate duration
            stop_str = programme.get("stop", "")
            if stop_str:
                try:
                    stop_time = datetime.strptime(stop_str[:14], "%Y%m%d%H%M%S")
                    duration_min = int((stop_time - start_time).seconds / 60)
                    program["duration"] = f"{duration_min} min"
                except ValueError:
                    pass

            programs.append(program)

        return programs

    def _get_xmltv_text(self, element: Element, tag: str) -> str:
        """Get text content from XMLTV element."""
        child = element.find(tag)
        return child.text if child is not None and child.text else ""
