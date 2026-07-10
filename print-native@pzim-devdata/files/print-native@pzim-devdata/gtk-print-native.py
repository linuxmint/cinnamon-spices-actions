#!/usr/bin/env python3
import sys
import mimetypes
import subprocess
import gi
gi.require_version("Gtk", "3.0")
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Pango, PangoCairo

# ===== SECTION #1_UTILS =====
def command_exists(cmd):
    return subprocess.call(
        ["which", cmd],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ) == 0

def detect_mime(filename):
    # 1. Par extension
    mime, _ = mimetypes.guess_type(filename)
    if mime:
        return mime
    # 2. Par contenu via `file`
    try:
        result = subprocess.run(
            ["file", "--mime-type", "-b", filename],
            capture_output=True, text=True
        )
        mime = result.stdout.strip()
        if mime:
            return mime
    except Exception:
        pass
    # 3. Tentative lecture UTF-8
    try:
        with open(filename, "rb") as f:
            f.read(512).decode("utf-8")
        return "text/plain"
    except Exception:
        pass
    return ""

# ===== SECTION #2_GTK_TEXT_PRINT =====
def print_text_with_gtk(filename):
    try:
        with open(filename, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        content = f"Erreur de lecture : {e}"

    print_op = Gtk.PrintOperation()
    pages_content = []

    def begin_print(operation, context):
        layout = context.create_pango_layout()
        layout.set_width(int(context.get_width() * Pango.SCALE))
        layout.set_wrap(Pango.WrapMode.WORD_CHAR)
        layout.set_text(content, -1)

        page_height = context.get_height() * Pango.SCALE
        iter_ = layout.get_iter()
        current_page_lines = []
        current_height = 0
        all_pages = []

        while True:
            ink_rect, logical_rect = iter_.get_line_extents()
            line_height = logical_rect.height
            if current_height + line_height > page_height and current_page_lines:
                all_pages.append(current_page_lines)
                current_page_lines = [iter_.get_line()]
                current_height = line_height
            else:
                current_page_lines.append(iter_.get_line())
                current_height += line_height
            if not iter_.next_line():
                break

        if current_page_lines:
            all_pages.append(current_page_lines)

        pages_content.extend(all_pages)
        operation.set_n_pages(max(1, len(pages_content)))

    def draw_page(operation, context, page_nr):
        cairo_ctx = context.get_cairo_context()
        layout = context.create_pango_layout()
        layout.set_width(int(context.get_width() * Pango.SCALE))
        layout.set_wrap(Pango.WrapMode.WORD_CHAR)
        layout.set_text(content, -1)
        cairo_ctx.move_to(0, 0)
        PangoCairo.show_layout(cairo_ctx, layout)

    def done(operation, result):
        Gtk.main_quit()

    print_op.connect("begin-print", begin_print)
    print_op.connect("draw-page", draw_page)
    print_op.connect("done", done)
    print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, None)
    Gtk.main()

# ===== SECTION #3_DISPATCHER =====
def smart_print(filename):
    mime = detect_mime(filename)

    # --- TEXTE ---
    if mime.startswith("text/") or mime in ("application/json", "application/xml"):
        print_text_with_gtk(filename)
        return

    # --- PDF ---
    if mime == "application/pdf" and command_exists("evince"):
        subprocess.run(["evince", "--print-dialog", filename])
        return

    # --- IMAGES ---
    if mime.startswith("image/") and command_exists("eog"):
        subprocess.run(["eog", "--print", filename])
        return

    # --- FALLBACK ---
    subprocess.run(["xdg-open", filename])

# ===== SECTION #4_MAIN =====
if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    smart_print(sys.argv[1])
