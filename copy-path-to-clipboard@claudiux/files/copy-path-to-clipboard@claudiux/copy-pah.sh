#!/usr/bin/env bash
# copy-path.sh

fp="$1"

# Handle SMB shares if a second argument (URL) was passed
if [[ -n "$2" && "$1" == *smb-share* ]]; then
    fp="$2"
fi

# Copy to clipboard (use wl-copy if on Wayland, xclip if on X11)
if command -v wl-copy &> /dev/null && [ "$XDG_SESSION_TYPE" == "wayland" ]; then
    printf '%s' "$fp" | wl-copy
else
    printf '%s' "$fp" | xclip -selection clipboard
fi
