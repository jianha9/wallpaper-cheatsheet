---
description: Uninstall the wallpaper-cheatsheet daemon and config files
allowed-tools: Bash
---

Remove all wallpaper-cheatsheet runtime files and stop the auto-update daemon. This does NOT uninstall the plugin itself.

## Step 1: Detect platform

Run:
```bash
python3 -c "import sys; print(sys.platform)" 2>/dev/null || python -c "import sys; print(sys.platform)" 2>/dev/null || echo "unknown"
```

Use the output to select the correct daemon removal commands below.

## Step 2: Unload and delete the startup daemon

### macOS (`darwin`)
```bash
launchctl unload ~/Library/LaunchAgents/com.wallpaper-cheatsheet.plist 2>/dev/null
rm -f ~/Library/LaunchAgents/com.wallpaper-cheatsheet.plist
```

### Linux (`linux`)
```bash
systemctl --user disable --now wallpaper-cheatsheet 2>/dev/null
rm -f ~/.config/systemd/user/wallpaper-cheatsheet.service
```

### Windows (`win32`)
```bash
powershell -Command "Unregister-ScheduledTask -TaskName 'wallpaper-cheatsheet' -Confirm:\$false -ErrorAction SilentlyContinue"
```

## Step 3: Remove config and runtime files

Run each of these commands:

```bash
rm -f ~/.claude/wallpaper/runner.py
```

```bash
rm -f ~/.claude/wallpaper/config.json
```

```bash
rm -f ~/.claude/wallpaper/generate.log
```

```bash
rm -f ~/.agent-wallpaper/wallpaper.png
```

## Step 4: Print completion message

Tell the user:
> Done. Open your OS wallpaper settings to choose a new background.
