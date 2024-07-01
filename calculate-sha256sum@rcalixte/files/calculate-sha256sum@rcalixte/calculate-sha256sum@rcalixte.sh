#! /bin/bash

TEXTDOMAIN="calculate-sha256sum@rcalixte"
TEXTDOMAINDIR="${HOME}/.local/share/locale"
_BUSY=$"Calculating sha256sum for"
BUSY="$(/usr/bin/gettext "$_BUSY")"
BASENAME="$(/usr/bin/basename -a "$@" | /usr/bin/tr '\n' ' ')"
TITLE="SHA256SUM: ${BASENAME}"

(
  HASH=$(/usr/bin/sha256sum "$@")
  exec 1>&-
  /usr/bin/zenity --title="${TITLE}" --info --text="${HASH}" --no-wrap
) | /usr/bin/zenity --title="${BUSY}: ${BASENAME%% }..." --progress --auto-close --no-cancel --pulsate
