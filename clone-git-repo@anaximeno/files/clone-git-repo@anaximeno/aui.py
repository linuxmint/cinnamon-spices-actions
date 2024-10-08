"""Action UI - Basic GTK Based UI Toolkit for Nemo Actions.
@Author: Anaxímeno Brito <anaximenobrito@gmail.com>
@Url: https://github.com/anaximeno/aui
@Version: 0.6
@License: MIT License

Copyright (c) 2024, Anaxímeno Brito

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, GLib
from typing import Iterable, Callable


HOME = os.path.expanduser("~")

ACTIONS_DIR = ".local/share/nemo/actions"
ICON_FILENAME = "icon.png"


def get_action_icon_path(uuid: str, use_dev_icon_if_found=None) -> str:
    """Returns the path of the `icon.png` file of the action.

    #### Params:

    - `uuid`: the uuid (or id) of the action. It will be used to locate the path of the `icon.png` file
    - `use_dev_icon_if_found`: whether to use or not dev icon even if the action icon existe (useful when
        the dev action and the normal action instances are both installed)
    """
    icon_path = os.path.join(HOME, ACTIONS_DIR, uuid, ICON_FILENAME)
    dev_icon_path = os.path.join(HOME, ACTIONS_DIR, "devtest-" + uuid, ICON_FILENAME)

    if os.path.exists(dev_icon_path) and (
        not os.path.exists(icon_path) or use_dev_icon_if_found is True
    ):
        return dev_icon_path

    return icon_path


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


class _InfoDialog(Gtk.Dialog):
    def __init__(
        self,
        *args,
        message: str,
        title: str = None,
        width: int,
        height: int,
        expander_label: str = "",
        expanded_text: str = "",
        **kwargs,
    ) -> None:
        super().__init__(*args, title=title, **kwargs)
        self.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self._box = Gtk.VBox()
        self.label = Gtk.Label()
        self.label.set_margin_top(10)
        self.label.set_margin_bottom(10)
        self.label.set_margin_start(10)
        self.label.set_margin_end(10)
        self.label.set_halign(Gtk.Align.CENTER)
        self.label.set_valign(Gtk.Align.CENTER)
        self.label.set_markup(message)

        self._box.pack_start(self.label, True, True, 0)

        self.expander_label = None
        self.expanded_text = None

        if expander_label:
            self.expander = Gtk.Expander(label=expander_label)
            self.expanded_text_label = Gtk.Label()
            self.expanded_text_label.set_markup(expanded_text)
            self.expanded_text_label.set_halign(Gtk.Align.START)
            self.expanded_text_label.set_margin_top(5)
            self.expanded_text_label.set_margin_start(10)
            self.expander.add(self.expanded_text_label)
            self._box.pack_start(self.expander, True, True, 10)

        self._content_area = self.get_content_area()
        self._content_area.add(self._box)
        self.set_default_size(width, height)
        self.show_all()


class InfoDialogWindow(DialogWindow):
    def __init__(
        self,
        message: str,
        title: str = None,
        window_icon_path: str = None,
        width: int = 360,
        height: int = 120,
        expander_label: str = "",
        expanded_text: str = "",
    ) -> None:
        super().__init__(title=title, icon_path=window_icon_path)
        self.dialog = _InfoDialog(
            flags=0,
            transient_for=self,
            title=title,
            message=message,
            width=width,
            height=height,
            expander_label=expander_label,
            expanded_text=expanded_text,
        )


class QuestionDialogWindow(DialogWindow):  # TODO: support markup annotations
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
            self._label = Gtk.Label(xalign=0)
            self._label.set_margin_top(2)
            self._label.set_margin_start(5)
            self._label.set_margin_end(5)
            self._label.set_markup(label)
            self._box.pack_start(self._label, False, False, 5)

        self.entry = Gtk.Entry(text=default_text)
        self.entry.set_margin_bottom(2)
        self.entry.set_margin_start(5)
        self.entry.set_margin_end(5)
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
        self.dialog.entry.connect("activate", self.on_entry_activate)

    def run(self):
        """Returns entry text if user clicked ok, else returns None."""
        response = super().run()
        if response == Gtk.ResponseType.OK:
            return self.dialog.entry.get_text()
        return None

    def on_entry_activate(self, entry):
        self.dialog.emit("response", Gtk.ResponseType.OK)


class _ProgressbarDialog(Gtk.Dialog):
    def __init__(
        self,
        title: str = None,
        message: str = None,
        expander_label: str = "",
        expanded_text: str = "",
        width: int = 360,
        height: int = 120,
        **kwargs,
    ):
        super().__init__(title=title, **kwargs)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        self.box = Gtk.VBox(spacing=15)
        self.progressbar = Gtk.ProgressBar()
        self.progressbar.set_margin_top(10)
        self.progressbar.set_margin_start(5)
        self.progressbar.set_margin_end(5)

        if message:
            self.progressbar.set_text(message)
            self.progressbar.set_show_text(True)

        self.box.pack_start(self.progressbar, True, True, 0)

        self.expander = None
        self.expanded_text_label = None
        if expander_label:
            self.expander = Gtk.Expander(label=expander_label)
            self.expander.set_margin_start(5)
            self.expander.set_margin_end(5)
            self.expanded_text_label = Gtk.Label()
            self.expanded_text_label.set_markup(expanded_text)
            self.expanded_text_label.set_halign(Gtk.Align.START)
            self.expanded_text_label.set_margin_top(5)
            self.expanded_text_label.set_margin_start(10)
            self.expander.add(self.expanded_text_label)
            self.box.pack_start(self.expander, True, True, 0)

        self._content_area = self.get_content_area()
        self._content_area.add(self.box)
        self.set_default_size(width, height)
        self.show_all()


class ProgressbarDialogWindow(DialogWindow):
    def __init__(
        self,
        timeout_callback: Callable,
        timeout_ms: int = 50,
        title: str = None,
        message: str = None,
        expander_label: str = "",
        expanded_text: str = "",
        window_icon_path: str = None,
        width: int = 360,
        height: int = 120,
        on_cancel_callback: Callable = None,
    ) -> None:
        super().__init__(title=title, icon_path=window_icon_path)
        self._timeout_ms = timeout_ms
        self._timeout_callback = timeout_callback
        self._on_cancel_callback = on_cancel_callback
        self.dialog = _ProgressbarDialog(
            flags=0,
            transient_for=self,
            title=title,
            message=message,
            width=width,
            height=height,
            expander_label=expander_label,
            expanded_text=expanded_text,
        )
        self._timeout_id = None
        self._active = True
        self.dialog.connect("response", self._on_cancel)

    @property
    def progressbar(self) -> Gtk.ProgressBar:
        return self.dialog.progressbar

    def _on_cancel(self, dialog, response_id) -> None:
        if self._on_cancel_callback:
            self._on_cancel_callback()

    def run(self):
        self._active = True
        self._timeout_id = GLib.timeout_add(
            self._timeout_ms,
            self._handle_on_timeout,
            None,
        )
        return super().run()

    def _handle_on_timeout(self, user_data) -> bool:
        if self._active:
            res = self._timeout_callback(user_data, self)
            self._active = res if res is not None else True
        return self._active

    def stop(self):
        self._active = False
        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None

    def destroy(self):
        self.stop()
        super().destroy()

    def set_expanded_text(self, text: str):
        if self.dialog.expanded_text_label is not None:
            self.dialog.expanded_text_label.set_markup(text)


class RadioChoiceButton:
    def __init__(self, id: str, label: str, on_toggled_cb: Callable = None) -> None:
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
        self._default_active_button_id = default_active_button_id
        self._radio_orientation = radio_orientation

        self._box = Gtk.VBox(spacing=0)

        if label is not None:
            self._label = Gtk.Label(xalign=0)
            self._label.set_markup(label)
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


class ActionableButton:
    _id_counter = 0

    def __init__(self, text: str, on_click_action: Callable) -> None:
        self._id = self._get_id()
        self._on_click_action = on_click_action
        self._text = text

    @classmethod
    def _get_id(cls):
        cls._id_counter += 1
        return cls._id_counter

    @property
    def id(self) -> str:
        return self._id

    @property
    def text(self) -> str:
        return self._text

    @property
    def on_click_action(self) -> Callable:
        return self._on_click_action

    def trigger_on_click_action(self, *args, **kwargs) -> None:
        self._on_click_action(*args, **kwargs)


class _ActionableDialog(Gtk.Dialog):
    def __init__(
        self,
        *args,
        title: str = None,
        message: str,
        buttons: Iterable[ActionableButton],
        width: int,
        height: int,
        **kwargs,
    ) -> None:
        super().__init__(*args, title=title, **kwargs)
        self._box = Gtk.VBox()
        self._label = Gtk.Label()
        self._label.set_margin_top(10)
        self._label.set_margin_bottom(10)
        self._label.set_margin_start(10)
        self._label.set_margin_end(10)
        self._label.set_halign(Gtk.Align.CENTER)
        self._label.set_valign(Gtk.Align.CENTER)
        self._label.set_markup(message)
        self._box.pack_start(self._label, True, True, 0)
        self._content_area = self.get_content_area()
        self._content_area.add(self._box)
        self._buttons = buttons

        for button in self._buttons:
            self.add_button(button.text, button.id)

        self.set_default_size(width, height)
        self.show_all()


class ActionableDialogWindow(DialogWindow):
    def __init__(
        self,
        *args,
        title: str,
        message: str,
        buttons: Iterable[ActionableButton],
        width: int = 360,
        height: int = 120,
        window_icon_path: str = None,
        **kwargs,
    ) -> None:
        super().__init__(
            *args,
            title=title,
            icon_path=window_icon_path,
            **kwargs,
        )
        self.buttons = buttons
        self.dialog = _ActionableDialog(
            flags=0,
            transient_for=self,
            message=message,
            buttons=buttons,
            width=width,
            height=height,
        )

    def run(self) -> None:
        response = super().run()
        for button in self.buttons:
            if response == button.id:
                button.trigger_on_click_action()
                break
