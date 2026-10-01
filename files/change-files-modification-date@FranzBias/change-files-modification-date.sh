#!/bin/bash
#
######################################################
#   Change File Modification Date by FranzBias (c)   #
#           https://github.com/FranzBias             #
#                                                    #
#       Allows changing the modification date        #
#           of one or more selected files            #
#                                                    #
#           Licensed under the MIT License.          #
#          See LICENSE file for full license.        #
######################################################

set -e

# Load translations
SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/translations.sh"
load_translations

# Function to get the translation
print_translation() {
    local key="$1"
    echo "${TRANSLATIONS[$key]}"
}

# Translations
MSG_NO_FILE=$(print_translation "file_not_selected")
MSG_NO_DATE=$(print_translation "date_not_selected")
MSG_NO_TIME=$(print_translation "no_time_selected")
MSG_MOD_COMPLETE=$(print_translation "modification_complete")
MSG_BACKUP=$(print_translation "enable_backup")
MSG_DEBUG=$(print_translation "enable_debug")
MSG_YES=$(print_translation "yes")
MSG_NO=$(print_translation "no")
MSG_CANCEL=$(print_translation "cancel")
MSG_OPTIONS=$(print_translation "select_options")
MSG_SELECT_DATE=$(print_translation "select_date")
MSG_SELECT_TIME=$(print_translation "select_time")

# Show backup and debug options
selected_options=$(zenity --list --checklist --title="$MSG_OPTIONS" --text="$MSG_OPTIONS" \
    --column="Select" --column="Option" FALSE "$MSG_BACKUP" FALSE "$MSG_DEBUG" --separator=":")

BACKUP_ENABLED=0
DEBUG_ENABLED=0

if [[ "$selected_options" == *"$MSG_BACKUP"* ]]; then
    BACKUP_ENABLED=1
fi

if [[ "$selected_options" == *"$MSG_DEBUG"* ]]; then
    DEBUG_ENABLED=1
fi

# Dependency control
for dep in zenity touch; do
    if ! command -v "$dep" &>/dev/null; then
        zenity --error --text="Missing dependency: $dep. Install it with: sudo apt install $dep"
        exit 1
    fi
done

# Select date
selected_date=$(LANG=en_US.UTF-8 zenity --calendar --title="$MSG_SELECT_DATE" --date-format="%Y%m%d")
if [ -z "$selected_date" ]; then
    zenity --error --text="$MSG_NO_DATE"
    exit 1
fi

# Select the time
hour_minute=$(LANG=en_US.UTF-8 zenity --list --title="$MSG_SELECT_TIME" --column="Time" \
    "00:00" "00:30" "01:00" "01:30" "02:00" "02:30" "03:00" "03:30" "04:00" "04:30" \
    "05:00" "05:30" "06:00" "06:30" "07:00" "07:30" "08:00" "08:30" "09:00" "09:30" \
    "10:00" "10:30" "11:00" "11:30" "12:00" "12:30" "13:00" "13:30" "14:00" "14:30" \
    "15:00" "15:30" "16:00" "16:30" "17:00" "17:30" "18:00" "18:30" "19:00" "19:30" \
    "20:00" "20:30" "21:00" "21:30" "22:00" "22:30" "23:00" "23:30")
if [ -z "$hour_minute" ]; then
    zenity --error --text="$MSG_NO_TIME"
    exit 1
fi

hour=$(echo "$hour_minute" | cut -d ':' -f1)
minute=$(echo "$hour_minute" | cut -d ':' -f2)
timestamp="${selected_date}${hour}${minute}.00"

# Initialise log if debug is active
if [ "$DEBUG_ENABLED" -eq 1 ]; then
    debug_file="$(dirname "$1")/Debug of change-files-modification-date.txt"
    count=1
    while [ -e "$debug_file" ]; do
        debug_file="$(dirname "$1")/Debug of change-files-modification-date $count.txt"
        ((count++))
    done
    echo "DEBUG LOG - $(date)" > "$debug_file"
fi

# Initialise any errors
error_log=""

# Apply changes to each file
for file in "$@"; do
    base_name=$(basename "$file")
    current_time=$(stat --format=%y "$file")

    backup_file="${file}.bkp"
    count=1
    while [ -e "$backup_file" ]; do
        backup_file="${file}.bkp$count"
        ((count++))
    done

    if [ "$BACKUP_ENABLED" -eq 1 ]; then
        cp --preserve=timestamps,mode,ownership "$file" "$backup_file"
    fi

    if [ "$DEBUG_ENABLED" -eq 1 ]; then
        echo "FILE NAME: $base_name" >> "$debug_file"
        echo "DATE AND TIME: $current_time" >> "$debug_file"
    fi

    is_read_only=$(stat -c %a "$file")
    if [ "$is_read_only" -eq 444 ]; then
        chmod +w "$file"
    fi

    if ! touch -t "$timestamp" -- "$file"; then
        error_log="$error_log$'\n'File: $file, Error: Read-only or modification failed"
        continue
    fi

    if [ "$is_read_only" -eq 444 ]; then
        chmod 444 "$file"
    fi
done

if [ "$DEBUG_ENABLED" -eq 1 ]; then
    if [ -z "$error_log" ]; then
        echo "CHANGE(S) DONE!" >> "$debug_file"
    else
        echo -e "ERROR(S) OCCURRED:$error_log" >> "$debug_file"
    fi
fi

zenity --info --text="$MSG_MOD_COMPLETE"
