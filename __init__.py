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

__version__ = "1.1.1"
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
                "User-Agent": "speedy_TheWeather/1.5.2"
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

        with open(
            UPDATE_INSTALLER_PATH,
            "wb"
        ) as installer_file:
            installer_file.write(installer_data)

        print(
            "[UPDATE] Installer downloaded:",
            UPDATE_INSTALLER_PATH
        )

        # Make installer executable
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
# CREATE DIRECTORIES
# ============================================================================

if not exists(SYSTEM_DIR):
    makedirs(SYSTEM_DIR)

if not exists(TEMP_DIR):
    makedirs(TEMP_DIR)

if not exists(DBG_DIR):
    makedirs(DBG_DIR)

if not exists(CACHE_BASE):
    makedirs(CACHE_BASE)

if not exists(WETTERKONTOR_CACHE):
    makedirs(WETTERKONTOR_CACHE)

if not exists(METEOGRAM_CACHE):
    makedirs(METEOGRAM_CACHE)

if not exists(WEATHER_DETAIL_CACHE):
    makedirs(WEATHER_DETAIL_CACHE)


# ============================================================================
# LANGUAGE
# ============================================================================

PluginLanguageDomain = "speedy_TheWeather"
PluginLanguagePath = "Extensions/speedy_TheWeather/locale"


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
        "speedy_TheWeather/1.5.2 "
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
# LANGUAGE INITIALIZATION
# ============================================================================

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
language.addCallback(localeInit)


# ============================================================================
# DETECT SCREEN RESOLUTION
# ============================================================================

def get_screen_resolution():
    """Get current screen resolution."""

    desktop = getDesktop(0)

    return desktop.size()


def get_resolution_type():
    """Get resolution type: hd, fhd, wqhd."""

    width = get_screen_resolution().width()

    if width >= 2560:
        return "wqhd"

    elif width >= 1920:
        return "fhd"

    else:
        # 1280x720 or smaller
        return "hd"


# ============================================================================
# SKIN LOADER
# ============================================================================

def load_skin_by_class(class_name):
    """
    Load skin using class name and current resolution.

    First tries custom skins:
        skins_user/

    Then built-in skins:
        skins/

    Finally falls back to HD.
    """

    if DEBUG:
        print("\n" + "=" * 60)
        print(
            "[SKIN DEBUG] Looking for skin: '%s'"
            % class_name
        )
        print(
            "[SKIN DEBUG] Built-in skins path = %s"
            % SKINS_PATH
        )
        print(
            "[SKIN DEBUG] Custom skins path = %s"
            % CUSTOM_SKINS_PATH
        )

    resolution = get_resolution_type()

    if DEBUG:
        print(
            "[SKIN DEBUG] resolution = %s"
            % resolution
        )

    # ------------------------------------------------------------------------
    # Custom skin
    # ------------------------------------------------------------------------

    custom_skin_file = None

    if exists(CUSTOM_SKINS_PATH):

        custom_skin_file = join(
            CUSTOM_SKINS_PATH,
            resolution,
            "%s.xml" % class_name
        )

        if DEBUG:
            print(
                "[SKIN DEBUG] Trying custom: %s"
                % custom_skin_file
            )

            print(
                "[SKIN DEBUG] Exists? %s"
                % exists(custom_skin_file)
            )

    else:

        if DEBUG:
            print(
                "[SKIN DEBUG] Custom skins directory "
                "does not exist"
            )

    # ------------------------------------------------------------------------
    # Built-in skins
    # ------------------------------------------------------------------------

    builtin_skin_file = join(
        SKINS_PATH,
        resolution,
        "%s.xml" % class_name
    )

    fallback_skin_file = join(
        SKINS_PATH,
        "hd",
        "%s.xml" % class_name
    )

    # ------------------------------------------------------------------------
    # Determine skin
    # ------------------------------------------------------------------------

    skin_file = None

    if (
        custom_skin_file
        and exists(custom_skin_file)
    ):

        skin_file = custom_skin_file

        if DEBUG:
            print(
                "[SKIN DEBUG] Using custom skin"
            )

    elif exists(builtin_skin_file):

        skin_file = builtin_skin_file

        if DEBUG:
            print(
                "[SKIN DEBUG] Using built-in skin "
                "for current resolution"
            )

    elif exists(fallback_skin_file):

        skin_file = fallback_skin_file

        if DEBUG:
            print(
                "[SKIN DEBUG] Using HD fallback skin"
            )

    else:

        if DEBUG:
            print(
                "[SKIN DEBUG] No skin found at all"
            )

    # ------------------------------------------------------------------------
    # Read skin
    # ------------------------------------------------------------------------

    if skin_file and exists(skin_file):

        if DEBUG:
            print(
                "[SKIN DEBUG] FOUND! Loading file: %s"
                % skin_file
            )

        try:

            with codecs.open(
                skin_file,
                "r",
                "utf-8"
            ) as f:

                content = f.read()

                if DEBUG:

                    print(
                        "[SKIN DEBUG] Loaded %s bytes"
                        % len(content)
                    )

                    print(
                        "[SKIN DEBUG] First 100 chars: %s"
                        % content[:100].replace(
                            chr(10),
                            " "
                        )
                    )

                    print(
                        "=" * 60 + "\n"
                    )

                return content

        except Exception as e:

            print(
                "[SKIN DEBUG] Error reading file: %s"
                % e
            )

    else:

        print(
            "[SKIN DEBUG] SKIN FILE MISSING: %s"
            % skin_file
        )

    if DEBUG:
        print(
            "=" * 60 + "\n"
        )

    return None


def load_skin_for_class(cls):
    return load_skin_by_class(
        cls.__name__
    )


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
# ICON PATH
# ============================================================================

def get_icon_path(
    icon_name,
    fallback="na.png"
):
    """
    Returns the full path of an icon from thumb/.

    If the requested icon does not exist,
    the fallback icon is returned.
    """

    path = join(
        THUMB_PATH,
        icon_name
    )

    if exists(path):
        return path

    fallback_path = join(
        THUMB_PATH,
        fallback
    )

    if exists(fallback_path):
        return fallback_path

    return None


# ============================================================================
# CLEANUP TEMP FILES
# ============================================================================

def cleanup_temp_files(keep_token=True):
    """
    Remove temporary folders.

    If keep_token=True, token.json is preserved.
    """

    dirs_to_clean = [
        TEMP_DIR,
        DBG_DIR
    ]

    for d in dirs_to_clean:

        if not exists(d):
            continue

        try:

            # ----------------------------------------------------------------
            # TEMP DIR - KEEP TOKEN
            # ----------------------------------------------------------------

            if (
                keep_token
                and d == TEMP_DIR
            ):

                token_path = join(
                    TEMP_DIR,
                    "weather_map_cache",
                    "token.json"
                )

                for root, dirs, files in walk(
                    d,
                    topdown=False
                ):

                    # --------------------------------------------------------
                    # Files
                    # --------------------------------------------------------

                    for name in files:

                        file_path = join(
                            root,
                            name
                        )

                        if file_path != token_path:

                            remove(
                                file_path
                            )

                    # --------------------------------------------------------
                    # Directories
                    # --------------------------------------------------------

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

                        rmdir(
                            dir_path
                        )

                # ------------------------------------------------------------
                # Recreate essential directories
                # ------------------------------------------------------------

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
                        % d
                    )

            # ----------------------------------------------------------------
            # COMPLETE REMOVE
            # ----------------------------------------------------------------

            else:

                shutil.rmtree(d)

                if DEBUG:

                    print(
                        "[Cleanup] Removed %s"
                        % d
                    )

                # ------------------------------------------------------------
                # Recreate TEMP
                # ------------------------------------------------------------

                if d == TEMP_DIR:

                    makedirs(d)

                    for sub in [
                        "meteogram",
                        "weather_detail",
                        "weather_map_cache/wetterkontor"
                    ]:

                        subdir = join(
                            d,
                            sub
                        )

                        if not exists(subdir):

                            makedirs(
                                subdir
                            )

                # ------------------------------------------------------------
                # Recreate DEBUG
                # ------------------------------------------------------------

                elif d == DBG_DIR:

                    makedirs(d)

        except Exception as e:

            print(
                "[Cleanup] Error cleaning %s: %s"
                % (
                    d,
                    e
                )
            )


# ============================================================================
# END
# ============================================================================
