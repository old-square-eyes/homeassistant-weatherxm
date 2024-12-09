from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState
import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the WeatherXM component."""
    # Initialize the domain data structure
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("WeatherXM component setup initialized.")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up WeatherXM from a config entry."""
    _LOGGER.debug("Setting up WeatherXM entry with ID: %s", entry.entry_id)

    # Store the config entry data in hass.data
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Check ConfigEntryState
    if entry.state != ConfigEntryState.SETUP_IN_PROGRESS:
        _LOGGER.warning("Config entry state is not SETUP_IN_PROGRESS: %s", entry.state)

    # Forward the entry to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.debug("Unloading WeatherXM entry with ID: %s", entry.entry_id)

    # Remove the entry data from hass.data
    if entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)

    # Unload the sensor platform
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    return True