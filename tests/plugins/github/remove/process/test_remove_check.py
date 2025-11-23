from pathlib import Path

from inline_snapshot import snapshot
from nonebot.adapters.github import IssueCommentCreated, IssuesOpened
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.plugins.github.event import get_mock_event
from tests.plugins.github.utils import (
    GitHubApi,
    MockIssue,
    MockUser,
    assert_subprocess_run_calls,
    check_json_data,
    generate_issue_body_remove,
    get_github_bot,
    get_issue_labels,
    mock_subprocess_run_with_side_effect,
    should_call_apis,
)


def get_remove_labels():
    return get_issue_labels(["Remove"])


async def test_process_remove_bot_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
    mock_installation_token,
):
    """测试正常的删除流程"""
    from src.plugins.github import plugin_config
    from src.providers.utils import dump_json5

    data = [
        {
            "name": "TESTBOT",
            "desc": "desc",
            "author": "test",
            "author_id": 20,
            "homepage": "https://vv.nonebot.dev",
            "tags": [],
            "is_official": False,
        }
    ]

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    remove_type = "Bot"
    mock_issue = MockIssue(
        body=generate_issue_body_remove(remove_type, "TESTBOT:https://vv.nonebot.dev"),
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

    mock_pulls_resp_list = mocker.MagicMock()
    mock_pulls_resp_list.parsed_data = [mock_pull]

    dump_json5(tmp_path / "bots.json5", data)

    check_json_data(plugin_config.input_config.bot_path, data)

    apis: list[GitHubApi] = [
        {"api": "rest.apps.async_get_repo_installation", "result": mock_installation},
        {
            "api": "rest.apps.async_create_installation_access_token",
            "result": mock_installation_token,
        },
        {"api": "rest.issues.async_get", "result": mock_issues_resp},
        {"api": "rest.pulls.async_create", "result": mock_pulls_resp},
        {"api": "rest.issues.async_add_labels", "result": True},
        {"api": "rest.issues.async_update", "result": True},
        {"api": "rest.pulls.async_list", "result": mock_pulls_resp_list},
        {"api": "rest.issues.async_list_comments", "result": mock_list_comments_resp},
        {"api": "rest.issues.async_create_comment", "result": True},
    ]

    data_list = [
        {"owner": "he0119", "repo": "action-test"},
        {"installation_id": mock_installation.parsed_data.id},
        {"owner": "he0119", "repo": "action-test", "issue_number": 80},
        snapshot(
            {
                "owner": "owner",
                "repo": "store",
                "title": "Bot: Remove TESTBOT",
                "body": "resolve he0119/action-test#80",
                "base": "master",
                "head": "remove/issue80",
            }
        ),
        {
            "owner": "owner",
            "repo": "store",
            "issue_number": 2,
            "labels": ["Remove", "Bot"],
        },
        snapshot(
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "title": "Bot: Remove TESTBOT",
            }
        ),
        {"owner": "owner", "repo": "store", "head": "owner:remove/issue80"},
        {"owner": "he0119", "repo": "action-test", "issue_number": 80},
        {
            "owner": "he0119",
            "repo": "action-test",
            "issue_number": 80,
            "body": snapshot(
                """\
# 📃 商店下架检查

> Bot: remove TESTBOT

**✅ 所有检查通过，一切准备就绪！**

> 成功发起插件下架流程，对应的拉取请求 owner/store#2 已经创建。

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
            ),
        },
    ]

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)
        event.payload.issue.labels = get_issue_labels(["Remove", remove_type])

        should_call_apis(ctx, apis, data_list)

        ctx.receive_event(bot, event)

    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "config", "--global", "safe.directory", "*"],
            [
                "git",
                "config",
                "--global",
                "url.https://x-access-token:test-token@github.com/.insteadOf",
                "https://github.com/",
            ],
            ["git", "switch", "-C", "remove/issue80"],
            ["git", "add", str(tmp_path / "bots.json5")],
            ["git", "config", "--global", "user.name", "test"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "test@users.noreply.github.com",
            ],
            ["git", "commit", "-m", ":pencil2: remove TESTBOT (#80)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/remove/issue80", "remove/issue80"],
            ["git", "push", "origin", "remove/issue80", "-f"],
        ],
    )


async def test_process_remove_plugin_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
    mock_installation_token,
):
    """测试正常的删除流程"""
    from src.plugins.github import plugin_config
    from src.providers.utils import dump_json5

    data = [
        {
            "module_name": "module_name",
            "project_link": "project_link",
            "name": "test",
            "desc": "desc",
            "author_id": 20,
            "homepage": "https://nonebot.dev",
            "tags": [{"label": "test", "color": "#ffffff"}],
            "is_official": False,
        }
    ]

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    remove_type = "Plugin"
    mock_issue = MockIssue(
        body=generate_issue_body_remove(remove_type, "project_link:module_name"),
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

    mock_pulls_resp_list = mocker.MagicMock()
    mock_pulls_resp_list.parsed_data = [mock_pull]

    dump_json5(tmp_path / "plugins.json5", data)

    check_json_data(plugin_config.input_config.plugin_path, data)

    apis: list[GitHubApi] = [
        {"api": "rest.apps.async_get_repo_installation", "result": mock_installation},
        {
            "api": "rest.apps.async_create_installation_access_token",
            "result": mock_installation_token,
        },
        {"api": "rest.issues.async_get", "result": mock_issues_resp},
        {"api": "rest.pulls.async_create", "result": mock_pulls_resp},
        {"api": "rest.issues.async_add_labels", "result": True},
        {"api": "rest.issues.async_update", "result": True},
        {"api": "rest.pulls.async_list", "result": mock_pulls_resp_list},
        {"api": "rest.issues.async_list_comments", "result": mock_list_comments_resp},
        {"api": "rest.issues.async_create_comment", "result": True},
    ]

    data_list = [
        {"owner": "he0119", "repo": "action-test"},
        {"installation_id": mock_installation.parsed_data.id},
        {"owner": "he0119", "repo": "action-test", "issue_number": 80},
        snapshot(
            {
                "owner": "owner",
                "repo": "store",
                "title": "Plugin: Remove test",
                "body": "resolve he0119/action-test#80",
                "base": "master",
                "head": "remove/issue80",
            }
        ),
        snapshot(
            {
                "owner": "owner",
                "repo": "store",
                "issue_number": 2,
                "labels": ["Remove", "Plugin"],
            }
        ),
        snapshot(
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "title": "Plugin: Remove test",
            }
        ),
        {"owner": "owner", "repo": "store", "head": "owner:remove/issue80"},
        {"owner": "he0119", "repo": "action-test", "issue_number": 80},
        {
            "owner": "he0119",
            "repo": "action-test",
            "issue_number": 80,
            "body": snapshot(
                """\
# 📃 商店下架检查

> Plugin: remove test

**✅ 所有检查通过，一切准备就绪！**

> 成功发起插件下架流程，对应的拉取请求 owner/store#2 已经创建。

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
            ),
        },
    ]

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)
        event.payload.issue.labels = get_issue_labels(["Remove", remove_type])

        should_call_apis(ctx, apis, data_list)

        ctx.receive_event(bot, event)

    expected_commands = [
        ["git", "config", "--global", "safe.directory", "*"],
        [
            "git",
            "config",
            "--global",
            "url.https://x-access-token:test-token@github.com/.insteadOf",
            "https://github.com/",
        ],
        ["git", "switch", "-C", "remove/issue80"],
        ["git", "add", str(tmp_path / "plugins.json5")],
        ["git", "config", "--global", "user.name", "test"],
        ["git", "config", "--global", "user.email", "test@users.noreply.github.com"],
        ["git", "commit", "-m", ":pencil2: remove test (#80)"],
        ["git", "fetch", "origin"],
        ["git", "diff", "origin/remove/issue80", "remove/issue80"],
        ["git", "push", "origin", "remove/issue80", "-f"],
    ]

    assert_subprocess_run_calls(mock_subprocess_run, expected_commands)


async def test_process_remove_not_found_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
    mock_installation_token,
):
    """要删除的包不在数据文件中的情况"""
    from src.plugins.github import plugin_config
    from src.providers.utils import dump_json5

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    remove_type = "Bot"
    mock_issue = MockIssue(
        body=generate_issue_body_remove(
            type=remove_type, key="TESTBOT:https://notfound.nonebot.dev"
        ),
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

    dump_json5(tmp_path / "bots.json5", [])

    check_json_data(plugin_config.input_config.bot_path, [])

    apis: list[GitHubApi] = [
        {"api": "rest.apps.async_get_repo_installation", "result": mock_installation},
        {
            "api": "rest.apps.async_create_installation_access_token",
            "result": mock_installation_token,
        },
        {"api": "rest.issues.async_get", "result": mock_issues_resp},
        {"api": "rest.issues.async_list_comments", "result": mock_list_comments_resp},
        {"api": "rest.issues.async_create_comment", "result": True},
    ]

    data_list = [
        {"owner": "he0119", "repo": "action-test"},
        {"installation_id": mock_installation.parsed_data.id},
        {"owner": "he0119", "repo": "action-test", "issue_number": 80},
        {"owner": "he0119", "repo": "action-test", "issue_number": 80},
        {
            "owner": "he0119",
            "repo": "action-test",
            "issue_number": 80,
            "body": snapshot(
                """\
# 📃 商店下架检查

> Error

**⚠️ 在下架检查过程中，我们发现以下问题：**

> ⚠️ 不存在对应信息的包

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
            ),
        },
    ]

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)
        event.payload.issue.labels = get_issue_labels(["Remove", remove_type])

        should_call_apis(ctx, apis, data_list)

        ctx.receive_event(bot, event)

    expected_commands = [
        ["git", "config", "--global", "safe.directory", "*"],
    ]

    assert_subprocess_run_calls(mock_subprocess_run, expected_commands)


async def test_process_remove_author_info_not_eq(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
    mock_installation_token,
):
    """删除包时作者信息不相等的问题"""
    from src.plugins.github import plugin_config
    from src.providers.utils import dump_json5

    bot_data = [
        {
            "name": "TESTBOT",
            "desc": "desc",
            "author": "test1",
            "author_id": 1,
            "homepage": "https://vv.nonebot.dev",
            "tags": [],
            "is_official": False,
        }
    ]

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    remove_type = "Bot"
    mock_issue = MockIssue(
        body=generate_issue_body_remove(
            type=remove_type, key="TESTBOT:https://vv.nonebot.dev"
        ),
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

    dump_json5(tmp_path / "bots.json5", bot_data)

    check_json_data(plugin_config.input_config.bot_path, bot_data)

    apis: list[GitHubApi] = [
        {"api": "rest.apps.async_get_repo_installation", "result": mock_installation},
        {
            "api": "rest.apps.async_create_installation_access_token",
            "result": mock_installation_token,
        },
        {"api": "rest.issues.async_get", "result": mock_issues_resp},
        {"api": "rest.issues.async_list_comments", "result": mock_list_comments_resp},
        {"api": "rest.issues.async_create_comment", "result": True},
    ]

    data_list = [
        {"owner": "he0119", "repo": "action-test"},
        {"installation_id": mock_installation.parsed_data.id},
        {"owner": "he0119", "repo": "action-test", "issue_number": 80},
        {"owner": "he0119", "repo": "action-test", "issue_number": 80},
        {
            "owner": "he0119",
            "repo": "action-test",
            "issue_number": 80,
            "body": snapshot(
                """\
# 📃 商店下架检查

> Error

**⚠️ 在下架检查过程中，我们发现以下问题：**

> ⚠️ 作者信息验证不匹配

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
            ),
        },
    ]

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)
        event.payload.issue.labels = get_issue_labels(["Remove", remove_type])

        should_call_apis(ctx, apis, data_list)

        ctx.receive_event(bot, event)

    expected_commands = [
        ["git", "config", "--global", "safe.directory", "*"],
    ]

    assert_subprocess_run_calls(mock_subprocess_run, expected_commands)


async def test_process_remove_issue_info_not_found(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
    mock_installation_token,
):
    """删除包时无法从议题获取信息的测试"""
    from src.plugins.github import plugin_config
    from src.providers.utils import dump_json5

    bot_data = [
        {
            "name": "TESTBOT",
            "desc": "desc",
            "author": "test1",
            "author_id": 1,
            "homepage": "https://vv.nonebot.dev",
            "tags": [],
            "is_official": False,
        }
    ]

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    remove_type = "Bot"
    mock_issue = MockIssue(
        body=generate_issue_body_remove(type=remove_type, key="TESTBOT:"),
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

    dump_json5(tmp_path / "bots.json5", bot_data)

    check_json_data(plugin_config.input_config.bot_path, bot_data)

    apis: list[GitHubApi] = [
        {"api": "rest.apps.async_get_repo_installation", "result": mock_installation},
        {
            "api": "rest.apps.async_create_installation_access_token",
            "result": mock_installation_token,
        },
        {"api": "rest.issues.async_get", "result": mock_issues_resp},
        {"api": "rest.issues.async_list_comments", "result": mock_list_comments_resp},
        {"api": "rest.issues.async_create_comment", "result": True},
    ]

    data_list = [
        {"owner": "he0119", "repo": "action-test"},
        {"installation_id": mock_installation.parsed_data.id},
        {"owner": "he0119", "repo": "action-test", "issue_number": 80},
        {"owner": "he0119", "repo": "action-test", "issue_number": 80},
        {
            "owner": "he0119",
            "repo": "action-test",
            "issue_number": 80,
            "body": snapshot(
                """\
# 📃 商店下架检查

> Error

**⚠️ 在下架检查过程中，我们发现以下问题：**

> ⚠️ 未填写数据项或填写格式有误

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
            ),
        },
    ]

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)
        event.payload.issue.labels = get_issue_labels(["Remove", remove_type])

        should_call_apis(ctx, apis, data_list)

        ctx.receive_event(bot, event)

    expected_commands = [
        ["git", "config", "--global", "safe.directory", "*"],
    ]

    assert_subprocess_run_calls(mock_subprocess_run, expected_commands)


async def test_process_remove_driver(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
    mock_installation_token,
):
    """不支持驱动器类型的删除"""
    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    remove_type = "Driver"
    mock_issue = MockIssue(
        body=generate_issue_body_remove(type=remove_type, key="TESTBOT:"),
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

    apis: list[GitHubApi] = [
        {"api": "rest.apps.async_get_repo_installation", "result": mock_installation},
        {
            "api": "rest.apps.async_create_installation_access_token",
            "result": mock_installation_token,
        },
        {"api": "rest.issues.async_get", "result": mock_issues_resp},
        {"api": "rest.issues.async_list_comments", "result": mock_list_comments_resp},
        {"api": "rest.issues.async_create_comment", "result": True},
    ]

    data_list = [
        {"owner": "he0119", "repo": "action-test"},
        {"installation_id": mock_installation.parsed_data.id},
        {"owner": "he0119", "repo": "action-test", "issue_number": 80},
        {"owner": "he0119", "repo": "action-test", "issue_number": 80},
        {
            "owner": "he0119",
            "repo": "action-test",
            "issue_number": 80,
            "body": snapshot(
                """\
# 📃 商店下架检查

> Error

**⚠️ 在下架检查过程中，我们发现以下问题：**

> ⚠️ 暂不支持的移除类型

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
            ),
        },
    ]

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)
        event.payload.issue.labels = get_issue_labels(["Remove", remove_type])

        should_call_apis(ctx, apis, data_list)

        ctx.receive_event(bot, event)

    expected_commands = [
        ["git", "config", "--global", "safe.directory", "*"],
    ]

    assert_subprocess_run_calls(mock_subprocess_run, expected_commands)


async def test_process_not_remove_label(app: App):
    """测试没有删除标签的情况"""
    from src.plugins.github.plugins.remove import remove_check_matcher

    remove_type = "Driver"

    async with app.test_matcher(remove_check_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)
        event.payload.issue.labels = get_issue_labels([remove_type])
        ctx.receive_event(bot, event)


async def test_process_trigger_by_bot(app: App):
    """测试 Bot 触发工作流的情况"""
    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssueCommentCreated)
        assert event.payload.comment.user
        event.payload.comment.user.type = "Bot"

        ctx.receive_event(bot, event)
        ctx.should_not_pass_rule()

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)
        assert event.payload.sender.type
        event.payload.sender.type = "Bot"

        ctx.receive_event(bot, event)
        ctx.should_not_pass_rule()
