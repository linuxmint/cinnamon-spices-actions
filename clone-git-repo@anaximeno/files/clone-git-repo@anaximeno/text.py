import os
import gettext

UUID = "clone-git-repo@anaximeno"
HOME = os.path.expanduser("~")
gettext.bindtextdomain(UUID, os.path.join(HOME, ".local/share/locale"))
gettext.textdomain(UUID)


_ = lambda message: gettext.gettext(message)


ACTION_TITLE = _("Clone a git repository")

GIT_URLS_TEXT = _("git urls")

FOLDER_NAME_ENTRY_LABEL = _("Enter the name for the cloned folder:")

FOLDER_NAME_INVALID = _(
    "The entered name is invalid. Please choose a name that follows folder naming rules."
)

GIT_URL_PATTERNS_LINK = (  # NOTE: this don't need translation.
    "<a href='https://git-scm.com/docs/git-clone#_git_urls'>%s</a>" % GIT_URLS_TEXT
)

ADDRESS_ENTRY_LABEL = _("Repository Address:")

ADDRESS_INVALID = (
    _(
        "The given Git address has an unrecognized format. "
        "Please review the supported patterns at %s and try again."
    )
    % GIT_URL_PATTERNS_LINK
)

CLONING_FOR = _("Cloning %s")

SUCCESSFUL_CLONING = _("Repository successfully cloned to %s")

UNSUCCESSFUL_CLONING = _("Error cloning repository %s !")

FOLDER_ALREADY_EXISTS_AT_PATH = _(
    "A folder named %s already exists in this location."
    " Please choose a different name or delete the existing folder."
)
