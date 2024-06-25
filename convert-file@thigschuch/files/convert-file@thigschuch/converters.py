import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

import text
from aui import InfoDialogWindow, ProgressbarDialogWindow


class Converter(ABC):

    def __init__(self, file: Path, format: str):
        self._process: subprocess.Popen = None
        self._buffer: str = ""

        self.file: Path = file
        self.format: str = format
        self.target_file: Path = self.file.with_suffix(f".{self.format.lower()}")

        self.valid_target_file()
        self.build_command()

    @abstractmethod
    def build_command(self) -> None:
        pass

    def valid_target_file(self) -> None:
        suffix = f".{self.format.lower()}"
        self.target_file = self.file.with_suffix(suffix)
        count = 1

        while self.target_file.exists():
            self.target_file = self.file.with_stem(
                f"{self.file.stem} ({count})"
            ).with_suffix(suffix)
            count += 1

    def convert(self) -> bool:
        self._process = subprocess.Popen(
            self.command,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
        )

        window = ProgressbarDialogWindow(
            title=text.CONVERTING_TITLE,
            message=text.CONVERTING_LABEL.format(format=self.format),
            timeout_callback=self._handle_progress,
            timeout_ms=10000,
        )

        window.run()
        window.destroy()

        # TODO: A way to handle the cancel by the user
        # if self._process.poll() is None:
        #     self._process.terminate()
        #     self._delete_target_file()
        #     return

        # self._success_dialog()

        return self._process.poll() == 0

    def _delete_target_file(self) -> None:
        if self.target_file.exists():
            self.target_file.unlink()

    def _success_dialog(self) -> None:
        InfoDialogWindow(
            title=text.SUCCESS_TITLE,
            message=text.SUCCESS_MESSAGE.format(format=self.format),
        ).run()

    def _handle_progress(self, _, window: ProgressbarDialogWindow) -> bool:
        if self._process and self._process.poll() is None:
            try:
                if self._process.stderr.readable():
                    self._buffer += self._process.stderr.read().decode("utf-8")
                    window.set_text(self._buffer)
                window.progressbar.pulse()
            except Exception as e:
                print(e)
                pass

        if self._process.poll() is not None:
            self._process.terminate()
            window.stop()
            window.destroy()
            return False

        return True


class ImageConverter(Converter):
    def build_command(self) -> None:
        self.command = [
            "convert",
            str(self.file),
            str(self.target_file),
        ]


class VideoConverter(Converter):
    def build_command(self) -> None:
        self.command = [
            "ffmpeg",
            "-i",
            str(self.file),
            str(self.target_file),
        ]


class AudioConverter(Converter):
    def build_command(self) -> None:
        self.command = [
            "ffmpeg",
            "-i",
            str(self.file),
            str(self.target_file),
        ]
