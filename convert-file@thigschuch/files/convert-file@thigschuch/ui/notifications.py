#!/usr/bin/python3
"""
NotificationService for desktop notifications.

This module provides a centralized notification system with consistent formatting,
icons, and urgency levels for conversion operations.
"""

import contextlib
import subprocess

from config.settings import settings_manager
from utils import text
from utils.logging import logger

from .icons import get_notification_icon


class NotificationService:
    """Service for sending desktop notifications related to file conversion operations.

    Provides a centralized way to send consistent, user-friendly notifications
    with appropriate icons, urgency levels, and formatting. All notifications
    respect user settings for enabling/disabling specific notification types.

    Class Attributes:
        settings: Dictionary of notification settings from configuration.
        icon: Default notification icon path or fallback icon name.

    Examples:
        >>> NotificationService.notify_conversion_success("example.jpg", "PNG")
        >>> NotificationService.notify_batch_started("JPEG", 5)
    """

    settings: dict = settings_manager.get("notifications", {})
    _icon: str = get_notification_icon() or "gtk-convert"

    @classmethod
    def send_notification(
        cls, title: str, message: str, urgency: str = "normal", icon: str = ""
    ) -> None:
        """Send a desktop notification using notify-send.

        Sends a desktop notification with the specified parameters. Respects
        global notification settings and handles errors gracefully.

        Args:
            title: The notification title text.
            message: The notification body message.
            urgency: Urgency level - "low", "normal", or "critical".
            icon: Custom icon path (uses default if empty).

        Returns:
            None

        Note:
            Silently fails if notifications are disabled or notify-send unavailable.
        """
        logger.debug("Sending notification: {} - {}", title, message)
        if not cls.settings.get("enabled", True):
            logger.debug("Notifications disabled, skipping")
            return

        if not icon:
            icon = cls._icon

        with contextlib.suppress(FileNotFoundError, subprocess.SubprocessError):
            subprocess.Popen(
                [
                    "notify-send",
                    f"--icon={icon}",
                    f"--urgency={urgency}",
                    f"--app-name={text.UI.APPLICATION_TITLE}",
                    title,
                    message,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.debug("Notification sent successfully")

    @classmethod
    def _notify(
        cls, setting_key: str, title: str, message: str, urgency: str = "normal"
    ) -> None:
        """Send notification if the specific setting is enabled.

        Internal helper method that checks individual notification settings
        before sending notifications.

        Args:
            setting_key: Configuration key to check for enablement.
            title: Notification title text.
            message: Notification body message.
            urgency: Urgency level for the notification.

        Returns:
            None
        """
        if not cls.settings.get(setting_key, True):
            return
        cls.send_notification(title, message, urgency)

    @classmethod
    def notify_missing_dependency(cls, dependency_name: str) -> None:
        """Notify about a missing system dependency.

        Sends a notification when a required tool or library is not found
        on the system, prompting the user to install it.

        Args:
            dependency_name: Name of the missing dependency/tool.

        Returns:
            None

        Examples:
            >>> NotificationService.notify_missing_dependency("ffmpeg")
        """
        cls._notify(
            "on_missing_dependency",
            text.Notifications.MISSING_TOOL_TITLE,
            text.Notifications.MISSING_TOOL_MESSAGE.format(tool=dependency_name),
        )

    @classmethod
    def notify_cancelled_conversion(
        cls, extension: str, completed: int = 0, total: int = 0, is_batch: bool = False
    ) -> None:
        """Notify about a cancelled conversion operation.

        Sends appropriate cancellation notification for single or batch conversions,
        including progress information for batch operations.

        Args:
            extension: Target file format extension.
            completed: Number of successfully completed conversions (batch only).
            total: Total number of files in batch (batch only).
            is_batch: Whether this is a batch conversion cancellation.

        Returns:
            None

        Examples:
            >>> NotificationService.notify_cancelled_conversion("PNG")
            >>> NotificationService.notify_cancelled_conversion("JPEG", 3, 5, True)
        """
        if is_batch:
            cls._notify(
                "on_batch_cancel",
                text.Notifications.BATCH_CONVERSION_CANCELLED_TITLE,
                text.Notifications.BATCH_CONVERSION_CANCELLED_MESSAGE.format(
                    completed=completed,
                    total=total,
                    extension=extension,
                ),
            )
            return

        cls._notify(
            "on_cancel",
            text.Notifications.SINGLE_CONVERSION_CANCELLED_TITLE,
            text.Notifications.SINGLE_CONVERSION_CANCELLED_MESSAGE.format(
                extension=extension
            ),
        )

    @classmethod
    def notify_conversion_started(
        cls, file_name: str = "", extension: str = ""
    ) -> None:
        """Notify about the start of a conversion operation.

        Sends a notification when a file conversion begins, showing the
        target format and optionally the filename.

        Args:
            file_name: Name of the file being converted (optional).
            extension: Target file format extension.

        Returns:
            None

        Examples:
            >>> NotificationService.notify_conversion_started("photo.jpg", "PNG")
        """
        cls._notify(
            "on_start",
            text.Notifications.CONVERSION_STARTED_TITLE,
            text.Notifications.CONVERSION_STARTED_MESSAGE.format(
                filename=file_name, extension=extension
            ),
        )

    @classmethod
    def notify_conversion_success(cls, file_name: str, extension: str) -> None:
        """Notify about a successful conversion.

        Sends a success notification when a file conversion completes
        successfully, showing the filename and target format.

        Args:
            file_name: Name of the successfully converted file.
            extension: Target file format extension.

        Returns:
            None

        Examples:
            >>> NotificationService.notify_conversion_success("document.pdf", "DOCX")
        """
        cls._notify(
            "on_success",
            text.Notifications.SUCCESS_TITLE,
            text.Notifications.SUCCESS_MESSAGE.format(
                filename=file_name, extension=extension
            ),
        )

    @classmethod
    def notify_conversion_failure(cls, file_name: str, extension: str) -> None:
        """Notify about a failed conversion.

        Sends a failure notification when a file conversion fails,
        showing the filename and attempted target format.

        Args:
            file_name: Name of the file that failed to convert.
            extension: Target file format extension that was attempted.

        Returns:
            None

        Examples:
            >>> NotificationService.notify_conversion_failure("corrupt.jpg", "PNG")
        """
        cls._notify(
            "on_failure",
            text.Notifications.FAILURE_TITLE,
            text.Notifications.FAILURE_MESSAGE.format(
                filename=file_name,
                extension=extension,
            ),
        )

    @classmethod
    def notify_batch_finished(cls, extension: str, completed: int, total: int) -> None:
        """Notify about completion of a batch conversion.

        Sends a summary notification for batch conversion completion,
        showing success/failure statistics and target format.

        Args:
            extension: Target file format extension for the batch.
            completed: Number of successfully converted files.
            total: Total number of files processed in the batch.

        Returns:
            None

        Note:
            Automatically determines success vs partial failure based on completion count.

        Examples:
            >>> NotificationService.notify_batch_finished("PNG", 5, 5)  # All successful
            >>> NotificationService.notify_batch_finished("JPEG", 3, 5)  # Some failed
        """
        total_count = completed + (total - completed)
        failed_conversions = total_count - completed

        if failed_conversions == 0:
            title = text.Notifications.BATCH_SUCCESS_TITLE
            message = text.Notifications.BATCH_SUCCESS_MESSAGE.format(
                successful=completed, total=total_count, extension=extension
            )
        else:
            title = text.Notifications.BATCH_FAILURE_TITLE
            message = text.Notifications.BATCH_FAILURE_MESSAGE.format(
                failed=failed_conversions, total=total_count, extension=extension
            )

        cls._notify(
            "on_batch_finish",
            title,
            message,
        )

    @classmethod
    def notify_batch_started(cls, extension: str, total: int = 0) -> None:
        """Notify about the start of a batch conversion.

        Sends a notification when a batch conversion begins, showing
        the target format and total number of files.

        Args:
            extension: Target file format extension for the batch.
            total: Total number of files to be processed.

        Returns:
            None

        Examples:
            >>> NotificationService.notify_batch_started("PNG", 10)
        """
        cls._notify(
            "on_batch_start",
            text.Notifications.BATCH_CONVERSION_STARTED_TITLE,
            text.Notifications.BATCH_CONVERSION_STARTED_MESSAGE.format(
                extension=extension,
                total=total,
            ),
        )

    @classmethod
    def notify_batch_step_start(cls, file_name: str, extension: str) -> None:
        """Notify about the start of an individual batch step.

        Sends a notification when processing of a specific file begins
        within a batch conversion operation.

        Args:
            file_name: Name of the file currently being processed.
            extension: Target file format extension.

        Returns:
            None

        Examples:
            >>> NotificationService.notify_batch_step_start("image1.jpg", "PNG")
        """
        cls._notify(
            "on_batch_step_start",
            text.Notifications.BATCH_STEP_CONVERSION_STARTED_TITLE,
            text.Notifications.BATCH_STEP_CONVERSION_STARTED_MESSAGE.format(
                filename=file_name, extension=extension
            ),
        )

    @classmethod
    def notify_batch_step_success(cls, file_name: str, extension: str) -> None:
        """Notify about successful completion of a batch step.

        Sends a success notification for an individual file within a
        batch conversion that completed successfully.

        Args:
            file_name: Name of the successfully converted file.
            extension: Target file format extension.

        Returns:
            None

        Examples:
            >>> NotificationService.notify_batch_step_success("photo.jpg", "PNG")
        """
        cls._notify(
            "on_batch_step_success",
            text.Notifications.SUCCESS_TITLE,
            text.Notifications.SUCCESS_MESSAGE.format(
                filename=file_name, extension=extension
            ),
        )

    @classmethod
    def notify_batch_step_failure(cls, file_name: str, extension: str) -> None:
        """Notify about failure of a batch step.

        Sends a failure notification for an individual file within a
        batch conversion that failed to convert.

        Args:
            file_name: Name of the file that failed to convert.
            extension: Target file format extension that was attempted.

        Returns:
            None

        Examples:
            >>> NotificationService.notify_batch_step_failure("corrupt.jpg", "PNG")
        """
        cls._notify(
            "on_batch_step_failure",
            text.Notifications.FAILURE_TITLE,
            text.Notifications.FAILURE_MESSAGE.format(
                filename=file_name,
                extension=extension,
            ),
        )

    @classmethod
    def notify_corrupted_user_settings(cls) -> None:
        """Notify about corrupted user settings file.

        Sends a notification when the user's settings file is found to be
        corrupted or unreadable, prompting them to check their configuration.

        Returns:
            None

        Examples:
            >>> NotificationService.notify_corrupted_user_settings()
        """
        cls._notify(
            "on_settings_corrupted",
            text.Notifications.USER_SETTINGS_CORRUPTED_TITLE,
            text.Notifications.USER_SETTINGS_CORRUPTED_MESSAGE,
        )


notification = NotificationService()
