from pytest_mock import MockerFixture


def test_comment_issue(mocker: MockerFixture):
    from src import Bot

    bot = Bot()
    bot.github = mocker.MagicMock()

    mock_list_comments_resp = mocker.MagicMock()
    bot.github.rest.issues.list_comments.return_value = mock_list_comments_resp

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp.parsed_data = [mock_comment]

    bot.comment_issue(1, "test")

    bot.github.rest.issues.update_comment.assert_not_called()
    bot.github.rest.issues.create_comment.assert_called_once_with(
        "owner",
        "repo",
        1,
        body="# 📃 商店发布检查结果\n\ntest\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n💪 Powered by NoneBot2 Publish Bot\n<!-- PUBLISH_BOT -->\n",
    )


def test_comment_issue_reuse(mocker: MockerFixture):
    from src import Bot

    bot = Bot()
    bot.github = mocker.MagicMock()

    mock_list_comments_resp = mocker.MagicMock()
    bot.github.rest.issues.list_comments.return_value = mock_list_comments_resp

    mock_comment = mocker.MagicMock()
    mock_comment.body = "任意的东西\n<!-- PUBLISH_BOT -->\n"
    mock_comment.id = 123
    mock_list_comments_resp.parsed_data = [mock_comment]

    bot.comment_issue(1, "test")

    bot.github.rest.issues.create_comment.assert_not_called()
    bot.github.rest.issues.update_comment.assert_called_once_with(
        "owner",
        "repo",
        123,
        body="# 📃 商店发布检查结果\n\ntest\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n♻️ 评论已更新至最新检查结果\n\n💪 Powered by NoneBot2 Publish Bot\n<!-- PUBLISH_BOT -->\n",
    )


def test_comment_issue_reuse_same(mocker: MockerFixture):
    """测试评论内容相同时不会更新评论"""
    from src import Bot

    bot = Bot()
    bot.github = mocker.MagicMock()

    mock_list_comments_resp = mocker.MagicMock()
    bot.github.rest.issues.list_comments.return_value = mock_list_comments_resp

    mock_comment = mocker.MagicMock()
    mock_comment.body = "# 📃 商店发布检查结果\n\ntest\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n♻️ 评论已更新至最新检查结果\n\n💪 Powered by NoneBot2 Publish Bot\n<!-- PUBLISH_BOT -->\n"
    mock_comment.id = 123
    mock_list_comments_resp.parsed_data = [mock_comment]

    bot.comment_issue(1, "test")

    bot.github.rest.issues.create_comment.assert_not_called()
    bot.github.rest.issues.update_comment.assert_not_called()
