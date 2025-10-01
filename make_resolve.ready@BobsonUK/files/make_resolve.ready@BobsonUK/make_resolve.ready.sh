#!/usr/bin/env bash
set -eou pipefail

# Make resolve.ready
# Author: BobsonUK
#
# Automatically transcode video and audio files into
# formats that are optimized for DaVinci Resolve:
# - Video: DNxHR HQ codec with PCM 24-bit audio (stored in resolve.ready/video/)
# - Audio: PCM 24-bit audio (stored in resolve.ready/audio/)
#
# Files are marked with "resolve.ready" in their filename and organized into
# dedicated directories to ensure they remain identifiable even if moved.

#------------------------------------------------------------------------------
# Function Definitions
#------------------------------------------------------------------------------

# Display error message and exit
show_error() {
    zenity --error --text="$1"
    exit 1
}

# Display warning message
show_warning() {
    zenity --warning --text="$1"
}

# Display info message with desktop notification sound
show_info() {
    zenity --info --text="$1" &
}

# Check if file is already processed based on filename
is_already_processed() {
    local filename=$(basename "$1")
    if [[ "$filename" == *".resolve.ready."* ]]; then
        return 0  # True - already processed
    fi
    return 1  # False - not processed
}

# Create output directory if it doesn't exist
ensure_output_directory() {
    local output_dir="$1"

    if [ ! -d "$output_dir" ]; then
        mkdir -p "$output_dir"
        # Return error if directory creation failed
        if [ $? -ne 0 ]; then
            return 1
        fi
    fi
    return 0
}

# Check if output file already exists
output_exists() {
    local output_file="$1"

    if [ -f "$output_file" ]; then
        return 0  # True - output exists
    fi
    return 1  # False - output doesn't exist
}

# Get output file path for video
get_video_output_path() {
    local input_file="$1"
    local base_name=$(basename "$input_file")
    local dir_name=$(dirname "$input_file")
    local file_name="${base_name%.*}"

    # Create resolve.ready/video subdirectory
    local output_dir="${dir_name}/resolve.ready/video"

    # Return path to output file with resolve.ready in the filename
    echo "${output_dir}/${file_name}.resolve.ready.mov"
}

# Get output file path for audio
get_audio_output_path() {
    local input_file="$1"
    local base_name=$(basename "$input_file")
    local dir_name=$(dirname "$input_file")
    local file_name="${base_name%.*}"

    # Create resolve.ready/audio subdirectory
    local output_dir="${dir_name}/resolve.ready/audio"

    # Return path to output file with resolve.ready in the filename
    echo "${output_dir}/${file_name}.resolve.ready.wav"
}

# Process video file
process_video() {
    local input_file="$1"
    local output_file="$2"
    local video_codec="dnxhr_hq"
    local audio_codec="pcm_s24le"

    ffmpeg -i "$input_file" -c:v dnxhd -profile:v "$video_codec" -c:a "$audio_codec" -threads 0 \
        "$output_file" 2>/dev/null

    return $?  # Return ffmpeg exit code
}

# Process audio file
process_audio() {
    local input_file="$1"
    local output_file="$2"
    local audio_codec="pcm_s24le"

    ffmpeg -i "$input_file" -c:a "$audio_codec" -threads 0 \
        "$output_file" 2>/dev/null

    return $?  # Return ffmpeg exit code
}

# Update progress bar
update_progress() {
    local message="$1"
    local percentage="$2"

    echo "# $message" >&3
    echo "$percentage" >&3
}

# Get file type
get_file_type() {
    file -b --mime-type "$1" 2>/dev/null | cut -d'/' -f1 || \
    file -b -i "$1" 2>/dev/null | cut -d';' -f1 | cut -d'/' -f1
}

#------------------------------------------------------------------------------
# Main Script
#------------------------------------------------------------------------------

# Check for ffmpeg dependency
if ! command -v ffmpeg &> /dev/null; then
    show_error "ffmpeg is not installed. Please install it first."
fi

# Check if files were provided
if [ $# -eq 0 ]; then
    show_error "No files selected. Please select files to process."
fi

# Collect valid files for processing
total_files=0
valid_files=()
for file in "$@"; do
    if [ -f "$file" ]; then
        valid_files+=("$file")
        total_files=$((total_files + 1))
    else
        show_warning "Not a file: '$file' (length: ${#file}, type: $(file -b "$file" 2>/dev/null || echo "cannot determine"))"
    fi
done

# Exit if no valid files
if [ $total_files -eq 0 ]; then
    show_error "No valid files to process."
fi

# Set up progress dialog
rm -f /tmp/progress_pipe
if ! mkfifo /tmp/progress_pipe 2>/dev/null; then
    show_error "Failed to create progress pipe. Check permissions in /tmp or install 'mkfifo'."
fi

# Start zenity progress dialog
(
    zenity --progress \
        --title="Make resolve.ready" \
        --text="Transcoding starting..." \
        --percentage=0 \
        --width=700 \
        --auto-close \
        --no-cancel < /tmp/progress_pipe
) &
ZENITY_PID=$!

# Wait briefly for Zenity to start
sleep 0.5  # Adjust delay as needed

# Open pipe for writing
exec 3> /tmp/progress_pipe

# Process each file
current_file=0
for file in "${valid_files[@]}"; do
    current_file=$((current_file + 1))
    base_name=$(basename "$file")

    # Calculate progress percentage (keep at 99% for last file until complete)
    if [ $current_file -eq $total_files ]; then
        percentage=99
    else
        percentage=$(( (current_file - 1) * 100 / total_files ))
    fi

    # Update progress with current file
    #update_progress "Processing file $current_file of $total_files: $base_name" "$percentage"
    #sleep 0.5

    # Skip already processed files
    if is_already_processed "$file"; then
        update_progress "Skipping already processed file: - $base_name" "$(( current_file * 100 / total_files ))"
        sleep 0.5
        continue
    fi

    # Determine file type and process accordingly
    file_type=$(get_file_type "$file")

    if [[ "$file_type" == "video" ]]; then
        # Get output file path for video
        output_file=$(get_video_output_path "$file")
        output_dir=$(dirname "$output_file")

        # Ensure output directory exists
        if ! ensure_output_directory "$output_dir"; then
            show_warning "Error creating directory: - $output_dir" &
            continue
        fi

        # Skip if output exists
        if output_exists "$output_file"; then
            update_progress "Skipping output file already exists for: - $base_name" "$(( current_file * 100 / total_files ))"
            sleep 0.5
            continue
        fi

        # Process video file
        update_progress "Transcoding video file: - $base_name" "$percentage"

        if ! process_video "$file" "$output_file"; then
            show_warning "Error transcoding video file: - $base_name" &
        fi

    elif [[ "$file_type" == "audio" ]]; then
        # Get output file path for audio
        output_file=$(get_audio_output_path "$file")
        output_dir=$(dirname "$output_file")

        # Ensure output directory exists
        if ! ensure_output_directory "$output_dir"; then
            show_warning "Error creating directory: - $output_dir" &
            continue
        fi

        # Skip if output exists
        if output_exists "$output_file"; then
            update_progress "Skipping output file already exists for: - $base_name" "$(( current_file * 100 / total_files ))"
            sleep 0.5
            continue
        fi

        # Process audio file
        update_progress "Transcoding audio file: - $base_name" "$percentage"

        if ! process_audio "$file" "$output_file"; then
            show_warning "Error transcoding audio file: - $base_name" &
        fi

    else
        # Unsupported file type
        show_warning "Unsupported file type: - $file_type for file $base_name" &
    fi

    # Update progress after processing each file
    if [ $current_file -eq $total_files ]; then
        update_progress "Transcoding finishing..." "99"
        sleep 1
        echo "100" >&3
    else
        update_progress "Processed: - $current_file of $total_files files" "$(( current_file * 100 / total_files ))"
        sleep 0.5
    fi
done

# Clean up
exec 3>&-
rm -f /tmp/progress_pipe

# Show completion message
show_info "Transcoding finished."

exit 0
