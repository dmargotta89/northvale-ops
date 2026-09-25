"""SKU short-link and branded-path lookups."""

from __future__ import annotations

import json
from pathlib import Path

from northvale.resources import find_repo_file

_SKU_KEY = "sku key"


def short_links_path() -> Path:
    return find_repo_file("data", "short-links.json")


def branded_paths_path() -> Path:
    return find_repo_file("data", "branded-paths.json")


def catalog_path() -> Path:
    return find_repo_file("data", "catalog.json")


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path.name} is not valid JSON: {exc}") from exc


def short_link_map(path: Path | None = None) -> dict[str, str]:
    """Map SKU keys to absolute short URLs."""
    raw = load_json(path or short_links_path())
    if not isinstance(raw, dict):
        raise ValueError("short-links.json must be a JSON object of sku-key to URL.")
    links: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("short-links.json values must be URL strings.")
        url = value.strip()
        if not url.startswith(("https://", "http://")):
            raise ValueError(f"Short link for {key} must be an http(s) URL.")
        links[key] = url
    return links


def branded_path_table(path: Path | None = None) -> tuple[str, dict[str, str]]:
    """Return ``(base_url, {sku: path})`` from branded-paths.json."""
    raw = load_json(path or branded_paths_path())
    if not isinstance(raw, dict):
        raise ValueError("branded-paths.json must be a JSON object.")
    if "paths" in raw:
        paths = raw["paths"]
        base = raw.get("base_url", "")
        if not isinstance(base, str):
            raise ValueError("branded-paths.json base_url must be a string.")
    else:
        paths = raw
        base = ""
    if not isinstance(paths, dict):
        raise ValueError("branded-paths.json paths must be an object of sku-key to path.")
    cleaned: dict[str, str] = {}
    for key, value in paths.items():
        if not isinstance(key, str) or not isinstance(value, str) or not value.startswith("/"):
            raise ValueError("Each branded path must be a string starting with '/'.")
        cleaned[key] = value
    return base.rstrip("/"), cleaned


def list_sku_keys(
    links: dict[str, str] | None = None,
    paths: dict[str, str] | None = None,
) -> list[str]:
    """Sorted union of short-link keys and branded-path keys."""
    if links is None:
        links = short_link_map()
    if paths is None:
        _, paths = branded_path_table()
    return sorted(set(links) | set(paths))


def short_url(sku: str, links: dict[str, str] | None = None) -> str:
    """Resolve one SKU key to its short URL string."""
    table = short_link_map() if links is None else links
    if sku in table:
        return table[sku]
    base, paths = branded_path_table()
    if sku in paths and base:
        return f"{base}{paths[sku]}"
    known = ", ".join(list_sku_keys(table, paths)) or "(none)"
    raise KeyError(f"Unknown {_SKU_KEY} {sku!r}. Known keys: {known}")
