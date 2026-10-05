```bash
#!/bin/bash

# =========================================================
# speedy_TheWeather Installer
# Version 1.9.9
# =========================================================

VERSION="1.9.9"
BRANCH="master"

REPO_OWNER="speedy005"
REPO_NAME="speedy_TheWeather"

DOWNLOAD_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/heads/${BRANCH}.tar.gz"

# =========================================================
# CHANGELOG
# =========================================================
# Supported languages:
# EN DE AR CS EL FI FR HU IT NL PL RU SK UA ZH
# =========================================================

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
• تم إصلاح ملفات اللغة وأسماء ملفات PO/MO.
• تمت إضافة وظيفة التحديث.
• تم إصلاح رادار المطر والطقس لسبعة أيام وأيقونات الطقس وإعادة تشغيل واجهة المستخدم الرسومية المنفصلة.
• تمت إضافة ألوان قابلة للتخصيص.
• تمت إضافة صور طقس تلقائية حسب وقت اليوم وخلفيات موسمية مع التنزيل والتثبيت التلقائي.
• تمت إضافة عرض شروق وغروب الشمس وشروق وغروب القمر.
• تمت إضافة مقارنة بيانات الطقس لموقعين بما في ذلك أوقات شروق وغروب الشمس والقمر.
• تمت إضافة ألوان مخصصة لوصف الطقس ودرجة الحرارة المحسوسة والرياح والأمطار ومعلومات الشمس والقمر.
• تم تحسين البحث عن المدن واختيار المدينة من خلال نافذة اختيار مخصصة للمواقع المطابقة.
• تم تحسين حسابات شروق وغروب القمر مع معالجة أفضل للتوقيت المحلي وفارق UTC.
• تم تحسين معالجة التاريخ والوقت في جميع أنحاء الإضافة.
• تم تحسين معالجة بيانات الطقس وعرضها بشكل أكثر موثوقية.
• تم تحسين الأداء على أجهزة Enigma2 الضعيفة من خلال تحسين تحميل الرادار وفك التشفير والتخزين المؤقت ومعالجة الرسوم المتحركة.
• تمت إضافة أوضاع أداء Ultra Low-End وLow-End وAuto وNormal.
• جميع الوظائف الحالية لا تزال متاحة.
• إذا أعجبك هذا البرنامج، يمكنك دعوتي إلى فنجان قهوة.
'

changelog_CS='
• Opraveny jazykové soubory a názvy souborů PO/MO.
• Přidána funkce aktualizace.
• Opraven radar deště, sedmidenní předpověď počasí, ikony počasí a restart odděleného GUI.
• Přidány přizpůsobitelné barvy.
• Přidány automatické obrázky počasí podle denní doby a sezónní pozadí s automatickým stažením a instalací.
• Přidáno zobrazení východu a západu slunce a východu a západu měsíce.
• Přidáno porovnání údajů o počasí pro dvě lokality včetně časů východu a západu slunce a měsíce.
• Přidány tematické barvy pro popis počasí, pocitovou teplotu, vítr, déšť a informace o slunci a měsíci.
• Vylepšeno vyhledávání měst a výběr města pomocí samostatného okna s odpovídajícími lokalitami.
• Vylepšeny výpočty východu a západu měsíce s lepším zpracováním místního času a posunu UTC.
• Vylepšeno zpracování data a času v celém pluginu.
• Vylepšeno zpracování a zobrazování údajů o počasí.
• Vylepšen výkon na slabších přijímačích Enigma2 optimalizací načítání radaru, dekódování, cache a animací.
• Přidány režimy výkonu Ultra Low-End, Low-End, Auto a Normal.
• Stávající funkce zůstávají k dispozici.
• Pokud se vám plugin líbí, můžete mě pozvat na kávu.
'

changelog_EL='
• Διορθώθηκαν τα αρχεία γλώσσας και τα ονόματα αρχείων PO/MO.
• Προστέθηκε λειτουργία ενημέρωσης.
• Διορθώθηκαν το ραντάρ βροχής, ο καιρός επτά ημερών, τα εικονίδια καιρού και η επανεκκίνηση του αποσυνδεδεμένου GUI.
• Προστέθηκαν προσαρμόσιμα χρώματα.
• Προστέθηκαν αυτόματες εικόνες καιρού ανάλογα με την ώρα της ημέρας και εποχιακά φόντα με αυτόματη λήψη και εγκατάσταση.
• Προστέθηκε εμφάνιση ανατολής και δύσης του ήλιου καθώς και ανατολής και δύσης της σελήνης.
• Προστέθηκε σύγκριση δεδομένων καιρού για δύο τοποθεσίες, συμπεριλαμβανομένων των ωρών ανατολής και δύσης ήλιου και σελήνης.
• Προστέθηκαν θεματικά χρώματα για την περιγραφή του καιρού, την αισθητή θερμοκρασία, τον άνεμο, τη βροχή και τις πληροφορίες ήλιου και σελήνης.
• Βελτιώθηκε η αναζήτηση πόλεων και η επιλογή πόλης με ειδικό παράθυρο επιλογής για τις αντίστοιχες τοποθεσίες.
• Βελτιώθηκαν οι υπολογισμοί ανατολής και δύσης της σελήνης με καλύτερη διαχείριση τοπικής ώρας και μετατόπισης UTC.
• Βελτιώθηκε η διαχείριση ημερομηνίας και ώρας σε όλο το plugin.
• Βελτιώθηκε η επεξεργασία και η αξιοπιστία εμφάνισης των δεδομένων καιρού.
• Βελτιώθηκε η απόδοση σε αδύναμους δέκτες Enigma2 με βελτιστοποίηση φόρτωσης ραντάρ, αποκωδικοποίησης, cache και κινούμενων εικόνων.
• Προστέθηκαν λειτουργίες απόδοσης Ultra Low-End, Low-End, Auto και Normal.
• Οι υπάρχουσες λειτουργίες παραμένουν διαθέσιμες.
• Αν σας αρέσει το plugin, μπορείτε να με κεράσετε έναν καφέ.
'

changelog_FI='
• Kielitiedostot ja PO/MO-tiedostojen nimet korjattu.
• Päivitystoiminto lisätty.
• Sadetutka, seitsemän päivän sääennuste, sääkuvakkeet ja erillisen käyttöliittymän uudelleenkäynnistys korjattu.
• Mukautettavat värit lisätty.
• Automaattiset sääkuvat vuorokaudenajan mukaan sekä vuodenaikojen taustakuvat automaattisella latauksella ja asennuksella lisätty.
• Auringonnousun ja -laskun sekä kuunnousun ja -laskun näyttö lisätty.
• Kahden sijainnin säätietojen vertailu lisätty, mukaan lukien auringon ja kuun nousu- ja laskuajat.
• Teemavärit sääkuvaukselle, koetulle lämpötilalle, tuulelle, sateelle sekä aurinko- ja kuutiedoille lisätty.
• Kaupunkihakua ja kaupungin valintaa parannettu erillisellä valintaikkunalla.
• Kuun nousu- ja laskulaskelmia parannettu paikallisen ajan ja UTC-siirtymän käsittelyllä.
• Päivämäärän ja ajan käsittelyä parannettu koko pluginissa.
• Säätietojen käsittelyä ja näyttövarmuutta parannettu.
• Suorituskykyä heikoilla Enigma2-vastaanottimilla parannettu optimoimalla tutkan latausta, dekoodausta, välimuistia ja animaatioita.
• Ultra Low-End-, Low-End-, Auto- ja Normal-suorituskykytilat lisätty.
• Nykyiset ominaisuudet ovat edelleen käytettävissä.
• Jos pidät tästä pluginista, voit tarjota minulle kahvin.
'

changelog_FR='
• Correction des fichiers de langue et des noms de fichiers PO/MO.
• Ajout de la fonction de mise à jour.
• Correction du radar de pluie, des prévisions à sept jours, des icônes météo et du redémarrage du GUI séparé.
• Ajout de couleurs personnalisables.
• Ajout d’images météo automatiques selon l’heure de la journée et de fonds saisonniers avec téléchargement et installation automatiques.
• Ajout de l’affichage du lever et du coucher du soleil ainsi que du lever et du coucher de la lune.
• Ajout de la comparaison des données météo pour deux emplacements, y compris les heures de lever et de coucher du soleil et de la lune.
• Ajout de couleurs thématiques pour la description météo, la température ressentie, le vent, la pluie et les informations sur le soleil et la lune.
• Amélioration de la recherche et de la sélection des villes avec une fenêtre dédiée.
• Amélioration des calculs de lever et de coucher de la lune avec une meilleure gestion de l’heure locale et du décalage UTC.
• Amélioration de la gestion de la date et de l’heure dans tout le plugin.
• Amélioration du traitement et de la fiabilité de l’affichage des données météo.
• Amélioration des performances sur les récepteurs Enigma2 peu puissants grâce à l’optimisation du chargement du radar, du décodage, du cache et des animations.
• Ajout des modes de performance Ultra Low-End, Low-End, Auto et Normal.
• Les fonctions existantes restent disponibles.
• Si vous aimez ce plugin, vous pouvez m’offrir un café.
'

changelog_HU='
• A nyelvi fájlok és a PO/MO fájlnevek javítva.
• Frissítési funkció hozzáadva.
• Az esőradar, a hétnapos időjárás, az időjárási ikonok és a leválasztott GUI újraindítása javítva.
• Testreszabható színek hozzáadva.
• Automatikus időjárási képek hozzáadva a napszak alapján, valamint szezonális hátterek automatikus letöltéssel és telepítéssel.
• Napkelte és napnyugta, valamint holdkelte és holdnyugta megjelenítése hozzáadva.
• Két hely időjárási adatainak összehasonlítása hozzáadva, beleértve a nap- és holdkelte, valamint nyugta időpontjait.
• Tematikus színek hozzáadva az időjárás leírásához, a hőérzethez, a szélhez, az esőhöz, valamint a nap- és holdinformációkhoz.
• Javított városkeresés és városválasztás külön kiválasztó ablakkal.
• Javított holdkelte- és holdnyugta-számítás a helyi idő és az UTC-eltolás jobb kezelésével.
• Javított dátum- és időkezelés a teljes pluginban.
• Megbízhatóbb időjárási adatfeldolgozás és megjelenítés.
• Javított teljesítmény gyengébb Enigma2 vevőkön optimalizált radarbetöltéssel, dekódolással, gyorsítótárazással és animációkezeléssel.
• Ultra Low-End, Low-End, Auto és Normal teljesítménymódok hozzáadva.
• A meglévő funkciók továbbra is elérhetők.
• Ha tetszik a plugin, meghívhatsz egy kávéra.
'

changelog_IT='
• Corretti i file delle lingue e i nomi dei file PO/MO.
• Aggiunta la funzione di aggiornamento.
• Corretti il radar della pioggia, le previsioni a sette giorni, le icone meteo e il riavvio della GUI separata.
• Aggiunti colori personalizzabili.
• Aggiunte immagini meteo automatiche in base all’ora del giorno e sfondi stagionali con download e installazione automatici.
• Aggiunta la visualizzazione di alba e tramonto e di levata e tramonto della luna.
• Aggiunto il confronto dei dati meteo per due località, inclusi gli orari di alba, tramonto, levata e tramonto della luna.
• Aggiunti colori tematici per la descrizione del meteo, la temperatura percepita, il vento, la pioggia e le informazioni su sole e luna.
• Migliorata la ricerca e la selezione delle città con una finestra dedicata.
• Migliorati i calcoli del sorgere e tramonto della luna con una gestione migliore dell’ora locale e dell’offset UTC.
• Migliorata la gestione di data e ora in tutto il plugin.
• Migliorata la gestione e l’affidabilità della visualizzazione dei dati meteo.
• Migliorate le prestazioni sui ricevitori Enigma2 meno potenti ottimizzando caricamento radar, decodifica, cache e animazioni.
• Aggiunte le modalità Ultra Low-End, Low-End, Auto e Normal.
• Le funzioni esistenti rimangono disponibili.
• Se ti piace questo plugin, puoi offrirmi un caffè.
'

changelog_NL='
• Taalbestanden en PO/MO-bestandsnamen opgelost.
• Updatefunctie toegevoegd.
• Regenradar, zevendaagse weersvoorspelling, weerpictogrammen en herstart van de losgekoppelde GUI opgelost.
• Aanpasbare kleuren toegevoegd.
• Automatische weerafbeeldingen op basis van het tijdstip van de dag en seizoensachtergronden met automatische download en installatie toegevoegd.
• Weergave van zonsopgang en zonsondergang en maanopkomst en maansondergang toegevoegd.
• Vergelijking van weergegevens voor twee locaties toegevoegd, inclusief tijden van zonsopgang, zonsondergang, maanopkomst en maansondergang.
• Thematische kleuren toegevoegd voor weersbeschrijving, gevoelstemperatuur, wind, regen en informatie over zon en maan.
• Verbeterde stadszoekfunctie en stadsselectie met een speciaal selectievenster voor overeenkomende locaties.
• Berekeningen van maanopkomst en maansondergang verbeterd met betere verwerking van lokale tijd en UTC-offset.
• Datum- en tijdverwerking in de hele plugin verbeterd.
• Verwerking en betrouwbaarheid van de weergave van weergegevens verbeterd.
• Prestaties op minder krachtige Enigma2-ontvangers verbeterd door optimalisatie van radar laden, decodering, caching en animaties.
• Ultra Low-End-, Low-End-, Auto- en Normal-prestatiemodi toegevoegd.
• Bestaande functies blijven beschikbaar.
• Als je deze plugin leuk vindt, kun je me op een koffie trakteren.
'

changelog_PL='
• Naprawiono pliki językowe oraz nazwy plików PO/MO.
• Dodano funkcję aktualizacji.
• Naprawiono radar opadów, prognozę siedmiodniową, ikony pogody oraz restart odłączonego GUI.
• Dodano konfigurowalne kolory.
• Dodano automatyczne obrazy pogody zależne od pory dnia oraz sezonowe tła z automatycznym pobieraniem i instalacją.
• Dodano wyświetlanie wschodu i zachodu słońca oraz wschodu i zachodu księżyca.
• Dodano porównanie danych pogodowych dla dwóch lokalizacji, w tym czasów wschodu i zachodu słońca oraz księżyca.
• Dodano tematyczne kolory dla opisu pogody, temperatury odczuwalnej, wiatru, deszczu oraz informacji o słońcu i księżycu.
• Ulepszono wyszukiwanie i wybór miast za pomocą dedykowanego okna wyboru pasujących lokalizacji.
• Ulepszono obliczenia wschodu i zachodu księżyca dzięki lepszemu uwzględnianiu czasu lokalnego i przesunięcia UTC.
• Ulepszono obsługę daty i czasu w całym pluginie.
• Ulepszono przetwarzanie danych pogodowych i niezawodność ich wyświetlania.
• Poprawiono wydajność na słabszych odbiornikach Enigma2 poprzez optymalizację ładowania radaru, dekodowania, cache i animacji.
• Dodano tryby wydajności Ultra Low-End, Low-End, Auto i Normal.
• Istniejące funkcje pozostają dostępne.
• Jeśli podoba Ci się ten plugin, możesz postawić mi kawę.
'

changelog_RU='
• Исправлены языковые файлы и имена файлов PO/MO.
• Добавлена функция обновления.
• Исправлены радар дождя, прогноз на семь дней, значки погоды и перезапуск отдельного GUI.
• Добавлены настраиваемые цвета.
• Добавлены автоматические изображения погоды в зависимости от времени суток и сезонные фоны с автоматической загрузкой и установкой.
• Добавлено отображение восхода и заката солнца, а также восхода и заката луны.
• Добавлено сравнение погодных данных для двух местоположений, включая время восхода и заката солнца и луны.
• Добавлены тематические цвета для описания погоды, ощущаемой температуры, ветра, дождя, а также информации о солнце и луне.
• Улучшены поиск города и выбор города с отдельным окном выбора подходящих местоположений.
• Улучшены расчёты восхода и захода луны с более точной обработкой местного времени и смещения UTC.
• Улучшена обработка даты и времени во всём плагине.
• Улучшена обработка и надёжность отображения погодных данных.
• Улучшена производительность на слабых ресиверах Enigma2 благодаря оптимизации загрузки радара, декодирования, кэширования и анимации.
• Добавлены режимы производительности Ultra Low-End, Low-End, Auto и Normal.
• Существующие функции остаются доступными.
• Если вам нравится этот плагин, можете угостить меня кофе.
'

changelog_SK='
• Opravené jazykové súbory a názvy súborov PO/MO.
• Pridaná funkcia aktualizácie.
• Opravený radar dažďa, sedemdňová predpoveď počasia, ikony počasia a reštart oddeleného GUI.
• Pridané prispôsobiteľné farby.
• Pridané automatické obrázky počasia podľa dennej doby a sezónne pozadia s automatickým stiahnutím a inštaláciou.
• Pridané zobrazenie východu a západu slnka a východu a západu mesiaca.
• Pridané porovnanie údajov o počasí pre dve lokality vrátane časov východu a západu slnka a mesiaca.
• Pridané tematické farby pre popis počasia, pocitovú teplotu, vietor, dážď a informácie o slnku a mesiaci.
• Vylepšené vyhľadávanie miest a výber mesta pomocou samostatného výberového okna.
• Vylepšené výpočty východu a západu mesiaca s lepším spracovaním miestneho času a posunu UTC.
• Vylepšené spracovanie dátumu a času v celom plugine.
• Vylepšené spracovanie a spoľahlivosť zobrazovania údajov o počasí.
• Vylepšený výkon na slabších prijímačoch Enigma2 optimalizáciou načítania radaru, dekódovania, cache a animácií.
• Pridané režimy výkonu Ultra Low-End, Low-End, Auto a Normal.
• Existujúce funkcie zostávajú dostupné.
• Ak sa vám plugin páči, môžete ma pozvať na kávu.
'

changelog_UA='
• Виправлено мовні файли та назви файлів PO/MO.
• Додано функцію оновлення.
• Виправлено радар дощу, семиденний прогноз погоди, піктограми погоди та перезапуск окремого GUI.
• Додано налаштовувані кольори.
• Додано автоматичні зображення погоди відповідно до часу доби та сезонні фони з автоматичним завантаженням і встановленням.
• Додано відображення сходу та заходу сонця, а також сходу та заходу місяця.
• Додано порівняння погодних даних для двох місць, включаючи час сходу та заходу сонця і місяця.
• Додано тематичні кольори для опису погоди, температури за відчуттями, вітру, дощу та інформації про сонце і місяць.
• Покращено пошук і вибір міста за допомогою окремого вікна вибору відповідних місць.
• Покращено розрахунок сходу та заходу місяця з кращою обробкою місцевого часу та зміщення UTC.
• Покращено роботу з датою та часом у всьому плагіні.
• Покращено обробку погодних даних і надійність їх відображення.
• Покращено продуктивність на слабких ресиверах Enigma2 завдяки оптимізації завантаження радара, декодування, кешування та анімацій.
• Додано режими продуктивності Ultra Low-End, Low-End, Auto та Normal.
• Існуючі функції залишаються доступними.
• Якщо вам подобається цей плагін, можете пригостити мене кавою.
'

changelog_ZH='
• 修复了语言文件以及 PO/MO 文件名。
• 添加了更新功能。
• 修复了降雨雷达、七天天气预报、天气图标以及独立 GUI 重启。
• 添加了可自定义颜色。
• 添加了根据一天中不同时间自动显示天气图片以及自动下载和安装季节性背景。
• 添加了日出、日落以及月出、月落显示。
• 添加了两个地点的天气数据比较，包括日出、日落、月出和月落时间。
• 为天气描述、体感温度、风、降雨以及太阳和月亮信息添加了主题颜色。
• 改进了城市搜索和城市选择，并增加了专用匹配地点选择窗口。
• 改进了月出和月落计算，更好地处理当地时间和 UTC 偏移。
• 改进了整个插件中的日期和时间处理。
• 改进了天气数据处理和显示可靠性。
• 通过优化雷达加载、解码、缓存和动画处理，提高了低端 Enigma2 接收机上的性能。
• 添加了 Ultra Low-End、Low-End、Auto 和 Normal 性能模式。
• 现有功能仍然可用。
• 如果你喜欢这个插件，欢迎请我喝杯咖啡。
'

# =========================================================
# LEGACY CHANGELOG COMPATIBILITY
# =========================================================
# Kept for compatibility with older code/installers.
# The plugin itself should use the changelog_<LANG>
# variables above.
# =========================================================

changelog="$changelog_EN"

# =========================================================
# INSTALLATION PATH
# =========================================================

if [ -d "/usr/lib/enigma2/python/Plugins/Extensions" ]; then

    PLUGIN_BASE="/usr/lib/enigma2/python/Plugins/Extensions"

elif [ -d "/usr/lib64/enigma2/python/Plugins/Extensions" ]; then

    PLUGIN_BASE="/usr/lib64/enigma2/python/Plugins/Extensions"

else

    PLUGIN_BASE="/usr/lib/enigma2/python/Plugins/Extensions"

fi

PLUGIN_NAME="speedy_TheWeather"
PLUGINPATH="${PLUGIN_BASE}/${PLUGIN_NAME}"

# =========================================================
# TEMPORARY FILES
# =========================================================

TMPPATH="/tmp/speedy_TheWeather_installer"
FILEPATH="${TMPPATH}/speedy_TheWeather.tar.gz"
EXTRACTPATH="${TMPPATH}/extract"

OLD_PLUGIN_BACKUP="/tmp/speedy_TheWeather_plugin_backup"

CONFIG_DIR="/etc/enigma2/speedy_TheWeather"
BACKUP_DIR="/tmp/speedy_TheWeather_config_backup"

AUTO_BG_DIR="${PLUGINPATH}/backgrounds/auto"
AUTO_BG_BACKUP="/tmp/speedy_TheWeather_auto_backgrounds_backup"

PLUGIN_SOURCE=""

# =========================================================
# STATE
# =========================================================

BACKUP_CREATED=0
PLUGIN_BACKUP_CREATED=0
AUTO_BG_BACKUP_CREATED=0

OSTYPE="Unknown"
STATUS=""

PYTHON="Unknown"
PYTHON_CMD=""
PYTHON_VERSION="Unknown"

DISTRO="Unknown"
DISTRO_VERSION="Unknown"
BOX_TYPE="Unknown"

DOWNLOADER=""
FILESIZE=0

# =========================================================
# LOGGING
# =========================================================

log()
{
    echo "[speedy_TheWeather] $1"
}

warning()
{
    echo
    echo "WARNING: $1"
    echo
}

error()
{
    echo
    echo "========================================================="
    echo "ERROR"
    echo "========================================================="
    echo "$1"
    echo "========================================================="
    echo
}

# =========================================================
# CLEANUP
# =========================================================

cleanup()
{
    log "Cleaning temporary files..."

    if [ -n "$TMPPATH" ] &&
       [ -d "$TMPPATH" ]; then

        rm -rf "$TMPPATH"

    fi
}

# =========================================================
# ROOT CHECK
# =========================================================

check_root()
{
    if [ "$(id -u)" -ne 0 ]; then

        error "This installer must be executed as root."
        exit 1

    fi
}

# =========================================================
# COMMAND CHECK
# =========================================================

check_command()
{
    command -v "$1" >/dev/null 2>&1
}

# =========================================================
# OS DETECTION
# =========================================================

detect_os()
{
    if check_command opkg; then

        OSTYPE="OE"
        STATUS="/var/lib/opkg/status"

    elif check_command apt-get &&
         [ -f "/var/lib/dpkg/status" ]; then

        OSTYPE="Debian"
        STATUS="/var/lib/dpkg/status"

    elif [ -f "/var/lib/opkg/status" ] ||
         [ -f "/etc/opkg/opkg.conf" ]; then

        OSTYPE="OE"
        STATUS="/var/lib/opkg/status"

    elif [ -f "/etc/debian_version" ] &&
         [ -f "/var/lib/dpkg/status" ]; then

        OSTYPE="Debian"
        STATUS="/var/lib/dpkg/status"

    else

        OSTYPE="Unknown"
        STATUS=""

    fi

    log "Detected OS: $OSTYPE"
}

# =========================================================
# PYTHON DETECTION
# =========================================================

detect_python()
{
    PYTHON_CMD=""
    PYTHON="Unknown"
    PYTHON_VERSION="Unknown"

    if check_command python3; then

        PYTHON_CMD="python3"
        PYTHON="PY3"

    elif check_command python; then

        if python --version 2>&1 |
            grep -q "^Python 3\."
        then

            PYTHON_CMD="python"
            PYTHON="PY3"

        else

            PYTHON_CMD="python"
            PYTHON="PY2"

        fi

    fi

    if [ -n "$PYTHON_CMD" ]; then

        PYTHON_VERSION=$(
            "$PYTHON_CMD" --version 2>&1
        )

        log "Python: $PYTHON_VERSION"

    else

        warning "Python was not found."

    fi
}

# =========================================================
# IMAGE / BOX DETECTION
# =========================================================

detect_image()
{
    BOX_TYPE=$(
        head -n 1 /etc/hostname 2>/dev/null
    )

    [ -z "$BOX_TYPE" ] &&
        BOX_TYPE="Unknown"

    if [ -f "/usr/lib/enigma.info" ]; then

        DISTRO=$(
            grep "^distro=" \
                /usr/lib/enigma.info \
                2>/dev/null |
            head -n 1 |
            cut -d "=" -f 2-
        )

        DISTRO_VERSION=$(
            grep "^imageversion=" \
                /usr/lib/enigma.info \
                2>/dev/null |
            head -n 1 |
            cut -d "=" -f 2-
        )

    elif [ -f "/etc/image-version" ]; then

        DISTRO=$(
            grep "^distro=" \
                /etc/image-version \
                2>/dev/null |
            head -n 1 |
            cut -d "=" -f 2-
        )

        DISTRO_VERSION=$(
            grep "^version=" \
                /etc/image-version \
                2>/dev/null |
            head -n 1 |
            cut -d "=" -f 2-
        )

    fi

    [ -z "$DISTRO" ] &&
        DISTRO="Unknown"

    [ -z "$DISTRO_VERSION" ] &&
        DISTRO_VERSION="Unknown"

    log "Image: $DISTRO $DISTRO_VERSION"
    log "Box: $BOX_TYPE"
}

# =========================================================
# INSTALL CURL
# =========================================================

install_curl()
{
    if check_command curl; then

        log "curl found."
        return 0

    fi

    log "curl not found."

    case "$OSTYPE" in

        OE)

            if check_command opkg; then

                log "Trying to install curl with opkg..."

                opkg update >/dev/null 2>&1 || true

                if opkg install curl >/dev/null 2>&1; then

                    if check_command curl; then

                        log "curl installed."
                        return 0

                    fi

                fi

            fi

            ;;

        Debian)

            if check_command apt-get; then

                log "Trying to install curl with apt..."

                apt-get update >/dev/null 2>&1 || true

                if apt-get install -y curl >/dev/null 2>&1; then

                    if check_command curl; then

                        log "curl installed."
                        return 0

                    fi

                fi

            fi

            ;;

    esac

    return 1
}

# =========================================================
# INSTALL WGET
# =========================================================

install_wget()
{
    if check_command wget; then

        log "wget found."
        return 0

    fi

    log "wget not found."

    case "$OSTYPE" in

        OE)

            if check_command opkg; then

                log "Trying to install wget with opkg..."

                opkg update >/dev/null 2>&1 || true

                if opkg install wget >/dev/null 2>&1; then

                    if check_command wget; then

                        log "wget installed."
                        return 0

                    fi

                fi

            fi

            ;;

        Debian)

            if check_command apt-get; then

                log "Trying to install wget with apt..."

                apt-get update >/dev/null 2>&1 || true

                if apt-get install -y wget >/dev/null 2>&1; then

                    if check_command wget; then

                        log "wget installed."
                        return 0

                    fi

                fi

            fi

            ;;

    esac

    return 1
}

# =========================================================
# SELECT DOWNLOADER
# =========================================================

select_downloader()
{
    DOWNLOADER=""

    if check_command curl; then

        DOWNLOADER="curl"

        log "Downloader selected: curl"

        return 0

    fi

    if check_command wget; then

        DOWNLOADER="wget"

        log "Downloader selected: wget"

        return 0

    fi

    if install_curl; then

        DOWNLOADER="curl"

        log "Downloader selected: curl"

        return 0

    fi

    if install_wget; then

        DOWNLOADER="wget"

        log "Downloader selected: wget"

        return 0

    fi

    error "Neither curl nor wget is available and neither could be installed."

    exit 1
}

# =========================================================
# DOWNLOAD
# =========================================================

download_package()
{
    log "Preparing download..."
    log "Version: $VERSION"
    log "Repository: ${REPO_OWNER}/${REPO_NAME}"
    log "Branch: $BRANCH"
    log "URL: $DOWNLOAD_URL"

    mkdir -p "$TMPPATH"

    rm -f "$FILEPATH"

    if [ "$DOWNLOADER" = "curl" ]; then

        log "Downloading with curl..."

        if curl \
            -L \
            --fail \
            --silent \
            --show-error \
            --connect-timeout 20 \
            --max-time 120 \
            --retry 3 \
            --retry-delay 2 \
            "$DOWNLOAD_URL" \
            -o "$FILEPATH"
        then

            log "curl download completed."

        else

            error "GitHub download failed using curl."

            return 1

        fi

    elif [ "$DOWNLOADER" = "wget" ]; then

        log "Downloading with wget..."

        if wget \
            -q \
            --server-response \
            --timeout=30 \
            --tries=3 \
            "$DOWNLOAD_URL" \
            -O "$FILEPATH" \
            2>"${TMPPATH}/wget.log"
        then

            log "wget download completed."

        else

            error "GitHub download failed using wget."

            if [ -f "${TMPPATH}/wget.log" ]; then

                echo
                echo "wget output:"
                echo "---------------------------------------------------------"

                cat "${TMPPATH}/wget.log"

                echo "---------------------------------------------------------"
                echo

            fi

            return 1

        fi

    else

        error "No downloader selected."

        return 1

    fi

    if [ ! -f "$FILEPATH" ]; then

        error "Download finished but archive file does not exist."

        return 1

    fi

    if [ ! -s "$FILEPATH" ]; then

        error "Downloaded archive is empty."

        return 1

    fi

    FILESIZE=$(
        wc -c < "$FILEPATH" 2>/dev/null
    )

    log "Downloaded size: ${FILESIZE} bytes"

    if [ "$FILESIZE" -lt 1000 ]; then

        warning "Downloaded file is suspiciously small."

        echo
        echo "First bytes of downloaded file:"
        echo "---------------------------------------------------------"

        head -c 500 "$FILEPATH" 2>/dev/null

        echo
        echo "---------------------------------------------------------"
        echo

        return 1

    fi

    return 0
}

# =========================================================
# VALIDATE ARCHIVE
# =========================================================

validate_archive()
{
    log "Validating downloaded archive..."

    if ! check_command gzip; then

        error "gzip command not found."

        return 1

    fi

    if ! check_command tar; then

        error "tar command not found."

        return 1

    fi

    if ! gzip -t "$FILEPATH" >/dev/null 2>&1; then

        error "Downloaded file is not a valid gzip archive."

        return 1

    fi

    log "gzip validation successful."

    if ! tar -tzf "$FILEPATH" >/dev/null 2>&1; then

        error "Downloaded file is not a valid tar archive."

        return 1

    fi

    log "tar validation successful."

    if ! tar -tzf "$FILEPATH" 2>/dev/null |
        grep -q "/plugin.py$"
    then

        error "Archive does not contain plugin.py."

        echo
        echo "Archive contents:"
        echo "---------------------------------------------------------"

        tar -tzf "$FILEPATH" 2>/dev/null |
            head -100

        echo "---------------------------------------------------------"
        echo

        return 1

    fi

    log "Archive contains plugin.py."

    return 0
}

# =========================================================
# EXTRACT PACKAGE
# =========================================================

extract_package()
{
    log "Extracting package..."

    rm -rf "$EXTRACTPATH"

    if ! mkdir -p "$EXTRACTPATH"; then

        error "Could not create extraction directory."

        return 1

    fi

    if ! tar \
        -xzf "$FILEPATH" \
        -C "$EXTRACTPATH"
    then

        error "Failed to extract archive."

        return 1

    fi

    log "Archive extracted successfully."

    return 0
}

# =========================================================
# FIND PLUGIN SOURCE
# =========================================================

find_plugin_source()
{
    PLUGIN_SOURCE=""

    log "Searching extracted archive for plugin..."

    while IFS= read -r FILE
    do

        [ -z "$FILE" ] &&
            continue

        DIR="$(dirname "$FILE")"

        if [ -f "$DIR/plugin.py" ] &&
           [ -f "$DIR/__init__.py" ]; then

            PLUGIN_SOURCE="$DIR"

            break

        fi

    done < <(
        find "$EXTRACTPATH" \
            -type f \
            -name "plugin.py" \
            2>/dev/null
    )

    if [ -z "$PLUGIN_SOURCE" ]; then

        error "Could not find speedy_TheWeather plugin files."

        echo
        echo "Extracted directories:"
        echo "---------------------------------------------------------"

        find "$EXTRACTPATH" \
            -maxdepth 6 \
            -type d \
            2>/dev/null |
            head -100

        echo
        echo "Plugin files:"
        echo "---------------------------------------------------------"

        find "$EXTRACTPATH" \
            -type f \
            \( \
                -name "plugin.py" \
                -o -name "__init__.py" \
            \) \
            2>/dev/null |
            head -100

        echo

        return 1

    fi

    log "Plugin source found:"
    log "$PLUGIN_SOURCE"

    return 0
}

# =========================================================
# VALIDATE PLUGIN SOURCE
# =========================================================

validate_plugin_source()
{
    if [ ! -d "$PLUGIN_SOURCE" ]; then

        error "Plugin source directory does not exist."

        return 1

    fi

    if [ ! -f "$PLUGIN_SOURCE/__init__.py" ]; then

        error "__init__.py is missing."

        return 1

    fi

    if [ ! -f "$PLUGIN_SOURCE/plugin.py" ]; then

        error "plugin.py is missing."

        return 1

    fi

    log "Plugin source validation successful."

    return 0
}

# =========================================================
# REMOVE REPOSITORY-ONLY FILES
# =========================================================

remove_repository_only_files()
{
    log "Removing repository-only files..."

    if [ ! -d "$PLUGIN_SOURCE" ]; then

        return 1

    fi

    find "$PLUGIN_SOURCE" \
        -type f \
        \( \
            -name "README.md" \
            -o -name "README" \
            -o -name "installer.sh" \
            -o -name "version.txt" \
            -o -name "*.svg" \
            -o -name "*backgrounds_auto.zip" \
        \) \
        -print \
        -delete \
        2>/dev/null

    if [ -d "$PLUGIN_SOURCE/converter" ]; then

        rm -rf "$PLUGIN_SOURCE/converter"

        log "Removed converter/"

    fi

    if [ -d "$PLUGIN_SOURCE/renderer" ]; then

        rm -rf "$PLUGIN_SOURCE/renderer"

        log "Removed renderer/"

    fi

    log "Repository-only files removed."

    return 0
}

# =========================================================
# CONFIG BACKUP
# =========================================================

backup_config()
{
    BACKUP_CREATED=0

    if [ ! -d "$CONFIG_DIR" ]; then

        log "No existing configuration found."

        return 0

    fi

    log "Backing up configuration..."

    rm -rf "$BACKUP_DIR"

    if cp -a "$CONFIG_DIR" "$BACKUP_DIR"; then

        BACKUP_CREATED=1

        log "Configuration backup successful."

        return 0

    fi

    error "Configuration backup failed."

    return 1
}

# =========================================================
# CONFIG RESTORE
# =========================================================

restore_config()
{
    if [ "$BACKUP_CREATED" -ne 1 ]; then

        return 0

    fi

    if [ ! -d "$BACKUP_DIR" ]; then

        warning "Configuration backup disappeared."

        return 1

    fi

    log "Restoring configuration..."

    rm -rf "$CONFIG_DIR"

    if ! mkdir -p "$CONFIG_DIR"; then

        warning "Could not recreate configuration directory."

        return 1

    fi

    if cp -a "$BACKUP_DIR"/. "$CONFIG_DIR"/; then

        log "Configuration restored."

        rm -rf "$BACKUP_DIR"

        BACKUP_CREATED=0

        return 0

    fi

    warning "Configuration restore failed."

    return 1
}

# =========================================================
# PLUGIN BACKUP
# =========================================================

backup_existing_plugin()
{
    PLUGIN_BACKUP_CREATED=0

    rm -rf "$OLD_PLUGIN_BACKUP"

    if [ ! -d "$PLUGINPATH" ]; then

        log "No previous plugin installation found."

        return 0

    fi

    log "Backing up existing plugin..."

    if cp -a "$PLUGINPATH" "$OLD_PLUGIN_BACKUP"; then

        PLUGIN_BACKUP_CREATED=1

        log "Existing plugin backup created."

        return 0

    fi

    error "Could not backup existing plugin."

    return 1
}

# =========================================================
# ROLLBACK PLUGIN
# =========================================================

rollback_plugin()
{
    if [ "$PLUGIN_BACKUP_CREATED" -ne 1 ]; then

        log "No plugin backup available for rollback."

        return 0

    fi

    if [ ! -d "$OLD_PLUGIN_BACKUP" ]; then

        warning "Plugin backup directory not found."

        return 1

    fi

    log "Rolling back previous plugin..."

    rm -rf "$PLUGINPATH"

    if ! mkdir -p "$PLUGIN_BASE"; then

        warning "Could not create plugin base directory."

        return 1

    fi

    if cp -a "$OLD_PLUGIN_BACKUP" "$PLUGINPATH"; then

        log "Plugin rollback successful."

        rm -rf "$OLD_PLUGIN_BACKUP"

        PLUGIN_BACKUP_CREATED=0

        return 0

    fi

    warning "Plugin rollback failed."

    return 1
}

# =========================================================
# AUTOMATIC BACKGROUND BACKUP
# =========================================================

backup_auto_backgrounds()
{
    AUTO_BG_BACKUP_CREATED=0

    if [ ! -d "$AUTO_BG_DIR" ]; then

        log "No existing automatic background directory."

        return 0

    fi

    if [ -z "$(
        find "$AUTO_BG_DIR" \
            -type f \
            2>/dev/null |
        head -n 1
    )" ]; then

        log "Automatic background directory is empty."

        return 0

    fi

    log "Backing up automatic weather backgrounds..."

    rm -rf "$AUTO_BG_BACKUP"

    if ! mkdir -p "$AUTO_BG_BACKUP"; then

        warning "Could not create background backup."

        return 1

    fi

    if cp -a \
        "$AUTO_BG_DIR"/. \
        "$AUTO_BG_BACKUP"/ \
        2>/dev/null
    then

        AUTO_BG_BACKUP_CREATED=1

        log "Automatic background backup successful."

        return 0

    fi

    rm -rf "$AUTO_BG_BACKUP"

    warning "Automatic background backup failed."

    return 1
}

# =========================================================
# RESTORE AUTOMATIC BACKGROUNDS
# =========================================================

restore_auto_backgrounds()
{
    if [ "$AUTO_BG_BACKUP_CREATED" -ne 1 ]; then

        return 0

    fi

    if [ ! -d "$AUTO_BG_BACKUP" ]; then

        warning "Automatic background backup not found."

        return 1

    fi

    NEW_AUTO_BG_DIR="${PLUGINPATH}/backgrounds/auto"

    log "Restoring automatic weather backgrounds..."

    if ! mkdir -p "$NEW_AUTO_BG_DIR"; then

        warning "Could not create automatic background directory."

        return 1

    fi

    if cp -a \
        "$AUTO_BG_BACKUP"/. \
        "$NEW_AUTO_BG_DIR"/ \
        2>/dev/null
    then

        log "Automatic backgrounds restored."

        rm -rf "$AUTO_BG_BACKUP"

        AUTO_BG_BACKUP_CREATED=0

        return 0

    fi

    warning "Automatic background restore failed."

    return 1
}

# =========================================================
# INSTALL PLUGIN
# =========================================================

install_plugin()
{
    log "Installing speedy_TheWeather v${VERSION}..."

    if ! mkdir -p "$PLUGIN_BASE"; then

        error "Could not create plugin base directory."

        return 1

    fi

    if [ -d "$PLUGINPATH" ]; then

        log "Removing old plugin installation..."

        if ! rm -rf "$PLUGINPATH"; then

            error "Could not remove old plugin installation."

            return 1

        fi

    fi

    if ! mkdir -p "$PLUGINPATH"; then

        error "Could not create plugin directory."

        return 1

    fi

    if ! remove_repository_only_files; then

        error "Could not clean repository-only files."

        return 1

    fi

    log "Copying plugin files..."

    if ! cp -a \
        "$PLUGIN_SOURCE"/. \
        "$PLUGINPATH"/
    then

        error "Failed to copy plugin files."

        return 1

    fi

    log "Plugin files copied."

    if [ ! -f "$PLUGINPATH/__init__.py" ]; then

        error "__init__.py missing after installation."

        return 1

    fi

    if [ ! -f "$PLUGINPATH/plugin.py" ]; then

        error "plugin.py missing after installation."

        return 1

    fi

    if [ -z "$(
        find "$PLUGINPATH" \
            -type f \
            2>/dev/null |
        head -n 1
    )" ]; then

        error "Plugin installation is empty."

        return 1

    fi

    if [ -f "$PLUGINPATH/README.md" ]; then

        error "README.md was installed unexpectedly."

        return 1

    fi

    if [ -f "$PLUGINPATH/installer.sh" ]; then

        error "installer.sh was installed unexpectedly."

        return 1

    fi

    if [ -f "$PLUGINPATH/version.txt" ]; then

        error "version.txt was installed unexpectedly."

        return 1

    fi

    if find "$PLUGINPATH" \
        -type f \
        -name "*.svg" \
        -print \
        -quit \
        2>/dev/null |
        grep -q .
    then

        error "An SVG file was installed unexpectedly."

        return 1

    fi

    if [ -d "$PLUGINPATH/converter" ]; then

        error "converter/ was installed unexpectedly."

        return 1

    fi

    if [ -d "$PLUGINPATH/renderer" ]; then

        error "renderer/ was installed unexpectedly."

        return 1

    fi

    log "Plugin installation verified."

    return 0
}

# =========================================================
# REMOVE OLD PLUGIN BACKUP
# =========================================================

remove_old_plugin_backup()
{
    if [ -d "$OLD_PLUGIN_BACKUP" ]; then

        rm -rf "$OLD_PLUGIN_BACKUP"

        PLUGIN_BACKUP_CREATED=0

        log "Old plugin backup removed."

    fi
}

# =========================================================
# CLEAN BACKUP STATE
# =========================================================

cleanup_backups()
{
    if [ "$BACKUP_CREATED" -eq 1 ]; then

        rm -rf "$BACKUP_DIR"

        BACKUP_CREATED=0

    fi

    if [ "$AUTO_BG_BACKUP_CREATED" -eq 1 ]; then

        rm -rf "$AUTO_BG_BACKUP"

        AUTO_BG_BACKUP_CREATED=0

    fi
}

# =========================================================
# INSTALLATION FAILED
# =========================================================

installation_failed()
{
    error "$1"

    log "Starting rollback..."

    if [ "$PLUGIN_BACKUP_CREATED" -eq 1 ]; then

        rollback_plugin

    fi

    if [ "$BACKUP_CREATED" -eq 1 ]; then

        restore_config

    fi

    if [ "$AUTO_BG_BACKUP_CREATED" -eq 1 ]; then

        restore_auto_backgrounds

    fi

    cleanup

    echo
    echo "========================================================="
    echo " speedy_TheWeather installation FAILED"
    echo "========================================================="
    echo

    exit 1
}

# =========================================================
# SHOW INFO
# =========================================================

show_info()
{
    echo
    echo "#########################################################"
    echo "#                                                       #"
    echo "#          speedy_TheWeather INSTALLED                 #"
    echo "#                                                       #"
    echo "#########################################################"
    echo "#                                                       #"
    echo "#  Version:       $VERSION"
    echo "#  Plugin path:   $PLUGINPATH"
    echo "#  Branch:        $BRANCH"
    echo "#  OS:            $OSTYPE"
    echo "#  Image:         $DISTRO"
    echo "#  Image version: $DISTRO_VERSION"
    echo "#  Box:            $BOX_TYPE"
    echo "#  Python:         $PYTHON_VERSION"
    echo "#  Downloader:     $DOWNLOADER"
    echo "#                                                       #"
    echo "#  GUI was NOT restarted automatically.                #"
    echo "#                                                       #"
    echo "#########################################################"
    echo

    echo "Repository-only content excluded:"
    echo "---------------------------------------------------------"
    echo "README.md"
    echo "installer.sh"
    echo "version.txt"
    echo "*.svg"
    echo "converter/"
    echo "renderer/"
    echo "*backgrounds_auto.zip"
    echo "---------------------------------------------------------"
    echo

    echo "Changelog EN:"
    echo "---------------------------------------------------------"
    echo "$changelog_EN"
    echo "---------------------------------------------------------"
    echo

    echo "Changelog DE:"
    echo "---------------------------------------------------------"
    echo "$changelog_DE"
    echo "---------------------------------------------------------"
    echo

    echo "Changelog AR:"
    echo "---------------------------------------------------------"
    echo "$changelog_AR"
    echo "---------------------------------------------------------"
    echo

    echo "Changelog CS:"
    echo "---------------------------------------------------------"
    echo "$changelog_CS"
    echo "---------------------------------------------------------"
    echo

    echo "Changelog EL:"
    echo "---------------------------------------------------------"
    echo "$changelog_EL"
    echo "---------------------------------------------------------"
    echo

    echo "Changelog FI:"
    echo "---------------------------------------------------------"
    echo "$changelog_FI"
    echo "---------------------------------------------------------"
    echo

    echo "Changelog FR:"
    echo "---------------------------------------------------------"
    echo "$changelog_FR"
    echo "---------------------------------------------------------"
    echo

    echo "Changelog HU:"
    echo "---------------------------------------------------------"
    echo "$changelog_HU"
    echo "---------------------------------------------------------"
    echo

    echo "Changelog IT:"
    echo "---------------------------------------------------------"
    echo "$changelog_IT"
    echo "---------------------------------------------------------"
    echo

    echo "Changelog NL:"
    echo "---------------------------------------------------------"
    echo "$changelog_NL"
    echo "---------------------------------------------------------"
    echo

    echo "Changelog PL:"
    echo "---------------------------------------------------------"
    echo "$changelog_PL"
    echo "---------------------------------------------------------"
    echo

    echo "Changelog RU:"
    echo "---------------------------------------------------------"
    echo "$changelog_RU"
    echo "---------------------------------------------------------"
    echo

    echo "Changelog SK:"
    echo "---------------------------------------------------------"
    echo "$changelog_SK"
    echo "---------------------------------------------------------"
    echo

    echo "Changelog UA:"
    echo "---------------------------------------------------------"
    echo "$changelog_UA"
    echo "---------------------------------------------------------"
    echo

    echo "Changelog ZH:"
    echo "---------------------------------------------------------"
    echo "$changelog_ZH"
    echo "---------------------------------------------------------"
    echo
}

# =========================================================
# FINAL
# =========================================================

finish_install()
{
    sync >/dev/null 2>&1 || true

    echo
    echo "========================================================="
    echo " speedy_TheWeather v${VERSION} installed successfully."
    echo "========================================================="
    echo
    echo "The Enigma2 GUI was NOT restarted automatically."
    echo "Please restart Enigma2 manually."
    echo

    return 0
}

# =========================================================
# MAIN
# =========================================================

echo
echo "========================================================="
echo "       speedy_TheWeather Installer v${VERSION}"
echo "========================================================="
echo

check_root

detect_os
detect_python
detect_image

select_downloader

cleanup

if ! mkdir -p "$TMPPATH"; then

    error "Could not create temporary directory: $TMPPATH"

    exit 1

fi

# =========================================================
# DOWNLOAD
# IMPORTANT:
# Do NOT touch the existing installation yet.
# =========================================================

if ! download_package; then

    cleanup

    exit 1

fi

# =========================================================
# VALIDATE ARCHIVE
# =========================================================

if ! validate_archive; then

    cleanup

    exit 1

fi

# =========================================================
# EXTRACT
# =========================================================

if ! extract_package; then

    cleanup

    exit 1

fi

# =========================================================
# FIND PLUGIN
# =========================================================

if ! find_plugin_source; then

    cleanup

    exit 1

fi

# =========================================================
# VALIDATE PLUGIN
# =========================================================

if ! validate_plugin_source; then

    cleanup

    exit 1

fi

# =========================================================
# BACKUP CURRENT CONFIGURATION
# =========================================================

if ! backup_config; then

    cleanup

    exit 1

fi

# =========================================================
# BACKUP CURRENT PLUGIN
# =========================================================

if ! backup_existing_plugin; then

    cleanup

    exit 1

fi

# =========================================================
# BACKUP AUTOMATIC BACKGROUNDS
# =========================================================

if ! backup_auto_backgrounds; then

    installation_failed \
        "Automatic weather background backup failed."

fi

# =========================================================
# INSTALL
# =========================================================

if ! install_plugin; then

    installation_failed \
        "Plugin installation failed."

fi

# =========================================================
# RESTORE CONFIGURATION
# =========================================================

if ! restore_config; then

    installation_failed \
        "Configuration restore failed."

fi

# =========================================================
# RESTORE AUTOMATIC BACKGROUNDS
# =========================================================

if ! restore_auto_backgrounds; then

    installation_failed \
        "Automatic weather backgrounds could not be restored."

fi

# =========================================================
# REMOVE OLD BACKUP
# =========================================================

remove_old_plugin_backup

# =========================================================
# CLEAN BACKUP STATE
# =========================================================

cleanup_backups

# =========================================================
# CLEAN TEMPORARY FILES
# =========================================================

cleanup

# =========================================================
# SHOW INFORMATION
# =========================================================

show_info

# =========================================================
# FINISH
# =========================================================

finish_install

exit 0
```
