from decimal import Decimal
from pathlib import Path

from click.testing import CliRunner
from PIL import Image

from northvale.cli import main
from northvale.price_static import resolve_offer, visible_compare, write_frames
from northvale.recipe import parse_recipe


def test_recipe_frames_and_rally_compare_price():
    recipe = parse_recipe()
    assert [spec.id for spec in recipe.frames] == ["feed", "portrait", "story"]
    offer = resolve_offer("rally-bands")
    assert offer.price == Decimal("28.99")
    assert visible_compare(offer) == Decimal("31.40")
    ab = resolve_offer("ab-wheel")
    assert ab.price == Decimal("29.99")
    assert visible_compare(ab) is None


def test_compare_at_below_price_is_not_shown():
    offer = resolve_offer("ab-wheel", compare_at="10.00")
    assert offer.compare_at == Decimal("10.00")
    assert visible_compare(offer) is None


def test_price_static_writes_recipe_sized_pngs(tmp_path: Path):
    written = write_frames("ab-wheel", tmp_path)
    recipe = parse_recipe()
    assert [path.name for path in written] == [f"ab-wheel-{spec.id}.png" for spec in recipe.frames]
    for path, spec in zip(written, recipe.frames, strict=True):
        with Image.open(path) as image:
            assert image.format == "PNG"
            assert image.size == (spec.width, spec.height)
            assert image.getpixel((0, 0)) == (198, 161, 91)


def test_price_static_composites_photo(tmp_path: Path):
    photo_path = tmp_path / "still.png"
    marker = (255, 0, 170)
    Image.new("RGB", (400, 400), marker).save(photo_path)
    out = tmp_path / "frames"
    written = write_frames("ab-wheel", out, frame_id="feed", photo=photo_path)
    assert len(written) == 1
    with Image.open(written[0]) as image:
        colors = image.getcolors(maxcolors=image.width * image.height)
        assert colors is not None
        assert any(color == marker for _count, color in colors)

    plain = write_frames("ab-wheel", tmp_path / "plain", frame_id="feed")
    with Image.open(plain[0]) as image:
        colors = image.getcolors(maxcolors=image.width * image.height)
        assert colors is not None
        assert all(color != marker for _count, color in colors)


def test_price_static_cli_single_frame(tmp_path: Path):
    destination = tmp_path / "ab-wheel-feed.png"
    result = CliRunner().invoke(
        main,
        ["price-static", "ab-wheel", "--frame", "feed", "-o", str(destination), "--price", "19.50"],
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == str(destination)
    assert destination.is_file()
    offer = resolve_offer("ab-wheel", price="19.50")
    assert offer.price == Decimal("19.50")


def test_price_static_unknown_sku_fails(tmp_path: Path):
    result = CliRunner().invoke(main, ["price-static", "missing-sku", "-o", str(tmp_path)])
    assert result.exit_code != 0
    assert "missing-sku" in f"{result.output}{result.stderr or ''}"
