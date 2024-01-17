CALCULATE SHA512SUM
===================

Calculate the sha512sum for selected file(s).

DESCRIPTION
-----------

This is an action to calculate the sha512sum for specific file(s).
This is particularly useful for verifying ISOs for example.

This is a different action from [verify-sha512sum@rcalixte](https://cinnamon-spices.linuxmint.com/actions/view/24) that prompts for the
sha512sum hash before proceeding further. This will only display the sha512sum
hash in a dialog where it can be copied.

DEPENDENCIES
------------

The following programs must be installed and available:

* `gettext` for translations in the action's script
* `sha512sum` to calculate the hash of file
* `zenity` to display the dialog with the result
