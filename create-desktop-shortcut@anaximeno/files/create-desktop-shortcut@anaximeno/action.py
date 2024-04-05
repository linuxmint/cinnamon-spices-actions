#!/usr/bin/python3

import os
import sys
import subprocess
import aui
import text

from pathlib import Path
from helpers import log


class CreateDesktopShortcut:
    def __init__(self, desktop_folder: str, items: list) -> None:
        # NOTE: you'll have to prepend a 'devtest-' to the UUID if
        # the action is installed using the `test-spice` script to
        # get the correct icon when testing.
        self._win_icon = aui.get_action_icon_path(text.UUID)
        self._override_on_file_exists = None
        self._desktop_folder = desktop_folder
        self._items = items

    def send_to_trash(self, item: Path) -> bool:
        try:
            response = subprocess.run(
                ["gio", "trash", item.as_posix()],  # TODO: import gio from gi.repo
                stderr=subprocess.DEVNULL,
            )
            return response.returncode == 0
        except:
            return False

    def prompt_not_created_message(self) -> None:
        dialog = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            message=text.SHORTCUTS_NOT_CREATED_MESSAGE,
            window_icon_path=self._win_icon,
        )
        dialog.run()
        dialog.destroy()

    def prompt_override_permission(self) -> str:
        dialog = aui.QuestionDialogWindow(
            title=text.ACTION_TITLE,
            message=text.FILE_ALREADY_EXISTS_AT_THE_DESKTOP_FOLDER,
            window_icon_path=self._win_icon,
        )
        override = dialog.run()
        dialog.destroy()
        return override

    def link_shortcut_to_item(self, shortcut: Path, item: Path) -> bool:
        if shortcut.exists():
            if self._override_on_file_exists is None:
                self._override_on_file_exists = self.prompt_override_permission()

            if self._override_on_file_exists == aui.QuestionDialogWindow.RESPONSE_YES:
                self.send_to_trash(shortcut)

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

    def run(self) -> None:
        not_created = []
        for item in items:
            try:
                shortcut = Path(os.path.join(self._desktop_folder, item.name))
                created = self.link_shortcut_to_item(shortcut=shortcut, item=item)
                if not created:
                    not_created.append(item)
            except Exception as e:
                not_created.append(item)
                log(
                    f"Error: couldn't create shortcut for {item.name!r}, exception => {e}"
                )

        if any(not_created):
            self.prompt_not_created_message()


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        log("Error: no files provided to create a desktop shortcut")
        exit(1)

    result = subprocess.run(["xdg-user-dir", "DESKTOP"], stdout=subprocess.PIPE)
    desktop = result.stdout.decode("utf-8").replace("\n", "")

    if not os.path.exists(desktop) or not os.path.isdir(desktop):
        log("Error: XDG User Dir 'DESKTOP' not found or invalid!")
        exit(1)

    items = [Path(item.replace("\\ ", " ")) for item in sys.argv[1:]]

    action = CreateDesktopShortcut(desktop_folder=desktop, items=items)
    action.run()
