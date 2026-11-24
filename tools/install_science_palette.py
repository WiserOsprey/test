#!/usr/bin/env python3
"""Install the science-fantasy palette in the fitted Pokédex source assets."""
import re
import struct
import sys
from pathlib import Path


PALETTE_5BIT = [
    (0, 0, 0),
    (2, 3, 5),
    (4, 8, 10),
    (8, 14, 12),
    (12, 18, 11),
    (17, 21, 14),
    (22, 24, 18),
    (27, 25, 20),
    (30, 29, 24),
    (31, 31, 29),
    (7, 15, 15),
    (13, 23, 22),
    (20, 26, 23),
    (21, 17, 11),
    (26, 22, 14),
    (31, 31, 31),
]


def rgb555(red, green, blue):
    return (red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10)


def words_to_bytes(colors):
    return b"".join(struct.pack("<H", rgb555(*rgb)) for rgb in colors)


def main():
    source_root = Path(sys.argv[1])
    palette_path = Path(sys.argv[2])
    palette_lines = palette_path.read_text(encoding="ascii").splitlines()
    if palette_lines[:3] != ["JASC-PAL", "0100", "96"]:
        raise SystemExit("Expected a 96-entry JASC-PAL file.")
    colors = [tuple(map(int, line.split())) for line in palette_lines[3:] if line.strip()]
    if len(colors) != 96:
        raise SystemExit("Expected exactly 96 palette colors.")

    graphics = source_root / "graphics" / "pokedex" / "purple"
    (graphics / "background.gbapal").write_bytes(words_to_bytes(colors))
    (graphics / "foreground.gbapal").write_bytes(words_to_bytes([
        tuple(channel << 3 for channel in color) for color in PALETTE_5BIT
    ]))

    c_file = source_root / "src" / "pokedex.c"
    text = c_file.read_text(encoding="utf-8")
    replacement = "static const u16 sPurpleInterfacePalette[] =\n{\n"
    rows = []
    for index, (red, green, blue) in enumerate(PALETTE_5BIT):
        rows.append("    RGB(%d, %d, %d)%s" % (
            red, green, blue, "," if index < 15 else ""
        ))
    replacement += "\n".join(rows) + "\n};"
    updated, count = re.subn(
        r"static const u16 sPurpleInterfacePalette\[\]\s*=\s*\{.*?\};",
        replacement,
        text,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise SystemExit("Could not find the fitted Pokédex interface palette.")
    c_file.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
