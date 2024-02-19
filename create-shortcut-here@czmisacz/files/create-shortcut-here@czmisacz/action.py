#!/usr/bin/python3

import os
import sys
import pathlib
import subprocess
import gettext

SHORTCUT_STR = gettext.gettext('shortcut')

def main() -> None:
    if len(sys.argv) <= 1:
        print("Error: no files provided to create a shortcut")
        exit(1)

    items = [pathlib.Path(item.replace("\\", "")) for item in sys.argv[1:]]

    for item in items:
        try:
            # Ensure that the item path is an absolute path
            item_absolute = item.resolve()

            if item_absolute.exists():
                # Initialize the counter
                counter = 1

                # Append " - Shortcut" to the item name before creating the symlink
                shortcut_name = f"{item.stem} - {SHORTCUT_STR}{item.suffix}"

                # Check if the shortcut already exists in the same directory as the item
                while (item.parent / shortcut_name).exists():
                    # If it does, increment the counter and try again
                    counter += 1
                    shortcut_name = f"{item.stem} - {SHORTCUT_STR} ({counter}){item.suffix}"

                # Create the symlink in the same directory as the item
                shortcut = item.parent / pathlib.Path(shortcut_name)
                shortcut.symlink_to(item_absolute, target_is_directory=item.is_dir())
            else:
                print(f"Error: couldn't create shortcut for {item_absolute.as_posix()!r}, not found!")
        except Exception as e:
            print(f"Error: {e} - couldn't create shortcut for {item_absolute.as_posix()!r}")

if __name__ == "__main__":
    main()
