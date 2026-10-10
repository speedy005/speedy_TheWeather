#-----------------------------------------------------------------------------
# v.2.0.1
# Original work by Caught
# https://www.linuxsat-support.com/cms/user/40812-caught/ 
# https://www.linuxsat-support.com/thread/163507-theweather-mod-by-speedy005-py-2-3/
# Modified by speedy005
# Copyright © Caught. All rights reserved.
# Modifications and improvements © speedy005.
# This software is based on the original work of Caught.
# Original author and modification credits must remain in the source code.
# -----------------------------------------------------------------------------

import os
import time
import json
import math
import shutil
import gettext
import datetime
import threading
import tempfile
import subprocess
import ast
from collections import deque, OrderedDict
try:
    from concurrent.futures import ThreadPoolExecutor, as_completed
except ImportError:
    ThreadPoolExecutor = None
    as_completed = None
try:
    import Queue as queue
except ImportError:
    import queue
from enigma import gRGB
from Screens.Console import Console
from enigma import eTimer
from enigma import ePoint
from Screens.Screen import Screen
from Components.Label import Label
from time import strftime, localtime
from Components.config import (
    config,
    ConfigSelection,
    ConfigYesNo,
    configfile,
    ConfigSubsection,
    getConfigListEntry
)
from Screens.ChoiceBox import ChoiceBox
from enigma import ePicLoad, getDesktop
from Components.MenuList import MenuList
from Components.Language import language
from Screens.MessageBox import MessageBox
from Screens.InfoBar import InfoBar
from Plugins.Plugin import PluginDescriptor
from datetime import datetime as dt_datetime
from datetime import timedelta, date, time
from Components.Pixmap import Pixmap, MovingPixmap
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.Sources.StaticText import StaticText
from Components.Converter.ClockToText import ClockToText
from Components.MultiContent import MultiContentEntryText
from Components.ActionMap import ActionMap, HelpableActionMap
from Tools.Directories import resolveFilename, SCOPE_CONFIG, SCOPE_PLUGINS, SCOPE_LANGUAGE
from enigma import eListboxPythonMultiContent, loadPNG, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER
from Components.ConfigList import ConfigListScreen
PluginLanguageDomain = "speedy_TheWeather"
PluginLanguagePath = os.path.join(resolveFilename(SCOPE_PLUGINS), "Extensions", "speedy_TheWeather", "locale")

def localeInit():
    lang = language.getLanguage()[:2]
    os.environ["LANGUAGE"] = lang
    gettext.bindtextdomain(PluginLanguageDomain, PluginLanguagePath)

localeInit()
language.addCallback(localeInit)

_translation_cache = {}
_translation_cache_lang = None

def _(txt):
    """Fast translation helper; cache the gettext catalog per language."""
    global _translation_cache_lang
    if not txt:
        return ""
    try:
        lang = language.getLanguage()[:2]
        translation = _translation_cache.get(lang)
        if translation is None:
            translation = gettext.translation(
                PluginLanguageDomain,
                PluginLanguagePath,
                languages=[lang],
                fallback=True
            )
            _translation_cache[lang] = translation
        _translation_cache_lang = lang
        return translation.gettext(txt)
    except Exception:
        return txt

OAWeather = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('OAWeather'))

# 1. Konfigurations-Variablen definieren
config.plugins.speedy_TheWeather = ConfigSubsection()
config.plugins.speedy_TheWeather.windunit = ConfigSelection(
    default="kmh",
    choices=[("kmh", _("km/h")), ("ms", _("m/s"))]
)
config.plugins.speedy_TheWeather.dateformat = ConfigSelection(
    default="slash",
    choices=[("slash", _("DD/MM/YYYY")), ("dot", _("DD.MM.YYYY"))]
)
config.plugins.speedy_TheWeather.performance = ConfigSelection(
    default="auto",
    choices=[
        ("auto", _("Auto")),
        ("ultra", _("Ultra Low-End")),
        ("low", _("Low-End")),
        ("normal", _("Normal"))
    ]
)

config.plugins.speedy_TheWeather.autoBackgrounds = ConfigYesNo(
    default=True
)

config.plugins.speedy_TheWeather.holidayBackgrounds = ConfigYesNo(
    default=True
)
# ---------------------------------------------------------------------------
# SevenDay Farbpalette
# ---------------------------------------------------------------------------
# Enigma2 nutzt hier 8-stellige ARGB-Werte. Die Palette ist bewusst als
# ConfigSelection aufgebaut: kein externer ColorPicker, keine Zusatz-Plugins
# und damit auch auf schwachen Boxen sehr leichtgewichtig.
SEVENDAY_COLOR_CHOICES = [
    # =========================
    # ORIGINAL-FARBEN (51)
    # =========================
    ("#00ff0000", _("Rot")),
    ("#0000ff00", _("Grün")),
    ("#000000ff", _("Blau")),
    ("#00ffff00", _("Gelb")),
    ("#0000ffff", _("Cyan")),
    ("#00ff00ff", _("Magenta")),
    ("#00ffffff", _("Weiß")),
    ("#00000000", _("Schwarz")),
    ("#00ff8000", _("Orange")),
    ("#00ff4000", _("Dunkelorange")),
    ("#00ffc000", _("Gold")),
    ("#00ffd700", _("Goldgelb")),
    ("#00808000", _("Oliv")),
    ("#0080ff00", _("Limette")),
    ("#0000ff80", _("Türkisgrün")),
    ("#00008080", _("Petrol")),
    ("#004080ff", _("Mittelblau")),
    ("#000080ff", _("Himmelblau")),
    ("#000040ff", _("Tiefblau")),
    ("#004000ff", _("Violettblau")),
    ("#008000ff", _("Violett")),
    ("#00c000ff", _("Pinkviolett")),
    ("#00ff0080", _("Pink")),
    ("#00ff4080", _("Hellpink")),
    ("#00ff80c0", _("Rosa")),
    ("#00ff8080", _("Hellrot")),
    ("#00ff4040", _("Korallenrot")),
    ("#00c00000", _("Dunkelrot")),
    ("#00800000", _("Weinrot")),
    ("#00804000", _("Braun")),
    ("#00c08040", _("Hellbraun")),
    ("#00e0c080", _("Beige")),
    ("#00ffe0c0", _("Creme")),
    ("#0080ff80", _("Hellgrün")),
    ("#0040c040", _("Mittelgrün")),
    ("#00008000", _("Dunkelgrün")),
    ("#00004000", _("Sehr dunkelgrün")),
    ("#00c0ff80", _("Gelbgrün")),
    ("#0080c000", _("Grasgrün")),
    ("#0080ffff", _("Hellcyan")),
    ("#0040c0ff", _("Hellblau")),
    ("#0080c0ff", _("Pastellblau")),
    ("#00004080", _("Dunkelblau")),
    ("#00002040", _("Marineblau")),
    ("#00c080ff", _("Hellviolett")),
    ("#008040c0", _("Mittelviolett")),
    ("#00400080", _("Dunkelviolett")),
    ("#00808080", _("Grau")),
    ("#00c0c0c0", _("Hellgrau")),
    ("#00404040", _("Dunkelgrau")),
    ("#00e0e0e0", _("Sehr hellgrau")),

    # =========================
    # NEUE FARBEN (49)
    # =========================

    # Rot / Pink
    ("#00e02020", _("Kirschrot")),
    ("#00e04040", _("Rubinrot")),
    ("#00a00020", _("Bordeaux")),
    ("#00c02040", _("Himbeerrot")),
    ("#00ff2060", _("Neonpink")),
    ("#00e02080", _("Fuchsia")),
    ("#00c04080", _("Beerenton")),
    ("#00ff60a0", _("Candy Pink")),

    # Orange / Gelb
    ("#00e06020", _("Mandarine")),
    ("#00ff6020", _("Aprikose")),
    ("#00e08040", _("Pfirsich")),
    ("#00e0a020", _("Bernstein")),
    ("#00ffc040", _("Safran")),
    ("#00ffe040", _("Zitronengelb")),
    ("#00e0c040", _("Honig")),
    ("#00ffb020", _("Neonorange")),

    # Grün
    ("#0040a040", _("Waldgrün")),
    ("#0060a040", _("Smaragdgrün")),
    ("#0020c080", _("Jadegrün")),
    ("#00408040", _("Tannengrün")),
    ("#00a0c060", _("Mintgrün")),
    ("#0060e080", _("Mint")),
    ("#0020ff40", _("Neongrün")),
    ("#0080e040", _("Apfelgrün")),

    # Cyan / Türkis
    ("#0040c0c0", _("Teal")),
    ("#0060d0d0", _("Aquamarin")),
    ("#0020e0e0", _("Neoncyan")),
    ("#00a0e0c0", _("Meeresgrün")),
    ("#0060a0a0", _("Lagune")),

    # Blau
    ("#0040a0ff", _("Kobaltblau")),
    ("#0000a0ff", _("Royalblau")),
    ("#0020e0ff", _("Electric Blue")),
    ("#0060ffff", _("Neonblau")),
    ("#0080e0ff", _("Azure")),
    ("#0060a0ff", _("Saphirblau")),
    ("#002080ff", _("Ozeanblau")),
    ("#00206080", _("Nachtblau")),

    # Violett / Lila
    ("#006020ff", _("Indigo")),
    ("#006040ff", _("Deep Purple")),
    ("#00a020ff", _("Royal Purple")),
    ("#00c040ff", _("Amethyst")),
    ("#00a060ff", _("Lavendel")),
    ("#00d080ff", _("Flieder")),
    ("#00e020ff", _("Neonviolett")),
    ("#008060ff", _("Pflaume")),

    # Braun / Metallic / besondere Farben
    ("#00a06020", _("Karamell")),
    ("#00c06020", _("Terrakotta")),
    ("#00a08040", _("Bronze")),
   
	# =========================
	# 20 WEITERE COOLE FARBEN
	# =========================

	("##00ff1493", _("Cyber Pink")),
	("##00b026ff", _("Galaxy Purple")),
	("##005c00ff", _("Cosmic Violet")),
	("##0000d9ff", _("Deep Electric Blue")),
	("##0000f5ff", _("Laser Blue")),
	("##0000ffc0", _("Holographic Cyan")),
	("##00ff00c0", _("Neon Cyan")),
	("##00b0ff40", _("Toxic Mint")),
	("##0020ff80", _("Acid Green")),
	("##00c0ff20", _("Lime Neon")),
	("##00ff6000", _("Solar Orange")),
	("##00ff2060", _("Sunset Pink")),
	("##00ff4060", _("Hot Coral")),
	("##00ff80e0", _("Bubblegum")),
	("##00e060e0", _("Candy Purple")),
	("##00a020e0", _("Electric Violet")),
	("##0040e0a0", _("Emerald Glow")),
	("##00e0a040", _("Golden Amber")),
	("##00c080ff", _("Mystic Lavender")),
	("##0040ffff", _("Arctic Blue")),
]



_SEVENDAY_COLOR_DEFAULTS = {
    "city": "#0000ff00",
    "bigtemp": "#000000ff",
    "weathertype": "#00ff0000",
    "feels": "#00ffff00",
    "wind": "#0000ffff",
    "day": "#0000ff00",
    "maxtemp": "#00ff0000",
    "mintemp": "#00004080",
    "daytype": "#00ffff00",
    "sun": "#00ffff00",
    "sunrise": "#0000ff00",
    "sunset": "#00ff0000",
    "moonrise": "#0000ff00",
    "moonset": "#00ff0000",
    "hour": "#00ff0000",
    "hourtemp": "#004080ff",
    "rain": "#0000ff00",
    "sunpercent": "#00ffff00",
    "humidity": "#004080ff",
    "windspeed": "#0000ffff",
    "clock": "#00ff0000",
    "date": "#0000ff00",
    "alert": "#00ffff00",
}

_TWOLOCATIONS_COLOR_DEFAULTS = {
    "weathertype": "#0000ffff",  # Cyan
    "feels":       "#0080c0ff",  # Hellblau
    "wind":        "#00ffa500",  # Orange
    "rain":        "#004080ff",  # Blau
    "sun":         "#00ffff00",  # Gelb
    "moon":        "#00ffd27f",  # Mondgold
}

# Two-Locations: jeder Standort besitzt seine eigene Farbpalette.
_TWOLocations_LEGACY_COLOR_DEFAULTS = dict(_TWOLOCATIONS_COLOR_DEFAULTS)

for _sd_color_name, _sd_color_default in _SEVENDAY_COLOR_DEFAULTS.items():
    setattr(
        config.plugins.speedy_TheWeather,
        "sevenday_color_" + _sd_color_name,
        ConfigSelection(
            default=_sd_color_default,
            choices=SEVENDAY_COLOR_CHOICES
        )
    )
# Neue getrennte Farben für Standort 1 und Standort 2.
for _tl_location in ("loc1", "loc2"):
    for _tl_color_name, _tl_color_default in _TWOLOCATIONS_COLOR_DEFAULTS.items():
        setattr(
            config.plugins.speedy_TheWeather,
            "twoloc_%s_color_%s" % (_tl_location, _tl_color_name),
            ConfigSelection(
                default=_tl_color_default,
                choices=SEVENDAY_COLOR_CHOICES
            )
        )

# Legacy-Werte bleiben für die Migration alter Einstellungen erhalten.
for _tl_color_name, _tl_color_default in _TWOLocations_LEGACY_COLOR_DEFAULTS.items():
    setattr(
        config.plugins.speedy_TheWeather,
        "twoloc_color_" + _tl_color_name,
        ConfigSelection(
            default=_tl_color_default,
            choices=SEVENDAY_COLOR_CHOICES
        )
    )

del _tl_location, _tl_color_name, _tl_color_default
del _sd_color_name, _sd_color_default

config.plugins.speedy_TheWeather.defaultzoom = ConfigSelection(
    default="7",
    choices=[
        ("5", "5"),
        ("6", "6"),
        ("7", "7"),
        ("8", "8"),
        ("9", "9"),
        ("10", "10"),
        ("11", "11"),
        ("12", "12"),
    ]
)

# add speedy005
PY3 = False

import sys
if sys.version_info[0] >= 3:
    PY3 = True
    unicode = str
    unichr = chr
    long = int
    from urllib.error import HTTPError, URLError
    from urllib.request import urlopen, Request
    from urllib.parse import quote_plus
    import urllib.request as urllib2
    import http.cookiejar as cookielib
else:
    from urllib2 import HTTPError, URLError, urlopen, Request
    from urllib import quote_plus
    import urllib2
    import cookielib
# add speedy005 end

def safeStr(value):
    if value is None:
        return ""
    if not PY3 and isinstance(value, unicode):
        return value.encode("utf-8")
    return str(value)

def stripCoords(value):
    return safeStr(value).split("|", 1)[0]

# Manual regression-test location. This is intentionally not auto-added to
# SavedLokaleWeer; it can be used as a saved entry for display testing.
TEST_MCMURDO_ENTRY = "McMurdo Station-6696480|-77.84632|166.66824"

# =============================================================================
# KOORDINATEN AUS EINEM EINTRAG LESEN
# =============================================================================

def getCoordsFromEntry(value):
    """
    Erwartet z.B.:

        Deutschland|51.4344|6.7623

    Rueckgabe:

        (latitude, longitude)

    Bei Fehler:

        (None, None)
    """
    try:
        parts = safeStr(value).split("|")

        if len(parts) != 3:
            return None, None

        lat = float(parts[1].strip())
        lon = float(parts[2].strip())

        # Plausibilitaetspruefung
        if lat < -90.0 or lat > 90.0:
            return None, None

        if lon < -180.0 or lon > 180.0:
            return None, None

        return lat, lon

    except Exception as e:
        print("[Moon] getCoordsFromEntry Fehler: %s" % str(e))
        return None, None


# =============================================================================
# MONDAUF- / MONDUNTERGANG
# =============================================================================
#
# Die Berechnung erfolgt komplett lokal.
# Kein Netzwerkzugriff erforderlich.
#
# Rueckgabe:
#
#     ("HH:MM", "HH:MM")
#
# Beispiel:
#
#     ("07:42", "19:13")
#
# Wenn der Mond an diesem Tag nicht auf- bzw. untergeht:
#
#     ("na", "19:13")
#
# =============================================================================

_MOON_RISESET_CACHE = {}


def _moon_julian_day(dt):
    """
    Julianischer Tag fuer eine UTC-Datetime.
    """

    return (
        (dt - datetime.datetime(2000, 1, 1, 12, 0, 0)).total_seconds()
        / 86400.0
        + 2451545.0
    )


def _moon_position(jd):
    """
    Niedrigaufloesende geozentrische Mondposition.

    Rueckgabe:
        longitude, latitude, distance
    """

    d = jd - 2451543.5

    N = math.radians(
        (125.1228 - 0.0529538083 * d) % 360.0
    )

    i = math.radians(5.1454)

    w = math.radians(
        (318.0634 + 0.1643573223 * d) % 360.0
    )

    a = 60.2666
    e = 0.0549

    M = math.radians(
        (115.3654 + 13.0649929509 * d) % 360.0
    )

    # -------------------------------------------------------------------------
    # Exzentrische Anomalie
    # -------------------------------------------------------------------------

    E = M + e * math.sin(M) * (
        1.0 + e * math.cos(M)
    )

    for _ in range(5):
        denominator = 1.0 - e * math.cos(E)

        if abs(denominator) < 0.000001:
            break

        E -= (
            E - e * math.sin(E) - M
        ) / denominator

    # -------------------------------------------------------------------------
    # Position in der Bahnebene
    # -------------------------------------------------------------------------

    xv = a * (
        math.cos(E) - e
    )

    yv = a * (
        math.sqrt(1.0 - e * e)
        * math.sin(E)
    )

    v = math.atan2(yv, xv)

    r = math.sqrt(
        xv * xv + yv * yv
    )

    # -------------------------------------------------------------------------
    # Ekliptische Koordinaten
    # -------------------------------------------------------------------------

    xh = r * (
        math.cos(N) * math.cos(v + w)
        -
        math.sin(N) * math.sin(v + w) * math.cos(i)
    )

    yh = r * (
        math.sin(N) * math.cos(v + w)
        +
        math.cos(N) * math.sin(v + w) * math.cos(i)
    )

    zh = r * (
        math.sin(v + w)
        * math.sin(i)
    )

    lon = math.atan2(
        yh,
        xh
    )

    lat = math.atan2(
        zh,
        math.sqrt(
            xh * xh + yh * yh
        )
    )

    # -------------------------------------------------------------------------
    # Stoerungen fuer die sichtbare Mondposition
    # -------------------------------------------------------------------------

    Ms = math.radians(
        (356.0470 + 0.9856002585 * d) % 360.0
    )

    ws = math.radians(
        (282.9404 + 0.0000470935 * d) % 360.0
    )

    Ls = (
        Ms + ws
    ) % (2.0 * math.pi)

    Mm = M

    Lm = (
        math.degrees(N + w + M)
    ) % 360.0

    Ls_deg = math.degrees(Ls)

    D = math.radians(
        (Lm - Ls_deg) % 360.0
    )

    F = math.radians(
        (Lm - math.degrees(N)) % 360.0
    )

    # -------------------------------------------------------------------------
    # Laengengrad-Stoerungen
    # -------------------------------------------------------------------------

    lon += math.radians(
        -1.274 * math.sin(Mm - D)
        + 0.658 * math.sin(2.0 * D)
        - 0.186 * math.sin(Ms)
        - 0.059 * math.sin(2.0 * Mm - 2.0 * D)
        - 0.057 * math.sin(Mm - 2.0 * D + Ms)
        + 0.053 * math.sin(Mm + 2.0 * D)
        + 0.046 * math.sin(2.0 * D - Ms)
        + 0.041 * math.sin(Mm - Ms)
        - 0.035 * math.sin(D)
        - 0.031 * math.sin(Mm + Ms)
        - 0.015 * math.sin(2.0 * F - 2.0 * D)
        + 0.011 * math.sin(Mm - 4.0 * D)
    )

    # -------------------------------------------------------------------------
    # Breitengrad-Stoerungen
    # -------------------------------------------------------------------------

    lat += math.radians(
        -0.173 * math.sin(F - 2.0 * D)
        -0.055 * math.sin(Mm - F - 2.0 * D)
        -0.046 * math.sin(Mm + F - 2.0 * D)
        +0.033 * math.sin(F + 2.0 * D)
        +0.017 * math.sin(2.0 * Mm + F)
    )

    return lon, lat, r


def _moon_altitude(dt_utc, lat_deg, lon_deg):
    """
    Mondhoehe ueber dem Horizont in Grad.

    dt_utc muss UTC sein.
    """

    try:
        jd = _moon_julian_day(dt_utc)

        moon_lon, moon_lat, _moon_distance = _moon_position(jd)

        # -------------------------------------------------------------
        # Ekliptik -> Aequator
        # -------------------------------------------------------------

        obliq = math.radians(
            23.4393
            - 3.563e-7 * (jd - 2451543.5)
        )

        sin_dec = (
            math.sin(moon_lat) * math.cos(obliq)
            +
            math.cos(moon_lat)
            * math.sin(obliq)
            * math.sin(moon_lon)
        )

        sin_dec = max(-1.0, min(1.0, sin_dec))

        dec = math.asin(sin_dec)

        # Rektaszension
        y = (
            math.sin(moon_lon) * math.cos(obliq)
            -
            math.tan(moon_lat) * math.sin(obliq)
        )

        x = math.cos(moon_lon)

        ra = math.atan2(y, x)

        # -------------------------------------------------------------
        # GMST
        # -------------------------------------------------------------

        T = (
            jd - 2451545.0
        ) / 36525.0

        gmst = (
            280.46061837
            +
            360.98564736629
            * (jd - 2451545.0)
            +
            0.000387933 * T * T
            -
            T * T * T / 38710000.0
        ) % 360.0

        # -------------------------------------------------------------
        # Lokale Sternzeit
        # -------------------------------------------------------------

        lst = math.radians(
            (gmst + float(lon_deg)) % 360.0
        )

        hour_angle = lst - ra

        # -------------------------------------------------------------
        # Horizontkoordinaten
        # -------------------------------------------------------------

        lat_rad = math.radians(
            float(lat_deg)
        )

        sin_alt = (
            math.sin(lat_rad)
            * math.sin(dec)
            +
            math.cos(lat_rad)
            * math.cos(dec)
            * math.cos(hour_angle)
        )

        sin_alt = max(-1.0, min(1.0, sin_alt))

        return math.degrees(
            math.asin(sin_alt)
        )

    except Exception as e:

        print(
            "[Moon] FEHLER _moon_altitude: %s"
            % str(e)
        )

        return -90.0


def _moon_rise_set_for_date(
        date_value,
        lat_deg,
        lon_deg
):
    """
    Berechnet Mondaufgang und Monduntergang
    fuer einen lokalen Kalendertag.

    Rueckgabe:

        ("HH:MM", "HH:MM")

    Wenn kein Auf- oder Untergang stattfindet:

        ("na", "HH:MM")
        oder
        ("HH:MM", "na")
    """

    try:

        # ========================================================
        # KOORDINATEN
        # ========================================================

        lat_deg = float(lat_deg)
        lon_deg = float(lon_deg)

        if lat_deg < -90.0 or lat_deg > 90.0:

            print(
                "[Moon] Ungueltige Latitude: %s"
                % str(lat_deg)
            )

            return "na", "na"

        if lon_deg < -180.0 or lon_deg > 180.0:

            print(
                "[Moon] Ungueltige Longitude: %s"
                % str(lon_deg)
            )

            return "na", "na"

        # ========================================================
        # DATUM
        # ========================================================

        if not isinstance(
            date_value,
            datetime.date
        ):

            print(
                "[Moon] Ungueltiges Datum: %s"
                % str(date_value)
            )

            return "na", "na"

        # ========================================================
        # CACHE
        # ========================================================

        key = (
            date_value.isoformat(),
            round(lat_deg, 4),
            round(lon_deg, 4)
        )

        if key in _MOON_RISESET_CACHE:

            cached = _MOON_RISESET_CACHE[key]

            print(
                "[Moon] Cache: %s | rise=%s | set=%s"
                % (
                    date_value.isoformat(),
                    cached[0],
                    cached[1]
                )
            )

            return cached

        # ========================================================
        # LOKALE MITTERNACHT
        # ========================================================

        local_midnight = datetime.datetime.combine(
            date_value,
            datetime.time(
                0,
                0,
                0
            )
        )

        # ========================================================
        # ZEITVERSATZ LOKAL -> UTC
        # ========================================================

        timestamp = time.mktime(
            local_midnight.timetuple()
        )

        local_tm = time.localtime(
            timestamp
        )

        if hasattr(
            local_tm,
            "tm_gmtoff"
        ):

            offset_seconds = (
                local_tm.tm_gmtoff
            )

        else:

            utc_tm = time.gmtime(
                timestamp
            )

            local_as_timestamp = (
                time.mktime(
                    (
                        local_tm.tm_year,
                        local_tm.tm_mon,
                        local_tm.tm_mday,
                        local_tm.tm_hour,
                        local_tm.tm_min,
                        local_tm.tm_sec,
                        0,
                        0,
                        -1
                    )
                )
            )

            utc_as_timestamp = (
                time.mktime(
                    (
                        utc_tm.tm_year,
                        utc_tm.tm_mon,
                        utc_tm.tm_mday,
                        utc_tm.tm_hour,
                        utc_tm.tm_min,
                        utc_tm.tm_sec,
                        0,
                        0,
                        -1
                    )
                )
            )

            offset_seconds = (
                local_as_timestamp
                - utc_as_timestamp
            )

        print(
            "[Moon] Datum=%s | Offset=%s Sekunden"
            % (
                date_value.isoformat(),
                str(offset_seconds)
            )
        )

        # ========================================================
        # LOKALE MINUTEN -> UTC
        # ========================================================

        def utc_for_local_minutes(
                minutes
        ):

            return (
                local_midnight
                + datetime.timedelta(
                    minutes=float(minutes)
                )
                - datetime.timedelta(
                    seconds=float(offset_seconds)
                )
            )

        # ========================================================
        # HORIZONTHOEHE
        #
        # -0.27 Grad ist ein sinnvoller praktischer
        # Horizontwert fuer den Mond.
        # ========================================================

        threshold = -0.27

        rise = None
        moonset = None

        # ========================================================
        # START 00:00
        # ========================================================

        previous_altitude = _moon_altitude(
            utc_for_local_minutes(0),
            lat_deg,
            lon_deg
        )

        print(
            "[Moon DEBUG] %s | 00:00 | altitude=%.3f"
            % (
                date_value.isoformat(),
                previous_altitude
            )
        )

        # ========================================================
        # ALLE 5 MINUTEN
        # ========================================================

        for minute in range(
            5,
            1441,
            5
        ):

            current_altitude = _moon_altitude(
                utc_for_local_minutes(minute),
                lat_deg,
                lon_deg
            )

            # ----------------------------------------------------
            # DEBUG JEDE VOLLE STUNDE
            # ----------------------------------------------------

            if minute % 60 == 0:

                print(
                    "[Moon DEBUG] %02d:%02d | altitude=%.3f"
                    % (
                        minute // 60,
                        minute % 60,
                        current_altitude
                    )
                )

            # ====================================================
            # MONDAUFGANG
            # ====================================================

            if (
                rise is None
                and
                previous_altitude < threshold
                and
                current_altitude >= threshold
            ):

                lo = float(
                    minute - 5
                )

                hi = float(
                    minute
                )

                # ------------------------------------------------
                # Binaere Verfeinerung
                # ------------------------------------------------

                for _ in range(20):

                    mid = (
                        lo + hi
                    ) / 2.0

                    altitude = _moon_altitude(
                        utc_for_local_minutes(mid),
                        lat_deg,
                        lon_deg
                    )

                    if altitude >= threshold:

                        hi = mid

                    else:

                        lo = mid

                rise = (
                    lo + hi
                ) / 2.0

                print(
                    "[Moon] MONDAUFGANG gefunden: "
                    "%.2f Minuten"
                    % rise
                )

            # ====================================================
            # MONDUNTERGANG
            # ====================================================

            if (
                moonset is None
                and
                previous_altitude >= threshold
                and
                current_altitude < threshold
            ):

                lo = float(
                    minute - 5
                )

                hi = float(
                    minute
                )

                # ------------------------------------------------
                # Binaere Verfeinerung
                # ------------------------------------------------

                for _ in range(20):

                    mid = (
                        lo + hi
                    ) / 2.0

                    altitude = _moon_altitude(
                        utc_for_local_minutes(mid),
                        lat_deg,
                        lon_deg
                    )

                    if altitude < threshold:

                        hi = mid

                    else:

                        lo = mid

                moonset = (
                    lo + hi
                ) / 2.0

                print(
                    "[Moon] MONDUNTERGANG gefunden: "
                    "%.2f Minuten"
                    % moonset
                )

            previous_altitude = (
                current_altitude
            )

            # ====================================================
            # BEIDE GEFUNDEN
            # ====================================================

            if (
                rise is not None
                and
                moonset is not None
            ):

                break

        # ========================================================
        # MINUTEN -> HH:MM
        # ========================================================

        def format_time(
                minutes
        ):

            if minutes is None:

                return "na"

            total_minutes = int(
                round(
                    float(minutes)
                )
            )

            total_minutes %= 1440

            hours = (
                total_minutes // 60
            )

            mins = (
                total_minutes % 60
            )

            return "%02d:%02d" % (
                hours,
                mins
            )

        # ========================================================
        # ERGEBNIS
        # ========================================================

        moonrise = format_time(
            rise
        )

        moonset_text = format_time(
            moonset
        )

        result = (
            moonrise,
            moonset_text
        )

        # ========================================================
        # CACHE SPEICHERN
        # ========================================================

        _MOON_RISESET_CACHE[key] = result

        if len(
            _MOON_RISESET_CACHE
        ) > 16:

            first_key = next(
                iter(
                    _MOON_RISESET_CACHE
                )
            )

            del _MOON_RISESET_CACHE[
                first_key
            ]

        # ========================================================
        # AUSGABE
        # ========================================================

        print(
            "[Moon] %s | lat=%.4f lon=%.4f | "
            "Aufgang=%s | Untergang=%s"
            % (
                date_value.isoformat(),
                lat_deg,
                lon_deg,
                moonrise,
                moonset_text
            )
        )

        return (
            moonrise,
            moonset_text
        )

    except Exception as e:

        print(
            "[Moon] FEHLER in "
            "_moon_rise_set_for_date: %s"
            % str(e)
        )

        try:

            import traceback

            traceback.print_exc()

        except Exception:

            pass

        return "na", "na"


# =============================================================================
# HILFSFUNKTION FUER DIE ANZEIGE
# =============================================================================

def getMoonRiseSet(date_value, lat_deg, lon_deg):
    """
    Komfortfunktion.

    Rueckgabe:
        moonrise, moonset
    """

    return _moon_rise_set_for_date(
        date_value,
        lat_deg,
        lon_deg
    )


# =============================================================================
# BEISPIEL FUER DIE VERWENDUNG
# =============================================================================
#
# WICHTIG:
#
# Nicht:
#
#     moonrise = _moon_rise_set_for_date(...)
#
# sondern:
#
#     moonrise, moonset = _moon_rise_set_for_date(...)
#
# =============================================================================

def getMoonTimesForLocation(date_value, location_entry):
    """
    Liest Koordinaten direkt aus einem Location-Eintrag.

    Beispiel location_entry:
        "Duisburg|51.4344|6.7623"

    Rueckgabe:
        ("HH:MM", "HH:MM")
    """

    lat, lon = getCoordsFromEntry(
        location_entry
    )

    if lat is None or lon is None:

        print(
            "[Moon] Keine gueltigen Koordinaten: %s"
            % safeStr(location_entry)
        )

        return "na", "na"

    return _moon_rise_set_for_date(
        date_value,
        lat,
        lon
    )



__version__ = "2.0.1"
VERSION = __version__

def iconToBgCategory(icon):
    icon = (icon or "").strip().lower()
    base = icon[0] if icon else ""
    mapping = {
        "a": "sunny", "j": "sunny",
        "b": "cloudy", "c": "cloudy", "r": "cloudy",
        "d": "mist", "n": "mist",
        "f": "rain", "m": "rain", "q": "rain", "w": "rain",
        "g": "thunder", "s": "thunder",
        "t": "snow", "u": "snow", "v": "snow",
    }
    return mapping.get(base, "")

version = '2.0.1'

# ============================================================
# AUTO WEATHER BACKGROUNDS
# ============================================================

backgroundAutoWeather = True
holidayBackgroundsEnabled = True

# ============================================================
# GITHUB UPDATE / DOWNLOAD
# ============================================================

UPDATE_RAW_BASE = (
    "https://raw.githubusercontent.com/"
    "speedy005/speedy_TheWeather/master"
)

UPDATE_PLUGIN_URL = (
    "https://raw.githubusercontent.com/"
    "speedy005/speedy_TheWeather/master/plugin.py"
)

UPDATE_INSTALLER_URL = (
    "https://raw.githubusercontent.com/"
    "speedy005/speedy_TheWeather/master/installer.sh"
)

UPDATE_DOWNLOAD_TIMEOUT = 30

# ============================================================
# AUTO WEATHER BACKGROUNDS - DOWNLOAD
# ============================================================

AUTO_BG_ZIP_URL = (
    UPDATE_RAW_BASE +
    "/backgrounds_auto.zip"
)

AUTO_BG_ZIP_FILE = (
    "/tmp/backgrounds_auto.zip"
)


# ============================================================
# AUTO WEATHER BACKGROUNDS - PATHS
# ============================================================

AUTO_BG_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp"
)

BACKGROUND_ROOT = (
    "/usr/lib/enigma2/python/Plugins/Extensions/"
    "speedy_TheWeather/backgrounds/"
)

AUTO_BG_DIR = os.path.join(
    BACKGROUND_ROOT,
    "auto"
)

AUTO_BG_MARKER = os.path.join(
    AUTO_BG_DIR,
    ".installed"
)


_AUTO_BG_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")
_AUTO_BG_ALIASES = {
    "clear": ("sunny", "clear", "sun"),
    "cloudy": ("cloudy", "cloud"),
    "mist": ("mist", "fog", "haze"),
    "rain": ("rain", "rainy", "shower", "drizzle"),
    "storm": ("thunder", "storm", "thunderstorm"),
    "snow": ("snow", "snowy", "winter"),
    "halloween": ("halloween",),
    "christmas": ("christmas", "kerst", "weihnachten", "xmas"),
    "newyear": ("newyear", "new_year", "neujahr", "silvester"),
    "easter": ("easter", "ostern"),
}
_AUTO_BG_FILE_CACHE = {}


# ============================================================
# HOLIDAY BACKGROUNDS
# ============================================================

HOLIDAY_BACKGROUNDS = [

    # Halloween
    (10, 25, 10, 31, "halloween"),

    # Weihnachten
    (12, 20, 12, 26, "christmas"),

    # Silvester / Neujahr
    (12, 28, 1, 2, "newyear"),

    # Ostern
    (3, 26, 3, 29, "easter"),
]

# ============================================================
# UPDATE SETTINGS
# ============================================================

UPDATE_CHECK_DELAY_MS = 8000
UPDATE_CHECK_TIMEOUT = 15

UPDATE_INSTALLER_PATH = (
    "/tmp/speedy_TheWeather_update_installer.sh"
)

UPDATE_SUCCESS_FILE = (
    "/tmp/speedy_TheWeather_update_success"
)

# ============================================================
# UPDATE STATE
# ============================================================

_updateStartTimer = None

# Einziger Timer für die Queue-Verarbeitung
_updatePollTimer = None

# Gemeinsame Update-Queue
_updateQueue = queue.Queue()

# Verhindert mehrfaches automatisches Starten der Update-Prüfung
_updateCheckStarted = False

# Verhindert parallele Update-Worker
_updateWorkerStarted = False

# Verhindert parallele Installationen
_updateInstallInProgress = False

# Enthält die aktuell gefundenen Update-Informationen
_updateInfo = None

# Enigma2 Console-Referenz während der Installation
_updateConsole = None

import os
import time
import zipfile
import subprocess

def ensureAutoBackgrounds():
    """
    Lädt backgrounds_auto.zip von GitHub.

    ZIP:
        auto/*.jpg
        extra/*.jpg

    Installation:
        auto/*  -> backgrounds/auto/
        extra/* -> backgrounds/

    Python 2 + Python 3 kompatibel.
    """

    if not backgroundAutoWeather:
        print("[speedy_TheWeather] Auto backgrounds deaktiviert")
        return False

    print("==================================================")
    print("[speedy_TheWeather] AUTO BG CHECK")
    print("==================================================")

    zipFile = AUTO_BG_ZIP_FILE

    try:
        # ====================================================
        # Verzeichnisse erstellen
        # ====================================================

        if not os.path.isdir(BACKGROUND_ROOT):
            os.makedirs(BACKGROUND_ROOT)

        if not os.path.isdir(AUTO_BG_DIR):
            os.makedirs(AUTO_BG_DIR)

        print(
            "[speedy_TheWeather] Background Root:"
        )
        print(BACKGROUND_ROOT)

        print(
            "[speedy_TheWeather] Auto Directory:"
        )
        print(AUTO_BG_DIR)

        # ====================================================
        # Benötigte AUTO-Dateien
        # ====================================================

        requiredAutoBackgrounds = (
            "sunny.jpg",
            "cloudy.jpg",
            "mist.jpg",
            "rain.jpg",
            "thunder.jpg",
            "snow.jpg",
            "halloween.jpg",
            "kerst.jpg",
            "newyear.jpg",
        )

        # ====================================================
        # Prüfen ob AUTO bereits installiert
        # ====================================================

        allInstalled = True

        for filename in requiredAutoBackgrounds:

            target = os.path.join(
                AUTO_BG_DIR,
                filename
            )

            if not os.path.isfile(target):
                allInstalled = False
                break

            try:
                if os.path.getsize(target) <= 0:
                    allInstalled = False
                    break
            except Exception:
                allInstalled = False
                break

        if allInstalled:

            print(
                "[speedy_TheWeather] "
                "Alle Auto-BGs bereits vorhanden."
            )

            try:
                with open(AUTO_BG_MARKER, "w") as f:
                    f.write("installed\n")
                    f.write(
                        "timestamp=%s\n"
                        % int(time.time())
                    )
            except Exception as e:
                print(
                    "[speedy_TheWeather] "
                    "Marker Fehler: %s"
                    % e
                )

            return True

        # ====================================================
        # Alte ZIP löschen
        # ====================================================

        try:
            if os.path.exists(zipFile):
                os.remove(zipFile)
        except Exception as e:
            print(
                "[speedy_TheWeather] "
                "Alte ZIP konnte nicht gelöscht werden: %s"
                % e
            )

        # ====================================================
        # DOWNLOAD
        # ====================================================

        print(
            "[speedy_TheWeather] Download startet..."
        )

        wget_path = "/usr/bin/wget" if os.path.exists("/usr/bin/wget") else "/bin/wget"
        if not os.path.exists(wget_path):
            print("[speedy_TheWeather] wget not found")
            return False

        command = [
            wget_path,
            "-O", zipFile,
            "--timeout=15",
            "--tries=2",
            AUTO_BG_ZIP_URL,
        ]
        print("[speedy_TheWeather] Download via wget")

        result = subprocess.call(command)

        print(
            "[speedy_TheWeather] wget return: %s"
            % result
        )

        if result != 0:
            print(
                "[speedy_TheWeather] "
                "DOWNLOAD FEHLGESCHLAGEN"
            )
            return False

        # ====================================================
        # ZIP vorhanden?
        # ====================================================

        if not os.path.isfile(zipFile):
            print(
                "[speedy_TheWeather] "
                "ZIP wurde nicht erstellt."
            )
            return False

        try:
            zipSize = os.path.getsize(zipFile)
        except Exception:
            zipSize = 0

        print(
            "[speedy_TheWeather] "
            "ZIP Größe: %s Bytes"
            % zipSize
        )

        if zipSize <= 0:
            print(
                "[speedy_TheWeather] "
                "ZIP ist leer."
            )
            return False

        # ====================================================
        # ZIP prüfen
        # ====================================================

        if not zipfile.is_zipfile(zipFile):

            print(
                "[speedy_TheWeather] "
                "FEHLER: Keine gültige ZIP!"
            )

            return False

        print(
            "[speedy_TheWeather] "
            "ZIP ist gültig."
        )

        # ====================================================
        # ZIP öffnen
        # ====================================================

        zf = zipfile.ZipFile(
            zipFile,
            "r"
        )

        try:

            members = zf.namelist()

            print(
                "[speedy_TheWeather] "
                "ZIP Dateien: %s"
                % len(members)
            )

            # =================================================
            # AUTO/
            # =================================================

            autoInstalled = 0

            for filename in requiredAutoBackgrounds:

                sourceName = (
                    "auto/" +
                    filename
                )

                targetPath = os.path.join(
                    AUTO_BG_DIR,
                    filename
                )

                if sourceName not in members:

                    print(
                        "[speedy_TheWeather] "
                        "AUTO fehlt in ZIP: %s"
                        % sourceName
                    )

                    continue

                try:

                    data = zf.read(
                        sourceName
                    )

                    if not data:
                        print(
                            "[speedy_TheWeather] "
                            "AUTO Datei leer: %s"
                            % sourceName
                        )
                        continue

                    tempPath = (
                        targetPath +
                        ".tmp"
                    )

                    with open(
                        tempPath,
                        "wb"
                    ) as f:
                        f.write(data)

                    if os.path.exists(
                        targetPath
                    ):
                        os.remove(
                            targetPath
                        )

                    os.rename(
                        tempPath,
                        targetPath
                    )

                    autoInstalled += 1

                    print(
                        "[speedy_TheWeather] "
                        "AUTO installiert: %s"
                        % filename
                    )

                except Exception as e:

                    print(
                        "[speedy_TheWeather] "
                        "AUTO Fehler %s: %s"
                        % (
                            filename,
                            e
                        )
                    )

                    try:
                        if os.path.exists(
                            tempPath
                        ):
                            os.remove(
                                tempPath
                            )
                    except Exception:
                        pass

            # =================================================
            # EXTRA/
            # =================================================

            extraInstalled = 0

            for member in members:

                if not member.startswith(
                    "extra/"
                ):
                    continue

                if member.endswith(
                    "/"
                ):
                    continue

                filename = os.path.basename(
                    member
                )

                if not filename:
                    continue

                targetPath = os.path.join(
                    BACKGROUND_ROOT,
                    filename
                )

                tempPath = (
                    targetPath +
                    ".tmp"
                )

                try:

                    data = zf.read(
                        member
                    )

                    if not data:
                        print(
                            "[speedy_TheWeather] "
                            "EXTRA Datei leer: %s"
                            % member
                        )
                        continue

                    with open(
                        tempPath,
                        "wb"
                    ) as f:
                        f.write(data)

                    if os.path.exists(
                        targetPath
                    ):
                        os.remove(
                            targetPath
                        )

                    os.rename(
                        tempPath,
                        targetPath
                    )

                    extraInstalled += 1

                    print(
                        "[speedy_TheWeather] "
                        "EXTRA installiert: %s"
                        % filename
                    )

                except Exception as e:

                    print(
                        "[speedy_TheWeather] "
                        "EXTRA Fehler %s: %s"
                        % (
                            member,
                            e
                        )
                    )

                    try:
                        if os.path.exists(
                            tempPath
                        ):
                            os.remove(
                                tempPath
                            )
                    except Exception:
                        pass

            print(
                "[speedy_TheWeather] "
                "AUTO installiert: %s"
                % autoInstalled
            )

            print(
                "[speedy_TheWeather] "
                "EXTRA installiert: %s"
                % extraInstalled
            )

        finally:

            zf.close()

        # ====================================================
        # AUTO-NACHKONTROLLE
        # ====================================================

        missing = []

        for filename in requiredAutoBackgrounds:

            target = os.path.join(
                AUTO_BG_DIR,
                filename
            )

            if not os.path.isfile(
                target
            ):
                missing.append(
                    filename
                )
                continue

            try:
                if os.path.getsize(
                    target
                ) <= 0:
                    missing.append(
                        filename
                    )
            except Exception:
                missing.append(
                    filename
                )

        if missing:

            print(
                "[speedy_TheWeather] "
                "FEHLER - AUTO Dateien fehlen:"
            )

            for filename in missing:
                print(
                    "  - %s"
                    % filename
                )

            return False

        # ====================================================
        # MARKER
        # ====================================================

        try:

            with open(
                AUTO_BG_MARKER,
                "w"
            ) as f:

                f.write(
                    "installed\n"
                )

                f.write(
                    "timestamp=%s\n"
                    % int(time.time())
                )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "Marker Fehler: %s"
                % e
            )

        # ====================================================
        # ZIP löschen
        # ====================================================

        try:

            if os.path.exists(
                zipFile
            ):
                os.remove(
                    zipFile
                )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "ZIP konnte nicht gelöscht werden: %s"
                % e
            )

        print(
            "=================================================="
        )

        print(
            "[speedy_TheWeather] "
            "AUTO BACKGROUNDS ERFOLGREICH INSTALLIERT"
        )

        print(
            "=================================================="
        )

        return True

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "ensureAutoBackgrounds FEHLER: %s"
            % e
        )

        return False

def findAutoBgFile(category):
    """Return the first valid background for *category*, with a small path cache."""
    if not category:
        return None
    try:
        category = str(category).strip().lower()
    except Exception:
        return None

    cached = _AUTO_BG_FILE_CACHE.get(category)
    if cached:
        try:
            if os.path.isfile(cached) and os.path.getsize(cached) > 0:
                return cached
        except Exception:
            pass
        _AUTO_BG_FILE_CACHE.pop(category, None)

    if not os.path.isdir(AUTO_BG_DIR):
        return None

    names = _AUTO_BG_ALIASES.get(category, (category,))
    for name in names:
        for ext in _AUTO_BG_EXTENSIONS:
            path = os.path.join(AUTO_BG_DIR, name + ext)
            try:
                if os.path.isfile(path) and os.path.getsize(path) > 0:
                    _AUTO_BG_FILE_CACHE[category] = path
                    return path
            except OSError:
                continue
    return None

def isNightTime():
    global weatherData
    try:
        dag = weatherData["days"][0]
        sunrise = dag.get("sunrise", "")
        sunset = dag.get("sunset", "")
        if not sunrise or not sunset:
            return False
        now = time.localtime()
        nowMin = now.tm_hour * 60 + now.tm_min
        sr = sunrise.split("T")[1]
        ss = sunset.split("T")[1]
        srMin = int(sr[:2]) * 60 + int(sr[3:5])
        ssMin = int(ss[:2]) * 60 + int(ss[3:5])
        return not (srMin <= nowMin < ssMin)
    except Exception:
        return False

def getHolidayBgCategory():
    """
    Ermittelt die aktuelle Feiertags-Kategorie.

    Gibt z.B. zurück:
        halloween
        christmas
        newyear
        easter

    oder None, wenn aktuell kein Feiertagszeitraum aktiv ist.
    """

    global holidayBackgroundsEnabled

    if not holidayBackgroundsEnabled:
        return None

    now = time.localtime()

    month = now.tm_mon
    day = now.tm_mday

    for sm, sd, em, ed, cat in HOLIDAY_BACKGROUNDS:

        # ----------------------------------------------------
        # Zeitraum innerhalb desselben Monats
        # ----------------------------------------------------

        if sm == em:

            if (
                month == sm
                and sd <= day <= ed
            ):
                return cat

        # ----------------------------------------------------
        # Zeitraum über den Jahreswechsel
        #
        # Beispiel:
        # 20.12. - 05.01.
        # ----------------------------------------------------

        elif sm > em:

            if (
                (month == sm and day >= sd)
                or
                (month == em and day <= ed)
                or
                (month > sm)
                or
                (month < em)
            ):
                return cat

        # ----------------------------------------------------
        # Normaler Zeitraum über mehrere Monate
        #
        # Beispiel:
        # 01.03. - 31.03.
        # oder
        # 15.03. - 15.04.
        # ----------------------------------------------------

        else:

            if (
                (month == sm and day >= sd)
                or
                (month == em and day <= ed)
                or
                (sm < month < em)
            ):
                return cat

    return None

def getAutoWeatherBackground():
    global weatherData

    defaultBg = (
        "/usr/lib/enigma2/python/Plugins/Extensions/"
        "speedy_TheWeather/"
        + SHARED_PACK +
        "/backgroundhd_2.png"
    )

    # -------------------------------------------------
    # FEIERTAG
    # -------------------------------------------------

    try:
        holidayCat = getHolidayBgCategory()
    except Exception as e:
        holidayCat = None
        print(
            "[speedy_TheWeather] AUTO: "
            "holiday check error: %s"
            % str(e)
        )

    if holidayCat:

        try:
            holidayBg = findAutoBgFile(
                holidayCat
            )
        except Exception as e:
            holidayBg = None
            print(
                "[speedy_TheWeather] AUTO: "
                "holiday background error: %s"
                % str(e)
            )

        if (
            holidayBg
            and os.path.isfile(holidayBg)
        ):
            print(
                "[speedy_TheWeather] "
                "AUTO holiday: %s -> %s"
                % (
                    holidayCat,
                    holidayBg
                )
            )

            return holidayBg

        print(
            "[speedy_TheWeather] "
            "AUTO holiday: kein Bild fuer %s"
            % holidayCat
        )

    # -------------------------------------------------
    # WETTERDATEN
    # -------------------------------------------------

    try:

        if not isinstance(
            weatherData,
            dict
        ):
            print(
                "[speedy_TheWeather] "
                "AUTO: weatherData ist kein dict"
            )
            return defaultBg

        days = weatherData.get(
            "days",
            []
        )

        if not days:
            print(
                "[speedy_TheWeather] "
                "AUTO: keine Wettertage vorhanden"
            )
            return defaultBg

        day = days[0]

        if not isinstance(
            day,
            dict
        ):
            print(
                "[speedy_TheWeather] "
                "AUTO: Wettertag ist ungueltig"
            )
            return defaultBg

        hours = day.get(
            "hours",
            []
        )

        if not isinstance(
            hours,
            list
        ):
            hours = []

        icon = None

        # -------------------------------------------------
        # AKTUELLE STUNDE
        # -------------------------------------------------

        now_hour = time.localtime().tm_hour

        for hour in hours:

            if not isinstance(
                hour,
                dict
            ):
                continue

            try:

                h = hour.get("hour")

                if h is None:
                    h = hour.get("time")

                if isinstance(
                    h,
                    str
                ):

                    h = h.strip()

                    if ":" in h:
                        h = h.split(
                            ":",
                            1
                        )[0]

                    elif "T" in h:

                        h = h.split(
                            "T",
                            1
                        )[-1]

                        if ":" in h:
                            h = h.split(
                                ":",
                                1
                            )[0]

                if h is not None:

                    if int(h) == now_hour:

                        icon = hour.get(
                            "iconcode"
                        )

                        if icon is None:
                            icon = hour.get(
                                "icon"
                            )

                        print(
                            "[speedy_TheWeather] "
                            "AUTO: aktuelles Stunden-Icon=%r"
                            % icon
                        )

                        if icon:
                            break

            except Exception:
                continue

        # -------------------------------------------------
        # FALLBACK TAGES-ICON
        # -------------------------------------------------

        if not icon:

            icon = day.get(
                "iconcode"
            )

            if icon is None:
                icon = day.get(
                    "icon"
                )

            print(
                "[speedy_TheWeather] "
                "AUTO: Tages-Icon=%r"
                % icon
            )

        # -------------------------------------------------
        # FALLBACK ERSTE STUNDE
        # -------------------------------------------------

        if not icon and hours:

            firstHour = hours[0]

            if isinstance(
                firstHour,
                dict
            ):

                icon = firstHour.get(
                    "iconcode"
                )

                if icon is None:
                    icon = firstHour.get(
                        "icon"
                    )

                print(
                    "[speedy_TheWeather] "
                    "AUTO: erstes Stunden-Icon=%r"
                    % icon
                )

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "AUTO: Wetterdaten nicht lesbar: %s"
            % str(e)
        )

        return defaultBg

    # -------------------------------------------------
    # KEIN ICON
    # -------------------------------------------------

    if icon is None:

        print(
            "[speedy_TheWeather] "
            "AUTO: kein Icon gefunden"
        )

        return defaultBg

    # -------------------------------------------------
    # ICON -> KATEGORIE
    # -------------------------------------------------

    try:

        category = iconToBgCategory(
            icon
        )

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "AUTO: iconToBgCategory Fehler: %s"
            % str(e)
        )

        return defaultBg

    print(
        "[speedy_TheWeather] "
        "AUTO: icon=%r category=%r"
        % (
            icon,
            category
        )
    )

    # -------------------------------------------------
    # KEINE KATEGORIE
    # -------------------------------------------------

    if not category:

        print(
            "[speedy_TheWeather] "
            "AUTO: keine Wetterkategorie fuer Icon %r"
            % icon
        )

        return defaultBg

    # -------------------------------------------------
    # NACHT-HINTERGRUND
    # -------------------------------------------------

    try:

        if isNightTime():

            nightCategory = (
                "clear"
                if category == "sunny"
                else category
            )

            nightBg = findAutoBgFile(
                nightCategory + "_night"
            )

            if (
                nightBg
                and os.path.isfile(nightBg)
            ):

                print(
                    "[speedy_TheWeather] "
                    "AUTO night: %s -> %s"
                    % (
                        nightCategory,
                        nightBg
                    )
                )

                return nightBg

            print(
                "[speedy_TheWeather] "
                "AUTO night: kein Bild fuer %s"
                % (
                    nightCategory + "_night"
                )
            )

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "AUTO: Nacht-Hintergrund Fehler: %s"
            % str(e)
        )

    # -------------------------------------------------
    # NORMALES WETTERBILD
    # -------------------------------------------------

    try:

        bgfile = findAutoBgFile(
            category
        )

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "AUTO: findAutoBgFile Fehler: %s"
            % str(e)
        )

        return defaultBg

    if (
        bgfile
        and os.path.isfile(bgfile)
    ):

        print(
            "[speedy_TheWeather] "
            "AUTO weather: %s -> %s"
            % (
                category,
                bgfile
            )
        )

        return bgfile

    # -------------------------------------------------
    # KEIN BILD GEFUNDEN
    # -------------------------------------------------

    print(
        "[speedy_TheWeather] "
        "AUTO: kein Bild fuer Kategorie %s"
        % category
    )

    print(
        "[speedy_TheWeather] "
        "AUTO: fallback -> %s"
        % defaultBg
    )

    return defaultBg



# ============================================================================
# VERSION COMPARISON
# ============================================================================

def _version_tuple(value):
    """
    Versionsnummer robust vergleichen.

    Beispiele:
        5.6  <  5.10
        1.4.3 < 1.4.4
    """

    try:

        parts = (
            safeStr(value)
            .strip()
            .lstrip("v")
            .split(".")
        )

        result = []

        for part in parts:

            number = ""

            for char in part:

                if char.isdigit():

                    number += char

                else:

                    break

            result.append(
                int(number)
                if number
                else 0
            )

        return (
            tuple(result)
            if result
            else (0,)
        )

    except Exception:

        return (0,)

# ============================================================================
# CHECK REMOTE VERSION
# ============================================================================

def _update_is_newer(remote_version):

    try:

        current_version = VERSION

    except Exception:

        try:

            current_version = __version__

        except Exception:

            current_version = "0.0.0"

    try:

        return (
            _version_tuple(
                remote_version
            )
            >
            _version_tuple(
                current_version
            )
        )

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "Version comparison failed: %s"
            % e
        )

        return False

# ============================================================================
# UPDATE DOWNLOAD
# ============================================================================

def _update_download(url, destination, timeout=None):
    """
    Download für das Update-System über wget.
    Gibt True bei Erfolg und False bei Fehler zurück.
    """

    if timeout is None:
        timeout = UPDATE_DOWNLOAD_TIMEOUT

    try:

        print(
            "[speedy_TheWeather] "
            "UPDATE DOWNLOAD START"
        )

        print(
            "[speedy_TheWeather] "
            "URL: %s"
            % url
        )

        print(
            "[speedy_TheWeather] "
            "DEST: %s"
            % destination
        )

        # --------------------------------------------------------
        # WGET SUCHEN
        # --------------------------------------------------------

        wgetPath = "/usr/bin/wget"

        if not os.path.exists(wgetPath):

            print(
                "[speedy_TheWeather] "
                "ERROR: wget not found: %s"
                % wgetPath
            )

            if os.path.exists("/bin/wget"):

                wgetPath = "/bin/wget"

                print(
                    "[speedy_TheWeather] "
                    "Using fallback wget: %s"
                    % wgetPath
                )

            else:

                print(
                    "[speedy_TheWeather] "
                    "ERROR: /bin/wget also not found"
                )

                return False

        # --------------------------------------------------------
        # ALTE DATEI ENTFERNEN
        # --------------------------------------------------------

        try:

            if os.path.exists(destination):

                os.remove(destination)

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "WARNING: could not remove old file: %s"
                % e
            )

        # --------------------------------------------------------
        # WGET COMMAND
        #
        # WICHTIG:
        # KEIN -q!
        #
        # Dadurch sehen wir bei einem Fehler die tatsächliche
        # wget-Meldung im Enigma2-Log.
        # --------------------------------------------------------

        command = [
            wgetPath,
            "--no-check-certificate",
            "--timeout=%d" % int(timeout),
            "--tries=2",
            "--user-agent=speedy_TheWeather-Updater/1.0",
            "-O", destination,
            url,
        ]

        print("[speedy_TheWeather] WGET DOWNLOAD")

        # --------------------------------------------------------
        # DOWNLOAD
        # --------------------------------------------------------

        result = subprocess.call(command)

        print(
            "[speedy_TheWeather] "
            "WGET RETURN CODE: %s"
            % result
        )

        # --------------------------------------------------------
        # DOWNLOAD FEHLER
        # --------------------------------------------------------

        if result != 0:

            print(
                "[speedy_TheWeather] "
                "ERROR: wget failed "
                "with return code %s"
                % result
            )

            try:

                if os.path.exists(destination):

                    os.remove(destination)

            except Exception:
                pass

            return False

        # --------------------------------------------------------
        # DATEI EXISTIERT?
        # --------------------------------------------------------

        if not os.path.exists(
            destination
        ):

            print(
                "[speedy_TheWeather] "
                "ERROR: downloaded file "
                "does not exist"
            )

            return False

        # --------------------------------------------------------
        # DATEIGRÖSSE
        # --------------------------------------------------------

        try:

            fileSize = os.path.getsize(
                destination
            )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "ERROR: cannot read file size: %s"
                % e
            )

            return False

        print(
            "[speedy_TheWeather] "
            "DOWNLOADED SIZE: %d bytes"
            % fileSize
        )

        # --------------------------------------------------------
        # LEERE DATEI
        # --------------------------------------------------------

        if fileSize <= 0:

            print(
                "[speedy_TheWeather] "
                "ERROR: downloaded file is empty"
            )

            try:

                os.remove(destination)

            except Exception:
                pass

            return False

        # --------------------------------------------------------
        # ERFOLG
        # --------------------------------------------------------

        print(
            "[speedy_TheWeather] "
            "UPDATE DOWNLOAD SUCCESS"
        )

        return True

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "UPDATE DOWNLOAD EXCEPTION: %s"
            % e
        )

        try:

            if os.path.exists(destination):

                os.remove(destination)

        except Exception:
            pass

        return False

# ============================================================================
# EXTRACT PLUGIN VERSION
# ============================================================================

def _update_extract_plugin_version(source):

    """
    Liest __version__, version oder VERSION aus plugin.py,
    ohne den Remote-Code auszuführen.
    """

    try:

        tree = ast.parse(
            source,
            filename="plugin.py"
        )

        for node in tree.body:

            if not isinstance(
                node,
                ast.Assign
            ):

                continue

            for target in node.targets:

                if not isinstance(
                    target,
                    ast.Name
                ):

                    continue

                if target.id not in (
                    "__version__",
                    "version",
                    "VERSION"
                ):

                    continue

                value = node.value

                # ------------------------------------------------
                # Python 3
                # ------------------------------------------------

                if (
                    isinstance(
                        value,
                        ast.Constant
                    )
                    and
                    isinstance(
                        value.value,
                        str
                    )
                ):

                    return value.value.strip()

                # ------------------------------------------------
                # Older Python / Enigma2
                # ------------------------------------------------

                if (
                    hasattr(
                        ast,
                        "Str"
                    )
                    and
                    isinstance(
                        value,
                        ast.Str
                    )
                ):

                    return value.s.strip()

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "Could not read GitHub plugin version: %s"
            % e
        )

    return ""

# ============================================================================
# EXTRACT INSTALLER INFORMATION
# ============================================================================

def _update_extract_installer_info(source, language=None):
    """
    Liest Version und mehrsprachige Changelogs aus installer.sh.

    Unterstützte Sprachen:
        EN, DE, AR, CS, EL, FI, FR, HU, IT, NL, PL, RU, SK, UA, ZH

    Unterstützte Formate:

        VERSION="1.9.8"

        changelog_EN='
        • Change one.
        • Change two.
        '

        changelog_DE='
        • Änderung eins.
        • Änderung zwei.
        '

    Zusätzlich weiterhin altes Format:

        changelog='v1.9.8 EN: ... | DE: ...'

    Parameter:
        language:
            Optional gewünschte Sprache, z.B. "DE", "EN", "EL".
            Wenn keine Sprache angegeben wird:
                DE -> EN -> erste vorhandene Sprache
    """

    result = {
        "version": "",
        "changelog": "",
        "changelog_EN": "",
        "changelog_DE": "",
        "changelog_AR": "",
        "changelog_CS": "",
        "changelog_EL": "",
        "changelog_FI": "",
        "changelog_FR": "",
        "changelog_HU": "",
        "changelog_IT": "",
        "changelog_NL": "",
        "changelog_PL": "",
        "changelog_RU": "",
        "changelog_SK": "",
        "changelog_UA": "",
        "changelog_ZH": ""
    }

    try:
        import re

        # ---------------------------------------------------------
        # SOURCE ABSICHERN
        # ---------------------------------------------------------
        if source is None:
            source = ""

        if not isinstance(source, str):
            try:
                source = source.decode("utf-8", "replace")
            except Exception:
                source = safeStr(source)

        # ---------------------------------------------------------
        # VERSION
        # ---------------------------------------------------------
        match = re.search(
            r'^\s*VERSION\s*=\s*["\']([^"\']+)["\']',
            source,
            re.MULTILINE
        )

        if match:
            result["version"] = match.group(1).strip()

        # ---------------------------------------------------------
        # UNTERSTÜTZTE SPRACHEN
        # ---------------------------------------------------------
        languages = (
            "EN",
            "DE",
            "AR",
            "CS",
            "EL",
            "FI",
            "FR",
            "HU",
            "IT",
            "NL",
            "PL",
            "RU",
            "SK",
            "UA",
            "ZH"
        )

        # ---------------------------------------------------------
        # MULTI LANGUAGE CHANGELOGS
        #
        # Unterstützt:
        #
        # changelog_EN='...'
        #
        # sowie:
        #
        # changelog_EN="..."
        #
        # Multiline wird ebenfalls unterstützt.
        # ---------------------------------------------------------
        for lang in languages:

            key = "changelog_" + lang

            pattern = (
                r"^\s*" +
                re.escape(key) +
                r"\s*=\s*(?P<quote>['\"])(?P<text>[\s\S]*?)(?P=quote)"
            )

            match = re.search(
                pattern,
                source,
                re.MULTILINE
            )

            if match:
                value = match.group("text")

                if value:
                    value = value.strip()

                result[key] = value

        # ---------------------------------------------------------
        # LEGACY CHANGELOG
        #
        # Nur verwenden, wenn kein moderner mehrsprachiger
        # Changelog gefunden wurde.
        # ---------------------------------------------------------
        if not any(
            result["changelog_" + lang]
            for lang in languages
        ):

            pattern = (
                r"^\s*changelog\s*=\s*"
                r"(?P<quote>['\"])(?P<text>[\s\S]*?)(?P=quote)"
            )

            match = re.search(
                pattern,
                source,
                re.MULTILINE
            )

            if match:
                legacy = match.group("text").strip()

                # -------------------------------------------------
                # LEGACY EN
                # -------------------------------------------------
                match_en = re.search(
                    r"(?:^|\s)EN:\s*(.*?)(?=\s*\|\s*DE:|$)",
                    legacy,
                    re.IGNORECASE | re.DOTALL
                )

                if match_en:
                    result["changelog_EN"] = (
                        match_en.group(1).strip()
                    )

                # -------------------------------------------------
                # LEGACY DE
                # -------------------------------------------------
                match_de = re.search(
                    r"(?:^|\s)DE:\s*(.*)$",
                    legacy,
                    re.IGNORECASE | re.DOTALL
                )

                if match_de:
                    result["changelog_DE"] = (
                        match_de.group(1).strip()
                    )

                # -------------------------------------------------
                # FALLBACK
                # -------------------------------------------------
                if (
                    not result["changelog_EN"]
                    and not result["changelog_DE"]
                ):
                    result["changelog"] = legacy

        # ---------------------------------------------------------
        # GEWÜNSCHTE SPRACHE BESTIMMEN
        # ---------------------------------------------------------
        selected_language = ""

        if language:
            try:
                selected_language = safeStr(
                    language
                ).strip().upper()
            except Exception:
                selected_language = ""

        # ---------------------------------------------------------
        # GEWÜNSCHTE SPRACHE
        # ---------------------------------------------------------
        if selected_language in languages:

            selected_key = (
                "changelog_" +
                selected_language
            )

            if result[selected_key]:
                result["changelog"] = (
                    result[selected_key]
                )

        # ---------------------------------------------------------
        # STANDARD:
        # DE -> EN -> erste vorhandene Sprache
        # ---------------------------------------------------------
        if not result["changelog"]:

            if result["changelog_DE"]:
                result["changelog"] = (
                    result["changelog_DE"]
                )

            elif result["changelog_EN"]:
                result["changelog"] = (
                    result["changelog_EN"]
                )

            else:
                # Erste vorhandene Sprache als Fallback
                for lang in languages:

                    value = result[
                        "changelog_" + lang
                    ]

                    if value:
                        result["changelog"] = value
                        break

        # ---------------------------------------------------------
        # SPRACHEN-METADATEN
        # ---------------------------------------------------------
        result["changelog_languages"] = []

        for lang in languages:

            if result["changelog_" + lang]:
                result["changelog_languages"].append(lang)

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "Could not read installer information: %s"
            % e
        )

    return result


def _update_changes_text(changes):
    """
    Formatiert Changelog-Daten für die Anzeige.

    Unterstützt:
        - Liste / Tuple
        - mehrzeilige Strings
        - Bulletpoints mit •
        - Bulletpoints mit -
        - Bulletpoints mit *
        - Fortsetzungszeilen

    Unicode-Sprachen wie:
        Deutsch
        Ελληνικά
        Русский
        العربية
        中文
        Українська
    werden unverändert unterstützt.
    """

    import re

    # ---------------------------------------------------------
    # LIST / TUPLE
    # ---------------------------------------------------------
    if isinstance(changes, (list, tuple)):

        items = []

        for item in changes:

            text = safeStr(item).strip()

            if not text:
                continue

            text = re.sub(
                r"^\s*(?:•|-|\*)\s*",
                "",
                text
            ).strip()

            if text:
                items.append(
                    "- " + _(text)
                )

        if items:
            return "\n".join(items)

        return _("No changes available.")

    # ---------------------------------------------------------
    # STRING
    # ---------------------------------------------------------
    text = safeStr(changes).strip()

    if not text:
        return _("No changes available.")

    lines = text.splitlines()

    items = []
    current = ""

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # -----------------------------------------------------
        # NEUER BULLETPOINT
        # -----------------------------------------------------
        if re.match(
            r"^\s*(?:•|-|\*)\s+",
            line
        ):

            if current:
                items.append(current)

            current = re.sub(
                r"^\s*(?:•|-|\*)\s*",
                "",
                line
            ).strip()

        else:

            # -------------------------------------------------
            # FORTSETZUNGSZEILE
            # -------------------------------------------------
            if current:
                current += " " + line

            else:
                current = line

    # ---------------------------------------------------------
    # LETZTEN EINTRAG ÜBERNEHMEN
    # ---------------------------------------------------------
    if current:
        items.append(current)

    # ---------------------------------------------------------
    # FORMATIERT AUSGEBEN
    # ---------------------------------------------------------
    if items:

        return "\n".join(
            "- " + _(item)
            for item in items
            if item.strip()
        )

    # ---------------------------------------------------------
    # NORMALER EINZEILIGER TEXT
    # ---------------------------------------------------------
    return _(text)



# ============================================================================
# UPDATE CHECK WORKER
# ============================================================================
UPDATE_DEBUG_LOG = "/tmp/speedy_update_debug.log"

def _update_debug(message):

    try:

        with open(
            UPDATE_DEBUG_LOG,
            "a"
        ) as debug_file:

            debug_file.write(
                "%s\n"
                % message
            )

    except Exception:

        pass

    try:

        print(
            "[speedy_TheWeather] %s"
            % message
        )

    except Exception:

        pass

def _update_check_worker():

    global _updateWorkerStarted

    plugin_path = None
    installer_path = None

    debug_log = "/tmp/speedy_update_debug.log"

    def debug(message):

        try:

            with open(
                debug_log,
                "a"
            ) as debug_file:

                debug_file.write(
                    "%s\n"
                    % message
                )

        except Exception:

            pass

        try:

            print(
                "[speedy_TheWeather] %s"
                % message
            )

        except Exception:

            pass

    try:

        # ------------------------------------------------------------
        # START
        # ------------------------------------------------------------

        try:

            with open(
                debug_log,
                "w"
            ) as debug_file:

                debug_file.write(
                    "speedy_TheWeather UPDATE DEBUG\n"
                )

        except Exception:

            pass

        debug(
            "=================================================="
        )

        debug(
            "UPDATE CHECK START"
        )

        debug(
            "Plugin URL: %s"
            % UPDATE_PLUGIN_URL
        )

        debug(
            "Installer URL: %s"
            % UPDATE_INSTALLER_URL
        )

        # ------------------------------------------------------------
        # CURRENT VERSION
        # ------------------------------------------------------------

        try:

            current_version = VERSION

        except Exception:

            try:

                current_version = __version__

            except Exception:

                current_version = "0.0.0"

        debug(
            "Installed VERSION: %s"
            % current_version
        )

        # ------------------------------------------------------------
        # TEMP PLUGIN FILE
        # ------------------------------------------------------------

        try:

            fd, plugin_path = tempfile.mkstemp(
                prefix=".speedy_TheWeather_remote_",
                suffix=".py",
                dir="/tmp"
            )

            os.close(fd)

        except Exception as e:

            debug(
                "ERROR creating temporary plugin file: %s"
                % e
            )

            _updateQueue.put(
                (
                    "error",
                    _(
                        "Could not create temporary update file."
                    )
                )
            )

            return

        debug(
            "Temporary plugin file: %s"
            % plugin_path
        )

        # ------------------------------------------------------------
        # DOWNLOAD REMOTE PLUGIN
        # ------------------------------------------------------------

        debug(
            "Downloading remote plugin.py..."
        )

        download_result = _update_download(
            UPDATE_PLUGIN_URL,
            plugin_path,
            timeout=UPDATE_CHECK_TIMEOUT
        )

        debug(
            "plugin.py download result: %s"
            % download_result
        )

        if not download_result:

            debug(
                "ERROR: Could not download remote plugin.py."
            )

            _updateQueue.put(
                (
                    "error",
                    _(
                        "Could not download update information."
                    )
                )
            )

            return

        # ------------------------------------------------------------
        # VERIFY FILE
        # ------------------------------------------------------------

        if not os.path.exists(
            plugin_path
        ):

            debug(
                "ERROR: Downloaded plugin.py does not exist."
            )

            _updateQueue.put(
                (
                    "error",
                    _(
                        "Downloaded update file is missing."
                    )
                )
            )

            return

        try:

            plugin_size = os.path.getsize(
                plugin_path
            )

        except Exception as e:

            plugin_size = 0

            debug(
                "ERROR: Could not get plugin.py size: %s"
                % e
            )

        debug(
            "Downloaded plugin.py size: %d bytes"
            % plugin_size
        )

        if plugin_size <= 0:

            debug(
                "ERROR: Downloaded plugin.py is empty."
            )

            _updateQueue.put(
                (
                    "error",
                    _(
                        "Downloaded update file is empty."
                    )
                )
            )

            return

        # ------------------------------------------------------------
        # READ REMOTE SOURCE
        # ------------------------------------------------------------

        debug(
            "Reading remote plugin.py..."
        )

        try:

            with open(
                plugin_path,
                "r",
                encoding="utf-8"
            ) as source_file:

                remote_source = (
                    source_file.read()
                )

        except Exception as e:

            debug(
                "ERROR reading remote plugin.py: %s"
                % e
            )

            _updateQueue.put(
                (
                    "error",
                    _(
                        "Could not read update information."
                    )
                )
            )

            return

        debug(
            "Remote plugin.py read successfully."
        )

        debug(
            "Remote plugin.py characters: %d"
            % len(remote_source)
        )

        # ------------------------------------------------------------
        # PYTHON SYNTAX CHECK
        # ------------------------------------------------------------

        debug(
            "Checking remote plugin.py syntax..."
        )

        try:

            ast.parse(
                remote_source,
                filename="plugin.py"
            )

        except SyntaxError as e:

            debug(
                "=================================================="
            )

            debug(
                "REMOTE PLUGIN PYTHON SYNTAX ERROR"
            )

            debug(
                "Message: %s"
                % getattr(
                    e,
                    "msg",
                    str(e)
                )
            )

            debug(
                "Line: %s"
                % getattr(
                    e,
                    "lineno",
                    "?"
                )
            )

            debug(
                "Column: %s"
                % getattr(
                    e,
                    "offset",
                    "?"
                )
            )

            debug(
                "End line: %s"
                % getattr(
                    e,
                    "end_lineno",
                    "?"
                )
            )

            debug(
                "End column: %s"
                % getattr(
                    e,
                    "end_offset",
                    "?"
                )
            )

            debug(
                "Source line: %s"
                % safeStr(
                    getattr(
                        e,
                        "text",
                        ""
                    )
                ).rstrip()
            )

            debug(
                "Full SyntaxError: %s"
                % safeStr(e)
            )

            debug(
                "=================================================="
            )

            try:

                error_message = (
                    "Remote plugin.py contains invalid Python syntax.\n\n"
                    "Line: %s\n"
                    "Column: %s\n\n"
                    "%s"
                    % (
                        getattr(
                            e,
                            "lineno",
                            "?"
                        ),
                        getattr(
                            e,
                            "offset",
                            "?"
                        ),
                        safeStr(e)
                    )
                )

                _updateQueue.put(
                    (
                        "error",
                        error_message
                    )
                )

            except Exception as queue_error:

                debug(
                    "Could not queue syntax error: %s"
                    % queue_error
                )

            return

        except Exception as e:

            debug(
                "REMOTE PLUGIN VALIDATION EXCEPTION"
            )

            debug(
                "Exception type: %s"
                % type(e).__name__
            )

            debug(
                "Exception: %s"
                % safeStr(e)
            )

            try:

                import traceback

                debug(
                    traceback.format_exc()
                )

            except Exception:

                pass

            try:

                _updateQueue.put(
                    (
                        "error",
                        _(
                            "Could not validate remote plugin.py."
                        )
                    )
                )

            except Exception:

                pass

            return

        debug(
            "Remote plugin.py syntax is valid."
        )

        # ------------------------------------------------------------
        # EXTRACT REMOTE VERSION
        # ------------------------------------------------------------

        debug(
            "Extracting remote version..."
        )

        try:

            remote_version = (
                _update_extract_plugin_version(
                    remote_source
                )
            )

        except Exception as e:

            debug(
                "ERROR extracting remote version: %s"
                % e
            )

            _updateQueue.put(
                (
                    "error",
                    _(
                        "Could not read remote plugin version."
                    )
                )
            )

            return

        if not remote_version:

            debug(
                "ERROR: Remote version could not be detected."
            )

            _updateQueue.put(
                (
                    "error",
                    _(
                        "Update information is incomplete."
                    )
                )
            )

            return

        debug(
            "Remote VERSION: %s"
            % remote_version
        )

        # ------------------------------------------------------------
        # VERSION COMPARISON
        # ------------------------------------------------------------

        debug(
            "Comparing versions..."
        )

        try:

            is_newer = _update_is_newer(
                remote_version
            )

        except Exception as e:

            debug(
                "ERROR during version comparison: %s"
                % e
            )

            _updateQueue.put(
                (
                    "error",
                    _(
                        "Could not compare plugin versions."
                    )
                )
            )

            return

        debug(
            "VERSION CHECK: installed=%s remote=%s newer=%s"
            % (
                current_version,
                remote_version,
                is_newer
            )
        )

        # ------------------------------------------------------------
        # NO UPDATE
        # ------------------------------------------------------------

        if not is_newer:

            debug(
                "Plugin is already up to date."
            )

            _updateQueue.put(
                (
                    "current",
                    {
                        "version": remote_version
                    }
                )
            )

            return

        # ------------------------------------------------------------
        # UPDATE AVAILABLE
        # ------------------------------------------------------------

        debug(
            "=================================================="
        )

        debug(
            "NEW UPDATE AVAILABLE"
        )

        debug(
            "Installed: %s"
            % current_version
        )

        debug(
            "Remote: %s"
            % remote_version
        )

        debug(
            "=================================================="
        )

        # ------------------------------------------------------------
        # TEMP INSTALLER FILE
        # ------------------------------------------------------------

        try:

            fd, installer_path = tempfile.mkstemp(
                prefix=".speedy_TheWeather_installer_info_",
                suffix=".sh",
                dir="/tmp"
            )

            os.close(fd)

        except Exception as e:

            debug(
                "ERROR creating temporary installer file: %s"
                % e
            )

            installer_path = None

        installer_info = {
            "version": "",
            "changelog": ""
        }

        # ------------------------------------------------------------
        # DOWNLOAD INSTALLER
        # ------------------------------------------------------------

        if installer_path:

            debug(
                "Temporary installer file: %s"
                % installer_path
            )

            debug(
                "Downloading installer.sh..."
            )

            installer_download_result = _update_download(
                UPDATE_INSTALLER_URL,
                installer_path,
                timeout=UPDATE_CHECK_TIMEOUT
            )

            debug(
                "installer.sh download result: %s"
                % installer_download_result
            )

            if installer_download_result:

                try:

                    with open(
                        installer_path,
                        "r",
                        encoding="utf-8"
                    ) as installer_file:

                        installer_source = (
                            installer_file.read()
                        )

                    debug(
                        "installer.sh read successfully."
                    )

                    debug(
                        "installer.sh characters: %d"
                        % len(installer_source)
                    )

                    try:

                        installer_info = (
                            _update_extract_installer_info(
                                installer_source
                            )
                        )

                    except Exception as e:

                        debug(
                            "ERROR extracting installer information: %s"
                            % e
                        )

                        installer_info = {
                            "version": "",
                            "changelog": ""
                        }

                    debug(
                        "Installer version: %s"
                        % installer_info.get(
                            "version",
                            ""
                        )
                    )

                    debug(
                        "Changelog detected: %s"
                        % bool(
                            installer_info.get(
                                "changelog",
                                ""
                            )
                        )
                    )

                except Exception as e:

                    debug(
                        "Could not read installer information: %s"
                        % e
                    )

            else:

                debug(
                    "WARNING: Could not download installer.sh."
                )

                debug(
                    "Continuing without installer information."
                )

        else:

            debug(
                "WARNING: Could not create installer info file."
            )

            debug(
                "Continuing without installer information."
            )

        # ------------------------------------------------------------
        # CHANGELOG
        # ------------------------------------------------------------

        changes = installer_info.get(
            "changelog",
            ""
        )

        if not changes:

            changes = _(
                "No changes available."
            )

        # ------------------------------------------------------------
        # QUEUE UPDATE INFORMATION
        # ------------------------------------------------------------

        debug(
            "QUEUE PUT: available / %s"
            % remote_version
        )

        try:

            _updateQueue.put(
                (
                    "available",
                    {
                        "version":
                            remote_version,

                        "changes":
                            changes,

                        "installer_version":
                            installer_info.get(
                                "version",
                                ""
                            )
                    }
                )
            )

            debug(
                "Update information successfully sent to GUI queue."
            )

        except Exception as e:

            debug(
                "Could not put update information into queue: %s"
                % e
            )

    except Exception as e:

        debug(
            "=================================================="
        )

        debug(
            "UPDATE CHECK WORKER EXCEPTION"
        )

        debug(
            "Exception type: %s"
            % type(e).__name__
        )

        debug(
            "Exception: %s"
            % safeStr(e)
        )

        try:

            import traceback

            debug(
                traceback.format_exc()
            )

        except Exception:

            pass

        debug(
            "=================================================="
        )

        try:

            _updateQueue.put(
                (
                    "error",
                    _(
                        "Update check failed."
                    )
                )
            )

        except Exception:

            pass

    finally:

        # ------------------------------------------------------------
        # CLEAN TEMP FILES
        # ------------------------------------------------------------

        for path in (
            plugin_path,
            installer_path
        ):

            if (
                path
                and
                os.path.exists(
                    path
                )
            ):

                try:

                    os.unlink(
                        path
                    )

                    debug(
                        "Removed temporary file: %s"
                        % path
                    )

                except Exception as e:

                    debug(
                        "Could not remove temporary file %s: %s"
                        % (
                            path,
                            e
                        )
                    )

        # ------------------------------------------------------------
        # ALLOW NEXT UPDATE CHECK
        # ------------------------------------------------------------

        _updateWorkerStarted = False

        debug(
            "UPDATE CHECK FINISHED"
        )

        debug(
            "=================================================="
        )

# ============================================================================
# UPDATE POLL
# ============================================================================

def _update_poll():

    global _updatePollTimer
    global _updateInfo
    global _updateInstallInProgress

    try:

        while True:

            try:

                result = _updateQueue.get_nowait()

            except Exception:

                break

            # --------------------------------------------------------------
            # QUEUE RESULT AUSPACKEN
            # --------------------------------------------------------------

            try:

                resultType, payload = result

            except Exception:

                print(
                    "[speedy_TheWeather] "
                    "UPDATE QUEUE: invalid result: %s"
                    % str(result)
                )

                continue

            print(
                "[speedy_TheWeather] "
                "UPDATE QUEUE RESULT: %s"
                % str(resultType)
            )

            # ==============================================================
            # UPDATE AVAILABLE
            # ==============================================================

            if resultType == "available":

                try:

                    if not isinstance(
                        payload,
                        dict
                    ):

                        print(
                            "[speedy_TheWeather] "
                            "UPDATE QUEUE: invalid available payload"
                        )

                        continue

                    remoteVersion = safeStr(
                        payload.get(
                            "version",
                            ""
                        )
                    )

                    changes = safeStr(
                        payload.get(
                            "changes",
                            ""
                        )
                    )

                    installerVersion = safeStr(
                        payload.get(
                            "installer_version",
                            ""
                        )
                    )

                    print(
                        "[speedy_TheWeather] "
                        "UPDATE AVAILABLE: %s"
                        % remoteVersion
                    )

                    _updateInfo = {
                        "version":
                            remoteVersion,

                        "changes":
                            changes,

                        "installer_version":
                            installerVersion
                    }

                    # ------------------------------------------------------
                    # UPDATE NUR ANZEIGEN, WENN KEINE INSTALLATION LÄUFT
                    # ------------------------------------------------------

                    if not _updateInstallInProgress:

                        try:

                            _update_show_message(
                                _updateInfo
                            )

                        except Exception as e:

                            print(
                                "[speedy_TheWeather] "
                                "Could not show update message: %s"
                                % e
                            )

                    else:

                        print(
                            "[speedy_TheWeather] "
                            "UPDATE AVAILABLE ignored because "
                            "installation is already running"
                        )

                except Exception as e:

                    print(
                        "[speedy_TheWeather] "
                        "ERROR handling update available: %s"
                        % e
                    )

                    try:

                        import traceback

                        print(
                            traceback.format_exc()
                        )

                    except Exception:

                        pass

            # ==============================================================
            # CURRENT / NO UPDATE
            # ==============================================================

            elif resultType == "current":

                try:

                    if isinstance(
                        payload,
                        dict
                    ):

                        currentVersion = safeStr(
                            payload.get(
                                "version",
                                ""
                            )
                        )

                    else:

                        currentVersion = safeStr(
                            payload
                        )

                    print(
                        "[speedy_TheWeather] "
                        "UPDATE CHECK: already current (%s)"
                        % currentVersion
                    )

                    # ------------------------------------------------------
                    # Nur bei manueller Prüfung anzeigen.
                    #
                    # Automatische Prüfungen sollen den Benutzer nicht
                    # ständig mit einer "bereits aktuell"-Meldung stören.
                    # ------------------------------------------------------

                    if (
                        currentVersion
                        and
                        _overlaySession is not None
                    ):

                        try:

                            _overlaySession.open(
                                MessageBox,
                                _(
                                    "You are already using the latest "
                                    "version (%s)."
                                ) % currentVersion,
                                MessageBox.TYPE_INFO
                            )

                        except Exception as e:

                            print(
                                "[speedy_TheWeather] "
                                "Could not show current-version "
                                "message: %s"
                                % e
                            )

                except Exception as e:

                    print(
                        "[speedy_TheWeather] "
                        "ERROR handling current update state: %s"
                        % e
                    )

                    try:

                        import traceback

                        print(
                            traceback.format_exc()
                        )

                    except Exception:

                        pass

            # ==============================================================
            # UPDATE CHECK ERROR
            # ==============================================================

            elif resultType == "error":

                try:

                    errorMessage = safeStr(
                        payload
                    )

                    if not errorMessage:

                        errorMessage = _(
                            "Could not check for updates."
                        )

                    print(
                        "[speedy_TheWeather] "
                        "UPDATE CHECK ERROR: %s"
                        % errorMessage
                    )

                    if _overlaySession is not None:

                        try:

                            _overlaySession.open(
                                MessageBox,
                                errorMessage,
                                MessageBox.TYPE_ERROR
                            )

                        except Exception as e:

                            print(
                                "[speedy_TheWeather] "
                                "Could not show update error: %s"
                                % e
                            )

                except Exception as e:

                    print(
                        "[speedy_TheWeather] "
                        "ERROR handling update error: %s"
                        % e
                    )

            # ==============================================================
            # INSTALLING
            # ==============================================================

            elif resultType == "installing":

                print(
                    "[speedy_TheWeather] "
                    "UPDATE INSTALLATION STARTED"
                )

                try:

                    _update_show_installing()

                except Exception as e:

                    print(
                        "[speedy_TheWeather] "
                        "Could not show installing message: %s"
                        % e
                    )

            # ==============================================================
            # INSTALLED
            # ==============================================================

            elif resultType == "installed":

                print(
                    "[speedy_TheWeather] "
                    "UPDATE INSTALLATION FINISHED"
                )

                try:

                    _update_install_finished()

                except Exception as e:

                    print(
                        "[speedy_TheWeather] "
                        "ERROR handling installed state: %s"
                        % e
                    )

            # ==============================================================
            # INSTALL ERROR
            # ==============================================================

            elif resultType == "install_error":

                print(
                    "[speedy_TheWeather] "
                    "UPDATE INSTALLATION FAILED"
                )

                try:

                    _update_install_error()

                except Exception as e:

                    print(
                        "[speedy_TheWeather] "
                        "ERROR handling install error: %s"
                        % e
                    )

            # ==============================================================
            # UNKNOWN MESSAGE
            # ==============================================================

            else:

                print(
                    "[speedy_TheWeather] "
                    "UPDATE QUEUE: unknown message type: %s"
                    % str(resultType)
                )

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "UPDATE POLL EXCEPTION: %s"
            % e
        )

        try:

            import traceback

            print(
                traceback.format_exc()
            )

        except Exception:

            pass

    finally:

        # ------------------------------------------------------------------
        # POLLER IMMER WEITERLAUFEN LASSEN
        # ------------------------------------------------------------------

        try:

            if _updatePollTimer is not None:

                _updatePollTimer.start(
                    500,
                    True
                )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "UPDATE POLL TIMER ERROR: %s"
                % e
            )

# ============================================================================
# START UPDATE WORKER
# ============================================================================

def _update_begin_worker():

    global _updatePollTimer
    global _updateWorkerStarted

    if _updateWorkerStarted:

        print(
            "[speedy_TheWeather] "
            "Update worker already running."
        )

        return

    _updateWorkerStarted = True

    try:

        # --------------------------------------------------------------------
        # CREATE POLL TIMER
        # --------------------------------------------------------------------

        if _updatePollTimer is None:

            _updatePollTimer = eTimer()

            safeTimerCallback(
                _updatePollTimer,
                _update_poll
            )

        else:

            try:

                _updatePollTimer.stop()

            except Exception:

                pass

        _updatePollTimer.start(
            500,
            True
        )

        # --------------------------------------------------------------------
        # START THREAD
        # --------------------------------------------------------------------

        thread = threading.Thread(
            target=_update_check_worker,
            name="speedy_TheWeather_UpdateCheck"
        )

        thread.daemon = True

        thread.start()

        print(
            "[speedy_TheWeather] "
            "GitHub update check started."
        )

    except Exception as e:

        _updateWorkerStarted = False

        print(
            "[speedy_TheWeather] "
            "Could not start update worker: %s"
            % e
        )

# ============================================================================
# START UPDATE CHECK
# ============================================================================

def _update_start_check():

    global _updateStartTimer
    global _updateCheckStarted

    # ----------------------------------------------------
    # Bereits geplant?
    # ----------------------------------------------------

    if _updateCheckStarted:

        print(
            "[speedy_TheWeather] "
            "Update check already scheduled."
        )

        return

    # ----------------------------------------------------
    # Automatischen Update-Check verzögert starten
    # ----------------------------------------------------

    try:

        _updateStartTimer = eTimer()

        safeTimerCallback(
            _updateStartTimer,
            _update_begin_worker
        )

        _updateStartTimer.start(
            UPDATE_CHECK_DELAY_MS,
            True
        )

        _updateCheckStarted = True

        print(
            "[speedy_TheWeather] "
            "Update check scheduled in %s ms."
            % UPDATE_CHECK_DELAY_MS
        )

    except Exception as e:

        _updateStartTimer = None

        _updateCheckStarted = False

        print(
            "[speedy_TheWeather] "
            "Could not start update timer: %s"
            % e
        )

# ============================================================================
# UPDATE AVAILABLE MESSAGE
# ============================================================================

def _update_show_message(info):

    remote_version = safeStr(
        info.get(
            "version",
            ""
        )
    ).strip()

    changes = safeStr(
        info.get(
            "changes",
            ""
        )
    ).strip()

    installer_version = safeStr(
        info.get(
            "installer_version",
            ""
        )
    ).strip()

    if not changes:

        changes = _(
            "No changes available."
        )

    installer_note = ""

    if installer_version:

        installer_note = (
            "\n"
            + _(
                "Installer version: %s"
            )
            % installer_version
        )

    try:

        installed_version = VERSION

    except Exception:

        installed_version = __version__

    message = (
        _(
            "A new version of speedy_TheWeather "
            "is available."
        )
        + "\n\n"
        + _(
            "Installed version: %s"
        )
        % installed_version
        + "\n"
        + _(
            "New version: %s"
        )
        % remote_version
        + installer_note
        + "\n\n"
        + _(
            "Changes:"
        )
        + "\n"
        + changes
        + "\n\n"
        + _(
            "Do you want to install the update?"
        )
    )

    print(
        "[speedy_TheWeather] "
        "Update version: %s"
        % remote_version
    )

    print(
        "[speedy_TheWeather] "
        "Installer version: %s"
        % installer_version
    )

    print(
        "[speedy_TheWeather] "
        "Update changes: %s"
        % changes
    )

    try:

        if _overlaySession is not None:

            _overlaySession.openWithCallback(
                _update_install_callback,
                MessageBox,
                message,
                MessageBox.TYPE_YESNO,
                default=True
            )

        else:

            print(
                "[speedy_TheWeather] "
                "No overlay session available."
            )

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "Could not show update dialog: %s"
            % e
        )

# ============================================================================
# UPDATE INSTALL CONFIRMATION
# ============================================================================

def _update_install_callback(answer):

    if answer:
        _update_install()

# ============================================================================
# UPDATE INSTALLING MESSAGE
# ============================================================================

def _update_show_installing():

    try:

        if _overlaySession is not None:

            _overlaySession.open(
                MessageBox,
                _(
                    "The update is being installed.\n\n"
                    "Please wait."
                ),
                MessageBox.TYPE_INFO,
                timeout=5
            )

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "Could not show install message: %s"
            % e
        )

# ============================================================================
# UPDATE INSTALL LOG
# ============================================================================

_UPDATE_INSTALL_LOG = "/tmp/speedy_update_install.log"

def _update_install_log(message):
    """Lightweight shared update-install logger; never breaks the update flow."""
    try:
        with open(_UPDATE_INSTALL_LOG, "a") as log_file:
            log_file.write("%s\\n" % message)
    except Exception:
        pass
    try:
        print("[speedy_TheWeather] %s" % message)
    except Exception:
        pass

# ============================================================================
# UPDATE INSTALL
# ============================================================================

def _update_install():

    global _updateInstallInProgress
    global _updateConsole

    if _updateInstallInProgress:

        print(
            "[speedy_TheWeather] "
            "Update installation already running."
        )

        return

    if not _updateInfo:

        print(
            "[speedy_TheWeather] "
            "No update information available."
        )

        return

    _updateInstallInProgress = True
    _updateConsole = None
    installLog = _UPDATE_INSTALL_LOG


    # ------------------------------------------------------------------------
    # LOG-FUNKTION
    # ------------------------------------------------------------------------

    # ------------------------------------------------------------------------
    # LOG NEU STARTEN
    # ------------------------------------------------------------------------

    try:

        with open(
            installLog,
            "w"
        ) as logFile:

            logFile.write(
                "speedy_TheWeather UPDATE INSTALL DEBUG\n"
            )

            logFile.write(
                "========================================\n"
            )

    except Exception:

        pass

    _update_install_log(
        "UPDATE INSTALL START"
    )

    _update_install_log(
        "Installer URL: %s"
        % UPDATE_INSTALLER_URL
    )

    _update_install_log(
        "Installer path: %s"
        % UPDATE_INSTALLER_PATH
    )

    # ------------------------------------------------------------------------
    # ALTES SUCCESS-MARKER ENTFERNEN
    # ------------------------------------------------------------------------

    try:

        if os.path.exists(
            UPDATE_SUCCESS_FILE
        ):

            os.unlink(
                UPDATE_SUCCESS_FILE
            )

            _update_install_log(
                "Old success marker removed."
            )

    except Exception as e:

        _update_install_log(
            "Could not remove old success marker: %s"
            % e
        )

    # ------------------------------------------------------------------------
    # ALTEN INSTALLER ENTFERNEN
    # ------------------------------------------------------------------------

    try:

        if os.path.exists(
            UPDATE_INSTALLER_PATH
        ):

            os.unlink(
                UPDATE_INSTALLER_PATH
            )

            _update_install_log(
                "Old installer removed."
            )

    except Exception as e:

        _update_install_log(
            "Could not remove old installer: %s"
            % e
        )

    # ------------------------------------------------------------------------
    # INSTALLER HERUNTERLADEN
    # ------------------------------------------------------------------------

    _update_install_log(
        "Downloading installer..."
    )

    try:

        downloadResult = _update_download(
            UPDATE_INSTALLER_URL,
            UPDATE_INSTALLER_PATH,
            timeout=UPDATE_DOWNLOAD_TIMEOUT
        )

    except Exception as e:

        _update_install_log(
            "Installer download exception: %s"
            % e
        )

        downloadResult = False

    _update_install_log(
        "Installer download result: %s"
        % downloadResult
    )

    if not downloadResult:

        _update_install_log(
            "INSTALLATION ABORTED: installer download failed."
        )

        _updateInstallInProgress = False

        try:

            _updateQueue.put(
                (
                    "install_error",
                    None
                )
            )

        except Exception:

            pass

        return

    # ------------------------------------------------------------------------
    # INSTALLER DATEI PRÜFEN
    # ------------------------------------------------------------------------

    if not os.path.isfile(
        UPDATE_INSTALLER_PATH
    ):

        _update_install_log(
            "INSTALLATION ABORTED: installer file does not exist."
        )

        _updateInstallInProgress = False

        try:

            _updateQueue.put(
                (
                    "install_error",
                    None
                )
            )

        except Exception:

            pass

        return

    try:

        installerSize = os.path.getsize(
            UPDATE_INSTALLER_PATH
        )

    except Exception:

        installerSize = 0

    _update_install_log(
        "Installer size: %d bytes"
        % installerSize
    )

    if installerSize <= 0:

        _update_install_log(
            "INSTALLATION ABORTED: installer file is empty."
        )

        _updateInstallInProgress = False

        try:

            _updateQueue.put(
                (
                    "install_error",
                    None
                )
            )

        except Exception:

            pass

        return

    # ------------------------------------------------------------------------
    # INSTALLER LESEN / PRÜFEN
    # ------------------------------------------------------------------------

    try:

        with open(
            UPDATE_INSTALLER_PATH,
            "r"
        ) as installerFile:

            installerContent = installerFile.read()

        _update_install_log(
            "Installer read test: OK"
        )

        try:

            firstLines = installerContent.splitlines()

            for line in firstLines[:10]:

                _update_install_log(
                    "INSTALLER: %s"
                    % line
                )

        except Exception:

            pass

    except Exception as e:

        _update_install_log(
            "INSTALLATION ABORTED: could not read installer: %s"
            % e
        )

        _updateInstallInProgress = False

        try:

            _updateQueue.put(
                (
                    "install_error",
                    None
                )
            )

        except Exception:

            pass

        return

    # ------------------------------------------------------------------------
    # CHMOD
    # ------------------------------------------------------------------------

    try:

        os.chmod(
            UPDATE_INSTALLER_PATH,
            0o755
        )

        _update_install_log(
            "chmod 0755: OK"
        )

    except Exception as e:

        _update_install_log(
            "INSTALLATION ABORTED: chmod failed: %s"
            % e
        )

        _updateInstallInProgress = False

        try:

            _updateQueue.put(
                (
                    "install_error",
                    None
                )
            )

        except Exception:

            pass

        return

    # ------------------------------------------------------------------------
    # BASH PRÜFEN
    # ------------------------------------------------------------------------

    bashPath = "/bin/bash"

    if not os.path.isfile(
        bashPath
    ):

        _update_install_log(
            "INSTALLATION ABORTED: /bin/bash not found."
        )

        _updateInstallInProgress = False

        try:

            _updateQueue.put(
                (
                    "install_error",
                    None
                )
            )

        except Exception:

            pass

        return

    if not os.access(
        bashPath,
        os.X_OK
    ):

        _update_install_log(
            "INSTALLATION ABORTED: /bin/bash is not executable."
        )

        _updateInstallInProgress = False

        try:

            _updateQueue.put(
                (
                    "install_error",
                    None
                )
            )

        except Exception:

            pass

        return

    _update_install_log(
        "/bin/bash: OK"
    )

    # ------------------------------------------------------------------------
    # ENIGMA2 SESSION PRÜFEN
    # ------------------------------------------------------------------------

    if _overlaySession is None:

        _update_install_log(
            "INSTALLATION ABORTED: no active Enigma2 session."
        )

        _updateInstallInProgress = False

        try:

            _updateQueue.put(
                (
                    "install_error",
                    None
                )
            )

        except Exception:

            pass

        return

    _update_install_log(
        "Enigma2 session: OK"
    )

    # ------------------------------------------------------------------------
    # INSTALLING STATUS AN QUEUE
    # ------------------------------------------------------------------------

    try:

        _updateQueue.put(
            (
                "installing",
                None
            )
        )

    except Exception as e:

        _update_install_log(
            "Could not queue installing message: %s"
            % e
        )

    # ------------------------------------------------------------------------
    # INSTALLER COMMAND
    #
    # KEIN tee
    # KEINE Umleitung der Installer-Ausgabe in die Logdatei
    #
    # Die komplette stdout/stderr-Ausgabe geht direkt an die
    # Enigma2 Console und ist dadurch live sichtbar.
    #
    # Der Success-Marker wird ausschließlich erzeugt, wenn
    # der Installer mit Exit-Code 0 beendet wurde.
    # ------------------------------------------------------------------------

    cmd = (
        "export LANG=C; "
        "export LC_ALL=C; "
        "/bin/bash \"%s\"; "
        "status=$?; "
        "if [ \"$status\" -eq 0 ]; then "
        "/bin/touch \"%s\"; "
        "fi; "
        "exit \"$status\""
        % (
            UPDATE_INSTALLER_PATH,
            UPDATE_SUCCESS_FILE
        )
    )

    _update_install_log(
        "Installer command:"
    )

    _update_install_log(
        cmd
    )

    _update_install_log(
        "Starting Enigma2 Console..."
    )

    # ------------------------------------------------------------------------
    # ENIGMA2 CONSOLE ÖFFNEN
    # ------------------------------------------------------------------------

    try:

        _updateConsole = _overlaySession.open(
            Console,
            _("Updating..."),
            cmdlist=[
                cmd
            ],
            finishedCallback=update_finished,
            closeOnSuccess=True
        )

        _update_install_log(
            "Enigma2 Console opened successfully."
        )

    except Exception as e:

        _updateConsole = None
        _updateInstallInProgress = False

        _update_install_log(
            "INSTALL EXCEPTION: %s"
            % e
        )

        try:

            import traceback

            _update_install_log(
                traceback.format_exc()
            )

        except Exception:

            pass

        try:

            _updateQueue.put(
                (
                    "install_error",
                    None
                )
            )

        except Exception:

            pass

# ============================================================================
# UPDATE FINISHED
# ============================================================================

def update_finished():

    global _updateConsole
    global _updateInstallInProgress
    global _updateRestartTimer


    # ------------------------------------------------------------------------
    # SUCCESS MARKER PRÜFEN
    # ------------------------------------------------------------------------

    success = os.path.exists(
        UPDATE_SUCCESS_FILE
    )

    _update_install_log(
        "Update success marker: %s"
        % success
    )

    # ------------------------------------------------------------------------
    # SUCCESS
    # ------------------------------------------------------------------------

    if success:

        _update_install_log(
            "UPDATE INSTALLATION SUCCESS"
        )

        _updateInstallInProgress = False

        # --------------------------------------------------------------------
        # INSTALLER LÖSCHEN
        # --------------------------------------------------------------------

        try:

            if os.path.exists(
                UPDATE_INSTALLER_PATH
            ):

                os.unlink(
                    UPDATE_INSTALLER_PATH
                )

                _update_install_log(
                    "Installer removed."
                )

        except Exception as e:

            _update_install_log(
                "Could not remove installer: %s"
                % e
            )

        # --------------------------------------------------------------------
        # SUCCESS MARKER LÖSCHEN
        # --------------------------------------------------------------------

        try:

            if os.path.exists(
                UPDATE_SUCCESS_FILE
            ):

                os.unlink(
                    UPDATE_SUCCESS_FILE
                )

                _update_install_log(
                    "Success marker removed."
                )

        except Exception as e:

            _update_install_log(
                "Could not remove success marker: %s"
                % e
            )

        # --------------------------------------------------------------------
        # ALTEN RESTART TIMER STOPPEN
        # --------------------------------------------------------------------

        try:

            if _updateRestartTimer is not None:

                try:

                    _updateRestartTimer.stop()

                except Exception:

                    pass

                _updateRestartTimer = None

        except Exception:

            pass

        # --------------------------------------------------------------------
        # RESTART TIMER ERSTELLEN
        # --------------------------------------------------------------------

        try:

            _updateRestartTimer = eTimer()

            def show_restart_message():

                global _updateRestartTimer

                try:

                    if _updateRestartTimer is not None:

                        _updateRestartTimer.stop()

                except Exception:

                    pass

                _updateRestartTimer = None

                try:

                    _update_install_finished()

                except Exception as e:

                    print(
                        "[speedy_TheWeather] "
                        "Could not finish update: %s"
                        % e
                    )

            safeTimerCallback(
                _updateRestartTimer,
                show_restart_message
            )

            _updateRestartTimer.start(
                200,
                True
            )

            _update_install_log(
                "Restart message timer started."
            )

        except Exception as e:

            _update_install_log(
                "Could not start restart timer: %s"
                % e
            )

            _updateRestartTimer = None

            try:

                _update_install_finished()

            except Exception as e:

                _update_install_log(
                    "Could not show restart message: %s"
                    % e
                )

        return

    # ------------------------------------------------------------------------
    # FAILURE
    # ------------------------------------------------------------------------

    _update_install_log(
        "UPDATE INSTALLATION FAILED"
    )

    _updateInstallInProgress = False

    _update_install_log(
        "Installer retained for diagnostic purposes:"
    )

    _update_install_log(
        UPDATE_INSTALLER_PATH
    )

    # ------------------------------------------------------------------------
    # SUCCESS MARKER AUFRÄUMEN
    # ------------------------------------------------------------------------

    try:

        if os.path.exists(
            UPDATE_SUCCESS_FILE
        ):

            os.unlink(
                UPDATE_SUCCESS_FILE
            )

            _update_install_log(
                "Failure success marker removed."
            )

    except Exception as e:

        _update_install_log(
            "Could not remove failure success marker: %s"
            % e
        )

    # ------------------------------------------------------------------------
    # FEHLER NUR EINMAL AN QUEUE SENDEN
    # ------------------------------------------------------------------------

    try:

        _updateQueue.put(
            (
                "install_error",
                None
            )
        )

        _update_install_log(
            "Install error queued."
        )

    except Exception as e:

        _update_install_log(
            "Could not queue install error: %s"
            % e
        )

# ============================================================================
# SUCCESSFUL UPDATE
# ============================================================================

def _update_install_finished():

    global _updateInstallInProgress
    global _updateInfo

    _updateInstallInProgress = False
    _updateInfo = None

    print(
        "[speedy_TheWeather] "
        "Update installation finished successfully."
    )

    # ------------------------------------------------------------------------
    # RESTART CALLBACK
    # ------------------------------------------------------------------------

    def restart_gui_callback(answer):

        if answer:

            print(
                "[speedy_TheWeather] "
                "User chose to restart Enigma2 GUI."
            )

            try:

                from enigma import quitMainloop

                quitMainloop(
                    3
                )

            except Exception as e:

                print(
                    "[speedy_TheWeather] "
                    "Could not restart Enigma2 GUI: %s"
                    % e
                )

        else:

            print(
                "[speedy_TheWeather] "
                "User chose NOT to restart Enigma2 GUI."
            )

    # ------------------------------------------------------------------------
    # ASK USER
    # ------------------------------------------------------------------------

    try:

        if _overlaySession is not None:

            _overlaySession.openWithCallback(
                restart_gui_callback,
                MessageBox,
                _(
                    "The update has been installed successfully.\n\n"
                    "Would you like to restart the Enigma2 GUI now?"
                ),
                MessageBox.TYPE_YESNO,
                default=True
            )

        else:

            print(
                "[speedy_TheWeather] "
                "No overlay session available."
            )

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "Could not show update restart question: %s"
            % e
        )

# ============================================================================
# UPDATE INSTALL ERROR
# ============================================================================

def _update_install_error():

    global _updateInstallInProgress
    global _updateInfo

    _updateInstallInProgress = False
    _updateInfo = None

    # ------------------------------------------------------------------------
    # CLEANUP SUCCESS MARKER
    # ------------------------------------------------------------------------

    try:

        if os.path.exists(
            UPDATE_SUCCESS_FILE
        ):

            os.unlink(
                UPDATE_SUCCESS_FILE
            )

    except Exception:

        pass

    # ------------------------------------------------------------------------
    # CLEANUP INSTALLER
    # ------------------------------------------------------------------------

    try:

        if os.path.exists(
            UPDATE_INSTALLER_PATH
        ):

            os.unlink(
                UPDATE_INSTALLER_PATH
            )

    except Exception:

        pass

    # ------------------------------------------------------------------------
    # ERROR MESSAGE
    # ------------------------------------------------------------------------

    try:

        if _overlaySession is not None:

            _overlaySession.open(
                MessageBox,
                _(
                    "The update could not be installed.\n\n"
                    "Please check the Internet connection "
                    "and try again."
                ),
                MessageBox.TYPE_ERROR
            )

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "Could not show update error: %s"
            % e
        )

# WICHTIG: Domain an den Dateinamen 'speedy_TheWeather.mo' anpassen!
# Alle festen Update-Dialogtexte sind mit _() markiert und damit über
# die vorhandenen .po/.mo-Dateien übersetzbar.
icoonpath = "Images"
SHARED_PACK = "Images"
backgroundpath = ""
CFG_DIR = "/etc/enigma2/speedy_TheWeather"

def _detectCanvasWidth():
    try:
        return getDesktop(0).size().width()
    except Exception:
        return 1920

weatherData = []
screens = []
_restartTimer = None
_restartTimerConn = None
_restartInProgress = False
_overlayScreen = None
_overlayEnabled = False
_overlayInfoscreenOpen = False
_overlaySession = None
OVERLAY_CFG = CFG_DIR + "/speedy_TheWeather_overlay.cfg"

# Asynchroner Plugin-Start: kein Wetter-HTTP im Enigma2-Hauptthread.
_startupWeatherQueue = queue.Queue()
_startupWeatherTimer = None
_startupWeatherRunning = False

def _readOverlayConfig():
    try:
        with open(OVERLAY_CFG) as f:
            return f.read().strip() == "1"
    except Exception:
        return False

_overlay_last_width = None
_overlay_z_set = False

def _overlayCheckVisibility():
    global _overlayScreen, _overlayEnabled, _overlaySession
    global _overlay_last_width, _overlay_z_set
    if _overlayScreen is None:
        return
    try:
        cur_w = _detectCanvasWidth()
        if _overlayScreen.instance:
            if cur_w != _overlay_last_width:
                try:
                    _overlayScreen.instance.move(ePoint(cur_w - 125, 0))
                    _overlay_last_width = cur_w
                except Exception:
                    pass
            if not _overlay_z_set:
                try:
                    _overlayScreen.instance.setZPosition(1000)
                    _overlay_z_set = True
                except Exception:
                    pass
        liveTv = False
        try:
            liveTv = InfoBar.instance is not None
        except Exception:
            liveTv = False
        topScreen = screens[-1] if screens else None
        topIsInfoscreen = isinstance(topScreen, infoscreen)
        anyPluginScreenOpen = len(screens) > 0

        systemMenuOpen = False
        try:
            if _overlaySession is not None:
                cd = _overlaySession.current_dialog
                if cd is not None and cd is not InfoBar.instance:
                    systemMenuOpen = True
        except Exception as e:
            print("[speedy_TheWeather] systemMenuOpen check fout:", e)

        if _overlayEnabled and (topIsInfoscreen or (liveTv and not anyPluginScreenOpen and not systemMenuOpen)):
            _overlayScreen.show()
        else:
            _overlayScreen.hide()
    except Exception as e:
        print("[speedy_TheWeather] _overlayCheckVisibility: fout:", e)

def _doIconpackRestart(session):
    main(session)

def _updateOverlayFromWeatherData():
    global _overlayScreen
    if _overlayScreen is None:
        return
    try:
        now_hour = datetime.datetime.now().hour
        hours = weatherData["days"][0].get("hours", [])

        temp = None

        for hourdata in hours:
            try:
                hour = int(hourdata.get("hour"))
            except (TypeError, ValueError):
                continue

            # Normale Stunden: 0-23
            if hour == now_hour:
                temp = hourdata.get("temperature")
                break

            # Falls Buienradar 1-24 verwendet:
            # 00:00 Uhr entspricht dann 24
            if now_hour == 0 and hour == 24:
                temp = hourdata.get("temperature")
                break

        # Fallback auf den ersten Stundenwert
        if temp is None and hours:
            temp = hours[0].get("temperature")

        if temp is not None:
            _overlayScreen["overlay_temp"].setText(
                "%s\xb0C" % int(round(float(temp)))
            )

    except Exception as e:
        print("[speedy_TheWeather] _updateOverlayFromWeatherData: fout:", e)

SavedLokaleWeer = []
lockaaleStad = ""
citynamedisplay = ""

sz_w = getDesktop(0).size().width()
sz_h = getDesktop(0).size().height()

HTTP_TIMEOUT = 15
HTTP_USER_AGENT = 'speedy_TheWeather-Enigma2Plugin/4.0'
HTTP_HEADERS = {
    'User-Agent': HTTP_USER_AGENT,
    'Accept': 'application/json,text/plain,*/*'
}
_weatherCache = {}
_weatherCacheLock = threading.RLock()
_WEATHER_CACHE_TTL = 5 * 60
_WEATHER_CACHE_MAX = 12

# Shared, bounded caches. They are deliberately small because Enigma2 receivers
# often have limited RAM/flash compared with a desktop system.
_ICON_CACHE = OrderedDict()
_ICON_CACHE_MAX = 96
_TILE_CACHE_TTL = 30 * 60
_TILE_CACHE_LOCK = threading.RLock()
_TILE_CACHE_DIR = "/tmp/speedy_TheWeather/cache"
# Low-End defaults are intentionally conservative. The actual worker count,
# frame count and decode pacing are selected per receiver in RadarScreen.
# Performance profile.  The GUI thread is deliberately given a large
# breathing margin on weak receivers.  One PNG decode at a time is much
# more important than shaving a few seconds from the initial download.
_RADAR_MAX_WORKERS = 2
_RADAR_ULTRA_WORKERS = 1
_RADAR_LOW_WORKERS = 1
_RADAR_NORMAL_WORKERS = 2
_RADAR_ULTRA_FRAME_COUNT = 3
_RADAR_LOW_FRAME_COUNT = 4
_RADAR_NORMAL_FRAME_COUNT = 5
_RADAR_ULTRA_DECODE_DELAY_MS = 85
_RADAR_LOW_DECODE_DELAY_MS = 60
_RADAR_NORMAL_DECODE_DELAY_MS = 30
_RADAR_ULTRA_ANIM_MS = 2600
_RADAR_LOW_ANIM_MS = 2100
_RADAR_NORMAL_ANIM_MS = 1500
_RADAR_POLL_INTERVAL_MS = 350

def _cache_file_for_url(url):
    import hashlib
    digest = hashlib.md5(safeStr(url).encode("utf-8")).hexdigest()
    return os.path.join(_TILE_CACHE_DIR, digest + ".png")

def _ensure_cache_dir():
    try:
        if not os.path.isdir(_TILE_CACHE_DIR):
            os.makedirs(_TILE_CACHE_DIR)
    except OSError:
        pass

def _load_cached_png(path):
    """Load one valid cached PNG. Never decode an expired cache entry."""
    if not path:
        return None
    try:
        stat = os.stat(path)
        if (
            stat.st_size <= 0
            or time.time() - stat.st_mtime > _TILE_CACHE_TTL
        ):
            return None
        return loadPNG(path)
    except Exception:
        return None

def _load_icon_cached(path):
    if not path:
        return None
    try:
        cached = _ICON_CACHE.get(path)
        if cached is not None:
            try:
                _ICON_CACHE.move_to_end(path)
            except AttributeError:
                pass
            return cached
        pix = loadPNG(path)
        if pix is not None:
            if len(_ICON_CACHE) >= _ICON_CACHE_MAX:
                try:
                    _ICON_CACHE.popitem(last=False)
                except TypeError:
                    _ICON_CACHE.pop(next(iter(_ICON_CACHE)))
            _ICON_CACHE[path] = pix
        return pix
    except Exception:
        return None

def _http_get(url, timeout=HTTP_TIMEOUT, headers=None):
    req_headers = dict(HTTP_HEADERS)
    if headers:
        req_headers.update(headers)
    req = Request(url, data=None, headers=req_headers)
    response = None
    try:
        response = urlopen(req, timeout=timeout)
        return response.read()
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass

def _http_json(url, timeout=HTTP_TIMEOUT, headers=None):
    try:
        raw = _http_get(url, timeout, headers)
        if not raw:
            return None
        if PY3 and isinstance(raw, bytes):
            raw = raw.decode('utf-8', 'replace')
        return json.loads(raw)
    except (HTTPError, URLError, ValueError, IOError, OSError) as e:
        print('[speedy_TheWeather] HTTP/JSON error:', e)
    except Exception as e:
        print('[speedy_TheWeather] unexpected HTTP error:', e)
    return None

def _weather_cache_get(key):
    now = time.time()
    with _weatherCacheLock:
        item = _weatherCache.get(key)
        if item and now - item[0] < _WEATHER_CACHE_TTL:
            return item[1]
    return None

def _weather_cache_put(key, data):
    with _weatherCacheLock:
        _weatherCache[key] = (time.time(), data)
        if len(_weatherCache) > _WEATHER_CACHE_MAX:
            oldest = min(_weatherCache.items(), key=lambda item: item[1][0])[0]
            _weatherCache.pop(oldest, None)

def _get_weather_by_city_id(city_id):
    try:
        city_id = int(city_id)
    except (TypeError, ValueError):
        return None
    key = 'id:%s' % city_id
    cached = _weather_cache_get(key)
    if cached is not None:
        return cached
    data = _http_json('http://api.buienradar.nl/data/forecast/1.1/all/%s' % city_id)
    if data is not None:
        _weather_cache_put(key, data)
    return data

def _search_city(query):
    try:
        query = safeStr(query).strip()

        print(
            "[speedy_TheWeather] CITY SEARCH: query=%r"
            % query
        )

        if not query:
            return None, None

        # ----------------------------------------
        # Eingabe:
        #
        # Berlin
        # Berlin(DE)
        # Berlin_DE
        # ----------------------------------------

        city = query
        country = ""

        if "(" in query and query.endswith(")"):
            city, country = query.rsplit("(", 1)
            city = city.strip()
            country = country[:-1].strip().lower()

        elif "_" in query:
            city, country = query.split("_", 1)
            city = city.strip()
            country = country.strip().lower()

        if not city:
            return None, None

        print(
            "[speedy_TheWeather] CITY SEARCH: "
            "city=%r country=%r"
            % (city, country)
        )

        # ----------------------------------------
        # Buienradar Location Search
        # ----------------------------------------

        url = (
            "https://location.buienradar.nl/1.1/location/search"
            "?query="
            + quote_plus(city)
        )

        print(
            "[speedy_TheWeather] CITY SEARCH URL: %s"
            % url
        )

        results = _http_json(url)

        print(
            "[speedy_TheWeather] CITY SEARCH RESULTS: %r"
            % results
        )

        if not isinstance(results, list):
            print(
                "[speedy_TheWeather] CITY SEARCH: "
                "Ergebnis ist keine Liste"
            )
            return None, None

        if not results:
            print(
                "[speedy_TheWeather] CITY SEARCH: "
                "keine Treffer"
            )
            return None, None

        # ----------------------------------------
        # passenden Treffer auswählen
        # ----------------------------------------

        selected = results[0]

        if country:

            for item in results:

                item_country = safeStr(
                    item.get(
                        "countrycode",
                        ""
                    )
                ).strip().lower()

                if item_country == country:
                    selected = item
                    break

        print(
            "[speedy_TheWeather] CITY SEARCH SELECTED: %r"
            % selected
        )

        city_id = selected.get("id")

        print(
            "[speedy_TheWeather] CITY SEARCH CITY_ID: %r"
            % city_id
        )

        if city_id is None:
            print(
                "[speedy_TheWeather] CITY SEARCH: "
                "keine City-ID"
            )
            return None, None

        # ----------------------------------------
        # Wetter über vorhandene Funktion laden
        # ----------------------------------------

        data = _get_weather_by_city_id(
            city_id
        )

        print(
            "[speedy_TheWeather] CITY WEATHER DATA: %s"
            % (
                "OK"
                if data is not None
                else "NONE"
            )
        )

        if data is None:
            print(
                "[speedy_TheWeather] CITY SEARCH: "
                "Wetterdaten nicht gefunden"
            )
            return None, None

        # ----------------------------------------
        # Anzeigename
        # ----------------------------------------

        name = "%s(%s)" % (
            selected.get(
                "name",
                city
            ),
            selected.get(
                "countrycode",
                ""
            )
        )

        print(
            "[speedy_TheWeather] CITY SEARCH OK: %s"
            % name
        )

        return data, name

    except Exception as e:

        print(
            "[speedy_TheWeather] CITY SEARCH ERROR: %s"
            % str(e)
        )

        try:
            import traceback
            traceback.print_exc()
        except Exception:
            pass

        return None, None

def getLocWeer(iscity=None, update_overlay=True):
    global weatherData, lockaaleStad, citynamedisplay
    lockaaleStad = iscity
    if not iscity:
        return False
    entry = stripCoords(iscity)
    try:
        parts = entry.rsplit('-', 1)
        if len(parts) == 2:
            data = _get_weather_by_city_id(parts[1])
            if data is not None:
                weatherData = data
                citynamedisplay = safeStr(parts[0])
                if update_overlay:
                    _updateOverlayFromWeatherData()
                return True
    except Exception as e:
        print('[speedy_TheWeather] city-id lookup failed:', e)
    data, name = _search_city(entry)
    if data is None:
        return False
    weatherData = data
    citynamedisplay = safeStr(name)
    if update_overlay:
        _updateOverlayFromWeatherData()
    return True

def getLocWeerFor(inputCity):
    """Return actual weather data and display name for a saved city."""
    inputCity = stripCoords(inputCity)

    try:
        parts = inputCity.rsplit("-", 1)
        if len(parts) == 2:
            citynumb = int(parts[1])
            data = _get_weather_by_city_id(citynumb)
            if data is not None:
                return data, str(parts[0]).strip()
    except (TypeError, ValueError, IndexError):
        pass
    except Exception as e:
        print("[speedy_TheWeather] getLocWeerFor city-id error: %s" % e)

    # Fallback for old config entries without a numeric city id.
    # _search_city() liefert echte Wetterdaten und nicht nur Such-Metadaten.
    try:
        data, name = _search_city(inputCity)
        if data is not None and name:
            return data, name
    except Exception as e:
        print("[speedy_TheWeather] getLocWeerFor fallback error: %s" % e)

    return None


def icontotext(icon):
    text = ""
    if icon == "a":
        text = _("Sunny / Clear")
    elif icon == "aa":
        text = _("Clear night")
    elif icon == "b":
        text = _("Sunny few clouds")
    elif icon == "bb":
        text = _("Light cloudy")
    elif icon == "c":
        text = _("Heavy clouds")
    elif icon == "cc":
        text = _("Heavy clouds")
    elif icon == "d":
        text = _("Changeable and chance of mist")
    elif icon == "dd":
        text = _("Changeable and chance of mist")
    elif icon == "f":
        text = _("Sunny and chance of showers")
    elif icon == "ff":
        text = _("Cloudy and chance of showers")
    elif icon == "g":
        text = _("Sunny and chance of thundershowers")
    elif icon == "gg":
        text = _("Showers and chance of thunder")
    elif icon == "j":
        text = _("Mostly sunny")
    elif icon == "jj":
        text = _("Mostly clear")
    elif icon == "m":
        text = _("Heavy clouds showers possible")
    elif icon == "mm":
        text = _("Heavy clouds showers possible")
    elif icon == "n":
        text = _("Sunny and chance of mist")
    elif icon == "nn":
        text = _("Clear and chance of mist")
    elif icon == "q":
        text = _("Heavy clouds  heavy showers")
    elif icon == "qq":
        text = _("Heavy clouds  heavy showers")
    elif icon == "r":
        text = _("Cloudy")
    elif icon == "rr":
        text = _("Cloudy")
    elif icon == "s":
        text = _("Heavy clouds  thundershowers")
    elif icon == "ss":
        text = _("Heavy clouds  thundershowers")
    elif icon == "t":
        text = _("Heavy clouds and heavy snowfall")
    elif icon == "tt":
        text = _("Heavy clouds and heavy snowfall")
    elif icon == "u":
        text = _("Changeable cloudy light snowfall")
    elif icon == "uu":
        text = _("Changeable cloudy light snowfall")
    elif icon == "v":
        text = _("Heavy clouds light snowfall")
    elif icon == "vv":
        text = _("Heavy clouds light snowfall")
    elif icon == "w":
        text = _("Heavy clouds winter rainfall")
    elif icon == "ww":
        text = _("Heavy clouds winter rainfall")
    else:
        text = _("No info")
    return text

def winddirtext(dirtext):
    text = ""
    if dirtext == "N":
        text = _("N")
    elif dirtext == "NO":
        text = _("NE")
    elif dirtext == "O":
        text = _("E")
    elif dirtext == "ZO":
        text = _("SE")
    elif dirtext == "Z":
        text = _("S")
    elif dirtext == "ZW":
        text = _("SW")
    elif dirtext == "W":
        text = _("W")
    elif dirtext == "NW":
        text = _("NW")
    return text

def kmh_to_beaufort(kmh):

    try:
        kmh = float(kmh)
    except (TypeError, ValueError):
        return None
    thresholds = [1, 6, 12, 20, 29, 39, 50, 62, 75, 89, 103, 118]
    for bft, upper in enumerate(thresholds):
        if kmh < upper:
            return bft
    return 12

def getDateFormat():
    try:
        if config.plugins.speedy_TheWeather.dateformat.value == "dot":
            return "Format:%a %d.%m.%y"
    except Exception:
        pass
    return "Format:%a %d/%m/%y"

def format_windspeed(kmh):
    try:
        value = float(kmh)
    except (TypeError, ValueError):
        return "--"
    try:
        if config.plugins.speedy_TheWeather.windunit.value == "ms":
            return "%.1f m/s" % (value / 3.6)
    except Exception:
        pass
    return "%.1f km/h" % value

def windspeed_with_beaufort(kmh):
    bft = kmh_to_beaufort(kmh)
    speed = format_windspeed(kmh)
    if bft is None:
        return speed
    return "%s (Bft %s)" % (speed, bft)

def localWeatherAlert(dayData):

    if not dayData:
        return "", ""

    try:
        windkmh = float(dayData.get("windspeed", 0) or 0)
    except (TypeError, ValueError):
        windkmh = 0
    try:
        rainmm = float(dayData.get("precipitationmm", 0) or 0)
    except (TypeError, ValueError):
        rainmm = 0
    try:
        feeltemp = float(dayData.get("feeltemperature", dayData.get("maxtemperature", 0)) or 0)
    except (TypeError, ValueError):
        feeltemp = 0

    bft = kmh_to_beaufort(windkmh)
    kandidaten = []

    # Wind: from Bft 7 (near gale)
    if bft is not None and bft >= 9:
        kandidaten.append((3, "red", _("Heavy storm!")))
    elif bft is not None and bft >= 7:
        kandidaten.append((2, "orange", _("Strong wind!")))

    # Precipitation
    if rainmm >= 30:
        kandidaten.append((3, "red", _("Very heavy rain!")))
    elif rainmm >= 15:
        kandidaten.append((2, "orange", _("Heavy rain!")))

    # Heat (yellow/orange/red)
    if feeltemp >= 35:
        kandidaten.append((3, "red", _("Extreme heat!")))
    elif feeltemp >= 30:
        kandidaten.append((2, "orange", _("Warm weather!")))

    # Cold (blue, separate scale independent of the red/orange/yellow chain)
    if feeltemp <= -15:
        kandidaten.append((3, "blue", _("Extreme cold!")))
    elif feeltemp <= -8:
        kandidaten.append((2, "blue", _("Severe cold!")))

    if not kandidaten:
        return "", ""

    # Highest priority wins; in case of equal priority: red > orange > blue > yellow
    kleur_volgorde = {"red": 3, "orange": 2, "blue": 1, "yellow": 0}
    kandidaten.sort(key=lambda k: (k[0], kleur_volgorde.get(k[1], 0)), reverse=True)
    _prio, kleur, tekst = kandidaten[0]
    return kleur, tekst

def checkInternet():
    try:
        data = _http_json('https://location.buienradar.nl/1.1/location/search?query=Amsterdam', timeout=5)
        return isinstance(data, list) and len(data) > 0
    except Exception as e:
        print('[speedy_TheWeather] connectivity check failed:', e)
        return False

class sevendays(Screen):

    # ================================================================
    # TEXTFARBEN
    # ================================================================

    # Aktuelles Wetter
    COLOR_CITY        = "#0000ff00"
    COLOR_BIGTEMP     = "#000000ff"
    COLOR_WEATHERTYPE = "#00ff0000"
    COLOR_FEELS       = "#00ffff00"
    COLOR_WIND        = "#0000ffff"

    # 7-Tage-Vorhersage
    COLOR_DAY         = "#0000ff00"
    COLOR_MAXTEMP     = "#00ff0000"
    COLOR_MINTEMP     = "#00004080"
    COLOR_DAYTYPE     = "#00ffff00"

    # Sonne / Mond
    COLOR_SUN         = "#00ffff00"
    COLOR_SUNRISE     = "#00ffff00"
    COLOR_SUNSET      = "#00ffff00"
    COLOR_MOONRISE    = "#00ffff00"
    COLOR_MOONSET     = "#00ffff00"

    # Stundenübersicht
    COLOR_HOUR        = "#00ff0000"
    COLOR_HOURTEMP    = "#004080ff"
    COLOR_RAIN        = "#0000ff00"
    COLOR_SUNPERCENT  = "#00ffff00"
    COLOR_HUMIDITY    = "#004080ff"
    COLOR_WIND_SPEED  = "#0000ffff"

    # Uhr / Datum
    COLOR_CLOCK       = "#00ff0000"
    COLOR_DATE        = "#0000ff00"

    # Alert
    COLOR_ALERT      = "#00ff0000"

    # ================================================================
    # PFAD
    # ================================================================

    WEATHER_PATH = (
        "/usr/lib/enigma2/python/Plugins/Extensions/"
        "speedy_TheWeather"
    )

    # ================================================================
    # INITIALISIERUNG
    # ================================================================

    def __init__(self, session):

        Screen.__init__(
            self,
            session
        )

        AddNewScreen(self)

        self.onClose.append(
            lambda: RemoveScreen(self)
        )

        global weatherData

        data = weatherData.get(
            "days",
            []
        )

        self.selected = 0
        self.hourStep = 1

        # ============================================================
        # OBERER WINDPFEIL
        # ============================================================

        winddir_top = (
            self._wind(data[0])
            if data
            else "na"
        )

        # ============================================================
        # TEMPERATURBILD
        # ============================================================

        tempicon = self._temp_picture(
            data
        )

        # ============================================================
        # FARBEN
        # ============================================================

        try:

            self._loadSevenDayColors()

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "_loadSevenDayColors Fehler:",
                repr(e)
            )

        # ============================================================
        # SKIN
        # ============================================================

        self.skin = self._build_skin(
            data,
            winddir_top,
            tempicon
        )

        # ============================================================
        # DATUMSFORMAT
        # ============================================================

        try:

            date_format = getDateFormat()

            for old in (
                "Format:%a %d/%m/%y",
                "Format:%a %d.%m",
                "Format:%a %d.%m.%y"
            ):

                self.skin = self.skin.replace(
                    old,
                    date_format
                )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "date format replacement failed:",
                repr(e)
            )

        # ============================================================
        # ALLGEMEINE WIDGETS
        # ============================================================

        self["city1"] = StaticText()

        self["city1"].text = str(
            citynamedisplay
        )

        for name in (
            "bigtemp1",
            "bigweathertype1",
            "GevoelsTemp1",
            "winddir1"
        ):

            self[name] = StaticText()

        for name in (
            "winddiricon1",
            "weatheralertbg1",
            "weatheralerticon1"
        ):

            self[name] = Pixmap()

        self["weatheralert1"] = Label("")

        self["yellowdot"] = MovingPixmap()

        self["bgpic"] = Pixmap()

        # ============================================================
        # HINTERGRUND
        # ============================================================

        try:

            self.picload = ePicLoad()

            self._picload_conn = safeSignalConnect(
                self.picload.PictureData,
                self.bgPictureLoaded
            )

            self.loadBackground()

        except Exception as e:

            print(
                "speedy_TheWeather: "
                "ePicLoad niet beschikbaar, "
                "standard Hintergrund:",
                repr(e)
            )

            self.picload = None

        # ============================================================
        # STUNDEN-WIDGETS
        # ============================================================

        defaults = {
            "dayhour3": "00h",
            "daytemp3": "--\xb0C",
            "sunpercent3": "--%",
            "daypercent3": "--%",
            "hrdayper3": "--%",
            "dayspeed3": "--Km/h"
        }

        for hour in range(8):

            for prefix, value in defaults.items():

                self._label(
                    "{}{}".format(
                        prefix,
                        hour
                    ),
                    value
                )

        # ============================================================
        # 7 TAGE
        # ============================================================

        for day in range(7):

            self._set_day(
                day,
                self._day(
                    data,
                    day
                )
            )

        # ============================================================
        # SONNE
        # ============================================================

        sunrise = "--"
        sunset = "--"

        try:

            sunrise, sunset = self._sun(
                data
            )

            if not sunrise or sunrise == "na":
                sunrise = "--"

            if not sunset or sunset == "na":
                sunset = "--"

            print(
                "[speedy_TheWeather] "
                "SONNE: sunrise=%s sunset=%s"
                % (
                    sunrise,
                    sunset
                )
            )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "SONNE FEHLER:",
                repr(e)
            )

            sunrise = "--"
            sunset = "--"

        # ============================================================
        # MOND
        # ============================================================

        moonrise = "--"
        moonset = "--"

        try:

            moonrise, moonset = self._moon(
                data
            )

            if not moonrise or moonrise == "na":
                moonrise = "--"

            if not moonset or moonset == "na":
                moonset = "--"

            print(
                "[speedy_TheWeather] "
                "MOND: moonrise=%s moonset=%s"
                % (
                    moonrise,
                    moonset
                )
            )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "MOND FEHLER:",
                repr(e)
            )

            moonrise = "--"
            moonset = "--"

        # ============================================================
        # SONNE / MOND ANZEIGE
        # ============================================================

        try:

            self["sunriselab"].text = str(
                sunrise
            )

            self["sunsetlab"].text = str(
                sunset
            )

            self["sunsep"].text = "-"

            self["moonriselab"].text = str(
                moonrise
            )

            self["moonsetlab"].text = str(
                moonset
            )

            self["moonsep"].text = "-"

            print(
                "[speedy_TheWeather] "
                "SONNE/MOND Anzeige: "
                "Sonne=%s - %s | Mond=%s - %s"
                % (
                    sunrise,
                    sunset,
                    moonrise,
                    moonset
                )
            )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "SONNE/MOND WIDGET FEHLER:",
                repr(e)
            )

        # ============================================================
        # FARBTASTEN
        # ============================================================

        self["key_red"] = StaticText(
            _("Back")
        )

        self["key_green"] = StaticText(
            _("Hours")
        )

        self["key_yellow"] = StaticText(
            _("Radar")
        )

        self["key_blue"] = StaticText(
            _("Compare Two Locations")
        )

        # ============================================================
        # ACTIONMAP
        # ============================================================

        self["myActionMap"] = ActionMap(
            [
                "SetupActions",
                "MenuActions",
                "ColorActions"
            ],
            {
                "menu": self.KeyMenu,
                "left": self.left,
                "right": self.right,
                "cancel": self.cancel,
                "red": self.cancel,
                "ok": self.fourteendays,
                "green": self.toggleHourStep,
                "yellow": self.openRadar,
                "blue": self.openTwoLocations
            },
            -1
        )

        # ============================================================
        # STARTANZEIGE
        # ============================================================

        self.updateFrameselect()

        # ============================================================
        # ALERT TIMER
        # ============================================================

        self.alertFixTimer = eTimer()

        self._alertFixTimer_conn = safeTimerCallback(
            self.alertFixTimer,
            self.updateFrameselect
        )

        self.alertFixTimer.start(
            200,
            True
        )

        # ============================================================
        # AKTUELLES GROSSES WETTERICON
        # ============================================================

        self.currentHourTimer = eTimer()

        self._currentHourTimer_conn = safeTimerCallback(
            self.currentHourTimer,
            self._updateCurrentBigIcon
        )

        self.currentHourTimer.start(
            60000,
            False
        )

        self.onClose.append(
            self._stopCurrentHourTimer
        )

    # ================================================================
    # ALLGEMEIN
    # ================================================================

    def _path(self, *parts):

        return "/".join(
            [self.WEATHER_PATH] + list(parts)
        )

    def _day(self, data, n):

        return (
            data[n]
            if n < len(data)
            else {}
        )

    def _wind(self, day):

        try:

            return str(
                day["hours"][0].get(
                    "winddirection"
                ) or "na"
            )

        except (
            KeyError,
            IndexError,
            TypeError
        ):

            return "na"

    def _icon(self, day):

        try:

            return str(
                day.get(
                    "iconcode"
                ) or "na"
            )

        except Exception:

            return "na"

    def _temp_picture(self, data):

        temps = []

        try:

            for day in data:

                for hour in day.get(
                    "hours",
                    []
                ):

                    if hour.get(
                        "temperature"
                    ) is not None:

                        temps.append(
                            round(
                                float(
                                    hour[
                                        "temperature"
                                    ]
                                )
                            )
                        )

                if len(temps) > 3:
                    break

        except Exception:

            pass

        if len(temps) < 2:
            return "tempeven.png"

        if temps[0] > temps[1]:
            return "tempcold.png"

        if temps[0] < temps[1]:
            return "temphot.png"

        return "tempeven.png"

    # ================================================================
    # SONNE
    # ================================================================

    def _sun(self, data):

        sunrise = "na"
        sunset = "na"

        try:

            if data:

                day = data[0]

                if day.get("sunrise"):

                    sunrise = str(
                        day["sunrise"]
                    ).split("T")[1][:5]

                if day.get("sunset"):

                    sunset = str(
                        day["sunset"]
                    ).split("T")[1][:5]

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "SONNE FEHLER:",
                repr(e)
            )

        return sunrise, sunset

    # ================================================================
    # MOND
    # ================================================================

    def _moon(self, data):

        try:

            print(
                "[speedy_TheWeather] MOND: "
                "lokaleStadt =",
                lockaaleStad
            )

            lat, lon = getCoordsFromEntry(
                lockaaleStad
            )

            print(
                "[speedy_TheWeather] MOND: "
                "Koordinaten = %s / %s"
                % (
                    str(lat),
                    str(lon)
                )
            )

            if lat is None or lon is None:

                print(
                    "[speedy_TheWeather] MOND: "
                    "keine Koordinaten"
                )

                return "--", "--"

            lat = float(lat)
            lon = float(lon)

            # ========================================================
            # HEUTIGES DATUM
            # ========================================================

            today = datetime.datetime.now().date()

            print(
                "[speedy_TheWeather] MOND: "
                "Datum=%s lat=%.4f lon=%.4f"
                % (
                    today.isoformat(),
                    lat,
                    lon
                )
            )

            # ========================================================
            # HEUTE BERECHNEN
            # ========================================================

            moonrise, moonset = _moon_rise_set_for_date(
                today,
                lat,
                lon
            )

            print(
                "[speedy_TheWeather] MOND: "
                "Heute rise=%s set=%s"
                % (
                    str(moonrise),
                    str(moonset)
                )
            )

            # ========================================================
            # MONDAUFGANG FEHLT
            # ========================================================

            if (
                not moonrise
                or
                moonrise == "na"
            ):

                previous_day = (
                    today
                    - datetime.timedelta(days=1)
                )

                previous_rise, previous_set = (
                    _moon_rise_set_for_date(
                        previous_day,
                        lat,
                        lon
                    )
                )

                print(
                    "[speedy_TheWeather] MOND: "
                    "Vortag=%s rise=%s set=%s"
                    % (
                        previous_day.isoformat(),
                        str(previous_rise),
                        str(previous_set)
                    )
                )

                if (
                    previous_rise
                    and
                    previous_rise != "na"
                ):

                    moonrise = previous_rise

                    print(
                        "[speedy_TheWeather] MOND: "
                        "Vortag-Aufgang uebernommen: %s"
                        % str(moonrise)
                    )

            # ========================================================
            # MONDUNTERGANG FEHLT
            # ========================================================

            if (
                not moonset
                or
                moonset == "na"
            ):

                next_day = (
                    today
                    + datetime.timedelta(days=1)
                )

                next_rise, next_set = (
                    _moon_rise_set_for_date(
                        next_day,
                        lat,
                        lon
                    )
                )

                print(
                    "[speedy_TheWeather] MOND: "
                    "Folgetag=%s rise=%s set=%s"
                    % (
                        next_day.isoformat(),
                        str(next_rise),
                        str(next_set)
                    )
                )

                if (
                    next_set
                    and
                    next_set != "na"
                ):

                    moonset = next_set

                    print(
                        "[speedy_TheWeather] MOND: "
                        "Folgetag-Untergang uebernommen: %s"
                        % str(moonset)
                    )

            # ========================================================
            # FINALER WERT
            # ========================================================

            if (
                not moonrise
                or
                moonrise == "na"
            ):

                moonrise = "--"

            else:

                moonrise = str(
                    moonrise
                )

            if (
                not moonset
                or
                moonset == "na"
            ):

                moonset = "--"

            else:

                moonset = str(
                    moonset
                )

            print(
                "[speedy_TheWeather] MOND: "
                "ENDERGEBNIS = [%s] - [%s]"
                % (
                    moonrise,
                    moonset
                )
            )

            return (
                moonrise,
                moonset
            )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "MOND FEHLER:",
                repr(e)
            )

            try:

                import traceback

                traceback.print_exc()

            except Exception:

                pass

            return "--", "--"

    # ================================================================
    # WIDGET-HELFER
    # ================================================================

    def _pixmap(self, name):

        self[name] = Pixmap()

    def _label(self, name, text=""):

        self[name] = StaticText()

        self[name].text = text

    def _label_xml(
            self,
            source,
            pos,
            size,
            font,
            halign="left",
            valign="center",
            color="#00ffffff",
            weight="Regular",
            nowrap=False
    ):

        nowrap_xml = (
            'noWrap="1" '
            if nowrap
            else ''
        )

        return (
            '<widget render="Label" source="{0}" '
            'position="{1}" size="{2}" zPosition="3" '
            'valign="{3}" halign="{4}" font="{7};{5}" '
            'foregroundColor="{6}" '
            'backgroundColor="#00202020" transparent="1" '
            '{8}'
            'shadowColor="black" shadowOffset="-2,-2"/>'
        ).format(
            source,
            pos,
            size,
            valign,
            halign,
            font,
            color,
            weight,
            nowrap_xml
        )

    def _icon_xml(
            self,
            name,
            pos,
            size,
            path,
            scale=False,
            z=3
    ):

        return (
            '<widget name="{0}" position="{1}" size="{2}" '
            '{3}zPosition="{4}" alphatest="blend" '
            'pixmap="{5}"/>'
        ).format(
            name,
            pos,
            size,
            'scale="1" ' if scale else '',
            z,
            path
        )

    def _eicon_xml(
            self,
            pos,
            size,
            path,
            scale=False,
            z=3
    ):

        return (
            '<ePixmap position="{0}" size="{1}" '
            '{2}zPosition="{3}" alphatest="blend" '
            'pixmap="{4}"/>'
        ).format(
            pos,
            size,
            'scale="1" ' if scale else '',
            z,
            path
        )

    # ================================================================
    # FARBTASTEN
    # ================================================================

    def _color_buttons_xml(self, hd=True):

        if hd:

            buttons = [
                (
                    "key_red",
                    "27,1040",
                    "310,45",
                    "red",
                    "20,1050",
                    "8,25",
                    38
                ),
                (
                    "key_green",
                    "342,1040",
                    "310,45",
                    "green",
                    "335,1050",
                    "8,25",
                    38
                ),
                (
                    "key_yellow",
                    "657,1040",
                    "310,45",
                    "yellow",
                    "650,1050",
                    "8,25",
                    38
                ),
                (
                    "key_blue",
                    "972,1040",
                    "510,45",
                    "blue",
                    "965,1050",
                    "8,25",
                    34
                )
            ]

        else:

            buttons = [
                (
                    "key_red",
                    "20,684",
                    "295,28",
                    "red",
                    "13,691",
                    "6,14",
                    25
                ),
                (
                    "key_green",
                    "325,684",
                    "295,28",
                    "green",
                    "318,691",
                    "6,14",
                    25
                ),
                (
                    "key_yellow",
                    "630,684",
                    "295,28",
                    "yellow",
                    "623,691",
                    "6,14",
                    25
                ),
                (
                    "key_blue",
                    "935,684",
                    "325,28",
                    "blue",
                    "928,691",
                    "6,14",
                    21
                )
            ]

        xml = ""

        for (
            name,
            pos,
            size,
            foreground,
            button_pos,
            button_size,
            font
        ) in buttons:

            xml += """
                <eLabel
                    position="{button_pos}"
                    size="{button_size}"
                    zPosition="12"
                    backgroundColor="{foreground}"
                    foregroundColor="{foreground}"/>

                <widget
                    source="{name}"
                    render="Label"
                    position="{pos}"
                    size="{size}"
                    zPosition="11"
                    font="Regular;{font}"
                    noWrap="1"
                    valign="center"
                    halign="center"
                    transparent="1"
                    backgroundColor="black"
                    foregroundColor="{foreground}"/>
            """.format(
                name=name,
                pos=pos,
                size=size,
                font=font,
                foreground=foreground,
                button_pos=button_pos,
                button_size=button_size
            )

        return xml

    # ================================================================
    # TAGESBEREICH
    # ================================================================

    def _build_day_section(
            self,
            day,
            data,
            hd=True
    ):

        icon = self._icon(data)
        wind = self._wind(data)

        hours = data.get(
            "hours",
            []
        )

        if hd:

            cfg = {
                "bigpos": "636,68",
                "bigsize": "150,150",
                "bigscale": False,

                "smallx": 131 + 248 * day,
                "smally": 498,
                "smallsize": "72,72",
                "smallscale": False,

                "daypos": "{},461".format(
                    138 + 248 * day
                ),
                "daysize": "155,40",
                "dayfont": 34,

                "maxpos": "{},571".format(
                    130 + 248 * day
                ),
                "maxsize": "110,54",
                "maxfont": 48,

                "minpos": "{},587".format(
                    245 + 248 * day
                ),
                "minsize": "110,36",
                "minfont": 28,

                "typepos": "{},617".format(
                    99 + 248 * day
                ),
                "typesize": "220,86",
                "typefont": 24,

                "sunpos": "760,238",
                "sunsize": "360,40",
                "sunfont": 30,

                "suniconpos": "630,225",
                "suniconsize": "120,60",

                "moonpos": "760,303",
                "moonsize": "360,40",
                "moonfont": 30,

                "mooniconpos": "630,290",
                "mooniconsize": "120,60",

                "hourx": 120,
                "hourstep": 216,
                "houry": 749,
                "hoursize": "72,72",
                "hourscale": False
            }

        else:

            cfg = {
                "bigpos": "422,54",
                "bigsize": "100,100",
                "bigscale": True,

                "smallx": 87 + 165 * day,
                "smally": 328,
                "smallsize": "48,48",
                "smallscale": True,

                "daypos": "{},302".format(
                    92 + 165 * day
                ),
                "daysize": "130,24",
                "dayfont": 22,

                "maxpos": "{},376".format(
                    92 + 165 * day
                ),
                "maxsize": "82,36",
                "maxfont": 32,

                "minpos": "{},389".format(
                    174 + 165 * day
                ),
                "minsize": "78,24",
                "minfont": 18,

                "typepos": "{},410".format(
                    69 + 165 * day
                ),
                "typesize": "138,54",
                "typefont": 16,

                "sunpos": "410,165",
                "sunsize": "230,30",
                "sunfont": 23,

                "suniconpos": "350,158",
                "suniconsize": "48,32",

                "moonpos": "410,207",
                "moonsize": "230,34",
                "moonfont": 23,

                "mooniconpos": "350,200",
                "mooniconsize": "48,32",

                "hourx": 80,
                "hourstep": 144,
                "houry": 474,
                "hoursize": "48,48",
                "hourscale": True
            }

        base = self.WEATHER_PATH
        path = icoonpath

        xml = ""

        # ============================================================
        # GROSSES WETTERICON
        # ============================================================

        xml += self._icon_xml(
            "bigWeerIcon1{}".format(day),
            cfg["bigpos"],
            cfg["bigsize"],
            "{}/{}/iconbighd/{}.png".format(
                base,
                path,
                icon
            ),
            cfg["bigscale"]
        )

        # ============================================================
        # WINDRICHTUNGS-ICON
        # ============================================================

        if not hd:

            xml += self._icon_xml(
                "bigDirIcon1{}".format(day),
                "778,234",
                "28,28",
                "{}/{}/windhd/{}.png".format(
                    base,
                    path,
                    wind
                ),
                True,
                1
            )

        # ============================================================
        # KLEINES WETTERICON
        # ============================================================

        xml += self._eicon_xml(
            "{},{}".format(
                cfg["smallx"],
                cfg["smally"]
            ),
            cfg["smallsize"],
            "{}/{}/iconhd/{}.png".format(
                base,
                path,
                icon
            ),
            cfg["smallscale"]
        )

        # ============================================================
        # WOCHENTAG
        # ============================================================

        xml += self._label_xml(
            "smallday2{}".format(day),
            cfg["daypos"],
            cfg["daysize"],
            cfg["dayfont"],
            color=self.COLOR_DAY
        )

        # ============================================================
        # MAXIMUM
        # ============================================================

        xml += self._label_xml(
            "maxtemp2{}".format(day),
            cfg["maxpos"],
            cfg["maxsize"],
            cfg["maxfont"],
            color=self.COLOR_MAXTEMP
        )

        # ============================================================
        # MINIMUM
        # ============================================================

        xml += self._label_xml(
            "minitemp2{}".format(day),
            cfg["minpos"],
            cfg["minsize"],
            cfg["minfont"],
            color=self.COLOR_MINTEMP
        )

        # ============================================================
        # WETTERBESCHREIBUNG
        # ============================================================

        xml += self._label_xml(
            "weertype2{}".format(day),
            cfg["typepos"],
            cfg["typesize"],
            cfg["typefont"],
            "center",
            color=self.COLOR_DAYTYPE
        )

        # ============================================================
        # SONNE / MOND
        # ============================================================

        if day == 0:

            sun_x, sun_y = [
                int(v)
                for v in cfg["sunpos"].split(",")
            ]

            sun_h = cfg["sunsize"].split(",")[1]

            if not hd:

                sun_field_w = 95
                sun_gap = 10

            else:

                sun_field_w = 95
                sun_gap = 8

            # --------------------------------------------------------
            # SONNENAUFGANG
            # --------------------------------------------------------

            xml += self._label_xml(
                "sunriselab",
                "{},{}".format(
                    sun_x,
                    sun_y
                ),
                "{},{}".format(
                    sun_field_w,
                    sun_h
                ),
                cfg["sunfont"],
                "center",
                color=self.COLOR_SUNRISE,
                nowrap=True
            )

            # --------------------------------------------------------
            # SONNENTRENNER
            # --------------------------------------------------------

            xml += self._label_xml(
                "sunsep",
                "{},{}".format(
                    sun_x + sun_field_w,
                    sun_y
                ),
                "{},{}".format(
                    sun_gap,
                    sun_h
                ),
                cfg["sunfont"],
                "center",
                color=self.COLOR_SUN,
                weight="Bold",
                nowrap=True
            )

            # --------------------------------------------------------
            # SONNENUNTERGANG
            # --------------------------------------------------------

            xml += self._label_xml(
                "sunsetlab",
                "{},{}".format(
                    sun_x
                    + sun_field_w
                    + sun_gap,
                    sun_y
                ),
                "{},{}".format(
                    sun_field_w,
                    sun_h
                ),
                cfg["sunfont"],
                "center",
                color=self.COLOR_SUNSET,
                nowrap=True
            )

            # --------------------------------------------------------
            # SONNENICON
            # --------------------------------------------------------

            xml += self._eicon_xml(
                cfg["suniconpos"],
                cfg["suniconsize"],
                "{}/{}/iconhd/sunupdownhd.png".format(
                    base,
                    path
                ),
                not hd
            )

            # --------------------------------------------------------
            # MOND POSITION
            # --------------------------------------------------------

            moon_x, moon_y = [
                int(v)
                for v in cfg["moonpos"].split(",")
            ]

            moon_h = cfg["moonsize"].split(",")[1]

            if not hd:

                moon_field_w = 105
                moon_gap = 10

            else:

                moon_field_w = 95
                moon_gap = 8

            # --------------------------------------------------------
            # MONDAUFGANG
            # --------------------------------------------------------

            xml += self._label_xml(
                "moonriselab",
                "{},{}".format(
                    moon_x,
                    moon_y
                ),
                "{},{}".format(
                    moon_field_w,
                    moon_h
                ),
                cfg["moonfont"],
                "center",
                color=self.COLOR_MOONRISE,
                nowrap=True
            )

            # --------------------------------------------------------
            # MONDTRENNER
            # --------------------------------------------------------

            xml += self._label_xml(
                "moonsep",
                "{},{}".format(
                    moon_x + moon_field_w,
                    moon_y
                ),
                "{},{}".format(
                    moon_gap,
                    moon_h
                ),
                cfg["moonfont"],
                "center",
                color=self.COLOR_SUN,
                weight="Bold",
                nowrap=True
            )

            # --------------------------------------------------------
            # MONDUNTERGANG
            # --------------------------------------------------------

            xml += self._label_xml(
                "moonsetlab",
                "{},{}".format(
                    moon_x
                    + moon_field_w
                    + moon_gap,
                    moon_y
                ),
                "{},{}".format(
                    moon_field_w,
                    moon_h
                ),
                cfg["moonfont"],
                "center",
                color=self.COLOR_MOONSET,
                nowrap=True
            )

            # --------------------------------------------------------
            # MONDICON
            # --------------------------------------------------------

            xml += self._eicon_xml(
                cfg["mooniconpos"],
                cfg["mooniconsize"],
                "{}/{}/iconhd/moonupdownhd.png".format(
                    base,
                    path
                ),
                not hd
            )

        # ============================================================
        # WIDGETS REGISTRIEREN
        # ============================================================

        self._pixmap(
            "bigWeerIcon1{}".format(day)
        )

        self._pixmap(
            "bigDirIcon1{}".format(day)
        )

        self._label(
            "smallday2{}".format(day)
        )

        self._label(
            "maxtemp2{}".format(day)
        )

        self._label(
            "minitemp2{}".format(day)
        )

        self._label(
            "weertype2{}".format(day)
        )

        if day == 0:

            self._label(
                "sunriselab"
            )

            self._label(
                "sunsetlab"
            )

            self._label(
                "sunsep"
            )

            self._label(
                "moonriselab"
            )

            self._label(
                "moonsetlab"
            )

            self._label(
                "moonsep"
            )

        # ============================================================
        # 8 STUNDENICONS
        # ============================================================

        for slot in range(8):

            hour = (
                hours[slot]
                if slot < len(hours)
                else {}
            )

            hour_icon = str(
                hour.get(
                    "iconcode"
                ) or "na"
            )

            name = "dayIcon{}{}".format(
                day,
                slot
            )

            x = (
                cfg["hourx"]
                + cfg["hourstep"] * slot
            )

            xml += self._icon_xml(
                name,
                "{},{}".format(
                    x,
                    cfg["houry"]
                ),
                cfg["hoursize"],
                "{}/{}/iconhd/{}.png".format(
                    base,
                    path,
                    hour_icon
                ),
                cfg["hourscale"],
                1
            )

            self._pixmap(
                name
            )

        return xml

    # ================================================================
    # STUNDENBEREICH
    # ================================================================

    def _build_hour_section(
            self,
            hour,
            hd=True
    ):

        base = self.WEATHER_PATH

        if hd:

            x = 216 * hour

            bg = (
                98 + x,
                736,
                "191,305",
                "vlak_uur.png"
            )

            labels = [
                (
                    "dayhour3",
                    205 + x,
                    757,
                    "105,42",
                    33,
                    "left"
                ),
                (
                    "daytemp3",
                    120 + x,
                    820,
                    "180,54",
                    48,
                    "left"
                ),
                (
                    "sunpercent3",
                    168 + x,
                    883,
                    "123,32",
                    27,
                    "left"
                ),
                (
                    "daypercent3",
                    168 + x,
                    922,
                    "120,30",
                    27,
                    "left"
                ),
                (
                    "hrdayper3",
                    168 + x,
                    961,
                    "123,32",
                    27,
                    "left"
                ),
                (
                    "dayspeed3",
                    168 + x,
                    1000,
                    "123,32",
                    27,
                    "left"
                )
            ]

            icons = [
                (
                    "sunicon",
                    114 + x,
                    879,
                    "36,36",
                    "sunpchd.png"
                ),
                (
                    "rainicon",
                    116 + x,
                    921,
                    "30,30",
                    "rainhd.png"
                ),
                (
                    "rhicon",
                    120 + x,
                    960,
                    "23,30",
                    "rhhd.png"
                ),
                (
                    "windicon",
                    119 + x,
                    997,
                    "38,38",
                    "turbinehd.png"
                )
            ]

            scale = False

        else:

            x = 144 * hour

            bg = (
                64 + x,
                469,
                "129,205",
                "vlak_uursd.png"
            )

            labels = [
                (
                    "dayhour3",
                    64 + x,
                    486,
                    "129,28",
                    20,
                    "center"
                ),
                (
                    "daytemp3",
                    80 + x,
                    520,
                    "120,36",
                    32,
                    "left"
                ),
                (
                    "sunpercent3",
                    112 + x,
                    560,
                    "82,21",
                    18,
                    "left"
                ),
                (
                    "daypercent3",
                    112 + x,
                    586,
                    "80,20",
                    18,
                    "left"
                ),
                (
                    "hrdayper3",
                    112 + x,
                    612,
                    "80,20",
                    18,
                    "left"
                ),
                (
                    "dayspeed3",
                    112 + x,
                    638,
                    "82,21",
                    18,
                    "left"
                )
            ]

            icons = [
                (
                    "sunicon",
                    76 + x,
                    558,
                    "24,24",
                    "sunpchd.png"
                ),
                (
                    "rainicon",
                    77 + x,
                    585,
                    "20,20",
                    "rainhd.png"
                ),
                (
                    "rhicon",
                    79 + x,
                    612,
                    "16,20",
                    "rhhd.png"
                ),
                (
                    "windicon",
                    79 + x,
                    636,
                    "25,25",
                    "turbinehd.png"
                )
            ]

            scale = True

        # ============================================================
        # HINTERGRUND
        # ============================================================

        name = "vlakuur{}".format(
            hour
        )

        xml = self._icon_xml(
            name,
            "{},{}".format(
                bg[0],
                bg[1]
            ),
            bg[2],
            "{}/{}/patches/{}".format(
                base,
                SHARED_PACK,
                bg[3]
            ),
            False,
            0
        )

        self._pixmap(
            name
        )

        # ============================================================
        # LABELS
        # ============================================================

        for (
            prefix,
            px,
            py,
            size,
            font,
            align
        ) in labels:

            name = "{}{}".format(
                prefix,
                hour
            )

            if prefix == "dayhour3":

                color = self.COLOR_HOUR

            elif prefix == "daytemp3":

                color = self.COLOR_HOURTEMP

            elif prefix == "sunpercent3":

                color = self.COLOR_SUNPERCENT

            elif prefix == "daypercent3":

                color = self.COLOR_RAIN

            elif prefix == "hrdayper3":

                color = self.COLOR_HUMIDITY

            elif prefix == "dayspeed3":

                color = self.COLOR_WIND_SPEED

            else:

                color = "#00ffffff"

            xml += self._label_xml(
                name,
                "{},{}".format(
                    px,
                    py
                ),
                size,
                font,
                align,
                color=color
            )

            self._label(
                name
            )

        # ============================================================
        # ICONS
        # ============================================================

        for (
            prefix,
            px,
            py,
            size,
            filename
        ) in icons:

            name = "{}{}".format(
                prefix,
                hour
            )

            xml += self._icon_xml(
                name,
                "{},{}".format(
                    px,
                    py
                ),
                size,
                "{}/{}/windhd/{}".format(
                    base,
                    icoonpath,
                    filename
                ),
                scale
            )

            self._pixmap(
                name
            )

        return xml

    # ================================================================
    # CLOCK
    # ================================================================

    def _clock_xml(
            self,
            pos,
            size,
            font,
            fmt,
            color="#00ffffff"
    ):

        return """
            <widget source="global.CurrentTime" render="Label"
                position="{0}" size="{1}" transparent="1"
                zPosition="1" font="Regular;{2}"
                foregroundColor="{4}"
                backgroundColor="#00202020"
                valign="center" halign="left"
                noWrap="1">
                <convert type="ClockToText">
                    Format:{3}
                </convert>
            </widget>
        """.format(
            pos,
            size,
            font,
            fmt,
            color
        )

    # ================================================================
    # HAUPTBEREICH
    # ================================================================

    def _main_widgets(
            self,
            hd,
            winddir_top
    ):

        base = self.WEATHER_PATH
        pack = SHARED_PACK

        if hd:

            return """
                <widget name="yellowdot"
                    position="275,463"
                    size="36,36"
                    pixmap="{base}/{pack}/buttons/yeldothd.png"
                    zPosition="3"
                    alphatest="blend"/>

                {city}
                {temp}
                {type}
                {feel}
                {wind}

                <widget name="winddiricon1"
                    position="1210,350"
                    scale="1"
                    size="36,36"
                    zPosition="4"
                    alphatest="blend"
                    pixmap="{base}/{path}/windhd/{winddir}.png"/>

                <widget name="weatheralertbg1"
                    position="1322,240"
                    size="588,72"
                    zPosition="2"
                    pixmap="{base}/{pack}/alert/vlak_alert.png"
                    alphatest="on"/>

                <widget name="weatheralerticon1"
                    position="1332,244"
                    size="64,64"
                    zPosition="4"
                    alphatest="blend"
                    transparent="1"/>

                <widget name="weatheralert1"
                    position="1440,244"
                    size="576,64"
                    zPosition="3"
                    valign="center"
                    halign="left"
                    font="Regular;48"
                    foregroundColor="{alert_color}"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>
            """.format(

                base=base,
                pack=pack,
                path=icoonpath,
                winddir=winddir_top,

                city=self._label_xml(
                    "city1",
                    "608,44",
                    "705,64",
                    48,
                    "center",
                    color=self.COLOR_CITY
                ),

                temp=self._label_xml(
                    "bigtemp1",
                    "870,122",
                    "353,118",
                    108,
                    color=self.COLOR_BIGTEMP
                ),

                type=self._label_xml(
                    "bigweathertype1",
                    "980,298",
                    "480,40",
                    28,
                    color=self.COLOR_WEATHERTYPE
                ),

                feel=self._label_xml(
                    "GevoelsTemp1",
                    "980,250",
                    "354,40",
                    28,
                    color=self.COLOR_FEELS
                ),

                wind=self._label_xml(
                    "winddir1",
                    "980,346",
                    "330,45",
                    28,
                    color=self.COLOR_WIND
                ),

                alert_color=self.COLOR_ALERT
            )

        return """
            <widget name="yellowdot"
                position="184,307"
                size="24,24"
                pixmap="{base}/{pack}/buttons/yeldot.png"
                zPosition="3"
                alphatest="blend"/>

            {city}
            {temp}
            {type}
            {feel}
            {wind}

            <widget name="winddiricon1"
                position="895,240"
                size="28,28"
                zPosition="4"
                alphatest="blend"
                pixmap="{base}/{path}/windhd/{winddir}.png"/>

            <widget name="weatheralertbg1"
                position="877,162"
                size="398,48"
                zPosition="2"
                pixmap="{base}/{pack}/alert/vlak_alertsd.png"
                alphatest="on"/>

            <widget name="weatheralerticon1"
                position="883,165"
                size="42,42"
                zPosition="4"
                alphatest="blend"
                transparent="1"/>

            <widget name="weatheralert1"
                position="955,165"
                size="320,42"
                zPosition="3"
                valign="center"
                halign="left"
                font="Regular;30"
                foregroundColor="{alert_color}"
                backgroundColor="#00202020"
                transparent="1"
                shadowColor="black"
                shadowOffset="-2,-2"/>
        """.format(

            base=base,
            pack=pack,
            path=icoonpath,
            winddir=winddir_top,

            city=self._label_xml(
                "city1",
                "405,37",
                "470,42",
                32,
                "center",
                color=self.COLOR_CITY
            ),

            temp=self._label_xml(
                "bigtemp1",
                "565,88",
                "235,76",
                72,
                color=self.COLOR_BIGTEMP
            ),

            type=self._label_xml(
                "bigweathertype1",
                "665,208",
                "320,30",
                18,
                color=self.COLOR_WEATHERTYPE
            ),

            feel=self._label_xml(
                "GevoelsTemp1",
                "665,176",
                "236,30",
                18,
                color=self.COLOR_FEELS
            ),

            wind=self._label_xml(
                "winddir1",
                "665,240",
                "230,30",
                18,
                color=self.COLOR_WIND
            ),

            alert_color=self.COLOR_ALERT
        )

    # ================================================================
    # HD SKIN
    # ================================================================

    def _build_hd_skin(
            self,
            data,
            winddir_top,
            tempicon
    ):

        content = ""

        for day in range(7):

            content += self._build_day_section(
                day,
                self._day(
                    data,
                    day
                ),
                True
            )

        for hour in range(8):

            content += self._build_hour_section(
                hour,
                True
            )

        return """
        <screen name="sevenday"
            title="seven"
            flags="wfNoBorder"
            position="center,center"
            size="1920,1080"
            backgroundColor="#ff000000">

            <widget name="bgpic"
                position="0,0"
                size="1920,1080"
                zPosition="-1"
                alphatest="blend"/>

            <ePixmap
                pixmap="{base}/{pack}/backgroundhd_2.png"
                position="center,center"
                size="1920,1080"
                zPosition="0"
                alphatest="blend"/>

            {clock}

            {date}

            {main}

            <ePixmap
                pixmap="{base}/{path}/windhd/{tempicon}"
                position="1112,143"
                size="90,80"
                zPosition="2"
                transparent="0"
                alphatest="blend"/>

            {content}

            <ePixmap
                pixmap="{base}/{pack}/buttons/menubutton.png"
                position="1580,46"
                size="90,54"
                zPosition="3"
                alphatest="blend"/>

            <ePixmap
                pixmap="{base}/{pack}/buttons/okbutton.png"
                position="1685,46"
                size="54,54"
                zPosition="3"
                alphatest="blend"/>

            {colorbuttons}

        </screen>
        """.format(

            base=self.WEATHER_PATH,
            pack=SHARED_PACK,
            path=icoonpath,
            tempicon=tempicon,
            content=content,

            clock=self._clock_xml(
                "1760,35",
                "400,45",
                30,
                "%H:%M:%S",
                color=self.COLOR_CLOCK
            ),

            date=self._clock_xml(
                "1760,72",
                "450,35",
                30,
                "%d.%m.%y",
                color=self.COLOR_DATE
            ),

            main=self._main_widgets(
                True,
                winddir_top
            ),

            colorbuttons=self._color_buttons_xml(
                True
            )
        )

    # ================================================================
    # SD SKIN
    # ================================================================

    def _build_sd_skin(
            self,
            data,
            winddir_top,
            tempicon
    ):

        content = ""

        for day in range(7):

            content += self._build_day_section(
                day,
                self._day(
                    data,
                    day
                ),
                False
            )

        for hour in range(8):

            content += self._build_hour_section(
                hour,
                False
            )

        return """
        <screen name="sevenday"
            title="seven"
            flags="wfNoBorder"
            position="center,center"
            size="1280,720">

            <widget name="bgpic"
                position="0,0"
                size="1280,720"
                zPosition="-1"
                alphatest="blend"/>

            <ePixmap
                pixmap="{base}/{pack}/backgroundhd_2.png"
                position="center,center"
                size="1280,720"
                scale="1"
                zPosition="0"
                alphatest="blend"/>

            {clock}

            {date}

            {main}

            <ePixmap
                pixmap="{base}/{path}/windhd/{tempicon}"
                position="752,99"
                size="60,53"
                scale="1"
                zPosition="2"
                transparent="0"
                alphatest="on"/>

            {content}

            <ePixmap
                pixmap="{base}/{pack}/buttons/menubuttonsd.png"
                position="1160,90"
                size="60,36"
                zPosition="10"
                alphatest="blend"/>

            <ePixmap
                pixmap="{base}/{pack}/buttons/okbuttonsd.png"
                position="1228,90"
                size="36,36"
                zPosition="10"
                alphatest="blend"/>

            {colorbuttons}

        </screen>
        """.format(

            base=self.WEATHER_PATH,
            pack=SHARED_PACK,
            path=icoonpath,
            tempicon=tempicon,
            content=content,

            clock=self._clock_xml(
                "1091,12",
                "150,55",
                24,
                "%H:%M:%S",
                color=self.COLOR_CLOCK
            ),

            date=self._clock_xml(
                "941,32",
                "210,55",
                16,
                "%a.%d.%m",
                color=self.COLOR_DATE
            ),

            main=self._main_widgets(
                False,
                winddir_top
            ),

            colorbuttons=self._color_buttons_xml(
                False
            )
        )

    # ================================================================
    # SKIN
    # ================================================================

    def _build_skin(
            self,
            data,
            winddir_top,
            tempicon
    ):

        if sz_w > 1800:

            return self._build_hd_skin(
                data,
                winddir_top,
                tempicon
            )

        return self._build_sd_skin(
            data,
            winddir_top,
            tempicon
        )

    # ================================================================
    # TAGESDATEN
    # ================================================================

    def _set_day(
            self,
            day,
            data
    ):

        names = (
            "smallday2",
            "maxtemp2",
            "minitemp2",
            "weertype2"
        )

        widgets = [
            "{}{}".format(
                x,
                day
            )
            for x in names
        ]

        has_data = bool(data) and (
            data.get("iconcode")
            or data.get("maxtemperature")
            or data.get("mintemperature")
            or data.get("maxtemp")
            or data.get("mintemp")
        )

        if not has_data:

            for name in widgets:

                try:

                    self[name].text = ""

                except Exception:

                    pass

            try:

                self[
                    "bigWeerIcon1{}".format(day)
                ].hide()

                self[
                    "bigDirIcon1{}".format(day)
                ].hide()

            except Exception:

                pass

            return

        # ============================================================
        # ICONS EINBLENDEN
        # ============================================================

        try:

            self[
                "bigWeerIcon1{}".format(day)
            ].show()

            self[
                "bigDirIcon1{}".format(day)
            ].show()

        except Exception:

            pass

        # ============================================================
        # DATUM
        # ============================================================

        info1 = ""

        if data.get("date"):

            try:

                date_value = str(
                    data["date"]
                ).split("T")[0]

                unix = time.mktime(
                    datetime.datetime(
                        int(date_value[:4]),
                        int(date_value[5:7]),
                        int(date_value[8:10])
                    ).timetuple()
                )

                info1 = _(
                    str(
                        strftime(
                            "%A",
                            localtime(unix)
                        )
                    ).title()[:2]
                )

                info1 += str(
                    strftime(
                        " %d.%m",
                        localtime(unix)
                    )
                )

            except Exception as e:

                print(
                    "[speedy_TheWeather] "
                    "Datum Fehler:",
                    repr(e)
                )

        # ============================================================
        # MINIMUM
        # ============================================================

        mintemp = data.get(
            "mintemp"
        )

        if mintemp is None:

            mintemp = data.get(
                "mintemperature"
            )

        # ============================================================
        # MAXIMUM
        # ============================================================

        maxtemp = data.get(
            "maxtemp"
        )

        if maxtemp is None:

            maxtemp = data.get(
                "maxtemperature"
            )

        info2 = ""
        info3 = ""

        # ============================================================
        # MINIMUM FORMATIEREN
        # ============================================================

        if mintemp is not None:

            try:

                info2 = "{:.0f}\xb0".format(
                    float(mintemp)
                )

            except (
                TypeError,
                ValueError
            ):

                info2 = (
                    safeStr(mintemp)
                    + "\xb0"
                )

        # ============================================================
        # MAXIMUM FORMATIEREN
        # ============================================================

        if maxtemp is not None:

            try:

                info3 = "{:.0f}\xb0".format(
                    float(maxtemp)
                )

            except (
                TypeError,
                ValueError
            ):

                info3 = (
                    safeStr(maxtemp)
                    + "\xb0"
                )

        # ============================================================
        # WIDGETS SETZEN
        # ============================================================

        self[
            "smallday2{}".format(day)
        ].text = info1

        self[
            "maxtemp2{}".format(day)
        ].text = info3

        self[
            "minitemp2{}".format(day)
        ].text = info2

        self[
            "weertype2{}".format(day)
        ].text = icontotext(
            str(
                data.get(
                    "iconcode"
                ) or "na"
            )
        )



    # ================================================================
    # INIT
    # ================================================================

    def __init__(self, session):

        Screen.__init__(
            self,
            session
        )

        AddNewScreen(self)

        self.onClose.append(
            lambda: RemoveScreen(self)
        )

        global weatherData

        data = weatherData.get(
            "days",
            []
        )

        self.selected = 0
        self.hourStep = 1

        # ============================================================
        # OBERER WINDPFEIL
        # ============================================================

        winddir_top = (
            self._wind(data[0])
            if data
            else "na"
        )

        # ============================================================
        # TEMPERATURBILD
        # ============================================================

        tempicon = self._temp_picture(
            data
        )

        # ============================================================
        # FARBEN LADEN
        # ============================================================

        self._loadSevenDayColors()

        # ============================================================
        # SKIN AUFBAUEN
        # ============================================================

        self.skin = self._build_skin(
            data,
            winddir_top,
            tempicon
        )

        # ============================================================
        # DATUMSFORMAT
        # ============================================================

        try:

            date_format = getDateFormat()

            for old in (
                "Format:%a %d/%m/%y",
                "Format:%a %d.%m",
                "Format:%a %d.%m.%y"
            ):

                self.skin = self.skin.replace(
                    old,
                    date_format
                )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "date format replacement failed:",
                repr(e)
            )

        # ============================================================
        # ALLGEMEINE WIDGETS
        # ============================================================

        self["city1"] = StaticText()

        self["city1"].text = str(
            citynamedisplay
        )

        for name in (
            "bigtemp1",
            "bigweathertype1",
            "GevoelsTemp1",
            "winddir1"
        ):

            self[name] = StaticText()

        for name in (
            "winddiricon1",
            "weatheralertbg1",
            "weatheralerticon1"
        ):

            self[name] = Pixmap()

        self["weatheralert1"] = Label("")

        self["yellowdot"] = MovingPixmap()

        self["bgpic"] = Pixmap()

        # ============================================================
        # HINTERGRUND
        # ============================================================

        try:

            self.picload = ePicLoad()

            self._picload_conn = safeSignalConnect(
                self.picload.PictureData,
                self.bgPictureLoaded
            )

            self.loadBackground()

        except Exception as e:

            print(
                "speedy_TheWeather: "
                "ePicLoad niet beschikbaar, "
                "standard Hintergrund:",
                repr(e)
            )

            self.picload = None

        # ============================================================
        # STUNDEN
        # ============================================================

        defaults = {
            "dayhour3": "00h",
            "daytemp3": "--\xb0C",
            "sunpercent3": "--%",
            "daypercent3": "--%",
            "hrdayper3": "--%",
            "dayspeed3": "--Km/h"
        }

        for hour in range(8):

            for prefix, value in defaults.items():

                self._label(
                    "{}{}".format(
                        prefix,
                        hour
                    ),
                    value
                )

        # ============================================================
        # 7 TAGE AUFBAUEN
        #
        # WICHTIG:
        # _set_day() baut dabei auch den Bereich fuer Tag 0 auf.
        #
        # Dadurch existieren danach:
        #
        # sunriselab
        # sunsetlab
        # sunsep
        # moonriselab
        # moonsetlab
        # moonsep
        #
        # Erst DANACH werden deren Texte gesetzt.
        # ============================================================

        for day in range(7):

            self._set_day(
                day,
                self._day(
                    data,
                    day
                )
            )

        # ============================================================
        # SONNE
        # ============================================================

        sunrise = "--"
        sunset = "--"

        try:

            sunrise, sunset = self._sun(
                data
            )

            if not sunrise or sunrise == "na":
                sunrise = "--"

            if not sunset or sunset == "na":
                sunset = "--"

            print(
                "[speedy_TheWeather] "
                "SONNE: sunrise=%s sunset=%s"
                % (
                    str(sunrise),
                    str(sunset)
                )
            )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "SONNE FEHLER:",
                repr(e)
            )

            sunrise = "--"
            sunset = "--"

        # ============================================================
        # MOND
        #
        # _moon() verwendet:
        #
        # HEUTE
        #   -> Mondaufgang / Monduntergang
        #
        # KEIN MONDAUFGANG HEUTE
        #   -> Vortag pruefen
        #
        # KEIN MONDUNTERGANG HEUTE
        #   -> Folgetag pruefen
        #
        # Damit gleiche Logik wie TwoLocations.
        # ============================================================

        moonrise = "--"
        moonset = "--"

        try:

            moonrise, moonset = self._moon(
                data
            )

            if not moonrise or moonrise == "na":
                moonrise = "--"

            if not moonset or moonset == "na":
                moonset = "--"

            print(
                "[speedy_TheWeather] "
                "MOND: moonrise=%s moonset=%s"
                % (
                    str(moonrise),
                    str(moonset)
                )
            )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "MOND FEHLER:",
                repr(e)
            )

            moonrise = "--"
            moonset = "--"

        # ============================================================
        # SONNE / MOND WIDGET-TEXTE
        #
        # WICHTIG:
        #
        # HIER KEIN self._label(...) MEHR!
        #
        # Die Widgets wurden bereits in
        # _build_day_section() erzeugt.
        # ============================================================

        try:

            self["sunriselab"].text = str(
                sunrise
            )

            self["sunsetlab"].text = str(
                sunset
            )

            self["sunsep"].text = "-"

            self["moonriselab"].text = str(
                moonrise
            )

            self["moonsetlab"].text = str(
                moonset
            )

            self["moonsep"].text = "-"

            print(
                "[speedy_TheWeather] "
                "SONNE/MOND Anzeige: "
                "Sonne=%s - %s | Mond=%s - %s"
                % (
                    str(sunrise),
                    str(sunset),
                    str(moonrise),
                    str(moonset)
                )
            )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "SONNE/MOND WIDGET FEHLER:",
                repr(e)
            )

        # ============================================================
        # FARBTASTEN
        # ============================================================

        self["key_red"] = StaticText(
            _("Back")
        )

        self["key_green"] = StaticText(
            _("Hours")
        )

        self["key_yellow"] = StaticText(
            _("Radar")
        )

        self["key_blue"] = StaticText(
            _("Compare Two Locations")
        )

        # ============================================================
        # ACTIONMAP
        # ============================================================

        self["myActionMap"] = ActionMap(
            [
                "SetupActions",
                "MenuActions",
                "ColorActions"
            ],
            {
                "menu": self.KeyMenu,
                "left": self.left,
                "right": self.right,
                "cancel": self.cancel,
                "red": self.cancel,
                "ok": self.fourteendays,
                "green": self.toggleHourStep,
                "yellow": self.openRadar,
                "blue": self.openTwoLocations
            },
            -1
        )

        # ============================================================
        # STARTANZEIGE
        # ============================================================

        self.updateFrameselect()

        # ============================================================
        # TIMER - ALERT
        # ============================================================

        self.alertFixTimer = eTimer()

        self._alertFixTimer_conn = safeTimerCallback(
            self.alertFixTimer,
            self.updateFrameselect
        )

        self.alertFixTimer.start(
            200,
            True
        )

        # ============================================================
        # TIMER - AKTUELLES GROSSES WETTERICON
        # ============================================================

        self.currentHourTimer = eTimer()

        self._currentHourTimer_conn = safeTimerCallback(
            self.currentHourTimer,
            self._updateCurrentBigIcon
        )

        self.currentHourTimer.start(
            60000,
            False
        )

        # ============================================================
        # TIMER BEIM SCHLIESSEN STOPPEN
        # ============================================================

        self.onClose.append(
            self._stopCurrentHourTimer
        )

    # ================================================================
    # FARBEN LADEN
    # ================================================================

    def _loadSevenDayColors(self):

        for (
            _color_name,
            _config_name
        ) in (
            ("COLOR_CITY", "city"),
            ("COLOR_BIGTEMP", "bigtemp"),
            ("COLOR_WEATHERTYPE", "weathertype"),
            ("COLOR_FEELS", "feels"),
            ("COLOR_WIND", "wind"),
            ("COLOR_DAY", "day"),
            ("COLOR_MAXTEMP", "maxtemp"),
            ("COLOR_MINTEMP", "mintemp"),
            ("COLOR_DAYTYPE", "daytype"),
            ("COLOR_SUN", "sun"),
            ("COLOR_SUNRISE", "sunrise"),
            ("COLOR_SUNSET", "sunset"),
            ("COLOR_MOONRISE", "moonrise"),
            ("COLOR_MOONSET", "moonset"),
            ("COLOR_HOUR", "hour"),
            ("COLOR_HOURTEMP", "hourtemp"),
            ("COLOR_RAIN", "rain"),
            ("COLOR_SUNPERCENT", "sunpercent"),
            ("COLOR_HUMIDITY", "humidity"),
            ("COLOR_WIND_SPEED", "windspeed"),
            ("COLOR_CLOCK", "clock"),
            ("COLOR_DATE", "date"),
            ("COLOR_ALERT", "alert"),
        ):

            try:

                cfg = getattr(
                    config.plugins.speedy_TheWeather,
                    "sevenday_color_" + _config_name
                )

                value = (
                    cfg.value
                    or _SEVENDAY_COLOR_DEFAULTS[
                        _config_name
                    ]
                )

                setattr(
                    self,
                    _color_name,
                    value
                )

            except Exception:

                setattr(
                    self,
                    _color_name,
                    _SEVENDAY_COLOR_DEFAULTS[
                        _config_name
                    ]
                )

    # ================================================================
    # SLOT HOURS
    # ================================================================

    def getSlotHours(self, day):

        global weatherData

        dataDagen = weatherData["days"]
        dataUrr = dataDagen[day]["hours"]

        result = []
        datacount = 0

        for data in dataUrr:

            try:

                hour = int(
                    data.get("hour")
                )

            except (
                TypeError,
                ValueError
            ):

                continue

            if (
                hour >= 1
                and self.hourStep > 0
                and ((hour - 1) % self.hourStep) == 0
            ):

                if datacount < 8:

                    result.append(data)
                    datacount += 1

        return result

    # ================================================================
    # STUNDENSCHRITT
    # ================================================================

    def toggleHourStep(self):

        if self.hourStep == 1:

            self.hourStep = 2

        elif self.hourStep == 2:

            self.hourStep = 3

        else:

            self.hourStep = 1

        self.updateFrameselect()

    # ================================================================
    # TIMER STOPPEN
    # ================================================================

    def _stopCurrentHourTimer(self):

        try:

            if hasattr(
                self,
                "currentHourTimer"
            ):

                self.currentHourTimer.stop()

        except Exception:
            pass

    # ================================================================
    # AKTUELLE STUNDE
    # ================================================================

    def _getCurrentHourData(self):

        try:

            hours = weatherData.get(
                "days",
                []
            )[0].get(
                "hours",
                []
            )

        except (
            AttributeError,
            IndexError,
            TypeError
        ):

            return None

        if not hours:
            return None

        try:

            now_hour = datetime.datetime.now().hour

        except Exception:

            now_hour = None

        if now_hour is not None:

            for entry in hours:

                try:

                    hour = int(
                        entry.get("hour")
                    )

                except (
                    TypeError,
                    ValueError,
                    AttributeError
                ):

                    continue

                if (
                    hour == now_hour
                    or (
                        now_hour == 0
                        and hour == 24
                    )
                ):

                    return entry

        return (
            hours[0]
            if isinstance(
                hours[0],
                dict
            )
            else None
        )

    # ================================================================
    # GROSSES ICON AKTUALISIEREN
    # ================================================================

    def _updateCurrentBigIcon(self):

        try:

            if self.selected != 0:
                return

            entry = self._getCurrentHourData()

            if not entry:
                return

            icon = (
                entry.get("iconcode")
                or entry.get("icon")
            )

            if not icon:
                return

            iconpath = os.path.join(
                self.WEATHER_PATH,
                icoonpath,
                "iconbighd",
                str(icon) + ".png"
            )

            widget = self[
                "bigWeerIcon10"
            ]

            if widget.instance is not None:

                widget.instance.setPixmap(
                    _load_icon_cached(
                        iconpath
                    )
                )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "current big icon update failed:",
                e
            )

    # ================================================================
    # AUSWAHL AKTUALISIEREN
    # ================================================================

    def updateFrameselect(self):

        if self.selected < 0:
            self.selected = 6

        elif self.selected > 6:
            self.selected = 0

        # ============================================================
        # GELBER PUNKT
        # ============================================================

        if sz_w > 1800:

            self["yellowdot"].moveTo(
                275 + (
                    248 * self.selected
                ),
                463,
                2
            )

        else:

            self["yellowdot"].moveTo(
                184 + (
                    165 * self.selected
                ),
                307,
                2
            )

        self["yellowdot"].startMoving()

        global weatherData

        dataDagen = weatherData["days"]

        if not dataDagen:
            return

        # ============================================================
        # OBERER BEREICH
        # ============================================================

        temptext = "na"

        try:

            if dataDagen[
                self.selected + 0
            ].get("temperature"):

                temptext = dataDagen[
                    self.selected + 0
                ]["temperature"]

        except Exception:
            pass

        try:

            dataPerUur = weatherData[
                "days"
            ][0]["hours"]

        except Exception:

            dataPerUur = []

        self["bigtemp1"].setText("")
        self["bigweathertype1"].setText("")
        self["GevoelsTemp1"].setText("")
        self["winddir1"].setText("")

        try:

            if dataPerUur:

                self["bigtemp1"].setText(
                    '{:>4}'.format(
                        str(
                            "%.1f"
                            % dataPerUur[0][
                                "temperature"
                            ]
                        )
                    )
                )

                self[
                    "GevoelsTemp1"
                ].setText(
                    _("Feels Like: ")
                    + str(
                        "%.1f"
                        % dataPerUur[0][
                            "feeltemperature"
                        ]
                    )
                    + "\xb0C"
                )

                self[
                    "winddir1"
                ].setText(
                    _("Wind direction: ")
                    + str(
                        winddirtext(
                            dataPerUur[0][
                                "winddirection"
                            ]
                        )
                    )
                )

                self[
                    "bigweathertype1"
                ].setText(
                    icontotext(
                        str(
                            dataPerUur[0][
                                "iconcode"
                            ]
                        )
                    )
                )

        except Exception:
            pass

        # ============================================================
        # WETTERWARNUNG
        # ============================================================

        try:

            alertKleur, alertTekst = (
                localWeatherAlert(
                    dataDagen[0]
                )
            )

        except Exception as e:

            alertKleur, alertTekst = "", ""

            print(
                "updateFrameselect: "
                "fout bij bepalen weeralarm:",
                e
            )

        if alertTekst:

            kleurwaarde = {
                "yellow": gRGB(0xf2c200),
                "orange": gRGB(0xff8c00),
                "red": gRGB(0xe02020),
                "blue": gRGB(0x40a0ff),
            }.get(
                alertKleur,
                gRGB(0xffffff)
            )

            self[
                "weatheralert1"
            ].setText(
                alertTekst
            )

            try:

                if (
                    self[
                        "weatheralert1"
                    ].instance is not None
                ):

                    self[
                        "weatheralert1"
                    ].instance.setForegroundColor(
                        kleurwaarde
                    )

            except Exception as e:

                print(
                    "updateFrameselect: "
                    "fout bij instellen "
                    "weeralarm-kleur:",
                    e
                )

            try:

                if sz_w > 1800:

                    iconpad = (
                        "/usr/lib/enigma2/python/"
                        "Plugins/Extensions/"
                        "speedy_TheWeather/"
                        + SHARED_PACK
                        + "/alert/alert_"
                        + alertKleur
                        + ".png"
                    )

                else:

                    iconpad = (
                        "/usr/lib/enigma2/python/"
                        "Plugins/Extensions/"
                        "speedy_TheWeather/"
                        + SHARED_PACK
                        + "/alert/alert_"
                        + alertKleur
                        + "_sd.png"
                    )

                if (
                    self[
                        "weatheralerticon1"
                    ].instance is not None
                ):

                    self[
                        "weatheralerticon1"
                    ].instance.setPixmapFromFile(
                        iconpad
                    )

                    self[
                        "weatheralerticon1"
                    ].show()

            except Exception as e:

                print(
                    "updateFrameselect: "
                    "fout bij laden alert-icoon:",
                    e
                )

                self[
                    "weatheralerticon1"
                ].hide()

            self[
                "weatheralertbg1"
            ].show()

        else:

            self[
                "weatheralert1"
            ].setText(
                ""
            )

            self[
                "weatheralerticon1"
            ].hide()

            self[
                "weatheralertbg1"
            ].hide()

        # ============================================================
        # GROSSE DATEN
        # ============================================================

        feeltext = "na"

        try:

            if dataDagen[0].get(
                "feeltemperature"
            ):

                feeltext = dataDagen[0][
                    "feeltemperature"
                ]

        except Exception:
            pass

        windtext = "na"

        try:

            if dataDagen[0].get(
                "winddirection"
            ):

                windtext = dataDagen[0][
                    "winddirection"
                ]

        except Exception:
            pass

        typetext = "na"

        try:

            if dataDagen[0].get(
                "iconcode"
            ):

                typetext = dataDagen[0][
                    "iconcode"
                ]

        except Exception:
            pass

        # ============================================================
        # ALLE GROSSEN ICONS VERSTECKEN
        # ============================================================

        for day in range(0, 7):

            try:

                self[
                    "bigWeerIcon1"
                    + str(day)
                ].hide()

            except Exception:
                pass

            try:

                self[
                    "bigDirIcon1"
                    + str(day)
                ].hide()

            except Exception:
                pass

        # ============================================================
        # AUSGEWÄHLTES ICON
        # ============================================================

        try:

            self[
                "bigWeerIcon1"
                + str(self.selected)
            ].show()

        except Exception:
            pass

        self._updateCurrentBigIcon()

        try:

            self[
                "bigDirIcon1"
                + str(self.selected)
            ].show()

        except Exception:
            pass

        # ============================================================
        # STUNDEN
        # ============================================================

        try:

            dataPerUur = weatherData[
                "days"
            ][
                self.selected
            ][
                "hours"
            ]

        except Exception:

            dataPerUur = []

        slotHours = self.getSlotHours(
            self.selected
        )

        # ============================================================
        # 8 STUNDENFELDER
        # ============================================================

        for perUurUpdate in range(0, 8):

            for day in range(0, 7):

                try:

                    self[
                        "dayIcon"
                        + str(day)
                        + str(perUurUpdate)
                    ].hide()

                except Exception:
                    pass

            try:

                self[
                    "vlakuur"
                    + str(perUurUpdate)
                ].hide()

            except Exception:
                pass

            for prefix in (
                "sunicon",
                "rainicon",
                "rhicon",
                "windicon"
            ):

                try:

                    self[
                        prefix
                        + str(perUurUpdate)
                    ].hide()

                except Exception:
                    pass

            slotHasData = (
                perUurUpdate
                < len(slotHours)
            )

            if slotHasData:

                try:

                    self[
                        "dayIcon"
                        + str(self.selected)
                        + str(perUurUpdate)
                    ].show()

                except Exception:
                    pass

                try:

                    self[
                        "vlakuur"
                        + str(perUurUpdate)
                    ].show()

                except Exception:
                    pass

                for prefix in (
                    "sunicon",
                    "rainicon",
                    "rhicon",
                    "windicon"
                ):

                    try:

                        self[
                            prefix
                            + str(perUurUpdate)
                        ].show()

                    except Exception:
                        pass

                try:

                    iconpath = (
                        "/usr/lib/enigma2/python/"
                        "Plugins/Extensions/"
                        "speedy_TheWeather/"
                        + icoonpath
                        + "/iconhd/"
                        + str(
                            slotHours[
                                perUurUpdate
                            ]["iconcode"]
                        )
                        + ".png"
                    )

                    self[
                        "dayIcon"
                        + str(self.selected)
                        + str(perUurUpdate)
                    ].instance.setPixmap(
                        _load_icon_cached(
                            iconpath
                        )
                    )

                except Exception:
                    pass

            # ========================================================
            # STUNDENTEXTE
            # ========================================================

            try:

                if slotHasData:

                    entry = slotHours[
                        perUurUpdate
                    ]

                    self[
                        "dayhour3"
                        + str(perUurUpdate)
                    ].setText(
                        str(
                            entry["hour"]
                        ) + _("h")
                    )

                    self[
                        "daytemp3"
                        + str(perUurUpdate)
                    ].setText(
                        '{:>4}'.format(
                            str(
                                "%.0f"
                                % entry[
                                    "temperature"
                                ]
                            )
                            + "\xb0C"
                        )
                    )

                    try:

                        precipitation = entry[
                            "precipation"
                        ]

                    except Exception:

                        precipitation = entry[
                            "precipitation"
                        ]

                    self[
                        "daypercent3"
                        + str(perUurUpdate)
                    ].setText(
                        str(
                            precipitation
                        ) + "%"
                    )

                    self[
                        "dayspeed3"
                        + str(perUurUpdate)
                    ].setText(
                        format_windspeed(
                            entry.get(
                                "windspeed"
                            )
                        )
                    )

                    self[
                        "sunpercent3"
                        + str(perUurUpdate)
                    ].setText(
                        str(
                            entry["sunshine"]
                        ) + "%"
                    )

                    self[
                        "hrdayper3"
                        + str(perUurUpdate)
                    ].setText(
                        str(
                            entry["humidity"]
                        ) + "%"
                    )

                else:

                    for prefix in (
                        "dayhour3",
                        "daytemp3",
                        "daypercent3",
                        "dayspeed3",
                        "sunpercent3",
                        "hrdayper3"
                    ):

                        self[
                            prefix
                            + str(perUurUpdate)
                        ].setText("")

            except Exception:

                try:

                    if slotHasData:

                        entry = slotHours[
                            perUurUpdate
                        ]

                        self[
                            "dayhour3"
                            + str(perUurUpdate)
                        ].setText(
                            str(
                                entry["hour"]
                            ) + _("h")
                        )

                        self[
                            "daytemp3"
                            + str(perUurUpdate)
                        ].setText(
                            '{:>4}'.format(
                                str(
                                    "%.0f"
                                    % entry[
                                        "temperature"
                                    ]
                                )
                                + "\xb0C"
                            )
                        )

                        self[
                            "daypercent3"
                            + str(perUurUpdate)
                        ].setText(
                            str(
                                entry[
                                    "precipitation"
                                ]
                            ) + "%"
                        )

                        self[
                            "dayspeed3"
                            + str(perUurUpdate)
                        ].setText(
                            format_windspeed(
                                entry.get(
                                    "windspeed"
                                )
                            )
                        )

                        self[
                            "sunpercent3"
                            + str(perUurUpdate)
                        ].setText(
                            str(
                                entry["sunshine"]
                            ) + "%"
                        )

                        self[
                            "hrdayper3"
                            + str(perUurUpdate)
                        ].setText(
                            str(
                                entry["humidity"]
                            ) + "%"
                        )

                    else:

                        for prefix in (
                            "dayhour3",
                            "daytemp3",
                            "daypercent3",
                            "dayspeed3",
                            "sunpercent3",
                            "hrdayper3"
                        ):

                            self[
                                prefix
                                + str(perUurUpdate)
                            ].setText("")

                except Exception:

                    try:

                        self[
                            "dayIcon"
                            + str(self.selected)
                            + str(perUurUpdate)
                        ].hide()

                    except Exception:
                        pass

                    try:

                        self[
                            "vlakuur"
                            + str(perUurUpdate)
                        ].hide()

                    except Exception:
                        pass

                    for prefix in (
                        "sunicon",
                        "rainicon",
                        "rhicon",
                        "windicon"
                    ):

                        try:

                            self[
                                prefix
                                + str(perUurUpdate)
                            ].hide()

                        except Exception:
                            pass

    # ================================================================
    # MENU
    # ================================================================

    def KeyMenu(self):

        self.session.open(
            localcityscreen
        )

    # ================================================================
    # LINKS
    # ================================================================

    def left(self):

        self.selected -= 1

        self.updateFrameselect()

    # ================================================================
    # RECHTS
    # ================================================================

    def right(self):

        self.selected += 1

        self.updateFrameselect()

    # ================================================================
    # 14 TAGE
    # ================================================================

    def fourteendays(self):

        self.session.open(
            fourteen
        )

    # ================================================================
    # BACKGROUND
    # ================================================================

    import os

    def loadBackground(self):

        global backgroundpath
        global backgroundAutoWeather

        if (
            not hasattr(
                self,
                'picload'
            )
            or self.picload is None
        ):
            return

        bg_folder = (
            "/usr/lib/enigma2/python/"
            "Plugins/Extensions/"
            "speedy_TheWeather/backgrounds"
        )

        default_bg = (
            "/usr/lib/enigma2/python/"
            "Plugins/Extensions/"
            "speedy_TheWeather/"
            + SHARED_PACK
            + "/backgroundhd_2.png"
        )

        # ============================================================
        # AUTO BACKGROUND
        # ============================================================

        try:

            backgroundAutoWeather = bool(
                config.plugins.speedy_TheWeather
                .autoBackgrounds.value
            )

        except Exception:
            pass

        bgfile = None

        if backgroundAutoWeather:

            try:

                auto_bg = (
                    getAutoWeatherBackground()
                )

                if (
                    auto_bg
                    and os.path.isfile(auto_bg)
                ):

                    bgfile = auto_bg

                    print(
                        "[speedy_TheWeather] "
                        "AUTO Hintergrund: %s"
                        % bgfile
                    )

            except Exception as e:

                print(
                    "[speedy_TheWeather] "
                    "AUTO Hintergrund Fehler: %s"
                    % e
                )

        # ============================================================
        # MANUELL / FALLBACK
        # ============================================================

        if not bgfile:

            if (
                backgroundpath
                and os.path.isabs(
                    backgroundpath
                )
                and os.path.isfile(
                    backgroundpath
                )
            ):

                bgfile = backgroundpath

            elif (
                backgroundpath
                and os.path.isfile(
                    os.path.join(
                        bg_folder,
                        backgroundpath
                    )
                )
            ):

                bgfile = os.path.join(
                    bg_folder,
                    backgroundpath
                )

            elif os.path.isfile(
                default_bg
            ):

                bgfile = default_bg

        # ============================================================
        # KEIN BILD
        # ============================================================

        if (
            not bgfile
            or not os.path.isfile(bgfile)
        ):

            print(
                "[speedy_TheWeather] "
                "Kein gültiger Hintergrund: %s"
                % bgfile
            )

            return

        print(
            "[speedy_TheWeather] "
            "Hintergrund wird geladen: %s"
            % bgfile
        )

        # ============================================================
        # DEKODIEREN
        # ============================================================

        try:

            if sz_w > 1800:

                self.picload.setPara(
                    [
                        1920,
                        1080,
                        1,
                        1,
                        False,
                        1,
                        "#ff000000"
                    ]
                )

            else:

                self.picload.setPara(
                    [
                        1280,
                        720,
                        1,
                        1,
                        False,
                        1,
                        "#ff000000"
                    ]
                )

            self.picload.startDecode(
                bgfile
            )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "loadBackground Fehler: %s"
                % e
            )

    # ================================================================
    # BACKGROUND GELADEN
    # ================================================================

    def bgPictureLoaded(
            self,
            picInfo=None
    ):

        if (
            not hasattr(
                self,
                'picload'
            )
            or self.picload is None
        ):
            return

        if (
            "bgpic" not in self
            or self["bgpic"] is None
            or self["bgpic"].instance is None
        ):
            return

        try:

            ptr = self.picload.getData()

            if ptr is not None:

                self[
                    "bgpic"
                ].instance.setPixmap(
                    ptr
                )

                self[
                    "bgpic"
                ].show()

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "bgPictureLoaded Fehler:",
                e
            )

    # ================================================================
    # RADAR
    # ================================================================

    def openRadar(self):

        global lockaaleStad

        print(
            "[speedy_TheWeather] "
            "openRadar lockaaleStad=%r"
            % lockaaleStad
        )

        lat, lon = getCoordsFromEntry(
            lockaaleStad
        )

        if (
            lat is not None
            and lon is not None
        ):

            parts = safeStr(
                lockaaleStad
            ).split("|")

            location_name = (
                parts[0].strip()
                if parts
                else ""
            )

            print(
                "[speedy_TheWeather] "
                "radar location_name=%r"
                % location_name
            )

            self.session.open(
                RadarScreen,
                lat=lat,
                lon=lon,
                zoom=7,
                location_name=location_name
            )

        else:

            self.session.open(
                MessageBox,
                _(
                    "No radar coordinates for this location.\n"
                    "Remove and re-add it via search to enable radar."
                ),
                MessageBox.TYPE_INFO
            )

    # ================================================================
    # TWO LOCATIONS
    # ================================================================

    def openTwoLocations(self):

        self.session.open(
            twolocations
        )

    # ================================================================
    # SETUP
    # ================================================================

    def openSetup(self):

        self.session.openWithCallback(
            self.setupClosed,
            speedy_TheWeatherSetup
        )

    def setupClosed(
            self,
            changed=False
    ):

        if changed:

            self.close()

            self.session.open(
                sevendays
            )

    # ================================================================
    # BACKGROUND CALLBACK
    # ================================================================

    def backgroundPickerCallback(
            self,
            changed=None
    ):

        if changed:

            self.loadBackground()

    # ================================================================
    # EXIT
    # ================================================================

    def exit(self):

        ClosePlugin()

    # ================================================================
    # CANCEL
    # ================================================================

    def cancel(self):

        ClosePlugin()

class fourteen(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        screen_title = _("7-Tage-Wetter")
        AddNewScreen(self)
        self.onClose.append(lambda: RemoveScreen(self))
        global weatherData
        skin = ""
        if sz_w > 1800:
            dayinfoblok = ""
            lines_size = {'-1.png': [122, 15], '-2.png': [122, 30], '-3.png': [122, 45], '-4.png': [122, 60], '-5.png': [122, 75], '-6.png': [122, 90], '-7.png': [122, 105], '-8.png': [122, 120], '-9.png': [122, 135], '-10.png': [122, 150], '-11.png': [122, 165], '-12.png': [122, 180], '-13.png': [122, 195], '-14.png': [122, 210], '-15.png': [122, 225], '0.png': [122, 5], '1.png': [122, 15], '2.png': [122, 30], '3.png': [122, 45], '4.png': [122, 60], '5.png': [122, 75], '6.png': [122, 90], '7.png': [122, 105], '8.png': [122, 120], '9.png': [122, 135], '10.png': [122, 150], '11.png': [122, 165], '12.png': [122, 180], '13.png': [122, 195], '14.png': [122, 210], '15.png': [122, 225], 'b-1.png': [122, 15], 'b-2.png': [122, 30], 'b-3.png': [122, 45], 'b-4.png': [122, 60], 'b-5.png': [122, 75], 'b-6.png': [122, 90], 'b-7.png': [122, 105], 'b-8.png': [122, 120], 'b-9.png': [122, 135], 'b-10.png': [122, 150], 'b-11.png': [122, 165], 'b-12.png': [122, 180], 'b-13.png': [122, 195], 'b-14.png': [122, 210], 'b-15.png': [122, 225], 'b0.png': [122, 5], 'b1.png': [122, 15], 'b2.png': [122, 30], 'b3.png': [122, 45], 'b4.png': [122, 60], 'b5.png': [122, 75], 'b6.png': [122, 90], 'b7.png': [122, 105], 'b8.png': [122, 120], 'b9.png': [122, 135], 'b10.png': [122, 150], 'b11.png': [122, 165], 'b12.png': [122, 180], 'b13.png': [122, 195], 'b14.png': [122, 210], 'b15.png': [122, 225]}
            dataDagen = weatherData["days"]
            maxheightshift = 2000
            for day in range(0, len(dataDagen)):
                dagenbefore = dataDagen[day]
                tempdiff = 0
                curtemp = int(round(dagenbefore["maxtemperature"]))
                if (day+1) < len(dataDagen):
                    tempdiff = int(round(dataDagen[day + 1]["maxtemperature"]) - curtemp)
                lineheight = 0
                if tempdiff > 0:
                    lineheight = tempdiff * 15
                yposline = (1200-(curtemp * 15))-lineheight
                yposline = (((yposline) + lineheight) - 12)
                if yposline < maxheightshift:
                    maxheightshift = yposline
            maxheightshift = 700-maxheightshift
            maxlowertemp = 0
            maxlowertempmover = 0
            for day in range(0, len(dataDagen)):
                dagenbefore = dataDagen[day]
                tempdiff = 0
                curtemp = int(round(dagenbefore["maxtemperature"]))
                if (day+1) < len(dataDagen):
                    tempdiff = int(round(dataDagen[day + 1]["maxtemperature"]) - curtemp)
                lineheight = 0
                if tempdiff > 0:
                    lineheight = tempdiff * 15
                yposline = (1200-(curtemp * 15))-lineheight
                shiftstart = 130
                rainamount = (int(float(dagenbefore["precipitationmm"]) * 2))
                if rainamount > 1 and rainamount < 10:
                    rainamount = 10
                if rainamount > 100:
                    rainamount = 100
                yposline = yposline + maxheightshift

                tempdiffcold = 0
                curtemp = int(round(dagenbefore["mintemperature"]))
                if (day+1) < len(dataDagen):
                    tempdiffcold = int(round(dataDagen[day + 1]["mintemperature"]) - curtemp)
                lineheightcold = 0
                if tempdiffcold > 0:
                    lineheightcold = tempdiffcold * 15
                yposlinecold = (1200-(curtemp*15)) - lineheightcold
                yposlinecold = yposlinecold+maxheightshift
                thatdaymin = (yposlinecold + 15) + lineheightcold + 54  # take 60 if hight of the linetempmin-label is too low (HD)
                if thatdaymin > maxlowertemp:
                    maxlowertemp = thatdaymin
            if maxlowertemp > sz_h:
                maxlowertempmover = maxlowertemp- sz_h

            for day in range(0, len(dataDagen)):
                dagenbefore = dataDagen[day]
                tempdiff = 0
                curtemp = int(round(dagenbefore["maxtemperature"]))
                if (day+1) < len(dataDagen):
                    tempdiff = int(round(dataDagen[day + 1]["maxtemperature"]) - curtemp)
                lineheight = 0
                if tempdiff > 0:
                    lineheight = tempdiff * 15
                yposline = (1200-(curtemp * 15))-lineheight
                shiftstart = 130
                rainamount = (int(float(dagenbefore["precipitationmm"]) * 2))
                if rainamount > 1 and rainamount < 10:
                    rainamount = 10
                if rainamount > 100:
                    rainamount = 100
                yposline = yposline + maxheightshift

                tempdiffcold = 0
                curtemp = int(round(dagenbefore["mintemperature"]))
                if (day+1) < len(dataDagen):
                    tempdiffcold = int(round(dataDagen[day + 1]["mintemperature"]) - curtemp)
                lineheightcold = 0
                if tempdiffcold > 0:
                    lineheightcold = tempdiffcold * 15
                yposlinecold = (1200-(curtemp*15)) - lineheightcold
                yposlinecold = yposlinecold+maxheightshift

                tempdiff = max(-15, min(15, tempdiff))
                tempdiffcold = max(-15, min(15, tempdiffcold))

                if day < (len(dataDagen) - 1):
                    linesize = """size="%s,%s\"""" % (lines_size[(str(tempdiff) + ".png")][0], lines_size[(str(tempdiff) + ".png")][1])
                    linesizeb = """size="%s,%s\"""" % (lines_size["b" + (str(tempdiffcold) + ".png")][0], lines_size[(str(tempdiffcold) + ".png")][1])
                    dayinfoblok += """
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/lines/""" + str(tempdiff) + """.png" position=\"""" + str((130 + (118 * day)) + 59) + """,""" + str(yposline) + """\" """+linesize+""" zPosition="10" transparent="0" alphatest="blend"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/lines/b""" + str(tempdiffcold) + """.png" position=\"""" + str((130 + (118 * day)) + 59) + """,""" + str(yposlinecold-maxlowertempmover) + """\" """+linesizeb+""" zPosition="10" transparent="0" alphatest="blend"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/lines/bar.png" position=\"""" + str((130 + (118 * day)) + 120) + """,140" size="10,900" zPosition="8" transparent="0" alphatest="blend"/>
                    """

                closedrainbar = int(round(rainamount/3)*3)
                dayinfoblok += """
                    <widget render="Label" source="regenval""" + str(day) + """" position=\"""" + str((134 + (118 * day)) + 0) + """,600" size="118,54" valign="center" halign="center" zPosition="20" font="Regular;25" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget render="Label" source="windspeed""" + str(day) + """" position=\"""" + str((134 + (118 * day)) + 0) + """,435" size="118,54" valign="center" halign="center" zPosition="20" font="Regular;25" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget render="Label" source="regenvalunit""" + str(day) + """" position=\"""" + str((134 + (118 * day)) + 0) + """,600" size="118,54" valign="center" halign="center" zPosition="20" font="Regular;30" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/lines/rain_""" + str(closedrainbar) + """.png" position=\"""" + str((128 + (118 * day)) + 45) + """,""" + str((602) - closedrainbar) + """\" size="60,""" + str(closedrainbar) + """\" zPosition="12" transparent="0" alphatest="blend"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/lines/rainstond.png" position=\"""" + str((110 + (118 * day)) + 45) + """,""" + str((600)) + """\" size="80,10" zPosition="15" transparent="0" alphatest="blend"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/lines/rdot.png" position=\"""" + str(((130 + (118 * day)) + 59)-12) + """,""" + str((((yposline) + lineheight)-12)) + """\" size="25,25" zPosition="10" transparent="0" alphatest="blend"/>
                    <widget name="bigWeerIcon1""" + str(day) + """" position=\"""" + str((130 + (118 * day)) + 28) + """,267" size="72,72" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + icoonpath + """/iconhd/""" + str(dagenbefore["iconcode"]) + """.png" zPosition="1" alphatest="blend"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/lines/bdot.png" position=\"""" + str(((130 + (118 * day)) + 59)-12) + """,""" + str(((yposlinecold) + lineheightcold)-12-maxlowertempmover) + """\" size="25,25" zPosition="10" transparent="0" alphatest="blend"/>
                    <widget name="wind""" + str(day) + """" position=\"""" + str((126 + (118 * day)) + 40) + """,370" size="56,56" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + icoonpath + """/windhd/""" + str(dagenbefore["winddirection"]) + """.png" zPosition="2" transparent="1" alphatest="blend"/>
                    <widget render="Label" source="dagvandeweek""" + str(day) + """" position=\"""" + str((134 + (118 * day)) + 0) + """,155" size="118,54" valign="center" halign="center" zPosition="15" font="Regular;45" foregroundColor="#00ff0000" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget render="Label" source="datumvandeweek""" + str(day) + """" position=\"""" + str((134 + (118 * day)) + 0) + """,195" size="118,54" valign="center" halign="center" zPosition="15" font="Regular;30" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget render="Label" source="linetempmax""" + str(day) + """" position=\"""" + str(((130 + (118 * day))-15) + 59) + """,""" + str(((yposline-45) + lineheight)) + """\" size="90,54" zPosition="15" font="Regular;30" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget render="Label" source="linetempmin""" + str(day) + """" position=\"""" + str(((130 + (118 * day))-15) + 59) + """,""" + str((yposlinecold + 15) + lineheightcold-maxlowertempmover) + """\" size="90,54" zPosition="15" font="Regular;30" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    """
            skin = """
                    <screen name="fourteen" flags="wfNoBorder" position="center,center" size="1920,1080" title=\"""" + screen_title + """">
                    <widget source="Title" foregroundColor="blue" render="Label" position="36,32" size="890,52" font="Regular;32" noWrap="1" transparent="1" valign="center" halign="left" zPosition="1" />
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/bgbluhd.png" position="center,center" size="1920,1080" zPosition="0" alphatest="blend"/>
                    <widget source="global.CurrentTime" render="Label" position="1634,35" size="225,45" transparent="1" zPosition="1" font="Regular;36" foregroundColor="#00ff0000" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%-H:%M:%S</convert></widget>
                    <widget source="global.CurrentTime" render="Label" position="1409,74" size="450,37" transparent="1" zPosition="1" font="Regular;24" foregroundColor="#0000ff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%a %d/%m/%y</convert></widget>
                    <widget render="Label" source="city1" position="608,44" size="705,64" zPosition="3" valign="center" halign="center" font="Regular;48" foregroundColor="#000000ff" backgroundColor="#00202020" transparent="1" />
                    """ + dayinfoblok + """
                    </screen>"""

            for day in range(0, len(dataDagen)):
                dagenbefore = dataDagen[day]
                tempdiff = 0
                curtemp = int(round(dagenbefore["maxtemperature"]))
                if (day+1) < len(dataDagen):
                    tempdiff = int(round(dataDagen[day + 1]["maxtemperature"]) - curtemp)
                lineheight = 0
                if tempdiff > 0:
                    lineheight = tempdiff*15
                yposline = (1200-(curtemp*15))-lineheight
                shiftstart = 130
                rainamount = (int(float(dagenbefore["precipitationmm"])*2))
                if rainamount > 1 and rainamount < 10:
                    rainamount = 10
                if rainamount > 100:
                    rainamount = 100
                yposline = yposline+maxheightshift

                self["windspeed" + str(day)] = StaticText()
                self["windspeed" + str(day)].text = windspeed_with_beaufort(dagenbefore["windspeed"])
                self["regenval" + str(day)] = StaticText()
                self["regenval" + str(day)].text = str(dagenbefore["precipitationmm"]) + " mm"
                self["regenvalunit" + str(day)] = StaticText()
                self["regenvalunit" + str(day)].text = str("")
                curtempcold = int(round(dagenbefore["mintemperature"]))
                self["linetempmax" + str(day)] = StaticText()
                self["linetempmax" + str(day)].text = str(curtemp)
                self["linetempmin" + str(day)] = StaticText()
                self["linetempmin" + str(day)].text = str(curtempcold)
                if day < 14:

                    mydate = dagenbefore["date"][:-9]

                    unixtimecode = time.mktime(
                        datetime.datetime(
                            int(mydate[:4]),
                            int(mydate[5:7]),
                            int(mydate[8:10])
                        ).timetuple()
                    )

                    info1 = _(
                        str(
                            strftime(
                                "%A",
                                localtime(unixtimecode)
                            )
                        ).title()[:2]
                    )

                    info2 = str(
                        strftime(
                            "%d-%m",
                            localtime(unixtimecode)
                        )
                    )

                self["bigWeerIcon1" + str(day)] = Pixmap()

                self["wind" + str(day)] = Pixmap()

                self["city1"] = StaticText()
                self["city1"].text = str(
                    citynamedisplay
                )

                self["dagvandeweek" + str(day)] = StaticText()
                self["dagvandeweek" + str(day)].text = str(
                    info1
                ).upper()

                self["datumvandeweek" + str(day)] = StaticText()
                self["datumvandeweek" + str(day)].text = str(
                    info2
                )
        else:
            dayinfoblok = ""
            lines_size = {'-1.png': [82, 10], '-2.png': [82, 20], '-3.png': [82, 30], '-4.png': [82, 40], '-5.png': [82, 50], '-6.png': [82, 60], '-7.png': [82, 70], '-8.png': [82, 80], '-9.png': [82, 90], '-10.png': [82, 100], '-11.png': [82, 110], '-12.png': [82, 120], '-13.png': [82, 130], '-14.png': [82, 140], '-15.png': [82, 150], '0.png': [82, 3], '1.png': [82, 10], '2.png': [82, 20], '3.png': [82, 30], '4.png': [82, 40], '5.png': [82, 50], '6.png': [82, 60], '7.png': [82, 70], '8.png': [82, 80], '9.png': [82, 90], '10.png': [82, 100], '11.png': [82, 110], '12.png': [82, 120], '13.png': [82, 130], '14.png': [82, 140], '15.png': [82, 150], 'b-1.png': [82, 10], 'b-2.png': [82, 20], 'b-3.png': [82, 30], 'b-4.png': [82, 40], 'b-5.png': [82, 50], 'b-6.png': [82, 60], 'b-7.png': [82, 70], 'b-8.png': [82, 80], 'b-9.png': [82, 90], 'b-10.png': [82, 110], 'b-11.png': [82, 110], 'b-12.png': [82, 120], 'b-13.png': [82, 130], 'b-14.png': [82, 140], 'b-15.png': [82, 150], 'b0.png': [82, 3], 'b1.png': [82, 10], 'b2.png': [82, 20], 'b3.png': [82, 30], 'b4.png': [82, 40], 'b5.png': [82, 50], 'b6.png': [82, 60], 'b7.png': [82, 70], 'b8.png': [82, 80], 'b9.png': [82, 90], 'b10.png': [82, 100], 'b11.png': [82, 110], 'b12.png': [82, 120], 'b13.png': [82, 130], 'b14.png': [82, 140], 'b15.png': [82, 150]}
            dataDagen = weatherData["days"]
            maxheightshift = 1333
            for day in range(0, len(dataDagen)):
                dagenbefore = dataDagen[day]
                tempdiff = 0
                curtemp = int(round(dagenbefore["maxtemperature"]))
                if (day+1) < len(dataDagen):
                    tempdiff = int(round(dataDagen[day + 1]["maxtemperature"]) - curtemp)
                lineheight = 0
                if tempdiff > 0:
                    lineheight = tempdiff * 10
                yposline = (800 - (curtemp * 10))-lineheight
                yposline = (((yposline) + lineheight) - 12)
                if yposline < maxheightshift:
                    maxheightshift = yposline
            maxheightshift = 467 - maxheightshift

            maxlowertemp = 0
            maxlowertempmover = 0
            for day in range(0, len(dataDagen)):
                dagenbefore = dataDagen[day]
                tempdiff = 0
                curtemp = int(round(dagenbefore["maxtemperature"]))
                if (day+1) < len(dataDagen):
                    tempdiff = int(round(dataDagen[day + 1]["maxtemperature"]) - curtemp)
                lineheight = 0
                if tempdiff > 0:
                    lineheight = tempdiff * 10
                yposline = (800 - (curtemp * 10)) - lineheight
                shiftstart = 130
                rainamount = (int(float(dagenbefore["precipitationmm"]) * 2))
                if rainamount > 1 and rainamount < 10:
                    rainamount = 10
                if rainamount > 100:
                    rainamount = 100
                yposline = yposline+maxheightshift

                tempdiffcold = 0
                curtemp = int(round(dagenbefore["mintemperature"]))
                if (day+1) < len(dataDagen):
                    tempdiffcold = int(round(dataDagen[day + 1]["mintemperature"]) - curtemp)
                lineheightcold = 0
                if tempdiffcold > 0:
                    lineheightcold = tempdiffcold * 10
                yposlinecold = (800-(curtemp*10)) - lineheightcold
                yposlinecold = yposlinecold + maxheightshift
                thatdaymin = (yposlinecold + 10) + lineheightcold + 36  # take 40 if hight of the linetempmin-label is too low (SD)
                if thatdaymin > maxlowertemp:
                    maxlowertemp = thatdaymin
            if maxlowertemp > sz_h:
                maxlowertempmover = maxlowertemp- sz_h




            for day in range(0, len(dataDagen)):
                dagenbefore = dataDagen[day]
                tempdiff = 0
                curtemp = int(round(dagenbefore["maxtemperature"]))
                if (day+1) < len(dataDagen):
                    tempdiff = int(round(dataDagen[day + 1]["maxtemperature"]) - curtemp)
                lineheight = 0
                if tempdiff > 0:
                    lineheight = tempdiff * 10
                yposline = (800 - (curtemp * 10)) - lineheight
                shiftstart = 130
                rainamount = (int(float(dagenbefore["precipitationmm"]) * 2))
                if rainamount > 1 and rainamount < 10:
                    rainamount = 10
                if rainamount > 100:
                    rainamount = 100
                yposline = yposline+maxheightshift

                tempdiffcold = 0
                curtemp = int(round(dagenbefore["mintemperature"]))
                if (day+1) < len(dataDagen):
                    tempdiffcold = int(round(dataDagen[day + 1]["mintemperature"]) - curtemp)
                lineheightcold = 0
                if tempdiffcold > 0:
                    lineheightcold = tempdiffcold * 10
                yposlinecold = (800-(curtemp*10)) - lineheightcold
                yposlinecold = yposlinecold + maxheightshift

                tempdiff = max(-15, min(15, tempdiff))
                tempdiffcold = max(-15, min(15, tempdiffcold))

                if day < (len(dataDagen) - 1):
                    linesize = """size="%s,%s\"""" % (lines_size[(str(tempdiff) + ".png")][0], lines_size[(str(tempdiff) + ".png")][1])
                    linesizeb = """size="%s,%s\"""" % (lines_size["b" + (str(tempdiffcold) + ".png")][0], lines_size[(str(tempdiffcold) + ".png")][1])
                    dayinfoblok += """
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/linessd/""" + str(tempdiff) + """.png" position=\"""" + str((86 + (79 * day)) + 39) + """,""" + str(yposline) + """\" """+linesize+""" zPosition="10" transparent="1" alphatest="blend"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/linessd/b""" + str(tempdiffcold) + """.png" position=\"""" + str((86 + (79 * day)) + 39) + """,""" + str(yposlinecold-maxlowertempmover) + """\" """+linesizeb+""" zPosition="10" transparent="1" alphatest="blend"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/linessd/bar.png" position=\"""" + str((86 + (79 * day)) + 80) + """,93" size="3,590" zPosition="8" transparent="0" alphatest="blend"/>
                    """

                closedrainbar = int(round(rainamount/3)*3)
                dayinfoblok += """
                    <widget render="Label" source="regenval""" + str(day) + """" position=\"""" + str((87 + (79 * day)) + 0) + """,400" size="79,36" valign="center" halign="center" zPosition="20" font="Regular;17" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget render="Label" source="windspeed""" + str(day) + """" position=\"""" + str((87 + (79 * day)) + 0) + """,278" size="79,48" valign="center" halign="center" zPosition="20" font="Regular;16" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget render="Label" source="regenvalunit""" + str(day) + """" position=\"""" + str((87 + (79 * day)) + 0) + """,400" size="79,36" valign="center" halign="center" zPosition="20" font="Regular;20" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/linessd/rain_""" + str(closedrainbar) + """.png" position=\"""" + str((80 + (79 * day)) + 30) + """,""" + str((405) - closedrainbar) + """\" size="40,""" + str(closedrainbar) + """\" zPosition="12" transparent="0" alphatest="blend"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/linessd/rainstond.png" position=\"""" + str((64 + (79 * day)) + 30) + """,""" + str((400)) + """\" size="67,7" zPosition="15" transparent="0" alphatest="blend"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/linessd/rdot.png" position=\"""" + str(((87 + (79 * day)) + 39)-8) + """,""" + str((((yposline) + lineheight)-8)) + """\" size="18,18" zPosition="10" transparent="0" alphatest="blend"/>
                    <widget name="bigWeerIcon1""" + str(day) + """" position=\"""" + str((87 + (79 * day)) + 19) + """,178" size="48,48" scale="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + icoonpath + """/iconhd/""" + str(dagenbefore["iconcode"]) + """.png" zPosition="1" alphatest="blend"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/linessd/bdot.png" position=\"""" + str(((87 + (79 * day)) + 39)-8) + """,""" + str(((yposlinecold) + lineheightcold)-8-maxlowertempmover) + """\" size="18,18" zPosition="10" transparent="0" alphatest="blend"/>
                    <widget name="wind""" + str(day) + """" position=\"""" + str((87 + (79 * day)) + 27) + """,240" size="28,28" scale="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + icoonpath + """/windhd/""" + str(dagenbefore["winddirection"]) + """.png" zPosition="2" alphatest="blend"/>
                    <widget render="Label" source="dagvandeweek""" + str(day) + """" position=\"""" + str((87 + (79 * day)) + 0) + """,103" size="79,36" valign="center" halign="center" zPosition="15" font="Regular;30" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget render="Label" source="datumvandeweek""" + str(day) + """" position=\"""" + str((87 + (79 * day)) + 0) + """,130" size="79,36" valign="center" halign="center" zPosition="15" font="Regular;20" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget render="Label" source="linetempmax""" + str(day) + """" position=\"""" + str(((103 + (79 * day))-10) + 26) + """,""" + str(((yposline-35) + lineheight)) + """\" size="60,36" zPosition="15" font="Regular;20" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget render="Label" source="linetempmin""" + str(day) + """" position=\"""" + str(((106 + (79 * day))-10) + 26) + """,""" + str((yposlinecold + 10) + lineheightcold-maxlowertempmover) + """\" size="60,36" zPosition="15" font="Regular;20" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    """
            skin = """
                    <screen name="fourteen" flags="wfNoBorder" position="center,center" size="1920,1080" title=\"""" + screen_title + """">
                    <widget source="Title" foregroundColor="blue" render="Label" position="36,32" size="890,52" font="Regular;32" noWrap="1" transparent="1" valign="center" halign="left" zPosition="1" />
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/bgbluhd.png" position="center,center" size="1280,720" scale="1" zPosition="0" alphatest="blend"/>
                    <widget source="global.CurrentTime" render="Label" position="1091,12" size="150,55" transparent="1" zPosition="1" font="Regular;24" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%-H:%M:%S</convert></widget>
                    <widget source="global.CurrentTime" render="Label" position="941,32" size="300,55" transparent="1" zPosition="1" font="Regular;16" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%a %d/%m/%y</convert></widget>
                    <widget render="Label" source="city1" position="406,30" size="470,43" zPosition="3" valign="center" halign="center" font="Regular;32" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" />
                    """ + dayinfoblok + """
                    </screen>"""
            for day in range(0, len(dataDagen)):
                dagenbefore = dataDagen[day]
                tempdiff = 0
                curtemp = int(round(dagenbefore["maxtemperature"]))
                if (day+1) < len(dataDagen):
                    tempdiff = int(round(dataDagen[day + 1]["maxtemperature"]) - curtemp)
                lineheight = 0
                if tempdiff > 0:
                    lineheight = tempdiff*10
                yposline = (800-(curtemp*10))-lineheight
                shiftstart = 130
                rainamount = (int(float(dagenbefore["precipitationmm"])*2))
                if rainamount > 1 and rainamount < 10:
                    rainamount = 10
                if rainamount > 100:
                    rainamount = 100
                yposline = yposline+maxheightshift

                self["windspeed" + str(day)] = StaticText()
                self["windspeed" + str(day)].text = windspeed_with_beaufort(dagenbefore["windspeed"])
                self["regenval" + str(day)] = StaticText()
                self["regenval" + str(day)].text = str(dagenbefore["precipitationmm"]) + " mm"
                self["regenvalunit" + str(day)] = StaticText()
                self["regenvalunit" + str(day)].text = str("")
                curtempcold = int(round(dagenbefore["mintemperature"]))
                self["linetempmax" + str(day)] = StaticText()
                self["linetempmax" + str(day)].text = str(curtemp)
                self["linetempmin" + str(day)] = StaticText()
                self["linetempmin" + str(day)].text = str(curtempcold)
                if day < 14:

                    mydate = dagenbefore["date"][:-9]
                    unixtimecode = time.mktime(datetime.datetime(int(mydate[:4]), int(mydate[5:][:2]), int(mydate[8:][:2])).timetuple())
                    unixtimecode = unixtimecode
                    info1 = _(str(strftime("%A", localtime(unixtimecode))).title()[:2])
                    info2 = str(strftime("%d-%m", localtime(unixtimecode)))

                self["bigWeerIcon1" + str(day)] = Pixmap()
                self["wind" + str(day)] = Pixmap()
                self["city1"] = StaticText()
                self["city1"].text = str(citynamedisplay)
                self["dagvandeweek" + str(day)] = StaticText()
                self["dagvandeweek" + str(day)].text = str(info1).upper()
                self["datumvandeweek" + str(day)] = StaticText()
                self["datumvandeweek" + str(day)].text = str(info2)
        self.session = session
        self.skin = skin.replace("Format:%a %d/%m/%y", getDateFormat())
        self["myActionMap"] = ActionMap(["SetupActions"], {"ok": self.dayseven, "cancel": self.cancel, "red": self.exit}, -1)

    def dayseven(self):
        self.close()

    def exit(self):
        self.close()

    def cancel(self):
        self.close()

class CitySearchKeyBoard(VirtualKeyBoard):
    def __init__(self, session, title=_("Enter cityname e.g. london"), text=""):
        VirtualKeyBoard.__init__(self, session, title=title, text=text)
        self.skinName = ["CitySearchKeyBoard"]
        for wname in ("prompt", "locale", "key_red", "key_green", "key_yellow", "key_blue"):
            try:
                self[wname]
            except KeyError:
                self[wname] = Label("")

        if sz_w > 1800:
            self.skin = """
                <screen name="CitySearchKeyBoard" position="center,center" size="1200,750" flags="wfNoBorder" title="Virtual keyboard">
                <widget name="prompt" position="15,10" size="1170,30" font="Regular;24" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1"/>
                <widget name="text" position="15,45" size="1170,50" font="Regular;34" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1"/>
                <widget name="list" position="15,105" size="1170,420" transparent="1"/>
                <widget name="locale" position="15,535" size="900,25" font="Regular;18" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1"/>
                <widget name="suggestions" position="15,565" size="1170,180" font="Regular;28" foregroundColor="#00ffff00" backgroundColor="#00202020"/>
                <widget name="key_red" position="15,750" size="200,30" font="Regular;20" foregroundColor="#00ff0000" backgroundColor="#00202020" transparent="1"/>
                <widget name="key_green" position="230,750" size="200,30" font="Regular;20" foregroundColor="#0000ff00" backgroundColor="#00202020" transparent="1"/>
                <widget name="key_yellow" position="445,750" size="200,30" font="Regular;20" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1"/>
                <widget name="key_blue" position="660,750" size="200,30" font="Regular;20" foregroundColor="#000000ff" backgroundColor="#00202020" transparent="1"/>
                </screen>"""
        else:
            self.skin = """
                <screen name="CitySearchKeyBoard" position="center,center" size="800,500" flags="wfNoBorder" title="Virtual keyboard">
                <widget name="prompt" position="10,7" size="780,20" font="Regular;16" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1"/>
                <widget name="text" position="10,30" size="780,33" font="Regular;22" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1"/>
                <widget name="list" position="10,70" size="780,280" transparent="1"/>
                <widget name="locale" position="10,357" size="600,17" font="Regular;12" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1"/>
                <widget name="suggestions" position="10,377" size="780,120" font="Regular;18" foregroundColor="#00ffff00" backgroundColor="#00202020"/>
                <widget name="key_red" position="10,500" size="133,20" font="Regular;14" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1"/>
                <widget name="key_green" position="153,500" size="133,20" font="Regular;14" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1"/>
                <widget name="key_yellow" position="297,500" size="133,20" font="Regular;14" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1"/>
                <widget name="key_blue" position="440,500" size="133,20" font="Regular;14" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1"/>
                </screen>"""

        self["suggestions"] = Label("")
        self.lastCheckedText = text
        self.searchResults = []

        self.suggestTimer = eTimer()
        self._suggestTimerConn = safeTimerCallback(self.suggestTimer, self.checkTextChanged)
        self.suggestTimer.start(400, False)


    def processSelect(self):
        VirtualKeyBoard.processSelect(self)

    def checkTextChanged(self):
        current = self["text"].getText()
        if current != self.lastCheckedText:
            self.lastCheckedText = current
            if len(current) >= 3:
                self.updateSuggestions(current)
            else:
                self["suggestions"].setText("")
                self.searchResults = []

    def close(self, *args):
        if hasattr(self, 'picload') and self.picload is not None:
            try:
                self.picload.PictureData.get().remove(self.bgPictureLoaded)
            except Exception:
                pass
            self.picload = None

        self.suggestTimer.stop()
        VirtualKeyBoard.close(self, *args)

    def updateSuggestions(self, searchterm):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
            cookie_jar = cookielib.CookieJar()
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
            urllib2.install_opener(opener)
            req = urllib2.Request("https://location.buienradar.nl/1.1/location/search?query=" + searchterm.replace(" ", "%20"), data=None, headers=headers)
            handler = urllib2.urlopen(req, timeout=8)
            antw = handler.read()
            self.searchResults = json.loads(antw)
        except Exception as e:
            print("[speedy_TheWeather] updateSuggestions fout:", e)
            self.searchResults = []
        print("[speedy_TheWeather] DEBUG eerste zoekresultaat:", self.searchResults[0] if self.searchResults else "leeg")
        names = [r.get("name", "") + " (" + r.get("countrycode", "") + ")" for r in self.searchResults[:6]]
        text = "\n".join(names)
        if not PY3 and isinstance(text, unicode):
            text = text.encode("utf-8")
        self["suggestions"].setText(text)

class localcityscreen(Screen):
    def __init__(self, session):
        if sz_w > 1800:
            skin = """
                    <screen name="startScreen" flags="wfNoBorder" position="center,center" size="1920,1080">
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png" position="0,112" size="1920,3" zPosition="1"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png" position="0,1010" size="1920,3" zPosition="1"/>
                    <widget source="global.CurrentTime" render="Label" position="1634,35" size="225,45" transparent="1" zPosition="3" font="Regular;36" foregroundColor="#00ff0000" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%-H:%M:%S</convert></widget>
                    <widget source="global.CurrentTime" render="Label" position="1409,74" size="450,37" transparent="1" zPosition="3" font="Regular;24" foregroundColor="#0000ff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%a %d/%m/%y</convert></widget>
                    <widget source="session.VideoPicture" render="Pig" position="30,160" size="720,405" backgroundColor="#ff000000" zPosition="1"/>
                    <widget source="session.CurrentService" render="Label" position="30,125" size="720,36" zPosition="1" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" font="Regular;28" noWrap="1" valign="center" halign="center"><convert type="ServiceName">Name</convert></widget>
                    <widget name="list" position="840,225" size="975,630" scrollbarMode="showOnDemand" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/list/list97563.png"/>\n
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red34.png" position="192,1022" size="34,34" alphatest="blend"/>
                    <widget name="key_red" position="242,1015" size="370,48" zPosition="1" font="Regular;40" halign="left" foregroundColor="#00ff0000" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/green34.png" position="628,1022" size="34,34" alphatest="blend"/>
                    <widget name="key_green" position="678,1015" size="370,48" zPosition="1" font="Regular;40" halign="left" foregroundColor="#0000ff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/yellow34.png" position="1064,1022" size="34,34" alphatest="blend"/>
                    <widget name="key_yellow" position="1114,1015" size="370,48" zPosition="1" font="Regular;40" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/blue34.png" position="1500,1022" size="34,34" alphatest="blend"/>
                    <widget name="key_blue" position="1550,1015" size="370,48" zPosition="1" font="Regular;40" halign="left" foregroundColor="#000000ff" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget name="favor" position="85,45" size="1085,55" valign="center" halign="left" zPosition="1" font="Regular;36" foregroundColor="#000000ff" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget name="helpinfo" position="150,722" size="500,600" valign="top" halign="left" zPosition="1" font="Regular;36" foregroundColor="#00ff0000" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget name="plaatsn" position="840,135" size="375,70" valign="center" halign="left" zPosition="1" font="Regular;63" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    </screen>"""
        else:
            skin = """
                    <screen name="startScreen" flags="wfNoBorder" position="center,center" size="1280,720">
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline2.png" position="0,88" size="1280,2" zPosition="1"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline2.png" position="0,630" size="1280,2" zPosition="1"/>
                    <widget source="global.CurrentTime" render="Label" position="1091,12" size="150,55" transparent="1" zPosition="1" font="Regular;24" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%-H:%M:%S</convert></widget>
                    <widget source="global.CurrentTime" render="Label" position="941,32" size="300,55" transparent="1" zPosition="1" font="Regular;16" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%a %d/%m/%y</convert></widget>
                    <widget source="session.VideoPicture" render="Pig" position="85,120" size="417,243" backgroundColor="#ff000000" zPosition="1"/>
                    <widget source="session.CurrentService" render="Label" position="85,93" size="417,32" zPosition="1" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" font="Regular;28" noWrap="1" valign="center" halign="center"><convert type="ServiceName">Name</convert></widget>
                    <widget name="list" position="630,156" size="650,420" scrollbarMode="showOnDemand" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/list/list65043.png"/>\n
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red26.png" position="145,663" size="26,26" alphatest="blend"/>
                    <widget name="key_red" position="185,663" size="220,32" zPosition="1" font="Regular;24" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/green26.png" position="420,663" size="26,26" alphatest="blend"/>
                    <widget name="key_green" position="460,663" size="220,32" zPosition="1" font="Regular;24" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/yellow26.png" position="695,663" size="26,26" alphatest="blend"/>
                    <widget name="key_yellow" position="735,663" size="220,32" zPosition="1" font="Regular;24" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/blue26.png" position="970,663" size="26,26" alphatest="blend"/>
                    <widget name="key_blue" position="1010,663" size="220,32" zPosition="1" font="Regular;24" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget name="favor" position="57,30" size="723,37" valign="center" halign="left" zPosition="1" font="Regular;24" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget name="helpinfo" position="100,481" size="335,320" valign="top" halign="left" zPosition="1" font="Regular;20" foregroundColor="#00ff0000" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget name="plaatsn" position="630,90" size="250,47" valign="center" halign="left" zPosition="1" font="Regular;42" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    </screen>"""

        self.session = session
        Screen.__init__(self, session)
        self.skin = skin.replace("Format:%a %d/%m/%y", getDateFormat())
        AddNewScreen(self)
        self.onClose.append(lambda: RemoveScreen(self))

        self["key_red"] = Label(_("Exit"))
        self["key_green"] = Label(_("Location +"))
        self["key_yellow"] = Label(_("Location -"))
        self["key_blue"] = Label(_("Settings"))
        self["favor"] = Label(_("Favorite Locations"))

        self.helpInfoDefault = _("Select city and:") + "\n" + _("- Press Ok for Weather info") + "\n" + _("- Press Menu for RainRadar")
        self["helpinfo"] = Label(self.helpInfoDefault)

        self["plaatsn"] = Label(_("Location:"))
        self.radarLoadTimer = eTimer()
        self._radarLoadTimerConn = safeTimerCallback(self.radarLoadTimer, self._openRadarDeferred)
        self.res = []
        self._citySearchTimer = eTimer()
        self._citySearchTimerConn = safeTimerCallback(self._citySearchTimer, self._pollCitySearch)
        self._citySearchThread = None
        self._citySearchResult = None
        self._citySearchError = None
        self._citySearchRequestId = 0
        self._citySearchBusy = False

        global SavedLokaleWeer
        for x in SavedLokaleWeer:
            cleanmadecity = stripCoords(x).rsplit("-", 1)[0]
            if sz_w > 1800:
                self.res.append([x, MultiContentEntryText(pos=(0, 0), size=(960, 63), font=0, flags=RT_HALIGN_LEFT, text=cleanmadecity, color_sel=0x00D2D226)])
            else:
                self.res.append([x, MultiContentEntryText(pos=(0, 0), size=(590, 42), font=0, flags=RT_HALIGN_LEFT, text=cleanmadecity, color_sel=0x00D2D226)])

        self["list"] = MenuList(self.res, True, eListboxPythonMultiContent)
        if sz_w > 1800:
            self["list"].l.setItemHeight(63)
            self['list'].l.setFont(0, gFont("Regular", 50))
        else:
            self["list"].l.setItemHeight(42)
            self['list'].l.setFont(0, gFont("Regular", 33))

        self["list"].show()
        self["actions"] = ActionMap(["WizardActions", "MenuActions", "ShortcutActions"], {"ok": self.go, "back": self.cancel, "menu": self.openRadarForSelected}, -1)
        self["ColorActions"] = HelpableActionMap(self, "ColorActions", {"red": self.exit, "yellow": self.removeLoc, "green": self.addLoc, "blue": self.addcityinf}, -1)

    def go(self):
        if len(SavedLokaleWeer) > 0:
            index = self["list"].getSelectedIndex()
            selecteddat = self.res[index][0]
            try:
                if getLocWeer(selecteddat.rstrip()):
                    file = open(CFG_DIR + "/speedy_TheWeather_last.cfg", "w")
                    file.write(selecteddat)
                    file.close()
                    self.session.open(sevendays)
                else:
                    self.session.open(MessageBox, _("Download error: Check spelling."), MessageBox.TYPE_INFO)
            except Exception:
                self.session.open(MessageBox, _("Download error: No response try again"), MessageBox.TYPE_INFO)

    def openRadarForSelected(self):
        if len(SavedLokaleWeer) > 0:
            index = self["list"].getSelectedIndex()
            selecteddat = self.res[index][0]
            lat, lon = getCoordsFromEntry(selecteddat)
            if lat is not None and lon is not None:
                self.pendingRadarCoords = (lat, lon)
                self["helpinfo"].setText(_("Loading radar..."))
                self.radarLoadTimer.start(50, True)
            else:
                self.session.open(MessageBox, _("No radar coordinates for this location.\nRemove and re-add it to enable radar."), MessageBox.TYPE_INFO)

    def _openRadarDeferred(self):
        global lockaaleStad

        lat, lon = self.pendingRadarCoords

        # Dynamischen Zoom aus den Einstellungen holen
        user_zoom = int(
            config.plugins.speedy_TheWeather.defaultzoom.value
        )

        # Ortsnamen aus dem gespeicherten Eintrag holen
        parts = safeStr(lockaaleStad).split("|")
        location_name = (
            parts[0].strip()
            if parts
            else ""
        )

        print(
            "[speedy_TheWeather] "
            "Radar deferred location=%r"
            % location_name
        )

        self.session.openWithCallback(
            self._radarClosed,
            RadarScreen,
            lat=lat,
            lon=lon,
            zoom=user_zoom,
            location_name=location_name
        )

    def _radarClosed(self, *args):
        self["helpinfo"].setText(self.helpInfoDefault)

    def addLoc(self):
        self.session.openWithCallback(self.onCityTyped, CitySearchKeyBoard, title=_("Enter cityname e.g. london"), text="")

    def removeLoc(self):
        if not SavedLokaleWeer:
            return

        index = self["list"].getSelectedIndex()
        if index < 0 or index >= len(SavedLokaleWeer):
            return

        del SavedLokaleWeer[index]

        try:
            with open(CFG_DIR + "/speedy_TheWeather.cfg", "w") as file:
                for x in SavedLokaleWeer:
                    file.write(safeStr(x) + "\n")
        except Exception as e:
            print("[speedy_TheWeather] Could not save locations after removal: %s" % e)
            return

        self.close()

    def onCityTyped(self, searchterm=None):
        if not searchterm or self._citySearchBusy:
            return

        self._citySearchRequestId += 1
        req_id = self._citySearchRequestId
        self._citySearchBusy = True
        self._citySearchResult = None
        self._citySearchError = None

        query = safeStr(searchterm).strip()

        # Falls der Eingabewert z.B. "Berlin(DE)" enthält,
        # nur "Berlin" an die Suche übergeben.
        if "(" in query and query.endswith(")"):
            query = query.rsplit("(", 1)[0].strip()

        print(
            "[speedy_TheWeather] CITY SEARCH START: '%s'"
            % query
        )

        def worker():
            try:
                if getattr(self, "_closed", False):
                    print(
                        "[speedy_TheWeather] CITY SEARCH: "
                        "Screen bereits geschlossen"
                    )
                    return

                url = (
                    "https://location.buienradar.nl/1.1/"
                    "location/search?query=%s"
                    % quote_plus(query)
                )

                print(
                    "[speedy_TheWeather] CITY SEARCH URL: %s"
                    % url
                )

                results = _http_json(
                    url,
                    timeout=12
                )

                # WICHTIG:
                # Default muss False sein!
                if getattr(self, "_closed", False):
                    return

                if req_id != getattr(
                    self,
                    "_citySearchRequestId",
                    None
                ):
                    print(
                        "[speedy_TheWeather] CITY SEARCH: "
                        "alte Anfrage verworfen"
                    )
                    return

                if not isinstance(results, list):
                    results = []

                self._citySearchResult = results

                print(
                    "[speedy_TheWeather] CITY SEARCH: "
                    "%d Ergebnisse"
                    % len(results)
                )

            except Exception as e:

                # Auch hier MUSS der Default False sein.
                if getattr(self, "_closed", False):
                    return

                if req_id == getattr(
                    self,
                    "_citySearchRequestId",
                    None
                ):
                    self._citySearchError = e

                print(
                    "[speedy_TheWeather] CITY SEARCH FEHLER: %s"
                    % str(e)
                )

        self._citySearchThread = threading.Thread(
            target=worker
        )
        self._citySearchThread.daemon = True
        self._citySearchThread.start()

        self._citySearchTimer.start(
            100,
            True
        )


    def _pollCitySearch(self):

        if (
            self._citySearchResult is None
            and self._citySearchError is None
        ):

            if (
                self._citySearchThread is not None
                and self._citySearchThread.is_alive()
            ):
                self._citySearchTimer.start(
                    100,
                    True
                )
                return

        result = self._citySearchResult
        error = self._citySearchError

        self._citySearchResult = None
        self._citySearchError = None
        self._citySearchBusy = False

        if error is not None:

            print(
                "[speedy_TheWeather] city search error: %s"
                % str(error)
            )

            self.session.open(
                MessageBox,
                _("No matching cities found."),
                MessageBox.TYPE_INFO
            )

            return

        if not result:

            print(
                "[speedy_TheWeather] CITY SEARCH: "
                "keine Ergebnisse"
            )

            self.session.open(
                MessageBox,
                _("No matching cities found."),
                MessageBox.TYPE_INFO
            )

            return

        print(
            "[speedy_TheWeather] ÖFFNE "
            "CitySuggestListScreen mit %d Ergebnissen"
            % len(result)
        )

        self.session.openWithCallback(
            self.onCityChosen,
            CitySuggestListScreen,
            result
        )

    def close(self, *args):
        self._citySearchRequestId += 1
        self._citySearchBusy = False

        try:
            self._citySearchTimer.stop()
        except Exception:
            pass

        try:
            self.radarLoadTimer.stop()
        except Exception:
            pass

        Screen.close(self, *args)

    def onCityChosen(self, chosen=None):
        if chosen is None:
            return

        loc = chosen.get("location") or {}
        name = safeStr(chosen.get("name", ""))
        city_id = chosen.get("id", "")
        entry = "%s-%s|%s|%s" % (
            name,
            city_id,
            loc.get("lat", ""),
            loc.get("lon", "")
        )

        global SavedLokaleWeer

        # Die Buienradar-City-ID ist die stabile Kennung der Stadt.
        # Damit werden Dubletten auch bei abweichender Schreibweise oder
        # unterschiedlichen Koordinaten verhindert.
        duplicate = False
        city_id_text = safeStr(city_id).strip()
        if city_id_text:
            for saved in SavedLokaleWeer:
                saved_parts = stripCoords(safeStr(saved)).rsplit("-", 1)
                if (
                    len(saved_parts) == 2
                    and safeStr(saved_parts[1]).strip() == city_id_text
                ):
                    duplicate = True
                    break

        if not duplicate and entry not in SavedLokaleWeer:
            SavedLokaleWeer.append(entry)

        try:
            with open(CFG_DIR + "/speedy_TheWeather.cfg", "w") as file:
                for x in SavedLokaleWeer:
                    file.write(safeStr(x) + "\n")
        except Exception as e:
            print("[speedy_TheWeather] Could not save location: %s" % e)
            self.session.open(
                MessageBox,
                _("Could not save the selected location."),
                MessageBox.TYPE_ERROR
            )
            return

        self.close()

    def addcityinf(self):
        # Öffnet direkt den Setup-Bildschirm (Blaue Taste).
        self.session.open(speedy_TheWeatherSetup)

    def exit(self):
        self.close()

    def cancel(self):
        self.close()

# 2. Der Setup-Bildschirm (macht die Optionen im Menü sichtbar)

from Components.Label import Label
from Components.config import ConfigNothing
from Screens.MessageBox import MessageBox

class speedy_TheWeatherSetup(ConfigListScreen, Screen):

    skin = """
    <screen name="speedy_TheWeatherSetup"
        position="410,220"
        size="1100,640"
        title="speedy_TheWeather Settings">

        <widget name="config"
            position="4,4"
            size="1070,550"
            scrollbarMode="showOnDemand"
            itemHeight="45"
            itemTextSelectedColor="#ffffff"
            itemTextUnselectedColor="#ffffff"
            font="Regular; 25" />

        <!-- Roter Button -->
        <ePixmap
            pixmap="skin_default/buttons/red.png"
            position="11,593"
            size="20,40"
            alphatest="on"
            zPosition="1" />

        <widget name="key_red"
            position="36,593"
            size="240,40"
            zPosition="2"
            transparent="1"
            font="Regular;20"
            halign="center"
            valign="center" />

        <!-- Grüner Button -->
        <ePixmap
            pixmap="skin_default/buttons/green.png"
            position="282,593"
            size="20,40"
            alphatest="on"
            zPosition="1" />

        <widget name="key_green"
            position="308,593"
            size="240,40"
            zPosition="2"
            transparent="1"
            font="Regular;20"
            halign="center"
            valign="center"
            foregroundColor="green" />

        <!-- Blauer Button -->
        <ePixmap
            pixmap="skin_default/buttons/blue.png"
            position="825,593"
            size="20,40"
            alphatest="on"
            zPosition="1" />

        <widget name="key_blue"
            position="851,593"
            size="240,40"
            zPosition="2"
            transparent="1"
            font="Regular;20"
            halign="center"
            valign="center"
            foregroundColor="blue" />

        <!-- Gelber Button -->
        <ePixmap
            pixmap="skin_default/buttons/yellow.png"
            position="554,593"
            size="20,40"
            alphatest="on"
            zPosition="1" />

        <widget name="key_yellow"
            position="579,593"
            size="240,40"
            zPosition="2"
            transparent="1"
            font="Regular;20"
            halign="center"
            valign="center"
            foregroundColor="yellow" />

        <!-- Version -->
        <widget name="Version"
            position="676,554"
            size="420,40"
            font="Regular;26"
            halign="center"
            valign="center"
            foregroundColor="red"
            transparent="1"
            backgroundColor="black" />

    </screen>
    """

    # ========================================================
    # INIT
    # ========================================================

    def __init__(self, session):

        Screen.__init__(
            self,
            session
        )

        self.session = session

        self._updateCheckTimer = None

        self.setTitle(
            _("speedy_TheWeather Settings")
        )

        # ====================================================
        # FARBIGE TASTEN
        # ====================================================

        self["key_red"] = Label(
            _("Cancel")
        )

        self["key_green"] = Label(
            _("Save")
        )

        self["key_blue"] = Label(
            _("Show 2 locations")
        )

        self["key_yellow"] = Label(
            _("Appearance")
        )

        # ====================================================
        # VERSION
        # ====================================================

        self["Version"] = Label(
            "speedy_TheWeather_v.%s" % VERSION
        )

        # ====================================================
        # SONDER-EINTRÄGE
        # ====================================================

        self.updateEntry = ConfigNothing()

        self.autoBackgroundDownloadEntry = ConfigNothing()

        self.sevenDayColorEntry = ConfigNothing()
        self.twolocationsColorEntry = ConfigNothing()
        # ====================================================
        # CONFIG-LISTE
        # ====================================================

        self.list = []

        # ----------------------------------------------------
        # Windgeschwindigkeit
        # ----------------------------------------------------

        self.list.append(
            getConfigListEntry(
                _("Wind speed:"),
                config.plugins.speedy_TheWeather.windunit
            )
        )

        # ----------------------------------------------------
        # Datumsformat
        # ----------------------------------------------------

        self.list.append(
            getConfigListEntry(
                _("Date format:"),
                config.plugins.speedy_TheWeather.dateformat
            )
        )

        # ----------------------------------------------------
        # Radar Zoom
        # ----------------------------------------------------

        self.list.append(
            getConfigListEntry(
                _("Radar default zoom:"),
                config.plugins.speedy_TheWeather.defaultzoom
            )
        )

        # ----------------------------------------------------
        # Performance
        # ----------------------------------------------------

        self.list.append(
            getConfigListEntry(
                _("Performance:"),
                config.plugins.speedy_TheWeather.performance
            )
        )

        # ====================================================
        # AUTO WEATHER BACKGROUNDS
        # ====================================================

        self.list.append(
            getConfigListEntry(
                _("Auto weather backgrounds:"),
                config.plugins.speedy_TheWeather.autoBackgrounds
            )
        )

        # ====================================================
        # HOLIDAY BACKGROUNDS
        # ====================================================

        self.list.append(
            getConfigListEntry(
                _("Holiday backgrounds:"),
                config.plugins.speedy_TheWeather.holidayBackgrounds
            )
        )

        # ====================================================
        # DOWNLOAD AUTO BACKGROUNDS
        # ====================================================

        self.list.append(
            getConfigListEntry(
                _("Download weather backgrounds"),
                self.autoBackgroundDownloadEntry
            )
        )

        # ====================================================
        # SEVENDAY FARBEN
        # ====================================================

        self.list.append(
            getConfigListEntry(
                _("SevenDay Farben einstellen:"),
                self.sevenDayColorEntry
            )
        )
        # ====================================================
        # TWO LOCATIONS FARBEN
        # ====================================================

        self.list.append(
            getConfigListEntry(
                _("Two Locations Farben einstellen:"),
                self.twolocationsColorEntry
            )
        )

        # ====================================================
        # UPDATE
        # ====================================================

        self.list.append(
            getConfigListEntry(
                _("Search for update"),
                self.updateEntry
            )
        )

        # ====================================================
        # CONFIG LIST SCREEN
        # ====================================================

        ConfigListScreen.__init__(
            self,
            self.list,
            session=session
        )

        # ====================================================
        # ACTION MAP
        # ====================================================

        self["actions"] = ActionMap(
            [
                "SetupActions",
                "ColorActions"
            ],
            {
                "green": self.save,
                "save": self.save,

                "red": self.keyCancel,
                "cancel": self.keyCancel,

                "blue": self.openTwoLocations,

                "yellow": self.openAppearance,

                "ok": self.handleOk,
            },
            -2
        )

    # ========================================================
    # OK-TASTE
    # ========================================================

    def handleOk(self):

        current = self["config"].getCurrent()

        if not current:
            return

        try:

            entry = current[1]

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "Could not read current entry: %s"
                % e
            )

            return

        # ====================================================
        # AUTO BACKGROUNDS
        # ====================================================

        if entry is self.autoBackgroundDownloadEntry:

            print(
                "[speedy_TheWeather] "
                "Weather background download selected."
            )

            self.downloadAutoBackgrounds()

            return

        # ====================================================
        # SEVENDAY FARBEN
        # ====================================================

        if entry is self.sevenDayColorEntry:

            print(
                "[speedy_TheWeather] "
                "SevenDay color settings selected."
            )

            try:

                self.session.open(
                    sevendayColorSetup
                )

            except Exception as e:

                print(
                    "[speedy_TheWeather] "
                    "Could not open SevenDay colors: %s"
                    % e
                )

                self.session.open(
                    MessageBox,
                    _(
                        "Could not open the SevenDay "
                        "color settings."
                    ),
                    MessageBox.TYPE_ERROR
                )

            return

        # ====================================================
        # TWO LOCATIONS FARBEN
        # ====================================================

        if entry is self.twolocationsColorEntry:

            print(
                "[speedy_TheWeather] "
                "Two Locations color settings selected."
            )

            try:

                self.session.open(
                    twolocationsColorSetup
                )

            except Exception as e:

                print(
                    "[speedy_TheWeather] "
                    "Could not open Two Locations colors: %s"
                    % e
                )

                self.session.open(
                    MessageBox,
                    _(
                        "Could not open the Two Locations "
                        "color settings."
                    ),
                    MessageBox.TYPE_ERROR
                )

            return

        # ====================================================
        # UPDATE
        # ====================================================

        if entry is self.updateEntry:

            print(
                "[speedy_TheWeather] "
                "Manual update check selected."
            )

            self.checkUpdate()

            return

        # ====================================================
        # NORMALE CONFIG-EINTRÄGE
        # ====================================================

        ConfigListScreen.keyOK(
            self
        )

    # ========================================================
    # DOWNLOAD AUTO BACKGROUNDS
    # ========================================================

    def downloadAutoBackgrounds(self):

        print(
            "[speedy_TheWeather] "
            "Opening background download confirmation."
        )

        self.session.openWithCallback(
            self.downloadAutoBackgroundsConfirmed,
            MessageBox,
            _(
                "Do you want to download the "
                "weather backgrounds now?"
            ),
            MessageBox.TYPE_YESNO,
            default=True
        )

    # ========================================================
    # DOWNLOAD AUTO BACKGROUNDS CONFIRMED
    # ========================================================

    def downloadAutoBackgroundsConfirmed(
        self,
        answer
    ):

        if not answer:

            print(
                "[speedy_TheWeather] "
                "Background download cancelled."
            )

            return

        print(
            "[speedy_TheWeather] "
            "Starting background download."
        )

        try:

            result = ensureAutoBackgrounds()

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "Background download exception: %s"
                % e
            )

            result = False

        if result:

            self.session.open(
                MessageBox,
                _(
                    "The weather backgrounds "
                    "were downloaded successfully."
                ),
                MessageBox.TYPE_INFO,
                timeout=5
            )

        else:

            self.session.open(
                MessageBox,
                _(
                    "The weather backgrounds "
                    "could not be downloaded."
                ),
                MessageBox.TYPE_ERROR
            )

    # ========================================================
    # MANUAL UPDATE CHECK
    # ========================================================

    def checkUpdate(self):

        global _overlaySession
        global _updatePollTimer
        global _updateWorkerStarted
        global _updateInfo

        # ----------------------------------------------------
        # Sicherheit: wirklich Update-Menüpunkt ausgewählt?
        # ----------------------------------------------------

        try:

            current = self["config"].getCurrent()

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "Could not get current config entry: %s"
                % e
            )

            return

        if not current:

            return

        if current[1] is not self.updateEntry:

            return

        # ----------------------------------------------------
        # Aktuelle Session für das globale Update-System setzen
        # ----------------------------------------------------

        _overlaySession = self.session

        _updateInfo = None

        print(
            "[speedy_TheWeather] "
            "Starting manual update check..."
        )

        # ----------------------------------------------------
        # Alten globalen Poll-Timer stoppen
        # ----------------------------------------------------

        try:

            if _updatePollTimer is not None:

                _updatePollTimer.stop()

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "Could not stop update poll timer: %s"
                % e
            )

        # ----------------------------------------------------
        # Falls bereits ein Worker läuft, keinen zweiten starten
        # ----------------------------------------------------

        if _updateWorkerStarted:

            print(
                "[speedy_TheWeather] "
                "Update worker already running."
            )

            return

        # ----------------------------------------------------
        # Alte Queue-Einträge entfernen
        #
        # Dadurch verarbeitet die neue Suche keine alten
        # Update-Ergebnisse.
        # ----------------------------------------------------

        try:

            while True:

                _updateQueue.get_nowait()

        except Exception:

            pass

        # ----------------------------------------------------
        # Globalen Poll-Timer sicherstellen
        #
        # WICHTIG:
        # NUR _update_poll() liest die Queue.
        # Es gibt KEINEN lokalen checkUpdateQueue()-Timer mehr.
        # ----------------------------------------------------

        try:

            if _updatePollTimer is None:

                _updatePollTimer = eTimer()

                _updatePollTimer.callback.append(
                    safeTimerCallback(
                        _update_poll
                    )
                )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "Could not create update poll timer: %s"
                % e
            )

            self.session.open(
                MessageBox,
                _(
                    "Update check failed."
                ),
                MessageBox.TYPE_ERROR
            )

            return

        # ----------------------------------------------------
        # Poller starten
        #
        # Nach 500 ms wird _update_poll() aufgerufen.
        # _update_poll() startet sich danach selbst erneut.
        # ----------------------------------------------------

        try:

            _updatePollTimer.start(
                500,
                True
            )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "Could not start update poll timer: %s"
                % e
            )

        # ----------------------------------------------------
        # Update Worker starten
        # ----------------------------------------------------

        try:

            _updateWorkerStarted = True

            thread = threading.Thread(
                target=_update_check_worker,
                name="speedy_TheWeather_ConfigUpdateCheck"
            )

            thread.daemon = True

            thread.start()

            print(
                "[speedy_TheWeather] "
                "Manual update worker started."
            )

        except Exception as e:

            _updateWorkerStarted = False

            print(
                "[speedy_TheWeather] "
                "Could not start update worker: %s"
                % e
            )

            try:

                _updateQueue.put(
                    (
                        "error",
                        _(
                            "Update check failed."
                        )
                    )
                )

            except Exception:

                pass

    # ========================================================
    # TWO LOCATIONS
    # ========================================================

    def openTwoLocations(self):

        self.session.open(
            twolocations
        )

    # ========================================================
    # APPEARANCE
    # ========================================================

    def openAppearance(self):

        self.session.open(
            infoscreen
        )

    # ========================================================
    # SAVE
    # ========================================================

    def save(self):

        for item in self["config"].list:

            try:

                item[1].save()

            except Exception:

                pass

        configfile.save()

        self.close(
            True
        )

    # ========================================================
    # CANCEL
    # ========================================================

    def keyCancel(self):

        for item in self["config"].list:

            try:

                item[1].cancel()

            except Exception:

                pass

        self.close()

    # ========================================================
    # CLEANUP
    # ========================================================


    def __del__(self):

        try:

            if _updatePollTimer is not None:

                _updatePollTimer.stop()

        except Exception:

            pass




class sevendayColorSetup(ConfigListScreen, Screen):
    """
    Separates Farbmenü für den SevenDay-Screen.

    Alle Farben sind ConfigSelection-Werte.
    """

    skin = """
    <screen name="sevendayColorSetup"
        position="center,center"
        size="1100,700"
        title="SevenDay Farben">

        <widget name="config"
            position="4,4"
            size="1070,600"
            scrollbarMode="showOnDemand"
            itemHeight="45"
            itemTextSelectedColor="#ffffff"
            itemTextUnselectedColor="#ffffff"
            font="Regular;30" />

        <ePixmap
            pixmap="skin_default/buttons/red.png"
            position="11,650"
            size="20,40"
            alphatest="on"
            zPosition="1" />

        <widget name="key_red"
            position="36,650"
            size="240,40"
            zPosition="2"
            transparent="1"
            font="Regular;25"
            halign="center"
            valign="center" />

        <ePixmap
            pixmap="skin_default/buttons/green.png"
            position="282,650"
            size="20,40"
            alphatest="on"
            zPosition="1" />

        <widget name="key_green"
            position="308,650"
            size="240,40"
            zPosition="2"
            transparent="1"
            font="Regular;25"
            halign="center"
            valign="center"
            foregroundColor="green" />

        <ePixmap
            pixmap="skin_default/buttons/yellow.png"
            position="554,650"
            size="20,40"
            alphatest="on"
            zPosition="1" />

        <widget name="key_yellow"
            position="579,650"
            size="240,40"
            zPosition="2"
            transparent="1"
            font="Regular;25"
            halign="center"
            valign="center"
            foregroundColor="yellow" />

        <ePixmap
            pixmap="skin_default/buttons/blue.png"
            position="825,650"
            size="20,40"
            alphatest="on"
            zPosition="1" />

        <widget name="key_blue"
            position="851,650"
            size="240,40"
            zPosition="2"
            transparent="1"
            font="Regular;25"
            halign="center"
            valign="center"
            foregroundColor="blue" />

    </screen>
    """

    _ENTRIES = (
        ("Stadt / Ort", "city"),
        ("Aktuelle Temperatur", "bigtemp"),
        ("Wetterbeschreibung", "weathertype"),
        ("Gefühlte Temperatur", "feels"),
        ("Windrichtung", "wind"),
        ("Wochentag", "day"),
        ("Höchsttemperatur", "maxtemp"),
        ("Tiefsttemperatur", "mintemp"),
        ("Tages-Wettertext", "daytype"),
        ("Sonnenaufgang", "sunrise"),
        ("Sonnenuntergang", "sunset"),
        ("Mondaufgang", "moonrise"),
        ("Monduntergang", "moonset"),
        ("Trennzeichen Sonne / Mond", "sun"),
        ("Stunde / Uhrzeit", "hour"),
        ("Stundentemperatur", "hourtemp"),
        ("Regen", "rain"),
        ("Sonnenwahrscheinlichkeit", "sunpercent"),
        ("Luftfeuchtigkeit", "humidity"),
        ("Windgeschwindigkeit", "windspeed"),
        ("Uhr", "clock"),
        ("Datum", "date"),
        ("Wetterwarnung", "alert"),
    )

    def __init__(self, session):

        Screen.__init__(
            self,
            session
        )

        self.session = session

        self["key_red"] = Label(
            _("Cancel")
        )

        self["key_green"] = Label(
            _("Save")
        )

        self["key_yellow"] = Label(
            _("Default colors")
        )

        self["key_blue"] = Label(
            _("Save & exit")
        )

        self.list = []

        for label, name in self._ENTRIES:

            self.list.append(
                getConfigListEntry(
                    _(label) + ":",
                    getattr(
                        config.plugins.speedy_TheWeather,
                        "sevenday_color_" + name
                    )
                )
            )

        ConfigListScreen.__init__(
            self,
            self.list,
            session=session
        )

        self["actions"] = ActionMap(
            [
                "SetupActions",
                "ColorActions"
            ],
            {
                "green": self.save,
                "blue": self.save,
                "red": self.keyCancel,
                "cancel": self.keyCancel,
                "save": self.save,
                "yellow": self.resetDefaults,
            },
            -2
        )

    def resetDefaults(self):

        for _label, name in self._ENTRIES:

            try:

                getattr(
                    config.plugins.speedy_TheWeather,
                    "sevenday_color_" + name
                ).setValue(
                    _SEVENDAY_COLOR_DEFAULTS[name]
                )

            except Exception as e:

                print(
                    "[speedy_TheWeather] "
                    "Could not reset SevenDay color %s: %s"
                    % (name, e)
                )

        try:

            self["config"].setList(
                self.list
            )

        except Exception:

            pass

    def save(self):

        for x in self["config"].list:

            try:

                x[1].save()

            except Exception:

                pass

        configfile.save()

        self.close(
            True
        )

    def keyCancel(self):

        for x in self["config"].list:

            try:

                x[1].cancel()

            except Exception:

                pass

        self.close()


class twolocationsColorSetup(ConfigListScreen, Screen):
    """
    Getrenntes Farbmenü für den Two-Locations-Screen.

    Standort 1 und Standort 2 besitzen jeweils eine eigene Palette.
    """

    skin = """
    <screen name="twolocationsColorSetup"
        position="center,center"
        size="1100,700"
        title="Two Locations Farben">

        <widget name="config"
            position="4,4"
            size="1070,600"
            scrollbarMode="showOnDemand"
            itemHeight="45"
            itemTextSelectedColor="#ffffff"
            itemTextUnselectedColor="#ffffff"
            font="Regular;30" />

        <ePixmap pixmap="skin_default/buttons/red.png" position="11,650" size="20,40" alphatest="on" zPosition="1" />
        <widget name="key_red" position="36,650" size="240,40" zPosition="2" transparent="1" font="Regular;25" halign="center" valign="center" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="282,650" size="20,40" alphatest="on" zPosition="1" />
        <widget name="key_green" position="308,650" size="240,40" zPosition="2" transparent="1" font="Regular;25" halign="center" valign="center" foregroundColor="green" />
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="554,650" size="20,40" alphatest="on" zPosition="1" />
        <widget name="key_yellow" position="579,650" size="240,40" zPosition="2" transparent="1" font="Regular;25" halign="center" valign="center" foregroundColor="yellow" />
        <ePixmap pixmap="skin_default/buttons/blue.png" position="825,650" size="20,40" alphatest="on" zPosition="1" />
        <widget name="key_blue" position="851,650" size="240,40" zPosition="2" transparent="1" font="Regular;25" halign="center" valign="center" foregroundColor="blue" />

    </screen>
    """

    _ENTRIES = (
        ("Wetterbeschreibung", "weathertype"),
        ("Gefühlte Temperatur", "feels"),
        ("Wind", "wind"),
        ("Regen", "rain"),
        ("Sonne", "sun"),
        ("Mond", "moon"),
    )

    def __init__(self, session):

        Screen.__init__(self, session)
        self.session = session

        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("Save"))
        self["key_yellow"] = Label(_("Default colors"))
        self["key_blue"] = Label(_("Save & exit"))

        # Einmalige Migration der alten gemeinsamen Palette:
        # alte Werte werden auf beide Standorte übernommen, solange die
        # neuen Standortwerte noch auf ihren Standardwerten stehen.
        self._migrateLegacyColors()

        self.location1Header = ConfigNothing()
        self.location2Header = ConfigNothing()
        self.list = []

        self.list.append(getConfigListEntry(_("=== Standort 1 Farben ==="), self.location1Header))
        for label, name in self._ENTRIES:
            self.list.append(getConfigListEntry(_(label) + ":", getattr(config.plugins.speedy_TheWeather, "twoloc_loc1_color_" + name)))

        self.list.append(getConfigListEntry(_("=== Standort 2 Farben ==="), self.location2Header))
        for label, name in self._ENTRIES:
            self.list.append(getConfigListEntry(_(label) + ":", getattr(config.plugins.speedy_TheWeather, "twoloc_loc2_color_" + name)))

        ConfigListScreen.__init__(self, self.list, session=session)

        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions"],
            {
                "green": self.save,
                "blue": self.save,
                "red": self.keyCancel,
                "cancel": self.keyCancel,
                "save": self.save,
                "yellow": self.resetDefaults,
            },
            -2
        )

    def _migrateLegacyColors(self):
        """Übernimmt alte gemeinsame Two-Locations-Farben auf beide Orte."""
        try:
            legacy_changed = False
            for _label, name in self._ENTRIES:
                legacy = getattr(config.plugins.speedy_TheWeather, "twoloc_color_" + name)
                if legacy.value != _TWOLocations_LEGACY_COLOR_DEFAULTS[name]:
                    legacy_changed = True
                    break

            if not legacy_changed:
                return

            for _label, name in self._ENTRIES:
                legacy = getattr(config.plugins.speedy_TheWeather, "twoloc_color_" + name)
                for location in ("loc1", "loc2"):
                    target = getattr(config.plugins.speedy_TheWeather, "twoloc_%s_color_%s" % (location, name))
                    if target.value == _TWOLOCATIONS_COLOR_DEFAULTS[name]:
                        target.setValue(legacy.value)

            print("[speedy_TheWeather] Legacy Two Locations Farben auf beide Standorte migriert.")
        except Exception as e:
            print("[speedy_TheWeather] Two Locations Farb-Migration fehlgeschlagen: %s" % e)

    def resetDefaults(self):
        for _label, name in self._ENTRIES:
            for location in ("loc1", "loc2"):
                try:
                    getattr(
                        config.plugins.speedy_TheWeather,
                        "twoloc_%s_color_%s" % (location, name)
                    ).setValue(_TWOLOCATIONS_COLOR_DEFAULTS[name])
                except Exception as e:
                    print(
                        "[speedy_TheWeather] Could not reset Two Locations %s color %s: %s"
                        % (location, name, e)
                    )

        try:
            self["config"].setList(self.list)
        except Exception:
            pass

    def save(self):
        for x in self["config"].list:
            try:
                x[1].save()
            except Exception:
                pass
        configfile.save()
        self.close(True)

    def keyCancel(self):
        for x in self["config"].list:
            try:
                x[1].cancel()
            except Exception:
                pass
        self.close()



class CitySuggestListScreen(Screen):
    def __init__(self, session, results):
        Screen.__init__(self, session)
        AddNewScreen(self)
        self.onClose.append(lambda: RemoveScreen(self))
        self._results = results

        if sz_w > 1800:
            skin = """
                <screen name="CitySuggestListScreen" flags="wfNoBorder" position="center,center" size="1920,1080">
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png" position="0,112" size="1920,3" zPosition="1"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png" position="0,1010" size="1920,3" zPosition="1"/>
                <widget source="session.VideoPicture" render="Pig" position="30,160" size="720,405" backgroundColor="#ff000000" zPosition="1"/>
                <widget source="session.CurrentService" render="Label" position="30,125" size="720,36" zPosition="1" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" font="Regular;28" noWrap="1" valign="center" halign="center"><convert type="ServiceName">Name</convert></widget>
                <widget source="global.CurrentTime" render="Label" position="1634,35" size="225,45" transparent="1" zPosition="3" font="Regular;34" foregroundColor="#00ffff00" backgroundColor="#0000ff00" valign="center" halign="right"><convert type="ClockToText">Format:%-H:%M:%S</convert></widget>
                <widget source="global.CurrentTime" render="Label" position="1409,74" size="450,37" transparent="1" zPosition="3" font="Regular;24" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%a %d/%m/%y</convert></widget>
                <widget name="list" position="840,225" size="975,630" scrollbarMode="showOnDemand" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/list/list97563.png"/>\n
                <widget name="title" position="840,135" size="1000,70" valign="center" halign="left" zPosition="1" font="Regular;44" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red34.png" position="192,1022" size="34,34" alphatest="blend"/>
                <widget name="key_red" position="242,1015" size="370,48" zPosition="1" font="Regular;40" halign="left" foregroundColor="#00ff0000" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                </screen>"""
        else:
            skin = """
                <screen name="CitySuggestListScreen" flags="wfNoBorder" position="center,center" size="1280,720">
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline2.png" position="0,88" size="1280,2" zPosition="1"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline2.png" position="0,630" size="1280,2" zPosition="1"/>
                <widget source="session.VideoPicture" render="Pig" position="85,120" size="417,243" backgroundColor="#ff000000" zPosition="1"/>
                <widget source="session.CurrentService" render="Label" position="85,93" size="417,32" zPosition="1" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" font="Regular;28" noWrap="1" valign="center" halign="center"><convert type="ServiceName">Name</convert></widget>
                <widget source="global.CurrentTime" render="Label" position="1091,12" size="150,55" transparent="1" zPosition="1" font="Regular;24" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%-H:%M:%S</convert></widget>
                <widget source="global.CurrentTime" render="Label" position="941,32" size="300,55" transparent="1" zPosition="1" font="Regular;16" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%a %d/%m/%y</convert></widget>
                <widget name="list" position="560,156" size="650,420" scrollbarMode="showOnDemand" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/list/list65043.png"/>\n
                <widget name="title" position="557,90" size="620,47" valign="center" halign="left" zPosition="1" font="Regular;36" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red26.png" position="145,663" size="26,26" alphatest="blend"/>
                <widget name="key_red" position="185,663" size="220,32" zPosition="1" font="Regular;24" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                </screen>"""
        self.skin = skin.replace("Format:%a %d/%m/%y", getDateFormat())

        self["title"] = Label(_("Choose a match:"))
        self["key_red"] = Label(_("Exit"))

        self.res = []
        base_counts = {}
        for r in results:
            base = "%s (%s)" % (r.get("name", ""), r.get("countrycode", ""))
            base_counts[base] = base_counts.get(base, 0) + 1

        seen_counts = {}
        for r in results:
            base = "%s (%s)" % (r.get("name", ""), r.get("countrycode", ""))
            loc = r.get("location", {}) or {}
            coords = " [%.2f, %.2f]" % (loc.get("lat", 0.0), loc.get("lon", 0.0))
            if base_counts[base] > 1:
                foad = r.get("foad", {}) or {}
                region = foad.get("name")
                if region:
                    label = "%s - %s%s" % (base, region, coords)
                else:
                    seen_counts[base] = seen_counts.get(base, 0) + 1
                    label = "%s (%d)%s" % (base, seen_counts[base], coords)
            else:
                label = base
            if not PY3 and isinstance(label, unicode):
                label = label.encode("utf-8")
            if sz_w > 1800:
                self.res.append([r, MultiContentEntryText(pos=(0, 0), size=(960, 63), font=0, flags=RT_HALIGN_LEFT, text=label, color_sel=0x00D2D226)])
            else:
                self.res.append([r, MultiContentEntryText(pos=(0, 0), size=(590, 42), font=0, flags=RT_HALIGN_LEFT, text=label, color_sel=0x00D2D226)])

        self["list"] = MenuList(self.res, True, eListboxPythonMultiContent)
        if sz_w > 1800:
            self["list"].l.setItemHeight(63)
            self["list"].l.setFont(0, gFont("Regular", 50))
        else:
            self["list"].l.setItemHeight(42)
            self["list"].l.setFont(0, gFont("Regular", 33))
        self["list"].show()

        self["actions"] = ActionMap(["WizardActions", "MenuActions", "ShortcutActions"], {"ok": self.selecteer, "back": self.annuleer, "red": self.annuleer}, -1)

    def selecteer(self):
        idx = self["list"].getSelectedIndex()
        if 0 <= idx < len(self._results):
            self.close(self._results[idx])
        else:
            self.close(None)

    def annuleer(self):
        self.close(None)

class infoscreen(Screen):
    def __init__(self, session):
        global _overlayScreen, _overlayEnabled

        # Dynamisches Datumsformat ermitteln
        try:
            if config.plugins.speedy_TheWeather.dateformat.value == "dot":
                date_fmt = "Format:%a %d.%m.%y"
            else:
                date_fmt = "Format:%a %d/%m/%y"
        except Exception:
            date_fmt = "Format:%a %d/%m/%y"

        if sz_w > 1800:
            skin = """
                    <screen name="startScreen" title="Infoscreen" flags="wfNoBorder" position="center,center" size="1920,1080">
                    <widget name="infos" position="85,45" size="1085,55" valign="center" halign="left" zPosition="1" font="Regular;36" foregroundColor="#000000ff" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png" position="0,112" size="1920,3" zPosition="1"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png" position="0,1010" size="1920,3" zPosition="1"/>
                    <widget source="global.CurrentTime" render="Label" position="1577,18" size="225,45" transparent="1" zPosition="3" font="Regular;36" foregroundColor="#00ff0000" backgroundColor="#00ff0000" valign="center" halign="right"><convert type="ClockToText">Format:%-H:%M:%S</convert></widget>
                    <widget source="global.CurrentTime" render="Label" position="1352,57" size="450,37" transparent="1" zPosition="3" font="Regular;24" foregroundColor="#0000ff00" backgroundColor="#0000ff00" valign="center" halign="right"><convert type="ClockToText">""" + date_fmt + """</convert></widget>
                    <widget source="session.VideoPicture" render="Pig" position="30,160" size="720,405" backgroundColor="#ff000000" zPosition="1"/>
                    <widget source="session.CurrentService" render="Label" position="30,125" size="720,36" zPosition="1" foregroundColor="#00ff0000" backgroundColor="#00202020" transparent="1" font="Regular;28" noWrap="1" valign="center" halign="center"><convert type="ServiceName">Name</convert></widget>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red34.png" position="192,1022" size="34,34" alphatest="blend"/>
                    <widget name="key_red" position="242,1020" size="370,48" zPosition="1" font="Regular;40" halign="left" foregroundColor="#00ff0000" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/green34.png" position="628,1022" size="34,34" alphatest="blend"/>
                    <widget name="key_green" position="678,1020" size="370,48" zPosition="1" font="Regular;40" halign="left" foregroundColor="#0000ff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/yellow34.png" position="1064,1022" size="34,34" alphatest="blend"/>
                    <widget name="key_yellow" position="1114,1020" size="370,48" zPosition="1" font="Regular;40" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/blue34.png" position="1500,1022" size="34,34" alphatest="blend"/>
                    <widget name="key_blue" position="1550,1020" size="370,48" zPosition="1" font="Regular;40" halign="left" foregroundColor="#000000ff" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget name="helpinfo" position="900,186" size="800,600" valign="top" halign="left" zPosition="1" font="Regular;36" foregroundColor="#00ff0000" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget name="version" position="1290,945" size="600,42" valign="center" halign="right" zPosition="1" font="Regular;36" foregroundColor="#00ff0000" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    </screen>"""
        else:
            skin = """
                    <screen name="startScreen" flags="wfNoBorder" position="center,center" size="1280,720">
                    <widget name="infos" position="57,30" size="723,37" valign="center" halign="left" zPosition="1" font="Regular;24" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline2.png" position="0,88" size="1280,2" zPosition="1"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline2.png" position="0,630" size="1280,2" zPosition="1"/>
                    <widget source="global.CurrentTime" render="Label" position="1021,10" size="150,55" transparent="1" zPosition="1" font="Regular;24" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%-H:%M:%S</convert></widget>
                    <widget source="global.CurrentTime" render="Label" position="871,30" size="300,55" transparent="1" zPosition="1" font="Regular;16" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">""" + date_fmt + """</convert></widget>
                    <widget source="session.VideoPicture" render="Pig" position="85,120" size="417,243" backgroundColor="#ff000000" zPosition="1"/>
                    <widget source="session.CurrentService" render="Label" position="85,93" size="417,32" zPosition="1" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" font="Regular;28" noWrap="1" valign="center" halign="center"><convert type="ServiceName">Name</convert></widget>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red26.png" position="145,663" size="26,26" alphatest="blend"/>
                    <widget name="key_red" position="185,663" size="220,32" zPosition="1" font="Regular;24" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/green26.png" position="420,663" size="26,26" alphatest="blend"/>
                    <widget name="key_green" position="460,663" size="220,32" zPosition="1" font="Regular;24" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/yellow26.png" position="695,663" size="26,26" alphatest="blend"/>
                    <widget name="key_yellow" position="735,663" size="220,32" zPosition="1" font="Regular;24" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/blue26.png" position="970,663" size="26,26" alphatest="blend"/>
                    <widget name="key_blue" position="1010,663" size="220,32" zPosition="1" font="Regular;24" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget name="helpinfo" position="700,106" size="400,320" valign="top" halign="left" zPosition="1" font="Regular;20" foregroundColor="#00ff0000" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    <widget name="version" position="860,590" size="400,28" valign="center" halign="right" zPosition="1" font="Regular;20" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                    </screen>"""

        self.session = session
        Screen.__init__(self, session)
        self.setTitle(_("Infoscreen"))
        self.skin = skin.replace("Format:%a %d/%m/%y", getDateFormat())
        self["infos"] = Label(_("Infoscreen"))
        self["key_red"] = Label(_("Exit"))
        self["key_green"] = Label(_("Standard Icons"))
        self["key_yellow"] = Label(_("Extra Icons "))
        self["key_blue"] = Label(_("Background"))
        self["helpinfo"] = Label(_("Tip!\nPress the hidden Yellow button in the main menu to open the RainRadar.\n\nPress the hidden Green button in the main menu to change the hour interval.\n\nPress the hidden Blue button in the main menu to compare two cities.\n\nPress OK here to toggle the temperature overlay: %s") % (_("ON") if _overlayEnabled else _("OFF")))
        self["actions"] = ActionMap(["WizardActions"], {"back": self.close, "ok": self.toggleOverlay}, -1)
        self["ColorActions"] = HelpableActionMap(self, "ColorActions", {"red": self.exit, "green": self.default, "yellow": self.extra, "blue": self.openBackgroundPicker}, -1)
        self["version"] = Label("speedy_TheWeather_v.%s" % version)
        AddNewScreen(self)
        self.onClose.append(lambda: RemoveScreen(self))
        global _overlayInfoscreenOpen
        _overlayInfoscreenOpen = True
        _overlayCheckVisibility()
        self.onClose.append(self._onCloseOverlay)

    def close(self, *args):
        self._closed = True

        # PicLoad Cleanup
        if hasattr(self, 'picload') and self.picload is not None:
            try:
                self.picload.PictureData.get().remove(self.bgPictureLoaded)
            except Exception:
                pass
            self.picload = None

        # Timers stoppen
        try:
            self.refreshTimer.stop()
        except Exception:
            pass
        try:
            self.animTimer.stop()
        except Exception:
            pass
        try:
            self.loadDelayTimer.stop()
        except Exception:
            pass
        try:
            if hasattr(self, '_radarPollTimer') and self._radarPollTimer:
                self._radarPollTimer.stop()
        except Exception:
            pass

        Screen.close(self, *args)

    def _onCloseOverlay(self):
        global _overlayInfoscreenOpen
        _overlayInfoscreenOpen = False
        _overlayCheckVisibility()

    def exit(self):
        self.close()

    def toggleOverlay(self):
        global _overlayEnabled
        _overlayEnabled = not _overlayEnabled
        try:
            with open(OVERLAY_CFG, "w") as f:
                f.write("1" if _overlayEnabled else "0")
        except Exception as e:
            print("[speedy_TheWeather] toggleOverlay: opslaan mislukt:", e)
        _overlayCheckVisibility()
        self["helpinfo"].setText(_("Tip!\nPress the hidden Yellow button in the main menu to open the RainRadar.\n\nPress the hidden Green button in the main menu to change the hour interval.\n\nPress the hidden Blue button in the main menu to compare two cities.\n\nPress OK here to toggle the temperature overlay: %s") % (_("ON") if _overlayEnabled else _("OFF")))

    def default(self):
        self["helpinfo"].setText(_("Loading standard icons, please wait..."))
        with open(CFG_DIR + "/iconpack.cfg", "w") as f:
            f.write("Images")
        self.switchIconpackAndRestart("Images")

    def extra(self):
        self["helpinfo"].setText(_("Loading extra icons, please wait..."))
        with open(CFG_DIR + "/iconpack.cfg", "w") as f:
            f.write("Images_extra")
        self.switchIconpackAndRestart("Images_extra")

    def openBackgroundPicker(self):
        self.session.openWithCallback(self.backgroundPickerCallback, BackgroundPickerScreen)

    def backgroundPickerCallback(self, changed=None):
        pass

    def switchIconpackAndRestart(self, nieuwPad):
        global icoonpath, _restartTimer, _restartTimerConn, _restartInProgress
        if _restartInProgress:
            return
        _restartInProgress = True
        icoonpath = nieuwPad
        self.session.open(MessageBox, _("Icon pack changed.\nThe plugin will restart..."), MessageBox.TYPE_INFO, timeout=3)
        _restartTimer = eTimer()
        _restartTimerConn = safeTimerCallback(_restartTimer, self._finishIconpackRestart)
        _restartTimer.start(1500, True)

    def _finishIconpackRestart(self, ret=None):
        global _restartTimer, _restartTimerConn
        sess = self.session
        self.close()
        ClosePlugin()
        _restartTimer = eTimer()
        _restartTimerConn = safeTimerCallback(_restartTimer, lambda: _doIconpackRestart(sess))
        _restartTimer.start(50, True)

class CityPickerScreen(Screen):
    """2e location"""

    def __init__(self, session, steden):
        Screen.__init__(self, session)
        AddNewScreen(self)
        self.onClose.append(lambda: RemoveScreen(self))

        if sz_w > 1800:
            skin = """
                <screen name="CityPickerScreen" flags="wfNoBorder" position="center,center" size="1920,1080">
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png" position="0,112" size="1920,3" zPosition="1"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png" position="0,1010" size="1920,3" zPosition="1"/>
                <widget source="global.CurrentTime" render="Label" position="1634,35" size="225,45" transparent="1" zPosition="3" font="Regular;36" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%-H:%M:%S</convert></widget>
                <widget source="global.CurrentTime" render="Label" position="1409,74" size="450,37" transparent="1" zPosition="3" font="Regular;24" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%a %d/%m/%y</convert></widget>
                <widget source="session.VideoPicture" render="Pig" position="30,160" size="720,405" backgroundColor="#ff000000" zPosition="1"/>
                <widget source="session.CurrentService" render="Label" position="30,125" size="720,36" zPosition="1" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" font="Regular;28" noWrap="1" valign="center" halign="center"><convert type="ServiceName">Name</convert></widget>
                <widget name="list" position="840,160" size="975,630" scrollbarMode="showOnDemand" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/list/list97563.png"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red34.png" position="192,1022" size="34,34" alphatest="blend"/>
                <widget name="key_red" position="242,1015" size="370,48" zPosition="1" font="Regular;40" halign="left" transparent="1" foregroundColor="#00ff0000" backgroundColor="#00202020" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="2elocation" position="840,50" size="900,55" valign="center" halign="left" zPosition="1" font="Regular;44" foregroundColor="#000000ff" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                </screen>"""
        else:
            skin = """
                <screen name="CityPickerScreen" flags="wfNoBorder" position="center,center" size="1280,720">
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline2.png" position="0,88" size="1280,2" zPosition="1"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline2.png" position="0,630" size="1280,2" zPosition="1"/>
                <widget source="global.CurrentTime" render="Label" position="1091,12" size="150,55" transparent="1" zPosition="1" font="Regular;24" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="left"><convert type="ClockToText">Format:%-H:%M:%S</convert></widget>
                <widget source="global.CurrentTime" render="Label" position="941,32" size="300,55" transparent="1" zPosition="1" font="Regular;16" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="left"><convert type="ClockToText">Format:%a %d/%m/%y</convert></widget>
                <widget source="session.VideoPicture" render="Pig" position="85,120" size="417,243" backgroundColor="#ff000000" zPosition="1"/>
                <widget source="session.CurrentService" render="Label" position="85,93" size="417,32" zPosition="1" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" font="Regular;28" noWrap="1" valign="center" halign="center"><convert type="ServiceName">Name</convert></widget>
                <widget name="list" position="630,100" size="650,462" scrollbarMode="showOnDemand" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/list/list65043.png"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red26.png" position="145,663" size="26,26" alphatest="blend"/>
                <widget name="key_red" position="185,663" size="220,32" zPosition="1" font="Regular;24" foregroundColor="#00ffff00" backgroundColor="#00202020" halign="left" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="2elocation" position="630,30" size="620,50" valign="center" halign="left" zPosition="1" font="Regular;36" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                </screen>"""

        self.skin = skin.replace("Format:%a %d/%m/%y", getDateFormat())
        self._steden = steden
        self.res = []

        for stad in steden:
            cleanmadecity = stripCoords(stad).rsplit("-", 1)[0]
            if sz_w > 1800:
                self.res.append([stad, MultiContentEntryText(pos=(0, 0), size=(860, 63), font=0, flags=RT_HALIGN_LEFT, text=cleanmadecity, color_sel=0x00D2D226)])
            else:
                self.res.append([stad, MultiContentEntryText(pos=(0, 0), size=(580, 42), font=0, flags=RT_HALIGN_LEFT, text=cleanmadecity, color_sel=0x00D2D226)])

        self["list"] = MenuList(self.res, True, eListboxPythonMultiContent)
        if sz_w > 1800:
            self["list"].l.setItemHeight(63)
            self["list"].l.setFont(0, gFont("Regular", 50))
        else:
            self["list"].l.setItemHeight(42)
            self["list"].l.setFont(0, gFont("Regular", 33))
        self["list"].show()
        self["2elocation"] = Label(_("Choose 2nd location:"))
        self["key_red"] = Label("Exit")
        self["actions"] = ActionMap(["WizardActions", "MenuActions"], {
            "ok": self.selecteer,
            "back": self.annuleer,
            "cancel": self.annuleer,
        }, -1)
        self["ColorActions"] = HelpableActionMap(self, "ColorActions", {
            "red": self.annuleer,
        }, -1)

    def selecteer(self):
        idx = self["list"].getSelectedIndex()
        if 0 <= idx < len(self._steden):
            self.close(self._steden[idx])
        else:
            self.close(None)

    def annuleer(self):
        self.close(None)

class twolocations(Screen):

    COMPARE_CFG = CFG_DIR + "/speedy_TheWeather_compare.cfg"

    def __init__(self, session):

        Screen.__init__(
            self,
            session
        )

        AddNewScreen(self)

        self.onClose.append(
            lambda: RemoveScreen(self)
        )

        self.compareCity = ""

        if os.path.exists(
            self.COMPARE_CFG
        ):

            try:

                with open(
                    self.COMPARE_CFG
                ) as f:

                    val = f.read().strip()

                    if val:
                        self.compareCity = val

            except Exception:
                pass

        # =========================================================
        # HD
        # =========================================================

        if sz_w > 1800:

            skin = """
                <screen name="twolocations"
                    flags="wfNoBorder"
                    position="center,center"
                    size="1920,1080">

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png"
                    position="0,112"
                    size="1920,3"
                    zPosition="1"/>

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png"
                    position="0,1010"
                    size="1920,3"
                    zPosition="1"/>

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png"
                    position="958,112"
                    size="3,868"
                    zPosition="1"/>

                <widget source="global.CurrentTime"
                    render="Label"
                    position="1634,35"
                    size="225,45"
                    transparent="1"
                    zPosition="3"
                    font="Regular;36"
                    foregroundColor="#00ff0000"
                    backgroundColor="#00ff0000"
                    valign="center"
                    halign="right">
                    <convert type="ClockToText">Format:%-H:%M:%S</convert>
                </widget>

                <widget source="global.CurrentTime"
                    render="Label"
                    position="1409,74"
                    size="450,37"
                    transparent="1"
                    zPosition="3"
                    font="Regular;24"
                    foregroundColor="#00ffff00"
                    backgroundColor="#0000ff00"
                    valign="center"
                    halign="right">
                    <convert type="ClockToText">Format:%a %d/%m/%y</convert>
                </widget>

                <!-- ===================== ORT 1 ===================== -->

                <widget name="loc1name"
                    position="40,125"
                    size="880,72"
                    zPosition="3"
                    font="Regular;58"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    halign="center"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1icon"
                    position="140,215"
                    size="160,160"
                    zPosition="3"
                    alphatest="blend"/>

                <widget name="loc1maxtemp"
                    position="320,215"
                    size="380,95"
                    zPosition="3"
                    font="Regular;78"
                    foregroundColor="#00ff0000"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1mintemp"
                    position="320,310"
                    size="600,60"
                    zPosition="3"
                    font="Regular;48"
                    foregroundColor="#000000ff"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1weertype"
                    position="320,400"
                    size="600,56"
                    zPosition="3"
                    font="Regular;44"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1feel"
                    position="320,468"
                    size="600,52"
                    zPosition="3"
                    font="Regular;40"
                    foregroundColor="#0080c0ff"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1wind"
                    position="320,530"
                    size="600,52"
                    zPosition="3"
                    font="Regular;40"
                    foregroundColor="#00ffa500"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1rain"
                    position="320,592"
                    size="600,52"
                    zPosition="3"
                    font="Regular;40"
                    foregroundColor="#004080ff"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1sun"
                    position="320,654"
                    size="600,52"
                    zPosition="3"
                    font="Regular;40"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1moon"
                    position="320,706"
                    size="600,52"
                    zPosition="3"
                    noWrap="1"
                    font="Regular;40"
                    foregroundColor="#00c080ff"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1alert"
                    position="320,772"
                    size="808,68"
                    zPosition="3"
                    font="Regular;48"
                    foregroundColor="#00ffffff"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1alerticon"
                    position="216,776"
                    size="64,64"
                    zPosition="4"
                    alphatest="blend"
                    transparent="1"/>


                <!-- ===================== ORT 2 ===================== -->

                <widget name="loc2name"
                    position="1000,125"
                    size="880,72"
                    zPosition="3"
                    font="Regular;58"
                    foregroundColor="#000000ff"
                    backgroundColor="#00202020"
                    halign="center"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2icon"
                    position="1100,215"
                    size="160,160"
                    zPosition="3"
                    alphatest="blend"/>

                <widget name="loc2maxtemp"
                    position="1280,215"
                    size="380,95"
                    zPosition="3"
                    font="Regular;78"
                    foregroundColor="#0000ff00"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2mintemp"
                    position="1280,310"
                    size="600,60"
                    zPosition="3"
                    font="Regular;48"
                    foregroundColor="#0000ff00"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2weertype"
                    position="1280,400"
                    size="600,56"
                    zPosition="3"
                    font="Regular;44"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2feel"
                    position="1280,468"
                    size="600,52"
                    zPosition="3"
                    font="Regular;40"
                    foregroundColor="#0080c0ff"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2wind"
                    position="1280,530"
                    size="600,52"
                    zPosition="3"
                    font="Regular;40"
                    foregroundColor="#00ffa500"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2rain"
                    position="1280,592"
                    size="600,52"
                    zPosition="3"
                    font="Regular;40"
                    foregroundColor="#004080ff"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2sun"
                    position="1280,654"
                    size="600,52"
                    zPosition="3"
                    font="Regular;40"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2moon"
                    position="1280,706"
                    size="600,52"
                    zPosition="3"
                    noWrap="1"
                    font="Regular;40"
                    foregroundColor="#00c080ff"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2alert"
                    position="1280,772"
                    size="808,68"
                    zPosition="3"
                    font="Regular;48"
                    foregroundColor="#00ffffff"
                    backgroundColor="#00202020"
                    halign="left"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2alerticon"
                    position="1176,776"
                    size="64,64"
                    zPosition="4"
                    alphatest="blend"
                    transparent="1"/>


                <widget name="statusmsg"
                    position="40,850"
                    size="1840,56"
                    zPosition="3"
                    font="Regular;40"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    halign="center"
                    valign="center"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red34.png"
                    position="192,1022"
                    size="34,34"
                    alphatest="blend"/>

                <widget name="key_red"
                    position="242,1015"
                    size="370,48"
                    zPosition="3"
                    font="Regular;40"
                    foregroundColor="#00ff0000"
                    backgroundColor="#00202020"
                    halign="left"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/yellow34.png"
                    position="628,1022"
                    size="34,34"
                    alphatest="blend"/>

                <widget name="comp"
                    position="85,45"
                    size="1085,55"
                    valign="center"
                    halign="left"
                    zPosition="1"
                    font="Regular;36"
                    foregroundColor="#000000ff"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="key_yellow"
                    position="678,1015"
                    size="600,48"
                    zPosition="3"
                    font="Regular;40"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    halign="left"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                </screen>"""

        # =========================================================
        # SD 1280x720
        # =========================================================

        else:

            skin = """
                <screen name="twolocations"
                    flags="wfNoBorder"
                    position="center,center"
                    size="1280,720">

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline2.png"
                    position="0,88"
                    size="1280,2"
                    zPosition="1"/>

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline2.png"
                    position="0,630"
                    size="1280,2"
                    zPosition="1"/>

                <widget source="global.CurrentTime"
                    render="Label"
                    position="1090,18"
                    size="170,40"
                    transparent="1"
                    zPosition="3"
                    font="Regular;30"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    valign="center"
                    halign="right">
                    <convert type="ClockToText">Format:%-H:%M:%S</convert>
                </widget>

                <widget source="global.CurrentTime"
                    render="Label"
                    position="940,52"
                    size="320,34"
                    transparent="1"
                    zPosition="3"
                    font="Regular;20"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    valign="center"
                    halign="right">
                    <convert type="ClockToText">Format:%a %d/%m/%y</convert>
                </widget>

                <!-- ===================== ORT 1 ===================== -->

                <widget name="loc1name"
                    position="244,95"
                    size="618,52"
                    zPosition="3"
                    font="Regular;42"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1icon"
                    position="94,143"
                    size="130,130"
                    scale="1"
                    zPosition="3"
                    alphatest="blend"/>

                <widget name="loc1maxtemp"
                    position="244,158"
                    size="470,80"
                    zPosition="3"
                    font="Regular;72"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1mintemp"
                    position="244,238"
                    size="470,44"
                    zPosition="3"
                    font="Regular;36"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1weertype"
                    position="244,296"
                    size="474,44"
                    zPosition="3"
                    font="Regular;34"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1feel"
                    position="244,348"
                    size="474,40"
                    zPosition="3"
                    font="Regular;32"
                    halign="left"
                    valign="center"
                    foregroundColor="#0080c0ff"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1wind"
                    position="244,394"
                    size="474,40"
                    zPosition="3"
                    font="Regular;32"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ffa500"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1rain"
                    position="244,440"
                    size="474,40"
                    zPosition="3"
                    font="Regular;32"
                    halign="left"
                    valign="center"
                    foregroundColor="#004080ff"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1sun"
                    position="244,486"
                    size="474,40"
                    zPosition="3"
                    font="Regular;32"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1moon"
                    position="244,526"
                    size="474,40"
                    zPosition="3"
                    noWrap="1"
                    font="Regular;32"
                    halign="left"
                    valign="center"
                    foregroundColor="#00c080ff"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1alert"
                    position="244,570"
                    size="576,40"
                    zPosition="3"
                    font="Regular;32"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ffffff"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc1alerticon"
                    position="183,570"
                    size="38,38"
                    zPosition="4"
                    alphatest="blend"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"/>


                <!-- ===================== ORT 2 ===================== -->

                <widget name="loc2name"
                    position="842,95"
                    size="618,52"
                    zPosition="3"
                    font="Regular;42"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2icon"
                    position="692,143"
                    size="130,130"
                    scale="1"
                    zPosition="3"
                    alphatest="blend"/>

                <widget name="loc2maxtemp"
                    position="842,158"
                    size="470,80"
                    zPosition="3"
                    font="Regular;72"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2mintemp"
                    position="842,238"
                    size="474,44"
                    zPosition="3"
                    font="Regular;36"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2weertype"
                    position="842,296"
                    size="474,44"
                    zPosition="3"
                    font="Regular;34"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2feel"
                    position="842,348"
                    size="474,40"
                    zPosition="3"
                    font="Regular;32"
                    halign="left"
                    valign="center"
                    foregroundColor="#0080c0ff"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2wind"
                    position="842,394"
                    size="474,40"
                    zPosition="3"
                    font="Regular;32"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ffa500"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2rain"
                    position="842,440"
                    size="474,40"
                    zPosition="3"
                    font="Regular;32"
                    halign="left"
                    valign="center"
                    foregroundColor="#004080ff"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2sun"
                    position="842,486"
                    size="474,40"
                    zPosition="3"
                    font="Regular;32"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2moon"
                    position="842,526"
                    size="474,40"
                    zPosition="3"
                    noWrap="1"
                    font="Regular;32"
                    halign="left"
                    valign="center"
                    foregroundColor="#00c080ff"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2alert"
                    position="842,570"
                    size="576,40"
                    zPosition="3"
                    font="Regular;32"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ffffff"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="loc2alerticon"
                    position="781,570"
                    size="38,38"
                    zPosition="4"
                    alphatest="blend"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"/>


                <widget name="statusmsg"
                    position="10,606"
                    size="1260,24"
                    zPosition="3"
                    font="Regular;22"
                    halign="center"
                    valign="center"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>


                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red26.png"
                    position="145,663"
                    size="26,26"
                    alphatest="blend"/>

                <widget name="key_red"
                    position="185,663"
                    size="220,32"
                    zPosition="1"
                    font="Regular;24"
                    halign="left"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <widget name="comp"
                    position="57,30"
                    size="723,37"
                    valign="center"
                    halign="left"
                    zPosition="1"
                    font="Regular;24"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/yellow26.png"
                    position="695,663"
                    size="26,26"
                    alphatest="blend"/>

                <widget name="key_yellow"
                    position="735,663"
                    size="220,32"
                    zPosition="1"
                    font="Regular;24"
                    halign="left"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                </screen>"""

        self.skin = skin.replace(
            "Format:%a %d/%m/%y",
            getDateFormat()
        )

        # =========================================================
        # Labels
        # =========================================================

        for n in [
            "loc1name",
            "loc1maxtemp",
            "loc1mintemp",
            "loc1weertype",
            "loc1feel",
            "loc1wind",
            "loc1rain",
            "loc1sun",
            "loc1moon",
            "loc1alert",

            "loc2name",
            "loc2maxtemp",
            "loc2mintemp",
            "loc2weertype",
            "loc2feel",
            "loc2wind",
            "loc2rain",
            "loc2sun",
            "loc2moon",
            "loc2alert",

            "statusmsg",
            "key_red",
            "key_yellow"
        ]:

            self[n] = Label("")

        for n in [
            "loc1icon",
            "loc2icon",
            "loc1alerticon",
            "loc2alerticon"
        ]:

            self[n] = Pixmap()

        # =========================================================
        # Actions
        # =========================================================

        self["actions"] = ActionMap(
            [
                "WizardActions",
                "MenuActions"
            ],
            {
                "back": self.exit,
                "cancel": self.exit
            },
            -1
        )

        self["ColorActions"] = HelpableActionMap(
            self,
            "ColorActions",
            {
                "red": self.exit,
                "yellow": self.changeCompareCity,
                "blue": self.exit
            },
            -1
        )

        self["key_red"] = Label(
            _("Exit")
        )

        self["key_yellow"] = Label(
            _("Choose 2nd location")
        )

        self["comp"] = Label(
            _("Compare Locations")
        )

        # =========================================================
        # Farben anwenden, sobald das Layout fertig ist
        # =========================================================

        self.onLayoutFinish.append(
            self._applyWeatherColors
        )

        # =========================================================
        # Daten laden
        # =========================================================

        self.fillLoc1()

        if self.compareCity:

            self.fillLoc2(
                self.compareCity
            )

        else:

            self._setText(
                "loc2name",
                _("No 2nd location")
            )

            self._setText(
                "statusmsg",
                _("Press YELLOW to choose a 2nd location.")
            )

        # =========================================================
        # Icon Timer
        # =========================================================

        self.iconFixTimer = eTimer()

        self._iconFixTimer_conn = safeTimerCallback(
            self.iconFixTimer,
            self.reloadIcons
        )

        self.iconFixTimer.start(
            300,
            True
        )

    # =============================================================
    # Konfigurierbare Farben
    # =============================================================

    def _applyWeatherColors(self):

        print(
            "[speedy_TheWeather] "
            "Two Locations Farben anwenden"
        )

        self._setWeatherColors(
            "loc1"
        )

        self._setWeatherColors(
            "loc2"
        )

    # =============================================================
    # Farbwert in Enigma2-gRGB umwandeln
    # =============================================================

    def _parseColor(self, value):
        """
        Wandelt die gespeicherten Config-Farbwerte in gRGB um.

        ConfigSelection verwendet hier Werte im Skin-Format
        #AARRGGBB. gRGB erwartet dagegen den eigentlichen RGB-Wert
        ohne den Alpha-Kanal.
        """

        if value is None:
            return gRGB(0xffffff)

        value = str(value).strip()

        if not value:
            return gRGB(0xffffff)

        # Bekannte Enigma2-/Skin-Farbnamen
        named = {
            "black": 0x000000,
            "white": 0xffffff,
            "red": 0xff0000,
            "green": 0x00ff00,
            "blue": 0x0000ff,
            "yellow": 0xffff00,
            "cyan": 0x00ffff,
            "magenta": 0xff00ff,
            "orange": 0xffa500,
            "gray": 0x808080,
            "grey": 0x808080,
        }

        lower = value.lower()
        if lower in named:
            return gRGB(named[lower])

        # #AARRGGBB / #RRGGBB
        if lower.startswith("#"):
            value = lower[1:]

        # 0xAARRGGBB / 0xRRGGBB
        elif lower.startswith("0x"):
            value = lower[2:]

        try:
            number = int(value, 16)
        except (TypeError, ValueError):
            raise ValueError("Ungültiger Farbwert: %r" % value)

        if len(value) <= 6:
            rgb = number & 0xffffff
        elif len(value) == 8:
            # Enigma2-Skin: AA RR GG BB
            rgb = number & 0xffffff
        else:
            raise ValueError("Ungültige Farblänge: %r" % value)

        return gRGB(rgb)

    # =============================================================
    # Farben setzen
    # =============================================================

    def _setWeatherColors(self, prefix):

        # prefix entspricht dem Widget-Präfix (loc1 / loc2).
        # Dadurch bekommt jeder Standort ausschließlich seine eigene Palette.
        location = "loc1" if prefix == "loc1" else "loc2"

        colors = {
            "weertype":
                getattr(config.plugins.speedy_TheWeather, "twoloc_%s_color_weathertype" % location),

            "feel":
                getattr(config.plugins.speedy_TheWeather, "twoloc_%s_color_feels" % location),

            "wind":
                getattr(config.plugins.speedy_TheWeather, "twoloc_%s_color_wind" % location),

            "rain":
                getattr(config.plugins.speedy_TheWeather, "twoloc_%s_color_rain" % location),

            "sun":
                getattr(config.plugins.speedy_TheWeather, "twoloc_%s_color_sun" % location),

            "moon":
                getattr(config.plugins.speedy_TheWeather, "twoloc_%s_color_moon" % location)
        }

        for name, colorConfig in colors.items():

            widgetName = (
                prefix +
                name
            )

            try:

                widget = self[
                    widgetName
                ]

                if widget.instance is None:

                    print(
                        "[speedy_TheWeather] "
                        "Widget noch nicht bereit: %s"
                        % widgetName
                    )

                    continue

                colorValue = colorConfig.value

                print(
                    "[speedy_TheWeather] "
                    "Setze %s auf %s"
                    % (
                        widgetName,
                        colorValue
                    )
                )

                color = self._parseColor(
                    colorValue
                )

                widget.instance.setForegroundColor(
                    color
                )

            except Exception as e:

                print(
                    "[speedy_TheWeather] "
                    "Farbe %s Fehler: %s"
                    % (
                        widgetName,
                        e
                    )
                )

    # =============================================================
    # Hilfsfunktion Text
    # =============================================================

    def _setText(self, key, value):

        try:

            self[key].setText(
                "" if value is None else str(value)
            )

        except Exception as e:

            print(
                "twolocations _setText fout op",
                key,
                ":",
                e
            )

    # =============================================================
    # Zeit aus verschiedenen API-Formaten lesen
    # =============================================================

    def _getTimeValue(self, value):

        if value is None:
            return ""

        try:

            value = str(
                value
            ).strip()

        except Exception:

            return ""

        if not value:
            return ""

        if "T" in value:

            try:

                value = value.split(
                    "T",
                    1
                )[1]

            except Exception:

                return ""

        elif " " in value and len(value) > 5:

            try:

                possible = value.split(
                    " "
                )[-1]

                if ":" in possible:
                    value = possible

            except Exception:
                pass

        if len(value) >= 5 and ":" in value:

            return value[:5]

        return value

    # =============================================================
    # Mondwert aus Tagesdaten holen
    # =============================================================

    def _getMoonTime(self, dag, names):

        for name in names:

            try:

                value = dag.get(
                    name
                )

                if value not in (
                    None,
                    "",
                    "None",
                    "--"
                ):

                    result = self._getTimeValue(
                        value
                    )

                    if result:
                        return result

            except Exception:
                pass

        return ""

    # =============================================================
    # Standort füllen
    # =============================================================

    def _fillLocation(
        self,
        data,
        naam,
        prefix
    ):

        try:

            dag = data[
                "days"
            ][0]

        except Exception:

            self._setText(
                prefix + "name",
                _("Data error")
            )

            return

        self._setText(
            prefix + "name",
            naam
        )

        # =========================================================
        # Aktuelle Stunde
        # =========================================================

        hours = dag.get(
            "hours",
            []
        )

        current_hour = None

        try:

            now = datetime.datetime.now()

            best_diff = None

            for hour in hours:

                htime = hour.get(
                    "time",
                    hour.get(
                        "datetime",
                        ""
                    )
                )

                if not htime:
                    continue

                try:

                    hstr = str(
                        htime
                    ).replace(
                        "Z",
                        ""
                    )

                    if "T" in hstr:

                        hstr = hstr.split(
                            "T"
                        )[1]

                    hstr = hstr[:5]

                    hh, mm = hstr.split(
                        ":"
                    )

                    hour_minutes = (
                        int(hh) * 60 +
                        int(mm)
                    )

                    now_minutes = (
                        now.hour * 60 +
                        now.minute
                    )

                    diff = abs(
                        hour_minutes -
                        now_minutes
                    )

                    if (
                        best_diff is None or
                        diff < best_diff
                    ):

                        best_diff = diff
                        current_hour = hour

                except Exception:

                    continue

        except Exception as e:

            print(
                "twolocations: aktuelle Stunde "
                "konnte nicht ermittelt werden:",
                e
            )

        if (
            current_hour is None and
            hours
        ):

            current_hour = hours[0]

        # =========================================================
        # Temperatur
        # =========================================================

        try:

            if (
                current_hour and
                "temperature" in current_hour
            ):

                curtemp = "%.1f\xb0C" % float(
                    current_hour[
                        "temperature"
                    ]
                )

            else:

                curtemp = "%.0f\xb0C" % float(
                    dag[
                        "maxtemperature"
                    ]
                )

        except Exception:

            curtemp = "--"

        self._setText(
            prefix + "maxtemp",
            curtemp
        )

        # =========================================================
        # Tages-Min/Max
        # =========================================================

        try:

            mintemp = "%.0f\xb0 / %.0f\xb0" % (
                float(
                    dag[
                        "mintemperature"
                    ]
                ),
                float(
                    dag[
                        "maxtemperature"
                    ]
                )
            )

        except Exception:

            mintemp = "--"

        self._setText(
            prefix + "mintemp",
            mintemp
        )

        # =========================================================
        # Wetterbeschreibung
        # =========================================================

        try:

            iconcode = ""

            if current_hour:

                iconcode = current_hour.get(
                    "iconcode",
                    ""
                )

            if not iconcode:

                iconcode = dag.get(
                    "iconcode",
                    ""
                )

            self._setText(
                prefix + "weertype",
                icontotext(
                    iconcode
                )
            )

        except Exception as e:

            print(
                "twolocations: "
                "Wetterbeschreibung Fehler:",
                e
            )

            self._setText(
                prefix + "weertype",
                ""
            )

        # =========================================================
        # Gefühlt
        # =========================================================

        try:

            if (
                current_hour and
                "feeltemperature" in current_hour
            ):

                feeltemp = current_hour[
                    "feeltemperature"
                ]

            else:

                feeltemp = dag.get(
                    "feeltemperature",
                    dag.get(
                        "maxtemperature",
                        "--"
                    )
                )

            self._setText(
                prefix + "feel",
                _("Feels Like: ") +
                "%.1f\xb0C" % float(
                    feeltemp
                )
            )

        except Exception:

            self._setText(
                prefix + "feel",
                ""
            )

        # =========================================================
        # Wind
        # =========================================================

        try:

            if (
                current_hour and
                "windspeed" in current_hour
            ):

                ws = current_hour[
                    "windspeed"
                ]

            else:

                ws = dag.get(
                    "windspeed",
                    0
                )

            self._setText(
                prefix + "wind",
                _("Wind: ") +
                windspeed_with_beaufort(
                    ws
                )
            )

        except Exception:

            self._setText(
                prefix + "wind",
                ""
            )

        # =========================================================
        # Regen
        # =========================================================

        try:

            if (
                current_hour and
                "precipitationmm" in current_hour
            ):

                rainmm = current_hour[
                    "precipitationmm"
                ]

            else:

                rainmm = dag.get(
                    "precipitationmm",
                    0
                )

            self._setText(
                prefix + "rain",
                _("Rain: ") +
                "%.1f mm" % float(
                    rainmm
                )
            )

        except Exception:

            self._setText(
                prefix + "rain",
                ""
            )

        # =========================================================
        # Sonne
        # =========================================================

        try:

            sunrise = self._getTimeValue(
                dag.get(
                    "sunrise",
                    ""
                )
            )

            sunset = self._getTimeValue(
                dag.get(
                    "sunset",
                    ""
                )
            )

            self._setText(
                prefix + "sun",
                _("Sun :") + " " +
                sunrise +
                "  -  " +
                sunset
            )

        except Exception as e:

            print(
                "twolocations: "
                "Sonne Fehler:",
                repr(e)
            )

            self._setText(
                prefix + "sun",
                ""
            )

        # =========================================================
        # MOND
        #
        # WICHTIG:
        # Dieser Block steht bewusst AUSSERHALB
        # des Sonne-except!
        # =========================================================

        try:

            location_entry = (
                lockaaleStad
                if prefix == "loc1"
                else self.compareCity
            )

            print(
                "twolocations: %s "
                "Mond Standort = %s"
                % (
                    prefix,
                    str(location_entry)
                )
            )

            moonrise = "na"
            moonset = "na"

            # =====================================================
            # Koordinaten holen
            # =====================================================

            lat, lon = getCoordsFromEntry(
                location_entry
            )

            print(
                "twolocations: %s "
                "Mond Koordinaten = %s / %s"
                % (
                    prefix,
                    str(lat),
                    str(lon)
                )
            )

            if lat is not None and lon is not None:

                lat = float(lat)
                lon = float(lon)

                today = (
                    datetime.datetime
                    .now()
                    .date()
                )

                print(
                    "twolocations: %s "
                    "Mond Berechnung fuer %s "
                    "lat=%.4f lon=%.4f"
                    % (
                        prefix,
                        today.isoformat(),
                        lat,
                        lon
                    )
                )

                # =================================================
                # Heute
                # =================================================

                moonrise, moonset = (
                    _moon_rise_set_for_date(
                        today,
                        lat,
                        lon
                    )
                )

                print(
                    "twolocations: %s "
                    "Mond heute: rise=%s set=%s"
                    % (
                        prefix,
                        str(moonrise),
                        str(moonset)
                    )
                )

                # =================================================
                # Kein Mondaufgang heute
                # -> Vortag pruefen
                # =================================================

                if (
                    not moonrise
                    or
                    moonrise == "na"
                ):

                    previous_day = (
                        today
                        - datetime.timedelta(
                            days=1
                        )
                    )

                    previous_rise, previous_set = (
                        _moon_rise_set_for_date(
                            previous_day,
                            lat,
                            lon
                        )
                    )

                    print(
                        "twolocations: %s "
                        "Mond Vortag: rise=%s set=%s"
                        % (
                            prefix,
                            str(previous_rise),
                            str(previous_set)
                        )
                    )

                    if (
                        previous_rise
                        and
                        previous_rise != "na"
                    ):

                        moonrise = previous_rise

                        print(
                            "twolocations: %s "
                            "Mondaufgang vom Vortag "
                            "uebernommen: %s"
                            % (
                                prefix,
                                str(moonrise)
                            )
                        )

                # =================================================
                # Kein Monduntergang heute
                # -> Folgetag pruefen
                # =================================================

                if (
                    not moonset
                    or
                    moonset == "na"
                ):

                    next_day = (
                        today
                        + datetime.timedelta(
                            days=1
                        )
                    )

                    next_rise, next_set = (
                        _moon_rise_set_for_date(
                            next_day,
                            lat,
                            lon
                        )
                    )

                    print(
                        "twolocations: %s "
                        "Mond Folgetag: rise=%s set=%s"
                        % (
                            prefix,
                            str(next_rise),
                            str(next_set)
                        )
                    )

                    if (
                        next_set
                        and
                        next_set != "na"
                    ):

                        moonset = next_set

                        print(
                            "twolocations: %s "
                            "Monduntergang vom Folgetag "
                            "uebernommen: %s"
                            % (
                                prefix,
                                str(moonset)
                            )
                        )

            else:

                print(
                    "twolocations: %s "
                    "Keine Koordinaten fuer Mondberechnung"
                    % prefix
                )

            # =====================================================
            # API-Fallback
            # =====================================================

            if (
                not moonrise
                or
                moonrise == "na"
            ):

                api_moonrise = self._getMoonTime(
                    dag,
                    [
                        "moonrise",
                        "moonriseTime",
                        "moonrise_time"
                    ]
                )

                if api_moonrise:

                    moonrise = api_moonrise

                    print(
                        "twolocations: %s "
                        "API-Mondaufgang = %s"
                        % (
                            prefix,
                            moonrise
                        )
                    )

            if (
                not moonset
                or
                moonset == "na"
            ):

                api_moonset = self._getMoonTime(
                    dag,
                    [
                        "moonset",
                        "moonsetTime",
                        "moonset_time"
                    ]
                )

                if api_moonset:

                    moonset = api_moonset

                    print(
                        "twolocations: %s "
                        "API-Monduntergang = %s"
                        % (
                            prefix,
                            moonset
                        )
                    )

            # =====================================================
            # Anzeige
            # =====================================================

            if (
                not moonrise
                or
                moonrise == "na"
            ):

                moonrise = "--"

            if (
                not moonset
                or
                moonset == "na"
            ):

                moonset = "--"

            moon_text = (
                _("Moon :") +
                " " +
                str(moonrise) +
                "  -  " +
                str(moonset)
            )

            self._setText(
                prefix + "moon",
                moon_text
            )

            print(
                "twolocations: %s "
                "MOND ANZEIGE = %s"
                % (
                    prefix,
                    moon_text
                )
            )

        except Exception as e:

            print(
                "twolocations: "
                "Mondauf-/untergang Fehler:",
                repr(e)
            )

            try:

                import traceback
                traceback.print_exc()

            except Exception:

                pass

            self._setText(
                prefix + "moon",
                _("Moon :") +
                " --  -  --"
            )

        # =========================================================
        # Warnung
        # =========================================================

        try:

            alertkleur, alerttekst = localWeatherAlert(
                dag
            )

            if alerttekst:

                kleurwaarde = {
                    "yellow": gRGB(0xf2c200),
                    "orange": gRGB(0xff8c00),
                    "red": gRGB(0xe02020),
                    "blue": gRGB(0x40a0ff)
                }.get(
                    alertkleur,
                    gRGB(0xffffff)
                )

                self._setText(
                    prefix + "alert",
                    alerttekst
                )

                try:

                    if self[
                        prefix + "alert"
                    ].instance is not None:

                        self[
                            prefix + "alert"
                        ].instance.setForegroundColor(
                            kleurwaarde
                        )

                except Exception:
                    pass

                try:

                    if sz_w > 1800:

                        alerticon = (
                            "/usr/lib/enigma2/python/"
                            "Plugins/Extensions/"
                            "speedy_TheWeather/" +
                            SHARED_PACK +
                            "/alert/alert_" +
                            alertkleur +
                            ".png"
                        )

                    else:

                        alerticon = (
                            "/usr/lib/enigma2/python/"
                            "Plugins/Extensions/"
                            "speedy_TheWeather/" +
                            SHARED_PACK +
                            "/alert/alert_" +
                            alertkleur +
                            "_sd.png"
                        )

                    if self[
                        prefix + "alerticon"
                    ].instance is not None:

                        self[
                            prefix + "alerticon"
                        ].instance.setPixmapFromFile(
                            alerticon
                        )

                        self[
                            prefix + "alerticon"
                        ].show()

                except Exception:

                    self[
                        prefix + "alerticon"
                    ].hide()

            else:

                self._setText(
                    prefix + "alert",
                    ""
                )

                self[
                    prefix + "alerticon"
                ].hide()

        except Exception:

            pass

        # =========================================================
        # Wetter-Icon
        # =========================================================

        try:

            if current_hour:

                iconcode = current_hour.get(
                    "iconcode",
                    ""
                )

            else:

                iconcode = dag.get(
                    "iconcode",
                    ""
                )

            iconbestand = (
                "/usr/lib/enigma2/python/"
                "Plugins/Extensions/"
                "speedy_TheWeather/" +
                icoonpath +
                "/iconbighd/" +
                str(iconcode) +
                ".png"
            )

            if self[
                prefix + "icon"
            ].instance is not None:

                self[
                    prefix + "icon"
                ].instance.setPixmapFromFile(
                    iconbestand
                )

        except Exception as e:

            print(
                "twolocations: Icon Fehler:",
                e
            )

    # =============================================================
    # Icons / Wetter neu laden
    # =============================================================

    def reloadIcons(self):

        self.fillLoc1()

        if self.compareCity:

            self.fillLoc2(
                self.compareCity
            )

        # Farben nach dem Reload erneut anwenden
        self._applyWeatherColors()

    # =============================================================
    # Ort 1
    # =============================================================

    def fillLoc1(self):

        global weatherData
        global citynamedisplay

        try:

            self._fillLocation(
                weatherData,
                citynamedisplay,
                "loc1"
            )

        except Exception as e:

            print(
                "twolocations fillLoc1 fout:",
                e
            )

            self._setText(
                "loc1name",
                _("Error loading")
            )

    # =============================================================
    # Ort 2
    # =============================================================

    def fillLoc2(self, city):

        self._setText(
            "statusmsg",
            _("Loading...")
        )

        try:

            data, naam = getLocWeerFor(
                city
            )

            if data and naam:

                self._fillLocation(
                    data,
                    naam,
                    "loc2"
                )

                self._setText(
                    "statusmsg",
                    ""
                )

                # Farbe nach dem Laden von Ort 2 erneut setzen
                self._setWeatherColors(
                    "loc2"
                )

            else:

                self._setText(
                    "loc2name",
                    _("Not found")
                )

                self._setText(
                    "statusmsg",
                    _(
                        "City not found. "
                        "Press YELLOW to change."
                    )
                )

        except Exception as e:

            print(
                "twolocations fillLoc2 fout:",
                e
            )

            self._setText(
                "loc2name",
                _("Error loading")
            )

            self._setText(
                "statusmsg",
                _("Error fetching data.")
            )

    # =============================================================
    # Zweiten Ort auswählen
    # =============================================================

    def changeCompareCity(self):

        global SavedLokaleWeer

        if not SavedLokaleWeer:

            self.session.open(
                MessageBox,
                _(
                    "No saved cities found.\n"
                    "First add cities via the location screen."
                ),
                MessageBox.TYPE_INFO
            )

            return

        self.session.openWithCallback(
            self.onCompareCityChosen,
            CityPickerScreen,
            SavedLokaleWeer
        )

    # =============================================================
    # Zweiten Ort speichern
    # =============================================================

    def onCompareCityChosen(
        self,
        stadcode=None
    ):

        if not stadcode:
            return

        self.compareCity = stadcode

        try:

            with open(
                self.COMPARE_CFG,
                "w"
            ) as f:

                f.write(
                    self.compareCity
                )

        except Exception as e:

            print(
                "twolocations: "
                "opslaan 2e stad mislukt:",
                e
            )

        self.fillLoc2(
            self.compareCity
        )

        # Farbe nach Auswahl erneut anwenden
        self._setWeatherColors(
            "loc2"
        )

    # =============================================================
    # Beenden
    # =============================================================

    def exit(self):

        self.close()

class BackgroundPickerScreen(Screen):
    BG_CFG = CFG_DIR + "/speedy_TheWeather_bg.cfg"
    BG_DIR = "/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/backgrounds/"
    EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")

    def __init__(self, session):
        Screen.__init__(self, session)
        AddNewScreen(self)
        self.onClose.append(lambda: RemoveScreen(self))

        if sz_w > 1800:
            skin = """
                <screen name="BackgroundPickerScreen" flags="wfNoBorder" position="center,center" size="1920,1080">
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png" position="0,112" size="1920,3" zPosition="1"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png" position="0,1010" size="1920,3" zPosition="1"/>
                <widget source="global.CurrentTime" render="Label" position="1634,35" size="225,45" transparent="1" zPosition="3" font="Regular;36" foregroundColor="#00ff0000" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%-H:%M:%S</convert></widget>
                <widget source="global.CurrentTime" render="Label" position="1409,74" size="450,37" transparent="1" zPosition="3" font="Regular;24" foregroundColor="#0000ff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%a %d/%m/%y</convert></widget>
                <widget name="preview" foregroundColor="#000000ff" backgroundColor="#00202020" transparent="1" position="30,160" size="720,405" zPosition="1" alphatest="blend"/>
                <widget name="list" position="840,160" size="975,756" scrollbarMode="showOnDemand" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/list/list97563.png"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red34.png" position="192,1022" size="34,34" alphatest="blend"/>
                <widget name="key_red" position="242,1015" size="370,48" zPosition="1" font="Regular;40" halign="left" foregroundColor="#00ff0000" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/green34.png" position="628,1022" size="34,34" alphatest="blend"/>
                <widget name="key_green" position="678,1015" size="600,48" zPosition="1" font="Regular;40" halign="left" foregroundColor="#0000ff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/yellow34.png" position="1200,1022" size="34,34" alphatest="blend"/>
                <widget name="key_yellow" position="1250,1015" size="600,48" zPosition="1" font="Regular;40" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="backgr" position="85,45" size="1085,55" valign="center" halign="left" zPosition="1" font="Regular;36" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                </screen>"""
        else:
            skin = """
                <screen name="BackgroundPickerScreen" flags="wfNoBorder" position="center,center" size="1280,720">
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline2.png" position="0,88" size="1280,2" zPosition="1"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline2.png" position="0,630" size="1280,2" zPosition="1"/>
                <widget source="global.CurrentTime" render="Label" position="1091,12" size="150,55" transparent="1" zPosition="1" font="Regular;24" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%-H:%M:%S</convert></widget>
                <widget source="global.CurrentTime" render="Label" position="941,32" size="300,55" transparent="1" zPosition="1" font="Regular;16" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%a %d/%m/%y</convert></widget>
                <widget name="preview" position="20,110" size="417,243" zPosition="1" alphatest="blend"/>
                <widget name="list" position="630,100" size="650,530" scrollbarMode="showOnDemand" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/list/list65043.png"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red26.png" position="145,663" size="26,26" alphatest="blend"/>
                <widget name="key_red" position="185,663" size="220,32" zPosition="1" font="Regular;24" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/green26.png" position="420,663" size="26,26" alphatest="blend"/>
                <widget name="key_green" position="460,663" size="220,32" zPosition="1" font="Regular;24" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/yellow26.png" position="700,663" size="26,26" alphatest="blend"/>
                <widget name="key_yellow" position="735,663" size="280,32" zPosition="1" font="Regular;24" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="backgr" position="57,30" size="723,37" valign="center" halign="left" zPosition="1" font="Regular;24" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                </screen>"""

        self.skin = skin.replace("Format:%a %d/%m/%y", getDateFormat())

        self._bestanden = []
        if os.path.isdir(self.BG_DIR):
            for f in sorted(os.listdir(self.BG_DIR)):
                if f.lower().endswith(self.EXTENSIONS):
                    self._bestanden.append(os.path.join(self.BG_DIR, f))

        self._bestanden.insert(0, "")

        self.res = []
        for pad in self._bestanden:
            naam = _("Standard") if pad == "" else os.path.basename(pad)
            if sz_w > 1800:
                self.res.append([pad, MultiContentEntryText(pos=(0, 0), size=(860, 63), font=0, flags=RT_HALIGN_LEFT, text=naam, color_sel=0x00D2D226)])
            else:
                self.res.append([pad, MultiContentEntryText(pos=(0, 0), size=(580, 42), font=0, flags=RT_HALIGN_LEFT, text=naam, color_sel=0x00D2D226)])

        self["list"] = MenuList(self.res, True, eListboxPythonMultiContent)
        if sz_w > 1800:
            self["list"].l.setItemHeight(63)
            self["list"].l.setFont(0, gFont("Regular", 50))
        else:
            self["list"].l.setItemHeight(42)
            self["list"].l.setFont(0, gFont("Regular", 33))
        self["list"].show()

        self["backgr"] = Label(_("Choose background:"))
        self["key_red"] = Label(_("Exit"))
        self["key_green"] = Label(_("Select"))
        self["key_yellow"] = Label(_("Standard"))
        self["preview"] = Pixmap()

        self["actions"] = ActionMap(["WizardActions", "MenuActions"], {
            "ok": self.selecteer,
            "back": self.annuleer,
            "cancel": self.annuleer,
            "up": self.omhoog,
            "down": self.omlaag,
        }, -1)
        self["ColorActions"] = HelpableActionMap(self, "ColorActions", {
            "red": self.annuleer,
            "green": self.selecteer,
            "yellow": self.resetStandaard,
        }, -1)

        # Preview-loader
        self.picload = ePicLoad()
        self._preview_picload_conn = safeSignalConnect(self.picload.PictureData, self.previewLoaded)

        self.previewTimer = eTimer()
        self._previewTimer_conn = safeTimerCallback(self.previewTimer, self.laadPreview)
        self.previewTimer.start(400, True)

        global backgroundpath
        if backgroundpath in self._bestanden:
            idx = self._bestanden.index(backgroundpath)
            self["list"].moveToIndex(idx)

    def omhoog(self):
        self["list"].up()
        self.previewTimer.start(300, True)

    def omlaag(self):
        self["list"].down()
        self.previewTimer.start(300, True)

    def laadPreview(self):
        idx = self["list"].getSelectedIndex()
        pad = self._bestanden[idx] if idx < len(self._bestanden) else ""
        if not pad:
            if sz_w > 1800:
                pad = "/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/" + SHARED_PACK + "/backgroundhd_2.png"
            else:
                pad = "/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/" + SHARED_PACK + "/backgroundhd_2.png"
        try:
            if sz_w > 1800:
                self.picload.setPara([720, 405, 1, 1, False, 1, "#ff000000"])
            else:
                self.picload.setPara([417, 243, 1, 1, False, 1, "#ff000000"])
            self.picload.startDecode(pad)
        except Exception as e:
            print("BackgroundPicker laadPreview fout:", e)

    def previewLoaded(self, picInfo=None):
        try:
            ptr = self.picload.getData()
            if ptr is not None:
                self["preview"].instance.setPixmap(ptr)
                self["preview"].show()
        except Exception as e:
            print("BackgroundPicker previewLoaded fout:", e)

    def _backToSevendays(self):
        for scr in list(screens):
            if scr is self:
                continue
            if isinstance(scr, sevendays):
                try:
                    scr.loadBackground()
                except Exception as e:
                    print("BackgroundPicker: kon achtergrond van sevendays niet verversen:", e)
            else:
                try:
                    scr.close()
                except Exception as e:
                    print("BackgroundPicker: kon tussenliggend scherm niet sluiten:", e)

    def selecteer(self):
        global backgroundpath
        idx = self["list"].getSelectedIndex()
        pad = self._bestanden[idx] if idx < len(self._bestanden) else ""
        backgroundpath = pad
        try:
            with open(self.BG_CFG, "w") as f:
                f.write(pad)
        except Exception as e:
            print("BackgroundPicker: opslaan mislukt:", e)
        self._backToSevendays()
        self.session.open(MessageBox, _("Loading background image, please wait..."), MessageBox.TYPE_INFO, timeout=4)
        self.close(True)

    def resetStandaard(self):
        global backgroundpath
        backgroundpath = ""
        try:
            with open(self.BG_CFG, "w") as f:
                f.write("")
        except Exception as e:
            print("BackgroundPicker: reset mislukt:", e)
        self._backToSevendays()
        self.session.open(MessageBox, _("Background reset to standard."), MessageBox.TYPE_INFO, timeout=2)
        self.close(True)

    def annuleer(self):
        self.close(False)

def AddNewScreen(screen):
    screens.append(screen)

def RemoveScreen(screen):
    try:
        screens.remove(screen)
    except ValueError:
        pass

def ClosePlugin():
    for screen in list(screens):
        try:
            screen.close()
        except Exception:
            None
    del screens[:]

def safeSignalConnect(sig, func):
    if hasattr(sig, "get"):
        try:
            sig.get().append(func)
            return None
        except Exception as e:
            print("[speedy_TheWeather] safeSignalConnect: .get().append faalde:", e)

    if hasattr(sig, "connect"):
        try:
            return sig.connect(func)
        except Exception as e:
            print("[speedy_TheWeather] safeSignalConnect: .connect faalde:", e)

    try:
        from enigma import eConnectCallback
        return eConnectCallback(sig, func)
    except Exception as e:
        print("[speedy_TheWeather] safeSignalConnect: eConnectCallback faalde:", e)

    try:
        sig.append(func)
        return None
    except Exception as e:
        print("[speedy_TheWeather] safeSignalConnect: .append faalde:", e)

    print("[speedy_TheWeather] safeSignalConnect: GEEN methode werkte. beschikbare attributen:", dir(sig))
    return None

def latlon_to_tile(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile

def fetchRadarTest(lat, lon, zoom=7, outdir="/tmp"):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
    xtile, ytile = latlon_to_tile(lat, lon, zoom)
    print("[speedy_TheWeather] tile x=%s y=%s z=%s" % (xtile, ytile, zoom))

    req = urllib2.Request("https://api.rainviewer.com/public/weather-maps.json", data=None, headers=headers)
    handler = urllib2.urlopen(req, timeout=10)
    meta = json.loads(handler.read())
    lastFrame = meta["radar"]["past"][-1]["path"]

    osmUrl = "https://tile.openstreetmap.org/%s/%s/%s.png" % (zoom, xtile, ytile)
    req = urllib2.Request(osmUrl, data=None, headers=headers)
    handler = urllib2.urlopen(req, timeout=10)
    with open(outdir + "/basemap_test.png", "wb") as f:
        f.write(handler.read())

    radarUrl = "https://tilecache.rainviewer.com%s/256/%s/%s/%s/2/1_1.png" % (lastFrame, zoom, xtile, ytile)
    req = urllib2.Request(radarUrl, data=None, headers=headers)
    handler = urllib2.urlopen(req, timeout=10)
    with open(outdir + "/radar_test.png", "wb") as f:
        f.write(handler.read())

    print("[speedy_TheWeather] basemap_test.png en radar_test.png weggeschreven naar %s" % outdir)

def safeTimerCallback(timer, func):
    if hasattr(timer, "callback"):
        try:
            timer.callback.append(func)
            return None
        except Exception as e:
            print("[speedy_TheWeather] safeTimerCallback: .callback.append faalde:", e)
    return safeSignalConnect(timer.timeout, func)


def _startup_weather_worker(session, location):
    """Load the last weather location off the Enigma2 main thread."""
    try:
        ok = getLocWeer(location, update_overlay=False)
        _startupWeatherQueue.put(("ok" if ok else "fail", session))
    except Exception as e:
        print("[speedy_TheWeather] startup weather failed: %s" % e)
        _startupWeatherQueue.put(("fail", session))


def _poll_startup_weather():
    global _startupWeatherTimer, _startupWeatherRunning
    try:
        result, session = _startupWeatherQueue.get_nowait()
    except queue.Empty:
        if _startupWeatherTimer is not None:
            try:
                _startupWeatherTimer.start(100, True)
            except Exception:
                pass
        return

    _startupWeatherRunning = False
    if result == "ok":
        _updateOverlayFromWeatherData()
        try:
            session.open(sevendays)
        except Exception:
            pass
    else:
        try:
            session.open(localcityscreen)
        except Exception:
            pass


def main(session, **kwargs):
    # Updateprüfung bleibt im Hintergrund.
    _update_start_check()

    global icoonpath, backgroundpath, _restartInProgress
    global SavedLokaleWeer, _startupWeatherTimer, _startupWeatherRunning
    _restartInProgress = False

    try:
        if not os.path.exists(CFG_DIR):
            os.makedirs(CFG_DIR)
    except OSError:
        pass

    # Konfiguration lesen: lokale Dateioperationen sind sehr kurz und blockieren
    # den UI-Thread nicht nennenswert. Der eigentliche Wetter-HTTP-Aufruf läuft
    # dagegen immer im Worker.
    SavedLokaleWeer = []
    locdirsave = CFG_DIR + "/speedy_TheWeather.cfg"
    if os.path.exists(locdirsave):
        try:
            with open(locdirsave) as f:
                SavedLokaleWeer = [line.rstrip() for line in f if line.rstrip()]
        except OSError:
            pass

    locdirsave = CFG_DIR + "/iconpack.cfg"
    if os.path.exists(locdirsave):
        try:
            with open(locdirsave) as f:
                value = f.read().strip()
                if value:
                    icoonpath = value
        except OSError:
            pass

    locdirsave = CFG_DIR + "/speedy_TheWeather_bg.cfg"
    if os.path.exists(locdirsave):
        try:
            with open(locdirsave) as f:
                value = f.read().strip()
                if value and os.path.exists(value):
                    backgroundpath = value
        except OSError:
            pass

    location = None
    locdirsave = CFG_DIR + "/speedy_TheWeather_last.cfg"
    if os.path.exists(locdirsave):
        try:
            with open(locdirsave) as f:
                for line in f:
                    value = line.rstrip()
                    if value:
                        location = value
        except OSError:
            pass

    if not location:
        session.open(localcityscreen)
        return

    if _startupWeatherRunning:
        return

    _startupWeatherRunning = True

    if _startupWeatherTimer is None:
        _startupWeatherTimer = eTimer()
        safeTimerCallback(_startupWeatherTimer, _poll_startup_weather)

    try:
        _startupWeatherTimer.start(100, True)
    except Exception:
        pass

    thread = threading.Thread(
        target=_startup_weather_worker,
        args=(session, location),
        name="speedy_TheWeather_StartupWeather"
    )
    thread.daemon = True
    thread.start()

class TempOverlay(Screen):
    def __init__(self, session):
        # Negative temperatures (e.g. -32.0°C at McMurdo Station) need
        # more horizontal space than the old 70px overlay provided.
        cur_w = getDesktop(0).size().width()
        ov_w = 125 if cur_w > 1800 else 105
        ov_h = 50 if cur_w > 1800 else 44
        print("[speedy_TheWeather] DEBUG __init__ cur_w=%s" % cur_w)
        if not cur_w:
            cur_w = sz_w or 1920
        skin = """
                <screen name="TempOverlay" position=\"""" + str(cur_w - ov_w - 15) + """,0" size=\"""" + str(ov_w) + "," + str(ov_h) + """" flags="wfNoBorder" backgroundColor="transparent">
                <widget name="overlay_temp" position="0,0" size=\"""" + str(ov_w) + "," + str(ov_h) + """" valign="center" halign="center" zPosition="1" font="Regular;34" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                </screen>"""
        Screen.__init__(self, session)
        self.skin = skin.replace("Format:%a %d/%m/%y", getDateFormat())
        self["overlay_temp"] = Label("")
        self.refreshTimer = eTimer()
        self._refreshTimerConn = safeTimerCallback(self.refreshTimer, self.refresh)
        self.refresh()
        self.visTimer = eTimer()
        self._visTimerConn = safeTimerCallback(self.visTimer, _overlayCheckVisibility)
        self.visTimer.start(3000, False)

    def refresh(self):
        global lockaaleStad
        try:
            stad = lockaaleStad
            if not stad:
                locdirsave = CFG_DIR + "/speedy_TheWeather_last.cfg"
                if os.path.exists(locdirsave):
                    for line in open(locdirsave):
                        stad = line.rstrip()
            if stad and getLocWeer(stad):
                _updateOverlayFromWeatherData()
        except Exception as e:
            print("[speedy_TheWeather] TempOverlay.refresh: fout:", e)
        try:
            self.refreshTimer.start(15 * 60 * 1000, True)
        except Exception:
            pass

# ================================================================
# RADAR SCREEN
# ================================================================

def _get_radar_performance_profile():
    """Build one small, immutable performance profile per RadarScreen."""
    try:
        mode = config.plugins.speedy_TheWeather.performance.value
    except Exception:
        mode = "auto"

    if mode == "ultra":
        return {
            "workers": _RADAR_ULTRA_WORKERS,
            "frames": _RADAR_ULTRA_FRAME_COUNT,
            "decode_delay": _RADAR_ULTRA_DECODE_DELAY_MS,
            "anim": _RADAR_ULTRA_ANIM_MS,
        }

    if mode == "low":
        return {
            "workers": _RADAR_LOW_WORKERS,
            "frames": _RADAR_LOW_FRAME_COUNT,
            "decode_delay": _RADAR_LOW_DECODE_DELAY_MS,
            "anim": _RADAR_LOW_ANIM_MS,
        }

    if mode == "normal":
        return {
            "workers": _RADAR_NORMAL_WORKERS,
            "frames": _RADAR_NORMAL_FRAME_COUNT,
            "decode_delay": _RADAR_NORMAL_DECODE_DELAY_MS,
            "anim": _RADAR_NORMAL_ANIM_MS,
        }

    # Auto deliberately errs on the side of responsiveness.
    try:
        width = int(getDesktop(0).size().width())
    except Exception:
        width = 1920

    total_kb = 999999
    try:
        with open("/proc/meminfo", "r") as memfile:
            for line in memfile:
                if line.startswith("MemTotal:"):
                    total_kb = int(line.split()[1])
                    break
    except Exception:
        pass

    if total_kb <= 160 * 1024:
        return {
            "workers": _RADAR_ULTRA_WORKERS,
            "frames": _RADAR_ULTRA_FRAME_COUNT,
            "decode_delay": _RADAR_ULTRA_DECODE_DELAY_MS,
            "anim": _RADAR_ULTRA_ANIM_MS,
        }

    if width <= 1280 or total_kb <= 256 * 1024:
        return {
            "workers": _RADAR_LOW_WORKERS,
            "frames": _RADAR_LOW_FRAME_COUNT,
            "decode_delay": _RADAR_LOW_DECODE_DELAY_MS,
            "anim": _RADAR_LOW_ANIM_MS,
        }

    return {
        "workers": _RADAR_NORMAL_WORKERS,
        "frames": _RADAR_NORMAL_FRAME_COUNT,
        "decode_delay": _RADAR_NORMAL_DECODE_DELAY_MS,
        "anim": _RADAR_NORMAL_ANIM_MS,
    }

class RadarScreen(Screen):
    GRID = 3
    CELL_HD = 250
    CELL_SD = 165
    BASE_ZOOM_OVERRIDE = None
    RADAR_ZOOM_MAX = 7
    RADAR_FRAME_COUNT = _RADAR_NORMAL_FRAME_COUNT

    def __init__(
        self,
        session,
        lat=51.05,
        lon=3.72,
        zoom=7,
        location_name=""
    ):
        Screen.__init__(self, session)
        self.skinName = ["RadarScreen"]

        # =========================================================
        # Grundzustand SOFORT initialisieren
        # =========================================================

        self.lat = lat
        self.lon = lon
        self.location_name = location_name or ""

        self.paused = False
        self.animTimerStarted = False
        self.fetchBusy = False
        self._closed = False

        self.currentFrameIndex = 0

        self.framePixmaps = []
        self.frameReady = []
        self.frameTimes = []
        self.frameIsForecast = []
        self.basePixmaps = {}

        self._radarThread = None
        self._radarResult = None
        self._radarError = None
        self._radarPollTimer = None
        self._fetchRequestId = 0

        # Receiver-aware performance profile.
        self._performance = _get_radar_performance_profile()
        self._radarFrameCount = self._performance["frames"]
        self._decodeDelayMs = self._performance["decode_delay"]
        self._animationIntervalMs = self._performance["anim"]

        # Persistenter Download-Pool: kein ThreadPool-Aufbau/Shutdown pro Batch.
        if ThreadPoolExecutor is not None:
            try:
                self._radarDownloadPool = ThreadPoolExecutor(
                    max_workers=self._performance["workers"]
                )
            except Exception:
                self._radarDownloadPool = None
        else:
            self._radarDownloadPool = None

        print(
            "[speedy_TheWeather] Radar performance: workers=%s frames=%s decode=%sms anim=%sms"
            % (
                self._performance["workers"],
                self._performance["frames"],
                self._decodeDelayMs,
                self._animationIntervalMs
            )
        )

        # =========================================================
        # Incremental decoder
        # =========================================================

        self._decodeTimer = eTimer()
        self._decodeTimerConn = safeTimerCallback(
            self._decodeTimer,
            self._decodeNextTile
        )

        # deque verhindert O(n)-Kosten durch pop(0) bei vielen Tiles.
        self._decodeQueue = deque()
        self._decodeActive = False
        self._decodeBaseFiles = {}
        self._decodeFrameFiles = []
        self._decodeRemaining = []

        # =========================================================
        # Ort bestimmen
        # =========================================================

        self.location_name = self._resolve_location_name()

        self["radarLocation"] = Label(
            self.location_name
        )

        # =========================================================
        # Datumsformat
        # =========================================================

        try:
            if config.plugins.speedy_TheWeather.dateformat.value == "dot":
                date_fmt = "Format:%a %d.%m.%y"
            else:
                date_fmt = "Format:%a %d/%m/%y"
        except Exception:
            date_fmt = "Format:%a %d/%m/%y"

        # =========================================================
        # Dynamische Radar-Kacheln
        # =========================================================

        baseWidgets = ""
        overlayWidgets = ""

        # =========================================================
        # FHD
        # =========================================================

        if sz_w > 1800:

            cell = self.CELL_HD
            x0, y0 = 959, 160

            for row in range(self.GRID):
                for col in range(self.GRID):

                    px = x0 + col * cell
                    py = y0 + row * cell

                    baseWidgets += (
                        '<widget name="radarBase_%s_%s" '
                        'position="%s,%s" '
                        'size="%s,%s" '
                        'zPosition="1" '
                        'transparent="1" '
                        'alphatest="blend" '
                        'scale="1"/>'
                        % (
                            row,
                            col,
                            px,
                            py,
                            cell,
                            cell
                        )
                    )

                    overlayWidgets += (
                        '<widget name="radarOverlay_%s_%s" '
                        'position="%s,%s" '
                        'size="%s,%s" '
                        'zPosition="2" '
                        'transparent="1" '
                        'alphatest="blend" '
                        'scale="1"/>'
                        % (
                            row,
                            col,
                            px,
                            py,
                            cell,
                            cell
                        )
                    )

            self.skin = """
                <screen name="RadarScreen"
                    position="center,center"
                    size="1920,1080"
                    flags="wfNoBorder"
                    title="RainViewer">

                """ + baseWidgets + overlayWidgets + """

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png"
                    position="0,112"
                    size="1920,3"
                    zPosition="1"/>

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png"
                    position="0,1010"
                    size="1920,3"
                    zPosition="1"/>

                <!-- =================================================
                     Uhr oben rechts
                     ================================================= -->

                <widget
                    source="global.CurrentTime"
                    render="Label"
                    position="1634,35"
                    size="225,45"
                    transparent="1"
                    zPosition="3"
                    font="Regular;36"
                    foregroundColor="#0000ff00"
                    backgroundColor="#00202020"
                    valign="center"
                    halign="right">

                    <convert type="ClockToText">
                        Format:%-H:%M:%S
                    </convert>

                </widget>

                <widget
                    source="global.CurrentTime"
                    render="Label"
                    position="1409,74"
                    size="450,37"
                    transparent="1"
                    zPosition="3"
                    font="Regular;24"
                    foregroundColor="#00ff0000"
                    backgroundColor="#00202020"
                    valign="center"
                    halign="right">

                    <convert type="ClockToText">
                        """ + date_fmt + """
                    </convert>

                </widget>

                <!-- =================================================
                     RainViewer - BLAU
                     ================================================= -->

                <widget
                    name="radarTitle"
                    position="30,40"
                    size="250,50"
                    zPosition="3"
                    foregroundColor="#000404b3"
                    backgroundColor="#00202020"
                    transparent="1"
                    font="Bold;40"
                    noWrap="1"
                    valign="center"
                    halign="left"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <!-- =================================================
                     Radar-Zeit - ROT
                     Direkt über dem Radar
                     ================================================= -->

                <widget
                    name="lastUpdate"
                    position="959,115"
                    size="400,36"
                    zPosition="3"
                    font="Bold;28"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ff0000"
                    backgroundColor="#00202020"
                    transparent="1"
                    noWrap="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <!-- =================================================
                     Ort - GRÜN
                     Direkt über dem Radar
                     ================================================= -->

                <widget
                    name="radarLocation"
                    position="1359,115"
                    size="397,36"
                    zPosition="3"
                    foregroundColor="#0000ff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    font="Bold;28"
                    noWrap="1"
                    valign="center"
                    halign="right"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <!-- =================================================
                     TV-Bild links
                     POSITION UNVERÄNDERT
                     ================================================= -->

                <widget
                    source="session.VideoPicture"
                    render="Pig"
                    position="30,160"
                    size="720,405"
                    backgroundColor="#ff000000"
                    zPosition="1"/>

                <!-- =================================================
                     Attribution
                     ================================================= -->

                <widget
                    name="attribution"
                    position="10,990"
                    size="600,25"
                    font="Regular;16"
                    transparent="1"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"/>

                <!-- =================================================
                     Buttons
                     ================================================= -->

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red34.png"
                    position="192,1022"
                    size="34,34"
                    alphatest="blend"/>

                <widget
                    name="key_red"
                    position="242,1015"
                    size="370,48"
                    zPosition="1"
                    font="Regular;40"
                    halign="left"
                    foregroundColor="#00ff0000"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/yellow34.png"
                    position="900,1022"
                    size="34,34"
                    alphatest="blend"/>

                <widget
                    name="key_yellow"
                    position="950,1015"
                    size="400,48"
                    zPosition="1"
                    font="Regular;40"
                    halign="left"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/blue34.png"
                    position="1500,1022"
                    size="34,34"
                    alphatest="blend"/>

                <widget
                    name="key_blue"
                    position="1550,1015"
                    size="370,48"
                    zPosition="1"
                    font="Regular;40"
                    halign="left"
                    foregroundColor="#000000ff"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                </screen>
            """

        # =========================================================
        # SD
        # =========================================================

        else:

            cell = self.CELL_SD
            x0, y0 = 639, 127

            for row in range(self.GRID):
                for col in range(self.GRID):

                    px = x0 + col * cell
                    py = y0 + row * cell

                    baseWidgets += (
                        '<widget name="radarBase_%s_%s" '
                        'position="%s,%s" '
                        'size="%s,%s" '
                        'zPosition="1" '
                        'transparent="1" '
                        'alphatest="blend" '
                        'scale="1"/>'
                        % (
                            row,
                            col,
                            px,
                            py,
                            cell,
                            cell
                        )
                    )

                    overlayWidgets += (
                        '<widget name="radarOverlay_%s_%s" '
                        'position="%s,%s" '
                        'size="%s,%s" '
                        'zPosition="2" '
                        'transparent="1" '
                        'alphatest="blend" '
                        'scale="1"/>'
                        % (
                            row,
                            col,
                            px,
                            py,
                            cell,
                            cell
                        )
                    )

            self.skin = """
                <screen name="RadarScreen"
                    position="center,center"
                    size="1280,720"
                    flags="wfNoBorder"
                    title="RainViewer">

                """ + baseWidgets + overlayWidgets + """

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png"
                    position="0,88"
                    size="1280,3"
                    zPosition="1"/>

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png"
                    position="0,648"
                    size="1280,3"
                    zPosition="1"/>

                <!-- =================================================
                     Uhr oben rechts
                     ================================================= -->

                <widget
                    source="global.CurrentTime"
                    render="Label"
                    position="1091,12"
                    size="150,55"
                    transparent="1"
                    zPosition="3"
                    font="Regular;26"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    valign="center"
                    halign="right">

                    <convert type="ClockToText">
                        Format:%-H:%M:%S
                    </convert>

                </widget>

                <widget
                    source="global.CurrentTime"
                    render="Label"
                    position="941,32"
                    size="300,55"
                    transparent="1"
                    zPosition="3"
                    font="Regular;20"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    valign="center"
                    halign="right">

                    <convert type="ClockToText">
                        """ + date_fmt + """
                    </convert>

                </widget>

                <!-- =================================================
                     RainViewer - BLAU
                     ================================================= -->

                <widget
                    name="radarTitle"
                    position="85,30"
                    size="180,40"
                    zPosition="3"
                    foregroundColor="#000404b3"
                    backgroundColor="#00202020"
                    transparent="1"
                    font="Bold;38"
                    noWrap="1"
                    valign="center"
                    halign="left"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <!-- =================================================
                     Radar-Zeit - ROT
                     Direkt über dem Radar
                     ================================================= -->

                <widget
                    name="lastUpdate"
                    position="639,92"
                    size="300,30"
                    zPosition="3"
                    font="Bold;21"
                    halign="left"
                    valign="center"
                    foregroundColor="#00ff0000"
                    backgroundColor="#00202020"
                    transparent="1"
                    noWrap="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <!-- =================================================
                     Ort - GRÜN
                     ================================================= -->

                <widget
                    name="radarLocation"
                    position="939,92"
                    size="195,30"
                    zPosition="3"
                    foregroundColor="#0000ff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    font="Bold;21"
                    noWrap="1"
                    valign="center"
                    halign="right"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <!-- =================================================
                     TV-Bild
                     POSITION UNVERÄNDERT
                     ================================================= -->

                <widget
                    source="session.VideoPicture"
                    render="Pig"
                    position="85,120"
                    size="417,243"
                    backgroundColor="#ff000000"
                    zPosition="1"/>

                <!-- =================================================
                     Attribution
                     ================================================= -->

                <widget
                    name="attribution"
                    position="10,620"
                    size="400,22"
                    font="Regular;14"
                    transparent="1"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"/>

                <!-- =================================================
                     Buttons
                     ================================================= -->

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red34.png"
                    position="100,665"
                    size="34,34"
                    alphatest="blend"/>

                <widget
                    name="key_red"
                    position="150,658"
                    size="250,40"
                    zPosition="1"
                    font="Regular;28"
                    halign="left"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/yellow34.png"
                    position="480,665"
                    size="34,34"
                    alphatest="blend"/>

                <widget
                    name="key_yellow"
                    position="530,658"
                    size="300,40"
                    zPosition="1"
                    font="Regular;28"
                    halign="left"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                <ePixmap
                    pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/blue34.png"
                    position="850,665"
                    size="34,34"
                    alphatest="blend"/>

                <widget
                    name="key_blue"
                    position="900,658"
                    size="300,40"
                    zPosition="1"
                    font="Regular;28"
                    halign="left"
                    foregroundColor="#00ffff00"
                    backgroundColor="#00202020"
                    transparent="1"
                    shadowColor="black"
                    shadowOffset="-2,-2"/>

                </screen>
            """

        # =========================================================
        # Pixmap Widgets
        # =========================================================

        for row in range(self.GRID):
            for col in range(self.GRID):

                self[
                    "radarBase_%s_%s" % (row, col)
                ] = Pixmap()

                self[
                    "radarOverlay_%s_%s" % (row, col)
                ] = Pixmap()

        # Direct widget references: avoid repeated Screen.__getitem__ lookups
        # during every radar frame.  Keep the Pixmaps permanently visible;
        # changing a Pixmap is substantially cheaper than hide/show cycles.
        self._baseWidgets = {}
        self._overlayWidgets = {}
        for row in range(self.GRID):
            for col in range(self.GRID):
                key = (row, col)
                self._baseWidgets[key] = self[
                    "radarBase_%s_%s" % (row, col)
                ]
                self._overlayWidgets[key] = self[
                    "radarOverlay_%s_%s" % (row, col)
                ]

        # =========================================================
        # Labels
        # =========================================================

        self["radarTitle"] = Label(
            _("RainViewer")
        )

        self["radarLocation"] = Label(
            self.location_name
        )

        self["attribution"] = Label(
            _("Weather data by RainViewer")
        )

        # WICHTIG:
        # Hier KEIN "Radar unavailable" setzen.
        self["lastUpdate"] = Label("")

        self["key_red"] = Label(
            _("Exit")
        )

        self["key_yellow"] = Label(
            _("Pause")
        )

        # =========================================================
        # Zoom
        # =========================================================

        self.ZOOM_LEVELS = [
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12
        ]

        try:

            init_zoom = int(
                config.plugins.speedy_TheWeather.defaultzoom.value
            )

        except Exception:

            try:
                init_zoom = int(zoom)
            except Exception:
                init_zoom = 7

        if init_zoom in self.ZOOM_LEVELS:

            self.zoomIndex = (
                self.ZOOM_LEVELS.index(
                    init_zoom
                )
            )

        else:

            self.zoomIndex = 2

        self.BASE_ZOOM_OVERRIDE = (
            self.ZOOM_LEVELS[
                self.zoomIndex
            ]
        )

        self["key_blue"] = Label(
            _("Map zoom: %s")
            % self.ZOOM_LEVELS[
                self.zoomIndex
            ]
        )

        # =========================================================
        # Actions
        # =========================================================

        self["actions"] = ActionMap(
            [
                "OkCancelActions",
                "ColorActions",
                "DirectionActions"
            ],
            {
                "cancel": self.close,
                "red": self.close,
                "yellow": self.togglePause,
                "blue": self.cycleBaseZoom,
                "up": self.zoomIn,
                "down": self.zoomOut,
                "pageUp": self.zoomIn,
                "pageDown": self.zoomOut,
            },
            -1
        )

        self.zoom = self.ZOOM_LEVELS[
            self.zoomIndex
        ]

        # =========================================================
        # Refresh Timer
        # =========================================================

        self.refreshTimer = eTimer()

        self._refreshTimerConn = safeTimerCallback(
            self.refreshTimer,
            self.startFetch
        )

        self.refreshTimer.start(
            10 * 60 * 1000,
            False
        )

        # =========================================================
        # Animation Timer
        # =========================================================

        self.animTimer = eTimer()

        self._animTimerConn = safeTimerCallback(
            self.animTimer,
            self.nextFrame
        )

        # =========================================================
        # Zoom Delay
        # =========================================================

        self.loadDelayTimer = eTimer()

        self._loadDelayTimerConn = safeTimerCallback(
            self.loadDelayTimer,
            self._doZoomFetch
        )

        # =========================================================
        # Temporary Directory
        # =========================================================

        self.tmpDir = (
            "/tmp/speedy_TheWeather"
        )

        if not os.path.exists(
            self.tmpDir
        ):

            try:
                os.makedirs(
                    self.tmpDir
                )
            except OSError:
                pass

        # =========================================================
        # Close
        # =========================================================

        self.onClose.append(
            self.cleanupAll
        )

        self.onLayoutFinish.append(
            self.startFetch
        )

    # =============================================================
    # LOCATION
    # =============================================================

    def _resolve_location_name(self):

        try:
            value = str(self.location_name).strip()
            if value:
                return value
        except Exception:
            pass

        return _("Unknown location")

    # =============================================================
    # ZOOM
    # =============================================================

    def zoomIn(self):

        if self.fetchBusy:
            return

        if self.zoomIndex < (
            len(self.ZOOM_LEVELS) - 1
        ):

            self.zoomIndex += 1
            self.applyZoomChange()

    def zoomOut(self):

        if self.fetchBusy:
            return

        if self.zoomIndex > 0:

            self.zoomIndex -= 1
            self.applyZoomChange()

    def cycleBaseZoom(self):

        if self.fetchBusy:

            self["key_blue"].setText(
                _("Please wait...")
            )

            return

        self.zoomIndex = (
            self.zoomIndex + 1
        ) % len(self.ZOOM_LEVELS)

        self.applyZoomChange()

    def applyZoomChange(self):

        if self.fetchBusy:
            return

        newZoom = self.ZOOM_LEVELS[
            self.zoomIndex
        ]

        self.zoom = newZoom
        self.BASE_ZOOM_OVERRIDE = newZoom

        self["key_blue"].setText(
            _("Loading...")
        )

        try:
            self.loadDelayTimer.stop()
        except Exception:
            pass

        self.loadDelayTimer.start(
            50,
            True
        )

    # =============================================================
    # PIXMAPS
    # =============================================================

    def _clear_pixmaps(self):

        self.basePixmaps.clear()
        self.framePixmaps = []
        self.frameReady = []
        self.frameTimes = []
        self.frameIsForecast = []

    # =============================================================
    # CLEANUP
    # =============================================================

    def cleanupFrames(self):

        if not os.path.exists(
            self.tmpDir
        ):
            return

        try:
            names = os.listdir(
                self.tmpDir
            )
        except OSError:
            return

        for name in names:

            if not (
                name.startswith(
                    "speedy_TheWeather_frame_"
                )
                or
                name.startswith(
                    "speedy_TheWeather_base_"
                )
            ):
                continue

            try:

                os.remove(
                    os.path.join(
                        self.tmpDir,
                        name
                    )
                )

            except OSError:
                pass

    def cleanupAll(self):

        # ---------------------------------------------------------
        # Screen ist geschlossen: laufende Worker ungültig machen
        # ---------------------------------------------------------

        self._closed = True

        try:
            self._fetchRequestId += 1
        except Exception:
            self._fetchRequestId = 1

        self._decodeActive = False
        self._decodeQueue = deque()

        try:
            self._decodeTimer.stop()
        except Exception:
            pass

        try:
            self.animTimer.stop()
        except Exception:
            pass

        try:
            self.refreshTimer.stop()
        except Exception:
            pass

        try:
            self.loadDelayTimer.stop()
        except Exception:
            pass

        try:
            if self._radarPollTimer is not None:
                self._radarPollTimer.stop()
        except Exception:
            pass

        if self._radarDownloadPool is not None:
            try:
                self._radarDownloadPool.shutdown(wait=False)
            except Exception:
                pass

            self._radarDownloadPool = None

        self._clear_pixmaps()
        self._baseWidgets = {}
        self._overlayWidgets = {}

        self.cleanupFrames()

    # =============================================================
    # TILE
    # =============================================================

    def _tile_xy(
        self,
        lat,
        lon,
        zoom
    ):

        x, y = latlon_to_tile(
            lat,
            lon,
            zoom
        )

        n = int(
            2 ** zoom
        )

        return (
            x % n,
            max(
                0,
                min(
                    n - 1,
                    y
                )
            )
        )

    # =============================================================
    # DOWNLOAD
    # =============================================================

    def _download_file(
        self,
        url,
        path
    ):
        """Download directly into the shared tile cache, atomically."""
        _ensure_cache_dir()
        cache_path = _cache_file_for_url(url)

        with _TILE_CACHE_LOCK:
            try:
                stat = os.stat(cache_path)
                if (
                    stat.st_size > 0
                    and time.time() - stat.st_mtime <= _TILE_CACHE_TTL
                ):
                    return cache_path
            except OSError:
                pass

        req = Request(
            url,
            data=None,
            headers={
                "User-Agent": "speedy_TheWeather/4.0",
                "Accept": "image/png,image/*,*/*"
            }
        )

        response = None
        tmp_path = cache_path + ".part.%s" % threading.current_thread().ident

        try:
            response = urlopen(req, timeout=12)
            with open(tmp_path, "wb") as f:
                while True:
                    chunk = response.read(64 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)

            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) <= 0:
                raise IOError("empty response")

            try:
                os.replace(tmp_path, cache_path)
            except AttributeError:
                os.rename(tmp_path, cache_path)

            return cache_path
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass

    # =============================================================
    # DOWNLOAD JOBS
    # =============================================================

    def _download_jobs(
        self,
        jobs,
        req_id
    ):

        results = {}

        if not jobs:
            return results

        def one(job):

            key, url, path = job

            currentRequestId = getattr(
                self,
                "_fetchRequestId",
                None
            )

            if (
                getattr(self, "_closed", True)
                or
                req_id != currentRequestId
            ):

                return key, None

            try:

                return (
                    key,
                    self._download_file(
                        url,
                        path
                    )
                )

            except Exception as e:

                return key, e

        if ThreadPoolExecutor is None:

            for job in jobs:

                key, value = one(job)

                if isinstance(
                    value,
                    Exception
                ):
                    raise value

                results[key] = value

            return results

        pool = getattr(
            self,
            "_radarDownloadPool",
            None
        )

        if pool is None:

            for job in jobs:

                key, value = one(job)

                if isinstance(
                    value,
                    Exception
                ):
                    raise value

                results[key] = value

            return results

        futures = [
            pool.submit(
                one,
                job
            )
            for job in jobs
        ]

        for future in futures:

            key, value = future.result()

            if isinstance(
                value,
                Exception
            ):
                raise value

            results[key] = value

            currentRequestId = getattr(
                self,
                "_fetchRequestId",
                None
            )

            if (
                getattr(self, "_closed", True)
                or
                req_id != currentRequestId
            ):
                return {}

        return results

    # =============================================================
    # FETCH
    # =============================================================

    def startFetch(self):

        if getattr(self, "_closed", True):
            return

        if getattr(self, "fetchBusy", False):
            return

        self.fetchBusy = True

        currentRequestId = getattr(
            self,
            "_fetchRequestId",
            0
        )

        currentRequestId += 1

        self._fetchRequestId = currentRequestId

        req_id = currentRequestId

        self._radarResult = None
        self._radarError = None

        try:
            self.animTimer.stop()
        except Exception:
            pass

        self.animTimerStarted = False

        self["key_blue"].setText(
            _("Loading...")
        )

        if self._radarPollTimer is None:

            self._radarPollTimer = eTimer()

            self._radarPollTimerConn = safeTimerCallback(
                self._radarPollTimer,
                self._pollRadarWorker
            )

        self._radarThread = threading.Thread(
            target=self._fetchTilesWorker,
            args=(req_id,)
        )

        self._radarThread.daemon = True

        self._radarThread.start()

        self._radarPollTimer.start(
            _RADAR_POLL_INTERVAL_MS,
            False
        )

    def _doZoomFetch(self):
        self.startFetch()

    def fetchTiles(self):
        return self._fetchTilesWorker(
            self._fetchRequestId
        )

    # =============================================================
    # WORKER
    # =============================================================

    def _fetchTilesWorker(
        self,
        req_id
    ):

        try:

            # -----------------------------------------------------
            # Request-ID / Screen sicher prüfen
            # -----------------------------------------------------

            currentRequestId = getattr(
                self,
                "_fetchRequestId",
                None
            )

            if currentRequestId is None:
                return

            if (
                getattr(self, "_closed", True)
                or
                req_id != currentRequestId
            ):
                return

            zoom = int(
                self.BASE_ZOOM_OVERRIDE
                if self.BASE_ZOOM_OVERRIDE is not None
                else self.zoom
            )

            radarZoom = min(
                zoom,
                self.RADAR_ZOOM_MAX
            )

            baseX, baseY = self._tile_xy(
                self.lat,
                self.lon,
                zoom
            )

            radarX, radarY = self._tile_xy(
                self.lat,
                self.lon,
                radarZoom
            )

            baseMapSize = 1 << zoom
            radarMapSize = 1 << radarZoom

            # -----------------------------------------------------
            # RainViewer Metadata
            # -----------------------------------------------------

            meta = _http_json(
                "https://api.rainviewer.com/public/weather-maps.json",
                timeout=12,
                headers={
                    "User-Agent":
                        "speedy_TheWeather/4.0"
                }
            )

            if not meta:
                raise RuntimeError(
                    "RainViewer metadata unavailable"
                )

            if (
                getattr(self, "_closed", True)
                or
                req_id != getattr(
                    self,
                    "_fetchRequestId",
                    None
                )
            ):
                return

            radar = (
                meta.get("radar")
                or {}
            )

            past = (
                radar.get("past")
                or []
            )

            if not past:
                raise RuntimeError(
                    "RainViewer returned no radar frames"
                )

            frames = past[
                -self._radarFrameCount:
            ]

            host = (
                meta.get("host")
                or
                "https://tilecache.rainviewer.com"
            )

            # -----------------------------------------------------
            # Base Map
            # -----------------------------------------------------

            jobs = []

            for row in range(self.GRID):

                for col in range(self.GRID):

                    x = (
                        baseX
                        + col
                        - 1
                    ) % baseMapSize

                    y = max(
                        0,
                        min(
                            baseMapSize - 1,
                            baseY
                            + row
                            - 1
                        )
                    )

                    url = (
                        "https://tile.openstreetmap.org/"
                        "%s/%s/%s.png"
                        % (
                            zoom,
                            x,
                            y
                        )
                    )

                    path = os.path.join(
                        self.tmpDir,
                        "speedy_TheWeather_base_%s_%s.png"
                        % (
                            row,
                            col
                        )
                    )

                    jobs.append(
                        (
                            (
                                "base",
                                row,
                                col
                            ),
                            url,
                            path
                        )
                    )

            downloaded = self._download_jobs(
                jobs,
                req_id
            )

            if (
                not downloaded
                and jobs
            ):

                raise RuntimeError(
                    "Base map download cancelled"
                )

            baseFiles = {}

            for key, path in downloaded.items():

                baseFiles[
                    (
                        key[1],
                        key[2]
                    )
                ] = path

            # -----------------------------------------------------
            # Radar Frames
            # -----------------------------------------------------

            frameFiles = []
            frameTimes = []

            for frameIndex, frame in enumerate(
                frames
            ):

                if (
                    getattr(self, "_closed", True)
                    or
                    req_id != getattr(
                        self,
                        "_fetchRequestId",
                        None
                    )
                ):
                    return

                framePath = frame.get(
                    "path"
                )

                if not framePath:
                    continue

                ts = frame.get(
                    "time"
                )

                jobs = []

                for row in range(self.GRID):

                    for col in range(self.GRID):

                        x = (
                            radarX
                            + col
                            - 1
                        ) % radarMapSize

                        y = max(
                            0,
                            min(
                                radarMapSize - 1,
                                radarY
                                + row
                                - 1
                            )
                        )

                        url = (
                            "%s%s/256/%s/%s/%s/2/1_1.png"
                            % (
                                host.rstrip("/"),
                                framePath,
                                radarZoom,
                                x,
                                y
                            )
                        )

                        path = os.path.join(
                            self.tmpDir,
                            "speedy_TheWeather_frame_%s_%s_%s.png"
                            % (
                                frameIndex,
                                row,
                                col
                            )
                        )

                        jobs.append(
                            (
                                (
                                    "frame",
                                    row,
                                    col
                                ),
                                url,
                                path
                            )
                        )

                downloaded = self._download_jobs(
                    jobs,
                    req_id
                )

                if (
                    getattr(self, "_closed", True)
                    or
                    req_id != getattr(
                        self,
                        "_fetchRequestId",
                        None
                    )
                ):
                    return

                if len(downloaded) != len(jobs):

                    raise RuntimeError(
                        "Radar tile download incomplete"
                    )

                frameFiles.append(
                    {
                        (
                            key[1],
                            key[2]
                        ): path
                        for key, path
                        in downloaded.items()
                    }
                )

                frameTimes.append(
                    ts
                )

            if not frameFiles:

                raise RuntimeError(
                    "No usable radar frames downloaded"
                )

            # -----------------------------------------------------
            # Ergebnis nochmals absichern
            # -----------------------------------------------------

            if (
                getattr(self, "_closed", True)
                or
                req_id != getattr(
                    self,
                    "_fetchRequestId",
                    None
                )
            ):
                return

            self._radarResult = {
                "reqId": req_id,
                "baseFiles": baseFiles,
                "frameFiles": frameFiles,
                "frameTimes": frameTimes,
                "radarZoom": radarZoom,
                "baseZoom": zoom,
            }

        except Exception as e:

            if (
                req_id == getattr(
                    self,
                    "_fetchRequestId",
                    None
                )
                and
                not getattr(
                    self,
                    "_closed",
                    True
                )
            ):

                self._radarError = e

    # =============================================================
    # POLL WORKER
    # =============================================================

    def _pollRadarWorker(self):

        if getattr(self, "_closed", True):
            return

        # ---------------------------------------------------------
        # Worker läuft noch
        # ---------------------------------------------------------

        if (
            self._radarResult is None
            and
            self._radarError is None
        ):

            if (
                self._radarThread is not None
                and
                self._radarThread.is_alive()
            ):

                if self._radarPollTimer is not None:
                    self._radarPollTimer.start(
                        _RADAR_POLL_INTERVAL_MS,
                        False
                    )

                return

            # Worker ist beendet, aber ohne Ergebnis.
            self.fetchBusy = False

            self["key_blue"].setText(
                _("Map zoom: %s")
                % self.ZOOM_LEVELS[
                    self.zoomIndex
                ]
            )

            print(
                "[speedy_TheWeather] "
                "Radar unavailable"
            )

            return

        # ---------------------------------------------------------
        # Poll-Timer stoppen, sobald Ergebnis/Fehler vorhanden ist.
        # ---------------------------------------------------------

        try:

            if self._radarPollTimer is not None:
                self._radarPollTimer.stop()

        except Exception:
            pass

        # ---------------------------------------------------------
        # Fehler
        # ---------------------------------------------------------

        if self._radarError is not None:

            err = self._radarError

            self._radarError = None
            self.fetchBusy = False

            self["key_blue"].setText(
                _("Map zoom: %s")
                % self.ZOOM_LEVELS[
                    self.zoomIndex
                ]
            )

            # NICHT lastUpdate verändern!
            print(
                "[speedy_TheWeather] "
                "Radar fetch error: %s"
                % err
            )

            return

        # ---------------------------------------------------------
        # Ergebnis
        # ---------------------------------------------------------

        result = self._radarResult

        self._radarResult = None

        currentRequestId = getattr(
            self,
            "_fetchRequestId",
            None
        )

        if (
            not result
            or
            currentRequestId is None
            or
            result.get("reqId") != currentRequestId
        ):

            self.fetchBusy = False
            return

        # ---------------------------------------------------------
        # Inkrementelle Dekodierung
        # ---------------------------------------------------------

        self._beginIncrementalDecode(
            result
        )

    # =============================================================
    # INCREMENTAL DECODE START
    # =============================================================

    def _beginIncrementalDecode(
        self,
        result
    ):
        if getattr(self, "_closed", True):
            return

        if not result:
            self.fetchBusy = False
            return

        try:
            self._decodeTimer.stop()
        except Exception:
            pass

        self._decodeActive = True
        self._decodeQueue = deque()

        self._decodeBaseFiles = dict(
            result.get("baseFiles", {})
        )

        self._decodeFrameFiles = list(
            result.get("frameFiles", [])
        )

        self.framePixmaps = [
            {}
            for _ in self._decodeFrameFiles
        ]

        self.frameReady = [
            False
            for _ in self._decodeFrameFiles
        ]

        self.frameTimes = list(
            result.get("frameTimes", [])
        )

        self.frameIsForecast = [
            False
            for _ in self._decodeFrameFiles
        ]

        self.currentFrameIndex = 0

        self._decodeRemaining = [
            len(files)
            for files in self._decodeFrameFiles
        ]

        # Perceived startup speed matters more than
        # finishing the base map first.
        # Decode centre base tile first, then frame 0,
        # then remaining base tiles and later frames.

        center = (
            self.GRID // 2,
            self.GRID // 2
        )

        center_path = self._decodeBaseFiles.get(center)

        if center_path:
            self._decodeQueue.append(
                ("base", center, center_path)
            )

        if self._decodeFrameFiles:

            for key, path in self._decodeFrameFiles[0].items():

                self._decodeQueue.append(
                    ("frame", 0, key, path)
                )

        for key, path in self._decodeBaseFiles.items():

            if key != center:

                self._decodeQueue.append(
                    ("base", key, path)
                )

        for frameIndex in range(
            1,
            len(self._decodeFrameFiles)
        ):

            for key, path in self._decodeFrameFiles[frameIndex].items():

                self._decodeQueue.append(
                    (
                        "frame",
                        frameIndex,
                        key,
                        path
                    )
                )

        try:
            self.animTimer.stop()
        except Exception:
            pass

        self.animTimerStarted = False

        if self._decodeQueue:

            self._decodeTimer.start(
                self._decodeDelayMs,
                True
            )

        else:

            self._finishDecode()

    # =============================================================
    # EIN TILE DEKODIEREN
    # =============================================================

    def _decodeNextTile(self):

        if (
            getattr(self, "_closed", True)
            or
            not getattr(self, "_decodeActive", False)
        ):
            return

        if not self._decodeQueue:
            self._finishDecode()
            return

        item = self._decodeQueue.popleft()

        try:

            itemType = item[0]

            if itemType == "base":

                key = item[1]
                path = item[2]

                pix = _load_cached_png(path)

                if pix is not None:

                    self.basePixmaps[key] = pix

                    widget = self._baseWidgets.get(key)

                    if widget is not None:

                        try:
                            widget.instance.setPixmap(pix)
                            widget.show()
                        except Exception:
                            pass

            else:

                frameIndex = item[1]
                key = item[2]
                path = item[3]

                pix = _load_cached_png(path)

                if (
                    frameIndex >= 0
                    and
                    frameIndex < len(self.framePixmaps)
                ):

                    if pix is not None:
                        self.framePixmaps[
                            frameIndex
                        ][key] = pix

                    if (
                        frameIndex < len(
                            self._decodeRemaining
                        )
                    ):

                        self._decodeRemaining[
                            frameIndex
                        ] -= 1

                        if (
                            self._decodeRemaining[
                                frameIndex
                            ] <= 0
                        ):
                            self._markFrameReady(
                                frameIndex
                            )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "Decode tile error: %s"
                % e
            )

        if (
            getattr(self, "_decodeActive", False)
            and
            not getattr(self, "_closed", True)
        ):

            try:

                self._decodeTimer.start(
                    self._decodeDelayMs,
                    True
                )

            except Exception:

                self._decodeNextTile()

    # =============================================================
    # FRAME READY
    # =============================================================

    def _markFrameReady(
        self,
        frameIndex
    ):

        if getattr(self, "_closed", True):
            return

        if (
            frameIndex < 0
            or
            frameIndex >= len(
                self.frameReady
            )
        ):
            return

        if self.frameReady[
            frameIndex
        ]:
            return

        self.frameReady[
            frameIndex
        ] = True

        # Ersten Frame sofort anzeigen.
        if frameIndex == 0:

            if getattr(self, "_closed", True):
                return

            self.showFrame(0)

            if (
                not getattr(self, "paused", True)
                and
                not getattr(self, "_closed", True)
            ):
                self.startAnimation()

    # =============================================================
    # DECODE FERTIG
    # =============================================================

    def _finishDecode(self):

        if getattr(self, "_closed", True):
            return

        self._decodeActive = False
        self._decodeQueue = deque()

        self._decodeBaseFiles = {}
        self._decodeFrameFiles = []
        self._decodeRemaining = []

        self.fetchBusy = False

        try:
            self["key_blue"].setText(
                _("Map zoom: %s")
                % self.ZOOM_LEVELS[
                    self.zoomIndex
                ]
            )
        except Exception:
            pass

        if (
            self.frameReady
            and
            self.frameReady[0]
            and
            not self.paused
            and
            not getattr(self, "_closed", True)
        ):
            self.startAnimation()

    # =============================================================
    # RADAR ZEIT
    # =============================================================

    def _setRadarFrameTime(
        self,
        timestamp
    ):

        try:

            timestamp = int(
                timestamp
            )

            if timestamp <= 0:
                return

            try:

                if (
                    config.plugins.speedy_TheWeather.dateformat.value
                    == "dot"
                ):

                    fmt = (
                        "%d.%m.%Y %H:%M"
                    )

                else:

                    fmt = (
                        "%d/%m/%Y %H:%M"
                    )

            except Exception:

                fmt = (
                    "%d.%m.%Y %H:%M"
                )

            radarTime = time.strftime(
                fmt,
                time.localtime(
                    timestamp
                )
            )

            self["lastUpdate"].setText(
                _("Radar: %s")
                % radarTime
            )

        except Exception:
            pass

    # =============================================================
    # FRAME ANZEIGEN
    # =============================================================

    def showFrame(
        self,
        index
    ):
        if self._closed:
            return
        if index < 0 or index >= len(self.framePixmaps):
            return
        if self.frameReady and not self.frameReady[index]:
            return

        self.currentFrameIndex = index
        cellPix = self.framePixmaps[index]

        # No hide/show pass here.  The nine overlay widgets stay visible
        # throughout the animation; only their Pixmap content changes.
        for key, widget in self._overlayWidgets.items():
            pix = cellPix.get(key)
            if pix is None:
                continue
            try:
                widget.instance.setPixmap(pix)
            except Exception:
                pass

        try:
            ts = self.frameTimes[index]
            if ts is not None:
                self._setRadarFrameTime(ts)
        except Exception:
            pass

    # =============================================================
    # ANIMATION START
    # =============================================================

    def startAnimation(self):

        if self._closed:
            return

        if self.paused:
            return

        if not self.framePixmaps:
            return

        if (
            not self.frameReady
            or
            self.currentFrameIndex
            >= len(self.frameReady)
        ):
            return

        if not self.frameReady[
            self.currentFrameIndex
        ]:

            return

        if self.animTimerStarted:
            return

        # Never animate while PNG decoding is still feeding the frame cache.
        # This avoids extra show/hide work on weak receivers.
        if self._decodeActive:
            return

        self.animTimerStarted = True

        try:

            self.animTimer.start(
                self._animationIntervalMs,
                False
            )

        except Exception:

            self.animTimerStarted = False

    # =============================================================
    # NEXT FRAME
    # =============================================================

    def nextFrame(self):

        if self._closed:
            return

        if self.paused:
            return

        if not self.framePixmaps:
            return

        if len(
            self.framePixmaps
        ) <= 1:
            return

        nextIndex = (
            self.currentFrameIndex + 1
        ) % len(
            self.framePixmaps
        )

        # Nur vollständig dekodierte Frames anzeigen.
        if (
            self.frameReady
            and
            nextIndex < len(
                self.frameReady
            )
            and
            self.frameReady[
                nextIndex
            ]
        ):

            self.showFrame(
                nextIndex
            )

    # =============================================================
    # PAUSE / PLAY
    # =============================================================

    def togglePause(self):

        if self._closed:
            return

        if self.paused:

            # -----------------------------------------------------
            # PLAY
            # -----------------------------------------------------

            self.paused = False

            self["key_yellow"].setText(
                _("Pause")
            )

            if (
                self.framePixmaps
                and
                self.frameReady
                and
                self.currentFrameIndex
                < len(
                    self.frameReady
                )
                and
                self.frameReady[
                    self.currentFrameIndex
                ]
            ):

                self.startAnimation()

        else:

            # -----------------------------------------------------
            # PAUSE
            # -----------------------------------------------------

            self.paused = True

            try:
                self.animTimer.stop()
            except Exception:
                pass

            self.animTimerStarted = False

            self["key_yellow"].setText(
                _("Play")
            )

    # =============================================================
    # CLOSE
    # =============================================================

    def close(
        self,
        *args
    ):

        if self._closed:
            return

        self._closed = True

        # Laufende Worker ungültig machen.
        self._fetchRequestId += 1

        self._decodeActive = False
        self._decodeQueue = deque()

        try:
            self.refreshTimer.stop()
        except Exception:
            pass

        try:
            self.animTimer.stop()
        except Exception:
            pass

        try:
            self.loadDelayTimer.stop()
        except Exception:
            pass

        try:
            self._decodeTimer.stop()
        except Exception:
            pass

        try:

            if self._radarPollTimer is not None:
                self._radarPollTimer.stop()

        except Exception:
            pass

        self.animTimerStarted = False

        if self._radarDownloadPool is not None:
            try:
                self._radarDownloadPool.shutdown(wait=False)
            except Exception:
                pass
            self._radarDownloadPool = None

        try:

            Screen.close(
                self,
                *args
            )

        except Exception:

            try:
                Screen.close(
                    self
                )
            except Exception:
                pass


# ====================================================================
# AUTOSTART
# ====================================================================

def autostart(
    reason,
    **kwargs
):

    global _overlayScreen
    global _overlayEnabled
    global _overlaySession

    print(
        "[speedy_TheWeather] "
        "autostart aangeroepen, "
        "reason=%s, session=%s"
        %
        (
            reason,
            kwargs.get(
                "session"
            )
        )
    )

    if reason == 0:

        session = kwargs.get(
            "session"
        )

        if session is None:

            print(
                "[speedy_TheWeather] "
                "autostart: keine session"
            )

            return

        _overlaySession = session

        try:

            _overlayEnabled = (
                _readOverlayConfig()
            )

            print(
                "[speedy_TheWeather] "
                "autostart: "
                "_overlayEnabled=%s"
                %
                _overlayEnabled
            )

            _overlayScreen = (
                session.instantiateDialog(
                    TempOverlay
                )
            )

            print(
                "[speedy_TheWeather] "
                "autostart: overlay=%s"
                %
                _overlayScreen
            )

            _overlayCheckVisibility()

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "autostart error: %s"
                % e
            )

    elif reason == 1:

        print(
            "[speedy_TheWeather] "
            "autostart: cleanup"
        )

        shutil.rmtree(
            "/tmp/speedy_TheWeather",
            ignore_errors=True
        )

# ====================================================================
# MENU
# ====================================================================

def menu(
    menuid,
    **kwargs
):

    if menuid == "mainmenu":

        return [
            (
                "speedy_TheWeather",
                main,
                "speedy_TheWeather_mainmenu",
                50
            )
        ]

    return []

# ====================================================================
# PLUGIN DESCRIPTOR
# ====================================================================

def Plugins(
    path,
    **kwargs
):

    return [

        PluginDescriptor(
            name="speedy_TheWeather",
            description="WeatherInfo",
            icon="Images/weerinfo.png",
            where=[
                PluginDescriptor.WHERE_EXTENSIONSMENU,
                PluginDescriptor.WHERE_PLUGINMENU
            ],
            fnc=main
        ),

        PluginDescriptor(
            where=PluginDescriptor.WHERE_MENU,
            fnc=menu
        ),

        PluginDescriptor(
            where=PluginDescriptor.WHERE_SESSIONSTART,
            fnc=autostart
        ),
    ]
