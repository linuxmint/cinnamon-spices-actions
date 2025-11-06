import os
import text


NEMO_DEBUG = os.environ.get("NEMO_DEBUG", "")
DEBUG = "Actions" in NEMO_DEBUG if NEMO_DEBUG else False


def log(*args, **kwargs):
    """Log debug messages if DEBUG is enabled."""
    if DEBUG is True:
        print(f"Action {text.UUID}:", *args, **kwargs)


def get_tmp_store_path() -> str:
        def make_tmp_dir(path: str) -> str:
            tmp_dir = os.path.join(path, text.UUID)
            os.makedirs(tmp_dir, exist_ok=True)
            return tmp_dir

        """Get a temporary storage path."""
        if os.environ.get("XDG_RUNTIME_DIR"):
            return make_tmp_dir(os.environ["XDG_RUNTIME_DIR"])
        elif os.path.exists("~/.cache"):
            return make_tmp_dir(os.path.join(os.path.expanduser("~/.cache"), text.UUID))
        elif os.path.exists("/tmp"):
            return make_tmp_dir("/tmp")
        elif os.path.exists("/var/tmp"):
            return make_tmp_dir("/var/tmp")
        else:
            os.makedirs(os.path.expanduser("~/.cache"), exist_ok=True)
            if os.path.exists("~/.cache"):
                return make_tmp_dir(os.path.expanduser("~/.cache"))
            else:
                log("Warn: Couldn't find a temporary storage path, using the current directory")
                return os.getcwd()
