from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
PNG_PATH = ROOT / "HEIC-Drop-Converter.png"
ICO_PATH = ROOT / "HEIC-Drop-Converter.ico"
SIZE = 1024


def font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def build_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (5, 35, 95, 255))
    d = ImageDraw.Draw(img)

    # Outer neon frame.
    for width, alpha in ((42, 40), (28, 85), (16, 180), (8, 255)):
        d.rounded_rectangle((35, 35, 989, 989), radius=115, outline=(20, 151, 255, alpha), width=width)

    # Rear purple photo card.
    d.rounded_rectangle((315, 185, 875, 800), radius=75, fill=(126, 75, 255, 255), outline=(235, 241, 255, 255), width=36)
    d.polygon([(360, 690), (520, 490), (650, 610), (760, 455), (845, 565), (845, 760), (360, 760)], fill=(85, 54, 224, 255))

    # Front blue photo card.
    d.rounded_rectangle((120, 325, 700, 875), radius=75, fill=(28, 166, 242, 255), outline=(239, 247, 255, 255), width=36)
    d.ellipse((465, 390, 565, 490), fill=(255, 198, 27, 255))
    d.polygon([(160, 775), (350, 515), (520, 690), (610, 585), (675, 650), (675, 830), (160, 830)], fill=(5, 45, 111, 255))

    # HEIC badge.
    badge = (525, 660, 930, 860)
    d.rounded_rectangle(badge, radius=80, fill=(3, 43, 111, 255), outline=(27, 151, 255, 255), width=18)

    # Draw HEIC as vector strokes so the badge is identical even when fonts differ.
    stroke = 22
    white = (255, 255, 255, 255)
    y1, y2 = 706, 813
    x = 595
    letter_w = 58
    gap = 28

    # H
    d.line((x, y1, x, y2), fill=white, width=stroke)
    d.line((x + letter_w, y1, x + letter_w, y2), fill=white, width=stroke)
    d.line((x, (y1 + y2) // 2, x + letter_w, (y1 + y2) // 2), fill=white, width=stroke)
    x += letter_w + gap

    # E
    d.line((x, y1, x, y2), fill=white, width=stroke)
    d.line((x, y1, x + letter_w, y1), fill=white, width=stroke)
    d.line((x, (y1 + y2) // 2, x + letter_w - 8, (y1 + y2) // 2), fill=white, width=stroke)
    d.line((x, y2, x + letter_w, y2), fill=white, width=stroke)
    x += letter_w + gap

    # I
    d.line((x, y1, x + letter_w, y1), fill=white, width=stroke)
    d.line((x + letter_w // 2, y1, x + letter_w // 2, y2), fill=white, width=stroke)
    d.line((x, y2, x + letter_w, y2), fill=white, width=stroke)
    x += letter_w + gap

    # C
    d.arc((x - 5, y1 - 2, x + letter_w + 18, y2 + 2), start=50, end=310, fill=white, width=stroke)

    img.save(PNG_PATH, optimize=True, compress_level=9)

    # Build a multi-resolution Windows icon from the generated artwork.
    img.save(
        ICO_PATH,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        bitmap_format="png",
    )

    print(f"Created: {PNG_PATH.name}")
    print(f"Created: {ICO_PATH.name}")


if __name__ == "__main__":
    build_icon()
