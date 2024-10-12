from pathlib import Path
import pytest
from pytest_mock import MockerFixture
from nonebug.app import App


@pytest.fixture(autouse=True)
def _remove_mock(app: App, tmp_path: Path, mocker: MockerFixture):
    from src.providers.validation.models import PublishType

    bot_path = tmp_path / "bots.json"
    plugin_path = tmp_path / "plugins.json"
    adapter_path = tmp_path / "adapters.json"

    mocker.patch.dict(
        "src.plugins.github.plugins.remove.constants.PUBLISH_PATH",
        {
            PublishType.PLUGIN: plugin_path,
            PublishType.ADAPTER: adapter_path,
            PublishType.BOT: bot_path,
        },
    )
