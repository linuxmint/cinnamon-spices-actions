#!/usr/bin/python3
"""
Enhanced dialog components for file conversion UI.

This module provides specialized dialog windows for file conversion operations,
built on top of the base aui framework with improved error handling and user experience.
"""

import contextlib
import subprocess
from typing import Iterable, Optional

from utils import text
from utils.logging import logger

from .aui import DialogWindow
from .gi import Gdk, GLib, Gtk


class _SelectDropdownDialog(Gtk.Dialog):
    """A dialog window with a dropdown menu for selecting options.

    This internal dialog provides a simple interface for users to select from
    a list of predefined choices using a dropdown combo box. It supports
    custom button labels and default selection.

    Attributes:
        box: Main vertical container for dialog elements.
        label: Label widget displaying the selection prompt.
        combo: ComboBoxText widget containing the selectable options.
    """

    def __init__(
        self,
        label: str,
        choices: Iterable[str],
        default_choice: Optional[str],
        ok_button_label: Optional[str] = "",
        width: int = 360,
        height: int = 120,
        **kwargs,
    ):
        """Initialize the dropdown selection dialog.

        Args:
            label: Text to display above the dropdown menu.
            choices: Iterable of strings representing available options.
            default_choice: Default selected option (must be in choices).
            ok_button_label: Custom label for OK button (uses default if empty).
            width: Dialog window width in pixels.
            height: Dialog window height in pixels.
            **kwargs: Additional arguments passed to Gtk.Dialog constructor.

        Returns:
            None
        """
        logger.debug(
            "Initializing dropdown selection dialog with {} choices", len(list(choices))
        )
        choices = list(choices)
        super().__init__(**kwargs)

        ok_label = ok_button_label or text.UI.OK_BUTTON_LABEL

        self.add_buttons(
            text.UI.CANCEL_BUTTON_LABEL,
            Gtk.ResponseType.CANCEL,
            ok_label,
            Gtk.ResponseType.OK,
        )

        self.box = Gtk.VBox(spacing=8)
        self.label = Gtk.Label(xalign=0)
        self.label.set_markup(label)
        self.label.set_margin_top(8)
        self.label.set_margin_start(8)
        self.label.set_margin_end(8)

        self.combo = Gtk.ComboBoxText()
        self.combo.set_margin_start(8)
        self.combo.set_margin_end(8)
        self.combo.set_margin_bottom(8)

        for choice in choices:
            self.combo.append_text(choice)

        if default_choice and default_choice in choices:
            self.combo.set_active(choices.index(default_choice))
        elif choices:
            self.combo.set_active(0)

        self.combo.connect("key-press-event", self._on_combo_key_press)

        self.box.pack_start(self.label, False, False, 0)
        self.box.pack_start(self.combo, False, False, 0)
        self.get_content_area().add(self.box)
        self.set_default_size(width, height)
        self.show_all()

    def _on_combo_key_press(self, widget, event) -> bool:
        """Handle keyboard events on the combo box.

        Prevents Enter key from opening the dropdown and instead triggers
        the OK button response. Space key still opens the dropdown normally.

        Args:
            widget: The combo box widget.
            event: The key press event.

        Returns:
            bool: True to stop event propagation, False to allow default behavior.
        """
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            logger.debug("Enter key pressed in combo box, triggering OK response")
            self.response(Gtk.ResponseType.OK)
            return True
        return False

    def get_selected(self) -> Optional[str]:
        """Get the currently selected choice from the dropdown.

        Returns:
            Optional[str]: The selected option text, or None if no selection.
        """
        selected = self.combo.get_active_text()
        logger.debug("Dropdown selection retrieved: {}", selected)
        return selected


class SelectDropdownDialogWindow(DialogWindow):
    """Dialog window wrapper for dropdown selection.

    Provides a user-friendly interface for selecting from multiple options
    with proper error handling and consistent styling. Wraps the internal
    _SelectDropdownDialog for enhanced functionality.

    Attributes:
        dialog: Internal _SelectDropdownDialog instance.
    """

    def __init__(
        self,
        label: str,
        choices: Iterable[str],
        default_choice: Optional[str] = None,
        ok_button_label: Optional[str] = None,
        width: int = 360,
        height: int = 120,
        **kwargs,
    ):
        """Initialize the dropdown selection dialog window.

        Args:
            label: Text to display above the dropdown menu.
            choices: Iterable of strings representing available options.
            default_choice: Default selected option (must be in choices).
            ok_button_label: Custom label for OK button.
            width: Dialog window width in pixels.
            height: Dialog window height in pixels.
            **kwargs: Additional arguments passed to DialogWindow constructor.

        Returns:
            None
        """
        logger.debug("Creating dropdown selection dialog window")
        super().__init__(**kwargs)
        self.dialog = _SelectDropdownDialog(
            label=label,
            choices=choices,
            default_choice=default_choice,
            ok_button_label=ok_button_label,
            width=width,
            height=height,
        )

    def get_selected(self) -> Optional[str]:
        """Get the currently selected choice from the dropdown.

        Returns:
            Optional[str]: The selected option text, or None if no selection.
        """
        selected = self.dialog.get_selected()
        logger.debug("Dialog window selection retrieved: {}", selected)
        return selected


class _ErrorDialog(Gtk.Dialog):
    """Enhanced error dialog with expandable details section.

    Provides comprehensive error reporting with copy-to-clipboard functionality,
    expandable details for debugging information, and direct GitHub issue reporting.
    Features modal behavior and stays on top for critical error visibility.

    Attributes:
        box: Main vertical container for dialog elements.
        label: Label widget displaying the main error message.
        copy_confirmation: Label showing copy confirmation (hidden by default).
        _copy_confirmation_message: Message displayed after copying to clipboard.
        _copy_button: Reference to the copy button for state management.
    """

    def __init__(
        self,
        message: str,
        error_details: str = "",
        copy_content: str = "",
        copy_button_label: str = "",
        copy_confirmation_message: str = "",
        width: int = 400,
        height: int = 152,
        **kwargs,
    ):
        """Initialize the enhanced error dialog.

        Args:
            message: Main error message to display (supports markup).
            error_details: Detailed error information for expandable section.
            copy_content: Content to copy to clipboard (defaults to error_details).
            copy_button_label: Custom label for copy button.
            copy_confirmation_message: Message shown after successful copy.
            width: Dialog window width in pixels.
            height: Dialog window height in pixels.
            **kwargs: Additional arguments passed to Gtk.Dialog constructor.

        Returns:
            None
        """
        logger.debug(
            "Initializing error dialog with message: {}",
            message[:50] + "..." if len(message) > 50 else message,
        )
        super().__init__(**kwargs)

        self.set_modal(True)
        self.set_keep_above(True)

        self._copy_confirmation_message = (
            copy_confirmation_message or text.UI.ERROR_DETAILS_COPIED_MESSAGE
        )

        if error_details:
            button_label = copy_button_label or text.UI.COPY_ERROR_BUTTON_LABEL
            copy_button = Gtk.Button(label=button_label)
            content_to_copy = copy_content or error_details
            copy_button.connect(
                "clicked", self._copy_error_to_clipboard, content_to_copy
            )
            self.get_action_area().pack_start(copy_button, False, False, 0)
            copy_button.show()
            self._copy_button = copy_button

            report_button = Gtk.Button(label=text.UI.REPORT_ERROR_BUTTON_LABEL)
            report_button.connect(
                "clicked", self._report_error_to_github, error_details
            )
            self.get_action_area().pack_start(report_button, False, False, 0)
            report_button.show()

        self.add_button(text.UI.OK_BUTTON_LABEL, Gtk.ResponseType.OK)

        self.connect("response", self._on_response)
        self.connect("key-press-event", self._on_key_press)

        self._setup_ui(message, error_details, width, height)

    def _setup_ui(
        self, message: str, error_details: str, width: int, height: int
    ) -> None:
        """Set up the dialog UI components.

        Args:
            message: Main error message to display.
            error_details: Detailed error information for expandable section.
            width: Dialog window width in pixels.
            height: Dialog window height in pixels.

        Returns:
            None
        """
        self.box = Gtk.VBox(spacing=8)

        self.label = Gtk.Label()
        self.label.set_markup(f"<span weight='bold'>{message}</span>")
        self.label.set_margin_top(8)
        self.label.set_margin_start(8)
        self.label.set_margin_end(8)
        self.label.set_halign(Gtk.Align.START)
        self.label.set_line_wrap(True)
        self.box.pack_start(self.label, False, False, 0)

        if error_details:
            self._add_error_details(error_details)

        self.get_content_area().add(self.box)
        self.set_default_size(width, height)
        self.show_all()

    def _add_error_details(self, error_details: str) -> None:
        """Add expandable error details section to the dialog.

        Creates an expandable section containing a label with the detailed
        error information and copy confirmation label.

        Args:
            error_details: Detailed error information to display.

        Returns:
            None
        """
        expander = Gtk.Expander()
        expander.set_expanded(True)
        expander.set_margin_start(8)
        expander.set_margin_end(8)
        expander.set_margin_top(0)
        expander.set_margin_bottom(8)

        details_container = Gtk.VBox(spacing=8)
        details_container.set_margin_top(8)

        details_label = Gtk.Label()
        escaped_details = GLib.markup_escape_text(error_details)
        details_label.set_markup(escaped_details)
        details_label.set_halign(Gtk.Align.START)
        details_label.set_valign(Gtk.Align.START)
        details_label.set_line_wrap(True)
        details_label.set_selectable(True)
        details_label.set_margin_start(8)
        details_label.set_margin_end(8)
        details_label.set_margin_top(8)
        details_label.set_margin_bottom(8)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(256)
        scrolled_window.add(details_label)
        details_container.pack_start(scrolled_window, True, True, 0)

        self.copy_confirmation = Gtk.Label()
        self.copy_confirmation.set_markup(f"<i>{self._copy_confirmation_message}</i>")
        self.copy_confirmation.set_halign(Gtk.Align.START)
        self.copy_confirmation.set_margin_start(8)
        self.copy_confirmation.set_no_show_all(True)
        details_container.pack_start(self.copy_confirmation, False, False, 0)

        expander.add(details_container)
        self.box.pack_start(expander, True, True, 0)

    def _copy_error_to_clipboard(self, button, error_details: str) -> None:
        """Copy error details to the system clipboard.

        Attempts to copy the error details to clipboard with persistence.
        Shows a confirmation message that auto-hides after 3 seconds.
        Falls back to basic clipboard functionality if advanced features fail.

        Args:
            button: The button that triggered this action (unused).
            error_details: Error details text to copy to clipboard.

        Returns:
            None
        """
        logger.debug(
            "Copying error details to clipboard ({} chars)", len(error_details)
        )
        try:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(error_details, -1)
            clipboard.store()

            if hasattr(self, "copy_confirmation"):
                self.copy_confirmation.show()

                def hide_confirmation() -> bool:
                    if hasattr(self, "copy_confirmation"):
                        self.copy_confirmation.hide()
                    return False

                GLib.timeout_add(3000, hide_confirmation)
            logger.debug("Error details copied to clipboard successfully")

        except Exception:
            logger.warning("Advanced clipboard copy failed, using basic copy")
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(error_details, -1)

    def _report_error_to_github(self, button, error_details: str) -> None:
        """Open GitHub issues page for error reporting.

        Attempts to open the GitHub issues page for this project using
        the system's default browser. Falls back to copying the URL
        to clipboard if browser opening fails.

        Args:
            button: The button that triggered this action (unused).
            error_details: Error details (unused, kept for consistency).

        Returns:
            None
        """
        github_url = "https://github.com/linuxmint/cinnamon-spices-actions/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aopen+convert-file%40thigschuch"
        logger.debug("Opening GitHub issues page for error reporting")

        try:
            subprocess.Popen(
                ["xdg-open", github_url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.debug("GitHub issues page opened successfully")
        except (FileNotFoundError, subprocess.SubprocessError):
            logger.warning("xdg-open failed, trying webbrowser module")
            try:
                import webbrowser

                webbrowser.open(github_url)
                logger.debug("GitHub issues page opened via webbrowser")
            except Exception:
                logger.warning("Browser opening failed, copying URL to clipboard")
                with contextlib.suppress(Exception):
                    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                    clipboard.set_text(github_url, -1)
                    clipboard.store()
                    logger.debug("GitHub URL copied to clipboard as fallback")

    def _on_key_press(self, widget, event) -> bool:
        """Handle keyboard events on the error dialog.

        Triggers OK button response when Enter/Return key is pressed,
        allowing quick dismissal of error dialogs via keyboard.

        Args:
            widget: The dialog widget.
            event: The key press event.

        Returns:
            bool: True to stop event propagation, False to allow default behavior.
        """
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            logger.debug("Enter key pressed in error dialog, triggering OK response")
            self.response(Gtk.ResponseType.OK)
            return True
        return False

    def _on_response(self, dialog, response_id) -> None:
        """Handle dialog response events.

        Processes dialog button clicks and manages dialog lifecycle.
        Currently only handles OK button responses.

        Args:
            dialog: The dialog widget that emitted the response.
            response_id: GTK response identifier.

        Returns:
            None
        """
        logger.debug("Error dialog response: {}", response_id)
        if response_id == Gtk.ResponseType.OK:
            logger.debug("Error dialog OK button clicked, destroying dialog")
            self.destroy()


class ErrorDialogWindow(DialogWindow):
    """Dialog window wrapper for error display.

    Provides enhanced error reporting with expandable details,
    copy-to-clipboard functionality, and consistent styling.
    Wraps the internal _ErrorDialog for enhanced functionality.

    Attributes:
        dialog: Internal _ErrorDialog instance.
    """

    def __init__(
        self,
        message: str,
        error_details: str = "",
        copy_content: str = "",
        copy_button_label: str = "",
        copy_confirmation_message: str = "",
        width: int = 600,
        height: int = 400,
        **kwargs,
    ):
        """Initialize the error dialog window.

        Args:
            message: Main error message to display (supports markup).
            error_details: Detailed error information for expandable section.
            copy_content: Content to copy to clipboard (defaults to error_details).
            copy_button_label: Custom label for copy button.
            copy_confirmation_message: Message shown after successful copy.
            width: Dialog window width in pixels.
            height: Dialog window height in pixels.
            **kwargs: Additional arguments passed to DialogWindow constructor.

        Returns:
            None
        """
        logger.debug("Creating error dialog window")
        super().__init__(**kwargs)
        self.dialog = _ErrorDialog(
            message=message,
            error_details=error_details,
            copy_content=copy_content,
            copy_button_label=copy_button_label,
            copy_confirmation_message=copy_confirmation_message,
            width=width,
            height=height,
        )
