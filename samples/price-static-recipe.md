# Price-static recipe

Northvale Home static price cards for ops review. The `northvale price-static` command reads the JSON block below and writes PNG frames on disk. It does not upload, schedule, or publish to Instagram, Distro, Meta ads, or Shopify.

Editing the prose in this file does not change the render. Editing the `recipe` block does.

## Required inputs

- A SKU key that resolves through `data/short-links.json` (branded paths are the fallback).
- A display title and price from `data/catalog.json`, or `--title` and `--price` on the command.
- Optional compare-at price. A struck-through compare price is drawn only when it is higher than the display price. `null`, blank, and `0.00` are ignored.
- Optional product photo via `--photo path/to/still.png` (PNG or JPEG). The CLI does not download photos. Without a photo, the frame uses a monogram well labeled `PRODUCT STILL`.
- This recipe file, found at `samples/price-static-recipe.md` unless `--recipe` points somewhere else.

Product photos are not stored in this repo. Export a still from the public storefront yourself and pass it with `--photo`.

## Frames

Three IG-oriented canvases are emitted unless `--frame` selects one: square feed, 4:5 portrait, and 9:16 story. Default files land in `output/price-static/<sku>-<frame>.png`, which is gitignored.

```recipe
{
  "brand": "Northvale Home",
  "background": "#10241C",
  "panel": "#F4EFE4",
  "ink": "#10241C",
  "accent": "#C6A15B",
  "muted": "#5E6F66",
  "cream": "#F4EFE4",
  "well": "#E4DDD0",
  "price_prefix": "$",
  "frames": [
    {"id": "feed", "width": 1080, "height": 1080},
    {"id": "portrait", "width": 1080, "height": 1350},
    {"id": "story", "width": 1080, "height": 1920}
  ]
}
```
