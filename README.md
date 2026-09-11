Markdown# speedy_TheWeather

**speedy_TheWeather** ist ein umfangreiches Wetter-Plugin für **Enigma2**-Receiver. Es liefert detaillierte aktuelle Wetterdaten, Mehrtages-Vorhersagen, stündliche Prognosen, Monddaten sowie ein integriertes Regenradar.

Das Plugin basiert auf der ursprünglichen Arbeit von **Caught** und wurde von **speedy005 / speedy006** weiterentwickelt und optimiert.

---

## Features

* **Aktuelles Wetter & Vorhersage:** 7-Tage-Wettervorhersage mit detaillierten Stundendaten (1h-, 2h- oder 3h-Intervalle).
* **Umfangreiche Parameter:** Höchst-/Tiefsttemperatur, gefühlte Temperatur, Windgeschwindigkeit, Windrichtung, Beaufort-Skala, Luftdruck, Luftfeuchtigkeit, UV-Index, Regenwahrscheinlichkeit und Niederschlagsmenge.
* **Sonne & Mond:** Sonnenaufgang, Sonnenuntergang sowie mathematisch berechnete **Mondphasen, Mondbeleuchtung, Mondaufgang und Monduntergang**.
* **Integriertes Regenradar:** Animarbares Regenradar basierend auf **RainViewer** mit **OpenStreetMap**-Kartenmaterial.
* **Wetterwarnungen:** Automatische Auswertung von Extremsituationen (Sturmböen, Starkregen, Hitze, extremer Frost).
* **Multi-Location:** Beliebig viele Orte speichern und schnell über die Ortssuche (Stadt + Ländercode) wechseln.
* **TV-Overlay:** Optionale Einblendung der aktuellen Temperatur während des laufenden TV-Programms.
* **Skinner-Support:** Eigener Converter (`conv_TheWeather`) und Renderer (`rend_TheWeatherPixmap`) für die freie Nutzung in InfoBars, SecondInfoBars und Custom Screens.
* **Performance & Stabilität:** 5-Minuten-Cache, asynchrone Radar-Downloads im Hintergrund und Kompatibilität mit Python 2 und Python 3.
* **Auto-Update:** Automatische Prüfung auf neue Versionen über GitHub inklusive Konsolen-Installer.

---

## Schnellinstallation (SSH / Telnet)

Führe folgenden Befehl auf deinem Enigma2-Receiver aus, um das Plugin zu installieren oder zu aktualisieren:

```bash
wget [https://raw.githubusercontent.com/speedy005/speedy_TheWeather/master/installer.sh](https://raw.githubusercontent.com/speedy005/speedy_TheWeather/master/installer.sh) -O installer.sh
chmod +x installer.sh
sh installer.sh
Verfügbare Converter-Parameter (conv_TheWeather)Für Skin-Entwickler stehen folgende Parameter zur Verfügung. Sie können mit einem Tag-Präfix genutzt werden (z. B. Day1,TemperatureMax oder Day2,WeatherText):KategorieConverter-TypBeschreibungAllgemeinCityName des ausgewählten OrtsDatum & TagDayName, Date, Date_EU, Date_EU_Short, Date_USWochentag oder formatiertes DatumTemperaturTemperatureMax, TemperatureMinMax-/Min-Temperatur in °CWindWindSpeed_KMH, WindSpeed_MS, WindSpeed_BFT, WindSpeed_MPH, WindDirection, WindDirectionDegreeWindwerte und -richtungenNiederschlagRainChance, RainAmountRegenwahrscheinlichkeit (%) und Menge (mm)Sonne & UVSunChance, Sunrise, Sunset, UVIndexSonnenschein-Chance, Zeiten und UV-WertLuft & DruckHumidity, PressureLuftfeuchtigkeit (%) und Luftdruck (hPa)MonddatenMoonPhase, MoonIllumination, MoonRise, MoonSetBerechnete Mondphase, Beleuchtung (%) und ZeitenGrafik/TextIcon, WeatherTextIcon-Code (für Renderer) und WetterbeschreibungSkin-Integration & XML-Widgets1. 5-Tage-Vorhersagescreen (TheWeather_5Days)XML<screen name="TheWeather_5Days" position="center,center" size="1800,900" title="5-Tage Wettervorhersage" backgroundColor="#101010" flags="wfNoBorder">

  <!-- ==================== TAG 1 (HEUTE) ==================== -->
  <widget source="session.CurrentService" render="Label" position="50,40" size="300,40" font="Regular;30" halign="center" valign="center" foregroundColor="#ffffff" transparent="1">
    <convert type="conv_TheWeather">Day1,DayName</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="50,85" size="300,25" font="Regular;20" halign="center" valign="center" foregroundColor="#a0a0a0" transparent="1">
    <convert type="conv_TheWeather">Day1,Date_EU</convert>
  </widget>
  <widget source="session.CurrentService" render="rend_TheWeatherPixmap" position="140,125" size="120,120" alphatest="blend" transparent="1">
    <convert type="conv_TheWeather">Day1,Icon</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="50,255" size="300,30" font="Regular;22" halign="center" valign="center" foregroundColor="#00aaff" transparent="1">
    <convert type="conv_TheWeather">Day1,WeatherText</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="50,300" size="300,45" font="Regular;36" halign="center" valign="center" foregroundColor="#ff5555" transparent="1">
    <convert type="conv_TheWeather">Day1,TemperatureMax</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="50,350" size="300,30" font="Regular;24" halign="center" valign="center" foregroundColor="#55aaff" transparent="1">
    <convert type="conv_TheWeather">Day1,TemperatureMin</convert>
  </widget>
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
2. InfoBar Integration inklusive Monddaten (infobar_theweather)XML<screen name="infobar_theweather" flags="wfNoBorder" position="0,0" backgroundColor="transparent">    
  <!-- Mond-Details -->
  <widget source="session.CurrentService" render="Label" position="483,765" size="250,30" font="Regular;20" halign="left" transparent="1">
    <convert type="conv_TheWeather">Day1,MoonPhase</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="689,705" size="100,30" font="Regular;20" halign="left" transparent="1">
    <convert type="conv_TheWeather">Day1,MoonIllumination</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="487,808" size="200,30" font="Regular;20" halign="left" transparent="1">
    <convert type="conv_TheWeather">Day1,MoonRise</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="485,706" size="200,30" font="Regular;20" halign="left" transparent="1">
    <convert type="conv_TheWeather">Day1,MoonSet</convert>
  </widget>

  <!-- Wetter-Details -->
  <widget source="session.CurrentService" render="Label" position="499,307" size="300,45" font="Regular;36" halign="center" valign="center" foregroundColor="#ff5555" transparent="1">
    <convert type="conv_TheWeather">City</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="497,355" size="300,45" font="Regular;36" halign="center" valign="center" foregroundColor="#ff5555" transparent="1">
    <convert type="conv_TheWeather">Day1,TemperatureMax</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="499,409" size="300,30" font="Regular;24" halign="center" valign="center" foregroundColor="#55aaff" transparent="1">
    <convert type="conv_TheWeather">Day1,TemperatureMin</convert>
  </widget>
  <widget source="session.CurrentService" render="rend_TheWeatherPixmap" position="825,312" size="120,120" alphatest="blend" transparent="1">
    <convert type="conv_TheWeather">Day1,Icon</convert>
  </widget>

  <!-- Allgemeine Wetterdaten -->
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

  <widget source="session.CurrentService" render="Label" position="802,489" size="200,30" font="Regular;22" halign="left" transparent="1">
    <convert type="conv_TheWeather">Day1,Date</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="1005,487" size="100,30" font="Regular;22" halign="left" transparent="1">
    <convert type="conv_TheWeather">Day1,DayName</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="798,528" size="300,30" font="Regular;22" halign="left" transparent="1">
    <convert type="conv_TheWeather">Day1,WeatherText</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="818,757" size="200,30" font="Regular;20" halign="left" transparent="1">
    <convert type="conv_TheWeather">Day1,Sunrise</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="855,801" size="200,30" font="Regular;20" halign="left" transparent="1">
    <convert type="conv_TheWeather">Day1,Sunset</convert>
  </widget>
</screen>
Konfiguration & PfadeDas Plugin speichert seine Konfigurationsdaten und Favoritenorte im folgenden Verzeichnis:Plaintext/etc/enigma2/speedy_TheWeather/
AnforderungenEnigma2-basierter Receiver (OpenATV, OpenPLi, VTi etc.)Aktive InternetverbindungPython 2 oder Python 3 UmgebungCredits & LizenzOriginal-Autor: CaughtModifikationen & Erweiterungen: speedy005 / speedy005Copyright © Caught / speedy005. Alle Rechte vorbehalten.
