from nonebot.adapters.github import PullRequestReviewSubmitted
from nonebug import App
from pytest_mock import MockerFixture

from tests.plugins.github.event import get_mock_event
from tests.plugins.github.utils import get_github_bot


async def test_auto_merge(app: App, mocker: MockerFixture, mock_installation) -> None:
    """测试审查后自动合并

    可直接合并的情况
    """
    from src.plugins.github.plugins.publish import auto_merge_matcher

    mock_subprocess_run = mocker.patch("subprocess.run")

    mock_pull = mocker.MagicMock()
    mock_pull.mergeable = True
    mock_pull_resp = mocker.MagicMock()
    mock_pull_resp.parsed_data = mock_pull

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestReviewSubmitted)

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

        ctx.receive_event(bot, event)
        ctx.should_pass_rule(auto_merge_matcher)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),  # type: ignore
        ],
        any_order=True,
    )


async def test_auto_merge_not_publish(app: App, mocker: MockerFixture) -> None:
    """测试审查后自动合并

    和发布无关
    """
    from src.plugins.github.plugins.publish import auto_merge_matcher

    mock_subprocess_run = mocker.patch("subprocess.run")

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
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
    from src.plugins.github.plugins.publish import auto_merge_matcher

    mock_subprocess_run = mocker.patch("subprocess.run")

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestReviewSubmitted)
        event.payload.review.author_association = "CONTRIBUTOR"

        ctx.receive_event(bot, event)
        ctx.should_not_pass_rule(auto_merge_matcher)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()


async def test_auto_merge_not_approve(app: App, mocker: MockerFixture) -> None:
    """测试审查后自动合并

    审核未通过
    """
    from src.plugins.github.plugins.publish import auto_merge_matcher

    mock_subprocess_run = mocker.patch("subprocess.run")

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(PullRequestReviewSubmitted)
        event.payload.review.state = "commented"

        ctx.receive_event(bot, event)
        ctx.should_not_pass_rule(auto_merge_matcher)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()