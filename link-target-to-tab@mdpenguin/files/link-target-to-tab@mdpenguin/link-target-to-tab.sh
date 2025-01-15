#!/bin/bash

# remove backslashes passed in by Nemo so parentheses handled correctly and find link target path
target_path=$(readlink -f "${1//'\'/}")

# open link target path in new tab of active Nemo window
nemo "$target_path" -t --existing-window
