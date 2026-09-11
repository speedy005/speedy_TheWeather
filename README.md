# speedy_TheWeather

**speedy_TheWeather** is a weather plugin for **Enigma2** receivers. It provides detailed current weather information, multi-day forecasts, hourly weather data and an integrated rain radar.

The plugin is based on the original work by **Caught** and has been modified and improved by **speedy005 / speedy006**. The original author and modification credits remain in the source code.

## Features

* Current weather information
* 7-day weather forecast
* Detailed hourly forecast
* Temperature and "Feels Like" temperature
* Wind direction and wind speed
* Beaufort wind scale
* Sunrise and sunset information
* Precipitation and humidity information
* Weather condition icons
* Integrated rain radar
* Rain radar based on **RainViewer**
* OpenStreetMap map tiles for the radar map
* Multiple saved/favorite locations
* Easy location search by city and country code
* Automatic handling of city IDs
* Weather alerts for:

  * Strong wind
  * Heavy rain
  * Extreme heat
  * Severe/extreme cold
* Optional temperature overlay during TV viewing
* Configurable wind speed units
* Configurable date format
* Configurable radar zoom level
* Automatic weather-data caching
* Internet connectivity check
* Background processing for radar network requests
* Automatic plugin update check
* Automatic update installation through the Enigma2 console
* Translation support through `.po` / `.mo` language files
* Python 2 / Python 3 compatibility considerations

## Weather Data

Weather forecasts are retrieved from **Buienradar**.

The plugin supports both direct city-ID lookups and city searches. City names can also be combined with a country code to improve location selection. Weather data is cached for **5 minutes** to reduce unnecessary network requests.

## Rain Radar

The plugin includes an integrated animated rain radar.

Radar data is retrieved from **RainViewer**, while map tiles are provided by **OpenStreetMap**. Radar requests are processed in a background thread so that network activity does not unnecessarily block the Enigma2 user interface.

The radar supports configurable zoom levels and displays recent radar frames as an animation.

## Weather Alerts

The plugin automatically evaluates weather conditions and can display warnings for significant weather situations.

Examples include:

* **Strong wind**
* **Heavy storm**
* **Heavy rain**
* **Very heavy rain**
* **Warm weather**
* **Extreme heat**
* **Severe cold**
* **Extreme cold**

The alert system evaluates wind speed, precipitation and the perceived temperature and displays the highest-priority warning.

## Locations

Multiple locations can be saved and selected from the location list.

The location screen allows users to:

* Add a location
* Remove a location
* Select a saved location
* Open weather information
* Open the rain radar
* Access plugin settings

The plugin stores its configuration and saved locations under:

```text
/etc/enigma2/speedy_TheWeather/
```

## Forecast Display

The main forecast screen provides a visual overview of the selected location.

Depending on the screen resolution, the plugin provides an optimized HD or SD layout. The forecast includes daily information as well as detailed hourly data.

The hourly display can be switched between different intervals:

* 1-hour intervals
* 2-hour intervals
* 3-hour intervals

This makes it possible to show either a more detailed or a more compact hourly forecast.

## Temperature Overlay

The plugin can display the current temperature as an overlay while watching live TV.

The overlay is automatically controlled depending on the current Enigma2 screen and is hidden when other plugin or system screens are active.

## Settings

The plugin currently provides configuration options for:

### Wind Unit

Available units:

* `km/h`
* `m/s`

### Date Format

Available formats:

* `DD/MM/YYYY`
* `DD.MM.YYYY`

### Default Radar Zoom

The default radar zoom can be selected from:

```text
5
6
7
8
9
10
11
12
```

## Performance Improvements

Several improvements have been implemented to improve stability and responsiveness:

* Centralized HTTP requests
* Proper HTTP timeouts
* Proper response cleanup
* Five-minute weather-data cache
* Improved city and location search
* Better handling of special characters
* Internet connectivity checks
* Removed blocking one-second delays
* Validation of invalid hour values
* Corrected sunrise/sunset handling
* Radar downloads moved to a background thread
* Controlled processing of radar results on the Enigma2 main thread
* Proper radar timer cleanup when screens are closed

The existing functionality and user interface have been kept largely unchanged.

## Automatic Updates

`speedy_TheWeather` includes an integrated update mechanism.

When the plugin is opened, it checks the GitHub `master` branch for a newer version. The remote `plugin.py` is downloaded and its version is checked without executing the downloaded Python code.

If a newer version is available, the plugin displays:

* Installed version
* New version
* Changelog
* Installer version

The user can then choose whether to install the update.

The installer is downloaded from the same GitHub repository and executed through the Enigma2 Console. After a successful installation, the plugin informs the user that the update has been completed.

## Requirements

* Enigma2-based receiver
* Working Internet connection
* Python support compatible with the installed Enigma2 image
* Access to the required weather and radar services

## Version

Current plugin version:

```text
1.2.6
```

## Credits

Original work:

**Caught**

Modifications and improvements:

**speedy005 / speedy006**

The source code retains the original author and modification credits as required by the project.

## Disclaimer

Weather information is provided by external online services and may be unavailable or inaccurate depending on network connectivity and service availability.

The weather alerts shown by the plugin are informational only and should not be considered official emergency warnings.

## License / Copyright

Copyright © Caught. All rights reserved.

Modifications and improvements © speedy006.

This software is based on the original work of Caught.

Original author and modification credits must remain in the source code.


converter and renderer for skinner

for all screens infobar secinfobar etc.

mod by speedy005




wget https://raw.githubusercontent.com/speedy005/speedy_TheWeather/master/installer.sh -O installer.sh
chmod +x installer.sh
sh installer.sh
