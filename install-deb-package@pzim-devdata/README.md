# Install Debian Package

Install Debian (.deb) packages directly from Nemo's context menu with automatic dependency resolution.

This action uses `apt install` instead of `dpkg -i`, which means it will automatically download and install any missing dependencies required by the package. The installation is performed in a terminal window where you can see the progress and enter your password when prompted.

## Requirements

- `apt` (pre-installed on Debian-based systems)

## Installation

### Via Cinnamon Spices

1. Right-click on the desktop
2. Select "System Settings"
3. Go to "Actions"
4. Click "Download" at the bottom
5. Search for "Install Debian Package"
6. Click "Install"

### Manual Installation

```bash
# Copy action to Nemo actions directory
cp -r install-deb-package@pzim-devdata ~/.local/share/nemo/actions/
```

## Usage

1. Right-click on any .deb file in Nemo
2. Select "Install Debian Package" from the context menu
3. A terminal window will open
4. Enter your password when prompted
5. The package and its dependencies will be installed automatically

## Why apt install instead of dpkg -i?

This action uses `apt install` instead of `dpkg -i` because:
- **Automatic dependency resolution**: apt will download and install any missing dependencies
- **Better error handling**: Clear messages if something goes wrong
- **Package verification**: Checks if the package is already installed

## Author

pzim-devdata
