#!/usr/bin/env python3
"""Install both battle views of a Reedwake creature using a shared palette."""
import sys
from pathlib import Path

from PIL import Image

from emerald_sprites import fit_sprite, index_sprite, write_battle_sprites

front_path, back_path, out_dir = map(Path, sys.argv[1:4])
front = fit_sprite(front_path)
back = fit_sprite(back_path)
pixels = [pixel[:3] for view in (front, back) for pixel in view.getdata() if pixel[3]]
sample = Image.new("RGB", (len(pixels), 1))
sample.putdata(pixels)
quantized = sample.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
palette = quantized.getpalette()[:45]
colors = [(0, 0, 0), *(tuple(palette[i:i + 3]) for i in range(0, 45, 3))]

write_battle_sprites(out_dir, index_sprite(front, colors), index_sprite(back, colors), colors)
