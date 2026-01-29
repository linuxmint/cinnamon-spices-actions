#!/bin/bash

# ===== SECTION #1_EMOTICONS_LIST =====
# List of most commonly used emoticons organized by category
EMOTICONS=(
    "👍 Thumbs up"
    "👎 Thumbs down"
    "👌 OK hand"
    "✌️ Victory hand"
    "🤝 Handshake"
    "🙏 Folded hands"
    "────────────"
    "😀 Grinning face"
    "😂 Face with tears of joy"
    "😊 Smiling face"
    "😍 Heart eyes"
    "🥰 Smiling face with hearts"
    "😘 Face blowing a kiss"
    "😉 Winking face"
    "🤔 Thinking face"
    "😎 Smiling face with sunglasses"
    "😢 Crying face"
    "😭 Loudly crying face"
    "😡 Pouting face"
    "🤗 Hugging face"
    "🤩 Star-struck"
    "😴 Sleeping face"
    "────────────"
    "❤️ Red heart"
    "⭐ Star"
    "✨ Sparkles"
    "🎉 Party popper"
    "🎊 Confetti ball"
    "🔥 Fire"
    "💯 Hundred points"
    "────────────"
    "More icons..."
)

# ===== SECTION #2_DISPLAY_MENU =====
# Display menu with zenity
choice=$(zenity --list \
    --title="Quick Emoticons" \
    --text="Select an emoticon to copy to clipboard:" \
    --column="Emoticon" \
    "${EMOTICONS[@]}" \
    --width=350 \
    --height=600 \
    --window-icon=face-smile \
    --modal \
    2>/dev/null)

# ===== SECTION #3_PROCESS_CHOICE =====
# Process user choice
if [ -n "$choice" ]; then
    if [ "$choice" = "More icons..." ]; then
        # Open gnome-characters for more options
        gnome-characters &
    elif [ "$choice" = "────────────" ]; then
        # Separator clicked, do nothing
        :
    else
        # Extract only the emoticon (first character before space)
        emoticon=$(echo "$choice" | awk '{print $1}')
        
        # Copy to clipboard
        echo -n "$emoticon" | xclip -selection clipboard
        
        # Confirmation notification
        notify-send "Emoticon copied" "$emoticon copied to clipboard" -i face-smile -t 2000
    fi
fi
