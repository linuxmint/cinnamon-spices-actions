#! /bin/bash

TEXTDOMAIN="verify-sha256sum@rcalixte"
TEXTDOMAINDIR="${HOME}/.local/share/locale"
FILENAME="$1"
BASENAME="$(/usr/bin/basename "$FILENAME")"
TITLE="SHA256SUM: ${BASENAME}"
_BUSY=$"Calculating sha256sum for"
_PROMPT=$"Please enter the hash (64 characters) to match:"
_INVALID_HASH=$"The provided hash was invalid. Please try again."
_SUCCESS=$"The hashes are the same"
_FAILURE=$"The hashes are not the same"
_REMOTE=$"The hash you provided"
_LOCAL=$"The file's hash"
BUSY="$(/usr/bin/gettext "$_BUSY")"
PROMPT="$(/usr/bin/gettext "$_PROMPT")"
INVALID_HASH="$(/usr/bin/gettext "$_INVALID_HASH")"
SUCCESS="$(/usr/bin/gettext "$_SUCCESS")"
FAILURE="$(/usr/bin/gettext "$_FAILURE")"
REMOTE="$(/usr/bin/gettext "$_REMOTE")"
LOCAL="$(/usr/bin/gettext "$_LOCAL")"

input_hash=$(/usr/bin/zenity --entry --title="${TITLE}" --text="${PROMPT}" --width=520 | /usr/bin/tr -d '[:space:]')

[[ -z $input_hash ]] && exit 1

[[ ${#input_hash} -ne 64 ]] && /usr/bin/zenity --error --text "${INVALID_HASH}" && exit 1

input_hash_lowered=$(/usr/bin/echo "${input_hash}" | /usr/bin/tr "[:upper:]" "[:lower:]")

(
  HASH=$(/usr/bin/sha256sum "${FILENAME}" | /usr/bin/cut -f1 -d' ')
  exec 1>&-
  if [[ "${input_hash_lowered}" == "${HASH}" ]]; then
    /usr/bin/zenity --info --title="${TITLE}" --text="${SUCCESS}:\n\n${HASH}" --no-wrap
  else
    /usr/bin/zenity --error --title="${TITLE}" --text="${FAILURE}.\n\n${REMOTE}:\n${input_hash_lowered}\n\n${LOCAL}:\n${HASH}" --no-wrap
  fi
) | /usr/bin/zenity --progress --title="${BUSY} ${FILENAME}..." --auto-close --no-cancel --pulsate
