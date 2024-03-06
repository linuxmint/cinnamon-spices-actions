#!/bin/bash

TEXTDOMAIN=$UUID  
TEXTDOMAINDIR=$LOCALE_DIR  

_SHORTCUT=$"shortcut"  
SHORTCUT_STR="$(gettext "$_SHORTCUT")"

main() {
    if [ "$#" -le 0 ]; then
        echo "Error: No files provided to create a shortcut."
        exit 1
    fi

    for item in "$@"; do
        item=${item//\\ / }  # Replace escaped spaces with actual spaces
        item_absolute=$(realpath "$item")

        if [ -e "$item_absolute" ]; then
            counter=1
            # Handle files without extensions
            file_extension="${item_absolute##*.}"
            if [ "$file_extension" = "$item_absolute" ]; then
                shortcut_name="${item_absolute} - $SHORTCUT_STR"
            else
                shortcut_name="${item_absolute%.*} - $SHORTCUT_STR.${file_extension}"
            fi

            # Check if the shortcut already exists in the same directory as the item
            while [ -e "$shortcut_name" ]; do
                ((counter++))
                if [ "$file_extension" = "$item_absolute" ]; then
                    shortcut_name="${item_absolute} - $SHORTCUT_STR ($counter)"
                else
                    shortcut_name="${item_absolute%.*} - $SHORTCUT_STR ($counter).${file_extension}"
                fi
            done

            # Create the symlink in the same directory as the item
            ln_output=$(ln -s "$item_absolute" "$shortcut_name" 2>&1)

            if [ $? -ne 0 ]; then
                echo "$ln_output"
                # Remove the "ln:" prefix from ln_output
                error_message="${ln_output#ln: }"
                zenity --error --text "$error_message"
            fi
        else
            echo "Error: Couldn't create shortcut for '$item_absolute', not found!"
        fi
    done
}

main "$@"
