#!/bin/bash
# Take screenshots directly from the desktop
# @git:duracell80

# LOCALIZATION
TEXTDOMAIN="cinnamon-take-screenshot@duracell80"
TEXTDOMAINDIR="${HOME}/.local/share/locale"

_SCREENSHOT_APP_NOT_AVAILABLE=$"Screenshot app not available, exiting."
_SCREENSHOT_NOT_TAKEN=$"The screenshot was not taken!"

SCREENSHOT_APP_NOT_AVAILABLE=$(gettext "$_SCREENSHOT_APP_NOT_AVAILABLE")
SCREENSHOT_NOT_TAKEN=$(gettext "$_SCREENSHOT_NOT_TAKEN")


# ENVIRONMENT VARS
DIR_PWD=$(pwd)
DIR_AUTOSAVE=$(gsettings get org.gnome.gnome-screenshot auto-save-directory)

if [ "${DIR_AUTOSAVE}" = "''" ]; then
	PICTURES_DIR="${HOME}/Pictures"

	if command -v xdg-user-dir &> /dev/null ; then
		PICTURES_DIR=$(xdg-user-dir PICTURES)
	fi

	# FALL BACK
	DIR_TGT="$PICTURES_DIR/Screenshots"
else
	# USERS CHOICE
	DIR_TGT=$(echo "${DIR_AUTOSAVE}" | sed "s/'//g")
fi

if ! [ -d "${DIR_TGT}" ]; then
	mkdir -p "${DIR_TGT}"
fi


# ZENITY DOESN'T SEEM TO WORK WITHOUT THIS WHEN NOT USING ENGLISH
LANG=$(locale | grep LANGUAGE | cut -d= -f2 | cut -d_ -f1)
REGI=$(locale | grep LANGUAGE | cut -d= -f2)
if [ "${LANG}" = "" ]; then
	LANG="en"
fi
export LC_ALL="${REGI}.utf-8"
# END ZENITY


# IF GNOME SCREEN SHOT AVAILABLE - TODO SUPPORT OTHER NON MINT ENVIRONMENTS
# OFFER THE AREA SELECTION TOOL, SAVE DIRECTLY TO DIRECTORY AND OPEN IN PIX
if [[ $(command -v gnome-screenshot &> /dev/null; echo $?) -ne 0 ]]; then
    zenity --error --icon-name=security-high-symbolic --text="$SCREENSHOT_APP_NOT_AVAILABLE";
	exit 1
else
    # US Date format: 2024-01-21 16-27-09 = +%Y-%m-%d %H:%M
    # ELSE USE UNIVERSAL SECONDS FOR FILE NAME
    TS=$(date +%s)

    FILENAME="${DIR_TGT}/screenshot-auto_${TS}.png"

    gnome-screenshot --area --file="$FILENAME"

    if [[ ! -f "$FILENAME" ]]; then
		notify-send -i camera-photo-symbolic -u low "$SCREENSHOT_NOT_TAKEN"
        exit 1
    elif command -v pix &> /dev/null ; then
        pix "$FILENAME" &
    else
        xdg-open "$FILENAME" &
    fi
fi
