#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (c) @speedy2026

from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Components.Language import language
from os.path import exists, join, dirname
from enigma import getDesktop, gRGB
from skin import parseColor
from os import makedirs, environ, rmdir, walk, remove
import gettext
import codecs
import shutil
import urllib.request
import subprocess
import os


# ============================================================================
# VERSION / AUTHOR
# ============================================================================

__version__ = "1.1.5"
VERSION = __version__

_AUTHOR_ = "by speedy - 2026"
IDEAS = "@speedy"
THANKS = "@speedy | @atvcaptain"


# ============================================================================
# PATHS
# ============================================================================

TEMP_DIR = "/tmp/speedy_TheWeather"
SYSTEM_DIR = "/etc/enigma2/speedy_TheWeather"

PLUGIN_PATH = dirname(__file__)


# ============================================================================
# UPDATE
# ============================================================================

GITHUB_REPOSITORY = "speedy005/speedy_TheWeather"
GITHUB_BRANCH = "master"

UPDATE_RAW_BASE = (
    "https://raw.githubusercontent.com/"
    "speedy005/speedy_TheWeather/"
    "refs/heads/master"
)

UPDATE_PLUGIN_URL = UPDATE_RAW_BASE + "/plugin.py"
UPDATE_INSTALLER_URL = UPDATE_RAW_BASE + "/installer.sh"

UPDATE_INSTALLER_PATH = join(
    TEMP_DIR,
    "speedy_TheWeather_update_installer.sh"
)


def update_plugin():
    """
    Download and execute the latest speedy_TheWeather installer.
    """

    try:

        print("=" * 60)
        print("[UPDATE] speedy_TheWeather")
        print("[UPDATE] Repository:", GITHUB_REPOSITORY)
        print("[UPDATE] Downloading installer...")
        print("=" * 60)

        request = urllib.request.Request(
            UPDATE_INSTALLER_URL,
            headers={
                "User-Agent": "speedy_TheWeather/1.1.1"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:

            installer_data = response.read()

        if not installer_data:

            print("[UPDATE] ERROR: Empty installer")

            return False

        if not exists(TEMP_DIR):

            makedirs(TEMP_DIR)

        with open(
            UPDATE_INSTALLER_PATH,
            "wb"
        ) as installer_file:

            installer_file.write(
                installer_data
            )

        print(
            "[UPDATE] Installer downloaded:",
            UPDATE_INSTALLER_PATH
        )

        try:

            os.chmod(
                UPDATE_INSTALLER_PATH,
                0o755
            )

        except Exception as e:

            print(
                "[UPDATE] chmod failed:",
                e
            )

        print("[UPDATE] Starting installer...")

        result = subprocess.call(
            ["/bin/sh", UPDATE_INSTALLER_PATH]
        )

        if result == 0:

            print(
                "[UPDATE] Update completed successfully"
            )

            try:

                remove(
                    UPDATE_INSTALLER_PATH
                )

            except Exception:

                pass

            return True

        print(
            "[UPDATE] Installer exited with code:",
            result
        )

        return False

    except Exception as e:

        print(
            "[UPDATE] ERROR:",
            e
        )

        try:

            if exists(
                UPDATE_INSTALLER_PATH
            ):

                remove(
                    UPDATE_INSTALLER_PATH
                )

        except Exception:

            pass

        return False


# ============================================================================
# DEBUG / CACHE
# ============================================================================

DEBUG = True
CACHE_EXPIRE = 3600


# ============================================================================
# CREATE REQUIRED DIRECTORIES
# ============================================================================

if not exists(SYSTEM_DIR):

    makedirs(
        SYSTEM_DIR
    )


if not exists(TEMP_DIR):

    makedirs(
        TEMP_DIR
    )


# ============================================================================
# LANGUAGE
# ============================================================================

PluginLanguageDomain = "speedy_TheWeather"

PluginLanguagePath = (
    "Extensions/speedy_TheWeather/locale"
)


def localeInit():

    lang = language.getLanguage()[:2]

    environ["LANGUAGE"] = lang

    if PluginLanguageDomain and PluginLanguagePath:

        gettext.bindtextdomain(
            PluginLanguageDomain,
            resolveFilename(
                SCOPE_PLUGINS,
                PluginLanguagePath
            ),
        )


def _(txt):

    if not txt:

        return ""

    translated = gettext.dgettext(
        PluginLanguageDomain,
        txt
    )

    if translated and translated != txt:

        return translated

    print(
        "[%s] fallback to default translation for %s"
        % (
            PluginLanguageDomain,
            txt
        )
    )

    return gettext.gettext(txt)


localeInit()

language.addCallback(
    localeInit
)


# ============================================================================
# HTTP HEADERS
# ============================================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/134.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": (
        "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
    ),
    "Connection": "keep-alive",
}


OSM_HEADERS = {
    "User-Agent": (
        "speedy_TheWeather/1.1.1 "
        "(Enigma2; OpenStreetMap; non-commercial; "
        "+https://github.com/speedy005/speedy_TheWeather)"
    ),
    "Referer": "https://www.foreca.com",
    "Accept": (
        "image/webp,image/png,image/*;q=0.8"
    ),
    "Accept-Language": (
        "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
    ),
    "Connection": "keep-alive",
}


# ============================================================================
# SCREEN RESOLUTION
# ============================================================================

def get_screen_resolution():

    desktop = getDesktop(0)

    return desktop.size()


def get_resolution_type():

    width = get_screen_resolution().width()

    if width >= 2560:

        return "wqhd"

    elif width >= 1920:

        return "fhd"

    else:

        return "hd"


# ============================================================================
# GLOBAL THEME
# ============================================================================

def apply_global_theme(screen):
    """
    Applies the background color from set_color.conf
    and transparency from set_alpha.conf.
    """

    color_file = join(
        SYSTEM_DIR,
        "set_color.conf"
    )

    alpha_file = join(
        SYSTEM_DIR,
        "set_alpha.conf"
    )


    # ------------------------------------------------------------------------
    # Background color
    # ------------------------------------------------------------------------

    if exists(color_file):

        try:

            with open(
                color_file,
                "r"
            ) as f:

                parts = (
                    f.read()
                    .strip()
                    .split()
                )

                if len(parts) >= 3:

                    r = parts[0]
                    g = parts[1]
                    b = parts[2]

                    bg_color = gRGB(
                        int(r),
                        int(g),
                        int(b)
                    )

                    if "background_plate" in screen:

                        screen[
                            "background_plate"
                        ].instance.setBackgroundColor(
                            bg_color
                        )

        except Exception as e:

            print(
                "[Theme] Error loading color:",
                e
            )


    # ------------------------------------------------------------------------
    # Transparency
    # ------------------------------------------------------------------------

    if exists(alpha_file):

        try:

            with open(
                alpha_file,
                "r"
            ) as f:

                alpha = f.read().strip()

                if "selection_overlay" in screen:

                    screen[
                        "selection_overlay"
                    ].instance.setBackgroundColor(
                        parseColor(alpha)
                    )

        except Exception as e:

            print(
                "[Theme] Error loading alpha:",
                e
            )


# ============================================================================
# CLEANUP TEMP FILES
# ============================================================================

def cleanup_temp_files(keep_token=True):
    """
    Remove temporary files.

    If keep_token=True, token.json is preserved.
    """

    d = TEMP_DIR

    if not exists(d):

        return


    try:

        # --------------------------------------------------------------------
        # Keep token.json
        # --------------------------------------------------------------------

        if keep_token:

            token_path = join(
                TEMP_DIR,
                "weather_map_cache",
                "token.json"
            )

            for root, dirs, files in walk(
                d,
                topdown=False
            ):

                # ------------------------------------------------------------
                # Files
                # ------------------------------------------------------------

                for name in files:

                    file_path = join(
                        root,
                        name
                    )

                    if file_path != token_path:

                        remove(
                            file_path
                        )


                # ------------------------------------------------------------
                # Directories
                # ------------------------------------------------------------

                for name in dirs:

                    dir_path = join(
                        root,
                        name
                    )

                    if (
                        dir_path
                        == join(
                            TEMP_DIR,
                            "weather_map_cache"
                        )
                    ):

                        continue

                    try:

                        rmdir(
                            dir_path
                        )

                    except OSError:

                        pass


            # ----------------------------------------------------------------
            # Recreate required TEMP directories
            # ----------------------------------------------------------------

            subdirs = [
                "meteogram",
                "weather_detail",
                "weather_map_cache/wetterkontor"
            ]

            for sub in subdirs:

                subdir = join(
                    TEMP_DIR,
                    sub
                )

                if not exists(subdir):

                    makedirs(
                        subdir
                    )


            if DEBUG:

                print(
                    "[Cleanup] Cleaned %s "
                    "(kept token)"
                    % TEMP_DIR
                )


        # --------------------------------------------------------------------
        # Complete remove
        # --------------------------------------------------------------------

        else:

            shutil.rmtree(
                TEMP_DIR
            )

            makedirs(
                TEMP_DIR
            )


            for sub in [
                "meteogram",
                "weather_detail",
                "weather_map_cache/wetterkontor"
            ]:

                subdir = join(
                    TEMP_DIR,
                    sub
                )

                if not exists(subdir):

                    makedirs(
                        subdir
                    )


            if DEBUG:

                print(
                    "[Cleanup] Removed and recreated %s"
                    % TEMP_DIR
                )


    except Exception as e:

        print(
            "[Cleanup] Error cleaning %s: %s"
            % (
                TEMP_DIR,
                e
            )
        )


# ============================================================================
# END
# ============================================================================
