#!/usr/bin/python3
import os, sys


def main() -> None:
    if len(sys.argv) < 2:
        exit(1)

    directory = sys.argv[1]
    files = sys.argv[2:]

    # if dir does not exist or is not writable
    if not os.path.exists(directory) or not os.access(directory, os.W_OK):
        exit(1)

    # Max. one file is accepted
    if len(files) > 1:
        exit(1)

    # Check write perms if file given
    if len(files) == 1 and not os.access(files[0], os.W_OK):
        exit(1)

    exit(0)


if __name__ == "__main__":
    main()
