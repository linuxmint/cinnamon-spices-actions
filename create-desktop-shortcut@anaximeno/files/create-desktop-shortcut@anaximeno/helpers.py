import os
import text


DEBUG = os.environ.get("NEMO_DEBUG") == "Actions"


def log(*args, **kwargs):
    if DEBUG:
        print(f"Action {text.UUID}:", *args, **kwargs)
