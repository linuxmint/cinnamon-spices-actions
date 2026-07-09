#!/bin/bash

show_error() {
    local text=$1
    if command -v zenity >/dev/null 2>&1; then
        zenity --error --width=480 --text="$text"
    else
        printf '%s\n' "$text" >&2
    fi
}

check_dependencies() {
    local missing=()
    command -v adb >/dev/null 2>&1 || missing+=("adb (Android SDK platform-tools)")
    command -v emulator >/dev/null 2>&1 || missing+=("emulator (Android SDK emulator)")
    command -v zenity >/dev/null 2>&1 || missing+=("zenity")

    if ((${#missing[@]})); then
        local msg
        msg=$(
            printf '%s\n' "Missing required programs:" ""
            printf '%s\n' "${missing[@]}" | sed 's/^/• /'
            printf '%s\n' "" "Install the Android SDK (or command-line tools) and add platform-tools" "and the emulator to your PATH (see README)."
        )
        show_error "$msg"
        exit 1
    fi
}

check_apk_readable() {
    local f=$1
    if [ ! -f "$f" ]; then
        show_error "File not found:\n$f"
        exit 1
    fi
    if [ ! -r "$f" ]; then
        show_error "Cannot read file:\n$f"
        exit 1
    fi
}

# Fake progress bar to indicate to the user that something is happening.
# it will increase every 0.2 seconds until the installation is complete.
# the max value is 95% and if the process finishes earlier, it will jump to 100%
# and then display the sucess message.
run_adb_install_with_progress() {
    local apk_path=$1
    shift

    local out zrc adb_rc log

    out=$(mktemp) || return 1

    (
        "$@" >"$out" 2>&1 &
        local pid=$!
        trap 'kill -9 "$pid" 2>/dev/null' EXIT

        echo "0"
        echo "# Installing $(basename "$apk_path")…"

        local p=0
        while kill -0 "$pid" 2>/dev/null; do
            p=$((p + 2))
            if [ "$p" -gt 95 ]; then
                p=95
            fi
            echo "$p"
            sleep 0.2
        done

        wait "$pid"
        adb_rc_inner=$?
        trap - EXIT
        echo "$adb_rc_inner" >"${out}.rc"

        echo "100"
        echo "# Completing…"
    ) | zenity --progress \
        --title="Installing $(basename "$apk_path")" \
        --width=480 \
        --percentage=0 \
        --auto-close \
        --auto-kill

    zrc=$?
    adb_rc=$(cat "${out}.rc" 2>/dev/null || echo 1)
    log=$(cat "$out" 2>/dev/null)
    rm -f "$out" "${out}.rc"

    # User closed the progress window (cancel)
    if [ "$zrc" -ne 0 ]; then
        exit 0
    fi

    if [ "$adb_rc" -ne 0 ] || [[ "$log" == *"Failure"* ]]; then
        show_error "Installation failed for $(basename "$apk_path"):\n\n$log"
        exit 1
    fi
    return 0
}

install_apks_on_serial() {
    local serial=$1
    shift
    local apk n=$#

    for apk in "$@"; do
        check_apk_readable "$apk"
        run_adb_install_with_progress "$apk" adb -s "$serial" install -r "$apk"
    done

    if [ "$n" -gt 1 ]; then
        zenity --info --width=380 --text="All $n APKs were installed successfully."
    else
        zenity --info --width=360 --text="APK installed successfully."
    fi
}

install_apks_on_emulator() {
    local apk n=$#

    for apk in "$@"; do
        check_apk_readable "$apk"
        run_adb_install_with_progress "$apk" adb -e install -r "$apk"
    done

    if [ "$n" -gt 1 ]; then
        zenity --info --width=380 --text="All $n APKs were installed successfully."
    else
        zenity --info --width=360 --text="APK installed successfully."
    fi
}

wait_for_emulator_boot() {
    local timeout=${1:-300}
    local elapsed=0
    while ((elapsed < timeout)); do
        if adb -e shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' | grep -qx 1; then
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    return 1
}

# --- main ---

check_dependencies

if [ "$#" -eq 0 ]; then
    show_error "No APK file was passed to this action."
    exit 1
fi

device_list=$(adb devices 2>/dev/null | awk 'NR>1 && $2 == "device" { print $1 }' | sed '/^$/d' || true)

# emulator -list-avds may print INFO/diagnostics on stdout (e.g. crashdata paths).
# Keep only single-token lines that look like AVD names, not log lines.
emulator_list=$(
    emulator -list-avds 2>/dev/null | awk '
        NF == 1 && $0 !~ /\|/ && $1 !~ /^(INFO|WARNING|ERROR|DEBUG|I\/)/ { print $1 }
    ' | sed '/^[[:space:]]*$/d' || true
)

combined_list=$(printf '%s\n%s\n' "$device_list" "$emulator_list" | sed '/^$/d' | sort -u)

if [ -z "$combined_list" ]; then
    zenity --info --width=420 --text="No devices or AVDs available.\n\nConnect a device (USB debugging) or create an AVD in Android Studio."
    exit 0
fi

readarray -t rows < <(printf '%s\n' "$combined_list")

selected=$(zenity --width=400 --list --title="ADB Devices and Emulators" \
    --column="Device or AVD" "${rows[@]}") || exit 0

if [ -z "$selected" ]; then
    exit 0
fi

if printf '%s\n' "$device_list" | grep -Fxq "$selected"; then
    install_apks_on_serial "$selected" "$@"
else
    emulator -avd "$selected" >/dev/null 2>&1 &
    if ! adb wait-for-device 2>/dev/null; then
        show_error "Timed out waiting for a device from adb."
        exit 1
    fi
    if ! wait_for_emulator_boot 300; then
        show_error "The emulator did not finish booting in time."
        exit 1
    fi
    install_apks_on_emulator "$@"
fi
