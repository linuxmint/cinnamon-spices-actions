#!/bin/bash
filepath="${1}"
parentpath="${2}"
filename="${filepath:${#parentpath}+1}"
desktopfile=$HOME/.local/share/applications/"${filename// /_}".desktop

#source conf file
#default_path isAsking
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
CONFIG_FILE="${SCRIPT_DIR}/quick-desktop-entry.conf"
source "${CONFIG_FILE}"

filemime=$(xdg-mime query filetype "${filepath}")
mimedefault=$(xdg-mime query default "${filemime}")

####zenity
directory_choice=(true "${default_path}" false "choose a directory" false "dont move" false "set and never ask again")
definitive_choice=(true "${default_path}" false "choose a directory" false "dont move")
ask_user() {
	zenity --list \
		--title "move appimage" \
		--text "where to move the appimage ?" \
		--radiolist \
		--column "" \
		--column=path \
		"${@}"
	if [[ $? -eq 1 ]]; then
		exit
	fi
}

edit_conf() {
	read IN
	sed -i "s|default_path=.*|default_path=\"${IN}\"|" "${CONFIG_FILE}"
	sed -i "s|isAsking=.*|isAsking=false|" "${CONFIG_FILE}"
	echo "${IN}"
}

process_user_answer() {
	read IN
	case "${IN}" in
	"dont move") echo "" ;;
	"choose a directory") zenity --file-selection --directory ;;
	"set and never ask again") ask_user "${definitive_choice[@]}" | process_user_answer | edit_conf ;;
	*) echo "${IN}" ;;
	esac

}

if [[ -n "${mimedefault}" ]]; then

	command="xdg-open \"${filepath}\""

else

	if [[ "${filemime}" == "application/vnd.appimage" ]]; then
		if [[ $isAsking == true ]]; then
			user_choice=$(ask_user "${directory_choice[@]}" | process_user_answer)
			parentpath=${user_choice:-$parentpath}
		else
			parentpath=${default_path:-$parentpath}
		fi

		mkdir -p "${parentpath}"
		chmod +x "${filepath}"
		mv "${filepath}" "${parentpath}"
		filepath="${parentpath}/${filename}"
		#TODO extract icon

	fi
	command="${filepath}"
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
