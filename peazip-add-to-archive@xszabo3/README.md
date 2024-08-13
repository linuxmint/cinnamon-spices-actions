# Add to archive action for the Flatpak version of PeaZip

Adds **Add to archive** action to the context menu (right-click menu) for the Nemo file manager. Actions make zipping and unzipping zip (and other) files more convenient.

## Prerequisites

Install the Flatpak version of PeaZip from the Software Manager.

**Important** - These files require the Flatpak version, they will not work if you installed the .deb package from the PeaZip website.

### Install instructions

To install this action please follow the steps below:

1. To download the action either:

    - Download the action through the **Actions** window from the **Download** tab. (Recommended)
    - Get it from [Cinnamon Spices](https://cinnamon-spices.linuxmint.com/actions/)
        - Unpack the downloaded zip
        - Paste the contents to the **~/.local/share/nemo/actions** folder

2. Place the icons in your icons folder:

    1. Navigate to the icon from the **~/.local/share/nemo/actions/peazip-add-to-archive@xszabo3/icon_to_move/** folder
        - Alternatively you can download the icons from [here](https://github.com/xszabo3/peazip-context-menu-items-nemo/tree/main/icons)

    2. Copy the icons

    3. Navigate to ~/.local/share/icons

    4. Paste the icons into the folder


### How to group actions

Same steps with pictures [here](https://github.com/xszabo3/peazip-context-menu-items-nemo?tab=readme-ov-file#how-to-group-actions)

This feature is available from Linux Mint **22**.

1. Open the **Actions** window.

2. Switch to the Layout tab

3. Click the **+** symbol and select the new submenu option
4. Choose a group name (in this case PeaZip)

5. Click *Save*

6. Now drag the actions on the new submenu with the mouse. The result will look like this:

7. Click *Save*

## Older versions

You can find the older versions of this action in a separate [repository](https://github.com/xszabo3/peazip-context-menu-items-nemo).

## Sources

The files are **not** 100% written by me. You can find the license and copyright information of the original files in the files directly or in the accompanying note in the folder.

Here is a list of used sources

- [PeaZip](https://github.com/peazip/PeaZip/) - PeaZip is released under LGPLv3 by Giorgio Tani.

- [The original actions](https://github.com/badmotorfinger/nemo-peazip-context-menu/) are released under MIT by badmotorfinger.
