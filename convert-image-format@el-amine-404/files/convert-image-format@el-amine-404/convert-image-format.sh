#!/bin/bash

TEXTDOMAIN="convert-image-format@el-amine-404"
TEXTDOMAINDIR="${HOME}/.local/share/locale"
_TITLE=$"Convert Image(s) Format"
_PROMPT=$"Choose the format to convert the image(s) to:"
_COLUMN_1=$"Select"
_COLUMN_2=$"Format"
_COLUMN_3=$"Description"
_PROGRESS_TITLE=$"Converting Images"
_PROGRESS_TEXT=$"Processing..."
_NOT_AN_IMAGE=$"is not an image file and will be skipped"

TITLE="$(/usr/bin/gettext "$_TITLE")"
PROMPT="$(/usr/bin/gettext "$_PROMPT")"
COLUMN_1="$(/usr/bin/gettext "$_COLUMN_1")"
COLUMN_2="$(/usr/bin/gettext "$_COLUMN_2")"
COLUMN_3="$(/usr/bin/gettext "$_COLUMN_3")"
PROGRESS_TITLE="$(/usr/bin/gettext "$_PROGRESS_TITLE")"
PROGRESS_TEXT="$(/usr/bin/gettext "$_PROGRESS_TEXT")"
NOT_AN_IMAGE="$(/usr/bin/gettext "$_NOT_AN_IMAGE")"

if ! EXTENSION=$(
  /usr/bin/zenity --list --radiolist \
    --title="$TITLE" \
    --text="$PROMPT" \
    --column="$COLUMN_1" --column="$COLUMN_2" --column="$COLUMN_3" \
    FALSE "apng" "Animated Portable Network Graphics" \
    FALSE "avif" "AV1 Image File Format" \
    FALSE "bmp" "Bitmap" \
    FALSE "cur" "Microsoft Icon" \
    FALSE "gif" "Graphics Interchange Format" \
    FALSE "heic" "High Efficiency Image Coding" \
    FALSE "heif" "High Efficiency Image Format" \
    FALSE "ico" "Microsoft Icon" \
    FALSE "j2k" "JPEG 2000 Code Stream" \
    FALSE "jfi" "JPEG (Joint Photographic Experts Group)" \
    FALSE "jfif" "JPEG (Joint Photographic Experts Group)" \
    FALSE "jif" "JPEG (Joint Photographic Experts Group)" \
    FALSE "jp2" "JPEG 2000 Image" \
    FALSE "jpe" "JPEG (Joint Photographic Experts Group)" \
    FALSE "jpeg" "JPEG (Joint Photographic Experts Group)" \
    FALSE "jpg" "JPEG (Joint Photographic Experts Group)" \
    FALSE "pjp" "JPEG (Joint Photographic Experts Group)" \
    FALSE "pjpeg" "JPEG (Joint Photographic Experts Group)" \
    FALSE "pdf" "Portable Document Format" \
    FALSE "png" "Portable Network Graphics" \
    FALSE "svg" "plaintext Scalable Vector Graphics" \
    FALSE "svgz" "compressed Scalable Vector Graphics" \
    FALSE "tif" "Tagged Image File Format" \
    FALSE "tiff" "Tagged Image File Format" \
    FALSE "webp" "Web Picture format"
); then
  exit
fi

# i removed the raw formats bc as far as i know you can not convert from other formats
# to raw formats (the reverse operation is possible) right? RIGHT? 😢
# + raw, arw, cr, cr2, nef, orf, sr2, rw2, nrw, k25, 3fr
#
# other formats need a more complex script so i removed them from the selection:
# FALSE "eps" "Encapsulated PostScript" \
# FALSE "ai" "Adobe Illustrator Document" \
# FALSE "tga" "Targa Image File" \
# FALSE "hdr" "High Dynamic Range Image" \
# FALSE "pcx" "PC Paintbrush Bitmap Image" \
# FALSE "psd" "Photoshop Document" \

# directory where the generated image will be saved
DIRECTORY=$(dirname "$1")

convert_image() {
  local FILE="$1"
  if [[ "${FILE##*.}" == "psd" ]]; then
    /usr/bin/convert "${FILE}[0]" -set filename:basename "%[basename]" "${DIRECTORY}/%[filename:basename].${EXTENSION}"
  elif [[ "${FILE##*.}" == "gif" ]]; then
    /usr/bin/convert "$FILE" -set filename:basename "%[basename]" "${DIRECTORY}/%[filename:basename]_frame_%05d.${EXTENSION}"
  elif [[ "${FILE##*.}" == "svg" && ("$EXTENSION" == "eps" || "$EXTENSION" == "pdf" || "$EXTENSION" == "png" || "$EXTENSION" == "ps" || "$EXTENSION" == "svg") ]]; then
    /usr/bin/rsvg-convert --format="$EXTENSION" --output="${FILE%.*}.${EXTENSION}" "$FILE"
  else
    /usr/bin/convert "$FILE" -set filename:basename "%[basename]" "${DIRECTORY}/%[filename:basename].${EXTENSION}"
  fi
}

(
  if [ "$EXTENSION" == "gif" ]; then
    /usr/bin/convert -delay 20 -loop 0 "$@" "${DIRECTORY}/output.gif"
    exit 0
  fi
) | /usr/bin/zenity --progress \
  --title="$PROGRESS_TITLE" \
  --text="$PROGRESS_TEXT" \
  --pulsate \
  --auto-close

if [ "$EXTENSION" == "gif" ]; then
  exit 0
fi

(
  TOTAL_FILES=$#
  COUNT=0
  for FILE in "$@"; do
    MIMETYPE=$(/usr/bin/file --mime-type -b "$FILE")
    if [[ $MIMETYPE == image/* ]]; then
      convert_image "$FILE"
      COUNT=$((COUNT + 1))
      echo "$((COUNT * 100 / TOTAL_FILES))"
      echo "# Converting $FILE ($COUNT of $TOTAL_FILES)"
    else
      /usr/bin/zenity --warning --text="$FILE $NOT_AN_IMAGE."
    fi
  done
) | /usr/bin/zenity --progress \
  --title="$PROGRESS_TITLE" \
  --text="$PROGRESS_TEXT" \
  --percentage=0 \
  --auto-close
