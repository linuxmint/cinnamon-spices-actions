#!/usr/bin/python3

import os
import sys
import pathlib
import subprocess

import text
import ui


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

    not_created = []
    for item in items:
        # XXX: it will not create a symlink if there's already a file with that name there,
        # we should instead ask the user what is the correct action (replace, replace all, cancel, etc)
        # when this happens.
        try:
            if item.exists():
                shortcut = pathlib.Path(os.path.join(desktop, item.name))
                shortcut.symlink_to(item.resolve(), target_is_directory=item.is_dir())
            else:
                not_created.append(item)
                print(
                    f"Error: couldn't create shortcut for {item.as_posix()!r}"
                    ", not found!"
                )
        except:
            not_created.append(item)
            print(f"Error: couldn't create shortcut for {item.as_posix()!r}")

    if any(not_created):
        dialog = ui.BasicMessageDialogWindow(
            title=text.ACTION_TITLE,
            message=text.SHORTCUTS_NOT_CREATED_MESSAGE,
        )
        dialog.run()
        dialog.destroy()


if __name__ == "__main__":
    main()
