# wallpaper-cheatsheet

A Claude Code plugin that turns your desktop wallpaper into a live cheatsheet of all your slash commands.

## What it does

Wallpaper-cheatsheet generates a dark glassmorphism wallpaper showing all built-in Claude Code commands plus every installed plugin's slash commands, arranged in a multi-column card layout. It auto-regenerates whenever your plugins change via a background file watcher. Supports macOS, Linux, and Windows.

## Install

```
/plugin install wallpaper-cheatsheet
/wallpaper-setup
```

## Commands

| Command | Description |
|---|---|
| `/wallpaper-setup` | Guided install: configure background, font, auto-update mode |
| `/wallpaper-update` | Manually refresh the wallpaper |
| `/wallpaper-remove` | Uninstall and clean up |

## Configuration

After setup, edit `~/.claude/wallpaper/config.json` to tweak appearance:

- `background.type`: `"gradient"` (default) or `"image"`
- `background.image_path`: path to a custom image (or one of the bundled presets in `assets/backgrounds/`)
- `font.scale`: `0.85` (compact), `1.0` (standard), `1.15` (large)
- `update_mode`: `"auto"` or `"manual"`

### Background presets

| File | Description |
|---|---|
| `dark-mesh.jpg` | Dark navy grid |
| `deep-space.jpg` | Starfield |
| `carbon.jpg` | Diagonal stripes |

## Requirements

- Python 3
- `pip install pillow watchdog` (done automatically by `/wallpaper-setup`)

## How auto-update works

When `update_mode` is set to `"auto"`, setup registers a platform-specific daemon — launchd on macOS, systemd on Linux, or Task Scheduler on Windows — that runs `runner.py --watch` in the background. The runner watches `~/.claude/plugins/installed_plugins.json` for changes and regenerates the wallpaper automatically whenever plugins are added or removed.

## Bug reports

Open an issue at https://github.com/jianha9/wallpaper-cheatsheet/issues

Please include your **platform** (macOS / Linux / Windows) and **Python version** (`python3 --version`) in the report.

## Contributing

PRs welcome. See `generate.py` for the rendering pipeline and `runner.py` for the file watcher.

## License

MIT
