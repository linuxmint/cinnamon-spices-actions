#!/bin/bash
# Check if file is valid for Steam
# Returns 0 (true) if file should show the action

file="$1"
filename=$(basename "$file")
ext="${filename##*.}"

# Check for specific extensions
case "$ext" in
    desktop|exe|sh|py|AppImage)
        exit 0
        ;;
esac

# Check if it's an executable file (without extension)
if [ -f "$file" ] && [ -x "$file" ]; then
    exit 0
fi

# Not a valid file
exit 1
