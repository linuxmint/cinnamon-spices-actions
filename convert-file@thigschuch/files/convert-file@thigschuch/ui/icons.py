#!/usr/bin/python3
"""
Icon and window management utilities for the file converter.

This module provides utilities for setting window icons and application names
to ensure consistent branding across all dialogs and notifications.
"""

import contextlib
import os
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Optional

from utils import text
from utils.logging import logger

from .gi import GLib, Gtk

_app_initialized = False


def _ensure_app_initialized() -> None:
    """Ensure GTK application is initialized with icon and name."""
    global _app_initialized
    if not _app_initialized:
        set_application_icon()
        set_application_name()
        _app_initialized = True


@lru_cache(maxsize=1)
def is_dark_theme() -> bool:
    """Detect if the current desktop theme is dark or light.

    Checks the GTK theme name from GNOME settings to determine if the
    current desktop theme uses dark colors. This is used to select
    appropriate icon variants for better visibility.

    Returns:
        bool: True if dark theme is detected, False for light theme.

    Note:
        Uses gsettings to query the current GTK theme and checks for
        common dark theme indicators in the theme name.

    Examples:
        >>> is_dark_theme()
        False  # Light theme detected
        >>> is_dark_theme()
        True   # Dark theme detected
    """
    logger.debug("Detecting desktop theme (dark/light)")
    with contextlib.suppress(Exception):
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
            capture_output=True,
            text=True,
            timeout=0.5,
        )

        if result.returncode == 0:
            theme_name: str = result.stdout.strip().strip("'\"").lower()
            dark_indicators: list[str] = [
                "dark",
                "black",
                "night",
                "nord",
                "dracula",
            ]
            is_dark = any(indicator in theme_name for indicator in dark_indicators)
            logger.debug("Theme detection: '{}' -> dark={}", theme_name, is_dark)
            return is_dark

    logger.debug("Theme detection failed, defaulting to light theme")
    return False


def set_application_icon() -> None:
    """Set the default application icon for GTK windows.

    Sets the default window icon that appears in the taskbar and window
    decorations for all application windows. Attempts to use the custom
    icon.png file, falling back to the system gtk-convert icon if unavailable.

    Returns:
        None

    Note:
        This affects the taskbar icon for all windows created by the application.
        Silently handles missing icon files and GTK unavailability.
    """
    logger.debug("Setting application icon")
    with contextlib.suppress(Exception):
        icon_path = Path(__file__).parent.parent / "icon.png"

        if Gtk:
            if icon_path.exists():
                Gtk.Window.set_default_icon_from_file(str(icon_path))
                logger.debug("Application icon set from: {}", str(icon_path))
            else:
                Gtk.Window.set_default_icon_name("gtk-convert")
                logger.debug("Application icon set to system default: gtk-convert")
        else:
            logger.debug("GTK not available, skipping icon setup")


def set_application_name() -> None:
    """Set the application name for consistent taskbar display.

    Sets the application name that appears in window titles, taskbar tooltips,
    and window manager identification. This ensures all windows show the same
    consistent name across different desktop environments.

    Returns:
        None

    Note:
        Sets both WM_CLASS environment variable and GLib application name
        for maximum compatibility across different window managers.
    """
    logger.debug("Setting application name: {}", text.UI.APPLICATION_TITLE)
    with contextlib.suppress(Exception):
        os.environ["WM_CLASS"] = text.UI.APPLICATION_TITLE
        if not GLib:
            logger.debug("GLib not available, skipping prgname setup")
            return
        GLib.set_application_name(text.UI.APPLICATION_TITLE)
        GLib.set_prgname("convert-file")
        logger.debug("Application name and prgname set successfully")


@lru_cache(maxsize=1)
def get_notification_icon() -> Optional[str]:
    """Get the path to the appropriate notification icon based on theme.

    Returns the path to a theme-appropriate notification icon. Uses
    icon_dark.png for dark themes and icon_light.png for light themes
    to ensure good visibility against the notification background.

    Returns:
        Optional[str]: Path to the appropriate icon file, or None if not found.

    Note:
        Automatically detects the current theme using is_dark_theme()
        and selects the corresponding icon variant.

    Examples:
        >>> icon_path = get_notification_icon()
        >>> icon_path
        '/path/to/action/icon_light.png'
    """
    logger.debug("Getting notification icon path")
    with contextlib.suppress(Exception):
        icon_filename: str = "icon_dark.png" if is_dark_theme() else "icon_light.png"
        icon_path = Path(__file__).parent.parent / "ui" / icon_filename
        if icon_path.exists():
            icon_path_str: str = str(icon_path)
            logger.debug("Notification icon found: {}", icon_path_str)
            return icon_path_str
        else:
            logger.debug("Notification icon not found: {}", str(icon_path))
            return None

    logger.debug("Error getting notification icon, returning None")
    return None
