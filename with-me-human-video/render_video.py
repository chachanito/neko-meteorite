"""Renderiza un video humano y emotivo de un minuto, listo para añadir música en TikTok."""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


WIDTH, HEIGHT = 720, 1280
FPS = 12
SCENE_CHANGES = (0, 19, 41, 60)
CAPTIONS = [
    (3, 14, "Me quedé con lo que no dije."),
    (18, 31, "Cada recuerdo todavía respira."),
    (34, 46, "No todo lo que termina deja de importar."),
    (48, 58, "Y aun así, voy a seguir adelante."),
]


def cover(image: Image.Image, width: int, height: int) -> Image.Image:
    scale = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def scene_frame(image: Image.Image, t: float, scene_index: int) -> Image.Image:
    x = round(12 + math.sin(t * .12 + scene_index) * 7)
    y = round(18 + math.cos(t * .10 + scene_index * .8) * 7)
    return image.crop((x, y, x + WIDTH, y + HEIGHT)).convert("RGBA")


def breathe(frame: Image.Image, t: float, scene_index: int) -> None:
    boxes = [(205, 490, 515, 1210), (105, 500, 580, 1170), (200, 490, 520, 1215)]
    box = boxes[scene_index]
    patch = frame.crop(box)
    stretch = 1 + math.sin(t * math.tau / 4.6) * .004
    moved = patch.resize((patch.width, round(patch.height * stretch)), Image.Resampling.BICUBIC)
    local = Image.new("RGBA", patch.size, (0, 0, 0, 0))
    local.alpha_composite(moved, (round(math.sin(t * .72) * 1.2), patch.height - moved.height))
    mask = Image.new("L", patch.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((18, 18, patch.width - 18, patch.height - 18), radius=70, fill=150)
    mask = mask.filter(ImageFilter.GaussianBlur(24))
    frame.paste(local, box, mask)


def rain_layer(t: float, strength: float, particles) -> Image.Image:
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    for x0, y0, speed, phase in particles:
        y = (y0 * 1420 + t * (290 + speed * 260)) % 1420 - 80
        x = x0 * WIDTH + math.sin(t * .35 + phase) * 3
        length = 16 + speed * 24
        draw.line((x, y, x - 5, y + length), fill=(180, 207, 248, int((35 + speed * 55) * strength)), width=1)
    return layer


def memory_glow(t: float, particles) -> Image.Image:
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    pulse = .55 + math.sin(t * .55) * .15
    draw.ellipse((310, 160, 760, 620), fill=(255, 189, 112, int(16 * pulse)))
    for x0, y0, speed, phase in particles[:28]:
        x = x0 * WIDTH
        y = 260 + ((y0 * 850 - t * (8 + speed * 11)) % 850)
        alpha = int(50 + 55 * max(0, math.sin(t * .8 + phase)))
        r = 1 + speed * 2
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 214, 158, alpha))
    return layer.filter(ImageFilter.GaussianBlur(1.2))


def dawn_leaves(t: float, particles) -> Image.Image:
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    for x0, y0, speed, phase in particles[:34]:
        x = (x0 * 850 + t * (15 + speed * 25)) % 850 - 65
        y = (y0 * 1420 + t * (18 + speed * 28)) % 1420 - 70
        sway = math.sin(t * .75 + phase) * 16
        size = 3 + speed * 7
        draw.ellipse((x + sway - size, y - size / 2, x + sway + size, y + size / 2), fill=(126, 78, 35, 115))
    return layer


def font(size: int) -> ImageFont.FreeTypeFont:
    choices = [
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    ]
    for choice in choices:
        if choice.exists():
            return ImageFont.truetype(str(choice), size)
    return ImageFont.load_default()


def caption_layer(t: float) -> Image.Image:
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    typeface = font(35)
    for start, end, text in CAPTIONS:
        if not start <= t <= end:
            continue
        fade = min(1, (t - start) / .6, (end - t) / .6)
        fade = max(0, fade)
        bbox = draw.textbbox((0, 0), text, font=typeface)
        text_width = bbox[2] - bbox[0]
        x = (WIDTH - text_width) / 2
        y = 1060
        draw.rounded_rectangle((x - 25, y - 17, x + text_width + 25, y + 58), radius=25, fill=(3, 5, 18, int(175 * fade)))
        draw.text(
            (x, y),
            text,
            font=typeface,
            fill=(255, 252, 255, int(255 * fade)),
            stroke_width=2,
            stroke_fill=(0, 0, 8, int(225 * fade)),
        )
    return layer


def transition(images: list[Image.Image], t: float) -> tuple[Image.Image, int]:
    if t < SCENE_CHANGES[1]:
        index = 0
        local = t
    elif t < SCENE_CHANGES[2]:
        index = 1
        local = t - SCENE_CHANGES[1]
    else:
        index = 2
        local = t - SCENE_CHANGES[2]

    frame = scene_frame(images[index], t, index)
    if index < 2:
        boundary = SCENE_CHANGES[index + 1]
        if boundary - 2 <= t < boundary:
            amount = (t - (boundary - 2)) / 2
            next_frame = scene_frame(images[index + 1], t, index + 1)
            frame = Image.blend(frame, next_frame, amount)
            if amount > .5:
                index += 1
    return frame, index


def render(output: Path, duration: int = 60, fps: int = FPS) -> None:
    root = Path(__file__).parent
    paths = [root / "assets/01-rainy-stop.png", root / "assets/02-memory-window.png", root / "assets/03-dawn-walk.png"]
    images = [cover(Image.open(path).convert("RGB"), WIDTH + 24, HEIGHT + 36) for path in paths]
    rng = random.Random(4117)
    particles = [(rng.random(), rng.random(), rng.random(), rng.random() * math.tau) for _ in range(105)]
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio.get_writer(
        output,
        fps=fps,
        codec="libx264",
        bitrate="3200k",
        pixelformat="yuv420p",
        macro_block_size=1,
        output_params=["-movflags", "+faststart"],
    )

    try:
        for number in range(duration * fps):
            t = number / fps
            frame, scene_index = transition(images, t)
            breathe(frame, t, scene_index)
            if scene_index == 0:
                frame.alpha_composite(rain_layer(t, 1, particles))
            elif scene_index == 1:
                frame.alpha_composite(rain_layer(t, .42, particles))
                frame.alpha_composite(memory_glow(t, particles))
            else:
                frame.alpha_composite(dawn_leaves(t, particles))

            frame.alpha_composite(caption_layer(t))
            if t > duration - 2:
                darkness = int(255 * ((t - (duration - 2)) / 2))
                frame.alpha_composite(Image.new("RGBA", frame.size, (2, 3, 12, darkness)))
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
    parser.add_argument("--output", type=Path, default=Path("with-me-human-video/with-me-emotional-1min.mp4"))
    args = parser.parse_args()
    render(args.output, args.duration, args.fps)


if __name__ == "__main__":
    main()
