import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import runner


def _make_plugins_json(tmp_path, install_path):
    pj = tmp_path / ".claude" / "plugins" / "installed_plugins.json"
    pj.parent.mkdir(parents=True, exist_ok=True)
    pj.write_text(json.dumps({"version": 2, "plugins": {
        "wallpaper-cheatsheet@repo": [{"installPath": str(install_path), "version": "1.0.0"}]
    }}))
    return pj


def test_find_generate_py_finds_existing(tmp_path, monkeypatch):
    install = tmp_path / "wallpaper-cheatsheet" / "1.0.0"
    install.mkdir(parents=True)
    gpy = install / "generate.py"
    gpy.write_text("# generate")
    _make_plugins_json(tmp_path, install)
    # patch Path.home() by monkeypatching the plugins JSON path
    monkeypatch.setattr(
        runner.Path, "home", lambda: tmp_path
    )
    result = runner.find_generate_py()
    assert result == gpy


def test_find_generate_py_missing_plugin(tmp_path, monkeypatch):
    pj = tmp_path / ".claude" / "plugins" / "installed_plugins.json"
    pj.parent.mkdir(parents=True, exist_ok=True)
    pj.write_text(json.dumps({"version": 2, "plugins": {}}))
    monkeypatch.setattr(runner.Path, "home", lambda: tmp_path)
    assert runner.find_generate_py() is None


def test_find_generate_py_missing_json(tmp_path, monkeypatch):
    monkeypatch.setattr(runner.Path, "home", lambda: tmp_path)
    assert runner.find_generate_py() is None


def test_run_once_calls_generate(tmp_path, monkeypatch):
    install = tmp_path / "wallpaper-cheatsheet" / "1.0.0"
    install.mkdir(parents=True)
    gpy = install / "generate.py"
    gpy.write_text("# generate")
    _make_plugins_json(tmp_path, install)
    monkeypatch.setattr(runner.Path, "home", lambda: tmp_path)
    calls = []
    monkeypatch.setattr(runner.subprocess, "run", lambda args, **kw: calls.append(args))
    runner.run_once()
    assert len(calls) == 1
    assert str(gpy) in calls[0]


def test_run_once_missing_plugin_prints_warning(tmp_path, monkeypatch, capsys):
    pj = tmp_path / ".claude" / "plugins" / "installed_plugins.json"
    pj.parent.mkdir(parents=True, exist_ok=True)
    pj.write_text(json.dumps({"version": 2, "plugins": {}}))
    monkeypatch.setattr(runner.Path, "home", lambda: tmp_path)
    runner.run_once()  # should not raise
    captured = capsys.readouterr()
    assert "wallpaper-cheatsheet" in captured.err
