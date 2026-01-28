# Print File

Open the native GTK print dialog for any file, providing the exact same printing experience as clicking File > Print in applications like gedit, evince, or any GNOME application.

This action uses GTK's PrintOperation API to display the system print dialog with full access to all CUPS printing options including printer selection, duplex printing, quality settings, color options, and more.

## Features

- **Native GTK print dialog**: Identical interface to File > Print in GNOME applications
- **Full CUPS integration**: All printer options available
- **No external dependencies**: Uses system GTK libraries
- **Universal file support**: Works with text files, PDFs, images, and more

## Requirements

- `python3-gi` (GTK bindings for Python, pre-installed on most systems)

## Installation

### Via Cinnamon Spices

1. Right-click on the desktop
2. Select "System Settings"
3. Go to "Actions"
4. Click "Download"
5. Search for "Print File"
6. Click "Install"

### Manual Installation

```bash
# Copy action to Nemo actions directory
cp -r print-native@pzim-devdata ~/.local/share/nemo/actions/
```

## Usage

1. Right-click on any file in Nemo
2. Select "Print File"
3. The native GTK print dialog opens (same as in gedit, evince, etc.)
4. Configure all printing options:
   - Select printer
   - Choose duplex mode (single/double-sided)
   - Set orientation (portrait/landscape)
   - Adjust quality settings
   - Configure color options
   - Set number of copies
   - And more...
5. Click "Print"

## Supported File Types

Text files, PDFs, PostScript, images (JPEG, PNG, GIF, BMP, TIFF, SVG), office documents, HTML, Markdown, and more.

## Technical Details

This action uses Python's `gi.repository.Gtk.PrintOperation` which is the same API used by GNOME applications like gedit and evince. This ensures a consistent, native printing experience with full CUPS support.

## Author

pzim-devdata
