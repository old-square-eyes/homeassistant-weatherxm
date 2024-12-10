import logging
from datetime import timedelta
import aiohttp

from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfSpeed,
    UnitOfPressure,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed, CoordinatorEntity
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

TOKEN_REFRESH_INTERVAL_DAYS = 30  # Default token refresh interval

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the WeatherXM sensor platform."""
    device_id = entry.data["station_id"]
    token = entry.data["access_token"]
    refresh_token = entry.data["refresh_token"]

    coordinator = WeatherXMDataUpdateCoordinator(hass, device_id, token, refresh_token, entry)
    try:
        await coordinator.async_config_entry_first_refresh()
    except UpdateFailed as err:
        # If the first update fails, we can raise ConfigEntryNotReady to delay setup
        _LOGGER.warning("Initial update failed. Will retry later: %s", err)
        raise ConfigEntryNotReady from err

    # Define units
    CELSIUS = UnitOfTemperature.CELSIUS
    MPS = UnitOfSpeed.METERS_PER_SECOND
    HPA = UnitOfPressure.HPA

    # Define the sensors
    sensors = [
        WeatherXMSensor(
            coordinator,
            "temperature",
            CELSIUS,
            "Temperature",
            device_class=SensorDeviceClass.TEMPERATURE
        ),
        WeatherXMSensor(
            coordinator,
            "humidity",
            PERCENTAGE,
            "Humidity",
            device_class=SensorDeviceClass.HUMIDITY
        ),
        WeatherXMSensor(
            coordinator,
            "wind_speed",
            MPS,
            "Wind Speed"
        ),
        WeatherXMSensor(
            coordinator,
            "wind_gust",
            MPS,
            "Wind Gust"
        ),
        WeatherXMSensor(
            coordinator,
            "wind_direction",
            "°",
            "Wind Direction"
        ),
        WeatherXMSensor(
            coordinator,
            "solar_irradiance",
            "W/m²",
            "Solar Irradiance"
        ),
        WeatherXMSensor(
            coordinator,
            "uv_index",
            None,
            "UV Index"
        ),
        WeatherXMSensor(
            coordinator,
            "precipitation",
            "mm",
            "Precipitation"
        ),
        WeatherXMSensor(
            coordinator,
            "pressure",
            HPA,
            "Pressure",
            device_class=SensorDeviceClass.PRESSURE
        ),
        WeatherXMSensor(
            coordinator,
            "dew_point",
            CELSIUS,
            "Dew Point",
            device_class=SensorDeviceClass.TEMPERATURE
        ),
        WeatherXMSensor(
            coordinator,
            "precipitation_accumulated",
            "mm",
            "Precipitation Accumulated"
        ),
        WeatherXMSensor(
            coordinator,
            "feels_like",
            CELSIUS,
            "Feels Like",
            device_class=SensorDeviceClass.TEMPERATURE
        ),
        WeatherXMSensor(
            coordinator,
            "actual_reward",
            "WXM",
            "Actual Reward"
        ),
        WeatherXMSensor(
            coordinator,
            "total_rewards",
            "WXM",
            "Total Rewards"
        ),
    ]

    async_add_entities(sensors, True)


class WeatherXMDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from WeatherXM API."""

    def __init__(self, hass, device_id, token, refresh_token, entry):
        """Initialize the data update coordinator."""
        self.device_id = device_id
        self.token = token
        self.refresh_token = refresh_token
        self.entry = entry
        self.hass = hass

        super().__init__(
            hass,
            _LOGGER,
            name="WeatherXM",
            update_method=self._async_update_data,
            update_interval=timedelta(minutes=10),
        )

        # Schedule token refresh
        self._schedule_token_refresh()

    def _schedule_token_refresh(self):
        """Schedule token refresh based on the configured interval."""
        async_call_later(
            self.hass,
            timedelta(days=TOKEN_REFRESH_INTERVAL_DAYS),
            self._refresh_token,
        )

    async def _refresh_token(self, _):
        """Refresh the access token using the refresh token."""
        _LOGGER.debug("Attempting to refresh WeatherXM token...")
        url = "https://api.weatherxm.com/api/v1/auth/refresh"
        payload = {"refreshToken": self.refresh_token}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.token = data["token"]
                    self.refresh_token = data["refreshToken"]

                    # Update config entry with new tokens
                    self.hass.config_entries.async_update_entry(
                        self.entry,
                        data={
                            **self.entry.data,
                            "access_token": self.token,
                            "refresh_token": self.refresh_token,
                        },
                    )
                    _LOGGER.info("Successfully refreshed WeatherXM token.")
                else:
                    text = await response.text()
                    _LOGGER.error(
                        "Failed to refresh WeatherXM token. Status: %s, Response: %s",
                        response.status,
                        text,
                    )
                    raise UpdateFailed(f"Failed to refresh token: {text}")

        # Reschedule the next refresh
        self._schedule_token_refresh()

    async def _fetch_data(self):
        """Fetch data from WeatherXM API asynchronously."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        url = f"https://api.weatherxm.com/api/v1/me/devices/{self.device_id}"
        _LOGGER.debug(f"Fetching data from URL: {url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 401:
                    _LOGGER.warning("Token expired, will attempt refresh.")
                    raise UpdateFailed("Token expired")

                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error(f"Failed to fetch data: {response.status} - {text}")
                    raise UpdateFailed(f"Error {response.status}: {text}")

                try:
                    return await response.json()
                except ValueError as err:
                    _LOGGER.error("Invalid JSON received from WeatherXM API")
                    raise UpdateFailed(f"Invalid JSON: {err}")

    async def _async_update_data(self):
        """Fetch data from WeatherXM API and handle token expiration."""
        _LOGGER.debug("Running _async_update_data to fetch new WeatherXM data.")
        try:
            data = await self._fetch_data()
            if 'error' in data:
                raise UpdateFailed(f"Error from WeatherXM API: {data['error']}")
            if 'current_weather' not in data or 'rewards' not in data:
                raise UpdateFailed(f"Unexpected data format: {data}")

            _LOGGER.debug("Successfully fetched and validated WeatherXM data.")
            return data
        except UpdateFailed as err:
            if "Token expired" in str(err):
                # Attempt to refresh token and retry once
                _LOGGER.debug("Token expired, refreshing and retrying data fetch.")
                await self._refresh_token(None)
                data = await self._fetch_data()
                if 'error' in data:
                    raise UpdateFailed(f"Error from WeatherXM API: {data['error']}")
                if 'current_weather' not in data or 'rewards' not in data:
                    raise UpdateFailed(f"Unexpected data format after token refresh: {data}")
                _LOGGER.debug("Successfully fetched data after token refresh.")
                return data
            else:
                raise err


class WeatherXMSensor(CoordinatorEntity, SensorEntity):
    """Representation of a WeatherXM sensor."""

    def __init__(self, coordinator, key, unit, name, device_class=None):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"WeatherXM {name}"
        self._attr_native_unit_of_measurement = unit  # Updated to use _attr_native_unit_of_measurement if running HA >= 2022.5
        if device_class is not None:
            self._attr_device_class = device_class

        self._attr_unique_id = f"{coordinator.device_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.device_id)},
            "name": "WeatherXM Station",
            "manufacturer": "WeatherXM",
            "model": "WeatherXM Station",
        }

        self._round_rules = {
            "pressure": 1,
            "dew_point": 1,
            "actual_reward": 2,
            "precipitation_accumulated": 1,
            "solar_irradiance": 1
        }

    @property
    def native_value(self):
        # If running older HA versions, revert to `state` property
        if not self.coordinator.data:
            return None

        value = None
        if self._key in self.coordinator.data.get("current_weather", {}):
            value = self.coordinator.data["current_weather"][self._key]
        elif self._key in self.coordinator.data.get("rewards", {}):
            value = self.coordinator.data["rewards"][self._key]

        if value is not None and self._key in self._round_rules:
            try:
                value = round(float(value), self._round_rules[self._key])
            except (ValueError, TypeError):
                pass

        return value

    @property
    def extra_state_attributes(self):
        attributes = {}
        if self.coordinator.data:
            if 'current_weather' in self.coordinator.data:
                attributes.update(self.coordinator.data["current_weather"])
            if 'rewards' in self.coordinator.data:
                attributes.update(self.coordinator.data["rewards"])
        return attributes
