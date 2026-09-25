"""Parse the price-static recipe markdown."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from northvale.resources import find_repo_file

_FENCE = re.compile(r"```(?:recipe|json)\s*\n(.*?)\n```", re.DOTALL)
_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
_FRAME_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class FrameSpec:
    id: str
    width: int
    height: int


@dataclass(frozen=True)
class Recipe:
    brand: str
    background: str
    panel: str
    ink: str
    accent: str
    muted: str
    cream: str
    well: str
    price_prefix: str
    frames: tuple[FrameSpec, ...]

    def frame(self, frame_id: str) -> FrameSpec:
        for spec in self.frames:
            if spec.id == frame_id:
                return spec
        known = ", ".join(spec.id for spec in self.frames)
        raise KeyError(f"Unknown frame {frame_id!r}. Recipe frames: {known}")


def recipe_path() -> Path:
    return find_repo_file("samples", "price-static-recipe.md")


def hex_rgb(value: str) -> tuple[int, int, int]:
    if not _HEX.match(value):
        raise ValueError(f"Color {value!r} must be a #RRGGBB hex string.")
    return (int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16))


def parse_recipe(path: Path | None = None) -> Recipe:
    recipe_file = path or recipe_path()
    text = recipe_file.read_text(encoding="utf-8")
    match = _FENCE.search(text)
    if match is None:
        raise ValueError(
            f"{recipe_file} has no ```recipe JSON block. "
            "Price-static reads canvas sizes and colors from that block."
        )
    try:
        raw = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Recipe JSON in {recipe_file.name} is invalid: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("Recipe JSON must be an object.")

    color_keys = ("background", "panel", "ink", "accent", "muted", "cream", "well")
    colors: dict[str, str] = {}
    for key in color_keys:
        value = raw.get(key)
        if not isinstance(value, str):
            raise ValueError(f"Recipe field {key} must be a #RRGGBB string.")
        hex_rgb(value)
        colors[key] = value.upper()

    brand = raw.get("brand")
    prefix = raw.get("price_prefix")
    if not isinstance(brand, str) or not brand.strip():
        raise ValueError("Recipe field brand must be a non-empty string.")
    if not isinstance(prefix, str) or not prefix:
        raise ValueError("Recipe field price_prefix must be a non-empty string.")

    frames_raw = raw.get("frames")
    if not isinstance(frames_raw, list) or not frames_raw:
        raise ValueError("Recipe field frames must be a non-empty list.")
    frames: list[FrameSpec] = []
    seen: set[str] = set()
    for item in frames_raw:
        if not isinstance(item, dict):
            raise ValueError("Each recipe frame must be an object with id, width, and height.")
        frame_id = item.get("id")
        width = item.get("width")
        height = item.get("height")
        if not isinstance(frame_id, str) or not _FRAME_ID.match(frame_id):
            raise ValueError(f"Frame id {frame_id!r} must be lowercase letters, numbers, and hyphens.")
        if frame_id in seen:
            raise ValueError(f"Duplicate frame id {frame_id!r}.")
        if not isinstance(width, int) or not isinstance(height, int) or width < 64 or height < 64:
            raise ValueError(f"Frame {frame_id} width and height must be integers >= 64.")
        seen.add(frame_id)
        frames.append(FrameSpec(id=frame_id, width=width, height=height))

    return Recipe(
        brand=brand.strip(),
        price_prefix=prefix,
        frames=tuple(frames),
        **colors,
    )
