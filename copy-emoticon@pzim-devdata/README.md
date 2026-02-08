# Copy an Emoticon

Quick access to commonly used emoticons with clipboard copy functionality.

## Features

- **30 common emoticons** organized by category (hands, faces, symbols)
- **One-click copy** to clipboard
- **Visual separators** between categories
- **"More icons..." button** to access the full character map (gnome-characters)
- **Desktop notifications** to confirm copy action
- **Lightweight** using zenity dialog

## Usage

Right-click in any Nemo window (or on the desktop) and select **"Copy an Emoticon"** from the context menu.

A dialog will appear with:
1. **Hand gestures** (👍 👎 👌 ✌️ 🤝 🙏)
2. **Face emoticons** (😀 😂 😊 😍 🥰 😘 😉 🤔 😎 😢 😭 😡 🤗 🤩 😴)
3. **Symbols** (❤️ ⭐ ✨ 🎉 🎊 🔥 💯)
4. **"More icons..."** button to open the complete character map

Click on any emoticon to copy it to your clipboard. A notification will confirm the action.

## Dependencies

- `zenity` - For the selection dialog
- `xclip` - For clipboard management
- `gnome-characters` - For accessing the full character library
- `notify-send` - For desktop notifications (usually pre-installed)

## Installation

### From Cinnamon Spices

1. Open **System Settings** → **Actions**
2. Search for **"Copy an Emoticon"**
3. Click **Install**

### Manual Installation

1. Download the latest release
2. Extract to `~/.local/share/nemo/actions/`
3. Restart Nemo: `nemo -q && nemo &`

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

## License

This Action is provided as-is under the GPL-3.0 license.

## Author

**pzim-devdata**

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
