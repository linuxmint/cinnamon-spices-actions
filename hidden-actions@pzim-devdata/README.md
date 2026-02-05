# Hidden Actions

Execute custom scripts with Ctrl+Right-click for advanced users. Keep your context menu clean while having quick access to powerful scripts.

## Features

- **Ctrl+Right-click activation** - Action only appears when Control key is pressed
- **Script launcher** - Clean zenity dialog to select scripts
- **Numbered list** - Scripts are numbered for easy selection
- **Auto-folder creation** - Creates `~/.local/share/hidden_scripts/` automatically
- **Empty folder handling** - Offers to open folder in Nemo when no scripts found
- **Lock icon theme** - Uses consistent lock icon for hidden features

## Usage

### Basic Usage

1. Right-click on empty space in Nemo (or desktop) → Nothing appears
2. **Hold Ctrl + Right-click** → "🔒 Hidden Actions" appears
3. Click the action → Script launcher dialog opens
4. Select a script → Script executes

### Adding Your Scripts

1. Place your executable scripts in `~/.local/share/hidden_scripts/`
2. Make them executable: `chmod +x ~/.local/share/hidden_scripts/your-script.sh`
3. Access via Ctrl+Right-click

### Example Scripts

Create a simple test script:

```bash
cat > ~/.local/share/hidden_scripts/hello.sh << 'EOF'
#!/bin/bash
notify-send "Hello" "This is a hidden action!" -i dialog-information
EOF

chmod +x ~/.local/share/hidden_scripts/hello.sh
```

Now Ctrl+Right-click in Nemo and run it!

## Use Cases

**Perfect for:**
- System administration scripts
- Development tools
- Advanced file operations
- Testing and debugging utilities
- Personal automation scripts

**Why hide them?**
- Reduces context menu clutter
- Prevents accidental execution
- Separates casual from power-user features
- Professional, clean interface

## Dependencies

- `python3` - For Ctrl key detection (usually pre-installed)
- `python3-xlib` - X11 library for keyboard state detection
- `zenity` - Dialog interface (usually pre-installed)

### Installing Dependencies

```bash
sudo apt install python3-xlib zenity
```

## Technical Details

### How Ctrl Detection Works

The action uses a Python script (`is-ctrl-pressed.py`) that:
1. Connects to X11 display server
2. Queries current keyboard modifier state
3. Returns exit code 0 if Ctrl is pressed, 1 otherwise
4. Nemo uses this as a condition to show/hide the action

### File Structure

```
~/.local/share/nemo/actions/
├── hidden-actions@pzim-devdata/
│   ├── is-ctrl-pressed.py          # Ctrl detection script
│   └── run-hidden-script.sh        # Script launcher
└── hidden-actions.nemo_action      # Nemo action definition

~/.local/share/hidden_scripts/             # Your custom scripts go here
├── script1.sh
├── script2.sh
└── ...
```

## Troubleshooting

### Action doesn't appear even with Ctrl

1. Verify python3-xlib is installed:

2. Check script permissions:
   ```bash
   ls -la ~/.local/share/nemo/actions/hidden-actions@pzim-devdata/
   ```
   Both `.py` and `.sh` files should be executable.

3. Restart Nemo:
   ```bash
   nemo -q && nemo &
   ```

### Scripts don't execute

Make sure your scripts in `~/.local/share/hidden_scripts/` are executable:

```bash
chmod +x ~/.local/share/hidden_scripts/*
```

## Translations

Available in 21 languages:
- Arabic (ar)
- Catalan (ca)
- Czech (cs)
- Danish (da)
- German (de)
- English Canada (en_CA)
- Spanish (es)
- Finnish (fi)
- French Canada (fr_CA)
- French (fr)
- Hungarian (hu)
- Italian (it)
- Japanese (ja)
- Dutch (nl)
- Polish (pl)
- Portuguese (pt)
- Russian (ru)
- Turkish (tr)
- Ukrainian (uk)
- Vietnamese (vi)
- Chinese Simplified (zh_CN)

## Security Note

Scripts in `~/.local/share/hidden_scripts/` can perform any action with your user permissions. Only add scripts you trust and understand.


## Author

**pzim-devdata**

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
