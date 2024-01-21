#!/bin/bash
# Take screenshots directly from the desktop
# @git:duracell80


# ENVIRONMENT VARS
LANG="en"
DIR_PWD=$(pwd)
DIR_TGT="${HOME}/Pictures/screenshots"

if ! [ -d "${DIR_TGT}" ]; then
    mkdir -p "${DIR_TGT}"
fi




# READ THE LANGUAGE FILE
if [[ "${PWD,,}" == "${HOME}" ]]; then
	DIR_APP="${HOME}/.local/share/nemo/actions/cinnamon-take-screenshot@duracell80"
else
	DIR_APP="${PWD}"
fi

LANG=$(locale | grep LANGUAGE | cut -d= -f2 | cut -d_ -f1)
REGI=$(locale | grep LANGUAGE | cut -d= -f2)
if [ "${LANG}" = "" ]; then
	LANG="en"
fi

if [ "${REGI}" = "" ]; then
        REGI="US"
fi

# FRENCH
if [ "${LANG,,}" = "fr" ]; then
	export LC_ALL="fr_FR.utf-8"
# SPANISH
elif [ "${LANG,,}" = "es" ]; then
        export LC_ALL="es_ES.utf-8"
# PORTUGUESE - BRAZIL
elif [ "${REGI,,}" = "pt_br" ]; then
        export LC_ALL="pt_BR.utf-8"
	    LANG="pt"
# PORTUGUESE
elif [ "${LANG,,}" = "pt" ]; then
        export LC_ALL="pt_PT.utf-8"        
# GERMAN
elif [ "${LANG,,}" = "de" ]; then
        export LC_ALL="de_DE.utf-8"
# ITALIAN
elif [ "${LANG,,}" = "it" ]; then
        export LC_ALL="it_IT.utf-8"
# DANISH
elif [ "${LANG,,}" = "da" ]; then
        export LC_ALL="da_DK.utf-8"
# FINNISH
elif [ "${LANG,,}" = "fi" ]; then
        export LC_ALL="fi_FI.utf-8"
# NORWEGIAN NYNORSK
elif [ "${LANG,,}" = "nn" ]; then
        export LC_ALL="nn_NO.utf-8"
        LANG_INS="installed"
# HUNGARIAN
elif [ "${LANG,,}" = "hu" ]; then
        export LC_ALL="hu_HU.utf-8"
# TURKISH
elif [ "${LANG,,}" = "tr" ]; then
        export LC_ALL="tr_TR.utf-8"
# RUSSIAN
elif [ "${LANG,,}" = "ru" ]; then
        export LC_ALL="ru_RU.utf-8"
# ENGLISH
elif [ "${LANG,,}" = "en" ]; then
    export LC_ALL="en_GB.utf-8"
else
	export LC_ALL="en_US.utf-8"
fi


if [ -f "${DIR_APP}/po-sh/lang_${LANG,,}.txt" ]; then
	while read line
	do
   		IFS=';' read -ra col <<< "$line"
		suffix="${col[0]}"
		declare $suffix="${col[1]}"
	done < "${DIR_APP}/po-sh/lang_${LANG,,}.txt"
else
	#XT-EN
	LAN00="Screenshot app not available, exiting."
fi





# IF GNOME SCREEN SHOT AVAILABLE - TODO SUPPORT OTHER NON MINT ENVIRONMENTS
# OFFER THE AREA SELECTION TOOL, SAVE DIRECTLY TO PICTURES AND OPEN IN PIX
if [[ $(compgen -c | grep -iw 'gnome-screenshot' | head -n1 | wc -l) == "0" ]]; then
    zenity --error --icon-name=security-high-symbolic --text="${LAN00}";
else
    TS=$(date +%s)
    gnome-screenshot --area --file="${DIR_TGT}/screenshot_${TS}.png"
    if [[ $(compgen -c | grep -iw 'pix' | head -n1 | wc -l) == "0" ]]; then
        exit
    else
        pix "${DIR_TGT}/screenshot_${TS}.png" &
    fi
fi
