#!/bin/sh
if [ ! -e ~/.killdone ]
then
zenity --info --title="XKill" --text="Click on the application that you want to kill."
echo "This instruction for XKill will not be shown again." > ~/.killdone
fi
sleep 1
xkill
