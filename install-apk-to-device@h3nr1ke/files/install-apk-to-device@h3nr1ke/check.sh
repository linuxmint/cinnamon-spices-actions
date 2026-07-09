#!/bin/bash
# Used by Nemo Conditions=exec: exit 0 only if the action can run.
# No UI here — avoids error dialogs every time the context menu is built.

: "${1:-}"

missing=0
for cmd in adb emulator zenity; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        missing=1
        break
    fi
done

exit "$missing"
