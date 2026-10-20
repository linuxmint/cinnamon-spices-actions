"""The "Add to Archive" dialog: a WinRAR-style window whose per-format
options grey out based on what the selected archiver actually supports.

Python/PyGObject port of ../archive_action_c/src/ui.c -- same tabbed
layout, same capability-driven sensitivity rules, same argv-building
logic, translated close to 1:1.
"""

import builtins
import os
import tempfile
import time

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

import archivers
import execute
import pathutil

_ = getattr(builtins, "_", lambda s: s)


def _strip_last_extension(name):
    return pathutil.strip_last_extension(name)


def _default_base_name(files, parent):
    if len(files) == 1:
        return pathutil.strip_last_extension(os.path.basename(files[0]))
    return os.path.basename(parent)


def _error_dialog(parent, msg, secondary=None):
    dialog = Gtk.MessageDialog(
        transient_for=parent, modal=True,
        message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
        text=msg)
    if secondary:
        dialog.format_secondary_text(secondary)
    dialog.run()
    dialog.destroy()


# ---------- date/time widget helpers ----------

def _labeled_spin(box, label, lo, hi):
    box.pack_start(Gtk.Label(label=label), False, False, 0)
    spin = Gtk.SpinButton.new_with_range(lo, hi, 1)
    spin.set_size_request(62, -1)
    box.pack_start(spin, False, False, 0)
    return spin


def _build_datetime_picker():
    """A GtkCalendar plus H/M/S spinners, for picking an absolute date+time.
    Returns (box, calendar, hour_spin, min_spin, sec_spin)."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    calendar = Gtk.Calendar()
    box.pack_start(calendar, False, False, 0)

    time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    h = _labeled_spin(time_box, "H:", 0, 23)
    m = _labeled_spin(time_box, "M:", 0, 59)
    s = _labeled_spin(time_box, "S:", 0, 59)
    box.pack_start(time_box, False, False, 0)

    return box, calendar, h, m, s


def _build_relative_duration():
    """Y/Mo/D/H/Mi/S spinners for a relative "older/newer than" duration.
    Returns (box, year, month, day, hour, minute, second)."""
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    y = _labeled_spin(box, "Y:", 0, 100)
    mo = _labeled_spin(box, "Mo:", 0, 11)
    d = _labeled_spin(box, "D:", 0, 30)
    h = _labeled_spin(box, "H:", 0, 23)
    mi = _labeled_spin(box, "Mi:", 0, 59)
    s = _labeled_spin(box, "S:", 0, 59)
    return box, y, mo, d, h, mi, s


def _relative_duration_seconds(spins):
    y, mo, d, h, mi, s = spins
    return (y.get_value() * 365.25 * 86400.0 +
            mo.get_value() * 30.44 * 86400.0 +
            d.get_value() * 86400.0 +
            h.get_value() * 3600.0 +
            mi.get_value() * 60.0 +
            s.get_value())


def _calendar_to_epoch(calendar, h, m, s):
    year, month, day = calendar.get_date()  # GTK3: month is 0-indexed
    dt = GLib.DateTime.new_local(year, month + 1, day,
                                  int(h.get_value()), int(m.get_value()), s.get_value())
    return float(dt.to_unix())


# ---------- compression flag mapping ----------

_COMPRESSION_FLAGS = {
    archivers.FMT_7Z: ["-mx0", "-mx1", "-mx3", "-mx5", "-mx7", "-mx9"],
    archivers.FMT_ZIP: ["-0", "-1", "-3", "-6", "-8", "-9"],
    archivers.FMT_RAR: ["-m0", "-m1", "-m2", "-m3", "-m4", "-m5"],
}


def _compression_flag(fmt_id, level):
    return _COMPRESSION_FLAGS.get(fmt_id, _COMPRESSION_FLAGS[archivers.FMT_7Z])[level]


# Which stdout format (see execute.py) each format's "create" batches
# will produce, given the flags the _build_*_job methods add (-bb1 for
# 7z, -v for tar/cpio; zip/rar/arj/arc/lha/shar all show this by default).
_LINE_PARSERS = {
    archivers.FMT_7Z: execute.LINE_PARSER_7Z,
    archivers.FMT_ZIP: execute.LINE_PARSER_ZIP,
    archivers.FMT_TAR: execute.LINE_PARSER_TAR,
    archivers.FMT_TAR_GZ: execute.LINE_PARSER_TAR,
    archivers.FMT_TAR_BZ2: execute.LINE_PARSER_TAR,
    archivers.FMT_TAR_XZ: execute.LINE_PARSER_TAR,
    archivers.FMT_TAR_ZST: execute.LINE_PARSER_TAR,
    archivers.FMT_TAR_LZ: execute.LINE_PARSER_TAR,
    archivers.FMT_TAR_LZO: execute.LINE_PARSER_TAR,
    archivers.FMT_TAR_Z: execute.LINE_PARSER_TAR,
    archivers.FMT_TAR_LZ4: execute.LINE_PARSER_TAR,
    archivers.FMT_RAR: execute.LINE_PARSER_RAR_ARJ,
    archivers.FMT_ARJ: execute.LINE_PARSER_RAR_ARJ,
    archivers.FMT_CPIO: execute.LINE_PARSER_CPIO,
    archivers.FMT_ARC: execute.LINE_PARSER_ARC,
    archivers.FMT_LHA: execute.LINE_PARSER_LHA,
    archivers.FMT_SHAR: execute.LINE_PARSER_SHAR,
}


# A very large selection is split into batches of this many files, each
# added to the archive as its own run of the archiver (see ArchiveWindow.
# _batches() and execute.ArchiveJob), so a single command line never has
# to hold an unbounded number of arguments.
BATCH_SIZE = 1000

# Extension a tar --use-compress-program binary appends when compressing
# a file in place (all of them keep this convention except lz4, handled
# separately in _build_compressed_tar_job).
_COMPRESSED_SUFFIXES = {
    "gzip": ".gz", "pigz": ".gz",
    "bzip2": ".bz2", "pbzip2": ".bz2", "lbzip2": ".bz2",
    "xz": ".xz",
    "zstd": ".zst",
    "lzip": ".lz", "plzip": ".lz",
    "lzop": ".lzo",
    "compress": ".Z",
    "lz4": ".lz4",
}


class ArchiveWindow:
    def __init__(self, files):
        self.files = files
        self.common_parent = pathutil.common_parent_dir(files)
        self.formats = archivers.detect()
        self.caps = 0
        self.current_format = None
        self.last_extension = None
        self.transferring = False

        self.window = Gtk.Window(title=_("Add to Archive"))
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_resizable(False)
        self.window.set_border_width(8)
        self.window.connect("destroy", self._on_window_destroy)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.window.add(outer)

        self.notebook = Gtk.Notebook()
        outer.pack_start(self.notebook, True, True, 0)

        self.notebook.append_page(self._build_general_tab(), Gtk.Label(label=_("General")))
        self.notebook.append_page(self._build_options_tab(), Gtk.Label(label=_("Options")))
        self.notebook.append_page(self._build_files_tab(), Gtk.Label(label=_("Files")))
        self.notebook.append_page(self._build_time_tab(), Gtk.Label(label=_("Time")))
        self.notebook.append_page(self._build_comment_tab(), Gtk.Label(label=_("Comment")))

        btn_box = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        btn_box.set_layout(Gtk.ButtonBoxStyle.END)
        btn_box.set_spacing(6)
        cancel_btn = Gtk.Button(label=_("Cancel"))
        create_btn = Gtk.Button(label=_("Create Archive"))
        create_btn.get_style_context().add_class("suggested-action")
        btn_box.add(cancel_btn)
        btn_box.add(create_btn)
        outer.pack_start(btn_box, False, False, 0)

        self.format_combo.connect("changed", self._on_format_changed)
        self.cb_encrypt.connect("toggled", self._on_encrypt_toggled)
        self.cb_header_enc.connect("toggled", self._on_encrypt_toggled)
        self.cb_recovery.connect("toggled", self._on_recovery_toggled)
        self.cb_split.connect("toggled", self._on_split_toggled)
        self.cb_comment.connect("toggled", self._on_comment_toggled)
        self.comment_source_combo.connect("changed", self._on_comment_source_changed)
        self.cb_date_filter.connect("toggled", self._on_date_filter_toggled)
        self.date_cond_combo.connect("changed", self._on_date_cond_changed)
        self.archive_time_combo.connect("changed", self._on_archive_time_changed)
        self.show_password_btn.connect("toggled", self._on_show_password_toggled)
        cancel_btn.connect("clicked", lambda *_a: self.window.destroy())
        create_btn.connect("clicked", self._on_create_clicked)

        # Initial state: seed the name (no extension yet -- the format
        # combo's "changed" signal below appends it), then pick the
        # first available format.
        base = _default_base_name(files, self.common_parent)
        self.archive_name_entry.set_text(os.path.join(self.common_parent, base))
        self.format_combo.set_active(0)

        self.window.show_all()

        # GtkNotebook refuses to switch to a page whose child isn't visible
        # yet, so this only takes effect once show_all() above has run --
        # done any earlier, it silently no-ops and GTK falls back to the
        # last page once everything becomes visible. show_all() also makes
        # every widget visible unconditionally, clobbering any hide done
        # during construction -- so the conditionally-hidden sections need
        # to be re-applied afterwards too.
        self.notebook.set_current_page(0)
        self._update_comment_sensitivity()
        self._update_date_filter_sensitivity()
        self._update_archive_time_sensitivity()

    # ---------- tab construction ----------

    def _new_tab_grid(self):
        grid = Gtk.Grid(row_spacing=8, column_spacing=8)
        grid.set_border_width(10)
        return grid

    def _build_general_tab(self):
        grid = self._new_tab_grid()
        row = 0

        grid.attach(Gtk.Label(label=_("Archive name:"), xalign=0), 0, row, 1, 1)
        self.archive_name_entry = Gtk.Entry(hexpand=True)
        grid.attach(self.archive_name_entry, 1, row, 3, 1)
        row += 1

        grid.attach(Gtk.Label(label=_("Archive format:"), xalign=0), 0, row, 1, 1)
        self.format_combo = Gtk.ComboBoxText()
        for fmt_id in archivers.FORMAT_ORDER:
            fmt = self.formats[fmt_id]
            if fmt.available:
                self.format_combo.append(fmt.extension, fmt.label)
        grid.attach(self.format_combo, 1, row, 1, 1)
        row += 1

        grid.attach(Gtk.Label(label=_("Compression method:"), xalign=0), 0, row, 1, 1)
        self.compression_combo = Gtk.ComboBoxText()
        for idx, label in enumerate([_("Store"), _("Fastest"), _("Fast"), _("Normal"), _("Good"), _("Best")]):
            self.compression_combo.append(str(idx), label)
        self.compression_combo.set_active(archivers.COMPRESS_NORMAL)
        grid.attach(self.compression_combo, 1, row, 1, 1)

        grid.attach(Gtk.Label(label=_("Dictionary size:"), xalign=0), 2, row, 1, 1)
        self.dict_size_combo = Gtk.ComboBoxText()
        for value, label in [("32m", "32 MiB"), ("64m", "64 MiB"), ("128m", "128 MiB"),
                              ("256m", "256 MiB"), ("512m", "512 MiB"), ("1g", "1 GiB")]:
            self.dict_size_combo.append(value, label)
        self.dict_size_combo.set_active(1)
        grid.attach(self.dict_size_combo, 3, row, 1, 1)
        row += 1

        self.cb_split = Gtk.CheckButton(label=_("Split into volumes, size:"))
        grid.attach(self.cb_split, 0, row, 1, 1)
        self.split_spin = Gtk.SpinButton.new_with_range(1, 999999, 1)
        self.split_spin.set_value(100)
        grid.attach(self.split_spin, 1, row, 1, 1)
        self.split_unit_combo = Gtk.ComboBoxText()
        for value, label in [("k", "KiB"), ("m", "MiB"), ("g", "GiB")]:
            self.split_unit_combo.append(value, label)
        self.split_unit_combo.set_active(1)
        grid.attach(self.split_unit_combo, 2, row, 1, 1)
        row += 1

        self.cb_encrypt = Gtk.CheckButton(label=_("Encrypt"))
        grid.attach(self.cb_encrypt, 0, row, 1, 1)
        self.cb_header_enc = Gtk.CheckButton(label=_("Encrypt file names"))
        grid.attach(self.cb_header_enc, 1, row, 2, 1)
        row += 1

        grid.attach(Gtk.Label(label=_("Password:"), xalign=0), 0, row, 1, 1)
        self.password_entry = Gtk.Entry(visibility=False)
        grid.attach(self.password_entry, 1, row, 1, 1)
        grid.attach(Gtk.Label(label=_("Confirm:"), xalign=0), 2, row, 1, 1)
        self.confirm_entry = Gtk.Entry(visibility=False)
        grid.attach(self.confirm_entry, 3, row, 1, 1)
        row += 1

        self.show_password_btn = Gtk.ToggleButton(label=_("Show password"))
        grid.attach(self.show_password_btn, 1, row, 2, 1)

        return grid

    def _build_options_tab(self):
        grid = self._new_tab_grid()
        row = 0

        self.cb_sfx = Gtk.CheckButton(label=_("Create self-extracting archive (SFX)"))
        grid.attach(self.cb_sfx, 0, row, 2, 1)
        self.cb_test = Gtk.CheckButton(label=_("Test archive after creation"))
        grid.attach(self.cb_test, 2, row, 2, 1)
        row += 1

        self.cb_recovery = Gtk.CheckButton(label=_("Add recovery record, %:"))
        grid.attach(self.cb_recovery, 0, row, 1, 1)
        self.recovery_spin = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.recovery_spin.set_value(5)
        grid.attach(self.recovery_spin, 1, row, 1, 1)
        row += 1

        self.cb_dedup_refs = Gtk.CheckButton(label=_("Save identical files as references"))
        grid.attach(self.cb_dedup_refs, 0, row, 3, 1)
        row += 1

        self.cb_delete_after = Gtk.CheckButton(label=_("Delete files after archiving"))
        grid.attach(self.cb_delete_after, 0, row, 3, 1)

        return grid

    def _build_files_tab(self):
        grid = self._new_tab_grid()
        row = 0

        self.cb_date_filter = Gtk.CheckButton(label=_("Include files by date"))
        grid.attach(self.cb_date_filter, 0, row, 4, 1)
        row += 1

        grid.attach(Gtk.Label(label=_("Time:"), xalign=0), 0, row, 1, 1)
        self.date_field_combo = Gtk.ComboBoxText()
        for value, label in [(pathutil.TIME_FIELD_MODIFICATION, _("Modification time")),
                              (pathutil.TIME_FIELD_CREATION, _("Creation time")),
                              (pathutil.TIME_FIELD_ACCESS, _("Access time")),
                              (pathutil.TIME_FIELD_ANY, _("Any time"))]:
            self.date_field_combo.append(value, label)
        self.date_field_combo.set_active(0)
        grid.attach(self.date_field_combo, 1, row, 1, 1)

        grid.attach(Gtk.Label(label=_("Condition:"), xalign=0), 2, row, 1, 1)
        self.date_cond_combo = Gtk.ComboBoxText()
        for value, label in [(pathutil.DATE_COND_OLDER, _("Older than")),
                              (pathutil.DATE_COND_NEWER, _("Newer than")),
                              (pathutil.DATE_COND_BEFORE, _("Before")),
                              (pathutil.DATE_COND_AFTER, _("After"))]:
            self.date_cond_combo.append(value, label)
        self.date_cond_combo.set_active(0)
        grid.attach(self.date_cond_combo, 3, row, 1, 1)
        row += 1

        (self.date_relative_box, self.date_rel_years, self.date_rel_months, self.date_rel_days,
         self.date_rel_hours, self.date_rel_mins, self.date_rel_secs) = _build_relative_duration()
        grid.attach(self.date_relative_box, 0, row, 4, 1)

        (self.date_absolute_box, self.date_calendar,
         self.date_abs_hours, self.date_abs_mins, self.date_abs_secs) = _build_datetime_picker()
        grid.attach(self.date_absolute_box, 0, row, 4, 1)

        return grid

    def _build_time_tab(self):
        grid = self._new_tab_grid()
        row = 0

        grid.attach(Gtk.Label(label=_("Set archive time to:"), xalign=0), 0, row, 1, 1)
        self.archive_time_combo = Gtk.ComboBoxText()
        for value, label in [("current", _("Current system time")),
                              ("original", _("Original archive time")),
                              ("latest", _("Latest file time")),
                              ("specified", _("Specified time"))]:
            self.archive_time_combo.append(value, label)
        self.archive_time_combo.set_active(0)
        grid.attach(self.archive_time_combo, 1, row, 2, 1)
        row += 1

        (self.archive_time_box, self.archive_time_calendar, self.archive_time_hours,
         self.archive_time_mins, self.archive_time_secs) = _build_datetime_picker()
        grid.attach(self.archive_time_box, 0, row, 4, 1)
        row += 1

        self.cb_store_mtime = Gtk.CheckButton(label=_("Store modification time"))
        grid.attach(self.cb_store_mtime, 0, row, 2, 1)
        self.cb_store_ctime = Gtk.CheckButton(label=_("Store creation time"))
        grid.attach(self.cb_store_ctime, 2, row, 2, 1)
        row += 1

        self.cb_store_atime = Gtk.CheckButton(label=_("Store access time"))
        grid.attach(self.cb_store_atime, 0, row, 2, 1)
        self.cb_preserve_atime = Gtk.CheckButton(label=_("Preserve source files' access time"))
        grid.attach(self.cb_preserve_atime, 2, row, 2, 1)
        row += 1

        self.cb_high_precision = Gtk.CheckButton(label=_("High precision time format"))
        grid.attach(self.cb_high_precision, 0, row, 2, 1)

        return grid

    def _build_comment_tab(self):
        grid = self._new_tab_grid()
        row = 0

        self.cb_comment = Gtk.CheckButton(label=_("Add comment"))
        grid.attach(self.cb_comment, 0, row, 1, 1)
        self.comment_source_combo = Gtk.ComboBoxText()
        self.comment_source_combo.append("text", _("Text"))
        self.comment_source_combo.append("file", _("From file"))
        self.comment_source_combo.set_active(0)
        grid.attach(self.comment_source_combo, 1, row, 1, 1)
        row += 1

        self.comment_text_view = Gtk.TextView()
        self.comment_text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.comment_text_scroll = Gtk.ScrolledWindow()
        self.comment_text_scroll.set_size_request(-1, 120)
        self.comment_text_scroll.add(self.comment_text_view)
        grid.attach(self.comment_text_scroll, 0, row, 4, 1)

        self.comment_file_chooser = Gtk.FileChooserButton(
            title=_("Select a comment file"), action=Gtk.FileChooserAction.OPEN)
        grid.attach(self.comment_file_chooser, 0, row, 4, 1)

        return grid

    # ---------- capability-driven sensitivity ----------

    def _update_password_sensitivity(self):
        encrypt_on = bool(self.caps & archivers.CAP_ENCRYPT) and self.cb_encrypt.get_active()
        self.password_entry.set_sensitive(encrypt_on)
        self.confirm_entry.set_sensitive(encrypt_on)
        self.show_password_btn.set_sensitive(encrypt_on)

        header_on = bool(self.caps & archivers.CAP_HEADER_ENC) and encrypt_on
        self.cb_header_enc.set_sensitive(header_on)
        if not header_on:
            self.cb_header_enc.set_active(False)

    def _update_recovery_sensitivity(self):
        on = bool(self.caps & archivers.CAP_RECOVERY) and self.cb_recovery.get_active()
        self.recovery_spin.set_sensitive(on)

    def _update_split_sensitivity(self):
        on = bool(self.caps & archivers.CAP_SPLIT) and self.cb_split.get_active()
        self.split_spin.set_sensitive(on)
        self.split_unit_combo.set_sensitive(on)

    def _update_comment_sensitivity(self):
        on = bool(self.caps & archivers.CAP_COMMENT) and self.cb_comment.get_active()
        self.comment_source_combo.set_sensitive(on)

        from_file = self.comment_source_combo.get_active_id() == "file"
        self.comment_file_chooser.set_visible(from_file)
        self.comment_text_scroll.set_visible(not from_file)
        self.comment_file_chooser.set_sensitive(on)
        self.comment_text_view.set_sensitive(on)

    def _update_date_filter_sensitivity(self):
        on = self.cb_date_filter.get_active()
        self.date_field_combo.set_sensitive(on)
        self.date_cond_combo.set_sensitive(on)
        self.date_relative_box.set_sensitive(on)
        self.date_absolute_box.set_sensitive(on)

        cond = self.date_cond_combo.get_active_id()
        relative = cond in (pathutil.DATE_COND_OLDER, pathutil.DATE_COND_NEWER)
        self.date_relative_box.set_visible(relative)
        self.date_absolute_box.set_visible(not relative)

    def _update_archive_time_sensitivity(self):
        mode = self.archive_time_combo.get_active_id()
        self.archive_time_box.set_visible(mode == "specified")

    def _apply_capabilities(self, caps):
        self.caps = caps

        self.cb_encrypt.set_sensitive(bool(caps & archivers.CAP_ENCRYPT))
        if not (caps & archivers.CAP_ENCRYPT):
            self.cb_encrypt.set_active(False)

        self.cb_sfx.set_sensitive(bool(caps & archivers.CAP_SFX))
        if not (caps & archivers.CAP_SFX):
            self.cb_sfx.set_active(False)

        self.cb_recovery.set_sensitive(bool(caps & archivers.CAP_RECOVERY))
        if not (caps & archivers.CAP_RECOVERY):
            self.cb_recovery.set_active(False)

        self.cb_split.set_sensitive(bool(caps & archivers.CAP_SPLIT))
        if not (caps & archivers.CAP_SPLIT):
            self.cb_split.set_active(False)

        can_test = bool(caps & (archivers.CAP_TEST | archivers.CAP_TEST_INLINE))
        self.cb_test.set_sensitive(can_test)
        if not can_test:
            self.cb_test.set_active(False)

        self.compression_combo.set_sensitive(bool(caps & archivers.CAP_COMPRESSION))
        self.dict_size_combo.set_sensitive(bool(caps & archivers.CAP_DICT_SIZE))

        self.cb_dedup_refs.set_sensitive(bool(caps & archivers.CAP_DEDUP_REFS))
        if not (caps & archivers.CAP_DEDUP_REFS):
            self.cb_dedup_refs.set_active(False)

        for cb, cap in ((self.cb_store_mtime, archivers.CAP_STORE_MTIME),
                        (self.cb_store_ctime, archivers.CAP_STORE_CTIME),
                        (self.cb_store_atime, archivers.CAP_STORE_ATIME),
                        (self.cb_preserve_atime, archivers.CAP_PRESERVE_ATIME),
                        (self.cb_high_precision, archivers.CAP_HIGH_PRECISION_TIME)):
            cb.set_sensitive(bool(caps & cap))
            if not (caps & cap):
                cb.set_active(False)

        self.cb_comment.set_sensitive(bool(caps & archivers.CAP_COMMENT))
        if not (caps & archivers.CAP_COMMENT):
            self.cb_comment.set_active(False)

        self._update_password_sensitivity()
        self._update_recovery_sensitivity()
        self._update_split_sensitivity()
        self._update_comment_sensitivity()

    def _set_archive_extension(self, new_ext):
        base = self.archive_name_entry.get_text()
        if self.last_extension:
            suffix = "." + self.last_extension
            if base.endswith(suffix):
                base = base[:-len(suffix)]
        self.archive_name_entry.set_text(f"{base}.{new_ext}")
        self.last_extension = new_ext

    # ---------- signal handlers ----------

    def _on_format_changed(self, combo):
        ext = combo.get_active_id()
        if not ext:
            return
        fmt = next(f for f in self.formats.values() if f.extension == ext)
        self.current_format = fmt.id
        self._set_archive_extension(fmt.extension)
        self._apply_capabilities(fmt.capabilities)

    def _on_encrypt_toggled(self, _btn):
        self._update_password_sensitivity()

    def _on_recovery_toggled(self, _btn):
        self._update_recovery_sensitivity()

    def _on_split_toggled(self, _btn):
        self._update_split_sensitivity()

    def _on_comment_toggled(self, _btn):
        self._update_comment_sensitivity()

    def _on_comment_source_changed(self, _combo):
        self._update_comment_sensitivity()

    def _on_date_filter_toggled(self, _btn):
        self._update_date_filter_sensitivity()

    def _on_date_cond_changed(self, _combo):
        self._update_date_filter_sensitivity()

    def _on_archive_time_changed(self, _combo):
        self._update_archive_time_sensitivity()

    def _on_show_password_toggled(self, btn):
        show = btn.get_active()
        self.password_entry.set_visibility(show)
        self.confirm_entry.set_visibility(show)

    def _on_window_destroy(self, *_a):
        if not self.transferring:
            Gtk.main_quit()

    # ---------- argv building ----------

    def _comment_text(self):
        buf = self.comment_text_view.get_buffer()
        start, end = buf.get_bounds()
        return buf.get_text(start, end, False)

    def _batches(self, files):
        """Yields (batch_files, is_first, is_last) chunks of at most
        BATCH_SIZE files -- always at least one chunk, even for an
        empty list, so callers can rely on the loop running once."""
        n = len(files)
        n_batches = max(1, (n + BATCH_SIZE - 1) // BATCH_SIZE)
        for b in range(n_batches):
            start = b * BATCH_SIZE
            chunk = files[start:start + BATCH_SIZE]
            yield chunk, b == 0, b == n_batches - 1

    def _build_7z_or_rar_batch(self, job, fmt, archive_path, password, batch_files, is_last_batch):
        job.start_batch()
        job.add_arg(fmt.bin)
        job.add_arg("a")
        if fmt.id == archivers.FMT_7Z:
            job.add_arg("-bb1")  # per-file "+ name" lines, for progress/the log

        if self.compression_combo.get_sensitive():
            level = int(self.compression_combo.get_active_id())
            job.add_arg(_compression_flag(fmt.id, level))

        if self.dict_size_combo.get_sensitive():
            size = self.dict_size_combo.get_active_id()
            if fmt.id == archivers.FMT_RAR:
                job.add_arg(f"-md{size}")
            else:
                job.add_arg(f"-m0=lzma2:d={size}")

        if self.cb_sfx.get_active():
            job.add_arg("-sfx")

        if self.cb_recovery.get_active():
            job.add_arg(f"-rr{self.recovery_spin.get_value_as_int()}%")

        if self.cb_split.get_active():
            size = self.split_spin.get_value_as_int()
            unit = self.split_unit_combo.get_active_id() or "m"
            job.add_arg(f"-v{size}{unit}")

        if self.cb_dedup_refs.get_active():
            job.add_arg("-oi" if fmt.id == archivers.FMT_RAR else "-snh")

        if fmt.id == archivers.FMT_RAR:
            if self.cb_store_mtime.get_active():
                job.add_arg("-tsm")
            if self.cb_store_ctime.get_active():
                job.add_arg("-tsc")
            if self.cb_store_atime.get_active():
                job.add_arg("-tsa")
            if self.cb_high_precision.get_active():
                job.add_arg("-ma5")
        if self.cb_preserve_atime.get_active():
            job.add_arg("-tsp" if fmt.id == archivers.FMT_RAR else "-ssp")

        encrypt = self.cb_encrypt.get_active()
        header_enc = self.cb_header_enc.get_active()

        if encrypt:
            if fmt.id == archivers.FMT_RAR:
                job.add_arg(("-hp" if header_enc else "-p") + password)
            else:
                if header_enc:
                    job.add_arg("-mhe=on")
                job.add_arg("-p" + password)

        if (is_last_batch and self.cb_comment.get_active() and
                self.cb_comment.get_sensitive() and fmt.id == archivers.FMT_RAR):
            if self.comment_source_combo.get_active_id() == "file":
                comment_path = self.comment_file_chooser.get_filename()
            else:
                fd, comment_path = tempfile.mkstemp(prefix="archive_comment_")
                with os.fdopen(fd, "w") as f:
                    f.write(self._comment_text())
            if comment_path:
                job.add_arg(f"-z{comment_path}")

        job.add_arg(archive_path)
        for f in batch_files:
            job.add_arg(pathutil.relative_to(f, self.common_parent))

    def _build_7z_or_rar_job(self, job, fmt, archive_path, password):
        for batch_files, _first, last in self._batches(self.effective_files):
            self._build_7z_or_rar_batch(job, fmt, archive_path, password, batch_files, last)

        if self.cb_test.get_active():
            job.add_test_arg(fmt.bin)
            job.add_test_arg("t")
            job.add_test_arg(archive_path)

    def _build_zip_batch(self, job, archive_path, password, batch_files, is_last_batch):
        job.start_batch()
        job.add_arg("zip")
        job.add_arg("-r")

        if self.compression_combo.get_sensitive():
            level = int(self.compression_combo.get_active_id())
            job.add_arg(_compression_flag(archivers.FMT_ZIP, level))

        if is_last_batch and self.cb_test.get_active():
            job.add_arg("-T")

        if self.cb_split.get_active():
            job.add_arg("-s")
            size = self.split_spin.get_value_as_int()
            unit = self.split_unit_combo.get_active_id() or "m"
            job.add_arg(f"{size}{unit}")

        if self.cb_encrypt.get_active():
            job.add_arg("-P" + password)

        if is_last_batch and self.cb_comment.get_active() and self.cb_comment.get_sensitive():
            if self.comment_source_combo.get_active_id() == "file":
                path = self.comment_file_chooser.get_filename()
                text = None
                if path:
                    with open(path, "r", errors="replace") as f:
                        text = f.read()
            else:
                text = self._comment_text()
            if text:
                job.add_arg("-z")
                job.set_stdin_text(text)

        job.add_arg(archive_path)
        for f in batch_files:
            job.add_arg(pathutil.relative_to(f, self.common_parent))

    def _build_zip_job(self, job, archive_path, password):
        for batch_files, _first, last in self._batches(self.effective_files):
            self._build_zip_batch(job, archive_path, password, batch_files, last)

    def _build_plain_tar_job(self, job, archive_path):
        """Plain (uncompressed) tar: native append via -rf, so each batch
        just writes straight to archive_path."""
        exists = os.path.exists(archive_path)
        for batch_files, is_first, _last in self._batches(self.effective_files):
            job.start_batch()
            job.add_arg("tar")
            job.add_arg("-v")  # one filename per line, for progress/the log
            job.add_arg("-rf" if (exists or not is_first) else "-cf")
            job.add_arg(archive_path)
            for f in batch_files:
                job.add_arg(pathutil.relative_to(f, self.common_parent))

    def _build_compressed_tar_job(self, job, fmt, archive_path):
        """Compressed tar can't be appended to in place, so a batched run
        builds an uncompressed temp .tar the same way plain tar does,
        then compresses it in place and renames the result over
        archive_path as a final step. A selection small enough for one
        batch skips all that and uses the simpler, single-shot
        --use-compress-program call."""
        batches = list(self._batches(self.effective_files))

        if len(batches) == 1:
            job.start_batch()
            job.add_arg("tar")
            job.add_arg("-v")
            job.add_arg(f"--use-compress-program={fmt.compress_program}")
            job.add_arg("-cf")
            job.add_arg(archive_path)
            for f in self.effective_files:
                job.add_arg(pathutil.relative_to(f, self.common_parent))
            return

        temp_tar = f"{archive_path}.tmp_batching.tar"
        for batch_files, is_first, _last in batches:
            job.start_batch()
            job.add_arg("tar")
            job.add_arg("-v")
            job.add_arg("-cf" if is_first else "-rf")
            job.add_arg(temp_tar)
            for f in batch_files:
                job.add_arg(pathutil.relative_to(f, self.common_parent))

        # The compress-in-place batch about to be appended doesn't add any
        # files itself, so "Work in background" should stop being offered
        # once the last of the batches above (the real file-adding ones)
        # finishes, not after this one too.
        job.set_last_file_batch(len(batches) - 1)

        suffix = _COMPRESSED_SUFFIXES.get(fmt.compress_program, "")
        compressed_name = f"{temp_tar}{suffix}"

        job.start_batch()
        if fmt.compress_program == "lz4":
            # lz4 defaults to writing to stdout rather than compressing a
            # named file in place like every other compressor here.
            job.add_arg("lz4")
            job.add_arg("-z")
            job.add_arg(temp_tar)
            job.add_arg(compressed_name)
        else:
            job.add_arg(fmt.compress_program)
            job.add_arg(temp_tar)

        job.set_rename_after(compressed_name, archive_path)

    def _build_tar_job(self, job, fmt, archive_path):
        if fmt.compress_program:
            self._build_compressed_tar_job(job, fmt, archive_path)
        else:
            self._build_plain_tar_job(job, archive_path)

    def _build_simple_add_batch(self, job, fmt, archive_path, password, batch_files):
        job.start_batch()
        job.add_arg(fmt.bin)
        job.add_arg("a")

        if fmt.id == archivers.FMT_ARJ:
            if self.cb_sfx.get_active():
                job.add_arg("-je")
            if self.cb_encrypt.get_active():
                job.add_arg(f"-g{password}")

        job.add_arg(archive_path)
        for f in batch_files:
            job.add_arg(pathutil.relative_to(f, self.common_parent))

    def _build_simple_add_job(self, job, fmt, archive_path, password):
        for batch_files, _first, _last in self._batches(self.effective_files):
            self._build_simple_add_batch(job, fmt, archive_path, password, batch_files)

    def _build_cpio_job(self, job, archive_path):
        # cpio reads its filename list from stdin, so it's immune to the
        # argv-size problem batching solves for every other format -- one
        # call handles any selection size.
        job.start_batch()
        job.add_arg("cpio")
        job.add_arg("-o")
        job.add_arg("-v")  # one filename per line, for progress/the log
        job.add_arg("-F")
        job.add_arg(archive_path)

        rel_files = [pathutil.relative_to(f, self.common_parent) for f in self.effective_files]
        job.set_stdin_text("\n".join(rel_files) + "\n")

    def _build_shar_job(self, job, archive_path):
        # shar can't be built incrementally (there's no "append" for a
        # self-extracting shell script), so this only ever runs as a
        # single batch -- _on_create_clicked() refuses upfront if the
        # selection is larger than BATCH_SIZE rather than attempt it and
        # risk an "Argument list too long" failure mid-archive.
        job.start_batch()
        job.add_arg("shar")
        # -o has to come before the file list -- shar's argument parser
        # is positional and errors out ("shar: -o: No such file or
        # directory") if given the other way round, unlike most GNU tools.
        job.add_arg("-o")
        job.add_arg(archive_path)
        for f in self.effective_files:
            job.add_arg(pathutil.relative_to(f, self.common_parent))

        # shar's -o PREFIX always writes PREFIX.01 (even unsplit), so point
        # it at a side name and rename that into place once it succeeds.
        job.set_rename_after(f"{archive_path}.01", archive_path)

    def _on_create_clicked(self, _btn):
        archive_text = self.archive_name_entry.get_text().strip()
        if not archive_text:
            _error_dialog(self.window, _("Please enter an archive name."))
            return

        password = self.password_entry.get_text()
        confirm = self.confirm_entry.get_text()
        if self.cb_encrypt.get_active() and password != confirm:
            _error_dialog(self.window, _("Passwords do not match."))
            return

        archive_path = (archive_text if os.path.isabs(archive_text)
                         else os.path.join(self.common_parent, archive_text))

        fmt = self.formats[self.current_format]
        archive_exists = os.path.exists(archive_path)

        if archive_exists and not (fmt.capabilities & archivers.CAP_APPEND_EXISTING):
            _error_dialog(self.window, _(
                "This archive already exists, and this format can't be updated in place "
                "(compressed tar archives have to be fully rewritten). Choose a different "
                "name, or delete the existing file first."))
            return

        # Directory expansion: needed for the date filter (which has to
        # test individual files) and for formats that don't reliably
        # recurse into directories themselves (CAP_FLAT_FILES_ONLY).
        # Skipped otherwise so 7z/zip/tar/rar keep getting the original
        # selection -- letting them recurse natively preserves empty
        # directories and avoids building a huge argv for deeply nested
        # selections.
        date_filter_on = self.cb_date_filter.get_active()
        need_flat = bool(fmt.capabilities & archivers.CAP_FLAT_FILES_ONLY)

        if date_filter_on:
            candidates = pathutil.expand_files_recursive(self.files)
            field = self.date_field_combo.get_active_id() or pathutil.TIME_FIELD_MODIFICATION
            cond = self.date_cond_combo.get_active_id() or pathutil.DATE_COND_OLDER
            relative = cond in (pathutil.DATE_COND_OLDER, pathutil.DATE_COND_NEWER)
            threshold = (_relative_duration_seconds(
                            (self.date_rel_years, self.date_rel_months, self.date_rel_days,
                             self.date_rel_hours, self.date_rel_mins, self.date_rel_secs))
                         if relative else
                         _calendar_to_epoch(self.date_calendar, self.date_abs_hours,
                                             self.date_abs_mins, self.date_abs_secs))
            now = time.time()
            self.effective_files = [f for f in candidates
                                     if pathutil.file_matches_date_filter(f, field, cond, threshold, now)]
        elif need_flat:
            self.effective_files = pathutil.expand_files_recursive(self.files)
        else:
            self.effective_files = self.files

        if not self.effective_files:
            msg = (_("No files match the date filter.") if date_filter_on
                   else _("The selection contains no files (only empty folders?), "
                          "and this format needs at least one."))
            _error_dialog(self.window, msg)
            return

        if fmt.id == archivers.FMT_SHAR and len(self.effective_files) > BATCH_SIZE:
            _error_dialog(self.window, _(
                "This selection has more than {n} files, and shar archives can't be "
                "built incrementally (there's no way to \"add to\" a self-extracting "
                "shell script). Choose a different format, or select fewer files."
            ).format(n=BATCH_SIZE))
            return

        job = execute.ArchiveJob(self.common_parent, archive_path)
        job.set_total_files(len(self.effective_files))
        job.set_line_parser(_LINE_PARSERS.get(fmt.id))

        if fmt.id == archivers.FMT_ZIP:
            self._build_zip_job(job, archive_path, password)
        elif fmt.id in (archivers.FMT_TAR, archivers.FMT_TAR_GZ, archivers.FMT_TAR_BZ2,
                        archivers.FMT_TAR_XZ, archivers.FMT_TAR_ZST, archivers.FMT_TAR_LZ,
                        archivers.FMT_TAR_LZO, archivers.FMT_TAR_Z, archivers.FMT_TAR_LZ4):
            self._build_tar_job(job, fmt, archive_path)
        elif fmt.id == archivers.FMT_CPIO:
            self._build_cpio_job(job, archive_path)
        elif fmt.id == archivers.FMT_SHAR:
            self._build_shar_job(job, archive_path)
        elif fmt.id in (archivers.FMT_ARJ, archivers.FMT_ARC, archivers.FMT_LHA):
            self._build_simple_add_job(job, fmt, archive_path, password)
        else:
            self._build_7z_or_rar_job(job, fmt, archive_path, password)

        # Archive timestamp: implemented ourselves (a post-success utime),
        # the same way for every format, since only RAR exposes anything
        # like this natively and even then not for an arbitrary instant.
        time_mode = self.archive_time_combo.get_active_id()
        if time_mode == "original" and archive_exists:
            times = pathutil.get_file_times(archive_path)
            if times:
                job.set_archive_time(times[0])
        elif time_mode == "latest":
            latest = 0
            for f in self.effective_files:
                times = pathutil.get_file_times(f)
                if times and times[0] > latest:
                    latest = times[0]
            if latest > 0:
                job.set_archive_time(latest)
        elif time_mode == "specified":
            job.set_archive_time(_calendar_to_epoch(
                self.archive_time_calendar, self.archive_time_hours,
                self.archive_time_mins, self.archive_time_secs))

        if self.cb_delete_after.get_active():
            confirm_dialog = Gtk.MessageDialog(
                transient_for=self.window, modal=True,
                message_type=Gtk.MessageType.QUESTION, buttons=Gtk.ButtonsType.YES_NO,
                text=_("Delete the {n} selected item(s) after the archive is created "
                       "successfully?").format(n=len(self.files)))
            res = confirm_dialog.run()
            confirm_dialog.destroy()
            if res == Gtk.ResponseType.YES:
                for f in self.files:
                    job.add_delete_after(f)

        self.transferring = True
        execute.run_archive_job(self.window, job)


def show_archive_window(files):
    """Builds and shows the dialog for `files` (absolute paths).
    Returns False (no window shown) if no supported archiver is
    installed at all."""
    formats = archivers.detect()

    if not any(fmt.available for fmt in formats.values()):
        _error_dialog(
            None, _("No supported archiver was found."),
            _("Install one of: p7zip-full, zip, tar, or rar."))
        return False

    ArchiveWindow(files)
    return True
