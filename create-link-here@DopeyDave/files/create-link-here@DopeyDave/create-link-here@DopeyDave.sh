#!/bin/bash

# Check if any files/folders are selected
if [ -z "$1" ]; then
  echo "No file/folder selected."
  exit 1
fi

# Get the target file or folder
TARGET="$1"

# Debug note:
# To print to the system log (file: /var/log/syslog),
#   in bash, use the following example:
#   logger "Target: $TARGET"

# If "\" char is in the string
# Note: Use [[double brackets]]
if [[ "$TARGET" == *\\* ]]; then
  # Remove all ("//") "\" chars
  TARGET="${TARGET//\\}"
fi

# Extract the filename and path
FILENAME=$(basename "$TARGET")
DIRNAME=$(dirname "$TARGET")

# Preserve the real filename, which could start with "." (hidden)
NAME_OF_FILE=$FILENAME

# If the filename starts with a dot, prepend an underscore to the filename
# in order to make it visible on the Desktop
if [[ "$FILENAME" == .* ]]; then
  FILENAME="_$FILENAME"
fi

# Create a .desktop file in the same directory as the selected file/folder
# Note: If hidden ("."), "_" is pre-pended so file will be visible
#       if it is moved to the Desktop
DESKTOP_FILE="${DIRNAME}/${FILENAME}.desktop"

# Check if the .desktop file already exists in this folder
if [ -e "$DESKTOP_FILE" ]; then
  echo "A .desktop file already exists for this item in this folder."
  exit 1
fi

# Determine the icon based on the type of file or folder
if [ -d "$TARGET" ]; then
  ICON="folder"
elif file --mime-type "$TARGET" | grep -q 'text/'; then
  ICON="text"
elif file --mime-type "$TARGET" | grep -q 'application/pdf'; then
  ICON="application-pdf"
elif file --mime-type "$TARGET" | grep -q 'image/'; then
  ICON="image-x-generic"
elif file --mime-type "$TARGET" | grep -q 'audio/'; then
  ICON="audio-x-generic"
elif file --mime-type "$TARGET" | grep -q 'video/'; then
  ICON="video-x-generic"
else # Unknown type
  ICON="application-octet-stream"
fi

# Create the .desktop file content
echo "[Desktop Entry]" > "$DESKTOP_FILE"
echo "Name=$NAME_OF_FILE" >> "$DESKTOP_FILE" # Use real name of file (this will show "." files/folders correctly on Desktop)
echo "URL=file://$TARGET" >> "$DESKTOP_FILE" # URL format needed for Link type
echo "Icon=$ICON" >> "$DESKTOP_FILE"
echo "Terminal=false" >> "$DESKTOP_FILE"
echo "Type=Link" >> "$DESKTOP_FILE" # Type needs to be Link

# Make the .desktop file executable
chmod +x "$DESKTOP_FILE"

# Output complete
echo "Created .desktop link: $DESKTOP_FILE"
