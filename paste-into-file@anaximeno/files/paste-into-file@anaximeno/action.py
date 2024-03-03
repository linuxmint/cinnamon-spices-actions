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


def append_content_to_file(filepath, content) -> bool:
    if os.path.isdir(filepath):
        return False
    try:
        with open(filepath, "at") as file:
            file.write(content)
        return True
    except Exception as e:
        return False


def main() -> None:
    if len(sys.argv) < 2:
        exit(1)

    directory = sys.argv[1]
    filepath = sys.argv[2] if len(sys.argv) > 2 else None

    # NOTE: For some reason nemo is sending the directory as
    # the filepath if no file is selected.
    if os.path.isdir(filepath):
        filepath = None

    clipcontent = subprocess.run(
        ["xclip", "-out", "-selection", "clipboard"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ).stdout.decode("utf-8")

    if filepath is None:
        response = get_file_name()

        if response is not None and response.strip() != "":
            filepath = os.path.join(directory, response)
            if os.path.isdir(filepath):
                prompt_invalid_file_name()
                exit(1)
            if os.path.exists(filepath) and not get_append_to_file_perm(filepath):
                exit(1)
            append_content_to_file(filepath, clipcontent)
        else:
            if response is not None:
                prompt_invalid_file_name()
            exit(1)
    else:
        if os.path.exists(filepath):
            response = get_file_name(default_filename=pathlib.Path(filepath).name)

            if response is None:
                exit(1)

            if response.strip() == "":
                prompt_invalid_file_name()
                exit(1)

            filepath = os.path.join(directory, response)

            if os.path.isdir(filepath):
                prompt_invalid_file_name()
                exit(1)
            if os.path.exists(filepath) and not get_append_to_file_perm(filepath):
                exit(1)

        append_content_to_file(filepath, clipcontent)


if __name__ == "__main__":
    main()
