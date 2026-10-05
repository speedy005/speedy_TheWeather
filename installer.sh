#!/bin/bash

###############################################################################
# speedy_TheWeather installer
# Version: 2.0.1
#
# GitHub:
#   https://github.com/speedy005/speedy_TheWeather
#
# IMPORTANT:
# - This file MUST be saved as UTF-8 without BOM.
# - Multilingual changelog is NOT printed to stdout.
# - The Python updater reads the changelog directly from installer.sh.
# - The installer does NOT automatically restart Enigma2.
###############################################################################

VERSION="2.0.1"
BRANCH="master"

REPO_OWNER="speedy005"
REPO_NAME="speedy_TheWeather"

DOWNLOAD_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/heads/${BRANCH}.tar.gz"

PLUGIN_NAME="speedy_TheWeather"

###############################################################################
# Console behaviour
###############################################################################

# Number of seconds the Enigma2 Console remains visible after completion.
# Increase this if your receiver is very fast.
FINISH_DELAY=10

###############################################################################
# Paths
###############################################################################

PLUGIN_BASE_32="/usr/lib/enigma2/python/Plugins/Extensions"
PLUGIN_BASE_64="/usr/lib64/enigma2/python/Plugins/Extensions"

PLUGINPATH=""

if [ -d "$PLUGIN_BASE_32" ]; then
    PLUGINPATH="${PLUGIN_BASE_32}/${PLUGIN_NAME}"
elif [ -d "$PLUGIN_BASE_64" ]; then
    PLUGINPATH="${PLUGIN_BASE_64}/${PLUGIN_NAME}"
else
    PLUGINPATH="${PLUGIN_BASE_32}/${PLUGIN_NAME}"
fi

CONFIG_DIR="/etc/enigma2/${PLUGIN_NAME}"

TMP_DIR="/tmp/${PLUGIN_NAME}_installer"

CONFIG_BACKUP="/tmp/${PLUGIN_NAME}_config_backup"
PLUGIN_BACKUP="/tmp/${PLUGIN_NAME}_plugin_backup"
AUTO_BACKGROUNDS_BACKUP="/tmp/${PLUGIN_NAME}_auto_backgrounds_backup"

AUTO_BACKGROUNDS_DIR="${PLUGINPATH}/backgrounds/auto"

ARCHIVE_FILE="${TMP_DIR}/${PLUGIN_NAME}.tar.gz"
EXTRACT_DIR="${TMP_DIR}/extract"

###############################################################################
# Multilingual changelog
#
# IMPORTANT:
# Do NOT echo these variables.
# They are read by the Python updater.
###############################################################################

changelog_EN='
• Fixed language files and PO/MO file names.
• Added update function.
• Fixed Rain Radar, Seven Day Weather, weather icons and detached GUI restart.
• Added customizable colors.
• Added automatic weather images based on the time of day and seasonal backgrounds with automatic download and installation.
• Added sunrise and sunset display as well as moonrise and moonset display.
• Added comparison of weather data for two locations including sunrise, sunset, moonrise and moonset times.
• Added themed colors for weather description, feels like temperature, wind, rain, sun and moon information.
• Added improved city search and city selection with a dedicated selection window for matching locations.
• Improved moonrise and moonset calculations with better local time and UTC offset handling.
• Improved date and time handling throughout the plugin.
• Improved weather data handling and display reliability.
• Improved performance on low-end Enigma2 receivers with optimized radar loading, decoding, caching and animation handling.
• Added Ultra Low-End, Low-End, Auto and Normal performance modes.
• Existing features remain available.
• Buy me a coffee if you like this plugin.
'

changelog_DE='
• Sprachdateien sowie PO-/MO-Dateinamen korrigiert.
• Update-Funktion hinzugefügt.
• Rain Radar, Sieben-Tage-Wetter, Wetter-Icons und Neustart der getrennten GUI korrigiert.
• Anpassbare Farben hinzugefügt.
• Automatische Wetterbilder passend zur Tageszeit sowie saisonale Hintergründe mit automatischem Download und Installation hinzugefügt.
• Anzeige von Sonnenaufgang und Sonnenuntergang sowie Mondaufgang und Monduntergang hinzugefügt.
• Vergleich der Wetterdaten für zwei Orte mit Anzeige von Sonnenaufgang, Sonnenuntergang, Mondaufgang und Monduntergang hinzugefügt.
• Thematische Farben für Wetterbeschreibung, gefühlte Temperatur, Wind, Regen sowie Sonnen- und Mondinformationen hinzugefügt.
• Verbesserte Stadt-Suche und Stadtauswahl mit einem eigenen Auswahlfenster für passende Orte hinzugefügt.
• Mondaufgangs- und Monduntergangsberechnung mit verbesserter Behandlung von Ortszeit und UTC-Zeitverschiebung verbessert.
• Datums- und Zeitverarbeitung im gesamten Plugin verbessert.
• Verarbeitung und Anzeige der Wetterdaten zuverlässiger gemacht.
• Performance auf schwachen Enigma2-Receivern durch optimiertes Radar-Laden, Decoding, Caching und Animationen verbessert.
• Ultra Low-End-, Low-End-, Auto- und Normal-Performance-Modi hinzugefügt.
• Bestehende Funktionen bleiben erhalten.
• Wenn dir dieses Plugin gefällt, kannst du mich gerne auf einen Kaffee einladen.
'

changelog_AR='
• تم إصلاح ملفات اللغات وأسماء ملفات PO/MO.
• تمت إضافة وظيفة التحديث.
• تم إصلاح رادار المطر والطقس لمدة سبعة أيام وأيقونات الطقس وإعادة تشغيل الواجهة الرسومية المنفصلة.
• تمت إضافة ألوان قابلة للتخصيص.
• تمت إضافة صور طقس تلقائية حسب وقت اليوم وخلفيات موسمية مع التنزيل والتثبيت التلقائي.
• تمت إضافة عرض شروق وغروب الشمس وكذلك شروق وغروب القمر.
• تمت إضافة مقارنة بيانات الطقس لموقعين بما في ذلك أوقات شروق وغروب الشمس والقمر.
• تمت إضافة ألوان مخصصة لوصف الطقس ودرجة الحرارة المحسوسة والرياح والأمطار ومعلومات الشمس والقمر.
• تم تحسين البحث عن المدن واختيار المدينة من خلال نافذة مخصصة لعرض المواقع المطابقة.
• تم تحسين حسابات شروق وغروب القمر مع معالجة أفضل للتوقيت المحلي وفارق التوقيت العالمي UTC.
• تم تحسين التعامل مع التاريخ والوقت في جميع أنحاء الإضافة.
• تم تحسين معالجة بيانات الطقس وعرضها بشكل أكثر موثوقية.
• تم تحسين الأداء على أجهزة Enigma2 الضعيفة من خلال تحسين تحميل الرادار وفك الترميز والتخزين المؤقت ومعالجة الرسوم المتحركة.
• تمت إضافة أوضاع أداء Ultra Low-End وLow-End وAuto وNormal.
• تبقى الميزات الحالية متاحة.
• إذا أعجبك هذا البرنامج، يمكنك دعمي بفنجان قهوة.
'

changelog_CS='
• Opraveny jazykové soubory a názvy souborů PO/MO.
• Přidána funkce aktualizace.
• Opraven radar deště, předpověď na sedm dní, ikony počasí a restart odděleného GUI.
• Přidány přizpůsobitelné barvy.
• Přidány automatické obrázky počasí podle denní doby a sezónní pozadí s automatickým stažením a instalací.
• Přidáno zobrazení východu a západu slunce a také východu a západu Měsíce.
• Přidáno porovnání údajů o počasí pro dvě lokality včetně časů východu a západu Slunce a Měsíce.
• Přidány tematické barvy pro popis počasí, pocitovou teplotu, vítr, déšť a informace o Slunci a Měsíci.
• Vylepšeno vyhledávání měst a výběr města pomocí samostatného okna s odpovídajícími lokalitami.
• Vylepšeny výpočty východu a západu Měsíce s lepším zpracováním místního času a UTC offsetu.
• Vylepšeno zpracování data a času v celém pluginu.
• Vylepšeno zpracování a zobrazování údajů o počasí.
• Vylepšen výkon na slabších přijímačích Enigma2 optimalizací načítání radaru, dekódování, cache a animací.
• Přidány výkonnostní režimy Ultra Low-End, Low-End, Auto a Normal.
• Stávající funkce zůstávají zachovány.
• Pokud se vám plugin líbí, můžete mě pozvat na kávu.
'

changelog_EL='
• Διορθώθηκαν τα αρχεία γλώσσας και τα ονόματα των αρχείων PO/MO.
• Προστέθηκε λειτουργία ενημέρωσης.
• Διορθώθηκαν το Rain Radar, η πρόγνωση επτά ημερών, τα εικονίδια καιρού και η επανεκκίνηση του αποσυνδεδεμένου GUI.
• Προστέθηκαν προσαρμόσιμα χρώματα.
• Προστέθηκαν αυτόματες εικόνες καιρού ανάλογα με την ώρα της ημέρας και εποχιακά φόντα με αυτόματη λήψη και εγκατάσταση.
• Προστέθηκε εμφάνιση ανατολής και δύσης του ήλιου καθώς και ανατολής και δύσης της σελήνης.
• Προστέθηκε σύγκριση δεδομένων καιρού για δύο τοποθεσίες, συμπεριλαμβανομένων των ωρών ανατολής και δύσης ήλιου και σελήνης.
• Προστέθηκαν θεματικά χρώματα για την περιγραφή καιρού, την αισθητή θερμοκρασία, τον άνεμο, τη βροχή και τις πληροφορίες ήλιου και σελήνης.
• Βελτιώθηκε η αναζήτηση πόλεων και η επιλογή πόλης με ειδικό παράθυρο επιλογής για τις αντίστοιχες τοποθεσίες.
• Βελτιώθηκαν οι υπολογισμοί ανατολής και δύσης της σελήνης με καλύτερη διαχείριση της τοπικής ώρας και της διαφοράς UTC.
• Βελτιώθηκε η διαχείριση ημερομηνίας και ώρας σε ολόκληρο το plugin.
• Βελτιώθηκε η επεξεργασία και εμφάνιση των δεδομένων καιρού.
• Βελτιώθηκε η απόδοση σε αδύναμους δέκτες Enigma2 με βελτιστοποιημένη φόρτωση, αποκωδικοποίηση, cache και animation του radar.
• Προστέθηκαν λειτουργίες απόδοσης Ultra Low-End, Low-End, Auto και Normal.
• Οι υπάρχουσες λειτουργίες παραμένουν διαθέσιμες.
• Αν σας αρέσει αυτό το plugin, μπορείτε να με κεράσετε έναν καφέ.
'

changelog_FI='
• Kielitiedostot sekä PO/MO-tiedostojen nimet korjattu.
• Päivitystoiminto lisätty.
• Rain Radar, seitsemän päivän sääennuste, sääkuvakkeet ja erillisen käyttöliittymän uudelleenkäynnistys korjattu.
• Mukautettavat värit lisätty.
• Automaattiset sääkuvat vuorokaudenajan mukaan sekä vuodenaikojen taustakuvat automaattisella latauksella ja asennuksella lisätty.
• Auringonnousun ja -laskun sekä kuun nousun ja laskun näyttäminen lisätty.
• Kahden sijainnin säätietojen vertailu, mukaan lukien auringon ja kuun nousu- ja laskuajat, lisätty.
• Teemavärit sääkuvaukselle, tuntulämpötilalle, tuulelle, sateelle sekä aurinko- ja kuutiedoille lisätty.
• Kaupunkihakua ja kaupungin valintaa parannettu erillisellä valintaikkunalla vastaaville sijainneille.
• Kuun nousu- ja laskulaskelmia parannettu paremman paikallisen ajan ja UTC-poikkeaman käsittelyn avulla.
• Päivämäärän ja ajan käsittelyä parannettu koko pluginissa.
• Säätietojen käsittelyä ja näyttöä parannettu luotettavuuden lisäämiseksi.
• Suorituskykyä heikoilla Enigma2-vastaanottimilla parannettu optimoimalla tutkan latausta, dekoodausta, välimuistia ja animaatioiden käsittelyä.
• Ultra Low-End-, Low-End-, Auto- ja Normal-suorituskykytilat lisätty.
• Nykyiset ominaisuudet säilyvät.
• Jos pidät tästä pluginista, voit tarjota minulle kahvin.
'

changelog_FR='
• Correction des fichiers de langue et des noms de fichiers PO/MO.
• Ajout de la fonction de mise à jour.
• Correction du Rain Radar, de la météo sur sept jours, des icônes météo et du redémarrage du GUI séparé.
• Ajout de couleurs personnalisables.
• Ajout d’images météo automatiques selon l’heure de la journée et de fonds saisonniers avec téléchargement et installation automatiques.
• Ajout de l’affichage du lever et du coucher du soleil ainsi que du lever et du coucher de la lune.
• Ajout de la comparaison des données météo pour deux emplacements, y compris les heures de lever et de coucher du soleil et de la lune.
• Ajout de couleurs thématiques pour la description météo, la température ressentie, le vent, la pluie et les informations sur le soleil et la lune.
• Amélioration de la recherche et de la sélection des villes avec une fenêtre dédiée aux emplacements correspondants.
• Amélioration des calculs du lever et du coucher de la lune avec une meilleure gestion de l’heure locale et du décalage UTC.
• Amélioration de la gestion de la date et de l’heure dans tout le plugin.
• Amélioration de la gestion et de l’affichage des données météo.
• Amélioration des performances sur les récepteurs Enigma2 peu puissants grâce à l’optimisation du chargement, du décodage, du cache et des animations du radar.
• Ajout des modes de performance Ultra Low-End, Low-End, Auto et Normal.
• Les fonctions existantes restent disponibles.
• Si vous aimez ce plugin, vous pouvez m’offrir un café.
'

changelog_HU='
• Javítva a nyelvi fájlok és a PO/MO fájlnevek kezelése.
• Hozzáadva a frissítési funkció.
• Javítva az esőradar, a hétnapos időjárás, az időjárásikonok és a leválasztott GUI újraindítása.
• Hozzáadható színek kerültek bevezetésre.
• Automatikus időjárási képek kerültek hozzáadásra a napszak alapján, valamint szezonális hátterek automatikus letöltéssel és telepítéssel.
• Hozzáadva a napkelte és napnyugta, valamint a holdkelte és holdnyugta megjelenítése.
• Két hely időjárási adatainak összehasonlítása került hozzáadásra, beleértve a nap- és holdkelte, illetve nyugta időpontjait.
• Témázott színek kerültek hozzáadásra az időjárás leírásához, a hőérzethez, a szélhez, az esőhöz, valamint a nap- és holdinformációkhoz.
• Javult a városkeresés és a városválasztás külön kiválasztó ablakkal.
• Javultak a holdkelte- és holdnyugta-számítások a helyi idő és az UTC-eltolás jobb kezelésével.
• Javult a dátum- és időkezelés a plugin egészében.
• Megbízhatóbb lett az időjárási adatok feldolgozása és megjelenítése.
• Javult a teljesítmény gyengébb Enigma2 vevőkészülékeken a radar betöltésének, dekódolásának, gyorsítótárazásának és animációinak optimalizálásával.
• Hozzáadva az Ultra Low-End, Low-End, Auto és Normal teljesítménymód.
• A meglévő funkciók továbbra is elérhetők.
• Ha tetszik a plugin, meghívhatsz egy kávéra.
'

changelog_IT='
• Corretti i file delle lingue e i nomi dei file PO/MO.
• Aggiunta la funzione di aggiornamento.
• Corretti Rain Radar, previsioni a sette giorni, icone meteo e riavvio della GUI separata.
• Aggiunti colori personalizzabili.
• Aggiunte immagini meteo automatiche in base all’ora del giorno e sfondi stagionali con download e installazione automatici.
• Aggiunta la visualizzazione di alba e tramonto del sole e di alba e tramonto della luna.
• Aggiunto il confronto dei dati meteo per due località, inclusi gli orari di alba e tramonto del sole e della luna.
• Aggiunti colori tematici per descrizione meteo, temperatura percepita, vento, pioggia e informazioni su sole e luna.
• Migliorata la ricerca delle città e la selezione della città con una finestra dedicata alle località corrispondenti.
• Migliorati i calcoli dell’alba e del tramonto della luna con una migliore gestione dell’ora locale e dell’offset UTC.
• Migliorata la gestione di data e ora in tutto il plugin.
• Migliorata l’affidabilità nella gestione e visualizzazione dei dati meteo.
• Migliorate le prestazioni sui ricevitori Enigma2 meno potenti ottimizzando caricamento, decodifica, cache e animazioni del radar.
• Aggiunte le modalità di prestazioni Ultra Low-End, Low-End, Auto e Normal.
• Le funzioni esistenti rimangono disponibili.
• Se ti piace questo plugin, puoi offrirmi un caffè.
'

changelog_NL='
• Taalbestanden en PO/MO-bestandsnamen gecorrigeerd.
• Updatefunctie toegevoegd.
• Rain Radar, zevendaags weer, weericonen en herstart van de losgekoppelde GUI gecorrigeerd.
• Aanpasbare kleuren toegevoegd.
• Automatische weerafbeeldingen op basis van het tijdstip en seizoensachtergronden met automatische download en installatie toegevoegd.
• Weergave van zonsopkomst en zonsondergang en maansopkomst en maanondergang toegevoegd.
• Vergelijking van weergegevens voor twee locaties toegevoegd, inclusief tijden van zonsopkomst, zonsondergang, maansopkomst en maanondergang.
• Thematische kleuren toegevoegd voor weersbeschrijving, gevoelstemperatuur, wind, regen en zon- en maaninformatie.
• Verbeterde stadszoekfunctie en stadsselectie met een speciaal selectievenster voor overeenkomende locaties.
• Berekeningen van maansopkomst en maanondergang verbeterd met betere verwerking van lokale tijd en UTC-offset.
• Datum- en tijdverwerking in de hele plugin verbeterd.
• Verwerking en weergave van weergegevens betrouwbaarder gemaakt.
• Prestaties op zwakke Enigma2-ontvangers verbeterd door geoptimaliseerd laden, decoderen, cachen en animeren van radar.
• Ultra Low-End-, Low-End-, Auto- en Normal-prestatiemodi toegevoegd.
• Bestaande functies blijven beschikbaar.
• Als je deze plugin leuk vindt, kun je me op een koffie trakteren.
'

changelog_PL='
• Naprawiono pliki językowe oraz nazwy plików PO/MO.
• Dodano funkcję aktualizacji.
• Naprawiono Rain Radar, pogodę na siedem dni, ikony pogody oraz restart odłączonego GUI.
• Dodano konfigurowalne kolory.
• Dodano automatyczne obrazy pogodowe zależne od pory dnia oraz sezonowe tła z automatycznym pobieraniem i instalacją.
• Dodano wyświetlanie wschodu i zachodu słońca oraz wschodu i zachodu księżyca.
• Dodano porównanie danych pogodowych dla dwóch lokalizacji, w tym czasów wschodu i zachodu słońca oraz księżyca.
• Dodano kolorystykę tematyczną dla opisu pogody, temperatury odczuwalnej, wiatru, deszczu oraz informacji o słońcu i księżycu.
• Ulepszono wyszukiwanie miast i wybór miasta dzięki osobnemu oknu wyboru pasujących lokalizacji.
• Ulepszono obliczenia wschodu i zachodu księżyca dzięki lepszej obsłudze czasu lokalnego i przesunięcia UTC.
• Ulepszono obsługę daty i czasu w całym pluginie.
• Ulepszono przetwarzanie i wyświetlanie danych pogodowych.
• Poprawiono wydajność na słabszych odbiornikach Enigma2 poprzez optymalizację ładowania radaru, dekodowania, pamięci podręcznej i animacji.
• Dodano tryby wydajności Ultra Low-End, Low-End, Auto i Normal.
• Istniejące funkcje pozostają dostępne.
• Jeśli podoba Ci się ten plugin, możesz postawić mi kawę.
'

changelog_RU='
• Исправлены языковые файлы и имена файлов PO/MO.
• Добавлена функция обновления.
• Исправлены Rain Radar, прогноз на семь дней, погодные иконки и перезапуск отдельного GUI.
• Добавлены настраиваемые цвета.
• Добавлены автоматические изображения погоды в зависимости от времени суток и сезонные фоны с автоматической загрузкой и установкой.
• Добавлено отображение восхода и заката солнца, а также восхода и захода луны.
• Добавлено сравнение погодных данных для двух мест, включая время восхода и заката солнца и луны.
• Добавлены тематические цвета для описания погоды, ощущаемой температуры, ветра, дождя и информации о солнце и луне.
• Улучшен поиск городов и выбор города с отдельным окном выбора подходящих мест.
• Улучшены расчёты восхода и захода луны благодаря улучшенной обработке местного времени и смещения UTC.
• Улучшена обработка даты и времени во всём плагине.
• Улучшена обработка и отображение погодных данных.
• Улучшена производительность на слабых ресиверах Enigma2 благодаря оптимизации загрузки радара, декодирования, кэширования и обработки анимаций.
• Добавлены режимы производительности Ultra Low-End, Low-End, Auto и Normal.
• Существующие функции остаются доступными.
• Если вам нравится этот плагин, можете угостить меня чашкой кофе.
'

changelog_SK='
• Opravené jazykové súbory a názvy súborov PO/MO.
• Pridaná funkcia aktualizácie.
• Opravený Rain Radar, sedemdňová predpoveď počasia, ikony počasia a reštart oddeleného GUI.
• Pridané nastaviteľné farby.
• Pridané automatické obrázky počasia podľa dennej doby a sezónne pozadia s automatickým stiahnutím a inštaláciou.
• Pridané zobrazenie východu a západu slnka a tiež východu a západu mesiaca.
• Pridané porovnanie údajov o počasí pre dve lokality vrátane časov východu a západu slnka a mesiaca.
• Pridané tematické farby pre popis počasia, pocitovú teplotu, vietor, dážď a informácie o slnku a mesiaci.
• Vylepšené vyhľadávanie miest a výber mesta pomocou samostatného okna pre zodpovedajúce lokality.
• Vylepšené výpočty východu a západu mesiaca s lepším spracovaním miestneho času a UTC posunu.
• Vylepšené spracovanie dátumu a času v celom plugine.
• Vylepšené spracovanie a zobrazovanie údajov o počasí.
• Vylepšený výkon na slabších prijímačoch Enigma2 optimalizáciou načítania radaru, dekódovania, cache a animácií.
• Pridané režimy výkonu Ultra Low-End, Low-End, Auto a Normal.
• Existujúce funkcie zostávajú dostupné.
• Ak sa vám plugin páči, môžete ma pozvať na kávu.
'

changelog_UA='
• Виправлено мовні файли та назви файлів PO/MO.
• Додано функцію оновлення.
• Виправлено Rain Radar, прогноз погоди на сім днів, іконки погоди та перезапуск окремого GUI.
• Додано налаштовувані кольори.
• Додано автоматичні зображення погоди відповідно до часу доби та сезонні фони з автоматичним завантаженням і встановленням.
• Додано відображення сходу та заходу сонця, а також сходу та заходу місяця.
• Додано порівняння погодних даних для двох місць, включно з часом сходу та заходу сонця і місяця.
• Додано тематичні кольори для опису погоди, відчутної температури, вітру, дощу та інформації про сонце і місяць.
• Покращено пошук міст і вибір міста за допомогою окремого вікна вибору відповідних місць.
• Покращено розрахунки сходу та заходу місяця завдяки кращій обробці місцевого часу та зміщення UTC.
• Покращено обробку дати та часу в усьому плагіні.
• Покращено обробку та відображення погодних даних.
• Покращено продуктивність на слабких приймачах Enigma2 завдяки оптимізації завантаження радара, декодування, кешування та анімації.
• Додано режими продуктивності Ultra Low-End, Low-End, Auto та Normal.
• Існуючі функції залишаються доступними.
• Якщо вам подобається цей плагін, можете пригостити мене кавою.
'

changelog_ZH='
• 修复语言文件以及 PO/MO 文件名。
• 添加更新功能。
• 修复 Rain Radar、七天天气、天气图标以及独立 GUI 重启。
• 添加可自定义颜色。
• 添加根据一天时间自动显示天气图片，以及自动下载和安装季节性背景。
• 添加日出、日落以及月出、月落显示。
• 添加两个地点之间的天气数据比较，包括日出、日落、月出和月落时间。
• 为天气描述、体感温度、风、雨、太阳和月亮信息添加主题颜色。
• 改进城市搜索和城市选择，并使用独立选择窗口显示匹配地点。
• 改进月出和月落计算，更好地处理本地时间和 UTC 偏移。
• 改进整个插件中的日期和时间处理。
• 改进天气数据处理和显示的可靠性。
• 通过优化雷达加载、解码、缓存和动画处理，提高低端 Enigma2 接收机上的性能。
• 添加 Ultra Low-End、Low-End、Auto 和 Normal 性能模式。
• 现有功能继续保留。
• 如果你喜欢这个插件，可以请我喝杯咖啡。
'

###############################################################################
# Generic helpers
###############################################################################

print_line()
{
    echo "---------------------------------------------------------"
}

show_header()
{
    clear 2>/dev/null || true

    echo
    echo "========================================================="
    echo "       speedy_TheWeather installer ${VERSION}"
    echo "========================================================="
    echo
    echo "Repository:"
    echo "https://github.com/${REPO_OWNER}/${REPO_NAME}"
    echo
}

show_info()
{
    echo
    echo "Plugin:"
    echo "${PLUGIN_NAME}"

    echo
    echo "Version:"
    echo "${VERSION}"

    echo
    echo "Branch:"
    echo "${BRANCH}"

    echo
    echo "Install path:"
    echo "${PLUGINPATH}"

    echo
    echo "Changelog:"
    print_line
    echo "Multilingual changelog stored in installer.sh."
    echo "The changelog is displayed by the plugin updater."
    print_line
    echo
}

command_exists()
{
    command -v "$1" >/dev/null 2>&1
}

cleanup_temp()
{
    rm -rf "$TMP_DIR" >/dev/null 2>&1 || true
}

###############################################################################
# Console finish handling
###############################################################################

console_pause()
{
    DELAY="${1:-$FINISH_DELAY}"

    case "$DELAY" in
        ''|*[!0-9]*)
            DELAY=20
            ;;
    esac

    echo
    echo "---------------------------------------------------------"
    echo
    echo "This window will close in ${DELAY} seconds."
    echo
    echo "Please wait..."
    echo

    while [ "$DELAY" -gt 0 ]; do
        printf "\rClosing in %2s seconds..." "$DELAY"
        sleep 1
        DELAY=$((DELAY - 1))
    done

    printf "\rClosing installer...                    \n"
}

finish_success()
{
    echo
    echo
    echo "========================================================="
    echo "       INSTALLATION COMPLETED SUCCESSFULLY"
    echo "========================================================="
    echo
    echo "Plugin:"
    echo "  ${PLUGIN_NAME}"
    echo
    echo "Version:"
    echo "  ${VERSION}"
    echo
    echo "Installed to:"
    echo "  ${PLUGINPATH}"
    echo
    echo "Configuration:"
    echo "  ${CONFIG_DIR}"
    echo
    echo "Automatic backgrounds:"
    echo "  Preserved"
    echo
    echo "---------------------------------------------------------"
    echo
    echo "IMPORTANT"
    echo
    echo "Please restart Enigma2 manually."
    echo
    echo "The installer does NOT restart the GUI automatically."
    echo
    echo "---------------------------------------------------------"
    echo
    echo "Installation finished successfully."
    echo

    console_pause "$FINISH_DELAY"
}

finish_error()
{
    ERROR_MESSAGE="$1"

    echo
    echo
    echo "========================================================="
    echo "              INSTALLATION FAILED"
    echo "========================================================="
    echo
    echo "Error:"
    echo "  ${ERROR_MESSAGE}"
    echo
    echo "The installer has stopped."
    echo
    echo "If a previous installation existed, rollback was attempted."
    echo
    echo "---------------------------------------------------------"

    console_pause "$FINISH_DELAY"
}

die()
{
    ERROR_MESSAGE="$1"

    finish_error "$ERROR_MESSAGE"

    cleanup_temp

    exit 1
}

###############################################################################
# System detection
###############################################################################

detect_system()
{
    echo
    echo "Detecting system..."

    if [ -f /etc/opkg/version ]; then
        PACKAGE_MANAGER="opkg"
        SYSTEM_TYPE="OE/Enigma2"
    elif command_exists apt-get; then
        PACKAGE_MANAGER="apt-get"
        SYSTEM_TYPE="Debian"
    else
        PACKAGE_MANAGER=""
        SYSTEM_TYPE="Unknown"
    fi

    if command_exists python3; then
        PYTHON_BIN="python3"
        PYTHON_VERSION="$(python3 --version 2>&1)"
    elif command_exists python; then
        PYTHON_BIN="python"
        PYTHON_VERSION="$(python --version 2>&1)"
    else
        PYTHON_BIN=""
        PYTHON_VERSION="not found"
    fi

    if [ -f /etc/image-version ]; then
        IMAGE_NAME="$(grep -E '^imagename=' /etc/image-version 2>/dev/null | head -n 1 | cut -d '=' -f 2-)"
        IMAGE_VERSION="$(grep -E '^version=' /etc/image-version 2>/dev/null | head -n 1 | cut -d '=' -f 2-)"
    else
        IMAGE_NAME=""
        IMAGE_VERSION=""
    fi

    if [ -f /etc/issue ]; then
        BOX_INFO="$(head -n 1 /etc/issue 2>/dev/null)"
    else
        BOX_INFO="$(uname -a 2>/dev/null)"
    fi

    echo "System type : ${SYSTEM_TYPE}"
    echo "Package mgr : ${PACKAGE_MANAGER:-not found}"
    echo "Python      : ${PYTHON_VERSION}"
    echo "Image       : ${IMAGE_NAME:-unknown}"
    echo "Image ver.  : ${IMAGE_VERSION:-unknown}"
    echo "Box         : ${BOX_INFO}"
    echo
}

###############################################################################
# Package installation
###############################################################################

install_package()
{
    PACKAGE="$1"

    [ -z "$PACKAGE_MANAGER" ] && return 1

    echo "Trying to install ${PACKAGE}..."

    if [ "$PACKAGE_MANAGER" = "opkg" ]; then
        opkg update >/dev/null 2>&1 || true
        opkg install "$PACKAGE" >/dev/null 2>&1
    elif [ "$PACKAGE_MANAGER" = "apt-get" ]; then
        apt-get update >/dev/null 2>&1 || true
        DEBIAN_FRONTEND=noninteractive apt-get install -y "$PACKAGE" >/dev/null 2>&1
    else
        return 1
    fi
}

find_download_tool()
{
    if command_exists curl; then
        DOWNLOAD_TOOL="curl"
        return 0
    fi

    if command_exists wget; then
        DOWNLOAD_TOOL="wget"
        return 0
    fi

    echo "curl/wget not found."

    if [ "$PACKAGE_MANAGER" = "opkg" ]; then
        install_package curl || install_package wget || true
    elif [ "$PACKAGE_MANAGER" = "apt-get" ]; then
        install_package curl || install_package wget || true
    fi

    if command_exists curl; then
        DOWNLOAD_TOOL="curl"
        return 0
    fi

    if command_exists wget; then
        DOWNLOAD_TOOL="wget"
        return 0
    fi

    return 1
}

###############################################################################
# Download
###############################################################################

download_file()
{
    URL="$1"
    OUTPUT="$2"

    echo
    echo "Downloading:"
    echo "$URL"
    echo

    if [ "$DOWNLOAD_TOOL" = "curl" ]; then
        curl \
            -L \
            --fail \
            --silent \
            --show-error \
            --connect-timeout 20 \
            --max-time 300 \
            -o "$OUTPUT" \
            "$URL"
    elif [ "$DOWNLOAD_TOOL" = "wget" ]; then
        wget \
            -q \
            --timeout=20 \
            --tries=3 \
            -O "$OUTPUT" \
            "$URL"
    else
        return 1
    fi
}

download_archive()
{
    mkdir -p "$TMP_DIR" || \
        die "Could not create temporary directory."

    rm -f "$ARCHIVE_FILE"

    ATTEMPT=1
    MAX_ATTEMPTS=3

    while [ "$ATTEMPT" -le "$MAX_ATTEMPTS" ]; do
        echo "Download attempt ${ATTEMPT}/${MAX_ATTEMPTS}..."

        if download_file "$DOWNLOAD_URL" "$ARCHIVE_FILE"; then
            if [ -s "$ARCHIVE_FILE" ]; then
                echo "Download successful."
                return 0
            fi
        fi

        echo "Download failed."

        rm -f "$ARCHIVE_FILE"

        ATTEMPT=$((ATTEMPT + 1))

        sleep 2
    done

    return 1
}

###############################################################################
# Archive validation
###############################################################################

validate_archive()
{
    echo
    echo "Validating downloaded archive..."

    [ -f "$ARCHIVE_FILE" ] || \
        die "Downloaded archive does not exist."

    if command_exists gzip; then
        gzip -t "$ARCHIVE_FILE" >/dev/null 2>&1 || \
            die "Downloaded file is not a valid gzip archive."
    fi

    if ! tar -tzf "$ARCHIVE_FILE" >/dev/null 2>&1; then
        die "Downloaded file is not a valid tar.gz archive."
    fi

    if ! tar -tzf "$ARCHIVE_FILE" | grep -q '/plugin.py$'; then
        die "Downloaded archive does not contain plugin.py."
    fi

    echo "Archive validation successful."
}

###############################################################################
# Extraction
###############################################################################

extract_archive()
{
    echo
    echo "Extracting archive..."

    rm -rf "$EXTRACT_DIR"

    mkdir -p "$EXTRACT_DIR" || \
        die "Could not create extraction directory."

    tar -xzf "$ARCHIVE_FILE" -C "$EXTRACT_DIR" || \
        die "Could not extract downloaded archive."

    SOURCE_PATH=""

    for DIR in "$EXTRACT_DIR"/*; do

        if [ -f "$DIR/plugin.py" ]; then
            SOURCE_PATH="$DIR"
            break
        fi

        if [ -f "$DIR/Plugins/Extensions/${PLUGIN_NAME}/plugin.py" ]; then
            SOURCE_PATH="$DIR/Plugins/Extensions/${PLUGIN_NAME}"
            break
        fi

        if [ -f "$DIR/usr/lib/enigma2/python/Plugins/Extensions/${PLUGIN_NAME}/plugin.py" ]; then
            SOURCE_PATH="$DIR/usr/lib/enigma2/python/Plugins/Extensions/${PLUGIN_NAME}"
            break
        fi

        if [ -f "$DIR/usr/lib64/enigma2/python/Plugins/Extensions/${PLUGIN_NAME}/plugin.py" ]; then
            SOURCE_PATH="$DIR/usr/lib64/enigma2/python/Plugins/Extensions/${PLUGIN_NAME}"
            break
        fi

    done

    [ -n "$SOURCE_PATH" ] || \
        die "Could not locate plugin source directory."

    echo
    echo "Source:"
    echo "$SOURCE_PATH"
}

###############################################################################
# Repository-only files
###############################################################################

remove_repository_files()
{
    echo
    echo "Removing repository-only files..."

    rm -f \
        "$SOURCE_PATH/README.md" \
        "$SOURCE_PATH/README" \
        "$SOURCE_PATH/installer.sh" \
        "$SOURCE_PATH/version.txt"

    find "$SOURCE_PATH" \
        -type f \
        \( \
            -name "*.svg" \
            -o -name "*backgrounds_auto.zip" \
        \) \
        -delete \
        2>/dev/null || true

    rm -rf \
        "$SOURCE_PATH/converter" \
        "$SOURCE_PATH/renderer"

    echo "Repository-only files removed."
}

###############################################################################
# Source validation
###############################################################################

validate_source()
{
    echo
    echo "Validating plugin source..."

    [ -f "$SOURCE_PATH/plugin.py" ] || \
        die "plugin.py is missing from source."

    if [ -f "$SOURCE_PATH/installer.sh" ]; then
        die "Repository installer.sh was not removed."
    fi

    if [ -f "$SOURCE_PATH/version.txt" ]; then
        die "Repository version.txt was not removed."
    fi

    if [ -d "$SOURCE_PATH/converter" ]; then
        die "Repository converter directory was not removed."
    fi

    if [ -d "$SOURCE_PATH/renderer" ]; then
        die "Repository renderer directory was not removed."
    fi

    echo "Source validation successful."
}

###############################################################################
# Config backup
###############################################################################

backup_config()
{
    echo
    echo "Backing up configuration..."

    rm -rf "$CONFIG_BACKUP"

    if [ -d "$CONFIG_DIR" ]; then
        cp -a "$CONFIG_DIR" "$CONFIG_BACKUP" || \
            die "Could not backup configuration."

        echo "Configuration backup created."
    else
        echo "No existing configuration found."
    fi
}

###############################################################################
# Plugin backup
###############################################################################

backup_plugin()
{
    echo
    echo "Backing up existing plugin..."

    rm -rf "$PLUGIN_BACKUP"

    if [ -d "$PLUGINPATH" ]; then
        cp -a "$PLUGINPATH" "$PLUGIN_BACKUP" || \
            die "Could not backup existing plugin."

        echo "Plugin backup created."
    else
        echo "No existing plugin installation found."
    fi
}

###############################################################################
# Automatic backgrounds backup
###############################################################################

backup_auto_backgrounds()
{
    echo
    echo "Backing up automatic backgrounds..."

    rm -rf "$AUTO_BACKGROUNDS_BACKUP"

    if [ -d "$AUTO_BACKGROUNDS_DIR" ]; then
        cp -a "$AUTO_BACKGROUNDS_DIR" "$AUTO_BACKGROUNDS_BACKUP" || \
            die "Could not backup automatic backgrounds."

        echo "Automatic backgrounds backup created."
    else
        echo "No existing automatic backgrounds found."
    fi
}

###############################################################################
# Restore config
###############################################################################

restore_config()
{
    echo
    echo "Restoring configuration..."

    if [ -d "$CONFIG_BACKUP" ]; then

        rm -rf "$CONFIG_DIR"

        cp -a "$CONFIG_BACKUP" "$CONFIG_DIR" || \
            die "Could not restore configuration."

        echo "Configuration restored."

    else

        echo "No configuration backup found."

    fi
}

###############################################################################
# Restore automatic backgrounds
###############################################################################

restore_auto_backgrounds()
{
    echo
    echo "Restoring automatic backgrounds..."

    if [ -d "$AUTO_BACKGROUNDS_BACKUP" ]; then

        mkdir -p "$(dirname "$AUTO_BACKGROUNDS_DIR")"

        rm -rf "$AUTO_BACKGROUNDS_DIR"

        cp -a "$AUTO_BACKGROUNDS_BACKUP" "$AUTO_BACKGROUNDS_DIR" || \
            die "Could not restore automatic backgrounds."

        echo "Automatic backgrounds restored."

    else

        echo "No automatic backgrounds backup found."

    fi
}

###############################################################################
# Restore previous plugin
###############################################################################

restore_plugin()
{
    echo
    echo "Rolling back plugin installation..."

    rm -rf "$PLUGINPATH"

    if [ -d "$PLUGIN_BACKUP" ]; then

        mkdir -p "$(dirname "$PLUGINPATH")"

        cp -a "$PLUGIN_BACKUP" "$PLUGINPATH" || \
            die "Could not restore previous plugin."

        echo "Previous plugin restored."

    else

        echo "No previous plugin installation existed."

    fi
}

###############################################################################
# Install
###############################################################################

install_plugin()
{
    echo
    echo "Installing plugin..."

    mkdir -p "$(dirname "$PLUGINPATH")" || \
        die "Could not create plugin base directory."

    rm -rf "$PLUGINPATH"

    if ! cp -a "$SOURCE_PATH" "$PLUGINPATH"; then

        echo
        echo "Plugin installation failed."

        restore_plugin
        restore_config
        restore_auto_backgrounds

        die "Could not copy plugin files."
    fi

    echo "Plugin installed."
}

###############################################################################
# Installation validation
###############################################################################

validate_installation()
{
    echo
    echo "Validating installed plugin..."

    [ -d "$PLUGINPATH" ] || {

        restore_plugin
        restore_config
        restore_auto_backgrounds

        die "Installed plugin directory does not exist."
    }

    [ -f "$PLUGINPATH/plugin.py" ] || {

        restore_plugin
        restore_config
        restore_auto_backgrounds

        die "Installed plugin.py is missing."
    }

    if [ -f "$PLUGINPATH/installer.sh" ]; then

        restore_plugin
        restore_config
        restore_auto_backgrounds

        die "installer.sh was accidentally installed."
    fi

    if [ -f "$PLUGINPATH/version.txt" ]; then

        restore_plugin
        restore_config
        restore_auto_backgrounds

        die "version.txt was accidentally installed."
    fi

    if [ -d "$PLUGINPATH/converter" ]; then

        restore_plugin
        restore_config
        restore_auto_backgrounds

        die "converter directory was accidentally installed."
    fi

    if [ -d "$PLUGINPATH/renderer" ]; then

        restore_plugin
        restore_config
        restore_auto_backgrounds

        die "renderer directory was accidentally installed."
    fi

    echo "Installation validation successful."
}

###############################################################################
# Cleanup backups
###############################################################################

cleanup_backups()
{
    echo
    echo "Cleaning up backups..."

    rm -rf "$CONFIG_BACKUP"
    rm -rf "$PLUGIN_BACKUP"
    rm -rf "$AUTO_BACKGROUNDS_BACKUP"

    echo "Backups cleaned."
}

###############################################################################
# Main
###############################################################################

main()
{
    show_header

    show_info

    detect_system

    if ! find_download_tool; then
        die "Neither curl nor wget is available and could not be installed."
    fi

    echo
    echo "Using download tool: ${DOWNLOAD_TOOL}"

    if ! download_archive; then
        die "Could not download the GitHub archive."
    fi

    validate_archive

    extract_archive

    remove_repository_files

    validate_source

    backup_config

    backup_plugin

    backup_auto_backgrounds

    install_plugin

    validate_installation

    restore_config

    restore_auto_backgrounds

    cleanup_backups

    cleanup_temp

    finish_success

    return 0
}

###############################################################################
# Run
###############################################################################

main "$?"

INSTALL_RESULT=$?

exit "$INSTALL_RESULT"

