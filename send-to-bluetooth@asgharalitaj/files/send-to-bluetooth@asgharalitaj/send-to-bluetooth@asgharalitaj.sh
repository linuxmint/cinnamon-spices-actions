#!/bin/bash

# Check if file argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <file>"
    exit 1
fi

# File to send
FILE="$1"

# Choose Bluetooth device
DEVICE=$(blueman-sendto --choose)

# Send file to the chosen device
blueman-sendto --send $FILE $DEVICE
