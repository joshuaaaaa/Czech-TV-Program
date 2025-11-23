import logging
import inspect
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Nastavení integrace z configuration.yaml (deprecated)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Nastavení integrace z config entry."""
    _LOGGER.info("Setting up Previo v4 integration for hotel %s", entry.data.get("hotel_id"))
    
    # Nastavení platformy sensor
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    
    # Registrace debug služeb
    async def debug_previo_service(call):
        """Debug služba pro Previo - manuální refresh."""
        entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if entry_data:
            coordinator = entry_data['coordinator']
            sync_callback = entry_data['sync_callback']
            tracked = entry_data['tracked']
            
            _LOGGER.info("=== MANUAL REFRESH START ===")
            _LOGGER.info("Current coordinator data: %s", coordinator.data)
            _LOGGER.info("Currently tracked: %s", tracked)
            _LOGGER.info("Coordinator last update success: %s", coordinator.last_update_success)
            _LOGGER.info("Requesting manual refresh...")
            
            await coordinator.async_request_refresh()
            
            _LOGGER.info("Manual refresh completed")
            _LOGGER.info("New coordinator data: %s", coordinator.data)
            _LOGGER.info("Calling sync callback manually...")

            # ✅ Opravená část
            if inspect.iscoroutinefunction(sync_callback):
                await sync_callback()
            else:
                await hass.async_add_executor_job(sync_callback)
            
            _LOGGER.info("Manual sync completed")
        else:
            _LOGGER.error("Entry data not found for entry %s", entry.entry_id)
    
    async def debug_entities_service(call):
        """Debug služba - zobrazí všechny entity."""
        entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if entry_data:
            coordinator = entry_data['coordinator']
            tracked = entry_data['tracked']
            
            _LOGGER.info("=== ENTITIES DEBUG ===")
            _LOGGER.info("Tracked reservations: %s", tracked)
            _LOGGER.info("Coordinator data keys: %s", list(coordinator.data.keys()) if coordinator.data else [])
            
            for entity_id, entity in hass.states.async_all().items():
                if entity_id.startswith('sensor.rezervace_'):
                    _LOGGER.info("Entity: %s", entity_id)
                    _LOGGER.info("  State: %s", entity.state)
                    _LOGGER.info("  Attributes: %s", dict(entity.attributes))
        else:
            _LOGGER.error("Entry data not found")
    
    # Registrace služeb bez schema (jednodušší)
    if not hass.services.has_service(DOMAIN, "manual_refresh"):
        hass.services.async_register(
            DOMAIN, 
            "manual_refresh", 
            debug_previo_service
        )
    
    if not hass.services.has_service(DOMAIN, "debug_entities"):
        hass.services.async_register(
            DOMAIN, 
            "debug_entities", 
            debug_entities_service
        )
    
    _LOGGER.info("Previo v4 integration setup completed")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Odstranění integrace."""
    _LOGGER.info("Unloading Previo v4 integration")
    
    # Odregistrace služeb
    if hass.services.has_service(DOMAIN, "manual_refresh"):
        hass.services.async_remove(DOMAIN, "manual_refresh")
    
    if hass.services.has_service(DOMAIN, "debug_entities"):
        hass.services.async_remove(DOMAIN, "debug_entities")
    
    # Vyčištění dat
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        del hass.data[DOMAIN][entry.entry_id]
    
    # Unload platformy
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
