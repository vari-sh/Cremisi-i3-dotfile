#!/bin/bash

# --- Cremisi Obsidian Palette ---
BG="17171c66"
TEXT="e9e1d1ff"
BLOOD="e2586aff"
CRIMSON="c42740ff"
WINE="b27a90ff"
LAPIS="6886bbff"
BORDER="27272cff"
AMBER="cf9142ff"

# Font definition
FONT="JetBrainsMono Nerd Font"

i3lock \
  --image="/usr/share/background/custom/tree_blurred.jpg" \
  --fill \
  --indicator \
  --radius=120 \
  --ring-width=10 \
  \
  --clock \
  --time-str="%H:%M:%S" \
  --time-font="$FONT" \
  --time-size=42 \
  --time-color="$TEXT" \
  --time-pos="x+w/2:y+h/2-170" \
  \
  --date-str="" \
  \
  --inside-color="$BG" \
  --ring-color="$BORDER" \
  --separator-color="00000000" \
  \
  --keyhl-color="$BLOOD" \
  --bshl-color="$WINE" \
  \
  --verif-text="Verifying..." \
  --verif-font="$FONT" \
  --verif-color="$TEXT" \
  --insidever-color="$BG" \
  --ringver-color="$LAPIS" \
  \
  --wrong-text="Failure!" \
  --wrong-font="$FONT" \
  --wrong-color="$BLOOD" \
  --insidewrong-color="$BG" \
  --ringwrong-color="$CRIMSON" \
  \
  --greeter-text="Type Password..." \
  --greeter-font="$FONT" \
  --greeter-color="$TEXT" \
  --greeter-size=16 \
  --greeter-pos="x+w/2:y+h/2+170" \
  \
  --modif-color="$AMBER" \
  --layout-font="$FONT" \
  --layout-color="$TEXT" \
  --force-clock
