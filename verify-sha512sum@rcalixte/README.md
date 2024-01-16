VERIFY SHA512SUM
================

Verify that a provided sha512sum hash matches for a single file.

DESCRIPTION
-----------

This is an action to verify the sha512sum for a specific file, provided
an input hash for comparison purposes.
This is particularly useful for verifying ISOs for example.

This is a different action from [calculate-sha512sum@rcalixte](https://cinnamon-spices.linuxmint.com/actions/view/23) that just
calculates and displays the sha512sum hash. This requires user input before
proceeding further.

DEPENDENCIES
------------

The following programs must be installed and available:

* `gettext` for translations in the action's script
* `sha512sum` to calculate the hash of file
* `zenity` to display dialogs including the result
