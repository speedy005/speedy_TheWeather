#-----------------------------------------------------------------------------
# v.1.6.3
# Original work by Caught
# https://www.linuxsat-support.com/cms/user/40812-caught/
# Modified by speedy005
# Copyright © Caught. All rights reserved.
# Modifications and improvements © speedy005.
# This software is based on the original work of Caught.
# Original author and modification credits must remain in the source code.
# -----------------------------------------------------------------------------
# Centralized all weather-related HTTP requests.
# Added proper timeouts and response cleanup.
#  Added a 5-minute cache for weather data.
#  Improved city/ID search robustness.
#  Added proper handling of special characters in city names.
#  Added Internet connectivity checks via Buienradar.
#  Cleaned up bare except: statements.
#  Removed blocking 1-second delays.
#  Added validation for invalid hour values.
#  Corrected Sunrise/Sunset handling.
#  Moved radar network requests to a background thread.
#  Radar results are subsequently processed in a controlled manner on the Enigma2 main thread.
#  Radar refresh continues to be handled via eTimer.
#  Radar timers are properly stopped and cleaned up when closing.
#  Existing functionality and screens remain essentially unchanged.
#  Python 2/3 compatibility has been taken into account.
#  Syntax check: OK
#  Python compilation check: OK
# -----------------------------------------------------------------------------
# v.1.7.0 Changelog (English):
#  - Added low-end performance optimizations for weak Enigma2 receivers.
#  - Reduced radar worker concurrency and radar timer wakeups.
#  - Added adaptive radar frame count for low-end receivers.
#  - Improved incremental PNG decoding to keep the GUI responsive.
#  - Prevented unnecessary radar animation work while frames are decoding.
#  - Added Performance mode: Auto / Low-End / Normal.
#  - Kept the existing radar UI and core features intact.
#  - Fixed weather icon handling and improved radar screen stability.
#  - Fixed date display in the Seven Day Weather screen.
#  - Improved detached GUI restart handling.
#  - Added customizable color settings.
#  - Added update-function support for version and changelog information.
#  - Fixed malformed locale language-file handling and improved PO/MO naming.
#
# v.1.7.0 Changelog (Deutsch):
#  - Low-End-Optimierungen für schwache Enigma2-Receiver hinzugefügt.
#  - Radar-Worker und unnötige Timer-Aufrufe reduziert.
#  - Adaptive Anzahl der Radar-Frames für schwache Receiver hinzugefügt.
#  - Inkrementelles PNG-Decoding verbessert, damit die GUI flüssig bleibt.
#  - Unnötige Radar-Animation während des Decodings verhindert.
#  - Performance-Modus hinzugefügt: Auto / Low-End / Normal.
#  - Vorhandene Radar-Oberfläche und Kernfunktionen beibehalten.
#  - Wetter-Icons korrigiert und die Stabilität des Radar-Bildschirms verbessert.
#  - Datumsanzeige im Sieben-Tage-Wetter korrigiert.
#  - Neustart der getrennten GUI verbessert.
#  - Individuell einstellbare Farben hinzugefügt.
#  - Update-Funktion für Versions- und Changelog-Informationen hinzugefügt.
#  - Fehlerhafte Locale-Sprachdatei behoben und PO/MO-Namen korrigiert.
#
# Support the project: Buy me a coffee if you like this plugin!
# Unterstützung für das Projekt: Wenn dir das Plugin gefällt, spendiere mir
# gerne einen Kaffee!
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
from enigma import eTimer
from enigma import ePoint
from Screens.Screen import Screen
from Components.Label import Label
from time import strftime, localtime
from Components.config import config, ConfigSelection, configfile, ConfigSubsection, getConfigListEntry
from Screens.ChoiceBox import ChoiceBox
from enigma import ePicLoad, getDesktop
from Components.MenuList import MenuList
from Components.Language import language
from Screens.MessageBox import MessageBox
from Screens.InfoBar import InfoBar
from Plugins.Plugin import PluginDescriptor
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
        ("low", _("Low-End")),
        ("normal", _("Normal"))
    ]
)

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

def getCoordsFromEntry(value):
    parts = safeStr(value).split("|")
    if len(parts) == 3:
        try:
            return float(parts[1]), float(parts[2])
        except ValueError:
            return None, None
    return None, None

__version__ = "1.6.3"
VERSION = __version__

version = '1.6.3'

# Installer/update changelog text. Keep both languages available so the
# update screen can display a localized release description.
CHANGELOG_EN = (
    "Low-end performance optimizations for weak Enigma2 receivers. "
    "Reduced radar workers and timer wakeups. Adaptive radar frame count "
    "and incremental PNG decoding. Added Performance mode (Auto / Low-End / Normal). "
    "Fixed weather icons, Seven Day Weather date display, radar screen stability, "
    "detached GUI restart handling, malformed locale language files and PO/MO names. "
    "Added customizable color settings and update-function support. "
    "Buy me a coffee if you like this plugin."
)

CHANGELOG_DE = (
    "Low-End-Optimierungen für schwache Enigma2-Receiver. "
    "Radar-Worker und Timer-Aufrufe reduziert. Adaptive Radar-Frame-Anzahl "
    "und inkrementelles PNG-Decoding. Performance-Modus (Auto / Low-End / Normal) hinzugefügt. "
    "Wetter-Icons, Datumsanzeige im Sieben-Tage-Wetter, Radar-Bildschirm, "
    "GUI-Neustart sowie fehlerhafte Locale-Sprachdateien und PO/MO-Namen korrigiert. "
    "Individuelle Farbeinstellungen und Update-Funktion hinzugefügt. "
    "Wenn dir das Plugin gefällt, spendiere mir gerne einen Kaffee."
)

UPDATE_RAW_BASE = (
    "https://raw.githubusercontent.com/"
    "speedy005/speedy_TheWeather/master"
)

UPDATE_PLUGIN_URL = (
    UPDATE_RAW_BASE +
    "/plugin.py"
)

UPDATE_INSTALLER_URL = (
    UPDATE_RAW_BASE +
    "/installer.sh"
)

UPDATE_CHECK_DELAY_MS = 8000
UPDATE_CHECK_TIMEOUT = 15

UPDATE_INSTALLER_PATH = (
    "/tmp/speedy_TheWeather_update_installer.sh"
)

UPDATE_SUCCESS_FILE = (
    "/tmp/speedy_TheWeather_update_success"
)


_updateStartTimer = None
_updatePollTimer = None

_updateQueue = queue.Queue()

_updateCheckStarted = False
_updateWorkerStarted = False
_updateInstallInProgress = False

_updateInfo = None

_updateConsole = None


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

def _update_is_newer(remote_version):

    return (
        _version_tuple(remote_version)
        >
        _version_tuple(version)
    )

# ============================================================================
# UPDATE DOWNLOAD
# ============================================================================

def _update_download(
    url,
    destination,
    timeout=None
):
    """
    Lädt eine Datei mit HTTP-Timeout und User-Agent herunter.
    """

    response = None

    if timeout is None:

        timeout = UPDATE_CHECK_TIMEOUT

    try:

        request = Request(
            url,
            headers={
                "User-Agent":
                    "speedy_TheWeather-Updater/1.0",

                "Accept":
                    "text/plain,"
                    "application/octet-stream,"
                    "*/*"
            }
        )

        response = urlopen(
            request,
            timeout=timeout
        )

        with open(
            destination,
            "wb"
        ) as target:

            while True:

                chunk = response.read(
                    64 * 1024
                )

                if not chunk:

                    break

                target.write(
                    chunk
                )

        return (
            os.path.isfile(
                destination
            )
            and
            os.path.getsize(
                destination
            ) > 0
        )

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "Update download failed:",
            e
        )

        return False

    finally:

        if response is not None:

            try:

                response.close()

            except Exception:

                pass

# ============================================================================
# EXTRACT PLUGIN VERSION
# ============================================================================

def _update_extract_plugin_version(source):
    """
    Read the plugin version from remote plugin.py
    without executing the remote code.
    """

    try:

        import ast

        tree = ast.parse(
            source,
            filename="plugin.py"
        )

        # ------------------------------------------------------------
        # Check direct string assignments.
        #
        # Supported:
        #
        # version = "1.4.4"
        # __version__ = "1.4.4"
        #
        # ------------------------------------------------------------

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
                    "version",
                    "__version__"
                ):
                    continue

                value = node.value

                if isinstance(
                    value,
                    ast.Constant
                ) and isinstance(
                    value.value,
                    str
                ):

                    return value.value.strip()

                if (
                    hasattr(
                        ast,
                        "Str"
                    )
                    and isinstance(
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

def _update_extract_installer_info(source):
    """
    Liest version/changelog aus installer.sh.
    """

    result = {
        "version": "",
        "changelog": ""
    }

    try:

        import re

        match = re.search(
            r"^version=['\"]([^'\"]+)['\"]",
            source,
            re.MULTILINE
        )

        if match:

            result["version"] = (
                match.group(1)
                .strip()
            )

        match = re.search(
            r"^(?:changelog|hangelog)=['\"](.*?)['\"]",
            source,
            re.MULTILINE
        )

        if match:

            result["changelog"] = (
                match.group(1)
                .strip()
            )

    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "Could not read installer information:",
            e
        )

    return result

# ============================================================================
# CHANGELOG TEXT
# ============================================================================

def _update_changes_text(changes):

    if isinstance(
        changes,
        (list, tuple)
    ):

        items = [
            safeStr(item).strip()
            for item in changes
            if safeStr(item).strip()
        ]

        if items:

            return "\n".join(
                "- " + _(item)
                for item in items
            )

    if safeStr(
        changes
    ).strip():

        return _(
            safeStr(
                changes
            ).strip()
        )

    return _(
        "No changes available."
    )

# ============================================================================
# UPDATE CHECK WORKER
# ============================================================================

def _update_check_worker():
    """
    Netzwerkprüfung im Hintergrund,
    damit Enigma2 nicht einfriert.
    """

    plugin_path = None
    installer_path = None

    try:

        # --------------------------------------------------------------------
        # TEMP PLUGIN FILE
        # --------------------------------------------------------------------

        fd, plugin_path = tempfile.mkstemp(
            prefix=".speedy_TheWeather_remote_",
            suffix=".py",
            dir="/tmp"
        )

        os.close(fd)


        # --------------------------------------------------------------------
        # DOWNLOAD REMOTE PLUGIN
        # --------------------------------------------------------------------

        if not _update_download(
            UPDATE_PLUGIN_URL,
            plugin_path
        ):

            _updateQueue.put(
                (
                    "error",
                    _(
                        "Update check failed."
                    )
                )
            )

            return


        # --------------------------------------------------------------------
        # READ REMOTE SOURCE
        # --------------------------------------------------------------------

        with open(
            plugin_path,
            "r",
            encoding="utf-8"
        ) as source_file:

            remote_source = (
                source_file.read()
            )


        # --------------------------------------------------------------------
        # CHECK SYNTAX
        # --------------------------------------------------------------------

        import ast

        ast.parse(
            remote_source,
            filename="plugin.py"
        )


        # --------------------------------------------------------------------
        # READ VERSION
        # --------------------------------------------------------------------

        remote_version = (
            _update_extract_plugin_version(
                remote_source
            )
        )

        if not remote_version:

            _updateQueue.put(
                (
                    "error",
                    _(
                        "Update information is incomplete."
                    )
                )
            )

            return


        # --------------------------------------------------------------------
        # CURRENT VERSION
        # --------------------------------------------------------------------

        if not _update_is_newer(
            remote_version
        ):

            print(
                "[speedy_TheWeather] "
                "Plugin is up to date: %s"
                % remote_version
            )

            _updateQueue.put(
                (
                    "current",
                    {
                        "version":
                            remote_version
                    }
                )
            )

            return


        # --------------------------------------------------------------------
        # TEMP INSTALLER INFORMATION
        # --------------------------------------------------------------------

        fd, installer_path = tempfile.mkstemp(
            prefix=".speedy_TheWeather_installer_info_",
            suffix=".sh",
            dir="/tmp"
        )

        os.close(fd)


        installer_info = {
            "version": "",
            "changelog": ""
        }


        if _update_download(
            UPDATE_INSTALLER_URL,
            installer_path
        ):

            try:

                with open(
                    installer_path,
                    "r",
                    encoding="utf-8"
                ) as installer_file:

                    installer_source = (
                        installer_file.read()
                    )

                installer_info = (
                    _update_extract_installer_info(
                        installer_source
                    )
                )

            except Exception as e:

                print(
                    "[speedy_TheWeather] "
                    "Could not read installer changelog:",
                    e
                )


        # --------------------------------------------------------------------
        # CHANGELOG
        # --------------------------------------------------------------------

        changes = (
            installer_info.get(
                "changelog",
                ""
            )
        )

        if not changes:

            changes = _(
                "No changes available."
            )


        # --------------------------------------------------------------------
        # SEND RESULT TO MAIN THREAD
        # --------------------------------------------------------------------

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


    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "Update check failed:",
            e
        )

        _updateQueue.put(
            (
                "error",
                _(
                    "Update check failed."
                )
            )
        )


    finally:

        for path in (
            plugin_path,
            installer_path
        ):

            if (
                path
                and
                os.path.exists(path)
            ):

                try:

                    os.unlink(path)

                except Exception:

                    pass

# ============================================================================
# UPDATE POLL
# ============================================================================

def _update_poll():

    global _updatePollTimer
    global _updateInfo

    try:

        while True:

            result, payload = (
                _updateQueue.get_nowait()
            )


            # ----------------------------------------------------------------
            # UPDATE AVAILABLE
            # ----------------------------------------------------------------

            if result == "available":

                _updateInfo = payload

                _update_show_message(
                    payload
                )


            # ----------------------------------------------------------------
            # CURRENT
            # ----------------------------------------------------------------

            elif result == "current":

                print(
                    "[speedy_TheWeather] "
                    "Plugin is up to date: %s"
                    % payload.get(
                        "version",
                        ""
                    )
                )


            # ----------------------------------------------------------------
            # INSTALLING
            # ----------------------------------------------------------------

            elif result == "installing":

                _update_show_installing()


            # ----------------------------------------------------------------
            # INSTALLED
            # ----------------------------------------------------------------

            elif result == "installed":

                _update_install_finished()


            # ----------------------------------------------------------------
            # ERROR
            # ----------------------------------------------------------------

            elif result == "error":

                print(
                    "[speedy_TheWeather] "
                    + safeStr(payload)
                )


            # ----------------------------------------------------------------
            # INSTALL ERROR
            # ----------------------------------------------------------------

            elif result == "install_error":

                _update_install_error()


    except queue.Empty:

        pass


    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "Update poll failed:",
            e
        )


    try:

        if _updatePollTimer is not None:

            _updatePollTimer.start(
                500,
                True
            )

    except Exception:

        pass

# ============================================================================
# START UPDATE WORKER
# ============================================================================

def _update_begin_worker():

    global _updatePollTimer
    global _updateWorkerStarted

    if _updateWorkerStarted:

        return

    _updateWorkerStarted = True


    try:

        _updatePollTimer = eTimer()

        safeTimerCallback(
            _updatePollTimer,
            _update_poll
        )

        _updatePollTimer.start(
            500,
            True
        )


    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "Could not start update poll timer:",
            e
        )

        return


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

# ============================================================================
# START UPDATE CHECK
# ============================================================================

def _update_start_check():

    global _updateStartTimer
    global _updateCheckStarted

    if _updateCheckStarted:

        return


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
            "Could not start update timer:",
            e
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


    message = (
        _(
            "A new version of speedy_TheWeather "
            "is available."
        )
        + "\n\n"
        + _(
            "Installed version: %s"
        )
        % VERSION
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
            "Could not show install message:",
            e
        )

# ============================================================================
# UPDATE INSTALL
# ============================================================================

def _update_install():

    global _updateInstallInProgress
    global _updateConsole

    if (
        _updateInstallInProgress
        or
        not _updateInfo
    ):

        return


    _updateInstallInProgress = True


    _updateQueue.put(
        (
            "installing",
            None
        )
    )


    try:

        print(
            "[speedy_TheWeather] "
            "Downloading installer..."
        )


        # --------------------------------------------------------------------
        # REMOVE OLD SUCCESS MARKER
        # --------------------------------------------------------------------

        try:

            if os.path.exists(
                UPDATE_SUCCESS_FILE
            ):

                os.unlink(
                    UPDATE_SUCCESS_FILE
                )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "Could not remove old success marker:",
                e
            )


        # --------------------------------------------------------------------
        # DOWNLOAD INSTALLER
        # --------------------------------------------------------------------

        if not _update_download(
            UPDATE_INSTALLER_URL,
            UPDATE_INSTALLER_PATH,
            timeout=30
        ):

            raise IOError(
                "installer download failed"
            )


        print(
            "[speedy_TheWeather] "
            "Installer downloaded to: %s"
            % UPDATE_INSTALLER_PATH
        )


        # --------------------------------------------------------------------
        # MAKE INSTALLER EXECUTABLE
        # --------------------------------------------------------------------

        try:

            os.chmod(
                UPDATE_INSTALLER_PATH,
                0o755
            )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "chmod failed: %s"
                % e
            )


        # --------------------------------------------------------------------
        # VERIFY INSTALLER
        # --------------------------------------------------------------------

        if not os.path.exists(
            UPDATE_INSTALLER_PATH
        ):

            raise IOError(
                "installer file does not exist"
            )


        # --------------------------------------------------------------------
        # START CONSOLE
        # --------------------------------------------------------------------

        from Screens.Console import Console


        if _overlaySession is None:

            raise RuntimeError(
                "No active Enigma2 session available for update"
            )


        # --------------------------------------------------------------------
        # IMPORTANT
        #
        # Console.py does not pass the installer return code to
        # finishedCallback().
        #
        # Therefore the shell command creates a success marker ONLY
        # when installer.sh exits with code 0.
        # --------------------------------------------------------------------

        cmd = (
            "/bin/bash \"%s\""
            " && "
            "/bin/touch \"%s\""
            %
            (
                UPDATE_INSTALLER_PATH,
                UPDATE_SUCCESS_FILE
            )
        )


        print(
            "[speedy_TheWeather] "
            "Starting installer in Console..."
        )


        _updateConsole = (
            _overlaySession.open(
                Console,
                _("Updating..."),
                cmdlist=[
                    cmd
                ],
                finishedCallback=
                    update_finished,
                closeOnSuccess=True
            )
        )


    except Exception as e:

        _updateInstallInProgress = False

        print(
            "[speedy_TheWeather] "
            "Update installation failed:",
            e
        )


        _updateQueue.put(
            (
                "install_error",
                None
            )
        )

# ============================================================================
# INSTALLER FINISHED
# ============================================================================

def update_finished():

    global _updateConsole
    global _updateInstallInProgress
    global _updateRestartTimer

    print(
        "[speedy_TheWeather] "
        "Update installer finished"
    )

    _updateConsole = None

    success = os.path.exists(
        UPDATE_SUCCESS_FILE
    )

    print(
        "[speedy_TheWeather] "
        "Update success marker: %s"
        % success
    )

    # ------------------------------------------------------------------------
    # SUCCESS
    # ------------------------------------------------------------------------

    if success:

        _updateInstallInProgress = False

        try:
            if os.path.exists(
                UPDATE_INSTALLER_PATH
            ):
                os.unlink(
                    UPDATE_INSTALLER_PATH
                )
        except Exception:
            pass

        print(
            "[speedy_TheWeather] "
            "Installer completed successfully."
        )

        # MessageBox nicht direkt aus dem
        # Console-Callback öffnen.
        try:

            _updateRestartTimer = eTimer()

            def show_restart_message():

                global _updateRestartTimer

                try:
                    _updateRestartTimer.stop()
                except Exception:
                    pass

                _updateRestartTimer = None

                print(
                    "[speedy_TheWeather] "
                    "Showing restart question."
                )

                _update_install_finished()

            _updateRestartTimer.callback.append(
                show_restart_message
            )

            _updateRestartTimer.start(
                200,
                True
            )

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "Could not start restart timer: %s"
                % e
            )

            _update_install_finished()

        # GANZ WICHTIG:
        # Nach erfolgreicher Installation hier abbrechen.
        return

    # ------------------------------------------------------------------------
    # FAILURE
    # ------------------------------------------------------------------------

    print(
        "[speedy_TheWeather] "
        "Installer did NOT complete successfully."
    )

    _updateInstallInProgress = False

    _updateQueue.put(
        (
            "install_error",
            None
        )
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
                quitMainloop(3)
            except Exception as e:
                print(
                    "[speedy_TheWeather] "
                    "Could not restart Enigma2 GUI:",
                    e
                )
        else:
            print(
                "[speedy_TheWeather] "
                "User chose NOT to restart Enigma2 GUI."
            )

    # ------------------------------------------------------------------------
    # ASK USER ONCE
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
            "Could not show update restart question:",
            e
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
_RADAR_MAX_WORKERS = 2
_RADAR_LOW_WORKERS = 1
_RADAR_NORMAL_WORKERS = 2
_RADAR_LOW_FRAME_COUNT = 4
_RADAR_NORMAL_FRAME_COUNT = 5
_RADAR_LOW_DECODE_DELAY_MS = 65
_RADAR_NORMAL_DECODE_DELAY_MS = 35
_RADAR_LOW_ANIM_MS = 1900
_RADAR_NORMAL_ANIM_MS = 1500
_RADAR_POLL_INTERVAL_MS = 300

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
    try:
        stat = os.stat(path)
        if stat.st_size <= 0 or time.time() - stat.st_mtime > _TILE_CACHE_TTL:
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
    query = safeStr(query).strip()
    if not query:
        return None, None
    parts = query.split('_', 1)
    city = parts[0].strip()
    country = parts[1].strip().lower() if len(parts) == 2 else ''
    if not city:
        return None, None
    url = 'https://location.buienradar.nl/1.1/location/search?query=' + quote_plus(city)
    results = _http_json(url)
    if not isinstance(results, list) or not results:
        return None, None
    selected = results[0]
    if country:
        for item in results:
            if safeStr(item.get('countrycode', '')).lower() == country:
                selected = item
                break
    city_id = selected.get('id')
    if city_id is None:
        return None, None
    data = _http_json('https://forecast.buienradar.nl/2.0/forecast/%s' % city_id)
    if data is None:
        return None, None
    name = '%s  %s' % (selected.get('name', city), selected.get('countrycode', ''))
    return data, name.strip()

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

    # ------------------------------------------------
    # Aktuelles Wetter
    # ------------------------------------------------
    COLOR_CITY        = "#0000ff00"   # Grün – Stadt/Ort
    COLOR_BIGTEMP     = "#000000ff"   # Blau – Temperatur
    COLOR_WEATHERTYPE = "#00ff0000"   # Rot
    COLOR_FEELS       = "#00ffff00"   # Gelb
    COLOR_WIND        = "#0000ffff"   # Cyan
    # ------------------------------------------------
    # 7-Tage-Vorhersage
    # ------------------------------------------------
    COLOR_DAY         = "#0000ff00"   # Grün
    COLOR_MAXTEMP     = "#00ff0000"   # Rot
    COLOR_MINTEMP     = "#00004080"   # Dunkelblau
    COLOR_DAYTYPE     = "#00ffff00"   # Gelb
    # ------------------------------------------------
    # Sonne
    # ------------------------------------------------
    COLOR_SUN         = "#00ffff00"   # Gelb
    # ------------------------------------------------
    # Stundenübersicht
    # ------------------------------------------------
    COLOR_HOUR        = "#00ff0000"   # Rot – Uhrzeit / Stunde
    COLOR_HOURTEMP    = "#004080ff"   # Blau – Temperatur / Grad
    COLOR_RAIN        = "#0000ff00"   # Grün
    COLOR_SUNPERCENT  = "#00ffff00"   # Gelb
    COLOR_HUMIDITY    = "#004080ff"   # Blau
    COLOR_WIND_SPEED  = "#0000ffff"   # Cyan
    # ------------------------------------------------
    # Uhr / Datum
    # ------------------------------------------------
    COLOR_CLOCK       = "#00ff0000"   # Weiß
    COLOR_DATE        = "#0000ff00"   # Weiß
    # ------------------------------------------------
    
    # ------------------------------------------------
    # colors samples
    # ------------------------------------------------
    #COLOR_01 = "#ffff0000"  # Rot
    #COLOR_02 = "#ff00ff00"  # Grün
    #COLOR_03 = "#ff0000ff"  # Blau
    #COLOR_04 = "#ffffff00"  # Gelb
    #COLOR_05 = "#ff00ffff"  # Cyan
    #COLOR_06 = "#ffff00ff"  # Magenta
    #COLOR_07 = "#ffffffff"  # Weiß
    #COLOR_08 = "#ff000000"  # Schwarz

    #COLOR_09 = "#ffff8000"  # Orange
    #COLOR_10 = "#ffff4000"  # Dunkelorange
    #COLOR_11 = "#ffffc000"  # Gold
    #COLOR_12 = "#ffffd700"  # Goldgelb
    #COLOR_13 = "#ff808000"  # Oliv
    #COLOR_14 = "#ff80ff00"  # Limette
    #COLOR_15 = "#ff00ff80"  # Türkisgrün
    #COLOR_16 = "#ff008080"  # Petrol

    #COLOR_17 = "#ff0080ff"  # Himmelblau
    #COLOR_18 = "#ff0040ff"  # Tiefblau
    #COLOR_19 = "#ff4000ff"  # Violettblau
    #COLOR_20 = "#ff8000ff"  # Violett
    #COLOR_21 = "#ffc000ff"  # Pinkviolett
    #COLOR_22 = "#ffff0080"  # Pink
    #COLOR_23 = "#ffff4080"  # Hellpink
    #COLOR_24 = "#ffff80c0"  # Rosa

    #COLOR_25 = "#ffff8080"  # Hellrot
    #COLOR_26 = "#ffff4040"  # Korallenrot
    #COLOR_27 = "#ffc00000"  # Dunkelrot
    #COLOR_28 = "#ff800000"  # Weinrot
    #COLOR_29 = "#ff804000"  # Braun
    #COLOR_30 = "#ffc08040"  # Hellbraun
    #COLOR_31 = "#ffe0c080"  # Beige
    #COLOR_32 = "#ffffe0c0"  # Creme

    #COLOR_33 = "#ff80ff80"  # Hellgrün
    #COLOR_34 = "#ff40c040"  # Mittelgrün
    #COLOR_35 = "#ff008000"  # Dunkelgrün
    #COLOR_36 = "#ff004000"  # Sehr dunkelgrün
    #COLOR_37 = "#ffc0ff80"  # Gelbgrün
    #COLOR_38 = "#ff80c000"  # Grasgrün

    #COLOR_39 = "#ff80ffff"  # Hellcyan
    #COLOR_40 = "#ff40c0ff"  # Hellblau
    #COLOR_41 = "#ff80c0ff"  # Pastellblau
    #COLOR_42 = "#ff004080"  # Dunkelblau
    #COLOR_43 = "#ff002040"  # Marineblau

    #COLOR_44 = "#ffc080ff"  # Hellviolett
    #COLOR_45 = "#ff8040c0"  # Mittelviolett
    #COLOR_46 = "#ff400080"  # Dunkelviolett

    #COLOR_47 = "#ff808080"  # Grau
    #COLOR_48 = "#ffc0c0c0"  # Hellgrau
    #COLOR_49 = "#ff404040"  # Dunkelgrau
    #COLOR_50 = "#ffe0e0e0"  # Sehr hellgrau
    
    # ================================================================
    # COLOR ASSIGNMENT
    # ================================================================

    # COLOR_CITY        → City name
    # COLOR_BIGTEMP     → Large current temperature
    # COLOR_WEATHERTYPE → Weather description
    # COLOR_FEELS       → Feels-like temperature
    # COLOR_WIND        → Wind direction
    #
    # COLOR_DAY         → Day of the week
    # COLOR_MAXTEMP     → Maximum temperature
    # COLOR_MINTEMP     → Minimum temperature
    # COLOR_DAYTYPE     → Weather description for individual days
    #
    # COLOR_SUN         → Sunrise / sunset
    #
    # COLOR_HOUR        → Time / hour
    # COLOR_HOURTEMP    → Temperature in hourly forecast
    # COLOR_RAIN        → Rain
    # COLOR_SUNPERCENT  → Sun probability
    # COLOR_HUMIDITY    → Humidity
    # COLOR_WIND_SPEED  → Wind speed
    #
    # COLOR_CLOCK       → Clock
    # COLOR_DATE        → Date
    
    # ================================================================
    # FARBZUORDNUNG
    # ================================================================

    # COLOR_CITY        → Stadtname
    # COLOR_BIGTEMP     → große aktuelle Temperatur
    # COLOR_WEATHERTYPE → Wetterbeschreibung
    # COLOR_FEELS       → gefühlte Temperatur
    # COLOR_WIND        → Windrichtung
    #
    # COLOR_DAY         → Wochentag
    # COLOR_MAXTEMP     → Höchsttemperatur
    # COLOR_MINTEMP     → Tiefsttemperatur
    # COLOR_DAYTYPE     → Wetterbeschreibung der einzelnen Tage
    #
    # COLOR_SUN         → Sonnenauf-/untergang
    #
    # COLOR_HOUR        → Uhrzeit / Stunde
    # COLOR_HOURTEMP    → Temperatur im Stundenverlauf
    # COLOR_RAIN        → Regen
    # COLOR_SUNPERCENT  → Sonnenwahrscheinlichkeit
    # COLOR_HUMIDITY    → Luftfeuchtigkeit
    # COLOR_WIND_SPEED  → Windgeschwindigkeit
    #
    # COLOR_CLOCK       → Uhr
    # COLOR_DATE        → Datum

    WEATHER_PATH = (
        "/usr/lib/enigma2/python/Plugins/Extensions/"
        "speedy_TheWeather"
    )

    # ================================================================
    # ALLGEMEIN
    # ================================================================

    def _path(self, *parts):
        return "/".join([self.WEATHER_PATH] + list(parts))

    def _day(self, data, n):
        return data[n] if n < len(data) else {}

    def _wind(self, day):
        try:
            wind = str(day.get("winddirection") or "na")

            if wind == "na" and day.get("hours"):
                wind = str(
                    day["hours"][0].get("winddirection") or "na"
                )

            return wind

        except Exception:
            return "na"

    def _icon(self, day):
        """
        Tages-/großes Wettericon exakt aus iconcode.
        Kein Fallback auf hours[0].
        """

        try:
            return str(day.get("iconcode") or "na")
        except Exception:
            return "na"

    def _temp_picture(self, data):
        temps = []

        try:
            for day in data:
                for hour in day.get("hours", []):
                    if hour.get("temperature") is not None:
                        temps.append(
                            round(float(hour["temperature"]))
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

        except Exception:
            pass

        return sunrise, sunset

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
            color="#00ffffff"
        ):
        return (
            '<widget render="Label" source="{0}" '
            'position="{1}" size="{2}" zPosition="3" '
            'valign="{3}" halign="{4}" font="Regular;{5}" '
            'foregroundColor="{6}" '
            'backgroundColor="#00202020" transparent="1" '
            'shadowColor="black" shadowOffset="-2,-2"/>'
        ).format(
            source,
            pos,
            size,
            valign,
            halign,
            font,
            color
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
    #
    # Keine externen PNG-Dateien nötig.
    # Die Beschriftungen werden direkt als Label erzeugt.
    # ================================================================

    # ================================================================
    # FARBTASTEN
    # ================================================================

    def _color_buttons_xml(self, hd=True):

        if hd:

            buttons = [
                ("key_red",    "27,1040",  "310,45", "red",    "20,1050",  "8,25", 38),
                ("key_green",  "342,1040", "310,45", "green",  "335,1050", "8,25", 38),
                ("key_yellow", "657,1040", "310,45", "yellow", "650,1050", "8,25", 38),
                ("key_blue",   "972,1040", "510,45", "blue",   "965,1050", "8,25", 34)
            ]

        else:
            buttons = [
                ("key_red", "20,684", "300,28", "red", "13,691", "6,14", 25),
                ("key_green", "325,684", "300,28", "green", "318,691", "6,14", 25),
                ("key_yellow", "630,684", "300,28", "yellow", "623,691", "6,14", 25),
                ("key_blue", "935,684", "500,28", "blue", "928,691", "6,14", 22)
            ]

        xml = ""

        for name, pos, size, foreground, button_pos, button_size, font in buttons:

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

    
    def _build_day_section(self, day, data, hd=True):

        icon = self._icon(data)
        wind = self._wind(data)
        hours = data.get("hours", [])

        if hd:

            cfg = {
                "bigpos": "636,102",
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

                "sunpos": "625,362",
                "sunsize": "200,40",
                "sunfont": 28,

                "suniconpos": "650,295",
                "suniconsize": "120,60",

                "hourx": 120,
                "hourstep": 216,
                "houry": 749,
                "hoursize": "72,72",
                "hourscale": False
            }

        else:

            cfg = {
                "bigpos": "422,76",
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

                "sunpos": "416,248",
                "sunsize": "200,40",
                "sunfont": 18,

                "suniconpos": "426,206",
                "suniconsize": "80,40",

                "hourx": 80,
                "hourstep": 144,
                "houry": 494,
                "hoursize": "48,48",
                "hourscale": True
            }

        base = self.WEATHER_PATH
        path = icoonpath

        xml = ""

        # ================================================================
        # GROSSES WETTER-ICON
        # ================================================================

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

        # ================================================================
        # WINDRICHTUNGS-ICON SD
        # ================================================================

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

        # ================================================================
        # KLEINES WETTER-ICON
        # ================================================================

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

        # ================================================================
        # WOCHENTAG
        # ================================================================

        xml += self._label_xml(
            "smallday2{}".format(day),
            cfg["daypos"],
            cfg["daysize"],
            cfg["dayfont"],
            color=self.COLOR_DAY
        )

        # ================================================================
        # MAXIMALE TEMPERATUR
        # ================================================================

        xml += self._label_xml(
            "maxtemp2{}".format(day),
            cfg["maxpos"],
            cfg["maxsize"],
            cfg["maxfont"],
            color=self.COLOR_MAXTEMP
        )

        # ================================================================
        # MINIMALE TEMPERATUR
        # ================================================================

        xml += self._label_xml(
            "minitemp2{}".format(day),
            cfg["minpos"],
            cfg["minsize"],
            cfg["minfont"],
            color=self.COLOR_MINTEMP
        )

        # ================================================================
        # WETTERBESCHREIBUNG
        # ================================================================

        xml += self._label_xml(
            "weertype2{}".format(day),
            cfg["typepos"],
            cfg["typesize"],
            cfg["typefont"],
            "center",
            color=self.COLOR_DAYTYPE
        )

        # ================================================================
        # SONNENAUF- / UNTERGANG
        # ================================================================

        xml += self._label_xml(
            "sunriselab",
            cfg["sunpos"],
            cfg["sunsize"],
            cfg["sunfont"],
            color=self.COLOR_SUN
        )

        # ================================================================
        # SONNEN-ICON
        # ================================================================

        xml += self._eicon_xml(
            cfg["suniconpos"],
            cfg["suniconsize"],
            "{}/{}/iconhd/sunupdownhd.png".format(
                base,
                path
            ),
            not hd
        )

        # ================================================================
        # PIXMAPS / LABELS REGISTRIEREN
        # ================================================================

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

        # ================================================================
        # 8 STUNDEN-ICONS
        # ================================================================

        for slot in range(8):

            hour = (
                hours[slot]
                if slot < len(hours)
                else {}
            )

            hour_icon = str(
                hour.get("iconcode") or "na"
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

            self._pixmap(name)

        return xml


    # ================================================================
    # STUNDENBEREICH
    # ================================================================

    def _build_hour_section(self, hour, hd=True):

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
                489,
                "129,205",
                "vlak_uursd.png"
            )

            labels = [
                (
                    "dayhour3",
                    64 + x,
                    506,
                    "129,28",
                    20,
                    "center"
                ),
               (
                    "daytemp3",
                    80 + x,
                    540,
                    "120,36",
                    32,
                    "left"
                ),
                (
                    "sunpercent3",
                    112 + x,
                    580,
                    "82,21",
                    18,
                    "left"
                ),
                (
                    "daypercent3",
                    112 + x,
                    606,
                    "80,20",
                    18,
                    "left"
                ),
                (
                    "hrdayper3",
                    112 + x,
                    632,
                    "80,20",
                    18,
                    "left"
                ),
                (
                    "dayspeed3",
                    112 + x,
                    658,
                    "82,21",
                    18,
                    "left"
                )
            ]

            icons = [
                (
                    "sunicon",
                    76 + x,
                    578,
                    "24,24",
                    "sunpchd.png"
                ),
                (
                    "rainicon",
                    77 + x,
                    605,
                    "20,20",
                    "rainhd.png"
                ),
                (
                    "rhicon",
                    79 + x,
                    632,
                    "16,20",
                    "rhhd.png"
                ),
                (
                    "windicon",
                    79 + x,
                    656,
                    "25,25",
                    "turbinehd.png"
                )
            ]

            scale = True

        # ================================================================
        # STUNDEN-HINTERGRUND
        # ================================================================

        name = "vlakuur{}".format(hour)

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

        self._pixmap(name)

        # ================================================================
        # STUNDEN-LABELS
        # ================================================================

        for prefix, px, py, size, font, align in labels:

            name = "{}{}".format(
                prefix,
                hour
            )

            # ------------------------------------------------------------
            # Farbe je nach Label
            # ------------------------------------------------------------

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

            self._label(name)

        # ================================================================
        # STUNDEN-ICONS
        # ================================================================

        for prefix, px, py, size, filename in icons:

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

            self._pixmap(name)

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
                    position="1100,350"
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
                    foregroundColor="#00ffff00"
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
                    "870,298",
                    "480,40",
                    28,
                    color=self.COLOR_WEATHERTYPE
                ),

                feel=self._label_xml(
                    "GevoelsTemp1",
                    "870,250",
                    "354,40",
                    28,
                    color=self.COLOR_FEELS
                ),

                wind=self._label_xml(
                    "winddir1",
                    "870,346",
                    "330,45",
                    28,
                    color=self.COLOR_WIND
                )
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
                position="795,240"
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
                size="340,42"
                zPosition="3"
                valign="center"
                halign="left"
                font="Regular;32"
                foregroundColor="#00ffff00"
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
                "565,208",
                "320,30",
                18,
                color=self.COLOR_WEATHERTYPE
            ),

            feel=self._label_xml(
                "GevoelsTemp1",
                "565,176",
                "236,30",
                18,
                color=self.COLOR_FEELS
            ),

            wind=self._label_xml(
                "winddir1",
                "565,240",
                "230,30",
                18,
                color=self.COLOR_WIND
            )
        )
        

    # ================================================================
    # HD SKIN
    # ================================================================

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
                self._day(data, day),
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

            <!-- ================================================= -->
            <!-- MENU + OK OBEN RECHTS                            -->
            <!-- ================================================= -->

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

            <!-- ================================================= -->
            <!-- FARBTASTEN UNTEN                                 -->
            <!-- ================================================= -->

            {colorbuttons}

        </screen>
        """.format(

            base=self.WEATHER_PATH,
            pack=SHARED_PACK,
            path=icoonpath,
            tempicon=tempicon,
            content=content,

            # ------------------------------------------------
            # Uhrzeit – WEISS
            # ------------------------------------------------

            clock=self._clock_xml(
                "1760,35",
                "400,45",
                30,
                "%H:%M:%S",
                color=self.COLOR_CLOCK
            ),

            # ------------------------------------------------
            # Datum – GELB
            # ------------------------------------------------

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

            colorbuttons=self._color_buttons_xml(True)
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
                self._day(data, day),
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

            <!-- ================================================= -->
            <!-- MENU + OK UNTEN RECHTS                           -->
            <!-- ================================================= -->

            <ePixmap
                pixmap="{base}/{pack}/buttons/menubuttonsd.png"
                position="1100,680"
                size="60,36"
                zPosition="10"
                alphatest="blend"/>

            <ePixmap
                pixmap="{base}/{pack}/buttons/okbuttonsd.png"
                position="1170,680"
                size="36,36"
                zPosition="10"
                alphatest="blend"/>

            <!-- ================================================= -->
            <!-- FARBTASTEN UNTEN                                 -->
            <!-- ================================================= -->

            {colorbuttons}

        </screen>
        """.format(

            base=self.WEATHER_PATH,
            pack=SHARED_PACK,
            path=icoonpath,
            tempicon=tempicon,
            content=content,

            # ------------------------------------------------
            # Uhrzeit – WEISS
            # ------------------------------------------------

            clock=self._clock_xml(
                "1091,12",
                "150,55",
                24,
                "%H:%M:%S",
                color=self.COLOR_CLOCK
            ),

            # ------------------------------------------------
            # Datum – GELB
            # ------------------------------------------------

            date=self._clock_xml(
                "941,32",
                "300,55",
                16,
                "%a.%d.%m",
                color=self.COLOR_DATE
            ),

            main=self._main_widgets(
                False,
                winddir_top
            ),

            colorbuttons=self._color_buttons_xml(False)
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

    def _set_day(self, day, data):

        names = (
            "smallday2",
            "maxtemp2",
            "minitemp2",
            "weertype2"
        )

        widgets = [
            "{}{}".format(x, day)
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
                self[name].text = ""

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

        try:

            self[
                "bigWeerIcon1{}".format(day)
            ].show()

            self[
                "bigDirIcon1{}".format(day)
            ].show()

        except Exception:
            pass

        # ------------------------------------------------------------
        # DATUM
        # ------------------------------------------------------------

        info1 = ""

        if data.get("date"):

            try:

                date = str(
                    data["date"]
                ).split("T")[0]

                unix = time.mktime(
                    datetime.datetime(
                        int(date[:4]),
                        int(date[5:7]),
                        int(date[8:10])
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
                    "[speedy_TheWeather] Datum Fehler:",
                    e
                )

        # ------------------------------------------------------------
        # TEMPERATUREN
        # ------------------------------------------------------------

        mintemp = data.get("mintemp")

        if mintemp is None:
            mintemp = data.get(
                "mintemperature"
            )

        maxtemp = data.get("maxtemp")

        if maxtemp is None:
            maxtemp = data.get(
                "maxtemperature"
            )

        info2 = ""
        info3 = ""

        if mintemp is not None:

            try:
                info2 = "{:.0f}\xb0".format(float(mintemp))
            except (TypeError, ValueError):
                info2 = safeStr(mintemp) + "\xb0"

        if maxtemp is not None:

            try:
                info3 = "{:.0f}\xb0".format(float(maxtemp))
            except (TypeError, ValueError):
                info3 = safeStr(maxtemp) + "\xb0"

        # ------------------------------------------------------------
        # ANZEIGEN
        # ------------------------------------------------------------

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
                data.get("iconcode") or "na"
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

        # ------------------------------------------------------------
        # OBERER WINDPFEIL
        # ------------------------------------------------------------

        winddir_top = (
            self._wind(data[0])
            if data
            else "na"
        )

        # ------------------------------------------------------------
        # TEMPERATURBILD
        # ------------------------------------------------------------

        tempicon = self._temp_picture(data)

        # ------------------------------------------------------------
        # SKIN
        # ------------------------------------------------------------

        self.skin = self._build_skin(
            data,
            winddir_top,
            tempicon
        )

        # ------------------------------------------------------------
        # DATUMSFORMAT
        # ------------------------------------------------------------

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
                e
            )

        # ------------------------------------------------------------
        # ALLGEMEINE WIDGETS
        # ------------------------------------------------------------

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

        # ------------------------------------------------------------
        # HINTERGRUND
        # ------------------------------------------------------------

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
                "standaard achtergrond:",
                e
            )

            self.picload = None

        # ------------------------------------------------------------
        # STUNDEN
        # ------------------------------------------------------------

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

        # ------------------------------------------------------------
        # SONNENAUFGANG / SONNENUNTERGANG
        # ------------------------------------------------------------

        sunrise, sunset = self._sun(data)

        self._label(
            "sunriselab",
            "{} - {}".format(
                sunrise,
                sunset
            )
        )

        # ------------------------------------------------------------
        # 7 TAGE
        # ------------------------------------------------------------

        for day in range(7):

            self._set_day(
                day,
                self._day(data, day)
            )
        # ------------------------------------------------------------
        # FARBTASTEN-BESCHRIFTUNGEN
        # ------------------------------------------------------------

        self["key_red"] = StaticText(_("Back"))
        self["key_green"] = StaticText(_("Hours"))
        self["key_yellow"] = StaticText(_("Radar"))
        self["key_blue"] = StaticText(_("Compare Two Locations"))
        # ------------------------------------------------------------
        # ACTIONMAP
        # ------------------------------------------------------------

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

        # ------------------------------------------------------------
        # STARTANZEIGE
        # ------------------------------------------------------------

        self.updateFrameselect()

        # ------------------------------------------------------------
        # TIMER
        # ------------------------------------------------------------

        self.alertFixTimer = eTimer()

        self._alertFixTimer_conn = safeTimerCallback(
            self.alertFixTimer,
            self.updateFrameselect
        )

        self.alertFixTimer.start(
            200,
            True
        )

    def getSlotHours(self, day):
        global weatherData
        dataDagen = weatherData["days"]
        dataUrr = dataDagen[day]["hours"]
        result = []
        datacount = 0
        for data in dataUrr:
            try:
                hour = int(data.get("hour"))
            except (TypeError, ValueError):
                continue
            if hour >= 1 and self.hourStep > 0 and ((hour - 1) % self.hourStep) == 0:
                if datacount < 8:
                    result.append(data)
                    datacount += 1
        return result

    def toggleHourStep(self):
        if self.hourStep == 1:
            self.hourStep = 2
        elif self.hourStep == 2:
            self.hourStep = 3
        else:
            self.hourStep = 1
        self.updateFrameselect()

    def updateFrameselect(self):
        if self.selected < 0:
            self.selected = 6
        elif self.selected > 6:
            self.selected = 0

        # ---------------------------------------------------------
        # Gelben Punkt unter dem ausgewählten Tag verschieben
        # ---------------------------------------------------------
        if sz_w > 1800:
            self["yellowdot"].moveTo(275 + (248 * self.selected), 463, 2)
        else:
            self["yellowdot"].moveTo(184 + (165 * self.selected), 307, 2)

        self["yellowdot"].startMoving()

        global weatherData
        dataDagen = weatherData["days"]

        # ---------------------------------------------------------
        # Sicherheit: Daten vorhanden?
        # ---------------------------------------------------------
        if not dataDagen:
            return

        # ---------------------------------------------------------
        # Oberer Bereich
        # Die Anzeige oben bleibt weiterhin auf Tag 0 / aktuelle
        # Wetterstunde bezogen, wie im bisherigen Code.
        # ---------------------------------------------------------
        temptext = "na"

        try:
            if dataDagen[self.selected + 0].get("temperature"):
                temptext = dataDagen[self.selected + 0]["temperature"]
        except Exception:
            pass

        try:
            dataPerUur = weatherData["days"][0]["hours"]
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
                        str("%.1f" % dataPerUur[0]["temperature"])
                    )
                )

                self["GevoelsTemp1"].setText(
                    _("Feels Like: ")
                    + str("%.1f" % dataPerUur[0]["feeltemperature"])
                    + "\xb0C"
                )

                self["winddir1"].setText(
                    _("Wind direction: ")
                    + str(winddirtext(dataPerUur[0]["winddirection"]))
                )

                self["bigweathertype1"].setText(
                    icontotext(str(dataPerUur[0]["iconcode"]))
                )
        except Exception:
            pass

        # ---------------------------------------------------------
        # Wetterwarnung
        # ---------------------------------------------------------
        try:
            alertKleur, alertTekst = localWeatherAlert(dataDagen[0])
        except Exception as e:
            alertKleur, alertTekst = "", ""
            print(
                "updateFrameselect: fout bij bepalen weeralarm:",
                e
            )

        if alertTekst:
            kleurwaarde = {
                "yellow": gRGB(0xf2c200),
                "orange": gRGB(0xff8c00),
                "red":    gRGB(0xe02020),
                "blue":   gRGB(0x40a0ff),
            }.get(alertKleur, gRGB(0xffffff))

            self["weatheralert1"].setText(alertTekst)

            try:
                if self["weatheralert1"].instance is not None:
                    self["weatheralert1"].instance.setForegroundColor(
                        kleurwaarde
                    )
            except Exception as e:
                print(
                    "updateFrameselect: fout bij instellen "
                    "weeralarm-kleur:",
                    e
                )

            try:
                if sz_w > 1800:
                    iconpad = (
                        "/usr/lib/enigma2/python/Plugins/Extensions/"
                        "speedy_TheWeather/"
                        + SHARED_PACK
                        + "/alert/alert_"
                        + alertKleur
                        + ".png"
                    )
                else:
                    iconpad = (
                        "/usr/lib/enigma2/python/Plugins/Extensions/"
                        "speedy_TheWeather/"
                        + SHARED_PACK
                        + "/alert/alert_"
                        + alertKleur
                        + "_sd.png"
                    )

                if self["weatheralerticon1"].instance is not None:
                    self["weatheralerticon1"].instance.setPixmapFromFile(
                        iconpad
                    )
                    self["weatheralerticon1"].show()

            except Exception as e:
                print(
                    "updateFrameselect: fout bij laden alert-icoon:",
                    e
                )
                self["weatheralerticon1"].hide()

            self["weatheralertbg1"].show()

        else:
            self["weatheralert1"].setText("")
            self["weatheralerticon1"].hide()
            self["weatheralertbg1"].hide()

        # ---------------------------------------------------------
        # Werte des ausgewählten Tages
        # ---------------------------------------------------------
        feeltext = "na"

        try:
            if dataDagen[0].get("feeltemperature"):
                feeltext = dataDagen[0]["feeltemperature"]
        except Exception:
            pass

        windtext = "na"

        try:
            if dataDagen[0].get("winddirection"):
                windtext = dataDagen[0]["winddirection"]
        except Exception:
            pass

        typetext = "na"

        try:
            if dataDagen[0].get("iconcode"):
                typetext = dataDagen[0]["iconcode"]
        except Exception:
            pass

        # ---------------------------------------------------------
        # WICHTIG:
        # Alle großen Tages-Wettericons zuerst verstecken.
        #
        # bigWeerIcon10 ... bigWeerIcon16 liegen absichtlich
        # auf derselben Position. Es darf deshalb immer nur
        # EIN Icon sichtbar sein.
        # ---------------------------------------------------------
        for day in range(0, 7):
            try:
                self["bigWeerIcon1" + str(day)].hide()
            except Exception:
                pass

            try:
                self["bigDirIcon1" + str(day)].hide()
            except Exception:
                pass

        # ---------------------------------------------------------
        # Nur das große Wettericon des ausgewählten Tages anzeigen
        # ---------------------------------------------------------
        try:
            self["bigWeerIcon1" + str(self.selected)].show()
        except Exception:
            pass

        try:
            self["bigDirIcon1" + str(self.selected)].show()
        except Exception:
            pass

        # ---------------------------------------------------------
        # Stunden des ausgewählten Tages
        # ---------------------------------------------------------
        try:
            dataPerUur = weatherData["days"][self.selected]["hours"]
        except Exception:
            dataPerUur = []

        slotHours = self.getSlotHours(self.selected)

        # ---------------------------------------------------------
        # 8 Stundenfelder aktualisieren
        # ---------------------------------------------------------
        for perUurUpdate in range(0, 8):

            # -----------------------------------------------------
            # Alle Tages-Icons für diesen Stundenplatz verstecken
            # -----------------------------------------------------
            for day in range(0, 7):
                try:
                    self[
                        "dayIcon"
                        + str(day)
                        + str(perUurUpdate)
                    ].hide()
                except Exception:
                    pass

            # -----------------------------------------------------
            # Stundenfeld und Zusatzicons verstecken
            # -----------------------------------------------------
            try:
                self["vlakuur" + str(perUurUpdate)].hide()
            except Exception:
                pass

            try:
                self["sunicon" + str(perUurUpdate)].hide()
            except Exception:
                pass

            try:
                self["rainicon" + str(perUurUpdate)].hide()
            except Exception:
                pass

            try:
                self["rhicon" + str(perUurUpdate)].hide()
            except Exception:
                pass

            try:
                self["windicon" + str(perUurUpdate)].hide()
            except Exception:
                pass

            # -----------------------------------------------------
            # Prüfen, ob für diesen Slot Daten vorhanden sind
            # -----------------------------------------------------
            slotHasData = (
                perUurUpdate < len(slotHours)
            )

            if slotHasData:

                # -------------------------------------------------
                # Icon des ausgewählten Tages anzeigen
                # -------------------------------------------------
                try:
                    self[
                        "dayIcon"
                        + str(self.selected)
                        + str(perUurUpdate)
                    ].show()
                except Exception:
                    pass

                # -------------------------------------------------
                # Stundenfeld anzeigen
                # -------------------------------------------------
                try:
                    self[
                        "vlakuur"
                        + str(perUurUpdate)
                    ].show()
                except Exception:
                    pass

                try:
                    self[
                        "sunicon"
                        + str(perUurUpdate)
                    ].show()
                except Exception:
                    pass

                # -------------------------------------------------
                # Wettericon laden
                # -------------------------------------------------
                try:
                    iconpath = (
                        "/usr/lib/enigma2/python/Plugins/Extensions/"
                        "speedy_TheWeather/"
                        + icoonpath
                        + "/iconhd/"
                        + str(
                            slotHours[perUurUpdate]["iconcode"]
                        )
                        + ".png"
                    )

                    self[
                        "dayIcon"
                        + str(self.selected)
                        + str(perUurUpdate)
                    ].instance.setPixmap(
                        _load_icon_cached(iconpath)
                    )

                except Exception:
                    pass

                # -------------------------------------------------
                # Regen / Luftfeuchtigkeit / Wind anzeigen
                # -------------------------------------------------
                try:
                    self[
                        "rainicon"
                        + str(perUurUpdate)
                    ].show()
                except Exception:
                    pass

                try:
                    self[
                        "rhicon"
                        + str(perUurUpdate)
                    ].show()
                except Exception:
                    pass

                try:
                    self[
                        "windicon"
                        + str(perUurUpdate)
                    ].show()
                except Exception:
                    pass

            # -----------------------------------------------------
            # Texte der Stundenfelder
            # -----------------------------------------------------
            try:
                if slotHasData:

                    entry = slotHours[perUurUpdate]

                    self[
                        "dayhour3"
                        + str(perUurUpdate)
                    ].setText(
                        str(entry["hour"]) + _("h")
                    )

                    self[
                        "daytemp3"
                        + str(perUurUpdate)
                    ].setText(
                        '{:>4}'.format(
                            str(
                                "%.0f"
                                % entry["temperature"]
                            )
                            + "\xb0C"
                        )
                    )

                    # Schreibweise des ursprünglichen Codes beibehalten
                    try:
                        precipitation = entry["precipation"]
                    except Exception:
                        precipitation = entry["precipitation"]

                    self[
                        "daypercent3"
                        + str(perUurUpdate)
                    ].setText(
                        str(precipitation) + "%"
                    )

                    self[
                        "dayspeed3"
                        + str(perUurUpdate)
                    ].setText(
                        format_windspeed(
                            entry.get("windspeed")
                        )
                    )

                    self[
                        "sunpercent3"
                        + str(perUurUpdate)
                    ].setText(
                        str(entry["sunshine"]) + "%"
                    )

                    self[
                        "hrdayper3"
                        + str(perUurUpdate)
                    ].setText(
                        str(entry["humidity"]) + "%"
                    )

                else:
                    self[
                        "dayhour3"
                        + str(perUurUpdate)
                    ].setText("")

                    self[
                        "daytemp3"
                        + str(perUurUpdate)
                    ].setText("")

                    self[
                        "daypercent3"
                        + str(perUurUpdate)
                    ].setText("")

                    self[
                        "dayspeed3"
                        + str(perUurUpdate)
                    ].setText("")

                    self[
                        "sunpercent3"
                        + str(perUurUpdate)
                    ].setText("")

                    self[
                        "hrdayper3"
                        + str(perUurUpdate)
                    ].setText("")

            except Exception:

                # -------------------------------------------------
                # Fallback für unterschiedliche API-Schreibweisen
                # -------------------------------------------------
                try:
                    if slotHasData:

                        entry = slotHours[perUurUpdate]

                        self[
                            "dayhour3"
                            + str(perUurUpdate)
                        ].setText(
                            str(entry["hour"]) + _("h")
                        )

                        self[
                            "daytemp3"
                            + str(perUurUpdate)
                        ].setText(
                            '{:>4}'.format(
                                str(
                                    "%.0f"
                                    % entry["temperature"]
                                )
                                + "\xb0C"
                            )
                        )

                        self[
                            "daypercent3"
                            + str(perUurUpdate)
                        ].setText(
                            str(
                                entry["precipitation"]
                            ) + "%"
                        )

                        self[
                            "dayspeed3"
                            + str(perUurUpdate)
                        ].setText(
                            format_windspeed(
                                entry.get("windspeed")
                            )
                        )

                        self[
                            "sunpercent3"
                            + str(perUurUpdate)
                        ].setText(
                            str(entry["sunshine"]) + "%"
                        )

                        self[
                            "hrdayper3"
                            + str(perUurUpdate)
                        ].setText(
                            str(entry["humidity"]) + "%"
                        )

                    else:
                        self[
                            "dayhour3"
                            + str(perUurUpdate)
                        ].setText("")

                        self[
                            "daytemp3"
                            + str(perUurUpdate)
                        ].setText("")

                        self[
                            "daypercent3"
                            + str(perUurUpdate)
                        ].setText("")

                        self[
                            "dayspeed3"
                            + str(perUurUpdate)
                        ].setText("")

                        self[
                            "sunpercent3"
                            + str(perUurUpdate)
                        ].setText("")

                        self[
                            "hrdayper3"
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

                    try:
                        self[
                            "sunicon"
                            + str(perUurUpdate)
                        ].hide()
                    except Exception:
                        pass

                    try:
                        self[
                            "rainicon"
                            + str(perUurUpdate)
                        ].hide()
                    except Exception:
                        pass

                    try:
                        self[
                            "rhicon"
                            + str(perUurUpdate)
                        ].hide()
                    except Exception:
                        pass

                    try:
                        self[
                            "windicon"
                            + str(perUurUpdate)
                        ].hide()
                    except Exception:
                        pass

    def KeyMenu(self):
        self.session.open(localcityscreen)

    def left(self):
        self.selected -= 1
        self.updateFrameselect()

    def right(self):
        self.selected += 1
        self.updateFrameselect()

    def fourteendays(self):
        self.session.open(fourteen)

    import os

    def loadBackground(self):
        global backgroundpath
        if not hasattr(self, 'picload') or self.picload is None:
            return

        bg_folder = "/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/backgrounds"
        default_bg = "/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/" + SHARED_PACK + "/backgroundhd_2.png"

        bgfile = None
        if backgroundpath and os.path.isabs(backgroundpath) and os.path.exists(backgroundpath):
            bgfile = backgroundpath
        elif backgroundpath and os.path.exists(os.path.join(bg_folder, backgroundpath)):
            bgfile = os.path.join(bg_folder, backgroundpath)
        elif os.path.exists(default_bg):
            bgfile = default_bg

        if not bgfile or not os.path.isfile(bgfile):
            return

        try:
            # Stoppt laufende Dekodierungen (verhindert C++ Null-Pointer Crash)
            self.picload.startDecode("") 
            
            if sz_w > 1800:
                self.picload.setPara([1920, 1080, 1, 1, False, 1, "#ff000000"])
            else:
                self.picload.setPara([1280, 720, 1, 1, False, 1, "#ff000000"])

            self.picload.startDecode(bgfile)
        except Exception as e:
            print("[speedy_TheWeather] loadBackground Fehler:", e)

    def bgPictureLoaded(self, picInfo=None):
        if not hasattr(self, 'picload') or self.picload is None:
            return
        
        # Prüft ob das Widget und die C++ Instanz existieren
        if "bgpic" not in self or self["bgpic"] is None or self["bgpic"].instance is None:
            return

        try:
            ptr = self.picload.getData()
            if ptr is not None:
                self["bgpic"].instance.setPixmap(ptr)
                self["bgpic"].show()
        except Exception as e:
            print("[speedy_TheWeather] bgPictureLoaded Fehler:", e)

    def openRadar(self):
        global lockaaleStad

        print(
            "[speedy_TheWeather] openRadar lockaaleStad=%r"
            % lockaaleStad
        )

        lat, lon = getCoordsFromEntry(lockaaleStad)

        if lat is not None and lon is not None:

            parts = safeStr(lockaaleStad).split("|")
            location_name = parts[0].strip() if parts else ""

            print(
                "[speedy_TheWeather] radar location_name=%r"
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
    
    #Temporary button for the twolocations
    def openTwoLocations(self):
        self.session.open(twolocations)

    def openSetup(self):
        self.session.openWithCallback(self.setupClosed, speedy_TheWeatherSetup)
    
    def setupClosed(self, changed=False):
        if changed:
            self.close()
            self.session.open(sevendays)
    
    def backgroundPickerCallback(self, changed=None):
        
        if changed:
            self.loadBackground()

    def exit(self):
        ClosePlugin()

    def cancel(self):
        ClosePlugin()

class fourteen(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        AddNewScreen(self)
        self.onClose.append(lambda: RemoveScreen(self))
        global weatherData
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
                    <screen name="fourteen" flags="wfNoBorder" position="center,center" size="1920,1080" title="fourteen">
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
                    <screen name="fourteen" flags="wfNoBorder" position="center,center" size="1280,720" title="fourteen">
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

        def worker():
            try:
                url = "https://location.buienradar.nl/1.1/location/search?query=%s" % quote_plus(query)
                results = _http_json(url, timeout=12)
                if req_id == self._citySearchRequestId:
                    self._citySearchResult = results or []
            except Exception as e:
                if req_id == self._citySearchRequestId:
                    self._citySearchError = e

        self._citySearchThread = threading.Thread(target=worker)
        self._citySearchThread.daemon = True
        self._citySearchThread.start()
        self._citySearchTimer.start(100, True)

    def _pollCitySearch(self):
        if self._citySearchResult is None and self._citySearchError is None:
            if self._citySearchThread is not None and self._citySearchThread.is_alive():
                self._citySearchTimer.start(100, True)
                return

        result = self._citySearchResult
        error = self._citySearchError
        self._citySearchResult = None
        self._citySearchError = None
        self._citySearchBusy = False

        if error is not None:
            print("[speedy_TheWeather] city search error: %s" % error)
            self.session.open(
                MessageBox,
                _("No matching cities found."),
                MessageBox.TYPE_INFO
            )
            return

        if not result:
            self.session.open(
                MessageBox,
                _("No matching cities found."),
                MessageBox.TYPE_INFO
            )
            return

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
    <screen name="speedy_TheWeatherSetup" position="410,220" size="1100,640" title="speedy_TheWeather Settings">
        <widget name="config" position="4,4" size="1070,550" scrollbarMode="showOnDemand" itemHeight="45" itemTextSelectedColor="#ffffff" itemTextUnselectedColor="#ffffff" font="Regular; 25" />

        <!-- Roter Button -->
        <ePixmap pixmap="skin_default/buttons/red.png" position="11,593" size="20,40" alphatest="on" zPosition="1" />
        <widget name="key_red" position="36,593" size="240,40" zPosition="2" transparent="1" font="Regular;20" halign="center" valign="center" />

        <!-- Grüner Button -->
        <ePixmap pixmap="skin_default/buttons/green.png" position="282,593" size="20,40" alphatest="on" zPosition="1" />
        <widget name="key_green" position="308,593" size="240,40" zPosition="2" transparent="1" font="Regular;20" halign="center" valign="center" foregroundColor="green" />

        <!-- Blauer Button -->
        <ePixmap pixmap="skin_default/buttons/blue.png" position="825,593" size="20,40" alphatest="on" zPosition="1" />
        <widget name="key_blue" position="851,593" size="240,40" zPosition="2" transparent="1" font="Regular;20" halign="center" valign="center" foregroundColor="blue" />

        <!-- Gelber Button -->
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="554,593" size="20,40" alphatest="on" zPosition="1" />
        <widget name="key_yellow" position="579,593" size="240,40" zPosition="2" transparent="1" font="Regular;20" halign="center" valign="center" foregroundColor="yellow" />
<widget name="Version" position="676,554" size="420,40" font="Regular;26" halign="center" valign="center" foregroundColor="red" transparent="1" backgroundColor="black" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("Save"))
        self["key_blue"] = Label(_("Show 2 locations"))
        self["key_yellow"] = Label(_("Appearance"))
        self["version"] = Label("speedy_TheWeather_v.%s" % VERSION)

        # Menüpunkt für die Update-Suche
        self.updateEntry = ConfigNothing()

        self.list = []

        self.list.append(
            getConfigListEntry(
                _("Wind speed:"),
                config.plugins.speedy_TheWeather.windunit
            )
        )

        self.list.append(
            getConfigListEntry(
                _("Date format:"),
                config.plugins.speedy_TheWeather.dateformat
            )
        )

        self.list.append(
            getConfigListEntry(
                _("Radar default zoom:"),
                config.plugins.speedy_TheWeather.defaultzoom
            )
        )

        self.list.append(
            getConfigListEntry(
                _("Performance:"),
                config.plugins.speedy_TheWeather.performance
            )
        )

        # Update-Suche
        self.list.append(
            getConfigListEntry(
                _("Search for update"),
                self.updateEntry
            )
        )

        ConfigListScreen.__init__(
            self,
            self.list,
            session=session
        )

        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions"],
            {
                "green": self.save,
                "red": self.keyCancel,
                "cancel": self.keyCancel,
                "save": self.save,
                "blue": self.openTwoLocations,
                "yellow": self.openAppearance,

                # OK auf "Search for update"
                "ok": self.checkUpdate,
            },
            -2
        )

 
    def checkUpdate(self):
        """
        Startet die Update-Prüfung nur dann,
        wenn der Menüpunkt "Search for update" ausgewählt ist.

        Die Prüfung läuft threadbasiert; die Rückgabe wird ausschließlich
        über eTimer im Enigma2-Mainthread verarbeitet.
        """

        current = self["config"].getCurrent()

        if not current:
            return

        if current[1] != self.updateEntry:
            return

        global _overlaySession, _updatePollTimer
        _overlaySession = self.session

        # Die globale Poll-Abfrage darf während des manuellen Checks nicht
        # dieselbe Queue parallel leeren.
        try:
            if _updatePollTimer is not None:
                _updatePollTimer.stop()
        except Exception:
            pass

        print("[speedy_TheWeather] Starting update check...")

        # Alten Timer sauber entfernen
        try:
            if hasattr(self, "_updateCheckTimer"):
                self._updateCheckTimer.stop()
        except Exception:
            pass

        # Hintergrundprüfung starten
        try:
            threading.Thread(
                target=_update_check_worker,
                name="speedy_TheWeather_ConfigUpdateCheck"
            ).start()
        except Exception as e:
            print(
                "[speedy_TheWeather] "
                "Could not start update thread: %s"
                % e
            )

            self.session.open(
                MessageBox,
                _("Update check failed."),
                MessageBox.TYPE_ERROR
            )
            return

        # eTimer für Queue-Abfrage erzeugen
        try:
            self._updateCheckTimer = eTimer()

            safeTimerCallback(
                self._updateCheckTimer,
                self.checkUpdateQueue
            )

            # Nach 100 ms erstmals prüfen
            self._updateCheckTimer.start(
                100,
                True
            )

            print(
                "[speedy_TheWeather] "
                "Update result timer started."
            )

        except Exception as e:

            self._updateCheckTimer = None

            print(
                "[speedy_TheWeather] "
                "Could not start update result timer: %s"
                % e
            )

            self.session.open(
                MessageBox,
                _("Update check failed."),
                MessageBox.TYPE_ERROR
            )


    def checkUpdateQueue(self):
        """
        Prüft die Update-Queue.

        Diese Funktion läuft immer im Enigma2-Mainthread
        über eTimer.
        """

        try:
            result = _updateQueue.get_nowait()

        except queue.Empty:

            # Noch kein Ergebnis vorhanden.
            # eTimer erneut in 100 ms starten.

            try:
                if hasattr(self, "_updateCheckTimer") and \
                   self._updateCheckTimer is not None:

                    self._updateCheckTimer.start(
                        100,
                        True
                    )

            except Exception as e:

                print(
                    "[speedy_TheWeather] "
                    "Could not restart update timer: %s"
                    % e
                )

            return

        except Exception as e:

            print(
                "[speedy_TheWeather] "
                "Update queue error: %s"
                % e
            )

            try:
                if hasattr(self, "_updateCheckTimer") and \
                   self._updateCheckTimer is not None:

                    self._updateCheckTimer.stop()

            except Exception:
                pass

            self.session.open(
                MessageBox,
                _("Update check failed."),
                MessageBox.TYPE_ERROR
            )

            return


        # -------------------------------------------------
        # Ergebnis vorhanden
        # -------------------------------------------------

        try:
            if hasattr(self, "_updateCheckTimer") and \
               self._updateCheckTimer is not None:

                self._updateCheckTimer.stop()

        except Exception:
            pass


        result_type, data = result


        # -------------------------------------------------
        # FEHLER
        # -------------------------------------------------

        if result_type == "error":

            self.session.open(
                MessageBox,
                data,
                MessageBox.TYPE_ERROR
            )

            return


        # -------------------------------------------------
        # KEIN UPDATE
        # -------------------------------------------------

        if result_type == "current":

            remote_version = data.get("version", "")

            self.session.open(
                MessageBox,
                _(
                    "The plugin is already up to date.\n\n"
                    "Version: %s"
                ) % remote_version,
                MessageBox.TYPE_INFO
            )

            return


        # -------------------------------------------------
        # UPDATE VERFÜGBAR
        # -------------------------------------------------

        if result_type == "available":

            # Einheitliche Anzeige für automatischen und manuellen Check.
            # Dadurch stimmt der msgid exakt mit der PO-Datei überein.
            globals()["_updateInfo"] = data
            _update_show_message(data)
            return


        # -------------------------------------------------
        # INSTALLATION
        # -------------------------------------------------

        if result_type == "installing":

            _update_show_installing()

            return


        # -------------------------------------------------
        # INSTALLIERT
        # -------------------------------------------------

        if result_type == "installed":

            _update_install_finished()

            return


        # -------------------------------------------------
        # INSTALLATIONSFEHLER
        # -------------------------------------------------

        if result_type == "install_error":

            _update_install_error()

            return


        print(
            "[speedy_TheWeather] "
            "Unknown update result: %s"
            % result_type
        )


    def __del__(self):
        """
        Timer beim Zerstören des Config-Screens stoppen.
        """

        try:
            if hasattr(self, "_updateCheckTimer") and \
               self._updateCheckTimer is not None:

                self._updateCheckTimer.stop()

        except Exception:
            pass

        try:
            ConfigListScreen.__del__(self)
        except Exception:
            pass

    def openTwoLocations(self):
        self.session.open(twolocations)

    def openAppearance(self):
        self.session.open(infoscreen)

    def save(self):
        for x in self["config"].list:
            x[1].save()

        configfile.save()
        self.close(True)

    def keyCancel(self):
        for x in self["config"].list:
            x[1].cancel()

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
                    <screen name="startScreen" flags="wfNoBorder" position="center,center" size="1920,1080">
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
        Screen.__init__(self, session)
        AddNewScreen(self)
        self.onClose.append(lambda: RemoveScreen(self))

        self.compareCity = ""
        if os.path.exists(self.COMPARE_CFG):
            try:
                with open(self.COMPARE_CFG) as f:
                    val = f.read().strip()
                    if val:
                        self.compareCity = val
            except Exception:
                pass

        if sz_w > 1800:
            skin = """
                <screen name="twolocations" flags="wfNoBorder" position="center,center" size="1920,1080">
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png" position="0,112" size="1920,3" zPosition="1"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png" position="0,1010" size="1920,3" zPosition="1"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline3.png" position="958,112" size="3,868" zPosition="1"/>
                <widget source="global.CurrentTime" render="Label" position="1634,35" size="225,45" transparent="1" zPosition="3" font="Regular;36" foregroundColor="#00ff0000" backgroundColor="#00ff0000" valign="center" halign="right"><convert type="ClockToText">Format:%-H:%M:%S</convert></widget>
                <widget source="global.CurrentTime" render="Label" position="1409,74" size="450,37" transparent="1" zPosition="3" font="Regular;24" foregroundColor="#00ffff00" backgroundColor="#0000ff00" valign="center" halign="right"><convert type="ClockToText">Format:%a %d/%m/%y</convert></widget>
                <widget name="loc1name"     position="40,125"   size="880,72"  zPosition="3" font="Regular;58" foregroundColor="#00ffff00" backgroundColor="#00202020" halign="center" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1icon"     position="140,215"  size="160,160" zPosition="3" alphatest="blend"/>
                <widget name="loc1maxtemp"  position="320,215"  size="380,95"  zPosition="3" font="Regular;78" foregroundColor="#00ff0000" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1mintemp"  position="320,310"  size="380,60"  zPosition="3" font="Regular;48" foregroundColor="#000000ff" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1weertype" position="320,400"  size="600,56"  zPosition="3" font="Regular;44" foregroundColor="#000000ff" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1feel"     position="320,468"  size="600,52"  zPosition="3" font="Regular;40" foregroundColor="#000000ff" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1wind"     position="320,530"  size="600,52"  zPosition="3" font="Regular;40" foregroundColor="#000000ff" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1rain"     position="320,592"  size="600,52"  zPosition="3" font="Regular;40" foregroundColor="#000000ff" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1sun"      position="320,654"  size="600,52"  zPosition="3" font="Regular;40" foregroundColor="#000000ff" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1alert"    position="320,720"  size="808,68"  zPosition="3" font="Regular;48" foregroundColor="#000000ff" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1alerticon" position="216,724"  size="64,64"   zPosition="4" alphatest="blend" transparent="1"/>
                <widget name="loc2name"     position="1000,125" size="880,72"  zPosition="3" font="Regular;58" foregroundColor="#000000ff" backgroundColor="#00202020" halign="center" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2icon"     position="1100,215" size="160,160" zPosition="3" alphatest="blend"/>
                <widget name="loc2maxtemp"  position="1280,215" size="380,95"  zPosition="3" font="Regular;78" foregroundColor="#0000ff00" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2mintemp"  position="1280,310" size="380,60"  zPosition="3" font="Regular;48" foregroundColor="#0000ff00" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2weertype" position="1280,400" size="600,56"  zPosition="3" font="Regular;44" foregroundColor="#0000ff00" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2feel"     position="1280,468" size="600,52"  zPosition="3" font="Regular;40" foregroundColor="#0000ff00" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2wind"     position="1280,530" size="600,52"  zPosition="3" font="Regular;40" foregroundColor="#0000ff00" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2rain"     position="1280,592" size="600,52"  zPosition="3" font="Regular;40" foregroundColor="#0000ff00" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2sun"      position="1280,654" size="600,52"  zPosition="3" font="Regular;40" foregroundColor="#0000ff00" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2alert"    position="1280,720" size="808,68"  zPosition="3" font="Regular;48" foregroundColor="#0000ff00" backgroundColor="#00202020" halign="left" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2alerticon" position="1176,724" size="64,64"  zPosition="4" alphatest="blend" transparent="1"/>
                <widget name="statusmsg"    position="40,808"   size="1840,56" zPosition="3" font="Regular;40" foregroundColor="#00ffff00" backgroundColor="#00202020" halign="center" valign="center" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red34.png"    position="192,1022"  size="34,34" alphatest="blend"/>
                <widget name="key_red" position="242,1015"  size="370,48" zPosition="3" font="Regular;40" foregroundColor="#00ff0000" backgroundColor="#00202020" halign="left" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/yellow34.png" position="628,1022"  size="34,34" alphatest="blend"/>
                <widget name="comp" position="85,45" size="1085,55" valign="center" halign="left" zPosition="1" font="Regular;36" foregroundColor="#000000ff" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="key_yellow" position="678,1015"  size="600,48" zPosition="3" font="Regular;40" foregroundColor="#00ffff00" backgroundColor="#00202020" halign="left" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                </screen>"""
        else:
            skin = """
                <screen name="twolocations" flags="wfNoBorder" position="center,center" size="1280,720">
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline2.png" position="0,88"   size="1280,2" zPosition="1"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/borders/smallline2.png" position="0,630" size="1280,2" zPosition="1"/>
                <widget source="global.CurrentTime" render="Label" position="1090,18" size="170,40" transparent="1" zPosition="3" font="Regular;30" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%-H:%M:%S</convert></widget>
                <widget source="global.CurrentTime" render="Label" position="940,52"  size="320,34" transparent="1" zPosition="3" font="Regular;20" foregroundColor="#00ffff00" backgroundColor="#00202020" valign="center" halign="right"><convert type="ClockToText">Format:%a %d/%m/%y</convert></widget>
                <widget name="loc1name"     position="244,95"    size="618,52"  zPosition="3" font="Regular;42" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1icon"     position="94,143"   size="130,130" scale="1" zPosition="3" alphatest="blend"/>
                <widget name="loc1maxtemp"  position="244,158"  size="470,80"  zPosition="3" font="Regular;72" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1mintemp"  position="244,238"  size="470,44"  zPosition="3" font="Regular;36" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1weertype" position="244,296"  size="474,44"  zPosition="3" font="Regular;34" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1feel"     position="244,348"  size="474,40"  zPosition="3" font="Regular;32" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1wind"     position="244,394"  size="474,40"  zPosition="3" font="Regular;32" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1rain"     position="244,440"  size="474,40"  zPosition="3" font="Regular;32" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1sun"      position="244,486"  size="474,40"  zPosition="3" font="Regular;32" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1alert"    position="244,538"  size="576,50"  zPosition="3" font="Regular;36" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc1alerticon" position="183,542"  size="42,42"   zPosition="4" alphatest="blend" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1"/>
                <widget name="loc2name"     position="842,95"   size="618,52"  zPosition="3" font="Regular;42" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2icon"     position="692,143"  size="130,130" scale="1" zPosition="3" alphatest="blend"/>
                <widget name="loc2maxtemp"  position="842,158"  size="470,80"  zPosition="3" font="Regular;72" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2mintemp"  position="842,238"  size="470,44"  zPosition="3" font="Regular;36" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2weertype" position="842,296"  size="474,44"  zPosition="3" font="Regular;34" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2feel"     position="842,348"  size="474,40"  zPosition="3" font="Regular;32" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2wind"     position="842,394"  size="474,40"  zPosition="3" font="Regular;32" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2rain"     position="842,440"  size="474,40"  zPosition="3" font="Regular;32" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2sun"      position="842,486"  size="474,40"  zPosition="3" font="Regular;32" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2alert"    position="842,538"  size="576,50"  zPosition="3" font="Regular;36" halign="left" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="loc2alerticon" position="781,542" size="42,42"   zPosition="4" alphatest="blend" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1"/>
                <widget name="statusmsg"    position="10,602"   size="1260,44" zPosition="3" font="Regular;30" halign="center" valign="center" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/red26.png" position="145,663" size="26,26" alphatest="blend"/>
                <widget name="key_red" position="185,663" size="220,32" zPosition="1" font="Regular;24" halign="left" foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <widget name="comp" position="57,30" size="723,37" valign="center" halign="left" zPosition="1" font="Regular;24"  foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/""" + SHARED_PACK + """/buttons/yellow26.png" position="695,663" size="26,26" alphatest="blend"/>
                <widget name="key_yellow" position="735,663" size="220,32" zPosition="1" font="Regular;24" halign="left"  foregroundColor="#00ffff00" backgroundColor="#00202020" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
                </screen>"""

        self.skin = skin.replace("Format:%a %d/%m/%y", getDateFormat())

        for n in ["loc1name","loc1maxtemp","loc1mintemp","loc1weertype","loc1feel","loc1wind","loc1rain","loc1sun","loc1alert",
                  "loc2name","loc2maxtemp","loc2mintemp","loc2weertype","loc2feel","loc2wind","loc2rain","loc2sun","loc2alert",
                  "statusmsg","key_red","key_yellow"]:
            self[n] = Label("")
        for n in ["loc1icon", "loc2icon", "loc1alerticon", "loc2alerticon"]:
            self[n] = Pixmap()

        self["actions"] = ActionMap(["WizardActions","MenuActions"], {"back": self.exit, "cancel": self.exit}, -1)
        self["ColorActions"] = HelpableActionMap(self, "ColorActions", {"red": self.exit, "yellow": self.changeCompareCity, "blue": self.exit}, -1)
        self["key_red"] = Label(_("Exit"))
        self["key_yellow"] = Label(_("Choose 2nd location"))
        self["comp"] = Label(_("Compare Locations"))

        self.fillLoc1()
        if self.compareCity:
            self.fillLoc2(self.compareCity)
        else:
            self._setText("loc2name", _("No 2nd location"))
            self._setText("statusmsg", _("Press YELLOW to choose a 2nd location."))

        self.iconFixTimer = eTimer()
        self._iconFixTimer_conn = safeTimerCallback(self.iconFixTimer, self.reloadIcons)
        self.iconFixTimer.start(300, True)

    def _setText(self, key, value):
        
        try:
            self[key].setText("" if value is None else str(value))
        except Exception as e:
            print("twolocations _setText fout op", key, ":", e)

    def _fillLocation(self, data, naam, prefix):
        
        try:
            dag = data["days"][0]
        except Exception:
            self._setText(prefix + "name", _("Data error"))
            return

        self._setText(prefix + "name", naam)

        try:
            curtemp = "%.1f\xb0C" % dag["hours"][0]["temperature"]
        except Exception:
            try:
                curtemp = "%.0f\xb0C" % dag["maxtemperature"]
            except Exception:
                curtemp = "--"
        self._setText(prefix + "maxtemp", curtemp)

        try:
            mintemp = "%.0f\xb0 / %.0f\xb0" % (dag["mintemperature"], dag["maxtemperature"])
        except Exception:
            mintemp = "--"
        self._setText(prefix + "mintemp", mintemp)

        try:
            self._setText(prefix + "weertype", icontotext(dag.get("iconcode", "")))
        except Exception:
            pass

        try:
            hours = dag.get("hours", [])
            if hours and "feeltemperature" in hours[0]:
                feeltemp = hours[0]["feeltemperature"]
            else:
                feeltemp = dag.get("feeltemperature", dag.get("maxtemperature", "--"))
            self._setText(prefix + "feel", _("Feels Like: ") + "%.1f\xb0C" % float(feeltemp))
        except Exception:
            pass

        try:
            ws = dag.get("windspeed", 0)
            self._setText(prefix + "wind", _("Wind: ") + windspeed_with_beaufort(ws))
        except Exception:
            pass

        try:
            rainmm = dag.get("precipitationmm", 0)
            self._setText(prefix + "rain", _("Rain: ") + "%.1f mm" % float(rainmm))
        except Exception:
            pass

        try:
            sunrise = (str(dag.get("sunrise", "")).split("T")[1])[:-3]
            sunset  = (str(dag.get("sunset",  "")).split("T")[1])[:-3]
            self._setText(prefix + "sun", _("Sun: ") + sunrise + "  -  " + sunset)
        except Exception:
            self._setText(prefix + "sun", "")

        try:
            alertkleur, alerttekst = localWeatherAlert(dag)
            if alerttekst:
                kleurwaarde = {"yellow": gRGB(0xf2c200), "orange": gRGB(0xff8c00),
                               "red": gRGB(0xe02020), "blue": gRGB(0x40a0ff)}.get(alertkleur, gRGB(0xffffff))
                self._setText(prefix + "alert", alerttekst)
                try:
                    if self[prefix + "alert"].instance is not None:
                        self[prefix + "alert"].instance.setForegroundColor(kleurwaarde)
                except Exception:
                    pass
                try:
                    if sz_w > 1800:
                        alerticon = "/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/" + SHARED_PACK + "/alert/alert_" + alertkleur + ".png"
                    else:
                        alerticon = "/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/" + SHARED_PACK + "/alert/alert_" + alertkleur + "_sd.png"
                    if self[prefix + "alerticon"].instance is not None:
                        self[prefix + "alerticon"].instance.setPixmapFromFile(alerticon)
                        self[prefix + "alerticon"].show()
                except Exception:
                    self[prefix + "alerticon"].hide()
            else:
                self._setText(prefix + "alert", "")
                self[prefix + "alerticon"].hide()
        except Exception:
            pass

        try:
            iconcode = dag.get("iconcode", "")
            if sz_w > 1800:
                iconbestand = "/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/" + icoonpath + "/iconbighd/" + str(iconcode) + ".png"
            else:
                iconbestand = "/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather/" + icoonpath + "/iconbighd/" + str(iconcode) + ".png"
            try:
                if self[prefix + "icon"].instance is not None:
                    self[prefix + "icon"].instance.setPixmapFromFile(iconbestand)
            except Exception:
                pass
        except Exception:
            pass

    def reloadIcons(self):
        
        self.fillLoc1()
        if self.compareCity:
            self.fillLoc2(self.compareCity)

    def fillLoc1(self):
        global weatherData, citynamedisplay
        try:
            self._fillLocation(weatherData, citynamedisplay, "loc1")
        except Exception as e:
            print("twolocations fillLoc1 fout:", e)
            self._setText("loc1name", _("Error loading"))

    def fillLoc2(self, city):
        self._setText("statusmsg", _("Loading..."))
        try:
            data, naam = getLocWeerFor(city)
            if data and naam:
                self._fillLocation(data, naam, "loc2")
                self._setText("statusmsg", "")
            else:
                self._setText("loc2name", _("Not found"))
                self._setText("statusmsg", _("City not found. Press YELLOW to change."))
        except Exception as e:
            print("twolocations fillLoc2 fout:", e)
            self._setText("loc2name", _("Error loading"))
            self._setText("statusmsg", _("Error fetching data."))

    def changeCompareCity(self):
        global SavedLokaleWeer
        if not SavedLokaleWeer:
            self.session.open(MessageBox, _("No saved cities found.\nFirst add cities via the location screen."), MessageBox.TYPE_INFO)
            return
        self.session.openWithCallback(self.onCompareCityChosen, CityPickerScreen, SavedLokaleWeer)

    def onCompareCityChosen(self, stadcode=None):
        if not stadcode:
            return
        self.compareCity = stadcode
        try:
            with open(self.COMPARE_CFG, "w") as f:
                f.write(self.compareCity)
        except Exception as e:
            print("twolocations: opslaan 2e stad mislukt:", e)
        self.fillLoc2(self.compareCity)

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
    """Return conservative settings for older Enigma2 receivers."""
    try:
        mode = config.plugins.speedy_TheWeather.performance.value
    except Exception:
        mode = "auto"

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

    # Auto: 1280px and below is treated as low-end. This is only a
    # heuristic; users can explicitly select Normal if desired.
    try:
        width = int(getDesktop(0).size().width())
    except Exception:
        width = 1920

    # RAM is a better low-end signal than CPU model names, which vary
    # considerably between Enigma2 images. Keep this probe tiny and local.
    low_memory = False
    try:
        with open("/proc/meminfo", "r") as memfile:
            for line in memfile:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    low_memory = kb <= (256 * 1024)
                    break
    except Exception:
        pass

    if width <= 1280 or low_memory:
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

        _ensure_cache_dir()

        cache_path = _cache_file_for_url(
            url
        )

        with _TILE_CACHE_LOCK:

            try:

                stat = os.stat(
                    cache_path
                )

                if (
                    stat.st_size > 0
                    and
                    time.time()
                    - stat.st_mtime
                    <= _TILE_CACHE_TTL
                ):

                    # Cache direkt dekodieren statt Cache -> Temp-Datei zu kopieren.
                    # Das spart Flash-I/O und einen kompletten Dateikopiervorgang.
                    return cache_path

            except OSError:
                pass

        req = Request(
            url,
            data=None,
            headers={
                "User-Agent":
                    "speedy_TheWeather/4.0",
                "Accept":
                    "image/png,image/*,*/*"
            }
        )

        response = None

        tmp_path = (
            path
            + ".part.%s"
            % threading.current_thread().ident
        )

        try:

            response = urlopen(
                req,
                timeout=12
            )

            data = response.read()

            if not data:
                raise IOError(
                    "empty response"
                )

            with open(
                tmp_path,
                "wb"
            ) as f:

                f.write(data)

            try:

                os.replace(
                    tmp_path,
                    path
                )

            except AttributeError:

                os.rename(
                    tmp_path,
                    path
                )

            with _TILE_CACHE_LOCK:

                try:

                    shutil.copyfile(
                        path,
                        cache_path
                    )

                except OSError:
                    pass

            return path

        finally:

            if response is not None:

                try:
                    response.close()
                except Exception:
                    pass

            try:

                if os.path.exists(
                    tmp_path
                ):

                    os.remove(
                        tmp_path
                    )

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

            if (
                self._closed
                or
                req_id != self._fetchRequestId
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

        pool = self._radarDownloadPool
        if pool is None:
            for job in jobs:
                key, value = one(job)
                if isinstance(value, Exception):
                    raise value
                results[key] = value
            return results

        futures = [
            pool.submit(one, job)
            for job in jobs
        ]

        for future in futures:
            key, value = future.result()

            if isinstance(value, Exception):
                raise value

            results[key] = value

            if (
                self._closed
                or
                req_id != self._fetchRequestId
            ):
                return {}

        return results

    # =============================================================
    # FETCH
    # =============================================================

    def startFetch(self):

        if self._closed:
            return

        if self.fetchBusy:
            return

        self.fetchBusy = True

        self._fetchRequestId += 1

        req_id = self._fetchRequestId

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
                self._closed
                or
                req_id != self._fetchRequestId
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
                    self._closed
                    or
                    req_id != self._fetchRequestId
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
                    self._closed
                    or
                    req_id != self._fetchRequestId
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
                req_id == self._fetchRequestId
                and not self._closed
            ):

                self._radarError = e

    # =============================================================
    # POLL WORKER
    # =============================================================

    def _pollRadarWorker(self):

        if self._closed:
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
        # WICHTIG:
        # Poll-Timer stoppen, sobald Ergebnis/Fehler vorhanden ist.
        # Sonst läuft er während des Decoders weiter.
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
            # Dadurch bleibt die letzte gültige Radarzeit stehen.
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

        if (
            not result
            or
            result.get("reqId")
            != self._fetchRequestId
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

        if self._closed:
            return

        try:
            self._decodeTimer.stop()
        except Exception:
            pass

        self._decodeActive = True

        self._decodeQueue = deque()

        self._decodeBaseFiles = dict(
            result.get(
                "baseFiles",
                {}
            )
        )

        self._decodeFrameFiles = list(
            result.get(
                "frameFiles",
                []
            )
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
            result.get(
                "frameTimes",
                []
            )
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

        # ---------------------------------------------------------
        # Base zuerst
        # ---------------------------------------------------------

        for key, path in (
            self._decodeBaseFiles.items()
        ):

            self._decodeQueue.append(
                (
                    "base",
                    key,
                    path
                )
            )

        # ---------------------------------------------------------
        # Frame 0 direkt danach
        # ---------------------------------------------------------

        if self._decodeFrameFiles:

            for key, path in (
                self._decodeFrameFiles[0].items()
            ):

                self._decodeQueue.append(
                    (
                        "frame",
                        0,
                        key,
                        path
                    )
                )

        # ---------------------------------------------------------
        # Restliche Frames
        # ---------------------------------------------------------

        for frameIndex in range(
            1,
            len(
                self._decodeFrameFiles
            )
        ):

            for key, path in (
                self._decodeFrameFiles[
                    frameIndex
                ].items()
            ):

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

        if self._closed:
            return

        if not self._decodeActive:
            return

        if not self._decodeQueue:

            self._finishDecode()
            return

        item = self._decodeQueue.popleft()

        try:

            itemType = item[0]

            # =====================================================
            # BASE
            # =====================================================

            if itemType == "base":

                key = item[1]
                path = item[2]

                pix = None

                try:

                    pix = _load_cached_png(
                        path
                    )

                except Exception:
                    pix = None

                if pix is None:

                    try:

                        pix = loadPNG(
                            path
                        )

                    except Exception:
                        pix = None

                if pix is not None:

                    self.basePixmaps[
                        key
                    ] = pix

                    try:

                        widget = self[
                            "radarBase_%s_%s"
                            % (
                                key[0],
                                key[1]
                            )
                        ]

                        widget.instance.setPixmap(
                            pix
                        )

                        widget.show()

                    except Exception:
                        pass

            # =====================================================
            # RADAR FRAME
            # =====================================================

            elif itemType == "frame":

                frameIndex = item[1]
                key = item[2]
                path = item[3]

                pix = None

                try:

                    pix = _load_cached_png(
                        path
                    )

                except Exception:
                    pix = None

                if pix is None:

                    try:

                        if (
                            path
                            and
                            os.path.exists(
                                path
                            )
                        ):

                            pix = loadPNG(
                                path
                            )

                    except Exception:
                        pix = None

                if (
                    frameIndex
                    <
                    len(
                        self.framePixmaps
                    )
                ):

                    if pix is not None:

                        self.framePixmaps[
                            frameIndex
                        ][key] = pix

                    self._decodeRemaining[
                        frameIndex
                    ] -= 1

                    if (
                        self._decodeRemaining[
                            frameIndex
                        ]
                        <= 0
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

        # ---------------------------------------------------------
        # Nächsten Tile mit Abstand verarbeiten.
        # ---------------------------------------------------------

        if (
            self._decodeActive
            and
            not self._closed
        ):

            try:

                self._decodeTimer.start(
                    15,
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

        if self._closed:
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

        # Erster Frame sofort anzeigen.
        if frameIndex == 0:

            self.showFrame(
                0
            )

            if not self.paused:

                self.startAnimation()

    # =============================================================
    # DECODE FERTIG
    # =============================================================

    def _finishDecode(self):

        if self._closed:
            return

        self._decodeActive = False
        self._decodeQueue = deque()

        self._decodeBaseFiles = {}
        self._decodeFrameFiles = []
        self._decodeRemaining = []

        self.fetchBusy = False

        self["key_blue"].setText(
            _("Map zoom: %s")
            % self.ZOOM_LEVELS[
                self.zoomIndex
            ]
        )

        if (
            self.frameReady
            and
            self.frameReady[0]
            and
            not self.paused
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

        if (
            index < 0
            or
            index >= len(
                self.framePixmaps
            )
        ):
            return

        if (
            self.frameReady
            and
            not self.frameReady[index]
        ):
            return

        self.currentFrameIndex = index

        # ---------------------------------------------------------
        # Alte Overlay-Tiles komplett ausblenden.
        # Verhindert Geisterbilder alter Frames.
        # ---------------------------------------------------------

        for row in range(
            self.GRID
        ):

            for col in range(
                self.GRID
            ):

                try:

                    self[
                        "radarOverlay_%s_%s"
                        % (
                            row,
                            col
                        )
                    ].hide()

                except Exception:
                    pass

        # ---------------------------------------------------------
        # Neues Frame
        # ---------------------------------------------------------

        cellPix = self.framePixmaps[
            index
        ]

        for (
            row,
            col
        ), pix in cellPix.items():

            if pix is None:
                continue

            try:

                widget = self[
                    "radarOverlay_%s_%s"
                    % (
                        row,
                        col
                    )
                ]

                widget.instance.setPixmap(
                    pix
                )

                widget.show()

            except Exception:
                pass

        # ---------------------------------------------------------
        # Nur hier wird die Radar-Zeit verändert.
        # ---------------------------------------------------------

        try:

            ts = self.frameTimes[
                index
            ]

            if ts is not None:

                self._setRadarFrameTime(
                    ts
                )

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
