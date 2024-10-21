# ruff: noqa: ASYNC101

import json
from pathlib import Path
import httpx
from githubkit import Response
from githubkit.exception import RequestFailed
from inline_snapshot import snapshot
from nonebot.adapters.github import (
    Adapter,
    IssueCommentCreated,
    IssuesOpened,
)
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.github.utils import (
    MockBody,
    MockIssue,
    check_json_data,
    generate_issue_body_bot,
    generate_issue_body_plugin_test_button,
    get_github_bot,
    get_issue_labels,
)


async def test_bot_process_publish_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试机器人的发布流程"""
    from src.plugins.github.plugins.publish import publish_check_matcher
    from src.plugins.github import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(body=MockBody(type="bot", name="test").generate()).as_mock(
        mocker
    )

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
        adapter, bot = get_github_bot(ctx)
        event_path = Path(__file__).parent.parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
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
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Bot: test

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 标签: test-#ffffff。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
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
                "author_id": 1,
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            }
        ],
    )

    assert mocked_api["homepage"].called


async def test_adapter_process_publish_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试适配器的发布流程"""
    from src.plugins.github.plugins.publish import publish_check_matcher
    from src.plugins.github import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(
        body=MockBody(type="adapter", name="test").generate()
    ).as_mock(mocker)

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Adapter: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = mock_pull

    with open(tmp_path / "adapters.json", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.adapter_path, [])

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = Path(__file__).parent.parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())

        assert isinstance(event, IssuesOpened)
        event.payload.issue.labels = get_issue_labels(["Adapter"])

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.pulls.async_create",
            {
                "owner": "he0119",
                "repo": "action-test",
                "title": snapshot("Adapter: test"),
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
                "labels": ["Adapter"],
            },
            True,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 80,
                    "title": "Adapter: test",
                }
            ),
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
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Adapter: test

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 标签: test-#ffffff。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
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
                ["git", "commit", "-m", snapshot(":beers: publish adapter test (#80)")],
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
        plugin_config.input_config.adapter_path,
        [
            snapshot(
                {
                    "module_name": "module_name",
                    "project_link": "project_link",
                    "name": "test",
                    "desc": "desc",
                    "author": "test",
                    "author_id": 1,
                    "homepage": "https://nonebot.dev",
                    "tags": [{"label": "test", "color": "#ffffff"}],
                    "is_official": False,
                }
            )
        ],
    )

    assert mocked_api["homepage"].called


async def test_edit_title(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试编辑标题

    名称被修改后，标题也应该被修改
    """
    from src.plugins.github.plugins.publish import publish_check_matcher
    from src.plugins.github import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(body=MockBody(type="bot", name="test1").generate()).as_mock(
        mocker
    )

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
    mock_pull.draft = False
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = Path(__file__).parent.parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
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
                    httpx.Response(422, request=httpx.Request("test", "test")),
                    None,  # type: ignore
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
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Bot: test1

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 标签: test-#ffffff。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
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
                "author_id": 1,
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            }
        ],
    )

    assert mocked_api["homepage"].called


async def test_edit_title_too_long(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试编辑标题

    标题过长的情况
    """
    from src.plugins.github.plugins.publish import publish_check_matcher
    from src.plugins.github import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(
        body=generate_issue_body_bot(
            name="looooooooooooooooooooooooooooooooooooooooooooooooooooooong"
        )
    ).as_mock(mocker)

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = Path(__file__).parent.parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
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
        # 修改标题，应该被截断，且不会更新拉取请求的标题
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
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Bot: looooooooooooooooooooooooooooooooooooooooooooooooooooooong

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ 名称: 字符过多。<dt>请确保其不超过 50 个字符。</dt></li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 标签: test-#ffffff。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
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
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试发布检查不通过"""
    from src.plugins.github.plugins.publish import publish_check_matcher
    from src.plugins.github import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(
        body=generate_issue_body_bot(name="test", homepage="https://www.baidu.com")
    ).as_mock(mocker)

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = Path(__file__).parent.parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
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
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Bot: test

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保你的项目主页可访问。</dt></li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 标签: test-#ffffff。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
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
        ]  # type: ignore
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
    from src.plugins.github.plugins.publish import publish_check_matcher

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = Path(__file__).parent.parent.parent / "events" / "pr-comment.json"
        event = Adapter.payload_to_event("1", "issue_comment", event_path.read_bytes())
        assert isinstance(event, IssueCommentCreated)

        ctx.receive_event(bot, event)

    assert mocked_api.calls == []
    mock_subprocess_run.assert_not_called()


async def test_issue_state_closed(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, mock_installation
) -> None:
    """测试议题已关闭

    event.issue.state = "closed"
    """
    from src.plugins.github.plugins.publish import publish_check_matcher

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(state="closed").as_mock(mocker)
    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = Path(__file__).parent.parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
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
        ]  # type: ignore
    )


async def test_not_publish_issue(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试议题与发布无关

    议题的标签不是 "Bot/Adapter/Plugin"
    """
    from src.plugins.github.plugins.publish import publish_check_matcher

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = Path(__file__).parent.parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)
        event.payload.issue.labels = []

        ctx.receive_event(bot, event)

    mock_subprocess_run.assert_not_called()


async def test_comment_by_self(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试自己评论触发的情况"""
    from src.plugins.github.plugins.publish import publish_check_matcher

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = (
            Path(__file__).parent.parent.parent / "events" / "issue-comment-bot.json"
        )
        event = Adapter.payload_to_event("1", "issue_comment", event_path.read_bytes())
        assert isinstance(event, IssueCommentCreated)

        ctx.receive_event(bot, event)

    mock_subprocess_run.assert_not_called()


async def test_skip_plugin_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试手动跳过插件测试的流程"""
    from src.plugins.github.plugins.publish import publish_check_matcher
    from src.plugins.github import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(number=70, body=MockBody("plugin").generate()).as_mock(
        mocker
    )

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "/skip"
    mock_comment.author_association = "OWNER"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

    with open(tmp_path / "plugins.json", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.plugin_path, [])

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = (
            Path(__file__).parent.parent.parent / "events" / "issue-comment-skip.json"
        )
        event = Adapter.payload_to_event("1", "issue_comment", event_path.read_bytes())
        assert isinstance(event, IssueCommentCreated)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
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
                "body": '### 插件名称\n\n### 插件描述\n\n### 插件项目仓库/主页链接\n\n### 插件类型\n\n### 插件支持的适配器\n\n### PyPI 项目名\n\nproject_link\n\n### 插件 import 包名\n\nmodule_name\n\n### 标签\n\n[{"label": "test", "color": "#ffffff"}]\n\n### 插件配置项\n\n```dotenv\nlog_level=DEBUG\n```',
            },
            True,
        )

        ctx.should_call_api(
            "rest.issues.async_update",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 70,
                "body": snapshot(
                    """\
### 插件名称

### 插件描述

### 插件项目仓库/主页链接

### 插件类型

### 插件支持的适配器

### PyPI 项目名

project_link

### 插件 import 包名

module_name

### 标签

[{"label": "test", "color": "#ffffff"}]

### 插件配置项

```dotenv
log_level=DEBUG
```

### 插件测试

- [x] 单击左侧按钮重新测试，完成时勾选框将被选中\
"""
                ),
            },
            True,
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {
                "owner": "he0119",
                "repo": "action-test",
                "head": "he0119:publish/issue70",
            },
            mock_pulls_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 70,
                    "title": "Plugin: project_link",
                }
            ),
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
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Plugin: project_link

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ 名称: 无法匹配到数据或值并不合法。<dt>请确保填写该数据项。</dt></li><li>⚠️ 描述: 无法匹配到数据或值并不合法。<dt>请确保填写该数据项。</dt></li><li>⚠️ 项目仓库/主页链接: 无法匹配到数据或值并不合法。<dt>请确保填写该数据项。</dt></li><li>⚠️ 插件类型 None 不符合规范。<dt>请确保插件类型正确，当前仅支持 application 与 library。</dt></li><li>⚠️ 插件测试元数据 &gt; 名称: 无法匹配到数据或值并不合法。<dt>请确保填写该数据项。</dt></li><li>⚠️ 插件测试元数据 &gt; 描述: 无法匹配到数据或值并不合法。<dt>请确保填写该数据项。</dt></li><li>⚠️ 插件测试元数据 &gt; 项目仓库/主页链接: 无法匹配到数据或值并不合法。<dt>请确保填写该数据项。</dt></li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 标签: test-#ffffff。</li><li>✅ 插件支持的适配器: 所有。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 已跳过。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
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
        ]  # type: ignore
    )

    # 检查文件是否正确
    check_json_data(plugin_config.input_config.plugin_path, [])

    assert mocked_api["project_link"].called


async def test_button_skip_publish_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """重测按钮被选中，跳过发布流程"""
    from src.plugins.github.plugins.publish import publish_check_matcher
    from src.plugins.github import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(
        body=generate_issue_body_plugin_test_button(
            body=MockBody(type="plugin").generate(), selected=True
        )
    ).as_mock(mocker)

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "OMG"
    mock_comment.author_association = "OWNER"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

    with open(tmp_path / "plugins.json", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.plugin_path, [])

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = (
            Path(__file__).parent.parent.parent / "events" / "issue-comment-skip.json"
        )
        event = Adapter.payload_to_event("1", "issue_comment", event_path.read_bytes())
        assert isinstance(event, IssueCommentCreated)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 70},
            mock_issues_resp,
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
        ]  # type: ignore
    )

    # 检查文件是否正确
    check_json_data(plugin_config.input_config.plugin_path, [])


async def test_convert_pull_request_to_draft(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """未通过时将拉取请求转换为草稿"""
    from src.plugins.github.plugins.publish import publish_check_matcher
    from src.plugins.github import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(
        number=1,
        body=generate_issue_body_bot(name="test", homepage="https://www.baidu.com"),
    ).as_mock(mocker)

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pull.title = "Bot: test"
    mock_pull.draft = False
    mock_pull.node_id = "123"
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = Path(__file__).parent.parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
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
        # 将拉取请求转换为草稿
        ctx.should_call_api(
            "async_graphql",
            {
                "query": "mutation convertPullRequestToDraft($pullRequestId: ID!) {\n                    convertPullRequestToDraft(input: {pullRequestId: $pullRequestId}) {\n                        clientMutationId\n                    }\n                }",
                "variables": {"pullRequestId": "123"},
            },
            True,
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
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Bot: test

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保你的项目主页可访问。</dt></li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 标签: test-#ffffff。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
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
        ]  # type: ignore
    )

    # 检查文件是否正确
    check_json_data(plugin_config.input_config.bot_path, [])

    assert mocked_api["homepage_failed"].called


async def test_process_publish_check_ready_for_review(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """当之前失败后再次通过测试时，应该将拉取请求标记为 ready for review"""
    from src.plugins.github.plugins.publish import publish_check_matcher
    from src.plugins.github import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(body=MockBody(type="bot", name="test").generate()).as_mock(
        mocker
    )

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
    mock_pull.title = "Bot: test"
    mock_pull.draft = True
    mock_pull.node_id = "123"
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

    with open(tmp_path / "bots.json", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = Path(__file__).parent.parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
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
            exception=RequestFailed(
                Response(
                    httpx.Response(422, request=httpx.Request("test", "test")),
                    None,  # type: ignore
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
        # 将拉取请求标记为可供审阅
        ctx.should_call_api(
            "async_graphql",
            {
                "query": snapshot(
                    """\
mutation markPullRequestReadyForReview($pullRequestId: ID!) {
                        markPullRequestReadyForReview(input: {pullRequestId: $pullRequestId}) {
                            clientMutationId
                        }
                    }\
"""
                ),
                "variables": {"pullRequestId": "123"},
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
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Bot: test

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 标签: test-#ffffff。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
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
                "author_id": 1,
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            }
        ],
    )

    assert mocked_api["homepage"].called
