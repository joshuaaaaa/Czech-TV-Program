"""API client for Czech TV Program."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any
from xml.etree.ElementTree import Element

from aiohttp.client import ClientError, ClientTimeout
from defusedxml import ElementTree as ET
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_BASE_URL, API_TIMEOUT, AVAILABLE_CHANNELS, DEFAULT_DAYS_AHEAD

_LOGGER = logging.getLogger(__name__)


class CzTVProgramAPI:
    """API client for Czech TV Program."""

    def __init__(self, hass: HomeAssistant, username: str, channels: list[str]):
        """Initialize the API client."""
        self.hass = hass
        self.username = username
        self.channels = channels or list(AVAILABLE_CHANNELS.keys())
        self.session = async_get_clientsession(hass)

    async def async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint."""
        # KRITICKÁ OPRAVA: Paralelní requesty místo sekvenčních
        tasks = []
        for channel_id in self.channels:
            tasks.append(self._fetch_channel_program_safe(channel_id))
        
        # Spustit všechny requesty paralelně s timeoutem
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=120  # Max 2 minuty pro všechny requesty
            )
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout při načítání TV programů (>120s)")
            return {}
        
        # Zpracovat výsledky
        all_data = {}
        for channel_id, result in zip(self.channels, results):
            if isinstance(result, Exception):
                _LOGGER.error("Chyba při načítání %s: %s", channel_id, result)
                all_data[channel_id] = []
            else:
                all_data[channel_id] = result
        
        return all_data

    async def _fetch_channel_program_safe(self, channel_id: str) -> list[dict[str, Any]]:
        """Fetch program for a specific channel with error handling."""
        try:
            return await self._fetch_channel_program(channel_id)
        except Exception as err:
            _LOGGER.error("Chyba při načítání programu pro %s: %s", channel_id, err)
            return []

    async def _fetch_channel_program(self, channel_id: str) -> list[dict[str, Any]]:
        """Fetch program for a specific channel."""
        # OPRAVA: Paralelní requesty pro jednotlivé dny
        tasks = []
        for day_offset in range(DEFAULT_DAYS_AHEAD):
            date = datetime.now() + timedelta(days=day_offset)
            tasks.append(self._fetch_day_program(channel_id, date))
        
        # Spustit všechny dny paralelně
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Spojit výsledky
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
        url = f"{API_BASE_URL}?user={self.username}&date={date_str}&channel={channel_id}"
        
        timeout = ClientTimeout(total=API_TIMEOUT)
        
        try:
            async with self.session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    content = await response.text()
                    return self._parse_xml(content, date)
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

    def _parse_xml(self, xml_content: str, date: datetime) -> list[dict[str, Any]]:
        """Parse XML response."""
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
            _LOGGER.error("Chyba při parsování XML: %s", err)

        return programs
