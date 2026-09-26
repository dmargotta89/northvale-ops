"""Draw recipe-driven static price cards. Does not publish anywhere."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from northvale.links import catalog_path, load_json, short_url
from northvale.recipe import FrameSpec, Recipe, hex_rgb, parse_recipe

_FONT_CANDIDATES = {
    False: (
        Path("/usr/share/fonts/truetype/macos/Inter-Regular.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ),
    True: (
        Path("/usr/share/fonts/truetype/macos/Inter-Bold.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ),
}


@dataclass(frozen=True)
class Offer:
    sku: str
    title: str
    price: Decimal
    compare_at: Decimal | None
    short_url: str


def parse_money(value: str, *, field: str) -> Decimal:
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field} must be a decimal amount, got {value!r}.") from exc
    if amount < 0:
        raise ValueError(f"{field} cannot be negative.")
    return amount.quantize(Decimal("0.01"))


def visible_compare(offer: Offer) -> Decimal | None:
    """Show a struck-through compare-at price only when it is higher than the price."""
    if offer.compare_at is not None and offer.compare_at > offer.price:
        return offer.compare_at
    return None


def resolve_offer(
    sku: str,
    *,
    price: str | None = None,
    compare_at: str | None = None,
    title: str | None = None,
) -> Offer:
    raw = load_json(catalog_path())
    if not isinstance(raw, dict):
        raise ValueError("catalog.json must be a JSON object keyed by SKU.")
    entry = raw.get(sku, {})
    if entry is None:
        entry = {}
    if not isinstance(entry, dict):
        raise ValueError(f"catalog.json entry for {sku} must be an object.")

    resolved_title = title if title is not None else entry.get("title")
    if not isinstance(resolved_title, str) or not resolved_title.strip():
        raise ValueError(f"No title for {sku}. Pass --title or add the SKU to data/catalog.json.")

    price_source = price if price is not None else entry.get("price")
    if price_source is None:
        raise ValueError(f"No price for {sku}. Pass --price or add the SKU to data/catalog.json.")
    resolved_price = parse_money(str(price_source), field="price")

    if compare_at is not None:
        compare_source: object = compare_at
    else:
        compare_source = entry.get("compare_at_price")
    resolved_compare: Decimal | None
    if compare_source is None or str(compare_source).strip() in {"", "0", "0.00"}:
        resolved_compare = None
    else:
        resolved_compare = parse_money(str(compare_source), field="compare_at_price")

    return Offer(
        sku=sku,
        title=resolved_title.strip(),
        price=resolved_price,
        compare_at=resolved_compare,
        short_url=short_url(sku),
    )


def load_font(size: int, *, bold: bool) -> ImageFont.ImageFont:
    size = max(12, size)
    for candidate in _FONT_CANDIDATES[bold]:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _text_height(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[3] - box[1]


def _open_photo(path: Path) -> Image.Image:
    with Image.open(path) as handle:
        transposed = ImageOps.exif_transpose(handle)
        if transposed is None:
            raise ValueError(f"Could not read photo {path}.")
        return transposed.convert("RGB")


def render_frame(recipe: Recipe, frame: FrameSpec, offer: Offer, photo: Image.Image | None) -> Image.Image:
    width, height = frame.width, frame.height
    background = hex_rgb(recipe.background)
    panel = hex_rgb(recipe.panel)
    ink = hex_rgb(recipe.ink)
    accent = hex_rgb(recipe.accent)
    muted = hex_rgb(recipe.muted)
    cream = hex_rgb(recipe.cream)
    well = hex_rgb(recipe.well)

    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)
    bar = max(8, height // 90)
    draw.rectangle((0, 0, width, bar), fill=accent)
    draw.rectangle((0, height - bar, width, height), fill=accent)

    margin = max(24, int(width * 0.055))
    card = (margin, margin + bar, width - margin, height - margin - bar)
    radius = max(16, width // 30)
    draw.rounded_rectangle(card, radius=radius, fill=panel)

    pad = max(20, int(width * 0.045))
    left = card[0] + pad
    right = card[2] - pad
    content_w = right - left
    top = card[1] + pad
    bottom = card[3] - pad

    brand_font = load_font(max(18, width // 42), bold=True)
    kicker_font = load_font(max(14, width // 48), bold=True)
    title_font = load_font(max(28, width // 18), bold=True)
    price_font = load_font(max(48, width // 8), bold=True)
    compare_font = load_font(max(18, width // 28), bold=False)
    meta_font = load_font(max(16, width // 40), bold=False)
    url_font = load_font(max(14, width // 46), bold=False)
    gap = max(8, width // 60)

    y = top
    brand = recipe.brand.upper()
    draw.text((left, y), brand, font=brand_font, fill=accent)
    y += _text_height(draw, brand, brand_font) + gap

    kicker = "TODAY'S PRICE"
    draw.text((left, y), kicker, font=kicker_font, fill=muted)
    y += _text_height(draw, kicker, kicker_font) + gap

    for line in wrap_text(draw, offer.title, title_font, content_w)[:3]:
        draw.text((left, y), line, font=title_font, fill=ink)
        y += _text_height(draw, line, title_font) + 4
    y += gap

    price_text = f"{recipe.price_prefix}{offer.price:.2f}"
    price_h = _text_height(draw, price_text, price_font)
    chip = f"SKU  {offer.sku}"
    chip_h = _text_height(draw, chip, meta_font) + pad // 2
    url_lines = wrap_text(draw, offer.short_url, url_font, content_w)[:2]
    url_h = sum(_text_height(draw, line, url_font) + 2 for line in url_lines)
    cluster_h = price_h + gap + chip_h + gap + url_h
    cluster_top = bottom - cluster_h
    photo_bottom = cluster_top - gap
    available = max(48, photo_bottom - y)
    if photo is None:
        side = min(content_w, available, max(160, int(width * 0.42)))
        well_left = left + (content_w - side) // 2
        photo_box = (well_left, y, well_left + side, y + side)
    else:
        photo_box = (left, y, right, y + available)
    _draw_photo_well(image, photo_box, photo, offer, ink, accent, muted, well)

    draw = ImageDraw.Draw(image)
    rule_y = cluster_top - max(6, gap // 2)
    draw.line((left, rule_y, left + content_w // 4, rule_y), fill=accent, width=max(3, width // 240))

    cursor = cluster_top
    draw.text((left, cursor), price_text, font=price_font, fill=ink)
    compare = visible_compare(offer)
    if compare is not None:
        compare_text = f"{recipe.price_prefix}{compare:.2f}"
        compare_x = left + int(draw.textlength(price_text, font=price_font)) + gap
        compare_h = _text_height(draw, compare_text, compare_font)
        compare_y = cursor + max(0, (price_h - compare_h) // 2)
        draw.text((compare_x, compare_y), compare_text, font=compare_font, fill=muted)
        compare_w = draw.textlength(compare_text, font=compare_font)
        strike = compare_y + compare_h // 2
        draw.line(
            (compare_x, strike, compare_x + compare_w, strike),
            fill=accent,
            width=max(2, width // 400),
        )
    cursor += price_h + gap

    chip_w = int(draw.textlength(chip, font=meta_font)) + pad
    draw.rounded_rectangle((left, cursor, left + chip_w, cursor + chip_h), radius=chip_h // 2, fill=background)
    chip_text_h = _text_height(draw, chip, meta_font)
    draw.text(
        (left + pad // 2, cursor + (chip_h - chip_text_h) / 2),
        chip,
        font=meta_font,
        fill=cream,
    )
    cursor += chip_h + gap
    for line in url_lines:
        draw.text((left, cursor), line, font=url_font, fill=muted)
        cursor += _text_height(draw, line, url_font) + 2
    return image


def _draw_photo_well(
    image: Image.Image,
    box: tuple[int, int, int, int],
    photo: Image.Image | None,
    offer: Offer,
    ink: tuple[int, int, int],
    accent: tuple[int, int, int],
    muted: tuple[int, int, int],
    well: tuple[int, int, int],
) -> None:
    draw = ImageDraw.Draw(image)
    radius = max(12, (box[2] - box[0]) // 24)
    draw.rounded_rectangle(box, radius=radius, fill=well)
    if photo is not None:
        fitted = photo.copy()
        inset = 12
        max_size = (max(1, box[2] - box[0] - inset * 2), max(1, box[3] - box[1] - inset * 2))
        fitted.thumbnail(max_size, Image.Resampling.LANCZOS)
        paste_x = box[0] + (box[2] - box[0] - fitted.width) // 2
        paste_y = box[1] + (box[3] - box[1] - fitted.height) // 2
        image.paste(fitted, (paste_x, paste_y))
        return

    draw = ImageDraw.Draw(image)
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    radius_px = max(24, min(box[2] - box[0], box[3] - box[1]) // 6)
    draw.ellipse(
        (cx - radius_px, cy - radius_px, cx + radius_px, cy + radius_px),
        outline=accent,
        width=max(4, radius_px // 14),
    )
    letter = (offer.title[:1] or offer.sku[:1]).upper()
    letter_font = load_font(max(18, radius_px), bold=True)
    bbox = draw.textbbox((0, 0), letter, font=letter_font)
    draw.text(
        (cx - (bbox[2] - bbox[0]) / 2 - bbox[0], cy - (bbox[3] - bbox[1]) / 2 - bbox[1]),
        letter,
        font=letter_font,
        fill=ink,
    )
    caption = "PRODUCT STILL"
    caption_font = load_font(max(12, (box[2] - box[0]) // 28), bold=True)
    caption_w = draw.textlength(caption, font=caption_font)
    caption_y = min(box[3] - 36, cy + radius_px + 16)
    draw.text((cx - caption_w / 2, caption_y), caption, font=caption_font, fill=muted)


def select_frames(recipe: Recipe, frame_id: str | None) -> tuple[FrameSpec, ...]:
    if frame_id is None:
        return recipe.frames
    return (recipe.frame(frame_id),)


def write_frames(
    sku: str,
    out_dir: Path,
    *,
    frame_id: str | None = None,
    photo: Path | None = None,
    price: str | None = None,
    compare_at: str | None = None,
    title: str | None = None,
    recipe_file: Path | None = None,
    single_file: Path | None = None,
) -> list[Path]:
    """Render price-static PNG frames for one SKU and return the written paths."""
    recipe = parse_recipe(recipe_file)
    frames = select_frames(recipe, frame_id)
    if single_file is not None and len(frames) != 1:
        ids = ", ".join(spec.id for spec in frames)
        raise ValueError(f"A single PNG path needs --frame. Available frames: {ids}")
    offer = resolve_offer(sku, price=price, compare_at=compare_at, title=title)
    opened = _open_photo(photo) if photo is not None else None
    written: list[Path] = []
    try:
        for spec in frames:
            rendered = render_frame(recipe, spec, offer, opened)
            if single_file is not None:
                destination = single_file
            else:
                destination = out_dir / f"{sku}-{spec.id}.png"
            destination.parent.mkdir(parents=True, exist_ok=True)
            rendered.save(destination, format="PNG")
            written.append(destination)
    finally:
        if opened is not None:
            opened.close()
    return written
