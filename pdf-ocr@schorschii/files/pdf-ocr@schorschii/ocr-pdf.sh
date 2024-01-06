#!/bin/bash

(
  OUTPUT=""
  COUNTER=0
  for file in "$@"; do
    PERCENTAGE=$[$COUNTER * 100 / $#]
    echo "# $file" # update progress dialog text
    echo $PERCENTAGE # update progress dialog percentage
    RUN=$(ocrmypdf "$file" "$file.ocr.pdf" 2>&1)
    OUTPUT="$OUTPUT$RUN"$'\n\n'
    COUNTER=$[$COUNTER + 1]
  done
  /usr/bin/zenity --title="PDF OCR" --text-info --no-wrap --font=Monospace <<< $OUTPUT
) | /usr/bin/zenity --title="PDF OCR" --text="..." --progress --auto-close --no-cancel --percentage=0
