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
    with open(file, "r") as f:
        assert json.load(f) == data


def test_process_publish_check(mocker: MockerFixture, tmp_path: Path) -> None:
    import src.globals as g
    from src import Bot

    bot = Bot()
    bot.github = mocker.MagicMock()

    mocker.patch("httpx.get", side_effect=mocked_httpx_get)
    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_result = mocker.MagicMock()
    mock_subprocess_run.side_effect = lambda *args, **kwargs: mock_result

    mock_issues_resp = mocker.MagicMock()
    bot.github.rest.issues.get.return_value = mock_issues_resp
    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.title = "Bot: test"
    mock_issue.number = 1
    mock_issue.state = "open"
    mock_issue.body = """**机器人名称：**\n\ntest\n\n**机器人功能：**\n\ndesc\n\n**机器人项目仓库/主页链接：**\n\nhttps://v2.nonebot.dev\n\n**标签：**\n\n[{"label": "test", "color": "#ffffff"}]"""
    mock_issue.user.login = "test"
    mock_issues_resp.parsed_data = mock_issue

    mock_list_comments_resp = mocker.MagicMock()
    bot.github.rest.issues.list_comments.return_value = mock_list_comments_resp
    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.status_code = 200
    bot.github.rest.pulls.create.return_value = mock_pulls_resp
    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pulls_resp.parsed_data = mock_pull

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    check_json_data(g.settings.input_config.bot_path, [])

    bot.process_publish_check(1)

    # 通过 issue number 获取 issue
    bot.github.rest.issues.get.assert_called_with("owner", "repo", 1)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
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

    # 检查是否创建了拉取请求
    bot.github.rest.pulls.create.assert_called_with(
        "owner",
        "repo",
        title="Bot: test",
        body="resolve #1",
        base="master",
        head="publish/issue1",
    )

    # 测试自动添加标签
    bot.github.rest.issues.add_labels.assert_has_calls(
        [
            mocker.call("owner", "repo", 1, labels=["Bot"]),  # 给议题添加标签
            mocker.call("owner", "repo", 2, labels=["Bot"]),  # 给拉取请求添加标签
        ]
    )

    # 检查是否创建了评论
    bot.github.rest.issues.create_comment.assert_called_with(
        "owner",
        "repo",
        1,
        body="""# 📃 商店发布检查结果\n\n> Bot: test\n\n**✅ 所有测试通过，一切准备就绪！**\n\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 项目 <a href="https://v2.nonebot.dev">主页</a> 返回状态码 200。</li></code></pre></details>\n\n---\n\n💪 Powered by NoneBot2 Publish Bot\n<!-- PUBLISH_BOT -->\n""",
    )


def test_edit_title(mocker: MockerFixture, tmp_path: Path) -> None:
    import src.globals as g
    from src import Bot

    bot = Bot()
    bot.github = mocker.MagicMock()

    mocker.patch("httpx.get", side_effect=mocked_httpx_get)
    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_result = mocker.MagicMock()
    mock_subprocess_run.side_effect = lambda *args, **kwargs: mock_result

    mock_issues_resp = mocker.MagicMock()
    bot.github.rest.issues.get.return_value = mock_issues_resp
    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.title = "Bot: test"
    mock_issue.number = 1
    mock_issue.state = "open"
    mock_issue.body = """**机器人名称：**\n\ntest1\n\n**机器人功能：**\n\ndesc\n\n**机器人项目仓库/主页链接：**\n\nhttps://v2.nonebot.dev\n\n**标签：**\n\n[{"label": "test", "color": "#ffffff"}]"""
    mock_issue.user.login = "test"
    mock_issues_resp.parsed_data = mock_issue

    mock_list_comments_resp = mocker.MagicMock()
    bot.github.rest.issues.list_comments.return_value = mock_list_comments_resp
    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.status_code = 403
    bot.github.rest.pulls.list.return_value = mock_pulls_resp
    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pull.title = "Bot: test"
    mock_pulls_resp.parsed_data = [mock_pull]

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    check_json_data(g.settings.input_config.bot_path, [])

    bot.process_publish_check(1)

    # 通过 issue number 获取 issue
    bot.github.rest.issues.get.assert_called_with("owner", "repo", 1)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
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
                ["git", "commit", "-m", ":beers: publish bot test1 (#1)"],
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
    bot.github.rest.pulls.create.assert_called_with(
        "owner",
        "repo",
        title="Bot: test1",
        body="resolve #1",
        base="master",
        head="publish/issue1",
    )

    # 测试自动添加标签
    bot.github.rest.issues.add_labels.assert_has_calls(
        [
            mocker.call("owner", "repo", 1, labels=["Bot"]),  # 给议题添加标签
        ]
    )

    # # 检查是否修改了标题
    bot.github.rest.issues.update.assert_called_with(
        "owner", "repo", 1, title="Bot: test1"
    )
    bot.github.rest.pulls.list.assert_called_with(
        "owner", "repo", head="owner:publish/issue1"
    )
    bot.github.rest.pulls.update.assert_called_with(
        "owner", "repo", 2, title="Bot: test1"
    )

    # 检查是否创建了评论
    bot.github.rest.issues.create_comment.assert_called_with(
        "owner",
        "repo",
        1,
        body="""# 📃 商店发布检查结果\n\n> Bot: test1\n\n**✅ 所有测试通过，一切准备就绪！**\n\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 项目 <a href="https://v2.nonebot.dev">主页</a> 返回状态码 200。</li></code></pre></details>\n\n---\n\n💪 Powered by NoneBot2 Publish Bot\n<!-- PUBLISH_BOT -->\n""",
    )
