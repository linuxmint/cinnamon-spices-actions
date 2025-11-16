#!/usr/bin/python3
"""
Batch file conversion action.

This module provides the BatchAction class for handling batch file conversions
with progress tracking, error handling, and user notifications. It orchestrates
the complex workflow of validating multiple files, managing output directories,
and processing conversions asynchronously.
"""

from pathlib import Path
from typing import List, Optional

from actions import BaseAction
from converters.base import Converter
from ui import notification
from utils import text
from utils.logging import logger
from utils.validation import FileValidator

from .batch_helpers import (
    BatchErrorHandler,
    BatchFileProcessor,
    BatchStateManager,
    FormatValidator,
    OutputManager,
)


class BatchAction(BaseAction):
    """Batch file conversion action handler.

    Manages the complete workflow for converting multiple files simultaneously
    with progress tracking, error aggregation, and user feedback.

    The batch conversion process includes:
    1. File validation and format compatibility checking
    2. Target format selection for all files
    3. Output directory creation and management
    4. Asynchronous conversion processing with progress tracking
    5. Error aggregation and reporting
    6. Completion notifications and cleanup

    Attributes:
        file_paths: List of file paths provided by the user.
        valid_files: List of validated files that passed all checks.
        target_format: The target format selected for conversion.
        error_handler: Manages error collection and reporting for batch operations.
        file_processor: Handles asynchronous file conversion processing.
        state_manager: Tracks conversion progress and state.
        output_manager: Manages output directory creation and cleanup.

    Examples:
        >>> action = BatchAction(["file1.jpg", "file2.png", "file3.bmp"])
        >>> success = action.run()  # Returns True even if some files fail
    """

    def __init__(self, file_paths: List[str]) -> None:
        """Initialize the batch conversion action.

        Args:
            file_paths: List of file paths to be converted. All files should
                       belong to the same format group (e.g., all images).

        Returns:
            None

        Note:
            File paths are converted to Path objects but not validated until
            run() is called.
        """
        super().__init__()
        self.file_paths = [Path(path) for path in file_paths]
        self.valid_files: List[Path] = []
        self.target_format: Optional[str] = None

        self.error_handler = BatchErrorHandler()
        self.file_processor = BatchFileProcessor()
        self.state_manager: Optional[BatchStateManager] = None
        self.output_manager: Optional[OutputManager] = None

    def run(self) -> bool:
        """Execute the complete batch conversion workflow.

        Orchestrates the entire batch conversion process including validation,
        format selection, output directory setup, and asynchronous processing
        with progress tracking.

        Returns:
            bool: True if the batch process completed (even with individual
                  file failures), False only if the entire process was aborted
                  due to critical errors.

        Raises:
            No exceptions are raised - all errors are handled internally.

        Note:
            Returns True even if some individual files fail to convert, as long
            as the batch process itself completes. Use error_handler to check
            for individual file errors.
        """
        logger.info("Starting batch conversion with {} files", len(self.file_paths))
        logger.debug("Batch files: {}", self.file_paths)
        try:
            if not self._validate_files():
                logger.error("Batch file validation failed")
                return False

            if not self._select_target_format():
                logger.info("User cancelled target format selection")
                return False

            if not self._setup_output_directory():
                logger.error("Failed to setup output directory")
                return False

            self._perform_batch_conversion()
            logger.info("Batch conversion process completed")
            return True

        except Exception as e:
            logger.error("Exception during batch conversion: {}", str(e))
            self._show_unexpected_error(e)
            return False

        finally:
            self.file_processor.shutdown()

    def _validate_files(self) -> bool:
        """Validate all files and ensure format group compatibility.

        Performs comprehensive validation on all input files including:
        - File existence and accessibility
        - Format recognition and support
        - Format group compatibility (all files must be same type)

        Invalid files are filtered out and error messages are collected
        for user display.

        Returns:
            bool: True if validation passes and at least one file is valid,
                  False if no valid files remain or format groups conflict.

        Note:
            Populates self.valid_files with successfully validated files.
            Shows combined error dialog for all validation failures.
        """
        logger.debug("Validating {} batch files", len(self.file_paths))
        if not self.file_paths:
            logger.warning("No file paths provided for batch validation")
            return False

        self.valid_files, format_groups, error_messages = (
            FormatValidator.validate_batch_files(self.file_paths)
        )

        logger.debug(
            "Batch validation results: {} valid files, {} format groups, {} errors",
            len(self.valid_files),
            len(format_groups),
            len(error_messages),
        )

        if error_messages:
            logger.error("Batch validation errors: {}", error_messages)
            combined_errors = "\n".join(f"• {error}" for error in error_messages)
            self._show_error(
                message=text.Validation.ERRORS_MESSAGE.format(
                    error_count=len(error_messages), errors=combined_errors
                )
            )

        compatibility_result = FormatValidator.check_format_groups_compatibility(
            format_groups
        )
        if not compatibility_result:
            logger.warning("Format groups are not compatible for batch conversion")
        else:
            logger.info(
                "Format groups are compatible, proceeding with batch conversion"
            )

        return compatibility_result

    def _select_target_format(self) -> bool:
        """Present format selection dialog for batch conversion.

        Determines the common target formats available for all valid files
        and presents a selection dialog to the user. Uses the first source
        format for dialog labeling.

        Returns:
            bool: True if user selected a target format, False if cancelled
                  or no common formats available.

        Note:
            Sets self.target_format to the selected format.
            Shows error dialog if no conversion options exist.
        """
        if not self.valid_files:
            return False

        source_formats = set()
        for file_path in self.valid_files:
            format_ext = FileValidator.get_file_format(file_path)
            if format_ext:
                source_formats.add(format_ext)

        format_list = FormatValidator.get_common_formats(list(source_formats))
        if not format_list:
            self._show_error(
                message=text.Conversion.NO_CONVERSION_OPTIONS_MESSAGE.format(
                    extension=", ".join(sorted(source_formats)),
                    filename=text.UI.MIXED_FORMATS_PLACEHOLDER,
                )
            )
            return False

        first_format = next(iter(source_formats))
        self.target_format = self._select_format(first_format, format_list)
        return self.target_format is not None

    def _setup_output_directory(self) -> bool:
        """Create and configure the output directory for converted files.

        Creates a timestamped output directory in the same location as the
        source files to contain all converted results.

        Returns:
            bool: True if output directory is ready, False on failure.

        Note:
            Uses the first valid file's directory as the base location.
        """
        if not self.valid_files:
            return False

        base_directory = self.valid_files[0].parent
        self.output_manager = OutputManager(base_directory)

        output_dir = self.output_manager.create_output_directory(len(self.valid_files))
        return output_dir is not None or True

    def _perform_batch_conversion(self) -> None:
        """Execute the batch conversion with progress tracking and notifications.

        Initializes the state manager, starts the progress dialog, and begins
        asynchronous processing of all files with real-time progress updates.

        Returns:
            None

        Note:
            This method blocks until all conversions complete or are cancelled.
            Progress is shown via a modal dialog with cancellation support.
        """
        if not self.valid_files or not self.target_format:
            return

        self.state_manager = BatchStateManager(self.valid_files, self.target_format)
        self.state_manager.set_cancel_callback(self._handle_cancellation)
        self.state_manager.set_progress_update_callback(self._handle_progress_update)

        notification.notify_batch_started(
            extension=self.target_format, total=len(self.valid_files)
        )

        self._start_next_conversion()

        self.state_manager.create_progress_dialog()
        self.state_manager.state.running = True
        self.state_manager.run_progress_dialog()

        self._show_completion_results()

    def _handle_cancellation(self) -> None:
        """Handle user cancellation of the batch conversion.

        Cancels the currently running conversion and prevents starting
        new conversions.

        Returns:
            None
        """
        self.file_processor.cancel_current_conversion()

    def _handle_progress_update(self) -> None:
        """Handle progress updates during batch conversion.

        Checks for completed conversions, processes results, and starts
        the next conversion if available. Updates the progress dialog
        with current status.

        Returns:
            None
        """
        if not self.state_manager:
            return

        if self.file_processor.is_conversion_complete():
            result = self.file_processor.get_conversion_result()
            if result:
                success, converter = result
                self._process_conversion_result(success, converter)
        elif (
            not self.file_processor.current_future
            and not self.state_manager.is_complete()
        ):
            self._start_next_conversion()

    def _process_conversion_result(
        self, success: bool, converter: Optional[Converter]
    ) -> None:
        """Process the result of a completed individual file conversion.

        Updates success/failure counts, sends notifications, and advances
        to the next file in the batch.

        Args:
            success: True if the conversion succeeded, False otherwise.
            converter: The converter instance used for the conversion.

        Returns:
            None
        """
        if not self.state_manager:
            return

        current_file = self.state_manager.get_current_file()
        if not current_file:
            return

        if success:
            self.state_manager.increment_success_count()
            if self.target_format:
                notification.notify_batch_step_success(
                    file_name=current_file.name, extension=self.target_format
                )
        else:
            self._record_conversion_error(current_file, converter)

        self.state_manager.move_to_next_file()

        if not self.state_manager.is_complete():
            self._start_next_conversion()

    def _start_next_conversion(self) -> None:
        """Start conversion of the next file in the batch.

        Retrieves the next file from the state manager and initiates
        its conversion asynchronously.

        Returns:
            None
        """
        if not self.state_manager or not self.target_format:
            return

        next_file = self.state_manager.get_current_file()
        if not next_file:
            return

        def cancel_check() -> bool:
            return self.state_manager.is_cancelled() if self.state_manager else False

        notification.notify_batch_step_start(
            file_name=next_file.name, extension=self.target_format
        )

        self.file_processor.start_conversion(
            next_file,
            self.target_format,
            self.output_manager.get_output_directory() if self.output_manager else None,
            cancel_check,
        )

    def _record_conversion_error(
        self, file_path: Path, converter: Optional[Converter]
    ) -> None:
        """Record a conversion error for reporting and user feedback.

        Extracts error details from the converter and records them
        for later display in the error summary.

        Args:
            file_path: Path to the file that failed conversion.
            converter: The converter instance that failed.

        Returns:
            None
        """
        error_msg = converter.get_last_error() if converter else None
        command = converter.get_last_command() if converter else None

        detailed_error = (
            error_msg if error_msg and error_msg.strip() else "Conversion failed"
        )

        self.error_handler.record_error(
            file_path, detailed_error, command, error_msg, converter
        )

        if (
            self.state_manager
            and not self.state_manager.is_cancelled()
            and self.target_format
        ):
            notification.notify_batch_step_failure(
                file_name=file_path.name, extension=self.target_format
            )

    def _show_completion_results(self) -> None:
        """Display completion notifications and error summaries.

        Sends appropriate completion notifications and shows error dialogs
        if any conversions failed. Handles cleanup of empty output directories.

        Returns:
            None
        """
        if not self.state_manager:
            return

        if self.state_manager.is_cancelled():
            notification.notify_cancelled_conversion(
                extension=self.target_format or "",
                completed=self.state_manager.state.successful_conversions,
                total=len(self.valid_files),
                is_batch=True,
            )
            self._cleanup_empty_output_directory()
        else:
            notification.notify_batch_finished(
                extension=self.target_format or "",
                completed=self.state_manager.state.successful_conversions,
                total=len(self.valid_files),
            )

        if not self.state_manager.is_cancelled() and self.error_handler.has_errors():
            self._show_batch_errors()

    def _cleanup_empty_output_directory(self) -> None:
        """Clean up empty output directory if no files were successfully converted.

        Removes the output directory if it contains no converted files,
        preventing accumulation of empty directories.

        Returns:
            None
        """
        if self.output_manager:
            self.output_manager.cleanup_empty_directory()

    def _show_batch_errors(self) -> None:
        """Display a summary dialog of all conversion errors.

        Shows a formatted error dialog containing details of all failed
        conversions in the batch.

        Returns:
            None
        """
        error_list = self.error_handler.get_formatted_errors()

        self._show_error(
            message=text.Operations.BATCH_CONVERSION_COMPLETED_WITH_ERRORS_MESSAGE.format(
                error_count=self.error_handler.get_error_count()
            ),
            details=text.Errors.FAILED_CONVERSIONS_PLACEHOLDER.format(
                errors=error_list
            ),
        )
