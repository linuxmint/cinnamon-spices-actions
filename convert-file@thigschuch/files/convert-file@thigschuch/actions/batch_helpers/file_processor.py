#!/usr/bin/python3
"""
File processing for batch conversions.

This module handles individual file conversion logic for batch
operations using a simplified threading model.
"""

from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import suppress
from pathlib import Path
from typing import Callable, Optional, Tuple

from converters.base import Converter
from core import ConverterFactory


class BatchFileProcessor:
    """Handles individual file conversion logic for batch operations.

    Uses ThreadPoolExecutor for cleaner asynchronous processing and provides
    cancellation support. Manages single-file conversions within batch operations
    with proper error handling and resource cleanup.

    Attributes:
        MAX_WORKERS: Maximum number of worker threads (default: 1).
        THREAD_NAME_PREFIX: Prefix for thread naming in the pool.
        max_workers: Configured maximum number of worker threads.
        executor: ThreadPoolExecutor instance for asynchronous processing.
        current_future: Currently executing conversion future.
        current_converter: Currently active converter instance.

    Examples:
        >>> processor = BatchFileProcessor()
        >>> processor.start_conversion(
        ...     Path("/tmp/video.mp4"),
        ...     "MP3",
        ...     output_dir=Path("/tmp/output")
        ... )
        >>> while not processor.is_conversion_complete():
        ...     pass  # Wait for completion
        >>> result = processor.get_conversion_result()
        >>> print(f"Conversion successful: {result[0] if result else False}")
    """

    MAX_WORKERS = 1
    THREAD_NAME_PREFIX = "batch-convert"

    def __init__(self, max_workers: Optional[int] = None) -> None:
        """Initialize the batch file processor.

        Creates a ThreadPoolExecutor with the specified number of workers
        for handling asynchronous file conversions.

        Args:
            max_workers: Maximum number of worker threads. If None, uses
                        MAX_WORKERS class constant (default: 1).

        Examples:
            >>> processor = BatchFileProcessor(max_workers=2)
            >>> print(f"Workers: {processor.max_workers}")  # 2
        """
        if max_workers is None:
            max_workers = self.MAX_WORKERS
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix=self.THREAD_NAME_PREFIX
        )
        self.current_future: Optional[Future] = None
        self.current_converter: Optional[Converter] = None

    def __del__(self) -> None:
        """Clean up the thread pool executor.

        Ensures the ThreadPoolExecutor is properly shut down when the
        processor instance is garbage collected.
        """
        self.executor.shutdown(wait=False)

    def start_conversion(
        self,
        file_path: Path,
        target_format: str,
        output_dir: Optional[Path] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> None:
        """Start asynchronous conversion of a single file.

        Initiates a background conversion process for the specified file.
        Cancels any currently running conversion before starting the new one.

        Args:
            file_path: Path to the file to convert.
            target_format: Target format for conversion (e.g., "MP3", "JPEG").
            output_dir: Optional output directory for batch mode. If None,
                       uses the same directory as the input file.
            cancel_check: Optional callable that returns True if conversion
                         should be cancelled. Called periodically during
                         conversion.

        Examples:
            >>> processor = BatchFileProcessor()
            >>> def should_cancel():
            ...     return False  # Never cancel
            >>> processor.start_conversion(
            ...     Path("/tmp/video.mp4"),
            ...     "MP3",
            ...     output_dir=Path("/tmp/output"),
            ...     cancel_check=should_cancel
            ... )
        """
        self.cancel_current_conversion()

        self.current_converter = ConverterFactory.create_converter(
            file_path,
            target_format,
            batch_mode=True,
            output_dir=output_dir,
            cancel_check=cancel_check,
        )

        if not self.current_converter:
            self.current_future = self.executor.submit(lambda: (False, None))
            return

        self.current_future = self.executor.submit(
            self._convert_file, self.current_converter
        )

    def _convert_file(self, converter: Converter) -> Tuple[bool, Converter]:
        """Convert a single file synchronously.

        Internal method that performs the actual file conversion in a worker thread.
        Handles exceptions and returns the conversion result.

        Args:
            converter: The converter instance to use for the conversion.

        Returns:
            Tuple[bool, Converter]: A tuple containing:
                - bool: True if conversion succeeded, False otherwise.
                - Converter: The converter instance used for conversion.

        Examples:
            >>> processor = BatchFileProcessor()
            >>> converter = ConverterFactory.create_converter(Path("/tmp/test.mp4"), "MP3")
            >>> if converter:
            ...     result = processor._convert_file(converter)
            ...     print(f"Success: {result[0]}")
        """
        try:
            success = converter.convert()
            return success, converter
        except Exception:
            return False, converter

    def is_conversion_complete(self) -> bool:
        """Check if the current conversion is complete.

        Determines whether the currently running conversion has finished,
        either successfully or with an error.

        Returns:
            bool: True if conversion is finished (successfully or with error),
                  False if still running or no conversion in progress.

        Examples:
            >>> processor = BatchFileProcessor()
            >>> processor.start_conversion(Path("/tmp/video.mp4"), "MP3")
            >>> # Wait a bit...
            >>> if processor.is_conversion_complete():
            ...     result = processor.get_conversion_result()
            ...     print(f"Done: {result is not None}")
        """
        return self.current_future is not None and self.current_future.done()

    def get_conversion_result(self) -> Optional[Tuple[bool, Optional[Converter]]]:
        """Get the result of the completed conversion.

        Retrieves the result of a finished conversion. Should only be called
        after is_conversion_complete() returns True.

        Returns:
            Optional[Tuple[bool, Optional[Converter]]]: A tuple containing:
                - bool: True if conversion succeeded, False otherwise.
                - Optional[Converter]: The converter instance used, or None if
                  converter creation failed.
                Returns None if no conversion is complete or running.

        Examples:
            >>> processor = BatchFileProcessor()
            >>> processor.start_conversion(Path("/tmp/video.mp4"), "MP3")
            >>> while not processor.is_conversion_complete():
            ...     pass  # Wait for completion
            >>> result = processor.get_conversion_result()
            >>> if result:
            ...     success, converter = result
            ...     print(f"Conversion {'succeeded' if success else 'failed'}")
        """
        if not self.is_conversion_complete() or not self.current_future:
            return None

        try:
            success, converter = self.current_future.result(timeout=0.1)
            return success, converter
        except Exception:
            return False, self.current_converter
        finally:
            self.current_future = None
            self.current_converter = None

    def cancel_current_conversion(self) -> None:
        """Cancel the currently running conversion.

        Attempts to cancel the active conversion by calling the converter's
        cancel method and cancelling the future. Cleans up internal state.

        Examples:
            >>> processor = BatchFileProcessor()
            >>> processor.start_conversion(Path("/tmp/video.mp4"), "MP3")
            >>> processor.cancel_current_conversion()  # Cancel immediately
        """
        if self.current_converter:
            with suppress(Exception):
                self.current_converter.cancel()

        if self.current_future and not self.current_future.done():
            self.current_future.cancel()

        self.current_future = None
        self.current_converter = None

    def shutdown(self) -> None:
        """Shutdown the processor and clean up resources.

        Cancels any running conversion and shuts down the ThreadPoolExecutor.
        Should be called when the processor is no longer needed.

        Examples:
            >>> processor = BatchFileProcessor()
            >>> # ... use processor ...
            >>> processor.shutdown()  # Clean shutdown
        """
        self.cancel_current_conversion()
        self.executor.shutdown(wait=True)
