#!/bin/bash

(
  OUTPUT=""
  COUNTER=0
  # Create an array containing all languages supported by tesseract.
  # What we do:
  #   remove the first line: `List of available languages in "/usr/share/tesseract-ocr/5/tessdata/" (5):`
  #   remove "osd" (Orientation and Script Detection for languages not on this list) from the output
  #   remove trailing newline characters using the `-t` option of readarray
  readarray -t LANGUAGES < <(tesseract --list-langs | sed '1d' | sed '/osd/d')
  # Create a string such as `deu+eng` by replacing whitespaces with `+`.
  LANGUAGES=$(echo ${LANGUAGES[@]} | sed 's/\s/\+/g')
  for file in "$@"; do
    PERCENTAGE=$[$COUNTER * 100 / $#]
    echo "# $file" # update progress dialog text
    echo $PERCENTAGE # update progress dialog percentage
    RUN=$(ocrmypdf -l "$LANGUAGES" "$file" "$file.ocr.pdf" 2>&1)
    OUTPUT="$OUTPUT$RUN"$'\n\n'
    COUNTER=$[$COUNTER + 1]
  done
  /usr/bin/zenity --title="PDF OCR" --text-info --no-wrap --font=Monospace <<< $OUTPUT
) | /usr/bin/zenity --title="PDF OCR" --text="..." --progress --auto-close --no-cancel --percentage=0
