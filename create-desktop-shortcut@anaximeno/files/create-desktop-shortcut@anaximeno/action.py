#!/usr/bin/python3

import os
import sys
import pathlib
import subprocess


def main() -> None:
    if len(sys.argv) <= 1:
        print("Error: no files provided to create a desktop shortcut")
        exit(1)

    result = subprocess.run(["xdg-user-dir", "DESKTOP"], stdout=subprocess.PIPE)
    desktop = result.stdout.decode("utf-8").replace("\n", "")

    if not os.path.exists(desktop) or not os.path.isdir(desktop):
        print("Error: XDG User Dir 'DESKTOP' not found or invalid!")
        exit(1)

    items = (pathlib.Path(item.replace("\\", "")) for item in sys.argv[1:])

    for item in items:
        # TODO: inform user of unsucessful shortcurt creations
        try:
            # XXX: it will not create a symlink if there's already a file with that name there,
            # we should instead ask the user what is the correct action (replace, replace all, cancel, etc)
            # when this happens.
            if item.exists():
                shortcut = pathlib.Path(os.path.join(desktop, item.name))
                os.symlink(str(item.resolve()), str(shortcut.resolve()), item.is_dir())
            else:
                print(
                    f"Error: couldn't create shortcut for {item.as_posix()!r}"
                    ", not found!"
                )
        except:
            print(f"Error: couldn't create shortcut for {item.as_posix()!r}!")


if __name__ == "__main__":
    main()
