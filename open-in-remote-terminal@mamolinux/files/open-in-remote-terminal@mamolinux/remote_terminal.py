#!/usr/bin/python3
# -*- coding: utf-8 -*-
# On linux-systems, root of an sftp location is usually mounted at:
# /run/user/<uid>/gvfs/sftp:host=<host-ip>

import os
import sys
import subprocess
import gettext

UUID = "open-in-remote-terminal@mamolinux"
HOME = os.path.expanduser("~")
gettext.bindtextdomain(UUID, os.path.join(HOME, ".local/share/locale"))
gettext.textdomain(UUID)

_ = lambda message: gettext.gettext(message)

print("")

def call_remote(uri):
    remote_address = uri.split('sftp:', 1)[1]
    # print(remote_address)

    if "," in remote_address:
        # in case "/run/user/<uid>/gvfs/sftp:host=<ip>,user=<username>/path"
        # is passed
        remote_host, sep, remote_userpath = remote_address.partition(',')
        # print(remote_address.partition(','))

        # remote path
        remote_user, sep, remote_path = remote_userpath.partition('/')
        # print(remote_userpath.partition('/'))

        # remote user
        # print(remote_user.partition('='))
        key, sep, remote_user = remote_user.partition('=')

        # remote ip
        key, sep, remote_ip = remote_host.partition('=')
        # print(remote_host.partition('='))
    else:
        # in case "/run/user/<uid>/gvfs/sftp:host=<ip>/path" is passed
        # remote path
        remote_host, sep, remote_path = remote_address.partition('/')
        # print(remote_address.partition('/'))

        # in case path contains the home folder and the user, try to use it instead OS user
        home, sep, user = remote_path.partition('/')

        # remote user from path. If not present, ask for username
        if user:
            remote_user = user
        else:
            dialog_args = {}
            dialog_args['title'] = _("Enter remote username")
            dialog_args['username'] = _("Username")
            dialog_cmd = ['zenity --entry --text="%(username)s" --title="%(title)s"' % dialog_args]
            remote_user = subprocess.check_output(dialog_cmd, shell=True).decode("utf-8", "strict").strip('\n')

        # remote ip
        key, sep, remote_ip = remote_host.partition('=')
        # print(remote_host.partition('='))

    ssh_args = {}
    ssh_args['remote_user'] = remote_user
    ssh_args['remote_ip'] = remote_ip
    ssh_args['remote_path'] = remote_path

    # run ssh command
    remote_cmd = [terminal, '-e',
        'ssh %(remote_user)s@%(remote_ip)s -t "cd /%(remote_path)s; $SHELL"' % ssh_args]
    subprocess.call(remote_cmd)


# terminal application
terminal="x-terminal-emulator"

# remote uri
uris = sys.argv[1:]
# print(uris)
for uri in uris:
    # print(uri)
    call_remote(uri)
