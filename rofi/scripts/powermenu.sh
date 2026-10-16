#!/bin/bash

# Options
lock="  Lock"
logout="󰗽  Logout"
reboot="  Reboot"
shutdown="  Shutdown"

# Put everything into a single variable
options="$lock\n$logout\n$reboot\n$shutdown"

# Open Rofi
selected_option=$(echo -e "$options" | rofi -dmenu -i -p "Power" -config ~/.config/rofi/config.rasi)

# Run the command matching the selection
case "$selected_option" in
    "$lock")
        betterlockscreen -l blur
        ;;
    "$logout")
        i3-msg exit
        ;;
    "$reboot")
        systemctl reboot
        ;;
    "$shutdown")
        systemctl poweroff
        ;;
esac