#!/usr/bin/env python3
"""
Claude Code slash command cheatsheet wallpaper generator.
Cross-platform, config-driven.
"""

import json
import os
import platform
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ── path constants ─────────────────────────────────────────────────────────────

SCRIPT_DIR   = Path(__file__).parent.resolve()
CONFIG_PATH  = Path.home() / ".claude" / "wallpaper" / "config.json"
OUTPUT_PATH  = Path.home() / ".agent-wallpaper" / "wallpaper.png"
PLUGINS_JSON = Path.home() / ".claude" / "plugins" / "installed_plugins.json"

# ── built-in commands ──────────────────────────────────────────────────────────

BUILTIN_COMMANDS: list[tuple[str, str]] = [
    ("/code-review",              "Review diff for bugs & quality issues"),
    ("/run",                      "Launch & test the app"),
    ("/verify",                   "Confirm a fix works in the running app"),
    ("/simplify",                 "Refactor changed code for clarity"),
    ("/security-review",          "Security audit the current diff"),
    ("/review",                   "Review a GitHub pull request"),
    ("/init",                     "Initialize CLAUDE.md for project"),
    ("/loop",                     "Run a prompt on a recurring interval"),
    ("/schedule",                 "Create scheduled cloud agents"),
    ("/update-config",            "Configure Claude Code settings"),
    ("/fewer-permission-prompts", "Scan & add tool allowlist"),
]

# ── color constants ────────────────────────────────────────────────────────────

BG_COLORS = [(13, 17, 23), (26, 26, 46), (22, 33, 62), (15, 52, 96)]

TITLE_COLOR          = (226, 232, 240)
SUBTITLE_COLOR       = (100, 116, 139)
BUILTIN_HDR_COLOR    = (148, 163, 184)
PLUGIN_HDR_COLOR     = (167, 139, 250)
CMD_NAME_COLOR       = (226, 232, 240)
PLUGIN_NAME_COLOR    = (196, 181, 253)
DESC_COLOR           = (100, 116, 139)
PLUGIN_LABEL_COLOR   = (120, 100, 190)
BUILTIN_LABEL_COLOR  = (148, 163, 184)
FOOTER_COLOR         = (80, 90, 110)

BUILTIN_CARD_FILL    = (255, 255, 255, 13)
BUILTIN_CARD_BORDER  = (255, 255, 255, 25)
PLUGIN_CARD_FILL     = (167, 139, 250, 18)
PLUGIN_CARD_BORDER   = (167, 139, 250, 50)

# ── config system ──────────────────────────────────────────────────────────────

_DEFAULTS: dict = {
    "update_mode": "auto",
    "background": {"type": "gradient", "image_path": None},
    "font": {
        "scale": 1.0,
        "ui_family": None,
        "mono_family": None,
        "bold_family": None,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base; missing keys fall back to base."""
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def load_config() -> dict:
    """Read CONFIG_PATH if present and deep-merge with defaults."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                user = json.load(f)
            return _deep_merge(_DEFAULTS, user)
        except Exception:
            pass
    return _deep_merge(_DEFAULTS, {})


# ── cross-platform font loader ─────────────────────────────────────────────────

def _platform_font_paths(mono: bool, bold: bool) -> list[str]:
    """Return ordered list of font path candidates for the current platform."""
    system = platform.system()

    if system == "Darwin":
        if bold:
            return [
                "/System/Library/Fonts/Menlo.ttc",
                "/System/Library/Fonts/Helvetica.ttc",
            ]
        if mono:
            return [
                "/System/Library/Fonts/SFNSMono.ttf",
                "/System/Library/Fonts/Menlo.ttc",
                "/System/Library/Fonts/Monaco.ttf",
            ]
        return [
            "/System/Library/Fonts/SFNS.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]

    if system == "Linux":
        if bold:
            return [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
            ]
        if mono:
            return [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            ]
        return [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]

    # Windows (and unknown platforms fall here)
    if bold or mono:
        return [
            "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/cour.ttf",
        ]
    return [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]


def _extract_description(skill_md: Path) -> str:
    """Extract description: value from YAML frontmatter; truncate at 55 chars."""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            return ""
        found_desc = None
        for line in lines[1:]:
            if line.strip() == "---":
                if found_desc is not None:
                    return found_desc
                return ""
            if line.startswith("description:") and found_desc is None:
                raw = line[len("description:"):].strip().strip('"\'')
                for sep in (".", "—", " -"):
                    idx = raw.find(sep)
                    if 0 < idx < 55:
                        found_desc = raw[:idx].strip()
                        break
                else:
                    if len(raw) > 55:
                        clipped = raw[:55].rsplit(" ", 1)[0].rstrip(",.;:")
                        found_desc = clipped + "…"
                    else:
                        found_desc = raw
        # no closing --- found
    except Exception:
        pass
    return ""


def _parse_plugins() -> list[dict]:
    """Parse PLUGINS_JSON; return list of {group, skill, description} dicts."""
    if not PLUGINS_JSON.exists():
        return []
    with open(PLUGINS_JSON) as f:
        data = json.load(f)

    results = []
    for plugin_key, installs in data.get("plugins", {}).items():
        if not installs:
            continue
        install_path = Path(installs[0]["installPath"])
        plugin_name  = plugin_key.split("@")[0]
        skills_dir   = install_path / "skills"
        if not skills_dir.exists():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            results.append({
                "group":       plugin_name,
                "skill":       f"/{skill_dir.name}",
                "description": _extract_description(skill_md),
            })

    return sorted(results, key=lambda x: (x["group"], x["skill"]))


def parse_commands() -> list[dict]:
    """Return unified command list: BUILT-IN group first, then plugins."""
    builtin = [
        {"group": "BUILT-IN", "skill": cmd, "description": desc}
        for cmd, desc in BUILTIN_COMMANDS
    ]
    return builtin + _parse_plugins()


def load_font(
    size: int,
    mono: bool = False,
    bold: bool = False,
    cfg: dict | None = None,
) -> ImageFont.FreeTypeFont:
    """Load the best available font for the given parameters."""
    candidates: list[str] = []

    if cfg is not None:
        font_cfg = cfg.get("font", {})
        if bold and font_cfg.get("bold_family"):
            candidates.append(font_cfg["bold_family"])
        elif mono and font_cfg.get("mono_family"):
            candidates.append(font_cfg["mono_family"])
        elif (not mono and not bold) and font_cfg.get("ui_family"):
            candidates.append(font_cfg["ui_family"])

    candidates.extend(_platform_font_paths(mono, bold))

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            pass

    return ImageFont.load_default()


# ── screen size detection ──────────────────────────────────────────────────────

def get_screen_size() -> tuple[int, int]:
    """Detect the primary screen resolution; fall back to (2560, 1600)."""
    system = platform.system()

    if system == "Darwin":
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True, text=True, timeout=5,
            )
            import re
            m = re.search(r"Resolution: (\d+) x (\d+)", result.stdout)
            if m:
                return int(m.group(1)), int(m.group(2))
        except Exception:
            pass

    elif system == "Linux":
        try:
            result = subprocess.run(
                ["xrandr", "--current"],
                capture_output=True, text=True, timeout=5,
            )
            import re
            m = re.search(r"current (\d+) x (\d+)", result.stdout)
            if m:
                return int(m.group(1)), int(m.group(2))
        except Exception:
            pass

    elif system == "Windows":
        try:
            import ctypes
            u = ctypes.windll.user32
            return u.GetSystemMetrics(0), u.GetSystemMetrics(1)
        except Exception:
            pass

    return 2560, 1600


# ── background builders ────────────────────────────────────────────────────────

def _make_gradient_bg(w: int, h: int) -> Image.Image:
    """Vertical 4-stop gradient using BG_COLORS."""
    strip = Image.new("RGB", (1, h))
    px = strip.load()
    n = len(BG_COLORS) - 1
    for y in range(h):
        t = y / max(h - 1, 1) * n
        i = min(int(t), n - 1)
        lt = t - i
        c1, c2 = BG_COLORS[i], BG_COLORS[i + 1]
        px[0, y] = tuple(int(a + (b - a) * lt) for a, b in zip(c1, c2))
    return strip.resize((w, h), Image.NEAREST)


def _make_background(w: int, h: int, cfg: dict) -> Image.Image:
    """Return RGB background image per config; fall back to gradient on error."""
    bg_cfg = cfg.get("background", {})
    if bg_cfg.get("type") == "image" and bg_cfg.get("image_path") is not None:
        try:
            src = Image.open(bg_cfg["image_path"]).convert("RGB")
            src_w, src_h = src.size
            scale = max(w / src_w, h / src_h)
            new_w = int(src_w * scale)
            new_h = int(src_h * scale)
            src = src.resize((new_w, new_h), Image.LANCZOS)
            left = (new_w - w) // 2
            top = (new_h - h) // 2
            src = src.crop((left, top, left + w, top + h))
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 160))
            base = src.convert("RGBA")
            base.alpha_composite(overlay)
            return base.convert("RGB")
        except Exception:
            pass
    return _make_gradient_bg(w, h)


# ── drawing primitives ─────────────────────────────────────────────────────────

def _draw_rounded_card(
    canvas: Image.Image,
    x: int, y: int, w: int, h: int,
    fill: tuple, outline: tuple, radius: int = 10,
) -> None:
    """Composite a semi-transparent rounded rect onto an RGBA canvas."""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x, y, x + w, y + h], radius=radius,
                        fill=fill, outline=outline, width=1)
    canvas.alpha_composite(layer)


# ── layout engine ──────────────────────────────────────────────────────────────

def _card_height(compact: bool, show_desc: bool, scale: float) -> int:
    if compact:
        base = 42 if show_desc else 30
    else:
        base = 58 if show_desc else 38
    return int(base * scale)


def _card_gap(compact: bool, scale: float) -> int:
    return int((5 if compact else 8) * scale)


def _measure_column_height(items: list[dict], scale: float, compact: bool, show_desc: bool) -> int:
    if not items:
        return 0
    ch = _card_height(compact, show_desc, scale)
    cg = _card_gap(compact, scale)
    label_h = int(28 * scale)
    label_gap = int(6 * scale)
    inter_group_h = int(12 * scale)

    groups: dict[str, list[dict]] = {}
    group_order: list[str] = []
    for item in items:
        g = item["group"]
        if g not in groups:
            groups[g] = []
            group_order.append(g)
        groups[g].append(item)

    total = 0
    for idx, g in enumerate(group_order):
        if idx > 0:
            total += inter_group_h
        total += label_h + label_gap
        n = len(groups[g])
        total += n * ch + max(0, n - 1) * cg

    return total


def _split_into_cols(commands: list[dict], n_cols: int) -> list[list[dict]]:
    n = len(commands)
    q, r = divmod(n, max(1, n_cols))
    result = []
    start = 0
    for i in range(n_cols):
        size = q + (1 if i < r else 0)
        result.append(commands[start:start + size])
        start += size
    return result


_PHASES = [
    (True,  True,  False),   # phase 1: show_desc, show_builtin, show_hidden_note
    (False, True,  False),   # phase 2
    (True,  False, True),    # phase 3
    (False, False, True),    # phase 4
]
_MIN_COLS = 2
_MAX_COLS = 6


def select_tier(all_commands: list[dict], canvas_w: int, canvas_h: int, font_scale: float = 1.0) -> dict:
    scale    = min(canvas_w / 3024, canvas_h / 1964) * font_scale
    pad_v    = int(72 * scale) * 2
    title_h  = int(88 * scale)
    footer_h = int(36 * scale)
    usable_h = canvas_h - pad_v - title_h

    for phase_idx, (show_desc, show_builtin, show_hidden_note) in enumerate(_PHASES):
        commands = (all_commands if show_builtin
                    else [c for c in all_commands if c["group"] != "BUILT-IN"])
        compact  = not show_desc
        extra    = footer_h if show_hidden_note else 0

        for n_cols in range(_MIN_COLS, _MAX_COLS + 1):
            chunks = _split_into_cols(commands, n_cols)
            col_h  = max(
                (_measure_column_height(ch, scale, compact, show_desc) for ch in chunks),
                default=0,
            )
            if col_h + extra <= usable_h:
                return {
                    "phase": phase_idx + 1,
                    "n_cols": n_cols,
                    "show_desc": show_desc,
                    "show_builtin": show_builtin,
                    "show_hidden_note": show_hidden_note,
                    "compact": compact,
                    "truncate_at": None,
                }

    # Truncate phase: phase 4 + MAX_COLS, shrink non-builtin list
    show_desc, show_builtin, show_hidden_note = _PHASES[3]
    commands = [c for c in all_commands if c["group"] != "BUILT-IN"]
    for max_count in range(len(commands) - 1, 0, -1):
        truncated = commands[:max_count]
        chunks    = _split_into_cols(truncated, _MAX_COLS)
        col_h     = max(
            (_measure_column_height(ch, scale, True, False) for ch in chunks),
            default=0,
        )
        if col_h + footer_h <= usable_h:
            return {
                "phase": 5, "n_cols": _MAX_COLS,
                "show_desc": False, "show_builtin": False,
                "show_hidden_note": True, "compact": True,
                "truncate_at": max_count,
            }

    return {  # absolute fallback
        "phase": 5, "n_cols": _MIN_COLS, "show_desc": False,
        "show_builtin": False, "show_hidden_note": True,
        "compact": True, "truncate_at": 1,
    }


# ── renderer functions ─────────────────────────────────────────────────────────

def _render_command_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    x: int, y: int, col_w: int, ch: int,
    radius: int, inner_x: int, inner_y: int,
    cmd_name: str, cmd_desc: str,
    is_plugin: bool,
    f_cmd: ImageFont.FreeTypeFont,
    f_desc: ImageFont.FreeTypeFont,
) -> None:
    fill   = PLUGIN_CARD_FILL   if is_plugin else BUILTIN_CARD_FILL
    border = PLUGIN_CARD_BORDER if is_plugin else BUILTIN_CARD_BORDER
    name_c = PLUGIN_NAME_COLOR  if is_plugin else CMD_NAME_COLOR

    _draw_rounded_card(canvas, x, y, col_w, ch, fill, border, radius)
    draw.text((x + inner_x, y + inner_y), cmd_name, font=f_cmd, fill=name_c)
    if cmd_desc:
        desc_y = y + inner_y + f_cmd.size + max(2, f_cmd.size // 5)
        draw.text((x + inner_x, desc_y), cmd_desc, font=f_desc, fill=DESC_COLOR)


def _render_column(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    x: int, y: int, col_w: int,
    ch: int, cg: int, radius: int, inner_x: int, inner_y: int,
    items: list[dict],
    show_desc: bool,
    f_cmd: ImageFont.FreeTypeFont,
    f_desc: ImageFont.FreeTypeFont,
    f_group_label: ImageFont.FreeTypeFont,
    scale: float,
) -> None:
    label_h   = int(28 * scale)
    label_gap = int(6  * scale)
    inter_gap = int(12 * scale)

    groups: dict[str, list] = {}
    for item in items:
        groups.setdefault(item["group"], []).append(item)

    first_group = True
    for group_name, group_items in groups.items():
        if not first_group:
            y += inter_gap
        first_group = False

        is_plugin   = group_name != "BUILT-IN"
        label_color = PLUGIN_LABEL_COLOR if is_plugin else BUILTIN_LABEL_COLOR
        draw.text((x, y), group_name, font=f_group_label, fill=label_color)
        y += label_h + label_gap

        for item in group_items:
            _render_command_card(
                canvas, draw, x, y, col_w, ch, radius, inner_x, inner_y,
                item["skill"],
                item["description"] if show_desc else "",
                is_plugin=is_plugin,
                f_cmd=f_cmd, f_desc=f_desc,
            )
            y += ch + cg


def render_wallpaper(
    output_path: Path,
    canvas_w: int,
    canvas_h: int,
    all_commands: list[dict],
    cfg: dict,
) -> None:
    font_scale = cfg.get("font", {}).get("scale", 1.0)
    scale      = min(canvas_w / 3024, canvas_h / 1964) * font_scale
    tier_cfg   = select_tier(all_commands, canvas_w, canvas_h, font_scale)

    canvas = _make_background(canvas_w, canvas_h, cfg).convert("RGBA")

    sz_title  = max(8,  int(28 * scale))
    sz_cmd    = max(7,  int(20 * scale * (0.85 if tier_cfg["compact"] else 1.0)))
    sz_desc   = max(6,  int(16 * scale * (0.85 if tier_cfg["compact"] else 1.0)))
    sz_label  = max(6,  sz_cmd + max(1, int(3 * scale)))
    sz_footer = max(6,  int(14 * scale))
    radius    = max(4,  int(10 * scale))

    f_title       = load_font(sz_title,  cfg=cfg)
    f_cmd         = load_font(sz_cmd,    mono=True,  cfg=cfg)
    f_desc        = load_font(sz_desc,   cfg=cfg)
    f_group_label = load_font(sz_label,  bold=True,  cfg=cfg)
    f_footer      = load_font(sz_footer, cfg=cfg)

    draw    = ImageDraw.Draw(canvas)
    pad_x   = int(60 * scale)
    pad_y   = int(72 * scale)
    col_gap = int(40 * scale)
    ch      = _card_height(tier_cfg["compact"], tier_cfg["show_desc"], scale)
    cg      = _card_gap(tier_cfg["compact"], scale)
    inner_x = int(12 * scale)
    inner_y = int(10 * scale)

    # title row
    logo_size = int(42 * scale)
    logo_r    = int(10 * scale)
    lx, ly    = pad_x, pad_y

    logo_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(logo_layer)
    ld.rounded_rectangle([lx, ly, lx + logo_size, ly + logo_size],
                         radius=logo_r, fill=(120, 80, 220, 220))
    canvas.alpha_composite(logo_layer)
    draw.text((lx + int(logo_size * 0.28), ly + int(logo_size * 0.22)),
              "C", font=load_font(int(logo_size * 0.55), cfg=cfg), fill=(255, 255, 255))

    title_x = lx + logo_size + int(14 * scale)
    title_y = ly + int((logo_size - sz_title) / 2)
    draw.text((title_x, title_y), "CLAUDE COMMANDS", font=f_title, fill=TITLE_COLOR)

    tag = "CHEATSHEET · AUTO-UPDATED"
    tag_bbox = draw.textbbox((0, 0), tag, font=f_footer)
    tag_w    = tag_bbox[2] - tag_bbox[0]
    draw.text((canvas_w - pad_x - tag_w,
               title_y + int((sz_title - sz_footer) / 2)),
              tag, font=f_footer, fill=FOOTER_COLOR)

    content_top = ly + logo_size + int(28 * scale)

    # which commands to show
    commands_to_show = (all_commands if tier_cfg["show_builtin"]
                        else [c for c in all_commands if c["group"] != "BUILT-IN"])
    if tier_cfg["truncate_at"] is not None:
        non_builtin = [c for c in commands_to_show if c["group"] != "BUILT-IN"]
        commands_to_show = non_builtin[:tier_cfg["truncate_at"]]

    n_cols     = tier_cfg["n_cols"]
    col_w      = (canvas_w - 2 * pad_x - (n_cols - 1) * col_gap) // n_cols
    col_starts = [pad_x + i * (col_w + col_gap) for i in range(n_cols)]
    chunks     = _split_into_cols(commands_to_show, n_cols)

    for i, chunk in enumerate(chunks):
        _render_column(
            canvas, draw, col_starts[i], content_top, col_w,
            ch, cg, radius, inner_x, inner_y,
            chunk, tier_cfg["show_desc"],
            f_cmd, f_desc, f_group_label, scale,
        )

    # footer note (phase 3+)
    if tier_cfg["show_hidden_note"]:
        note      = "Built-in commands hidden — run /help to see them"
        note_bbox = draw.textbbox((0, 0), note, font=f_footer)
        note_w    = note_bbox[2] - note_bbox[0]
        note_y    = canvas_h - int(48 * scale)
        draw.text(((canvas_w - note_w) // 2, note_y),
                  note, font=f_footer, fill=FOOTER_COLOR)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(str(output_path))


# ── wallpaper setter ───────────────────────────────────────────────────────────

def _set_wallpaper_linux(path: Path) -> None:
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    uri = f"file://{path}"
    if any(d in desktop for d in ("gnome", "unity", "budgie", "pop")):
        subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", uri],
            check=True,
        )
        subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", uri],
            check=False,
        )
    elif "xfce" in desktop:
        subprocess.run(
            ["xfconf-query", "-c", "xfce4-desktop",
             "-p", "/backdrop/screen0/monitorVGA-1/workspace0/last-image",
             "-s", str(path)],
            check=True,
        )
    elif "kde" in desktop or "plasma" in desktop:
        script = (
            "var d=desktops();"
            "for(var i=0;i<d.length;i++){"
            "d[i].wallpaperPlugin='org.kde.image';"
            "d[i].currentConfigGroup=['Wallpaper','org.kde.image','General'];"
            f"d[i].writeConfig('Image','file://{path}');"
            "}"
        )
        subprocess.run(
            ["qdbus", "org.kde.plasmashell", "/PlasmaShell",
             "org.kde.PlasmaShell.evaluateScript", script],
            check=True,
        )
    else:
        subprocess.run(["feh", "--bg-fill", str(path)], check=True)


def set_wallpaper(path: Path) -> None:
    import platform
    system = platform.system()
    if system == "Darwin":
        escaped = str(path).replace('\\', '\\\\').replace('"', '\\"')
        script = (
            f'tell application "System Events" to set picture of every desktop '
            f'to POSIX file "{escaped}"'
        )
        subprocess.run(["osascript", "-e", script], check=True)
    elif system == "Linux":
        _set_wallpaper_linux(path)
    elif system == "Windows":
        import ctypes
        ctypes.windll.user32.SystemParametersInfoW(20, 0, str(path.resolve()), 3)
    else:
        raise NotImplementedError(f"Unsupported platform: {system}")


def main() -> None:
    cfg          = load_config()
    w, h         = get_screen_size()
    all_commands = parse_commands()
    render_wallpaper(OUTPUT_PATH, w, h, all_commands, cfg)
    try:
        set_wallpaper(OUTPUT_PATH)
    except (subprocess.CalledProcessError, NotImplementedError, Exception) as e:
        print(f"Warning: could not set wallpaper: {e}")
        print(f"PNG saved to: {OUTPUT_PATH}")
        return
    tier = select_tier(all_commands, w, h, cfg.get("font", {}).get("scale", 1.0))
    print(f"Wallpaper updated — phase={tier['phase']} commands={len(all_commands)}")


if __name__ == "__main__":
    main()
