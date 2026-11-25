#!/usr/bin/env python3
"""Fit Reedwake's title lettering and install the new title screen."""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

art_path, source = map(Path, sys.argv[1:3])

# The title uses a small block alphabet built for single GBA display pixels.
glyphs = {
    "A": [
        "01110",
        "11011",
        "11011",
        "11111",
        "11011",
        "11011",
        "11011"
    ],
    "D": [
        "11110",
        "11011",
        "11011",
        "11011",
        "11011",
        "11011",
        "11110"
    ],
    "E": [
        "11111",
        "11000",
        "11000",
        "11110",
        "11000",
        "11000",
        "11111"
    ],
    "H": [
        "11011",
        "11011",
        "11011",
        "11111",
        "11011",
        "11011",
        "11011"
    ],
    "I": [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "11111"
    ],
    "K": [
        "11011",
        "11010",
        "11100",
        "11100",
        "11010",
        "11011",
        "11011"
    ],
    "N": [
        "11001",
        "11101",
        "11101",
        "11011",
        "11011",
        "11001",
        "11001"
    ],
    "O": [
        "01110",
        "11011",
        "11011",
        "11011",
        "11011",
        "11011",
        "01110"
    ],
    "P": [
        "11110",
        "11011",
        "11011",
        "11110",
        "11000",
        "11000",
        "11000"
    ],
    "R": [
        "11110",
        "11011",
        "11011",
        "11110",
        "11100",
        "11010",
        "11011"
    ],
    "S": [
        "01111",
        "11000",
        "11000",
        "01110",
        "00011",
        "00011",
        "11110"
    ],
    "T": [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100"
    ],
    "W": [
        "10001",
        "10001",
        "10001",
        "10101",
        "10101",
        "11111",
        "11011"
    ],
    " ": [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000"
    ]
}


def draw_text(draw, text, y, scale, face, shade, shadow, tracking=1):
    advance = 5 * scale + tracking
    x = (240 - (len(text) * advance - tracking)) // 2
    for character in text:
        for row, pixels in enumerate(glyphs[character]):
            for column, ink in enumerate(pixels):
                if ink == "0":
                    continue
                left = x + column * scale
                top = y + row * scale
                draw.rectangle((left + 1, top + 2, left + scale, top + scale + 1), fill=shadow)
        x += advance
    x = (240 - (len(text) * advance - tracking)) // 2
    for character in text:
        for row, pixels in enumerate(glyphs[character]):
            for column, ink in enumerate(pixels):
                if ink == "0":
                    continue
                left = x + column * scale
                top = y + row * scale
                draw.rectangle((left, top, left + scale - 1, top + scale - 1),
                               fill=face if row < 4 else shade)
        x += advance


with Image.open(art_path) as background:
    image = background.convert("RGB")
if image.size != (240, 160):
    raise SystemExit("Reedwake title art must be 240 by 160 pixels")

draw = ImageDraw.Draw(image)
draw_text(draw, "REEDWAKE", 19, 4, (246, 228, 177), (222, 174, 108), (14, 22, 47), tracking=4)
draw.line((27, 57, 46, 57), fill=(83, 164, 171))
draw.line((194, 57, 213, 57), fill=(83, 164, 171))
draw_text(draw, "THE RESONANT TIDE", 54, 1, (171, 232, 222), (121, 203, 198), (16, 37, 63), tracking=2)
draw.rectangle((79, 139, 160, 154), fill=(12, 21, 42), outline=(67, 118, 131))
draw_text(draw, "PRESS START", 143, 1, (229, 246, 216), (166, 216, 186), (22, 53, 63))

indexed = image.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
palette = indexed.getpalette()
indexed.putpalette(palette + [0] * (768 - len(palette)))
indexed.save(source / "graphics/title_screen/reedwake.png", bits=8)

title = source / "src/title_screen.c"
original = title.read_text(encoding="utf-8")
blend_data = re.search(r"(?ms)^const u16 gTitleScreenAlphaBlend\[64\] =\n\{.*?^\};", original)
if blend_data is None:
    raise SystemExit("Intro alpha blend table is missing")
template = Path(__file__).with_name("reedwake_title.c").read_text(encoding="utf-8")
title.write_text(template.replace("/* Intro blend table */", blend_data[0]), encoding="utf-8")
