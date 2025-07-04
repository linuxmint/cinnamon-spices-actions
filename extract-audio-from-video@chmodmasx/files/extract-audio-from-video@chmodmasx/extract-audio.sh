#!/bin/bash

# Extract Audio from Video - Cinnamon Action
# Author: chmodmasx
# Description: Extract original audio track from video files without conversion

# Get the input file
INPUT_FILE="$1"

# Check if input file exists
if [[ ! -f "$INPUT_FILE" ]]; then
    zenity --error --title="Error" --text="File not found: $INPUT_FILE"
    exit 1
fi

# Internationalization support
if [[ "$LANG" == es* ]]; then
    TITLE="Extraer Audio del Video"
    PROMPT="Selecciona el formato de audio a extraer:"
    COLUMN_1="Seleccionar"
    COLUMN_2="Formato"
    COLUMN_3="Descripción"
    ERROR_TITLE="Error"
    ERROR_NO_SELECTION="No se seleccionó ningún formato"
    ERROR_EXTRACTION="Error durante la extracción"
    SUCCESS_TITLE="Éxito"
    SUCCESS_MESSAGE="Audio extraído exitosamente"
    PROGRESS_TITLE="Extrayendo audio..."
    PROGRESS_TEXT="Procesando archivo:"
    CONFIRM_TITLE="Confirmar"
    CONFIRM_MESSAGE="ya existe. ¿Desea sobrescribirlo?"
    DETECTING_MESSAGE="Detectando formato de audio..."
    FLAC_TITLE="Calidad FLAC"
    FLAC_PROMPT="Selecciona el nivel de compresión FLAC:"
    CANCELLED_TITLE="Cancelado"
    CANCELLED_MESSAGE="Operación cancelada por el usuario"
else
    TITLE="Extract Audio from Video"
    PROMPT="Select the audio format to extract:"
    COLUMN_1="Select"
    COLUMN_2="Format"
    COLUMN_3="Description"
    ERROR_TITLE="Error"
    ERROR_NO_SELECTION="No format selected"
    ERROR_EXTRACTION="Error during extraction"
    SUCCESS_TITLE="Success"
    SUCCESS_MESSAGE="Audio extracted successfully"
    PROGRESS_TITLE="Extracting audio..."
    PROGRESS_TEXT="Processing file:"
    CONFIRM_TITLE="Confirm"
    CONFIRM_MESSAGE="already exists. Do you want to overwrite it?"
    DETECTING_MESSAGE="Detecting audio format..."
    FLAC_TITLE="FLAC Quality"
    FLAC_PROMPT="Select FLAC compression level:"
    CANCELLED_TITLE="Cancelled"
    CANCELLED_MESSAGE="Operation cancelled by user"
fi

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    # Try to open software center with apturl (like color-picker@fmete does)
    if command -v apturl &> /dev/null; then
        apturl apt://ffmpeg
    fi
    exit 1
fi

# Get file information
INPUT_DIR=$(dirname "$INPUT_FILE")
INPUT_BASENAME=$(basename "$INPUT_FILE")
INPUT_NAME="${INPUT_BASENAME%.*}"

# Function to get audio codec from video file
get_audio_codec() {
    ffprobe -v quiet -select_streams a:0 -show_entries stream=codec_name -of csv=p=0 "$INPUT_FILE" 2>/dev/null
}

# Function to get appropriate file extension for audio codec
get_audio_extension() {
    local codec="$1"
    case "$codec" in
        "aac") echo "aac" ;;
        "mp3") echo "mp3" ;;
        "flac") echo "flac" ;;
        "vorbis") echo "ogg" ;;
        "opus") echo "opus" ;;
        "pcm_s16le"|"pcm_s24le"|"pcm_s32le") echo "wav" ;;
        "ac3") echo "ac3" ;;
        "eac3") echo "eac3" ;;
        "dts") echo "dts" ;;
        "truehd") echo "thd" ;;
        "wmav1"|"wmav2") echo "wma" ;;
        "alac") echo "m4a" ;;
        *) echo "aac" ;; # Default fallback
    esac
}

# Show format selection dialog
FORMAT=$(zenity --list --radiolist \
    --title="$TITLE" \
    --text="$PROMPT" \
    --height=400 \
    --width=500 \
    --column="$COLUMN_1" --column="$COLUMN_2" --column="$COLUMN_3" \
    TRUE "original" "Original format (no conversion)" \
    FALSE "mp3" "MP3 - Most compatible, good compression" \
    FALSE "flac" "FLAC - Lossless compression, larger files" \
    FALSE "ogg" "OGG - Open source, good compression" \
    FALSE "wav" "WAV - Uncompressed, largest files" \
    FALSE "aac" "AAC - High quality, good compression" \
    FALSE "m4a" "M4A - Apple format, good quality" \
    FALSE "opus" "OPUS - Modern codec, excellent compression")

# Check if user selected a format
if [[ -z "$FORMAT" ]]; then
    zenity --error --title="$ERROR_TITLE" --text="$ERROR_NO_SELECTION"
    exit 1
fi

# Handle original format extraction
if [[ "$FORMAT" == "original" ]]; then
    # Detect audio codec for original format
    AUDIO_CODEC=$(get_audio_codec)
    if [[ -z "$AUDIO_CODEC" ]]; then
        zenity --error --title="$ERROR_TITLE" --text="No audio track found in the video file"
        exit 1
    fi
    
    # Get appropriate extension for original codec
    FORMAT=$(get_audio_extension "$AUDIO_CODEC")
    USE_COPY_CODEC=true
else
    USE_COPY_CODEC=false
fi

# Handle FLAC quality selection
if [[ "$FORMAT" == "flac" ]]; then
    FLAC_QUALITY=$(zenity --list --radiolist \
        --title="$FLAC_TITLE" \
        --text="$FLAC_PROMPT" \
        --height=400 \
        --width=600 \
        --column="$COLUMN_1" --column="$COLUMN_2" --column="$COLUMN_3" \
        FALSE "0" "Fastest compression, largest files" \
        FALSE "1" "Fast compression" \
        FALSE "2" "Good speed/size balance" \
        FALSE "3" "Balanced compression" \
        FALSE "4" "Good compression" \
        TRUE "5" "Default - Good compression/speed balance" \
        FALSE "6" "Better compression" \
        FALSE "7" "High compression" \
        FALSE "8" "Best compression, smallest files (slowest)")
    
    # Check if user selected a quality level
    if [[ -z "$FLAC_QUALITY" ]]; then
        zenity --error --title="$ERROR_TITLE" --text="$ERROR_NO_SELECTION"
        exit 1
    fi
    
    USE_FLAC_QUALITY=true
else
    USE_FLAC_QUALITY=false
fi

# Set output filename
OUTPUT_FILE="$INPUT_DIR/${INPUT_NAME}.$FORMAT"

# Check if output file already exists
if [[ -f "$OUTPUT_FILE" ]]; then
    if ! zenity --question --title="$CONFIRM_TITLE" --text="${INPUT_NAME}.$FORMAT $CONFIRM_MESSAGE"; then
        exit 0
    fi
fi

# Set ffmpeg parameters based on format
if [[ "$USE_COPY_CODEC" == "true" ]]; then
    FFMPEG_PARAMS="-vn -acodec copy"
else
    case "$FORMAT" in
        "mp3")
            FFMPEG_PARAMS="-vn -acodec libmp3lame -ab 192k"
            ;;
        "flac")
            if [[ "$USE_FLAC_QUALITY" == "true" ]]; then
                FFMPEG_PARAMS="-vn -acodec flac -compression_level $FLAC_QUALITY"
            else
                FFMPEG_PARAMS="-vn -acodec flac"
            fi
            ;;
        "ogg")
            FFMPEG_PARAMS="-vn -acodec libvorbis -ab 192k"
            ;;
        "wav")
            FFMPEG_PARAMS="-vn -acodec pcm_s16le"
            ;;
        "aac")
            FFMPEG_PARAMS="-vn -acodec aac -ab 192k"
            ;;
        "m4a")
            FFMPEG_PARAMS="-vn -acodec aac -ab 192k"
            ;;
        "opus")
            FFMPEG_PARAMS="-vn -acodec libopus -ab 128k"
            ;;
        *)
            zenity --error --title="$ERROR_TITLE" --text="Unsupported format: $FORMAT"
            exit 1
            ;;
    esac
fi

# Function to extract audio
extract_audio() {
    # Get total duration of the video
    TOTAL_DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$INPUT_FILE" 2>/dev/null)
    
    # Create unique temporary files for this process
    PROCESS_ID="$$_$(date +%s)_$(shuf -i 1000-9999 -n 1)"
    PID_FILE="/tmp/extract_audio_${PROCESS_ID}.pid"
    CANCEL_FILE="/tmp/extract_audio_cancel_${PROCESS_ID}.flag"
    
    # Function to cleanup on exit
    cleanup() {
        # Signal that we're cleaning up
        touch "$CANCEL_FILE"
        
        # Kill ffmpeg if it's still running
        if [[ -f "$PID_FILE" ]]; then
            FFMPEG_PID=$(cat "$PID_FILE" 2>/dev/null)
            if [[ -n "$FFMPEG_PID" ]] && kill -0 "$FFMPEG_PID" 2>/dev/null; then
                # Send SIGTERM first
                kill -TERM "$FFMPEG_PID" 2>/dev/null
                # Give it 2 seconds to terminate gracefully
                sleep 2
                # Force kill if still running
                if kill -0 "$FFMPEG_PID" 2>/dev/null; then
                    kill -KILL "$FFMPEG_PID" 2>/dev/null
                fi
            fi
            rm -f "$PID_FILE"
        fi
        
        # Clean up partial output file if it exists and is likely incomplete
        if [[ -f "$OUTPUT_FILE" ]]; then
            FILE_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
            # Remove file if it's very small (likely incomplete)
            if [[ "$FILE_SIZE" -lt 1024 ]]; then
                rm -f "$OUTPUT_FILE"
            fi
        fi
        
        # Clean up temporary files
        rm -f "$CANCEL_FILE"
    }
    
    # Set trap to cleanup on script termination
    trap cleanup EXIT INT TERM
    
    # Progress indicator
    (
        echo "5"
        echo "# $DETECTING_MESSAGE"
        
        echo "10"
        echo "# Starting extraction..."
        
        # Start ffmpeg in background and capture its PID
        ffmpeg -i "$INPUT_FILE" $FFMPEG_PARAMS -y "$OUTPUT_FILE" -progress pipe:1 2>/dev/null &
        FFMPEG_PID=$!
        echo "$FFMPEG_PID" > "$PID_FILE"
        
        # Monitor ffmpeg process for cancellation
        (
            while kill -0 "$FFMPEG_PID" 2>/dev/null; do
                if [[ -f "$CANCEL_FILE" ]]; then
                    kill -TERM "$FFMPEG_PID" 2>/dev/null
                    sleep 1
                    if kill -0 "$FFMPEG_PID" 2>/dev/null; then
                        kill -KILL "$FFMPEG_PID" 2>/dev/null
                    fi
                    break
                fi
                sleep 0.2
            done
        ) &
        MONITOR_PID=$!
        
        # Monitor ffmpeg output for progress
        while kill -0 "$FFMPEG_PID" 2>/dev/null && [[ ! -f "$CANCEL_FILE" ]]; do
            if read -t 1 line; then
                if [[ $line =~ ^out_time_ms=([0-9]+)$ ]]; then
                    # Convert microseconds to seconds
                    CURRENT_TIME_MS=${BASH_REMATCH[1]}
                    CURRENT_TIME=$((CURRENT_TIME_MS / 1000000))
                    
                    # Calculate percentage if we have total duration
                    if [[ -n "$TOTAL_DURATION" ]] && [[ "$TOTAL_DURATION" != "N/A" ]] && (( $(echo "$TOTAL_DURATION > 0" | awk '{print ($1 > 0)}') )); then
                        # Use awk for floating point arithmetic instead of bc
                        PERCENTAGE=$(echo "$CURRENT_TIME $TOTAL_DURATION" | awk '{printf "%.0f", ($1 * 85 / $2) + 10}')
                        # Ensure percentage is within bounds
                        if (( PERCENTAGE > 95 )); then
                            PERCENTAGE=95
                        fi
                        if (( PERCENTAGE < 10 )); then
                            PERCENTAGE=10
                        fi
                        echo "$PERCENTAGE"
                        if [[ "$USE_COPY_CODEC" == "true" ]]; then
                            echo "# Extracting audio... $(printf "%.1f" $CURRENT_TIME)s / $(printf "%.1f" $TOTAL_DURATION)s"
                        else
                            echo "# Converting audio... $(printf "%.1f" $CURRENT_TIME)s / $(printf "%.1f" $TOTAL_DURATION)s"
                        fi
                    else
                        # Fallback to pulsating progress if duration is unknown
                        PULSE_PROGRESS=$((35 + (RANDOM % 30)))
                        echo "$PULSE_PROGRESS"
                        if [[ "$USE_COPY_CODEC" == "true" ]]; then
                            echo "# Extracting audio..."
                        else
                            echo "# Converting audio..."
                        fi
                    fi
                fi
            fi
        done < <(ffmpeg -i "$INPUT_FILE" $FFMPEG_PARAMS -y "$OUTPUT_FILE" -progress pipe:1 2>/dev/null)
        
        # Kill monitor process
        kill "$MONITOR_PID" 2>/dev/null
        
        # Wait for ffmpeg to complete if not cancelled
        if [[ ! -f "$CANCEL_FILE" ]]; then
            wait "$FFMPEG_PID"
            FFMPEG_EXIT_CODE=$?
            
            # Check if process completed successfully
            if [[ $FFMPEG_EXIT_CODE -eq 0 ]]; then
                echo "98"
                echo "# Finishing..."
                sleep 0.5
                echo "100"
                echo "# Done!"
            else
                # ffmpeg failed
                exit 1
            fi
        else
            # Process was cancelled
            exit 1
        fi
        
        # Clean up PID file
        rm -f "$PID_FILE"
        
    ) | zenity --progress \
        --title="$PROGRESS_TITLE" \
        --text="$PROGRESS_TEXT $INPUT_BASENAME" \
        --percentage=0 \
        --auto-close
    
    # Store the exit code of the zenity progress dialog
    ZENITY_EXIT_CODE=$?
    
    # If zenity was cancelled (exit code 1), trigger cleanup
    if [[ $ZENITY_EXIT_CODE -eq 1 ]]; then
        cleanup
        return 1
    fi
    
    return 0
}

# Extract audio
if extract_audio; then
    # Check if output file was created successfully
    if [[ -f "$OUTPUT_FILE" ]]; then
        # Get file size to verify it's a complete file
        FILE_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
        if [[ "$FILE_SIZE" -gt 1024 ]]; then
            if [[ "$USE_COPY_CODEC" == "true" ]]; then
                zenity --info --title="$SUCCESS_TITLE" --text="$SUCCESS_MESSAGE\n\nOutput file: ${INPUT_NAME}.$FORMAT\nOriginal codec: $AUDIO_CODEC"
            elif [[ "$FORMAT" == "flac" && "$USE_FLAC_QUALITY" == "true" ]]; then
                zenity --info --title="$SUCCESS_TITLE" --text="$SUCCESS_MESSAGE\n\nOutput file: ${INPUT_NAME}.$FORMAT\nConverted to: FLAC (Quality Level $FLAC_QUALITY)"
            else
                zenity --info --title="$SUCCESS_TITLE" --text="$SUCCESS_MESSAGE\n\nOutput file: ${INPUT_NAME}.$FORMAT\nConverted to: $FORMAT"
            fi
        else
            zenity --error --title="$ERROR_TITLE" --text="$ERROR_EXTRACTION - Output file is incomplete"
            exit 1
        fi
    else
        zenity --error --title="$ERROR_TITLE" --text="$ERROR_EXTRACTION - Output file not created"
        exit 1
    fi
else
    # Check if operation was cancelled
    if [[ -f "$OUTPUT_FILE" ]]; then
        FILE_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
        if [[ "$FILE_SIZE" -lt 1024 ]]; then
            rm -f "$OUTPUT_FILE"
        fi
    fi
    zenity --info --title="$CANCELLED_TITLE" --text="$CANCELLED_MESSAGE"
    exit 0
fi
