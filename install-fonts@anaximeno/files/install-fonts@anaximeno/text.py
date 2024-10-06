import os, gettext

UUID = "install-fonts@anaximeno"
HOME = os.path.expanduser("~")

gettext.bindtextdomain(UUID, os.path.join(HOME, ".local/share/locale"))
gettext.textdomain(UUID)


def _(msg: str) -> str:
    return gettext.gettext(msg)


WINDOW_TITLE = _("Install fonts")

SUCCESSFUL_INSTALL = _("Fonts were installed successfuly!")

UNSUCCESSFUL_INSTALL = _("Fonts could not be installed!")

PARTIAL_SUCCESS_INSTALL = _("Some fonts could not be installed!")

CACHE_UPDATE_PROGRESS_MESSAGE = _("Updating fonts cache...")

CACHE_NOT_UPDATED = _(
    "Could not update fonts cache.\n"
    "The installation of the fonts may not take immediate effect."
)

POST_INSTALL_EXPANDER_LABEL = _("Post installation issues")

SIMILAR_FONT_FILE_ALREADY_INSTALLED = _(
    "Some similar fonts are already installed.\nWhat should be done in this case?"
)

CANCEL = _("Cancel")

IGNORE = _("Ignore")

OVERRIDE = _("Override")
