#!/usr/bin/python3

import os
import sys
import subprocess

from pathlib import Path

import ui
import text


DEBUG = os.environ.get("NEMO_DEBUG", False) == "Actions"
def log(*args, **kwargs):
    if DEBUG: print(f"Action {text.UUID}:", *args, **kwargs)


def send_to_trash(item: Path) -> bool:
    try:
        response = subprocess.run(
            ["gio", "trash", item.as_posix()],
            stderr=subprocess.DEVNULL,
        )
        return response.returncode == 0
    except:
        return False


def prompt_not_created_message() -> None:
    dialog = ui.BasicMessageDialogWindow()
    dialog.run()
    dialog.destroy()


def prompt_override_permission() -> str:
    dialog = ui.OverrideQuestionMessageDialogWindow()
    override = dialog.run()
    dialog.destroy()
    return override


override = None
def link_shortcut_to_item(shortcut: Path, item: Path) -> bool:
    global override
    if shortcut.exists():
        if override is None:
            override = prompt_override_permission()

        if override == "y":
            send_to_trash(shortcut)

        if shortcut.exists():
            log(
                f"Info: not creating a shortcut for {item.name!r}, "
                "item with the same name in the desktop folder."
            )
            return False

    if item.exists():
        shortcut.symlink_to(item.resolve(), target_is_directory=item.is_dir())
        return True
    else:
        log(f"Error: couldn't create shortcut for {item.name!r}" ", not found!")
        return False


def main() -> None:
    if len(sys.argv) <= 1:
        log("Error: no files provided to create a desktop shortcut")
        exit(1)

    result = subprocess.run(["xdg-user-dir", "DESKTOP"], stdout=subprocess.PIPE)
    desktop = result.stdout.decode("utf-8").replace("\n", "")

    if not os.path.exists(desktop) or not os.path.isdir(desktop):
        log("Error: XDG User Dir 'DESKTOP' not found or invalid!")
        exit(1)

    items = (Path(item.replace("\\ ", " ")) for item in sys.argv[1:])

    not_created = []
    for item in items:
        try:
            shortcut = Path(os.path.join(desktop, item.name))
            created = link_shortcut_to_item(shortcut=shortcut, item=item)
            if not created:
                not_created.append(item)
        except Exception as e:
            not_created.append(item)
            log(f"Error: couldn't create shortcut for {item.name!r}, exception => {e}")

    if any(not_created):
        prompt_not_created_message()


if __name__ == "__main__":
    main()
