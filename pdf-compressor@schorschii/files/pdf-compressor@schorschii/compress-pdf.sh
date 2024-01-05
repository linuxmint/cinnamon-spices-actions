#!/bin/bash

# author: schorschii

for var in "$@"; do

	# remove "file://" from url
	fileUrl=${var//file:\/\//}

	# decode urlencoded path
	filePathUncoded=$(python3 -c "import sys; from urllib.parse import unquote; print(unquote(sys.stdin.read()));" <<< "$fileUrl")

	# start ghostscript for PDF conversion
	gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH -sOutputFile="$filePathUncoded.compressed.pdf" "$filePathUncoded" | zenity --progress --text "Please wait...\n$filePathUncoded" --auto-close --pulsate --auto-kill --no-cancel

done
