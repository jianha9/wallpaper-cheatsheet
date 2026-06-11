---
description: Install and configure the wallpaper-cheatsheet plugin (background, font scale, auto-update)
allowed-tools: Bash, Write, AskUserQuestion
---

Set up the wallpaper-cheatsheet plugin step by step. Follow each step in order.

---

## Step 1: Detect platform and Python

Run:
```bash
python3 -c "import sys; print(sys.platform)" 2>/dev/null || echo "NOT_FOUND"
```

If the output is `NOT_FOUND`, this is either Windows or Python 3 is not installed. On Windows, try:
```bash
python -c "import sys; print(sys.platform)" 2>/dev/null || echo "NOT_FOUND"
```

If both are `NOT_FOUND`, tell the user:
> Python 3 is required but was not found. Install it from https://www.python.org/downloads/ and re-run `/wallpaper-setup`.

Then stop.

Store the detected platform string (e.g. `darwin`, `linux`, `win32`) and the working Python command (`python3` or `python`) for use in later steps.

---

## Step 2: Install Python dependencies

**macOS / Linux** (platform is `darwin` or `linux`):
```bash
pip3 install pillow watchdog -q
```

**Windows** (platform is `win32`):
```bash
pip install pillow watchdog -q
```

If this fails, tell the user to check that pip is installed and retry.

---

## Step 3: Ask configuration questions

Ask all three questions **one at a time** using AskUserQuestion.

### Question 1 — Background

- header: `Background`
- question: `Choose a background style for your wallpaper:`
- options:
  1. `Dark gradient (default)` — description: `Smooth dark navy-to-midnight blue gradient`
  2. `dark-mesh.jpg` — description: `Dark navy with subtle grid mesh`
  3. `deep-space.jpg` — description: `Near-black with scattered stars`
  4. `carbon.jpg` — description: `Dark charcoal diagonal stripe pattern`

### Question 2 — Font scale

- header: `Font scale`
- question: `Choose font scale for the wallpaper:`
- options:
  1. `1.0 — standard (default)`
  2. `0.85 — compact (more commands visible)`
  3. `1.15 — large (easier to read from distance)`

### Question 3 — Update mode

- header: `Update mode`
- question: `How should the wallpaper stay up to date?`
- options:
  1. `Auto — file watcher regenerates wallpaper when plugins change (default)`
  2. `Manual — run /wallpaper-update whenever you want a refresh`

---

## Step 4: Find the plugin install path

Read `~/.claude/plugins/installed_plugins.json`:
```bash
cat ~/.claude/plugins/installed_plugins.json
```

Find the entry whose key contains `wallpaper-cheatsheet`. The value is the install path. Store this as `INSTALL_PATH`.

---

## Step 5: Write config.json

Create the wallpaper config directory and write the config file.

First create the directory:
```bash
mkdir -p ~/.claude/wallpaper
```

Then write `~/.claude/wallpaper/config.json` with the following content, substituting values based on user answers:

- **Background** mapping:
  - Option 1 (Dark gradient): `"type": "gradient"`, `"image_path": null`
  - Option 2 (dark-mesh.jpg): `"type": "image"`, `"image_path": "<INSTALL_PATH>/assets/backgrounds/dark-mesh.jpg"`
  - Option 3 (deep-space.jpg): `"type": "image"`, `"image_path": "<INSTALL_PATH>/assets/backgrounds/deep-space.jpg"`
  - Option 4 (carbon.jpg): `"type": "image"`, `"image_path": "<INSTALL_PATH>/assets/backgrounds/carbon.jpg"`

- **Font scale** mapping:
  - Option 1 → `1.0`
  - Option 2 → `0.85`
  - Option 3 → `1.15`

- **Update mode** mapping:
  - Option 1 → `"auto"`
  - Option 2 → `"manual"`

Write the file with these exact fields (replace placeholder values with the mapped ones):

```json
{
  "update_mode": "<auto or manual>",
  "background": {
    "type": "<gradient or image>",
    "image_path": <null or "<INSTALL_PATH>/assets/backgrounds/<name>.jpg">
  },
  "font": {
    "scale": <1.0, 0.85, or 1.15>
  }
}
```

---

## Step 6: Copy runner.py

Copy the plugin's runner script to the wallpaper config directory:

```bash
mkdir -p ~/.claude/wallpaper
cp "<INSTALL_PATH>/runner.py" ~/.claude/wallpaper/runner.py
chmod +x ~/.claude/wallpaper/runner.py
```

Replace `<INSTALL_PATH>` with the path found in Step 4.

---

## Step 7: Register the auto-update daemon (skip entirely if user chose Manual mode)

If the user chose **Manual** update mode, skip this step completely.

If the user chose **Auto** update mode, register a startup daemon based on platform:

### macOS (`darwin`)

Detect the python3 path and home directory:
```bash
which python3
echo $HOME
```

Write the file `~/Library/LaunchAgents/com.wallpaper-cheatsheet.plist` with this content (substitute the actual `python3` path and `$HOME` value):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.wallpaper-cheatsheet</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/python3</string>
        <string>/Users/<user>/.claude/wallpaper/runner.py</string>
        <string>--watch</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/<user>/.claude/wallpaper/generate.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/<user>/.claude/wallpaper/generate.log</string>
</dict>
</plist>
```

Replace `/path/to/python3` with the output of `which python3`, and replace `/Users/<user>` with the actual `$HOME` value.

Then load the daemon:
```bash
launchctl load ~/Library/LaunchAgents/com.wallpaper-cheatsheet.plist
```

### Linux (`linux`)

Detect the python3 path and home directory:
```bash
which python3
echo $HOME
```

Write the file `~/.config/systemd/user/wallpaper-cheatsheet.service` with this content (substitute actual paths):

```ini
[Unit]
Description=wallpaper-cheatsheet file watcher

[Service]
ExecStart=/usr/bin/python3 /home/<user>/.claude/wallpaper/runner.py --watch
Restart=on-failure
StandardOutput=append:/home/<user>/.claude/wallpaper/generate.log
StandardError=append:/home/<user>/.claude/wallpaper/generate.log

[Install]
WantedBy=default.target
```

Replace `/usr/bin/python3` with the actual path from `which python3`, and replace `/home/<user>` with the actual `$HOME` value. Then enable and start it:
```bash
systemctl --user enable --now wallpaper-cheatsheet
```

### Windows (`win32`)

Run this PowerShell command to register a Task Scheduler task:
```bash
powershell -Command "
\$python = (Get-Command python).Source
\$runner = \"\$env:USERPROFILE\\.claude\\wallpaper\\runner.py\"
\$action = New-ScheduledTaskAction -Execute \$python -Argument \"\$runner --watch\"
\$trigger = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName 'wallpaper-cheatsheet' -Action \$action -Trigger \$trigger -RunLevel Highest -Force
"
```

---

## Step 8: Generate the first wallpaper

**macOS / Linux**:
```bash
python3 "<INSTALL_PATH>/generate.py"
```

**Windows**:
```bash
python "<INSTALL_PATH>/generate.py"
```

Replace `<INSTALL_PATH>` with the path found in Step 4.

If the command outputs an error about setting the wallpaper (e.g., `set_wallpaper` failed), tell the user:
> Wallpaper image saved to `~/.agent-wallpaper/wallpaper.png`. Open your OS wallpaper settings to set it manually.

---

## Step 9: Print summary

Print a clear summary to the user:

- **Background:** what was configured (gradient or image filename)
- **Font scale:** the chosen value (1.0, 0.85, or 1.15)
- **Update mode:** Auto (file watcher running) or Manual
- **To refresh the wallpaper manually:** run `/wallpaper-update`
- **To uninstall:** run `/wallpaper-remove`
