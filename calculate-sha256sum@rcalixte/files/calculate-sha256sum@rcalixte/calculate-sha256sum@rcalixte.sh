#! /bin/bash

FILENAME="$1"
BASENAME="$(/usr/bin/basename "$FILENAME")"
TITLE="SHA256SUM FOR ${BASENAME}"

(
  HASH=$(/usr/bin/sha256sum "${FILENAME}" | /usr/bin/cut -f1 -d' ')
  exec 1>&-
  /usr/bin/zenity --title="${TITLE}" --info --text="${HASH}" --no-wrap
) | /usr/bin/zenity --title="Calculating sha256sum for ${FILENAME}..." --progress --auto-close --no-cancel --pulsate
