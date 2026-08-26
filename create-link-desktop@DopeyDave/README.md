Create a Link on the Desktop
========================

Description
-----------

This Action adds the ability to create a link on the Desktop of a file or folder. The link is created using the .desktop file type, which allows for proper path tracking and display on the Desktop.

The behavior is similar to the Windows "create a shortcut" / "send to desktop" functionality.

Shortcuts made of hidden files/folders (filename prepended with ".") will be visible on the Desktop. Normally in Cinnamon, hidden files/folders do not display on the Desktop. Although you can enable the "show hidden files" option in Nemo, this only affects Nemo, and does not affect the Desktop display. But by using .desktop shortcut files, this can allow them to appear. This Action takes the existing filename and alters it so Cinnamon does not consider it a hidden item ("_" is prepended). It then keeps the .desktop "Name" attribute true to the file/folder's actual name, since this is the filename that is actually used for display (this is true for Nemo in a folder view as well as Cinnamon on the Desktop).

This following Actions should be paired for a complete package:
* create-link-desktop@DopeyDave (You Are Here)
* create-link-here@DopeyDave
* follow-desktop-link@DopeyDave

Usage
-----------

Right click on a file or folder. Select the new option "Create Link on Desktop".
