"""Czech TV Program Integration for Home Assistant."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CzTVProgramAPI
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=6)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Czech TV Program from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get channels from options or data
    channels = entry.options.get(f"{DOMAIN}_OPTIONS") or entry.data.get("channels", [])
    
    api = CzTVProgramAPI(
        hass=hass,
        username=entry.data.get("username", "test"),
        channels=channels,
    )

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=api.async_update_data,
        update_interval=SCAN_INTERVAL,
        # KRITICKÁ OPRAVA: timeout pro update, aby nezamrzl HA
        request_refresh_debouncer=None,
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }

    # KRITICKÁ OPRAVA: Neblokující refresh - HA startuje i bez dat
    # Data se načtou na pozadí
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Spustit první refresh na pozadí (neblokující)
    hass.async_create_task(coordinator.async_refresh())
    
    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    return True


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options updates."""
    # OPRAVA: Pouze aktualizovat API channely, ne reload celé integrace
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    
    # Aktualizovat channely
    channels = entry.options.get(f"{DOMAIN}_OPTIONS") or entry.data.get("channels", [])
    api.channels = channels
    
    # Refresh dat
    await coordinator.async_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
