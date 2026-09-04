TheWeather

converter and renderer for skinner

for all screens infobat secinfobar etc.


<screen name="TheWeather_5Days" position="center,center" size="1800,900" title="5-Tage Wettervorhersage" backgroundColor="#101010" flags="wfNoBorder">

<!-- ==================== TAG 1 (HEUTE) ==================== -->
<!-- Kopfzeile: Wochentag & Datum -->
<widget source="session.CurrentService" render="Label" position="50,40" size="300,40" font="Regular;30" halign="center" valign="center" foregroundColor="#ffffff" transparent="1">
<convert type="conv_TheWeatherPixmap">Day1,DayName</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,85" size="300,25" font="Regular;20" halign="center" valign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeatherPixmap">Day1,Date_EU</convert>
</widget>

<!-- Wetter-Icon -->
<widget source="session.CurrentService" render="rend_TheWeatherPixmap" position="140,125" size="120,120" alphatest="blend" transparent="1">
<convert type="conv_TheWeatherPixmap">Day1,Icon</convert>
</widget>

<!-- Wettertext -->
<widget source="session.CurrentService" render="Label" position="50,255" size="300,30" font="Regular;22" halign="center" valign="center" foregroundColor="#00aaff" transparent="1">
<convert type="conv_TheWeatherPixmap">Day1,WeatherText</convert>
</widget>

<!-- Temperaturen Max / Min -->
<widget source="session.CurrentService" render="Label" position="50,300" size="300,45" font="Regular;36" halign="center" valign="center" foregroundColor="#ff5555" transparent="1">
<convert type="conv_TheWeatherPixmap">Day1,TemperatureMax</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,350" size="300,30" font="Regular;24" halign="center" valign="center" foregroundColor="#55aaff" transparent="1">
<convert type="conv_TheWeatherPixmap">Day1,TemperatureMin</convert>
</widget>

<!-- Details: Wind, Niederschlag, Druck, UV -->
<widget source="session.CurrentService" render="Label" position="50,410" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day1,WindSpeed_KMH</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,440" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeatherPixmap">Day1,WindDirection</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,480" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day1,RainChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,510" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeatherPixmap">Day1,RainAmount</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,550" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day1,SunChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,590" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day1,Humidity</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="50,630" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day1,Pressure</convert>
</widget>


<!-- ==================== TAG 2 (MORGEN) ==================== -->
<widget source="session.CurrentService" render="Label" position="390,40" size="300,40" font="Regular;30" halign="center" valign="center" foregroundColor="#ffffff" transparent="1">
<convert type="conv_TheWeatherPixmap">Day2,DayName</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,85" size="300,25" font="Regular;20" halign="center" valign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeatherPixmap">Day2,Date_EU</convert>
</widget>
<widget source="session.CurrentService" render="rend_TheWeatherPixmap" position="480,125" size="120,120" alphatest="blend" transparent="1">
<convert type="conv_TheWeatherPixmap">Day2,Icon</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,255" size="300,30" font="Regular;22" halign="center" valign="center" foregroundColor="#00aaff" transparent="1">
<convert type="conv_TheWeatherPixmap">Day2,WeatherText</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,300" size="300,45" font="Regular;36" halign="center" valign="center" foregroundColor="#ff5555" transparent="1">
<convert type="conv_TheWeatherPixmap">Day2,TemperatureMax</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,350" size="300,30" font="Regular;24" halign="center" valign="center" foregroundColor="#55aaff" transparent="1">
<convert type="conv_TheWeatherPixmap">Day2,TemperatureMin</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,410" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day2,WindSpeed_KMH</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,440" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeatherPixmap">Day2,WindDirection</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,480" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day2,RainChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,510" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeatherPixmap">Day2,RainAmount</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,550" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day2,SunChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,590" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day2,Humidity</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="390,630" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day2,Pressure</convert>
</widget>


<!-- ==================== TAG 3 ==================== -->
<widget source="session.CurrentService" render="Label" position="730,40" size="300,40" font="Regular;30" halign="center" valign="center" foregroundColor="#ffffff" transparent="1">
<convert type="conv_TheWeatherPixmap">Day3,DayName</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,85" size="300,25" font="Regular;20" halign="center" valign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeatherPixmap">Day3,Date_EU</convert>
</widget>
<widget source="session.CurrentService" render="rend_TheWeatherPixmap" position="820,125" size="120,120" alphatest="blend" transparent="1">
<convert type="conv_TheWeatherPixmap">Day3,Icon</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,255" size="300,30" font="Regular;22" halign="center" valign="center" foregroundColor="#00aaff" transparent="1">
<convert type="conv_TheWeatherPixmap">Day3,WeatherText</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,300" size="300,45" font="Regular;36" halign="center" valign="center" foregroundColor="#ff5555" transparent="1">
<convert type="conv_TheWeatherPixmap">Day3,TemperatureMax</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,350" size="300,30" font="Regular;24" halign="center" valign="center" foregroundColor="#55aaff" transparent="1">
<convert type="conv_TheWeatherPixmap">Day3,TemperatureMin</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,410" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day3,WindSpeed_KMH</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,440" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeatherPixmap">Day3,WindDirection</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,480" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day3,RainChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,510" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeatherPixmap">Day3,RainAmount</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,550" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day3,SunChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,590" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day3,Humidity</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="730,630" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day3,Pressure</convert>
</widget>


<!-- ==================== TAG 4 ==================== -->
<widget source="session.CurrentService" render="Label" position="1070,40" size="300,40" font="Regular;30" halign="center" valign="center" foregroundColor="#ffffff" transparent="1">
<convert type="conv_TheWeatherPixmap">Day4,DayName</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,85" size="300,25" font="Regular;20" halign="center" valign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeatherPixmap">Day4,Date_EU</convert>
</widget>
<widget source="session.CurrentService" render="rend_TheWeatherPixmap" position="1160,125" size="120,120" alphatest="blend" transparent="1">
<convert type="conv_TheWeatherPixmap">Day4,Icon</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,255" size="300,30" font="Regular;22" halign="center" valign="center" foregroundColor="#00aaff" transparent="1">
<convert type="conv_TheWeatherPixmap">Day4,WeatherText</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,300" size="300,45" font="Regular;36" halign="center" valign="center" foregroundColor="#ff5555" transparent="1">
<convert type="conv_TheWeatherPixmap">Day4,TemperatureMax</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,350" size="300,30" font="Regular;24" halign="center" valign="center" foregroundColor="#55aaff" transparent="1">
<convert type="conv_TheWeatherPixmap">Day4,TemperatureMin</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,410" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day4,WindSpeed_KMH</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,440" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeatherPixmap">Day4,WindDirection</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,480" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day4,RainChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,510" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeatherPixmap">Day4,RainAmount</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,550" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day4,SunChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,590" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day4,Humidity</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1070,630" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day4,Pressure</convert>
</widget>


<!-- ==================== TAG 5 ==================== -->
<widget source="session.CurrentService" render="Label" position="1410,40" size="300,40" font="Regular;30" halign="center" valign="center" foregroundColor="#ffffff" transparent="1">
<convert type="conv_TheWeatherPixmap">Day5,DayName</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,85" size="300,25" font="Regular;20" halign="center" valign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeatherPixmap">Day5,Date_EU</convert>
</widget>
<widget source="session.CurrentService" render="rend_TheWeatherPixmap" position="1500,125" size="120,120" alphatest="blend" transparent="1">
<convert type="conv_TheWeatherPixmap">Day5,Icon</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,255" size="300,30" font="Regular;22" halign="center" valign="center" foregroundColor="#00aaff" transparent="1">
<convert type="conv_TheWeatherPixmap">Day5,WeatherText</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,300" size="300,45" font="Regular;36" halign="center" valign="center" foregroundColor="#ff5555" transparent="1">
<convert type="conv_TheWeatherPixmap">Day5,TemperatureMax</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,350" size="300,30" font="Regular;24" halign="center" valign="center" foregroundColor="#55aaff" transparent="1">
<convert type="conv_TheWeatherPixmap">Day5,TemperatureMin</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,410" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day5,WindSpeed_KMH</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,440" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeatherPixmap">Day5,WindDirection</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,480" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day5,RainChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,510" size="300,25" font="Regular;18" halign="center" foregroundColor="#a0a0a0" transparent="1">
<convert type="conv_TheWeatherPixmap">Day5,RainAmount</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,550" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day5,SunChance</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,590" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day5,Humidity</convert>
</widget>
<widget source="session.CurrentService" render="Label" position="1410,630" size="300,25" font="Regular;20" halign="center" transparent="1">
<convert type="conv_TheWeatherPixmap">Day5,Pressure</convert>
</widget>

</screen>
