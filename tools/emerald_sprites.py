"""Prepare Emerald battle sprites and the palettes they share."""
from colorsys import hsv_to_rgb, rgb_to_hsv

from PIL import Image


def fit_sprite(path):
    with Image.open(path) as source:
        image = source.convert("RGBA")
    alpha = image.getchannel("A").point(lambda value: 255 if value >= 128 else 0)
    image.putalpha(alpha)
    bounds = alpha.getbbox()
    if bounds is None:
        raise ValueError(f"{path} has no visible pixels")
    image = image.crop(bounds)
    scale = min(60 / image.width, 58 / image.height)
    width = max(1, round(image.width * scale))
    height = max(1, round(image.height * scale))
    image = image.resize((width, height), Image.Resampling.NEAREST)
    result = Image.new("RGBA", (64, 64))
    result.paste(image, ((64 - width) // 2, 60 - height))
    return result


def index_sprite(image, colors):
    result = Image.new("P", image.size)
    palette = [channel for color in colors for channel in color]
    result.putpalette(palette + [0] * (768 - len(palette)))
    # Index zero is reserved for transparency, including when art uses black.
    opaque_indices = range(1, len(colors))
    matches = {}
    indices = []
    for r, g, b, alpha in image.getdata():
        if not alpha:
            indices.append(0)
            continue
        rgb = (r, g, b)
        if rgb not in matches:
            matches[rgb] = min(opaque_indices, key=lambda i:
                               sum((a - b) ** 2 for a, b in zip(rgb, colors[i])))
        indices.append(matches[rgb])
    result.putdata(indices)
    return result


def write_palette(path, colors):
    with path.open("w", encoding="ascii", newline="\n") as stream:
        stream.write("JASC-PAL\n0100\n16\n")
        for color in colors:
            stream.write(" ".join(map(str, color)) + "\n")


def shiny_palette(colors):
    result = [colors[0]]
    for color in colors[1:]:
        hue, saturation, value = rgb_to_hsv(*(channel / 255 for channel in color))
        shifted = hsv_to_rgb((hue + 0.34) % 1.0, saturation, value)
        result.append(tuple(round(channel * 255) for channel in shifted))
    return result


def write_battle_sprites(out_dir, front, back, colors, animation_size=None):
    out_dir.mkdir(parents=True, exist_ok=True)
    animation_path = out_dir / "anim_front.png"
    if animation_size is None:
        with Image.open(animation_path) as previous_animation:
            animation_size = previous_animation.size
    width, height = animation_size
    if width % 64 or height % 64:
        raise ValueError(f"Unsupported animation sheet dimensions: {width} x {height}")
    frames = Image.new("P", (width, height))
    frames.putpalette(front.getpalette())
    for index, (y, x) in enumerate((y, x) for y in range(0, height, 64)
                                    for x in range(0, width, 64)):
        # Each animation command still addresses the same number of frames.
        frame = front.crop((0, index % 2, 64, 64))
        frames.paste(frame, (x, y))
    frames.save(animation_path, transparency=0)
    front.save(out_dir / "front.png", transparency=0)
    back.save(out_dir / "back.png", transparency=0)
    write_palette(out_dir / "normal.pal", colors)
    write_palette(out_dir / "shiny.pal", shiny_palette(colors))


def install_pair(front_path, back_path, out_dir, animation_size=None):
    front = fit_sprite(front_path)
    back = fit_sprite(back_path)
    pixels = [pixel[:3] for view in (front, back) for pixel in view.getdata() if pixel[3]]
    sample = Image.new("RGB", (len(pixels), 1))
    sample.putdata(pixels)
    quantized = sample.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    palette = quantized.getpalette()[:45]
    colors = [(0, 0, 0), *(tuple(palette[i:i + 3]) for i in range(0, 45, 3))]

    write_battle_sprites(out_dir, index_sprite(front, colors), index_sprite(back, colors), colors, animation_size)
