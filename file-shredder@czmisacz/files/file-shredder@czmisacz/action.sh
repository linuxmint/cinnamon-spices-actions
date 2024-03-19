#!/bin/bash

# Uncomment and specify path to save a logs of file corruption
# LOG_FILE="/your/debug/file/location.txt"

TEXTDOMAIN="file-shredder@czmisacz"
TEXTDOMAINDIR="${HOME}/.local/share/locale"

_SHRED=$"This will permanently remove selected files."  
SHRED_STR="$(gettext "$_SHRED")"

_ARE_YOU_SURE=$"Are you sure you want shred selected files?"  
ARE_YOU_SURE_STR="$(gettext "$_ARE_YOU_SURE")"

# Zenity dialog to confirm before starting the script
zenity --question --icon-name=dialog-warning --text="<big>$ARE_YOU_SURE_STR</big>\n\n$SHRED_STR" || exit

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
