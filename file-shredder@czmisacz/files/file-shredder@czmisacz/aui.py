#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Action UI - GTK Based UI Toolkit for Nemo Actions.
@Author: Anaxímeno Brito <anaximenobrito@gmail.com>
@Url: https://github.com/anaximeno/aui
@Version: 0.8
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

__version__ = "0.8"


import os
import sys
import gi

import argparse
import select

gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gtk, GdkPixbuf, GLib
from typing import Iterable, Callable, Optional, List
from argparse import Namespace, ArgumentParser


HOME = os.path.expanduser("~")
ICON_LOCATION = os.path.join(HOME, ".local/share/nemo/actions/%s/icon.png")


def log(*messages: object) -> None:
    """Logs a message to the stderr.

    #### Params:

    - `messages`: the messages to be logged
    """
    print(*messages, file=sys.stderr)


def get_action_icon_path(uuid: str, use_dev_icon: Optional[bool] = None) -> str:
    """Returns the path of the `icon.png` file of the action.

    #### Params:

    - `uuid`: the uuid (or id) of the action. It will be used to locate the path of the `icon.png` file
    - `use_dev_icon`: whether to use or not dev icon even if the action icon exists (useful when
        the dev action and the normal action instances are both installed)
    """
    icon_path = ICON_LOCATION % uuid
    dev_icon_path = ICON_LOCATION % ("devtest-" + uuid)

    if os.path.exists(dev_icon_path) and (
        not os.path.exists(icon_path) or use_dev_icon is True
    ):
        return dev_icon_path

    return icon_path


## --- Generic Components ---


class _ScrollableExpanderComponent(Gtk.Expander):
    def __init__(
        self,
        label: str,
        expanded_text: str,
        min_content_height: int = 80,
        max_content_height: int = 150,
        margin: tuple[int, int, int, int] = (0, 15, 10, 15),
    ) -> None:
        super().__init__(label=label if label else "")

        self.set_margin_top(margin[0])
        self.set_margin_end(margin[1])
        self.set_margin_bottom(margin[2])
        self.set_margin_start(margin[3])

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(min_content_height)
        scrolled.set_max_content_height(max_content_height)

        self.expanded_text_label = Gtk.Label()
        self.expanded_text_label.set_markup(expanded_text if expanded_text else "")
        self.expanded_text_label.set_halign(Gtk.Align.START)
        self.expanded_text_label.set_valign(Gtk.Align.START)
        self.expanded_text_label.set_margin_top(5)
        self.expanded_text_label.set_margin_start(10)
        self.expanded_text_label.set_margin_end(10)
        self.expanded_text_label.set_margin_bottom(5)
        self.expanded_text_label.set_line_wrap(True)
        self.expanded_text_label.set_line_wrap_mode(2)
        self.expanded_text_label.set_selectable(True)

        scrolled.add(self.expanded_text_label)
        self.add(scrolled)

    def set_expanded_text(self, text: str) -> None:
        self.expanded_text_label.set_markup(text)


class _HeaderComponent(Gtk.Box):
    def __init__(
        self,
        title: str,
        icon_path: str = None,
        icon_name: str = None,
        spacing: int = 20,
        margin: tuple[int, int, int, int] = (10, 10, 10, 10),
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=spacing)
        self.set_margin_top(margin[0])
        self.set_margin_end(margin[1])
        self.set_margin_bottom(margin[2])
        self.set_margin_start(margin[3])

        self._icon_image = None
        try:
            if icon_path is not None and os.path.exists(icon_path):
                # TODO: don't hardcode icon size
                icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 48, 48)
                self._icon_image = Gtk.Image.new_from_pixbuf(icon_pixbuf)
                self.pack_start(self._icon_image, False, False, 0)
            elif icon_name is not None:
                # TODO: don't hardcode icon size
                icon_pixbuf = Gtk.IconTheme.get_default().load_icon(icon_name, 48, 0)
                self._icon_image = Gtk.Image.new_from_pixbuf(icon_pixbuf)
                self.pack_start(self._icon_image, False, False, 0)
        except Exception as e:
            log("aui.py: Failed to load icon for ContentHeaderComponent. Exception:", e)

        if title is not None:
            self.text_box = Gtk.VBox(spacing=5)

            self.title_label = Gtk.Label()
            self.title_label.set_markup(f"<span size='large'><b>{title}</b></span>")
            self.title_label.set_halign(Gtk.Align.CENTER)
            self.title_label.set_valign(Gtk.Align.CENTER)
            self.text_box.pack_start(self.title_label, False, False, 0)

            self.pack_start(self.text_box, True, True, 0)


## --- Dialog Windows ---


class DialogWindow(Gtk.Window):
    _dialog: Gtk.Dialog

    def __init__(self, *args, icon_path: str = None, icon_name: str = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._dialog = None
        self._icon_path = icon_path
        self._icon_name = icon_name
        self._icon = None

        try:
            if self._icon_path is not None and os.path.exists(self._icon_path):
                self._icon = GdkPixbuf.Pixbuf.new_from_file(self._icon_path)
                self.set_icon(self._icon)
            elif self._icon_name is not None:
                # TODO: don't hardcode icon size
                self._icon = Gtk.IconTheme.get_default().load_icon(self._icon_name, 64, 0)
                self.set_icon(self._icon)
        except Exception as e:
            log("aui.py: Failed to load icon for DialogWindow. Exception:", e)

    @property
    def dialog(self) -> Gtk.Dialog | None:
        return self._dialog

    @dialog.setter
    def dialog(self, dialog: Gtk.Dialog) -> None:
        self._dialog = dialog

    def run(self):
        if self.dialog is None:
            raise RuntimeError("DialogWindow: dialog property is not set.")
        return self.dialog.run()

    def destroy(self):
        if self.dialog is not None:
            self.dialog.destroy()
        super().destroy()


class _InfoDialog(Gtk.Dialog):
    def __init__(
        self,
        *args,
        message: str,
        title: str = None,
        header: str = None,
        width: int,
        height: int,
        resizable: bool = False,
        expander_label: str = "",
        expanded_text: str = "",
        icon_path: str = None,
        icon_name: str = None,
        hide_in_dialog_icon: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(*args, title=title, **kwargs)
        self.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self._box = Gtk.VBox(spacing=10)

        if header is not None or icon_path is not None or icon_name is not None:
            self._header = _HeaderComponent(
                title=header,
                icon_path=icon_path if not hide_in_dialog_icon else None,
                icon_name=icon_name if not hide_in_dialog_icon else None,
                margin=(10, 10, 0, 10),
            )
            self._box.pack_start(self._header, False, False, 0)

        self.label = Gtk.Label()
        self.label.set_margin_top(20)
        self.label.set_margin_bottom(15)
        self.label.set_margin_start(20)
        self.label.set_margin_end(20)
        self.label.set_halign(Gtk.Align.CENTER)
        self.label.set_valign(Gtk.Align.CENTER)
        self.label.set_justify(Gtk.Justification.CENTER)
        self.label.set_line_wrap(True)
        self.label.set_line_wrap_mode(2)
        self.label.set_max_width_chars(width // 10)
        self.label.set_markup(message)

        self._box.pack_start(self.label, True, True, 0)

        self.expander_label = None
        self.expanded_text = None

        if expander_label:
            self.expander = _ScrollableExpanderComponent(
                label=expander_label,
                expanded_text=expanded_text,
                margin=(0, 15, 10, 15),
            )
            self._box.pack_start(self.expander, False, False, 0)

        self._content_area = self.get_content_area()
        self._content_area.add(self._box)
        self.set_default_size(width, height)
        self.set_resizable(resizable)
        self.show_all()


class InfoDialogWindow(DialogWindow):
    def __init__(
        self,
        message: str,
        title: str = None,
        header: str = None,
        width: int = 360,
        height: int = 120,
        resizable: bool = False,
        expander_label: str = "",
        expanded_text: str = "",
        icon_path: str = None,
        icon_name: str = None,
        hide_in_dialog_icon: bool = False,
    ) -> None:
        super().__init__(title=title, icon_path=icon_path, icon_name=icon_name)
        self.dialog = _InfoDialog(
            flags=0,
            transient_for=self,
            title=title,
            header=header,
            message=message,
            width=width,
            height=height,
            resizable=resizable,
            expander_label=expander_label,
            expanded_text=expanded_text,
            icon_path=icon_path,
            icon_name=icon_name,
            hide_in_dialog_icon=hide_in_dialog_icon,
        )


class _QuestionDialog(Gtk.Dialog):
    def __init__(
        self,
        *args,
        message: str,
        title: str = None,
        header: str = None,
        width: int = 360,
        height: int = 120,
        icon_path: str = None,
        icon_name: str = None,
        hide_in_dialog_icon: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(*args, title=title, **kwargs)
        self.add_buttons(
            Gtk.STOCK_NO,
            Gtk.ResponseType.NO,
            Gtk.STOCK_YES,
            Gtk.ResponseType.YES,
        )

        self._content_area = self.get_content_area()

        if header is not None or icon_path is not None or icon_name is not None:
            self._header = _HeaderComponent(
                title=header,
                icon_path=icon_path if not hide_in_dialog_icon else None,
                icon_name=icon_name if not hide_in_dialog_icon else None,
                margin=(10, 10, 0, 10),
            )
            self._content_area.add(self._header)

        self.label = Gtk.Label()
        self.label.set_margin_top(20)
        self.label.set_margin_bottom(15)
        self.label.set_margin_start(20)
        self.label.set_margin_end(20)
        self.label.set_halign(Gtk.Align.CENTER)
        self.label.set_valign(Gtk.Align.CENTER)
        self.label.set_justify(Gtk.Justification.CENTER)
        self.label.set_line_wrap(True)
        self.label.set_line_wrap_mode(2)
        self.label.set_max_width_chars(width // 10)
        self.label.set_markup(message)

        self._content_area.add(self.label)

        self.set_default_size(width, height)
        self.set_resizable(False)
        self.show_all()



class QuestionDialogWindow(DialogWindow):
    RESPONSE_YES = "y"
    RESPONSE_NO = "n"

    def __init__(
        self,
        message: str,
        title: str = None,
        header: str = None,
        width: int = 360,
        height: int = 120,
        icon_path: str = None,
        icon_name: str = None,
        hide_in_dialog_icon: bool = False,
    ) -> None:
        super().__init__(title=title, icon_path=icon_path, icon_name=icon_name)
        self.dialog = _QuestionDialog(
            flags=0,
            transient_for=self,
            title=title,
            message=message,
            header=header,
            width=width,
            height=height,
            icon_path=icon_path,
            icon_name=icon_name,
            hide_in_dialog_icon=hide_in_dialog_icon,
        )

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
        header: str = None,
        default_text: str = "",
        width: int = 360,
        height: int = 120,
        icon_path: str = None,
        icon_name: str = None,
        hide_in_dialog_icon: bool = False,
        **kwargs,
    ):
        super().__init__(title=title, **kwargs)
        self.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK,
        )

        self._content_area = self.get_content_area()

        if header is not None or icon_path is not None or icon_name is not None:
            self._header = _HeaderComponent(
                title=header,
                icon_path=icon_path if not hide_in_dialog_icon else None,
                icon_name=icon_name if not hide_in_dialog_icon else None,
                margin=(10, 10, 0, 10),
            )
            self._content_area.add(self._header)

        self._box = Gtk.VBox(spacing=10)
        self._box.set_margin_top(10)
        self._box.set_margin_bottom(10)
        self._box.set_margin_start(15)
        self._box.set_margin_end(15)

        if label is not None:
            self._label = Gtk.Label(xalign=0)
            self._label.set_markup(label)
            self._label.set_line_wrap(True)
            self._label.set_line_wrap_mode(2)
            self._label.set_max_width_chars(width // 10)
            self._box.pack_start(self._label, False, False, 0)

        self.entry = Gtk.Entry(text=default_text)
        self.entry.set_activates_default(True)
        self._box.pack_start(self.entry, False, False, 0)

        self._content_area.add(self._box)
        self.set_default_size(width, height)
        self.set_default_response(Gtk.ResponseType.OK)
        self.show_all()


class EntryDialogWindow(DialogWindow):
    def __init__(
        self,
        title: str = None,
        label: str = None,
        default_text: str = "",
        header: str = None,
        icon_path: str = None,
        icon_name: str = None,
        width: int = 360,
        height: int = 120,
        hide_in_dialog_icon: bool = False,
    ) -> None:
        super().__init__(title=title, icon_path=icon_path, icon_name=icon_name)
        self.dialog = _EntryDialog(
            flags=0,
            transient_for=self,
            title=title,
            label=label,
            default_text=default_text,
            header=header,
            width=width,
            height=height,
            icon_path=icon_path,
            icon_name=icon_name,
            hide_in_dialog_icon=hide_in_dialog_icon,
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
        header: str = None,
        expander_label: str = "",
        expanded_text: str = "",
        width: int = 360,
        height: int = 120,
        icon_path: str = None,
        icon_name: str = None,
        hide_in_dialog_icon: bool = False,
        no_cancel: bool = False,
        **kwargs,
    ):
        super().__init__(title=title, **kwargs)

        self._content_area = self.get_content_area()

        if header is not None or icon_path is not None or icon_name is not None:
            self._header = _HeaderComponent(
                title=header,
                icon_path=icon_path if not hide_in_dialog_icon else None,
                icon_name=icon_name if not hide_in_dialog_icon else None,
                margin=(10, 10, 0, 10),
            )
            self._content_area.add(self._header)

        self.box = Gtk.VBox(spacing=12)
        self.box.set_margin_top(15)
        self.box.set_margin_bottom(15)
        self.box.set_margin_start(20)
        self.box.set_margin_end(20)

        self.progressbar = Gtk.ProgressBar()
        self.progressbar.set_pulse_step(0.1)

        if message:
            self.progressbar.set_text(message)
            self.progressbar.set_show_text(True)

        self.box.pack_start(self.progressbar, False, False, 0)

        self.expander = None
        if expander_label:
            self.expander = _ScrollableExpanderComponent(
                label=expander_label,
                expanded_text=expanded_text,
                margin=(0, 15, 10, 0),
            )
            self.box.pack_start(self.expander, False, False, 0)

        self._action_button = Gtk.Button.new_from_stock(Gtk.STOCK_CANCEL)
        self.add_action_widget(self._action_button, Gtk.ResponseType.CANCEL)

        if no_cancel:
            self._action_button.set_sensitive(False)

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
        header: str = None,
        expander_label: str = "",
        expanded_text: str = "",
        icon_path: str = None,
        icon_name: str = None,
        width: int = 360,
        height: int = 120,
        on_cancel_callback: Callable = None,
        no_cancel: bool = False,
        hide_in_dialog_icon: bool = False,
    ) -> None:
        super().__init__(title=title, icon_path=icon_path, icon_name=icon_name)
        self._timeout_ms = timeout_ms
        self._timeout_callback = timeout_callback
        self._on_cancel_callback = on_cancel_callback
        self.dialog = _ProgressbarDialog(
            flags=0,
            transient_for=self,
            title=title,
            message=message,
            header=header,
            width=width,
            height=height,
            expander_label=expander_label,
            expanded_text=expanded_text,
            icon_name=icon_name,
            icon_path=icon_path,
            hide_in_dialog_icon=hide_in_dialog_icon,
            no_cancel=no_cancel,
        )
        self._timeout_id = None
        self._active = True
        self._completed = False
        self.dialog.connect("response", self._on_response)

    @property
    def progressbar(self) -> Gtk.ProgressBar:
        return self.dialog.progressbar

    def _on_timeout(self, user_data) -> bool:
        if self._active:
            res = self._timeout_callback(user_data, self)
            self._active = res if res is not None else True
        return self._active

    def _on_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.CANCEL and not self._completed:
            self.cancel(close=False)

    def run(self) -> bool:
        self._active = True
        self._timeout_id = GLib.timeout_add(
            self._timeout_ms,
            self._on_timeout,
            None,
        )
        return super().run() == Gtk.ResponseType.OK

    def complete(self, close=False) -> None:
        self.dialog._action_button.set_label(Gtk.STOCK_OK)
        self.dialog._action_button.set_sensitive(True)
        self._completed = True
        self.stop(cancel=False)
        if close:
            self.dialog.response(Gtk.ResponseType.OK)

    def cancel(self, close=True) -> None:
        self.stop(cancel=True)
        if self._on_cancel_callback:
            self._on_cancel_callback()
        if close:
            self.dialog.response(Gtk.ResponseType.CANCEL)
        log("aui.py: ProgressbarDialogWindow: Cancelled")

    def stop(self, cancel=False) -> None:
        if not self._active:
            return

        self._active = False
        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None

    def destroy(self):
        self.stop()
        super().destroy()

    def set_expanded_text(self, text: str):
        if self.dialog.expander is not None:
            self.dialog.expander.set_expanded_text(text)


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
        radio_buttons: List[RadioChoiceButton],
        default_active_button_id: Optional[str] = None,
        radio_spacing: float = 5,
        radio_orientation=Gtk.Orientation.VERTICAL,
        title: Optional[str] = None,
        label: Optional[str] = None,
        header: Optional[str] = None,
        width: int = 360,
        height: int = 120,
        icon_path: Optional[str] = None,
        icon_name: Optional[str] = None,
        hide_in_dialog_icon: bool = False,
        **kwargs,
    ):
        super().__init__(title=title, **kwargs)

        self.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK,
        )

        self._content_area = self.get_content_area()

        if header is not None or icon_path is not None or icon_name is not None:
            self._header = _HeaderComponent(
                title=header,
                icon_path=icon_path if not hide_in_dialog_icon else None,
                icon_name=icon_name if not hide_in_dialog_icon else None,
                margin=(10, 10, 0, 10),
            )
            self._content_area.add(self._header)

        self.radio_buttons = radio_buttons
        self._radio_buttons_spacing = radio_spacing
        self._default_active_button_id = default_active_button_id
        self._radio_orientation = radio_orientation

        self._box = Gtk.VBox(spacing=12)
        self._box.set_margin_top(15)
        self._box.set_margin_bottom(15)
        self._box.set_margin_start(20)
        self._box.set_margin_end(20)

        if label is not None:
            self._label = Gtk.Label(xalign=0)
            self._label.set_markup(label)
            self._label.set_line_wrap(True)
            self._label.set_line_wrap_mode(2)
            self._label.set_max_width_chars(width // 10)
            self._box.pack_start(self._label, False, False, 0)

        self._radio_box = Gtk.Box(
            spacing=self._radio_buttons_spacing,
            orientation=self._radio_orientation,
        )

        self._box.pack_start(self._radio_box, False, False, 0)

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

        self._content_area.add(self._box)

        self.set_default_size(width, height)
        self.set_default_response(Gtk.ResponseType.OK)
        self.show_all()


class RadioChoiceDialogWindow(DialogWindow):
    VERTICAL_RADIO = Gtk.Orientation.VERTICAL
    HORIZONTAL_RADIO = Gtk.Orientation.HORIZONTAL

    def __init__(
        self,
        radio_buttons: List[RadioChoiceButton],
        default_active_button_id: Optional[str] = None,
        radio_spacing: float = 5,
        radio_orientation=VERTICAL_RADIO,
        title: Optional[str] = None,
        label: Optional[str] = None,
        header: Optional[str] = None,
        icon_path: Optional[str] = None,
        icon_name: Optional[str] = None,
        hide_in_dialog_icon: bool = False,
        width: int = 360,
        height: int = 120,
    ) -> None:
        super().__init__(title=title, icon_path=icon_path, icon_name=icon_name)
        self.dialog = _RadioChoiceDialog(
            flags=0,
            transient_for=self,
            radio_buttons=radio_buttons,
            default_active_button_id=default_active_button_id,
            radio_spacing=radio_spacing,
            radio_orientation=radio_orientation,
            title=title,
            label=label,
            header=header,
            width=width,
            height=height,
            icon_path=icon_path,
            icon_name=icon_name,
            hide_in_dialog_icon=hide_in_dialog_icon,
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
    def __init__(self, id: int, text: str, on_click_action: Callable | None = None) -> None:
        self._id = id
        self._on_click_action = on_click_action
        self._text = text

    @property
    def id(self) -> int:
        return self._id

    @property
    def text(self) -> str:
        return self._text

    @property
    def on_click_action(self) -> Callable | None:
        return self._on_click_action

    def trigger_on_click_action(self, *args, **kwargs) -> None:
        if self._on_click_action is not None:
            self._on_click_action(*args, **kwargs)


class _ActionableDialog(Gtk.Dialog):
    def __init__(
        self,
        *args,
        title: str = None,
        message: str,
        header: str = None,
        buttons: Iterable[ActionableButton],
        width: int,
        height: int,
        default_button_id: Optional[int] = None,
        icon_path: str = None,
        icon_name: str = None,
        hide_in_dialog_icon: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(*args, title=title, **kwargs)
        self._content_area = self.get_content_area()

        if header is not None or icon_path is not None or icon_name is not None:
            self._header = _HeaderComponent(
                title=header,
                icon_path=icon_path if not hide_in_dialog_icon else None,
                icon_name=icon_name if not hide_in_dialog_icon else None,
                margin=(10, 10, 0, 10),
            )
            self._content_area.add(self._header)

        self._box = Gtk.VBox(spacing=10)
        self._label = Gtk.Label()
        self._label.set_margin_top(20)
        self._label.set_margin_bottom(15)
        self._label.set_margin_start(20)
        self._label.set_margin_end(20)
        self._label.set_halign(Gtk.Align.CENTER)
        self._label.set_valign(Gtk.Align.CENTER)
        self._label.set_justify(Gtk.Justification.CENTER)
        self._label.set_line_wrap(True)
        self._label.set_line_wrap_mode(2)
        self._label.set_max_width_chars(width // 10)
        self._label.set_markup(message)
        self._box.pack_start(self._label, True, True, 0)
        self._content_area.add(self._box)
        self._buttons = buttons
        self._default_button_id = default_button_id

        for button in self._buttons:
            self.add_button(button.text, button.id)
            if button.id == self._default_button_id:
                self.set_default_response(button.id)

        self.set_default_size(width, height)
        self.show_all()


class ActionableDialogWindow(DialogWindow):
    def __init__(
        self,
        *args,
        title: str,
        message: str,
        header: str = None,
        buttons: Iterable[ActionableButton],
        width: int = 360,
        height: int = 120,
        icon_path: str = None,
        icon_name: str = None,
        default_button_id: Optional[int] = None,
        hide_in_dialog_icon: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(
            *args,
            title=title,
            icon_path=icon_path,
            icon_name=icon_name,
            **kwargs,
        )
        self.buttons = buttons
        self.dialog = _ActionableDialog(
            flags=0,
            transient_for=self,
            title=title,
            message=message,
            header=header,
            buttons=buttons,
            width=width,
            height=height,
            default_button_id=default_button_id,
            icon_path=icon_path,
            icon_name=icon_name,
            hide_in_dialog_icon=hide_in_dialog_icon,
        )

    def run(self) -> Optional[int]:
        response = super().run()
        for button in self.buttons:
            if response == button.id:
                button.trigger_on_click_action()
                return button.id
        return None

# TODO: Add more dialog windows (e.g., FileChooserDialogWindow, ColorChooserDialogWindow, FormDialogWindow, etc.)

## --- Command Line Interface ---

def run(parser: ArgumentParser, args: Namespace) -> None:
    if args.version is True:
        print(f"Action UI v{__version__}")

    elif args.dialog_type == 'info':
        dialog = InfoDialogWindow(
            message=args.text,
            title=args.title,
            header=args.header,
            expanded_text=args.expanded_text,
            expander_label=args.expander_label,
            icon_path=args.icon_path,
            icon_name=args.icon_name,
            hide_in_dialog_icon=args.hide_in_dialog_icon,
            width=args.width,
            height=args.height
        )
        dialog.run()
        dialog.destroy()

    elif args.dialog_type == 'question':
        dialog = QuestionDialogWindow(
            message=args.text,
            title=args.title,
            header=args.header,
            icon_path=args.icon_path,
            icon_name=args.icon_name,
            hide_in_dialog_icon=args.hide_in_dialog_icon,
            width=args.width,
            height=args.height
        )
        result = dialog.run()
        dialog.destroy()
        if result == QuestionDialogWindow.RESPONSE_YES:
            exit(0)
        else:
            exit(1)

    elif args.dialog_type == 'entry':
        dialog = EntryDialogWindow(
            title=args.title,
            label=args.text,
            default_text=args.entry_text,
            header=args.header,
            icon_path=args.icon_path,
            icon_name=args.icon_name,
            hide_in_dialog_icon=args.hide_in_dialog_icon,
            width=args.width,
            height=args.height
        )
        result = dialog.run()
        dialog.destroy()
        if result is not None:
            print(result)
            exit(0)
        else:
            exit(1)

    elif args.dialog_type == 'choice':
        radio_buttons = []
        if args.add_choice:
            for choice_id, choice_text in enumerate(args.add_choice, 1):
                radio_buttons.append(RadioChoiceButton(id=choice_id, label=choice_text))

        orientation = RadioChoiceDialogWindow.VERTICAL_RADIO
        if args.orientation == 'horizontal':
            orientation = RadioChoiceDialogWindow.HORIZONTAL_RADIO

        dialog = RadioChoiceDialogWindow(
            radio_buttons=radio_buttons,
            default_active_button_id=args.default_choice,
            radio_orientation=orientation,
            title=args.title,
            label=args.text,
            header=args.header,
            icon_path=args.icon_path,
            icon_name=args.icon_name,
            hide_in_dialog_icon=args.hide_in_dialog_icon,
            width=args.width,
            height=args.height
        )
        result = dialog.run()
        dialog.destroy()
        if result is not None:
            print(result)
            exit(0)
        else:
            exit(1)

    elif args.dialog_type == 'action':
        actionable_buttons = []
        if args.add_button:
            for button_id, button_text in enumerate(args.add_button, 1):
                actionable_buttons.append(ActionableButton(
                    id=button_id,
                    text=button_text,
                ))

        dialog = ActionableDialogWindow(
            title=args.title,
            message=args.text,
            buttons=actionable_buttons,
            default_button_id=args.default_button,
            header=args.header,
            icon_path=args.icon_path,
            icon_name=args.icon_name,
            hide_in_dialog_icon=args.hide_in_dialog_icon,
            width=args.width,
            height=args.height
        )
        result = dialog.run()
        dialog.destroy()
        if result is not None:
            print(result)
            exit(0)
        else:
            exit(1)

    elif args.dialog_type == 'progress':
        def progress_timeout_callback(user_data, progress_dialog: ProgressbarDialogWindow):
            if args.pulse:
                progress_dialog.progressbar.pulse()

            try:
                if select.select([sys.stdin], [], [], 0)[0]:
                    line = sys.stdin.readline().strip()
                    if not line:
                        return True
                    elif line.isnumeric():
                        try:
                            progress_value = int(line)
                            if 0 <= progress_value <= 100 and not args.pulse:
                                progress_dialog.progressbar.set_fraction(progress_value / 100.0)
                            if progress_value >= 100:
                                progress_dialog.progressbar.set_fraction(1.0)
                                progress_dialog.complete(close=args.auto_close)
                        except ValueError:
                            # NOTE: Ignore lines that cannot be parsed as integers
                            pass
                    elif line.startswith("#"):
                        progress_dialog.progressbar.set_text(line[1:].strip())
                    elif line.startswith(">") and args.expander_label:
                        progress_dialog.set_expanded_text(line[1:].strip())
            except Exception as e:
                # NOTE: Ignore exceptions during progress input polling, but log for debugging.
                log(f"aui.py: Exception in progress_timeout_callback: {e}")

            return True

        cancelled = False
        def on_cancel_callback():
            nonlocal cancelled
            cancelled = True

        dialog = ProgressbarDialogWindow(
            timeout_callback=progress_timeout_callback,
            timeout_ms=args.timeout_ms,
            title=args.title,
            message=args.text,
            header=args.header,
            icon_path=args.icon_path,
            icon_name=args.icon_name,
            hide_in_dialog_icon=args.hide_in_dialog_icon,
            width=args.width,
            height=args.height,
            on_cancel_callback=on_cancel_callback,
            no_cancel=args.no_cancel,
            expander_label=args.expander_label,
            expanded_text=args.expanded_text,
        )
        dialog.run()
        dialog.destroy()
        if cancelled:
            exit(1)
        else:
            exit(0)

    else:
        parser.print_help()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Action UI - GTK Dialog Tool")
    parser.add_argument('--version', help='show the version and exit', action='store_true')

    subparsers = parser.add_subparsers(dest='dialog_type', help='Dialog types')

    # Info dialog window
    info_parser = subparsers.add_parser('info', help='Show information dialog')
    info_parser.add_argument('--text', required=True, help='Dialog text')
    info_parser.add_argument('--title', help='Dialog window title', required=True)
    info_parser.add_argument('--header', help='Dialog header text')
    info_parser.add_argument('--width', type=int, default=360, help='Dialog window width')
    info_parser.add_argument('--height', type=int, default=120, help='Dialog window height')
    info_parser.add_argument('--icon-path', help='Window icon path')
    info_parser.add_argument('--icon-name', help='Window icon name')
    info_parser.add_argument('--hide-in-dialog-icon', action='store_true', help='Hide icon in dialog header')
    info_parser.add_argument('--expander-label', help='Expander label text')
    info_parser.add_argument('--expanded-text', help='Expanded text content')

    # Question dialog window
    question_parser = subparsers.add_parser('question', help='Show question dialog')
    question_parser.add_argument('--text', required=True, help='Dialog text')
    question_parser.add_argument('--header', help='Dialog header text')
    question_parser.add_argument('--title', help='Dialog window title', required=True)
    question_parser.add_argument('--width', type=int, default=360, help='Dialog window width')
    question_parser.add_argument('--height', type=int, default=120, help='Dialog window height')
    question_parser.add_argument('--icon-path', help='Window icon path')
    question_parser.add_argument('--icon-name', help='Window icon name')
    question_parser.add_argument('--hide-in-dialog-icon', action='store_true', help='Hide icon in dialog header')

    # Entry dialog window
    entry_parser = subparsers.add_parser('entry', help='Show text entry dialog')
    entry_parser.add_argument('--text', help='Dialog label text')
    entry_parser.add_argument('--title', help='Dialog window title', required=True)
    entry_parser.add_argument('--entry-text', default='', help='Default entry text')
    entry_parser.add_argument('--header', help='Dialog header text')
    entry_parser.add_argument('--width', type=int, default=360, help='Dialog window width')
    entry_parser.add_argument('--height', type=int, default=120, help='Dialog window height')
    entry_parser.add_argument('--icon-path', help='Window icon path')
    entry_parser.add_argument('--icon-name', help='Window icon name')
    entry_parser.add_argument('--hide-in-dialog-icon', action='store_true', help='Hide icon in dialog header')

    # Radio choice dialog window
    choice_parser = subparsers.add_parser('choice', help='Show choice dialog')
    choice_parser.add_argument('--text', required=True, help='Dialog text')
    choice_parser.add_argument('--header', help='Dialog header text')
    choice_parser.add_argument('--title', help='Dialog window title', required=True)
    choice_parser.add_argument('--width', type=int, default=360, help='Dialog window width')
    choice_parser.add_argument('--height', type=int, default=120, help='Dialog window height')
    choice_parser.add_argument('--icon-path', help='Window icon path')
    choice_parser.add_argument('--icon-name', help='Window icon name')
    choice_parser.add_argument('--hide-in-dialog-icon', action='store_true', help='Hide icon in dialog header')
    choice_parser.add_argument('--add-choice', action='append', help='Add a choice option (can be used multiple times).', required=True)
    choice_parser.add_argument('--default-choice', type=int, help='Default active choice ID')
    choice_parser.add_argument('--orientation', choices=['vertical', 'horizontal'],
                              default='vertical', help='Radio buttons orientation')

    # Action dialog window
    action_parser = subparsers.add_parser('action', help='Show action dialog')
    action_parser.add_argument('--text', required=True, help='Dialog text')
    action_parser.add_argument('--header', help='Dialog header text')
    action_parser.add_argument('--title', help='Dialog window title', required=True)
    action_parser.add_argument('--width', type=int, default=360, help='Dialog window width')
    action_parser.add_argument('--height', type=int, default=120, help='Dialog window height')
    action_parser.add_argument('--icon-path', help='Window icon path')
    action_parser.add_argument('--icon-name', help='Window icon name')
    action_parser.add_argument('--hide-in-dialog-icon', action='store_true', help='Hide icon in dialog header')
    action_parser.add_argument('--add-button', action='append', help='Add a button option (can be used multiple times).', required=True)
    action_parser.add_argument('--default-button', type=int, help='Default button id (starts from 1, based on order added).')

    # Progress bar dialog window
    progress_parser = subparsers.add_parser('progress', help='Show progress dialog')
    progress_parser.add_argument('--text', required=True, help='Dialog text')
    progress_parser.add_argument('--header', help='Dialog header text')
    progress_parser.add_argument('--title', help='Dialog window title', required=True)
    progress_parser.add_argument('--width', type=int, default=360, help='Dialog window width')
    progress_parser.add_argument('--height', type=int, default=120, help='Dialog window height')
    progress_parser.add_argument('--icon-path', help='Window icon path')
    progress_parser.add_argument('--icon-name', help='Window icon name')
    progress_parser.add_argument('--hide-in-dialog-icon', action='store_true', help='Hide icon in dialog header')
    progress_parser.add_argument('--pulse', action='store_true', help='Enable pulsing animation')
    progress_parser.add_argument('--timeout-ms', type=int, default=50, help='Timeout in milliseconds for progress updates')
    progress_parser.add_argument('--auto-close', action='store_true', help='Auto close dialog when progress reaches 100%')
    progress_parser.add_argument('--no-cancel', action='store_true', help='Disable cancel button')
    progress_parser.add_argument('--expander-label', help='Expander label text')
    progress_parser.add_argument('--expanded-text', help='Expanded text content')

    #TODO: Add more dialog types to CLI

    args = parser.parse_args()

    run(parser, args)
