#!/bin/bash

## This script checks the cwd in nemo,
## if it's allowed to access it, and to be accessible
## it must not be root dir, or an empty dir such as trash
## otherwise we exit with code 1 telling nemo not to add the action
## to the menu

WORKING_DIR=$1


if [[ -z "$WORKING_DIR" || "$WORKING_DIR" == '/' ]]; then
    exit 1
fi

exit 0