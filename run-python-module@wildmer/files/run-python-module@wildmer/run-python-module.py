#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    terminal = "x-terminal-emulator"

    module_path = Path(sys.argv[1])

    if not module_path.is_dir():
        print(f"Error: provided path is not a directory: {module_path}")
        sys.exit(1)

    working_dir = module_path.parent
    module_name = module_path.name

    remote_cmd = [
        terminal,
        "-e",
        "bash",
        "-c",
        f'cd "{working_dir}" && python3 -m "{module_name}"; exec bash',
    ]

    subprocess.call(remote_cmd)
