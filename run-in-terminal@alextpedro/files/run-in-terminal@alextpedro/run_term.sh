#!/bin/bash

DIR="$( cd "$( dirname "$1" )" && pwd )"
TRM=$(gsettings get org.cinnamon.desktop.default-applications.terminal exec | tr -d \')

exec $TRM -- $SHELL -c "cd $DIR; $1; exec $SHELL"
