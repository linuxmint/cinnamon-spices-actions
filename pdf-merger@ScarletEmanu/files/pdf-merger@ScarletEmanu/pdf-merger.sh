#!/bin/bash
#
######################################################
# PDF Merger by ScarletEmanu, based on work by Alfcx #
######################################################
#
dir=`dirname "$1"` ;
#

# Ask for the Name of the output file
_TITLE=$"Name the Output File"
TITLE="$(/usr/bin/gettext "$_TITLE")"
_TEXT=$"The input files will be united in alphabetical order into one output file.\nEnter the name of the output file here (without the extension .pdf)" 
TEXT="$(/usr/bin/gettext "$_TEXT")"
if ! OUTPUTNAME=$(zenity --entry \
  --title="$TITLE" \
  --text="$TEXT" \
  --width=300) ; then
  exit;
fi ;
# 

# Merge the files
pdftk "$@" cat output "$dir/$OUTPUTNAME.pdf" ;
#
