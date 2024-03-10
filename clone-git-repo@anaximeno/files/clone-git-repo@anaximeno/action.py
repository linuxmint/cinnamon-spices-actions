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

    for override in overrides[1:]:
        l = len(override)
        overriden = override + overriden[l:]

    return overriden


class GitRepoCloneApp:
    REPO_NAME_REGEX = r"\/([^\/]+)(\.git)?$"

    ASSUME_PROTOCOL = "http"

    def __init__(self, directory: str, default_protocol: str = ASSUME_PROTOCOL) -> None:
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self._default_protocol = default_protocol
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

        response = window.run()
        window.destroy()

        if response is None:
            print(
                "Action clone-git-repo@anaximeno:",
                "Info:",
                f"user cancelled the operation",
            )
            exit(1)

        response = response.strip()

        if response == "":
            self.prompt_user_git_address_invalid(response)
            exit(1)

        return response

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
        print(
            "Action clone-git-repo@anaximeno:",
            "Error:",
            f"invalid repository address {address!r}",
        )
        window = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            message=text.ADDRESS_INVALID,
            window_icon_path=self._win_icon_path,
        )
        window.run()
        window.destroy()

    def prompt_user_folder_name_invalid(self, folder_name: str) -> None:
        print(
            "Action clone-git-repo@anaximeno:",
            "Error:",
            f"invalid folder name {folder_name!r}",
        )
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
            address = f"{self._default_protocol}{address}"
        elif not "://" in address:
            address = f"{self._default_protocol}://{address}"

        if not address.endswith(".git"):
            address = f"{address}.git"

        return address

    def clone_git_repo(self, address: str, local_path: str) -> bool:
        print(
            "Action clone-git-repo@anaximeno:",
            "Info:",
            f"cloning repo {address!r} to {local_path!r}",
        )

        self._process = subprocess.Popen(
            ["git", "clone", "--progress", address, local_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        window = aui.ProgressbarDialogWindow(
            title=text.ACTION_TITLE,
            message=text.CLONING_FOR % address,
            window_icon_path=aui.get_action_icon_path(text.UUID),
            timeout_callback=self._handle_progress,
            timeout_ms=35,
        )

        window.run()
        window.destroy()

        return self._process.poll() == 0

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

        folder_path = os.path.join(self._directory, folder_name)
        formal_address = self._formalize_address(address)
        success = self.clone_git_repo(formal_address, folder_path)

        if not success or not os.path.exists(folder_path):
            self.prompt_unsuccessful_cloning(formal_address)
            exit(1)

        self.prompt_successful_cloning(folder_path)

    def _handle_progress(self, user_data, window: aui.ProgressbarDialogWindow) -> bool:
        if self._process and self._process.poll() is None:
            try:
                if self._process.stderr.readable():
                    self._buff += self._process.stderr.read(8).decode("utf-8")
                    window.progressbar.set_text(roverride(self._buff.split("\n")[-1]))
                window.progressbar.pulse()
            except UnicodeDecodeError as e:
                print("Action clone-git-repo@anaximeno:", "Exception:", e)

        if self._process.poll() is not None:
            window.stop()
            window.destroy()
            return False

        return True

    def prompt_successful_cloning(self, folder_path):
        print(
            "Action clone-git-repo@anaximeno:",
            "Info:",
            f"repo {folder_path!r} was cloned successfully",
        )
        window = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            window_icon_path=aui.get_action_icon_path(text.UUID),
            message=text.SUCCESSFUL_CLONING % f"<b>{folder_path}</b>",
        )
        window.run()
        window.destroy()

    def prompt_unsuccessful_cloning(self, repository_address):
        print(
            "Action clone-git-repo@anaximeno:",
            "Error:",
            f"repo {repository_address!r} wasn't cloned successfully",
        )
        window = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            window_icon_path=aui.get_action_icon_path(text.UUID),
            message=text.UNSUCCESSFUL_CLONING % f"<b>{repository_address}</b>",
        )
        window.run()
        window.destroy()


if __name__ == "__main__":
    app = GitRepoCloneApp(directory=sys.argv[1].replace("\\ ", " "))
    app.run()
