#!/usr/bin/python3

import os
import sys
import text
import aui

from pathlib import Path


def get_new_folder_path(base_folder: Path) -> Path:
    window = aui.EntryDialogWindow(
        title=text.TITLE,
        label=text.TEXT,
        default_text=text.ENTRY_DEFAULT,
        window_icon_path=aui.get_action_icon_path(text.UUID),
    )
    name = window.run()
    window.destroy()
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
        window = aui.QuestionDialogWindow(
            message=text.FOLDER_EXISTS % new_folder_path.name,
            title=text.TITLE,
            window_icon_path=aui.get_action_icon_path(text.UUID),
        )
        response = window.run()
        window.destroy()

        if response != aui.QuestionDialogWindow.RESPONSE_YES:
            exit(1)
    else:
        try:
            os.mkdir(new_folder_path)
        except:
            window = aui.InfoDialogWindow(
                message=text.FOLDER_NOT_CREATED % new_folder_path.name,
                title=text.TITLE,
                window_icon_path=aui.get_action_icon_path(text.UUID),
            )
            window.run()
            window.destroy()
            exit(1)

    moved, not_moved = move_items_to_the_new_folder(sys.argv[2:], new_folder_path)

    if not_moved:
        message = text.ALL_NOT_MOVED if not moved else text.N_NOT_MOVED % len(not_moved)
        window = aui.InfoDialogWindow(
            message=message,
            window_icon_path=aui.get_action_icon_path(text.UUID),
            title=text.TITLE,
        )
        window.run()
        window.destroy()
        exit(1)


if __name__ == "__main__":
    main()
