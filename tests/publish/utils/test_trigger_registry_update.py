from typing import cast

from nonebot import get_adapter
from nonebot.adapters.github import Adapter, GitHubBot
from nonebot.adapters.github.config import GitHubApp
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.publish.utils import (
    generate_issue_body_bot,
    generate_issue_body_plugin_skip_test,
)


async def test_trigger_registry_update(app: App, mocker: MockerFixture):
    from src.plugins.github.models import RepoInfo
    from src.plugins.github.plugins.publish.utils import trigger_registry_update
    from src.providers.validation import PublishType

    mock_sleep = mocker.patch("asyncio.sleep")
    mock_sleep.return_value = None

    mock_issue = mocker.MagicMock()
    mock_issue.state = "open"
    mock_issue.body = "### PyPI 项目名\n\nproject_link1\n\n### 插件 import 包名\n\nmodule_name1\n\n### 插件配置项\n\n```dotenv\nlog_level=DEBUG\n```"
    mock_issue.number = 1

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "owner", "repo": "repo", "issue_number": 1},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.repos.async_create_dispatch_event",
            {
                "repo": "registry",
                "owner": "owner",
                "event_type": "registry_update",
                "client_payload": {
                    "type": "Plugin",
                    "key": "project_link1:module_name1",
                    "config": "log_level=DEBUG\n",
                },
            },
            True,
        )

        await trigger_registry_update(
            bot,
            RepoInfo(owner="owner", repo="repo"),
            PublishType.PLUGIN,
            mock_issue,
        )

    mock_sleep.assert_awaited_once_with(300)


async def test_trigger_registry_update_skip_test(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
):
    """跳过插件加载测试的情况"""
    from src.plugins.github.models import RepoInfo
    from src.plugins.github.plugins.publish.utils import trigger_registry_update
    from src.providers.validation import PublishType

    mock_sleep = mocker.patch("asyncio.sleep")
    mock_sleep.return_value = None

    mock_issue = mocker.MagicMock()
    mock_issue.state = "open"
    mock_issue.body = generate_issue_body_plugin_skip_test()
    mock_issue.number = 1
    mock_issue.user.login = "user"

    mock_comment = mocker.MagicMock()
    mock_comment.body = "/skip"
    mock_comment.author_association = "OWNER"

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "owner", "repo": "repo", "issue_number": 1},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.repos.async_create_dispatch_event",
            {
                "repo": "registry",
                "owner": "owner",
                "event_type": "registry_update",
                "client_payload": {
                    "type": "Plugin",
                    "key": "project_link:module_name",
                    "config": "log_level=DEBUG\n",
                    "data": '{"module_name": "module_name", "project_link": "project_link", "name": "name", "desc": "desc", "author": "user", "author_id": 1, "homepage": "https://nonebot.dev", "tags": [{"label": "test", "color": "#ffffff"}], "is_official": false, "type": "application", "supported_adapters": ["nonebot.adapters.onebot.v11"], "load": false, "metadata": {"name": "name", "description": "desc", "homepage": "https://nonebot.dev", "type": "application", "supported_adapters": ["nonebot.adapters.onebot.v11"]}}',
                },
            },
            True,
        )

        await trigger_registry_update(
            bot,
            RepoInfo(owner="owner", repo="repo"),
            PublishType.PLUGIN,
            mock_issue,
        )

    mock_sleep.assert_awaited_once_with(300)


async def test_trigger_registry_update_bot(app: App, mocker: MockerFixture):
    """机器人发布的情况"""
    from src.plugins.github.models import RepoInfo
    from src.plugins.github.plugins.publish.utils import trigger_registry_update
    from src.providers.validation import PublishType

    mock_sleep = mocker.patch("asyncio.sleep")
    mock_sleep.return_value = None

    mock_issue = mocker.MagicMock()
    mock_issue.state = "open"
    mock_issue.body = generate_issue_body_bot()
    mock_issue.number = 1

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

        ctx.should_call_api(
            "rest.repos.async_create_dispatch_event",
            {
                "repo": "registry",
                "owner": "owner",
                "event_type": "registry_update",
                "client_payload": {"type": "Bot"},
            },
            True,
        )

        await trigger_registry_update(
            bot,
            RepoInfo(owner="owner", repo="repo"),
            PublishType.BOT,
            mock_issue,
        )

    mock_sleep.assert_awaited_once_with(300)


async def test_trigger_registry_update_plugins_issue_body_info_missing(
    app: App, mocker: MockerFixture
):
    """如果议题信息不全，应该不会触发更新"""
    from src.plugins.github.models import RepoInfo
    from src.plugins.github.plugins.publish.utils import trigger_registry_update
    from src.providers.validation import PublishType

    mock_issue = mocker.MagicMock()
    mock_issue.state = "open"
    mock_issue.body = "### 插件配置项\n\n```dotenv\nlog_level=DEBUG\n```"
    mock_issue.number = 1

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "owner", "repo": "repo", "issue_number": 1},
            mock_list_comments_resp,
        )

        await trigger_registry_update(
            bot,
            RepoInfo(owner="owner", repo="repo"),
            PublishType.PLUGIN,
            mock_issue,
        )


async def test_trigger_registry_update_validation_failed(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
):
    """验证失败时也不会触发更新"""
    from src.plugins.github.models import RepoInfo
    from src.plugins.github.plugins.publish.utils import trigger_registry_update
    from src.providers.validation import PublishType

    mock_issue = mocker.MagicMock()
    mock_issue.state = "open"
    mock_issue.body = generate_issue_body_plugin_skip_test(
        homepage="https://www.baidu.com"
    )
    mock_issue.number = 1

    mock_comment = mocker.MagicMock()
    mock_comment.body = "/skip"
    mock_comment.author_association = "OWNER"

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "owner", "repo": "repo", "issue_number": 1},
            mock_list_comments_resp,
        )

        await trigger_registry_update(
            bot,
            RepoInfo(owner="owner", repo="repo"),
            PublishType.PLUGIN,
            mock_issue,
        )

    assert mocked_api["homepage_failed"].called
