#!/bin/bash

FILEPATH=$1

SIZE=$(du -sh $FILEPATH | awk '{print $1}')
MIMETYPE=$(file --mime-type $FILEPATH | awk '{print $2}')
MODIFIED=$(stat -c %y $FILEPATH)
OWNER=$(stat -c %U $FILEPATH)
PERMS=$(stat -c %a $FILEPATH)

CHECKSUM=$(curl -s https://api.virustotal.com/v3/files/$(md5sum $FILEPATH | cut -d' ' -f1) | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['attributes']['last_analysis_stats'])")

TMPFILE=/tmp/file-info-output.txt

cat > $TMPFILE << EOF
File: $FILEPATH
Size: $SIZE
Type: $MIMETYPE
Modified: $MODIFIED
Owner: $OWNER
Permissions: $PERMS
VirusTotal: $CHECKSUM
EOF

zenity --text-info --title="File Info" --filename=$TMPFILE
rm $TMPFILE
