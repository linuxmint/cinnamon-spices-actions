#!/bin/bash

path="$1"

# exit without error if path is a Nemo search
if [ "$path" == "Search" ]; then
    exit 0;
fi

exit 1;