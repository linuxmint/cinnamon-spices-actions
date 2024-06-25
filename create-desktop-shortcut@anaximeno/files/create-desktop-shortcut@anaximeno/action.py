#!/usr/bin/python3

import os
import sys
import subprocess
import aui
import text
import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio
from pathlib import Path
from helpers import log


class CreateDesktopShortcutAction:
    def __init__(self, desktop_folder: str, items: list[Path]) -> None:
        self._win_icon = aui.get_action_icon_path(text.UUID)
        self._override_on_file_exists = None
        self._desktop_folder = desktop_folder
        self._items = items
        self._not_created = []
        self._created = []

    def send_to_trash(self, item: Path) -> bool:
        try:
            file = Gio.File.new_for_path(item.as_posix())
            file.trash(cancellable=None)
            return True
        except Exception as e:
            log("Exception:", e)
            return False

    def display_not_created_message(self) -> None:
        dialog = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            message=text.SHORTCUTS_NOT_CREATED_MESSAGE,
            window_icon_path=self._win_icon,
        )
        dialog.run()
        dialog.destroy()

    def ask_for_override_permission(self) -> str:
        dialog = aui.QuestionDialogWindow(
            title=text.ACTION_TITLE,
            message=text.FILE_ALREADY_EXISTS_AT_THE_DESKTOP_FOLDER,
            window_icon_path=self._win_icon,
        )
        override = dialog.run()
        dialog.destroy()
        return override

    def link_shortcut_to_item(self, item: Path) -> tuple[Path, bool]:
        shortcut = Path(os.path.join(self._desktop_folder, item.name))
        if shortcut.exists() or shortcut.is_symlink():
            if not shortcut.is_symlink() and self._override_on_file_exists is None:
                self._override_on_file_exists = self.ask_for_override_permission()

            if shortcut.is_symlink() or self._override_on_file_exists == aui.QuestionDialogWindow.RESPONSE_YES:
                self.send_to_trash(shortcut)

            if shortcut.exists():
                log(
                    f"Info: not creating a shortcut for {item.name!r}, "
                    "item with the same name in the desktop folder."
                )
                return (shortcut, False)

        if item.exists():
            shortcut.symlink_to(item.resolve(), target_is_directory=item.is_dir())
            return (shortcut, shortcut.is_symlink())
        else:
            log(f"Error: couldn't create shortcut for {item.name!r}" ", not found!")
            return (shortcut, False)

    def run(self) -> None:
        for item in self._items:
            try:
                _, created = self.link_shortcut_to_item(item=item)

                if created:
                    self._created.append(item)
                else:
                    self._not_created.append(item)
            except Exception as e:
                self._not_created.append(item)
                log(
                    f"Error: couldn't create shortcut for {item.name!r}, exception => {e}"
                )

        self._report()

    def _report(self) -> None:
        log("Created", len(self._created), "Not Created", len(self._not_created))
        if any(self._not_created):
            self.display_not_created_message()


def parse_item(item: str) -> str:
    item = item.replace("\\ ", " ")
    item = item.replace("\\'", "\'")
    return item


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        log("Error: no files provided to create a desktop shortcut")
        exit(1)

    desktop = ""

    try:
        result = subprocess.run(["xdg-user-dir", "DESKTOP"], stdout=subprocess.PIPE)
        desktop = result.stdout.decode("utf-8").replace("\n", "")
    except Exception as e:
        log("Exception:", e)

    if not desktop or not os.path.exists(desktop):
        desktop = os.path.join(os.environ.get("HOME", ""), "Desktop")

    if not os.path.exists(desktop) or not os.path.isdir(desktop):
        log("Error: XDG User Dir 'DESKTOP' not found or invalid!")
        exit(1)

    items = [Path(parse_item(item)) for item in sys.argv[1:]]

    action = CreateDesktopShortcutAction(desktop_folder=desktop, items=items)
    action.run()
