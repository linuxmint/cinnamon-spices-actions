#!/usr/bin/python3
import os
import sys
import aui
import text

from urllib.parse import urlparse


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


def check_git_address_valid(address: str) ->  bool:
    pass # TODO


def parse_repo_name(address: str) -> str:
    pass # TODO


def main() -> None:
    directory = sys.argv[1]
    # TODO

if __name__ == "__main__":
    main()
