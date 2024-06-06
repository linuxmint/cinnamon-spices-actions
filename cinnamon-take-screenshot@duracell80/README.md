Take Screenshot
==============

Launch a screenshot area selection utility directly from the desktop context menu.

DESCRIPTION
-----------

This action calls a screenshot utility directly from the desktop context menu to allow for the caputure of a selected area. It will auto save the capture to either the location noted from "gsettings get org.gnome.gnome-screenshot auto-save-directory" or a fallback in ~/Pictures/screenshots and display the file in pix.

Now uses delay. To set type in a terminal "gsettings set org.gnome.gnome-screenshot delay 5" for a 5 second delay.

DEPENDENCIES
------------

The following programs must be installed and available

* `gnome-screenshot`, `pix`, `cinnamon`, `gsettings`, `zenity`
