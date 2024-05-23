#!/bin/bash

FILEPATH=$1
FOLDER="$(dirname "$FILEPATH")"


# is this not a file or we canot write in the folder ?
if [[ ! -f $FILEPATH ]] || [[ ! -w "$FOLDER" ]]; then
    exit 1
fi

exit 0
