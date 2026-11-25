"""Add district map tiles and format trainer battle portraits."""
import struct

from PIL import Image

from emerald_sprites import fit_sprite, index_sprite


def append_district_tiles(directory, shades, art):
    sheet_file = directory / "tiles.png"
    with Image.open(sheet_file) as image:
        old = image.copy()
    if old.mode != "P" or old.width != 128 or old.height % 8 != 0:
        raise SystemExit("Unexpected district tile sheet")
    count = old.width * old.height // 64
    sheet = Image.new("P", (128, old.height + 8 * ((4 * len(art) + 15) // 16)))
    sheet.putpalette(old.getpalette())
    sheet.paste(old, (0, 0))
    palette = directory / "palettes/12.pal"
    palette.write_text("JASC-PAL\n0100\n16\n" + "\n".join(
        " ".join(map(str, rgb)) for rgb in shades) + "\n", encoding="ascii")

    mt = directory / "metatiles.bin"
    at = directory / "metatile_attributes.bin"
    data = bytearray(mt.read_bytes())
    attrs = bytearray(at.read_bytes())
    if len(data) != 8 * len(attrs):
        raise SystemExit("Invalid district tile attributes")
    ids = {}
    for name, tile in art.items():
        ids[name] = 512 + len(data) // 16
        entries = []
        for y in (0, 8):
            for x in (0, 8):
                sheet.paste(tile.crop((x, y, x + 8, y + 8)), ((count % 16) * 8, (count // 16) * 8))
                entries.append((12 << 12) | (512 + count))
                count += 1
        data.extend(struct.pack("<8H", *entries, 0, 0, 0, 0))
        attrs.extend(b"\0\0")
    sheet.save(sheet_file, bits=4)
    mt.write_bytes(data)
    at.write_bytes(attrs)
    return ids


def install_trainer_art(portrait, destination):
    sprite = fit_sprite(portrait)
    visible = [pixel[:3] for pixel in sprite.getdata() if pixel[3]]
    sample = Image.new("RGB", (len(visible), 1))
    sample.putdata(visible)
    quantized = sample.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    palette = quantized.getpalette()[:45]
    colors = [(0, 0, 0), *(tuple(palette[i:i + 3]) for i in range(0, 45, 3))]
    index_sprite(sprite, colors).save(destination,
                                     bits=4, transparency=0)
