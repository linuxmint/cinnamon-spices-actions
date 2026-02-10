# Open Link in Browser

A Nemo action that opens URLs from your clipboard directly in your default web browser.

## Features

- **Automatic detection**: The action appears in Nemo's context menu only when your clipboard contains a valid URL (http:// or https://)
- **One-click opening**: Simply right-click anywhere in Nemo and select "Open Link in Browser"
- **No file selection required**: Works from any location in Nemo
- **Desktop notifications**: Get visual feedback when a link is opened
- **Multi-environment support**: Compatible with both X11 (xclip) and Wayland (wl-paste)
- **Smart validation**: Checks clipboard content before attempting to open

## How to Use

1. Copy any URL to your clipboard (Ctrl+C)
   - Example: https://www.example.com
2. Open Nemo file manager
3. Right-click anywhere (no need to select a file)
4. Click "Open Link in Browser"
5. The URL opens in your default web browser

The action will only appear in the context menu when your clipboard contains a valid URL starting with `http://` or `https://`.

## Requirements

Depending on your display server, you need one of the following clipboard utilities:

**For X11:**
```bash
sudo apt install xclip
```

**For Wayland:**
```bash
sudo apt install wl-clipboard
```

The scripts automatically detect which environment you're using.

## Installation

The action will be automatically installed through Linux Mint's Nemo Actions manager, or you can install it manually:

1. Download the action to `~/.local/share/nemo/actions/`
2. Place the folder open-link-in-browser@pzim-devdata in `~/.local/share/nemo/actions/`
3. Make scripts executable:
```bash
chmod +x ~/.local/share/nemo/actions/open-link-in-browser@pzim-devdata/*.sh
```
4. Restart Nemo: `nemo -q`

## Technical Details

The action uses two shell scripts:

- **check-clipboard-has-url.sh**: Validates clipboard content (condition for displaying the action)
- **open-clipboard-link.sh**: Retrieves the URL and opens it using `xdg-open`

Both scripts are compatible with X11 and Wayland environments.

## Troubleshooting

**Action doesn't appear:**
- Make sure you have copied a URL starting with http:// or https://
- Verify that xclip (X11) or wl-clipboard (Wayland) is installed
- Check that scripts are executable

**Link doesn't open:**
- Verify that `xdg-open` is available on your system
- Check that you have a default browser configured

## License

This action is provided as-is for the Linux Mint community.

## Author

pzim-devdata
