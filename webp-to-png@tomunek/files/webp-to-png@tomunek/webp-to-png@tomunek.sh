#!/bin/bash
ffmpeg -i "$1" "${1%.webp}".png