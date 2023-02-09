import json
from pathlib import Path
from typing import Any

from pytest_mock import MockerFixture


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


def test_resolve_conflict_pull_requests(mocker: MockerFixture, tmp_path: Path) -> None:
    import src.globals as g
    from src import Bot

    bot = Bot()
    bot.github = mocker.MagicMock()

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
    mock_issue.body = """**机器人名称：**\n\ntest\n\n**机器人功能：**\n\ndesc\n\n**机器人项目仓库/主页链接：**\n\nhttps://v2.nonebot.dev\n\n**标签：**\n\n[{"label": "test", "color": "#ffffff"}]"""
    mock_issue.user.login = "test"
    mock_issue.labels = [mock_label]

    mock_issues_resp = mocker.MagicMock()
    bot.github.rest.issues.get.return_value = mock_issues_resp
    mock_issues_resp.parsed_data = mock_issue

    mock_pull = mocker.MagicMock()
    mock_pull.head.ref = "publish/issue1"

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    check_json_data(g.settings.input_config.bot_path, [])

    bot.resolve_conflict_pull_requests([mock_pull])

    bot.github.rest.issues.get.assert_called_with("owner", "repo", 1)

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
        g.settings.input_config.bot_path,
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
