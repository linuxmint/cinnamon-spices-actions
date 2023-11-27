#! /bin/bash

TEXTDOMAIN="calculate-sha256sum@rcalixte"
TEXTDOMAINDIR="${HOME}/.local/share/locale"
FILENAME="$1"
BASENAME="$(/usr/bin/basename "$FILENAME")"
TITLE="SHA256SUM: ${BASENAME}"
_BUSY=$"Calculating sha256sum for"
BUSY="$(/usr/bin/gettext "$_BUSY")"

(
  HASH=$(/usr/bin/sha256sum "${FILENAME}" | /usr/bin/cut -f1 -d' ')
  exec 1>&-
  /usr/bin/zenity --title="${TITLE}" --info --text="${HASH}" --no-wrap
) | /usr/bin/zenity --title="${BUSY} ${FILENAME}..." --progress --auto-close --no-cancel --pulsate
