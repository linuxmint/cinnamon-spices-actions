import os, gettext

UUID = "create-desktop-shortcut@anaximeno"
HOME = os.path.expanduser("~")

gettext.bindtextdomain(UUID, os.path.join(HOME, ".local/share/locale"))
gettext.textdomain(UUID)


def _(msg: str) -> str: return gettext.gettext(msg)


ACTION_TITLE = _("Create Desktop Shortcut Action")
SHORTCUTS_NOT_CREATED_MESSAGE = _("Couldn't create all shortcuts!")
FILE_ALREADY_EXISTS_AT_THE_DESKTOP_FOLDER = _(
    "File named '%s' already exists inside the desktop folder!"
    " What should be done?")
