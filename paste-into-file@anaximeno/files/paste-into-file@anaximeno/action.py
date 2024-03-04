#!/usr/bin/python3
import os, sys
import pathlib
import aui
import text
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


APPEND_MODE = "at"
OVERRIDE_MODE = "wt"


def get_file_exists_chosen_action(filename) -> bool:
    window = aui.RadioChoiceDialogWindow(
        radio_buttons=(
            aui.RadioChoiceButton(APPEND_MODE, text.APPEND_TO_END),
            aui.RadioChoiceButton(OVERRIDE_MODE, text.OVERRIDE_CONTENT),
        ),
        radio_orientation=aui.RadioChoiceDialogWindow.VERTICAL_RADIO,
        radio_spacing=5,
        label=text.STATE_THAT_FILE_EXISTS % filename,
        window_icon_path=aui.get_action_icon_path(text.UUID),
        title=text.ACTION_TITLE,
    )
    choice = window.run()
    window.destroy()
    return choice


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


def prompt_no_clipcontent() -> None:
    window = aui.InfoDialogWindow(
        title=text.ACTION_TITLE,
        window_icon_path=aui.get_action_icon_path(text.UUID),
        message=text.NO_CLIPBOARD_CONTENT,
    )
    window.run()
    window.destroy()


def paste_content_into_file(filepath, content, file_mode=APPEND_MODE) -> bool:
    if os.path.isdir(filepath):
        return False
    try:
        with open(filepath, file_mode) as file:
            file.write(content)
        return True
    except Exception as e:
        return False


def main() -> None:
    if len(sys.argv) < 2:
        exit(1)

    file_paste_mode = APPEND_MODE  # Use the less harmful operation as the default
    directory = sys.argv[1].replace("\\ ", " ")
    filepath = sys.argv[2].replace("\\ ", " ") if len(sys.argv) > 2 else None

    # NOTE: For some reason nemo is sending the directory as
    # the filepath if no file is selected.
    if os.path.isdir(filepath):
        filepath = None

    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipcontent = clipboard.wait_for_text()

    if not clipcontent:
        prompt_no_clipcontent()
        exit(1)

    if filepath is None:
        filename = get_file_name()

        if filename is not None and filename.strip() != "":
            filepath = os.path.join(directory, filename)
            if os.path.isdir(filepath):
                prompt_invalid_file_name()
                exit(1)

            if os.path.exists(filepath):
                choice = get_file_exists_chosen_action(filename)

                if not choice:
                    exit(1)

                file_paste_mode = choice

            paste_content_into_file(filepath, clipcontent, file_paste_mode)
        else:
            if filename is not None:
                prompt_invalid_file_name()
            exit(1)
    else:
        if os.path.exists(filepath):
            filename = get_file_name(default_filename=pathlib.Path(filepath).name)

            if filename is None:
                exit(1)

            filepath = os.path.join(directory, filename)

            if filename.strip() == "" or os.path.isdir(filepath):
                prompt_invalid_file_name()
                exit(1)

            if os.path.exists(filepath):
                choice = get_file_exists_chosen_action(filename)

                if not choice:
                    exit(1)

                file_paste_mode = choice

        paste_content_into_file(filepath, clipcontent, file_paste_mode)


if __name__ == "__main__":
    main()
