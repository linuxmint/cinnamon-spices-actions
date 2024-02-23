#!/usr/bin/env python3

import subprocess
import sys


def main():
    '''
    Take the list of arguments and build the xdg-email command
    '''
    if len(sys.argv) < 1:
        sys.exit(2)

    xdg_cmd: list = ['/usr/bin/xdg-email']
    for file_arg in sys.argv[1:]:
        xdg_cmd.extend(['--attach', file_arg])
    subprocess.run(xdg_cmd, check=False)


if __name__ == '__main__':
    main()
