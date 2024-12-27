#!/bin/bash
#
######################################################
# PDF Cut by ernemir, based on work by ScarletEmanu #
######################################################
#
#
TEXTDOMAINDIR=$HOME/.local/share/locale/
TEXTDOMAIN=pdf-cut@ernemir

_TITLE=$"PDF Cut"
TITLE="$(/usr/bin/gettext "$_TITLE")"
_TEXT=$"Enter page range"
TEXT="$(/usr/bin/gettext "$_TEXT")"
_FROM=$"From:"
FROM="$(/usr/bin/gettext "$_FROM")"
_TO=$"To:"
TO="$(/usr/bin/gettext "$_TO")"
_RANGE_ERROR=$"Invalid range"
RANGE_ERROR="$(/usr/bin/gettext "$_RANGE_ERROR")"
_NUMBER_ERROR=$"You must enter numbers"
NUMBER_ERROR="$(/usr/bin/gettext "$_NUMBER_ERROR")"

# Ask for page range
data=$(zenity --forms \
               --title="$TITLE" \
               --text="$TEXT" \
               --add-entry="$FROM" \
               --add-entry="$TO")
ans=$?
if [ $ans -eq 0 ]
then
    IFS="|" read -r -a array <<< "$data"
    if [[ ${array[0]} =~ ^[0-9]+$ ]] && [[ ${array[1]} =~ ^[0-9]+$ ]]; then
        if [[ ! ${array[0]} -gt ${array[1]} ]]; then
            output="${1%.*}_cut.pdf"
            gs -sDEVICE=pdfwrite -dNOPAUSE -dBATCH -dSAFER -dFirstPage="${array[0]}" -dLastPage="${array[1]}" -sOutputFile="$output" "$1"
        else
            zenity --error --text "$RANGE_ERROR"
        fi
    else
        zenity --error --text "$NUMBER_ERROR"
    fi
fi