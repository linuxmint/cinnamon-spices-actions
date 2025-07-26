#!/bin/bash

## Here we handle exception.
## We will catch if currently right clicked directory actually exists,
## ... Or is it the root filesystem?
WORKING_DIR=$1


## IF:   WORKING_DIR is empty      (eg. recents, trash or search results)   --- does not exist
## OR:   WORKING_DIR is /          (eg. favorites or root filesystem)       --- we don't touch root filesystem
if [[ -z "$WORKING_DIR" || "$WORKING_DIR" == '/' ]]; then
    
    # THEN: We exit with err. code 1, so that Nemo action will receive err. condition
    # ...and won't continue executing, aka. won't show Zed menu entry at all.
    exit 1
fi

exit 0