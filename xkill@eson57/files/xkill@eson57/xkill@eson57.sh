#!/usr/bin/bash

TEXTDOMAIN="xkill@eson57"
TEXTDOMAINDIR="${HOME}/.local/share/locale"
_TEXT=$"Click on the application that you want to kill."
TEXT="$(/usr/bin/gettext "$_TEXT")"
_ONCE=$"This instruction for XKill will not be shown again."
ONCE="$(/usr/bin/gettext "$_ONCE")"

KILLDONE=~/.local/share/nemo/actions/xkill@eson57/.killdone

if [ ! -e $KILLDONE ]
then
zenity --info --title="XKill" --text="${TEXT}"
echo "${ONCE}" > $KILLDONE
fi
sleep 1
xkill
