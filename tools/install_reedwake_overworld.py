#!/usr/bin/env python3
"""Replace building and path art while preserving map events and doors."""
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from reedwake_district_assets import append_district_tiles

ROOT = Path(sys.argv[1])
PALETTE = [
    (0, 0, 0), (22, 24, 39), (35, 38, 58), (54, 60, 77),
    (79, 89, 105), (118, 141, 139), (172, 187, 165), (220, 218, 173),
    (57, 86, 90), (57, 133, 129), (100, 190, 172), (177, 226, 183),
    (94, 55, 59), (152, 86, 66), (207, 132, 78), (249, 192, 110),
]


def facade(style):
    roof, seam, light = {"station": (8, 9, 10), "observatory": (3, 4, 10),
                         "tram": (12, 13, 15)}[style]
    image = Image.new("P", (48, 48), 1)
    draw = ImageDraw.Draw(image)
    draw.rectangle((1, 2, 46, 30), fill=roof, outline=1)
    draw.rectangle((3, 3, 44, 29), outline=seam)
    for y in range(7, 29, 5):
        draw.line((3, y, 44, y), fill=seam)
        draw.line((6, y + 1, 40, y + 1), fill=roof)
    if style == "observatory":
        draw.ellipse((11, 0, 36, 26), fill=8, outline=1)
        draw.ellipse((13, 1, 34, 22), fill=9, outline=10)
        draw.arc((19, 1, 29, 22), 90, 270, fill=15)
        draw.rectangle((25, 5, 34, 9), fill=3, outline=1)
        draw.rectangle((30, 4, 36, 8), fill=6, outline=4)
    elif style == "tram":
        for x in (9, 34):
            draw.rectangle((x, 4, x + 4, 26), fill=2)
            for y in (5, 9, 13, 17, 21):
                draw.line((x - 1, y, x + 5, y), fill=14)
        draw.rectangle((20, 7, 27, 19), fill=3, outline=15)
        draw.line((22, 14, 25, 11), fill=10)
    else:
        draw.line((23, 4, 23, 28), fill=15, width=2)
        draw.rectangle((9, 10, 16, 20), fill=3, outline=14)
        draw.rectangle((31, 10, 38, 20), fill=3, outline=14)
    draw.rectangle((1, 29, 46, 33), fill=14, outline=1)
    draw.rectangle((2, 34, 45, 47), fill=6, outline=4)
    draw.line((2, 38, 45, 38), fill=5)
    draw.line((2, 44, 45, 44), fill=5)
    for x in (6, 34):
        draw.rectangle((x, 36, x + 7, 44), fill=8, outline=3)
        draw.line((x + 2, 39, x + 5, 39), fill=light)
        draw.line((x + 3, 37, x + 3, 42), fill=light)
    draw.rectangle((18, 34, 29, 47), fill=2, outline=13)
    draw.line((19, 34, 28, 34), fill=15)
    return {f"{style}_{x}_{y}": image.crop((16*x, 16*y, 16*x+16, 16*y+16))
            for y in range(3) for x in range(3)}


def install(name, tileset, buildings):
    tiles = {}
    for _, _, style in buildings:
        tiles.update(facade(style))
    paving = Image.new("P", (16, 16), 4)
    draw = ImageDraw.Draw(paving)
    draw.rectangle((0, 0, 15, 15), outline=3)
    draw.line((0, 7, 15, 7), fill=3)
    draw.line((7, 0, 7, 7), fill=3)
    draw.line((4, 8, 4, 15), fill=3)
    draw.point([(2, 2), (11, 3), (8, 10), (14, 12)], fill=5)
    tiles["paving"] = paving
    folder = ROOT / "data/tilesets/secondary" / tileset
    ids = append_district_tiles(folder, PALETTE, tiles)
    if (folder / "tiles.png").is_file():
        with Image.open(folder / "tiles.png") as sheet:
            if sheet.width * sheet.height // 64 > 512:
                raise SystemExit("The secondary tile sheet exceeds the GBA limit.")
    path = ROOT / "data/layouts" / name / "map.bin"
    original = struct.unpack("<400H", path.read_bytes())
    cells = list(original)
    touched = set()
    for x, door_y, style in buildings:
        for y in range(3):
            for dx in range(3):
                pos = (door_y - 3 + y) * 20 + x - 1 + dx
                word = original[pos]
                if word & 0xC00:
                    cells[pos] = (word & 0xFC00) | ids[f"{style}_{dx}_{y}"]
                    touched.add(pos)
        if cells[door_y * 20 + x] != original[door_y * 20 + x]:
            raise SystemExit("Building replacement touched a warp tile.")
        for dx in (-1, 0, 1):
            pos = (door_y + 1) * 20 + x + dx
            if original[pos] == 0x3001:
                cells[pos] = 0x3000 | ids["paving"]
    if not touched or any((a ^ b) & 0xFC00 for a, b in zip(cells, original)):
        raise SystemExit("Invalid overworld collision change.")
    path.write_bytes(struct.pack("<400H", *cells))


install("LittlerootTown", "petalburg",
        [(5, 8, "station"), (14, 8, "station"), (7, 16, "observatory")])
install("LavaridgeTown", "lavaridge", [(5, 15, "tram")])
