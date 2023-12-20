#!/usr/bin/env python3

import gettext
import os
import sys
import time

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GLib, Gtk

UUID: str = 'reload-all-desklets@rcalixte'
HOME: str = os.path.expanduser('~')
gettext.bindtextdomain(f'{HOME}/.local/share/locale')
gettext.textdomain(UUID)
TEXT: str = gettext.gettext('Reload successfully completed.')
OK: str = gettext.gettext('OK')
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

    if os.environ['XDG_SESSION_TYPE'] == 'x11':
        win = Gtk.Window(title='')
        dialog = Gtk.MessageDialog(transient_for=win, flags=0, text=TEXT,
                                   message_type=Gtk.MessageType.INFO)
        dialog.add_button(OK, Gtk.ResponseType.CLOSE)
        dialog.connect('destroy', Gtk.main_quit)
        dialog.run()
        dialog.destroy()
        Gtk.main()


if __name__ == '__main__':
    main()
