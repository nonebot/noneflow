# type: ignore
import json
from pathlib import Path
from typing import Any

from github.Repository import Repository
from pytest_mock import MockerFixture

from src.utils import resolve_conflict_pull_requests


def mocked_requests_get(url: str):
    class MockResponse:
        def __init__(self, status_code: int):
            self.status_code = status_code

    if url == "https://v2.nonebot.dev":
        return MockResponse(200)

    return MockResponse(404)


def check_json_data(file: Path, data: Any) -> None:
    with open(file, "r") as f:
        assert json.load(f) == data


def test_resolve_conflict_pull_requests(mocker: MockerFixture, tmp_path: Path) -> None:
    import src.globals as g

    mocker.patch("requests.get", side_effect=mocked_requests_get)
    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_repo: Repository = mocker.MagicMock()

    mock_repo.get_issue().title = "Bot: test"
    mock_repo.get_issue().number = 1
    mock_repo.get_issue().state = "open"
    mock_repo.get_issue().body = """**机器人名称：**\n\ntest\n\n**机器人功能：**\n\ndesc\n\n**机器人项目仓库/主页链接：**\n\nhttps://v2.nonebot.dev\n\n**标签：**\n\n[{"label": "test", "color": "#ffffff"}]"""
    mock_repo.get_issue().user.login = "test"
    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_repo.get_issue().get_comments.return_value = [mock_comment]

    mock_label = mocker.MagicMock()
    mock_label.name = "Bot"
    mock_repo.get_issue().labels = [mock_label]

    mock_pull = mocker.MagicMock()
    mock_pull.head.ref = "publish/issue1"

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    check_json_data(g.settings.input_config.bot_path, [])

    resolve_conflict_pull_requests([mock_pull], mock_repo)

    mock_repo.get_issue.assert_called_with(1)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(["git", "checkout", "master"], check=True),
            mocker.call(["git", "switch", "-C", "publish/issue1"], check=True),
            mocker.call(["git", "config", "--global", "user.name", "test"], check=True),
            mocker.call(
                [
                    "git",
                    "config",
                    "--global",
                    "user.email",
                    "test@users.noreply.github.com",
                ],
                check=True,
            ),
            mocker.call(["git", "add", "-A"], check=True),
            mocker.call(
                ["git", "commit", "-m", ":beers: publish bot test"], check=True
            ),
            mocker.call(["git", "push", "origin", "publish/issue1", "-f"], check=True),
        ]
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
