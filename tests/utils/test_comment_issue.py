# from nonebug import App
# from pytest_mock import MockerFixture


# async def test_comment_issue(app: App, mocker: MockerFixture):
#     from nonebot.adapters.github import GitHubBot
#     from nonebot.adapters.github.config import GitHubApp

#     from src.plugins.publish.models import RepoInfo
#     from src.plugins.publish.utils import comment_issue

#     repo_info = RepoInfo(owner="owner", repo="repo")
#     github = mocker.MagicMock()

#     async with app.test_api() as ctx:
#         bot = ctx.create_bot(base=GitHubBot, app=GitHubApp(app_id="1", private_key="1"))

#         mocker.patch.object(bot, "_github", github)

#         mock_list_comments_resp = mocker.MagicMock()
#         github.rest.issues.list_comments.return_value = mock_list_comments_resp

#         mock_comment = mocker.MagicMock()
#         mock_comment.body = "Bot: test"
#         mock_list_comments_resp.parsed_data = [mock_comment]

#         await comment_issue(bot, repo_info, 1, "test")

#         github.rest.issues.update_comment.assert_not_called()
#         github.rest.issues.create_comment.assert_called_once_with(
#             "owner",
#             "repo",
#             1,
#             body="# 📃 商店发布检查结果\n\ntest\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n💪 Powered by [NoneBot2 Publish Bot](https://github.com/nonebot/noneflow)\n<!-- PUBLISH_BOT -->\n",
#         )


# async def test_comment_issue_reuse(mocker: MockerFixture):
#     bot.github = mocker.MagicMock()

#     mock_list_comments_resp = mocker.MagicMock()
#     bot.github.rest.issues.list_comments.return_value = mock_list_comments_resp

#     mock_comment = mocker.MagicMock()
#     mock_comment.body = "任意的东西\n<!-- PUBLISH_BOT -->\n"
#     mock_comment.id = 123
#     mock_list_comments_resp.parsed_data = [mock_comment]

#     bot.comment_issue(1, "test")

#     bot.github.rest.issues.create_comment.assert_not_called()
#     bot.github.rest.issues.update_comment.assert_called_once_with(
#         "owner",
#         "repo",
#         123,
#         body="# 📃 商店发布检查结果\n\ntest\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n♻️ 评论已更新至最新检查结果\n\n💪 Powered by [NoneBot2 Publish Bot](https://github.com/nonebot/noneflow)\n<!-- PUBLISH_BOT -->\n",
#     )


# async def test_comment_issue_reuse_same(mocker: MockerFixture):
#     """测试评论内容相同时不会更新评论"""
#     from src import Bot

#     bot = Bot()
#     bot.github = mocker.MagicMock()

#     mock_list_comments_resp = mocker.MagicMock()
#     bot.github.rest.issues.list_comments.return_value = mock_list_comments_resp

#     mock_comment = mocker.MagicMock()
#     mock_comment.body = "# 📃 商店发布检查结果\n\ntest\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n♻️ 评论已更新至最新检查结果\n\n💪 Powered by [NoneBot2 Publish Bot](https://github.com/nonebot/noneflow)\n<!-- PUBLISH_BOT -->\n"
#     mock_comment.id = 123
#     mock_list_comments_resp.parsed_data = [mock_comment]

#     bot.comment_issue(1, "test")

#     bot.github.rest.issues.create_comment.assert_not_called()
#     bot.github.rest.issues.update_comment.assert_not_called()
