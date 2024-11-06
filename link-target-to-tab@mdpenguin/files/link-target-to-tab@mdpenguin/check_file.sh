#!/bin/bash

file="$1"

# exit with no errors if file is a symlink
if [ -L "$file" ]; then
    exit 0;
fi

exit 1;