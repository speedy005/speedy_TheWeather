```
#!/bin/bash

# =========================================================
# speedy_TheWeather GitHub Installer / Updater
# =========================================================

version='1.1.1'
changelog='Added automatic GitHub update check and installer. Fixed update version detection and plugin installation paths.'


# =========================================================
# GITHUB
# =========================================================

REPOSITORY="https://github.com/speedy005/speedy_TheWeather.git"

BRANCH="master"

DOWNLOAD_URL="https://github.com/speedy005/speedy_TheWeather/archive/refs/heads/${BRANCH}.tar.gz"


# =========================================================
# PATHS
# =========================================================

TMPPATH="/tmp/speedy_TheWeather-install"
FILEPATH="/tmp/speedy_TheWeather-${BRANCH}.tar.gz"

BACKUP_DIR="/tmp/speedy_TheWeather_backup"
OLD_PLUGIN_BACKUP="/tmp/speedy_TheWeather-old-plugin"

CONFIG_DIR="/etc/enigma2/speedy_TheWeather"


# =========================================================
# DETERMINE PLUGIN PATH
# =========================================================

if [ -d "/usr/lib64/enigma2/python/Plugins/Extensions" ]; then
    PLUGINPATH="/usr/lib64/enigma2/python/Plugins/Extensions/speedy_TheWeather"
else
    PLUGINPATH="/usr/lib/enigma2/python/Plugins/Extensions/speedy_TheWeather"
fi


# =========================================================
# GLOBAL VARIABLES
# =========================================================

OSTYPE="Unknown"
STATUS=""

PYTHON="Unknown"
PYTHON_CMD=""
PYTHON_VERSION="Unknown"

DISTRO="Unknown"
DISTRO_VERSION="Unknown"
BOX_TYPE="Unknown"

PACKAGESIX=""
PACKAGEREQUESTS=""
PACKAGEPILLOW=""

PLUGIN_SOURCE=""

BACKUP_CREATED=0


# =========================================================
# LOGGING
# =========================================================

log()
{
    echo "[speedy_TheWeather] $1"
}


error()
{
    echo
    echo "========================================================="
    echo "ERROR: $1"
    echo "========================================================="
    echo
}


# =========================================================
# CLEANUP
# =========================================================

cleanup()
{
    log "Cleaning up temporary files..."

    rm -rf "$TMPPATH"
    rm -f "$FILEPATH"
}


# =========================================================
# OS DETECTION
# =========================================================

detect_os()
{
    if [ -f "/usr/lib/enigma.info" ]; then

        OSTYPE="DreamOs"
        STATUS="/var/lib/dpkg/status"

    elif [ -f "/etc/debian_version" ] &&
         [ -f "/var/lib/dpkg/status" ]; then

        OSTYPE="Debian"
        STATUS="/var/lib/dpkg/status"

    elif [ -f "/var/lib/opkg/status" ] ||
         [ -f "/etc/opkg/opkg.conf" ]; then

        OSTYPE="OE"
        STATUS="/var/lib/opkg/status"

    else

        OSTYPE="Unknown"
        STATUS=""

    fi

    log "Detected OS type: $OSTYPE"
}


# =========================================================
# PYTHON DETECTION
# =========================================================

detect_python()
{
    PYTHON_CMD=""
    PYTHON="Unknown"
    PYTHON_VERSION="Unknown"

    if command -v python3 >/dev/null 2>&1; then

        PYTHON_CMD="python3"
        PYTHON="PY3"

    elif command -v python >/dev/null 2>&1; then

        if python --version 2>&1 | grep -q "^Python 3\."; then

            PYTHON_CMD="python"
            PYTHON="PY3"

        else

            PYTHON_CMD="python"
            PYTHON="PY2"

        fi

    else

        error "Python was not found."
        exit 1

    fi

    PYTHON_VERSION=$(
        "$PYTHON_CMD" --version 2>&1
    )

    log "Python detected: $PYTHON_VERSION"


    if [ "$PYTHON" = "PY3" ]; then

        PACKAGESIX="python3-six"
        PACKAGEREQUESTS="python3-requests"
        PACKAGEPILLOW="python3-pillow"

    else

        PACKAGESIX="python-six"
        PACKAGEREQUESTS="python-requests"
        PACKAGEPILLOW="python-pillow"

    fi
}


# =========================================================
# IMAGE DETECTION
# =========================================================

detect_image()
{
    BOX_TYPE=$(
        head -n 1 /etc/hostname 2>/dev/null
    )

    if [ -z "$BOX_TYPE" ]; then
        BOX_TYPE="Unknown"
    fi


    if [ -f "/usr/lib/enigma.info" ]; then

        DISTRO=$(
            grep "^distro=" /usr/lib/enigma.info 2>/dev/null |
            head -n 1 |
            cut -d "=" -f 2-
        )

        DISTRO_VERSION=$(
            grep "^imageversion=" /usr/lib/enigma.info 2>/dev/null |
            head -n 1 |
            cut -d "=" -f 2-
        )

    elif [ -f "/etc/image-version" ]; then

        DISTRO=$(
            grep "^distro=" /etc/image-version 2>/dev/null |
            head -n 1 |
            cut -d "=" -f 2-
        )

        DISTRO_VERSION=$(
            grep "^version=" /etc/image-version 2>/dev/null |
            head -n 1 |
            cut -d "=" -f 2-
        )

    else

        DISTRO="Unknown"
        DISTRO_VERSION="Unknown"

    fi


    [ -z "$DISTRO" ] &&
        DISTRO="Unknown"

    [ -z "$DISTRO_VERSION" ] &&
        DISTRO_VERSION="Unknown"


    log "Image: $DISTRO $DISTRO_VERSION"
    log "Box: $BOX_TYPE"
}


# =========================================================
# WGET
# =========================================================

install_wget()
{
    if command -v wget >/dev/null 2>&1; then

        log "wget already installed."
        return 0

    fi


    log "wget not found. Installing wget..."


    case "$OSTYPE" in

        DreamOs|Debian)

            apt-get update || {
                error "apt-get update failed."
                exit 1
            }

            apt-get install -y wget || {
                error "wget installation failed."
                exit 1
            }

            ;;


        OE)

            opkg update || {
                error "opkg update failed."
                exit 1
            }

            opkg install wget || {
                error "wget installation failed."
                exit 1
            }

            ;;


        *)

            error "Cannot install wget on unknown OS."
            exit 1

            ;;

    esac


    if ! command -v wget >/dev/null 2>&1; then

        error "wget installation failed."
        exit 1

    fi


    log "wget installed successfully."
}


# =========================================================
# PACKAGE CHECK
# =========================================================

package_installed()
{
    local pkg="$1"

    [ -z "$pkg" ] && return 1


    case "$OSTYPE" in

        DreamOs|Debian)

            if command -v dpkg-query >/dev/null 2>&1; then

                dpkg-query \
                    -W \
                    -f='${Status}' \
                    "$pkg" 2>/dev/null |
                    grep -q "install ok installed"

                return $?

            fi

            ;;


        OE)

            if command -v opkg >/dev/null 2>&1; then

                opkg status "$pkg" 2>/dev/null |
                    grep -q "^Status:.*ok installed"

                return $?

            fi

            ;;

    esac


    return 1
}


# =========================================================
# PACKAGE INSTALLATION
# =========================================================

install_pkg()
{
    local pkg="$1"

    [ -z "$pkg" ] && return 0


    if package_installed "$pkg"; then

        log "$pkg already installed."
        return 0

    fi


    log "Installing package: $pkg"


    case "$OSTYPE" in

        DreamOs|Debian)

            apt-get update >/dev/null 2>&1 || true

            if apt-get install -y "$pkg"; then

                log "$pkg installation finished."

            else

                log "Warning: Could not install $pkg."
                return 1

            fi

            ;;


        OE)

            opkg update >/dev/null 2>&1 || true

            if opkg install "$pkg"; then

                log "$pkg installation finished."

            else

                log "Warning: Could not install $pkg."
                return 1

            fi

            ;;


        *)

            log "Cannot install $pkg on unknown OS."
            return 1

            ;;

    esac


    if package_installed "$pkg"; then

        log "$pkg verified successfully."
        return 0

    fi


    log "Warning: Could not verify $pkg."
    return 1
}


# =========================================================
# DEPENDENCIES
# =========================================================

install_dependencies()
{
    log "Checking dependencies..."

    [ -n "$PACKAGESIX" ] &&
        install_pkg "$PACKAGESIX" || true

    [ -n "$PACKAGEREQUESTS" ] &&
        install_pkg "$PACKAGEREQUESTS" || true

    [ -n "$PACKAGEPILLOW" ] &&
        install_pkg "$PACKAGEPILLOW" || true
}


# =========================================================
# CONFIG BACKUP
# =========================================================

backup_config()
{
    BACKUP_CREATED=0


    if [ ! -d "$CONFIG_DIR" ]; then

        log "No existing configuration directory found."
        return 0

    fi


    log "Creating configuration backup..."


    rm -rf "$BACKUP_DIR"


    if cp -a "$CONFIG_DIR" "$BACKUP_DIR"; then

        BACKUP_CREATED=1
        log "Configuration backup successful."

    else

        error "Configuration backup failed."
        exit 1

    fi
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
        return 0
    fi


    log "Restoring configuration..."


    mkdir -p "$CONFIG_DIR"


    if cp -a "$BACKUP_DIR"/. "$CONFIG_DIR"/; then

        log "Configuration restored successfully."

    else

        log "Warning: Configuration restore failed."

    fi


    rm -rf "$BACKUP_DIR"

    BACKUP_CREATED=0
}


# =========================================================
# DOWNLOAD
# =========================================================

download_package()
{
    log "Downloading speedy_TheWeather v$version..."
    log "Repository: $REPOSITORY"
    log "Branch: $BRANCH"
    log "URL: $DOWNLOAD_URL"


    rm -f "$FILEPATH"


    if ! wget \
        --no-verbose \
        --timeout=30 \
        --tries=3 \
        "$DOWNLOAD_URL" \
        -O "$FILEPATH"
    then

        error "Failed to download speedy_TheWeather."

        cleanup
        exit 1

    fi


    if [ ! -s "$FILEPATH" ]; then

        error "Downloaded archive is empty."

        cleanup
        exit 1

    fi


    if ! gzip -t "$FILEPATH" >/dev/null 2>&1; then

        error "Downloaded file is not a valid gzip archive."

        cleanup
        exit 1

    fi


    if ! tar -tzf "$FILEPATH" >/dev/null 2>&1; then

        error "Downloaded file is not a valid tar archive."

        cleanup
        exit 1

    fi


    log "Archive validation successful."
}


# =========================================================
# EXTRACT
# =========================================================

extract_package()
{
    log "Extracting package..."


    rm -rf "$TMPPATH"


    mkdir -p "$TMPPATH"


    if ! tar -xzf "$FILEPATH" -C "$TMPPATH"; then

        error "Failed to extract package."

        cleanup
        exit 1

    fi


    log "Extraction successful."
}


# =========================================================
# FIND PLUGIN SOURCE
# =========================================================

find_plugin_source()
{
    PLUGIN_SOURCE=""


    # -----------------------------------------------------
    # GitHub archive normally contains:
    #
    # speedy_TheWeather-master/
    # -----------------------------------------------------

    if [ -d "$TMPPATH/speedy_TheWeather-${BRANCH}" ]; then

        PLUGIN_SOURCE="$TMPPATH/speedy_TheWeather-${BRANCH}"

    fi


    # -----------------------------------------------------
    # Search fallback
    # -----------------------------------------------------

    if [ -z "$PLUGIN_SOURCE" ]; then

        PLUGIN_SOURCE=$(
            find "$TMPPATH" \
                -type d \
                -name "speedy_TheWeather-${BRANCH}" \
                2>/dev/null |
            head -n 1
        )

    fi


    # -----------------------------------------------------
    # Search for plugin.py fallback
    # -----------------------------------------------------

    if [ -z "$PLUGIN_SOURCE" ]; then

        PLUGIN_SOURCE=$(
            find "$TMPPATH" \
                -type f \
                -name "plugin.py" \
                2>/dev/null |
            head -n 1 |
            sed 's|/plugin.py$||'
        )

    fi


    if [ -z "$PLUGIN_SOURCE" ] ||
       [ ! -d "$PLUGIN_SOURCE" ]; then

        error "Could not find speedy_TheWeather in GitHub archive."

        echo
        echo "Archive contents:"
        echo "---------------------------------------------------------"

        tar -tzf "$FILEPATH" 2>/dev/null |
            head -100

        echo

        cleanup
        exit 1

    fi


    # -----------------------------------------------------
    # Validate plugin
    # -----------------------------------------------------

    if [ ! -f "$PLUGIN_SOURCE/__init__.py" ]; then

        error "Invalid plugin archive: __init__.py missing."

        cleanup
        exit 1

    fi


    if [ ! -f "$PLUGIN_SOURCE/plugin.py" ]; then

        error "Invalid plugin archive: plugin.py missing."

        cleanup
        exit 1

    fi


    log "Plugin source found:"
    log "$PLUGIN_SOURCE"
}


# =========================================================
# BACKUP EXISTING PLUGIN
# =========================================================

backup_existing_plugin()
{
    rm -rf "$OLD_PLUGIN_BACKUP"


    if [ ! -d "$PLUGINPATH" ]; then

        log "No existing plugin installation found."
        return 0

    fi


    log "Backing up current plugin..."


    if cp -a "$PLUGINPATH" "$OLD_PLUGIN_BACKUP"; then

        log "Plugin backup successful."

    else

        error "Could not backup existing plugin."
        exit 1

    fi
}


# =========================================================
# ROLLBACK
# =========================================================

rollback_plugin()
{
    if [ ! -d "$OLD_PLUGIN_BACKUP" ]; then

        log "No plugin backup available."
        return 1

    fi


    log "Rolling back plugin..."


    rm -rf "$PLUGINPATH"

    mkdir -p "$(dirname "$PLUGINPATH")"


    if cp -a "$OLD_PLUGIN_BACKUP" "$PLUGINPATH"; then

        log "Plugin rollback successful."

        return 0

    fi


    log "WARNING: Plugin rollback failed!"

    return 1
}


# =========================================================
# INSTALL PLUGIN
# =========================================================

install_plugin()
{
    log "Installing speedy_TheWeather v$version..."


    mkdir -p "$(dirname "$PLUGINPATH")"


    if [ -d "$PLUGINPATH" ]; then

        log "Removing old plugin files..."

        if ! rm -rf "$PLUGINPATH"; then

            error "Could not remove old plugin."

            rollback_plugin
            cleanup

            exit 1

        fi

    fi


    mkdir -p "$PLUGINPATH"


    if ! cp -a "$PLUGIN_SOURCE"/. "$PLUGINPATH"/; then

        error "Failed to copy plugin files."

        rollback_plugin
        cleanup

        exit 1

    fi


    # -----------------------------------------------------
    # Verify installation
    # -----------------------------------------------------

    if [ ! -f "$PLUGINPATH/__init__.py" ] ||
       [ ! -f "$PLUGINPATH/plugin.py" ]; then

        error "Plugin installation verification failed."

        rollback_plugin
        cleanup

        exit 1

    fi


    chmod -R 755 "$PLUGINPATH"


    log "Plugin installation successful."
}


# =========================================================
# REMOVE BACKUP
# =========================================================

remove_old_plugin_backup()
{
    if [ -d "$OLD_PLUGIN_BACKUP" ]; then

        rm -rf "$OLD_PLUGIN_BACKUP"
    fi
}


# =========================================================
# SHOW INFORMATION
# =========================================================

show_info()
{
    echo
    echo "========================================================="
    echo " speedy_TheWeather v$version"
    echo " GitHub update successful"
    echo "========================================================="
    echo
    echo "Repository:"
    echo "$REPOSITORY"
    echo
    echo "Branch:"
    echo "$BRANCH"
    echo
    echo "Plugin:"
    echo "$PLUGINPATH"
    echo
    echo "Changelog:"
    echo "$changelog"
    echo
}


# =========================================================
# RESTART ENIGMA2
# =========================================================

restart_gui()
{
    log "Restarting Enigma2 GUI..."


    sync >/dev/null 2>&1 || true

    sleep 2


    if command -v systemctl >/dev/null 2>&1; then

        systemctl restart enigma2
        return $?

    fi


    if [ -x "/etc/init.d/enigma2" ]; then

        /etc/init.d/enigma2 restart
        return $?

    fi


    if command -v init >/dev/null 2>&1; then

        init 4
        sleep 2
        init 3

        return $?

    fi


    if command -v killall >/dev/null 2>&1; then

        killall -HUP enigma2 2>/dev/null || true

        return 0

    fi


    log "WARNING: Could not restart Enigma2 automatically."

    return 1
}


# =========================================================
# MAIN
# =========================================================

echo
echo "========================================================="
echo "       speedy_TheWeather GitHub Installer v$version"
echo "========================================================="
echo


# =========================================================
# ROOT
# =========================================================

if [ "$(id -u)" -ne 0 ]; then

    error "This installer must be executed as root."

    exit 1

fi


# =========================================================
# ENVIRONMENT
# =========================================================

detect_os
detect_python
detect_image


# =========================================================
# WGET
# =========================================================

install_wget


# =========================================================
# DEPENDENCIES
# =========================================================

install_dependencies


# =========================================================
# PREPARE
# =========================================================

cleanup

mkdir -p "$TMPPATH"


# =========================================================
# BACKUP CONFIG
# =========================================================

backup_config


# =========================================================
# DOWNLOAD
# =========================================================

download_package


# =========================================================
# EXTRACT
# =========================================================

extract_package


# =========================================================
# FIND SOURCE
# =========================================================

find_plugin_source


# =========================================================
# BACKUP PLUGIN
# =========================================================

backup_existing_plugin


# =========================================================
# INSTALL
# =========================================================

install_plugin


# =========================================================
# RESTORE CONFIG
# =========================================================

restore_config


# =========================================================
# REMOVE BACKUP
# =========================================================

remove_old_plugin_backup


# =========================================================
# CLEANUP
# =========================================================

cleanup


# =========================================================
# INFORMATION
# =========================================================

show_info


# =========================================================
# RESTART GUI
# =========================================================

restart_gui


exit 0

```
