#!/bin/bash
# ===== SECTION #1_URL_RETRIEVAL =====
# Get clipboard content

if command -v xclip &> /dev/null; then
    # X11
    url=$(xclip -o -selection clipboard 2>/dev/null)
elif command -v wl-paste &> /dev/null; then
    # Wayland
    url=$(wl-paste 2>/dev/null)
else
    notify-send -t 30000 "Error" "No clipboard tool available (xclip/wl-paste)"
    exit 1
fi

# ===== SECTION #2_URL_VALIDATION =====
# Verify it's a valid URL
if [[ ! "$url" =~ ^https?:// ]]; then
    notify-send -t 30000 "Error" "Clipboard does not contain a valid URL"
    exit 1
fi

# ===== SECTION #3_BROWSER_OPENING =====
# Open URL in default browser
xdg-open "$url" &

# Success notification
notify-send -t 30000 "Link Opened" "$url"
