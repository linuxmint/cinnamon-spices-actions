#!/usr/bin/python3
import os, sys, pathlib
import subprocess
import aui
import text


def get_append_to_file_perm(filename) -> bool:
    window = aui.QuestionDialogWindow(
        message=text.FILE_EXISTS % filename,
        window_icon_path=aui.get_action_icon_path(text.UUID),
        title=text.ACTION_TITLE,
    )
    response = window.run()
    window.destroy()
    return response == aui.QuestionDialogWindow.RESPONSE_YES


def get_file_name(default_filename: str = None) -> str:
    window = aui.EntryDialogWindow(
        title=text.ACTION_TITLE,
        window_icon_path=aui.get_action_icon_path(text.UUID),
        label=text.ENTRY_LABEL,
        default_text=default_filename,
    )
    response = window.run()
    window.destroy()
    return response


def prompt_invalid_file_name() -> None:
    window = aui.InfoDialogWindow(
        title=text.ACTION_TITLE,
        message=text.INVALID_FILE_NAME,
        window_icon_path=aui.get_action_icon_path(text.UUID),
    )
    window.run()
    window.destroy()


def main() -> None:
    if len(sys.argv) < 2:
        exit(1)

    directory = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) > 2 else None

    # NOTE: For some reason nemo is sending the directory as
    # the filename if no file is selected.
    if os.path.isdir(filename):
        filename = None

    clipcontent = subprocess.run(
        ["xclip", "-out", "-selection", "clipboard"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ).stdout.decode("utf-8")

    if filename is None:
        response = get_file_name()

        if response is not None and response.strip() != "":
            filename = os.path.join(directory, response)
            if os.path.exists(filename) and not get_append_to_file_perm(filename):
                exit(1)
            with open(filename, "at") as file:
                file.write(clipcontent)
        else:
            if response is not None:
                prompt_invalid_file_name()
            exit(1)
    else:
        if os.path.exists(filename):
            response = get_file_name(default_filename=pathlib.Path(filename).name)

            if response is None:
                exit(1)

            if response.strip() == "":
                prompt_invalid_file_name()
                exit(1)

            filename = os.path.join(directory, response)
            if os.path.exists(filename) and not get_append_to_file_perm(filename):
                exit(1)

        with open(filename, "at") as file:
            file.write(clipcontent)


if __name__ == "__main__":
    main()
