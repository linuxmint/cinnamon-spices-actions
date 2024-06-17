#!/bin/bash
P=$1
shift
F=$(printf '%q ' "$@")
act=$(dirname $0)
csv="$act/po/$(echo $LANG | sed 's/.UTF-8//').csv"
editor="(vim -c 'set filetype=toml' -c 'set ignorecase' || less)"
cmd="[ -f $csv ] || $act/wget_lang.sh ; cd $P ; mediainfo --Language=file://$csv $F | sed 's/ *:/齾:/' | column -s '齾' -t -L | $editor ; mediainfo $F | $editor"
x-terminal-emulator -e "$cmd"

# echo $cmd >> /home/n/.local/share/nemo/actions/mediainfo@aclon/cmd.log
# x-terminal-emulator -e "echo x-terminal-emulator -e \"$cmd\" | less"
