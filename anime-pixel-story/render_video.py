"""Renderiza una historia humana de anime pixel art, sin palabras ni audio."""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


WIDTH, HEIGHT = 360, 640
FPS = 12
BOUNDARIES = (0, 20, 40, 60)


def cover(image: Image.Image, width: int, height: int) -> Image.Image:
    scale = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def base_frame(image: Image.Image, t: float, index: int) -> Image.Image:
    x = round(4 + math.sin(t * .14 + index) * 2)
    y = round(6 + math.cos(t * .11 + index) * 2)
    return image.crop((x, y, x + WIDTH, y + HEIGHT)).convert("RGBA")


def subject_motion(frame: Image.Image, t: float, index: int) -> None:
    boxes = [(82, 240, 220, 580), (22, 315, 215, 570), (102, 252, 218, 570)]
    box = boxes[index]
    patch = frame.crop(box)
    bob = round(math.sin(t * math.tau / (4.4 + index * .3)))
    stretch = patch.height + round(math.sin(t * math.tau / 4.8) * 1)
    moved = patch.resize((patch.width, stretch), Image.Resampling.NEAREST)
    local = Image.new("RGBA", patch.size, (0, 0, 0, 0))
    local.alpha_composite(moved, (0, patch.height - moved.height + bob))
    mask = Image.new("L", patch.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((10, 10, patch.width - 10, patch.height - 10), radius=18, fill=150)
    mask = mask.filter(ImageFilter.GaussianBlur(5))
    frame.paste(local, box, mask)


def pixel_dissolve(first: Image.Image, second: Image.Image, amount: float, seed: int) -> Image.Image:
    output = first.copy()
    rng = random.Random(seed)
    block = 8
    for y in range(0, HEIGHT, block):
        for x in range(0, WIDTH, block):
            threshold = rng.random()
            if threshold < amount:
                output.paste(second.crop((x, y, min(x + block, WIDTH), min(y + block, HEIGHT))), (x, y))
    return output


def timeline(images: list[Image.Image], t: float) -> tuple[Image.Image, int]:
    if t < BOUNDARIES[1]:
        index = 0
    elif t < BOUNDARIES[2]:
        index = 1
    else:
        index = 2
    frame = base_frame(images[index], t, index)
    if index < 2 and t >= BOUNDARIES[index + 1] - 2:
        amount = (t - (BOUNDARIES[index + 1] - 2)) / 2
        next_frame = base_frame(images[index + 1], t, index + 1)
        frame = pixel_dissolve(frame, next_frame, amount, 700 + index)
        if amount > .55:
            index += 1
    return frame, index


def glow_rect(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple[int, int, int], strength: float) -> None:
    for radius, alpha in ((7, 12), (4, 26), (2, 70)):
        draw.rectangle((x - radius, y - radius, x + radius, y + radius), fill=(*color, int(alpha * strength)))
    draw.rectangle((x - 1, y - 1, x + 1, y + 1), fill=(*color, int(220 * strength)))


def rain(t: float, particles, amount: float = 1) -> Image.Image:
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    for px, py, speed, phase in particles:
        y = int((py * 710 + t * (95 + speed * 110)) % 710 - 35)
        x = int(px * WIDTH + math.sin(t * .3 + phase) * 2)
        length = int(6 + speed * 9)
        draw.line((x, y, x - 2, y + length), fill=(162, 190, 245, int((42 + speed * 65) * amount)), width=1)
    for offset in range(0, WIDTH, 34):
        ripple = (t * 34 + offset) % 110
        if ripple < 12:
            y = 555 + (offset * 7 % 68)
            width = 2 + int(ripple / 3)
            draw.ellipse((offset - width, y - 1, offset + width, y + 1), outline=(145, 183, 232, int(80 * amount)), width=1)
    return layer


def memory_lights(t: float, particles) -> Image.Image:
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    pulse = .65 + math.sin(t * .8) * .2
    glow_rect(draw, 214, 360, (255, 180, 78), pulse)
    glow_rect(draw, 272, 355, (255, 147, 74), pulse * .8)
    for px, py, speed, phase in particles[:22]:
        x = int(25 + px * 310 + math.sin(t * .35 + phase) * 3)
        y = int(310 + ((py * 250 - t * (2 + speed * 3)) % 260))
        strength = max(0, math.sin(t * 1.1 + phase))
        if strength > .3:
            glow_rect(draw, x, y, (255, 207, 111), strength * .65)
    return layer


def dawn_petals(t: float, particles) -> Image.Image:
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    for px, py, speed, phase in particles[:46]:
        x = int((px * 420 + t * (8 + speed * 12)) % 420 - 30 + math.sin(t * .7 + phase) * 5)
        y = int((py * 700 + t * (7 + speed * 10)) % 700 - 30)
        size = 1 + int(speed * 2)
        draw.rectangle((x - size, y, x + size, y + 1), fill=(255, 155, 196, 120))
    train_x = int(202 + min(1, (t - 40) / 20) * 28)
    train_y = int(373 - min(1, (t - 40) / 20) * 11)
    glow_rect(draw, train_x, train_y, (255, 75, 58), .75 + math.sin(t * 4) * .2)
    return layer


def render(output: Path, duration: int = 60, fps: int = FPS) -> None:
    root = Path(__file__).parent
    sources = [
        root / "assets/01-waiting-rain.png",
        root / "assets/02-shared-memory.png",
        root / "assets/03-letting-go.png",
    ]
    images = [cover(Image.open(path).convert("RGB"), WIDTH + 8, HEIGHT + 12) for path in sources]
    rng = random.Random(8821)
    particles = [(rng.random(), rng.random(), rng.random(), rng.random() * math.tau) for _ in range(95)]
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio.get_writer(
        output,
        fps=fps,
        codec="libx264",
        bitrate="2300k",
        pixelformat="yuv420p",
        macro_block_size=1,
        output_params=["-vf", "scale=720:1280:flags=neighbor", "-movflags", "+faststart"],
    )
    try:
        for number in range(duration * fps):
            t = number / fps
            frame, index = timeline(images, t)
            subject_motion(frame, t, index)
            if index == 0:
                frame.alpha_composite(rain(t, particles, 1))
            elif index == 1:
                frame.alpha_composite(rain(t, particles, .35))
                frame.alpha_composite(memory_lights(t, particles))
            else:
                frame.alpha_composite(dawn_petals(t, particles))
            if t > duration - 2:
                darkness = int(255 * (t - (duration - 2)) / 2)
                frame.alpha_composite(Image.new("RGBA", frame.size, (3, 4, 15, darkness)))
            writer.append_data(np.asarray(frame.convert("RGB")))
            if number % (fps * 10) == 0:
                print(f"Renderizados {number // fps:>2}/{duration} segundos", flush=True)
    finally:
        writer.close()
    print(f"Video terminado: {output.resolve()}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--fps", type=int, default=FPS)
    parser.add_argument("--output", type=Path, default=Path("anime-pixel-story/anime-pixel-historia-1min.mp4"))
    args = parser.parse_args()
    render(args.output, args.duration, args.fps)


if __name__ == "__main__":
    main()
