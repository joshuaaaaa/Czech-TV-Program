import logging
import xml.etree.ElementTree as ET
from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)

class PrevioClient:
    def __init__(self, session: ClientSession, url: str, login: str, password: str, hotel_id: str):
        self._session = session
        self._url = url
        self._login = login
        self._password = password
        self._hotel_id = hotel_id

    async def get_data(self):
        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
        <request>
            <credentials>
                <login>{self._login}</login>
                <password>{self._password}</password>
            </credentials>
            <data>
                <hotId>{self._hotel_id}</hotId>
            </data>
        </request>
        """

        headers = {
            "Content-Type": "application/xml"
        }

        async with self._session.post(self._url, data=payload, headers=headers) as response:
            response_text = await response.text()
            return self._parse_response(response_text)

    def _parse_response(self, xml_string):
        root = ET.fromstring(xml_string)
        reservations = []

        for res in root.findall(".//reservation"):
            try:
                reservation_id = res.findtext("id")
                voucher = res.findtext("voucher") or ""
                room = res.findtext("room") or ""
                checkin = res.findtext("checkIn") or ""
                checkout = res.findtext("checkOut") or ""

                reservations.append({
                    "id": reservation_id,
                    "voucher": voucher,
                    "room": room,
                    "checkin": checkin,
                    "checkout": checkout,
                })
            except Exception as e:
                _LOGGER.error(f"Failed to parse reservation: {e}")

        return reservations
