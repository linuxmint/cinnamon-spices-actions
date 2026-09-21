# Paste into Document

Paste clipboard content directly into a new document from Nemo's context menu. Supports multiple output formats including LibreOffice documents, Microsoft Word, PDF, and many text/code formats.

## Features

- Rich text support: Preserves formatting (bold, italic, colors, tables, lists, etc.)
- Image support: Paste images from clipboard or copied files
- Multiple formats: Choose from 20+ output formats across three categories
- Two HTML modes: Save copied code as-is, or keep the raw HTML of a copied web page
- Smart filename: Auto-suggests filename based on content (HTML title, headings, or most repeated word)
- Clipboard snapshot: Content is captured before the dialog opens, so copying text while naming the file never alters the document
- No extension by default: The first entry of the format list adds no extension
- No auto-open: Creates document without opening it
- Current location: Document created where you right-clicked

## Supported Output Formats

### Text / Code

- Text (.txt), Markdown (.md), JSON (.json), YAML (.yaml)
- CSV (.csv), TSV (.tsv), INI (.ini), TOML (.toml), SQL (.sql)
- Python (.py), Shell script (.sh), JavaScript (.js), TypeScript (.ts)
- CSS (.css), PHP (.php), C (.c), C++ (.cpp), Java (.java), Ruby (.rb)
- XML (.xml), SVG source (.svg)
- HTML file from code (.html)

### Web page copy

- Raw HTML (copied web page, .html)

### Documents

- LibreOffice Writer (.odt), Microsoft Word (.docx), Rich Text (.rtf), PDF (.pdf)

The first entry of the format dropdown, **No extension added**, writes the plain text content without appending any extension.

## How It Handles Web Content

Two distinct HTML modes exist:

- **HTML file from code**: when you copy HTML source code from an editor (VS Code, vim, browser devtools), the file is saved exactly as copied. This mode always uses the plain text clipboard target, never a rendered variant.
- **Raw HTML (copied web page)**: when you copy content from a web page, this mode keeps the clipboard `text/html` target as-is, preserving the page structure.

For other text formats (.txt, .md, .py, etc.): clean, readable text is extracted without HTML tags. For document formats (.odt, .docx, .rtf, .pdf): HTML formatting is preserved through LibreOffice conversion.

## How Filename is Suggested

- Copied image file: Uses original filename
- HTML title or `<h1>`-`<h3>` heading: Uses its first words
- Plain text: Uses the phrase leading to the most repeated word
- Image in memory: Uses timestamp
- Default: `new_document`

## Technical Details

- Uses GTK 3 for dialog interface
- LibreOffice headless mode for document conversion
- Reads all clipboard representations (pixbuf, file URIs, text/html, plain text) once, before showing any dialog
- Handles images via base64 encoding
- Creates executable scripts when .sh format is selected

## Requirements

- `python3` (pre-installed on most systems)
- `libreoffice` (only for document formats: .odt, .docx, .rtf, .pdf)

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
cp -r paste-into-document@pzim-devdata ~/.local/share/nemo/actions/
nemo -q; nemo &
```

## Usage

1. Copy content to clipboard (text, formatted text, HTML, image, or file)
2. Navigate to desired folder in Nemo
3. Right-click in empty space
4. Select "Paste into Document"
5. Enter filename (auto-suggested based on content)
6. Choose output format from the dropdown (first entry: no extension)
7. Click OK

The document is created at current location without opening it.
