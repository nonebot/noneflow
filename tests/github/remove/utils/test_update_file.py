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
    from src.plugins.github.plugins.remove.validation import RemoveInfo
    from src.providers.utils import dump_json5
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
    dump_json5(tmp_path / "bots.json5", data)

    check_json_data(plugin_config.input_config.bot_path, data)

    remove_info = RemoveInfo(
        publish_type=PublishType.BOT,
        key="CoolQBot:https://github.com/he0119/CoolQBot",
        name="CoolQBot",
    )
    update_file(remove_info)

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
