from pathlib import Path
from unittest.mock import MagicMock

from inline_snapshot import snapshot
from nonebot.adapters.github import PullRequestClosed
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.plugins.github.event import get_mock_event
from tests.plugins.github.resolve.utils import get_pr_labels
from tests.plugins.github.utils import (
    GitHubApi,
    MockIssue,
    assert_subprocess_run_calls,
    generate_issue_body_bot,
    generate_issue_body_remove,
    get_github_bot,
    mock_subprocess_run_with_side_effect,
    should_call_apis,
)


async def test_resolve_pull_request(
    app: App,
    mocker: MockerFixture,
    mock_installation: MagicMock,
    mocked_api: MockRouter,
    tmp_path: Path,
) -> None:
    """测试能正确处理拉取请求关闭后其他拉取请求的冲突问题"""
    from src.plugins.github.plugins.resolve import pr_close_matcher

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_issue = MockIssue(
        body=generate_issue_body_remove(type="Bot"), number=76
    ).as_mock(mocker)
    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_publish_issue = MockIssue(body=generate_issue_body_bot(), number=100).as_mock(
        mocker
    )
    mock_publish_issue_resp = mocker.MagicMock()
    mock_publish_issue_resp.parsed_data = mock_publish_issue
    mock_publish_pull = mocker.MagicMock()
    mock_publish_pull.title = "Bot: test"
    mock_publish_pull.draft = False
    mock_publish_pull.head.ref = "publish/issue100"
    mock_publish_pull.labels = get_pr_labels(["Publish", "Bot"])
    mock_remove_issue = MockIssue(
        body=generate_issue_body_remove(
            type="Bot", key="CoolQBot:https://github.com/he0119/CoolQBot"
        ),
        number=101,
    ).as_mock(mocker)
    mock_remove_issue_resp = mocker.MagicMock()
    mock_remove_issue_resp.parsed_data = mock_remove_issue
    mock_remove_pull = mocker.MagicMock()
    mock_remove_pull.title = "Bot: remove CoolQBot"
    mock_remove_pull.draft = False
    mock_remove_pull.head.ref = "remove/issue101"
    mock_remove_pull.labels = get_pr_labels(["Remove", "Bot"])
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_publish_pull, mock_remove_pull]

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)

        event = get_mock_event(PullRequestClosed)
        event.payload.pull_request.labels = get_pr_labels(["Remove", "Bot"])
        event.payload.pull_request.merged = True

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.apps.async_get_repo_installation",
                    result=mock_installation,
                ),
                GitHubApi(
                    api="rest.issues.async_get",
                    result=mock_issues_resp,
                ),
                GitHubApi(
                    api="rest.issues.async_update",
                    result=True,
                ),
                GitHubApi(
                    api="rest.pulls.async_list",
                    result=mock_pulls_resp,
                ),
                GitHubApi(
                    api="rest.issues.async_get",
                    result=mock_publish_issue_resp,
                ),
                GitHubApi(
                    api="rest.issues.async_get",
                    result=mock_remove_issue_resp,
                ),
            ],
            snapshot(
                {
                    0: {"owner": "he0119", "repo": "action-test"},
                    1: {"owner": "he0119", "repo": "action-test", "issue_number": 76},
                    2: {
                        "owner": "he0119",
                        "repo": "action-test",
                        "issue_number": 76,
                        "state": "closed",
                        "state_reason": "completed",
                    },
                    3: {"owner": "he0119", "repo": "action-test", "state": "open"},
                    4: {"owner": "he0119", "repo": "action-test", "issue_number": 100},
                    5: {"owner": "he0119", "repo": "action-test", "issue_number": 101},
                }
            ),
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_rule(pr_close_matcher)

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "config", "--global", "safe.directory", "*"],
            ["git", "push", "origin", "--delete", "publish/issue76"],
            # 处理发布
            ["git", "checkout", "master"],
            ["git", "pull"],
            ["git", "switch", "-C", "publish/issue100"],
            ["git", "add", str(tmp_path / "bots.json5")],
            ["git", "config", "--global", "user.name", "test"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "test@users.noreply.github.com",
            ],
            ["git", "commit", "-m", ":beers: publish bot name (#100)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/publish/issue100", "publish/issue100"],
            ["git", "push", "origin", "publish/issue100", "-f"],
            # 处理移除
            ["git", "checkout", "master"],
            ["git", "pull"],
            ["git", "switch", "-C", "remove/issue101"],
            ["git", "add", str(tmp_path / "bots.json5")],
            ["git", "config", "--global", "user.name", "test"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "test@users.noreply.github.com",
            ],
            ["git", "commit", "-m", ":pencil2: remove CoolQBot (#101)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/remove/issue101", "remove/issue101"],
            ["git", "push", "origin", "remove/issue101", "-f"],
        ],
    )

    assert mocked_api["homepage"].called
