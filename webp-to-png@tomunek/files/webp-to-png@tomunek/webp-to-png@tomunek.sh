#!/bin/bash
if [[ $1 == *.webp ]]; then
    ffmpeg -i "$1" "${1%.webp}".png
elif [[ $1 == *.webm ]]; then
    ffmpeg -i "$1" "${1%.webm}".mp4
fi