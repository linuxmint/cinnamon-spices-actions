import os
import gettext

UUID = "clone-git-repo@anaximeno"
HOME = os.path.expanduser("~")
gettext.bindtextdomain(UUID, os.path.join(HOME, ".local/share/locale"))
gettext.textdomain(UUID)


_ = lambda message: gettext.gettext(message)


ACTION_TITLE = "Clone a git repository"

ADDRESS_ENTRY_LABEL = "Git repository address:"

FOLDER_NAME_ENTRY_LABEL = "Name to clone as:"

USERNAME_ENTRY_LABEL = "Username:"

PASSWORD_ENTRY_LABEL = "Password (or access token):"
