from pathlib import Path

import pyjson5
import pytest
from pytest_mock import MockerFixture
from respx import MockRouter

from src.providers.constants import (
    REGISTRY_ADAPTERS_URL,
    REGISTRY_BOTS_URL,
    REGISTRY_DRIVERS_URL,
    REGISTRY_PLUGIN_CONFIG_URL,
    REGISTRY_PLUGINS_URL,
    REGISTRY_RESULTS_URL,
    STORE_ADAPTERS_URL,
    STORE_BOTS_URL,
    STORE_DRIVERS_URL,
    STORE_PLUGINS_URL,
)


def load_json(name: str) -> dict:
    # 商店为 json5 格式
    if name.startswith("store_"):
        name = f"{name}.json5"
    else:
        name = f"{name}.json"

    path = Path(__file__).parent / "store" / name
    with path.open("r", encoding="utf-8") as f:
        return pyjson5.load(f)  # type: ignore


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

    mocked_api.get(STORE_ADAPTERS_URL).respond(json=load_json("store_adapters"))
    mocked_api.get(STORE_BOTS_URL).respond(json=load_json("store_bots"))
    mocked_api.get(STORE_DRIVERS_URL).respond(json=load_json("store_drivers"))
    mocked_api.get(STORE_PLUGINS_URL).respond(json=load_json("store_plugins"))
    mocked_api.get(REGISTRY_ADAPTERS_URL).respond(json=load_json("registry_adapters"))
    mocked_api.get(REGISTRY_BOTS_URL).respond(json=load_json("registry_bots"))
    mocked_api.get(REGISTRY_DRIVERS_URL).respond(json=load_json("registry_drivers"))
    mocked_api.get(REGISTRY_PLUGINS_URL).respond(json=load_json("registry_plugins"))
    mocked_api.get(REGISTRY_RESULTS_URL).respond(json=load_json("registry_results"))
    mocked_api.get(REGISTRY_PLUGIN_CONFIG_URL).respond(json=load_json("plugin_configs"))

    return paths
