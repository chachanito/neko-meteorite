"""Genera una colección de videos verticales animados desde los 20 artes del proyecto."""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


WIDTH, HEIGHT = 360, 640
SCENES = [
    ("fox-meteor-valley.png", "01-zorro-meteoros", "meteors"),
    ("03-rabbit-moon.png", "02-conejo-luna", "petals"),
    ("04-panda-fireflies.png", "03-panda-luciernagas", "fireflies"),
    ("05-owl-aurora.png", "04-buho-aurora", "aurora"),
    ("06-raccoon-city.png", "05-mapache-ciudad", "rain"),
    ("07-deer-blossoms.png", "06-venado-cerezos", "petals"),
    ("08-penguin-aurora.png", "07-pinguino-hielo", "snow"),
    ("09-capybara-springs.png", "08-capibara-termal", "steam"),
    ("10-corgi-sunflowers.png", "09-corgi-girasoles", "fireflies"),
    ("11-red-panda-lanterns.png", "10-panda-rojo-faroles", "lanterns"),
    ("12-koala-blue-moon.png", "11-koala-luna-azul", "leaves"),
    ("13-elephant-planets.png", "12-elefante-planetas", "cosmos"),
    ("14-otter-ocean.png", "13-nutria-oceano", "waves"),
    ("15-hedgehog-mushrooms.png", "14-erizo-hongos", "spores"),
    ("16-polar-bear-cabin.png", "15-oso-polar-cabana", "snow"),
    ("17-frog-lotus.png", "16-rana-loto", "ripples"),
    ("18-wolf-storm.png", "17-lobo-tormenta", "storm"),
    ("19-astronaut-cat.png", "18-gato-astronauta", "cosmos"),
    ("20-duck-terraces.png", "19-pato-terrazas", "lanterns"),
    ("21-persian-cat-lake.png", "20-gato-persa-lago", "willow"),
]


def cover(image: Image.Image, width: int, height: int) -> Image.Image:
    scale = max(width / image.width, height / image.height)
    size = (round(image.width * scale), round(image.height * scale))
    resized = image.resize(size, Image.Resampling.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def vignette() -> Image.Image:
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    pixels = layer.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            edge = max(abs(x - WIDTH / 2) / (WIDTH / 2), abs(y - HEIGHT / 2) / (HEIGHT / 2))
            alpha = min(48, int(max(0, edge - .68) ** 2 * 150))
            pixels[x, y] = (1, 2, 15, alpha)
    return layer


def particles(seed: int, count: int = 76):
    rng = random.Random(1200 + seed * 97)
    return [(rng.random(), rng.random(), rng.random(), rng.random() * math.tau) for _ in range(count)]


def character_breathe(frame: Image.Image, t: float, seed: int) -> None:
    # A feathered local transformation keeps the landscape stable while the character breathes.
    centers = [(180, 510), (180, 500), (182, 493), (180, 486), (183, 500)]
    cx, cy = centers[seed % len(centers)]
    box = (cx - 58, cy - 92, cx + 58, cy + 78)
    patch = frame.crop(box)
    stretch = 1 + math.sin(t * math.tau / (3.8 + seed % 4 * .25)) * .006
    moved = patch.resize((patch.width, max(1, round(patch.height * stretch))), Image.Resampling.BICUBIC)
    canvas = Image.new("RGBA", patch.size, (0, 0, 0, 0))
    y = patch.height - moved.height
    canvas.alpha_composite(moved, (round(math.sin(t * .7 + seed) * .7), y))
    mask = Image.new("L", patch.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((8, 8, patch.width - 8, patch.height - 8), radius=24, fill=195)
    mask = mask.filter(ImageFilter.GaussianBlur(10))
    frame.paste(canvas, box, mask)


def glow(draw: ImageDraw.ImageDraw, x: float, y: float, rgb: tuple[int, int, int], strength: float, radius: float = 5):
    for step in range(4, 0, -1):
        r = radius * step / 4
        a = int(18 * strength * (5 - step))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(*rgb, a))
    draw.ellipse((x - .8, y - .8, x + .8, y + .8), fill=(*rgb, int(190 * strength)))


def draw_meteors(draw: ImageDraw.ImageDraw, t: float, seed: int):
    for index, offset in enumerate((0, 2.3, 4.9)):
        cycle = (t + offset + seed * .4) % 8.3
        if cycle > 1.25:
            continue
        p = cycle / 1.25
        alpha = int(math.sin(p * math.pi) * 220)
        start_x = (28 + index * 119 + seed * 13) % 330
        x, y = start_x + 95 * p, 55 + index * 72 + 42 * p
        draw.line((x - 38, y - 18, x, y), fill=(205, 210, 255, alpha), width=1)
        draw.ellipse((x - 1.4, y - 1.4, x + 1.4, y + 1.4), fill=(255, 255, 255, alpha))


def draw_effect(layer: Image.Image, effect: str, t: float, seed: int, dots):
    draw = ImageDraw.Draw(layer, "RGBA")
    if effect in {"meteors", "cosmos"}:
        draw_meteors(draw, t, seed)

    if effect in {"fireflies", "ripples", "willow"}:
        for px, py, speed, phase in dots[:26]:
            x = 18 + px * 324 + math.sin(t * (.25 + speed * .45) + phase) * 5
            y = 365 + py * 225 + math.cos(t * (.2 + speed * .35) + phase) * 4
            strength = max(0, math.sin(t * 1.15 + phase))
            if strength > .12:
                glow(draw, x, y, (255, 220, 125), strength, 5)

    if effect in {"petals", "leaves", "willow"}:
        color = (246, 170, 214) if effect == "petals" else (101, 144, 117)
        for px, py, speed, phase in dots[:38]:
            y = ((py * 700 + t * (8 + speed * 11)) % 700) - 30
            x = px * WIDTH + math.sin(t * .55 + phase) * (8 + speed * 12)
            size = 1.5 + speed * 2.5
            draw.ellipse((x - size, y - size / 2, x + size, y + size / 2), fill=(*color, 95))

    if effect in {"snow", "aurora"}:
        for px, py, speed, phase in dots[:52]:
            y = ((py * 690 + t * (5 + speed * 10)) % 690) - 20
            x = px * WIDTH + math.sin(t * .45 + phase) * 5
            radius = .6 + speed * 1.4
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(225, 238, 255, 105))

    if effect == "aurora":
        points = [(0, 165)] + [(x, 155 + math.sin(x / 48 + t * .22) * 18) for x in range(0, WIDTH + 30, 30)] + [(WIDTH, 225), (0, 225)]
        draw.polygon(points, fill=(80, 255, 204, 18))

    if effect in {"rain", "storm"}:
        for px, py, speed, phase in dots:
            y = (py * 720 + t * (95 + speed * 90)) % 720 - 40
            x = px * WIDTH
            draw.line((x, y, x - 4, y + 15), fill=(155, 188, 236, 65), width=1)
        flash = (t + seed) % 13.7
        if effect == "storm" and flash < .11:
            draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(180, 194, 255, int((.11 - flash) * 520)))

    if effect == "steam":
        for px, py, speed, phase in dots[:18]:
            y = 585 - ((py * 150 + t * (8 + speed * 8)) % 150)
            x = 30 + px * 300 + math.sin(t * .4 + phase) * 8
            draw.ellipse((x - 8, y - 3, x + 8, y + 3), fill=(220, 216, 255, 20))

    if effect == "lanterns":
        for px, py, speed, phase in dots[:18]:
            y = 610 - ((py * 680 + t * (7 + speed * 9)) % 680)
            x = 18 + px * 324 + math.sin(t * .28 + phase) * 4
            strength = .55 + .35 * math.sin(t * .9 + phase)
            glow(draw, x, y, (255, 154, 70), strength, 7)
            draw.rounded_rectangle((x - 2, y - 3, x + 2, y + 3), radius=1, fill=(255, 177, 85, int(170 * strength)))

    if effect in {"waves", "ripples", "willow"}:
        for index in range(5):
            y = 500 + index * 26 + math.sin(t * .65 + index) * 2
            start = 18 + index * 13
            draw.arc((start, y - 5, WIDTH - start, y + 8), 7, 173, fill=(120, 177, 239, 38), width=1)

    if effect == "spores":
        for px, py, speed, phase in dots[:34]:
            y = 620 - ((py * 420 + t * (4 + speed * 7)) % 450)
            x = px * WIDTH + math.sin(t * .45 + phase) * 7
            glow(draw, x, y, (106, 224, 255), .4 + speed * .5, 4)

    if effect == "cosmos":
        for px, py, speed, phase in dots[:42]:
            pulse = .25 + .75 * max(0, math.sin(t * (1 + speed) + phase))
            x, y = px * WIDTH, py * 390
            draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(215, 220, 255, int(145 * pulse)))


def grass_and_grace(layer: Image.Image, t: float, seed: int, dots):
    draw = ImageDraw.Draw(layer, "RGBA")
    for px, py, depth, phase in dots[:44]:
        x = px * WIDTH
        y = 514 + py * 124
        length = 4 + depth * 10
        sway = math.sin(t * .58 + phase + seed) * (1 + depth * 2)
        draw.line((x, y, x + sway, y - length), fill=(50, 75, 124, int(35 + depth * 35)), width=1)

    # Una pequeña gracia visual alrededor del personaje cada pocos segundos.
    cycle = (t + seed * .73) % 9.5
    if cycle < 1.4:
        strength = math.sin(cycle / 1.4 * math.pi)
        for i in range(4):
            angle = i * math.pi / 2 + t * .35
            x = 180 + math.cos(angle) * (39 + i * 4)
            y = 472 + math.sin(angle) * (26 + i * 3)
            r = 1 + strength * 1.3
            draw.line((x - r * 2, y, x + r * 2, y), fill=(230, 221, 255, int(120 * strength)), width=1)
            draw.line((x, y - r * 2, x, y + r * 2), fill=(230, 221, 255, int(120 * strength)), width=1)


def render_scene(source: Path, output: Path, effect: str, seed: int, duration: int, fps: int, shade: Image.Image):
    base = cover(Image.open(source).convert("RGB"), WIDTH + 8, HEIGHT + 12)
    dots = particles(seed)
    writer = imageio.get_writer(
        output,
        fps=fps,
        codec="libx264",
        bitrate="1400k",
        pixelformat="yuv420p",
        macro_block_size=1,
        output_params=["-vf", "scale=720:1280:flags=lanczos", "-movflags", "+faststart"],
    )
    try:
        for number in range(duration * fps):
            t = number / fps
            drift_x = round(4 + math.sin(t * math.tau / (26 + seed % 5)) * 1.5)
            drift_y = round(6 + math.cos(t * math.tau / (31 + seed % 7)) * 1.5)
            frame = base.crop((drift_x, drift_y, drift_x + WIDTH, drift_y + HEIGHT)).convert("RGBA")
            character_breathe(frame, t, seed)
            layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
            draw_effect(layer, effect, t, seed, dots)
            grass_and_grace(layer, t, seed, dots)
            frame.alpha_composite(layer)
            frame.alpha_composite(shade)
            writer.append_data(np.asarray(frame.convert("RGB")))
    finally:
        writer.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=120)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=Path("neko-sprite-pilot/collection-20"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    assets = root / "assets"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    shade = vignette()
    selected = SCENES[args.start - 1:args.start - 1 + args.limit]
    for index, (filename, slug, effect) in enumerate(selected, start=args.start):
        output = args.output_dir / f"{slug}-2min.mp4"
        if output.exists() and not args.overwrite:
            print(f"[{index:02}/20] Ya existe: {output.name}", flush=True)
            continue
        print(f"[{index:02}/20] Renderizando {slug} · efecto {effect}", flush=True)
        render_scene(assets / filename, output, effect, index, args.duration, args.fps, shade)
        print(f"[{index:02}/20] Terminado: {output.name}", flush=True)


if __name__ == "__main__":
    main()
