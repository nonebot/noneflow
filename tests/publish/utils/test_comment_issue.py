from typing import cast

from nonebot import get_adapter
from nonebot.adapters.github import Adapter, GitHubBot
from nonebot.adapters.github.config import GitHubApp
from nonebug import App
from pytest_mock import MockerFixture


async def test_comment_issue(app: App, mocker: MockerFixture):
    from src.plugins.publish.models import RepoInfo
    from src.plugins.publish.utils import comment_issue

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
                "body": "# 📃 商店发布检查结果\n\ntest\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n",
            },
            True,
        )

        await comment_issue(bot, RepoInfo(owner="owner", repo="repo"), 1, "test")


async def test_comment_issue_reuse(app: App, mocker: MockerFixture):
    from src.plugins.publish.models import RepoInfo
    from src.plugins.publish.utils import comment_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "任意的东西\n<!-- NONEFLOW -->\n"
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
                "body": "# 📃 商店发布检查结果\n\ntest\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n♻️ 评论已更新至最新检查结果\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n",
            },
            True,
        )

        await comment_issue(bot, RepoInfo(owner="owner", repo="repo"), 1, "test")


async def test_comment_issue_reuse_same(app: App, mocker: MockerFixture):
    """测试评论内容相同时不会更新评论"""
    from src.plugins.publish.models import RepoInfo
    from src.plugins.publish.utils import comment_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "# 📃 商店发布检查结果\n\ntest\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n♻️ 评论已更新至最新检查结果\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n"
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

        await comment_issue(bot, RepoInfo(owner="owner", repo="repo"), 1, "test")
