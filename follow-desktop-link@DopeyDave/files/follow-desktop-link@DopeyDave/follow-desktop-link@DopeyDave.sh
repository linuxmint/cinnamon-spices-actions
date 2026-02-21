#!/bin/bash

for file in "$@"; do
    # Extract the target path from the URL= line
    url=$(grep -E '^URL=' "$file" | sed -E 's/^URL=//')

    # Remove the file:// prefix if present
    target="${url#file://}"

    # Decode any URL-encoded characters (like spaces (%20) in path)
    target=$(printf '%b' "${target//%/\\x}")

    if [[ -d "$target" ]]; then
        nemo "$target"
    elif [[ -f "$target" ]]; then
        nemo --no-desktop --browser "$(dirname "$target")"
    else
        zenity --error --text="Target not found or invalid: $target"
    fi
done
