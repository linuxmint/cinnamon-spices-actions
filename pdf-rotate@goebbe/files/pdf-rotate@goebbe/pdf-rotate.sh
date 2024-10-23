#!/bin/bash
#
# turn-pdf.sh
#
# Rotate the selected pdf-file(s) 90 degrees clockwise from the right-click context menu in Nemo file manager.
#
# Place this action in ~/.local/share/nemo/actions/...
# This file has to be executable, check the permisions.
# Restart Nemo once.
# INSTALL qpdf first: 
# sudo apt install qpdf
# 
# Usage: select pdf-files, right click, Rotate PDF(s)

echo "$@" | while read -r file
  do
    qpdf "$file" --replace-input --rotate=+90    
done

exit 0

