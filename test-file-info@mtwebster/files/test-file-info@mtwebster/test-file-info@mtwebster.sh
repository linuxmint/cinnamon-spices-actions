#!/bin/bash

FILEPATH="$1"

SIZE=$(du -sh "$FILEPATH" | awk '{print $1}')
MIMETYPE=$(file --mime-type "$FILEPATH" | awk '{print $2}')
MODIFIED=$(stat -c %y "$FILEPATH")
OWNER=$(stat -c %U "$FILEPATH")
PERMS=$(stat -c %a "$FILEPATH")

TMPFILE=$(mktemp /tmp/file-info-XXXXXX.txt)

cat > "$TMPFILE" << EOF
File: $FILEPATH
Size: $SIZE
Type: $MIMETYPE
Modified: $MODIFIED
Owner: $OWNER
Permissions: $PERMS
EOF

zenity --text-info --title="File Info" --filename="$TMPFILE"
rm "$TMPFILE"
