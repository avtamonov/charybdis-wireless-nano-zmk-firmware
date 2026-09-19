"""Render the five everyday ZMK layers as one A4 landscape reference sheet.

The parsed keymap-drawer YAML remains the source of truth. Russian legends are
annotations for the host's standard Russian layout, not another firmware layer.
"""

from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
from xml.etree import ElementTree

import cairosvg
from PIL import Image
import yaml
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from keymap_legends import BASE_LATIN, BASE_RUSSIAN


LAYERS = ("Base", "Symbol", "Number", "Mouse", "Function")


def register_font() -> str:
    candidates = (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            pdfmetrics.registerFont(TTFont("KeymapUnicode", str(candidate)))
            return "KeymapUnicode"
    raise FileNotFoundError("Install a Cyrillic-capable font (DejaVu Sans or Arial)")


def legend(key: object) -> tuple[str, str, bool]:
    if isinstance(key, dict):
        tap = str(key.get("t", key.get("tap", "")))
        hold = str(key.get("h", key.get("hold", "")))
        transparent = key.get("type") == "trans"
        return ("" if transparent and tap == "▽" else tap), hold, transparent
    return str(key or ""), "", False


def short_label(value: str) -> str:
    aliases = {
        "&mkp MB1": "MB1", "&mkp MB2": "MB2", "&mkp MB3": "MB3",
        "&usb_dongle": "USB", "&bt_profile_1": "BT 1",
        "&bt_profile_2": "BT 2", "&bt_profile_3": "BT 3",
        "Ctl+Alt+ DEL": "C+A+Del", "Ctl+ BACK SPACE": "C+Bksp",
        "BACK SPACE": "Bksp", "PRINT SCREEN": "PrtSc",
    }
    return aliases.get(value, value.replace("Ctl+ ", "C+").replace("&mkp ", ""))


def fit_text(value: str, font: str, size: float, max_width: float) -> float:
    while size > 4.2 and pdfmetrics.stringWidth(value, font, size) > max_width:
        size -= 0.35
    return size


def draw_card(
    pdf: canvas.Canvas,
    name: str,
    keys: list,
    positions: list[dict],
    bounds: tuple[float, float, float, float],
    box: tuple[float, float, float, float],
    font: str,
) -> None:
    left, bottom, width, height = box
    pdf.setFillColor(colors.white)
    pdf.setStrokeColor(colors.HexColor("#CDD6E0"))
    pdf.roundRect(left, bottom, width, height, 8, fill=1, stroke=1)
    pdf.setFillColor(colors.HexColor("#23364F"))
    pdf.setFont(font, 10)
    pdf.drawString(left + 11, bottom + height - 16, name.upper())

    min_x, min_y, max_x, max_y = bounds
    scale = min((width - 20) / (max_x - min_x), (height - 34) / (max_y - min_y))
    key_w, key_h = scale * 0.91, scale * 0.85
    layout_width = (max_x - min_x) * scale
    x0 = left + (width - layout_width) / 2
    top = bottom + height - 27

    for index, (key, pos) in enumerate(zip(keys, positions, strict=True)):
        tap, hold, transparent = legend(key)
        x = x0 + (float(pos["x"]) - min_x) * scale
        y = top - (float(pos["y"]) - min_y) * scale - key_h
        pdf.setFillColor(colors.HexColor("#F4F7FA" if not transparent else "#FAFBFC"))
        pdf.setStrokeColor(colors.HexColor("#BCC9D7"))
        pdf.roundRect(x, y, key_w, key_h, 3, fill=1, stroke=1)

        tap = short_label(tap)
        if tap:
            pdf.setFillColor(colors.HexColor("#26374B" if not transparent else "#A4ADBA"))
            size = fit_text(tap, font, 8.0, key_w - 4)
            pdf.setFont(font, size)
            pdf.drawCentredString(x + key_w / 2, y + key_h * 0.45, tap)
        if hold:
            hold = short_label(hold)
            pdf.setFillColor(colors.HexColor("#66768B"))
            size = fit_text(hold, font, 5.2, key_w - 3)
            pdf.setFont(font, size)
            pdf.drawCentredString(x + key_w / 2, y + 2.7, hold)
        if name == "Base" and index < len(BASE_RUSSIAN):
            pdf.setFillColor(colors.HexColor("#126CA0"))
            pdf.setFont(font, 6.8)
            pdf.drawRightString(x + key_w - 2.5, y + key_h - 7.5, BASE_RUSSIAN[index])


def render(keymap_path: Path, layout_path: Path, combo_svg: Path, output_path: Path) -> None:
    with keymap_path.open(encoding="utf-8") as stream:
        keymap = yaml.safe_load(stream)
    with layout_path.open(encoding="utf-8") as stream:
        layout = json.load(stream)

    positions = [dict(pos) for pos in layout["layouts"]["default_transform"]["layout"]]
    # The five rotated thumb keys have identical unrotated x/y coordinates in
    # QMK info.json. Use their visible centers from the physical layout.
    thumb_centers = ((2.48, 3.125), (3.59, 3.27), (4.61, 3.70),
                     (7.39, 3.70), (8.41, 3.27))
    for pos, (x, y) in zip(positions[30:], thumb_centers, strict=True):
        pos["x"], pos["y"] = x, y
    layers = keymap["layers"]
    if len(positions) != 35:
        raise ValueError(f"Expected 35 physical positions, got {len(positions)}")
    for name in LAYERS:
        if name not in layers or len(layers[name]) != len(positions):
            raise ValueError(f"Layer {name} is missing or has the wrong key count")
    latin = tuple(legend(key)[0] for key in layers["Base"][:30])
    if latin != BASE_LATIN:
        raise ValueError("Base positions changed; review the Russian legend map")

    bounds = (
        min(float(pos["x"]) for pos in positions),
        min(float(pos["y"]) for pos in positions),
        max(float(pos["x"]) + float(pos.get("w", 1)) for pos in positions),
        max(float(pos["y"]) + float(pos.get("h", 1)) for pos in positions),
    )
    font = register_font()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page_w, page_h = landscape(A4)
    pdf = canvas.Canvas(str(output_path), pagesize=(page_w, page_h), pageCompression=1)
    pdf.setTitle("Charybdis - five layers, English and Russian")
    pdf.setFillColor(colors.HexColor("#F0F4F8"))
    pdf.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor("#1D3048"))
    pdf.setFont(font, 15)
    pdf.drawString(24, page_h - 27, "CHARYBDIS / КАРТА СЛОЁВ")
    pdf.setFillColor(colors.HexColor("#5C7088"))
    pdf.setFont(font, 8)
    pdf.drawRightString(page_w - 24, page_h - 24, "A4 · EN + RU · 5 слоёв")

    margin, gap = 24.0, 12.0
    content_top, content_bottom = page_h - 42, 39.0
    card_w = (page_w - margin * 2 - gap) / 2
    card_h = (content_top - content_bottom - gap * 2) / 3
    for index, name in enumerate(LAYERS):
        row, col = divmod(index, 2)
        box = (
            margin + col * (card_w + gap),
            content_top - (row + 1) * card_h - row * gap,
            card_w,
            card_h,
        )
        draw_card(pdf, name, layers[name], positions, bounds, box, font)

    # Embed the diagram produced by Keymap Drawer; do not draw combos here.
    notes_x = margin + card_w + gap + 12
    notes_y = content_top - 3 * card_h - 2 * gap + card_h - 20
    pdf.setFillColor(colors.HexColor("#23364F"))
    pdf.setFont(font, 10)
    pdf.drawString(notes_x, notes_y, "КОМБО")
    svg_size = ElementTree.parse(combo_svg).getroot().attrib["viewBox"].split()
    svg_w, svg_h = float(svg_size[2]), float(svg_size[3])
    png = cairosvg.svg2png(url=str(combo_svg), output_width=round(svg_w * 2))
    with Image.open(BytesIO(png)) as raster:
        scale = raster.width / svg_w
        # Omit the SVG's duplicate title and outer vertical whitespace.
        crop = raster.crop((0, round(svg_h * 0.13 * scale), raster.width,
                            round(svg_h * 0.89 * scale)))
        image_h = card_h - 35
        image_w = min(card_w - 24, image_h * crop.width / crop.height)
        image_h = image_w * crop.height / crop.width
        image_x = margin + card_w + gap + (card_w - image_w) / 2
        pdf.drawImage(ImageReader(crop), image_x, notes_y - 14 - image_h,
                      width=image_w, height=image_h, mask="auto")

    pdf.setFillColor(colors.HexColor("#61748B"))
    pdf.setFont(font, 7)
    pdf.drawString(margin, 20, "Источник: сгенерированная схема qwerty.yaml; стандартная русская раскладка ОС")
    pdf.drawRightString(page_w - margin, 20, "1 / 1")
    pdf.save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keymap", type=Path, required=True)
    parser.add_argument("--layout", type=Path, required=True)
    parser.add_argument("--combo-svg", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(args.keymap, args.layout, args.combo_svg, args.output)
