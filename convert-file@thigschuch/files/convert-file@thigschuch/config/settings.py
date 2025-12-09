#!/usr/bin/python3
"""
Settings management for convert-file action.

This module handles loading and saving user configuration files,
merging them with default settings, and providing a clean API
for accessing conversion command templates and conversion rules.

The settings system uses a hierarchical approach:
1. Default settings (shipped with the application)
2. System settings (installed in user config directory)
3. User customizations (user_settings.json)

Settings are merged with user customizations taking precedence.
"""

import json
import shutil
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logging import logger


class SettingsManager:
    """Manages user configuration settings for file conversions.

    Handles loading default settings, user customizations, and provides
    an API for accessing command templates and conversion rules.

    The settings manager implements a three-tier configuration system:
    - Default settings: Built-in application defaults
    - System settings: Application-maintained settings in user directory
    - User settings: User customizations that override defaults

    Attributes:
        _default_config_file: Path to built-in default settings.
        _user_config_dir: User configuration directory path.
        _system_config_file: System settings file in user directory.
        _user_config_file: User customization settings file.
        _merged_settings: Cached merged settings dictionary.

    Examples:
        >>> manager = SettingsManager()
        >>> settings = manager.load_settings()
        >>> template = manager.get_converter_template("image", "PNG")
    """

    def __init__(self) -> None:
        """Initialize the settings manager.

        Sets up file paths for default, system, and user configuration files.
        Creates the user configuration directory if it doesn't exist and
        ensures all required configuration files are present.

        Returns:
            None
        """
        self._default_config_file = Path(__file__).parent / "settings.json"
        self._default_user_config_file = Path(__file__).parent / "user_settings.json"
        self._user_config_dir = Path.home() / ".config" / "convert-file@thigschuch"
        self._system_config_file = self._user_config_dir / "settings.json"
        self._user_config_file = self._user_config_dir / "user_settings.json"

        self._merged_settings: Optional[Dict[str, Any]] = None

        logger.debug(
            "Initializing settings manager with config dir: {}", self._user_config_dir
        )
        self._ensure_user_config_exists()
        self.load_settings()

    def _ensure_user_config_exists(self) -> None:
        """Ensure user configuration directory and files exist.

        Creates the user config directory structure if it doesn't exist.
        Copies default settings to the user directory and creates empty
        user customization files. Updates system settings if version differs.

        Returns:
            None

        Note:
            This method handles version updates by replacing system settings
            when the default version differs from the installed version.
        """
        logger.debug("Ensuring user config directory exists: {}", self._user_config_dir)
        if not self._user_config_dir.exists():
            self._user_config_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Created user config directory")

        if self._system_config_file.exists():
            try:
                default_settings = self._load_json_file(self._default_config_file)
                system_settings = self._load_json_file(self._system_config_file)

                if self._needs_version_update(system_settings, default_settings):
                    shutil.copy2(self._default_config_file, self._system_config_file)
                    logger.debug("Updated system settings to new version")
            except Exception:
                shutil.copy2(self._default_config_file, self._system_config_file)
                logger.debug("Copied default settings due to error loading existing")
        elif self._default_config_file.exists():
            shutil.copy2(self._default_config_file, self._system_config_file)
            logger.debug("Copied default settings to system config")

        if not self._user_config_file.exists():
            shutil.copy2(self._default_user_config_file, self._user_config_file)
            logger.debug("Created user settings file")

    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a JSON configuration file.

        Args:
            file_path: Path to the JSON file to load.

        Returns:
            Dict[str, Any]: Dictionary containing the parsed JSON data.

        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            json.JSONDecodeError: If the file contains invalid JSON syntax.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Configuration file not found: {file_path}") from e
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in configuration file: {file_path}", e.doc, e.pos
            ) from e

    def _deep_merge_dicts(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries with override values taking precedence.

        Performs a recursive merge of dictionaries, handling nested dictionaries
        and lists appropriately. Override values completely replace base values
        for simple types, but lists are prepended and dictionaries are merged.

        Args:
            base: Base dictionary to merge into.
            override: Dictionary with values that override the base.

        Returns:
            Dict[str, Any]: New dictionary with merged values.

        Note:
            For lists, override items are prepended to base items.
            For nested dictionaries, the merge is performed recursively.
        """
        result = base.copy()

        for key, value in override.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._deep_merge_dicts(result[key], value)

                elif isinstance(result[key], list) and isinstance(value, list):
                    result[key] = [
                        item for item in value if item not in result[key]
                    ] + result[key]

                else:
                    result[key] = value

            else:
                result[key] = value

        return result

    def load_settings(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load and merge system and user settings.

        Loads settings from the three-tier configuration system:
        1. System settings (application defaults in user directory)
        2. User settings (customizations)
        3. Merges them with user settings taking precedence

        Args:
            force_reload: If True, reloads from disk even if cached. Defaults to False.

        Returns:
            Dict[str, Any]: Dictionary containing merged settings.

        Note:
            Settings are cached after first load for performance.
            Use force_reload=True to refresh from disk.
        """
        if self._merged_settings is not None and not force_reload:
            logger.debug("Returning cached settings")
            return self._merged_settings

        logger.debug("Loading settings from disk (force_reload={})", force_reload)
        try:
            system_settings = self._load_json_file(self._system_config_file)
            logger.debug("Loaded system settings successfully")
        except (FileNotFoundError, json.JSONDecodeError):
            try:
                system_settings = self._load_json_file(self._default_config_file)
                logger.debug("Loaded default settings as fallback")
            except (FileNotFoundError, json.JSONDecodeError):
                system_settings = {
                    "version": "1.0.0",
                    "audio_rules": {},
                    "video_rules": {},
                    "image_rules": {},
                    "special_rules": [],
                }
                logger.warning("Using hardcoded fallback settings")

        user_settings = {}
        try:
            user_settings = self._load_json_file(self._user_config_file)
            logger.debug("Loaded user settings successfully")
        except FileNotFoundError:
            logger.debug("User settings file not found, using defaults")
            pass
        except json.JSONDecodeError:
            from ui import notification

            notification.notify_corrupted_user_settings()
            logger.warning("User settings file corrupted, using defaults")

        if user_settings:
            self._merged_settings = self._deep_merge_dicts(
                system_settings, user_settings
            )
            logger.debug("Merged system and user settings")
        else:
            self._merged_settings = system_settings
            logger.debug("Using system settings only")

        return self._merged_settings

    def _needs_version_update(
        self, user_settings: Dict[str, Any], default_settings: Dict[str, Any]
    ) -> bool:
        """Check if system settings need to be updated based on version.

        Compares version numbers between installed system settings and
        default settings to determine if an update is needed.

        Args:
            user_settings: Current system settings from user directory.
            default_settings: Latest default settings from application.

        Returns:
            bool: True if settings should be replaced with newer version.
        """
        user_version = user_settings.get("version", "0.0.0")
        default_version = default_settings.get("version", "1.0.0")

        return user_version != default_version

    def get_special_rules(self) -> List[Dict[str, Any]]:
        """Get list of special conversion rules.

        Retrieves all special conversion rules defined in settings.
        Special rules handle cross-format conversions that don't follow
        standard converter patterns (e.g., PDF→JPEG, MP4→MP3).

        Returns:
            List[Dict[str, Any]]: List of special rule dictionaries, each containing
                                'from_format', 'to_format', and command information.
        """
        return self.get("special_rules", [])

    @lru_cache(maxsize=256)
    def find_special_rule(
        self, from_format: str, to_format: str
    ) -> Optional[Dict[str, Any]]:
        """Find a special rule for specific format conversion.

        Searches through special conversion rules to find one that matches
        the given source and target formats.

        Args:
            from_format: Source format (case-insensitive).
            to_format: Target format (case-insensitive).

        Returns:
            Optional[Dict[str, Any]]: Special rule dictionary if found, None otherwise.

        Examples:
            >>> rule = manager.find_special_rule("PDF", "JPEG")
            >>> rule is not None
            True
        """
        from_format = from_format.upper()
        to_format = to_format.upper()

        return next(
            (
                rule
                for rule in self.get_special_rules()
                if (
                    rule.get("from", "").upper() == from_format
                    and rule.get("to", "").upper() == to_format
                )
            ),
            None,
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value with a default fallback.

        Retrieves a setting value from the merged settings, returning the
        default value if the key is not found.

        Args:
            key: Setting key to retrieve.
            default: Default value to return if key not found.

        Returns:
            Any: The setting value or the default value.

        Examples:
            >>> version = manager.get("version", "1.0.0")
            >>> timeout = manager.get("timeout", 30000)
        """
        settings = self.load_settings()
        return settings.get(key, default)

    @lru_cache(maxsize=128)
    def get_output_restricted_formats(self) -> set:
        """Get formats that are restricted from being used as output targets.

        Returns a set of formats that cannot be generated as output due to
        technical limitations or specialized requirements. These include:
        - Archive formats that require specific internal structures (DMG, DEB, RPM)
        - Image formats that need specialized hardware/software (RAW formats)

        However, if a user defines a special rule for creating these formats,
        they will be allowed as exceptions.

        Returns:
            set: Set of format names (uppercase) that are restricted as output targets.
        """
        output_restricted: set[str] = self.get("output_restricted_formats", set())
        return {fmt.upper() for fmt in output_restricted}

    @lru_cache(maxsize=32)
    def get_default_formats(self, group_name: str) -> List[str]:
        """Get the default target formats for a format group.

        Retrieves the recommended target formats for a given format group
        (IMAGE, VIDEO, AUDIO, DOCUMENT, ARCHIVE).

        Args:
            group_name: Name of the format group (case-insensitive).

        Returns:
            List[str]: List of default format names (uppercase) for the group.
                      Falls back to hardcoded defaults if not configured.

        Examples:
            >>> formats = manager.get_default_formats("IMAGE")
            >>> "PNG" in formats
            True
        """
        fallback_defaults = {
            "IMAGE": ("PNG", "JPEG"),
            "VIDEO": ("MP4", "MKV"),
            "AUDIO": ("MP3", "AAC"),
            "DOCUMENT": ("PDF", "DOCX"),
            "ARCHIVE": ("ZIP", "ISO"),
        }

        default_formats_config: dict = self.get("default_formats", {})

        formats = default_formats_config.get(
            group_name, fallback_defaults.get(group_name, [])
        )

        return [fmt.upper() for fmt in formats]


settings_manager = SettingsManager()


def get_converter_template(
    converter_type: str,
    target_format: str,
    input_file: Optional[Path] = None,
) -> tuple[Optional[str], Optional[dict]]:
    """Get the appropriate command template for a converter type and target format.

    Retrieves command templates from settings, checking format-specific templates
    first, then falling back to general command templates. Handles special
    conversion rules for cross-format conversions and multi-file scenarios.

    Args:
        converter_type: Type of converter ('audio', 'video', 'image', 'document', 'archive', 'special').
        target_format: Target format (e.g., 'MP3', 'MP4', 'JPEG').
        input_file: Optional input file path, required for special converter type.

    Returns:
        tuple[Optional[str], Optional[dict]]: Tuple containing:
            - Command template string or None if not found
            - Rule dictionary or None (for additional context)

    Examples:
        >>> template, rule = get_converter_template("image", "PNG")
        >>> template is not None
        True
    """
    logger.debug(
        "Getting converter template for type '{}' and format '{}'",
        converter_type,
        target_format,
    )
    settings = settings_manager.load_settings()

    if converter_type == "special":
        from utils.validation import FileValidator

        source_format = FileValidator.get_file_format(input_file) if input_file else ""

        rule = settings_manager.find_special_rule(source_format, target_format)
        if not rule:
            logger.warning(
                "No special rule found for {} -> {}", source_format, target_format
            )
            return None, None

        logger.debug("Found special rule for conversion")

        command = rule.get("command")
        if command:
            logger.debug("Returning special rule command")
            return command, rule
        else:
            logger.warning("Special rule found but has no command")
            return None, None

    rule_key = f"{converter_type}_rules"
    rule = settings.get(rule_key, {})

    format_commands = rule.get("by_target", {})
    target_format_upper = target_format.upper()

    if target_format_upper in format_commands:
        logger.debug("Using format-specific command template")
        return format_commands[target_format_upper], None

    template = rule.get("default")
    logger.debug("Using general command template: {}", template is not None)
    return template, rule
