# wallpaper-cheatsheet

A Claude Code plugin that generates a dark glassmorphism desktop wallpaper showing all
slash commands (built-in + installed plugins) as a live cheatsheet.

## Commands

- `/wallpaper-setup` — Guided install: configures background, font scale, update mode,
  writes config.json, copies runner.py, registers auto-update daemon (launchd/systemd/Task Scheduler)
- `/wallpaper-update` — Manually refresh the wallpaper (re-scans plugins, keeps config)
- `/wallpaper-remove` — Remove the wallpaper, daemon, and all generated files

## Key files

- `generate.py` — Image renderer. Reads `~/.claude/wallpaper/config.json` and
  `~/.claude/plugins/installed_plugins.json`. Writes `~/.agent-wallpaper/wallpaper.png`.
- `runner.py` — Stable wrapper copied to `~/.claude/wallpaper/runner.py` during setup.
  Resolves the current versioned generate.py at runtime so plugin updates don't break the daemon.
- `assets/backgrounds/` — Three bundled dark background presets.

## Requirements

Python 3, pillow, watchdog
