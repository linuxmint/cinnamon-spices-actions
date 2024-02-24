import text
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class BasicMessageDialogWindow(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="")
        self.dialog = Gtk.MessageDialog(
            flags=0,
            transient_for=self,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=text.ACTION_TITLE,
        )
        self.dialog.format_secondary_text(text.SHORTCUTS_NOT_CREATED_MESSAGE)

    def run(self):
        return self.dialog.run()

    def destroy(self):
        self.dialog.destroy()
        super().destroy()


class OverrideQuestionMessageDialogWindow(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="")
        self.dialog = Gtk.MessageDialog(
            flags=0,
            transient_for=self,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=text.ACTION_TITLE,
        )
        self.dialog.set_default_size(150, 100)
        self.dialog.format_secondary_text(
            text.FILE_ALREADY_EXISTS_AT_THE_DESKTOP_FOLDER
        )

    def run(self):
        response = self.dialog.run()
        return "y" if response == Gtk.ResponseType.YES else "n"

    def destroy(self):
        self.dialog.destroy()
        super().destroy()
