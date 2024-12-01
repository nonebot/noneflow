from inline_snapshot import snapshot
from nonebot.adapters.github import PullRequestClosed
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.github.event import get_mock_event
from tests.github.utils import (
    MockBody,
    MockIssue,
    MockUser,
    generate_issue_body_plugin_skip_test,
    get_github_bot,
)


async def test_process_pull_request(
    app: App,
    mocker: MockerFixture,
    mock_installation,
    mocked_api: MockRouter,
) -> None:
    from src.providers.docker_test import Metadata
    from src.providers.validation import PublishType

    mock_time = mocker.patch("src.providers.models.datetime")
    mock_now = mocker.MagicMock()
    mock_now.isoformat.return_value = "2023-09-01T00:00:00+00:00Z"
    mock_time.now.return_value = mock_now

    mock_subprocess_run = mocker.patch("subprocess.run")

    mock_issue = MockIssue(body=MockBody("plugin").generate()).as_mock(mocker)

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

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

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestClosed)
        event.payload.pull_request.merged = True

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 76},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
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
                            "time": "2023-09-01T00:00:00+00:00",
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
        ctx.should_call_api(
            "rest.issues.async_update",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "state": "closed",
                "state_reason": "completed",
            },
            True,
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {"owner": "he0119", "repo": "action-test", "state": "open"},
            mock_pulls_resp,
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
                ["git", "push", "origin", "--delete", "publish/issue76"],
                check=True,
                capture_output=True,
            ),
        ],  # type: ignore
        any_order=True,
    )


async def test_process_pull_request_not_merged(
    app: App, mocker: MockerFixture, mock_installation
) -> None:
    mock_subprocess_run = mocker.patch("subprocess.run")

    mock_issue = MockIssue().as_mock(mocker)

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestClosed)
        assert isinstance(event, PullRequestClosed)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 76},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "state": "closed",
                "state_reason": "not_planned",
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
                ["git", "push", "origin", "--delete", "publish/issue76"],
                check=True,
                capture_output=True,
            ),
        ],  # type: ignore
        any_order=True,
    )


async def test_process_pull_request_skip_plugin_test(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, mock_installation
) -> None:
    """跳过测试的插件合并时的情况"""
    from src.providers.validation import PublishType

    mock_time = mocker.patch("src.providers.models.datetime")
    mock_now = mocker.MagicMock()
    mock_now.isoformat.return_value = "2023-09-01T00:00:00+00:00Z"
    mock_time.now.return_value = mock_now

    mock_subprocess_run = mocker.patch("subprocess.run")

    mock_issue = MockIssue(
        body=generate_issue_body_plugin_skip_test(), user=MockUser(login="user", id=1)
    ).as_mock(mocker)

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

    mock_comment = mocker.MagicMock()
    mock_comment.body = "/skip"
    mock_comment.author_association = "OWNER"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestClosed)
        event.payload.pull_request.merged = True

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 76},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
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
                            "author": "user",
                            "homepage": "https://nonebot.dev",
                            "tags": [{"label": "test", "color": "#ffffff"}],
                            "is_official": False,
                            "type": "application",
                            "supported_adapters": ["nonebot.adapters.onebot.v11"],
                            "valid": True,
                            "time": "2023-09-01T00:00:00+00:00",
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
        ctx.should_call_api(
            "rest.issues.async_update",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "state": "closed",
                "state_reason": "completed",
            },
            True,
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {"owner": "he0119", "repo": "action-test", "state": "open"},
            mock_pulls_resp,
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
                ["git", "push", "origin", "--delete", "publish/issue76"],
                check=True,
                capture_output=True,
            ),
        ],  # type: ignore
        any_order=True,
    )


async def test_not_publish(app: App, mocker: MockerFixture) -> None:
    """测试与发布无关的拉取请求"""
    mock_subprocess_run = mocker.patch("subprocess.run")

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestClosed)
        event.payload.pull_request.labels = []

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()


async def test_extract_issue_number_from_ref_failed(
    app: App, mocker: MockerFixture
) -> None:
    """测试从分支名中提取议题号失败"""

    mock_subprocess_run = mocker.patch("subprocess.run")

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestClosed)
        event.payload.pull_request.head.ref = "1"

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()
