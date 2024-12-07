from typing import Any, NotRequired, TypedDict
from unittest.mock import MagicMock, _Call, call

from inline_snapshot import snapshot
from nonebot.adapters.github import PullRequestClosed
from nonebug import App
from nonebug.mixin.process import MatcherContext
from pytest_mock import MockerFixture, MockType

from tests.plugins.github.event import get_mock_event
from tests.plugins.github.resolve.utils import get_pr_labels
from tests.plugins.github.utils import (
    MockIssue,
    generate_issue_body_remove,
    get_github_bot,
)


class GitHubApi(TypedDict):
    api: str
    result: Any | None
    exception: NotRequired[Exception | None]


def should_call_api(ctx: MatcherContext, apis: list[GitHubApi], data: Any) -> None:
    for api in apis:
        ctx.should_call_api(**api, data=data[api["api"]])


def assert_subprocess_run_calls(mock: MockType, commands: list[list[str]]):
    calls = []
    for command in commands:
        calls.append(call(command, check=True, capture_output=True))
        calls.append(call().stdout.decode())
        calls.append(_Call(("().stdout.decode().__str__", (), {})))

    mock.assert_has_calls(calls)


async def test_resolve_pull_request(
    app: App, mocker: MockerFixture, mock_installation: MagicMock
) -> None:
    """删除流程的拉取请求关闭流程"""
    mock_subprocess_run = mocker.patch("subprocess.run")

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

        should_call_api(
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
            ],
            snapshot(
                {
                    "rest.apps.async_get_repo_installation": {
                        "owner": "he0119",
                        "repo": "action-test",
                    },
                    "rest.issues.async_get": {
                        "owner": "he0119",
                        "repo": "action-test",
                        "issue_number": 76,
                    },
                    "rest.issues.async_update": {
                        "owner": "he0119",
                        "repo": "action-test",
                        "issue_number": 76,
                        "state": "closed",
                        "state_reason": "completed",
                    },
                    "rest.pulls.async_list": {
                        "owner": "he0119",
                        "repo": "action-test",
                        "state": "open",
                    },
                }
            ),
        )
        ctx.receive_event(bot, event)

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "config", "--global", "safe.directory", "*"],
            ["git", "push", "origin", "--delete", "publish/issue76"],
        ],
    )
