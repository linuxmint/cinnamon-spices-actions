#!/bin/bash

#Petición de datos:
if ! FORM_INPUT=$(zenity --forms --title="Check hash of selected file" --text="Fichero:\n<u><span color='blue' font='8'>$1</span></u>\n\nEnter the hash to check:" \
    --add-entry="MD5:" \
    --add-entry="SHA1:" \
    --add-entry="SHA256:" \
    --add-entry="SHA512:" \
    --width=500 --height=280 --separator="|" 2>/dev/null); then exit 0 ; fi


if (($(echo "$FORM_INPUT" | tr -cd '|' | wc -c) == 3)) && ! (echo "$FORM_INPUT" | grep -q '[\`;&$\\]'); then
    IFS='|' read -r -a HASHES_VALUES <<< "$FORM_INPUT" #Crea el array con los datos
    HASH_NAMES=("MD5" "SHA1" "SHA256" "SHA512")
else exit 1; fi

CONT=0
HASH_TYPE=""
USER_HASH=""

for i in "${!HASHES_VALUES[@]}"; do
    if [ -n "${HASHES_VALUES[$i]}" ]; then
        CONT=$((CONT + 1))
        HASH_TYPE="${HASH_NAMES[$i]}"
        USER_HASH="${HASHES_VALUES[$i]}"
    fi
done



# Verifica número de entradas y validación de valores hexadecimales.
if [ "$CONT" -ne 1 ] || ! echo "$USER_HASH" | grep -Eq '^[0-9a-fA-F]+$'; then
    zenity --error --title="Error in the information provided" --text="One of the following problems has occurred:\n🔸 No hash entered\n🔸 Multiple hashes entered at once\n🔸 Hash entered with invalid characters\n\nPlease check that you fill one (and only one) of the text boxes and that it is a valid (hexadecimal) hash."
    exit 1
else
    USER_HASH=$(echo "$USER_HASH" | tr '[:upper:]' '[:lower:]')
fi



# Calcula el hash del archivo según el tipo seleccionado por el usuario.
case "$HASH_TYPE" in
    "MD5")
    CALCULATED_HASH=$(md5sum "$1" | awk '{print $1}')
    ;;"SHA1")
    CALCULATED_HASH=$(sha1sum "$1" | awk '{print $1}')
    ;;"SHA256")
    CALCULATED_HASH=$(sha256sum "$1" | awk '{print $1}')
    ;;"SHA512")
    CALCULATED_HASH=$(sha512sum "$1" | awk '{print $1}')
;;esac
CALCULATED_HASH=$(echo "$CALCULATED_HASH" | tr '[:upper:'] '[:lower:]')


#Compara y muestra los resultados:
if [ "$USER_HASH" = "$CALCULATED_HASH" ]; then
    zenity --info --title="🎉 Hashes match!" --text="<tt>Tipo: <b>$HASH_TYPE</b>\n\n<span color='green'>$USER_HASH</span> (entered)\n<span color='green'>$CALCULATED_HASH</span> (calculated)</tt>"
else
    zenity --error --title="❌ Hashes do NOT match!" --text="<tt>Tipo: $HASH_TYPE\n\n<span color='red'>$USER_HASH</span> (entered)\n<span color='red'>$CALCULATED_HASH</span> (calculated)</tt>"
fi

exit 0
