#!/usr/bin/python3

import os
import sys
import subprocess
import gettext

from pathlib import Path

UUID = "move-into-a-new-folder@anaximeno"
HOME = os.path.expanduser("~")
gettext.bindtextdomain(UUID, os.path.join(HOME, "/.local/share/locale"))
gettext.textdomain(UUID)

_ = lambda message: gettext.gettext(message)

S_TITLE = _("Move Into a New Folder")
S_TEXT = _("Insert the name of the new folder:")
S_ENTRY_DEFAULT = _("New Folder")
S_FOLDER_EXISTS = _(
    "Folder named '%s' already exists inside the current folder, do you want to move the selected files inside?"
)
S_FOLDER_NOT_CREATED = _(
    "Couldn't create a new folder named '%s' inside the current folder!"
)


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
        try:
            new_path = folder.joinpath(item_path.name)
            item_new_path = item_path.rename(new_path.resolve())
            moved.append(item_new_path)
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
            args=["zenity", "--question", f"--text={text}", "--no-wrap"],
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

    _, not_moved = move_items_to_the_new_folder(sys.argv[2:], new_folder_path)

    if not_moved:
        subprocess.run(
            args=[
                "zenity",
                "--error"
                # f"--text=" #TODO
            ],
            stdout=subprocess.DEVNULL,
        )


if __name__ == "__main__":
    main()
