#!/bin/bash
#x-terminal-emulator
DIR="$( cd "$( dirname "$1" )" && pwd )"
gnome-terminal -- bash -c "cd $DIR; $1; exec bash"

