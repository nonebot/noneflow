from nonebot.adapters.github import PullRequestReviewSubmitted
from nonebug import App
from pytest_mock import MockerFixture

from tests.github.event import get_mock_event
from tests.github.utils import get_github_bot


def get_issue_labels(labels: list[str]):
    from githubkit.rest import (
        WebhookPullRequestReviewSubmittedPropPullRequestPropLabelsItems as Label,
    )

    return [
        Label.model_construct(
            **{
                "color": "2A2219",
                "default": False,
                "description": "",
                "id": 2798075966,
                "name": label,
                "node_id": "MDU6TGFiZWwyNzk4MDc1OTY2",
                "url": "https://api.github.com/repos/he0119/action-test/labels/Config",
            }
        )
        for label in labels
    ]


async def test_config_auto_merge(
    app: App, mocker: MockerFixture, mock_installation
) -> None:
    """测试审查后自动合并

    可直接合并的情况
    """
    from src.plugins.github.plugins.config import auto_merge_matcher

    mock_subprocess_run = mocker.patch("subprocess.run")

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestReviewSubmitted)
        event.payload.pull_request.labels = get_issue_labels(["Config", "Plugin"])

        ctx.receive_event(bot, event)
        ctx.should_pass_rule(auto_merge_matcher)
        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.pulls.async_merge",
            {
                "owner": "he0119",
                "repo": "action-test",
                "pull_number": 100,
                "merge_method": "rebase",
            },
            True,
        )

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
        ],  # type: ignore
        any_order=True,
    )


async def test_auto_merge_not_remove(app: App, mocker: MockerFixture) -> None:
    """测试审查后自动合并

    和配置无关
    """
    from src.plugins.github.plugins.config import auto_merge_matcher

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_resolve_conflict_pull_requests = mocker.patch(
        "src.plugins.github.plugins.remove.resolve_conflict_pull_requests"
    )

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestReviewSubmitted)
        event.payload.pull_request.labels = []
        ctx.receive_event(bot, event)
        ctx.should_not_pass_rule(auto_merge_matcher)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()
    mock_resolve_conflict_pull_requests.assert_not_called()


async def test_auto_merge_not_member(app: App, mocker: MockerFixture) -> None:
    """测试审查后自动合并

    审核者不是仓库成员
    """
    from src.plugins.github.plugins.config import auto_merge_matcher

    mock_subprocess_run = mocker.patch("subprocess.run")

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestReviewSubmitted)
        event.payload.review.author_association = "CONTRIBUTOR"
        event.payload.pull_request.labels = get_issue_labels(["Config", "Plugin"])

        ctx.receive_event(bot, event)
        ctx.should_not_pass_rule(auto_merge_matcher)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()


async def test_auto_merge_not_approve(app: App, mocker: MockerFixture) -> None:
    """测试审查后自动合并

    审核未通过
    """
    from src.plugins.github.plugins.config import auto_merge_matcher

    mock_subprocess_run = mocker.patch("subprocess.run")

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestReviewSubmitted)
        event.payload.pull_request.labels = get_issue_labels(["Config", "Plugin"])
        event.payload.review.state = "commented"

        ctx.receive_event(bot, event)
        ctx.should_not_pass_rule(auto_merge_matcher)

    # 测试 git 命令

    mock_subprocess_run.assert_not_called()
