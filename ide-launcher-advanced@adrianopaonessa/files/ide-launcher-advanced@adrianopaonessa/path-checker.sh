#!/bin/bash

# Check for exceptions
CURRENT_DIR=$1


# if CURRENT_DIR is empty or CURRENT_DIR is root
if [[ -z "$CURRENT_DIR" || "$CURRENT_DIR" == '/' ]]; then
    # don't show the action
    exit 1
fi

# everything is fine, show the action
exit 0