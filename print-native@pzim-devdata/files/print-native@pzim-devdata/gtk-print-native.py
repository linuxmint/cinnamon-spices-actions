#!/usr/bin/env python3
"""
Script pour ouvrir le dialogue d'impression GTK natif
Équivalent à Fichier > Imprimer dans gedit
"""

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

def print_file(filename):
    """Ouvre le dialogue d'impression GTK pour un fichier"""
    
    # Créer l'opération d'impression
    print_op = Gtk.PrintOperation()
    
    # Configurer l'opération
    print_op.set_n_pages(1)
    print_op.set_unit(Gtk.Unit.POINTS)
    
    # Connecter le signal pour dessiner la page
    def draw_page(operation, context, page_nr):
        """Callback pour dessiner le contenu à imprimer"""
        cairo_ctx = context.get_cairo_context()
        pango_layout = context.create_pango_layout()
        
        # Lire le fichier
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            content = f"Erreur de lecture : {str(e)}"
        
        # Configurer le texte
        pango_layout.set_text(content, -1)
        pango_layout.set_width(int(context.get_width() * 1024))
        
        # Dessiner
        cairo_ctx.move_to(0, 0)
        from gi.repository import PangoCairo
        PangoCairo.show_layout(cairo_ctx, pango_layout)
    
    print_op.connect("draw-page", draw_page)
    
    # Lancer l'opération d'impression (affiche le dialogue)
    result = print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, None)
    
    if result == Gtk.PrintOperationResult.APPLY:
        print("Impression lancée")
    elif result == Gtk.PrintOperationResult.CANCEL:
        print("Impression annulée")
    else:
        print("Erreur d'impression")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: gtk-print-native.py <fichier>")
        sys.exit(1)
    
    filename = sys.argv[1]
    print_file(filename)
