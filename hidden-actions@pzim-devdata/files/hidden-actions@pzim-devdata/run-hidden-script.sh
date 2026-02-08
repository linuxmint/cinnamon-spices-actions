#!/bin/bash

# ===== SECTION #1_CONFIGURATION =====
SCRIPT_DIR="$HOME/.local/share/hidden_scripts"

# Create directory if it doesn't exist
mkdir -p "$SCRIPT_DIR"

# ===== SECTION #2_LIST_SCRIPTS =====
scripts=$(ls -1 "$SCRIPT_DIR" 2>/dev/null | grep -v '^$')

# ===== SECTION #3_HANDLE_EMPTY_FOLDER =====
if [ -z "$scripts" ]; then
    zenity --question \
        --text="No scripts found in ~/.local/share/hidden_scripts/\n\nOpen folder in Nemo?" \
        --title="🔒 Hidden Actions" \
        --ok-label="Open Folder" \
        --cancel-label="Cancel" \
        --width=400 \
        --window-icon=changes-prevent
    
    if [ $? -eq 0 ]; then
        nemo "$SCRIPT_DIR" &
    fi
    exit 0
fi

# ===== SECTION #4_DISPLAY_MENU =====
# Number the scripts
numbered_list=$(echo "$scripts" | nl -w1 -s'. ')

choice=$(echo "$numbered_list" | zenity --list \
    --column="Script" \
    --title="🔒 Hidden Actions" \
    --text="Select a script to execute:" \
    --height=400 \
    --width=400)

# ===== SECTION #5_EXECUTE_SCRIPT =====
if [ -n "$choice" ]; then
    # Extract filename (remove number prefix)
    script_name=$(echo "$choice" | sed 's/^[0-9]*\. //')
    "$SCRIPT_DIR/$script_name"
fi
