#!/bin/sh

# =========================================================
# speedy_TheWeather GitHub Installer / Updater
# POSIX /bin/sh compatible
# =========================================================

VERSION="1.1.1"

CHANGELOG="Added automatic GitHub update check and installer. Fixed update version detection and plugin installation paths."

REPOSITORY="https://github.com/speedy005/speedy_TheWeather.git"
BRANCH="master"

DOWNLOAD_URL="https://github.com/speedy005/speedy_TheWeather/archive/refs/heads/${BRANCH}.tar.gz"


# =========================================================
# PATHS
# =========================================================

TMP_ROOT="/tmp/speedy_TheWeather-update"
ARCHIVE="/tmp/speedy_TheWeather-${BRANCH}.tar.gz"

PLUGIN_NAME="speedy_TheWeather"

DEFAULT_PLUGIN_PATH="/usr/lib/enigma2/python/Plugins/Extensions/${PLUGIN_NAME}"
LIB64_PLUGIN_PATH="/usr/lib64/enigma2/python/Plugins/Extensions/${PLUGIN_NAME}"

PLUGIN_PATH=""

PLUGIN_BACKUP="/tmp/speedy_TheWeather-plugin-backup"
CONFIG_BACKUP="/tmp/speedy_TheWeather-config-backup"

CONFIG_DIR="/etc/enigma2/speedy_TheWeather"


# =========================================================
# GLOBALS
# =========================================================

PLUGIN_SOURCE=""

OS_TYPE="Unknown"
DISTRO="Unknown"
DISTRO_VERSION="Unknown"
BOX_TYPE="Unknown"

PYTHON_CMD=""
PYTHON_VERSION="Unknown"

CONFIG_BACKUP_CREATED=0
PLUGIN_BACKUP_CREATED=0


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

    rm -rf "$TMP_ROOT"
    rm -f "$ARCHIVE"
}


# =========================================================
# DETERMINE PLUGIN PATH
# =========================================================

detect_plugin_path()
{
    # -----------------------------------------------------
    # Prefer the currently installed plugin path.
    # This prevents an update from accidentally switching
    # between /usr/lib and /usr/lib64.
    # -----------------------------------------------------

    if [ -d "$DEFAULT_PLUGIN_PATH" ]; then

        PLUGIN_PATH="$DEFAULT_PLUGIN_PATH"

    elif [ -d "$LIB64_PLUGIN_PATH" ]; then

        PLUGIN_PATH="$LIB64_PLUGIN_PATH"

    elif [ -d "/usr/lib64/enigma2/python/Plugins/Extensions" ]; then

        PLUGIN_PATH="$LIB64_PLUGIN_PATH"

    else

        PLUGIN_PATH="$DEFAULT_PLUGIN_PATH"

    fi


    log "Plugin path:"
    log "$PLUGIN_PATH"
}


# =========================================================
# OS DETECTION
# =========================================================

detect_os()
{
    if [ -f "/usr/lib/enigma.info" ]; then

        OS_TYPE="DreamOs"

    elif [ -f "/etc/debian_version" ] &&
         [ -f "/var/lib/dpkg/status" ]; then

        OS_TYPE="Debian"

    elif [ -f "/var/lib/opkg/status" ] ||
         [ -f "/etc/opkg/opkg.conf" ]; then

        OS_TYPE="OE"

    else

        OS_TYPE="Unknown"

    fi


    log "Detected OS type: $OS_TYPE"
}


# =========================================================
# IMAGE DETECTION
# =========================================================

detect_image()
{
    if [ -f "/etc/hostname" ]; then

        BOX_TYPE="$(head -n 1 /etc/hostname 2>/dev/null)"

    fi


    [ -z "$BOX_TYPE" ] && BOX_TYPE="Unknown"


    if [ -f "/usr/lib/enigma.info" ]; then

        DISTRO="$(
            grep "^distro=" /usr/lib/enigma.info 2>/dev/null |
            head -n 1 |
            cut -d "=" -f 2-
        )"

        DISTRO_VERSION="$(
            grep "^imageversion=" /usr/lib/enigma.info 2>/dev/null |
            head -n 1 |
            cut -d "=" -f 2-
        )"

    elif [ -f "/etc/image-version" ]; then

        DISTRO="$(
            grep "^distro=" /etc/image-version 2>/dev/null |
            head -n 1 |
            cut -d "=" -f 2-
        )"

        DISTRO_VERSION="$(
            grep "^version=" /etc/image-version 2>/dev/null |
            head -n 1 |
            cut -d "=" -f 2-
        )"

    fi


    [ -z "$DISTRO" ] && DISTRO="Unknown"
    [ -z "$DISTRO_VERSION" ] && DISTRO_VERSION="Unknown"


    log "Image: $DISTRO $DISTRO_VERSION"
    log "Box: $BOX_TYPE"
}


# =========================================================
# PYTHON DETECTION
# =========================================================

detect_python()
{
    PYTHON_CMD=""
    PYTHON_VERSION="Unknown"


    if command -v python3 >/dev/null 2>&1; then

        PYTHON_CMD="python3"

    elif command -v python >/dev/null 2>&1; then

        PYTHON_CMD="python"

    else

        error "Python was not found."

        exit 1

    fi


    PYTHON_VERSION="$(
        "$PYTHON_CMD" --version 2>&1
    )"


    log "Python detected: $PYTHON_VERSION"
}


# =========================================================
# WGET CHECK
# =========================================================

check_wget()
{
    if command -v wget >/dev/null 2>&1; then

        log "wget found."
        return 0

    fi


    error "wget was not found."

    case "$OS_TYPE" in

        DreamOs|Debian)

            log "Trying to install wget..."

            apt-get update >/dev/null 2>&1 || true
            apt-get install -y wget >/dev/null 2>&1 || true

            ;;

        OE)

            log "Trying to install wget..."

            opkg update >/dev/null 2>&1 || true
            opkg install wget >/dev/null 2>&1 || true

            ;;

        *)

            ;;

    esac


    if command -v wget >/dev/null 2>&1; then

        log "wget installed successfully."
        return 0

    fi


    error "wget is required but could not be installed."

    exit 1
}


# =========================================================
# DOWNLOAD
# =========================================================

download_package()
{
    log "Downloading speedy_TheWeather v$VERSION..."
    log "Repository: $REPOSITORY"
    log "Branch: $BRANCH"

    rm -f "$ARCHIVE"


    if ! wget \
        -T 30 \
        -t 3 \
        -O "$ARCHIVE" \
        "$DOWNLOAD_URL"
    then

        error "Failed to download speedy_TheWeather."

        cleanup
        exit 1

    fi


    if [ ! -s "$ARCHIVE" ]; then

        error "Downloaded archive is empty."

        cleanup
        exit 1

    fi


    log "Download successful."


    # -----------------------------------------------------
    # Validate gzip
    # -----------------------------------------------------

    if ! gzip -t "$ARCHIVE" >/dev/null 2>&1; then

        error "Downloaded file is not a valid gzip archive."

        cleanup
        exit 1

    fi


    # -----------------------------------------------------
    # Validate tar
    # -----------------------------------------------------

    if ! tar -tzf "$ARCHIVE" >/dev/null 2>&1; then

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


    rm -rf "$TMP_ROOT"


    if ! mkdir -p "$TMP_ROOT"; then

        error "Could not create temporary directory."

        cleanup
        exit 1

    fi


    if ! tar -xzf "$ARCHIVE" -C "$TMP_ROOT"; then

        error "Failed to extract GitHub archive."

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
    # Normal GitHub archive path
    # -----------------------------------------------------

    if [ -d "$TMP_ROOT/speedy_TheWeather-${BRANCH}" ]; then

        PLUGIN_SOURCE="$TMP_ROOT/speedy_TheWeather-${BRANCH}"

    fi


    # -----------------------------------------------------
    # Fallback: search directory
    # -----------------------------------------------------

    if [ -z "$PLUGIN_SOURCE" ]; then

        PLUGIN_SOURCE="$(
            find "$TMP_ROOT" \
                -type d \
                -name "speedy_TheWeather-${BRANCH}" \
                2>/dev/null |
            head -n 1
        )"

    fi


    # -----------------------------------------------------
    # Fallback: find plugin.py
    # -----------------------------------------------------

    if [ -z "$PLUGIN_SOURCE" ]; then

        PLUGIN_SOURCE="$(
            find "$TMP_ROOT" \
                -type f \
                -name "plugin.py" \
                2>/dev/null |
            head -n 1 |
            sed 's|/plugin.py$||'
        )"

    fi


    if [ -z "$PLUGIN_SOURCE" ] ||
       [ ! -d "$PLUGIN_SOURCE" ]; then

        error "Could not find speedy_TheWeather in GitHub archive."

        echo
        echo "Archive contents:"
        echo "---------------------------------------------------------"

        tar -tzf "$ARCHIVE" 2>/dev/null |
            head -100

        echo

        cleanup
        exit 1

    fi


    log "Plugin source found:"
    log "$PLUGIN_SOURCE"


    # =====================================================
    # VALIDATE REQUIRED FILES
    # =====================================================

    if [ ! -f "$PLUGIN_SOURCE/__init__.py" ]; then

        error "__init__.py is missing."

        cleanup
        exit 1

    fi


    if [ ! -f "$PLUGIN_SOURCE/plugin.py" ]; then

        error "plugin.py is missing."

        cleanup
        exit 1

    fi


    if [ ! -d "$PLUGIN_SOURCE/locale" ]; then

        log "WARNING: locale directory is missing."

    fi


    if [ ! -f "$PLUGIN_SOURCE/locale/de/LC_MESSAGES/TheWeather.mo" ]; then

        log "WARNING: German TheWeather.mo is missing."

    fi


    log "Plugin archive validation successful."
}


# =========================================================
# BACKUP CONFIGURATION
# =========================================================

backup_config()
{
    CONFIG_BACKUP_CREATED=0


    if [ ! -d "$CONFIG_DIR" ]; then

        log "No existing configuration directory found."

        return 0

    fi


    log "Backing up configuration..."


    rm -rf "$CONFIG_BACKUP"


    if ! cp -a "$CONFIG_DIR" "$CONFIG_BACKUP"; then

        error "Could not backup configuration."

        exit 1

    fi


    CONFIG_BACKUP_CREATED=1

    log "Configuration backup successful."
}


# =========================================================
# RESTORE CONFIGURATION
# =========================================================

restore_config()
{
    if [ "$CONFIG_BACKUP_CREATED" -ne 1 ]; then

        return 0

    fi


    if [ ! -d "$CONFIG_BACKUP" ]; then

        return 0

    fi


    log "Restoring configuration..."


    mkdir -p "$CONFIG_DIR"


    if cp -a "$CONFIG_BACKUP"/. "$CONFIG_DIR"/; then

        log "Configuration restored successfully."

        rm -rf "$CONFIG_BACKUP"

        CONFIG_BACKUP_CREATED=0

        return 0

    fi


    log "WARNING: Configuration restore failed."

    return 1
}


# =========================================================
# BACKUP CURRENT PLUGIN
# =========================================================

backup_plugin()
{
    PLUGIN_BACKUP_CREATED=0


    if [ ! -d "$PLUGIN_PATH" ]; then

        log "No existing plugin installation found."

        return 0

    fi


    log "Backing up current plugin..."


    rm -rf "$PLUGIN_BACKUP"


    if ! cp -a "$PLUGIN_PATH" "$PLUGIN_BACKUP"; then

        error "Could not backup current plugin."

        exit 1

    fi


    PLUGIN_BACKUP_CREATED=1

    log "Plugin backup successful."
}


# =========================================================
# ROLLBACK PLUGIN
# =========================================================

rollback_plugin()
{
    if [ "$PLUGIN_BACKUP_CREATED" -ne 1 ]; then

        log "No plugin backup available."

        return 1

    fi


    if [ ! -d "$PLUGIN_BACKUP" ]; then

        log "Plugin backup directory does not exist."

        return 1

    fi


    log "Rolling back previous plugin installation..."


    rm -rf "$PLUGIN_PATH"


    mkdir -p "$(dirname "$PLUGIN_PATH")"


    if cp -a "$PLUGIN_BACKUP" "$PLUGIN_PATH"; then

        log "Plugin rollback successful."

        return 0

    fi


    log "WARNING: Plugin rollback failed."

    return 1
}


# =========================================================
# INSTALL PLUGIN
# =========================================================

install_plugin()
{
    log "Installing speedy_TheWeather v$VERSION..."
    log "Target:"
    log "$PLUGIN_PATH"


    mkdir -p "$(dirname "$PLUGIN_PATH")"


    # -----------------------------------------------------
    # Remove old plugin
    # -----------------------------------------------------

    if [ -d "$PLUGIN_PATH" ]; then

        log "Removing old plugin..."

        if ! rm -rf "$PLUGIN_PATH"; then

            error "Could not remove old plugin."

            rollback_plugin
            exit 1

        fi

    fi


    # -----------------------------------------------------
    # Create new plugin directory
    # -----------------------------------------------------

    if ! mkdir -p "$PLUGIN_PATH"; then

        error "Could not create plugin directory."

        rollback_plugin
        exit 1

    fi


    # -----------------------------------------------------
    # Copy new plugin
    # -----------------------------------------------------

    log "Copying new plugin files..."


    if ! cp -a "$PLUGIN_SOURCE"/. "$PLUGIN_PATH"/; then

        error "Failed to copy plugin files."

        rollback_plugin
        exit 1

    fi


    # -----------------------------------------------------
    # Verify installation
    # -----------------------------------------------------

    if [ ! -f "$PLUGIN_PATH/__init__.py" ]; then

        error "Installation verification failed: __init__.py missing."

        rollback_plugin
        exit 1

    fi


    if [ ! -f "$PLUGIN_PATH/plugin.py" ]; then

        error "Installation verification failed: plugin.py missing."

        rollback_plugin
        exit 1

    fi


    # -----------------------------------------------------
    # Permissions
    # -----------------------------------------------------

    chmod -R 755 "$PLUGIN_PATH" 2>/dev/null || true


    log "Plugin installation successful."
}


# =========================================================
# VERIFY INSTALLED VERSION
# =========================================================

verify_installation()
{
    INSTALLED_VERSION=""


    if [ -f "$PLUGIN_PATH/__init__.py" ]; then

        INSTALLED_VERSION="$(
            grep -m 1 "__version__" "$PLUGIN_PATH/__init__.py" 2>/dev/null |
            sed -n 's/.*__version__[[:space:]]*=[[:space:]]*["'\'']\([^"'\'']*\)["'\''].*/\1/p'
        )"

    fi


    if [ -n "$INSTALLED_VERSION" ]; then

        log "Installed plugin version: $INSTALLED_VERSION"

    else

        log "WARNING: Could not determine installed plugin version."

    fi


    # -----------------------------------------------------
    # Required files
    # -----------------------------------------------------

    if [ ! -f "$PLUGIN_PATH/__init__.py" ] ||
       [ ! -f "$PLUGIN_PATH/plugin.py" ]; then

        error "Final installation verification failed."

        rollback_plugin
        exit 1

    fi


    log "Final installation verification successful."
}


# =========================================================
# REMOVE BACKUPS
# =========================================================

remove_backups()
{
    if [ -d "$PLUGIN_BACKUP" ]; then

        rm -rf "$PLUGIN_BACKUP"

    fi


    if [ -d "$CONFIG_BACKUP" ]; then

        rm -rf "$CONFIG_BACKUP"

    fi


    PLUGIN_BACKUP_CREATED=0
    CONFIG_BACKUP_CREATED=0
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

        if systemctl restart enigma2; then

            return 0

        fi

    fi


    if [ -x "/etc/init.d/enigma2" ]; then

        if /etc/init.d/enigma2 restart; then

            return 0

        fi

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
# SHOW SUCCESS
# =========================================================

show_success()
{
    echo
    echo "========================================================="
    echo " speedy_TheWeather update successful"
    echo "========================================================="
    echo
    echo "Version:"
    echo "$VERSION"
    echo
    echo "Plugin:"
    echo "$PLUGIN_PATH"
    echo
    echo "Repository:"
    echo "$REPOSITORY"
    echo
    echo "Branch:"
    echo "$BRANCH"
    echo
    echo "Changelog:"
    echo "$CHANGELOG"
    echo
    echo "========================================================="
    echo
}


# =========================================================
# MAIN
# =========================================================

echo
echo "========================================================="
echo " speedy_TheWeather GitHub Installer"
echo " Version $VERSION"
echo "========================================================="
echo


# =========================================================
# ROOT CHECK
# =========================================================

if [ "$(id -u)" -ne 0 ]; then

    error "This installer must be executed as root."

    exit 1

fi


# =========================================================
# DETECTION
# =========================================================

detect_plugin_path
detect_os
detect_image
detect_python


# =========================================================
# WGET
# =========================================================

check_wget


# =========================================================
# PREPARE
# =========================================================

cleanup

mkdir -p "$TMP_ROOT" || {

    error "Could not create temporary directory."

    exit 1

}


# =========================================================
# BACKUP
# =========================================================

backup_config
backup_plugin


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
# INSTALL
# =========================================================

install_plugin


# =========================================================
# RESTORE CONFIG
# =========================================================

restore_config


# =========================================================
# VERIFY
# =========================================================

verify_installation


# =========================================================
# CLEANUP
# =========================================================

cleanup


# =========================================================
# REMOVE BACKUPS
# =========================================================

remove_backups


# =========================================================
# SUCCESS
# =========================================================

show_success


# =========================================================
# RESTART
# =========================================================

restart_gui


exit 0
