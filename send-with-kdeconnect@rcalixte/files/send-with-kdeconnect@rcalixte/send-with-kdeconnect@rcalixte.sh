#! /bin/bash

TEXTDOMAIN="send-with-kdeconnect@rcalixte"
TEXTDOMAINDIR="${HOME}/.local/share/locale"
_TITLE=$"File(s) to send"
_TEXT=$"Select the target device"
_COLUMN=$"Device Name"
_NODEVICES=$"No devices available.\n\nPlease check KDE Connect and try again."
TITLE="$(/usr/bin/gettext "$_TITLE")"
TEXT="$(/usr/bin/gettext "$_TEXT")"
COLUMN="$(/usr/bin/gettext "$_COLUMN")"
NODEVICES="$(/usr/bin/gettext "$_NODEVICES")"

declare -A DEVICEMAP

while IFS=' ' read -r value key; do
  DEVICEMAP[$key]=$value;
done <<< $(/usr/bin/kdeconnect-cli --id-name-only --list-available 2>/dev/null)

[[ ${#DEVICEMAP[@]} -eq 0 ]] && /usr/bin/zenity --error --text="${NODEVICES}" && exit 1

SELECTION=$(/usr/bin/zenity --list --title "${TITLE}" --column "${COLUMN}" --text "${TEXT}:" "${!DEVICEMAP[@]}")

[[ -z $SELECTION ]] && exit

for filename in "$@"; do
  /usr/bin/kdeconnect-cli --device "${DEVICEMAP[$SELECTION]}" --share "${filename}"
done;
