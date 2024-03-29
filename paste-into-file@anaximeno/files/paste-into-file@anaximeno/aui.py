"""Action UI - Basic GTK Based UI Toolkit for Nemo Actions.
@Author: Anaxímeno Brito <anaximenobrito@gmail.com>
@Url: https://github.com/anaximeno/aui
@Version: 0.2
@License: BSD 3-Clause License

Copyright (c) 2024, Anaxímeno Brito

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
contributors may be used to endorse or promote products derived from
this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import os
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, GLib
from typing import Iterable


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


class _EntryDialog(Gtk.Dialog):
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
        self._box = Gtk.VBox(spacing=0)

        if label is not None:
            self._label = Gtk.Label(label=label, xalign=0)
            self._box.pack_start(self._label, False, False, 5)

        self.entry = Gtk.Entry(text=default_text)
        self._box.pack_start(self.entry, True, True, 0)

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
        width: int = 360,
        height: int = 120,
    ) -> None:
        super().__init__(title=title, icon_path=window_icon_path)
        self.dialog = _EntryDialog(
            flags=0,
            transient_for=self,
            title=title,
            label=label,
            default_text=default_text,
            width=width,
            height=height,
        )

    def run(self):
        """Returns entry text if user clicked ok, else returns None."""
        response = super().run()
        if response == Gtk.ResponseType.OK:
            return self.dialog.entry.get_text()
        return None


class _InfiniteProgressbarDialog(Gtk.Dialog):
    def __init__(
        self,
        title: str = None,
        message: str = None,
        width: int = 360,
        height: int = 120,
        **kwargs,
    ):
        super().__init__(title=title, **kwargs)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        self.progressbar = Gtk.ProgressBar()

        if message:
            self.progressbar.set_text(message)
            self.progressbar.set_show_text(True)

        self.progressbar.pulse()

        self._content_area = self.get_content_area()
        self._content_area.add(self.progressbar)
        self.set_default_size(width, height)
        self.show_all()


class InfiniteProgressbarDialogWindow(DialogWindow):
    def __init__(
        self,
        title: str = None,
        message: str = None,
        window_icon_path: str = None,
        width: int = 360,
        height: int = 120,
    ) -> None:
        super().__init__(title=title, icon_path=window_icon_path)
        self.dialog = _InfiniteProgressbarDialog(
            flags=0,
            transient_for=self,
            title=title,
            message=message,
            width=width,
            height=height,
        )
        self._timeout_id = None
        self._active = True

    def run(self):
        self._active = True
        self._timeout_id = GLib.timeout_add(50, self._on_timeout, None)
        return super().run()

    def _on_timeout(self, user_data) -> bool:
        self.dialog.progressbar.pulse()
        return self._active

    def stop(self):
        self._active = False

    def destroy(self):
        self.stop()
        super().destroy()


class RadioChoiceButton:
    def __init__(self, id: str, label: str, on_toggled_cb=None) -> None:
        self._id = id
        self._label = label
        self._on_toggled_cb = on_toggled_cb
        self._gtk_button = None

    @property
    def id(self) -> str:
        return self._id

    @property
    def label(self) -> str:
        return self._label

    @property
    def gtk_button(self) -> Gtk.RadioButton | None:
        return self._gtk_button

    def create_gtk_button(self, from_widget=None) -> Gtk.RadioButton:
        self._gtk_button = Gtk.RadioButton.new_with_label_from_widget(
            from_widget, self._label
        )
        if self._on_toggled_cb is not None:
            self._gtk_button.connect("toggled", self._on_toggled_cb, self._id)
        return self._gtk_button


class _RadioChoiceDialog(Gtk.Dialog):
    def __init__(
        self,
        radio_buttons: Iterable[RadioChoiceButton],
        default_active_button_id: str = None,
        radio_spacing: float = 5,
        radio_orientation=Gtk.Orientation.VERTICAL,
        title: str = None,
        label: str = None,
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

        self.radio_buttons = radio_buttons
        self._radio_buttons_spacing = radio_spacing
        self._radio_orientation = radio_orientation
        self._default_active_button_id = default_active_button_id

        self._box = Gtk.VBox(spacing=0)

        if label is not None:
            self._label = Gtk.Label(label=label, xalign=0)
            self._box.pack_start(self._label, False, False, 10)

        self._radio_box = Gtk.Box(
            spacing=self._radio_buttons_spacing,
            orientation=self._radio_orientation,
        )

        self._box.pack_start(self._radio_box, True, True, 0)

        if any(self.radio_buttons):
            first_button = self.radio_buttons[0]
            first_gtk_btn = first_button.create_gtk_button(None)

            if first_button.id == self._default_active_button_id:
                first_gtk_btn.set_active(True)

            self._radio_box.pack_start(first_gtk_btn, False, False, 0)

            for radio_button in self.radio_buttons[1:]:
                gtk_btn = radio_button.create_gtk_button(first_gtk_btn)
                self._radio_box.pack_start(gtk_btn, False, False, 0)

                if radio_button.id == self._default_active_button_id:
                    gtk_btn.set_active(True)

        self._content_area = self.get_content_area()
        self._content_area.add(self._box)
        self.set_default_size(width, height)
        self.show_all()


class RadioChoiceDialogWindow(DialogWindow):
    VERTICAL_RADIO = Gtk.Orientation.VERTICAL
    HORIZONTAL_RADIO = Gtk.Orientation.HORIZONTAL

    def __init__(
        self,
        radio_buttons: Iterable[RadioChoiceButton],
        default_active_button_id: str = None,
        radio_spacing: float = 5,
        radio_orientation=VERTICAL_RADIO,
        title: str = None,
        label: str = None,
        window_icon_path: str = None,
        width: int = 360,
        height: int = 120,
    ) -> None:
        super().__init__(title=title, icon_path=window_icon_path)
        self.dialog = _RadioChoiceDialog(
            flags=0,
            transient_for=self,
            radio_buttons=radio_buttons,
            default_active_button_id=default_active_button_id,
            radio_spacing=radio_spacing,
            radio_orientation=radio_orientation,
            title=title,
            label=label,
            width=width,
            height=height,
        )

    def run(self) -> str | None:
        """Returns the choice button `id` if user clicked ok, else returns None."""
        response = super().run()
        if response == Gtk.ResponseType.OK:
            for btn in self.dialog.radio_buttons:
                if btn.gtk_button.get_active():
                    return btn.id
        return None
