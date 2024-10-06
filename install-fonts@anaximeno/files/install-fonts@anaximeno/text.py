import os, gettext

UUID = "install-fonts@anaximeno"
HOME = os.path.expanduser("~")

gettext.bindtextdomain(UUID, os.path.join(HOME, ".local/share/locale"))
gettext.textdomain(UUID)


def _(msg: str) -> str: return gettext.gettext(msg)


