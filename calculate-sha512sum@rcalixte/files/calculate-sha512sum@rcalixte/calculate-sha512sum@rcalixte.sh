#! /bin/bash

TEXTDOMAIN="calculate-sha512sum@rcalixte"
TEXTDOMAINDIR="${HOME}/.local/share/locale"
_BUSY=$"Calculating sha512sum for"
BUSY="$(/usr/bin/gettext "$_BUSY")"
BASENAME="$(/usr/bin/basename -a "$@" | /usr/bin/tr '\n' ' ')"
TITLE="SHA512SUM: ${BASENAME}"

(
  HASH=$(/usr/bin/sha512sum "$@")
  exec 1>&-
  /usr/bin/zenity --title="${TITLE}" --info --text="${HASH}" --no-wrap
) | /usr/bin/zenity --title="${BUSY}: ${BASENAME%% }..." --progress --auto-close --no-cancel --pulsate
