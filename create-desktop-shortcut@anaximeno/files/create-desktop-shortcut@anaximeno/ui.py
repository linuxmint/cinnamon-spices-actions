import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk


class BasicMessageDialogWindow(Gtk.Window):
    def __init__(self, title: str, message: str) -> None:
        super().__init__(title="")
        self.title = title
        self.message = message
        self.dialog = Gtk.MessageDialog(
            flags=0,
            transient_for=self,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=self.title
        )
        self.dialog.format_secondary_text(self.message)

    def run(self):
        return self.dialog.run()

    def destroy(self):
        return self.dialog.destroy()

class OverrideQuestionMessageDialogWindow(Gtk.Window):
    # TODO: finish this
    def __init__(self, title: str, message: str) -> None:
        super().__init__(title="")
        self.title = title
        self.message = message
        self.dialog = Gtk.MessageDialog(
            flags=0,
            transient_for=self,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=self.title
        )
        self.dialog.set_default_size(150, 100)
        self.dialog.format_secondary_text(self.message)

    def run(self):
        return self.dialog.run()

    def destroy(self):
        return self.dialog.destroy()
