from inline_snapshot import snapshot
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.github.utils import (
    MockBody,
    MockIssue,
    generate_issue_body_plugin_skip_test,
    get_github_bot,
)


async def test_trigger_registry_update(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
):
    from src.plugins.github.models import IssueHandler, RepoInfo
    from src.plugins.github.plugins.publish.utils import trigger_registry_update
    from src.providers.docker_test import Metadata
    from src.providers.validation import PublishType

    mock_time = mocker.patch("src.providers.models.datetime")
    mock_now = mocker.MagicMock()
    mock_now.isoformat.return_value = "2023-09-01T00:00:00+00:00Z"
    mock_time.now.return_value = mock_now

    mock_issue = MockIssue(
        body=MockBody(type="plugin").generate(),
        number=1,
    ).as_mock(mocker)

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_test_result = mocker.MagicMock()
    mock_test_result.metadata = Metadata(
        name="name",
        desc="desc",
        homepage="https://nonebot.dev",
        type="application",
        supported_adapters=["~onebot.v11"],
    )
    mock_test_result.load = True
    mock_test_result.version = "1.0.0"
    mock_test_result.output = ""
    mock_docker = mocker.patch("src.providers.docker_test.DockerPluginTest.run")
    mock_docker.return_value = mock_test_result

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "owner", "repo": "registry", "issue_number": 1},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.repos.async_create_dispatch_event",
            snapshot(
                {
                    "repo": "registry",
                    "owner": "owner",
                    "event_type": "registry_update",
                    "client_payload": {
                        "type": PublishType.PLUGIN,
                        "registry": {
                            "module_name": "module_name",
                            "project_link": "project_link",
                            "name": "name",
                            "desc": "desc",
                            "author": "test",
                            "homepage": "https://nonebot.dev",
                            "tags": [{"label": "test", "color": "#ffffff"}],
                            "is_official": False,
                            "type": "application",
                            "supported_adapters": ["nonebot.adapters.onebot.v11"],
                            "valid": True,
                            "time": "2023-09-01T00:00:00+00:00Z",
                            "version": "1.0.0",
                            "skip_test": False,
                        },
                        "result": {
                            "time": "2023-09-01T00:00:00+00:00Z",
                            "config": "log_level=DEBUG",
                            "version": "1.0.0",
                            "test_env": {"python==3.12": True},
                            "results": {
                                "validation": True,
                                "load": True,
                                "metadata": True,
                            },
                            "outputs": {
                                "validation": None,
                                "load": "",
                                "metadata": {
                                    "name": "name",
                                    "description": "desc",
                                    "homepage": "https://nonebot.dev",
                                    "type": "application",
                                    "supported_adapters": [
                                        "nonebot.adapters.onebot.v11"
                                    ],
                                },
                            },
                        },
                    },
                }
            ),
            True,
        )

        handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="registry"),
            issue=mock_issue,
        )
        await trigger_registry_update(handler, PublishType.PLUGIN)

    assert mocked_api["homepage"].called


async def test_trigger_registry_update_skip_test(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
):
    """跳过插件加载测试的情况"""
    from src.plugins.github.models import IssueHandler, RepoInfo
    from src.plugins.github.plugins.publish.utils import trigger_registry_update
    from src.providers.validation import PublishType

    mock_time = mocker.patch("src.providers.models.datetime")
    mock_now = mocker.MagicMock()
    mock_now.isoformat.return_value = "2023-09-01T00:00:00+00:00Z"
    mock_time.now.return_value = mock_now

    mock_issue = MockIssue(
        body=MockBody(type="plugin", skip=True).generate(),
        number=1,
    ).as_mock(mocker)

    mock_comment = mocker.MagicMock()
    mock_comment.body = "/skip"
    mock_comment.author_association = "OWNER"

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "owner", "repo": "registry", "issue_number": 1},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.repos.async_create_dispatch_event",
            snapshot(
                {
                    "repo": "registry",
                    "owner": "owner",
                    "event_type": "registry_update",
                    "client_payload": {
                        "type": PublishType.PLUGIN,
                        "registry": {
                            "module_name": "module_name",
                            "project_link": "project_link",
                            "name": "name",
                            "desc": "desc",
                            "author": "test",
                            "homepage": "https://nonebot.dev",
                            "tags": [{"label": "test", "color": "#ffffff"}],
                            "is_official": False,
                            "type": "application",
                            "supported_adapters": ["nonebot.adapters.onebot.v11"],
                            "valid": True,
                            "time": "2023-09-01T00:00:00+00:00Z",
                            "version": "0.0.1",
                            "skip_test": True,
                        },
                        "result": {
                            "time": "2023-09-01T00:00:00+00:00Z",
                            "config": "log_level=DEBUG",
                            "version": "0.0.1",
                            "test_env": {"python==3.12": True},
                            "results": {
                                "validation": True,
                                "load": True,
                                "metadata": True,
                            },
                            "outputs": {
                                "validation": None,
                                "load": "插件未进行测试",
                                "metadata": {
                                    "name": "name",
                                    "description": "desc",
                                    "homepage": "https://nonebot.dev",
                                    "type": "application",
                                    "supported_adapters": [
                                        "nonebot.adapters.onebot.v11"
                                    ],
                                },
                            },
                        },
                    },
                }
            ),
            True,
        )

        handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="registry"),
            issue=mock_issue,
        )
        await trigger_registry_update(handler, PublishType.PLUGIN)


async def test_trigger_registry_update_bot(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
):
    """机器人发布的情况

    已经有相同机器人的时候，registry_update 不会影响到机器人的测试
    """
    from src.plugins.github.models import IssueHandler, RepoInfo
    from src.plugins.github.plugins.publish.utils import trigger_registry_update
    from src.providers.validation import PublishType

    mock_issue = MockIssue(
        body=MockBody(type="bot", homepage="https://v2.nonebot.dev").generate(),
        number=1,
    ).as_mock(mocker)

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        ctx.should_call_api(
            "rest.repos.async_create_dispatch_event",
            snapshot(
                {
                    "repo": "registry",
                    "owner": "owner",
                    "event_type": "registry_update",
                    "client_payload": {
                        "type": PublishType.BOT,
                        "registry": {
                            "name": "name",
                            "desc": "desc",
                            "author": "test",
                            "homepage": "https://v2.nonebot.dev",
                            "tags": [{"label": "test", "color": "#ffffff"}],
                            "is_official": False,
                        },
                        "result": None,
                    },
                }
            ),
            True,
        )

        handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="registry"),
            issue=mock_issue,
        )

        await trigger_registry_update(handler, PublishType.BOT)

    assert mocked_api["homepage_v2"].called


async def test_trigger_registry_update_plugins_issue_body_info_missing(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
):
    """如果议题信息不全，应该不会触发更新"""
    from githubkit.rest import Issue

    from src.plugins.github.models import IssueHandler, RepoInfo
    from src.plugins.github.plugins.publish.utils import trigger_registry_update
    from src.providers.docker_test import Metadata
    from src.providers.validation import PublishType

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.state = "open"
    mock_issue.body = "### 插件配置项\n\n```dotenv\nlog_level=DEBUG\n```"
    mock_issue.number = 1

    mock_user = mocker.MagicMock()
    mock_user.login = "test"
    mock_user.id = 1
    mock_issue.user = mock_user

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_test_result = mocker.MagicMock()
    mock_test_result.metadata = Metadata(
        name="name",
        desc="desc",
        homepage="https://nonebot.dev",
        type="application",
        supported_adapters=["~onebot.v11"],
    )
    mock_test_result.load = True
    mock_test_result.output = ""
    mock_docker = mocker.patch("src.providers.docker_test.DockerPluginTest.run")
    mock_docker.return_value = mock_test_result

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "owner", "repo": "registry", "issue_number": 1},
            mock_list_comments_resp,
        )

        handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="registry"),
            issue=mock_issue,
        )

        await trigger_registry_update(handler, PublishType.PLUGIN)

    assert mocked_api["homepage"].called


async def test_trigger_registry_update_validation_failed(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
):
    """验证失败时也不会触发更新"""
    from src.plugins.github.models import IssueHandler, RepoInfo
    from src.plugins.github.plugins.publish.utils import trigger_registry_update
    from src.providers.validation import PublishType

    mock_issue = MockIssue(
        1, body=generate_issue_body_plugin_skip_test(homepage="https://www.baidu.com")
    ).as_mock(mocker)

    mock_comment = mocker.MagicMock()
    mock_comment.body = "/skip"
    mock_comment.author_association = "OWNER"

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "owner", "repo": "registry", "issue_number": 1},
            mock_list_comments_resp,
        )
        handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="registry"),
            issue=mock_issue,
        )
        await trigger_registry_update(handler, PublishType.PLUGIN)

    assert mocked_api["homepage_failed"].called
