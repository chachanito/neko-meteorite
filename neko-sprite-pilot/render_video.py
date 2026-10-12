"""Renderizador directo de la escena Neko a video vertical MP4."""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


WIDTH, HEIGHT = 360, 640
FRAME_ORDER = [0, 1, 2, 3, 4, 5, 6, 7, 6, 5, 4, 3, 2, 1]


def cover(image: Image.Image, width: int, height: int) -> Image.Image:
    scale = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def prepare_assets(root: Path):
    background = Image.open(root / "assets/night-valley-background.png").convert("RGB")
    background = cover(background, WIDTH + 8, HEIGHT + 12)

    sheet = Image.open(root / "assets/neko-sprite-sheet.png").convert("RGBA")
    cell_w, cell_h = sheet.width // 4, sheet.height // 2
    cats = []
    for frame in range(8):
        col, row = frame % 4, frame // 4
        cell = sheet.crop((col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h))
        cats.append(cell.resize((108, 144), Image.Resampling.LANCZOS))

    shade = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    shade_pixels = shade.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            edge = max(abs(x - WIDTH / 2) / (WIDTH / 2), abs(y - HEIGHT / 2) / (HEIGHT / 2))
            alpha = int(max(0, edge - .66) ** 2 * 145)
            shade_pixels[x, y] = (1, 2, 14, min(54, alpha))
    return background, cats, shade


def seeded_scene():
    rng = random.Random(2471)
    stars = [(rng.randrange(8, WIDTH - 8), rng.randrange(8, 388), rng.uniform(.5, 1.5), rng.random() * math.tau) for _ in range(58)]
    grass = [(rng.randrange(WIDTH), rng.randrange(493, 638), rng.randrange(5, 16), rng.random() * math.tau, rng.random()) for _ in range(82)]
    fireflies = [(rng.randrange(25, WIDTH - 25), rng.randrange(405, 576), rng.random() * math.tau, rng.uniform(.35, .75)) for _ in range(13)]
    flowers = [(rng.randrange(18, WIDTH - 18), rng.randrange(520, 625), rng.randrange(5, 10), rng.random() * math.tau) for _ in range(14)]
    return stars, grass, fireflies, flowers


def add_glow(frame: Image.Image, x: float, y: float, color: tuple[int, int, int], alpha: int, radius: int = 6):
    glow = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(radius / 2))
    frame.alpha_composite(glow)


def shooting_star(layer: Image.Image, t: float, offset: float, start: tuple[int, int], travel: tuple[int, int]):
    cycle = (t + offset) % 7.2
    if cycle > 1.35:
        return
    p = cycle / 1.35
    alpha = int(math.sin(p * math.pi) * 220)
    x, y = start[0] + travel[0] * p, start[1] + travel[1] * p
    tail_x, tail_y = x - travel[0] * .34, y - travel[1] * .34
    draw = ImageDraw.Draw(layer, "RGBA")
    for step in range(8):
        q = step / 8
        x1 = tail_x + (x - tail_x) * q
        y1 = tail_y + (y - tail_y) * q
        x2 = tail_x + (x - tail_x) * (q + 1 / 8)
        y2 = tail_y + (y - tail_y) * (q + 1 / 8)
        draw.line((x1, y1, x2, y2), fill=(210, 213, 255, int(alpha * q)), width=1)
    draw.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=(255, 255, 255, alpha))


def render(root: Path, output: Path, duration: int, fps: int):
    background, cats, shade = prepare_assets(root)
    stars, grass, fireflies, flowers = seeded_scene()
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio.get_writer(
        output,
        fps=fps,
        codec="libx264",
        bitrate="2500k",
        pixelformat="yuv420p",
        macro_block_size=1,
        output_params=["-vf", "scale=720:1280:flags=lanczos", "-movflags", "+faststart"],
    )

    try:
        for number in range(duration * fps):
            t = number / fps
            drift_x = round(4 + math.sin(t * math.tau / 24) * 2)
            drift_y = round(6 + math.cos(t * math.tau / 30) * 2)
            frame = background.crop((drift_x, drift_y, drift_x + WIDTH, drift_y + HEIGHT)).convert("RGBA")
            layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            draw = ImageDraw.Draw(layer, "RGBA")

            for x, y, radius, phase in stars:
                pulse = .20 + (.5 + .5 * math.sin(t * 1.25 + phase)) * .55
                a = int(150 * pulse)
                draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(225, 228, 255, a))

            for x, y, length, phase, depth in grass:
                sway = math.sin(t * .62 + phase) * (1.2 + depth * 2.1)
                color = (45, 65, 113, int(58 + depth * 62))
                draw.line((x, y, x + sway * .28, y - length * .55, x + sway, y - length), fill=color, width=1)

            for x, y, length, phase in flowers:
                sway = math.sin(t * .55 + phase) * 1.8
                draw.line((x, y, x + sway, y - length), fill=(44, 65, 116, 92), width=1)
                fx, fy = x + sway, y - length
                draw.ellipse((fx - 1.5, fy - 1.5, fx + 1.5, fy + 1.5), fill=(171, 145, 217, 110))

            for x, y, phase, speed in fireflies:
                fx = x + math.sin(t * speed + phase) * 4
                fy = y + math.cos(t * speed * .76 + phase) * 3
                strength = max(0, math.sin(t * 1.1 + phase))
                if strength > .18:
                    add_glow(layer, fx, fy, (255, 219, 135), int(55 * strength), 5)
                    draw.ellipse((fx - .7, fy - .7, fx + .7, fy + .7), fill=(255, 231, 164, int(180 * strength)))

            shooting_star(layer, t, 0, (15, 60), (145, 58))
            shooting_star(layer, t, 2.4, (222, 112), (112, 44))
            shooting_star(layer, t, 4.8, (344, 45), (-126, 50))
            frame.alpha_composite(layer)

            shadow = Image.new("RGBA", frame.size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow, "RGBA")
            shadow_width = 82 + math.sin(t * math.tau / 4.48) * 4
            shadow_draw.ellipse((180 - shadow_width / 2, 543, 180 + shadow_width / 2, 558), fill=(2, 4, 18, 90))
            shadow = shadow.filter(ImageFilter.GaussianBlur(5))
            frame.alpha_composite(shadow)

            sequence = int(t / .32) % len(FRAME_ORDER)
            cat = cats[FRAME_ORDER[sequence]]
            bob = round(math.sin(t * math.tau / 4.48))
            frame.alpha_composite(cat, (126, 413 + bob))
            frame.alpha_composite(shade)
            writer.append_data(np.asarray(frame.convert("RGB")))

            if number % (fps * 10) == 0:
                print(f"Renderizados {number // fps:>3}/{duration} segundos", flush=True)
    finally:
        writer.close()
    print(f"Video terminado: {output.resolve()}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=120)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--output", type=Path, default=Path("neko-sprite-pilot/exports/neko-noche-2min.mp4"))
    args = parser.parse_args()
    render(Path(__file__).parent, args.output, args.duration, args.fps)


if __name__ == "__main__":
    main()
