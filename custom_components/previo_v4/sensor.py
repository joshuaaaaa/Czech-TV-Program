# sensor.py
from datetime import datetime, timedelta
import logging
import xml.etree.ElementTree as ET
from collections import defaultdict

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, STATUS_MAPPING, STATUS_MAPPING_CZ

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=15)

# Nastavení jazyka pro statusy (změňte na STATUS_MAPPING_CZ pro češtinu)
USE_STATUS_MAPPING = STATUS_MAPPING  # nebo STATUS_MAPPING_CZ

# ------------------------------------------------------------------ #
# 1. Nastavení platformy                                             #
# ------------------------------------------------------------------ #
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Nastav koordinátora a vytvoř senzory."""
    coordinator = PrevioCoordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()

    hotel_id = config_entry.data["hotel_id"]
    device = DeviceInfo(
        identifiers={(DOMAIN, hotel_id)},
        name=f"Hotel {hotel_id}",
        manufacturer="Previo",
    )

    tracked = set()

    def _sync_entities():
        """Přidej nové senzory, které ještě nejsou sledovány."""
        _LOGGER.info("=== SYNC ENTITIES START ===")
        _LOGGER.info("Coordinator data: %s", coordinator.data)
        _LOGGER.info("Tracked: %s", tracked)
        
        new_entities = []
        if coordinator.data:
            for res_id in coordinator.data:
                _LOGGER.info("Processing res_id: %s, tracked: %s", res_id, res_id in tracked)
                if res_id not in tracked:
                    _LOGGER.info("Creating new sensor for %s", res_id)
                    new_entities.append(
                        PrevioV4Sensor(coordinator, res_id, device, hotel_id)
                    )
                    tracked.add(res_id)
        
        if new_entities:
            _LOGGER.info("Adding %d new entities", len(new_entities))
            async_add_entities(new_entities)
        else:
            _LOGGER.info("No new entities to add")
        _LOGGER.info("=== SYNC ENTITIES END ===")

    # Uložení dat pro debug služby
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    
    hass.data[DOMAIN][config_entry.entry_id] = {
        'coordinator': coordinator,
        'sync_callback': _sync_entities,
        'tracked': tracked
    }

    _sync_entities()
    coordinator.async_add_listener(_sync_entities)


# ------------------------------------------------------------------ #
# 2. Koordinátor – načítá data z API každých 15 min                  #
# ------------------------------------------------------------------ #
class PrevioCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config_entry):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.config_entry = config_entry

    async def _async_update_data(self):
        """Stáhni a rozparsoj XML z Previa."""
        _LOGGER.info("=== STARTING DATA UPDATE ===")
        
        login = self.config_entry.data["login"]
        password = self.config_entry.data["password"]
        hotel_id = self.config_entry.data["hotel_id"]
        session = async_get_clientsession(self.hass)

        today = datetime.now()
        to_date = today + timedelta(days=30)

        # Podle oficiální Previo API dokumentace:
        # cosId: 1=Option, 2=Confirmed, 3=Checked in, 6=Waiting list, 
        #        7=Cancelled, 8=No-show, 9=Checked out, 10=Other
        xml_payload = f"""<?xml version="1.0"?>
<request>
    <login>{login}</login>
    <password>{password}</password>
    <hotId>{hotel_id}</hotId>
    <term>
        <from>{today.strftime('%Y-%m-%d')}</from>
        <to>{to_date.strftime('%Y-%m-%d')}</to>
    </term>
    <statuses>
        <cosId>1</cosId>
        <cosId>2</cosId>
        <cosId>3</cosId>
        <cosId>6</cosId>
        <cosId>7</cosId>
        <cosId>8</cosId>
        <cosId>9</cosId>
        <cosId>10</cosId>
    </statuses>
    <limit><offset>0</offset><limit>50</limit></limit>
</request>"""

        try:
            async with session.post(
                "https://api.previo.app/x1/hotel/searchReservations",
                data=xml_payload,
                headers={"Content-Type": "application/xml"},
            ) as resp:
                text = await resp.text()
                _LOGGER.info("Previo response received, length: %d", len(text))
        except Exception as e:
            _LOGGER.error("Chyba při volání Previa: %s", e)
            return {}

        # Seskupení rezervací podle resId
        grouped_reservations = defaultdict(list)
        
        try:
            tree = ET.fromstring(text)
            reservations = tree.findall(".//reservation")
            _LOGGER.info("Found %d reservations in XML", len(reservations))
            
            for res in reservations:
                res_id = res.findtext("resId")
                if not res_id:
                    continue
                grouped_reservations[res_id].append(res)
            
            _LOGGER.info("Grouped into %d unique reservations", len(grouped_reservations))
            
        except Exception as e:
            _LOGGER.error("Chyba při parsování XML: %s", e)
            return {}

        # Zpracování seskupených rezervací
        data = {}
        
        for res_id, res_list in grouped_reservations.items():
            try:
                # Detekce SINGLE vs GROUP
                is_group = len(res_list) > 1
                _LOGGER.info("Processing resId %s: %s reservation with %d room(s)", 
                           res_id, "GROUP" if is_group else "SINGLE", len(res_list))
                
                # Inicializace agregovaných dat
                rooms = []
                com_ids = []
                alfred_pins = []
                card_keys = []
                checkins = []
                checkouts = []
                prices = []
                guests = []
                market_codes_all = []
                
                # První rezervace pro základní údaje
                first_res = res_list[0]
                voucher = first_res.findtext("voucher") or "není"
                status_id = first_res.findtext("status/statusId", "0")
                
                # Zpracování každé pod-rezervace (pokoje)
                for res in res_list:
                    # comId
                    com_id = res.findtext("comId")
                    if com_id:
                        com_ids.append(com_id)
                    
                    # Pokoj
                    room_el = res.find("object")
                    if room_el is not None:
                        room_name = room_el.findtext("name")
                        if room_name:
                            rooms.append(room_name)
                    
                    # Host (první v této pod-rezervaci)
                    guest_el = res.find("guest")
                    if guest_el is not None:
                        guest_name = guest_el.findtext("name")
                        if guest_name:
                            guests.append(guest_name)
                    
                    # Alfred PIN
                    alfred_code_list = res.find("alfredCodeList")
                    if alfred_code_list is not None:
                        for alfred_code in alfred_code_list.findall("alfredCode"):
                            pin = alfred_code.findtext("pin")
                            if pin:
                                alfred_pins.append(pin)
                    
                    # Card Key
                    card_data_list = res.find("cardDataList")
                    if card_data_list is not None:
                        for card_data in card_data_list.findall("cardData"):
                            key = card_data.findtext("key")
                            if key:
                                card_keys.append(key)
                    
                    # Check-in/out
                    checkin_str = res.findtext("term/from")
                    checkout_str = res.findtext("term/to")
                    
                    if checkin_str:
                        try:
                            dt = datetime.strptime(checkin_str, "%Y-%m-%d %H:%M:%S")
                            checkins.append(dt.strftime("%B %d, %Y at %I:%M:%S %p"))
                        except ValueError:
                            checkins.append(checkin_str)
                    
                    if checkout_str:
                        try:
                            dt = datetime.strptime(checkout_str, "%Y-%m-%d %H:%M:%S")
                            checkouts.append(dt.strftime("%B %d, %Y at %I:%M:%S %p"))
                        except ValueError:
                            checkouts.append(checkout_str)
                    
                    # Cena
                    price_str = res.findtext("price", "0")
                    try:
                        price_float = float(price_str) if price_str else 0.0
                        prices.append(price_float)
                    except ValueError:
                        prices.append(0.0)
                    
                    # Market codes
                    market_code_list = res.find("marketCodeList")
                    if market_code_list is not None:
                        for market_code in market_code_list.findall("marketCode"):
                            code = market_code.text
                            if code and code not in market_codes_all:
                                market_codes_all.append(code)
                
                # Agregace dat
                total_price = sum(prices)
                
                # Výpočet dnů do check-in (z prvního check-in)
                days_until_checkin = None
                if checkins:
                    try:
                        checkin_dt = datetime.strptime(checkins[0], "%B %d, %Y at %I:%M:%S %p")
                        today = datetime.now()
                        days_until_checkin = (checkin_dt.date() - today.date()).days
                    except ValueError:
                        pass
                
                # Sestavení finálních dat
                data[res_id] = {
                    "voucher": voucher,
                    "guest": guests[0] if guests else "Host",  # První host
                    
                    # SINGLE/GROUP konzistence
                    "room": ", ".join(rooms) if rooms else "neznámý pokoj",  # String pro backward compatibility
                    "rooms": rooms,  # List
                    
                    "alfred_pin": alfred_pins[0] if len(alfred_pins) == 1 else None,  # Single
                    "alfred_pins": alfred_pins,  # List
                    
                    "card_key": card_keys[0] if len(card_keys) == 1 else None,  # Single
                    "card_keys": card_keys,  # List
                    
                    "com_id": com_ids[0] if len(com_ids) == 1 else None,  # Single
                    "com_ids": com_ids,  # List
                    
                    "checkin": checkins[0] if checkins else None,  # První pro backward compatibility
                    "checkout": checkouts[0] if checkouts else None,  # První
                    "checkins": checkins,  # List všech
                    "checkouts": checkouts,  # List všech
                    
                    "price": f"{total_price:.2f}",
                    "price_numeric": total_price,
                    "price_formatted": f"{total_price:.2f} CZK" if total_price > 0 else "0 CZK",
                    
                    "status_id": status_id,
                    "status_name": USE_STATUS_MAPPING.get(status_id, f"Unknown Status {status_id}"),
                    "status_name_en": STATUS_MAPPING.get(status_id, f"Unknown Status {status_id}"),
                    "status_name_cz": STATUS_MAPPING_CZ.get(status_id, f"Neznámý status {status_id}"),
                    
                    "market_codes": market_codes_all,
                    "market_codes_text": ", ".join(market_codes_all) if market_codes_all else "žádné",
                    
                    "days_until_checkin": days_until_checkin,
                    "hotel_id": hotel_id,
                    "last_updated": datetime.now().isoformat(),
                    
                    # Metadata
                    "is_group": is_group,
                    "room_count": len(rooms),
                }
                
                _LOGGER.info("Processed reservation %s (%s): %d rooms, status: %s", 
                           res_id, "GROUP" if is_group else "SINGLE", len(rooms), 
                           STATUS_MAPPING.get(status_id, f"Status {status_id}"))
                
            except Exception as e:
                _LOGGER.error("Chyba při zpracování rezervace %s: %s", res_id, e)
                continue

        _LOGGER.info("Final data: %d reservations processed", len(data))
        return data


# ------------------------------------------------------------------ #
# 3. Senzor – jedna rezervace = jedna entita                         #
# ------------------------------------------------------------------ #
class PrevioV4Sensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, res_id, device, hotel_id):
        super().__init__(coordinator)
        self._res_id = res_id
        self._attr_device_info = device
        self._attr_unique_id = f"{DOMAIN}_{hotel_id}_{res_id}"

    @property
    def name(self):
        if not self.available:
            return f"Previo v4 {self._res_id}"
        voucher = self.coordinator.data[self._res_id].get("voucher", "rezervace")
        return f"Previo v4 {voucher}"

    @property
    def native_value(self):
        if not self.available:
            return None
        return self.coordinator.data[self._res_id].get("voucher")

    @property
    def extra_state_attributes(self):
        if not self.available:
            return {}
            
        info = self.coordinator.data[self._res_id]
        
        return {
            "res_id": self._res_id,
            "guest": info["guest"],
            
            # Pokoje
            "room": info["room"],  # String pro backward compatibility
            "rooms": info["rooms"],  # List
            "room_count": info["room_count"],
            "is_group": info["is_group"],
            
            # PINy a klíče
            "alfred_pin": info.get("alfred_pin"),  # Single nebo None
            "alfred_pins": info["alfred_pins"],  # List
            "card_key": info.get("card_key"),  # Single nebo None
            "card_keys": info["card_keys"],  # List
            
            # ComId
            "com_id": info.get("com_id"),  # Single nebo None
            "com_ids": info["com_ids"],  # List
            
            # Časy
            "checkin": info["checkin"],  # První (backward compatibility)
            "checkout": info["checkout"],  # První
            "checkins": info["checkins"],  # List všech
            "checkouts": info["checkouts"],  # List všech
            "days_until_checkin": info["days_until_checkin"],
            
            # Ceny
            "price": info["price_formatted"],
            "price_numeric": info["price_numeric"],
            
            # Status (všechny verze pro flexibilitu)
            "status_id": info["status_id"],
            "status": info["status_name"],          # Vybraný jazyk
            "status_en": info["status_name_en"],    # Anglicky
            "status_cz": info["status_name_cz"],    # Česky
            
            # Ostatní
            "market_codes": info["market_codes"],
            "market_codes_text": info["market_codes_text"],
            "hotel_id": info["hotel_id"],
            "last_updated": info["last_updated"],
        }

    @property
    def available(self):
        return (
            self.coordinator.last_update_success 
            and self.coordinator.data is not None
            and self._res_id in self.coordinator.data
        )