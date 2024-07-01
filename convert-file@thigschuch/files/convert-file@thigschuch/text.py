import gettext
import os

UUID = "convert-file@thigschuch"
HOME = os.path.expanduser("~")
gettext.bindtextdomain(UUID, f"{HOME}/.local/share/locale")
gettext.textdomain(UUID)


def _(message) -> str:
    return gettext.gettext(message)


NOT_SUPPORTED_TITLE = _("Error")
NOT_SUPPORTED_LABEL = _("The file format is not supported.")

SELECT_TITLE = _("Select a format")
SELECT_LABEL = _("Select the format to convert the file to.")

CONVERTING_TITLE = _("Converting")
CONVERTING_LABEL = _("Converting file to {format}...")

SUCCESS_TITLE = _("Success")
SUCCESS_MESSAGE = _("The file has been converted to {format}.")

ERROR_TITLE = _("Error")
ERROR_MESSAGE = _("An error occurred while converting the file.")

INVALID_FILE_TITLE = _("Invalid file")
INVALID_FILE_MESSAGE = _("The file is not valid.")

NO_FILE_EXTENSION_TITLE = _("No file name or extension")
NO_FILE_EXTENSION_MESSAGE = _("The file must have a name and an extension.")
