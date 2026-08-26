Create a Link Here
========================

Description
-----------

This Action adds the ability to create a link "here" (in the same folder) for a file or folder. The link is created using the .desktop file type, which allows for proper path tracking and display on the Desktop (if the shortcut happens to be moved there).

The behavior is similar to the Windows "create a shortcut" / "send to desktop" functionality.

**Difference from Nemo's "Make Link"?:** Nemo does have a seemingly similar functionality built-in, which is called "Make Link". **However, the only similarity is in name, not functionality.** Nemo's "Make Link" creates a link file to the object, whereas this Action creates a .desktop file to the object. The differences are obvious in use. For example, if you have a file (hello.txt), using Nemo's "Make Link" will result in a link file with the name "Link to hello.txt". When double clicking this link (to open with a text editor), the filename the text editor will show is incorrectly stated as "Link to hello.txt" rather than just "hello.txt". Even worse, if you happen to move this link to some other folder and then double click it, the path will also be wrong, incorrectly displaying the path to the link file itself rather than the path to the actual file. For example: "/path/to/hello.txt" vs "/path/to/my_folder/Link to hello.txt". **This does not happen when using this Action.** This Action uses .desktop files, which preserve the path of the actual file, as well as correctly identifying the name of the file.

This following Actions should be paired for a complete package:
* create-link-desktop@DopeyDave
* create-link-here@DopeyDave    (You Are Here)
* follow-desktop-link@DopeyDave

Usage
-----------

Right click on a file or folder. Select the new option "Create Link Here".
