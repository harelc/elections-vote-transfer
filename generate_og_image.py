#!/usr/bin/env python3
"""Generate OG social preview image (1200x630) for kolot-nodedim.netlify.app"""

from PIL import Image, ImageDraw, ImageFont
import os

WIDTH, HEIGHT = 1200, 630
BG_COLOR = (30, 41, 59)       # #1e293b
TEXT_WHITE = (248, 250, 252)   # #f8fafc
TEXT_MUTED = (148, 163, 184)   # #94a3b8
ACCENT = (59, 130, 246)       # #3b82f6

def generate():
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Draw accent line at top
    draw.rectangle([0, 0, WIDTH, 6], fill=ACCENT)

    # Draw ballot box emoji/icon area (simple geometric representation)
    box_x, box_y = 540, 120
    box_w, box_h = 120, 100
    # Box body
    draw.rectangle([box_x, box_y + 20, box_x + box_w, box_y + box_h], fill=(51, 65, 85), outline=TEXT_MUTED, width=2)
    # Box lid
    draw.rectangle([box_x - 5, box_y + 10, box_x + box_w + 5, box_y + 30], fill=(51, 65, 85), outline=TEXT_MUTED, width=2)
    # Slot
    draw.rectangle([box_x + 35, box_y + 14, box_x + 85, box_y + 22], fill=BG_COLOR)
    # Paper coming out of slot
    draw.rectangle([box_x + 45, box_y - 10, box_x + 75, box_y + 18], fill=TEXT_WHITE)

    # Title text
    try:
        # Try system Hebrew font
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Hebrew Bold.ttc", 72)
    except (OSError, IOError):
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        except (OSError, IOError):
            title_font = ImageFont.load_default()

    try:
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Hebrew.ttc", 32)
    except (OSError, IOError):
        try:
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except (OSError, IOError):
            subtitle_font = ImageFont.load_default()

    try:
        url_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Hebrew.ttc", 24)
    except (OSError, IOError):
        try:
            url_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except (OSError, IOError):
            url_font = ImageFont.load_default()

    # Title: קולות נודדים
    title = "קולות נודדים"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((WIDTH - tw) / 2, 260), title, fill=TEXT_WHITE, font=title_font)

    # Subtitle
    subtitle = "Israeli Election Data Explorer"
    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sw = bbox[2] - bbox[0]
    draw.text(((WIDTH - sw) / 2, 360), subtitle, fill=TEXT_MUTED, font=subtitle_font)

    # Subtitle Hebrew
    subtitle_he = "ניתוח אינטראקטיבי של נתוני בחירות לכנסת"
    bbox = draw.textbbox((0, 0), subtitle_he, font=subtitle_font)
    shw = bbox[2] - bbox[0]
    draw.text(((WIDTH - shw) / 2, 410), subtitle_he, fill=TEXT_MUTED, font=subtitle_font)

    # URL at bottom
    url_text = "kolot-nodedim.netlify.app"
    bbox = draw.textbbox((0, 0), url_text, font=url_font)
    uw = bbox[2] - bbox[0]
    draw.text(((WIDTH - uw) / 2, 550), url_text, fill=ACCENT, font=url_font)

    # Draw bottom accent line
    draw.rectangle([0, HEIGHT - 6, WIDTH, HEIGHT], fill=ACCENT)

    out_path = os.path.join(os.path.dirname(__file__), 'site', 'og-image.png')
    img.save(out_path, 'PNG')
    print(f"Generated {out_path} ({WIDTH}x{HEIGHT})")

if __name__ == '__main__':
    generate()
