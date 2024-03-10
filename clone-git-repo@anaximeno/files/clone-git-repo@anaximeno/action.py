#!/usr/bin/python3
import os
import sys
import re
import subprocess
import aui
import text
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from pathlib import Path


def roverride(string: str) -> str:
    overrides = string.split("\r")
    overriden = overrides[0]
    if len(overrides) > 2 and len(overrides[-1]) >= len(overrides[-2]):
        overriden = overrides[-1] + overriden[len(overrides[-1]) :]
    else:
        for override in overrides:
            overriden = override + overriden[len(override) :]
    return overriden


class GitRepoCloneApp:
    REPO_NAME_REGEX = r"\/([^\/]+)(\.git)?$"

    ASSUME_PROTOCOL = "http"

    def __init__(self, directory: str, default_protocol: str = ASSUME_PROTOCOL) -> None:
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self._win_icon_path = aui.get_action_icon_path(text.UUID)
        self._directory = directory
        self._process = None
        self._buff = ""

    def get_address_from_clipboard(self) -> str | None:
        clipcontent = self.clipboard.wait_for_text()
        if clipcontent and self.extract_folder_name_from_address(clipcontent):
            return clipcontent
        return None

    def extract_folder_name_from_address(self, address: str) -> str:
        re_match = re.search(self.REPO_NAME_REGEX, address)
        if re_match is not None:
            return re_match.group(1).replace(".git", "")
        return ""

    def prompt_user_for_repo_address(self, default_address: str = "") -> str | None:
        window = aui.EntryDialogWindow(
            title=text.ACTION_TITLE,
            window_icon_path=self._win_icon_path,
            label=text.ADDRESS_ENTRY_LABEL,
            default_text=default_address,
        )

        user_response = window.run()
        window.destroy()

        if user_response is None:
            exit(1)

        user_response = user_response.strip()

        if user_response == "":  # TODO: Make a stronger address validity check?
            self.prompt_user_git_address_invalid(user_response)
            exit(1)

        return user_response

    def prompt_user_for_cloned_folder_name(self, default_name: str) -> str | None:
        window = aui.EntryDialogWindow(
            title=text.ACTION_TITLE,
            window_icon_path=self._win_icon_path,
            label=text.FOLDER_NAME_ENTRY_LABEL,
            default_text=default_name,
        )

        response = window.run()
        window.destroy()

        return response

    def prompt_user_git_address_invalid(self, address: str) -> None:
        window = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            message=text.ADDRESS_INVALID,
            window_icon_path=self._win_icon_path,
        )
        window.run()
        window.destroy()

    def prompt_user_folder_name_invalid(self, folder_name: str) -> None:
        window = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            message=text.FOLDER_NAME_INVALID,
            window_icon_path=self._win_icon_path,
        )
        window.run()
        window.destroy()

    def _formalize_address(self, address: str) -> str:
        if address.startswith("file://"):
            return address
        elif os.path.exists(address):
            return f"file://{Path(address).resolve()}"

        if address.startswith("git@"):
            address = f"ssh://{address}"
        elif address.startswith("://"):
            address = f"{self.ASSUME_PROTOCOL}{address}"
        elif not "://" in address:
            address = f"{self.ASSUME_PROTOCOL}://{address}"

        if not address.endswith(".git"):
            address = f"{address}.git"

        return address

    def clone_git_repo(self, address: str, local_path: str) -> bool:
        self._process = subprocess.Popen(
            ["git", "clone", "--progress", address, local_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        window = aui.ProgressbarDialogWindow(
            title=text.ACTION_TITLE,
            message=text.CLONING_FOR % address,
            window_icon_path=aui.get_action_icon_path(text.UUID),
            timeout_callback=self.handle_progress,
            timeout_ms=35,
        )

        window.run()
        window.destroy()

        return (
            self._process.poll() == 0
        )  # TODO: also check for the cloned repo folder name if exists

    def run(self) -> None:
        clipaddress = self.get_address_from_clipboard()
        address = self.prompt_user_for_repo_address(clipaddress)
        folder_name = self.extract_folder_name_from_address(address)

        if not address or not folder_name:
            self.prompt_user_git_address_invalid(address)
            exit(1)

        folder_name = self.prompt_user_for_cloned_folder_name(folder_name)

        if not folder_name:
            self.prompt_user_folder_name_invalid(folder_name)
            exit(1)

        formal_address = self._formalize_address(address)
        folder_path = os.path.join(self._directory, folder_name)

        success = self.clone_git_repo(formal_address, folder_path)

        if not success:
            # prompt_unsuccessful_cloning() # TODO
            exit(1)

    def handle_progress(self, user_data, window: aui.ProgressbarDialogWindow) -> bool:
        if self._process and self._process.poll() is None:
            try:
                self._buff += self._process.stderr.read(100).decode("utf-8")
                window.progressbar.set_text(roverride(self._buff.split("\n")[-1]))
                window.progressbar.pulse()
                return True
            except UnicodeDecodeError as e:
                print(e)
                pass
        window.stop()
        window.destroy()
        return False


if __name__ == "__main__":
    app = GitRepoCloneApp(directory=sys.argv[1].replace("\\ ", " "))
    app.run()
