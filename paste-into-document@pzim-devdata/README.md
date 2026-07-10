# Paste into Document (.odt)

Paste clipboard content directly into a new document from Nemo's context menu. Supports multiple output formats including LibreOffice documents, PDF, and various text formats.

## Features

- **Rich text support**: Preserves formatting (bold, italic, colors, tables, lists, etc.)
- **Image support**: Paste images from clipboard or copied files
- **Multiple formats**: Choose from 11 different output formats
- **HTML preservation**: Keep original HTML structure when copying from web pages
- **Smart filename**: Auto-suggests filename based on content
- **No auto-open**: Creates document without opening it
- **Current location**: Document created where you right-clicked

## Supported Output Formats

### Text / Code
- Text (.txt) - Clean text without HTML tags
- Markdown (.md)
- HTML with formatting (.html) - Preserves HTML structure from web pages
- JSON (.json)
- YAML (.yaml)
- CSV (.csv)
- Python (.py)
- Shell script (.sh)

### Documents
- LibreOffice Writer (.odt)
- PDF (.pdf)

## How It Handles Web Content

When copying text from a web page:
- **Text formats** (.txt, .md, .py, etc.): Extracts clean, readable text without HTML tags
- **HTML format** (.html): Preserves the original HTML structure and formatting
- **Document formats** (.odt, .pdf): Extracts clean text for better readability

This means you can copy formatted content from websites and get clean, readable documents automatically.

## Requirements

- `python3` (pre-installed on most systems)
- `libreoffice` (for document formats)

## Installation

### Via Cinnamon Spices

1. Right-click on the desktop
2. Select "System Settings"
3. Go to "Actions"
4. Click "Download"
5. Search for "Paste into Document"
6. Click "Install"

### Manual Installation

```bash
# Copy action to Nemo actions directory
cp -r paste-into-document@pzim-devdata ~/.local/share/nemo/actions/
```

## Usage

1. Copy content to clipboard (text, formatted text, image, or file)
2. Navigate to desired folder in Nemo
3. Right-click in empty space or on a file
4. Select "Paste into Document (.odt)"
5. Enter filename (auto-suggested based on content)
6. Choose output format from dropdown
7. Click OK

The document is created at current location without opening.

## How Filename is Suggested

- **Copied file**: Uses original filename
- **Text/HTML**: Uses first 3-5 words
- **Image**: Uses timestamp
- **Default**: `new_document`

## Technical Details

- Uses GTK 3 for dialog interface
- LibreOffice headless mode for document conversion
- Supports HTML clipboard for rich formatting
- Intelligent HTML parsing: extracts text or preserves structure based on chosen format
- Handles images via base64 encoding
- Creates executable scripts when .sh format selected

## Why (.odt) in the name?

There is already a "paste-into-file" action that only creates plain text files. This action is different as it creates formatted LibreOffice documents and offers multiple format choices, with .odt being the primary format.

## Author

pzim-devdata
