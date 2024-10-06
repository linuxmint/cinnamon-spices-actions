#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
import text
import aui

from pathlib import Path


HOME = os.path.expanduser("~")

FONTS_DIRS = [
    os.path.join(HOME, ".local/share/fonts"),
    os.path.join(HOME, ".fonts"),
]

NEMO_DEBUG = os.environ.get("NEMO_DEBUG", "")
DEBUG = os.environ.get("DEBUG", "0")


def log(*args, **kwargs):
    if DEBUG == "1" or "Actions" in NEMO_DEBUG:
        print(f"Action {text.UUID}:", *args, **kwargs)


def create_dir(self, path) -> bool:
    try:
        os.mkdir(path)
    except Exception as e:
        log(f"Could not create dir: {e}")
        return False
    return True


def symlink_dir(link_dir, target_dir) -> None:
    link_dir = Path(link_dir)
    if not link_dir.exists():
        link_dir.symlink_to(target_dir, target_is_directory=True)
        log(f"Created symlink: {link_dir} -> {target_dir}")


class FontsInstallerAction:
    def __init__(self, file_paths: list[Path]) -> None:
        self.file_paths = file_paths
        self.fonts_dir = self.get_fonts_dir()

    def get_fonts_dir(self) -> str | None:
        fonts_dir = None
        for path in FONTS_DIRS:
            if fonts_dir is None and os.path.isdir(path):
                fonts_dir = path
            elif fonts_dir is not None and not os.path.exists(path):
                # symlink to other non created paths to the first path
                symlink_dir(link_dir=path, target_dir=fonts_dir)
        else:
            for path in FONTS_DIRS:
                if fonts_dir is None:
                    if create_dir(path) and os.path.isdir(path):
                        fonts_dir = path
                        log(f"Created fonts install dir: {fonts_dir}")
                else:
                    # symlink to other non created paths to the first path
                    symlink_dir(link_dir=path, target_dir=fonts_dir)
        return fonts_dir

    def update_fonts_cache(self) -> bool:
        try:
            subprocess.run(
                ["fc-cache", "-f", "-v"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            log(f"Could not create font cache: {e}")
            return False
        return True

    def install_font_to_dir(self, file: Path, dir: str) -> bool:
        try:
            if not file.exists():
                log(f"Error: File not found at: {file.resolve()}")
                return False

            new_path = os.path.join(dir, file.name)

            if os.path.exists(new_path):
                log(f"Warning: File already exists at installation site: {new_path}")
                pass  # TODO: Alert user of things being overwriten, ask for confirmation

            shutil.copy2(file.resolve(), new_path)

            if os.path.exists(new_path):
                log(f"Info: Font was installed at: {new_path}")
            else:
                log(f"Error: Could not install font at {dir}")
                return False
        except Exception as e:
            log(f"Error: Could not install font: {e}")
            return False
        return True

    def finish(self, n_files_moved: int) -> None:
        if n_files_moved == 0:
            log("Fonts were not installed!")
            exit(1)

        font_cache_success = self.update_fonts_cache()  # Add progress?

        if not font_cache_success:
            log(
                "Font cache could be updated with success!"
            )  # XXX: add this to the second line on the ui

        if n_files_moved < len(self.file_paths):
            log("Some fonts could not be installed successfuly!")
        else:
            log("All fonts were installed successfuly!")

    def run(self) -> None:
        if not self.fonts_dir:
            log("Could not find or create install dirs for the fonts")
            exit(1)

        files_moved = 0
        for file in self.file_paths:
            if self.install_font_to_dir(file, self.fonts_dir):
                files_moved += 1

        self.finish(files_moved)


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        log("No font files provided.")
        exit(1)

    file_paths = [Path(path) for path in sys.argv[1:]]
    action = FontsInstallerAction(file_paths=file_paths)
    action.run()
    exit(0)
