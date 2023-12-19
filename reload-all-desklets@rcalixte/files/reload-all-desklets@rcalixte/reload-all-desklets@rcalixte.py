#!/usr/bin/env python3

import os
import gettext
import signal
import subprocess
import sys
import time

from gi.repository import Gio, GLib

UUID: str = 'reload-all-desklets@rcalixte'
HOME: str = os.path.expanduser('~')
gettext.bindtextdomain(f'{HOME}/.local/share/locale')
gettext.textdomain(UUID)
TEXT: str = gettext.gettext("All active desklets were reloaded.")
BUS_TYPE: Gio.BusType = Gio.BusType.SESSION
DBUS_PATH: str = 'org.Cinnamon'
DESKLET: str = 'DESKLET'
FLAG: Gio.DBusProxyFlags = Gio.DBusProxyFlags.NONE
GSETTING: str = '/org/Cinnamon'
KEY: str = 'enabled-desklets'
SETTINGS: str = 'org.cinnamon'
BADS: set = {'cpuload@kimse'}


def main():
    settings: Gio.Settings = Gio.Settings.new(SETTINGS)
    enabled_desklets: set = {x.split(':')[0] for x in settings.get_strv(KEY)}

    try:
        proxy: Gio.DBusProxy = Gio.DBusProxy.new_for_bus_sync(BUS_TYPE, FLAG,
                                                              None, DBUS_PATH,
                                                              GSETTING,
                                                              DBUS_PATH, None)
    except GLib.Error:
        return

    if not proxy:
        sys.exit(1)

    for desklet in enabled_desklets:
        if desklet not in BADS:
            try:
                proxy.ReloadXlet('(ss)', desklet, DESKLET)
                time.sleep(0.05)
                proxy.ReloadXlet('(ss)', desklet, DESKLET)
                time.sleep(0.01)
            except GLib.GError:
                time.sleep(0.05)

    subprocess.run(["/usr/bin/zenity", "--info", f"--text={TEXT}"])


if __name__ == "__main__":
    main()
