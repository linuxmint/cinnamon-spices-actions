"""Action UI - Basic GTK Based UI Toolkit for Nemo Actions.
@Author: Anaxímeno Brito <anaximenobrito@gmail.com>
@Url: https://github.com/anaximeno/aui
@Version: 0.1
@License: BSD 3-Clause
"""

import os
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf


def get_action_icon_path(uuid: str) -> str:
    """Returns the path of the `icon.png` file of the action.

    #### Params:

    - `uuid`: the uuid (or id) of the action. It will be used to locate the path of the `icon.png`
              file. Please note that if the action is installed the `test-spice` script, you'll
              have to prepend a `devtest-` to the uuid for it to return the correct location of the
              icon file.
    """
    ACTIONS_DIR = ".local/share/nemo/actions"
    ICON_FILENAME = "icon.png"
    HOME = os.path.expanduser("~")
    return os.path.join(HOME, ACTIONS_DIR, uuid, ICON_FILENAME)


class DialogWindow(Gtk.Window):
    dialog: Gtk.Dialog

    def __init__(self, *args, icon_path: str = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._icon_path = icon_path
        if self._icon_path is not None and os.path.exists(self._icon_path):
            self._icon = GdkPixbuf.Pixbuf.new_from_file(self._icon_path)
            self.set_icon(self._icon)

    def run(self):
        return self.dialog.run()

    def destroy(self):
        self.dialog.destroy()
        super().destroy()


class InfoDialogWindow(DialogWindow):
    def __init__(
        self,
        message: str,
        title: str = None,
        window_icon_path: str = None,
    ) -> None:
        super().__init__(title=title, icon_path=window_icon_path)
        self.dialog = Gtk.MessageDialog(
            flags=0,
            transient_for=self,
            title=title,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
        )
        self.dialog.format_secondary_text(message)


class QuestionDialogWindow(DialogWindow):
    RESPONSE_YES = "y"
    RESPONSE_NO = "n"

    def __init__(
        self,
        message: str,
        title: str = None,
        window_icon_path: str = None,
    ) -> None:
        super().__init__(title=title, icon_path=window_icon_path)
        self.dialog = Gtk.MessageDialog(
            flags=0,
            transient_for=self,
            title=title,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
        )
        self.dialog.format_secondary_text(message)

    def run(self):
        """Returns `y` if the user clicked yes, or `n` if the user clicked no.
        If no response was given (by closing the window or clicking escape) it
        returns python `None`.
        """
        response = super().run()
        if response == Gtk.ResponseType.YES:
            return self.RESPONSE_YES
        elif response == Gtk.ResponseType.NO:
            return self.RESPONSE_NO
        return None


class EntryDialog(Gtk.Dialog):
    def __init__(
        self,
        title: str = None,
        label: str = None,
        default_text: str = "",
        width: int = 360,
        height: int = 120,
        **kwargs,
    ):
        super().__init__(title=title, **kwargs)
        self.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK,
        )
        self._box = Gtk.HBox(spacing=5)

        if label is not None:
            self._label = Gtk.Label(label=label)
            self._box.pack_start(self._label, False, False, 5)

        self.entry = Gtk.Entry(text=default_text)
        self._box.pack_start(self.entry, True, True, 2)

        self._content_area = self.get_content_area()
        self._content_area.add(self._box)
        self.set_default_size(width, height)
        self.show_all()


class EntryDialogWindow(DialogWindow):
    def __init__(
        self,
        title: str = None,
        label: str = None,
        default_text: str = "",
        window_icon_path: str = None,
    ) -> None:
        super().__init__(title=title, icon_path=window_icon_path)
        self.dialog = EntryDialog(
            flags=0,
            transient_for=self,
            title=title,
            label=label,
            default_text=default_text,
        )

    def run(self):
        """Returns entry text if user clicked ok, else returns None."""
        response = super().run()
        if response == Gtk.ResponseType.OK:
            return self.dialog.entry.get_text()
        return None
