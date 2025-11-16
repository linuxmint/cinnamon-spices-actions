#!/usr/bin/python3
"""
State management for batch conversions.

This module provides consolidated state tracking and progress UI management
for batch file conversion operations.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from ui import Gtk, ProgressbarDialogWindow
from utils import text
from utils.logging import logger


@dataclass
class BatchConversionState:
    """Core state data for batch conversion tracking.

    Data class containing the essential state information for
    tracking progress during batch file conversion operations.

    Attributes:
        current_index: Index of the currently processing file (0-based).
        successful_conversions: Number of files successfully converted.
        cancelled: True if the batch operation was cancelled by user.
        cancelling: True if cancellation is in progress.
        running: True if the batch conversion is currently active.

    Examples:
        >>> state = BatchConversionState(current_index=5, successful_conversions=4)
        >>> print(f"Processing file {state.current_index + 1}")
    """

    current_index: int = 0
    successful_conversions: int = 0
    cancelled: bool = False
    cancelling: bool = False
    running: bool = False


class BatchStateManager:
    """Consolidated state management and progress UI for batch conversions.

    Combines state tracking and progress dialog management into a single,
    cohesive component for batch file conversion operations. Handles progress
    updates, cancellation detection, and UI responsiveness during batch processing.

    Attributes:
        CANCELLING_TIMEOUT_COUNTER: Initial value for cancellation timeout counter.
        MAX_CANCELLING_TIMEOUTS: Maximum timeouts to wait during cancellation.
        PROGRESS_UPDATE_TIMEOUT_MS: Milliseconds between progress updates.
        valid_files: List of files being processed in the batch.
        target_format: Target format for all conversions.
        state: Current batch conversion state.
        _progress_window: GTK progress dialog window instance.

    Examples:
        >>> files = [Path("/tmp/video1.mp4"), Path("/tmp/video2.mp4")]
        >>> manager = BatchStateManager(files, "MP3")
        >>> manager.create_progress_dialog()
        >>> # ... run batch conversion ...
        >>> manager.run_progress_dialog()
    """

    CANCELLING_TIMEOUT_COUNTER = 0
    MAX_CANCELLING_TIMEOUTS = 50
    PROGRESS_UPDATE_TIMEOUT_MS = 10

    def __init__(self, valid_files: List[Path], target_format: str) -> None:
        """Initialize the batch state manager.

        Args:
            valid_files: List of validated file paths for batch processing.
            target_format: Target format string for all conversions (e.g., "MP3").

        Examples:
            >>> files = [Path("/tmp/test1.mp4"), Path("/tmp/test2.mp4")]
            >>> manager = BatchStateManager(files, "AVI")
            >>> print(f"Processing {len(manager.valid_files)} files to {manager.target_format}")
        """
        self.valid_files = valid_files
        self.target_format = target_format
        self.state = BatchConversionState()
        self._progress_window: Optional[ProgressbarDialogWindow] = None
        self._cancelling_timeout_counter = self.CANCELLING_TIMEOUT_COUNTER
        self._max_cancelling_timeouts = self.MAX_CANCELLING_TIMEOUTS
        self._progress_update_timeout_ms = self.PROGRESS_UPDATE_TIMEOUT_MS

        self._on_cancel_callback: Optional[Callable[[], None]] = None
        self._on_progress_update_callback: Optional[Callable[[], None]] = None

    def set_cancel_callback(self, callback: Callable[[], None]) -> None:
        """Set callback to be called when conversion is cancelled.

        Args:
            callback: Function to call when batch conversion is cancelled.
                     Should handle cleanup and state updates.

        Examples:
            >>> def on_cancel():
            ...     print("Batch conversion cancelled")
            >>> manager.set_cancel_callback(on_cancel)
        """
        self._on_cancel_callback = callback

    def set_progress_update_callback(self, callback: Callable[[], None]) -> None:
        """Set callback to be called on progress updates.

        Args:
            callback: Function to call during progress updates.
                     Typically used to update conversion state.

        Examples:
            >>> def on_progress():
            ...     print("Progress update")
            >>> manager.set_progress_update_callback(on_progress)
        """
        self._on_progress_update_callback = callback

    def create_progress_dialog(self) -> None:
        """Create and configure the progress dialog.

        Initializes the GTK progress dialog with initial message and timeout
        callback for real-time progress updates during batch conversion.

        Examples:
            >>> manager = BatchStateManager([Path("/tmp/file.mp4")], "MP3")
            >>> manager.create_progress_dialog()
            >>> # Dialog is now ready to display progress
        """
        logger.debug(
            "Creating progress dialog for batch conversion of {} files to {}",
            len(self.valid_files),
            self.target_format,
        )
        self._progress_window = ProgressbarDialogWindow(
            message=text.Conversion.BATCH_CONVERSION_PROGRESS_MESSAGE.format(
                file=self.valid_files[0].name,
                extension=self.target_format,
                current=1,
                total=len(self.valid_files),
            ),
            timeout_callback=self._handle_progress_timeout,
            timeout_ms=self._progress_update_timeout_ms,
        )

        if self._progress_window:
            self._progress_window.progressbar.set_fraction(0.0)
            self._setup_dialog_event_handlers()
            logger.debug("Progress dialog created and configured")

    def _setup_dialog_event_handlers(self) -> None:
        """Set up event handlers for the progress dialog.

        Configures GTK signal handlers for dialog response and delete events
        to properly handle user cancellation requests.
        """
        if not self._progress_window:
            return

        def on_response(dialog, response_id) -> None:
            if response_id in (
                Gtk.ResponseType.CANCEL,
                Gtk.ResponseType.DELETE_EVENT,
            ):
                self.state.cancelled = True
                self.state.cancelling = True
                self.state.running = False

                if self._on_cancel_callback:
                    self._on_cancel_callback()

                self._handle_cancellation_ui()

        self._progress_window.dialog.connect("response", on_response)

        def on_delete_event(dialog, event) -> bool:
            self.state.cancelled = True
            self.state.cancelling = True
            self.state.running = False

            if self._on_cancel_callback:
                self._on_cancel_callback()

            self._handle_cancellation_ui()
            return False

        self._progress_window.dialog.connect("delete-event", on_delete_event)

    def run_progress_dialog(self) -> None:
        """Run the progress dialog and handle completion.

        Starts the GTK dialog main loop and waits for completion or cancellation.
        Automatically destroys the dialog when finished.

        Examples:
            >>> manager.create_progress_dialog()
            >>> manager.run_progress_dialog()  # Blocks until completion
        """
        if self._progress_window:
            self._progress_window.run()
            self._progress_window.destroy()

    def _handle_progress_timeout(self, _, progress_window) -> bool:
        """Handle progress timeout callback.

        Called periodically by GTK to update progress and handle state changes.
        Manages the conversion lifecycle including cancellation and completion.

        Args:
            _: Unused timeout source parameter.
            progress_window: The progress dialog window instance.

        Returns:
            bool: True to continue timeout callbacks, False to stop.

        Examples:
            >>> # Called automatically by GTK timeout mechanism
            >>> continue_updates = manager._handle_progress_timeout(None, window)
        """
        if self.state.cancelling:
            return self._handle_cancellation_timeout()

        if self.state.cancelled:
            self.state.running = False
            return False

        if not self.state.running or not self.target_format:
            return False

        if self.state.current_index < len(self.valid_files):
            return self._handle_active_conversion(progress_window)
        else:
            return self._handle_all_files_completed(progress_window)

    def _handle_cancellation_timeout(self) -> bool:
        """Handle timeout during cancellation.

        Manages the waiting period during cancellation to allow running
        conversions to complete gracefully before forcing cleanup.

        Returns:
            bool: True to continue waiting, False to force completion.

        Examples:
            >>> # Called during cancellation process
            >>> should_continue = manager._handle_cancellation_timeout()
        """
        self._cancelling_timeout_counter += 1

        if self._cancelling_timeout_counter >= self._max_cancelling_timeouts:
            if self._progress_window:
                self._progress_window.dialog.emit("response", Gtk.ResponseType.CANCEL)
            return False

        if self._progress_window:
            self._progress_window.progressbar.pulse()
        return True

    def _handle_active_conversion(self, progress_window) -> bool:
        """Handle active conversion progress.

        Updates the progress display and triggers progress callbacks
        during active file conversion.

        Args:
            progress_window: The progress dialog window instance.

        Returns:
            bool: True to continue processing, False to stop.

        Examples:
            >>> # Called when files are being actively converted
            >>> continue_processing = manager._handle_active_conversion(window)
        """
        self._update_progress_display(progress_window)

        if (
            hasattr(self, "_on_progress_update_callback")
            and self._on_progress_update_callback
        ):
            progress_window.progressbar.pulse()

        if self._on_progress_update_callback:
            self._on_progress_update_callback()

        return True

    def _handle_all_files_completed(self, progress_window) -> bool:
        """Handle completion of all files.

        Signals completion of the batch conversion and closes the progress dialog.

        Args:
            progress_window: The progress dialog window instance.

        Returns:
            bool: False to stop progress updates (conversion complete).

        Examples:
            >>> # Called when all files have been processed
            >>> finished = manager._handle_all_files_completed(window)
            >>> print(f"Batch complete: {not finished}")
        """
        self.state.running = False
        progress_window.dialog.emit("response", Gtk.ResponseType.OK)
        return False

    def _update_progress_display(self, progress_window) -> None:
        """Update progress bar and message.

        Updates the GTK progress bar fraction and message text to reflect
        current conversion progress.

        Args:
            progress_window: The progress dialog window instance.

        Raises:
            Exception: If batch conversion was cancelled by user.

        Examples:
            >>> # Called to refresh progress display
            >>> manager._update_progress_display(window)
        """
        progress_fraction = self.state.current_index / len(self.valid_files)
        progress_window.progressbar.set_fraction(progress_fraction)
        progress_window.set_message(
            text.Conversion.BATCH_CONVERSION_PROGRESS_MESSAGE.format(
                file=self.valid_files[self.state.current_index].name,
                extension=self.target_format,
                current=self.state.current_index + 1,
                total=len(self.valid_files),
            )
        )

        while Gtk.events_pending():
            Gtk.main_iteration()
        time.sleep(0.1)

        if self.state.cancelled:
            raise Exception(text.Operations.BATCH_CONVERSION_CANCELLED_MESSAGE)

    def _handle_cancellation_ui(self) -> None:
        """Update UI to show cancellation is in progress.

        Modifies the progress dialog to indicate cancellation is in progress,
        disabling the cancel button and updating its label.

        Examples:
            >>> # Called when user cancels the batch operation
            >>> manager._handle_cancellation_ui()
        """
        if not self._progress_window:
            return

        action_area = self._progress_window.dialog.get_action_area()
        if action_area:
            buttons = action_area.get_children()
            for button in buttons:
                if isinstance(button, Gtk.Button):
                    label = button.get_label()
                    if label == text.UI.CANCEL_BUTTON_LABEL:
                        button.set_label(text.UI.CANCELLING_BUTTON_LABEL)
                        button.set_sensitive(False)
                        break

        while Gtk.events_pending():
            Gtk.main_iteration()

    def is_cancelled(self) -> bool:
        """Check if the conversion has been cancelled.

        Returns:
            bool: True if the batch conversion was cancelled by the user.

        Examples:
            >>> if manager.is_cancelled():
            ...     print("Batch was cancelled")
        """
        return self.state.cancelled

    def increment_success_count(self) -> None:
        """Increment the successful conversions counter.

        Updates the internal state to reflect a successful file conversion.

        Examples:
            >>> manager.increment_success_count()
            >>> print(f"Successful: {manager.state.successful_conversions}")
        """
        self.state.successful_conversions += 1
        logger.debug(
            "Incremented success count to {}", self.state.successful_conversions
        )

    def move_to_next_file(self) -> None:
        """Move to the next file in the batch.

        Advances the current file index for processing the next file in the batch.

        Examples:
            >>> manager.move_to_next_file()
            >>> next_file = manager.get_current_file()
        """
        self.state.current_index += 1
        logger.debug("Moved to next file, current index: {}", self.state.current_index)

    def get_current_file(self) -> Optional[Path]:
        """Get the current file being processed.

        Returns:
            Optional[Path]: Path to the currently processing file, or None if
                           all files have been processed.

        Examples:
            >>> current = manager.get_current_file()
            >>> if current:
            ...     print(f"Processing: {current.name}")
        """
        if self.state.current_index < len(self.valid_files):
            return self.valid_files[self.state.current_index]
        return None

    def is_complete(self) -> bool:
        """Check if all files have been processed.

        Returns:
            bool: True if all files in the batch have been processed,
                  False if more files remain.

        Examples:
            >>> if manager.is_complete():
            ...     print("Batch conversion finished")
        """
        return self.state.current_index >= len(self.valid_files)
