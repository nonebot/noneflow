import json
from pathlib import Path
from typing import Any, cast

from nonebot import get_adapter
from nonebot.adapters.github import Adapter, GitHubBot
from nonebot.adapters.github.config import GitHubApp
from nonebug import App
from pytest_mock import MockerFixture

from tests.publish.utils import generate_issue_body_bot


def mocked_httpx_get(url: str):
    class MockResponse:
        def __init__(self, status_code: int):
            self.status_code = status_code

    if url == "https://v2.nonebot.dev":
        return MockResponse(200)

    return MockResponse(404)


def check_json_data(file: Path, data: Any) -> None:
    with open(file) as f:
        assert json.load(f) == data


async def test_resolve_conflict_pull_requests(
    app: App, mocker: MockerFixture, tmp_path: Path
) -> None:
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.models import RepoInfo
    from src.plugins.publish.utils import resolve_conflict_pull_requests

    mocker.patch("httpx.get", side_effect=mocked_httpx_get)
    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_result = mocker.MagicMock()
    mock_subprocess_run.side_effect = lambda *args, **kwargs: mock_result

    mock_label = mocker.MagicMock()
    mock_label.name = "Bot"

    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.title = "Bot: test"
    mock_issue.number = 1
    mock_issue.state = "open"
    mock_issue.body = generate_issue_body_bot(name="test")
    mock_issue.user.login = "test"
    mock_issue.labels = [mock_label]

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_pull = mocker.MagicMock()
    mock_pull.head.ref = "publish/issue1"

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "owner", "repo": "repo", "issue_number": 1},
            mock_issues_resp,
        )

        await resolve_conflict_pull_requests(
            bot, RepoInfo(owner="owner", repo="repo"), [mock_pull]
        )

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(["git", "checkout", "master"], check=True, capture_output=True),
            mocker.call(
                ["git", "switch", "-C", "publish/issue1"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "config", "--global", "user.name", "test"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                [
                    "git",
                    "config",
                    "--global",
                    "user.email",
                    "test@users.noreply.github.com",
                ],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "add", "-A"], check=True, capture_output=True),
            mocker.call(
                ["git", "commit", "-m", ":beers: publish bot test (#1)"],
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
                "name": "test",
                "desc": "desc",
                "author": "test",
                "homepage": "https://v2.nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            }
        ],
    )
