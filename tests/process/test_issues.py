# type: ignore
import json
from pathlib import Path
from typing import Any

from github.Repository import Repository
from pytest_mock import MockerFixture

from src.process import process_issues_event


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


def test_process_issues(mocker: MockerFixture, tmp_path: Path) -> None:
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

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    with open(tmp_path / "events.json", "w") as f:
        json.dump(
            {
                "action": "opened",
                "issue": {
                    "number": 1,
                },
            },
            f,
        )

    check_json_data(g.settings.input_config.bot_path, [])

    process_issues_event(mock_repo)

    mock_repo.get_issue.assert_called_with(1)
    # 测试自动添加标签
    mock_repo.get_issue().edit.assert_called_with(labels=["Bot"])

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
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
                ["git", "commit", "-m", ":beers: publish bot test (#1)"], check=True
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

    # 检查是否创建了拉取请求
    mock_repo.create_pull.assert_called_with(
        title="Bot: test",
        body="resolve #1",
        base="master",
        head="publish/issue1",
    )
    mock_repo.create_pull().add_to_labels.assert_called_with("Bot")

    # 检查是否创建了评论
    mock_repo.get_issue().create_comment.assert_called_with(
        """# 📃 商店发布检查结果\n\n> Bot: test\n\n**✅ 所有测试通过，一切准备就绪!**\n\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff</li><li>✅ 项目 <a href="https://v2.nonebot.dev">主页</a> 返回状态码 200.</li></code></pre></details>\n\n---\n\n💪 Powered by NoneBot2 Publish Bot\n<!-- PUBLISH_BOT -->\n"""
    )


def test_edit_title(mocker: MockerFixture, tmp_path: Path) -> None:
    from github import GithubException

    import src.globals as g

    mocker.patch("requests.get", side_effect=mocked_requests_get)
    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_repo: Repository = mocker.MagicMock()
    mock_repo.owner.login = "test"

    mock_repo.get_issue().title = "Bot: test"
    mock_repo.get_issue().number = 1
    mock_repo.get_issue().state = "open"
    mock_repo.get_issue().body = """**机器人名称：**\n\ntest1\n\n**机器人功能：**\n\ndesc\n\n**机器人项目仓库/主页链接：**\n\nhttps://v2.nonebot.dev\n\n**标签：**\n\n[{"label": "test", "color": "#ffffff"}]"""
    mock_repo.get_issue().user.login = "test"

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_repo.get_issue().get_comments.return_value = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.title = "Bot: test"
    mock_repo.get_pulls.return_value = [mock_pull]
    mock_repo.create_pull.side_effect = GithubException(
        status=422, data={"message": "title already exists"}, headers=None
    )

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    with open(tmp_path / "events.json", "w") as f:
        json.dump(
            {
                "action": "opened",
                "issue": {
                    "number": 1,
                },
            },
            f,
        )

    check_json_data(g.settings.input_config.bot_path, [])

    process_issues_event(mock_repo)

    mock_repo.get_issue.assert_called_with(1)
    # 测试自动添加标签
    mock_repo.get_issue().edit.assert_has_calls(
        [
            mocker.call(labels=["Bot"]),
            mocker.call(title="Bot: test1"),
        ]
    )

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
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
                ["git", "commit", "-m", ":beers: publish bot test1 (#1)"], check=True
            ),
            mocker.call(["git", "push", "origin", "publish/issue1", "-f"], check=True),
        ]
    )

    # 检查文件是否正确
    check_json_data(
        g.settings.input_config.bot_path,
        [
            {
                "name": "test1",
                "desc": "desc",
                "author": "test",
                "homepage": "https://v2.nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            }
        ],
    )

    # 检查是否创建了拉取请求
    mock_repo.create_pull.assert_called_with(
        title="Bot: test1",
        body="resolve #1",
        base="master",
        head="publish/issue1",
    )

    # 检查是否修改了标题
    mock_repo.get_pulls.assert_called_with(head="test:publish/issue1")
    mock_pull.edit.assert_called_with(title="Bot: test1")

    # 检查是否创建了评论
    mock_repo.get_issue().create_comment.assert_called_with(
        """# 📃 商店发布检查结果\n\n> Bot: test1\n\n**✅ 所有测试通过，一切准备就绪!**\n\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff</li><li>✅ 项目 <a href="https://v2.nonebot.dev">主页</a> 返回状态码 200.</li></code></pre></details>\n\n---\n\n💪 Powered by NoneBot2 Publish Bot\n<!-- PUBLISH_BOT -->\n"""
    )
