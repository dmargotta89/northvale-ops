from click.testing import CliRunner

from northvale.cli import main
from northvale.links import list_sku_keys


def test_sku_map_lists_sorted_union():
    keys = list_sku_keys()
    assert "ab-wheel" in keys
    assert keys == sorted(keys)
    result = CliRunner().invoke(main, ["sku-map"])
    assert result.exit_code == 0
    assert result.output.splitlines() == keys


def test_help_lists_ops_commands():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    for name in ("short-link", "sku-map", "price-static"):
        assert name in result.output
