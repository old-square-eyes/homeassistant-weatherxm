import logging
import requests
from datetime import datetime, timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfSpeed,
    UnitOfPressure,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_call_later
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

TOKEN_REFRESH_INTERVAL_DAYS = 30  # Default token refresh interval


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the WeatherXM sensor platform."""
    device_id = entry.data["station_id"]
    token = entry.data["access_token"]
    refresh_token = entry.data["refresh_token"]

    # Create the data update coordinator
    coordinator = WeatherXMDataUpdateCoordinator(hass, device_id, token, refresh_token, entry)
    await coordinator.async_refresh()
    # Define units
    CELSIUS = UnitOfTemperature.CELSIUS
    MPS = UnitOfSpeed.METERS_PER_SECOND
    HPA = UnitOfPressure.HPA

    # Define the sensors
    sensors = [
        WeatherXMSensor(coordinator, "temperature", CELSIUS, "Temperature", device_class="temperature"),
        WeatherXMSensor(coordinator, "humidity", PERCENTAGE, "Humidity", device_class="humidity"),
        WeatherXMSensor(coordinator, "wind_speed", MPS, "Wind Speed", device_class="wind_speed"),
        WeatherXMSensor(coordinator, "wind_gust", MPS, "Wind Gust"),
        WeatherXMSensor(coordinator, "wind_direction", "°", "Wind Direction"),
        WeatherXMSensor(coordinator, "solar_irradiance", "W/m²", "Solar Irradiance"),
        WeatherXMSensor(coordinator, "uv_index", "UV Index", "UV Index"),
        WeatherXMSensor(coordinator, "precipitation", "mm", "Precipitation"),
        WeatherXMSensor(coordinator, "pressure", HPA, "Pressure"),
        WeatherXMSensor(coordinator, "dew_point", CELSIUS, "Dew Point"),
        WeatherXMSensor(coordinator, "precipitation_accumulated", "mm", "Precipitation Accumulated"),
        WeatherXMSensor(coordinator, "feels_like", CELSIUS, "Feels Like", device_class="temperature"),
        WeatherXMSensor(coordinator, "actual_reward", "WXM", "Actual Reward"),
        WeatherXMSensor(coordinator, "total_rewards", "WXM", "Total Rewards"),
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
        url = "https://api.weatherxm.com/api/v1/auth/refresh"
        payload = {"refreshToken": self.refresh_token}
        headers = {"Content-Type": "application/json"}

        try:
            response = await self.hass.async_add_executor_job(
                lambda: requests.post(url, json=payload, headers=headers)
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data["token"]
                self.refresh_token = data["refreshToken"]

                # Update config entry
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
                _LOGGER.error(
                    "Failed to refresh WeatherXM token. Status: %s, Response: %s",
                    response.status_code,
                    response.text,
                )
        except Exception as e:
            _LOGGER.error("Error refreshing WeatherXM token: %s", e)

        # Reschedule the next refresh
        self._schedule_token_refresh()

    def _fetch_data(self):
        """Fetch data from WeatherXM API."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        url = f"https://api.weatherxm.com/api/v1/me/devices/{self.device_id}"
        _LOGGER.debug(f"Fetching data from URL: {url}")
        response = requests.get(url, headers=headers)

        if response.status_code == 401:  # Token expired
            _LOGGER.warning("Token expired, refreshing token.")
            self.hass.async_create_task(self._refresh_token(None))
            raise UpdateFailed("Token expired, refreshing token.")

        if response.status_code != 200:
            _LOGGER.error(f"Failed to fetch data: {response.status_code} - {response.text}")
            raise UpdateFailed(f"Error {response.status_code}: {response.text}")

        try:
            return response.json()
        except ValueError as err:
            _LOGGER.error("Invalid JSON received from WeatherXM API")
            raise UpdateFailed(f"Invalid JSON: {err}")

    async def _async_update_data(self):
        """Fetch data from WeatherXM API."""
        try:
            data = await self.hass.async_add_executor_job(self._fetch_data)

            if 'error' in data:
                raise UpdateFailed(f"Error from WeatherXM API: {data['error']}")
            if 'current_weather' not in data or 'rewards' not in data:
                raise UpdateFailed(f"Unexpected data format: {data}")

            return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching data from WeatherXM API: {err}")

class WeatherXMSensor(SensorEntity):
    """Representation of a WeatherXM sensor."""

    def __init__(self, coordinator, key, unit, name, device_class=None):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._key = key
        self._attr_name = f"WeatherXM {name}"
        self._attr_unit_of_measurement = unit
        if device_class:
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
        }

    @property
    def state(self):
        """Return the state of the sensor, with optional rounding."""
        if not self.coordinator.data:
            return None

        value = None
        if self._key in self.coordinator.data["current_weather"]:
            value = self.coordinator.data["current_weather"][self._key]
        elif self._key in self.coordinator.data["rewards"]:
            value = self.coordinator.data["rewards"][self._key]

        if value is not None and self._key in self._round_rules:
            try:
                value = round(float(value), self._round_rules[self._key])
            except (ValueError, TypeError):
                pass

        return value

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attributes = {}
        if self.coordinator.data:
            if 'current_weather' in self.coordinator.data:
                attributes.update(self.coordinator.data["current_weather"])
            if 'rewards' in self.coordinator.data:
                attributes.update(self.coordinator.data["rewards"])
        return attributes
