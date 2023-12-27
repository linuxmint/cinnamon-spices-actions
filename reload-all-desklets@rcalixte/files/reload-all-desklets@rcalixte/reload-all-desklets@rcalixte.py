#!/usr/bin/env python3

import gettext
import os
import subprocess
import time

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk

UUID: str = 'reload-all-desklets@rcalixte'
HOME: str = os.path.expanduser('~')
gettext.bindtextdomain(UUID, f'{HOME}/.local/share/locale')
gettext.textdomain(UUID)
TEXT: str = gettext.gettext('Reload successfully completed.')
DESKLET: str = 'DESKLET'
ED_KEY: str = 'enabled-desklets'
LOCKED: str = 'lock-desklets'
SETTINGS: str = 'org.cinnamon'
AVOIDS: set = {'cpuload@kimse', 'show-remote-ip-desklet@nejdetckenobi'}
SESSION: str = os.environ['XDG_SESSION_TYPE']


def main():
    settings: Gio.Settings = Gio.Settings.new(SETTINGS)
    enabled_desklets: set = {uuid.split(':')[0] for uuid in settings.get_strv(ED_KEY)}

    is_reloaded: bool = False
    for desklet in enabled_desklets:
        if desklet not in AVOIDS:
            is_reloaded = True
            subprocess.run(['/usr/bin/cinnamon-dbus-command', 'ReloadXlet',
                            desklet, DESKLET], stdout=subprocess.DEVNULL,
                            check=False)
            time.sleep(0.05)
            subprocess.run(['/usr/bin/cinnamon-dbus-command', 'ReloadXlet',
                            desklet, DESKLET], stdout=subprocess.DEVNULL,
                            check=False)
            time.sleep(0.01)

    if is_reloaded and SESSION == 'x11' and not settings.get_boolean(LOCKED):
        win = Gtk.Window(title='')
        dialog = Gtk.MessageDialog(transient_for=win, flags=0, text=TEXT,
                                   message_type=Gtk.MessageType.INFO,
                                   buttons=Gtk.ButtonsType.OK)
        dialog.connect('destroy', lambda *_: None)
        dialog.connect('response', lambda *_: None)
        dialog.run()
        dialog.destroy()


if __name__ == '__main__':
    main()
