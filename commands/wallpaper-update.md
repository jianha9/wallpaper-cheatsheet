---
description: Manually regenerate the wallpaper from current plugin commands
allowed-tools: Bash
---

Refresh the wallpaper by running the installed runner script.

## Step 1: Check that the plugin is set up

Verify that the runner script exists:

```bash
test -f ~/.claude/wallpaper/runner.py && echo "EXISTS" || echo "MISSING"
```

If the output is `MISSING`, tell the user:
> The wallpaper runner is not installed. Run `/wallpaper-setup` first to complete setup.

Then stop.

## Step 2: Run the runner

**macOS / Linux** (platform is `darwin` or `linux`):
```bash
python3 ~/.claude/wallpaper/runner.py
```

**Windows** (platform is `win32`):
```bash
python %USERPROFILE%\.claude\wallpaper\runner.py
```

To detect platform, run:
```bash
python3 -c "import sys; print(sys.platform)" 2>/dev/null || python -c "import sys; print(sys.platform)" 2>/dev/null
```

If the runner exits without error, the wallpaper has been regenerated. Tell the user the wallpaper was updated successfully.

If the runner prints an error about setting the wallpaper, tell the user:
> Wallpaper image saved to `~/.agent-wallpaper/wallpaper.png`. Open your OS wallpaper settings to set it manually.
