#!/bin/bash

vscodeInstalled=true
vsCodeInsiderInstalled=true
vsCodiumInstalled=true
vsCodiumInsidersInstalled=true
sublimeTextInstalled=true

installedNum=0
installedIDEs=()

CURRENT_DIR=$1

###############################
# Check if vs code, code-insiders and codium are installed
if ! command -v code &> /dev/null ; then vscodeInstalled=false;
else
    installedNum=$((installedNum+1));
    installedIDEs+=("Visual Studio Code");
fi

if ! command -v code-insiders &> /dev/null ; then vsCodeInsiderInstalled=false;
else
    installedNum=$((installedNum+1));
    installedIDEs+=("Visual Studio Code Insiders");
fi

if ! command -v codium &> /dev/null ; then vsCodiumInstalled=false;
else
    installedNum=$((installedNum+1));
    installedIDEs+=("VSCodium");
fi

if ! command -v codium-insiders &> /dev/null ; then vsCodiumInsidersInstalled=false;
else
    installedNum=$((installedNum+1));
    installedIDEs+=("VSCodium Insiders");
fi

if ! command -v subl &> /dev/null ; then sublimeTextInstalled=false;
else
    installedNum=$((installedNum+1));
    installedIDEs+=("Sublime Text");
fi

#########################################
# Check if more than one app is installed
check_more_than_one() {
    if [ "$installedNum" -gt 1 ] ; then
        echo "More than one IDE installed!";
        echo "Wich one to launch?"
        echo
        for (( i=0; i<${#installedIDEs[@]}; i++ )) ; do
            echo "[$((i+1))] ${installedIDEs[$i]}"
        done
        echo
        echo "Enter value: "
    
        # Ask the user input of wich one to launch
        read IDE
        IDE=$(($IDE-1))

        # Launch the IDE
        for (( i=0; i<${#installedIDEs[@]}; i++ )) ; do
            if [ "$IDE" -eq "$i" ] ; then
                echo; echo "Launching ${installedIDEs[$i]}...";
                
                if [ "${installedIDEs[$i]}" == "Visual Studio Code" ] ; then code "${CURRENT_DIR}"; exit 0;
                elif [ "${installedIDEs[$i]}" == "Visual Studio Code Insiders" ] ; then code-insiders "${CURRENT_DIR}"; exit 0;
                elif [ "${installedIDEs[$i]}" == "VSCodium" ] ; then codium "${CURRENT_DIR}"; exit 0;
                elif [ "${installedIDEs[$i]}" == "VSCodium Insiders" ] ; then codium-insiders "${CURRENT_DIR}"; exit 0;
                elif [ "${installedIDEs[$i]}" == "Sublime Text" ] ; then subl "${CURRENT_DIR}"; sublime_launched;
                else echo;echo "Error: Value not valid, retry";echo;echo "=============================="; check_more_than_one; fi
            fi
        done

        check_more_than_one
    else
        # Launch the installed one
        if $vscodeInstalled ; then code "${CURRENT_DIR}";
        elif $vsCodeInsiderInstalled ; then code-insiders "${CURRENT_DIR}";
        elif $vsCodiumInstalled ; then codium "${CURRENT_DIR}";
        elif $vsCodiumInsidersInstalled ; then codium-insiders "${CURRENT_DIR}";
        elif $sublimeTextInstalled ; then subl "${CURRENT_DIR}";
        else echo;echo "Error: Value not valid, retry";echo;echo "=============================="; check_more_than_one; fi
    fi
}

sublime_launched() {
    echo;echo;echo;
    echo "==================================================================================";
    echo "Sublime Text launched. This window will stay open to prevent the IDE from closing.";
    echo "This window will close automatically when Sublime Text is closed.";
    echo "==================================================================================";

    # Loop until Sublime is closed
    while [ -n "$(pgrep -f sublime_text)" ] ; do sleep 1 ; done
    exit 0;
}

check_more_than_one

exit 0