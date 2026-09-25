# Northvale Home ops

Local helpers for the Northvale Home storefront: look up a short link, list SKU keys, and draw static price cards. This repo is an installable Python CLI. It does not talk to ad platforms or store admin APIs.

**NO secrets. NO Distro/ads/IG publish automation. NO Meta/Shopify write tokens in this repo.**

Display prices and product URLs in `data/` are public storefront facts for local creative ops. Do not add access tokens, app secrets, session cookies, or publish scripts here.

## Install

Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

The editable install exposes the console script `northvale`.

```bash
northvale --help
pytest
```

## CLI

`northvale --help` lists `short-link`, `sku-map`, and `price-static`.

```bash
northvale short-link ab-wheel
northvale sku-map
northvale price-static ab-wheel
northvale price-static ab-wheel --frame portrait --photo ./still.png -o output/price-static
```

`short-link` prints one URL and nothing else. `ab-wheel` prints:

```text
https://nhfqt2-t6.myshopify.com/products/automatic-rebound-abdominal-wheel
```

`sku-map` prints the sorted union of SKU keys from `data/short-links.json` and `data/branded-paths.json`, one key per line.

`price-static` writes PNG frames. It reads canvas sizes and colors from `samples/price-static-recipe.md`. Default output is `output/price-static/<sku>-<frame>.png` (feed 1080×1080, portrait 1080×1350, story 1080×1920). Pass `-o` with a directory, or a `.png` path together with `--frame`, to choose the destination. `--price`, `--compare-at`, and `--title` override the catalog for that run. A compare-at price is drawn struck through only when it is higher than the display price.

### Price-static inputs

The generator does not download product photography. Pass a PNG or JPEG with `--photo` when you want the still composited into the card. Without `--photo`, the frame still renders: brand, title, price, SKU chip, short URL, and a monogram well marked `PRODUCT STILL`.

Required for a full card:

- SKU key in `data/short-links.json` (or a branded path, used when the short-link table has no entry)
- Title and price in `data/catalog.json`, unless you pass `--title` and `--price`
- Optional photo file on disk
- Recipe file `samples/price-static-recipe.md` (override with `--recipe`)

Generated images under `output/` are gitignored.

## Data file layout

| Path | Role |
| --- | --- |
| `data/short-links.json` | Object of SKU key → absolute `http(s)` short URL. This is what `short-link` prints. |
| `data/branded-paths.json` | `base_url` plus `paths` of SKU key → storefront path starting with `/`. Keys are included in `sku-map`. If a key is missing from short-links, the CLI joins `base_url` and the path. |
| `data/catalog.json` | Object of SKU key → `title`, `price`, and `compare_at_price` (`null` when there is no higher compare price). Used only by `price-static`. |
| `samples/price-static-recipe.md` | Human notes plus one fenced `recipe` JSON block (brand, colors, `price_prefix`, frame id/width/height). The renderer uses that block. |

SKU keys in the seed data are ops nicknames (`ab-wheel`, `sliding-board`, `yoga-set`, `rally-bands`, `shake-cup`, `waist-trainer`, `curveboost`), not the raw Shopify variant SKUs.

## Tests

```bash
pytest
```

Short-link lookup, SKU map, recipe frame sizes, and price-static PNG output are covered. Price-static tests check dimensions, the recipe accent bar, and that `--photo` pixels are composited into the frame.
