import subprocess
import sys
from pathlib import Path

from click.testing import CliRunner

from northvale.cli import main
from northvale.links import branded_path_table, short_link_map, short_url


def test_ab_wheel_short_link_is_https_url():
    url = short_url("ab-wheel")
    assert url == "https://nhfqt2-t6.myshopify.com/products/automatic-rebound-abdominal-wheel"
    assert " " not in url


def test_short_link_command_prints_url_only():
    result = CliRunner().invoke(main, ["short-link", "ab-wheel"])
    assert result.exit_code == 0
    assert result.output == "https://nhfqt2-t6.myshopify.com/products/automatic-rebound-abdominal-wheel\n"


def _combined(result) -> str:
    return f"{result.output}{result.stderr or ''}"


def test_unknown_sku_is_an_error():
    result = CliRunner().invoke(main, ["short-link", "missing-sku"])
    assert result.exit_code != 0
    assert "missing-sku" in _combined(result)


def test_short_links_match_branded_paths():
    links = short_link_map()
    base, paths = branded_path_table()
    assert base.startswith("https://")
    assert set(links) == set(paths)
    for key, path in paths.items():
        assert links[key] == f"{base}{path}"


def test_installed_console_script_prints_ab_wheel():
    executable = Path(sys.executable).with_name("northvale")
    assert executable.is_file(), "northvale console script is not next to this interpreter; pip install -e ."
    completed = subprocess.run(
        [executable, "short-link", "ab-wheel"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert (
        completed.stdout.strip()
        == "https://nhfqt2-t6.myshopify.com/products/automatic-rebound-abdominal-wheel"
    )
    help_run = subprocess.run(
        [executable, "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    for name in ("short-link", "sku-map", "price-static"):
        assert name in help_run.stdout
