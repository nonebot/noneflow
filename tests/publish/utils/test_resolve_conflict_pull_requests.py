# ruff: noqa: ASYNC101
import json
from pathlib import Path
from typing import Any, cast

from nonebot import get_adapter
from nonebot.adapters.github import Adapter, GitHubBot
from nonebot.adapters.github.config import GitHubApp
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter


def check_json_data(file: Path, data: Any) -> None:
    with open(file, encoding="utf-8") as f:
        assert json.load(f) == data


async def test_resolve_conflict_pull_requests_adapter(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    from src.plugins.github import plugin_config
    from src.plugins.github.plugins.publish.utils import resolve_conflict_pull_requests

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_result = mocker.MagicMock()
    mock_subprocess_run.side_effect = lambda *args, **kwargs: mock_result

    mock_label = mocker.MagicMock()
    mock_label.name = "Adapter"

    mock_pull = mocker.MagicMock()
    mock_pull.head.ref = "publish/issue1"
    mock_pull.draft = False
    mock_pull.labels = [mock_label]

    with open(tmp_path / "adapters.json", "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "module_name": "nonebot.adapters.onebot.v11",
                    "project_link": "nonebot-adapter-onebot",
                    "name": "OneBot V11",
                    "desc": "OneBot V11 协议",
                    "author": "yanyongyu",
                    "homepage": "https://onebot.adapters.nonebot.dev/",
                    "tags": [],
                    "is_official": True,
                }
            ],
            f,
            ensure_ascii=False,
        )

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

        await resolve_conflict_pull_requests([mock_pull])

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "checkout", "publish/issue1"], check=True, capture_output=True
            ),
            mocker.call(["git", "checkout", "master"], check=True, capture_output=True),
            mocker.call(
                ["git", "switch", "-C", "publish/issue1"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "config", "--global", "user.name", "yanyongyu"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                [
                    "git",
                    "config",
                    "--global",
                    "user.email",
                    "yanyongyu@users.noreply.github.com",
                ],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "add", "-A"], check=True, capture_output=True),
            mocker.call(
                ["git", "commit", "-m", ":beers: publish adapter OneBot V11 (#1)"],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "diff", "origin/publish/issue1", "publish/issue1"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "push", "origin", "publish/issue1", "-f"],
                check=True,
                capture_output=True,
            ),
        ]  # type: ignore
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.adapter_path,
        [
            {
                "module_name": "nonebot.adapters.onebot.v11",
                "project_link": "nonebot-adapter-onebot",
                "name": "OneBot V11",
                "desc": "OneBot V11 协议",
                "author": "yanyongyu",
                "homepage": "https://onebot.adapters.nonebot.dev/",
                "tags": [],
                "is_official": True,
            },
            {
                "module_name": "nonebot.adapters.onebot.v11",
                "project_link": "nonebot-adapter-onebot",
                "name": "OneBot V11",
                "desc": "OneBot V11 协议",
                "author": "yanyongyu",
                "homepage": "https://onebot.adapters.nonebot.dev/",
                "tags": [],
                "is_official": True,
            },
        ],
    )

    assert not mocked_api["homepage"].called


async def test_resolve_conflict_pull_requests_bot(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    from src.plugins.github import plugin_config
    from src.plugins.github.plugins.publish.utils import resolve_conflict_pull_requests

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_result = mocker.MagicMock()
    mock_subprocess_run.side_effect = lambda *args, **kwargs: mock_result

    mock_label = mocker.MagicMock()
    mock_label.name = "Bot"

    mock_pull = mocker.MagicMock()
    mock_pull.head.ref = "publish/issue1"
    mock_pull.draft = False
    mock_pull.labels = [mock_label]

    with open(tmp_path / "bots.json", "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "name": "CoolQBot",
                    "desc": "基于 NoneBot2 的聊天机器人",
                    "author": "he0119",
                    "homepage": "https://github.com/he0119/CoolQBot",
                    "tags": [],
                    "is_official": False,
                }
            ],
            f,
            ensure_ascii=False,
        )

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

        await resolve_conflict_pull_requests([mock_pull])

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "checkout", "publish/issue1"], check=True, capture_output=True
            ),
            mocker.call(["git", "checkout", "master"], check=True, capture_output=True),
            mocker.call(
                ["git", "switch", "-C", "publish/issue1"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "config", "--global", "user.name", "he0119"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                [
                    "git",
                    "config",
                    "--global",
                    "user.email",
                    "he0119@users.noreply.github.com",
                ],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "add", "-A"], check=True, capture_output=True),
            mocker.call(
                ["git", "commit", "-m", ":beers: publish bot CoolQBot (#1)"],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "diff", "origin/publish/issue1", "publish/issue1"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "push", "origin", "publish/issue1", "-f"],
                check=True,
                capture_output=True,
            ),
        ]  # type: ignore
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.bot_path,
        [
            {
                "name": "CoolQBot",
                "desc": "基于 NoneBot2 的聊天机器人",
                "author": "he0119",
                "homepage": "https://github.com/he0119/CoolQBot",
                "tags": [],
                "is_official": False,
            },
            {
                "name": "CoolQBot",
                "desc": "基于 NoneBot2 的聊天机器人",
                "author": "he0119",
                "homepage": "https://github.com/he0119/CoolQBot",
                "tags": [],
                "is_official": False,
            },
        ],
    )

    assert not mocked_api["homepage"].called


async def test_resolve_conflict_pull_requests_plugin(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    from src.plugins.github import plugin_config
    from src.plugins.github.plugins.publish.utils import resolve_conflict_pull_requests

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_result = mocker.MagicMock()
    mock_subprocess_run.side_effect = lambda *args, **kwargs: mock_result

    mock_label = mocker.MagicMock()
    mock_label.name = "Plugin"

    mock_pull = mocker.MagicMock()
    mock_pull.head.ref = "publish/issue1"
    mock_pull.draft = False
    mock_pull.labels = [mock_label]
    mock_pull.title = "Plugin: 帮助"

    with open(tmp_path / "plugins.json", "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "module_name": "nonebot_plugin_treehelp",
                    "project_link": "nonebot-plugin-treehelp",
                    "author": "he0119",
                    "tags": [],
                    "is_official": True,
                }
            ],
            f,
            ensure_ascii=False,
        )

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

        await resolve_conflict_pull_requests([mock_pull])

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "checkout", "publish/issue1"], check=True, capture_output=True
            ),
            mocker.call(["git", "checkout", "master"], check=True, capture_output=True),
            mocker.call(
                ["git", "switch", "-C", "publish/issue1"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "config", "--global", "user.name", "he0119"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                [
                    "git",
                    "config",
                    "--global",
                    "user.email",
                    "he0119@users.noreply.github.com",
                ],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "add", "-A"], check=True, capture_output=True),
            mocker.call(
                ["git", "commit", "-m", ":beers: publish plugin 帮助 (#1)"],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "diff", "origin/publish/issue1", "publish/issue1"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "push", "origin", "publish/issue1", "-f"],
                check=True,
                capture_output=True,
            ),
        ]  # type: ignore
    )

    # 检查文件是否正确
    # 因为没有进行 git 操作，所有会有两个插件信息
    check_json_data(
        plugin_config.input_config.plugin_path,
        [
            {
                "module_name": "nonebot_plugin_treehelp",
                "project_link": "nonebot-plugin-treehelp",
                "author": "he0119",
                "tags": [],
                "is_official": True,
            },
            {
                "module_name": "nonebot_plugin_treehelp",
                "project_link": "nonebot-plugin-treehelp",
                "author": "he0119",
                "tags": [],
                "is_official": True,
            },
        ],
    )

    assert not mocked_api["homepage"].called


async def test_resolve_conflict_pull_requests_draft(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    from src.plugins.github import plugin_config
    from src.plugins.github.plugins.publish.utils import resolve_conflict_pull_requests

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_result = mocker.MagicMock()
    mock_subprocess_run.side_effect = lambda *args, **kwargs: mock_result

    mock_label = mocker.MagicMock()
    mock_label.name = "Bot"

    mock_pull = mocker.MagicMock()
    mock_pull.head.ref = "publish/issue1"
    mock_pull.draft = True
    mock_pull.labels = [mock_label]

    with open(tmp_path / "bots.json", "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "name": "CoolQBot",
                    "desc": "基于 NoneBot2 的聊天机器人",
                    "author": "he0119",
                    "homepage": "https://github.com/he0119/CoolQBot",
                    "tags": [],
                    "is_official": False,
                }
            ],
            f,
            ensure_ascii=False,
        )

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

        await resolve_conflict_pull_requests([mock_pull])

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.bot_path,
        [
            {
                "name": "CoolQBot",
                "desc": "基于 NoneBot2 的聊天机器人",
                "author": "he0119",
                "homepage": "https://github.com/he0119/CoolQBot",
                "tags": [],
                "is_official": False,
            }
        ],
    )

    assert not mocked_api["homepage"].called


async def test_resolve_conflict_pull_requests_ref(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    from src.plugins.github import plugin_config
    from src.plugins.github.plugins.publish.utils import resolve_conflict_pull_requests

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_result = mocker.MagicMock()
    mock_subprocess_run.side_effect = lambda *args, **kwargs: mock_result

    mock_label = mocker.MagicMock()
    mock_label.name = "Bot"

    mock_pull = mocker.MagicMock()
    mock_pull.head.ref = "publish/issue"
    mock_pull.draft = False
    mock_pull.labels = [mock_label]

    with open(tmp_path / "bots.json", "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "name": "CoolQBot",
                    "desc": "基于 NoneBot2 的聊天机器人",
                    "author": "he0119",
                    "homepage": "https://github.com/he0119/CoolQBot",
                    "tags": [],
                    "is_official": False,
                }
            ],
            f,
            ensure_ascii=False,
        )

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

        await resolve_conflict_pull_requests([mock_pull])

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.bot_path,
        [
            {
                "name": "CoolQBot",
                "desc": "基于 NoneBot2 的聊天机器人",
                "author": "he0119",
                "homepage": "https://github.com/he0119/CoolQBot",
                "tags": [],
                "is_official": False,
            }
        ],
    )

    assert not mocked_api["homepage"].called
