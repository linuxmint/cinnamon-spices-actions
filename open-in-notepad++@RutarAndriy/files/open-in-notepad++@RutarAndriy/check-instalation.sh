#!/bin/bash

# Перевірка наявності піктограми notepad++
# Якщо піктограми не існує - створюємо її
if [[ ! -f ~/.local/share/icons/hicolor/16x16/apps/notepad++.png ]]
then
    # Отримуємо шлях до виконуваного файлу
    dir="$(dirname $0)"
    # Переходимо у необхідну директорію
    cd "$dir""/icons/"
    # Додаємо піктограми різних розмірів
    for size in 16 32 48 64 128 256; do
        xdg-icon-resource install --novendor --size $size $size"x"$size.png notepad++
    done
fi

# Перевірка наявності інстальованого Notepad++
if [[ -f ~/.wine/drive_c/Program\ Files/Notepad++/notepad++.exe ]]
then
    # Інстальовано 64-бітну версію програми
    exit 0
elif [[ -f ~/.wine/drive_c/Program\ Files\ \(x86\)/Notepad++/notepad++.exe ]]
then
    # Інстальовано 32-бітну версію програми
    exit 0
else
    # Програму не інстальовано
    exit 1    
fi

