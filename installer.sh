#!/bin/bash

# =========================================================
# speedy_TheWeather Installer
# Version 1.9.5
# =========================================================

VERSION="1.9.5"
BRANCH="master"

REPO_OWNER="speedy005"
REPO_NAME="speedy_TheWeather"

DOWNLOAD_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/heads/${BRANCH}.tar.gz"

# =========================================================
# CHANGELOG
# =========================================================

changelog='v1.9.5 EN: Fixed language files and PO/MO file names. Added update function. Fixed Rain Radar, Seven Day Weather, weather icons and detached GUI restart. Added customizable colors. Added automatic weather images based on the time of day and seasonal backgrounds with automatic download and installation. Added sunrise and sunset display as well as moonrise and moonset display. Added comparison of weather data for two locations including sunrise, sunset, moonrise and moonset times. Added themed colors for weather description, feels like temperature, wind, rain, sun and moon information. Added improved city search and city selection with a dedicated selection window for matching locations. Improved moonrise and moonset calculations with better local time and UTC offset handling. Improved date and time handling throughout the plugin. Improved weather data handling and display reliability. Improved performance on low-end Enigma2 receivers with optimized radar loading, decoding, caching and animation handling. Added Ultra Low-End, Low-End, Auto and Normal performance modes. Existing features remain available. Buy me a coffee if you like this plugin. | DE: Sprachdateien sowie PO-/MO-Dateinamen korrigiert. Update-Funktion hinzugefügt. Rain Radar, Sieben-Tage-Wetter, Wetter-Icons und Neustart der getrennten GUI korrigiert. Anpassbare Farben hinzugefügt. Automatische Wetterbilder passend zur Tageszeit sowie saisonale Hintergründe mit automatischem Download und Installation hinzugefügt. Anzeige von Sonnenaufgang und Sonnenuntergang sowie Mondaufgang und Monduntergang hinzugefügt. Vergleich der Wetterdaten für zwei Orte mit Anzeige von Sonnenaufgang, Sonnenuntergang, Mondaufgang und Monduntergang hinzugefügt. Thematische Farben für Wetterbeschreibung, gefühlte Temperatur, Wind, Regen sowie Sonnen- und Mondinformationen hinzugefügt. Verbesserte Stadt-Suche und Stadtauswahl mit einem eigenen Auswahlfenster für passende Orte hinzugefügt. Mondaufgangs- und Monduntergangsberechnung mit verbesserter Behandlung von Ortszeit und UTC-Zeitverschiebung verbessert. Datums- und Zeitverarbeitung im gesamten Plugin verbessert. Verarbeitung und Anzeige der Wetterdaten zuverlässiger gemacht. Performance auf schwachen Enigma2-Receivern durch optimiertes Radar-Laden, Decoding, Caching und Animationen verbessert. Ultra Low-End-, Low-End-, Auto- und Normal-Performance-Modi hinzugefügt. Bestehende Funktionen bleiben erhalten. Wenn dir dieses Plugin gefällt, kannst du mich gerne auf einen Kaffee einladen.'

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

    # -----------------------------------------------------
    # /usr/lib/enigma.info
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # /etc/image-version
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Prefer curl
    # -----------------------------------------------------

    if check_command curl; then

        DOWNLOADER="curl"

        log "Downloader selected: curl"

        return 0

    fi

    # -----------------------------------------------------
    # Then wget
    # -----------------------------------------------------

    if check_command wget; then

        DOWNLOADER="wget"

        log "Downloader selected: wget"

        return 0

    fi

    # -----------------------------------------------------
    # Try curl installation
    # -----------------------------------------------------

    if install_curl; then

        DOWNLOADER="curl"

        log "Downloader selected: curl"

        return 0

    fi

    # -----------------------------------------------------
    # Try wget installation
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CURL
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # WGET
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # File exists
    # -----------------------------------------------------

    if [ ! -f "$FILEPATH" ]; then

        error "Download finished but archive file does not exist."

        return 1

    fi

    # -----------------------------------------------------
    # File not empty
    # -----------------------------------------------------

    if [ ! -s "$FILEPATH" ]; then

        error "Downloaded archive is empty."

        return 1

    fi

    FILESIZE=$(
        wc -c < "$FILEPATH" 2>/dev/null
    )

    log "Downloaded size: ${FILESIZE} bytes"

    # -----------------------------------------------------
    # Check suspiciously small file
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # gzip
    # -----------------------------------------------------

    if ! gzip -t "$FILEPATH" >/dev/null 2>&1; then

        error "Downloaded file is not a valid gzip archive."

        return 1

    fi

    log "gzip validation successful."

    # -----------------------------------------------------
    # tar
    # -----------------------------------------------------

    if ! tar -tzf "$FILEPATH" >/dev/null 2>&1; then

        error "Downloaded file is not a valid tar archive."

        return 1

    fi

    log "tar validation successful."

    # -----------------------------------------------------
    # plugin.py
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Files
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Repository folders
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Plugin base
    # -----------------------------------------------------

    if ! mkdir -p "$PLUGIN_BASE"; then

        error "Could not create plugin base directory."

        return 1

    fi

    # -----------------------------------------------------
    # Remove old installation
    # -----------------------------------------------------

    if [ -d "$PLUGINPATH" ]; then

        log "Removing old plugin installation..."

        if ! rm -rf "$PLUGINPATH"; then

            error "Could not remove old plugin installation."

            return 1

        fi

    fi

    # -----------------------------------------------------
    # Create target
    # -----------------------------------------------------

    if ! mkdir -p "$PLUGINPATH"; then

        error "Could not create plugin directory."

        return 1

    fi

    # -----------------------------------------------------
    # Clean repository-only files
    # -----------------------------------------------------

    if ! remove_repository_only_files; then

        error "Could not clean repository-only files."

        return 1

    fi

    # -----------------------------------------------------
    # Copy plugin
    # -----------------------------------------------------

    log "Copying plugin files..."

    if ! cp -a \
        "$PLUGIN_SOURCE"/. \
        "$PLUGINPATH"/
    then

        error "Failed to copy plugin files."

        return 1

    fi

    log "Plugin files copied."

    # -----------------------------------------------------
    # Verify core files
    # -----------------------------------------------------

    if [ ! -f "$PLUGINPATH/__init__.py" ]; then

        error "__init__.py missing after installation."

        return 1

    fi

    if [ ! -f "$PLUGINPATH/plugin.py" ]; then

        error "plugin.py missing after installation."

        return 1

    fi

    # -----------------------------------------------------
    # Verify plugin isn't empty
    # -----------------------------------------------------

    if [ -z "$(
        find "$PLUGINPATH" \
            -type f \
            2>/dev/null |
        head -n 1
    )" ]; then

        error "Plugin installation is empty."

        return 1

    fi

    # -----------------------------------------------------
    # Verify README
    # -----------------------------------------------------

    if [ -f "$PLUGINPATH/README.md" ]; then

        error "README.md was installed unexpectedly."

        return 1

    fi

    # -----------------------------------------------------
    # Verify installer
    # -----------------------------------------------------

    if [ -f "$PLUGINPATH/installer.sh" ]; then

        error "installer.sh was installed unexpectedly."

        return 1

    fi

    # -----------------------------------------------------
    # Verify version.txt
    # -----------------------------------------------------

    if [ -f "$PLUGINPATH/version.txt" ]; then

        error "version.txt was installed unexpectedly."

        return 1

    fi

    # -----------------------------------------------------
    # Verify SVG
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Verify converter
    # -----------------------------------------------------

    if [ -d "$PLUGINPATH/converter" ]; then

        error "converter/ was installed unexpectedly."

        return 1

    fi

    # -----------------------------------------------------
    # Verify renderer
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Plugin
    # -----------------------------------------------------

    if [ "$PLUGIN_BACKUP_CREATED" -eq 1 ]; then

        rollback_plugin

    fi

    # -----------------------------------------------------
    # Configuration
    # -----------------------------------------------------

    if [ "$BACKUP_CREATED" -eq 1 ]; then

        restore_config

    fi

    # -----------------------------------------------------
    # Automatic backgrounds
    # -----------------------------------------------------

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

    echo "Changelog:"
    echo "---------------------------------------------------------"
    echo "$CHANGELOG"
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

# =========================================================
# ROOT
# =========================================================

check_root

# =========================================================
# ENVIRONMENT
# =========================================================

detect_os
detect_python
detect_image

# =========================================================
# DOWNLOADER
# =========================================================

select_downloader

# =========================================================
# TEMPORARY DIRECTORY
# =========================================================

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
