#!/bin/bash

# Переходимо у необхідну директорію
cd "$1"

if [[ $2 == .* ]]
then
    exit 1 # Файл починається із символу '.'
elif grep "^$2$" .hidden
then
    exit 0 # Файл прихований
else 
    exit 1 # Файл видимий
fi
