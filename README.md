# Cremisi i3 Dotfiles

> *Ex umbra in lucem.* — A reliquary of configurations, bound in crypt stone and blood.

Gothic and arcane: an i3 desktop built around the **Cremisi Obsidian** colour scheme — sixteen materials drawn from bone, stone, crimson and candlewax.

Full colour scheme and editor ports: [vari-sh.github.io/cremisi](https://vari-sh.github.io/cremisi/)

---

## Screenshots

![Cremisi desktop — editor and terminal](Screenshots/Cremisi_desktop_1.png)

![Cremisi desktop — file manager and fastfetch](Screenshots/Cremisi_desktop_2.png)

---

## The Palette

| Name | Hex | Role |
|---|---|---|
| `ground` | `#17171c` | Crypt stone — background |
| `ink` | `#e9e1d1` | Bone — foreground text |
| `crimson` | `#c42740` | The accent. The only one. |
| `blood` | `#e2586a` | Parentheses, errors, cursor |
| `lapis` | `#6886bb` | Functions, prompt |
| `amber` | `#cf9142` | Git, durations, warnings |
| `malachite` | `#44a078` | Success, Python |
| `verdigris` | `#6bb3b0` | Time |
| `amethyst` | `#9c7bb0` | OS, user |
| `tallow` | `#dccb9a` | Path, types |
| `incense` | `#9e8d99` | Comments, muted text |
| `wine` | `#b27a90` | Hostname |
| `petal` | `#c58f96` | Window title |
| `sealwax` | `#c6784c` | Warmth |
| `iron` | `#9a948c` | Neutral punctuation |

---

## Contents

All configurations live under `Dotfiles/`:

```
i3/               Window manager — Cremisi Obsidian theming, keybindings, gaps
polybar/          Status bar — IP, CPU, RAM, battery, volume, clock
kitty/            Terminal emulator — colours and font
rofi/             Launcher and power menu
dunst/            Notification daemon
picom/            Compositor — blur, shadows, rounded corners
starship.toml     Shell prompt
betterlockscreen/ Lock screen
yazi/             File manager — Cremisi Obsidian and Catppuccin Mocha flavours
```

---

## Dependencies

- **i3** — tiling window manager
- **polybar** — status bar
- **kitty** — terminal
- **rofi** — application launcher
- **dunst** — notifications
- **picom** — compositor
- **starship** — shell prompt
- **betterlockscreen** — lock screen
- **yazi** — file manager
- **JetBrainsMono Nerd Font** — the sole typeface
- **nitrogen** — wallpaper
- **flameshot** — screenshots
- **greenclip** — clipboard manager
- **jq**, **curl** — required by the polybar IP monitor script

---

## Rite of Entry

```bash
git clone https://github.com/vari-sh/Cremisi-i3-dotfile
cd Cremisi-i3-dotfile/Dotfiles

# Copy into ~/.config/
cp -r i3 polybar kitty rofi dunst picom yazi ~/.config/
cp starship.toml ~/.config/
cp betterlockscreen/betterlockscreenrc ~/.config/betterlockscreen/

# Reload i3
i3-msg restart
```

Or use `stow` if you prefer symlinks:

```bash
stow --target ~/.config .
```
