#!/usr/bin/env python3
"""Install native-size Rillfin battle views using the approved 16-color palette."""
import sys
from pathlib import Path
from PIL import Image

front_path, back_path, palette_path, out_dir = map(Path, sys.argv[1:5])

def load_jasc(path):
    lines = path.read_text().splitlines()
    if lines[0] != "JASC-PAL" or lines[1] != "0100":
        raise SystemExit("Expected a JASC-PAL 0100 palette")
    count = int(lines[2])
    colors = [tuple(map(int, line.split())) for line in lines[3:3 + count]]
    if len(colors) != 16:
        raise SystemExit("Emerald sprites need exactly 16 palette entries")
    return colors

colors = load_jasc(palette_path)
out_dir.mkdir(parents=True, exist_ok=True)
# Front was already reduced and inspected at its configured native canvas.
Image.open(front_path).save(out_dir / "front.png")

source = Image.open(back_path).convert("RGBA")
alpha = source.getchannel("A")
bbox = alpha.getbbox()
if bbox is None:
    raise SystemExit("Back sprite has no visible pixels")
source = source.crop(bbox)
max_w, max_h = 60, 58
scale = min(max_w / source.width, max_h / source.height)
size = (max(1, round(source.width * scale)), max(1, round(source.height * scale)))
source = source.resize(size, Image.Resampling.NEAREST)
x = (64 - size[0]) // 2
y = 60 - size[1]

palette = [0, 0, 0]
for color in colors[1:]:
    palette.extend(color)
palette.extend([0] * (768 - len(palette)))
palette_image = Image.new("P", (1, 1))
palette_image.putpalette(palette)
rgb = source.convert("RGB")
mapped = rgb.quantize(palette=palette_image, dither=Image.Dither.NONE)
out = Image.new("P", (64, 64), 0)
out.putpalette(palette)
mapped_pixels = mapped.load()
source_alpha = source.getchannel("A").load()
out_pixels = out.load()
for sy in range(size[1]):
    for sx in range(size[0]):
        if source_alpha[sx, sy] >= 128:
            out_pixels[x + sx, y + sy] = mapped_pixels[sx, sy] + 1
out.info["transparency"] = 0
out.save(out_dir / "back.png", transparency=0)
