from nonebot.adapters.github import PullRequestReviewSubmitted
from nonebug import App
from pytest_mock import MockerFixture

from tests.plugins.github.event import get_mock_event
from tests.plugins.github.utils import (
    assert_subprocess_run_calls,
    get_github_bot,
    mock_subprocess_run_with_side_effect,
    should_call_apis,
)


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
    app: App, mocker: MockerFixture, mock_installation, mock_installation_token
) -> None:
    """测试审查后自动合并

    可直接合并的情况
    """
    from src.plugins.github.plugins.config import auto_merge_matcher

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    async with app.test_matcher() as ctx:
        _adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestReviewSubmitted)
        event.payload.pull_request.labels = get_issue_labels(["Config", "Plugin"])

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
                    "api": "rest.pulls.async_merge",
                    "result": True,
                },
            ],
            [
                {"owner": "he0119", "repo": "action-test"},
                {"installation_id": mock_installation.parsed_data.id},
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "pull_number": 100,
                    "merge_method": "rebase",
                },
            ],
        )

        ctx.receive_event(bot, event)
        ctx.should_pass_rule(auto_merge_matcher)

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [["git", "config", "--global", "safe.directory", "*"]],
    )


async def test_auto_merge_not_remove(app: App, mocker: MockerFixture) -> None:
    """测试审查后自动合并

    和配置无关
    """
    from src.plugins.github.plugins.config import auto_merge_matcher

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    async with app.test_matcher() as ctx:
        _adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestReviewSubmitted)
        event.payload.pull_request.labels = []

        ctx.receive_event(bot, event)
        ctx.should_not_pass_rule(auto_merge_matcher)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()


async def test_auto_merge_not_member(app: App, mocker: MockerFixture) -> None:
    """测试审查后自动合并

    审核者不是仓库成员
    """
    from src.plugins.github.plugins.config import auto_merge_matcher

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    async with app.test_matcher() as ctx:
        _adapter, bot = get_github_bot(ctx)
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

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    async with app.test_matcher() as ctx:
        _adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestReviewSubmitted)
        event.payload.pull_request.labels = get_issue_labels(["Config", "Plugin"])
        event.payload.review.state = "commented"

        ctx.receive_event(bot, event)
        ctx.should_not_pass_rule(auto_merge_matcher)

    # 测试 git 命令

    mock_subprocess_run.assert_not_called()
