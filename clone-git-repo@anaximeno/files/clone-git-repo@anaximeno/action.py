#!/usr/bin/python3
import os
import sys
import re
import aui
import text


REPO_NAME_REGEX = r"\/([^\/]+)(\.git)?$"

ASSUME_PROTOCOL = "https"


def get_repository_address() -> str | None:
    window = aui.EntryDialogWindow(
        title=text.ACTION_TITLE,
        window_icon_path=aui.get_action_icon_path(text.UUID),
        label=text.ADDRESS_ENTRY_LABEL,
    )
    response = window.run()
    window.destroy()
    return response


def get_name_to_clone_as(default_name: str = None) -> str | None:
    window = aui.EntryDialogWindow(
        title=text.ACTION_TITLE,
        window_icon_path=aui.get_action_icon_path(text.UUID),
        label=text.FOLDER_NAME_ENTRY_LABEL,
        default_text=default_name,
    )
    response = window.run()
    window.destroy()
    return response


def get_repo_name_from_address(address: str) -> str:
    re_match = re.search(REPO_NAME_REGEX, address)
    if re_match is not None:
        return re_match.group(1).replace(".git", "")
    return ""


def prompt_git_address_invalid(address: str) -> bool:
    window = aui.InfoDialogWindow(
        title=text.ACTION_TITLE,
        message=text.ADDRESS_INVALID
        % (address, "https://to-be-added.url"),  # XXX: update url
        window_icon_path=aui.get_action_icon_path(text.UUID),
    )
    window.run()
    window.destroy()


def formalize_address(address: str) -> str:
    if not address.startswith("git@") and not "://" in address:
        address = f"{ASSUME_PROTOCOL}://{address}"
    if not address.endswith(".git"):
        address = f"{address}.git"
    return address


def main() -> None:
    directory = sys.argv[1].replace("\\ ", " ")

    address = get_repository_address().strip()
    repo_name = get_repo_name_from_address(address)

    if address == "" or repo_name == "":
        prompt_git_address_invalid(address)
        exit(1)

    formal_address = formalize_address(address)
    folder_name = get_name_to_clone_as(repo_name)


if __name__ == "__main__":
    main()