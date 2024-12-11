# WeatherXM Integration for Home Assistant

![Screenshot 2024-12-11 133447](https://github.com/user-attachments/assets/58edb966-8d9c-4bc7-ba33-ad7cf983aba2)

This is an UNOFFICIAL custom integration for integrating WeatherXM weather stations into Home Assistant. It is not supplied, maintained, or approved by WeatherXM.

It is based on the official, public API https://api.weatherxm.com/api/v1/docs

No warranty is provided. This integration is in Alpha. Use at your own risk.

<img width="620" alt="Screenshot 2024-12-10 at 00 13 51" src="https://github.com/user-attachments/assets/e2f2982e-1868-4e36-b688-f9037fda15ac">

## Features
- Retrieves weather data from WeatherXM stations.
- Automatically refreshes authentication tokens.
- Displays metrics like temperature, humidity, wind speed, and more.

## Installation via HACS
1. Open [HACS](https://hacs.xyz/) in your Home Assistant.
2. Go to **Integrations**.
3. Click the **+ Explore & Download Repositories** button.
4. Search for **WeatherXM** and install it.
5. Restart Home Assistant.
6. Add the integration via **Settings > Devices & Services > Add Integration** and search for "WeatherXM".

Alternatively, if the repository is not listed in HACS:
1. Open **HACS > Integrations > Custom Repositories**.
2. Add this repository URL: `https://github.com/old-square-eyes/homeassistant-weatherxm` as a custom repository.
3. Follow the steps above to install and configure.

## Configuration
- Enter your WeatherXM credentials and select your station during setup.

## Issues
Report any issues on [GitHub](https://github.com/old-square-eyes/homeassistant-weatherxm/issues).
