#!/bin/bash
# Take screenshots directly from the desktop
# @git:duracell80


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



# READ THE LANGUAGE FILE FOR THE ERROR MESSAGE
# IF SCREENSHOT APP NOT AVAILABLE, MISSING DEPS MIGHT PREVENT MENU ITEM FROM SHOWING
if [[ "${PWD,,}" == "${HOME,,}" ]]; then
	DIR_APP="${HOME}/.local/share/nemo/actions/cinnamon-take-screenshot@duracell80"
else
	DIR_APP="${PWD}"
fi



# ZENITY DOESN'T SEEM TO WORK WITHOUT THIS WHEN NOT USING ENGLISH
LANG=$(locale | grep LANGUAGE | cut -d= -f2 | cut -d_ -f1)
REGI=$(locale | grep LANGUAGE | cut -d= -f2)
if [ "${LANG}" = "" ]; then
	LANG="en"
fi
export LC_ALL="${REGI}.utf-8"
# END ZENITY


if [ -f "${DIR_APP}/po-sh/lang_${LANG,,}.txt" ]; then
	while read line
	do
   		IFS=';' read -ra col <<< "$line"
		suffix="${col[0]}"
		declare $suffix="${col[1]}"
	done < "${DIR_APP}/po-sh/lang_${LANG,,}.txt"
else
	#FALL BACK ON EN
	LAN00="Screenshot app not available, exiting."
fi







# IF GNOME SCREEN SHOT AVAILABLE - TODO SUPPORT OTHER NON MINT ENVIRONMENTS
# OFFER THE AREA SELECTION TOOL, SAVE DIRECTLY TO DIRECTORY AND OPEN IN PIX
if [[ $(compgen -c | grep -iw 'gnome-screenshot' | head -n1 | wc -l) == "0" ]]; then
    zenity --error --icon-name=security-high-symbolic --text="${LAN00}";
else
    # US Date format: 2024-01-21 16-27-09 = +%Y-%m-%d %H:%M
    # ELSE USE UNIVERSAL SECONDS FOR FILE NAME
    TS=$(date +%s)

   gnome-screenshot --area --file="${DIR_TGT}/screenshot-auto_${TS}.png"
    if [[ $(compgen -c | grep -iw 'pix' | head -n1 | wc -l) == "0" ]]; then
        exit
    else
        pix "${DIR_TGT}/screenshot-auto_${TS}.png" &
    fi
fi
