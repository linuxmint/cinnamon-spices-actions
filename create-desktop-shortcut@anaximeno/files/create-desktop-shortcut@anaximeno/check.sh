#!/bin/bash

ACTION_DIR=$(echo $1 | sed 's/\\//g')
DESKTOP=$(xdg-user-dir DESKTOP)

# Don't show the action in the context menu,
# when we are inside the desktop folder.
if [[ $ACTION_DIR -ef $DESKTOP ]]; then
    exit 1
fi

exit 0
