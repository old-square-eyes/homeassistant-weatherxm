# WeatherXM Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://hacs.xyz/)

This is a custom integration for integrating WeatherXM weather stations into Home Assistant.

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
