#!/usr/bin/env python3
"""Social preview image (1200×630) for kolot-nodedim.netlify.app.

WhatsApp and Twitter draw this above the link title, then compress it hard.
The picture is the product: the name, and vote flows in the party colors
used on the site. The domain is left off — the platforms print it themselves.
"""

import os
import urllib.request

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1200, 630
SCALE = 4

INK = (22, 24, 29)          # #16181d
TITLE = (243, 245, 248)     # #f3f5f8
SUB = (214, 220, 230)

# Bright party colors from the live maps. Dark navy / brown drop out
# once WhatsApp recompresses the thumbnail, so the card uses the ones
# that still read at a few hundred pixels.
FLOWS = [
    ((37, 99, 235), 32),    # הליכוד
    ((6, 182, 212), 24),    # יש עתיד
    ((124, 58, 237), 16),   # המחנה הממלכתי
    ((219, 39, 119), 12),   # ישראל ביתנו
]

# Right-hand column is reordered so the flows cross, the way a transfer
# actually looks. Not a published result — a signature.
RIGHT_ORDER = [1, 0, 3, 2]

FONT_URL = "https://github.com/google/fonts/raw/refs/heads/main/ofl/heebo/Heebo%5Bwght%5D.ttf"
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Heebo[wght].ttf")


def ensure_font():
    if os.path.exists(FONT_PATH) and os.path.getsize(FONT_PATH) > 1000:
        return FONT_PATH
    os.makedirs(os.path.dirname(FONT_PATH), exist_ok=True)
    urllib.request.urlretrieve(FONT_URL, FONT_PATH)
    return FONT_PATH


def font(path, size, weight):
    face = ImageFont.truetype(path, size)
    face.set_variation_by_axes([weight])
    return face


def visual(text):
    """Pillow has no bidi. Pure Hebrew reverses into visual order."""
    return text[::-1]


def stack(weights, top, gap):
    ys = []
    y = top
    for w in weights:
        ys.append((y, y + w))
        y += w + gap
    return ys


def ribbon(draw, y0a, y0b, y1a, y1b, fill, pad, stub, samples=80):
    W = WIDTH * SCALE
    x0, x1 = stub, W - stub

    def edge(ya, yb):
        pts = [(0, ya)]
        pts.append((x0, ya))
        for i in range(1, samples):
            t = i / samples
            u = 1 - t
            # Horizontal tangents, same as a Sankey link.
            x = (u ** 3) * x0 + 3 * (u ** 2) * t * (x0 + (x1 - x0) * 0.45) \
                + 3 * u * (t ** 2) * (x0 + (x1 - x0) * 0.55) + (t ** 3) * x1
            y = (u ** 3) * ya + 3 * (u ** 2) * t * ya + 3 * u * (t ** 2) * yb + (t ** 3) * yb
            pts.append((x, y))
        pts.append((x1, yb))
        pts.append((W, yb))
        return pts

    top = edge(y0a - pad, y1a - pad)
    bot = edge(y0b + pad, y1b + pad)
    draw.polygon(top + bot[::-1], fill=fill)


def generate():
    path = ensure_font()
    img = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), INK)
    draw = ImageDraw.Draw(img)

    title_face = font(path, 112 * SCALE, 700)
    sub_face = font(path, 40 * SCALE, 500)

    title = visual("קולות נודדים")
    subtitle = visual("לאן עברו הקולות בין בחירות לכנסת")

    draw.text((WIDTH * SCALE / 2, 72 * SCALE), title, font=title_face, fill=TITLE, anchor="mt")
    draw.text((WIDTH * SCALE / 2, 206 * SCALE), subtitle, font=sub_face, fill=SUB, anchor="mt")

    gap = 16 * SCALE
    stub = 0
    flow_top = 292 * SCALE
    usable = (HEIGHT * SCALE - flow_top) - gap * (len(FLOWS) - 1)
    total = sum(w for _, w in FLOWS)
    weights = [w / total * usable for _, w in FLOWS]
    left = stack(weights, flow_top, gap)
    right = stack([weights[i] for i in RIGHT_ORDER], flow_top, gap)
    right_of = {party: right[pos] for pos, party in enumerate(RIGHT_ORDER)}

    # Smallest first, so the two big flows cross in front and stay readable.
    order = sorted(range(len(FLOWS)), key=lambda i: weights[i])
    halo = gap / 2
    for i in order:
        color = FLOWS[i][0]
        y0a, y0b = left[i]
        y1a, y1b = right_of[i]
        ribbon(draw, y0a, y0b, y1a, y1b, INK, halo, stub)
        ribbon(draw, y0a, y0b, y1a, y1b, color, 0, stub)

    out = img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site", "og-image.png")
    out.save(out_path, "PNG", optimize=True)
    print(f"Generated {out_path} ({WIDTH}x{HEIGHT}, {os.path.getsize(out_path)} bytes)")


if __name__ == "__main__":
    generate()
