#!/bin/bash

# Інстальовано 64-бітну версію програми
if [[ -f ~/.wine/drive_c/Program\ Files/Notepad++/notepad++.exe ]]
then   
    wine ~/.wine/drive_c/Program\ Files/Notepad++/notepad++.exe "$1"

# Інстальовано 32-бітну версію програми
else
    wine ~/.wine/drive_c/Program\ Files\ \(x86\)/Notepad++/notepad++.exe "$1"
   
fi
