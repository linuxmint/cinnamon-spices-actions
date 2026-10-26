"""Runs an archiver command with a non-blocking progress window.

Mirrors ../archive_action_c/src/exec.c: a job is a sequence of one or
more "batches" (each a plain argv list handed straight to
GLib.spawn_async -- no shell involved, so a filename can never be
interpreted as shell syntax), run in order, followed by an optional
final "test" command. Splitting a very large selection into batches
and adding each one to the archive in turn (instead of one huge
command line) is how ui.py avoids the OS argument-length limit.

The progress window also parses each archiver's stdout for per-file
"added" lines (see parse_added_filename()) to drive a real, file-count
progress bar and a collapsible log, and offers Pause/Continue (SIGSTOP/
SIGCONT on the running archiver -- a real OS-level pause, not something
the archiver has to cooperate with) and "work in background" (lowers
the archiver's scheduling priority and minimizes the window).
"""

import builtins
import os
import shutil
import signal

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

_ = getattr(builtins, "_", lambda s: s)

# "One level down" for the background button: a single, moderate nice
# step. Linux nice values run -20 (highest priority) to 19 (lowest).
BACKGROUND_NICE_STEP = 5

# Which archiver stdout format (see parse_added_filename()) a job's
# "create" batches should be parsed as, to recognize per-file
# completion lines and drive real progress plus the collapsible log
# instead of an indeterminate pulse.
LINE_PARSER_TAR = "tar"            # tar -v: the filename, alone, per line
LINE_PARSER_ZIP = "zip"            # "  adding: <name> (stored/deflated NN%)"
LINE_PARSER_7Z = "7z"              # "+ <name>" (needs -bb1)
LINE_PARSER_RAR_ARJ = "rar_arj"    # "Adding    <name>...<backspace animation>OK"
LINE_PARSER_CPIO = "cpio"          # "'<name>'" (cpio -v; Unicode quotes)
LINE_PARSER_ARC = "arc"            # "Adding file:   <name>      analyzing..."
LINE_PARSER_LHA = "lha"            # "<name>\t- Method(NN%) o"
LINE_PARSER_SHAR = "shar"          # "shar: Saving <name> (text|binary)"


def parse_added_filename(kind, line):
    """Returns the filename `line` reports as added, per `kind`'s
    format, or None if the line isn't a per-file completion line.
    See archive_action_c/README.md for the sample output (piped, i.e.
    non-tty, since that's how we run them) each of these was checked
    against."""
    if kind == LINE_PARSER_TAR:
        name = line.strip()

    elif kind == LINE_PARSER_ZIP:
        p = line.lstrip(" ")
        if p.startswith("adding: "):
            rest = p[len("adding: "):]
        elif p.startswith("updating: "):
            rest = p[len("updating: "):]
        else:
            return None
        paren = rest.rfind("(")
        name = (rest[:paren] if paren != -1 else rest).strip()

    elif kind == LINE_PARSER_7Z:
        if not line.startswith("+ "):
            return None
        name = line[2:].strip()

    elif kind == LINE_PARSER_RAR_ARJ:
        if not line.startswith("Adding"):
            return None
        name = line[len("Adding"):].split("\b")[0].strip()

    elif kind == LINE_PARSER_CPIO:
        s = line.strip()
        if len(s) >= 6 and s.startswith("‘") and s.endswith("’"):
            name = s[1:-1]
        else:
            name = s

    elif kind == LINE_PARSER_ARC:
        if not line.startswith("Adding file:"):
            return None
        p = line[len("Adding file:"):].lstrip(" ")
        stop = p.find("  ")
        name = (p[:stop] if stop != -1 else p).strip()

    elif kind == LINE_PARSER_LHA:
        tab = line.find("\t")
        if tab == -1:
            return None
        name = line[:tab].strip()

    elif kind == LINE_PARSER_SHAR:
        if not line.startswith("shar: Saving "):
            return None
        rest = line[len("shar: Saving "):]
        paren = rest.rfind("(")
        name = (rest[:paren] if paren != -1 else rest).strip()

    else:
        return None

    return name or None


class ArchiveJob:
    def __init__(self, working_dir, archive_path):
        self.batches = []         # list of argv lists, run in order
        self.test_argv = None     # optional final command
        self.working_dir = working_dir
        self.archive_path = archive_path
        self.stdin_text = None    # fed to the LAST batch's stdin, then EOF
        self.set_mtime = None     # epoch seconds, applied on success
        self.delete_after = []    # absolute paths to remove on success
        self.rename_after = None  # (from_path, to_path), applied on success
        self.total_files = 0      # for the progress bar
        self.line_parser = None   # a LINE_PARSER_* constant, or None
        self.last_file_batch = None  # index of the last file-adding batch,
                                      # or None meaning "the last batch"

    def start_batch(self):
        self.batches.append([])

    def add_arg(self, arg):
        assert self.batches, "start_batch() must be called first"
        self.batches[-1].append(arg)

    def add_test_arg(self, arg):
        if self.test_argv is None:
            self.test_argv = []
        self.test_argv.append(arg)

    def set_stdin_text(self, text):
        self.stdin_text = text

    def set_archive_time(self, epoch_seconds):
        self.set_mtime = epoch_seconds

    def add_delete_after(self, path):
        self.delete_after.append(path)

    def set_rename_after(self, from_path, to_path):
        self.rename_after = (from_path, to_path)

    def set_total_files(self, total_files):
        self.total_files = total_files

    def set_line_parser(self, kind):
        self.line_parser = kind

    def set_last_file_batch(self, batch_index):
        self.last_file_batch = batch_index


class _ExecUI:
    def __init__(self, job):
        self.job = job
        self.stage = "create"
        self.batch_index = 0
        self.files_done = 0
        self.stderr_buf = []
        self.pulse_id = None
        self.io_watch_id = None
        self.out_watch_id = None
        self.channel = None
        self.out_channel = None
        self.current_pid = None
        self.paused = False
        self.backgrounded = False

        self.window = Gtk.Window(title=_("Creating archive"))
        self.window.set_resizable(False)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_border_width(12)
        self.window.connect("destroy", lambda *_a: Gtk.main_quit())

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.window.add(box)

        box.pack_start(Gtk.Label(label=os.path.basename(job.archive_path)), False, False, 0)

        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)
        self.progress.set_text(_("Working..."))
        self.progress.set_size_request(320, -1)
        box.pack_start(self.progress, True, True, 0)

        expander = Gtk.Expander(label=_("Show files"))
        expander.set_expanded(False)
        box.pack_start(expander, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_size_request(320, 200)
        expander.add(scroll)

        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_cursor_visible(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.NONE)
        self.log_buffer = self.log_view.get_buffer()
        scroll.add(self.log_view)

        btn_box = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        btn_box.set_layout(Gtk.ButtonBoxStyle.START)
        btn_box.set_spacing(6)
        self.pause_btn = Gtk.Button(label=_("Pause"))
        self.background_btn = Gtk.Button(label=_("Work in background"))
        btn_box.add(self.pause_btn)
        btn_box.add(self.background_btn)
        box.pack_start(btn_box, False, False, 0)
        self.pause_btn.connect("clicked", self._on_pause_clicked)
        self.background_btn.connect("clicked", self._on_background_clicked)

        self.close_btn = Gtk.Button(label=_("Close"))
        self.close_btn.set_sensitive(False)
        self.close_btn.connect("clicked", lambda *_a: self.window.destroy())
        box.pack_start(self.close_btn, False, False, 0)

        self.window.show_all()

    def _pulse(self):
        self.progress.pulse()
        return True

    def _append_log_line(self, filename):
        end = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end, f"{filename} - added\n")
        end = self.log_buffer.get_end_iter()
        mark = self.log_buffer.create_mark(None, end, False)
        self.log_view.scroll_to_mark(mark, 0.0, False, 0, 0)
        self.log_buffer.delete_mark(mark)

    def _update_create_progress(self):
        total = self.job.total_files
        fraction = min(1.0, self.files_done / total) if total > 0 else 0.0
        self.progress.set_fraction(fraction)
        self.progress.set_text(
            _("Adding files... ({done} of {total})").format(done=self.files_done, total=total))

    def _read_stderr(self, channel, condition):
        if condition & GLib.IOCondition.IN:
            while True:
                status, buf, length, _term = channel.read_line()
                if length == 0:
                    break
                self.stderr_buf.append(buf)
                if status != GLib.IOStatus.NORMAL:
                    break
        if condition & (GLib.IOCondition.HUP | GLib.IOCondition.ERR):
            self.io_watch_id = None
            return False
        return True

    def _read_stdout(self, channel, condition):
        if condition & GLib.IOCondition.IN:
            while True:
                status, line, length, _term = channel.read_line()
                if status != GLib.IOStatus.NORMAL or length == 0:
                    break
                name = parse_added_filename(self.job.line_parser, line)
                if name:
                    self.files_done += 1
                    self._update_create_progress()
                    self._append_log_line(name)
        if condition & (GLib.IOCondition.HUP | GLib.IOCondition.ERR):
            self.out_watch_id = None
            return False
        return True

    def _start_stage(self, argv):
        is_last_batch = self.stage == "create" and self.batch_index + 1 == len(self.job.batches)
        want_stdin = is_last_batch and self.job.stdin_text is not None
        want_stdout = self.stage == "create" and self.job.line_parser is not None

        try:
            pid, stdin_fd, stdout_fd, stderr_fd = GLib.spawn_async(
                argv,
                working_directory=self.job.working_dir,
                flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD | GLib.SpawnFlags.SEARCH_PATH,
                standard_input=want_stdin,
                standard_output=want_stdout,
                standard_error=True,
            )
        except GLib.Error as e:
            self.stderr_buf.append(e.message)
            self._finish(False)
            return

        if want_stdin:
            os.write(stdin_fd, self.job.stdin_text.encode("utf-8"))
            os.close(stdin_fd)

        self.current_pid = pid
        if self.paused:
            os.kill(pid, signal.SIGSTOP)
        if self.backgrounded:
            try:
                os.setpriority(os.PRIO_PROCESS, pid,
                                os.getpriority(os.PRIO_PROCESS, pid) + BACKGROUND_NICE_STEP)
            except OSError:
                pass

        if want_stdout:
            self.out_channel = GLib.IOChannel.unix_new(stdout_fd)
            self.out_channel.set_close_on_unref(True)
            self.out_watch_id = GLib.io_add_watch(
                self.out_channel, GLib.PRIORITY_DEFAULT,
                GLib.IOCondition.IN | GLib.IOCondition.HUP, self._read_stdout)

        self.channel = GLib.IOChannel.unix_new(stderr_fd)
        self.channel.set_close_on_unref(True)
        self.io_watch_id = GLib.io_add_watch(
            self.channel, GLib.PRIORITY_DEFAULT,
            GLib.IOCondition.IN | GLib.IOCondition.HUP, self._read_stderr)

        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self._on_child_exit)

        # Only formats without a recognized stdout format fall back to
        # an indeterminate pulse during creation; everything else drives
        # the progress bar from real per-file counts (see _read_stdout).
        if not want_stdout and self.pulse_id is None:
            self.pulse_id = GLib.timeout_add(100, self._pulse)

    def _start_current_batch(self):
        if self.job.line_parser is not None:
            self._update_create_progress()
        self._start_stage(self.job.batches[self.batch_index])

    def _on_pause_clicked(self, _btn):
        self.paused = not self.paused
        if self.paused:
            if self.current_pid:
                os.kill(self.current_pid, signal.SIGSTOP)
            self.pause_btn.set_label(_("Continue"))
        else:
            if self.current_pid:
                os.kill(self.current_pid, signal.SIGCONT)
            self.pause_btn.set_label(_("Pause"))

    def _on_background_clicked(self, btn):
        self.backgrounded = not self.backgrounded

        if self.backgrounded:
            if self.current_pid:
                try:
                    os.setpriority(os.PRIO_PROCESS, self.current_pid,
                                    os.getpriority(os.PRIO_PROCESS, self.current_pid) +
                                    BACKGROUND_NICE_STEP)
                except OSError:
                    pass
            self.window.iconify()
            btn.set_label(_("Run in foreground"))
        else:
            if self.current_pid:
                try:
                    os.setpriority(os.PRIO_PROCESS, self.current_pid, 0)
                except OSError:
                    pass
            btn.set_label(_("Work in background"))

    def _on_child_exit(self, pid, status):
        GLib.spawn_close_pid(pid)
        self.current_pid = None

        if self.io_watch_id is not None:
            GLib.source_remove(self.io_watch_id)
            self.io_watch_id = None
        if self.channel is not None:
            self.channel.shutdown(False)
            self.channel = None
        if self.out_watch_id is not None:
            GLib.source_remove(self.out_watch_id)
            self.out_watch_id = None
        if self.out_channel is not None:
            self.out_channel.shutdown(False)
            self.out_channel = None

        success = os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0

        if not success:
            self._finish(False)
            return

        if self.stage == "create":
            last_file_batch = (self.job.last_file_batch
                                if self.job.last_file_batch is not None
                                else len(self.job.batches) - 1)
            if self.batch_index == last_file_batch:
                self.background_btn.set_sensitive(False)

        if self.stage == "create" and self.batch_index + 1 < len(self.job.batches):
            self.batch_index += 1
            self.stderr_buf = []
            self._start_current_batch()
            return

        if self.stage == "create" and self.job.test_argv:
            self.stage = "test"
            self.stderr_buf = []
            self.progress.set_text(_("Testing archive integrity..."))
            if self.pulse_id is None:
                self.pulse_id = GLib.timeout_add(100, self._pulse)
            self._start_stage(self.job.test_argv)
            return

        self._finish(True)

    def _apply_post_success(self):
        warnings = []

        if self.job.rename_after is not None:
            from_path, to_path = self.job.rename_after
            try:
                os.replace(from_path, to_path)
            except OSError as e:
                warnings.append(_("Could not rename {src} to {dst}: {error}").format(
                    src=from_path, dst=to_path, error=e))

        if self.job.set_mtime is not None:
            try:
                os.utime(self.job.archive_path, (self.job.set_mtime, self.job.set_mtime))
            except OSError as e:
                warnings.append(_("Could not set archive timestamp: {error}").format(error=e))

        for path in self.job.delete_after:
            try:
                if os.path.isdir(path) and not os.path.islink(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except OSError as e:
                warnings.append(_("Could not delete {path}: {error}").format(path=path, error=e))

        return warnings

    def _finish(self, success):
        if self.pulse_id is not None:
            GLib.source_remove(self.pulse_id)
            self.pulse_id = None

        self.progress.set_fraction(1.0)

        if success:
            warnings = self._apply_post_success()
            self.progress.set_text(_("Archive created: {path}").format(path=self.job.archive_path))

            if warnings:
                dialog = Gtk.MessageDialog(
                    transient_for=self.window, modal=True,
                    message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.OK,
                    text=_("Archive created, but some cleanup steps failed."))
                dialog.format_secondary_text("\n".join(warnings))
                dialog.run()
                dialog.destroy()
        else:
            if self.stage == "test":
                fail_text = _("Integrity test failed.")
            elif len(self.job.batches) > 1:
                fail_text = _("Archive creation failed (adding files).")
            else:
                fail_text = _("Archive creation failed.")
            self.progress.set_text(_("Archive failed"))
            detail = "".join(self.stderr_buf).strip()

            dialog = Gtk.MessageDialog(
                transient_for=self.window, modal=True,
                message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
                text=fail_text)
            if detail:
                dialog.format_secondary_text(detail)
            dialog.run()
            dialog.destroy()

        self.close_btn.set_sensitive(True)
        self.pause_btn.set_sensitive(False)
        self.background_btn.set_sensitive(False)

    def run(self):
        self._start_current_batch()


def run_archive_job(window_to_close, job):
    """Destroys `window_to_close` (may be None), then runs the job with
    a non-blocking progress window."""
    if window_to_close is not None:
        window_to_close.destroy()
    _ExecUI(job).run()
