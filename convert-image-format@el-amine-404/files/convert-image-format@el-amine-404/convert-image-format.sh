#!/bin/bash

TEXTDOMAIN="convert-image-format@el-amine-404"
TEXTDOMAINDIR="${HOME}/.local/share/locale"

# Images

_IMAGE__TITLE=$"Convert Image(s) Format"
_IMAGE__PROMPT=$"Choose the format to convert the image(s) to:"
_IMAGE__COLUMN_1=$"Select"
_IMAGE__COLUMN_2=$"Format"
_IMAGE__COLUMN_3=$"Description"

_PROGRESS_TITLE=$"Converting Images"
_PROGRESS_TEXT=$"Processing..."
_NOT_AN_IMAGE=$"is not an image file and will be skipped"

IMAGE__TITLE="$(/usr/bin/gettext "$_IMAGE__TITLE")"
IMAGE__PROMPT="$(/usr/bin/gettext "$_IMAGE__PROMPT")"
IMAGE__COLUMN_1="$(/usr/bin/gettext "$_IMAGE__COLUMN_1")"
IMAGE__COLUMN_2="$(/usr/bin/gettext "$_IMAGE__COLUMN_2")"
IMAGE__COLUMN_3="$(/usr/bin/gettext "$_IMAGE__COLUMN_3")"

PROGRESS_TITLE="$(/usr/bin/gettext "$_PROGRESS_TITLE")"
PROGRESS_TEXT="$(/usr/bin/gettext "$_PROGRESS_TEXT")"
NOT_AN_IMAGE="$(/usr/bin/gettext "$_NOT_AN_IMAGE")"

# PDF

_PDF__TITLE=$"PDF to Image Conversion"
_PDF__PROMPT=$"Enter the required details for conversion.\n\nNote: Leaving fields empty will apply default values."
_PDF__COMBO_LABEL=$"Format (default: png)"
_PDF__COMBO_VALUES="png|jpg|tiff"
_PDF__ENTRY_1=$"Resolution / DPI (default: 300)"
_PDF__ENTRY_2=$"First Page (default: 1)"
_PDF__ENTRY_3=$"Last Page (default: last page of document)"

PDF__TITLE="$(/usr/bin/gettext "$_PDF__TITLE")"
PDF__PROMPT="$(/usr/bin/gettext "$_PDF__PROMPT")"
PDF__COMBO_LABEL="$(/usr/bin/gettext "$_PDF__COMBO_LABEL")"
PDF__COMBO_VALUES="$(/usr/bin/gettext "$_PDF__COMBO_VALUES")"
PDF__ENTRY_1="$(/usr/bin/gettext "$_PDF__ENTRY_1")"
PDF__ENTRY_2="$(/usr/bin/gettext "$_PDF__ENTRY_2")"
PDF__ENTRY_3="$(/usr/bin/gettext "$_PDF__ENTRY_3")"

_NOT_A_PDF=$"is not a valid PDF file and will be skipped"
_NOT_A_VALID_FORMAT=$"Unsupported format. Possible values are: png(default), jpeg, tiff"

NOT_A_PDF="$(/usr/bin/gettext "$_NOT_A_PDF")"
NOT_A_VALID_FORMAT="$(/usr/bin/gettext "$_NOT_A_VALID_FORMAT")"

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

# full path to the selected file
FILE="$1"
# directory where the generated image will be saved
DIRECTORY=$(dirname "$1")

convert_image() {

  if ! EXTENSION=$(
    /usr/bin/zenity --list --radiolist \
      --title="$IMAGE__TITLE" \
      --text="$IMAGE__PROMPT" \
      --height=320 \
      --width=640 \
      --column="$IMAGE__COLUMN_1" --column="$IMAGE__COLUMN_2" --column="$IMAGE__COLUMN_3" \
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

convert_pdf() {

  if [ -z "$1" ]; then
    echo "Error: File argument is required."
    return 1
  fi

  if ! PDF_INFO=$(
    /usr/bin/zenity --forms \
      --title="$PDF__TITLE" \
      --text="$PDF__PROMPT" \
      --add-combo="$PDF__COMBO_LABEL" --combo-values="$PDF__COMBO_VALUES" \
      --add-entry="$PDF__ENTRY_1" \
      --add-entry="$PDF__ENTRY_2" \
      --add-entry="$PDF__ENTRY_3" \
      --separator="|"
  ); then
    exit
  fi

  local file="$1"

  # Parse the information returned from zenity
  # xargs is used to strip whitespace :)
  format=$(echo "$PDF_INFO" | cut -d "|" -f1 | xargs)
  resolution=$(echo "$PDF_INFO" | cut -d "|" -f2 | xargs)
  firstpage=$(echo "$PDF_INFO" | cut -d "|" -f3 | xargs)
  lastpage=$(echo "$PDF_INFO" | cut -d "|" -f4 | xargs)

  # Set default values if arguments are not provided
  format="${format:-png}"
  resolution="${resolution:-300}"
  firstpage="${firstpage:-1}"
  # Calculate last page if not provided
  if [ -z "$lastpage" ]; then
    lastpage=$(pdfinfo "$file" | grep '^Pages:' | awk '{print $2}')
  fi

  # Create directory based on the filename
  # directory where the generated image will be saved
  FILE_NAME=$(basename "$file" .pdf)

  [ ! -d "${DIRECTORY}/images_${FILE_NAME}" ] && mkdir -pv "${DIRECTORY}/images_${FILE_NAME}"

  # Determine format options based on provided format
  case "$format" in
  "jpg") format_options="-jpeg" ;;
  "png") format_options="-png" ;;
  "tiff") format_options="-tiff" ;;
  *)
    /usr/bin/zenity --warning --text="$NOT_A_VALID_FORMAT"
    return 1
    ;;
  esac

  pdftoppm \
    "${format_options}" \
    -forcenum \
    -sep _ \
    -r "$resolution" \
    -f "$firstpage" \
    -l "$lastpage" \
    "$file" \
    "${DIRECTORY}/images_${FILE_NAME}/pg"

}

(
  if [ "$EXTENSION" == "gif" ]; then
    /usr/bin/convert -delay 20 -loop 0 "$@" "${DIRECTORY}/output.gif"
    exit 0
  fi
) | /usr/bin/zenity --progress \
  --title="$IMAGE__PROGRESS_TITLE" \
  --text="$IMAGE__PROGRESS_TEXT" \
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
    elif [[ $MIMETYPE == application/pdf ]]; then
      convert_pdf "$FILE"
      COUNT=$((COUNT + 1))
      echo "$((COUNT * 100 / TOTAL_FILES))"
      echo "# Converting $FILE ($COUNT of $TOTAL_FILES)"
    else
      [[ $MIMETYPE == image/* ]] && /usr/bin/zenity --warning --text="$FILE $NOT_AN_IMAGE."
      [[ $MIMETYPE == application/pdf ]] && /usr/bin/zenity --warning --text="$FILE $NOT_A_PDF."
    fi
  done
) | /usr/bin/zenity --progress \
  --title="$PROGRESS_TITLE" \
  --text="$PROGRESS_TEXT" \
  --percentage=0 \
  --auto-close
