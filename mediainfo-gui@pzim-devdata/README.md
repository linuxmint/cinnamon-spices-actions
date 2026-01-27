# Display Media Information

Display detailed media file information using MediaInfo GUI. This action allows you to quickly access comprehensive technical and metadata information about video, audio, image, and subtitle files directly from Nemo's context menu.

Unlike the basic properties tab in Cinnamon which shows limited information, MediaInfo GUI provides extensive details including:
- Container format and codec information
- Video: resolution, frame rate, bit rate, color space, HDR metadata
- Audio: channels, sample rate, bit depth, codec details
- Metadata: EXIF (images), ID3/Vorbis tags (audio), technical parameters
- Subtitles: format, language, encoding information

This action is particularly useful for media professionals, video editors, and anyone who needs detailed technical information about their media files.

## Requirements

- `mediainfo-gui` must be installed

## Installation

### Via Cinnamon Spices

1. Right-click on the desktop
2. Select "System Settings"
3. Go to "Actions" 
4. Click "Download" at the bottom
5. Search for "Display Media Information"
6. Click "Install"

### Manual Installation

```bash
# Install dependency
sudo apt install mediainfo-gui

# Copy action to Nemo actions directory
cp -r mediainfo-gui@pzim-devdata ~/.local/share/nemo/actions/
```

## Usage

1. Right-click on any media file in Nemo
2. Select "Display Media Information" from the context menu
3. MediaInfo GUI will open showing comprehensive file information

## Supported Formats

### Video
MPEG-4, QuickTime, Matroska, AVI, WMV, MPEG-PS/TS, MXF, FLV, WebM, and many more

### Audio
MP3, AAC, FLAC, OGG, AC3, DTS, WAV, WMA, and many more

### Images (Metadata)
JPEG, PNG, TIFF, GIF, WebP, HEIF/HEIC, BMP, DNG (RAW), and more

### Subtitles
SRT, SSA/ASS, SAMI, VobSub, WebVTT, TTML

## Information Displayed

- **General**: Container format, duration, file size, creation date
- **Video**: Codec, resolution, frame rate, bit rate, color space, HDR info
- **Audio**: Codec, channels, sample rate, bit depth, bit rate, language
- **Images**: EXIF metadata, GPS, camera settings, software used
- **Subtitles**: Format, language, encoding

## Author

pzim-devdata

## License

This Nemo action configuration is released under GPL-3.0 license.
MediaInfo itself is released under BSD-2-Clause license.
