#!/bin/bash

# author: schorschii

overwrite=NO
if zenity --question --text="Do you want to overwrite the original file(s)?"; then
	overwrite=YES
fi

for file in "$@"; do

	filePath="file://$file"

	ffmpeg -i "$filePath" -acodec pcm_s16le -vcodec copy "$filePath.converted.mov" \
		| zenity --progress --text "Please wait...\n$filePath" --auto-close --pulsate --auto-kill --no-cancel

	if [ "$overwrite" == "YES" ]; then
		rm "$file"
		mv "$file.converted.mov" "$file"
	fi

done
