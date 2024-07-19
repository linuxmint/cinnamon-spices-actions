#!/bin/bash

# Check if file argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <file>"
    exit 1
fi

# File to send
FILE="$1"

blueman-sendto $FILE
