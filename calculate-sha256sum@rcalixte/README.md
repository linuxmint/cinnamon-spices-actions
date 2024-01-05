CALCULATE SHA256SUM
===================

Calculate the sha256sum for selected file(s).

DESCRIPTION
-----------

This is an action to calculate the sha256sum for specific file(s).
This is particularly useful for verifying ISOs for example.

This is a different action from [verify-sha256sum@rcalixte](https://cinnamon-spices.linuxmint.com/actions/view/9) that prompts for the
sha256sum hash before proceeding further. This will only display the sha256sum
hash in a dialog where it can be copied.

DEPENDENCIES
------------

The following programs must be installed and available:

* `gettext` for translations in the action's script
* `sha256sum` to calculate the hash of file
* `zenity` to display the dialog with the result
