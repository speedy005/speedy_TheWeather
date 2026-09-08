#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# ============================================================
# speedy_TheWeather
# ============================================================

from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Components.Language import language

from os.path import exists, dirname
from os import environ, remove, system

import gettext
import ssl

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen


# ============================================================
# VERSION
# ============================================================

__version__ = "1.1.1"
VERSION = __version__

_AUTHOR_ = "by speedy - 2026"


# ============================================================
# GITHUB
# ============================================================

GITHUB_REPO = (
    "https://github.com/"
    "speedy005/speedy_TheWeather.git"
)

GITHUB_BRANCH = "master"

GITHUB_RAW = (
    "https://raw.githubusercontent.com/"
    "speedy005/speedy_TheWeather/"
    + GITHUB_BRANCH
)

VERSION_URL = GITHUB_RAW + "/version.txt"

INSTALLER_URL = GITHUB_RAW + "/installer.sh"


# ============================================================
# PATHS
# ============================================================

PLUGIN_PATH = dirname(__file__)

TEMP_INSTALLER = (
    "/tmp/speedy_TheWeather_installer.sh"
)


# ============================================================
# LANGUAGE
# ============================================================

PluginLanguageDomain = "speedy_TheWeather"

PluginLanguagePath = (
    "Extensions/speedy_TheWeather/locale"
)


def localeInit():

    lang = language.getLanguage()[:2]

    environ["LANGUAGE"] = lang

    if (
        PluginLanguageDomain
        and PluginLanguagePath
    ):

        gettext.bindtextdomain(
            PluginLanguageDomain,
            resolveFilename(
                SCOPE_PLUGINS,
                PluginLanguagePath
            )
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

    return txt


localeInit()

language.addCallback(localeInit)


# ============================================================
# GITHUB CONNECTION
# ============================================================

def _github_open(url, timeout=10):
    """
    Open a GitHub URL.

    Compatible with older Enigma2 Python versions.
    """

    request = Request(
        url,
        headers={
            "User-Agent":
                "speedy_TheWeather-Updater"
        }
    )

    try:

        context = ssl._create_unverified_context()

        return urlopen(
            request,
            timeout=timeout,
            context=context
        )

    except TypeError:

        # Compatibility fallback
        return urlopen(
            request,
            timeout=timeout
        )


# ============================================================
# VERSION PARSER
# ============================================================

def _version_tuple(version):
    """
    Convert version string into a comparable tuple.

    Example:

        1.2.10 -> (1, 2, 10)
    """

    if not version:
        return (0,)


    try:

        version = str(
            version
        ).strip()


        if version.startswith("v"):
            version = version[1:]


        parts = version.split(".")


        result = []

        for part in parts:

            number = ""

            for char in part:

                if char.isdigit():
                    number += char

                else:
                    break


            if number:
                result.append(
                    int(number)
                )

            else:
                result.append(0)


        return tuple(result)

    except Exception:

        return (0,)


# ============================================================
# GET CURRENT GITHUB VERSION
# ============================================================

def get_github_version():
    """
    Get the latest version from GitHub.

    GitHub file:

        version.txt
    """

    try:

        response = _github_open(
            VERSION_URL,
            timeout=10
        )


        data = response.read()


        try:

            version = data.decode(
                "utf-8"
            )

        except AttributeError:

            version = data


        version = version.strip()


        if version.startswith("v"):
            version = version[1:]


        if not version:

            print(
                "[speedy_TheWeather] "
                "GitHub version.txt is empty"
            )

            return None


        print(
            "[speedy_TheWeather] "
            "GitHub version: %s"
            % version
        )


        return version


    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "GitHub version check failed: %s"
            % e
        )

        return None


# ============================================================
# CHECK UPDATE
# ============================================================

def check_for_update():
    """
    Check if a newer GitHub version exists.

    Returns:

        version string
        or None
    """

    latest = get_github_version()


    if not latest:

        return None


    current_tuple = _version_tuple(
        __version__
    )

    latest_tuple = _version_tuple(
        latest
    )


    if latest_tuple > current_tuple:

        print(
            "[speedy_TheWeather] "
            "Update available: %s -> %s"
            % (
                __version__,
                latest
            )
        )

        return latest


    print(
        "[speedy_TheWeather] "
        "Plugin is up to date: %s"
        % __version__
    )


    return None


# ============================================================
# DOWNLOAD INSTALLER
# ============================================================

def download_installer():
    """
    Download installer.sh from GitHub.
    """

    try:

        response = _github_open(
            INSTALLER_URL,
            timeout=20
        )


        data = response.read()


        if not data:

            print(
                "[speedy_TheWeather] "
                "Downloaded installer is empty"
            )

            return False


        with open(
            TEMP_INSTALLER,
            "wb"
        ) as installer:

            installer.write(data)


        if not exists(
            TEMP_INSTALLER
        ):

            print(
                "[speedy_TheWeather] "
                "Installer file was not created"
            )

            return False


        print(
            "[speedy_TheWeather] "
            "Installer downloaded"
        )


        return True


    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "Installer download failed: %s"
            % e
        )

        return False


# ============================================================
# INSTALL UPDATE
# ============================================================

def install_update():
    """
    Download and execute the GitHub installer.
    """

    if not download_installer():

        return False


    try:

        # Make installer executable
        result = system(
            "chmod 755 %s"
            % TEMP_INSTALLER
        )


        if result != 0:

            print(
                "[speedy_TheWeather] "
                "Could not make installer executable"
            )

            return False


        print(
            "[speedy_TheWeather] "
            "Starting GitHub installer..."
        )


        result = system(
            "/bin/sh %s"
            % TEMP_INSTALLER
        )


        if result == 0:

            print(
                "[speedy_TheWeather] "
                "Update installer finished successfully"
            )

            return True


        print(
            "[speedy_TheWeather] "
            "Installer returned error code: %s"
            % result
        )


        return False


    except Exception as e:

        print(
            "[speedy_TheWeather] "
            "Update execution failed: %s"
            % e
        )

        return False


    finally:

        try:

            if exists(
                TEMP_INSTALLER
            ):

                remove(
                    TEMP_INSTALLER
                )

        except Exception:

            pass


# ============================================================
# UPDATE INFORMATION
# ============================================================

def get_update_info():
    """
    Return update information.

    Example:

        {
            "current": "1.1.0",
            "latest": "1.1.1",
            "update": True
        }
    """

    latest = get_github_version()


    if not latest:

        return {
            "current": __version__,
            "latest": None,
            "update": False
        }


    update_available = (
        _version_tuple(latest)
        >
        _version_tuple(__version__)
    )


    return {
        "current": __version__,
        "latest": latest,
        "update": update_available
    }
