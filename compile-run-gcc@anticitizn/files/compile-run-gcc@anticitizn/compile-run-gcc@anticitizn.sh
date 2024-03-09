#! /bin/bash
FILENAME="$1"

# Remove the file's original extension and change it to .out
DIR="$(dirname "${FILENAME}")"
OUTPUT="${DIR}/a.out"

# Compile all files using GCC
gcc -I./ -o $OUTPUT $@ -Wall

# Run the program
if [ -f "$OUTPUT" ]; then
    "$OUTPUT"
fi

echo

# Hold the terminal open until a keypress is detected
read -n 1 -s -r -p "Press any key to close..."