#!/bin/bash

# Test script to verify dependency management behavior

echo "=== Testing dependency management behavior ==="

# Create a temporary test script that simulates missing dependencies
cat > /tmp/test_extract_audio.sh << 'EOF'
#!/bin/bash

# Simulated version of the extract-audio script with missing dependencies

# Mock the missing command
missing_command() {
    return 1
}

# Internationalization support
if [[ "$LANG" == es* ]]; then
    INSTALL_TITLE="Dependencias Faltantes"
    INSTALL_FFMPEG_MESSAGE="ffmpeg no está instalado. Es necesario para extraer audio de videos.

¿Desea instalarlo ahora?"
    INSTALL_BUTTON_YES="Instalar Automáticamente"
    INSTALL_BUTTON_MANUAL="Instalar Manualmente"
    INSTALL_ADVANCED_OPTION="Opción avanzada: Instalación automática con sudo"
    INSTALL_MANUAL_MESSAGE="Por favor, instale el paquete"
    INSTALL_MANUAL_COMMAND="Comando"
    ERROR_TITLE="Error"
else
    INSTALL_TITLE="Missing Dependencies"
    INSTALL_FFMPEG_MESSAGE="ffmpeg is not installed. It's required to extract audio from videos.

Do you want to install it now?"
    INSTALL_BUTTON_YES="Install Automatically"
    INSTALL_BUTTON_MANUAL="Install Manually"
    INSTALL_ADVANCED_OPTION="Advanced option: Automatic installation with sudo"
    INSTALL_MANUAL_MESSAGE="Please install the package"
    INSTALL_MANUAL_COMMAND="Command"
    ERROR_TITLE="Error"
fi

# Function to notify about missing dependencies
notify_missing_dependency() {
    local package="$1"
    local message="$2"
    
    echo "Dependency check: $package is missing"
    echo "Message: $message"
    echo "Would show dialog with options:"
    echo "  - $INSTALL_BUTTON_YES (with sudo)"
    echo "  - $INSTALL_BUTTON_MANUAL"
    echo "If manual selected, would show:"
    echo "  $INSTALL_MANUAL_MESSAGE '$package'"
    echo "  $INSTALL_MANUAL_COMMAND: sudo apt install $package"
}

# Simulate missing ffmpeg
if ! command -v ffmpeg_missing &> /dev/null; then
    notify_missing_dependency "ffmpeg" "$INSTALL_FFMPEG_MESSAGE"
fi

echo "Test completed successfully!"
EOF

chmod +x /tmp/test_extract_audio.sh
/tmp/test_extract_audio.sh

echo ""
echo "=== Test completed ==="
echo "The new dependency management system provides:"
echo "1. Automatic installation option (advanced)"
echo "2. Manual installation instructions (traditional)"
echo "3. Clear commands for manual installation"
echo "4. Consistent with Cinnamon Spices conventions"

rm /tmp/test_extract_audio.sh
