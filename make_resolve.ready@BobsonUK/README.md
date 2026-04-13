# Make resolve.ready
Convert video/audio files to DaVinci Resolve compatible formats.

# Description
Automatically transcode video and audio files into
formats that are optimized for DaVinci Resolve:
- Video: DNxHR HQ codec with PCM 24-bit audio (stored in resolve.ready/video/)
- Audio: PCM 24-bit audio (stored in resolve.ready/audio/)

Files are marked with "resolve.ready" in their filename and organized into
dedicated directories to ensure they remain identifiable even if moved.

# Dependencies
The following packages need to be installed:
- zenity
- ffmpeg
