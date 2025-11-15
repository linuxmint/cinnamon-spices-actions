VERIFY SHA256SUM
================

Verify that a provided sha256sum hash matches for a single file.

DESCRIPTION
-----------

This is an action to verify the sha256sum for a specific file, provided
an input hash for comparison purposes.
This is particularly useful for verifying ISOs for example.

This is a different action from [calculate-sha256sum@rcalixte](https://cinnamon-spices.linuxmint.com/actions/view/3) that just
calculates and displays the sha256sum hash. This requires user input before
proceeding further. The input hash will be automatically converted to the
equivalent lower case for comparison.

DEPENDENCIES
------------

The following programs must be installed and available:

* `gettext` for translations in the action's script
* `sha256sum` to calculate the hash of file
* `zenity` to display dialogs including the result
