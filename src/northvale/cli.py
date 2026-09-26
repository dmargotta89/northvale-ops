"""Northvale Home ops CLI."""

from __future__ import annotations

from pathlib import Path

import click

from northvale.links import list_sku_keys, short_url
from northvale.price_static import write_frames
from northvale.recipe import recipe_path


@click.group()
@click.version_option(package_name="northvale-ops")
def main() -> None:
    """Northvale Home ops helpers.

    Local commands for short links, SKU keys, and static price cards.
    Does not publish to Instagram, Distro, Meta, or Shopify.
    """


@main.command("short-link")
@click.argument("sku_key")
def short_link_cmd(sku_key: str) -> None:
    """Print the short URL for a SKU key."""
    try:
        click.echo(short_url(sku_key))
    except (KeyError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc


@main.command("sku-map")
def sku_map_cmd() -> None:
    """List SKU keys from short-links and branded paths."""
    try:
        keys = list_sku_keys()
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    for key in keys:
        click.echo(key)


@main.command("price-static")
@click.argument("sku_key")
@click.option("--frame", "frame_id", default=None, help="Render one recipe frame id instead of every frame.")
@click.option("--photo", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=None, help="Product photo (PNG or JPEG). Not fetched by this command.")
@click.option("--price", default=None, help="Override the catalog display price.")
@click.option("--compare-at", default=None, help="Override the catalog compare-at price.")
@click.option("--title", default=None, help="Override the catalog product title.")
@click.option(
    "--recipe",
    "recipe_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Recipe markdown. Defaults to samples/price-static-recipe.md.",
)
@click.option(
    "-o",
    "--output",
    "output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory, or a .png path when --frame selects one frame.",
)
def price_static_cmd(
    sku_key: str,
    frame_id: str | None,
    photo: Path | None,
    price: str | None,
    compare_at: str | None,
    title: str | None,
    recipe_file: Path | None,
    output: Path | None,
) -> None:
    """Generate price-static PNG frames for a SKU from the recipe."""
    single_file: Path | None = None
    out_dir = Path("output") / "price-static"
    if output is not None:
        if output.suffix.lower() == ".png":
            single_file = output
        else:
            out_dir = output
    try:
        if recipe_file is None:
            recipe_path()
        written = write_frames(
            sku_key,
            out_dir,
            frame_id=frame_id,
            photo=photo,
            price=price,
            compare_at=compare_at,
            title=title,
            recipe_file=recipe_file,
            single_file=single_file,
        )
    except (KeyError, ValueError, FileNotFoundError, OSError) as exc:
        raise click.ClickException(str(exc)) from exc
    for path in written:
        click.echo(path)
