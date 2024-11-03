import json
from pathlib import Path
from typing import Any

import pytest
from inline_snapshot import snapshot
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.github.utils import (
    MockIssue,
    MockUser,
    generate_issue_body_remove,
    get_github_bot,
)


def check_json_data(file: Path, data: Any) -> None:
    with open(file, encoding="utf-8") as f:
        assert json.load(f) == data


@pytest.fixture
def mock_pull(mocker: MockerFixture):
    mock_pull = mocker.MagicMock()
    mock_pull.head.ref = "remove/issue1"
    mock_pull.draft = False

    return mock_pull


async def test_resolve_conflict_pull_requests_bot(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path, mock_pull
) -> None:
    from src.plugins.github import plugin_config
    from src.plugins.github.models import GithubHandler, RepoInfo
    from src.plugins.github.plugins.remove.utils import resolve_conflict_pull_requests

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_result = mocker.MagicMock()
    mock_subprocess_run.side_effect = lambda *args, **kwargs: mock_result

    mock_issue_repo = mocker.MagicMock()
    mock_issue = MockIssue(
        number=1,
        body=generate_issue_body_remove(
            "Bot", "CoolQBot:https://github.com/he0119/CoolQBot"
        ),
        user=MockUser(login="he0119", id=1),
    ).as_mock(mocker)
    mock_issue_repo.parsed_data = mock_issue

    mock_label = mocker.MagicMock()
    mock_label.name = "Bot"

    mock_pull.labels = [mock_label]

    with open(tmp_path / "bots.json", "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "name": "CoolQBot",
                    "desc": "基于 NoneBot2 的聊天机器人",
                    "author_id": 1,
                    "homepage": "https://github.com/he0119/CoolQBot",
                    "tags": [],
                    "is_official": False,
                }
            ],
            f,
            ensure_ascii=False,
        )

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        handler = GithubHandler(bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"))

        ctx.should_call_api(
            "rest.issues.async_get",
            snapshot({"owner": "owner", "repo": "repo", "issue_number": 1}),
            mock_issue_repo,
        )

        await resolve_conflict_pull_requests(handler, [mock_pull])

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "checkout", "remove/issue1"], check=True, capture_output=True
            ),
            mocker.call(["git", "checkout", "master"], check=True, capture_output=True),
            mocker.call(
                ["git", "switch", "-C", "remove/issue1"],
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
                ["git", "commit", "-m", ":hammer: remove CoolQBot (#1)"],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "diff", "origin/remove/issue1", "remove/issue1"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "push", "origin", "remove/issue1", "-f"],
                check=True,
                capture_output=True,
            ),
        ]  # type: ignore
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.bot_path,
        snapshot([]),
    )


async def test_resolve_conflict_pull_requests_plugin(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path, mock_pull
) -> None:
    from src.plugins.github import plugin_config
    from src.plugins.github.models import GithubHandler, RepoInfo
    from src.plugins.github.plugins.remove.utils import resolve_conflict_pull_requests

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_result = mocker.MagicMock()
    mock_subprocess_run.side_effect = lambda *args, **kwargs: mock_result

    mock_label = mocker.MagicMock()
    mock_label.name = "Plugin"

    mock_issue_repo = mocker.MagicMock()
    mock_issue = MockIssue(
        number=1,
        body=generate_issue_body_remove(
            "Plugin", "nonebot-plugin-treehelp:nonebot_plugin_treehelp"
        ),
        user=MockUser(login="he0119", id=1),
    ).as_mock(mocker)
    mock_issue_repo.parsed_data = mock_issue

    mock_pull.labels = [mock_label]
    mock_pull.title = "Plugin: 帮助"

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Plugin: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    with open(tmp_path / "plugins.json", "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "module_name": "nonebot_plugin_treehelp",
                    "project_link": "nonebot-plugin-treehelp",
                    "author_id": 1,
                    "tags": [],
                    "is_official": True,
                }
            ],
            f,
            ensure_ascii=False,
        )

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        ctx.should_call_api(
            "rest.issues.async_get",
            snapshot({"owner": "owner", "repo": "repo", "issue_number": 1}),
            mock_issue_repo,
        )

        handler = GithubHandler(bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"))

        await resolve_conflict_pull_requests(handler, [mock_pull])

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "checkout", "remove/issue1"], check=True, capture_output=True
            ),
            mocker.call(["git", "checkout", "master"], check=True, capture_output=True),
            mocker.call(
                ["git", "switch", "-C", "remove/issue1"],
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
                ["git", "commit", "-m", ":hammer: remove nonebot_plugin_treehelp (#1)"],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "diff", "origin/remove/issue1", "remove/issue1"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "push", "origin", "remove/issue1", "-f"],
                check=True,
                capture_output=True,
            ),
        ]  # type: ignore
    )

    check_json_data(
        plugin_config.input_config.plugin_path,
        snapshot([]),
    )
