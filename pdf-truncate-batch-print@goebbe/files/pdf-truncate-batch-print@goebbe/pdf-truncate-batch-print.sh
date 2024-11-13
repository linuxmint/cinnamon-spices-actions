#!/bin/bash

# Required packages on Debian based distributions: cups poppler-utils zenity
# sudo apt install cups poppler-utils zenity

# After installation this file should be in .local/share/nemo/actions/pdf-truncate-batch-print.sh
# This .sh-file has to be executable. 

# Usage: 
# 1. Select one or more PDF(s), right click, select: Truncate and mass-print PDF(s)
# 2. Choose the number of pages to be truncated. E.g. if you do not want the first page 
# and the last two pages to be printed for all selected files, then 
# set "# of pages cut at the start:" to 1 and "# of pages cut from the end:" to 2. 
# 3. Choose the printer and between one-sided and two-sided printing.
# The same truncation will be applied to all pdfs during the mass print. 

# This action could be convenient for batch-printing pdf(s) that e.g. all start 
# with the same cover-letter and end with two pages of small print. 

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>. 

## terminate script at the first nonzero exit code - make cancel in the first two dialogs terminate
set -e

## Text strings for zenity dialogs (translation friendly)
_TITLE=$"Truncate PDF-printing"
TITLE="$(/usr/bin/gettext "$_TITLE")"

#############################################
## 1. Choose number of pages to be truncated:
#############################################
_TEXT1=$"Number of pages that should NOT be printed.\n \
Empty fields result in no truncation."
TEXT1="$(/usr/bin/gettext "$_TEXT1")"

_ENTRY1=$"Number of pages cut at the start:"
ENTRY1="$(/usr/bin/gettext "$_ENTRY1")"

_ENTRY2=$"Number of pages cut from the end:"
ENTRY2="$(/usr/bin/gettext "$_ENTRY2")"

leftrighttrunc="$( \
    zenity --forms --title="$TITLE" \
    --width=300 --height=300 \
	--text="$TEXT1" \
	--separator="," \
	--add-entry="$ENTRY1" \
	--add-entry="$ENTRY2" \
    )"

## Seperate the two numbers from $leftrighttrunc
lefttrunc=$(echo $leftrighttrunc | awk -F "," '{print $1}')
righttrunc=$(echo $leftrighttrunc | awk -F "," '{print $2}')

## If the truncate variables are empty: set their values to 0:
lefttrunc=${lefttrunc:=0}
righttrunc=${righttrunc:=0}

## if $lefttrunc or $righttrunc are not positive integers print an error message and exit
if [[ ! "$lefttrunc" =~ ^[0-9]+$ ]] || [[ ! "$righttrunc" =~ ^[0-9]+$ ]] ; then 
  zenity --error --text="The number of pages have to be zero or positive integers"; exit 1
fi

#############################################
## 2. Choose the printer:
#############################################
_TEXT2=$"Select a printer for batch-printing"
TEXT2="$(/usr/bin/gettext "$_TEXT2")"

_COLUMN=$"Printers:"
COLUMN="$(/usr/bin/gettext "$_COLUMN")"

## printernames is an array with the names of all available printers: 
readarray -t printernames < <( lpstat -p | awk '$1=="printer" {print $2}')

myprinter="$( \
    zenity --list --title="$TITLE" \
    --width=300 --height=300 \
    --text="$TEXT2" \
    --column="$COLUMN" \
    "${printernames[@]}" \
    )"

## If $myprinter is empty: set $myprinter to the default printer:
defaultprinter=$(lpstat -d | awk '{print $4}')
myprinter=${myprinter:="$defaultprinter"}

#############################################
## 3. Choose between one-sided and two-sided printing:
#############################################

_TEXT3=$" <b>Summary:</b> \n \
Number of pages cut at the start: $lefttrunc \n \
Number of pages cut from the end: $righttrunc \n \
Printer: $myprinter \n \n \
Choose one-sided or two-sided printing  \n \n \
<b>Batch-printing will start instantly! </b>"
TEXT3="$(/usr/bin/gettext "$_TEXT3")"

_BUTTON_ONE=$"one-sided"
BUTTON_ONE="$(/usr/bin/gettext "$_BUTTON_ONE")"

_BUTTON_CANCEL=$"Cancel"
BUTTON_CANCEL="$(/usr/bin/gettext "$_BUTTON_CANCEL")"

_BUTTON_TWO=$"two-sided"
BUTTON_TWO="$(/usr/bin/gettext "$_BUTTON_TWO")"

# unset exit on error for the following dialog
set +e

msides="$( \
    zenity --question --title="$TITLE" \
    --width=300 --height=300 \
    --text="$TEXT3" \
    --switch \
    --extra-button "$BUTTON_ONE" \
    --extra-button "$BUTTON_CANCEL" \
    --extra-button "$BUTTON_TWO" \
    )"

if [ "$msides" = "$BUTTON_ONE" ]; then mysides="one-sided"
elif [ "$msides" = "$BUTTON_TWO" ]; then mysides="two-sided-long-edge"
else exit 1
fi

## Debug: Uncomment the following line to check if the variables are generated correctly: 
#echo "$lefttrunc" "$righttrunc" "$myprinter" "$msides" "$mysides" > ~/test2.txt

#############################################
## 4. Mass print the pdf(s) applying left- and righttruncation to each pdf: 
#############################################
echo "$@" | while read -r file
do
    ## npage is the total number of pages:
    numpages=$(pdfinfo "$file" | awk '/^Pages:/ {print $2}')
    ## firstp is the first page to be printed: 
    firstp=$(("$lefttrunc"+1))
    ## lastp is the last page to be printed: 
    lastp=$(("$numpages"-"$righttrunc"))
    # only print if there is at least one page to print:
    if (( (lpage-fpage) > -1 )); then
      lpr -o sides="$mysides" -o ColorModel=Gray -o page-ranges="$firstp"-"$lastp" -P "$myprinter" "$file"
    fi
done

exit 0

## EOF
