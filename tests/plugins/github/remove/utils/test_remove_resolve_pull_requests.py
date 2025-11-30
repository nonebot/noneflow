from pathlib import Path

import pytest
from inline_snapshot import snapshot
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.plugins.github.utils import (
    MockIssue,
    MockUser,
    assert_subprocess_run_calls,
    check_json_data,
    generate_issue_body_remove,
    get_github_bot,
)


def get_issue_labels(mocker: MockerFixture, labels: list[str]):
    mocker_labels = []
    for label in labels:
        mocker_label = mocker.MagicMock()
        mocker_label.name = label
        mocker_labels.append(mocker_label)
    return mocker_labels


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
    from src.plugins.github.handlers import GithubHandler
    from src.plugins.github.plugins.remove.utils import resolve_conflict_pull_requests
    from src.providers.models import RepoInfo
    from src.providers.utils import dump_json5

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

    mock_pull.labels = get_issue_labels(mocker, ["Bot", "Remove"])

    dump_json5(
        tmp_path / "bots.json5",
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
    )

    async with app.test_api() as ctx:
        _adapter, bot = get_github_bot(ctx)

        handler = GithubHandler(bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"))

        ctx.should_call_api(
            "rest.issues.async_get",
            snapshot({"owner": "owner", "repo": "repo", "issue_number": 1}),
            mock_issue_repo,
        )

        await resolve_conflict_pull_requests(handler, [mock_pull])

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "checkout", "master"],
            ["git", "pull"],
            ["git", "switch", "-C", "remove/issue1"],
            ["git", "add", str(tmp_path / "bots.json5")],
            ["git", "config", "--global", "user.name", "he0119"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "he0119@users.noreply.github.com",
            ],
            ["git", "commit", "-m", ":pencil2: remove CoolQBot (#1)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/remove/issue1", "remove/issue1"],
            ["git", "push", "origin", "remove/issue1", "-f"],
        ],
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
    from src.plugins.github.handlers import GithubHandler
    from src.plugins.github.plugins.remove.utils import resolve_conflict_pull_requests
    from src.providers.models import RepoInfo
    from src.providers.utils import dump_json5

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_result = mocker.MagicMock()
    mock_subprocess_run.side_effect = lambda *args, **kwargs: mock_result

    mock_issue_repo = mocker.MagicMock()
    mock_issue = MockIssue(
        number=1,
        body=generate_issue_body_remove(
            "Plugin", "nonebot-plugin-treehelp:nonebot_plugin_treehelp"
        ),
        user=MockUser(login="he0119", id=1),
    ).as_mock(mocker)
    mock_issue_repo.parsed_data = mock_issue

    mock_pull.labels = get_issue_labels(mocker, ["Plugin", "Remove"])
    mock_pull.title = "Plugin: 帮助"

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Plugin: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    dump_json5(
        tmp_path / "plugins.json5",
        [
            {
                "module_name": "nonebot_plugin_treehelp",
                "project_link": "nonebot-plugin-treehelp",
                "author_id": 1,
                "tags": [],
                "is_official": True,
            }
        ],
    )

    async with app.test_api() as ctx:
        _adapter, bot = get_github_bot(ctx)

        ctx.should_call_api(
            "rest.issues.async_get",
            snapshot({"owner": "owner", "repo": "repo", "issue_number": 1}),
            mock_issue_repo,
        )

        handler = GithubHandler(bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"))

        await resolve_conflict_pull_requests(handler, [mock_pull])

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "checkout", "master"],
            ["git", "pull"],
            ["git", "switch", "-C", "remove/issue1"],
            ["git", "add", str(tmp_path / "plugins.json5")],
            ["git", "config", "--global", "user.name", "he0119"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "he0119@users.noreply.github.com",
            ],
            ["git", "commit", "-m", ":pencil2: remove nonebot_plugin_treehelp (#1)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/remove/issue1", "remove/issue1"],
            ["git", "push", "origin", "remove/issue1", "-f"],
        ],
    )

    check_json_data(
        plugin_config.input_config.plugin_path,
        snapshot([]),
    )


async def test_resolve_conflict_pull_requests_not_found(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path, mock_pull
) -> None:
    from src.plugins.github import plugin_config
    from src.plugins.github.handlers import GithubHandler
    from src.plugins.github.plugins.remove.utils import resolve_conflict_pull_requests
    from src.providers.models import RepoInfo
    from src.providers.utils import dump_json5

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_result = mocker.MagicMock()
    mock_subprocess_run.side_effect = lambda *args, **kwargs: mock_result

    mock_issue_repo = mocker.MagicMock()
    mock_issue = MockIssue(
        number=1,
        body=generate_issue_body_remove(
            "Plugin", "nonebot-plugin-treehelp:nonebot_plugin_treehelp"
        ),
        user=MockUser(login="he0119", id=1),
    ).as_mock(mocker)
    mock_issue_repo.parsed_data = mock_issue

    mock_pull.labels = get_issue_labels(mocker, ["Plugin", "Remove"])
    mock_pull.title = "Plugin: 帮助"

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Plugin: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    dump_json5(tmp_path / "plugins.json5", [])

    async with app.test_api() as ctx:
        _adapter, bot = get_github_bot(ctx)

        ctx.should_call_api(
            "rest.issues.async_get",
            snapshot({"owner": "owner", "repo": "repo", "issue_number": 1}),
            mock_issue_repo,
        )

        handler = GithubHandler(bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"))

        await resolve_conflict_pull_requests(handler, [mock_pull])

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()

    check_json_data(
        plugin_config.input_config.plugin_path,
        snapshot([]),
    )
