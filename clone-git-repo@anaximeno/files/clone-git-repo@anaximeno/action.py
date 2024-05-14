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


NEMO_DEBUG = os.environ.get("NEMO_DEBUG", "")
DEBUG = "Actions" in NEMO_DEBUG if NEMO_DEBUG else False
UNCOMMON_REPO_NAME_CHARS_SET = set("!\"#$%&'()*+,.:;<=>?@[\\]^`{|}~")
REPO_NAME_REGEX = r"\/([^\/]+)(\.git)?$"


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
    def __init__(self, directory: str, assume_protocol: str = "http") -> None:
        self._directory = directory
        self._assume_protocol = assume_protocol
        self._win_icon_path = aui.get_action_icon_path(text.UUID)
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self._process = None
        self._formal_address = ""
        self._folder_path = ""
        self._buff = ""

    def get_address_from_clipboard(self) -> str:
        clipcontent: str = self.clipboard.wait_for_text()
        addresscontent: str = ""

        if clipcontent:
            clipcontent = clipcontent.strip().rstrip("/").rstrip("?")
            reponame = self.extract_repo_name_from_address(clipcontent)
            if reponame and not " " in clipcontent:
                addresscontent = clipcontent
                log("Info: Got clipboard address:", addresscontent)

        if not addresscontent:
            log("Info: Couldn't get a valid git address from the clipboard")

        return addresscontent

    def extract_repo_name_from_address(self, address: str) -> str:
        re_match = re.search(REPO_NAME_REGEX, address)
        if re_match is not None:
            name = re_match.group(1)
            name = name.replace(".git", "")
            if not any(UNCOMMON_REPO_NAME_CHARS_SET.intersection(name)):
                return name
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
            log("Info: User cancelled the operation")
            exit(1)

        response = response.strip()

        if response == "":
            log("Error: Invalid repository address")
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
        log("Error: Invalid repository address:", address)
        window = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            message=text.ADDRESS_INVALID,
            window_icon_path=self._win_icon_path,
        )
        window.run()
        window.destroy()

    def prompt_user_folder_name_invalid(self, folder_name: str) -> None:
        log("Error: Invalid folder name:", folder_name)
        window = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            message=text.FOLDER_NAME_INVALID,
            window_icon_path=self._win_icon_path,
        )
        window.run()
        window.destroy()

    def prompt_folder_already_exists(self, folder_name: str) -> None:
        log("Error: Folder already exists:", self._folder_path)
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
            address = f"{self._assume_protocol}{address}"
        elif not "://" in address:
            address = f"{self._assume_protocol}://{address}"

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
            expander_label=text.MORE_INFO,
        )

        window.run()
        window.destroy()

        return self._process.poll() == 0

    def run(self) -> None:
        clipaddress = self.get_address_from_clipboard()
        address = self.prompt_user_for_repo_address(clipaddress)
        folder_name = self.extract_repo_name_from_address(address)

        if not address or not folder_name:
            self.prompt_user_git_address_invalid(address)
            exit(1)
        else:
            log("Info: Address:", address)

        folder_name = self.prompt_user_for_cloned_folder_name(folder_name)

        if not folder_name:
            exit(1)

        if folder_name == "":
            self.prompt_user_folder_name_invalid(folder_name)
            exit(1)
        else:
            log("Info: Folder name:", folder_name)

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
                    split_content = self._buff.split("\n")
                    window.progressbar.set_text(roverride(split_content[-1]))
                    expand_text = "\n".join(roverride(line) for line in split_content)
                    window.set_expanded_text(expand_text)
                window.progressbar.pulse()
            except UnicodeDecodeError as e:
                log("Exception:", e)

        if self._process.poll() is not None:
            window.stop()
            window.destroy()
            return False

        return True

    def prompt_successful_cloning(self, folder_path):
        log(f"Info: repo {self._formal_address!r} was successfully cloned")
        window = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            window_icon_path=self._win_icon_path,
            message=text.SUCCESSFUL_CLONING % f"<b>{folder_path}</b>",
        )
        window.run()
        window.destroy()

    def prompt_unsuccessful_cloning(self, repository_address):
        log(f"Error: repo {repository_address!r} wasn't cloned successfully")
        buffer_lines = "\n".join(roverride(line) for line in self._buff.split("\n"))
        stderr_buf = self._process.stderr.read().decode("utf-8")
        cloning_info = buffer_lines + stderr_buf
        log("Error: Git stderr message:", cloning_info)
        window = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            window_icon_path=self._win_icon_path,
            message=text.UNSUCCESSFUL_CLONING % f"<b>{repository_address}</b>",
            expander_label=text.CLONE_INFO,
            expanded_text=cloning_info,
        )
        window.run()
        window.destroy()


if __name__ == "__main__":
    app = GitRepoCloneApp(directory=sys.argv[1].replace("\\ ", " "))
    app.run()
