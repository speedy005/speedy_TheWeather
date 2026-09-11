import json
import time
import threading
from datetime import datetime
try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

from Components.Converter.Converter import Converter
from Components.Element import cached

# Cache für Wetterdaten
_CACHE = {}
_CACHE_TTL = 300
_LOCK = threading.RLock()

# Zuordnung von Buienradar/OpenData IDs zu Städtenamen
CITY_NAMES = {
    "2855146": "Ratingen",
    "2759794": "Amsterdam",
    "2750405": "Groningen",
    "2755251": "Rotterdam",
    "2745912": "Utrecht",
    "2925533": "Frankfurt",
    "2950159": "Berlin",
    "2867714": "München",
    "2911298": "Hamburg",
    "2803013": "Wien",
    "2657896": "Zürich"
}

def get_weather_data(city_id):
    now = time.time()
    with _LOCK:
        if city_id in _CACHE and (now - _CACHE[city_id][0] < _CACHE_TTL):
            return _CACHE[city_id][1]
        
    url = "https://forecast.buienradar.nl/2.0/forecast/%s" % city_id
    req = Request(url, headers={'User-Agent': 'Enigma2-TheWeather-Converter/1.0'})
    try:
        res = urlopen(req, timeout=10)
        data = json.loads(res.read().decode('utf-8'))
        with _LOCK:
            _CACHE[city_id] = (now, data)
        return data
    except Exception as e:
        print("[TheWeather Converter] Error fetching weather:", e)
        return None


class conv_TheWeather(Converter, object):
    def __init__(self, type):
        Converter.__init__(self, type)
        self.type = type.strip().split(",")
        self.day_index = 0
        self.data_type = self.type[0]

        # Tag-Index bestimmen (Day1 = 0, Day2 = 1, ...)
        if len(self.type) > 1:
            if self.type[0].startswith("Day"):
                try:
                    self.day_index = int(self.type[0].replace("Day", "")) - 1
                except ValueError:
                    self.day_index = 0
                self.data_type = self.type[1]

        # Konfigurierte Stadt-ID für Ratingen
        self.city_id = "2855146"

    def ms_to_bft(self, ms):
        if ms < 0.3: return 0
        elif ms < 1.6: return 1
        elif ms < 3.4: return 2
        elif ms < 5.5: return 3
        elif ms < 8.0: return 4
        elif ms < 10.8: return 5
        elif ms < 13.9: return 6
        elif ms < 17.2: return 7
        elif ms < 20.8: return 8
        elif ms < 24.5: return 9
        elif ms < 28.5: return 10
        elif ms < 32.7: return 11
        else: return 12

    @cached
    def getText(self):
        # 0. STADT / LOCATION (Name aus CITY_NAMES Dictionary holen)
        if self.data_type == "City":
            return CITY_NAMES.get(str(self.city_id), "Ratingen")

        data = get_weather_data(self.city_id)
        if not data or "days" not in data or len(data["days"]) <= self.day_index:
            return "N/A"

        try:
            day_data = data["days"][self.day_index]

            date_str = day_data.get("date", "").split("T")[0]
            dt = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.now()

            # --- 1. DATUM & TAG ---
            if self.data_type in ("Date", "Date_EU"):
                return dt.strftime("%d.%m.%Y")
            elif self.data_type == "Date_EU_Short":
                return dt.strftime("%d.%m.")
            elif self.data_type == "Date_US":
                return dt.strftime("%m/%d/%Y")
            elif self.data_type == "Date_US_Short":
                return dt.strftime("%m/%d/")
            elif self.data_type == "DayName":
                weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
                return weekdays[dt.weekday()]

            # --- 2. TEMPERATUREN ---
            elif self.data_type == "TemperatureMax":
                return "%s°C" % int(round(day_data.get("maxtemp", 0)))
            elif self.data_type == "TemperatureMin":
                return "%s°C" % int(round(day_data.get("mintemp", 0)))

            # --- 3. WINDGESCHWINDIGKEIT ---
            elif self.data_type == "WindSpeed_KMH":
                ms = day_data.get("wind", 0)
                return "%s km/h" % int(round(ms * 3.6))
            elif self.data_type == "WindSpeed_MS":
                return "%s m/s" % int(round(day_data.get("wind", 0)))
            elif self.data_type == "WindSpeed_BFT":
                ms = day_data.get("wind", 0)
                return "%s Bft" % self.ms_to_bft(ms)
            elif self.data_type == "WindSpeed_MPH":
                ms = day_data.get("wind", 0)
                return "%s mph" % int(round(ms * 2.23694))

            # --- 4. WINDRICHTUNG ---
            elif self.data_type == "WindDirection":
                return str(day_data.get("winddirection", "")).upper()
            elif self.data_type == "WindDirectionDegree":
                return "%s°" % str(day_data.get("winddirectiondegrees", "0"))

            # --- 5. NIEDERSCHLAG & BENEBELUNG ---
            elif self.data_type == "RainChance":
                return "%s%%" % int(round(day_data.get("rainprobability", 0)))
            elif self.data_type == "RainAmount":
                return "%s mm" % round(day_data.get("rain", 0), 1)

            # --- 6. LUFTDRUCK & LUFTFEUCHTIGKEIT ---
            elif self.data_type == "Pressure":
                return "%s hPa" % int(round(day_data.get("pressure", 0)))
            elif self.data_type == "Humidity":
                return "%s%%" % int(round(day_data.get("humidity", 0)))

            # --- 7. SONNE & UV ---
            elif self.data_type == "SunChance":
                return "%s%%" % int(round(day_data.get("sunprobability", 0)))
            elif self.data_type == "UVIndex":
                return "%s" % day_data.get("uvindex", 0)
            elif self.data_type == "Sunrise":
                sunrise = day_data.get("sunrise", "")
                return sunrise.split("T")[1][:5] if "T" in sunrise else "N/A"
            elif self.data_type == "Sunset":
                sunset = day_data.get("sunset", "")
                return sunset.split("T")[1][:5] if "T" in sunset else "N/A"

            # --- 8. ICON & WETTERTEXT ---
            elif self.data_type == "Icon":
                return str(day_data.get("iconcode", ""))
            elif self.data_type == "WeatherText":
                icons = {
                    "a": "Sonnig", "aa": "Klare Nacht", "b": "Leicht bewölkt",
                    "c": "Stark bewölkt", "d": "Bewölkt mit Sonne", "f": "Regenschauer",
                    "g": "Gewitter", "h": "Hagel", "i": "Schneeregen", "j": "Sonne mit Regen",
                    "k": "Sonne mit Schnee", "l": "Leichter Regen", "m": "Starker Regen",
                    "n": "Nebel", "o": "Bewölkt", "p": "Bedeckt", "q": "Regen",
                    "r": "Bewölkt", "s": "Schneefall", "t": "Starker Schneefall",
                    "u": "Leichter Schneefall", "v": "Schneefall", "w": "Graupel"
                }
                code = str(day_data.get("iconcode", ""))
                return icons.get(code, "Keine Info")

        except Exception as e:
            print("[TheWeather Converter] Parse Error:", e)

        return ""

    text = property(getText)