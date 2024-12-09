import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import requests
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

@callback
def configured_instances(hass):
    """Return a set of configured instances."""
    return {entry.data["station_id"] for entry in hass.config_entries.async_entries(DOMAIN)}

class WeatherXMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WeatherXM."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize the config flow."""
        self.username = None
        self.password = None
        self.token_data = None
        self.stations = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step where the user provides username and password."""
        errors = {}

        if user_input is not None:
            self.username = user_input["username"]
            self.password = user_input["password"]
            _LOGGER.debug("Received username and password from user.")

            try:
                # Authenticate with the API
                _LOGGER.debug("Authenticating with WeatherXM API...")
                self.token_data = await self._authenticate(self.username, self.password)
                _LOGGER.debug("Authentication successful. Token obtained.")

                # Fetch the list of stations
                _LOGGER.debug("Fetching list of stations for this user...")
                self.stations = await self._fetch_stations(self.token_data["token"])
                _LOGGER.debug("Stations fetched successfully: %s", list(self.stations.keys()))

                # Proceed to the station selection step
                return await self.async_step_select_station()
            except Exception as e:
                _LOGGER.error("Error during WeatherXM authentication or station fetch: %s", e)
                errors["base"] = "invalid_auth"

        # Display the login form
        data_schema = vol.Schema({
            vol.Required("username"): str,
            vol.Required("password"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_select_station(self, user_input=None):
        """Handle station selection step, providing a dropdown of stations."""
        errors = {}

        if user_input is not None:
            selected_station = user_input["station"]

            # Check if this station is already configured
            if selected_station in configured_instances(self.hass):
                errors["base"] = "already_configured"
            else:
                _LOGGER.debug("User selected station: %s (ID: %s)", selected_station, self.stations[selected_station])
                return self.async_create_entry(
                    title=f"WeatherXM {selected_station}",
                    data={
                        "username": self.username,
                        "access_token": self.token_data["token"],
                        "refresh_token": self.token_data["refreshToken"],
                        "station_id": self.stations[selected_station],
                    },
                )

        # Populate the dropdown with station names
        station_names = list(self.stations.keys())
        data_schema = vol.Schema({
            vol.Required("station"): vol.In(station_names)
        })

        return self.async_show_form(
            step_id="select_station",
            data_schema=data_schema,
            errors=errors,
        )

    async def _authenticate(self, username, password):
        """Authenticate with the WeatherXM API."""
        url = "https://api.weatherxm.com/api/v1/auth/login"
        payload = {"username": username, "password": password}
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        _LOGGER.debug("Auth request to %s with username: %s", url, username)

        session = async_get_clientsession(self.hass)
        response = await self.hass.async_add_executor_job(
            lambda: requests.post(url, headers=headers, json=payload)
        )

        if response.status_code == 200:
            data = response.json()
            # Expecting 'token' and 'refreshToken'
            if "token" in data and "refreshToken" in data:
                return data
            else:
                _LOGGER.error("Authentication response missing expected tokens. Response: %s", data)
                raise ValueError("Missing tokens in authentication response")
        else:
            raise ValueError(f"Authentication failed: HTTP {response.status_code} - {response.text}")

    async def _fetch_stations(self, access_token):
        """Fetch the list of stations for the authenticated user."""
        url = "https://api.weatherxm.com/api/v1/me/devices"
        headers = {"Authorization": f"Bearer {access_token}"}

        session = async_get_clientsession(self.hass)
        response = await self.hass.async_add_executor_job(
            lambda: requests.get(url, headers=headers)
        )

        if response.status_code == 200:
            devices = response.json()
            stations = {station["name"]: station["id"] for station in devices if "name" in station and "id" in station}
            return stations
        else:
            raise ValueError(f"Failed to fetch stations: HTTP {response.status_code} - {response.text}")
