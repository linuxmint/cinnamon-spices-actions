VERIFY MD5SUM
=============

Verify that a provided md5sum hash matches for a single file.

DESCRIPTION
-----------

This is an action to verify the md5sum for a specific file, provided
an input hash for comparison purposes.
This is useful e.g. for verifying ISOs.

DEPENDENCIES
------------

The following programs must be installed and available:

* `gettext` for translations in the action's script
* `md5sum` to calculate the hash of file
* `zenity` to display dialogs including the result
