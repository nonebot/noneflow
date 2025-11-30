from inline_snapshot import snapshot
from nonebot.adapters.github import PullRequestClosed
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.plugins.github.event import get_mock_event
from tests.plugins.github.utils import (
    MockBody,
    MockIssue,
    assert_subprocess_run_calls,
    get_github_bot,
    mock_subprocess_run_with_side_effect,
)


async def test_process_pull_request(
    app: App,
    mocker: MockerFixture,
    mock_installation,
    mock_installation_token,
    mocked_api: MockRouter,
) -> None:
    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_issue = MockIssue(body=MockBody("plugin").generate()).as_mock(mocker)

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

    mock_comment_bot = mocker.MagicMock()
    mock_comment_bot.body = """
<details>\n<summary>历史测试</summary>
<pre><code>
<li>⚠️ <a href="https://github.com/nonebot/nonebot2/actions/runs/1">2025-03-28 02:21:18 CST</a></li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/2">2025-03-28 02:21:18 CST</a></li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/3">2025-03-28 02:22:18 CST</a></li><li>⚠️ <a href="https://github.com/nonebot/nonebot2/actions/runs/4">2025-03-28 02:22:18 CST</a></li>
</code></pre>
</details>
<!-- NONEFLOW -->
"""
    mock_comment_bot.id = 123

    mock_comment_user = mocker.MagicMock()
    mock_comment_user.body = "user comment"
    mock_comment_user.id = 456

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment_bot, mock_comment_user]

    mock_artifact = mocker.MagicMock()
    mock_artifact.name = "noneflow"
    mock_artifact.id = 233

    mock_list_artifacts_data = mocker.MagicMock()
    mock_list_artifacts_data.total_count = 1
    mock_list_artifacts_data.artifacts = [mock_artifact]

    mock_list_artifacts_resp = mocker.MagicMock()
    mock_list_artifacts_resp.parsed_data = mock_list_artifacts_data

    async with app.test_matcher() as ctx:
        _adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestClosed)
        event.payload.pull_request.merged = True

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
            "rest.issues.async_list_comments",
            snapshot({"owner": "he0119", "repo": "action-test", "issue_number": 80}),
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.actions.async_list_workflow_run_artifacts",
            snapshot({"owner": "he0119", "repo": "action-test", "run_id": 3}),
            mock_list_artifacts_resp,
        )
        ctx.should_call_api(
            "rest.repos.async_create_dispatch_event",
            snapshot(
                {
                    "owner": "owner",
                    "repo": "registry",
                    "event_type": "registry_update",
                    "client_payload": {
                        "repo_info": {"owner": "he0119", "repo": "action-test"},
                        "artifact_id": 233,
                    },
                }
            ),
            None,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 80,
                    "state": "closed",
                    "state_reason": "completed",
                }
            ),
            None,
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            snapshot({"owner": "he0119", "repo": "action-test", "state": "open"}),
            mock_pulls_resp,
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


async def test_process_pull_request_not_merged(
    app: App, mocker: MockerFixture, mock_installation, mock_installation_token
) -> None:
    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_issue = MockIssue().as_mock(mocker)

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    async with app.test_matcher() as ctx:
        _adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestClosed)
        assert isinstance(event, PullRequestClosed)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.apps.async_create_installation_access_token",
            {"installation_id": mock_installation.parsed_data.id},
            mock_installation_token,
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


async def test_not_publish(app: App, mocker: MockerFixture) -> None:
    """测试与发布无关的拉取请求"""
    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    async with app.test_matcher() as ctx:
        _adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestClosed)
        event.payload.pull_request.labels = []

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()


async def test_extract_issue_number_from_ref_failed(
    app: App, mocker: MockerFixture
) -> None:
    """测试从分支名中提取议题号失败"""

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    async with app.test_matcher() as ctx:
        _adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestClosed)
        event.payload.pull_request.head.ref = "1"

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()
