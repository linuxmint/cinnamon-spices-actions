import os
import gettext

UUID = "paste-into-file@anaximeno"
HOME = os.path.expanduser("~")
gettext.bindtextdomain(UUID, os.path.join(HOME, ".local/share/locale"))
gettext.textdomain(UUID)


_ = lambda message: gettext.gettext(message)


ACTION_TITLE = _("Paste into file")

ENTRY_LABEL = _("File name:")

FILE_EXISTS = _(
    "File '%s' already exists. Do you want to append the clipboard content to the end of the file?"
)

INVALID_FILE_NAME = _("Invalid file name!")

NO_CLIPBOARD_CONTENT = _(
    "There's nothing on the clipboard to paste into a file! Aborting operation..."
)
# NOTE: these below aren't used yet, but might need them in a future release
APPEND_TO_END = _("Append to the end of the file")

OVERRIDE_CONTENT = _("Override the content of the file")

FILE_EXISTS = _("File '%s' already exists. How to proceed?")
