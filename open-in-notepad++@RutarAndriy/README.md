# Open in Notepad++

Opens a file in Notepad++ via Wine. Supports x32 and x64 versions of the program.
Notepad++ should be installed in the standard directory (`drive_c/Program Files/Notepad++` for x64 version or `drive_c/Program Files (x86)/Notepad++` for x32 version) and with the standard wine-prefix: `~/.wine`

## Dependencies

The following packages must be installed:

* `xdg-utils` for running `xdg-icon-resource` command
* `wine` for launch notepad++.exe
