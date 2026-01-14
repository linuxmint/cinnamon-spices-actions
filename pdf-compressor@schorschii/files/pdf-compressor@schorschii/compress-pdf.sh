#!/bin/bash

# author: schorschii

for file in "$@"; do

	# start ghostscript for PDF conversion
	gs -sDEVICE=pdfwrite \
	   -dCompatibilityLevel=1.4 \
	   -dPDFSETTINGS=/ebook \
	   -dNOPAUSE -dQUIET -dBATCH \
	   -sOutputFile="$file.compressed.pdf" \
	   "$file" \
	   | zenity --text "$file" \
	            --progress --auto-close --pulsate --auto-kill --no-cancel

done
