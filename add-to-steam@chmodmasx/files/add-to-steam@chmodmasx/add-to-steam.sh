#!/bin/bash
set -euo pipefail

add_to_steam() {
	local file="$1"
	local basename_file
	basename_file=$(basename "$file")
	local encoded_url
	encoded_url="steam://addnonsteamgame/$(python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=""))' "$file")"

	if command -v steam &>/dev/null; then
		setsid steam "$encoded_url" >/dev/null 2>&1 || true
	elif command -v flatpak &>/dev/null && flatpak info com.valvesoftware.Steam >/dev/null 2>&1; then
		setsid flatpak run com.valvesoftware.Steam "$encoded_url" >/dev/null 2>&1 || true
	fi

	if command -v notify-send &>/dev/null; then
		notify-send -i steam "Add to Steam" "$basename_file has been added to Steam." -t 5000 || true
	fi
	return 0
}

show_error() {
	local message="$1"
	if command -v zenity &>/dev/null; then
		zenity --error --title="Error - Add to Steam" --text="$message" --width=400 2>/dev/null || true
	elif command -v notify-send &>/dev/null; then
		notify-send -i dialog-error "Error - Add to Steam" "$message" -t 5000 2>/dev/null || true
	fi
	echo "ERROR: $message" >&2
}

verify_steam_running() {
	if pgrep -x "steam" >/dev/null 2>&1 || \
	   pgrep -x "steamwebhelper" >/dev/null 2>&1 || \
	   pgrep -f "com.valvesoftware.Steam" >/dev/null 2>&1 || \
	   (command -v flatpak >/dev/null 2>&1 && flatpak ps --columns=app | grep -q "com.valvesoftware.Steam") || \
	   ps ax 2>/dev/null | grep -q 'ubuntu12_32/[s]team'; then
		return 0
	fi
	return 1
}

validate_file() {
	local file="$1"
	if [[ ! -e "$file" ]]; then
		show_error "File not found:\n$file"
		return 1
	fi
	local lower_file
	lower_file="${file,,}"
	if [[ "$lower_file" == *.exe ]]; then
		return 0
	fi
	local mime
	mime=$(xdg-mime query filetype "$file" 2>/dev/null)
	case "$mime" in
		"application/x-desktop"|"application/x-ms-dos-executable"|\
		"application/vnd.microsoft.portable-executable"|"application/x-msdownload"|\
		"application/x-dosexec"|"application/x-msdos-program"|"application/x-winexe")
			return 0
			;;
		"application/x-executable"|"application/vnd.appimage"|"application/x-iso9660-appimage"|\
		"application/x-appimage"|"application/x-shellscript"|"text/x-shellscript"|\
		"text/x-python")
			if [[ -x "$file" ]]; then
				return 0
			else
				show_error "File is not executable.\nMake it executable first: chmod +x \"$(basename "$file")\""
				return 1
			fi
			;;
		*)
			show_error "Unsupported file type: $mime"
			return 1
			;;
	esac
}

main() {
	if [[ $# -eq 0 ]]; then
		show_error "Usage: add-to-steam.sh <file1> [file2] [...]"
		exit 1
	fi
	if ! verify_steam_running; then
		show_error "Steam must be running.\nPlease start Steam first."
		exit 1
	fi
	local success_count=0
	local fail_count=0
	local total=$#
	for file in "$@"; do
		if validate_file "$file"; then
			if add_to_steam "$file"; then
				success_count=$((success_count + 1))
			else
				show_error "Error adding $(basename "$file") to Steam."
				fail_count=$((fail_count + 1))
			fi
		else
			fail_count=$((fail_count + 1))
		fi
	done
	if [[ $total -gt 1 ]]; then
			local summary="Processed: $total\nSuccessful: $success_count\nFailed: $fail_count"
			if [[ $fail_count -eq 0 ]]; then
				if command -v notify-send &>/dev/null; then
					notify-send -i steam "Add to Steam - Summary" "$summary" -t 7000 || true
				fi
			else
				show_error "$summary"
			fi
	fi
	[[ $fail_count -eq 0 ]] && exit 0 || exit 1
}

main "$@"
