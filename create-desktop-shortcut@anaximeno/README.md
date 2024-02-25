# Create Desktop Shortcut

Creates a shortcut of folders, applications, files, and others, on the desktop folder.

## Installation Instructions

It is highly recommendable that you install this action through the actions settings module available by default starting from LM 21.3 and in the updated versions of LMDE 6 (write `actions` on the app menu to find this module), however, if that is not available or accessible for any reason follow through the following procedures to install this action in your system:

1. The following dependencies must be available on your system: `nemo`, `xdg-user-dirs`, `python3`, `bash`, and `gtk3`, if you are on a more recent version of Linux Mint it is very likelly that they are already installed on your system,

2. Download the package of this action from the [cinnamon spices web-site](https://cinnamon-spices.linuxmint.com/actions/view/11),

3. After downloading the package open the terminal in the folder the where the downloaded `create-desktop-shortcut@anaximeno.zip` file is located and run the following commands to install the action on your system:

```bash
unzip create-desktop-shortcut@anaximeno.zip -d ~/.local/share/nemo/actions
cd ~/.local/share/nemo/actions && cinnamon-xlet-makepot -i create-desktop-shortcut@anaximeno && cd -1
```
