#!/usr/bin/python3

import os
import sys
import text
import aui

from pathlib import Path


class MoveIntoNewFolder:
    def __init__(self, base_folder: Path, items: list) -> None:
        self._window_icon = aui.get_action_icon_path(text.UUID)
        self._base_folder = base_folder
        self._items = items

    def get_new_folder_path(self) -> tuple[str, Path]:
        window = aui.EntryDialogWindow(
            title=text.ACTION_TITLE,
            label=text.ENTRY_LABEL,
            window_icon_path=self._window_icon,
            default_text=text.ENTRY_DEFAULT,
        )
        name = window.run()
        window.destroy()
        if name is None:
            exit(0)
        elif not name.strip():
            exit(1)
        path = self._base_folder.joinpath(name)
        return name, path


    def move_items_to_folder(self, items: list[str], folder: Path) -> tuple[list, list]:
        moved, not_moved = [], []
        for item in items:
            item_path = Path(item.replace("\\", ""))
            if not item_path.exists():
                continue
            try:
                new_path = folder.joinpath(item_path.name)
                item_at_new_path = item_path.rename(new_path.resolve())
                if item_at_new_path.exists() and not item_path.exists():
                    moved.append(item_at_new_path)
                else:
                    not_moved.append(item_path)
            except:
                not_moved.append(item_path)
        return moved, not_moved

    def try_create_folder(self, path: Path) -> bool:
        try:
            os.mkdir(path)
        except:
            window = aui.InfoDialogWindow(
                message=text.FOLDER_NOT_CREATED % path.name,
                title=text.ACTION_TITLE,
                window_icon_path=aui.get_action_icon_path(text.UUID),
            )
            window.run()
            window.destroy()
            exit(1)

    def run(self):
        new_folder_name, new_folder_path = self.get_new_folder_path()

        if new_folder_path.exists():
            window = aui.QuestionDialogWindow(
                message=text.FOLDER_EXISTS % new_folder_name,
                title=text.ACTION_TITLE,
                window_icon_path=aui.get_action_icon_path(text.UUID),
            )
            response = window.run()
            window.destroy()

            if response != aui.QuestionDialogWindow.RESPONSE_YES:
                exit(1)
        else:
            self.try_create_folder(new_folder_path)

        moved, not_moved = self.move_items_to_folder(self._items, new_folder_path)

        if not_moved:
            message = text.ALL_NOT_MOVED if not moved else text.N_NOT_MOVED % len(not_moved)
            window = aui.InfoDialogWindow(
                message=message,
                window_icon_path=aui.get_action_icon_path(text.UUID),
                title=text.ACTION_TITLE,
            )
            window.run()
            window.destroy()
            exit(1)


if __name__ == "__main__":
    base_folder = Path(sys.argv[1].replace("\\", ""))
    items = sys.argv[2:]
    action = MoveIntoNewFolder(base_folder, items)
    action.run()