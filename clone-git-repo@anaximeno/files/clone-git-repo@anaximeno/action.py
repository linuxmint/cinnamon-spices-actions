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


DEBUG = os.environ.get("NEMO_DEBUG") == "Actions"


def log(*args, **kwargs):
    if DEBUG is True:
        print(f"Action {text.UUID}:", *args, **kwargs)


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

    def __init__(self, directory: str) -> None:
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self._win_icon_path = aui.get_action_icon_path(text.UUID)
        self._directory = directory
        self._process = None
        self._formal_address = ""
        self._folder_path = ""
        self._buff = ""

    def get_address_from_clipboard(self) -> str:
        clipcontent = self.clipboard.wait_for_text()

        addresscontent = ""
        if clipcontent and self.extract_folder_name_from_address(clipcontent):
            addresscontent = clipcontent

        log(
            "Info:",
            (
                f"got address {addresscontent!r} from clipboard"
                if addresscontent != ""
                else "couldn't get address from clipboard"
            ),
        )

        return addresscontent

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
            log("Info: user cancelled the operation")
            exit(1)

        response = response.strip()

        if response == "":
            log("Error: invalid repository address")
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
        log(f"Error: invalid repository address {address!r}")
        window = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            message=text.ADDRESS_INVALID,
            window_icon_path=self._win_icon_path,
        )
        window.run()
        window.destroy()

    def prompt_user_folder_name_invalid(self, folder_name: str) -> None:
        log(f"Error: invalid folder name {folder_name!r}")
        window = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            message=text.FOLDER_NAME_INVALID,
            window_icon_path=self._win_icon_path,
        )
        window.run()
        window.destroy()

    def prompt_folder_already_exists(self, folder_name: str) -> None:
        log(f"Error: folder already exists {self._folder_path!r}")
        window = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            message=text.FOLDER_ALREADY_EXISTS_AT_PATH % f"<b>{folder_name}</b>",
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
            ## XXX: not working when prepending 'ssh://' to the
            ## address.
            pass
        elif address.startswith("://"):
            address = f"{self.ASSUME_PROTOCOL}{address}"
        elif not "://" in address:
            address = f"{self.ASSUME_PROTOCOL}://{address}"

        if not address.endswith(".git"):
            address = f"{address}.git"

        return address

    def clone_git_repo(self, address: str, local_path: str) -> bool:
        log(f"Info: cloning from {address!r}")
        log(f"Info: cloning to {local_path!r}")

        self._process = subprocess.Popen(
            ["git", "clone", "--progress", address, local_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        window = aui.ProgressbarDialogWindow(
            title=text.ACTION_TITLE,
            message=text.CLONING_FOR % address,
            window_icon_path=self._win_icon_path,
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
            exit(1)

        if folder_name == "":
            self.prompt_user_folder_name_invalid(folder_name)
            exit(1)

        self._folder_path = os.path.join(self._directory, folder_name)

        if os.path.exists(self._folder_path):
            self.prompt_folder_already_exists(folder_name)
            exit(1)

        self._formal_address = self._formalize_address(address)
        success = self.clone_git_repo(self._formal_address, self._folder_path)

        if not success or not os.path.exists(self._folder_path):
            self.prompt_unsuccessful_cloning(self._formal_address)
            exit(1)

        self.prompt_successful_cloning(self._folder_path)

    def _handle_progress(self, user_data, window: aui.ProgressbarDialogWindow) -> bool:
        if self._process and self._process.poll() is None:
            try:
                if self._process.stderr.readable():
                    self._buff += self._process.stderr.read(8).decode("utf-8")
                    window.progressbar.set_text(roverride(self._buff.split("\n")[-1]))
                window.progressbar.pulse()
            except UnicodeDecodeError as e:
                log("Exception:", e)

        if self._process.poll() is not None:
            window.stop()
            window.destroy()
            return False

        return True

    def prompt_successful_cloning(self, folder_path):
        log(f"Info: repo {folder_path!r} was successfully cloned")
        window = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            window_icon_path=self._win_icon_path,
            message=text.SUCCESSFUL_CLONING % f"<b>{folder_path}</b>",
        )
        window.run()
        window.destroy()

    def prompt_unsuccessful_cloning(self, repository_address):
        log(f"Error: repo {repository_address!r} wasn't cloned successfully")
        if self._buff:
            log(
                "Info:",
                f"Clone from repo {self._formal_address!r} to local folder",
                f"at {self._folder_path!r}: Buffer Data:\n\n{self._buff}\n",
            )
        window = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            window_icon_path=self._win_icon_path,
            message=text.UNSUCCESSFUL_CLONING % f"<b>{repository_address}</b>",
        )
        window.run()
        window.destroy()


if __name__ == "__main__":
    app = GitRepoCloneApp(directory=sys.argv[1].replace("\\ ", " "))
    app.run()
