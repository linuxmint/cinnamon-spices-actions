BACKUP THIS FILE
================

Backup the selected file by creating a copy and appending the suffix .bkp

DESCRIPTION
-----------

By selecting a file and clicking "Backup this File", a new file will be create following the pattern `<filename>.bkp`.

If a `.bkp` file already exists for the selected file, the new one will be generate with an index in the end, like `.bkp2`

If a `.bkp2` file already exists, a `.bkp3` will be create and so on...

Useful to backup config files during tests.

DEPENDENCIES
------------

The following programs must be installed and available:

* `gettext` to get the correct translation to the action
* `bash` to execute the commands