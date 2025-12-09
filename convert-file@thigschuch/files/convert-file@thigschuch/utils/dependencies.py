"""
Linux Dependency Manager

Simple utility to detect package manager and provide install commands
for required dependencies.

Supported tools:
- Media: ffmpeg
- Documents: libreoffice, pandoc, ebook-convert (calibre)
- Images: imagemagick
- Archives: 7z, zip, unzip, tar, rar, dpkg-deb, rpm2cpio, cpio, genisoimage, lzop, xz
"""

import shutil
from functools import lru_cache
from typing import Optional

from .logging import logger
from .text import text

PACKAGE_MANAGERS = {
    "apt": "sudo apt install {package}",
    "dnf": "sudo dnf install {package}",
    "yum": "sudo yum install {package}",
    "pacman": "sudo pacman -S {package}",
    "zypper": "sudo zypper install {package}",
    "emerge": "sudo emerge {package}",
    "apk": "sudo apk add {package}",
    "flatpak": "flatpak install flathub {package}",
    "snap": "sudo snap install {package}",
}

PACKAGE_NAMES = {
    "7z": {
        "dnf": "p7zip",
        "yum": "p7zip",
        "pacman": "p7zip",
        "zypper": "p7zip",
        "emerge": "app-arch/p7zip",
        "apk": "p7zip",
        "default": "p7zip-full",
    },
    "imagemagick": {"emerge": "media-gfx/imagemagick", "default": "imagemagick"},
    "libreoffice": {"emerge": "app-office/libreoffice", "default": "libreoffice"},
    "ffmpeg": {"emerge": "media-video/ffmpeg", "default": "ffmpeg"},
    "pandoc": {"emerge": "app-text/pandoc", "default": "pandoc"},
    "zip": {"default": "zip"},
    "unzip": {"default": "unzip"},
    "tar": {"default": "tar"},
    "rar": {"emerge": "app-arch/rar", "default": "rar"},
    "dpkg-deb": {"default": "dpkg"},
    "rpm2cpio": {
        "dnf": "rpm",
        "yum": "rpm",
        "pacman": "rpm-tools",
        "zypper": "rpm",
        "emerge": "app-arch/rpm",
        "default": "rpm2cpio",
    },
    "cpio": {
        "emerge": "app-arch/cpio",
        "default": "cpio",
    },
    "genisoimage": {
        "pacman": "cdrtools",
        "emerge": "app-cdr/cdrtools",
        "default": "genisoimage",
    },
    "lzop": {
        "emerge": "app-arch/lzop",
        "default": "lzop",
    },
    "xz": {
        "dnf": "xz",
        "yum": "xz",
        "pacman": "xz",
        "zypper": "xz",
        "emerge": "app-arch/xz-utils",
        "apk": "xz",
        "default": "xz-utils",
    },
    "gzip": {"default": "gzip"},
    "bzip2": {"default": "bzip2"},
    "ebook-convert": {
        "emerge": "app-text/calibre",
        "flatpak": "com.calibre_ebook.calibre",
        "default": "calibre",
    },
    "pdftohtml": {
        "pacman": "poppler",
        "zypper": "poppler-tools",
        "emerge": "media-libs/poppler",
        "default": "poppler-utils",
    },
    "pdftotext": {
        "pacman": "poppler",
        "zypper": "poppler-tools",
        "emerge": "media-libs/poppler",
        "default": "poppler-utils",
    },
}


class DependencyManager:
    """Manages detection of package managers and provides installation commands for required dependencies.

    This class automatically detects the system's package manager and provides
    appropriate installation commands for various multimedia processing tools.
    It supports multiple Linux distributions and package managers.

    Attributes:
        _detected_manager: The detected package manager command name.

    Examples:
        >>> manager = DependencyManager()
        >>> manager.is_installed("ffmpeg")
        True
        >>> manager.get_install_command("pandoc")
        'sudo apt install pandoc'
    """

    def __init__(self) -> None:
        """Initialize the dependency manager.

        Package manager detection is deferred until first needed.

        Returns:
            None
        """
        self._detected_manager: Optional[str] = None
        logger.debug("Initializing dependency manager")

    def detect_package_manager(self) -> Optional[str]:
        """Detects the first available package manager from the predefined list.

        Iterates through supported package managers and returns the first one
        found in the system's PATH. Updates the internal detected manager state.

        Returns:
            Optional[str]: The detected package manager command name, or None if none found.

        Examples:
            >>> manager = DependencyManager()
            >>> manager.detect_package_manager()
            'apt'
        """
        logger.debug("Detecting package manager")
        for manager in PACKAGE_MANAGERS:
            if shutil.which(manager):
                self._detected_manager = manager
                logger.debug("Detected package manager: {}", manager)
                return manager
        self._detected_manager = None
        logger.debug("No package manager detected")
        return None

    def is_installed(self, dependency: str) -> bool:
        """Checks if a given dependency is installed on the system.

        Uses shutil.which() to check if the dependency executable is available
        in the system's PATH.

        Args:
            dependency: The name of the dependency executable to check.

        Returns:
            bool: True if the dependency is installed and available, False otherwise.

        Examples:
            >>> manager.is_installed("ffmpeg")
            True
            >>> manager.is_installed("nonexistent_tool")
            False
        """
        installed = shutil.which(dependency) is not None
        logger.debug("Dependency '{}' installed: {}", dependency, installed)
        return installed

    @lru_cache(maxsize=128)
    def get_install_command(self, dependency: str) -> Optional[str]:
        """Provides the installation command for the specified dependency.

        Generates a complete installation command using the detected package
        manager and the appropriate package name for the dependency.

        Args:
            dependency: The name of the dependency to install.

        Returns:
            Optional[str]: The complete installation command string, or None if unsupported.

        Examples:
            >>> manager.get_install_command("ffmpeg")
            'sudo apt install ffmpeg'
            >>> manager.get_install_command("unknown_tool")
            None
        """
        logger.debug("Getting install command for dependency: {}", dependency)
        if dependency not in PACKAGE_NAMES.keys():
            logger.debug("Dependency '{}' not supported", dependency)
            return None

        if self._detected_manager is None:
            self.detect_package_manager()

        if self._detected_manager is None:
            logger.debug("No package manager detected for install command")
            return None

        package_name = self._get_package_name(dependency)
        command = PACKAGE_MANAGERS[self._detected_manager].format(package=package_name)
        logger.debug("Generated install command: {}", command)
        return command

    @lru_cache(maxsize=128)
    def get_install_instructions(self, dependency: str) -> Optional[str]:
        """Get comprehensive installation instructions for a dependency.

        Returns installation instructions if the dependency is not installed.
        If already installed, returns None. Falls back to manual installation
        message if no package manager command is available.

        Args:
            dependency: The name of the dependency to get instructions for.

        Returns:
            Optional[str]: Installation instructions or None if already installed.

        Examples:
            >>> manager.get_install_instructions("ffmpeg")
            'sudo apt install ffmpeg'
            >>> manager.get_install_instructions("installed_tool")
            None
        """
        logger.debug("Getting install instructions for dependency: {}", dependency)
        if self.is_installed(dependency):
            logger.debug("Dependency '{}' already installed", dependency)
            return None

        command = self.get_install_command(dependency)

        if command:
            logger.debug("Returning package manager install command")
            return command
        else:
            logger.debug("Returning manual installation message")
            return text.UI.MANUAL_INSTALLATION_REQUIRED_MESSAGE.format(
                dependency=dependency
            )

    def _get_package_name(self, dependency: str) -> str:
        """Get the correct package name for the detected package manager.

        Looks up the appropriate package name for the current package manager,
        falling back to the default package name if no specific mapping exists.

        Args:
            dependency: The dependency name to look up.

        Returns:
            str: The package name appropriate for the current package manager.

        Examples:
            >>> manager._detected_manager = "apt"
            >>> manager._get_package_name("7z")
            'p7zip-full'
        """
        mapping: dict = PACKAGE_NAMES.get(dependency, {})
        package_name = mapping.get(
            self._detected_manager, mapping.get("default", dependency)
        )
        logger.debug(
            "Package name for '{}' with manager '{}': {}",
            dependency,
            self._detected_manager,
            package_name,
        )
        return package_name


dependency_manager = DependencyManager()
