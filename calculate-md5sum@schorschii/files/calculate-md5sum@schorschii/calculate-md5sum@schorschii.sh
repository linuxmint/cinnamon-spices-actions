#! /bin/bash

TEXTDOMAIN="calculate-md5sum@schorschii"
TEXTDOMAINDIR="${HOME}/.local/share/locale"

TITLE="MD5SUM"
_BUSY=$"Calculating md5sum..."
BUSY="$(/usr/bin/gettext "$_BUSY")"

(
  HASH=$(/usr/bin/md5sum "$@")
  exec 1>&-
  /usr/bin/zenity --title="${TITLE}" --text-info --no-wrap --font=Monospace <<< ${HASH}
) | /usr/bin/zenity --title=MD5SUM --text="${BUSY}" --progress --auto-close --no-cancel --pulsate
