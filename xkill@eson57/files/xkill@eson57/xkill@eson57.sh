#!/bin/sh
if [ ! -e ~/.local/share/nemo/actions/xkill@eson57/.killdone ]
then
zenity --info --title="XKill" --text="Click on the application that you want to kill."
echo "This instruction for XKill will not be shown again." > ~/.local/share/nemo/actions/xkill@eson57/.killdone
fi
sleep 1
xkill
