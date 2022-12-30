import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True, scope="function")
def clear_cache():
    """每次运行前都清除 cache"""
    from src.models import check_url

    check_url.cache_clear()


@pytest.fixture(autouse=True, scope="function")
def setup_globals(tmp_path: Path):
    import src.globals as g
    from src.models import Config, Settings

    adapter_path = tmp_path / "adapters.json"
    with adapter_path.open("w") as f:
        json.dump(
            [
                {
                    "module_name": "module_name1",
                    "project_link": "project_link1",
                    "name": "name",
                    "desc": "desc",
                    "author": "author",
                    "homepage": "https://v2.nonebot.dev",
                    "tags": [],
                    "is_official": False,
                },
            ],
            f,
        )
    bot_path = tmp_path / "bots.json"
    with bot_path.open("w") as f:
        json.dump(
            [
                {
                    "name": "name",
                    "desc": "desc",
                    "author": "author",
                    "homepage": "https://v2.nonebot.dev",
                    "tags": [],
                    "is_official": False,
                },
            ],
            f,
        )
    plugin_path = tmp_path / "plugins.json"
    with plugin_path.open("w") as f:
        json.dump(
            [
                {
                    "module_name": "module_name1",
                    "project_link": "project_link1",
                    "name": "name",
                    "desc": "desc",
                    "author": "author",
                    "homepage": "https://v2.nonebot.dev",
                    "tags": [],
                    "is_official": False,
                },
            ],
            f,
        )

    g.settings = Settings(
        input_token="token",  # type: ignore
        input_config=Config(
            base="master",
            adapter_path=adapter_path,
            bot_path=bot_path,
            plugin_path=plugin_path,
        ),
        github_repository="owner/repo",
        github_event_name="",
        github_event_path=tmp_path / "events.json",
        runner_debug=False,
    )

    g.skip_plugin_test = False
