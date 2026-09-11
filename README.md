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


for skinner
for all screens infobat secinfobar etc.


<screen name="TheWeather_5Days" position="center,center" size="1800,900" title="5-Tage Wettervorhersage" backgroundColor="#101010" flags="wfNoBorder">

<!-- ==================== TAG 1 (HEUTE) ==================== -->
<!-- Kopfzeile: Wochentag & Datum -->
<widget source="session.CurrentService" render="Label" position="50,40" size="300,40" font="Regular;30" halign="center" valign="center" foregroundColor="#ffffff" transparent="1">
<convert type="conv_TheWeather">Day1,DayName</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,85" size="300,25" font="Regular;20" halign="center" valign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day1,Date_EU</convert>
</widget>

<!-- Wetter-Icon -->
<widget source="session.CurrentService" render="rend_TheWeatherPixmap" position="140,125" size="120,120" alphatest="blend" transparent="1">
<convert type="conv_TheWeather">Day1,Icon</convert>
</widget>

<!-- Wettertext -->
<widget source="session.CurrentService" render="Label" position="50,255" size="300,30" font="Regular;22" halign="center" valign="center" foregroundColor="#00aaff" transparent="1">
<convert type="conv_TheWeather">Day1,WeatherText</convert>
</widget>

<!-- Temperaturen Max / Min -->
<widget source="session.CurrentService" render="Label" position="50,300" size="300,45" font="Regular;36" halign="center" valign="center" foregroundColor="#ff5555" transparent="1">
<convert type="conv_TheWeather">Day1,TemperatureMax</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,350" size="300,30" font="Regular;24" halign="center" valign="center" foregroundColor="#55aaff" transparent="1">
<convert type="conv_TheWeather">Day1,TemperatureMin</convert>
</widget>

<!-- Details: Wind, Niederschlag, Druck, UV -->
<widget source="session.CurrentService" render="Label" position="50,410" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day1,WindSpeed_KMH</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,440" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day1,WindDirection</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,480" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day1,RainChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,510" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day1,RainAmount</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,550" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day1,SunChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,590" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day1,Humidity</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,630" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day1,Pressure</convert>
</widget>


<!-- ==================== TAG 2 (MORGEN) ==================== -->
<widget source="session.CurrentService" render="Label" position="390,40" size="300,40" font="Regular;30" halign="center" valign="center" foregroundColor="#ffffff" transparent="1">
<convert type="conv_TheWeather">Day2,DayName</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,85" size="300,25" font="Regular;20" halign="center" valign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day2,Date_EU</convert>
</widget>
<widget source="session.CurrentService" render="rend_TheWeatherPixmap" position="480,125" size="120,120" alphatest="blend" transparent="1">
<convert type="conv_TheWeather">Day2,Icon</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,255" size="300,30" font="Regular;22" halign="center" valign="center" foregroundColor="#00aaff" transparent="1">
<convert type="conv_TheWeather">Day2,WeatherText</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,300" size="300,45" font="Regular;36" halign="center" valign="center" foregroundColor="#ff5555" transparent="1">
<convert type="conv_TheWeather">Day2,TemperatureMax</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,350" size="300,30" font="Regular;24" halign="center" valign="center" foregroundColor="#55aaff" transparent="1">
<convert type="conv_TheWeather">Day2,TemperatureMin</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,410" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day2,WindSpeed_KMH</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,440" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day2,WindDirection</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,480" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day2,RainChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,510" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day2,RainAmount</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,550" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day2,SunChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,590" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day2,Humidity</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,630" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day2,Pressure</convert>
</widget>


<!-- ==================== TAG 3 ==================== -->
<widget source="session.CurrentService" render="Label" position="730,40" size="300,40" font="Regular;30" halign="center" valign="center" foregroundColor="#ffffff" transparent="1">
<convert type="conv_TheWeather">Day3,DayName</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,85" size="300,25" font="Regular;20" halign="center" valign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day3,Date_EU</convert>
</widget>
<widget source="session.CurrentService" render="rend_TheWeatherPixmap" position="820,125" size="120,120" alphatest="blend" transparent="1">
<convert type="conv_TheWeather">Day3,Icon</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,255" size="300,30" font="Regular;22" halign="center" valign="center" foregroundColor="#00aaff" transparent="1">
<convert type="conv_TheWeather">Day3,WeatherText</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,300" size="300,45" font="Regular;36" halign="center" valign="center" foregroundColor="#ff5555" transparent="1">
<convert type="conv_TheWeather">Day3,TemperatureMax</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,350" size="300,30" font="Regular;24" halign="center" valign="center" foregroundColor="#55aaff" transparent="1">
<convert type="conv_TheWeather">Day3,TemperatureMin</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,410" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day3,WindSpeed_KMH</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,440" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day3,WindDirection</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,480" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day3,RainChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,510" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day3,RainAmount</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,550" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day3,SunChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,590" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day3,Humidity</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,630" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day3,Pressure</convert>
</widget>


<!-- ==================== TAG 4 ==================== -->
<widget source="session.CurrentService" render="Label" position="1070,40" size="300,40" font="Regular;30" halign="center" valign="center" foregroundColor="#ffffff" transparent="1">
<convert type="conv_TheWeather">Day4,DayName</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,85" size="300,25" font="Regular;20" halign="center" valign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day4,Date_EU</convert>
</widget>
<widget source="session.CurrentService" render="rend_TheWeatherPixmap" position="1160,125" size="120,120" alphatest="blend" transparent="1">
<convert type="conv_TheWeather">Day4,Icon</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,255" size="300,30" font="Regular;22" halign="center" valign="center" foregroundColor="#00aaff" transparent="1">
<convert type="conv_TheWeather">Day4,WeatherText</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,300" size="300,45" font="Regular;36" halign="center" valign="center" foregroundColor="#ff5555" transparent="1">
<convert type="conv_TheWeather">Day4,TemperatureMax</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,350" size="300,30" font="Regular;24" halign="center" valign="center" foregroundColor="#55aaff" transparent="1">
<convert type="conv_TheWeather">Day4,TemperatureMin</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,410" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day4,WindSpeed_KMH</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,440" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day4,WindDirection</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,480" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day4,RainChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,510" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day4,RainAmount</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,550" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day4,SunChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,590" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day4,Humidity</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,630" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day4,Pressure</convert>
</widget>


<!-- ==================== TAG 5 ==================== -->
<widget source="session.CurrentService" render="Label" position="1410,40" size="300,40" font="Regular;30" halign="center" valign="center" foregroundColor="#ffffff" transparent="1">
<convert type="conv_TheWeather">Day5,DayName</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,85" size="300,25" font="Regular;20" halign="center" valign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day5,Date_EU</convert>
</widget>
<widget source="session.CurrentService" render="rend_TheWeatherPixmap" position="1500,125" size="120,120" alphatest="blend" transparent="1">
<convert type="conv_TheWeather">Day5,Icon</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,255" size="300,30" font="Regular;22" halign="center" valign="center" foregroundColor="#00aaff" transparent="1">
<convert type="conv_TheWeather">Day5,WeatherText</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,300" size="300,45" font="Regular;36" halign="center" valign="center" foregroundColor="#ff5555" transparent="1">
<convert type="conv_TheWeather">Day5,TemperatureMax</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,350" size="300,30" font="Regular;24" halign="center" valign="center" foregroundColor="#55aaff" transparent="1">
<convert type="conv_TheWeather">Day5,TemperatureMin</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,410" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day5,WindSpeed_KMH</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,440" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day5,WindDirection</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,480" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day5,RainChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,510" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day5,RainAmount</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,550" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day5,SunChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,590" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day5,Humidity</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,630" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day5,Pressure</convert>
</widget>

</screen>



<screen name="infobar_theweather" flags="wfNoBorder" position="0,0" backgroundColor="transparent">    
<!-- Mondphase (z.B. Vollmond, Zunehmender Mond) -->
<widget source="session.CurrentService" render="Label" position="483,765" size="250,30" font="Regular;20" halign="left" transparent="1">
   <convert type="conv_TheWeather">Day1,MoonPhase</convert>
</widget>

<!-- Mondbeleuchtung in Prozent (z.B. 100%) -->
<widget source="session.CurrentService" render="Label" position="689,705" size="100,30" font="Regular;20" halign="left" transparent="1">
   <convert type="conv_TheWeather">Day1,MoonIllumination</convert>
</widget>

<!-- Mondaufgang -->
<widget source="session.CurrentService" render="Label" position="487,808" size="200,30" font="Regular;20" halign="left" transparent="1">
   <convert type="conv_TheWeather">Day1,MoonRise</convert>
</widget>

<!-- Monduntergang -->
<widget source="session.CurrentService" render="Label" position="485,706" size="200,30" font="Regular;20" halign="left" transparent="1">
   <convert type="conv_TheWeather">Day1,MoonSet</convert>
</widget>
<!-- KOPFZEILE: STADTNAME -->
   <widget source="session.CurrentService" render="Label" position="497,355" size="300,45" font="Regular;36" halign="center" valign="center" foregroundColor="#ff5555" transparent="1">
<convert type="conv_TheWeather">Day1,TemperatureMax</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="499,307" size="300,45" font="Regular;36" halign="center" valign="center" foregroundColor="#ff5555" transparent="1">
<convert type="conv_TheWeather">City</convert>
</widget>
<widget source="session.CurrentService" render="rend_TheWeatherPixmap" position="825,312" size="120,120" alphatest="blend" transparent="1">
<convert type="conv_TheWeather">Day1,Icon</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="499,409" size="300,30" font="Regular;24" halign="center" valign="center" foregroundColor="#55aaff" transparent="1">
<convert type="conv_TheWeather">Day1,TemperatureMin</convert>
</widget>

<!-- Details: Wind, Niederschlag, Druck, UV -->
<widget source="session.CurrentService" render="Label" position="499,443" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day1,WindSpeed_KMH</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="486,475" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day1,WindDirection</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="478,491" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day1,RainChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="488,532" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeather">Day1,RainAmount</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="492,575" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day1,SunChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="486,604" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day1,Humidity</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="482,632" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeather">Day1,Pressure</convert>
</widget>
<eLabel name="" position="489,301" size="650,550" zPosition="-20" />
<widget source="session.CurrentService" render="Label" position="810,442" size="300,40" font="Regular;28" halign="left" transparent="1">
   <convert type="conv_TheWeather">City</convert>
</widget>

<!-- Datum (z.B. 11.09.2026) -->
<widget source="session.CurrentService" render="Label" position="802,489" size="200,30" font="Regular;22" halign="left" transparent="1">
   <convert type="conv_TheWeather">Day1,Date</convert>
</widget>

<!-- Wochentag (z.B. Fr) -->
<widget source="session.CurrentService" render="Label" position="1005,487" size="100,30" font="Regular;22" halign="left" transparent="1">
   <convert type="conv_TheWeather">Day1,DayName</convert>
</widget>

<!-- Wetterbeschreibung (z.B. Leicht bewölkt) -->
<widget source="session.CurrentService" render="Label" position="798,528" size="300,30" font="Regular;22" halign="left" transparent="1">
   <convert type="conv_TheWeather">Day1,WeatherText</convert>
</widget>

<!-- Maximal-Temperatur -->
<widget source="session.CurrentService" render="Label" position="802,565" size="150,30" font="Regular;22" halign="left" transparent="1">
   <convert type="conv_TheWeather">Day1,TemperatureMax</convert>
</widget>

<!-- Minimal-Temperatur -->
<widget source="session.TheWeather" render="Label" position="967,564" size="150,30" font="Regular;22" halign="left" transparent="1">
   <convert type="conv_TheWeather">Day1,TemperatureMin</convert>
</widget>

<!-- Regenwahrscheinlichkeit -->
<widget source="session.CurrentService" render="Label" position="800,600" size="200,30" font="Regular;20" halign="left" transparent="1">
   <convert type="conv_TheWeather">Day1,RainChance</convert>
</widget>

<!-- Regenmenge -->
<widget source="session.CurrentService" render="Label" position="803,633" size="200,30" font="Regular;20" halign="left" transparent="1">
   <convert type="conv_TheWeather">Day1,RainAmount</convert>
</widget>

<!-- Windgeschwindigkeit (km/h) -->
<widget source="session.TheWeather" render="Label" position="789,666" size="200,30" font="Regular;20" halign="left" transparent="1">
   <convert type="conv_TheWeather">Day1,WindSpeed_KMH</convert>
</widget>

<!-- Windrichtung (z.B. SW) -->
<widget source="session.CurrentService" render="Label" position="818,707" size="150,30" font="Regular;20" halign="left" transparent="1">
   <convert type="conv_TheWeather">Day1,WindDirection</convert>
</widget>

<!-- Sonnenaufgang & Sonnenuntergang -->
<widget source="session.CurrentService" render="Label" position="818,757" size="200,30" font="Regular;20" halign="left" transparent="1">
   <convert type="conv_TheWeather">Day1,Sunrise</convert>
</widget>

<widget source="session.CurrentService" render="Label" position="855,801" size="200,30" font="Regular;20" halign="left" transparent="1">
   <convert type="conv_TheWeather">Day1,Sunset</convert>
</widget>

<!-- Wetter-Icon Code (für Pixmap-Renderer oder Icon-Packs) -->
<widget source="session.CurrentService" render="rend_TheWeatherPixmap" position="1013,642" size="120,120" font="Regular;20" halign="left" transparent="0">
   <convert type="conv_TheWeather">Day1,Icon</convert>
</widget>
</screen> 
