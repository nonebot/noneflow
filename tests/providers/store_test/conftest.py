from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from respx import MockRouter


@pytest.fixture
def mocked_store_data(
    tmp_path: Path, mocker: MockerFixture, mocked_api: MockRouter
) -> dict[str, Path]:
    plugin_test_path = tmp_path / "plugin_test"
    plugin_test_path.mkdir()

    paths = {
        "adapters": plugin_test_path / "adapters.json",
        "bots": plugin_test_path / "bots.json",
        "drivers": plugin_test_path / "drivers.json",
        "plugins": plugin_test_path / "plugins.json",
        "results": plugin_test_path / "results.json",
        "plugin_configs": plugin_test_path / "plugin_configs.json",
    }

    mocker.patch("src.providers.store_test.store.RESULTS_PATH", paths["results"])
    mocker.patch("src.providers.store_test.store.ADAPTERS_PATH", paths["adapters"])
    mocker.patch("src.providers.store_test.store.BOTS_PATH", paths["bots"])
    mocker.patch("src.providers.store_test.store.DRIVERS_PATH", paths["drivers"])
    mocker.patch("src.providers.store_test.store.PLUGINS_PATH", paths["plugins"])
    mocker.patch(
        "src.providers.store_test.store.PLUGIN_CONFIG_PATH", paths["plugin_configs"]
    )

    return paths
