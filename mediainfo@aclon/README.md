# MEDIAINFO
View meta info via `mediainfo`. `:q!` to exit&view the English language, use `vim` firstly.

## DEPENDENCIES
The following programs must be installed and available:

- `mediainfo` for media meta data
- `x-terminal-emulator` for call your default GUI terminal
- `less` for text viewing


The following packages could be installed for better experience:

- `neovim` for text editing
- `mediainfo-gui` for mediainfo-gui.nemo_action

## TEST TRANSLATION
```bash
uuid=mediainfo@aclon && ./test-spice -r && ./cinnamon-spices-makepot $uuid --install && ./test-spice $uuid
```