import json
from pathlib import Path
from inline_snapshot import snapshot
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from nonebot.adapters.github import (
    Adapter,
    IssuesOpened,
)


from tests.github.utils import (
    MockIssue,
    MockUser,
    check_json_data,
    generate_issue_body_remove,
    get_github_bot,
    get_issue_labels,
)


def get_remove_labels():
    return get_issue_labels(["Remove"])


async def test_process_remove_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
):
    """测试正常的删除流程"""
    from src.plugins.github.plugins.remove import remove_check_matcher
    from src.plugins.github import plugin_config

    bot_data = [
        {
            "name": "TESTBOT",
            "desc": "desc",
            "author": "test",
            "author_id": 20,
            "homepage": "https://vv.nonebot.dev",
            "tags": [],
            "is_official": False,
        },
    ]

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(
        body=generate_issue_body_remove("https://vv.nonebot.dev"),
        user=MockUser(login="test", id=20),
    ).as_mock(mocker)

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
        json.dump(bot_data, f)

    check_json_data(plugin_config.input_config.bot_path, bot_data)

    async with app.test_matcher(remove_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = Path(__file__).parent.parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)
        event.payload.issue.labels = get_remove_labels()

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
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "title": "Bot: Remove TESTBOT",
                    "body": "resolve #80",
                    "base": "master",
                    "head": "remove/issue80",
                }
            ),
            mock_pulls_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_add_labels",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 2,
                "labels": ["Remove"],
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
                    "title": "Bot: Remove TESTBOT",
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
# 📃 商店下架检查

> Bot: remove TESTBOT

**✅ 所有检查通过，一切准备就绪！**

> 发起插件下架流程！

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
            },
            True,
        )

        ctx.receive_event(bot, event)

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
                ["git", "switch", "-C", "remove/issue80"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "config", "--global", "user.name", snapshot("test")],
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
            mocker.call(
                ["git", "add", "-A"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "commit", "-m", snapshot(":hammer: remove TESTBOT (#80)")],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "fetch", "origin"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "diff", "origin/remove/issue80", "remove/issue80"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "push", "origin", "remove/issue80", "-f"],
                check=True,
                capture_output=True,
            ),
        ]  # type: ignore
    )


async def test_process_remove_not_found_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
):
    """要删除的包不在数据文件中的情况"""
    from src.plugins.github.plugins.remove import remove_check_matcher
    from src.plugins.github import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(
        body=generate_issue_body_remove("https://notfound.nonebot.dev"),
        user=MockUser(login="test", id=20),
    ).as_mock(mocker)

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

    async with app.test_matcher(remove_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = Path(__file__).parent.parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)
        event.payload.issue.labels = get_remove_labels()

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
# 📃 商店下架检查

> Error

**⚠️ 在下架检查过程中，我们发现以下问题：**

> ⚠️ not_found: 没有包含对应主页链接的包

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
            },
            True,
        )

        ctx.receive_event(bot, event)

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


async def test_process_remove_author_eq_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
):
    """删除包时作者信息不相等的问题"""
    from src.plugins.github.plugins.remove import remove_check_matcher
    from src.plugins.github import plugin_config

    bot_data = [
        {
            "name": "TESTBOT",
            "desc": "desc",
            "author": "test1",
            "author_id": 1,
            "homepage": "https://vv.nonebot.dev",
            "tags": [],
            "is_official": False,
        },
    ]

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(
        body=generate_issue_body_remove("https://vv.nonebot.dev"),
        user=MockUser(login="test", id=20),
    ).as_mock(mocker)

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
        json.dump(bot_data, f)

    check_json_data(plugin_config.input_config.bot_path, bot_data)

    async with app.test_matcher(remove_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = Path(__file__).parent.parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)
        event.payload.issue.labels = get_remove_labels()

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
# 📃 商店下架检查

> Error

**⚠️ 在下架检查过程中，我们发现以下问题：**

> ⚠️ author_info: 作者信息不匹配

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
            },
            True,
        )

        ctx.receive_event(bot, event)

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
