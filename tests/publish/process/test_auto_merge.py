from pathlib import Path
from typing import cast

from nonebot import get_adapter
from nonebot.adapters.github import Adapter, GitHubBot, PullRequestReviewSubmitted
from nonebot.adapters.github.config import GitHubApp
from nonebug import App
from pytest_mock import MockerFixture


async def test_auto_merge(app: App, mocker: MockerFixture) -> None:
    """测试审查后自动合并

    可直接合并的情况
    """
    from src.plugins.publish import auto_merge_matcher

    mock_subprocess_run = mocker.patch("subprocess.run")

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_pull = mocker.MagicMock()
    mock_pull.mergeable = True
    mock_pull_resp = mocker.MagicMock()
    mock_pull_resp.parsed_data = mock_pull

    async with app.test_matcher(auto_merge_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = (
            Path(__file__).parent.parent
            / "events"
            / "pull_request_review_submitted.json"
        )
        event = Adapter.payload_to_event(
            "1", "pull_request_review", event_path.read_bytes()
        )
        assert isinstance(event, PullRequestReviewSubmitted)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation_resp,
        )
        ctx.should_call_api(
            "rest.pulls.async_get",
            {"owner": "he0119", "repo": "action-test", "pull_number": 100},
            mock_pull_resp,
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


async def test_auto_merge_need_rebase(app: App, mocker: MockerFixture) -> None:
    """测试审查后自动合并

    需要 rebase 的情况
    """
    from src.plugins.publish import auto_merge_matcher

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_resolve_conflict_pull_requests = mocker.patch(
        "src.plugins.publish.resolve_conflict_pull_requests"
    )

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_pull = mocker.MagicMock()
    mock_pull.mergeable = False
    mock_pull.head.ref = "publish/issue1"
    mock_pull_resp = mocker.MagicMock()
    mock_pull_resp.parsed_data = mock_pull

    async with app.test_matcher(auto_merge_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = (
            Path(__file__).parent.parent
            / "events"
            / "pull_request_review_submitted.json"
        )
        event = Adapter.payload_to_event(
            "1", "pull_request_review", event_path.read_bytes()
        )
        assert isinstance(event, PullRequestReviewSubmitted)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation_resp,
        )
        ctx.should_call_api(
            "rest.pulls.async_get",
            {"owner": "he0119", "repo": "action-test", "pull_number": 100},
            mock_pull_resp,
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

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "fetch", "origin", "master"],
                check=True,
                capture_output=True,
            ),  # type: ignore
        ],
        any_order=True,
    )
    mock_resolve_conflict_pull_requests.assert_called_once_with([mock_pull])


async def test_auto_merge_not_publish(app: App, mocker: MockerFixture) -> None:
    """测试审查后自动合并

    和发布无关
    """
    from src.plugins.publish import auto_merge_matcher

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_resolve_conflict_pull_requests = mocker.patch(
        "src.plugins.publish.resolve_conflict_pull_requests"
    )

    async with app.test_matcher(auto_merge_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = (
            Path(__file__).parent.parent
            / "events"
            / "pull_request_review_submitted.json"
        )
        event = Adapter.payload_to_event(
            "1", "pull_request_review", event_path.read_bytes()
        )
        assert isinstance(event, PullRequestReviewSubmitted)
        event.payload.pull_request.labels = []

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()
    mock_resolve_conflict_pull_requests.assert_not_called()


async def test_auto_merge_not_member(app: App, mocker: MockerFixture) -> None:
    """测试审查后自动合并

    审核者不是仓库成员
    """
    from src.plugins.publish import auto_merge_matcher

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_resolve_conflict_pull_requests = mocker.patch(
        "src.plugins.publish.resolve_conflict_pull_requests"
    )

    async with app.test_matcher(auto_merge_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = (
            Path(__file__).parent.parent
            / "events"
            / "pull_request_review_submitted.json"
        )
        event = Adapter.payload_to_event(
            "1", "pull_request_review", event_path.read_bytes()
        )
        assert isinstance(event, PullRequestReviewSubmitted)
        event.payload.review.author_association = "CONTRIBUTOR"

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()
    mock_resolve_conflict_pull_requests.assert_not_called()


async def test_auto_merge_not_approve(app: App, mocker: MockerFixture) -> None:
    """测试审查后自动合并

    审核未通过
    """
    from src.plugins.publish import auto_merge_matcher

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_resolve_conflict_pull_requests = mocker.patch(
        "src.plugins.publish.resolve_conflict_pull_requests"
    )

    async with app.test_matcher(auto_merge_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = (
            Path(__file__).parent.parent
            / "events"
            / "pull_request_review_submitted.json"
        )
        event = Adapter.payload_to_event(
            "1", "pull_request_review", event_path.read_bytes()
        )
        assert isinstance(event, PullRequestReviewSubmitted)
        event.payload.review.state = "commented"

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()
    mock_resolve_conflict_pull_requests.assert_not_called()
