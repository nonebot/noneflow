from unittest.mock import MagicMock

from nonebot.adapters.github import PullRequestClosed
from nonebug import App
from pytest_mock import MockerFixture

from tests.plugins.github.event import get_mock_event
from tests.plugins.github.resolve.utils import get_pr_labels
from tests.plugins.github.utils import (
    MockIssue,
    assert_subprocess_run_calls,
    generate_issue_body_remove,
    get_github_bot,
    mock_subprocess_run_with_side_effect,
    should_call_apis,
)


async def test_remove_process_pull_request(
    app: App,
    mocker: MockerFixture,
    mock_installation: MagicMock,
    mock_installation_token: MagicMock,
) -> None:
    """删除流程的拉取请求关闭流程"""
    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    remove_type = "Bot"
    mock_issue = MockIssue(
        body=generate_issue_body_remove(type=remove_type), number=76
    ).as_mock(mocker)

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)

        event = get_mock_event(PullRequestClosed)
        event.payload.pull_request.labels = get_pr_labels(["Remove", "Bot"])
        event.payload.pull_request.merged = True

        should_call_apis(
            ctx,
            [
                {
                    "api": "rest.apps.async_get_repo_installation",
                    "result": mock_installation,
                },
                {
                    "api": "rest.apps.async_create_installation_access_token",
                    "result": mock_installation_token,
                },
                {
                    "api": "rest.issues.async_get",
                    "result": mock_issues_resp,
                },
                {
                    "api": "rest.issues.async_update",
                    "result": True,
                },
                {
                    "api": "rest.pulls.async_list",
                    "result": mock_pulls_resp,
                },
            ],
            [
                {"owner": "he0119", "repo": "action-test"},
                {"installation_id": mock_installation.parsed_data.id},
                {"owner": "he0119", "repo": "action-test", "issue_number": 76},
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 76,
                    "state": "closed",
                    "state_reason": "completed",
                },
                {"owner": "he0119", "repo": "action-test", "state": "open"},
            ],
        )
        ctx.receive_event(bot, event)

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


async def test_not_remove(app: App, mocker: MockerFixture) -> None:
    """测试与发布无关的拉取请求"""

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestClosed)
        event.payload.pull_request.labels = []

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()


async def test_process_remove_pull_request_not_merged(
    app: App, mocker: MockerFixture, mock_installation, mock_installation_token
) -> None:
    """删除掉不合并的分支"""
    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    remove_type = "Bot"
    mock_issue = MockIssue(
        body=generate_issue_body_remove(type=remove_type, key="TEST:omg"), number=76
    ).as_mock(mocker)
    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestClosed)
        event.payload.pull_request.labels = get_pr_labels(["Remove", "Bot"])

        should_call_apis(
            ctx,
            [
                {
                    "api": "rest.apps.async_get_repo_installation",
                    "result": mock_installation,
                },
                {
                    "api": "rest.apps.async_create_installation_access_token",
                    "result": mock_installation_token,
                },
                {
                    "api": "rest.issues.async_get",
                    "result": mock_issues_resp,
                },
                {
                    "api": "rest.issues.async_update",
                    "result": True,
                },
            ],
            [
                {"owner": "he0119", "repo": "action-test"},
                {"installation_id": mock_installation.parsed_data.id},
                {"owner": "he0119", "repo": "action-test", "issue_number": 76},
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 76,
                    "state": "closed",
                    "state_reason": "not_planned",
                },
            ],
        )

        ctx.receive_event(bot, event)

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
