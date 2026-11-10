"""Turn assets/avatar.png into ASCII art for the profile card.

Run once locally (needs Pillow) whenever the photo changes:
    pip install pillow && python tools/make_ascii.py
Writes assets/ascii-dark.txt and assets/ascii-light.txt.
"""
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parent.parent
COLS = 58
# Monospace glyphs are about twice as tall as they are wide.
CHAR_ASPECT = 0.5
# Face-and-shoulders box (left, top, right, bottom) in the 400px photo.
CROP = (70, 0, 350, 330)
RAMP = " .`:-=+*cox#%&@"


# Below this the photo is just backdrop; it stays blank on both cards.
BACKDROP = 28


def glyph(v, invert):
    if v < BACKDROP:
        return " "
    if invert:
        v = 255 - v + BACKDROP
    return RAMP[min(v, 255) * (len(RAMP) - 1) // 255]


def render(img, invert):
    w, h = img.size
    rows = round(COLS * h / w * CHAR_ASPECT)
    px = img.resize((COLS, rows), Image.LANCZOS).load()
    lines = []
    for y in range(rows):
        lines.append("".join(glyph(px[x, y], invert) for x in range(COLS)).rstrip())
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    indent = min(len(l) - len(l.lstrip()) for l in lines if l)
    return "\n".join(l[indent:] for l in lines) + "\n"


def main():
    img = Image.open(ROOT / "assets" / "avatar.png").convert("L").crop(CROP)
    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Contrast(img).enhance(1.3)
    # Dark card: bright pixels get dense glyphs. Light card: the reverse,
    # like a pencil sketch, with the backdrop still blank.
    (ROOT / "assets" / "ascii-dark.txt").write_text(render(img, invert=False))
    (ROOT / "assets" / "ascii-light.txt").write_text(render(img, invert=True))


if __name__ == "__main__":
    main()
