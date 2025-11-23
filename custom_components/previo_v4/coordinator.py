import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .client import PrevioClient

_LOGGER = logging.getLogger(__name__)

class PrevioDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        self.hass = hass
        self.url = entry.data["url"]
        self.login = entry.data["login"]
        self.password = entry.data["password"]
        self.hotel_id = entry.data["hotel_id"]

        self.client = PrevioClient(
            session=async_get_clientsession(hass),
            url=self.url,
            login=self.login,
            password=self.password,
            hotel_id=self.hotel_id
        )

        super().__init__(
            hass,
            _LOGGER,
            name="Previo v4",
            update_interval=timedelta(minutes=15),
        )

    async def _async_update_data(self):
        return await self.client.get_data()