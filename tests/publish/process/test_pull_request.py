from pathlib import Path
from typing import cast

from nonebot import get_adapter
from nonebot.adapters.github import Adapter, GitHubBot, PullRequestClosed
from nonebot.adapters.github.config import GitHubApp
from nonebug import App
from pytest_mock import MockerFixture


async def test_process_pull_request(app: App, mocker: MockerFixture) -> None:
    from src.plugins.publish import pr_close_matcher

    event_path = Path(__file__).parent.parent / "events" / "pr-close.json"

    mock_subprocess_run = mocker.patch("subprocess.run")

    mock_issue = mocker.MagicMock()
    mock_issue.state = "open"

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123

    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

    async with app.test_matcher(pr_close_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event = Adapter.payload_to_event("1", "pull_request", event_path.read_bytes())
        assert isinstance(event, PullRequestClosed)
        event.payload.pull_request.merged = True

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation_resp,
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
                },
            },
            True,
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
                "issue_number": 76,
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


async def test_process_pull_request_not_merged(app: App, mocker: MockerFixture) -> None:
    from src.plugins.publish import pr_close_matcher

    event_path = Path(__file__).parent.parent / "events" / "pr-close.json"

    mock_subprocess_run = mocker.patch("subprocess.run")

    mock_issue = mocker.MagicMock()
    mock_issue.state = "open"

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123

    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    async with app.test_matcher(pr_close_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event = Adapter.payload_to_event("1", "pull_request", event_path.read_bytes())
        assert isinstance(event, PullRequestClosed)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation_resp,
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
                "issue_number": 76,
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


async def test_not_publish(app: App, mocker: MockerFixture) -> None:
    """测试与发布无关的拉取请求"""
    from src.plugins.publish import pr_close_matcher

    event_path = Path(__file__).parent.parent / "events" / "pr-close.json"

    mock_subprocess_run = mocker.patch("subprocess.run")

    async with app.test_matcher(pr_close_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event = Adapter.payload_to_event("1", "pull_request", event_path.read_bytes())
        assert isinstance(event, PullRequestClosed)
        event.payload.pull_request.labels = []

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()


async def test_extract_issue_number_from_ref_failed(
    app: App, mocker: MockerFixture
) -> None:
    """测试从分支名中提取议题号失败"""
    from src.plugins.publish import pr_close_matcher

    event_path = Path(__file__).parent.parent / "events" / "pr-close.json"

    mock_subprocess_run = mocker.patch("subprocess.run")

    async with app.test_matcher(pr_close_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event = Adapter.payload_to_event("1", "pull_request", event_path.read_bytes())
        assert isinstance(event, PullRequestClosed)
        event.payload.pull_request.head.ref = "1"

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()
    mock_subprocess_run.assert_not_called()
