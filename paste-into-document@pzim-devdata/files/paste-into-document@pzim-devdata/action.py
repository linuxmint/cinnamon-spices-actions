#!/usr/bin/python3
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
ACTION_TITLE = "Paste into document"
ENTRY_LABEL = "Document name (without extension):"
FORMAT_LABEL = "Output format:"
INVALID_FILE_NAME = "Invalid file name!"
NO_CLIPBOARD_CONTENT = "No content found in clipboard. Operation cancelled."
FILE_EXISTS_MESSAGE = "File '%s' already exists. Do you want to replace it?"
PROCESSING_MESSAGE = "Creating document..."
ERROR_MESSAGE = "An error occurred while creating the document."

# Formats disponibles organisés par catégorie
FORMATS = {
    "Text / Code": [
        ("Text (.txt)", "txt"),
        ("Markdown (.md)", "md"),
        ("Raw HTML (.html)", "html"),
        ("JSON (.json)", "json"),
        ("YAML (.yaml)", "yaml"),
        ("CSV (.csv)", "csv"),
        ("Python (.py)", "py"),
        ("Shell script (.sh)", "sh"),
    ],
    "Documents": [
        ("LibreOffice Writer (.odt)", "odt"),
        ("PDF (.pdf)", "pdf"),
    ]
}

# Formats texte simple (pas de conversion LibreOffice)
TEXT_FORMATS = {"txt", "md", "html", "json", "yaml", "csv", "py", "sh"}

# ===== SECTION #2_GENERATION_NOM_PAR_DEFAUT =====
def slugify(text, max_words=5, max_len=40):
    """Nettoie un texte pour créer un nom de fichier en détectant les éléments pertinents"""
    # Enlever les balises HTML si présentes
    text_clean = re.sub(r'<[^>]+>', '', text)
    
    # Mots à ignorer (HTML/CSS et mots courants)
    html_keywords = {'div', 'span', 'style', 'class', 'data', 'rgb', 'color', 'panel', 'quot', 
                     'flow', 'href', 'src', 'img', 'html', 'body', 'head', 'meta', 'the', 'and', 
                     'for', 'with', 'this', 'that', 'from'}
    
    candidates = []
    
    # STRATÉGIE 1 : Détecter les paires clé=valeur (ex: "title=Mon Document" ou "nom: Rapport")
    kv_patterns = [
        r'(?:title|name|nom|titre|subject|sujet|filename)\s*[=:]\s*["\']?([^"\'\n]{3,30})["\']?',
        r'(?:Title|Name|Nom|Titre|Subject|Sujet)\s*[=:]\s*["\']?([^"\'\n]{3,30})["\']?'
    ]
    for pattern in kv_patterns:
        matches = re.findall(pattern, text_clean, re.IGNORECASE)
        if matches:
            # Nettoyer et ajouter les valeurs trouvées
            for match in matches[:2]:  # Prendre max 2 résultats
                words = re.findall(r"[a-zA-Z0-9]+", match)
                clean_words = [w.lower() for w in words if len(w) >= 3 and w.lower() not in html_keywords]
                if clean_words:
                    candidates.append(('kv_pair', clean_words[:4]))
    
    # STRATÉGIE 2 : Détecter les mots en MAJUSCULES (titres potentiels)
    # Chercher séquences de 2-6 mots consécutifs en majuscules
    uppercase_pattern = r'\b([A-Z][A-Z]+(?:\s+[A-Z][A-Z]+){1,5})\b'
    uppercase_matches = re.findall(uppercase_pattern, text_clean)
    for match in uppercase_matches[:2]:
        words = re.findall(r"[A-Z]+", match)
        clean_words = [w.lower() for w in words if len(w) >= 3 and w.lower() not in html_keywords]
        if len(clean_words) >= 2:  # Au moins 2 mots en majuscules
            candidates.append(('uppercase', clean_words[:4]))
    
    # STRATÉGIE 3 : Détecter les mots répétés (importance par fréquence)
    all_words = re.findall(r"[a-zA-Z]{3,}", text_clean.lower())
    word_counts = {}
    for word in all_words:
        if word not in html_keywords and not word.startswith('data'):
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # Garder les mots répétés au moins 2 fois
    repeated_words = [(word, count) for word, count in word_counts.items() if count >= 2]
    if repeated_words:
        # Trier par fréquence décroissante
        repeated_words.sort(key=lambda x: x[1], reverse=True)
        top_repeated = [word for word, count in repeated_words[:4]]
        candidates.append(('repeated', top_repeated))
    
    # STRATÉGIE 4 : Détecter la première ligne/phrase (souvent le titre)
    first_line = text_clean.split('\n')[0].strip()
    if len(first_line) > 5 and len(first_line) < 100:
        first_words = re.findall(r"[a-zA-Z0-9]{3,}", first_line.lower())
        clean_first = [w for w in first_words if w not in html_keywords][:5]
        if len(clean_first) >= 2:
            candidates.append(('first_line', clean_first))
    
    # STRATÉGIE 5 : Fallback - premiers mots significatifs du texte
    words = re.findall(r"[a-zA-Z0-9]{3,}", text_clean.lower())
    words_filtered = [w for w in words if w not in html_keywords and not w.startswith('data')]
    if words_filtered:
        candidates.append(('fallback', words_filtered[:max_words]))
    
    # Sélectionner le meilleur candidat (ordre de priorité)
    if not candidates:
        return None
    
    # Priorité : kv_pair > uppercase > repeated > first_line > fallback
    priority_order = ['kv_pair', 'uppercase', 'repeated', 'first_line', 'fallback']
    for strategy in priority_order:
        for cand_type, cand_words in candidates:
            if cand_type == strategy and cand_words:
                slug = "_".join(cand_words[:max_words])
                return slug[:max_len] if slug else None
    
    return None


def guess_default_filename(content, content_type):
    """Génère un nom de fichier par défaut basé sur le contenu"""
    # URI / fichier image
    if content_type == "image_file":
        base = os.path.basename(content)
        return os.path.splitext(base)[0]
    
    # Texte ou HTML - prendre les premiers mots
    if content_type in ("text", "html") and isinstance(content, str):
        name = slugify(content)
        if name:
            return name
    
    # Image en mémoire
    if content_type == "image":
        return "image_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return "new_document"

# ===== SECTION #3_DIALOGUES =====
def get_file_name_and_format(default_name: str = None):
    """Demande le nom du fichier et le format via un dialogue GTK"""
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
    
    # Champ nom de fichier
    label_name = Gtk.Label(label=ENTRY_LABEL)
    label_name.set_halign(Gtk.Align.START)
    box.pack_start(label_name, False, False, 0)
    
    entry = Gtk.Entry()
    if default_name:
        entry.set_text(default_name)
    entry.set_activates_default(True)
    box.pack_start(entry, False, False, 0)
    
    # Séparateur
    separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    box.pack_start(separator, False, False, 5)
    
    # Sélecteur de format
    label_format = Gtk.Label(label=FORMAT_LABEL)
    label_format.set_halign(Gtk.Align.START)
    box.pack_start(label_format, False, False, 0)
    
    combo = Gtk.ComboBoxText()
    format_list = []
    
    for category, formats in FORMATS.items():
        for label, ext in formats:
            display_label = f"{category} — {label}"
            combo.append_text(display_label)
            format_list.append(ext)
    
    combo.set_active(0)  # Par défaut : premier format
    box.pack_start(combo, False, False, 0)
    
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.set_default_size(450, 180)
    dialog.show_all()
    
    response = dialog.run()
    
    if response == Gtk.ResponseType.OK:
        filename = entry.get_text().strip()
        format_ext = format_list[combo.get_active()]
    else:
        filename = None
        format_ext = None
    
    dialog.destroy()
    return filename, format_ext


def show_message(message: str, message_type=Gtk.MessageType.INFO):
    """Affiche un message d'information ou d'erreur"""
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
    """Pose une question oui/non à l'utilisateur"""
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

# ===== SECTION #4_GESTION_PRESSE_PAPIERS =====
def strip_html_tags(html_content):
    """Extrait le texte visible d'un contenu HTML"""
    # Supprimer scripts et styles avec leur contenu
    html_clean = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_clean = re.sub(r'<style[^>]*>.*?</style>', '', html_clean, flags=re.DOTALL | re.IGNORECASE)
    # Remplacer <br>, <p>, <div> par des sauts de ligne
    html_clean = re.sub(r'<br\s*/?>', '\n', html_clean, flags=re.IGNORECASE)
    html_clean = re.sub(r'</p>', '\n', html_clean, flags=re.IGNORECASE)
    html_clean = re.sub(r'</div>', '\n', html_clean, flags=re.IGNORECASE)
    # Supprimer toutes les balises restantes
    text = re.sub(r'<[^>]+>', '', html_clean)
    # Décoder les entités HTML courantes
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'")
    # Nettoyer les espaces multiples et lignes vides excessives
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n\n+', '\n\n', text)
    return text.strip()


def get_clipboard_content(preserve_html=False):
    """Récupère le contenu du presse-papiers (image, URI, HTML ou texte)
    
    Args:
        preserve_html: Si True, conserve le HTML brut. Si False, extrait le texte visible.
    """
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    
    # 1. Image en mémoire
    pixbuf = clipboard.wait_for_image()
    if pixbuf is not None:
        return pixbuf, "image"
    
    # 2. URIs (chemins de fichiers)
    uris = clipboard.wait_for_uris()
    if uris and len(uris) > 0:
        uri = uris[0]
        if uri.startswith('file://'):
            import urllib.parse
            filepath = urllib.parse.unquote(uri[7:])
            
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff', '.svg')
            if filepath.lower().endswith(image_extensions):
                return filepath, "image_file"
    
    # 3. HTML
    html_target = Gdk.Atom.intern("text/html", False)
    if clipboard.wait_is_target_available(html_target):
        selection_data = clipboard.wait_for_contents(html_target)
        if selection_data:
            html_content = selection_data.get_data().decode('utf-8', errors='ignore')
            
            if preserve_html:
                # Conserver le HTML brut pour format .html
                return html_content, "html"
            else:
                # Extraire le texte propre pour autres formats
                text_content = strip_html_tags(html_content)
                if text_content:
                    return text_content, "text"
    
    # 4. Texte brut (fallback)
    text_content = clipboard.wait_for_text()
    if text_content:
        return text_content, "text"
    
    return None, None

# ===== SECTION #5_CREATION_FICHIERS_TEXTE =====
def create_text_file(content, filepath, format_ext):
    """Crée un fichier texte simple"""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            if isinstance(content, str):
                f.write(content)
            else:
                f.write("")
        
        # Rendre exécutable si script shell
        if format_ext == "sh":
            os.chmod(filepath, 0o755)
        
        return True
    except Exception as e:
        print(f"Error creating text file: {e}", file=sys.stderr)
        return False

# ===== SECTION #6_CREATION_DOCUMENTS_LIBREOFFICE =====
def create_document_from_content(content, content_type, output_filepath, format_ext):
    """Crée un document LibreOffice à partir du contenu"""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Étape 1 : Créer HTML temporaire
        if content_type == "image":
            # Image en mémoire → PNG → base64
            temp_image = os.path.join(temp_dir, "image.png")
            content.savev(temp_image, "png", [], [])
            
            import base64
            with open(temp_image, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            html_content = f'<img src="data:image/png;base64,{image_data}" />'
        
        elif content_type == "image_file":
            # Fichier image → base64
            import base64
            with open(content, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            ext = os.path.splitext(content)[1].lower()
            mime_types = {
                '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.gif': 'image/gif', '.bmp': 'image/bmp', '.webp': 'image/webp',
            }
            mime_type = mime_types.get(ext, 'image/jpeg')
            
            html_content = f'<img src="data:{mime_type};base64,{image_data}" />'
        
        elif content_type == "html":
            html_content = content
        
        else:  # text
            html_content = content.replace('\n', '<br>')
        
        # Créer fichier HTML
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
        
        # Étape 2 : Convertir HTML → format demandé
        # D'abord HTML → ODT
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
        
        # Étape 3 : Convertir ODT → format final si nécessaire
        if format_ext == "odt":
            # Déjà en ODT, juste déplacer
            shutil.move(temp_odt, output_filepath)
        
        elif format_ext == "pdf":
            # Convertir ODT → PDF
            result = subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", temp_dir,
                    temp_odt
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return False
            
            temp_final = os.path.join(temp_dir, "temp.pdf")
            
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
def create_document_dispatch(content, content_type, filepath, format_ext):
    """Dispatche vers la bonne fonction selon le format"""
    if format_ext in TEXT_FORMATS:
        return create_text_file(content, filepath, format_ext)
    else:
        return create_document_from_content(content, content_type, filepath, format_ext)

# ===== SECTION #8_LOGIQUE_PRINCIPALE =====
def main() -> None:
    if len(sys.argv) < 2:
        exit(1)
    
    directory = sys.argv[1].replace("\\ ", " ")
    
    # Récupérer d'abord le contenu du presse-papiers (avec texte extrait pour le nom)
    content_preview, content_type_preview = get_clipboard_content(preserve_html=False)
    
    if not content_preview:
        show_message(NO_CLIPBOARD_CONTENT, Gtk.MessageType.WARNING)
        exit(1)
    
    # Générer un nom par défaut basé sur le contenu
    default_name = guess_default_filename(content_preview, content_type_preview)
    if not default_name:
        default_name = "new_document"
    
    # Demander nom et format avec le vrai nom par défaut
    filename, format_ext = get_file_name_and_format(default_name)
    
    if not filename or filename.strip() == "":
        exit(1)
    
    # Récupérer le contenu à nouveau avec le bon paramètre HTML selon le format choisi
    preserve_html = (format_ext == "html")
    content, content_type = get_clipboard_content(preserve_html=preserve_html)
    
    if not content:
        show_message(NO_CLIPBOARD_CONTENT, Gtk.MessageType.WARNING)
        exit(1)
    
    filename = filename.strip()
    
    # Ajouter extension si pas déjà présente
    if not filename.lower().endswith(f'.{format_ext}'):
        filename = f"{filename}.{format_ext}"
    
    filepath = os.path.join(directory, filename)
    
    # Vérifier validité
    if os.path.isdir(filepath):
        show_message(INVALID_FILE_NAME, Gtk.MessageType.ERROR)
        exit(1)
    
    # Confirmation si existe
    if os.path.exists(filepath):
        if not ask_yes_no(FILE_EXISTS_MESSAGE % filename):
            exit(1)
    
    # Créer document
    success = create_document_dispatch(content, content_type, filepath, format_ext)
    
    if not success:
        show_message(ERROR_MESSAGE, Gtk.MessageType.ERROR)
        exit(1)
    
    exit(0)


if __name__ == "__main__":
    main()
