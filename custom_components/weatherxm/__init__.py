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
    _LOGGER.debug("Setting up WeatherXM entry with ID: %s", entry.entry_id)

    try:
        # Perform any required setup
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = entry.data

        # Forward entry setup
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    except Exception as e:
        _LOGGER.error(f"Error setting up WeatherXM entry: {e}")
        raise ConfigEntryNotReady from e  # Raise this to defer setup until ready
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