import os, gettext

UUID = "create-desktop-shortcut@anaximeno"
HOME = os.path.expanduser("~")

gettext.bindtextdomain(UUID, os.path.join(HOME, ".local/share/locale"))
gettext.textdomain(UUID)


def _(msg: str) -> str: return gettext.gettext(msg)


ACTION_TITLE = _("Create a desktop shortcut")

SHORTCUTS_NOT_CREATED_MESSAGE = _("Couldn't create all shortcuts!")

FILE_ALREADY_EXISTS_AT_THE_DESKTOP_FOLDER = _(
    "Some items already exist with the same name in the desktop folder, "
    "should they be overridden? (Overridden items in the desktop folder will be sent to the trash.)"
)
