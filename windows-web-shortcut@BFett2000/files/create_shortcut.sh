#!/bin/bash

# Get the folder where the user right-clicked
if [ -n "$1" ]; then
    DEST=$(realpath "$1")
else
    DEST=$(xdg-user-dir DESKTOP)
fi

# Confirm URL or file path of the link
URL=$(zenity --entry --width=250 --title "Shortcut Location" --text="Enter the URL or file path for this shortcut:" --entry-text="")
if [ -z "$URL" ]; then
    notify-send --expire-time=200000 "Shortcut creation canceled."
    exit 1
fi

# Auto-format web addresses missing a scheme
if [ ! -e "$URL" ]; then
    case "$URL" in
        http://*|https://*|file://*) ;;
        *) URL="https://$URL" ;;
    esac
fi

# Safe target validation: check if local path exists or if it begins with a valid web scheme
if [ ! -e "$URL" ]; then
    case "$URL" in
        http://*|https://*|ftp://*)
            ;;
        *)
            notify-send --expire-time=200000 "Error: '$URL' is not a valid file path or web address."
            exit 1
            ;;
    esac
fi

# Confirm name of the shortcut
NAME=$(zenity --entry --width=250 --title "Shortcut Name" --text="Enter a name for this shortcut:" --entry-text="")
if [ -z "$NAME" ]; then
    notify-send --expire-time=200000 "Shortcut creation canceled."
    exit 1
fi

# Verify target directory exists before file generation
if [ ! -d "$DEST" ]; then
    notify-send --expire-time=200000 "Error: Destination directory $DEST does not exist."
    exit 1
fi

# Check if the shortcut already exists
if [ -e "$DEST/$NAME.desktop" ]; then
    notify-send --expire-time=200000 "Error: $DEST/$NAME.desktop already exists."
    exit 1
fi

# Determine Icon Based on Target Type
if [ -d "$URL" ]; then
    # Local Folder Target
    CUSTOM_ICON=$(gio info -a "metadata::custom-icon" "$URL" | grep "metadata::custom-icon:" | cut -d' ' -f4-)

    if [ -n "$CUSTOM_ICON" ]; then
        ICON_ID="$CUSTOM_ICON"
    else
        ICON_ID="folder"
    fi
else
    # External Web Target: Isolate main domain host for icon fetch
    HOST=$(echo "$URL" | awk -F'/' '{print $3}' | cut -d':' -f1)

    # Extract base domain (e.g., assets.science.nasa.gov -> nasa.gov)
    DOMAIN=$(echo "$HOST" | awk -F'.' '{ if (NF>2) print $(NF-1)"."$NF; else print $0 }')

    ICON_DIR="$HOME/.local/share/icons/web_shortcuts"
    mkdir -p "$ICON_DIR"

    LOCAL_ICON="$ICON_DIR/$DOMAIN.png"

    # Download high-res favicon using the root domain
    if [ ! -f "$LOCAL_ICON" ]; then
        curl -s -L "https://www.google.com/s2/favicons?sz=64&domain=$DOMAIN" -o "$LOCAL_ICON"
    fi

    if [ -s "$LOCAL_ICON" ]; then
        ICON_ID="$LOCAL_ICON"
    else
        ICON_ID="syncthing"
    fi
fi

# Write .desktop file safely
cat <<EOF > "$DEST/$NAME.desktop"
[Desktop Entry]
Name=$NAME
URL=$URL
Comment=
Terminal=false
Icon=$ICON_ID
Type=Link
EOF

# Ensure permissions and set shortcut overlay emblem
chmod 644 "$DEST/$NAME.desktop"
gio set -t stringv "$DEST/$NAME.desktop" metadata::emblems emblem-symbolic-link

if [ $? -eq 0 ]; then
    notify-send --expire-time=200000 "Shortcut successfully created in $DEST"
    exit 0
else
    notify-send --expire-time=200000 "Error: Failed to create shortcut."
    exit 1
fi
