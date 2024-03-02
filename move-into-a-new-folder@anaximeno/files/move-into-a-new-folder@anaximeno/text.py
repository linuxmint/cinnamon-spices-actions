import os
import gettext

UUID = "move-into-a-new-folder@anaximeno"
HOME = os.path.expanduser("~")
gettext.bindtextdomain(UUID, os.path.join(HOME, ".local/share/locale"))
gettext.textdomain(UUID)


_ = lambda message: gettext.gettext(message)


TITLE = _("Move Into a New Folder")

TEXT = _("Name of the new folder:")

ENTRY_DEFAULT = _("New Folder")

FOLDER_EXISTS = _(
    "Folder '%s' already exists inside the current directory,"
    " do you want to move the selected files inside?"
)

FOLDER_NOT_CREATED = _(
    "Couldn't create a new folder '%s' inside the current directory!"
)

N_NOT_MOVED = _("Could not move %d of the selected items into a new folder!")

ALL_NOT_MOVED = _("Could not move any of the selected items into a new folder!")
