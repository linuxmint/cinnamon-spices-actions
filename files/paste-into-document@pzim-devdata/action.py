#!/usr/bin/python3
# Paste into Document : Nemo action - save clipboard content as a document
import os
import sys
import subprocess
import tempfile
import shutil
import re
import datetime
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

# ===== SECTION #1_CONSTANTES =====
ACTION_TITLE = "Paste into Document"
ENTRY_LABEL = "Document name (without extension):"
FORMAT_LABEL = "Output format:"
NO_EXTENSION_ENTRY = "No extension added"
INVALID_FILE_NAME = "Invalid file name!"
NO_CLIPBOARD_CONTENT = "No content found in clipboard. Operation cancelled."
FILE_EXISTS_MESSAGE = "File '%s' already exists. Do you want to replace it?"
ERROR_MESSAGE = "An error occurred while creating the document."

# Writing modes
MODE_TEXT = "text"          # plain write : copied code saved as-is
MODE_RAW_HTML = "raw_html"  # write the clipboard text/html target as-is
MODE_LO = "lo"              # LibreOffice headless conversion pipeline

# Formats available, organized by category
FORMATS = {
    "Text / Code": [
        ("Text (.txt)", "txt", MODE_TEXT),
        ("Markdown (.md)", "md", MODE_TEXT),
        ("JSON (.json)", "json", MODE_TEXT),
        ("YAML (.yaml)", "yaml", MODE_TEXT),
        ("CSV (.csv)", "csv", MODE_TEXT),
        ("TSV (.tsv)", "tsv", MODE_TEXT),
        ("INI (.ini)", "ini", MODE_TEXT),
        ("TOML (.toml)", "toml", MODE_TEXT),
        ("SQL (.sql)", "sql", MODE_TEXT),
        ("Python (.py)", "py", MODE_TEXT),
        ("Shell script (.sh)", "sh", MODE_TEXT),
        ("JavaScript (.js)", "js", MODE_TEXT),
        ("TypeScript (.ts)", "ts", MODE_TEXT),
        ("CSS (.css)", "css", MODE_TEXT),
        ("PHP (.php)", "php", MODE_TEXT),
        ("C (.c)", "c", MODE_TEXT),
        ("C++ (.cpp)", "cpp", MODE_TEXT),
        ("Java (.java)", "java", MODE_TEXT),
        ("Ruby (.rb)", "rb", MODE_TEXT),
        ("XML (.xml)", "xml", MODE_TEXT),
        ("SVG source (.svg)", "svg", MODE_TEXT),
        ("HTML file from code (.html)", "html", MODE_TEXT),
    ],
    "Web page copy": [
        ("Raw HTML (copied web page, .html)", "html", MODE_RAW_HTML),
    ],
    "Documents": [
        ("LibreOffice Writer (.odt)", "odt", MODE_LO),
        ("Microsoft Word (.docx)", "docx", MODE_LO),
        ("Rich Text (.rtf)", "rtf", MODE_LO),
        ("PDF (.pdf)", "pdf", MODE_LO),
    ]
}

# ===== SECTION #2_GENERATION_NOM_PAR_DEFAUT =====
def slugify(text, max_words=5, max_len=40):
    """Builds a file name from text by detecting the most repeated word"""

    def extract_words(text_input):
        text_clean = text_input.replace("'", " ").replace("`", " ").replace("\u2019", " ")
        return re.findall(r"[\w]+", text_clean.lower(), re.UNICODE)

    common_words = {'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'au', 'aux',
                   'je', 'tu', 'il', 'elle', 'on', 'nous', 'vous', 'ils', 'elles',
                   'me', 'te', 'se', 'lui', 'leur', 'y', 'en',
                   'mon', 'ton', 'son', 'ma', 'ta', 'sa', 'mes', 'tes', 'ses',
                   'ce', 'cet', 'cette', 'ces', 'qui', 'que', 'quoi', 'dont', 'où',
                   'et', 'ou', 'mais', 'donc', 'or', 'ni', 'car', 'si',
                   'à', 'dans', 'par', 'pour', 'vers', 'avec', 'sans', 'sous', 'sur', 'chez',
                   'est', 'sont', 'était', 'étaient', 'être', 'avoir', 'ai', 'as', 'a', 'ont', 'suis', 'es',
                   'the', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
                   'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being', 'he', 'she', 'they', 'his', 'her',
                   'this', 'that', 'these', 'those', 'it', 'its',
                   'div', 'span', 'style', 'class', 'data', 'href', 'src', 'img', 'html', 'body', 'head'}

    candidates = []

    # STRATEGY 0: extract HTML <title> if present (highest priority)
    title_match = re.search(r'<title[^>]*>\s*(.+?)\s*</title>', text, re.IGNORECASE | re.DOTALL)
    if title_match:
        title_text = title_match.group(1).strip()
        title_text = title_text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        title_text = title_text.replace('&quot;', '"').replace('&#39;', "'").replace('&mdash;', '-').replace('&ndash;', '-')

        if title_text and len(title_text) >= 3:
            title_words = extract_words(title_text)
            clean_title = [w for w in title_words if len(w) >= 2 and w not in common_words]
            if clean_title:
                candidates.append(('html_title', clean_title[:max_words]))

    # STRATEGY 0a: extract <h1>, <h2>, <h3>
    for heading_level in ['h1', 'h2', 'h3']:
        heading_match = re.search(rf'<{heading_level}[^>]*>(.*?)</{heading_level}>', text, re.IGNORECASE | re.DOTALL)
        if heading_match:
            heading_text = heading_match.group(1).strip()
            heading_text = re.sub(r'<[^>]+>', '', heading_text)
            heading_text = heading_text.replace('&nbsp;', ' ').replace('&amp;', '&')

            if heading_text and len(heading_text) >= 3:
                heading_words = extract_words(heading_text)
                clean_heading = [w for w in heading_words if len(w) >= 2 and w not in common_words]
                if clean_heading and len(clean_heading) >= 1:
                    candidates.append(('html_heading', clean_heading[:max_words]))
                    break

    # STRATEGY 0b: first relevant link text
    skip_phrases = {'skip to', 'skip content', 'menu', 'navigation',
                   'back', 'next', 'previous', 'more', 'close'}

    all_links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', text, re.IGNORECASE | re.DOTALL)

    for href_url, link_text in all_links[:15]:
        link_text = re.sub(r'<[^>]+>', '', link_text).strip()
        link_text = link_text.replace('&nbsp;', ' ').replace('&amp;', '&')

        if link_text and len(link_text) >= 3:
            link_lower = link_text.lower()

            if not any(skip in link_lower for skip in skip_phrases):
                link_words = extract_words(link_text)
                clean_link = [w for w in link_words if len(w) >= 2 and w not in common_words]

                if clean_link and len(clean_link) >= 1:
                    candidates.append(('html_href', clean_link[:max_words]))
                    break

    # Remove HTML tags for other strategies
    text_clean = re.sub(r'<[^>]+>', '', text)

    # MAIN STRATEGY: most repeated word + phrase leading to it
    all_words = extract_words(text_clean)

    if len(all_words) >= 3:
        word_counts = {}
        for word in all_words:
            if len(word) >= 3 and word not in common_words:
                word_counts[word] = word_counts.get(word, 0) + 1

        if word_counts:
            most_repeated_word = max(word_counts, key=word_counts.get)

            try:
                first_occurrence_index = all_words.index(most_repeated_word)

                start_index = max(0, first_occurrence_index - (max_words - 1))
                phrase_words = all_words[start_index:first_occurrence_index + 1]

                phrase_clean = [w for w in phrase_words if len(w) >= 2]

                if len(phrase_clean) >= 1:
                    candidates.append(('repeated_phrase', phrase_clean[:max_words]))
            except ValueError:
                pass

    if not candidates:
        return None

    priority_order = ['html_title', 'html_heading', 'repeated_phrase', 'html_href']
    for strategy in priority_order:
        for cand_type, cand_words in candidates:
            if cand_type == strategy and cand_words:
                slug = "_".join(cand_words[:max_words])
                return slug[:max_len] if slug else None

    return None


def guess_default_filename(snap):
    """Builds a default file name from a clipboard snapshot"""
    if snap["image_file"]:
        base = os.path.basename(snap["image_file"])
        return os.path.splitext(base)[0]

    # Prefer raw HTML (richer title extraction), fallback to plain text
    for content in (snap["raw_html"], snap["text"], snap["html_text"]):
        if isinstance(content, str) and content.strip():
            name = slugify(content)
            if name:
                return name

    if snap["image"]:
        return "image_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    return "new_document"

# ===== SECTION #3_DIALOGUES =====
def get_file_name_and_format(default_name=None):
    """Asks for file name and output format via a GTK dialog"""
    dialog = Gtk.Dialog(
        title=ACTION_TITLE,
        flags=Gtk.DialogFlags.MODAL
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        Gtk.STOCK_OK, Gtk.ResponseType.OK
    )

    box = dialog.get_content_area()
    box.set_spacing(10)
    box.set_margin_top(10)
    box.set_margin_bottom(10)
    box.set_margin_start(15)
    box.set_margin_end(15)

    # File name field
    label_name = Gtk.Label(label=ENTRY_LABEL)
    label_name.set_halign(Gtk.Align.START)
    box.pack_start(label_name, False, False, 0)

    entry = Gtk.Entry()
    if default_name:
        entry.set_text(default_name)
    entry.set_activates_default(True)
    box.pack_start(entry, False, False, 0)

    separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    box.pack_start(separator, False, False, 5)

    # Format selector
    label_format = Gtk.Label(label=FORMAT_LABEL)
    label_format.set_halign(Gtk.Align.START)
    box.pack_start(label_format, False, False, 0)

    combo = Gtk.ComboBoxText()
    format_list = []   # (ext, mode) in combo order ; ext=None means no extension

    # First entry: no extension, plain-text content
    combo.append_text(NO_EXTENSION_ENTRY)
    format_list.append((None, MODE_TEXT))

    for category, formats in FORMATS.items():
        for label, ext, mode in formats:
            combo.append_text(f"{category} \u2014 {label}")
            format_list.append((ext, mode))

    combo.set_active(0)  # Default: no extension
    box.pack_start(combo, False, False, 0)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.set_default_size(480, 200)
    dialog.show_all()

    response = dialog.run()

    if response == Gtk.ResponseType.OK:
        filename = entry.get_text().strip()
        index = combo.get_active()
        format_ext, mode = format_list[index]
    else:
        filename = None
        format_ext = None
        mode = None

    dialog.destroy()
    return filename, format_ext, mode


def show_message(message: str, message_type=Gtk.MessageType.INFO):
    """Shows an info or error message"""
    dialog = Gtk.MessageDialog(
        flags=Gtk.DialogFlags.MODAL,
        message_type=message_type,
        buttons=Gtk.ButtonsType.OK,
        text=message
    )
    dialog.set_title(ACTION_TITLE)
    dialog.run()
    dialog.destroy()


def ask_yes_no(question: str) -> bool:
    """Asks a yes/no question"""
    dialog = Gtk.MessageDialog(
        flags=Gtk.DialogFlags.MODAL,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.YES_NO,
        text=question
    )
    dialog.set_title(ACTION_TITLE)
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.YES

# ===== SECTION #4_SNAPSHOT_PRESSE_PAPIERS =====
def strip_html_tags(html_content):
    """Extracts visible text from HTML content"""
    html_clean = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_clean = re.sub(r'<style[^>]*>.*?</style>', '', html_clean, flags=re.DOTALL | re.IGNORECASE)
    html_clean = re.sub(r'<br\s*/?>', '\n', html_clean, flags=re.IGNORECASE)
    html_clean = re.sub(r'</p>', '\n', html_clean, flags=re.IGNORECASE)
    html_clean = re.sub(r'</div>', '\n', html_clean, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', html_clean)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'")
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n\n+', '\n\n', text)
    return text.strip()


def snapshot_clipboard():
    """Reads the clipboard ONCE and stores every representation.

    Called before any dialog so that later copies (typically the file
    name itself) can never overwrite the original content.
    """
    clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    snap = {
        "image": None,       # in-memory pixbuf
        "image_file": None,  # path of a copied image file
        "raw_html": None,    # text/html target, as-is (web page copy)
        "html_text": None,   # visible text extracted from raw_html
        "text": None         # plain text target (copied code included)
    }

    # 1. In-memory image
    pixbuf = clip.wait_for_image()
    if pixbuf is not None:
        snap["image"] = pixbuf

    # 2. File URIs
    uris = clip.wait_for_uris()
    if uris:
        uri = uris[0]
        if uri.startswith('file://'):
            import urllib.parse
            filepath = urllib.parse.unquote(uri[7:])

            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff', '.svg')
            if filepath.lower().endswith(image_extensions):
                snap["image_file"] = filepath

    # 3. Raw HTML target (available after a web page copy)
    html_target = Gdk.Atom.intern("text/html", False)
    if clip.wait_is_target_available(html_target):
        selection_data = clip.wait_for_contents(html_target)
        if selection_data:
            raw = selection_data.get_data().decode('utf-8', errors='ignore')
            if raw:
                snap["raw_html"] = raw
                stripped = strip_html_tags(raw)
                if stripped:
                    snap["html_text"] = stripped

    # 4. Plain text (copied code lands here, even if an editor
    #    also provides a syntax-highlighted text/html target)
    snap["text"] = clip.wait_for_text()

    return snap


def snapshot_is_empty(snap):
    return not any(v is not None and v != "" for v in snap.values())


def pick_content(snap, mode):
    """Selects the best (content, content_type) pair for the chosen mode"""
    if mode == MODE_RAW_HTML:
        # Raw HTML from a web page copy ; if unavailable, the plain
        # text is likely HTML code copied from an editor : keep it as-is
        if snap["raw_html"]:
            return snap["raw_html"], "html"
        if snap["text"]:
            return snap["text"], "text"
        if snap["html_text"]:
            return snap["html_text"], "text"
        return None, None

    if mode == MODE_LO:
        # LibreOffice pipeline : HTML preferred over plain text
        if snap["image"]:
            return snap["image"], "image"
        if snap["image_file"]:
            return snap["image_file"], "image_file"
        if snap["raw_html"]:
            return snap["raw_html"], "html"
        if snap["text"]:
            return snap["text"], "text"
        if snap["html_text"]:
            return snap["html_text"], "text"
        return None, None

    # MODE_TEXT : plain text wins, protects copied code integrity
    if snap["text"]:
        return snap["text"], "text"
    if snap["html_text"]:
        return snap["html_text"], "text"
    if snap["raw_html"]:
        return snap["raw_html"], "text"
    if snap["image_file"]:
        return snap["image_file"], "image_file"
    if snap["image"]:
        return snap["image"], "image"
    return None, None

# ===== SECTION #5_CREATION_FICHIERS_TEXTE =====
def create_text_file(content, filepath, format_ext):
    """Creates a plain text file (code or raw HTML saved as-is)"""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            if isinstance(content, str):
                f.write(content)
            else:
                f.write("")

        # Make shell scripts executable
        if format_ext == "sh":
            os.chmod(filepath, 0o755)

        return True
    except Exception as e:
        print(f"Error creating text file: {e}", file=sys.stderr)
        return False

# ===== SECTION #6_CREATION_DOCUMENTS_LIBREOFFICE =====
def create_document_from_content(content, content_type, output_filepath, format_ext):
    """Creates a document via LibreOffice headless HTML-to-target conversion"""
    temp_dir = tempfile.mkdtemp()

    try:
        # Step 1: build the temporary HTML
        if content_type == "image":
            temp_image = os.path.join(temp_dir, "image.png")
            content.savev(temp_image, "png", [], [])

            import base64
            with open(temp_image, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            html_content = f'<img src="data:image/png;base64,{image_data}" />'

        elif content_type == "image_file":
            import base64
            with open(content, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            ext = os.path.splitext(content)[1].lower()
            mime_types = {
                '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.gif': 'image/gif', '.bmp': 'image/bmp', '.webp': 'image/webp',
                '.svg': 'image/svg+xml',
            }
            mime_type = mime_types.get(ext, 'image/jpeg')

            html_content = f'<img src="data:{mime_type};base64,{image_data}" />'

        elif content_type == "html":
            html_content = content

        else:  # text
            html_content = content.replace('\n', '<br>')

        temp_html = os.path.join(temp_dir, "temp.html")
        with open(temp_html, "w", encoding="utf-8") as f:
            html_doc = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
{html_content}
</body>
</html>"""
            f.write(html_doc)

        # Step 2: HTML -> ODT
        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to", "odt",
                "--outdir", temp_dir,
                temp_html
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return False

        temp_odt = os.path.join(temp_dir, "temp.odt")

        if not os.path.exists(temp_odt):
            return False

        # Step 3: ODT -> final format if needed
        if format_ext == "odt":
            shutil.move(temp_odt, output_filepath)

        else:
            result = subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to", format_ext,
                    "--outdir", temp_dir,
                    temp_odt
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return False

            temp_final = os.path.join(temp_dir, f"temp.{format_ext}")

            if not os.path.exists(temp_final):
                return False

            shutil.move(temp_final, output_filepath)

        return True

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# ===== SECTION #7_DISPATCH =====
def create_document_dispatch(content, content_type, filepath, format_ext, mode):
    """Dispatches to the right function according to the writing mode"""
    if mode == MODE_LO:
        return create_document_from_content(content, content_type, filepath, format_ext)
    return create_text_file(content, filepath, format_ext)

# ===== SECTION #8_LOGIQUE_PRINCIPALE =====
def main() -> None:
    if len(sys.argv) < 2:
        exit(1)

    directory = sys.argv[1].replace("\\ ", " ")

    # Snapshot the clipboard BEFORE any dialog : later copies
    # (file name, etc.) can no longer replace the original content
    snap = snapshot_clipboard()

    if snapshot_is_empty(snap):
        show_message(NO_CLIPBOARD_CONTENT, Gtk.MessageType.WARNING)
        exit(1)

    # Default name computed from the frozen snapshot
    default_name = guess_default_filename(snap) or "new_document"

    # Dialog returns : filename, format_ext (None if "no extension"), mode
    filename, format_ext, mode = get_file_name_and_format(default_name)

    if not filename or filename.strip() == "":
        exit(1)

    # Select content from the frozen snapshot, according to the mode
    content, content_type = pick_content(snap, mode)

    if content is None:
        show_message(NO_CLIPBOARD_CONTENT, Gtk.MessageType.WARNING)
        exit(1)

    filename = filename.strip()

    # Append extension only when a real format was selected.
    # "No extension added" -> format_ext is None -> nothing appended.
    # If the user typed "notes.txt" himself, the name is kept untouched.
    if format_ext and not filename.lower().endswith(f'.{format_ext}'):
        filename = f"{filename}.{format_ext}"

    filepath = os.path.join(directory, filename)

    # Validity check
    if os.path.isdir(filepath):
        show_message(INVALID_FILE_NAME, Gtk.MessageType.ERROR)
        exit(1)

    # Confirmation if the file exists
    if os.path.exists(filepath):
        if not ask_yes_no(FILE_EXISTS_MESSAGE % filename):
            exit(1)

    success = create_document_dispatch(content, content_type, filepath, format_ext, mode)

    if not success:
        show_message(ERROR_MESSAGE, Gtk.MessageType.ERROR)
        exit(1)

    exit(0)


if __name__ == "__main__":
    main()
