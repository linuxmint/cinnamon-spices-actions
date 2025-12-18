"""Action UI - Basic GTK Based UI Toolkit for Nemo Actions.

@Author: Anaxímeno Brito <anaximenobrito@gmail.com>
@Url: https://github.com/anaximeno/aui
@Version: 0.5
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

import gettext

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from pathlib import Path
from typing import Callable, Optional, Sequence, Union

from gi.repository import GdkPixbuf, GLib, Gtk
from utils import text
from utils.logging import logger

_ = gettext.gettext


def _ensure_app_initialized() -> None:
    """Ensure GTK application is initialized with icon and name."""
    try:
        from .icons import _ensure_app_initialized as _init_app

        _init_app()
    except ImportError:
        pass


HOME = Path.home()

ACTIONS_DIR = ".local/share/nemo/actions"
ICON_FILENAME = "icon.png"


def get_action_icon_path(
    uuid: str, use_dev_icon_if_found: Optional[bool] = None
) -> str:
    """Returns the path of the `icon.png` file of the action.

    Args:
        uuid: The uuid (or id) of the action. It will be used to locate the path of the `icon.png` file.
        use_dev_icon_if_found: Whether to use or not dev icon even if the action icon exists (useful when
            the dev action and the normal action instances are both installed).

    Returns:
        str: Path to the icon file.

    Note:
        Prefers dev icon if it exists and use_dev_icon_if_found is True, otherwise uses regular icon.
    """
    icon_path = HOME / ACTIONS_DIR / uuid / ICON_FILENAME
    dev_icon_path = HOME / ACTIONS_DIR / f"devtest-{uuid}" / ICON_FILENAME

    if dev_icon_path.exists() and (
        not icon_path.exists() or use_dev_icon_if_found is True
    ):
        return str(dev_icon_path)

    return str(icon_path)


class DialogWindow(Gtk.Window):
    """Base dialog window wrapper for consistent dialog behavior.

    Provides a wrapper around GTK dialogs with consistent icon handling
    and lifecycle management. All dialog windows should inherit from this class.

    Attributes:
        dialog: The underlying GTK dialog widget.
        _icon_path: Path to the window icon file.
        _icon: Loaded GdkPixbuf icon image.
    """

    dialog: Gtk.Dialog

    def __init__(self, *args, icon_path: Optional[str] = None, **kwargs) -> None:
        """Initialize the dialog window.

        Args:
            *args: Variable arguments passed to Gtk.Window.
            icon_path: Path to the window icon file.
            **kwargs: Keyword arguments passed to Gtk.Window.

        Returns:
            None
        """
        _ensure_app_initialized()
        logger.debug("Initializing dialog window with icon_path: {}", icon_path)
        super().__init__(*args, **kwargs)
        self._icon_path = icon_path
        if self._icon_path is not None and Path(self._icon_path).exists():
            self._icon = GdkPixbuf.Pixbuf.new_from_file(self._icon_path)
            self.set_icon(self._icon)
            logger.debug("Dialog window icon loaded from: {}", icon_path)
        else:
            logger.debug("Dialog window icon not found or not specified")

    def run(self) -> Union[int, str, None]:
        """Run the dialog and return the response.

        Returns:
            Union[int, str, None]: Dialog response code or value.
        """
        logger.debug("Running dialog window")
        response = self.dialog.run()
        logger.debug("Dialog window response: {}", response)
        return response

    def destroy(self) -> None:
        """Destroy the dialog and clean up resources."""
        logger.debug("Destroying dialog window")
        self.dialog.destroy()
        super().destroy()


class _InfoDialog(Gtk.Dialog):
    """Internal information dialog with optional expandable details.

    A basic information display dialog that can show a message with
    optional expandable text section for additional details.
    """

    def __init__(
        self,
        *args,
        message: str,
        title: Optional[str] = None,
        width: int,
        height: int,
        expander_label: str = "",
        expanded_text: str = "",
        **kwargs,
    ):
        """Initialize the information dialog.

        Args:
            *args: Variable arguments passed to Gtk.Dialog.
            message: Main message text to display (supports markup).
            title: Dialog window title.
            width: Dialog width in pixels.
            height: Dialog height in pixels.
            expander_label: Label for expandable section (empty for no expander).
            expanded_text: Text to show when expander is expanded.
            **kwargs: Keyword arguments passed to Gtk.Dialog.

        Returns:
            None
        """
        super().__init__(*args, title=title, **kwargs)
        self.add_buttons(_("OK"), Gtk.ResponseType.OK)
        self._box = Gtk.VBox()
        self.label = Gtk.Label()
        self.label.set_margin_top(8)
        self.label.set_margin_bottom(8)
        self.label.set_margin_start(8)
        self.label.set_margin_end(8)
        self.label.set_halign(Gtk.Align.CENTER)
        self.label.set_valign(Gtk.Align.CENTER)
        self.label.set_xalign(0.5)
        self.label.set_yalign(0.5)
        self.label.set_justify(Gtk.Justification.CENTER)
        self.label.set_selectable(True)
        self.label.set_markup(message)

        self._box.pack_start(self.label, True, True, 0)

        self.expander_label = None
        self.expanded_text = None

        if expander_label:
            self.expander = Gtk.Expander(label=expander_label)
            self.expanded_text_label = Gtk.Label()
            self.expanded_text_label.set_markup(expanded_text)
            self.expanded_text_label.set_halign(Gtk.Align.START)
            self.expanded_text_label.set_margin_top(8)
            self.expanded_text_label.set_margin_start(8)
            self.expander.add(self.expanded_text_label)
            self._box.pack_start(self.expander, True, True, 8)

        self._content_area = self.get_content_area()
        self._content_area.add(self._box)
        self.set_default_size(width, height)
        self.show_all()


class InfoDialogWindow(DialogWindow):
    """Information dialog window wrapper.

    Provides a user-friendly information display dialog with optional
    expandable details section for additional information.
    """

    def __init__(
        self,
        message: str,
        title: Optional[str] = None,
        window_icon_path: Optional[str] = None,
        width: int = 360,
        height: int = 120,
        expander_label: str = "",
        expanded_text: str = "",
    ):
        """Initialize the information dialog window.

        Args:
            message: Main message text to display (supports markup).
            title: Dialog window title.
            window_icon_path: Path to window icon file.
            width: Dialog width in pixels.
            height: Dialog height in pixels.
            expander_label: Label for expandable section.
            expanded_text: Text to show when expander is expanded.

        Returns:
            None
        """
        logger.debug("Creating info dialog window with title: {}", title)
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


class QuestionDialogWindow(DialogWindow):
    """Question dialog window for yes/no user prompts.

    Displays a question to the user with Yes/No buttons and returns
    the user's response. Supports markup in the question text.
    """

    RESPONSE_YES = "y"
    RESPONSE_NO = "n"

    def __init__(
        self,
        message: str,
        title: Optional[str] = None,
        window_icon_path: Optional[str] = None,
    ):
        """Initialize the question dialog window.

        Args:
            message: Question text to display (supports markup).
            title: Dialog window title.
            window_icon_path: Path to window icon file.

        Returns:
            None
        """
        logger.debug("Creating question dialog window with title: {}", title)
        super().__init__(title=title, icon_path=window_icon_path)
        self.dialog = Gtk.MessageDialog(
            flags=0,
            transient_for=self,
            title=title,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
        )
        self.dialog.format_secondary_text(message)

    def run(self) -> Optional[str]:
        """Run the dialog and return the user's response.

        Returns:
            Optional[str]: 'y' for Yes, 'n' for No, None if cancelled/closed.

        Examples:
            >>> dialog = QuestionDialogWindow("Continue?")
            >>> response = dialog.run()
            >>> if response == dialog.RESPONSE_YES:
            ...     print("User said yes")
        """
        logger.debug("Running question dialog")
        response = super().run()
        if response == Gtk.ResponseType.YES:
            logger.debug("Question dialog response: YES")
            return self.RESPONSE_YES
        elif response == Gtk.ResponseType.NO:
            logger.debug("Question dialog response: NO")
            return self.RESPONSE_NO
        logger.debug("Question dialog cancelled")
        return None


class _EntryDialog(Gtk.Dialog):
    """Internal text entry dialog for user input.

    Provides a simple dialog with a label and text entry field
    for collecting user input strings.
    """

    def __init__(
        self,
        title: Optional[str] = None,
        label: Optional[str] = None,
        default_text: str = "",
        width: int = 360,
        height: int = 120,
        **kwargs,
    ):
        """Initialize the entry dialog.

        Args:
            title: Dialog window title.
            label: Label text above the entry field (supports markup).
            default_text: Default text in the entry field.
            width: Dialog width in pixels.
            height: Dialog height in pixels.
            **kwargs: Keyword arguments passed to Gtk.Dialog.

        Returns:
            None
        """
        super().__init__(title=title, **kwargs)
        self.add_buttons(
            text.UI.CANCEL_BUTTON_LABEL,
            Gtk.ResponseType.CANCEL,
            text.UI.OK_BUTTON_LABEL,
            Gtk.ResponseType.OK,
        )
        self._box = Gtk.VBox(spacing=0)

        if label is not None:
            self._label = Gtk.Label(xalign=0)
            self._label.set_margin_top(8)
            self._label.set_margin_start(8)
            self._label.set_margin_end(8)
            self._label.set_markup(label)
            self._box.pack_start(self._label, False, False, 8)

        self.entry = Gtk.Entry(text=default_text)
        self.entry.set_margin_bottom(8)
        self.entry.set_margin_start(8)
        self.entry.set_margin_end(8)
        self._box.pack_start(self.entry, True, True, 0)

        self._content_area = self.get_content_area()
        self._content_area.add(self._box)
        self.set_default_size(width, height)
        self.show_all()


class EntryDialogWindow(DialogWindow):
    """Text entry dialog window for user input collection.

    Provides a dialog with a text entry field for collecting string input
    from the user. Supports default text and label customization.
    """

    def __init__(
        self,
        title: Optional[str] = None,
        label: Optional[str] = None,
        default_text: str = "",
        window_icon_path: Optional[str] = None,
        width: int = 360,
        height: int = 120,
    ):
        """Initialize the entry dialog window.

        Args:
            title: Dialog window title.
            label: Label text above the entry field (supports markup).
            default_text: Default text in the entry field.
            window_icon_path: Path to window icon file.
            width: Dialog width in pixels.
            height: Dialog height in pixels.

        Returns:
            None
        """
        logger.debug("Creating entry dialog window with title: {}", title)
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

    def run(self) -> Optional[str]:
        """Run the dialog and return the entered text.

        Returns:
            Optional[str]: Entered text if OK clicked, None if cancelled.

        Examples:
            >>> dialog = EntryDialogWindow("Enter name", "Name:")
            >>> name = dialog.run()
            >>> if name:
            ...     print(f"User entered: {name}")
        """
        logger.debug("Running entry dialog")
        response = super().run()
        if response == Gtk.ResponseType.OK:
            entered_text = self.dialog.entry.get_text()
            logger.debug(
                "Entry dialog OK clicked, text entered: {} chars", len(entered_text)
            )
            return entered_text
        logger.debug("Entry dialog cancelled")
        return None

    def on_entry_activate(self, entry) -> None:
        """Handle Enter key press in the entry field."""
        logger.debug("Entry dialog: Enter key pressed, emitting OK response")
        self.dialog.emit("response", Gtk.ResponseType.OK)


class _ProgressbarDialog(Gtk.Dialog):
    """Internal progress bar dialog with optional expandable details.

    Displays a progress bar with optional message and expandable text
    section for showing detailed progress information.
    """

    def __init__(
        self,
        title: Optional[str] = None,
        message: Optional[str] = None,
        expander_label: str = "",
        expanded_text: str = "",
        width: int = 360,
        height: int = 120,
        **kwargs,
    ):
        """Initialize the progress bar dialog.

        Args:
            title: Dialog window title.
            message: Message text above the progress bar (supports markup).
            expander_label: Label for expandable details section.
            expanded_text: Text to show when expander is expanded.
            width: Dialog width in pixels.
            height: Dialog height in pixels.
            **kwargs: Keyword arguments passed to Gtk.Dialog.

        Returns:
            None
        """
        super().__init__(title=title, **kwargs)
        self.add_buttons(text.UI.CANCEL_BUTTON_LABEL, Gtk.ResponseType.CANCEL)
        self.box = Gtk.VBox(spacing=8)
        self.progressbar = Gtk.ProgressBar()
        self.progressbar.set_margin_top(8)
        self.progressbar.set_margin_bottom(8)
        self.progressbar.set_margin_start(8)
        self.progressbar.set_margin_end(8)

        if message:
            self.message_label = Gtk.Label()
            self.message_label.set_markup(message)
            self.message_label.set_halign(Gtk.Align.CENTER)
            self.message_label.set_valign(Gtk.Align.CENTER)
            self.message_label.set_justify(Gtk.Justification.CENTER)
            self.message_label.set_margin_top(8)
            self.message_label.set_margin_bottom(0)
            self.message_label.set_margin_start(8)
            self.message_label.set_margin_end(8)
            self.message_box = Gtk.HBox()
            self.message_box.pack_start(self.message_label, True, False, 0)
            self.box.pack_start(self.message_box, False, False, 0)

        self.box.pack_start(self.progressbar, True, True, 0)

        self.expander = None
        self.expanded_text_label = None
        if expander_label:
            self.expander = Gtk.Expander(label=expander_label)
            self.expander.set_margin_top(0)
            self.expander.set_margin_bottom(8)
            self.expander.set_margin_start(8)
            self.expander.set_margin_end(8)
            self.expanded_text_label = Gtk.Label()
            self.expanded_text_label.set_markup(expanded_text)
            self.expanded_text_label.set_halign(Gtk.Align.START)
            self.expanded_text_label.set_margin_top(8)
            self.expanded_text_label.set_margin_start(8)
            self.expander.add(self.expanded_text_label)
            self.box.pack_start(self.expander, True, True, 0)

        self._content_area = self.get_content_area()
        self._content_area.add(self.box)
        self.set_default_size(width, height)
        self.show_all()


class ProgressbarDialogWindow(DialogWindow):
    """Progress bar dialog window with timeout-based updates.

    Displays a progress bar that can be updated via a callback function
    called at regular intervals. Supports cancellation and expandable details.
    """

    def __init__(
        self,
        timeout_callback: Callable,
        timeout_ms: int = 50,
        title: Optional[str] = None,
        message: Optional[str] = None,
        expander_label: str = "",
        expanded_text: str = "",
        window_icon_path: Optional[str] = None,
        width: int = 360,
        height: int = 120,
    ):
        """Initialize the progress bar dialog window.

        Args:
            timeout_callback: Function called periodically to update progress.
            timeout_ms: Milliseconds between callback invocations.
            title: Dialog window title.
            message: Message text above the progress bar.
            expander_label: Label for expandable details section.
            expanded_text: Text to show when expander is expanded.
            window_icon_path: Path to window icon file.
            width: Dialog width in pixels.
            height: Dialog height in pixels.

        Returns:
            None
        """
        logger.debug("Creating progress bar dialog window with title: {}", title)
        super().__init__(title=title, icon_path=window_icon_path)
        self._timeout_ms = timeout_ms
        self._timeout_callback = timeout_callback
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

    @property
    def progressbar(self) -> Gtk.ProgressBar:
        """Get the progress bar widget for direct manipulation."""
        return self.dialog.progressbar

    def set_message(self, message: str) -> None:
        """Update the message text above the progress bar.

        Args:
            message: New message text (supports markup).
        """
        logger.debug(
            "Progress dialog message updated: {}",
            message[:50] + "..." if len(message) > 50 else message,
        )
        if self.dialog.message_label is not None:
            self.dialog.message_label.set_markup(message)

    def run(self) -> Union[int, str, None]:
        """Run the dialog with periodic callback updates."""
        logger.debug("Running progress bar dialog with {}ms timeout", self._timeout_ms)
        self._active = True
        self._timeout_id = GLib.timeout_add(
            self._timeout_ms,
            self._handle_on_timeout,
            None,
        )
        response = super().run()
        logger.debug("Progress bar dialog finished with response: {}", response)
        return response

    def _handle_on_timeout(self, user_data) -> bool:
        """Handle timeout callback and determine continuation."""
        if self._active:
            res = self._timeout_callback(user_data, self)
            self._active = res if res is not None else True
            logger.debug(
                "Progress dialog timeout callback executed, continue: {}", self._active
            )
        return self._active

    def stop(self) -> None:
        """Stop the timeout callback and progress updates."""
        logger.debug("Stopping progress dialog timeout")
        self._active = False
        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None

    def destroy(self) -> None:
        """Destroy the dialog and stop any running timeouts."""
        logger.debug("Destroying progress bar dialog")
        self.stop()
        super().destroy()

    def set_expanded_text(self, text: str) -> None:
        """Update the text in the expandable details section.

        Args:
            text: New text for the expanded section (supports markup).
        """
        logger.debug("Progress dialog expanded text updated: {} chars", len(text))
        if self.dialog.expanded_text_label is not None:
            self.dialog.expanded_text_label.set_markup(text)


class RadioChoiceButton:
    """Radio button choice with ID and label for selection dialogs.

    Represents a single choice in a radio button group, with an ID for
    programmatic identification and a display label for the user.
    """

    def __init__(
        self, id: str, label: str, on_toggled_cb: Optional[Callable] = None
    ) -> None:
        """Initialize the radio choice button.

        Args:
            id: Unique identifier for this choice.
            label: Display text for the radio button.
            on_toggled_cb: Callback function called when button is toggled.

        Returns:
            None
        """
        self._id = id
        self._label = label
        self._on_toggled_cb = on_toggled_cb
        self._gtk_button = None

    @property
    def id(self) -> str:
        """Get the unique identifier for this choice."""
        return self._id

    @property
    def label(self) -> str:
        """Get the display label for this choice."""
        return self._label

    @property
    def gtk_button(self) -> Optional[Gtk.RadioButton]:
        """Get the underlying GTK radio button widget."""
        return self._gtk_button

    def create_gtk_button(
        self, from_widget: Optional[Gtk.RadioButton] = None
    ) -> Gtk.RadioButton:
        """Create the GTK radio button widget.

        Args:
            from_widget: Previous radio button in the group (None for first button).

        Returns:
            Gtk.RadioButton: The created GTK radio button widget.
        """
        self._gtk_button = Gtk.RadioButton.new_with_label_from_widget(
            from_widget, self._label
        )
        if self._on_toggled_cb is not None:
            self._gtk_button.connect("toggled", self._on_toggled_cb, self._id)
        return self._gtk_button


class _RadioChoiceDialog(Gtk.Dialog):
    """Internal radio button selection dialog.

    Displays a group of radio buttons for single-choice selection,
    with optional label and configurable layout orientation.
    """

    def __init__(
        self,
        radio_buttons: Sequence[RadioChoiceButton],
        default_active_button_id: Optional[str] = None,
        radio_spacing: float = 8,
        radio_orientation=Gtk.Orientation.VERTICAL,
        title: Optional[str] = None,
        label: Optional[str] = None,
        width: int = 360,
        height: int = 120,
        **kwargs,
    ):
        """Initialize the radio choice dialog.

        Args:
            radio_buttons: Sequence of RadioChoiceButton objects.
            default_active_button_id: ID of button to activate by default.
            radio_spacing: Spacing between radio buttons in pixels.
            radio_orientation: Layout orientation (VERTICAL/HORIZONTAL).
            title: Dialog window title.
            label: Label text above the radio buttons.
            width: Dialog width in pixels.
            height: Dialog height in pixels.
            **kwargs: Keyword arguments passed to Gtk.Dialog.

        Returns:
            None
        """
        super().__init__(title=title, **kwargs)

        self.add_buttons(
            text.UI.CANCEL_BUTTON_LABEL,
            Gtk.ResponseType.CANCEL,
            text.UI.OK_BUTTON_LABEL,
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
            self._box.pack_start(self._label, False, False, 8)

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
    """Radio button selection dialog window.

    Provides a dialog with radio buttons for single-choice user selection.
    Supports vertical or horizontal layouts and default selection.
    """

    VERTICAL_RADIO = Gtk.Orientation.VERTICAL
    HORIZONTAL_RADIO = Gtk.Orientation.HORIZONTAL

    def __init__(
        self,
        radio_buttons: Sequence[RadioChoiceButton],
        default_active_button_id: Optional[str] = None,
        radio_spacing: float = 8,
        radio_orientation=VERTICAL_RADIO,
        title: Optional[str] = None,
        label: Optional[str] = None,
        window_icon_path: Optional[str] = None,
        width: int = 360,
        height: int = 120,
    ):
        """Initialize the radio choice dialog window.

        Args:
            radio_buttons: Sequence of RadioChoiceButton objects to display.
            default_active_button_id: ID of button to select by default.
            radio_spacing: Spacing between radio buttons in pixels.
            radio_orientation: Layout orientation (VERTICAL_RADIO/HORIZONTAL_RADIO).
            title: Dialog window title.
            label: Label text above the radio buttons (supports markup).
            window_icon_path: Path to window icon file.
            width: Dialog width in pixels.
            height: Dialog height in pixels.

        Returns:
            None
        """
        logger.debug(
            "Creating radio choice dialog window with {} buttons", len(radio_buttons)
        )
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

    def run(self) -> Optional[str]:
        """Run the dialog and return the selected choice ID.

        Returns:
            Optional[str]: ID of selected radio button, or None if cancelled.
        Examples:
            >>> buttons = [RadioChoiceButton("opt1", "Option 1")]
            >>> dialog = RadioChoiceDialogWindow(buttons)
            >>> choice = dialog.run()
            >>> if choice:
            ...     print(f"Selected: {choice}")
        """
        logger.debug("Running radio choice dialog")
        response = super().run()
        if response == Gtk.ResponseType.OK:
            for btn in self.dialog.radio_buttons:
                if btn.gtk_button.get_active():
                    selected_id = btn.id
                    logger.debug("Radio choice dialog selected: {}", selected_id)
                    return selected_id
        logger.debug("Radio choice dialog cancelled")
        return None
