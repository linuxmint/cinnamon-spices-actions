SEND TO PRINTER
===============

Send file(s) to print via the default printer

DESCRIPTION
-----------

This action will attempt to print the selected file(s) *once* to the default
printer.

__NOTE:__ There must be a printer configured as the default printer.

__NOTE:__ If there are any errors, they will be silently discarded.

__NOTE:__ When printing multiple files, the name of the print job will be the
first file in the list.

DEPENDENCIES
------------

The following programs must be installed and available:

* `lpr` to submit files for printing (provided by the packages below)

Depending on your family of distro, the following package needs to be
installed to satisfy the aforementioned program dependency.

* __Debian/Mint/Ubuntu__: Install the package **cups-bsd**
* __Fedora__: Install the package **cups-client**
* __Arch/Manjaro__: Install the package **cups**
