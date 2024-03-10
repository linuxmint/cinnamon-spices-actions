import os
import gettext

UUID = "clone-git-repo@anaximeno"
HOME = os.path.expanduser("~")
gettext.bindtextdomain(UUID, os.path.join(HOME, ".local/share/locale"))
gettext.textdomain(UUID)


_ = lambda message: gettext.gettext(message)

# TODO: improve text before release!

ACTION_TITLE = _("Clone a git repository")

GIT_URLS_TEXT = _("git urls")

FOLDER_NAME_ENTRY_LABEL = _("Name to clone as:")

USERNAME_ENTRY_LABEL = _("Username:")

PASSWORD_ENTRY_LABEL = _("Password (or access token):")

FOLDER_NAME_INVALID = _("Invalid folder name!")

GIT_URL_PATTERNS_LINK = (  # NOTE: this don't need a translation.
    "<a href='https://git-scm.com/docs/git-clone#_git_urls'>%s</a>" % GIT_URLS_TEXT
)

ADDRESS_ENTRY_LABEL = (
    _("Git repository address (see %s for supported addresses):")
    % GIT_URL_PATTERNS_LINK
)


ADDRESS_INVALID = (
    _(
        "The given Git address has an unrecognized format. "
        "Please review the supported patterns at %s and try again."
    )
    % GIT_URL_PATTERNS_LINK
)


ADDRESS_IS_NOT_GIT_REPO = _(
    "The provided address '%s' is not accessible or is not a git repository."
)

CLONING_FOR = _("Cloning for %s")

SUCCESSFUL_CLONING = _("Repository succesfuly cloned to %s")

UNSUCCESSFUL_CLONING = _("Repository at %s couldn't be cloned successfully!")
