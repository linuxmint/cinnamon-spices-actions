#!/bin/bash
# ===== SECTION #1_CLIPBOARD_VERIFICATION =====
# Verification script: returns 0 if clipboard contains an HTTP(S) URL

# Get clipboard content (compatible with X11 and Wayland)
if command -v xclip &> /dev/null; then
    # X11
    clipboard_content=$(xclip -o -selection clipboard 2>/dev/null)
elif command -v wl-paste &> /dev/null; then
    # Wayland
    clipboard_content=$(wl-paste 2>/dev/null)
else
    # No clipboard tool available
    exit 1
fi

# Check if content starts with http:// or https://
if [[ "$clipboard_content" =~ ^https?:// ]]; then
    exit 0  # URL found
else
    exit 1  # No URL
fi
