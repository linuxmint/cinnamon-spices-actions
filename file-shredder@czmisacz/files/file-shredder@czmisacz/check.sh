#!/bin/bash


for file_to_corrupt in "$@"; do

    ACTION_DIR=$(echo "$file_to_corrupt" | sed 's/\\//g')

    # Some locations like trash or recent don't return a parent dir.
    # It is not possible to create a shortcut of them.
    if [[ -z "$ACTION_DIR" ]]; then
        exit 1
    fi

done
exit 0