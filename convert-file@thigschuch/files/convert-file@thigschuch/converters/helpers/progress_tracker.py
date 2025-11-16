#!/usr/bin/python3
"""
Progress tracking utilities for converters.

This module provides progress tracking and cancellation management
for converter operations.
"""

from typing import Callable, Optional


class ProgressTracker:
    """Tracks conversion progress and handles cancellation.

    Provides centralized progress tracking and cancellation callback
    management for converter operations. Supports both internal cancellation
    state and external cancellation checks for coordinated operation control.

    Attributes:
        _cancelled: Internal flag indicating if operation was cancelled.
        _external_cancel_check: Optional external callback for cancellation checks.

    Examples:
        >>> def external_check():
        ...     return False  # Not cancelled
        >>> tracker = ProgressTracker(external_check)
        >>> cancel_check = tracker.create_cancel_check()
        >>> if cancel_check():
        ...     print("Operation cancelled")
    """

    def __init__(
        self, external_cancel_check: Optional[Callable[[], bool]] = None
    ) -> None:
        """Initialize the progress tracker.

        Args:
            external_cancel_check: Optional callback function that returns True
                                 if the operation should be cancelled externally.
        """
        self._cancelled = False
        self._external_cancel_check = external_cancel_check

    def cancel(self) -> None:
        """Mark the conversion as cancelled.

        Sets the internal cancellation flag to True, indicating that
        the current operation should be stopped.

        Examples:
            >>> tracker = ProgressTracker()
            >>> tracker.cancel()
            >>> cancel_check = tracker.create_cancel_check()
            >>> print(cancel_check())  # True
            True
        """
        self._cancelled = True

    def reset(self) -> None:
        """Reset the cancellation state.

        Clears the internal cancellation flag, allowing operations
        to proceed normally again.

        Examples:
            >>> tracker = ProgressTracker()
            >>> tracker.cancel()
            >>> tracker.reset()
            >>> cancel_check = tracker.create_cancel_check()
            >>> print(cancel_check())  # False
            False
        """
        self._cancelled = False

    def create_cancel_check(self) -> Callable[[], bool]:
        """Create a cancel check function for external use.

        Returns a function that can be called repeatedly to check if
        the operation has been cancelled, either internally or externally.

        Returns:
            Callable[[], bool]: A function that returns True if the operation
                               has been cancelled, False otherwise.

        Examples:
            >>> tracker = ProgressTracker()
            >>> cancel_check = tracker.create_cancel_check()
            >>> # Use in a loop
            >>> while not cancel_check():
            ...     # Do work
            ...     pass
        """

        def cancel_check() -> bool:
            if self._cancelled:
                return True
            if self._external_cancel_check and self._external_cancel_check():
                return True
            return False

        return cancel_check

    def create_cancel_callback(self) -> Callable[[], None]:
        """Create a cancel callback function for external use.

        Returns a function that can be called to cancel the operation.
        Useful for connecting to UI elements or external cancellation sources.

        Returns:
            Callable[[], None]: A function that cancels the operation when called.

        Examples:
            >>> tracker = ProgressTracker()
            >>> cancel_callback = tracker.create_cancel_callback()
            >>> # Connect to a button click
            >>> button.connect("clicked", cancel_callback)
        """

        def cancel_callback() -> None:
            self._cancelled = True

        return cancel_callback
