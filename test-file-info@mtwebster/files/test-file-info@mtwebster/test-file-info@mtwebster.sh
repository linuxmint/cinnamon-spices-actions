#!/bin/bash

FILEPATH="$1"

SIZE=$(du -sh "$FILEPATH" | awk '{print $1}')
MIMETYPE=$(file --mime-type "$FILEPATH" | awk '{print $2}')
MODIFIED=$(stat -c %y "$FILEPATH")
OWNER=$(stat -c %U "$FILEPATH")
PERMS=$(stat -c %a "$FILEPATH")

INFO=$(printf "File: %s\nSize: %s\nType: %s\nModified: %s\nOwner: %s\nPermissions: %s" \
    "$FILEPATH" "$SIZE" "$MIMETYPE" "$MODIFIED" "$OWNER" "$PERMS")

zenity --info --title="File Info" --text="$INFO" --no-wrap
