#!/bin/bash
# ============================================================================
# Add to Steam - Script para Cinnamon/Nemo
# Basado en steamos-add-to-steam adaptado para Cinnamon
# Versión: 2.0
# ============================================================================
# Este script permite añadir juegos que no son de Steam a tu biblioteca de Steam
# desde el menú contextual de Nemo (gestor de archivos de Cinnamon)
# ============================================================================

set -euo pipefail

# ============================================================================
# FUNCIONES
# ============================================================================

add_to_steam() {
    local file="$1"
    local basename_file
    basename_file=$(basename "$file")
    
    # URL encoding usando Python (igual que el original de KDE)
    local encoded_url
    encoded_url="steam://addnonsteamgame/$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$file''', safe=''))")"
    
    # Crear archivo temporal (igual que el original)
    touch /tmp/addnonsteamgamefile 2>/dev/null || true
    
    # Abrir en Steam
    # Intentos en orden: cliente 'steam' en PATH, Steam Flatpak, xdg-open como fallback.
    if command -v steam &>/dev/null; then
        setsid steam "$encoded_url" >/dev/null 2>&1 || true
    elif command -v flatpak &>/dev/null && flatpak info com.valvesoftware.Steam >/dev/null 2>&1; then
        # Llamar flatpak run; algunos sistemas permiten pasar la URL directamente
        setsid flatpak run --branch=stable --arch=x86_64 com.valvesoftware.Steam "$encoded_url" >/dev/null 2>&1 || \
            setsid flatpak run com.valvesoftware.Steam "$encoded_url" >/dev/null 2>&1 || true
    else
        xdg-open "$encoded_url" >/dev/null 2>&1 || true
    fi

    # Notificación estilo Cinnamon (equivalente a kdialog --passivepopup)
    if command -v notify-send &>/dev/null; then
        notify-send -i steam "Add to Steam" "$basename_file ha sido añadido a Steam." -t 5000
    fi

    return 0
}

show_error() {
    local message="$1"
    
    # Intentar zenity primero (diálogo modal como kdialog --error)
    if command -v zenity &>/dev/null; then
        zenity --error --title="Error - Add to Steam" --text="$message" --width=400 2>/dev/null
    # Fallback a notify-send (notificación pasiva)
    elif command -v notify-send &>/dev/null; then
        notify-send -i dialog-error "Error - Add to Steam" "$message" -t 5000 2>/dev/null
    fi
    
    # Siempre imprimir a stderr
    echo "ERROR: $message" >&2
}

verify_steam_running() {
    # Verificar Steam en múltiples formatos:
    # - Proceso normal: steam, steamwebhelper
    # - Flatpak: com.valvesoftware.Steam
    # - Legacy SteamOS: ubuntu12_32/steam (como el original)
    if pgrep -x "steam" >/dev/null 2>&1 || \
       pgrep -x "steamwebhelper" >/dev/null 2>&1 || \
       pgrep -f "com.valvesoftware.Steam" >/dev/null 2>&1 || \
       # flatpak ps lists running flatpak apps
       (command -v flatpak >/dev/null 2>&1 && flatpak ps --columns=app | grep -q "com.valvesoftware.Steam") || \
       ps ax 2>/dev/null | grep -q 'ubuntu12_32/[s]team'; then
        return 0
    fi
    return 1
}

validate_file() {
    local file="$1"
    
    # Verificar que el archivo existe
    if [[ ! -e "$file" ]]; then
        show_error "Archivo no encontrado:\n$file"
        return 1
    fi
    
    # Obtener tipo MIME (igual que el original)
    local mime
    mime=$(xdg-mime query filetype "$file" 2>/dev/null)
    
    # Verificar tipo de archivo (mismos tipos MIME que el original de KDE)
    case "$mime" in
        # Archivos .desktop y ejecutables Windows
        "application/x-desktop"|"application/x-ms-dos-executable"|\
        "application/vnd.microsoft.portable-executable"|"application/x-msdownload")
            return 0
            ;;
        # Ejecutables Linux, AppImages y scripts
        "application/x-executable"|"application/vnd.appimage"|"application/x-shellscript")
            # Verificar que es ejecutable (igual que el original)
            if [[ -x "$file" ]]; then
                return 0
            else
                show_error "No se puede añadir el juego a Steam.\n\nEl archivo no es ejecutable.\n\nHazlo ejecutable primero:\nchmod +x \"$(basename "$file")\""
                return 1
            fi
            ;;
        # Tipo no soportado
        *)
            show_error "Tipo de archivo no soportado: $mime\n\nTipos soportados:\n• Archivos .desktop\n• Ejecutables de Linux (.bin, .sh)\n• AppImages\n• Ejecutables de Windows (.exe)"
            return 1
            ;;
    esac
}

# ============================================================================
# SCRIPT PRINCIPAL
# ============================================================================

main() {
    # Verificar que se proporcionaron argumentos
    if [[ $# -eq 0 ]]; then
        show_error "Uso: add-to-steam.sh <archivo1> [archivo2] [...]"
        exit 1
    fi
    
    # Verificar que Steam está en ejecución (igual que el original)
    if ! verify_steam_running; then
        show_error "Steam debe estar en ejecución.\n\nPor favor, inicia Steam primero."
        exit 1
    fi
    
    # Procesar cada archivo (mejora sobre el original: soporte múltiples archivos)
    local success_count=0
    local fail_count=0
    local total=$#
    
    for file in "$@"; do
        if validate_file "$file"; then
            if add_to_steam "$file"; then
                ((success_count++))
            else
                show_error "Error al añadir $(basename "$file") a Steam."
                ((fail_count++))
            fi
        else
            ((fail_count++))
        fi
    done
    
    # Mostrar resumen si se procesaron múltiples archivos
    if [[ $total -gt 1 ]]; then
        local summary="Procesados: $total\nExitosos: $success_count\nFallidos: $fail_count"
        
        if [[ $fail_count -eq 0 ]]; then
            if command -v notify-send &>/dev/null; then
                notify-send -i steam "Add to Steam - Resumen" "$summary" -t 7000
            fi
        else
            show_error "$summary"
        fi
    fi
    
    # Exit code: 0 si todos exitosos, 1 si alguno falló
    [[ $fail_count -eq 0 ]] && exit 0 || exit 1
}

# Ejecutar función principal
main "$@"
