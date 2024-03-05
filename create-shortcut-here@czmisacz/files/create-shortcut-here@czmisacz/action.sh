#!/bin/bash

UUID="create-shortcut-here@czmisacz"
HOME_DIR="$HOME"
LOCALE_DIR="$HOME_DIR/.local/share/locale/$UUID"
SHORTCUT_STR="shortcut"

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
            shortcut_name="${item_absolute%.*} - $SHORTCUT_STR.${item_absolute##*.}"

            # Check if the shortcut already exists in the same directory as the item
            while [ -e "$shortcut_name" ]; do
                ((counter++))
                shortcut_name="${item_absolute%.*} - $SHORTCUT_STR ($counter).${item_absolute##*.}"
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
