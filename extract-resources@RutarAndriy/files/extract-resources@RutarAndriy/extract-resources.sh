#!/bin/bash

# Задаємо необхідні глобальні змінні
TEXTDOMAINDIR=$HOME/.local/share/locale/
TEXTDOMAIN=extract-resources@RutarAndriy

_TITLE=$"Extracting resources"
TITLE="$(/usr/bin/gettext "$_TITLE")"
_MESSAGE=$"Resources successfully extracted to $2_res/ folder"
MESSAGE="$(/usr/bin/gettext "$_MESSAGE")"

# Створюємо нову директорію
mkdir "$1/$2_res"

# Видобуваємо зображення
wrestool -x --output="$1/$2_res" --raw --type=3 "$1/$2"

# Видобуваємо курсори
wrestool -x --output="$1/$2_res" --type=12 "$1/$2"

# Видобуваємо іконки
wrestool -x --output="$1/$2_res" --type=14 "$1/$2"

# Відображаємо інформаційне повідомлення
notify-send "$TITLE" "$MESSAGE"
