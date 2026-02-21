#!/bin/bash

# Only show the action for regular files (not symlinks, devices, etc.)
MIMETYPE=$(python3 -c "import mimetypes; print(mimetypes.guess_type('$1')[0] or 'unknown')")

if [ "$MIMETYPE" != "unknown" ]; then
    exit 0
fi

exit 1
