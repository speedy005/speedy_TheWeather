# 🌤️ speedy_TheWeather

**speedy_TheWeather** ist ein umfangreiches Wetter-Plugin für **Enigma2-Receiver**.

Das Plugin bietet aktuelle Wetterdaten, Mehrtagesvorhersagen, stündliche Prognosen, Sonnen- und Monddaten sowie ein integriertes animiertes Regenradar.

Das Projekt basiert auf der ursprünglichen Arbeit von **Caught** und wurde von **speedy005 / speedy006** weiterentwickelt, modernisiert und optimiert.

---

## ✨ Features

| Funktion                   | Beschreibung                                                |
| -------------------------- | ----------------------------------------------------------- |
| 🌤️ **Aktuelles Wetter**   | Detaillierte aktuelle Wetterdaten und 7-Tage-Vorhersage     |
| 🕐 **Stündliche Prognose** | Wetterdaten in 1h-, 2h- oder 3h-Intervallen                 |
| 🌡️ **Temperaturen**       | Höchst-, Tiefst- und gefühlte Temperatur                    |
| 💨 **Wind**                | Geschwindigkeit, Richtung und Beaufort-Skala                |
| 🌧️ **Niederschlag**       | Regenwahrscheinlichkeit und Niederschlagsmenge              |
| ☀️ **Sonne & UV**          | Sonnenaufgang, Sonnenuntergang und UV-Index                 |
| 🌙 **Mond**                | Mondphase, Beleuchtung, Mondaufgang und Monduntergang       |
| 🗺️ **Regenradar**         | Animiertes Radar auf Basis von RainViewer und OpenStreetMap |
| ⚠️ **Wetterwarnungen**     | Erkennung von Sturm, Starkregen, Hitze und Frost            |
| 📍 **Multi-Location**      | Beliebig viele Orte speichern und schnell wechseln          |
| 📺 **TV-Overlay**          | Aktuelle Temperatur optional direkt im laufenden TV-Bild    |
| 🎨 **Skinner-Support**     | Converter und Renderer für eigene Skins                     |
| ⚡ **Performance**          | 5-Minuten-Cache und asynchrone Radar-Downloads              |
| 🐍 **Python**              | Kompatibel mit Python 2 und Python 3                        |
| 🔄 **Auto-Update**         | Automatische Updateprüfung über GitHub                      |
| 🛠️ **Installer**          | Integrierter Konsolen-Installer                             |

---

## 📦 Schnellinstallation

Die Installation bzw. Aktualisierung kann direkt per **SSH / Telnet** auf dem Enigma2-Receiver erfolgen.

```bash
wget https://raw.githubusercontent.com/speedy005/speedy_TheWeather/master/installer.sh -O installer.sh
chmod +x installer.sh
sh installer.sh
```

> **Hinweis:** Der Installer übernimmt die Installation bzw. Aktualisierung des Plugins.

---

# 🎨 Converter & Skin-Integration

Das Plugin stellt den Converter

```text
conv_TheWeather
```

sowie den Renderer

```text
rend_TheWeatherPixmap
```

zur Verfügung.

Damit können Wetterdaten direkt in **InfoBars**, **SecondInfoBars** und **Custom Screens** von Enigma2-Skins verwendet werden.

---

## 🔧 Verfügbare Converter-Parameter

Die Parameter können mit einem Tagespräfix verwendet werden.

Beispiele:

```text
Day1,TemperatureMax
Day2,WeatherText
Day3,MoonPhase
```

### Parameterübersicht

| Kategorie         | Converter             | Beschreibung                      |
| ----------------- | --------------------- | --------------------------------- |
| **Allgemein**     | `City`                | Ausgewählter Ort                  |
| **Datum & Tag**   | `DayName`             | Wochentag                         |
|                   | `Date`                | Datum                             |
|                   | `Date_EU`             | Europäisch formatiertes Datum     |
|                   | `Date_EU_Short`       | Kurzes europäisches Datum         |
|                   | `Date_US`             | US-Datumsformat                   |
| **Temperatur**    | `TemperatureMax`      | Höchsttemperatur                  |
|                   | `TemperatureMin`      | Tiefsttemperatur                  |
| **Wind**          | `WindSpeed_KMH`       | Windgeschwindigkeit in km/h       |
|                   | `WindSpeed_MS`        | Windgeschwindigkeit in m/s        |
|                   | `WindSpeed_BFT`       | Windstärke nach Beaufort          |
|                   | `WindSpeed_MPH`       | Windgeschwindigkeit in mph        |
|                   | `WindDirection`       | Windrichtung                      |
|                   | `WindDirectionDegree` | Windrichtung in Grad              |
| **Niederschlag**  | `RainChance`          | Regenwahrscheinlichkeit in %      |
|                   | `RainAmount`          | Niederschlagsmenge in mm          |
| **Sonne & UV**    | `SunChance`           | Sonnenschein-Wahrscheinlichkeit   |
|                   | `Sunrise`             | Sonnenaufgang                     |
|                   | `Sunset`              | Sonnenuntergang                   |
|                   | `UVIndex`             | UV-Index                          |
| **Luft & Druck**  | `Humidity`            | Luftfeuchtigkeit in %             |
|                   | `Pressure`            | Luftdruck in hPa                  |
| **Mond**          | `MoonPhase`           | Berechnete Mondphase              |
|                   | `MoonIllumination`    | Mondbeleuchtung in %              |
|                   | `MoonRise`            | Mondaufgang                       |
|                   | `MoonSet`             | Monduntergang                     |
| **Grafik & Text** | `Icon`                | Wetter-Icon-Code für den Renderer |
|                   | `WeatherText`         | Wetterbeschreibung                |

---

# 🖥️ Skin-Integration

## 1. 5-Tage-Vorhersage

Beispiel für einen eigenen Wetter-Screen:

**Screen:** `TheWeather_5Days`

```xml
<screen
    name="TheWeather_5Days"
    position="center,center"
    size="1800,900"
    title="5-Tage Wettervorhersage"
    backgroundColor="#101010"
    flags="wfNoBorder">

    <!-- ========================================================= -->
    <!-- TAG 1 – HEUTE                                             -->
    <!-- ========================================================= -->

    <widget
        source="session.CurrentService"
        render="Label"
        position="50,40"
        size="300,40"
        font="Regular;30"
        halign="center"
        valign="center"
        foregroundColor="#ffffff"
        transparent="1">
        <convert type="conv_TheWeather">Day1,DayName</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="50,85"
        size="300,25"
        font="Regular;20"
        halign="center"
        valign="center"
        foregroundColor="#a0a0a0"
        transparent="1">
        <convert type="conv_TheWeather">Day1,Date_EU</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="rend_TheWeatherPixmap"
        position="140,125"
        size="120,120"
        alphatest="blend"
        transparent="1">
        <convert type="conv_TheWeather">Day1,Icon</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="50,255"
        size="300,30"
        font="Regular;22"
        halign="center"
        valign="center"
        foregroundColor="#00aaff"
        transparent="1">
        <convert type="conv_TheWeather">Day1,WeatherText</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="50,300"
        size="300,45"
        font="Regular;36"
        halign="center"
        valign="center"
        foregroundColor="#ff5555"
        transparent="1">
        <convert type="conv_TheWeather">Day1,TemperatureMax</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="50,350"
        size="300,30"
        font="Regular;24"
        halign="center"
        valign="center"
        foregroundColor="#55aaff"
        transparent="1">
        <convert type="conv_TheWeather">Day1,TemperatureMin</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="50,410"
        size="300,25"
        font="Regular;20"
        halign="center"
        transparent="1">
        <convert type="conv_TheWeather">Day1,WindSpeed_KMH</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="50,440"
        size="300,25"
        font="Regular;18"
        halign="center"
        foregroundColor="#a0a0a0"
        transparent="1">
        <convert type="conv_TheWeather">Day1,WindDirection</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="50,480"
        size="300,25"
        font="Regular;20"
        halign="center"
        transparent="1">
        <convert type="conv_TheWeather">Day1,RainChance</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="50,510"
        size="300,25"
        font="Regular;18"
        halign="center"
        foregroundColor="#a0a0a0"
        transparent="1">
        <convert type="conv_TheWeather">Day1,RainAmount</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="50,550"
        size="300,25"
        font="Regular;20"
        halign="center"
        transparent="1">
        <convert type="conv_TheWeather">Day1,SunChance</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="50,590"
        size="300,25"
        font="Regular;20"
        halign="center"
        transparent="1">
        <convert type="conv_TheWeather">Day1,Humidity</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="50,630"
        size="300,25"
        font="Regular;20"
        halign="center"
        transparent="1">
        <convert type="conv_TheWeather">Day1,Pressure</convert>
    </widget>

    <!-- ========================================================= -->
    <!-- TAG 2 – MORGEN                                            -->
    <!-- ========================================================= -->

    <widget
        source="session.CurrentService"
        render="Label"
        position="390,40"
        size="300,40"
        font="Regular;30"
        halign="center"
        valign="center"
        foregroundColor="#ffffff"
        transparent="1">
        <convert type="conv_TheWeather">Day2,DayName</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="390,85"
        size="300,25"
        font="Regular;20"
        halign="center"
        valign="center"
        foregroundColor="#a0a0a0"
        transparent="1">
        <convert type="conv_TheWeather">Day2,Date_EU</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="rend_TheWeatherPixmap"
        position="480,125"
        size="120,120"
        alphatest="blend"
        transparent="1">
        <convert type="conv_TheWeather">Day2,Icon</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="390,255"
        size="300,30"
        font="Regular;22"
        halign="center"
        valign="center"
        foregroundColor="#00aaff"
        transparent="1">
        <convert type="conv_TheWeather">Day2,WeatherText</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="390,300"
        size="300,45"
        font="Regular;36"
        halign="center"
        valign="center"
        foregroundColor="#ff5555"
        transparent="1">
        <convert type="conv_TheWeather">Day2,TemperatureMax</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="390,350"
        size="300,30"
        font="Regular;24"
        halign="center"
        valign="center"
        foregroundColor="#55aaff"
        transparent="1">
        <convert type="conv_TheWeather">Day2,TemperatureMin</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="390,410"
        size="300,25"
        font="Regular;20"
        halign="center"
        transparent="1">
        <convert type="conv_TheWeather">Day2,WindSpeed_KMH</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="390,440"
        size="300,25"
        font="Regular;18"
        halign="center"
        foregroundColor="#a0a0a0"
        transparent="1">
        <convert type="conv_TheWeather">Day2,WindDirection</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="390,480"
        size="300,25"
        font="Regular;20"
        halign="center"
        transparent="1">
        <convert type="conv_TheWeather">Day2,RainChance</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="390,510"
        size="300,25"
        font="Regular;18"
        halign="center"
        foregroundColor="#a0a0a0"
        transparent="1">
        <convert type="conv_TheWeather">Day2,RainAmount</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="390,550"
        size="300,25"
        font="Regular;20"
        halign="center"
        transparent="1">
        <convert type="conv_TheWeather">Day2,SunChance</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="390,590"
        size="300,25"
        font="Regular;20"
        halign="center"
        transparent="1">
        <convert type="conv_TheWeather">Day2,Humidity</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="390,630"
        size="300,25"
        font="Regular;20"
        halign="center"
        transparent="1">
        <convert type="conv_TheWeather">Day2,Pressure</convert>
    </widget>

    <!--
        TAG 3, TAG 4 und TAG 5 werden nach demselben Schema aufgebaut.

        Positionen:
        Day3 = X 730
        Day4 = X 1070
        Day5 = X 1410

        Die jeweiligen Converter werden entsprechend angepasst:
        Day3,...
        Day4,...
        Day5,...
    -->

</screen>
```

> **Hinweis:** Die fünf Tage verwenden dasselbe Widget-Schema. Die X-Positionen sind jeweils um **340 Pixel** versetzt.

---

# 🌙 2. InfoBar-Integration inklusive Monddaten

Beispiel für eine `InfoBar` mit Wetter-, Sonnen- und Monddaten.

**Screen:** `infobar_theweather`

```xml
<screen
    name="infobar_theweather"
    flags="wfNoBorder"
    position="0,0"
    backgroundColor="transparent">

    <!-- ========================================================= -->
    <!-- MOND-DATEN                                                -->
    <!-- ========================================================= -->

    <widget
        source="session.CurrentService"
        render="Label"
        position="483,765"
        size="250,30"
        font="Regular;20"
        halign="left"
        transparent="1">
        <convert type="conv_TheWeather">Day1,MoonPhase</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="689,705"
        size="100,30"
        font="Regular;20"
        halign="left"
        transparent="1">
        <convert type="conv_TheWeather">Day1,MoonIllumination</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="487,808"
        size="200,30"
        font="Regular;20"
        halign="left"
        transparent="1">
        <convert type="conv_TheWeather">Day1,MoonRise</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="485,706"
        size="200,30"
        font="Regular;20"
        halign="left"
        transparent="1">
        <convert type="conv_TheWeather">Day1,MoonSet</convert>
    </widget>

    <!-- ========================================================= -->
    <!-- WETTER-DETAILS                                            -->
    <!-- ========================================================= -->

    <widget
        source="session.CurrentService"
        render="Label"
        position="499,307"
        size="300,45"
        font="Regular;36"
        halign="center"
        valign="center"
        foregroundColor="#ff5555"
        transparent="1">
        <convert type="conv_TheWeather">City</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="497,355"
        size="300,45"
        font="Regular;36"
        halign="center"
        valign="center"
        foregroundColor="#ff5555"
        transparent="1">
        <convert type="conv_TheWeather">Day1,TemperatureMax</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="499,409"
        size="300,30"
        font="Regular;24"
        halign="center"
        valign="center"
        foregroundColor="#55aaff"
        transparent="1">
        <convert type="conv_TheWeather">Day1,TemperatureMin</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="rend_TheWeatherPixmap"
        position="825,312"
        size="120,120"
        alphatest="blend"
        transparent="1">
        <convert type="conv_TheWeather">Day1,Icon</convert>
    </widget>

    <!-- ========================================================= -->
    <!-- ALLGEMEINE WETTERDATEN                                    -->
    <!-- ========================================================= -->

    <widget
        source="session.CurrentService"
        render="Label"
        position="499,443"
        size="300,25"
        font="Regular;20"
        halign="center"
        transparent="1">
        <convert type="conv_TheWeather">Day1,WindSpeed_KMH</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="486,475"
        size="300,25"
        font="Regular;18"
        halign="center"
        foregroundColor="#a0a0a0"
        transparent="1">
        <convert type="conv_TheWeather">Day1,WindDirection</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="478,491"
        size="300,25"
        font="Regular;20"
        halign="center"
        transparent="1">
        <convert type="conv_TheWeather">Day1,RainChance</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="488,532"
        size="300,25"
        font="Regular;18"
        halign="center"
        foregroundColor="#a0a0a0"
        transparent="1">
        <convert type="conv_TheWeather">Day1,RainAmount</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="492,575"
        size="300,25"
        font="Regular;20"
        halign="center"
        transparent="1">
        <convert type="conv_TheWeather">Day1,SunChance</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="486,604"
        size="300,25"
        font="Regular;20"
        halign="center"
        transparent="1">
        <convert type="conv_TheWeather">Day1,Humidity</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="482,632"
        size="300,25"
        font="Regular;20"
        halign="center"
        transparent="1">
        <convert type="conv_TheWeather">Day1,Pressure</convert>
    </widget>

    <!-- ========================================================= -->
    <!-- DATUM & BESCHREIBUNG                                      -->
    <!-- ========================================================= -->

    <widget
        source="session.CurrentService"
        render="Label"
        position="802,489"
        size="200,30"
        font="Regular;22"
        halign="left"
        transparent="1">
        <convert type="conv_TheWeather">Day1,Date</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="1005,487"
        size="100,30"
        font="Regular;22"
        halign="left"
        transparent="1">
        <convert type="conv_TheWeather">Day1,DayName</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="798,528"
        size="300,30"
        font="Regular;22"
        halign="left"
        transparent="1">
        <convert type="conv_TheWeather">Day1,WeatherText</convert>
    </widget>

    <!-- ========================================================= -->
    <!-- SONNE                                                      -->
    <!-- ========================================================= -->

    <widget
        source="session.CurrentService"
        render="Label"
        position="818,757"
        size="200,30"
        font="Regular;20"
        halign="left"
        transparent="1">
        <convert type="conv_TheWeather">Day1,Sunrise</convert>
    </widget>

    <widget
        source="session.CurrentService"
        render="Label"
        position="855,801"
        size="200,30"
        font="Regular;20"
        halign="left"
        transparent="1">
        <convert type="conv_TheWeather">Day1,Sunset</convert>
    </widget>

</screen>
```

---

# ⚙️ Konfiguration & Pfade

Die Konfigurationsdateien und gespeicherten Favoritenorte befinden sich unter:

```text
/etc/enigma2/speedy_TheWeather/
```

---

# 📋 Anforderungen

* Enigma2-basierter Receiver
* OpenATV, OpenPLi, VTi oder vergleichbare Images
* Aktive Internetverbindung
* Python 2 **oder** Python 3
* Ausreichend freier Speicherplatz für Plugin und Wetterdaten

---

# 👨‍💻 Credits & Lizenz

**Originalautor**

* Caught

**Weiterentwicklung & Erweiterungen**

* speedy005
* speedy006

**Copyright**

```text
Copyright © Caught / speedy005
Alle Rechte vorbehalten.
```

---

# 🌍 English

## speedy_TheWeather

**speedy_TheWeather** is a feature-rich weather plugin for **Enigma2 receivers**.

It provides detailed current weather information, multi-day forecasts, hourly weather data, moon phase calculations, and an integrated animated rain radar.

The plugin is based on the original work by **Caught** and has been further developed, modernized, and optimized by **speedy005 / speedy006**.

---

## ✨ Features

| Feature                 | Description                                    |
| ----------------------- | ---------------------------------------------- |
| 🌤️ **Current Weather** | Detailed current weather information           |
| 📅 **Forecast**         | 7-day weather forecast                         |
| 🕐 **Hourly Forecast**  | 1h, 2h or 3h intervals                         |
| 🌡️ **Temperature**     | High, low and feels-like temperature           |
| 💨 **Wind**             | Speed, direction and Beaufort scale            |
| 🌧️ **Precipitation**   | Rain probability and precipitation amount      |
| ☀️ **Sun & UV**         | Sunrise, sunset and UV index                   |
| 🌙 **Moon Data**        | Moon phase, illumination, moonrise and moonset |
| 🗺️ **Rain Radar**      | Animated RainViewer radar with OpenStreetMap   |
| ⚠️ **Weather Alerts**   | Severe weather detection                       |
| 📍 **Multi-Location**   | Multiple saved locations                       |
| 📺 **TV Overlay**       | Optional temperature overlay                   |
| 🎨 **Skin Support**     | Custom converter and renderer                  |
| ⚡ **Caching**           | 5-minute weather cache                         |
| 🔄 **Auto Update**      | GitHub-based update system                     |

---

## 📦 Quick Installation

Run the following commands via SSH/Telnet:

```bash
wget https://raw.githubusercontent.com/speedy005/speedy_TheWeather/master/installer.sh -O installer.sh
chmod +x installer.sh
sh installer.sh
```

---

## 🔧 Converter Parameters

Use the converter with a day prefix:

```text
Day1,TemperatureMax
Day2,WeatherText
Day3,MoonPhase
```

| Category    | Converter                                     | Description                |
| ----------- | --------------------------------------------- | -------------------------- |
| General     | `City`                                        | Selected location          |
| Date        | `DayName`                                     | Day of the week            |
| Date        | `Date`, `Date_EU`, `Date_EU_Short`, `Date_US` | Formatted date             |
| Temperature | `TemperatureMax`                              | Maximum temperature        |
| Temperature | `TemperatureMin`                              | Minimum temperature        |
| Wind        | `WindSpeed_KMH`                               | Wind speed in km/h         |
| Wind        | `WindSpeed_MS`                                | Wind speed in m/s          |
| Wind        | `WindSpeed_BFT`                               | Beaufort scale             |
| Wind        | `WindSpeed_MPH`                               | Wind speed in mph          |
| Wind        | `WindDirection`                               | Wind direction             |
| Wind        | `WindDirectionDegree`                         | Direction in degrees       |
| Rain        | `RainChance`                                  | Rain probability (%)       |
| Rain        | `RainAmount`                                  | Precipitation amount (mm)  |
| Sun         | `SunChance`                                   | Sunshine probability       |
| Sun         | `Sunrise`                                     | Sunrise time               |
| Sun         | `Sunset`                                      | Sunset time                |
| UV          | `UVIndex`                                     | UV index                   |
| Air         | `Humidity`                                    | Relative humidity (%)      |
| Air         | `Pressure`                                    | Atmospheric pressure (hPa) |
| Moon        | `MoonPhase`                                   | Calculated moon phase      |
| Moon        | `MoonIllumination`                            | Moon illumination (%)      |
| Moon        | `MoonRise`                                    | Moonrise                   |
| Moon        | `MoonSet`                                     | Moonset                    |
| Graphics    | `Icon`                                        | Weather icon code          |
| Text        | `WeatherText`                                 | Weather description        |

---

## ⚙️ Configuration Path

```text
/etc/enigma2/speedy_TheWeather/
```

---

## 📋 Requirements

* Enigma2-based receiver
* OpenATV, OpenPLi, VTi or similar image
* Active internet connection
* Python 2 or Python 3

---

## 👨‍💻 Credits & License

**Original Author:** Caught

**Modifications & Enhancements:** speedy005 / speedy006

```text
Copyright © Caught / speedy005
All rights reserved.
```
