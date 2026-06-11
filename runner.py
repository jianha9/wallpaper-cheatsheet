#!/usr/bin/env python3
"""
Stable wrapper copied to ~/.claude/wallpaper/runner.py during /wallpaper-setup.
Resolves the current generate.py from the installed wallpaper-cheatsheet plugin
at runtime — plugin version upgrades are transparent.

Usage:
    python runner.py           # run once (used by /wallpaper-update)
    python runner.py --watch   # daemon mode (used by auto-update startup)
"""
import json
import subprocess
import sys
from pathlib import Path


def find_generate_py() -> Path | None:
    """Locate generate.py from the installed wallpaper-cheatsheet plugin."""
    pj = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    try:
        data = json.loads(pj.read_text())
        for key, installs in data.get("plugins", {}).items():
            if "wallpaper-cheatsheet" in key and installs:
                gpy = Path(installs[0]["installPath"]) / "generate.py"
                if gpy.exists():
                    return gpy
    except Exception:
        pass
    return None


def run_once() -> None:
    """Find and run generate.py once."""
    gpy = find_generate_py()
    if gpy:
        subprocess.run([sys.executable, str(gpy)], check=False)
    else:
        print("wallpaper-cheatsheet: could not find generate.py — is the plugin installed?",
              file=sys.stderr)


def watch() -> None:
    """Watch installed_plugins.json for changes and re-run generate.py on each change."""
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    pj = Path.home() / ".claude" / "plugins" / "installed_plugins.json"

    class _Handler(FileSystemEventHandler):
        def on_modified(self, event):
            if Path(event.src_path).name == "installed_plugins.json":
                run_once()

        on_created = on_modified

    run_once()  # generate immediately on daemon start

    observer = Observer()
    observer.schedule(_Handler(), str(pj.parent), recursive=False)
    observer.start()
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        watch()
    else:
        run_once()
