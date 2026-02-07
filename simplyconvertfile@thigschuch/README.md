# Simply Convert File

A Nemo action for converting files between different formats. Right-click any supported file in the file manager to convert it.

![Screenshot](./screenshots/screenshot.png)

## About

This Nemo action is a thin integration layer that calls [SimplyConvertFile](https://github.com/thigschuch/simplyconvertfile), a standalone file conversion application. All conversion logic, format support, configuration, and UI are provided by the standalone app.

### Highlights

- **80+ supported formats** across images, video, audio, documents, and archives
- **Single & batch conversion** with progress tracking and cancellation
- **Cross-format conversions** (e.g., video to audio, GIF to video, documents to PDF)
- **Customizable** quality settings, conversion rules, and notifications
- **Internationalization** with 14+ languages

For full documentation on features, configuration, supported formats, and troubleshooting, see the [SimplyConvertFile README](https://github.com/thigschuch/simplyconvertfile).

## Dependencies

- **[SimplyConvertFile](https://github.com/thigschuch/simplyconvertfile)** — the standalone conversion application

Install it by downloading the latest `.deb` package from the [SimplyConvertFile releases](https://github.com/thigschuch/simplyconvertfile/releases):
```bash
sudo dpkg -i simplyconvertfile_*.deb
```

SimplyConvertFile has its own dependencies for format-specific conversions (ImageMagick, FFmpeg, LibreOffice, etc.). See its documentation for details.

## Installation

### Cinnamon Spices
1. Open **System Settings** → **Actions** (under Preferences)
2. Click **Download** → Search for "Simply Convert File" → **Install**
3. Install SimplyConvertFile

### Via APT Repository (recommended)

Add the SimplyConvertFile APT repository to get automatic updates via `apt upgrade`:

```bash
# Import the signing key
curl -fsSL https://thigschuch.github.io/SimplyConvertFile/gpg.key | sudo gpg --dearmor -o /usr/share/keyrings/simplyconvertfile.gpg

# Add the repository
echo "deb [signed-by=/usr/share/keyrings/simplyconvertfile.gpg] https://thigschuch.github.io/SimplyConvertFile/ stable main" | sudo tee /etc/apt/sources.list.d/simplyconvertfile.list

# Install
sudo apt update && sudo apt install simplyconvertfile
```

To update later:

```bash
sudo apt update && sudo apt upgrade
```

### Via .deb Package

Download and install the latest `.deb` release directly from the terminal:

```bash
# Download the latest release
wget -O /tmp/simplyconvertfile.deb \
  "$(curl -s https://api.github.com/repos/ThigSchuch/SimplyConvertFile/releases/latest \
  | grep -o '"browser_download_url": "[^"]*\.deb"' \
  | cut -d'"' -f4)"

# Install it
sudo dpkg -i /tmp/simplyconvertfile.deb
sudo apt-get install -f
```

Or download manually from the [Releases page](https://github.com/ThigSchuch/SimplyConvertFile/releases) and install:

```bash
sudo dpkg -i simplyconvertfile_*.deb
sudo apt-get install -f  # install dependencies if needed
```

## Usage

1. Right-click a file (or select multiple files) in Nemo
2. Select **"Simply Convert File"** from the context menu
3. Choose the target format and convert

For detailed usage instructions, batch conversion, keyboard shortcuts, configuration options, and more, see the [SimplyConvertFile documentation](https://github.com/thigschuch/simplyconvertfile).

## License

See [COPYING](../COPYING) file for license information.

## Author

**ThigSchuch**