import json
from pathlib import Path

from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.github.utils import check_json_data


async def test_update_file(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    from src.plugins.github import plugin_config
    from src.plugins.github.plugins.remove.utils import update_file
    from src.providers.validation.models import PublishType

    data = [
        {
            "name": "CoolQBot",
            "desc": "基于 NoneBot2 的聊天机器人",
            "author_id": 1,
            "homepage": "https://github.com/he0119/CoolQBot",
            "tags": [],
            "is_official": False,
        },
        {
            "name": "CoolQBot2",
            "desc": "基于 NoneBot2 的聊天机器人",
            "author_id": 1,
            "homepage": "https://github.com/he0119/CoolQBot",
            "tags": [],
            "is_official": False,
        },
    ]
    with open(tmp_path / "bots.json", "w", encoding="utf-8") as f:
        json.dump(data, f)

    check_json_data(plugin_config.input_config.bot_path, data)

    update_file(PublishType.BOT, "CoolQBot:https://github.com/he0119/CoolQBot")

    check_json_data(
        plugin_config.input_config.bot_path,
        [
            {
                "name": "CoolQBot2",
                "desc": "基于 NoneBot2 的聊天机器人",
                "author_id": 1,
                "homepage": "https://github.com/he0119/CoolQBot",
                "tags": [],
                "is_official": False,
            }
        ],
    )
