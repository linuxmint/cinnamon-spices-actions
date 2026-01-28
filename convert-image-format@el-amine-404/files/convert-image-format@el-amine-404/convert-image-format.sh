#!/bin/bash

TEXTDOMAIN="convert-image-format@el-amine-404"
TEXTDOMAINDIR="${HOME}/.local/share/locale"

ERR_LOG=$(mktemp)

# shellcheck disable=SC2329
cleanup() {
    rm -f "$ERR_LOG"
}
trap cleanup EXIT

# ----------------------------------------------------------------------------------------
# SECTION A: LOCALIZATION STRINGS/KEYS
# ----------------------------------------------------------------------------------------

# --- Image Context ---
_IMAGE__TITLE=$"Convert Image(s) Format"
_IMAGE__PROMPT=$"Choose the format to convert the image(s) to:"
_IMAGE__COLUMN_1=$"Select"
_IMAGE__COLUMN_2=$"Format"
_IMAGE__COLUMN_3=$"Description"

# --- GIF Context ---
_GIF__MERGE_PROMPT=$"You have selected multiple images and chosen GIF as the format.\n\nDo you want to merge them into a single animated GIF?"
_GIF__SAVE_TITLE=$"Save GIF As"

# --- Progress Context ---
_PROGRESS_TITLE=$"Converting Images"
_PROGRESS_TEXT=$"Processing..."

# --- PDF Context ---
_PDF__TITLE=$"PDF to Image Conversion"
_PDF__PROMPT=$"Enter the required details for conversion.\n\nNote: Leaving fields empty will apply default values."
_PDF__COMBO_LABEL=$"Format (default: png)"
_PDF__COMBO_VALUES="png|jpg|tiff"
_PDF__ENTRY_1=$"Resolution / DPI (default: 300)"
_PDF__ENTRY_2=$"First Page (default: 1)"
_PDF__ENTRY_3=$"Last Page (default: last page of document)"
_PDF__MERGE_PROMPT=$"You have selected multiple images and chosen PDF as the format.\n\nDo you want to merge them into a single PDF document?\n(Click 'No' to convert them to separate PDF files)"
_PDF__SAVE_TITLE=$"Save Merged PDF As"

# --- Error & Reporting Context ---
_ERROR__TITLE=$"Conversion Errors"
_ERROR__SKIPPED=$"The following files were skipped (unsupported format):"
_ERR_MISSING_DEP=$"Missing dependency:"

# ----------------------------------------------------------------------------------------
# SECTION B: LOCALIZATION RESOLUTION
# ----------------------------------------------------------------------------------------

# --- Image Context ---
IMAGE__TITLE="$(/usr/bin/gettext "$_IMAGE__TITLE")"
IMAGE__PROMPT="$(/usr/bin/gettext "$_IMAGE__PROMPT")"
IMAGE__COLUMN_1="$(/usr/bin/gettext "$_IMAGE__COLUMN_1")"
IMAGE__COLUMN_2="$(/usr/bin/gettext "$_IMAGE__COLUMN_2")"
IMAGE__COLUMN_3="$(/usr/bin/gettext "$_IMAGE__COLUMN_3")"

# --- GIF Context ---
GIF__MERGE_PROMPT="$(/usr/bin/gettext "$_GIF__MERGE_PROMPT")"
GIF__SAVE_TITLE="$(/usr/bin/gettext "$_GIF__SAVE_TITLE")"

# --- Progress Context ---
PROGRESS_TITLE="$(/usr/bin/gettext "$_PROGRESS_TITLE")"
PROGRESS_TEXT="$(/usr/bin/gettext "$_PROGRESS_TEXT")"

# --- PDF Context ---
PDF__TITLE="$(/usr/bin/gettext "$_PDF__TITLE")"
PDF__PROMPT="$(/usr/bin/gettext "$_PDF__PROMPT")"
PDF__COMBO_LABEL="$(/usr/bin/gettext "$_PDF__COMBO_LABEL")"
PDF__COMBO_VALUES="$(/usr/bin/gettext "$_PDF__COMBO_VALUES")"
PDF__ENTRY_1="$(/usr/bin/gettext "$_PDF__ENTRY_1")"
PDF__ENTRY_2="$(/usr/bin/gettext "$_PDF__ENTRY_2")"
PDF__ENTRY_3="$(/usr/bin/gettext "$_PDF__ENTRY_3")"
PDF__MERGE_PROMPT="$(/usr/bin/gettext "$_PDF__MERGE_PROMPT")"
PDF__SAVE_TITLE="$(/usr/bin/gettext "$_PDF__SAVE_TITLE")"

# --- Error & Reporting Context ---
ERROR__TITLE="$(/usr/bin/gettext "$_ERROR__TITLE")"
ERROR__SKIPPED="$(/usr/bin/gettext "$_ERROR__SKIPPED")"
ERR_MISSING_DEP="$(/usr/bin/gettext "$_ERR_MISSING_DEP")"

# ------------------------------------------------------------------------------
# SECTION C: CORE FUNCTIONS
# ------------------------------------------------------------------------------

check_dependencies() {
    if ! command -v zenity &> /dev/null; then
        if command -v notify-send &> /dev/null; then
            /usr/bin/notify-send "Error" "The program 'zenity' is required." -u critical
        fi
        exit 1
    fi

    # only essential dependencies, others can be installed later if the user wants to:
    local deps=("convert" "file" "pdftoppm" "xargs" "cut")
    for cmd in "${deps[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            /usr/bin/zenity --error --text="${ERR_MISSING_DEP} $cmd"
            exit 1
        fi
    done
}

verify_tool() {
  local cmd="$1"
  local feature_name="$2"
  if ! command -v "$cmd" &> /dev/null; then
    log_error "DEPENDENCY" "Missing tool '$cmd'. Required for: $feature_name"
    return 1
  fi
  return 0
}

get_safe_path() {
    local full_path="$1"
    local dir
    dir=$(dirname "$full_path")
    local filename
    filename=$(basename "$full_path")
    local ext="${filename##*.}"
    local name="${filename%.*}"

    local new_path="$full_path"
    local counter=1

    while [ -e "$new_path" ]; do
        new_path="${dir}/${name}_${counter}.${ext}"
        counter=$((counter + 1))
    done

    echo "$new_path"
}

log_error() {
    local file="$1"
    local msg="$2"
    echo "--------------------------------------------------" >> "$ERR_LOG"
    echo "FILE:  $(basename "$file")" >> "$ERR_LOG"
    echo "ERROR: $msg" >> "$ERR_LOG"
}

get_image_target_format() {
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
      FALSE "jxl" "JPEG XL Image Coding System" \
      FALSE "pjp" "JPEG (Joint Photographic Experts Group)" \
      FALSE "pjpeg" "JPEG (Joint Photographic Experts Group)" \
      FALSE "pdf" "Portable Document Format" \
      FALSE "png" "Portable Network Graphics" \
      FALSE "svg" "plaintext Scalable Vector Graphics" \
      FALSE "svgz" "compressed Scalable Vector Graphics" \
      FALSE "tif" "Tagged Image File Format" \
      FALSE "tiff" "Tagged Image File Format" \
      FALSE "webp" "Web Picture format"
}

get_pdf_settings() {
    /usr/bin/zenity --forms \
      --title="$PDF__TITLE" \
      --text="$PDF__PROMPT" \
      --add-combo="$PDF__COMBO_LABEL" --combo-values="$PDF__COMBO_VALUES" \
      --add-entry="$PDF__ENTRY_1" \
      --add-entry="$PDF__ENTRY_2" \
      --add-entry="$PDF__ENTRY_3" \
      --separator="|"
}

convert_image() {
  local file="$1"
  local target_ext="$2"
  local output_msg=""

  local dir
  dir=$(dirname "$file")
  local filename
  filename=$(basename "$file")
  local basename="${filename%.*}"
  local source_ext="${filename##*.}"
  source_ext="${source_ext,,}"

  local target_file="${dir}/${basename}.${target_ext}"
  local safe_target
  safe_target=$(get_safe_path "$target_file")


  if [[ "$target_ext" == "jxl" ]]; then
    verify_tool "cjxl" "JPEG XL Encoding" || return 1
    output_msg=$(/usr/bin/convert "$file" png:- | /usr/bin/cjxl - "$safe_target" 2>&1)

  elif [[ "$source_ext" == "jxl" ]]; then
    verify_tool "djxl" "JPEG XL Decoding" || return 1
    output_msg=$(/usr/bin/djxl "$file" - | /usr/bin/convert - "$safe_target" 2>&1)

  elif [[ "$source_ext" == "psd" ]]; then
    output_msg=$(/usr/bin/convert "${file}[0]" "$safe_target" 2>&1)

  elif [[ "$source_ext" == "gif" ]]; then
    local safe_base="${safe_target%.*}"
    output_msg=$(/usr/bin/convert "$file" -coalesce "${safe_base}_frame_%05d.${target_ext}" 2>&1)

  elif [[ "$source_ext" == "svg" ]] && [[ "$target_ext" =~ ^(eps|pdf|png|ps|svg)$ ]]; then
    verify_tool "rsvg-convert" "Better SVG Conversion" || return 1
    output_msg=$(/usr/bin/rsvg-convert --format="$target_ext" --output="$safe_target" "$file" 2>&1)

  else
    output_msg=$(/usr/bin/convert "$file" "$safe_target" 2>&1)
  fi

  if [ $? -ne 0 ]; then
    log_error "$file" "$output_msg"
  fi
}

create_animated_gif() {
    local first_file="${IMAGES_LIST[0]}"
    local default_dir
    default_dir=$(dirname "$first_file")
    local output_msg=""

    OUTPUT_FILE=$(/usr/bin/zenity --file-selection --save --confirm-overwrite \
        --title="$GIF__SAVE_TITLE" \
        --filename="${default_dir}/animation.gif")

    if [ -z "$OUTPUT_FILE" ]; then return; fi

    if [[ "${OUTPUT_FILE##*.}" != "gif" ]]; then
        OUTPUT_FILE="${OUTPUT_FILE}.gif"
    fi

    (
      output_msg=$(/usr/bin/convert -delay 20 -loop 0 "${IMAGES_LIST[@]}" "$OUTPUT_FILE" 2>&1)
      if [ $? -ne 0 ]; then
          log_error "Animated GIF Merge" "$output_msg"
      fi
    ) | /usr/bin/zenity --progress --title="$PROGRESS_TITLE" --pulsate --auto-close
}

convert_pdf() {
    local file="$1"
    local settings="$2"
    local output_msg=""

    verify_tool "pdftoppm" "PDF to Image" || return 1

    local p_fmt
    p_fmt=$(echo "$settings" | cut -d "|" -f1 | xargs)
    local p_dpi
    p_dpi=$(echo "$settings" | cut -d "|" -f2 | xargs)
    local p_start
    p_start=$(echo "$settings" | cut -d "|" -f3 | xargs)
    local p_end
    p_end=$(echo "$settings" | cut -d "|" -f4 | xargs)

    p_fmt="${p_fmt:-png}"
    p_dpi="${p_dpi:-300}"
    p_start="${p_start:-1}"

    if [[ -z "$p_end" ]] && command -v pdfinfo &> /dev/null; then
      p_end=$(pdfinfo "$file" | grep '^Pages:' | awk '{print $2}')
    fi

    local fmt_flag=""
    case "$p_fmt" in
        "jpg"|"jpeg") fmt_flag="-jpeg" ;;
        "png")        fmt_flag="-png" ;;
        "tiff"|"tif") fmt_flag="-tiff" ;;
        *) return 1 ;;
    esac

    local dir
    dir=$(dirname "$file")
    local bname
    bname=$(basename "$file" .pdf)

    local raw_out_dir="${dir}/${bname}_images"
    local safe_out_dir="$raw_out_dir"
    local counter=1
    while [ -d "$safe_out_dir" ]; do
        safe_out_dir="${raw_out_dir}_${counter}"
        counter=$((counter + 1))
    done
    mkdir -pv "$safe_out_dir"

    local args=(
      "$fmt_flag"
      "-r" "$p_dpi"
      "-f" "$p_start"
      "-forcenum"
      "-sep" "_"
    )
    if [[ -n "$p_end" ]]; then args+=("-l" "$p_end"); fi

    output_msg=$(pdftoppm "${args[@]}" "$file" "${safe_out_dir}/pg" 2>&1)

    if [ $? -ne 0 ]; then
        log_error "$file" "$output_msg"
    fi
}

create_merged_pdf() {
    local first_file="${IMAGES_LIST[0]}"
    local default_dir
    default_dir=$(dirname "$first_file")
    local output_msg=""

    verify_tool "img2pdf" "Merge Images to PDF" || return 1

    OUTPUT_FILE=$(/usr/bin/zenity --file-selection --save --confirm-overwrite \
        --title="$PDF__SAVE_TITLE" \
        --filename="${default_dir}/merged_images.pdf")

    if [ -z "$OUTPUT_FILE" ]; then return; fi

    if [[ "${OUTPUT_FILE##*.}" != "pdf" ]]; then
        OUTPUT_FILE="${OUTPUT_FILE}.pdf"
    fi

    (
      output_msg=$(/usr/bin/img2pdf "${IMAGES_LIST[@]}" --output "$OUTPUT_FILE" 2>&1)
      if [ $? -ne 0 ]; then
          log_error "PDF Merge" "$output_msg"
      fi
    ) | /usr/bin/zenity --progress --title="$PROGRESS_TITLE" --pulsate --auto-close
}


check_dependencies

declare -a IMAGES_LIST
declare -a PDFS_LIST
declare -a SKIPPED_LIST

for file in "$@"; do
    mime=$(file --mime-type -b "$file")
    if [[ "$mime" == image/* ]]; then
        IMAGES_LIST+=("$file")
    elif [[ "$mime" == application/pdf ]]; then
        PDFS_LIST+=("$file")
    else
        SKIPPED_LIST+=("$file")
    fi
done

TARGET_IMG_EXT=""
PDF_SETTINGS=""

if [ ${#IMAGES_LIST[@]} -gt 0 ]; then
    TARGET_IMG_EXT=$(get_image_target_format)
    [ -z "$TARGET_IMG_EXT" ] && exit 0

    if [[ "$TARGET_IMG_EXT" == "gif" && ${#IMAGES_LIST[@]} -gt 1 ]]; then
        if /usr/bin/zenity --question --text="$GIF__MERGE_PROMPT"; then
            create_animated_gif
            IMAGES_LIST=()
        fi
    fi

    if [[ "$TARGET_IMG_EXT" == "pdf" && ${#IMAGES_LIST[@]} -gt 1 ]]; then

        if /usr/bin/zenity --question \
            --text="$PDF__MERGE_PROMPT" \
            --ok-label="Merge into single PDF" \
            --cancel-label="Keep separate PDFs"; then

            create_merged_pdf
            IMAGES_LIST=()
        fi
    fi
fi


if [ ${#PDFS_LIST[@]} -gt 0 ]; then
    PDF_SETTINGS=$(get_pdf_settings)
    [ -z "$PDF_SETTINGS" ] && exit 0
fi


TOTAL_FILES=$((${#IMAGES_LIST[@]} + ${#PDFS_LIST[@]}))
CURRENT=0

(
    if [ ${#IMAGES_LIST[@]} -gt 0 ]; then
        for img in "${IMAGES_LIST[@]}"; do
            echo "# Converting: $(basename "$img")"
            convert_image "$img" "$TARGET_IMG_EXT"
            CURRENT=$((CURRENT + 1)); echo $((CURRENT * 100 / TOTAL_FILES))
        done
    fi

    if [ ${#PDFS_LIST[@]} -gt 0 ]; then
        for pdf in "${PDFS_LIST[@]}"; do
            echo "# Extracting PDF: $(basename "$pdf")"
            convert_pdf "$pdf" "$PDF_SETTINGS"
            CURRENT=$((CURRENT + 1)); echo $((CURRENT * 100 / TOTAL_FILES))
        done
    fi

) | /usr/bin/zenity --progress \
        --title="$PROGRESS_TITLE" \
        --text="$PROGRESS_TEXT" \
        --percentage=0 \
        --auto-close

if [ -s "$ERR_LOG" ]; then
    /usr/bin/zenity --text-info \
        --title="$ERROR__TITLE" \
        --filename="$ERR_LOG" \
        --width=600 --height=400 \
        --font="Monospace"
fi

if [ ${#SKIPPED_LIST[@]} -gt 0 ]; then
    skipped_names=""
    for f in "${SKIPPED_LIST[@]}"; do
        skipped_names+="$(basename "$f")\n"
    done
    /usr/bin/zenity --warning \
        --title="$ERROR__TITLE" \
        --text="$ERROR__SKIPPED\n\n$skipped_names" \
        --width=400
fi

exit 0
