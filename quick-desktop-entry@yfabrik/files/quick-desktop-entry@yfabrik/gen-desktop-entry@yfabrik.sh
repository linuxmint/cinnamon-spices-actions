#!/bin/bash
filepath="${1}"
parentpath="${2}"
filename="${filepath:${#parentpath}+1}"

desktopfile=$HOME/.local/share/applications/"${filename// /_}".desktop
filemime=$(xdg-mime query filetype "${filepath}")
mimedefault=$(xdg-mime query default "${filemime}")

if [[ -n "${mimedefault}" ]]; then

	command="xdg-open \"${filepath}\""
	
else

	if [[ "${filemime}" == "application/vnd.appimage" ]]; then

		parentpath="$HOME/Applications"
		mkdir -p "${parentpath}"
		chmod +x "${filepath}"
		mv "${filepath}" "${parentpath}"
		filepath="${parentpath}/${filename}"
		#TODO extract icon
		command="${filepath}"
	else
		command="${filepath}"
	fi
fi

cat >"${desktopfile}" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Exec=${command}
Name=${filename}
Comment=${filename}
Path=${parentpath}
#Icon=
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

chmod +x "${desktopfile}"
xdg-open "${desktopfile}"
