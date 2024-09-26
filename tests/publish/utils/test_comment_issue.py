from typing import cast

from nonebot import get_adapter
from nonebot.adapters.github import Adapter, GitHubBot
from nonebot.adapters.github.config import GitHubApp
from nonebug import App
from pytest_mock import MockerFixture


async def test_comment_issue(app: App, mocker: MockerFixture):
    from src.plugins.github.models import RepoInfo, GithubHandler

    render_comment = "test"

    mock_result = mocker.AsyncMock()
    mock_result.render_issue_comment.return_value = "test"

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "owner", "repo": "repo", "issue_number": 1},
            mock_list_comments_resp,
        )

        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "owner",
                "repo": "repo",
                "issue_number": 1,
                "body": "test",
            },
            True,
        )

        handler = GithubHandler(bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"))

        await handler.comment_issue(render_comment, 1)


async def test_comment_issue_reuse(app: App, mocker: MockerFixture):
    from src.plugins.github.constants import NONEFLOW_MARKER
    from src.plugins.github.models import RepoInfo, GithubHandler

    render_comment = "test"

    mock_result = mocker.AsyncMock()
    mock_result.render_issue_comment.return_value = "test"

    mock_comment = mocker.MagicMock()
    mock_comment.body = f"任意的东西\n{NONEFLOW_MARKER}\n"
    mock_comment.id = 123

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "owner", "repo": "repo", "issue_number": 1},
            mock_list_comments_resp,
        )

        ctx.should_call_api(
            "rest.issues.async_update_comment",
            {
                "owner": "owner",
                "repo": "repo",
                "comment_id": 123,
                "body": "test",
            },
            True,
        )

        handler = GithubHandler(bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"))

        await handler.comment_issue(render_comment, 1)


async def test_comment_issue_reuse_same(app: App, mocker: MockerFixture):
    """测试评论内容相同时不会更新评论"""
    from src.plugins.github.models import RepoInfo, GithubHandler

    render_comment = "test\n<!-- NONEFLOW -->\n"

    mock_comment = mocker.MagicMock()
    mock_comment.body = "test\n<!-- NONEFLOW -->\n"
    mock_comment.id = 123

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "owner", "repo": "repo", "issue_number": 1},
            mock_list_comments_resp,
        )

        handler = GithubHandler(bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"))

        await handler.comment_issue(render_comment, 1)

    # mock_render_comment.assert_called_once_with("test\n<!-- NONEFLOW -->\n", True)
