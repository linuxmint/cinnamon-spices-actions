#!/bin/bash

ACTION_DIR=$(echo $1 | sed 's/\\//g')

# Some locations like trash or recent don't return a parent dir.
if [[ -z "$ACTION_DIR" ]]; then
    exit 1
fi

# Check write permission to the current folder
if [[ ! -w "$ACTION_DIR" ]]; then
    exit 1
fi

exit 0
