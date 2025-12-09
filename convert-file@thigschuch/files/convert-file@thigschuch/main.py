#!/usr/bin/env python3
"""
Convert File - Nemo Action for File Conversion.

This module serves as the main entry point for the Convert File Nemo action,
providing a unified interface for both single file and batch file conversions.

The application supports conversion between various file formats including:
- Images (JPEG, PNG, GIF, BMP, TIFF, WebP, etc.)
- Videos (MP4, AVI, MKV, MOV, WebM, etc.)
- Audio files (MP3, WAV, FLAC, OGG, AAC, etc.)
- Documents (PDF, DOCX, HTML, TXT, etc.)
- Archives (ZIP, TAR, 7Z, RAR, etc.)

Features:
- Single file conversion with format selection dialog
- Batch conversion for multiple files of the same type
- Progress tracking and cancellation support
- Comprehensive error handling and user notifications
- Configurable conversion templates and settings
- Cross-platform compatibility (Linux-focused)

Usage:
    python main.py <file_path> [file_path2 ...]

Examples:
    # Convert single image
    python main.py image.jpg

    # Convert multiple images to PNG
    python main.py image1.jpg image2.bmp image3.tiff

    # Convert video file
    python main.py video.mp4

Note:
    For batch conversions, all files must belong to the same format group
    (e.g., all images, all videos, etc.).
"""

import sys
import traceback
from pathlib import Path
from typing import List

from actions import Action, BatchAction
from ui import InfoDialogWindow
from utils import text
from utils.logging import logger


def main() -> None:
    """Main entry point for the Convert File application.

    Parses command-line arguments and executes the appropriate conversion workflow
    based on the number of files provided. Handles both single file and batch
    conversions with proper validation and error handling.

    Command-line Usage:
        python main.py <file_path> [file_path2 ...]

    Args:
        None (reads from sys.argv)

    Returns:
        None

    Raises:
        SystemExit: With code 1 if invalid usage or conversion fails

    Examples:
        >>> # Single file conversion
        >>> main()  # When sys.argv = ['main.py', 'document.pdf']

        >>> # Batch conversion
        >>> main()  # When sys.argv = ['main.py', 'image1.jpg', 'image2.png']
    """
    logger.info("Convert File application started")
    logger.debug("Command line arguments: {}", sys.argv)

    if len(sys.argv) < 2:
        logger.error("Invalid usage: no file paths provided")
        dialog = InfoDialogWindow(message=text.Validation.INVALID_USAGE_MESSAGE)
        dialog.run()
        dialog.destroy()
        sys.exit(1)

    file_paths: List[str] = sys.argv[1:]
    logger.debug("Processing {} file(s): {}", len(file_paths), file_paths)

    try:
        if len(file_paths) == 1:
            logger.info("Starting single file conversion")
            action = Action(Path(file_paths[0]))

        else:
            logger.info("Starting batch conversion with {} files", len(file_paths))
            action = BatchAction(file_paths)

        action.run()
        logger.info("Conversion action completed successfully")

    except Exception as e:
        logger.error("Conversion failed with error: {}", str(e))
        logger.error("Traceback:\n{}", traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
