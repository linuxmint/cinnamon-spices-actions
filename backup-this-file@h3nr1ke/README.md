BACKUP THIS FILE
================

Create a backup of the selected file by copying it and appending the suffix .bkp.

DESCRIPTION
-----------

By selecting a file and clicking "Backup this File," a new file will be created following the pattern `<filename>.bkp`.

If a `.bkp` file already exists for the selected file, the new one will be generated with an index at the end, like `.bkp2`.

If a `.bkp2` file already exists, a `.bkp3` will be created, and so on.

This is useful for backing up config files during tests.

DEPENDENCIES
------------

The following programs must be installed and available:

* `gettext` to get the correct translation to the action
* `bash` to execute the commands