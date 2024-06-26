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
        "DEFAULT": "PNG",
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
        "DEFAULT": "MP4",
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
        "DEFAULT": "MP3",
    },
}


class Action:
    """
    Class representing an action to convert a file to a different format.

    Attributes:
        file (Path): The path to the file to be converted.
        file_format_type (str): The type of the file format.
        target_formats (Tuple): Available target formats for conversion.
        target_format (str): The selected target format for conversion.
        converter (Converter): The converter instance to perform the conversion.

    Methods:
        valid_file() -> bool: Checks if the file is valid for conversion.
        _get_file_format_type() -> Optional[str]: Determines the file format typebased on its suffix.
        _get_available_formats() -> Optional[Tuple[str]]: Retrieves available target formats based on the file format type.
        _select_format() -> str: Displays a dialog window to select the target format for conversion.

    When an instance of this class is created, it checks the validity of the file, determines the file format type,
    retrieves available target formats, selects a target format, and performs the conversion using the selected converter.
    """

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
        """
        Checks if the file is valid for conversion.

        Returns:
            bool: True if the file is valid for conversion, False otherwise.
        """
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
        """
        Determines the file format type based on the suffix of the file.

        Returns:
            Optional[str]: The file format type if it is found in the FORMATTERS dictionary, None otherwise.
        """
        suffix = self.file.suffix[1:].upper()

        return next(
            (key for key, value in FORMATTERS.items() if suffix in value["FORMATS"]),
            None,
        )

    def _get_available_formats(self) -> Optional[Tuple[str]]:
        """
        Determines the available target formats based on the file format type.

        Returns:
            Optional[Tuple[str]]: A tuple of available target formats if the file format type is found in the FORMATTERS dictionary, None otherwise.
        """
        return (
            FORMATTERS[self.file_format_type]["FORMATS"]
            if self.file_format_type
            else None
        )

    def _select_format(self) -> str:
        """
        Displays a dialog window to select the target format for conversion.

        Returns:
            str: The selected target format for conversion.
        """
        dialog = SelectDropdownDialogWindow(
            title=text.SELECT_TITLE,
            label=text.SELECT_LABEL,
            choices=self.target_formats,
            default_choice=FORMATTERS[self.file_format_type]["DEFAULT"],
        )

        dialog.run()
        target_format = dialog.get_selected()
        dialog.destroy()
        return target_format


def main():
    """
    Main function to execute the file conversion action based on the provided command-line argument.

    This function checks if there is exactly one command-line argument provided.
    If so, it creates an instance of the Action class with the file path obtained from the command-line argument,
    triggering the file conversion process.

    Parameters:
        None

    Returns:
        None
    """
    if len(sys.argv) == 2:
        Action(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
