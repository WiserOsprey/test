#!/usr/bin/env python3
"""Install Rillfin's two battle views using its dedicated palette."""
import sys
from pathlib import Path

from PIL import Image

from emerald_sprites import fit_sprite, index_sprite, write_battle_sprites

front_path, back_path, palette_path, out_dir = map(Path, sys.argv[1:5])
header, version, count, *rows = palette_path.read_text(encoding="ascii").splitlines()
if (header, version, count) != ("JASC-PAL", "0100", "16") or len(rows) != 16:
    raise SystemExit("Rillfin needs a JASC-PAL 0100 palette with 16 entries")
colors = [tuple(map(int, row.split())) for row in rows]

with Image.open(front_path) as image:
    if image.size != (64, 64):
        raise SystemExit("Rillfin's front view should already fit the battle canvas")
    front = index_sprite(image.convert("RGBA"), colors)
back = index_sprite(fit_sprite(back_path), colors)
write_battle_sprites(out_dir, front, back, colors)
