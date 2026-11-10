#!/bin/bash

# EN (default)
declare -A TRANSLATIONS_EN
TRANSLATIONS_EN["file_not_selected"]="No file selected. Exiting."
TRANSLATIONS_EN["date_not_selected"]="No date selected. Exiting."
TRANSLATIONS_EN["no_time_selected"]="No time selected. Exiting."
TRANSLATIONS_EN["modification_complete"]="Modification complete!"
TRANSLATIONS_EN["enable_backup"]="Enable file backup"
TRANSLATIONS_EN["enable_debug"]="Enable debug (log file)"
TRANSLATIONS_EN["yes"]="Yes"
TRANSLATIONS_EN["no"]="No"
TRANSLATIONS_EN["cancel"]="Cancel"
TRANSLATIONS_EN["select_options"]="Select options:"
TRANSLATIONS_EN["select_date"]="Select the date"
TRANSLATIONS_EN["select_time"]="Select the time"

# DE
declare -A TRANSLATIONS_DE
TRANSLATIONS_DE["file_not_selected"]="Keine Datei ausgewählt. Beende."
TRANSLATIONS_DE["date_not_selected"]="Kein Datum ausgewählt. Beende."
TRANSLATIONS_DE["no_time_selected"]="Keine Zeit ausgewählt. Beende."
TRANSLATIONS_DE["modification_complete"]="Änderung abgeschlossen!"
TRANSLATIONS_DE["enable_backup"]="Dateisicherung aktivieren"
TRANSLATIONS_DE["enable_debug"]="Debug aktivieren (Protokolldatei)"
TRANSLATIONS_DE["yes"]="Ja"
TRANSLATIONS_DE["no"]="Nein"
TRANSLATIONS_DE["cancel"]="Abbrechen"
TRANSLATIONS_DE["select_options"]="Optionen auswählen:"
TRANSLATIONS_DE["select_date"]="Wähle das Datum"
TRANSLATIONS_DE["select_time"]="Wähle die Uhrzeit"

# IT
declare -A TRANSLATIONS_IT
TRANSLATIONS_IT["file_not_selected"]="Nessun file selezionato. Uscita."
TRANSLATIONS_IT["date_not_selected"]="Nessuna data selezionata. Uscita."
TRANSLATIONS_IT["no_time_selected"]="Nessun orario selezionato. Uscita."
TRANSLATIONS_IT["modification_complete"]="Modifica completata!"
TRANSLATIONS_IT["enable_backup"]="Abilita backup dei file"
TRANSLATIONS_IT["enable_debug"]="Abilita debug (file di log)"
TRANSLATIONS_IT["yes"]="Sì"
TRANSLATIONS_IT["no"]="No"
TRANSLATIONS_IT["cancel"]="Annulla"
TRANSLATIONS_IT["select_options"]="Seleziona le opzioni:"
TRANSLATIONS_IT["select_date"]="Seleziona la data"
TRANSLATIONS_IT["select_time"]="Seleziona l'orario"

declare -A TRANSLATIONS

# Function to load translations in the correct language
load_translations() {
    lang=${LANG:0:2}

    case "$lang" in
        de) TRANSLATIONS=("${TRANSLATIONS_DE[@]}") ;;
        it) TRANSLATIONS=("${TRANSLATIONS_IT[@]}") ;;
        *)  TRANSLATIONS=("${TRANSLATIONS_EN[@]}") ;;
    esac

    # Set the keys correctly
    for key in "${!TRANSLATIONS_EN[@]}"; do
        case "$lang" in
            de) TRANSLATIONS[$key]="${TRANSLATIONS_DE[$key]}" ;;
            it) TRANSLATIONS[$key]="${TRANSLATIONS_IT[$key]}" ;;
            *)  TRANSLATIONS[$key]="${TRANSLATIONS_EN[$key]}" ;;
        esac
    done
}
