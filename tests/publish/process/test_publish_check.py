import json
from pathlib import Path
from typing import Any, cast

import httpx
from githubkit import Response
from githubkit.exception import RequestFailed
from nonebot import get_adapter
from nonebot.adapters.github import (
    Adapter,
    GitHubBot,
    IssueCommentCreated,
    IssuesOpened,
)
from nonebot.adapters.github.config import GitHubApp
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.publish.utils import generate_issue_body_bot, generate_issue_body_plugin


def check_json_data(file: Path, data: Any) -> None:
    with open(file) as f:
        assert json.load(f) == data


async def test_process_publish_check(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    """测试一个正常的发布流程"""
    from src.plugins.publish import publish_check_matcher
    from src.plugins.publish.config import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.title = "Bot: test"
    mock_issue.number = 80
    mock_issue.state = "open"
    mock_issue.body = generate_issue_body_bot(name="test")
    mock_issue.user.login = "test"

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = mock_pull

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.pulls.async_create",
            {
                "owner": "he0119",
                "repo": "action-test",
                "title": "Bot: test",
                "body": "resolve #80",
                "base": "master",
                "head": "publish/issue80",
            },
            mock_pulls_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_add_labels",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 2,
                "labels": ["Bot"],
            },
            True,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "body": """# 📃 商店发布检查结果\n\n> Bot: test\n\n**✅ 所有测试通过，一切准备就绪！**\n\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li></code></pre></details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n""",
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["pre-commit", "install", "--install-hooks"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "switch", "-C", "publish/issue80"],
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
                ["git", "commit", "-m", ":beers: publish bot test (#80)"],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "diff", "origin/publish/issue80", "publish/issue80"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "push", "origin", "publish/issue80", "-f"],
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
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            }
        ],
    )

    assert mocked_api["homepage"].called


async def test_edit_title(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    """测试编辑标题

    名称被修改后，标题也应该被修改
    """
    from src.plugins.publish import publish_check_matcher
    from src.plugins.publish.config import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.title = "Bot: test"
    mock_issue.number = 80
    mock_issue.state = "open"
    mock_issue.body = generate_issue_body_bot(name="test1")
    mock_issue.user.login = "test"

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.pulls.async_create",
            {
                "owner": "he0119",
                "repo": "action-test",
                "title": "Bot: test1",
                "body": "resolve #80",
                "base": "master",
                "head": "publish/issue80",
            },
            exception=RequestFailed(
                Response(
                    httpx.Response(422, request=httpx.Request("test", "test")), None
                )
            ),
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {
                "owner": "he0119",
                "repo": "action-test",
                "head": "he0119:publish/issue80",
            },
            mock_pulls_resp,
        )
        # 修改标题
        ctx.should_call_api(
            "rest.pulls.async_update",
            {
                "owner": "he0119",
                "repo": "action-test",
                "pull_number": 2,
                "title": "Bot: test1",
            },
            True,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "title": "Bot: test1",
            },
            True,
        )

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "body": """# 📃 商店发布检查结果\n\n> Bot: test1\n\n**✅ 所有测试通过，一切准备就绪！**\n\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li></code></pre></details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n""",
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["pre-commit", "install", "--install-hooks"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "switch", "-C", "publish/issue80"],
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
                ["git", "commit", "-m", ":beers: publish bot test1 (#80)"],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "diff", "origin/publish/issue80", "publish/issue80"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "push", "origin", "publish/issue80", "-f"],
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
                "name": "test1",
                "desc": "desc",
                "author": "test",
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            }
        ],
    )

    assert mocked_api["homepage"].called


async def test_edit_title_too_long(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    """测试编辑标题

    标题过长的情况
    """
    from src.plugins.publish import publish_check_matcher
    from src.plugins.publish.config import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.title = "Bot: test"
    mock_issue.number = 80
    mock_issue.state = "open"
    mock_issue.body = generate_issue_body_bot(
        name="looooooooooooooooooooooooooooooooooooooooooooooooooooooong"
    )
    mock_issue.user.login = "test"

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        # 修改标题，应该被阶段，且不会更新拉取请求的标题
        ctx.should_call_api(
            "rest.issues.async_update",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "title": "Bot: looooooooooooooooooooooooooooooooooooooooooooooooo",
            },
            True,
        )

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "body": """# 📃 商店发布检查结果\n\n> Bot: looooooooooooooooooooooooooooooooooooooooooooooooooooooong\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 名称过长。<dt>请确保名称不超过 50 个字符。</dt></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li></code></pre></details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n""",
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            )  # type: ignore
        ]
    )

    # 检查文件是否正确
    check_json_data(plugin_config.input_config.bot_path, [])

    assert mocked_api["homepage"].called


async def test_process_publish_check_not_pass(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    """测试发布检查不通过"""
    from src.plugins.publish import publish_check_matcher
    from src.plugins.publish.config import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.title = "Bot: test"
    mock_issue.number = 1
    mock_issue.state = "open"
    mock_issue.body = generate_issue_body_bot(
        name="test", homepage="https://www.baidu.com"
    )
    mock_issue.user.login = "test"

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        # 检查是否需要跳过插件测试
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        # 检查是否可以复用评论
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )

        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "body": """# 📃 商店发布检查结果\n\n> Bot: test\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保你的项目主页可访问。</dt></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li></code></pre></details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n""",
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["pre-commit", "install", "--install-hooks"],
                check=True,
                capture_output=True,
            ),
        ]
    )

    # 检查文件是否正确
    check_json_data(plugin_config.input_config.bot_path, [])

    assert mocked_api["homepage_failed"].called


async def test_comment_at_pull_request(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试在拉取请求下评论

    event.issue.pull_request 不为空
    """
    from src.plugins.publish import publish_check_matcher

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "pr-comment.json"
        event = Adapter.payload_to_event("1", "issue_comment", event_path.read_bytes())
        assert isinstance(event, IssueCommentCreated)

        ctx.receive_event(bot, event)

    assert mocked_api.calls == []
    mock_subprocess_run.assert_not_called()


async def test_issue_state_closed(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试议题已关闭

    event.issue.state = "closed"
    """
    from src.plugins.publish import publish_check_matcher

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.state = "closed"
    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )

        ctx.receive_event(bot, event)

    assert mocked_api.calls == []
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["pre-commit", "install", "--install-hooks"],
                check=True,
                capture_output=True,
            ),
        ]
    )


async def test_not_publish_issue(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试议题与发布无关

    议题的标签不是 "Bot/Adapter/Plugin"
    """
    from src.plugins.publish import publish_check_matcher

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)
        event.payload.issue.labels = []

        ctx.receive_event(bot, event)

    mock_subprocess_run.assert_not_called()


async def test_comment_by_self(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试自己评论触发的情况"""
    from src.plugins.publish import publish_check_matcher

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-comment-bot.json"
        event = Adapter.payload_to_event("1", "issue_comment", event_path.read_bytes())
        assert isinstance(event, IssueCommentCreated)

        ctx.receive_event(bot, event)

    mock_subprocess_run.assert_not_called()


async def test_skip_plugin_check(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    """测试手动跳过插件测试的流程"""
    from src.plugins.publish import publish_check_matcher
    from src.plugins.publish.config import plugin_config

    mocker.patch.object(plugin_config, "plugin_test_result", False)

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.title = "Plugin: project_link"
    mock_issue.number = 70
    mock_issue.state = "open"
    mock_issue.body = generate_issue_body_plugin()
    mock_issue.user.login = "test"

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "/skip"
    mock_comment.author_association = "OWNER"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = mock_pull

    with open(tmp_path / "plugins.json", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.plugin_path, [])

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-comment-skip.json"
        event = Adapter.payload_to_event("1", "issue_comment", event_path.read_bytes())
        assert isinstance(event, IssueCommentCreated)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 70},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 70},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 70,
                "body": '### 插件名称\n\n### 插件描述\n\n### 插件项目仓库/主页链接\n\n### 插件类型\n\n### 插件支持的适配器\n\n### PyPI 项目名\n\nproject_link\n\n### 插件 import 包名\n\nmodule_name\n\n### 标签\n\n[{"label": "test", "color": "#ffffff"}]',
            },
            True,
        )
        # 修改标题
        ctx.should_call_api(
            "rest.issues.async_update",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 70,
                "title": "Plugin: ",
            },
            True,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 70},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 70,
                "body": """# 📃 商店发布检查结果\n\n> Plugin: \n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 名称: 无法匹配到数据。<dt>请确保填写该项目。</dt></li><li>⚠️ 功能: 无法匹配到数据。<dt>请确保填写该项目。</dt></li><li>⚠️ 项目仓库/主页链接: 无法匹配到数据。<dt>请确保填写该项目。</dt></li><li>⚠️ 插件类型不能为空。<dt>请确保填写插件类型。</dt></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 项目 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 已跳过。</li></code></pre></details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n""",
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["pre-commit", "install", "--install-hooks"],
                check=True,
                capture_output=True,
            ),
        ]
    )

    # 检查文件是否正确
    check_json_data(plugin_config.input_config.plugin_path, [])

    assert mocked_api["project_link"].called
    assert mocked_api["project_link"].called
