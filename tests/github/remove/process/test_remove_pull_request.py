from pathlib import Path
from unittest.mock import MagicMock

from nonebot.adapters.github import Adapter, PullRequestClosed
from nonebug import App
from pytest_mock import MockerFixture

from tests.github.utils import MockIssue, generate_issue_body_remove, get_github_bot


def get_remove_labels():
    from githubkit.rest import PullRequestPropLabelsItems as Label

    return [
        Label.model_construct(
            **{
                "color": "2A2219",
                "default": False,
                "description": "",
                "id": 2798075966,
                "name": "Remove",
                "node_id": "MDU6TGFiZWwyNzk4MDc1OTY2",
                "url": "https://api.github.com/repos/he0119/action-test/labels/Remove",
            }
        )
    ]


async def test_remove_process_pull_request(
    app: App, mocker: MockerFixture, mock_installation: MagicMock
) -> None:
    """删除流程的拉取请求关闭流程"""
    from src.plugins.github.plugins.remove import pr_close_matcher

    mock_subprocess_run = mocker.patch("subprocess.run")

    mock_issue = MockIssue(body=generate_issue_body_remove(), number=76).as_mock(mocker)

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    async with app.test_matcher(pr_close_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event_path = Path(__file__).parent.parent.parent / "events" / "pr-close.json"
        event = adapter.payload_to_event("1", "pull_request", event_path.read_bytes())
        assert isinstance(event, PullRequestClosed)
        event.payload.pull_request.labels = get_remove_labels()
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
                ["pre-commit", "install", "--install-hooks"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "push", "origin", "--delete", "publish/issue76"],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
        ],  # type: ignore
        any_order=True,
    )


async def test_not_remove(app: App, mocker: MockerFixture) -> None:
    """测试与发布无关的拉取请求"""
    from src.plugins.github.plugins.remove import pr_close_matcher

    event_path = Path(__file__).parent.parent.parent / "events" / "pr-close.json"

    mock_subprocess_run = mocker.patch("subprocess.run")

    async with app.test_matcher(pr_close_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event = Adapter.payload_to_event("1", "pull_request", event_path.read_bytes())
        assert isinstance(event, PullRequestClosed)
        event.payload.pull_request.labels = []

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()


async def test_process_remove_pull_request_not_merged(
    app: App, mocker: MockerFixture, mock_installation
) -> None:
    """删除掉不合并的分支"""
    from src.plugins.github.plugins.remove import pr_close_matcher

    event_path = Path(__file__).parent.parent.parent / "events" / "pr-close.json"

    mock_subprocess_run = mocker.patch("subprocess.run")

    mock_issue = MockIssue(body=generate_issue_body_remove(), number=76).as_mock(mocker)
    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    async with app.test_matcher(pr_close_matcher) as ctx:
        adapter, bot = get_github_bot(ctx)
        event = adapter.payload_to_event("1", "pull_request", event_path.read_bytes())
        assert isinstance(event, PullRequestClosed)
        event.payload.pull_request.labels = get_remove_labels()

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
                ["pre-commit", "install", "--install-hooks"],
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
