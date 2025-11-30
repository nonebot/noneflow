from unittest.mock import MagicMock

from inline_snapshot import snapshot
from nonebot.adapters.github import PullRequestClosed
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.plugins.github.event import get_mock_event
from tests.plugins.github.resolve.utils import get_pr_labels
from tests.plugins.github.utils import (
    MockIssue,
    assert_subprocess_run_calls,
    generate_issue_body_remove,
    get_github_bot,
    mock_subprocess_run_with_side_effect,
)


async def test_resolve_close_issue(
    app: App,
    mocker: MockerFixture,
    mock_installation: MagicMock,
    mock_installation_token: MagicMock,
    mocked_api: MockRouter,
) -> None:
    """测试能正确关闭议题"""
    from src.plugins.github.plugins.resolve import pr_close_matcher

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)
    mock_resolve_conflict_pull_requests = mocker.patch(
        "src.plugins.github.plugins.resolve.resolve_conflict_pull_requests"
    )

    mock_issue = MockIssue(
        body=generate_issue_body_remove(type="Bot"), number=76
    ).as_mock(mocker)
    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    async with app.test_matcher() as ctx:
        _adapter, bot = get_github_bot(ctx)

        event = get_mock_event(PullRequestClosed)
        event.payload.pull_request.labels = get_pr_labels(["Publish", "Bot"])
        event.payload.pull_request.merged = False

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            snapshot({"owner": "he0119", "repo": "action-test"}),
            mock_installation,
        )
        ctx.should_call_api(
            "rest.apps.async_create_installation_access_token",
            snapshot({"installation_id": mock_installation.parsed_data.id}),
            mock_installation_token,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            snapshot({"owner": "he0119", "repo": "action-test", "issue_number": 76}),
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 76,
                    "state": "closed",
                    "state_reason": "not_planned",
                }
            ),
            mock_issues_resp,
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_rule(pr_close_matcher)

    # 测试 git 命令
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
            ["git", "push", "origin", "--delete", "publish/issue76"],
        ],
    )

    assert not mocked_api["homepage"].called
    mock_resolve_conflict_pull_requests.assert_not_awaited()


async def test_resolve_close_issue_already_closed(
    app: App,
    mocker: MockerFixture,
    mock_installation: MagicMock,
    mock_installation_token: MagicMock,
    mocked_api: MockRouter,
) -> None:
    """测试议题已经关闭的情况

    需要再关闭一次议题，设置为 not_planned
    """
    from src.plugins.github.plugins.resolve import pr_close_matcher

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)
    mock_resolve_conflict_pull_requests = mocker.patch(
        "src.plugins.github.plugins.resolve.resolve_conflict_pull_requests"
    )

    mock_issue = MockIssue(
        body=generate_issue_body_remove(type="Bot"),
        number=76,
        state="closed",
        state_reason="completed",
    ).as_mock(mocker)
    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    async with app.test_matcher() as ctx:
        _adapter, bot = get_github_bot(ctx)

        event = get_mock_event(PullRequestClosed)
        event.payload.pull_request.labels = get_pr_labels(["Publish", "Bot"])
        event.payload.pull_request.merged = False

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            snapshot({"owner": "he0119", "repo": "action-test"}),
            mock_installation,
        )
        ctx.should_call_api(
            "rest.apps.async_create_installation_access_token",
            snapshot({"installation_id": mock_installation.parsed_data.id}),
            mock_installation_token,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            snapshot({"owner": "he0119", "repo": "action-test", "issue_number": 76}),
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 76,
                    "state": "closed",
                    "state_reason": "not_planned",
                }
            ),
            mock_issues_resp,
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_rule(pr_close_matcher)

    # 测试 git 命令
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
            ["git", "push", "origin", "--delete", "publish/issue76"],
        ],
    )

    assert not mocked_api["homepage"].called
    mock_resolve_conflict_pull_requests.assert_not_awaited()
