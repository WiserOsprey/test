#!/usr/bin/env python3
"""Quantize a paired creature concept into Emerald's indexed 64x64 sprite format."""
import sys
from pathlib import Path
from PIL import Image

front_path, back_path, out_dir = map(Path, sys.argv[1:4])
out_dir.mkdir(parents=True, exist_ok=True)

def prepare(path):
    image = Image.open(path).convert("RGBA")
    bounds = image.getchannel("A").getbbox()
    if bounds is None:
        raise SystemExit(f"{path} has no visible pixels")
    image = image.crop(bounds)
    scale = min(60 / image.width, 58 / image.height)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    image = image.resize(size, Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    canvas.alpha_composite(image, ((64 - size[0]) // 2, 60 - size[1]))
    return canvas

front = prepare(front_path)
back = prepare(back_path)

visible = [image.getchannel("A").getbbox() for image in (front, back)]
combined = Image.new("RGB", (128, 64), (64, 64, 64))
for i, image in enumerate((front, back)):
    box = image.getchannel("A").getbbox()
    if box:
        combined.paste(image.convert("RGB").crop(box), (i * 64, 0))

sample = combined.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
raw = sample.getpalette()[:45]
colors = [tuple(raw[i:i + 3]) for i in range(0, 45, 3)]
palette = [0, 0, 0]
for rgb in colors:
    palette.extend(rgb)
palette.extend([0] * (768 - len(palette)))
palette_image = Image.new("P", (1, 1))
palette_image.putpalette(palette)

def save_sprite(image, path):
    mapped = image.convert("RGB").quantize(palette=palette_image, dither=Image.Dither.NONE)
    alpha = image.getchannel("A").load()
    source = mapped.load()
    output = Image.new("P", (64, 64), 0)
    output.putpalette(palette)
    target = output.load()
    for y in range(64):
        for x in range(64):
            if alpha[x, y] >= 128:
                target[x, y] = source[x, y] + 1
    output.save(path, transparency=0)

save_sprite(front, out_dir / "front.png")
save_sprite(back, out_dir / "back.png")
with (out_dir / "normal.pal").open("w", newline="\n") as stream:
    stream.write("JASC-PAL\n0100\n16\n")
    stream.write("0 0 0\n")
    for r, g, b in colors:
        stream.write(f"{r} {g} {b}\n")
