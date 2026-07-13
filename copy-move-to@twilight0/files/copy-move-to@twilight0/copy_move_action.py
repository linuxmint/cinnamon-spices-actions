#!/usr/bin/env python3
import sys
import os
import shutil
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

def get_last_location(op):
    config_file = os.path.expanduser(f"~/.config/dory/last_{op}_location.txt")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                path = f.read().strip()
                if os.path.isdir(path):
                    return path
        except Exception:
            pass
    return os.path.expanduser("~")

def save_last_location(op, path):
    config_dir = os.path.expanduser("~/.config/dory")
    os.makedirs(config_dir, exist_ok=True)
    config_file = os.path.join(config_dir, f"last_{op}_location.txt")
    try:
        with open(config_file, "w") as f:
            f.write(path)
    except Exception:
        pass

class ProgressWindow(Gtk.Window):
    def __init__(self, op, sources, dest):
        super().__init__(title="File Operation")
        self.op = op
        self.sources = sources
        self.dest = dest
        self.error_msg = None
        
        self.set_default_size(400, 120)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(15)
        self.set_keep_above(True)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)
        
        operation_text = "Copying" if op == "copy" else "Moving"
        self.label = Gtk.Label(label=f"{operation_text} {len(sources)} items...")
        self.label.set_alignment(0, 0.5)
        vbox.pack_start(self.label, False, False, 0)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        vbox.pack_start(hbox, False, False, 0)
        
        self.spinner = Gtk.Spinner()
        hbox.pack_start(self.spinner, False, False, 0)
        self.spinner.start()
        
        self.progress_bar = Gtk.ProgressBar()
        hbox.pack_start(self.progress_bar, True, True, 0)
        
        self.show_all()
        
        self.pulse_id = GLib.timeout_add(100, self.pulse_progress)
        
        self.thread = threading.Thread(target=self.run_operation)
        self.thread.daemon = True
        self.thread.start()
        
    def pulse_progress(self):
        self.progress_bar.pulse()
        return True
        
    def run_operation(self):
        try:
            for src in self.sources:
                if not os.path.exists(src):
                    continue
                basename = os.path.basename(src)
                target = os.path.join(self.dest, basename)
                
                # Suffix renaming if target exists
                if os.path.exists(target):
                    root, ext = os.path.splitext(basename)
                    counter = 1
                    while os.path.exists(target):
                        target = os.path.join(self.dest, f"{root} ({counter}){ext}")
                        counter += 1
                
                if self.op == "copy":
                    if os.path.isdir(src):
                        shutil.copytree(src, target)
                    else:
                        shutil.copy2(src, target)
                else:
                    shutil.move(src, target)
        except Exception as e:
            self.error_msg = str(e)
            
        GLib.idle_add(self.on_finished)
        
    def on_finished(self):
        GLib.source_remove(self.pulse_id)
        self.spinner.stop()
        self.destroy()
        
        if self.error_msg:
            err_dialog = Gtk.MessageDialog(
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                message_format=f"Error during {self.op} operation:\n{self.error_msg}"
            )
            err_dialog.run()
            err_dialog.destroy()
        
        Gtk.main_quit()

def main():
    if len(sys.argv) < 3:
        print("Usage: copy_move_action.py <copy|move> <file1> [file2 ...]")
        sys.exit(1)
        
    op = sys.argv[1]
    sources = sys.argv[2:]
    
    Gtk.init(None)
    
    last_dir = get_last_location(op)
    
    title = "Copy To..." if op == "copy" else "Move To..."
    action = Gtk.FileChooserAction.SELECT_FOLDER
    
    # Use FileChooserNative to follow modern desktop portal standards and avoid deprecated widgets
    dialog = Gtk.FileChooserNative.new(
        title=title,
        parent=None,
        action=action,
        accept_label="_Select",
        cancel_label="_Cancel"
    )
    dialog.set_current_folder(last_dir)
    dialog.set_modal(True)
    
    response = dialog.run()
    dest = dialog.get_filename()
    dialog.destroy()
    
    if response == Gtk.ResponseType.ACCEPT and dest:
        save_last_location(op, dest)
        ProgressWindow(op, sources, dest)
        Gtk.main()

if __name__ == "__main__":
    main()
