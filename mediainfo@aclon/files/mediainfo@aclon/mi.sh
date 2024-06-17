#!/bin/bash
P=$1
cd $P
shift
F=$(printf '%q ' "$@")
act=$(dirname $0)
csv="$act/po/$(echo $LANG | sed 's/.UTF-8//').csv"
editor="(vim -c 'set filetype=config' -c 'set ignorecase' || less)"
format="sed 's/ *:/齾:/' | column -t -L -s '齾' -o ''"
# format="format"                               # Shorter 1st col mode
cmd="[ -f $csv ] || $act/wget_lang.sh ; mediainfo --Language=file://$csv $F | $format | $editor ; mediainfo $F | $format | $editor"
# cmd="bash -c \" . $act/func.sh ; $cmd \""     # Shorter 1st col mode
x-terminal-emulator -e "$cmd"

# echo $cmd_new >> $act/cmd.log
# x-terminal-emulator -e "echo x-terminal-emulator -e \"$cmd\" | less ; echo source $act/func.sh | less ; source $act/func.sh ; echo aaa $(declare -f format) | less"
