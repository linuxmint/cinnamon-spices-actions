#!/usr/bin/env bash

arr=()
SAVEIFS=$IFS
IFS=$(echo -en "\n\b")

for var in "$@"
do
    if [ -n "$var" ]; then
        path=$(readlink -f "$var")
        arr+=("$path")
    fi
done

# Archivo de configuración para guardar ruta personalizada
config_file="$HOME/.config/telegram_launcher.conf"

# Lista de posibles comandos para Telegram
telegram_candidates=(
    "telegram-desktop"
    "telegram"
    "Telegram"
    "$HOME/.local/bin/Telegram"
    "/opt/telegram/Telegram"
    "/usr/bin/telegram-desktop"
    "/usr/local/bin/Telegram"
)

telegram_cmd=""
is_flatpak=false

# Cargar ruta personalizada si existe
if [ -f "$config_file" ]; then
    saved_cmd=$(<"$config_file")
    if [ -x "$saved_cmd" ]; then
        telegram_cmd="$saved_cmd"
    fi
fi

# Buscar el ejecutable de Telegram si no se cargó desde config
if [ -z "$telegram_cmd" ]; then
    for cmd in "${telegram_candidates[@]}"; do
        if command -v "$cmd" >/dev/null 2>&1; then
            telegram_cmd="$cmd"
            break
        elif [[ -x "$cmd" ]]; then
            telegram_cmd="$cmd"
            break
        fi
    done
fi

# Si no encontró ninguno, probar con Flatpak (sólo si está instalado Telegram)
if [ -z "$telegram_cmd" ] && command -v flatpak >/dev/null; then
    if flatpak list --app | grep -q org.telegram.desktop; then
        telegram_cmd=(flatpak run --file-forwarding org.telegram.desktop)
        is_flatpak=true
    fi
fi

# Ejecutar el comando con los archivos
if [ -n "$telegram_cmd" ]; then
    if [ "$is_flatpak" = true ]; then
        "${telegram_cmd[@]}" -sendpath @@ "${arr[@]}" @@
        wmctrl -x -a Telegram
    else
        "$telegram_cmd" -sendpath "${arr[@]}"
        wmctrl -x -a Telegram.TelegramDesktop
    fi
else
    zenity --question \
        --title="Telegram no encontrado" \
        --text="No se encontró una instalación de Telegram compatible.\n¿Querés seleccionar el ejecutable manualmente?"

    if [ $? -eq 0 ]; then
        manual_path=$(zenity --file-selection --title="Seleccioná el ejecutable de Telegram")

        if [ -n "$manual_path" ] && [ -x "$manual_path" ]; then
            telegram_cmd="$manual_path"
            echo "$telegram_cmd" > "$config_file"
            "$telegram_cmd" -sendpath "${arr[@]}"
            wmctrl -x -a Telegram.TelegramDesktop
        else
            zenity --error --title="Error" --text="El archivo seleccionado no es un ejecutable válido."
            exit 1
        fi
    else
        zenity --error --title="Telegram no encontrado" --text="No se pudo ejecutar Telegram."
        exit 1
    fi
fi

IFS=$SAVEIFS

