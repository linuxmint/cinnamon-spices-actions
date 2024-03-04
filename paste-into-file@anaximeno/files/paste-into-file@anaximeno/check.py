#!/usr/bin/python3
import os, sys
import subprocess


def main() -> None:
    if len(sys.argv) < 2:
        exit(1)

    directory = sys.argv[1].replace("\\ ", " ")
    files = sys.argv[2:]

    # if dir does not exist or is not writable
    if not os.path.exists(directory) or not os.access(directory, os.W_OK):
        exit(1)

    # Max. one file is accepted
    if len(files) > 1:
        exit(1)

    # Check write perms if file given
    if len(files) == 1 and not os.access(files[0].replace("\\ ", " "), os.W_OK):
        exit(1)

    ## XXX: It doesn't work very well if the user performed a cut operation before
    ##    triggering the check below.
    # command = ["xclip", "-out", "-selection", "clipboard"]

    # clipcontent = subprocess.run(
    #     command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=0.5,
    # ).stdout.decode("utf-8")

    # # Check if the clipboard is not empty
    # if clipcontent.strip() == "":
    #     exit(1)

    exit(0)


if __name__ == "__main__":
    main()
