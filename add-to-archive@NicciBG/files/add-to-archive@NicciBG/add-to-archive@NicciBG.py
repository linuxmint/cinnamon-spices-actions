#!/usr/bin/env python3
"""Nemo "Create Archive" action entry point.

Nemo runs this with the selected files as arguments (see the %F in the
Exec= line of add-to-archive@NicciBG.nemo_action.in).
"""

import gettext
import os
import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

UUID = "add-to-archive@NicciBG"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Makes _() available to every module in this directory without each one
# having to import gettext itself.
gettext.install(UUID, os.path.join(SCRIPT_DIR, "po"))

import ui  # noqa: E402  (needs sys.path/_ set up first)


def main():
    files = [os.path.abspath(f) for f in sys.argv[1:]]

    if not files:
        dialog = Gtk.MessageDialog(
            transient_for=None, modal=True,
            message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
            text=_("No files were selected."))
        dialog.run()
        dialog.destroy()
        return 1

    if ui.show_archive_window(files):
        Gtk.main()

    return 0


if __name__ == "__main__":
    sys.exit(main())
