from typing import cast

from nonebot import get_adapter
from nonebot.adapters.github import Adapter, GitHubBot
from nonebot.adapters.github.config import GitHubApp
from nonebug import App
from pytest_mock import MockerFixture


async def test_ensure_issue_content(app: App, mocker: MockerFixture):
    """确保议题内容完整"""
    from src.plugins.github.models import RepoInfo
    from src.plugins.github.plugins.publish.utils import ensure_issue_content

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
            "rest.issues.async_update",
            {
                "owner": "owner",
                "repo": "repo",
                "issue_number": 1,
                "body": "### 插件名称\n\n### 插件描述\n\n### 插件项目仓库/主页链接\n\n### 插件类型\n\n### 插件支持的适配器\n\n什么都没有",
            },
            True,
        )

        await ensure_issue_content(
            bot, RepoInfo(owner="owner", repo="repo"), 1, "什么都没有"
        )


async def test_ensure_issue_content_partial(app: App, mocker: MockerFixture):
    """确保议题内容被补全"""
    from src.plugins.github.models import RepoInfo
    from src.plugins.github.plugins.publish.utils import ensure_issue_content

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
            "rest.issues.async_update",
            {
                "owner": "owner",
                "repo": "repo",
                "issue_number": 1,
                "body": "### 插件描述\n\n### 插件项目仓库/主页链接\n\n### 插件支持的适配器\n\n### 插件名称\n\nname\n\n### 插件类型\n",
            },
            True,
        )

        await ensure_issue_content(
            bot,
            RepoInfo(owner="owner", repo="repo"),
            1,
            "### 插件名称\n\nname\n\n### 插件类型\n",
        )


async def test_ensure_issue_content_complete(app: App, mocker: MockerFixture):
    """确保议题内容已经补全之后不会再次补全"""
    from src.plugins.github.models import RepoInfo
    from src.plugins.github.plugins.publish.utils import ensure_issue_content

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

        await ensure_issue_content(
            bot,
            RepoInfo(owner="owner", repo="repo"),
            1,
            "### 插件描述\n\n### 插件项目仓库/主页链接\n\n### 插件支持的适配器\n\n### 插件名称\n\nname\n\n### 插件类型\n",
        )
