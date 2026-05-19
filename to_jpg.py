#!/usr/bin/env python3
"""Convert generated HTML pages to JPG images."""
from pathlib import Path
from weasyprint import HTML, CSS
import subprocess, os
from PIL import Image

ROOT = Path(__file__).parent
SRC  = ROOT / "output"
TMP  = ROOT / "tmp_pdf"
TMP.mkdir(exist_ok=True)

css = CSS(string="@page { size: 1440px 7200px; margin: 0; } body { width: 1440px; }")

for html_path in sorted(SRC.glob("*.html")):
    stem = html_path.stem
    pdf = TMP / f"{stem}.pdf"
    HTML(str(html_path)).write_pdf(str(pdf), stylesheets=[css])
    # convert PDF first page to PNG then crop & save JPG
    subprocess.run(["pdftoppm", "-r", "85", "-png", "-f", "1", "-l", "1",
                    str(pdf), str(TMP / stem)], check=True)
    png_path = TMP / f"{stem}-1.png"
    if not png_path.exists():
        # naming may vary
        candidates = list(TMP.glob(f"{stem}-*.png"))
        if candidates:
            png_path = candidates[0]
    img = Image.open(png_path).convert("RGB")
    # auto-crop bottom whitespace
    bbox = img.getbbox()
    if bbox:
        # tight crop: scan from bottom for any non-white row
        w, h = img.size
        px = img.load()
        last = h - 1
        for y in range(h - 1, -1, -1):
            row_white = True
            for x in range(0, w, 20):
                r, g, b = px[x, y]
                if not (r > 245 and g > 245 and b > 245):
                    row_white = False
                    break
            if not row_white:
                last = y
                break
        img = img.crop((0, 0, w, min(h, last + 40)))
    jpg = SRC / f"{stem}.jpg"
    img.save(jpg, "JPEG", quality=85, optimize=True)
    print(f"  ✓ {jpg.name}  {img.size}")

# clean up
import shutil
shutil.rmtree(TMP, ignore_errors=True)
