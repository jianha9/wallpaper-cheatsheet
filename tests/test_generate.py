import json
import sys
import platform
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import generate


# ── constants ──────────────────────────────────────────────────────────────────

def test_builtin_commands_count():
    assert len(generate.BUILTIN_COMMANDS) == 11


def test_builtin_commands_are_tuples():
    for cmd in generate.BUILTIN_COMMANDS:
        assert isinstance(cmd, tuple) and len(cmd) == 2


# ── _deep_merge ────────────────────────────────────────────────────────────────

def test_deep_merge_fills_missing_keys():
    base = {"a": 1, "b": {"x": 10, "y": 20}}
    over = {"b": {"x": 99}}
    result = generate._deep_merge(base, over)
    assert result["a"] == 1
    assert result["b"]["x"] == 99
    assert result["b"]["y"] == 20


def test_deep_merge_override_wins():
    result = generate._deep_merge({"a": 1}, {"a": 2})
    assert result["a"] == 2


# ── load_config ────────────────────────────────────────────────────────────────

def test_load_config_missing_file_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(generate, "CONFIG_PATH", tmp_path / "nonexistent.json")
    cfg = generate.load_config()
    assert cfg["update_mode"] == "auto"
    assert cfg["background"]["type"] == "gradient"
    assert cfg["font"]["scale"] == 1.0


def test_load_config_reads_values(tmp_path, monkeypatch):
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"update_mode": "manual", "font": {"scale": 1.15}}))
    monkeypatch.setattr(generate, "CONFIG_PATH", p)
    cfg = generate.load_config()
    assert cfg["update_mode"] == "manual"
    assert cfg["font"]["scale"] == 1.15
    assert cfg["font"]["ui_family"] is None  # default preserved


def test_load_config_partial_background(tmp_path, monkeypatch):
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"background": {"type": "image", "image_path": "/some/img.jpg"}}))
    monkeypatch.setattr(generate, "CONFIG_PATH", p)
    cfg = generate.load_config()
    assert cfg["background"]["type"] == "image"
    assert cfg["background"]["image_path"] == "/some/img.jpg"


# ── _platform_font_paths ───────────────────────────────────────────────────────

def test_platform_font_paths_returns_list(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    paths = generate._platform_font_paths(mono=False, bold=False)
    assert isinstance(paths, list)
    assert len(paths) > 0


def test_platform_font_paths_darwin_mono(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    paths = generate._platform_font_paths(mono=True, bold=False)
    assert any("Mono" in p or "Menlo" in p for p in paths)


def test_platform_font_paths_linux(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Linux")
    paths = generate._platform_font_paths(mono=False, bold=False)
    assert any("dejavu" in p.lower() or "liberation" in p.lower() for p in paths)


# ── load_font ──────────────────────────────────────────────────────────────────

def test_load_font_returns_font_object():
    font = generate.load_font(14)
    assert font is not None


def test_load_font_respects_cfg_ui_family(tmp_path):
    cfg = {
        "font": {
            "scale": 1.0,
            "ui_family": "/System/Library/Fonts/SFNS.ttf",
            "mono_family": None,
            "bold_family": None,
        }
    }
    font = generate.load_font(12, mono=False, bold=False, cfg=cfg)
    assert font is not None


def test_load_font_falls_back_gracefully():
    cfg = {
        "font": {
            "scale": 1.0,
            "ui_family": "/nonexistent/font.ttf",
            "mono_family": None,
            "bold_family": None,
        }
    }
    font = generate.load_font(12, cfg=cfg)
    assert font is not None  # load_default() fallback


# ── _extract_description ──────────────────────────────────────────────────────

def test_extract_description_basic(tmp_path):
    md = tmp_path / "SKILL.md"
    md.write_text("---\nname: test\ndescription: Turn ideas into designs\n---\n# Body")
    assert generate._extract_description(md) == "Turn ideas into designs"

def test_extract_description_truncates_at_period(tmp_path):
    md = tmp_path / "SKILL.md"
    md.write_text("---\ndescription: Use before coding. More text.\n---\n")
    assert generate._extract_description(md) == "Use before coding"

def test_extract_description_truncates_at_word_boundary(tmp_path):
    md = tmp_path / "SKILL.md"
    md.write_text("---\ndescription: Use when implementing any feature or bugfix before writing implementation code\n---\n")
    result = generate._extract_description(md)
    assert result.endswith("…")
    assert len(result) <= 56  # 55 chars + ellipsis
    assert " " not in result[result.rfind("…") - 1]  # no trailing space before ellipsis

def test_extract_description_no_frontmatter(tmp_path):
    md = tmp_path / "SKILL.md"
    md.write_text("# Just a heading")
    assert generate._extract_description(md) == ""

def test_extract_description_no_closing_delimiter(tmp_path):
    md = tmp_path / "SKILL.md"
    md.write_text("---\ndescription: In frontmatter\n# Body\ndescription: Not valid\n")
    assert generate._extract_description(md) == ""

def test_extract_description_missing_file(tmp_path):
    assert generate._extract_description(tmp_path / "missing.md") == ""

# ── _parse_plugins / parse_commands ──────────────────────────────────────────

def _make_plugins_json(tmp_path, plugin_name, skills):
    install = tmp_path / "cache" / plugin_name / "1.0.0"
    for skill_name, desc in skills:
        sd = install / "skills" / skill_name
        sd.mkdir(parents=True)
        (sd / "SKILL.md").write_text(f"---\ndescription: {desc}\n---\n")
    pj = tmp_path / "installed_plugins.json"
    pj.write_text(json.dumps({"version": 2, "plugins": {
        f"{plugin_name}@repo": [{"installPath": str(install), "version": "1.0.0"}]
    }}))
    return pj

def test_parse_plugins_returns_unified_format(tmp_path, monkeypatch):
    pj = _make_plugins_json(tmp_path, "superpowers",
                            [("brainstorming", "Explore design"), ("writing-plans", "Plan tasks")])
    monkeypatch.setattr(generate, "PLUGINS_JSON", pj)
    result = generate._parse_plugins()
    assert len(result) == 2
    assert result[0] == {"group": "superpowers", "skill": "/brainstorming", "description": "Explore design"}

def test_parse_plugins_sorted(tmp_path, monkeypatch):
    install_a = tmp_path / "a" / "1.0"
    install_b = tmp_path / "b" / "1.0"
    for install, sname in [(install_a, "z-skill"), (install_b, "a-skill")]:
        sd = install / "skills" / sname
        sd.mkdir(parents=True)
        (sd / "SKILL.md").write_text("---\ndescription: desc\n---\n")
    pj = tmp_path / "installed_plugins.json"
    pj.write_text(json.dumps({"version": 2, "plugins": {
        "alpha@r": [{"installPath": str(install_a), "version": "1.0"}],
        "beta@r":  [{"installPath": str(install_b), "version": "1.0"}],
    }}))
    monkeypatch.setattr(generate, "PLUGINS_JSON", pj)
    result = generate._parse_plugins()
    assert result[0]["group"] == "alpha"
    assert result[1]["group"] == "beta"

def test_parse_plugins_missing_json(tmp_path, monkeypatch):
    monkeypatch.setattr(generate, "PLUGINS_JSON", tmp_path / "missing.json")
    assert generate._parse_plugins() == []

def test_parse_plugins_skips_no_skill_md(tmp_path, monkeypatch):
    install = tmp_path / "cache" / "myplugin" / "1.0"
    (install / "skills" / "no-md").mkdir(parents=True)
    pj = tmp_path / "installed_plugins.json"
    pj.write_text(json.dumps({"version": 2, "plugins": {
        "myplugin@r": [{"installPath": str(install), "version": "1.0"}]
    }}))
    monkeypatch.setattr(generate, "PLUGINS_JSON", pj)
    assert generate._parse_plugins() == []

def test_parse_commands_builtin_first(tmp_path, monkeypatch):
    monkeypatch.setattr(generate, "PLUGINS_JSON", tmp_path / "missing.json")
    result = generate.parse_commands()
    assert result[0]["group"] == "BUILT-IN"
    assert len([r for r in result if r["group"] == "BUILT-IN"]) == 11

def test_parse_commands_unified_format(tmp_path, monkeypatch):
    pj = _make_plugins_json(tmp_path, "myplugin", [("my-skill", "Does something")])
    monkeypatch.setattr(generate, "PLUGINS_JSON", pj)
    result = generate.parse_commands()
    plugin_cmds = [r for r in result if r["group"] == "myplugin"]
    assert len(plugin_cmds) == 1
    assert plugin_cmds[0]["skill"] == "/my-skill"


# ── get_screen_size ────────────────────────────────────────────────────────────

def test_get_screen_size_darwin(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    fake = "  Resolution: 3024 x 1964 Retina\n"
    monkeypatch.setattr(generate.subprocess, "run",
        lambda *a, **kw: type("R", (), {"stdout": fake, "returncode": 0})())
    assert generate.get_screen_size() == (3024, 1964)

def test_get_screen_size_linux(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Linux")
    fake = "Screen 0: ... current 2560 x 1440, ..."
    monkeypatch.setattr(generate.subprocess, "run",
        lambda *a, **kw: type("R", (), {"stdout": fake, "returncode": 0})())
    assert generate.get_screen_size() == (2560, 1440)

def test_get_screen_size_fallback(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr(generate.subprocess, "run",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("no display")))
    w, h = generate.get_screen_size()
    assert w == 2560 and h == 1600


# ── _make_background ──────────────────────────────────────────────────────────

def test_make_gradient_bg_size():
    img = generate._make_gradient_bg(100, 60)
    assert img.size == (100, 60) and img.mode == "RGB"

def test_make_gradient_bg_top_darker():
    img = generate._make_gradient_bg(10, 100)
    assert sum(img.getpixel((5, 0))) < sum(img.getpixel((5, 99)))

def test_make_background_gradient():
    cfg = {"background": {"type": "gradient", "image_path": None}}
    img = generate._make_background(100, 60, cfg)
    assert img.size == (100, 60) and img.mode == "RGB"

def test_make_background_image_missing_falls_back(tmp_path):
    cfg = {"background": {"type": "image", "image_path": str(tmp_path / "nope.jpg")}}
    img = generate._make_background(100, 60, cfg)
    assert img.size == (100, 60) and img.mode == "RGB"

def test_make_background_image_darkens(tmp_path):
    from PIL import Image as PilImage
    src = tmp_path / "white.jpg"
    PilImage.new("RGB", (200, 200), (255, 255, 255)).save(str(src))
    cfg = {"background": {"type": "image", "image_path": str(src)}}
    img = generate._make_background(200, 200, cfg)
    assert all(v < 255 for v in img.getpixel((100, 100)))


# ── layout engine ─────────────────────────────────────────────────────────────

def _cmds(n, group="plug"):
    return [{"group": group, "skill": f"/s{i}", "description": "d"} for i in range(n)]

def test_measure_column_height_scales_with_count():
    h5  = generate._measure_column_height(_cmds(5),  1.0, False, True)
    h10 = generate._measure_column_height(_cmds(10), 1.0, False, True)
    assert h10 > h5

def test_measure_column_height_compact_shorter():
    items = _cmds(8)
    assert generate._measure_column_height(items, 1.0, True, True) < \
           generate._measure_column_height(items, 1.0, False, True)

def test_measure_column_height_nodesc_shorter():
    items = _cmds(8)
    assert generate._measure_column_height(items, 1.0, False, False) < \
           generate._measure_column_height(items, 1.0, False, True)

def test_measure_column_height_empty():
    assert generate._measure_column_height([], 1.0, False, True) == 0

def test_split_into_cols_count():
    cols = generate._split_into_cols(_cmds(20), 4)
    assert len(cols) == 4
    assert sum(len(c) for c in cols) == 20

def test_split_into_cols_roughly_equal():
    cols = generate._split_into_cols(_cmds(10), 3)
    sizes = [len(c) for c in cols]
    assert max(sizes) - min(sizes) <= 1

def test_select_tier_phase1_large_canvas():
    cmds = _cmds(11, "BUILT-IN") + _cmds(5, "plug")
    r = generate.select_tier(cmds, 3024, 1964)
    assert r["phase"] == 1
    assert r["show_builtin"] is True
    assert r["truncate_at"] is None

def test_select_tier_hides_builtin_on_overflow():
    # 300 plugin commands on a small canvas forces the algorithm past phase 2
    cmds = _cmds(11, "BUILT-IN") + _cmds(300, "plug")
    r = generate.select_tier(cmds, 1280, 800)
    assert r["show_builtin"] is False
    assert r["show_hidden_note"] is True

def test_select_tier_truncate_extreme():
    cmds = _cmds(11, "BUILT-IN") + _cmds(500, "plug")
    r = generate.select_tier(cmds, 1280, 800)
    assert r["truncate_at"] is not None
    assert r["truncate_at"] < 500

def test_select_tier_larger_canvas_not_worse():
    cmds = _cmds(11, "BUILT-IN") + _cmds(20, "plug")
    r_big   = generate.select_tier(cmds, 3024, 1964)
    r_small = generate.select_tier(cmds, 1280,  800)
    assert r_small["phase"] >= r_big["phase"]

def test_select_tier_font_scale_affects_layout():
    cmds = _cmds(11, "BUILT-IN") + _cmds(30, "plug")
    r_normal = generate.select_tier(cmds, 2560, 1600, font_scale=1.0)
    r_large  = generate.select_tier(cmds, 2560, 1600, font_scale=1.5)
    assert r_large["phase"] >= r_normal["phase"]


# ── render_wallpaper ──────────────────────────────────────────────────────────

def _default_cfg():
    return {
        "background": {"type": "gradient", "image_path": None},
        "font": {"scale": 1.0, "ui_family": None, "mono_family": None, "bold_family": None},
    }

def test_render_wallpaper_creates_rgb_png(tmp_path):
    from PIL import Image as PilImage
    out  = tmp_path / "wall.png"
    cmds = ([{"group": "BUILT-IN", "skill": "/help", "description": "Show help"}] +
            [{"group": "superpowers", "skill": "/brain", "description": "Think"}])
    generate.render_wallpaper(out, 800, 500, cmds, _default_cfg())
    assert out.exists()
    img = PilImage.open(out)
    assert img.size == (800, 500) and img.mode == "RGB"

def test_render_wallpaper_creates_output_dir(tmp_path):
    out  = tmp_path / "nested" / "dir" / "wall.png"
    cmds = [{"group": "BUILT-IN", "skill": "/help", "description": "d"}]
    generate.render_wallpaper(out, 400, 300, cmds, _default_cfg())
    assert out.exists()

def test_render_wallpaper_with_image_bg(tmp_path):
    from PIL import Image as PilImage
    bg = tmp_path / "bg.jpg"
    PilImage.new("RGB", (400, 300), (30, 30, 30)).save(str(bg))
    cfg = {"background": {"type": "image", "image_path": str(bg)},
           "font": {"scale": 1.0, "ui_family": None, "mono_family": None, "bold_family": None}}
    out = tmp_path / "wall.png"
    cmds = [{"group": "BUILT-IN", "skill": "/help", "description": "d"}]
    generate.render_wallpaper(out, 400, 300, cmds, cfg)
    assert out.exists()


# ── set_wallpaper ─────────────────────────────────────────────────────────────

def test_set_wallpaper_darwin_calls_osascript(monkeypatch, tmp_path):
    import platform
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    calls = []
    monkeypatch.setattr(generate.subprocess, "run", lambda args, **kw: calls.append(args))
    png = tmp_path / "wall.png"; png.write_bytes(b"")
    generate.set_wallpaper(png)
    assert calls[0][0] == "osascript"
    assert str(png) in calls[0][2]

def test_set_wallpaper_darwin_escapes_quotes(monkeypatch, tmp_path):
    import platform
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    calls = []
    monkeypatch.setattr(generate.subprocess, "run", lambda args, **kw: calls.append(args))
    tricky = tmp_path / 'wall"paper.png'; tricky.write_bytes(b"")
    generate.set_wallpaper(tricky)
    assert '\\"' in calls[0][2]

def test_set_wallpaper_linux_gnome(monkeypatch, tmp_path):
    import platform
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
    calls = []
    monkeypatch.setattr(generate.subprocess, "run", lambda args, **kw: calls.append(args))
    png = tmp_path / "wall.png"; png.write_bytes(b"")
    generate.set_wallpaper(png)
    assert any("gsettings" in str(c) for c in calls)

def test_set_wallpaper_linux_feh_fallback(monkeypatch, tmp_path):
    import platform
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "i3")
    calls = []
    monkeypatch.setattr(generate.subprocess, "run", lambda args, **kw: calls.append(args))
    png = tmp_path / "wall.png"; png.write_bytes(b"")
    generate.set_wallpaper(png)
    assert any("feh" in str(c) for c in calls)

def test_set_wallpaper_unsupported_platform(monkeypatch, tmp_path):
    import platform
    monkeypatch.setattr(platform, "system", lambda: "FreeBSD")
    png = tmp_path / "wall.png"; png.write_bytes(b"")
    with pytest.raises(NotImplementedError):
        generate.set_wallpaper(png)
