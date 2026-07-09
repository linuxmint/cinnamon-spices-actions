#!/bin/bash
# Manual smoke test (not used by Nemo). Run from a terminal.

for cmd in adb emulator zenity; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Missing: $cmd" >&2
        exit 1
    fi
done

device_list=$(adb devices 2>/dev/null | awk 'NR>1 && $2 == "device" { print $1 }')
emulator_list=$(
    emulator -list-avds 2>/dev/null | awk '
        NF == 1 && $0 !~ /\|/ && $1 !~ /^(INFO|WARNING|ERROR|DEBUG|I\/)/ { print $1 }
    ' | sed '/^[[:space:]]*$/d'
)

combined_list=$(printf '%s\n%s\n' "$device_list" "$emulator_list" | sed '/^$/d' | sort -u)

if [ -z "$combined_list" ]; then
    zenity --info --text="No devices or AVDs available"
    exit 0
fi

readarray -t rows < <(printf '%s\n' "$combined_list")

selected_item=$(zenity --list --title="ADB Devices and Emulators" --column="ID" "${rows[@]}") || exit 0

if [ -z "$selected_item" ]; then
    exit 0
fi

zenity --info --text="Selected: $selected_item"
