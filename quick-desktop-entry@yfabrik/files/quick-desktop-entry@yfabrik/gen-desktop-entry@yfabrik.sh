#!/bin/bash
file=$1
dirpath=$2
filepath=$3
filename=$4
desktopfile=$HOME/.local/share/applications/$filename.desktop


case $(xdg-mime query filetype $file) in

application/vnd.appimage)
    dirpath="$HOME/Applications"
    mkdir -p ${dirpath}
    chmod +x $file
    mv $file ${dirpath}
    filepath=$HOME/Applications/$file
    command=$filepath
    ;;
application/x-ms-dos-executable)
    command="wine $filepath"
    ;;
application/*)
    command=$filepath
    ;;
*)
    command="xdg-open $filepath"
    ;;

esac


cat >$desktopfile <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Exec=$command
Name=$filename
Comment=$filename
Icon=$filename
Path=$dirpath
#StartupNotify=true
#Categories=#Utility;Development;Office;Graphics;Network;AudioVideo;System;Settings;Education;Game;Science;Accessibility
## if icon not working in the taskbar get from ' xprop WM_CLASS '
#StartupWMClass=glfw-application
#Keyword=
#MimeType=

# Desktop Action Open
# Name=Open
# Exec=/path/to/open-command
# Icon=open-icon
# Tooltip=Open the application

EOF
chmod +x $desktopfile
xdg-open $desktopfile
