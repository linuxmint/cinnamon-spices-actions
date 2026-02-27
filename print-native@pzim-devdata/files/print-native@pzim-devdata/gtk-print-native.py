#!/usr/bin/env python3

import sys
import mimetypes
import subprocess
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, PangoCairo


# ===== SECTION #1_UTILS =====

def command_exists(cmd):
    return subprocess.call(
        ["which", cmd],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ) == 0


# ===== SECTION #2_GTK_TEXT_PRINT =====

def print_text_with_gtk(filename):
    print_op = Gtk.PrintOperation()
    print_op.set_n_pages(1)

    def draw_page(operation, context, page_nr):
        cairo_ctx = context.get_cairo_context()
        layout = context.create_pango_layout()

        try:
            with open(filename, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            content = f"Erreur de lecture : {e}"

        layout.set_text(content, -1)
        layout.set_width(int(context.get_width() * 1024))

        cairo_ctx.move_to(20, 20)
        PangoCairo.show_layout(cairo_ctx, layout)

    print_op.connect("draw-page", draw_page)
    print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, None)


# ===== SECTION #3_DISPATCHER =====

def smart_print(filename):
    mime, _ = mimetypes.guess_type(filename)
    mime = mime or ""

    # --- TEXTE ---
    if mime.startswith("text/") or mime in (
        "application/json",
        "application/xml",
    ):
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

