#!/bin/bash
. gettext.sh

# Uncomment and specify path to save a logs of file corruption
# LOG_FILE="/your/debug/file/location.txt"

# Corruption & removal using "shred"
secure_unlink_file() {
    local file="$1"
    if [ -e "$file" ]; then
        local error_message
        error_message=$(shred -z -u "$file" 2>&1)  # Capture error message

        local exit_code=$?
        if [ $exit_code -ne 0 ]; then
            zenity --error --text="$error_message"
        fi

        # Uncomment the following line if you want to log the error message to a file
        echo "Error message: $error_message" # >> "$LOG_FILE" 2>&1

        return $exit_code
    fi

    return 0
}

corrupt_step() {
    local file="$1"
    local pattern="$2"
    
    if [ ! -f "$file" ]; then
        return 1
    fi

    echo -n -e "$pattern" > "$file"  # Apply the entire pattern to the file
    if [ $? -ne 0 ]; then
        return 1
    fi

    return 0
}

# Custom corruption of a file using patterns
corrupt_file() {
    local file="$1"

    if [ ! -f "$file" ]; then
        echo "corrupt: \"$file\" not found" # >> "$LOG_FILE" 2>&1 # UNCOMMENT FOR LOGGING
        return 1
    fi

    for pattern in "www" "vvv" "333" "555" "uuu" "aaa" "444" "555" "666" "www"; do
        corrupt_step "$file" "$pattern"
        if [ $? -ne 0 ]; then
            return 0
        fi
    done

    return 0
}

# Recursive function to process files and directories
process_files_and_directories() {
    local dir="$1"

    shopt -s nullglob
    for entry in "$dir"/* "$dir"/.*; do
        # Exclude "." and ".."
        if [ "$entry" != "$dir/." ] && [ "$entry" != "$dir/.." ]; then
            if [ -f "$entry" ]; then
                # Process file
                corrupt_file "$entry"
                if [ $? -eq 0 ]; then
                    echo "File \"$entry\" corrupted successfully." # >> "$LOG_FILE" 2>&1 # UNCOMMENT FOR LOGGING
                    secure_unlink_file "$entry"
                    if [ $? -eq 0 ]; then
                        echo "File \"$entry\" securely removed successfully." # >> "$LOG_FILE" 2>&1 # UNCOMMENT FOR LOGGING
                    else
                        echo "Failed to securely remove \"$entry\"." # >> "$LOG_FILE" 2>&1 # UNCOMMENT FOR LOGGING
                    fi
                else
                    echo "File corruption for \"$entry\" failed." # >> "$LOG_FILE" 2>&1 # UNCOMMENT FOR LOGGING
                fi
            elif [ -d "$entry" ]; then
                # Recursively process directory
                process_files_and_directories "$entry"
            fi
        fi
    done

    # After processing contents, remove the current directory
    if [ -z "$(ls -A "$dir")" ]; then
        rmdir "$dir" # >> "$LOG_FILE" 2>&1 # UNCOMMENT FOR LOGGING
        if [ $? -eq 0 ]; then
            echo "Folder \"$dir\" removed successfully." # >> "$LOG_FILE" 2>&1 # UNCOMMENT FOR LOGGING
        else
            echo "Failed to remove folder \"$dir\"." # >> "$LOG_FILE" 2>&1 # UNCOMMENT FOR LOGGING
        fi
    fi
}


# Process multiple files or folders
init_eval_gettext
export TEXTDOMAIN="action.sh"
export LANG="es_ES.UTF-8"
title=$(gettext "REALLY SHRED FILES")
text1=$(gettext "This will PERMANENTLY delete the following files. Undeletion will be impossible")
text2=$(gettext "You must type SHRED FILES in this dialog and press OK to really shred these files/directories")

response=$(zenity --entry --title="${title}?" --text="${text1}!\r\n${text2}.")

if [ "$response" != "SHRED FILES" ]; then
    zenity --info --text="Not deleted"
    exit 0
else
    zenity --into --text="Deleted"
    exit 0
fi

for file_to_corrupt in "$@"; do
    # Remove backslashes and quotes from the file path
    file_to_corrupt=$(echo "$file_to_corrupt" | sed 's/\\//g' | tr -d '"')
    
    if [ -e "$file_to_corrupt" ]; then
        if [ -d "$file_to_corrupt" ]; then
            # Process files and directories
            process_files_and_directories "$file_to_corrupt"
        else
            # Process individual file
            corrupt_file "$file_to_corrupt"
            if [ $? -eq 0 ]; then
                echo "File \"$file_to_corrupt\" corrupted successfully." # >> "$LOG_FILE" 2>&1 # UNCOMMENT FOR LOGGING
                secure_unlink_file "$file_to_corrupt"
                if [ $? -eq 0 ]; then
                    echo "File \"$file_to_corrupt\" securely removed successfully." # >> "$LOG_FILE" 2>&1 # UNCOMMENT FOR LOGGING
                else
                    echo "Failed to securely remove \"$file_to_corrupt\"." # >> "$LOG_FILE" 2>&1 # UNCOMMENT FOR LOGGING
                fi
            else
                echo "File corruption for \"$file_to_corrupt\" failed." # >> "$LOG_FILE" 2>&1 # UNCOMMENT FOR LOGGING
            fi
        fi
    else
        echo "Invalid path: \"$file_to_corrupt\"" # >> "$LOG_FILE" 2>&1 # UNCOMMENT FOR LOGGING
    fi
done
