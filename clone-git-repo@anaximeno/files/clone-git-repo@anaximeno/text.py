import os
import gettext

UUID = "clone-git-repo@anaximeno"
HOME = os.path.expanduser("~")
gettext.bindtextdomain(UUID, os.path.join(HOME, ".local/share/locale"))
gettext.textdomain(UUID)


_ = lambda message: gettext.gettext(message)


ACTION_TITLE = _("Clone a git repository")

ADDRESS_ENTRY_LABEL = _("Git repository address:")

FOLDER_NAME_ENTRY_LABEL = _("Name to clone as:")

USERNAME_ENTRY_LABEL = _("Username:")

PASSWORD_ENTRY_LABEL = _("Password (or access token):")

ADDRESS_INVALID = _("The Git address '%s' has an unrecognized format. Please review the supported patterns at %s and try again.")
