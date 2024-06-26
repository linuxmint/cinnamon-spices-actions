#!/usr/bin/python3
import sys
from pathlib import Path
from typing import Optional, Tuple

import aui
import gi
import text
from converters import AudioConverter, Converter, ImageConverter, VideoConverter
from custom_aui import SelectDropdownDialogWindow
from gi.repository import Gtk

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")

FORMATTERS = {
    "IMAGE": {
        "CONVERTER": ImageConverter,
        "FORMATS": (
            "BMP",
            "GIF",
            "HEIC",
            "ICO",
            "JPEG",
            "PNG",
            "TIFF",
            "WEBP",
        ),
    },
    "VIDEO": {
        "CONVERTER": VideoConverter,
        "FORMATS": (
            "3GP",
            "AVI",
            "FLV",
            "MKV",
            "MOV",
            "MP4",
            "WEBM",
        ),
    },
    "AUDIO": {
        "CONVERTER": AudioConverter,
        "FORMATS": (
            "AAC",
            "AIFF",
            "FLAC",
            "M4A",
            "MP3",
            "OGG",
            "OPUS",
            "WAV",
            "WMA",
        ),
    },
}


class Action:
    def __init__(self, file: Path):
        self.file: Path = file
        if not self.valid_file():
            return

        self.file_format_type: str = self._get_file_format_type()

        self.target_formats: Tuple = self._get_available_formats()

        if not self.target_formats:
            aui.InfoDialogWindow(
                title=text.NOT_SUPPORTED_TITLE,
                message=text.NOT_SUPPORTED_LABEL,
            ).run()
            return

        self.target_format: str = self._select_format()

        if not self.target_format:
            return

        self.converter: Converter = FORMATTERS[self.file_format_type]["CONVERTER"](
            self.file, self.target_format
        )
        self.converter.convert()

    def valid_file(self) -> bool:
        if not self.file.exists() or not self.file.is_file():
            aui.InfoDialogWindow(
                title=text.INVALID_FILE_TITLE, message=text.INVALID_FILE_MESSAGE
            ).run()
            return False

        if not self.file.suffix:
            aui.InfoDialogWindow(
                title=text.NO_FILE_EXTENSION_TITLE,
                message=text.NO_FILE_EXTENSION_MESSAGE,
            ).run()
            return False

        return True

    def _get_file_format_type(self) -> Optional[str]:
        suffix = self.file.suffix[1:].upper()

        return next(
            (key for key, value in FORMATTERS.items() if suffix in value["FORMATS"]),
            None,
        )

    def _get_available_formats(self) -> Optional[Tuple[str]]:
        return (
            FORMATTERS[self.file_format_type]["FORMATS"]
            if self.file_format_type
            else None
        )

    def _select_format(self) -> str:
        dialog = SelectDropdownDialogWindow(
            title=text.SELECT_TITLE,
            label=text.SELECT_LABEL,
            choices=self.target_formats,
            default_choice=self.target_formats[0],
        )

        dialog.run()
        target_format = dialog.get_selected()
        dialog.destroy()
        return target_format


def main():
    if len(sys.argv) == 2:
        Action(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
