#!/usr/bin/python3

import os
import sys
import subprocess
import gettext

from pathlib import Path

UUID = "move-into-a-new-folder@anaximeno"
HOME = os.path.expanduser("~")
gettext.bindtextdomain(UUID, os.path.join(HOME, ".local/share/locale"))
gettext.textdomain(UUID)

_ = lambda message: gettext.gettext(message)

S_TITLE = _("Move Into a New Folder")
S_TEXT = _("Name of the new folder:")
S_ENTRY_DEFAULT = _("New Folder")
S_FOLDER_EXISTS = _(
    "Folder '%s' already exists inside the current directory, do you want to move the selected files inside?"
)
S_FOLDER_NOT_CREATED = _(
    "Couldn't create a new folder '%s' inside the current directory!"
)
S_N_NOT_MOVED = _("Could not move %d of the selected items into a new folder!")
S_ALL_NOT_MOVED = _("Could not move any of the selected items into a new folder!")


def get_new_folder_path(base_folder: Path, dialog_width: int = 360) -> Path:
    result = subprocess.run(
        args=[
            "zenity",
            "--entry",
            f"--width={dialog_width}",
            f"--title={S_TITLE}",
            f"--text={S_TEXT}",
            f"--entry-text={S_ENTRY_DEFAULT}",
        ],
        stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")

    name = result.replace("\n", "")
    path = base_folder.joinpath(name)

    return name, path


def move_items_to_the_new_folder(items: list[str], folder: Path) -> tuple[list, list]:
    moved, not_moved = [], []
    for item in items:
        item_path = Path(item.replace("\\", ""))

        if not item_path.exists():
            continue

        try:
            new_path = folder.joinpath(item_path.name)
            item_new_path = item_path.rename(new_path.resolve())
            if item_new_path.exists() and not item_path.exists():
                moved.append(item_new_path)
            else:
                not_moved.append(item_path)
        except:
            not_moved.append(item_path)

    return moved, not_moved


def main():
    base_folder = Path(sys.argv[1].replace("\\", ""))
    new_folder_name, new_folder_path = get_new_folder_path(base_folder)

    if not new_folder_name.strip():
        exit(1)

    if new_folder_path.exists():
        text = S_FOLDER_EXISTS % new_folder_path.name
        response = subprocess.run(
            args=["zenity", "--question", f"--text={text}"],
            stdout=subprocess.PIPE,
        )

        if response.returncode != 0:
            exit(response.returncode)
    else:
        try:
            os.mkdir(new_folder_path)
        except:
            text = S_FOLDER_NOT_CREATED % new_folder_path.name

            subprocess.run(
                args=["zenity", "--error", f"--text={text}", "--no-wrap"],
                stdout=subprocess.PIPE,
            )

            exit(1)

    moved, not_moved = move_items_to_the_new_folder(sys.argv[2:], new_folder_path)

    if not_moved:
        text = S_ALL_NOT_MOVED if not moved else S_N_NOT_MOVED % len(not_moved)

        subprocess.run(
            args=["zenity", "--error", f"--text={text}", "--no-wrap"],
            stdout=subprocess.DEVNULL,
        )

        exit(1)


if __name__ == "__main__":
    main()
