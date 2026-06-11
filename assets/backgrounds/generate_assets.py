#!/usr/bin/env python3
"""
Generate preset background images for the wallpaper-cheatsheet plugin.

Generates three 2560×1600px JPEG backgrounds:
- dark-mesh.jpg: dark navy with subtle grid pattern
- deep-space.jpg: dark starfield with scattered bright dots
- carbon.jpg: dark diagonal stripe pattern (carbon fiber style)
"""

import random
from pathlib import Path
from PIL import Image, ImageDraw


def hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple:
    """Convert hex color string to RGBA tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (alpha,)


def create_dark_mesh() -> Image.Image:
    """
    Create dark mesh background with subtle grid pattern.

    Base: very dark navy #0a0e1a
    Grid: horizontal and vertical lines (~80px spacing, 1px width)
    Lines: very faint blue-purple rgba(100, 120, 200, 40)
    Gradient: subtle radial overlay from center (#131929) to edges (#060810)
    """
    width, height = 2560, 1600

    # Create base image with dark navy background
    img = Image.new('RGB', (width, height), hex_to_rgba('#0a0e1a')[:3])
    draw = ImageDraw.Draw(img, 'RGBA')

    # Draw grid pattern
    grid_spacing = 80
    line_color = (100, 120, 200, 40)  # very faint blue-purple

    # Vertical lines
    for x in range(0, width, grid_spacing):
        draw.line([(x, 0), (x, height)], fill=line_color, width=1)

    # Horizontal lines
    for y in range(0, height, grid_spacing):
        draw.line([(0, y), (width, y)], fill=line_color, width=1)

    # Apply radial gradient overlay
    # Create a gradient image
    gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    gradient_draw = ImageDraw.Draw(gradient)

    center_x, center_y = width // 2, height // 2
    max_dist = ((center_x ** 2) + (center_y ** 2)) ** 0.5

    # Draw concentric circles for radial gradient
    center_color = hex_to_rgba('#131929')
    edge_color = hex_to_rgba('#060810')

    for radius in range(int(max_dist), 0, -1):
        ratio = (max_dist - radius) / max_dist
        r = int(center_color[0] * (1 - ratio) + edge_color[0] * ratio)
        g = int(center_color[1] * (1 - ratio) + edge_color[1] * ratio)
        b = int(center_color[2] * (1 - ratio) + edge_color[2] * ratio)

        # Subtle opacity for gradient
        a = int(30 * (1 - ratio))
        gradient_draw.ellipse(
            [(center_x - radius, center_y - radius),
             (center_x + radius, center_y + radius)],
            fill=(r, g, b, a)
        )

    # Composite gradient onto main image
    img = Image.alpha_composite(img.convert('RGBA'), gradient)

    return img.convert('RGB')


def create_deep_space() -> Image.Image:
    """
    Create dark starfield background.

    Base: near-black #050710
    Stars: ~800 tiny circles (r=1-2px, white/light-blue, opacity 30-100%)
    Bright stars: ~20 larger circles (r=2-4px) with soft glow effect
    Optional: faint diagonal nebula smear
    """
    width, height = 2560, 1600

    # Create base image with near-black background
    img = Image.new('RGB', (width, height), hex_to_rgba('#050710')[:3])
    draw = ImageDraw.Draw(img, 'RGBA')

    random.seed(42)  # For reproducibility

    # Draw regular stars (~800)
    for _ in range(800):
        x = random.randint(0, width)
        y = random.randint(0, height)
        radius = random.randint(1, 2)

        # White or light blue colors
        if random.random() < 0.7:
            color = (255, 255, 255, random.randint(80, 255))
        else:
            color = (180, 220, 255, random.randint(80, 255))

        draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            fill=color
        )

    # Draw bright stars with glow (~20)
    for _ in range(20):
        x = random.randint(0, width)
        y = random.randint(0, height)

        # Draw glow with decreasing opacity
        for glow_radius in range(10, 0, -1):
            opacity = int(30 * (1 - glow_radius / 10))
            glow_draw = ImageDraw.Draw(img, 'RGBA')
            glow_draw.ellipse(
                [(x - glow_radius, y - glow_radius),
                 (x + glow_radius, y + glow_radius)],
                fill=(200, 230, 255, opacity)
            )

        # Draw bright center
        draw.ellipse(
            [(x - 3, y - 3), (x + 3, y + 3)],
            fill=(255, 255, 255, 255)
        )

    # Add faint diagonal nebula smear
    nebula_draw = ImageDraw.Draw(img, 'RGBA')
    nebula_y_start = height // 4
    nebula_y_end = height - height // 4

    # Draw a wide gradient band diagonally
    for i in range(0, width + height, 5):
        x1 = i
        y1 = nebula_y_start
        x2 = i + height
        y2 = nebula_y_end

        opacity = int(15 * random.random())
        nebula_draw.line(
            [(x1, y1), (x2, y2)],
            fill=(120, 100, 200, opacity),
            width=100
        )

    return img.convert('RGB')


def create_carbon() -> Image.Image:
    """
    Create dark diagonal stripe pattern (carbon fiber style).

    Base: dark charcoal #111318
    Stripes: diagonal at 45°, alternating between #0d1015 and #181c24, width ~12px
    Grid overlay: very faint thin lines every 24px for carbon weave look
    Brightness: 15-20% (very dark)
    """
    width, height = 2560, 1600

    # Create base image with dark charcoal background
    img = Image.new('RGB', (width, height), hex_to_rgba('#111318')[:3])
    draw = ImageDraw.Draw(img, 'RGBA')

    # Draw diagonal stripes at 45°
    stripe_width = 12
    color1 = hex_to_rgba('#0d1015')[:3]
    color2 = hex_to_rgba('#181c24')[:3]

    # Iterate diagonally across the image
    diagonal_dist = width + height
    for offset in range(0, diagonal_dist, stripe_width * 2):
        # Determine which color to use
        stripe_index = (offset // stripe_width) % 2
        color = color1 if stripe_index == 0 else color2

        # Draw diagonal stripe by drawing rectangles along 45° lines
        for i in range(stripe_width):
            x_start = offset + i
            for y in range(height):
                # Calculate corresponding x for the 45° diagonal
                x = x_start - y
                if 0 <= x < width:
                    img.putpixel((x, y), color)

    # Add subtle grid overlay for carbon weave effect
    grid_spacing = 24
    grid_color = (60, 65, 75, 25)  # very faint, thin lines

    grid_draw = ImageDraw.Draw(img, 'RGBA')

    # Vertical lines
    for x in range(0, width, grid_spacing):
        grid_draw.line([(x, 0), (x, height)], fill=grid_color, width=1)

    # Horizontal lines
    for y in range(0, height, grid_spacing):
        grid_draw.line([(0, y), (width, y)], fill=grid_color, width=1)

    return img.convert('RGB')


def save_image(img: Image.Image, filename: str, output_dir: Path) -> None:
    """Save image as JPEG with quality >= 85."""
    output_path = output_dir / filename
    img.save(output_path, 'JPEG', quality=90)
    file_size_kb = output_path.stat().st_size / 1024
    print(f"✓ {filename} ({file_size_kb:.1f} KB)")


def main():
    """Generate all three background images."""
    script_dir = Path(__file__).parent

    print("Generating background images (2560×1600px)...")
    print()

    # Generate dark-mesh
    print("Creating dark-mesh.jpg...")
    img = create_dark_mesh()
    save_image(img, 'dark-mesh.jpg', script_dir)

    # Generate deep-space
    print("Creating deep-space.jpg...")
    img = create_deep_space()
    save_image(img, 'deep-space.jpg', script_dir)

    # Generate carbon
    print("Creating carbon.jpg...")
    img = create_carbon()
    save_image(img, 'carbon.jpg', script_dir)

    print()
    print("Done! All backgrounds generated successfully.")


if __name__ == '__main__':
    main()
