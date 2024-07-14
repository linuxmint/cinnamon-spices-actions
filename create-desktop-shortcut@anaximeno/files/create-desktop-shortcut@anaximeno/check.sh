#!/bin/bash

ACTION_DIR="$(echo $1 | sed 's/\\//g')"
DESKTOP="$HOME/Desktop"

if command -v xdg-user-dir &>/dev/null; then
    if [[ -d "$(xdg-user-dir DESKTOP)" ]]; then
        DESKTOP="$(xdg-user-dir DESKTOP)"
    fi
fi

# Don't show the action if the desktop folder does not
# exist or was not found.
if [[ ! -d $DESKTOP ]]; then
    exit 1
fi

# Don't show the action in the context menu,
# when we are inside the desktop folder.
if [[ $ACTION_DIR -ef $DESKTOP ]]; then
    exit 1
fi

# Some locations like trash or recent don't return a parent dir.
# It is not possible to create a shortcut of them.
if [[ -z "$ACTION_DIR" ]]; then
    exit 1
fi

exit 0
